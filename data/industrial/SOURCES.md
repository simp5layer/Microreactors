# Industrial cities — MODON (Stream B / WP B1-B2)

## Status: interactive web-GIS; geocode the city list manually

- **MODON web-GIS viewer:** https://webgis.modon.gov.sa/modonmaps24
- **MODON GIS services page:** https://modon.gov.sa/en/Eservices/Pages/GIS.aspx
- **Barrier:** MODON publishes an interactive map of its ~36 industrial cities but no open bulk
  shapefile/CSV export. The ArcGIS viewer may expose a REST `MapServer`/`FeatureServer` endpoint —
  worth inspecting network calls at `webgis.modon.gov.sa` for a queryable service before manual work.

### Practical approach
MODON's industrial cities are named and their locations public. The big ones relevant here
(Jubail, Yanbu, Ras Al Khair are Royal-Commission not MODON, but MODON cities like Riyadh 1/2/3,
Dammam, Sudair, Al-Kharj, Qassim, etc.) are geocodable by name. Build an `industrial_cities.csv`
(name, region, lat, lon, approx area/occupancy if published) analogous to the site register.

### Note
For the four use-case categories in Proposal 2, "industrial" sites overlap RCJY cities
(Jubail/Yanbu/Ras Al Khair) — those are already in `../sites/site_register_v0.csv`. MODON coverage
mainly matters if the site pool is expanded toward the 30–80 target with mid-size industrial zones.
