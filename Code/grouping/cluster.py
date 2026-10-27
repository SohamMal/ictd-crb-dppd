"""
Step 4: average-linkage hierarchical clustering (HAC) on the Gower distances.

Start with every tehsil as its own group, repeatedly merge the two groups with
the smallest average pairwise distance, and record the merge tree (dendrogram).
Cutting the tree at different heights gives k = 2..8 groups.

Run:  python Code/grouping/cluster.py
Out:  outputs/grouping/dendrogram_baseline.png
      outputs/grouping/labels_by_k.csv   (tehsil x k group labels)
      outputs/grouping/sizes_by_k.csv    (group sizes per k, largest first)
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import squareform

import config
import gower

K_RANGE = range(2, 9)


def build_tree(dist):
    """Average-linkage merge tree from a square distance matrix."""
    return linkage(squareform(dist, checks=True), method="average")


def cut_tree(tree, names, k_range=K_RANGE):
    """Group label per tehsil for each k (labels numbered by group size, 1 = largest)."""
    labels = {}
    for k in k_range:
        raw = pd.Series(fcluster(tree, t=k, criterion="maxclust"), index=names)
        order = raw.value_counts().index
        labels[f"k{k}"] = raw.map({g: i + 1 for i, g in enumerate(order)})
    return pd.DataFrame(labels)


def main():
    df, dist, _ = gower.main()
    names = df[config.NAME_COL].tolist()
    tree = build_tree(dist)
    labels = cut_tree(tree, names)

    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    labels.index.name = config.NAME_COL
    labels.to_csv(config.OUT_DIR / "labels_by_k.csv")

    sizes = {
        k: "/".join(str(s) for s in labels[k].value_counts().sort_index())
        for k in labels.columns
    }
    pd.Series(sizes, name="group_sizes").to_csv(config.OUT_DIR / "sizes_by_k.csv")

    fig, ax = plt.subplots(figsize=(22, 8))
    dendrogram(tree, labels=names, leaf_font_size=7, color_threshold=None, ax=ax)
    ax.set_ylabel("Average Gower distance at merge")
    ax.set_title("Punjab tehsils: average-linkage HAC (baseline, 6 dimensions)")
    fig.tight_layout()
    fig.savefig(config.OUT_DIR / "dendrogram_baseline.png", dpi=150)

    for k, s in sizes.items():
        print(f"{k}: {s}")
    return tree, labels


if __name__ == "__main__":
    main()
