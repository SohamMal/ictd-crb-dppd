# Problem definition — crop residue burning (CRB) in Punjab
**DPPD position:** Stage 1 › Problem Definition · **Status:** Done (Assignment 1), refined since · **Last updated:** 2026-10-06

## In plain words
After the paddy harvest (Oct–Nov), many Punjab and Haryana farmers burn the leftover straw to clear fields fast for wheat. This is a major source of winter air pollution in Delhi NCR. Years of subsidies (Happy Seeder, Super Seeder, custom hiring centres) have not stopped it evenly. The interesting fact is that places with similar conditions burn very different amounts. Our question is: **which places already burn much less than similar places, and what can others learn from them?**

## Technical summary
- **Objective:** identify geographic units with significantly lower paddy-residue burning than structurally similar peers. Explain the difference and turn it into guidance for NGOs and government.
- **Exact question (current):** among the 97 current Punjab tehsils, grouped by structural conditions, which tehsils burn significantly less paddy stubble than their peer group, and why?
- **Outcome variable:** satellite-measured burnt paddy area (Sentinel-2 BAIS2 + TCB). See `2.1/task_burn_detection.md`.
- **Out of scope:** wheat-residue burning (Apr–May), Haryana (deferred), Stages 4–5 of DPPD.
- **Literature used:** CEEW (2024, 2025) on CRM adoption barriers; RGICS (2024); Vadrevu & Lasko (2018) MODIS vs VIIRS; Walker et al. (2022) Sentinel-2 burn detection; Albanna et al. (2022) DPPD; Naeher et al. (2023) farmer survey.

## Log (append-only, chronological)
### Early Sep 2026 — Assignment 1 position paper (reconstructed)
**Plain:** We wrote the first version of the problem. It looked at **districts**, counted fires with NASA FIRMS, and planned to test causes with a regression model.
**Technical:** A1 (ACM sigconf, `0. Material/Assignment 1/`). The paper lists Soham Malvadkar and Aryan Rana as authors. Design: district-year panel; Y = FIRMS/VIIRS fire count normalised by cropped area, paddy window Oct–Nov and wheat window Apr–May; covariates CRM machines, mandi access and prices, water. Pipeline: §2.2 non-model PD ranking + Mann-Kendall trend → §2.3 descriptive characterisation → §2.4 causal FE/DiD → §2.5 "Second Deviant Pass" on causal output. Pilot on 4 district-years. [C]

### Sep 2026 — Problem sharpened through method feedback (reconstructed)
**Plain:** Feedback changed three things. We now use better satellite data than fire counts. We compare like with like before ranking. We work at a finer level than districts.
**Technical:** (1) FIRMS undercounts about 3.67× vs Sentinel-2, so it was dropped (`2.1/task_burn_detection.md`). (2) Basma: Homogeneous Grouping is a mandatory DPPD step, so it was added (`1.2/task_suitability.md`). (3) The unit moved district → tehsil (97 current Punjab tehsils) so deviants are not hidden inside district averages. Wheat window dropped from the core scope. [C]

### 2026-10-06 — Scope confirmed by supervisor
**Plain:** The professor confirmed: Punjab first, Haryana only after the Punjab pipeline works.
**Technical:** [C] Punjab-only scope (Prof. Aaditeshwar, Oct 2026 meeting). See `docs/HANDOFF_UPDATE_2026-10-06.md`.
