# CHAT_ARCHIVE.md
_Summaries of important discussions, reconstructed from project notes, **not verbatim transcripts**. The earlier chat text was not available to the assistant that wrote this. To make this a true archive, paste key excerpts under the matching headings (marked **[PASTE]**). Append-only; newest at the bottom._

## 1. Method foundations (Aug–Sep 2026)
- **Original design skipped Homogeneous Grouping.** Basma's feedback: this is an official DPPD step; team incorporated it. Her critiques map to canonical pipeline requirements, not preferences.
- **Burn index selection.** NBR pre/post failed because harvest causes a huge spectral shift. BAIS2 first looked poor; cause was an implementation bug (simplified two-band formula instead of Filipponi red-edge). With correct BAIS2 + TCB, accuracy 95.53%. FIRMS/VIIRS dropped (3.67x undercount). **[PASTE: validation outputs]**
- **Prof. feedback on update presentation:** "good clarity on methodology"; no other concerns.
- **Resolution mismatch.** Block-level groundwater, district-level zones, village-level rice could not be grouped until Prof. approved mixed-resolution inheritance. Soham's principle: collect at the finest resolution, then let grouping design adapt.

## 2. Data collection (Sept 2026)
- **Rice 2022 staleness.** 98.6% of Punjab villages had 2022 = 2020. A standalone `village_rice_2022.csv` was byte-identical, proving the source is stale. Decision: generate 2022–24 via Sentinel-1 SAR. Spot checks: Ludhiana village 78.8%; Fazilka `034223` 87.1% vs official 71.3% / 69.8%. Soham had assumed Fazilka was low-rice; the data corrected the stereotype. First attempt used wrong district codes (guessed 051/052/056; correct Ludhiana/Patiala/Sangrur = 041/048/053). **[PASTE: SAR script + charts]**
- **Merge validation.** Majority-area-overlap rule for multi-zone villages; Punjab-only scope; open: Tarn Taran / SBS Nagar zero zone data (969 villages), Fatehgarh Sahib drainage gap (104 villages), 8 missing villages. ID-vintage mismatch blocked merging.
- **Agro-climatic plan.** Soham proposed building the component from separate variables (rainfall, temperature, terrain, water) because NARP zones are district-based and would group dissimilar tehsils. Rainfall via CHIRPS; 15-yr window chosen over WMO 30-yr.
- **Tehsil CI pipeline.** Separate satellite pipeline so a deviant tehsil is not hidden in a district average. Sum-then-divide rule. 45-tehsil mean 204.6%; belts above baseline; six high-swing tehsils.
- **Soil.** HARSAC ruled out; NBSS&LUP Bhoomi WFS chosen.

## 3. Grouping session with ChatGPT context files (3 Oct 2026)
- ChatGPT produced the six-dimension design, Gower+HAC, Dhar Kalan outlier, 25/14/55/2 → 25/14/57, silhouette 0.287, bootstrap ARI 0.572, sensitivity results. **No code was provided**, so everything must be rebuilt. **[PASTE: ChatGPT context files + any code]**
- Soham decisions: rainfall 5-yr prototype then ~15-yr; dropped temperature (guessed no effect); keep Chen rice (structural trait); switch rice to share of tehsil area; drop any useless variable because it distorts distances; groundwater year undecided. Soham is new to clustering and wants steps explained.
- Master files and rice-script provenance recorded (Chen 2022 GeoTIFF over LGD tehsil polygons, not village CSVs).
- Advisor question deck prepared: rice snapshot vs SAR extension, groundwater year, replacing zones, equal weights, Punjab-only scope, follow-up call.

## 4. Handoff (5 Oct 2026)
- Soham asked for a handoff pack for Claude Code. Target: finish whole project by end of 22 Oct 2026.
- Pack: `CLAUDE.md`, `project_tracker.md`, `PROJECT_OVERVIEW.md`, `METHODOLOGY.md`, `DECISIONS.md`, `DATA_INVENTORY.md`, `CURRENT_STATUS.md`, `CHAT_ARCHIVE.md`.
- Soham's working preference: review proposed document changes as markdown diffs before they are applied.
