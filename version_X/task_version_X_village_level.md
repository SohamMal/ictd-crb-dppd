# Task: Version X, village-level DPPD (Stages 2–3)

## Objective
Exact question: *Which Punjab villages burn significantly less paddy stubble than villages with the same structural conditions, and do the online drivers explain why?* This repeats the main tehsil pipeline at village resolution as a separate version (folder `version_X/`). Soham (2026-11-10) asked Claude to take its own decisions and report back after driver identification.

## In plain words
Same recipe as the tehsil study, with smaller pieces. Villages are grouped by climate, zone, groundwater, soil and rice share. Each village's burning is read from satellite at 10 paddy spots a season. A village is a positive deviant if it burns far less than its look-alikes, season after season, and keeps that verdict when the data are resampled and the settings changed. Then the 8 online drivers are compared between those villages and their look-alikes. See `README.md` for the result tables.

## Approaches considered
| Choice | Selected | Rejected (why) |
|---|---|---|
| Burn measure | point sample, main-version RF detector (10 pts/village/season) | full-pixel server-side RF (time-series candidate logic hard to port, risk of Earth Engine time-outs); new detector (would break comparability) |
| Village scope | Central + South-west, rice ≥ 25 ha | Foothills (measure fails there); all villages (tiny-rice villages give noise) |
| Grouping | same 5 dims, Gower + average HAC, k = 3, then rice terciles | nesting villages inside the tehsil regions only (would not test whether the village view regroups Punjab); Ward/k-means (departs from the frozen method) |
| Bootstrap | Jeffreys-Beta then Binomial | plain binomial (zero-burn seasons never vary, so zero villages pass automatically) |
| Stage 3 | within-peer percentiles, within-tehsil sign test, cluster bootstrap, Holm | raw pooled correlations (confounded by region and spatial clustering) |

## Data / preprocessing
- Units: LGD village bridge (12,662 rows, 12,660 unique Census-2011 codes) joined to SHRUG PC11 polygons (all matched).
- Rice: recomputed from `clipped_2020.tif` / `clipped_2022.tif` on village polygons (PIL rasterisation; rasterio DLL blocked). Check: `clipped_2022.tif` equals the India-wide `chen_2022.tif` window at 100% of sampled pixels, and the two Chen years agree on 99.2% of pixels, so the near-identical village rice columns are real, not a stale copy. Calibrated with the main version's district factors.
- Structural: village rainfall, soil and groundwater masters (Data/), AESR polygons overlaid per village.
- Earth Engine: 95,942 points × 5 seasons (S2 bands 25 Aug–1 Dec); 28,782 points × 5 seasons NDVI 1 Sep–31 Jan. Both completed with only transient retries.

## Experiments and raw results
- k table (`outputs/grouping/k_table.csv`): k = 2: sil 0.353, ARI 1.00; **k = 3: 0.377, ARI 0.991 (p10 0.392)**; k = 4: 0.356, 0.950; k = 6: 0.371, 0.891. Dimension separation at k = 3: zone 0.377, rainfall 0.161, groundwater 0.095, rice 0.035, soil 0.021.
- Burn checks: village→tehsil ρ 0.967 / 0.964 / 0.966 / 0.943 / 0.976 (2020–24). Between-season ρ 0.43–0.70 (2024 is the weakest season, as in the main version). Rice ρ in groups 0.26–0.42, in peers 0.03–0.28.
- PD: 9,277 ranked villages. Static kept 299 (strict 256: 155 validated, 101 caveat; candidate 43). ND contrast 222. Temporal kept 213. Most drops are V1 bootstrap fails.
- Overlap with the main version: Abohar 41/80 villages PD, Dinanagar 36/208, Gurdaspur 27/347, Talwandi Sabo 6/57; Phagwara 5/110, Jalandhar-I 2/66, Banga 2/108, Adampur 0/149. Not tehsil PDs but rich in village PDs: Dudhan Sadhan 26/94, Kapurthala 41/243, Sardulgarh 12/69, Amritsar-II 9/101, Fazilka 10/143.
- Drivers: see README table. Within-tehsil, D1 turnaround is shorter for PDs (64% below the tehsil median, Holm p 5e-10; 248 PDs with normal harvest timing: −2.5 d, p 1e-5). D5 is weaker (p 0.02 → 0.006 on V5-pass PDs). Everything else n.s. RF out-of-tehsil R² 0.156.
- Blockers met: rasterio blocked (tifffile + PIL used); `clipped_2022` suspicion (cleared); a bug inverting the expected-side readout (fixed before reporting).

## Final implemented solution
`version_X/Code/vx_*.py`, run in the order of the README table. All numbers above regenerate from code.

## Log
### 2026-11-10 — Version X built through Stage 3 (Claude, autonomous) [P]
- Built the village base, peer grouping, burn measure, PD identification + validation, and drivers + comparison, all as above. Every decision is [P], awaiting Soham's review. The main version was not modified.
- Journey-worthy for the tracker (needs Soham's approval): Doaba tehsil PDs largely dissolve at village level; 180 village PDs sit outside the tehsil PDs; drivers explain little; the D1 sign is opposite to the hypothesis.
