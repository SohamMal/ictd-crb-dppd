"""
Version X, Stage 3: the main version's 8 online drivers, per village (2026-11-10)

Same hypotheses and sources as Code/predictors/drivers.py (D8 CRM machines dropped there too: no district table).
What changes at village level:
  D1 turnaround   harvest -> estimated wheat sowing (green-up - 28 days; green-up used only if the clear look before
                  it is <= 20 days earlier), per point-season from vx_harvest_gap.py (3 points per village);
                  village value = median over its point-seasons 2020-24. Harvest day of year kept for context
  D2 early crop   share of harvested point-seasons with NDVI >= 0.6 on a clear look after harvest, by 30 Nov [P]
  D3 labour       Census 2011 PCA of the village itself: agricultural labourers per cultivator; cultivators per
                  100 ha of village rice (calibrated Chen 2022) = small-farm proxy
  D4 straw buyers km from the village's rice-point centroid to the nearest biomass / CBG plant (plants placed at the
                  host tehsil's rice-point centroid as in the main version, so this is coarse), plants within 30 km
  D5 border       km to the inter-state and to the international border (SHRUG 2011 district polygons)
  D6 city         km to the nearest GHS-SMOD 2020 urban-centre cell (class 30) and to any urban cell (>= 21);
                  the main version's "urban area share of the tehsil" has no meaning for one village
  D7 basmati      district basmati share 2023 (APEDA) / district rice 2021-22: district value, as before
  D9 livestock    20th Livestock Census 2019 bovines of the village (main-version name match, livestock_match.csv)
                  per Census-2011 cultivator; NaN where the village was not matched

Run:  python version_X/Code/vx_drivers.py   (after vx_harvest_gap.py)
Out:  version_X/outputs/predictors/village_drivers.csv
"""

import sys
import types
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "predictors"))
sys.path.insert(0, str(ROOT / "Code" / "burn"))
sys.modules.setdefault("rasterio", types.ModuleType("rasterio"))
import drivers as dr  # noqa: E402

VX = ROOT / "version_X" / "outputs"
OUT = VX / "predictors"
ID = "c2011_village_code"
YEARS = range(2020, 2025)


def d1_d2():
    p = pd.read_csv(OUT / "harvest_gap" / "point_dates.csv", dtype={ID: str},
                    parse_dates=["harvest", "greenup", "look_before_greenup"])
    p = p[p.year.isin(YEARS) & p.harvest.notna()]
    gap = (p.greenup - p.look_before_greenup).dt.days
    ok = p.greenup.notna() & (gap <= dr.MAX_GREENUP_GAP)
    p["turnaround"] = np.where(ok, (p.greenup - p.harvest).dt.days - dr.GREENUP_LAG, np.nan)
    p["harvest_doy"] = p.harvest.dt.dayofyear
    p["early"] = p.ndvi_by_30nov >= dr.EARLY_NDVI
    return p.groupby(ID).agg(d1_turnaround_days=("turnaround", "median"), d1_harvest_doy=("harvest_doy", "median"),
                             d1_point_seasons=("turnaround", "count"), d2_early_canopy_share=("early", "mean"))


def centroids():
    p = pd.read_csv(VX / "villages" / "points_new.csv", dtype={ID: str}).groupby(ID)[["lon", "lat"]].mean()
    return gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.lon, p.lat), crs="EPSG:4326").to_crs(dr.METRIC)


def d3_d9(vb):
    v = dr.census_villages()
    v = v.drop_duplicates("code").set_index("code")
    rice = vb.set_index(ID).rice_ha_2022_cal
    t = pd.DataFrame(index=v.index)
    t["d3_labourers_per_cultivator"] = v.ag_labourers / v.cultivators.replace(0, np.nan)
    t["d3_cultivators_per_100ha_rice"] = 100 * v.cultivators / rice.reindex(v.index).replace(0, np.nan)
    m = pd.read_csv(ROOT / "outputs" / "predictors" / "drivers" / "livestock_match.csv", dtype={"code": str})
    bov = m.groupby("code").bovines.sum()
    t["d9_bovines_per_cultivator"] = bov.reindex(v.index) / v.cultivators.replace(0, np.nan)
    t["census_population_2011"] = v.TOT_P
    t.index.name = ID
    return t


def d4(c):
    b = pd.read_csv(dr.PRED / "straw_buyers.csv")
    tp = pd.read_csv(ROOT / "outputs" / "burn_tehsil" / "points.csv").groupby("lgd_tehsil_code")[["lon", "lat"]].mean()
    names = pd.read_csv(ROOT / "outputs" / "grouping" / "FROZEN_groups.csv").set_index("lgd_tehsil_name").lgd_tehsil_code
    xy = tp.loc[b.host_tehsil.map(names)]
    sites = gpd.GeoSeries(gpd.points_from_xy(xy.lon, xy.lat), crs="EPSG:4326").to_crs(dr.METRIC)
    sx, sy = sites.x.to_numpy(), sites.y.to_numpy()
    km = np.hypot(c.geometry.x.to_numpy()[:, None] - sx, c.geometry.y.to_numpy()[:, None] - sy) / 1000
    return pd.DataFrame({"d4_buyers_within_30km": (km <= dr.BUYER_KM).sum(axis=1), "d4_km_nearest_buyer": km.min(axis=1)},
                        index=c.index)


def d5(c):
    d = gpd.read_file(dr.DISTRICTS).to_crs(dr.METRIC)
    pb = unary_union(d[d.pc11_s_id == dr.PUNJAB].geometry).buffer(200)
    nb = unary_union(d[d.pc11_s_id.isin(dr.NEIGHBOURS)].geometry).buffer(200)
    edge = pb.boundary
    return pd.DataFrame({"d5_km_interstate_border": c.geometry.distance(edge.intersection(nb)) / 1000,
                         "d5_km_international_border": c.geometry.distance(edge.difference(nb)) / 1000}, index=c.index)


def d6(c):
    cells = dr.smod_cells().to_crs(dr.METRIC)
    out = {}
    for name, cl in [("d6_km_urban_centre", cells.smod == 30), ("d6_km_any_urban", cells.smod >= 21)]:
        s = cells[cl]
        sx, sy = s.geometry.x.to_numpy(), s.geometry.y.to_numpy()
        x, y = c.geometry.x.to_numpy(), c.geometry.y.to_numpy()
        best = np.full(len(x), np.inf)
        for k in range(0, len(sx), 2000):       # chunks keep the distance matrix small
            best = np.minimum(best, np.hypot(x[:, None] - sx[k:k + 2000], y[:, None] - sy[k:k + 2000]).min(axis=1))
        out[name] = best / 1000
    return pd.DataFrame(out, index=c.index)


def d7(vb):
    t = dr.d7_basmati().set_index("lgd_tehsil_code")
    code = vb.set_index(ID).lgd_tehsil_code.astype(int)
    return pd.DataFrame({"d7_basmati_share_district": code.map(t.d7_basmati_share_district),
                         "d7_basmati_row_inconsistent": code.map(t.d7_basmati_row_inconsistent)})


def main():
    vb = pd.read_csv(VX / "villages" / "village_base.csv", dtype={ID: str, "lgd_tehsil_code": str})
    c = centroids()
    parts = [d1_d2(), d3_d9(vb), d4(c), d5(c), d6(c), d7(vb)]
    t = pd.DataFrame(index=c.index)
    for p in parts:
        t = t.join(p, how="left")
    t.round(4).to_csv(OUT / "village_drivers.csv")
    print(t.describe().T.round(3).to_string())
    print("\nmissing share:", t.isna().mean().round(3)[lambda s: s > 0].to_dict())


if __name__ == "__main__":
    main()
