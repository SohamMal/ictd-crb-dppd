"""
Version X, step 3a: village grouping master (2026-11-10)

Same 5 structural dimensions as the frozen tehsil grouping v4 (2026-10-07), each at the finest resolution the
data has; nothing is a driver and nothing is a burn outcome.

  rice         rice_share_2022_cal   village Chen 2022 rice / village area, x district calibration factor
                                     (vx_villages.py)                                            native: village
  rainfall     monsoon_rainfall_mm   mean monsoon rainfall 2020-25 (Data/Rainfall village file)    native: ~village
  zone         aesr_share_*          share of village area in each NBSS&LUP AESR 2018 zone          native: 1:4M map
  groundwater  extraction_pct_2022   CGWB 2022 stage of extraction of the village's block           native: block
  soil         8 classes             NBSS&LUP soil map unit at the village (Data/Soil Data village file)

Population (the PD population of version X):
  - village in a Central or South-west tehsil (Foothills / Dhar Kalan: burn measure fails, main version 10-23)
  - rice_ha_both >= MIN_RICE_HA (rice in both Chen 2020 and 2022): below that the village has too few rice
    pixels for 10 distinct sample points and too little paddy for burning to matter to an NGO
  - rice, rainfall, groundwater, zone and a soil map unit present (a single missing soil class is allowed)

Run:  python version_X/Code/vx_group_master.py
Out:  version_X/outputs/grouping/village_master.csv
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
VX = ROOT / "version_X" / "outputs"
OUT = VX / "grouping"
D = ROOT / "Data"
MIN_RICE_HA = 25
ZONES = ["14.2", "2.5", "4.1", "9.1"]
SOIL = {"particle_size": "grouping_particle_size", "drainage": "grouping_drainage",
        "soil_texture": "soil_texture_dominant", "soil_depth": "soil_depth_dominant",
        "ph_class": "ph_class_dominant", "salinity": "salinity_dominant",
        "sodicity": "sodicity_dominant", "erosion": "erosion_dominant"}


def aesr_shares(vpoly):
    z = gpd.read_file(D / "AgroClimate Zones" / "AESR" / "punjab_aesr_2018_raw.geojson")
    z = z[z.STATE == "PUNJAB"].to_crs(32643).dissolve(by="aesr_id", as_index=False)[["aesr_id", "geometry"]]
    z = z[z.aesr_id.astype(str).isin(ZONES)]
    v = vpoly.to_crs(32643)
    ov = gpd.overlay(v[["c2011_village_code", "geometry"]], z, how="intersection", keep_geom_type=True)
    ov["a"] = ov.area
    s = ov.pivot_table(index="c2011_village_code", columns="aesr_id", values="a", aggfunc="sum").fillna(0)
    cov = s.sum(axis=1) / v.set_index("c2011_village_code").area.reindex(s.index)
    s = s.div(s.sum(axis=1), axis=0)
    s.columns = [f"aesr_share_{str(c).replace('.', '_')}" for c in s.columns]
    s["aesr_coverage"] = cov
    return s.reset_index()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = {"dtype": {"c2011_village_code": str}}
    b = pd.read_csv(VX / "villages" / "village_base.csv", **s)
    vp = gpd.read_file(VX / "villages" / "village_polygons.gpkg")
    rain = pd.read_csv(D / "Rainfall" / "punjab_village_monsoon_rainfall_2020_2025.csv", **s)[
        ["c2011_village_code", "monsoon_rainfall_mm_2020_2025"]].drop_duplicates("c2011_village_code")
    gw = pd.read_csv(D / "Ground Water" / "punjab_village_groundwater_master_2022_2025.csv", **s)[
        ["c2011_village_code", "groundwater_block", "extraction_stage_pct_2022"]].drop_duplicates("c2011_village_code")
    soil = pd.read_csv(D / "Soil Data" / "punjab_village_soil_master.csv", **s)
    soil = soil[["c2011_village_code"] + list(SOIL.values())].rename(
        columns={v: f"soil_{k}" for k, v in SOIL.items()}).drop_duplicates("c2011_village_code")
    m = (b.merge(rain, on="c2011_village_code", how="left").merge(gw, on="c2011_village_code", how="left")
         .merge(soil, on="c2011_village_code", how="left").merge(aesr_shares(vp), on="c2011_village_code", how="left"))
    m = m.rename(columns={"monsoon_rainfall_mm_2020_2025": "monsoon_rainfall_mm",
                          "extraction_stage_pct_2022": "extraction_pct_2022"})
    for c in [f"aesr_share_{z.replace('.', '_')}" for z in ZONES]:
        if c not in m:
            m[c] = 0.0
    needed = ["rice_share_2022_cal", "monsoon_rainfall_mm", "extraction_pct_2022", "aesr_share_9_1"] + \
             [f"soil_{k}" for k in SOIL]
    m["in_region"] = m.group.isin(["Central", "South-west"])
    m["enough_rice"] = m.rice_ha_both >= MIN_RICE_HA
    m["complete"] = m[needed].notna().all(axis=1)
    m["in_population"] = m.in_region & m.enough_rice & m.complete
    m.round(5).to_csv(OUT / "village_master.csv", index=False)
    r = m[m.in_region]
    print(f"villages {len(m)}; in Central/South-west {len(r)}; rice >= {MIN_RICE_HA} ha {r.enough_rice.sum()}; "
          f"complete {(r.enough_rice & r.complete).sum()}")
    print("missing among region + rice:", r[r.enough_rice][needed].isna().sum()[lambda x: x > 0].to_dict())
    p = m[m.in_population]
    print(f"population {len(p)}; share of region rice kept "
          f"{p.rice_ha_2022_cal.sum() / r.rice_ha_2022_cal.sum():.3f}")
    print(p[["rice_share_2022_cal", "monsoon_rainfall_mm", "extraction_pct_2022", "area_ha", "rice_ha_both"]]
          .describe().round(2).to_string())


if __name__ == "__main__":
    main()
