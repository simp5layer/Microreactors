# Population / demand proxies

## sau_ppp_2020_1km_Aggregated_UNadj.tif (9.7 MB)
- **Source:** WorldPop, https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/2020/SAU/
- **Retrieved:** 2026-07-04 via curl (100 m product repeatedly stalled server-side; 1 km
  aggregated is sufficient for site-level density features — sites are ranked on
  population within tens-of-km radii, not street-level)
- **License:** CC BY 4.0 — cite: WorldPop (www.worldpop.org), Univ. of Southampton
- **Content:** estimated persons per pixel (~1 km), 2020, UN-adjusted totals
- **Use:** per-site population within 5/20/50 km radii → "population density" AHP criterion
  (lower preferred for early siting/licensing) and remote-electrification demand proxy
- **If higher resolution needed later:** the **100 m constrained** product is confirmed available and
  small (~13 MB, CC BY 4.0) at
  `https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/SAU/sau_ppp_2020_UNadj_constrained.tif`
  (hub page id=50064). The WorldPop server was intermittently timing out 2026-07-03/04 — retry later;
  the 1 km aggregated raster already in hand is sufficient for site-level density features.

## GASTAT (General Authority for Statistics)
- **Current portal:** https://open.data.gov.sa/ (200 OK). The old dataset URL
  `od.data.gov.sa/.../population-by-nationality-and-region` is **defunct** — it now 302-redirects to
  the portal root, not an equivalent dataset (confirmed in the deep-research run). Search the new
  portal for the current population dataset.
- Also `https://www.stats.gov.sa/` — city/governorate population tables (XLSX).
- To be pulled selectively for named-site sanity checks only (WorldPop is the primary density source).
