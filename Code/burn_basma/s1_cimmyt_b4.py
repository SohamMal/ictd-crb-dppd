"""
Branch B, test B4: Basma's "ploughed, not burnt" row, approximated on CIMMYT 1 km cells (2026-10-22)

No field-level ploughed-unburnt truth exists (CIMMYT plot coordinates are rounded to 0.01 deg), so the
unit is the ~1 km cell, as in Code/burn/cimmyt_cell_validation.py (cells and survey shares reused).

Per cell, official window 15 Sep - 30 Nov (2022: capped at the cell's last visit date):
  candidates  cropland pixels (ESA WorldCover 2021 = 40, 20 m) flagged burnt by BAIS2+TCB in any clear
              Sentinel-2 look (same pooled relaxed-mask model as branch A) = the "official" rule
  S1 filter   for every flagged look on date d and every relative orbit over the cell: dVV = first S1 image
              in (d, d+12] minus last in [d-12, d] (same orbit), on 30 m focal-mean linear power, in dB;
              dVV averaged over the orbits that have a pair. A candidate with mean dVV > t is reclassified
              as ploughing. A pixel stays burnt if at least one of its candidate looks survives.
Basma's numbers, per cell group:
  reclassified share = 1 - survivors / candidates
  want: high in cells whose farmers did not burn (esp. Super Seeder / Happy Seeder), low in all-burnt cells

Run:  python Code/burn_basma/s1_cimmyt_b4.py
Out:  outputs/burn_basma/b4_cell_shares.csv, b4_scores.csv (local only: cell locations are sensitive)
"""

import sys
from pathlib import Path

import ee
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "burn"))
import cimmyt_cell_validation as cv  # noqa: E402
import labelling_package as lp  # noqa: E402
from transfer_checks import MASKS, ROOT, ee_classifier, indices, init_ee  # noqa: E402

OUT = ROOT / "outputs" / "burn_basma"
THRESHOLDS = [1.5, 3.0]
PAIR_DAYS = 12


def s1_db_smooth(img):
    lin = ee.Image(10).pow(img.select("VV").divide(10)).focalMean(30, "circle", "meters")
    return lin.log10().multiply(10).rename("VV").copyProperties(img, ["system:time_start", "relativeOrbitNumber_start"])


def cell_shares(w):
    path = OUT / "b4_cell_shares_v2.csv"
    if path.exists():
        return pd.read_csv(path)
    sc, m = lp.model()
    clf = ee_classifier(sc, m)
    crop = ee.Image("ESA/WorldCover/v200/2021").select("Map").eq(40)
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
    s1all = (ee.ImageCollection("COPERNICUS/S1_GRD").filter(ee.Filter.eq("instrumentMode", "IW"))
             .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV")))

    def one(f):
        geom = f.geometry()
        start, end = ee.Date(f.get("start")), ee.Date(f.get("end"))
        s1 = s1all.filterBounds(geom).filterDate(start.advance(-PAIR_DAYS, "day"), end.advance(PAIR_DAYS, "day")) \
                  .map(s1_db_smooth)
        orbits = s1.aggregate_array("relativeOrbitNumber_start").distinct()

        def dvv(d):
            def per_orbit(o):
                so = s1.filter(ee.Filter.eq("relativeOrbitNumber_start", o))
                bef = so.filterDate(d.advance(-PAIR_DAYS, "day"), d.advance(1, "day")).sort("system:time_start", False)
                aft = so.filterDate(d.advance(1, "day"), d.advance(PAIR_DAYS + 1, "day")).sort("system:time_start")
                ok = bef.size().gt(0).And(aft.size().gt(0))
                return ee.Image(ee.Algorithms.If(ok, ee.Image(aft.first()).subtract(ee.Image(bef.first())),
                                                 ee.Image.constant(0).rename("VV").updateMask(0))).toFloat()
            return ee.ImageCollection(orbits.map(per_orbit)).mean().rename("dVV")

        surv_names = [f"surv_{t}".replace(".", "_") for t in THRESHOLDS]

        def per_look(img):
            cand = clf(indices(img, MASKS["relaxed_scl2457"])).unmask(0)
            d = dvv(img.date()).unmask(-99)            # no S1 pair -> cannot reclassify, stays a burn
            surv = [cand.And(d.lte(t)).rename(n) for t, n in zip(THRESHOLDS, surv_names)]
            days = ee.Image.constant(img.date().difference(start, "day")).rename("t").updateMask(cand)
            return ee.Image.cat([cand.rename("cand")] + surv).toFloat().addBands(days.toFloat())

        col = s2.filterBounds(geom).filterDate(start, end).map(per_look)
        names = ["cand"] + surv_names
        flags = col.select(names)
        empty = ee.Image.constant([0] * len(names)).rename(names).toFloat().updateMask(0)
        # pixel rule "any": burnt if at least one candidate look survives
        anyflag = ee.Image(ee.Algorithms.If(col.size().gt(0), flags.max(), empty)).updateMask(crop)
        # event counts: every flagged look is one candidate event
        events = ee.Image(ee.Algorithms.If(col.size().gt(0), flags.sum(), empty)).updateMask(crop)                    .rename([f"ev_{n}" for n in names])
        # pixel rule "first": only the pixel's first candidate look counts (its date + whether it survived)
        firstcol = col.map(lambda i: i.select(["t"] + surv_names).updateMask(i.select("cand")))
        first = ee.Image(ee.Algorithms.If(col.size().gt(0), firstcol.reduce(ee.Reducer.min(1 + len(surv_names))),
                                          ee.Image.constant([0] * (1 + len(surv_names))).updateMask(0)))                   .rename(["first_t"] + [f"first_{n}" for n in surv_names]).unmask(0).updateMask(crop)
        img = anyflag.addBands(events).addBands(first.select([f"first_{n}" for n in surv_names]))
        st = img.reduceRegion(ee.Reducer.mean(), geom, 20, maxPixels=1e8, tileScale=4)
        return f.set(st).set({"images": col.size(), "orbits": orbits.size()})

    parts = []
    for k in range(0, len(w), 25):
        chunk = w.iloc[k:k + 25]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Rectangle([r.lon - cv.HALF, r.lat - cv.HALF, r.lon + cv.HALF, r.lat + cv.HALF]),
                                              {"cell": r.cell, "start": r.start, "end": r.end})
                                   for r in chunk.itertuples()])
        df = ee.data.computeFeatures({"expression": fc.map(one), "fileFormat": "PANDAS_DATAFRAME"})
        parts.append(df.drop(columns=["geo"], errors="ignore"))
        print(f"  cells {k + len(chunk)}/{len(w)}", flush=True)
    res = pd.concat(parts, ignore_index=True)
    res.to_csv(path, index=False)
    return res


def evaluate(c, rs):
    d = c.merge(rs, on="cell", how="inner")
    surv = [col for col in d if col.startswith("surv_")]
    rows = []
    for year, g in d.groupby("year"):
        groups = {"all burnt": g[g.survey_burnt == 1], "some burnt": g[(g.survey_burnt > 0) & (g.survey_burnt < 1)],
                  "none burnt": g[g.survey_burnt == 0],
                  "none burnt, SS/HS used": g[(g.survey_burnt == 0) & (g.n_unburnt_SS_HS >= 1)]}
        for name, h in groups.items():
            r = {"year": year, "cells": name, "n": len(h), "candidate_share": round(h.cand.mean(), 3)}
            for s in surv:
                t = s.replace("surv_", "").replace("_", ".")
                r[f"burnt_share_t{t}"] = round(h[s].mean(), 3)
                r[f"reclassified_t{t}"] = round(1 - h[s].sum() / h.cand.sum(), 3) if h.cand.sum() else None
            rows.append(r)
            r2 = {"year": year, "cells": name + " | events", "n": len(h)}
            for s_ in surv:
                t = s_.replace("surv_", "").replace("_", ".")
                r2[f"reclassified_t{t}"] = round(1 - h["ev_" + s_].sum() / h.ev_cand.sum(), 3)
                r2[f"burnt_share_t{t}"] = round(h["first_" + s_].mean(), 3)   # first-event rule
            rows.append(r2)
        for col in ["cand"] + surv + [f"first_{x}" for x in surv]:
            rows.append({"year": year, "cells": f"rho survey vs {col}", "n": len(g),
                         "candidate_share": round(g.survey_burnt.corr(g[col], "spearman"), 3)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "b4_scores_v2.csv", index=False)
    print(t.to_string(index=False))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = cv.cells(cv.plots())
    init_ee()
    w = []
    for r in c.itertuples():
        s, e = pd.Timestamp(f"{r.year}-09-15"), pd.Timestamp(f"{r.year}-11-30")
        if r.year == 2022:
            e = min(e, r.visit_max)
        w.append({"cell": r.cell, "lat": r.lat, "lon": r.lon, "start": str(s.date()),
                  "end": str((e + pd.Timedelta(days=1)).date())})
    rs = cell_shares(pd.DataFrame(w))
    evaluate(c, rs)


if __name__ == "__main__":
    main()
