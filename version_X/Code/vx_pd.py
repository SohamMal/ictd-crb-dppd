"""
Version X, step 4: village positive deviants, identification + validation (2026-11-10)

Identification = the main version's rules (Code/pd/pd_identify.py, 2026-10-23), unit = village, compared only
with villages of the same peer group = version-X group x rice-share band (vx_grouping.py, vx_peer_groups.py):
  static PD     log(5-season mean + c) < Q1 - 1.5 IQR of the group, AND in the group's lowest quartile in all
                seasons but one; candidate-PD = bottom 10% of the group mean + the same consistency rule
  temporal PD   Theil-Sen slope of log(value + c) minus the group median slope < Q1 - 1.5 IQR; candidate = bottom 10%
  NDs           the mirror image. c = 10% of the group median of village means. No regression residuals.
Village rules added because one village-season rests on ~11 points, not 100:
  season used   only if >= MIN_LOOK points have a verdict; village ranked only if >= MIN_SEASONS seasons
Validation (main version V1-V5, adapted):
  V1 bootstrap  redraw of every village-season: p ~ Beta(k + 0.5, n - k + 0.5) (Jeffreys), then Binomial(n, p)
                (a plain binomial redraw would keep a 0-of-11 season at 0 in every draw); rerun both rules, B draws;
                share of draws keeping the flag (PD or candidate-PD counts as kept). >= 0.8 pass, 0.5-0.8 flag, < 0.5 fail
  V2 settings   (a) cut 0.5 instead of 0.786, (b) peers = inherited tehsil region x rice band, (c) peers = village
                group without rice bands. Static: kept in >= 2 of 3 = pass, 1 = flag, 0 = fail. Temporal (b, c
                only): kept in both = pass, one = flag, none = fail
  V3 looks      mean points with a verdict per season < 0.75 x group median = flag
  V4 rice       share of harvest panel points (3 per village) with a paddy harvest seen < group Q1 = flag
  V5 timing     median harvest date >= 10 days later than the group median = flag
Final label: any fail -> dropped; <= 1 flag -> validated PD; more -> PD with caveat. NDs: V1-V3 -> "contrast" if
no fail. Strict PD (beyond the fence) and candidate-PD are reported separately.

Run:  python version_X/Code/vx_pd.py [--boot 200]
Out:  version_X/outputs/pd/pd_table.csv, pd_validated.csv, summary.csv, tehsil_overlap.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import theilslopes

ROOT = Path(__file__).resolve().parents[2]
VX = ROOT / "version_X" / "outputs"
OUT = VX / "pd"
ID = "c2011_village_code"
YEARS = list(range(2020, 2025))
MIN_LOOK, MIN_SEASONS = 5, 4
MAX_MISSED, NEAR, C_SHARE = 1, 0.10, 0.10
SEED = 42


def iqr_bounds(x):
    q1, q3 = np.percentile(x, [25, 75])
    return q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)


def slopes(long, value):
    """Theil-Sen slope per village of log(value + c); vectorised over villages with the same seasons."""
    out = {}
    for code, d in long.groupby(ID):
        y = np.log(d[value].to_numpy() + d["c"].to_numpy())
        out[code] = theilslopes(y, d.year.to_numpy())[0] if np.unique(y).size > 1 else 0.0
    return pd.Series(out, name="slope")


def identify(long, value, by, with_temporal=True):
    """long: one row per village-season (ID, year, value, by). Returns one row per village with flags."""
    means = long.groupby([ID, by])[value].mean().rename("mean").reset_index()
    c = (C_SHARE * means.groupby(by)["mean"].median()).rename("c")
    means = means.merge(c, left_on=by, right_index=True)
    long = long.merge(c, left_on=by, right_index=True)
    q = long.groupby([by, "year"])[value]
    long = long.assign(bottom=long[value] <= q.transform(lambda x: x.quantile(0.25)),
                       top=long[value] >= q.transform(lambda x: x.quantile(0.75)))
    qy = long.groupby(ID).agg(years_bottom_q=("bottom", "sum"), years_top_q=("top", "sum"), n_years=("year", "size"))
    t = means.merge(qy, left_on=ID, right_index=True)
    if with_temporal:
        t = t.merge(slopes(long, value), left_on=ID, right_index=True)
    rows = []
    for _, d in t.groupby(by):
        d = d.copy()
        k = max(1, int(round(NEAR * len(d))))
        lm = np.log(d["mean"] + d["c"])
        lo, hi = iqr_bounds(lm)
        clo = d.years_bottom_q >= d.n_years - MAX_MISSED
        chi = d.years_top_q >= d.n_years - MAX_MISSED
        rlo, rhi = d["mean"].rank(method="min"), d["mean"].rank(method="min", ascending=False)
        d["static"] = np.select([(lm < lo) & clo, (rlo <= k) & clo, (lm > hi) & chi, (rhi <= k) & chi],
                                ["PD", "candidate-PD", "ND", "candidate-ND"], "")
        if with_temporal:
            d["slope_dev"] = d.slope - d.slope.median()
            lo, hi = iqr_bounds(d.slope_dev)
            rlo, rhi = d.slope_dev.rank(method="min"), d.slope_dev.rank(method="min", ascending=False)
            d["temporal"] = np.select([d.slope_dev < lo, rlo <= k, d.slope_dev > hi, rhi <= k],
                                      ["PD", "candidate-PD", "ND", "candidate-ND"], "")
            d["pct_per_year_vs_group"] = 100 * (np.exp(d.slope_dev) - 1)
        d["n_in_group"] = len(d)
        rows.append(d)
    return pd.concat(rows)


def side(flag):
    return np.where(pd.Series(flag).str.endswith("PD"), "PD", np.where(pd.Series(flag).str.endswith("ND"), "ND", ""))


def load():
    vm = pd.read_csv(VX / "burn" / "village_burn_measure.csv", dtype={ID: str})
    vg = pd.read_csv(VX / "grouping" / "village_groups.csv", dtype={ID: str, "lgd_tehsil_code": str})
    vm = vm[vm.year.isin(YEARS) & (vm.n_look >= MIN_LOOK)]
    ok = vm.groupby(ID).year.count()
    vm = vm[vm[ID].isin(ok[ok >= MIN_SEASONS].index)]
    long = vm.merge(vg[[ID, "peer", "region_peer", "vgroup", "tehsil_region"]], on=ID)
    return long, vg


def bootstrap(long, B, rng):
    keep = {("static", "main"): [], ("temporal", "main"): []}
    n = long.n_look.to_numpy()
    k = long.n_burnt.to_numpy()
    for b in range(B):
        p = rng.beta(k + 0.5, n - k + 0.5)       # Jeffreys posterior: a 0-of-11 season is not certainly 0
        x = long.assign(bs=rng.binomial(n, p) / n)
        f = identify(x[[ID, "year", "bs", "peer"]], "bs", "peer").set_index(ID)
        keep[("static", "main")].append(pd.Series(side(f.static), index=f.index))
        keep[("temporal", "main")].append(pd.Series(side(f.temporal), index=f.index))
        if b % 20 == 0:
            print(f"  bootstrap {b}/{B}", flush=True)
    return {k: pd.concat(v, axis=1) for k, v in keep.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=200)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    long, vg = load()
    print(f"ranked villages: {long[ID].nunique()} | village-seasons {len(long)} | "
          f"median verdicts per village-season {long.n_look.median()}", flush=True)

    t = identify(long[[ID, "year", "burnt_share", "peer"]], "burnt_share", "peer")
    a = identify(long[[ID, "year", "burnt_share_05", "peer"]], "burnt_share_05", "peer", False)
    r = identify(long[[ID, "year", "burnt_share", "region_peer"]], "burnt_share", "region_peer")
    g = identify(long[[ID, "year", "burnt_share", "vgroup"]], "burnt_share", "vgroup")
    t = t.merge(a[[ID, "static"]].rename(columns={"static": "static_cut05"}), on=ID).merge(
        r[[ID, "static", "temporal"]].rename(columns={"static": "static_region", "temporal": "temporal_region"}),
        on=ID).merge(g[[ID, "static", "temporal"]].rename(columns={"static": "static_nobands",
                                                                    "temporal": "temporal_nobands"}), on=ID)
    t = t.merge(long.groupby(ID)[["vgroup", "tehsil_region"]].first(), left_on=ID, right_index=True)
    looks = long.groupby(ID).n_look.mean().rename("looks_mean")
    t = t.merge(looks, left_on=ID, right_index=True)

    bs = bootstrap(long, args.boot, rng)
    for kind in ["static", "temporal"]:
        m = bs[(kind, "main")]
        obs = pd.Series(side(t[kind]), index=t[ID])
        t[f"boot_keep_{kind}"] = [(m.loc[c] == s).mean() if s else np.nan for c, s in obs.items()]

    hg = pd.read_csv(VX / "predictors" / "harvest_gap" / "point_dates.csv", dtype={ID: str},
                     parse_dates=["harvest", "greenup"])
    hg = hg[hg.year.isin(YEARS)]
    hg["harvest_doy"] = hg.harvest.dt.dayofyear
    hv = hg.groupby(ID).agg(harvest_found=("harvest", lambda s: s.notna().mean()),
                            harvest_doy=("harvest_doy", "median"))
    t = t.merge(hv, left_on=ID, right_index=True, how="left")
    t = t.merge(vg[[ID, "c2011_village_name", "lgd_tehsil_code", "lgd_tehsil_name", "lgd_district_name",
                    "rice_share_2022_cal", "rice_ha_2022_cal"]], on=ID)

    labs = []
    for kind in ["static", "temporal"]:
        u = t[t[kind] != ""].copy()
        u["kind"], u["rule"], u["flag_side"] = kind, u[kind], side(u[kind])
        u["boot_keep"] = u[f"boot_keep_{kind}"]
        labs.append(u)
    u = pd.concat(labs, ignore_index=True)
    grp = t.groupby("peer").agg(looks_g=("looks_mean", "median"), hf_q1=("harvest_found", lambda s: s.quantile(.25)),
                                  hd_g=("harvest_doy", "median"))
    u = u.merge(grp, left_on="peer", right_index=True)
    u["v1"] = np.select([u.boot_keep >= 0.8, u.boot_keep >= 0.5], ["pass", "flag"], "fail")
    if_static = u.kind == "static"
    kept_a = side(u.static_cut05) == u.flag_side
    kept_b = np.where(if_static, side(u.static_region) == u.flag_side, side(u.temporal_region) == u.flag_side)
    kept_c = np.where(if_static, side(u.static_nobands) == u.flag_side, side(u.temporal_nobands) == u.flag_side)
    nk = kept_b.astype(int) + kept_c.astype(int) + np.where(if_static, kept_a.astype(int), 0)
    need = np.where(if_static, 2, 2)                    # static: 2 of 3; temporal: 2 of 2
    u["v2_kept"] = nk.astype(str) + "/" + np.where(if_static, "3", "2")
    u["v2"] = np.select([nk >= need, nk >= 1], ["pass", "flag"], "fail")
    u["v3"] = np.where(u.looks_mean < 0.75 * u.looks_g, "flag", "pass")
    pdm = u.flag_side == "PD"
    u["v4"] = np.where(pdm, np.where(u.harvest_found < u.hf_q1, "flag", "pass"), "n/a")
    u["v5"] = np.where(pdm, np.where(u.harvest_doy - u.hd_g >= 10, "flag", "pass"), "n/a")
    checks = ["v1", "v2", "v3", "v4", "v5"]
    u["n_fail"] = (u[checks] == "fail").sum(axis=1)
    u["n_flags"] = (u[checks] == "flag").sum(axis=1)
    u["reasons"] = u[checks].apply(lambda s: "; ".join(f"{k}:{v}" for k, v in s.items() if v in ("flag", "fail")), axis=1)
    u["label"] = np.select([u.n_fail > 0, ~pdm, u.n_flags <= 1], ["dropped", "contrast", "validated PD"], "PD with caveat")
    u["strict"] = u.rule.isin(["PD", "ND"])

    cols = [ID, "c2011_village_name", "lgd_tehsil_name", "lgd_district_name", "peer", "vgroup", "tehsil_region",
            "n_in_group",
            "n_years", "mean", "c", "years_bottom_q", "years_top_q", "slope_dev", "pct_per_year_vs_group",
            "static", "temporal", "static_cut05", "static_region", "temporal_region", "static_nobands",
            "temporal_nobands", "boot_keep_static",
            "boot_keep_temporal", "looks_mean", "harvest_found", "harvest_doy", "rice_share_2022_cal",
            "rice_ha_2022_cal", "lgd_tehsil_code"]
    t[cols].sort_values(["peer", "mean"]).round(4).to_csv(OUT / "pd_table.csv", index=False)
    ucols = [ID, "c2011_village_name", "lgd_tehsil_name", "lgd_district_name", "peer", "kind", "rule", "strict",
             "flag_side", "mean", "pct_per_year_vs_group", "boot_keep", "v2_kept"] + checks + ["n_flags", "reasons", "label",
             "rice_share_2022_cal", "lgd_tehsil_code"]
    u[ucols].round(4).to_csv(OUT / "pd_validated.csv", index=False)

    s = u.groupby(["kind", "flag_side", "strict", "label"]).size().rename("n").reset_index()
    s.to_csv(OUT / "summary.csv", index=False)
    print("\nflags per group (static):")
    print(pd.crosstab(t.peer, t.static))
    print("\nflags per group (temporal):")
    print(pd.crosstab(t.peer, t.temporal))
    print("\nvalidation outcome:")
    print(s.to_string(index=False))

    # where do village PDs sit relative to the tehsil-level picture?
    tp = pd.read_csv(ROOT / "outputs" / "pd" / "pd_validated.csv", dtype={"lgd_tehsil_code": str})
    tp = tp[tp.label != "dropped"].drop_duplicates(["lgd_tehsil_code", "kind"])
    tlab = tp.assign(tl=tp.rule + ":" + tp.kind).groupby(
        "lgd_tehsil_code").tl.agg(", ".join)
    val = u[u.label.isin(["validated PD", "PD with caveat"]) & (u.kind == "static")]
    ov = t.groupby(["lgd_tehsil_code", "lgd_tehsil_name"]).agg(villages_ranked=(ID, "size"),
                                                               tehsil_mean_of_villages=("mean", "mean")).reset_index()
    ov = ov.merge(val.groupby("lgd_tehsil_code").size().rename("village_pds_static"), on="lgd_tehsil_code", how="left")
    ov["village_pds_static"] = ov.village_pds_static.fillna(0).astype(int)
    ov["share_pd_villages"] = ov.village_pds_static / ov.villages_ranked
    ov["tehsil_label_main_version"] = ov.lgd_tehsil_code.map(tlab).fillna("")
    ov.sort_values("share_pd_villages", ascending=False).round(4).to_csv(OUT / "tehsil_overlap.csv", index=False)
    print("\nvillage static PDs (validated + caveat) by tehsil label of the main version:")
    ov["tl"] = np.where(ov.tehsil_label_main_version.str.contains("static:PD"), "tehsil static PD",
                        np.where(ov.tehsil_label_main_version.str.contains("static:ND"), "tehsil static ND", "other"))
    print(ov.groupby("tl")[["villages_ranked", "village_pds_static"]].sum().assign(
        share=lambda d: (d.village_pds_static / d.villages_ranked).round(3)))


if __name__ == "__main__":
    main()
