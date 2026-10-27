"""Jalandhar 2021 test of a Sentinel-2 model trained on Walker ground truth (2026-10-27).

Pipeline, as it would run anywhere (no event day given):
  flag first   old BAIS2+TCB detector (lp.model(), z > 0) -> first flagged clear look = candidate event
  then check   random forest trained on ALL Walker fields (ground truth, 2019) on the candidate look
               vs the median of clear looks in the 20 days before it (features as s2_from_planet_labels.py)
Cut-offs: 0.5, and the cut that keeps 90% of Walker burnt fields in 5-fold CV (set on Walker only).

Judges (no manual labels used):
  A  Planet rule (outputs/planet/jalandhar_planet_rule_fields.csv): 95 CEEW-unburnt fields,
     29 Oct .. 13 Nov 2021, burnt if Planet brightness ratio <= 0.765. S2 window = same dates.
  B  CEEW field visit 29 Oct 2021: 262 burnt (partial / complete) + 95 unburnt; S2 window 1 .. 29 Oct.

S2: COPERNICUS/S2_SR_HARMONIZED, 10 Sep .. 20 Nov 2021, CLOUDY_PIXEL_PERCENTAGE < 60, relaxed SCL
{2,4,5,7}, field MEAN of B2..B8, B11, B12 (as Walker), clear share >= 0.8; one tile per field and date
(highest clear share). Cached in outputs/planet/jalandhar_s2_fieldmeans_2021.csv.

--mask cloudprob (step 0, 2026-10-27): Walker-style clouds instead of SCL. COPERNICUS/S2_CLOUD_PROBABILITY
joined by image id, pixel dropped if probability >= 50 (Walker's 'GEECloudProb' option); no SCL classes.
Cached in outputs/planet/jalandhar_s2_fieldmeans_2021_cloudprob.csv; outputs get a _cloudprob suffix.

--pre-looks k (option c, 2026-10-27): 'before' = median of only the last k clear looks in the 20 d before
(Walker training and Jalandhar alike), so it is stubble rather than standing crop. Outputs get _prek.

--candidate jump (2026-10-27): candidate = flagged look (z > 0) with the largest rise in z over the previous
clear look, instead of the first flagged look (a weak first flag is often crop drying). Outputs get _jump.

Run:  python Code/planet/jalandhar_walker_model_test.py [--extract] [--mask scl|cloudprob] [--pre-looks k]
      [--candidate first|jump]
Out:  outputs/planet/jalandhar_walker_fields_A.csv, _fields_B.csv, _results.csv
"""
import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "planet"))
import s2_from_planet_labels as w  # noqa: E402  (also puts Code/burn, Code/burn_basma on the path)

OUT = ROOT / "outputs" / "planet"
CACHE = {"scl": OUT / "jalandhar_s2_fieldmeans_2021.csv",
         "cloudprob": OUT / "jalandhar_s2_fieldmeans_2021_cloudprob.csv"}
SUFFIX = {"scl": "", "cloudprob": "_cloudprob"}
CLOUDPROB_MAX = 50
BANDS = list(w.S2.values())  # B2 B3 B4 B5 B6 B7 B8 B11 B12
CLEAR = 0.8
PRE_DAYS = 20
PRE_LOOKS = None  # set from --pre-looks
CANDIDATE = "first"  # set from --candidate
WIN_A = (pd.Timestamp("2021-10-29"), pd.Timestamp("2021-11-13"))
WIN_B = (pd.Timestamp("2021-10-01"), pd.Timestamp("2021-10-29"))
EDGE = pd.Timestamp("2021-11-13")


def extract(mask):
    import ee
    from transfer_checks import fields, init_ee, to_df
    init_ee()
    fc = fields(2021)
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
           .filterDate("2021-09-10", "2021-11-21").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))
    ids = col.aggregate_array("system:index").getInfo()
    print(f"{len(ids)} images", flush=True)
    red = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
    recs = []
    for k, iid in enumerate(ids, 1):
        img = ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + iid)
        if mask == "scl":
            scl = img.select("SCL")
            valid = scl.eq(2).Or(scl.eq(4)).Or(scl.eq(5)).Or(scl.eq(7))
        else:
            valid = ee.Image("COPERNICUS/S2_CLOUD_PROBABILITY/" + iid).select("probability").lt(CLOUDPROB_MAX)
        sr = img.select(BANDS).divide(10000).updateMask(valid)
        allpx = img.select("B2").gt(-1e9).rename("all")  # footprint pixels, for the clear share
        st = sr.addBands(allpx).reduceRegions(collection=fc, reducer=red, scale=20, tileScale=4)
        df = to_df(st)
        df["image"] = iid
        df["date"] = pd.to_datetime(iid[:8])
        recs.append(df)
        print(f"  {k}/{len(ids)} {iid[:8]}", flush=True)
    ts = pd.concat(recs, ignore_index=True)
    ts.to_csv(CACHE[mask], index=False)


def looks(mask="scl"):
    d = pd.read_csv(CACHE[mask], parse_dates=["date"])
    d = d.rename(columns={f"{b}_mean": b for b in BANDS})
    d["clear_share"] = d["B2_count"] / d["all_count"].replace(0, np.nan)
    d = d[(d.clear_share >= CLEAR)].dropna(subset=BANDS)
    d = d.sort_values("clear_share", ascending=False).drop_duplicates(["field_id", "date"])
    d["NDVI"] = (d.B8 - d.B4) / (d.B8 + d.B4)
    d["NBR"] = (d.B8 - d.B12) / (d.B8 + d.B12)
    d["NBR2"] = (d.B11 - d.B12) / (d.B11 + d.B12)
    d["BAIS2"] = w.bais2(d.B4, d.B6, d.B7, d.B8, d.B12)  # B8 for B8A, as in W1
    d["TCB"] = w.tcb(d.B2, d.B3, d.B4, d.B8, d.B11, d.B12)
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=w.VARS)
    sc, m = w.lp.model()
    d["z"] = m.decision_function(sc.transform(d[["BAIS2", "TCB"]].to_numpy()))
    return d.sort_values(["field_id", "date"])


def walker_model():
    """RF on all Walker fields (ground truth); CV cut keeping 90% of Walker burns."""
    z = zipfile.ZipFile(w.ZIP)
    s2 = pd.concat([w.s2_looks(z, k).assign(kind=k) for k in ["burnt", "tilled"]], ignore_index=True)
    f = pd.concat([w.s2_features(s2[s2.kind == k], PRE_LOOKS).assign(kind=k) for k in ["burnt", "tilled"]])
    cols = [c for c in f.columns if c.startswith(("post_", "d_")) and c != "post_day"]
    X, y = f[cols].to_numpy(), (f.kind == "burnt").astype(int).to_numpy()
    make = lambda: w.RandomForestClassifier(500, min_samples_leaf=5, class_weight="balanced",  # noqa: E731
                                            random_state=42, n_jobs=-1)
    oof = np.zeros(len(y))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=42).split(X, y):
        oof[te] = make().fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    cut90 = float(np.quantile(oof[y == 1], 0.1))
    print(f"Walker CV: cut keeping 90% burns = {cut90:.3f}; tilled called burnt at that cut "
          f"{(oof[y == 0] >= cut90).mean():.3f} (n {int((y == 0).sum())})")
    return make().fit(X, y), cols, cut90


def before(g, date):
    pre = g[(g.date < date) & (g.date >= date - pd.Timedelta(days=PRE_DAYS))]
    return pre.tail(PRE_LOOKS) if PRE_LOOKS else pre


def score_fields(d, ids, win, rf, cols):
    """Per field: first flagged look in win = candidate; RF prob on candidate vs pre-looks."""
    rows = []
    for fid in ids:
        g = d[d.field_id == fid]
        inwin = g[(g.date >= win[0]) & (g.date <= win[1])]
        r = {"field_id": fid, "s2_looks": len(inwin), "old_called_burnt": int((inwin.z > 0).any())}
        flagged = inwin[inwin.z > 0]
        if len(flagged):
            if CANDIDATE == "jump":
                rise = g.z.diff().reindex(flagged.index)  # vs the previous clear look (may be before win)
                c = flagged.loc[rise.fillna(-np.inf).idxmax()]
                r["candidate_rise"] = round(rise.loc[c.name], 2) if pd.notna(rise.loc[c.name]) else np.nan
            else:
                c = flagged.iloc[0]
            pre = before(g, c.date)
            r.update({"candidate_date": c.date, "candidate_z": round(c.z, 2), "n_pre": len(pre),
                      "pre_last_date": pre.date.max() if len(pre) else pd.NaT,
                      "pre_ndvi": round(pre.NDVI.median(), 3) if len(pre) else np.nan})
            if len(pre):
                x = pd.concat([c[w.VARS].astype(float).add_prefix("post_"),
                               (c[w.VARS].astype(float) - pre[w.VARS].median()).add_prefix("d_")])
                r["prob"] = rf.predict_proba(x[cols].to_numpy()[None, :])[0, 1]
                # sensitivity: best-scoring flagged look in the window (not only the first)
                ps = []
                for _, cc in flagged.iterrows():
                    pp = before(g, cc.date)
                    if len(pp):
                        xx = pd.concat([cc[w.VARS].astype(float).add_prefix("post_"),
                                        (cc[w.VARS].astype(float) - pp[w.VARS].median()).add_prefix("d_")])
                        ps.append(rf.predict_proba(xx[cols].to_numpy()[None, :])[0, 1])
                r["prob_any"] = max(ps)
        rows.append(r)
    return pd.DataFrame(rows)


def summarise(f, truth, judge, subset, cut90):
    out = []
    t = f[truth].astype(int)
    for method, called in [
        ("old BAIS2+TCB", f.old_called_burnt == 1),
        ("Walker RF, cut 0.5", f.prob.fillna(0) >= 0.5),
        (f"Walker RF, cut {cut90:.2f} (90% Walker burns)", f.prob.fillna(0) >= cut90),
        (f"Walker RF any flagged look, cut {cut90:.2f}", f.prob_any.fillna(0) >= cut90),
    ]:
        out.append({"judge": judge, "subset": subset, "method": method,
                    "judge_burnt": int((t == 1).sum()), "judge_not_burnt": int((t == 0).sum()),
                    "burns_caught": f"{int((called & (t == 1)).sum())}/{int((t == 1).sum())}",
                    "not_burnt_called_burnt": f"{int((called & (t == 0)).sum())}/{int((t == 0).sum())}",
                    "share_burns_caught": round((called[t == 1]).mean(), 3),
                    "share_not_burnt_called_burnt": round((called[t == 0]).mean(), 3)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--mask", choices=["scl", "cloudprob"], default="scl")
    ap.add_argument("--pre-looks", type=int, default=None)
    ap.add_argument("--candidate", choices=["first", "jump"], default="first")
    args = ap.parse_args()
    global PRE_LOOKS, CANDIDATE
    PRE_LOOKS, CANDIDATE = args.pre_looks, args.candidate
    mask, sfx = args.mask, (SUFFIX[args.mask] + (f"_pre{PRE_LOOKS}" if PRE_LOOKS else "")
                            + ("_jump" if CANDIDATE == "jump" else ""))
    if args.extract or not CACHE[mask].exists():
        extract(mask)
    d = looks(mask)
    print(f"clear field looks: {len(d)}, fields {d.field_id.nunique()}, dates {d.date.nunique()}")
    rf, cols, cut90 = walker_model()

    # Judge A: Planet rule on the 95 CEEW-unburnt fields
    pr = pd.read_csv(OUT / "jalandhar_planet_rule_fields.csv", parse_dates=["burn_day"])
    a = score_fields(d, pr.field_id, WIN_A, rf, cols).merge(
        pr[["field_id", "min_ratio", "burn_day", "planet_burnt"]], on="field_id")
    a.to_csv(OUT / f"jalandhar_walker_fields_A{sfx}.csv", index=False)

    # Judge B: CEEW field visit on 29 Oct
    cat = d.drop_duplicates("field_id").set_index("field_id").field_category
    b = score_fields(d, cat.index, WIN_B, rf, cols)
    b["field_category"] = b.field_id.map(cat)
    b["ceew_burnt"] = (b.field_category != "unburnt").astype(int)
    b.to_csv(OUT / f"jalandhar_walker_fields_B{sfx}.csv", index=False)

    res = []
    res += summarise(a, "planet_burnt", "A Planet rule (29 Oct-13 Nov)", "all 95", cut90)
    res += summarise(a[a.burn_day != EDGE], "planet_burnt", "A Planet rule (29 Oct-13 Nov)",
                     "darkest Planet day not 13 Nov", cut90)
    res += summarise(b, "ceew_burnt", "B CEEW visit (by 29 Oct)", "all", cut90)
    for c in ["completely_burnt", "partially_burnt"]:
        res += summarise(b[b.field_category.isin([c, "unburnt"])], "ceew_burnt", "B CEEW visit (by 29 Oct)",
                         f"{c} vs unburnt", cut90)
    res = pd.DataFrame(res)
    res.to_csv(OUT / f"jalandhar_walker_results{sfx}.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(res.drop(columns=["share_burns_caught", "share_not_burnt_called_burnt"]).to_string(index=False))
    na = a[a.planet_burnt == 0]
    print("\nPlanet-not-burnt fields the old detector flagged:")
    print(na[na.old_called_burnt == 1][["field_id", "candidate_date", "candidate_z", "n_pre", "prob", "prob_any",
                                         "min_ratio", "burn_day"]].round(3).to_string(index=False))
    print("\nfields with a candidate but no pre-look (A / B):",
          int((a.old_called_burnt.eq(1) & a.prob.isna()).sum()), "/", int((b.old_called_burnt.eq(1) & b.prob.isna()).sum()))


if __name__ == "__main__":
    main()
