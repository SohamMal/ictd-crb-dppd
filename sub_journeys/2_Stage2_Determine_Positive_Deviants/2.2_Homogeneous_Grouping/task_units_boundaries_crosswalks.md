# Units, boundaries & crosswalks
**DPPD position:** Stage 2 › Homogeneous Grouping (also feeds Performance Measurement) · **Status:** Done for Punjab; Haryana behind · **Last updated:** 2026-10-06

## In plain words
Every dataset uses a different map of places. Some use 2011 Census villages and tehsils; others use today's tehsils, which have since been split and redrawn. Before anything can be compared, every number has to land in the same set of places. We chose the **97 current Punjab tehsils** as our unit. It is finer than districts (so good performers aren't hidden in averages) but coarser than 12,000+ villages (so the data stays reliable). We built "bridge" tables that translate old village and tehsil codes into today's tehsils.

## Technical summary
- **Unit [C]:** 97 current Punjab tehsils (LGD subdistrict codes). Rejected: ~12.8k villages (too granular for several datasets); 23 districts (too coarse, hides PDs); 151 units Punjab+Haryana (Haryana data incomplete).
- **Village base layer [C]:** SHRUG v2.2 PC11 village polygons (Development Data Lab). Punjab 12,808 / Haryana 6,998, EPSG:4326, geometry checks passed (`Data/Boundaries/validate_shrug_boundaries.py`). GEE asset `projects/ictd-507010/assets/shrug/shrug_villages`.
- **ID-vintage problem:** SHRUG/Census use 2011 codes (Punjab 20 districts) vs current LGD (23 districts, 97 tehsils). Soil and rice village data are keyed on 2011 IDs.
- **Bridges** (`Data/LGD/Final Output/`, built by `Data/LGD/build_crosswalk.py`, `deep_bridge_analysis.py`, `build_village_reverse_bridge.py` from LGD directory exports dated 2026-09-21):
  - `tehsil_bridge_summary_punjab.csv`: 97 rows (`lgd_sd_code, current_tehsil, current_district, change_type, c2011_primary_code, …, village_count, source_breakdown`). change_type: UNCHANGED 45 · CARVED_FROM 43 · MULTI_SOURCE 9.
  - `tehsil_bridge_detail_punjab.csv`, `tehsil_bridge_reverse_punjab.csv`
  - `village_level_bridge_punjab.csv`: key `c2011_village_code` (= `pc11_tv_id`, 6-digit zero-padded) → `lgd_tehsil_code`. Used by the CI, rainfall, soil and groundwater roll-ups.
  - ✘ `tehsil_bridge_detailed_punjab.csv`: **unreliable, excluded.**
  - Null codes (000000) and town codes (800xxx duplicates) excluded from village matching.
- **Village → CD block (for groundwater) [C]:** `Data/build_punjab_block_crosswalk.py` from Census PCA (`Data/census_punjab/`): 12,581 villages → 142 blocks, 0 unmapped, 0 duplicates.
- **Current tehsil polygons [C, 2026-10-06]:** Esri India `IAB2024/IAB_Subdistrict_2024` layer, fetched by LGD code with an exact-97 check, cached at `Data/Rice/rice_area_output/punjab_current_tehsils_lgd.gpkg` (includes `tehsil_area_ha`). Σ area 50,371 km² vs official Punjab 50,362 km².
- **Mixed-resolution inheritance [C, Prof.]:** each variable kept at its native level, inherited downward (district/block → village → tehsil roll-up).
- **Open [?]:** placeholder village codes 800166, 800252 and other `8xxxxx`; 8 villages unaccounted in the Sept merge (12,800 vs 12,808); Mewat vs Nuh naming (Haryana).

## Log (append-only, chronological)
### Sep 2026 — SHRUG v2.2 locked as village layer (reconstructed)
**Plain:** We picked a public village-boundary map, checked it carefully, and uploaded it to Earth Engine.
**Technical:** Village counts and CRS checked; uploaded to GEE. [C]

### Sep 2026 — Mixed-resolution architecture approved (reconstructed)
**Plain:** The professor agreed we keep each dataset at its own level and pass it down, rather than forcing all data to one level.
**Technical:** Approved by Prof. Aaditeshwar. Majority-area-overlap rule for villages crossing zone boundaries (relevant if a zone variable is used). [C]

### Sep 2026 — Village → block crosswalk (reconstructed)
**Plain:** We linked each village to its development block so block-level groundwater data could reach villages.
**Technical:** 12,581 villages → 142 blocks, 0 unmapped. [C]

### 2026-09-21 → 3 Oct 2026 — 2011 ↔ current LGD tehsil bridges (reconstructed)
**Plain:** Many 2011 tehsils have been split into new ones, and a few new tehsils took villages from several old ones. We traced each village to its current tehsil.
**Technical:** LGD XML exports parsed; 20 new tehsils traced to 2011 parents through village codes; 43 carved, 9 multi-source. `..._detailed_` variant found unreliable and excluded. [C]

### 3 Oct 2026 — Grouping unit fixed at 97 current tehsils (reconstructed)
**Plain:** Tehsils are the middle ground between too-fine villages and too-coarse districts.
**Technical:** Masters built at 97 tehsils. [C]

### 2026-10-06 — Current tehsil polygons cached
**Plain:** We saved today's tehsil boundaries to a local file so maps and satellite work use the exact same shapes.
**Technical:** GPKG written by the patched rice script (see `task_rice_area.md`). Geodesic vs UTM 43N area differ by ≤0.08%; 11 polygon holes handled correctly. [C]
