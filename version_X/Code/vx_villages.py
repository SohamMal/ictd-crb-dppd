"""
Version X, step 1: village base table + burn sample points (2026-11-10)

Version X = the same DPPD pipeline as the main (tehsil) version, but the unit is the Census-2011 village.
Main-version code and outputs are not touched; this folder only reads them.

Unit       c2011 village in the LGD village bridge (Data/LGD/Final Output/village_level_bridge_punjab.csv),
           12,660 unique codes; a 2011 village split into two LGD villages (2 cases) is kept once.
Geometry   SHRUG v2.2 PC11 village polygons (join on village + 2011 sub-district code; all matched).
Rice       recomputed here from the Chen GeoTIFFs (clipped_2020.tif, clipped_2022.tif, 10 m) on current
           village polygons. clipped_2022.tif checked against the India-wide chen_2022.tif (identical,
           vx_chen2022_window.py); Chen 2020 and 2022 agree on 99.2% of pixels, hence the near-identical
           village columns.
           rice_ha_2022_cal = Chen 2022 x the tehsil's district calibration factor (main version, 2026-10-07).
Points     N_NEW random 10 m pixels per village that are rice in BOTH Chen 2020 and 2022 (as the tehsil
           points), only in villages of the PD regions (Central, South-west). Foothills and Dhar Kalan are
           not measured: the main version showed the burn measure fails there (2026-10-19/23).
           The 9,700 main-version tehsil points are reused (their verdicts already exist) and joined to the
           village they fall in.

rasterio is blocked by Windows Application Control, so rasters are read with tifffile and villages are
rasterised with PIL on the raster grid (EPSG:4326, 8.98e-5 deg).

Run:  python version_X/Code/vx_villages.py
Out:  version_X/outputs/villages/village_base.csv, village_polygons.gpkg, points_new.csv, points_old.csv
"""

import site
import sys
from pathlib import Path

sys.path.append(site.getusersitepackages())
import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import tifffile  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
VX = ROOT / "version_X"
OUT = VX / "outputs" / "villages"
RICE = ROOT / "Data" / "Rice" / "rice_area_output"
BRIDGE = ROOT / "Data" / "LGD" / "Final Output" / "village_level_bridge_punjab.csv"
SHRUG = ROOT / "Data" / "Boundaries" / "shrug-pc11-village-poly-shp" / "village_modified.shp"
CAL = RICE / "punjab_tehsil_rice_2022_calibrated.csv"
GROUPS = ROOT / "outputs" / "grouping" / "FROZEN_groups.csv"
OLD_POINTS = ROOT / "outputs" / "burn_tehsil" / "points.csv"
X0, Y0 = 73.88, 32.52
DX, DY = 8.983070561493456e-05, 8.983195608879386e-05
MEASURED_REGIONS = ["Central", "South-west"]
N_NEW = 10
BATCH = 1500
SEED = 7
METRIC = "EPSG:32643"


def villages():
    br = pd.read_csv(BRIDGE, dtype=str).drop_duplicates("c2011_village_code")
    v = gpd.read_file(SHRUG)
    v = v[v.pc11_s_id == "03"]
    g = br.merge(v[["pc11_tv_id", "pc11_sd_id", "geometry"]], left_on=["c2011_village_code", "c2011_tehsil_code"],
                 right_on=["pc11_tv_id", "pc11_sd_id"], how="inner")
    g = gpd.GeoDataFrame(g, geometry="geometry", crs=v.crs)
    grp = pd.read_csv(GROUPS, dtype={"lgd_tehsil_code": str})[["lgd_tehsil_code", "group", "group_2way"]]
    cal = pd.read_csv(CAL, dtype={"lgd_tehsil_code": str})[["lgd_tehsil_code", "calibration_factor"]]
    g = g.merge(grp, on="lgd_tehsil_code", how="left").merge(cal, on="lgd_tehsil_code", how="left")
    g["area_ha"] = g.to_crs(METRIC).area / 1e4
    keep = ["c2011_village_code", "c2011_village_name", "lgd_village_code", "lgd_village_name", "c2011_tehsil_code",
            "lgd_tehsil_code", "lgd_tehsil_name", "lgd_district_name", "group", "group_2way", "calibration_factor",
            "area_ha", "geometry"]
    return g[keep].reset_index(drop=True)


def rings(geom):
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    for p in polys:
        yield np.asarray(p.exterior.coords), [np.asarray(i.coords) for i in p.interiors]


def village_mask(geom, shape):
    minx, miny, maxx, maxy = geom.bounds
    c0, c1 = max(int((minx - X0) / DX) - 1, 0), min(int((maxx - X0) / DX) + 2, shape[1])
    r0, r1 = max(int((Y0 - maxy) / DY) - 1, 0), min(int((Y0 - miny) / DY) + 2, shape[0])
    if c1 <= c0 or r1 <= r0:
        return None
    img = Image.new("L", (c1 - c0, r1 - r0), 0)
    dr = ImageDraw.Draw(img)
    for ext, holes in rings(geom):
        to_px = lambda xy: [((x - X0) / DX - c0, (Y0 - y) / DY - r0) for x, y in xy]  # noqa: E731
        dr.polygon(to_px(ext), fill=1)
        for h in holes:
            dr.polygon(to_px(h), fill=0)
    return (r0, r1, c0, c1), np.asarray(img, dtype=bool)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    v = villages()
    print(f"villages with geometry: {len(v)}", flush=True)
    a20 = tifffile.imread(RICE / "clipped_2020.tif")
    a22 = tifffile.imread(RICE / "clipped_2022.tif")
    rng = np.random.default_rng(SEED)
    rows, pts = [], []
    for i, d in enumerate(v.itertuples()):
        lat = d.geometry.centroid.y
        px_ha = (111320 * np.cos(np.radians(lat)) * DX) * (110574 * DY) / 1e4
        m = village_mask(d.geometry, a20.shape)
        rec = {"c2011_village_code": d.c2011_village_code, "px_ha": px_ha}
        if m is None:
            rows.append(rec)
            continue
        (r0, r1, c0, c1), mk = m
        w20, w22 = a20[r0:r1, c0:c1] == 1, a22[r0:r1, c0:c1] == 1
        both = w20 & w22 & mk
        rec.update(n_px=int(mk.sum()), rice_px_2020=int((w20 & mk).sum()), rice_px_2022=int((w22 & mk).sum()),
                   rice_px_both=int(both.sum()))
        rows.append(rec)
        if d.group in MEASURED_REGIONS and rec["rice_px_both"] > 0:
            rr, cc = np.nonzero(both)
            pick = rng.choice(len(rr), size=min(N_NEW, len(rr)), replace=False)
            for k, j in enumerate(pick):
                pts.append({"loc": f"V{d.c2011_village_code}_{k:02d}", "c2011_village_code": d.c2011_village_code,
                            "lgd_tehsil_code": d.lgd_tehsil_code, "district": d.lgd_district_name,
                            "lon": X0 + (c0 + cc[j] + 0.5) * DX, "lat": Y0 - (r0 + rr[j] + 0.5) * DY})
        if i % 1000 == 0:
            print(f"  {i}/{len(v)}", flush=True)
    r = pd.DataFrame(rows)
    b = v.drop(columns="geometry").merge(r, on="c2011_village_code")
    for c in ["2020", "2022", "both"]:
        b[f"rice_ha_{c}"] = b[f"rice_px_{c}"] * b.px_ha
    b["raster_area_ha"] = b.n_px * b.px_ha
    b["rice_ha_2022_cal"] = b.rice_ha_2022 * b.calibration_factor
    b["rice_share_2022_cal"] = (b.rice_ha_2022_cal / b.area_ha).clip(upper=1)
    b.round(4).to_csv(OUT / "village_base.csv", index=False)
    v[["c2011_village_code", "lgd_tehsil_code", "group", "geometry"]].to_file(OUT / "village_polygons.gpkg")

    p = pd.DataFrame(pts)
    p["batch"] = np.arange(len(p)) // BATCH
    p.to_csv(OUT / "points_new.csv", index=False)

    old = pd.read_csv(OLD_POINTS, dtype={"lgd_tehsil_code": str})
    og = gpd.GeoDataFrame(old, geometry=gpd.points_from_xy(old.lon, old.lat), crs="EPSG:4326")
    j = gpd.sjoin(og, v[["c2011_village_code", "geometry"]], predicate="within", how="left")
    j = j.drop_duplicates("loc")
    j.drop(columns=["geometry", "index_right"]).to_csv(OUT / "points_old.csv", index=False)

    print(f"\nnew points: {len(p)} in {p.c2011_village_code.nunique()} villages, {p.batch.nunique()} batches")
    print(f"old points joined to a village: {j.c2011_village_code.notna().sum()}/{len(j)}")
    print("rice totals (Mha): 2020 %.3f  2022 %.3f  2022 cal %.3f" % (b.rice_ha_2020.sum() / 1e6,
          b.rice_ha_2022.sum() / 1e6, b.rice_ha_2022_cal.sum() / 1e6))
    print("raster area / polygon area (median): %.3f" % (b.raster_area_ha / b.area_ha).median())


if __name__ == "__main__":
    main()
