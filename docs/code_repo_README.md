# Finding Places That Burn Less: Positive Deviance in Punjab's Crop Residue Burning

Code for a **Data-Powered Positive Deviance (DPPD)** study of paddy stubble burning in Punjab, India.
We group Punjab's 97 tehsils (sub-districts) into peer groups using only conditions a tehsil cannot change,
measure how much paddy area each tehsil burns from Sentinel-2 imagery, and find tehsils that burn much less
than their peers (positive deviants). We then test candidate explanations using public data.

The full write-up is in [`paper/report.pdf`](paper/report.pdf).

**Authors:** Soham Malvadkar, Aryan Rana. IIT Delhi, course COL7761 (ICT for Development), 2026.
**Supervisor:** Prof. Aaditeshwar Seth.

## Main results

- **Peer groups:** three groups (Central, South-west, Foothills), stable under resampling (adjusted Rand index 0.89).
- **Burn detector:** cuts false alarms on ploughed fields from 81% to 18% while still catching 90% of burns.
  Its tehsil ranking agrees with VIIRS fire counts (Spearman ρ 0.78–0.87, 2019–2023).
- **Positive deviants:** Abohar (South-west) is the clearest. A cluster of Doaba tehsils (Dinanagar, Phagwara,
  Adampur, Jalandhar-I) burns about half as much as the rest of Central Punjab. Talwandi Sabo is also validated.

## Repository layout

```
Code/
  grouping/      peer grouping (Gower distance, clustering, stability, sensitivity)
  burn/          tehsil burn measure from Sentinel-2, VIIRS fire counts, data checks
  planet/        burn-vs-ploughing detector built on Walker et al. field data
  burn_basma/    helper functions used by the detector (burn indices, Walker data loader)
  pd/            positive deviant identification and validation
  predictors/    desk study of candidate drivers
  impact/        sample-size calculation for the proposed pilot
  figures/       figures used in the report
  gee/           Google Earth Engine script (cropping intensity)
Data/            grouping input tables (other raw data must be downloaded, see below)
results/         final outputs (see below)
paper/           final report (PDF)
```

Some scripts in `burn/`, `planet/` and `burn_basma/` are helpers imported by the main scripts. Keep the folder layout as it is.

## Setup

1. Python 3.11 or later:
   ```
   pip install -r requirements.txt
   ```
2. Google Earth Engine account. Run `earthengine authenticate` once, then set your own Earth Engine
   project name in `Code/burn/transfer_checks.py` (`PROJECT = ...`).
3. Planet scripts (`Code/planet/planet_*.py`) need your own Planet API key in the `PL_API_KEY` environment
   variable. Planet imagery is licensed and is not included. The main pipeline does not need it.

All scripts are run from the repository root and find their inputs relative to it.

## Data

Most raw data are not included (about 15 GB). Place them in `Data/` with these paths:

| Path | Source |
|---|---|
| `Data/punjab_homogeneous_grouping_master_*.csv` | Grouping input table, one row per tehsil (included in this repository) |
| `Data/Rice/rice_area_output/` | Paddy rice map of India, 10 m (Chen et al., 2024, *Remote Sensing* 16:3180); tehsil boundaries with LGD codes |
| `Data/Rice/official/` | District rice area, Statistical Abstract of Punjab 2022 |
| `Data/LGD/Final Output/village_level_bridge_punjab.csv` | Village crosswalk between 2011 Census and current tehsils (Local Government Directory) |
| `Data/Boundaries/shrug-pc11dist-poly-shp/` | SHRUG v2.2 district boundaries (Asher et al., 2021) |
| `Data/census_punjab/` | Census of India 2011, Primary Census Abstract, Punjab villages |
| `Data/Burning/CREAMS/` | Official district burnt-area figures (CREAMS, IARI) |
| `Data/Predictors/` | Driver source tables (straw buyers, district basmati share, livestock census) |
| `Code/Ground Truth Data/Walker/` | Walker et al. burnt and ploughed field time series (Zenodo 10.5281/zenodo.11225292) |
| `Code/Ground Truth Data/*.geojson` | CEEW field-verified burnt fields, 2020 and 2021 |

Sentinel-2, VIIRS, CHIRPS rainfall and GHS-SMOD settlement data are read directly from Google Earth Engine.

## Running the pipeline

Run in this order. Each script lists its inputs and outputs in its header.

**1. Peer grouping**
```
python Code/grouping/cluster.py
python Code/grouping/evaluate.py
python Code/grouping/stability.py
python Code/grouping/sensitivity.py
python Code/grouping/freeze.py
```

**2. Burn measure**
```
python Code/planet/jalandhar_walker_model_test.py --pre-looks 1 --candidate jump   # detector test on Walker fields
python Code/burn/tehsil_metric.py        # sample points per tehsil + baseline measure
python Code/burn/tehsil_metric_rf.py     # final tehsil burn measure
python Code/burn/fire_counts.py          # VIIRS fire counts, for cross-checks
```

**3. Positive deviants**
```
python Code/pd/pd_identify.py --measure s2rf
python Code/pd/pd_identify.py --measure s2rf_2023
python Code/pd/pd_identify.py --measure viirs
python Code/pd/pd_robust.py
python Code/pd/pd_validate.py --boot 1000
```

**4. Drivers**
```
python Code/predictors/drivers.py
python Code/predictors/harvest_gap.py
python Code/predictors/compare_drivers.py
python Code/predictors/urban_check.py
```

**5. Pilot sample size**
```
python Code/impact/sample_size.py
```

**Figures**
```
python Code/figures/make_grouping_figures.py
python Code/figures/make_pd_figures.py
python Code/figures/make_final_figures.py
```

Outputs are written to `outputs/`. Random seeds are fixed, and the grouping records the hashes of its input files in `FROZEN_config.json`.

## Results files

| File | Contents |
|---|---|
| `results/FROZEN_groups.csv` | Peer group of each tehsil, with stability scores |
| `results/FROZEN_group_profiles.csv` | Average conditions of each group (rice share, rainfall, zone, groundwater) |
| `results/FROZEN_config.json` | Final grouping settings and input file hashes |
| `results/tehsil_burn_measure.csv` | Share of paddy area burnt per tehsil and season, 2019–2024 |
| `results/pd_validated.csv` | Positive and negative deviants with the result of each validation check |

## Limitations

- The 2024 season is less certain: most of its detections appear in late November and may include ploughing.
  Every result is also checked on 2020–2023.
- The 15 Foothills tehsils are measured but not ranked.
- Drivers are tested only with public data, so they are leads for field validation, not causes.

## Acknowledgements

Prof. Aaditeshwar Seth; Basma Albanna and Andreas Pawelke (DPPD initiative); Planet Labs PBC (Education and Research Program);
Walker et al. and CEEW for releasing their field data.
