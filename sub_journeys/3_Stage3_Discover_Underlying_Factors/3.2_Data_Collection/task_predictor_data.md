# Predictor data collection
**DPPD position:** Stage 3 › Data Collection · **Status:** Not started · **Last updated:** 2026-10-06

## In plain words
Here we collect the things that might *explain* why a tehsil burns less: access to straw-management machines, nearby factories that buy straw, markets, crop varieties. These were deliberately kept out of the grouping, because they are possible causes we want to discover, not conditions to control for.

## Technical summary
- **Hypothesised drivers [P]** (from A1 §2.1 + later notes): CRM machine subsidies / counts (district/block); Custom Hiring Centres; ex-situ demand (biomass power, paper, CBG plants nearby); mandi access (Agmarknet locations, distance); short-duration varieties (PR-126) vs basmati; Happy Seeder / Super SMS adoption; awareness campaigns; cooperative density.
- **Rule [C]:** these never enter grouping.
- **Constraint:** collect only what is quick (≤1 day); many are district-level only.

## Log (append-only, chronological)
### 2026-10-06 — File created
**Plain:** Placeholder.
**Technical:** Planned 15 Oct.

### 2026-10-23 — Driver catalogue widened; recent (2019+) sources preferred, older as fallback
**Plain:** Soham confirmed the first list (labour, farm size, straw buyers, mandis, towns, CRM/CHCs, varieties, enforcement). He asked to look for more possible causes and for data from 2019 onward where possible, with older data kept as a fallback. Deep, tehsil-specific research waits until the PDs are known, so we search only where it matters. A straw-buyer list compiled from news and PEDA, with a source per plant, is acceptable if no official list exists.
**Technical:**
- [C] Soham: list confirmed; prefer 2019+ data, older as fallback; tehsil-specific deep research deferred until PDs exist; news-compiled plant list OK.
- [P] Added drivers: district/state-border proximity (Dipoppa & Gulzar 2024, Nature: fires +15% when wind carries smoke to a neighbouring jurisdiction; larger near borders); satellite-derived harvest date and the harvest-to-wheat-sowing gap; post-paddy crop (potato/vegetables, Doaba); livestock density (straw as fodder; 20th Livestock Census 2019, village level via dataful); leasing/absentee (NRI) ownership; MGNREGA job cards (village, 2019+) as a recent labour-pool proxy; PM-KISAN village beneficiaries ÷ rice ha as a recent farm-size proxy; staggered transplanting zones (2022–25, district lists); awareness/zero-burning village awards; KVK/PAU extension distance.
- Recency: Agriculture Census 2021-22 Phase I done in Punjab but tehsil tables not found → fallback 2015-16 (tehsil tables exist per the FAO catalogue). Village-wise CHC list on agrimachinerypb.com not found publicly → fallback district CHC targets 2024-25 + NGT status reports. PR-126 / DSR district-wise not found (only Ludhiana PR-126 ≈ 46% in 2024; basmati 2024 district figures in news).
- Endogeneity flag [P]: enforcement (red entries, FIRs), hotspot-village nodal officers and awards react to past burning → use only lagged or as context, never as a clean cause.

### 2026-10-24 — Driver 1 built: harvest date and harvest-to-wheat-sowing turnaround; checked against CIMMYT
**Plain:** We measure, for each tehsil and year, when paddy is harvested and when the next crop greens up, using Sentinel-2 greenness at 30 fixed rice points per tehsil. The time between the two is the turnaround. A short turnaround is the main reason farmers give for burning. We checked against the CIMMYT survey, where farmers reported their own dates. Our harvest date is about 3 days earlier than reported, with a typical error of 6 days. The field shows green about 4 weeks (28 days) after the farmer says wheat was sown, so estimated sowing = green-up − 28 days. Field by field the match is weak, because survey plots are located only to ~1 km and our points are other fields in the same cell. District averages rank correctly (harvest 0.80; sowing 0.77 in 2021 and 0.93 in 2022). Since tehsil values are averages too, this is the level that matters.
**Technical:**
- [C] Soham: start Stage 3 with satellite/distance drivers (group A), harvest/turnaround first.
- Code: `Code/predictors/harvest_gap.py` → `outputs/predictors/harvest_gap/` (`tehsil_harvest_gap.csv`, `point_dates.csv`, `cimmyt_validation.csv`; raw NDVI cached in `raw/`). S2 SR Harmonized, cloud < 60%, SCL 4/5, 1 Sep–31 Jan, 10 m NDVI; first 30 points per tehsil from `outputs/burn_tehsil/points.csv` (same panel as the burn measure); 2019–2024.
- Rules: harvest = midpoint between last look NDVI ≥ 0.45 and first look on/after 15 Sep with NDVI < 0.30 (uncertainty = half the look gap); green-up = first look after harvest with NDVI ≥ 0.30 sustained over the next look; none by 31 Jan → `no_greenup_share`; turnaround = gap − 28 d.
- CIMMYT validation (15 rice points per 0.01° cell): 2021, 138 cells / 262 plots: harvest error median −3.0 d, MAE 5.8, cell ρ 0.15; green-up − reported sowing median 28 d (IQR 23–32), cell ρ 0.04. 2022, 137 cells / 426 plots (sowing only): lag 27 d (IQR 23–32), cell ρ 0.56. District medians: harvest ρ 0.80 (2021, 4 districts); sowing ρ 0.77 (2021, 4), **0.93** (2022, 8).
- Reading [P]: level and between-area ranking hold; cell-level ρ is low because of location rounding (different fields), not necessarily a measurement fault. Tehsil run 2019–2024 launched 2026-10-24.

### 2026-10-24 — Harvest/turnaround tehsil run: results; 2019 green-up unreliable (December cloud/fog)
**Plain:** The run finished for 97 tehsils, 2019–2024. Paddy is harvested around 22–26 October (median). Fields are re-sown about 2–3 weeks later, which matches the 15–18 day window farmers describe. South-west harvests about a week later than Central (day 302 vs 296). Tehsil rankings repeat only moderately from year to year (0.2–0.6), so the turnaround is partly a tehsil trait and partly year-specific. 2019 cannot be trusted for the sowing side. December 2019 had about one clear image per field, so green-up dates there are up to a month late (two-thirds of points have > 20 days between looks). 2024 has a smaller version of the same issue (15%). The harvest dates themselves are fine in all years.
**Technical:**
- Harvest found for 97–100% of points; harvest DOY median 294–299 (2019–2024); clear looks per point per season median 14 (2019) to 21.
- Turnaround (gap − 28 d), median across tehsils: 2019 37.0 (unreliable), 2020 22.0, 2021 17.0, 2022 14.0, 2023 14.0, 2024 22.0. 2024 min −15 (green-up < 28 d after harvest: early potato/weeds, or the lag rule).
- By group (all years): harvest DOY Central 295.5, South-west 302, Foothills 294; turnaround Central 17.0, SW 19.0, Foothills 18.8.
- Year-to-year Spearman of tehsil turnaround: 0.19–0.63 (2020–22 highest).
- Green-up look-gap (green-up date − previous clear look): median 30 d in 2019 (66% > 20 d; December 1.0 clear look/point) vs 5–10 d in 2020–2024 (2–5% > 20 d; 2024 15%). January green-ups: 2019 54%, 2024 20%, others 2–15%.
- Proposed fix [P]: store green-up uncertainty per point and compute tehsil turnaround only from points with uncertainty ≤ 20 d; mark 2019 turnaround as not usable (harvest date kept). The burn/PD seasons are 2020–2024, so 2019 is not needed.

### 2026-11-10 — All drivers collected from online data except CRM machines
**Plain:** Soham approved 9 candidate drivers, all from online data. Eight were built for every tehsil (or, for basmati, every district). The ninth, straw-management machines and hiring centres per district, could not be found anywhere online at district level, only as state totals, so it is dropped and stated as a limitation. Livestock turned out better than expected: a public copy of the 2019 Livestock Census gives counts for every village, so it is measured per tehsil rather than per district.
**Technical:**
- [C] Soham 2026-11-10: all 9 drivers, tier 1 first; online data only (no contacts).
- Code: `Code/predictors/drivers.py` → `outputs/predictors/drivers/tehsil_drivers.csv` (97 tehsils), `livestock_match.csv`. Source tables tracked in git: `Data/Predictors/straw_buyers.csv`, `basmati_district_2023.csv` (`.gitignore` now keeps `Data/Predictors/*.csv`; downloads stay ignored).
- D1 turnaround: harvest-gap points 2020–24; green-up used only if the clear look before it is ≤ 20 d earlier (fix proposed 10-24). Median 16 d.
- D2 early second crop: share of harvested points with NDVI ≥ 0.6 after harvest and by 30 Nov. A December cut (≥ 0.6 by 31 Dec) was rejected: wheat also reaches it (about 50% of points everywhere). The 30 Nov version picks out Amritsar-I (37%), Amloh, Jalandhar-II, Majitha. Median 5%.
- D3 labour / small farms: Census 2011 village PCA (on disk), 12,581/12,581 villages bridged to current tehsils. Agricultural labourers per cultivator (Abohar 1.61, state maximum); cultivators per 100 ha calibrated rice.
- D4 straw buyers: 14 plants, one source each. 7 private biomass plants from HT 2017 (Muktsar, **Abohar**, Malout, Garhshankar, Rajpura, Nakodar, Mansa); Sukhbir Agro near Ferozepur (Mongabay 2021); 6 operational CBG plants (Khanna, Sangrur, Moga, Fatehgarh Sahib, Patiala, Hoshiarpur; BioEnergy Times, about 2025). Town-level only, placed at the host tehsil's rice centroid. PEDA project pages returned no table. Limits: the biomass list dates from 2017 and CBG start years are unknown.
- D5 border: SHRUG 2011 district polygons; km to inter-state and international border from the rice-point centroid.
- D6 city: JRC GHS-SMOD V2-0 2020 via GEE (1 km); km to urban-centre cell (class 30); urban share (classes ≥ 21) of tehsil area.
- D7 basmati: APEDA Basmati Crop Survey 2023 Vol III p.11 (district table extracted with PyMuPDF), over Statistical Abstract 2022 rice area 2021-22. APEDA's district totals sum to 767.6, not the published 812.4 thousand ha. Rows where the total and the variety columns differ by > 20% are marked: Barnala, Bathinda, Kapurthala (→ Phagwara), Malerkotla, Moga, Gurdaspur. Malerkotla is pooled with Sangrur.
- D8 CRM machines / CHCs: **dropped**. Only state totals online (e.g. 23,792 CHCs; ~1.46 lakh machines since 2018-19, from a party-run wiki citing a government release). CEEW's CHC report is > 10 MB (fetch limit); CAQM and Punjab agriculture pages were not readable.
- D9 livestock: 20th Livestock Census 2019 village file (ARTPARK public copy of DAHD data, 67 MB, `Data/Predictors/livestock/`), matched to Census 2011 villages by block + hadbast number + name similarity ≥ 0.6, else unique name + number. 11,466/12,816 villages, 91.8% of bovines. The Statistical Abstract 2019 only has 2012 data, with rotated text that cannot be parsed. DAHD and the Punjab government sites refused automated fetches.
