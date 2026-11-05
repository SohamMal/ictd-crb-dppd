# A3 interim deck — outline (due 2026-11-06)

**Brief from Prof. (mail, 2026-11-01):** problem statement, methodology, implementation, results. Core implementation should be done; we are in the results phase.
**Shape:** 25 main slides + 4 backup. The class knows DPPD, so no method theory. The deck shows **what we did so far, step by step**: grouping → measuring burning (the full journey to the current detector) → positive deviants → next.
**Figure status:** ✅ exists · 🛠 needs making (short script from existing CSVs) · ✍ drawn diagram.

---

### 1. Title
- Finding Positive Deviants in Crop Residue Burning: a DPPD study of Punjab tehsils
- Soham Malvadkar · COL7761 · Supervisor Prof. Aaditeshwar Seth · Advisors Basma Albanna, Andreas Pawelke

### 2. Recap and where we are
- Question: *which of Punjab's 97 tehsils burn much less than structurally similar peers, and why?*
- Pipeline strip: Grouping ✔ · Burn measurement ✔ · PD identification ✔ · PD validation ◐ · Underlying factors ◐.

## Part 1 — Homogeneous grouping (7 slides)

### 3. Grouping variables
- Rule: structural conditions only; no drivers (machines, mandis), no burning data; frozen **before** burning was measured.
- Table of 5 dimensions: calibrated rice share 2022, monsoon rainfall 2020–25, AESR zone shares, groundwater extraction 2022, soil (8 descriptors), each with "why it matters for burning".

### 4. Data problems we fixed on the way
- Chen rice map biased by region (Fazilka ×1.71 over, central ×0.76–0.93 under) → calibrated to official district rice area.
- Satellite cropping intensity: ρ 0.18 vs official → dropped (moves only 2 tehsils).
- Slope data defective (identical values across tehsils) → terrain replaced by AESR zones.
- 2011 vs current boundaries → village/tehsil crosswalks.
- Figure: ✅ `outputs/figures/fig_F_rice_calibration.png`.

### 5. Distance between tehsils
- Mixed numbers + categories → Gower distance (each difference scaled 0–1).
- **Dimension-balanced:** average columns within a dimension first, then 5 dimensions with equal weight (soil's 8 columns get one vote, not 8).
- Outlier Dhar Kalan excluded from the ranges.
- Figure: ✍ small worked example (two tehsils, per-dimension scores → one distance).

### 6. Dendrogram
- Average-linkage hierarchical clustering: merge the two closest groups, repeat; the tree shows every possible cut.
- Mark the 3-group and 2-group cut lines; Dhar Kalan joins last.
- Figure: ✅ `outputs/figures/fig_B_dendrogram.png` (full slide).

### 7. Choosing the number of groups
- Silhouette per k, groups < 5 tehsils set aside, bootstrap ARI per k.
- k = 3: silhouette 0.377, ARI 0.890. k = 4–5 give the same 3 usable groups; k = 6 splits Central, ARI 0.71.
- Figure: ✅ `outputs/figures/fig_D_choosing_k.png`.

### 8. Is it stable? Bootstrap + sensitivity
- 300 resamples of 80%: group survival Central 100%, Foothills 100%, SW 93.7%; 3 borderline tehsils (Firozpur, Faridkot, Dinanagar); consensus placement.
- Weights ±15%, drop each dimension: 10/12 changes keep ARI ≥ 0.83. SW/Central border is the weak point → PDs must also hold under Plains/Foothills (ARI 0.981).
- Figure: ✅ `outputs/figures/fig_E_sensitivity.png`.

### 9. Final groups
- **Central 63 / South-west 18 / Foothills 15 + Dhar Kalan.** No location given, yet groups are connected belts (central plains, Malwa SW, Kandi foothills).
- Figure: ✅ `outputs/figures/fig_A_group_map.png` + ✅ `fig_C_group_profiles.png` (or a medians table).

## Part 2 — Measuring burning: the journey to the current method (9 slides)

### 10. What we need to measure
- Per tehsil, per season (2020–24): share of paddy fields burnt. Season 15 Sep–30 Nov (ISRO protocol used by CAQM).
- Why not fire counts (VIIRS): ~3.7× fewer detections; farmers burn after the satellite pass (collapse in 2024–25). Kept as a cross-check.

### 11. First detector: burn index on Sentinel-2
- BAIS2 (red-edge burn index) + Tasseled Cap Brightness, trained on CEEW labelled fields (438): **95.5% accuracy, 98% recall**; NBR only 81%.
- Fixes on the way: simplified BAIS2 formula failed → full formula; cloud mask threw away fresh ash (3/54 fields kept) → widened mask (436/438).

### 12. The problem: burnt looks like ploughed
- Over a whole season it flags almost everything: 94.6% of random cropland points, 92% of fields CEEW saw unburnt.
- Char vs freshly ploughed soil: same Sentinel-2 colour (AUC 0.51). On Walker ground truth: **98% of burns caught, but 81% of ploughed-not-burnt fields flagged.**
- Why: ash is black only 2–3 days, then fades to soil colour; Sentinel-2 passes every 5 days.
- Figure: ✅ Planet strip from `outputs/planet/strips_v2_jalandhar_2021/` (a field going black then fading).

### 13. What we tried that did not work
- **Heat (Landsat / MODIS land surface temperature):** ash is not hotter than soil; MODIS heat peak only helps with timing. Heat-peak window cut over-flagging 95% → 56%, but tehsil ranks barely matched fire counts (ρ 0.10–0.27).
- **Radar roughness (Sentinel-1; Basma's suggestion):** 12-day revisit, wrong direction on ploughed fields → documented negative result.
- **Sharper index rules** (jump, NBR2, peak size): no gain on the CIMMYT survey.

### 14. The idea that worked: look at the right moment, learn from ground truth
- Daily PlanetScope separates ash from soil (AUC 0.96) because it sees the 2–3 dark days.
- Walker et al. ground truth: 2,204 burnt + 223 ploughed-not-burnt fields with Sentinel-2 series → train a model on what a real burn looks like **at the change**.

### 15. Current detector: step by step
1. **Flag:** BAIS2+TCB score > 0 on any clear look → possible event (burnt or ploughed).
2. **Candidate:** the flagged look with the **largest jump** over the previous clear look (burning is sudden, drying and harvest are gradual).
3. **Before/after features:** candidate vs the one clear look before it: bands B2–B12, NDVI, NBR, NBR2, BAIS2, TCB (after values + changes).
4. **Decide:** random forest (500 trees) trained on Walker burnt vs ploughed → burnt if probability ≥ 0.79.
- Figure: ✍ 4-box diagram + 🛠 one field's score over the season with the candidate look marked.

### 16. How good is it?
- Walker 5-fold CV: burns caught **90%**, ploughed called burnt **81% → 18%**, AUC 0.94.
- Independent test, Jalandhar 2021, not retrained: daily-Planet judge: not-burnt called burnt 23/32 → 0–3/32; CEEW field visit: unburnt called burnt 28/95 → 1–2/95.
- Cost: misses burns, mostly partial burns. Fine for DPPD *if the miss rate is similar across tehsils* (stated assumption).
- Figure: compact Table 4/5 (old vs current detector).

### 17. From fields to tehsils
- 100 cropland points per tehsil × 97 tehsils × 6 seasons (9,700 points/season; ≥ 97% get a verdict). Tehsil value = burnt share of points.
- Figure: 🛠 map of points over one tehsil, or ✍ points → tehsil diagram.

### 18. Does the tehsil measure hold up?
- Ranks match VIIRS fire counts **ρ 0.78–0.87** (2019–23); old heat-peak table only 0.10–0.27.
- Year-to-year stability **ρ 0.82–0.91** → lasting local behaviour.
- Official CREAMS 2022 (till 24 Oct): district ρ 0.87; state 7.8% vs 9.9%.
- Weak spots: 2024 (72% of burns seen after 15 Nov; VIIRS ρ 0.51), 2019 level, 2020 district order.
- Figure: 🛠 scatter: our burnt share vs VIIRS fires per 1,000 ha rice.

## Part 3 — Positive deviants (4 slides)

### 19. Who burns how much
- Area-weighted burnt %, 2020–23: Central ≈ 52–67%, South-west ≈ 60–70%, Foothills ≈ 20–27%.
- Within-group spread is large (Central 0.25 → 0.81) → room for deviance.
- Figure: 🛠 tehsil map of mean burnt share 2020–24.

### 20. Two kinds of deviance
- **Static:** mean burnt share 2020–24, compared within the group.
- **Temporal (Basma):** trend of burning per year vs the group's trend; compares each tehsil with its own past.
- Foothills measured but not ranked (15 tehsils, weaker validation) → 81 tehsils ranked.
- Figure: 🛠 one example: tehsil vs group trend line.

### 21. The PD rule
- Strict: beyond the group's IQR fence (Q1 − 1.5 IQR, log scale) in **both** runs (2020–24 and 2020–23, because 2024 is suspect).
- Broader list: old "bottom 10%" rule shown alongside.
- Fences: Central static 0.225 (median 0.61); SW 0.454 (median 0.73).
- Figure: 🛠 box plot per group with fences and flagged tehsils.

### 22. Positive deviants found
- **Abohar (SW): the only strict PD.** Burnt share 0.34 vs group median 0.73; also the fastest reducer (−11%/yr vs group).
- **Borderline:** Dinanagar (static), Samana (temporal).
- **Doaba low-burning cluster** (Gurdaspur, Phagwara, Adampur, Jalandhar-I, Banga): ~half the group median but low together → likely structural (e.g. potato/vegetable rotation), a question, not PDs.
- Negative deviants: Malout (borderline, rising fastest); lowest static: Lehra, Zira, Moonak, Guruharsahai.
- Same list with VIIRS fire counts → not an artefact of one sensor.
- Figure: 🛠 PD map + compact table from `outputs/pd/robust/robust_deviants.csv`.

## Part 4 — Status and next (3 slides)

### 23. Underlying factors: started
- Harvest-to-sowing turnaround from Sentinel-2 greenness, checked against CIMMYT (district ρ 0.80 harvest, 0.77–0.93 sowing).
- Harvest ≈ 22–26 Oct; re-sown 14–22 days later; SW harvests ~1 week later than Central.
- Planned drivers: CHC/CRM machines, straw buyers (biomass plants), mandis, farm size, livestock, post-paddy crop, border proximity. Compare Abohar (+ borderline) vs NDs.

### 24. Limitations
- Ploughing tested only on Walker 2019 (2 districts, 128 ploughed fields); partial burns under-counted (~half missed).
- Rice map biased within districts; 5-yr rainfall; equal weights; 97 units.
- Planet quota: daily imagery only as a judge, not at tehsil scale.
- "With more resources (Planet quota, field labels), the same pipeline gives sharper results."

### 25. Next steps to 25 Nov
- PD validation: data quality at PDs, cut 0.5 sensitivity, Doaba structural check, Dinanagar border status.
- Stage 3 drivers (slide 23) → what Abohar does differently.
- Impact assessment design: pilot in matched tehsils, satellite burn measure as outcome (before/after vs comparison), farmer survey.

## Backup slides
- B1. Data sources table (compact Table 1).
- B2. Difficulties table (D1–D20).
- B3. Full robust deviant table (old + strict rule).
- B4. Detector cut-off 0.79 vs 0.5 (tehsil ranks ρ 0.84–0.98: the cut changes the level, not the order).

---

## Decisions for Soham
1. **Format:** PowerPoint (.pptx) or a web slide deck (downloads as .pptx/PDF)?
2. **Talk length:** 25 slides fits ~20 min. If the slot is shorter, merge 5+6, 10+11, 13+14, 20+21.
3. **Figures to make (🛠, one script):** field score timeline, VIIRS scatter, burnt-share map, temporal example, group box plot, PD map. OK to write `Code/figures/make_pd_figures.py`?
