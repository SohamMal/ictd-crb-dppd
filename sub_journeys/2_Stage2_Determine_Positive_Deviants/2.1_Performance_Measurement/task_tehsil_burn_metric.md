# Tehsil burn metric — scaling BAIS2+TCB to 97 tehsils
**DPPD position:** Stage 2 › Performance Measurement · **Status:** Not started (begins after grouping freeze) · **Last updated:** 2026-10-06

## In plain words
The burn classifier works on fields. To compare tehsils we need one number per tehsil per year. The leading candidate is "what share of the tehsil's rice area was burnt". This adjusts for the fact that big or rice-heavy tehsils naturally have more to burn.

## Technical summary
- **Objective:** a per-tehsil, per-year burn performance value for 2022–2024 (3 seasons, so PDs must be consistent, not one-off).
- **Candidate metric [P]:** burnt paddy area / Chen 2022 rice area (`chen_rice_area_ha_2022`). Not yet decided.
- **Planned pipeline [P]:** GEE; S2 SR Harmonized; post-harvest window ≈ 15 Oct – 30 Nov (snapshot(s) or composite); cloud mask; Chen 2022 rice mask; BAIS2+TCB classifier from `task_burn_detection.md`; `reduceRegions` sum over tehsil polygons (`Data/Rice/rice_area_output/punjab_current_tehsils_lgd.gpkg`); per-tehsil valid-pixel % as a quality flag.
- **QA plan [P]:** year-to-year correlation; rank correlation vs FIRMS (sanity only); visual checks (high/mid/low tehsil); late-harvest window risk.
- **Open [?]:** metric definition; years; single snapshot vs multi-date.

## Log (append-only, chronological)
### 2026-10-06 — File created
**Plain:** Placeholder; work starts after the groups are frozen (plan: 11–12 Oct).
**Technical:** Tehsil polygons are now cached as GPKG, so the same geometry can be uploaded to GEE. [C]

### 2026-10-07 — Phase B design decisions
**Plain:** We agreed how to measure burning per tehsil. Look for burn scars on all cropland, not on the biased rice map. Check every clear satellite image through the harvest season, not one snapshot. Divide burnt area by the calibrated rice area. Use five seasons (2020–2024) so a "positive deviant" has to be consistent, not lucky in one year. Before scaling up, we test whether the burn threshold learned on 380 fields still works on other dates, at pixel level, and across many images.
**Technical:**
- [C] Metric = burnt cropland area (Oct–Dec) / `rice_area_ha_2022_cal` (calibrated to official district totals); values > 1 flagged.
- [C] Detection area = ESA WorldCover cropland (not the Chen rice mask: Chen over-maps rice ×1.3–1.7 in SW/foothills, which would deflate burnt share there → false PDs).
- [C] Window = every clear S2 SR Harmonized image, 1 Oct – 15 Dec; per-tehsil clear-observation counts as a quality flag.
- [C] Years = **2020–2024** (5 seasons; Soham: "only 3 years will lead to cherry counting"). Includes both CEEW ground-truth years (2020-11-10, 2021-10-29); 2023 flood year included.
- [C] Classifier = BAIS2 + TCB logistic model; transferability tested first (Soham's question: is the threshold learned on 380 fields valid for all villages?). Risks: date/haze drift (TCB), sandy SW soils, field-median vs pixel, false-positive accumulation over ~14 looks.
- Plan: check 1 cross-date/area transfer (train 2021 → test 2020 and reverse); check 2 pixel-level accuracy; check 3 multi-look rule ("any look" vs "≥2 consecutive" vs "became dark") over the full Oct–Dec series; check 4 (SW hand-labelled spot check, ~50 fields) decided after 1–3.
- Roll-up: village `reduceRegions` → tehsil via `village_level_bridge_punjab.csv` (no new GEE asset needed).

### 2026-10-11 — Window changed to the official season, 15 Sep–30 Nov
**Plain:** We now look for burning only during the government's official stubble-burning season, 15 September to 30 November. December is dropped. This does not solve the ploughed-field problem, but it removes some false alarms and matches how official fire counts are made.
**Technical:** [C] Soham. Supersedes the 2026-10-07 "[C] Window = 1 Oct – 15 Dec". Source: ISRO protocol adopted by CAQM (counts 15 Sep–30 Nov annually). Mid-November cut-off rejected. Evidence in `task_burn_detection.md` (2026-10-11, window entry).

### 2026-10-27 — Final-model tehsil run built and started (single pixel, cut 0.79 main / 0.5 sensitivity, 2019–2024)
**Plain:** We are now recomputing the burn measure for all 97 tehsils with the final Sentinel-2 model. It uses the same 100 rice points per tehsil as the old heat-peak table, so the two can be compared directly. For each point and season, the model finds the picture where the burn score jumps most (15 Sep–30 Nov). It compares that picture with the last clear picture before it and decides burnt or not. A point with no clear picture, or with no picture before the jump, is "unknown" and left out. The heat peak is no longer used. Each point is read as a single 20 m pixel, the best option on Jalandhar in the gate test of single pixel vs 3×3 vs 5×5.
**Technical:**
- [C] Soham (2026-10-27): single pixel; main cut = Walker cut90 (0.786), sensitivity 0.5; seasons 2019–2024 (PD uses 2020–2024; 2019 for the CREAMS check); heat peak dropped; the old heat-peak table is kept as the comparison measure.
- Code: `Code/burn/tehsil_metric_rf.py` → `outputs/burn_tehsil_rf/` (`tehsil_burn_measure.csv` with `burnt_share`, `burnt_share_05`, `n_look`, `n_unknown`; `point_verdicts.csv`; `aggregation_checks{,_05}.csv`; `district_from_tehsils.csv`; `old_vs_new.csv`; raw S2 cache in `raw/`).
- Extraction: S2 SR Harmonized, CLOUDY_PIXEL_PERCENTAGE < 60, 25 Aug – 1 Dec (for the 20-day "before"), `sampleRegions` scale 20 of SCL + B2–B8, B11, B12; clear = SCL {2,4,5,7}; same-day tiles averaged. Indices and old-detector z computed locally (`labelling_package.model()`), RF = `jalandhar_walker_model_test.walker_model()` with pre_looks 1.
- 2022 also scored with the window ending 24 Oct for the CREAMS in-season table.
- Smoke test (first 200 points: Dhar Kalan, Pathankot): runs end to end; points with a verdict 92–100 per tehsil per year.

### 2026-10-28 — Final-model tehsil run done: matches CREAMS 2022 and VIIRS far better than the heat-peak table, and stable from year to year
**Plain:** All 97 tehsils have a burn share for 2019–2024. Almost every point got a verdict: at worst 70 of 100 in one tehsil in 2022, typically 100. Three checks say the new measure is sound:
- **Official 2022 figures (CREAMS, till 24 Oct):** the district order agrees strongly (ρ 0.87), and so does the state total (7.8% vs 9.9%).
- **Satellite fire counts (VIIRS):** the tehsil order agrees closely in every year (ρ 0.78–0.87; 0.51 in 2024, when farmers dodge the satellite's pass). The old heat-peak table agreed only weakly with VIIRS (0.22–0.36).
- **Year-to-year stability:** each year's tehsil order resembles the next year's (ρ 0.82–0.91; 0.62 into 2024). That is what a real, lasting behaviour looks like.
The weak spots are the 2019 level (our 59% vs CREAMS 37%; CREAMS changed its method between 2019 and 2020) and the 2020 district order (ρ 0.50, the old table 0.82). The new and old tehsil tables rank tehsils very differently (ρ 0.1–0.5). The strict (0.79) and loose (0.5) cuts rank tehsils almost the same (ρ 0.84–0.98), so the cut choice changes the level, not the order.
**Technical:** `python Code/burn/tehsil_metric_rf.py` (started 2026-10-27 23:49; finished 2026-10-28 ~00:35) → `outputs/burn_tehsil_rf/`. Walker cut90 = 0.786.
- [C] Points with a verdict / 9,700: 2019 9,633; 2020 9,693; 2021 9,695; 2022 9,441; 2023 9,675; 2024 9,677. Per tehsil min: 80, 99, 98, 70, 94, 96.
- [C] vs CREAMS (main cut; all 22 districts / 18 plains): 2019 state 59.3 vs 37.4, ρ 0.754 / 0.567; 2020 59.7 vs 55.7, ρ 0.503 / 0.160; 2022 (≤ 24 Oct) 7.8 vs 9.9, ρ 0.871 / 0.884. Cut 0.5: 2019 75.2, ρ 0.692; 2020 76.8, ρ 0.523; 2022 12.1, ρ 0.947 / 0.971. Heat-peak table (same check): 2019 ρ 0.366, 2020 0.815, 2022 0.644.
- [C] Spearman, 81 PD-group tehsils: new vs heat-peak 0.11–0.26; main vs 0.5 cut 0.84–0.97; year-to-year (main) 2019→20 0.84, 20→21 0.91, 21→22 0.84, 22→23 0.82, 23→24 0.62; vs VIIRS fires per 1,000 ha rice 2019 0.79, 2020 0.86, 2021 0.87, 2022 0.79, 2023 0.78, 2024 0.51.
- [C] Area-weighted burnt % (main), Central / South-west / Foothills: 2019 58.9 / 67.4 / 30.6; 2020 61.1 / 66.0 / 26.8; 2021 66.9 / 70.2 / 25.9; 2022 53.3 / 61.3 / 21.7; 2023 52.5 / 60.2 / 19.9; 2024 58.7 / 80.7 / 28.6.
- Reading [P]: the new measure is fit for PD identification (2020–2024). Caveats for the report: the 2019 level (CREAMS method change), the 2020 district order, the 2024 SW jump (80.7%; unchecked), partial-burn under-count, and untested pixel-level false alarms on ploughed fields.
