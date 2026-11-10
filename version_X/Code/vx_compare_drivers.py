"""
Version X, Stage 3 analysis: village PDs vs peers, driver by driver (2026-11-10)

Village level gives hundreds of ranked units instead of 81 tehsils, so beyond the main version's descriptive
reading (compare_drivers.py) the drivers can be tested. Still observational: these are associations, not causes.
All readings are WITHIN peer groups (village group x rice band, vx_peer_groups.py): every value is first turned
into its percentile inside the village's peer group (0 = lowest, 1 = highest), so peers with different climate or
rice share are never compared directly.

  A. PD profile      validated village PDs (static; "validated PD" + "PD with caveat"): median driver percentile,
                     share of PDs on the side the hypothesis expects, Mann-Whitney PD vs the other villages
  B. ND profile      the same for static NDs ("contrast"), expecting the opposite side
  C. gradient        Spearman of driver percentile vs burn percentile over all ranked villages; 95% CI by tehsil
                     cluster bootstrap (villages of one tehsil share district policy, so they are not independent)
  D. within tehsil   each PD's driver percentile among the ranked villages of its own tehsil: removes district and
                     tehsil-level differences (basmati share is district-level, so D7 is not read here). Sign test
  p-values of A, B, D are Holm-corrected over the 12 drivers (*_holm). "expected side" < 0.5 = PDs lean AGAINST
  the hypothesis
  F. robustness      D repeated for PDs with V5 pass (harvest not >= 10 days later than peers)
  E. joint           least squares of burn percentile on all driver percentiles at once (+ rice-share percentile),
                     tehsil cluster-bootstrap CI; and a random forest with tehsil-grouped 5-fold CV (out-of-tehsil
                     R2) + permutation importance, to see how much the 8 drivers explain together
Expected sign = the main version's hypotheses (task_predictor_data.md).

Run:  python version_X/Code/vx_compare_drivers.py
Out:  version_X/outputs/predictors/driver_summary.csv, joint_model.csv, robustness_v5_pass.csv, pd_profiles.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, mannwhitneyu, spearmanr
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parents[2]
VX = ROOT / "version_X" / "outputs"
OUT = VX / "predictors"
ID = "c2011_village_code"
B, SEED = 500, 42

DRIVERS = {
    "d1_turnaround_days": ("Harvest-to-wheat turnaround (days)", -1),
    "d1_harvest_doy": ("Paddy harvest date (day of year)", +1),
    "d2_early_canopy_share": ("Early second crop (potato/veg) share", -1),
    "d3_labourers_per_cultivator": ("Farm labourers per cultivator (2011)", -1),
    "d3_cultivators_per_100ha_rice": ("Cultivators per 100 ha rice (small farms, 2011)", -1),
    "d4_km_nearest_buyer": ("km to nearest straw buyer", +1),
    "d5_km_interstate_border": ("km to inter-state border", -1),
    "d5_km_international_border": ("km to international border", 0),
    "d6_km_urban_centre": ("km to nearest urban centre", +1),
    "d6_km_any_urban": ("km to nearest town (any urban cell)", +1),
    "d7_basmati_share_district": ("Basmati share of rice (district)", -1),
    "d9_bovines_per_cultivator": ("Cattle + buffalo per cultivator (2019)", -1),
}


def pct(s, by):
    return s.groupby(by).rank(pct=True)


def cluster_boot(df, fn, rng):
    teh = df.lgd_tehsil_code.unique()
    groups = {t: g for t, g in df.groupby("lgd_tehsil_code")}
    out = []
    for _ in range(B):
        pick = rng.choice(teh, len(teh), replace=True)
        out.append(fn(pd.concat([groups[t] for t in pick], ignore_index=True)))
    return np.percentile(np.array(out), [2.5, 97.5], axis=0)


def main():
    rng = np.random.default_rng(SEED)
    t = pd.read_csv(VX / "pd" / "pd_table.csv", dtype={ID: str, "lgd_tehsil_code": str})
    v = pd.read_csv(VX / "pd" / "pd_validated.csv", dtype={ID: str})
    d = pd.read_csv(OUT / "village_drivers.csv", dtype={ID: str})
    x = t.merge(d, on=ID, how="left")
    st = v[v.kind == "static"]
    pds = set(st[st.label.isin(["validated PD", "PD with caveat"])][ID])
    nds = set(st[st.label == "contrast"][ID])
    x["is_pd"], x["is_nd"] = x[ID].isin(pds), x[ID].isin(nds)
    x["burn_p"] = pct(x["mean"], x.peer)
    x["rice_p"] = pct(x.rice_share_2022_cal, x.peer)
    for c in DRIVERS:
        x[c + "_p"] = pct(x[c], x.peer)
        x[c + "_pt"] = pct(x[c], x.lgd_tehsil_code)
    print(f"ranked villages {len(x)} | static PDs kept {len(pds)} | static NDs {len(nds)}")

    rows = []
    for c, (name, sign) in DRIVERS.items():
        p = x[c + "_p"]
        ok = p.notna()
        pdp, ndp, rest = p[x.is_pd & ok], p[x.is_nd & ok], p[~x.is_pd & ~x.is_nd & ok]
        r = {"driver": c, "name": name, "expected_sign": sign, "coverage": round(ok.mean(), 3)}
        r["pd_n"], r["pd_median_pctile"] = len(pdp), round(pdp.median(), 3)
        r["nd_n"], r["nd_median_pctile"] = len(ndp), round(ndp.median(), 3)
        if sign != 0 and len(pdp):
            # sign +1: more of the driver -> more burning, so PDs are expected BELOW the peer median
            exp_pd = (pdp < 0.5) if sign > 0 else (pdp > 0.5)
            r["pd_expected_side"] = round(exp_pd.mean(), 3)
            exp_nd = (ndp > 0.5) if sign > 0 else (ndp < 0.5)
            r["nd_expected_side"] = round(exp_nd.mean(), 3) if len(ndp) else np.nan
        r["pd_vs_rest_p"] = mannwhitneyu(pdp, rest).pvalue if len(pdp) > 2 else np.nan
        r["nd_vs_rest_p"] = mannwhitneyu(ndp, rest).pvalue if len(ndp) > 2 else np.nan
        sub = x[ok & x.burn_p.notna()][["lgd_tehsil_code", "burn_p", c + "_p"]]
        rho = spearmanr(sub[c + "_p"], sub.burn_p)[0]
        lo, hi = cluster_boot(sub, lambda s: spearmanr(s[c + "_p"], s.burn_p)[0], rng)
        r.update(rho_gradient=round(rho, 3), rho_ci_lo=round(lo, 3), rho_ci_hi=round(hi, 3))
        for grp in sorted(x.peer.str[:2].unique()):
            s = sub[x.loc[sub.index, "peer"].str.startswith(grp)]
            r[f"rho_{grp}"] = round(spearmanr(s[c + "_p"], s.burn_p)[0], 3)
        if c != "d7_basmati_share_district":
            w = x[x.is_pd][c + "_pt"].dropna()
            if sign != 0 and len(w):
                k = int(((w < 0.5) if sign > 0 else (w > 0.5)).sum())
                r["within_tehsil_expected_side"] = round(k / len(w), 3)
                r["within_tehsil_sign_p"] = binomtest(k, len(w), 0.5).pvalue
        rows.append(r)
    s = pd.DataFrame(rows)
    for col in ["pd_vs_rest_p", "nd_vs_rest_p", "within_tehsil_sign_p"]:   # Holm over the 12 drivers
        q = s[col].dropna().sort_values()
        m = len(q)
        adj = np.minimum(1, np.maximum.accumulate([(m - i) * v for i, v in enumerate(q)]))
        s.loc[q.index, col + "_holm"] = adj
    s["ci_excludes_0"] = (s.rho_ci_lo > 0) | (s.rho_ci_hi < 0)
    s.to_csv(OUT / "driver_summary.csv", index=False, float_format="%.4g")
    print(s[["driver", "expected_sign", "pd_median_pctile", "pd_expected_side", "pd_vs_rest_p_holm",
             "nd_median_pctile", "nd_expected_side", "nd_vs_rest_p_holm", "rho_gradient", "rho_ci_lo", "rho_ci_hi",
             "within_tehsil_expected_side", "within_tehsil_sign_p_holm"]].to_string(index=False))

    # E. joint models on within-peer percentiles (missing driver -> 0.5 = peer median, flagged by coverage above)
    feats = [c + "_p" for c in DRIVERS] + ["rice_p"]
    j = x[x.burn_p.notna()].copy()
    j[feats] = j[feats].fillna(0.5)
    X = np.column_stack([np.ones(len(j)), j[feats].to_numpy() - 0.5])
    yv = j.burn_p.to_numpy()

    def ols(df):
        Xd = np.column_stack([np.ones(len(df)), df[feats].to_numpy() - 0.5])
        return np.linalg.lstsq(Xd, df.burn_p.to_numpy(), rcond=None)[0][1:]
    beta = np.linalg.lstsq(X, yv, rcond=None)[0][1:]
    lo, hi = cluster_boot(j[["lgd_tehsil_code", "burn_p"] + feats], ols, rng)
    r2 = 1 - ((yv - X @ np.linalg.lstsq(X, yv, rcond=None)[0]) ** 2).sum() / ((yv - yv.mean()) ** 2).sum()

    rf = RandomForestRegressor(300, min_samples_leaf=20, n_jobs=-1, random_state=SEED)
    cv_pred = np.zeros(len(j))
    for tr, te in GroupKFold(5).split(j, groups=j.lgd_tehsil_code):
        rf.fit(j.iloc[tr][feats], yv[tr])
        cv_pred[te] = rf.predict(j.iloc[te][feats])
    cv_r2 = 1 - ((yv - cv_pred) ** 2).sum() / ((yv - yv.mean()) ** 2).sum()
    rf.fit(j[feats], yv)
    pi = permutation_importance(rf, j[feats], yv, n_repeats=5, random_state=SEED, n_jobs=-1)
    jm = pd.DataFrame({"feature": feats, "ols_beta": beta, "ols_ci_lo": lo, "ols_ci_hi": hi,
                       "rf_perm_importance": pi.importances_mean})
    jm.to_csv(OUT / "joint_model.csv", index=False, float_format="%.4g")
    print(f"\njoint OLS R2 (in-sample) {r2:.3f} | random forest out-of-tehsil CV R2 {cv_r2:.3f}")
    print(jm.round(3).to_string(index=False))

    # F. robustness: PDs whose harvest is not >= 10 days later than peers (V5 pass), since a late harvest could push
    # burning past the 30 Nov window and shorten the measured turnaround; within-tehsil reading as in D
    ok5 = set(st[st.label.isin(["validated PD", "PD with caveat"]) & (st.v5 == "pass")][ID])
    rob = []
    for c, (name, sign) in DRIVERS.items():
        if sign == 0 or c == "d7_basmati_share_district":
            continue
        w = x[x[ID].isin(ok5)][c + "_pt"].dropna()
        k = int(((w < 0.5) if sign > 0 else (w > 0.5)).sum())
        dev = (x[c] - x.groupby("peer")[c].transform("median"))[x[ID].isin(ok5)].median()
        rob.append({"driver": c, "n_pd_v5_pass": len(w), "within_tehsil_expected_side": round(k / len(w), 3),
                    "sign_p": binomtest(k, len(w), 0.5).pvalue, "median_diff_vs_peer_median": round(dev, 3)})
    rob = pd.DataFrame(rob)
    rob.to_csv(OUT / "robustness_v5_pass.csv", index=False, float_format="%.4g")
    print("\nF. PDs with normal harvest timing only (within tehsil):")
    print(rob.to_string(index=False))

    prof = x[x.is_pd | x.is_nd][[ID, "c2011_village_name", "lgd_tehsil_name", "peer", "is_pd", "mean"] +
                                [c + "_p" for c in DRIVERS]]
    prof.round(3).to_csv(OUT / "pd_profiles.csv", index=False)
    with open(OUT / "joint_model_r2.txt", "w") as f:
        f.write(f"ols_r2_in_sample {r2:.4f}\nrf_out_of_tehsil_cv_r2 {cv_r2:.4f}\nn {len(j)}\n")


if __name__ == "__main__":
    main()
