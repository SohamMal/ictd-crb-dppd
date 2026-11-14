# Draft — §8 Impact Assessment (proposal)

> Status: **proposed**, drafted 2026-11-15 for Soham's review. Not yet merged into `report_draft.md`.
> Sections §1–§7 stand on their own as a paper; §8 is the proposal a partner (NGO, government department or funder) could adopt.
> Items marked **[TBD]** need a decision or a computation before submission.

---

## 8. Impact Assessment (proposal)

This section turns the study's leads into a plan that a partner could fund and run. It answers three questions:
- **What would we change?** Burning in non-PD villages, by transferring what the PDs appear to do differently.
- **How would we know it worked?** A matched, randomised pilot scored by the satellite burn measure built in this study, backed by a farmer survey.
- **What would a partner receive?** A survey instrument, a logframe, a sample-size and budget sketch, and seasonal monitoring outputs.

### 8.1 What the study implies for NGOs and government

1. **Where to look.** The PD list tells field teams where to go first: Abohar in the South-west, and the Doaba tehsils in Central Punjab. The heavy-burning NDs (Lehra, Zira, Moonak, Guruharsahai) are the natural comparison. A small field study in these places could confirm what practices differ, at a fraction of the cost of a statewide survey.
2. **What to test.** Abohar's profile points to three levers that can be transferred to other South-west tehsils and tested there:
   - an assured local straw buyer (a biomass plant within the tehsil);
   - labour for manual straw handling;
   - fodder demand from livestock.

   For the Doaba belt, the question for fieldwork is what farmers do with straw before an October potato or vegetable crop, and whether that can work in wheat-only areas.
3. **How to target.** Programmes that rank districts or tehsils by burning should compare like with like (peer groups) and allow for rice share. Otherwise they reward places that simply grow less paddy and blame places that grow more.
4. **How to monitor.** Fire counts (VIIRS) collapsed in 2024–25 as farmers timed fires to avoid the satellite pass. Field-level Sentinel-2 detection that separates burning from ploughing gives an evasion-resistant alternative. It is free, covers every season, and produces tehsil rankings that agree with fire counts in the years before evasion. The pipeline can be rerun each season and extended to Haryana.

### 8.2 Theory of change

DPPD stops at "candidate explanations" (Stage 3). The handbook's next step is to check those explanations and test whether they transfer [8]. We propose two phases:

```
PD leads (this study)
   → Phase 1: confirm in the field what PDs do differently      (1 season)
   → Phase 2: pilot the confirmed levers in matched non-PD villages (1–2 seasons)
   → measure the change in burning with satellite + survey
   → scale up through the partner if the effect holds
```

Assumptions that must hold, and where each is tested:

| Assumption | Tested in |
|---|---|
| PD practices are real, not a data artefact | Phase 1 field visits to satellite points |
| The practices are transferable (not tied to Doaba's region or Abohar's plant) | Phase 1 interviews; Phase 2 pilot |
| Farmers adopt the lever when it is offered | Phase 2 take-up indicators |
| Adoption lowers burning, not just shifts it in time or place | Phase 2 satellite outcome incl. buffer villages |

### 8.3 Phase 1: field validation (one season, Sep–Dec)

**Why first.** The main limitation of this study is that no practice is confirmed on the ground (§6). A funder will not pay for a pilot of unconfirmed levers. Phase 1 is cheap and fixes that.

**Where.**

| Role | Tehsils | Why |
|---|---|---|
| PD | Abohar | Only strict PD; single-case profile (§4.4) |
| PD | Dinanagar, Phagwara, Jalandhar-I, Adampur | Doaba belt, Central group |
| ND | Lehra, Zira, Moonak, Guruharsahai | Heavy burners in the same groups |
| Typical peer | 2 per group, near the group median **[TBD: pick by code]** | Shows what "normal" looks like |

**Village selection.** Within each tehsil, rank villages by their 2020–24 satellite burnt share and select about 6 villages spread across that range (this needs the §3.4 burn measure run on more points per village, a cheap extension of the existing pipeline). This gives both "PD villages inside PD tehsils" and ordinary villages for contrast.

**Activities.**
- **Farmer survey:** about 20 rice farmers per village, sampled from the village list (§8.5).
- **Focus groups:** one per village (farmers; separately labourers where possible).
- **Key-informant interviews:** block agriculture officer, the biomass/CBG plant buyer, CRM hiring-centre operators, the village sarpanch.
- **Ground truth for the detector:** visit a sample of the study's Sentinel-2 points around harvest and record burnt / ploughed / baled / standing stubble with a dated, geotagged photo. This gives the field-located ploughing check the study lacked (D11).

**Output.** A short validation note per PD: which candidate levers are confirmed, which are rejected, and which new ones appeared. Only confirmed levers go to Phase 2.

### 8.4 Phase 2: pilot of the levers (matched, randomised)

**Levers to pilot** (assuming Phase 1 confirms them; Abohar-derived, South-west group):

| Lever | What the partner provides | Cost driver |
|---|---|---|
| A. Assured straw buyer | Baler + aggregator contract linked to a biomass or CBG plant, with a fixed collection date and price | Baling and transport per tonne |
| B. Labour for manual handling | Paid labour days during the harvest–sowing window | Wages |
| C. Fodder linkage | Straw-to-dairy link (collection, storage, buyer) | Storage and transport |

The Doaba lever is not specified until Phase 1 shows what it is.

**Design.**
- **Unit:** the village. Straw collection and labour are organised by village, and burning spreads by example within a village.
- **Sampling frame:** villages in **non-PD tehsils of the same peer group** (South-west for levers A–C). The peer groups are what make treated and control villages comparable. This is the main thing DPPD adds to a standard pilot.
- **Assignment:** villages are paired on 2020–24 burnt share and rice share, then one village in each pair is randomly chosen for the lever. One arm per lever plus control, or A alone if budget is tight **[TBD with partner]**.
- **If the partner cannot randomise:** a phased (stepped-wedge) rollout, where every village eventually gets the lever but the order is random.
- **Spillovers:** a straw buyer may also take straw from neighbouring villages. Controls are drawn at least one village away from treated ones, and the villages directly next to treated ones are tracked as a separate "neighbour" group.

**Analysis.** Compare treated and control villages in the pilot season, allowing for each village's own baseline burnt share (2020–24, already measured) and its peer group (ANCOVA, §8.7). This uses the baseline more efficiently than a plain difference-in-differences, which is kept as a robustness check. Controls from the same peer group absorb weather and policy shocks that hit the whole region in the same year.

### 8.5 Outcomes and indicators

| Level | Indicator | Source | When |
|---|---|---|---|
| **Primary outcome** | Village burnt share of rice fields | Sentinel-2 detector (§3.4), all rice fields in the village rather than 10 sample points | Every season, no field cost |
| Secondary | Share of plots where the farmer reports burning | Survey, with a list experiment (below) | Baseline + endline |
| Secondary | Wheat sowing date | Survey; Sentinel-2 green-up | Endline |
| Secondary | Residue-management cost and net income per acre | Survey | Endline |
| Secondary | Wheat yield | Survey (crop cut if budget allows) | Following April |
| Take-up | Share of farmers who sold straw / used labour / supplied fodder; tonnes collected | Partner records | During season |
| Cross-check | Fire counts | VIIRS | Every season |

**Why the satellite measure is primary.** It covers every field, needs no interview, cannot be talked around, and has a five-season baseline already. Fire counts are kept only as a cross-check because farmers now time fires to avoid the satellite pass.

**Why a list experiment.** Burning is illegal, so farmers under-report it when asked directly. In a list experiment, half the farmers get a list of 4 harmless statements and the other half get the same list plus "I burnt straw on at least one plot last season". Each farmer says only *how many* statements are true, never which. The difference in average counts between the two halves estimates the share who burnt, without any farmer admitting it.

### 8.6 Survey instrument (summary)

The full questionnaire is in Appendix A. Modules:

| # | Module | Purpose |
|---|---|---|
| 1 | Household and farm | Land owned/leased, plots, crops, off-farm and overseas income |
| 2 | Paddy season | Variety (PR-126, basmati, other), harvest date, combine type (with/without SMS) |
| 3 | Residue handling per plot | Burnt / incorporated / baled / fed / mulched / left; why |
| 4 | Machines | Own or hire; Super Seeder / Happy Seeder / baler; cost; waiting time; CRM subsidy received |
| 5 | Straw market | Buyer, price, distance, who pays for baling, reliability |
| 6 | Labour and livestock | Hired labour availability and wage at harvest; cattle and buffalo; fodder use of straw |
| 7 | Next crop and timing | Wheat / potato / vegetables; days between harvest and sowing; pressure felt |
| 8 | Norms and enforcement | What neighbours do; fines, red entries, visits by officials; awareness of the rules |
| 9 | Barriers and preferences | What would make the farmer stop burning; willingness to sell straw at a given price |
| 10 | List experiment | Sensitive burning question (§8.5) |

### 8.7 Sample size

How many villages Phase 2 needs depends on two things:
- **How much burning differs between similar places.** This is the noise a pilot effect has to stand out from.
- **How well a place's past seasons predict its next one.** The stronger the link, the more noise the baseline removes, and the fewer villages are needed.

**Where the numbers come from.** Both are estimated from the study's tehsil burn measure (§3.4). It revisits the same 100 points in every tehsil each season, 2019–24 (`Code/impact/sample_size.py`; outputs in `outputs/impact/`).
- **Frame:** the 17 South-west tehsils other than Abohar, which hold 1,633 Census villages. Abohar is excluded because the levers come from there.
- **Pilot season:** 2023. **Baseline:** each field's 2019–22 burning.
- **Analysis:** pilot-season burning compared between arms, allowing for the village baseline (ANCOVA).
- **Test:** 80% power, 5% two-sided significance, with a small-sample correction.

**What the data show.**
- In 2023, 65% of fields burnt.
- Tehsils in the frame differ by an SD of 0.11, and the tehsil explains about 5% of the field-to-field variation.
- A field that burnt before is more likely to burn again: within-tehsil correlation 0.36.
- Tehsil burning levels tracked each other almost perfectly from 2019 to 2023 (estimated correlation ≈ 1.0, on 17 tehsils), but not into 2024 (0.25).

**Two things the tehsil data cannot tell us, set as ranges.** The pilot unit is the village, and the data have no village identifier.
- **How much villages differ.** Villages are smaller than tehsils and usually more alike inside, so they should differ more from each other. We set the between-village variation at 1×, 2× and 3× the between-tehsil value.
- **How steady a village's burning level is from year to year.** A village has more local shocks than a tehsil (a buyer arrives or leaves, harvest timing shifts). We set this correlation at 0.9, 0.7 and 0.5 rather than the tehsil estimate of ≈ 1.0, which would make the baseline look unrealistically strong.

**Table 10. Villages needed per arm to detect a 10-point drop.** *(2023 as pilot season, 30 points scored per village per season. One arm = one lever, or control; with pairs, villages per arm = number of pairs.)*

| Year-to-year steadiness of a village's level | Villages differ 1× as much as tehsils | 2× | 3× |
|---|---|---|---|
| 0.9 | 15 | 18 | 21 |
| 0.7 | 21 | **30** | 39 |
| 0.5 | 25 | 39 | 52 |

**How the middle case (2×, 0.7) changes:**

| Change | Villages per arm |
|---|---|
| Fewer points per village: 10 | 48 |
| More points: 100 | 23 |
| More points: 300 | 21 |
| No baseline, 30 points | 49 |
| A 5-point drop instead of 10 | 114 |
| A 15-point drop instead of 10 | 14 |
| 2022 as pilot season | 32 |
| 2024 as pilot season | 20 |

**Recommendation.**
- Design for a **10-point drop**, about one-sixth of current burning. A smaller effect would hardly justify the lever's cost.
- Score **at least 30 points per village** each season. This costs nothing extra: it only needs more Sentinel-2 extraction, and points beyond 30 add little.
- Plan on the middle case, **30 villages per arm**, rounded up to **35 pairs (70 villages) per lever** to allow for villages where the lever is not delivered.
- The pessimistic corner of Table 10 (52 per arm) still fits easily within the 1,633-village frame. Three levers plus control would need about 140 villages.
- Add the neighbouring villages tracked for spillovers (§8.4).

**Caveats.**
- The between-village spread and the village-level steadiness are assumptions, not estimates. Phase 1 can measure both by scoring 30 points in each surveyed village, and the sample size should be recomputed before Phase 2.
- The calculation uses the normal-approximation formula. Shares near 100% cannot rise, which squeezes the variation, so a check by simulation on the Phase 1 data is advisable.
- Matching pairs on baseline and rice share is not credited, so the numbers err on the high side.

### 8.8 Recommended formats

**For data collection.**
- Tablet survey on KoboToolbox or ODK (free, works offline), in Punjabi, with GPS-tagged plots and dated photos for the ground-truth visits.
- Enumerators trained on the list experiment and on the burnt / ploughed / baled categories using example photos.

**For the partner and government.**
- **Seasonal ranking report:** tehsil and village burnt share, ranked within peer groups, produced each December by rerunning the pipeline.
- **Policy brief:** 2 pages, Punjabi and English: where the PDs are, what they do, what was piloted, and what it changed.
- **Logframe:** the table below, ready to lift into a funding proposal.
- **Open data:** anonymised village-level outcomes and code, so others can check the result.

**Logframe.**

| Level | Description | Indicator | Means of verification |
|---|---|---|---|
| Impact | Less paddy-straw burning in Punjab's South-west | Village burnt share, peer-group adjusted | Sentinel-2 detector |
| Outcome | Farmers in pilot villages manage straw without burning | Reported burning (list experiment); straw sold / fed | Survey; partner records |
| Outputs | Lever delivered on time in pilot villages | Villages served; tonnes collected; labour days | Partner records |
| Activities | Phase 1 validation; pilot set-up; baseline and endline surveys | Surveys completed; contracts signed | Field reports |
| Inputs | Enumerators, balers/contracts, labour budget, analysis time | Budget spent vs plan | Accounts |

### 8.9 Timeline

| Month | Phase 1 (year 1) | Phase 2 (year 2) |
|---|---|---|
| Jun–Jul | Ethics approval; enumerator hiring; village selection from the satellite measure | Pair and randomise villages; sign straw contracts |
| Aug | Pilot the questionnaire | Baseline survey |
| Sep–Nov | Field visits at harvest; ground-truth photos; interviews | Lever delivered; take-up monitored |
| Dec | Survey; validation note | Endline survey; satellite outcome computed |
| Jan–Mar | Analysis; decide which levers go to Phase 2 | Analysis; policy brief; scale-up decision |

### 8.10 Budget sketch **[TBD: costs to be filled with partner]**

| Line | Driver |
|---|---|
| Enumerators and supervisors | Villages × farmers × days |
| Travel and accommodation | Tehsils visited |
| Lever costs (baling, labour, fodder logistics) | Treated villages × tonnes or days |
| Tablets and software | One-time; KoboToolbox is free |
| Satellite analysis | Compute only; data are free (Sentinel-2) |
| Analysis and reporting | Researcher time |

### 8.11 Ethics

- Ethics (IRB) approval before any fieldwork; informed consent read aloud in Punjabi.
- Because burning is illegal, answers about burning are never stored with names, phone numbers or plot coordinates; the list experiment avoids direct admission altogether.
- Satellite outcomes are reported at village level or above, never per named farmer, so they cannot be used for enforcement against individuals.
- The pilot adds an option (a buyer, labour, a fodder link); it never withholds an existing scheme from control villages.

### 8.12 Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Phase 1 rejects the levers | No Phase 2 | Phase 1 is designed to fail cheaply; report what was learned |
| Bad weather or a late harvest year | Burning rises everywhere | Same-season controls from the same peer group |
| Burning moves to neighbouring villages | Effect overstated | Neighbour villages tracked separately |
| Farmers shift burning to cloudy days or late November | Satellite misses burns | Full Sep–Nov window; survey list experiment as second measure |
| Straw buyer or plant fails mid-season | Lever not delivered | Track take-up; analyse by actual delivery as well as by assignment |
| Partner capacity | Delays | Start with lever A only in a small number of village pairs |

---

## Appendix A. Farmer questionnaire (draft)

*Asked of one adult who makes farming decisions. Reference period: the most recent kharif (paddy) season. Codes in brackets.*

**Module 1 — Household and farm**
1. How many acres do you operate this year? Owned ___ Leased in ___ Leased out ___
2. How many separate plots? ___
3. Which crops did you grow in the last kharif and rabi seasons? (multi-select)
4. Does anyone in the household earn regular off-farm income? (none / job in India / remittance from abroad / business)

**Module 2 — Paddy season**
5. For each paddy plot: variety (PR-126 / PR-131 / Pusa-44 / basmati / other), transplanting date, harvest date.
6. How was the plot harvested? (combine with SMS / combine without SMS / manual)
7. Did you or a contractor own the combine? Cost per acre?

**Module 3 — Residue handling (per plot)**
8. What happened to the straw on this plot? (burnt fully / burnt partly / incorporated with Super Seeder / incorporated by ploughing / baled and sold / baled and kept / fed to animals / mulched with Happy Seeder / left standing)
9. How many days after harvest? ___
10. Main reason for this choice? (cost / time before sowing / no machine / no buyer / habit / other)
11. Did you handle straw differently three years ago? How?

**Module 4 — Machines**
12. Do you own any of: Super Seeder, Happy Seeder, mulcher, baler, MB plough, rotavator?
13. If you hired a machine: from whom (cooperative / CRM centre / private), cost per acre, days waited.
14. Did you receive any CRM subsidy or incentive? Which?

**Module 5 — Straw market**
15. Did anyone offer to buy or collect your straw? (yes / no) Who? Price per quintal or per acre?
16. Distance to the buyer or collection point (km)?
17. Who paid for baling and transport?
18. Would you sell straw at ₹___ per quintal if collected from the field? (willingness-to-accept ladder)

**Module 6 — Labour and livestock**
19. Could you hire labour at harvest when needed? Daily wage?
20. Number of cattle and buffalo owned. Do you use paddy straw as fodder? Share of your straw?
21. Does anyone in the village buy straw for fodder?

**Module 7 — Next crop and timing**
22. What did you sow after paddy? Date?
23. How many days did you feel you had between harvest and sowing? Was that enough?

**Module 8 — Norms and enforcement**
24. Out of 10 farmers in your village, how many do you think burnt straw last season? ___
25. Has any official visited, fined or recorded a "red entry" against farmers in your village? You personally?
26. Do you know the rules on straw burning and the penalties? (yes / partly / no)

**Module 9 — Barriers and preferences**
27. What one thing would most help you avoid burning? (machine on time / buyer / labour / more days before sowing / payment per acre / other)
28. Would you join a village straw-collection arrangement if one were set up? (yes / maybe / no) Why?

**Module 10 — List experiment** *(random half gets list A, the other half list B)*
29. "I will read some statements. Please tell me only **how many** are true for you, not which ones."
   - List A: (a) I grew wheat last rabi; (b) I own a tractor; (c) I sold milk last month; (d) I visited the mandi in October.
   - List B: the same four, plus (e) I burnt straw on at least one plot last season.
