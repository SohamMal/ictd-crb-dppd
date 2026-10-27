# DAY_PLAN.md — Day-wise route to completion
_Created 2026-10-06. **Target: submit by Tue 20 Oct 2026** (hard backstop: 22 Oct). 15 working days._
_Status of this file: **[P] proposed plan**. It is a current-state file: tick boxes and adjust dates freely. Decisions and history still go to `project_tracker.md` §7 (append-only)._
_Basis: `project_tracker.md` (incl. 2026-10-06 supervisor update), `HANDOFF_UPDATE_2026-10-06.md`, `CURRENT_STATUS.md`, `DECISIONS.md`, `METHODOLOGY.md`._

---

## 0. How to read this plan
- **Phases** map to DPPD stages. Each day = goal → tasks → deliverables (files) → *done when* → *fallback if blocked*.
- **Gates** (🚧) are hard checkpoints. If a gate slips, use the fallback, do not let it eat the next phase.
- **Rule of thumb:** grouping must freeze by **Sat 10 Oct**. Everything after depends on it.
- **Scope [C]:** Punjab only, 97 tehsils. Haryana = stretch goal only (Day 15 buffer), otherwise a stated limitation.
- **Budget:** ~6–8 focused hours/day. Each day has a 1-hour slack built in.

| Phase | Dates | DPPD step | Output |
|---|---|---|---|
| A. Grouping rebuild | Tue 6 – Sat 10 Oct | Stage 2 · Step 2 | Frozen peer groups (code + numbers) |
| B. Performance measurement | Sun 11 – Mon 12 Oct | Stage 2 · Step 1 | Tehsil burn metric table |
| C. PD identification + validation | Tue 13 – Wed 14 Oct | Stage 2 · Steps 3–4 | Validated PD list |
| D. Discover predictors | Thu 15 – Fri 16 Oct | Stage 3 | PD vs non-PD comparison + recommendations |
| E. Report + slides | Sat 17 – Mon 19 Oct | — | Final report, slides, repo |
| F. Submit / buffer | Tue 20 Oct | — | Submission |

---

## Phase A — Homogeneous grouping (freeze by 10 Oct)

### Day 1 · Tue 6 Oct — Rice share + clustering skeleton
**Goal:** inputs are final for the baseline run; pipeline code exists.
- [ ] Patch `Data/Rice/calc_chen2022_rice_area_current_lgd.py` → add `tehsil_area_ha` (polygon area, equal-area CRS e.g. EPSG:32643) and `rice_share = rice_area_ha / tehsil_area_ha`. **Show diff first.**
- [ ] Rerun; sanity check: shares in [0,1], high in Sangrur/Patiala/Ludhiana belt, low in Kandi/Pathankot.
- [ ] Update the three masters with `rice_share` (keep old hectares column, don't delete).
- [ ] Create `Code/grouping/` with `config.py` (**configurable dimension list**, weights, transforms) and `gower.py` (dimension-balanced Gower: numeric = range-normalised |diff|, categorical = 0/1 mismatch, mean within dimension, weighted mean across dimensions).
- [ ] Soil: use **original categorical columns** from `_transformed.csv`, not `_encoded.csv` [C per handoff §4].
- [ ] Start zone-data search (30 min): ICAR-ATARI / PAU agro-climatic sub-zones, NBSS&LUP agro-ecological sub-regions (AESR, ~60 sub-regions, finer than district), Punjab "Kandi / Central / South-western / Sub-mountainous" belts at block level.

**Deliverables:** patched rice script, updated masters, `Code/grouping/{config,gower}.py`
**Done when:** a 97×97 distance matrix is saved as `outputs/grouping/dist_baseline.csv`.
**Fallback:** if area computation is slow, compute tehsil area from the LGD polygons once and cache it.

### Day 2 · Wed 7 Oct — Baseline clustering, reproduce or disprove 25/14/57
**Goal:** first reproducible grouping result.
- [ ] `cluster.py`: average-linkage HAC on precomputed matrix; dendrogram; cuts k = 2…8.
- [ ] Silhouette per k (precomputed metric); table of group sizes per k.
- [ ] Check: is Dhar Kalan a singleton at every k? Do we get 25/14/55/2 → 25/14/57? Record silhouette (reported 0.287).
- [ ] Group profile table: per group, median of each variable + modal soil classes (this explains *what* each group is — needed for the report).
- [ ] Map of groups over tehsil polygons (`outputs/grouping/map_baseline.png`).

**Deliverables:** `cluster.py`, `outputs/grouping/{dendrogram,silhouette_by_k,sizes_by_k,profiles}.*`
**Done when:** baseline numbers are in a CSV produced by code, compared side-by-side with the ChatGPT numbers.
**Fallback:** if results differ from 25/14/57, trust the code; note the difference (journey-worthy).

### Day 3 · Thu 8 Oct — Stability + sensitivity
**Goal:** know how robust the grouping is.
- [ ] `stability.py`: bootstrap 80% subsample, 300 runs, ARI vs full-data labels (on overlapping tehsils); per-tehsil co-assignment frequency → list of unstable tehsils.
- [ ] One-factor-at-a-time sensitivity, each reported as ARI vs baseline:
  - no log transforms · groundwater 2025 (sensitivity only [C]) · each weight ±15% · drop each dimension in turn · soil with near-constant descriptors dropped (evidence only, **don't drop without your OK**).
- [ ] Untested-assumption check: add temperature/rainfall variability as a *test-only* dimension if data is quick; otherwise list as limitation.
- [ ] Zone data search continues (aim: a file in hand by end of day).

**Deliverables:** `outputs/grouping/{bootstrap_ari,sensitivity_table,unstable_tehsils}.csv`
**Done when:** a single sensitivity table exists with one row per perturbation.
**Fallback:** if 300 runs is slow, 100 runs + note it.

### Day 4 · Fri 9 Oct — Zones replace rainfall + terrain
**Goal:** implement the supervisor-endorsed design [C: zones replace rainfall & terrain].
- [ ] Map zone data to 97 tehsils (majority-area overlap; village-level inheritance via `village_level_bridge_punjab.csv` if zones are finer).
- [ ] Decide encoding with Soham: **categorical zone label (0/1 mismatch)** vs numeric zone attributes. **[?] Needs your call.**
- [ ] Run zone design through Day 2–3 pipeline (config switch only). Compare with baseline: ARI, silhouette, sizes, map.
- [ ] Weight justification (1 hr): look for equal-weight precedent in DPPD handbook / composite-index literature (OECD composite indicator handbook; Gower 1971; DPPD papers). Draft 3-line justification.
- [ ] **Email Prof. Aaditeshwar** with: zone design result, weight justification (or the question), freeze proposal. Ask for a reply by Sat.
- [ ] Schedule follow-up call with **Basma & Andreas** for ~Tue 13 / Wed 14 Oct (topic: PD identification + validation).

**Deliverables:** `outputs/grouping/zones_vs_baseline.csv`, email sent, call scheduled.
**Fallback:** if no tehsil-level zone data found by today → use the **baseline (rainfall + terrain)** for freezing and state it as a documented deviation. Do not let zone data block Phase B.

### 🚧 Day 5 · Sat 10 Oct — Inspect, choose cut, FREEZE grouping
**Goal:** frozen groups.
- [ ] Inspect unstable tehsils (esp. G1): which dimension drives them? Look at their raw values.
- [ ] Compare alternative cuts (k−1, k+1) on silhouette, stability, min group size (≥ ~10 tehsils so PD stats make sense), interpretability.
- [ ] Freeze: `outputs/grouping/FROZEN_groups.csv` (`lgd_sd_code, tehsil_name, group, outlier_flag`), plus config hash/version.
- [ ] Write `sub_journeys/task_homogeneous_grouping_clustering.md` entry (I give you the snippet; you approve).
- [ ] Tracker §7 entry: "Grouping frozen".

**Gate:** grouping file frozen tonight. **Fallback:** freeze best current version anyway; any later advisor change becomes a sensitivity check, not a redo.

---

## Phase B — Performance measurement

### Day 6 · Sun 11 Oct — Scale BAIS2+TCB to tehsil (GEE)
**Goal:** burnt area per tehsil, per year.
- [ ] Confirm metric with Soham: **[P] burnt share of rice area** = burnt paddy area / Chen 2022 rice area (normalises for tehsil size and rice amount).
- [ ] GEE script: Sentinel-2 SR Harmonized, post-harvest window (approx. 15 Oct – 30 Nov; composite or multiple snapshots), cloud mask, Chen 2022 rice mask, validated BAIS2 (Filipponi) + TCB thresholds → burnt pixel mask → `reduceRegions` sum over 97 tehsils.
- [ ] Years: **2022, 2023, 2024** (3 seasons → PDs must be consistent, not one-off). Start exports for all years tonight.
- [ ] Log per tehsil: % valid (cloud-free) pixels, so low-quality tehsils can be flagged.

**Deliverables:** `Code/gee/burn_tehsil_bais2_tcb.js`, exported `burn_tehsil_{2022,2023,2024}.csv`
**Fallback:** if exports are too slow → 2022 + 2024 only, or coarser scale (20 m).

### Day 7 · Mon 12 Oct — Burn metric QA
**Goal:** a trusted performance table.
- [ ] Merge exports → `outputs/performance/tehsil_burn_metric.csv` (per year + 3-yr mean).
- [ ] QA: cloud-coverage flags; year-to-year correlation; sanity vs FIRMS counts (rank correlation only, not as the measure); map of burn share.
- [ ] Cross-check a few tehsils visually in GEE (one high, one low, one mid).
- [ ] Note harvest-timing risk: late-harvest tehsils may burn after window → check window end.

**Deliverables:** performance table + map + QA notes.
**Done when:** every frozen-group tehsil has a burn value with a quality flag.

---

## Phase C — PD identification & validation

### Day 8 · Tue 13 Oct — PD identification
**Goal:** candidate positive deviants within each peer group.
- [ ] Within each frozen group: z-score / percentile of burn share per year. **[P] PD rule:** in the bottom ~10–20% of its group (or z ≤ −1) in **at least 2 of 3 years** and on the 3-yr mean. Confirm thresholds against the DPPD handbook.
- [ ] **Not residual-based** (Prof.'s rule); Section 2.5 "Second Deviant Pass" stays out unless approved.
- [ ] Also flag *negative* deviants (worst burners) — useful contrast for Stage 3.
- [ ] Outlier (Dhar Kalan) handled separately/contextually.
- [ ] Basma & Andreas call (if scheduled today/tomorrow): present grouping + PD rule.

**Deliverables:** `outputs/pd/pd_candidates.csv`, ranking plots per group.

### Day 9 · Wed 14 Oct — PD validation
**Goal:** rule out artefacts; final PD list.
- [ ] Robustness: PD still PD under (a) alternative cut k±1, (b) groundwater 2025 grouping, (c) different burn threshold / window.
- [ ] Artefact checks: low rice share (little to burn), cloud gaps, crop switching (rice share fell after 2022?), early/late harvest, boundary errors.
- [ ] Visual check of each PD in Sentinel-2 imagery.
- [ ] Final list: `outputs/pd/pd_validated.csv` with reason codes for dropped candidates.
- [ ] Journey + tracker snippet (you approve).

**Fallback:** if few/no PDs survive → loosen to "consistent low burners" and report honestly; this is still a result.

---

## Phase D — Discover predictors (Stage 3)

### Day 10 · Thu 15 Oct — Hypotheses + quick data
**Goal:** test candidate drivers that are *allowed here* (they were banned from grouping).
- [ ] Hypothesis list: CRM machine subsidy/availability (district/block, from Punjab Agri Dept / PIB data), custom hiring centres, biomass/paper/power plants nearby (ex-situ demand), mandi distance, basmati vs non-basmati (PR-126 short-duration varieties), Happy Seeder / super-SMS adoption, Gaushala/fodder use, awareness campaigns, cooperative density.
- [ ] Collect what is **quick** (≤ 1 day): public lists of biomass plants & CHCs, CRM machine counts by district, mandi locations (Agmarknet).
- [ ] Compute for PD vs non-PD tehsils within the same group.

**Deliverables:** `Data/predictors/*.csv`, `outputs/predictors/pd_vs_peers.csv`

### Day 11 · Fri 16 Oct — Predictor analysis + recommendations
- [ ] Within-group comparisons (Mann-Whitney / effect sizes; small n → descriptive, not causal).
- [ ] Literature/news triangulation for each PD tehsil (local initiatives, plants, NGO programmes).
- [ ] Draft interview/field-validation guide for future work (DPPD step that we cannot fully execute in time → stated limitation).
- [ ] Draft actionable recommendations for NGOs / government (which practice, where to replicate, in which peer group).

**Deliverables:** predictor table, recommendation list, figures.

---

## Phase E — Report & presentation

### Day 12 · Sat 17 Oct — Report: Methodology + Experiments
- [ ] Build from tracker + journeys: problem–method fit, data, boundaries/crosswalks, grouping (dims, Gower, HAC, weights justification), burn measure (BAIS2+TCB validation), PD rule.
- [ ] Freeze all figures (`outputs/figures/`).

### Day 13 · Sun 18 Oct — Report: Results, Discussion, Limitations
- [ ] Results: groups, stability, burn map, PD list, predictors.
- [ ] Limitations: Punjab only, Chen 2022 fixed, zone/rainfall choice, equal weights, no field validation, satellite window, small n.
- [ ] Recommendations + future work (Haryana, village-level PD, field interviews).
- [ ] Send draft to Prof. Aaditeshwar if feedback is possible before 20 Oct.

### Day 14 · Mon 19 Oct — Slides + reproducibility
- [ ] Slides (~12–15): problem → DPPD → data → grouping → burn → PDs → predictors → recommendations.
- [ ] `run_all.py` / README: master files → distance → clustering → stability → PD → figures, one command.
- [ ] Re-run end to end on a clean session; confirm numbers in report match outputs.

---

## Phase F — Submit

### 🚧 Day 15 · Tue 20 Oct — Final review & submit
- [ ] Proofread, references, figure captions, numbers cross-checked.
- [ ] Submit. Final tracker §7 entry.
- [ ] Remaining buffer (21–22 Oct): only for slips. Haryana replication only if everything above is done.

---

## Key dependencies & risk register
| Risk | Effect | Mitigation |
|---|---|---|
| No tehsil-level zone data | Phase A slips | Day 4 fallback: freeze with rainfall + terrain, document as deviation |
| Prof. reply late on weights/zones | Can't freeze | Freeze anyway on Day 5; later feedback → sensitivity only |
| GEE exports slow / quota | Phase B slips | Start exports Day 6 night; reduce years/scale |
| Clouds in post-harvest window | Biased burn share | Valid-pixel flag; multi-date composite |
| Few PDs survive validation | Thin Stage 3 | Report "consistent low burners"; honest negative result is valid DPPD output |
| Predictor data unavailable | Weak Stage 3 | Limit to 3–4 quick variables + literature triangulation |

## Questions to resolve early (owner: Soham)
1. **[?]** Zone encoding: categorical label or numeric attributes? (needed Day 4)
2. **[?]** Burn metric = burnt share of rice area? (needed Day 6)
3. **[?]** Years for performance: 2022–2024? (needed Day 6)
4. **[?]** PD threshold rule (bottom % / z-score, years required)? (needed Day 8)
5. **[?]** Report format and submission requirements (length, template — ACM sigconf like A1?).
