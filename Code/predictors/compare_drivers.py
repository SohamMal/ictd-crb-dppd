"""
Stage 3 analysis: validated PDs vs their group and vs the NDs, driver by driver (2026-11-10)

Plan [C] Soham, 2026-11-10 (task_predictor_analysis.md): descriptive, not causal (6 validated PDs + 2 with caveat,
4 static NDs). Three readings per driver, all within the frozen groups (Central 63, South-west 18):
  1. PD / ND profile   each unit's value and its percentile in its group; per driver, how many PDs sit on the
                       side of the group median that the hypothesis expects (and how many NDs on the other side)
  2. rho               Spearman of the driver with the 2020-24 mean burnt share across all tehsils of the group
  3. partial rho       the same with calibrated rice share held constant (Spearman of the rank residuals after
                       removing rank(rice share)); burning rises with rice share (V4), so a driver that only stands
                       in for "less rice" loses its correlation here. This is analysis, not PD identification, so the
                       "no residual-based identification" rule does not apply
Expected sign = the hypothesis [P] from task_predictor_data.md (e.g. a longer turnaround -> less burning -> rho < 0).

Run:  python Code/predictors/compare_drivers.py   (after drivers.py, pd_validate.py)
Out:  outputs/predictors/drivers/{unit_profiles,driver_summary}.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "predictors" / "drivers"
GROUPS = ["Central", "South-west"]

# driver column -> (plain name, expected sign of rho with burning)
DRIVERS = {
    "d1_turnaround_days": ("Harvest-to-wheat turnaround (days)", -1),
    "d2_early_canopy_share": ("Early second crop (potato/veg) share", -1),
    "d3_labourers_per_cultivator": ("Farm labourers per cultivator (2011)", -1),
    "d3_cultivators_per_100ha_rice": ("Cultivators per 100 ha rice (small farms, 2011)", -1),
    "d4_buyers_within_30km": ("Straw buyers within 30 km", -1),
    "d4_km_nearest_buyer": ("km to nearest straw buyer", +1),
    "d5_km_interstate_border": ("km to inter-state border", -1),
    "d6_km_urban_centre": ("km to nearest urban centre", +1),
    "d6_urban_area_share": ("Urban area share", -1),
    "d7_basmati_share_district": ("Basmati share of rice (district)", -1),
    "d9_bovines_per_cultivator": ("Cattle + buffalo per cultivator (2019)", -1),
}


def partial_spearman(x, y, z):
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    res = lambda r: r - np.polyval(np.polyfit(rz, r, 1), rz)  # noqa: E731
    return spearmanr(res(rx), res(ry))


def main():
    g = pd.read_csv(ROOT / "outputs" / "grouping" / "FROZEN_groups.csv")[["lgd_tehsil_code", "lgd_tehsil_name", "group"]]
    g = g[g.group.isin(GROUPS)]
    burn = pd.read_csv(ROOT / "outputs" / "pd" / "s2rf" / "pd_table.csv")[["lgd_tehsil_code", "mean"]].rename(
        columns={"mean": "burnt_share_2020_24"})
    rice = pd.read_csv(ROOT / "Data" / "punjab_homogeneous_grouping_master_raw_97tehsils.csv")[
        ["lgd_tehsil_code", "rice_share_2022_cal"]]
    d = g.merge(burn).merge(rice).merge(pd.read_csv(OUT / "tehsil_drivers.csv"), on="lgd_tehsil_code")

    v = pd.read_csv(ROOT / "outputs" / "pd" / "pd_validated.csv")
    v = v[(v.rule == "static") & v.label.isin(["validated PD", "PD with caveat", "contrast"])]
    units = v[["lgd_tehsil_code", "label"]].drop_duplicates("lgd_tehsil_code")
    units["role"] = units.label.map({"validated PD": "PD", "PD with caveat": "PD (caveat)", "contrast": "ND"})

    for col in DRIVERS:
        d[f"{col}_pct"] = d.groupby("group")[col].rank(pct=True)
    prof = units.merge(d, on="lgd_tehsil_code")
    keep = ["lgd_tehsil_name", "group", "role", "burnt_share_2020_24", "rice_share_2022_cal"]
    prof[keep + [c for col in DRIVERS for c in (col, f"{col}_pct")]].round(3).sort_values(
        ["role", "group", "burnt_share_2020_24"]).to_csv(OUT / "unit_profiles.csv", index=False)

    rows = []
    for col, (name, sign) in DRIVERS.items():
        r = {"driver": col, "name": name, "expected_sign": sign}
        for grp, x in d.groupby("group"):
            x = x.dropna(subset=[col])
            rho, p = spearmanr(x[col], x.burnt_share_2020_24)
            prho, pp = partial_spearman(x[col], x.burnt_share_2020_24, x.rice_share_2022_cal)
            r.update({f"rho_{grp}": rho, f"p_{grp}": p, f"partial_rho_{grp}": prho, f"partial_p_{grp}": pp})
        med = d.groupby("group")[col].median()
        pu = prof[prof.role.str.startswith("PD")]
        nu = prof[prof.role == "ND"]
        # expected side for a PD: low burning -> driver below median if sign > 0, above if sign < 0
        pd_side = np.where(sign < 0, pu[col] > pu.group.map(med), pu[col] < pu.group.map(med))
        nd_side = np.where(sign < 0, nu[col] < nu.group.map(med), nu[col] > nu.group.map(med))
        r.update({"pds_expected_side": f"{pd_side.sum()}/{len(pu)}", "nds_expected_side": f"{nd_side.sum()}/{len(nu)}",
                  "pds_on_side": ", ".join(pu.lgd_tehsil_name[pd_side])})
        rows.append(r)
    s = pd.DataFrame(rows)
    s.round(3).to_csv(OUT / "driver_summary.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(s.drop(columns=["driver"]).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
