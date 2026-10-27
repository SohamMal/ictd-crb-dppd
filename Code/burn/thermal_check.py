"""
Does surface temperature separate char from ploughed soil? (Prof. Aaditeshwar's heat suggestion, 2026-10-15)

Optical Sentinel-2 bands cannot tell char from tilled soil (BAIS2 AUC 0.511, char_vs_soil.py).
Hypothesis: fire leaves a dry, dark, warm surface; pre-sowing ploughed fields are often irrigated
(moist, cooler). Test with Landsat 7/8/9 Collection 2 surface temperature (ST) on the CEEW fields,
same proxy classes as char_vs_soil.py:

  char     burnt fields (completely / partially) within +-WIN days of their label date
  soil     the same burnt fields >= 25 days after the label date, NDVI < 0.3
  stubble  harvested-unburnt fields within +-WIN days of the label date
  green    green / golden unburnt fields within +-WIN days of the label date

Landsat revisits every 8-16 days, so WIN = 3 and 5 are both reported.
Weather changes temperature day to day, so the main feature is the field's anomaly:
LST_anom = field median LST - median LST of the 1 km ring around the field (same image).
Caveat: Landsat thermal is sensed at 100 m (L8/9) / 60 m (L7) and resampled to 30 m;
CEEW fields are ~1-2 ha, so a field's LST is partly blended with neighbours.

Run:  python Code/burn/thermal_check.py [--skip-extract]
Out:  outputs/burn_checks/thermal_*.csv
"""

import argparse

import ee
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from transfer_checks import LABEL_DATES, OUT, fields, init_ee, to_df

# collection id -> (thermal band, red, nir)
SENSORS = {
    "LANDSAT/LE07/C02/T1_L2": ("ST_B6", "SR_B3", "SR_B4"),
    "LANDSAT/LC08/C02/T1_L2": ("ST_B10", "SR_B4", "SR_B5"),
    "LANDSAT/LC09/C02/T1_L2": ("ST_B10", "SR_B4", "SR_B5"),
}
RING_M = 1000
FEATURES = ["LST", "LST_anom", "NDVI"]


def prep(img, st, red, nir):
    qa = img.select("QA_PIXEL")
    # bits 1 dilated cloud, 3 cloud, 4 cloud shadow, 5 snow
    clear = qa.bitwiseAnd(0b111010).eq(0)
    lst = img.select(st).multiply(0.00341802).add(149.0).subtract(273.15).rename("LST")
    sr = img.select([red, nir]).multiply(0.0000275).add(-0.2)
    ndvi = sr.normalizedDifference([nir, red]).rename("NDVI")
    return lst.addBands(ndvi).updateMask(clear)


def extract():
    recs = []
    for year in LABEL_DATES:
        fc = fields(year)
        ring = fc.map(lambda f: f.setGeometry(f.geometry().buffer(RING_M).difference(f.geometry(), 1)))
        for cid, (st, red, nir) in SENSORS.items():
            col = (ee.ImageCollection(cid).filterBounds(fc.geometry())
                   .filterDate(f"{year}-10-01", f"{year}-12-16")
                   .filter(ee.Filter.lt("CLOUD_COVER", 60)))
            ids = col.aggregate_array("system:index").getInfo()
            print(f"{year} {cid.split('/')[1]}: {len(ids)} images", flush=True)
            for iid in ids:
                img = prep(ee.Image(f"{cid}/{iid}"), st, red, nir)
                f_df = to_df(img.reduceRegions(collection=fc, reducer=ee.Reducer.median(), scale=30, tileScale=4))
                r_df = to_df(img.select("LST").reduceRegions(collection=ring, reducer=ee.Reducer.median(),
                                                             scale=30, tileScale=4))
                # single-band reduceRegions names its output "median"; missing if no clear pixels
                if "LST" not in f_df or "median" not in r_df:
                    print(f"  {iid}: no clear pixels", flush=True)
                    continue
                df = f_df.merge(r_df[["field_id", "median"]].rename(columns={"median": "LST_ring"}),
                                on="field_id", how="left")
                df["sensor"], df["image"] = cid.split("/")[1], iid
                df["date"] = pd.to_datetime(iid.split("_")[-1], format="%Y%m%d")
                recs.append(df)
                print(f"  {iid}: {df.LST.notna().sum()} fields clear", flush=True)
    ts = pd.concat(recs, ignore_index=True)
    ts.to_csv(OUT / "thermal_timeseries.csv", index=False)
    return ts


def add_classes(ts, win):
    ts = ts.dropna(subset=["LST", "LST_ring"]).copy()
    ts["LST_anom"] = ts.LST - ts.LST_ring
    ts = ts.groupby(["year", "field_id", "field_category", "burnt", "date"], as_index=False)[FEATURES].mean()
    lab = ts.year.map({y: pd.Timestamp(v[1]) for y, v in LABEL_DATES.items()})
    ts["days"] = (ts.date - lab).dt.days
    near = ts.days.abs() <= win
    cls = pd.Series("", index=ts.index)
    cls[(ts.burnt == 1) & near] = "char"
    cls[(ts.burnt == 1) & (ts.days >= 25) & (ts.NDVI < 0.3)] = "soil"
    cls[(ts.field_category == "unburnt") & near] = "stubble"
    cls[ts.field_category.isin(["green_unburnt", "golden_yellow_unburnt"]) & near] = "green"
    ts["proxy_class"] = cls
    return ts


def separability(ts, win):
    d = ts[ts.proxy_class != ""]
    rows = []
    for f in FEATURES:
        row = {"window_days": win, "feature": f}
        for other in ["soil", "stubble", "green"]:
            sub = d[d.proxy_class.isin(["char", other])]
            y = (sub.proxy_class == "char").astype(int)
            if y.nunique() < 2:
                row[f"auc_char_vs_{other}"] = np.nan
                continue
            auc = roc_auc_score(y, sub[f])
            row[f"auc_char_vs_{other}"] = round(max(auc, 1 - auc), 3)
            row[f"char_higher_than_{other}"] = auc >= 0.5
        rows.append(row)
    n = d.proxy_class.value_counts().rename("n")
    med = d.groupby("proxy_class")[FEATURES].median().round(2).join(n)
    med.insert(0, "window_days", win)
    print(f"\n=== window +-{win} d ===")
    print("Class sizes (field-looks):", n.to_dict())
    print("Dates per class:", d.groupby("proxy_class").date.nunique().to_dict())
    print(pd.DataFrame(rows).to_string(index=False))
    print(med.to_string())
    return pd.DataFrame(rows), med.reset_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-extract", action="store_true")
    a = ap.parse_args()
    if a.skip_extract:
        ts = pd.read_csv(OUT / "thermal_timeseries.csv", parse_dates=["date"])
    else:
        init_ee()
        ts = extract()
    seps, meds = [], []
    for win in (3, 5):
        s, m = separability(add_classes(ts, win), win)
        seps.append(s)
        meds.append(m)
    pd.concat(seps).to_csv(OUT / "thermal_separability.csv", index=False)
    pd.concat(meds).to_csv(OUT / "thermal_class_medians.csv", index=False)


if __name__ == "__main__":
    main()
