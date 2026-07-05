#!/usr/bin/env python3
"""Pull NASA POWER daily temperature series + monthly climatology for every site
in data/sites/site_register_v0.csv.

Outputs, per site, into data/climate/nasa_power/:
  <site_id>_<slug>_daily_2015-2024.csv   (T2M, T2M_MAX, T2M_MIN, RH2M, WS2M)
  <site_id>_<slug>_climatology.json      (30-year monthly climatology)

NASA POWER is free, no key, no registration. Grid cell ~0.5 deg x 0.625 deg,
so coordinate uncertainty of a few tens of km does not matter for climate.
API docs: https://power.larc.nasa.gov/docs/services/api/
"""

import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITES_CSV = ROOT / "data" / "sites" / "site_register_v0.csv"
OUT_DIR = ROOT / "data" / "climate" / "nasa_power"

DAILY_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
    "?parameters=T2M,T2M_MAX,T2M_MIN,RH2M,WS2M&community=RE"
    "&longitude={lon}&latitude={lat}&start=20150101&end=20241231&format=CSV"
)
CLIM_URL = (
    "https://power.larc.nasa.gov/api/temporal/climatology/point"
    "?parameters=T2M,T2M_MAX,T2M_MIN,RH2M,WS2M&community=RE"
    "&longitude={lon}&latitude={lat}&format=JSON"
)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def fetch(url: str, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            print(f"  retry {attempt + 1} after error: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SITES_CSV, newline="") as f:
        sites = list(csv.DictReader(f))

    for i, s in enumerate(sites, 1):
        slug = slugify(s["name"])
        daily_path = OUT_DIR / f"{s['site_id']}_{slug}_daily_2015-2024.csv"
        clim_path = OUT_DIR / f"{s['site_id']}_{slug}_climatology.json"
        print(f"[{i}/{len(sites)}] {s['name']} ({s['lat']}, {s['lon']})")

        if not daily_path.exists():
            daily_path.write_bytes(fetch(DAILY_URL.format(lat=s["lat"], lon=s["lon"])))
            time.sleep(1)
        if not clim_path.exists():
            raw = fetch(CLIM_URL.format(lat=s["lat"], lon=s["lon"]))
            clim_path.write_text(json.dumps(json.loads(raw), indent=1))
            time.sleep(1)

    print(f"done -> {OUT_DIR}")


if __name__ == "__main__":
    main()
