# OpenFOAM CFD (v2) — Heater Air-Side UA Unit Cell — Design Spec

**Date:** 2026-07-05
**Project:** Desert thermal derating of the eVinci-class open-air Brayton microreactor (Phase 1, Stream A)
**Depends on:** `phase1_derating/` v1 (calibration v1.1) and v1.5 (ε-NTU) — this refines their assumed heat-exchanger UA.
**Status:** design approved in brainstorming (2026-07-05); pending spec review → implementation plan.

---

## 1. Problem & goal

v1.5 replaced v1's fixed-TIT shortcut with sized ε-NTU heat exchangers, but the heater's **air-side UA
(≈152 kW/K)** and its **flow scaling (UA ∝ ṁⁿ, n assumed 0.6)** are assumptions. This CFD computes them
for a defined finned-tube geometry and — as importantly — **establishes and validates an OpenFOAM air-side
model** we can trust for later cases where no correlation exists (the full bundle's pressure drop; the
intake-recirculation study). Output feeds back to produce the **v2** derating curve.

**Non-goal:** the compressor mass-flow law (ṁ vs ambient) is a compressor-map/similarity question, NOT a
CFD target here. This CFD pins how UA responds to whatever ṁ the compressor delivers.

**Scope decisions (from brainstorming):**
- Target = **heater air-side UA** (not intake recirculation — deferred as a possible follow-on study).
- Geometry = **staggered finned-tube** (richest validation correlations; how these heaters are built).
- Thermal treatment = **isothermal wall + analytical fin efficiency** (fluid-only mesh; textbook air-side extraction).
- Domain = **Approach 1: streamwise-periodic single-tube unit cell** (fully-developed bundle interior);
  **Approach 2 (multi-row developing section) is an optional refinement** if entrance effects prove material.

## 2. Architecture & tooling

```
phase1_derating/cfd/
  README.md            purpose, how to run, results summary
  geometry/            reference finned-tube params (Python); derives cell dimensions; targets v1.5 UA
  heater_unitcell/     the OpenFOAM case (0/ constant/ system/), templated per Reynolds number
  run/                 Docker wrapper (of.sh) + Allrun + Re-sweep driver
  postprocessing/      extract h(Re), f(Re); fit exponents; apply fin efficiency → UA(ṁ), Δp(ṁ)
  validation/          Briggs–Young / ESDU comparison; mesh-independence check
  results/             correlations, plots, v2 curve regeneration
```
- **OpenFOAM in Docker** (ESI `openfoam.com` image, pinned version). A thin `run/of.sh` mounts the case
  dir into the container; editing on macOS, solver runs in Linux. No native install. Docker confirmed present.

## 3. Geometry & physics

**Unit cell:** one staggered finned tube, one fin-pitch tall, surrounding air passage; **cyclic** in
transverse + spanwise directions, **streamwise-periodic** — the smallest fully-developed-interior domain.

**Reference finned-tube geometry** (high-temp air-cooled HX practice; high-temp alloy, source ~760 °C — no
aluminium). Point values below; **swept in sensitivity**; tuned so a bundle hits v1.5's UA ≈ 152 kW/K:

| Parameter | Reference value |
|---|---|
| Tube outer diameter d₀ | 25.4 mm |
| Fin height / thickness | 12 mm / 0.5 mm |
| Fin pitch (density) | 4 mm (~250 fins/m) |
| Transverse × longitudinal pitch | 2.0 d₀ × 1.75 d₀, staggered |

**Operating conditions (inherited from v1/v1.5 — no new data):**
- Air in at recuperator outlet **T3 ≈ 467 °C**, heated toward **TIT ≈ 742 °C**.
- Isothermal tube wall at heat-pipe source **~760 °C**.
- **Temperature-dependent** air properties (ρ, μ, k, cₚ) — large variation across 467–760 °C.

**Solver & closures:**
- **`rhoSimpleFoam`** — steady, compressible/variable-density, low-Mach (Mach ≪ 0.3; buoyancy negligible under forced convection).
- **k-ω SST**, **wall-resolved y⁺ ≈ 1**.
- Thermophysical: Sutherland μ(T), JANAF/polynomial cₚ(T).
- Extracted per run: **h** (wall heat flux) and **f** (streamwise Δp). Fin efficiency applied analytically.

## 4. Mesh, Reynolds sweep & feedback

- **Mesh:** `snappyHexMesh` with boundary-layer inflation to y⁺ ≈ 1 on tube+fin surfaces.
  **Mesh-independence gate** (2–3 refinement levels, asymptotic h/f) required before trusting any number.
- **Re sweep:** 5–6 Reynolds numbers spanning ±~30% around design (robust fit, no extrapolation); each a
  steady RANS solve. Fit **Nu = C·Reᵐ·Pr¹ᐟ³** and **f = C′·Reᵖ**. Exponent *m* = the heat-transfer scaling
  that replaces v1.5's assumed n = 0.6.
- **Feedback → v2:**
  1. h(Re) + analytical fin efficiency → **UA(ṁ)** (computed magnitude + exponent, replaces 152 kW/K & n=0.6).
  2. f(Re) → **air-side Δp(ṁ)** → fan/parasitic-power estimate (new).
  3. Feed both into `hx_entu_v1_5.py` → regenerate → **v2 derating curve**.

## 5. Validation & success criteria

**Validation:**
- **Method:** CFD Nu(Re) & f(Re) vs **Briggs–Young** and **ESDU** staggered finned-tube correlations;
  target ~15–20% agreement. Passing = air-side model validated for reuse on harder cases.
- Mesh independence + y⁺ ≈ 1 confirmed.
- Sanity: UA lands near 152 kW/K; a wild miss → resize the reference geometry (free parameter, documented).

**Definition of done:**
1. Mesh-independent, y⁺-resolved solution.
2. CFD Nu & f within ~20% of correlations → air-side model validated.
3. UA(ṁ) magnitude + exponent and Δp(ṁ) extracted, fed into v1.5 → **v2 curve produced**.
4. Documented: `cfd/README.md`, spec sheet §4d, `DECISIONS_LOG.md` D12.

**Effort/compute:** medium; runs on macOS in Docker (each Re point minutes–~1 h; full sweep + validation ~a
few days wall-clock). No HPC for the unit cell.

**Risk/fallback:** CFD–correlation divergence = a setup signal (mesh/BC/turbulence) to debug, not a result.
The correlations are themselves the fallback air-side model, so v2 is not blocked if OpenFOAM setup stalls.

## 6. Out of scope (explicit)
- Intake/exhaust recirculation study (possible follow-on; needs assumed skid external geometry).
- Full-bundle 3-D case (rung 3).
- Conjugate heat transfer / solid fin conduction (possible refinement; isothermal + analytical fin efficiency used here).
- Compressor mass-flow law (compressor-map question, not CFD).
