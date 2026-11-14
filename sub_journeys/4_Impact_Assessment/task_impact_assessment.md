# Task: Impact assessment design (final report §8)

**Objective.** Prof's 2026-11-01 mail: final report (due 2026-11-25) = paper-quality §1–§7 + a separate impact assessment section (proposed methodology, survey questions, recommended formats) that a partner could use as a funding proposal.

### 2026-11-15 — Design proposed and §8 drafted
**Plain:** Designed a two-phase plan: first check the PD leads in the field, then pilot the Abohar levers (straw buyer, labour, fodder) in matched non-PD villages and measure the change with our satellite burn measure plus a farmer survey.
**Technical:** Draft in `report/draft_impact_section.md` (status: proposed, not merged). Phase 1 = PD/ND/typical-peer tehsils, ~6 villages × ~20 farmers, FGDs, KIIs, ground-truth photos at Sentinel-2 points. Phase 2 = village-level paired cluster RCT (stepped-wedge fallback) within non-PD tehsils of the South-west peer group; DiD on village burnt share vs 2020–24 baseline; buffer/neighbour villages for spillovers. Secondary outcomes via survey incl. list experiment for burning. Appendix A questionnaire (10 modules), logframe, timeline, budget lines, ethics, risks.
- Approaches considered: (a) evaluate a PD-informed intervention — **selected** (the DPPD step after Stage 3); (b) evaluate the DPPD ranking tool itself (do agencies target better) — not selected as primary, covered only as the seasonal monitoring output.
- Open [TBD]: sample size, typical-peer picks, number of arms, budget figures.

### 2026-11-15 — §8 merged into the report; first sample-size calculation withdrawn
**Plain:** §8 and the questionnaire are now in the report. The first sample-size calculation used data that is not part of the project, so it was removed; it will be redone from the main tehsil burn measure.
**Technical:** §7 impact bullets moved to §8.1, replaced by a 3-line pointer; §8.1–§8.12 inserted before Figures; Appendix A after References; §8.4 analysis = ANCOVA on baseline + peer group (DiD as robustness). §8.7 reset to TBD; `Code/impact/` and `outputs/impact/` removed.
- Still open: sample size, budget figures, typical-peer tehsil picks, number of arms.

### 2026-11-15 — Pilot sample size redone from the main tehsil burn measure
**Plain:** Worked out how many villages a pilot needs using only the project's tehsil burn data. For a 10-point drop, scored on 30 satellite points per village, the middle case needs 30 villages per arm; we recommend 35 pairs per lever.
**Technical:** `Code/impact/sample_size.py` → `outputs/impact/{variance_components,sample_size_table}.csv`, `run.log`. Frame = 17 South-west tehsils minus Abohar (1,633 Census villages, LGD bridge). Fields = the fixed 100 points/tehsil, 2019–24. One-way ANOVA split of var(y), var(x), cov(x,y) into between-tehsil B and within W; 2023: mean 0.65, ICC_tehsil 0.051, between SD 0.108, field persistence 0.36; true tehsil corr ≈1.0 (2019–23), 0.25 for 2024. Village scenarios: between-village var = k·B (k = 1, 2, 3), true-level autocorrelation π_c = 0.9/0.7/0.5 (tehsil ≈1.0 judged unrealistic for villages: first run with it gave 2–5 villages/arm). Cluster ANCOVA on village means of m points, t-iterated n. δ = 0.10, m = 30: 15–52 per arm, middle (k 2, π_c 0.7) = 30; m 10 → 48, 100 → 23; no baseline 49; δ 0.05 → 114.
- Rejected: simulating villages (no village IDs in the main data). Caveat: k and π_c are assumptions; Phase 1 should measure them.
