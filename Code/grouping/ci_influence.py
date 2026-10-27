"""
How much does cropping intensity (CI) shape the frozen grouping? (2026-10-07)

1. Rerun the full procedure WITHOUT the CI dimension (Gower -> HAC -> cut ->
   small-group merge -> bootstrap consensus) and compare with FROZEN_groups.csv.
2. Separation power per dimension under the frozen groups: mean between-group
   distance / mean within-group distance on that dimension alone (1 = no separation).
3. Correlation of all pairwise distances with vs without CI.

Run:  python Code/grouping/ci_influence.py
Out:  outputs/grouping/ci_influence_dimension_separation.csv
      outputs/grouping/ci_influence_groups_without_ci.csv
"""

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

import config
import gower
from stability import group_tehsils, match_to_full

K = 4


def consensus_labels(df, k):
    """Full-data labels and bootstrap-consensus labels (same rules as stability.py)."""
    full, _ = group_tehsils(df, k)
    groups = set(np.unique(full))
    rng = np.random.default_rng(config.SEED)
    n = len(df)
    keep = int(round(config.BOOTSTRAP_FRACTION * n))
    votes = [[] for _ in range(n)]
    for _ in range(config.BOOTSTRAP_RUNS):
        idx = np.sort(rng.choice(n, keep, replace=False))
        sub, _ = group_tehsils(df.iloc[idx].reset_index(drop=True), k)
        matched = match_to_full(full[idx], sub)
        if set(matched) == groups:
            for j, i in enumerate(idx):
                votes[i].append(matched[j])
    return np.array([pd.Series(v).mode()[0] if v else full[i] for i, v in enumerate(votes)])


def main():
    df = pd.read_csv(config.MASTER_CSV)
    df = df[~df[config.NAME_COL].isin(config.OUTLIERS)].reset_index(drop=True)
    names = df[config.NAME_COL]
    frozen = pd.read_csv(config.OUT_DIR / "FROZEN_groups.csv").set_index(config.NAME_COL)
    g = frozen.loc[names, "group"].to_numpy()

    # 2. separation power per dimension (frozen groups)
    _, per_dim = gower.gower_matrix(df, config.DIMENSIONS, config.WEIGHTS, config.RANGE_EXCLUDE)
    same = g[:, None] == g[None, :]
    off = ~np.eye(len(g), dtype=bool)
    rows = []
    for dim, d in per_dim.items():
        within = d[same & off].mean()
        between = d[~same].mean()
        rows.append({"dimension": dim, "mean_within": round(within, 4),
                     "mean_between": round(between, 4), "separation_ratio": round(between / within, 3)})
    sep = pd.DataFrame(rows).sort_values("separation_ratio", ascending=False)

    # 3. distance correlation with vs without CI
    dims_no_ci = {k: v for k, v in config.DIMENSIONS.items() if k != "cropping_intensity"}
    d_all, _ = gower.gower_matrix(df, config.DIMENSIONS, None, config.RANGE_EXCLUDE)
    d_no, _ = gower.gower_matrix(df, dims_no_ci, None, config.RANGE_EXCLUDE)
    iu = np.triu_indices(len(df), 1)
    r = np.corrcoef(d_all[iu], d_no[iu])[0, 1]

    # 1. full procedure without CI, consensus
    original = config.DIMENSIONS
    config.DIMENSIONS = dims_no_ci
    try:
        cons = consensus_labels(df, K)
    finally:
        config.DIMENSIONS = original
    mapping = {c: pd.Series(g[cons == c]).mode()[0] for c in np.unique(cons)}
    aligned = np.array([mapping[c] for c in cons])
    out = pd.DataFrame({"group_frozen": g, "group_without_ci": aligned}, index=names)
    out["changed"] = out.group_frozen != out.group_without_ci
    out["borderline_frozen"] = frozen.loc[names, "borderline"].to_numpy()

    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    sep.to_csv(config.OUT_DIR / "ci_influence_dimension_separation.csv", index=False)
    out.to_csv(config.OUT_DIR / "ci_influence_groups_without_ci.csv")

    print("Separation power per dimension (between / within, frozen groups):")
    print(sep.to_string(index=False))
    print(f"\nCorrelation of pairwise distances with vs without CI: {r:.3f}")
    print(f"\nWithout CI (consensus, k={K}): sizes {pd.Series(aligned).value_counts().to_dict()}")
    print(f"ARI vs frozen: {adjusted_rand_score(g, aligned):.3f}")
    ch = out[out.changed]
    print(f"Changed: {len(ch)}")
    if len(ch):
        print(ch.to_string())
    print("\nCI median by frozen group:", df.groupby(g)["CI_3yr_pooled"].median().round(1).to_dict())


if __name__ == "__main__":
    main()
