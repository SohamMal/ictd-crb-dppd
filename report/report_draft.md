# Finding Positive Deviants in Crop Residue Burning: A Data-Powered Positive Deviance Study of Punjab Tehsils

**Soham Malvadkar** · mcs262493@cse.iitd.ac.in · IIT Delhi, COL7761 ICTD, 2026
Supervisor: Prof. Aaditeshwar Seth · Advisors: Basma Albanna, Andreas Pawelke

> **Draft status (14 Oct 2026).** Sections 1–3.3, 4.1, 5 and 6 are written from frozen outputs. Sections marked ⏸ wait for the burn measure (Section 3.4). Every number cites the file that produced it; regenerate figures with `python Code/figures/make_grouping_figures.py`.

---

## Abstract
⏸ *Write last.*

---

## 1. Introduction

Every October and November, farmers in Punjab burn paddy straw to clear their fields for wheat. The window between the paddy harvest and wheat sowing is short. Burning is the cheapest and fastest way to clear the straw. The smoke is a major seasonal contributor to air pollution across the Indo-Gangetic Plain and in Delhi NCR [1]. Since 2018 the government has subsidised crop residue management (CRM) machines such as the Happy Seeder and Super Seeder, expanded Custom Hiring Centres, and promoted short-duration paddy varieties. Yet farmers still cite rental cost, machine availability in the narrow sowing window and doubts about yields as reasons to keep burning [2, 3].

Burning is not uniform, even between places that look alike in climate, cropping and nominal access to the same schemes [4]. Most existing work estimates aggregate emissions, compares satellite sensors, or explains *average* adoption behaviour [5, 6]. This project asks a different question: **which places already burn much less than places like them, and what are they doing differently?**

That question is the core of **Data-Powered Positive Deviance (DPPD)** [7, 8]. DPPD uses data to find *positive deviants*: units that achieve much better outcomes than their peers despite facing the same constraints. Their practices are, by construction, feasible under local conditions. That makes them more credible to other farmers and officials than solutions imported from elsewhere.

**Scope.** This study covers the **97 current tehsils of Punjab** (LGD codes). Tehsils are fine enough that good performers are not hidden in district averages, and coarse enough that every dataset is reliable at this level. Haryana was in the original proposal. It was deferred because several of its datasets are incomplete (Section 5).

**Contributions so far.**
1. A reproducible, fully coded **homogeneous grouping** of Punjab's tehsils into three peer regions (Central 63, South-west 18, Foothills 15) plus one outlier. It is built only from structural conditions and stress-tested for stability and sensitivity (Sections 3.3, 4.1).
2. A **data-quality audit** of satellite products commonly used for Punjab. Chen et al.'s rice map is biased by region; satellite cropping intensity disagrees with official statistics; and in Sentinel-2, burnt fields cannot be told apart from freshly ploughed fields over a season (Section 5).
3. ⏸ Positive deviant tehsils (static and temporal) and the factors that distinguish them.

---

## 2. Data

All variables are brought to the 97 current tehsils. Each variable stays at its native resolution (village, block, district) and is inherited downward through crosswalks, then rolled up to the tehsil. Prof. Seth approved this mixed-resolution design.

**Table 1. Datasets.** *(G = used in grouping; P = performance measurement; X = examined and dropped)*

| Variable | Source | Native level | Year(s) | Use | Notes |
|---|---|---|---|---|---|
| Village boundaries | SHRUG v2.2, Development Data Lab [9] | Village (Census 2011) | 2011 | Base layer | 12,808 Punjab villages |
| Tehsil boundaries | Esri India `IAB_Subdistrict_2024`, LGD codes | Tehsil | 2024 | Base layer | 97 tehsils; Σ area 50,371 km² vs official 50,362 km² |
| 2011 ↔ current crosswalk | Built from LGD directory exports (21 Sep 2026) | Village → tehsil | — | Base layer | 45 tehsils unchanged, 43 carved from a 2011 tehsil, 9 drawn from several |
| Rice area | Chen et al. 10 m paddy map [10], calibrated to official district rice area [11] | 10 m pixel → tehsil | 2022 (official 2021-22) | G | `rice_share_2022_cal` = rice area / tehsil area |
| Monsoon rainfall | CHIRPS daily, Google Earth Engine [12] | ~5 km → village → tehsil | 2020–2025 mean, Jun–Sep | G | `mean_monsoon_rainfall_mm` |
| Agro-ecological sub-regions | NBSS&LUP AESR 2018 polygons, Bhoomi Geoportal [13] | Polygon (~1:4M) | 2018 | G | Share of tehsil area in zones 14.2, 2.5, 4.1, 9.1 |
| Groundwater stress | CGWB, *Ground Water Resources of Punjab* (as on 31.03.2022) [14] | Block → village → tehsil | 2022 | G | Stage of extraction, % of annual recharge |
| Soil | NBSS&LUP 1:250K soil map [13] | Map unit → 2011 tehsil → village → tehsil | static | G | 8 categorical descriptors (particle size, drainage, texture, depth, pH, salinity, sodicity, erosion) |
| Cropping intensity | Own Sentinel-2 NDVI season count (GEE) | Village → tehsil | 2022–24 | X | Dropped: Spearman ρ = 0.18 vs official (Section 5) |
| Terrain | Village elevation and slope (GEE export) | Village → tehsil | static | X | Dropped: defective slope values (Section 5) |
| NARP agro-climatic zones | ICAR-CRIDA district contingency plans | District | — | X | Dropped: district-level, missing for 2 districts |
| Burn labels | CEEW, *Patterns of Crop Residue Burning* v2 [15] | Field polygons | 29 Oct 2021, 10 Nov 2020 | P | 438 fields labelled from very-high-resolution imagery; CC BY-NC 4.0 |
| Burn imagery | Sentinel-2 SR Harmonized, GEE | 10–20 m | 2020–2024 | P | BAIS2 + Tasseled Cap Brightness |
| Active fires | NASA FIRMS (MODIS/VIIRS) | 375 m – 1 km | — | X / fallback | ~3.7× fewer detections than Sentinel-2 burnt area |

---

## 3. Methodology

### 3.1 The DPPD pipeline
We follow the DPPD handbook [8]:

1. **Assess problem–method fit.** Is the outcome measurable, does it vary, and do some units plausibly outperform peers through their own practices?
2. **Determine positive deviants.**
   (a) *Performance measurement:* a tehsil-level burning measure.
   (b) *Homogeneous grouping:* sort tehsils into peer groups that share the same structural conditions.
   (c) *PD identification:* tehsils that burn far less than their own group.
   (d) *PD validation:* check that deviants are not artefacts of measurement or grouping.
3. **Discover underlying factors.** Explain what the deviants do differently.

Grouping (2b) was deliberately done **before** performance measurement. This ensures the peer groups cannot be shaped, even unintentionally, by knowledge of who burns.

### 3.2 Grouping variables

**Rule.** A grouping variable must be a *structural, non-transferable* condition: something a tehsil cannot change through its own choices, which shapes how hard it is to avoid burning. Hypothesised *drivers* of burning (CRM machine density, mandi access, awareness campaigns) are excluded. They are what Stage 3 must discover; grouping on them would hide exactly the deviance we want to find. **Burning outcomes are never used to build groups.**

**Table 2. Final grouping dimensions (frozen v4, 7 Oct 2026; `outputs/grouping/FROZEN_config.json`).**

| # | Dimension | Variable(s) | Why it is structural and relevant to burning |
|---|---|---|---|
| 1 | Rice | Calibrated rice share of tehsil area, 2022 | More paddy means more straw to clear in the same short window |
| 2 | Rainfall | Mean monsoon (Jun–Sep) rainfall, 2020–25 | Drives irrigation need and crop timing; separates the arid south-west from the wetter centre |
| 3 | Agro-ecological zone | Share of area in AESR 14.2, 2.5, 4.1, 9.1 | Combined climate, landform and growing-period class; separates the Siwalik foothills from the plains |
| 4 | Groundwater | Stage of extraction 2022 (%) | Under Punjab's groundwater law, paddy transplanting is delayed to save water. A later transplant means a later harvest and less time before wheat |
| 5 | Soil | 8 NBSS&LUP descriptors (categorical) | Affects drainage, workability and how easily wheat can be sown into residue |

**Variables considered and removed** (details in Section 5):
- *Cropping intensity:* the satellite estimate could not be validated, and removing it changed only 2 borderline tehsils.
- *Terrain (elevation, slope):* the slope data were defective. AESR zones replaced terrain because they capture the foothill/plain contrast from a published source.
- *District NARP zones:* too coarse.
- *Temperature and rainfall variability:* not included. This is an untested assumption, stated as a limitation.

### 3.3 Grouping method
Code: `Code/grouping/` (`config.py`, `gower.py`, `cluster.py`, `evaluate.py`, `stability.py`, `sensitivity.py`, `freeze.py`). All outputs are in `outputs/grouping/`. Master input SHA-256 is recorded in `FROZEN_config.json`.

**Step 1: Distance between every pair of tehsils (dimension-balanced Gower).** The variables mix numbers (rainfall in mm, shares) and categories (soil texture), so we use Gower distance [16]. It turns each difference into a 0–1 score:
- **Numeric columns:** |a − b| / range.
- **Categorical columns:** 0 if the same, 1 if different.
- **Missing values:** that column is skipped for that pair.

Standard Gower averages all columns equally, so a dimension with many columns (soil has 8) would get 8 votes. That would overpower rainfall (1 vote). We therefore **average columns within each dimension first, then average the 5 dimensions with equal weight (1/5)**. Every dimension gets one equal vote.

The outlier Dhar Kalan (a hill tehsil with 7% rice and 1,604 mm rain) is excluded when computing each column's range. Otherwise its extreme values would stretch the ruler and compress everyone else's differences by about 12%. Its own differences are capped at 1.

*Why equal weights?* There is no agreed evidence that any one condition matters more for burning. Equal weights are the neutral default in composite-indicator practice. We test the choice explicitly instead of assuming it (Step 5).

**Step 2: Hierarchical clustering (average linkage).** We start with every tehsil as its own group and repeatedly merge the two groups with the smallest average pairwise distance. This produces a merge tree (Fig. B), and cutting it at different heights gives 2, 3, 4, … groups. We chose average-linkage hierarchical clustering because:
- it works directly on a custom distance matrix (k-means cannot);
- it does not force groups to be round or equal-sized;
- the tree shows how groups relate;
- Prof. Seth endorsed it.

**Step 3: Choosing the number of groups (silhouette).** For each tehsil, the silhouette compares how close it is to its own group versus the nearest other group (+1 clearly placed, 0 on a border, below 0 closer to another group). We set aside groups with fewer than 5 tehsils (a peer group needs enough members to compare against). Then we read the silhouette alongside group sizes and interpretability.

**Step 4: Stability (bootstrap).** We draw 80% of tehsils at random, regroup them, and compare the result with the full-data grouping using the Adjusted Rand Index [17] (1 = identical, 0 = no better than chance). We repeat this 300 times (seed 42). From the same resamples we compute:
- *group survival:* how often each group reappears as its own group;
- *switch rate:* per tehsil, how often it lands in a different group when its own group survives.

Tehsils with a switch rate above 20% are flagged **borderline**. Each tehsil's final group is its **consensus** group, the one it lands in most often across resamples. This reduces dependence on a single tree cut.

**Step 5: Sensitivity (one factor at a time).** We change one design choice at a time and measure ARI against the frozen grouping:
- each dimension's weight ×0.85 and ×1.15;
- each dimension dropped;
- soil without its near-constant descriptors.

**Step 6: Freeze rule.** A grouping is frozen when it meets four conditions:
- groups of at least 5 tehsils;
- mean bootstrap ARI ≥ 0.8;
- groups that make agronomic sense;
- known weak points documented (borderline tehsils, weight-sensitive boundaries).

### 3.4 Performance measurement ⏸
*Status: method chosen, scaling blocked (Section 5, D11). Write once the burnt-vs-ploughed rule is settled.*

Decided so far:
- **Indicator:** BAIS2 [18] + Tasseled Cap Brightness on Sentinel-2. A logistic boundary trained on CEEW fields scored 95.5% accuracy and 98.1% recall in 5-fold cross-validation, versus 81.3% accuracy for NBR.
- **Cropland:** look for burns on all cropland (ESA WorldCover), not only on Chen's rice map, because that map is biased by region.
- **Season:** 15 Sep – 30 Nov, the ISRO protocol used by CAQM.
- **Tehsil metric:** burnt area / calibrated rice area, over 5 seasons (2020–2024).
- **Open:** a rule that does not count freshly ploughed soil as burnt.

### 3.5 PD identification ⏸
Decided so far:
- **Static deviance:** lowest burning relative to its own group.
- **Temporal deviance:** fastest reduction in burning over five years relative to its own group's trend (suggested by B. Albanna). Comparing each tehsil with its own past cancels out unmeasured fixed differences.
- A tehsil good on both is the strongest PD.
- A PD must hold under both the 3-region and the 2-group (Plains / Foothills) grouping.

Open: threshold rule and trend estimator.

### 3.6 PD validation ⏸ · 3.7 Discovering underlying factors ⏸

---

## 4. Results

### 4.1 Homogeneous groups

**Three peer regions and one outlier** (`outputs/grouping/FROZEN_groups.csv`; Fig. A):

| Group | Tehsils | Median rice share | Median monsoon rain | Median GW extraction | Dominant AESR | Character |
|---|---|---|---|---|---|---|
| Central | 63 | 75% | 721 mm | 230% | 9.1 / 4.1 (semi-arid plains) | Paddy-dominated plains, most over-exploited groundwater |
| South-west | 18 | 59% | 467 mm | 118% | 2.5 (arid western plain) | Dry cotton–paddy belt, less paddy, lower groundwater stress |
| Foothills | 15 | 28% | 981 mm | 117% | 14.2 (Siwalik foothills) | Wet, hilly Kandi belt, least paddy |
| Outlier | 1 (Dhar Kalan) | 7% | 1,604 mm | 27% | 14.2 | Hill tehsil unlike any other; set aside |

*(Medians from `Data/punjab_homogeneous_grouping_master_transformed.csv` joined to the frozen labels; Fig. C.)*

**Location was never given to the method, yet the groups form three geographically connected regions.** They match Punjab's known agro-ecological belts: the central plains, the Malwa south-west and the Kandi/Siwalik foothills (Fig. A). This is strong evidence that the grouping captures real structure rather than noise.

**Quality** (`outputs/grouping/stability_by_k.csv`, Fig. D):
- Silhouette **0.377**, mean bootstrap ARI **0.890** (5th percentile 0.563). Group survival: Central 100%, Foothills 100%, South-west 93.7%.
- The 2-group alternative (Plains 81 / Foothills 15) is even more stable: silhouette 0.409, ARI **0.981**. It nests exactly: Central + South-west = Plains.
- Cuts at k = 4 and 5 give the same three groups (smaller fragments fall below 5 tehsils). At k = 6, Central splits and stability falls to ARI 0.71.
- Only **3 tehsils are borderline** (switch rate > 20%): Firozpur and Faridkot (South-west / Central border) and Dinanagar (Central / Foothills).

**Sensitivity** (`outputs/grouping/sensitivity_table.csv`, Fig. E):
- 10 of 12 weight changes keep ARI ≥ 0.83, moving at most 5 tehsils.
- The South-west / Central boundary is the weak point. 15% more weight on rice or soil, or dropping any one dimension, merges the South-west back into Central (ARI 0.48–0.60).
- The Foothills / Plains split survives every test.

*Interpretation:* the South-west is real, since it shows up in rainfall, zones and groundwater together. But it shades gradually into the centre across Malwa rather than meeting it at a sharp line. We therefore keep three groups (so Bathinda is not judged against Ludhiana) and require every candidate deviant to hold under the 2-group version too.

### 4.2 Burn measurement ⏸ · 4.3 Positive deviants ⏸ · 4.4 Predictors ⏸

---

## 5. Difficulties encountered, how we tackled them, and what remains

Many of the hardest parts of this project were data problems, not modelling problems. We record them because they affect how far the results can be trusted, and because others using the same public datasets for Punjab will hit them too.

**Table 3. Difficulties.** *(Status: ✅ resolved · ◐ partly resolved, residual limitation · ⛔ open / blocking)*

| # | Difficulty | How we found it | How we tackled it | Status / plan |
|---|---|---|---|---|
| D1 | **Unreproducible early results.** The first grouping (3 groups 25/14/57, ARI 0.572, silhouette 0.287) came from a ChatGPT session with no code. | No script could regenerate the numbers. | Rebuilt the whole pipeline (Gower → HAC → silhouette → bootstrap → sensitivity) in Python, step by step, checking distances against hand calculations. All reported numbers now come from `Code/grouping/`. The rebuilt sensitivity contradicted the earlier claim that ±15% weights moved groups a lot. | ✅ |
| D2 | **Changing boundaries.** Most data are keyed to 2011 Census villages and tehsils; Punjab now has 23 districts and 97 tehsils, many carved out of old ones. | ID mismatches when merging datasets. | Built village- and tehsil-level bridges from LGD exports (45 unchanged, 43 carved, 9 drawn from several 2011 tehsils), so every village is traced to its current tehsil. One bridge variant proved unreliable and was excluded. | ✅ (8 of 12,808 villages unaccounted; negligible at tehsil level) |
| D3 | **Stale rice data.** The village rice file's "2022" column was a copy of 2020 (98.6% identical). | Comparing year columns. | Recomputed rice area directly from Chen et al.'s 2022 GeoTIFF over current tehsil polygons, with geodesic pixel areas. | ✅ |
| D4 | **Rice area confounded by tehsil size.** Total rice hectares mostly measure how big a tehsil is. | Rice ha vs rice share: Spearman 0.52 only. | Switched to rice share (rice area / tehsil area). | ✅ |
| D5 | **Regional bias in the satellite rice map.** Chen 2022 over-maps rice in the south-west cotton belt and foothills (Fazilka ×1.71, SAS Nagar ×1.41, Hoshiarpur ×1.40, Bathinda ×1.37) and under-maps central Punjab (×0.76–0.93). | The south-west looked more paddy-dominated than Sangrur/Patiala, against agronomic knowledge. Checked against official district rice area (Statistical Abstract 2022). Fig. F. | Calibrated: each tehsil's Chen rice area is scaled so its district total matches the official figure. Chen decides how rice is spread *within* a district; official statistics decide the district total. | ◐ Within-district errors remain (e.g. cotton pixels inside a Bathinda tehsil). The burn measure avoids using Chen as a mask. |
| D6 | **Unreliable satellite cropping intensity.** Our Sentinel-2 CI hardly agreed with official district CI (ρ = 0.18), was higher almost everywhere (up to +44 points), and swung 20–32 points between years in 6 tehsils. Part of the GEE script was missing. | Aggregating to districts and comparing with Statistical Abstracts. | Tested its influence: dropping CI, or substituting official CI, moved only 2 borderline tehsils (ARI 0.93). Dropped CI from the grouping; stability improved (ARI 0.89, borderline tehsils 9 → 3). | ◐ A validated tehsil-level CI is future work. |
| D7 | **Defective terrain data.** Different tehsils had identical slope values with zero variation between villages (e.g. Dhar Kalan and Pathankot both 1.046, despite 578 m vs 296 m elevation). | Investigating why Nawanshahr sat with the foothills. | Replaced the terrain dimension with official agro-ecological zones (AESR 2018), which capture the foothill/plain contrast from a published source. | ✅ (noted as a data-quality limitation) |
| D8 | **No zone data finer than district.** Official NARP zones are assigned by district (Patiala is listed in three zones), and two districts had none. | Coverage check on the zone master. | Found the NBSS&LUP AESR 2018 zone polygons on the Bhoomi Geoportal. Bulk download (WFS) is disabled, so we wrote a script that pulls each polygon through repeated point queries (WMS GetFeatureInfo) until 99.99% of Punjab was covered, then computed each tehsil's area share per zone. Shares, not a single label, because 21 tehsils are genuinely split. | ✅ |
| D9 | **Coarse zone map loses the dry south-west.** AESR's arid zone (≈1:4M scale) also covers 12 wetter central tehsils, so zones alone merged the south-west into the centre (ARI 0.41). | Exploratory runs of alternative designs. | Kept rainfall alongside zones (zones replace terrain only), which recovers the south-west (ARI 0.90 vs earlier design). Overlap accepted: AESR classes are partly defined from rainfall. | ✅ |
| D10 | **Soil data access and resolution.** Bulk export disabled; one soil sample per 2011 tehsil; several descriptors nearly constant (96/97 tehsils "Deep"). | Inspecting descriptor distributions. | Point queries at tehsil centroids; soil kept as original categories (not one-hot, which would count one difference several times); tested dropping near-constant descriptors (ARI 0.96) and kept all 8. | ◐ Carved tehsils inherit their parent's soil. |
| D11 | **Burnt fields look like ploughed fields.** Over a season, almost every field is eventually flagged "burnt": 94.6% of 279 random cropland points in 2022, and 92% of fields CEEW saw unburnt. Char and freshly tilled soil have almost identical Sentinel-2 spectra (BAIS2 AUC 0.51 for char vs soil). No tested index, threshold set (ours, CEEW's, Naeher & Ziulu's) or classifier separated them. | Season-long transfer checks, then a direct char-vs-soil comparison on CEEW fields. | Confirmed it is a known limit of 10–20 m imagery: Walker et al. [6] report Sentinel-only no-burn accuracy of 0.51. Narrowed the window to the official season (15 Sep–30 Nov). Reviewed tillage-detection literature; timing-based methods (Jain group, 2024) are a partial route. With Prof. Seth's approval, wrote to B. Albanna and A. Pawelke (12 Oct) about how their Nile Delta study handled it. | ⛔ Awaiting advisors' reply. **Fallback by 15 Oct:** see Section 6. |
| D12 | **Cloud mask discarded burnt pixels.** Sentinel-2's scene classification labels fresh char "dark area" or "unclassified", so the original mask kept only 3 of 54 burnt fields on the 2020 date. The reported 95.5% was effectively tested on one date and area. | Checking which pixels survived the mask. | Widened the mask (SCL 2, 4, 5, 7): 436/438 fields kept. Cross-date transfer: 100% and 96.1% accuracy. | ✅ |
| D13 | **Early burn-index failures.** NBR change detection mistakes harvest itself for burning; BAIS2 first performed badly. | Validation against CEEW fields. | NBR rejected; the BAIS2 failure was traced to a simplified formula. The full red-edge formula [18] fixed it. | ✅ |
| D14 | **Active-fire counts undercount.** FIRMS/VIIRS detects ~3.7× fewer burns than Sentinel-2 and misses small and late-afternoon fires. | Comparison with Sentinel-2 burnt area. | Not used as the main measure; kept as a consistent fallback (constant satellite set S-NPP + NOAA-20 across years). | ◐ |
| D15 | **Visual labelling infeasible.** Hand-labelling burnt vs ploughed in 10 m image chips was not possible (one clear smoke event in 60 points). | Labelling tool built and attempted. | Switched to CEEW fields as a natural experiment (same fields on the burn date vs a month later). | ✅ (method), feeds D11 |
| D16 | **Equal weights need justification.** | Supervisor feedback. | Tested rather than assumed: weights ±15% (Fig. E). Most perturbations leave groups intact; the South-west boundary is weight-sensitive, so PDs must hold under the 2-group version too. | ◐ |
| D17 | **A gradual boundary.** The South-west / Central border is a gradient across Malwa. A single tree cut placed 5 border tehsils in the South-west although they sat with Central in most resamples. | Bootstrap switch rates. | Consensus assignment across 300 resamples; separate group-survival and tehsil-switch measures; borderline flags; PD rule tied to both groupings. | ✅ |
| D18 | **Practical computing issues.** Windows Smart App Control blocked newer library builds; long Earth Engine exports stalled or dropped connections. | Failed installs and runs. | Pinned working versions (e.g. pyproj 3.6.1); added retries, resume-from-checkpoint and caching to GEE scripts. | ✅ |
| D19 | **Scope cut to Punjab.** Haryana lacks numeric groundwater data (category only), a complete crosswalk and consistent soil/CI sources. | Data inventory. | Punjab first, as agreed with the supervisor; the pipeline is configurable so Haryana can be added. | ◐ Future work |

---

## 6. Limitations and future work

**Limitations of the grouping**
- Rice share uses one year (2022) and is only corrected at district level (D5).
- Rainfall uses a 5-year window (2020–2025) rather than a 15- or 30-year normal.
- Temperature and rainfall variability were not included (untested assumption).
- Soil is effectively one sample per 2011 tehsil (D10).
- Equal weights are a design choice; the South-west boundary is sensitive to them (D16).
- 97 units is a small sample; the outlier Dhar Kalan cannot be benchmarked.

**Limitations of the burn measurement** ⏸ (complete after D11 is resolved)
- Validation labels come from expert image interpretation on two dates in two small areas, not field visits.
- Char vs ploughed-soil confusion (D11).

**Fallback plan for D11 if no advisor guidance arrives by ~15 Oct** ⏸ *(proposed, to confirm with Soham)*
Options, to be chosen with evidence:
1. Count a field as burnt only when it moves from bright stubble to char within a few days (needs a harvest date). Ploughing usually comes after burning, so the first transition is more telling than a season union.
2. Use VIIRS active-fire counts per rice hectare as the main measure. They undercount, but consistently, which matters most for *relative* comparison within peer groups.
3. Report both, and trust only PDs that agree.

**Future work**
- A validated tehsil-level cropping intensity (tuned thresholds, checked against Statistical Abstracts).
- Higher-frequency imagery (PlanetScope) or timing-based tillage classification to separate burning from ploughing.
- Extend to Haryana once its crosswalk and groundwater data are complete.
- Village-level PD analysis inside PD tehsils, and field interviews to validate Stage 3 findings.
- A longer rainfall normal and sensitivity to temperature.

---

## 7. Conclusion ⏸

---

## Figures
| Fig | File | Caption |
|---|---|---|
| A | `outputs/figures/fig_A_group_map.png` | Frozen homogeneous groups of 97 Punjab tehsils. Hatched = borderline (switch rate > 20%). Groups were built without any location information. |
| B | `outputs/figures/fig_B_dendrogram.png` | Average-linkage merge tree on dimension-balanced Gower distance; dashed line = cut into 3 groups + outlier. |
| C | `outputs/figures/fig_C_group_profiles.png` | Structural profile of each group: rice share, monsoon rainfall, groundwater extraction (dots = tehsils, bar = median) and mean AESR zone composition. |
| D | `outputs/figures/fig_D_choosing_k.png` | Silhouette and bootstrap ARI (300 × 80%) by number of groups; groups < 5 tehsils set aside. |
| E | `outputs/figures/fig_E_sensitivity.png` | One-factor-at-a-time sensitivity: ARI of each variant vs the frozen grouping. |
| F | `outputs/figures/fig_F_rice_calibration.png` | Chen et al. 2022 vs official district rice area (2021-22); labelled districts deviate > 20%. |

---

## References
*(Numbering provisional; [1]–[7] carried from Assignment 1. Check details before submission.)*

[1] Tracing the haze: satellite-based assessment of stubble burning and air quality in Delhi. PMC, 2025.
[2] L.S. Kurinji and M. Ghosh. Why are Punjab's Farmers Averse to CRM & Happy Seeder Machines? CEEW, 2024.
[3] Rajiv Gandhi Institute for Contemporary Studies. Adoption of Crop Residue Management (CRM) Machinery in Punjab. RGICS, 2024.
[4] CEEW. How Can Punjab End Stubble Burning With Crop Residue Management? 2025.
[5] K. Vadrevu and K. Lasko. Intercomparison of MODIS Aqua and VIIRS I-Band Fires and Emissions in an Agricultural Landscape. *Remote Sensing* 10(7):978, 2018.
[6] K. Walker, B. Moscona, K. Jack, S. Jayachandran, N. Kala, R. Pande, J. Xue, M. Burke. Detecting Crop Burning in India using Satellite Data. arXiv:2209.10148, 2022.
[7] B. Albanna, R. Heeks, A. Pawelke, J. Boy, J. Handl, A. Gluecker. Data-Powered Positive Deviance: Combining Traditional and Non-Traditional Data to Identify and Characterise Development-Related Outperformers. *Development Engineering*, 2022.
[8] DPPD Initiative. *Data-Powered Positive Deviance Handbook*, Nov 2021.
[9] Development Data Lab. SHRUG v2.2. ⏸ full citation
[10] Chen et al. 10 m paddy rice maps, 2024. figshare 10.6084/m9.figshare.24228619. ⏸ full citation
[11] Government of Punjab. *Statistical Abstract of Punjab 2022*, Table 4.7.
[12] C. Funk et al. The climate hazards infrared precipitation with stations (CHIRPS). *Scientific Data* 2, 2015.
[13] ICAR-NBSS&LUP. Bhoomi Geoportal: AESR 2018 and 1:250K soil layers.
[14] CGWB. *Dynamic Ground Water Resources of Punjab State as on 31.03.2022*.
[15] S.M. Ignatious, P. Rishikesh, M. Rafiuddin (CEEW). *Patterns of Crop Residue Burning*, v2. Zenodo, 2026. doi:10.5281/zenodo.20179137.
[16] J.C. Gower. A general coefficient of similarity and some of its properties. *Biometrics* 27(4):857–871, 1971.
[17] L. Hubert and P. Arabie. Comparing partitions. *Journal of Classification* 2:193–218, 1985.
[18] F. Filipponi. BAIS2: Burned Area Index for Sentinel-2. *Proceedings* 2(7):364, 2018.
⏸ Naeher & Ziulu (2025); Dipoppa & Gulzar (2024); Jain group tillage paper (2024); Arbain & Imasu (2025) as cited in Section 5.
