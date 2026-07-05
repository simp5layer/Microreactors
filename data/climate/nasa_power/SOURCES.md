# NASA POWER — per-site climate data

- **Source:** NASA POWER API, https://power.larc.nasa.gov/ (Prediction Of Worldwide Energy Resources)
- **Retrieved:** 2026-07-03 via `scripts/pull_nasa_power.py`
- **License:** Free and open (NASA data policy), no registration/key required
- **Community:** `RE` (renewable energy)
- **Spatial resolution:** ~0.5° × 0.625° grid cell (~55 km) — site coordinate uncertainty of tens of km is immaterial
- **Parameters:** `T2M` (2 m air temp, °C), `T2M_MAX`, `T2M_MIN`, `RH2M` (relative humidity %), `WS2M` (wind speed m/s)
- **Files per site:**
  - `<id>_<slug>_daily_2015-2024.csv` — daily values, 10 years (header block precedes CSV data; data starts after `-END HEADER-`)
  - `<id>_<slug>_climatology.json` — long-term monthly climatology
- **Known caveat:** POWER daily T2M is a reanalysis product (MERRA-2 derived); desert extreme maxima can be underestimated by 1–3 °C vs. station data. For the derating applicator, consider bias-checking against GSOD/ISD station records at 2–3 sites (e.g., Sharurah, Jubail) before relying on absolute extremes.
- **Next fidelity step:** hourly pulls (`/api/temporal/hourly/point`) for top-ranked sites when computing effective capacity factor — daily min/max + a diurnal model suffices for v0/v1.
