"""
Version X, step 3c: peer groups = village group x rice-share band (2026-11-10)

Why: in the village clustering (vx_grouping.py) the rice dimension hardly separates the groups (between - within
distance 0.035 vs zone 0.377, rainfall 0.161): the groups are climate/zone groups. But rice share is the
structural trait that burning follows most (main version V4: rho 0.70 Central, 0.63 South-west), and at village
level it spans 0.08-1.0 inside every group. A village with half its land in other crops would then look like a
PD only because it has less paddy. So inside each group villages are split into rice-share terciles (bands
L/M/H) and compared only within group x band. Both cuts are structural (no driver, no burn value).
Sensitivities in vx_pd.py V2: group without bands; tehsil region x band.

Run:  python version_X/Code/vx_peer_groups.py
Out:  version_X/outputs/grouping/village_groups.csv (adds rice_band, peer, region_peer), peer_profiles.csv
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
G = ROOT / "version_X" / "outputs" / "grouping"
BANDS = ["L", "M", "H"]


def band(df, by):
    return df.groupby(by).rice_share_2022_cal.transform(lambda s: pd.qcut(s, 3, labels=BANDS).astype(str))


def main():
    v = pd.read_csv(G / "village_groups.csv", dtype={"c2011_village_code": str, "lgd_tehsil_code": str})
    v["rice_band"] = band(v, "vgroup")
    v["peer"] = v.vgroup + "-" + v.rice_band
    v["region_peer"] = v.tehsil_region + "-" + band(v, "tehsil_region")
    v.to_csv(G / "village_groups.csv", index=False)
    p = v.groupby("peer").agg(n=("c2011_village_code", "size"), rice_min=("rice_share_2022_cal", "min"),
                              rice_median=("rice_share_2022_cal", "median"), rice_max=("rice_share_2022_cal", "max"),
                              rain_mm=("monsoon_rainfall_mm", "median"), gw_pct=("extraction_pct_2022", "median"))
    p.round(3).to_csv(G / "peer_profiles.csv")
    print(p.round(3).to_string())


if __name__ == "__main__":
    main()
