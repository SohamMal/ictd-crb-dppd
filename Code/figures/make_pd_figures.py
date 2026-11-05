"""
Deck/report figures for the tehsil burn measure and PD identification (Stage 2, Steps 1 and 3).

Reads only finished outputs, so the figures always match the numbers in the report.

Fig G  mean burnt share map 2020-24      fig_G_burn_map.png
Fig H  burn measure vs VIIRS (one year)  fig_H_burn_vs_viirs.png
Fig I  static PD fences per group        fig_I_pd_fences.png
Fig J  positive / negative deviant map   fig_J_pd_map.png

Run:  python Code/figures/make_pd_figures.py
Out:  outputs/figures/
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "figures"
POLYGONS = ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg"
GROUPS = ROOT / "outputs" / "grouping" / "FROZEN_groups.csv"
BURN = ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv"
FIRES = ROOT / "outputs" / "burn_fire" / "tehsil_fire_measure.csv"
PD_TABLE = ROOT / "outputs" / "pd" / "s2rf" / "pd_table.csv"
ROBUST = ROOT / "outputs" / "pd" / "robust" / "robust_deviants.csv"

PD_YEARS = range(2020, 2025)
VIIRS_YEAR = 2021

# Same palette as make_grouping_figures.py.
COLORS = {
    "Central": "#2a78d6",
    "South-west": "#eb6834",
    "Foothills": "#1baf7a",
    "Outlier": "#a3a29c",
}
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
DOABA = ["Gurdaspur", "Phagwara", "Adampur", "Jalandhar - I", "Banga"]

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


def load_map():
    poly = gpd.read_file(POLYGONS)[["lgd_tehsil_code", "geometry"]]
    groups = pd.read_csv(GROUPS)[["lgd_tehsil_code", "lgd_tehsil_name", "group"]]
    return poly.merge(groups, on="lgd_tehsil_code")


def fig_burn_map(gdf):
    burn = pd.read_csv(BURN)
    mean = (burn[burn["year"].isin(PD_YEARS)]
            .groupby("lgd_tehsil_code")["burnt_share"].mean().rename("mean_share"))
    g = gdf.merge(mean, on="lgd_tehsil_code")
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    g.plot(ax=ax, column="mean_share", cmap="YlOrRd", vmin=0, vmax=0.9,
           edgecolor="white", linewidth=0.5, legend=True,
           legend_kwds={"label": "Share of cropland points burnt (mean 2020–24)",
                        "orientation": "horizontal", "shrink": 0.7, "pad": 0.02})
    g.dissolve("group").boundary.plot(ax=ax, color=INK, linewidth=1.1)
    ax.set_axis_off()
    fig.savefig(OUT / "fig_G_burn_map.png")
    plt.close(fig)


def fig_burn_vs_viirs():
    burn = pd.read_csv(BURN)
    fires = pd.read_csv(FIRES)[["lgd_tehsil_code", "year", "fires_per_1000ha_rice"]]
    d = burn[(burn["year"] == VIIRS_YEAR) & burn["in_pd_identification"]].merge(
        fires, on=["lgd_tehsil_code", "year"])
    rho = spearmanr(d["burnt_share"], d["fires_per_1000ha_rice"])[0]
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    for grp, s in d.groupby("group"):
        ax.scatter(s["fires_per_1000ha_rice"], s["burnt_share"], s=28, color=COLORS[grp],
                   edgecolor="white", linewidth=0.5, label=f"{grp} ({len(s)})")
    ax.set_xlabel(f"VIIRS active fires per 1,000 ha rice ({VIIRS_YEAR})")
    ax.set_ylabel(f"Our burnt share ({VIIRS_YEAR})")
    ax.yaxis.grid(True, color=GRID, lw=0.6)
    ax.text(0.98, 0.04, f"Spearman ρ = {rho:.2f}  (n = {len(d)})", transform=ax.transAxes,
            ha="right", fontsize=10, color=INK)
    ax.legend(frameon=False, loc="upper left")
    fig.savefig(OUT / "fig_H_burn_vs_viirs.png")
    plt.close(fig)
    return rho, len(d)


def fig_pd_fences():
    t = pd.read_csv(PD_TABLE)
    show = ["Central", "South-west"]
    labels = {"Abohar", "Dinanagar", "Guruharsahai"}
    fig, axes = plt.subplots(2, 1, figsize=(7.5, 3.8), sharex=True)
    rng = np.random.default_rng(0)
    fences = {}
    for ax, grp in zip(axes, show):
        d = t[t["group"] == grp]
        c = d["c"].iloc[0]
        log_mean = np.log(d["mean"] + c)
        q1, q3 = np.percentile(log_mean, [25, 75])
        lo = np.exp(q1 - 1.5 * (q3 - q1)) - c
        med = d["mean"].median()
        fences[grp] = (lo, med)
        y = rng.uniform(-0.25, 0.25, len(d))
        doaba = d["lgd_tehsil_name"].isin(DOABA).to_numpy()
        ax.scatter(d["mean"][~doaba], y[~doaba], s=26, color=COLORS[grp],
                   edgecolor="white", linewidth=0.5, zorder=3)
        ax.scatter(d["mean"][doaba], y[doaba], s=34, color="white", edgecolor=COLORS[grp],
                   linewidth=1.4, zorder=3, label="Doaba cluster")
        ax.axvline(lo, color=INK, ls="--", lw=1)
        ax.axvline(med, color=INK_2, lw=1)
        ax.text(lo, 0.42, f" fence {lo:.2f}", fontsize=8, color=INK, va="bottom")
        ax.text(med, 0.42, f" median {med:.2f}", fontsize=8, color=INK_2, va="bottom")
        for (_, r), yy in zip(d.iterrows(), y):
            if r["lgd_tehsil_name"] in labels:
                ax.annotate(r["lgd_tehsil_name"], (r["mean"], yy), xytext=(0, -11),
                            textcoords="offset points", ha="center", fontsize=7.5, color=INK)
        if grp == "Central":
            ax.text(0.80, -0.5, "highest: Lehra · Zira · Moonak", ha="center", fontsize=7.5,
                    color=INK)
        ax.set_ylim(-0.6, 0.6)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.set_title(f"{grp} ({len(d)} tehsils)", loc="left", fontsize=9, color=INK)
    axes[0].legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 1.0), fontsize=8)
    axes[1].set_xscale("log")
    axes[1].set_xticks([0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0])
    axes[1].set_xticklabels(["0.2", "0.3", "0.4", "0.5", "0.6", "0.8", "1.0"])
    axes[1].set_xlabel("Mean burnt share 2020–24 (log scale)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_I_pd_fences.png")
    plt.close(fig)
    return fences


def fig_pd_map(gdf):
    r = pd.read_csv(ROBUST)
    r = r[r["status"].str.startswith("robust")]
    strict = r["strict_rule"].fillna("")
    cls = {}
    for name, rule, s in zip(r["lgd_tehsil_name"], r["old_rule"], strict):
        if name in DOABA:
            cls[name] = "Low-burning cluster (Doaba)"
        elif s.startswith("PD"):
            cls[name] = "Strict PD"
        elif "borderline PD" in s:
            cls[name] = "Borderline PD"
        elif rule.startswith("ND"):
            cls[name] = "Negative deviant"
    style = {
        "Strict PD": "#0f7b4a",
        "Borderline PD": "#7fd1a8",
        "Low-burning cluster (Doaba)": "#2a78d6",
        "Negative deviant": "#c0392b",
    }
    base = {"Central": "#ecebe7", "South-west": "#d9d7d1", "Foothills": "#f7f7f5",
            "Outlier": "#f7f7f5"}
    g = gdf.copy()
    g["cls"] = g["lgd_tehsil_name"].map(cls)
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    g.plot(ax=ax, color=g["group"].map(base), edgecolor="white", linewidth=0.5)
    hit = g[g["cls"].notna()]
    hit.plot(ax=ax, color=hit["cls"].map(style), edgecolor="white", linewidth=0.5)
    g.dissolve("group").boundary.plot(ax=ax, color=INK_2, linewidth=0.9)
    for _, row in hit.iterrows():
        if row["cls"] in ("Strict PD", "Borderline PD") or row["lgd_tehsil_name"] == "Malout":
            p = row.geometry.representative_point()
            off = (-60, -28) if row["lgd_tehsil_name"] == "Abohar" else (14, 8)
            ax.annotate(row["lgd_tehsil_name"], (p.x, p.y), xytext=off,
                        textcoords="offset points", fontsize=11, color=INK,
                        arrowprops=dict(arrowstyle="-", color=INK, lw=0.6))
    handles = [Patch(facecolor=v, edgecolor="white", label=k) for k, v in style.items()]
    handles += [Patch(facecolor=base["Central"], edgecolor=INK_2, label="Central (not flagged)"),
                Patch(facecolor=base["South-west"], edgecolor=INK_2, label="South-west (not flagged)"),
                Patch(facecolor=base["Foothills"], edgecolor=INK_2, label="Foothills (not ranked)")]
    ax.legend(handles=handles, frameon=False, loc="upper left", bbox_to_anchor=(0.92, 0.95),
              fontsize=11)
    ax.set_axis_off()
    fig.savefig(OUT / "fig_J_pd_map.png")
    plt.close(fig)
    return cls


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gdf = load_map()
    fig_burn_map(gdf)
    rho, n = fig_burn_vs_viirs()
    print(f"Fig H: Spearman {VIIRS_YEAR} = {rho:.3f} (n = {n})")
    for grp, (lo, med) in fig_pd_fences().items():
        print(f"Fig I: {grp} fence {lo:.3f}, median {med:.3f}")
    print("Fig J:", fig_pd_map(gdf))


if __name__ == "__main__":
    main()
