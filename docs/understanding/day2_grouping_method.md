# Day 2 (Sun 9 Nov) — How the groups are formed and checked

> Reading time: about 30 minutes. Yesterday: *why* we group and the 5 facts per tehsil (rice share, rainfall, zone, groundwater, soil). Today: how a computer turns those facts into groups, why we stopped at **3 groups**, and how we checked they are real.

---

## 0. The whole method in 5 steps

| Step | Question it answers | Tool (name to remember) |
|---|---|---|
| 1 | How different are two tehsils? | **Gower distance** (a 0-to-1 score) |
| 2 | Which tehsils belong together? | **Hierarchical clustering** (builds a family tree) |
| 3 | How many groups? | Cut the tree; score each cut with the **silhouette** |
| 4 | Are the groups a fluke? | **Bootstrap**: redo it 300 times on 80% samples, compare with **ARI** |
| 5 | Do the groups depend on our choices? | **Sensitivity**: change one choice at a time |

Everything runs in code (`Code/grouping/`), so every number can be reproduced. An earlier attempt with ChatGPT (3 Oct: groups of 25/14/57) had no code behind it; we could not reproduce it, so it was discarded.

---

## 1. Step 1 — One "difference score" for every pair of tehsils

The problem: our five facts are in different units. Rainfall is in mm (hundreds), rice share is a fraction (0–1), soil is words ("Loamy", "Sandy"). You cannot just subtract and add them.

**Gower distance** solves this in three moves:

1. **Put every number on the same 0–1 ruler.** Divide the difference by the full spread across Punjab. Rainfall runs from 310 to 1,281 mm, a spread of 971 mm. A 314 mm difference is 314 / 971 = **0.32** of the full spread.
2. **Words: same = 0, different = 1.** "Loamy" vs "Loamy" = 0; "Loamy" vs "Sandy" = 1.
3. **Average.** First average inside each dimension, then average the five dimensions. Each dimension gets **one equal vote (1/5)**, whether it has 1 column (rainfall), 4 columns (zone shares) or 8 columns (soil). Without this, soil's 8 columns would outvote rainfall's 1.

### A real worked example: Ajnala (Amritsar) vs Talwandi Sabo (Bathinda)

| Dimension | Ajnala | Talwandi Sabo | Difference ÷ spread | Score |
|---|---|---|---|---|
| Rice share | 0.695 | 0.571 | 0.124 ÷ 0.683 | 0.18 |
| Rainfall | 778 mm | 464 mm | 314 ÷ 971 | 0.32 |
| Zone (4 shares) | 100% zone 9.1 | 100% zone 2.5 | 2 of 4 shares differ fully | 0.50 |
| Groundwater | 161% | 78% | 82 ÷ 372 | 0.22 |
| Soil (8 properties) | Coarse-loamy, … | Fine-loamy, … | 1 of 8 differ | 0.13 |
| **Average of the 5** | | | | **0.27** |

So the two tehsils are 0.27 apart: fairly different. Ajnala vs its neighbour Lopoke scores **0.014**: almost identical. This is done for all 97 × 97 pairs and stored as a table (`outputs/grouping/dist_baseline.csv`).

**Good sign:** each tehsil's closest matches are its geographic neighbours, even though the method was never told where any tehsil is.

### The Dhar Kalan decision
Dhar Kalan (Pathankot) is a hill tehsil unlike any other: 1,604 mm rain, 7% rice. It sets the extreme value for several variables. If it set the ruler, everyone else's differences would shrink by ~12% (because the spread would be stretched by one odd case). So **Dhar Kalan is left out when measuring the spread**, but it stays in the data. Later it is set aside as an **outlier**: it joins the tree last, far from everyone, and is reported separately rather than ranked.

---

## 2. Step 2 — Building the family tree (hierarchical clustering)

**How it works**, like building a family tree from the bottom up:
1. Start with every tehsil alone.
2. Find the two closest tehsils (or groups) and join them.
3. Repeat until everything is one big group.

The result is a tree (a **dendrogram**, Fig. B): tehsils that join low down are very similar; branches that join high up are very different.

**"Average linkage"** decides how far apart two *groups* are: the average of all tehsil-to-tehsil distances between them. It is the middle option. "Single linkage" (closest pair only) tends to form long chains; "complete linkage" (farthest pair) is very strict. Average linkage is the common default with Gower distance.

**Why this method and not the famous "k-means"?** k-means needs to compute an "average tehsil", which is impossible with soil words like "Loamy". Hierarchical clustering only needs the pairwise distance table, so it works with mixed data. It also shows the whole structure at once (the tree), and the professor endorsed it.

**What the tree showed** (without ever seeing a map): the Siwalik **foothill belt** splits off clearly, then the **dry south-west**, and the rest forms the **central plains**. Dhar Kalan joins last of all.

---

## 3. Step 3 — How many groups? (silhouette)

Cutting the tree at different heights gives 2, 3, 4… groups. We need a way to choose.

**Silhouette** asks, for each tehsil: *am I clearly closer to my own group than to the next-nearest group?*
- a = my average distance to my own group; b = my average distance to the nearest other group.
- s = (b − a) ÷ the larger of the two.
- s near **1**: clearly in the right group. Near **0**: on the border. **Below 0**: closer to another group (probably misplaced).
- Example: a = 0.15, b = 0.25 → s = 0.10 ÷ 0.25 = 0.40.

The **mean silhouette** over all tehsils scores the cut. Caution: fewer groups always look "cleaner" (one huge group + one small one is trivially clear), so silhouette is read together with group sizes and whether the groups make sense.

**Two extra rules:**
- **Minimum group size 5.** A group of 2 tehsils cannot host a "who burns less than peers" comparison. Members of tiny groups are moved to the nearest big group.
- **Dhar Kalan set aside** before cutting.

---

## 4. Step 4 — Is it a fluke? (bootstrap + ARI)

**Bootstrap:** hide a random 20% of tehsils, redo the *entire* procedure on the remaining 80% (including re-measuring the spreads), and see whether the same tehsils still end up together. Repeat **300 times** (fixed random seed 42, so it is reproducible).

**ARI (Adjusted Rand Index)** compares two groupings by looking at **every pair** of tehsils: are they together in both, or apart in both (agree), or together in one and apart in the other (disagree)?
- Example with 4 tehsils A, B, C, D. Run 1: {A,B} {C,D}. Run 2: {A,B,C} {D}. Of the 6 pairs, 3 agree (AB together; AD, BD apart) and 3 disagree. Raw agreement = 50%.
- But random groupings already agree on many pairs by luck. ARI **subtracts the luck**: here ARI = **0**, i.e. no better than chance. ARI = 1 means identical groupings.
- Rough reading: above 0.8 very stable; 0.6–0.8 fairly stable; below 0.5 weak.

**Two finer measures** added later:
- **Group survival:** in what share of the 300 runs does each group still appear as its own group?
- **Switching rate:** when a tehsil's group survives, how often does *that tehsil* end up in a different group? A tehsil switching in ≥ 20% of runs is flagged **borderline**.

**Consensus placement:** each tehsil is finally put in the group it lands in **most often** across the 300 runs, not just in the single full-data tree. (In the final version this made no difference: consensus = tree.)

### Results for the final design (`outputs/grouping/stability_by_k.csv`, Fig. D)

| Cut | Group sizes | Silhouette | ARI (mean) |
|---|---|---|---|
| 2 groups | 81 / 15 | 0.409 | **0.981** |
| **3 groups (chosen)** | **63 / 18 / 15** | **0.377** | **0.890** |
| 4–5 | same 3 groups (small pieces merged back) | 0.377 | 0.87 / 0.77 |
| 6 | 48 / 18 / 15 / 15 (central splits) | 0.348 | 0.71 |

**Why 3 and not 2?** 2 groups are slightly more stable, but they would put Bathinda (464 mm rain, cotton–paddy belt) in the same group as Ludhiana. 3 groups give the dry south-west its own peers and are still very stable (ARI 0.89). Beyond 3, the central plains start splitting and stability drops.

---

## 5. Step 5 — Does it depend on our choices? (sensitivity)

We changed **one choice at a time** and measured ARI against the final grouping (`sensitivity_table.csv`, Fig. E):

| Change | Result |
|---|---|
| Each dimension's weight ±15% (10 of 12 runs) | ARI ≥ 0.83; at most a few border tehsils move |
| Rice or soil weight +15% | ARI ~0.5: the south-west merges back into central |
| Drop any one dimension | ARI 0.48–0.60: the south-west merges into central |
| Drop near-constant soil properties | ARI 0.97: almost no change |

**How to read it:** the **foothills vs plains** split survives every test. The **south-west vs central** border is real (it shows in rainfall, zone and groundwater together, which is why dropping any one of them dissolves it) but **gradual**: Malwa shades from central to south-west rather than meeting at a sharp line. This is why we also keep the 2-group version (Plains = Central + South-west, Foothills) as a cross-check on every positive deviant (Day 4).

**Equal weights:** we had no basis to say rainfall matters more than soil, so each dimension gets 1/5. The sensitivity test is our defence: moderate weight changes barely move the groups.

---

## 6. The final frozen grouping (7 Oct, version 4)

| Group | Tehsils | Median rice share | Median monsoon rain | Median groundwater use | Character |
|---|---|---|---|---|---|
| **Central** | 63 | 75% | 721 mm | 230% | Paddy-heavy plains, most over-pumped water |
| **South-west** | 18 | 59% | 467 mm | 118% | Dry cotton–paddy belt |
| **Foothills** | 15 | 28% | 981 mm | 117% | Wet, hilly Kandi belt |
| Outlier | Dhar Kalan | 7% | 1,604 mm | 27% | Set aside |

- **South-west (18):** Abohar, Bathinda, Budhlada, Faridkot, Fazilka, Firozpur, Gidderbaha, Guruharsahai, Jaitu, Jalalabad, Kotkapura, Malout, Mansa, Maur, Rampura Phul, Sardulgarh, Sri Muktsar Sahib, Talwandi Sabo.
- **Foothills (15):** Anandpur Sahib, Balachaur, Chamkaur Sahib, Dasua, Dera Bassi, Garhshankar, Hoshiarpur, Kharar, Morinda, Mukerian, Nangal, Pathankot, Rup Nagar, SAS Nagar, Tanda.
- **Central (63):** all the rest.
- **Group survival:** Central 100%, Foothills 100%, South-west 94% of runs.
- **Borderline (3):** Firozpur (switches 43%), Dinanagar (31%), Faridkot (24%).
- **Strongest evidence it is real (Fig. A):** the three groups form **connected regions on the map**, matching Punjab's known belts, although location was never an input.

### How we got here (versions)

| Version | What changed | Groups |
|---|---|---|
| ChatGPT, 3 Oct | No code | 25 / 14 / 57, not reproducible, discarded |
| v1, 6 Oct | Zones replace broken terrain | 66 / 16 / 14 |
| v2, 7 Oct | Rice share calibrated to official totals | 58 / 22 / 16 |
| v3, 7 Oct | Consensus placement (5 border tehsils back to Central) | 63 / 17 / 16 |
| **v4, 7 Oct (final)** | Unreliable cropping intensity dropped | **63 / 18 / 15** |

Each change fixed a data problem, and each made the result more stable (v4: only 3 borderline tehsils, down from 9).

---

## Questions you may get (and how to answer)

**Q1. Silhouette 0.377 sounds low.**
On a −1 to 1 scale, 0.25–0.5 is normally read as "reasonable structure". Real places change gradually, so very high values are rare. We do not rely on silhouette alone: stability (ARI 0.89) and the map both support the groups.

**Q2. Why equal weights? Isn't that arbitrary?**
Any weighting is a choice; equal is the neutral one when there is no evidence for another. We tested ±15% on each dimension: 10 of 12 changes barely move the groups. The honest weak spot is the south-west border, which we state.

**Q3. Why not k-means / DBSCAN / other methods?**
k-means cannot handle categorical soil data. Hierarchical clustering works directly on Gower distances, shows the full structure, and was endorsed by the supervisor. A comparison with other algorithms could be future work.

**Q4. Why exclude Dhar Kalan? Isn't that cherry-picking?**
It is not removed from the data; it is reported separately. One extreme hill tehsil has no real peers, so ranking it against plains tehsils would be unfair to both. Leaving it out of the "ruler" stops it from shrinking everyone else's differences.

**Q5. How do you know the groups are not just random?**
Three independent signs: (1) the same groups reappear in ~9 of 10 random 80% samples (ARI 0.89); (2) they form connected regions on the map without using location; (3) they match Punjab's known agro-ecological belts.

**Q6. The south-west disappears when you drop any one variable. Doesn't that make it fragile?**
It shows the south-west is defined by several facts together (dry, arid zone, lower water stress), not by one. But yes, the border is gradual. That is why every positive deviant is also checked under the simpler 2-group version.

**Q7. Why minimum group size 5?**
Positive deviance means "much better than peers". With 2–3 peers there is no meaningful "normal" to deviate from. 5 is a practical minimum.

**Q8. Suggestion: "Use more groups for finer comparison."**
At 6 groups the central plains split and stability drops to ARI 0.71, and smaller groups make "unusual" harder to judge. If pressed, you can offer it as a sensitivity check.

**Q9. Suggestion: "Weight rice share higher, it is the main driver of straw."**
Can be argued. Our test: rice +15% merges the south-west back into central. So a higher rice weight is effectively the 2-group version, which we already run as a cross-check.

---

## Say it in one minute

"For each pair of tehsils we compute a 0-to-1 difference score, the Gower distance. It puts rainfall, rice share, groundwater, zone shares and soil on a common scale and gives each of the five dimensions an equal vote. Hierarchical clustering then joins the most similar tehsils step by step into a tree. We cut the tree into three groups: central plains (63), dry south-west (18) and Siwalik foothills (15), with the hill tehsil Dhar Kalan set aside. We checked this by redoing everything 300 times on random 80% samples: the groups reappear about 90% of the time (ARI 0.89). We also changed each weight by 15%: the groups barely moved. The groups form connected regions on the map although location was never used. The one soft spot is the gradual south-west/central border, so every positive deviant is also checked under a simpler two-group version."

---

**Tomorrow (Day 3):** how we measure burning from satellite images. Why freshly ploughed fields look like burnt ones, how we got around it, and how one burn number per tehsil per year was built and checked.
