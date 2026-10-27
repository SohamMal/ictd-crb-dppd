# Agro-climatic zones
**DPPD position:** Stage 2 › Homogeneous Grouping (climate/terrain dimension) · **Status:** **Active**: need zone data finer than district · **Last updated:** 2026-10-06

## In plain words
Agricultural scientists divide Punjab into zones (e.g. "Sub-mountainous", "Central plain", "Western") that summarise climate, terrain and soil together. We first collected the official zones, but they are assigned by **district**. A district can span very different land (Patiala is listed in three zones), so we dropped them for rainfall + terrain. The professor has now said richer zone data exists. Our new plan is to use zones **instead of** rainfall and terrain, so the same information isn't counted twice. The task is to find zone data at tehsil level or finer.

## Technical summary
- **Collected (district level):** `Data/AgroClimate Zones/Masters/punjab_agro_climatic_master.csv` (+ Haryana). Columns: ICAR agro-ecological sub-region, Planning Commission region (VI Trans-Gangetic / I West Himalayan), **NARP zone** (PB-1 Sub-mountainous Undulating, PB-2 Undulating Plain, PB-3 Central Plain, PB-4 Western Plain, PB-5 Western), source = ICAR-CRIDA District Agriculture Contingency Plans. Recorded inconsistencies: Faridkot PB-4 vs PB-5 across documents; Gurdaspur/Pathankot dual PB-1/PB-2; Patiala triple PB-2/3/4; Barnala zone list blank.
- **Coverage gap (Sept merge):** Tarn Taran and SBS Nagar had zero zone data (969 villages). `Data/02 Cleaned/agro_climatic_zone_cleaned.csv`.
- **Rejected (3 Oct):** ✘ NARP at district level: tehsils with very different rainfall in one district would be grouped together.
- **Reinstated (2026-10-06) [C]:** zones replace rainfall + terrain; data must be tehsil-level or richer.
- **Candidate sources to search [P]:** NBSS&LUP agro-ecological sub-regions (AESR) as polygons (~60 sub-regions nationally, crossing district lines); PAU / ICAR-ATARI Punjab sub-zones; block-level "Kandi / Central / South-western / Sub-mountainous" belts (the CI QA already uses Kandi and Southwestern belt labels).
- **Mapping plan [P]:** polygon zones → majority-area overlap per village (rule already approved) → tehsil mode or area shares.
- **Open [?] (Soham):** encode as a categorical zone label (0/1 mismatch in Gower) or as numeric zone attributes?

## Log (append-only, chronological)
### Sep 2026 — District zone masters built (reconstructed)
**Plain:** We collected official zone labels per district from government contingency plans.
**Technical:** Master files above; majority-area-overlap rule set for multi-zone villages. [C]

### 3 Oct 2026 — Zones replaced by rainfall + terrain (reconstructed)
**Plain:** District zones were too coarse, so we measured rainfall and terrain directly instead.
**Technical:** Superseded the earlier "NARP preferred" note. Needed advisor sign-off. [C]

### 2026-10-06 — Supervisor reverses: use zones (richer data exists)
**Plain:** The professor said better zone data is available. We will use zones in place of rainfall and terrain.
**Technical:** [C] Zones replace rainfall + terrain (Soham's decision, to avoid overlap). The dimension set is provisional (5 or 6 dimensions) until zone data is found. The clustering code will take a configurable dimension list. Fallback (DAY_PLAN Day 4): if no tehsil-level zone data by 9 Oct, freeze with rainfall + terrain and document the deviation.

### 2026-10-06 — Found finer-than-district zone data: NBSS&LUP AESR 2018 polygons
**Plain:** Instead of fixing the broken slope data, we searched for zone data first. The national soil-survey agency (NBSS&LUP) publishes a 2018 map of agro-ecological sub-regions drawn as real map shapes, not by district. We downloaded every shape covering Punjab and measured what share of each tehsil falls in each zone. Punjab has four main zones: Siwalik foothills (sub-humid), two semi-arid plains (moister and drier), and the arid south-west.
**Technical:**
- Searched: PAU's 6 zones (incl. a Flood Plain Region) are only published as district lists or maps in papers, with no GIS file found. FAO GAEZ hosts an "Agro Ecological Subregions of India" dataset page. Our saved Bhoomi GeoServer capabilities (`Data/Soil Data/getcapabilities_1.1.1.xml`) list `nbss_geoserver:AESR_2018`, `AESR_1999`, `AER_2015`, physiographic regions.
- Old GeoServer IP `14.139.123.73:8080` now times out; the current endpoint is `https://bhoomigeoportal-nbsslup.in/geoserver/wms`. WFS is disabled ("Service WFS is disabled"), but WMS `GetFeatureInfo` returns full polygon geometry + attributes.
- Fetch: `Data/AgroClimate Zones/AESR/fetch_zone_polygons.py` (iterative point queries at uncovered parts of the union of the 97 tehsil polygons until <0.01% uncovered) → `punjab_aesr_2018_raw.geojson` (16 features incl. neighbouring states; 6 clipped to PUNJAB). 201 queries; it stalled on a 0.012% border sliver (boundary mismatch), which is fine.
- Punjab zones (km², UTM43): **9.1** Northern Plain, Alluvial Plain Semi-Arid (moist), LGP 90–120: 12,533 · **2.5** Western Plain, Marusthali Typic Arid, LGP 60–90: 18,057 · **4.1** Northern Plain/Aravalli landscape Semi-Arid (dry), LGP 90–120: 12,094 · **14.2** Siwalik Hills/Outer Himalayas Sub-humid, LGP 120–150: 7,489 · slivers 14.3 (13) and 2.1 (12).
- Tehsil overlay (area shares): coverage ≥ 0.944 for all 97. Dominant zone counts: 2.5 → 27, 9.1 → 27, 4.1 → 24, 14.2 → 19. 21 tehsils have dominant share < 0.8 (genuinely split, e.g. Amritsar-I 4.1/9.1 = 0.56/0.44). Saved `punjab_tehsil_aesr2018_shares_exploratory.csv` (exploratory, produced by inline code; to be scripted if adopted).
- Agreement with grouping B: all 15 SW tehsils are in 2.5; 13/16 foothills in 14.2; central is spread over 4.1 (24), 9.1 (24), 2.5 (12), 14.2 (5). Mapping scale is coarse (AESR ≈ 1:4M), e.g. Samrala 57% in Siwalik 14.2.

### 2026-10-06 — Exploratory test: AESR zones in the grouping (not adopted)
**Plain:** We tried the zones in place of rainfall + terrain. As one category label per tehsil, the zone takes over and the groups simply become the four zones. As area shares, the dry south-west group disappears, because the arid zone also covers 12 central tehsils and nothing else separates them once rainfall is removed. Replacing only terrain with zones, and keeping rainfall, gives almost the same groups as before (only 3 border tehsils move) and gets rid of the broken slope data.
**Technical (Dhar Kalan aside, small-group merge, ARI vs B):**
- Zones replace rainfall + terrain, **shares** (4 numeric share columns in one dimension): k3–k5 → 79/17, ARI 0.410 (SW dissolves into central); k6 64/17/15, ARI 0.215.
- Zones replace rainfall + terrain, **dominant label** (1 categorical): k4–k6 → 27/27/24/18, ARI 0.211, silhouette 0.571. The groups are essentially the AESR zones (a one-column 0/1 dimension dominates the Gower mean).
- **Zones (shares) replace terrain only, rainfall kept:** k4/k5 → **66/16/14, ARI 0.897, silhouette 0.315**; moved only Gurdaspur, Mansa, Nawanshahr. k3 81/15 (ARI 0.460).
- Decision needed [?] (Soham): (a) zones replace rainfall + terrain as planned (SW lost / zones dominate); (b) zones replace terrain only, keep rainfall; (c) keep baseline and use AESR only as external validation. Encoding: shares vs label.

### 2026-10-06 — DECISION: AESR 2018 zones replace terrain only (rainfall kept), encoded as area shares
**Plain:** We will use the official agro-ecological zones, but only in place of terrain (elevation + slope). Rainfall stays. Each tehsil is described by what share of its land falls in each zone (e.g. 56% semi-arid dry plain, 44% moist plain), not by one forced label.

Why:
- **Zones instead of terrain:** zones are official, published data (NBSS&LUP 2018). They capture the foothills-vs-plains difference terrain was meant to capture. Our slope data turned out to be broken (identical values across different tehsils, zero variation between villages), so replacing terrain removes a defective variable without spending time recomputing it.
- **Rainfall kept:** the zone map is drawn at a very coarse scale. Its arid zone covers 27 tehsils, including 12 central-plain tehsils that are much wetter than the true south-west. Without rainfall, the dry south-west group (which the sensitivity test showed is real) disappears. Rainfall is measured per village, so it sees the difference the zone map cannot.
- **Shares instead of a label:** 21 tehsils are genuinely split between two zones. A single label would force them into one zone, and as a single 0/1 column it overpowers the other dimensions (the groups just became the four zones).

**Technical:**
- [C] Soham, 2026-10-06: option (b) with shares. This supersedes the same-day decision "zones replace rainfall + terrain" (Soham's earlier choice, made to avoid overlap). It is a deliberate, evidence-based deviation.
- New `zone` dimension = 4 numeric columns: share of tehsil area in AESR **14.2, 2.5, 4.1, 9.1** (slivers 14.3 and 2.1 < 0.1% of Punjab are ignored), compared with range-normalised |diff| and averaged within the dimension. Dimensions become: cropping intensity, rice share, rainfall, **zone**, groundwater 2022, soil (6, equal weights).
- Evidence (exploratory, ARI vs grouping B, Dhar Kalan aside, k5): (a) zones replace rain + terrain, shares → 79/17, ARI 0.410; (a) label → 27/27/24/18, ARI 0.211; **(b) shares → 66/16/14, ARI 0.897, silhouette 0.315**, only Gurdaspur, Mansa, Nawanshahr move.
- Acknowledged overlap: AESR classes are partly defined from rainfall (length of growing period), so zone and rainfall are not fully independent. Accepted because rainfall carries information the 1:4M zone map lacks. Report wording: "AESR zones replace terrain; rainfall retained because AESR (≈1:4M) cannot separate the arid south-west from the drier central plain."
- External validation retained either way: all 15 SW tehsils lie in AESR 2.5; 13/16 foothill tehsils in AESR 14.2.
- To do: script the tehsil × zone share computation (replace the exploratory CSV), add the columns to the masters, update `config.DIMENSIONS`, rerun Steps 3–7, then freeze.

### 2026-10-06 — AESR shares scripted and added to masters
**Plain:** The zone shares are now produced by a proper, rerunnable script and stored in the master files.
**Technical:** `Data/AgroClimate Zones/AESR/compute_tehsil_aesr_shares.py` → `punjab_tehsil_aesr2018_shares.csv` (`aesr_share_14_2, _2_5, _4_1, _9_1, aesr_dominant, aesr_dominant_share, aesr_coverage`). Zones dissolved by `aesr_id`, slivers <0.1% of Punjab dropped (14.3: 0.03%, 2.1: 0.02%), overlay in UTM 43N, shares normalised by AESR-mapped area (coverage min 0.944, a state-border mismatch). Punjab area fractions: 2.5 36.0%, 9.1 25.0%, 4.1 24.1%, 14.2 14.9%. Results identical to the exploratory run. Masters: raw 30→37, transformed 40→47, encoded 58→65 cols; backups `Data/_backup_2026-10-06_pre_aesr/`. Exploratory CSV deleted.
