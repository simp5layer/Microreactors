# Deep-Research Source Survey — verified findings (persisted)

Run 2026-07-04 (deep-research workflow, 111 verified agents, 29 sources fetched, 141 claims → 25
adversarially verified → 21 confirmed / 4 refuted). This is the persisted synthesis; the actionable
download URLs already live in each `data/<folder>/SOURCES.md`. Kept here so future agents have the full
provenance, the **refuted** claims (things NOT to assume), and the **open questions**.

## Confirmed (3-0 verified) — the 5 directly-accessible categories
1. **NASA POWER** — keyless GET, any Saudi coordinate. Hourly `T2M` (2 m air temp, °C) from 2001-01-01 to
   near-real-time (UTC + LST); daily from 1981; plus monthly/climatology. Endpoints
   `/api/temporal/{hourly,daily,climatology}/point`. Reanalysis (MERRA-2), native ~0.5°×0.625° → grid-cell
   values, not station. Verified live against Riyadh in 2026 (API v2.9.4/2.9.5).
2. **WRI Aqueduct 4.0** — single ~261 MB zip, `files.wri.org/aqueduct/aqueduct-4-0-water-risk-data.zip`,
   CC BY 4.0, HydroBASINS level, global (Saudi covered). GitHub `wri/Aqueduct40` = metadata only.
3. **WorldPop** — Saudi 2020 population, 100 m constrained GeoTIFF (~13 MB, CC BY 4.0) at
   `data.worldpop.org/.../Global_2000_2020_Constrained/2020/BSGM/SAU/sau_ppp_2020_UNadj_constrained.tif`.
4. **GEM Global Seismic Hazard Map** — Zenodo concept DOI **10.5281/zenodo.8409646** (v2026.1), PGA 10%/50 yr
   on rock (VS30 800), CC BY-NC-SA 4.0; incorporates the Saudi Geological Survey Arabian Peninsula (ARB) model.
5. **Global Solar Atlas / World Bank** — dataset 0038379 (Solargis/ESMAP), CC BY 4.0, no registration.

## Refuted (do NOT assume these — they were tested false)
- ❌ "NASA POWER requires a community code (SB/AG/RE)" — not mandatory (0-3).
- ❌ "Only single-point queries exist" — daily/monthly/climatology **support bounding-box/regional** requests
  (0-3), so the 30–80-site expansion need not be one call per site (Hourly stays point-only).
- ❌ "Aqueduct download requires registration" — optional, not an access gate (0-3).
- ⚠ "Five concurrent-request cap" — only weakly supported (1-2); community reports ~30 req/60 s/IP throttling,
  no hard documented quota. `pull_nasa_power.py` uses conservative 1 s spacing.

## Caveats carried forward
- All NASA POWER temperatures are gridded reanalysis, not station obs — fine for climatology-based derating,
  but desert extreme maxima can be underestimated 1–3 °C; bias-check against GSOD/ISD at 2–3 sites if absolute
  extremes matter. GEM is non-commercial (academic OK). Attribution required (not an access barrier) for
  WorldPop, Aqueduct, GEM, Global Solar Atlas.

## Open questions (unverified in this run — needing portal checks, likely the project's real barriers)
- **GASTAT / mining cadastre (Ta'adeen) / MODON**: is site-level license geometry or a coordinate list public?
  (Findings: transactional portals behind login; geocode named sites instead — see mining/ & industrial/ SOURCES.)
- **KRUSTY / eVinci / ENDF-B / DEEP / HERON-RAVEN-TEAL / SWCC**: not re-verified in this batch, but all were
  separately located and downloaded/documented (see nuclear_benchmarks/, evinci_docs/, economics/ SOURCES).
- **K.A.CARE Renewable Resource Atlas**: confirmed **offline** (rratlas.energy.gov.sa NXDOMAIN 2026-07-04).

*Full raw workflow output (all 141 claims, per-agent journal) was in the session scratchpad and is not
retained; re-run the deep-research workflow to regenerate if needed.*
