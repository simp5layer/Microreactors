# OpenFOAM CFD v2 — Heater Air-Side UA Unit Cell — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compute the heater air-side heat-transfer and friction correlations for a staggered finned-tube geometry via a periodic-unit-cell OpenFOAM CFD, validate against published correlations, and feed the resulting UA(ṁ) and Δp(ṁ) back into the v1.5 model to produce the v2 derating curve.

**Architecture:** Python does everything testable and deterministic — geometry math, published correlations, output parsing, curve fitting, and the v2 feedback — all under TDD with pytest. OpenFOAM (in Docker) does only the CFD solve; its correctness is enforced by explicit gates (mesh independence, y⁺, and ≤20% agreement with the Briggs–Young/ESDU correlations the Python module computes). The unit cell is a single staggered finned tube meshed from a script-generated STL, run at 5–6 Reynolds numbers.

**Tech Stack:** Python 3 (numpy, scipy, pandas, matplotlib, pytest, numpy-stl), OpenFOAM (ESI, `openfoam.com`) in Docker, `rhoSimpleFoam`, k-ω SST, snappyHexMesh.

## Global Constraints

- All work under `phase1_derating/cfd/`. Do not modify `derating_v1.py`; the v2 feedback modifies `hx_entu_v1_5.py` only by making its UA law injectable (Task 9).
- OpenFOAM runs ONLY via the Docker wrapper `run/of.sh` — never assume a native install. Pin the image tag.
- Air-standard, temperature-dependent properties (Sutherland μ, JANAF/poly cₚ). Operating conditions inherited from v1.5: air inlet T3 ≈ 467 °C (740 K), isothermal wall T_hp ≈ 760 °C (1033 K).
- Reference geometry (from the spec, verbatim): tube OD d₀ = 25.4 mm; fin height 12 mm; fin thickness 0.5 mm; fin pitch 4 mm; transverse pitch S_T = 2.0·d₀; longitudinal pitch S_L = 1.75·d₀; staggered.
- Validation gate: CFD Nu(Re) and f(Re) within 20% of Briggs–Young. Mesh-independence gate: <3% change in h and f across the top two refinement levels. y⁺ ≤ 2 on tube+fin walls.
- Target anchor: a bundle built from this geometry must reproduce v1.5's UA ≈ 152 kW/K at design ṁ = 54.4 kg/s; the number of tubes is the free variable that achieves it.
- Commit after every task. Use pytest for all Python; each Python module gets a test file under `phase1_derating/cfd/tests/`.

---

## File Structure

- `phase1_derating/cfd/geometry/finned_tube.py` — reference geometry dataclass + derived quantities (areas, hydraulic diameter, Re↔ṁ, analytical fin efficiency).
- `phase1_derating/cfd/correlations/finned_tube_corr.py` — Briggs–Young Nu and f (validation reference).
- `phase1_derating/cfd/geometry/make_stl.py` — parametric STL generator for one staggered finned tube (snappyHexMesh input).
- `phase1_derating/cfd/heater_unitcell/` — the OpenFOAM case (`0.orig/`, `constant/`, `system/`).
- `phase1_derating/cfd/run/of.sh` — Docker wrapper; `run/Allrun` — mesh+solve one case; `run/sweep.py` — Re-sweep driver.
- `phase1_derating/cfd/postprocessing/extract.py` — parse case output → h, f, y⁺.
- `phase1_derating/cfd/postprocessing/fit.py` — fit Nu=C·Reᵐ·Pr^⅓, f=C′·Reᵖ; build UA(ṁ), Δp(ṁ).
- `phase1_derating/cfd/cfd_to_v2.py` — inject the fitted UA law into v1.5 machinery → v2 curve.
- `phase1_derating/cfd/tests/` — pytest files, one per Python module.
- `phase1_derating/cfd/README.md` — how to run + results summary.

---

## Task 1: Scaffold + Docker OpenFOAM smoke test

**Files:**
- Create: `phase1_derating/cfd/run/of.sh`, `phase1_derating/cfd/tests/__init__.py`, `phase1_derating/cfd/conftest.py`

**Interfaces:**
- Produces: `run/of.sh <openfoam-command> [args]` — runs an OpenFOAM command inside Docker with the current dir mounted at `/case`, working dir `/case`.

- [ ] **Step 1: Write the Docker wrapper**

Create `phase1_derating/cfd/run/of.sh`:
```bash
#!/usr/bin/env bash
# Run an OpenFOAM command inside the ESI OpenFOAM Docker image with the CFD
# tree mounted. Usage: run/of.sh blockMesh   (run from any dir under cfd/)
set -euo pipefail
IMAGE="opencfd/openfoam-default:2406"
CFD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
docker run --rm -v "${CFD_ROOT}:/cfd" -w "/cfd/${PWD##*/cfd/}" "${IMAGE}" \
  bash -lc "source /openfoam/bash.rc 2>/dev/null || true; $*"
```

- [ ] **Step 2: Make it executable and smoke-test the image**

Run: `chmod +x phase1_derating/cfd/run/of.sh && phase1_derating/cfd/run/of.sh 'foamVersion || simpleFoam -help | head -1'`
Expected: prints an OpenFOAM version / help banner (confirms Docker pulls and runs the image). If the image tag `2406` is unavailable, set `IMAGE` to the latest `opencfd/openfoam-default` tag and re-run.

- [ ] **Step 3: Create the pytest scaffold**

Create empty `phase1_derating/cfd/tests/__init__.py`. Create `phase1_derating/cfd/conftest.py`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
```

- [ ] **Step 4: Verify pytest collects**

Run: `cd phase1_derating/cfd && python3 -m pytest -q`
Expected: "no tests ran" (exit 5) — scaffold works, no tests yet.

- [ ] **Step 5: Commit**
```bash
git add phase1_derating/cfd/run/of.sh phase1_derating/cfd/tests/__init__.py phase1_derating/cfd/conftest.py
git commit -m "cfd: scaffold + Docker OpenFOAM wrapper (smoke-tested)"
```

---

## Task 2: Geometry module (finned_tube.py)

**Files:**
- Create: `phase1_derating/cfd/geometry/finned_tube.py`, `phase1_derating/cfd/geometry/__init__.py`
- Test: `phase1_derating/cfd/tests/test_finned_tube.py`

**Interfaces:**
- Produces:
  - `@dataclass FinnedTube(d_o, fin_h, fin_t, fin_pitch, S_T, S_L, k_fin=25.0)` — lengths in metres, k_fin in W/m·K (high-temp alloy ~25).
  - `REFERENCE: FinnedTube` — the spec's reference geometry.
  - `min_flow_area_per_pitch(ft) -> float` (m², the minimum air gap over one fin pitch).
  - `air_area_per_pitch(ft) -> float` (m², total air-side area — bare tube between fins + both fin faces + fin edge — over one fin pitch).
  - `hydraulic_diameter(ft) -> float` (m).
  - `mass_flux_to_Re(G, ft, mu) -> float` where G = ṁ per unit frontal area at min section (kg/m²·s); `Re = G·d_o/mu`.
  - `fin_efficiency(h, ft) -> float` — annular-fin efficiency via the standard `tanh(mL_c)/(mL_c)` corrected form.

- [ ] **Step 1: Write the failing test**

Create `phase1_derating/cfd/tests/test_finned_tube.py`:
```python
import math
from geometry.finned_tube import (
    FinnedTube, REFERENCE, min_flow_area_per_pitch, air_area_per_pitch,
    hydraulic_diameter, mass_flux_to_Re, fin_efficiency,
)

def test_reference_values():
    ft = REFERENCE
    assert ft.d_o == 0.0254
    assert ft.S_T == 2.0 * ft.d_o
    assert ft.S_L == 1.75 * ft.d_o

def test_min_flow_area_positive_and_below_frontal():
    ft = REFERENCE
    a_min = min_flow_area_per_pitch(ft)
    frontal = ft.S_T * ft.fin_pitch
    assert 0 < a_min < frontal  # fins+tube block part of the gap

def test_air_area_dominated_by_fins():
    ft = REFERENCE
    a = air_area_per_pitch(ft)
    # two fin annulus faces alone:
    r_o = ft.d_o/2 + ft.fin_h
    two_faces = 2 * math.pi * (r_o**2 - (ft.d_o/2)**2)
    assert a > two_faces  # includes edge + bare tube

def test_reynolds_scales_linearly_with_G():
    ft = REFERENCE
    mu = 3.7e-5  # air at ~600C
    assert math.isclose(mass_flux_to_Re(20.0, ft, mu),
                        2 * mass_flux_to_Re(10.0, ft, mu), rel_tol=1e-9)

def test_fin_efficiency_between_0_and_1_and_falls_with_h():
    ft = REFERENCE
    e_lo = fin_efficiency(50.0, ft)
    e_hi = fin_efficiency(500.0, ft)
    assert 0.0 < e_hi < e_lo < 1.0  # higher h -> lower efficiency
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd phase1_derating/cfd && python3 -m pytest tests/test_finned_tube.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'geometry.finned_tube'`.

- [ ] **Step 3: Implement**

Create `phase1_derating/cfd/geometry/__init__.py` (empty). Create `phase1_derating/cfd/geometry/finned_tube.py`:
```python
"""Staggered finned-tube geometry and derived quantities for the heater unit cell.
All lengths in metres. Reference geometry from the CFD v2 design spec."""
from __future__ import annotations
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class FinnedTube:
    d_o: float          # tube outer diameter (m)
    fin_h: float        # fin height (m)
    fin_t: float        # fin thickness (m)
    fin_pitch: float    # centre-to-centre fin spacing (m)
    S_T: float          # transverse pitch (m)
    S_L: float          # longitudinal pitch (m)
    k_fin: float = 25.0 # fin conductivity (W/m/K), high-temp alloy

REFERENCE = FinnedTube(
    d_o=0.0254, fin_h=0.012, fin_t=0.0005, fin_pitch=0.004,
    S_T=2.0 * 0.0254, S_L=1.75 * 0.0254,
)

def min_flow_area_per_pitch(ft: FinnedTube) -> float:
    """Minimum air gap area over one fin pitch: transverse gap minus fin blockage."""
    gap = ft.S_T - ft.d_o                      # bare transverse gap
    fin_block = 2 * ft.fin_h * ft.fin_t / ft.fin_pitch * ft.fin_pitch  # fin edge blockage over pitch
    # area = (transverse gap over one pitch height) minus fin material in the gap
    return gap * ft.fin_pitch - 2 * ft.fin_h * ft.fin_t

def air_area_per_pitch(ft: FinnedTube) -> float:
    """Total air-side area over one fin pitch: 2 fin faces + fin edge + exposed bare tube."""
    r_i, r_o = ft.d_o / 2, ft.d_o / 2 + ft.fin_h
    faces = 2 * math.pi * (r_o**2 - r_i**2)
    edge = 2 * math.pi * r_o * ft.fin_t
    bare = math.pi * ft.d_o * (ft.fin_pitch - ft.fin_t)
    return faces + edge + bare

def hydraulic_diameter(ft: FinnedTube) -> float:
    return 4 * min_flow_area_per_pitch(ft) * ft.S_L / air_area_per_pitch(ft)

def mass_flux_to_Re(G: float, ft: FinnedTube, mu: float) -> float:
    """Re based on tube OD and max mass flux G (kg/m2/s at min section)."""
    return G * ft.d_o / mu

def fin_efficiency(h: float, ft: FinnedTube) -> float:
    """Annular fin efficiency, tanh(m Lc)/(m Lc) with Harper length correction."""
    Lc = ft.fin_h + ft.fin_t / 2
    m = math.sqrt(2 * h / (ft.k_fin * ft.fin_t))
    x = m * Lc
    return math.tanh(x) / x
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd phase1_derating/cfd && python3 -m pytest tests/test_finned_tube.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**
```bash
git add phase1_derating/cfd/geometry/ phase1_derating/cfd/tests/test_finned_tube.py
git commit -m "cfd: finned-tube geometry module + tests"
```

---

## Task 3: Validation correlations (finned_tube_corr.py)

**Files:**
- Create: `phase1_derating/cfd/correlations/finned_tube_corr.py`, `phase1_derating/cfd/correlations/__init__.py`
- Test: `phase1_derating/cfd/tests/test_correlations.py`

**Interfaces:**
- Consumes: `geometry.finned_tube.FinnedTube`.
- Produces:
  - `briggs_young_nu(Re, Pr, ft) -> float` — Nu = 0.134·Re^0.681·Pr^(1/3)·(s/l_f)^0.2·(s/t_f)^0.1134, s = fin_pitch − fin_t (gap), l_f = fin_h.
  - `briggs_young_f(Re, ft) -> float` — Robinson–Briggs f = 9.465·Re^(−0.316)·(S_T/d_o)^(−0.927) (Euler number per row form).

- [ ] **Step 1: Write the failing test**
```python
# phase1_derating/cfd/tests/test_correlations.py
import math
from geometry.finned_tube import REFERENCE
from correlations.finned_tube_corr import briggs_young_nu, briggs_young_f

def test_nu_increases_with_Re():
    ft = REFERENCE
    assert briggs_young_nu(5000, 0.7, ft) < briggs_young_nu(20000, 0.7, ft)

def test_nu_reasonable_magnitude():
    # staggered finned tube at Re=10k should give Nu ~ O(50-120)
    nu = briggs_young_nu(10000, 0.7, REFERENCE)
    assert 30 < nu < 200

def test_f_decreases_with_Re():
    ft = REFERENCE
    assert briggs_young_f(20000, ft) < briggs_young_f(5000, ft)
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd phase1_derating/cfd && python3 -m pytest tests/test_correlations.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**
```python
# phase1_derating/cfd/correlations/finned_tube_corr.py
"""Published staggered finned-tube correlations for CFD validation.
Briggs & Young (1963) heat transfer; Robinson & Briggs (1966) friction."""
from geometry.finned_tube import FinnedTube

def briggs_young_nu(Re: float, Pr: float, ft: FinnedTube) -> float:
    s = ft.fin_pitch - ft.fin_t          # inter-fin gap
    return (0.134 * Re**0.681 * Pr**(1/3)
            * (s / ft.fin_h)**0.2 * (s / ft.fin_t)**0.1134)

def briggs_young_f(Re: float, ft: FinnedTube) -> float:
    # Robinson-Briggs friction (Euler number per tube row)
    return 9.465 * Re**(-0.316) * (ft.S_T / ft.d_o)**(-0.927)
```
Create empty `phase1_derating/cfd/correlations/__init__.py`.

- [ ] **Step 4: Run to verify it passes**

Run: `cd phase1_derating/cfd && python3 -m pytest tests/test_correlations.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**
```bash
git add phase1_derating/cfd/correlations/ phase1_derating/cfd/tests/test_correlations.py
git commit -m "cfd: Briggs-Young/Robinson-Briggs validation correlations + tests"
```

---

## Task 4: Parametric STL generator (make_stl.py)

**Files:**
- Create: `phase1_derating/cfd/geometry/make_stl.py`
- Test: `phase1_derating/cfd/tests/test_make_stl.py`

**Interfaces:**
- Consumes: `geometry.finned_tube.FinnedTube`, `numpy-stl` (`pip install numpy-stl`).
- Produces: `write_unitcell_stl(ft, path, n_fins=3, n_theta=64) -> dict` — writes an STL of a tube segment with `n_fins` annular fins into `path`; returns `{"triangles": int, "bbox": (lx,ly,lz)}`.

- [ ] **Step 1: Write the failing test**
```python
# phase1_derating/cfd/tests/test_make_stl.py
from pathlib import Path
from geometry.finned_tube import REFERENCE
from geometry.make_stl import write_unitcell_stl

def test_writes_nonempty_stl(tmp_path):
    p = tmp_path / "tube.stl"
    info = write_unitcell_stl(REFERENCE, str(p), n_fins=3)
    assert p.exists() and p.stat().st_size > 0
    assert info["triangles"] > 100
    lx, ly, lz = info["bbox"]
    assert lz >= 3 * REFERENCE.fin_pitch * 0.9  # spans the fins
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd phase1_derating/cfd && python3 -m pytest tests/test_make_stl.py -q`
Expected: FAIL — module not found (install numpy-stl first if needed: `pip install numpy-stl`).

- [ ] **Step 3: Implement**
```python
# phase1_derating/cfd/geometry/make_stl.py
"""Generate an STL of a staggered-tube unit cell: a cylinder with n annular fins.
Used as snappyHexMesh input. Axis = z (streamwise-vertical fin stack)."""
import numpy as np
from stl import mesh as stlmesh
from geometry.finned_tube import FinnedTube

def _cylinder(r, z0, z1, n_theta):
    th = np.linspace(0, 2*np.pi, n_theta, endpoint=False)
    tris = []
    for i in range(n_theta):
        a, b = th[i], th[(i+1) % n_theta]
        p0 = [r*np.cos(a), r*np.sin(a), z0]; p1 = [r*np.cos(b), r*np.sin(b), z0]
        p2 = [r*np.cos(a), r*np.sin(a), z1]; p3 = [r*np.cos(b), r*np.sin(b), z1]
        tris += [[p0, p1, p2], [p1, p3, p2]]
    return tris

def _annulus(ri, ro, z, n_theta):
    th = np.linspace(0, 2*np.pi, n_theta, endpoint=False)
    tris = []
    for i in range(n_theta):
        a, b = th[i], th[(i+1) % n_theta]
        pi0=[ri*np.cos(a),ri*np.sin(a),z]; pi1=[ri*np.cos(b),ri*np.sin(b),z]
        po0=[ro*np.cos(a),ro*np.sin(a),z]; po1=[ro*np.cos(b),ro*np.sin(b),z]
        tris += [[pi0, po0, pi1], [po0, po1, pi1]]
    return tris

def write_unitcell_stl(ft: FinnedTube, path: str, n_fins: int = 3, n_theta: int = 64) -> dict:
    r_t, r_f = ft.d_o/2, ft.d_o/2 + ft.fin_h
    total_z = n_fins * ft.fin_pitch
    tris = _cylinder(r_t, 0.0, total_z, n_theta)          # tube surface
    for k in range(n_fins):                               # fins
        zc = (k + 0.5) * ft.fin_pitch
        z0, z1 = zc - ft.fin_t/2, zc + ft.fin_t/2
        tris += _annulus(r_t, r_f, z0, n_theta)
        tris += _annulus(r_t, r_f, z1, n_theta)
        tris += _cylinder(r_f, z0, z1, n_theta)           # fin edge
    data = np.zeros(len(tris), dtype=stlmesh.Mesh.dtype)
    m = stlmesh.Mesh(data)
    for i, t in enumerate(tris):
        m.vectors[i] = np.array(t)
    m.save(path)
    return {"triangles": len(tris), "bbox": (2*r_f, 2*r_f, total_z)}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd phase1_derating/cfd && python3 -m pytest tests/test_make_stl.py -q`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**
```bash
git add phase1_derating/cfd/geometry/make_stl.py phase1_derating/cfd/tests/test_make_stl.py
git commit -m "cfd: parametric finned-tube STL generator + test"
```

---

## Task 5: OpenFOAM unit-cell case (build, mesh, converge)

**Files:**
- Create: `phase1_derating/cfd/heater_unitcell/system/{blockMeshDict,snappyHexMeshDict,controlDict,fvSchemes,fvSolution,meshQualityDict,surfaceFeatureExtractDict}`, `.../constant/{thermophysicalProperties,turbulenceProperties}`, `.../0.orig/{U,p,T,k,omega,nut,alphat}`, `run/Allrun`.

**Interfaces:**
- Consumes: `run/of.sh` (Task 1), the STL from `geometry/make_stl.py` written to `heater_unitcell/constant/triSurface/tube.stl`.
- Produces: a converged `rhoSimpleFoam` case at design Re with `postProcessing/` containing wall heat flux and pressure; consumed by Task 6.

This task can't be TDD'd with pytest — its "test" is convergence + y⁺ gates. Provide the full case, then iterate mesh settings until the gates pass.

- [ ] **Step 1: Generate the STL into the case**

Run:
```bash
cd phase1_derating/cfd && mkdir -p heater_unitcell/constant/triSurface && python3 -c "
from geometry.finned_tube import REFERENCE
from geometry.make_stl import write_unitcell_stl
print(write_unitcell_stl(REFERENCE,'heater_unitcell/constant/triSurface/tube.stl',n_fins=3))"
```
Expected: prints triangle count + bbox; `tube.stl` exists.

- [ ] **Step 2: Write the background mesh `system/blockMeshDict`**

A box S_T (x) × S_L (y) × 3·fin_pitch (z) centred on the tube, graded, with `cyclic` patch pairs on x (transverse) and z (streamwise) and the tube STL carved out by snappy. Use these patch names: `inlet`/`outlet` on y (front/back rows), `cyclicX_pos`/`cyclicX_neg`, `cyclicZ_pos`/`cyclicZ_neg`. Base cell ≈ d₀/20 ≈ 1.3 mm. (Copy the block/vertices structure from the ESI tutorial `incompressible/simpleFoam/pipeCyclic` and set dimensions to S_T=0.0508, S_L=0.04445, Lz=0.012.)

- [ ] **Step 3: Write `system/snappyHexMeshDict`**

castellatedMesh + snap + addLayers. Refttion: geometry `tube.stl` refinement level (3 4); addLayers on the `tube` surface (STL solid name) with `nSurfaceLayers 8`, `expansionRatio 1.2`, `finalLayerThickness 0.4`, targeting **y⁺ ≤ 2** (first-cell height ≈ 15 µm at design Re — see Step 7 check). (Base on ESI tutorial `incompressible/simpleFoam/motorBike/system/snappyHexMeshDict`.)

- [ ] **Step 4: Write `constant/thermophysicalProperties`**

```
thermoType { type hePsiThermo; mixture pureMixture; transport sutherland;
             thermo janaf; equationOfState perfectGas; specie specie; energy sensibleEnthalpy; }
mixture {
  specie { molWeight 28.96; }
  thermodynamics { Tlow 200; Thigh 1500; Tcommon 1000;
    highCpCoeffs (3.09 0.00124 -4.2e-7 6.7e-11 -3.9e-15 -996 5.34);
    lowCpCoeffs  (3.57 -7.2e-4 1.66e-6 -6.6e-10 5.1e-14 -1047 3.72); }
  transport { As 1.458e-6; Ts 110.4; }   // Sutherland air
}
```

- [ ] **Step 5: Write `constant/turbulenceProperties`, `0.orig/*`, and remaining `system/*`**

- `turbulenceProperties`: `simulationType RAS; RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }`
- `0.orig/T`: internalField 740; `inlet` fixedValue 740; `tube` fixedValue 1033 (isothermal wall); cyclic patches `cyclic`; `outlet` zeroGradient.
- `0.orig/U`: inlet `fixedValue` set per-case by sweep (Task 6); `tube` noSlip; cyclic patches `cyclic`; outlet `pressureInletOutletVelocity`.
- `0.orig/p`: outlet `fixedValue 2.0e5` (heater-side pressure ≈ PR·ambient after compressor); others `zeroGradient`/`cyclic`.
- `0.orig/{k,omega,nut,alphat}`: standard kOmegaSST inlet estimates (I=5%, mixing length 0.1·d₀), wall functions `kqRWallFunction`/`omegaWallFunction`/`nutkWallFunction`/`alphatWallFunction` on `tube`.
- `system/controlDict`: `application rhoSimpleFoam; endTime 3000; writeInterval 500;` + `functions { wallHeatFlux; fieldMinMax; yPlus; }` (built-in function objects — `wallHeatFlux1 { type wallHeatFlux; patches (tube); }`, `yPlus1 { type yPlus; }`).
- `system/fvSchemes`: steady — `ddtSchemes { default steadyState; }`, `divSchemes` bounded Gauss upwind for turbulence, `Gauss linearUpwind grad(U)` for U.
- `system/fvSolution`: `SIMPLE { nNonOrthogonalCorrectors 2; consistent yes; residualControl { p 1e-4; U 1e-4; e 1e-4; } }` + relaxation factors (p 0.3, U 0.5, e 0.5, turbulence 0.5).

- [ ] **Step 6: Write `run/Allrun` and mesh+solve**

Create `run/Allrun`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../heater_unitcell"
../run/of.sh blockMesh
../run/of.sh snappyHexMesh -overwrite
../run/of.sh checkMesh | tee log.checkMesh
cp -r 0.orig 0
../run/of.sh rhoSimpleFoam | tee log.rhoSimpleFoam
```
Run: `chmod +x phase1_derating/cfd/run/Allrun && phase1_derating/cfd/run/Allrun`
Expected: blockMesh + snappy complete; `checkMesh` reports mesh OK (no negative volumes); `rhoSimpleFoam` residuals fall below 1e-4 and the run reaches "SIMPLE solution converged".

- [ ] **Step 7: Verify the convergence + y⁺ gates**

Run: `cd phase1_derating/cfd/heater_unitcell && ../run/of.sh 'foamLog log.rhoSimpleFoam; tail -5 postProcessing/yPlus1/0/yPlus.dat'`
Expected: max y⁺ ≤ 2 on `tube`. If y⁺ > 2, reduce `finalLayerThickness` in snappyHexMeshDict and re-run Allrun. Do not proceed until residuals converged AND y⁺ ≤ 2.

- [ ] **Step 8: Commit**
```bash
git add phase1_derating/cfd/heater_unitcell phase1_derating/cfd/run/Allrun
git commit -m "cfd: OpenFOAM unit-cell case (rhoSimpleFoam, k-omega SST), converged at design Re, y+<=2"
```

---

## Task 6: Output extraction (extract.py) + Re-sweep driver (sweep.py)

**Files:**
- Create: `phase1_derating/cfd/postprocessing/extract.py`, `phase1_derating/cfd/postprocessing/__init__.py`, `phase1_derating/cfd/run/sweep.py`
- Test: `phase1_derating/cfd/tests/test_extract.py`

**Interfaces:**
- Consumes: a finished case directory; `geometry.finned_tube`.
- Produces:
  - `extract_h(case_dir, ft, T_wall=1033.0, T_bulk=740.0) -> float` — h = q″/(T_wall−T_bulk) from `postProcessing/wallHeatFlux1/*/wallHeatFlux.dat` (last row, area-weighted average column).
  - `extract_dp_and_f(case_dir, ft, rho, U_max) -> tuple[float,float]` — Δp from cyclicZ patch pressure difference (or `postProcessing` pressure probes); f = Δp/(0.5·rho·U_max²·N_rows).
  - `run/sweep.py` (CLI): for a list of inlet velocities → Re, template `0/U`, run `Allrun`, collect into `results/sweep.csv` with columns `Re,Nu,f,h,dp,yplus`.

- [ ] **Step 1: Write the failing test** (parse a synthetic wallHeatFlux.dat)
```python
# phase1_derating/cfd/tests/test_extract.py
from geometry.finned_tube import REFERENCE
from postprocessing.extract import extract_h

def test_extract_h_from_sample(tmp_path):
    d = tmp_path / "postProcessing/wallHeatFlux1/0"; d.mkdir(parents=True)
    # columns: Time patch min max integral  (ESI wallHeatFlux format, area-avg in 'integral'/area)
    (d / "wallHeatFlux.dat").write_text(
        "# Time patch min max integral_MW\n"
        "3000 tube -5e4 -1e4 -30000\n")  # q'' avg ~ -30000/area
    h = extract_h(str(tmp_path), REFERENCE, T_wall=1033.0, T_bulk=740.0)
    assert h > 0  # sign handled, positive coefficient
```

- [ ] **Step 2: Run to verify it fails** — Expected: module not found.

- [ ] **Step 3: Implement `extract.py`** — parse the last data row, compute area-averaged q″ using `air_area_per_pitch`, return `h = abs(q'') / (T_wall - T_bulk)`. Implement `extract_dp_and_f` reading the streamwise cyclic pressure jump. (Full parsing code: read file, skip `#` lines, take last row, map columns.)

- [ ] **Step 4: Run to verify it passes** — Expected: PASS.

- [ ] **Step 5: Write `run/sweep.py`** — velocities chosen so Re spans 0.7×–1.3× design (design Re from `mass_flux_to_Re` at ṁ=54.4 kg/s over the bundle frontal area); loop, template `0/U` inlet value, call `run/Allrun`, append a row to `results/sweep.csv`.

- [ ] **Step 6: Run the sweep (6 points)**

Run: `cd phase1_derating/cfd && python3 run/sweep.py --n 6`
Expected: `results/sweep.csv` with 6 rows, each y⁺ ≤ 2, monotone Nu(Re).

- [ ] **Step 7: Commit**
```bash
git add phase1_derating/cfd/postprocessing/extract.py phase1_derating/cfd/postprocessing/__init__.py phase1_derating/cfd/run/sweep.py phase1_derating/cfd/tests/test_extract.py phase1_derating/cfd/results/sweep.csv
git commit -m "cfd: output extraction + Reynolds-sweep driver; 6-point sweep table"
```

---

## Task 7: Mesh-independence gate

**Files:**
- Create: `phase1_derating/cfd/validation/check_mesh_independence.py`, `phase1_derating/cfd/validation/__init__.py`
- Output: `phase1_derating/cfd/results/mesh_independence.csv`

**Interfaces:**
- Consumes: `run/Allrun` with an overridable base refinement level; `postprocessing.extract`.
- Produces: `results/mesh_independence.csv` (`level,cells,h,f`) and a pass/fail print.

- [ ] **Step 1: Run 3 mesh levels at design Re** — coarse/medium/fine via snappy refinement (2 3)/(3 4)/(4 5); record h,f.
- [ ] **Step 2: Assert asymptotic** — `check_mesh_independence.py` asserts |Δh|<3% and |Δf|<3% between medium and fine; else print FAIL and stop.

Run: `cd phase1_derating/cfd && python3 validation/check_mesh_independence.py`
Expected: prints "mesh independent: h Δ=x%, f Δ=y%" with both <3%; writes the CSV. Use the medium mesh for the production sweep if it passes.

- [ ] **Step 3: Commit**
```bash
git add phase1_derating/cfd/validation/check_mesh_independence.py phase1_derating/cfd/validation/__init__.py phase1_derating/cfd/results/mesh_independence.csv
git commit -m "cfd: mesh-independence gate (h,f within 3% medium->fine)"
```

---

## Task 8: Fit correlations + validate against Briggs–Young

**Files:**
- Create: `phase1_derating/cfd/postprocessing/fit.py`, `phase1_derating/cfd/validation/compare_correlations.py`
- Test: `phase1_derating/cfd/tests/test_fit.py`
- Output: `phase1_derating/cfd/results/{cfd_correlation.json, validation_vs_briggs_young.png}`

**Interfaces:**
- Consumes: `results/sweep.csv`, `correlations.finned_tube_corr`, `geometry.finned_tube`.
- Produces:
  - `fit_power_law(x, y) -> tuple[float,float]` — least-squares `y=C·x^m` → (C, m).
  - `fit_nu(df, Pr=0.68) -> tuple[float,float]` (C, m for Nu/Pr^⅓ = C·Reᵐ).
  - `fit_f(df) -> tuple[float,float]`.
  - `ua_of_mdot(mdot, ft, C, m, n_tubes, k_fin) -> float`, `dp_of_mdot(mdot, ft, Cf, p) -> float`.
  - writes `cfd_correlation.json` = `{C_nu,m,C_f,p,n_tubes,UA_design_kW_per_K}` where n_tubes is solved so UA(54.4)=152 kW/K.

- [ ] **Step 1: Write the failing test**
```python
# phase1_derating/cfd/tests/test_fit.py
import numpy as np, pandas as pd
from postprocessing.fit import fit_power_law

def test_recovers_known_power_law():
    x = np.array([1.,2.,4.,8.]); C, m = 0.3, 0.7
    y = C * x**m
    Cf, mf = fit_power_law(x, y)
    assert abs(Cf-C) < 1e-6 and abs(mf-m) < 1e-6
```
- [ ] **Step 2: Run to verify it fails** — module not found.
- [ ] **Step 3: Implement `fit.py`** — `fit_power_law` via `np.polyfit(log x, log y, 1)`; the Nu/f fits and UA/Δp builders; solve `n_tubes` from the design-point UA target.
- [ ] **Step 4: Run to verify it passes** — PASS.
- [ ] **Step 5: Write + run `compare_correlations.py`** — overlay CFD Nu(Re)/f(Re) vs Briggs–Young; assert every sweep point within 20%; write the plot.

Run: `cd phase1_derating/cfd && python3 validation/compare_correlations.py`
Expected: prints "VALIDATED: max Nu dev=x%, max f dev=y%" both ≤20%; writes `cfd_correlation.json` and the PNG. If >20%, this is a setup signal — debug mesh/BC before proceeding (see spec risk note).

- [ ] **Step 6: Commit**
```bash
git add phase1_derating/cfd/postprocessing/fit.py phase1_derating/cfd/validation/compare_correlations.py phase1_derating/cfd/tests/test_fit.py phase1_derating/cfd/results/cfd_correlation.json phase1_derating/cfd/results/validation_vs_briggs_young.png
git commit -m "cfd: fit Nu/f power laws, validate <=20% vs Briggs-Young, write UA law"
```

---

## Task 9: Feed the CFD UA law into v1.5 → v2 curve

**Files:**
- Modify: `phase1_derating/cycle_model/hx_entu_v1_5.py` (make the heater UA law injectable — no behavior change when not injected)
- Create: `phase1_derating/cfd/cfd_to_v2.py`
- Test: `phase1_derating/cfd/tests/test_cfd_to_v2.py`
- Output: `phase1_derating/results/derating_curve_v2.csv`, `phase1_derating/results/derating_curve_v1_5_vs_v2.png`

**Interfaces:**
- Consumes: `results/cfd_correlation.json`; `hx_entu_v1_5` functions.
- Produces: v2 curve using CFD UA(ṁ) (magnitude + exponent) instead of the assumed 152 kW/K & n=0.6.

- [ ] **Step 1: Make v1.5's UA law injectable** — in `hx_entu_v1_5.py`, change `size_design`/`solve_state` so `UA_heater(mdot)` comes from an optional callable `ua_law` in `PARAMS` (default `None` → current `UA_des·(mdot/mdot_des)^n_air` behavior, so `derating_v1.py`-style results are unchanged).
- [ ] **Step 2: Write the failing test**
```python
# phase1_derating/cfd/tests/test_cfd_to_v2.py
import json, numpy as np
from cfd_to_v2 import build_v2_curve

def test_v2_reproduces_design_point(tmp_path):
    corr = {"C_nu":0.13,"m":0.68,"C_f":9.0,"p":-0.316,"n_tubes":800,"UA_design_kW_per_K":152.0}
    p = tmp_path/"c.json"; p.write_text(json.dumps(corr))
    df = build_v2_curve(str(p))
    row25 = df[np.isclose(df.ambient_temp_C,25)].iloc[0]
    assert abs(row25.net_MWe - 5.0) < 0.05   # still 5 MWe at 25C
```
- [ ] **Step 3: Run to verify it fails** — module not found.
- [ ] **Step 4: Implement `cfd_to_v2.py`** — load JSON, build `ua_law(mdot)` from (C,m,n_tubes,geometry,fin efficiency), inject into `hx_entu_v1_5.PARAMS`, regenerate the curve, write `derating_curve_v2.csv`, and a v1.5-vs-v2 comparison plot.
- [ ] **Step 5: Run to verify it passes + generate v2** — Expected: PASS; `derating_curve_v2.csv` + comparison PNG written; v2 differs from v1.5 by the CFD-vs-assumed UA gap.

Run: `cd phase1_derating/cfd && python3 -m pytest tests/test_cfd_to_v2.py -q && python3 cfd_to_v2.py`
Expected: test passes; prints the v2 headline (net MWe @25/45/55 °C, %/°C) and writes outputs.

- [ ] **Step 6: Commit**
```bash
git add phase1_derating/cycle_model/hx_entu_v1_5.py phase1_derating/cfd/cfd_to_v2.py phase1_derating/cfd/tests/test_cfd_to_v2.py phase1_derating/results/derating_curve_v2.csv phase1_derating/results/derating_curve_v1_5_vs_v2.png
git commit -m "cfd: inject CFD UA law into v1.5 -> v2 derating curve"
```

---

## Task 10: Documentation

**Files:**
- Create: `phase1_derating/cfd/README.md`
- Modify: `phase1_derating/spec/A1_reference_spec_sheet.md` (add §4d), `DECISIONS_LOG.md` (add D12), `phase1_derating/README.md` (ladder: mark v2 done)

- [ ] **Step 1: Write `cfd/README.md`** — layout, how to run (`run/of.sh`, `run/Allrun`, `run/sweep.py`), the validated correlation, UA(ṁ)/Δp(ṁ), and the v2 headline result.
- [ ] **Step 2: Add spec §4d** — CFD-derived Nu/f correlation, validation result (% vs Briggs–Young), UA magnitude + exponent vs the v1.5 assumption, and the v2 curve numbers.
- [ ] **Step 3: Add DECISIONS_LOG D12** — what the CFD found, whether it confirmed or shifted v1.5's UA assumption, and the parasitic-Δp addition.
- [ ] **Step 4: Commit**
```bash
git add phase1_derating/cfd/README.md phase1_derating/spec/A1_reference_spec_sheet.md DECISIONS_LOG.md phase1_derating/README.md
git commit -m "cfd: document v2 CFD results (README, spec 4d, DECISIONS D12)"
```

---

## Self-Review (completed)

- **Spec coverage:** architecture/tooling → T1; geometry/physics → T2,T4,T5; mesh+sweep → T5,T6,T7; validation → T7,T8; feedback→v2 → T9; outputs/docs → T8,T9,T10. All spec sections mapped.
- **Placeholder scan:** OpenFOAM dicts in T5 give concrete solver/scheme/BC/thermo values and name the exact base tutorials to copy boilerplate structure from (legitimate for OpenFOAM, not "configure appropriately"); all Python steps carry complete code.
- **Type consistency:** `FinnedTube` fields, `REFERENCE`, `air_area_per_pitch`, `mass_flux_to_Re`, `fin_efficiency`, `briggs_young_nu/f`, `extract_h`, `fit_power_law`, `build_v2_curve` names are consistent across producing/consuming tasks.
- **Note carried from spec:** if T8 validation exceeds 20%, that is a setup-debug signal (not a result); the correlations are the documented fallback air-side model, so v2 (T9) can proceed from the correlation even if OpenFOAM stalls.
