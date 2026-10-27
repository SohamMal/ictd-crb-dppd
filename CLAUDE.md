# CLAUDE.md — DPPD Crop Residue Burning (Punjab & Haryana)

> Entry point for Claude Code. Read this first, then `project_tracker.md`, then the relevant `sub_journeys/task_*.md` for whatever you are working on.
> Handoff written 2026-10-05 from the claude.ai "ICTD" project. Project target: **finish everything by end of 22 Oct 2026**.

## 1. What this project is
- IIT Delhi ICTD course project (COL7761). Applies **Data-Powered Positive Deviance (DPPD)** to **crop residue burning (CRB)** in Punjab and Haryana.
- Goal: find geographic units that burn significantly less paddy stubble than *structurally similar peers*, understand why, and give actionable guidance to NGOs / government.
- Owner: Soham (mcs262493@cse.iitd.ac.in), MCS student. Handles GEE/JavaScript, satellite work, Python. **Solo project** (Aryan Rana is not on this project; the village rice CSVs originally came from him).
- Supervisor: Prof. Aaditeshwar Seth. Advisors: Basma Albanna (DPPD co-author, founder-level authority on the method; runs a parallel DPPD rice-burning project in Egypt's Nile Delta) and Andreas Pawelke (DPPD, datapoweredpd.org).
- Reference: `DPPD_Handbook_Nov_2021.pdf` (the canonical method). Keep a copy in the repo root.

## 2. Canonical DPPD pipeline (do not break this)
1. Problem–Method Fit → 2. Determine Positive Deviants (Performance Measurement → **Homogeneous Grouping** → PD Identification → PD Validation) → 3. Discover Predictors.
- **Current position: Stage 2, Step 2 (Homogeneous Grouping).** Performance measurement is deliberately paused until grouping is settled.
- **Hard rule:** grouping variables must be structural, non-transferable conditions (climate, soil, rice area, water, terrain). Hypothesised *drivers* (CRM machines, mandi access, etc.) must never enter grouping. **Burning outcomes must never be used to build groups.**

## 3. How to work with Soham
- Plain-language, accessible explanations; clear logical flow linking one concept to the next.
- Terse and direct. Prefer iterative clarification over accepting the first interpretation.
- He is new to clustering. Explain *why* a method step is done, not only what it does.
- **Show proposed changes to any existing document as a markdown diff first; apply to the final file only after he approves.**
- Always label items as **confirmed** vs **proposed** before writing them into documentation.
- Do not add or drop grouping variables without confirming first.
- Everything must be **reproducible in code** (earlier clustering/silhouette/bootstrap numbers came from ChatGPT with no code and must be re-derived).

## 4. Documentation rules (carried over verbatim in intent)
**Master file `project_tracker.md`** — high-level architecture, status, timeline, milestone decision log (`Date | Decision | Reason | Impact`). **Append-only; never overwrite or erase entries.** Add new updates chronologically at the bottom.

**Task files `sub_journeys/task_<name>.md`** — one file per task; never combine unrelated tasks. Append chronologically. Each holds: objective + exact question, approaches considered (selected vs rejected, with reasons), data sources / preprocessing / pipeline, experiments + raw results + blockers, final implemented solution.

**Operational directives**
- Create/update these files **only when explicitly told** ("generate", "update tracker"). This handoff pack is the baseline generation.
- When a major development happens, immediately tell Soham it is journey-worthy and give the **exact text snippet** to append and the target file. Do not write it until he says so.
- Style: high-density Markdown, concise, objective, no fluff, but keep enough technical detail to later draft the report's Methodology, Experiments and Results sections.

## 5. Files to copy into the local repo alongside these docs
These were used in the claude.ai sessions but are **not** contained in these markdown files:
- `DPPD_Handbook_Nov_2021.pdf`
- `DPPD_Crop_Residue_Burning_Questions_for_Prof__Aaditeshwar.pptx` (advisor question deck)
- Grouping masters: `punjab_homogeneous_grouping_master_raw_97tehsils.csv`, `..._transformed.csv`, `..._encoded.csv`
- Scripts: `calc_chen2022_rice_area_current_lgd.py`, the CI v2 script, any GEE JS scripts, the clustering/stability code (if any exists)
- Crosswalks: `tehsil_bridge_summary_punjab.csv`, `tehsil_bridge_detail_punjab.csv`, `tehsil_bridge_reverse_punjab.csv`, `village_level_bridge_punjab.csv` (**`tehsil_bridge_detailed_punjab.csv` is excluded as unreliable**)
- Data: SHRUG v2.2 village gpkg, Chen et al. (2024) GeoTIFFs, 2026 terrain file, village CSVs (`village_rice_all_years.csv`, etc.)
- ChatGPT context files from the 3 Oct 2026 grouping session

## 6. Immediate next actions (as of 2026-10-05)
1. Patch `calc_chen2022_rice_area_current_lgd.py` to output tehsil polygon area + **rice share** (rice area / tehsil area); rerun; update masters.
2. Decide groundwater year (2022 vs 2025) — likely needs Prof. Aaditeshwar.
3. Rebuild clustering **reproducibly in code**: dimension-balanced Gower → average-linkage HAC → silhouette, bootstrap ARI, one-factor-at-a-time sensitivity.
4. Inspect unstable G1 tehsils; compare alternative cuts; then freeze or revise grouping.
5. Resume performance measurement (BAIS2+TCB scaled to tehsil) once grouping is frozen.
6. Get answers to the open questions in `project_tracker.md` §5 (Prof. Aaditeshwar; follow-up call with Basma & Andreas).
