# CURRENT_STATUS.md
_Snapshot: 5 Oct 2026. **Deadline: end of 22 Oct 2026 (17 days).** This is a *current-state* file: overwrite freely as work moves. History goes in `project_tracker.md` §7 (append-only)._

## Where we are
Stage 2, Step 2: **Homogeneous Grouping**. A provisional grouping of 97 Punjab tehsils exists but was produced by ChatGPT without code, so it has to be rebuilt and verified. Performance measurement is paused. PD identification, validation and Stage 3 have not started.

## Completed
- Assignment 1 position paper (ACM sigconf).
- Update presentation (Prof.: "good clarity on methodology").
- Burn detection method locked and validated (BAIS2+TCB, 95.53% acc, 98.11% recall, F1 0.9683).
- SHRUG village layer locked; Punjab village→block crosswalk done; tehsil/village bridge files for Punjab.
- Six-dimension design fixed; master files (raw / transformed / encoded) built for 97 tehsils.
- Terrain done for all 97; rainfall prototype done; CI pipeline method locked, `CI_3yr_pooled` in master.
- Provisional groups: G1=25, G2=14, G3=57 + Dhar Kalan outlier.
- Sentinel-1 SAR rice classifier validated on two villages (spare track).

## In progress / pending
| Item | State |
|---|---|
| Rice share patch | Patch `calc_chen2022_rice_area_current_lgd.py` to output tehsil polygon area + rice share, rerun, update masters. **Not done** |
| Groundwater year | 2022 vs 2025 undecided |
| Clustering rebuild | Not started (no code exists) |
| Stability analysis | Reported ARI 0.572 / silhouette 0.287 unverified |
| CI QA | Threshold tuning and 6 high-swing tehsils unresolved |
| Rainfall window | Prototype 2020–2025; 15-yr expansion planned |
| Haryana | Deferred (crosswalk, groundwater category-only, soil, CI editions) |
| Assignment 2 | Due 20 Sept; submission status **[?]**. Final report still to be drafted |

## Immediate next steps (in order)
1. Copy the files listed in `CLAUDE.md` §5 into the local repo; fill the **[?]** gaps in `DATA_INVENTORY.md` (column names, file names, DEM source).
2. Patch and rerun the rice script → rice share; update masters.
3. Write the clustering pipeline in code: load transformed master → dimension-balanced Gower (equal 1/6) → average-linkage HAC → silhouette → compare with reported 25/14/57 and Dhar Kalan outlier.
4. Bootstrap (80%, 300 runs, ARI) and one-factor-at-a-time sensitivity (no logs, groundwater 2025, ±15% weights, each dimension dropped).
5. Inspect unstable G1 tehsils; compare alternative cuts; decide freeze vs revise.
6. Take the open questions to Prof. Aaditeshwar (see `DECISIONS.md` §3); hold the follow-up call with Basma and Andreas.
7. After freezing: scale BAIS2+TCB burn measure to tehsil level, then PD identification and validation.
8. Draft report sections (Methodology, Experiments, Results) from tracker/journeys.

## Blockers and risks
- **Advisor sign-off** needed on: groundwater year, replacing agro-climatic zones with rainfall + terrain, equal weights, Punjab-only scope.
- **Untested assumption**: dropping temperature and rainfall variability. A quick sensitivity test would defend it.
- **Timeline**: PD identification, validation and the report must fit in the remaining days. Freeze grouping early.
- **Conflicting notes** (see `DECISIONS.md` §4): rice source (Chen vs SAR), rainfall window, NARP status. Confirm with Soham when relevant.
- **Reproducibility**: nothing from the 3 Oct clustering session can be cited until rerun.

## Open data checks
- Confirm Chen 2022 tehsil values are not affected by the stale village CSV (they should not be: computed from GeoTIFF).
- Confirm how CI for the 52 current tehsils (from the remaining 32 2011-tehsils) was finalised.
- 8 villages unaccounted in the Sept village merge (12,800 vs 12,808); likely moot at tehsil level.
