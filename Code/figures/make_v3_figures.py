"""
New figures for the version 3 final deck (Code/figures/make_final_deck_v3.py).

v3_distance_matrix.png : the real 97 x 97 dimension-balanced Gower matrix, tehsils ordered by group and tree.
v3_silhouette.png      : left half of fig_D (silhouette by k), cropped.
v3_bootstrap.png       : right half of fig_D (bootstrap ARI by k), cropped.
v3_ceew_test.png       : detector tested on CEEW field visits + Planet judge, Jalandhar 2021 (report Table 5).
v3_dev_ladder.png      : how the detector improved during development (report §4.2, judge A, cut-off 0.5).
v3_fence.png           : how the PD fence is drawn, real South-west group, 2020-24 mean burnt share.

Run:  python Code/figures/make_v3_figures.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "figures" / "final"
FIG = ROOT / "outputs" / "figures"
GRP = ROOT / "outputs" / "grouping"
BURN = ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv"

INK, INK_2 = "#1f1a17", "#6b6560"
EMBER, GOOD, GREY = "#e4572e", "#0f7b4a", "#bdb5b0"
GROUP = {"Central": "#2a78d6", "South-west": "#eb6834", "Foothills": "#1baf7a", "Outlier": "#9a9a9a"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": INK_2,
    "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 200,
    "savefig.bbox": "tight", "savefig.facecolor": "white",
})


def distance_matrix():
    d = pd.read_csv(GRP / "dist_baseline.csv", index_col=0)
    grp = pd.read_csv(GRP / "FROZEN_groups.csv").set_index("lgd_tehsil_name")["group"]
    order = []
    for g in ["Central", "South-west", "Foothills", "Outlier"]:
        names = [n for n in d.index if grp[n] == g]
        if len(names) > 2:
            sub = d.loc[names, names].values
            Z = linkage(squareform(sub, checks=False), "average")
            names = [names[i] for i in leaves_list(Z)]
        order += names
    m = d.loc[order, order].values
    fig, ax = plt.subplots(figsize=(8.2, 7.4))
    im = ax.imshow(m, cmap="magma", vmin=0, vmax=0.7)
    # group bands
    start = 0
    for g in ["Central", "South-west", "Foothills", "Outlier"]:
        k = sum(grp[n] == g for n in order)
        ax.add_patch(plt.Rectangle((start - 0.5, start - 0.5), k, k, fill=False, ec="white", lw=1.6))
        ax.add_patch(plt.Rectangle((-4.5, start - 0.5), 3, k, color=GROUP[g], clip_on=False))
        ax.add_patch(plt.Rectangle((start - 0.5, -4.5), k, 3, color=GROUP[g], clip_on=False))
        if k > 3:
            ax.text(-6, start + k / 2, f"{g}\n({k})", ha="right", va="center", fontsize=12, color=GROUP[g],
                    fontweight="bold")
        start += k
    ax.set_xlim(-4.6, len(order) - 0.5)
    ax.set_ylim(len(order) - 0.5, -4.6)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("Gower distance (0 = identical)")
    fig.savefig(OUT / "v3_distance_matrix.png")
    plt.close(fig)


def split_fig_d():
    im = Image.open(FIG / "fig_D_choosing_k.png")
    w, h = im.size
    im.crop((0, 0, w // 2, h)).save(OUT / "v3_silhouette.png")
    im.crop((w // 2, 0, w, h)).save(OUT / "v3_bootstrap.png")


def ceew_test():
    # report Table 5 (outputs/planet/jalandhar_walker_results_pre1_jump.csv, jalandhar_cutoff_sweep.csv)
    labels = ["Old index\n(midterm)", "New detector\ncut-off 0.5", "New detector\ncut-off 0.8"]
    kept = [257 / 262, 145 / 262, 89 / 262]
    false = [28 / 95, 2 / 95, 1 / 95]
    cols = [GREY, EMBER, "#b8401f"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.6))
    for ax, vals, raw, t in [(a2, kept, ["257/262", "145/262", "89/262"], "Burnt fields still called burnt"),
                             (a1, false, ["28/95", "2/95", "1/95"], "Unburnt fields wrongly called burnt")]:
        b = ax.bar(range(3), vals, color=cols, width=0.62)
        for i, (v, r) in enumerate(zip(vals, raw)):
            ax.text(i, v + 0.02, f"{v:.0%}\n({r})", ha="center", va="bottom", fontsize=12, color=INK)
        ax.set_xticks(range(3), labels, fontsize=11)
        ax.set_ylim(0, 1.18)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_title(t, loc="left", fontsize=14, color=INK)
    fig.tight_layout(w_pad=3)
    fig.savefig(OUT / "v3_ceew_test.png")
    plt.close(fig)


def dev_ladder():
    # report §4.2: Jalandhar 2021, judge A (Planet rule), cut-off 0.5
    steps = ["Old index\n(any flagged look)", "Forest, 'before'\n= 20-day median", "'before' = last\nclear look",
             "candidate =\nlargest jump"]
    kept = [63, 36, 47, 51]
    false = ["23/32", "2–3/32", "2–3/32", "3/32"]
    cols = [GREY, "#f2b8a2", "#ec8a66", EMBER]
    fig, ax = plt.subplots(figsize=(10, 4.4))
    ax.bar(range(4), kept, color=cols, width=0.62)
    for i, (k, f) in enumerate(zip(kept, false)):
        ax.text(i, k + 1.2, f"{k}/63", ha="center", va="bottom", fontsize=14, fontweight="bold", color=INK)
        ax.text(i, 3, f"false alarms\n{f}", ha="center", va="bottom", fontsize=11,
                color="white" if i > 1 else INK, fontweight="bold" if i == 0 else "normal")
    ax.set_xticks(range(4), steps, fontsize=12)
    ax.set_ylim(0, 75)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_title("Planet-judged burns kept (of 63), Jalandhar 2021", loc="left", fontsize=14, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "v3_dev_ladder.png")
    plt.close(fig)


def fence():
    b = pd.read_csv(BURN)
    b = b[b.year.between(2020, 2024) & (b.group == "South-west")]
    mean = b.groupby("lgd_tehsil_name")["burnt_share"].mean().sort_values()
    c = 0.1 * mean.median()
    lg = np.log(mean + c)
    q1, q3 = np.percentile(lg, [25, 75])
    f = q1 - 1.5 * (q3 - q1)
    back = lambda v: np.exp(v) - c  # noqa: E731
    print(f"SW fence {back(f):.3f}, median {mean.median():.3f}, Q1 {back(q1):.3f}, Q3 {back(q3):.3f}")
    fig, ax = plt.subplots(figsize=(11, 3.6))
    y = np.zeros(len(mean)) + np.random.default_rng(1).uniform(-0.12, 0.12, len(mean))
    ax.add_patch(plt.Rectangle((back(q1), -0.3), back(q3) - back(q1), 0.6, color="#fbe0d6", zorder=0))
    ax.axvline(mean.median(), color=INK_2, lw=1.5)
    ax.axvline(back(f), color=INK, ls="--", lw=1.5)
    ax.scatter(mean.values, y, s=70, color=GROUP["South-west"], ec="white", zorder=3)
    ab = mean["Abohar"]
    ax.scatter([ab], [0], s=160, facecolor="none", ec=GOOD, lw=2.5, zorder=4)
    ax.text(ab, -0.42, f"Abohar {ab:.2f}", ha="center", color=GOOD, fontsize=13, fontweight="bold")
    ax.text(back(f) * 0.985, 0.42, f"fence {back(f):.2f}", ha="right", fontsize=12, color=INK)
    ax.text(mean.median() * 1.012, 0.42, f"median {mean.median():.2f}", ha="left", fontsize=12, color=INK_2)
    ax.text((back(q1) + back(q3)) / 2, -0.42, "middle half (Q1–Q3)", ha="center", fontsize=11, color="#b8401f",
            bbox=dict(fc="white", ec="none", pad=1))
    ax.annotate("", xy=(back(f), 0.32), xytext=(back(q1), 0.32),
                arrowprops=dict(arrowstyle="<->", color=INK_2))
    ax.text((back(f) + back(q1)) / 2, 0.22, "1.5 × IQR", ha="center", fontsize=11, color=INK_2)
    ax.set_xscale("log")
    ax.set_xlim(0.28, 1.0)
    ax.set_xticks([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], ["0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"])
    ax.minorticks_off()
    ax.set_ylim(-0.55, 0.55)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Mean burnt share 2020–24, South-west group, 18 tehsils (log scale)")
    fig.savefig(OUT / "v3_fence.png")
    plt.close(fig)


if __name__ == "__main__":
    distance_matrix()
    split_fig_d()
    ceew_test()
    dev_ladder()
    fence()
