"""Generate a synthetic global member-origin flow dataset for the map viz.

Real city coordinates (public geographic facts) carry SYNTHETIC member counts
and flows toward three fictional FitFlow hub cities. Output: data/geo/flows.json
with cities (lat/lng/members) and flows (origin -> hub, value).

Run: python -m data_gen.geo_flows
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "geo"

# fictional FitFlow hubs placed at plausible global coordinates (synthetic)
HUBS = [
    {"id": "ARD", "name": "Arden",       "lat": 40.71, "lng": -74.01, "region": "Americas"},
    {"id": "BRW", "name": "Brightwater", "lat": 51.51, "lng": -0.13,  "region": "Europe"},
    {"id": "CRL", "name": "Crestline",   "lat": 1.35,  "lng": 103.82, "region": "Asia-Pacific"},
]

# (name, lat, lng, nearest hub) — real coords, synthetic membership
ORIGINS = [
    ("Toronto", 43.65, -79.38, "ARD"), ("Chicago", 41.88, -87.63, "ARD"),
    ("Los Angeles", 34.05, -118.24, "ARD"), ("Mexico City", 19.43, -99.13, "ARD"),
    ("Sao Paulo", -23.55, -46.63, "ARD"), ("Bogota", 4.71, -74.07, "ARD"),
    ("Buenos Aires", -34.60, -58.38, "ARD"), ("Lima", -12.05, -77.04, "ARD"),
    ("Miami", 25.76, -80.19, "ARD"), ("Vancouver", 49.28, -123.12, "ARD"),
    ("Boston", 42.36, -71.06, "ARD"), ("Houston", 29.76, -95.37, "ARD"),
    ("Santiago", -33.45, -70.67, "ARD"), ("Montreal", 45.50, -73.57, "ARD"),
    ("Paris", 48.86, 2.35, "BRW"), ("Berlin", 52.52, 13.40, "BRW"),
    ("Madrid", 40.42, -3.70, "BRW"), ("Rome", 41.90, 12.50, "BRW"),
    ("Amsterdam", 52.37, 4.90, "BRW"), ("Dublin", 53.35, -6.26, "BRW"),
    ("Stockholm", 59.33, 18.07, "BRW"), ("Lisbon", 38.72, -9.14, "BRW"),
    ("Warsaw", 52.23, 21.01, "BRW"), ("Vienna", 48.21, 16.37, "BRW"),
    ("Istanbul", 41.01, 28.98, "BRW"), ("Dubai", 25.20, 55.27, "BRW"),
    ("Cairo", 30.04, 31.24, "BRW"), ("Lagos", 6.52, 3.38, "BRW"),
    ("Johannesburg", -26.20, 28.05, "BRW"), ("Nairobi", -1.29, 36.82, "BRW"),
    ("Tel Aviv", 32.08, 34.78, "BRW"), ("Manchester", 53.48, -2.24, "BRW"),
    ("Tokyo", 35.68, 139.69, "CRL"), ("Seoul", 37.57, 126.98, "CRL"),
    ("Shanghai", 31.23, 121.47, "CRL"), ("Hong Kong", 22.32, 114.17, "CRL"),
    ("Sydney", -33.87, 151.21, "CRL"), ("Melbourne", -37.81, 144.96, "CRL"),
    ("Mumbai", 19.08, 72.88, "CRL"), ("Delhi", 28.61, 77.21, "CRL"),
    ("Bangkok", 13.76, 100.50, "CRL"), ("Jakarta", -6.21, 106.85, "CRL"),
    ("Manila", 14.60, 120.98, "CRL"), ("Kuala Lumpur", 3.14, 101.69, "CRL"),
    ("Auckland", -36.85, 174.76, "CRL"), ("Taipei", 25.03, 121.57, "CRL"),
    ("Ho Chi Minh City", 10.82, 106.63, "CRL"), ("Bengaluru", 12.97, 77.59, "CRL"),
]


def gen(seed: int = 11) -> dict:
    rng = random.Random(seed)
    hub_by_id = {h["id"]: h for h in HUBS}
    cities, flows = [], []
    hub_totals = {h["id"]: 0 for h in HUBS}

    for name, lat, lng, hub in ORIGINS:
        members = rng.randint(80, 2400)
        # a richer city skews toward "diverse" origin mix
        diversity = round(rng.uniform(0.25, 0.95), 2)
        cities.append({"name": name, "lat": lat, "lng": lng, "members": members,
                       "diversity": diversity, "hub": hub, "kind": "origin"})
        flows.append({"from": [lng, lat], "to": [hub_by_id[hub]["lng"], hub_by_id[hub]["lat"]],
                      "from_name": name, "to_name": hub_by_id[hub]["name"],
                      "value": members, "hub": hub})
        hub_totals[hub] += members

    for h in HUBS:
        cities.append({"name": h["name"], "lat": h["lat"], "lng": h["lng"],
                       "members": hub_totals[h["id"]], "diversity": None,
                       "hub": h["id"], "kind": "hub"})

    return {"hubs": HUBS, "cities": cities, "flows": flows,
            "hub_totals": hub_totals,
            "totals": {"origins": len(ORIGINS), "members": sum(hub_totals.values())}}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = gen()
    (OUT / "flows.json").write_text(json.dumps(data), encoding="utf-8")
    print(f"wrote {OUT/'flows.json'}: {len(data['cities'])} cities, "
          f"{len(data['flows'])} flows, {data['totals']['members']:,} members")


if __name__ == "__main__":
    main()
