# Positive deviant validation
**DPPD position:** Stage 2 › Positive Deviant Validation · **Status:** Not started · **Last updated:** 2026-10-06

## In plain words
Before trusting a "positive deviant", we check it isn't a mistake. Maybe clouds hid the fires, the tehsil has little rice to burn, farmers switched crops, or harvest fell outside our satellite window. Only tehsils that pass these checks count as real positive deviants.

## Technical summary
- **Robustness [P]:** PD status kept under alternative cut (k±1), groundwater-2025 grouping, different burn threshold/window.
- **Artefact checks [P]:** low rice share; cloud/valid-pixel gaps; crop switching after 2022; early/late harvest; boundary errors; visual Sentinel-2 check per PD.
- **Output [P]:** `outputs/pd/pd_validated.csv` with reason codes for dropped candidates. If few survive, report "consistent low burners" honestly.
- Ground-truth provenance must be confirmed before external citation [?].

## Log (append-only, chronological)
### 2026-10-06 — File created
**Plain:** Placeholder; planned for 14 Oct.
**Technical:** Depends on `2.3/task_pd_identification.md`.

### 2026-11-07 — Validation plan and scope chosen (core checks + visual check)
**Plain:** Validation asks whether a flagged tehsil really burns less, or whether the result comes from noise, a data error, or a structural difference we did not group on. Soham chose eight checks run in code on data we already have, plus one hand check on satellite images. The main risk is Abohar: it lies in a cotton belt, so "low burning" could mean "little paddy there to burn".
**Technical:**
- Units [C]: strict PD Abohar; borderline Dinanagar (static), Samana (temporal); Doaba low-burning cluster (Gurdaspur, Phagwara, Adampur, Jalandhar-I, Banga); old-rule only Talwandi Sabo, Dirba; NDs (Lehra, Zira, Moonak, Guruharsahai, Malout) as a light contrast.
- Checks [C scope, P detail]: V1 point bootstrap of the fence; V2 settings (cut 0.5, offset c 5/10/20%, alternative grouping); V3 clear-look / unknown share; V4 rice presence (rice share, harvest found); V5 harvest timing; V6 triangulation (VIIRS, CREAMS district, Doaba rotation signal); V7 blind Sentinel-2 visual check (no Planet). V8 local knowledge (Prof. Aaditeshwar, Basma) in parallel, outside code.
- Basis: DPPD Handbook p. 67–68 (time series, triangulation, local knowledge). Output planned: `outputs/pd/pd_validated.csv` with per-check pass/flag/fail and a final label.

### 2026-11-07/08 — V1–V6 run; V7 labelling package built
**Plain:** The lowest-burner PDs mostly hold up against noise and changed settings. Abohar, the strict PD, survives 92% of resampled datasets and every alternative setting. The fastest-reducer PDs Samana and Dirba do **not** hold up: they keep their flag in fewer than 4 of 10 resamples, so their trend could be sampling luck. The same is true of all three "rising fastest" NDs. The main warning comes from rice: every low-burner PD except Talwandi Sabo has less rice than most of its group, and across all tehsils burning goes up with rice share even inside a group. A low burner may simply be a tehsil where paddy is less dominant, or where the rice map includes non-rice fields. The visual check (120 points to label by eye) is ready.
**Technical:**
- Code: `Code/pd/pd_validate.py` (V1–V6, final table), `Code/pd/pd_visual_package.py` (V7 build / `--score`). `pd_identify.py`: new measures `s2rf_05`, `s2rf_05_2023`; options `--c-share`, `--groups`, `--tag` (defaults reproduce earlier outputs byte-for-byte). `grouping/sensitivity.py` also writes `sensitivity_labels.csv` (sensitivity table unchanged).
- Out: `outputs/pd/validation/v1_bootstrap.csv` … `v6_triangulation.csv`, `outputs/pd/pd_validated.csv`.
- [C] V1 (B = 1,000, binomial redraw of each tehsil-year's verdicts, seed 42; strict units on strict rule, others on old rule): static PDs Dinanagar 1.00, Phagwara 0.99, Jalandhar-I 0.98, Talwandi Sabo 0.97, Gurdaspur 0.97, **Abohar 0.92 (strict)**, Adampur 0.89, Banga 0.72; temporal PDs Abohar 0.92, **Samana 0.40, Dirba 0.39**; static NDs 0.97–1.00; temporal NDs Batala 0.14, Majitha 0.23, Malout 0.30.
- [C] V2 (cut 0.5; c 5% / 20%; rainfall ×0.85 grouping, which moves Bagha Purana, Patran, Dirba, Moonak, Sunam to South-west): all units kept in ≥ 3/4. Abohar static is strict in 4/4. Adampur, Jalandhar-I, Samana, Dirba and all temporal NDs drop at cut 0.5.
- [C] V3: unknown share > 2× group median at Gurdaspur (2.4%), Zira, Batala, Majitha (Majha/Doaba cloud); median clear looks ≈ 12 everywhere except S2 tile-overlap tehsils (≈ 24–26).
- [C] V4: rice share (cal) below group Q1 at Abohar 0.37 (SW Q1 0.52; Chen calibration ×0.58), Dinanagar 0.53, Jalandhar-I 0.41, Adampur 0.59, Banga 0.59, Gurdaspur 0.63, Phagwara 0.65 (Central Q1 0.70). Harvest seen at Abohar 82% and Dinanagar 87% of panel points (group medians 98% / 99%). Within-group Spearman of rice share vs mean burnt share 2020–24: **Central 0.70, South-west 0.63** (p < 0.01).
- [C] V5: no unit harvests ≥ 10 days later than its group. 44–47% of burnt verdicts at Abohar and Talwandi Sabo fall on 20–30 Nov (SW harvest later), so fires after 30 Nov may be missed there; the effect is group-wide.
- [C] V6: VIIRS agrees for 6/8 static PDs (from robust table). CREAMS district percentiles and green-up are in `v6_triangulation.csv` (read pending).
- [C] Final labels (V7 pending): validated PD = Abohar (static + temporal), Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo; PD with caveat = Gurdaspur, Banga; dropped = Samana, Dirba (V1 fail). Note: under the [P] rule a V4 flag alone still gives "validated PD".
- Side finding [P]: the 19 Central tehsils in the S2 tile overlap (about 2× clear looks; Patiala, Sangrur, Fatehgarh Sahib, Ludhiana) have more negative trends than the rest (median −1.1 vs +0.2 %/yr vs group; Mann–Whitney p = 0.08). The top 6 temporal fallers are all overlap tehsils. Look density may bias the trend; it is confounded with geography.
- V7: `outputs/pd/validation/v7/label_tool.html` built: 120 points (20 × Abohar, Dinanagar, Samana, Phagwara, Zira, Lehra), 2023, 12–32 clear looks per point, blind (tehsil and verdict only in `points_meta.csv`). Awaiting Soham's labels → save `v7_labels.csv` there → `pd_visual_package.py --score` → rerun `pd_validate.py`.
- Open [?]: (1) treat low rice share as an artefact (mask) or a structural condition; options include scoring only harvest-confirmed points, or comparing within rice-share bands. (2) Whether to test the tile-overlap effect (thin the looks to one orbit). Both are new steps and need Soham's OK.
