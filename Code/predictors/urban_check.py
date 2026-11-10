"""
Stage 3 check: is the urban effect local (fields near towns burn less) or a tehsil-wide trait? (2026-11-10)

Question [C] Soham, 2026-11-10: urban area share is the only driver that holds for the Central PDs with rice share
held constant (compare_drivers.py). Two readings: (a) fields close to built-up land burn less (smoke is noticed,
peri-urban farming, or a measurement effect at small mixed fields), or (b) the whole tehsil differs.

Data: the 100 rice points per tehsil of the burn measure and their 2020-24 verdicts (cut 0.786); distance from
each point to the nearest GHS-SMOD 2020 urban cell (class >= 21, 1 km grid, cell centres) and to an urban centre
(class 30). Central and South-west only.
Both distances are tested (MEASURES); the broad class >= 21 covers most of Central (72% of points within 2 km),
so the urban-centre distance is the sharper test.
  1. burnt share by distance band, raw and within tehsil-season (point verdict minus its tehsil-season mean)
  2. within slope: burnt ~ log(1 + km to urban) after removing tehsil-season means; 95% CI from 1,000 bootstrap
     draws of whole tehsils (points in a tehsil are not independent)
  3. artefact check: unknown verdicts and clear looks by band
  4. PD check: tehsil burnt share from points > FAR_KM from urban land only; is each PD still low in its group?

Run:  python Code/predictors/urban_check.py   (after drivers.py, which caches the SMOD grid)
Out:  outputs/predictors/drivers/urban_check_{bands,slope,far_points}.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import drivers as dr

ROOT = dr.ROOT
OUT = dr.OUT
GROUPS = ["Central", "South-west"]
YEARS = range(2020, 2025)
BANDS = [0, 2, 5, 10, np.inf]
FAR_KM = 5
MEASURES = {"km_urban": "urban cell (class >= 21)", "km_centre": "urban centre (class 30)"}
N_BOOT = 1000
SEED = 42


def point_distances():
    cells = dr.smod_cells().to_crs(dr.METRIC)
    xy = np.c_[cells.geometry.x, cells.geometry.y]
    p = pd.read_csv(dr.POINTS)
    pg = dr.gpd.GeoDataFrame(p, geometry=dr.gpd.points_from_xy(p.lon, p.lat), crs="EPSG:4326").to_crs(dr.METRIC)
    pxy = np.c_[pg.geometry.x, pg.geometry.y]
    for name, mask in [("km_urban", cells.smod.to_numpy() >= 21), ("km_centre", cells.smod.to_numpy() == 30)]:
        p[name] = cKDTree(xy[mask]).query(pxy)[0] / 1000
    return p[["loc", "lgd_tehsil_code", "km_urban", "km_centre"]]


def within_slope(d, x):
    """OLS slope of demeaned burnt on demeaned x (both demeaned by tehsil-season)."""
    yd = d.burnt - d.groupby(["lgd_tehsil_code", "year"]).burnt.transform("mean")
    xd = x - x.groupby([d.lgd_tehsil_code, d.year]).transform("mean")
    return (xd * yd).sum() / (xd ** 2).sum()


def main():
    g = pd.read_csv(ROOT / "outputs" / "grouping" / "FROZEN_groups.csv")[["lgd_tehsil_code", "lgd_tehsil_name", "group"]]
    g = g[g.group.isin(GROUPS)]
    v = pd.read_csv(ROOT / "outputs" / "burn_tehsil_rf" / "point_verdicts.csv")[["loc", "year", "burnt", "n_win"]]
    v = v[v.year.isin(YEARS)]
    d = v.merge(point_distances(), on="loc").merge(g, on="lgd_tehsil_code")
    d["unknown"] = d.burnt.isna()
    k = d[~d.unknown].copy()
    k["within"] = k.burnt - k.groupby(["lgd_tehsil_code", "year"]).burnt.transform("mean")
    bands, rows, far_tables = [], [], []
    for m, label in MEASURES.items():
        bands.append(band_table(d, k, m, label))
        rows += slope_rows(k, m, label)
        far_tables.append(far_table(k, g, m))
    bands = pd.concat(bands)
    slope = pd.DataFrame(rows)
    f = far_tables[0].merge(far_tables[1], on="lgd_tehsil_code", suffixes=("_urban", "_centre"))
    f = g.merge(f, on="lgd_tehsil_code")
    pdv = pd.read_csv(ROOT / "outputs" / "pd" / "pd_validated.csv")
    pdv = pdv[pdv.rule == "static"][["lgd_tehsil_code", "label"]]
    f = f.merge(pdv, on="lgd_tehsil_code", how="left")

    bands.round(4).to_csv(OUT / "urban_check_bands.csv", index=False)
    slope.round(4).to_csv(OUT / "urban_check_slope.csv", index=False)
    f.round(4).to_csv(OUT / "urban_check_far_points.csv", index=False)
    pd.set_option("display.width", 250)
    print(bands.round(3).to_string(index=False))
    print(slope.round(3).to_string(index=False))
    print(f[f.label.notna()].sort_values(["label", "group"]).round(3).to_string(index=False))


def band_table(d, k, m, label):
    lab = ["0-2 km", "2-5 km", "5-10 km", ">10 km"]
    d = d.assign(band=pd.cut(d[m], BANDS, right=False, labels=lab))
    k = k.assign(band=pd.cut(k[m], BANDS, right=False, labels=lab))
    return k.groupby(["group", "band"], observed=True).agg(
        points=("burnt", "size"), burnt_share=("burnt", "mean"), within_tehsil=("within", "mean")).join(
        d.groupby(["group", "band"], observed=True).agg(unknown_share=("unknown", "mean"),
                                                        looks_median=("n_win", "median"))).reset_index().assign(
        distance_to=label)


def slope_rows(k, m, label):
    rng = np.random.default_rng(SEED)
    rows = []
    for grp, x in k.groupby("group"):
        lx = np.log1p(x[m])
        est = within_slope(x, lx)
        codes = x.lgd_tehsil_code.unique()
        by = {c: x[x.lgd_tehsil_code == c] for c in codes}
        boot = []
        for _ in range(N_BOOT):
            s = pd.concat([by[c].assign(lgd_tehsil_code=i) for i, c in enumerate(rng.choice(codes, len(codes)))])
            boot.append(within_slope(s, np.log1p(s[m])))
        lo, hi = np.percentile(boot, [2.5, 97.5])
        # effect in burnt-share points of moving from 1 km to 10 km from urban land
        rows.append({"distance_to": label, "group": grp, "tehsils": len(codes), "point_seasons": len(x), "slope_per_log1p_km": est,
                     "ci_lo": lo, "ci_hi": hi, "change_1km_to_10km": est * (np.log1p(10) - np.log1p(1)),
                     "ci_lo_1to10": lo * (np.log1p(10) - np.log1p(1)), "ci_hi_1to10": hi * (np.log1p(10) - np.log1p(1))})
    return rows


def far_table(k, g, m):
    k = k.merge(g[["lgd_tehsil_code", "group"]].rename(columns={"group": "grp"}), on="lgd_tehsil_code")
    far = k[k[m] > FAR_KM].groupby("lgd_tehsil_code").agg(far_share=("burnt", "mean"), far_n=("burnt", "size"))
    allp = k.groupby("lgd_tehsil_code").agg(all_share=("burnt", "mean"), all_n=("burnt", "size"))
    f = allp.join(far).reset_index().merge(g[["lgd_tehsil_code", "group"]], on="lgd_tehsil_code")
    f["far_point_share"] = f.far_n / f.all_n
    f["rank_all"] = f.groupby("group").all_share.rank(pct=True)
    f["rank_far"] = f.groupby("group").far_share.rank(pct=True)
    return f.drop(columns="group")


if __name__ == "__main__":
    main()
