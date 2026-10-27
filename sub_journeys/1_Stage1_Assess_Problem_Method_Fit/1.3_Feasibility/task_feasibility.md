# Feasibility — data, skills, time
**DPPD position:** Stage 1 › Feasibility · **Status:** Done; scope revised several times · **Last updated:** 2026-10-06

## In plain words
Can one student finish this in a semester with free, public data? Mostly yes. Satellite imagery (Sentinel-2) and Google Earth Engine are free, and the structural data (rainfall, soil, groundwater, rice maps, boundaries) is public. The hard parts were (1) matching old 2011 village and tehsil codes to today's codes, and (2) time. To keep the work manageable we narrowed to Punjab only and fixed some data to a single year (2022).

## Technical summary
- **Data feasibility:** all inputs are public. Sentinel-2 SR Harmonized and Sentinel-1 (GEE project `ictd-507010`); CHIRPS; Chen et al. (2024) 10 m paddy maps; NBSS&LUP Bhoomi soil (WFS/WMS); CGWB 2022 / PWRDA 2025 groundwater; SHRUG v2.2 boundaries; LGD directory; Punjab Statistical Abstracts.
- **Main data risks found:** 2011-vs-current ID mismatch; stale 2022 rice column in village CSV; district-only resolution for agro-climatic zones and CRM data; Haryana datasets incomplete.
- **Skills:** Python (geopandas, rasterio), GEE (JS + Python API), basic statistics. Deep-learning approach dropped in A1.
- **Time:** whole project to finish by end of 22 Oct 2026 (`docs/DAY_PLAN.md`).

## Log (append-only, chronological)
### Early Sep 2026 — A1 feasibility (reconstructed)
**Plain:** The first plan used only public data at district level, with a two-person team and a one-month timeline.
**Technical:** A1 §4: FIRMS, Agriculture Census, Agmarknet, CGWB, CRM scheme data. CRM data district-only, accepted as a limitation. Pilot FIRMS ingestion + trend analysis worked end-to-end. Paddy detection via NDVI was a stretch goal. [C]

### Sep 2026 — Satellite burn mapping proven feasible (reconstructed)
**Plain:** We checked against real labelled fields that Sentinel-2 can tell burnt from unburnt fields. It can, about 95% of the time.
**Technical:** See `2.1/task_burn_detection.md` (380 fields, BAIS2+TCB accuracy 95.53%). [C]

### Sep–3 Oct 2026 — Scope narrowed (reconstructed)
**Plain:** Haryana's data lagged behind, so we focused on Punjab's 97 tehsils first.
**Technical:** 151 units (Punjab + Haryana) → 97 current Punjab tehsils. Haryana: crosswalk incomplete, groundwater category-only, CI editions incomplete. [C]

### 2026-10-06 — Supervisor fixes years and scope
**Plain:** To save time, the professor agreed that rice and groundwater stay at 2022, and that we don't build our own multi-year rice maps.
**Technical:** [C] Chen 2022 rice fixed (Sentinel-1 SAR extension retired). [C] Groundwater 2022 (2025 = sensitivity only). [C] Punjab only for now. Solo project [C]; Aryan Rana is not on this project.

### 2026-10-06 — Environment blocker resolved
**Plain:** A Windows security feature blocked a mapping library. An older version of the library works.
**Technical:** pyproj 3.8.0 `_context` DLL blocked by Windows Smart App Control ("An Application Control policy has blocked this file"). `pip install --force-reinstall` did not help. **pyproj 3.6.1 loads** and is pinned. Python 3.12.10. [C]
