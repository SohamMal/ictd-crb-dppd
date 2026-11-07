"""
Positive deviant identification within frozen groups (2026-10-23)

Rules [C] (Soham, 2026-10-23); DPPD Handbook pp. 63-66 (IQR rule, as in the Egypt case):
- Log scale (2026-10-23 revision): burn values are right-skewed with a floor at 0, so on the raw
  scale Q1 - 1.5*IQR falls below 0 and no tehsil can pass (VIIRS Central: -5.76). All rules work on
  log(value + c), c = 10% of the group median of tehsil means (keeps near-zero values stable).
- Static PD: log 5-season mean < Q1 - 1.5*IQR of its group, AND in the group's lowest quartile in
  all seasons but one (4 of 5; 3 of 4 for a 4-season run). "candidate-PD" = bottom 10% of the group mean AND the same consistency
  rule (potential PDs, confirmed only at validation / fieldwork).
- Temporal PD: Theil-Sen slope of log(value + c) over the seasons (relative change per year) minus
  the group median slope; PD if deviance < Q1 - 1.5*IQR of the group's deviances.
  candidate-PD = bottom 10%. pct_per_year_vs_group = exp(slope_dev) - 1.
- Negative deviants: the mirror image (above Q3 + 1.5*IQR; top quartile all seasons but one; top 10%).
- Groups: frozen v4 Central and South-west only (Foothills excluded 2026-10-23; Outlier out).
  The merged Plains grouping (81 tehsils) is run as well and reported, not used to drop PDs.
Direct comparison of each tehsil with its group; no regression residuals (Prof. Aaditeshwar).

Input: any long table with one value per tehsil-year (lower = less burning).

Measures: viirs (backup, 2019-23); s2rf = final S2 model tehsil table (tehsil_metric_rf.py, cut 0.786),
2020-24 (main); s2rf_2023 = same, 2020-23 (sensitivity: 2024 is the weak season). Robust PDs = flagged in
both s2rf runs (pd_robust.py). s2rf_05 / s2rf_05_2023 = the same at the 0.5 cut (validation V2, 2026-11-07).

Validation options (2026-11-07; defaults reproduce the runs above):
  --c-share S   offset c = S x group median (default 0.10)
  --groups F    CSV (lgd_tehsil_code, group) replacing the frozen group of each tehsil
  --tag T       write to outputs/pd/<measure>_<T>/ instead of outputs/pd/<measure>/

Run:  python Code/pd/pd_identify.py --measure viirs|s2rf|s2rf_2023|s2rf_05|s2rf_05_2023
Out:  outputs/pd/<measure>/pd_table.csv, pd_summary.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

ROOT = Path(__file__).resolve().parents[2]
GROUPS = ROOT / "outputs" / "grouping" / "FROZEN_groups.csv"
PD_GROUPS = ["Central", "South-west"]
MAX_SEASONS_MISSED = 1   # consistency: in the quartile in all seasons but one
NEAR_SHARE = 0.10
C_SHARE = 0.10           # offset c = C_SHARE x group median of tehsil means

# measure name -> (file, value column, seasons)
MEASURES = {
    "viirs": (ROOT / "outputs" / "burn_fire" / "tehsil_fire_measure.csv",
              "fires_per_1000ha_rice", range(2019, 2024)),
    "s2rf": (ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv",
             "burnt_share", range(2020, 2025)),
    "s2rf_2023": (ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv",
                  "burnt_share", range(2020, 2024)),
    "s2rf_05": (ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv",
                "burnt_share_05", range(2020, 2025)),
    "s2rf_05_2023": (ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv",
                     "burnt_share_05", range(2020, 2024)),
}


def load_groups(alt=None):
    g = pd.read_csv(GROUPS)
    if alt is not None:
        g = g.drop(columns="group").merge(pd.read_csv(alt)[["lgd_tehsil_code", "group"]], on="lgd_tehsil_code")
    g = g[g["group"].isin(PD_GROUPS)]
    return g[["lgd_tehsil_code", "lgd_tehsil_name", "lgd_district_name", "group", "group_2way"]]


def iqr_bounds(x):
    q1, q3 = np.percentile(x, [25, 75])
    return q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)


def flag_within(df, by):
    """Static and temporal flags for every tehsil, compared within the column `by`."""
    out = []
    for name, d in df.groupby(by):
        d = d.copy()
        n = len(d)
        k_near = max(1, int(round(NEAR_SHARE * n)))

        log_mean = np.log(d["mean"] + d["c"])
        lo, hi = iqr_bounds(log_mean)
        consistent_lo = d["years_bottom_q"] >= d["n_years"] - MAX_SEASONS_MISSED
        consistent_hi = d["years_top_q"] >= d["n_years"] - MAX_SEASONS_MISSED
        rank_lo = d["mean"].rank(method="min")
        rank_hi = d["mean"].rank(method="min", ascending=False)
        d["static"] = np.select(
            [(log_mean < lo) & consistent_lo, (rank_lo <= k_near) & consistent_lo,
             (log_mean > hi) & consistent_hi, (rank_hi <= k_near) & consistent_hi],
            ["PD", "candidate-PD", "ND", "candidate-ND"], "")

        d["slope_dev"] = d["slope"] - d["slope"].median()
        lo, hi = iqr_bounds(d["slope_dev"])
        rank_lo = d["slope_dev"].rank(method="min")
        rank_hi = d["slope_dev"].rank(method="min", ascending=False)
        d["temporal"] = np.select(
            [d["slope_dev"] < lo, rank_lo <= k_near, d["slope_dev"] > hi, rank_hi <= k_near],
            ["PD", "candidate-PD", "ND", "candidate-ND"], "")
        d["pct_per_year_vs_group"] = 100 * (np.exp(d["slope_dev"]) - 1)

        d["n_in_group"] = n
        out.append(d)
    return pd.concat(out)


def tehsil_stats(long, value, years, by, c_share=C_SHARE):
    """Per tehsil: season mean, offset c of its group, Theil-Sen slope of log(value + c)."""
    long = long[long["year"].isin(years)]
    means = long.groupby(["lgd_tehsil_code", by])[value].mean()
    c = (c_share * means.groupby(by).median()).rename("c")
    long = long.merge(c, left_on=by, right_index=True)
    rows = []
    for code, d in long.groupby("lgd_tehsil_code"):
        d = d.sort_values("year")
        y = np.log(d[value] + d["c"])
        slope = theilslopes(y, d["year"])[0] if y.nunique() > 1 else 0.0
        rows.append({"lgd_tehsil_code": code, "mean": d[value].mean(), "c": d["c"].iloc[0],
                     "slope": slope, "n_years": len(d)})
    return pd.DataFrame(rows)


def quartile_years(long, value, years, by):
    """Number of seasons each tehsil is in its group's lowest / highest quartile."""
    long = long[long["year"].isin(years)]
    q = long.groupby([by, "year"])[value]
    long = long.assign(bottom=long[value] <= q.transform(lambda x: x.quantile(0.25)),
                       top=long[value] >= q.transform(lambda x: x.quantile(0.75)))
    return long.groupby("lgd_tehsil_code")[["bottom", "top"]].sum().rename(
        columns={"bottom": "years_bottom_q", "top": "years_top_q"}).reset_index()


def run(long, value, years, groups, by, c_share=C_SHARE):
    long = long.merge(groups[["lgd_tehsil_code", by]], on="lgd_tehsil_code")
    stats = tehsil_stats(long, value, years, by, c_share).merge(groups, on="lgd_tehsil_code")
    stats = stats.merge(quartile_years(long, value, years, by), on="lgd_tehsil_code")
    return flag_within(stats, by)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", default="viirs", choices=MEASURES)
    ap.add_argument("--c-share", type=float, default=C_SHARE)
    ap.add_argument("--groups", default=None)
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()
    path, value, years = MEASURES[args.measure]
    years = list(years)

    long = pd.read_csv(path)[["lgd_tehsil_code", "year", value]]
    groups = load_groups(args.groups)
    missing = set(groups["lgd_tehsil_code"]) - set(long["lgd_tehsil_code"])
    assert not missing, f"tehsils without a burn value: {missing}"

    main_run = run(long, value, years, groups, "group", args.c_share)
    plains = run(long, value, years, groups, "group_2way", args.c_share)[
        ["lgd_tehsil_code", "slope_dev", "static", "temporal"]].rename(
        columns={"slope_dev": "slope_dev_plains", "static": "static_plains",
                 "temporal": "temporal_plains"})
    t = main_run.merge(plains, on="lgd_tehsil_code")

    pd_like = lambda s: s.isin(["PD", "candidate-PD"])
    t["both"] = np.where(pd_like(t["static"]) & pd_like(t["temporal"]), "PD both", "")
    t["survives_plains"] = np.where(
        pd_like(t["static"]) | pd_like(t["temporal"]),
        (pd_like(t["static"]) & pd_like(t["static_plains"]))
        | (pd_like(t["temporal"]) & pd_like(t["temporal_plains"])), "")

    out = ROOT / "outputs" / "pd" / (args.measure + (f"_{args.tag}" if args.tag else ""))
    out.mkdir(parents=True, exist_ok=True)
    cols = ["lgd_tehsil_code", "lgd_tehsil_name", "lgd_district_name", "group", "n_in_group",
            "n_years", "mean", "c", "years_bottom_q", "years_top_q", "slope", "slope_dev",
            "pct_per_year_vs_group",
            "static", "temporal", "both", "static_plains", "temporal_plains", "survives_plains"]
    t = t[cols].sort_values(["group", "mean"])
    t.to_csv(out / "pd_table.csv", index=False)

    summary = pd.concat([
        t.groupby("group")["static"].value_counts().rename("n").reset_index().assign(kind="static")
         .rename(columns={"static": "flag"}),
        t.groupby("group")["temporal"].value_counts().rename("n").reset_index().assign(kind="temporal")
         .rename(columns={"temporal": "flag"}),
    ])
    summary = summary[summary["flag"] != ""]
    summary.to_csv(out / "pd_summary.csv", index=False)

    print(f"measure={args.measure} value={value} seasons={years[0]}-{years[-1]} c_share={args.c_share}"
          f" groups={args.groups or 'frozen'}")
    print(summary.pivot_table(index=["kind", "flag"], columns="group", values="n", fill_value=0))
    flagged = t[(t["static"] != "") | (t["temporal"] != "")]
    print(flagged[["lgd_tehsil_name", "group", "mean", "years_bottom_q", "years_top_q",
                   "pct_per_year_vs_group",
                   "static", "temporal", "both", "survives_plains"]].to_string(index=False))


if __name__ == "__main__":
    main()
