"""
Version X figures (2026-11-10)

  village_pd_map.png   ranked villages shaded by village group, static village PDs (validated / caveat) and
                       static NDs (contrast) on top, current tehsil outlines; tehsil-level validated PDs outlined
  burn_map.png         5-season mean burnt share per ranked village

Run:  python version_X/Code/vx_figures.py
Out:  version_X/outputs/figures/
"""

from pathlib import Path

import geopandas as gpd
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
VX = ROOT / "version_X" / "outputs"
OUT = VX / "figures"
ID = "c2011_village_code"
GROUP_COL = {"V1": "#dfe8d0", "V2": "#f1e4c8", "V3": "#e6dcef"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vp = gpd.read_file(VX / "villages" / "village_polygons.gpkg")
    t = pd.read_csv(VX / "pd" / "pd_table.csv", dtype={ID: str})
    v = pd.read_csv(VX / "pd" / "pd_validated.csv", dtype={ID: str})
    st = v[v.kind == "static"]
    g = vp.merge(t[[ID, "vgroup", "mean"]], on=ID)
    teh = gpd.read_file(ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg").to_crs(vp.crs)
    tp = pd.read_csv(ROOT / "outputs" / "pd" / "pd_validated.csv")
    tpd = teh[teh.lgd_tehsil_code.isin(tp[(tp.kind == "PD") & (tp.rule == "static") & (tp.label != "dropped")]
                                        .lgd_tehsil_code)]

    fig, ax = plt.subplots(figsize=(10, 10))
    for k, c in GROUP_COL.items():
        g[g.vgroup == k].plot(ax=ax, color=c, linewidth=0)
    teh.boundary.plot(ax=ax, color="#9a9a9a", linewidth=0.3)
    tpd.boundary.plot(ax=ax, color="black", linewidth=1.2)
    for lab, col, name in [("validated PD", "#c0392b", "village PD (validated)"),
                           ("PD with caveat", "#f39c12", "village PD (caveat)")]:
        s = g[g[ID].isin(st[st.label == lab][ID])]
        s.representative_point().plot(ax=ax, color=col, markersize=7, label=f"{name}: {len(s)}")
    nd = g[g[ID].isin(st[st.label == "contrast"][ID])]
    nd.representative_point().plot(ax=ax, color="#2c3e91", markersize=5, marker="x", label=f"village ND: {len(nd)}")
    handles, labels = ax.get_legend_handles_labels()
    for k, c in GROUP_COL.items():
        handles.append(plt.Rectangle((0, 0), 1, 1, color=c))
        labels.append(f"group {k}")
    handles.append(plt.Line2D([], [], color="black", linewidth=1.2))
    labels.append("tehsil PD (main version)")
    ax.legend(handles, labels, loc="lower left", fontsize=9, frameon=True)
    ax.set_title("Version X: village positive deviants within peer groups (static, 2020-24)")
    ax.set_axis_off()
    fig.savefig(OUT / "village_pd_map.png", dpi=170, bbox_inches="tight")

    fig, ax = plt.subplots(figsize=(10, 10))
    g.plot(ax=ax, column="mean", cmap="YlOrRd", linewidth=0, legend=True, vmin=0, vmax=1,
           legend_kwds={"shrink": 0.6, "label": "mean burnt share of rice points, 2020-24"})
    teh.boundary.plot(ax=ax, color="#666666", linewidth=0.3)
    ax.set_title("Version X: village burning (Sentinel-2 RF detector, 10 rice points per village per season)")
    ax.set_axis_off()
    fig.savefig(OUT / "burn_map.png", dpi=170, bbox_inches="tight")


if __name__ == "__main__":
    main()
