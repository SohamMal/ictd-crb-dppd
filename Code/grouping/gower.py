"""
Dimension-balanced Gower distance between tehsils.

Step 2: per column, a difference in [0, 1]
    numeric      |a - b| / range   (range = max - min over tehsils not in range_exclude;
                                    capped at 1 for excluded extreme tehsils)
    categorical  0 if same value, 1 if different
    missing      that column is skipped for that pair
Step 3: average the columns inside each dimension, then take the weighted
    mean across dimensions (equal weights by default).

Run:  python Code/grouping/gower.py
Out:  outputs/grouping/dist_baseline.csv  (97 x 97, labelled by tehsil name)
"""

import numpy as np
import pandas as pd

import config


def column_distance(values, kind, range_mask):
    """n x n matrix of per-pair differences for one column (NaN where missing)."""
    if kind == "numeric":
        x = values.astype(float).to_numpy()
        ref = x[range_mask]
        span = np.nanmax(ref) - np.nanmin(ref)
        if span == 0:
            d = np.zeros((len(x), len(x)))
        else:
            d = np.minimum(np.abs(x[:, None] - x[None, :]) / span, 1.0)
        d[np.isnan(x)] = np.nan
        d[:, np.isnan(x)] = np.nan
        return d

    if kind == "categorical":
        v = values.to_numpy(dtype=object)
        missing = pd.isna(values).to_numpy()
        d = (v[:, None] != v[None, :]).astype(float)
        d[missing] = np.nan
        d[:, missing] = np.nan
        return d

    raise ValueError(f"Unknown kind: {kind}")


def dimension_distances(df, dimensions, range_exclude=()):
    """Return {dimension: n x n matrix}, each the mean of its columns' differences."""
    range_mask = ~df[config.NAME_COL].isin(range_exclude).to_numpy()
    out = {}
    for dim, cols in dimensions.items():
        stack = np.stack(
            [column_distance(df[col], kind, range_mask) for col, kind in cols]
        )
        out[dim] = np.nanmean(stack, axis=0)
    return out


def gower_matrix(df, dimensions, weights=None, range_exclude=()):
    """Weighted mean of dimension distances -> (n x n distance matrix, per-dimension dict)."""
    per_dim = dimension_distances(df, dimensions, range_exclude)
    names = list(dimensions)
    if weights is None:
        weights = {d: 1.0 / len(names) for d in names}
    w = np.array([weights[d] for d in names], dtype=float)
    w = w / w.sum()
    dist = sum(wi * per_dim[d] for wi, d in zip(w, names))
    if np.isnan(dist).any():
        raise ValueError("A whole dimension is missing for some pair of tehsils.")
    return dist, per_dim


def main():
    df = pd.read_csv(config.MASTER_CSV)
    needed = [c for cols in config.DIMENSIONS.values() for c, _ in cols]
    missing_cols = [c for c in needed if c not in df.columns]
    if missing_cols:
        raise KeyError(f"Columns not in master: {missing_cols}")

    dist, per_dim = gower_matrix(
        df, config.DIMENSIONS, config.WEIGHTS, config.RANGE_EXCLUDE
    )

    # Sanity checks: zero diagonal, symmetric, within [0, 1].
    assert np.allclose(np.diag(dist), 0)
    assert np.allclose(dist, dist.T)
    assert dist.min() >= 0 and dist.max() <= 1

    names = df[config.NAME_COL].tolist()
    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = config.OUT_DIR / "dist_baseline.csv"
    pd.DataFrame(dist, index=names, columns=names).to_csv(out)

    print(f"Tehsils: {len(names)} | dimensions: {list(config.DIMENSIONS)}")
    print(f"Saved: {out}")
    return df, dist, per_dim


if __name__ == "__main__":
    main()
