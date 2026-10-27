"""Labelling strips, version 2: fewer fields per page, bigger chips, and a relative-brightness line.

  python -I Code/planet/planet_strips_v2.py jalandhar_2021 [--rows 5] [--pages 2]

Per field and day: relative brightness = mean visible reflectance (R+G+B)/3 of the field's
clear pixels / median of clear pixels in a ring 30-250 m around it, from the same scene.
Being a ratio within one picture, it removes most day-to-day calibration differences.
1.0 = as bright as the neighbours; a sharp drop on one day = sudden darkening (burn candidate).
Days without a clear picture are shaded on the line.

Same field order as version 1 (random, seed 42; CEEW class hidden). Version 1 outputs are
not touched. Outputs: outputs/planet/strips_v2_<site>/page_XX.png,
outputs/planet/relbright_v2_<site>.csv, outputs/planet/labels_v2_<site>.csv.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planet_search import OUT, SITES
from planet_strips import PAD, chip, stretch

RING = (30, 250)  # m, neighbourhood ring around the field
MIN_CLEAR = 0.9
YLIM = (0.5, 1.8)


def rel_brightness(srcs, udms, g):
    """(ratio, clear share) from the scene with the most clear field pixels, or None."""
    x0, y0, x1, y1 = g.buffer(RING[1]).bounds
    best = None
    for s, u in zip(srcs, udms):
        b = s.bounds
        if not (b.left <= x0 and b.right >= x1 and b.bottom <= y0 and b.top >= y1):
            continue
        w = from_bounds(x0, y0, x1, y1, s.transform)
        img = s.read([1, 2, 3], window=w).astype(float)
        if img.shape[1] < 2 or img.shape[2] < 2:
            continue
        wt = s.window_transform(w)
        field = ~geometry_mask([mapping(g)], out_shape=img.shape[1:], transform=wt)
        ring = (~geometry_mask([mapping(g.buffer(RING[1]))], out_shape=img.shape[1:], transform=wt)
                & geometry_mask([mapping(g.buffer(RING[0]))], out_shape=img.shape[1:], transform=wt))
        ok = u.read(1, window=w).astype(bool) & (img > 0).all(0)
        vis = img.mean(0)
        if field.sum() == 0:
            continue
        share = (ok & field).sum() / field.sum()
        if (ok & ring).sum() < 50 or (ok & field).sum() < 5:
            continue
        r = vis[ok & field].mean() / np.median(vis[ok & ring])
        if best is None or share > best[1]:
            best = (r, share)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", choices=list(SITES))
    ap.add_argument("--classes", nargs="+", default=["unburnt", "golden_yellow_unburnt", "green_unburnt"])
    ap.add_argument("--rows", type=int, default=5)
    ap.add_argument("--pages", type=int, default=0, help="0 = all")
    ap.add_argument("--from-page", type=int, default=1, help="skip earlier pages (already built)")
    a = ap.parse_args()
    path, d0 = SITES[a.site]
    days = sorted(p for p in (OUT / "orders").glob(f"{a.site}_*") if list(p.glob("*_SR_clip.tif")))
    day_srcs = []
    for p in days:
        sr = sorted(p.glob("*_SR_clip.tif"))
        srcs = [rasterio.open(t) for t in sr]
        day_srcs.append((date.fromisoformat(p.name[-10:]), srcs,
                         [rasterio.open(str(t).replace("_AnalyticMS_SR_clip", "_udm2_clip")) for t in sr],
                         stretch(srcs)))
    to_r = Transformer.from_crs(4326, day_srcs[0][1][0].crs, always_xy=True).transform

    feats = [f for f in json.loads(path.read_text())["features"]
             if f["properties"]["field_category"] in a.classes]
    rng = np.random.default_rng(42)
    feats = [feats[i] for i in rng.permutation(len(feats))]
    n_pages = -(-len(feats) // a.rows)
    if a.pages:
        n_pages = min(n_pages, a.pages)
    dest = OUT / f"strips_v2_{a.site}"
    dest.mkdir(parents=True, exist_ok=True)
    ncol = len(day_srcs)
    xs = [(d - d0).days for d, *_ in day_srcs]
    series, labels = [], []
    for pg in range(a.from_page - 1, n_pages):
        part = feats[pg * a.rows:(pg + 1) * a.rows]
        fig = plt.figure(figsize=(1.45 * ncol, 3.6 * len(part)))
        outer = fig.add_gridspec(len(part), 1, hspace=0.45, top=0.96, bottom=0.03)
        for i, f in enumerate(part):
            fid = f["properties"]["field_id"]
            g = transform(to_r, shape(f["geometry"]))
            inner = outer[i].subgridspec(2, ncol, height_ratios=[1.3, 1], hspace=0.15, wspace=0.05)
            vals = []
            for j, (d, srcs, udms, (lo, hi)) in enumerate(day_srcs):
                ax = fig.add_subplot(inner[0, j])
                ax.set_xticks([]); ax.set_yticks([])
                ax.set_title(f"{d:%d %b} ({xs[j]:+d})", fontsize=8)
                c = chip(srcs, udms, g, lo, hi)
                rb = rel_brightness(srcs, udms, g)
                ok = rb is not None and rb[1] >= MIN_CLEAR
                vals.append(rb[0] if ok else np.nan)
                series.append({"field_id": fid, "day": d.isoformat(), "days_from_label": xs[j],
                               "rel_brightness": rb[0] if rb else np.nan,
                               "clear_share": rb[1] if rb else np.nan})
                if c is None:
                    ax.set_facecolor("0.85")
                    continue
                x0, y0, x1, y1 = g.buffer(PAD).bounds
                ax.imshow(c[0], extent=(x0, x1, y0, y1))
                for poly in getattr(g, "geoms", [g]):
                    ax.plot(*poly.exterior.xy, color="cyan", lw=1)
                if not ok:
                    for sp in ax.spines.values():
                        sp.set_color("red"); sp.set_linewidth(2)
            ax = fig.add_subplot(inner[1, :])
            v = np.array(vals)
            for x, val in zip(xs, v):
                if np.isnan(val):
                    ax.axvspan(x - 0.5, x + 0.5, color="0.88", lw=0)
            # missing calendar days (no order at all) also shaded
            for x in range(min(xs), max(xs) + 1):
                if x not in xs:
                    ax.axvspan(x - 0.5, x + 0.5, color="0.88", lw=0)
            m = ~np.isnan(v)
            ax.plot(np.array(xs)[m], v[m], "-o", color="black", ms=4, lw=1.2)
            ax.axhline(1, color="0.5", lw=0.8, ls="--")
            ax.set_xlim(min(xs) - 0.5, max(xs) + 0.5)
            ax.set_ylim(*YLIM)  # same scale for every field, so drops are comparable
            ax.set_xticks(range(min(xs), max(xs) + 1))
            ax.tick_params(labelsize=7)
            ax.set_ylabel("brightness vs\nneighbours", fontsize=8)
            ax.set_xlabel("days from CEEW visit (grey band = no clear picture)", fontsize=7)
            ax.text(0.003, 0.97, f"field {fid}", transform=ax.transAxes, va="top", fontsize=10, weight="bold")
            labels.append({"field_id": fid, "page": pg + 1, "clear_days": int(m.sum()),
                           "label": "", "change_day": "", "note": ""})
        fig.suptitle(f"{a.site} v2: one field per block. Top: PlanetScope 3 m true colour "
                     "(red frame = cloud/haze over field, grey = no picture). Bottom: field brightness "
                     "/ neighbours (1 = same as neighbours).", fontsize=10, y=0.99)
        fig.savefig(dest / f"page_{pg + 1:02d}.png", dpi=110, bbox_inches="tight")
        plt.close(fig)
    # never overwrite an existing sheet (it may hold labels): suffix with the page range
    tag = "" if a.from_page == 1 else f"_p{a.from_page:02d}-{n_pages:02d}"
    for stem, df in (("relbright_v2", series), ("labels_v2", labels)):
        f = OUT / f"{stem}_{a.site}{tag}.csv"
        if f.exists():
            raise SystemExit(f"{f.name} exists; not overwriting")
        pd.DataFrame(df).to_csv(f, index=False)
    print(f"{len(labels)} fields on {n_pages} pages -> {dest}")


if __name__ == "__main__":
    main()
