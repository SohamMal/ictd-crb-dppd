# Day 1 (Sat 8 Nov) — Why we group, and what we group on

> Reading time: about 25 minutes. Tomorrow (Day 2) explains *how* the groups are actually formed. Today is only about *why* we group and *which facts* about each place we use.

---

## 1. Where this step sits in the project

Our project uses **Data-Powered Positive Deviance (DPPD)**. The idea in one line: *in every population there are a few members who do much better than others facing the same conditions; find them, learn what they do differently, and spread it.*

For us the "members" are **tehsils** of Punjab, and "doing better" means **burning less paddy stubble**.

DPPD Stage 2 has four steps:

1. **Measure performance** — how much does each tehsil burn? (Day 3)
2. **Homogeneous grouping** — put tehsils that face the *same conditions* together. (Days 1–2)
3. **Identify positive deviants (PDs)** — inside each group, who burns far less than its peers? (Day 4)
4. Validate them (not part of this reading plan).

## 2. Why group at all? (the most important idea of today)

Think of comparing schools by exam results. A school in a rich city with good labs will score higher than a village school with no teacher for maths. Calling the city school a "positive deviant" would be silly: it is not doing anything clever, it just has better circumstances. The interesting school is the **village school that scores like a city school**, because *it* may be doing something others can copy.

Burning works the same way. The hilly north-east of Punjab (Hoshiarpur, Pathankot) has little paddy, more rain and more small fields. It naturally burns less. If we ranked all 97 tehsils together, these hill tehsils would top the list, and we would "discover" nothing except that hills have less paddy.

So we first sort tehsils into groups of **look-alikes**, and only then ask: *within this group, who burns far less than the rest?* That difference can no longer be blamed on circumstances, so it is more likely due to something people *do*.

### The three hard rules for what may go into grouping

| Rule | Why |
|---|---|
| **Only structural conditions**: things a farmer cannot change or copy (rainfall, soil, how much land is paddy, water table, agro-climatic zone). | These are the "circumstances" we want to hold equal. |
| **Never the suspected causes** (e.g. number of Happy Seeder machines, distance to a mandi, awareness camps). | These are exactly what we hope to *discover* in Stage 3. If we grouped on them, we would hide the very answer we are looking for. |
| **Never burning itself.** | That would be circular: we would build groups using the thing we are trying to compare. |

## 3. The unit: why tehsils?

We had three choices of "place":

| Option | Count | Problem |
|---|---|---|
| Villages | ~12,800 | Too fine. Several datasets do not exist at village level, and a single village's burn number is noisy. |
| Districts | 23 | Too coarse. A district average hides a good tehsil inside it. Some districts also span very different land (Patiala sits in three agro-climatic zones). |
| **Tehsils** ✔ | **97** | The middle ground: fine enough to find good performers, coarse enough for reliable data. |

**The boundary problem.** Old data (Census 2011, the village map we use) is labelled with **2011 codes**, when Punjab had 20 districts. Today Punjab has 23 districts and 97 tehsils. Many tehsils have been split since 2011. Of today's 97: **45 are unchanged, 43 were carved out of an old tehsil, and 9 took villages from several old tehsils.**

So we built **"bridge" tables**: for each village, which *current* tehsil it belongs to. Every dataset first lands on villages (or blocks, or districts) and is then passed to today's tehsils through these bridges. The professor approved this "keep each dataset at its own level and pass it down" approach.

## 4. The five things we group on (final, frozen 7 Oct)

| # | Dimension | What it measures | Why it matters for burning | Source | How it becomes one number per tehsil |
|---|---|---|---|---|---|
| 1 | **Rice share** | Fraction of the tehsil's land that is paddy (7% in hilly Dhar Kalan to 87% in Moonak) | More paddy = more straw to get rid of in a short time | Chen et al. (2024) 10 m rice map for 2022, **calibrated** to government district totals | Count rice pixels in the tehsil, divide by tehsil land area |
| 2 | **Monsoon rainfall** | Average June–September rain, 2020–2025 (310 mm in the dry south-west to 1,600 mm near the hills) | Shapes how much irrigation paddy needs and when it is harvested | CHIRPS satellite rainfall (~5 km) | Average per village, then average of villages |
| 3 | **Agro-ecological zone** | Share of the tehsil's area in each of Punjab's 4 official zones (Siwalik foothills, two semi-arid plains, arid south-west) | Summarises climate + terrain + growing season | NBSS&LUP AESR 2018 zone map | Overlay the zone map on tehsil boundaries; e.g. Amritsar-I = 56% zone 4.1, 44% zone 9.1 |
| 4 | **Groundwater stress (2022)** | Water pumped as % of what is recharged. Over 100% = over-exploited | Paddy here runs on groundwater; Punjab's water-saving law delays transplanting, which pushes harvest later and squeezes the time before wheat | Central Ground Water Board 2022 block report | Each village takes its block's value; tehsil = average of its villages |
| 5 | **Soil** | 8 properties: particle size, drainage, texture, depth, pH, salinity, sodicity, erosion | Affects what grows, drainage, and how easy it is to sow wheat into straw | NBSS&LUP national soil map (1:250,000) | Most common value among the tehsil's villages, per property |

### Small terms used above
- **Pixel / "10 m map"**: a satellite map is a grid of tiny squares. "10 m" means each square is 10 m × 10 m on the ground and is marked rice or not-rice.
- **Calibrated rice share** (important, people may ask): we checked Chen's map against the government's official rice area per district. It was **wrong in a regional way**: it counted too *little* rice in central Punjab (about 10–25% less) and too *much* in the south-west cotton belt (Fazilka 1.7×, Bathinda 1.4×) and the foothills, probably mistaking cotton and maize for rice. So we kept Chen's map only for *how rice is spread between tehsils inside a district*, and scaled each district so its total equals the official figure (e.g. Fazilka ×0.59, Kapurthala ×1.31).
- **Why "share" and not "hectares of rice"?** Hectares mostly tell you how *big* a tehsil is. Share tells you how *paddy-dominated* it is, which is the condition we care about.
- **Why zone "shares" and not one zone label?** 21 tehsils are genuinely split between two zones. A single label forces them into one, and in testing a single yes/no label overpowered everything else (the groups just became the four zones).

## 5. What we tried and dropped (be ready to explain each)

| Dropped | Why it was dropped | Evidence |
|---|---|---|
| **Cropping intensity** (crops per year, ~200% = rice + wheat) | Our satellite measurement was unreliable: it hardly agreed with the government's district figures (rank agreement ρ = 0.18, where 1 = same order, 0 = no relation). | We tested before dropping: removing it moved only 2 of 96 tehsils; replacing it with the official figure gave the same groups. So a correct version would not change the grouping. Listed as future work. |
| **Terrain** (elevation, slope) | The slope data was broken: different tehsils had *exactly* the same slope and zero variation between villages. | Replaced by the agro-ecological zones, which capture hills vs plains from an official source. |
| **District-level agro-climatic zones** | Assigned per district, too coarse (Patiala in three zones). | Replaced by the finer AESR 2018 zone *map*, which cuts across district lines. |
| **Groundwater 2025** | Everything else refers to ~2022; mixing years is inconsistent. Professor fixed 2022. | — |

**A decision that was reversed, and why.** The professor first suggested zones *replace* both rainfall and terrain. We tested it: without rainfall, the dry south-west group disappeared, because the zone map is drawn very coarsely (its "arid" zone also covers 12 wetter central tehsils). Rainfall, measured per village, sees the difference. So zones replaced only terrain; rainfall stayed. We openly accept that zone and rainfall overlap a little.

---

## Questions you may get (and how to answer)

**Q1. Why not include Happy Seeders / CRM machines in the grouping? They obviously matter.**
They may matter, which is exactly why they stay out. They are a *possible cause* of low burning. If two tehsils were grouped because both have many machines, we could never discover that machines explain the difference. Machines are tested in Stage 3.

**Q2. Why not group on farm size or landholding?**
Arguable either way. We treat it as a candidate *explanation* to test in Stage 3, not a fixed condition. If suggested, you can say: "Good point; it is borderline structural. We keep it out so we can test it as a predictor, and we can add it as a sensitivity check."

**Q3. What about harvest date or rice variety (PUSA-44 vs PR-126)?**
Partly a farmer *choice*, so it is a driver, not a structure. Keep out of grouping; study in Stage 3.

**Q4. Isn't groundwater stress caused by farmers' own pumping? Then it is behaviour, not structure.**
It builds up over decades and no farmer can change it in one season or copy it from a neighbour. For our purpose it is a slow-moving condition that shapes the season (through the transplanting law). Fair point to acknowledge.

**Q5. Is the rice map trustworthy?**
Not by itself. We found it is biased by region and corrected the district totals with official statistics. What remains unfixed: errors *inside* a district (cotton fields inside a Bathinda tehsil may still be counted as rice). This is a stated limitation.

**Q6. Rainfall over only 5 years (2020–2025)? Climate normals use 30.**
True; a 15-year window was planned but deferred. It is a stated limitation. The spread between tehsils (310 vs 1,600 mm) is so large that a longer window is unlikely to reorder them much, but we have not tested it.

**Q7. Cropping intensity is central to burning (tight rice→wheat gap). Why drop it?**
Almost all Punjab is rice–wheat (around 200%), so it barely differs between tehsils; our satellite version was unreliable; and two tests showed it does not change the groups. Honest limitation: the official figure is district-level, so we cannot prove a *correct tehsil-level* value would not split some tehsils.

**Q8. Soil comes from a 1:250,000 map. Is that detailed enough?**
No, it is coarse: effectively one soil type per 2011 tehsil, so newly carved tehsils inherit their parent's soil. Stated limitation. Most tehsils share the same soil on several properties anyway.

**Q9. Why didn't you include temperature?**
It was assumed not to differ much across Punjab but never tested. Stated limitation.

**Q10. Why not Haryana?**
Haryana's data was incomplete (e.g. groundwater only as categories, no numbers). Punjab only, for now.

---

## Say it in one minute

"Before comparing burning, we put tehsils into groups of look-alikes, so that a tehsil is judged only against places facing the same conditions. We use 97 current tehsils, translating older 2011 data to today's boundaries with village-level bridge tables. Tehsils are compared on five structural conditions they cannot change: how much of their land is paddy (corrected against official statistics), monsoon rainfall, official agro-ecological zone, groundwater stress, and soil. We deliberately leave out anything that might *explain* low burning, such as machines, and we never use burning itself. Two variables, cropping intensity and terrain, were dropped after we found the data was faulty and tested that dropping them does not change the result."

---

**Tomorrow (Day 2):** how these five facts become a single "how different are two tehsils" score, how the computer builds a family tree of tehsils, why we chose 3 groups, and how we checked that the groups are not a fluke.
