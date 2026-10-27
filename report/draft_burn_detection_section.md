# DRAFT — Burn detection: telling burnt from ploughed fields (Methodology + Results)

> Draft section, 2026-10-27. Not yet merged into `report_draft.md`. Source of all numbers: `sub_journeys/2_Stage2_Determine_Positive_Deviants/2.1_Performance_Measurement/task_burn_detection.md` (entries 2026-10-26 / 27) and `task_burn_detection_basma.md` (W1). Scripts in `Code/planet/`.

## 1. Problem

Our Sentinel-2 burn detector (BAIS2 + Tasseled Cap Brightness, logistic boundary) finds burnt fields but cannot tell ash from freshly ploughed soil. On Walker et al.'s (2022) ground truth (Punjab 2019; 2,204 burnt and 223 ploughed-not-burnt fields), it flags **98%** of burnt fields and **81%** of ploughed fields in the 10 days after the event. This works directly against DPPD: tehsils whose farmers plough instead of burning (the likely positive deviants) would look like burners.

## 2. Routes tried and rejected

| Route | Result |
|---|---|
| Land surface temperature (Landsat, MODIS) | Pixels too coarse for fields; false alarms reduced but about half of ploughed fields still called burnt |
| Sentinel-1 radar roughness (Basma's filter) | 12-day revisit; on probably-ploughed fields the signal went the wrong way |
| Spectral thresholds / single-date classifiers | Char vs ploughed soil AUC 0.51–0.73; unstable across years |
| Walker-style cloud masking (cloud probability < 50%) | No effect: field values identical on clear looks |

**Key insight.** Fresh ash is near-black for only **2–3 days** and then fades toward the colour of ploughed soil. On Walker's fields, daily PlanetScope (3 m) separates burnt from ploughed fields well (AUC 0.96; at 90% of burns caught, 9% of ploughed fields called burnt). Sentinel-2 revisits only every 5 days, so it often sees faded ash.

## 3. Methodology: final pipeline

1. **Flag.** The existing BAIS2 + TCB detector scores every clear Sentinel-2 look (S2 L2A, relaxed SCL mask, field mean). A score above 0 marks a possible event (burnt or ploughed).
2. **Candidate.** Among flagged looks, the one with the **largest rise in score** over the previous clear look. Burning is sudden; crop drying and harvest are gradual.
3. **Before vs after features.** Candidate look vs the **single clear look just before it**: 9 bands (B2–B8, B11, B12) and 5 indices (NDVI, NBR, NBR2, BAIS2, TCB), as post values and post − pre changes.
4. **Check.** A random forest (500 trees, balanced classes) trained on **Walker's ground truth** (burnt vs ploughed-not-burnt) decides burnt / not burnt.
5. **Cut-off.** **0.79** (keeps 90% of Walker's burns) as the main setting; **0.5** as a sensitivity check.

**Role of Planet.** (i) An independent judge of the model in a new year and district (Jalandhar 2021), using an automatic rule (field brightness falls to ≤ 0.765 of its earlier level). (ii) We also showed that Planet-derived labels are good enough to train Sentinel-2 where no field survey exists.

**Validation design.** Walker: 5-fold cross-validation. Jalandhar: no retraining and no manual labels; two judges. (A) The Planet rule on the 95 fields CEEW saw unburnt on 29 Oct, followed to 13 Nov. (B) CEEW's field visit on 29 Oct: 262 burnt, 95 unburnt.

## 4. Results

### 4.1 Walker ground truth (2019, cross-validated)

| Method | Burns caught | Ploughed called burnt |
|---|---|---|
| Old BAIS2 + TCB (any look 0–10 d) | 98% | 81% |
| Daily Planet rule (cut-off keeping 90% of burns) | 90% | 9% |
| Sentinel-2 trained on Planet labels | 89% | 22% |
| Sentinel-2 trained on ground truth (same setup) | 89% | 16% |
| **Final model, cut-off 0.79** | **90%** | **18%** |
| Final model, cut-off 0.5 | 97.5% | 51% |

AUC of the final model: 0.938. Sentinel-2 trained on noisy Planet labels comes close to Sentinel-2 trained on ground truth (22% vs 16%).

### 4.2 Jalandhar 2021 (Walker-trained model, not retrained)

| Judge | Old detector | Final, cut-off 0.5 | Final, cut-off 0.8 |
|---|---|---|---|
| A Planet rule: burns kept | 63/63 | 51/63 | 37/63 |
| A Planet rule: not-burnt called burnt | 23/32 | 3/32 | 0/32 |
| B CEEW visit: burns kept | 257/262 | 145/262 | 89/262 |
| B CEEW visit: unburnt called burnt | 28/95 | 2/95 | 1/95 |

- Ranking burnt vs not-burnt fields (judge A): AUC 0.94 vs 0.89 for the old detector (0.98 vs 0.84 leaving out fields at the Planet window edge).
- CEEW completely burnt fields: 56/72 kept at cut-off 0.5; partially burnt: 89/190.

### 4.3 Development steps (Jalandhar, judge A, cut-off 0.5)

| Step | Burns kept | Not-burnt called burnt |
|---|---|---|
| "Before" = 20-day median, first flagged look | 36/63 | 2/32 |
| "Before" = last clear look | 47/63 | 3/32 |
| Candidate = largest score jump | 51/63 | 3/32 |
| + Jalandhar Planet labels in training (weight 1 / 10) | 52/63 / 55/63 | 3/32 / 5/32 |
| Label-free cut-offs: Walker balance 0.82 / Jalandhar Otsu 0.57 | 37/63 / 50/63 | 0/32 / 1/32 |

## 5. Main finding

The pipeline sharply reduces false alarms: in Jalandhar from 23/32 to 0–3/32, and on Walker's ploughed fields from 81% to 18%. The cost is missed burns, mostly partially burnt fields. At the strict cut-off it keeps 37/63 Planet-seen burns and 89/262 CEEW-burnt fields. For DPPD, an under-count of burns is less harmful to tehsil rankings than ploughing false alarms, **provided the under-count is similar across tehsils** (assumption, not tested).

## 6. Limitations

- **Ploughing validated on Walker only:** one season (2019), two districts, no field locations, event dates uncertain by days, 128 ploughed fields.
- **Small Jalandhar check:** 95 Planet-judged fields (32 not burnt), one Sentinel-2 tile, one season. Its not-burnt fields are mostly stubble, so it does not test ploughing.
- **Imperfect Planet judge:** at its fixed cut-off on Walker it misses about 5% of burns and calls about 21% of ploughed fields burnt.
- **Partial burns:** diluted in field averages; about half missed.
- **Gaps between clear Sentinel-2 looks** (e.g. 19 → 29 Oct 2021) let ash fade before it is seen.
- **No single cut-off** is good for both ploughing (Walker) and burn catch (Jalandhar).
- **Resources:** the Planet Education & Research quota counts at least 100 km² per scene (about 30 scenes a month), so daily Planet cannot cover tehsils directly. With more quota, Planet could label more places and years, or measure the demonstration tehsil directly.

## 7. Reproducibility

| Step | Script | Outputs |
|---|---|---|
| Planet rule on Walker | `Code/planet/walker_planet_test.py` | `outputs/planet/walker_planet_*.csv` |
| S2 trained on Planet labels (Walker) | `Code/planet/s2_from_planet_labels.py` | `outputs/planet/s2fromplanet_*.csv` |
| Jalandhar test (cloud mask, before window, candidate) | `Code/planet/jalandhar_walker_model_test.py --pre-looks 1 --candidate jump` | `outputs/planet/jalandhar_walker_*_pre1_jump.csv` |
| Retrain with Planet labels | `Code/planet/jalandhar_planet_retrain.py` | `outputs/planet/jalandhar_retrain_*.csv` |
| Cut-off tests | `Code/planet/jalandhar_cutoff.py` | `outputs/planet/jalandhar_cutoff_*.csv` |
| Old detector on Walker (W1) | `Code/burn_basma/walker_tilled_test.py` | `outputs/burn_basma/w1_*.csv` |

Walker data: Zenodo 11225292 (code + field series). CEEW ground truth: Zenodo (2020, 2021 field polygons). Seeds: 42 throughout.
