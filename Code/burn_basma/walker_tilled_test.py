"""
Branch B, test W1: does BAIS2+TCB call ploughed-not-burnt fields "burnt"? (2026-10-22)

The missing row of Basma's confusion table, on ground-known fields. Walker et al. (2022, J-PAL
Punjab PES study, 2019 season) published location-free Sentinel-2 L2A field means, one row per
day from the event (cloud-probability masked):
  TS_polyData_SentinelV4_<band>.csv        2,204 burnt fields,             day 0 = estimated burn date
  TSTilled_polyData_SentinelV4_<band>.csv    223 tilled-not-burnt fields,  day 0 = estimated till date
(day 0 = midpoint between the last monitor visit before and first visit after the event)
Source: Code/Ground Truth Data/Walker/burntfields_punjab-v1.0.0.zip (Zenodo 11225292), read in place.

The same pooled relaxed-mask model as branch A is applied to every clear look. Walker ships no
B8A, so BAIS2 uses B8; step 0 measures that substitution on the CEEW label-date fields (GEE).

Run:  python Code/burn_basma/walker_tilled_test.py [--skip-b8-check]
Out:  outputs/burn_basma/w1_*.csv (no locations in any file)
"""

import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "burn"))
import labelling_package as lp  # noqa: E402
from transfer_checks import MASKS, ROOT, SCALE, LABEL_DATES, fields, init_ee, label_image, to_df  # noqa: E402

OUT = ROOT / "outputs" / "burn_basma"
ZIP = ROOT / "Code" / "Ground Truth Data" / "Walker" / "burntfields_punjab-v1.0.0.zip"
TS = "klwalker-sb-burntfields_punjab-5c604ec/data/TSpoly_dataframes/"
BANDS = {"blue": "B2", "green": "B3", "red": "B4", "redEdge2": "B6", "redEdge3": "B7",
         "nir": "B8", "SWIR1": "B11", "SWIR2": "B12"}
WINDOWS = [(-50, -16), (-15, -1), (0, 10), (11, 30), (31, 60)]


def bais2(b4, b6, b7, nir, b12):
    p1 = np.sqrt(b6 * b7 * nir / b4)
    p2 = (b12 - nir) / np.sqrt(b12 + nir) + 1
    return (1 - p1) * p2


def tcb(b2, b3, b4, b8, b11, b12):
    return 0.3510 * b2 + 0.3813 * b3 + 0.3437 * b4 + 0.7196 * b8 + 0.2396 * b11 + 0.1949 * b12


# ---------------------------------------------------------------- step 0: B8 for B8A on CEEW
def b8_check(sc, m):
    import ee
    rows = []
    for year in LABEL_DATES:
        img = label_image(year)
        sr = img.select(["B2", "B3", "B4", "B6", "B7", "B8", "B8A", "B11", "B12"]).divide(10000)
        scl = img.select("SCL")
        valid = scl.eq(MASKS["relaxed_scl2457"][0])
        for c in MASKS["relaxed_scl2457"][1:]:
            valid = valid.Or(scl.eq(c))
        sr = sr.updateMask(valid)
        out = []
        for nir in ["B8A", "B8"]:
            p1 = sr.select("B6").multiply(sr.select("B7")).multiply(sr.select(nir)).divide(sr.select("B4")).sqrt()
            p2 = sr.select("B12").subtract(sr.select(nir)).divide(sr.select("B12").add(sr.select(nir)).sqrt()).add(1)
            out.append(ee.Image(1).subtract(p1).multiply(p2).rename(f"BAIS2_{nir}"))
        t = (sr.select("B2").multiply(0.3510).add(sr.select("B3").multiply(0.3813))
             .add(sr.select("B4").multiply(0.3437)).add(sr.select("B8").multiply(0.7196))
             .add(sr.select("B11").multiply(0.2396)).add(sr.select("B12").multiply(0.1949)).rename("TCB"))
        st = ee.Image.cat(out + [t]).reduceRegions(collection=fields(year), reducer=ee.Reducer.median(),
                                                   scale=SCALE, tileScale=4)
        rows.append(to_df(st))
    d = pd.concat(rows, ignore_index=True).dropna(subset=["BAIS2_B8A", "BAIS2_B8", "TCB"])
    for nir in ["B8A", "B8"]:
        d[f"pred_{nir}"] = m.predict(sc.transform(d[[f"BAIS2_{nir}", "TCB"]].to_numpy()))
    d.to_csv(OUT / "w1_b8_check_fields.csv", index=False)
    res = pd.DataFrame([{
        "n_fields": len(d),
        "median_BAIS2_shift_B8_minus_B8A": round((d.BAIS2_B8 - d.BAIS2_B8A).median(), 4),
        "predictions_unchanged": round((d.pred_B8 == d.pred_B8A).mean(), 4),
        "accuracy_B8A": round((d.pred_B8A == d.burnt).mean(), 4),
        "accuracy_B8": round((d.pred_B8 == d.burnt).mean(), 4)}])
    res.to_csv(OUT / "w1_b8_check.csv", index=False)
    print("\n[step 0] BAIS2 with B8 instead of B8A, CEEW label-date fields, same model")
    print(res.to_string(index=False))


# ---------------------------------------------------------------- Walker series
def load(kind):
    prefix = {"burnt": "TS_", "tilled": "TSTilled_"}[kind]
    with zipfile.ZipFile(ZIP) as z:
        parts = []
        for band, s2 in BANDS.items():
            with z.open(f"{TS}{prefix}polyData_SentinelV4_{band}.csv") as f:
                w = pd.read_csv(f, index_col=0).copy()
            parts.append(w.rename_axis("day").reset_index().melt("day", var_name="field", value_name=s2)
                         .set_index(["day", "field"]))
    d = pd.concat(parts, axis=1).dropna().reset_index()
    d[list(BANDS.values())] = d[list(BANDS.values())] / 10000
    d["day"] = d.day.astype(int)
    d["kind"] = kind
    return d


def score(d, sc, m):
    d["BAIS2"] = bais2(d.B4, d.B6, d.B7, d.B8, d.B12)
    d["TCB"] = tcb(d.B2, d.B3, d.B4, d.B8, d.B11, d.B12)
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=["BAIS2", "TCB"])
    z = sc.transform(d[["BAIS2", "TCB"]].to_numpy())
    d["z"] = m.decision_function(z)
    d["flag"] = (d.z > 0).astype(int)
    return d


def report(d):
    d["window"] = pd.cut(d.day, [a - 0.5 for a, _ in WINDOWS] + [WINDOWS[-1][1] + 0.5],
                         labels=[f"{a:+d}..{b:+d}" for a, b in WINDOWS])
    looks = d.groupby(["kind", "window"], observed=True).agg(
        looks=("flag", "size"), fields=("field", "nunique"), share_looks_flagged=("flag", "mean"),
        median_BAIS2=("BAIS2", "median"), median_TCB=("TCB", "median")).round(3)
    fld = (d.groupby(["kind", "window", "field"], observed=True).flag.max()
           .groupby(["kind", "window"], observed=True).agg(share_fields_flagged_any="mean").round(3))
    t = looks.join(fld)
    t.to_csv(OUT / "w1_by_window.csv")
    print("\n[W1] BAIS2+TCB flags by days from event (burnt: burn date; tilled: till date)")
    print(t.to_string())

    # Basma's table: a field counts as "called burnt" if any clear look in 0..+10 d is flagged
    post = d[(d.day >= 0) & (d.day <= 10)]
    f = post.groupby(["kind", "field"]).flag.max().reset_index()
    ct = pd.crosstab(f.kind, f.flag.map({1: "called burnt", 0: "called not burnt"}), margins=True)
    ct.to_csv(OUT / "w1_confusion_0_10d.csv")
    print("\n[W1] field-level table, any flag within 0..+10 d of the event")
    print(ct.to_string())

    # separability of the model score itself, as in the char-vs-soil AUC (0.51) of branch A
    aucs = []
    for a, b in [(0, 10), (0, 5), (6, 15), (11, 30)]:
        p = d[(d.day >= a) & (d.day <= b)]
        for var in ["z", "BAIS2", "TCB"]:
            y = (p.kind == "burnt").astype(int)
            aucs.append({"days": f"{a}..{b}", "score": var, "n_burnt": int(y.sum()), "n_tilled": int((1 - y).sum()),
                         "AUC_burnt_vs_tilled": round(roc_auc_score(y, p[var]), 3)})
    au = pd.DataFrame(aucs)
    au.to_csv(OUT / "w1_auc.csv", index=False)
    print("\n[W1] AUC, burnt looks vs tilled looks at the same days from event (0.5 = no separation)")
    print(au.pivot(index="days", columns="score", values="AUC_burnt_vs_tilled").to_string())

    # stricter cut-off: keep a fixed share of burnt fields, how many tilled fields still pass?
    # field score = max model score (z) or min brightness (-TCB) over its clear looks in the window
    sweep = []
    for a, b in [(0, 5), (0, 10)]:
        p = d[(d.day >= a) & (d.day <= b)].assign(negTCB=lambda x: -x.TCB)
        f = p.groupby(["kind", "field"])[["z", "negTCB"]].max().reset_index()
        for var in ["z", "negTCB"]:
            for keep in [0.95, 0.9, 0.8, 0.7]:
                t = f[f.kind == "burnt"][var].quantile(1 - keep)
                sweep.append({"days": f"{a}..{b}", "score": var, "burnt_fields_kept": keep,
                              "cutoff": round(t, 3), "tilled_fields_called_burnt": round((f[f.kind == "tilled"][var] >= t).mean(), 3),
                              "n_burnt": int((f.kind == "burnt").sum()), "n_tilled": int((f.kind == "tilled").sum())})
    sw = pd.DataFrame(sweep)
    sw.to_csv(OUT / "w1_cutoff_sweep.csv", index=False)
    print("\n[W1] stricter cut-off: share of tilled fields still called burnt when X% of burnt fields are kept")
    print(sw.to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-b8-check", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sc, m = lp.model()
    if not a.skip_b8_check:
        init_ee()
        b8_check(sc, m)
    d = pd.concat([score(load(k), sc, m) for k in ["burnt", "tilled"]], ignore_index=True)
    print(f"\nclear looks: {d.groupby('kind').size().to_dict()}, fields: {d.groupby('kind').field.nunique().to_dict()}")
    report(d)


if __name__ == "__main__":
    main()
