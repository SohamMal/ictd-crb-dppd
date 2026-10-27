# Homogeneous grouping — clustering the 97 tehsils
**DPPD position:** Stage 2 › Homogeneous Grouping · **Status:** **Active**: rebuild reproducibly in code · **Last updated:** 2026-10-06

## In plain words
DPPD only works if we compare like with like. So before looking at burning, we sort the 97 tehsils into groups that share the same fixed conditions: crops per year, how paddy-dominated they are, climate/terrain, water stress and soil. Then a "positive deviant" is a tehsil that burns much less than *its own group*, not less than Punjab overall.

How the sorting works:
1. Measure how different every pair of tehsils is (a "distance"), giving each of the dimensions equal say.
2. Repeatedly merge the most similar tehsils into bigger and bigger clusters, which draws a tree (dendrogram).
3. Cut the tree at the level that gives clear, stable, reasonably sized groups.

A first attempt (with ChatGPT, 3 Oct) gave 3 groups (25 / 14 / 57) plus one odd tehsil (Dhar Kalan). There was no code behind those numbers, so we must rebuild them in code before trusting them.

## Technical summary
- **Hard rules [C]:** only structural, non-transferable variables. Never hypothesised drivers (CRM machines, mandi access). **Never burn outcomes.** Do not add or drop variables without Soham's confirmation.
- **Dimensions (baseline, 6) [P]:**

| Dimension | Variable(s) | Transform |
|---|---|---|
| Cropping intensity | `CI_3yr_pooled` | none |
| Rice | `rice_share_2022` *(was `rice_area_log1p` until 2026-10-06)* | none |
| Rainfall | `mean_monsoon_rainfall_mm` | none |
| Terrain | `elevation_mean`, `slope_mean` | log1p |
| Groundwater | `mean_extraction_pct_2022` | none |
| Soil | 8 categorical descriptors | categorical |

  Planned replacement [C, 2026-10-06]: rainfall + terrain → agro-climatic zone dimension once tehsil-level data is found, giving 5 or 6 dimensions.
- **Distance [P]:** dimension-balanced Gower. Numeric = |xᵢ − xⱼ| / range; categorical = 0/1 mismatch. Average within each dimension (terrain = mean of 2, soil = mean of its descriptors), then a weighted mean across dimensions with equal weights 1/D. Equal weights still need a written justification [P].
- **Clustering [C: hierarchical endorsed by Prof.]:** average-linkage HAC on the precomputed 97×97 matrix; cuts k = 2…8.
- **Evaluation plan [P]:** silhouette per k (precomputed metric); bootstrap 80% subsamples × 300, ARI vs full-data labels + per-tehsil co-assignment stability; one-factor-at-a-time sensitivity (no logs; groundwater 2025; each weight ±15%; drop each dimension; soil without near-constant descriptors); group profile table; map.
- **Freeze criteria [P]:** silhouette, bootstrap stability, minimum group size (~≥10 so within-group PD stats make sense), interpretability. Target freeze **Sat 10 Oct 2026** → `outputs/grouping/FROZEN_groups.csv`.
- **Code location [P]:** `Code/grouping/` (`config.py` with a configurable dimension list, `gower.py`, `cluster.py`, `stability.py`).

## Log (append-only, chronological)
### 3 Oct 2026 — Provisional grouping from ChatGPT session (reconstructed; **not citable until reproduced**)
**Plain:** A first try produced three groups and one outlier. The method was sensible, but there was no code, so the numbers are unverified.
**Technical:** Dhar Kalan (Pathankot) a singleton at every k → contextual outlier. Without it: 25/14/55/2; the 2-tehsil branch (Adampur, Jalandhar-II) merged into the 55 group → **G1 = 25, G2 = 14, G3 = 57**. Reported silhouette 0.287; bootstrap (80%, 300) mean ARI 0.572, G1 least stable; sensitivity ARI ≈ 0.05–1.00 (no logs / GW 2025 / ±15% weights changed groups a lot). Inputs then used `rice_area_log1p` and possibly one-hot soil [?]. [P]

### 3 Oct 2026 — Decision: rebuild in code (reconstructed)
**Plain:** We decided every number must come from code we can rerun.
**Technical:** First task for Claude Code. [C]

### 2026-10-06 — Supervisor feedback on grouping
**Plain:** The professor endorsed this clustering method, fixed groundwater to 2022, and asked to use zones instead of rainfall + terrain. Equal weighting still needs a justification.
**Technical:** [C] HAC endorsed; GW 2022; zones replace rainfall + terrain. [P] Equal weights: Soham researches a justification (e.g. composite-indicator literature), else asks Prof. [C] Soil as original categoricals (not one-hot). Build with a configurable dimension list; run the current six as the baseline first.

### 2026-10-06 — Rice input changed to rice share
**Plain:** The rice dimension now uses rice share instead of rice hectares, so the ChatGPT result is no longer directly comparable on rice anyway.
**Technical:** [C] `rice_share_2022` (raw; Gower range-normalises). See `task_rice_area.md`.

### 2026-10-06 — Steps 1–3 built: dimension-balanced Gower distance
**Plain:** We turned "how similar are two tehsils" into one score from 0 (identical) to 1 (as different as Punjab gets) for every pair. The code matches the hand-worked examples, and each tehsil's nearest neighbours make geographic sense even though location was never given to the method. Dhar Kalan is far from everyone, which supports treating it as an outlier.
**Technical:**
- Code: `Code/grouping/config.py` (configurable `DIMENSIONS`, `WEIGHTS=None` → equal, `RANGE_EXCLUDE=[]`), `Code/grouping/gower.py` → `outputs/grouping/dist_baseline.csv` (97×97, labelled by tehsil name). Input `Data/punjab_homogeneous_grouping_master_transformed.csv`.
- Rules: numeric |a−b|/range (range over all 97); categorical 0/1; missing → column skipped for that pair (`nanmean`); mean within dimension; equal-weight mean across 6 dimensions. Asserts: zero diagonal, symmetric, values in [0,1].
- Missing: Amloh `dominant_drainage` NaN → its soil distance averages 7 descriptors (e.g. Amloh–Ajnala soil 0.571 = 4/7).
- Checks vs hand calculation: Ajnala–Amritsar-I 0.050 (CI .004, rice .036, rain .033, terrain .039, GW .188, soil 0); Ajnala–Talwandi Sabo 0.156 (.021, .230, .243, .098, .221, .125). [C]
- Pairwise distances: min 0.013, median 0.198, max 0.780. Nearest: Ajnala → Lopoke .028, Majitha .037, Amritsar-I .050; Talwandi Sabo → Sardulgarh .039, Maur .048, Budhlada .061.
- Mean distance to others: most typical Tarn Taran / Lopoke .155, Ajnala .156; most atypical Dhar Kalan **0.594**, then Anandpur Sahib .372, Pathankot .347, Rup Nagar .334, Balachaur .329. Dhar Kalan's nearest neighbour is Pathankot (0.288).
- Dhar Kalan sets the min or max of 4/6 numeric variables (rain, elevation, slope max; CI, rice min). Excluding it from range computation raises the median pair distance among the other 96 from 0.195 to 0.221 (~12% ruler compression). [P] Not adopted; decide with Step 4.
- Env: scipy not installed; needed for Step 4 (HAC).

### 2026-10-06 — Dhar Kalan excluded from the range ("ruler"), option (a)
**Plain:** Dhar Kalan stays in the clustering, but we no longer let its extreme values set the full spread of each variable. Otherwise everyone else's differences look ~12% smaller than they are.
**Technical:** [C] Soham chose option (a). `config.RANGE_EXCLUDE = ["Dhar Kalan"]`; its per-column differences are capped at 1. `dist_baseline.csv` regenerated with this setting.

### 2026-10-06 — Step 4 built: average-linkage HAC, first tree
**Plain:** The method merged the most similar tehsils step by step into a family tree. Without being told any locations, it recovered Punjab's known farming regions: the foothill (Kandi) belt, the dry south-west cotton–paddy belt, and the large central plain. Dhar Kalan is far from everything. A small Jalandhar cluster also splits off early because its groundwater stress is extreme.
**Technical:**
- Code: `Code/grouping/cluster.py` (SciPy 1.18.1 `linkage(method="average")` on `squareform(dist)`; `fcluster(maxclust)` for k = 2..8; labels renumbered 1 = largest). Outputs `outputs/grouping/{dendrogram_baseline.png, labels_by_k.csv, sizes_by_k.csv}`. Env: scipy 1.18.1, scikit-learn 1.9.1, matplotlib 3.11.2 installed (no Smart App Control block).
- Sizes: k2 96/1 · k3 80/16/1 · k4 77/16/3/1 · k5 77/16/2/1/1 · **k6 62/16/15/2/1/1** · k7 62/15/13/3/2/1/1 · k8 59/15/13/3/3/2/1/1.
- Merge heights: Dhar Kalan joins last at ≈0.67; foothill group joins the rest at ≈0.36; Jalandhar trio (Jalandhar-I, Jalandhar-II, Adampur) at ≈0.29; south-west joins central at ≈0.24.
- k6 profiles (medians: CI, rice share, rain mm, elev m, GW % 2022):
  - G1 central plains (62): 204.8, 0.65, 708, 237, 227. Ludhiana, Sangrur, Amritsar, Patiala, Fatehgarh Sahib, Gurdaspur …
  - G2 foothills / Kandi (16): 194.3, 0.35, 996, 294, 104. Dinanagar, Gurdaspur, Dasua, Garhshankar, Hoshiarpur, Mukerian, Tanda, Pathankot, Anandpur Sahib, Nangal, Rup Nagar, Dera Bassi, Kharar, SAS Nagar, Balachaur, Nawanshahr.
  - G3 south-west (15): 202.1, 0.73, 458, 200, 99. Bathinda, Maur, Talwandi Sabo, Faridkot, Jaitu, Kotkapura, Abohar, Fazilka, Jalalabad, Guruharsahai, Budhlada, Sardulgarh, Gidderbaha, Malout, Sri Muktsar Sahib.
  - Adampur + Jalandhar-II (2); Jalandhar-I (1; GW 392.5%, the top of the range); Dhar Kalan (1).
- Jalandhar check: Jalandhar-I's villages fall mostly in the "Jalandhar East" groundwater block (72/79 villages; 400% in 2022), a real rural block value, not an urban artefact. Jalandhar-II mostly "Jalandhar West" (243%); Adampur in Adampur/Bhogpur (213/203%).
- Comparison with ChatGPT (3 Oct): the same Adampur + Jalandhar-II 2-tehsil branch and the same Dhar Kalan singleton reappear; group sizes differ (inputs changed: rice share instead of rice ha, categorical soil, range excl. Dhar Kalan). 25/14/57 is not reproduced as such. [C]
- Open [P]: which k; how to treat the Jalandhar trio (tiny groups can't host PD comparison). Next: Step 5 (silhouette per k).

### 2026-10-06 — Step 5 built: silhouette per cut
**Plain:** For each possible number of groups we scored how clearly each tehsil sits in its own group (1 = clearly, 0 = on the border, below 0 = closer to another group). Fewer groups always score higher, because one huge group plus one outlier is trivially "clear". So the score has to be read together with group size and with whether the groups mean anything. The Jalandhar trio fits comfortably inside the central plains once merged, which supports merging them.
**Technical:**
- Code: `Code/grouping/evaluate.py` (`sklearn.metrics.silhouette_samples(metric="precomputed")`; singleton s = 0). Outputs `outputs/grouping/{silhouette_by_k.csv, silhouette_per_tehsil.csv}`.
- Env: scikit-learn 1.9.1 blocked by Windows Smart App Control (`_datasets_pair` DLL) → pinned **scikit-learn 1.7.2** (loads).
- Results (mean silhouette · # negative · # groups ≥10): k2 96/1 0.611 · 2 · 1 | **k3 80/16/1 0.437 · 1 · 2** | k4 77/16/3/1 0.337 · 5 · 2 | k5 77/16/2/1/1 0.293 · 8 · 2 | **k6 62/16/15/2/1/1 0.274 · 6 · 3** | k7 0.222 · 13 · 3 | k8 0.207 · 15 · 3.
- k3 per group: central+SW (80) 0.446, foothills (16) 0.422; only Nawanshahr negative (−0.075).
- k6 per group: central 0.213, foothills 0.313, south-west 0.484, Adampur+Jalandhar-II 0.557. Negatives: Mansa −0.358, Firozpur −0.173, Nawanshahr −0.157, Mehal Kalan −0.077, Shahkot −0.026, Kapurthala −0.009 (borderline tehsils).
- What-if [P]: k6 with Jalandhar-I, Jalandhar-II, Adampur merged into central → **65/16/15/1, silhouette 0.319**, 7 negative; the trio's own s = 0.235 / 0.228 / 0.102 (all positive, so they fit the central group).
- Silhouette 0.287 reported by ChatGPT is not comparable (different inputs and cut).
- Open [P]: choose between k3 (80/16 + Dhar Kalan) and "3 regions" (65/16/15 + Dhar Kalan). Step 6 stability should decide.

### 2026-10-06 — Step 6 built: bootstrap stability (ARI)
**Plain:** We hid a random 20% of tehsils 300 times, regrouped each time, and checked whether the same tehsils stayed together. Both candidates are very stable (ARI ≥ 0.8). The simple 2-group split (plains vs foothills) is the most stable. The 3-region split (central / foothills / south-west) is only a little less stable and keeps the dry south-west separate. Two tehsils, Nawanshahr and Gurdaspur, keep switching between foothills and plains under any choice.
**Technical:**
- Explained ARI to Soham first (pair counting, chance adjustment, worked 5-tehsil example: Rand 0.6 → ARI 0.17).
- Code: `Code/grouping/stability.py`. Config additions: `OUTLIERS=["Dhar Kalan"]` (set aside before cutting; as a last-joining singleton it changes no other merge), `MIN_GROUP_SIZE=5` (members of smaller groups moved to the large group with the lowest average distance; this generalises the Jalandhar-trio merge), `BOOTSTRAP_RUNS=300`, `BOOTSTRAP_FRACTION=0.8` (77 of 96), `SEED=42`. The whole procedure (Gower with ranges re-measured on the subsample → HAC → cut k → small-group merge) is rerun on each subsample; ARI vs full-data labels on the same tehsils; per-tehsil Jaccard overlap of group-mates. Runtime ≈13 s.
- Outputs: `outputs/grouping/{stability_by_k.csv, stability_per_tehsil.csv, labels_final_rule.csv}`.
- Results on 96 tehsils (sizes · silhouette · ARI mean [p5–p95]):
  - k2 80/16 · 0.444 · **0.901** [0.810–1.0] ← candidate A
  - k3 80/16 · 0.444 · 0.854 [0.537–1.0]
  - k4 80/16 · 0.444 · 0.753 [0.407–1.0]
  - k5 **65/16/15** · 0.324 · **0.811** [0.407–1.0] ← candidate B
  - k6 66/15/15 · 0.329 · 0.780 [0.347–1.0]
  - k7 66/15/15 · 0.329 · 0.688 [0.297–1.0]
  - (k3–k4 collapse to 80/16 and k6–k7 to 66/15/15 after the small-group merge.)
- Candidate B membership: central 65 (incl. Jalandhar-I, Jalandhar-II, Adampur via the merge rule); foothills 16 (Dinanagar, Gurdaspur, Dasua, Garhshankar, Hoshiarpur, Mukerian, Tanda, Pathankot, Anandpur Sahib, Nangal, Rup Nagar, Dera Bassi, Kharar, SAS Nagar, Balachaur, Nawanshahr); south-west 15 (Bathinda, Maur, Talwandi Sabo, Faridkot, Jaitu, Kotkapura, Abohar, Fazilka, Jalalabad, Guruharsahai, Budhlada, Sardulgarh, Gidderbaha, Malout, Sri Muktsar Sahib).
- Per-tehsil mate-overlap: B central 0.899, foothills 0.761, south-west 0.797; ≥0.8 for 92% of tehsils (A: 98%). Least stable in both: **Nawanshahr** (A 0.193 / B 0.161), **Gurdaspur** (0.326 / 0.302). Under B the whole south-west group sits at ~0.8, i.e. in some subsamples it merges with central as a block (B's p5 = 0.407).
- vs ChatGPT reported ARI 0.572: the code-based grouping is markedly more stable (different inputs). [C]
- [P] Lean: B (ARI 0.81 is still "very stable", and it separates the south-west). Pending: one-factor-at-a-time sensitivity, then freeze.

### 2026-10-06 — Candidate B chosen; minimum group size 5 confirmed
**Plain:** We'll use three regional peer groups (central plains, foothills, south-west), with Dhar Kalan set aside as an outlier.
**Technical:** [C] Soham: B (k5 → 65/16/15 + Dhar Kalan outlier), `MIN_GROUP_SIZE = 5`. Not yet frozen (pending sensitivity + borderline inspection).

### 2026-10-06 — Sensitivity (one factor at a time) on candidate B
**Plain:** We changed one design choice at a time and checked how much the three groups move. Nudging any weight by ±15%, removing the log, or swapping to 2025 groundwater barely matters: at most 5 border tehsils move, and usually only Gurdaspur and Nawanshahr. Equal weights are therefore not a fragile choice. Removing rice, rainfall or groundwater makes the south-west group vanish into the centre, so those three dimensions together are what define the south-west. Removing soil also reshapes the groups. Removing cropping intensity or terrain changes almost nothing.
**Technical:**
- Code: `Code/grouping/sensitivity.py` → `outputs/grouping/sensitivity_table.csv`. Same procedure as stability (`group_tehsils`, k = 5, Dhar Kalan aside, small-group merge); ARI vs baseline; moved tehsils after matching each new group to its best-overlapping baseline group.
- Results (sizes · ARI · moved):
  - GW 2025: 64/18/14 · 0.832 · Firozpur, Gurdaspur, Mansa, Dharamkot, Nawanshahr
  - No log on terrain: 67/15/14 · 0.931 · Gurdaspur, Nawanshahr
  - Weights ±15% (12 runs): 6 runs identical (ARI 1.000), 6 runs 0.931 with only Gurdaspur + Nawanshahr moving
  - Drop CI: 0.931 (Gurdaspur, Nawanshahr) · Drop terrain: 66/15/15 · 0.897 (+Adampur)
  - **Drop rice: 75/21 · 0.437** · **Drop rainfall: 82/14 · 0.487** · **Drop groundwater: 74/15/7 · 0.339**. In each, the south-west group dissolves (moves en bloc).
  - Drop soil: 55/20/14/7 · 0.615 (7 moved: Mehal Kalan, Firozpur, Zira, Gurdaspur, Mansa, Dharamkot, Nawanshahr)
  - Soil without depth/salinity/erosion: 68/15/13 · 0.897 (Gurdaspur, Dera Bassi, Nawanshahr)
- Implications:
  - (1) Equal weights are defensible on robustness grounds: ±15% gives ARI ≥ 0.93. This contradicts the ChatGPT claim that ±15% moved groups noticeably.
  - (2) CI and terrain add little beyond the other dimensions (CI sd only 9.3 pts; terrain overlaps with rainfall). Relevant to the zones-replace-rainfall+terrain plan: rainfall is load-bearing for the south-west split, so any zone dimension must still separate the dry south-west.
  - (3) Near-constant soil descriptors: dropping them moves 3 tehsils (ARI 0.897). [P] Soham to decide.
  - (4) Gurdaspur and Nawanshahr are the only systematically borderline tehsils.
- Untested assumption (temperature, rainfall variability) not checked: no temporal-variability data in hand; stays a stated limitation.

### 2026-10-06 — Near-constant soil descriptors kept
**Plain:** Dropping depth, salinity and erosion would move only 3 border tehsils, so we keep all 8 soil properties.
**Technical:** [C] Soham: keep all 8 soil descriptors (sensitivity ARI 0.897 if dropped).

### 2026-10-06 — Step 7: borderline tehsils inspected; slope data defect found
**Plain:** Gurdaspur really is a foothills tehsil: wet (1,083 mm), lower groundwater stress, fewer crops per year. It is on average clearly closer to the foothills than to the plains, although its single closest neighbours are plains tehsils (Batala, Kalanaur). Nawanshahr is genuinely in-between: on average it is closer to the central plains, and it sits with the foothills mainly because of its slope value. That slope data looks broken: several tehsils share exactly the same slope with zero variation between their villages, even where elevation differs a lot. So the grouping is not frozen yet.
**Technical:**
- Group medians (CI, rice share, rain, elev, slope, GW22): central 204.9, 0.65, 715, 236, 0.11, 229 · foothills 194.3, 0.35, 996, 294, 0.41, 104 · SW 202.1, 0.73, 458, 200, 0.02, 99.
- Gurdaspur: CI 194.8, rice 0.53, rain 1,083, elev 254, slope 0.42, GW 134.7, Fine-loamy. Avg distance → foothills 0.193 vs central 0.249 (rain .126 vs .370; GW .102 vs .265; CI .078 vs .219). Nearest: Batala .074, Kalanaur .089, Banga .105 (central), Nawanshahr .112, Dinanagar .119 (foothills). **Foothills, robust.**
- Nawanshahr: CI 204.5, rice 0.56, rain 822, elev 254, slope 0.80, GW 138.2, Fine-loamy. Avg distance → central **0.209** vs foothills 0.243; terrain is the only dimension pulling it to foothills (terrain .409 to central vs .298). Nearest: Banga .082, Kalanaur .103, Batala .109 (all central). **Transitional**; in foothills only through the tree structure (average linkage joined it with Gurdaspur early).
- **Slope defect:** `slope_mean` identical for Dhar Kalan and Pathankot (1.046) and for Nangal and Anandpur Sahib (0.963), each with `slope_interVillage_stdDev = 0.000`, while elevation differs (578 vs 296 m). Village file shows within-village `slope_stdDev = 0.0` (e.g. Darbahn). Likely slope computed at a coarse scale (coarse DEM / large `reduceRegions` scale). The "slope range 0–1 too low for Shivalik" anomaly from the handoff is probably the same issue. [P] Source script not in repo.
- Test, terrain = elevation only: 59/22/15, ARI vs B 0.803, silhouette 0.334 (vs 0.324). Moves Batala, Kalanaur, Rajpura, Chamkaur Sahib, Morinda, Banga (central → foothills). Gurdaspur foothills (s 0.341). Nawanshahr still borderline (s −0.081; central .171 vs foothills .186).
- Decision pending [?]: how to handle slope before freezing (recompute / elevation-only / drop terrain / keep and flag).

### 2026-10-06 — Dimension set revised: zones replace terrain (decided, not yet run)
**Plain:** The grouping will use official agro-ecological zones instead of terrain, because the slope data is broken and the zones capture foothills vs plains from a published source. Rainfall stays, because without it the dry south-west group disappears.
**Technical:**
- [C] New dimensions (6, equal weights): CI_3yr_pooled · rice_share_2022 · mean_monsoon_rainfall_mm · **zone (AESR 2018 shares 14.2 / 2.5 / 4.1 / 9.1)** · mean_extraction_pct_2022 · soil (8 categorical). Terrain removed.
- Exploratory run of this set (k5): 66/16/14, ARI 0.897 vs B, silhouette 0.315; moved Gurdaspur, Mansa, Nawanshahr. Full reasoning in `task_agroclimatic_zones.md` and `task_terrain.md`.
- The grouping-B results above (stability, sensitivity, Step 7) were computed with terrain and must be rerun with the new set before freezing.

### 2026-10-06 — Full rerun with zone dimension: the 3-region split is softer than it looked
**Plain:** With zones in place of terrain, the same three regions still appear (central 66, south-west 16, foothills 14). But the border between central plains and south-west is now less stable: small changes (2025 groundwater, a bit more weight on soil) make the south-west merge back into the centre. The foothills-vs-plains split stays rock solid in every version. Comparing four designs shows this is not a zone problem. The south-west/central border is a gradual change across Malwa, not a sharp line. The old terrain version looked more stable only with help from the broken slope data. Not frozen; decision needed.
**Technical:**
- Config: `zone` dimension (4 AESR share columns) replaces terrain. `sensitivity.py`: `K_CHOSEN = 4`; "no_log_terrain" scenario replaced by "terrain_instead_of_zone (pre-2026-10-06 design)".
- Tree (97, incl. Dhar Kalan): k2 82/15 · k3 82/14/1 · k4 79/14/3/1 · k5 63/16/14/3/1 · k6 63/16/14/2/1/1. Silhouette k2 0.413, k3 0.378, k5 0.282.
- Stability (96, small-group merge): k2 82/14 sil 0.392 ARI **0.948** · k3 81/15 0.909 · **k4 66/16/14 sil 0.316 ARI 0.772** [p5 0.362] · k5 66/16/14 0.704 · k6 57/16/14/9 0.645.
- k4 groups: central 66 (mate overlap 0.833; now includes Gurdaspur, Nawanshahr); **south-west 16** (0.743): Bathinda, Maur, Talwandi Sabo, Faridkot, Jaitu, Kotkapura, Abohar, Fazilka, Jalalabad, Guruharsahai, Budhlada, **Mansa**, Sardulgarh, Gidderbaha, Malout, Sri Muktsar Sahib; **foothills 14** (0.922): Dinanagar, Dasua, Garhshankar, Hoshiarpur, Mukerian, Tanda, Pathankot, Anandpur Sahib, Nangal, Rup Nagar, Dera Bassi, Kharar, SAS Nagar, Balachaur. Tehsils with overlap ≥0.8: 68% (was 92%). Least stable: Bagha Purana .571, Dirba .597, Sunam .600, Moonak .612, Patran .621, Firozpur .650, Rampura Phul .675, Nihal Singhwala .681, Lehra .681, Adampur .711 (all on the Malwa central/SW gradient).
- Sensitivity (k4, ARI vs 66/16/14): weights ±15% → 1.000 in 9/12, CI×0.85 0.931, **GW×0.85 0.634**, **soil×1.15 0.501** (SW dissolves). **GW 2025 0.501** (SW dissolves). Terrain instead of zone 0.475. Drop CI 0.931; drop rice 0.623; drop rainfall 0.449; drop zone 0.501; drop GW 0.449; drop soil 0.600; soil w/o near-constant 0.931.
- Design comparison (`Code/grouping/compare_designs.py`, 300 bootstraps each):

| Design | 2 groups (ARI) | 3 regions (sizes, ARI) |
|---|---|---|
| Zone (current) | 82/14, 0.948 | 66/16/14, 0.772 |
| Terrain elev+slope (old, slope defective) | 80/16, 0.901 | 65/16/15, 0.811 |
| Elevation only | 74/22, 0.676 | 59/22/15, 0.630 |
| Zone + elevation | 84/12, 0.968 | 67/17/12, 0.756 |

- Reading: foothills vs plains is robust under every design (ARI 0.90–0.97, except elevation-only). The central/SW split sits at 0.63–0.81 under every design, so it is a real but gradual boundary.
- Decision needed [?]: (1) freeze 3 regions (zone design, k4) and flag the Malwa-gradient tehsils as borderline, with PD results checked against the 2-group alternative; (2) freeze 2 groups (82/14); (3) revert to the terrain design (rejected: depends on defective slope).

### 2026-10-06 — GROUPING FROZEN: 2 peer groups (Plains 82 / Foothills 14) + Dhar Kalan outlier
**Plain:** We froze the simplest grouping that is clearly real: the Siwalik foothill belt (14 tehsils) and the plains (82), with Dhar Kalan kept aside as a one-off hill tehsil. It is the most stable option (tehsils stay with the same group-mates 95% of the time). The south-west vs central difference is real but gradual, so drawing a hard line through Malwa would make the groups depend on small choices. The cost is that the plains group is broad: a south-western tehsil like Bathinda is compared with central tehsils like Ludhiana. We will keep this in mind when identifying positive deviants.
**Technical:**
- [C] Soham chose option 2 (2 groups) over 3 regions (ARI 0.772, fragile to GW year and soil weight) and over the old terrain design (defective slope).
- Dimensions (6, equal weights): CI_3yr_pooled · rice_share_2022 · mean_monsoon_rainfall_mm · zone (AESR 2018 shares 14.2/2.5/4.1/9.1) · mean_extraction_pct_2022 · soil (8 categorical). Gower with range excluding Dhar Kalan; average-linkage HAC; k = 2; Dhar Kalan set aside; `MIN_GROUP_SIZE = 5`.
- Quality: silhouette 0.392; bootstrap ARI **0.948** [p5 0.802, p95 1.00]; mean mate-overlap Plains 0.983, Foothills 0.913. Borderline (overlap < 0.8): **Tanda** only (0.757); next lowest Dinanagar 0.834.
- Foothills (14): Anandpur Sahib, Balachaur, Dasua, Dera Bassi, Dinanagar, Garhshankar, Hoshiarpur, Kharar, Mukerian, Nangal, Pathankot, Rup Nagar, SAS Nagar (Mohali), Tanda.
- Group medians (CI · rice share · rain mm · AESR 14.2 share · GW 2022 % · elev m): Foothills 194.2 · 0.350 · 996 · 0.957 · 88 · 296 | Plains 204.1 · 0.657 · 676 · 0.000 · 206 · 232 | Dhar Kalan 179.8 · 0.070 · 1,604 · 1.0 · 27 · 578.
- Code: `Code/grouping/freeze.py` → `outputs/grouping/FROZEN_groups.csv` (`lgd_tehsil_code, lgd_tehsil_name, lgd_district_name, group, outlier, borderline, bootstrap_mate_overlap`), `FROZEN_group_profiles.csv`, `FROZEN_config.json` (dimensions, settings, SHA-256 of the transformed master).
- vs ChatGPT 3 Oct (25/14/57 + Dhar Kalan): not reproduced; superseded by this code-based result.
- Implications for PD identification [P]: (1) the plains group spans the Malwa rainfall/rice gradient, so check whether candidate PDs cluster at one end of it (e.g. compare within-plains results against rainfall / AESR 2.5 share), and report the 3-region version (66/16/14) as a robustness check; (2) the foothills group is small (14), so PD statistics there are thin; (3) Dhar Kalan is reported contextually, not ranked.

### 2026-10-06 — CORRECTION: previous entry (2-group freeze) SUPERSEDED. Frozen grouping = 3 regions
**Plain:** Soham meant option 1 (three regions), not option 2. The freeze is redone with three peer groups: central plains (66), south-west (16), foothills (14), plus Dhar Kalan kept aside. The south-west gets its own peers, so Bathinda is no longer compared with Ludhiana. Because the central/south-west border is a gradual change across Malwa, every candidate positive deviant will also be checked under the simpler 2-group version (plains/foothills) and trusted only if it holds in both. The two versions nest neatly: central + south-west = plains exactly.
**Technical:**
- [C] Soham: "my mistake i meant to say 3 groups". The 2-group freeze above is superseded (kept here for the record).
- `Code/grouping/freeze.py`: `K_FROZEN = 4` (3 groups after the small-group merge), `K_ALTERNATIVE = 2`. Groups named by zone shares (highest AESR 14.2 = Foothills; highest AESR 2.5 among the rest = South-west; remaining = Central). New column `group_2way`. Outputs overwritten: `outputs/grouping/FROZEN_groups.csv` (`lgd_tehsil_code, lgd_tehsil_name, lgd_district_name, group, group_2way, outlier, borderline, bootstrap_mate_overlap`), `FROZEN_group_profiles.csv`, `FROZEN_config.json`.
- Quality (k4 on 96): silhouette 0.316; bootstrap ARI 0.772 [p5 0.362]; mean mate-overlap Central 0.833, South-west 0.743, Foothills 0.922. Nesting: Central (66) + South-west (16) = Plains (82) of the 2-way cut; Foothills (14) identical in both.
- Members. South-west (16): Abohar, Bathinda, Budhlada, Faridkot, Fazilka, Gidderbaha, Guruharsahai, Jaitu, Jalalabad, Kotkapura, Malout, Mansa, Maur, Sardulgarh, Sri Muktsar Sahib, Talwandi Sabo. Foothills (14): Anandpur Sahib, Balachaur, Dasua, Dera Bassi, Dinanagar, Garhshankar, Hoshiarpur, Kharar, Mukerian, Nangal, Pathankot, Rup Nagar, SAS Nagar (Mohali), Tanda. Central (66): all others except Dhar Kalan.
- Medians (CI · rice share · rain mm · AESR 14.2 · AESR 2.5 · GW22 % · elev m): Central 204.8 · 0.642 · 721 · 0 · 0 · 227 · 239 | South-west 202.1 · 0.724 · 461 · 0 · 1.0 · 105 · 204 | Foothills 194.2 · 0.350 · 996 · 0.957 · 0 · 88 · 296.
- Borderline flag (overlap < 0.8): 31 tehsils = all 16 South-west (0.715–0.766, because the whole group sometimes merges with Central as a block) + 14 Central on the Malwa gradient (Bagha Purana .571, Dirba .597, Sunam .600, Moonak .612, Patran .621, Firozpur .650, Rampura Phul .675, Lehra .681, Nihal Singhwala .681, Adampur .711, Tapa .725, Gurdaspur .751, Barnala .761, Sangrur .794) + Tanda (Foothills .785). [P] This flag mixes "my whole group merged" with "I personally switch groups"; a per-tehsil switching measure would be more precise.
- Rule for PD identification [C]: a PD must hold under both `group` (3 regions) and `group_2way` (2 groups).

### 2026-10-07 — New borderline measure: group survival + tehsil switching rate
**Plain:** The old "borderline" flag counted a tehsil as unstable even when it never moved and only its whole group had merged. Now we measure two things separately: how often each group survives as its own group, and, when a tehsil's group survives, how often the tehsil itself ends up elsewhere. Only tehsils that personally switch are flagged.
**Technical:** Soham asked whether it was worth it; answer: not essential (the dual-grouping PD rule already covers the central/SW border), but cheap and it makes the report honest, so added. `stability.py`: each subsample group is named after the full-data group most of its members belong to (`match_to_full`); group survival = share of runs where a full-data group appears; `k*_switch` = share of runs, among those where the tehsil's own group survived, in which it was matched to a different group. New output `outputs/grouping/group_survival_by_k.csv`; `stability_per_tehsil.csv` gains `k*_switch` columns. `freeze.py`: borderline = `switch_rate >= 0.2` (switches in ≥1 of 5 runs).

### 2026-10-07 — Rerun with calibrated rice; GROUPING RE-FROZEN (v2): Central 58 / South-west 22 / Foothills 16 + Dhar Kalan
**Plain:** With the corrected rice numbers the three regions remain, but the south-west grows to 22: it now also takes in Barnala, Tapa, Rampura Phul, Lehra, Sangrur and Firozpur, and two Rupnagar-area tehsils (Chamkaur Sahib, Morinda) join the foothills. All three groups survive in at least 92% of reshuffles. Only 9 tehsils personally switch groups often; five of them (Sangrur, Barnala, Tapa, Lehra, Firozpur) switch more often than not, so they sit right on the central/south-west border. The south-west split still depends on weighting: giving cropping intensity or soil 15% more weight merges the south-west back into central.
**Technical:**
- Previous freeze (v1, uncalibrated Chen) archived at `outputs/grouping_frozen_v1_chen_uncalibrated/`.
- Tree (97): k2 80/17 · k3 80/16/1 · k4 78/16/2/1 · k5 56/22/16/2/1. Stability (96): k2 80/16 sil 0.396 ARI **0.946** · k3 80/16 0.741 · **k4 58/22/16 sil 0.327 ARI 0.749** [p5 0.455] · k5 49/22/16/9 0.646.
- Group survival (k4): Central 1.000, South-west **0.917**, Foothills 1.000. (k2: both 1.000.)
- Switching (k4, ≥0.2 = borderline): Sangrur 0.876, Barnala 0.820, Tapa 0.798, Lehra 0.742, Firozpur 0.564, Dinanagar 0.300, Faridkot 0.242, Rampura Phul 0.233, Morinda 0.211. Under the 2-group cut only Dinanagar 0.300 and Morinda 0.211 switch.
- Frozen v2 (`freeze.py`, K_FROZEN = 4): **Central 58 · South-west 22 · Foothills 16 · Outlier 1**.
  - South-west: Abohar, Barnala, Bathinda, Budhlada, Faridkot, Fazilka, Firozpur, Gidderbaha, Guruharsahai, Jaitu, Jalalabad, Kotkapura, Lehra, Malout, Mansa, Maur, Rampura Phul, Sangrur, Sardulgarh, Sri Muktsar Sahib, Talwandi Sabo, Tapa.
  - Foothills: Anandpur Sahib, Balachaur, Chamkaur Sahib, Dasua, Dera Bassi, Dinanagar, Garhshankar, Hoshiarpur, Kharar, Morinda, Mukerian, Nangal, Pathankot, Rup Nagar, SAS Nagar (Mohali), Tanda.
  - 2-way alternative: Plains 80 (= Central + South-west) / Foothills 16 (nested exactly).
  - Medians (CI · rice share cal · rain · AESR 14.2 · AESR 2.5 · GW22): Central 204.4 · 0.748 · 725 · 0 · 0 · 230 | South-west 203.0 · 0.691 · 482 · 0 · 1.0 · 131 | Foothills 194.3 · 0.282 · 988 · 0.981 · 0 · 104.
  - vs v1: moved Central → SW: Barnala, Firozpur, Lehra, Rampura Phul, Sangrur, Tapa; Central → Foothills: Chamkaur Sahib, Morinda.
- Sensitivity (k4, GW-2025 scenario removed per decision): weights ±15%: CI×0.85 1.000, rain×0.85 0.936, rice×0.85 / rain×1.15 / GW×1.15 / GW×0.85 0.835, zone×1.15 0.800, soil×0.85 0.722, rice×1.15 0.687, zone×0.85 0.620, **CI×1.15 0.484, soil×1.15 0.484** (SW dissolves). Drops: rice 0.875, CI 0.832, GW 0.771, soil 0.771, zone 0.422, rainfall 0.270. Terrain-instead-of-zone 0.709. Most moves are the 9 borderline tehsils, except where the SW dissolves as a block.
- Implication: the equal-weights justification is solid for the 2-group cut but weak for the 3-region cut; the report must say so. PD rule (hold under both groupings) stays essential.
- [P] Proposal pending: consensus assignment for tehsils with switch rate > 0.5.

### 2026-10-07 — Consensus placement adopted; FINAL FROZEN GROUPING (v3): Central 63 / South-west 17 / Foothills 16 + Dhar Kalan
**Plain:** Five tehsils (Sangrur, Barnala, Tapa, Lehra, Firozpur) were placed in the south-west by the single full-data tree, but across 300 reshuffles they sat with the central plains most of the time. We now place every tehsil in the group it lands in most often across the reshuffles ("consensus"). Only those five moved, back to central, and the groups fit the data better (silhouette 0.327 → 0.354). They stay flagged as borderline.
**Technical:**
- [C] Soham approved consensus placement.
- `stability.py`: per k, consensus label = most frequent matched group over runs where **all** full-data groups survived; `k*_consensus_share` = frequency of that label; output `outputs/grouping/labels_consensus.csv`.
- `freeze.py`: group = consensus label at K_FROZEN = 4 (3 groups); `group_2way` = consensus at k = 2; new columns `moved_by_consensus`, `consensus_share`; `FROZEN_config.json` records `assignment`, `silhouette_consensus` 0.354, `silhouette_tree_cut` 0.327.
- Moved (South-west → Central): Barnala (consensus share 0.820), Firozpur 0.564, Lehra 0.742, Sangrur 0.876, Tapa 0.798.
- **Final groups:** Central **63** · South-west **17** (Abohar, Bathinda, Budhlada, Faridkot, Fazilka, Gidderbaha, Guruharsahai, Jaitu, Jalalabad, Kotkapura, Malout, Mansa, Maur, Rampura Phul, Sardulgarh, Sri Muktsar Sahib, Talwandi Sabo) · Foothills **16** (Anandpur Sahib, Balachaur, Chamkaur Sahib, Dasua, Dera Bassi, Dinanagar, Garhshankar, Hoshiarpur, Kharar, Morinda, Mukerian, Nangal, Pathankot, Rup Nagar, SAS Nagar, Tanda) · Dhar Kalan outlier. 2-way: Plains 80 (= Central + SW) / Foothills 16.
- Medians (CI · rice share cal · rain · AESR 2.5 · GW22): Central 204.7 · 0.757 · 721 · 0 · 230 | South-west 202.1 · 0.571 · 464 · 1.0 · 111 | Foothills 194.3 · 0.282 · 988 · 0 · 104.
- Borderline (switch ≥ 0.2), with consensus share: Firozpur .564, Dinanagar .686, Lehra .742, Faridkot .758, Rampura Phul .767, Morinda .788, Tapa .798, Barnala .820, Sangrur .876.
- Note: sensitivity and bootstrap ARI were computed against the tree cut (58/22/16); the consensus partition differs only in these 5 border tehsils.

### 2026-10-07 — CI dropped (5 dimensions); FINAL FROZEN GROUPING v4: Central 63 / South-west 18 / Foothills 15 + Dhar Kalan
**Plain:** Removing the unreliable cropping-intensity variable made the grouping clearly more stable. The three regions now appear directly when the tree is cut into three (no small-group fixes needed), stay together in about 9 of 10 reshuffles, and only 3 tehsils are borderline (was 9). Versus v3, only Firozpur (to south-west) and Dinanagar (to central) moved, exactly as predicted. Caveat: the south-west split still depends on weights. 15% more weight on rice or soil, or dropping any one dimension, merges the south-west back into central.
**Technical:**
- Dimensions (5, equal weights 1/5): rice_share_2022_cal · mean_monsoon_rainfall_mm · zone (AESR 2018 shares) · mean_extraction_pct_2022 · soil (8 categorical). Range excl. Dhar Kalan; Dhar Kalan set aside; MIN_GROUP_SIZE 5; bootstrap 300 × 80%, seed 42.
- v3 outputs archived: `outputs/grouping_frozen_v3_with_ci/`. `freeze.py` K_FROZEN = 3; `sensitivity.py` K_CHOSEN = 3.
- Tree (97): k2 81/16 · k3 81/15/1 · k4 63/18/15/1. Stability (96): k2 81/15 sil 0.409 ARI **0.981** [p5 0.932] · **k3 63/18/15 sil 0.377 ARI 0.890** [p5 0.563] · k4 63/18/15 0.870 · k5 0.765. Group survival k3: Central 1.000, South-west 0.937, Foothills 1.000.
- Consensus = tree cut (no moves); silhouette 0.377. Borderline (switch ≥ 0.2): Firozpur .431 (SW), Dinanagar .308 (Central), Faridkot .243 (SW).
- **South-west (18):** Abohar, Bathinda, Budhlada, Faridkot, Fazilka, Firozpur, Gidderbaha, Guruharsahai, Jaitu, Jalalabad, Kotkapura, Malout, Mansa, Maur, Rampura Phul, Sardulgarh, Sri Muktsar Sahib, Talwandi Sabo. **Foothills (15):** Anandpur Sahib, Balachaur, Chamkaur Sahib, Dasua, Dera Bassi, Garhshankar, Hoshiarpur, Kharar, Morinda, Mukerian, Nangal, Pathankot, Rup Nagar, SAS Nagar (Mohali), Tanda. **Central (63):** the rest. 2-way: Plains 81 (= Central + SW) / Foothills 15.
- Medians (rice share cal · rain · AESR 14.2 · AESR 2.5 · GW22): Central 0.751 · 721 · 0 · 0 · 230 | South-west 0.587 · 467 · 0 · 1.0 · 118 | Foothills 0.281 · 981 · 1.0 · 0 · 117.
- Sensitivity (k3, ARI vs 63/18/15): rice×0.85, rain×1.15, GW×1.15 → 1.000; zone×0.85 0.966; GW×0.85, soil×0.85 0.932; rain×0.85, zone×1.15 0.833; **soil×1.15 0.510; rice×1.15 0.484** (SW merges). Drops: soil-without-near-constant 0.965; rice 0.599; rainfall 0.551; zone 0.523; GW 0.484; soil 0.484; terrain-instead-of-zone 0.484.
- Reading: 10/12 weight perturbations keep ARI ≥ 0.83; all five dimensions are needed for the SW split; equal weights are defensible but the SW/central boundary is weight-sensitive. Keep the PD rule (hold under both 3-region and 2-way groupings).

### 2026-10-14 — Report figures for the frozen grouping (v4)
**Plain:** We made six report figures straight from the frozen outputs, so the pictures always match the numbers. The map shows the three groups form connected regions (central plains, dry south-west, Siwalik foothills) even though the method never saw locations. That is the clearest sign the grouping is real. The other figures show the merge tree, what makes each group different, why 3 groups, how robust the groups are to weight changes, and the Chen-vs-official rice correction.
**Technical:** `Code/figures/make_grouping_figures.py` → `outputs/figures/fig_A_group_map.png` (polygons `punjab_current_tehsils_lgd.gpkg` ⋈ `FROZEN_groups.csv` on `lgd_tehsil_code`, UTM 43N, borderline hatched), `fig_B_dendrogram.png` (average linkage recomputed from `dist_baseline.csv`; branches coloured by consensus group; cut between the 4th- and 3rd-last merge heights = 3 groups + Dhar Kalan), `fig_C_group_profiles.png` (rice share cal, rainfall, GW 2022 strip plots + mean AESR shares; Dhar Kalan excluded), `fig_D_choosing_k.png` (`stability_by_k.csv`: silhouette, mean ARI with p05–p95 band), `fig_E_sensitivity.png` (`sensitivity_table.csv`, retired terrain design excluded), `fig_F_rice_calibration.png` (`chen_vs_official_by_district.csv`). Palette: validated categorical slots 1–3 (all-pairs safe), outlier grey. Used in `report/report_draft.md` §4.1.
