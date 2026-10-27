"""Order clipped PlanetScope surface reflectance for one CEEW site and day (Orders API).

AOI = CEEW fields + BUFFER m. Scenes for the day are picked greedily (clearest first)
until the AOI is covered; each is clipped to the AOI, so the charge should be the
clipped area per scene (checked against the dashboard meter on the first order).

  python -I Code/planet/planet_order.py jalandhar_2021 2021-10-29          # dry run
  python -I Code/planet/planet_order.py jalandhar_2021 2021-10-29 --place  # order + download

Reads outputs/planet/catalogue_scenes.csv (from planet_search.py).
Downloads to outputs/planet/orders/<site>_<day>/.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform, unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
from planet_search import OUT, SITES, api_key

BUFFER = 300  # m around the CEEW fields
MIN_CLEAR = 80
ORDERS_URL = "https://api.planet.com/compute/ops/orders/v2"
ITEM_URL = "https://api.planet.com/data/v1/item-types/PSScene/items/{}"
to_m = Transformer.from_crs(4326, 32643, always_xy=True).transform
to_deg = Transformer.from_crs(32643, 4326, always_xy=True).transform


def site_aoi(site):
    path, _ = SITES[site]
    fields = [transform(to_m, shape(f["geometry"])) for f in json.loads(path.read_text())["features"]]
    return unary_union(fields).buffer(BUFFER).simplify(10)  # metres, UTM 43N


def pick_scenes(s, site, day, aoi):
    sc = pd.read_csv(OUT / "catalogue_scenes.csv")
    sc = sc[(sc.site == site) & (sc.day == day) & (sc.clear_percent >= MIN_CLEAR)
            & sc.can_download_sr].sort_values("clear_percent", ascending=False)
    chosen, left = [], aoi
    for sid in sc.id:
        fp = transform(to_m, shape(s.get(ITEM_URL.format(sid)).json()["geometry"]))
        part = fp.intersection(aoi)
        if part.intersection(left).area < 0.02 * aoi.area:  # adds < 2% new cover
            continue
        chosen.append((sid, part.area / 1e6))
        left = left.difference(fp)
        if left.area < 0.01 * aoi.area:
            break
    return chosen, 1 - left.area / aoi.area


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", choices=list(SITES))
    ap.add_argument("day")
    ap.add_argument("--place", action="store_true")
    a = ap.parse_args()
    s = requests.Session()
    s.auth = (api_key(), "")
    retry = Retry(total=8, backoff_factor=5, status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=None)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    name = f"{a.site}_{a.day}"
    old = [o for o in s.get(ORDERS_URL).json()["orders"]
           if o["name"] == name and o["state"] in ("queued", "running", "success", "partial")]
    if old and a.place:  # already ordered: download again, no new quota
        print("reusing existing order", old[0]["id"])
        download(s, old[0]["_links"]["_self"], name)
        return
    aoi = site_aoi(a.site)
    chosen, cover = pick_scenes(s, a.site, a.day, aoi)
    print(f"AOI {aoi.area / 1e6:.1f} km2; {len(chosen)} scenes cover {cover:.1%}")
    for sid, km2 in chosen:
        print(f"  {sid}  clipped {km2:.1f} km2")
    print(f"estimated charge {sum(k for _, k in chosen):.1f} km2")
    if not chosen:
        print("no clear scene for this day; nothing ordered")
        return
    if not a.place:
        return
    body = {
        "name": name,
        "products": [{"item_ids": [c[0] for c in chosen], "item_type": "PSScene",
                      "product_bundle": "analytic_sr_udm2"}],
        "tools": [{"clip": {"aoi": mapping(transform(to_deg, aoi))}}],
    }
    r = s.post(ORDERS_URL, json=body)
    if not r.ok:
        raise SystemExit(f"order failed {r.status_code}: {r.text}")
    url = r.json()["_links"]["_self"]
    print("order placed:", url)
    download(s, url, name)


def download(s, url, name):
    """Wait for the order, then fetch every result file (written via .part, so a
    broken transfer never leaves a half file under the real name)."""
    while True:
        o = s.get(url).json()
        if o["state"] in ("success", "partial", "failed", "cancelled"):
            break
        time.sleep(30)
    print("state:", o["state"])
    dest = OUT / "orders" / name
    dest.mkdir(parents=True, exist_ok=True)
    for res in o["_links"].get("results", []):
        f = dest / Path(res["name"]).name
        tmp = f.with_name(f.name + ".part")
        with s.get(res["location"], stream=True, timeout=120) as d:
            d.raise_for_status()
            with open(tmp, "wb") as fh:
                for chunk in d.iter_content(1 << 20):
                    fh.write(chunk)
        tmp.replace(f)
        print("  saved", f.name)


if __name__ == "__main__":
    main()
