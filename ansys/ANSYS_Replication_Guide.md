---
title: "Replicating the Finned-Tube Heater CFD in ANSYS Fluent"
subtitle: "Air-side heat-transfer validation of an eVinci-class heat-pipe reactor heater — porting the OpenFOAM v2 case to ANSYS"
author: "Combined Microreactor Project | Phase 1 Derating | CFD replication guide"
date: "For an ANSYS licence supporting ~80 M cells"
---

# 1. Purpose and scope

This guide contains everything needed to reproduce, in **ANSYS Fluent**, the air-side heat-transfer validation
that was originally performed in OpenFOAM (`rhoSimpleFoam`, $k$–$\omega$ SST). The simulated object is a single
**finned-tube unit cell** of the reactor heater: cross-flow air being heated by a hot, isothermal (condensing-sodium
heat-pipe) tube wall. The deliverable of the CFD is one dimensionless number — the **Nusselt number** — validated
against a published finned-tube correlation.

**Target to reproduce:** $Nu \approx 45.9$ at $Re = 8368$, within $\pm20\%$ of the Briggs–Young correlation
($Nu_{BY}=54.1$, i.e. a deviation of $-15.2\%$). Reaching this certifies the air-side heat-transfer model.

**What the ~80 M-cell licence unlocks (beyond the original single-cell, single-point scope):** a formal
grid-convergence study, a full multi-row staggered bank (removing the fin-clipping limitation), conjugate heat
transfer in the fins, and a multi-point Reynolds sweep. These optional extensions are in §11.

# 2. Reference results to match

All values below are measured or derived from the converged OpenFOAM solution and are the acceptance targets for the
ANSYS run.

| Quantity | Symbol | Value | Notes |
|---|---|---|---|
| Wall heat rate (tube patch) | $Q$ | 256.3 W | surface integral of wall heat flux |
| Inlet–outlet pressure drop | $\Delta p$ | 148.4 Pa | area-averaged |
| Air outlet temperature | $T_{out}$ | 808.6 K | mass-weighted |
| Log-mean temperature diff. | $\Delta T_{lm}$ | 257.1 K | driving $\Delta T$ (see §8) |
| Heat-transfer coefficient | $h$ | ~110 W m⁻² K⁻¹ | $q''/\Delta T_{lm}$ |
| **Nusselt number** | $Nu$ | **45.9** | $h\,d_o/k$; **the headline** |
| Reynolds number | $Re$ | 8368 | min-flow mass flux, tube OD |
| Friction factor | $f$ | 1.69 | informational only (see §9) |
| Near-wall resolution | $y^+$ | mean 0.24 / max 4.6 | tube+fin walls |
| Mesh size (original) | — | 3.29 M cells | baseline; refine with 80 M budget |

# 3. Geometry

## 3.1 Reference finned tube (staggered bank)

| Parameter | Symbol | Value |
|---|---|---|
| Tube outer diameter | $d_o$ | 25.4 mm (= 1 in) |
| Fin height | — | 12.0 mm |
| Fin thickness | $t$ | 0.5 mm |
| Fin pitch (centre-to-centre) | $p_f$ | 4.0 mm |
| Inter-fin gap | $s = p_f - t$ | 3.5 mm |
| Transverse pitch | $S_T = 2.0\,d_o$ | 50.8 mm |
| Longitudinal pitch | $S_L = 1.75\,d_o$ | 44.45 mm |
| Fin material conductivity | $k_{fin}$ | 25 W m⁻¹ K⁻¹ (high-temp alloy) |

> **Provenance note.** The eVinci heat-exchanger geometry is not public; these are representative standard
> finned-tube values (1-inch tube, conventional pitch ratios). See references [8, 9].

## 3.2 Computational domain (the "unit cell")

One tube, spanning **three fin pitches** along its axis, with periodic/symmetry planes standing in for the infinite
bank. Axis convention:

| Axis | Extent | Physical meaning | Boundary type |
|---|---|---|---|
| $x$ (transverse) | $\pm S_T/2 = \pm25.4$ mm | tube-to-tube | translational **periodic** |
| $y$ (streamwise) | $\pm S_L/2 = \pm22.225$ mm | flow direction | **inlet** / **outlet** |
| $z$ (tube axis, spanwise) | $0 \to 12$ mm ($3 p_f$) | along the tube | **symmetry** (mid-fin-gap planes) |

The fluid domain is the box **minus** the solid tube-plus-fins. Tube axis lies along $z$ at $(x,y)=(0,0)$; fins sit
at $z = 2, 6, 10$ mm so the $z=0$ and $z=12$ mm faces fall on symmetry planes.

## 3.3 Build options in ANSYS

- **SpaceClaim / DesignModeler:** create the box, create the finned tube (cylinder + three annular fin discs),
  Boolean-subtract the solid from the box to get the fluid domain. Name the faces (`inlet`, `outlet`, `tube`,
  `periodic_x_pos/neg`, `sym_z_pos/neg`).
- **Or import the existing STL:** `phase1_derating/cfd/heater_unitcell/constant/triSurface/tube.stl` is the exact
  finned-tube surface; wrap/subtract it inside the box.

> **Fin-clipping caveat (inherited).** The fin outer radius (24.7 mm) exceeds $S_L/2$ (22.225 mm), so in a
> single-tube box the fins are clipped at the inlet/outlet planes. This is inherent to one-tube domains and biases
> friction, not heat transfer. With 80 M cells you can instead build a **multi-row bank** (§11) to remove it.

# 4. Mesh

## 4.1 Strategy

- **Recommended:** Fluent Meshing **poly-hexcore** (Mosaic) with **boundary-layer inflation** on the `tube` walls,
  or ANSYS Meshing with sweep + inflation.
- **Thin fins (0.5 mm):** enforce local face sizing so $\ge 4$ cells span the fin thickness and wrap inflation
  around the fin tips/edges.
- **Near-wall target:** $y^+ \le 1$ on tube+fin walls (the original achieved mean 0.24). $k$–$\omega$ SST needs a
  wall-resolved mesh here — do **not** use wall functions.

## 4.2 First-cell height (inflation)

Flat-plate estimate at the min-flow velocity ($U_{max}\approx13.7$ m/s, $L=d_o$, film properties):
$C_f\approx0.058\,Re^{-0.2}\approx9.5\times10^{-3}$, $\tau_w\approx0.84$ Pa, $u_\tau\approx0.94$ m/s, giving for
$y^+=1$:

$$ y_1 = \frac{y^+\,\mu}{\rho\,u_\tau} \approx \frac{(1)(3.9\times10^{-5})}{(0.94)(0.94)} \approx 44\ \mu\text{m}. $$

**Recommendation:** first-layer height **20–30 µm**, growth ratio **1.15–1.2**, **12–15 layers**; then *verify* the
$y^+$ contour on `tube` after the solve and adjust (fin leading edges run higher). The original OpenFOAM first cell
was ~24 µm ($\Rightarrow y^+$ mean 0.24).

## 4.3 Grid-convergence study (use the 80 M budget)

Run **three systematically refined meshes** (e.g. ~8 M / ~25 M / ~80 M cells, refinement ratio ~1.5 per direction),
report $Nu$ on each, and compute the **Grid Convergence Index (GCI)** [10]. This replaces the single-mesh adequacy
argument of the original (a documented limitation) with a formal mesh-independence result.

# 5. Physics and solver setup (Fluent)

| Setting | Value | OpenFOAM equivalent |
|---|---|---|
| Solver | Pressure-based, **Coupled** scheme, **Steady** | `rhoSimpleFoam` (compressible SIMPLE) |
| Energy equation | **On** | — |
| Viscous model | **$k$–$\omega$ SST**, low-Re / wall-resolved | `kOmegaSST` (RAS) |
| Operating pressure | 200 000 Pa (2 bar, heater side) | `p` field ≈ 2e5 |
| Gravity | Off | — |

## 5.1 Material — air (temperature-dependent)

| Property | Method in Fluent | Value / coefficients |
|---|---|---|
| Density | **ideal-gas** | $\rho = p/(RT)$, $R=287$ J kg⁻¹ K⁻¹ |
| Viscosity | **Sutherland (two-coefficient)** | $\mu = \dfrac{1.458\times10^{-6}\,T^{1.5}}{T+110.4}$ |
| Specific heat $c_p$ | piecewise-poly (JANAF) or constant | ~1080 J kg⁻¹ K⁻¹ at film temp |
| Thermal conductivity $k$ | set to hold $Pr=0.69$ | $k = \mu c_p/Pr \approx 0.061$ W m⁻¹ K⁻¹ at film |

> **Consistency note.** The validation fixes the air Prandtl number at **$Pr = 0.69$** (high-temperature air) and
> derives $k = \mu c_p / Pr$. Reproduce this so that $Nu = h d_o/k$ is comparable with the Briggs–Young correlation
> (which is evaluated at the same $Pr$). If you instead use kinetic-theory $k$, report the actual $Pr$ used.

# 6. Boundary conditions

| Face | Fluent BC | Settings |
|---|---|---|
| `inlet` | velocity-inlet | $U=6.3623$ m s⁻¹ (normal, $+y$); $T=740$ K; turb. intensity ~5%, viscosity ratio ~10 |
| `outlet` | pressure-outlet | gauge 0 Pa (operating 200 kPa); backflow $T=740$ K, backflow turb. as inlet |
| `tube` (+ fins) | wall | no-slip; **fixed temperature $T_w = 1033$ K** (condensing-Na heat-pipe wall) |
| `periodic_x_*` | periodic | **translational**, offset $S_T=50.8$ mm |
| `sym_z_*` | symmetry | mid-fin-gap planes |

> The isothermal wall represents the sodium heat-pipe condenser, which is genuinely near-isothermal by phase change.
> If you enable conjugate heat transfer (§11), instead set the fin solid with $k_{fin}=25$ W m⁻¹ K⁻¹ and apply
> 1033 K at the tube bore.

# 7. Solution controls and convergence

- **Spatial discretization:** second-order upwind for momentum, energy, turbulence; PRESTO! or second-order for
  pressure.
- **Coupled** controls: pseudo-transient or a Courant number ramp; keep density/energy under-relaxation moderate
  early (the original used heavy under-relaxation: $p$ 0.3, $\rho$ 0.05).
- **Initialization:** hybrid initialization, or standard from inlet values.
- **Convergence:** scaled residuals $< 10^{-4}$ (target $10^{-5}$–$10^{-6}$), **and** monitor to steadiness:
  (i) area-weighted **wall heat flux on `tube`**, (ii) mass-weighted **outlet temperature**, (iii) mass imbalance
  inlet vs outlet $< 0.1\%$. The original converged in 464 iterations.
- **Temperature limiter (optional):** clamp $T$ to a physical band (e.g. 300–1200 K) to survive early transients.

# 8. Post-processing — computing $Nu$, $Re$, $f$

Extract three integrals from the converged solution (Reports → Surface Integrals / Fluxes):

1. **$Q$** = integral of *Total Surface Heat Flux* over `tube` → target 256 W.
2. **$T_{out}$** = mass-weighted average of temperature on `outlet`.
3. **$\dot m$** = mass flow rate at `inlet`; **$\Delta p$** = area-avg $p$(inlet) − area-avg $p$(outlet).

Then compute (property model: $R=287$, $c_p=1080$, $Pr=0.69$, Sutherland $\mu$):

$$ q'' = \frac{Q}{A_{wetted}}, \qquad
\Delta T_{lm} = \frac{\Delta T_{in}-\Delta T_{out}}{\ln(\Delta T_{in}/\Delta T_{out})},\quad
\Delta T_{in}=T_w-T_{in},\ \Delta T_{out}=T_w-T_{out}. $$

$$ h = \frac{q''}{\Delta T_{lm}}, \qquad
T_{film}=\tfrac{1}{2}\!\left(T_w + \tfrac{T_{in}+T_{out}}{2}\right), \qquad
Nu = \frac{h\,d_o}{k(T_{film})}. $$

$$ Re = \frac{G_{max}\,d_o}{\mu(T_{film})},\quad G_{max}=\frac{\dot m}{A_{min}},\quad
A_{min}=3\big[(S_T-d_o)p_f - 2\,(\text{fin height})\,t\big]=2.69\times10^{-4}\ \text{m}^2. $$

$$ f = \frac{\Delta p}{\tfrac12\,\rho_{in}\,U_{max}^2\,N_{rows}}, \qquad U_{max}=\frac{\dot m}{\rho_{in} A_{min}}. $$

> **Critical convention — use LMTD, not wall-minus-inlet.** The air warms across the tube, so the driving $\Delta T$
> is the log-mean. Using the naïve $T_w-T_{in}$ gives $Nu=40.3$ ($-25.5\%$, **fails** validation); LMTD gives
> $Nu=45.9$ ($-15.2\%$, **passes**). Briggs–Young is itself LMTD-based, so LMTD is the like-for-like choice.

# 9. Validation correlations

Evaluate at the CFD-derived $Re$ and $Pr$.

**Briggs–Young (1963) — heat transfer** [1]:
$$ Nu_{BY} = 0.134\,Re^{0.681}\,Pr^{1/3}\left(\frac{s}{H_{fin}}\right)^{0.2}\left(\frac{s}{t}\right)^{0.1134}. $$
With $s=3.5$ mm, $H_{fin}=12$ mm, $t=0.5$ mm ($s/H_{fin}=0.292$, $s/t=7.0$) at $Re=8368$, $Pr=0.69$:
$Nu_{BY}=54.1$. **Acceptance: CFD within $\pm20\%$ → validated.**

**Robinson–Briggs (1966) — friction** [2]:
$$ f_{RB} = 9.465\,Re^{-0.316}\left(\frac{S_T}{d_o}\right)^{-0.927} = 0.287\ \text{at } Re=8368,\ S_T/d_o=2.0. $$

> **Friction caveat.** In the single-tube box the CFD $\Delta p$ spans the whole domain (plenum + wake), while
> Robinson–Briggs describes only the per-row bundle loss; the two are not directly comparable, so friction is
> reported but **not used**. A multi-row bank (§11) makes $f$ meaningful.

# 10. Expected outcome and checks

| Check | Expected | Meaning |
|---|---|---|
| $Nu$ (LMTD) | 44–48 (orig. 45.9) | within $\pm20\%$ of $Nu_{BY}=54.1$ → **validated** |
| $y^+$ on tube | mean $<1$ | wall-resolved; $k$–$\omega$ SST valid |
| $Q$ | ~256 W (single cell) | energy into the air |
| Mass imbalance | $<0.1\%$ | converged |
| GCI (3 meshes) | $<$ few % | mesh-independent (new, vs original) |

If $Nu$ lands materially outside $\pm20\%$, first check: (a) LMTD used, not $T_w-T_{in}$; (b) $Pr=0.69$ and $k$
consistent; (c) $y^+\le1$; (d) $Re$ computed on the **min-flow** section, not inlet velocity.

# 11. Extensions enabled by the 80 M-cell budget

1. **Grid-convergence (GCI) study** — 3 meshes; converts the original single-mesh adequacy claim into a formal
   mesh-independence proof.
2. **Multi-row staggered bank** (e.g. 4–6 rows × several columns with true periodicity) — removes fin clipping and
   makes the **friction factor** validate against Robinson–Briggs.
3. **Conjugate heat transfer (CHT)** — model the fin as solid with $k_{fin}=25$ W m⁻¹ K⁻¹ and 1033 K at the tube
   bore, obtaining the **fin efficiency** ($\eta_{fin}\approx0.53$) directly rather than analytically.
4. **Reynolds sweep** (6 points, e.g. $Re=4000$–$14000$) — a fully CFD-derived $Nu(Re)$ law, replacing the
   correlation-anchored curve.

# 12. OpenFOAM → ANSYS quick map (appendix)

| OpenFOAM | ANSYS Fluent |
|---|---|
| `rhoSimpleFoam` (steady compressible SIMPLE) | Pressure-based Coupled, Steady |
| `kOmegaSST` | $k$–$\omega$ SST |
| `thermophysicalProperties` (perfectGas, Sutherland, JANAF) | ideal-gas density, Sutherland viscosity, piecewise $c_p$ |
| `fixedValue U` inlet | velocity-inlet |
| `inletOutlet` / pressure outlet | pressure-outlet |
| `fixedValue T=1033` on `tube` | wall, fixed temperature 1033 K |
| `cyclic` (x) | translational periodic |
| `symmetryPlane` (z) | symmetry |
| `wallHeatFlux`, `yPlus` function objects | Surface Integrals / $y^+$ contour |
| `snappyHexMesh` + 8 layers | Fluent Meshing poly-hexcore + inflation |

# References

1. Briggs, D. E., & Young, E. H. (1963). *Convection heat transfer and pressure drop of air flowing across
   triangular pitch banks of finned tubes.* Chemical Engineering Progress Symposium Series, **59**(41), 1–10.
2. Robinson, K. K., & Briggs, D. E. (1966). *Pressure drop of air flowing across triangular pitch banks of finned
   tubes.* Chemical Engineering Progress Symposium Series, **62**(64), 177–184.
3. Menter, F. R. (1994). *Two-equation eddy-viscosity turbulence models for engineering applications.* AIAA Journal,
   **32**(8), 1598–1605.
4. ANSYS Inc. (2024). *ANSYS Fluent Theory Guide* and *ANSYS Fluent User's Guide*, Release 2024 R2.
5. Incropera, F. P., DeWitt, D. P., Bergman, T. L., & Lavine, A. S. (2017). *Fundamentals of Heat and Mass
   Transfer* (8th ed.). Wiley. [LMTD, $\varepsilon$–NTU, Nusselt, fin efficiency]
6. Kays, W. M., & London, A. L. (1984). *Compact Heat Exchangers* (3rd ed.). McGraw-Hill.
7. White, F. M. (2006). *Viscous Fluid Flow* (3rd ed.). McGraw-Hill. [Sutherland viscosity law]
8. IAEA (2024). *Advanced Reactors Information System (ARIS): SMR Catalogue 2024* — Westinghouse eVinci datasheet.
9. Project source: `phase1_derating/cfd/` (OpenFOAM case, `README.md`, `validation/single_point_check.py`,
   `correlations/finned_tube_corr.py`); `spec/A1_reference_spec_sheet.md` §4d; `DECISIONS_LOG.md` D12.
10. Celik, I. B., et al. (2008). *Procedure for estimation and reporting of uncertainty due to discretization in CFD
    applications (Grid Convergence Index).* Journal of Fluids Engineering, **130**(7), 078001.
