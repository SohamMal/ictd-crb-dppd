# Positive deviant identification
**DPPD position:** Stage 2 › Positive Deviant Identification · **Status:** Not started · **Last updated:** 2026-10-06

## In plain words
Once groups are frozen and each tehsil has a burn score, we look inside each group for tehsils that burn clearly less than their peers, and do so consistently across years rather than in one lucky season.

## Technical summary
- **Constraint [C]:** no residual-based identification (Prof. Aaditeshwar). Direct within-group comparison of the performance metric.
- **Candidate rule [P]:** within each frozen group, bottom ~10–20% (or z ≤ −1) of burn share in ≥2 of 3 years (2022–24) and on the 3-yr mean. Check thresholds against the DPPD handbook (pp. 63–66).
- Also flag **negative deviants** (worst burners) as a Stage 3 contrast. Dhar Kalan (outlier) handled separately.
- **Open [?]:** A1 §2.5 "Second Deviant Pass" (unapproved); A1 Mann-Kendall trend layer (keep or drop).

## Log (append-only, chronological)
### 2026-10-06 — File created
**Plain:** Placeholder; planned for 13 Oct.
**Technical:** Depends on `2.2/task_clustering.md` (frozen groups) and `2.1/task_tehsil_burn_metric.md`.

### 2026-10-10 — Temporal deviance added to the method (Basma's first mail)
**Plain:** At the start of the project Basma suggested looking for tehsils that *cut* burning faster than their group over five years, not only those that burn least. Each tehsil is then compared with its own past, so things we could not measure (soil, farm size, local enforcement) cancel out. Soham decided this must be part of our method.
**Technical:**
- Source: Basma Albanna, first advisory mail (project start; exact date not recorded). Points: (1) drop fire counts, use burnt area / rice area per unit per year from BAIS2 + TCB; (2) district too coarse, S2 allows village level; (3) group on structural conditions first, keep hypothesised drivers out; (4) **temporal deviance**: "who reduced burning faster than the group's average over the past five years, not who is lowest"; each unit becomes its own control, so unmeasured within-group structural variance drops out; (5) related studies on the same population (early-sown wheat; zero tillage vs burning).
- [C] Soham: temporal deviance is a mandatory part of the methodology.
- [?] Open design: static + temporal side by side, or temporal as primary; trend measure (slope vs first/last-year change; relation to the A1 Mann-Kendall layer); 5 seasons 2020–24 already fixed in `2.1/task_tehsil_burn_metric.md`; check against Prof.'s "no residual-based identification" rule (a trend vs the group average is a direct comparison, not a regression residual, but confirm).
- Dependency: temporal deviance needs a burn measure that separates burning from ploughing. "Stopped burning, started ploughing" is the change it looks for, and the current S2 season-long detector scores both as burnt (`2.1/task_burn_detection.md`, 2026-10-09).

### 2026-10-11 — Static and temporal run alongside
**Plain:** We will report both "who burns least in its group" and "who cut burning fastest compared with its group". A tehsil that is good on both is the strongest positive deviant.
**Technical:** [C] Soham: static + temporal side by side (not temporal-only). Open [?]: trend measure; how to combine the two lists.

### 2026-10-23 — PD rules fixed and coded; dry run on the VIIRS backup measure
**Plain:** While the main burn measure runs, we fixed the PD rules and wrote the code. We tested it on the fire-count backup. **Static:** a tehsil is a PD if its average burning is far below its group (the handbook's 1.5×IQR rule, as in Basma's Egypt case) and it is in the group's lowest quarter in at least 4 of 5 years. No tehsil is that extreme, so the weaker "near-PD" tier (lowest 10% and consistent) is what gets flagged: Doaba tehsils (Jalandhar I/II, Phagwara, Adampur, Banga, Dinanagar) in Central and Abohar and Sardulgarh in South-west. **Temporal:** a tehsil's 5-year trend line is compared with the group's typical trend. This mostly picks *heavy* burners that fell fastest (Barnala, Zira, Mehal Kalan, Mansa). Low burners cannot fall much in absolute terms, so static PDs and temporal PDs never overlap. We need to decide whether that is acceptable or whether the trend should be measured relative to each tehsil's own level.
**Technical:**
- [C] Soham: static = 5-season mean < Q1 − 1.5×IQR (within group) AND ≤ group Q1 in ≥ 4/5 seasons; near-PD fallback = bottom 10% of mean + same consistency. Temporal = Theil–Sen slope − group median slope, PD if < Q1 − 1.5×IQR, near-PD = bottom 10%. NDs are the mirror image. Plains (merged 81) grouping is **report-only** (`survives_plains`), not a filter.
- Code: `Code/pd/pd_identify.py --measure viirs` → `outputs/pd/viirs/pd_table.csv`, `pd_summary.csv`. Groups from `outputs/grouping/FROZEN_groups.csv` (Central 63, South-west 18; Foothills and Outlier excluded). Adding the main measure = one new entry in `MEASURES`.
- VIIRS dry run (fires per 1,000 ha rice, 2019–2023): static 1.5×IQR PD = 0 in both groups (Q1 − 1.5×IQR < 0 with a floor at 0). Near-PD: Central 6 (Dinanagar 0.23, Jalandhar-I 0.42, Jalandhar-II 0.75, Phagwara 0.76, Adampur 0.86, Banga 0.86; all 5/5 years in Q1), SW 2 (Abohar 1.07, Sardulgarh 3.94). Temporal PD: SW 3 (Mansa, Rampura Phul, Guruharsahai); Central near-PD 6 (Samana, Patran, Bagha Purana, Mehal Kalan, Zira, Barnala). PD on both = 0.
- Reading [P]: (1) the static list matches the known low-burning Doaba belt, which is a sanity pass but may itself be structural (different rotations) → check at validation. (2) The absolute slope rewards heavy burners (level effect); 4 temporal near-PDs are also static near-NDs. (3) VIIRS trends are contaminated by overpass evasion (fires collapse 2024–25), so the temporal result here tests the code only, not a finding.
- Open [?]: temporal on absolute vs level-adjusted change; whether near-PDs are reported as PDs (labelled weak) given that 1.5×IQR flags nobody.

### 2026-10-23 — Rules moved to log scale; trend made relative; near-PD renamed candidate-PD
**Plain:** Soham asked for a relative trend and objected that the rule should find PDs. The strict rule failed because burning cannot go below zero and a few tehsils burn very heavily. That pushes the raw cut-off below zero (Central −5.76), so nobody could pass. All rules now work on a log scale, where halving counts the same at any level. This also makes the trend relative (% change per year compared with the group). On VIIRS, Abohar is now a strict static PD. The fastest relative fallers are low-to-mid burners (Gurdaspur, Khanna, Fatehgarh Churian, Amloh, Kalanaur, Amritsar-I; Mansa, Malout in SW), not only heavy burners. The bottom 10% are reported as "candidate PDs", which the validation step and fieldwork confirm or reject.
**Technical:**
- [C] Soham: relative trend; log-scale rules; candidate-PD tier. Supersedes the 2026-10-23 absolute-slope temporal rule and the "near-PD" label.
- Implementation: value → log(value + c), c = 0.10 × group median of tehsil means (per grouping run). Static fence on log mean; temporal = Theil–Sen slope of log(value + c) − group median; `pct_per_year_vs_group` = 100·(exp(slope_dev) − 1). Fence in the merged Plains run uses its own c.
- VIIRS 2019–2023 result: static PD SW 1 (Abohar); candidate-PD Central 6 (Doaba belt + Dinanagar, as before), SW 1 (Sardulgarh). Temporal candidate-PD Central 6 (Gurdaspur −21%/yr vs group, Khanna −20, Fatehgarh Churian −19, Amloh −15, Kalanaur −14, Amritsar-I −12), SW 2 (Mansa −10, Malout −9); temporal ND Central 1 (Banga +38). Strict temporal PD = 0. PD on both = 0.
- Scratch test without the offset (log of the raw mean) also made Dinanagar a strict PD (fence 0.32); with c = 10% of the group median it falls just short → result is sensitive to c [P]: check c ∈ {5%, 10%, 20%} on the main measure.
- Reading [P]: Gurdaspur, Kalanaur and Fatehgarh Churian are low burners (5/5 years in Q1) and are also falling fast, so they are close to "good on both" (static rank just outside the bottom 10%). VIIRS trends are still contaminated by overpass evasion, so this remains a code test.

### 2026-10-28 — PD identification on the final S2 measure: 8 robust static PDs, 3 robust temporal PDs; Abohar is a PD on both
**Plain:** We ran the PD rules on the new burn measure twice: on 2020–2024 (main) and on 2020–2023 (without the doubtful 2024 season). A tehsil counts as a **robust** PD only if both runs flag it. **Lowest burners (static), 8 robust:** in Central, Dinanagar, Gurdaspur, Phagwara, Adampur, Jalandhar-I and Banga (burnt share 0.21–0.34 against a group median of about 0.62); in South-west, Abohar and Talwandi Sabo. Six of the eight were also flagged by the VIIRS fire counts, an independent source. **Fastest to cut burning (temporal), 3 robust:** Abohar (about 11% per year faster than its group), Samana (9%) and Dirba (8%). **Abohar is the only tehsil that is both a low burner and a fast reducer**, and it is a strict PD (beyond the IQR fence), not just a candidate. Things to check at validation: (1) the static PDs are mostly the Doaba belt, which may differ structurally (other crop rotations). (2) Dinanagar burns least but its burning is rising (temporal candidate-ND). (3) Talwandi Sabo's burning rises 14.5% per year faster than its group in the main run, and it falls away under the Plains grouping. **Robust negative deviants** (for the Stage 3 contrast): Lehra, Zira, Moonak and Guruharsahai burn most. Batala, Majitha and Malout are increasing fastest.
**Technical:**
- [C] Soham (2026-10-28): main = `s2rf` (`outputs/burn_tehsil_rf/tehsil_burn_measure.csv`, `burnt_share`, cut 0.786), seasons 2020–2024; sensitivity = `s2rf_2023` (2020–2023); robust = flagged (PD or candidate-PD; ND or candidate-ND) in both runs, same rule.
- Code change: `pd_identify.py` consistency rule generalised from ">= 4 seasons" to "all seasons but one" (`MAX_SEASONS_MISSED = 1`; 4/5 as before, 3/4 for the 4-season run) [P → applied; same result for 5 seasons, VIIRS output unchanged]. New `Code/pd/pd_robust.py` → `outputs/pd/robust/robust_deviants.csv`. Run outputs `outputs/pd/s2rf/`, `outputs/pd/s2rf_2023/`.
- [C] Counts, main run (Central / SW): static PD 1/1, candidate-PD 5/1, candidate-ND 5/2; temporal PD 1/0, candidate-PD 5/2, ND 0/1, candidate-ND 6/1. 2020–23 run: static PD 0/1, candidate-PD 6/1, candidate-ND 6/2; temporal PD 1/1, candidate-PD 5/1, ND 0/3, candidate-ND 6/0.

| Tehsil | Group | Robust as | Mean share 2020–24 | Main static / temporal | 2020–23 static / temporal | %/yr vs group (main) | Plains | VIIRS static / temporal |
|---|---|---|---|---|---|---|---|---|
| Abohar | SW | PD static + temporal | 0.338 | PD / cand-PD | PD / PD | −11.1 | ✔ | PD / – |
| Dinanagar | C | PD static | 0.212 | PD / cand-ND | cand-PD / cand-ND | +6.5 | ✔ | cand-PD / – |
| Gurdaspur | C | PD static | 0.289 | cand-PD / – | cand-PD / – | +2.3 | ✔ | – / cand-PD |
| Phagwara | C | PD static | 0.300 | cand-PD / – | cand-PD / – | +6.0 | ✔ | cand-PD / – |
| Adampur | C | PD static | 0.302 | cand-PD / – | cand-PD / – | −4.9 | ✔ | cand-PD / – |
| Jalandhar-I | C | PD static | 0.308 | cand-PD / – | cand-PD / – | −1.4 | ✔ | cand-PD / cand-ND |
| Banga | C | PD static | 0.342 | cand-PD / – | cand-PD / – | +5.6 | ✔ | cand-PD / ND |
| Talwandi Sabo | SW | PD static | 0.504 | cand-PD / ND | cand-PD / – | +14.5 | ✘ | – / – |
| Samana | C | PD temporal | 0.634 | – / PD | – / cand-PD | −9.1 | ✔ | – / – |
| Dirba | C | PD temporal | 0.706 | – / cand-PD | – / cand-PD | −8.2 | ✔ | cand-ND / – |

- [C] Robust ND: static Lehra 0.790, Zira 0.797, Moonak 0.810 (C), Guruharsahai 0.895 (SW); temporal Batala (+9.9%/yr), Majitha (+7.7) (C), Malout (+9.3; VIIRS temporal cand-PD) (SW).
- [C] Flagged in one run only (not robust): main only — Patiala, Amloh, Bhawanigarh, Nabha (temporal cand-PD), Jaitu (temporal cand-PD); 2020–23 only — Payal (temporal PD), Khanna, Khamanon, Dera Baba Nanak, Kotkapura (temporal cand-PD). Temporal flags are less stable than static ones (dropping one season changes a 5-point trend).
- Reading [P]: static robust list ≈ VIIRS dry-run list (Doaba + Dinanagar; Abohar), so it is not an artefact of one sensor. Next = PD validation: structural check of the Doaba belt (crop rotation, rice share inside the group), data quality (clear looks, unknown points) at the PDs, cut 0.5 sensitivity, and the Dinanagar / Talwandi Sabo conflicts.

### 2026-10-29 — Strict IQR rule added beside the old rule: one strict PD (Abohar, static), three borderline PDs, no strict ND
**Plain:** Soham pointed out that "bottom 10% of the group" only means a tehsil is among the lowest. It does not show a tehsil is far from normal, which is what a positive deviant should be. Both rules are now reported side by side. **Old rule** (unchanged): flagged as PD or bottom-10% candidate in both runs. **Strict rule:** a PD must be beyond the IQR fence (Q1 − 1.5×IQR on the log scale) in **both** runs (2020–24 and 2020–23). "Borderline" = beyond the fence in one run and in the bottom 10% in the other. Under the strict rule: **Abohar is the only PD** (lowest burner in South-west, beyond the fence in both runs). **Borderline PDs:** Dinanagar (lowest burner; misses the 2020–23 fence by 0.001), Abohar (fastest reduction; misses the main fence by 0.3 %/yr), Samana (fastest reduction; misses the 2020–23 fence by 0.3 %/yr). The Doaba cluster (Gurdaspur, Phagwara, Adampur, Jalandhar-I, Banga) burns about half the group median, but it sits together as a group and so counts as part of the normal spread. It is reported as a low-burning cluster to examine (possibly structural), not as PDs. No strict negative deviant; Malout is a borderline ND (burning rising fastest).
**Technical:**
- [C] Soham (2026-10-29): keep both rules in the output. `Code/pd/pd_robust.py`: columns `old_rule` (was `robust`) and `strict_rule`; `strict_{rule}_{PD,ND}` = exact "PD"/"ND" in both runs; `border_{rule}_{kind}` = exact flag in one run and PD-or-candidate in the other. No new threshold. → `outputs/pd/robust/robust_deviants.csv`. `pd_identify.py` unchanged (it already labels PD vs candidate-PD).
- [C] Fences (burnt share; main / 2020–23): Central static 0.225 / 0.206 (median 0.61 / 0.58), SW static 0.454 / 0.376 (median 0.73 / 0.70); Central temporal −8.9 / −11.4 %/yr vs group, SW −11.4 / −3.7.
- [C] Strict-rule values: Abohar static 0.338 / 0.327 (✔ / ✔); Dinanagar 0.212 / 0.207 (✔ / ✘); Abohar temporal −11.1 / −17.4 (✘ / ✔); Samana −9.1 / −8.6 (✔ / ✘); Payal −15.4 in 2020–23 only (not candidate in main → not borderline). ND: Malout temporal (cand-ND / ND) borderline; Bathinda, Budhlada ND in 2020–23 only.
- Reading [P]: report strict PDs as the main result and the old-rule list as the broader "low-burning" set. Stage 3 then compares Abohar (+ borderline Dinanagar, Samana) with the NDs, and studies the Doaba cluster as a structural question.
