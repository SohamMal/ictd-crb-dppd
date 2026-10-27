"""
Step 5: how well separated are the groups at each cut? (silhouette)

For each tehsil:  a = average distance to the other members of its own group,
                  b = average distance to the members of the nearest other group,
                  s = (b - a) / max(a, b)   in [-1, 1].
s near 1: clearly in the right group; near 0: on the border; < 0: closer to
another group than to its own. A one-tehsil group gets s = 0 (scikit-learn rule).
The overall score is the mean s over all tehsils.

Run:  python Code/grouping/evaluate.py      (after cluster.py)
Out:  outputs/grouping/silhouette_by_k.csv
      outputs/grouping/silhouette_per_tehsil.csv
"""

import pandas as pd
from sklearn.metrics import silhouette_samples

import config
import gower
from cluster import K_RANGE, build_tree, cut_tree


def silhouette_table(dist, labels):
    """Overall and per-tehsil silhouettes for every labelling column."""
    summary, per_tehsil = [], {}
    for col in labels.columns:
        s = pd.Series(
            silhouette_samples(dist, labels[col], metric="precomputed"),
            index=labels.index,
        )
        per_tehsil[col] = s
        sizes = labels[col].value_counts().sort_index()
        summary.append(
            {
                "cut": col,
                "group_sizes": "/".join(str(n) for n in sizes),
                "silhouette_mean": round(s.mean(), 3),
                "n_negative": int((s < 0).sum()),
                "smallest_group": int(sizes.min()),
                "groups_of_10_or_more": int((sizes >= 10).sum()),
            }
        )
    return pd.DataFrame(summary).set_index("cut"), pd.DataFrame(per_tehsil)


def main():
    df, dist, _ = gower.main()
    names = df[config.NAME_COL].tolist()
    labels = cut_tree(build_tree(dist), names, K_RANGE)

    summary, per_tehsil = silhouette_table(dist, labels)
    summary.to_csv(config.OUT_DIR / "silhouette_by_k.csv")
    per_tehsil.index.name = config.NAME_COL
    per_tehsil.round(4).to_csv(config.OUT_DIR / "silhouette_per_tehsil.csv")
    print(summary.to_string())
    return labels, summary, per_tehsil


if __name__ == "__main__":
    main()
