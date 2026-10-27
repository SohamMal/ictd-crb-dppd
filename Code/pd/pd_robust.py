"""
Robust positive / negative deviants (2026-10-28)

A tehsil is robust if it is flagged (PD or candidate-PD; ND or candidate-ND for negatives) in BOTH the
main S2 run (2020-24) and the sensitivity run without the weak 2024 season (2020-23), for the same rule
(static or temporal). [C] Soham, 2026-10-28. The VIIRS backup flag is shown for reference only.

Run:  python Code/pd/pd_identify.py --measure s2rf; ... --measure s2rf_2023; ... --measure viirs
      python Code/pd/pd_robust.py
Out:  outputs/pd/robust/robust_deviants.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PD = ROOT / "outputs" / "pd"
RUNS = {"main": "s2rf", "no2024": "s2rf_2023", "viirs": "viirs"}
KEEP = ["lgd_tehsil_code", "mean", "static", "temporal", "pct_per_year_vs_group", "survives_plains"]


def main():
    t = None
    for tag, m in RUNS.items():
        d = pd.read_csv(PD / m / "pd_table.csv").fillna({"static": "", "temporal": ""})
        d = d[(["lgd_tehsil_name", "lgd_district_name", "group"] if t is None else []) + KEEP]
        d = d.rename(columns={c: f"{c}_{tag}" for c in KEEP if c != "lgd_tehsil_code"})
        t = d if t is None else t.merge(d, on="lgd_tehsil_code", how="left")

    pos = lambda s: s.isin(["PD", "candidate-PD"])  # noqa: E731
    neg = lambda s: s.isin(["ND", "candidate-ND"])  # noqa: E731
    rows = []
    for rule in ["static", "temporal"]:
        a, b = t[f"{rule}_main"], t[f"{rule}_no2024"]
        for kind, f in [("PD", pos), ("ND", neg)]:
            t[f"robust_{rule}_{kind}"] = f(a) & f(b)
            t[f"only_one_{rule}_{kind}"] = f(a) ^ f(b)
    t["robust"] = np.select(
        [t.robust_static_PD & t.robust_temporal_PD, t.robust_static_PD, t.robust_temporal_PD,
         t.robust_static_ND & t.robust_temporal_ND, t.robust_static_ND, t.robust_temporal_ND],
        ["PD static + temporal", "PD static", "PD temporal",
         "ND static + temporal", "ND static", "ND temporal"], "")
    flagged = t[(t.robust != "") | t.filter(like="only_one_").any(axis=1)].copy()
    flagged["status"] = np.where(flagged.robust != "", "robust", "one run only")
    cols = ["lgd_tehsil_name", "lgd_district_name", "group", "status", "robust",
            "mean_main", "mean_no2024", "static_main", "static_no2024", "temporal_main", "temporal_no2024",
            "pct_per_year_vs_group_main", "pct_per_year_vs_group_no2024", "survives_plains_main",
            "static_viirs", "temporal_viirs"]
    flagged = flagged[cols].sort_values(["status", "robust", "group", "mean_main"])
    out = PD / "robust"
    out.mkdir(parents=True, exist_ok=True)
    flagged.round(3).to_csv(out / "robust_deviants.csv", index=False)
    pd.set_option("display.width", 250)
    show = ["lgd_tehsil_name", "group", "status", "robust", "mean_main", "static_main", "static_no2024",
            "temporal_main", "temporal_no2024", "pct_per_year_vs_group_main", "survives_plains_main",
            "static_viirs", "temporal_viirs"]
    print(flagged[show].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
