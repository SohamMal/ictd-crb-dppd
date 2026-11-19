"""
Figures for the final deck (report/final_deck_outline.md). Real data and real imagery only.

Reads finished outputs (and the Earth Engine pulls of fetch_final_gee.py); writes
outputs/figures/final/fNN_*.png. Numbers printed to stdout so they can be checked against the report.

Run:  python Code/figures/fetch_final_gee.py   (once; Earth Engine)
      python Code/figures/make_final_figures.py
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "figures"))
from make_pd_figures import COLORS, load_map  # noqa: E402

OUT = ROOT / "outputs" / "figures" / "final"
RAW = OUT / "raw"
BURN = ROOT / "outputs" / "burn_tehsil_rf" / "tehsil_burn_measure.csv"
VERDICTS = ROOT / "outputs" / "burn_tehsil_rf" / "point_verdicts.csv"
POINTS = ROOT / "outputs" / "burn_tehsil" / "points.csv"
FIRES = ROOT / "outputs" / "burn_fire" / "tehsil_fires.csv"
MASTER = ROOT / "Data" / "punjab_homogeneous_grouping_master_transformed.csv"
DRIVERS = ROOT / "outputs" / "predictors" / "drivers"
SAMPLE = ROOT / "outputs" / "impact" / "sample_size_table.csv"
LABEL_IMG = ROOT / "outputs" / "burn_labelling" / "img"
PLANET = ROOT / "outputs" / "planet"
GT = ROOT / "Code" / "Ground Truth Data"

INK, INK_2, GRID = "#1f1a17", "#6b6560", "#e4e3df"
EMBER, GOOD, GOOD_2, BAD = "#e4572e", "#0f7b4a", "#7fd1a8", "#c0392b"
PD_YEARS = range(2020, 2025)

# Final labels after validation (report §4.3.3, outputs/pd/pd_validated.csv).
STRICT = ["Abohar"]
VALIDATED = ["Dinanagar", "Phagwara", "Jalandhar - I", "Adampur", "Talwandi Sabo"]
CAVEAT = ["Gurdaspur", "Banga"]
NDS = ["Lehra", "Zira", "Moonak", "Guruharsahai"]
PDS = STRICT + VALIDATED + CAVEAT
SHORT = {"Jalandhar - I": "Jalandhar-I"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.edgecolor": INK_2,
    "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 200,
    "savefig.bbox": "tight", "savefig.facecolor": "white",
})


def save(fig, name):
    fig.savefig(OUT / name)
    plt.close(fig)
    print("saved", name)


def mean_burn():
    b = pd.read_csv(BURN)
    return b[b.year.isin(PD_YEARS)].groupby("lgd_tehsil_code").burnt_share.mean().rename("mean_share")


# ---------- 1. one field through the season (Sentinel-2, 2022) ----------
def f01_season():
    frames = [("20221001", "1 Oct\npaddy standing"), ("20221021", "21 Oct\nripening"),
              ("20221029", "29 Oct\nharvested"), ("20221113", "13 Nov\ncleared"),
              ("20221130", "30 Nov\nsown"), ("20221215", "15 Dec\nwheat up")]
    fig, axes = plt.subplots(1, len(frames), figsize=(14, 3.0))
    for ax, (d, lab) in zip(axes, frames):
        im = Image.open(LABEL_IMG / f"CE000_{d}_tc.png").convert("RGB").resize((480, 480), Image.NEAREST)
        ax.imshow(im)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(lab, fontsize=13, color=INK)
    fig.tight_layout(w_pad=0.6)
    save(fig, "f01_season_field.png")


# ---------- 2. fire counts collapse ----------
def f02_viirs():
    f = pd.read_csv(FIRES).groupby("year").fire_all.sum()
    b = pd.read_csv(BURN)
    share = b.groupby("year").apply(lambda d: d.burnt_ha.sum() / d.rice_ha.sum(), include_groups=False)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"wspace": 0.3})
    a1.bar(f.index, f.values / 1000, color=[INK_2 if y < 2024 else BAD for y in f.index], width=0.7)
    for y, v in f.items():
        a1.text(y, v / 1000 + 0.4, f"{v/1000:.1f}k", ha="center", fontsize=11, color=INK)
    a1.set_title("VIIRS active fires, Punjab, 15 Sep–30 Nov", loc="left", fontsize=13, color=INK)
    a1.set_ylabel("fires (thousands)")
    a1.set_xticks(f.index)
    a2.bar(share.index, share.values * 100, color=[EMBER if y < 2024 else "#f2b8a5" for y in share.index],
           width=0.7, hatch=[None if y < 2024 else "//" for y in share.index])
    for y, v in share.items():
        a2.text(y, v * 100 + 1.2, f"{v*100:.0f}%", ha="center", fontsize=11, color=INK)
    a2.set_title("Our measure: share of paddy area burnt", loc="left", fontsize=13, color=INK)
    a2.set_ylim(0, 80)
    a2.set_xticks(share.index)
    a2.text(2024, 72, "doubtful", ha="center", fontsize=10, color=INK_2)
    save(fig, "f02_viirs_collapse.png")
    print("  fires", f.to_dict(), "\n  share", share.round(3).to_dict())


# ---------- 3. final PD map ----------
def f03_pd_map(gdf, name="f03_pd_map.png", labels=True, size=7.2):
    style = {**{n: GOOD for n in STRICT}, **{n: "#2fa36b" for n in VALIDATED},
             **{n: GOOD_2 for n in CAVEAT}, **{n: BAD for n in NDS}}
    base = {"Central": "#e9edf3", "South-west": "#f6e7de", "Foothills": "#eef5f1", "Outlier": "#f5f5f3"}
    g = gdf.copy()
    fig, ax = plt.subplots(figsize=(size, size))
    g.plot(ax=ax, color=g["group"].map(base), edgecolor="white", linewidth=0.5)
    hit = g[g.lgd_tehsil_name.isin(style)]
    hit.plot(ax=ax, color=hit.lgd_tehsil_name.map(style), edgecolor="white", linewidth=0.5)
    g.dissolve("group").boundary.plot(ax=ax, color=INK_2, linewidth=0.9)
    if labels:
        off = {"Abohar": (-70, -30), "Talwandi Sabo": (10, -30), "Dinanagar": (25, 12),
               "Gurdaspur": (-85, 5), "Phagwara": (50, -30), "Adampur": (-80, 0), "Jalandhar - I": (-60, -55),
               "Banga": (45, 18), "Lehra": (25, -12), "Zira": (-70, 22), "Moonak": (25, -18),
               "Guruharsahai": (-95, 5)}
        for _, r in hit.iterrows():
            p = r.geometry.representative_point()
            n = r.lgd_tehsil_name
            ax.annotate(SHORT.get(n, n), (p.x, p.y), xytext=off.get(n, (12, 8)), textcoords="offset points",
                        fontsize=11, color=INK, weight="bold" if n in STRICT else "normal",
                        arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.6))
    handles = [Patch(color=GOOD, label="Strict PD"), Patch(color="#2fa36b", label="Validated PD"),
               Patch(color=GOOD_2, label="PD with caveat"), Patch(color=BAD, label="Negative deviant (contrast)"),
               Patch(facecolor=base["Central"], edgecolor=INK_2, label="Central"),
               Patch(facecolor=base["South-west"], edgecolor=INK_2, label="South-west"),
               Patch(facecolor=base["Foothills"], edgecolor=INK_2, label="Foothills (not ranked)")]
    ax.legend(handles=handles, frameon=False, loc="upper left", bbox_to_anchor=(0.88, 0.98), fontsize=11)
    ax.set_axis_off()
    save(fig, name)


# ---------- 4. grouping variables ----------
def f04_variables(gdf):
    m = pd.read_csv(MASTER)
    g = gdf.merge(m[["lgd_tehsil_code", "rice_share_2022_cal", "mean_monsoon_rainfall_mm",
                     "aesr_dominant", "mean_extraction_pct_2022", "dominant_particle_size"]], on="lgd_tehsil_code")
    panels = [("rice_share_2022_cal", "Rice share", "YlGn", None), ("mean_monsoon_rainfall_mm", "Monsoon rain", "Blues", None),
              ("aesr_dominant", "Agro-ecological zone", "Set2", "cat"),
              ("mean_extraction_pct_2022", "Groundwater use", "OrRd", None),
              ("dominant_particle_size", "Soil type", "Pastel1", "cat")]
    fig, axes = plt.subplots(1, 5, figsize=(16, 4.2))
    for ax, (col, lab, cmap, kind) in zip(axes, panels):
        if kind == "cat":
            g[col] = g[col].astype(str)
            g.plot(ax=ax, column=col, cmap=cmap, categorical=True, edgecolor="white", linewidth=0.3)
        else:
            g.plot(ax=ax, column=col, cmap=cmap, edgecolor="white", linewidth=0.3)
        g.dissolve("group").boundary.plot(ax=ax, color=INK, linewidth=0.6)
        ax.set_title(lab, fontsize=14, color=INK)
        ax.set_axis_off()
    fig.tight_layout(w_pad=0.2)
    save(fig, "f04_grouping_variables.png")


# ---------- 5/6. PlanetScope strips ----------
def planet_days():
    """[(date, [(sr[b,r,c], clear[r,c], (x0,dx,y0,dy))], epsg)] via the GDAL-free reader
    (rasterio's DLL is blocked by Windows Application Control)."""
    import pickle
    cache = RAW / "planet_days_jalandhar_2021.pkl"  # pure-Python LZW is slow; cache the decoded scenes
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    sys.path.insert(0, str(ROOT / "Code" / "planet"))
    import tiffread
    out, box = [], None
    for p in sorted((PLANET / "orders").glob("jalandhar_2021_*")):
        sr = sorted(p.glob("*_SR_clip.tif"))
        if not sr:
            continue
        scenes = []
        for t in sr:
            a, (ox, dx, oy, dy), epsg = tiffread.read(t)
            u, _, _ = tiffread.read(str(t).replace("_AnalyticMS_SR_clip", "_udm2_clip"))
            # stretch from the whole scene (as planet_strips.py), then keep only the area around the
            # two example fields so the cache stays small
            valid = a[[2, 1, 0]][:, (a[:3] > 0).all(0)].astype(float)
            lohi = (np.percentile(valid, 2, axis=1), np.percentile(valid, 98, axis=1))
            if box is None:
                from shapely.ops import unary_union
                box = unary_union([field_geom(f, epsg) for f in (263, 265)]).buffer(400).bounds
            x0, y0, x1, y1 = box
            c0, c1 = max(int((x0 - ox) / dx), 0), min(int(np.ceil((x1 - ox) / dx)), a.shape[2])
            r0, r1 = max(int((y1 - oy) / dy), 0), min(int(np.ceil((y0 - oy) / dy)), a.shape[1])
            if c1 <= c0 or r1 <= r0:
                continue
            scenes.append((a[:, r0:r1, c0:c1].copy(), u[0, r0:r1, c0:c1].copy(),
                           (ox + c0 * dx, dx, oy + r0 * dy, dy), lohi))
        out.append((date.fromisoformat(p.name[-10:]), scenes, epsg))
    cache.write_bytes(pickle.dumps(out))
    return out


def field_geom(fid, epsg):
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform
    feats = json.loads((GT / "partially_completely_burnt_2021_10_29.geojson").read_text())["features"]
    f = next(f for f in feats if f["properties"]["field_id"] == fid)
    to_r = Transformer.from_crs(4326, epsg, always_xy=True).transform
    return transform(to_r, shape(f["geometry"]))


PAD = 60  # m around the field, as in Code/planet/planet_strips.py


def chip(scenes, g):
    """Clearest crop of the field among one day's scenes: (rgb, extent) or None."""
    x0, y0, x1, y1 = g.buffer(PAD).bounds
    best = None
    for a, clear, (ox, dx, oy, dy), (lo, hi) in scenes:
        c0, c1 = int((x0 - ox) / dx), int(np.ceil((x1 - ox) / dx))
        r0, r1 = int((y1 - oy) / dy), int(np.ceil((y0 - oy) / dy))
        if c0 < 0 or r0 < 0 or c1 > a.shape[2] or r1 > a.shape[1]:
            continue
        img = a[[2, 1, 0], r0:r1, c0:c1].astype(float)
        if (img > 0).all(0).mean() < 0.95:
            continue
        share = clear[r0:r1, c0:c1].astype(bool).mean()
        if best is None or share > best[0]:
            rgb = np.clip((img - lo[:, None, None]) / (hi - lo)[:, None, None], 0, 1).transpose(1, 2, 0)
            ext = (ox + c0 * dx, ox + c1 * dx, oy + r1 * dy, oy + r0 * dy)
            best = (share, rgb, ext)
    return None if best is None else best[1:]


def strip_row(axes, days, fid, picks, s2=None):
    g = field_geom(fid, days[0][2])
    by_day = {d: sc for d, sc, _ in days}
    for ax, d in zip(axes, picks):
        ax.set_xticks([]); ax.set_yticks([])
        c = chip(by_day[d], g)
        if c is None:
            ax.set_facecolor("0.9")
        else:
            ax.imshow(c[0], extent=c[1])
            for poly in getattr(g, "geoms", [g]):
                ax.plot(*poly.exterior.xy, color="cyan", lw=1.4)
        ax.set_title(f"{d:%d %b}", fontsize=12, color=INK)
        if s2 is not None and d in s2:
            for sp in ax.spines.values():
                sp.set_color(EMBER); sp.set_linewidth(4)


def f05_planet_pair(days):
    rule = pd.read_csv(PLANET / "jalandhar_planet_rule_fields.csv").set_index("field_id")
    have = [d for d, _, _ in days]

    def window(center, n=7):
        c = date.fromisoformat(center)
        return sorted(sorted(have, key=lambda d: abs((d - c).days))[:n])

    epsg = days[0][2]
    by_day = {d: sc for d, sc, _ in days}

    def usable(fid):
        g = field_geom(fid, epsg)
        return [d for d in have if chip(by_day[d], g) is not None]

    rows = []
    for fid, lab in [(263, "Burnt field"), (265, "Ploughed, not burnt")]:
        have_f = usable(fid)
        c = date.fromisoformat(rule.loc[fid, "burn_day"])
        rows.append((fid, lab, sorted(sorted(have_f, key=lambda d: abs((d - c).days))[:7])))
    fig, axes = plt.subplots(2, 7, figsize=(15, 5.2))
    for r, (fid, lab, picks) in enumerate(rows):
        strip_row(axes[r], days, fid, picks)
        axes[r][0].set_ylabel(lab, fontsize=14, color=INK, labelpad=10)
    fig.tight_layout(h_pad=1.2, w_pad=0.4)
    save(fig, "f05_planet_burnt_vs_ploughed.png")
    print("  burn days", rule.loc[[263, 265], ["burn_day", "label"]].to_dict())


def f06_planet_vs_s2(days):
    s2 = pd.read_csv(RAW / "s2_dates_jalandhar_2021.csv")
    s2c = {date.fromisoformat(d) for d in s2[s2.clear].date}
    picks = [d for d, _, _ in days if date(2021, 10, 30) <= d <= date(2021, 11, 9)]
    cols = (len(picks) + 1) // 2
    fig, axes = plt.subplots(2, cols, figsize=(2.6 * cols, 4.6))
    axes = axes.ravel()
    for ax in axes[len(picks):]:
        ax.set_axis_off()
    strip_row(axes, days, 263, picks, s2=s2c)
    fig.tight_layout(w_pad=0.3)
    save(fig, "f06_planet_vs_s2.png")
    print("  S2 clear dates", sorted(s2c), "\n  Planet days shown", picks)


# ---------- 7. detector before/after ----------
def f07_detector():
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    x = np.arange(2)
    old, new = [98, 81], [90, 18]
    ax.bar(x - 0.18, old, 0.34, color="#bdb6b0", label="First detector (season index)")
    ax.bar(x + 0.18, new, 0.34, color=EMBER, label="Current detector")
    for i in range(2):
        ax.text(x[i] - 0.18, old[i] + 2, f"{old[i]}%", ha="center", fontsize=13)
        ax.text(x[i] + 0.18, new[i] + 2, f"{new[i]}%", ha="center", fontsize=13, weight="bold")
    ax.set_xticks(x, ["Burns caught\n(higher is better)", "Ploughed fields called burnt\n(lower is better)"])
    ax.set_ylim(0, 115); ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=10, bbox_to_anchor=(0.5, 1.08))
    save(fig, "f07_detector_bars.png")


# ---------- 8. points over two tehsils ----------
def f08_points(gdf):
    pts = pd.read_csv(POINTS)
    v = pd.read_csv(VERDICTS)
    v = v[v.year == 2022][["loc", "burnt"]]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
    for ax, name in zip(axes, ["Phagwara", "Lehra"]):
        meta = json.loads((RAW / f"tehsil_{name.lower()}.json").read_text())
        x0, y0, x1, y1 = meta["bounds"]
        ax.imshow(Image.open(RAW / f"tehsil_{name.lower()}.png").convert("RGB"), extent=(x0, x1, y0, y1))
        poly = gdf[gdf.lgd_tehsil_name == name]
        poly.boundary.plot(ax=ax, color="white", linewidth=1.6)
        code = poly.lgd_tehsil_code.iloc[0]
        p = pts[pts.lgd_tehsil_code == code].merge(v, on="loc", how="left")
        col = p.burnt.map({1.0: EMBER, 0.0: "#2fd6ff"}).fillna("#bbbbbb")
        ax.scatter(p.lon, p.lat, s=46, c=col, edgecolor="black", linewidth=0.6, zorder=3)
        share = p.burnt.mean()
        ax.set_title(f"{name}: {share*100:.0f}% of points burnt (2022)", fontsize=14, color=INK)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        ax.set_axis_off()
        print(f"  {name} {meta['date']} n={len(p)} burnt={share:.2f}")
    h = [Line2D([], [], marker="o", ls="", mfc=EMBER, mec="black", ms=9, label="burnt"),
         Line2D([], [], marker="o", ls="", mfc="#2fd6ff", mec="black", ms=9, label="not burnt")]
    fig.legend(handles=h, frameon=False, loc="lower center", ncol=2, fontsize=12)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "f08_points_two_tehsils.png")


# ---------- 9. yearly maps ----------
def f09_yearly(gdf):
    b = pd.read_csv(BURN)
    fig, axes = plt.subplots(1, 5, figsize=(16, 3.9))
    for ax, y in zip(axes, PD_YEARS):
        g = gdf.merge(b[b.year == y][["lgd_tehsil_code", "burnt_share"]], on="lgd_tehsil_code")
        g.plot(ax=ax, column="burnt_share", cmap="YlOrRd", vmin=0, vmax=0.9, edgecolor="white", linewidth=0.3)
        ax.set_title(str(y), fontsize=14, color=INK)
        ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=plt.Normalize(0, 0.9))
    cb = fig.colorbar(sm, ax=axes, orientation="horizontal", fraction=0.05, pad=0.02, shrink=0.4)
    cb.set_label("share of points burnt")
    save(fig, "f09_yearly_maps.png")


# ---------- 10. Abohar vs its group ----------
def f10_abohar():
    b = pd.read_csv(BURN)
    b = b[b.year.isin(PD_YEARS)]
    sw = b[b.group == "South-west"]
    q = sw.groupby("year").burnt_share.quantile([0.25, 0.5, 0.75]).unstack()
    ab = b[b.lgd_tehsil_name == "Abohar"].set_index("year").burnt_share
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.fill_between(q.index, q[0.25] * 100, q[0.75] * 100, color=COLORS["South-west"], alpha=0.18,
                    label="middle half of South-west tehsils")
    ax.plot(q.index, q[0.5] * 100, color=COLORS["South-west"], lw=2.5, marker="o", label="South-west median")
    ax.plot(ab.index, ab.values * 100, color=GOOD, lw=3, marker="o", label="Abohar")
    for y, v in ab.items():
        ax.text(y, v * 100 - 6, f"{v*100:.0f}%", ha="center", color=GOOD, fontsize=11)
    ax.set_ylim(0, 100); ax.set_ylabel("share of points burnt (%)")
    ax.set_xticks(list(PD_YEARS))
    ax.yaxis.grid(True, color=GRID)
    ax.legend(frameon=False, loc="upper left", fontsize=11, ncol=1)
    save(fig, "f10_abohar_vs_group.png")
    print("  Abohar", ab.round(2).to_dict(), "SW median", q[0.5].round(2).to_dict())


# ---------- 11. validation grid (report Table 7) ----------
def f11_validation():
    checks = ["Resam-\npling", "Other\nsettings", "Clear\nlooks", "Rice\nmap", "Real paddy\nfields",
              "Harvest\ntiming"]
    rows = [("Abohar", "pppfpp", "validated"), ("Dinanagar", "pppfpp", "validated"),
            ("Phagwara", "pppfpp", "validated"), ("Jalandhar-I", "pppfpp", "validated"),
            ("Adampur", "pppfpp", "validated"), ("Talwandi Sabo", "pppppp", "validated"),
            ("Gurdaspur", "ppffpp", "caveat"), ("Banga", "fppfpf", "caveat"),
            ("Samana (trend)", "xppppp", "dropped"), ("Dirba (trend)", "xppppp", "dropped")]
    # column order: V1, V2, V3, V4, V4b, V5 -> fix Banga: V1 flag, V2 ok, V3 ok, V4 flag, V4b flag, V5 ok
    rows[7] = ("Banga", "fppffp", "caveat")
    sym = {"p": ("✔", GOOD), "f": ("!", "#d39b22"), "x": ("✘", BAD)}
    fig, ax = plt.subplots(figsize=(11, 5.6))
    for i, (name, s, lab) in enumerate(rows):
        y = len(rows) - i
        fade = lab == "dropped"
        ax.text(-0.55, y, name, ha="right", va="center", fontsize=13, color=INK_2 if fade else INK)
        for j, c in enumerate(s):
            t, col = sym[c]
            ax.add_patch(Rectangle((j - 0.42, y - 0.4), 0.84, 0.8, color="#f5f4f2" if not fade else "#fbfbfa"))
            ax.text(j, y, t, ha="center", va="center", fontsize=16, color=col, weight="bold",
                    alpha=0.5 if fade and c != "x" else 1)
        lc = {"validated": GOOD, "caveat": "#d39b22", "dropped": BAD}[lab]
        ax.text(len(checks) - 0.2, y, {"validated": "validated PD", "caveat": "PD with caveat",
                                       "dropped": "dropped"}[lab], va="center", fontsize=13, color=lc, weight="bold")
    for j, c in enumerate(checks):
        ax.text(j, len(rows) + 0.85, c, ha="center", va="bottom", fontsize=11.5, color=INK_2, rotation=0, wrap=True)
    ax.set_xlim(-2.9, len(checks) + 1.6); ax.set_ylim(0.3, len(rows) + 1.6)
    ax.set_axis_off()
    save(fig, "f11_validation_grid.png")


# ---------- 12. burning vs rice share ----------
def f12_rice(gdf):
    m = pd.read_csv(MASTER)[["lgd_tehsil_code", "rice_share_2022_cal"]]
    d = gdf.drop(columns="geometry").merge(m, on="lgd_tehsil_code").merge(mean_burn(), on="lgd_tehsil_code")
    d = d[d.group.isin(["Central", "South-west"])]
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for grp, s in d.groupby("group"):
        ax.scatter(s.rice_share_2022_cal * 100, s.mean_share * 100, s=40, color=COLORS[grp], alpha=0.55,
                   edgecolor="white", label=grp)
    for n in PDS + NDS:
        r = d[d.lgd_tehsil_name == n]
        if r.empty:
            continue
        x, y = r.rice_share_2022_cal.iloc[0] * 100, r.mean_share.iloc[0] * 100
        ax.scatter(x, y, s=90, facecolor="none", edgecolor=GOOD if n in PDS else BAD, linewidth=2.2, zorder=4)
        off = {"Gurdaspur": (2, -14), "Phagwara": (8, 4), "Adampur": (-58, -12)}.get(n, (6, -4 if n in PDS else 4))
        ax.annotate(SHORT.get(n, n), (x, y), xytext=off, textcoords="offset points",
                    fontsize=10, color=GOOD if n in PDS else BAD)
    ax.set_xlabel("rice share of tehsil area, 2022 (%)")
    ax.set_ylabel("mean share burnt 2020–24 (%)")
    ax.yaxis.grid(True, color=GRID)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "f12_burn_vs_rice.png")


# ---------- 13. driver chart ----------
def f13_drivers():
    s = pd.read_csv(DRIVERS / "driver_summary.csv")
    short = {"d6_urban_area_share": "Urban area share", "d1_turnaround_days": "Harvest-to-sowing days",
             "d3_cultivators_per_100ha_rice": "Small farms (cultivators/ha)",
             "d2_early_canopy_share": "Early second crop", "d4_km_nearest_buyer": "km to straw buyer",
             "d4_buyers_within_30km": "Straw buyers ≤ 30 km", "d3_labourers_per_cultivator": "Labour per cultivator",
             "d9_bovines_per_cultivator": "Cattle per cultivator", "d7_basmati_share_district": "Basmati share",
             "d6_km_urban_centre": "km to town", "d5_km_interstate_border": "km to state border"}
    bin_ = {"d6_urban_area_share": GOOD, "d1_turnaround_days": "#d39b22", "d3_cultivators_per_100ha_rice": "#d39b22"}
    s = s[s.driver.isin(short)].copy()
    s["sign_rho"] = s["rho_Central"] * s["expected_sign"]
    s["sign_partial"] = s["partial_rho_Central"] * s["expected_sign"]
    s = s.sort_values("sign_rho")
    fig, ax = plt.subplots(figsize=(9, 5.6))
    for i, r in enumerate(s.itertuples()):
        c = bin_.get(r.driver, "#b5aea8")
        ax.plot([r.sign_rho, r.sign_partial], [i, i], color=c, lw=2.5)
        ax.scatter(r.sign_rho, i, s=80, color=c, zorder=3)
        ax.scatter(r.sign_partial, i, s=80, facecolor="white", edgecolor=c, linewidth=2, zorder=3)
    ax.set_yticks(range(len(s)), [short[d] for d in s.driver], fontsize=12)
    ax.axvline(0, color=INK_2, lw=0.8)
    ax.set_xlabel("← works against less burning      link with less burning (Central, Spearman) →")
    h = [Line2D([], [], marker="o", ls="", color=INK_2, ms=9, label="raw link"),
         Line2D([], [], marker="o", ls="", mfc="white", mec=INK_2, mew=2, ms=9, label="rice share held constant"),
         Patch(color=GOOD, label="consistent"), Patch(color="#d39b22", label="mostly rice share"),
         Patch(color="#b5aea8", label="no consistent link")]
    ax.legend(handles=h, frameon=False, loc="lower right", fontsize=10.5)
    ax.xaxis.grid(True, color=GRID)
    save(fig, "f13_drivers.png")


# ---------- 14. Doaba far from towns ----------
def f14_doaba():
    u = pd.read_csv(DRIVERS / "urban_check_far_points.csv")
    names = ["Dinanagar", "Phagwara", "Jalandhar - I", "Adampur"]
    u = u.set_index("lgd_tehsil_name").loc[names]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    x = np.arange(len(names))
    ax.bar(x - 0.18, u.all_share_centre * 100, 0.34, color="#9fc3ea", label="all fields")
    ax.bar(x + 0.18, u.far_share_centre * 100, 0.34, color=COLORS["Central"], label="fields > 5 km from any town")
    ax.axhline(61, color=INK_2, ls="--", lw=1.2)
    ax.text(len(names) - 0.5, 62.5, "Central median 61%", ha="right", fontsize=11, color=INK_2)
    for i, (a, f) in enumerate(zip(u.all_share_centre, u.far_share_centre)):
        ax.text(i - 0.18, a * 100 + 1.2, f"{a*100:.0f}", ha="center", fontsize=11)
        ax.text(i + 0.18, f * 100 + 1.2, f"{f*100:.0f}", ha="center", fontsize=11, weight="bold")
    ax.set_xticks(x, [SHORT.get(n, n) for n in names], fontsize=12)
    ax.set_ylim(0, 75); ax.set_ylabel("share burnt (%)")
    ax.legend(frameon=False, loc="upper left", fontsize=11)
    save(fig, "f14_doaba_far_fields.png")
    print("  far", u[["all_share_centre", "far_share_centre", "far_point_share_centre"]].round(3).to_dict())


# ---------- 15. Abohar percentiles ----------
def f15_abohar_profile():
    p = pd.read_csv(DRIVERS / "unit_profiles.csv").set_index("lgd_tehsil_name").loc["Abohar"]
    items = [("d4_km_nearest_buyer", "Straw buyer inside the tehsil", True),
             ("d3_labourers_per_cultivator", "Farm labourers per cultivator", False),
             ("d9_bovines_per_cultivator", "Cattle + buffalo per cultivator", False),
             ("d2_early_canopy_share", "Early second crop", False),
             ("d7_basmati_share_district", "Basmati share (district)", False),
             ("d6_urban_area_share", "Urban area share", False)]
    vals = [(lab, (1 - p[f"{c}_pct"]) if inv else p[f"{c}_pct"]) for c, lab, inv in items]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for i, (lab, v) in enumerate(vals[::-1]):
        ax.barh(i, 100, color="#f1f0ee", height=0.6)
        ax.barh(i, v * 100, color=GOOD if v >= 0.8 else "#b5aea8", height=0.6)
        ax.text(v * 100 + 1.5, i, f"{v*100:.0f}th", va="center", fontsize=12)
    ax.set_yticks(range(len(vals)), [l for l, _ in vals[::-1]], fontsize=12)
    ax.set_xlim(0, 112); ax.set_xticks([0, 50, 100])
    ax.set_xlabel("Abohar's percentile within South-west tehsils")
    save(fig, "f15_abohar_profile.png")
    print("  Abohar pct", dict(vals))


# ---------- 16. sample size ----------
def f16_sample():
    t = pd.read_csv(SAMPLE)
    t = t[(t.target == 2023) & (t.k == 2) & (t.points == 30)]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    for pc, c in zip([0.9, 0.7, 0.5], ["#9fc3ea", COLORS["Central"], "#16457e"]):
        s = t[np.isclose(t.pi_c, pc)].sort_values("delta")
        ax.plot(s.delta * 100, s.n_ancova, marker="o", color=c, lw=2.2, label=f"year-to-year steadiness {pc}")
    mid = t[np.isclose(t.pi_c, 0.7) & np.isclose(t.delta, 0.1)].n_ancova.iloc[0]
    ax.scatter([10], [mid], s=160, facecolor="none", edgecolor=EMBER, linewidth=2.5, zorder=5)
    ax.annotate(f"design: {mid} villages per arm", (10, mid), xytext=(20, 30), textcoords="offset points",
                fontsize=12, color=EMBER, arrowprops=dict(arrowstyle="-", color=EMBER))
    ax.set_xlabel("drop in burning to detect (percentage points)")
    ax.set_ylabel("villages per arm")
    ax.set_yscale("log"); ax.set_yticks([10, 20, 50, 100, 200], ["10", "20", "50", "100", "200"])
    ax.yaxis.grid(True, color=GRID)
    ax.legend(frameon=False, fontsize=10.5)
    save(fig, "f16_sample_size.png")
    print("  mid case n =", mid)


# ---------- 17. ground-truth coverage ----------
def f17_ground_truth(gdf):
    import zipfile
    z = zipfile.ZipFile(GT / "Walker" / "burntfields_punjab-v1.0.0.zip")
    aoi = gpd.read_file(z.open("klwalker-sb-burntfields_punjab-5c604ec/data/AOI.geojson"))
    if aoi.crs is None:
        aoi = aoi.set_crs(4326)
    ceew = pd.concat([gpd.read_file(GT / f) for f in ["partially_completely_burnt_2021_10_29.geojson",
                                                         "partially_completely_burnt_2020_11_10.geojson"]])
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    gdf.plot(ax=ax, color="#f3f2ef", edgecolor="white", linewidth=0.4)
    gdf.dissolve("group").boundary.plot(ax=ax, color=INK_2, linewidth=0.7)
    aoi.to_crs(gdf.crs).plot(ax=ax, facecolor=EMBER, alpha=0.35, edgecolor=EMBER, linewidth=1.5)
    c = ceew.to_crs(gdf.crs).geometry.centroid
    ax.scatter(c.x, c.y, s=10, color=COLORS["Central"], zorder=3)
    ax.legend(handles=[Patch(facecolor=EMBER, alpha=0.4, label="Walker et al. 2019 (burnt vs ploughed)"),
                       Line2D([], [], marker="o", ls="", color=COLORS["Central"], label="CEEW visited fields 2020–21")],
              frameon=False, loc="upper left", bbox_to_anchor=(0.62, 0.98), fontsize=11)
    ax.set_axis_off()
    save(fig, "f17_ground_truth_coverage.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gdf = load_map()
    only = set(sys.argv[1:])
    run = lambda k: not only or k in only  # noqa: E731
    if run("f01"): f01_season()
    if run("f02"): f02_viirs()
    if run("f03"): f03_pd_map(gdf)
    if run("f04"): f04_variables(gdf)
    if run("f05") or run("f06"):
        days = planet_days()
        if run("f05"): f05_planet_pair(days)
        if run("f06"): f06_planet_vs_s2(days)
    if run("f07"): f07_detector()
    if run("f08"): f08_points(gdf)
    if run("f09"): f09_yearly(gdf)
    if run("f10"): f10_abohar()
    if run("f11"): f11_validation()
    if run("f12"): f12_rice(gdf)
    if run("f13"): f13_drivers()
    if run("f14"): f14_doaba()
    if run("f15"): f15_abohar_profile()
    if run("f16"): f16_sample()
    if run("f17"): f17_ground_truth(gdf)


if __name__ == "__main__":
    main()


# ================= method figures (added 2026-11-20) =================
def f18_gower_example():
    """Real per-dimension Gower scores for two pairs (json for a pptx table)."""
    sys.path.insert(0, str(ROOT / "Code" / "grouping"))
    import config
    from gower import gower_matrix
    df = pd.read_csv(config.MASTER_CSV)
    dist, per_dim = gower_matrix(df, config.DIMENSIONS, range_exclude=("Dhar Kalan",))
    names = df[config.NAME_COL].tolist()
    pairs = [("Phagwara", "Adampur"), ("Phagwara", "Abohar")]
    out = {}
    for a, b in pairs:
        i, j = names.index(a), names.index(b)
        out[f"{a}|{b}"] = {**{d: round(float(per_dim[d][i, j]), 2) for d in config.DIMENSIONS},
                           "distance": round(float(dist[i, j]), 2)}
    cols = ["rice_share_2022_cal", "mean_monsoon_rainfall_mm", "aesr_dominant", "mean_extraction_pct_2022",
            "dominant_particle_size"]
    vals = df.set_index(config.NAME_COL).loc[["Phagwara", "Adampur", "Abohar"], cols]
    out["values"] = json.loads(vals.to_json(orient="index"))
    (OUT / "f18_gower_example.json").write_text(json.dumps(out, indent=1))
    print("  gower", {k: v for k, v in out.items() if k != "values"})


def f19_detector_series():
    """Two real sample points (Lehra, 2022): both flagged; the forest keeps one, rejects one."""
    # same steps as Code/burn/tehsil_metric_rf.looks (that module imports rasterio, blocked here)
    sys.path.insert(0, str(ROOT / "Code" / "planet"))
    import s2_from_planet_labels as w
    raw_dir = ROOT / "outputs" / "burn_tehsil_rf" / "raw"

    def looks(s):
        d = s.copy()
        bands = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B11", "B12"]
        d[bands] = d[bands] / 10000
        d["NDVI"] = (d.B8 - d.B4) / (d.B8 + d.B4)
        d["NBR"] = (d.B8 - d.B12) / (d.B8 + d.B12)
        d["NBR2"] = (d.B11 - d.B12) / (d.B11 + d.B12)
        d["BAIS2"] = w.bais2(d.B4, d.B6, d.B7, d.B8, d.B12)
        d["TCB"] = w.tcb(d.B2, d.B3, d.B4, d.B8, d.B11, d.B12)
        d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=w.VARS)
        sc, m = w.lp.model()
        d["z"] = m.decision_function(sc.transform(d[["BAIS2", "TCB"]].to_numpy()))
        return d.sort_values(["loc", "date"])
    v = pd.read_csv(VERDICTS, parse_dates=["candidate_date", "pre_date"])
    pts = pd.read_csv(POINTS)
    code = gpd.read_file(ROOT / "Data" / "Rice" / "rice_area_output" / "punjab_current_tehsils_lgd.gpkg")
    code = int(code[code.lgd_tehsil_name_current == "Lehra"].lgd_tehsil_code.iloc[0])
    vv = v[(v.year == 2022) & v["loc"].str.startswith(f"T{code}_") & v.prob.notna()]
    yes = vv.sort_values("prob").iloc[-1]
    no = vv[vv.prob < 0.2].sort_values("candidate_z").iloc[-1]
    batch = int(pts[pts["loc"] == yes["loc"]].batch.iloc[0])
    raw = pd.concat([pd.read_csv(f, parse_dates=["date"]) for f in raw_dir.glob("s2_2022_b*.csv")])
    raw = raw[raw["loc"].isin([yes["loc"], no["loc"]])]
    d = looks(raw)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.3), sharey=True)
    for ax, r, lab in [(axes[0], yes, "burnt"), (axes[1], no, "not burnt")]:
        g = d[(d["loc"] == r["loc"]) & (d.date >= "2022-09-15") & (d.date <= "2022-11-30")]
        ax.axhline(0, color=INK_2, lw=1, ls="--")
        ax.text(pd.Timestamp("2022-09-16"), 0.15, "flag line (score > 0)", fontsize=10, color=INK_2)
        ax.plot(g.date, g.z, "-o", color=INK, ms=5, lw=1.5)
        c, p = r.candidate_date, r.pre_date
        ax.scatter([p], g[g.date == p].z, s=160, facecolor="none", edgecolor=COLORS["Central"], lw=2.5, zorder=4)
        ax.scatter([c], g[g.date == c].z, s=160, facecolor="none", edgecolor=EMBER, lw=2.5, zorder=4)
        ax.annotate("before", (p, g[g.date == p].z.iloc[0]), xytext=(-20, -26), textcoords="offset points",
                    color=COLORS["Central"], fontsize=11)
        ax.annotate("candidate\n(sharpest jump)", (c, g[g.date == c].z.iloc[0]), xytext=(10, 6),
                    textcoords="offset points", color=EMBER, fontsize=11)
        col = EMBER if r.prob >= 0.786 else COLORS["Central"]
        ax.set_title(f"Forest: p = {r.prob:.2f} → {lab}", loc="left", fontsize=13, color=col)
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
        ax.yaxis.grid(True, color=GRID)
    axes[0].set_ylabel("burn-index score (BAIS2 + TCB)")
    fig.tight_layout()
    save(fig, "f19_detector_series.png")
    print("  points", yes["loc"], round(yes.prob, 2), no["loc"], round(no.prob, 2))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "methods":
    f18_gower_example()
    f19_detector_series()
