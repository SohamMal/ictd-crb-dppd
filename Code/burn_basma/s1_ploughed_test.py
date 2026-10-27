"""
Branch B, test B5: Basma's radar filter on single fields that were probably ploughed, not burnt (2026-10-22)

Walker's ground-known tilled fields (W1) carry no location, so no radar can be fetched for them.
Here a located "ploughed, not burnt" set is built from the CEEW 2021 Jalandhar fields:
  start   field labelled "unburnt" (harvested, stubble standing) on the ground on 2021-10-29
  event   residue disappears: first clear S2 look after the label date with NBR2 (= tillage index
          NDTI, (B11-B12)/(B11+B12)) below T, previous look above T. T = cut-off that best separates
          stubble from burnt fields on the label date. 2021 has a clear look every 5 days, so the
          event lies inside a <= 5 d bracket (previous look p, event look e).
  class   probable ploughed  TCB at e brighter than 90% of fresh burns (Walker burnt fields, 0..5 d)
                             and no VIIRS fire pixel over the field in [p, e]
          probable burnt     TCB at e darker than 90% of ploughed fields (Walker tilled, 0..5 d)
                             or a VIIRS fire pixel in [p, e]
          unclear            in between
Truth for the burnt side: CEEW fields labelled burnt on the ground (event look = the label date look,
previous look = the one before it).
Labels for the ploughed side are inferred from optical data (not seen on the ground) -> weaker truth.
Radar never enters the labelling, so the radar test below is independent of how fields were picked.

Radar (Basma's rule, as in B2): per field and relative orbit, dVV / dVH / d(VH-VV) between
  operational  last S1 image <= e and first S1 image > e   (what a deployed filter would do)
  bracket      last S1 image <= p and first S1 image > e   (pair surely spans the event)
averaged over orbits. Reused: outputs/burn_checks/charsoil_timeseries.csv (S2 field medians),
outputs/burn_basma/s1_field_series.csv (S1 field means, fields shrunk 10 m).

Run:  python Code/burn_basma/s1_ploughed_test.py
Out:  outputs/burn_basma/b5_*.csv
"""

import sys
from pathlib import Path

import ee
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "burn"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import labelling_package as lp  # noqa: E402
import walker_tilled_test as wt  # noqa: E402
from transfer_checks import BURNT, ROOT, fields, init_ee, to_df  # noqa: E402

OUT = ROOT / "outputs" / "burn_basma"
YEAR, LABEL = 2021, pd.Timestamp("2021-10-29")
THRESHOLDS = [1.5, 3.0]
MAX_PAIR = 12   # first S1 image after the event must be within 12 d


def s2_series():
    t = pd.read_csv(ROOT / "outputs" / "burn_checks" / "charsoil_timeseries.csv", parse_dates=["date"])
    t = t[t.year == YEAR].dropna(subset=["NBR2", "TCB"])
    t = t.groupby(["field_id", "field_category", "date"], as_index=False)[["NBR2", "TCB", "NDVI"]].mean()
    t["day"] = (t.date - LABEL).dt.days
    return t.sort_values(["field_id", "day"])


def thresholds(t):
    lab = t[(t.day == 0) & (t.field_category.isin(BURNT | {"unburnt"}))]
    y = (lab.field_category == "unburnt").astype(int)
    fpr, tpr, cut = roc_curve(y, lab.NBR2)
    T = float(cut[np.argmax(tpr - fpr)])
    sc, m = lp.model()
    w = pd.concat([wt.score(wt.load(k), sc, m) for k in ["burnt", "tilled"]], ignore_index=True)
    early = w[(w.day >= 0) & (w.day <= 5)]
    tcb_bright = float(early[early.kind == "burnt"].TCB.quantile(0.9))   # brighter than 90% of fresh burns
    tcb_dark = float(early[early.kind == "tilled"].TCB.quantile(0.1))    # darker than 90% of fresh ploughing
    th = {"NBR2_T": round(T, 4), "AUC_NBR2_stubble_vs_burnt": round(roc_auc_score(y, lab.NBR2), 3),
          "TCB_bright": round(tcb_bright, 4), "TCB_dark": round(tcb_dark, 4)}
    pd.DataFrame([th]).to_csv(OUT / "b5_thresholds.csv", index=False)
    print("[B5] thresholds", th)
    return th


def events(t, th):
    rows = []
    for (fid, cat), g in t.groupby(["field_id", "field_category"]):
        g = g.reset_index(drop=True)
        if cat in BURNT:
            e = g[g.day == 0]
            if e.empty or e.index[0] == 0:
                continue
            i = e.index[0]
            rows.append({"field_id": fid, "truth": "burnt (ground)", "p_day": g.day[i - 1], "e_day": 0,
                         "TCB_e": g.TCB[i], "NBR2_e": g.NBR2[i]})
        elif cat == "unburnt":
            after = g[g.day >= 0]
            hit = None
            for i in after.index[1:]:
                if g.NBR2[i] < th["NBR2_T"] <= g.NBR2[i - 1]:
                    hit = i
                    break
            if hit is None:
                rows.append({"field_id": fid, "truth": "residue stays", "p_day": np.nan, "e_day": np.nan})
                continue
            rows.append({"field_id": fid, "truth": "stubble field, residue removed", "p_day": g.day[hit - 1],
                         "e_day": g.day[hit], "TCB_e": g.TCB[hit], "NBR2_e": g.NBR2[hit]})
    return pd.DataFrame(rows)


def viirs(ev):
    """Any VIIRS active-fire pixel (FireMask >= 7, 1 km) over the field between p and e."""
    s = ev.dropna(subset=["e_day"])
    s = s[s.truth != "burnt (ground)"]
    win = {str(int(r.field_id)): [str((LABEL + pd.Timedelta(days=r.p_day)).date()),
                                  str((LABEL + pd.Timedelta(days=r.e_day + 1)).date())] for r in s.itertuples()}
    vi = ee.ImageCollection("NASA/VIIRS/002/VNP14A1").select("FireMask")

    def one(f):
        w = ee.List(ee.Dictionary(win).get(ee.Number(f.get("field_id")).format("%d")))
        days = vi.filterDate(w.get(0), w.get(1))
        fire = ee.Image(ee.Algorithms.If(days.size().gt(0), days.map(lambda i: i.gte(7)).max(), ee.Image(0))).unmask(0)
        return f.set("viirs_fire", fire.rename("v").reduceRegion(ee.Reducer.max(), f.geometry().centroid(1), 1000).get("v"))
    fc = fields(YEAR).filter(ee.Filter.inList("field_id", s.field_id.tolist()))
    d = to_df(fc.map(one)).reindex(columns=["field_id", "viirs_fire"])
    return ev.merge(d, on="field_id", how="left")


def classify(ev, th):
    def c(r):
        if r.truth != "stubble field, residue removed":
            return r.truth
        if r.viirs_fire == 1 or r.TCB_e <= th["TCB_dark"]:
            return "probable burnt (later)"
        if r.TCB_e >= th["TCB_bright"]:
            return "probable ploughed"
        return "unclear"
    ev["cls"] = ev.apply(c, axis=1)
    return ev


def radar(ev):
    s1 = pd.read_csv(OUT / "s1_field_series.csv")
    s1 = s1[s1.year == YEAR].drop_duplicates(["field_id", "orbit", "date"])
    rows = []
    for r in ev.dropna(subset=["e_day"]).itertuples():
        g = s1[s1.field_id == r.field_id]
        for orb, h in g.groupby("orbit"):
            h = h.sort_values("day")
            aft = h[(h.day > r.e_day) & (h.day <= r.e_day + MAX_PAIR)]
            if aft.empty:
                continue
            a = aft.iloc[0]
            for mode, cut in [("operational", r.e_day), ("bracket", r.p_day)]:
                bef = h[h.day <= cut]
                if bef.empty:
                    continue
                b = bef.iloc[-1]
                rows.append({"field_id": r.field_id, "cls": r.cls, "mode": mode, "orbit": orb,
                             "dVV": a.VV - b.VV, "dVH": a.VH - b.VH, "dVHVV": a.VH_VV - b.VH_VV, "gap_d": a.day - b.day})
    pr = pd.DataFrame(rows)
    pr.to_csv(OUT / "b5_pairs.csv", index=False)
    return pr.groupby(["field_id", "cls", "mode"], as_index=False)[["dVV", "dVH", "dVHVV", "gap_d"]].mean()


def report(ev, f):
    print("\n[B5] fields by class")
    print(ev.cls.value_counts().to_string())
    ev.to_csv(OUT / "b5_field_classes.csv", index=False)
    rows, aucs = [], []
    for mode, g in f.groupby("mode"):
        for cls, h in g.groupby("cls"):
            r = {"mode": mode, "class": cls, "n_fields": len(h), "median_gap_d": h.gap_d.median()}
            for v in ["dVV", "dVH", "dVHVV"]:
                r[f"median_{v}"] = round(h[v].median(), 2)
            for t in THRESHOLDS:
                r[f"called_ploughing_dVV>{t}"] = round((h.dVV > t).mean(), 3)
                r[f"called_ploughing_dVH>{t}"] = round((h.dVH > t).mean(), 3)
            rows.append(r)
        pb = g[g.cls.isin(["probable ploughed", "burnt (ground)"])]
        if pb.cls.nunique() == 2:
            y = (pb.cls == "probable ploughed").astype(int)
            for v in ["dVV", "dVH", "dVHVV"]:
                aucs.append({"mode": mode, "change": v, "n_ploughed": int(y.sum()), "n_burnt": int((1 - y).sum()),
                             "AUC_ploughed_higher": round(roc_auc_score(y, pb[v]), 3)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "b5_by_class.csv", index=False)
    print("\n[B5] radar change across the event, per field (mean over orbits)")
    print(t.to_string(index=False))
    a = pd.DataFrame(aucs)
    a.to_csv(OUT / "b5_auc.csv", index=False)
    print("\n[B5] AUC probable-ploughed vs ground-burnt (1 = radar rises more on ploughed fields, 0.5 = no difference)")
    print(a.to_string(index=False))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    init_ee()
    t = s2_series()
    th = thresholds(t)
    ev = classify(viirs(events(t, th)), th)
    report(ev, radar(ev))


if __name__ == "__main__":
    main()
