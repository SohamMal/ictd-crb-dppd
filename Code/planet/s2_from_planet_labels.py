"""Prof. Aaditeshwar's suggestion (2026-10-26): train Sentinel-2 on Planet labels, test on ground truth.

Walker et al. (2022) ship field-mean PlanetScope AND Sentinel-2 series for the same 2019 fields
(same column IDs), aligned on the ground-known event day:
  TS_*        2,204 burnt fields          (day 0 = burn date)
  TSTilled_*    223 tilled, not burnt      (day 0 = till date)
Source: Code/Ground Truth Data/Walker/burntfields_punjab-v1.0.0.zip (Zenodo 11225292), read in place.

1. Planet label (ground truth NOT used): Jalandhar rule (planet_apply_jalandhar.py).
   brightness = (B+G+R+NIR)/4; ratio = min over 0..+5 d / median over -15..-1 d; burnt if <= 0.765.
2. Sentinel-2 features, one row per field:
   pre  = median of each clear look in -20..-1 d; post = FIRST clear look in 0..+10 d
   (what a 5-day revisit would see). Bands B2..B8, B11, B12 (Walker has no B8A) + NDVI, NBR,
   NBR2, BAIS2, TCB; post values and post - pre changes. Day of the look is NOT a feature.
3. 5-fold CV (seed 42): train on the training folds' Planet labels, predict the held-out fold,
   score against ground truth. Same folds for: S2 trained on ground truth (the best S2 can do),
   the old BAIS2+TCB detector (first post look, z > 0), and the Planet rule itself.

Run:  python Code/planet/s2_from_planet_labels.py
Out:  outputs/planet/s2fromplanet_fields.csv, s2fromplanet_results.csv, s2fromplanet_labels.csv
"""
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "burn_basma"))
sys.path.insert(0, str(ROOT / "Code" / "burn"))
from walker_tilled_test import bais2, tcb, lp  # noqa: E402

ZIP = ROOT / "Code" / "Ground Truth Data" / "Walker" / "burntfields_punjab-v1.0.0.zip"
TS = "klwalker-sb-burntfields_punjab-5c604ec/data/TSpoly_dataframes/"
OUT = ROOT / "outputs" / "planet"
S2 = {"blue": "B2", "green": "B3", "red": "B4", "redEdge1": "B5", "redEdge2": "B6", "redEdge3": "B7",
      "nir": "B8", "SWIR1": "B11", "SWIR2": "B12"}
PL = ["blue", "green", "red", "nir"]
CUT = 0.765          # Jalandhar rule cut-off (keeps 90% of Walker burnt fields, 0..2 d)
PL_POST = (0, 5)
S2_PRE, S2_POST = (-20, -1), (0, 10)
KEEP = [0.9, 0.8]


def read(z, name):
    d = pd.read_csv(io.BytesIO(z.read(TS + name)), index_col=0)
    d.index = d.index.astype(int)
    return d


def planet_labels(z, kind):
    stem = {"burnt": "TS_", "tilled": "TSTilled_"}[kind] + "polyData_PlanetV4_"
    b = {k: read(z, stem + k + ".csv") for k in PL}
    bright = sum(d.where(d > 0) for d in b.values()) / 4
    rows = []
    for fid in bright.columns:
        x = bright[fid].dropna()
        base = x[(x.index >= -15) & (x.index <= -1)]
        post = x[(x.index >= PL_POST[0]) & (x.index <= PL_POST[1])]
        r = post.min() / base.median() if len(base) and len(post) else np.nan
        rows.append({"field": fid, "kind": kind, "planet_ratio": r, "planet_base": base.median() if len(base) else np.nan})
    return pd.DataFrame(rows)


def s2_looks(z, kind):
    stem = {"burnt": "TS_", "tilled": "TSTilled_"}[kind] + "polyData_SentinelV4_"
    parts = [read(z, stem + band + ".csv").rename_axis("day").reset_index()
             .melt("day", var_name="field", value_name=s2).set_index(["day", "field"])
             for band, s2 in S2.items()]
    d = pd.concat(parts, axis=1).dropna().reset_index()
    d = d[(d[list(S2.values())] > 0).all(axis=1)]
    d[list(S2.values())] = d[list(S2.values())] / 10000
    d["NDVI"] = (d.B8 - d.B4) / (d.B8 + d.B4)
    d["NBR"] = (d.B8 - d.B12) / (d.B8 + d.B12)
    d["NBR2"] = (d.B11 - d.B12) / (d.B11 + d.B12)
    d["BAIS2"] = bais2(d.B4, d.B6, d.B7, d.B8, d.B12)
    d["TCB"] = tcb(d.B2, d.B3, d.B4, d.B8, d.B11, d.B12)
    return d.replace([np.inf, -np.inf], np.nan).dropna()


VARS = list(S2.values()) + ["NDVI", "NBR", "NBR2", "BAIS2", "TCB"]


def s2_features(d, pre_looks=None):
    """pre_looks = k: 'before' = median of only the last k clear looks in -20..-1 d (None = all)."""
    pre = d[(d.day >= S2_PRE[0]) & (d.day <= S2_PRE[1])].sort_values("day")
    if pre_looks:
        pre = pre.groupby("field").tail(pre_looks)
    pre = pre.groupby("field")[VARS].median()
    post = (d[(d.day >= S2_POST[0]) & (d.day <= S2_POST[1])].sort_values("day")
            .groupby("field").first())
    both = post.index.intersection(pre.index)
    post, pre = post.loc[both], pre.loc[both]
    f = post[VARS].add_prefix("post_").join((post[VARS] - pre[VARS]).add_prefix("d_"))
    f["post_day"] = post.day  # reported only, never a feature
    return f


def rates(y_true, called):
    t, c = np.asarray(y_true), np.asarray(called)
    return {"burns_caught": round(c[t == 1].mean(), 3), "tilled_called_burnt": round(c[t == 0].mean(), 3),
            "n_tilled_called_burnt": int(c[t == 0].sum())}


def wilson(k, n, zc=1.96):
    p = k / n
    den = 1 + zc ** 2 / n
    mid = (p + zc ** 2 / (2 * n)) / den
    half = zc * np.sqrt(p * (1 - p) / n + zc ** 2 / (4 * n ** 2)) / den
    return round(mid - half, 3), round(mid + half, 3)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(ZIP)
    pl = pd.concat([planet_labels(z, k) for k in ["burnt", "tilled"]], ignore_index=True)
    s2 = pd.concat([s2_looks(z, k).assign(kind=k) for k in ["burnt", "tilled"]], ignore_index=True)

    # sanity check that Planet and S2 column IDs are the same fields: pre-event brightness should correlate
    pre_s2 = (s2[(s2.day >= -15) & (s2.day <= -1)].assign(v=lambda x: (x.B2 + x.B3 + x.B4 + x.B8) / 4)
              .groupby(["kind", "field"]).v.median().rename("s2_base").reset_index())
    chk = pl.merge(pre_s2, on=["kind", "field"]).dropna()
    rho = chk.groupby("kind")[["planet_base", "s2_base"]].corr(method="spearman").xs("planet_base", level=1).s2_base
    print("ID check, Spearman(Planet pre, S2 pre) by class:", rho.round(2).to_dict(), "n", chk.groupby("kind").size().to_dict())

    feats = pd.concat([s2_features(s2[s2.kind == k]).assign(kind=k) for k in ["burnt", "tilled"]]).reset_index()
    f = feats.merge(pl, on=["kind", "field"], how="left")
    f["truth"] = (f.kind == "burnt").astype(int)
    f["planet_label"] = np.where(f.planet_ratio.isna(), np.nan, (f.planet_ratio <= CUT).astype(float))
    sc, m = lp.model()
    f["old_z"] = m.decision_function(sc.transform(f[["post_BAIS2", "post_TCB"]].to_numpy()))
    f.to_csv(OUT / "s2fromplanet_fields.csv", index=False)

    lab = pd.crosstab(f.kind, f.planet_label.map({1.0: "Planet: burnt", 0.0: "Planet: not burnt"}).fillna("no Planet look"))
    lab.to_csv(OUT / "s2fromplanet_labels.csv")
    print(f"\nfields with S2 pre + first post look: {f.groupby('kind').size().to_dict()}; "
          f"median day of first post look: {f.groupby('kind').post_day.median().to_dict()}")
    print("\nPlanet labels vs ground truth (label noise the S2 model is trained on):\n", lab.to_string())

    X = f[[c for c in f.columns if c.startswith(("post_", "d_")) and c != "post_day"]].to_numpy()
    y = f.truth.to_numpy()
    models = {
        "logistic": lambda: make_pipeline(StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=5000)),
        "random forest": lambda: RandomForestClassifier(500, min_samples_leaf=5, class_weight="balanced",
                                                        random_state=42, n_jobs=-1),
    }
    scores = {}
    for name, make in models.items():
        for train_on in ["Planet labels", "ground truth"]:
            s = np.full(len(f), np.nan)
            for tr, te in StratifiedKFold(5, shuffle=True, random_state=42).split(X, y):
                if train_on == "Planet labels":
                    tr = tr[~np.isnan(f.planet_label.to_numpy()[tr])]
                    ytr = f.planet_label.to_numpy()[tr].astype(int)
                else:
                    ytr = y[tr]
                s[te] = make().fit(X[tr], ytr).predict_proba(X[te])[:, 1]
            scores[f"S2 {name}, trained on {train_on}"] = (s, s >= 0.5)
    scores["S2 old BAIS2+TCB (first look)"] = (f.old_z.to_numpy(), f.old_z.to_numpy() > 0)
    has_pl = f.planet_ratio.notna().to_numpy()

    res = []
    for name, (s, called) in scores.items():
        for subset, ok in [("all fields", np.ones(len(f), bool)), ("fields with Planet look", has_pl)]:
            r = {"method": name, "fields": subset, "n_burnt": int(y[ok].sum()), "n_tilled": int((1 - y[ok]).sum()),
                 "AUC": round(roc_auc_score(y[ok], s[ok]), 3), **rates(y[ok], called[ok])}
            r["tilled_called_burnt_95CI"] = wilson(r["n_tilled_called_burnt"], r["n_tilled"])
            for k in KEEP:
                cut = np.quantile(s[ok][y[ok] == 1], 1 - k)
                r[f"tilled_called_burnt_at_{int(k * 100)}pct_burns"] = round((s[ok][y[ok] == 0] >= cut).mean(), 3)
            # cut-off without ground truth: keep 90% of the fields PLANET calls burnt (usable in any Planet-covered area)
            pb = s[(f.planet_label == 1).to_numpy()]
            cut = np.quantile(pb, 0.1)
            r.update({"planetcut_burns_caught": round((s[ok][y[ok] == 1] >= cut).mean(), 3),
                      "planetcut_tilled_called_burnt": round((s[ok][y[ok] == 0] >= cut).mean(), 3)})
            res.append(r)
    ok = has_pl
    s = -f.planet_ratio.to_numpy()
    r = {"method": "Planet rule itself (ratio <= 0.765)", "fields": "fields with Planet look",
         "n_burnt": int(y[ok].sum()), "n_tilled": int((1 - y[ok]).sum()), "AUC": round(roc_auc_score(y[ok], s[ok]), 3),
         **rates(y[ok], f.planet_label.to_numpy()[ok] == 1)}
    r["tilled_called_burnt_95CI"] = wilson(r["n_tilled_called_burnt"], r["n_tilled"])
    for k in KEEP:
        cut = np.quantile(s[ok][y[ok] == 1], 1 - k)
        r[f"tilled_called_burnt_at_{int(k * 100)}pct_burns"] = round((s[ok][y[ok] == 0] >= cut).mean(), 3)
    res.append(r)
    res = pd.DataFrame(res)
    res.to_csv(OUT / "s2fromplanet_results.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    print("\nHeld-out results vs ground truth (5-fold CV; called burnt = prob >= 0.5, or z > 0):")
    print(res.to_string(index=False))

    rf = models["random forest"]().fit(X[has_pl], f.planet_label.to_numpy()[has_pl].astype(int))
    cols = [c for c in f.columns if c.startswith(("post_", "d_")) and c != "post_day"]
    imp = pd.Series(rf.feature_importances_, cols).sort_values(ascending=False)
    print("\nTop random-forest features (trained on Planet labels):\n", imp.head(10).round(3).to_string())


if __name__ == "__main__":
    main()
