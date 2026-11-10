# Day 3 (Mon 10 Nov) — Measuring burning from satellites

> Reading time: about 35 minutes. This is the hardest day and the step with the most twists. Days 1–2 built the peer groups. Today: how we got **one burning number per tehsil per year**, the big problem we hit (ploughed fields look burnt), and how we solved it well enough.

---

## 1. Satellite basics you need (nothing more)

- **Sentinel-2**: a free European satellite pair. It photographs every place in Punjab about **every 5 days**. Each pixel covers **10–20 m** on the ground.
- **Bands**: it records not just red/green/blue but also invisible light (near-infrared, short-wave infrared). Burnt ground, green crops, straw and soil reflect these differently.
- **Index**: a simple formula combining bands into one number that highlights something (greenness, burn scars, brightness).
- **Clouds**: a cloudy picture is useless. Each picture comes with a cloud/shadow label per pixel, which we use to keep only **clear looks**.
- **Google Earth Engine (GEE)**: Google's free platform where these images live. We send it a request ("give me these bands at these points on these dates") instead of downloading terabytes.
- **Ground truth**: fields whose real status (burnt / not burnt) is known independently. It is what we score a detector against.

## 2. Why not just count fires?

NASA's fire satellites (VIIRS/FIRMS) detect **heat at the moment they fly over** (around 1:30 pm). Paddy fires are small and short, and farmers increasingly burn **after** the satellite has passed. Studies find fire counts miss most burnt area (about 3.7× undercount in Punjab). Official fire counts fell ~85% between 2021 and 2024, partly because of this dodging. So fire counts are kept only as a **cross-check**, not as our measure. We measure **burn scars** (the charred field) instead.

## 3. The first detector: BAIS2 + TCB (worked on paper)

- **BAIS2**: a published burn index, sensitive to burnt material. **TCB** (Tasseled Cap Brightness): overall brightness; burnt fields are darker.
- Tested on **CEEW ground truth**: 438 fields near Jalandhar (2021) and Sangrur (2020), labelled burnt/unburnt by CEEW experts from very-high-resolution Google Earth images.
- A simple boundary (logistic regression) on BAIS2 + TCB was correct **95.5%** of the time and caught **98%** of burnt fields. The standard index NBR did worse (81%), because harvesting alone changes a field's appearance a lot.

That looked solved. It was not.

## 4. The big problem: ploughed soil looks like ash

The CEEW test used **one picture per field, on the day CEEW looked**. To measure a whole season we must look at **every clear picture from mid-September to November**. When we did that:

- **95% of random cropland spots in Punjab got called "burnt" at least once** in 2022. Punjab does not burn 95% of its fields.
- The reason: after harvest, farmers who do **not** burn plough the straw in or sow wheat. **Freshly ploughed, moist soil is dark**, like ash. In Sentinel-2's colours, ash and ploughed soil are almost identical (BAIS2 could separate them no better than a coin toss: score 0.51, where 0.5 = chance).
- Confirmed on proper ground truth (**Walker et al. 2022**: Punjab 2019, 2,204 field-verified burnt and 223 ploughed-not-burnt fields): the detector called **98% of burnt fields burnt and also 81% of ploughed fields burnt**.

**Why this is fatal for DPPD:** the positive deviants we are looking for are exactly the places where farmers **plough instead of burning**. A detector that calls ploughing "burning" would make them look like burners and hide them.

## 5. What we tried (and why each failed)

| Attempt | Idea | Result |
|---|---|---|
| Label by eye on Sentinel-2 | Soham marks burnt vs ploughed on 60 spots | Not possible: at 10 m they look the same |
| Shorter season window | Stop before ploughing starts | Ploughing and burning overlap in time; window fixed to the official 15 Sep–30 Nov season instead |
| **Heat** (Prof. Aaditeshwar's idea) | Fire is hot, ploughing is not. Use satellite temperature (Landsat, MODIS) and look for a heat peak | Over-flagging fell from 95% to ~56%, but the rule always finds *some* peak each year, so it can never say "no fire here". Still about half of ploughed fields called burnt |
| **Radar** (Basma's idea) | Ploughing makes soil rough, which radar sees | Radar passes only every 12 days; on probably-ploughed fields the signal went the *opposite* way |
| Better formulas / literature | Other thresholds and indices | Others hit the same wall; their ground truth never included ploughed fields |

## 6. The key insight: ash fades in 2–3 days

Looking at **daily PlanetScope** pictures (3 m pixels, a commercial satellite; we got free academic access): a burnt field turns **pure black** for only **2–3 days**, then fades towards the colour of ploughed soil.

- Sentinel-2 comes every 5 days and is often clouded, so it usually sees **faded** ash. That is why it confuses the two.
- Daily Planet catches the black days. On Walker's fields, a simple Planet rule ("did the field suddenly get much darker than the week before?") caught 90% of burns while calling only **9%** of ploughed fields burnt.
- But Planet is limited: our free quota is 3,000 km² per month (and each picture is charged as at least 100 km²). Punjab is 50,000 km². So Planet **cannot measure all tehsils**. It is used to **teach and to check** the Sentinel-2 detector.

## 7. The final detector (5 steps)

Professor's suggestion: *train Sentinel-2 with the help of a better source, and show it works on one area.* The final pipeline:

1. **Flag**: the old BAIS2 + TCB score marks every clear look that *might* be an event (burnt **or** ploughed).
2. **Pick the candidate**: the look with the **largest jump** in the score from the previous look. Burning is sudden; drying and harvest are gradual.
3. **Before vs after**: compare the candidate look with the **one clear look just before it**, on 9 bands and 5 indices.
4. **Decide**: a **random forest** answers "burnt or ploughed?". A random forest is many simple yes/no decision trees, each trained on a slightly different slice of data, that **vote**; the share of votes is a 0–1 probability. It was trained on **Walker's field-verified burnt vs ploughed fields**.
5. **Cut-off**: call it burnt if the probability ≥ **0.79** (strict, main setting). A loose cut of **0.5** is run as a sensitivity check.

### How well it works

| Test | Old detector | Final (cut 0.79) |
|---|---|---|
| Walker 2019: burns caught | 98% | **90%** |
| Walker 2019: ploughed called burnt | 81% | **18%** |
| Jalandhar 2021 (new year and place, not retrained), judged by Planet: not-burnt fields called burnt | 23 of 32 | **0 of 32** |
| Jalandhar 2021, judged by CEEW: burns kept | 257 of 262 | 89 of 262 |

**The trade-off:** false alarms almost disappear, but the strict setting **misses many burns**, mostly **partially burnt** fields. We accept this because for ranking tehsils, **missing some burns everywhere** does less harm than **counting ploughing as burning** (which specifically punishes the good tehsils). This assumes the misses are similar across tehsils; that assumption is stated, not proven.

## 8. From fields to one number per tehsil

| Choice | What we did | Why |
|---|---|---|
| Where to look | **100 fixed random rice points per tehsil** (rice in both the 2020 and 2022 rice maps); the same points every year | Keeps the work manageable for 97 tehsils × 6 years, and the same points make years comparable |
| How big a spot | **A single 20 m pixel** at each point | Fields are small (half under 0.42 ha). Bigger squares mixed in neighbouring fields and paths and missed more burns |
| Season | **15 Sep – 30 Nov** | The official stubble-burning season (ISRO protocol used by the government's CAQM) |
| Years | 2019–2024 measured; **2020–2024 used for PDs** | Five seasons, so a PD must be consistently good, not lucky once |
| The number | **Burnt share** = share of a tehsil's points judged burnt that season | A point with no usable clear picture is "unknown" and left out (almost all points got a verdict: typically 100 of 100, worst 70) |

Output: `outputs/burn_tehsil_rf/tehsil_burn_measure.csv`. Maps: Fig. G (burn map), Fig. H (vs fire counts).

## 9. Is the tehsil number believable? (checks)

| Check | Result | Reading |
|---|---|---|
| Official CREAMS district figures, 2022 (till 24 Oct) | Rank agreement **ρ 0.87**; state 7.8% vs official 9.9% | Strong |
| VIIRS fire counts, tehsil ranks | ρ **0.78–0.87** (2019–2023), 0.51 in 2024 | Strong; the old heat-peak version managed only 0.1–0.3 |
| Year-to-year stability of tehsil ranks | ρ **0.82–0.91** (0.62 into 2024) | Burning habits are local and lasting, as expected |
| Strict (0.79) vs loose (0.5) cut | Tehsil ranks ρ 0.84–0.98 | The cut changes the *level*, not the *order* |

(ρ = rank agreement: 1 = same order, 0 = unrelated.)

**Weak spots (state them openly):**
- **2019 level** too high vs official (59% vs 37%); the official method changed between 2019 and 2020. 2019 is not used for PDs.
- **2020 district order** agrees less (ρ 0.50).
- **2024 looks different**: 72% of its burns are first seen in the second half of November (other years 10–32%), and agreement drops. Either a genuinely late harvest or ploughing false alarms. So PDs are also run on **2020–2023 without 2024** (Day 4).
- **Partial burns** are under-counted; **ploughing false alarms at single-pixel level** were not testable here.

**Burnt share by group** (area-weighted, typical year): Central ~55–65%, South-west ~60–70%, Foothills ~20–30%.

### Why the Foothills are left out of PD identification
Earlier versions **over-counted** burning in the Foothills. Even with the best data, **no source ranks foothill burning consistently**: the official figures themselves jump between years (SAS Nagar 5% → 29% → 2.5%), and there is very little burning there in any source. So the 15 Foothill tehsils are **measured** (so state totals add up) but **not ranked** for positive deviance. PD identification uses **81 tehsils**: Central 63 + South-west 18.

---

## Questions you may get (and how to answer)

**Q1. Why not just use the government's (CREAMS) burnt-area data?**
It is published only per **district** (too coarse for tehsil PDs), the full-season area exists only for some years, and its method changed in 2020. We use it as a **check**, not as the measure.

**Q2. Why not fire counts? They are official and simple.**
They miss most small fires and are increasingly dodged by burning after the satellite passes. A tehsil that learnt to dodge would look like a positive deviant. We use them only as a cross-check.

**Q3. 18% of ploughed fields still called burnt. Is that acceptable?**
It is down from 81%. No free satellite separates them perfectly; even daily Planet gets 9%. For ranking tehsils it is good enough, and it is a stated limitation.

**Q4. You miss many burns at the strict cut. Doesn't that bias results?**
It lowers the **level** of burning everywhere. Rankings barely change between the strict and loose cuts (ρ 0.84–0.98). The risk would be if misses were *much* higher in some tehsils (e.g. where partial burning is common); that is untested and stated.

**Q5. The model was trained on 2019 Walker fields. Does it work in other years and places?**
We tested it on a different year and place (Jalandhar 2021) **without retraining**, judged by two independent sources (Planet and CEEW). False alarms stayed near zero. It is still only one extra place, which we state.

**Q6. Why 100 points per tehsil and not every field?**
Cost and time on a free platform for 97 tehsils × 6 years. 100 points give a sampling error of roughly ±5 percentage points, small compared with the differences between tehsils.

**Q7. Why not use Planet for everything since it works best?**
Quota: 3,000 km² a month vs 50,000 km² of Punjab, with each picture charged as at least 100 km². With more quota, Planet could measure a tehsil directly: future work.

**Q8. Why drop the Foothills? Aren't they the lowest burners?**
They burn least *because of* their conditions (little paddy, wet, small fields), which is why they are their own group. But we cannot rank tehsils *within* that group reliably with any data source, so we do not claim PDs there.

**Q9. Suggestion: "Use machine learning on all bands from the start."**
We did try richer feature sets and classifiers on Sentinel-2 alone. They could not separate ash from soil, because the information is not in a picture taken days after the burn. The fix was **timing** (catch the jump, compare with just before) plus **better training labels**, not a fancier model.

---

## Say it in one minute

"We measure burning from Sentinel-2 burn scars, not fire counts, because fire counts miss small fires and farmers now burn after the satellite passes. Our first detector, BAIS2 plus brightness, was 95% accurate on single-date test fields, but across a whole season it called freshly ploughed soil 'burnt'. That is fatal for DPPD, because tehsils that plough instead of burning are exactly the positive deviants. Daily Planet images showed that ash is black for only 2–3 days. So we rebuilt the detector: it finds the sudden jump in the burn score, compares it with the picture just before, and lets a random forest trained on field-verified burnt-versus-ploughed data decide. Ploughing false alarms fell from 81% to 18%. We then scored 100 rice points in every tehsil, every season from 2019 to 2024. The resulting tehsil ranking agrees with official district figures (ρ 0.87) and with fire counts (ρ 0.78–0.87), and is stable from year to year. The Foothills are measured but not ranked, because no source ranks burning there reliably."

---

**Tomorrow (Day 4, last):** using these burn numbers inside each group to find the positive deviants: the rules, the result (Abohar), and what is still uncertain.
