# Draft: §3.4 (tehsil measure), §3.5, §3.6 and §4.3 for `report_draft.md` (2026-11-10)

> **Status: [P] draft for Soham's review.** Not yet merged into `report_draft.md`. Proposed placement:
> - **§3.4:** the "Tehsil measure" block replaces the three "Tehsil measure ⏸" bullets at the end of §3.4. The "*Status: … tehsil aggregation ⏸*" line goes.
> - **§3.5 and §3.6:** replace their placeholders.
> - **§4.3:** replaces "4.3 Positive deviants ⏸".
> - **Abstract / Contributions:** item 4 of the Contributions list can then be filled in (bottom of this file).
>
> Sources: `sub_journeys/2_Stage2_Determine_Positive_Deviants/2.1/task_tehsil_burn_metric.md`, `2.3/task_pd_identification.md`, `2.4/task_pd_validation.md`; outputs in `outputs/burn_tehsil_rf/`, `outputs/pd/`.

---

### 3.4 Performance measurement — *tehsil measure (replaces the ⏸ bullets)*

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

---

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

---

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

---

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

**Table 4. Robust deviants** (`outputs/pd/robust/robust_deviants.csv`; burnt share = 2020–24 mean; %/yr = trend relative to the group, main run).

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

**Table 5. Validation of robust PDs** (`outputs/pd/pd_validated.csv`).

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

---

### Suggested text for Contributions item 4 (§1)
4. **Positive deviant tehsils, validated on the data.** Abohar is the only strict PD: lowest burner in the South-west and among its fastest reducers. A low-burning Doaba cluster (Dinanagar, Phagwara, Jalandhar-I, Adampur, with Gurdaspur and Banga) and Talwandi Sabo also hold up. The checks were resampling, alternative settings, cloud gaps, rice presence and harvest timing. Temporal deviance alone proved too noisy at 100 points per tehsil (Sections 3.5, 3.6, 4.3).

### Suggested additions to §6 Limitations
- PD identification rests on 100 points per tehsil. That is enough for the static ranking (V1), not for five-season trends.
- 2024 is a doubtful season (late-November burns; weaker agreement with VIIRS). Every result is also shown without it.
- The Foothills (15 tehsils) are measured but not ranked.
- No visual or field confirmation of any PD point; cotton passing the harvest filter at Abohar is not ruled out.
- Burning rises with rice share within the frozen groups. The groups control rice share only coarsely, so finer groups (or rice-share bands) are a design option for future work.
