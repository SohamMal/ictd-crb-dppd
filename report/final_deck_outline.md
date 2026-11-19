# Final presentation — outline (due 2026-11-25, 3:30 pm)

**Brief (Prof. mail, 2026-11-01):** final presentation, long session, given with the final report (with impact assessment section).
**Slot:** 15 min (confirmed by Soham 2026-11-19). **Shape:** 22 main slides, mostly visual (20–45 s each) + backup.
**Story:** *who burns less than their peers → why we trust that → why they burn less → what to do about it.* Answer first.
**Sources:** every number from `report/report_draft.md` (section per slide) and the outputs it cites. version_X is not used.
**Build:** `python Code/figures/make_final_figures.py` then `python Code/figures/make_final_deck.py` → `report/final_deck.pptx`.

## Design rules (Soham 2026-11-19: clean, clear, easy to follow, more real illustrations)
- One message per slide; the title states it as a sentence.
- At most 3 short bullets; the visual takes ≥ 60% of the slide.
- Real visuals only: our maps/charts from our data, real satellite images (PlanetScope, Sentinel-2). No stock icons or clip-art.
- Fixed colours: PD green, ND red, burnt = ember; peer groups keep the A3 colours (Central blue, South-west orange, Foothills teal).
- Big-number callouts for key results. Every image captioned with source and date.
- Field-fire photo on slide 2: not used (download not approved); slide 2 uses our own burn map.

## Slides (≈ 15:00)

| # | Title message | Main visual | Source | ~s |
|---|---|---|---|---|
| **Opening** | | | | **1:45** |
| 1 | Title | Real PlanetScope chip of burnt fields | `outputs/planet/chips_jalandhar_2021_2021-10-29.png` | 15 |
| 2 | Punjab burns most of its paddy every Oct–Nov, despite subsidies | Burn map 2020–24 + big number | `fig_G` | 30 |
| 3 | Harvest to wheat in ~3 weeks: the clock farmers face | One field's real Sentinel-2 season (images + greenness line) | `outputs/burn_labelling/img/` | 30 |
| 4 | Fire counts are no longer a reliable measure | VIIRS fires per season, Punjab | `outputs/pd/viirs` / `outputs/burn_fire` | 30 |
| 5 | Answer: Abohar and a Doaba belt burn far less than their peers | Final PD map (validated labels) | `outputs/pd/pd_validated.csv` | 30 |
| **A. Why the list can be trusted** | | | | **4:15** |
| 6 | Peers are built only from structural conditions | 5 small maps of the grouping variables | grouping master | 40 |
| 7 | Three peer regions emerge, with no location given | Group map | `fig_A` | 30 |
| 8 | Burnt fields look like ploughed fields | PlanetScope day-by-day strip of one field | `outputs/planet/strips_v2_jalandhar_2021/` | 45 |
| 9 | Ash fades before Sentinel-2 comes back | Real pass dates, Planet vs Sentinel-2, ash window shaded | `outputs/planet/catalogue_days.csv` | 40 |
| 10 | Our detector cuts ploughing false alarms from 81% to 18% | 4-step flow + before/after bar | §4.2 | 45 |
| 11 | From fields to tehsils: 100 points per tehsil | Points over one tehsil, burnt / not | `outputs/burn_tehsil_rf` | 30 |
| 12 | The tehsil measure agrees with fire counts and is stable | VIIRS scatter + 5 yearly maps | `fig_H`, burn_tehsil_rf | 45 |
| **B. Who** | | | | **2:30** |
| 13 | A PD lies beyond its group's fence | Fences plot | `fig_I` | 40 |
| 14 | Abohar burns about half its group, every season | Abohar vs SW median by season | burn_tehsil_rf | 35 |
| 15 | Static PDs survive validation; trend-based ones do not | ✔/✗ validation grid | `outputs/pd/pd_validated.csv` | 40 |
| 16 | Not just less rice: PDs burn little on real paddy fields | Burnt share vs rice share scatter, PDs labelled | grouping + burn CSVs | 35 |
| **C. Why** | | | | **3:00** |
| 17 | Only urban share is consistent; others restate rice | Driver dot chart (ρ vs partial ρ) | `outputs/predictors` | 45 |
| 18 | Doaba is low-burning as a region, not near towns | Bars: all fields vs > 5 km from towns | §4.4 | 40 |
| 19 | What the landscapes look like | Sentinel-2 true colour: Doaba PD vs heavy-burning ND | GEE export | 30 |
| 20 | Abohar: straw buyer, labour, livestock, early second crop | Percentile bars | `outputs/predictors` | 45 |
| **D. So what** | | | | **3:30** |
| 21 | What to do, and how we would test it | 4 action cards + two-phase pilot flow + sample-size chart | §8 | 90 |
| 22 | Limits and takeaways | Ground-truth coverage map + 3 takeaways | label CSVs | 60 |

## Backup
B1 data sources · B2 grouping detail (`fig_B`, `fig_D`, `fig_E`) · B3 difficulties (Table 9, short) · B4 detector cut-off 0.79 vs 0.5 · B5 full deviant + validation tables · B6 full driver table · B7 sample size Table 10 · B8 survey modules + logframe · B9 two surprises (turnaround/farm size = rice; border runs opposite).

---
*Earlier drafts of this outline (18 → 15 → 22 slides) were superseded on 2026-11-19 after the slot was confirmed and more visuals were requested.*
