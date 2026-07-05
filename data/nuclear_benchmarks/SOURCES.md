# Nuclear benchmarks & OpenMC data (Stream A / WP A3)

## KRUSTY benchmark model — `virtual_test_bed/microreactors/KRUSTY/` (28 files)
- **Source:** INL Virtual Test Bed (VTB), https://github.com/idaholab/virtual_test_bed
  (sparse checkout of `microreactors/KRUSTY` only). Docs:
  https://mooseframework.inl.gov/virtual_test_bed/microreactors/KRUSTY/Model_Description.html
- **Retrieved:** 2026-07-04
- **License:** LGPL/INL open (see repo LICENSE)
- **What it is:** KRUSTY (Kilopower Reactor Using Stirling TechnologY) — the 2018 NNSS criticality
  experiment, the standard validation case for space/heat-pipe micro-cores. Folder contains:
  - `Neutronics/Serpent/` — Serpent Monte-Carlo inputs (geometry + materials → **translate to OpenMC**)
  - `Neutronics/Griffin/`, `MC23/` — deterministic + MC inputs
  - `Multiphysics_*` — Griffin (neutronics) + BISON (thermomechanics) coupled cases at 15/30 °C
  - `gold/` — reference output CSVs (expected k-eff, power, reactivity) = **the validation targets**
- **Use:** rebuild the KRUSTY core in OpenMC, match k-eff and reactivity coefficients against the
  `gold/` outputs and published values. This is objective O2 deliverable (i).
- **Gold-standard spec (behind paywall):** the ICSBEP Handbook evaluation (OECD-NEA) is the formally
  peer-reviewed benchmark; access via OECD-NEA / an institutional login. The VTB model + published
  KRUSTY papers (Poston et al., *Nuclear Technology* 2020) are sufficient open substitutes.

## OpenMC cross sections — `openmc_xs/endfb-viii.1-hdf5.tar.xz` (9.0 GB compressed)
- **Source:** https://openmc.org/data/ → ENDF/B-VIII.1 HDF5
  (`https://anl.box.com/shared/static/6qr7jezzihkj9p9esl5jn19qgpujyjyz.xz`)
- **Retrieved:** 2026-07-04 (xz integrity verified)
- **License:** public (ENDF/B evaluated nuclear data, processed with NJOY2016.78 by OpenMC team)
- **Temperatures:** 250, 293.6, 600, 900, 1200, 2500 K — covers KRUSTY + eVinci operating range;
  includes incident neutron, photoatomic, atomic relaxation, thermal scattering + depletion chains
- **NOT yet extracted** (expands to a large multi-GB `endfb-viii.1-hdf5/` tree). To use:
  `tar -xf endfb-viii.1-hdf5.tar.xz` then
  `export OPENMC_CROSS_SECTIONS=$(pwd)/endfb-viii.1-hdf5/cross_sections.xml`
- **Note:** VIII.1 chosen over VIII.0 (both linked on openmc.org/data) as the newest evaluation.
  VIII.0 (smaller, ~2.5 GB) is the fallback if a published KRUSTY OpenMC benchmark pinned that version —
  match the benchmark's library for the validation run. The depletion chain XML (needed for decay-heat,
  objective O2-ii) ships in this same bundle.
