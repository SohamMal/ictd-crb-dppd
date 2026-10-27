"""
Does MODIS heat track how much of a 1 km pixel burnt? (2026-10-18)

modis_lste_check.py could not validate MODIS LST & emissivity: CEEW fields cover only ~2-5% of a
1 km pixel. Here the 1 km reference comes from our own BAIS2 + TCB model on the single label-date
Sentinel-2 image (reliable on one date: 96-100% on CEEW; only season-long accumulation fails).

  burnt_frac  share of a MODIS pixel's cropland (ESA WorldCover 2021 = 40) flagged burnt at 20 m
              on the label image (2020-11-10, 2021-10-29); pixels need >= 50% valid cropland
  MODIS       MOD21A1D (Terra ~10:30), MYD21A1D (Aqua ~13:30), MYD21A1N (~01:30), QC good;
              anomaly = pixel - daily median of the box; afternoon - morning = Aqua - Terra same day
  windows     baseline -60..-30 d, burn -15..+5 d, after +25..+45 d (vs label date); weekly means

Area: CEEW fields' bounding box + 30 km, clipped to the label image footprint.
Caveat: on the label date "burnt" pixels can also include tilled soil (the known confusion);
small on 29 Oct 2021, larger on 10 Nov 2020.

Run:  python Code/burn/modis_vs_s2_burnfrac.py [--skip-extract]
Out:  outputs/burn_checks/modis_s2_*.csv
"""

import argparse

import ee
import numpy as np
import pandas as pd

from transfer_checks import (LABEL_DATES, MASKS, OUT, ee_classifier, fields, fit, indices, init_ee,
                             label_image)

PASSES = {"terra": "MODIS/061/MOD21A1D", "aqua": "MODIS/061/MYD21A1D", "night": "MODIS/061/MYD21A1N"}
REGION_KM = 30
WINDOWS = {"base": (-60, -30), "burn": (-15, 5), "after": (25, 45)}
WEEKS = list(range(-63, 50, 7))
MASK = "relaxed_scl2457"


def pooled_model():
    df = pd.read_csv(OUT / f"check1_field_medians_{MASK}.csv").dropna(subset=["BAIS2", "TCB"])
    return fit(df)


def burnt_fraction(year, region, proj, clf):
    img = label_image(year)
    crop = ee.ImageCollection("ESA/WorldCover/v200").first().eq(40)
    flag = clf(indices(img, MASKS[MASK]))                       # 1/0, masked where SCL invalid
    valid = flag.mask().And(crop).rename("valid")
    burnt = flag.updateMask(crop).rename("burnt_frac")
    foot = img.select("B2").mask().rename("in_tile")
    stack = burnt.addBands(valid.unmask(0)).addBands(foot.unmask(0)).reproject(img.select("B2").projection().atScale(20))
    return stack.reduceResolution(ee.Reducer.mean(), maxPixels=4096).reproject(proj)


def prep(img):
    good = img.select("QC").bitwiseAnd(3).eq(0)
    out = img.select("LST_1KM").subtract(273.15).rename("LST").addBands(img.select(["Emis_29", "Emis_31"]))
    return out.updateMask(good).set("day", img.date().format("YYYY-MM-dd"),
                                    "system:time_start", img.get("system:time_start"))


def anomaly_col(cid, year, region):
    col = ee.ImageCollection(cid).filterDate(f"{year}-08-01", f"{year}-12-31").map(prep)

    bands = ["LST", "Emis_29", "Emis_31"]

    def add_median(img):
        med = img.reduceRegion(ee.Reducer.median(), region, 1000, maxPixels=1e9)
        return img.set({f"med_{b}": med.get(b) for b in bands})

    def anom(img):
        ref = ee.Image.constant([img.get(f"med_{b}") for b in bands]).rename(bands)
        return img.subtract(ref).float().copyProperties(img, ["day", "system:time_start"])
    # fully cloudy days have no regional median: drop them
    return col.map(add_median).filter(ee.Filter.notNull([f"med_{b}" for b in bands])).map(anom)


def window_mean(col, lab, a, b, bands, suffix):
    return (col.filterDate(lab.advance(a, "day"), lab.advance(b + 1, "day")).select(bands).mean()
            .rename([f"{x}_{suffix}" for x in bands]))


def metrics(year, region):
    lab = ee.Date(LABEL_DATES[year][1])
    cols = {k: anomaly_col(cid, year, region) for k, cid in PASSES.items()}
    join = ee.Join.inner().apply(cols["aqua"], cols["terra"], ee.Filter.equals(leftField="day", rightField="day"))
    aft = ee.ImageCollection(join.map(lambda f: ee.Image(f.get("primary")).select("LST")
                                      .subtract(ee.Image(f.get("secondary")).select("LST")).rename("AM").float()
                                      .copyProperties(ee.Image(f.get("primary")), ["system:time_start"])))
    sets = [(cols["aqua"], ["LST", "Emis_29", "Emis_31"], "aqua"), (cols["terra"], ["LST"], "terra"),
            (cols["night"], ["LST"], "night"), (aft, ["AM"], "am")]
    bands = []
    for col, bs, tag in sets:
        for w, (a, b) in WINDOWS.items():
            bands.append(window_mean(col, lab, a, b, bs, f"{tag}_{w}"))
        for wk in WEEKS:
            bands.append(window_mean(col, lab, wk, wk + 6, bs, f"{tag}_w{wk}"))
    return ee.Image.cat(bands)


def extract():
    sc, m = pooled_model()
    clf = ee_classifier(sc, m)
    proj = ee.Image(ee.ImageCollection(PASSES["aqua"]).first()).select("LST_1KM").projection()
    parts = []
    for year in LABEL_DATES:
        region = fields(year).geometry().bounds(1).buffer(REGION_KM * 1000, 1000).bounds(1)
        stack = burnt_fraction(year, region, proj, clf).addBands(metrics(year, region))
        samp = stack.sample(region=region, projection=proj, scale=proj.nominalScale(),
                            geometries=False, tileScale=8, dropNulls=False)
        df = ee.data.computeFeatures({"expression": samp, "fileFormat": "PANDAS_DATAFRAME"})
        df["year"] = year
        print(f"{year}: {len(df)} MODIS pixels sampled", flush=True)
        parts.append(df)
    df = pd.concat(parts, ignore_index=True)
    df.to_csv(OUT / "modis_s2_pixels.csv", index=False)
    return df


def evaluate(df):
    df = df[(df.in_tile >= 0.99) & (df.valid >= 0.5)].dropna(subset=["burnt_frac"]).copy()
    df["bf_q"] = df.groupby("year").burnt_frac.transform(lambda s: pd.qcut(s, 5, labels=False, duplicates="drop"))
    print("\nUsable pixels:", df.groupby("year").size().to_dict())
    print("Burnt fraction:", df.groupby("year").burnt_frac.describe().round(3).to_dict("index"))
    rows = []
    for year, g in df.groupby("year"):
        for tag, b in [("aqua", "LST"), ("terra", "LST"), ("night", "LST"), ("am", "AM"),
                       ("aqua", "Emis_29"), ("aqua", "Emis_31")]:
            base, burn, after = (g[f"{b}_{tag}_{w}"] for w in ("base", "burn", "after"))
            rise, fall = burn - base, burn - after
            ok = rise.notna()
            rows.append({"year": year, "feature": f"{b}_{tag}", "n": int(ok.sum()),
                         "rho_burnfrac_vs_level": round(g.burnt_frac.corr(burn, "spearman"), 3),
                         "rho_burnfrac_vs_rise": round(g.burnt_frac[ok].corr(rise[ok], "spearman"), 3),
                         "rho_burnfrac_vs_fall": round(g.burnt_frac.corr(fall, "spearman"), 3),
                         "rise_top_q_minus_bottom_q": round(rise[g.bf_q == 4].mean() - rise[g.bf_q == 0].mean(), 3)})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "modis_s2_evaluation.csv", index=False)
    print("\nSpearman with burnt fraction (level = burn-window mean; rise = burn - base; fall = burn - after)")
    print(res.to_string(index=False))

    curve = []
    for (year, q), g in df.groupby(["year", "bf_q"]):
        r = {"year": year, "burnfrac_quintile": int(q), "burnt_frac_mean": round(g.burnt_frac.mean(), 3)}
        for wk in WEEKS:
            r[f"AM_w{wk}"] = round(g[f"AM_am_w{wk}"].mean(), 2)
            r[f"LSTaqua_w{wk}"] = round(g[f"LST_aqua_w{wk}"].mean(), 2)
        curve.append(r)
    curve = pd.DataFrame(curve)
    curve.to_csv(OUT / "modis_s2_weekly_curve.csv", index=False)
    for pre in ("AM", "LSTaqua"):
        cols = ["year", "burnfrac_quintile", "burnt_frac_mean"] + [c for c in curve if c.startswith(pre + "_w")]
        t = curve[cols].rename(columns=lambda c: c.replace(pre + "_w", ""))
        print(f"\nWeekly mean anomaly, {pre} (columns = week start, days from label):")
        print(t.to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-extract", action="store_true")
    a = ap.parse_args()
    if a.skip_extract:
        df = pd.read_csv(OUT / "modis_s2_pixels.csv")
    else:
        init_ee()
        df = extract()
    evaluate(df)


if __name__ == "__main__":
    main()
