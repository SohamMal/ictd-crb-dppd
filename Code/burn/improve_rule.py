"""
Sharper burn rule, scored on CIMMYT 1 km cells (2026-10-18)

The heat-peak window rule (any clear S2 flag within the MODIS peak window) separates 2021 CIMMYT
cells (all-burnt 0.74 vs all-unburnt 0.53) but not 2022. Ploughed / sown soil inside the window is
still flagged. Candidate refinements, per pixel, computed per cell and window:

  any       flagged (pooled BAIS2+TCB model) in >= 1 clear look in the window (current rule)
  jump      a flagged look in the window preceded by a clear UNflagged look of the same pixel within
            GAP days: the stubble -> dark transition. Single dark looks with no stubble look just
            before (e.g. soil that stays dark for weeks) do not count
  jump_nbrTT jump, and NBR2 = (B11 - B12) / (B11 + B12) > T at the flagged look (char kept a
            higher NBR2 than ploughed soil: medians 0.099 vs 0.049, AUC 0.735, char_vs_soil.py)
  rise      MODIS Aqua-day anomaly: smoothed peak - mean 15 Aug - 15 Sep (cell centre)

Windows: season (1 Oct - 15 Dec), peak -7..+7, peak -21..+14. 2022 windows end at the last visit.
Scores per year: AUC all-burnt vs all-unburnt cells, Spearman with survey burnt share (all cells).
Combination: logistic regression on survey burnt share (weighted by plots), trained leave-one-
district-out on 2021, then trained on all 2021 and tested on 2022.

Run:  python Code/burn/improve_rule.py
Out:  outputs/burn_cimmyt/improve_*.csv
"""

import ee
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

import labelling_package as lp
from cimmyt_cell_validation import HALF, OUT, cells, plots
from modis_lste_check import whittaker
from peak_window import LAM
from transfer_checks import MASKS, ee_classifier, indices, init_ee

GAP = 12
NBR2_T = [0.06, 0.08, 0.10]
WINS = ["season", "peak_-7_7", "peak_-21_14"]


def windows(c, pk):
    c = c.merge(pk.rename(columns={"loc": "cell"})[["cell", "peak_date"]], on="cell", how="left")
    rows = []
    for r in c.itertuples():
        y = r.year
        cap = r.visit_max if y == 2022 else pd.Timestamp(f"{y}-12-31")
        spec = {"season": (pd.Timestamp(f"{y}-10-01"), pd.Timestamp(f"{y}-12-15"))}
        if pd.notna(r.peak_date):
            spec["peak_-7_7"] = (r.peak_date - pd.Timedelta(days=7), r.peak_date + pd.Timedelta(days=7))
            spec["peak_-21_14"] = (r.peak_date - pd.Timedelta(days=21), r.peak_date + pd.Timedelta(days=14))
        for name, (s, e) in spec.items():
            e = min(e, cap)
            if e > s:
                rows.append({"cell": r.cell, "lat": r.lat, "lon": r.lon, "rule": name, "start": str(s.date()),
                             "end": str((e + pd.Timedelta(days=1)).date()),
                             "lookback": str((s - pd.Timedelta(days=GAP)).date())})
    return c, pd.DataFrame(rows)


def ee_features(w):
    path = OUT / "improve_cell_shares.csv"
    if path.exists():
        return pd.read_csv(path)
    sc, m = lp.model()
    clf = ee_classifier(sc, m)
    crop = ee.Image("ESA/WorldCover/v200/2021").select("Map").eq(40)
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
    empty_flag = ee.Image.constant(0).toByte().rename("burnt_px").updateMask(0)
    bands = ["any", "jump"] + [f"jump_nbr{round(t * 100):02d}" for t in NBR2_T]
    empty_out = ee.Image.constant([0] * len(bands)).toByte().rename(bands).updateMask(0)

    def prep(img):
        flag = clf(indices(img, MASKS["relaxed_scl2457"])).toByte()            # masked where SCL invalid
        sr = img.select(["B11", "B12"]).divide(10000)
        nbr2 = sr.normalizedDifference(["B11", "B12"]).rename("NBR2").updateMask(flag.mask())
        return flag.addBands(nbr2).copyProperties(img, ["system:time_start"])

    def one(f):
        geom = f.geometry()
        col = s2.filterBounds(geom).filterDate(f.get("lookback"), f.get("end")).map(prep)
        unfl = col.map(lambda i: i.select("burnt_px").eq(0).selfMask().copyProperties(i, ["system:time_start"]))
        inwin = col.filterDate(f.get("start"), f.get("end"))

        def per_look(img):
            t = img.date()
            prior = unfl.filterDate(t.advance(-GAP, "day"), t)
            had_stubble = ee.Image(ee.Algorithms.If(prior.size().gt(0), prior.max(), empty_flag)).unmask(0).eq(1)
            fl = img.select("burnt_px").eq(1)
            jump = fl.And(had_stubble)
            out = [fl.rename("any"), jump.rename("jump")]
            out += [jump.And(img.select("NBR2").gt(t_)).rename(f"jump_nbr{round(t_ * 100):02d}") for t_ in NBR2_T]
            return ee.Image.cat(out).toByte().updateMask(img.select("burnt_px").mask())

        anyimg = ee.Image(ee.Algorithms.If(inwin.size().gt(0), inwin.map(per_look).max(), empty_out))
        st = anyimg.updateMask(crop).reduceRegion(ee.Reducer.mean(), geom, 20, maxPixels=1e8, tileScale=4)
        return f.set(st).set("images", inwin.size())

    parts = []
    for k in range(0, len(w), 60):
        chunk = w.iloc[k:k + 60]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Rectangle([r.lon - HALF, r.lat - HALF, r.lon + HALF, r.lat + HALF]),
                                              {"cell": r.cell, "rule": r.rule, "start": r.start, "end": r.end,
                                               "lookback": r.lookback}) for r in chunk.itertuples()])
        for attempt in range(4):
            try:
                df = ee.data.computeFeatures({"expression": fc.map(one), "fileFormat": "PANDAS_DATAFRAME"})
                break
            except Exception as e:
                print(f"    retry {attempt + 1}: {str(e)[:80]}", flush=True)
        else:
            raise RuntimeError("Earth Engine request failed 4 times")
        parts.append(df.drop(columns=["geo"], errors="ignore"))
        print(f"  cells x windows {k + len(chunk)}/{len(w)}", flush=True)
    res = pd.concat(parts, ignore_index=True)
    res.to_csv(path, index=False)
    return res


def modis_rise(c):
    ms = pd.read_csv(OUT / "modis_aqua_anomaly.csv", parse_dates=["date"])
    yr = c.set_index("cell").year
    rows = []
    for cell, g in ms.groupby("loc"):
        y = int(yr[cell])
        days = pd.date_range(f"{y}-08-01", f"{y}-12-31")
        z = whittaker(g.groupby("date").anom.mean().reindex(days).to_numpy(dtype=float), LAM)
        base = np.nanmean(z[(days >= f"{y}-08-15") & (days <= f"{y}-09-15")])
        inside = (days >= f"{y}-09-15") & (days <= f"{y}-11-30")
        rows.append({"cell": cell, "rise": np.nanmax(z[inside]) - base, "peak_level": np.nanmax(z[inside])})
    return pd.DataFrame(rows)


def auc(y, s):
    ok = ~(np.isnan(y) | np.isnan(s))
    return roc_auc_score(y[ok], s[ok]) if len(np.unique(y[ok])) == 2 else np.nan


def score(d):
    feats = [c for c in d.columns if "|" in c] + ["rise", "peak_level"]
    rows = []
    for year, g in d.groupby("year"):
        ext = g[g.survey_burnt.isin([0, 1])]
        for f in feats:
            rows.append({"year": year, "feature": f, "cells": int(g[f].notna().sum()),
                         "mean": round(g[f].mean(), 3),
                         "auc_allburnt_vs_allunburnt": round(auc(ext.survey_burnt.to_numpy(float), ext[f].to_numpy(float)), 3),
                         "rho_all": round(g.survey_burnt.corr(g[f], "spearman"), 3),
                         "mean_allburnt": round(ext[ext.survey_burnt == 1][f].mean(), 3),
                         "mean_allunburnt": round(ext[ext.survey_burnt == 0][f].mean(), 3)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "improve_feature_scores.csv", index=False)
    piv = t.pivot_table(index="feature", columns="year", values=["auc_allburnt_vs_allunburnt", "rho_all", "mean_allburnt", "mean_allunburnt"])
    print("\nSingle features (AUC: all-burnt vs all-unburnt cells; rho: survey share, all cells):")
    print(piv.round(3).to_string())
    return t


def combos(d):
    sets = {"any|peak_-7_7": ["any|peak_-7_7"],
            "any|peak_-7_7 + rise": ["any|peak_-7_7", "rise"],
            "jump|peak_-7_7 + rise": ["jump|peak_-7_7", "rise"],
            "jump_nbr08|peak_-7_7 + rise": ["jump_nbr08|peak_-7_7", "rise"],
            "jump|season + rise": ["jump|season", "rise"],
            "jump|peak_-21_14 + jump_nbr08|peak_-21_14 + rise": ["jump|peak_-21_14", "jump_nbr08|peak_-21_14", "rise"]}
    a, b = d[d.year == 2021], d[d.year == 2022]
    rows = []
    for name, fs in sets.items():
        if not all(f in d for f in fs):
            continue
        A = a.dropna(subset=fs + ["survey_burnt"])
        pred = pd.Series(np.nan, index=A.index)
        for dist in A.district.unique():               # leave one district out
            tr, te = A[A.district != dist], A[A.district == dist]
            m, sc = fit(tr, fs)
            pred[te.index] = m.predict_proba(sc.transform(te[fs]))[:, 1]
        ext = A.survey_burnt.isin([0, 1])
        m, sc = fit(A, fs)
        B = b.dropna(subset=fs + ["survey_burnt"])
        pb = m.predict_proba(sc.transform(B[fs]))[:, 1]
        extb = B.survey_burnt.isin([0, 1])
        rows.append({"features": name,
                     "2021_LODO_auc": round(auc(A.survey_burnt[ext].to_numpy(float), pred[ext].to_numpy(float)), 3),
                     "2021_LODO_rho": round(A.survey_burnt.corr(pred, "spearman"), 3),
                     "2022_test_auc": round(auc(B.survey_burnt[extb].to_numpy(float), pb[extb.to_numpy()]), 3),
                     "2022_test_rho": round(pd.Series(pb, index=B.index).corr(B.survey_burnt, "spearman"), 3),
                     "coefs": dict(zip(fs, np.round(m.coef_[0], 2)))})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "improve_combos.csv", index=False)
    print("\nCombinations (2021 leave-one-district-out; then fit on 2021, test on 2022):")
    print(t.to_string(index=False))


def fit(df, fs):
    """Logistic on plot-level outcomes: each cell contributes burnt and unburnt plot counts."""
    X = df[fs].to_numpy(float)
    sc = StandardScaler().fit(X)
    Xs = sc.transform(X)
    yb = df.survey_burnt.to_numpy(float) * df.n_plots.to_numpy(float)
    yu = df.n_plots.to_numpy(float) - yb
    Xd = np.vstack([Xs, Xs])
    y = np.r_[np.ones(len(Xs)), np.zeros(len(Xs))]
    w = np.r_[yb, yu]
    keep = w > 0
    m = LogisticRegression(max_iter=2000).fit(Xd[keep], y[keep], sample_weight=w[keep])
    return m, sc


def main():
    p = plots()
    c = cells(p)
    pk = pd.read_csv(OUT / "cell_peaks.csv", parse_dates=["peak_date"])
    c, w = windows(c, pk)
    init_ee()
    ee_df = ee_features(w)
    wide = ee_df.pivot_table(index="cell", columns="rule", values=["any", "jump"] + [f"jump_nbr{round(t * 100):02d}" for t in NBR2_T])
    wide.columns = [f"{a}|{b}" for a, b in wide.columns]
    d = c.merge(wide.reset_index(), on="cell", how="left").merge(modis_rise(c), on="cell", how="left")
    d.to_csv(OUT / "improve_cell_table.csv", index=False)
    score(d)
    combos(d)


if __name__ == "__main__":
    main()
