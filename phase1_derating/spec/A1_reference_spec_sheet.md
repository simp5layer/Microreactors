# A1 — Reference Reactor Spec Sheet (eVinci-class heat-pipe microreactor)

**Purpose:** the fixed, sourced parameter set every downstream model (v1 cycle, CFD, safety) inherits.
**Primary source:** IAEA ARIS *SMR catalogue 2024*, Westinghouse eVinci datasheet (pp. 333–335),
content provided by Westinghouse — `data/evinci_docs/IAEA_ARIS_SMR_catalogue_2024.pdf`.
**Status:** factual block locked; assumption block pending decisions (see bottom).

## 1. Known parameters (from ARIS 2024 — citable)

| Parameter | Value | Note |
|---|---|---|
| Reactor type | Micro-modular, heat-pipe | |
| Coolant / moderator | Sodium (Na) heat pipes / graphite | no bulk primary coolant |
| **Thermal / electric capacity** | **15 MWth / 5 MWe** | ⇒ net efficiency ≈ **33 %** at (unstated) design point |
| **Power conversion system** | **Open-air Brayton cycle** | *decisive for derating — see §3* |
| Primary circulation | Natural (capillary, heat pipes) | |
| Primary operating pressure | 0.12 MPa | near-atmospheric |
| Core inlet/outlet temperature | **N/A (not published)** | → assumption from Na heat-pipe physics |
| Fuel | TRISO compacts, 19.75 % HALEU (U-235) | recorded as design fact only; **no enrichment analysis** (123-Agreement) |
| Refuelling interval | 8 full-power years | |
| Reactivity control | Control drums (primary) + shutdown rods | |
| Approach to safety | Inherent + passive shutdown & heat removal | supports A5 safety case |
| Design life | 8 years | |
| Plant footprint | < 2 000 m² | |
| Seismic design (SSE) | 1 g PGA | |
| Packaging | 2 ISO shipping containers (reactor+PCS / power-electronics+I&C) | |
| Design status | Detailed Design | |

**Discrepancy flagged:** project CLAUDE.md quotes ~13 MWth; ARIS 2024 (authoritative, Westinghouse-provided)
says **15 MWth / 5 MWe**. Adopt ARIS. Waste heat to reject ≈ 15 − 5 = **10 MW** (before PCS/parasitic detail).

## 2. Heat path (from ARIS text)

Core (TRISO/graphite) → **Na heat pipes** (passive, ~fixed delivery temperature) → **heat exchanger** →
**open-air Brayton PCS** → electricity. Heat pipes thermally decouple the core from the PCS: the core makes
15 MWth regardless of weather; **all ambient sensitivity lives in the PCS.**

## 3. Why "open-air Brayton" changes everything (the key finding)

An **open-air** Brayton draws its working fluid *from ambient* and exhausts it — so:
- **Compressor inlet temperature = ambient temperature.** This is the classic gas-turbine "hot-day derating":
  compressor work rises with inlet T, and intake air density (∝ 1/T) falls, cutting mass flow and net power.
- The derating is therefore **dominated by cycle thermodynamics** (compressor inlet), not by a closed-loop
  air-cooled condenser. → **v1 (the cycle model) captures most of the penalty**; CFD's role narrows to the
  heat-pipe→air heat-exchanger effectiveness and intake/exhaust recirculation.
- An open-air Brayton in 55 °C desert air is close to the **worst-case** cycle for thermal derating — which
  makes the "desert thermal penalty" both physically dominant and the right story for the paper.
- Note vs. our earlier plan: the CFD is **less** of a closed-condenser problem than assumed; re-scope A4
  around the hot-side HX + intake recirculation once v1 exists.

## 4. Assumption block — LOCKED for v1 (calibration v1.1; each carries a sensitivity range)

Decisions (2026-07-04): **normalize to 25 °C · calibrate to 33% net · electricity-only.**
Calibration philosophy (v1.1): **fix the well-characterized quantity, solve for the unknown.** BOP losses
are well-known → fix η_mech; TIT is non-public/design-specific → solve it to hit net 33% and verify it
lands in the Na heat-pipe band. Remaining non-public parameters are swept in `cycle_model/derating_v1.py`
(this is what makes absolute-number uncertainty defensible — the *shape* is robust).

| Parameter | Basis | v1.1 baseline | Sweep range |
|---|---|---|---|
| Lumped generator+mech+parasitic η_mech | **FIXED** — small-genset literature (~0.90–0.94) | **0.93** | 0.90–0.95 |
| Turbine-inlet temperature (TIT) | **SOLVED** to hit net 33%; gated to Na heat-pipe band | **742 °C** ✓ in-band | (re-solved per combo) |
| Brayton pressure ratio | Recuperated microturbine; low PR favours efficiency | **3.0** | 2.5–3.5 |
| Compressor isentropic eff. | Small-machine literature | **0.82** | (in refinement) |
| Turbine isentropic eff. | " | **0.85** | (in refinement) |
| Recuperator effectiveness | Recuperated Brayton | **0.88** | (in refinement) |
| Mass-flow law vs ambient | Compressor similarity | **corrected (∝p/√T)** | corrected / density(∝p/T) |
| Design-point ambient anchor | decision | **25 °C** (100% ref) | — |

**Calibration check (passed):** η_mech=0.93 → cycle thermal eff 35.8% → **solved TIT = 742 °C**, inside the
650–750 °C Na heat-pipe band ✓. Supersedes v1.0 (which fixed TIT and solved η_mech → 0.971, the optimistic
edge). Sensitivity re-solves TIT per combo and **drops out-of-band sets** (e.g. η_mech 0.90 + PR 2.5 → 763 °C):
10 of 18 combos are physically consistent — that self-filtering is itself a rigor gain. See DECISIONS_LOG D10.

## 4b. v1 results (from `results/derating_curve_v1.csv`, calibration v1.1)
- Net **5.00 MWe @ 25 °C** (nameplate) → **4.11 MWe @ 55 °C** = **−17.7% power**, efficiency 33.3%→29.3%.
- Mean electric derating **≈ 0.60 %/°C** (25–45 °C) — **~4× the Carnot-only slope (0.14 %/°C)**, and in the
  known gas-turbine hot-day range (0.5–0.9 %/°C). This gap *is* the paper's core physics claim.
- Cycle absorbs 14.0/15 MWth at 55 °C → ~1 MWth of mild thermal derating (reactor sheds heat it can't convert).
- Sensitivity band is asymmetric (skews low at high ambient): the **mass-flow law** (corrected ∝p/√T vs
  density ∝p/T) is the dominant remaining uncertainty — a prime target for the CFD (v2) to pin down.

## 4c. v1.5 — ε-NTU heat-exchanger refinement (`cycle_model/hx_entu_v1_5.py`)
Replaces v1's *assumed* recuperator effectiveness + fixed TIT with sized ε-NTU components (recuperator
balanced counterflow ε=NTU/(1+NTU); heater = condensing-Na isothermal source ε=1−exp(−NTU); air-side
UA∝ṁ⁰·⁶) coupled to the reactor's fixed-power energy balance. **Adversarially verified** (3-lens workflow):
equations confirmed correct; a draft sizing artifact (design pinned to the regime knife-edge) was caught
and fixed by sizing the heater to an independent design approach with real heat-pipe headroom.

**Headline v1.5 finding — the derating is control-strategy-dependent, bracketed by two bounds:**
| Bound | Strategy | Derating (25–45 °C) | @55 °C |
|---|---|---|---|
| **v1 fixed-TIT (baseline)** | firing temp held constant; reactor power follows / self-throttles | 0.60 %/°C | **−17.7%** |
| **v1.5 regime B (optimistic)** | reactor pins 15 MWth, TIT floats up with ambient to the heat-pipe ceiling | 0.15 %/°C then steepens | **−8.8%** |

- **B→A crossover** (TIT hits the Na heat-pipe ceiling → reactor sheds heat, curve steepens) is a *computed*
  result set by heat-pipe headroom: **35 / 45 / 55 °C** for a source ceiling of **780 / 800 / 820 °C**.
- **Which is more physical:** v1 fixed-TIT is the conservative, likely-more-realistic baseline — eVinci's
  strong **negative temperature reactivity feedback** (ARIS: inherent self-regulation) resists the core
  running hotter, which is exactly what regime B requires. Regime B is the optimistic bound (assumes the
  core tolerates rising temperature). **Phase-2 interface stays on v1 (conservative);** v1.5 regime-B is the
  optimistic sensitivity bound.
- **Also delivered:** HX sizing (UA_heater ≈ 152 kW/K, UA_recup ≈ 401 kW/K — targets for the CFD air-side),
  and a fixed efficiency accounting: **plant_efficiency = net/15 MWth** (fuel-to-electric, primary) vs
  cycle_efficiency (net/absorbed) — they diverge ~2 pts once heat is shed. *(Note: v1's reported efficiency
  is cycle efficiency; slightly optimistic at high ambient — use plant efficiency for the fuel-to-electric claim.)*

## 4d. CFD v2 — air-side UA validation (Option 1)
`phase1_derating/cfd/` — a steady compressible `rhoSimpleFoam` + k-ω SST OpenFOAM solve of the
staggered finned-tube heater unit cell (tube OD 25.4 mm, fin height 12 mm/thickness 0.5 mm/pitch
4 mm, S_T=2.0·d₀, S_L=1.75·d₀; wall 1033 K, air inlet 740 K, ≈2 bar), 3.29M cells, checkMesh OK,
SIMPLE converged in 464 iterations, y⁺ mean 0.244/max 4.63, design point Re = 8368.

**Path taken — Option 1:** a single validated CFD point (not a multi-point Re sweep), because the
point validated heat transfer and the sensitivity analysis below shows the result is second-order
in the air-side law anyway. See `phase1_derating/cfd/README.md` and DECISIONS_LOG D12.

**Validation result (Re = 8368):**
| Quantity | CFD | Correlation | Deviation | Verdict |
|---|---|---|---|---|
| Nu (LMTD) | 45.9 | 54.1 (Briggs–Young) | −15.2% | within ±20% → **heat transfer VALIDATED** |
| f | 1.688 | 0.287 (Robinson–Briggs) | +489% | outside ±20% → **friction does NOT validate** |

The friction miss is a measurement-domain mismatch (CFD Δp spans the whole unit cell — inlet +
outlet + wake, ≈1.7 velocity heads — vs the correlation's per-row bundle loss), compounded by fin
clipping (below); not a Reynolds-dependence problem a sweep would fix. Friction is therefore kept
**informational only** and is not wired into the v2 power balance.

**UA(ṁ) law adopted:** the now-CFD-validated Briggs–Young Nu(Re) law, converted to heater UA and
anchored to v1.5's design magnitude — **UA = 152.35 kW/K at ṁ_des = 54.37 kg/s** (v2 == v1.5 exactly
at the design point). The raw Nu scaling (Re^0.681) is steeper than v1.5's assumed exponent, but
UA = h·A·η_o and the reference fin is thermally inefficient (η_fin ≈ 0.53 at design, realistic for a
low-conductivity k ≈ 25 W/m·K high-temperature alloy): overall surface efficiency η_o falls
0.62→0.54 as ṁ rises (dln η_o/dln ṁ ≈ −0.23), so the net effective exponent is
**n_air_effective = 0.454 — SHALLOWER than v1.5's assumed 0.6**, not steeper.

**v2 curve** (`results/derating_curve_v2.csv`, this UA law injected into v1.5's regime-B cycle):
| Ambient | v2 net MWe (% of 25 °C) | Regime |
|---:|:---:|:---:|
| 25 °C | 5.000 (100.0%) | B |
| 35 °C | 4.926 (98.5%) | B |
| 45 °C | 4.852 (97.1%) | A |
| 55 °C | 4.566 (91.3%) | A |

Mean derating 0.15%/°C (25–45 °C); penalty at 55 °C = **−8.7%** vs v1.5's −8.8% (assumed UA∝ṁ⁰·⁶)
— a **+0.08-point delta that CONFIRMS v1.5**. Reason: the open-air Brayton's ambient-driven air
mass flow varies only ~4–5% over 25→55 °C, so even the 0.6→0.454 exponent change is second-order —
the desert penalty is dominated by compressor-inlet thermodynamics, and the CFD's job (confirming
the air-side heat-exchanger law doesn't change that) is done.

**Limitations (full detail in `phase1_derating/cfd/README.md`):** fin clipping (reference fin
outer radius 24.7 mm > S_L/2 = 22.2 mm, so fins overrun the single-tube box and are clipped at
inlet/outlet, ~42% of the inlet plane at fin z-levels — inherent to fin height ≈ tube radius plus a
single-tube domain); friction not validated/not used; mesh independence not formally studied (single
validated point + adequacy evidence, not a 3-level grid-convergence study); localized ω bounding at
fin tips (does not perturb converged bulk fields); Option 1 chosen over a full 6-point CFD sweep.

## 5. Comparators (for cross-class sensitivity, from same ARIS catalogue)
USNC MMR (HTGR, molten-salt store), MARVEL (INL), Oklo Aurora — datasheets in the same PDF; extract later.
