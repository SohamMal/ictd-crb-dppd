"""Apply the Planet burn rule (calibrated on Walker ground truth) to located CEEW fields, Jalandhar 2021.

Rule (from walker_planet_test.py, all-band brightness (B+G+R+NIR)/4, days 0..2 after the event):
  ratio(t) = brightness(t) / median brightness of the field's clear looks in [t-15, t-1]
  burnt if min_t ratio(t) <= CUT, where CUT keeps 90% of Walker's burnt fields (0..2 d window).
  burn day = the t with the lowest ratio.
Applied to the 95 CEEW fields that were unburnt on 29 Oct (our 19 Planet days, 25 Oct - 13 Nov).
Compared with Soham's labels and with the Sentinel-2 detector (s2check_fields.csv).

Out: outputs/planet/jalandhar_planet_rule_fields.csv, jalandhar_planet_rule_vs_labels.csv,
     outputs/planet/fig_jalandhar_planet_vs_s2.png
"""
import json
import sys
import zipfile
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.path import Path as MPath
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform

sys.path.insert(0, str(Path(__file__).resolve().parent))
import walker_planet_test as wt  # noqa: E402
from planet_search import OUT, SITES  # noqa: E402
import tiffread  # noqa: E402  (rasterio DLL blocked by Windows Application Control)

SITE = "jalandhar_2021"
KEEP = 0.9
CLASSES = ["unburnt"]


def walker_cut():
    z = zipfile.ZipFile(wt.ZIP)
    b = wt.load(z, "burnt")
    br = (b["blue"] + b["green"] + b["red"] + b["nir"]) / 4
    r = []
    for fid in br.columns:
        x = br[fid].dropna()
        base = x[(x.index >= -15) & (x.index <= -1)].median()
        p = x[(x.index >= 0) & (x.index <= 2)]
        if len(p) and base == base:
            r.append(p.min() / base)
    return float(np.quantile(r, KEEP))


def field_pixels(arr, tr, g):
    """Values [bands, n] of pixels whose centres fall inside polygon g (UTM metres), or None."""
    x0, dx, y0, dy = tr
    minx, miny, maxx, maxy = g.bounds
    c0, c1 = int((minx - x0) // dx), int((maxx - x0) // dx) + 1
    r0, r1 = int((maxy - y0) // dy), int((miny - y0) // dy) + 1
    if c0 < 0 or r0 < 0 or c1 > arr.shape[2] or r1 > arr.shape[1]:
        return None
    cols, rows = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
    pts = np.c_[(x0 + (cols.ravel() + 0.5) * dx), (y0 + (rows.ravel() + 0.5) * dy)]
    inside = np.zeros(len(pts), bool)
    for poly in getattr(g, "geoms", [g]):
        inside |= MPath(np.asarray(poly.exterior.coords)).contains_points(pts)
    if not inside.any():
        return None
    return arr[:, rows.ravel()[inside], cols.ravel()[inside]]


def field_series(feats):
    days = sorted(p for p in (OUT / "orders").glob(f"{SITE}_*") if list(p.glob("*_SR_clip.tif")))
    to_m = Transformer.from_crs(4326, 32643, always_xy=True).transform
    geoms = [(f["properties"]["field_id"], transform(to_m, shape(f["geometry"]))) for f in feats]
    rows = []
    for p in days:
        d = date.fromisoformat(p.name[-10:])
        scenes = []
        for t in sorted(p.glob("*_SR_clip.tif")):
            sr, tr, epsg = tiffread.read(t)
            assert epsg == 32643, (t, epsg)
            udm, _, _ = tiffread.read(str(t).replace("_AnalyticMS_SR_clip", "_udm2_clip"))
            scenes.append((sr, udm[0], tr))
        for fid, g in geoms:
            best = None
            for sr, clear, tr in scenes:
                px = field_pixels(np.concatenate([sr, clear[None].astype(sr.dtype)]), tr, g)
                if px is None:
                    continue
                ok = (px[4] == 1) & (px[:4] > 0).all(0)
                share = ok.mean()
                if share >= 0.9 and (best is None or share > best[1]):
                    best = (px[:4, ok].astype(float).mean(), share)
            if best:
                rows.append({"field_id": fid, "day": d, "bright": best[0]})
        print("  read", d, len(scenes), "scenes")
    return pd.DataFrame(rows)


def classify(ts, cut):
    out = []
    for fid, g in ts.sort_values("day").groupby("field_id"):
        g = g.set_index("day").bright
        best = (np.inf, None)
        for t, v in g.items():
            prev = g[(g.index < t) & (g.index >= t - pd.Timedelta(days=15))]
            if len(prev):
                r = v / prev.median()
                if r < best[0]:
                    best = (r, t)
        out.append({"field_id": fid, "min_ratio": best[0] if best[1] is not None else np.nan,
                    "burn_day": best[1], "planet_burnt": int(best[0] <= cut) if best[1] is not None else np.nan})
    return pd.DataFrame(out)


def main():
    cut = walker_cut()
    print(f"cut-off (keeps {KEEP:.0%} of Walker burnt fields, 0..2 d): ratio <= {cut:.3f}")
    allf = json.loads(SITES[SITE][0].read_text())["features"]
    feats = [f for f in allf if f["properties"]["field_category"] in CLASSES]
    ts = field_series(feats)
    ts["day"] = pd.to_datetime(ts.day)
    c = classify(ts, cut)
    c["burn_day"] = pd.to_datetime(c.burn_day)
    lab = pd.concat([pd.read_csv(OUT / "labels_v2_jalandhar_2021.csv"),
                     pd.read_csv(OUT / "labels_v2_jalandhar_2021_p03-19.csv")])[["field_id", "label"]]
    lab["label"] = lab.label.astype(str).str.strip().str.lower().replace("nan", "not labelled")
    s2 = pd.read_csv(OUT / "s2check_fields.csv")[["field_id", "flag_any_29oct_13nov"]].rename(
        columns={"flag_any_29oct_13nov": "s2_burnt"})
    c = c.merge(lab, on="field_id", how="left").merge(s2, on="field_id", how="left")
    c.to_csv(OUT / "jalandhar_planet_rule_fields.csv", index=False)
    t = c.groupby("label").agg(fields=("field_id", "size"), planet_called_burnt=("planet_burnt", "mean"),
                               s2_called_burnt=("s2_burnt", "mean"), median_min_ratio=("min_ratio", "median")).round(3)
    t.to_csv(OUT / "jalandhar_planet_rule_vs_labels.csv")
    print(t.to_string())
    print(c[c.label.isin(["burnt", "ploughed", "stubble", "green"])].sort_values(["label", "min_ratio"]).to_string(index=False))

    # map: CEEW unburnt fields coloured by Planet rule, outline = Sentinel-2 flag
    to_m = Transformer.from_crs(4326, 32643, always_xy=True).transform
    geo = {f["properties"]["field_id"]: transform(to_m, shape(f["geometry"])) for f in feats}
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5), sharex=True, sharey=True)
    for ax, col, title in [(axes[0], "s2_burnt", "Sentinel-2 detector (29 Oct - 13 Nov)"),
                           (axes[1], "planet_burnt", "Planet daily rule (25 Oct - 13 Nov)")]:
        for _, r in c.iterrows():
            g = geo[r.field_id]
            colr = "#c0392b" if r[col] == 1 else ("#7f8c8d" if pd.isna(r[col]) else "#27ae60")
            for p in getattr(g, "geoms", [g]):
                ax.fill(*p.exterior.xy, color=colr, ec="black", lw=0.6)
            if r.label == "ploughed":
                ax.annotate("ploughed (265)", g.centroid.coords[0], xytext=(15, 15), textcoords="offset points",
                            arrowprops=dict(arrowstyle="->"), fontsize=8)
        ax.set_title(title, fontsize=10)
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color="#c0392b", label="called burnt"), Patch(color="#27ae60", label="not burnt"),
                        Patch(color="#7f8c8d", label="no data")], loc="lower center", ncol=3)
    fig.suptitle("95 CEEW fields unburnt on 29 Oct 2021, Jalandhar: what happened next", fontsize=11)
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    fig.savefig(OUT / "fig_jalandhar_planet_vs_s2.png", dpi=140)


if __name__ == "__main__":
    main()
