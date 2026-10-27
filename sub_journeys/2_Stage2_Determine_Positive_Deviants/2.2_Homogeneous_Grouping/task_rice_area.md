# Rice area → rice share
**DPPD position:** Stage 2 › Homogeneous Grouping (rice dimension) · **Status:** Done — `rice_share_2022` in masters (2026-10-06) · **Last updated:** 2026-10-06

## In plain words
How much of a tehsil is under paddy is a basic condition of the place: more paddy means more straw to deal with. We measured it from a published 10 m rice map for 2022 (Chen et al. 2024). First we used total rice hectares, but that mostly tells you how *big* a tehsil is. We switched to **rice share**: the fraction of the tehsil's land that is paddy. It ranges from 7% (hilly Dhar Kalan) to 78.5% (Talwandi Sabo). Along the way we found that an older village rice file had a broken 2022 column, and we briefly built our own radar-based rice maps. The professor later agreed that one fixed year (2022) is enough.

## Technical summary
- **Source [C]:** Chen et al. (2024) 10 m paddy maps, figshare `10.6084/m9.figshare.24228619`; "Winter" files 2018/2020/2022 = Kharif rice. `Data/Rice/chen_2022.tif`: EPSG:4326, res 8.98e-5°, 1 = rice, 0 = non-rice.
- **Script [C]:** `Data/Rice/calc_chen2022_rice_area_current_lgd.py`
  1. 97 LGD codes from `Data/LGD/Final Output/tehsil_bridge_summary_punjab.csv` (`lgd_sd_code`, `current_tehsil`).
  2. Polygons fetched from Esri India `IAB2024/IAB_Subdistrict_2024`; fails unless exactly the 97 codes come back.
  3. Rice pixels per tehsil via `rasterio.mask` (`all_touched=False`); each pixel's area computed **geodesically on the WGS84 ellipsoid** row by row (a 0.0000898° pixel is ~84 m² at 32.4 N, not 100 m²).
  4. *(2026-10-06 patch)* `tehsil_area_ha` = geodesic polygon area (`pyproj.Geod.geometry_area_perimeter`, same ellipsoid, so numerator and denominator use the same method); `rice_share_2022 = chen_rice_area_ha_2022 / tehsil_area_ha`; check share ∈ [0,1]; polygons cached to `punjab_current_tehsils_lgd.gpkg`.
- **Output:** `Data/Rice/rice_area_output/punjab_current_tehsil_rice_2022.csv`: `lgd_tehsil_code, lgd_tehsil_name, chen_rice_pixel_count_2022, chen_rice_area_ha_2022, tehsil_area_ha, rice_share_2022`.
- **Grouping variable [C, 2026-10-06]:** `rice_share_2022` (raw, no log). `rice_area_log1p` is kept in the masters but no longer used.
- **Caveat [C]:** the denominator is **total tehsil land area**, not cultivated area. Urban or forest-heavy tehsils (Jalandhar-I 0.325, SAS Nagar 0.349) get a lower share partly because of non-farm land. This is still the structural "how paddy-dominated is this place" measure we want.
- **Rejected / retired:**
  - ✘ Absolute rice hectares: confounded by tehsil size (Spearman with share = 0.52, so the choice matters).
  - ✘ Village CSV `village_rice_all_years.csv` 2022 column: stale copy of 2020 (98.6% identical; standalone `village_rice_2022.csv` byte-identical). 2018/2020 columns are fine (r = 0.988). Chen 2022 in the masters comes from the GeoTIFF directly, so it is not affected.
  - ✘ Sentinel-1 SAR 2022–24 rice (retired 2026-10-06): rule VH < −18 dB in mid-Jun–Jul transplant window AND rise ≥ 5 dB by Aug–Sep. Validated on 2 villages only (Ludhiana 78.8%; Fazilka `034223` 87.1% vs official 71.3% / 69.8%).

## Log (append-only, chronological)
### Sep 2026 — Stale 2022 column found (reconstructed)
**Plain:** The village rice file's 2022 numbers were just a copy of 2020.
**Technical:** 98.6% of Punjab villages had 2022 = 2020; the standalone 2022 file was byte-identical, so the staleness is in the source. [C]

### Sep 2026 — Sentinel-1 SAR rice side-track (reconstructed)
**Plain:** We built our own radar-based rice detector for 2022–24. It worked on test villages, and showed that Fazilka is rice-heavy, the opposite of what we had assumed.
**Technical:** Rule as above. The first attempt used wrong district codes (guessed 051/052/056; correct Ludhiana/Patiala/Sangrur = 041/048/053). Full export never confirmed. [C]

### 3 Oct 2026 — Keep Chen 2022; switch to rice share (reconstructed)
**Plain:** We decided a single good rice year is enough for grouping, and that share is fairer than hectares.
**Technical:** Rice treated as a structural trait. Share avoids the size confound. Script patch pending. [C]

### 2026-10-06 — Supervisor: Chen 2022 fixed, SAR retired
**Plain:** The professor confirmed: no need to extend rice maps to 2023–24.
**Technical:** [C] Chen 2022 fixed. SAR scripts kept in the repo as reference only.

### 2026-10-06 — Rice share computed and added to masters
**Plain:** We added tehsil land area and rice share. All checks passed: rice hectares unchanged, total area matches Punjab's official area, and share is low in the hills and high in the Malwa plains.
**Technical:**
- Run: `python ../calc_chen2022_rice_area_current_lgd.py --rice-tif ../chen_2022.tif --summary-csv "../../LGD/Final Output/tehsil_bridge_summary_punjab.csv" --out punjab_current_tehsil_rice_2022.csv` (from `rice_area_output/`). Env: pyproj pinned to 3.6.1 (3.8.0 blocked by Windows Smart App Control).
- QA: rice ha max abs change vs previous output = 0.0; Σ tehsil area 50,371 km² vs official 50,362; geodesic vs UTM 43N −0.003% to −0.080%; 11 holes OK; 97/97 tehsils have rice > 0. Σ rice = 3,053,086 ha.
- `rice_share_2022`: min 0.070 (Dhar Kalan), Q1 0.552, median 0.641, Q3 0.700, max 0.785 (Talwandi Sabo); mean 0.598, sd 0.141.
- District medians: lowest Pathankot 0.212, Hoshiarpur 0.289, Rupnagar 0.351, SAS Nagar 0.396; highest Bathinda 0.736, Faridkot 0.731, Moga 0.726, Barnala 0.723. Sangrur 0.665, Patiala 0.652, Ludhiana 0.635.
- **[P] Flag:** SW Malwa (Bathinda/Mansa/Faridkot/Moga) is above the Sangrur/Patiala belt, which is against expectation. The state total (30.5 lakh ha) is close to official paddy area. Verify against official 2022 district paddy area if available (Statistical Abstract district crop tables are not text-extractable).
- Masters updated (join on `lgd_tehsil_code`, chen rice ha cross-checked equal): raw 28→30 cols (+`tehsil_area_ha`, `rice_share_2022`); transformed 37→40 and encoded 55→58 (+ those + `rice_share_2022_z`, population sd, ddof = 0, matching the existing z-columns). Backups in `Data/_backup_2026-10-06/`.
- [C] Soham: `rice_share_2022` replaces `rice_area_log1p` as the grouping variable ("more logical").

### 2026-10-07 — Check vs official statistics: Chen 2022 is biased by region (SW and foothills over-mapped)
**Plain:** We compared Chen's satellite rice map with the government's official rice area for each district. Chen is not uniformly off. It **under-counts** rice in central Punjab by about 10–25%, but **over-counts** it in the cotton belt of the south-west (Fazilka 1.7×, Bathinda 1.4×, Mansa 1.3×) and in the foothills (Hoshiarpur, Mohali, Rupnagar about 1.3–1.4×). So the earlier surprise, the south-west looking more paddy-dominated than Sangrur/Patiala, is mostly an error in the map, not reality. In official numbers, Sangrur, Barnala, Moga and Patiala are the most paddy-dominated districts, and Bathinda, Mansa and Fazilka are much lower. This affects our grouping (rice share is one of the six dimensions) and, more seriously, the coming burn measurement, which was going to use Chen to decide which fields are rice.
**Technical:**
- Official: Statistical Abstract of Punjab 2022, Table 4.7 (rice area, 2021-22 P, thousand ha, Director of Agriculture), PDF p.151; district order from the English labels on p.152. Patiala text layer reads 283.7, corrected to **233.7** (Table 4.8 p.161; district sum then equals the state total 3,144.6). Sangrur includes Malerkotla. Saved `Data/Rice/official/punjab_district_rice_area_2021_22_statabstract2022.csv` + README. 2021-22 vs 2022: spot checks for 2022-23 (Ludhiana 258.8, Amritsar 181.0, Barnala 114.5 thousand ha) are within ~2%.
- Comparison (`Data/Rice/official/chen_vs_official_by_district.csv`), Chen 2022 / official: Kapurthala 0.76, Jalandhar 0.80, Sangrur 0.83, Gurdaspur 0.84, Tarn Taran 0.84, Fatehgarh Sahib 0.85, Ferozepur 0.86, Barnala 0.87, Ludhiana 0.88, Amritsar 0.89, Moga 0.90, Patiala 0.90, Faridkot 0.93, SBS Nagar 0.94, Pathankot 0.95, Muktsar 1.04, **Mansa 1.28, Rupnagar 1.30, Bathinda 1.38, Hoshiarpur 1.40, SAS Nagar 1.41, Fazilka 1.71**. State: 3,053 vs 3,145 (0.97).
- By frozen group (Chen / official-implied): Central 0.87, South-west 1.22, Foothills 1.23.
- Rice share, district level: Spearman(Chen, official) = 0.62 only. Official share: Barnala 0.815, Sangrur 0.809, Moga 0.807, Faridkot 0.792, Ferozepur 0.792 … Bathinda 0.534, Mansa 0.565, Fazilka 0.393.
- Likely cause [P]: confusion with cotton and other kharif crops in the SW cotton belt, and with maize in the foothills.
- Denominators: both shares use our geodesic district area (sum of tehsils), so the comparison is like-for-like.
- Implications: (1) the grouping's rice dimension is distorted (the SW looks more rice-heavy than it is); (2) **Phase B:** a Chen-based rice mask would include non-rice fields in the SW and foothills and deflate their burnt-share-of-rice, risking false positive deviants exactly there. Decision needed [?] (Soham).

### 2026-10-07 — DECISION + DONE: Chen calibrated to official district totals
**Plain:** We keep Chen's map for *how rice is spread between tehsils inside a district*, but scale each district so its total matches the government figure. South-west and foothill tehsils go down (e.g. Fazilka ×0.59, Bathinda ×0.73); central tehsils go up (e.g. Kapurthala ×1.31, Sangrur ×1.21). The calibrated rice share now drives the grouping.
**Technical:**
- [C] Soham chose option 1 (calibration) over official-district-share-for-all and keep-Chen.
- `Data/Rice/calibrate_rice_to_official.py` → `rice_area_output/punjab_tehsil_rice_2022_calibrated.csv` (`calibration_factor, rice_area_ha_2022_cal, rice_share_2022_cal`). factor = official district rice (2021-22, thousand ha × 1000) / Σ Chen tehsil rice in district; Malerkotla → Sangrur. Asserts district sums = official; shares ∈ [0,1].
- Factors: Fazilka 0.585, SAS Nagar 0.709, Hoshiarpur 0.716, Bathinda 0.727, Rupnagar 0.768, Mansa 0.784, Muktsar 0.964, Pathankot 1.053, SBS Nagar 1.063, Faridkot 1.079, Patiala 1.113, Moga 1.115, Amritsar 1.120, Ludhiana 1.143, Barnala 1.150, Ferozepur 1.169, Fatehgarh Sahib 1.177, Tarn Taran 1.191, Gurdaspur 1.194, Sangrur 1.213, Jalandhar 1.257, Kapurthala 1.314.
- `rice_share_2022_cal`: min 0.074 (Dhar Kalan), Q1 0.546, median 0.707, Q3 0.788, max 0.871 (Moonak); mean 0.637. Spearman vs uncalibrated share 0.654.
- Masters: + `calibration_factor, rice_area_ha_2022_cal, rice_share_2022_cal` (+ `_z` in transformed/encoded): raw 37→40, transformed 47→51, encoded 65→69. Backups `Data/_backup_2026-10-07_pre_ricecal/`. `config.DIMENSIONS["rice"] = rice_share_2022_cal`.
- Limitation: calibration fixes district totals, not within-district errors (e.g. cotton pixels within a Bathinda tehsil still mislabelled). The Phase B rice *mask* problem remains open.
