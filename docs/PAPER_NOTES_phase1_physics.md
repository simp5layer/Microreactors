# Paper Notes — Phase 1 Physics (Derating + Neutronics + CFD)

**Purpose:** everything that should go into the first draft of the paper's physics half — the desert
thermal derating of an eVinci-class heat-pipe microreactor, its CFD validation, and the bounded
OpenMC neutronics package. Assembled from the committed project work so the draft can be written
without re-deriving. Numbers are pulled from the locked spec, the CFD campaign, and the derating
CSVs; **items marked `[FILL]` are results the authors must insert** (chiefly the OpenMC run, which
is not in this repo).

**Status (2026-07-08):** derating curve done through v2 (CFD-validated); OpenMC neutronics reported
complete by co-author (numbers pending insertion here); safety case (A5) and Phase-2 siting coupling
not yet built. This file covers the physics stream (Stream A). Phase 2 (siting) is the paper's second
half and is flagged where it plugs in but not drafted here.

**Source docs (authoritative, cite these internally):** `phase1_derating/spec/A1_reference_spec_sheet.md`,
`phase1_derating/cfd/README.md`, `DECISIONS_LOG.md` (D3, D6–D12), `RESEARCH_OBJECTIVES.md`,
`data/nuclear_benchmarks/SOURCES.md`.

---

## 1. Paper framing

### 1.1 The gap / novelty (this is the paper's reason to exist)
Published microreactor **siting** studies score "climate" heuristically (Proposal 2 gave ambient
temperature a 10% AHP weight). Published **derating** studies stop at the plant fence. **No study
closes the loop** — physics-derived, per-site effective output driving the siting decision. Phase 1
produces that physics (the derating curve); Phase 2 embeds it in the siting framework. The closed
loop is the contribution.

### 1.2 Working title options
- "The Desert Thermal Penalty on an Air-Cooled Heat-Pipe Microreactor, and Its Consequences for
  Siting in Saudi Arabia"
- "From Ambient Heat to Site Ranking: A Physics-Grounded Derating Curve for eVinci-class Microreactors"

### 1.3 Target journal (decide at M5, DP3)
*Applied Energy* / *Energy Conversion & Management* (energy story) vs *Desalination* (water story).
Choose after the strongest result lands. Optional secondary route: contribute the thermal results to
the OECD-NEA heat-pipe microreactor benchmark.

### 1.4 One-paragraph abstract draft (physics half)
> Heat-pipe microreactors such as the Westinghouse eVinci are proposed for arid regions precisely
> because they need no cooling water — but that same water-free, open-air power conversion is what
> exposes them to a large "hot-day" derating in desert ambient conditions. We quantify the net-power
> and efficiency penalty of an eVinci-class 15 MWth / 5 MWe unit across a 25–55 °C ambient range using
> a three-tier physics model: a calibrated open-air recuperated Brayton cycle, an ε-NTU heat-exchanger
> refinement with a reactor energy balance, and an OpenFOAM CFD validation of the air-side heater. A
> bounded OpenMC neutronics package (validated against the KRUSTY criticality benchmark) supplies the
> temperature reactivity coefficients and decay-heat basis that justify the thermal-boundary
> assumptions. We find a derating of [conservative −17.7% to optimistic −8.7%] in net electrical
> output at 55 °C relative to 25 °C, dominated by compressor-inlet thermodynamics and robust to the
> detailed air-side heat-transfer law. [Phase 2: this curve, applied per-site via NASA POWER
> climatology, changes the ranking of candidate Saudi sites relative to the heuristic climate baseline.]

### 1.5 Proposed section map (combined paper)
1. Introduction & gap
2. Reference design & assumptions (Table 1)
3. Methods — cycle model (v1/v1.1) → ε-NTU (v1.5) → CFD (v2) → neutronics (OpenMC)
4. Results — derating curve (Table + figure), CFD validation, neutronics validation
5. Discussion — system-boundary / "isolated environment" argument; robustness; intake-conditioning trade
6. Limitations
7. [Phase 2 — siting methodology & results]
8. Conclusions
9. Data & code availability

---

## 2. Reference design (paper Table 1)

Source: **IAEA ARIS SMR catalogue 2024** (Westinghouse-provided eVinci datasheet, pp. 333–335).

| Parameter | Value | Note |
|---|---|---|
| Reactor type | Micro-modular, heat-pipe | |
| Coolant / moderator | Sodium (Na) heat pipes / graphite | no bulk primary coolant |
| Thermal / electric capacity | **15 MWth / 5 MWe** | ⇒ net efficiency ≈ **33%** at (unstated) design point |
| Power conversion system | **Open-air Brayton cycle** | decisive for derating (compressor breathes ambient) |
| Primary circulation | Natural (capillary, heat pipes) | |
| Primary operating pressure | 0.12 MPa | near-atmospheric |
| Core inlet/outlet temperature | not published | assumption from Na heat-pipe physics (650–750 °C band) |
| Fuel | TRISO compacts, 19.75% HALEU | design fact only; **no enrichment analysis** (123-Agreement) |
| Refuelling interval | 8 full-power years | |
| Reactivity control | Control drums (primary) + shutdown rods | |
| Approach to safety | Inherent + passive shutdown & heat removal | supports safety case |
| Design life | 8 years | |
| Plant footprint | < 2000 m² | |
| Seismic design (SSE) | 1 g PGA | |
| Packaging | 2 ISO shipping containers | |
| Design status | Detailed Design | |

**Waste heat to reject** ≈ 15 − 5 = **10 MW** (before PCS/parasitic detail).

**Assumption discipline (cite D6):** the eVinci cooler geometry and cycle internals are not public.
The paper models "how a heat-pipe microreactor *of this class* derates," not a digital twin. The
reported quantity is *relative* (%/°C), governed by air physics largely invariant to fin pitch /
exact geometry. Every non-public parameter is entered as a **range** and swept; the curve *shape* is
the robust result. Calibration philosophy (D8/D10): **fix the well-characterized quantity, solve for
the unknown** — fix lumped mechanical/parasitic efficiency η_mech = 0.93, solve turbine-inlet
temperature (TIT) to hit net 33% at 25 °C, verify it lands in the Na heat-pipe band (solved TIT =
**742 °C**, in-band ✓).

---

## 3. Methods

### 3.1 Tier 1 — Thermodynamic cycle model (v1 / v1.1)
- Open-air **recuperated Brayton** cycle, air-standard properties; Carnot + Curzon–Ahlborn bounds
  reported alongside. Code: `phase1_derating/cycle_model/derating_v1.py`.
- Calibration v1.1 (D10): η_mech fixed 0.93; PR = 3.0 (recuperated cycles gain efficiency at low PR;
  PR 3.5 pushed solved TIT over the heat-pipe ceiling — a signal it was too high); compressor/turbine
  isentropic eff 0.82 / 0.85; recuperator effectiveness 0.88; **mass-flow law corrected ∝ p/√T**
  (compressor similarity).
- Normalized to 25 °C = 100% (D8): ARIS gives 5 MWe but not at what ambient; 25 °C is the proposal's
  cool end, so the penalty is the drop into desert heat (avoids claiming an unstated rated point).
- Sensitivity: TIT re-solved per parameter combo; out-of-band sets dropped (10 of 18 combos physically
  consistent — the self-filtering is itself a rigor gain). Band is asymmetric (skews low at high
  ambient); the mass-flow law (∝ p/√T vs density ∝ p/T) is the dominant remaining uncertainty → the
  target the CFD (v2) was built to pin.

### 3.2 Tier 2 — ε-NTU refinement + control-strategy bracket (v1.5)
- Code: `phase1_derating/cycle_model/hx_entu_v1_5.py`. Replaces v1's *assumed* recuperator
  effectiveness + fixed TIT with **sized ε-NTU components** (recuperator = balanced counterflow
  ε = NTU/(1+NTU); heater = condensing-Na isothermal source ε = 1 − exp(−NTU); air-side UA ∝ ṁ^0.6)
  coupled to the reactor's **fixed-power energy balance**.
- **Adversarially verified** (3-lens review, D11): equations and code confirmed correct; a draft
  sizing artifact (design pinned to the regime knife-edge, making regime A appear from 26 °C
  regardless of heat-pipe ceiling) was caught and fixed by sizing the heater to an independent design
  approach (18 °C → design source 760 °C) with real headroom below the 800 °C ceiling.
- **Key conceptual output — the derating is control-strategy-dependent, bracketed by two bounds:**
  - **Regime A / v1 fixed-TIT (conservative):** firing temperature held constant; reactor power
    follows / self-throttles. −17.7% at 55 °C.
  - **Regime B floating-TIT (optimistic):** reactor pins 15 MWth, TIT floats up with ambient to the
    heat-pipe ceiling. −8.8% at 55 °C.
  - **B→A crossover** (TIT hits the Na ceiling → reactor sheds heat, curve steepens) is a *computed*
    result set by heat-pipe headroom: **35 / 45 / 55 °C** for a source ceiling of **780 / 800 / 820 °C**.
- **Which bound is more physical:** v1 fixed-TIT is the conservative, likely-more-realistic baseline —
  eVinci's strong **negative temperature reactivity feedback** (ARIS; and quantified by the OpenMC
  package, §3.4) resists the core running hotter, which is exactly what regime B requires. **The
  Phase-2 interface stays on the conservative v1 curve; v1.5 regime-B is the optimistic sensitivity bound.**
- Also delivered: HX sizing targets for the CFD — **UA_heater ≈ 152 kW/K, UA_recup ≈ 401 kW/K** — and
  a fixed efficiency accounting: report **plant_efficiency = net / 15 MWth** (fuel-to-electric) as
  primary, distinct from cycle_efficiency (net / absorbed), which diverge ~2 pts once heat is shed.

### 3.3 Tier 3 — CFD validation of the air-side heater (v2) — *the CFD chapter*

**Goal:** replace v1.5's *assumed* air-side heater UA(ṁ) scaling (UA ∝ ṁ^0.6) with a physics-grounded,
CFD-validated law, and check whether it changes the derating curve. Directory: `phase1_derating/cfd/`.

**Approach — "Option 1" (single validated point, not a multi-point Reynolds sweep; D12).** Once one
well-instrumented CFD point at the cycle design Reynolds number validated heat transfer against
published correlations, a 6-point sweep would only refine a Nu(Re) *shape* the sensitivity analysis
shows is second-order to the derating result. The ±20% single-point gate was the plan's own documented
criterion for "CFD confirms the assumed model is usable"; it was met. A fully CFD-derived Nu(Re)
correlation and a friction-domain fix are recorded as **documented future extensions**, not silently
dropped.

**Numerical setup:**
- Solver: steady compressible **`rhoSimpleFoam`** + **k-ω SST** turbulence, OpenFOAM ESI image
  (`opencfd/openfoam-default:2406`) via Docker; meshed with snappyHexMesh.
- Geometry: staggered finned-tube **unit cell** (single tube, 3 fin pitches spanwise). Tube OD
  25.4 mm; fin height 12 mm, thickness 0.5 mm, pitch 4 mm; transverse pitch S_T = 2.0·d₀, longitudinal
  pitch S_L = 1.75·d₀.
- Boundary conditions: isothermal tube wall **1033 K**; air inlet **740 K, ≈ 2 bar**;
  temperature-dependent air (Sutherland viscosity, JANAF cp). Axes: x = transverse → cyclic; y =
  streamwise → inlet/outlet; z = tube axis → symmetryPlane at mid-fin-gap (spanwise closure).
- Mesh: **3.29 M cells**; checkMesh OK (max non-orthogonality 64.8, max skewness 3.05).
- Convergence: SIMPLE converged in **464 iterations**, all residuals < 1e-4; **y⁺ mean 0.244, max 4.63**.
- Design point: **Re = 8368** (tube-OD, minimum-flow-section mass flux).

**Validation (Re = 8368):**

| Quantity | CFD | Correlation | Deviation | Verdict |
|---|---|---|---|---|
| Nu (heat transfer, LMTD) | 45.9 | 54.1 (Briggs–Young) | **−15.2%** | within ±20% → **heat transfer VALIDATED** |
| f (friction) | 1.688 | 0.287 (Robinson–Briggs) | **+489%** | outside ±20% → **does NOT validate** |

- **ΔT convention matters:** Nu is computed with the **LMTD** (log-mean temperature difference), the
  physically correct mean driving ΔT for a heat-exchanger balance with air-side bulk warming, and the
  basis of the Briggs–Young correlation. The simpler wall-minus-inlet ΔT understates h and gives
  Nu = 40.3 (−25.5%, outside ±20%) for the *same* run — so the LMTD choice is material and must be
  stated explicitly in the paper.
- **Why friction misses (and why that's acceptable):** measurement-domain mismatch — the CFD Δp spans
  the whole unit cell (inlet + bundle + outlet wake, ≈ 1.7 velocity heads), while Robinson–Briggs
  describes only the incremental per-row bundle loss in a fully developed bank. Compounded by fin
  clipping (§6). Not a Reynolds-dependence issue a sweep would fix. Friction is carried **informational
  only** and is **not** wired into the v2 power balance.
- **Why heat transfer validates cleanly:** it is dominated by the well-resolved bulk boundary layer
  (mean y⁺ 0.244), not by the entrance/exit geometry.

**The UA(ṁ) law injected into v2:** the CFD-validated Briggs–Young Nu(Re) law (Nu ∝ Re^0.681),
converted to overall heater UA and anchored to v1.5's design magnitude **UA = 152.35 kW/K at
ṁ_des = 54.37 kg/s** (so v2 reproduces v1.5 exactly at the design point). Subtlety worth reporting:
the raw h scales *steeper* than v1.5's assumed 0.6, but UA = h·A·η_o, and the reference fin is
thermally **inefficient** (η_fin ≈ 0.53 at design — realistic for a low-conductivity k ≈ 25 W/m·K
high-temperature alloy). Overall surface efficiency η_o *falls* as ṁ rises (0.62 → 0.54,
dln η_o/dln ṁ ≈ −0.23), and that modulation dominates the raw scaling:
**n_air_effective = 0.681 − 0.23 ≈ 0.454 — SHALLOWER than v1.5's assumed 0.6**, not steeper.

**Lasting asset:** a **validated OpenFOAM air-side setup** — the foundation the intake/exhaust
recirculation study (the highest-value CFD follow-on; §10) will stand on.

### 3.4 Bounded neutronics package (OpenMC) — *co-author's chapter; numbers `[FILL]`*

**Scope (D3, objective O2):** OpenMC does **not** drive the derating curve — heat pipes decouple the
core from ambient, so the derating physics lives entirely in the power-conversion system. OpenMC is
the bounded package delivering three things that support the thermal-boundary and safety arguments,
retained for nuclear-thesis credibility and the KRUSTY / OECD-NEA validation route. **Explicitly not a
depletion / core-life study.**

Three deliverables:
1. **KRUSTY benchmark validation** — rebuild the KRUSTY (Kilopower, 2018 NNSS criticality experiment)
   core in OpenMC; match k-eff and reactivity against the INL Virtual Test Bed `gold/` references
   (Serpent / Griffin / MCNP models are in `data/nuclear_benchmarks/.../KRUSTY/Neutronics/`) and the
   published values (Poston et al., *Nuclear Technology* 2020). Cross sections: ENDF/B-VIII.1 HDF5.
   **Target: k-eff within ~500 pcm of the published benchmark.**
2. **Temperature reactivity coefficients** — the quantitative basis for the "negative temperature
   feedback / self-regulation" argument that justifies choosing the **conservative fixed-TIT** derating
   baseline over the optimistic floating-TIT bound (§3.2). KRUSTY is the canonical demonstration of
   this self-regulation, which is why it is the right validation anchor.
3. **Decay-heat curve** — input for the extreme-ambient safety case (A5), cross-checked against the
   **ANS-5.1** decay-heat standard.

**`[FILL]` — insert the co-author's actual OpenMC results:**
- KRUSTY k-eff: `[FILL: OpenMC k-eff ± σ]` vs published `[FILL]` vs VTB gold Serpent/MCNP `[FILL]`;
  Δρ = `[FILL] pcm` (target ≤ 500 pcm).
- Temperature reactivity coefficient: `[FILL: value in pcm/K or ¢/K, over what temperature range]`;
  sign negative, magnitude vs KRUSTY measured `[FILL]`.
- Decay heat: `[FILL: P_decay(t) at key times, e.g. 1 s / 1 min / 1 h / 1 day post-shutdown as % of
  nominal]`; agreement with ANS-5.1 `[FILL]`.
- Model description: `[FILL: geometry simplifications, materials, number of particles/batches,
  statistical uncertainty, library version VIII.1 vs VIII.0]`.

> **Note for authors:** these OpenMC results are reported complete by the co-author but are **not in
> this repository** — only the KRUSTY benchmark *inputs* and the cross-section library are here. Drop
> the numbers into the `[FILL]` slots (or commit the OpenMC case + outputs so this file can be updated
> from them). Do not publish the placeholders.

---

## 4. Results — the derating curve

### 4.1 Headline numbers

| Tier | Strategy | Derating slope (25–45 °C) | Net penalty @ 55 °C | Role |
|---|---|---|---|---|
| **v1 fixed-TIT** | firing temp held; reactor self-throttles | **0.60 %/°C** | **−17.7%** (5.00 → 4.11 MWe) | **conservative baseline = Phase-2 interface** |
| **v1.5 regime-B** | reactor pins 15 MWth, TIT floats to Na ceiling | 0.15 %/°C then steepens | **−8.8%** | optimistic bound |
| **v2 (CFD-validated)** | v1.5 with CFD air-side UA law (n_air = 0.454) | 0.15 %/°C | **−8.7%** | confirms v1.5 (+0.08 pt) |

- The v1 slope (~0.60 %/°C) is **~4× the Carnot-only slope (0.14 %/°C)** and sits in the known
  gas-turbine hot-day range (0.5–0.9 %/°C). **That gap is the paper's core physics claim.**
- The result is therefore a **bracket**: net output at 55 °C is down **8.7% (optimistic) to 17.7%
  (conservative)** relative to 25 °C, with the conservative bound favored by the negative-feedback
  argument (§3.4).

### 4.2 v2 curve (selected points; full table in `results/derating_curve_v2.csv`)

| Ambient | v2 net MWe | % of 25 °C | Regime |
|---:|---:|---:|:---:|
| 25 °C | 5.000 | 100.0% | B |
| 35 °C | 4.926 | 98.5% | B |
| 45 °C | 4.852 | 97.1% | A |
| 55 °C | 4.566 | 91.3% | A |

Data files (interface artifacts): `derating_curve_v1.csv` (committed interface), `derating_curve_v1_5.csv`,
`derating_curve_v2.csv`; comparison figures `derating_curve_v1_vs_v1_5.png`, `derating_curve_v1_5_vs_v2.png`.

### 4.3 CFD validation result → §3.3 table. Neutronics validation → §3.4 `[FILL]`.

---

## 5. Discussion

### 5.1 The "isolated environment" question — system boundary (a robustness argument, put this in the paper)

A natural objection: *won't the reactor be run in a controlled, isolated environment, making a
derating study moot?* For the eVinci the premise is **backwards**, and answering it *strengthens* the
study. Structure the argument as a "system boundary" subsection:

- **The eVinci is not isolated from ambient — it is deliberately ambient-coupled.** Two hard
  thermodynamic boundary conditions, both from the vendor's stated design (ARIS 2024; Westinghouse/DOE
  public statements): (1) **open-air Brayton** — the compressor *breathes ambient air* as its working
  fluid, so compressor inlet temperature = ambient temperature; (2) **air-cooled, water-free** — the
  ultimate heat sink is the desert air, so ~10 MW of waste heat must leave into whatever the ambient
  temperature is. The water-free feature Westinghouse *markets* for arid siting is the very thing that
  makes it lose output in the heat.
- **What IS isolated — and why that helps.** The nuclear *core* is thermally decoupled and
  self-regulating (Na heat pipes deliver heat at near-fixed temperature; negative temperature
  reactivity feedback holds ~15 MWth regardless of weather — quantified by the OpenMC package, §3.4).
  So *all* ambient sensitivity lives in the power-conversion system. This is a **gift to the method**:
  the computed derating is cleanly attributable to PCS thermodynamics, with no confounding from core
  physics. Reviewer says "the reactor is controlled, not exposed" → reply: "exactly, which is why the
  whole penalty lives in the open-air Brayton cycle, and that is what we model."
- **Second law makes it inescapable.** Even a hypothetical fully-isolated machine cannot escape the
  sink: η ≤ 1 − T_cold/T_hot, and in the desert T_cold *is* the hot ambient air. No enclosure changes
  what the waste heat ultimately dumps into. For the open-air Brayton it is worse than pure Carnot (the
  compressor-inlet penalty adds on top) — which is why the slope is ~4× the Carnot slope.

### 5.2 Why the derating is robust to the air-side heat-transfer law (the v2 finding)
The exponent change from the assumed 0.6 to the CFD-validated 0.454 moves the 55 °C penalty by only
+0.08 pt (−8.8% → −8.7%). Reason: the open-air Brayton's **ambient-driven air mass flow varies only
~4–5% over the whole 25→55 °C range**, so even a materially different UA-scaling exponent is
second-order. The penalty is dominated by **compressor-inlet thermodynamics**, not the air-side HX
law. The CFD's job was to confirm that assumption was safe — and it did. This "independent physics
simulation confirms the assumption" is itself a credibility result worth stating.

### 5.3 Intake-conditioning trade — the strongest counter, turned into a result (new content to add)
The sharpest form of the objection is not "isolate the reactor" but **"why not condition/chill the
compressor inlet?"** (standard gas-turbine practice). Meet it head-on: conditioning does not erase the
penalty, it **relocates** it. Two sub-cases to quantify and add as a short sensitivity:
- **Evaporative inlet cooling needs water** → destroys the water-free advantage that made the eVinci
  attractive for Saudi siting. Quantify the water flow to hold inlet at 25 °C in 55 °C ambient.
- **Mechanical inlet chilling is a parasitic electrical load** → comes straight off the 5 MWe.
  Quantify the % of net output a chiller would consume.
Either way the penalty is **conserved** (lost efficiency, or water/parasitic power). Showing this
turns the reviewer's best objection into a publishable robustness result. *(This subsection is not yet
computed — flagged as recommended new content; see §9.)*
- Footnote: even a hypothetical *closed*-Brayton eVinci variant would still be air-cooled (water-free
  is the brand promise), so the heat-sink channel survives; only the compressor-inlet channel softens.
  The study is robust to that too.

---

## 6. Limitations (consolidated, honest — put these in the paper, don't hide them)

**CFD:**
1. **Fin clipping.** Reference fin outer radius (24.7 mm) exceeds S_L/2 (22.2 mm), so the 12 mm fins
   overrun the single-tube box and are clipped at inlet/outlet (~42% of the inlet plane is fin metal
   at fin z-levels). Inherent to fin height ≈ tube radius in a single-tube domain. Biases friction;
   heat transfer still validates (−15.2%).
2. **Friction not validated, not used** (informational only).
3. **Mesh independence not formally studied** — a single validated point + adequacy evidence (−15.2%
   Nu, y⁺ mean 0.244, clean checkMesh), not a formal 3-level grid-convergence study (future work).
4. **Localized ω bounding at fin leading-edge tips** — near-singular-corner artifact; does not perturb
   the converged bulk U/p/T fields.
5. **y⁺ gate exceedance at fin tips** — mean 0.244 satisfies the plan's y⁺ ≤ 2 gate, but max 4.63
   exceeds it at the fin leading edges; k-ω SST blended wall functions remain valid and integrated h
   is bulk-dominated, so the validation holds.
6. **Option 1, not a full sweep** — single-point validation + correlation-driven curve, a deliberate
   efficiency choice once the point passed the ±20% gate.

**Cycle model:** absolute numbers depend on non-public parameters (TIT, HX sizing, cycle internals),
entered as ranges and swept; the *shape* is the robust claim. v1 reported efficiency is cycle
efficiency (slightly optimistic at high ambient) — use plant efficiency (net/15 MWth) for the
fuel-to-electric claim.

**Neutronics:** bounded package (no depletion); simplified KRUSTY-anchored core, not a digital twin of
the eVinci (public data insufficient). `[FILL: statistical uncertainty, geometry simplifications]`.

**Scope not yet done:** extreme-ambient safety case (A5, loss-of-forced-cooling at 55 °C, MELCOR or
lumped fallback) and the Phase-2 siting coupling are not in this draft.

---

## 7. Figures & tables checklist

| # | Item | Source file | Status |
|---|---|---|---|
| T1 | Reference design spec | §2 / A1 spec | ready |
| T2 | Derating headline bracket | §4.1 | ready |
| T3 | CFD validation (Nu, f) | §3.3 | ready |
| T4 | OpenMC validation (k-eff, α_T, decay heat) | §3.4 | **`[FILL]`** |
| F1 | Derating curve v1 vs v1.5 (the two bounds) | `derating_curve_v1_vs_v1_5.png` | ready |
| F2 | Derating curve v1.5 vs v2 (CFD confirms) | `derating_curve_v1_5_vs_v2.png` | ready |
| F3 | CFD domain / mesh / temperature field | regenerate from OpenFOAM case | to render |
| F4 | Decay-heat curve vs ANS-5.1 | OpenMC output | **`[FILL]`** |
| F5 | (Phase 2) site-ranking delta heuristic vs physics | Phase 2 | future |

---

## 8. Reproducibility / data & code availability

- Cycle model: `phase1_derating/cycle_model/derating_v1.py`, `hx_entu_v1_5.py`
  (numpy, pandas, matplotlib, scipy; CoolProp planned for variable air properties).
- CFD: `phase1_derating/cfd/` — OpenFOAM case *source* committed (dicts, `0.orig`, STL); run artifacts
  (mesh, logs, processor dirs, postProcessing) gitignored, regenerated by `run/Allrun`. Post-processing
  is pure Python: `validation/single_point_check.py`, `postprocessing/fit.py`, `cfd_to_v2.py`. 21-test
  pytest suite, all green. Committed on branch `cfd-v2-heater-unitcell` (awaiting merge decision).
- Neutronics: `[FILL: commit the OpenMC case + outputs]`. Benchmark inputs + XS in
  `data/nuclear_benchmarks/` (KRUSTY VTB models; ENDF/B-VIII.1 HDF5, gitignored 9 GB).
- Interface artifacts: `phase1_derating/results/derating_curve_v{1,1_5,2}.csv`.

---

## 9. Recommended additions before submission (my notes)
1. **Compute the intake-conditioning sensitivity (§5.3)** — the single highest-value new result; it
   pre-empties the paper's most likely reviewer objection and is genuinely novel content.
2. **Insert the OpenMC numbers (§3.4 `[FILL]`)** and add the α_T → self-regulation → conservative-baseline
   logical chain explicitly (it ties the neutronics to the derating choice, which is the integrated story).
3. **Render CFD figures (F3)** and a decay-heat figure (F4) for publication.
4. **State the LMTD-vs-inlet ΔT convention explicitly** in Methods — it is the difference between
   validating (−15.2%) and not (−25.5%), and reviewers will check it.
5. Decide the derating headline: lead with the **bracket** [−8.7%, −17.7%] and name the conservative
   v1 as the recommended interface, rather than a single number — it is more defensible and it *is* the
   finding (control-strategy dependence).

## 10. Open items / still-needed for the full paper
- **Safety case (A5):** 55 °C loss-of-forced-cooling transient; MELCOR if licensed (DP1) else
  lumped-parameter with OpenMC decay heat. Not started.
- **Phase-2 siting coupling:** NASA POWER hourly T per site × derating curve → per-site effective
  capacity factor → AHP/RF/SHAP re-run; heuristic-vs-physics ranking delta = RQ3 headline. Not started.
- **Highest-value CFD follow-on:** intake/exhaust **recirculation** study (hot exhaust re-ingested →
  effective inlet T above ambient → derating *worse* than weather alone; no correlation covers it,
  needs CFD; the validated air-side setup is the foundation). Feeds Phase-2 (layout/site dependent).

## 11. References to assemble
- IAEA ARIS SMR catalogue 2024 — eVinci datasheet (reference design).
- Poston, D.I. et al., "Results of the KRUSTY Nuclear System Test" & "KRUSTY Reactor Design,"
  *Nuclear Technology*, 2020 (neutronics validation anchor).
- Briggs & Young (1963) — finned-tube Nusselt correlation (CFD heat-transfer validation).
- Robinson & Briggs (1966) — finned-tube friction correlation (CFD friction comparison).
- ANS-5.1 — decay-heat standard (neutronics cross-check).
- Kröger, "Air-Cooled Heat Exchangers and Cooling Towers" (air-side HX method reference).
- INL Virtual Test Bed — KRUSTY model (github.com/idaholab/virtual_test_bed).
- Romano et al. — OpenMC. | OpenFOAM (ESI/OpenCFD 2406).
- Gas-turbine hot-day / ambient-derating literature (0.5–0.9 %/°C context).
- Westinghouse eVinci public / NRC pre-application materials.
- (Phase 2) NASA POWER; WRI Aqueduct; IAEA DEEP; SWCC LCOW ≈ SAR 1.7/m³ benchmark.
