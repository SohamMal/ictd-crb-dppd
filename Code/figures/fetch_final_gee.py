"""
Earth Engine pulls for the final deck (real imagery, nothing synthetic).

1. Sentinel-2 true-colour thumbnails of four tehsils on one clear November date:
   a Doaba PD (Phagwara) vs a heavy-burning Central ND (Lehra), and
   Abohar (SW PD) vs Guruharsahai (SW ND). Same season, same stretch, same box size.
2. Sentinel-2 acquisition dates over the Jalandhar 2021 CEEW fields (Oct-Nov), to set against the
   PlanetScope days we hold (slide "ash fades before Sentinel-2 comes back").

Run:  python Code/figures/fetch_final_gee.py
Out:  outputs/figures/final/raw/s2_<tehsil>.png, s2_<tehsil>.json, s2_dates_jalandhar_2021.csv
"""
import json
import sys
import urllib.request
from pathlib import Path

import ee
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "burn"))
from transfer_checks import init_ee  # noqa: E402

POLYGONS = ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg"
GT = ROOT / "Code" / "Ground Truth Data" / "partially_completely_burnt_2021_10_29.geojson"
RAW = ROOT / "outputs" / "figures" / "final" / "raw"

TEHSILS = ["Phagwara", "Lehra", "Abohar", "Guruharsahai"]
SEASON = ("2022-10-25", "2022-11-25")  # mid-burning window, a season with good Nov skies
BOX_KM = 6.0
PX = 900


def tehsil_points():
    g = gpd.read_file(POLYGONS)
    name_col = next(c for c in g.columns if "name" in c.lower() and "tehsil" in c.lower())
    g = g[g[name_col].isin(TEHSILS)].to_crs(4326)
    return {r[name_col]: r.geometry.representative_point() for _, r in g.iterrows()}


def clearest(region):
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region)
           .filterDate(*SEASON).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)))

    def score(img):
        scl = img.select("SCL")
        bad = scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10))
        frac = bad.reduceRegion(ee.Reducer.mean(), region, 60).get("SCL")
        return img.set("bad", frac)

    return ee.Image(col.map(score).filter(ee.Filter.lt("bad", 0.02)).sort("system:time_start").first())


def thumbs():
    for name, p in tehsil_points().items():
        pt = ee.Geometry.Point([p.x, p.y])
        region = pt.buffer(BOX_KM * 500).bounds()
        img = clearest(region)
        date = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd").getInfo()
        vis = img.visualize(bands=["B4", "B3", "B2"], min=0, max=2200, gamma=1.3)
        url = vis.getThumbURL({"region": region, "dimensions": PX, "format": "png"})
        out = RAW / f"s2_{name.lower()}.png"
        urllib.request.urlretrieve(url, out)
        (RAW / f"s2_{name.lower()}.json").write_text(json.dumps(
            {"tehsil": name, "date": date, "lon": p.x, "lat": p.y, "box_km": BOX_KM}))
        print(name, date, out.name)


def tehsil_thumbs(names=("Phagwara", "Lehra")):
    """Whole-tehsil true colour in EPSG:4326 with known bounds, so sample points can be overlaid."""
    g = gpd.read_file(POLYGONS).to_crs(4326)
    for name in names:
        geom = g[g["lgd_tehsil_name_current"] == name].geometry.union_all()
        x0, y0, x1, y1 = geom.buffer(0.01).bounds
        region = ee.Geometry.Rectangle([x0, y0, x1, y1], proj="EPSG:4326", geodesic=False)
        # a tehsil can straddle two orbits, so no single date covers it: cloud-masked median of the
        # first half of the burning window instead (stated in the caption)
        def mask(i):
            scl = i.select("SCL")
            return i.updateMask(scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)))
        win = ("2022-10-25", "2022-11-10")
        img = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region).filterDate(*win)
               .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40)).map(mask).median())
        date = f"median {win[0]} to {win[1]}"
        vis = img.visualize(bands=["B4", "B3", "B2"], min=0, max=2200, gamma=1.3)
        url = vis.getThumbURL({"region": region, "dimensions": 1200, "format": "png", "crs": "EPSG:4326"})
        out = RAW / f"tehsil_{name.lower()}.png"
        urllib.request.urlretrieve(url, out)
        (RAW / f"tehsil_{name.lower()}.json").write_text(json.dumps(
            {"tehsil": name, "date": date, "bounds": [x0, y0, x1, y1]}))
        print(name, date, out.name)


def s2_dates():
    fields = gpd.read_file(GT).to_crs(4326)
    c = fields.geometry.union_all().centroid
    region = ee.Geometry.Point([c.x, c.y]).buffer(2000)
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region)
           .filterDate("2021-10-09", "2021-11-19"))

    def info(img):
        scl = img.select("SCL")
        bad = scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10))
        frac = bad.reduceRegion(ee.Reducer.mean(), region, 60).get("SCL")
        return ee.Feature(None, {"date": ee.Date(img.get("system:time_start")).format("YYYY-MM-dd"),
                                 "bad_share": frac})

    rows = col.map(info).getInfo()["features"]
    df = (pd.DataFrame([f["properties"] for f in rows]).groupby("date", as_index=False)["bad_share"].min())
    df["clear"] = df["bad_share"] < 0.1
    df.to_csv(RAW / "s2_dates_jalandhar_2021.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    init_ee()
    thumbs()
    tehsil_thumbs()
    s2_dates()
