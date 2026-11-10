"""
Stage 3 drivers D1-D7, D9 (2026-11-10). D8 (CRM machines / CHCs per district) dropped: no district table online

Plan [C] Soham, 2026-11-10 (all 9 drivers, online data only; task_predictor_data.md). Drivers are possible
causes (transferable), never grouping variables. Seasons 2020-24 (the PD seasons).

  D1 turnaround   harvest -> estimated wheat sowing (days), from harvest_gap.py point dates; a green-up is used
                  only if the clear look before it is <= 20 days earlier (2026-10-24 proposed fix). Tehsil value =
                  median over seasons of the tehsil-season median. Harvest day of year kept for context.
  D2 early crop   share of harvested panel points with NDVI >= 0.6 on a clear look after harvest and by 30 Nov:
                  a full canopy that early is potato / vegetables / fodder, not wheat (sown 1-15 Nov). Proxy [P]
  D3 labour       Census 2011 village PCA (main + marginal workers): agricultural labourers per cultivator, and
                  cultivators per 100 ha of rice (calibrated 2022) as a small-farm proxy. Villages -> current
                  tehsils with the LGD village bridge. Towns not included (village tables only)
  D5 border       km from the tehsil's rice-point centroid to the nearest inter-state border (HR, RJ, HP, J&K,
                  Chandigarh) and to the international border (SHRUG 2011 district polygons)
  D6 city         GHSL settlement model 2020 (JRC GHS-SMOD V2-0, 1 km): km to the nearest urban-centre cell
                  (class 30) and share of tehsil area in urban cells (classes 21-30)
  D4 straw buyers biomass power and CBG plants (Data/Predictors/straw_buyers.csv, one source per plant; town-level
                  only, placed at the host tehsil's rice-point centroid): plants within 30 km and km to the nearest.
                  The biomass list is from 2017 and CBG start years are unknown, so this is a rough proxy [P]
  D7 basmati      district basmati area 2023 (APEDA Basmati Crop Survey 2023 Vol III, satellite + field) / district
                  rice area 2021-22 (Statistical Abstract 2022). Every tehsil gets its district value. APEDA's own
                  table does not add up for some rows (district total vs variety columns); the published district
                  total is used and the row is marked. Malerkotla is pooled with Sangrur (one rice figure)
  D9 livestock    20th Livestock Census 2019, village level (ARTPARK public copy of DAHD data): cattle + buffalo
                  per Census-2011 cultivator, over the villages matched to Census 2011 (same block + hadbast
                  number + name similarity >= 0.6, else unique name + number statewide)

Run:  python Code/predictors/drivers.py
Out:  outputs/predictors/drivers/tehsil_drivers.csv, livestock_match.csv
"""

import glob
import sys
from pathlib import Path

import ee
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "burn"))
from transfer_checks import init_ee  # noqa: E402

OUT = ROOT / "outputs" / "predictors" / "drivers"
HG = ROOT / "outputs" / "predictors" / "harvest_gap"
POINTS = ROOT / "outputs" / "burn_tehsil" / "points.csv"
MASTER = ROOT / "Data" / "punjab_homogeneous_grouping_master_raw_97tehsils.csv"
BRIDGE = ROOT / "Data" / "LGD" / "Final Output" / "village_level_bridge_punjab.csv"
CENSUS = ROOT / "Data" / "census_punjab"
DISTRICTS = ROOT / "Data" / "Boundaries" / "shrug-pc11dist-poly-shp"
TEHSILS = ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg"
YEARS = range(2020, 2025)
GREENUP_LAG = 28
MAX_GREENUP_GAP = 20
EARLY_NDVI, EARLY_BY = 0.6, "11-30"
PRED = ROOT / "Data" / "Predictors"
BUYER_KM = 30
BASMATI_BAD = 0.2     # |district total - variety sum| / total above this = row marked inconsistent
OFFICIAL_RICE = ROOT / "Data" / "Rice" / "official" / "punjab_district_rice_area_2021_22_statabstract2022.csv"
PUNJAB, NEIGHBOURS = "03", ["01", "02", "04", "06", "08"]   # J&K, HP, Chandigarh, Haryana, Rajasthan (pc11)
METRIC = "EPSG:32643"


def season_points():
    pdt = pd.read_csv(HG / "point_dates.csv", parse_dates=["harvest", "greenup"])
    pdt = pdt[pdt.year.isin(YEARS) & pdt.harvest.notna()]
    rows = []
    for y in YEARS:
        s = pd.read_csv(HG / "raw" / f"ndvi_tehsil_{y}.csv", parse_dates=["date"])
        d = s.merge(pdt[pdt.year == y][["loc", "harvest", "greenup"]], on="loc")
        before = d[d.date < d.greenup].groupby("loc").date.max().rename("look_before_greenup")
        after = d[(d.date > d.harvest) & (d.date <= f"{y}-{EARLY_BY}")].groupby("loc").ndvi.max().rename("ndvi_by_30nov")
        rows.append(pd.concat([before, after], axis=1).reset_index().assign(year=y))
    p = pdt.merge(pd.concat(rows), on=["loc", "year"], how="left")
    p["greenup_gap_days"] = (p.greenup - p.look_before_greenup).dt.days
    ok = p.greenup.notna() & (p.greenup_gap_days <= MAX_GREENUP_GAP)
    p["turnaround_days"] = np.where(ok, (p.greenup - p.harvest).dt.days - GREENUP_LAG, np.nan)
    p["harvest_doy"] = p.harvest.dt.dayofyear
    p["early_canopy"] = p.ndvi_by_30nov >= EARLY_NDVI
    return p.merge(pd.read_csv(POINTS)[["loc", "lgd_tehsil_code"]], on="loc")


def d1_d2():
    p = season_points()
    ty = p.groupby(["lgd_tehsil_code", "year"]).agg(
        turnaround=("turnaround_days", "median"), harvest_doy=("harvest_doy", "median"),
        early_canopy=("early_canopy", "mean"), turnaround_n=("turnaround_days", "count"))
    t = ty.groupby("lgd_tehsil_code").agg(
        d1_turnaround_days=("turnaround", "median"), d1_harvest_doy=("harvest_doy", "median"),
        d1_points_used=("turnaround_n", "sum"), d2_early_canopy_share=("early_canopy", "mean"))
    return t.reset_index()


def census_villages():
    x = pd.concat([pd.read_excel(f) for f in sorted(glob.glob(str(CENSUS / "PCA_CDB-03*.xlsx")))])
    blk = x[x.Level == "CD BLOCK"].drop_duplicates(["District", "CD Block"])[["District", "CD Block", "Name"]]
    x = x[x.Level == "VILLAGE"].merge(blk.rename(columns={"Name": "block"}), on=["District", "CD Block"])
    x["code"] = x["Town/Village"].astype(int).astype(str).str.zfill(6)
    x["cultivators"] = x.MAIN_CL_P + x.MARG_CL_P
    x["ag_labourers"] = x.MAIN_AL_P + x.MARG_AL_P
    b = pd.read_csv(BRIDGE, dtype={"c2011_village_code": str}).drop_duplicates("c2011_village_code")
    v = x.merge(b[["c2011_village_code", "lgd_tehsil_code"]], left_on="code", right_on="c2011_village_code")
    print(f"  D3: {len(v)}/{len(x)} census villages matched to a current tehsil")
    return v


def d3_census(v):
    t = v.groupby("lgd_tehsil_code")[["cultivators", "ag_labourers", "TOT_P"]].sum()
    rice = pd.read_csv(MASTER).set_index("lgd_tehsil_code").rice_area_ha_2022_cal
    t["d3_labourers_per_cultivator"] = t.ag_labourers / t.cultivators
    t["d3_cultivators_per_100ha_rice"] = 100 * t.cultivators / rice.reindex(t.index)
    return t[["d3_labourers_per_cultivator", "d3_cultivators_per_100ha_rice"]].reset_index()


def d9_livestock(v):
    from difflib import SequenceMatcher
    l = pd.read_csv(PRED / "livestock" / "all-india-20th-livestock-census.csv", low_memory=False)
    l = l[(l["state.name"] == "Punjab") & (l["location.type"] == "rural")].reset_index(drop=True)
    l["bovines"] = l[[c for c in l if c.startswith(("population.cattle", "population.buffalo"))]].sum(axis=1)

    def num(s):   # hadbast number in brackets at the end of the name
        return s.str.extract(r"\((\d+)\)\s*$")[0]

    def norm(s):
        return s.str.replace(r"\(.*?\)", "", regex=True).str.lower().str.replace(r"[^a-z]", "", regex=True)

    v = v.assign(n=num(v.Name), nm=norm(v.Name), bk=norm(v.block))
    l = l.assign(n=num(l["village.name"]), nm=norm(l["village.name"]), bk=norm(l["block.name"])).reset_index()
    c = l.merge(v[["code", "n", "nm", "bk"]], on=["bk", "n"], suffixes=("", "_c"))
    c["sim"] = [SequenceMatcher(None, a, b).ratio() for a, b in zip(c.nm, c.nm_c)]
    c = c[c.sim >= 0.6].sort_values("sim", ascending=False).drop_duplicates("index").drop_duplicates("code")
    rest = v[~v.code.isin(c.code)].groupby(["nm", "n"]).filter(lambda g: len(g) == 1)
    c2 = l[~l["index"].isin(c["index"])].merge(rest[["code", "nm", "n"]], on=["nm", "n"])
    c2 = c2.drop_duplicates("index").drop_duplicates("code").assign(sim=1.0)
    m = pd.concat([c[["index", "code", "sim"]], c2[["index", "code", "sim"]]]).merge(
        l[["index", "village.name", "block.name", "bovines"]], on="index")
    m.to_csv(OUT / "livestock_match.csv", index=False)
    print(f"  D9: {len(m)}/{len(l)} livestock villages matched ({m.bovines.sum() / l.bovines.sum():.1%} of bovines)")
    mv = v.merge(m[["code", "bovines"]], on="code")
    t = mv.groupby("lgd_tehsil_code").agg(bov=("bovines", "sum"), cult=("cultivators", "sum"))
    share = mv.groupby("lgd_tehsil_code").TOT_P.sum() / v.groupby("lgd_tehsil_code").TOT_P.sum()
    return pd.DataFrame({"lgd_tehsil_code": t.index.to_numpy(),
                         "d9_bovines_per_cultivator": (t.bov / t.cult).to_numpy(),
                         "d9_match_pop_share": share.reindex(t.index).to_numpy()})


def d4_buyers(c):
    b = pd.read_csv(PRED / "straw_buyers.csv")
    names = pd.read_csv(ROOT / "outputs" / "grouping" / "FROZEN_groups.csv").set_index("lgd_tehsil_name").lgd_tehsil_code
    b["lgd_tehsil_code"] = b.host_tehsil.map(names)
    assert b.lgd_tehsil_code.notna().all(), b[b.lgd_tehsil_code.isna()]
    sites = c.loc[b.lgd_tehsil_code].geometry.to_numpy()
    km = np.array([[g.distance(s) / 1000 for s in sites] for g in c.geometry])
    return pd.DataFrame({"lgd_tehsil_code": c.index.to_numpy(),
                         "d4_buyers_within_30km": (km <= BUYER_KM).sum(axis=1),
                         "d4_km_nearest_buyer": km.min(axis=1)})


def d7_basmati():
    b = pd.read_csv(PRED / "basmati_district_2023.csv")
    b["inconsistent"] = (b.basmati_000ha - b.variety_sum_000ha).abs() / b.basmati_000ha > BASMATI_BAD
    b["pool"] = b.lgd_district_name.replace({"Malerkotla": "Sangrur"})
    pool = b.groupby("pool").agg(basmati=("basmati_000ha", "sum"), bad=("inconsistent", "any"))
    rice = pd.read_csv(OFFICIAL_RICE).set_index("district").rice_area_thousand_ha_2021_22
    pool["share"] = pool.basmati / rice.reindex(pool.index)
    g = pd.read_csv(ROOT / "outputs" / "grouping" / "FROZEN_groups.csv")[["lgd_tehsil_code", "lgd_district_name"]]
    g["pool"] = g.lgd_district_name.replace({"Malerkotla": "Sangrur"})
    g = g.merge(pool, left_on="pool", right_index=True, how="left")
    return pd.DataFrame({"lgd_tehsil_code": g.lgd_tehsil_code, "d7_basmati_share_district": g.share,
                         "d7_basmati_row_inconsistent": g.bad})


def centroids():
    p = pd.read_csv(POINTS).groupby("lgd_tehsil_code")[["lon", "lat"]].mean()
    return gpd.GeoDataFrame(p, geometry=[Point(xy) for xy in zip(p.lon, p.lat)], crs="EPSG:4326").to_crs(METRIC)


def d5_border(c):
    d = gpd.read_file(DISTRICTS).to_crs(METRIC)
    pb = unary_union(d[d.pc11_s_id == PUNJAB].geometry).buffer(200)
    nb = unary_union(d[d.pc11_s_id.isin(NEIGHBOURS)].geometry).buffer(200)
    edge = pb.boundary
    inter = edge.intersection(nb)
    intl = edge.difference(nb)
    return pd.DataFrame({"lgd_tehsil_code": c.index.to_numpy(),
                         "d5_km_interstate_border": c.geometry.distance(inter).to_numpy() / 1000,
                         "d5_km_international_border": c.geometry.distance(intl).to_numpy() / 1000})


def smod_cells():
    """GHS-SMOD 2020 cell centres (0.01 deg grid over Punjab + 0.3 deg), cached in raw/."""
    path = OUT / "raw" / "smod_2020_cells.csv"
    if path.exists():
        d = pd.read_csv(path)
        return gpd.GeoDataFrame(d[["smod"]], geometry=gpd.points_from_xy(d.lon, d.lat), crs="EPSG:4326")
    init_ee()
    t = gpd.read_file(TEHSILS)
    w, s, e, n = t.total_bounds + np.array([-0.3, -0.3, 0.3, 0.3])
    step = 0.01
    img = ee.ImageCollection("JRC/GHSL/P2023A/GHS_SMOD_V2-0").filter(ee.Filter.eq("system:index", "2020")).first()
    arr = ee.data.computePixels({
        "expression": img.select("smod_code"),
        "fileFormat": "NUMPY_NDARRAY",
        "grid": {"dimensions": {"width": int((e - w) / step), "height": int((n - s) / step)},
                 "affineTransform": {"scaleX": step, "shearX": 0, "translateX": w,
                                     "shearY": 0, "scaleY": -step, "translateY": n},
                 "crsCode": "EPSG:4326"}})["smod_code"]
    rows, cols = np.indices(arr.shape)
    lon, lat = w + (cols + 0.5) * step, n - (rows + 0.5) * step
    path.parent.mkdir(exist_ok=True)
    pd.DataFrame({"lon": lon.ravel(), "lat": lat.ravel(), "smod": arr.ravel()}).to_csv(path, index=False)
    return gpd.GeoDataFrame({"smod": arr.ravel()}, geometry=gpd.points_from_xy(lon.ravel(), lat.ravel()),
                            crs="EPSG:4326")


def d6_city(c):
    t = gpd.read_file(TEHSILS)
    cells = smod_cells()
    centre = unary_union(cells[cells.smod == 30].to_crs(METRIC).geometry)
    inside = gpd.sjoin(cells, t[["lgd_tehsil_code", "geometry"]], predicate="within")
    share = inside.groupby("lgd_tehsil_code").smod.apply(lambda x: (x >= 21).mean())
    return pd.DataFrame({"lgd_tehsil_code": c.index.to_numpy(), "d6_km_urban_centre": c.geometry.distance(centre).to_numpy() / 1000,
                         "d6_urban_area_share": share.reindex(c.index).to_numpy()})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = centroids()
    t = d1_d2()
    v = census_villages()
    for part in (d3_census(v), d4_buyers(c), d5_border(c), d6_city(c), d7_basmati(), d9_livestock(v)):
        t = t.merge(part, on="lgd_tehsil_code", how="outer")
    t.round(4).to_csv(OUT / "tehsil_drivers.csv", index=False)
    print(t.describe().T.round(3))


if __name__ == "__main__":
    main()
