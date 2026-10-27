"""
Freeze the peer groups used for PD identification.

Decision 2026-10-06 (Soham): 3 regions (central / south-west / foothills), with
Dhar Kalan as a contextual outlier. The central/south-west border is a gradient, so
tehsils with low bootstrap stability are flagged borderline and PD results are to be
checked against the 2-group alternative (k = 2: plains / foothills). Uses the same procedure as stability.py (Gower on config
DIMENSIONS -> average-linkage HAC -> cut k -> small-group merge).

Run:  python Code/grouping/freeze.py      (after stability.py, for per-tehsil stability)
Out:  outputs/grouping/FROZEN_groups.csv
      outputs/grouping/FROZEN_group_profiles.csv
      outputs/grouping/FROZEN_config.json
"""

import hashlib
import json
from datetime import date

import pandas as pd

from sklearn.metrics import silhouette_score

import config
from stability import group_tehsils

K_FROZEN = 3  # 3 groups (central / south-west / foothills); 5 dims after CI dropped
K_ALTERNATIVE = 2  # plains / foothills, robustness check for PDs
BORDERLINE_SWITCH = 0.2  # tehsil switches group in >= 1 of 5 runs where its group survived


def main():
    full = pd.read_csv(config.MASTER_CSV)
    df = full[~full[config.NAME_COL].isin(config.OUTLIERS)].reset_index(drop=True)
    # Consensus placement (2026-10-07): each tehsil goes to the group it falls in most
    # often across bootstrap runs, not only the single full-data tree cut.
    consensus = pd.read_csv(config.OUT_DIR / "labels_consensus.csv", index_col=0)
    tree_labels, dist = group_tehsils(df, K_FROZEN)
    df["group_id"] = df[config.NAME_COL].map(consensus[f"k{K_FROZEN}"]).to_numpy()
    df["tree_group_id"] = tree_labels

    # Name groups by zone: highest mean Siwalik (14.2) share = Foothills,
    # highest mean arid (2.5) share among the rest = South-west, remaining = Central.
    means = df.groupby("group_id")[["aesr_share_14_2", "aesr_share_2_5"]].mean()
    foot = means["aesr_share_14_2"].idxmax()
    sw = means.drop(index=foot)["aesr_share_2_5"].idxmax()
    names = {g: "Foothills" if g == foot else "South-west" if g == sw else "Central"
             for g in means.index}
    assert len(names) == 3
    df["group"] = df["group_id"].map(names)

    alt = df[config.NAME_COL].map(consensus[f"k{K_ALTERNATIVE}"]).to_numpy()
    alt_foot = pd.Series(alt).groupby(alt).apply(lambda i: df.loc[i.index, "aesr_share_14_2"].mean()).idxmax()
    df["group_2way"] = ["Foothills" if a == alt_foot else "Plains" for a in alt]

    stab = pd.read_csv(config.OUT_DIR / "stability_per_tehsil.csv", index_col=0)
    df["bootstrap_mate_overlap"] = df[config.NAME_COL].map(stab[f"k{K_FROZEN}"])
    df["switch_rate"] = df[config.NAME_COL].map(stab[f"k{K_FROZEN}_switch"])
    df["switch_rate_2way"] = df[config.NAME_COL].map(stab[f"k{K_ALTERNATIVE}_switch"])
    df["consensus_share"] = df[config.NAME_COL].map(stab[f"k{K_FROZEN}_consensus_share"])
    df["moved_by_consensus"] = df["group_id"] != df["tree_group_id"]
    sil = silhouette_score(dist, df["group_id"], metric="precomputed")
    sil_tree = silhouette_score(dist, tree_labels, metric="precomputed")
    df["borderline"] = df["switch_rate"] >= BORDERLINE_SWITCH
    df["outlier"] = False

    out_cols = [config.ID_COL, config.NAME_COL, "lgd_district_name", "group", "group_2way",
                "outlier", "borderline", "moved_by_consensus", "consensus_share",
                "switch_rate", "switch_rate_2way", "bootstrap_mate_overlap"]
    frozen = pd.concat([
        df[out_cols],
        full[full[config.NAME_COL].isin(config.OUTLIERS)]
        .assign(group="Outlier", group_2way="Outlier", outlier=True, borderline=False, moved_by_consensus=False, consensus_share=None, switch_rate=None, switch_rate_2way=None, bootstrap_mate_overlap=None)[out_cols],
    ]).sort_values(["group", config.NAME_COL]).reset_index(drop=True)
    assert len(frozen) == len(full) and frozen[config.ID_COL].is_unique

    profile_cols = ["CI_3yr_pooled", "rice_share_2022_cal", "mean_monsoon_rainfall_mm",
                    "aesr_share_14_2", "aesr_share_2_5", "aesr_share_4_1", "aesr_share_9_1",
                    "mean_extraction_pct_2022", "elevation_mean"]
    prof = full.merge(frozen[[config.ID_COL, "group"]], on=config.ID_COL)
    profiles = prof.groupby("group")[profile_cols].median().round(3)
    profiles.insert(0, "n_tehsils", prof.groupby("group").size())

    cfg = {
        "frozen_on": str(date.today()),
        "k": K_FROZEN,
        "k_alternative_2way": K_ALTERNATIVE,
        "master_csv": str(config.MASTER_CSV.relative_to(config.ROOT)),
        "dimensions": config.DIMENSIONS,
        "weights": config.WEIGHTS or "equal",
        "range_exclude": config.RANGE_EXCLUDE,
        "outliers": config.OUTLIERS,
        "min_group_size": config.MIN_GROUP_SIZE,
        "borderline_switch_rate": BORDERLINE_SWITCH,
        "assignment": "bootstrap consensus (labels_consensus.csv)",
        "silhouette_consensus": round(sil, 3),
        "silhouette_tree_cut": round(sil_tree, 3),
        "master_sha256": hashlib.sha256(config.MASTER_CSV.read_bytes()).hexdigest(),
    }

    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    frozen.to_csv(config.OUT_DIR / "FROZEN_groups.csv", index=False)
    profiles.to_csv(config.OUT_DIR / "FROZEN_group_profiles.csv")
    (config.OUT_DIR / "FROZEN_config.json").write_text(json.dumps(cfg, indent=2))

    print(frozen["group"].value_counts().to_string())
    print("\nBorderline:", frozen.loc[frozen["borderline"], config.NAME_COL].tolist())
    print("Moved by consensus:", frozen.loc[frozen["moved_by_consensus"], config.NAME_COL].tolist())
    print(f"Silhouette: consensus {sil:.3f} | tree cut {sil_tree:.3f}")
    print("\nGroup profiles (medians):")
    print(profiles.to_string())


if __name__ == "__main__":
    main()
