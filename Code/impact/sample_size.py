"""Sample size for the Phase 2 pilot (report §8.7), from the main tehsil burn measure.

Question: how many South-west villages per arm (lever vs control) are needed to
detect a drop of 5 / 10 / 15 percentage points in village burnt share,
at 80% power and 5% two-sided significance?

Data (main pipeline only):
  outputs/burn_tehsil_rf/point_verdicts.csv   9,700 fixed points (100 per tehsil),
                                              same fields every season 2019-24
  outputs/burn_tehsil_rf/tehsil_burn_measure.csv   tehsil -> peer group
  Data/LGD/village_bridge_punjab.csv          Census villages per tehsil (frame size)

Frame: South-west group minus Abohar (the PD the levers come from): 17 tehsils.

Method (cluster trial with a baseline, ANCOVA on cluster means):
  Field outcome y = burnt (0/1) in the pilot season T; baseline x = the same
  field's mean burnt over the earlier seasons. Split the variance of y, x and
  their covariance into a between-tehsil part B and a within-tehsil part W
  (one-way ANOVA estimator). The data have tehsils, not villages, so the
  between-VILLAGE part is set to k x B (k = 1, 2, 3); villages are smaller and
  usually more alike inside than tehsils, so k = 1 is the optimistic end.
  The total (B + W) stays fixed; W shrinks accordingly.
  The year-to-year correlation of the TRUE village level (pi_c) is also set by
  scenario (0.9 / 0.7 / 0.5). Tehsil levels track almost perfectly in 2019-23
  (estimate ~1.0 on 17 tehsils), but villages have more local shocks (a buyer
  appears or leaves, harvest timing), and 2024 shows 0.25 even for tehsils.
  The within-village field persistence is taken from the data.
  A village mean over m scored fields then has
      Var(Y) = B_yy + W_yy / m,  Var(X) = B_xx + W_xx / m,  Cov = B_xy + W_xy / m
  and the ANCOVA residual variance is Var(Y) - Cov^2 / Var(X).
  Villages per arm n = 2 (t_0.975 + t_0.80)^2 * var / delta^2, iterated on df.

Run from repo root:  python Code/impact/sample_size.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "impact"
OUT.mkdir(parents=True, exist_ok=True)

GROUP, EXCLUDE = "South-west", ["Abohar"]
TARGETS, MAIN_TARGET = [2022, 2023, 2024], 2023   # 2024 = doubtful season (§6)
DELTAS = [0.05, 0.10, 0.15]
M_POINTS = [10, 30, 100, 300]
K_FACTORS = [1, 2, 3]
PI_C = [0.9, 0.7, 0.5]
ALPHA, POWER, N_PARAMS = 0.05, 0.80, 3          # intercept, treatment, baseline

lines = []


def log(s=""):
    print(s)
    lines.append(str(s))


def components(df, a, b):
    """Between- and within-tehsil (co)variance of columns a, b (ANOVA estimator)."""
    g = df.groupby("tehsil")
    n_t = g.size()
    k = len(n_t)
    N = n_t.sum()
    ma, mb = g[a].mean(), g[b].mean()
    da = df[a] - df.tehsil.map(ma)
    db = df[b] - df.tehsil.map(mb)
    W = (da * db).sum() / (N - k)
    MSB = (n_t * (ma - df[a].mean()) * (mb - df[b].mean())).sum() / (k - 1)
    n0 = (N - (n_t ** 2).sum() / N) / (k - 1)
    B = (MSB - W) / n0
    return B, W


def n_per_arm(var, delta):
    z = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(POWER)
    n = int(np.ceil(2 * z ** 2 * var / delta ** 2))
    for _ in range(50):
        df = max(2 * n - N_PARAMS, 2)
        zt = stats.t.ppf(1 - ALPHA / 2, df) + stats.t.ppf(POWER, df)
        n_new = int(np.ceil(2 * zt ** 2 * var / delta ** 2))
        if n_new == n:
            break
        n = n_new
    return n


def main():
    tm = pd.read_csv(ROOT / "outputs/burn_tehsil_rf/tehsil_burn_measure.csv")
    frame = tm[(tm.group == GROUP) & ~tm.lgd_tehsil_name.isin(EXCLUDE)]
    codes = set(frame.lgd_tehsil_code)
    names = sorted(frame.lgd_tehsil_name.unique())
    log(f"Frame: {len(names)} {GROUP} tehsils (excluding {', '.join(EXCLUDE)})")

    br = pd.read_csv(ROOT / "Data/LGD/village_bridge_punjab.csv")
    n_vill = br[br.lgd_tehsil_code.isin(codes)].lgd_village_code.nunique()
    log(f"Census villages in these tehsils: {n_vill}")

    pts = pd.read_csv(ROOT / "outputs/burn_tehsil_rf/point_verdicts.csv")
    pts["tehsil"] = pts["loc"].str.extract(r"^T(\d+)_")[0].astype(int)
    pts = pts[pts.tehsil.isin(codes)]
    wide = pts.pivot_table(index=["loc", "tehsil"], columns="year", values="burnt").reset_index()

    comp_rows, size_rows = [], []
    for T in TARGETS:
        base_years = [y for y in wide.columns if isinstance(y, (int, np.integer)) and y < T]
        d = wide[["loc", "tehsil", T]].rename(columns={T: "y"}).copy()
        d["x"] = wide[base_years].mean(axis=1)
        d["n_base"] = wide[base_years].notna().sum(axis=1)
        d = d[d.y.notna() & (d.n_base >= 2)]

        Byy, Wyy = components(d, "y", "y")
        Bxx, Wxx = components(d, "x", "x")
        Bxy, Wxy = components(d, "x", "y")
        tot = dict(yy=Byy + Wyy, xx=Bxx + Wxx, xy=Bxy + Wxy)
        comp_rows.append(dict(
            target=T, baseline=f"{min(base_years)}-{max(base_years)}", fields=len(d),
            mean_y=d.y.mean(), icc_tehsil=Byy / tot["yy"],
            between_sd=np.sqrt(max(Byy, 0)),
            tehsil_corr_true=Bxy / np.sqrt(Bxx * Byy) if Bxx > 0 and Byy > 0 else np.nan,
            field_persistence=Wxy / np.sqrt(Wxx * Wyy)))

        rho_w = Wxy / np.sqrt(Wxx * Wyy)          # field persistence within tehsil
        for k, pc in [(k, pc) for k in K_FACTORS for pc in PI_C]:
            bv = dict(yy=k * Byy, xx=k * Bxx)
            if bv["yy"] >= tot["yy"] or bv["xx"] >= tot["xx"]:
                continue
            bv["xy"] = pc * np.sqrt(bv["xx"] * bv["yy"])
            wv = dict(yy=tot["yy"] - bv["yy"], xx=tot["xx"] - bv["xx"])
            wv["xy"] = rho_w * np.sqrt(wv["xx"] * wv["yy"])
            for m in M_POINTS:
                vy = bv["yy"] + wv["yy"] / m
                vx = bv["xx"] + wv["xx"] / m
                cxy = bv["xy"] + wv["xy"] / m
                v_anc = vy - cxy ** 2 / vx
                for d_ in DELTAS:
                    size_rows.append(dict(
                        target=T, k=k, pi_c=pc, icc_village=bv["yy"] / tot["yy"], points=m,
                        delta=d_, r_baseline=cxy / np.sqrt(vx * vy),
                        n_no_baseline=n_per_arm(vy, d_), n_ancova=n_per_arm(v_anc, d_)))

    comp = pd.DataFrame(comp_rows).round(4)
    size = pd.DataFrame(size_rows).round(4)
    comp.to_csv(OUT / "variance_components.csv", index=False)
    size.to_csv(OUT / "sample_size_table.csv", index=False)

    log("\nVariance components (field level, frame tehsils):")
    log(comp.to_string(index=False))
    for T in TARGETS:
        s = size[(size.target == T) & (size.delta == 0.10) & (size.points == 30)]
        log(f"\n{T}: villages per arm, 10-pt drop, 30 points (rows pi_c, cols k)")
        log(s.pivot(index="pi_c", columns="k", values="n_ancova").to_string())
    s = size[(size.target == MAIN_TARGET) & (size.delta == 0.10) & (size.k == 2)]
    log(f"\n{MAIN_TARGET}: k = 2, 10-pt drop, by points (rows pi_c)")
    log(s.pivot(index="pi_c", columns="points", values="n_ancova").to_string())
    log("no baseline:")
    log(s.pivot(index="pi_c", columns="points", values="n_no_baseline").to_string())
    s = size[(size.target == MAIN_TARGET) & (size.points == 30) & (size.k == 2)]
    log(f"\n{MAIN_TARGET}: k = 2, 30 points, by delta (rows pi_c)")
    log(s.pivot(index="pi_c", columns="delta", values="n_ancova").to_string())
    (OUT / "run.log").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
