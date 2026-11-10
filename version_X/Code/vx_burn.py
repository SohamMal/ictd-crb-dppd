"""
Version X, step 2: village burning measure (2026-11-10)

Same detector as the main version's final measure (Code/burn/tehsil_metric_rf.py, 2026-10-27): Sentinel-2
candidate look (old BAIS2+TCB detector fires, largest z rise) in 15 Sep - 30 Nov, the last clear look in the
20 days before it, random forest trained on all Walker fields, burnt if prob >= Walker cut90 (0.786; main) or
>= 0.5 (sensitivity). Read at single 20 m pixels. Nothing in the detector is changed, so village and tehsil
numbers are directly comparable.

Points: version_X/outputs/villages/points_new.csv (10 rice pixels per village, Central + South-west) plus the
main version's 100-per-tehsil points (points_old.csv, verdicts reused from outputs/burn_tehsil_rf/
point_verdicts.csv). Seasons 2020-24 = the PD seasons of the main version.

Village burnt share (season) = burnt points / points with a verdict. With ~11 points a season the season value
is coarse (SE up to 0.15), which is why PD identification works on the 5-season pool (~55 point-seasons).

Run:  python version_X/Code/vx_burn.py [--limit N]
Out:  version_X/outputs/burn/point_verdicts.csv, village_burn_measure.csv (raw S2 extracts in raw/)
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import types

import numpy as np
import pandas as pd

# rasterio's DLL is blocked by Windows Application Control; tehsil_metric imports it only for its point
# sampler (not used here), so a stub module lets the detector code load.
sys.modules.setdefault("rasterio", types.ModuleType("rasterio"))

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "burn"))
import tehsil_metric_rf as tmr  # noqa: E402
from transfer_checks import init_ee  # noqa: E402

VX = ROOT / "version_X" / "outputs"
OUT = VX / "burn"
YEARS = range(2020, 2025)
WORKERS = 6


def village_table(res, pts):
    d = res.merge(pts[["loc", "c2011_village_code"]], on="loc")
    g = d.groupby(["year", "c2011_village_code"])
    t = g.burnt.agg(burnt_share="mean", n_look="count", n_burnt="sum").reset_index()
    t05 = g.burnt_05.agg(burnt_share_05="mean", n_burnt_05="sum").reset_index()
    t = t.merge(t05, on=["year", "c2011_village_code"])
    t["n_points"] = g.size().values
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    out = OUT if not args.limit else OUT / f"smoke_{args.limit}"
    tmr.RAW = out / "raw"
    tmr.RAW.mkdir(parents=True, exist_ok=True)
    pts = pd.read_csv(VX / "villages" / "points_new.csv", dtype={"c2011_village_code": str})
    if args.limit:
        pts = pts.head(args.limit).assign(batch=0)
    init_ee()

    def fetch(job):
        y, b = job
        tmr.s2_bands(pts[pts.batch == b], y, b)
        print(f"== done {y} b{b}", flush=True)
    jobs = [(y, b) for b in sorted(pts.batch.unique()) for y in YEARS]
    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(fetch, jobs))

    tmr.jw.PRE_LOOKS, tmr.jw.CANDIDATE = 1, "jump"
    rf, cols, cut90 = tmr.jw.walker_model()
    res = []
    for y in YEARS:
        d = tmr.looks(pd.concat([tmr.s2_bands(p, y, b) for b, p in pts.groupby("batch")], ignore_index=True))
        r = tmr.verdicts(d, pts["loc"], y, rf, cols, cut90)
        res.append(r)
        print(f"{y}: verdicts {int(r.burnt.notna().sum())}/{len(r)}, burnt share {r.burnt.mean():.3f} "
              f"(cut {cut90:.3f})", flush=True)
    res = pd.concat(res, ignore_index=True)
    res.to_csv(out / "point_verdicts_new.csv", index=False)

    old = pd.read_csv(VX / "villages" / "points_old.csv", dtype={"c2011_village_code": str}).dropna(
        subset=["c2011_village_code"])
    ov = pd.read_csv(ROOT / "outputs" / "burn_tehsil_rf" / "point_verdicts.csv")
    ov = ov[ov.year.isin(YEARS) & ov["loc"].isin(old["loc"])]
    allp = pd.concat([pts[["loc", "c2011_village_code"]], old[["loc", "c2011_village_code"]]], ignore_index=True)
    allres = pd.concat([res, ov], ignore_index=True)
    allres.to_csv(out / "point_verdicts.csv", index=False)
    vt = village_table(allres, allp)
    vt.to_csv(out / "village_burn_measure.csv", index=False)
    print("\nverdicts per village-season (median, 10th pct):",
          vt.n_look.median(), np.percentile(vt.n_look, 10))


if __name__ == "__main__":
    main()
