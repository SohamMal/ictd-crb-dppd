"""Exploratory (2026-10-06): bootstrap stability of alternative dimension designs.
Run: python Code/grouping/compare_designs.py"""
import numpy as np, pandas as pd, config, stability
from sklearn.metrics import adjusted_rand_score, silhouette_score
base = config.DIMENSIONS
nz = {k: v for k, v in base.items() if k != "zone"}
designs = {
  "A_zone (current)": base,
  "B_terrain elev+slope (old)": {**nz, "terrain": [("elevation_log1p","numeric"),("slope_log1p","numeric")]},
  "C_elevation only": {**nz, "terrain": [("elevation_log1p","numeric")]},
  "D_zone + elevation": {**base, "elevation": [("elevation_log1p","numeric")]},
}
df = pd.read_csv(config.MASTER_CSV); df = df[~df[config.NAME_COL].isin(config.OUTLIERS)].reset_index(drop=True)
rng = np.random.default_rng(config.SEED); n = len(df); keep = int(round(0.8*n))
samples = [np.sort(rng.choice(n, keep, replace=False)) for _ in range(300)]
for name, dims in designs.items():
    config.DIMENSIONS = dims
    for k in range(2, 7):
        full, dist = stability.group_tehsils(df, k)
        sizes = pd.Series(full).value_counts().sort_index().tolist()
        if len(sizes) < 3: 
            if k == 2: pass
            else: continue
        aris = [adjusted_rand_score(full[i], stability.group_tehsils(df.iloc[i].reset_index(drop=True), k)[0]) for i in samples]
        print(f"{name:28s} k{k} {sizes} sil {silhouette_score(dist, full, metric='precomputed'):.3f} ARI {np.mean(aris):.3f} p05 {np.percentile(aris,5):.3f}", flush=True)
        if len(sizes) == 3: break
config.DIMENSIONS = base
