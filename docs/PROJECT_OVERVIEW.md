# PROJECT_OVERVIEW.md
_Handoff snapshot: 5 Oct 2026. Source: project memory + DPPD handbook (`DPPD_Handbook_Nov_2021.pdf`). Status tags: **[CONFIRMED]** = agreed/locked, **[PROPOSED]** = not yet approved._

## 1. What this project is
- Course project, IIT Delhi ICTD (COL7761), applying **Data-Powered Positive Deviance (DPPD)** to **crop residue burning (CRB)** of paddy stubble in **Punjab and Haryana**.
- **Goal**: find geographic units that burn significantly *less* paddy stubble than structurally similar peers (the "positive deviants"), understand why, and turn that into actionable guidance for NGOs and government.
- **Core idea**: compare like with like. Units are first grouped by *structural, non-changeable conditions*; only then is burning compared inside each group.

## 2. People
| Role | Who |
|---|---|
| Student / GEE + satellite work | Soham |
| Project partner | None: solo project [C 2026-10-06]. Aryan Rana is not on this project; the village rice-area CSVs originally came from him |
| Supervisor | Prof. Aaditeshwar Seth (approves design decisions) |
| External advisor | Basma Albanna (DPPD co-author; her critiques map to canonical DPPD requirements) |
| External advisor | Andreas (parallel DPPD rice-burning project, Egypt Nile Delta) |

## 3. Canonical DPPD pipeline (where we are)
1. **Stage 1** Problem-method fit (Suitability → Feasibility → Desirability). _Done (Assignment 1)._
2. **Stage 2** Determining positive deviants:
   1. Performance Measurement (burn proxy) — _method locked, scaling to units paused_
   2. **Homogeneous Grouping** — _CURRENT STEP; provisional groups exist_
   3. PD Identification — _not started_
   4. PD Validation — _not started_
3. **Stage 3** Discovering predictors of PD performance — _not started_.

Note: the original design skipped Homogeneous Grouping; Basma flagged it and the team incorporated it.

## 4. Scope
- **Geography**: Punjab first (**97 current tehsils**); Haryana deferred (crosswalks and several datasets behind).
- **Grouping unit**: 97 current Punjab tehsils (LGD codes), used for the prototype masters. The earlier 151-unit figure was Punjab + Haryana combined and is superseded for now. **[CONFIRMED mixed-resolution architecture; tehsil as the final unit has not had a recorded joint sign-off]**
- **Burn measurement**: Sentinel-2 based (BAIS2 + Tasseled Cap Brightness), single post-harvest snapshot with cropland mask.
- **Out of scope for grouping**: hypothesised drivers (CRM machine access, mandi access). They belong in Stage 3, never in grouping.

## 5. Deliverables
- **Assignment 1** (ACM sigconf position paper): complete.
- **Assignment 2** (due 20 Sept 2026): extends A1 with technical methodology, dataset description, preliminary results. _Check whether submitted; status not recorded in memory._
- **Target**: whole project complete by **end of 22 Oct 2026**.

## 6. Key literature
- Albanna et al., *Development Engineering* (2022) — DPPD method
- CEEW (2025) CRB monitoring study
- Naeher & Ziulu (2025), *Applied Economics*
- Naeher, Albanna, Kumar & Vollmer (2023), *Scientific Data* — plot-level survey, 1,206 farmers, 70 villages
- Chen et al. (2024) — 10 m paddy dataset

## 7. Working conventions
See `CLAUDE.md` in this folder. Short version: append-only tracker, one journey file per task, only write files when told, flag confirmed vs proposed, show diffs before changing final documents.
