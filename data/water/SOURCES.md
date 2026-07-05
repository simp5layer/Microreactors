# Water stress — WRI Aqueduct 4.0

## aqueduct-4-0-water-risk-data.zip (249 MB)
- **Source:** World Resources Institute, https://files.wri.org/aqueduct/aqueduct-4-0-water-risk-data.zip
  (landing: https://www.wri.org/data/aqueduct-global-maps-40-data)
- **Retrieved:** 2026-07-04
- **License:** CC BY 4.0 — cite WRI Aqueduct 4.0 (2023)
- **Version snapshot:** `Aqueduct40_waterrisk_download_Y2023M07D05`
- **Contents:**
  - `CVS/Aqueduct40_baseline_annual_y2023m07d05.csv` (193 MB) — per hydrological basin (HydroBASINS level), all indicators
  - `CVS/Aqueduct40_baseline_monthly_...csv` — monthly baseline
  - `CVS/Aqueduct40_future_annual_...csv` — 2030/2050/2080 projections under SSP scenarios
  - `GDB/Aq40_Y2023D07M05.gdb` — Esri file geodatabase (polygon geometries; read with GeoPandas/`fiona`)
- **Key indicator for this project:** `bws` (baseline water stress) + its category `bws_cat`/label;
  Saudi basins mostly fall in "Extremely High" (>80%). Also `w_awr_def_tot_cat` (overall water risk).
- **How to attach to a site:** point-in-polygon the site lat/lon against the GDB polygons, or spatial-join
  to the basin containing the site, and read the indicator columns. Data dictionary:
  https://github.com/wri/Aqueduct40/blob/master/data_dictionary_water-risk-atlas.md
- **Alternate access (no big download):** WRI Aqueduct layers are also in Google Earth Engine
  (`WRI/Aqueduct_Water_Risk/V4/baseline_annual`) if you move the pipeline to GEE.
