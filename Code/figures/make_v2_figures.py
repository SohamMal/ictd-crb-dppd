"""
New figures for the version 2 final deck (report/final_deck_outline_version2.md).

f20_toy_merge.png : average-linkage clustering on 6 real tehsils, using the real
                    dimension-balanced Gower distances (outputs/grouping/dist_baseline.csv).

Run:  python Code/figures/make_v2_figures.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "figures" / "final"
DIST = ROOT / "outputs" / "grouping" / "dist_baseline.csv"
GROUPS = ROOT / "outputs" / "grouping" / "FROZEN_groups.csv"

INK, INK_2 = "#1f1a17", "#6b6560"
EMBER = "#e4572e"
GROUP = {"Central": "#2a78d6", "South-west": "#eb6834"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": INK_2,
    "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 200,
    "savefig.bbox": "tight", "savefig.facecolor": "white",
})

NAMES = ["Phagwara", "Jalandhar - I", "Adampur", "Lehra", "Abohar", "Fazilka"]
SHORT = {"Jalandhar - I": "Jalandhar-I"}


def toy_merge():
    d = pd.read_csv(DIST, index_col=0).loc[NAMES, NAMES]
    grp = pd.read_csv(GROUPS).set_index("lgd_tehsil_name")["group"]
    labels = [SHORT.get(n, n) for n in NAMES]
    Z = linkage(squareform(d.values, checks=False), "average")
    print("toy merges (i, j, height, size):")
    print(np.round(Z, 3))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={"width_ratios": [1, 1.15]})

    # Left: distance table as a heatmap
    v = d.values.copy()
    mask = np.eye(len(NAMES), dtype=bool)
    shown = np.where(mask, np.nan, v)
    a1.imshow(shown, cmap="Greys_r", vmin=0.1, vmax=0.65)
    for i in range(len(NAMES)):
        for j in range(len(NAMES)):
            if i == j:
                a1.text(j, i, "–", ha="center", va="center", color=INK_2, fontsize=12)
                continue
            col = "white" if v[i, j] < 0.33 else INK
            a1.text(j, i, f"{v[i, j]:.2f}", ha="center", va="center", fontsize=12, color=col,
                    fontweight="bold" if v[i, j] < 0.23 else "normal")
    a1.set_xticks(range(len(NAMES)), labels, rotation=35, ha="right")
    a1.set_yticks(range(len(NAMES)), labels)
    for t, n in zip(a1.get_yticklabels(), NAMES):
        t.set_color(GROUP[grp[n]])
    for t, n in zip(a1.get_xticklabels(), NAMES):
        t.set_color(GROUP[grp[n]])
    for s in a1.spines.values():
        s.set_visible(False)
    a1.tick_params(length=0)
    a1.set_title("Gower distance (0 = identical)", fontsize=14, color=INK, loc="left")

    # Right: dendrogram with merge order
    dn = dendrogram(Z, labels=labels, ax=a2, color_threshold=0, above_threshold_color=INK_2,
                    leaf_font_size=13)
    plt.setp(a2.get_xticklabels(), rotation=25, ha="right")
    for t in a2.get_xticklabels():
        name = NAMES[labels.index(t.get_text())]
        t.set_color(GROUP[grp[name]])
    a2.set_ylabel("distance at merge")
    a2.set_ylim(0, 0.5)
    # label each merge with its step number at the top of its bracket
    order = np.argsort([max(ys[1], ys[2]) for ys in dn["dcoord"]])
    for step, k in enumerate(order, start=1):
        xs, ys = dn["icoord"][k], dn["dcoord"][k]
        x, y = (xs[1] + xs[2]) / 2, ys[1]
        a2.plot(x, y, "o", ms=20, color=EMBER, zorder=3)
        a2.text(x, y, str(step), ha="center", va="center", color="white", fontsize=12,
                fontweight="bold", zorder=4)
        a2.text(x + 2.2, y + 0.012, f"{y:.2f}", fontsize=11, color=INK_2)
    a2.axhline(0.38, ls="--", color=EMBER, lw=1.2)
    a2.text(a2.get_xlim()[1], 0.39, "cut → 2 groups", ha="right", va="bottom", color=EMBER, fontsize=11)
    a2.set_title("Merge the closest pair, repeat", fontsize=14, color=INK, loc="left")

    fig.tight_layout(w_pad=3)
    fig.savefig(OUT / "f20_toy_merge.png")
    plt.close(fig)


if __name__ == "__main__":
    toy_merge()
