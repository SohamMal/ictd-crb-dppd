"""Option (a), 2026-10-27: set the Walker model's cut-off without using either judge's labels.

Model and Jalandhar probabilities: jalandhar_walker_model_test.py --pre-looks 1 --candidate jump
(outputs/planet/jalandhar_walker_fields_{A,B}_pre1_jump.csv, column prob).
  1. Walker balance  : cut maximising (burns caught + tilled rejected) on Walker 5-fold out-of-fold
                       probabilities (Youden's J), ground truth 2019 only.
  2. Jalandhar Otsu  : valley of the UNLABELLED Jalandhar candidate probabilities (judge A and B windows
                       pooled), Otsu's method (split that makes the two groups most compact).
Plus a sweep over cut-offs 0.1..0.9 (reference only: reading it uses the judges' labels).

Run:  python Code/planet/jalandhar_cutoff.py
Out:  outputs/planet/jalandhar_cutoff_results.csv, jalandhar_cutoff_sweep.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "planet"))
import jalandhar_planet_retrain as rt  # noqa: E402

OUT = ROOT / "outputs" / "planet"


def walker_oof():
    X, y, _ = rt.walker_xy()
    oof = np.zeros(len(y))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=42).split(X, y):
        rf = rt.w.RandomForestClassifier(500, min_samples_leaf=5, class_weight="balanced",
                                         random_state=42, n_jobs=-1).fit(X[tr], y[tr])
        oof[te] = rf.predict_proba(X[te])[:, 1]
    return oof, y


def youden(p, y):
    cuts = np.round(np.arange(0.05, 0.96, 0.01), 2)
    j = [(p[y == 1] >= c).mean() + (p[y == 0] < c).mean() - 1 for c in cuts]
    return float(cuts[int(np.argmax(j))])


def otsu(p, bins=100):
    h, e = np.histogram(p, bins=bins, range=(0, 1))
    mid = (e[:-1] + e[1:]) / 2
    best, cut = -1, 0.5
    for i in range(1, bins):
        w0, w1 = h[:i].sum(), h[i:].sum()
        if not w0 or not w1:
            continue
        m0, m1 = (h[:i] * mid[:i]).sum() / w0, (h[i:] * mid[i:]).sum() / w1
        between = w0 * w1 * (m0 - m1) ** 2
        if between > best:
            best, cut = between, e[i]
    return float(round(cut, 2))


def rates(f, t, cut):
    called = f.prob.fillna(0) >= cut
    tt = f[t].astype(int)
    return (f"{int((called & (tt == 1)).sum())}/{int((tt == 1).sum())}",
            f"{int((called & (tt == 0)).sum())}/{int((tt == 0).sum())}")


def main():
    a = pd.read_csv(OUT / "jalandhar_walker_fields_A_pre1_jump.csv", parse_dates=["burn_day"])
    b = pd.read_csv(OUT / "jalandhar_walker_fields_B_pre1_jump.csv")
    oof, y = walker_oof()
    c_y = youden(oof, y)
    print(f"Walker OOF at Youden cut {c_y}: burns caught {(oof[y == 1] >= c_y).mean():.3f}, "
          f"tilled called burnt {(oof[y == 0] >= c_y).mean():.3f}")
    pool = np.concatenate([a.prob.dropna(), b.prob.dropna()])
    c_o = otsu(pool)
    hist = np.histogram(pool, bins=10, range=(0, 1))[0]
    print(f"Jalandhar unlabelled candidate probs (n {len(pool)}), counts per 0.1 bin: {hist.tolist()}; Otsu cut {c_o}")

    subsets = [("A Planet rule", "all 95", a, "planet_burnt"),
               ("A Planet rule", "darkest day != 13 Nov", a[a.burn_day != rt.j.EDGE], "planet_burnt"),
               ("B CEEW visit", "all", b, "ceew_burnt"),
               ("B CEEW visit", "completely burnt vs unburnt", b[b.field_category != "partially_burnt"], "ceew_burnt"),
               ("B CEEW visit", "partially burnt vs unburnt", b[b.field_category != "completely_burnt"], "ceew_burnt")]
    res = []
    for judge, sub, f, t in subsets:
        r = {"judge": judge, "subset": sub}
        for name, c in [("default 0.5", 0.5), (f"Walker balance {c_y}", c_y), (f"Jalandhar Otsu {c_o}", c_o)]:
            r[f"{name}: burns"], r[f"{name}: not-burnt called burnt"] = rates(f, t, c)
        old = f.old_called_burnt == 1
        tt = f[t].astype(int)
        r["old: burns"] = f"{int((old & (tt == 1)).sum())}/{int((tt == 1).sum())}"
        r["old: not-burnt called burnt"] = f"{int((old & (tt == 0)).sum())}/{int((tt == 0).sum())}"
        res.append(r)
    res = pd.DataFrame(res)
    res.to_csv(OUT / "jalandhar_cutoff_results.csv", index=False)
    sweep = []
    for c in np.round(np.arange(0.1, 0.91, 0.1), 1):
        for judge, sub, f, t in subsets[:1] + subsets[2:3]:
            bu, fa = rates(f, t, c)
            sweep.append({"cut": c, "judge": judge, "burns": bu, "not_burnt_called_burnt": fa})
    sweep = pd.DataFrame(sweep)
    sweep.to_csv(OUT / "jalandhar_cutoff_sweep.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.to_string(index=False))
    print("\nSweep (reference only, uses labels):")
    print(sweep.pivot(index="cut", columns="judge", values=["burns", "not_burnt_called_burnt"]).to_string())


if __name__ == "__main__":
    main()
