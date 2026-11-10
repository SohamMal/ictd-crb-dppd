# Draft: Stage 3 sections for `report_draft.md` (2026-11-10)

> **Status: merged into `report_draft.md` on 2026-11-10** (tables renumbered there: 3 Drivers, 6 Robust deviants, 7 Validation, 8 Drivers vs burning). Edit the report, not this file. Proposed placement: §3.7 replaces the "3.7 Discovering underlying factors ⏸" placeholder, §4.4 replaces "4.4 Predictors ⏸", the limitation and future-work bullets go into §6, and the references continue the list at [21].
> **Depends on unwritten sections:** §3.5 (PD identification), §3.6 (PD validation) and §4.3 (positive deviants) are still placeholders in the report. The text below refers to them for the PD list: 6 validated static PDs, 2 PDs with caveat, 4 static NDs.
> Every number below comes from `outputs/predictors/drivers/` (`driver_summary.csv`, `unit_profiles.csv`, `urban_check_*.csv`); code in `Code/predictors/`.

---

### 3.7 Discovering underlying factors

**Approach.** DPPD normally confirms positive deviants and their practices through fieldwork. This project is academic and uses no fieldwork, interviews or expert consultation. Stage 3 is therefore a **retrospective desk study on public online data**, which the handbook allows when field engagement is not possible [8, p. 77–78]. The aim is to find *candidate* explanations that a later field study could test. The aim is not to prove causes.

**Drivers, not conditions.** A driver is something that could, in principle, be changed or transferred: a crop rotation, a market for straw, a labour arrangement. Structural conditions (rainfall, soil, rice share, groundwater, zone) were used to build the peer groups (§3.2) and are never re-used as drivers. We started from a catalogue of hypothesised drivers drawn from the literature and news, and kept those with public data at tehsil or district level for 2019 or later. Older data was used only as a fallback.

**Table 6. Drivers.** *(T = tehsil level; D = district value given to every tehsil in it)*

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

### 4.4 Predictors

**Table 7. Drivers vs burning within groups.** *(ρ = Spearman with 2020–24 mean burnt share; partial = rice share held constant; \* p < 0.05, \*\* p < 0.01. Expected sign: negative if more of the driver should mean less burning. "Sides" = PDs on the expected side of the group median / NDs on the opposite side.)*

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

### Additions to §6 Limitations and future work

**Limitations of Stage 3**
- No fieldwork or interviews, so no practice is confirmed on the ground (academic scope).
- Small numbers: 8 PDs and 4 NDs; 44 tests, so about 2 false positives at p < 0.05.
- Mixed years: Census 2011, Livestock Census 2019, settlement model 2020, basmati 2023, burning 2020–24.
- District-level basmati cannot separate tehsils within a district (e.g. Phagwara and Kapurthala), and APEDA's district table is internally inconsistent for 6 districts.
- The straw-buyer list is town-level, the biomass part dates from 2017, and CBG start years are unknown.
- CRM machine and hiring-centre data, the scheme most directly aimed at burning, is not available by district online.
- 8% of 2019 livestock (by head) could not be matched to Census villages.

**Future work**
- Field interviews in the Doaba PDs and in Abohar, structured around the leads above.
- District CRM machine and hiring-centre data via RTI or the Punjab agriculture department.
- A dated, geocoded straw-buyer list with collection radii.
- Tehsil-level basmati and potato maps from Sentinel-2.

---

### References (continue at [21])
[21] CIMMYT. Punjab plot-owner surveys 2021 and 2022 (paddy harvest and wheat sowing dates). ⏸ full citation
[22] Office of the Registrar General & Census Commissioner, India. *Census of India 2011: Primary Census Abstract, Punjab* (village-level, PCA_CDB-03).
[23] Hindustan Times (Bathinda). Biomass plants in Punjab have a chequered journey. 18 Nov 2017. https://www.pressreader.com/india/hindustan-times-bathinda/20171118/282230895988653
[24] Mongabay-India. From pollution to power, what stops paddy straw from becoming the fuel of choice. Dec 2021. https://india.mongabay.com/2021/12/from-pollution-to-power-what-stops-paddy-straw-from-becoming-the-fuel-of-choice/
[25] BioEnergy Times. Four CBG plants to come up in Punjab in 2026-27, to consume 1.08 lakh tonnes of paddy residue. https://bioenergytimes.com/four-cbg-plants-to-come-up-in-punjab-in-2026-27-to-consume-1-08-lakh-tonnes-of-paddy-residue/
[26] G. Dipoppa, S. Gulzar. Bureaucrat incentives reduce crop burning and child mortality in South Asia. *Nature*, 2024. ⏸ check title, volume and pages
[27] M. Schiavina, M. Melchiorri, M. Pesaresi. GHS-SMOD R2023A: GHS settlement layers, application of the Degree of Urbanisation methodology. European Commission JRC, 2023. (Earth Engine: JRC/GHSL/P2023A/GHS_SMOD_V2-0)
[28] APEDA. *Crop Survey for Estimation/Assessment of Acreage, Crop Health and Expected Yield of Basmati Rice during 2023*, Volume III, 2025. https://apeda.gov.in/sites/default/files/documents/2025-06/Basmati_Crop_survey_Report_3_Season_2023.pdf
[29] Department of Animal Husbandry and Dairying. *20th Livestock Census 2019*, village-level data, via ARTPARK Public Data (dataset 0041). https://publicdata.artpark.ai/en/latest/datasets/0041.html
