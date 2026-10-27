"""
District-level check of the burn rules against IARI CREAMS official burnt area (2026-10-18)

CREAMS (ICAR-IARI) publishes district-wise paddy area and burnt area for Punjab, estimated from
multi-date satellite images with ground truth (Data/Burning/CREAMS/creams_district_burnt_2018_2020.csv,
parsed from 03_RiceResidue_BurntStatistics_PunHar_2019.pdf and 04_RiceResidue_BurnStatistics_2020.pdf).
It is an independent estimate, not field truth. Tables exist for 2018-2020 only; Sentinel-2 surface
reflectance over Punjab starts in Dec 2018, so the check uses 2019 and 2020. For 2022 only an
in-season table exists (Special Report 3, burnt area till 24 Oct 2022, Wayback copy of KRISHI
handle 123456789/75226); there the rules count only looks up to 24 Oct.

Sample: N_PER random rice pixels per district (Chen et al. 2020 rice map, 10 m; current districts,
Malerkotla merged into Sangrur as in 2019-20). Per point and year:
  S2 flags  pooled relaxed-mask BAIS2+TCB model, every clear look 15 Sep - 16 Dec (20 m)
  MODIS     MYD21A1D LST anomaly vs 30 km focal mean, Whittaker lambda 50, peak 15 Sep - 30 Nov
  rules     season (1 Oct - 15 Dec), official (15 Sep - 30 Nov), peak -7..+7, peak -21..+14
District share = share of sampled points flagged; compared with CREAMS burnt_pct (Spearman,
Pearson, mean bias). Sampling error at N_PER = 120 is about +-4.5 points per district.

Run:  python Code/burn/district_check.py
Out:  outputs/burn_district/*.csv
"""

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import ee
from shapely.geometry import Point

import labelling_package as lp
from peak_window import modis_series, peaks, LAM, WINDOWS
from transfer_checks import MASKS, ROOT, ee_classifier, indices, init_ee

OUT = ROOT / "outputs" / "burn_district"
CREAMS = ROOT / "Data" / "Burning" / "CREAMS" / "creams_district_burnt_2018_2020.csv"
RICE = ROOT / "Data" / "Rice" / "rice_area_output" / "clipped_2020.tif"
TEHSILS = ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg"
CREAMS_2022 = ROOT / "Data" / "Burning" / "CREAMS" / "creams_district_burnt_2022_to24oct.csv"
YEARS = [2019, 2020, 2022]
# 2022: only an in-season official table exists (CREAMS Special Report 3, burnt area till 24 Oct 2022)
CUTOFF = {2022: "2022-10-24"}
N_PER = 120
SEED = 42
CLEAR_SCL = [2, 4, 5, 7]


def sample_points():
    path = OUT / "points.csv"
    if path.exists():
        return pd.read_csv(path)
    t = gpd.read_file(TEHSILS)
    t["district"] = t.district.replace({"Malerkotla": "Sangrur"})
    dist = t.dissolve("district").reset_index()[["district", "geometry"]]
    rng = np.random.default_rng(SEED)
    rows = []
    with rasterio.open(RICE) as r:
        for d in dist.itertuples():
            minx, miny, maxx, maxy = d.geometry.bounds
            got, tries = 0, 0
            while got < N_PER and tries < 200000:
                xs, ys = rng.uniform(minx, maxx, 500), rng.uniform(miny, maxy, 500)
                tries += 500
                vals = np.array([v[0] for v in r.sample(zip(xs, ys))])
                for x, y, v in zip(xs, ys, vals):
                    if v == 1 and d.geometry.contains(Point(x, y)):
                        rows.append({"loc": f"{d.district[:4].upper()}{got:03d}", "district": d.district, "lon": x, "lat": y})
                        got += 1
                        if got == N_PER:
                            break
            print(f"  {d.district}: {got} rice points", flush=True)
    pts = pd.DataFrame(rows)
    pts.to_csv(path, index=False)
    return pts


def s2_series(pts, year):
    path = OUT / f"s2_series_{year}.csv"
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
            stack = img.select("SCL").addBands(clf(indices(img, MASKS["relaxed_scl2457"])).unmask(-1))
            d = img.date().format("YYYY-MM-dd")
            return stack.sampleRegions(collection=fc, scale=20, geometries=False).map(lambda f: f.set("date", d))
        for attempt in range(4):
            try:
                df = ee.data.computeFeatures({"expression": col.map(samp).flatten(), "fileFormat": "PANDAS_DATAFRAME"})
                break
            except Exception as e:
                print(f"    retry {attempt + 1}: {str(e)[:80]}", flush=True)
        else:
            raise RuntimeError("Sentinel-2 extraction failed 4 times")
        print(f"  S2 {year} {start}..{end}: {len(df)} point-looks", flush=True)
        parts.append(df.drop(columns=["geo"], errors="ignore"))
    s = pd.concat(parts, ignore_index=True)
    s["date"] = pd.to_datetime(s.date)
    s = s[s.SCL.isin(CLEAR_SCL) & (s.burnt_px >= 0)]
    s = s.groupby(["loc", "date"], as_index=False).burnt_px.max().rename(columns={"burnt_px": "flag"})
    s.to_csv(path, index=False)
    return s


def point_rules(flags, pk, year):
    f = flags.merge(pk[["loc", "peak_date"]], on="loc", how="left")
    if year in CUTOFF:                      # compare like with like: burns seen by the official cut-off date
        f = f[f.date <= CUTOFF[year]]
    d = (f.date - f.peak_date).dt.days
    sel = {"season": (f.date >= f"{year}-10-01") & (f.date <= f"{year}-12-15"),
           "official": (f.date >= f"{year}-09-15") & (f.date <= f"{year}-11-30")}
    for a, b in WINDOWS:
        sel[f"peak_{a}_{b}"] = (d >= a) & (d <= b)
    out = pd.DataFrame({"loc": flags["loc"].unique()}).set_index("loc")   # all points; NaN = no look before cut-off
    for k, s in sel.items():
        out[k] = f[s].groupby("loc").flag.max()
    return out.reset_index()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pts = sample_points()
    init_ee()
    c22 = pd.read_csv(CREAMS_2022)
    cre = pd.concat([pd.read_csv(CREAMS), pd.DataFrame({"year": 2022, "district": c22.district,
                     "rice_kha": c22.sown_ha / 1000, "burnt_kha": c22.burnt_ha / 1000,
                     "burnt_pct": c22.burnt_pct_of_sown})], ignore_index=True)
    rows, tabs = [], []
    for year in YEARS:
        flags = s2_series(pts, year)
        p = pts.assign(year=year)
        ms = modis_series(p[["loc", "year", "lon", "lat"]], path=OUT / f"modis_{year}.csv")
        pk = peaks(ms, p, LAM)
        res = point_rules(flags, pk, year).merge(pts[["loc", "district"]], on="loc")
        rules = [c for c in res.columns if c not in ("loc", "district")]
        dist = res.groupby("district")[rules].mean().mul(100).round(1)
        dist["n_points"] = res.groupby("district").size()
        dist = dist.join(cre[cre.year == year].set_index("district")[["rice_kha", "burnt_pct"]])
        dist.insert(0, "year", year)
        tabs.append(dist.reset_index())
        for r in rules:
            ok = dist.dropna(subset=[r, "burnt_pct"])
            w = ok.rice_kha / ok.rice_kha.sum()
            rows.append({"year": year, "rule": r, "districts": len(ok),
                         "spearman": round(ok[r].corr(ok.burnt_pct, "spearman"), 3),
                         "pearson": round(ok[r].corr(ok.burnt_pct), 3),
                         "state_ours_pct": round((ok[r] * w).sum(), 1),
                         "state_creams_pct": round((ok.burnt_pct * w).sum(), 1),
                         "mean_abs_diff_pts": round((ok[r] - ok.burnt_pct).abs().mean(), 1)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "district_scores.csv", index=False)
    pd.concat(tabs).to_csv(OUT / "district_table.csv", index=False)
    print("\nDistrict agreement with CREAMS burnt % (state figures weighted by CREAMS rice area):")
    print(t.to_string(index=False))
    for d in tabs:
        print(d[["district", "season", "peak_-7_7", "peak_-21_14", "burnt_pct", "n_points"]].to_string(index=False))


if __name__ == "__main__":
    main()
