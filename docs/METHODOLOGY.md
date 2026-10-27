# METHODOLOGY.md
_Each component is tagged **[LOCKED]**, **[PROVISIONAL]**, or **[PROPOSED]**. Numbers marked "reported" came from earlier sessions (some from ChatGPT, no code) and **must be reproduced** before citing._

## A. Performance measurement (burn detection) — [LOCKED, scaling paused]
- **Proxy**: BAIS2 + Tasseled Cap Brightness (TCB) on Sentinel-2 (decision D9).
- **Why**: NBR pre/post change detection fails here, because harvest alone causes a spectral shift that looks like burning. Correct approach = one post-harvest snapshot + cropland mask.
- **Implementation traps**: BAIS2 needs the full Filipponi red-edge formula (not the simplified two-band version); TCB coefficients must be verified. Earlier poor results were implementation bugs.
- **Validation** (380 labelled fields; Hoshiarpur/Jalandhar 2021, Sangrur area 2020; stratified 5-fold CV): BAIS2+TCB accuracy 95.53%, recall 98.11%, F1 0.9683. NBR: accuracy 81.32%, recall 82.26%.
- **FIRMS/VIIRS dropped**: ~3.67x undercount vs Sentinel-2.
- **Open**: confirm ground-truth provenance before citing externally; scale BAIS2+TCB to pixel / tehsil level.

## B. Boundaries and crosswalks — [LOCKED for Punjab]
- **Village polygons**: SHRUG v2.2 (Punjab 12,808 villages; Haryana 6,998), EPSG:4326, PC11 coding. Uploaded to GEE as `projects/ictd-507010/assets/shrug/shrug_villages`.
- **Tehsil unit**: 97 current Punjab tehsils (LGD codes) via bridge files `tehsil_bridge_summary/detail/reverse_punjab.csv` (`tehsil_bridge_detailed_punjab.csv` excluded as unreliable). Village-to-tehsil: `village_level_bridge_punjab.csv`, join key `pc11_tv_id`.
- **ID-vintage problem**: SHRUG uses 2011 district codes (20 Punjab, 21 Haryana) vs current 23/22. Spatial reassignment needed. Soil and rice map to 2011 IDs.
- **Mixed-resolution design** [CONFIRMED by Prof.]: each variable stays at native resolution (village/tehsil/block/district) and is inherited downward through crosswalks.

## C. Homogeneous grouping — [PROVISIONAL]
**Principle**: grouping variables must be structural and non-transferable. Burn outcomes are never used to build groups.

**Six dimensions (97 Punjab tehsils)**
| Dimension | Variable(s) | Notes |
|---|---|---|
| Cropping intensity | `CI_3yr_pooled` (2022–24) | Satellite CI, see D |
| Rice | `chen_rice_area_ha_2022` → **switching to rice share of tehsil area** | Chen 2022 GeoTIFF masked over LGD tehsil polygons by `calc_chen2022_rice_area_current_lgd.py`; patch to output tehsil area + share (rerun pending) |
| Rainfall | mean monsoon rainfall 2020–2025 | 5-yr prototype window; plan to move to 15-yr (2006–2020) |
| Terrain | `elevation_mean`, `slope_mean` | 2026 terrain file, all 97 covered |
| Groundwater | `mean_extraction_pct_2022` | 2022 vs 2025 undecided |
| Soil | 8 categorical descriptors (particle size, drainage, texture, depth, pH, salinity, sodicity, erosion) | One missing drainage value set to `Unknown` |

- **Agro-climatic zones (NARP) are no longer used**: replaced by mean rainfall + terrain because zones follow district boundaries and would lump tehsils with very different rainfall together. (An earlier note said NARP was chosen; the 3 Oct design supersedes it.) Advisor confirmation of this swap is an open question.
- **Dropped**: gross cropped area (too much work at tehsil level), rainfall variability, temperature and other agro-climatic variables (guessed not to matter). Do not add variables without confirming.
- **Principle**: any variable or descriptor that is not useful should be dropped, since it distorts distances (applies to soil descriptors too).
- **Transforms**: log1p on rice area, elevation, slope; soil stays categorical.
- **Distance**: custom *dimension-balanced Gower*. Distance is computed within each dimension (terrain = mean of 2 variables, soil = mean of 8), then the six dimensions are averaged with equal weight 1/6. Numeric = range-normalised absolute difference; categorical = 0/1 mismatch. Equal weights are a design choice and must be justified in the report.
- **Clustering**: average-linkage HAC on the precomputed 97x97 matrix; several k tested.
- **Reported results (need reproduction)**: Dhar Kalan (Pathankot) is a singleton outlier at every k, kept as contextual outlier. After removing it: 25/14/55/2; the 2-tehsil branch (Adampur, Jalandhar-II) merged into the 55 group → **G1=25, G2=14, G3=57**, silhouette 0.287. Bootstrap (80%, 300 runs) mean ARI 0.572; G1 least stable. Sensitivity (no logs, 2025 groundwater, ±15% weights) changed groups a lot (ARI ~0.05–1.00).
- **To do**: rebuild reproducibly in code, stability check, one-factor-at-a-time sensitivity, compare alternative cuts, then freeze or revise.

## D. Cropping intensity pipeline (tehsil, satellite) — [LOCKED method; QA open]
- `CI = 100 × (A1 + 2·A2 + 3·A3) / (A1 + A2 + A3)` from Sentinel-2 SR Harmonized NDVI, Kharif/Rabi/Zaid windows, ESA WorldCover cropland mask. Computed per village, rolled up to tehsil afterwards. Always **sum then divide**, never average percentages.
- Ag-years 2022–2024. 45 "clean" 2011-tehsils: mean CI 204.6% (179.8–235.3%).
- **QA flags**: Southwestern Belt (200.4% vs expected 175–190%) and Kandi Belt (192.7% vs 150–175%) run high vs Statistical Abstract baselines; needs threshold tuning (`PEAK_MIN`, `TROUGH_MAX`, `AMPLITUDE_MIN`) or acceptance that satellite CI differs structurally. Unusual year-to-year swings (20–32 pts) in Sultanpur Lodhi, Nihal Singhwala, Balachaur, Nangal, Tapa, Khadur Sahib.
- Remaining 32 2011-tehsils map to 52 current tehsils (43 split, 9 blended) → roll up by bridge file's current `lgd_sd_code`, not `pc11_sd_id`.
- Existing district-level CI from Punjab Statistical Abstract is the baseline/cross-check.

## E. Rainfall — [PROVISIONAL]
- CHIRPS daily in GEE, June–Sept totals per year, mean over window, `reduceRegions()` mean over village polygons; centroid-sample fallback for villages smaller than the ~5 km pixel.
- Earlier decision: 15-yr window (2006–2020) instead of 30-yr WMO; flag as limitation. Current prototype uses 2020–2025.

## F. Rice area 2022–2024 via Sentinel-1 SAR — [side track; see conflict in DECISIONS]
- Reason: village CSV 2022 column is a stale copy of 2020 (98.6% identical); the standalone 2022 file is byte-identical, so the staleness is in the source.
- Rule: pixel = rice if VH < −18 dB in mid-June–July transplant window AND rises ≥ 5 dB by Aug–Sept. Optical rejected (monsoon clouds).
- Validation: Ludhiana village 78.8%; Fazilka village `034223` 87.1% vs official 71.3% (2018) / 69.8% (2020), so both sources agree it is rice-heavy.
- Full export not confirmed as run.

## G. Not yet started
- PD identification (note: Prof. has a rule against residual-based deviant identification; the team's "Second Deviant Pass", Sec 2.5, is unapproved).
- PD validation, Stage 3 predictors.
