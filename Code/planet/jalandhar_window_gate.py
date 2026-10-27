"""Gate test before the tehsil run (2026-10-27): does the final model still work on a 3x3 window
instead of a whole-field mean?

The tehsil run has no field boundaries, only random rice points. There each point is read as the mean of a
~60 m square (3x3 pixels at 20 m) around it. Here the same is done on the 357 Jalandhar 2021 fields: one
random point inside each field (seed 42; random, not central, so edge cases occur as they will in tehsils),
a 60 m square around it, clear share >= 0.8 inside the square. Everything else is the final setting from
jalandhar_walker_model_test.py: Walker RF, jump candidate, last-1-look "before", cuts 0.5 and Walker cut90.

Pass if the window results stay close to the field-mean results (A 51/63 burns, 3/32 false at 0.5).

Run:  python Code/planet/jalandhar_window_gate.py [--extract]
Out:  outputs/planet/jalandhar_s2_window_2021.csv (cache), jalandhar_window_fields_{A,B}.csv,
      jalandhar_window_results.csv
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Point, shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "planet"))
import jalandhar_walker_model_test as jw  # noqa: E402

OUT = jw.OUT
CACHE = OUT / "jalandhar_s2_window_2021.csv"
HALF = 30  # m; square of 60 m = 3x3 pixels at 20 m
SEED = 42


def random_points():
    from transfer_checks import GT_DIR, LABEL_DATES
    gj = json.loads((GT_DIR / LABEL_DATES[2021][0]).read_text())
    rng = np.random.default_rng(SEED)
    rows = []
    for f in gj["features"]:
        g = shape(f["geometry"])
        minx, miny, maxx, maxy = g.bounds
        while True:
            p = Point(rng.uniform(minx, maxx), rng.uniform(miny, maxy))
            if g.contains(p):
                break
        rows.append({"field_id": f["properties"]["field_id"],
                     "field_category": f["properties"]["field_category"], "lon": p.x, "lat": p.y})
    return pd.DataFrame(rows)


def extract():
    import ee
    from transfer_checks import init_ee, to_df
    init_ee()
    pts = random_points()
    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry.Point([r.lon, r.lat]).buffer(HALF).bounds(),
                   {"field_id": r.field_id, "field_category": r.field_category}) for r in pts.itertuples()])
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
           .filterDate("2021-09-10", "2021-11-21").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))
    ids = col.aggregate_array("system:index").getInfo()
    print(f"{len(ids)} images", flush=True)
    red = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
    recs = []
    for k, iid in enumerate(ids, 1):
        img = ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + iid)
        scl = img.select("SCL")
        valid = scl.eq(2).Or(scl.eq(4)).Or(scl.eq(5)).Or(scl.eq(7))
        sr = img.select(jw.BANDS).divide(10000).updateMask(valid)
        allpx = img.select("B2").gt(-1e9).rename("all")
        st = sr.addBands(allpx).reduceRegions(collection=fc, reducer=red, scale=20, tileScale=4)
        df = to_df(st)
        df["image"] = iid
        df["date"] = pd.to_datetime(iid[:8])
        recs.append(df)
        print(f"  {k}/{len(ids)} {iid[:8]}", flush=True)
    pd.concat(recs, ignore_index=True).to_csv(CACHE, index=False)
    pts.to_csv(OUT / "jalandhar_window_points.csv", index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true")
    args = ap.parse_args()
    if args.extract or not CACHE.exists():
        extract()
    jw.PRE_LOOKS, jw.CANDIDATE = 1, "jump"
    jw.CACHE["window"] = CACHE
    d = jw.looks("window")
    print(f"clear window looks: {len(d)}, fields {d.field_id.nunique()}, dates {d.date.nunique()}")
    rf, cols, cut90 = jw.walker_model()

    pr = pd.read_csv(OUT / "jalandhar_planet_rule_fields.csv", parse_dates=["burn_day"])
    a = jw.score_fields(d, pr.field_id, jw.WIN_A, rf, cols).merge(
        pr[["field_id", "min_ratio", "burn_day", "planet_burnt"]], on="field_id")
    a.to_csv(OUT / "jalandhar_window_fields_A.csv", index=False)
    cat = d.drop_duplicates("field_id").set_index("field_id").field_category
    b = jw.score_fields(d, cat.index, jw.WIN_B, rf, cols)
    b["field_category"] = b.field_id.map(cat)
    b["ceew_burnt"] = (b.field_category != "unburnt").astype(int)
    b.to_csv(OUT / "jalandhar_window_fields_B.csv", index=False)

    res = []
    res += jw.summarise(a, "planet_burnt", "A Planet rule (29 Oct-13 Nov)", "all 95", cut90)
    res += jw.summarise(a[a.burn_day != jw.EDGE], "planet_burnt", "A Planet rule (29 Oct-13 Nov)",
                        "darkest Planet day not 13 Nov", cut90)
    res += jw.summarise(b, "ceew_burnt", "B CEEW visit (by 29 Oct)", "all", cut90)
    for c in ["completely_burnt", "partially_burnt"]:
        res += jw.summarise(b[b.field_category.isin([c, "unburnt"])], "ceew_burnt", "B CEEW visit (by 29 Oct)",
                            f"{c} vs unburnt", cut90)
    res = pd.DataFrame(res)
    res.to_csv(OUT / "jalandhar_window_results.csv", index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(res.drop(columns=["share_burns_caught", "share_not_burnt_called_burnt"]).to_string(index=False))

    # per-field agreement with the field-mean run (same setting)
    for j, f in [("A", a), ("B", b)]:
        ref = pd.read_csv(OUT / f"jalandhar_walker_fields_{j}_pre1_jump.csv")[["field_id", "prob"]]
        m = f[["field_id", "prob"]].merge(ref, on="field_id", suffixes=("_win", "_field"))
        both = m.dropna()
        for cut in [0.5, cut90]:
            cw, cf = m.prob_win.fillna(0) >= cut, m.prob_field.fillna(0) >= cut
            print(f"{j} cut {cut:.2f}: same call {int((cw == cf).sum())}/{len(m)}; "
                  f"window-only burnt {int((cw & ~cf).sum())}, field-only burnt {int((cf & ~cw).sum())}")
        print(f"{j} prob correlation (fields scored both ways, n {len(both)}): "
              f"{both.prob_win.corr(both.prob_field):.3f}; no score in window run "
              f"{int(m.prob_win.isna().sum())}, in field run {int(m.prob_field.isna().sum())}")


if __name__ == "__main__":
    main()
