# PROJECT TRACKER — DPPD Crop Residue Burning (Punjab & Haryana)

**Rule: APPEND-ONLY.** Never overwrite or erase entries. Add updates chronologically at the bottom (§7 Update Log). §1–§6 are the baseline snapshot as of **2026-10-05** (reconstructed from claude.ai session notes at handoff to Claude Code); after this date, change status by appending to §7, not by editing above.

Legend: **[C]** confirmed · **[P]** proposed / provisional · **[?]** unknown / not recorded

---

## 1. Architecture & timeline

**Pipeline (canonical DPPD):** Stage 1 Fit → Stage 2 {Performance Measurement → Homogeneous Grouping → PD Identification → PD Validation} → Stage 3 Predictors.

**Technical architecture (current design)**
- Performance measure: Sentinel-2 post-harvest snapshot, **BAIS2 + Tasseled Cap Brightness (TCB)**, cropland/paddy masked. [C]
- Grouping unit: **97 current Punjab tehsils** (LGD codes). [C for prototype; earlier plan of 151 units across both states was proposed, now superseded for Punjab]
- Mixed-resolution inheritance: each variable kept at native resolution, inherited downward via crosswalks (approved by Prof. Aaditeshwar). [C]
- Grouping: 6 equally weighted dimensions → dimension-balanced Gower distance → average-linkage HAC. [P: provisional, not frozen]
- Scope: **Punjab only for now**, Haryana repeated after pipeline works. [P: awaiting advisor confirmation]

**Timeline**
| Date | Event |
|---|---|
| Sep 2026 (early) | Assignment 1 (ACM sigconf position paper) complete; structure Abstract→Problem→Proposed System 2.1–2.5→Theory of Change→Feasibility→Literature→References |
| Sep 2026 | Update presentation; Prof. Aaditeshwar: "good clarity on methodology" |
| 20 Sep 2026 | Assignment 2 due (extend A1 with technical methodology, dataset description, preliminary results) |
| Sep 2026 | Grouping data collection across variables; SHRUG village boundaries locked; GEE pipelines (rainfall, SAR rice) |
| 3 Oct 2026 | Grouping moved to 97-tehsil master files; ChatGPT-produced clustering reviewed; rebuild-in-code decided |
| 5 Oct 2026 | Handoff to Claude Code |
| **22 Oct 2026 (end)** | **Target: whole project complete** |

## 2. Modules / tasks — status

| Module | Status | Journey file |
|---|---|---|
| Burn detection (BAIS2+TCB) | **Completed** (validated); scaling to tehsil paused | `task_burn_detection.md` |
| Village boundaries & crosswalks | Mostly done (Punjab); Haryana behind | `task_village_boundaries_crosswalks.md` |
| Cropping intensity (tehsil, satellite) | Methodology locked; master has `CI_3yr_pooled` for 97 tehsils; threshold tuning unresolved | `task_cropping_intensity.md` |
| Rice area | Chen 2022 in master; **switch to rice share pending rerun**; SAR 2022–24 track validated but status vs Chen-only decision open | `task_rice_area.md` |
| Rainfall | Prototype in master (2020–2025 mean); 15-yr window planned | `task_rainfall.md` |
| Terrain | Done (2026 terrain file, all 97 covered) | `task_terrain.md` |
| Groundwater | Cleaned; **year undecided (2022 vs 2025)** | `task_groundwater.md` |
| Soil | 8 descriptors in master; extraction details thin in notes | `task_soil.md` |
| Homogeneous grouping / clustering | **Active.** Provisional 25/14/57 + Dhar Kalan outlier; rebuild in code pending | `task_homogeneous_grouping_clustering.md` |
| PD identification, validation, predictors | Not started | — |
| Haryana replication | Deferred | — |

## 3. Locked methodological decisions (summary)
- Primary burn proxy BAIS2+TCB; FIRMS/VIIRS dropped (≈3.67× undercount vs Sentinel-2).
- Single post-harvest snapshot with cropland mask; NBR pre/post change detection rejected.
- Grouping variables are structural only; burning outcomes never used for grouping.
- Variable set (6 dimensions): cropping intensity, rice, rainfall, terrain, groundwater, soil. Gross cropped area, rainfall variability, temperature and other agro-climatic variables dropped. **Do not add variables without confirming.**
- Agro-climatic zones (NARP) replaced by mean rainfall + terrain because zones follow district boundaries.
- Equal 1/6 weight per dimension (design choice; must be justified in report).
- Any variable/descriptor that is not useful for grouping should be dropped, since every one affects distances.

## 4. Decision log (append-only)
`Date | Decision | Reason | Impact`

| Date | Decision | Reason | Impact |
|---|---|---|---|
| ≤Sep 2026 | D9: BAIS2 + TCB as primary burn proxy | NBR gave 81.32% acc / 82.26% recall; BAIS2+TCB gave 95.53% / 98.11% (F1 0.9683, 380 fields, stratified 5-fold CV). Earlier poor results were implementation bugs (wrong BAIS2 formula) | Performance measure fixed |
| ≤Sep 2026 | Drop FIRMS/VIIRS | ~3.67× undercount vs Sentinel-2 in Punjab/Haryana | Satellite-only detection |
| ≤Sep 2026 | Reject NBR pre/post change detection | Harvest itself produces a spectral shift indistinguishable from burning | Use post-harvest snapshot + cropland mask |
| ≤Sep 2026 | Add Homogeneous Grouping step | Basma's feedback: original design skipped an official DPPD step | Stage 2 Step 2 now the active work |
| Sep 2026 | Mixed-resolution architecture approved | Variables exist at village/tehsil/block/district; forcing one level loses information | Native resolution per variable, inherit downward |
| Sep 2026 | SHRUG v2.2 as village boundary source | Punjab 12,808 / Haryana 6,998 villages, geometry checks passed, EPSG:4326, PC11 coding | Village base layer fixed |
| Sep 2026 | HARSAC soil ruled out | Manual form only, no bulk export, no Punjab equivalent | Soil from NBSS&LUP (symmetric coverage) |
| Sep 2026 | Majority-area-overlap to resolve multi-zone villages | Largest intersection wins | Applies if zone-based variable used |
| Sep 2026 | Rainfall window 15 yr (2006–2020) instead of 30-yr WMO | Balance stability vs recent monsoon patterns; flag as limitation | **Superseded 3 Oct for prototype** (2020–2025); 15-yr window remains intended for final |
| Sep 2026 | Tehsil CI via village-level A1/A2/A3 summed then CI formula once | Averaging percentages is wrong | Sum-then-divide rule |
| Sep 2026 | Generate 2022–24 rice via Sentinel-1 SAR rather than fix Chen/Aryan 2022 column | Aryan's file 2022 column = stale copy of 2020 (98.6% identical; standalone 2022 file byte-identical) | SAR track created; later partly overtaken by 3 Oct decision |
| 3 Oct 2026 | Grouping unit = 97 current Punjab tehsils | Tehsil is middle ground between ~20k villages and 41 districts | Masters built at 97 tehsils |
| 3 Oct 2026 | Dropped gross cropped area and rainfall variability | Too much work at tehsil level / mean rainfall only | 6-dimension design |
| 3 Oct 2026 | Keep Chen rice area for grouping; do **not** rebuild with SAR | Treated as structural spatial trait | SAR pipeline not needed for grouping (still available) |
| 3 Oct 2026 | Rainfall = 2020–2025 mean for prototype | Speed; expand to ~15 yr after prototype works | Revisit before freezing |
| 3 Oct 2026 | Switch rice dimension from absolute hectares to **rice share of tehsil area** | Absolute area is confounded by tehsil size | Script patch + rerun pending |
| 3 Oct 2026 | Rebuild clustering reproducibly in code | Earlier results from ChatGPT without code | Reproduction is next task |
| 3 Oct 2026 | Dhar Kalan (Pathankot) kept as contextual outlier, not a peer group | Singleton at every k | 96 tehsils across 3 groups |
| 3 Oct 2026 | Merge Adampur + Jalandhar-II 2-tehsil branch into the 55 group | Too small to be a peer group | Provisional groups 25 / 14 / 57 |
| 2026-10-22 | Burn detector tested on ground-known ploughed fields (Walker/J-PAL 2019 series) | 81% of ploughed-not-burnt fields called "burnt" within 10 days (burnt: 98%); radar filter (Branch B) did not fix it | Burn measure as built would hide positive deviants; next lever is early brightness on near-daily imagery (Planet, pending) |
| 2026-10-22 | Basma's S1 filter tested on single fields (CEEW 2021; 27 probable-ploughed vs 262 ground-burnt) | Radar falls on ploughed fields; rule calls 7% of ploughed "ploughing" but drops 33% of real burns | Radar route (Branch B) closed pending Planet labels; burn measure still needs a ploughed-vs-ash fix |

## 5. Open questions
**For Prof. Aaditeshwar** (deck: *DPPD Crop Residue Burning – Questions for Prof. Aaditeshwar*)
1. (a) Can rice area stay a fixed 2022 snapshot, or extend to 2023–24 via own SAR pipeline (lengthy)? (b) Groundwater year 2022 or 2025? (switching changes grouping)
2. Is replacing agro-climatic zones with mean rainfall + terrain, and dropping temperature/rainfall variability (untested judgement), acceptable — or test the assumption first?
3. Is equal weighting acceptable, and how to justify it in the report? (±15% weight changes shifted grouping noticeably)
4. Is a Punjab-only study acceptable for now, Haryana to follow?
5. What to do about the follow-up call with Basma and Andreas (not yet held)?

**Other open items**
- Section 2.5 "Second Deviant Pass" (team extension) — sign-off needed; risks conflicting with Prof.'s rule against residual-based deviant identification.
- Duplicate placeholder village codes 800166, 800252 and other `8xxxxx` codes — include/exclude decision pending.
- Mewat vs Nuh district-name judgement call.
- Confirm ground-truth dataset provenance before citing results externally.
- Hand-check CI threshold issues and high-swing tehsils (see CI journey).

## 6. Key learnings
- Collect data at finest resolution; design grouping to what the data honestly supports.
- BAIS2 needs the Filipponi red-edge formula and verified TCB coefficients.
- A district stereotype (Fazilka = low rice) was wrong; check against data before assuming.
- ID-vintage mismatch (2011 Census vs current LGD) is the recurring merge hazard; always go through bridge files.

---

## 7. Update Log (append below this line, chronological)

### 2026-10-05 — Handoff baseline
- Baseline snapshot generated from claude.ai project notes for transfer to Claude Code. Known gaps (not in notes): contents of scripts, GEE asset names other than `projects/ictd-507010/assets/shrug/shrug_villages`, how CI for the remaining 52 current tehsils was finalised, final groundwater/soil file names.

### 2026-10-06 — Supervisor feedback applied (Oct 2026 meeting, exact date not recorded)
- [C] Groundwater year = 2022 only (grouping built around 2022). 2025 kept only as sensitivity.
- [C] Punjab only for now; Haryana after the Punjab pipeline works.
- [C] Hierarchical clustering endorsed. Rice fixed at Chen 2022; no Sentinel-1 extension to 2023–24.
- [C] Zones now REPLACE rainfall and terrain. Needs tehsil-level/richer zone data; dimension set provisional until found.
- [P] Equal weights: Soham to research justification first; ask Prof. at next meeting if none found.
- Impact: rainfall 15-yr extension and terrain slope check now low priority. Superseded in handoff docs: groundwater year, rice SAR, zones, six-dimension count.
- [C] Solo project (Aryan Rana not on this project). [C] Assignment 2 submitted. [C] Tehsil-level burn metric not yet decided (candidate: burnt share of rice area).
- Tracker renamed `project_tracker (3).md` → `project_tracker.md`. Corrections source: `docs/HANDOFF_UPDATE_2026-10-06.md` (wins over older handoff docs where they conflict).

### 2026-10-06/07 — Rice share; zones; GROUPING FROZEN (3 regions)
- [C] Rice: calc_chen2022_rice_area_current_lgd.py patched (+tehsil_area_ha geodesic, +rice_share_2022, polygon GPKG). rice_share_2022 replaces rice_area_log1p. Env: pyproj 3.6.1, scikit-learn 1.7.2 (newer blocked by Windows Smart App Control).
- [C] Slope data defective (identical values, zero within-tehsil variation) → terrain removed from grouping.
- [C] Zones: NBSS&LUP AESR 2018 polygons (Bhoomi WMS) → tehsil area shares (14.2/2.5/4.1/9.1). Zones replace terrain only; rainfall kept (AESR ≈1:4M cannot separate arid SW from central). Supersedes "zones replace rainfall + terrain".
- [C] Grouping rebuilt in code (Code/grouping/): dimension-balanced Gower (6 dims, equal weights) → average-linkage HAC → silhouette → bootstrap ARI (300×80%) → OFAT sensitivity.
- [C] FROZEN: Central 66 / South-west 16 / Foothills 14 + Dhar Kalan outlier; ARI 0.772, silhouette 0.316 (outputs/grouping/FROZEN_*). SW/central border is a gradient → PDs must hold under both 3-region and 2-group (Plains 82 / Foothills 14, ARI 0.948) groupings. ChatGPT 25/14/57 superseded.
- [C] Groundwater: 2022 final; 2025 dropped entirely (no sensitivity use). Rainfall: 2020–2025 (5-yr) window accepted for now; extension deferred.
- sub_journeys/ created (DPPD stage › step). Next: resolve open QA items (SW rice share check, CI threshold QA, etc.), then Phase B tehsil burn metric (BAIS2+TCB).

### 2026-10-07 — Rice calibrated; CI dropped; GROUPING FROZEN v4
- [C] Chen 2022 over-maps rice in SW/foothills (×1.04–1.71) and under-maps central (×0.76–0.93) vs official district area (Stat. Abstract 2022, 2021-22). Tehsil rice calibrated to official district totals (calibrate_rice_to_official.py); rice_share_2022_cal used for grouping.
- [C] CI dropped: satellite CI ρ=0.18 vs official; GEE script (v2) inflates CI by design (untuned thresholds, monsoon weeds, double-counted long crops); script for 32 tehsils missing. Dropping CI or using official CI changes only 2 borderline tehsils (ARI 0.93). Validated tehsil CI = future work.
- [C] Borderline measure = per-tehsil switching rate + group survival; consensus placement adopted.
- [C] FROZEN v4 (5 dims: rice share cal, rainfall, AESR zone shares, GW 2022, soil): Central 63 / South-west 18 / Foothills 15 + Dhar Kalan; ARI 0.890, silhouette 0.377; borderline Firozpur, Dinanagar, Faridkot. 2-way: Plains 81 / Foothills 15 (ARI 0.981). SW split weight-sensitive (rice/soil ×1.15 → merges) → PDs must hold under both groupings.
- Next: confirm ground-truth provenance, then Phase B (tehsil burn metric). Open risk: Chen rice mask over-includes non-rice in SW/foothills.

### 2026-10-10 — Temporal deviance added; Basma's references reviewed
- [C] Temporal deviance (Basma's first mail: who reduced burning faster than the group average over 5 years) is a mandatory part of PD identification. [C] Runs alongside static (lowest burner); both reported, a tehsil good on both = strongest PD. Trend measure open.
- [C] Basma's cited studies read (CEEW 2025 brief; Naeher & Ziulu 2025; Albanna et al. 2026). They support burnt area over fire counts but none addresses char vs tilled-soil confusion.
- Impact: the burn measure must separate burning from ploughing, otherwise temporal deviance cannot see the behaviour change. Question to Basma/Andreas is now blocking.

### 2026-10-11 — Burn window = official ISRO/CAQM season (15 Sep–30 Nov)
- [C] Performance window changed from 1 Oct–15 Dec to **15 Sep–30 Nov** (ISRO protocol used by CAQM for paddy residue burning counts). Reason: no burning season beyond 30 Nov in official monitoring; defensible in report.
- Evidence: false-flag accumulation drops (60 Punjab spots 2022: 0.80 → 0.73) but CEEW 2021 unburnt fields are already 89% flagged by 15 Nov. Ploughing/sowing for wheat (PAU: by 7–15 Nov) overlaps burning, so char vs tilled-soil separation is still required.
- Impact: all Phase B exports use 15 Sep–30 Nov; mid-November cut rejected (would miss late fires → false PDs in late-harvest tehsils).

### 2026-10-22 — Basma replied; burn detection split into Branch A / Branch B
- [C] Basma: no Egypt experience with ploughed vs burnt. Suggests a Sentinel-1 filter: BAIS2+TCB flags = dated candidates; backscatter rise (ΔVV, ΔVH, Δ(VH−VV)) across the candidate date → ploughing, drop. Validate with a truth × prediction table that includes ploughed-not-burnt fields.
- [C] Folder branches from the 2026-10-12 checkpoint. A = work since then (heat-peak rule, CIMMYT, CREAMS, VIIRS backup) in Code/burn, outputs/burn_*. B = Basma's route in Code/burn_basma, outputs/burn_basma, task_burn_detection_basma.md. Grouping v4 shared.
- Impact: both measures can be compared on the same validation data; the report can present both.

### 2026-10-12 → 10-19 (catch-up, written 2026-10-22) — Branch A: heat-peak window rule built and validated at district level
- [C] 10-12: Prof. Aaditeshwar approved writing to Basma & Andreas (reply came 10-22, see above).
- [C] 10-15/16: Prof.'s suggestion = add heat + read burning as a before/peak/after curve (Whittaker-smoothed). Landsat LST does not separate ash from ploughed soil (headline AUC 0.77 was a sensor/date artefact; ash cooler than soil).
- [C] 10-18: MODIS LST (1 km, daily) vs a 1 km S2 burnt-fraction reference: heat peak tracks burning timing (most-burnt pixels ~+1 °C above region, then −0.6 °C). Emissivity adds nothing. Used for timing only.
- [C] 10-18: Heat-peak window rule (S2 BAIS2+TCB counted only within days of the pixel's MODIS heat peak): random-cropland over-flagging 95% → ~56% (2022); keeps 88–96% of CEEW burnt fields.
- [C] 10-18: CIMMYT 2021/2022 plot survey (burnt + Super/Happy Seeder classes) downloaded; coordinates rounded to 0.01° → 1 km cell validation only. 2021: 74% vs 53% burnt in all-burnt vs no-burn cells (season rule ~98% everywhere); 2022: no separation. Sharper rules (jump, NBR2, peak size) did not help.
- [C] 10-18/19: District validation: vs CREAMS 2020 ρ 0.81 (level +8 pts); 2019 ρ 0.15 (official method changed between years); vs IARI 2022 in-season (till 24 Oct) ρ 0.70–0.76.
- [C] 10-18: Backup measure = VIIRS fire counts per tehsil / rice area: stable ranking (0.92–0.97, 2019–23), matches CREAMS 2019 (0.85) not 2020 (0.43); collapses 2024–25 (−78%, −91%; overpass evasion). Main and backup agree weakly (0.22–0.36).
- [C] 10-19: Foothill over-count not explained by shadows, green crop, non-cropland or heat-peak timing → most likely ash vs ploughed-soil confusion, worst where little real burning. Soham rejected a fire-evidence gate and a soil baseline; chose within-group ranking check: holds for Central (0.48/0.62/0.75) and South-west (0.77/0.77), fails for Foothills (n = 4 districts).
- Open [P]: Foothills PD identification — exclude, or report as low-confidence exploratory. Status of measure: "validated against official district estimates and field surveys, with stated limits"; not field-level validated (W1, 10-22: 81% of ploughed fields flagged).

### 2026-10-23 — Branch A extended; Foothills out of PD identification
- [C] Branch B frozen as a documented negative result (radar filter fails B2–B5; W1 false alarms shared by both branches).
- [C] Foothills (15 tehsils) excluded from PD identification for now; still measured. 81 tehsils ranked (Central 63, South-west 18).
- Impact: measure all 97 tehsils; validate by area-weighted sums at district, full-state and plains-state (minus 4 foothill districts) level.
