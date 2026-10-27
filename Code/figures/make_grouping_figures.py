"""
Report figures for the frozen homogeneous grouping (Stage 2, Step 2).

Reads only frozen outputs, so the figures always match the numbers in the report.

Fig A  group map            fig_A_group_map.png
Fig B  dendrogram           fig_B_dendrogram.png
Fig C  group profiles       fig_C_group_profiles.png
Fig D  choosing k           fig_D_choosing_k.png
Fig E  sensitivity (OFAT)   fig_E_sensitivity.png
Fig F  rice calibration     fig_F_rice_calibration.png

Run:  python Code/figures/make_grouping_figures.py
Out:  outputs/figures/
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform

ROOT = Path(__file__).resolve().parents[2]
GROUPING = ROOT / "outputs" / "grouping"
OUT = ROOT / "outputs" / "figures"
POLYGONS = ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg"
MASTER = ROOT / "Data" / "punjab_homogeneous_grouping_master_transformed.csv"
CHEN_VS_OFFICIAL = ROOT / "Data" / "Rice" / "official" / "chen_vs_official_by_district.csv"

# Categorical slots 1-3 of the validated reference palette (all-pairs safe for maps).
COLORS = {
    "Central": "#2a78d6",
    "South-west": "#eb6834",
    "Foothills": "#1baf7a",
    "Outlier": "#a3a29c",
}
GROUP_ORDER = ["Central", "South-west", "Foothills"]
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": INK_2,
    "axes.labelcolor": INK_2,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def load_groups():
    g = pd.read_csv(GROUPING / "FROZEN_groups.csv")
    g["label"] = np.where(g["outlier"], "Outlier", g["group"])
    return g


def legend_handles(include_outlier=True):
    keys = GROUP_ORDER + (["Outlier"] if include_outlier else [])
    return [Patch(facecolor=COLORS[k], edgecolor="white", label=k) for k in keys]


def fig_a_map(groups):
    poly = gpd.read_file(POLYGONS)[["lgd_tehsil_code", "geometry"]]
    gdf = poly.merge(groups, on="lgd_tehsil_code", how="left", validate="1:1")
    assert gdf["label"].notna().all(), "tehsil without a group"
    gdf = gdf.to_crs(32643)  # UTM 43N: metres, undistorted shapes

    fig, ax = plt.subplots(figsize=(7, 7.5))
    gdf.plot(ax=ax, color=gdf["label"].map(COLORS), edgecolor="white", linewidth=0.6)

    border = gdf[gdf["borderline"]]
    border.plot(ax=ax, facecolor="none", edgecolor=INK, linewidth=1.2, hatch="////")
    for _, r in pd.concat([border, gdf[gdf["outlier"]]]).iterrows():
        p = r.geometry.representative_point()
        ax.annotate(
            r["lgd_tehsil_name"], (p.x, p.y), xytext=(8, 8), textcoords="offset points",
            fontsize=8, color=INK,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85),
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.6),
        )

    counts = groups["label"].value_counts()
    handles = [
        Patch(facecolor=COLORS[k], edgecolor="white", label=f"{k} ({counts[k]})")
        for k in GROUP_ORDER + ["Outlier"]
    ]
    handles.append(Patch(facecolor="white", edgecolor=INK, hatch="////",
                         label="Borderline (switch rate > 20%)"))
    ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=8)
    ax.set_axis_off()
    ax.set_title("Homogeneous groups of Punjab tehsils (frozen v4)", loc="left",
                 color=INK, fontsize=11)
    fig.savefig(OUT / "fig_A_group_map.png")
    plt.close(fig)


def fig_b_dendrogram(groups):
    dist = pd.read_csv(GROUPING / "dist_baseline.csv", index_col=0)
    names = dist.index.tolist()
    tree = linkage(squareform(dist.to_numpy(), checks=False), method="average")
    label_of = groups.set_index("lgd_tehsil_name")["label"].reindex(names).to_numpy()

    # Colour a branch by its group only when every tehsil below it shares that group.
    n = len(names)
    members = {i: {i} for i in range(n)}
    for j, (a, b, *_rest) in enumerate(tree):
        members[n + j] = members[int(a)] | members[int(b)]

    def link_color(node):
        labs = {label_of[i] for i in members[node]}
        return COLORS[labs.pop()] if len(labs) == 1 else INK_2

    # 3 groups + 1 outlier = the 4-cluster cut of the tree.
    cut = (tree[-4, 2] + tree[-3, 2]) / 2

    fig, ax = plt.subplots(figsize=(18, 6))
    d = dendrogram(tree, labels=names, leaf_font_size=6.5, link_color_func=link_color, ax=ax)
    for tick in ax.get_xticklabels():
        tick.set_color(COLORS[label_of[names.index(tick.get_text())]])
    ax.axhline(cut, color=INK, linestyle="--", linewidth=1)
    ax.text(ax.get_xlim()[1], cut, "  cut: 3 groups + outlier", va="bottom", ha="right",
            fontsize=8, color=INK)
    ax.set_ylabel("Average Gower distance at merge")
    ax.spines["bottom"].set_visible(False)
    ax.legend(handles=legend_handles(), loc="lower right", bbox_to_anchor=(1, 1.0), frameon=False, ncol=4)
    ax.set_title("How tehsils merge into groups (average-linkage, dimension-balanced Gower)",
                 loc="left", color=INK, fontsize=11)
    assert len(d["leaves"]) == n
    fig.savefig(OUT / "fig_B_dendrogram.png")
    plt.close(fig)


def fig_c_profiles(groups):
    m = pd.read_csv(MASTER).merge(groups[["lgd_tehsil_code", "label"]], on="lgd_tehsil_code")
    m = m[m["label"] != "Outlier"]
    numeric = [
        ("rice_share_2022_cal", "Rice share of tehsil area\n(Chen 2022, calibrated)", "{:.0%}"),
        ("mean_monsoon_rainfall_mm", "Mean monsoon rainfall (mm)", "{:.0f}"),
        ("mean_extraction_pct_2022", "Groundwater extraction 2022\n(% of recharge)", "{:.0f}%"),
    ]
    zones = {
        "aesr_share_9_1": "9.1 moist semi-arid plain",
        "aesr_share_4_1": "4.1 dry semi-arid plain",
        "aesr_share_2_5": "2.5 arid western plain",
        "aesr_share_14_2": "14.2 Siwalik foothills",
    }

    fig, axes = plt.subplots(1, 4, figsize=(14, 3.6), gridspec_kw={"wspace": 0.45})
    rng = np.random.default_rng(0)
    y = {g: i for i, g in enumerate(GROUP_ORDER[::-1])}
    for ax, (col, title, fmt) in zip(axes, numeric):
        for g in GROUP_ORDER:
            v = m.loc[m["label"] == g, col]
            jitter = rng.uniform(-0.18, 0.18, len(v))
            ax.scatter(v, y[g] + jitter, s=18, color=COLORS[g], edgecolor="white",
                       linewidth=0.6, zorder=3)
            med = v.median()
            ax.plot([med, med], [y[g] - 0.32, y[g] + 0.32], color=INK, lw=2, zorder=4)
            ax.annotate(fmt.format(med),
                        (med, y[g] + 0.34), ha="center", va="bottom", fontsize=7.5, color=INK)
        ax.set_yticks(list(y.values()), list(y.keys()))
        ax.set_ylim(-0.6, len(y) - 0.2)
        ax.set_title(title, loc="left", fontsize=9, color=INK)
        ax.xaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        if col == "rice_share_2022_cal":
            ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))

    ax = axes[3]
    shares = m.groupby("label")[list(zones)].mean().reindex(GROUP_ORDER[::-1])
    left = np.zeros(len(shares))
    greys = ["#d4d3cd", "#a3a29c", "#6f6e69", "#3d3c39"]
    for (col, name), c in zip(zones.items(), greys):
        ax.barh(shares.index, shares[col], left=left, color=c, edgecolor="white",
                linewidth=2, height=0.55, label=f"AESR {name}")
        left += shares[col].to_numpy()
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_title("Mean share of area in each\nagro-ecological sub-region", loc="left",
                 fontsize=9, color=INK)
    ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)

    fig.suptitle("What makes each group different (dots = tehsils, bar = median; Dhar Kalan excluded)",
                 x=0.08, ha="left", y=1.04, fontsize=11, color=INK)
    fig.savefig(OUT / "fig_C_group_profiles.png")
    plt.close(fig)


def fig_d_choosing_k():
    s = pd.read_csv(GROUPING / "stability_by_k.csv")
    s["k"] = s["cut"].str[1:].astype(int)
    # Groups of >= 5 tehsils only (min_group_size); sizes column names them.
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"wspace": 0.3})
    chosen = s["cut"] == "k3"
    for ax, col, title in [
        (axes[0], "silhouette", "Silhouette (higher = tighter, better separated)"),
        (axes[1], "ari_mean", "Bootstrap stability: mean ARI, 300 × 80% resamples"),
    ]:
        if col == "ari_mean":
            ax.fill_between(s["k"], s["ari_p05"], s["ari_p95"], color=COLORS["Central"],
                            alpha=0.15, lw=0, label="5th–95th percentile")
        ax.plot(s["k"], s[col], color=COLORS["Central"], lw=2, marker="o", ms=6, zorder=3)
        ax.scatter(s.loc[chosen, "k"], s.loc[chosen, col], s=140, facecolor="none",
                   edgecolor=INK, lw=1.5, zorder=4)
        ax.annotate(f"chosen: {s.loc[chosen, 'group_sizes'].item()}\n{s.loc[chosen, col].item():.3f}",
                    (3, s.loc[chosen, col].item()), xytext=(14, -26), textcoords="offset points",
                    fontsize=8, color=INK)
        ax.set_xticks(s["k"])
        ax.set_xlabel("Requested number of groups (groups < 5 tehsils set aside)")
        ax.set_title(title, loc="left", fontsize=9.5, color=INK)
        ax.yaxis.grid(True, color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        ax.set_ylim(0, 1.05 if col == "ari_mean" else 0.5)
    axes[1].legend(frameon=False, fontsize=8, loc="lower left")
    fig.savefig(OUT / "fig_D_choosing_k.png")
    plt.close(fig)


def fig_e_sensitivity():
    t = pd.read_csv(GROUPING / "sensitivity_table.csv")
    t = t[~t["scenario"].str.startswith("terrain_instead")]  # retired design, not a test
    pretty = {
        "drop_": "Drop ", "weight_": "", "_x1.15": " weight ×1.15", "_x0.85": " weight ×0.85",
    }
    labels = t["scenario"]
    for a, b in pretty.items():
        labels = labels.str.replace(a, b, regex=False)
    labels = labels.str.replace("soil_without_near_constant", "Soil without near-constant columns", regex=False)
    t = t.assign(label=labels.str.capitalize()).sort_values("ari_vs_baseline")

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = np.where(t["ari_vs_baseline"] >= 0.8, COLORS["Central"], COLORS["South-west"])
    ax.barh(t["label"], t["ari_vs_baseline"], color=colors, height=0.6, edgecolor="white")
    for yv, (ari, moved) in enumerate(zip(t["ari_vs_baseline"], t["n_moved"])):
        ax.text(ari + 0.01, yv, f"{ari:.2f}  ({moved} moved)", va="center", fontsize=7.5, color=INK)
    ax.axvline(0.8, color=INK_2, ls="--", lw=1)
    ax.set_xlim(0, 1.25)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xlabel("ARI vs frozen grouping (1 = identical)")
    ax.xaxis.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(handles=[
        Patch(color=COLORS["Central"], label="ARI ≥ 0.8: grouping holds"),
        Patch(color=COLORS["South-west"], label="ARI < 0.8: grouping changes (mostly the South-west / Central border)"),
    ], frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.4, -0.12), ncol=1)
    ax.set_title("One-factor-at-a-time sensitivity of the grouping", loc="left",
                 fontsize=11, color=INK)
    fig.savefig(OUT / "fig_E_sensitivity.png")
    plt.close(fig)


def fig_f_rice_calibration():
    c = pd.read_csv(CHEN_VS_OFFICIAL)
    fig, ax = plt.subplots(figsize=(6, 5.5))
    over = c["ratio"] > 1
    ax.scatter(c.loc[~over, "official"], c.loc[~over, "chen"], s=40, color=COLORS["Central"],
               edgecolor="white", lw=0.8, label="Chen under-maps (ratio < 1)", zorder=3)
    ax.scatter(c.loc[over, "official"], c.loc[over, "chen"], s=40, color=COLORS["South-west"],
               edgecolor="white", lw=0.8, label="Chen over-maps (ratio > 1)", zorder=3)
    lim = max(c["official"].max(), c["chen"].max()) * 1.08
    ax.plot([0, lim], [0, lim], color=INK_2, ls="--", lw=1, label="1:1 (perfect agreement)")
    for _, r in c[(c["ratio"] > 1.25) | (c["ratio"] < 0.8)].iterrows():
        offset = {"S.A.S Nagar": (8, -8), "Rupnagar": (-4, 10), "Hoshiarpur": (-30, 10)}.get(r["dist"], (5, 3))
        ax.annotate(f"{r['dist']} ×{r['ratio']:.2f}", (r["official"], r["chen"]),
                    xytext=offset, textcoords="offset points", fontsize=7.5, color=INK)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Official rice area 2021-22, thousand ha (Statistical Abstract 2022)")
    ax.set_ylabel("Chen et al. rice area 2022, thousand ha")
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title("Satellite vs official rice area by district (n = 22)", loc="left",
                 fontsize=11, color=INK)
    fig.savefig(OUT / "fig_F_rice_calibration.png")
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    groups = load_groups()
    fig_a_map(groups)
    fig_b_dendrogram(groups)
    fig_c_profiles(groups)
    fig_d_choosing_k()
    fig_e_sensitivity()
    fig_f_rice_calibration()
    print(f"Saved 6 figures to {OUT}")


if __name__ == "__main__":
    main()
