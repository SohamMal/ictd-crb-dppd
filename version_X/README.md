# Version X: village-level DPPD (Punjab, Central + South-west)

_Built 2026-11-10 by Claude on Soham's instruction ("go to village level; take your own decisions; come back when driver identification is done"). Every decision below is **[P] proposed**: Claude made it, Soham has not reviewed it. The main (tehsil) version is untouched. This folder only reads its code and outputs._

## In plain words
The main version asked which **tehsils** burn less than similar tehsils. Version X asks the same of the **villages** (9,277 ranked). Three results matter:
1. **Village PDs exist, and many are invisible at tehsil level.** 299 villages burn far less than peers with the same climate, zone and rice share, and keep that verdict through the checks. 180 of them lie in tehsils the main version never flagged (e.g. Kapurthala 41, Dudhan Sadhan 26, Sardulgarh 12). None lie in the 4 tehsil NDs.
2. **Some tehsil PDs are partly a grouping effect.** Abohar (41 of 80 villages are PDs), Dinanagar and Gurdaspur hold up. Jalandhar-I, Adampur, Phagwara and Banga have almost no village PDs. Their villages are mostly low-rice villages of the wetter northern group, which burns little anyway. The tehsil grouping put them in one "Central" group with heavy-burning Malwa.
3. **None of the 8 online drivers explains the village PDs well.** Labour, farm size, livestock, distance to cities and to straw buyers, and basmati do not separate PD villages from their peers. The one consistent within-tehsil signal is that **PD villages show a ~2.5-day shorter gap between paddy harvest and the wheat green-up**. This fits in-situ sowing (Happy/Super Seeder), but it may also be a measurement effect, because unburnt stubble can re-green. The 8 drivers together explain ~16% of village burning out of tehsil (cross-validated). That leaves the "why" for fieldwork or richer data.

## Pipeline (run in this order; all scripts in `Code/`)
| Step | Script | What it does | Key output |
|---|---|---|---|
| base | `vx_villages.py` | 12,660 Census-2011 villages (LGD bridge + SHRUG polygons); rice area recomputed from Chen 2020/2022 rasters (PIL rasterisation, rasterio is blocked); 10 random rice-in-both-years pixels per Central/South-west village | `outputs/villages/village_base.csv`, `points_new.csv` (95,942 points) |
| check | `vx_chen2022_window.py` | Confirms `clipped_2022.tif` = India-wide Chen 2022 (100%); Chen 2020 vs 2022 agree on 99.2% of pixels | (check only) |
| 2.2 | `vx_group_master.py` | 5 structural dimensions per village: rice share (cal.), monsoon rainfall, AESR zone shares, groundwater 2022 (block), soil (8 classes) | `outputs/grouping/village_master.csv` |
| 2.2 | `vx_grouping.py` | Dimension-balanced Gower → average-linkage HAC → silhouette, bootstrap ARI (40 × 80%) | `k_table.csv`, `village_groups.csv` |
| 2.2 | `vx_peer_groups.py` | Peer group = village group × rice-share tercile (L/M/H) | `peer_profiles.csv` |
| 2.1 | `vx_burn.py` | Main version's final S2 random-forest detector (cut 0.786), 2020-24, on the village points + reused tehsil points | `outputs/burn/village_burn_measure.csv` |
| 2.1 | `vx_burn_checks.py` | Aggregation to tehsil, season-to-season reliability, rice-share link | `checks_*.csv` |
| 3 input | `vx_harvest_gap.py` | NDVI harvest / green-up, 3 points per village, Sep–Jan, 2020-24 | `outputs/predictors/harvest_gap/point_dates.csv` |
| 2.3–2.4 | `vx_pd.py` | Main-version IQR rules within peer groups + validation V1–V5 | `outputs/pd/pd_table.csv`, `pd_validated.csv`, `tehsil_overlap.csv` |
| 3 | `vx_drivers.py` | D1–D7, D9 per village | `outputs/predictors/village_drivers.csv` |
| 3 | `vx_compare_drivers.py` | PD/ND profiles, gradient, within-tehsil test, joint models, robustness | `driver_summary.csv`, `joint_model.csv`, `robustness_v5_pass.csv` |
| fig | `vx_figures.py` | Maps | `outputs/figures/village_pd_map.png`, `burn_map.png` |

Runtime: the Earth Engine extractions took ~5 h (burn) and ~5 h (NDVI) in parallel. `raw/` caches are git-ignored.

## Decisions [P] and why
| # | Decision | Reason |
|---|---|---|
| X1 | Unit = Census-2011 village (LGD bridge, 12,660) | Every village-level structural file (rainfall, soil, groundwater) is keyed on it |
| X2 | Measure and rank only Central + South-west villages | The main version showed the burn measure fails in the Foothills (2026-10-19/23); Dhar Kalan was an outlier |
| X3 | Population = rice in both Chen years ≥ 25 ha, structural data complete → **9,278** villages (98.8% of the regions' rice) | Below 25 ha there are too few distinct rice pixels, and too little paddy to matter |
| X4 | Same 5 grouping dimensions, equal weights; numeric ruler = 1st–99th percentile | Keeps the frozen v4 design; stops a few extreme villages from compressing every distance |
| X5 | Cut k = 3 (best silhouette among stable cuts) | 4,305 / 3,334 / 1,639; silhouette 0.377; bootstrap ARI median 0.991 (**p10 0.39**: in some draws the north/south split moves) |
| X6 | Peer = group × rice tercile (9 peers, 546–1,436 villages) | Rice barely separates the clusters (separation 0.035, against 0.377 for zone). Inside a group, burning still follows rice share (ρ 0.26–0.42). Within bands that drops to 0.03–0.28 |
| X7 | 10 points per village per season, the same detector as the main version | Directly comparable with the tehsil numbers; ~5 h of Earth Engine time |
| X8 | Season counted if ≥ 5 verdicts; village ranked if ≥ 4 seasons | One season rests on ~10 points |
| X9 | V1 bootstrap draws p from Beta(k+½, n−k+½) before Binomial(n, p) | A plain binomial redraw keeps 0-of-10 seasons at 0 for ever, which would make zero-burn villages pass automatically |
| X10 | V2 = cut 0.5; tehsil region × band; group without bands (static: kept in ≥ 2 of 3 = pass) | The main version's settings check, plus the new grouping choices |
| X11 | Stage 3 reads every driver as a percentile inside its peer group; within-tehsil sign test; tehsil-cluster bootstrap CIs; Holm correction | Hundreds of PDs allow testing, but villages in one tehsil are not independent |

## Results
**Grouping (2.2).** V1 = north (AESR 9.1, ~840 mm, Majha/Doaba; 100% Central), V2 = central-south (AESR 4.1, ~660 mm; 97% Central), V3 = south-west (AESR 2.5, ~460 mm; 98% South-west). So the village view **splits the tehsil "Central" region into north and south**. ARI vs the tehsil regions is 0.38 at k = 3 and 0.94 at k = 2. Caveat: the split follows the 1:4M AESR line, and at village level zone shares are mostly 0/1.

**Burn measure (2.1).** 46,235 village-seasons, median 10 verdicts each. Aggregated to tehsils, it agrees with the main tehsil measure at ρ 0.94–0.98 every season (means within 0.01). Village ranks repeat across seasons (ρ 0.43–0.70), so they are not noise. Burn level by group: V1 0.44, V2 0.66, V3 0.78.

**PDs (2.3–2.4).** Static PD validation (`pd_validated.csv`):

| | strict (beyond fence) | candidate (bottom 10%) |
|---|---|---|
| validated PD | 155 | 25 |
| PD with caveat | 101 | 18 |
| dropped (V1 bootstrap fails mostly) | 46 | 449 |

- 222 static NDs kept as contrast (no strict NDs: the upper fence lies above 100%).
- Temporal: 213 PDs pass, but the trend rests on 5 seasons of ~10 points, so treat it as secondary; 24 villages are PD on both.
- Village PDs by main-version tehsil label: 10.6% of villages in tehsil static PDs, 2.3% elsewhere, 0% in tehsil static NDs (`tehsil_overlap.csv`).

**Drivers (3)** (`driver_summary.csv`; percentiles within peer; ★ = Holm p < 0.05):

| Driver | Hypothesis | PD median pctile | Within-tehsil (PDs on expected side) | Reading |
|---|---|---|---|---|
| D1 turnaround | longer → less burning | 0.29 ★ | 0.31 ★ (against) | PDs have **shorter** turnaround (−2.5 d, holds without late-harvest PDs) |
| D1 harvest date | later → more burning | 0.70 ★ | 0.30 ★ (against) | PDs harvest slightly later. Mostly the 17% with ≥ 10 d later harvest (V5 flags); without them median +0.5 d |
| D2 early second crop | more → less | 0.37 | 0.43 | no signal |
| D3 labourers / cultivator | more → less | 0.51 | 0.47 | no signal |
| D3 cultivators / 100 ha rice | more → less | 0.44 | 0.48 | no signal |
| D4 km to straw buyer | farther → more | 0.55 | 0.49 | no signal for PDs; NDs are *nearer* buyers (0.34 ★); the plant list is coarse |
| D5 km to inter-state border | farther → less | 0.21 ★ | 0.41 (against, p 0.02) | PDs lie nearer borders: mostly the Abohar/Fazilka and Gurdaspur clusters (location, not a mechanism) |
| D6 km to town | farther → more | 0.60 ★ | 0.45 | PDs slightly *farther* from towns (against); not within tehsil |
| D7 basmati (district) | more → less | 0.63 | n/a | no signal |
| D9 bovines / cultivator | more → less | 0.53 | 0.44 | no signal |

Joint: OLS on peer percentiles R² 0.11 (in-sample). Random forest R² 0.16 out of tehsil (5-fold grouped CV). Its importance is dominated by location proxies (border distances, buyer distance, district basmati).

## Limitations
- The burn detector is the main version's: 18% of tilled Walker fields are still called burnt at the cut, and V7 (visual check) was not done. In V3-L (low-rice South-west), cotton passing the rice mask is not ruled out (the main version had the same caveat at Abohar).
- Kapurthala's 41 PDs fall in group V2 (AESR 4.1) although Kapurthala is Doaba. Part of its deviance may be the same north-vs-Malwa effect the zone line misses.
- Village points are a sample (10 per season), so a single village verdict is uncertain. The V1 bootstrap covers sampling noise, not detector error.
- D1's sign may be mechanical (re-greening of unburnt stubble). D4 places plants at tehsil centroids. D7 is district-level. Census labour is from 2011.
- Associations are not causes. Villages cluster in space; the CIs are tehsil-clustered, but the Mann-Whitney p-values are not.
