"""
Step 6: are the groups stable? (bootstrap + ARI)

Grouping procedure (applied identically to the full data and every subsample):
  1. drop config.OUTLIERS (Dhar Kalan)
  2. Gower distance on the tehsils present (ranges re-measured on them)
  3. average-linkage tree, cut into k groups
  4. groups smaller than MIN_GROUP_SIZE -> members moved to the closest large group

Stability:
  repeat BOOTSTRAP_RUNS times: keep a random 80% of tehsils, rerun the procedure,
  compare with the full-data groups on the same tehsils using the ARI.
  Per tehsil: overlap (Jaccard) between its group-mates in the subsample and its
  group-mates in the full data, averaged over the runs that included it.
  Group survival: share of runs in which each full-data group still appears (each
  subsample group is named after the full-data group most of its members belong to).
  Tehsil switching (k*_switch): share of runs, among those where the tehsil's own
  group survived, in which the tehsil landed in a different group.
  Consensus (labels_consensus.csv): each tehsil's most frequent group over the runs in
  which every full-data group survived; k*_consensus_share = how often it was there.

Run:  python Code/grouping/stability.py
Out:  outputs/grouping/stability_by_k.csv
      outputs/grouping/stability_per_tehsil.csv
      outputs/grouping/labels_final_rule.csv   (full-data groups per k, after steps 1-4)
      outputs/grouping/group_survival_by_k.csv
      outputs/grouping/labels_consensus.csv    (consensus groups per k)
"""

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster
from sklearn.metrics import adjusted_rand_score, silhouette_score

import config
import gower
from cluster import build_tree

K_RANGE = range(2, 8)


def merge_small_groups(labels, dist, min_size):
    """Move members of groups below min_size to the large group with the lowest average distance."""
    labels = labels.copy()
    sizes = pd.Series(labels).value_counts()
    large = sizes[sizes >= min_size].index
    for g in sizes[sizes < min_size].index:
        for i in np.flatnonzero(labels == g):
            avg = {h: dist[i, labels == h].mean() for h in large}
            labels[i] = min(avg, key=avg.get)
    # renumber 1 = largest group
    order = pd.Series(labels).value_counts().index
    return np.array([list(order).index(g) + 1 for g in labels])


def group_tehsils(df, k):
    """Full grouping procedure on the tehsils in df. Returns (labels, dist)."""
    dist, _ = gower.gower_matrix(
        df, config.DIMENSIONS, config.WEIGHTS, config.RANGE_EXCLUDE
    )
    raw = fcluster(build_tree(dist), t=k, criterion="maxclust")
    return merge_small_groups(raw, dist, config.MIN_GROUP_SIZE), dist


def jaccard_mates(labels_a, labels_b, i):
    """Overlap of tehsil i's group-mates under two labellings of the same tehsils."""
    a = set(np.flatnonzero(labels_a == labels_a[i])) - {i}
    b = set(np.flatnonzero(labels_b == labels_b[i])) - {i}
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def match_to_full(ref, sub):
    """Name each subsample group after the full-data group most of its members belong to."""
    mapping = {g: pd.Series(ref[sub == g]).mode()[0] for g in np.unique(sub)}
    return np.array([mapping[g] for g in sub])


def main():
    df = pd.read_csv(config.MASTER_CSV)
    df = df[~df[config.NAME_COL].isin(config.OUTLIERS)].reset_index(drop=True)
    names = df[config.NAME_COL].to_numpy()
    n = len(df)
    rng = np.random.default_rng(config.SEED)
    n_keep = int(round(config.BOOTSTRAP_FRACTION * n))
    samples = [
        np.sort(rng.choice(n, n_keep, replace=False))
        for _ in range(config.BOOTSTRAP_RUNS)
    ]

    summary, per_tehsil, final, survival_rows, consensus = [], {}, {}, [], {}
    for k in K_RANGE:
        full, full_dist = group_tehsils(df, k)
        final[f"k{k}"] = full
        aris, mate_scores = [], [[] for _ in range(n)]
        groups = np.unique(full)
        survived = {g: 0 for g in groups}
        switch = [[] for _ in range(n)]
        votes = [[] for _ in range(n)]
        for idx in samples:
            sub, _ = group_tehsils(df.iloc[idx].reset_index(drop=True), k)
            ref = full[idx]
            aris.append(adjusted_rand_score(ref, sub))
            matched = match_to_full(ref, sub)
            alive = set(matched)
            for g in groups:
                survived[g] += g in alive
            all_alive = alive == set(groups)
            for j, i in enumerate(idx):
                mate_scores[i].append(jaccard_mates(ref, sub, j))
                # switching: only in runs where the tehsil's own group still exists
                if ref[j] in alive:
                    switch[i].append(matched[j] != ref[j])
                # consensus votes: only runs where every full-data group exists
                if all_alive:
                    votes[i].append(matched[j])
        per_tehsil[f"k{k}"] = [np.mean(s) for s in mate_scores]
        per_tehsil[f"k{k}_switch"] = [np.mean(s) if s else np.nan for s in switch]
        cons, cons_share = [], []
        for i, v in enumerate(votes):
            if v:
                vc = pd.Series(v).value_counts()
                cons.append(vc.index[0])
                cons_share.append(vc.iloc[0] / len(v))
            else:
                cons.append(full[i])
                cons_share.append(np.nan)
        consensus[f"k{k}"] = cons
        per_tehsil[f"k{k}_consensus_share"] = cons_share
        survival_rows.extend(
            {"cut": f"k{k}", "group": g, "size": int((full == g).sum()),
             "survival_rate": round(survived[g] / len(samples), 3)}
            for g in groups
        )
        sizes = pd.Series(full).value_counts().sort_index()
        aris = np.array(aris)
        summary.append(
            {
                "cut": f"k{k}",
                "group_sizes": "/".join(str(s) for s in sizes),
                "silhouette": round(
                    silhouette_score(full_dist, full, metric="precomputed"), 3
                ) if len(sizes) > 1 else np.nan,
                "ari_mean": round(aris.mean(), 3),
                "ari_p05": round(np.percentile(aris, 5), 3),
                "ari_p95": round(np.percentile(aris, 95), 3),
            }
        )

    summary = pd.DataFrame(summary).set_index("cut")
    per_tehsil = pd.DataFrame(per_tehsil, index=names).round(3)
    final = pd.DataFrame(final, index=names)
    per_tehsil.index.name = final.index.name = config.NAME_COL

    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(config.OUT_DIR / "stability_by_k.csv")
    per_tehsil.to_csv(config.OUT_DIR / "stability_per_tehsil.csv")
    final.to_csv(config.OUT_DIR / "labels_final_rule.csv")
    pd.DataFrame(survival_rows).to_csv(config.OUT_DIR / "group_survival_by_k.csv", index=False)
    consensus = pd.DataFrame(consensus, index=names)
    consensus.index.name = config.NAME_COL
    consensus.to_csv(config.OUT_DIR / "labels_consensus.csv")
    print(f"Tehsils clustered: {n} (outliers set aside: {config.OUTLIERS})")
    print(f"Bootstrap: {config.BOOTSTRAP_RUNS} runs x {n_keep} tehsils, seed {config.SEED}")
    print(summary.to_string())
    return summary, per_tehsil, final, consensus


if __name__ == "__main__":
    main()
