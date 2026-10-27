"""
Stage 3 predictor: paddy harvest date, wheat green-up date and the turnaround gap per tehsil (2026-10-23)

Hypothesis [P]: a longer gap between paddy harvest and wheat sowing leaves time to manage straw
without fire (the reason farmers cite most, CEEW). The gap is a farmer/variety/policy outcome
(short-duration PR-126, transplanting zones), so it is a driver, never a grouping variable.

Data: Sentinel-2 SR Harmonized NDVI, every clear look (SCL 4/5) 1 Sep - 31 Jan, at a fixed panel of
N_PER rice points per tehsil (first N_PER of outputs/burn_tehsil/points.csv: rice in both Chen
2020 and 2022 maps, so the same fields every season).
Per point and season:
  harvest   first clear look on/after 15 Sep with NDVI < LOW that follows a look with NDVI >= HIGH;
            date = midpoint of the two looks; uncertainty = half the gap between them
  green-up  first clear look after harvest with NDVI >= LOW where the next clear look is also >= LOW
            (sustained re-greening = wheat, or potato/vegetables); none by 31 Jan = no second crop seen
  gap       green-up - harvest (days); turnaround = gap - GREENUP_LAG (harvest -> estimated sowing)
Per tehsil: medians, share of points with a harvest found, share with no green-up.
Validation: CIMMYT 2021 plot survey (reported paddy harvest and wheat sowing dates; 2022 wheat sowing
only). Plots are located only to 0.01 deg cells, so N_CELL rice points are sampled inside each cell
and the cell median is compared with the median reported date.

Run:  python Code/predictors/harvest_gap.py
Out:  outputs/predictors/harvest_gap/*.csv (raw extracts cached in raw/)
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "burn"))
from transfer_checks import GT_DIR, ROOT, init_ee  # noqa: E402

OUT = ROOT / "outputs" / "predictors" / "harvest_gap"
RAW = OUT / "raw"
POINTS = ROOT / "outputs" / "burn_tehsil" / "points.csv"
RICE_DIR = ROOT / "Data" / "Rice" / "rice_area_output"
CIMMYT = GT_DIR / "CIMMYT" / "extracted"
YEARS = range(2019, 2025)
N_PER = 30
N_CELL = 15
HALF = 0.005
BATCH = 1000
WORKERS = 2                            # the burn run is using Earth Engine at the same time
HIGH, LOW = 0.45, 0.30
GREENUP_LAG = 28                       # days from wheat sowing to NDVI >= LOW (CIMMYT 2021: 28, 2022: 27)
CLEAR_SCL = [4, 5]
SEED = 7


def ndvi_series(pts, year, tag):
    """Clear-look NDVI per point, 1 Sep (year) - 31 Jan (year + 1)."""
    path = RAW / f"ndvi_{tag}_{year}.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    months = pd.date_range(f"{year}-09-01", f"{year + 1}-02-01", freq="MS")
    parts = []
    for k in range(0, len(pts), BATCH):
        p = pts.iloc[k:k + BATCH]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"loc": r.loc})
                                   for r in p.itertuples()])
        for start, end in zip(months[:-1], months[1:]):
            col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
                   .filterDate(str(start.date()), str(end.date()))
                   .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))

            def samp(img):
                stack = img.normalizedDifference(["B8", "B4"]).rename("ndvi").addBands(img.select("SCL"))
                d = img.date().format("YYYY-MM-dd")
                return stack.sampleRegions(collection=fc, scale=10, geometries=False).map(lambda f: f.set("date", d))
            for attempt in range(6):
                try:
                    df = ee.data.computeFeatures({"expression": col.map(samp).flatten(),
                                                  "fileFormat": "PANDAS_DATAFRAME"})
                    break
                except Exception as e:
                    print(f"    retry {attempt + 1}: {str(e)[:80]}", flush=True)
                    time.sleep(30 * (attempt + 1))
            else:
                raise RuntimeError("Sentinel-2 extraction failed 6 times")
            print(f"  {tag} {year} {k // BATCH} {start:%Y-%m}: {len(df)} point-looks", flush=True)
            parts.append(df.drop(columns=["geo"], errors="ignore"))
    s = pd.concat(parts, ignore_index=True)
    s["date"] = pd.to_datetime(s.date)
    s = s[s.SCL.isin(CLEAR_SCL)]
    s = s.groupby(["loc", "date"], as_index=False).ndvi.max()      # tile overlaps: same day twice
    s.to_csv(path, index=False)
    return s


def point_dates(s, year):
    """Harvest, green-up and gap per point (NaT/NaN where not found)."""
    rows = []
    start = pd.Timestamp(f"{year}-09-15")
    for loc, d in s.sort_values("date").groupby("loc"):
        dates, v = d["date"].to_numpy(), d["ndvi"].to_numpy()
        harvest = unc = green = None
        for i in range(1, len(v)):
            if dates[i] >= start and v[i] < LOW and v[:i].max() >= HIGH:
                j = np.where(v[:i] >= HIGH)[0][-1]                    # last green look before the drop
                half = (dates[i] - dates[j]) / 2
                harvest, unc = dates[j] + half, half / np.timedelta64(1, "D")
                for m in range(i + 1, len(v) - 1):
                    if v[m] >= LOW and v[m + 1] >= LOW:
                        green = dates[m]
                        break
                break
        rows.append({"loc": loc, "year": year, "harvest": harvest, "harvest_unc_days": unc,
                     "greenup": green, "looks": len(v)})
    r = pd.DataFrame(rows)
    r["harvest"] = pd.to_datetime(r["harvest"])
    r["greenup"] = pd.to_datetime(r["greenup"])
    r["gap_days"] = (r["greenup"] - r["harvest"]).dt.days
    return r


def tehsil_table(res, pts):
    res = res.merge(pts[["loc", "lgd_tehsil_code"]], on="loc")
    jan1 = pd.to_datetime(res["year"].astype(str) + "-01-01")
    res["harvest_doy"] = (res["harvest"] - jan1).dt.days + 1           # day of year of the paddy season
    res["greenup_doy"] = (res["greenup"] - jan1).dt.days + 1           # > 365 = January next year
    g = res.groupby(["lgd_tehsil_code", "year"])
    t = pd.DataFrame({
        "points": g.size(),
        "harvest_found": g.harvest.apply(lambda x: x.notna().mean()),
        "harvest_doy_median": g.harvest_doy.median(),
        "harvest_unc_median": g.harvest_unc_days.median(),
        "greenup_doy_median": g.greenup_doy.median(),
        "gap_days_median": g.gap_days.median(),
        "turnaround_days_median": g.gap_days.median() - GREENUP_LAG,     # harvest -> estimated wheat sowing
        "no_greenup_share": g.apply(lambda d: (d.harvest.notna() & d.greenup.isna()).sum() / max(d.harvest.notna().sum(), 1)),
        "looks_median": g.looks.median(),
    }).reset_index()
    return t


def cimmyt_cells():
    """2021: reported harvest + wheat sowing; 2022: wheat sowing. One row per 0.01 deg cell and year."""
    a = pd.read_excel(CIMMYT / "Punjab_plot_owner_2021 No PII.xlsx", "Main sheet")
    a = pd.DataFrame({"year": 2021, "district": a.District_name, "lat": a.Plot_GPS_centre_gps_Lat,
                      "lon": a.Plot_GPS_center_gps_Long, "rep_harvest": a.Date_harvesting_kha,
                      "rep_wheat_sow": a.Wheat_sowing_date})
    b = pd.read_excel(CIMMYT / "Punjab_Plot_Owner_2022 No PII.xlsx", "Main_data")
    sow = pd.to_datetime(b["Wheat _Sowing_ Date"].astype("Int64").astype(str) + " " + b["Wheat _Sowing_ Month"]
                         + " 2022", format="%d %b %Y", errors="coerce")
    b = pd.DataFrame({"year": 2022, "district": b.District_name, "lat": b.Inside_plot_GPS_Lat,
                      "lon": b.Inside_plot_GPS_Long, "rep_harvest": pd.NaT, "rep_wheat_sow": sow})
    c = pd.concat([a, b]).dropna(subset=["lat", "lon"])
    c["lat"], c["lon"] = c.lat.round(2), c.lon.round(2)
    c["cell"] = c.lat.map("{:.2f}".format) + "_" + c.lon.map("{:.2f}".format)
    return (c.groupby(["year", "cell", "district", "lat", "lon"])
             .agg(plots=("rep_wheat_sow", "size"), rep_harvest=("rep_harvest", "median"),
                  rep_wheat_sow=("rep_wheat_sow", "median")).reset_index())


def cell_points(cells):
    path = OUT / "cimmyt_cell_points.csv"
    if path.exists():
        return pd.read_csv(path)
    rng = np.random.default_rng(SEED)
    rows = []
    u = cells.drop_duplicates("cell")
    with rasterio.open(RICE_DIR / "clipped_2020.tif") as r20, rasterio.open(RICE_DIR / "clipped_2022.tif") as r22:
        for c in u.itertuples():
            xs = rng.uniform(c.lon - HALF, c.lon + HALF, 3000)
            ys = rng.uniform(c.lat - HALF, c.lat + HALF, 3000)
            xy = list(zip(xs, ys))
            rice = (np.array([v[0] for v in r20.sample(xy)]) == 1) & (np.array([v[0] for v in r22.sample(xy)]) == 1)
            for i, (x, y) in enumerate(list(zip(xs[rice], ys[rice]))[:N_CELL]):
                rows.append({"loc": f"C{c.cell}_{i:02d}", "cell": c.cell, "lon": x, "lat": y})
    p = pd.DataFrame(rows)
    p.to_csv(path, index=False)
    return p


def validate():
    cells = cimmyt_cells()
    cp = cell_points(cells)
    out = []
    for y in (2021, 2022):
        r = point_dates(ndvi_series(cp, y, "cimmyt"), y).merge(cp[["loc", "cell"]], on="loc")
        m = r.groupby("cell").agg(sat_harvest=("harvest", "median"), sat_greenup=("greenup", "median"),
                                  found=("harvest", lambda x: x.notna().mean())).reset_index()
        out.append(cells[cells.year == y].merge(m, on="cell"))
    v = pd.concat(out)
    v["harvest_err"] = (v.sat_harvest - v.rep_harvest).dt.days
    v["greenup_minus_sow"] = (v.sat_greenup - v.rep_wheat_sow).dt.days
    v.to_csv(OUT / "cimmyt_validation.csv", index=False)
    for y, d in v.groupby("year"):
        print(f"CIMMYT {y}: cells {len(d)}, plots {d.plots.sum()}")
        if d.rep_harvest.notna().any():
            e = d.harvest_err.dropna()
            print(f"  harvest error (sat - reported) days: median {e.median():.1f}, MAE {e.abs().mean():.1f}, "
                  f"rho {d[['sat_harvest', 'rep_harvest']].dropna().apply(lambda c: c.rank()).corr().iloc[0, 1]:.2f}")
        e = d.greenup_minus_sow.dropna()
        print(f"  green-up - reported wheat sowing days: median {e.median():.1f}, IQR "
              f"{e.quantile(.25):.0f}..{e.quantile(.75):.0f}, rho "
              f"{d[['sat_greenup', 'rep_wheat_sow']].dropna().apply(lambda c: c.rank()).corr().iloc[0, 1]:.2f}")
    return v


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(exist_ok=True)
    init_ee()
    validate()

    pts = pd.read_csv(POINTS)
    pts = pts.groupby("lgd_tehsil_code").head(N_PER).reset_index(drop=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        series = dict(zip(YEARS, ex.map(lambda y: ndvi_series(pts, y, "tehsil"), YEARS)))
    res = pd.concat([point_dates(series[y], y) for y in YEARS], ignore_index=True)
    res.to_csv(OUT / "point_dates.csv", index=False)
    t = tehsil_table(res, pts)
    t.round(3).to_csv(OUT / "tehsil_harvest_gap.csv", index=False)
    print(t.groupby("year")[["harvest_found", "harvest_doy_median", "greenup_doy_median", "gap_days_median",
                             "no_greenup_share"]].median().round(2))


if __name__ == "__main__":
    main()
