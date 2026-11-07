"""
Step 6b: one-factor-at-a-time sensitivity of the chosen grouping (candidate B).

Change one design choice, rerun the full grouping procedure (stability.group_tehsils)
at the same k, and compare with the baseline groups using the ARI.
ARI 1 = identical groups; lower = the choice matters and must be defended.

Run:  python Code/grouping/sensitivity.py
Out:  outputs/grouping/sensitivity_table.csv,
      sensitivity_labels.csv (per scenario, each tehsil's group matched to the baseline numbering;
      used by Code/pd/pd_validate.py for the alternative-grouping PD run)
"""

import copy

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

import config
from stability import group_tehsils

K_CHOSEN = 3  # 3 regions: central / south-west / foothills
SOIL_NEAR_CONSTANT = [
    "dominant_soil_depth",
    "dominant_salinity",
    "dominant_erosion",
]


def replace_column(dims, old, new):
    dims = copy.deepcopy(dims)
    for cols in dims.values():
        for i, (c, kind) in enumerate(cols):
            if c == old:
                cols[i] = (new, kind)
    return dims


def scenarios(df):
    """Yield (name, df, dimensions, weights) for each one-factor change."""
    base = config.DIMENSIONS
    names = list(base)
    equal = {d: 1.0 for d in names}

    # Groundwater 2025 scenario removed 2026-10-07: 2022 is final, 2025 not used.

    if "zone" in base:
        old = {k: v for k, v in base.items() if k != "zone"}
        old["terrain"] = [("elevation_log1p", "numeric"), ("slope_log1p", "numeric")]
        yield "terrain_instead_of_zone (pre-2026-10-06 design)", df, old, None

    for d in names:
        for f in (1.15, 0.85):
            w = dict(equal)
            w[d] = f
            yield f"weight_{d}_x{f}", df, base, w

    for d in names:
        dims = {k: v for k, v in base.items() if k != d}
        yield f"drop_{d}", df, dims, None

    soil = [(c, k) for c, k in base["soil"] if c not in SOIL_NEAR_CONSTANT]
    yield "soil_without_near_constant", df, {**base, "soil": soil}, None


def align(base_labels, new_labels):
    """Renumber the new groups to their best-overlapping baseline group."""
    mapping = {}
    for g in np.unique(new_labels):
        mapping[g] = pd.Series(base_labels[new_labels == g]).mode()[0]
    return np.array([mapping[g] for g in new_labels])


def moved_tehsils(base_labels, new_labels, names):
    """Tehsils whose group changed, after matching each new group to its best-overlapping baseline group."""
    aligned = align(base_labels, new_labels)
    return [n for n, a, b in zip(names, aligned, base_labels) if a != b]


def main():
    df = pd.read_csv(config.MASTER_CSV)
    df = df[~df[config.NAME_COL].isin(config.OUTLIERS)].reset_index(drop=True)
    names = df[config.NAME_COL].tolist()

    original = (config.DIMENSIONS, config.WEIGHTS)
    base_labels, _ = group_tehsils(df, K_CHOSEN)

    rows = []
    aligned = {"baseline": base_labels}
    for name, sdf, dims, weights in scenarios(df):
        config.DIMENSIONS, config.WEIGHTS = dims, weights
        try:
            labels, _ = group_tehsils(sdf, K_CHOSEN)
        finally:
            config.DIMENSIONS, config.WEIGHTS = original
        moved = moved_tehsils(base_labels, labels, names)
        aligned[name] = align(base_labels, labels)
        rows.append(
            {
                "scenario": name,
                "group_sizes": "/".join(
                    str(s) for s in pd.Series(labels).value_counts().sort_index()
                ),
                "ari_vs_baseline": round(adjusted_rand_score(base_labels, labels), 3),
                "n_moved": len(moved),
                "moved": "; ".join(moved),
            }
        )

    table = pd.DataFrame(rows).set_index("scenario")
    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(config.OUT_DIR / "sensitivity_table.csv")
    pd.DataFrame({config.NAME_COL: names, **aligned}).to_csv(
        config.OUT_DIR / "sensitivity_labels.csv", index=False)
    base_sizes = "/".join(str(s) for s in pd.Series(base_labels).value_counts().sort_index())
    print(f"Baseline (k={K_CHOSEN}): {base_sizes}")
    with pd.option_context("display.max_colwidth", 90, "display.width", 200):
        print(table.to_string())
    return table


if __name__ == "__main__":
    main()
