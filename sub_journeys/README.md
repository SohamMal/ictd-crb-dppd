# Sub-journeys — index

One file per task, organised by **DPPD handbook stage → step** (`0. Material/DPPD/DPPD_Handbook_Nov_2021.pdf`, contents p. 3).
Stages 4 (Design & Implement Interventions) and 5 (Monitor & Evaluate) are out of scope for this course project and have no folders.

**Rules**
- Append-only. New log entries go at the bottom of the file's *Log*, newest last. Never erase old entries; mark them superseded instead.
- Every file has an **In plain words** part (for a non-specialist) and a **Technical** part (detail for the report's Methodology / Experiments / Results).
- Tags: **[C]** confirmed · **[P]** proposed / provisional · **[?]** not recorded / unknown.
- Entries dated before 2026-10-05 are marked **(reconstructed)**. They were rebuilt from the handoff docs in `docs/`, Assignment 1, and the scripts in the repo. They are not verbatim chat history.
- Files are written/updated only when Soham says so.

## Index

| Stage › Step | File | Status (2026-10-06) |
|---|---|---|
| **1 · Assess Problem-Method Fit** | | |
| 1.1 Problem Definition | `1_Stage1_Assess_Problem_Method_Fit/1.1_Problem_Definition/task_problem_definition.md` | Done (A1) |
| 1.2 Suitability | `1_Stage1_Assess_Problem_Method_Fit/1.2_Suitability/task_suitability.md` | Done |
| 1.3 Feasibility | `1_Stage1_Assess_Problem_Method_Fit/1.3_Feasibility/task_feasibility.md` | Done; scope revised several times |
| 1.4 Desirability | `1_Stage1_Assess_Problem_Method_Fit/1.4_Desirability/task_desirability.md` | Thin; to strengthen in report |
| **2 · Determine Positive Deviants** | | |
| 2.1 Performance Measurement | `2_Stage2_Determine_Positive_Deviants/2.1_Performance_Measurement/task_burn_detection.md` | Method locked + validated; ground truth = CEEW Zenodo (cited) |
| 2.1 Performance Measurement | `.../2.1_Performance_Measurement/task_tehsil_burn_metric.md` | **Next**: grouping frozen |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_units_boundaries_crosswalks.md` | Done for Punjab |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_cropping_intensity.md` | Dropped from grouping (unreliable; no effect); future work |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_rice_area.md` | Calibrated to official district totals (2026-10-07) |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_rainfall.md` | In grouping (kept; zones replace terrain only) |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_terrain.md` | Removed from grouping (slope defect); replaced by zones |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_agroclimatic_zones.md` | AESR 2018 shares adopted (replace terrain) |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_groundwater.md` | 2022 fixed |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_soil.md` | In master; encoding fixed |
| 2.2 Homogeneous Grouping | `.../2.2_Homogeneous_Grouping/task_clustering.md` | **FROZEN v4 2026-10-07** (5 dims, CI dropped): Central 63 / South-west 18 / Foothills 15 + Dhar Kalan |
| 2.3 PD Identification | `.../2.3_PD_Identification/task_pd_identification.md` | Not started |
| 2.4 PD Validation | `.../2.4_PD_Validation/task_pd_validation.md` | Not started |
| **3 · Discover Underlying Factors** | | |
| 3.1 Fieldwork Planning | `3_Stage3_Discover_Underlying_Factors/3.1_Fieldwork_Planning/task_fieldwork_planning.md` | Not started |
| 3.2 Data Collection | `3_Stage3_Discover_Underlying_Factors/3.2_Data_Collection/task_predictor_data.md` | Not started |
| 3.3 Data Analysis | `3_Stage3_Discover_Underlying_Factors/3.3_Data_Analysis/task_predictor_analysis.md` | Not started |

## File template
```markdown
# <Task name>
**DPPD position:** Stage › Step · **Status:** … · **Last updated:** YYYY-MM-DD

## In plain words
3–6 sentences: what we needed, what we tried, what we chose, why.

## Technical summary
- Objective + exact question
- Approaches considered (✔ selected / ✘ rejected + reason)
- Data sources · preprocessing · pipeline (scripts, files, columns)
- Final implemented solution
- Open issues

## Log (append-only, chronological)
### YYYY-MM-DD — <event>
**Plain:** …
**Technical:** … [C]/[P]/[?]
```
