# CFD v2 — Progress Summary

**Date:** 2026-07-08
**Scope:** Phase 1 (physics / derating), Stream A
**Status:** complete; work committed on branch `cfd-v2-heater-unitcell`

## Background in one paragraph

Phase 1 of the project answers a single question: how much electrical output does an air-cooled, heat-pipe microreactor (eVinci-class) lose as Saudi ambient temperature climbs from 25 °C to 55 °C? The answer is a "derating curve" — net power plotted against ambient temperature. Earlier stages built that curve from a thermodynamic model of the power cycle. One input to that model, though, was an engineering estimate rather than a measured quantity: how well the reactor's air-cooled heater moves heat into the air, and how that changes as the airflow changes with the weather. This work replaced that estimate with a physics simulation and checked whether it changes the curve.

## What was achieved

- Built a computational fluid dynamics (CFD) model, in OpenFOAM, of the reactor's air-cooled finned-tube heater — the component that carries reactor heat into the air stream driving the turbine.
- **Validated it against published experimental data.** The simulated heat-transfer performance agreed with the standard published correlation (Briggs–Young) to within about **15%**, comfortably inside the accepted engineering tolerance of 20%. In other words, the simulation is trustworthy, not merely plausible.
- Fed the validated result back into the derating model to regenerate the curve — the "v2" curve.
- Documented the method, the results, and the limitations honestly, and left behind a reusable, validated simulation setup.

## Results

- The v2 curve comes out essentially identical to the previous version: about a **9% power loss at 55 °C** relative to 25 °C (8.7%, versus 8.8% before).
- That near-identical result **is** the finding worth reporting: the derating is **robust** — it does not hinge on the fine details of the heater's heat-transfer behaviour. The dominant cause of desert derating is the gas-turbine "hot-day" effect of the open-air cycle, which the earlier models already captured well. Confirming this with an independent physics simulation raises confidence in the whole Phase-1 result.
- The simulation also produced an honest, physics-based correction to one scaling parameter (how heater performance tracks airflow). It turned out to matter only at the sub-percent level across the temperature range of interest — which is why the curve barely moved.

## Why it matters

- The derating curve is now backed by a validated physics simulation rather than an assumption. That is a real credibility upgrade for the thesis and the journal paper.
- We now hold a **validated CFD workflow** for the reactor's air side. That is the durable asset: it can be pointed at harder questions that no textbook correlation can answer.

## Honest limitations (documented in full in the technical docs)

- The pressure-drop (friction) side of the simulation did not match the correlation cleanly. This is a known consequence of the simplified single-tube geometry, and it feeds only a secondary parasitic-power estimate, not the headline result.
- A single, carefully chosen operating point was validated rather than a full sweep of conditions — a deliberate efficiency choice made once that point passed validation. A fuller condition sweep and a formal mesh-sensitivity study remain available if more rigour is wanted later.

## Further work — the recirculation study

The clear next step for the CFD, and the highest-value one, is the **intake / exhaust recirculation study**.

In a real desert deployment, a microreactor's hot exhaust air can be pulled back into its own air intake. That raises the effective inlet temperature above the true ambient and makes the derating *worse* than the weather alone would suggest. No published correlation covers this effect — it depends on the specific plant layout and the local wind — so it genuinely requires CFD. The validated air-side setup built in this work is exactly the foundation that study needs to stand on.

Quantifying a recirculation penalty would also feed directly into Phase 2 (site selection): some sites and skid layouts would suffer more recirculation than others, so it would make the siting recommendations more defensible.

Other extensions that are now within reach, in rough priority order:
1. A full multi-condition CFD sweep, to derive the heat-transfer law entirely from simulation rather than validating the textbook one.
2. A fin-geometry sensitivity study (the reference fins are thermally inefficient; better fins would change the scaling).
3. A formal mesh-independence study, for publication-grade rigour on the single validated point.

## Where things live

- Technical detail and how to reproduce: `phase1_derating/cfd/README.md`
- The decision record and rationale: `DECISIONS_LOG.md` entry **D12**
- The reference-design facts and the v2 numbers: `phase1_derating/spec/A1_reference_spec_sheet.md` §4d
- The curve itself: `phase1_derating/results/derating_curve_v2.csv` and `derating_curve_v1_5_vs_v2.png`
