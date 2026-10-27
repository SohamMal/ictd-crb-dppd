"""
Why does the heat-peak rule over-count in the foothill districts? Diagnosis only (2026-10-19)

district_check.py: foothill districts read far above CREAMS (2019 Pathankot 66.7 vs 1.6%, Rupnagar
78.3 vs 11.2%; 2022 till 24 Oct SAS Nagar 34.7 vs 2.5%, Rupnagar 28.9 vs 10.6%). Hypotheses:
  H1 dark shadows read as char: the relaxed mask keeps SCL 2 (dark area) and 7 (unclassified)
  H2 flags on unharvested / green crop (high NDVI at the flagged look)
  H3 points that are not cropland now (WorldCover 2021) or sit on slopes (SRTM)
  H4 heat peaks at odd times (window edge, weak amplitude)
Same rice points as district_check.py (outputs/burn_district/points.csv). Foothill districts vs four
plains districts, 2019 and 2022 (2022 looks counted till 24 Oct, as in the CREAMS comparison).

Run:  python Code/burn/foothill_diag.py
Out:  outputs/burn_district/diag_*.csv
"""

import ee
import numpy as np
import pandas as pd

import labelling_package as lp
from peak_window import LAM, peaks
from transfer_checks import MASKS, ROOT, ee_classifier, indices, init_ee

OUT = ROOT / "outputs" / "burn_district"
FOOT = ["Pathankot", "Rupnagar", "S A S Nagar", "Hoshiarpur", "Gurdaspur", "Shahid Bhagat Singh Nagar"]
PLAINS = ["Sangrur", "Bathinda", "Patiala", "Ludhiana"]
YEARS = {2019: None, 2022: "2022-10-24"}


def looks(pts, year):
    path = OUT / f"diag_looks_{year}.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    sc, m = lp.model()
    clf = ee_classifier(sc, m)
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"loc": r.loc}) for r in pts.itertuples()])
    parts = []
    for start, end in [(f"{year}-09-15", f"{year}-10-15"), (f"{year}-10-15", f"{year}-11-15"), (f"{year}-11-15", f"{year}-12-17")]:
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
               .filterDate(start, end).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))

        def samp(img):
            idx = indices(img, MASKS["relaxed_scl2457"])     # masked off clear classes: those looks drop out
            flag = clf(idx).unmask(-1)
            sr = img.select(["B4", "B8"]).divide(10000)
            ndvi = sr.normalizedDifference(["B8", "B4"]).rename("NDVI")
            stack = img.select("SCL").addBands([flag, ndvi, idx])
            d = img.date().format("YYYY-MM-dd")
            return stack.sampleRegions(collection=fc, scale=20, geometries=False).map(lambda f: f.set("date", d))
        df = ee.data.computeFeatures({"expression": col.map(samp).flatten(), "fileFormat": "PANDAS_DATAFRAME"})
        parts.append(df.drop(columns=["geo"], errors="ignore"))
        print(f"  {year} {start}..{end}: {len(df)} point-looks", flush=True)
    s = pd.concat(parts, ignore_index=True)
    s["date"] = pd.to_datetime(s.date)
    s.to_csv(path, index=False)
    return s


def site(pts):
    path = OUT / "diag_site.csv"
    if path.exists():
        return pd.read_csv(path)
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"loc": r.loc}) for r in pts.itertuples()])
    wc = ee.Image("ESA/WorldCover/v200/2021").select("Map").rename("worldcover")
    slope = ee.Terrain.slope(ee.Image("USGS/SRTMGL1_003")).rename("slope_deg")
    df = ee.data.computeFeatures({"expression": wc.addBands(slope).sampleRegions(collection=fc, scale=10, geometries=False),
                                  "fileFormat": "PANDAS_DATAFRAME"}).drop(columns=["geo"], errors="ignore")
    df.to_csv(path, index=False)
    return df


def main():
    pts = pd.read_csv(OUT / "points.csv")
    pts = pts[pts.district.isin(FOOT + PLAINS)].copy()
    pts["group"] = np.where(pts.district.isin(FOOT), "foothill", "plains")
    init_ee()
    st = site(pts)
    rows, look_rows = [], []
    for year, cut in YEARS.items():
        s = looks(pts, year)
        if cut:
            s = s[s.date <= cut]
        ms = pd.read_csv(OUT / f"modis_{year}.csv", parse_dates=["date"])
        pk = peaks(ms[ms["loc"].isin(pts["loc"])], pts.assign(year=year), LAM)
        s = s.merge(pk[["loc", "peak_date", "peak_anom"]], on="loc", how="left").merge(pts[["loc", "district", "group"]], on="loc")
        s["d"] = (s.date - s.peak_date).dt.days
        clear = s[s.SCL.isin([2, 4, 5, 7]) & (s.burnt_px >= 0)]
        win = clear[(clear.d >= -7) & (clear.d <= 7)]
        fl = win[win.burnt_px == 1]
        # per point: flagged in window, and which SCL class carried its flag(s)
        pt = pts[["loc", "district", "group"]].copy()
        pt["flagged"] = pt["loc"].map(win.groupby("loc").burnt_px.max())
        pt["flag_only_scl2or7"] = pt["loc"].map(fl.groupby("loc").SCL.apply(lambda x: x.isin([2, 7]).all()))
        pt["ndvi_at_flag"] = pt["loc"].map(fl.groupby("loc").NDVI.median())
        pt["looks_season"] = pt["loc"].map(clear.groupby("loc").size())
        pt = pt.merge(pk[["loc", "peak_date", "peak_anom"]], on="loc", how="left").merge(st, on="loc", how="left")
        pt["peak_doy"] = pt.peak_date.dt.dayofyear
        pt["peak_at_edge"] = pt.peak_date.isin([pd.Timestamp(f"{year}-09-15"), pd.Timestamp(f"{year}-11-30")])
        pt["year"] = year
        rows.append(pt)
        # share of all clear looks by SCL, and flag rate per SCL class
        g = clear.groupby(["group", "SCL"]).agg(looks=("burnt_px", "size"), flag_rate=("burnt_px", "mean")).reset_index()
        g["share_of_looks"] = g.looks / g.groupby("group").looks.transform("sum")
        g["year"] = year
        look_rows.append(g)
    P = pd.concat(rows, ignore_index=True)
    P.to_csv(OUT / "diag_points.csv", index=False)
    L = pd.concat(look_rows, ignore_index=True)
    L.to_csv(OUT / "diag_scl.csv", index=False)

    agg = P.groupby(["year", "group"]).agg(
        points=("loc", "size"), flagged=("flagged", "mean"),
        flag_only_dark_scl=("flag_only_scl2or7", "mean"),
        ndvi_at_flag_med=("ndvi_at_flag", "median"),
        flagged_with_ndvi_gt_04=("ndvi_at_flag", lambda x: (x > 0.4).mean() if x.notna().any() else np.nan),
        not_cropland_wc=("worldcover", lambda x: (x != 40).mean()),
        slope_gt_3deg=("slope_deg", lambda x: (x > 3).mean()),
        looks_season_med=("looks_season", "median"),
        peak_doy_med=("peak_doy", "median"), peak_at_edge=("peak_at_edge", "mean"),
        peak_anom_med=("peak_anom", "median")).round(3)
    print("\nBy group (flag stats among flagged points):")
    print(agg.T.to_string())
    print("\nSCL class of clear looks, and flag rate per class:")
    print(L.pivot_table(index=["year", "SCL"], columns="group", values=["share_of_looks", "flag_rate"]).round(3).to_string())
    print("\nFoothill districts:")
    print(P[P.group == "foothill"].groupby(["year", "district"]).agg(
        flagged=("flagged", "mean"), only_dark=("flag_only_scl2or7", "mean"),
        ndvi_flag=("ndvi_at_flag", "median"), not_crop=("worldcover", lambda x: (x != 40).mean()),
        peak_edge=("peak_at_edge", "mean")).round(2).to_string())


if __name__ == "__main__":
    main()
