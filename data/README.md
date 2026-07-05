# Project Data Directory

All external data for the derating + siting study. Every subfolder gets a `SOURCES.md`
noting origin URL, retrieval date, license, and any access caveats. Nothing in here is
hand-edited — raw downloads only; derived/processed tables live elsewhere (pipeline TBD).

| Folder | Contents | Feeds |
|--------|----------|-------|
| `sites/` | Candidate site register (v0 = 16 sites from Proposal 2; → 30–80) | B1 |
| `climate/nasa_power/` | NASA POWER daily series (2015–2024) + monthly climatology per site | B2, B3 (derating applicator) |
| `water/` | WRI Aqueduct water-risk layers for Saudi Arabia | B2 |
| `population/` | WorldPop rasters, GASTAT extracts | B2 |
| `mining/` | Mining cadastre / license locations (Ministry of Industry & Mineral Resources) | B1, B2 |
| `industrial/` | MODON industrial-city registry | B1, B2 |
| `grid/` | OSM power-infrastructure extract, SEC report data | B2 |
| `nuclear_benchmarks/` | KRUSTY benchmark specs/reports for OpenMC validation | A3 |
| `evinci_docs/` | Public eVinci design documents (NRC ADAMS, IAEA ARIS, papers) | A1 |
| `economics/` | IAEA DEEP tool, SWCC cost references, HERON/RAVEN pointers | B6 |
| `seismic/` | Seismic hazard layers (GEM/global models, SGS if available) | B2 |
| `renewables/` | Solar atlas comparator context | B2 (optional) |

## Site register notes

`sites/site_register_v0.csv` — the 16 named sites from `Microreactor_Siting_Proposal_2.docx`
with approximate coordinates. `coord_confidence=low` rows (the two central-Arabian gold mines)
must be verified against the mining cadastre before any distance-based features are computed.
For NASA POWER climate this doesn't matter (grid cell ~55 km), so climate pulls proceed on v0.

## Reproducibility

Scripted pulls live in `../scripts/` (e.g., `pull_nasa_power.py`). Re-running a script must be
idempotent (skip existing files). Large datasets that are impractical to commit are documented
in the relevant `SOURCES.md` with the exact download command instead.
