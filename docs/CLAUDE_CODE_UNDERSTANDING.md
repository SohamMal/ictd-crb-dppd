# Claude Code — Understanding Check (for confirmation against claude.ai web project)

_Written 2026-10-06 by Claude Code after reading `CLAUDE.md`, all `docs/*.md`, and inspecting the local repo. Purpose: Soham pastes this into the claude.ai "ICTD" project and confirms/corrects each point. Nothing here changes any decision; it is a read-back._

Legend: **[C]** I understand this as confirmed · **[P]** I understand this as proposed/provisional · **[?]** I am unsure or found a mismatch — please confirm · **[V]** I verified this in the local files.

---

## 1. Project in one paragraph
IIT Delhi ICTD (COL7761) project applying **Data-Powered Positive Deviance (DPPD)** to **paddy stubble burning** in Punjab (Haryana later). We find tehsils that burn significantly less than **structurally similar peers**, then find out why, to give actionable guidance to NGOs/government. Deadline: **end of 22 Oct 2026** (16 days from today). [C]

## 2. People
| Role | Who | Note |
|---|---|---|
| Student / owner | Soham | GEE, satellite, Python [C] |
| Partner | — | **[C] Solo project.** Aryan Rana is not on this project (village rice CSVs originally came from him) |
| Supervisor | Prof. Aaditeshwar Seth | Approves design decisions [C] |
| Advisors | Basma Albanna (DPPD co-author, founder-level authority), Andreas (Egypt Nile Delta rice-burning DPPD) | Follow-up call not yet held [C] |

## 3. Where we are in the DPPD pipeline
- Stage 1 (Problem–method fit): done via Assignment 1. [C]
- Stage 2 Step 1 (Performance measurement): method locked (BAIS2+TCB), **deliberately paused** until grouping is frozen. [C]
- **Stage 2 Step 2 (Homogeneous grouping): ACTIVE.** [C]
- Stage 2 Steps 3–4 (PD identification, validation), Stage 3 (predictors): not started. [C]
- Assignment 2 (due 20 Sep): **[C] submitted.**

## 4. Hard rules I will follow
1. Grouping variables = structural, non-transferable only (climate, soil, rice, water, terrain, CI). [C]
2. Hypothesised drivers (CRM machines, mandi access, etc.) never enter grouping — Stage 3 only. [C]
3. Burning outcomes never used to build groups. [C]
4. No adding/dropping grouping variables (or soil descriptors) without your confirmation. [C]
5. Every number must be reproducible in code; the 3 Oct ChatGPT numbers (silhouette 0.287, ARI 0.572, 25/14/57) are **not citable** until rerun. [C]
6. Docs: `project_tracker.md` append-only; one `sub_journeys/task_*.md` per task; write only when told; show diffs first; label confirmed vs proposed. [C]
7. Always go through bridge files for 2011-Census ↔ current-LGD joins; `tehsil_bridge_detailed_punjab.csv` is excluded as unreliable. [C]

## 5. Performance measure (paused)
- Sentinel-2 single post-harvest snapshot, **BAIS2 (Filipponi red-edge) + Tasseled Cap Brightness**, cropland/paddy masked. [C]
- Validation: 380 fields, stratified 5-fold CV → acc 95.53%, recall 98.11%, F1 0.9683; NBR 81.32% / 82.26%. [C, reported]
- Rejected: NBR pre/post (harvest mimics burn), FIRMS/VIIRS (~3.67× undercount). [C]
- Ground-truth provenance must be confirmed before external citation. [C]
- **[C] Tehsil-level burn metric NOT yet decided.** Candidate: burnt share of rice area (suggestion only). Revisit after grouping freezes.

## 6. Homogeneous grouping — current design
**Unit:** 97 current Punjab tehsils (LGD codes), 23 districts. [C] [V: 97 unique codes, 23 districts]

**Six equally weighted dimensions (1/6 each):** [P — design fixed, weights need advisor sign-off]
| Dimension | Variable in master | Transform | Status |
|---|---|---|---|
| Cropping intensity | `CI_3yr_pooled` (2022–24) | z-score | [C]; threshold QA open |
| Rice | `chen_rice_area_ha_2022` | log1p + z | **[P] to be replaced by rice share = rice area / tehsil polygon area** (script patch pending) |
| Rainfall | `mean_monsoon_rainfall_mm` (CHIRPS Jun–Sep, 2020–25) | z | [P] prototype window; ~15-yr intended |
| Terrain | `elevation_mean`, `slope_mean` | log1p + z | [C] |
| Groundwater | `mean_extraction_pct_2022` | z | **[?] year 2022 vs 2025 open** — masters currently use 2022 [V] |
| Soil | 8 categorical: particle size, drainage, texture, depth, pH, salinity, sodicity, erosion | categorical / one-hot | [C]; one drainage value missing → `Unknown` |

**Dropped:** NARP agro-climatic zones (district-based) → replaced by rainfall + terrain; gross cropped area; rainfall variability; temperature. Dropping temperature/variability is an **untested assumption**. [C decision, needs advisor sign-off]

**Method:** dimension-balanced Gower (numeric = range-normalised |diff|, categorical = 0/1 mismatch; average within dimension, then equal-weight across 6) → average-linkage HAC on 97×97 matrix → silhouette, bootstrap ARI (80%, 300 runs), one-factor-at-a-time sensitivity. [P]

**Provisional result (unverified, ChatGPT):** Dhar Kalan (Pathankot) singleton outlier at every k → kept as contextual outlier; remaining 25/14/55/2 → 2-tehsil branch (Adampur, Jalandhar-II) merged into 55 → **G1=25, G2=14, G3=57**. G1 least stable. [P]

## 7. What I verified in the local files (2026-10-06)
- Tracker renamed: `docs/project_tracker (3).md` → `docs/project_tracker.md`. [V]
- Grouping masters present in `Data/`: `..._raw_97tehsils.csv`, `..._transformed.csv`, `..._encoded.csv` — 97 rows each. [V]
- Raw master: only missing value = 1 `dominant_drainage`; encoded file has `dominant_drainage_Unknown`. [V]
- Drainage distribution: Well 75, Moderately well 14, Excessive 6, Poor 1, missing 1. [V] → several soil one-hot columns are near-constant; relevant to the "drop useless descriptors" rule.
- CI_3yr_pooled range 179.8–237.5 (mean 203.6); rice 1,849–108,663 ha. [V]
- `slope_mean` range 0.0–1.0 (mean 0.2) looks low for Shivalik tehsils (e.g. Dhar Kalan). Data-quality check, **low priority** (terrain likely replaced by zones); not a handoff gap.
- Rice script `Data/Rice/calc_chen2022_rice_area_current_lgd.py` exists and enforces 97 unique output rows. [V]
- Per-variable masters and scripts exist for CI, rice, rainfall, terrain, groundwater (2022 & 2025), soil, LGD bridges. [V]

## 8. Do we have everything?
**Enough to proceed** with the next two tasks (rice-share patch, clustering rebuild). [V]
Still missing locally (non-blocking for now):
- Advisor question deck `DPPD_Crop_Residue_Burning_Questions_for_Prof__Aaditeshwar.pptx`
- ChatGPT context files from the 3 Oct session (only useful to compare against the rebuild)
- GEE JS scripts (rainfall, CI, terrain, burn detection) — needed later for burn-measure scaling and report reproducibility
- `sub_journeys/` folder — deliberately deferred

## 9. Immediate plan (in order)
1. Patch rice script → tehsil polygon area + rice share; rerun; update masters (diff shown first).
2. Groundwater year decision (likely Prof.); default to 2022 in code with a switch.
3. Clustering pipeline in Python: Gower → HAC → silhouette → bootstrap ARI → OFAT sensitivity (no logs, GW 2025, ±15% weights, drop-one-dimension).
4. Compare with provisional 25/14/57 + Dhar Kalan; inspect unstable G1; freeze or revise.
5. Scale BAIS2+TCB to tehsil → PD identification → validation → predictors → report.

## 10. Open questions (carried from tracker §5 / DECISIONS §3)
1. Rice: Chen 2022 snapshot vs SAR 2023–24 extension.
2. Groundwater 2022 vs 2025.
3. Zones → rainfall+terrain, and dropping temperature/variability: acceptable or test first?
4. Equal weights: acceptable + justification.
5. Punjab-only now: acceptable?
6. Basma's village-resolution suggestion vs tehsil unit.
7. Section 2.5 "Second Deviant Pass" vs Prof.'s rule against residual-based PD identification.
8. Placeholder village codes `8xxxxx` (800166, 800252); Mewat vs Nuh.
9. Ground-truth provenance before external citation.

## 11. Please confirm / correct
- [x] Solo project (§2)
- [x] Assignment 2 submitted (§3)
- [x] Burn metric undecided (§5)
- [ ] Slope check — low priority (§7)
- [ ] Anything in §6 that the web project remembers differently (esp. the soil descriptor set and transforms)
- [ ] Any decision made in claude.ai after 5 Oct that is not reflected here

---

## 12. Superseded by supervisor feedback (2026-10-06)
See `HANDOFF_UPDATE_2026-10-06.md` (wins over this file and older handoff docs where they conflict). Summary:
- **[C] Groundwater = 2022 only**; 2025 only as sensitivity. (Overrides §6 "[?] year open".)
- **[C] Rice = Chen 2022 fixed**; SAR pipeline retired. Rice-share patch still pending.
- **[C] Punjab only**; Haryana later. **[C] Hierarchical clustering endorsed.**
- **[C] Agro-climatic zones REPLACE rainfall + terrain.** Dimension set provisional (5 or 6) until tehsil-level/richer zone data is found. Zone encoding (categorical label vs numeric attributes) **[?]**.
- **[P] Equal weights**: Soham researching justification.
- **[C] Soil in Gower = original 8 categorical columns (0/1 mismatch)**, not the one-hot `..._encoded.csv`. Dropping near-constant descriptors only with evidence + Soham's approval.
- Clustering code must take a **configurable dimension list**; run current six as baseline first.
- Note: Dhar Kalan's outlier status is likely terrain-driven (elevation 578 m vs mean 244 m); may change once terrain is replaced.
