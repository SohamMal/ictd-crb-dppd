"""Minimal GeoTIFF reader for Planet clips without GDAL (rasterio's DLL is blocked by Windows
Application Control since 2026-10-26; imagecodecs too). Pure Python LZW + numpy.

read(path) -> (array [bands, rows, cols], transform (x0, dx, y0, dy), epsg)
Supports what Planet's analytic_sr_udm2 clips use: strips or tiles, LZW or none, predictor 1/2,
planar config 1 or 2, uint8/uint16.
"""
import site
import sys

sys.path.append(site.getusersitepackages())  # tifffile installed with --user; -I hides it
import numpy as np  # noqa: E402
import tifffile  # noqa: E402


def lzw_decode(data):
    out = bytearray()
    table = [bytes([i]) for i in range(256)] + [b"", b""]
    bits, nbits, pos, n = 0, 0, 0, len(data)
    width = 9
    prev = None
    while True:
        while nbits < width:
            if pos >= n:
                return bytes(out)
            bits = (bits << 8) | data[pos]
            pos += 1
            nbits += 8
        nbits -= width
        code = (bits >> nbits) & ((1 << width) - 1)
        bits &= (1 << nbits) - 1
        if code == 257:
            break
        if code == 256:
            table = table[:258]
            width = 9
            prev = None
            continue
        if prev is None:
            entry = table[code]
        elif code < len(table):
            entry = table[code]
            table.append(prev + entry[:1])
        else:
            entry = prev + prev[:1]
            table.append(entry)
        out += entry
        prev = entry
        # TIFF "early change": widen one code early
        if len(table) + 1 >= (1 << width) and width < 12:
            width += 1
    return bytes(out)


def read(path):
    with tifffile.TiffFile(path) as t:
        p = t.pages[0]
        comp, pred = int(p.compression), int(p.predictor)
        dt = np.dtype(p.dtype).newbyteorder("<" if t.byteorder == "<" else ">")
        spp = p.samplesperpixel
        planar = int(p.planarconfig)
        H, W = p.imagelength, p.imagewidth
        fh = t.filehandle
        if p.is_tiled:
            th, tw = p.tilelength, p.tilewidth
        else:
            th, tw = p.rowsperstrip, W
        segs = []
        for off, cnt in zip(p.dataoffsets, p.databytecounts):
            fh.seek(off)
            raw = fh.read(cnt)
            segs.append(lzw_decode(raw) if comp == 5 else raw if comp == 1 else None)
        if any(s is None for s in segs):
            raise ValueError(f"compression {comp} not supported")
        scale = p.tags["ModelPixelScaleTag"].value
        tie = p.tags["ModelTiepointTag"].value
        geokeys = p.tags["GeoKeyDirectoryTag"].value
    epsg = None
    for i in range(4, len(geokeys), 4):
        if geokeys[i] in (3072, 2048):
            epsg = geokeys[i + 3]
    nb = spp if planar == 2 else 1
    per = 1 if planar == 2 else spp
    ny, nx = -(-H // th), -(-W // tw)
    arr = np.zeros((spp, ny * th, nx * tw), dtype=dt.newbyteorder("="))
    k = 0
    for b in range(nb):
        for iy in range(ny):
            for ix in range(nx):
                buf = np.frombuffer(segs[k], dtype=dt)
                k += 1
                rows = buf.size // (tw * per)
                blk = buf[: rows * tw * per].reshape(rows, tw, per).astype(dt.newbyteorder("="))
                if pred == 2:
                    blk = np.cumsum(blk, axis=1, dtype=blk.dtype)
                if planar == 2:
                    arr[b, iy * th: iy * th + rows, ix * tw:(ix + 1) * tw] = blk[:, :, 0]
                else:
                    arr[:, iy * th: iy * th + rows, ix * tw:(ix + 1) * tw] = blk.transpose(2, 0, 1)
    arr = arr[:, :H, :W]
    x0 = tie[3] - tie[0] * scale[0]
    y0 = tie[4] + tie[1] * scale[1]
    return arr, (x0, scale[0], y0, -scale[1]), epsg
