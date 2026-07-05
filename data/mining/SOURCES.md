# Mining locations (Stream B / WP B1-B2)

## Status: no public bulk download — extract manually or geocode by name

- **Ta'adeen mining platform (official cadastre):** https://taadeen.sa/en  ·  interactive map:
  https://taadeen.sa/en/mining-map  ·  licensed-operator portal: https://taadeen.sa/MiningPortal/Login
  - **Barrier:** the public map is an interactive web-GIS; no open bulk export of license polygons.
    The full cadastre (license boundaries/holders) sits behind the operator/investor portal login.
- **Saudi Geological Survey national geodatabase:** https://ngd.sgs.gov.sa/ar (Arabic) — mineral
  occurrence layers; some viewable, export gated.
- **Ministry of Industry & Mineral Resources (MIM):** publishes mining-sector stats, not per-site GIS.

### Practical approach for this project
The named producing mines (Maaden operations: Mansourah-Massarah, Ad Duwayhi, Jabal Sayid,
Al Jalamid, Waad Al Shamal, Bulghah, Sukhaybarat, Mahd Ad Dhahab, etc.) are individually
**geocodable** — their coordinates are public (already in `../sites/site_register_v0.csv`, plus
Maaden disclosures and OSM `landuse=quarry` / `industrial=mine`). For the siting study we need site
**points**, not full cadastre polygons, so manual geocoding of the operating-mine list is sufficient
and defensible. Document each coordinate's source in the site register.

### If cadastre-level data becomes necessary
Request an export through KACST's institutional channel to MIM/Ta'adeen, or scrape the map viewer's
tile/API endpoint (check terms first).
