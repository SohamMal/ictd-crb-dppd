"""Report figure: Sentinel-2 detector vs daily Planet rule, on ground truth and on located CEEW fields.

Reads only saved results (no imagery):
  outputs/burn_basma/w1_cutoff_sweep.csv          S2 on Walker ground truth (0..5 d, z, 90% burns kept)
  outputs/planet/walker_planet_sweep.csv          Planet on the same ground truth (0..5 d, brightness ratio)
  outputs/planet/jalandhar_planet_rule_fields.csv Planet rule + S2 flags on Soham's labelled Jalandhar fields
Out: outputs/planet/fig_planet_vs_s2.png
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "planet"
S2, PL = "#2a78d6", "#eb6834"  # reference palette slots 1-2 (blue, orange)
INK, INK2, SURF = "#0b0b0b", "#52514e", "#fcfcfb"


def main():
    s2 = pd.read_csv(ROOT / "outputs" / "burn_basma" / "w1_cutoff_sweep.csv")
    s2 = s2[(s2.days == "0..5") & (s2.score == "z") & (s2.burnt_fields_kept == 0.9)].iloc[0]
    pl = pd.read_csv(OUT / "walker_planet_sweep.csv")
    pl = pl[(pl.days == "0..5") & (pl.score == "bright ratio") & (pl.burnt_fields_kept == 0.9)].iloc[0]
    j = pd.read_csv(OUT / "jalandhar_planet_rule_fields.csv")
    burnt = j[j.label == "burnt"]
    calm = j[j.label.isin(["stubble", "green"])]

    panels = [
        ("A. Ground truth (Walker et al., Punjab 2019)\nploughed-not-burnt fields wrongly called burnt,\nwith the cut-off set to catch 90% of burns",
         [("Ploughed fields\ncalled burnt", s2.tilled_fields_called_burnt, pl.tilled_fields_called_burnt,
           f"n = {int(s2.n_tilled)}", f"n = {int(pl.n_tilled)}")], "lower is better"),
        ("B. Located CEEW fields, Jalandhar 2021\n(Soham's labels from daily Planet pictures)",
         [("Burnt fields\ncaught", burnt.s2_burnt.mean(), burnt.planet_burnt.mean(),
           f"{int(burnt.s2_burnt.sum())}/{len(burnt)}", f"{int(burnt.planet_burnt.sum())}/{len(burnt)}"),
          ("No-event fields\ncalled burnt", calm.s2_burnt.mean(), calm.planet_burnt.mean(),
           f"{int(calm.s2_burnt.sum())}/{len(calm)}", f"{int(calm.planet_burnt.sum())}/{len(calm)}")],
         "caught: higher is better · no-event: lower is better"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 2]}, facecolor=SURF)
    w = 0.34
    for ax, (title, groups, note) in zip(axes, panels):
        ax.set_facecolor(SURF)
        for i, (name, a, b, la, lb) in enumerate(groups):
            for dx, v, lab, col in [(-w / 2 - 0.01, a, la, S2), (w / 2 + 0.01, b, lb, PL)]:
                ax.bar(i + dx, v, w, color=col, zorder=2)
                ax.text(i + dx, v + 0.02, f"{v:.0%}\n({lab})", ha="center", va="bottom", fontsize=8.5, color=INK)
        ax.set_xticks(range(len(groups)), [g[0] for g in groups], fontsize=9, color=INK)
        ax.set_ylim(0, 1.22)
        ax.set_yticks(np.linspace(0, 1, 6), [f"{t:.0%}" for t in np.linspace(0, 1, 6)], fontsize=8, color=INK2)
        ax.grid(axis="y", color="#e4e3df", lw=0.8, zorder=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(INK2)
        ax.tick_params(length=0)
        ax.set_title(title, fontsize=9.5, color=INK, loc="left")
        ax.text(0, -0.2, note, transform=ax.transAxes, fontsize=8, color=INK2)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=S2, label="Sentinel-2 detector (every ~5 days)"),
                        Patch(color=PL, label="Planet daily rule (every ~1 day)")],
               loc="upper center", ncol=2, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(OUT / "fig_planet_vs_s2.png", dpi=160, facecolor=SURF)
    print(OUT / "fig_planet_vs_s2.png")


if __name__ == "__main__":
    main()
