# Terrain (elevation, slope)
**DPPD position:** Stage 2 › Homogeneous Grouping (terrain dimension) · **Status:** In master; **expected to be replaced by agro-climatic zones** · **Last updated:** 2026-10-06

## In plain words
Most of Punjab is flat plain. The north-east edge (Shivalik foothills, the Kandi belt) is higher and hilly, with smaller fields and different farming. Elevation and slope separate those foothill tehsils from the plains. Like rainfall, terrain will probably be replaced by agro-climatic zones.

## Technical summary
- **Source:** village-level GEE export `Data/Terrain/village_terrain_elevation_slope_punjab_2026.csv` (elevation mean/sd, local relief `elev_local_stddev`, slope mean/sd per SHRUG village). DEM source (SRTM vs Copernicus) not recorded [?].
- **Tehsil file:** `Data/Terrain/tehsil_terrain_punjab_current_2026.csv`: `elevation_mean, elevation_interVillage_stdDev, elev_local_stddev_mean, slope_mean, slope_interVillage_stdDev, village_count`. All 97 covered. Roll-up script not in repo [?].
- **Grouping variables:** `elevation_mean`, `slope_mean`, each log1p-transformed. Across the 97 tehsils: elevation 181–578 m (mean 244); slope 0.02–1.05 (mean 0.18).
- **Anomaly (low priority):** slope values look too low for Shivalik tehsils (e.g. Dhar Kalan); units/derivation unverified. A 1-degree mean slope in the foothills is implausible if the units are degrees.

## Log (append-only, chronological)
### Sep–3 Oct 2026 — Terrain added for all 97 tehsils (reconstructed)
**Plain:** Elevation and slope were added to tell foothill tehsils apart from the plains.
**Technical:** "2026 terrain file", all 97 covered; log1p on elevation and slope in the transformed master. [C]

### 2026-10-06 — Supervisor: zones replace rainfall + terrain
**Plain:** Terrain will likely leave the grouping once zone data is found.
**Technical:** [C] Kept as the baseline run and as a reference. Slope units check is low priority; note it if terrain stays.

### 2026-10-06 — Slope defect found; terrain replaced by AESR zones
**Plain:** Checking a borderline tehsil (Nawanshahr) revealed that the slope numbers are unreliable. Different tehsils share exactly the same slope with no variation between villages. Rather than recompute slope, we replaced the whole terrain dimension with official agro-ecological zones, which capture foothills vs plains from a published source.
**Technical:**
- Defect: `slope_mean` = 1.046 for both Dhar Kalan and Pathankot, and 0.963 for both Nangal and Anandpur Sahib, each with `slope_interVillage_stdDev = 0.000`, while elevations differ (578 vs 296 m). Within-village `slope_stdDev = 0.0` in the village file. Likely computed at a coarse scale; source script not in repo. Elevation looks valid.
- Options considered: ✘ recompute slope in GEE (SRTM 30 m), correct but ~1 h and terrain was due to be replaced anyway; ✘ elevation only (moves 6 tehsils: Batala, Kalanaur, Rajpura, Chamkaur Sahib, Morinda, Banga; ARI 0.803); ✘ keep and flag (known-bad variable); ✔ replace terrain with AESR 2018 zone shares (see `task_agroclimatic_zones.md`).
- [C] Terrain (`elevation_log1p`, `slope_log1p`) removed from the grouping dimensions. Columns stay in the masters and the terrain files stay in the repo for reference. The slope defect should be noted in the report's data-quality limitations.
