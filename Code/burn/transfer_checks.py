"""
Phase B pre-checks: does the BAIS2 + TCB burn model transfer beyond its 380 training fields?

Ground truth: CEEW "Patterns of Crop Residue Burning" (Zenodo 10.5281/zenodo.20179137),
fields labelled on 2020-11-10 (Sangrur area) and 2021-10-29 (Jalandhar/Kapurthala area).
Index formulas copied from Code/Decision_pilot_ground_data (2).ipynb (Filipponi BAIS2,
Shi & Xu 2019 Sentinel-2 TCB coefficients).

Checks
  0  mask audit   Which Sentinel-2 SCL classes do pixels of burnt vs unburnt fields fall in?
                  (the notebook kept only SCL 4 vegetation + 5 bare soil)
  1  transfer     Train on one date/area, test on the other (field medians), for each mask.
  2  pixel        Apply the field-trained model to 20 m pixels inside the fields.
  3  multi-look   Classify every clear image 1 Oct - 15 Dec; compare season rules
                  (any look / >=2 consecutive looks / became dark after a clear unburnt look).

Run:  python Code/burn/transfer_checks.py [--checks 0 1 2 3]
Out:  outputs/burn_checks/*.csv
Needs: Earth Engine authentication (ee.Authenticate()) and project ictd-507010.
"""

import argparse
import json
from pathlib import Path

import ee
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
GT_DIR = ROOT / "Code" / "Ground Truth Data"
OUT = ROOT / "outputs" / "burn_checks"
PROJECT = "ictd-507010"

LABEL_DATES = {
    2020: ("partially_completely_burnt_2020_11_10.geojson", "2020-11-10",
           "20201110T053041_20201110T053044_T43REP"),
    2021: ("partially_completely_burnt_2021_10_29.geojson", "2021-10-29",
           "20211029T053941_20211029T053942_T43REQ"),
}
BURNT = {"completely_burnt", "partially_burnt"}
MASKS = {
    "notebook_scl45": [4, 5],              # as in the validated notebook
    "relaxed_scl2457": [2, 4, 5, 7],       # + dark area pixels, unclassified
}
SCALE = 20


# ---------------------------------------------------------------- indices
def indices(image, keep_scl):
    bands = ["B2", "B3", "B4", "B6", "B7", "B8", "B8A", "B11", "B12"]
    sr = image.select(bands).divide(10000)
    scl = image.select("SCL")
    valid = scl.eq(keep_scl[0])
    for c in keep_scl[1:]:
        valid = valid.Or(scl.eq(c))
    sr = sr.updateMask(valid)
    p1 = sr.select("B6").multiply(sr.select("B7")).multiply(sr.select("B8A")).divide(sr.select("B4")).sqrt()
    p2 = sr.select("B12").subtract(sr.select("B8A")).divide(sr.select("B12").add(sr.select("B8A")).sqrt()).add(1)
    bais2 = ee.Image(1).subtract(p1).multiply(p2).rename("BAIS2")
    tcb = (sr.select("B2").multiply(0.3510).add(sr.select("B3").multiply(0.3813))
           .add(sr.select("B4").multiply(0.3437)).add(sr.select("B8").multiply(0.7196))
           .add(sr.select("B11").multiply(0.2396)).add(sr.select("B12").multiply(0.1949))
           .rename("TCB"))
    return bais2.addBands(tcb)


def fields(year):
    path = GT_DIR / LABEL_DATES[year][0]
    gj = json.loads(path.read_text())
    feats = []
    for f in gj["features"]:
        p = f["properties"]
        feats.append(ee.Feature(ee.Geometry(f["geometry"]), {
            "field_id": p["field_id"], "field_category": p["field_category"],
            "burnt": int(p["field_category"] in BURNT), "year": year}))
    return ee.FeatureCollection(feats)


def to_df(fc):
    return pd.DataFrame([f["properties"] for f in fc.getInfo()["features"]])


def label_image(year):
    return ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + LABEL_DATES[year][2])


# ---------------------------------------------------------------- model helpers
def fit(df):
    X = df[["BAIS2", "TCB"]].to_numpy()
    sc = StandardScaler().fit(X)
    m = LogisticRegression(random_state=42).fit(sc.transform(X), df["burnt"])
    return sc, m


def scores(y, pred):
    return {"n": len(y), "accuracy": round(accuracy_score(y, pred), 4),
            "precision": round(precision_score(y, pred, zero_division=0), 4),
            "recall": round(recall_score(y, pred, zero_division=0), 4),
            "f1": round(f1_score(y, pred, zero_division=0), 4),
            "false_alarm_rate": round(((pred == 1) & (y == 0)).sum() / max((y == 0).sum(), 1), 4)}


def ee_classifier(sc, m):
    """Return f(image_with_BAIS2_TCB) -> 1-band 'burnt' image using the sklearn model."""
    mu, sd = sc.mean_, sc.scale_
    w, b = m.coef_[0], m.intercept_[0]

    def apply(img):
        z = (img.select("BAIS2").subtract(mu[0]).divide(sd[0]).multiply(w[0])
             .add(img.select("TCB").subtract(mu[1]).divide(sd[1]).multiply(w[1])).add(b))
        return z.gt(0).rename("burnt_px")
    return apply


# ---------------------------------------------------------------- checks
def check0_mask_audit():
    rows = []
    for year in LABEL_DATES:
        scl = label_image(year).select("SCL")
        hist = scl.reduceRegions(collection=fields(year),
                                 reducer=ee.Reducer.frequencyHistogram(), scale=SCALE, tileScale=4)
        for p in to_df(hist).to_dict("records"):
            h = p.get("histogram") or {}
            for cls, cnt in h.items():
                rows.append({"year": year, "field_id": p["field_id"],
                             "field_category": p["field_category"], "scl": int(float(cls)), "pixels": cnt})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "check0_scl_pixels.csv", index=False)
    tab = df.assign(group=np.where(df.field_category.isin(BURNT), "burnt", "unburnt")) \
            .pivot_table(index="scl", columns="group", values="pixels", aggfunc="sum").fillna(0)
    tab = (tab / tab.sum() * 100).round(1)
    print("\n[check 0] % of field pixels by Sentinel-2 SCL class (4 veg, 5 bare, 2 dark area, 3 shadow, 6 water, 7 unclassified, 8-10 cloud)")
    print(tab.to_string())
    tab.to_csv(OUT / "check0_scl_share.csv")


def field_medians(mask):
    parts = []
    for year in LABEL_DATES:
        img = indices(label_image(year), MASKS[mask])
        parts.append(to_df(img.reduceRegions(collection=fields(year),
                                             reducer=ee.Reducer.median(), scale=SCALE, tileScale=4)))
    return pd.concat(parts, ignore_index=True)


def check1_transfer():
    rows, models = [], {}
    for mask in MASKS:
        df = field_medians(mask)
        df.to_csv(OUT / f"check1_field_medians_{mask}.csv", index=False)
        ok = df.dropna(subset=["BAIS2", "TCB"])
        missing = df[df[["BAIS2", "TCB"]].isna().any(axis=1)]
        print(f"\n[check 1] mask {mask}: fields with values {len(ok)}/{len(df)}; "
              f"missing by class {missing.field_category.value_counts().to_dict()}")
        for train_y, test_y in [(2021, 2020), (2020, 2021)]:
            sc, m = fit(ok[ok.year == train_y])
            te = ok[ok.year == test_y]
            pred = m.predict(sc.transform(te[["BAIS2", "TCB"]].to_numpy()))
            rows.append({"mask": mask, "train": train_y, "test": test_y, **scores(te.burnt.to_numpy(), pred)})
        # within-year (in-sample) for reference, and pooled model for checks 2-3
        for yr in LABEL_DATES:
            sc, m = fit(ok[ok.year == yr])
            te = ok[ok.year == yr]
            pred = m.predict(sc.transform(te[["BAIS2", "TCB"]].to_numpy()))
            rows.append({"mask": mask, "train": yr, "test": f"{yr} (same, in-sample)",
                         **scores(te.burnt.to_numpy(), pred)})
        models[mask] = fit(ok)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "check1_transfer.csv", index=False)
    print(res.to_string(index=False))
    return models


def check2_pixel(models):
    rows = []
    for mask, (sc, m) in models.items():
        clf = ee_classifier(sc, m)
        for year in LABEL_DATES:
            img = indices(label_image(year), MASKS[mask])
            flag = clf(img)
            red = flag.reduceRegions(collection=fields(year),
                                     reducer=ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True),
                                     scale=SCALE, tileScale=4)
            df = to_df(red).rename(columns={"mean": "burnt_pixel_share", "count": "pixels"})
            df["mask"] = mask
            rows.append(df)
    df = pd.concat(rows, ignore_index=True)
    df.to_csv(OUT / "check2_pixel_by_field.csv", index=False)
    out = []
    for mask, g in df.dropna(subset=["burnt_pixel_share"]).groupby("mask"):
        correct = np.where(g.burnt == 1, g.burnt_pixel_share, 1 - g.burnt_pixel_share) * g.pixels
        out.append({"mask": mask, "fields": len(g), "pixels": int(g.pixels.sum()),
                    "pixel_accuracy": round(correct.sum() / g.pixels.sum(), 4),
                    "burnt_fields_mean_burnt_px": round(g[g.burnt == 1].burnt_pixel_share.mean(), 3),
                    "unburnt_fields_mean_burnt_px": round(g[g.burnt == 0].burnt_pixel_share.mean(), 3),
                    "field_rule_majority_acc": round(((g.burnt_pixel_share >= 0.5).astype(int) == g.burnt).mean(), 4)})
    res = pd.DataFrame(out)
    res.to_csv(OUT / "check2_pixel_summary.csv", index=False)
    print("\n[check 2] pixel-level")
    print(res.to_string(index=False))


def check3_multilook(models, mask="relaxed_scl2457"):
    sc, m = models[mask]
    clf = ee_classifier(sc, m)
    recs = []
    for year in LABEL_DATES:
        fc = fields(year)
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
               .filterBounds(fc.geometry())
               .filterDate(f"{year}-10-01", f"{year}-12-16")
               .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)))
        ids = col.aggregate_array("system:index").getInfo()
        print(f"\n[check 3] {year}: {len(ids)} images")
        for iid in ids:
            img = ee.Image("COPERNICUS/S2_SR_HARMONIZED/" + iid)
            flag = clf(indices(img, MASKS[mask]))
            red = flag.reduceRegions(collection=fc,
                                     reducer=ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True),
                                     scale=SCALE, tileScale=4)
            df = to_df(red)
            df["image"] = iid
            df["date"] = pd.to_datetime(iid[:8])
            recs.append(df)
    ts = pd.concat(recs, ignore_index=True).rename(columns={"mean": "burnt_pixel_share", "count": "pixels"})
    ts.to_csv(OUT / "check3_timeseries.csv", index=False)
    evaluate_multilook(ts)


def evaluate_multilook(ts, min_pixels=3):
    ts = ts[ts.pixels >= min_pixels].copy()
    # one value per field-date (two tiles can image the same date)
    ts = ts.groupby(["year", "field_id", "field_category", "burnt", "date"], as_index=False).burnt_pixel_share.mean()
    ts["look_burnt"] = ts.burnt_pixel_share >= 0.5
    rows = []
    for (year, fid), g in ts.sort_values("date").groupby(["year", "field_id"]):
        label_date = pd.Timestamp(LABEL_DATES[year][1])
        seq = g.look_burnt.to_numpy()
        before = g[g.date < label_date - pd.Timedelta(days=2)]
        rows.append({
            "year": year, "field_id": fid, "field_category": g.field_category.iloc[0],
            "burnt": g.burnt.iloc[0], "looks": len(g),
            "any_look": bool(seq.any()),
            "two_consecutive": bool(np.any(seq[:-1] & seq[1:])) if len(seq) > 1 else False,
            "became_dark": bool(np.any(~seq[:-1] & seq[1:])) if len(seq) > 1 else False,
            "flag_before_label": bool(before.look_burnt.any()) if len(before) else False,
        })
    f = pd.DataFrame(rows)
    f.to_csv(OUT / "check3_field_rules.csv", index=False)
    out = []
    for rule in ["any_look", "two_consecutive", "became_dark"]:
        b, u = f[f.burnt == 1], f[f.burnt == 0]
        out.append({"rule": rule,
                    "burnt_fields_detected": round(b[rule].mean(), 3),
                    "unburnt_fields_flagged_in_season": round(u[rule].mean(), 3)})
    res = pd.DataFrame(out)
    u = f[f.burnt == 0]
    print("\n[check 3] season rules (unburnt fields may genuinely burn later in the season)")
    print(res.to_string(index=False))
    print(f"Unburnt-labelled fields flagged burnt BEFORE their label date (likely false alarms): "
          f"{u.flag_before_label.mean():.3f} (n={len(u)})")
    print("Looks per field:", f.looks.describe().round(1).to_dict())
    res.to_csv(OUT / "check3_rule_summary.csv", index=False)


def init_ee():
    """Initialize Earth Engine; fall back to the Earth Engine scope only if the saved
    login was granted just that scope (other consent checkboxes left unticked)."""
    try:
        ee.Initialize(project=PROJECT)
    except ee.EEException:
        from ee import oauth
        from google.oauth2 import credentials as cl
        args = oauth.get_credentials_arguments()
        args["scopes"] = ["https://www.googleapis.com/auth/earthengine"]
        ee.Initialize(credentials=cl.Credentials(None, **args), project=PROJECT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checks", nargs="+", type=int, default=[0, 1, 2, 3])
    args = ap.parse_args()
    init_ee()
    OUT.mkdir(parents=True, exist_ok=True)
    if 0 in args.checks:
        check0_mask_audit()
    models = check1_transfer() if {1, 2, 3} & set(args.checks) else None
    if 2 in args.checks:
        check2_pixel(models)
    if 3 in args.checks:
        check3_multilook(models)


if __name__ == "__main__":
    main()
