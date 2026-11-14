"""Sample size for the Phase 2 pilot (report §8.7).

Question: how many South-west villages must get a lever (and how many controls)
to detect a drop of 5 / 10 / 15 percentage points in village burnt share,
at 80% power and 5% two-sided significance?

Inputs (version_X, village level, 2020-24, ~10 Sentinel-2 points per village-season):
  version_X/outputs/burn/village_burn_measure.csv
  version_X/outputs/grouping/village_groups.csv
  version_X/outputs/pd/pd_validated.csv

Frame: villages in South-west tehsils, excluding Abohar (the tehsil PD, where the
levers come from) and excluding validated village PDs (already low burners).

Method:
  1. Pilot outcome Y = burnt share in a target season; baseline X = mean of the
     earlier seasons. Analysis = ANCOVA: Y ~ treatment + X + peer group.
     The noise that matters is the residual SD of Y after X and peer group.
  2. Villages per arm n = 2 (z_0.975 + z_0.80)^2 sigma^2 / delta^2.
     Pairing on baseline and rice share is not credited, so n is conservative.
  3. "As measured" sigma includes the sampling noise of ~10 points per village.
     A pilot would score all rice fields, so we also report sigma with that
     binomial noise removed ("full field") and for 30 / 100 points per village.
  4. Simulation check: random assignment on real data, add -delta to treated
     villages, refit ANCOVA, count rejections.

Run: python Code/impact/power_calc.py   (from repo root)
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
VX = ROOT / "version_X" / "outputs"
OUT = ROOT / "outputs" / "impact"
OUT.mkdir(parents=True, exist_ok=True)

MIN_LOOKS = 5             # season counted if >= 5 verdicts (version_X rule X8)
TARGETS = [2022, 2023, 2024]   # 2024 = doubtful season, sensitivity only
MAIN_TARGET = 2023
DELTAS = [0.05, 0.10, 0.15]
ALPHA, POWER = 0.05, 0.80
Z = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(POWER)
N_SIM, SEED = 1000, 7

log_lines = []


def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


def load_frame():
    code = {"c2011_village_code": str}
    burn = pd.read_csv(VX / "burn" / "village_burn_measure.csv", dtype=code)
    grp = pd.read_csv(VX / "grouping" / "village_groups.csv", dtype=code)
    pdv = pd.read_csv(VX / "pd" / "pd_validated.csv", dtype=code)

    pd_codes = set(pdv.loc[(pdv.flag_side == "PD")
                           & pdv.label.isin(["PD", "PD with caveat"]),
                           "c2011_village_code"])
    frame = grp[(grp.tehsil_region == "South-west")
                & (grp.lgd_tehsil_name != "Abohar")
                & ~grp.c2011_village_code.isin(pd_codes)]
    log(f"South-west villages: {(grp.tehsil_region == 'South-west').sum()}; "
        f"frame after dropping Abohar and village PDs: {len(frame)}")

    burn = burn[burn.n_look >= MIN_LOOKS]
    burn = burn.merge(frame[["c2011_village_code", "peer", "lgd_tehsil_name"]],
                      on="c2011_village_code")
    return burn


def season_table(burn, target):
    """One row per village: Y (target season), X (mean of earlier seasons)."""
    y = burn[burn.year == target][["c2011_village_code", "peer", "burnt_share", "n_look"]]
    x = (burn[burn.year < target].groupby("c2011_village_code")
         .agg(x=("burnt_share", "mean"), n_base=("year", "size")).reset_index())
    t = y.merge(x, on="c2011_village_code")
    t = t[t.n_base >= 2].rename(columns={"burnt_share": "y"})
    return t.reset_index(drop=True)


def design(t, with_x=True, treat=None):
    cols = [np.ones(len(t))]
    if treat is not None:
        cols.append(treat)
    if with_x:
        cols.append(t.x.to_numpy())
    dummies = pd.get_dummies(t.peer, drop_first=True).to_numpy(float)
    return np.column_stack(cols + [dummies])


def resid_var(t, with_x=True, y=None):
    y = t.y.to_numpy() if y is None else y
    X = design(t, with_x)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    return r @ r / (len(y) - X.shape[1])


N_PEER_PARAMS = 11   # intercept, treatment, baseline, 8 peer dummies (upper bound)


def n_per_arm(var, delta):
    """Normal formula, then iterate with t quantiles (df = 2n - parameters)."""
    n = int(np.ceil(2 * Z ** 2 * var / delta ** 2))
    for _ in range(50):
        df = max(2 * n - N_PEER_PARAMS, 2)
        zt = stats.t.ppf(1 - ALPHA / 2, df) + stats.t.ppf(POWER, df)
        n_new = int(np.ceil(2 * zt ** 2 * var / delta ** 2))
        if n_new == n:
            break
        n = n_new
    return n


def n_by_simulation(t, n0, delta, rng):
    """Smallest n (in ~5% steps from n0) whose simulated power reaches POWER."""
    n = n0
    while 2 * n <= len(t):
        pw = simulate(t, n, delta, rng)
        if pw >= POWER:
            return n, pw
        n = int(np.ceil(n * 1.05)) + 1
    return None, None


def simulate(t, n, delta, rng):
    hits = 0
    for _ in range(N_SIM):
        idx = rng.choice(len(t), 2 * n, replace=False)
        s = t.iloc[idx].reset_index(drop=True)
        treat = np.r_[np.ones(n), np.zeros(n)]
        y = s.y.to_numpy() - delta * treat
        X = design(s, True, treat)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ beta
        dof = len(y) - X.shape[1]
        s2 = r @ r / dof
        se = np.sqrt(s2 * np.linalg.pinv(X.T @ X)[1, 1])
        hits += abs(beta[1] / se) > stats.t.ppf(1 - ALPHA / 2, dof)
    return hits / N_SIM


def main():
    burn = load_frame()
    rng = np.random.default_rng(SEED)
    var_rows, power_rows = [], []

    for target in TARGETS:
        t = season_table(burn, target)
        v_raw = t.y.var(ddof=1)
        v_peer = resid_var(t, with_x=False)
        v_anc = resid_var(t, with_x=True)
        # binomial sampling noise of Y at ~10 points (unbiased p(1-p)/(n-1))
        p, m = t.y.to_numpy(), t.n_look.to_numpy()
        v_samp = np.mean(p * (1 - p) / np.maximum(m - 1, 1))
        v_ff = max(v_anc - v_samp, 1e-6)
        r_xy = np.corrcoef(t.x, t.y)[0, 1]
        var_rows.append(dict(target=target, villages=len(t), mean_y=t.y.mean(),
                             sd_raw=np.sqrt(v_raw), sd_peer=np.sqrt(v_peer),
                             sd_ancova=np.sqrt(v_anc), sd_sampling=np.sqrt(v_samp),
                             sd_full_field=np.sqrt(v_ff), corr_baseline=r_xy))

        # sigma for scenarios: as measured, m points per village, full field
        pbar = np.mean(p * (1 - p))
        scen = {"as measured (~10 pts)": v_anc,
                "30 pts per village": v_ff + pbar / 30,
                "100 pts per village": v_ff + pbar / 100,
                "full field": v_ff,
                "no baseline, as measured": v_peer}
        for name, v in scen.items():
            for d in DELTAS:
                power_rows.append(dict(target=target, scenario=name, delta=d,
                                       sd=np.sqrt(v), villages_per_arm=n_per_arm(v, d)))

        if target == MAIN_TARGET:
            log(f"\nSimulation check (target {target}, as measured, {N_SIM} draws):")
            for d in DELTAS:
                n = n_per_arm(v_anc, d)
                if 2 * n > len(t):
                    log(f"  delta {d:.2f}: n {n}/arm exceeds frame, skipped")
                    continue
                pw = simulate(t, n, d, rng)
                n_sim, pw_sim = n_by_simulation(t, n, d, rng)
                log(f"  delta {d:.2f}: formula n {n}/arm -> simulated power {pw:.2f}; "
                    f"simulation needs n {n_sim}/arm (power {pw_sim:.2f})")
                power_rows.append(dict(target=target, scenario="as measured, simulated",
                                       delta=d, sd=np.sqrt(v_anc), villages_per_arm=n_sim))

    var_df = pd.DataFrame(var_rows).round(4)
    pow_df = pd.DataFrame(power_rows).round(4)
    var_df.to_csv(OUT / "variance_components.csv", index=False)
    pow_df.to_csv(OUT / "power_table.csv", index=False)

    log("\nVariance components (SD of village burnt share):")
    log(var_df.to_string(index=False))
    log(f"\nVillages per arm (target {MAIN_TARGET}, 80% power, alpha 0.05):")
    log(pow_df[pow_df.target == MAIN_TARGET]
        .pivot(index="scenario", columns="delta", values="villages_per_arm")
        .to_string())
    (OUT / "run.log").write_text("\n".join(log_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
