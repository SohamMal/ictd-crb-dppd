"""
Grouping configuration: which dimensions define "similar tehsils".

Edit DIMENSIONS to swap variables (e.g. replace rainfall + terrain with
agro-climatic zones). Nothing else in the pipeline needs to change.

Rules (CLAUDE.md §2): structural variables only; never hypothesised drivers;
never burn outcomes.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MASTER_CSV = ROOT / "Data" / "punjab_homogeneous_grouping_master_transformed.csv"
OUT_DIR = ROOT / "outputs" / "grouping"

ID_COL = "lgd_tehsil_code"
NAME_COL = "lgd_tehsil_name"

# Each dimension: list of (column, kind). kind = "numeric" or "categorical".
# Numeric columns are compared as |a - b| / range; categorical as same=0 / different=1.
# Within a dimension the column differences are averaged, so every dimension
# gets one vote no matter how many columns it has.
DIMENSIONS = {
    # Cropping intensity (CI_3yr_pooled) dropped 2026-10-07: satellite CI unreliable
    # (rho 0.18 vs official) and not shaping the grouping (see ci_influence.py).
    # Chen 2022 calibrated to official district rice area (2026-10-07).
    "rice": [("rice_share_2022_cal", "numeric")],
    "rainfall": [("mean_monsoon_rainfall_mm", "numeric")],
    # Terrain (elevation_log1p, slope_log1p) removed 2026-10-06: slope data defective.
    # Replaced by share of tehsil area in each NBSS&LUP AESR 2018 zone.
    "zone": [
        ("aesr_share_14_2", "numeric"),
        ("aesr_share_2_5", "numeric"),
        ("aesr_share_4_1", "numeric"),
        ("aesr_share_9_1", "numeric"),
    ],
    "groundwater": [("mean_extraction_pct_2022", "numeric")],
    "soil": [
        ("dominant_particle_size", "categorical"),
        ("dominant_drainage", "categorical"),
        ("dominant_soil_texture", "categorical"),
        ("dominant_soil_depth", "categorical"),
        ("dominant_ph_class", "categorical"),
        ("dominant_salinity", "categorical"),
        ("dominant_sodicity", "categorical"),
        ("dominant_erosion", "categorical"),
    ],
}

# Weight per dimension. None = equal weights (1 / number of dimensions).
WEIGHTS = None

# Tehsils left out when measuring each numeric column's range (the "ruler").
# They stay in the clustering; their differences are capped at 1.
# Dhar Kalan sets the min/max of 4 of 6 numeric variables and would compress
# everyone else's differences by ~12% (decided 2026-10-06, option a).
RANGE_EXCLUDE = ["Dhar Kalan"]

# Contextual outliers: a singleton at every cut, so they are set aside before
# cutting groups (they join the tree last and do not change any other merge).
OUTLIERS = ["Dhar Kalan"]

# Groups smaller than this cannot host a peer comparison; their members are
# moved to the large group they are closest to (average distance).
MIN_GROUP_SIZE = 5

# Stability (bootstrap) settings.
BOOTSTRAP_RUNS = 300
BOOTSTRAP_FRACTION = 0.8
SEED = 42
