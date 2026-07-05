# Grid / power infrastructure

## gcc-states-latest.osm.pbf (240 MB)
- **Source:** Geofabrik, https://download.geofabrik.de/asia/gcc-states.html
- **Retrieved:** 2026-07-03 (rolling "latest" snapshot — record: retrieved Jul 2026)
- **License:** ODbL (OpenStreetMap contributors) — attribution required in the paper
- **Coverage:** all GCC states incl. Saudi Arabia; full OSM data, needs filtering to
  `power=line|substation|plant|generator` for the grid-distance feature
- **Processing (not yet done):** `brew install osmium-tool` then e.g.
  `osmium tags-filter gcc-states-latest.osm.pbf nwr/power=line,minor_line,substation,plant -o saudi_power.osm.pbf`
  then load with pyrosm/GeoPandas. Alternative: `pip install pyrosm` reads the PBF directly.
- **Caveat:** OSM completeness for Saudi transmission lines is imperfect (rural gaps).
  Cross-check the resulting grid-distance feature against SEC annual-report maps for the
  named sites; treat OSM distance as a lower-fidelity feature with stated uncertainty.

## kapsarc_saudi_electricity_load_monthly_by_region.csv (1,584 rows)
- **Source:** KAPSARC Data Portal,
  https://datasource.kapsarc.org/explore/dataset/saudi-arabia-electricity-load-monthly-by-region/
  (pulled via `.../exports/csv`)
- **Retrieved:** 2026-07-04
- **License:** KAPSARC open data (attribution)
- **Content:** monthly electricity load (max/avg/min GW) by region (Central/Eastern/Western/Southern),
  2009→. Use as a **regional demand proxy** for the industrial/electrification use-case matching and
  power-class sizing.

## SEC / official grid data — collect as needed
- Saudi Electricity Company annual reports (system maps, transmission capacity):
  https://www.se.com.sa/en/Investors/Reports-and-Presentations/Annual-Reports/
- Use for cross-checking the OSM-derived grid-distance feature at the named sites.
