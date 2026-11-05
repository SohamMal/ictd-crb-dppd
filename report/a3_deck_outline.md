# A3 interim deck — outline (due 2026-11-06)

**Brief from Prof. (mail, 2026-11-01):** problem statement, methodology, implementation, results. Core implementation should be done; we are in the results phase.
**Shape:** 15 main slides + 3 backup. Story = *"We built a sound DPPD pipeline end to end, and it finds a small, defensible set of positive deviants."*
**Figure status:** ✅ exists · 🛠 needs making (small script from existing CSVs) · ✍ drawn diagram.

---

## Part 1 — Problem (2 slides)

### 1. Title
- Finding Positive Deviants in Crop Residue Burning: a DPPD study of Punjab tehsils
- Soham Malvadkar · COL7761 · Supervisor Prof. Aaditeshwar Seth · Advisors Basma Albanna, Andreas Pawelke

### 2. Problem statement
- Every Oct–Nov Punjab burns paddy straw; short gap before wheat sowing; major smoke source for the IGP / Delhi.
- Subsidies since 2018 (Happy/Super Seeder, CHCs), yet burning persists.
- Burning is **uneven even between similar places** → **Question:** *which tehsils burn much less than structurally similar peers, and what do they do differently?*
- Unit: **97 current Punjab tehsils** (Haryana deferred: incomplete data).
- Figure: ✍ one photo or map of Punjab fires (optional).

## Part 2 — Methodology (3 slides)

### 3. Why DPPD (problem–method fit)
- Outcome is measurable from satellites, varies a lot, and local solutions are plausible.
- PD practices already work under local constraints → more credible than imported fixes.
- Figure: ✍ DPPD pipeline strip: Fit → **Grouping → Measurement → PD identification → Validation** → Underlying factors. Highlight where we are (validation / factors).

### 4. Design rules we follow
- Grouping uses **structural conditions only** (climate, rice, water, soil). Never drivers (machines, mandis) and never burning outcomes.
- Grouping was frozen **before** burning was measured, so groups can't be bent by who burns.
- Everything re-derived in code (`Code/`), reproducible.
- Two kinds of deviance: **static** (lowest burner in group, 2020–24) and **temporal** (fastest decline vs group trend; Basma's suggestion).

### 5. Data
- Compact Table 1 from the report: SHRUG villages, LGD tehsils + 2011↔current crosswalk, Chen 2022 rice (calibrated to official), CHIRPS rainfall, AESR zones, CGWB groundwater 2022, NBSS&LUP soil, Sentinel-2, PlanetScope, Walker et al. ground truth, CEEW fields, CREAMS, VIIRS.
- One line: "mixed resolutions brought to tehsils through crosswalks".

## Part 3 — Implementation (5 slides)

### 6. Homogeneous grouping — method
- Dimension-balanced Gower distance (5 dimensions, equal votes) → average-linkage hierarchical clustering → silhouette → bootstrap ARI (300 × 80%) → one-factor sensitivity.
- Figure: ✅ `outputs/figures/fig_B_dendrogram.png` or ✅ `fig_D_choosing_k.png`.

### 7. Homogeneous grouping — result
- **Central 63 / South-west 18 / Foothills 15 + Dhar Kalan outlier.** Silhouette 0.377, ARI 0.890; 2-group version ARI 0.981.
- No location was given to the method, yet the groups form connected agro-ecological belts.
- Weak point: SW/Central border is a gradient → PDs must also hold under the 2-group version.
- Figure: ✅ `outputs/figures/fig_A_group_map.png` (+ ✅ `fig_C_group_profiles.png` in backup).

### 8. The hard problem: burnt vs ploughed
- Burn index (BAIS2 + TCB) catches 98% of burns **but also flags 81% of ploughed-not-burnt fields** (Walker ground truth).
- Fresh ash is black for only 2–3 days, then looks like ploughed soil; Sentinel-2 revisits every 5 days.
- Tried and rejected: land surface temperature, Sentinel-1 radar (Basma's suggestion; documented negative result).
- Figure: ✅ `outputs/planet/fig_planet_vs_s2.png` or a Planet strip from `outputs/planet/strips_v2_jalandhar_2021/`.

### 9. Our burn detector
- Flag (BAIS2+TCB) → pick the look with the **largest jump** → random forest on before/after bands, trained on Walker ground truth → cut-off 0.79.
- Walker CV: **burns caught 90%, ploughed called burnt 81% → 18%**, AUC 0.94.
- Independent test, Jalandhar 2021 (not retrained, daily PlanetScope as judge): not-burnt called burnt 23/32 → 0–3/32.
- Figure: ✍ 4-box pipeline diagram + Table 4 (compact).

### 10. From fields to tehsils
- 100 cropland points per tehsil × 6 seasons (2019–24), season 15 Sep–30 Nov (ISRO/CAQM window). Metric = burnt share.
- Checks: tehsil ranking vs VIIRS fire counts **ρ 0.78–0.87**; year-to-year stability **ρ 0.82–0.91**; CREAMS 2022 district ρ 0.87 (state 7.8% vs 9.9%).
- Caveats: 2024 suspect (72% of burns seen after 15 Nov; VIIRS ρ 0.51); level higher than CREAMS in 2019.
- Figure: 🛠 scatter: our tehsil burnt share vs VIIRS fires/rice ha (one year), or the check table.

## Part 4 — Results (3 slides)

### 11. Who burns how much
- Area-weighted burnt %, 2020–23: Central ≈ 52–67%, South-west ≈ 60–70%, Foothills ≈ 20–27%.
- Within-group spread is large (Central 0.25 → 0.81) → room for deviance.
- Figure: 🛠 tehsil choropleth of mean burnt share 2020–24.

### 12. PD identification — rule
- Static: burnt share below the group's IQR fence (Q1 − 1.5 IQR, log scale). Temporal: decline vs group trend beyond the fence.
- Robust = holds in **both** runs (2020–24 and 2020–23, because 2024 is suspect). Old "bottom 10%" rule shown alongside.
- Foothills measured but not ranked (n too small, weaker validation).

### 13. PD identification — result (headline)
- **Abohar (SW): the only strict PD.** Burnt share 0.34 vs group median 0.73; also the fastest reducer (−11%/yr vs group).
- **Borderline:** Dinanagar (static), Samana (temporal).
- **Doaba low-burning cluster** (Gurdaspur, Phagwara, Adampur, Jalandhar-I, Banga): ~half the group median but low together → likely structural (e.g. potato/vegetable rotation), studied as a question, not as PDs.
- Negative deviants: Malout (borderline, burning rising fastest); bottom static: Lehra, Zira, Moonak, Guruharsahai.
- Same list appears with VIIRS fire counts → not an artefact of one sensor.
- Figure: 🛠 PD map (PD / borderline / Doaba cluster / ND highlighted on group map) + compact table from `outputs/pd/robust/robust_deviants.csv`.

## Part 5 — Status and next (2 slides)

### 14. Limitations (honest)
- Ploughing tested only on Walker 2019 (2 districts, 128 ploughed fields); partial burns under-counted (~half missed).
- Rice map regional bias (calibrated at district only); 5-yr rainfall; equal weights; 97 units.
- Planet quota: daily imagery only as a judge, not at tehsil scale.
- Framing: "with more resources (Planet quota, field labels), the same pipeline gives sharper results."

### 15. Next steps to 25 Nov
- **PD validation:** data quality at PDs (clear looks, verdict counts), cut 0.5 sensitivity, Doaba structural check, Dinanagar border status.
- **Underlying factors (Stage 3):** harvest-to-sowing turnaround already built (harvest ≈ 22–26 Oct; turnaround 14–22 days; SW harvests ~1 week later). Next: CHC/CRM machines, straw buyers (biomass plants), mandis, farm size, livestock, post-paddy crop, border proximity. Compare Abohar (+ borderline) vs NDs.
- **Impact assessment design** (final report): pilot in matched tehsils, satellite burn measure as outcome (before/after vs comparison), farmer survey.

## Backup slides
- B1. Difficulties table (D1–D20, condensed to the top 6).
- B2. Grouping sensitivity (✅ `fig_E_sensitivity.png`) and rice calibration (✅ `fig_F_rice_calibration.png`).
- B3. Full robust deviant table (old + strict rule).

---

## Decisions for Soham
1. **Format:** PowerPoint (.pptx) or a web slide deck (downloads as .pptx/PDF)?
2. **Slide 15:** include the harvest-turnaround result as an early Stage 3 result, or only as the plan?
3. **Talk length:** if the time limit is short (~10 min), merge 3+4, 6+7, 11+12 → 12 slides.
4. **Figures to make (🛠, ~1 short script):** VIIRS check scatter, burnt-share map, PD map. OK to write `Code/figures/make_pd_figures.py`?
