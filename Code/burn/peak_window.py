"""
Heat-peak window: read BAIS2 + TCB only around each pixel's MODIS heat peak (2026-10-18)

modis_vs_s2_burnfrac.py showed that 1 km MODIS LST (vs its surroundings) rises to a peak when a
pixel's fields burn and then cools (irrigation / sowing), and the peak comes later where burning
is later. Season-long accumulation of single-date BAIS2+TCB flags over-counts (95% of random
cropland spots flagged at least once, because tilled soil looks like char). Rule tested here:

  1 MODIS Aqua-day LST (MYD21A1D, ~13:30), anomaly = pixel - 30 km focal mean (same day),
    1 Aug - 31 Dec; Whittaker smoother (lambda LAM, 2nd differences, missing days weight 0)
  2 peak date = argmax of the smoothed anomaly within the official season 15 Sep - 30 Nov
  3 a location is burnt if any clear Sentinel-2 look in [peak - A, peak + B] is flagged
    (pooled relaxed-mask BAIS2+TCB logistic model, as before)

Compared with the season rule (any look 1 Oct - 15 Dec) on
  - CEEW fields 2020/2021 (S2 flags from check3_timeseries.csv: field burnt-pixel share >= 0.5)
  - random cropland spots 2022 (same draw as labelling_package.py: seed 42, 120 per frozen-v4
    group, ESA WorldCover cropland; the 60 labelling spots were biased, this pool is not)

Run:  python Code/burn/peak_window.py [--skip-extract]
Out:  outputs/burn_peak/*.csv
"""

import argparse
import json
import random

import ee
import numpy as np
import pandas as pd

import labelling_package as lp
from modis_lste_check import whittaker
from transfer_checks import BURNT, GT_DIR, LABEL_DATES, ROOT, ee_classifier, init_ee

OUT = ROOT / "outputs" / "burn_peak"
AQUA = "MODIS/061/MYD21A1D"
FOCAL_M = 30000
SEASON_PEAK = ("09-15", "11-30")
WINDOWS = [(-7, 7), (-14, 7), (-21, 7), (-14, 14), (-21, 14)]
LAMS = [10, 50, 200]
LAM = 50


# ---------------------------------------------------------------- locations + S2 flags
def ceew_points():
    rows = []
    for year, (fn, *_r) in LABEL_DATES.items():
        for f in json.loads((GT_DIR / fn).read_text())["features"]:
            coords = np.array(_flatten(f["geometry"]["coordinates"]))  # vertex mean ~ centroid
            rows.append({"loc": f"{year}_{f['properties']['field_id']}", "year": year,
                         "lon": coords[:, 0].mean(), "lat": coords[:, 1].mean(),
                         "field_category": f["properties"]["field_category"],
                         "burnt": int(f["properties"]["field_category"] in BURNT)})
    return pd.DataFrame(rows)


def _flatten(c):
    return [c] if isinstance(c[0], (int, float)) else [p for x in c for p in _flatten(x)]


def ceew_flags():
    ts = pd.read_csv(ROOT / "outputs" / "burn_checks" / "check3_timeseries.csv", parse_dates=["date"])
    ts = ts[ts.pixels >= 3]
    ts = ts.groupby(["year", "field_id", "date"], as_index=False).burnt_pixel_share.mean()
    ts["loc"] = ts.year.astype(str) + "_" + ts.field_id.astype(str)
    ts["flag"] = (ts.burnt_pixel_share >= 0.5).astype(int)
    return ts[["loc", "date", "flag"]]


def spot_points_and_flags():
    pts_path, ser_path = OUT / "spots_meta.csv", OUT / "spots_series.csv"
    if pts_path.exists() and ser_path.exists():
        return pd.read_csv(pts_path), pd.read_csv(ser_path, parse_dates=["date"])
    lp.SEASON = ("2022-09-15", "2022-12-16")
    rng = random.Random(lp.SEED)
    sc, m = lp.model()
    clf = ee_classifier(sc, m)
    metas, sers = [], []
    for group, geom in lp.group_geometries().items():
        pts = lp.random_points(geom, lp.CANDIDATES_PER_GROUP, rng)
        s, coords = lp.candidate_series(group, geom, pts, clf)
        cs = lp.clear_series(s)
        metas.append(pd.DataFrame([{"loc": p, "group": group, "lon": c[0], "lat": c[1], "year": 2022}
                                   for p, c in coords.items()]))
        sers.append(cs.rename(columns={"pid": "loc"}))
    meta, ser = pd.concat(metas, ignore_index=True), pd.concat(sers, ignore_index=True)
    ser["date"] = pd.to_datetime(ser.date, format="%Y%m%d")
    meta.to_csv(pts_path, index=False)
    ser[["loc", "date", "flag"]].to_csv(ser_path, index=False)
    return meta, ser[["loc", "date", "flag"]]


# ---------------------------------------------------------------- MODIS series
def modis_series(pts, path=OUT / "modis_aqua_anomaly.csv"):
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    kernel = ee.Kernel.circle(FOCAL_M, "meters")

    def anom(img):
        good = img.select("QC").bitwiseAnd(3).eq(0)
        lst = img.select("LST_1KM").subtract(273.15).updateMask(good)
        ref = lst.reduceNeighborhood(ee.Reducer.mean(), kernel)
        return lst.subtract(ref).rename("anom").set("day", img.date().format("YYYY-MM-dd"))

    parts = []
    for year, g in pts.groupby("year"):
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"loc": r.loc})
                                   for r in g.itertuples()])
        for mth in range(8, 13):
            start = ee.Date.fromYMD(int(year), mth, 1)
            col = ee.ImageCollection(AQUA).filterDate(start, start.advance(1, "month")).map(anom)
            samp = col.map(lambda img: img.sampleRegions(collection=fc, scale=1000, geometries=False)
                           .map(lambda f: f.set("date", img.get("day")))).flatten()
            df = ee.data.computeFeatures({"expression": samp, "fileFormat": "PANDAS_DATAFRAME"})
            print(f"  MODIS {year}-{mth:02d}: {len(df)} location-days", flush=True)
            parts.append(df)
    df = pd.concat(parts, ignore_index=True)
    df["date"] = pd.to_datetime(df.date)
    df[["loc", "date", "anom"]].to_csv(path, index=False)
    return df[["loc", "date", "anom"]]


def peaks(ms, pts, lam):
    yr = pts.set_index("loc").year
    rows = []
    for loc, g in ms.groupby("loc"):
        y = int(yr[loc])
        days = pd.date_range(f"{y}-08-01", f"{y}-12-31")
        s = g.groupby("date").anom.mean().reindex(days).to_numpy(dtype=float)
        z = whittaker(s, lam)
        inside = (days >= pd.Timestamp(f"{y}-{SEASON_PEAK[0]}")) & (days <= pd.Timestamp(f"{y}-{SEASON_PEAK[1]}"))
        if np.isnan(z).all():
            continue
        zi = np.where(inside, z, -np.inf)
        k = int(np.argmax(zi))
        rows.append({"loc": loc, "peak_date": days[k], "peak_anom": round(z[k], 3),
                     "clear_days": int((~np.isnan(s)).sum())})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- rules
def apply_rules(flags, pk, pts):
    f = flags.merge(pk[["loc", "peak_date"]], on="loc")
    f["d"] = (f.date - f.peak_date).dt.days
    yr = f["loc"].map(pts.set_index("loc").year)
    out = pts.set_index("loc")[[]].copy()
    season = f[(f.date >= pd.to_datetime(yr.astype(str) + "-10-01")) & (f.date <= pd.to_datetime(yr.astype(str) + "-12-15"))]
    out["season_any"] = season.groupby("loc").flag.max()
    official = f[(f.date >= pd.to_datetime(yr.astype(str) + "-09-15")) & (f.date <= pd.to_datetime(yr.astype(str) + "-11-30"))]
    out["official_any"] = official.groupby("loc").flag.max()
    for a, b in WINDOWS:
        w = f[(f.d >= a) & (f.d <= b)]
        out[f"win_{a}_{b}"] = w.groupby("loc").flag.max()
        out[f"looks_{a}_{b}"] = w.groupby("loc").size()
    return out.reset_index()


def summarise(res, pts, tag):
    rules = ["season_any", "official_any"] + [f"win_{a}_{b}" for a, b in WINDOWS]
    d = res.merge(pts, on="loc")
    rows = []
    if "burnt" in d:
        for cat, g in [("CEEW burnt", d[d.burnt == 1]), ("CEEW unburnt (harvested)", d[d.field_category == "unburnt"]),
                       ("CEEW standing crop", d[d.field_category.isin(["green_unburnt", "golden_yellow_unburnt"])])]:
            rows.append({"set": cat, "n": len(g), **{r: round(g[r].mean(), 3) for r in rules},
                         **{f"no_look_{a}_{b}": round(g[f"looks_{a}_{b}"].isna().mean(), 3) for a, b in WINDOWS}})
    else:
        for grp, g in [("all", d)] + list(d.groupby("group")):
            rows.append({"set": f"2022 spots {grp}", "n": len(g), **{r: round(g[r].mean(), 3) for r in rules},
                         **{f"no_look_{a}_{b}": round(g[f"looks_{a}_{b}"].isna().mean(), 3) for a, b in WINDOWS}})
    t = pd.DataFrame(rows)
    print(f"\n[{tag}] share flagged burnt (locations with no clear look in the window excluded; no_look_* = their share)")
    print(t.to_string(index=False))
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-extract", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not a.skip_extract:
        init_ee()
    cp = ceew_points()
    sp, sflags = spot_points_and_flags()
    pts = pd.concat([cp, sp], ignore_index=True)
    ms = modis_series(pts)
    cflags = ceew_flags()

    tables = []
    for lam in LAMS:
        pk = peaks(ms, pts, lam)
        pk.to_csv(OUT / f"peaks_lam{lam}.csv", index=False)
        c = pk.merge(cp, on="loc")
        c["peak_minus_label"] = (c.peak_date - c.year.map({y: pd.Timestamp(v[1]) for y, v in LABEL_DATES.items()})).dt.days
        print(f"\n=== lambda {lam} ===")
        print("CEEW peak - label date (days), by year:",
              c.groupby("year").peak_minus_label.describe()[["count", "25%", "50%", "75%"]].to_dict("index"))
        print("2022 spot peak dates:", pk.merge(sp, on="loc").peak_date.describe()[["min", "25%", "50%", "75%", "max"]].astype(str).to_dict())
        for flags, p, tag in [(cflags, cp, "CEEW"), (sflags, sp, "spots 2022")]:
            t = summarise(apply_rules(flags, pk, p), p, f"{tag}, lambda {lam}")
            t.insert(0, "lambda", lam)
            tables.append(t)
    pd.concat(tables).to_csv(OUT / "rule_summary.csv", index=False)


if __name__ == "__main__":
    main()
