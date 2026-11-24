# The whole project, end to end: a teaching guide

*For presenting and defending the final talk (25 Nov 2026). Assumes no machine learning, statistics or satellite background. Every number comes from `report/report_draft.md` and the code it cites.*

**How to read this.** Part A is the 2-minute story: learn it first. Part B teaches the background ideas from zero (satellites, Earth Engine, indices, machine learning, statistics). Part C walks through every stage: what we did, how the code does it, what came out, and **why we chose it** (the "Defend it" boxes). Part D is a one-page decision table, Part E has likely questions with answers, and Part F is a numbers cheat-sheet.

---

# Part A. The story in two minutes

1. **Problem.** Every Oct–Nov, Punjab farmers burn paddy straw to clear fields fast for wheat. The smoke is a major cause of winter pollution in north India. Subsidised machines (Happy Seeder, Super Seeder) have not stopped it.
2. **Question.** Some places burn much less than places *like them*. Which ones, and why? That is **Data-Powered Positive Deviance (DPPD)**: use data to find "positive deviants" (PDs) that do better than their peers under the same conditions, then learn from them.
3. **Unit.** Punjab's **97 tehsils** (sub-districts).
4. **Peer groups.** We grouped tehsils only on things they cannot change: rice share, rainfall, agro-ecological zone, groundwater, soil. Result: **3 groups** (Central 63, South-west 18, Foothills 15) plus 1 outlier. Stable when tested (ARI 0.89).
5. **Measuring burning.** Satellite burn indices also flag *freshly ploughed* fields as burnt (81% of ploughed fields). We built a two-stage Sentinel-2 detector with a random forest trained on ground truth and checked with daily PlanetScope images. Ploughing false alarms dropped **81% → 18%**, keeping 90% of burns.
6. **Tehsil score.** 100 fixed rice points per tehsil, every season 2020–24. Burnt share = burnt points ÷ points with a verdict. Ranks tehsils like NASA fire counts do (ρ 0.78–0.87) and is stable year to year.
7. **Positive deviants.** **Abohar** (South-west) is the only strict PD: lowest burner in its group and among the fastest reducers. A **Doaba cluster** (Dinanagar, Phagwara, Jalandhar-I, Adampur) and **Talwandi Sabo** also hold up under 6 validation checks.
8. **Why.** Desk study of 9 public drivers. Doaba's low burning is a **regional trait** (marked by urban surroundings) and not a "near a town" effect. Abohar has a local straw buyer, lots of farm labour and livestock, and an early second crop. Some popular explanations (turnaround time, farm size) mostly restate how much rice a place grows.
9. **So what.** Where field teams should look, three levers to test (straw buyer, labour, fodder), fair ranking (peers + rice share), and a pilot design with a sample size (30 villages per arm, 35 pairs per lever).
10. **Honest limits.** No fieldwork, so results are **leads, not causes**.

---

# Part B. Background ideas, from zero

## B1. The problem itself

- **Rice–wheat system.** Punjab grows paddy (rice) in the monsoon (Jun–Oct) and wheat in winter (Nov–Apr).
- **The squeeze.** Paddy is harvested in October, and wheat must be sown by about mid-November for a good yield. That leaves **2–4 weeks**.
- **Combine harvesters** cut high and leave loose straw and stubble. Clearing it costs money, machines and time. A matchstick costs nothing and clears the field in a day.
- **Why it got worse.** Punjab's groundwater law (2009) delays paddy transplanting to save water. Later transplanting means later harvest, so the window is even shorter.
- **What has been tried.** Since 2018: subsidies for crop residue management (CRM) machines, Custom Hiring Centres, fines and "red entries", short-duration varieties (PR-126). Burning has fallen but not evenly, and farmers still cite cost, machine availability and yield doubts.

## B2. Positive Deviance and DPPD

- **Positive Deviance (PD).** An old development idea: in any community, a few people facing the same constraints do much better. Their solutions are already proven to work locally, so others trust them more than outside solutions.
- **Classic PD** finds them by fieldwork. **Data-Powered PD** (Albanna et al., 2022) finds them from data (satellites, administrative records), which scales to whole states.
- **The DPPD handbook pipeline** (we follow it exactly):
  1. **Assess problem–method fit.** Is the outcome measurable? Does it vary? Could some units outperform through their own practices?
  2. **Determine positive deviants:** (a) performance measurement, (b) **homogeneous grouping**, (c) PD identification, (d) PD validation.
  3. **Discover underlying factors:** what the PDs do differently.
- **The core idea is "like with like".** A tehsil with little rice will burn little; that is not deviance. A PD must beat tehsils that have the *same* conditions. That is why grouping comes before ranking.

## B3. Satellites from zero

**What a satellite image is.** A camera in orbit takes a picture as a grid of squares (**pixels**). Each pixel stores how much light came back from that patch of ground, separately for several colours.

**Bands.** Each colour range is a **band**. Our eyes see three bands (blue, green, red). Satellites also see bands our eyes cannot:
- **Near-infrared (NIR):** healthy leaves reflect it very strongly. Good for "is it green and growing?"
- **Red-edge:** the narrow zone between red and NIR; sensitive to plant condition.
- **Short-wave infrared (SWIR):** sensitive to water in leaves and soil, and to char/ash.

**Reflectance.** The fraction of sunlight reflected, 0 to 1. Fresh ash is very dark (low in almost all bands). Green crop is low in red, high in NIR. Bare soil is moderately bright everywhere.

**Two numbers describe any satellite:**
- **Resolution:** how big a pixel is (10 m = a 10 × 10 m square).
- **Revisit:** how often it photographs the same spot.

**Satellites in this project:**

| Satellite | Pixel | Revisit | Cost | Our use |
|---|---|---|---|---|
| **Sentinel-2** (EU) | 10–20 m, 13 bands | ~5 days | Free | Main burn measure |
| **PlanetScope** (Planet Labs) | 3 m, 4 bands (B, G, R, NIR) | Daily | Paid; we had education access | "Judge" to check our detector |
| **VIIRS / MODIS** (NASA FIRMS) | 375 m–1 km, thermal | Twice a day | Free | Fire counts: comparison only |
| **Sentinel-1** (radar) | 10 m | 12 days here | Free | Tested for ploughing; rejected |

**Two important Sentinel-2 details:**
- **Clouds.** Optical satellites cannot see through clouds. Each Sentinel-2 image includes a **Scene Classification Layer (SCL)**: a label per pixel (cloud, shadow, vegetation, bare soil, water, dark area, ...). We keep pixels labelled **2 (dark area), 4 (vegetation), 5 (bare soil), 7 (unclassified)**. We had to *add* 2 and 7 because Sentinel-2 labels fresh char as "dark area" or "unclassified"; the original mask threw away 51 of 54 burnt fields (difficulty D12).
- **Fire counts vs burnt area.** VIIRS detects *heat* at the moment it passes overhead. It misses small fires and fires lit when the satellite is not overhead. Farmers have learned the pass times, so fire counts collapsed in 2024–25 even though burning did not. Sentinel-2 sees the *scar* (ash) for days after, which is harder to dodge.

## B4. Google Earth Engine (GEE) from zero

**What it is.** A Google service holding petabytes of free satellite images, plus computers to process them. You write a short script (JavaScript in the browser, or Python), and the computing happens on Google's servers. You never download whole images.

**Five concepts are enough to explain our use:**

| Concept | Meaning | In our code |
|---|---|---|
| `ImageCollection` | A stack of all images of one product | `ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")` = every Sentinel-2 surface-reflectance image |
| `filterBounds` / `filterDate` | Keep only images over our points and in our dates | Our 100 points per tehsil; 15 Sep – 30 Nov of each year |
| Metadata filter | Drop very cloudy scenes early | `CLOUDY_PIXEL_PERCENTAGE < 60` |
| `select` / `map` | Pick bands; apply a function to every image | Bands B2–B8, B11, B12 + SCL |
| `sampleRegions` | Read pixel values at given points | Value at each point on each date, at 20 m |

**What our burn script does in GEE** (`Code/burn/tehsil_metric_rf.py`):
1. Uploads the ~9,700 sample points (97 tehsils × 100).
2. For each year, filters Sentinel-2 to those points and dates.
3. For every image, reads the bands and SCL at every point → a table "point, date, band values".
4. Downloads this table (in batches, with automatic retries because long requests drop, D18).
5. Everything after that (cloud filtering, indices, the random forest) runs in **Python on the laptop**.

**Other GEE jobs in the project:** CHIRPS rainfall averaged per village (Jun–Sep, 2020–25); a cropping-intensity script (later dropped); terrain export (later dropped); urban surroundings from the JRC GHS-SMOD layer.

**If asked "why GEE?":** free, all of Sentinel-2's archive in one place, no downloading terabytes, and the same script reruns every season.

## B5. Spectral indices: turning bands into one useful number

An **index** combines bands so one number answers one question.

- **NDVI** = (NIR − Red) / (NIR + Red). High (0.6–0.9) = green crop; low (< 0.3) = bare or harvested. Used to detect **harvest** (NDVI drops) and **wheat green-up**.
- **NBR** (Normalized Burn Ratio) = (NIR − SWIR2) / (NIR + SWIR2). Classic burn index for forests. **Rejected** here: harvest itself also makes NBR drop, so harvest looks like burning (D13).
- **BAIS2** (Burned Area Index for Sentinel-2, Filipponi 2018). Built for Sentinel-2's red-edge bands:
  `BAIS2 = (1 − √(B6·B7·B8A / B4)) × ((B12 − B8A)/√(B12 + B8A) + 1)`
  Intuition: burnt surfaces lose the red-edge/NIR "vegetation glow" and gain in SWIR; BAIS2 rises on burnt ground. An early version failed because we used a simplified formula; the full red-edge formula fixed it.
- **TCB** (Tasseled Cap Brightness) = weighted sum of six bands (0.351·B2 + 0.381·B3 + 0.344·B4 + 0.720·B8 + 0.240·B11 + 0.195·B12). Simply "how bright overall". Ash is very dark → low TCB.
- **Why BAIS2 + TCB together:** BAIS2 says "burn-like spectrum", TCB says "dark". Together they separate fresh burns from unburnt crop very well. On CEEW's 380 labelled fields: **95.5% accuracy** vs 81.3% for NBR (the midterm result).

## B6. Machine learning from zero (only what we used)

**Classification.** Teaching a computer to put things into categories (here: *burnt* or *not burnt*) from measurements.
- **Features:** the measurements we give it (band values, indices, change since the previous look).
- **Labels:** the right answers for training examples (from ground truth).
- **Training:** the computer finds a rule linking features to labels.
- **Testing:** check the rule on examples it has *not* seen. Testing on training data is cheating, because the model may just memorise.

**Logistic regression** (our midterm detector). Draws one straight line (a weighted sum) through the feature space: `z = w1·BAIS2 + w2·TCB + b`. If z > 0 → burnt. Simple and transparent. This "z score" is reused in the final detector as a first filter.

**Decision tree.** A flowchart of yes/no questions learned from data: "Is BAIS2 > 0.4? If yes, did brightness fall by more than 0.05? ..." Easy to read but jumpy: small changes in data give a different tree.

**Random forest.** **500 decision trees**, each trained on a random sample of the examples and a random subset of features. Each tree votes; the share of trees voting "burnt" is the **probability**. Why it is good here:
- Handles many features and non-straight-line patterns (burnt vs ploughed is not a single line).
- Averaging many trees makes it stable and resistant to over-fitting.
- Works well with a few thousand examples; no deep learning needed.
- Our settings: 500 trees, `min_samples_leaf = 5` (each leaf needs ≥ 5 examples, to avoid memorising), `class_weight = "balanced"` (Walker has 2,204 burnt but only 223 ploughed fields; balancing stops the model ignoring the rare class).

**Probability and cut-off.** The forest outputs, e.g., 0.83. We call "burnt" if ≥ the **cut-off**. A higher cut-off means fewer false alarms but more missed burns. We chose **0.79 (0.786)**: the value that keeps 90% of Walker's true burns. 0.5 is the sensitivity check.

**Measuring a detector:**
- **Recall / "burns caught":** of truly burnt fields, what share we call burnt.
- **False-alarm rate / "ploughed called burnt":** of truly not-burnt fields, what share we wrongly call burnt.
- **Accuracy:** share of all fields called correctly (misleading when classes are unequal).
- **AUC** (area under the ROC curve): pick one burnt and one not-burnt field at random; AUC = the chance the model gives the burnt one a higher score. 0.5 = coin toss, 1.0 = perfect. It judges the *ranking*, independent of the cut-off. Final model 0.938; Planet rule 0.96; BAIS2 for char-vs-soil 0.51 (useless).

**Cross-validation (5-fold).** Split the data into 5 parts. Train on 4, test on the 5th; rotate 5 times. Every field is tested exactly once by a model that never saw it. This is how the Walker numbers are computed.

**Out-of-sample transfer.** The strongest test: train on one place/year (Walker, 2019), test on a completely different one (Jalandhar 2021) without retraining. We did this.

## B7. Statistics from zero (only what we used)

- **Median:** middle value when sorted. Robust: one extreme tehsil does not move it.
- **Quartiles:** Q1 = 25% of values below; Q3 = 75% below. **IQR** = Q3 − Q1, the spread of the middle half.
- **Tukey fence** (handbook's outlier rule): a value is unusual if it is below **Q1 − 1.5 × IQR** or above **Q3 + 1.5 × IQR**. Not tied to any assumed distribution.
- **Log scale:** turns "multiply" into "add". On a log scale, going from 0.4 to 0.2 is the same step as 0.2 to 0.1 (both halve). Used because burnt shares cannot go below 0 and the raw fence fell below 0 (no tehsil could ever be a PD).
- **Spearman ρ (rank correlation):** convert values to ranks, then measure whether the ranks rise together. +1 = same order, 0 = unrelated, −1 = opposite. Rank-based, so outliers and curved relationships do not break it. We use it because we care about **order** (who burns more), not exact levels.
- **Partial correlation:** correlation between X and Y after removing what a third variable Z explains in both. Used to ask: "does this driver still relate to burning once rice share is held constant?"
- **p-value:** the chance of a pattern this strong if there were truly no relationship. p < 0.05 is the usual "significant" bar. **Multiple testing:** run 44 tests and about 2 will pass by chance. So we only trust patterns that repeat across several readings.
- **Bootstrap:** to see how much a result depends on the particular data we have, resample the data many times (with replacement, or 80% subsets) and redo the analysis each time. If the result keeps appearing, it is robust.
- **Theil–Sen slope:** a trend line robust to outliers. Compute the slope between every pair of seasons and take the **median**. With 5 seasons, one strange year can swing an ordinary trend line; Theil–Sen resists that.
- **Power / sample size:** how many units a trial needs to reliably detect an effect of a given size (80% chance of detecting it at 5% significance is the standard).

---

# Part C. Stage by stage

## C1. Stage 1: Problem–method fit

**What.** Before doing anything, check DPPD suits this problem. The handbook asks four things:

| Question | Our answer |
|---|---|
| **Problem definition** | Paddy-straw burning in Punjab; which tehsils burn much less than structurally similar peers, and why? |
| **Suitability:** does the outcome vary among similar units, so PDs plausibly exist? | Yes. Districts with similar crops, climate and subsidy access burn very different amounts (CEEW 2025). |
| **Feasibility:** data, skills, time? | All public data: Sentinel-2 via GEE, rainfall, soil, groundwater, rice maps, census. One student, one semester. Narrowed to Punjab. |
| **Desirability:** who benefits? | NGOs and the Punjab agriculture department: a list of *nearby, real* places that already burn less is more actionable than a general model. |

**How the design changed (worth telling, shows learning):**
- Assignment 1 used **districts**, **fire counts** and a **regression**.
- Feedback changed three things: (1) fire counts undercount (~3.7× fewer than Sentinel-2) → satellite burnt area; (2) Basma Albanna (DPPD co-author) pointed out that homogeneous grouping is a *required* DPPD step → added, and it became the main work; (3) districts hide good performers inside averages → tehsils.
- **Haryana dropped** (in the original proposal) because its groundwater is category-only, the boundary crosswalk is incomplete and soil/CI sources are inconsistent. Agreed with Prof. Seth: Punjab first.

> **Defend it: why not just regression?** Regression finds what predicts burning *on average*. DPPD looks for *exceptions* that do well under the same constraints. Prof. Seth also set a rule: no PDs from regression residuals. Residuals depend on which variables you put in the model and inherit its biases; a direct comparison inside peer groups is transparent.

## C2. The unit: tehsils, and the boundary problem

**Why tehsils.** Fine enough that a good performer is not hidden in a district average (Punjab has only 23 districts, too few to rank). Coarse enough that every dataset is reliable there (rainfall, groundwater, soil are not reliable per village). 97 tehsils.

**The boundary problem (D2).** Most data use **2011 Census** villages and tehsils. Punjab has since created new districts and tehsils, many carved out of old ones.
- We built **crosswalks** (bridges) from the government's LGD directory: every 2011 village → its current tehsil.
- Result: 45 tehsils unchanged, 43 carved from one 2011 tehsil, 9 drawn from several. Only 8 of 12,808 villages unaccounted for.
- **Mixed-resolution design** (approved by Prof. Seth): keep each dataset at its native level (village, block, district), pass it *down* to villages through the crosswalk, then roll it *up* to current tehsils. Nothing is thrown away.
- Tehsil polygons: Esri India 2024 layer with LGD codes. Total area 50,371 km² vs official 50,362 km² (checks out).

## C3. Grouping variables (Stage 2b, part 1)

**The rule** (the most important rule of the project, be ready to state it):
> A grouping variable must be **structural and non-transferable**: something a tehsil cannot change by its own choices, which makes avoiding burning easier or harder.
> **Drivers** (machines, mandis, awareness) are **never** used for grouping; they are what Stage 3 must find. **Burning itself is never used** to build groups.

Why? If we grouped on machine density, tehsils with many machines would be compared only with each other, and the effect of machines would vanish from the comparison. We would hide exactly the deviance we want to find.

**The five dimensions:**

| # | Dimension | Variable | Source | Why it is structural and matters |
|---|---|---|---|---|
| 1 | **Rice** | Calibrated rice share of tehsil area, 2022 | Chen et al. 10 m paddy map, scaled to official district totals | More paddy = more straw to clear in the same short window |
| 2 | **Rainfall** | Mean monsoon (Jun–Sep) rainfall 2020–25 | CHIRPS (in GEE) | Separates the arid south-west from the wetter centre; drives irrigation and crop timing |
| 3 | **Agro-ecological zone** | Share of tehsil area in each of AESR zones 14.2, 2.5, 4.1, 9.1 | NBSS&LUP AESR 2018 map | Official climate + landform + growing-period class; separates Siwalik foothills from plains |
| 4 | **Groundwater** | Stage of extraction 2022 (% of annual recharge) | CGWB report, block level | Water-saving law delays transplanting where water is scarce → later harvest → less time |
| 5 | **Soil** | 8 categorical descriptors (particle size, drainage, texture, depth, pH, salinity, sodicity, erosion) | NBSS&LUP 1:250K soil map | Drainage and workability affect how easily wheat can be sown into residue |

**How each was built and what went wrong:**

- **Rice share.**
  - The village rice file's "2022" column turned out to be a copy of 2020 (98.6% identical) (D3). So we recomputed from Chen's 2022 GeoTIFF over current tehsil polygons.
  - Total rice hectares mostly measures *tehsil size* (D4). So we use **share** = rice area ÷ tehsil area.
  - Chen's map is **regionally biased** (D5): it over-maps rice in the south-west cotton belt and foothills (Fazilka ×1.71, Bathinda ×1.37) and under-maps central Punjab. We found this because the south-west looked more paddy-dominated than Sangrur, which agronomically is wrong. **Calibration:** scale each tehsil's Chen rice so its district total matches the official Statistical Abstract. Chen decides *where within a district* rice is; official statistics decide *how much*.
- **Rainfall.** CHIRPS daily rainfall (~5 km), summed for Jun–Sep, averaged 2020–25, read per village in GEE, averaged to tehsils. Limitation: 5-year window, not a 30-year normal.
- **Zones.** Official NARP zones exist only per district (Patiala listed in three zones; two districts missing) (D8). The finer AESR map was on the Bhoomi Geoportal but bulk download was disabled. We wrote a script that rebuilt each zone polygon from thousands of point queries until 99.99% of Punjab was covered. We use **shares**, not one label, because 21 tehsils are genuinely split between zones.
- **Groundwater.** CGWB block values → villages → tehsils. Year 2022 fixed by Prof. Seth (2025 only as sensitivity).
- **Soil.** One sample per 2011 tehsil, via point queries at centroids (bulk export disabled). Kept as **original categories** (not one-hot coding, which would count one difference several times). Several descriptors are nearly constant (96/97 "Deep"); dropping them barely changes groups (ARI 0.96), so all 8 were kept.

**Variables considered and dropped (examiners like this):**

| Variable | Why dropped |
|---|---|
| **Cropping intensity** (own Sentinel-2 NDVI season count) | Agreed poorly with official district values (ρ = 0.18), up to +44 points too high, swung 20–32 points year to year. Dropping it changed only 2 borderline tehsils (ARI 0.93), and stability *improved* (borderline 9 → 3). (D6) |
| **Terrain** (elevation, slope) | Defective slope data: different tehsils with identical slope (Dhar Kalan and Pathankot both 1.046 despite 578 m vs 296 m). Replaced by AESR zones, which capture foothill vs plain. (D7) |
| **NARP zones** | District-level only; 2 districts missing. (D8) |
| **Temperature, rainfall variability** | Not included; stated as an untested assumption. |

**Interesting check (D9):** AESR's arid zone is drawn coarsely and covers 12 wetter central tehsils. With zones alone, the south-west merged into the centre (ARI 0.41). Keeping rainfall too recovers it. Some overlap between zone and rainfall is accepted.

## C4. Grouping method (Stage 2b, part 2)

The code is in `Code/grouping/` (`gower.py → cluster.py → evaluate.py → stability.py → sensitivity.py → freeze.py`). Everything is reproducible: earlier numbers that came without code were re-derived from scratch and some were contradicted (D1).

### Step 1. How different are two tehsils? (dimension-balanced Gower distance)

**The problem.** Our variables are mixed: some are numbers in different units (mm of rain, % extraction, shares), some are categories (soil texture "Sandy" vs "Coarse-loamy"). Ordinary distance (Euclidean) cannot compare mm with soil types.

**Gower distance** turns every difference into a **0–1 score**:
- Number: |a − b| ÷ (range of that column across all tehsils). E.g. rainfall runs from about 310 to 1,281 mm (outlier excluded), a range of ~970 mm, so a 100 mm gap ≈ 0.10.
- Category: 0 if the same, 1 if different.
- Missing: that column is skipped for that pair.

**Our change: dimension balance.** Plain Gower averages all *columns*. Soil has 8 columns, rainfall 1, so soil would get 8 votes and rainfall 1. We **average within each dimension first, then average the 5 dimensions equally (1/5 each)**. Each dimension gets one vote.

**Outlier handling.** Dhar Kalan (hill tehsil, 7% rice, 1,604 mm rain) would stretch every range and squeeze everyone else's differences by ~12%. So ranges are computed without it; its own differences are capped at 1.

**Worked example (on the slide):**

| Pair | Rice | Rain | Zone | Groundwater | Soil | **Distance (average of 5)** |
|---|---|---|---|---|---|---|
| Phagwara–Adampur | 0.09 | 0.09 | 0.00 | 0.12 | 0.88 | **0.24** |
| Phagwara–Abohar | 0.42 | 0.38 | 0.50 | 0.63 | 0.62 | **0.51** |

Phagwara (65% rice, 767 mm, zone 9.1, 265% extraction) and Adampur (59%, 854 mm, 9.1, 219%) are close on everything except soil. Abohar (37%, 395 mm, 2.5, 32%) is far on everything. So Phagwara–Abohar is about twice as far.

> **Defend it: why equal weights?** No evidence says one condition matters more for burning. Equal weights are the neutral default in composite indicators. Rather than assume they are right, we **tested** them: each weight ×0.85 and ×1.15 (Step 5).

### Step 2. Build groups by merging (average-linkage hierarchical clustering)

**The algorithm in plain words:**
1. Start: each tehsil is its own group (97 groups).
2. Find the two groups that are closest and merge them.
3. The distance between two groups = the **average** of all tehsil-to-tehsil distances between them ("average linkage").
4. Repeat until everything is one group.
5. The record of merges is a tree (**dendrogram**). Cutting the tree at a height gives 2, 3, 4, ... groups.

**Toy example with 6 real tehsils** (real distances from `outputs/grouping/dist_baseline.csv`, same as slide 8):

|  | Phagwara | Jalandhar-I | Adampur | Lehra | Abohar | Fazilka |
|---|---|---|---|---|---|---|
| Phagwara | – | 0.22 | 0.24 | 0.27 | 0.51 | 0.40 |
| Jalandhar-I | | – | 0.29 | 0.31 | 0.43 | 0.45 |
| Adampur | | | – | 0.38 | 0.44 | 0.50 |
| Lehra | | | | – | 0.34 | 0.36 |
| Abohar | | | | | – | 0.17 |

1. Smallest distance: **Abohar + Fazilka (0.17)** → merge.
2. Next: **Phagwara + Jalandhar-I (0.22)** → merge.
3. Adampur to {Phagwara, Jalandhar-I} = average(0.24, 0.29) = **0.265** → Adampur joins.
4. Lehra to {Phagwara, Jalandhar-I, Adampur} = average(0.27, 0.31, 0.38) = **0.32** → Lehra joins.
5. Finally {Abohar, Fazilka} joins the rest at **0.43**.

Cut the tree at about 0.4 and you get two groups: a central/Doaba one and a south-west one. Exactly the real grouping.

> **Defend it: why hierarchical clustering and not k-means?**
> - k-means needs averages of numeric columns; it cannot work on a custom distance with categories. Hierarchical clustering works directly on any distance table.
> - It does not force round, equal-sized groups.
> - The tree shows how groups relate (South-west and Central merge before Foothills joins).
> - Prof. Seth endorsed it.
>
> **Why average linkage?** "Single" linkage (closest pair) chains groups together through in-between tehsils; "complete" (farthest pair) is driven by one extreme pair. Average is the balanced middle.

### Step 3. How many groups? (silhouette)

For each tehsil: **a** = average distance to its own group; **b** = average distance to the nearest *other* group.
**Silhouette s = (b − a) / max(a, b).** +1 = clearly placed, 0 = on the border, < 0 = closer to another group. Average over all tehsils.

Rule: ignore cuts that create groups with < 5 tehsils (a peer group needs enough members to compare against). Then read silhouette together with group sizes and whether groups make agronomic sense.
- **k = 3: silhouette 0.377.** k = 2 (Plains 81 / Foothills 15): 0.409.
- k = 4 and 5 give the same three groups (the extra pieces have < 5 tehsils).
- k = 6 splits Central and stability falls (ARI 0.71).

> **Defend it: why 3 and not 2, when 2 scores higher?** With 2 groups, Bathinda (arid, 467 mm, cotton belt) would be judged against Ludhiana (wet, paddy-dominated). The South-west is real: it shows up in rainfall, zones and groundwater together. So we keep 3, but require every PD to hold under the 2-group version too (it nests exactly: Central + South-west = Plains).

### Step 4. Can we trust it? (bootstrap stability, ARI)

**Idea.** If the groups are real, they should reappear when we redo the clustering on slightly different data.
- Draw a random **80%** of tehsils, recluster, compare with the full grouping. Repeat **300 times** (seed 42, so reproducible).
- Comparison measure: **Adjusted Rand Index (ARI)**. Take every pair of tehsils and ask: are they together in both groupings, or apart in both? ARI is the agreement, corrected so chance agreement scores 0. 1 = identical.
- **Result: mean ARI 0.890.** Group survival: Central 100%, Foothills 100%, South-west 93.7%.
- **Switch rate** per tehsil: how often it lands in a different group. > 20% = **borderline**. Only 3: Firozpur, Faridkot (South-west/Central border), Dinanagar (Central/Foothills).
- **Consensus assignment:** each tehsil's final group is the one it lands in most often across the 300 resamples. A single tree cut had put 5 border tehsils in the South-west although they sat with Central in most resamples (D17).

### Step 5. Does it depend on my choices? (one-factor-at-a-time sensitivity)

Change one design choice at a time; compare with the frozen grouping by ARI:
- Each dimension's weight ×0.85 and ×1.15; each dimension dropped; soil without near-constant descriptors.
- **10 of 12 weight changes keep ARI ≥ 0.83**, moving at most 5 tehsils.
- **Weak point:** the South-west/Central boundary. +15% weight on rice or soil, or dropping any dimension, merges South-west back into Central (ARI 0.48–0.60).
- The Foothills/Plains split survives **every** test.
- Interpretation: South-west shades gradually into Central across Malwa; it is a gradient, not a wall. Hence the "must hold under 2 groups too" rule.

### Step 6. Freeze

Frozen when: groups ≥ 5 tehsils; mean ARI ≥ 0.8; groups make agronomic sense; weak points documented. Frozen as v4 on 7 Oct 2026 (`outputs/grouping/FROZEN_config.json`, with the input file's SHA-256 hash so anyone can check the exact data used).

### Result

| Group | Tehsils | Median rice | Median monsoon rain | Median GW extraction | Character |
|---|---|---|---|---|---|
| **Central** | 63 | 75% | 721 mm | 230% | Paddy-dominated plains, most over-exploited groundwater |
| **South-west** | 18 | 59% | 467 mm | 118% | Dry cotton–paddy belt |
| **Foothills** | 15 | 28% | 981 mm | 117% | Wet, hilly Kandi belt |
| Outlier | 1 (Dhar Kalan) | 7% | 1,604 mm | 27% | Hill tehsil, set aside |

**The best evidence that it is real:** the method was never told where any tehsil is, yet the groups form **three geographically connected regions** matching Punjab's known belts (central plains, Malwa south-west, Kandi/Siwalik foothills).

> **Defend it: why was grouping done *before* measuring burning?** So the groups could not be shaped, even unconsciously, by knowing who burns.

## C5. Measuring burning: the detector (Stage 2a, part 1)

This was the hardest part of the project. Tell it as a story.

### Chapter 1: the midterm detector worked... on one day

- Ground truth: **CEEW** labelled 438 field polygons as burnt/unburnt from very-high-resolution imagery on 10 Nov 2020 and 29 Oct 2021.
- Logistic regression on BAIS2 + TCB: **95.5% accuracy, 98.1% recall** (5-fold cross-validation), vs 81.3% for NBR.
- Fix along the way: the cloud mask (SCL) was throwing away burnt pixels; widened to SCL 2/4/5/7 → 436/438 fields kept (D12).

### Chapter 2: over a whole season, almost everything looked burnt

- Running the detector on every clear look from Sep to Nov: **94.6% of 279 random cropland points** flagged as burnt in 2022, and **92% of fields CEEW saw unburnt**. Impossible.
- Cause: **freshly ploughed soil looks like ash** to Sentinel-2. Directly comparing char and soil on CEEW fields: BAIS2 AUC 0.51 (a coin toss).
- Confirmed on **Walker et al.'s** field ground truth (2019; 2,204 burnt and 223 ploughed-not-burnt fields): the old detector flagged 98% of burnt **and 81% of ploughed** fields.
- **Why this matters for DPPD:** a tehsil that ploughs straw *in* instead of burning (exactly the good behaviour we want to find) would look like a heavy burner. False alarms on ploughing would hide the PDs.

### Chapter 3: tried and failed (one line each)

| Attempt | Why it failed |
|---|---|
| Tighter season window | Burning and ploughing happen in the same weeks |
| Heat (Landsat land-surface temperature, MODIS) | Still called about half of ploughed fields burnt |
| Sentinel-1 radar roughness (Basma's suggestion) | 12-day revisit too slow; moved the wrong way on probably-ploughed fields; dropped 33% of real burns |
| Other published thresholds (CEEW's, Naeher & Ziulu's) | None separated char from soil |
| Hand-labelling 10 m image chips | Not possible by eye (one clear smoke event in 60 points) (D15) |

### Chapter 4: the key insight, time

Daily **PlanetScope** images showed it: fresh ash is **near-black for only 2–3 days**, then fades toward the colour of ploughed soil. Sentinel-2 comes every ~5 days, often cloudy, so it usually sees the *faded* ash.
- On Walker's ground-truth fields, a simple Planet rule (brightness drops sharply vs the previous 15 days) separates burnt from ploughed with **AUC 0.96**.
- So: (1) Planet can act as an **independent judge**; (2) the Sentinel-2 detector should look at the **change** around the event, not just the state.

### Chapter 5: the final two-stage detector

For each field/point and season:
1. **Flag.** Score every clear Sentinel-2 look with the old BAIS2 + TCB logistic model (z). z > 0 = possible event (burnt *or* ploughed).
2. **Candidate.** Among flagged looks, pick the one with the **largest rise in z** over the previous clear look. Reason: burning is *sudden*; drying and harvest are gradual.
3. **Before.** The last clear look within 20 days before the candidate.
4. **Features.** At the candidate look: bands B2–B8, B11, B12 and indices NDVI, NBR, NBR2, BAIS2, TCB. Plus the **change** (candidate − before) for each.
5. **Check.** A **random forest** (500 trees, balanced) trained on Walker's ground truth (burnt vs ploughed-not-burnt) gives a probability.
6. **Cut-off 0.79:** burnt if ≥ 0.79. Chosen to keep 90% of Walker's burns. 0.5 = sensitivity.

Point = "unknown" if it has no clear look in the window or no look before the candidate. Unknowns are left out.

**Results.**

| On Walker 2019 (5-fold CV) | Burns caught | Ploughed called burnt |
|---|---|---|
| Old BAIS2 + TCB | 98% | **81%** |
| Daily Planet rule | 90% | 9% |
| Sentinel-2 trained on Planet labels | 89% | 22% |
| **Final model, cut-off 0.79** | **90%** | **18%** |
| Final model, cut-off 0.5 | 97.5% | 51% |

**Independent check: Jalandhar 2021**, a new year and district, model **not retrained**, two judges:
- Planet judge: not-burnt fields called burnt **23/32 (old) → 3/32 (cut 0.5) → 0/32 (cut 0.8)**. Ranking AUC 0.94 vs 0.89.
- CEEW field visit: unburnt called burnt 28/95 → 2/95.
- **Cost:** missed burns, mostly **partially** burnt fields (field averages dilute partial burns). At 0.5, 56/72 fully burnt fields caught, but only 89/190 partially burnt.
- Bonus: Sentinel-2 trained on noisy Planet labels is almost as good as on ground truth (22% vs 16% false alarms) → Planet could label new regions where no field survey exists.

> **Defend it: why accept missing burns to cut false alarms?** For DPPD what matters is *ranking* tehsils. An under-count that is similar everywhere does not change the order much. A ploughing false alarm, though, specifically penalises the tehsils that manage straw well, which hides PDs. (Assumption stated: that the under-count is similar across tehsils, untested.)
>
> **Why train on Walker and not our own labels?** Walker is the only public field ground truth of *ploughed-not-burnt* fields in Punjab. CEEW's labels have burnt vs standing stubble, not ploughing.
>
> **Why not use Planet everywhere?** Quota: education access charges ≥ 100 km² per scene however small the clip; 3,000 km²/month. Punjab is 50,000 km² every day for 2.5 months. Sentinel-2 is free and covers everything; Planet is the judge.

## C6. From fields to tehsils: the burn measure (Stage 2a, part 2)

**Sample points.**
- **100 random 20 m rice pixels per tehsil** (9,700 total). A pixel qualifies only if Chen's map calls it rice in **both 2020 and 2022** (removes stray pixels).
- The **same points** are read every season → year-to-year change is real change, not a different sample.
- Each point is read as a **single pixel** (in Jalandhar tests a single pixel beat 3×3 and 5×5 windows, because fields are small).
- Earlier plan was all cropland (to avoid Chen's bias). Changed because Chen's bias is mostly about *how much* rice (fixed by calibration), not *where*. Residual risk (cotton points in the south-west) is checked in validation V4/V4b.

**Season window.** 15 Sep – 30 Nov, the ISRO protocol used by CAQM (the official air-quality commission).

**Tehsil value.** Burnt share = burnt points ÷ points with a verdict. Nearly every point gets a verdict (≥ 70 of 100 in any tehsil-season).

**Seasons.** PD analysis on **2020–2024**. Every rule is also rerun on **2020–2023** because 2024 behaves oddly (72% of burns first seen in late November; agreement with VIIRS drops to 0.51). 2019 is only used for checks.

**Does the measure make sense?**
- **Same order as VIIRS fire counts:** ρ 0.78–0.87 (2019–23). The old heat-peak measure agreed at only 0.10–0.27.
- **Stable year to year:** ρ 0.82–0.91 between consecutive seasons.
- **District order vs official CREAMS figures:** 0.75 (2019), 0.50 (2020), 0.87 (2022).
- **Cut-off 0.79 vs 0.5 give the same order** (ρ 0.84–0.98): the cut-off changes the level, not the ranking.
- Weak spots: the 2019 level is far above CREAMS (CREAMS changed method); 2024 odd.

**Which tehsils are ranked.** Central 63 + South-west 18 = **81**. Foothills (15) are measured but **not ranked**: little rice, so ash-vs-soil confusion is worst relative to real burning, and the ranking check against district figures failed (only 4 districts). Dhar Kalan has no peers.

**Spread:** Central median burnt share 0.62 (0.25–0.81); South-west 0.73 (0.34–0.90). Punjab burns over half its paddy fields (52–64% across 2020–24).

## C7. PD identification (Stage 2c)

Code: `Code/pd/pd_identify.py`, `pd_robust.py`.

**Two kinds of deviance**, always against the tehsil's **own group**:
- **Static:** burns the least.
- **Temporal:** reduced burning the fastest over 2020–24 (Basma's suggestion). Comparing a tehsil with its own past cancels fixed unmeasured differences (soil, farm size, local enforcement).
- **Negative deviants (NDs)** are the mirror image; they are the contrast for Stage 3.
- **No regression residuals** (Prof. Seth's rule): every rule is a direct within-group comparison.

**Why log scale.** On the raw scale, the handbook's lower fence (Q1 − 1.5 × IQR) falls below zero (Central: −5.76 in a dry run), so no tehsil could ever be a PD. On **log(value + c)**, with c = 10% of the group median (c avoids log of 0), halving counts the same at any level, and trends become **% change per year**.

**Rules:**
- **Static PD:** log 5-season mean below the group's lower fence, **and** in the group's lowest quarter in at least 4 of 5 seasons (stops one lucky season making a PD).
- **Temporal PD:** Theil–Sen slope of log burning, minus the group's median slope; PD if below the lower fence of these deviations. Reported as "% per year faster than the group".
- **Candidate PD:** in the bottom 10% of the group, but not beyond the fence ("among the lowest", not "far from normal").
- **NDs:** mirror (above upper fence / top quarter / top 10%).

**Robustness.** Each rule is run on 2020–24 and 2020–23.
- **Strict rule (headline):** beyond the fence in **both** runs.
- **Old rule:** PD or candidate in both runs (broader "low-burning" set).

**Results.**

| Tehsil | Group | Kind | Strict | Burnt share | Trend vs group |
|---|---|---|---|---|---|
| **Abohar** | SW | static + temporal | **PD** (static); borderline (temporal) | 0.34 | −11.1%/yr |
| Dinanagar | C | static | borderline | 0.21 | +6.5%/yr |
| Phagwara, Adampur, Jalandhar-I | C | static | – | 0.30–0.31 | |
| Gurdaspur, Banga | C | static | – | 0.29–0.34 | |
| Talwandi Sabo | SW | static | – | 0.50 | +14.5%/yr |
| Samana, Dirba | C | temporal | (Samana borderline) | 0.63–0.71 | −9.1 / −8.2 |
| *NDs:* Lehra, Zira, Moonak (C), Guruharsahai (SW) | | static | | 0.79–0.90 | |

Fences: Central 0.225 vs median 0.61; South-west 0.454 vs median 0.73.

**How to explain it:**
- **Abohar is the only strict PD:** lowest in the South-west, beyond the fence in both runs, and among the fastest reducers. The only tehsil good on both kinds.
- **The Doaba cluster burns about half the Central median.** But they sit *together*, so the fence treats them as part of normal spread: they are a **low-burning region**, not isolated outliers. 6 of 8 static PDs were also flagged using VIIRS fire counts, so the list does not depend on one sensor.
- **Static and temporal barely overlap.** Dinanagar burns least but its burning is *rising*.

## C8. PD validation (Stage 2d)

The handbook asks: before fieldwork, check each PD is a real signal, not noise or a data artefact. We had no fieldwork, so all checks are on data, **with thresholds fixed in advance** (`Code/pd/pd_validate.py`).

| Check | Question | How | Rule |
|---|---|---|---|
| **V1 Sampling bootstrap** | Luck of which 100 points? | Resample each tehsil-season's verdicts 1,000 times; rerun both runs | Kept ≥ 80% = pass; 50–80% flag; < 50% fail |
| **V2 Settings** | Depends on my choices? | Cut 0.5; offset c 5% and 20%; alternative grouping (rain weight ×0.85) | Kept in all but one = pass |
| **V3 Clear looks** | Do clouds hide fires? | Unknown share and looks per point vs group | > 2× group median = flag |
| **V4 Rice** | Just less paddy? | Calibrated rice share; share of points with a paddy harvest seen | Below group Q1 = flag |
| **V4b Harvest-confirmed** | Do non-paddy points pull the score down? | Recompute using only points where a paddy harvest was seen | Flag lost = flag |
| **V5 Timing** | Harvest so late burns fall outside window? | Median harvest date vs group | ≥ 10 days later = flag |
| **V6 Triangulation** | Do other sources agree? | VIIRS flags; CREAMS district rank | Information only |

**Label:** any fail → dropped; ≤ 1 flag → validated PD; more → PD with caveat.

**Results:**
- **Validated PDs:** Abohar (static and temporal), Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo.
- **With caveat:** Gurdaspur (clouds), Banga (bootstrap 0.72, harvest check).
- **Dropped:** Samana (0.40) and Dirba (0.39): temporal flags kept in only ~4 of 10 resamples. All temporal NDs fail too. **A 5-season trend from 100 points is too noisy** to name a deviant on its own. (Side finding: the fastest-falling Central tehsils lie where two Sentinel-2 tiles overlap and get twice as many looks; look density may bias the trend.)
- **Rice is the main warning.** Every static PD except Talwandi Sabo has less rice than 3/4 of its group (V4 flag), and within groups burning rises with rice share (ρ 0.70 Central, 0.63 South-west). **But V4b shows the PDs still burn little on fields that really grew paddy** (Abohar 0.43 → 0.45 vs group 0.73; Dinanagar 0.22 → 0.25 vs 0.62). So it is not non-paddy points dragging the score down.
- **No timing artefact (V5).**
- **Not done:** V7 blind visual check of 120 points (tool built, not labelled); V8 asking local experts (no human contact in this project).

## C9. Stage 3: why do the PDs burn less?

**Approach.** A **desk study on public online data** (handbook allows this when fieldwork is not possible). Aim: *candidate* explanations for a field study, not proof of cause.

**Drivers vs conditions.** A driver is something that can be changed or transferred (a rotation, a straw market, labour). Structural conditions already went into grouping and are never reused.

**The nine drivers:**

| # | Driver | Why it might lower burning | How measured |
|---|---|---|---|
| D1 | Harvest-to-wheat turnaround | More days to manage straw | Sentinel-2 NDVI: harvest = drop below 0.30 after ≥ 0.45; green-up ≥ 0.30; sowing = green-up − 28 days (checked against CIMMYT farmer dates) |
| D2 | Early second crop (potato, vegetables, fodder) | Sown in October, so straw must be cleared other ways | NDVI ≥ 0.6 by 30 Nov (wheat cannot reach full canopy that early) |
| D3 | Farm labour; small farms | Manual handling; affordability | Census 2011 labourers per cultivator; cultivators per 100 ha rice |
| D4 | Straw buyers | Burning = lost sale | 14 biomass/CBG plants from news; plants within 30 km, distance to nearest |
| D5 | Distance to state border | Smoke drifting to another state is less policed (Dipoppa & Gulzar, *Nature* 2024) | District polygons |
| D6 | Urban surroundings | Smoke is noticed; off-farm work; vegetable markets | JRC GHS-SMOD 2020 (in GEE): urban area share; km to urban centre |
| D7 | Basmati share | Basmati straw fed to cattle | APEDA 2023 ÷ official rice area (district) |
| D8 | CRM machines / hiring centres | Clear straw without fire | **Dropped:** no district table online |
| D9 | Livestock | Straw as fodder | Livestock Census 2019, village level |

**Three ways of comparing, all inside groups:**
1. **Profiles:** each PD/ND's percentile in its group; count how many PDs are on the "expected" side of the median and NDs on the other.
2. **Spearman ρ** between driver and burning across the group.
3. **Partial ρ with rice share held constant.** Because burning rises with rice share inside groups, any driver that just tracks "less paddy" would look important. Removing rice share exposes that. (This is analysis, not PD identification, so the no-regression rule does not apply.)

**Honesty about numbers:** 8 PDs, 4 NDs, 44 tests → ~2 false positives at p < 0.05 expected by chance. So only patterns that repeat across all three readings count.

**Findings:**
1. **Urban surroundings mark the Doaba belt, as a region, not a town effect.**
   - 7/8 PDs above group median urban share, all 4 NDs below. Central ρ −0.61; still −0.30 with rice held constant.
   - **Field-level test:** within a tehsil, do fields near towns burn less? Only within 2 km (6–8 points less), and only 4% of fields are that close. Beyond 2 km, distance doesn't matter.
   - Scored using only fields **> 5 km from any town**, the PDs still burn as little (Dinanagar 0.21 → 0.20, Phagwara 0.30 → 0.27, Jalandhar-I 0.31 → 0.32, Adampur unchanged).
   - So urban share is a **marker of the Doaba region** and what comes with it (potato/vegetable rotations, off-farm and overseas income, dense markets). Not "towns reduce burning". The sign even reverses in the South-west.
2. **Abohar: a single-case profile.** Rural, but: a biomass power plant in the tehsil (a local straw buyer); the most farm labourers per cultivator in Punjab (1.61); the most cattle and buffalo per cultivator in its group; the highest early-second-crop share in its group; a basmati-heavy district (57%). Each is a plausible lever; with one tehsil they cannot be separated → a **lead for fieldwork**.
3. **Apparent drivers that are really rice share.** Turnaround (ρ −0.38) and small farms (−0.28 / −0.49) lose their link once rice share is held constant.
4. **Border runs the "wrong" way in the South-west** (near the border = *less* burning, ρ +0.83). Likely the cotton belt along the Rajasthan border, where paddy is newer and less dominant: a regional pattern, not a border effect.
5. **No consistent link:** straw buyers within 30 km, labour per cultivator overall, basmati, livestock. Weak tests because data are coarse or dated.

## C10. Impact assessment (proposal)

**What it adds.** DPPD stops at candidate explanations. We propose how a partner would confirm and test them.

**Theory of change:** PD leads → **Phase 1** confirm in field (1 season) → **Phase 2** pilot levers in matched non-PD villages (1–2 seasons) → measure with satellite + survey → scale if it works.

**Assumptions and where tested:** practices are real (Phase 1 visits to satellite points); transferable (Phase 1 interviews, Phase 2); farmers adopt (take-up); adoption lowers burning, not just moves it (satellite outcome incl. neighbouring villages).

**Phase 1 (field validation).** Abohar + 4 Doaba PDs, 4 NDs, 2 typical tehsils per group. ~6 villages per tehsil across the burning range. Farmer survey (~20 per village), focus groups, key informants (agriculture officer, plant buyer, hiring centres, sarpanch), and **geotagged photos of our satellite points** (burnt/ploughed/baled/stubble), which gives the field-located ploughing check we lacked.

**Phase 2 (pilot).** Levers from Abohar: (A) assured straw buyer, (B) paid labour, (C) fodder linkage.
- Unit = **village**. Frame = villages in **non-PD tehsils of the same peer group** (this is what DPPD adds: comparable treated and control).
- **Pair** villages on baseline burnt share and rice share, randomly treat one of each pair. If randomisation impossible: stepped-wedge (random order of rollout).
- Spillovers: controls at least one village away; neighbours tracked.
- Analysis: **ANCOVA** (compare end-of-pilot burning between arms, adjusting for each village's own baseline).

**Outcomes.** Primary: **village burnt share from our Sentinel-2 detector** (covers every field, no interviews, cannot be talked around, 5-season baseline exists). Secondary: survey with a **list experiment** (burning is illegal, so people under-report; half get 4 harmless statements, half get the same + "I burnt straw"; each says only *how many* are true; the difference in averages estimates the share burning without anyone admitting it).

**Sample size** (`Code/impact/sample_size.py`). From our data (South-west frame, 1,633 villages): 2023 burning 65%; tehsils differ by SD 0.11; field burning correlates 0.36 year to year. Two unknowns set as ranges (village spread 1–3× tehsil spread; village year-to-year steadiness 0.5–0.9). Middle case: **30 villages per arm** for a 10-point drop with ≥ 30 points per village → round up to **35 pairs (70 villages) per lever**. Without the baseline it would be 49; for a 5-point drop, 114.

**Ethics.** IRB approval; consent in Punjabi; burning answers never stored with names or plot coordinates; satellite outcomes only at village level or above (never used for enforcement on individuals); pilot only *adds* options, never withholds a scheme.

---

# Part D. Decision table (one page to defend everything)

| Decision | Alternatives | Why this one | If pushed, say |
|---|---|---|---|
| DPPD, not regression | Regression on drivers | Finds feasible local exceptions; Prof's no-residuals rule | Regression explains averages; we want outliers under the same constraints |
| Tehsil unit | District, village | Districts too few (23) and hide PDs; village data unreliable | 97 units, all data reliable at that level |
| Punjab only | + Haryana | Haryana data incomplete | Pipeline is configurable; Haryana is future work |
| Grouping before measuring | Measure first | Groups cannot be shaped by knowing who burns | Prevents unconscious bias |
| Only structural variables | Include machines, mandis | Drivers in grouping hide the deviance | Drivers are what Stage 3 discovers |
| Rice **share**, calibrated | Rice hectares; raw Chen | Hectares = tehsil size; Chen biased by region | Official district totals, Chen's spatial pattern |
| Drop cropping intensity, terrain | Keep them | Failed validation / defective; dropping barely changes groups | Tested, not assumed: ARI 0.93 |
| Dimension-balanced Gower | Euclidean; plain Gower | Mixed data; soil's 8 columns would get 8 votes | Each dimension one vote |
| Equal weights | Expert weights | No evidence for any ranking | ±15% tested: 10/12 keep ARI ≥ 0.83 |
| Average-linkage hierarchical | k-means, single/complete linkage | Works on custom distance; no shape assumption; tree; Prof endorsed | k-means can't use categories |
| k = 3 | k = 2 (higher silhouette) | Don't judge arid Bathinda against wet Ludhiana | PDs must also hold under k = 2 |
| Consensus over 300 bootstraps | One tree cut | Border tehsils misassigned by one cut | ARI 0.89 |
| BAIS2 + TCB base | NBR | NBR confuses harvest with burning | 95.5% vs 81.3% |
| Two-stage RF detector | Single index; radar; heat | Only approach that separates burnt from ploughed | 81% → 18% false alarms |
| Cut-off 0.79 | 0.5 | Ploughing false alarms hide PDs; ranking stable either way | ρ 0.84–0.98 between cut-offs |
| Planet as judge, not measure | Planet everywhere | Quota | Sentinel-2 scales, Planet checks |
| 100 fixed rice points | All cropland; new points yearly | Same points → true change; rice in 2 years removes strays | V1 bootstrap shows 100 is enough for static ranking |
| Log scale + IQR fence | Raw scale; z-scores | Raw fence < 0; handbook rule; no distribution assumption | Halving counts the same at any level |
| Strict rule = both 2020–24 and 2020–23 | One run | 2024 doubtful | Results never rest on 2024 alone |
| Foothills not ranked | Rank all 96 | Ash/soil confusion worst; ranking check failed | Measured, reported, not ranked |
| Desk study for Stage 3 | Fieldwork | Academic scope: no human contact | Leads, not causes; Phase 1 tests them |
| Partial ρ on rice share | Plain ρ | Rice share confounds drivers | Exposes turnaround and farm size as rice proxies |

---

# Part E. Questions you may get (with answers)

**Method and DPPD**

1. *What makes this DPPD and not just ranking?* Comparing only within homogeneous peer groups, defining deviance by a fixed statistical rule, validating before interpreting, then studying what PDs do differently.
2. *Isn't a low burner just a place with less rice?* That's why rice share is a grouping variable. Inside groups burning still rises with rice, so we flag it (V4) and recheck on harvest-confirmed paddy fields only (V4b). PDs still burn little on real paddy.
3. *Why no regression residuals?* Residuals depend on which variables enter the model and inherit their bias. Prof. Seth's rule; direct comparison is transparent.
4. *Why only one strict PD?* The fence is strict by design ("far from normal"). The Doaba tehsils are low but clustered, so they form the low tail of the group, not outliers. We report both honestly.

**Grouping**

5. *Why these five variables?* They are conditions a tehsil cannot change, each with a clear link to how hard it is to avoid burning, each from a published source.
6. *Why not machines or mandi access?* They are drivers; grouping on them would hide their effect.
7. *How do you know the groups are not arbitrary?* Silhouette 0.377, bootstrap ARI 0.89, weights ±15% mostly harmless, and the groups form three connected regions on the map though location was never an input.
8. *What is ARI?* Agreement between two groupings, counted over all pairs of tehsils, corrected for chance. 1 = identical, 0 = chance.
9. *Is silhouette 0.377 good?* Moderate. Typical for real-world data with gradients. We don't rely on it alone: stability and interpretability back it up.
10. *Your South-west group is sensitive. Doesn't that undermine it?* It is a gradient, not a wall. That's why PDs must also hold under the 2-group version.
11. *Why is Dhar Kalan an outlier?* Hill tehsil, 7% rice, 1,604 mm rain. Nothing similar; it cannot be benchmarked.

**Satellites and the detector**

12. *Why not use NASA fire counts?* They undercount ~3.7×, miss small fires and fires timed to avoid the pass; they collapsed in 2024–25. We use them only as a cross-check.
13. *What is the ploughing problem in one sentence?* After 2–3 days, ash looks like freshly ploughed soil to Sentinel-2, so ploughed fields get called burnt.
14. *Why does it matter?* Tehsils that plough straw in (good behaviour) would look like heavy burners, hiding exactly the PDs we want.
15. *What does the random forest learn?* From Walker's fields, how a real burn differs from ploughing in the *change* between the look before and the event look: burns are sudden and darker in specific bands.
16. *Why should a model trained on 2019 work in 2021 elsewhere?* We tested exactly that in Jalandhar 2021 without retraining: false alarms fell from 23/32 to 0–3/32.
17. *You miss burns. Doesn't that bias rankings?* It lowers the level, not the order (ρ 0.84–0.98 across cut-offs). It is a stated assumption that the under-count is similar across tehsils.
18. *Why 100 points and not every field?* Computing cost through GEE and enough precision for static ranking (V1 bootstrap ≥ 0.89 for all but one PD). Not enough for trends, which we say.
19. *How do you handle clouds?* SCL mask keeps clear pixels only; V3 checks whether PDs have unusually many unknown points. None do except a Gurdaspur flag.
20. *What is GEE doing vs your laptop?* GEE filters and reads pixel values at our points; the laptop computes indices, the forest, and all statistics.

**PDs and validation**

21. *Why a log scale?* The raw lower fence was below zero, so no PD was possible; on log scale halving counts equally at any level.
22. *Why Theil–Sen?* With 5 seasons, one odd year swings an ordinary trend line; median of pairwise slopes resists it.
23. *Why did temporal PDs fail?* With 100 points and 5 seasons, trends are noisy: Samana and Dirba keep their flag in only ~40% of resamples. Abohar's holds (0.92).
24. *Why is 2024 treated separately?* 72% of burns first seen in late November and weaker agreement with VIIRS, suggesting late harvest or ploughing counted. Every result is shown without it.
25. *What validation would you add with more time?* The blind visual check (V7) and field visits to the satellite points.

**Stage 3 and impact**

26. *Isn't "urban" a structural condition?* It is not used to group; it is a marker. We show it is regional, not proximity: PDs burn just as little on fields > 5 km from towns.
27. *Can you claim Abohar's straw plant causes low burning?* No. One tehsil, several co-occurring features; it is a lead for fieldwork.
28. *Why is CRM machine data missing?* Not available by district online, only state totals. Stated limitation; RTI is the route.
29. *With 44 tests, aren't some findings chance?* About 2 would pass by chance. We only lean on patterns that repeat across profiles, ρ and partial ρ.
30. *Why is the satellite measure the primary pilot outcome?* Covers every field, needs no interviews, can't be talked around, and a 5-season baseline already exists.
31. *How did you get 30 villages per arm?* Normal-approximation power calculation (80% power, 5% significance) for a 10-point drop, using the spread and year-to-year correlation from our own 2019–24 data, with two village-level unknowns set as ranges; middle case.
32. *What is a list experiment?* A way to estimate the share of people doing something sensitive without anyone admitting it: compare average counts of "true" statements between two lists differing by one sensitive item.

**Big picture**

33. *What is the main contribution?* A fully coded DPPD pipeline from public data: stable peer groups, a ploughing-resistant burn measure, validated PDs, and leads plus a pilot design.
34. *What would you do differently?* Start with the ploughing problem early (it cost the most time); secure field ground truth; get CRM machine data by RTI.
35. *Is any of this causal?* No. The PDs are validated on data; the explanations are hypotheses for Phase 1.

---

# Part F. Numbers cheat-sheet

| Item | Number |
|---|---|
| Tehsils | 97 (Central 63, South-west 18, Foothills 15, outlier 1); 81 ranked |
| Villages | 12,808 (Census 2011) |
| Silhouette (k = 3) | 0.377 (k = 2: 0.409) |
| Bootstrap ARI | 0.890 (300 × 80%, seed 42); k = 2: 0.981 |
| Borderline tehsils | 3 (Firozpur, Faridkot, Dinanagar) |
| Sensitivity | 10/12 weight changes ARI ≥ 0.83 |
| Midterm detector | 95.5% accuracy, 98.1% recall vs NBR 81.3% |
| Season-long problem | 94.6% of random cropland points flagged; 81% of ploughed fields |
| Final detector (Walker) | 90% burns caught, 18% ploughed false alarms, AUC 0.938, cut-off 0.79 |
| Planet rule | AUC 0.96 |
| Jalandhar 2021 | not-burnt called burnt 23/32 → 0–3/32 |
| Points | 100 per tehsil, 20 m, rice in Chen 2020 & 2022 |
| Window | 15 Sep – 30 Nov; PD seasons 2020–24 (+2020–23) |
| Agreement with VIIRS | ρ 0.78–0.87 (2024: 0.51) |
| Year-to-year stability | ρ 0.82–0.91 |
| Central / SW median burnt share | 0.62 / 0.73 |
| Fences | Central 0.225; SW 0.454 |
| Abohar | 0.34 burnt share, −11.1%/yr vs group, bootstrap 0.92 |
| Rice vs burning within group | ρ 0.70 Central, 0.63 SW |
| Urban share vs burning (Central) | ρ −0.61; partial −0.30 |
| Sample size | 30 villages/arm; 35 pairs/lever; 1,633-village frame |

---

# Part G. Limitations to state before anyone asks

- No fieldwork or expert contact: PDs validated on data only; drivers are leads, not causes.
- Ploughing tested only on Walker (2019, two districts, 223 ploughed fields); Jalandhar check is small and does not test ploughing.
- Partial burns about half missed; under-count assumed similar across tehsils.
- 100 points per tehsil: fine for static ranking, too noisy for trends.
- 2024 doubtful; Foothills not ranked.
- Rice map corrected only at district level; burning still rises with rice share inside groups.
- Grouping: one rice year, 5-year rainfall, soil one sample per 2011 tehsil, equal weights a choice.
- Stage 3: 8 PDs, 4 NDs, mixed data years, no CRM machine data.

**One-line close:** *"We built a reproducible pipeline that finds tehsils burning far less than their true peers, fixed the main reason satellites mismeasure burning, and turned what we found into concrete levers and a pilot a partner can run, with every result labelled as a lead to be confirmed in the field."*
