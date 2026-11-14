# Task: Impact assessment design (final report §8)

**Objective.** Prof's 2026-11-01 mail: final report (due 2026-11-25) = paper-quality §1–§7 + a separate impact assessment section (proposed methodology, survey questions, recommended formats) that a partner could use as a funding proposal.

### 2026-11-15 — Design proposed and §8 drafted
**Plain:** Designed a two-phase plan: first check the PD leads in the field, then pilot the Abohar levers (straw buyer, labour, fodder) in matched non-PD villages and measure the change with our satellite burn measure plus a farmer survey.
**Technical:** Draft in `report/draft_impact_section.md` (status: proposed, not merged). Phase 1 = PD/ND/typical-peer tehsils, ~6 villages × ~20 farmers, FGDs, KIIs, ground-truth photos at Sentinel-2 points. Phase 2 = village-level paired cluster RCT (stepped-wedge fallback) within non-PD tehsils of the South-west peer group; DiD on village burnt share vs 2020–24 baseline; buffer/neighbour villages for spillovers. Secondary outcomes via survey incl. list experiment for burning. Appendix A questionnaire (10 modules), logframe, timeline, budget lines, ethics, risks.
- Approaches considered: (a) evaluate a PD-informed intervention — **selected** (the DPPD step after Stage 3); (b) evaluate the DPPD ranking tool itself (do agencies target better) — not selected as primary, covered only as the seasonal monitoring output.
- Open [TBD]: sample size (power calc from `version_X` village burn measure, needs approval), typical-peer picks, number of arms, budget figures.

### 2026-11-15 — Pilot sample size computed; §8 merged into the report
**Plain:** Used our own village burn data to work out how many villages a pilot needs. To detect a 10-point drop in burning, about 22 villages per arm are needed if each village is scored on 30 satellite points and its past burning is allowed for; we recommend 25 pairs per lever.
**Technical:** `Code/impact/power_calc.py` → `outputs/impact/{power_table,variance_components}.csv`, `run.log`. Frame = 1,597 South-west villages (version_X), minus Abohar and validated village PDs. Target 2023, baseline mean 2020–22, ANCOVA with peer FE; r(baseline, 2023) = 0.67; SD 0.21 raw → 0.16 after baseline; binomial sampling SD ≈ 0.13 at ~10 pts. n/arm (δ = 0.10, 80%, α 0.05): 63 no baseline; 42 baseline at 10 pts (simulation; formula 39 gave 0.74 power, so t-iteration + simulation search added); 22 at 30 pts; 16 at 100 pts; 13 full field (lower bound). 2024 as target: r = 0.31. Pairing not credited (conservative).
- Report: §7 impact bullets moved to §8.1, replaced by a 3-line pointer; §8.1–§8.12 inserted before Figures; Appendix A questionnaire after References; Table 10 = sample size; §8.4 analysis switched from DiD to ANCOVA (DiD as robustness) to match §8.7.
- Still open: budget figures, typical-peer tehsil picks, number of arms.
