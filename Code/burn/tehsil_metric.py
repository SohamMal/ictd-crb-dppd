"""
Tehsil burning measure (Branch A): heat-peak window rule per tehsil and year (2026-10-23)

Same rule as validated at district level (district_check.py, 2026-10-18/19), now with a sample
of rice points in every tehsil:
  S2 flags  pooled relaxed-mask BAIS2+TCB model, every clear look 15 Sep - 7 Dec (20 m)
  MODIS     MYD21A1D LST anomaly vs 30 km focal mean, Whittaker lambda 50, peak 15 Sep - 30 Nov
  rule      a point is burnt if any clear look in [peak - 7, peak + 7] is flagged
Points: N_PER random pixels per tehsil that are rice in BOTH the Chen 2020 and 2022 maps. The same
points are used every year (a panel), so year-to-year change is not sampling noise.
Tehsil burnt share = share of points with a clear look in the window that are flagged.
Burnt ha = share x tehsil rice ha (Chen: 2018 map for 2019, 2020 map for 2020-21, 2022 raster
area for 2022+; the 2022 column of tehsil_rice_punjab_current_2026.csv is stale = 2020).

Checks (Foothills are measured; they are only left out of PD identification):
  district  area-weighted sums of tehsils vs CREAMS burnt % (2019, 2020; 2022 till 24 Oct)
  state     all districts, and "plains" = minus Hoshiarpur, Rupnagar, S A S Nagar, Pathankot
  previous  district shares vs the 2026-10-18 district point sample (district_table.csv)

Run:  python Code/burn/tehsil_metric.py
Out:  outputs/burn_tehsil/*.csv (raw extracts cached in outputs/burn_tehsil/raw/)
"""

import time
from concurrent.futures import ThreadPoolExecutor

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import ee

import labelling_package as lp
from peak_window import modis_series, peaks, LAM
from transfer_checks import MASKS, ROOT, ee_classifier, indices, init_ee

OUT = ROOT / "outputs" / "burn_tehsil"
RAW = OUT / "raw"
RICE_DIR = ROOT / "Data" / "Rice" / "rice_area_output"
TEHSILS = RICE_DIR / "punjab_current_tehsils_lgd.gpkg"
RICE_HA = ROOT / "Data" / "Rice" / "tehsil_rice_punjab_current_2026.csv"
RICE_HA_2022 = RICE_DIR / "punjab_current_tehsil_rice_2022.csv"
GROUPS = ROOT / "outputs" / "grouping" / "FROZEN_groups.csv"
CREAMS = ROOT / "Data" / "Burning" / "CREAMS" / "creams_district_burnt_2018_2020.csv"
CREAMS_2022 = ROOT / "Data" / "Burning" / "CREAMS" / "creams_district_burnt_2022_to24oct.csv"
PREV = ROOT / "outputs" / "burn_district" / "district_table.csv"
YEARS = range(2019, 2025)
CUTOFF = {2022: "2022-10-24"}          # official 2022 table is in-season (burnt area till 24 Oct)
FOOTHILL_DISTRICTS = ["Hoshiarpur", "Rupnagar", "S A S Nagar", "Pathankot"]
WINDOW = (-7, 7)
N_PER = 100
BATCH = 1500
WORKERS = 6                            # parallel Earth Engine requests (one per year x batch)
SEED = 42
CLEAR_SCL = [2, 4, 5, 7]


def sample_points():
    path = OUT / "points.csv"
    if path.exists():
        return pd.read_csv(path)
    t = gpd.read_file(TEHSILS)
    rng = np.random.default_rng(SEED)
    rows = []
    with rasterio.open(RICE_DIR / "clipped_2020.tif") as r20, rasterio.open(RICE_DIR / "clipped_2022.tif") as r22:
        for d in t.sort_values("lgd_tehsil_code").itertuples():
            minx, miny, maxx, maxy = d.geometry.bounds
            got, tries = [], 0
            while len(got) < N_PER and tries < 400000:
                xs, ys = rng.uniform(minx, maxx, 1000), rng.uniform(miny, maxy, 1000)
                tries += 1000
                xy = list(zip(xs, ys))
                rice = (np.array([v[0] for v in r20.sample(xy)]) == 1) & (np.array([v[0] for v in r22.sample(xy)]) == 1)
                cand = gpd.GeoSeries(gpd.points_from_xy(xs[rice], ys[rice]))
                inside = cand[cand.within(d.geometry)]
                got.extend(list(inside)[:N_PER - len(got)])
            rows += [{"loc": f"T{d.lgd_tehsil_code}_{i:03d}", "lgd_tehsil_code": d.lgd_tehsil_code,
                      "district": d.district, "lon": p.x, "lat": p.y} for i, p in enumerate(got)]
            print(f"  {d.lgd_tehsil_code} {d.district}: {len(got)} rice points", flush=True)
    pts = pd.DataFrame(rows)
    pts["batch"] = np.arange(len(pts)) // BATCH
    pts.to_csv(path, index=False)
    return pts


def s2_series(pts, year, batch, clf):
    path = RAW / f"s2_{year}_b{batch}.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"loc": r.loc}) for r in pts.itertuples()])
    parts = []
    for start, end in [(f"{year}-09-15", f"{year}-10-15"), (f"{year}-10-15", f"{year}-11-15"), (f"{year}-11-15", f"{year}-12-08")]:
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
               .filterDate(start, end).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))

        def samp(img):
            stack = img.select("SCL").addBands(clf(indices(img, MASKS["relaxed_scl2457"])).unmask(-1))
            d = img.date().format("YYYY-MM-dd")
            return stack.sampleRegions(collection=fc, scale=20, geometries=False).map(lambda f: f.set("date", d))
        for attempt in range(6):
            try:
                df = ee.data.computeFeatures({"expression": col.map(samp).flatten(), "fileFormat": "PANDAS_DATAFRAME"})
                break
            except Exception as e:
                print(f"    retry {attempt + 1}: {str(e)[:80]}", flush=True)
                time.sleep(30 * (attempt + 1))
        else:
            raise RuntimeError("Sentinel-2 extraction failed 6 times")
        print(f"  S2 {year} b{batch} {start}..{end}: {len(df)} point-looks", flush=True)
        parts.append(df.drop(columns=["geo"], errors="ignore"))
    s = pd.concat(parts, ignore_index=True)
    s["date"] = pd.to_datetime(s.date)
    s = s[s.SCL.isin(CLEAR_SCL) & (s.burnt_px >= 0)]
    s = s.groupby(["loc", "date"], as_index=False).burnt_px.max().rename(columns={"burnt_px": "flag"})
    s.to_csv(path, index=False)
    return s


def point_burnt(flags, pk, locs, cutoff=None):
    """1/0 per point; NaN = no clear look in the peak window (or no MODIS peak)."""
    f = flags.merge(pk[["loc", "peak_date"]], on="loc")
    if cutoff:
        f = f[f.date <= cutoff]
    d = (f.date - f.peak_date).dt.days
    w = f[(d >= WINDOW[0]) & (d <= WINDOW[1])]
    return w.groupby("loc").flag.max().reindex(locs)


def year_points(pts, year, clf):
    path = RAW / f"points_{year}.csv"
    if path.exists():
        return pd.read_csv(path)
    out = []
    for b, p in pts.groupby("batch"):
        flags = s2_series(p, year, b, clf)
        ms = modis_series(p.assign(year=year)[["loc", "year", "lon", "lat"]], path=RAW / f"modis_{year}_b{b}.csv")
        pk = peaks(ms, p.assign(year=year), LAM)
        r = pd.DataFrame({"loc": p["loc"].values, "year": year})
        r["burnt"] = point_burnt(flags, pk, p["loc"]).values
        if year in CUTOFF:
            r["burnt_cutoff"] = point_burnt(flags, pk, p["loc"], CUTOFF[year]).values
        r = r.merge(pk[["loc", "peak_date", "peak_anom"]], on="loc", how="left")
        out.append(r)
    res = pd.concat(out, ignore_index=True)
    res.to_csv(path, index=False)
    return res


def rice_ha():
    r = pd.read_csv(RICE_HA)
    r22 = pd.read_csv(RICE_HA_2022)[["lgd_tehsil_code", "chen_rice_area_ha_2022"]]
    r = r.merge(r22, on="lgd_tehsil_code", how="left")
    rows = []
    for y in YEARS:
        col = "rice_area_ha_2018" if y <= 2019 else "rice_area_ha_2020" if y <= 2021 else "chen_rice_area_ha_2022"
        rows.append(pd.DataFrame({"lgd_tehsil_code": r.lgd_tehsil_code, "year": y, "rice_ha": r[col]}))
    return pd.concat(rows, ignore_index=True)


def tehsil_table(res, pts, col="burnt"):
    d = res.merge(pts[["loc", "lgd_tehsil_code", "district"]], on="loc")
    g = d.groupby(["year", "lgd_tehsil_code", "district"])
    t = g[col].agg(burnt_share="mean", n_look="count").reset_index()
    t["n_points"] = g.size().values
    t["se"] = np.sqrt(t.burnt_share * (1 - t.burnt_share) / t.n_look)
    t = t.merge(rice_ha(), on=["lgd_tehsil_code", "year"], how="left")
    t["burnt_ha"] = t.burnt_share * t.rice_ha
    return t


def creams():
    c22 = pd.read_csv(CREAMS_2022)
    c = pd.concat([pd.read_csv(CREAMS), pd.DataFrame({"year": 2022, "district": c22.district,
                   "rice_kha": c22.sown_ha / 1000, "burnt_kha": c22.burnt_ha / 1000})], ignore_index=True)
    return c[["year", "district", "rice_kha", "burnt_kha"]]


def checks(tt):
    """tt: tehsil table used for validation (2022 = cut-off version)."""
    t = tt.assign(district=tt.district.replace({"Malerkotla": "Sangrur"}))   # CREAMS predates Malerkotla
    dist = t.groupby(["year", "district"])[["burnt_ha", "rice_ha"]].sum().reset_index()
    dist["ours_pct"] = 100 * dist.burnt_ha / dist.rice_ha
    cr = creams()
    dist = dist.merge(cr, on=["year", "district"], how="inner")
    dist["creams_pct"] = 100 * dist.burnt_kha / dist.rice_kha
    prev = pd.read_csv(PREV)[["year", "district", "peak_-7_7"]].rename(columns={"peak_-7_7": "district_sample_pct"})
    dist = dist.merge(prev, on=["year", "district"], how="left")
    rows = []
    for y, g in dist.groupby("year"):
        for scope, s in [("all districts", g), ("plains (no foothill districts)", g[~g.district.isin(FOOTHILL_DISTRICTS)])]:
            rows.append({"year": y, "scope": scope, "districts": len(s),
                         "state_ours_pct": round(100 * s.burnt_ha.sum() / s.rice_ha.sum(), 1),
                         "state_creams_pct": round(100 * s.burnt_kha.sum() / s.rice_kha.sum(), 1),
                         "spearman": round(s.ours_pct.corr(s.creams_pct, "spearman"), 3),
                         "pearson": round(s.ours_pct.corr(s.creams_pct), 3),
                         "mean_abs_diff_pts": round((s.ours_pct - s.creams_pct).abs().mean(), 1),
                         "rho_vs_district_sample": round(s.ours_pct.corr(s.district_sample_pct, "spearman"), 3)})
    return dist.round(2), pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    pts = sample_points()
    init_ee()
    sc, m = lp.model()
    clf = ee_classifier(sc, m)

    def fetch(job):
        y, b = job
        p = pts[pts.batch == b]
        s2_series(p, y, b, clf)
        for attempt in range(6):          # peak_window.modis_series has no retry of its own
            try:
                modis_series(p.assign(year=y)[["loc", "year", "lon", "lat"]], path=RAW / f"modis_{y}_b{b}.csv")
                break
            except Exception as e:
                print(f"    MODIS {y} b{b} retry {attempt + 1}: {str(e)[:80]}", flush=True)
                time.sleep(30 * (attempt + 1))
        else:
            raise RuntimeError(f"MODIS extraction {y} b{b} failed 6 times")
        print(f"== done {y} b{b}", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(fetch, [(y, b) for y in YEARS for b in sorted(pts.batch.unique())]))
    res = pd.concat([year_points(pts, y, clf) for y in YEARS], ignore_index=True)

    grp = pd.read_csv(GROUPS)[["lgd_tehsil_code", "lgd_tehsil_name", "group"]]
    tt = tehsil_table(res, pts).merge(grp, on="lgd_tehsil_code", how="left")
    tt["in_pd_identification"] = tt.group.isin(["Central", "South-west"])
    tt.round(4).to_csv(OUT / "tehsil_burn_measure.csv", index=False)

    val = tt.copy()
    cut = tehsil_table(res[res.year.isin(CUTOFF)], pts, "burnt_cutoff")
    val = pd.concat([val[~val.year.isin(CUTOFF)], cut], ignore_index=True)
    dist, scores = checks(val)
    dist.to_csv(OUT / "district_from_tehsils.csv", index=False)
    scores.to_csv(OUT / "aggregation_checks.csv", index=False)

    print("\nPoints per tehsil with a clear look in the window (median, min) by year:")
    print(tt.groupby("year").n_look.agg(["median", "min"]).to_string())
    print("\nState and district checks vs CREAMS (2022 = till 24 Oct):")
    print(scores.to_string(index=False))
    print("\nArea-weighted burnt % by group and year:")
    gy = tt.groupby(["year", "group"])[["burnt_ha", "rice_ha"]].sum()
    print((100 * gy.burnt_ha / gy.rice_ha).round(1).unstack().to_string())


if __name__ == "__main__":
    main()
