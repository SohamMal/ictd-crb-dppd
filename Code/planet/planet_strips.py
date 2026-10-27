"""Daily labelling strips: one row per CEEW field, one column per downloaded Planet day.

  python -I Code/planet/planet_strips.py jalandhar_2021 [--classes unburnt] [--rows 10]

Colour stretch is set per day (2-98 percentile of all that day's clipped scenes): Planet's
satellites differ in calibration, so one fixed stretch gave strong day-to-day colour casts.
A chip therefore shows a field's brightness relative to the whole AOI on that day.
A chip gets a red title when < 90% of the field's pixels are clear in udm2 (band 1).
Fields are shown in random order (seed 42) with their CEEW class hidden.
Outputs: outputs/planet/strips_<site>/page_XX.png and labels_<site>.csv (blank label column).
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

PAD = 60  # m around the field


def stretch(srcs):
    px = np.concatenate([s.read([3, 2, 1]).reshape(3, -1) for s in srcs], axis=1).astype(float)
    px = px[:, (px > 0).all(0)]
    return np.percentile(px, 2, axis=1), np.percentile(px, 98, axis=1)


def chip(srcs, udms, g, lo, hi):
    """Best chip of field g among one day's scenes: (rgb, clear share) or None."""
    x0, y0, x1, y1 = g.buffer(PAD).bounds
    best = None
    for s, u in zip(srcs, udms):
        b = s.bounds
        if not (b.left <= x0 and b.right >= x1 and b.bottom <= y0 and b.top >= y1):
            continue
        w = from_bounds(x0, y0, x1, y1, s.transform)
        img = s.read([3, 2, 1], window=w).astype(float)
        if img.shape[1] < 2 or img.shape[2] < 2:
            continue
        inside = ~geometry_mask([mapping(g)], out_shape=img.shape[1:],
                                transform=s.window_transform(w), all_touched=True)
        valid = (img > 0).all(0) & inside
        if valid.sum() < 0.9 * inside.sum():
            continue
        clear = u.read(1, window=w).astype(bool) & inside
        share = clear.sum() / max(inside.sum(), 1)
        if best is None or share > best[1]:
            rgb = np.clip((img - lo[:, None, None]) / (hi - lo)[:, None, None], 0, 1).transpose(1, 2, 0)
            best = (rgb, share)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", choices=list(SITES))
    ap.add_argument("--classes", nargs="+", default=["unburnt", "golden_yellow_unburnt", "green_unburnt"])
    ap.add_argument("--rows", type=int, default=10)
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
    ref = day_srcs[0][1]
    to_r = Transformer.from_crs(4326, ref[0].crs, always_xy=True).transform

    feats = [f for f in json.loads(path.read_text())["features"]
             if f["properties"]["field_category"] in a.classes]
    rng = np.random.default_rng(42)
    feats = [feats[i] for i in rng.permutation(len(feats))]
    dest = OUT / f"strips_{a.site}"
    dest.mkdir(parents=True, exist_ok=True)
    rows = []
    ncol = len(day_srcs)
    for page in range(0, len(feats), a.rows):
        part = feats[page:page + a.rows]
        fig, axes = plt.subplots(len(part), ncol, figsize=(1.15 * ncol, 1.3 * len(part)), squeeze=False)
        for i, f in enumerate(part):
            fid = f["properties"]["field_id"]
            g = transform(to_r, shape(f["geometry"]))
            n_ok = 0
            for j, (d, srcs, udms, (lo, hi)) in enumerate(day_srcs):
                ax = axes[i, j]
                ax.set_xticks([]); ax.set_yticks([])
                if i == 0:
                    ax.set_title(f"{d:%d %b}\n{(d - d0).days:+d} d", fontsize=7)
                c = chip(srcs, udms, g, lo, hi)
                if c is None:
                    ax.set_facecolor("0.85")
                    continue
                x0, y0, x1, y1 = g.buffer(PAD).bounds
                ax.imshow(c[0], extent=(x0, x1, y0, y1))
                for poly in getattr(g, "geoms", [g]):
                    ax.plot(*poly.exterior.xy, color="cyan", lw=0.8)
                if c[1] < 0.9:
                    for sp in ax.spines.values():
                        sp.set_color("red"); sp.set_linewidth(1.5)
                else:
                    n_ok += 1
            axes[i, 0].set_ylabel(f"field {fid}", fontsize=8)
            rows.append({"field_id": fid, "page": page // a.rows + 1, "clear_days": n_ok,
                         "label": "", "change_day": "", "note": ""})
        fig.suptitle(f"{a.site}: CEEW fields (class hidden), PlanetScope 3 m true colour. "
                     "Red frame = cloud/haze over field. Grey = no picture.", fontsize=8)
        fig.tight_layout()
        fig.savefig(dest / f"page_{page // a.rows + 1:02d}.png", dpi=120)
        plt.close(fig)
    pd.DataFrame(rows).to_csv(OUT / f"labels_{a.site}.csv", index=False)
    print(f"{len(feats)} fields, {ncol} days, {len(rows) and rows[-1]['page']} pages -> {dest}")


if __name__ == "__main__":
    main()
