"""Can daily PlanetScope tell burnt from ploughed fields? Test on Walker et al. ground truth (Punjab 2019).

Input (read in place from the Walker zip, Zenodo 11225292): field-mean PlanetScope series aligned
on the event day (rows = days -50..+66, reflectance x 10,000):
  TS_polyData_PlanetV4_<band>.csv       2,205 burnt fields (day 0 = burn date)
  TSTilled_polyData_PlanetV4_<band>.csv   223 tilled, not burnt (day 0 = till date)
No locations are needed or used.

Per field
  base   = median over days -15..-1 (straw before the event)
  post   = minimum over days 0..+W (darkest look soon after the event)
  scores = post / base for visible mean (B+G+R)/3, NIR, and all-band brightness (B+G+R+NIR)/4;
           also the absolute post values. Lower = darker after the event = more burn-like.
Compared with the Sentinel-2 detector on the same ground truth (W1, outputs/burn_basma/w1_cutoff_sweep.csv):
share of tilled fields called burnt when the cut-off keeps 90 / 80 / 70% of burnt fields.

Out: outputs/planet/walker_planet_fields.csv, walker_planet_auc.csv, walker_planet_sweep.csv
"""
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

ROOT = Path(__file__).resolve().parents[2]
ZIP = ROOT / "Code" / "Ground Truth Data" / "Walker" / "burntfields_punjab-v1.0.0.zip"
PREFIX = "klwalker-sb-burntfields_punjab-5c604ec/data/TSpoly_dataframes/"
OUT = ROOT / "outputs" / "planet"
BANDS = ["blue", "green", "red", "nir"]
BASE = (-15, -1)
WINDOWS = [5, 10]
KEEP = [0.9, 0.8, 0.7]


def load(z, kind):
    stem = "TS_polyData_PlanetV4_" if kind == "burnt" else "TSTilled_polyData_PlanetV4_"
    bands = {}
    for b in BANDS:
        d = pd.read_csv(io.BytesIO(z.read(PREFIX + stem + b + ".csv")), index_col=0)
        d.index = d.index.astype(int)
        bands[b] = d.where(d > 0)  # 0 / negative = no data
    return bands


def features(bands, kind):
    vis = (bands["blue"] + bands["green"] + bands["red"]) / 3
    allb = (vis * 3 + bands["nir"]) / 4
    series = {"vis": vis, "nir": bands["nir"], "bright": allb}
    rows = []
    for fid in vis.columns:
        r = {"field": fid, "kind": kind}
        for name, s in series.items():
            x = s[fid].dropna()
            base = x[(x.index >= BASE[0]) & (x.index <= BASE[1])]
            r[f"{name}_base"] = base.median() if len(base) else np.nan
            for w in WINDOWS:
                post = x[(x.index >= 0) & (x.index <= w)]
                r[f"{name}_post{w}"] = post.min() if len(post) else np.nan
                r[f"{name}_ratio{w}"] = r[f"{name}_post{w}"] / r[f"{name}_base"]
                if name == "vis":
                    r[f"n_looks_0_{w}"] = len(post)
                    r[f"first_look_{w}"] = post.index.min() if len(post) else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(ZIP)
    f = pd.concat([features(load(z, k), k) for k in ["burnt", "tilled"]], ignore_index=True)
    f.to_csv(OUT / "walker_planet_fields.csv", index=False)
    y = (f.kind == "burnt").astype(int)

    auc, sweep = [], []
    for w in WINDOWS:
        ok = f[f"vis_ratio{w}"].notna() & f[f"nir_ratio{w}"].notna()
        g, yy = f[ok], y[ok]
        cols = {f"vis ratio": f"vis_ratio{w}", "nir ratio": f"nir_ratio{w}", "bright ratio": f"bright_ratio{w}",
                "vis post (absolute)": f"vis_post{w}", "bright post (absolute)": f"bright_post{w}"}
        # 2-feature logistic (visible + NIR ratios), 5-fold cross-validated scores
        X = g[[f"vis_ratio{w}", f"nir_ratio{w}"]].to_numpy()
        cv = StratifiedKFold(5, shuffle=True, random_state=42)
        lr = LogisticRegression(class_weight="balanced", max_iter=1000)
        scores = {name: -g[c].to_numpy() for name, c in cols.items()}  # lower value = burn-like
        scores["logistic vis+nir ratio (CV)"] = cross_val_predict(lr, X, yy, cv=cv, method="decision_function")
        for name, s in scores.items():
            auc.append({"days": f"0..{w}", "score": name, "auc": round(roc_auc_score(yy, s), 3),
                        "n_burnt": int(yy.sum()), "n_tilled": int((1 - yy).sum())})
            sb, st = s[yy.to_numpy() == 1], s[yy.to_numpy() == 0]
            for k in KEEP:
                cut = np.quantile(sb, 1 - k)
                sweep.append({"days": f"0..{w}", "score": name, "burnt_fields_kept": k,
                              "tilled_fields_called_burnt": round(float((st >= cut).mean()), 3),
                              "n_burnt": len(sb), "n_tilled": len(st)})
    auc, sweep = pd.DataFrame(auc), pd.DataFrame(sweep)
    auc.to_csv(OUT / "walker_planet_auc.csv", index=False)
    sweep.to_csv(OUT / "walker_planet_sweep.csv", index=False)
    pd.set_option("display.width", 200)
    print(f.groupby("kind")[["n_looks_0_5", "first_look_5", "vis_ratio5", "nir_ratio5", "vis_ratio10"]].median())
    print(auc.to_string(index=False))
    print(sweep.pivot_table(index=["days", "score"], columns="burnt_fields_kept",
                            values="tilled_fields_called_burnt").to_string())
    s2 = pd.read_csv(ROOT / "outputs" / "burn_basma" / "w1_cutoff_sweep.csv")
    print("\nSentinel-2 on the same ground truth (W1):")
    print(s2.pivot_table(index=["days", "score"], columns="burnt_fields_kept",
                         values="tilled_fields_called_burnt").to_string())


if __name__ == "__main__":
    main()
