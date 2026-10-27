# Cropping intensity (CI)
**DPPD position:** Stage 2 › Homogeneous Grouping (dimension 1 of grouping) · **Status:** In master (`CI_3yr_pooled`); QA open · **Last updated:** 2026-10-06

## In plain words
Cropping intensity is how many crops a piece of land grows per year: 100% = one crop, 200% = two. Punjab is mostly rice-then-wheat, about 200%. It matters for burning because a tight rice→wheat turnaround leaves little time to clear straw. Official numbers exist only per district, which would hide differences between tehsils, so we measured CI ourselves from satellite greenness for every village and added the villages up to tehsils.

## Technical summary
- **Formula [C]:** `CI = 100 × (A1 + 2·A2 + 3·A3) / (A1 + A2 + A3)`, where Ak = cropland pixels with k detected growing seasons in the ag-year.
- **Detection:** Sentinel-2 SR Harmonized NDVI time series, Kharif/Rabi/Zaid windows, ESA WorldCover cropland mask, peak/trough rules (`PEAK_MIN`, `TROUGH_MAX`, `AMPLITUDE_MIN`; values not recorded [?]). GEE, per village.
- **Roll-up [C]:** `Data/Crop Intensity/Punjab/compute_and_audit_ci.py`. Village A1/A2/A3 **summed** per current tehsil via `village_level_bridge_punjab.csv`, then the formula is applied once (**sum-then-divide**; averaging village percentages is wrong). Inputs: `punjab_ci_clean45_villages_{yr}.csv` + `punjab_ci_villages_{yr}.csv` from `~/Downloads/Croppin Intensity/` [?: not in repo]. Output `punjab_tehsil_cropping_intensity_2022_2024.csv`.
- **Grouping variable:** `CI_3yr_pooled` (2022–2024). Across the 97 tehsils: mean 203.65, sd 9.29, min 179.78, max 237.50.
- **Baseline / cross-check:** district CI from Punjab Statistical Abstracts (`Data/Crop Intensity/`, `crop_intensity_punjab_haryana.csv`, 2018-19 to 2021-22; `CI = GCA/NSA × 100`).
- **QA flags (open):** satellite CI runs above the Abstract baseline in the Southwestern belt (200.4 vs 175–190) and Kandi belt (192.7 vs 150–175), so either the thresholds need tuning or satellite CI differs structurally. Year-to-year swings of 20–32 pts in Sultanpur Lodhi, Nihal Singhwala, Balachaur, Nangal, Tapa, Khadur Sahib.
- **Open [?]:** how CI for the 52 current tehsils from the remaining 32 2011-tehsils was finalised (master has all 97 filled).

## Log (append-only, chronological)
### Sep 2026 — District CI baseline from Statistical Abstracts (reconstructed)
**Plain:** We first collected the government's district CI numbers to use as a reference.
**Technical:** pdfplumber extraction ("Classification of Area" table, Net Area Sown / Total Cropped Area), Punjab 22 + Haryana 22 districts, 2018-19 to 2021-22. [C]

### Sep 2026 — Own satellite CI at tehsil level (reconstructed)
**Plain:** District numbers would hide tehsil differences, so we built our own satellite measurement.
**Technical:** 45 "clean" (unchanged) 2011-tehsils first: mean 204.6% (179.8–235.3). Sum-then-divide rule adopted. [C]

### Late Sep – 3 Oct 2026 — Extended to all 97 current tehsils (reconstructed)
**Plain:** We extended the CI calculation to every current tehsil, including the newly split ones.
**Technical:** Remaining 32 2011-tehsils → 52 current (43 carved, 9 blended), rolled up by `lgd_tehsil_code`, not `pc11_sd_id`. `CI_3yr_pooled` written to masters. Threshold tuning still open. [C]

### 2026-10-07 — QA: satellite CI vs official district CI. Poor agreement
**Plain:** We added our satellite CI up to districts and compared it with the government's district CI. They hardly agree on which districts crop more intensively. Our satellite CI is higher almost everywhere, by up to 44 points in Jalandhar and Rupnagar, and it also jumps around between years. CI is one of the six grouping dimensions, so this matters. Decision pending.
**Technical:**
- Satellite: district = Σ village A1/A2/A3 from `Punjab/punjab_tehsil_cropping_intensity_2022_2024.csv` (sum-then-divide; Malerkotla → Sangrur). Official: `crop_intensity_punjab.csv` 2021-22 (GCA/NSA×100, Statistical Abstract; SAS Nagar missing).
- Spearman(official 2021-22, satellite 2022) = **0.184** (n = 21). Satellite − official (2022): Pathankot −12.4; Gurdaspur +3.6, Muktsar +5.0, Fazilka +5.1, Mansa +8.8, Moga +9.1, Amritsar +11.1, Patiala +11.2, Bathinda +11.3, SBS Nagar +11.9, Sangrur +12.3, Kapurthala +13.5, Faridkot +16.0, Barnala +17.5, Tarn Taran +18.9, Ludhiana +23.8, Fatehgarh Sahib +24.1, Ferozepur +25.3, Hoshiarpur +29.0, **Jalandhar +43.4, Rupnagar +43.7**.
- Year swings at district level are large (e.g. Bathinda 209.2 → 194.1 → 200.3; Kapurthala 214.3 → 210.6 → 226.0).
- Caveats: different definitions (official = gross cropped / net sown from land records; satellite = detected NDVI seasons on ESA WorldCover cropland pixels), and year mismatch (2021-22 vs 2022).
- Grouping relevance (sensitivity at k4): drop CI → ARI 0.832; CI weight ×1.15 → 0.484 (SW dissolves). CI sd across tehsils is only 9.3 pts.
- Options [?] (Soham): keep + limitation / replace with official district CI / calibrate to official / drop the CI dimension / retune GEE thresholds.

### 2026-10-07 — Does CI shape the grouping? Test before deciding to drop
**Plain:** Soham's rule: CI can only be dropped if we show it barely affects the groups; otherwise it must be recalculated properly. We tested this three ways. CI is the weakest of the six dimensions at telling the groups apart. Removing it changes only 2 of 96 tehsils, both already flagged borderline. Replacing our satellite CI with the official district CI, as a stand-in for a "correctly measured" CI, gives exactly the same groups as dropping it. So recalculating CI would not change the grouping, and no GEE rework is needed.
**Technical:** `Code/grouping/ci_influence.py` → `outputs/grouping/ci_influence_dimension_separation.csv`, `ci_influence_groups_without_ci.csv`.
- Separation power (mean between-group ÷ mean within-group distance, frozen v3 groups): rice 2.918, rainfall 2.510, groundwater 1.756, zone 1.469, soil 1.193, **CI 1.138** (lowest; 1 = no separation).
- Pairwise distances with vs without CI: r = 0.972.
- Full procedure without CI (k4 + bootstrap consensus): Central 63 / South-west 18 / Foothills 15, **ARI 0.932 vs frozen**; changed only **Firozpur** (Central → SW) and **Dinanagar** (Foothills → Central), both borderline in v3.
- Official district CI (2021-22, inherited to tehsils; range 134.9–201.0; medians Central 196.2, SW 197.9, Foothills 164.6): separation 2.013, but the grouping is identical to dropping CI (ARI 0.932, same 2 changes). A correct CI mainly re-encodes the foothills difference already carried by zone and rainfall.
- Satellite CI medians by group: Central 204.7, SW 202.1, Foothills 194.3.
- Conclusion [P]: dropping CI is safe and evidence-based; recalculating CI is not needed for grouping. Awaiting Soham's decision.

### 2026-10-07 — Review of the GEE CI script (v2): logic correct, design choices inflate CI
**Plain:** We read the Earth Engine script line by line. The arithmetic is right: it counts crops per pixel and adds pixel counts before dividing. But several design choices push CI up compared with official figures. The script almost never finds single-cropped land (only 5–8% of pixels), while official CI of about 165 in Hoshiarpur/Rupnagar implies a third or more of the land grows only one crop. It also counts a third (summer) crop on 6–22% of pixels. Likely causes: monsoon weeds on fallow land being read as a kharif crop, long crops like sugarcane counted twice, the cropland map leaving out marginal rainfed land, and thresholds that were never tuned. This is a measurement difference, not a single bug. It supports dropping CI, since even a correct CI does not change the grouping.
**Technical:**
- Script saved to `Code/gee/ci_village_punjab_v2.js` (pasted from the GEE link, which needs a login). Covers the 45 clean 2011 tehsils; the variant behind `punjab_ci_villages_{yr}.csv` (other villages) is not in the repo [?].
- Correct: CI = 100(A1 + 2A2 + 3A3)/(A1 + A2 + A3) with village pixel sums exported and summed to tehsil before dividing; SCL cloud mask (keeps 2, 4, 5, 6, 7); empty-collection guard; 10 m, tileScale 8.
- Season rule: crop in a window if p90 NDVI ≥ PEAK_MIN 0.475 AND (p10 NDVI in the 25 days before ≤ TROUGH_MAX 0.225 OR peak − trough ≥ AMPLITUDE_MIN 0.20). Windows for ag-year y: kharif Jul 1–Oct 31, rabi Dec 1–Mar 31, zaid Apr 15–Jun 15 (y+1). Thresholds marked "tune after first look"; never tuned.
- Observed pixel mix (all tehsils): 2022 A1 5.7% / A2 81.9% / A3 12.5%; 2023 7.8 / 86.0 / 6.3; 2024 4.7 / 85.6 / 9.8. Highest A3 (2022): Jalandhar 22.4%, Kapurthala 20.7%, Barnala 19.0%, Ludhiana 18.5%. Highest A1: Pathankot 17.1%, Hoshiarpur 16.1%, SAS Nagar 14.6%.
- Likely inflation mechanisms [P]:
  - (1) Kharif: PEAK_MIN 0.475 is low, and "trough low" alone suffices, so monsoon weed/grass greening on fallow or rainfed land passes as a crop.
  - (2) Perennial/long crops (sugarcane, fodder) can be flagged in two windows (e.g. kharif + zaid after ratoon), while official statistics count them once.
  - (3) ESA WorldCover 2021 cropland (class 40) likely excludes marginal kandi/rainfed fields, and pixels with zero detected seasons drop out of the denominator. Both shift the sample towards intensively cropped land.
  - (4) Zaid detections (summer moong, spring maize, potato–maize sequences in Doaba) are partly real but unvalidated.
  - (5) Labels: script year 2022 = ag-year 2022-23 vs official 2021-22.
  - (6) Kharif 2023 was affected by the July 2023 Punjab floods (swing year).
- Relevance: does not change the CI-influence result (grouping identical with official CI or without CI). Phase B note: the burn script should not reuse these NDVI thresholds without validation.

### 2026-10-07 — Provenance of the "other 32 2011-tehsils" CI exports
**Plain:** The script for the remaining villages is missing, but the export files strongly suggest it was the same script with only the tehsil filter changed. Same columns, exported in the same session about 20 minutes later, covering exactly the villages the first script left out, with a very similar crop-count mix. This is likely but not proven.
**Technical:**
- Files (`~/Downloads/Croppin Intensity/`, not in repo): `punjab_ci_clean45_villages_{2022,2023,2024} (1).csv` (6,169 villages, 45 pc11_sd_id; modified 27 Sep 14:45–14:56) and `punjab_ci_villages_{yr}.csv` (6,639 villages, 32 pc11_sd_id; all modified 27 Sep 15:17). Disjoint tehsil sets; 6,169 + 6,639 = 12,808 = full SHRUG Punjab. Identical columns `pc11_tv_id, pc11_sd_id, ag_year, A1, A2, A3`.
- Pixel mix (A1/A2/A3), clean45 vs other: 2022 .060/.803/.137 vs .056/.829/.114 (CI 207.7 vs 205.8); 2023 .082/.838/.080 vs .076/.876/.048 (199.8 vs 197.2); 2024 .047/.833/.120 vs .048/.873/.079 (207.3 vs 203.1). Consistent with the same thresholds (the remaining tehsils show slightly fewer triple-crop pixels).
- [?] Exact script unverified (thresholds could have been edited). Possible recovery: GEE Code Editor script history / Tasks tab for `punjab_ci_villages_*`. Low priority if CI is dropped; record as a provenance gap otherwise.

### 2026-10-07 — DECISION: CI dropped from grouping; validated tehsil CI = future work
**Plain:** Our tehsil CI is not measured correctly, and official CI exists only per district. Recalculating it properly would take 1–2 days of Earth Engine tuning, and every test says it would not change the groups. So CI leaves the grouping and is listed as future work.
**Technical:**
- [C] Soham accepted the recommendation (drop now; recalculation deferred).
- Soham's counter-point, recorded: official CI is district-level, so the official-CI test cannot show whether a correct *tehsil* CI would split tehsils within a district. Response: the main real CI variation (Kandi single cropping) is already captured at tehsil level by zone + rainfall. Residual risk accepted and to be stated.
- Report wording: "Tehsil-level CI could not be measured reliably (satellite CI ρ = 0.18 vs official); since neither dropping CI nor substituting official CI changed the grouping beyond two borderline tehsils, CI was excluded; a validated tehsil CI is left for future work."
- `config.py`: `cropping_intensity` removed; `CI_3yr_pooled` stays in the masters.
