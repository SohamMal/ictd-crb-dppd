"""Visual check of one Planet order: true-colour chips of CEEW fields, outlined, grouped by CEEW class.

  python -I Code/planet/planet_chips.py jalandhar_2021 2021-10-29 [--per-class 6]

Same colour stretch for every chip (2-98 percentile over all clipped scenes), so
brightness is comparable across fields. Output: outputs/planet/chips_<site>_<day>.png
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planet_search import OUT, SITES

PAD = 60  # m around the field


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", choices=list(SITES))
    ap.add_argument("day")
    ap.add_argument("--per-class", type=int, default=6)
    a = ap.parse_args()
    tifs = sorted((OUT / "orders" / f"{a.site}_{a.day}").glob("*_SR_clip.tif"))
    srcs = [rasterio.open(t) for t in tifs]
    crs = srcs[0].crs
    to_r = Transformer.from_crs(4326, crs, always_xy=True).transform

    # common stretch from all scenes (bands: 1 blue, 2 green, 3 red, 4 nir)
    px = np.concatenate([s.read([3, 2, 1]).reshape(3, -1) for s in srcs], axis=1).astype(float)
    px = px[:, (px > 0).all(0)]
    lo, hi = np.percentile(px, 2, axis=1), np.percentile(px, 98, axis=1)

    feats = json.loads(SITES[a.site][0].read_text())["features"]
    by_cls = {}
    for f in feats:
        g = transform(to_r, shape(f["geometry"]))
        by_cls.setdefault(f["properties"]["field_category"], []).append((f["properties"]["field_id"], g))
    order = [c for c in ("completely_burnt", "partially_burnt", "unburnt", "golden_yellow_unburnt", "green_unburnt") if c in by_cls]

    fig, axes = plt.subplots(len(order), a.per_class, figsize=(2.6 * a.per_class, 2.9 * len(order)))
    axes = np.atleast_2d(axes)
    for i, c in enumerate(order):
        # largest fields first, keep those fully inside a scene with no nodata
        cand = sorted(by_cls[c], key=lambda t: -t[1].area)
        j = 0
        for fid, g in cand:
            if j == a.per_class:
                break
            x0, y0, x1, y1 = g.buffer(PAD).bounds
            for s in srcs:
                b = s.bounds
                if not (b.left <= x0 and b.right >= x1 and b.bottom <= y0 and b.top >= y1):
                    continue
                w = from_bounds(x0, y0, x1, y1, s.transform)
                img = s.read([3, 2, 1], window=w).astype(float)
                if (img == 0).all(0).mean() > 0.05:
                    continue
                rgb = np.clip((img - lo[:, None, None]) / (hi - lo)[:, None, None], 0, 1).transpose(1, 2, 0)
                ax = axes[i, j]
                ax.imshow(rgb, extent=(x0, x1, y0, y1))
                for poly in getattr(g, "geoms", [g]):
                    ax.plot(*poly.exterior.xy, color="cyan", lw=1.2)
                ax.set_title(f"#{fid}  {g.area / 1e4:.2f} ha", fontsize=8)
                ax.set_xticks([]); ax.set_yticks([])
                j += 1
                break
        axes[i, 0].set_ylabel(c.replace("_", " "), fontsize=9)
        for k in range(j, a.per_class):
            axes[i, k].axis("off")
    fig.suptitle(f"PlanetScope 3 m true colour, {a.site}, {a.day} (CEEW class per row)", fontsize=10)
    fig.tight_layout()
    out = OUT / f"chips_{a.site}_{a.day}.png"
    fig.savefig(out, dpi=130)
    print(out)


if __name__ == "__main__":
    main()
