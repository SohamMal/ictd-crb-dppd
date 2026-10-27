"""Free Planet catalogue search (Data API quick-search) over the CEEW ground-truth sites.

Uses no download quota. For each site: every PlanetScope scene (PSScene) within
+/- WINDOW days of the CEEW image date that touches the fields' convex hull,
with cloud cover, share of the hull covered, number of CEEW fields fully inside,
and whether our account may download the surface-reflectance asset.

Key: PL_API_KEY from the environment, else from the Windows user registry (setx).
Outputs: outputs/planet/catalogue_scenes.csv (one row per scene),
         outputs/planet/catalogue_days.csv (best clear coverage per site-day).
"""
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
GT = ROOT / "Code" / "Ground Truth Data"
OUT = ROOT / "outputs" / "planet"
WINDOW = 20  # days either side of the CEEW image date
SITES = {
    "sangrur_2020": (GT / "partially_completely_burnt_2020_11_10.geojson", date(2020, 11, 10)),
    "jalandhar_2021": (GT / "partially_completely_burnt_2021_10_29.geojson", date(2021, 10, 29)),
}
SEARCH_URL = "https://api.planet.com/data/v1/quick-search"


def api_key():
    k = os.environ.get("PL_API_KEY")
    if not k and sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            k = winreg.QueryValueEx(h, "PL_API_KEY")[0]
    if not k:
        sys.exit("PL_API_KEY not set")
    return k


def search(session, aoi, d0, d1):
    body = {
        "item_types": ["PSScene"],
        "filter": {"type": "AndFilter", "config": [
            {"type": "GeometryFilter", "field_name": "geometry", "config": mapping(aoi)},
            {"type": "DateRangeFilter", "field_name": "acquired",
             "config": {"gte": f"{d0}T00:00:00Z", "lte": f"{d1}T23:59:59Z"}},
        ]},
    }
    r = session.post(SEARCH_URL, json=body, params={"_page_size": 250})
    r.raise_for_status()
    page = r.json()
    while True:
        yield from page["features"]
        nxt = page["_links"].get("_next")
        if not nxt:
            break
        page = session.get(nxt).json()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    s.auth = (api_key(), "")
    rows = []
    for site, (path, d) in SITES.items():
        fields = [shape(f["geometry"]) for f in json.loads(path.read_text())["features"]]
        hull = unary_union(fields).convex_hull
        for it in search(s, hull, d - timedelta(WINDOW), d + timedelta(WINDOW)):
            p = it["properties"]
            fp = shape(it["geometry"])
            rows.append({
                "site": site, "id": it["id"],
                "acquired": p["acquired"], "day": p["acquired"][:10],
                "days_from_label": (date.fromisoformat(p["acquired"][:10]) - d).days,
                "instrument": p.get("instrument"), "satellite_id": p.get("satellite_id"),
                "cloud_cover": p.get("cloud_cover"), "clear_percent": p.get("clear_percent"),
                "quality": p.get("quality_category"), "gsd": p.get("gsd"),
                "hull_cover": round(fp.intersection(hull).area / hull.area, 3),
                "fields_inside": sum(fp.contains(f) for f in fields), "n_fields": len(fields),
                "can_download_sr": "assets.ortho_analytic_4b_sr:download" in it.get("_permissions", []),
                "can_download_8b_sr": "assets.ortho_analytic_8b_sr:download" in it.get("_permissions", []),
            })
    sc = pd.DataFrame(rows).sort_values(["site", "acquired"])
    sc.to_csv(OUT / "catalogue_scenes.csv", index=False)
    # per site-day: fields covered by at least one scene with clear_percent >= 80
    clear = sc[sc.clear_percent >= 80]
    days = (sc.groupby(["site", "day", "days_from_label"])
              .agg(n_scenes=("id", "size"), max_clear=("clear_percent", "max"),
                   hull_cover_sum=("hull_cover", "sum"))
              .reset_index())
    cf = clear.groupby(["site", "day"]).fields_inside.sum().rename("fields_in_clear_scenes")
    days = days.merge(cf, on=["site", "day"], how="left").fillna({"fields_in_clear_scenes": 0})
    days.to_csv(OUT / "catalogue_days.csv", index=False)
    print(sc.groupby("site").agg(scenes=("id", "size"), days=("day", "nunique"),
                                 can_dl_sr=("can_download_sr", "mean")))
    pd.set_option("display.width", 200)
    print(days.to_string(index=False))


if __name__ == "__main__":
    main()
