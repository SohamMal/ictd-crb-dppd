"""
Version X: checks on the village burning measure (2026-11-10)

  1. aggregation  village shares x calibrated village rice ha, summed to tehsils, vs the main version's tehsil
                  measure (same detector, independent points except ~1 shared point per village): Spearman per season
  2. reliability  Spearman of village burnt share between seasons (a pure-noise measure would give ~0)
  3. rice         Spearman of village rice share vs 5-season mean burnt share, per village group and per peer group
                  (group x rice band): shows what the rice bands of vx_peer_groups.py remove

Run:  python version_X/Code/vx_burn_checks.py
Out:  version_X/outputs/burn/checks_{aggregation,reliability,rice}.csv
"""

from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
VX = ROOT / "version_X" / "outputs"
ID = "c2011_village_code"


def main():
    vm = pd.read_csv(VX / "burn" / "village_burn_measure.csv", dtype={ID: str})
    vg = pd.read_csv(VX / "grouping" / "village_groups.csv", dtype={ID: str})
    m = vm.merge(vg[[ID, "lgd_tehsil_code", "rice_ha_2022_cal", "rice_share_2022_cal", "peer", "vgroup"]], on=ID)
    m["b"] = m.burnt_share * m.rice_ha_2022_cal
    t = m.groupby(["year", "lgd_tehsil_code"]).agg(b=("b", "sum"), r=("rice_ha_2022_cal", "sum")).reset_index()
    t["village_agg"] = t.b / t.r
    tt = pd.read_csv(ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv")
    x = t.merge(tt[["year", "lgd_tehsil_code", "burnt_share"]], on=["year", "lgd_tehsil_code"])
    agg = pd.DataFrame([{"year": y, "tehsils": len(g), "rho": spearmanr(g.village_agg, g.burnt_share)[0],
                         "mean_village_agg": g.village_agg.mean(), "mean_tehsil": g.burnt_share.mean()}
                        for y, g in x.groupby("year")])
    rel = m.pivot_table(index=ID, columns="year", values="burnt_share").corr(method="spearman")
    mm = m.groupby(ID).agg(mean=("burnt_share", "mean"), rice=("rice_share_2022_cal", "first"),
                           vgroup=("vgroup", "first"), peer=("peer", "first"))
    rice = pd.DataFrame([{"level": lvl, "unit": k, "n": len(d), "rho_rice_vs_burn": spearmanr(d.rice, d["mean"])[0],
                          "median_burn": d["mean"].median()}
                         for lvl in ["vgroup", "peer"] for k, d in mm.groupby(lvl)])
    for name, df in [("aggregation", agg), ("reliability", rel), ("rice", rice)]:
        df.round(3).to_csv(VX / "burn" / f"checks_{name}.csv", index=name == "reliability")
        print(f"\n{name}\n", df.round(3).to_string())


if __name__ == "__main__":
    main()
