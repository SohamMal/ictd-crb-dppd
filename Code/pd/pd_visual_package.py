"""
PD validation V7: blind visual check of the burn verdicts at PD and ND tehsils (2026-11-07)

Question: does the model miss fires (or read non-rice as "not burnt") more at the PDs than at the NDs? If it
does, a PD can be an artefact of the measure. Plan [C] Soham, 2026-11-07 (task_pd_validation.md).

Sample: 20 random panel points (outputs/burn_tehsil/points.csv, the points the tehsil measure uses) per
tehsil with a 2023 verdict, in Abohar, Dinanagar, Samana, Phagwara (PDs) and Zira, Lehra (ND controls).
Season 2023 (middle of 2020-24, not the weak 2024 season). Frames: every clear Sentinel-2 look at the
point (SCL 2/4/5/7) 1 Sep - 5 Dec, true colour + SWIR false colour (same chips as
Code/burn/labelling_package.py). Points are shuffled and renamed; tehsil and model verdict are not shown.

Labels: burnt / not burnt: ploughed or sown / standing or harvested after the window / not rice / can't tell.

Run:  python Code/pd/pd_visual_package.py            build outputs/pd/validation/v7/label_tool.html
      python Code/pd/pd_visual_package.py --score    after saving v7_labels.csv next to it
Out:  v7/label_tool.html, img/, points_meta.csv (hidden key); --score -> outputs/pd/validation/v7_visual.csv
"""

import argparse
import json
import random
import sys
from pathlib import Path

import ee
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Code" / "burn"))
import labelling_package as lp  # noqa: E402
from transfer_checks import init_ee  # noqa: E402

OUT = ROOT / "outputs" / "pd" / "validation" / "v7"
IMG = OUT / "img"
YEAR = 2023
SHOW = (f"{YEAR}-09-01", f"{YEAR}-12-06")
TEHSILS = {"Abohar": "PD", "Dinanagar": "PD", "Samana": "PD", "Phagwara": "PD", "Zira": "ND", "Lehra": "ND"}
N_PER = 20
CLEAR_SCL = {2, 4, 5, 7}
SEED = 42
LABELS = [("burnt", "Burnt"), ("ploughed_sown", "Not burnt: ploughed / sown"),
          ("standing_late", "Standing or harvested after 30 Nov"), ("not_rice", "Not rice (orchard, cotton, other)"),
          ("cant_tell", "Can't tell")]


def choose_points():
    pts = pd.read_csv(ROOT / "outputs" / "burn_tehsil" / "points.csv")
    g = pd.read_csv(ROOT / "outputs" / "grouping" / "FROZEN_groups.csv")[["lgd_tehsil_code", "lgd_tehsil_name"]]
    v = pd.read_csv(ROOT / "outputs" / "burn_tehsil_rf" / "point_verdicts.csv")
    v = v[(v.year == YEAR) & v.burnt.notna()][["loc", "candidate_date", "prob", "burnt", "burnt_05"]]
    pts = pts.merge(g, on="lgd_tehsil_code").merge(v, on="loc")
    pts = pts[pts.lgd_tehsil_name.isin(TEHSILS)]
    take = pts.groupby("lgd_tehsil_name").sample(N_PER, random_state=SEED)
    take = take.sample(frac=1, random_state=SEED).reset_index(drop=True)
    take["pid"] = [f"V7_{i + 1:03d}" for i in range(len(take))]
    take["kind"] = take.lgd_tehsil_name.map(TEHSILS)
    return take


def clear_looks(meta):
    """Clear Sentinel-2 images at each point in the display window (one per date)."""
    rows = []
    for name, d in meta.groupby("lgd_tehsil_name"):
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([r.lon, r.lat]), {"pid": r.pid}) for r in d.itertuples()])
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(fc.geometry())
               .filterDate(*SHOW).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))
        ids = col.aggregate_array("system:index").getInfo()
        for iid in ids:
            feats = ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + iid).select("SCL").sampleRegions(
                collection=fc, scale=20, geometries=False).getInfo()["features"]
            rows += [{"pid": f["properties"]["pid"], "image": iid, "date": iid[:8], "scl": int(f["properties"]["SCL"])}
                     for f in feats]
        print(f"  {name}: {len(ids)} images")
    s = pd.DataFrame(rows)
    s = s[s.scl.isin(CLEAR_SCL)]
    return s.sort_values(["date", "image"]).drop_duplicates(["pid", "date"])


def build_tool(meta, series):
    lp.IMG = IMG  # chips go to this package's img/
    tool = []
    for i, r in enumerate(meta.itertuples(), 1):
        ps = series[series.pid == r.pid].sort_values("date")
        frames = lp.fetch_frames(r.pid, r.lon, r.lat, ps.image.tolist())
        tool.append({"pid": r.pid, "lon": round(r.lon, 6), "lat": round(r.lat, 6),
                     "dates": [{"date": d, **frames[d]} for d in ps.date]})
        print(f"  frames {i}/{len(meta)} {r.pid} ({len(ps)} dates)")

    html = (ROOT / "Code" / "burn" / "label_tool_template.html").read_text(encoding="utf-8")
    radios = "\n".join(f'      <label><input type="radio" name="label" value="{v}">{k} · {t}</label>'
                       for k, (v, t) in enumerate(LABELS, 1))
    keys = "".join(str(k) for k in range(1, len(LABELS) + 1))
    swaps = [
        ("Burn Labelling 2022", f"PD visual check {YEAR}"),
        ("Burn labelling: Punjab, Oct–Dec 2022", f"PD visual check: Punjab, Sep–Dec {YEAR}"),
        ("burn_labels_2022_v1", f"pd_v7_labels_{YEAR}_v1"),
        ("burn_labels_2022.csv", "v7_labels.csv"),
        ("<code>outputs/burn_labelling/</code>", "<code>outputs/pd/validation/v7/</code>"),
        ("1 burnt · 2 ploughed/sown · 3 other · 4 can't tell", " · ".join(f"{k} {t.lower()}" for k, (_, t) in enumerate(LABELS, 1))),
        ("(not 2022)", f"(not {YEAR})"),
        ("Use <b>Not burnt, other</b> for no change, standing crop all season, orchard or non-paddy.",
         "Use <b>Standing or harvested after 30 Nov</b> if the paddy is still green or golden in the last dates, "
         "<b>Not rice</b> for an orchard, cotton, fodder or any field that never looks like paddy."),
        ('"1234".includes(e.key)', f'"{keys}".includes(e.key)'),
        ('["burnt", "not_burnt_ploughed_sown", "not_burnt_other", "cant_tell"]', json.dumps([v for v, _ in LABELS])),
    ]
    for a, b in swaps:
        assert a in html, a
        html = html.replace(a, b)
    start = html.index('      <label><input type="radio" name="label" value="burnt">')
    end = html.index("    </div>", start)
    html = html[:start] + radios + "\n" + html[end:]
    html = html.replace("__POINTS_JSON__", json.dumps(tool))
    (OUT / "label_tool.html").write_text(html, encoding="utf-8")
    print(f"\nDone: {len(tool)} points -> {OUT / 'label_tool.html'}")


def score():
    meta = pd.read_csv(OUT / "points_meta.csv")
    lab = pd.read_csv(OUT / "v7_labels.csv")[["pid", "label", "confidence"]]
    d = meta.merge(lab, on="pid")
    d = d[d.label.notna() & (d.label != "")]
    known = d[d.label.isin(["burnt", "ploughed_sown"])]
    rows = []
    for name, x in d.groupby("lgd_tehsil_name"):
        k = known[known.lgd_tehsil_name == name]
        rows.append({
            "lgd_tehsil_name": name, "kind": TEHSILS[name], "labelled": len(x),
            "cant_tell": (x.label == "cant_tell").mean(), "not_rice_share": (x.label == "not_rice").mean(),
            "standing_late_share": (x.label == "standing_late").mean(),
            "eye_burnt_share": (k.label == "burnt").mean(), "model_burnt_share": k.burnt.mean(),
            "agreement": (k.burnt == (k.label == "burnt")).mean(),
            "missed_burns": ((k.label == "burnt") & (k.burnt == 0)).sum() / max(1, (k.label == "burnt").sum()),
            "false_alarms": ((k.label != "burnt") & (k.burnt == 1)).sum() / max(1, (k.label != "burnt").sum()),
        })
    t = pd.DataFrame(rows)
    nd_miss = t[t.kind == "ND"].missed_burns.mean()
    # [P] flag a PD if the model misses clearly more burns there than at the NDs, or a fifth of points are not rice
    t["v7"] = np.where(t.kind == "ND", "control",
                       np.where((t.missed_burns > nd_miss + 0.15) | (t.not_rice_share >= 0.2), "flag", "pass"))
    t.round(3).to_csv(OUT.parent / "v7_visual.csv", index=False)
    print(t.round(3).to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", action="store_true")
    args = ap.parse_args()
    if args.score:
        score()
        return
    init_ee()
    IMG.mkdir(parents=True, exist_ok=True)
    meta_path, series_path = OUT / "points_meta.csv", OUT / "point_series.csv"
    if meta_path.exists() and series_path.exists():
        print("Reusing cached point selection")
        meta, series = pd.read_csv(meta_path), pd.read_csv(series_path, dtype={"date": str})
    else:
        meta = choose_points()
        series = clear_looks(meta)
        meta.to_csv(meta_path, index=False)
        series.to_csv(series_path, index=False)
    build_tool(meta, series)


if __name__ == "__main__":
    random.seed(SEED)
    main()
