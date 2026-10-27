# Soil
**DPPD position:** Stage 2 › Homogeneous Grouping (soil dimension) · **Status:** In master; encoding decided; descriptor pruning to propose · **Last updated:** 2026-10-06

## In plain words
Soil type affects what grows well, how water drains, and how hard it is to sow wheat into leftover straw. We took soil descriptions from the national soil survey map (NBSS&LUP): eight properties such as texture, drainage and salinity. Each tehsil gets its most common value for each property. Most Punjab tehsils share the same soil on several properties (e.g. 96 of 97 are "Deep"), so some properties barely help tell tehsils apart. We may propose dropping those, with evidence.

## Technical summary
- **Source [C]:** NBSS&LUP Bhoomi Geoportal, 1:250K soil layer (`nbss_geoserver:250K_Soils_Data`). WFS bulk export disabled → WMS `GetFeatureInfo` point queries (`Data/Soil Data/fetch_soil_type.py`, `http://14.139.123.73:8080/geoserver/wms`, ~1 km box) at tehsil centroids (`tehsil_centroids.csv`).
- **Rejected:** ✘ HARSAC (Haryana): manual form only, no bulk export, no Punjab equivalent. ✘ SLUSI file: Haryana only.
- **Pipeline:** `soil_master.csv` = one soil map unit per **Census-2011 tehsil** (77 Punjab 2011 tehsils; how the unit was chosen, centroid point vs area-dominant, is not recorded [?]) → villages inherit via `c2011_tehsil_code` (`Data/Soil Data/compute_tehsil_soil.py`) → current tehsil = **mode across villages** per descriptor. Output `punjab_tehsil_soil_master.csv`.
- **Implication [P]:** effectively one soil sample per 2011 tehsil. Carved current tehsils inherit their parent's soil, so soil cannot separate a split tehsil from its parent.
- **8 descriptors in master and their tehsil counts:**

| Descriptor | Distribution (97) |
|---|---|
| particle_size | Coarse-loamy 47, Fine-loamy 44, Sandy 4, Fine 1, Fine-silty 1 |
| drainage | Well 75, Moderately well 14, Excessive 6, Poor 1, missing→`Unknown` 1 |
| soil_texture | Loamy 86, Sandy 11 |
| soil_depth | Deep 96, Moderately deep 1 |
| ph_class | Slightly alkaline 69, Moderately alkaline 17, Neutral 11 |
| salinity | Negligible 85, Slight 11, Moderate 1 |
| sodicity | Negligible 79, Slight 16, Moderate 2 |
| erosion | Slight 85, Moderate 10, Severe 2 |

- **Encoding [C, 2026-10-06]:** use the **original categorical columns** (one per descriptor) with 0/1 mismatch in Gower. Do not use the one-hot `_encoded.csv`: it counts one real soil difference several times and dilutes the soil average with near-constant dummy columns.
- **Open [P]:** near-constant descriptors (depth 96/97; salinity, erosion 85/97) add little; propose dropping with evidence (sensitivity run). Soham's call. Fatehgarh Sahib drainage gap (104 villages) → 1 tehsil `Unknown`.

## Log (append-only, chronological)
### Sep 2026 — Soil source chosen (reconstructed)
**Plain:** We used the national soil map because it covers both states the same way.
**Technical:** NBSS&LUP chosen; HARSAC ruled out. WMS point-query workaround. [C]

### 3 Oct 2026 — 8 descriptors in master (reconstructed)
**Plain:** Eight soil properties went into the first grouping as categories.
**Technical:** One-hot encoded file built alongside. One drainage value set to `Unknown`. [C]

### 2026-10-06 — Categorical, not one-hot
**Plain:** We'll compare soils property by property ("same or different") rather than with many yes/no columns, so a single soil difference isn't counted several times.
**Technical:** [C] Categorical Gower on the original columns; dropping descriptors only with Soham's approval after evidence.
