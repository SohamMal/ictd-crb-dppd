"""
Backup burning measure: VIIRS active-fire counts per tehsil-season, scaled by rice area (2026-10-18)

Precedent: Dipoppa & Gulzar (2024, Nature) and Khanna, Mahajan & RSA (2025) measure burning with
satellite active-fire detections. Thermal detection, not confused by ploughed soil, but misses small,
short and evening fires (CEEW 2025: 169 burnt fields vs 7 VIIRS detections on two days), so it is a
consistent undercount.

Data: NASA/VIIRS/002/VNP14A1 (Suomi-NPP only, one sensor for all years), daily 1 km, FireMask
7/8/9 = fire (low / nominal / high confidence); MaxFRP in MW (scale 0.1). Season 15 Sep - 30 Nov
(CAQM / ISRO protocol).
Per tehsil and year: fire pixel-days (all confidence; nominal+high), summed MaxFRP, and fire
pixel-days per 1,000 ha rice (Chen et al. rice area: 2018 map for 2019, 2020 map for 2020-21,
2022 map from 2022).
Check: district totals vs CREAMS burnt % (2019, 2020) and vs our heat-peak S2 rule
(outputs/burn_district/district_table.csv).

Run:  python Code/burn/fire_counts.py
Out:  outputs/burn_fire/*.csv
"""

import geopandas as gpd
import pandas as pd
import ee

from transfer_checks import ROOT, init_ee

OUT = ROOT / "outputs" / "burn_fire"
TEHSILS = ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg"
RICE = ROOT / "Data" / "Rice" / "tehsil_rice_punjab_current_2026.csv"
CREAMS = ROOT / "Data" / "Burning" / "CREAMS" / "creams_district_burnt_2018_2020.csv"
OURS = ROOT / "outputs" / "burn_district" / "district_table.csv"
YEARS = range(2019, 2026)
VIIRS = "NASA/VIIRS/002/VNP14A1"


def rice_col(year):
    return "rice_area_ha_2018" if year <= 2019 else "rice_area_ha_2020" if year <= 2021 else "rice_area_ha_2022"


def extract():
    path = OUT / "tehsil_fires.csv"
    if path.exists():
        return pd.read_csv(path)
    t = gpd.read_file(TEHSILS).to_crs(4326)
    t["geometry"] = t.geometry.simplify(0.0005)
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__), {"lgd_tehsil_code": int(c)})
                               for c, g in zip(t.lgd_tehsil_code, t.geometry)])
    rows = []
    for y in YEARS:
        col = ee.ImageCollection(VIIRS).filterDate(f"{y}-09-15", f"{y}-12-01")
        n_days = col.size().getInfo()

        def daily(img):
            m = img.select("FireMask")
            frp = img.select("MaxFRP").multiply(0.1)
            return ee.Image.cat(m.gte(7).rename("fire_all"), m.gte(8).rename("fire_nomhigh"),
                                frp.updateMask(m.gte(7)).unmask(0).rename("frp_mw"))
        proj = ee.Image(col.first()).select("FireMask").projection()
        season = col.map(daily).sum()
        # count native 1 km pixels (pixel centres inside the tehsil)
        red = season.reduceRegions(collection=fc, reducer=ee.Reducer.sum().unweighted(), crs=proj,
                                   scale=proj.nominalScale())
        df = ee.data.computeFeatures({"expression": red, "fileFormat": "PANDAS_DATAFRAME"}).drop(columns=["geo"], errors="ignore")
        df["year"], df["viirs_days"] = y, n_days
        rows.append(df)
        print(f"  {y}: {n_days} VIIRS days, {df.fire_all.sum():.0f} fire pixel-days in Punjab", flush=True)
    df = pd.concat(rows, ignore_index=True)
    df.to_csv(path, index=False)
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    init_ee()
    f = extract()
    rice = pd.read_csv(RICE)
    f = f.merge(rice, on="lgd_tehsil_code", how="left")
    f["rice_ha"] = [r[rice_col(y)] for y, (_, r) in zip(f.year, f.iterrows())]
    f["fires_per_1000ha_rice"] = f.fire_all / f.rice_ha * 1000
    f["frp_per_1000ha_rice"] = f.frp_mw / f.rice_ha * 1000
    f.to_csv(OUT / "tehsil_fire_measure.csv", index=False)
    print("\nPunjab fire pixel-days per season:", f.groupby("year").fire_all.sum().astype(int).to_dict())
    print("Tehsils with rice area:", f.groupby("year").rice_ha.count().to_dict())

    # year-to-year stability of the tehsil ranking
    piv = f.pivot_table(index="lgd_tehsil_code", columns="year", values="fires_per_1000ha_rice")
    print("\nTehsil ranking stability (Spearman between years):")
    print(piv.corr("spearman").round(2).to_string())

    # district check vs CREAMS and vs our S2 heat-peak rule
    f["district"] = f.lgd_district_name.replace({"Malerkotla": "Sangrur", "S.A.S Nagar": "S A S Nagar"})
    d = f.groupby(["year", "district"]).agg(fires=("fire_all", "sum"), frp=("frp_mw", "sum"),
                                            rice_ha=("rice_ha", "sum")).reset_index()
    d["fires_per_1000ha"] = d.fires / d.rice_ha * 1000
    cre = pd.read_csv(CREAMS)
    ours = pd.read_csv(OURS)[["year", "district", "peak_-7_7"]]
    d = d.merge(cre[["year", "district", "burnt_pct"]], on=["year", "district"], how="left").merge(
        ours, on=["year", "district"], how="left")
    d.to_csv(OUT / "district_fire_check.csv", index=False)
    rows = []
    for y, g in d[d.year.isin([2019, 2020])].groupby("year"):
        rows.append({"year": y, "districts": int(g.burnt_pct.notna().sum()),
                     "rho_fires_vs_creams": round(g.fires_per_1000ha.corr(g.burnt_pct, "spearman"), 3),
                     "rho_frp_vs_creams": round((g.frp / g.rice_ha).corr(g.burnt_pct, "spearman"), 3),
                     "rho_peakrule_vs_creams": round(g["peak_-7_7"].corr(g.burnt_pct, "spearman"), 3),
                     "rho_fires_vs_peakrule": round(g.fires_per_1000ha.corr(g["peak_-7_7"], "spearman"), 3)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "district_fire_scores.csv", index=False)
    print("\nDistrict rank agreement (Spearman, 22 districts):")
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
