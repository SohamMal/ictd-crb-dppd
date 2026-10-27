"""
Branch B (Basma's route): can Sentinel-1 radar tell ploughing from burning? (2026-10-22)

Idea (Basma Albanna, 2026-10-22): BAIS2+TCB flags are dated candidate burns. Take the Sentinel-1
images just before and just after each candidate; a backscatter rise (dVV, dVH, d(VH-VV), dB) means
the soil was roughened by ploughing -> drop; flat or falling -> keep as burn.

Tests
  B1  coverage   S1 GRD IW (VV+VH) acquisitions over Punjab, 15 Sep - 30 Nov, 2019-2022, per
                 relative orbit and pass; revisit gap per orbit at the CEEW sites
  B2  burnt row  CEEW fields (2020-11-10 Sangrur, 2021-10-29 Jalandhar). Candidate date = label
                 date. Same-orbit pair: last image <= label date, first image > label date.
                 Share of burnt fields a "rise" rule would throw out, over a threshold sweep;
                 unburnt (stubble / green) fields as control
  B3  ploughing  same fields, backscatter from 30 d before to 45 d after the label date. Burnt
                 fields are ploughed / sown within ~25 d (char_vs_soil.py "soil" class), so a later
                 rise means S1 can see that ploughing

Field values: mean of linear power over the field shrunk inward by 10 m (edge mixing), back to dB.
Images compared only within one relative orbit (viewing geometry changes backscatter).

Run:  python Code/burn_basma/s1_tests.py [--skip-extract]
Out:  outputs/burn_basma/b1_*.csv, b2_*.csv, b3_*.csv, s1_field_series.csv
"""

import argparse
import sys
from pathlib import Path

import ee
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "burn"))
from transfer_checks import BURNT, LABEL_DATES, ROOT, fields, init_ee, to_df  # noqa: E402

OUT = ROOT / "outputs" / "burn_basma"
PUNJAB_BBOX = [73.85, 29.53, 76.95, 32.52]  # Punjab state
SEASONS = [2019, 2020, 2021, 2022]
THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 3.0]


def s1(region, start, end):
    return (ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(region).filterDate(start, end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")))


def meta(col):
    keys = ["system:time_start", "relativeOrbitNumber_start", "orbitProperties_pass", "platform_number"]
    vals = col.reduceColumns(ee.Reducer.toList(len(keys)), keys).get("list").getInfo()
    df = pd.DataFrame(vals, columns=["t", "orbit", "pass", "platform"])
    df["date"] = pd.to_datetime(df.t, unit="ms").dt.date
    return df.drop(columns="t")


# ---------------------------------------------------------------- B1
def b1():
    rows, gaps = [], []
    for y in SEASONS:
        m = meta(s1(ee.Geometry.Rectangle(PUNJAB_BBOX), f"{y}-09-15", f"{y}-12-01"))
        m["season"] = y
        rows.append(m)
        d = m.drop_duplicates(["orbit", "date"]).sort_values("date")
        for (orb, ps), g in d.groupby(["orbit", "pass"]):
            dd = pd.to_datetime(g.date).diff().dt.days.dropna()
            gaps.append({"season": y, "orbit": orb, "pass": ps, "platforms": "".join(sorted(m[m.orbit == orb].platform.unique())),
                         "dates": len(g), "median_gap_d": dd.median(), "max_gap_d": dd.max()})
    pd.concat(rows).to_csv(OUT / "b1_s1_acquisitions.csv", index=False)
    gp = pd.DataFrame(gaps)
    gp.to_csv(OUT / "b1_revisit_by_orbit.csv", index=False)
    print("\n[B1] S1 IW VV+VH over Punjab, 15 Sep - 30 Nov: per relative orbit")
    print(gp.to_string(index=False))

    # any-orbit revisit at the two CEEW sites (what a pixel actually gets)
    site = []
    for y, (_, label, _) in LABEL_DATES.items():
        pt = fields(y).geometry().centroid(10)
        for season in SEASONS:
            m = meta(s1(pt, f"{season}-09-15", f"{season}-12-01")).drop_duplicates(["orbit", "date"])
            dd = pd.to_datetime(m.sort_values("date").date).diff().dt.days.dropna()
            site.append({"site": f"CEEW {y}", "season": season, "orbits": sorted(m.orbit.unique().tolist()),
                         "dates": len(m), "median_gap_any_orbit_d": dd.median(), "max_gap_any_orbit_d": dd.max()})
    st = pd.DataFrame(site)
    st.to_csv(OUT / "b1_revisit_at_ceew_sites.csv", index=False)
    print("\n[B1] revisit at CEEW sites (any orbit)")
    print(st.to_string(index=False))


# ---------------------------------------------------------------- extraction (B2, B3)
def extract():
    out = []
    for y, (_, label, _) in LABEL_DATES.items():
        fc = fields(y).map(lambda f: f.set("area_m2", f.geometry().area(1))
                           .setGeometry(f.geometry().buffer(-10, 1)))
        fc = fc.filter(ee.Filter.gt("area_m2", 0))
        lab = pd.Timestamp(label)
        col = s1(fc.geometry(), str((lab - pd.Timedelta(days=35)).date()), str((lab + pd.Timedelta(days=50)).date()))

        def per_image(img):
            lin = ee.Image(10).pow(img.select(["VV", "VH"]).divide(10))
            r = lin.reduceRegions(collection=fc, reducer=ee.Reducer.mean().combine(ee.Reducer.count(), None, True),
                                  scale=10, tileScale=4)
            return r.map(lambda f: f.set({"date": img.date().format("YYYY-MM-dd"),
                                          "orbit": img.get("relativeOrbitNumber_start"),
                                          "pass": img.get("orbitProperties_pass")}).setGeometry(None))
        ids = col.aggregate_array("system:index").getInfo()
        df = pd.concat([to_df(per_image(ee.Image(col.filter(ee.Filter.eq("system:index", i)).first())))
                        for i in ids])  # one image per request (5000-element cap)
        df["label_date"] = label
        out.append(df)
        print(f"  {y}: {len(df)} field-looks")
    ts = pd.concat(out)
    ts = ts.dropna(subset=["VV_mean", "VH_mean"])
    ts["VV"] = 10 * np.log10(ts.VV_mean)
    ts["VH"] = 10 * np.log10(ts.VH_mean)
    ts["VH_VV"] = ts.VH - ts.VV
    ts["day"] = (pd.to_datetime(ts.date) - pd.to_datetime(ts.label_date)).dt.days
    ts = ts.rename(columns={"VV_count": "n_px"}).drop(columns=["VV_mean", "VH_mean", "VH_count"], errors="ignore")
    ts.to_csv(OUT / "s1_field_series.csv", index=False)
    return ts


def cls(c):
    return "burnt" if c in BURNT else ("stubble" if c == "unburnt" else "green/golden")


# ---------------------------------------------------------------- B2
def b2(ts):
    ts = ts.drop_duplicates(["year", "field_id", "orbit", "date"])
    rows = []
    for (yr, fid, orb), g in ts.groupby(["year", "field_id", "orbit"]):
        g = g.sort_values("day")
        bef, aft = g[g.day <= 0], g[g.day > 0]
        if bef.empty or aft.empty:
            continue
        b, a = bef.iloc[-1], aft.iloc[0]
        rows.append({"year": yr, "field_id": fid, "orbit": orb, "class": cls(b.field_category),
                     "n_px": b.n_px, "day_before": b.day, "day_after": a.day,
                     "dVV": a.VV - b.VV, "dVH": a.VH - b.VH, "dVHVV": a.VH_VV - b.VH_VV})
    pr = pd.DataFrame(rows)
    pr.to_csv(OUT / "b2_pairs.csv", index=False)

    print("\n[B2] same-orbit pair bracketing the label date: median change (dB) and days")
    print(pr.groupby(["year", "orbit", "class"]).agg(
        n=("field_id", "size"), before=("day_before", "median"), after=("day_after", "median"),
        dVV=("dVV", "median"), dVH=("dVH", "median"), dVHVV=("dVHVV", "median")).round(2).to_string())

    sweep = []
    for t in THRESHOLDS:
        for var in ["dVV", "dVH"]:
            for (yr, c), g in pr.groupby(["year", "class"]):
                sweep.append({"year": yr, "class": c, "rule": f"{var} > +{t} dB",
                              "n_pairs": len(g), "share_called_ploughing": round((g[var] > t).mean(), 3)})
    sw = pd.DataFrame(sweep)
    sw.to_csv(OUT / "b2_threshold_sweep.csv", index=False)
    print("\n[B2] share of field-pairs a rise rule would call 'ploughing' (burnt row = real burns thrown out)")
    print(sw.pivot_table(index="rule", columns=["year", "class"], values="share_called_ploughing").to_string())

    # speckle / noise: spread of change on stable green-unburnt fields and its link with field size
    pr["size_bin"] = pd.cut(pr.n_px, [0, 50, 100, 200, 10_000], labels=["<0.5ha", "0.5-1ha", "1-2ha", ">2ha"])
    noise = pr.groupby(["class", "size_bin"], observed=True).agg(
        n=("field_id", "size"), sd_dVV=("dVV", "std"), sd_dVH=("dVH", "std")).round(2)
    noise.to_csv(OUT / "b2_noise_by_size.csv")
    print("\n[B2] spread of the change by field size (pixels inside field, 10 m)")
    print(noise.to_string())
    return pr


# ---------------------------------------------------------------- B3
def b3(ts):
    ts = ts.drop_duplicates(["year", "field_id", "orbit", "date"]).copy()
    ts["class"] = ts.field_category.map(cls)
    # anomaly vs each field's last image of the same orbit on/before the label date
    base = (ts[ts.day <= 0].sort_values("day").groupby(["year", "field_id", "orbit"]).last()[["VV", "VH", "VH_VV"]]
            .add_suffix("_0"))
    ts = ts.join(base, on=["year", "field_id", "orbit"], how="inner")
    for v in ["VV", "VH", "VH_VV"]:
        ts["d" + v] = ts[v] - ts[v + "_0"]
    ts["week"] = (ts.day // 7) * 7
    curve = ts.groupby(["year", "class", "week"]).agg(n=("field_id", "size"), VV=("VV", "median"), VH=("VH", "median"),
                                                     dVV=("dVV", "median"), dVH=("dVH", "median"),
                                                     dVHVV=("dVH_VV", "median")).round(2)
    curve.to_csv(OUT / "b3_weekly_curve.csv")
    print("\n[B3] weekly median backscatter (dB) and change vs pre-label image, by days from label date")
    print(curve.to_string())

    # per field: was there any rise of >= 1.5 / 3 dB in dVV within +1..+45 d (i.e. later ploughing seen)?
    late = ts[(ts.day > 0)].groupby(["year", "class", "field_id"]).dVV.max()
    rise = late.groupby(["year", "class"]).agg(n="size", rise_1_5=lambda s: round((s > 1.5).mean(), 3),
                                               rise_3=lambda s: round((s > 3).mean(), 3), median_max=lambda s: round(s.median(), 2))
    rise.to_csv(OUT / "b3_later_rise.csv")
    print("\n[B3] fields with a VV rise after the label date (max over +1..+45 d)")
    print(rise.to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-extract", action="store_true")
    ap.add_argument("--only", nargs="*", default=["b1", "b2", "b3"])
    a = ap.parse_args()
    init_ee()
    OUT.mkdir(parents=True, exist_ok=True)
    if "b1" in a.only:
        b1()
    if {"b2", "b3"} & set(a.only):
        ts = pd.read_csv(OUT / "s1_field_series.csv") if a.skip_extract else extract()
        if "b2" in a.only:
            b2(ts)
        if "b3" in a.only:
            b3(ts)


if __name__ == "__main__":
    main()
