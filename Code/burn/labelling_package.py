"""
Build a temporal labelling package: is a "burnt" flag really burning, or ploughed soil?

Check 3 (transfer_checks.py) showed that across a season the BAIS2+TCB model keeps
flagging fields as burnt for > 30 days and flags 94% of harvested-unburnt fields,
probably confusing tilled/irrigated soil with char. CEEW's single-date labels cannot
separate the two, so Soham labels ~60 cropland spots across the 2022 season by eye.

Sampling (season Oct 1 - Dec 15, 2022; frozen groups v4):
  random cropland points (ESA WorldCover 2021 class 40) per group: Central 24, South-west 21,
  Foothills 15; 2/3 drawn from points the model flags burnt at least once, 1/3 never flagged.
For each chosen point: one image per clear date (SCL at the point in 2,4,5,7), 400 m chips in
true colour (B4,B3,B2) and SWIR false colour (B12,B8,B4), centre marked.

Model flags are NOT shown in the tool (blind labelling); they are saved to points_meta.csv.

Run:  python Code/burn/labelling_package.py
Out:  outputs/burn_labelling/label_tool.html  (open in a browser; labels save in the browser,
      "Download CSV" writes burn_labels_2022.csv -> save it into outputs/burn_labelling/)
      outputs/burn_labelling/img/*.png, points_meta.csv, point_series.csv
"""

import io
import json
import random
import time
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from PIL import Image, ImageDraw
from shapely.geometry import Point
from shapely.ops import unary_union

from transfer_checks import MASKS, ROOT, ee_classifier, fit, indices, init_ee

OUT = ROOT / "outputs" / "burn_labelling"
IMG = OUT / "img"
SEASON = ("2022-10-01", "2022-12-16")
TARGET = {"Central": 24, "South-west": 21, "Foothills": 15}
FLAGGED_SHARE = 2 / 3
CANDIDATES_PER_GROUP = 120
CLEAR_SCL = {2, 4, 5, 7}
CHIP_M = 200          # half-width of the chip in metres (400 m box)
FRAME_PX = 160
SEED = 42


def group_geometries():
    frozen = pd.read_csv(ROOT / "outputs" / "grouping" / "FROZEN_groups.csv")
    tehsils = gpd.read_file(ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg")
    tehsils = tehsils.merge(frozen[["lgd_tehsil_code", "group"]], on="lgd_tehsil_code")
    return {g: unary_union(tehsils[tehsils.group == g].geometry).simplify(0.002)
            for g in TARGET}


def random_points(geom, n, rng):
    minx, miny, maxx, maxy = geom.bounds
    pts = []
    while len(pts) < n:
        p = Point(rng.uniform(minx, maxx), rng.uniform(miny, maxy))
        if geom.contains(p):
            pts.append(p)
    return pts


def model():
    df = pd.read_csv(ROOT / "outputs" / "burn_checks" / "check1_field_medians_relaxed_scl2457.csv")
    return fit(df.dropna(subset=["BAIS2", "TCB"]))


def candidate_series(group, geom, pts, clf):
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([p.x, p.y]), {"pid": f"{group[:2].upper()}{i:03d}"})
                               for i, p in enumerate(pts)])
    crop = ee.Image("ESA/WorldCover/v200/2021").select("Map").eq(40).rename("crop")
    on_crop = crop.sampleRegions(collection=fc, scale=10, geometries=True).filter(ee.Filter.eq("crop", 1))
    pts_crop = on_crop.getInfo()["features"]
    print(f"  {group}: {len(pts_crop)}/{len(pts)} candidates on cropland")
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(f["geometry"]["coordinates"]),
                                          {"pid": f["properties"]["pid"]})
                               for f in pts_crop])
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
           .filterDate(*SEASON).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))
    ids = col.aggregate_array("system:index").getInfo()
    print(f"  {group}: {len(ids)} images")
    rows = []
    for iid in ids:
        img = ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + iid)
        stack = img.select("SCL").addBands(clf(indices(img, MASKS["relaxed_scl2457"])).unmask(-1))
        feats = stack.sampleRegions(collection=fc, scale=20, geometries=False).getInfo()["features"]
        for f in feats:
            p = f["properties"]
            rows.append({"pid": p["pid"], "image": iid, "date": iid[:8],
                         "scl": int(p["SCL"]), "flag": int(p["burnt_px"])})
    coords = {f["properties"]["pid"]: f["geometry"]["coordinates"] for f in pts_crop}
    return pd.DataFrame(rows), coords


def clear_series(s):
    """One look per date: keep clear observations, prefer a clear tile when two tiles share a date."""
    s = s[s.scl.isin(CLEAR_SCL) & (s.flag >= 0)]
    return s.sort_values(["date", "image"]).drop_duplicates(["pid", "date"])


def fetch_frames(pid, lon, lat, images):
    region = ee.Geometry.Point([lon, lat]).buffer(CHIP_M).bounds()
    vis = {
        "tc": lambda i: i.visualize(bands=["B4", "B3", "B2"], min=0, max=2500, gamma=1.2),
        "swir": lambda i: i.visualize(bands=["B12", "B8", "B4"], min=0, max=4000),
    }
    paths = {}
    for kind, fn in vis.items():
        col = ee.ImageCollection([fn(ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + iid)) for iid in images])
        names = [f"{pid}_{iid[:8]}_{kind}.png" for iid in images]
        if all((IMG / n).exists() for n in names):  # resume: already downloaded
            for iid, n in zip(images, names):
                paths.setdefault(iid[:8], {})[kind] = f"img/{n}"
            continue
        strip = None
        for attempt in range(5):
            try:
                url = col.getFilmstripThumbURL({"dimensions": FRAME_PX, "region": region, "format": "png"})
                strip = Image.open(io.BytesIO(requests.get(url, timeout=300).content)).convert("RGB")
                break
            except Exception as e:  # dropped connections from the thumbnail server
                print(f"    retry {attempt + 1} for {pid} {kind}: {type(e).__name__}")
                time.sleep(10 * (attempt + 1))
        if strip is None:
            raise RuntimeError(f"Could not fetch frames for {pid} {kind}")
        w, h = strip.size
        n = len(images)
        vertical = h >= w
        step = (h if vertical else w) // n
        for k, iid in enumerate(images):
            box = (0, k * step, w, (k + 1) * step) if vertical else (k * step, 0, (k + 1) * step, h)
            fr = strip.crop(box).resize((FRAME_PX, FRAME_PX), Image.NEAREST)
            d = ImageDraw.Draw(fr)
            c = FRAME_PX // 2
            d.rectangle([c - 9, c - 9, c + 9, c + 9], outline=(255, 0, 255), width=2)
            name = f"{pid}_{iid[:8]}_{kind}.png"
            fr.save(IMG / name)
            paths.setdefault(iid[:8], {})[kind] = f"img/{name}"
    return paths


def main():
    init_ee()
    OUT.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    sc, m = model()
    clf = ee_classifier(sc, m)

    meta_path, series_path = OUT / "points_meta.csv", OUT / "point_series.csv"
    if meta_path.exists() and series_path.exists():
        print("Reusing cached spot selection")
        meta = pd.read_csv(meta_path)
        series = pd.read_csv(series_path, dtype={"date": str})
        chosen = meta.to_dict("records")
    else:
        meta, series, chosen = select_points(rng, clf)
        meta.to_csv(meta_path, index=False)
        series.to_csv(series_path, index=False)
    rng.shuffle(chosen)  # random order in the tool, groups mixed
    order = [c["pid"] for c in chosen]
    build_tool(meta, series, order)


def select_points(rng, clf):
    chosen, all_series = [], []
    for group, geom in group_geometries().items():
        pts = random_points(geom, CANDIDATES_PER_GROUP, rng)
        s, coords = candidate_series(group, geom, pts, clf)
        cs = clear_series(s)
        summ = cs.groupby("pid").agg(looks=("date", "size"), ever_flagged=("flag", "max")).reset_index()
        summ = summ[summ.looks >= 6]
        n_flag = round(TARGET[group] * FLAGGED_SHARE)
        flagged = summ[summ.ever_flagged == 1].pid.tolist()
        never = summ[summ.ever_flagged == 0].pid.tolist()
        rng.shuffle(flagged)
        rng.shuffle(never)
        take = flagged[:n_flag] + never[:TARGET[group] - n_flag]
        if len(take) < TARGET[group]:  # top up from whichever pool has spare points
            spare = [p for p in flagged[n_flag:] + never[TARGET[group] - n_flag:] if p not in take]
            take += spare[:TARGET[group] - len(take)]
        print(f"  {group}: flagged pool {len(flagged)}, never pool {len(never)}, chosen {len(take)}")
        for pid in take:
            chosen.append({"pid": pid, "group": group, "lon": coords[pid][0], "lat": coords[pid][1],
                           "ever_flagged": int(summ.set_index("pid").loc[pid, "ever_flagged"])})
        all_series.append(cs[cs.pid.isin(take)])

    return pd.DataFrame(chosen), pd.concat(all_series, ignore_index=True), chosen


def build_tool(meta, series, order):
    tool_points = []
    for i, pid in enumerate(order, 1):
        row = meta.set_index("pid").loc[pid]
        ps = series[series.pid == pid].sort_values("date")
        frames = fetch_frames(pid, row.lon, row.lat, ps.image.tolist())
        tool_points.append({"pid": pid, "lon": round(row.lon, 6), "lat": round(row.lat, 6),
                            "dates": [{"date": d, **frames[d]} for d in ps.date]})
        print(f"  frames {i}/{len(order)} {pid} ({len(ps)} dates)")

    html = (Path(__file__).parent / "label_tool_template.html").read_text(encoding="utf-8")
    html = html.replace("__POINTS_JSON__", json.dumps(tool_points))
    (OUT / "label_tool.html").write_text(html, encoding="utf-8")
    print(f"\nDone: {len(tool_points)} points -> {OUT / 'label_tool.html'}")


if __name__ == "__main__":
    main()
