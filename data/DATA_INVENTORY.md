# Data Inventory — status of all data categories

Compiled 2026-07-04 from the deep-research source survey + direct downloads. Each row: what it feeds
(work package in `RESEARCH_OBJECTIVES.md`), acquisition status, and where it lives. Per-folder
`SOURCES.md` files hold the exact URLs, licenses, and processing notes.

## Legend
✅ downloaded · 🟡 partial / manual step needed · 🔗 pointer only (tool or gated) · ⛔ no open bulk source (workaround noted)

| # | Category | Feeds | Status | Location |
|---|----------|-------|--------|----------|
| 1 | **NASA POWER** climate (daily 2015–2024 + climatology, 16 sites) | B2, B3, A2 | ✅ | `climate/nasa_power/` (32 files) |
| 2 | **WRI Aqueduct 4.0** water risk (CSV + GDB) | B2 (water-stress criterion) | ✅ | `water/aqueduct-4-0-water-risk-data.zip` (249 MB) |
| 3a | **WorldPop** population raster (1 km, 2020) | B2 (pop-density criterion) | ✅ | `population/sau_ppp_2020_1km_Aggregated_UNadj.tif` |
| 3b | **GASTAT** open data (city/region population) | B2 sanity-check | 🔗 | portal https://open.data.gov.sa (200 OK) — pull tables as needed |
| 4 | **Mining** cadastre (Ta'adeen / SGS) | B1, B2 | ⛔→🟡 | `mining/SOURCES.md` — geocode named mines (points suffice) |
| 5 | **MODON** industrial cities | B1, B2 | ⛔→🟡 | `industrial/SOURCES.md` — geocode city list; check ArcGIS REST endpoint |
| 6a | **OSM** power infrastructure (GCC extract) | B2 (grid-distance) | ✅ | `grid/gcc-states-latest.osm.pbf` (240 MB) |
| 6b | **KAPSARC** regional electricity load | B (demand proxy) | ✅ | `grid/kapsarc_...load_monthly_by_region.csv` (1,584 rows) |
| 6c | **SEC** annual reports (grid maps) | B2 cross-check | 🔗 | link in `grid/SOURCES.md` |
| 7 | **KRUSTY** benchmark model (INL VTB) | A3 (OpenMC validation) | ✅ | `nuclear_benchmarks/virtual_test_bed/microreactors/KRUSTY/` |
| 8a | **IAEA ARIS** SMR catalogue 2024 (eVinci datasheet) | A1 | ✅ | `evinci_docs/IAEA_ARIS_SMR_catalogue_2024.pdf` |
| 8b | **NRC** eVinci pre-app doc (ML23355A166) | A1 | 🟡 | ADAMS blocks curl — fetch manually (`evinci_docs/SOURCES.md`) |
| 9 | **ENDF/B-VIII.1** cross sections (OpenMC) | A3 | ✅ (downloading) | `nuclear_benchmarks/openmc_xs/endfb-viii.1-hdf5.tar.xz` |
| 10 | **IAEA DEEP** desalination cost tool | B6 | 🔗 | request access (`economics/SOURCES.md`); open spreadsheet fallback |
| 11 | **HERON / RAVEN / TEAL** technoeconomics | B6 | 🔗 | GitHub clone when needed (`economics/SOURCES.md`) |
| 12 | **SWCC** annual report 2022 (LCOW anchor) | B6 | ✅ | `economics/SWCC-Annual-Report-2022-EN.pdf` |
| 13 | **GEM** seismic hazard | B2 (exclusion layer) | 🔗 | `seismic/SOURCES.md` — Zenodo DOI 10.5281/zenodo.8409646 confirmed; qualitative flag used (935 MB not worth it) |
| 14 | **Global Solar Atlas** (World Bank ds 0038379) | B2 (optional context) | 🔗 | `renewables/SOURCES.md` — K.A.CARE atlas confirmed DEAD; use World Bank/Solargis |

## What's fully in hand vs. what needs a step

**Ready to build on now (✅):** all climate, water stress, population, grid topology + demand,
the KRUSTY validation model, the eVinci design datasheet, the desalination cost anchor, and (once the
current download finishes) the OpenMC cross sections. **Stream A can start the core model + KRUSTY
validation and Stream B can build the full AHP→RF→SHAP pipeline on real data with no further
acquisition.**

**Manual/gated items — none block the critical path:**
- Mining & MODON locations: no open bulk GIS, but we need **points not polygons** → geocode the named
  sites (already started in `sites/site_register_v0.csv`). This is the main hands-on data task for B1.
- NRC eVinci PDF: ARIS datasheet already covers the design envelope; fetch the NRC doc manually only if
  a specific licensing detail is needed.
- DEEP / HERON / RAVEN: tools, not datasets — install at WP B6. Open spreadsheet LCOW method is a valid
  fallback that keeps everything open-source.
- Seismic & solar: minor/optional criteria; qualitative values available immediately, rasters later.

## Immediate next data tasks
1. **Geocode the mine + MODON city lists** → expand `sites/site_register_v0.csv` toward 30–80 (B1).
2. **Verify the two low-confidence gold-mine coordinates** (S01, S02) against Maaden disclosures/OSM.
3. **Spatial-join sites → Aqueduct basins** and **sample WorldPop within radii** → first real feature columns (B2).
4. **Extract eVinci datasheet** from the ARIS catalogue into the A1 spec table.
