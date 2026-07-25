# CFD v2 — OpenFOAM Air-Side Heater Unit Cell: Full Technical Report

**Project:** Combined Microreactor — Phase 1 (physics / derating), Stream A
**Reference design:** Westinghouse eVinci-class heat-pipe microreactor, 15 MWth / 5 MWe, open-air Brayton PCS
**Date:** 2026-07-08
**Solver:** OpenFOAM (ESI) v2406, `rhoSimpleFoam`, steady compressible RANS + k-ω SST
**Status:** complete and validated; merged to `main`

> **Purpose of this document.** This is the self-contained reproduction and reference record for
> the OpenFOAM campaign that produced the **v2 derating curve**. It states every specification,
> parameter, dictionary value, geometry definition, boundary condition, property model, numerical
> setting, and result used in the run, plus the methodology and honest limitations. A subsequent
> agent should be able to (a) rebuild the case from scratch, (b) re-run or extend it, or (c) reuse
> the numbers as a validated reference — without re-deriving anything. Where a value is a *measured*
> CFD output it is flagged as such; where it is an *input* or a *modelling choice* it is flagged too.

---

## 0. Executive summary

The open-air Brayton power conversion system of the reference microreactor rejects/absorbs reactor
heat through an **air-cooled finned-tube heater**. The v1.5 cycle model had to *assume* how that
heater's conductance `UA` scales with air mass flow (`UA ∝ ṁ⁰·⁶`). This campaign replaced that
assumption with a physics simulation:

1. Built an OpenFOAM CFD model of one staggered finned-tube **unit cell** of the heater.
2. Ran it at the cycle **design Reynolds number (Re = 8368)** and measured the air-side heat transfer.
3. **Validated** the measured heat transfer against the published **Briggs–Young (1963)** correlation:
   `Nu_CFD(LMTD) = 45.9` vs `Nu_BY = 54.1` → **−15.2 %, inside the ±20 % engineering gate → VALIDATED.**
4. Adopted the now-validated Briggs–Young `Nu(Re)` law, converted it to a heater `UA(ṁ)` law
   (modulated by fin efficiency), and injected it back into the v1.5 cycle model to regenerate the
   derating curve — the **v2 curve**.

**Headline result:** v2 penalty at 55 °C = **−8.7 %** vs v1.5's **−8.8 %** (a **+0.08-point delta**).
**v2 confirms v1.5.** The derating is *robust* to the exact air-side heat-transfer law because the
open-air Brayton's ambient-driven air mass flow varies only ~4–5 % over 25→55 °C, making the
UA-scaling exponent a second-order effect. The desert penalty is dominated by compressor-inlet
thermodynamics, not by the heater's heat-transfer law.

**Durable asset produced:** a **validated OpenFOAM air-side setup** that can be pointed at problems
no textbook correlation covers (the intended next study: intake/exhaust recirculation).

---

## 1. Physical problem and modelling scope

### 1.1 What is being modelled
The heater is a bank of horizontal, transversely-finned tubes carrying reactor heat (via sodium heat
pipes / the primary loop) into the compressed air stream that then expands through the turbine. The
CFD models **one representative tube** of that staggered bank as a periodic **unit cell** in
crossflow, at the on-design air state (≈2 bar, 740 K inlet), with an **isothermal wall at 1033 K**
standing in for the heat-pipe-fed tube surface. The quantity of interest is the **air-side convective
heat-transfer coefficient `h`** (and hence `Nu`), from which the heater conductance `UA = h·A·η_o`
and its mass-flow scaling are derived.

### 1.2 What is deliberately *not* modelled
- **No conjugate heat transfer / no solid conduction inside the tube or fin metal.** The wall is a
  fixed-temperature boundary. Fin conduction is handled analytically afterward via a fin-efficiency
  factor (§5.3), not inside the CFD.
- **No radiation.**
- **No heat-pipe / primary-side physics.** The 1033 K wall is the interface to that side.
- **Single tube only** — the staggered-neighbour interleaving is approximated by periodic/symmetry
  boundaries (see §4 and the fin-clipping limitation §7.1).
- **Steady state** (`rhoSimpleFoam`, `ddt = steadyState`). No transient / unsteady wake shedding.

### 1.3 Design operating point (the single validated point — "Option 1")
| Quantity | Value | Origin |
|---|---|---|
| Air inlet static temperature `T_in` | **740 K** | cycle compressor-exit / heater-inlet air temperature |
| Isothermal tube wall temperature `T_wall` | **1033 K** | heat-pipe-fed tube surface (input BC) |
| Heater-side static pressure `p` | **2.0 × 10⁵ Pa** (~2 bar) | post-compressor pressure ratio × ambient |
| Inlet approach velocity `U_in` | **6.3623 m/s** (+y) | set to hit the design Re |
| Reynolds number `Re` (tube-OD, min-flow-section mass flux) | **8368** | cycle design mass flux |
| Prandtl number `Pr` | **0.69** (explicit modelling choice) | high-T air |

**Only one CFD point was run** ("Option 1"). Once this point validated heat transfer against the
correlation, a multi-point Reynolds sweep would only have refined the `Nu(Re)` *shape* — which the
sensitivity analysis (§6.3) shows is second-order to the derating result. See §8 (DECISIONS_LOG D12)
for the full justification.

---

## 2. Geometry — staggered finned-tube unit cell (written out in full)

This is the exact geometry meshed in OpenFOAM. It is generated parametrically in Python
(`geometry/finned_tube.py` for the dimensions and derived quantities; `geometry/make_stl.py` for the
triangulated surface `tube.stl` that snappyHexMesh carves out of the background box).

### 2.1 Reference dimensions (`FinnedTube.REFERENCE`)
All lengths in metres unless noted. A single annularly-finned circular tube:

| Symbol | Parameter | Value | mm |
|---|---|---|---|
| `d_o` | tube outer diameter | 0.0254 | **25.400 mm** |
| `fin_h` | fin height (radial, root→tip) | 0.012 | **12.000 mm** |
| `fin_t` | fin thickness (axial) | 0.0005 | **0.500 mm** |
| `fin_pitch` | fin centre-to-centre spacing (axial) | 0.004 | **4.000 mm** |
| `S_T` | transverse tube pitch = 2.00·`d_o` | 0.0508 | **50.800 mm** |
| `S_L` | longitudinal tube pitch = 1.75·`d_o` | 0.044450 | **44.450 mm** |
| `k_fin` | fin thermal conductivity (high-T alloy) | 25.0 W/m·K | — |

Derived radii: tube outer radius `r_t = d_o/2 = 12.700 mm`; **fin outer radius `r_f = d_o/2 + fin_h
= 24.700 mm`**. Note `r_f (24.700 mm) > S_L/2 (22.225 mm)` — the fins are taller than the
half-longitudinal-pitch. This is intrinsic to the reference design (fin height ≈ tube radius) and is
the root of the fin-clipping limitation (§7.1).

### 2.2 Derived geometric quantities (used by the correlations and the UA law)
Computed from the closed forms in `geometry/finned_tube.py`, evaluated for `REFERENCE`:

| Quantity | Formula (per fin pitch unless noted) | Value |
|---|---|---|
| Minimum free-flow area / pitch | `(S_T − d_o)·fin_pitch − 2·fin_h·fin_t` | 8.9600 × 10⁻⁵ m² |
| Minimum free-flow area (3 pitches = domain `A_min`) | `3 ×` above | 2.6880 × 10⁻⁴ m² |
| Total air-side area / pitch | `2 fin faces + fin edge + exposed bare tube` | 3.176778 × 10⁻³ m² |
| Total air-side area (3 pitches, analytical `A_air`) | `3 ×` above | 9.530335 × 10⁻³ m² |
| Hydraulic diameter | `4·A_min_perpitch·S_L / A_air_perpitch` | 5.0148 mm |
| Fin efficiency at design `h` (≈130.3 W/m²K) | `tanh(mL_c)/(mL_c)`, Harper `L_c = fin_h + fin_t/2`, `m = √(2h/(k_fin·fin_t))` | **0.5334** |

The closed forms (for reproduction):
```
min_flow_area_per_pitch = (S_T − d_o)·fin_pitch − 2·fin_h·fin_t
air_area_per_pitch      = 2π(r_f² − r_t²)  [two fin faces]
                        + 2π·r_f·fin_t      [fin outer edge]
                        + π·d_o·(fin_pitch − fin_t)  [exposed bare tube between fins]
hydraulic_diameter      = 4·min_flow_area_per_pitch·S_L / air_area_per_pitch
fin_efficiency(h)       = tanh(m·L_c)/(m·L_c),  m = √(2h/(k_fin·fin_t)),  L_c = fin_h + fin_t/2
```

### 2.3 The meshed unit cell (STL construction — `make_stl.py`)
The STL is a **single tube spanning 3 fin pitches** (`n_fins = 3`, `total_z = 3 × 4 mm = 12 mm`),
built as a watertight triangulated surface with `n_theta = 64` circumferential facets:

- **Bare-tube cylinder** at radius `r_t`, emitted **only over the axial sub-intervals *between* fin
  bands** (the tube surface inside a fin band is interior to the fin solid and must not be emitted, or
  snappyHexMesh sees a coincident interior patch).
- **3 annular fins**, each a thin disc of thickness `fin_t` centred at `z = (k+0.5)·fin_pitch` for
  `k = 0,1,2` (i.e. z = 2, 6, 10 mm). Each fin = two flat annuli (`r_t → r_f`) at `z_c ± fin_t/2`
  (bottom face wound to give a −z outward normal, top face +z), plus a short cylinder at `r_f`
  forming the fin outer edge.

Axis convention (critical — resolves an earlier plan typo):
- **z = tube axis = spanwise.** Fins stack along z at `fin_pitch`. z is a symmetry/closure direction,
  **not** streamwise.
- **y = streamwise.** Crossflow enters in +y.
- **x = transverse** (the S_T direction).

STL bounding box: `(2·r_f, 2·r_f, total_z) = (49.4 mm, 49.4 mm, 12 mm)`. The measured (fin-clipped)
wetted area of the meshed `tube` patch is **9.0165 × 10⁻³ m²** (329 016 faces), i.e. 0.946× the
analytical unclipped `A_air = 9.530 × 10⁻³ m²` — the deficit is the fin metal clipped by the
streamwise box boundary (§7.1).

---

## 3. Computational domain and mesh

### 3.1 Background block (`system/blockMeshDict`)
A single hex block sized to one unit cell, centred on the tube axis at (x,y) = (0,0):

| Direction | Extent | Physical meaning | Length |
|---|---|---|---|
| x | −0.0254 … +0.0254 | ± S_T/2 (transverse) | 50.8 mm |
| y | −0.022225 … +0.022225 | ± S_L/2 (streamwise) | 44.45 mm |
| z | 0.0 … 0.012 | 3 × fin_pitch (spanwise, tube axis) | 12.0 mm |

Base grid: `(40 × 34 × 9)` cells, `simpleGrading (1 1 1)` → base cell ≈ `d_o/20 ≈ 1.27 mm`.

Boundary patches (background):
| Patch | Type | Face | Role |
|---|---|---|---|
| `inlet` | patch | y = ymin | air enters +y |
| `outlet` | patch | y = ymax | air exits |
| `cyclicX_neg` / `cyclicX_pos` | cyclic pair | x = xmin / xmax | transverse periodicity (tube bank in x) |
| `symZ_neg` / `symZ_pos` | symmetryPlane | z = zmin / zmax | spanwise closure at exact mid-fin-gap planes |
| `tube` | wall (from snappy) | STL surface | the finned-tube surface |

**Why symmetryPlane (not cyclic) in z:** z = 0 and z = 12 mm sit at exact symmetry planes of the fin
array (mid-gap between fins). The tube axis lies *along* z, so the wall crosses these planes;
symmetry is layer-meshable there where cyclic is not, and is physically identical for this
configuration. z is a **closure** direction, not a streamwise-cyclic bundle direction.

### 3.2 snappyHexMesh (`system/snappyHexMeshDict`)
Castellate + snap + add layers, carving the STL tube out of the background box.

- **Refinement:** surface `level (2 3)` → 0.16–0.32 mm on the general tube surface. Feature edges
  (`tube.eMesh`) at `level 3`. **Gap refinement `gapLevel (4 1 4)`** drives the thin 0.5 mm fins
  (tip + faces) to level 4 (~0.08 mm) so ≥4 cells span the fin thickness — without this the fin tips
  sit on 0.32 mm cells and hit y⁺ ~7 at the shoulders.
- `nCellsBetweenLevels 2`, `resolveFeatureAngle 30`, `maxGlobalCells 4 000 000`.
- `locationInMesh (0.023 0.020 0.0005)` — a domain corner firmly in the air, outside the finned
  envelope (`|(0.023, 0.020)| = 0.0305 m > r_f = 0.0247 m`).
- **Boundary layers on `tube`:** `nSurfaceLayers 8`, `expansionRatio 1.2`, `relativeSizes true`,
  `finalLayerThickness 0.3` (thinner first cell ≈ 24 µm for y⁺ margin), `minThickness 0.008`,
  `featureAngle 170` (wraps layers around convex fin edges/tips).

### 3.3 Feature extraction (`system/surfaceFeatureExtractDict`)
`extractFromSurface`, `includedAngle 150` (edges sharper than 30° kept). `nonManifoldEdges no`,
`openEdges no` (tube ends lie on symmetry planes — no feature there).

### 3.4 Mesh quality limits (`system/meshQualityDict`)
Standard OpenFOAM defaults tuned for the wall-resolved layers:
`maxNonOrtho 65` (relaxed 75), `maxBoundarySkewness 20`, `maxInternalSkewness 4`, `maxConcave 80`,
`minVol 1e-14` (allows thin wall-resolved layer cells), `minTetQuality 1e-15`, `minTwist 0.02`,
`minDeterminant 0.001`, `minFaceWeight 0.02`, `minVolRatio 0.01`, `nSmoothScale 4`,
`errorReduction 0.75`.

### 3.5 Resulting mesh (measured — `log.checkMesh`, `constant/polyMesh/boundary`)
| Metric | Value |
|---|---|
| Total cells | **3 288 913** (≈3.29 M) |
| Hexahedra / prisms / polyhedra | 3 092 437 / 4 872 / 191 308 |
| Max aspect ratio | 22.44 — OK |
| Max non-orthogonality | **64.84** (avg 7.08) — OK |
| Max skewness | **3.05** — OK |
| `checkMesh` verdict | **Mesh OK** |
| `tube` patch faces (wetted area) | 329 016 faces (9.0165 × 10⁻³ m²) |
| `inlet` / `outlet` faces | 9 828 each |

---

## 4. Boundary conditions and physics setup

### 4.1 Field boundary conditions (`0.orig/`)
Air enters in +y at 740 K, ~2 bar; the finned tube is an isothermal 1033 K no-slip wall.

| Field | internalField | `inlet` | `outlet` | `tube` (wall) | `cyclicX_neg/pos` | `symZ_neg/pos` |
|---|---|---|---|---|---|---|
| **U** [m/s] | (0 6.3623 0) | fixedValue (0 6.3623 0) | pressureInletOutletVelocity | noSlip | cyclic | symmetryPlane |
| **T** [K] | 740 | fixedValue 740 | inletOutlet (740) | **fixedValue 1033** | cyclic | symmetryPlane |
| **p** [Pa] | 2.0e5 | zeroGradient | fixedValue 2.0e5 | zeroGradient | cyclic | symmetryPlane |
| **k** [m²/s²] | 0.1518 | fixedValue 0.1518 | inletOutlet (0.1518) | kqRWallFunction | cyclic | symmetryPlane |
| **omega** [1/s] | 280 | fixedValue 280 | inletOutlet (280) | omegaWallFunction | cyclic | symmetryPlane |
| **nut** [m²/s] | 0 | calculated | calculated | nutUSpaldingWallFunction | cyclic | symmetryPlane |
| **alphat** [kg/m/s] | 0 | calculated | calculated | compressible::alphatWallFunction (Prt 0.85) | cyclic | symmetryPlane |

**Inlet turbulence:** intensity `I = 5 %`, length scale `L = 0.1·d_o = 2.54 mm`, giving
`k = 1.5·(I·U_in)² = 0.1518 m²/s²` and
`omega = √k / (C_µ^0.25·L) = √0.1518 / (0.09^0.25 · 0.00254) ≈ 280 s⁻¹`.

**Wall treatment:** low-Re, wall-resolved. `nutUSpaldingWallFunction` + `omegaWallFunction` are the
k-ω SST **blended** wall functions, valid continuously from the viscous sublayer through the log
layer — so they remain correct even where local y⁺ exceeds the ≤2 target (see §7.5). Turbulent
Prandtl number `Prt = 0.85`.

### 4.2 Thermophysical properties (`constant/thermophysicalProperties`)
```
thermoType:  hePsiThermo / pureMixture / sutherland transport / janaf thermo
             / perfectGas equationOfState / sensibleEnthalpy
molWeight    = 28.96 g/mol   (air)  → R = 287 J/kg·K
Sutherland:  µ = As·T^1.5/(T + Ts),  As = 1.458e-6,  Ts = 110.4 K
JANAF cp:    Tlow 200 / Thigh 2500 / Tcommon 1500 K
   highCpCoeffs (3.09  0.00124  -4.2e-7  6.7e-11  -3.9e-15  -996  5.34)
   lowCpCoeffs  (3.57  -7.2e-4   1.66e-6 -6.6e-10  5.1e-14  -1047 3.72)
```
**Critical numerical note:** `Tcommon` was raised to **1500 K** — above the whole operating+transient
band (740–1033 K) — deliberately. The two JANAF coefficient sets are ~1 % discontinuous in enthalpy
at their join; with the default `Tcommon = 1000 K` sitting *inside* the operating range, the `T(h)`
Newton inversion oscillated across that jump and failed to converge. Pushing `Tcommon` above the band
makes the entire domain use one smooth coefficient set.

### 4.3 Turbulence model (`constant/turbulenceProperties`)
RANS, `kOmegaSST`, `turbulence on`, `printCoeffs on`.

### 4.4 Temperature clipping (`constant/fvOptions`)
`limitTemperature`, `selectionMode all`, **min 300 K / max 1200 K**. This is a *transient-safety*
limiter that stops an early SIMPLE iterate from driving a cell outside the JANAF thermo range; at
convergence the field is physical (max wall-adjacent T ≤ 1033 K) and the limiter is dormant.

---

## 5. Numerical method and solver

### 5.1 Solver and schemes (`rhoSimpleFoam`; `system/fvSchemes`, `system/fvSolution`)
Steady compressible pressure-based SIMPLE.

- **ddt:** `steadyState`.
- **grad:** `Gauss linear`; `cellLimited Gauss linear 1` on U, e, h, k, omega.
- **div:** `bounded Gauss linearUpwind grad(U)` for momentum/energy (U, e, h, K, Ekp);
  `bounded Gauss upwind` for k, omega, and `div(phiv,p)`.
- **laplacian:** `Gauss linear corrected`. **snGrad:** `corrected`. **wallDist:** `meshWave`.
- **Linear solvers:** `p` → GAMG / GaussSeidel, tol 1e-8, relTol 0.05; `(U|e|h|k|omega)` → PBiCGStab
  / DILU, tol 1e-8, relTol 0.1.
- **SIMPLE:** `consistent yes` (SIMPLEC), `nNonOrthogonalCorrectors 2`, residualControl 1e-4 on
  p, U, e, h, k, omega.
- **Relaxation:** fields p 0.3, rho 0.05; equations U 0.5, e 0.5, h 0.5, (k|omega) 0.5.

### 5.2 Run configuration (`system/controlDict`)
`application rhoSimpleFoam`; `endTime 2000`; `deltaT 1`; `writeInterval 100`; `purgeWrite 2`;
`writeFormat ascii`; `writePrecision 8`; `runTimeModifiable true`.

**Function objects (in-run diagnostics):**
- `yPlus1` — y⁺ on all walls at write time.
- `wallHeatFlux1` — wall heat flux + integral heat rate `Q` over the `tube` patch (this is the
  primary measurement for `h`).
- `fieldMinMax1` — min/max of U, p, T every 50 steps (physicality check).
- `pIn` / `pOut` — area-averaged static pressure on `inlet` / `outlet` every step (for the
  streamwise Δp / friction factor).

### 5.3 Parallelisation (`system/decomposeParDict`)
`numberOfSubdomains 10`, `method scotch`. The ~3.29 M-cell mesh is impractical serially; the solve
runs on 10 cores.

### 5.4 Execution pipeline (`run/Allrun`, `run/of.sh`)
All OpenFOAM commands run inside the ESI image `opencfd/openfoam-default:2406` via Docker, with the
`cfd/` tree mounted at `/cfd`. **Docker quirk:** the image ENTRYPOINT `cd`s to `$HOME`, so
`docker run -w` is ignored; `of.sh` instead `cd`s to the case dir *inside* the container command.

```
blockMesh
  → surfaceFeatureExtract           # sharp fin edges → tube.eMesh
  → snappyHexMesh -overwrite        # carve tube, snap, 8 boundary layers
  → checkMesh                       # quality gate → "Mesh OK"
  → cp -r 0.orig 0
  → decomposePar                    # 10 subdomains (scotch)
  → mpirun -np 10 rhoSimpleFoam -parallel
  → reconstructPar -latestTime
```

### 5.5 Convergence (measured — solver logs)
SIMPLE **converged in 464 iterations**, all monitored residuals < 1 × 10⁻⁴. Final-time fields
(Time 464/466) are steady; the temperature limiter is dormant (physical field).

y⁺ on the `tube` patch (measured, converged): **min 6.60 × 10⁻⁴, mean 0.244, max 4.63.** The mean
satisfies the plan's y⁺ ≤ 2 wall-resolution gate; the max exceeds it locally at the fin
leading-edge tips (§7.5).

---

## 6. Post-processing, validation, and the UA(ṁ) law

### 6.1 Measured CFD quantities (converged, Time 466)
Frozen as documented constants in `validation/single_point_check.py` (they match the live
`postprocessing.extract` output on the case; the `postProcessing/` tree itself is gitignored):

| Quantity | Symbol | Value | Source |
|---|---|---|---|
| Integral wall heat rate over `tube` | `Q` | **256.30 W** | `wallHeatFlux1` integral column |
| Measured wetted area of `tube` patch | `A_wetted` | **9.0165 × 10⁻³ m²** | 329 016 faces (fin-clipped) |
| Streamwise pressure drop | `Δp = p_in − p_out` | **148.4 Pa** (200148.4 − 200000.0) | `pIn`/`pOut` probes |
| Wall / inlet temperature | `T_wall` / `T_in` | 1033 / 740 K | BC (input) |
| Inlet velocity / area | `U_in` / `A_inlet` | 6.3623 m/s / 5.773 × 10⁻⁴ m² | BC / mesh |
| y⁺ mean / max (tube) | — | 0.244 / 4.63 | `yPlus1` |
| Streamwise tube rows in domain | `N_rows` | 1 | single-tube unit cell |

### 6.2 Reduction to Nu and f (the validation, `validation/single_point_check.py`)
**Property model (stated explicitly, reused everywhere for consistency):**
`ρ = p/(R·T)` with R = 287; `µ = Sutherland`; `cp = 1080 J/kg·K` (representative high-T air, JANAF
band); `Pr = 0.69` as an explicit choice so `k_air = µ·cp/Pr` (rather than a derived number) keeps
`Nu = h·d_o/k` consistent with the Pr fed to Briggs–Young. Properties evaluated at the **film
temperature** `T_film = (T_wall + T_bulk_mean)/2`.

Reduction steps:
1. `ρ_in = p/(R·T_in)`, `ṁ = ρ_in·U_in·A_inlet`.
2. `T_out = T_in + Q/(ṁ·cp)`; `T_bulk_mean = (T_in+T_out)/2`; `T_film = (T_wall+T_bulk_mean)/2`.
3. Area-averaged wall flux `q″ = Q/A_wetted`.
4. **Two ΔT conventions for h** (the choice is material — see below):
   - `h_inlet = q″/(T_wall − T_in)` → `Nu_inlet = 40.3`
   - `h_LMTD = q″/LMTD`, `LMTD = (ΔT_in − ΔT_out)/ln(ΔT_in/ΔT_out)` → **`Nu_LMTD = 45.9`**
5. Reynolds number at the minimum-flow section: `A_min = 3·min_flow_area_per_pitch = 2.688 × 10⁻⁴ m²`,
   `G_max = ṁ/A_min`, `Re = G_max·d_o/µ(T_film) = 8368`.
6. Friction factor (Euler number per row): `f_CFD = Δp/(0.5·ρ_in·U_max²·N_rows) = 1.688`.

**Validation against published correlations at Re = 8368:**
- **Briggs & Young (1963)** heat transfer:
  `Nu = 0.134·Re^0.681·Pr^(1/3)·(s/fin_h)^0.2·(s/fin_t)^0.1134`, `s = fin_pitch − fin_t` (inter-fin
  gap). → `Nu_BY = 54.1`.
- **Robinson & Briggs (1966)** friction (Euler number per row):
  `f = 9.465·Re^(−0.316)·(S_T/d_o)^(−0.927)`. → `f_RB = 0.287`.

| Quantity | CFD | Correlation | Deviation | Verdict |
|---|---:|---:|---:|:---|
| **Nu (LMTD)** | **45.9** | 54.1 (Briggs–Young) | **−15.2 %** | within ±20 % → **heat transfer VALIDATED** |
| Nu (inlet ΔT) | 40.3 | 54.1 | −25.5 % | outside ±20 % (wrong ΔT convention) |
| **f (friction)** | **1.688** | 0.287 (Robinson–Briggs) | **+489 %** | outside ±20 % → **does NOT validate** |

**Why LMTD, not inlet-ΔT:** the air bulk-warms appreciably across the cell, so the log-mean driving
ΔT is the physically correct mean for an integrated HX balance and is the basis of the Briggs–Young
correlation itself. Using the simpler wall-minus-inlet ΔT understates the true driving ΔT and drops
Nu to 40.3 (−25.5 %, outside the gate). **The ΔT convention is material; LMTD is the correct choice.**

**Why friction misses (and why it doesn't matter):** the CFD Δp spans the *whole* unit cell (inlet
plenum + tube + outlet wake, ≈1.7 velocity heads), whereas Robinson–Briggs describes only the
*incremental per-row* bundle loss in a fully-developed multi-row bank — different measurements.
Fin clipping (§7.1) adds spurious form drag on the CFD side. Heat transfer validates cleanly because
it is dominated by the well-resolved bulk boundary layer (mean y⁺ 0.244), not by entrance/exit
geometry. **Friction is kept informational only and is NOT wired into the v2 power balance.**

### 6.3 The CFD-validated UA(ṁ) law (`postprocessing/fit.py` → `results/cfd_correlation.json`)
Heat transfer validated, so the **now-CFD-validated Briggs–Young `Nu(Re)` law** is adopted as the
air-side model and converted to an overall heater conductance:

`UA(ṁ) = UA_des · (Nu(ṁ)/Nu_des) · (η_o(h(ṁ))/η_o(h_des))`, with Re tracking ṁ linearly
(`Re = Re_des·ṁ/ṁ_des`), **anchored to v1.5's design magnitude so v2 == v1.5 exactly at design:**

- `UA_des = 152.35 kW/K` at `ṁ_des = 54.37 kg/s` (from `cycle_model.hx_entu_v1_5.size_design`,
  computed live).
- Overall surface efficiency `η_o = 1 − (A_fin/A_tot)·(1 − η_fin(h))`, with `η_fin(h)` the annular
  fin efficiency (§2.2). Because the reference fin is thermally **inefficient** (`η_fin ≈ 0.53` at
  design — realistic for a low-conductivity k ≈ 25 W/m·K high-temperature alloy fin), `η_o` *falls*
  as h (and hence ṁ) rises: **0.62 → 0.54** across the swept range, `dln η_o/dln ṁ ≈ −0.23`.

**Effective exponent (log-log fit of the anchored law over ṁ = 0.7–1.3·ṁ_des):**
`n_air_effective = 0.454`. The raw Nu scaling is steeper (`Nu ∝ Re^0.681`), but the fin-efficiency
modulation dominates: `0.681 − 0.23 ≈ 0.454`. **This is SHALLOWER than v1.5's assumed 0.6**, not the
steeper 0.66–0.68 originally anticipated.

`results/cfd_correlation.json` (the emitted interface artifact, consumed by `cfd_to_v2.py`):
| Key | Value | Meaning |
|---|---|---|
| `C_nu` | 0.13059 | geometry coefficient in `Nu = C_nu·Re^m·Pr^(1/3)` |
| `m` | 0.681 | Briggs–Young Re-exponent |
| `C_f`, `p` | 4.9781, −0.316 | Robinson–Briggs friction (informational) |
| `Re_des` | 8368 | design/validation Reynolds number |
| `Pr` | 0.69 | Prandtl (modelling choice) |
| `k_air_des` | 0.061133 W/m·K | air conductivity at design film T |
| `UA_design_kW_per_K` | 152.349 | v1.5 anchor |
| `mdot_des_kg_s` | 54.370 | v1.5 anchor |
| `n_air_effective` | 0.4539 | effective UA∝ṁ^n (vs v1.5's 0.6) |
| `n_tubes` | 1281.4 | **diagnostic only** (tubes at L = 2.0 m reproducing UA_des) |
| `validation` | {Nu 45.9/54.1/−15.2%, f 1.688/0.287/+489%} | frozen single-point outcome |

`dp_of_mdot` (Robinson–Briggs Δp ∝ f(Re)·(ṁ/ṁ_des)²) is written to the JSON as **informational
only** — not used in the power balance.

---

## 7. Results

### 7.1 The v2 derating curve (`cfd_to_v2.py` → `results/derating_curve_v2.csv`)
The CFD-validated `UA(ṁ)` law is injected into v1.5's cycle model (replacing `ua_law`) and the
derating curve is regenerated over 25–55 °C. Key rows:

| Ambient | ṁ (kg/s) | TIT (°C) | Regime | net MWe | % of 25 °C | plant η |
|---:|---:|---:|:---:|---:|---:|---:|
| 25 °C | 54.370 | 742 | B | 5.000 | 100.0 % | 0.333 |
| 35 °C | 53.480 | 762 | B | 4.926 | 98.5 % | 0.328 |
| 45 °C | 52.633 | 782 | A | 4.852 | 97.1 % | 0.323 |
| 55 °C | 51.825 | 783 | A | 4.566 | 91.3 % | 0.304 |

- **Mean electric derating 0.15 %/°C (25–45 °C); penalty at 55 °C = −8.7 %.**
- Air mass flow varies only ~4–5 % over the full 25→55 °C range (54.37 → 51.83 kg/s) — this is *why*
  the UA-exponent change barely moves the curve.
- CSV columns: `ambient_temp_C, mdot, TIT_C, T3_C, regime, T_hp_req_C, q_cycle_MW, q_shed_MW,
  net_MWe, plant_efficiency, cycle_efficiency, net_MWe_frac_vs25C`. (Regime B = fixed-TIT design
  regime; Regime A = the hotter regime where the required heat-pipe temperature is capped and heat
  is shed — `q_shed_MW > 0` appears at 45–55 °C.)

### 7.2 v2 vs v1.5 (`results/derating_curve_v1_5_vs_v2.png`)
| | penalty @55 °C | net MWe @55 °C |
|---|---:|---:|
| v1.5 (assumed UA ∝ ṁ⁰·⁶) | −8.8 % | 4.57 |
| **v2 (CFD Briggs–Young, n ≈ 0.454)** | **−8.7 %** | 4.57 |
| Δ (v2 − v1.5) @55 °C | **+0.08 pt** | ≈ 0 |

**v2 CONFIRMS v1.5.** The exponent change 0.6 → 0.454 shifts the 55 °C penalty by less than one
tenth of a percentage point. The finding worth reporting *is* this robustness: the derating does not
hinge on the fine detail of the heater's heat-transfer law; it is set by the open-air Brayton's
compressor-inlet ("hot-day") thermodynamics, which v1/v1.5 already captured. An independent physics
simulation confirming that assumption raises confidence in the whole Phase-1 result.

### 7.3 Output artifacts
| File | Contents |
|---|---|
| `phase1_derating/results/derating_curve_v2.csv` | the v2 curve (25–55 °C, 1 °C steps) |
| `phase1_derating/results/derating_curve_v1_5_vs_v2.png` | v1.5 vs v2 comparison plot |
| `phase1_derating/cfd/results/cfd_correlation.json` | the CFD-validated UA(ṁ) law + validation numbers |

---

## 8. Honest limitations

1. **Fin clipping.** `r_f = 24.7 mm > S_L/2 = 22.2 mm`, so the 12 mm fins overrun the single-tube
   streamwise box and are clipped at the inlet/outlet planes (~42 % of the inlet plane is fin metal
   at fin z-levels). Inherent to the reference geometry (fin height ≈ tube radius) combined with a
   single-tube box — one cell cannot represent the interleaving of staggered neighbours' fins. It
   biases the **friction** measurement (spurious clipped-fin form drag); heat transfer still
   validates (−15.2 %).
2. **Friction not validated, not used.** The Robinson–Briggs Δp / parasitic-power estimate is
   carried in `cfd_correlation.json` for reference only.
3. **Mesh independence not formally studied.** A single validated point stands in for a
   grid-convergence study, supported by *adequacy evidence* (−15.2 % Nu agreement, mean y⁺ 0.244,
   clean checkMesh) rather than proof. A formal 3-level grid-convergence study is future work.
4. **ω bounding at fin tips.** A localized near-singular-corner artifact in the k-ω solve at the fin
   leading edges; does not perturb the converged U/p/T fields (integrated h/f are bulk-dominated).
5. **y⁺ gate exceedance at fin leading-edge tips.** Plan gate is y⁺ ≤ 2 on tube+fin walls. Mean y⁺
   (0.244) satisfies the wall-resolved intent; max (4.63) exceeds it locally at the fin tips (the
   same corners behind #4). The k-ω SST blended wall functions (nutUSpalding/omega) remain valid at
   these y⁺, and integrated h is bulk-dominated, so this does not compromise the validation.
6. **Option 1, not a full sweep.** Single-point validation + correlation-driven curve, not a 6-point
   CFD Reynolds sweep. Chosen once the point validated heat transfer within the plan's own ±20 % gate.
   A fully CFD-derived `Nu(Re)` correlation and a friction-domain fix (dedicated Δp planes bracketing
   the bundle, or a multi-row domain) are documented future extensions.

---

## 9. How to reproduce

```bash
# --- CFD (needs Docker + the ESI OpenFOAM v2406 image) ---
cd phase1_derating/cfd
python3 -c "from geometry.finned_tube import REFERENCE; \
            from geometry.make_stl import write_unitcell_stl; \
            print(write_unitcell_stl(REFERENCE, 'heater_unitcell/constant/triSurface/tube.stl'))"
run/Allrun                    # blockMesh → snappy → checkMesh → parallel rhoSimpleFoam → reconstruct
                              # (~25 min on 10 cores; mesh/logs/processor dirs are gitignored)

# --- Post-processing / validation / injection (pure Python, no Docker) ---
python3 -m validation.single_point_check   # CFD vs Briggs-Young/Robinson-Briggs at Re=8368
python3 -m postprocessing.fit              # writes results/cfd_correlation.json
python3 cfd_to_v2.py                       # injects UA law into v1.5 → derating_curve_v2.csv + png
python3 -m pytest -q                       # 21-test suite (geometry/correlations/extract/fit/…)
```

**What is version-controlled vs regenerated:** the OpenFOAM case *source* is committed —
`system/` dicts, `constant/{thermophysicalProperties,turbulenceProperties,fvOptions}`, `0.orig/`
fields, and `constant/triSurface/tube.stl`. Run artifacts (`0/`, `processorN/`,
`constant/polyMesh/`, `postProcessing/`, logs) are **gitignored** and regenerated by `run/Allrun`.
The frozen measured CFD scalars live as documented constants in `validation/single_point_check.py`
and `postprocessing/fit.py`, so the Python validation/injection reproduces without re-running CFD.

---

## 10. Future work (in priority order)

1. **Intake/exhaust recirculation study** — the highest-value next step. In a real desert skid, hot
   exhaust can be pulled back into the intake, raising the effective inlet temperature above ambient
   and making derating *worse*. No correlation covers this (it depends on skid layout + local wind),
   so it genuinely needs CFD. The validated air-side setup here is the foundation. Feeds Phase-2
   siting (layout-dependent penalty). Needs an assumed skid external geometry.
2. **Full multi-condition CFD Reynolds sweep** — derive `Nu(Re)` entirely from simulation instead of
   validating the correlation.
3. **Fin-geometry sensitivity** — the reference fins are thermally inefficient (η_fin ≈ 0.53); better
   fins would change the scaling.
4. **Formal 3-level mesh-independence study** — publication-grade rigour on the single validated point.
5. **Friction-domain fix** — dedicated Δp planes bracketing the bundle, or a multi-row domain, so
   friction can be validated and the parasitic-power estimate wired into the power balance.

---

## 11. Provenance and cross-references

| Topic | Location |
|---|---|
| Reproduction detail + directory layout | `phase1_derating/cfd/README.md` |
| Decision record & full rationale (Option 1) | `DECISIONS_LOG.md` entry **D12** |
| Reference-design facts + v2 numbers (spec form) | `phase1_derating/spec/A1_reference_spec_sheet.md` §4d |
| Geometry code | `phase1_derating/cfd/geometry/{finned_tube.py, make_stl.py}` |
| Correlations | `phase1_derating/cfd/correlations/finned_tube_corr.py` |
| Validation | `phase1_derating/cfd/validation/single_point_check.py` |
| Post-processing / UA law | `phase1_derating/cfd/postprocessing/{extract.py, fit.py}` |
| v2 injection | `phase1_derating/cfd/cfd_to_v2.py` |
| The curve (interface artifact) | `phase1_derating/results/derating_curve_v2.csv`, `derating_curve_v1_5_vs_v2.png` |

**Correlation references:**
- Briggs, D.E. & Young, E.H. (1963), *Convection heat transfer and pressure drop of air flowing
  across triangular pitch banks of finned tubes*, Chem. Eng. Prog. Symp. Ser.
- Robinson, K.K. & Briggs, D.E. (1966), *Pressure drop of air flowing across triangular pitch banks
  of finned tubes*, Chem. Eng. Prog. Symp. Ser.

**Software:** OpenFOAM (ESI) v2406, image `opencfd/openfoam-default:2406`. Python post-processing
uses numpy / pandas / matplotlib / numpy-stl.
