# Phase 1 — Desert Thermal Derating (physics stream)

Produces the **derating curve**: net output/efficiency of the eVinci-class heat-pipe microreactor vs.
ambient temperature (25–55 °C). This is the single interface Phase 2 (siting) consumes.

## Layout
```
spec/         A1_reference_spec_sheet.md   fixed reactor parameters (ARIS 2024 + documented assumptions)
cycle_model/  derating_v1.py               v1 thermodynamic model (open-air recuperated Brayton)
              hx_entu_v1_5.py              v1.5 ε-NTU HX + energy-balance refinement (adversarially verified)
results/      derating_curve_v1.csv        THE interface artifact (schema below) — replaces v0 placeholder
              derating_curve_v1_sensitivity.csv   assumption envelope
              derating_curve_v1.png        figure
              derating_curve_v1_5.csv      v1.5 curve + regime flag + both efficiencies
              derating_curve_v1_vs_v1_5.png   v1 vs v1.5 comparison (the two control-strategy bounds)
              derating_curve_v2.csv        v2 curve (CFD-validated air-side UA law injected into v1.5)
              derating_curve_v1_5_vs_v2.png   v1.5 vs v2 comparison (confirms v1.5)
cfd/          OpenFOAM heater-unitcell CFD campaign (Option 1: single-point validation, not a full
              sweep) — see `cfd/README.md`
refs/         (papers / benchmark data)
```

## Fidelity ladder (per RESEARCH_OBJECTIVES.md)
- **v1 (done, calibration v1.1):** thermodynamic cycle model, air-standard properties. Calibration fixes
  η_mech=0.93 and solves TIT=742 °C (in Na heat-pipe band) to hit net 33% @ 25 °C. `derating_v1.py`.
- **v1.5 (done, adversarially verified):** ε-NTU heat exchangers + reactor energy balance
  (`hx_entu_v1_5.py`). Shows the derating is **control-strategy-dependent**, bracketed by v1 fixed-TIT
  (−17.7% @55 °C, conservative baseline = the interface) and regime-B floating-TIT (−8.8%, optimistic).
  B→A crossover set by heat-pipe headroom. Sizes UA_heater≈152 / UA_recup≈401 kW/K for the CFD.
- **v2 (done, Option 1 — CFD validation-driven, not a full sweep):** OpenFOAM (`rhoSimpleFoam` + k-ω SST)
  solve of the staggered finned-tube heater unit cell (3.29M cells, converged, y⁺ mean 0.244) at the
  design Reynolds number, Re=8368. **Heat transfer validated** (Nu −15.2% vs Briggs–Young, within ±20%);
  **friction did not** (+489%, informational only, not wired into the power balance). The CFD-validated
  Nu(Re) law gives air-side UA scaling exponent n_air=0.454 (shallower than v1.5's assumed 0.6, from
  fin-efficiency modulation). Injected into v1.5: **penalty @55 °C = −8.7% vs v1.5's −8.8% (+0.08 pt) —
  v2 CONFIRMS v1.5**, because the ambient-driven mass-flow range (25–55 °C) is only ~4–5%, making the
  exact UA exponent second-order. See `cfd/README.md`, A1 spec §4d, DECISIONS_LOG D12 for full detail
  and honest limitations (fin clipping, friction non-validation, no formal mesh-independence study).
- Refinements: CoolProp variable air properties; compressor map instead of similarity; site-pressure
  (elevation) per Phase-2 site; CHP heat path; full CFD Reynolds sweep + friction-domain fix (future
  extension beyond Option 1).

## Interface schema (`derating_curve_v1.csv`)
`ambient_temp_C, net_MWe, net_efficiency, heat_rejection_capacity_frac, mdot_frac, w_net_kJkg, q_cycle_MW, TIT_C, net_MWe_frac_vs25C`
Phase 2 uses: NASA POWER hourly T per site → interpolate this table → per-site effective capacity factor.

## Key v1 result
Net power **−17.7% at 55 °C vs 25 °C** (5.00→4.11 MWe); derating **≈0.60 %/°C**, ~4× the Carnot slope —
the desert penalty is real and dominated by the open-air Brayton's ambient-breathing compressor. The
dominant remaining uncertainty is the compressor mass-flow law (∝p/√T vs ∝p/T) — a target for the CFD (v2).

## Reproduce
`python3 cycle_model/derating_v1.py` then `python3 cycle_model/hx_entu_v1_5.py`  (numpy, pandas, matplotlib, scipy)
(run v1 first — v1.5's comparison plot reads `derating_curve_v1.csv`)
For v2: the OpenFOAM CFD case itself is not re-run by default (see `cfd/README.md` for `run/of.sh`/
`run/Allrun`); `cd cfd && python3 -m postprocessing.fit && python3 cfd_to_v2.py` regenerates
`derating_curve_v2.csv` from the frozen, already-converged CFD validation numbers.
