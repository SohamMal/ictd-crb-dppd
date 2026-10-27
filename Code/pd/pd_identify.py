"""
Positive deviant identification within frozen groups (2026-10-23)

Rules [C] (Soham, 2026-10-23); DPPD Handbook pp. 63-66 (IQR rule, as in the Egypt case):
- Log scale (2026-10-23 revision): burn values are right-skewed with a floor at 0, so on the raw
  scale Q1 - 1.5*IQR falls below 0 and no tehsil can pass (VIIRS Central: -5.76). All rules work on
  log(value + c), c = 10% of the group median of tehsil means (keeps near-zero values stable).
- Static PD: log 5-season mean < Q1 - 1.5*IQR of its group, AND in the group's lowest quartile in
  >= 4 of the 5 seasons. "candidate-PD" = bottom 10% of the group mean AND the same consistency
  rule (potential PDs, confirmed only at validation / fieldwork).
- Temporal PD: Theil-Sen slope of log(value + c) over the seasons (relative change per year) minus
  the group median slope; PD if deviance < Q1 - 1.5*IQR of the group's deviances.
  candidate-PD = bottom 10%. pct_per_year_vs_group = exp(slope_dev) - 1.
- Negative deviants: the mirror image (above Q3 + 1.5*IQR; top quartile >= 4 of 5; top 10%).
- Groups: frozen v4 Central and South-west only (Foothills excluded 2026-10-23; Outlier out).
  The merged Plains grouping (81 tehsils) is run as well and reported, not used to drop PDs.
Direct comparison of each tehsil with its group; no regression residuals (Prof. Aaditeshwar).

Input: any long table with one value per tehsil-year (lower = less burning).

Run:  python Code/pd/pd_identify.py --measure viirs
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
MIN_YEARS_IN_QUARTILE = 4
NEAR_SHARE = 0.10

# measure name -> (file, value column, seasons)
MEASURES = {
    "viirs": (ROOT / "outputs" / "burn_fire" / "tehsil_fire_measure.csv",
              "fires_per_1000ha_rice", range(2019, 2024)),
}


def load_groups():
    g = pd.read_csv(GROUPS)
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
        consistent_lo = d["years_bottom_q"] >= MIN_YEARS_IN_QUARTILE
        consistent_hi = d["years_top_q"] >= MIN_YEARS_IN_QUARTILE
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


def tehsil_stats(long, value, years, by):
    """Per tehsil: season mean, offset c of its group, Theil-Sen slope of log(value + c)."""
    long = long[long["year"].isin(years)]
    means = long.groupby(["lgd_tehsil_code", by])[value].mean()
    c = (NEAR_SHARE * means.groupby(by).median()).rename("c")
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


def run(long, value, years, groups, by):
    long = long.merge(groups[["lgd_tehsil_code", by]], on="lgd_tehsil_code")
    stats = tehsil_stats(long, value, years, by).merge(groups, on="lgd_tehsil_code")
    stats = stats.merge(quartile_years(long, value, years, by), on="lgd_tehsil_code")
    return flag_within(stats, by)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--measure", default="viirs", choices=MEASURES)
    args = ap.parse_args()
    path, value, years = MEASURES[args.measure]
    years = list(years)

    long = pd.read_csv(path)[["lgd_tehsil_code", "year", value]]
    groups = load_groups()
    missing = set(groups["lgd_tehsil_code"]) - set(long["lgd_tehsil_code"])
    assert not missing, f"tehsils without a burn value: {missing}"

    main_run = run(long, value, years, groups, "group")
    plains = run(long, value, years, groups, "group_2way")[
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

    out = ROOT / "outputs" / "pd" / args.measure
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

    print(f"measure={args.measure} value={value} seasons={years[0]}-{years[-1]}")
    print(summary.pivot_table(index=["kind", "flag"], columns="group", values="n", fill_value=0))
    flagged = t[(t["static"] != "") | (t["temporal"] != "")]
    print(flagged[["lgd_tehsil_name", "group", "mean", "years_bottom_q", "years_top_q",
                   "pct_per_year_vs_group",
                   "static", "temporal", "both", "survives_plains"]].to_string(index=False))


if __name__ == "__main__":
    main()
