# Solar / renewables comparator (Stream B — optional context)

## K.A.CARE Renewable Resource Atlas — ⛔ OFFLINE (confirmed dead)
- Former URL `http://rratlas.energy.gov.sa` returns **NXDOMAIN as of 2026-07-04** (verified in the
  deep-research run). Wayback shows it live mid-2024, 404 by April 2025. The in-country measured
  solar/wind station network it hosted is no longer publicly reachable. Do not rely on it.

## Global Solar Atlas / World Bank — ✅ substitute (use this)
- **World Bank Data Catalog dataset 0038379** ("Global Photovoltaic Power Potential by Country"),
  https://datacatalog.worldbank.org/search/dataset/0038379 — CC BY 4.0, public, no registration.
  Produced by Solargis for ESMAP/World Bank. Hosts PV-potential layers + country comparison sheet.
- **Global Solar Atlas download page:** https://globalsolaratlas.info/download — serves the full
  GHI/DNI/PVOUT/TEMP GeoTIFF rasters, but it is a **JavaScript single-page app** — no static URL to
  curl; select "Saudi Arabia" in a browser to get the country bundle. Same CC BY 4.0 Solargis product.
- **Attribution required:** "© 2020 The World Bank, Source: Global Solar Atlas 2.0, Solargis."

## Why this folder exists (low priority)
Solar is the comparator / opportunity-cost context ("why a microreactor vs. PV+storage at this site"),
and the Global Solar Atlas `TEMP` layer is an independent cross-check on NASA POWER T2M for the
derating input. Not a core AHP criterion — collect the Saudi bundle manually only if the comparator
analysis is pursued.
