# Final presentation — outline, version 2 (due 2026-11-25, 3:30 pm)

**Status:** proposed (Soham, 2026-11-22). Does not replace `final_deck_outline.md` (27-slide version).
**Slot:** 15 min. **Shape:** 25 main slides + backup.
**Story:** *problem → where we were at the midterm (17 Sep) → what we did since (one page) → how each piece works → the PDs, why, and what to do → impact assessment.*
**Sources:** every number from `report/report_draft.md` and the outputs it cites. version_X is not used.

## Rules for this version (Soham 2026-11-22)
- Show the technical methodology of what worked: not too deep, not too shallow, enough to tell what we did.
- "Tried & failed" is quick (one line per attempt); the focus is on what worked.
- Clustering (slides 7–9) and the detector (slides 12–13) are full explanation slides.
- No mention of ChatGPT.
- Design rules from version 1 still apply: one message per slide, title as a sentence, at most 3–4 bullets, real visuals only, fixed colours, every image captioned.

## Slides

| # | Section | Title message | Content / visual | Source |
|---|---|---|---|---|
| **Problem** | | | | |
| 1 | — | Title | Sentinel-2, Lehra, 26 Oct 2022 | `raw/s2_lehra.png` |
| 2 | Problem | Punjab burns over half its paddy straw, in a few weeks between paddy and wheat | Burn map 2020–24 (52–64%) + season strip: burning and ploughing share one window | `fig_G`, `f01`, §1 |
| 3 | Problem | Fire counts fail, so: which tehsils burn less than places like them? | VIIRS vs our measure + DPPD pipeline strip | `f02`, §3.1, §8.1 |
| **Midterm (17 Sep)** | | | | |
| 4 | Midterm | Burn proxy chosen at the midterm | BAIS2+TCB vs NBR on 380 fields: 95.5% vs 81.3% accuracy; 5 vs 47 missed burns | 17 Sep deck, slides 9–10 |
| 5 | Midterm | Grouping designed at the midterm | 5 structural factors; drivers (CRM, mandis) kept out; tehsil unit; 2011 → current boundary bridge | 17 Sep deck, slides 12–15 |
| **Since the midterm** | | | | |
| 6 | Summary | Six things since the midterm | 1 peer groups · 2 ploughing-proof detector · 3 tehsil measure · 4 PDs · 5 validation · 6 why and what to do; final PD map beside | `f03` |
| **A. Peer groups** | | | | |
| 7 | Groups | How alike are two tehsils? | Each of 5 variables gives a 0–1 difference (numbers scaled by range; zones and soil compared as shares); each dimension weighs 1/5 (dimension-balanced Gower). Worked example: Phagwara–Adampur 0.24 vs Phagwara–Abohar 0.51 | `f18_gower_example.json`, §3.3 |
| 8 | Groups | Building groups by merging | 5-tehsil toy example, step by step: each starts alone → merge the two closest (group distance = average of all pairs) → repeat. Then the real 97-tehsil dendrogram with the cut line | **new figure**; `fig_B`, §3.3 |
| 9 | Groups | Where to cut, and can we trust it? | Silhouette (closer to own group than the next?) 0.377; bootstrap 300 × 80% resamples, ARI 0.890; weights ±15%. 3-region map: Central 63 / South-west 18 / Foothills 15 | `fig_D`, `fig_A`, §3.3, §4.1 |
| **B. Burn detector** | | | | |
| 10 | Detector | Burnt and ploughed fields look alike | PlanetScope strips: burnt vs ploughed; midterm detector called 81% of ploughed fields burnt | `f05`, §4.2 |
| 11 | Detector | Tried & failed | One line each: tighter season window; heat (Landsat LST, MODIS); radar filter (dropped 33% of real burns) | **new slide**; §5 |
| 12 | Detector | Planet as the judge | Planet images daily; Sentinel-2 saw this field on 2 of 10 days. On ground-known fields Planet separates burnt from ploughed (AUC 0.96), so it can teach Sentinel-2 | `f06`, §3.4 |
| 13 | Detector | How the detector decides | (1) score each clear Sentinel-2 date with BAIS2+TCB; (2) largest jump = candidate burn date; (3) compare with last clear look before; (4) random forest trained on ground-truth fields → probability, ≥ 0.79 = burnt. Two Lehra points: p = 1.00 / 0.18 | `f19`, §3.4 |
| 14 | Detector | Result | Ploughing false alarms 81% → 18%, 90% of burns kept. Planet check, Jalandhar 2021: 23/32 → 0–3/32 | `f07`, §4.2 |
| **C. Fields → tehsils** | | | | |
| 15 | Tehsils | Method | 100 fixed rice points per tehsil; 15 Sep–30 Nov; 2019–24; burnt share = burnt points / 100. Side box: VIIRS backup only (collapses 2024–25), Foothills measured but excluded, 2024 flagged (late burns) | `f08`, §3.4 |
| 16 | Tehsils | Result | Ranks match VIIRS (ρ 0.78–0.87), stable year to year (0.82–0.91) | `fig_H`, `f09`, §4.3.1 |
| **D. PD identification** | | | | |
| 17 | PDs | A PD lies beyond its own group's fence | Log scale; IQR fence within group; Theil–Sen trend for fast reducers; robust = flagged in 2020–24 and 2020–23. Abohar vs South-west median as the example | `fig_I`, `f10`, §3.5 |
| **E. Validation** | | | | |
| 18 | Validation | Six checks, fixed in advance | V1–V6 + V4b; validation grid (Samana, Dirba dropped); PDs stay low on real paddy (rice-share scatter) | `f11`, `f12`, §3.6, §4.3.3 |
| **Why they burn less** | | | | |
| 19 | Why | How we looked for factors | Nine public drivers (online data only); three tests: group profiles, ρ, partial ρ with rice share held constant | §3.7 |
| 20 | Why | Doaba is a regional trait, not a town effect | Urban share ρ −0.61 (partial −0.30); PDs burn as little on fields > 5 km from towns | `f13`, `f14`, §4.4 |
| 21 | Why | Abohar's profile | Straw buyer in the tehsil, most labourers per cultivator in Punjab, most livestock in group, early second crop | `f15`, §4.4 |
| **What to do** | | | | |
| 22 | So what | The PDs, and what to do with them | PDs (Abohar; Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo) vs NDs (Lehra, Zira, Moonak, Guruharsahai). Test Abohar's levers (straw buyer, labour, fodder) in South-west; Doaba = fieldwork question; target by peers + rice share; monitor with Sentinel-2 (evasion-resistant) | §8.1 |
| **Impact assessment** | | | | |
| 23 | Impact | Theory of change | PD leads → Phase 1 confirm in field → Phase 2 pilot → measure → scale; 4 assumptions and where each is tested | **new figure**; §8.2 |
| 24 | Impact | Phase 1 and Phase 2 design, and sample size | Phase 1: one season, PD/ND/typical tehsils, survey + focus groups + ground-truth photos. Phase 2: villages in non-PD tehsils of the same peer group, paired on baseline + rice share, randomised. Outcome: satellite burnt share + list experiment. 30 villages per arm for a 10-point drop (35 pairs per lever) | **new figure**; `f16`, §8.3–8.7 |
| **Close** | | | | |
| 25 | Close | Limits, and three takeaways | Ground-truth coverage map | `f17`, §6–7 |

## Backup
B1 data sources · B2 grouping detail (`fig_B`, `fig_D`, `fig_E`) · B3 detector cut-off 0.79 vs 0.5 · B4 full driver table · B5 survey modules + logframe.

## New work needed
- Slide 8: toy 5-tehsil merging figure.
- Slide 11: tried-and-failed slide (text).
- Slides 23–24: theory-of-change and pilot-design figures.
- All other slides reuse existing figures and content.
