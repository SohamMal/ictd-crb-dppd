"""
Can char (fresh burn) be told apart from ploughed / sown soil? (Phase B, step A, 2026-10-09)

The season-long check showed the BAIS2+TCB model flags ~94% of harvested-unburnt CEEW
fields and keeps burnt fields "burnt" for > 30 days, i.e. it reads tilled soil as char.
Visual labelling of 10 m chips was not feasible, so we build proxy classes from the CEEW
fields themselves, across every clear Sentinel-2 look (1 Oct - 15 Dec, 2020 and 2021):

  char     burnt fields (completely / partially) within +-3 days of their label date
  soil     the same burnt fields >= 25 days after the label date (ploughed / sown), NDVI < 0.3
  stubble  harvested-unburnt fields within +-3 days of the label date
  green    green / golden unburnt fields (standing crop) within +-3 days of the label date

Steps
  1 extract field-median bands + indices for every look (Earth Engine)
  2 separability per feature (AUC) for char vs soil and char vs stubble
  3 classifier char vs not-char (soil + stubble + green): logistic on several features,
    cross-year validation (train 2021 -> test 2020 and reverse); compare with BAIS2+TCB
  4 rerun the season rules with the new classifier on the CEEW time series

Run:  python Code/burn/char_vs_soil.py [--skip-extract]
Out:  outputs/burn_checks/charsoil_*.csv
"""

import argparse

import ee
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from transfer_checks import LABEL_DATES, MASKS, OUT, BURNT, fields, init_ee, to_df

BANDS = ["B2", "B3", "B4", "B8", "B8A", "B11", "B12"]
FEATURES_ALL = ["B2", "B3", "B4", "B8", "B8A", "B11", "B12", "NDVI", "NBR", "NBR2", "BAIS2", "TCB",
                "SWIR_ratio", "VIS_mean"]
SETS = {
    "BAIS2+TCB (current)": ["BAIS2", "TCB"],
    "NBR2+SWIR": ["NBR2", "B11", "B12"],
    "BAIS2+TCB+NBR2+B12": ["BAIS2", "TCB", "NBR2", "B12"],
    "all bands+indices": FEATURES_ALL,
}


def feature_image(img):
    sr = img.select(BANDS).divide(10000)
    scl = img.select("SCL")
    valid = scl.eq(2).Or(scl.eq(4)).Or(scl.eq(5)).Or(scl.eq(7))
    sr = sr.updateMask(valid)
    b = {k: sr.select(k) for k in BANDS}
    ndvi = b["B8"].subtract(b["B4"]).divide(b["B8"].add(b["B4"])).rename("NDVI")
    nbr = b["B8"].subtract(b["B12"]).divide(b["B8"].add(b["B12"])).rename("NBR")
    nbr2 = b["B11"].subtract(b["B12"]).divide(b["B11"].add(b["B12"])).rename("NBR2")
    s6 = img.select(["B6", "B7"]).divide(10000).updateMask(valid)
    p1 = s6.select("B6").multiply(s6.select("B7")).multiply(b["B8A"]).divide(b["B4"]).sqrt()
    p2 = b["B12"].subtract(b["B8A"]).divide(b["B12"].add(b["B8A"]).sqrt()).add(1)
    bais2 = ee.Image(1).subtract(p1).multiply(p2).rename("BAIS2")
    tcb = (b["B2"].multiply(0.3510).add(b["B3"].multiply(0.3813)).add(b["B4"].multiply(0.3437))
           .add(b["B8"].multiply(0.7196)).add(b["B11"].multiply(0.2396)).add(b["B12"].multiply(0.1949))
           .rename("TCB"))
    swir_ratio = b["B12"].divide(b["B8A"]).rename("SWIR_ratio")
    vis = b["B2"].add(b["B3"]).add(b["B4"]).divide(3).rename("VIS_mean")
    return sr.addBands([ndvi, nbr, nbr2, bais2, tcb, swir_ratio, vis])


def extract():
    recs = []
    for year in LABEL_DATES:
        fc = fields(year)
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
               .filterDate(f"{year}-10-01", f"{year}-12-16")
               .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))
        ids = col.aggregate_array("system:index").getInfo()
        print(f"{year}: {len(ids)} images", flush=True)
        for k, iid in enumerate(ids, 1):
            img = feature_image(ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + iid))
            red = img.reduceRegions(collection=fc, reducer=ee.Reducer.median(), scale=20, tileScale=4)
            df = to_df(red)
            df["image"] = iid
            df["date"] = pd.to_datetime(iid[:8])
            recs.append(df)
            print(f"  {k}/{len(ids)} {iid[:8]}", flush=True)
    ts = pd.concat(recs, ignore_index=True)
    ts.to_csv(OUT / "charsoil_timeseries.csv", index=False)
    return ts


def add_classes(ts):
    ts = ts.dropna(subset=["B12", "BAIS2"]).copy()
    ts = ts.groupby(["year", "field_id", "field_category", "burnt", "date"], as_index=False)[FEATURES_ALL].mean()
    lab = ts.year.map({y: pd.Timestamp(v[1]) for y, v in LABEL_DATES.items()})
    ts["days"] = (ts.date - lab).dt.days
    near = ts.days.abs() <= 3
    cls = pd.Series("", index=ts.index)
    cls[(ts.burnt == 1) & near] = "char"
    cls[(ts.burnt == 1) & (ts.days >= 25) & (ts.NDVI < 0.3)] = "soil"
    cls[(ts.field_category == "unburnt") & near] = "stubble"
    cls[ts.field_category.isin(["green_unburnt", "golden_yellow_unburnt"]) & near] = "green"
    ts["proxy_class"] = cls
    return ts


def separability(ts):
    d = ts[ts.proxy_class != ""]
    rows = []
    for f in FEATURES_ALL:
        row = {"feature": f}
        for other in ["soil", "stubble", "green"]:
            sub = d[d.proxy_class.isin(["char", other])]
            y = (sub.proxy_class == "char").astype(int)
            auc = roc_auc_score(y, sub[f])
            row[f"auc_char_vs_{other}"] = round(max(auc, 1 - auc), 3)
            row[f"char_higher_than_{other}"] = auc >= 0.5
        rows.append(row)
    res = pd.DataFrame(rows).sort_values("auc_char_vs_soil", ascending=False)
    med = d.groupby("proxy_class")[FEATURES_ALL].median().round(3)
    res.to_csv(OUT / "charsoil_separability.csv", index=False)
    med.to_csv(OUT / "charsoil_class_medians.csv")
    print("\nClass sizes (field-looks):", d.proxy_class.value_counts().to_dict())
    print("\nSeparability (AUC; 0.5 = none, 1 = perfect):")
    print(res[["feature", "auc_char_vs_soil", "auc_char_vs_stubble", "auc_char_vs_green"]].to_string(index=False))
    print("\nClass medians:")
    print(med[["B4", "B8", "B11", "B12", "NDVI", "NBR", "NBR2", "BAIS2", "TCB"]].to_string())


def fit(df, feats):
    X = df[feats].to_numpy()
    sc = StandardScaler().fit(X)
    y = (df.proxy_class == "char").astype(int)
    return sc, LogisticRegression(max_iter=2000, class_weight="balanced").fit(sc.transform(X), y)


def classifiers(ts):
    d = ts[ts.proxy_class != ""]
    rows, models = [], {}
    for name, feats in SETS.items():
        for tr, te in [(2021, 2020), (2020, 2021)]:
            sc, m = fit(d[d.year == tr], feats)
            t = d[d.year == te]
            pred = m.predict(sc.transform(t[feats].to_numpy()))
            r = {"features": name, "train": tr, "test": te}
            for c in ["char", "soil", "stubble", "green"]:
                sub = pred[(t.proxy_class == c).to_numpy()]
                r[f"{c}_called_char"] = round(sub.mean(), 3) if len(sub) else np.nan
            rows.append(r)
        models[name] = fit(d, feats)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "charsoil_classifiers.csv", index=False)
    print("\nCross-year test: share of each proxy class called 'char' (want char high, others low)")
    print(res.to_string(index=False))
    return models


def season_rules(ts, models):
    out = []
    for name, (sc, m) in models.items():
        feats = SETS[name]
        t = ts.copy()
        t["flag"] = m.predict(sc.transform(t[feats].to_numpy())).astype(bool)
        for (year, fid), g in t.sort_values("date").groupby(["year", "field_id"]):
            seq = g.flag.to_numpy()
            out.append({"features": name, "year": year, "field_id": fid,
                        "field_category": g.field_category.iloc[0], "burnt": g.burnt.iloc[0],
                        "any_look": seq.any(),
                        "two_consecutive": bool(np.any(seq[:-1] & seq[1:])) if len(seq) > 1 else False,
                        "before_label": bool(g[g.days < -2].flag.any()),
                        "after_25d": bool(g[g.days >= 25].flag.any())})
    f = pd.DataFrame(out)
    f.to_csv(OUT / "charsoil_season_fields.csv", index=False)
    rows = []
    for name, g in f.groupby("features", sort=False):
        b, u = g[g.burnt == 1], g[g.burnt == 0]
        rows.append({"features": name,
                     "burnt_detected_any": round(b.any_look.mean(), 3),
                     "burnt_detected_2consec": round(b.two_consecutive.mean(), 3),
                     "burnt_still_flagged_after_25d": round(b.after_25d.mean(), 3),
                     "unburnt_flagged_any": round(u.any_look.mean(), 3),
                     "unburnt_flagged_2consec": round(u.two_consecutive.mean(), 3),
                     "unburnt_flagged_before_label": round(u.before_label.mean(), 3)})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "charsoil_season_summary.csv", index=False)
    print("\nSeason rules with each classifier (CEEW fields, 2020 + 2021):")
    print(res.to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-extract", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.skip_extract:
        ts = pd.read_csv(OUT / "charsoil_timeseries.csv", parse_dates=["date"])
    else:
        init_ee()
        ts = extract()
    ts = add_classes(ts)
    separability(ts)
    models = classifiers(ts)
    season_rules(ts, models)


if __name__ == "__main__":
    main()
