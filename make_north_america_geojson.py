#!/usr/bin/env python3
"""Build site/src/data/north-america.geojson for the story-page animated map.

Combines three sources into one FeatureCollection:
  - Canadian provinces (site/src/data/canada-provinces.geojson) — animated from
    the model, kind="ca", keyed by province code.
  - US states (Natural-Earth-derived) — static context, kind="us", carrying an
    approximate present-day French-at-home share (`frstatic`).
  - Mexico + Central America + Cuba — neutral context, kind="other".

Alaska/Hawaii/Puerto Rico are dropped so no polygon crosses the antimeridian.
Every polygon is checked for winding: d3-geo treats a ring that encloses more
than half the sphere as the whole-sphere complement (it floods the map). We
detect those with a signed spherical-area test and reverse them. The US states
source has exactly one such ring (Virginia); Canada and Natural Earth are clean.
"""
import json
import math
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "site", "src", "data")
US_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_1_states_provinces.geojson"
WORLD_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"

# Approximate % of residents speaking French at home (static context only).
US_FR = {
    "Maine": 3.7, "New Hampshire": 2.1, "Vermont": 1.6, "Louisiana": 1.8,
    "Rhode Island": 1.3, "Massachusetts": 0.9, "Connecticut": 0.8, "New York": 0.6,
    "Florida": 0.7, "New Jersey": 0.5, "California": 0.4,
}
DEFAULT_US = 0.3
CONTEXT = {"Mexico", "Guatemala", "Belize", "Honduras", "Cuba", "El Salvador", "Nicaragua"}
DROP_US = {"Alaska", "Hawaii", "Puerto Rico"}


def rnd(coords, nd=2):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], nd), round(coords[1], nd)]
    return [rnd(c, nd) for c in coords]


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def ring_spherical_area(ring):
    """Signed area (steradians) of a lon/lat ring on the unit sphere. Magnitude
    > 2*pi means the ring is wound so its 'interior' is the sphere complement."""
    a = 0.0
    for i in range(len(ring) - 1):
        lon1, lat1 = math.radians(ring[i][0]), math.radians(ring[i][1])
        lon2, lat2 = math.radians(ring[i + 1][0]), math.radians(ring[i + 1][1])
        a += (lon2 - lon1) * (2 + math.sin(lat1) + math.sin(lat2))
    return a / 2.0


def rewind_polygon(rings, code, fixed):
    if abs(ring_spherical_area(rings[0])) > 2 * math.pi:
        fixed.append(code)
        return [r[::-1] for r in rings]
    return rings


def rewind(geom, code, fixed):
    if geom["type"] == "Polygon":
        geom["coordinates"] = rewind_polygon(geom["coordinates"], code, fixed)
    elif geom["type"] == "MultiPolygon":
        geom["coordinates"] = [rewind_polygon(p, code, fixed) for p in geom["coordinates"]]


def main():
    feats = []

    ca = json.load(open(os.path.join(DATA, "canada-provinces.geojson")))
    for f in ca["features"]:
        feats.append({"type": "Feature", "geometry": f["geometry"],
                      "properties": {"code": f["properties"]["code"],
                                     "name": f["properties"]["name"], "kind": "ca"}})

    us = fetch_json(US_URL)
    for f in us["features"]:
        p = f["properties"]
        if p.get("admin") != "United States of America":
            continue
        nm = p["name"]
        if nm in DROP_US:
            continue
        feats.append({"type": "Feature",
                      "geometry": {"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])},
                      "properties": {"code": "US-" + nm, "name": nm, "kind": "us",
                                     "frstatic": US_FR.get(nm, DEFAULT_US)}})

    world = fetch_json(WORLD_URL)
    for f in world["features"]:
        nm = f["properties"].get("ADMIN") or f["properties"].get("NAME")
        if nm in CONTEXT:
            feats.append({"type": "Feature",
                          "geometry": {"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])},
                          "properties": {"code": "X-" + nm, "name": nm, "kind": "other", "frstatic": 0.2}})

    fixed = []
    for f in feats:
        rewind(f["geometry"], f["properties"]["code"], fixed)

    out = {"type": "FeatureCollection", "features": feats}
    path = os.path.join(DATA, "north-america.geojson")
    json.dump(out, open(path, "w"), separators=(",", ":"))
    kinds = {}
    for f in feats:
        kinds[f["properties"]["kind"]] = kinds.get(f["properties"]["kind"], 0) + 1
    print("features:", len(feats), kinds, "size KB:", round(os.path.getsize(path) / 1024))
    print("rewound inverted polygons:", sorted(set(fixed)) or "(none)")


if __name__ == "__main__":
    main()
