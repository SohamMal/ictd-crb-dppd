"""Option (b), 2026-10-27: retrain the Sentinel-2 model on Walker ground truth + Jalandhar Planet labels.

Same pipeline as jalandhar_walker_model_test.py with the adopted setting (candidate = flagged look with
the largest rise in z; "before" = the last clear look). Jalandhar training rows = the 95 CEEW-unburnt
fields that have a candidate in 29 Oct .. 13 Nov, labelled by the automatic Planet rule (no manual labels).

Fair test: 5 folds over Jalandhar field IDs (seed 42). For each fold, train on all Walker fields + the
Jalandhar Planet-labelled fields outside the fold; predict both judges' fields inside the fold.
Jalandhar rows weighted 1 (as Walker fields) or 10 (so ~70 local fields count against ~2,200 Walker ones).
Judges as before: A = Planet rule (95 fields), B = CEEW visit 29 Oct (357 fields). Judge B also uses
fields that trained the model in other folds only through judge A's later window (different dates).

Run:  python Code/planet/jalandhar_planet_retrain.py
Out:  outputs/planet/jalandhar_retrain_fields_{A,B}.csv, jalandhar_retrain_results.csv
"""
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "planet"))
import jalandhar_walker_model_test as j  # noqa: E402
w = j.w

j.PRE_LOOKS, j.CANDIDATE = 1, "jump"
OUT = ROOT / "outputs" / "planet"
WEIGHTS = [1, 10]


def candidate_rows(d, ids, win):
    """Feature row of the jump candidate per field (None if never flagged); same rule as j.score_fields."""
    rows, feats = [], []
    for fid in ids:
        g = d[d.field_id == fid]
        inwin = g[(g.date >= win[0]) & (g.date <= win[1])]
        flagged = inwin[inwin.z > 0]
        r = {"field_id": fid, "old_called_burnt": int(len(flagged) > 0)}
        x = None
        if len(flagged):
            rise = g.z.diff().reindex(flagged.index)
            c = flagged.loc[rise.fillna(-np.inf).idxmax()]
            pre = j.before(g, c.date)
            r.update({"candidate_date": c.date, "candidate_z": round(c.z, 2)})
            if len(pre):
                x = pd.concat([c[w.VARS].astype(float).add_prefix("post_"),
                               (c[w.VARS].astype(float) - pre[w.VARS].median()).add_prefix("d_")])
        rows.append(r)
        feats.append(x)
    return pd.DataFrame(rows), feats


def walker_xy():
    z = zipfile.ZipFile(w.ZIP)
    s2 = pd.concat([w.s2_looks(z, k).assign(kind=k) for k in ["burnt", "tilled"]], ignore_index=True)
    f = pd.concat([w.s2_features(s2[s2.kind == k], 1).assign(kind=k) for k in ["burnt", "tilled"]])
    cols = [c for c in f.columns if c.startswith(("post_", "d_")) and c != "post_day"]
    return f[cols].to_numpy(), (f.kind == "burnt").astype(int).to_numpy(), cols


def main():
    d = j.looks("scl")
    Xw, yw, cols = walker_xy()
    pr = pd.read_csv(OUT / "jalandhar_planet_rule_fields.csv", parse_dates=["burn_day"])
    a, fa = candidate_rows(d, pr.field_id, j.WIN_A)
    a = a.merge(pr[["field_id", "min_ratio", "burn_day", "planet_burnt"]], on="field_id")
    cat = d.drop_duplicates("field_id").set_index("field_id").field_category
    b, fb = candidate_rows(d, cat.index, j.WIN_B)
    b["field_category"] = b.field_id.map(cat)
    b["ceew_burnt"] = (b.field_category != "unburnt").astype(int)

    has_a = np.array([x is not None for x in fa])
    XA = np.array([x[cols].to_numpy() if x is not None else np.full(len(cols), np.nan) for x in fa])
    XB = np.array([x[cols].to_numpy() if x is not None else np.full(len(cols), np.nan) for x in fb])
    has_b = ~np.isnan(XB).any(axis=1)
    yA = a.planet_burnt.to_numpy()
    print(f"Jalandhar training rows (Planet-labelled, with a candidate): {has_a.sum()} "
          f"(burnt {int(yA[has_a].sum())}, not {int((1 - yA[has_a]).sum())})")

    all_ids = np.array(sorted(cat.index))
    folds = {fid: k for k, (_, te) in enumerate(KFold(5, shuffle=True, random_state=42).split(all_ids))
             for fid in all_ids[te]}
    fold_a, fold_b = a.field_id.map(folds).to_numpy(), b.field_id.map(folds).to_numpy()

    for wt in [0] + WEIGHTS:  # 0 = Walker only (reference, same folds)
        pa, pb = np.full(len(a), np.nan), np.full(len(b), np.nan)
        for k in range(5):
            tr = has_a & (fold_a != k)
            X = np.vstack([Xw, XA[tr]]) if wt else Xw
            y = np.concatenate([yw, yA[tr]]) if wt else yw
            sw = np.concatenate([np.ones(len(yw)), np.full(tr.sum(), wt)]) if wt else None
            rf = w.RandomForestClassifier(500, min_samples_leaf=5, class_weight="balanced",
                                          random_state=42, n_jobs=-1).fit(X, y, sample_weight=sw)
            ia, ib = has_a & (fold_a == k), has_b & (fold_b == k)
            if ia.any():
                pa[ia] = rf.predict_proba(XA[ia])[:, 1]
            if ib.any():
                pb[ib] = rf.predict_proba(XB[ib])[:, 1]
        a[f"prob_w{wt}"], b[f"prob_w{wt}"] = pa, pb

    a.to_csv(OUT / "jalandhar_retrain_fields_A.csv", index=False)
    b.to_csv(OUT / "jalandhar_retrain_fields_B.csv", index=False)
    res = []
    for judge, f, t, subsets in [
        ("A Planet rule", a, "planet_burnt", {"all 95": a.index == a.index, "darkest day != 13 Nov": a.burn_day != j.EDGE}),
        ("B CEEW visit", b, "ceew_burnt", {"all": b.index == b.index,
                                           "completely burnt vs unburnt": b.field_category != "partially_burnt",
                                           "partially burnt vs unburnt": b.field_category != "completely_burnt"}),
    ]:
        for sub, ok in subsets.items():
            g = f[np.asarray(ok)]
            tt = g[t].astype(int)
            methods = [("old BAIS2+TCB", g.old_called_burnt == 1, g.candidate_z.fillna(-99))] + [
                ("Walker only" if wt == 0 else f"Walker + Jalandhar Planet, weight {wt}",
                 g[f"prob_w{wt}"].fillna(0) >= 0.5, g[f"prob_w{wt}"].fillna(0))
                for wt in [0] + WEIGHTS]
            for name, called, score in methods:
                res.append({"judge": judge, "subset": sub, "method": name,
                            "burns_caught": f"{int((called & (tt == 1)).sum())}/{int((tt == 1).sum())}",
                            "not_burnt_called_burnt": f"{int((called & (tt == 0)).sum())}/{int((tt == 0).sum())}",
                            "AUC": round(roc_auc_score(tt, score), 3)})
    res = pd.DataFrame(res)
    res.to_csv(OUT / "jalandhar_retrain_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
