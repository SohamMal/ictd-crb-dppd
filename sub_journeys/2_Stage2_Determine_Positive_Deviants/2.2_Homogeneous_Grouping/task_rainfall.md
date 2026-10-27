# Rainfall (monsoon)
**DPPD position:** Stage 2 › Homogeneous Grouping (climate dimension) · **Status:** In master; **expected to be replaced by agro-climatic zones** · **Last updated:** 2026-10-06

## In plain words
Monsoon rain shapes how much irrigation paddy needs and when it is harvested. Rain in Punjab ranges from about 300 mm in the dry south-west to 1,600 mm near the hills. We measured average June–September rainfall for each village from satellite rainfall data and averaged the villages into tehsils. It was added because district-level climate zones were too coarse. The professor has since said richer zone data exists, so zones will likely replace rainfall.

## Technical summary
- **Source:** CHIRPS daily (~5 km), GEE. Jun–Sep total per year, mean over window, `reduceRegions()` mean over SHRUG village polygons; centroid sampling fallback for villages smaller than a pixel.
- **Window:** prototype 2020–2025 (in master). Intended 15-yr (2006–2020) instead of the 30-yr WMO normal; GEE task `village_monsoon_rainfall_2006_2020` existed but its null/ID check is not recorded [?]. Now low priority.
- **Roll-up:** `Data/Rainfall/compute_tehsil_rainfall.py`. Village values joined via `village_level_bridge_punjab.csv`; tehsil = **unweighted mean of village means** (also median/min/max/std). Output `punjab_tehsil_monsoon_rainfall_2020_2025.csv`.
- **Grouping variable:** `mean_monsoon_rainfall_mm`. Across the 97 tehsils: mean 739, sd 217, min 310, max 1,604.
- **Dropped [C, 3 Oct]:** rainfall variability; temperature. This is an **untested assumption** ("guessed not to matter").

## Log (append-only, chronological)
### Sep 2026 — Rainfall chosen over NARP zones (reconstructed)
**Plain:** Climate zones are drawn by district, which would lump wet and dry tehsils together, so we measured rainfall directly.
**Technical:** CHIRPS pipeline; 15-yr window decided over 30-yr WMO (balances stability vs recent monsoon shifts; limitation). [C]

### 3 Oct 2026 — 2020–2025 prototype in master (reconstructed)
**Plain:** For speed, a 6-year average went into the first grouping.
**Technical:** 15-yr expansion planned after the prototype works. [C]

### 2026-10-06 — Supervisor: zones replace rainfall + terrain
**Plain:** The professor says better zone data exists. We will use zones instead of rainfall and terrain, so the same climate information isn't counted twice.
**Technical:** [C] Rainfall likely leaves the grouping set once zone data is found (see `task_agroclimatic_zones.md`). Kept in the masters and repo as reference; the current six-dimension run is the baseline. 15-yr extension now low priority.

### 2026-10-06 — Rainfall KEPT in grouping (zones replace terrain only)
**Plain:** We planned to drop rainfall once zone data arrived, but tests showed the zone map is too coarse to tell the dry south-west from the wetter central plain. Rainfall does that job, so it stays.
**Technical:**
- [C] Soham chose option (b): AESR zones (shares) replace terrain; `mean_monsoon_rainfall_mm` (2020–2025) stays. Evidence: dropping rainfall in the sensitivity test → 82/14, ARI 0.487 (SW dissolves); zones replacing rainfall + terrain → ARI 0.410 (SW dissolves); zones replacing terrain only → ARI 0.897.
- Known overlap with zones (AESR growing-period classes derive partly from rainfall), accepted.
- Consequence: the planned 15-yr (2006–2020) rainfall window regains some relevance. [P] Decide whether to extend before the final run or state the 2020–2025 window as a limitation.

### 2026-10-07 — 5-year window accepted for now
**Plain:** The 2020–2025 average stays for now. A longer window may be revisited later.
**Technical:** [C] Soham: 5-yr (2020–2025) window OK for now; 15-yr extension deferred. State as a limitation if not extended.
