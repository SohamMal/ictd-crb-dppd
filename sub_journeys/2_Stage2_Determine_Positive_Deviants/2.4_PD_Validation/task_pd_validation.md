# Positive deviant validation
**DPPD position:** Stage 2 › Positive Deviant Validation · **Status:** Not started · **Last updated:** 2026-10-06

## In plain words
Before trusting a "positive deviant", we check it isn't a mistake. Maybe clouds hid the fires, the tehsil has little rice to burn, farmers switched crops, or harvest fell outside our satellite window. Only tehsils that pass these checks count as real positive deviants.

## Technical summary
- **Robustness [P]:** PD status kept under alternative cut (k±1), groundwater-2025 grouping, different burn threshold/window.
- **Artefact checks [P]:** low rice share; cloud/valid-pixel gaps; crop switching after 2022; early/late harvest; boundary errors; visual Sentinel-2 check per PD.
- **Output [P]:** `outputs/pd/pd_validated.csv` with reason codes for dropped candidates. If few survive, report "consistent low burners" honestly.
- Ground-truth provenance must be confirmed before external citation [?].

## Log (append-only, chronological)
### 2026-10-06 — File created
**Plain:** Placeholder; planned for 14 Oct.
**Technical:** Depends on `2.3/task_pd_identification.md`.
