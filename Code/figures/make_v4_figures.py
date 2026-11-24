"""
Figures for the final deck v4.

v4_gower_corr_matrix.png : correlation-matrix style view of the real dimension-balanced Gower distances
                           (lower triangle, every cell annotated) for 12 example tehsils, 4 per peer group.

Run:  python Code/figures/make_v4_figures.py
In:   outputs/grouping/dist_baseline.csv (97 x 97), outputs/grouping/FROZEN_groups.csv
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GRP = ROOT / "outputs" / "grouping"
OUT = ROOT / "outputs" / "figures" / "final"

INK_2 = "#6b6560"
GROUP = {"Central": "#2a78d6", "South-west": "#eb6834", "Foothills": "#1baf7a"}
EXAMPLES = {"Central": ["Phagwara", "Adampur", "Jalandhar - I", "Lehra"],
            "South-west": ["Abohar", "Fazilka", "Bathinda", "Mansa"],
            "Foothills": ["Pathankot", "Hoshiarpur", "Anandpur Sahib", "Nangal"]}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "savefig.dpi": 200,
                     "savefig.bbox": "tight", "savefig.facecolor": "white"})


def gower_corr_matrix():
    d = pd.read_csv(GRP / "dist_baseline.csv", index_col=0)
    grp = pd.read_csv(GRP / "FROZEN_groups.csv").set_index("lgd_tehsil_name")["group"]
    names = [n for g in EXAMPLES for n in EXAMPLES[g]]
    assert all(grp[n] == g for g in EXAMPLES for n in EXAMPLES[g])
    m = d.loc[names, names].values
    k = len(names)
    show = np.where(np.tril(np.ones((k, k), bool)), m, np.nan)

    fig, ax = plt.subplots(figsize=(9.6, 8.2))
    im = ax.imshow(show, cmap="YlGnBu_r", vmin=0, vmax=0.7)
    for i in range(k):
        for j in range(i + 1):
            v = m[i, j]
            ax.text(j, i, "0" if i == j else f"{v:.2f}", ha="center", va="center", fontsize=11,
                    color="white" if v < 0.3 else "#1f1a17", fontweight="bold" if i != j and v < 0.3 else None)
    # group separators (inside the triangle only)
    for b in (4, 8):
        ax.plot([-0.5, b - 0.5], [b - 0.5, b - 0.5], color="white", lw=3)
        ax.plot([b - 0.5, b - 0.5], [b - 0.5, k - 0.5], color="white", lw=3)
    labels = [n.replace("Jalandhar - I", "Jalandhar-I") for n in names]
    ax.set_xticks(range(k), labels, rotation=45, ha="right")
    ax.set_yticks(range(k), labels)
    for t, n in zip(ax.get_xticklabels(), names):
        t.set_color(GROUP[grp[n]])
    for t, n in zip(ax.get_yticklabels(), names):
        t.set_color(GROUP[grp[n]])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("Gower distance (0 = identical, 1 = most different)", color=INK_2)
    cb.outline.set_visible(False)
    for i, (g, c) in enumerate(GROUP.items()):
        ax.text(k - 0.5, 0.2 + i * 0.75, f"■ {g}", color=c, ha="right", fontsize=13, fontweight="bold")
    fig.savefig(OUT / "v4_gower_corr_matrix.png")
    plt.close(fig)


if __name__ == "__main__":
    gower_corr_matrix()
    print("saved", OUT / "v4_gower_corr_matrix.png")
