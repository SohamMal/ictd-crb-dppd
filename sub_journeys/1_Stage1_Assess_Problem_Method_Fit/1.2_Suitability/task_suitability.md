# Suitability — is DPPD the right method for CRB?
**DPPD position:** Stage 1 › Suitability · **Status:** Done · **Last updated:** 2026-10-06

## In plain words
Positive Deviance works only if some units really do better than similar units. For burning, that looks likely: districts with similar crops, climate and subsidy access burn very different amounts. Satellites watch every field every few days, so we can measure burning everywhere without surveys. One early mistake was skipping the "compare only with similar units" step. A DPPD co-author (Basma Albanna) pointed out that this step is required, and we added it.

## Technical summary
- **Suitability conditions (handbook Stage 1):** (a) the outcome varies among comparable units, so PDs plausibly exist; (b) the outcome is observable at scale in non-traditional data (Sentinel-2); (c) the units' practices are discoverable and transferable (CRM use, ex-situ residue markets, local initiatives).
- **Theory of change (A1 §3, still valid in spirit):** PDs exist and are not noise → their enabling conditions are partly observable in public data → specific existing examples are more actionable than generic "what predicts burning" models.
- **Method constraints [C]:**
  - Grouping variables must be **structural and non-transferable** (climate, soil, rice, water, terrain).
  - Hypothesised **drivers** (CRM machines, mandi access) never enter grouping; they belong in Stage 3.
  - **Burning outcomes never build groups.**
  - Prof. Aaditeshwar's rule: no residual-based deviant identification, so PDs come from direct within-group comparison, not model residuals.
- **Open:** A1 §2.5 "Second Deviant Pass" (deviants on causal-model output) is unapproved and may conflict with the no-residuals rule. [?]

## Log (append-only, chronological)
### Early Sep 2026 — DPPD chosen; non-model PD identification (reconstructed)
**Plain:** We chose DPPD and decided to find deviants by direct ranking, not by fitting a model first.
**Technical:** A1 §2.2: model residuals on historically biased intervention data would encode that bias, so PDs come from directly comparable normalised outcomes. Mann-Kendall trend test as a temporal cross-check. [C]

### Sep 2026 — Homogeneous Grouping added after Basma's feedback (reconstructed)
**Plain:** The first design ranked districts directly against each other. Basma said DPPD requires first sorting units into groups of similar ones, then ranking only inside each group. We added that step, and it became the main work of the project.
**Technical:** The original design skipped Stage 2 › Homogeneous Grouping. Basma's critique maps to a canonical pipeline requirement, not a preference. Stage 2 is now Performance Measurement → Homogeneous Grouping → PD Identification → PD Validation. [C]

### Sep 2026 — Mixed-resolution design approved (reconstructed)
**Plain:** Our data comes at different levels (village, block, district). The professor approved keeping each dataset at its own level and passing it down to finer units, instead of throwing detail away.
**Technical:** Variables kept at native resolution and inherited downward through crosswalks (`2.2/task_units_boundaries_crosswalks.md`). Approved by Prof. Aaditeshwar. [C]
