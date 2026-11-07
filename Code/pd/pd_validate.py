"""
Positive deviant validation, checks V1-V6 (2026-11-07)

Plan [C] Soham, 2026-11-07 (task_pd_validation.md); DPPD Handbook p. 67-68 (time series, triangulation,
local knowledge). Thresholds are [P] and printed with the results. Units = tehsils robust under the old rule
(outputs/pd/robust/robust_deviants.csv); every check is computed for all 81 ranked tehsils so each unit is read
against its group.

  V1 bootstrap   resample each tehsil-year's points with replacement (= binomial draw on its verdicts), rerun
                 both runs (2020-24, 2020-23) B times; share of draws where the tehsil keeps its flag.
                 Strict units (PD/ND beyond the fence) are scored on the strict rule, others on the old rule.
                 >= 80% pass, 50-80% flag, < 50% fail
  V2 settings    cut 0.5; offset c 5% / 20%; alternative grouping (rainfall weight x0.85, which moves 5 tehsils
                 between Central and South-west). Kept (old rule) in all scenarios but one = pass, else flag
  V3 looks       unknown-point share and median clear looks per point in the window, vs group.
                 flag if unknown share > 2x group median and > 1 pt, or median looks < 0.75x group median
  V4 rice        (PDs only) calibrated rice share and share of panel points where a paddy harvest is seen
                 (harvest_gap.py), vs group. flag if either is below the group Q1
  V4b harvest    (2026-11-08, [C] Soham option A) the 30-point harvest panel (harvest_gap.py, first 30 points per
                 tehsil): burnt share on all 30 points vs only points where a paddy harvest is seen that season
                 (NDVI >= 0.45 then < 0.30 after 15 Sep). Both rerun through the same rules and runs. Kept (old
                 rule) on all 30 points but lost on harvest-confirmed ones = flag (the filter's own effect); otherwise pass.
                 Losses on both are the 30-vs-100-point sample size, not the filter. Does not remove cotton
  V5 timing      (PDs only) median paddy harvest date vs group; flag if >= 10 days later. Share of burnt
                 verdicts dated 20-30 Nov shown for reference
  V6 triangulate information only: VIIRS flags, district CREAMS 2020 / 2022 percentile among districts,
                 next-crop green-up date and no-green-up share vs group (Doaba rotation signal)
Final label (PDs): any fail -> dropped; <= 1 flag -> validated PD; else PD with caveat. NDs get the same
V1-V3 and the label "contrast". V7 (blind visual check, pd_visual_package.py --score -> v7_visual.csv) is read
when present and counts like the other checks; tehsils outside its sample show "not checked".

Run:  python Code/pd/pd_validate.py [--boot 1000] [--reuse-v1]   (--reuse-v1 reads the saved v1_bootstrap.csv)
Out:  outputs/pd/validation/v1_bootstrap.csv ... v6_triangulation.csv, v4b_harvest_confirmed.csv,
      outputs/pd/pd_validated.csv
"""

import argparse

import numpy as np
import pandas as pd

import pd_identify as pi

ROOT = pi.ROOT
PD = ROOT / "outputs" / "pd"
OUT = PD / "validation"
MEASURE = ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv"
VERDICTS = ROOT / "outputs" / "burn_tehsil_rf" / "point_verdicts.csv"
POINTS = ROOT / "outputs" / "burn_tehsil" / "points.csv"
MASTER = ROOT / "Data" / "punjab_homogeneous_grouping_master_raw_97tehsils.csv"
HARVEST = ROOT / "outputs" / "predictors" / "harvest_gap" / "tehsil_harvest_gap.csv"
HARVEST_POINTS = ROOT / "outputs" / "predictors" / "harvest_gap" / "point_dates.csv"
DISTRICT = ROOT / "outputs" / "burn_tehsil_rf" / "district_from_tehsils.csv"
SENS_LABELS = ROOT / "outputs" / "grouping" / "sensitivity_labels.csv"
ALT_SCENARIO = "weight_rainfall_x0.85"
RUNS = {"main": range(2020, 2025), "no2024": range(2020, 2024)}
SEED = 42


def pos(s):
    return s.isin(["PD", "candidate-PD"])


def neg(s):
    return s.isin(["ND", "candidate-ND"])


def two_runs(long, value, groups, c_share=pi.C_SHARE):
    """Static / temporal flags of every tehsil in both runs: columns {rule}_{run}."""
    t = None
    for tag, years in RUNS.items():
        d = pi.run(long, value, list(years), groups, "group", c_share)
        d = d[["lgd_tehsil_code", "static", "temporal"]].rename(
            columns={"static": f"static_{tag}", "temporal": f"temporal_{tag}"})
        t = d if t is None else t.merge(d, on="lgd_tehsil_code")
    return t.set_index("lgd_tehsil_code")


def kept(t, unit):
    """Does each unit keep its flag in this table? unit: rows with code, rule, kind, strict."""
    out = []
    for u in unit.itertuples():
        if u.lgd_tehsil_code not in t.index:
            out.append(False)
            continue
        a, b = t.at[u.lgd_tehsil_code, f"{u.rule}_main"], t.at[u.lgd_tehsil_code, f"{u.rule}_no2024"]
        if u.strict:
            out.append(a == u.kind and b == u.kind)
        else:
            f = pos if u.kind == "PD" else neg
            out.append(bool(f(pd.Series([a, b])).all()))
    return np.array(out)


def units():
    """One row per (tehsil, rule, kind) the tehsil is robust for; strict = beyond the fence in both runs."""
    r = pd.read_csv(PD / "robust" / "robust_deviants.csv").fillna("")
    g = pi.load_groups()[["lgd_tehsil_code", "lgd_tehsil_name"]]
    r = r[r.old_rule != ""].merge(g, on="lgd_tehsil_name")
    rows = []
    for x in r.itertuples():
        kind = "PD" if x.old_rule.startswith("PD") else "ND"
        for rule in ["static", "temporal"]:
            if rule in x.old_rule:
                strict = f"{kind} {rule}" in [s.strip() for s in x.strict_rule.split(",")]
                rows.append({"lgd_tehsil_code": x.lgd_tehsil_code, "lgd_tehsil_name": x.lgd_tehsil_name,
                             "group": x.group, "rule": rule, "kind": kind, "strict": strict,
                             "strict_rule": x.strict_rule})
    return pd.DataFrame(rows)


def v1_bootstrap(unit, groups, n_boot):
    m = pd.read_csv(MEASURE)
    m = m[m.lgd_tehsil_code.isin(groups.lgd_tehsil_code)][["lgd_tehsil_code", "year", "burnt_share", "n_look"]]
    k = np.round(m.burnt_share * m.n_look).astype(int).to_numpy()
    n = m.n_look.to_numpy()
    rng = np.random.default_rng(SEED)
    hits = np.zeros(len(unit))
    for b in range(n_boot):
        draw = m[["lgd_tehsil_code", "year"]].assign(burnt_share=rng.binomial(n, k / n) / n)
        hits += kept(two_runs(draw, "burnt_share", groups), unit)
        if (b + 1) % 100 == 0:
            print(f"  V1 bootstrap {b + 1}/{n_boot}", flush=True)
    return unit.assign(boot_keep=hits / n_boot)


def alt_groups():
    """Frozen groups with the tehsils the alternative scenario moves put in their new group."""
    s = pd.read_csv(SENS_LABELS)
    g = pd.read_csv(pi.GROUPS)
    s = s.merge(g[["lgd_tehsil_name", "lgd_tehsil_code", "group"]], on="lgd_tehsil_name")
    name = s.groupby("baseline")["group"].agg(lambda x: x.mode()[0])
    s["alt"] = np.where(s[ALT_SCENARIO] == s["baseline"], s["group"], s[ALT_SCENARIO].map(name))
    path = OUT / f"groups_{ALT_SCENARIO}.csv"
    s[["lgd_tehsil_code", "lgd_tehsil_name", "group", "alt"]].rename(
        columns={"group": "frozen_group", "alt": "group"}).to_csv(path, index=False)
    moved = s[s.alt != s.group]
    print(f"  V2 alternative grouping {ALT_SCENARIO}: moved "
          + "; ".join(f"{r.lgd_tehsil_name} {r.group}->{r.alt}" for r in moved.itertuples()))
    return path


def v2_settings(unit, long, groups):
    scen = {
        "cut_0.5": two_runs(long.rename(columns={"burnt_share": "x", "burnt_share_05": "burnt_share"}),
                            "burnt_share", groups),
        "c_5pct": two_runs(long, "burnt_share", groups, 0.05),
        "c_20pct": two_runs(long, "burnt_share", groups, 0.20),
        "alt_grouping": two_runs(long, "burnt_share", pi.load_groups(alt_groups())),
    }
    old = unit.assign(strict=False)
    out = unit.copy()
    for name, t in scen.items():
        out[f"{name}_old_rule"] = kept(t, old)
        out[f"{name}_strict"] = kept(t, unit.assign(strict=True))
    old_cols = [c for c in out if c.endswith("_old_rule")]
    out["v2_kept_old_rule"] = out[old_cols].sum(axis=1)
    out["v2_scenarios"] = len(old_cols)
    return out


def vs_group(df, col, groups):
    d = df if "group" in df else df.merge(groups[["lgd_tehsil_code", "group"]], on="lgd_tehsil_code")
    q = d.groupby("group")[col]
    return d.assign(**{f"{col}_grp_median": q.transform("median"), f"{col}_grp_q1": q.transform(lambda x: x.quantile(0.25))})


def v3_looks(groups):
    m = pd.read_csv(MEASURE)
    m = m[m.year.isin(RUNS["main"])]
    unk = (m.groupby("lgd_tehsil_code").n_unknown.sum() / m.groupby("lgd_tehsil_code").n_points.sum()).rename("unknown_share")
    v = pd.read_csv(VERDICTS).merge(pd.read_csv(POINTS)[["loc", "lgd_tehsil_code"]], on="loc")
    looks = v[v.year.isin(RUNS["main"])].groupby("lgd_tehsil_code").n_win.median().rename("looks_median")
    d = pd.concat([unk, looks], axis=1).reset_index()
    d = vs_group(vs_group(d, "unknown_share", groups), "looks_median", groups)
    d["v3_flag"] = (((d.unknown_share > 2 * d.unknown_share_grp_median) & (d.unknown_share - d.unknown_share_grp_median > 0.01))
                    | (d.looks_median < 0.75 * d.looks_median_grp_median))
    return d


def v4_rice(groups):
    r = pd.read_csv(MASTER)[["lgd_tehsil_code", "rice_share_2022_cal", "calibration_factor"]]
    h = pd.read_csv(HARVEST)
    h = h[h.year.isin(RUNS["main"])].groupby("lgd_tehsil_code").harvest_found.mean().rename("harvest_found").reset_index()
    d = r.merge(h, on="lgd_tehsil_code")
    d = vs_group(vs_group(d, "rice_share_2022_cal", groups), "harvest_found", groups)
    d["v4_flag"] = (d.rice_share_2022_cal < d.rice_share_2022_cal_grp_q1) | (d.harvest_found < d.harvest_found_grp_q1)
    return d


def v4b_harvest_confirmed(unit, groups):
    v = pd.read_csv(VERDICTS)[["loc", "year", "burnt"]]
    h = pd.read_csv(HARVEST_POINTS)[["loc", "year", "harvest"]]
    d = h.merge(v, on=["loc", "year"]).merge(pd.read_csv(POINTS)[["loc", "lgd_tehsil_code"]], on="loc")
    d = d[d.burnt.notna()].assign(confirmed=lambda x: x.harvest.notna())
    long = d.groupby(["lgd_tehsil_code", "year"]).agg(
        share_30=("burnt", "mean"), n_30=("burnt", "size"), n_confirmed=("confirmed", "sum")).reset_index()
    long = long.merge(d[d.confirmed].groupby(["lgd_tehsil_code", "year"]).burnt.mean().rename("share_confirmed")
                      .reset_index(), on=["lgd_tehsil_code", "year"], how="left")
    long = long[long.lgd_tehsil_code.isin(groups.lgd_tehsil_code)]
    out = unit.copy()
    for col in ["share_30", "share_confirmed"]:
        t = two_runs(long.rename(columns={col: "value"}), "value", groups)
        out[f"{col}_old_rule"] = kept(t, unit.assign(strict=False))
        out[f"{col}_strict"] = kept(t, unit.assign(strict=True))
        for tag in RUNS:
            out[f"{col}_static_{tag}"] = out.lgd_tehsil_code.map(t[f"static_{tag}"])
            out[f"{col}_temporal_{tag}"] = out.lgd_tehsil_code.map(t[f"temporal_{tag}"])
    main = long[long.year.isin(RUNS["main"])]
    m = main.groupby("lgd_tehsil_code").agg(mean_30=("share_30", "mean"), mean_confirmed=("share_confirmed", "mean"),
                                            confirmed_share=("n_confirmed", "sum"), n=("n_30", "sum"))
    m["confirmed_share"] = m.confirmed_share / m.n
    m = vs_group(vs_group(m.drop(columns="n").reset_index(), "mean_30", groups), "mean_confirmed", groups)
    # are burnt verdicts themselves less often harvest-confirmed? (would bias the confirmed share down)
    burnt_conf = d[d.year.isin(RUNS["main"]) & (d.burnt == 1)].groupby("lgd_tehsil_code").confirmed.mean()
    m["burnt_points_confirmed"] = m.lgd_tehsil_code.map(burnt_conf)
    out = out.merge(m.drop(columns="group"), on="lgd_tehsil_code")
    out["v4b"] = np.where(out.share_30_old_rule & ~out.share_confirmed_old_rule, "flag", "pass")
    return out


def v5_timing(groups):
    h = pd.read_csv(HARVEST)
    h = h[h.year.isin(RUNS["main"])].groupby("lgd_tehsil_code").harvest_doy_median.median().rename("harvest_doy").reset_index()
    v = pd.read_csv(VERDICTS).merge(pd.read_csv(POINTS)[["loc", "lgd_tehsil_code"]], on="loc")
    v = v[v.year.isin(RUNS["main"]) & (v.burnt == 1)]
    date = pd.to_datetime(v.candidate_date)
    late = (date.dt.month.eq(11) & date.dt.day.ge(20)).groupby(v.lgd_tehsil_code).mean().rename("burnt_late_nov_share")
    d = vs_group(h.merge(late.reset_index(), on="lgd_tehsil_code", how="left"), "harvest_doy", groups)
    d["harvest_days_vs_group"] = d.harvest_doy - d.harvest_doy_grp_median
    d["v5_flag"] = d.harvest_days_vs_group >= 10
    return d


def v6_triangulation(groups):
    r = pd.read_csv(PD / "robust" / "robust_deviants.csv")[["lgd_tehsil_name", "static_viirs", "temporal_viirs"]]
    g = pd.read_csv(pi.GROUPS)[["lgd_tehsil_code", "lgd_tehsil_name", "lgd_district_name"]]
    d = g.merge(r, on="lgd_tehsil_name", how="left")
    dist = pd.read_csv(DISTRICT)
    for y in (2020, 2022):
        p = dist[dist.year == y].set_index("district").creams_pct.rank(pct=True).rename(f"creams_{y}_pctile")
        d = d.merge(p, left_on="lgd_district_name", right_index=True, how="left")
    h = pd.read_csv(HARVEST)
    h = h[h.year.isin(RUNS["main"])].groupby("lgd_tehsil_code")[["greenup_doy_median", "no_greenup_share"]].median().reset_index()
    d = d.merge(h, on="lgd_tehsil_code", how="left")
    d = d[d.lgd_tehsil_code.isin(groups.lgd_tehsil_code)]
    return vs_group(vs_group(d, "greenup_doy_median", groups), "no_greenup_share", groups)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--reuse-v1", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    groups = pi.load_groups()
    unit = units()
    long = pd.read_csv(MEASURE)[["lgd_tehsil_code", "year", "burnt_share", "burnt_share_05"]]

    v3, v4, v5, v6 = v3_looks(groups), v4_rice(groups), v5_timing(groups), v6_triangulation(groups)
    v2 = v2_settings(unit, long, groups)
    v4b = v4b_harvest_confirmed(unit, groups)
    v1 = pd.read_csv(OUT / "v1_bootstrap.csv") if args.reuse_v1 else v1_bootstrap(unit, groups, args.boot)
    for name, d in [("v1_bootstrap", v1), ("v2_settings", v2), ("v3_looks", v3), ("v4_rice", v4),
                    ("v4b_harvest_confirmed", v4b), ("v5_timing", v5), ("v6_triangulation", v6)]:
        d.round(4).to_csv(OUT / f"{name}.csv", index=False)

    t = v1.merge(v2[["lgd_tehsil_code", "rule", "kind", "v2_kept_old_rule", "v2_scenarios"]],
                 on=["lgd_tehsil_code", "rule", "kind"])
    t = t.merge(v3[["lgd_tehsil_code", "unknown_share", "looks_median", "v3_flag"]], on="lgd_tehsil_code")
    t = t.merge(v4[["lgd_tehsil_code", "rice_share_2022_cal", "rice_share_2022_cal_grp_median", "calibration_factor",
                    "harvest_found", "harvest_found_grp_median", "v4_flag"]], on="lgd_tehsil_code")
    t = t.merge(v4b[["lgd_tehsil_code", "rule", "kind", "mean_30", "mean_confirmed", "mean_confirmed_grp_median",
                     "confirmed_share", "v4b"]], on=["lgd_tehsil_code", "rule", "kind"])
    t = t.merge(v5[["lgd_tehsil_code", "harvest_days_vs_group", "burnt_late_nov_share", "v5_flag"]], on="lgd_tehsil_code")
    t = t.merge(v6[["lgd_tehsil_code", "static_viirs", "temporal_viirs", "creams_2020_pctile", "creams_2022_pctile",
                    "greenup_doy_median", "greenup_doy_median_grp_median", "no_greenup_share"]], on="lgd_tehsil_code")

    t["v1"] = np.select([t.boot_keep >= 0.8, t.boot_keep >= 0.5], ["pass", "flag"], "fail")
    t["v2"] = np.where(t.v2_kept_old_rule >= t.v2_scenarios - 1, "pass", "flag")
    is_pd = t.kind == "PD"
    t["v3"] = np.where(t.v3_flag, "flag", "pass")
    t["v4"] = np.where(~is_pd, "n/a", np.where(t.v4_flag, "flag", "pass"))
    t["v4b"] = np.where(~is_pd, "n/a", t.v4b)
    t["v5"] = np.where(~is_pd, "n/a", np.where(t.v5_flag, "flag", "pass"))
    v7 = OUT / "v7_visual.csv"
    t["v7"] = "not checked"
    if v7.exists():
        t["v7"] = t.lgd_tehsil_name.map(pd.read_csv(v7).set_index("lgd_tehsil_name").v7).fillna("not checked")
    checks = ["v1", "v2", "v3", "v4", "v4b", "v5", "v7"]
    t["n_flags"] = (t[checks] == "flag").sum(axis=1)
    t["reasons"] = t.apply(lambda r: "; ".join(f"{c}:{r[c]}" for c in checks if r[c] in ("flag", "fail")), axis=1)
    t["label"] = np.where(~is_pd, "contrast",
                          np.select([(t[checks] == "fail").any(axis=1), t.n_flags <= 1],
                                    ["dropped", "validated PD"], "PD with caveat"))
    t = t.drop(columns=["v3_flag", "v4_flag", "v5_flag"]).sort_values(["kind", "rule", "group", "lgd_tehsil_name"])
    t.round(4).to_csv(PD / "pd_validated.csv", index=False)

    pd.set_option("display.width", 250)
    print(t[["lgd_tehsil_name", "group", "kind", "rule", "strict", "boot_keep", "v2_kept_old_rule", "v1", "v2", "v3",
             "v4", "v4b", "v5", "label", "reasons"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
