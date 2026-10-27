"""
Backup measure vs the in-season official 2022 table (2026-10-19)

CREAMS Special Report 3 gives district burnt area in Punjab till 24 Oct 2022. For a like-with-like
test, VIIRS fire pixel-days (NASA/VIIRS/002/VNP14A1, FireMask >= 7) are summed over 15 Sep - 24 Oct
2022 per district and divided by CREAMS sown area; compared with CREAMS burnt % of sown area.

Run:  python Code/burn/fire_cutoff_2022.py
Out:  outputs/burn_fire/district_fire_2022_to24oct.csv
"""

import geopandas as gpd
import pandas as pd
import ee

from fire_counts import OUT, TEHSILS, VIIRS
from transfer_checks import ROOT, init_ee

CREAMS_2022 = ROOT / "Data" / "Burning" / "CREAMS" / "creams_district_burnt_2022_to24oct.csv"


def main():
    init_ee()
    t = gpd.read_file(TEHSILS).to_crs(4326)
    t["district"] = t.district.replace({"Malerkotla": "Sangrur", "S.A.S Nagar": "S A S Nagar"})
    d = t.dissolve("district").reset_index()[["district", "geometry"]]
    d["geometry"] = d.geometry.simplify(0.0005)
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__), {"district": n})
                               for n, g in zip(d.district, d.geometry)])
    col = ee.ImageCollection(VIIRS).filterDate("2022-09-15", "2022-10-25")
    proj = ee.Image(col.first()).select("FireMask").projection()
    fires = col.map(lambda i: i.select("FireMask").gte(7).rename("fires")).sum()
    df = ee.data.computeFeatures({"expression": fires.reduceRegions(collection=fc, reducer=ee.Reducer.sum().unweighted(),
                                                                    crs=proj, scale=proj.nominalScale()),
                                  "fileFormat": "PANDAS_DATAFRAME"}).drop(columns=["geo"], errors="ignore")
    df = df.rename(columns={"sum": "fires"}).merge(pd.read_csv(CREAMS_2022), on="district")
    df["fires_per_1000ha"] = df.fires / df.sown_ha * 1000
    df.to_csv(OUT / "district_fire_2022_to24oct.csv", index=False)
    print(f"districts {len(df)}, fire pixel-days {df.fires.sum():.0f}")
    print("Spearman fires/1000 ha vs CREAMS burnt % of sown (till 24 Oct 2022):",
          round(df.fires_per_1000ha.corr(df.burnt_pct_of_sown, "spearman"), 3))
    print("Spearman fires/1000 ha vs CREAMS burnt % of harvested:",
          round(df.fires_per_1000ha.corr(df.burnt_pct_of_harvested, "spearman"), 3))


if __name__ == "__main__":
    main()
