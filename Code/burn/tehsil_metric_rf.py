"""
Tehsil burning measure with the final Sentinel-2 model (2026-10-27)

Replaces the heat-peak rule of tehsil_metric.py (kept as the comparison measure). Final setting from the
Jalandhar tests (task_burn_detection.md, 2026-10-27), read at single 20 m pixels (gate test: pixel beats
3x3 / 5x5 windows at the strict cut, Jalandhar fields being small):
  candidate  clear look in 15 Sep - 30 Nov where the old BAIS2+TCB detector fires (z > 0) and z rises most
             over the previous clear look (which may lie before 15 Sep)
  before     the last clear look in the 20 days before the candidate
  model      random forest on all Walker fields (pre_looks = 1), candidate bands/indices + change vs before
  burnt      prob >= Walker cut90 (0.786, keeps 90% of Walker burns; main) and prob >= 0.5 (sensitivity)
Per point and season: 1 / 0; NaN (unknown) = no clear look in the window, or a candidate with no look before.

Points: the same 100 rice points per tehsil as tehsil_metric.py (outputs/burn_tehsil/points.csv), so both
measures sample the same places. Tehsil burnt share = burnt points / points with a verdict; burnt ha = share
x tehsil rice ha (tehsil_metric.rice_ha). 2022 is also scored with the window ending 24 Oct for the CREAMS
check (official 2022 table is in-season).

Run:  python Code/burn/tehsil_metric_rf.py [--limit N]   (N = first N points only, for a smoke test)
Out:  outputs/burn_tehsil_rf/tehsil_burn_measure.csv, point_verdicts.csv, aggregation_checks{,_05}.csv,
      district_from_tehsils.csv, old_vs_new.csv (raw extracts cached in outputs/burn_tehsil_rf/raw/)
"""

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import ee

import tehsil_metric as tm
from transfer_checks import ROOT, init_ee

sys.path.insert(0, str(ROOT / "Code" / "planet"))
import jalandhar_walker_model_test as jw  # noqa: E402  (also imports s2_from_planet_labels as jw.w)

w = jw.w
OUT = ROOT / "outputs" / "burn_tehsil_rf"
RAW = OUT / "raw"
YEARS = tm.YEARS
WIN = ("09-15", "11-30")
CUTOFF = tm.CUTOFF                     # {2022: "2022-10-24"}
PRE_DAYS = 20
EXTRACT = [("08-25", "09-15"), ("09-15", "10-15"), ("10-15", "11-15"), ("11-15", "12-01")]
CLEAR_SCL = tm.CLEAR_SCL
BANDS = jw.BANDS
WORKERS = 6


def s2_bands(pts, year, batch, tag=""):
    path = RAW / f"s2{tag}_{year}_b{batch}.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"loc": r.loc}) for r in pts.itertuples()])
    parts = []
    for start, end in EXTRACT:
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
               .filterDate(f"{year}-{start}", f"{year}-{end}").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))

        def samp(img):
            d = img.date().format("YYYY-MM-dd")
            return (img.select(["SCL"] + BANDS).sampleRegions(collection=fc, scale=20, geometries=False)
                    .map(lambda f: f.set("date", d)))
        for attempt in range(6):
            try:
                df = ee.data.computeFeatures({"expression": col.map(samp).flatten(), "fileFormat": "PANDAS_DATAFRAME"})
                break
            except Exception as e:
                print(f"    retry {attempt + 1}: {str(e)[:80]}", flush=True)
                time.sleep(30 * (attempt + 1))
        else:
            raise RuntimeError("Sentinel-2 extraction failed 6 times")
        print(f"  S2 {year} b{batch} {start}..{end}: {len(df)} point-looks", flush=True)
        parts.append(df.drop(columns=["geo"], errors="ignore"))
    s = pd.concat(parts, ignore_index=True)
    s["date"] = pd.to_datetime(s.date)
    s = s[s.SCL.isin(CLEAR_SCL)].drop(columns="SCL")
    s = s.groupby(["loc", "date"], as_index=False)[BANDS].mean()   # overlapping tiles, same day
    s.to_csv(path, index=False)
    return s


def looks(s):
    """Clear looks with indices and the old detector's z (as jalandhar_walker_model_test.looks)."""
    d = s.copy()
    d[BANDS] = d[BANDS] / 10000
    d["NDVI"] = (d.B8 - d.B4) / (d.B8 + d.B4)
    d["NBR"] = (d.B8 - d.B12) / (d.B8 + d.B12)
    d["NBR2"] = (d.B11 - d.B12) / (d.B11 + d.B12)
    d["BAIS2"] = w.bais2(d.B4, d.B6, d.B7, d.B8, d.B12)
    d["TCB"] = w.tcb(d.B2, d.B3, d.B4, d.B8, d.B11, d.B12)
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=w.VARS)
    sc, m = w.lp.model()
    d["z"] = m.decision_function(sc.transform(d[["BAIS2", "TCB"]].to_numpy()))
    return d.sort_values(["loc", "date"]).reset_index(drop=True)


def verdicts(d, locs, year, rf, cols, cut, win_end=None):
    """Per point: candidate, before, RF prob; burnt at cut and at 0.5."""
    w0 = pd.Timestamp(f"{year}-{WIN[0]}")
    w1 = pd.Timestamp(win_end or f"{year}-{WIN[1]}")
    d = d.copy()
    d["rise"] = d.groupby("loc").z.diff()
    inwin = d[(d.date >= w0) & (d.date <= w1)]
    n_win = inwin.groupby("loc").size()
    flagged = inwin[inwin.z > 0]
    cand = flagged.loc[flagged.rise.fillna(-np.inf).groupby(flagged["loc"]).idxmax()]
    by_loc = dict(tuple(d.groupby("loc")))
    rows, X = [], []
    for c in cand.itertuples():
        g = by_loc[c.loc]
        g = g[(g.date < c.date) & (g.date >= c.date - pd.Timedelta(days=PRE_DAYS))]
        if len(g):
            pre = g.iloc[-1]
            cv = np.array([getattr(c, v) for v in w.VARS], float)
            x = pd.concat([pd.Series(cv, index=w.VARS).add_prefix("post_"),
                           pd.Series(cv - pre[w.VARS].to_numpy(float), index=w.VARS).add_prefix("d_")])
            X.append(x[cols].to_numpy())
            rows.append({"loc": c.loc, "candidate_date": c.date, "candidate_z": c.z, "pre_date": pre.date})
        else:
            rows.append({"loc": c.loc, "candidate_date": c.date, "candidate_z": c.z, "pre_date": pd.NaT})
    v = pd.DataFrame(rows, columns=["loc", "candidate_date", "candidate_z", "pre_date"])
    v["prob"] = np.nan
    has = v.pre_date.notna().to_numpy()
    if has.any():
        v.loc[has, "prob"] = rf.predict_proba(np.vstack(X))[:, 1]
    r = pd.DataFrame({"loc": list(locs)}).merge(v, on="loc", how="left")
    r["year"] = year
    r["n_win"] = r["loc"].map(n_win).fillna(0).astype(int)
    for name, k in [("burnt", cut), ("burnt_05", 0.5)]:
        b = (r.prob >= k).astype(float)
        b[r.n_win == 0] = np.nan                                   # no clear look in the window
        b[r.candidate_date.notna() & r.prob.isna()] = np.nan       # candidate but no look before
        r[name] = b
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    global OUT, RAW
    pts = pd.read_csv(tm.OUT / "points.csv")
    if args.limit:
        pts = pts.head(args.limit).assign(batch=0)
        OUT = OUT / f"smoke_{args.limit}"
        RAW = OUT / "raw"
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    init_ee()

    def fetch(job):
        y, b = job
        s2_bands(pts[pts.batch == b], y, b)
        print(f"== done {y} b{b}", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(fetch, [(y, b) for y in YEARS for b in sorted(pts.batch.unique())]))

    jw.PRE_LOOKS, jw.CANDIDATE = 1, "jump"
    rf, cols, cut90 = jw.walker_model()
    res, cut = [], []
    for y in YEARS:
        d = looks(pd.concat([s2_bands(p, y, b) for b, p in pts.groupby("batch")], ignore_index=True))
        res.append(verdicts(d, pts["loc"], y, rf, cols, cut90))
        if y in CUTOFF:
            cut.append(verdicts(d, pts["loc"], y, rf, cols, cut90, CUTOFF[y]))
        r = res[-1]
        print(f"{y}: points with a verdict {int(r.burnt.notna().sum())}/{len(r)}, "
              f"burnt share {r.burnt.mean():.3f} (cut {cut90:.3f}), {r.burnt_05.mean():.3f} (cut 0.5)", flush=True)
    res = pd.concat(res, ignore_index=True)
    res.to_csv(OUT / "point_verdicts.csv", index=False)

    grp = pd.read_csv(tm.GROUPS)[["lgd_tehsil_code", "lgd_tehsil_name", "group"]]
    t = tm.tehsil_table(res, pts)
    t05 = tm.tehsil_table(res, pts, "burnt_05")[["year", "lgd_tehsil_code", "burnt_share", "burnt_ha"]]
    t = t.merge(t05.rename(columns={"burnt_share": "burnt_share_05", "burnt_ha": "burnt_ha_05"}),
                on=["year", "lgd_tehsil_code"]).merge(grp, on="lgd_tehsil_code", how="left")
    t["n_unknown"] = t.n_points - t.n_look
    t["in_pd_identification"] = t.group.isin(["Central", "South-west"])
    t.round(4).to_csv(OUT / "tehsil_burn_measure.csv", index=False)

    cut = pd.concat(cut, ignore_index=True)
    for col, sfx in [("burnt", ""), ("burnt_05", "_05")]:
        val = pd.concat([tm.tehsil_table(res[~res.year.isin(CUTOFF)], pts, col),
                         tm.tehsil_table(cut, pts, col)], ignore_index=True)
        dist, scores = tm.checks(val)
        if not sfx:
            dist.to_csv(OUT / "district_from_tehsils.csv", index=False)
        scores.to_csv(OUT / f"aggregation_checks{sfx}.csv", index=False)
        print(f"\nState and district checks vs CREAMS, {col} (2022 = till 24 Oct):")
        print(scores.to_string(index=False))

    old = pd.read_csv(tm.OUT / "tehsil_burn_measure.csv")[["year", "lgd_tehsil_code", "burnt_share"]]
    m = t.merge(old, on=["year", "lgd_tehsil_code"], suffixes=("", "_old"))
    ovn = []
    for y, g in m.groupby("year"):
        for scope, s in [("all", g), ("PD groups", g[g.in_pd_identification])]:
            ovn.append({"year": y, "scope": scope, "n": len(s),
                        "rho_new_vs_old": round(s.burnt_share.corr(s.burnt_share_old, "spearman"), 3),
                        "rho_05_vs_old": round(s.burnt_share_05.corr(s.burnt_share_old, "spearman"), 3),
                        "rho_new_vs_05": round(s.burnt_share.corr(s.burnt_share_05, "spearman"), 3)})
    ovn = pd.DataFrame(ovn)
    ovn.to_csv(OUT / "old_vs_new.csv", index=False)
    print("\nTehsil rank agreement (Spearman):")
    print(ovn.to_string(index=False))
    print("\nPoints per tehsil with a verdict (median, min) by year:")
    print(t.groupby("year").n_look.agg(["median", "min"]).to_string())
    print("\nArea-weighted burnt % by group and year (main cut):")
    gy = t.groupby(["year", "group"])[["burnt_ha", "rice_ha"]].sum()
    print((100 * gy.burnt_ha / gy.rice_ha).round(1).unstack().to_string())


if __name__ == "__main__":
    main()
