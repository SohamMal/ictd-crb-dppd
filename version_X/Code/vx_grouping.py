"""
Version X, step 3b: homogeneous grouping of villages (2026-11-10)

Same method as the frozen tehsil grouping (Code/grouping/): dimension-balanced Gower distance (5 dimensions,
equal weight 1/5) -> average-linkage hierarchical clustering -> cut at k -> silhouette, bootstrap ARI.
Changes needed at village scale (decisions, version X):
  ruler       numeric range = 1st-99th percentile of the population (differences capped at 1). With 9,278
              villages a few extreme ones would otherwise set the ruler (the tehsil version left Dhar Kalan
              out of the range for the same reason).
  min size    a peer group needs >= MIN_GROUP villages for the quartile rules of PD identification; smaller
              branches are moved to the large group they are closest to (average distance), as at tehsil level.
  bootstrap   BOOT runs x 80% of villages (300 at tehsil level; one village tree takes ~1 min).
  choice of k largest silhouette among k = 2..8 whose groups stay stable (bootstrap ARI >= 0.75).
The result is compared with the frozen tehsil regions each village inherits (ARI), which answers "does the
village view regroup Punjab differently?".

Run:  python version_X/Code/vx_grouping.py
Out:  version_X/outputs/grouping/  dist (not saved; 9k x 9k), k_table.csv, village_groups.csv, group_profiles.csv
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import adjusted_rand_score, silhouette_samples

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "version_X" / "outputs" / "grouping"
DIMENSIONS = {
    "rice": [("rice_share_2022_cal", "numeric")],
    "rainfall": [("monsoon_rainfall_mm", "numeric")],
    "zone": [("aesr_share_14_2", "numeric"), ("aesr_share_2_5", "numeric"),
             ("aesr_share_4_1", "numeric"), ("aesr_share_9_1", "numeric")],
    "groundwater": [("extraction_pct_2022", "numeric")],
    "soil": [(f"soil_{c}", "categorical") for c in ["particle_size", "drainage", "soil_texture", "soil_depth",
                                                   "ph_class", "salinity", "sodicity", "erosion"]],
}
K_RANGE = range(2, 9)
MIN_GROUP = 100
BOOT, FRAC, SEED = 40, 0.8, 42
ARI_OK = 0.75


def gower(df, weights=None):
    n = len(df)
    names = list(DIMENSIONS)
    w = {d: 1 / len(names) for d in names} if weights is None else weights
    tot = np.zeros((n, n), np.float32)
    per_dim = {}
    for dim, cols in DIMENSIONS.items():
        s = np.zeros((n, n), np.float32)
        cnt = np.zeros((n, n), np.float32)
        for col, kind in cols:
            if kind == "numeric":
                x = df[col].to_numpy(np.float32)
                lo, hi = np.nanpercentile(x, [1, 99])
                span = hi - lo if hi > lo else (np.nanmax(x) - np.nanmin(x)) or 1.0
                d = np.minimum(np.abs(x[:, None] - x[None, :]) / span, 1.0)
                ok = ~np.isnan(x)
            else:
                codes, _ = pd.factorize(df[col])
                d = (codes[:, None] != codes[None, :]).astype(np.float32)
                ok = codes >= 0
            okm = ok[:, None] & ok[None, :]
            s += np.where(okm, d, 0)
            cnt += okm
            del d, okm
        dd = s / np.maximum(cnt, 1)
        per_dim[dim] = dd
        tot += w[dim] * dd
    np.fill_diagonal(tot, 0)
    return tot, per_dim


def tree(dist):
    return linkage(squareform(dist, checks=False).astype(np.float64), method="average")


def merge_small(labels, dist, min_size):
    lab = labels.copy()
    while True:
        sizes = pd.Series(lab).value_counts()
        small = sizes[sizes < min_size]
        big = sizes[sizes >= min_size].index
        if small.empty or len(big) == 0:
            return lab
        g = small.index[-1]
        idx = np.where(lab == g)[0]
        best = min(big, key=lambda b: dist[np.ix_(idx, np.where(lab == b)[0])].mean())
        lab[idx] = best


def relabel(lab):
    order = pd.Series(lab).value_counts().index
    return pd.Series(lab).map({g: i + 1 for i, g in enumerate(order)}).to_numpy()


def cut(z, dist, k):
    return relabel(merge_small(fcluster(z, k, "maxclust"), dist, MIN_GROUP))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m = pd.read_csv(OUT / "village_master.csv", dtype={"c2011_village_code": str, "lgd_tehsil_code": str})
    p = m[m.in_population].reset_index(drop=True)
    print(f"population: {len(p)} villages", flush=True)
    dist, per_dim = gower(p)
    z = tree(dist)
    print("tree built", flush=True)

    labels = {k: cut(z, dist, k) for k in K_RANGE}
    rng = np.random.default_rng(SEED)
    boots = []
    for b in range(BOOT):
        idx = np.sort(rng.choice(len(p), int(FRAC * len(p)), replace=False))
        sub = dist[np.ix_(idx, idx)]
        zs = tree(sub)
        for k in K_RANGE:
            boots.append({"run": b, "k": k, "ari": adjusted_rand_score(labels[k][idx], cut(zs, sub, k))})
        del sub
        if b % 10 == 0:
            print(f"  bootstrap {b}/{BOOT}", flush=True)
    boots = pd.DataFrame(boots)

    rows = []
    region = p.group.to_numpy()
    for k in K_RANGE:
        lab = labels[k]
        ng = len(np.unique(lab))
        sil = float(silhouette_samples(dist, lab, metric="precomputed").mean()) if ng > 1 else np.nan
        bk = boots[boots.k == k].ari
        rows.append({"k_cut": k, "groups_after_merge": ng, "sizes": "/".join(map(str, np.bincount(lab)[1:])),
                     "silhouette": round(sil, 3), "boot_ari_median": round(bk.median(), 3),
                     "boot_ari_p10": round(bk.quantile(0.1), 3),
                     "ari_vs_tehsil_regions": round(adjusted_rand_score(region, lab), 3)})
    kt = pd.DataFrame(rows)
    kt.to_csv(OUT / "k_table.csv", index=False)
    print(kt.to_string(index=False))

    ok = kt[(kt.boot_ari_median >= ARI_OK) & (kt.groups_after_merge > 1)].drop_duplicates("groups_after_merge")
    best = ok.sort_values("silhouette", ascending=False).iloc[0] if len(ok) else kt.iloc[0]
    k = int(best.k_cut)
    lab = labels[k]
    sil = silhouette_samples(dist, lab, metric="precomputed")
    p["vgroup"] = [f"V{g}" for g in lab]
    p["silhouette"] = sil.round(3)

    # how strongly each dimension separates the chosen groups: mean between-group minus within-group distance
    sep = {}
    same = lab[:, None] == lab[None, :]
    for d, dd in per_dim.items():
        sep[d] = round(float(dd[~same].mean() - dd[same & ~np.eye(len(lab), dtype=bool)].mean()), 3)

    keep = ["c2011_village_code", "c2011_village_name", "lgd_tehsil_code", "lgd_tehsil_name", "lgd_district_name",
            "group", "group_2way", "vgroup", "silhouette", "rice_share_2022_cal", "rice_ha_2022_cal", "rice_ha_both",
            "area_ha", "monsoon_rainfall_mm", "extraction_pct_2022", "aesr_share_14_2", "aesr_share_2_5",
            "aesr_share_4_1", "aesr_share_9_1", "soil_particle_size", "soil_soil_texture", "soil_drainage"]
    p[keep].rename(columns={"group": "tehsil_region", "group_2way": "tehsil_region_2way"}).to_csv(
        OUT / "village_groups.csv", index=False)
    prof = p.groupby("vgroup").agg(n=("c2011_village_code", "size"), rice_share=("rice_share_2022_cal", "median"),
                                   rain_mm=("monsoon_rainfall_mm", "median"),
                                   gw_pct=("extraction_pct_2022", "median"),
                                   zone_14_2=("aesr_share_14_2", "mean"), zone_2_5=("aesr_share_2_5", "mean"),
                                   zone_4_1=("aesr_share_4_1", "mean"), zone_9_1=("aesr_share_9_1", "mean"),
                                   top_soil=("soil_particle_size", lambda s: s.mode().iat[0]),
                                   silhouette=("silhouette", "mean"),
                                   share_central=("group", lambda s: (s == "Central").mean()))
    prof.round(3).to_csv(OUT / "group_profiles.csv")
    print(f"\nchosen cut k={k}: {best.sizes}, silhouette {best.silhouette}, boot ARI {best.boot_ari_median}")
    print(prof.round(3).to_string())
    print("dimension separation (between - within):", sep)
    print("cross-tab vs tehsil regions:\n", pd.crosstab(p.vgroup, p.group))
    json.dump({"k_cut": k, "dimensions": {d: [c for c, _ in v] for d, v in DIMENSIONS.items()},
               "weights": "equal", "min_group": MIN_GROUP, "boot": BOOT, "frac": FRAC, "separation": sep,
               "silhouette": float(best.silhouette), "boot_ari_median": float(best.boot_ari_median)},
              open(OUT / "chosen.json", "w"), indent=1)


if __name__ == "__main__":
    main()
