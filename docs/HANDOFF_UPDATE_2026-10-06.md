# HANDOFF_UPDATE_2026-10-06.md
_Corrections to the handoff pack (`CLAUDE.md`, `project_handoff.md`, `DECISIONS.md`, `CURRENT_STATUS.md`, `CHAT_ARCHIVE.md`, `METHODOLOGY.md`). Source: Soham's meeting with Prof. Aaditeshwar (Oct 2026, exact date not recorded) and your read-back (`CLAUDE_CODE_UNDERSTANDING.md`). **Where this file conflicts with the handoff pack, this file wins.**_
_Tags: **[C]** confirmed · **[P]** proposed · **[?]** Soham must answer._
_Per working rules: do **not** edit the older files or the tracker yet. Show Soham a markdown diff first and apply only after approval. The tracker snippet in §6 is for him to approve._

## 1. Your read-back was accurate
Everything in `CLAUDE_CODE_UNDERSTANDING.md` matches the handoff, apart from the items below. The handoff simply predates the supervisor meeting.

## 2. Decisions that changed
| Topic | Old (in handoff) | Now |
|---|---|---|
| Groundwater year | 2022 vs 2025 open | **[C] 2022 only**, because the grouping is built around 2022. Use 2025 only as a sensitivity check |
| Rice | Chen 2022 snapshot vs Sentinel-1 SAR 2023–24 extension | **[C] Chen 2022 fixed.** No SAR extension (academic project). The SAR pipeline is retired, not needed |
| Scope | Punjab-only awaiting confirmation | **[C] Punjab only for now.** Haryana after the Punjab pipeline works |
| Clustering | Hierarchical, provisional | **[C] Hierarchical clustering endorsed** |
| Agro-climatic zones | NARP replaced by rainfall + terrain | **[C] Reversed.** Prof. said more zone data exists than NARP. Soham's decision: use zones **instead of** rainfall and terrain, which avoids overlap between them. Needs tehsil-level or richer zone data |
| Equal weights | Needs advisor sign-off | **[P] Pending.** Soham researches the justification first; asks Prof. at next meeting (or earlier) if he finds none |

## 3. Consequences for the design
- **The six-dimension set is provisional again.** Rainfall (`mean_monsoon_rainfall_mm`) and terrain (`elevation_mean`, `slope_mean`) are expected to be replaced by a zone-based dimension. Depending on what zone data is found, the final set may be five or six dimensions.
- Build the clustering code with a **configurable list of dimensions**, so swapping them needs no rewrite. Run the current six as a baseline first.
- The **rainfall 15-year extension** and the **slope_mean units check** are now low priority. Still note the slope anomaly (range 0.0–1.0, too low for Shivalik tehsils such as Dhar Kalan) in case terrain stays.
- **Zone data is the new open data task.** Find tehsil-level (or finer) agro-climatic zone data. NARP is district-level and was already judged unsuitable. How the zone data becomes distance variables (categorical zone label vs numeric zone attributes) is **[?]** for Soham.
- Rainfall and terrain files, the SAR rice scripts and groundwater 2025 files stay in the repo as reference. Do not delete them.

## 4. Technical point to act on
You found near-constant soil dummy columns (drainage: Well 75, Moderately well 14, Excessive 6, Poor 1, Unknown 1). Use the **original categorical columns, one per descriptor,** in the Gower distance with 0/1 mismatch. Do **not** use the one-hot `..._encoded.csv`: it counts one real soil difference several times and dilutes the average with near-constant columns.
- Whether to drop near-constant descriptors is Soham's call under his "drop any useless variable" rule. **Propose it with evidence; do not drop on your own.**

## 5. Answers to your §11 questions
| Question | Answer |
|---|---|
| Partner vs solo | **[?]** Soham to answer. The notes tie Aryan Rana to a different course project, though the village rice file came from him |
| Assignment 2 submitted? | **[?]** Soham to answer. Not recorded |
| Tehsil-level burn metric | Not decided, so your [P] stands. Candidate: burnt share of rice area (a suggestion, not a decision). Revisit after grouping freezes |
| Slope units / DEM source | Not recorded. Treat as low priority per §3 |
| Soil descriptor set and transforms | Matches the handoff |
| Decisions after 5 Oct | Only the supervisor-meeting items in §2 are known |

## 6. Text to append to `project_tracker.md` §7 (after Soham approves)
```
### 2026-10-06 — Supervisor feedback applied (Oct 2026 meeting, exact date not recorded)
- [C] Groundwater year = 2022 only (grouping built around 2022). 2025 kept only as sensitivity.
- [C] Punjab only for now; Haryana after the Punjab pipeline works.
- [C] Hierarchical clustering endorsed. Rice fixed at Chen 2022; no Sentinel-1 extension to 2023–24.
- [C] Zones now REPLACE rainfall and terrain. Needs tehsil-level/richer zone data; dimension set provisional until found.
- [P] Equal weights: Soham to research justification first; ask Prof. at next meeting if none found.
- Impact: rainfall 15-yr extension and terrain slope check now low priority. Superseded in handoff docs: groundwater year, rice SAR, zones, six-dimension count.
```

## 7. Adjusted plan (proposed, in order)
1. Patch `calc_chen2022_rice_area_current_lgd.py` for tehsil area + rice share; rerun; update masters (show diff first).
2. Build the clustering pipeline: configurable dimensions, groundwater fixed at 2022, original categorical soil columns, Gower → average-linkage HAC → silhouette → 80% bootstrap ARI (300 runs) → sensitivity (no logs, groundwater 2025, ±15% weights, drop one dimension at a time). Reproduce or disprove 25/14/57 and the Dhar Kalan outlier.
3. In parallel, locate tehsil-level agro-climatic zone data; then rebuild with zones in place of rainfall + terrain and compare with the baseline.
4. Weight justification: Soham researches; flag any findings.
5. Freeze or revise grouping. Then scale BAIS2 + TCB to tehsil → PD identification → validation → predictors → report (target end of 22 Oct 2026).

## 8. Still-valid rules (unchanged)
Burn outcomes never build groups · no hypothesised drivers in grouping · no adding or dropping variables without confirming · ChatGPT numbers not citable until rerun · tracker append-only · write docs only when told · diff first · label confirmed vs proposed.
