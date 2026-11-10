"""
Version X, Stage 3 input: paddy harvest, wheat green-up and turnaround per village point (2026-11-10)

Same rules as the main version (Code/predictors/harvest_gap.py, 2026-10-23; turnaround fix of drivers.py):
NDVI on every clear S2 look 1 Sep - 31 Jan; harvest = drop from >= 0.45 to < 0.30 after 15 Sep; green-up =
first of two consecutive looks >= 0.30 after harvest. Points = the first N_PER of each village's burn points
(version_X/outputs/villages/points_new.csv), seasons 2020-24. Fewer points than the burn measure (3 vs 10)
because a median date per village over 5 seasons needs fewer points than a burnt share.

Run:  python version_X/Code/vx_harvest_gap.py
Out:  version_X/outputs/predictors/harvest_gap/point_dates.csv (+ NDVI series per year/batch in raw/)
"""

import sys
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "predictors"))
sys.path.insert(0, str(ROOT / "Code" / "burn"))
sys.modules.setdefault("rasterio", types.ModuleType("rasterio"))   # DLL blocked; only used for CIMMYT cells
import harvest_gap as hg  # noqa: E402
from transfer_checks import init_ee  # noqa: E402

OUT = ROOT / "version_X" / "outputs" / "predictors" / "harvest_gap"
YEARS = range(2020, 2025)
N_PER = 3
CHUNK = 1000
WORKERS = 2


def main():
    hg.RAW = OUT / "raw"
    hg.RAW.mkdir(parents=True, exist_ok=True)
    pts = pd.read_csv(ROOT / "version_X" / "outputs" / "villages" / "points_new.csv",
                      dtype={"c2011_village_code": str})
    pts = pts.groupby("c2011_village_code").head(N_PER).reset_index(drop=True)
    chunks = [(y, k) for y in YEARS for k in range(0, len(pts), CHUNK)]
    init_ee()
    with ThreadPoolExecutor(WORKERS) as ex:
        series = list(ex.map(lambda j: (j[0], hg.ndvi_series(pts.iloc[j[1]:j[1] + CHUNK], j[0], f"v{j[1] // CHUNK:02d}")),
                             chunks))
    res = []
    for y in YEARS:
        s = pd.concat([d for yy, d in series if yy == y], ignore_index=True)
        r = hg.point_dates(s, y)
        before = s.merge(r[["loc", "greenup"]], on="loc")
        before = before[before.date < before.greenup].groupby("loc").date.max().rename("look_before_greenup")
        late = s.merge(r[["loc", "harvest"]], on="loc")
        late = late[(late.date > late.harvest) & (late.date <= f"{y}-11-30")].groupby("loc").ndvi.max().rename(
            "ndvi_by_30nov")
        res.append(r.merge(before, on="loc", how="left").merge(late, on="loc", how="left"))
        print(f"{y}: harvest found {r.harvest.notna().mean():.2f}, green-up {r.greenup.notna().mean():.2f}", flush=True)
    res = pd.concat(res, ignore_index=True).merge(pts[["loc", "c2011_village_code"]], on="loc")
    res.to_csv(OUT / "point_dates.csv", index=False)


if __name__ == "__main__":
    main()
