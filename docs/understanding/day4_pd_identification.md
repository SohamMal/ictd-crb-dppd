# Day 4 — Finding the positive deviants

> Reading time: about 30 minutes. Last day. You now have peer groups (Days 1–2) and a burnt share per tehsil per season (Day 3). Today: the rules that turn those numbers into a list of positive deviants (PDs), what the list says, and how far to trust it.

---

## 1. Who is compared with whom

- **81 tehsils** are ranked: **Central 63** and **South-west 18**. Each tehsil is compared **only with its own group**.
- **Foothills (15)** are measured but not ranked: no data source ranks burning there reliably (Day 3).
- **Dhar Kalan** (outlier) has no peers, so it is not ranked.
- **Seasons:** 2020–2024 (five seasons). 2019 is not used (weak level, official method change).

Every rule is a **direct comparison within the group**. We use no regression "residuals" (predicted-vs-actual leftovers), as the supervisor required.

## 2. Two kinds of "positive deviant"

| Kind | Question | Why it matters |
|---|---|---|
| **Static** | Who burns **far less** than its group, on average over 5 seasons? | The classic DPPD question |
| **Temporal** | Who **cut burning faster** than its group over 2020–2024? | Suggested by Basma. Each tehsil is compared with its own past, so fixed things we could not measure (soil, farm size, local officials) cancel out |

A tehsil good on **both** is the strongest PD. **Negative deviants (NDs)** are the mirror image (burn far more, or rising fastest). They are the contrast group for Stage 3: *what do PDs do that NDs don't?*

## 3. The statistics you need

**Quartiles and IQR.** Sort a group's values from low to high. **Q1** is the value one quarter of the way up, **Q3** three quarters up. The **IQR** (inter-quartile range) = Q3 − Q1 is the spread of the "middle half" of the group: what counts as normal.

**The outlier fence (from the DPPD handbook, pp. 63–66).** A value below **Q1 − 1.5 × IQR** is far outside the normal spread. This is the standard box-plot outlier rule, and Basma used it in her Egypt project. A tehsil beyond this fence is a **PD**, not merely "low".

**Why a log scale?** On the raw burnt-share scale the fence fell **below zero** (dry run: −5.76 on fire counts), because a few tehsils burn very heavily and stretch the IQR. Burning cannot go below zero, so nobody could ever be a PD. On a **log scale**, *halving* burning counts the same at any level (0.6 → 0.3 is the same step as 0.2 → 0.1). Then the fence sits at a sensible place.
- Small detail: we take log(value + c), with **c = 10% of the group median**. The c avoids log(0) for a tehsil with zero burning.

**The resulting fences on burnt share:**

| Group | Group median | PD fence (2020–24) |
|---|---|---|
| Central | 0.61 | **0.225** |
| South-west | 0.73 | **0.454** |

So in Central, a tehsil must average under about 22% burnt to be a strict PD, against a typical 61%.

**Theil–Sen slope (for the temporal trend).** For 5 seasons there are 10 pairs of years. Compute the slope for each pair and take the **median**. One odd season cannot drag the trend, which an ordinary trend line would allow with only 5 points. Because it is on the log scale, the slope reads as **"% change per year"**.

## 4. The rules

**Static PD:**
1. The tehsil's 5-season average (log scale) is **below the fence**, **and**
2. **Consistency:** it is in the group's lowest quarter in **at least 4 of 5 seasons**. One lucky season cannot make a PD.

**Temporal PD:** take the tehsil's trend minus the **group's median trend**. A PD has a deviation below the fence of the group's deviations, i.e. it falls much faster than its peers. It is reported as "% per year faster than the group".

**Candidate PD:** in the **bottom 10%** of the group (and consistent), but not beyond the fence. Soham's point: "bottom 10%" only says a tehsil is *among the lowest*; it does not show it is *far from normal*. So candidates are a weaker tier.

**NDs:** the mirror image (above Q3 + 1.5 × IQR; top quarter; top 10%).

### Robustness: run everything twice

Because the 2024 season looks odd (Day 3), every rule is run on:
- **Main:** 2020–2024
- **Sensitivity:** 2020–2023 (without 2024)

Then two labels are reported side by side:
- **Strict rule (headline):** beyond the fence in **both** runs. *Borderline* = beyond the fence in one run and a candidate in the other.
- **Old rule (broader "low-burning" set):** PD or candidate in both runs.

**Grouping check:** the rules are also run with Central + South-west merged into one "Plains" group (the 2-group version from Day 2). This is **reported**, not used to drop anyone.

## 5. Results

### Strict rule (the headline)
- **Abohar (South-west) is the only strict PD.** It is the lowest burner in its group (average 0.34 vs group median 0.73), beyond the fence in both runs. It is also among the fastest reducers (−11%/yr vs group; borderline under the strict temporal rule). **It is the only tehsil good on both kinds.**
- **Borderline PDs:** **Dinanagar** (lowest burner in Central at 0.21; misses the 2020–23 fence by 0.001) and **Samana** (fast reducer; misses one fence by 0.3%/yr).
- **No strict ND.** Malout (rising fastest) is a borderline ND.

### Old rule (the broader low-burning set)

| Tehsil | Group | Kind | Avg burnt share | Trend vs group |
|---|---|---|---|---|
| Abohar | SW | static + temporal | 0.34 | −11.1%/yr |
| Dinanagar | Central | static | 0.21 | +6.5%/yr |
| Gurdaspur | Central | static | 0.29 | +2.3%/yr |
| Phagwara | Central | static | 0.30 | +6.0%/yr |
| Adampur | Central | static | 0.30 | −4.9%/yr |
| Jalandhar-I | Central | static | 0.31 | −1.4%/yr |
| Banga | Central | static | 0.34 | +5.6%/yr |
| Talwandi Sabo | SW | static | 0.50 | +14.5%/yr |
| Samana | Central | temporal | 0.63 | −9.1%/yr |
| Dirba | Central | temporal | 0.71 | −8.2%/yr |

**Negative deviants:** static Lehra, Zira, Moonak (Central) and Guruharsahai (SW), burning 0.79–0.90; temporal Batala, Majitha (Central) and Malout (SW), rising 8–10%/yr faster than their groups.

Maps and fences: Fig. I (fences), Fig. J (PD map).

### How to read the results
1. **The Doaba cluster.** Gurdaspur, Phagwara, Adampur, Jalandhar-I and Banga (plus Dinanagar) burn about **half** the Central median. But because they sit **together**, they widen the group's normal spread, and the fence counts them as normal. They are a **low-burning region**, not isolated deviants. This could be structural (e.g. other crop rotations in Doaba), which validation checks.
2. **Static and temporal barely overlap.** Dinanagar burns least but its burning is **rising**; Talwandi Sabo's is rising fastest of all. Only Abohar is good on both.
3. **Not a one-sensor artefact.** 6 of the 8 static PDs were also flagged when the same rules were run on **VIIRS fire counts**, an independent source.

## 6. What happened next (validation, in brief)

Not part of this reading plan, but you will be asked "so are they real?". Validation ran checks in code (`outputs/pd/pd_validated.csv`):
- **Static PDs survive** resampling of the 100 points (kept in ≥ 89% of resamples, except Banga 72%), the loose cut (0.5), a different c, and the other grouping.
- **Temporal PDs mostly do not.** Samana and Dirba keep their flag in only ~40% of resamples, so they are **dropped**. A 5-season trend from 100 points is too noisy, except for Abohar.
- **Rice is the main warning.** Most PDs have less rice than their peers, and burning rises with rice share even inside a group. But when only points with a confirmed paddy harvest are scored, the PDs still burn little (Abohar 0.45 vs group 0.73). So they burn less **on real paddy fields**. The rice gradient is carried into Stage 3.
- **Final list for Stage 3:** validated PDs **Abohar** (static + temporal), **Dinanagar, Phagwara, Jalandhar-I, Adampur, Talwandi Sabo**; with caveat **Gurdaspur, Banga**; contrast NDs **Lehra, Zira, Moonak, Guruharsahai**.

---

## Questions you may get (and how to answer)

**Q1. Why the 1.5 × IQR rule and not "bottom 10%"?**
Bottom 10% always flags someone, even in a group where nobody is unusual. The fence flags only tehsils **far from normal**, which is what "deviant" means. It is the handbook's rule and the one used in Basma's Egypt study. We report the bottom-10% tier too, but labelled as candidates.

**Q2. Only one strict PD. Did the method fail?**
No. It is an honest result: few tehsils are far outside their peers. DPPD does not need many PDs; one well-validated PD plus a clear low-burning cluster is enough to study in Stage 3. Forcing more by loosening the rule would make the list meaningless.

**Q3. Why log scale? Isn't that just to get results?**
On the raw scale the fence was below zero, so no tehsil could ever qualify; the rule was mathematically broken, not strict. The log scale also matches how we think about burning: cutting it by half matters equally whether you start at 60% or 20%.

**Q4. Why not use regression (predict burning from conditions, then find the biggest under-performers)?**
The supervisor ruled out residual-based identification. Peer groups do the "holding conditions equal" job in a transparent way, and every PD can be explained as "it burns X vs its peers' Y".

**Q5. Why drop 2024 in the second run? Isn't that cherry-picking?**
We don't choose one: a tehsil counts only if it holds in **both** runs. That is stricter, not looser.

**Q6. Doaba tehsils burn half as much. Why aren't they PDs?**
Because they are a whole region, not individuals. A region burning less may be explained by structure (rotations, more vegetables or maize). They stay as a "low-burning cluster" for Stage 3 to examine.

**Q7. Abohar is in the cotton belt. Isn't it just less paddy?**
That was the biggest risk. Abohar's rice map needed a large correction. But scoring only points where a paddy harvest was actually seen, Abohar still burns 0.45 vs its group's 0.73. So it burns less on real paddy fields. Remaining risk: cotton fields that happen to pass the harvest test.

**Q8. Temporal deviance was Basma's key suggestion, yet you dropped most of it?**
We kept it in the method, ran it, and validated it. The data could not support it: a 5-season trend is too noisy at this sample size. Reporting that honestly is a finding. Abohar's trend does survive. With more seasons or more points per tehsil, temporal deviance becomes usable (future work).

**Q9. Suggestion: "Use z-scores (below mean − 1 SD) instead."**
Mean and standard deviation are pulled by the heavy burners, which is exactly the problem the IQR rule avoids. You can offer z-scores as a sensitivity check, but the handbook recommends quartile-based fences.

---

## Say it in one minute

"Within each peer group (Central 63, South-west 18) we look for tehsils that burn far less than their peers over five seasons (static), or cut burning much faster than their peers (temporal). 'Far' means beyond the handbook's outlier fence, Q1 minus 1.5 times the IQR, computed on a log scale so that halving burning counts the same at any level. A static PD must also be in its group's lowest quarter in at least four of five seasons. Everything is run with and without the doubtful 2024 season, and a tehsil counts only if it holds in both. The result: Abohar in the south-west is the one strict PD, low on both kinds. Dinanagar and Samana are borderline, and a low-burning Doaba cluster burns about half the central median. Validation kept the static PDs but dropped most temporal ones as too noisy. The final Stage 3 list is Abohar, Dinanagar, Phagwara, Jalandhar-I, Adampur and Talwandi Sabo, contrasted with the heavy burners Lehra, Zira, Moonak and Guruharsahai."

---

**You have now covered grouping → burn measurement → PD identification.** For questions on Stage 3 (why PDs burn less), see `report/report_draft.md` §3.7 and §4.4.
