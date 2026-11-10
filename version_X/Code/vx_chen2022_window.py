"""
Version X: cut the Punjab window out of the India-wide Chen 2022 rice map (2026-11-10)

CHECK ONLY. Suspicion: clipped_2022.tif might be a stale copy of 2020 (98.6% of villages have the same rice
pixel count in both). Result (2026-11-10): the window cut from the India-wide Data/Rice/chen_2022.tif equals
clipped_2022.tif at 100% of pixels (every 7th pixel checked), and clipped_2020 vs 2022 agree on 99.2% of pixels
(10.90 M of 11.03 / 11.15 M rice pixels in both). So clipped_2022.tif IS the Chen 2022 map; the two Chen years
are simply almost the same map. The .npy was deleted after the check (2.2 GB). rasterio is blocked, so the
strips are decoded one by one with zlib.

Grid: same pixel size as clipped_*.tif; clipped origin (73.88, 32.52) falls at India col 32086.21, row 25419.06,
so clipped pixel (i, j) = India pixel (25419 + i, 32086 + j) (pixel centres fall inside it).

Run:  python version_X/Code/vx_chen2022_window.py
Out:  version_X/outputs/villages/chen2022_punjab_window.npy (uint8, same shape as clipped_2020.tif)
"""

import site
import sys
import zlib
from pathlib import Path

sys.path.append(site.getusersitepackages())
import numpy as np  # noqa: E402
import tifffile  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "Data" / "Rice" / "chen_2022.tif"
OUT = ROOT / "version_X" / "outputs" / "villages" / "chen2022_punjab_window.npy"
ROW0, COL0 = 25419, 32086
SHAPE = (54212, 41411)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tifffile.TiffFile(SRC) as t:
        p = t.pages[0]
        assert p.rowsperstrip == 1 and p.compression == 8, (p.rowsperstrip, p.compression)
        pred = p.predictor
        offs, cnts = p.dataoffsets, p.databytecounts
        width = p.shape[1]
        out = np.zeros(SHAPE, np.uint8)
        fh = t.filehandle
        for i in range(SHAPE[0]):
            fh.seek(offs[ROW0 + i])
            row = np.frombuffer(zlib.decompress(fh.read(cnts[ROW0 + i])), np.uint8)
            assert row.size == width
            if pred == 2:
                row = np.cumsum(row, dtype=np.uint8)
            out[i] = row[COL0:COL0 + SHAPE[1]]
            if i % 10000 == 0:
                print(f"  row {i}/{SHAPE[0]}", flush=True)
    np.save(OUT, out)
    print("values:", np.unique(out[::50, ::50], return_counts=True))


if __name__ == "__main__":
    main()
