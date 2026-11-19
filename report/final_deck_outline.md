# Final presentation — outline (due 2026-11-25, 3:30 pm)

**Brief (Prof. mail, 2026-11-01):** final presentation, long session, given with the final report (with impact assessment section).
**Slot:** 15 min (confirmed by Soham 2026-11-19). **Shape:** 27 main slides (results ~25 s, method ~40 s each) + 8 backup.
**Story:** *answer first → how we did it (method) → who the deviants are → why they burn less → what to do.*
Methodology added 2026-11-20 at Soham's request: grouping, detector, PD rule, validation, Stage 3 design.
**Sources:** every number from `report/report_draft.md` (section per slide) and the outputs it cites. version_X is not used.
**Build:** `python Code/figures/fetch_final_gee.py` (once, Earth Engine) → `python Code/figures/make_final_figures.py` (+ `methods`) → `python Code/figures/make_final_deck.py` → `report/final_deck.pptx` (copy in `0. Material/Presentations/`). The pptx and Planet-derived figures are not in git (Planet licence).

## Design rules (Soham 2026-11-19: clean, clear, easy to follow, real illustrations)
- One message per slide; the title states it as a sentence, on one line.
- At most 3–4 short bullets; the visual takes most of the slide.
- Real visuals only: our maps/charts from our data, real satellite images (PlanetScope, Sentinel-2). No stock icons or clip-art.
- Fixed colours: PD green, ND red, burnt = ember; peer groups keep the A3 colours (Central blue, South-west orange, Foothills teal).
- Every image captioned with source and date.
- Field-fire photo on slide 2: not used (download not approved).

## Slides

| # | Title message | Main visual | Source |
|---|---|---|---|
| **Opening** | | | |
| 1 | Title | Sentinel-2, Lehra, 26 Oct 2022 | `raw/s2_lehra.png` |
| 2 | Punjab burns over half its paddy straw every autumn | Burn map 2020–24, 52–64% | `fig_G`, §1 |
| 3 | From paddy to wheat in a few weeks | One point's Sentinel-2 season, 6 dates | `f01` |
| 4 | Fire counts are no longer a reliable way to measure burning | VIIRS fires 2019–25 vs our measure | `f02`, §8.1 |
| 5 | Abohar and a Doaba belt burn far less than places like them | Final PD map (validated labels) | `f03`, §4.3.3 |
| **Method overview** | | | |
| 6 | How we did it: the DPPD pipeline, step by step | 5-step cards + hard rules | §3.1 |
| **A. Fair peers** | | | |
| 7 | Peers are built only from conditions a tehsil cannot change | 5 grouping-variable maps | `f04`, §3.2 |
| 8 | Step 1: how alike are two tehsils? (dimension-balanced Gower) | Worked example: Phagwara–Adampur 0.24, Phagwara–Abohar 0.51 | `f18_gower_example.json`, §3.3 |
| 9 | Step 2: merge the closest tehsils, then choose where to cut | Dendrogram + choosing k; silhouette 0.377, ARI 0.890 | `fig_B`, `fig_D`, §3.3 |
| 10 | Three peer regions emerge, though no location was given | Group map + medians table | `fig_A`, §4.1 |
| **A. Measuring burning** | | | |
| 11 | Burnt and ploughed fields soon look alike | PlanetScope strips: burnt vs ploughed field | `f05`, §3.4 |
| 12 | Planet sees every day; Sentinel-2 saw this field on 2 of 10 | One burnt field, 10 Planet days, Sentinel-2 passes framed | `f06` |
| 13 | Our detector: flag, pick the sudden change, let a forest decide | Two real Lehra points (p = 1.00 burnt / 0.18 not) + 4 steps | `f19`, §3.4 |
| 14 | How good is it? Ploughing false alarms fall from 81% to 18% | Before/after bars; Jalandhar 28/95 → 1–2/95 | `f07`, §4.2 |
| 15 | From fields to tehsils: 100 points per tehsil | Rice-pixel points over Phagwara (19%) and Lehra (73%) | `f08`, §3.4 |
| 16 | The tehsil measure matches fire counts and is stable | VIIRS scatter + yearly maps; ρ 0.78–0.87, 0.82–0.91 | `fig_H`, `f09`, §4.3.1 |
| **B. Positive deviants** | | | |
| 17 | A positive deviant lies beyond its own group's fence | Fences plot + rules (log scale, IQR fence, Theil–Sen, strict) | `fig_I`, §3.5 |
| 18 | Abohar burns far less than its group in every season | Abohar vs South-west median and IQR band | `f10` |
| 19 | Before trusting a PD: six checks on the data, fixed in advance | V1–V5 + V4b table, labelling rule | §3.6 |
| 20 | Low burners survive every check; fast reducers do not | ✔/!/✘ validation grid | `f11`, Table 7 |
| 21 | Not just less rice: PDs stay low on real paddy fields | Burnt share vs rice share scatter | `f12`, §4.3.3 |
| **C. Why they burn less** | | | |
| 22 | Stage 3: nine public drivers, tested three ways | Drivers table + profiles / ρ / partial ρ | §3.7 |
| 23 | Only urban surroundings line up; others restate rice | Driver dumbbell chart (ρ vs partial ρ) | `f13`, Table 8 |
| 24 | Doaba burns little as a region, not near towns | All fields vs fields > 5 km from towns | `f14`, §4.4 |
| 25 | Abohar: straw buyer, labour, livestock, early second crop | Percentile bars | `f15`, §4.4 |
| **D. So what** | | | |
| 26 | What to do, and how we would test it | 4 action cards + two-phase pilot + sample-size chart | `f16`, §8 |
| 27 | Limits, and three takeaways | Ground-truth coverage map | `f17`, §6–7 |

## Backup
B1 data sources · B2 grouping detail (`fig_B`, `fig_D`, `fig_E`) · B3 detector cut-off 0.79 vs 0.5 · B4 robust deviants + validation table · B5 full driver table · B6 pilot sample size · B7 survey modules + logframe · B8 landscapes from space (Sentinel-2: Phagwara, Lehra, Abohar, Guruharsahai; moved from main deck 2026-11-20).

## If it runs long
Speak over, rather than show: slide 3 (paddy to wheat), slide 18 (Abohar line chart), slide 12 (Planet vs Sentinel-2).

---
*Earlier drafts (18 → 15 → 22 slides) were superseded on 2026-11-19; methodology slides added 2026-11-20.*
