# Groundwater stress
**DPPD position:** Stage 2 › Homogeneous Grouping (water dimension) · **Status:** Done; **2022 fixed** · **Last updated:** 2026-10-06

## In plain words
Punjab's paddy runs on groundwater, and most blocks pump more than is recharged. This shapes farming: Punjab's law delaying paddy transplanting to save water also pushes harvest later, leaving less time before wheat. We use the official "stage of extraction": how much water is pumped as a % of what is replenished. Above 100% means over-exploited. The data comes per block, so each village inherits its block's value and tehsils average their villages. The professor fixed the year at 2022 to match the other data.

## Technical summary
- **Sources [C]:**
  - 2022: CGWB *Ground Water Resources of Punjab State (as on 31.03.2022)*, Annexure I / Table 3 → `Data/Ground Water/punjab_groundwater_blocks_2022.csv` (`block, extraction_stage_pct, category, status`).
  - 2025: PWRDA Seventh Amendment to Punjab Groundwater Extraction and Conservation Directions 2023, Annexure 1 (2025 assessment; notified 19.02.2026) → village master via block crosswalk (`Data/groundwater_output/`).
- **Pipeline:** `Data/Ground Water/compute_tehsil_groundwater.py`. Village → groundwater block (2025 village master, from the Census-PCA village→block crosswalk) → attach 2022 block values by block name → join `village_level_bridge_punjab.csv` → tehsil **unweighted mean of village values** (+ median, dominant category, category counts). 99.4% of villages have data. Output `punjab_tehsil_groundwater_master_2022_2025.csv`.
- **Grouping variable [C]:** `mean_extraction_pct_2022`. Across the 97 tehsils: mean 188, sd 85, min 20, max 393. 2025: mean 184, max 522. `dominant_category_2025`: over-exploited 73, safe 11, semi-critical 7, critical 6.
- **Sensitivity [C]:** a 2025 run as a check only.
- **Haryana:** category-only (no numeric %), deferred.

## Log (append-only, chronological)
### Sep 2026 — Block data cleaned and crosswalked (reconstructed)
**Plain:** We collected block-level water stress and linked every village to its block.
**Technical:** `groundwater_cleaned.csv`; village→block crosswalk 12,581 → 142 blocks. [C]

### 3 Oct 2026 — Year undecided (reconstructed)
**Plain:** 2025 is newer data, but everything else is 2022, and switching years changed the groups.
**Technical:** 2022 vs 2025 taken to Prof. as an open question. [C]

### 2026-10-06 — Supervisor: 2022 only
**Plain:** The professor chose 2022 so all grouping data refer to the same time. 2025 is only a robustness check.
**Technical:** [C] `mean_extraction_pct_2022` in grouping; `mean_extraction_pct_2025` = sensitivity run.

### 2026-10-07 — 2025 data dropped entirely
**Plain:** 2022 is the final groundwater year. The 2025 numbers are not used anywhere, not even as a robustness check.
**Technical:** [C] Soham: "finalized the 2022 gw data, no need of 2025 one". `mean_extraction_pct_2025` stays in the masters as an unused column. The "gw_2025_instead_of_2022" scenario in `Code/grouping/sensitivity.py` is no longer part of the reported sensitivity analysis (its earlier results stay in `task_clustering.md` for the record).
