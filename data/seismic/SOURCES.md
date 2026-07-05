# Seismic hazard (Stream B — exclusion/derating layer, minor criterion)

## Status: use GEM global model; Saudi is mostly low-hazard except margins

- **GEM Global Seismic Hazard Map:** https://www.globalquakemodel.org/product/global-seismic-hazard-map
  - Viewer (2026 update): https://maps.openquake.org/map/gshm-v2026_1/
  - **Data — Zenodo concept DOI 10.5281/zenodo.8409646** (latest v2026.1). Primary layer: PGA with
    10% probability of exceedance in 50 years on reference rock (VS30 = 800 m/s). Vector bundle
    `gshm_v2026_1_vector.zip` ≈ 935 MB; PNG/poster smaller. **Not auto-downloaded** — 935 MB is
    disproportionate for a minor criterion; grab it only if a quantitative PGA feature is needed.
  - **Arabian Peninsula model (ARB):** https://hazard.openquake.org/gem/models/ARB/ — the regional
    model (built by the Saudi Geological Survey, v2018.2.0) folded into the global mosaic; a lighter
    way to get Saudi-specific hazard values.
- **License:** GEM data **CC BY-NC-SA 4.0** — non-commercial; fine for academic publication, but note
  the license if any commercial spin-off. For formal nuclear siting, IAEA SSG-9 / NRC use stricter
  return periods (2%/50 yr ≈ 2475 yr); GEM publishes those layers too. 10%/50 yr is the standard
  multi-criteria *screening* metric — sufficient here.
- **Saudi Geological Survey:** https://ngd.sgs.gov.sa — national seismic network / hazard layers
  (Arabic portal, export gated).

### Domain note (so this criterion can be set without the raster if needed)
Saudi seismic hazard is **low across the interior (Arabian Shield/Platform)** and elevated only at:
(1) the **Red Sea rift margin** (western coast — Jazan, Farasan, NEOM/Gulf of Aqaba, which had the
2009 Harrat Lunayyir dike intrusion + M5.7 near Al-Ays), and (2) **Harrat volcanic fields**
(Rahat near Madinah, Khaybar, Lunayyir). The Gulf of Aqaba (NEOM) is the highest-hazard zone.
This lets you assign a qualitative low/medium/high seismic flag per site immediately; swap in GEM
PGA values later for a quantitative feature.
