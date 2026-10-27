# DECISIONS.md
_Format: Decision | Alternatives considered | Reason | Evidence | Consequence. Status: **LOCKED** / **PROVISIONAL** / **OPEN**. The dated one-line log lives in `project_tracker.md` §4; this file adds the rejected alternatives and reasoning._

## 1. Locked decisions
| ID | Decision | Alternatives rejected | Reason / evidence | Consequence |
|---|---|---|---|---|
| D9 | Burn proxy = **BAIS2 + TCB** on Sentinel-2, single post-harvest snapshot, cropland mask | NBR pre/post change detection; simplified two-band BAIS2; FIRMS/VIIRS | NBR: 81.32% acc / 82.26% recall. BAIS2+TCB: 95.53% / 98.11%, F1 0.9683 (380 fields, stratified 5-fold CV). Harvest itself causes a spectral shift that mimics burning. Earlier bad results were a wrong BAIS2 formula. | Use Filipponi red-edge BAIS2; verify TCB coefficients |
| — | Drop FIRMS/VIIRS | Using thermal fire counts | ~3.67x undercount vs Sentinel-2 | Satellite optical detection only |
| — | Add Homogeneous Grouping | Original design (skip it) | Basma: it is an official, non-negotiable DPPD step | Stage 2 Step 2 is active work |
| — | Grouping variables are structural only | Including CRM machines, mandi access etc. | Those are hypothesised drivers, belong in Stage 3. Burn outcomes never used for groups. | Keeps PD logic valid |
| — | **Mixed-resolution architecture** (Prof. approved) | Force one common resolution | Data exists at village/tehsil/block/district | Each variable stays native, inherits downward through crosswalks |
| — | Village boundaries = **SHRUG v2.2** | Other boundary sets | Punjab 12,808 / Haryana 6,998 villages, geometry checks passed, EPSG:4326, PC11 | Base layer fixed |
| — | Soil from **NBSS&LUP** | HARSAC (Haryana) | HARSAC: manual form only, no bulk export, no Punjab equivalent. SLUSI file is Haryana-only (same asymmetry). | Symmetric soil coverage |
| — | Majority-area-overlap for multi-zone villages | Pick first / average | Largest intersection wins | Only matters if a zone-based variable returns |
| — | Tehsil CI = village A1/A2/A3 **summed**, CI formula applied once | Averaging village percentages | Averaging percentages is mathematically wrong | Sum-then-divide rule |
| 3 Oct | Grouping unit = **97 current Punjab tehsils** | ~20k villages (too granular); 41 districts (too coarse); 151 units (Punjab+Haryana) | Middle ground; Punjab first | Masters built at 97 |
| 3 Oct | Six dimensions: CI, rice, rainfall, terrain, groundwater, soil | Gross cropped area, rainfall variability, temperature, other agro-climatic variables | Too much work at tehsil level / judged unlikely to matter (**untested assumption**) | Do not add variables without confirming |
| 3 Oct | Replace NARP zones with mean rainfall + terrain | NARP zones (district-based) | Tehsils with very different rainfall in one district would be grouped together | Needs advisor sign-off |
| 3 Oct | Keep **Chen rice area** for grouping, not rebuilt with SAR | Sentinel-1 SAR 2022–24 rice | Rice area treated as a structural spatial trait; SAR is lengthy | SAR track retained as spare, not required |
| 3 Oct | Rice dimension = **rice share of tehsil area** | Absolute hectares | Absolute area is confounded by tehsil size | Script patch + rerun pending |
| 3 Oct | Rebuild clustering **reproducibly in code** | Trust ChatGPT-produced numbers | No code existed for earlier silhouette / bootstrap results | First task for Claude Code |
| 3 Oct | Dhar Kalan (Pathankot) = contextual outlier, not a peer group | Force into a group | Singleton at every k | 96 tehsils across 3 groups |
| 3 Oct | Merge Adampur + Jalandhar-II (2-tehsil branch) into the 55 group | Keep as 4th group | Too small to be a peer group | Provisional G1=25, G2=14, G3=57 |
| 3 Oct | Equal 1/6 weight per dimension | Unequal / expert weights | Simple, defensible design choice | Must be justified in report |

## 2. Provisional (could still change)
- **Rainfall window**: prototype uses 2020–2025 mean; an earlier decision set 15 yr (2006–2020) instead of the 30-yr WMO standard. Intended final = ~15 yr; flag as limitation either way.
- **Groundwater year**: 2022 vs 2025 undecided (switching changes grouping; 2025 is better data but the other dimensions are 2022-labelled).
- **Clustering cut**: provisional 25/14/57, silhouette 0.287, bootstrap ARI 0.572. Not frozen.
- **CI thresholds** (`PEAK_MIN`, `TROUGH_MAX`, `AMPLITUDE_MIN`): not tuned; satellite CI runs above Statistical Abstract baselines in Southwestern and Kandi belts.

## 3. Open decisions (need Prof. Aaditeshwar / group)
1. Rice: fixed 2022 snapshot vs extend to 2023–24 via own SAR pipeline.
2. Groundwater year 2022 vs 2025.
3. Is replacing agro-climatic zones with rainfall + terrain, and dropping temperature/variability, acceptable, or must the assumption be tested first?
4. Equal weighting: acceptable, and how to justify? (±15% weight changes moved groups noticeably.)
5. Punjab-only study now, Haryana later: acceptable?
6. District vs village resolution: Basma recommends village; team scope was district/tehsil. Discuss before finalising.
7. Section 2.5 "Second Deviant Pass": team's own extension, risks conflicting with the Prof.'s rule against residual-based deviant identification.
8. Placeholder village codes (800166, 800252 and any other `8xxxxx`): include or exclude.
9. Mewat vs Nuh canonical district name (16-entry district crosswalk otherwise confirmed).
10. Confirm ground-truth dataset provenance (Chen et al. 2024 for rice fields, NBSS&LUP for soil) before citing results externally.

## 4. Superseded / contradicted notes (read before trusting older text)
- "NARP zone chosen as the preferred classification" (Sept) → superseded by rainfall + terrain (3 Oct).
- "Tehsil = 151 units" → 97 for Punjab only.
- "Rice via Sentinel-1 for 2022–24" (Sept) → partly overtaken by "keep Chen" (3 Oct). Chen 2022 in the masters was computed directly from the GeoTIFF, **not** from the stale village CSVs, so the stale-column problem does not affect it. Worth a one-line verification.
- "Rainfall 15 yr" (Sept) → prototype 5-6 yr (3 Oct); 15 yr still intended.

## 5. Hard-won learnings
- Collect data at the finest resolution available; design grouping around what the data honestly supports.
- NBR pre/post fails for Punjab/Haryana CRB.
- Check intuition against data (Fazilka village assumed low-rice; SAR 87.1% and official 71.3%/69.8% both showed it is rice-heavy).
- ID-vintage mismatch (2011 Census vs current LGD) is the recurring merge hazard; always go through the bridge files.
- Basma's feedback carries founder-level authority on DPPD.
