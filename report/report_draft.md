# Finding Positive Deviants in Crop Residue Burning: A Data-Powered Positive Deviance Study of Punjab Tehsils

**Soham Malvadkar** · mcs262493@cse.iitd.ac.in · IIT Delhi, COL7761 ICTD, 2026
Supervisor: Prof. Aaditeshwar Seth · Advisors: Basma Albanna, Andreas Pawelke

> **Draft status (10 Nov 2026).** Sections 1–6 are written from frozen outputs. Abstract, §7 and references completed 10 Nov. Every number cites the file that produced it; regenerate figures with `python Code/figures/make_grouping_figures.py`.

---

## Abstract
Paddy-straw burning in Punjab is a major seasonal source of air pollution. It continues despite years of subsidies for straw-management machines. We apply Data-Powered Positive Deviance (DPPD) to Punjab's 97 tehsils to ask which places burn much less than places like them, and why.

**Peer groups.** Tehsils are grouped only on structural conditions: rice share, rainfall, agro-ecological zone, groundwater and soil. The method is dimension-balanced Gower distance with average-linkage clustering, stress-tested for stability (ARI 0.89) and sensitivity. This gives three peer regions: Central, South-west and Foothills.

**Burn measure.** Burning is measured with a two-stage Sentinel-2 detector. A random forest, trained on field ground truth and checked against daily PlanetScope, separates burnt from freshly ploughed fields. This cuts ploughing false alarms from 81% to 18%. At tehsil level, the measure ranks tehsils like VIIRS fire counts (ρ 0.78–0.87) and is stable from year to year.

**Positive deviants.** On 2020–2024, Abohar is the only strict positive deviant: the lowest burner in the South-west and among its fastest reducers. A low-burning Doaba cluster (Dinanagar, Phagwara, Jalandhar-I, Adampur) and Talwandi Sabo also survive resampling, alternative settings and data-artefact checks. Fastest-reducer trends proved too noisy to name deviants by themselves.

**Drivers.** A desk study of nine candidate drivers from public online data, with no fieldwork, finds two things. The Doaba PDs share a tehsil-wide regional marker (urban surroundings) rather than a near-town effect. Abohar combines a local straw buyer, abundant farm labour and livestock, and an early second crop. Apparent drivers such as turnaround time and farm size mostly restate the rice-share gradient.

The pipeline is fully coded and reproducible. Its findings are leads for field validation, not causal claims.

---

## 1. Introduction

Every October and November, farmers in Punjab burn paddy straw to clear their fields for wheat. The window between the paddy harvest and wheat sowing is short. Burning is the cheapest and fastest way to clear the straw. The smoke is a major seasonal contributor to air pollution across the Indo-Gangetic Plain and in Delhi NCR [1]. Since 2018 the government has subsidised crop residue management (CRM) machines such as the Happy Seeder and Super Seeder, expanded Custom Hiring Centres, and promoted short-duration paddy varieties. Yet farmers still cite rental cost, machine availability in the narrow sowing window and doubts about yields as reasons to keep burning [2, 3].

Burning is not uniform, even between places that look alike in climate, cropping and nominal access to the same schemes [4]. Most existing work estimates aggregate emissions, compares satellite sensors, or explains *average* adoption behaviour [5, 6]. This project asks a different question: **which places already burn much less than places like them, and what are they doing differently?**

That question is the core of **Data-Powered Positive Deviance (DPPD)** [7, 8]. DPPD uses data to find *positive deviants*: units that achieve much better outcomes than their peers despite facing the same constraints. Their practices are, by construction, feasible under local conditions. That makes them more credible to other farmers and officials than solutions imported from elsewhere.

**Scope.** This study covers the **97 current tehsils of Punjab** (LGD codes). Tehsils are fine enough that good performers are not hidden in district averages, and coarse enough that every dataset is reliable at this level. Haryana was in the original proposal. It was deferred because several of its datasets are incomplete (Section 5).

**Contributions so far.**
1. A reproducible, fully coded **homogeneous grouping** of Punjab's tehsils into three peer regions (Central 63, South-west 18, Foothills 15) plus one outlier. It is built only from structural conditions and stress-tested for stability and sensitivity (Sections 3.3, 4.1).
2. A **data-quality audit** of satellite products commonly used for Punjab. Chen et al.'s rice map is biased by region; satellite cropping intensity disagrees with official statistics; and in Sentinel-2, burnt fields cannot be told apart from freshly ploughed fields over a season (Section 5).
3. A **burnt-vs-ploughed detection pipeline** for Sentinel-2. It is trained on Walker et al.'s ground truth and checked independently with daily PlanetScope in a new year and district. It cuts ploughed fields wrongly called burnt from 81% to 18% while catching 90% of burns (Sections 3.4, 4.2).
4. **Positive deviant tehsils, validated on the data.** Abohar is the only strict PD: lowest burner in the South-west and among its fastest reducers. A low-burning Doaba cluster (Dinanagar, Phagwara, Jalandhar-I, Adampur, with Gurdaspur and Banga) and Talwandi Sabo also hold up under resampling, alternative settings, cloud, rice-presence and harvest-timing checks. Temporal deviance alone proved too noisy at 100 points per tehsil (Sections 3.5, 3.6, 4.3).
5. **A desk study of drivers from public online data.** The Doaba PDs share a regional marker (urban surroundings) that is tehsil-wide, not a near-town effect. Abohar has a distinct single-case profile: a local straw buyer, abundant farm labour and livestock, and an early second crop. Apparent drivers such as turnaround time and farm size mostly restate the rice-share gradient (Sections 3.7, 4.4).

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
| Burnt vs ploughed ground truth | Walker et al. [6], field-mean Sentinel-2 and PlanetScope series (Zenodo 11225292) [20] | Field (no locations) | 2019 | P | 2,204 burnt / 223 ploughed-not-burnt fields, aligned on event day |
| Daily imagery | PlanetScope PSScene, 4-band SR + UDM2, Planet Education & Research [19] | 3 m | 25 Oct – 13 Nov 2021 | P | 19 days over the Jalandhar CEEW fields; used as an independent judge |
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

### 3.4 Performance measurement
**Why a two-stage detector.** BAIS2 [18] + Tasseled Cap Brightness (TCB) finds burns well. A logistic boundary on CEEW fields gives 95.5% accuracy and 98.1% recall in 5-fold cross-validation, versus 81.3% accuracy for NBR. But it cannot tell ash from freshly ploughed soil (D11). On Walker et al.'s ground truth (2019), it flags 98% of burnt fields **and 81% of ploughed-not-burnt fields**. Fresh ash is near-black for only 2–3 days and then fades toward the colour of ploughed soil. Daily PlanetScope separates the two well (AUC 0.96). Sentinel-2's 5-day revisit often misses those days.

**Pipeline** (`Code/planet/jalandhar_walker_model_test.py --pre-looks 1 --candidate jump`):
1. **Flag.** The BAIS2 + TCB model scores every clear Sentinel-2 look (field mean, SCL 2/4/5/7). A score above 0 marks a possible event (burnt or ploughed).
2. **Candidate.** The flagged look with the **largest rise in score** over the previous clear look. Burning is sudden; crop drying and harvest are gradual.
3. **Features.** Candidate look vs the **one clear look before it**: B2–B8, B11, B12, NDVI, NBR, NBR2, BAIS2, TCB, as post values and post − pre changes.
4. **Check.** A random forest (500 trees, balanced) trained on **Walker's ground truth** (burnt vs ploughed-not-burnt) decides burnt / not burnt.
5. **Cut-off.** **0.79** (keeps 90% of Walker's burns) as the main setting; 0.5 as a sensitivity check. Ploughing false alarms are the bigger threat to DPPD, because they hide tehsils that plough instead of burning.

**Role of PlanetScope.** (i) An independent judge in a new year and district (Jalandhar 2021). An automatic rule calls a field burnt if its brightness ((B+G+R+NIR)/4) falls to ≤ 0.765 of its median over the previous 15 days. (ii) Planet labels are good enough to train Sentinel-2 where no field survey exists (Section 4.2).

**Validation design.** Walker: 5-fold cross-validation. Jalandhar 2021: no retraining, no manual labels, two judges: (A) the Planet rule on the 95 fields CEEW saw unburnt on 29 Oct, followed to 13 Nov; (B) CEEW's field visit on 29 Oct (262 burnt, 95 unburnt).

**Sample points.** Each tehsil has a fixed panel of **100 random 20 m rice pixels**: pixels that are rice in *both* the Chen 2020 and 2022 maps [10]. The same points are read every season, so year-to-year change is not sampling noise. The earlier plan was to use all cropland, to avoid Chen's regional bias (D5). We changed it for two reasons. Requiring rice in two map years removes most stray pixels. And the bias in Chen is mainly *how much* rice a district has, which calibration corrects, rather than *where* it is. The residual risk (non-paddy points in the cotton belt) is tested in §3.6 (V4, V4b).

**Season and reading.** For every point and season, we take every clear Sentinel-2 look (SCL 2/4/5/7) from 15 Sep to 30 Nov, the ISRO protocol used by CAQM. Each point is read as a single 20 m pixel. In the Jalandhar gate test, a single pixel beat 3×3 and 5×5 windows at the strict cut-off, because Jalandhar fields are small.

The detector of §3.4 then runs as follows:
- **Candidate.** The look where the BAIS2 + TCB score fires (z > 0) and rises most over the previous clear look.
- **Before.** The last clear look in the 20 days before the candidate.
- **Check.** The random forest decides burnt or not burnt.
- **Unknown.** A point is "unknown" if it has no clear look in the window, or no look before the candidate. Unknown points are left out.

**Tehsil value.** Burnt share = burnt points ÷ points with a verdict, per season.
- Main cut-off: **0.786** (keeps 90% of Walker's burns); sensitivity: 0.5.
- PD seasons: **2020–2024**. 2019 is used only for the CREAMS check.
- Every PD rule is also run on **2020–2023**, because 2024 behaves differently (§4.3).
- Code: `Code/burn/tehsil_metric_rf.py` → `outputs/burn_tehsil_rf/tehsil_burn_measure.csv`.

**Units ranked.** 81 tehsils: Central 63 and South-west 18. The 15 Foothills tehsils are measured but **not ranked**. There, ash-vs-ploughed-soil confusion is worst relative to real burning, and the within-group ranking check against district figures failed (n = 4 districts). The outlier Dhar Kalan has no peers.

### 3.5 PD identification

**Two kinds of deviance** [7, 8], both measured against the tehsil's own group:
- **Static:** burns least.
- **Temporal:** cut burning fastest over 2020–2024. This was suggested by B. Albanna. Comparing each tehsil with its own past cancels out unmeasured fixed differences such as soil, farm size or local enforcement.

A tehsil good on both is the strongest PD. Negative deviants (NDs) are the mirror image and serve as the contrast in Stage 3. No regression residuals are used: every rule is a direct comparison within the group (supervisor's constraint).

**Why a log scale.** Burnt share cannot go below zero, and a few tehsils burn very heavily. On the raw scale, the handbook's outlier fence (Q1 − 1.5 × IQR [8, pp. 63–66]) falls below zero, so no tehsil can ever be a PD (VIIRS dry run: Central fence −5.76). All rules therefore use **log(value + c)**, with c = 10% of the group median. On a log scale, halving burning counts the same at any level, and the temporal trend becomes a *relative* change (% per year).

**Rules** (`Code/pd/pd_identify.py`):
- **Static PD:** the log 5-season mean lies below the group's Q1 − 1.5 × IQR, **and** the tehsil is in the group's lowest quarter in all seasons but one (4 of 5). This consistency test stops one lucky season from making a PD.
- **Temporal PD:** take the Theil–Sen slope of log(value + c) over the seasons, minus the group's median slope. The tehsil is a PD if that deviation is below Q1 − 1.5 × IQR of the group's deviations. It is reported as % per year faster than the group. Theil–Sen is used because five points are too few for an ordinary trend line to resist one odd season.
- **Candidate PD:** in the bottom 10% of the group (and, for static, the same consistency test), but not beyond the fence. These are "among the lowest", not "far from normal".
- **NDs:** the mirror image (above Q3 + 1.5 × IQR; top quarter; top 10%).

**Robustness across seasons.** Every rule is run on 2020–2024 (main) and 2020–2023 (without the weak 2024 season). Two rules are then reported side by side:
- **Old rule:** PD or candidate in both runs. This gives the broader "low-burning" set.
- **Strict rule:** beyond the fence in both runs. *Borderline* means beyond the fence in one run and a candidate in the other.

The strict rule is the headline. Being in the bottom 10% shows a tehsil is among the lowest, not that it is far from its peers.

**Grouping sensitivity.** The merged Plains grouping (81 tehsils as one group) is also run and reported. It is not used to drop PDs.

### 3.6 PD validation

The handbook asks for an initial check that a deviant is a real signal, not noise or a data artefact, before fieldwork [8, p. 67–68]. With no fieldwork or expert contact in this project, all checks are made on the data (`Code/pd/pd_validate.py`, `outputs/pd/pd_validated.csv`). Each tehsil robust under the old rule is checked; thresholds are fixed in advance.

| Check | Question | How | Rule |
|---|---|---|---|
| **V1 Sampling bootstrap** | Is the flag luck in which 100 points were drawn? | Redraw each tehsil-season's verdicts with replacement (binomial), rerun both runs, 1,000 times | Flag kept in ≥ 80% of draws = pass; 50–80% = flag; < 50% = fail |
| **V2 Settings** | Does the flag depend on our choices? | Cut 0.5; offset c 5% and 20%; alternative grouping (rainfall weight × 0.85, which moves 5 tehsils from Central to South-west) | Kept in all scenarios but one = pass |
| **V3 Clear looks** | Do cloud gaps hide fires? | Unknown-point share and clear looks per point vs group | Unknown share > 2× group median (and > 1 point) = flag |
| **V4 Rice** | Is there less paddy to burn? | Calibrated rice share; share of points where a paddy harvest is seen | Below group Q1 on either = flag |
| **V4b Harvest-confirmed** | Do non-paddy points pull the score down? | On the 30-point harvest panel: burnt share on all points vs only points with a harvest seen that season; same rules | Flag survives on all points but is lost on confirmed points = flag |
| **V5 Timing** | Is harvest so late that burning falls outside the window? | Median harvest date vs group | ≥ 10 days later = flag |
| **V6 Triangulation** | Do independent sources agree? | VIIRS fire-count flags; CREAMS district rank | Information only |

**Final label.** Any fail → *dropped*. At most one flag → *validated PD*. More flags → *PD with caveat*. NDs get V1–V3 and the label *contrast*.

Two further checks were planned and not done. A blind visual check of 120 points on Sentinel-2 images (V7) was built but not labelled. Sharing the list with local experts (V8) was dropped, because the project uses no human contact. Both are stated limitations.

### 3.7 Discovering underlying factors

**Approach.** DPPD normally confirms positive deviants and their practices through fieldwork. This project is academic and uses no fieldwork, interviews or expert consultation. Stage 3 is therefore a **retrospective desk study on public online data**, which the handbook allows when field engagement is not possible [8, p. 77–78]. The aim is to find *candidate* explanations that a later field study could test. The aim is not to prove causes.

**Drivers, not conditions.** A driver is something that could, in principle, be changed or transferred: a crop rotation, a market for straw, a labour arrangement. Structural conditions (rainfall, soil, rice share, groundwater, zone) were used to build the peer groups (§3.2) and are never re-used as drivers. We started from a catalogue of hypothesised drivers drawn from the literature and news, and kept those with public data at tehsil or district level for 2019 or later. Older data was used only as a fallback.

**Table 3. Drivers.** *(T = tehsil level; D = district value given to every tehsil in it)*

| # | Driver | Why it might lower burning | Source | Level, year |
|---|---|---|---|---|
| D1 | Harvest-to-wheat turnaround | More days to manage straw without fire | Sentinel-2 NDVI at the 30-point panel: harvest = drop below 0.30 after ≥ 0.45; green-up = sustained ≥ 0.30; sowing = green-up − 28 d (checked against CIMMYT farmer-reported dates [21]) | T, 2020–24 |
| D2 | Early second crop (potato, vegetables, fodder) | These crops are sown in October, so straw must be cleared by other means | Share of harvested points with NDVI ≥ 0.6 by 30 Nov (wheat sown 1–15 Nov cannot reach full canopy that early) | T, 2020–24 |
| D3 | Farm labour; small farms | Labour for manual straw handling; small farms less able to afford machines | Census 2011 village Primary Census Abstract [22]: agricultural labourers per cultivator; cultivators per 100 ha rice | T, 2011 |
| D4 | Straw buyers | A buyer makes burning a lost sale | 14 biomass power and compressed-biogas plants compiled from news, one source per plant [23–25]; plants within 30 km, km to nearest | T, 2017–25, town-level |
| D5 | Distance to state border | Burning rises where smoke drifts into another jurisdiction [26] | SHRUG 2011 district polygons [9] | T |
| D6 | Urban surroundings | Smoke is noticed; off-farm work; vegetable markets | JRC GHS-SMOD 2020 settlement model, 1 km [27]: urban area share (classes ≥ 21); km to urban centre (class 30) | T, 2020 |
| D7 | Basmati share | Basmati straw is fed to cattle and less often burnt | APEDA Basmati Crop Survey 2023 [28] ÷ official rice area 2021-22 [11] | D, 2023 |
| D8 | CRM machines and hiring centres | Machines clear straw without fire | No district-level table online, only state totals → **dropped** | — |
| D9 | Livestock | Straw used as fodder or bedding | 20th Livestock Census 2019, village level [29], matched to Census 2011 villages (91.8% of cattle and buffalo matched) | T, 2019 |

**Comparison.** All comparisons are made inside the frozen groups (Central 63, South-west 18), in three ways:
1. **Profiles.** For each PD and ND, its value and percentile in its group. For each driver, we count how many PDs sit on the side of the group median that the hypothesis predicts, and how many NDs sit on the other side.
2. **Rank correlation** (Spearman ρ) between the driver and the 2020–24 mean burnt share, across all tehsils in the group.
3. **Partial rank correlation with rice share held constant.** Within groups, burning still rises with rice share (ρ 0.70 in Central, 0.63 in South-west; §3.6). A driver that only stands in for "less paddy" would show a correlation for that reason alone. We therefore remove the rank of rice share from both the driver and burning, then correlate what is left. This is analysis, not PD identification, so the rule against regression-based PD identification does not apply.

With 8 PDs and 4 NDs, the comparison is **descriptive**. We ran 44 correlation tests (11 drivers × 2 groups × 2 versions), so about two would pass p < 0.05 by chance alone. We only lean on patterns that repeat across the three readings.

**Urban check.** The driver with the clearest pattern, urban surroundings, was tested further at the level of the 100 sample fields per tehsil. Do fields near a town burn less than fields far from towns *in the same tehsil*? We compared each field's verdict with its tehsil-season mean (so tehsil-wide differences cancel out), estimated the slope on log distance, and drew 95% intervals from 1,000 bootstrap resamples of whole tehsils. We then re-scored each PD using only fields more than 5 km from an urban centre.

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

### 4.2 Burn detection: burnt vs ploughed

**Table 4. Walker ground truth, 2019, 5-fold cross-validation** (`outputs/burn_basma/w1_*.csv`, `outputs/planet/walker_planet_*.csv`, `s2fromplanet_results.csv`).

| Method | Burns caught | Ploughed called burnt |
|---|---|---|
| Old BAIS2 + TCB (any look 0–10 d) | 98% | 81% |
| Daily Planet rule (cut-off keeping 90% of burns) | 90% | 9% |
| Sentinel-2 trained on Planet labels | 89% | 22% |
| Sentinel-2 trained on ground truth (same setup) | 89% | 16% |
| **Final model, cut-off 0.79** | **90%** | **18%** |
| Final model, cut-off 0.5 | 97.5% | 51% |

Final model AUC 0.938. Sentinel-2 trained on noisy Planet labels comes close to Sentinel-2 trained on ground truth (22% vs 16%).

**Table 5. Jalandhar 2021, Walker-trained model, not retrained** (`outputs/planet/jalandhar_walker_results_pre1_jump.csv`, `jalandhar_cutoff_sweep.csv`).

| Judge | Old detector | Final, cut-off 0.5 | Final, cut-off 0.8 |
|---|---|---|---|
| A Planet rule: burns kept | 63/63 | 51/63 | 37/63 |
| A Planet rule: not-burnt called burnt | 23/32 | 3/32 | 0/32 |
| B CEEW visit: burns kept | 257/262 | 145/262 | 89/262 |
| B CEEW visit: unburnt called burnt | 28/95 | 2/95 | 1/95 |

- Ranking burnt vs not-burnt (judge A): AUC 0.94 vs 0.89 for the old detector.
- At cut-off 0.5, CEEW completely burnt fields: 56/72 kept; partially burnt: 89/190.
- Development (judge A, cut-off 0.5): 20-day "before" median 36/63 → last clear look 47/63 → largest-jump candidate 51/63, with false alarms 2–3/32 throughout.
- No gain from: Walker-style cloud masking (identical field values); adding 86 Jalandhar Planet-labelled fields to training (52–55/63, false alarms up to 5/32); label-free cut-offs (Walker balance 0.82: 37/63; Jalandhar Otsu 0.57: 50/63).

*Interpretation:* the pipeline sharply reduces false alarms (Jalandhar 23/32 → 0–3/32; Walker ploughed 81% → 18%). The cost is missed burns, mostly partially burnt fields. For DPPD, an under-count of burns harms tehsil rankings less than ploughing false alarms, **provided the under-count is similar across tehsils** (assumption, not tested). No single cut-off is good for both ploughing (Walker) and burn catch (Jalandhar).

### 4.3 Tehsil burn measure and positive deviants

#### 4.3.1 The tehsil burn measure

Almost every point gets a verdict: 9,441–9,695 of 9,700 per season, at least 70 of 100 in any tehsil-season. Three checks support using the measure for ranking (`outputs/burn_tehsil_rf/`):

| Check | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| District order vs CREAMS [official], ρ, 22 districts | 0.75 | 0.50 | — | 0.87 (till 24 Oct) | — | — |
| State burnt %: ours vs CREAMS | 59.3 vs 37.4 | 59.7 vs 55.7 | — | 7.8 vs 9.9 | — | — |
| Tehsil order vs VIIRS fire counts, ρ, 81 tehsils | 0.79 | 0.86 | 0.87 | 0.79 | 0.78 | 0.51 |
| Same order as the next season, ρ | 0.84 | 0.91 | 0.84 | 0.82 | 0.62 | — |
| Burnt points first seen 16–30 Nov | 23% | 13% | 10% | 11% | 32% | 72% |

- **It ranks tehsils the way an independent sensor does.** VIIRS agreement is ρ 0.78–0.87, and the order is stable from year to year (0.82–0.91). The old heat-peak measure agreed with VIIRS only at 0.10–0.27. VIIRS is itself biased by farmers timing fires to avoid the satellite pass, so this is reassurance, not proof.
- **The two cut-offs give almost the same order** (ρ 0.84–0.98). The cut-off changes the level of burning, not the ranking.
- **Weak spots:**
  - The 2019 level is far above CREAMS (CREAMS changed its method between 2019 and 2020).
  - The 2020 district order is weak (0.50).
  - **2024** is the odd season: 72% of burns are first seen in late November, and agreement with VIIRS and with 2023 drops. That could be a late harvest, or ploughing and sowing being counted. Hence the 2020–2023 sensitivity run.
- **Spread of 5-season mean burnt share (2020–24):** Central median 0.62 (min 0.25, max 0.81); South-west median 0.73 (0.34–0.90).

#### 4.3.2 Positive and negative deviants

**Table 6. Robust deviants** (`outputs/pd/robust/robust_deviants.csv`; burnt share = 2020–24 mean; %/yr = trend relative to the group, main run).

| Tehsil | Group | Kind | Strict rule | Burnt share | %/yr vs group | Same flag in VIIRS dry run |
|---|---|---|---|---|---|---|
| **Abohar** | SW | static + temporal | **PD (static)**; borderline (temporal) | 0.34 | −11.1 | static PD |
| Dinanagar | C | static | borderline | 0.21 | +6.5 | candidate |
| Gurdaspur | C | static | — | 0.29 | +2.3 | — |
| Phagwara | C | static | — | 0.30 | +6.0 | candidate |
| Adampur | C | static | — | 0.30 | −4.9 | candidate |
| Jalandhar-I | C | static | — | 0.31 | −1.4 | candidate |
| Banga | C | static | — | 0.34 | +5.6 | candidate |
| Talwandi Sabo | SW | static | — | 0.50 | +14.5 | — |
| Samana | C | temporal | borderline | 0.63 | −9.1 | — |
| Dirba | C | temporal | — | 0.71 | −8.2 | — |
| *NDs:* Lehra, Zira, Moonak (C); Guruharsahai (SW) | | static | — | 0.79–0.90 | | |
| *NDs:* Batala, Majitha (C); Malout (SW) | | temporal | Malout borderline | | +7.7 to +9.9 | |

Fences on burnt share (main / 2020–23): Central 0.225 / 0.206 against a median of 0.61 / 0.58; South-west 0.454 / 0.376 against 0.73 / 0.70.

- **Abohar is the only strict PD.** It is the lowest burner in the South-west, beyond the fence in both runs, and also among the fastest reducers. It is the only tehsil good on both kinds of deviance.
- **The Doaba cluster burns about half the Central median** (Gurdaspur, Phagwara, Adampur, Jalandhar-I, Banga, plus borderline Dinanagar). But these tehsils sit together, so the fence counts them as part of the normal spread. They form a low-burning *region* rather than isolated deviants. Six of the eight static PDs were also flagged by VIIRS fire counts, so the list does not depend on one sensor.
- **Static and temporal deviants barely overlap.** Dinanagar burns least but its burning is rising (+6.5%/yr vs group). Talwandi Sabo's burning is rising fastest of all the PDs (+14.5%/yr), and it drops out under the Plains grouping.

#### 4.3.3 Validation

**Table 7. Validation of robust PDs** (`outputs/pd/pd_validated.csv`).

| Tehsil | V1 bootstrap | V2 settings kept | V3 | V4 rice | V4b | V5 | Label |
|---|---|---|---|---|---|---|---|
| Abohar (static, strict) | 0.92 | 4/4 (strict in 4/4) | ✔ | flag | ✔ | ✔ | **validated PD** |
| Abohar (temporal) | 0.92 | 4/4 | ✔ | flag | ✔ | ✔ | **validated PD** |
| Dinanagar | 1.00 | 4/4 | ✔ | flag | ✔ | ✔ | validated PD |
| Phagwara | 0.99 | 4/4 | ✔ | flag | ✔ | ✔ | validated PD |
| Jalandhar-I | 0.98 | 3/4 | ✔ | flag | ✔ | ✔ | validated PD |
| Adampur | 0.89 | 3/4 | ✔ | flag | ✔ | ✔ | validated PD |
| Talwandi Sabo | 0.97 | 4/4 | ✔ | ✔ | ✔ | ✔ | validated PD |
| Gurdaspur | 0.97 | 4/4 | flag | flag | ✔ | ✔ | PD with caveat |
| Banga | 0.72 | 4/4 | ✔ | flag | flag | ✔ | PD with caveat |
| Samana (temporal) | **0.40** | 3/4 | ✔ | ✔ | ✔ | ✔ | **dropped** |
| Dirba (temporal) | **0.39** | 3/4 | ✔ | ✔ | ✔ | ✔ | **dropped** |

- **The static list holds up.** It survives sampling noise (V1 ≥ 0.89 except Banga), the 0.5 cut, a different offset and a different grouping (V2).
- **Temporal deviance does not hold up, except for Abohar.** Samana and Dirba keep their flag in only about 4 of 10 resamples. All three temporal NDs fail the same way (Batala 0.14, Majitha 0.23, Malout 0.30). A five-season trend from 100 points per tehsil is too noisy to name a deviant on its own. A side observation: the fastest-falling Central tehsils are all in the Sentinel-2 tile overlap, where they get about twice as many clear looks. Look density may itself bias the trend (Mann–Whitney p = 0.08).
- **Rice is the main warning.**
  - Every static PD except Talwandi Sabo has less rice than three-quarters of its group (V4).
  - Across all tehsils, burning rises with rice share even inside a group (Spearman 0.70 Central, 0.63 South-west).
  - Abohar's rice map had to be scaled by 0.58, and a paddy harvest is seen at only 82% of its points (group median 98%).
  - The harvest-confirmed rescoring (V4b) shows this is **not** caused by non-paddy points pulling the score down. Points with no harvest do burn less (Central 0.16 vs 0.59), but they are few. Excluding them moves Abohar from 0.43 to 0.45 (group median 0.73) and Dinanagar from 0.22 to 0.25 (0.62). The PDs burn little on fields that really grew paddy.
  - The rice-share gradient is therefore treated as structural and carried into Stage 3 (§4.4).
  - Cotton fields that pass the harvest test are not ruled out (no visual check).
- **No timing artefact (V5).** No PD harvests 10 or more days later than its group. In the South-west, 44–47% of burns at Abohar and Talwandi Sabo are seen in the last ten days of the window, so late fires may be missed there. This affects the whole group.

**Final list for Stage 3:**
- **Validated PDs:** Abohar (static and temporal), Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo.
- **With caveat:** Gurdaspur, Banga.
- **Contrast:** the static NDs Lehra, Zira, Moonak and Guruharsahai.

### 4.4 Predictors

**Table 8. Drivers vs burning within groups.** *(ρ = Spearman with 2020–24 mean burnt share; partial = rice share held constant; \* p < 0.05, \*\* p < 0.01. Expected sign: negative if more of the driver should mean less burning. "Sides" = PDs on the expected side of the group median / NDs on the opposite side.)*

| Driver | Expected | Central ρ (partial), n = 63 | South-west ρ (partial), n = 18 | Sides PD / ND |
|---|---|---|---|---|
| **Urban area share** | − | **−0.61\*\* (−0.30\*)** | +0.45 (+0.52\*) | **7/8, 4/4** |
| km to urban centre | + | +0.12 (−0.19) | +0.08 (+0.08) | 6/8, 3/4 |
| Turnaround (days) | − | −0.38\*\* (−0.20) | +0.40 (+0.04) | 4/8, 2/4 |
| Cultivators per 100 ha rice | − | −0.28\* (−0.19) | −0.49\* (−0.05) | 5/8, 2/4 |
| Early second crop share | − | −0.16 (+0.05) | −0.56\* (−0.47, p = 0.05) | 5/8, 2/4 |
| km to inter-state border | − | +0.11 (+0.07) | **+0.83\*\* (+0.75\*\*)** | 0/8, 2/4 |
| km to nearest straw buyer | + | −0.20 (−0.26\*) | 0.00 (+0.17) | 5/8, 3/4 |
| Straw buyers within 30 km | − | +0.06 (+0.16) | +0.27 (+0.04) | 1/8, 2/4 |
| Labourers per cultivator | − | +0.08 (+0.18) | +0.16 (+0.21) | 4/8, 1/4 |
| Basmati share (district) | − | +0.01 (−0.05) | +0.14 (+0.01) | 4/8, 1/4 |
| Cattle + buffalo per cultivator | − | −0.18 (−0.02) | −0.19 (+0.06) | 4/8, 3/4 |

**1. Urban surroundings mark the low-burning Doaba belt, but as a region, not a town effect.** Urban area share is the only driver consistent on all three readings in Central:
- 7 of 8 PDs have more urban land than their group median, and all 4 NDs have less.
- Central ρ is −0.61, and −0.30 with rice share held constant.

The field-level check shows the effect is not local:
- Fields within 2 km of an urban centre burn 6 points (Central) and 8 points (South-west) less than their tehsil's average, but only 4% of fields are that close.
- Beyond 2 km, distance makes no difference. Within tehsils, moving from 1 km to 10 km adds 6.8 points of burning in Central (95% CI 3.7–10.2).
- Scored on fields more than 5 km from any urban centre, the PDs still burn as little and keep their rank:

| PD | All fields | Fields > 5 km from an urban centre | Share of fields kept |
|---|---|---|---|
| Dinanagar | 0.21 | 0.20 | 79% |
| Phagwara | 0.30 | 0.27 | 58% |
| Jalandhar-I | 0.31 | 0.32 | 40% |
| Adampur | 0.30 | 0.30 | 100% |

The low burning is therefore a tehsil-wide trait of the Doaba/Jalandhar belt. Urban share is best read as a marker of that region, together with what comes with it: potato and vegetable rotations, off-farm and overseas incomes, dense markets. It should not be read as "being near a town reduces burning". Two checks found no measurement effect near towns: missing verdicts are 0.8–1.2% and clear looks 12–13 at every distance. The marker does not carry over to the South-west, where the sign reverses.

**2. Abohar: a single-case profile.** Abohar is the only strict PD (§4.3) and is rural (urban share at the 6th percentile of South-west). Its profile differs on several drivers at once (percentile within South-west):
- a biomass power plant listed inside the tehsil, i.e. an established local straw buyer [23];
- the most agricultural labourers per cultivator in Punjab (1.61; 100th percentile);
- the highest cattle and buffalo per cultivator in its group (100th);
- the highest early-second-crop share in its group (100th);
- a basmati-heavy district (Fazilka, 57% of rice; 94th);
- 13 km from the Rajasthan border.

Each of these is a plausible route to less burning. With one tehsil they cannot be separated, so this is a lead for fieldwork, not a finding.

**3. Apparent drivers that are really rice share.** Turnaround time (Central ρ −0.38) and small farms (−0.28 / −0.49) look related to burning. Both lose their link once rice share is held constant. Where paddy dominates, harvest and sowing are more crowded and farm structure differs, so these drivers mostly restate the rice-share gradient.

**4. The border runs the "wrong" way in the South-west.** Tehsils near the Rajasthan/Haryana border burn *less* (ρ +0.83 between distance and burning; +0.75 with rice share held constant), the opposite of the cross-border pattern reported by Dipoppa & Gulzar [26]. The likely reason is the cotton belt along that border, where paddy is a more recent and less dominant crop. This is a regional pattern rather than a border effect.

**5. No consistent link:** straw buyers within 30 km, labour per cultivator across the group, district basmati share, and livestock. The straw-buyer list is town-level and partly dated (2017 biomass list; CBG start years unknown). Basmati is available only by district, and its source table does not add up for 6 districts. Both are weak tests.

**What this means for interventions (for §7 / impact).**
- The Central PDs differ from their peers as a *region*. A transferable practice would have to be found inside that region: for example, what Doaba farmers do with straw before an October potato crop. Only fieldwork can show that.
- Abohar points to three concrete, transferable levers worth testing elsewhere in the South-west: an assured straw buyer, labour for manual handling, and fodder demand.
- Turnaround and farm size cannot be used to target interventions without first allowing for rice share.

---

## 5. Difficulties encountered, how we tackled them, and what remains

Many of the hardest parts of this project were data problems, not modelling problems. We record them because they affect how far the results can be trusted, and because others using the same public datasets for Punjab will hit them too.

**Table 9. Difficulties.** *(Status: ✅ resolved · ◐ partly resolved, residual limitation · ⛔ open / blocking)*

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
| D11 | **Burnt fields look like ploughed fields.** Over a season, almost every field is eventually flagged "burnt": 94.6% of 279 random cropland points in 2022, and 92% of fields CEEW saw unburnt. Char and freshly tilled soil have almost identical Sentinel-2 spectra (BAIS2 AUC 0.51 for char vs soil). No tested index, threshold set (ours, CEEW's, Naeher & Ziulu's [30]) or classifier separated them. Published Sentinel-2 burn maps for Punjab do not handle tillage [32], although tillage itself can be detected from Sentinel-2 [31]. | Season-long transfer checks, then a direct char-vs-soil comparison on CEEW fields. | Confirmed on Walker's ground truth: 81% of ploughed fields flagged. Tried and rejected: land surface temperature (still about half of ploughed fields called burnt); Sentinel-1 radar roughness, B. Albanna's suggestion (12-day revisit, wrong direction on probably-ploughed fields). Found that ash is near-black only 2–3 days, so daily PlanetScope separates it (AUC 0.96). Built a two-stage detector: flag → largest-jump candidate → random forest trained on Walker ground truth, checked independently with Planet in Jalandhar 2021 (Sections 3.4, 4.2). | ◐ Ploughed called burnt 81% → 18% at 90% burn catch (Walker); in Jalandhar, burns are under-counted (partial burns), and ploughing itself is not tested there. |
| D12 | **Cloud mask discarded burnt pixels.** Sentinel-2's scene classification labels fresh char "dark area" or "unclassified", so the original mask kept only 3 of 54 burnt fields on the 2020 date. The reported 95.5% was effectively tested on one date and area. | Checking which pixels survived the mask. | Widened the mask (SCL 2, 4, 5, 7): 436/438 fields kept. Cross-date transfer: 100% and 96.1% accuracy. | ✅ |
| D13 | **Early burn-index failures.** NBR change detection mistakes harvest itself for burning; BAIS2 first performed badly. | Validation against CEEW fields. | NBR rejected; the BAIS2 failure was traced to a simplified formula. The full red-edge formula [18] fixed it. | ✅ |
| D14 | **Active-fire counts undercount.** FIRMS/VIIRS detects ~3.7× fewer burns than Sentinel-2 and misses small and late-afternoon fires. | Comparison with Sentinel-2 burnt area. | Not used as the main measure; kept as a consistent fallback (constant satellite set S-NPP + NOAA-20 across years). | ◐ |
| D15 | **Visual labelling infeasible.** Hand-labelling burnt vs ploughed in 10 m image chips was not possible (one clear smoke event in 60 points). | Labelling tool built and attempted. | Switched to CEEW fields as a natural experiment (same fields on the burn date vs a month later). | ✅ (method), feeds D11 |
| D16 | **Equal weights need justification.** | Supervisor feedback. | Tested rather than assumed: weights ±15% (Fig. E). Most perturbations leave groups intact; the South-west boundary is weight-sensitive, so PDs must hold under the 2-group version too. | ◐ |
| D17 | **A gradual boundary.** The South-west / Central border is a gradient across Malwa. A single tree cut placed 5 border tehsils in the South-west although they sat with Central in most resamples. | Bootstrap switch rates. | Consensus assignment across 300 resamples; separate group-survival and tehsil-switch measures; borderline flags; PD rule tied to both groupings. | ✅ |
| D18 | **Practical computing issues.** Windows Smart App Control blocked newer library builds; long Earth Engine exports stalled or dropped connections. | Failed installs and runs. | Pinned working versions (e.g. pyproj 3.6.1); added retries, resume-from-checkpoint and caching to GEE scripts. | ✅ |
| D19 | **Scope cut to Punjab.** Haryana lacks numeric groundwater data (category only), a complete crosswalk and consistent soil/CI sources. | Data inventory. | Punjab first, as agreed with the supervisor; the pipeline is configurable so Haryana can be added. | ◐ Future work |
| D20 | **Planet quota.** Education & Research access charges at least 100 km² per scene however small the clip (75 scenes = 7,500 km² of a 3,000 km²/month quota). | Quota used vs clipped area. | Used Planet only as a judge on one small area (Jalandhar CEEW fields) and through Walker's published Planet series; Sentinel-2 does the scaling. | ◐ Daily Planet cannot cover tehsils on this plan. |

---

## 6. Limitations and future work

**Limitations of the grouping**
- Rice share uses one year (2022) and is only corrected at district level (D5).
- Rainfall uses a 5-year window (2020–2025) rather than a 15- or 30-year normal.
- Temperature and rainfall variability were not included (untested assumption).
- Soil is effectively one sample per 2011 tehsil (D10).
- Equal weights are a design choice; the South-west boundary is sensitive to them (D16).
- 97 units is a small sample; the outlier Dhar Kalan cannot be benchmarked.

**Limitations of the burn measurement**
- Ploughing is validated only on Walker's data: one season (2019), two districts, no field locations, event dates uncertain by days, 128 ploughed fields.
- The Jalandhar check is small: 95 Planet-judged fields (32 not burnt), one Sentinel-2 tile, one season. Its not-burnt fields are mostly stubble, so it does not test ploughing.
- The Planet judge is imperfect: at its fixed cut-off on Walker it misses about 5% of burns and calls about 21% of ploughed fields burnt.
- CEEW labels come from expert image interpretation on two dates in two small areas, not field visits.
- Partial burns are diluted in field averages; about half are missed.
- Gaps between clear Sentinel-2 looks (e.g. 19 → 29 Oct 2021) let ash fade before it is seen.
- No single cut-off is good for both ploughing and burn catch; 0.79 is the main setting, 0.5 a sensitivity check.

**Limitations of PD identification and validation**
- PD identification rests on 100 points per tehsil. That is enough for the static ranking (V1), not for five-season trends.
- 2024 is a doubtful season (late-November burns; weaker agreement with VIIRS). Every result is also shown without it.
- The Foothills (15 tehsils) are measured but not ranked.
- No visual or field confirmation of any PD point; cotton passing the harvest filter at Abohar is not ruled out.
- Burning rises with rice share within the frozen groups. The groups control rice share only coarsely, so finer groups (or rice-share bands) are a design option for future work.

**Limitations of Stage 3**
- No fieldwork or interviews, so no practice is confirmed on the ground (academic scope).
- Small numbers: 8 PDs and 4 NDs; 44 tests, so about 2 false positives at p < 0.05.
- Mixed years: Census 2011, Livestock Census 2019, settlement model 2020, basmati 2023, burning 2020–24.
- District-level basmati cannot separate tehsils within a district (e.g. Phagwara and Kapurthala), and APEDA's district table is internally inconsistent for 6 districts.
- The straw-buyer list is town-level, the biomass part dates from 2017, and CBG start years are unknown.
- CRM machine and hiring-centre data, the scheme most directly aimed at burning, is not available by district online.
- 8% of 2019 livestock (by head) could not be matched to Census villages.

**Future work**
- A validated tehsil-level cropping intensity (tuned thresholds, checked against Statistical Abstracts).
- With more PlanetScope quota: Planet labels for more places and years (to retrain and check the Sentinel-2 model), and a direct daily-Planet measure for a demonstration tehsil.
- Pixel-level (not field-mean) detection, to recover partial burns.
- Extend to Haryana once its crosswalk and groundwater data are complete.
- Village-level PD analysis inside PD tehsils, and field interviews to validate Stage 3 findings.
- Field interviews in the Doaba PDs and in Abohar, structured around the leads above.
- District CRM machine and hiring-centre data via RTI or the Punjab agriculture department.
- A dated, geocoded straw-buyer list with collection radii.
- Tehsil-level basmati and potato maps from Sentinel-2.
- A longer rainfall normal and sensitivity to temperature.

---

## 7. Conclusion

**What we built.** We built an end-to-end, reproducible DPPD pipeline for crop residue burning, running from public data to a validated list of positive deviant tehsils and candidate explanations. Every number in this report is produced by code in the repository (`Code/`). The pipeline has three parts:
- **Peer groups** from structural conditions only, tested for stability and sensitivity (§3.3, §4.1).
- **A burnt-vs-ploughed Sentinel-2 detector.** This addresses the main weakness of season-long burn indices in Punjab, which count ploughed fields as burnt (§3.4, §4.2).
- **PD identification and validation** on the data, combining static and temporal deviance with explicit checks for noise and artefacts (§3.5, §3.6, §4.3).

**What we found.**
- **Abohar** is the clearest positive deviant: it burns least among the South-west tehsils and has cut burning faster than its group.
- A **Doaba belt** of Central tehsils (Dinanagar, Phagwara, Jalandhar-I, Adampur, with Gurdaspur and Banga) burns about half as much as the rest of Central Punjab. It does so as a region, and the difference holds on fields far from towns.
- Low burning in both places is on fields that really grew paddy. It is not an artefact of the rice map or of cloud gaps.
- Fastest-reducer trends could not be confirmed at 100 sample points per tehsil.
- Several commonly cited explanations are weaker once rice share is held constant. A shorter harvest-to-sowing window and smaller farms mostly mark the places where paddy dominates.

**What this means in practice.** The PD list shows where field teams should look first, Abohar's profile suggests three levers to test, and peer-group comparison with rice share allowed for is the fair way to rank places. Section 8 turns these leads into a proposal for field validation and a pilot.

**Limits on these conclusions.** This is an academic study:
- There was no fieldwork, so no practice is confirmed on the ground.
- Stage 3 rests on 8 PDs and 4 NDs and on public data of mixed years and resolutions.
- District data on straw-management machines, the main state intervention, was not available online.
- 2024 is a doubtful season, and the Foothills are measured but not ranked.

The results are therefore leads for field validation, not causal claims. With field access, more PlanetScope quota and district CRM data, the same pipeline would give firmer answers (§6).

---

## 8. Impact Assessment (proposal)

This section turns the study's leads into a plan that a partner could fund and run. It answers three questions:
- **What would we change?** Burning in non-PD villages, by transferring what the PDs appear to do differently.
- **How would we know it worked?** A matched, randomised pilot scored by the satellite burn measure built in this study, backed by a farmer survey.
- **What would a partner receive?** A survey instrument, a logframe, a sample-size and budget sketch, and seasonal monitoring outputs.

### 8.1 What the study implies for NGOs and government

1. **Where to look.** The PD list tells field teams where to go first: Abohar in the South-west, and the Doaba tehsils in Central Punjab. The heavy-burning NDs (Lehra, Zira, Moonak, Guruharsahai) are the natural comparison. A small field study in these places could confirm what practices differ, at a fraction of the cost of a statewide survey.
2. **What to test.** Abohar's profile points to three levers that can be transferred to other South-west tehsils and tested there:
   - an assured local straw buyer (a biomass plant within the tehsil);
   - labour for manual straw handling;
   - fodder demand from livestock.

   For the Doaba belt, the question for fieldwork is what farmers do with straw before an October potato or vegetable crop, and whether that can work in wheat-only areas.
3. **How to target.** Programmes that rank districts or tehsils by burning should compare like with like (peer groups) and allow for rice share. Otherwise they reward places that simply grow less paddy and blame places that grow more.
4. **How to monitor.** Fire counts (VIIRS) collapsed in 2024–25 as farmers timed fires to avoid the satellite pass. Field-level Sentinel-2 detection that separates burning from ploughing gives an evasion-resistant alternative. It is free, covers every season, and produces tehsil rankings that agree with fire counts in the years before evasion. The pipeline can be rerun each season and extended to Haryana.

### 8.2 Theory of change

DPPD stops at "candidate explanations" (Stage 3). The handbook's next step is to check those explanations and test whether they transfer [8]. We propose two phases:

```
PD leads (this study)
   → Phase 1: confirm in the field what PDs do differently      (1 season)
   → Phase 2: pilot the confirmed levers in matched non-PD villages (1–2 seasons)
   → measure the change in burning with satellite + survey
   → scale up through the partner if the effect holds
```

Assumptions that must hold, and where each is tested:

| Assumption | Tested in |
|---|---|
| PD practices are real, not a data artefact | Phase 1 field visits to satellite points |
| The practices are transferable (not tied to Doaba's region or Abohar's plant) | Phase 1 interviews; Phase 2 pilot |
| Farmers adopt the lever when it is offered | Phase 2 take-up indicators |
| Adoption lowers burning, not just shifts it in time or place | Phase 2 satellite outcome incl. buffer villages |

### 8.3 Phase 1: field validation (one season, Sep–Dec)

**Why first.** The main limitation of this study is that no practice is confirmed on the ground (§6). A funder will not pay for a pilot of unconfirmed levers. Phase 1 is cheap and fixes that.

**Where.**

| Role | Tehsils | Why |
|---|---|---|
| PD | Abohar | Only strict PD; single-case profile (§4.4) |
| PD | Dinanagar, Phagwara, Jalandhar-I, Adampur | Doaba belt, Central group |
| ND | Lehra, Zira, Moonak, Guruharsahai | Heavy burners in the same groups |
| Typical peer | 2 per group, near the group median **[TBD: pick by code]** | Shows what "normal" looks like |

**Village selection.** Within each tehsil, rank villages by their 2020–24 satellite burnt share and select about 6 villages spread across that range (the village-level measure is already built in `version_X/`). This gives both "PD villages inside PD tehsils" and ordinary villages for contrast.

**Activities.**
- **Farmer survey:** about 20 rice farmers per village, sampled from the village list (§8.5).
- **Focus groups:** one per village (farmers; separately labourers where possible).
- **Key-informant interviews:** block agriculture officer, the biomass/CBG plant buyer, CRM hiring-centre operators, the village sarpanch.
- **Ground truth for the detector:** visit a sample of the study's Sentinel-2 points around harvest and record burnt / ploughed / baled / standing stubble with a dated, geotagged photo. This gives the field-located ploughing check the study lacked (D11).

**Output.** A short validation note per PD: which candidate levers are confirmed, which are rejected, and which new ones appeared. Only confirmed levers go to Phase 2.

### 8.4 Phase 2: pilot of the levers (matched, randomised)

**Levers to pilot** (assuming Phase 1 confirms them; Abohar-derived, South-west group):

| Lever | What the partner provides | Cost driver |
|---|---|---|
| A. Assured straw buyer | Baler + aggregator contract linked to a biomass or CBG plant, with a fixed collection date and price | Baling and transport per tonne |
| B. Labour for manual handling | Paid labour days during the harvest–sowing window | Wages |
| C. Fodder linkage | Straw-to-dairy link (collection, storage, buyer) | Storage and transport |

The Doaba lever is not specified until Phase 1 shows what it is.

**Design.**
- **Unit:** the village. Straw collection and labour are organised by village, and burning spreads by example within a village.
- **Sampling frame:** villages in **non-PD tehsils of the same peer group** (South-west for levers A–C). The peer groups are what make treated and control villages comparable. This is the main thing DPPD adds to a standard pilot.
- **Assignment:** villages are paired on 2020–24 burnt share and rice share, then one village in each pair is randomly chosen for the lever. One arm per lever plus control, or A alone if budget is tight **[TBD with partner]**.
- **If the partner cannot randomise:** a phased (stepped-wedge) rollout, where every village eventually gets the lever but the order is random.
- **Spillovers:** a straw buyer may also take straw from neighbouring villages. Controls are drawn at least one village away from treated ones, and the villages directly next to treated ones are tracked as a separate "neighbour" group.

**Analysis.** Compare treated and control villages in the pilot season, allowing for each village's own baseline burnt share (2020–24, already measured) and its peer group (ANCOVA, §8.7). This uses the baseline more efficiently than a plain difference-in-differences, which is kept as a robustness check. Controls from the same peer group absorb weather and policy shocks that hit the whole region in the same year.

### 8.5 Outcomes and indicators

| Level | Indicator | Source | When |
|---|---|---|---|
| **Primary outcome** | Village burnt share of rice fields | Sentinel-2 detector (§3.4), all rice fields in the village rather than 10 sample points | Every season, no field cost |
| Secondary | Share of plots where the farmer reports burning | Survey, with a list experiment (below) | Baseline + endline |
| Secondary | Wheat sowing date | Survey; Sentinel-2 green-up | Endline |
| Secondary | Residue-management cost and net income per acre | Survey | Endline |
| Secondary | Wheat yield | Survey (crop cut if budget allows) | Following April |
| Take-up | Share of farmers who sold straw / used labour / supplied fodder; tonnes collected | Partner records | During season |
| Cross-check | Fire counts | VIIRS | Every season |

**Why the satellite measure is primary.** It covers every field, needs no interview, cannot be talked around, and has a five-season baseline already. Fire counts are kept only as a cross-check because farmers now time fires to avoid the satellite pass.

**Why a list experiment.** Burning is illegal, so farmers under-report it when asked directly. In a list experiment, half the farmers get a list of 4 harmless statements and the other half get the same list plus "I burnt straw on at least one plot last season". Each farmer says only *how many* statements are true, never which. The difference in average counts between the two halves estimates the share who burnt, without any farmer admitting it.

### 8.6 Survey instrument (summary)

The full questionnaire is in Appendix A. Modules:

| # | Module | Purpose |
|---|---|---|
| 1 | Household and farm | Land owned/leased, plots, crops, off-farm and overseas income |
| 2 | Paddy season | Variety (PR-126, basmati, other), harvest date, combine type (with/without SMS) |
| 3 | Residue handling per plot | Burnt / incorporated / baled / fed / mulched / left; why |
| 4 | Machines | Own or hire; Super Seeder / Happy Seeder / baler; cost; waiting time; CRM subsidy received |
| 5 | Straw market | Buyer, price, distance, who pays for baling, reliability |
| 6 | Labour and livestock | Hired labour availability and wage at harvest; cattle and buffalo; fodder use of straw |
| 7 | Next crop and timing | Wheat / potato / vegetables; days between harvest and sowing; pressure felt |
| 8 | Norms and enforcement | What neighbours do; fines, red entries, visits by officials; awareness of the rules |
| 9 | Barriers and preferences | What would make the farmer stop burning; willingness to sell straw at a given price |
| 10 | List experiment | Sensitive burning question (§8.5) |

### 8.7 Sample size

How many villages Phase 2 needs depends on two numbers, both estimated from the study's own village-level burn measure (`Code/impact/power_calc.py`; outputs in `outputs/impact/`):
- **How much burnt share varies between similar villages.** This is the noise a pilot effect has to stand out from.
- **How well a village's past seasons predict its next one.** The stronger the link, the more noise the baseline removes, and the fewer villages are needed.

**Set-up.**
- **Frame:** 1,597 South-west villages. Abohar is excluded because the levers come from there, and validated village PDs are excluded because they already burn little.
- **Pilot outcome:** 2023 burnt share.
- **Baseline:** the mean of 2020–22.
- **Analysis:** pilot season regressed on treatment, baseline and peer group (ANCOVA).
- **Test:** 80% power, 5% two-sided significance, for a drop of 5, 10 or 15 percentage points.
- **Pairing:** not credited, so the numbers err on the high side.

**What the data show.**
- Mean burnt share is 0.69, with a village-to-village SD of 0.21.
- The baseline correlates with the pilot season at r = 0.67, and allowing for it cuts the SD to 0.16.
- About 0.13 of that SD is sampling noise from the 10 points per village. A pilot that scores more fields per village is therefore much more precise.

**Table 10. Villages needed per arm (2023 as pilot season).** *(One arm = one lever, or control. With pairs, villages per arm = number of pairs.)*

| Measurement in the pilot | 5-point drop | 10-point drop | 15-point drop |
|---|---|---|---|
| No baseline, 10 points per village | 246 | 63 | 29 |
| Baseline, 10 points per village (checked by simulation) | 152 | 42 | 21 |
| Baseline, 30 points per village | 81 | 22 | 11 |
| Baseline, 100 points per village | 56 | 16 | 7 |
| Baseline, all rice fields (lower bound) | 46 | 13 | 6 |

**Checks.**
- **Simulation:** we assigned villages at random on the real data, cut the treated villages' burning by a fixed amount, and refitted the model 1,000 times. For a 10-point drop the formula's 39 villages gave 74% power, so the simulated 42 is used in Table 10.
- **Other pilot seasons:**
  - With 2022 as the pilot season, fewer villages are needed (formula: 32 instead of 39 per arm at 10 points per village).
  - With 2024, the baseline predicts much less (r = 0.31; 2024 is the doubtful season, §6). The baseline-adjusted numbers rise to 26 per arm at 30 points per village and 22 at 100.

**Recommendation.**
- Design for a **10-point drop**. That is about one-seventh of current burning, and a smaller effect would hardly justify the lever's cost.
- Score **at least 30 points per village** each season. This is free: it only needs more Sentinel-2 extraction.
- That needs **22 villages per arm**. Rounding up to **25 pairs (50 villages) per lever** allows for villages where the lever is not delivered.
- Add the neighbouring villages that are tracked for spillovers (§8.4).
- One lever plus control fits easily within the 1,597-village frame. All three levers plus control would need about 100 pilot villages.

**Caveats.**
- The "all rice fields" row subtracts estimated sampling noise. It also ignores that a more precise baseline would help further, so treat it as a rough bound only.
- Shares near 100% cannot rise, which squeezes the variation. The simulation captures this on the real data; the formula does not.

### 8.8 Recommended formats

**For data collection.**
- Tablet survey on KoboToolbox or ODK (free, works offline), in Punjabi, with GPS-tagged plots and dated photos for the ground-truth visits.
- Enumerators trained on the list experiment and on the burnt / ploughed / baled categories using example photos.

**For the partner and government.**
- **Seasonal ranking report:** tehsil and village burnt share, ranked within peer groups, produced each December by rerunning the pipeline.
- **Policy brief:** 2 pages, Punjabi and English: where the PDs are, what they do, what was piloted, and what it changed.
- **Logframe:** the table below, ready to lift into a funding proposal.
- **Open data:** anonymised village-level outcomes and code, so others can check the result.

**Logframe.**

| Level | Description | Indicator | Means of verification |
|---|---|---|---|
| Impact | Less paddy-straw burning in Punjab's South-west | Village burnt share, peer-group adjusted | Sentinel-2 detector |
| Outcome | Farmers in pilot villages manage straw without burning | Reported burning (list experiment); straw sold / fed | Survey; partner records |
| Outputs | Lever delivered on time in pilot villages | Villages served; tonnes collected; labour days | Partner records |
| Activities | Phase 1 validation; pilot set-up; baseline and endline surveys | Surveys completed; contracts signed | Field reports |
| Inputs | Enumerators, balers/contracts, labour budget, analysis time | Budget spent vs plan | Accounts |

### 8.9 Timeline

| Month | Phase 1 (year 1) | Phase 2 (year 2) |
|---|---|---|
| Jun–Jul | Ethics approval; enumerator hiring; village selection from the satellite measure | Pair and randomise villages; sign straw contracts |
| Aug | Pilot the questionnaire | Baseline survey |
| Sep–Nov | Field visits at harvest; ground-truth photos; interviews | Lever delivered; take-up monitored |
| Dec | Survey; validation note | Endline survey; satellite outcome computed |
| Jan–Mar | Analysis; decide which levers go to Phase 2 | Analysis; policy brief; scale-up decision |

### 8.10 Budget sketch **[TBD: costs to be filled with partner]**

| Line | Driver |
|---|---|
| Enumerators and supervisors | Villages × farmers × days |
| Travel and accommodation | Tehsils visited |
| Lever costs (baling, labour, fodder logistics) | Treated villages × tonnes or days |
| Tablets and software | One-time; KoboToolbox is free |
| Satellite analysis | Compute only; data are free (Sentinel-2) |
| Analysis and reporting | Researcher time |

### 8.11 Ethics

- Ethics (IRB) approval before any fieldwork; informed consent read aloud in Punjabi.
- Because burning is illegal, answers about burning are never stored with names, phone numbers or plot coordinates; the list experiment avoids direct admission altogether.
- Satellite outcomes are reported at village level or above, never per named farmer, so they cannot be used for enforcement against individuals.
- The pilot adds an option (a buyer, labour, a fodder link); it never withholds an existing scheme from control villages.

### 8.12 Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Phase 1 rejects the levers | No Phase 2 | Phase 1 is designed to fail cheaply; report what was learned |
| Bad weather or a late harvest year | Burning rises everywhere | Same-season controls from the same peer group |
| Burning moves to neighbouring villages | Effect overstated | Neighbour villages tracked separately |
| Farmers shift burning to cloudy days or late November | Satellite misses burns | Full Sep–Nov window; survey list experiment as second measure |
| Straw buyer or plant fails mid-season | Lever not delivered | Track take-up; analyse by actual delivery as well as by assignment |
| Partner capacity | Delays | Start with lever A only in a small number of village pairs |

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
[9] S. Asher, T. Lunt, R. Matsuura, P. Novosad. Development Research at High Geographic Resolution: An Analysis of Night-Lights, Firms, and Poverty in India Using the SHRUG Open Data Platform. *The World Bank Economic Review* 35(4):845–871, 2021. (Data: SHRUG v2.2, Development Data Lab.)
[10] X. Chen, R. Shen, B. Pan, Q. Peng, X. Zhang, Y. Fu, W. Yuan. A High-Resolution Distribution Dataset of Paddy Rice in India Based on Satellite Data. *Remote Sensing* 16(17):3180, 2024. doi:10.3390/rs16173180. (Data: figshare 10.6084/m9.figshare.24228619.)
[11] Government of Punjab. *Statistical Abstract of Punjab 2022*, Table 4.7.
[12] C. Funk et al. The climate hazards infrared precipitation with stations (CHIRPS). *Scientific Data* 2, 2015.
[13] ICAR-NBSS&LUP. Bhoomi Geoportal: AESR 2018 and 1:250K soil layers.
[14] CGWB. *Dynamic Ground Water Resources of Punjab State as on 31.03.2022*.
[15] S.M. Ignatious, P. Rishikesh, M. Rafiuddin (CEEW). *Patterns of Crop Residue Burning*, v2. Zenodo, 2026. doi:10.5281/zenodo.20179137.
[16] J.C. Gower. A general coefficient of similarity and some of its properties. *Biometrics* 27(4):857–871, 1971.
[17] L. Hubert and P. Arabie. Comparing partitions. *Journal of Classification* 2:193–218, 1985.
[18] F. Filipponi. BAIS2: Burned Area Index for Sentinel-2. *Proceedings* 2(7):364, 2018.
[19] Planet Labs PBC. PlanetScope imagery, Education and Research Program, 2026.
[20] K. Walker et al. burntfields_punjab v1.0.0 (code and field time series). Zenodo, doi:10.5281/zenodo.11225292.
[21] V. Krishna. Plot-level datasets for groundtruthing and satellite detection of tillage operations, Punjab (India) [2021 and 2022 plot-owner surveys]. CIMMYT Research Data & Software Repository Network, 2024. hdl:11529/10548905.
[22] Office of the Registrar General & Census Commissioner, India. *Census of India 2011: Primary Census Abstract, Punjab* (village-level, PCA_CDB-03).
[23] Hindustan Times (Bathinda). Biomass plants in Punjab have a chequered journey. 18 Nov 2017. https://www.pressreader.com/india/hindustan-times-bathinda/20171118/282230895988653
[24] Mongabay-India. From pollution to power, what stops paddy straw from becoming the fuel of choice. Dec 2021. https://india.mongabay.com/2021/12/from-pollution-to-power-what-stops-paddy-straw-from-becoming-the-fuel-of-choice/
[25] BioEnergy Times. Four CBG plants to come up in Punjab in 2026-27, to consume 1.08 lakh tonnes of paddy residue. https://bioenergytimes.com/four-cbg-plants-to-come-up-in-punjab-in-2026-27-to-consume-1-08-lakh-tonnes-of-paddy-residue/
[26] G. Dipoppa, S. Gulzar. Bureaucrat incentives reduce crop burning and child mortality in South Asia. *Nature* 634(8036):1125–1131, 2024. doi:10.1038/s41586-024-08046-z.
[27] M. Schiavina, M. Melchiorri, M. Pesaresi. GHS-SMOD R2023A: GHS settlement layers, application of the Degree of Urbanisation methodology. European Commission JRC, 2023. (Earth Engine: JRC/GHSL/P2023A/GHS_SMOD_V2-0)
[28] APEDA. *Crop Survey for Estimation/Assessment of Acreage, Crop Health and Expected Yield of Basmati Rice during 2023*, Volume III, 2025. https://apeda.gov.in/sites/default/files/documents/2025-06/Basmati_Crop_survey_Report_3_Season_2023.pdf
[29] Department of Animal Husbandry and Dairying. *20th Livestock Census 2019*, village-level data, via ARTPARK Public Data (dataset 0041). https://publicdata.artpark.ai/en/latest/datasets/0041.html
[30] D. Naeher, V. Ziulu. Does adoption of zero tillage reduce crop residue burning? Evidence from satellite remote sensing and household survey data in India. *Applied Economics*, 2025. doi:10.1080/00036846.2025.2567582.
[31] M.V. Deshpande, D. Pillai, V.V. Krishna, M. Jain. Detecting and quantifying zero tillage technology adoption in Indian smallholder systems using Sentinel-2 multi-spectral imagery. *International Journal of Applied Earth Observation and Geoinformation* 128:103779, 2024. doi:10.1016/j.jag.2024.103779.
[32] A.A. Arbain, R. Imasu. Spatiotemporal Variation of Burnt Area Detected from High-Resolution Sentinel-2 Observation During the Post-Monsoon Fire Seasons of 2022–2024 in Punjab, India. *Sensors* 25(17):5588, 2025. doi:10.3390/s25175588.

---

## Appendix A. Farmer questionnaire (draft)

*Asked of one adult who makes farming decisions. Reference period: the most recent kharif (paddy) season. Codes in brackets.*

**Module 1 — Household and farm**
1. How many acres do you operate this year? Owned ___ Leased in ___ Leased out ___
2. How many separate plots? ___
3. Which crops did you grow in the last kharif and rabi seasons? (multi-select)
4. Does anyone in the household earn regular off-farm income? (none / job in India / remittance from abroad / business)

**Module 2 — Paddy season**
5. For each paddy plot: variety (PR-126 / PR-131 / Pusa-44 / basmati / other), transplanting date, harvest date.
6. How was the plot harvested? (combine with SMS / combine without SMS / manual)
7. Did you or a contractor own the combine? Cost per acre?

**Module 3 — Residue handling (per plot)**
8. What happened to the straw on this plot? (burnt fully / burnt partly / incorporated with Super Seeder / incorporated by ploughing / baled and sold / baled and kept / fed to animals / mulched with Happy Seeder / left standing)
9. How many days after harvest? ___
10. Main reason for this choice? (cost / time before sowing / no machine / no buyer / habit / other)
11. Did you handle straw differently three years ago? How?

**Module 4 — Machines**
12. Do you own any of: Super Seeder, Happy Seeder, mulcher, baler, MB plough, rotavator?
13. If you hired a machine: from whom (cooperative / CRM centre / private), cost per acre, days waited.
14. Did you receive any CRM subsidy or incentive? Which?

**Module 5 — Straw market**
15. Did anyone offer to buy or collect your straw? (yes / no) Who? Price per quintal or per acre?
16. Distance to the buyer or collection point (km)?
17. Who paid for baling and transport?
18. Would you sell straw at ₹___ per quintal if collected from the field? (willingness-to-accept ladder)

**Module 6 — Labour and livestock**
19. Could you hire labour at harvest when needed? Daily wage?
20. Number of cattle and buffalo owned. Do you use paddy straw as fodder? Share of your straw?
21. Does anyone in the village buy straw for fodder?

**Module 7 — Next crop and timing**
22. What did you sow after paddy? Date?
23. How many days did you feel you had between harvest and sowing? Was that enough?

**Module 8 — Norms and enforcement**
24. Out of 10 farmers in your village, how many do you think burnt straw last season? ___
25. Has any official visited, fined or recorded a "red entry" against farmers in your village? You personally?
26. Do you know the rules on straw burning and the penalties? (yes / partly / no)

**Module 9 — Barriers and preferences**
27. What one thing would most help you avoid burning? (machine on time / buyer / labour / more days before sowing / payment per acre / other)
28. Would you join a village straw-collection arrangement if one were set up? (yes / maybe / no) Why?

**Module 10 — List experiment** *(random half gets list A, the other half list B)*
29. "I will read some statements. Please tell me only **how many** are true for you, not which ones."
   - List A: (a) I grew wheat last rabi; (b) I own a tractor; (c) I sold milk last month; (d) I visited the mandi in October.
   - List B: the same four, plus (e) I burnt straw on at least one plot last season.
