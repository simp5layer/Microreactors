# Economics — desalination cost benchmark + technoeconomic tools (Stream B / WP B6)

## SWCC-Annual-Report-2022-EN.pdf (17 MB)
- **Source:** Saudi Water Conversion Corp. (now SWA), https://www.swcc.gov.sa/uploads/SWCC-Annual-Report-2022-EN.pdf
- **Retrieved:** 2026-07-04
- **License:** public corporate report
- **Use:** production volumes, plant capacities, cost context to anchor LCOW. The headline
  **SAR 1.7/m³** cost-reduction figure is corroborated by trade press (desalination-news.com,
  Dec 2025); use SWCC's own reports for the citable production/cost numbers and note the SAR 1.7/m³
  as the current SWCC-reported benchmark to calibrate against.

## IAEA DEEP (Desalination Economic Evaluation Program) — REQUEST ACCESS
- **Source:** https://nucleus.iaea.org/Pages/deep.aspx
- **Barrier:** distributed by IAEA on request (not an open direct download). Register on IAEA NUCLEUS
  or request via the desalination programme page. Dr. Alshehri / KACST may already have it.
- **Fallback:** DEEP's methodology is published (IAEA-TECDOC series); a transparent LCOW/LCOE
  spreadsheet implementing the same annualised-cost method is an acceptable substitute and keeps the
  toolchain fully open.

## HERON / RAVEN / TEAL (INL open-source technoeconomics) — clone when needed
- RAVEN: https://github.com/idaholab/raven  (parent framework; large)
- HERON: https://github.com/idaholab/HERON  (economic optimization plugin for RAVEN)
- TEAL:  https://github.com/idaholab/TEAL   (cash-flow / NPV / LCOE engine, RAVEN plugin)
- **License:** Apache-2.0 (INL). Install: clone RAVEN, run its `dependencies` conda setup, register
  HERON+TEAL as plugins (`raven/scripts/install_plugins.py`). Heavy dependency stack — defer to WP B6.
- **Not downloaded here** (multi-GB build env); pointers only. Confirm versions at clone time.
