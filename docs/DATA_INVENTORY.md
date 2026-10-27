# DATA_INVENTORY.md
_Only facts recorded in project notes. **[?]** = not recorded; fill in from the local files when you copy them across (e.g. `head -1 file.csv`)._

## 1. Boundaries & crosswalks
| Item | Source / file | Level | Years / vintage | Known limitations |
|---|---|---|---|---|
| Village polygons | SHRUG v2.2 (Development Data Lab), gpkg | Village | PC11 (2011 Census) | Punjab 12,808 / Haryana 6,998. District codes 2011 (20/21) vs current 23/22 → reassignment needed. Placeholder polygons 800166, 800252 (duplicates) and other `8xxxxx` codes pending decision. GEE asset: `projects/ictd-507010/assets/shrug/shrug_villages` |
| Tehsil bridge | `tehsil_bridge_summary_punjab.csv`, `tehsil_bridge_detail_punjab.csv`, `tehsil_bridge_reverse_punjab.csv` | 2011 tehsil ↔ current LGD tehsil | 2011 → current | `tehsil_bridge_detailed_punjab.csv` is **unreliable, excluded**. 43 2011-tehsils split into 2–3, 9 blended into 1 |
| Village bridge | `village_level_bridge_punjab.csv` (key `pc11_tv_id`) | Village → current tehsil | — | Haryana equivalent incomplete |
| Village → CD block | Punjab crosswalk: 12,581 villages → 142 blocks, 0 unmapped, 0 duplicates | Village/block | — | Haryana meaningfully behind |
| Current tehsil polygons | India GIS / Esri subdistrict layer, LGD codes | Tehsil | current | Used by rice-area script |
| District name map | 16-entry canonical crosswalk | District | — | Mewat vs Nuh open |

## 2. Grouping variables (97 Punjab tehsils)
| Dimension | Column(s) | Source | Years | Known limitations |
|---|---|---|---|---|
| Cropping intensity | `CI_3yr_pooled` | Sentinel-2 SR Harmonized NDVI, ESA WorldCover cropland mask, GEE; village A1/A2/A3 summed to tehsil | Ag-years 2022–2024 | Thresholds untuned; Southwestern and Kandi belts above Statistical Abstract baseline; high year-to-year swings in 6 tehsils; how remaining 52 current tehsils were finalised **[?]** |
| CI baseline | Punjab Statistical Abstract (pbeso.punjab.gov.in); Haryana: esaharyana.gov.in district abstracts | District | Punjab editions incl. 2021, 2023 in progress; Haryana 3 editions | Cross-check only; Haryana incomplete |
| Rice area | `chen_rice_area_ha_2022` (→ rice share pending) | Chen et al. (2024) 10 m paddy GeoTIFF, class 1 pixels → ha, masked by LGD tehsils (`calc_chen2022_rice_area_current_lgd.py`). figshare `10.6084/m9.figshare.24228619`; "Winter" files 2018/2020/2022 = Kharif rice | 2022 | Single-year snapshot. Village CSV `village_rice_all_years.csv` 2022 column is stale (98.6% = 2020); 2018/2020 columns clean (0.988 correlation, no nulls). Standalone `village_rice_2022.csv` byte-identical to stale column |
| Rice (spare) | Sentinel-1 VH SAR rule, GEE | Village | 2022–24 | Validated on 2 villages only; full export not confirmed |
| Rainfall | mean monsoon (Jun–Sep) rainfall | CHIRPS daily, GEE | 2020–2025 (prototype); 2006–2020 intended | ~5 km pixel; centroid fallback for small villages; GEE task `village_monsoon_rainfall_2006_2020` null/ID check not recorded |
| Terrain | `elevation_mean`, `slope_mean` | 2026 terrain file (DEM source SRTM or Copernicus **[?]**) | static | None recorded; all 97 covered |
| Groundwater | `mean_extraction_pct_2022` | PWRDA Punjab Directions (block-level) | 2022 (2025 also available) | Punjab numeric extraction %; Haryana category-only. Block-level, inherited downward |
| Soil | 8 categorical descriptors (particle size, drainage, texture, depth, pH, salinity, sodicity, erosion) | NBSS&LUP Bhoomi Geoportal, 1:250K, WFS `http://14.139.123.73:8080/geoserver/wfs` | static | Fatehgarh Sahib drainage missing for 104 villages (one drainage value set to `Unknown` at tehsil level); extraction route details thin **[?]** |
| Agro-climatic zones | NARP (district-based) | — | — | **No longer used**; Tarn Taran and SBS Nagar had zero zone data (969 villages) |

## 3. Master grouping files (to copy)
`punjab_homogeneous_grouping_master_raw_97tehsils.csv`, `..._transformed.csv` (log1p on rice area, elevation, slope; one drainage `Unknown`), `..._encoded.csv`. Exact column lists **[?]**.

## 4. Burn / validation data
| Item | Source | Known limitations |
|---|---|---|
| Ground truth | 380 labelled fields: Hoshiarpur/Jalandhar 2021, Sangrur area 2020; Chen et al. (2024) for rice fields, NBSS&LUP for soil | Provenance to confirm before external citing; only 3 areas |
| Burn imagery | Sentinel-2 (BAIS2 + TCB) | Not yet scaled to tehsil |
| Public survey | Naeher et al. (2023), *Scientific Data*, 1,206 farmers, 70 villages | For Stage 3 / validation context |
| Rejected | FIRMS/VIIRS | ~3.67x undercount |

## 5. Merge-validation anomalies (village-level, Sept; may no longer matter at tehsil level)
- Merged Punjab file had 12,800 villages vs 12,808 SHRUG baseline (8 unaccounted).
- Haryana deliberately excluded from current merge.
- ID-vintage mismatch across soil / rice (2011 IDs), CI (latest district-wise), zones.

## 6. External resources
GEE project `ictd-507010`; reference PDF `DPPD_Handbook_Nov_2021.pdf`; advisor deck `DPPD_Crop_Residue_Burning_Questions_for_Prof__Aaditeshwar.pptx`.
