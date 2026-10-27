"""
Validate the burn rules at 1 km on CIMMYT survey plots (2026-10-18)

Ground truth: Krishna (2024), CIMMYT, hdl:11529/10548905 (research use, no redistribution).
Plot coordinates are anonymised to 0.01 deg, so each plot is only known to lie in a ~1.1 x 0.96 km
box. Unit = that box ("cell"). Personal columns (farmer name, mobile, enumerator) are never read.

  2021  262 plots, 4 districts; farmer-reported burning of paddy residue (recall), Super Seeder /
        Happy Seeder use, paddy harvest and wheat sowing dates
  2022  426 plots, 8 districts, visited 10-30 Nov 2022; enumerator saw "weeds charred"; tillage class

Per cell:
  survey   share of surveyed plots burnt (2021) / charred (2022)
  rules    share of the cell's cropland (ESA WorldCover 2021 = 40, 20 m) flagged burnt in at least one
           clear Sentinel-2 look within the rule's window (pooled relaxed-mask BAIS2+TCB model):
             season       1 Oct - 15 Dec
             official     15 Sep - 30 Nov
             peak_a_b     MODIS heat peak + [a, b] days (peak_window.py, lambda 50, cell centre)
             farmer       2021 only: cell's earliest harvest - 2 d -> latest sowing + 5 d (best case)
           2022 windows end at the cell's last visit date (later burning was not observable)
Checks: Spearman survey share vs rule share; mean rule share in all-burnt vs all-unburnt cells;
2021: does the MODIS peak fall within the farmers' harvest -> sowing window.

Run:  python Code/burn/cimmyt_cell_validation.py
Out:  outputs/burn_cimmyt/*.csv (local only: cell locations are sensitive)
"""

import ee
import numpy as np
import pandas as pd

import labelling_package as lp
from peak_window import LAM, modis_series, peaks
from transfer_checks import GT_DIR, MASKS, ROOT, ee_classifier, indices, init_ee

SRC = GT_DIR / "CIMMYT" / "extracted"
OUT = ROOT / "outputs" / "burn_cimmyt"
HALF = 0.005
PEAK_WINDOWS = [(-7, 7), (-21, 14)]


# ---------------------------------------------------------------- survey -> cells
def plots():
    a = pd.read_excel(SRC / "Punjab_plot_owner_2021 No PII.xlsx", "Main sheet",
                      usecols=["Farmer_id", "District_name", "Burnt_kha_resi_in_Plot", "Plot_used_sup_seeder",
                               "Plot_used_hs", "Date_harvesting_kha", "Wheat_sowing_date", "Interview_date",
                               "Plot_GPS_centre_gps_Lat", "Plot_GPS_center_gps_Long"])
    a = pd.DataFrame({"year": 2021, "district": a.District_name, "lat": a.Plot_GPS_centre_gps_Lat,
                      "lon": a.Plot_GPS_center_gps_Long,
                      "burnt": a.Burnt_kha_resi_in_Plot.where(a.Burnt_kha_resi_in_Plot.isin([0, 1])),
                      "machine": np.where(a.Plot_used_sup_seeder == 1, "SS", np.where(a.Plot_used_hs == 1, "HS", "none")),
                      "harvest": pd.to_datetime(a.Date_harvesting_kha), "sowing": pd.to_datetime(a.Wheat_sowing_date),
                      "visit": pd.to_datetime(a.Interview_date)})

    def norm(c):
        return c.replace(" ", "")
    want = ["District_name", "Date_interview", "Plot_observations", "Till_Category_Wheat_2022",
            "Inside_plot_GPS_Lat", "Inside_plot_GPS_Long"]
    b = pd.read_excel(SRC / "Punjab_Plot_Owner_2022 No PII.xlsx", "Main_data", usecols=lambda c: norm(c) in want)
    b.columns = [norm(c) for c in b.columns]
    obs = b.Plot_observations.fillna("").str.lower()
    b = pd.DataFrame({"year": 2022, "district": b.District_name, "lat": b.Inside_plot_GPS_Lat,
                      "lon": b.Inside_plot_GPS_Long, "burnt": np.where(obs == "", np.nan, obs.str.contains("charred")),
                      "machine": b.Till_Category_Wheat_2022.fillna("").str.split("_").str[0],
                      "visit": pd.to_datetime(b.Date_interview)})
    p = pd.concat([a, b], ignore_index=True).dropna(subset=["lat", "lon"])
    p["cell"] = p.year.astype(str) + "_" + p.lat.round(2).astype(str) + "_" + p.lon.round(2).astype(str)
    return p


def cells(p):
    g = p.groupby("cell")
    c = g.agg(year=("year", "first"), district=("district", "first"), lat=("lat", "first"), lon=("lon", "first"),
              n_plots=("burnt", "count"), survey_burnt=("burnt", "mean"),
              harvest_min=("harvest", "min"), sowing_max=("sowing", "max"), visit_max=("visit", "max")).reset_index()
    unb_mach = p[(p.burnt == 0) & p.machine.isin(["SS", "HS"])].groupby("cell").size()
    c["n_unburnt_SS_HS"] = c.cell.map(unb_mach).fillna(0).astype(int)
    return c


# ---------------------------------------------------------------- rule shares per cell (Earth Engine)
def windows(c, pk):
    c = c.merge(pk.rename(columns={"loc": "cell"})[["cell", "peak_date"]], on="cell", how="left")
    w = []
    for r in c.itertuples():
        y = r.year
        end_cap = r.visit_max if y == 2022 else pd.Timestamp(f"{y}-12-31")
        spec = {"season": (pd.Timestamp(f"{y}-10-01"), pd.Timestamp(f"{y}-12-15")),
                "official": (pd.Timestamp(f"{y}-09-15"), pd.Timestamp(f"{y}-11-30"))}
        if pd.notna(r.peak_date):
            for a, b in PEAK_WINDOWS:
                spec[f"peak_{a}_{b}"] = (r.peak_date + pd.Timedelta(days=a), r.peak_date + pd.Timedelta(days=b))
        if y == 2021:
            spec["farmer"] = (r.harvest_min - pd.Timedelta(days=2), r.sowing_max + pd.Timedelta(days=5))
        for name, (s, e) in spec.items():
            e = min(e, end_cap)
            if e > s:
                w.append({"cell": r.cell, "year": y, "lat": r.lat, "lon": r.lon, "rule": name,
                          "start": str(s.date()), "end": str((e + pd.Timedelta(days=1)).date())})
    return c, pd.DataFrame(w)


def rule_shares(w):
    path = OUT / "cell_rule_shares.csv"
    if path.exists():
        return pd.read_csv(path)
    sc, m = lp.model()
    clf = ee_classifier(sc, m)
    crop = ee.Image("ESA/WorldCover/v200/2021").select("Map").eq(40)
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))

    def one(f):
        geom = f.geometry()
        col = (s2.filterBounds(geom).filterDate(f.get("start"), f.get("end"))
               .map(lambda img: clf(indices(img, MASKS["relaxed_scl2457"])).toByte()))
        empty = ee.Image.constant(0).toByte().rename("burnt_px").updateMask(0)   # window with no image
        anyflag = ee.Image(ee.Algorithms.If(col.size().gt(0), col.max(), empty)).updateMask(crop)  # any clear look flagged
        st = anyflag.reduceRegion(ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True),
                                  geom, 20, maxPixels=1e8, tileScale=4)
        return f.set({"share": st.get("burnt_px_mean"), "pixels": st.get("burnt_px_count"),
                      "images": col.size()})

    parts = []
    for k in range(0, len(w), 150):
        chunk = w.iloc[k:k + 150]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Rectangle([r.lon - HALF, r.lat - HALF, r.lon + HALF, r.lat + HALF]),
                                              {"cell": r.cell, "rule": r.rule, "start": r.start, "end": r.end})
                                   for r in chunk.itertuples()])
        df = ee.data.computeFeatures({"expression": fc.map(one), "fileFormat": "PANDAS_DATAFRAME"})
        parts.append(df.drop(columns=["geo"], errors="ignore"))
        print(f"  rule shares {k + len(chunk)}/{len(w)}", flush=True)
    res = pd.concat(parts, ignore_index=True)
    res.to_csv(path, index=False)
    return res


# ---------------------------------------------------------------- evaluation
def evaluate(c, rs):
    wide = rs.pivot_table(index="cell", columns="rule", values="share").reset_index()
    d = c.merge(wide, on="cell", how="left")
    d.to_csv(OUT / "cell_table.csv", index=False)
    rules = [r for r in ["season", "official"] + [f"peak_{a}_{b}" for a, b in PEAK_WINDOWS] + ["farmer"] if r in d]
    rows = []
    for year, g in d.groupby("year"):
        g = g[g.n_plots >= 1]
        allb, allu = g[g.survey_burnt == 1], g[g.survey_burnt == 0]
        mach = g[(g.survey_burnt == 0) & (g.n_unburnt_SS_HS >= 1)]
        multi = g[g.n_plots >= 3]
        for r in rules:
            if g[r].notna().sum() == 0:
                continue
            rows.append({"year": year, "rule": r, "cells": int(g[r].notna().sum()),
                         "mean_flagged_share": round(g[r].mean(), 3),
                         "survey_burnt_share": round(g.survey_burnt.mean(), 3),
                         "rho_all": round(g.survey_burnt.corr(g[r], "spearman"), 3),
                         "rho_cells_3plus_plots": round(multi.survey_burnt.corr(multi[r], "spearman"), 3) if len(multi) > 5 else np.nan,
                         "flagged_in_all_burnt_cells": round(allb[r].mean(), 3),
                         "flagged_in_all_unburnt_cells": round(allu[r].mean(), 3),
                         "flagged_in_unburnt_SS_HS_cells": round(mach[r].mean(), 3),
                         "n_all_burnt": len(allb), "n_all_unburnt": len(allu), "n_unburnt_SS_HS": len(mach)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "cell_rule_scores.csv", index=False)
    print("\nCell-level scores (share = cropland share of the 1 km cell flagged burnt):")
    print(t.to_string(index=False))

    a = d[(d.year == 2021) & d.peak_date.notna()].copy()
    a["peak_in_window"] = (a.peak_date >= a.harvest_min - pd.Timedelta(days=7)) & (a.peak_date <= a.sowing_max + pd.Timedelta(days=7))
    a["peak_minus_harvest"] = (a.peak_date - a.harvest_min).dt.days
    a["grp"] = pd.cut(a.survey_burnt, [-0.01, 0.0, 0.99, 1.0], labels=["none burnt", "some burnt", "all burnt"])
    tab = a.groupby("grp", observed=True).agg(cells=("cell", "size"), peak_in_farmer_window=("peak_in_window", "mean"),
                                              median_peak_minus_first_harvest=("peak_minus_harvest", "median")).round(3)
    tab.to_csv(OUT / "cell_peak_timing.csv")
    print("\n2021: MODIS peak within farmers' harvest -> sowing window (+-7 d):")
    print(tab.to_string())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = plots()
    c = cells(p)
    print("Cells:", c.groupby("year").agg(cells=("cell", "size"), plots=("n_plots", "sum"),
                                          plots_per_cell=("n_plots", "median"), burnt=("survey_burnt", "mean")).round(2).to_dict("index"))
    init_ee()
    ms = modis_series(c.rename(columns={"cell": "loc"})[["loc", "year", "lon", "lat"]], path=OUT / "modis_aqua_anomaly.csv")
    pk = peaks(ms, c.rename(columns={"cell": "loc"}), LAM)
    pk.to_csv(OUT / "cell_peaks.csv", index=False)
    c, w = windows(c, pk)
    rs = rule_shares(w)
    evaluate(c, rs)


if __name__ == "__main__":
    main()
