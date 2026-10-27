"""
Does MODIS land surface temperature & emissivity show burning as a heat peak? (2026-10-18)

Prof. Aaditeshwar suggested adding a heat measure to BAIS2 + TCB and reading burning as a curve
(before -> peak -> cooling). Soham recalls "land surface temperature" and "emissivity", i.e. the
MODIS LST & Emissivity product (MOD21/MYD21, TES algorithm: emissivity retrieved per observation).

Landsat LST (thermal_check.py) only sees ~10:30 am, when bare ploughed soil and char are equally
warm. MODIS Aqua passes ~13:30, when fires burn. Key feature:
  afternoon - morning  = Aqua-day anomaly - Terra-day anomaly (same day)
Bare ground is warm at both passes; a fire adds heat only in the afternoon.

Unit = 1 km MODIS pixel holding CEEW fields. Label = share of the pixel's CEEW fields that are
burnt on the label date (2020-11-10 Sangrur, 2021-10-29 Jalandhar/Kapurthala).
Weather is removed by subtracting the daily median of all pixels within REGION_KM of the fields.
Series are smoothed with a Whittaker smoother (missing days weight 0).

Run:  python Code/burn/modis_lste_check.py [--skip-extract] [--lam 5]
Out:  outputs/burn_checks/modis_*.csv
"""

import argparse

import ee
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import spsolve

from transfer_checks import LABEL_DATES, OUT, BURNT, fields, init_ee, to_df

PASSES = {"terra_day": "MODIS/061/MOD21A1D", "aqua_day": "MODIS/061/MYD21A1D",
          "aqua_night": "MODIS/061/MYD21A1N"}
VARS = ["LST", "Emis_29", "Emis_31", "Emis_32"]
REGION_KM = 30
MONTHS = [8, 9, 10, 11, 12]


def prep(img):
    good = img.select("QC").bitwiseAnd(3).eq(0)          # bits 0-1: 0 = produced, good quality
    # the Earth Engine copy is already scaled: LST in K, emissivity 0-1
    lst = img.select("LST_1KM").subtract(273.15).rename("LST")
    emis = img.select(["Emis_29", "Emis_31", "Emis_32"])
    return lst.addBands(emis).updateMask(good).copyProperties(img, ["system:time_start"])


def pixel_points(year):
    """One point per MODIS pixel that holds CEEW fields, with that pixel's burnt share."""
    fc = fields(year)
    proj = ee.Image(ee.ImageCollection(PASSES["aqua_day"]).first()).select("LST_1KM").projection()
    pc = ee.Image.pixelCoordinates(proj).floor().int()
    cent = fc.map(lambda f: f.setGeometry(f.geometry().centroid(1)))
    df = to_df(pc.sampleRegions(collection=cent, scale=proj.nominalScale(), geometries=False))
    lonlat = [f["geometry"]["coordinates"] for f in cent.getInfo()["features"]]
    ids = [f["properties"]["field_id"] for f in cent.getInfo()["features"]]
    df = df.merge(pd.DataFrame({"field_id": ids, "lon": [c[0] for c in lonlat],
                                "lat": [c[1] for c in lonlat]}), on="field_id")
    df["pix"] = df.x.astype(str) + "_" + df.y.astype(str)
    df["is_burnt"] = df.field_category.isin(BURNT).astype(int)
    pix = df.groupby("pix").agg(n_fields=("field_id", "size"), burnt_share=("is_burnt", "mean"),
                                lon=("lon", "first"), lat=("lat", "first")).reset_index()
    pix["year"] = year
    return pix, fc


def extract():
    ts, reg, pixs = [], [], []
    for year in LABEL_DATES:
        pix, fc = pixel_points(year)
        pixs.append(pix)
        print(f"{year}: {len(pix)} MODIS pixels hold CEEW fields", flush=True)
        pts = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"pix": r.pix})
                                    for r in pix.itertuples()])
        region = fc.geometry().bounds(1).buffer(REGION_KM * 1000, 1000)
        for name, cid in PASSES.items():
            for m in MONTHS:
                start = ee.Date.fromYMD(year, m, 1)
                col = ee.ImageCollection(cid).filterDate(start, start.advance(1, "month")).map(prep)

                def sample(img):
                    d = img.date().format("YYYY-MM-dd")
                    return img.sampleRegions(collection=pts, scale=1000, geometries=False).map(
                        lambda f: f.set("date", d))

                def regional(img):
                    v = img.reduceRegion(ee.Reducer.median(), region, 1000, maxPixels=1e8)
                    return ee.Feature(None, v).set("date", img.date().format("YYYY-MM-dd"))

                s = to_df(col.map(sample).flatten())
                r = to_df(col.map(regional))
                for d in (s, r):
                    d["year"], d["pass"] = year, name
                ts.append(s)
                reg.append(r)
                print(f"  {name} {year}-{m:02d}: {len(s)} pixel-days", flush=True)
    ts, reg, pixs = (pd.concat(x, ignore_index=True) for x in (ts, reg, pixs))
    ts.to_csv(OUT / "modis_pixel_series.csv", index=False)
    reg.to_csv(OUT / "modis_regional_series.csv", index=False)
    pixs.to_csv(OUT / "modis_pixels.csv", index=False)
    return ts, reg, pixs


def whittaker(y, lam):
    """Whittaker smoother: minimise sum w (y - z)^2 + lam * sum (2nd diff z)^2; NaN -> weight 0."""
    w = (~np.isnan(y)).astype(float)
    if w.sum() < 4:
        return np.full_like(y, np.nan)
    n = len(y)
    D = sparse.diags([1, -2, 1], [0, 1, 2], shape=(n - 2, n))
    W = sparse.diags(w)
    return spsolve((W + lam * D.T @ D).tocsc(), w * np.nan_to_num(y))


def anomalies(ts, reg, lam):
    ts, reg = ts.copy(), reg.copy()
    for d in (ts, reg):
        d["date"] = pd.to_datetime(d.date)
    reg = reg.rename(columns={v: v + "_reg" for v in VARS})
    a = ts.merge(reg[["year", "pass", "date"] + [v + "_reg" for v in VARS]], on=["year", "pass", "date"])
    for v in VARS:
        a[v] = a[v] - a[v + "_reg"]
    a = a.pivot_table(index=["year", "pix", "date"], columns="pass", values=VARS).reset_index()
    a.columns = ["_".join(c).strip("_") for c in a.columns]
    a["LST_aft_minus_morn"] = a.LST_aqua_day - a.LST_terra_day
    feats = [c for c in a.columns if c not in ("year", "pix", "date")]
    out = []
    for (year, pix), g in a.groupby(["year", "pix"]):
        days = pd.date_range(f"{year}-08-01", f"{year}-12-31")
        g = g.set_index("date").reindex(days)
        g["year"], g["pix"] = year, pix
        for f in feats:
            g[f + "_sm"] = whittaker(g[f].to_numpy(dtype=float), lam)
        out.append(g.rename_axis("date").reset_index())
    return pd.concat(out, ignore_index=True), feats


def evaluate(sm, feats, pixs):
    sm = sm.merge(pixs[["year", "pix", "n_fields", "burnt_share"]], on=["year", "pix"])
    lab = sm.year.map({y: pd.Timestamp(v[1]) for y, v in LABEL_DATES.items()})
    sm["days"] = (sm.date - lab).dt.days
    rows = []
    for year, g in sm.groupby("year"):
        base = g[(g.days >= -60) & (g.days <= -30)].groupby("pix")
        burn = g[(g.days >= -15) & (g.days <= 5)].groupby("pix")
        after = g[(g.days >= 25) & (g.days <= 45)].groupby("pix")
        info = g.groupby("pix")[["burnt_share", "n_fields"]].first()
        for f in feats:
            c = f + "_sm"
            t = info.assign(base=base[c].mean(), peak=burn[c].max(), after=after[c].mean()).dropna()
            t["rise"] = t.peak - t.base
            t["fall"] = t.peak - t.after
            many = t[t.n_fields >= 3]
            rows.append({"year": year, "feature": f, "n_pix": len(t), "n_pix_3plus": len(many),
                         "median_rise": round(t.rise.median(), 3),
                         "median_fall": round(t.fall.median(), 3),
                         "spearman_rise_vs_burnt_share": round(t.rise.corr(t.burnt_share, "spearman"), 3),
                         "spearman_rise_vs_burnt_share_3plus":
                             round(many.rise.corr(many.burnt_share, "spearman"), 3) if len(many) > 4 else np.nan})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "modis_evaluation.csv", index=False)
    print("\nRise = peak (label -15..+5 d) - baseline (-60..-30 d); fall = peak - after (+25..+45 d)")
    print(res.to_string(index=False))

    # weekly curve, pixels split at the median burnt share
    sm["week"] = (sm.days // 7) * 7
    sm["burn_group"] = np.where(sm.burnt_share >= sm.groupby("year").burnt_share.transform("median"),
                                "high_burn", "low_burn")
    keep = ["LST_aqua_day_sm", "LST_terra_day_sm", "LST_aft_minus_morn_sm", "Emis_29_aqua_day_sm",
            "Emis_31_aqua_day_sm"]
    curve = sm[(sm.days >= -63) & (sm.days <= 49)].groupby(["year", "burn_group", "week"])[keep].mean().round(3)
    curve.to_csv(OUT / "modis_weekly_curve.csv")
    print("\nWeekly mean (smoothed anomaly vs region), by pixel burn group:")
    print(curve.to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-extract", action="store_true")
    ap.add_argument("--lam", type=float, default=5.0)
    a = ap.parse_args()
    if a.skip_extract:
        ts, reg, pixs = (pd.read_csv(OUT / f"modis_{n}.csv")
                         for n in ("pixel_series", "regional_series", "pixels"))
    else:
        init_ee()
        ts, reg, pixs = extract()
    print("\nPixels:", pixs.groupby("year").agg(n=("pix", "size"), fields=("n_fields", "sum"),
                                                share_med=("burnt_share", "median")).to_dict("index"))
    sm, feats = anomalies(ts, reg, a.lam)
    evaluate(sm, feats, pixs)


if __name__ == "__main__":
    main()
