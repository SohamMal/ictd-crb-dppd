# Final presentation — outline (due 2026-11-25, 3:30 pm)

**Brief (Prof. mail, 2026-11-01):** final presentation, long session, given with the final report (which has an impact assessment section).
**Shape:** 18 main slides + backup. **Answer first**, method cut down (the class saw it at A3), Stage 3 and impact expanded (new since 6 Nov).
**Story:** *who burns less than their peers → why we trust that → why they burn less → what to do about it.*
**Sources:** every number is from `report/report_draft.md` (section given per slide). version_X is not used.
**Build:** extend the A3 style (`Code/figures/make_a3_deck.py` helpers) into `Code/figures/make_final_deck.py`.
**Figure status:** ✅ exists · 🛠 needs making (short script from existing CSVs) · ✍ drawn diagram · ♻ reuse an A3 slide.
**Timing:** minutes are for a ~20 min talk; see "If the slot is shorter" at the end.

---

## Opening (3 slides, ~2.5 min)

### 1. Title
- Finding Positive Deviants in Crop Residue Burning: a DPPD study of Punjab tehsils
- Soham Malvadkar · COL7761 · Supervisor Prof. Aaditeshwar Seth · Advisors Basma Albanna, Andreas Pawelke

### 2. The problem
- Every Oct–Nov, Punjab burns paddy straw to clear fields for wheat; a major seasonal source of pollution in the Indo-Gangetic Plain and Delhi NCR (§1).
- Burning continues despite CRM machine subsidies since 2018, custom hiring centres and short-duration varieties.
- Burning is uneven even between places that look alike → some places may already have a working answer.
- Measurement is breaking: VIIRS fire counts collapsed in 2024–25 as farmers time fires to dodge the satellite pass (§8.1).
- Figure: ✅ `fig_G_burn_map.png` (or a single striking number).

### 3. The question and the answer
- *Which of Punjab's 97 tehsils burn much less than structurally similar peers, and why?*
- **Answer up front:**
  - **Abohar** (South-west): the only strict PD, burnt share 0.34 vs group median 0.73.
  - **Doaba belt** (Central): Dinanagar, Phagwara, Jalandhar-I, Adampur (+ Gurdaspur, Banga with caveat) burn about half the Central median, as a region.
- Pipeline strip: Grouping ✔ · Burn measure ✔ · PD identification ✔ · PD validation ✔ · Underlying factors ✔ (desk study).
- Figure: ✅ `fig_J_pd_map.png`.

## Part A — Why the list can be trusted (4 slides, ~5 min; compressed from A3)

### 4. Fair peers
- Structural conditions only: rice share 2022 (calibrated), monsoon rainfall 2020–25, AESR zone, groundwater 2022, soil. No drivers, no burning data; frozen before burning was measured.
- Dimension-balanced Gower → average-linkage clustering → **Central 63 / South-west 18 / Foothills 15** (+ Dhar Kalan outlier).
- Stability on one line: silhouette 0.377, bootstrap ARI 0.890; the SW/Central border is the weak point (checked again in validation).
- Figure: ✅ `fig_A_group_map.png`. ♻ A3 slides 3–8 go to backup.

### 5. The measurement trap: burnt looks like ploughed
- Season-long Sentinel-2 burn index (BAIS2+TCB): catches 98% of burns but flags **81% of ploughed-not-burnt fields**.
- Why: ash is black only 2–3 days, then fades to soil colour; Sentinel-2 passes every 5 days.
- Figure: ♻ A3 slide 10 (Planet strip + ash-fading diagram); ✅ `outputs/planet/fig_planet_vs_s2.png`.

### 6. The detector
- 4 boxes: flag → candidate (largest jump) → before/after features → random forest (Walker ground truth, burnt if p ≥ 0.79).
- Walker 5-fold CV: burns caught 90%, ploughed called burnt **81% → 18%**, AUC 0.94.
- Independent Jalandhar 2021 test (not retrained): CEEW unburnt called burnt 28/95 → 1–2/95.
- Cost: partial burns under-counted; assumed similar across tehsils.
- Figure: ♻ A3 slide 12 diagram + old-vs-current table.

### 7. The tehsil measure holds up
- 100 cropland points per tehsil per season, 2020–24.
- Ranks match VIIRS fire counts **ρ 0.78–0.87**; year-to-year **ρ 0.82–0.91**; CREAMS 2022 district ρ 0.87.
- Weak spot: 2024 (late burns; VIIRS ρ 0.51) → every result is also checked on 2020–23.
- Figure: ✅ `fig_H_burn_vs_viirs.png`.

## Part B — Who the positive deviants are (3 slides, ~3.5 min)

### 8. The PD rule
- Static deviance: 2020–24 mean burnt share within the group. Temporal deviance (Basma): trend vs group trend.
- Strict rule: beyond the group's IQR fence (Q1 − 1.5 IQR, log scale) in **both** runs (2020–24 and 2020–23).
- Fences: Central 0.225 (median 0.61); South-west 0.454 (median 0.73). Foothills measured, not ranked.
- Figure: ✅ `fig_I_pd_fences.png`.

### 9. Validation: what survived
- Checks V1–V5: bootstrap, alternative settings (0.5 cut, offset, Plains grouping), looks, rice, timing (§3.6, Table 7).
- **Static list holds:** bootstrap ≥ 0.89 for all validated PDs (Banga 0.72 → caveat).
- **Temporal deviance does not, except Abohar:** Samana 0.40, Dirba 0.39 → dropped. Five seasons × 100 points is too noisy for a trend.
- Final: validated PDs Abohar, Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo; caveat Gurdaspur, Banga; contrast NDs Lehra, Zira, Moonak, Guruharsahai.
- Figure: 🛠 compact validation table (✔ / flag grid) from `outputs/pd/pd_validated.csv`.

### 10. The rice warning, and why the list survives it
- Every static PD except Talwandi Sabo has less rice than three-quarters of its group; burning rises with rice share inside groups (ρ 0.70 Central, 0.63 SW).
- Harvest-confirmed rescoring (V4b): only fields where a paddy harvest is seen. Abohar 0.43 → 0.45 (median 0.73); Dinanagar 0.22 → 0.25 (0.62).
- **PDs burn little on fields that really grew paddy.** The rice gradient is treated as structural and carried into Stage 3.
- Figure: 🛠 before/after bar (all points vs harvest-confirmed) for the PDs vs group medians.

## Part C — Why they burn less (4 slides, ~4.5 min; new core)

### 11. Driver triage
- 9 candidate drivers from public online data, tested three ways: within-group ρ, partial ρ (rice share held constant), PD/ND sides (Table 8).
- Three bins:
  - **Consistent:** urban area share (Central ρ −0.61, partial −0.30; PDs 7/8, NDs 4/4).
  - **Really rice share:** turnaround time, cultivators per ha (lose their link once rice is held constant).
  - **No consistent link:** straw buyers within 30 km, labour per cultivator, basmati share, livestock (weak data noted).
- Figure: 🛠 triage chart: ρ vs partial ρ per driver, coloured by bin.

### 12. Doaba: a region, not a town effect
- Fields within 2 km of a town burn 6–8 points less, but only 4% of fields are that close; beyond 2 km distance makes no difference.
- On fields > 5 km from any urban centre the PDs keep their low burning: Dinanagar 0.21 → 0.20, Phagwara 0.30 → 0.27, Jalandhar-I 0.31 → 0.32, Adampur 0.30 → 0.30.
- Read urban share as a **marker of the Doaba belt** (potato/vegetable rotations, off-farm and overseas income, dense markets), not "towns reduce burning".
- Figure: table above + ✅ crop of `fig_J_pd_map.png` on Doaba.

### 13. Abohar: one rural PD, several levers at once
- Percentile within South-west: biomass power plant inside the tehsil (local straw buyer); most farm labourers per cultivator in Punjab (1.61, 100th); most cattle + buffalo per cultivator (100th); highest early-second-crop share (100th); basmati-heavy district (94th); 13 km from Rajasthan.
- One tehsil → these cannot be separated. **A lead for fieldwork, not a finding.**
- Figure: 🛠 horizontal percentile bars for Abohar vs SW group.

### 14. Two surprises
- **Turnaround time and farm size** look like drivers but mostly restate the rice gradient → don't target on them without allowing for rice.
- **The border runs the "wrong" way in the South-west:** near the Rajasthan/Haryana border tehsils burn less (ρ +0.83; partial +0.75), opposite to Dipoppa & Gulzar. Likely the cotton belt, where paddy is newer and less dominant.
- Figure: none, or 🛠 small scatter of border distance vs burnt share (SW).

## Part D — So what (3 slides, ~4 min)

### 15. What NGOs and government can do with this
1. **Where to look:** Abohar and the Doaba tehsils first; heavy-burning NDs as comparison.
2. **What to test:** Abohar's three transferable levers: assured straw buyer, labour for manual handling, fodder demand. For Doaba: what farmers do with straw before an October potato/vegetable crop.
3. **How to target:** rank within peer groups and allow for rice share, otherwise you reward places that just grow less paddy.
4. **How to monitor:** a free field-level Sentinel-2 detector that farmers can't dodge by timing fires, rerun each December.
- Figure: none (4 cards).

### 16. Impact assessment proposal
- Theory of change: PD leads → **Phase 1** confirm in the field (1 season) → **Phase 2** pilot confirmed levers in matched non-PD villages → measure → scale.
- Phase 1: Abohar + 4 Doaba PDs, 4 NDs, 2 typical peers per group; ~6 villages per tehsil chosen by satellite burnt share; ~20 farmers per village; ground-truth photos for the detector.
- Phase 2: village unit, villages paired on baseline burning + rice share inside the same peer group, one randomly treated; stepped-wedge if no randomisation.
- Outcome: village burnt share from our detector (primary), survey with a **list experiment** (burning is illegal), take-up records, VIIRS cross-check.
- Sample size: 10-point drop, 80% power → **~30 villages per arm** (range 15–52), rounded to 35 pairs per lever; frame of 1,633 SW villages.
- Figure: ✍ theory-of-change / two-phase diagram.

### 17. Limitations, and what more resources buy
- No fieldwork: no practice confirmed on the ground.
- Stage 3 rests on 8 PDs and 4 NDs and public data of mixed years and resolutions; no district CRM machine data online.
- Ploughing tested only on Walker 2019; partial burns under-counted; 2024 doubtful; Foothills not ranked; equal grouping weights.
- With field access, more PlanetScope quota and CRM data, the same pipeline gives firmer answers.

### 18. Takeaways
1. Compare like with like, and allow for rice share: low burning is not just less paddy.
2. Separating burning from ploughing is essential, and possible with free Sentinel-2 imagery.
3. Abohar and the Doaba belt are where to look; their levers are leads to test, not proven causes.
- Thanks; repo is reproducible (`Code/`).

---

## Backup slides
- B1. Data sources table (report Table 1).
- B2. Grouping detail: ♻ A3 slides 4–7 (data fixes, Gower worked example, dendrogram `fig_B`, choosing k `fig_D`, sensitivity `fig_E`).
- B3. Difficulties table D1–D20 (report Table 9).
- B4. Detector cut-off 0.79 vs 0.5 (tehsil ranks ρ 0.84–0.98: changes level, not order).
- B5. Full robust deviant table (report Table 6) + validation table (Table 7).
- B6. Full driver table (report Table 8).
- B7. Sample size Table 10 + sensitivity rows (§8.7).
- B8. Survey modules (§8.6) + logframe (§8.8).

## If the slot is shorter (~15 min)
- Merge 5–7 into 2 slides (trap + detector-with-validation).
- Merge 13–14 into 1 slide.
- Move 10 to backup and keep its one-line conclusion on slide 9.

---

## Decisions for Soham
1. **Slot length:** how many minutes? Decides 18 vs ~14 main slides.
2. **Format:** PowerPoint via `make_final_deck.py` (same style as A3), as proposed?
3. **Figures to make (🛠, one script `Code/figures/make_final_figures.py`):** validation grid, V4b before/after bars, driver triage chart, Abohar percentile bars, optional SW border scatter. OK?
4. **Diagram (✍):** two-phase theory of change for slide 16.
