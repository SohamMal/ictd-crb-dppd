# Predictor analysis & recommendations
**DPPD position:** Stage 3 › Data Analysis · **Status:** Not started · **Last updated:** 2026-10-06

## In plain words
We compare positive deviants with their own peers on each possible driver, to see what consistently differs. Then we turn that into practical advice: which practice, where to try it, and for which kind of tehsil.

## Technical summary
- **Plan [P]:** within-group PD vs non-PD comparisons (Mann-Whitney / effect sizes; small n → descriptive, not causal); literature/news triangulation; recommendations per peer group.
- **Open [?]:** A1 planned a causal FE/DiD stage (§2.4); whether it stays in scope is undecided.

## Log (append-only, chronological)
### 2026-10-06 — File created
**Plain:** Placeholder.
**Technical:** Planned 16 Oct.

### 2026-11-10 — First driver comparison: urban surroundings stand out in Central; little else holds once rice share is controlled
**Plain:** We compared the validated PDs with their peers on each driver. **The clearest pattern is urban surroundings.** 7 of the 8 low-burner PDs have more urban land around their fields than their group's median, and all 4 heavy burners have less. In Central, more urban land goes with less burning (ρ −0.61), and part of this holds even after accounting for rice share (−0.30). This fits the Doaba/Jalandhar belt: smoke near towns is noticed, off-farm work and vegetable markets are close. It does **not** explain Abohar, which is rural.
Abohar's own profile is different. It has a biomass power plant inside the tehsil (an early straw buyer), the most farm labourers per cultivator in Punjab, the highest basmati share among the PDs (Fazilka 57% of rice), and it sits 13 km from the Rajasthan border.
Several drivers that look related to burning (turnaround time, small farms) lose their link once rice share is held constant. They are probably standing in for "where paddy dominates". Basmati, livestock and straw-buyer distance show no consistent link. All of this is descriptive: with 8 PDs and 4 NDs we cannot claim causes.
**Technical:**
- Code: `Code/predictors/compare_drivers.py` → `outputs/predictors/drivers/unit_profiles.csv`, `driver_summary.csv`. Units: static PDs labelled validated (6) or caveat (2) in `pd_validated.csv`, static NDs (4). Burning = 2020–24 mean burnt share (s2rf). Partial ρ = Spearman of rank residuals after removing rank(calibrated rice share), within group.
- [C] Spearman ρ with burning (Central n = 63 / SW n = 18; partial in brackets):
  - urban area share: −0.61** (−0.30*) / +0.45 (+0.52*)
  - turnaround: −0.38** (−0.20) / +0.40 (+0.04)
  - cultivators per 100 ha rice: −0.28* (−0.19) / −0.49* (−0.05)
  - early second crop: −0.16 (+0.05) / −0.56* (−0.47, p = 0.05)
  - km to inter-state border: +0.11 (+0.07) / **+0.83** (+0.75**)
  - km nearest straw buyer: −0.20 (−0.26*) / 0.00 (+0.17)
  - labourers per cultivator, buyers within 30 km, km to urban centre, basmati, bovines per cultivator: |ρ| ≤ 0.27, none significant
  - (* p < 0.05, ** p < 0.01; 44 tests, so about 2 false positives are expected at 0.05.)
- [C] Side counts (PDs on the side of the group median the hypothesis expects / NDs on the opposite side): urban share 7/8 and 4/4; km to urban centre 6/8 and 3/4; turnaround 4/8 and 2/4; basmati 4/8 and 1/4; border 0/8 and 2/4.
- Reading [P]:
  - (1) Urban surroundings are the only driver that is consistent for the Central PDs and survives the rice control. It is not a practice farmers can copy, but it points to things that may come with towns: market access for vegetables, off-farm jobs, and enforcement or smoke visibility. A possible measurement effect (small peri-urban fields, mixed pixels) is not ruled out.
  - (2) In South-west the border sign is opposite to Dipoppa & Gulzar. Tehsils near the Rajasthan/Haryana border burn *less*, even with rice share held constant. This is probably the cotton belt (later paddy expansion) rather than a border effect.
  - (3) Abohar has a single-case profile (biomass plant in tehsil, labour, basmati). It is a lead for the report, not a finding.
  - (4) Turnaround and small farms are confounded with rice share.
- Open [?]: how to present this in the report (driver table + Abohar and Doaba case profiles); whether to add any check of the urban effect (e.g. burning at rice points far from towns inside the same tehsils).

### 2026-11-10 — Urban check: the urban link is a tehsil-wide trait, not fields next to towns
**Plain:** We tested whether the urban link works field by field: do rice fields close to a town burn less than fields farther away *in the same tehsil*? Only slightly. Fields within 2 km of a town or city burn about 6–8 points less than the rest of their tehsil, but only 4% of fields are that close. Beyond 2 km, distance makes no difference. Most importantly, when we score the PDs using only fields more than 5 km from any town, they burn just as little and keep the same rank in their group. So the low burning in Doaba/Jalandhar is not explained by fields next to towns. "Urban surroundings" marks a region that differs as a whole (the Doaba belt), not a local town effect. No sign of a measurement problem near towns: cloud gaps and clear looks are the same at every distance.
**Technical:**
- Code: `Code/predictors/urban_check.py` (SMOD grid now cached by `drivers.py` `smod_cells()`, outputs unchanged) → `outputs/predictors/drivers/urban_check_{bands,slope,far_points}.csv`. Point verdicts 2020–24, Central + SW; distance from each rice point to the nearest GHS-SMOD 2020 cell of class ≥ 21 (urban cluster) and class 30 (urban centre).
- The class ≥ 21 distance is not usable as a test: 72% of Central point-seasons are within 2 km and no point in Adampur, Dinanagar, Jalandhar-I, Phagwara, Banga, Gurdaspur or Zira is > 5 km away. Urban-centre distance is used for the reading.
- [C] Burnt share by distance to urban centre (raw / within tehsil-season), Central: 0–2 km 0.470 / −0.063 (n = 1,393); 2–5 km 0.536 / −0.003; 5–10 km 0.559 / −0.004; > 10 km 0.589 / +0.007. SW: 0–2 km 0.628 / −0.081 (n = 320); others within ±0.014.
- [C] Within-tehsil slope (burnt ~ log(1 + km), tehsil-season demeaned, 1,000 tehsil-bootstrap draws): Central +0.040 per log-km → 1 → 10 km = +6.8 pts (95% CI 3.7–10.2); SW +2.3 pts (−6.7 to 10.6).
- [C] PDs on points > 5 km from an urban centre only (share of points kept; burnt share all → far; group percentile all → far): Dinanagar 79%, 0.212 → 0.203, 0.016 → 0.016; Phagwara 58%, 0.301 → 0.273, 0.048 → 0.032; Jalandhar-I 40%, 0.310 → 0.321, 0.079 → 0.079; Adampur 100%, unchanged 0.302; Gurdaspur 0.289 → 0.280; Banga 0.342 → 0.355; Abohar 0.337 → 0.321; Talwandi Sabo 0.504 → 0.541 (percentile 0.111 unchanged). NDs unchanged.
- [C] Artefact check by band: unknown share 0.8–1.2% (Central), 0–0.2% (SW); median clear looks 12–13 in every band.
- Reading [P]: a small local near-town effect exists (≤ 2 km). The PD gap (about 30 pts below the group median) is tehsil-wide. In the report, urban share should be presented as a regional marker of the Doaba belt (with things that come with it: vegetable/potato markets, off-farm work, NRI incomes), not as "proximity to towns reduces burning".
