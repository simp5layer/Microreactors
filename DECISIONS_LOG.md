# Decisions Log — rationale & consequences

The *why* behind the project's choices, for future agents/collaborators to synthesize without
re-deriving. Complements the *what* (RESEARCH_OBJECTIVES.md), the *data* (data/DATA_INVENTORY.md),
and the *facts* (phase1_derating/spec/A1_reference_spec_sheet.md). Newest decisions at the bottom.
Dates absolute. When a decision is later overturned, append a follow-up entry — don't edit history.

---

## D1 — Merge the two proposals into one project, coupled by a single interface
**Decision:** Phase 1 (physics → derating curve) + Phase 2 (siting feasibility), joined by exactly one
artifact: the derating curve `ambient_temp_C → net_MWe / net_efficiency`.
**Why:** the only thing Phase 2 needs from Phase 1 is per-site derating; a single interface lets the two
streams run in parallel and lets Phase 2 build against a placeholder while Phase 1 refines the real curve.
**Consequence:** curve versions (v0 placeholder → v1 cycle → v2 CFD-corrected) are drop-in swaps; the
heuristic-vs-physics ranking delta becomes the headline result (RQ3).

## D2 — Team = two students, streams left unassigned
**Decision:** Omar + Saud (both KAU Nuclear Eng., same KACST co-op). Stream A (physics) / Stream B (siting)
ownership deferred to kickoff (DP2).
**Why:** both need visible nuclear content in their theses; assignment depends on who takes physics vs.
data/ML. **Consequence:** work packages written stream-agnostic; one combined paper + two theses.

## D3 — OpenMC kept but descoped to a bounded package
**Decision:** OpenMC does NOT drive the derating curve; it delivers only (i) KRUSTY validation, (ii) decay
heat for the safety case, (iii) temperature reactivity coefficients. No depletion/core-life study.
**Why:** heat pipes thermally decouple the core from ambient — the core makes 15 MWth regardless of weather,
so the derating physics is entirely in the power-conversion system (thermo + CFD), zero neutronics. OpenMC
is retained for nuclear-thesis credibility + the KRUSTY/OECD-NEA validation route, not because the curve
needs it. **Consequence:** nothing on the critical path waits on OpenMC; it can shrink if the timeline tightens.

## D4 — Data acquisition: download the open, document the gated, geocode the rest
**Decision:** downloaded all openly-available datasets into `data/`; documented gated sources with
workarounds (see data/DATA_INVENTORY.md).
**Why/consequence:** the only external dataset the CFD/derating actually consumes (ambient T) is in hand;
mining/MODON have no open bulk GIS but the study needs site *points not polygons*, so geocoding the named
sites is the fix. K.A.CARE atlas confirmed dead → World Bank/Solargis substitute. NRC eVinci PDF blocked →
IAEA ARIS datasheet covers the design envelope. See data/RESEARCH_SOURCES_REPORT.md for the full survey.

## D5 — Sequence: lock A1 spec sheet and build v1 BEFORE any CFD
**Decision:** the true first build step is A1 (reference spec sheet) → v1 (thermodynamic derating curve),
not the OpenFOAM CFD.
**Why:** CFD sits *downstream* — it needs boundary conditions (waste-heat duty, cycle cold-end temperature,
process fluid/flow) that come out of A1 and v1. Meshing first would mean inventing those inputs ad hoc.
The only external data the CFD needs (ambient) we already have; everything else is upstream engineering.
**Consequence:** A1 + v1 done first; CFD (v2) inherits documented inputs.

## D6 — Accuracy of an assumed reference design (resolved concern)
**Concern raised:** eVinci's cooler geometry/cycle internals aren't public — won't assuming them make the
CFD/derating inaccurate?
**Resolution (the reasoning, so it isn't re-litigated):**
- Two different accuracy questions: "digital twin of the real unit" (impossible, not the goal) vs. "how an
  air-cooled heat-pipe microreactor of this CLASS derates in desert heat" (the actual, answerable question).
- The published result is a *relative* quantity (%/°C), governed by air physics (density ∝ 1/T, shrinking ΔT,
  compressor-inlet effect) that is largely invariant to fin pitch / exact geometry. Two reasonable coolers
  sized to the same duty give near-identical curve *shape*.
- What's genuinely fixed (not assumed): waste-heat duty (public 15/5 ratings), heat-pipe temperature band
  (Na physics), ambient (NASA POWER). The free inputs are HX sizing + cycle internals.
- The discipline that neutralizes the worry: a **parametric sensitivity sweep** across the plausible ranges,
  plotted as a band. Stable shape ⇒ result doesn't depend on the guess; movement ⇒ report a band. Plus solver
  validation against a published air-cooled HX case (Kröger) separates "method accurate" from "geometry real."
- This is standard, expected practice; Proposal 2 already anchors to "publicly documented" specs.
**Consequence:** every non-public parameter is entered with a range; v1 already ships a sensitivity band.

## D7 — eVinci reference facts corrected from IAEA ARIS 2024
**Decision:** adopt **15 MWth / 5 MWe** and **open-air Brayton PCS** (ARIS datasheet, Westinghouse-provided).
**Why/consequence:** supersedes the earlier ~13 MWth figure in CLAUDE.md (now corrected). The open-air
Brayton is decisive — the compressor breathes ambient air, so derating is gas-turbine "hot-day" physics
dominated by the cycle (v1 captures most of it), and the CFD (A4) re-scopes to the heat-pipe→air HX and
intake/exhaust recirculation, NOT a closed condenser. HALEU/enrichment recorded as a design fact only —
no enrichment analysis (123-Agreement, per CLAUDE.md).

## D8 — v1 modeling choices (2026-07-04)
**Decisions (all chosen by the user from recommended options):**
1. **Normalize the curve to 25 °C.** ARIS states 5 MWe but not at what ambient; 25 °C is the proposal's cool
   end, so "100%" = 25 °C output and the penalty is the drop into desert heat. Avoids claiming an unstated
   rated point. *(Alt considered: ISO 15 °C inflates the penalty; 45 °C assumes a hot design point.)*
2. **Calibrate to net 33%** (= 5 MWe / 15 MWth) at 25 °C by lumping generator+mechanical+parasitic losses
   into η_mech, keeping all thermodynamic params at literature values. Anchors to the one hard number.
3. **Electricity-only** for v1; CHP heat path is a later extension.
**Consequence:** v1 is a real engineering model pinned to reality at one point, with everything else swept.

## D9 — v1 result & its one caveat (2026-07-04)
**Result:** net power −19.7% at 55 °C vs 25 °C (5.00 → 4.02 MWe), efficiency 33.3% → 28.6%; mean derating
**≈0.67 %/°C** (25–45 °C) — **~5× the Carnot-only slope (0.14 %/°C)**, matching the known gas-turbine hot-day
range. That gap is the paper's core physics claim.
**Caveat (documented, not hidden):** calibration lands η_mech = 0.971 — the optimistic edge (~3% losses vs a
realistic 5–8%). Reading: the real unit likely runs TIT nearer the 750 °C heat-pipe max or carries more
parasitic load; both are inside the sensitivity sweep. **Fix = v1.1** (bump baseline TIT to 750 °C). Not a blocker.

## D10 — v1.1 calibration tune (2026-07-04)
**Decision:** invert the calibration. v1.0 fixed TIT and solved η_mech → 0.971 (only ~3% BOP loss, too
optimistic). v1.1 applies "**pin the well-characterized quantity, solve for the unknown**":
- **FIX η_mech = 0.93** (generator+mechanical+parasitic; well-known from small-genset literature).
- **SOLVE TIT** so net efficiency = 33% at 25 °C; **verify it lands in the Na heat-pipe band (650–750 °C).**
- **Lower baseline PR 3.5 → 3.0** (recuperated cycles gain efficiency at low PR; PR 3.5 pushed solved TIT to
  ~756 °C, over the heat-pipe ceiling — a signal 3.5 was too high).
**Why:** TIT is genuinely non-public and design-specific, so *solving* for it is honest; BOP losses are
well-characterized, so *fixing* them is safe. The sensitivity now re-solves TIT per combo and drops
out-of-band sets (10/18 physically consistent) — self-filtering to realistic parameter space.
**Result:** solved TIT = **742 °C** (in-band ✓), cycle thermal eff 35.8%, η_mech 0.93. Curve barely moves:
−17.7% power at 55 °C (was −19.7%), slope **0.60 %/°C** (was 0.67) — still ~4× Carnot. The tune improved
calibration realism without changing the physics story, confirming the result is robust. New finding: the
**mass-flow law** (corrected ∝p/√T vs density ∝p/T) is now the dominant remaining uncertainty (asymmetric
band) → a prime thing for the CFD (v2) to pin.
**Consequence:** v1 is calibration-complete. Files regenerated (same `derating_curve_v1.*` names).

## D11 — v1.5 ε-NTU refinement + adversarial verification (2026-07-04)
**What:** built `cycle_model/hx_entu_v1_5.py` — open recuperated Brayton with sized ε-NTU heat exchangers
(recuperator + condensing-Na heater) coupled to the reactor fixed-power energy balance.
**Verification (used the workflow "superpowers"):** ran a 3-lens adversarial review (thermodynamics /
ε-NTU+regime logic / code-numerics). Verdict: **equations & code correct** (Brayton, both ε-NTU closures,
fixed-point convergence, design point all confirmed), but two real issues:
  1. **CRITICAL — regime story was a sizing artifact.** Draft sized heater ε from `TIT_design/T_hp_max`,
     pinning the design point on the B/A knife-edge → regime A from 26 °C regardless; a lens proved it by
     sweeping T_hp_max 760–950 °C with the crossover stuck at 26 °C. **Fixed:** size the heater to an
     independent design approach (18 °C → design source 760 °C) below the ceiling (800 °C), giving real
     headroom. Non-degeneracy now holds: crossover moves 35/45/55 °C with ceiling 780/800/820 °C.
  2. **MINOR — efficiency denominator.** Divided net by absorbed heat, not the fixed 15 MWth → overstated
     plant efficiency ~2 pts when heat is shed. **Fixed:** report plant_efficiency (net/15) as primary.
  3. **MINOR — mass-flow law** noted as the shallow bound for a constant-physical-speed genset.
**Result & reframing:** v1.5 shows the derating is **control-strategy-dependent, bracketed** by v1 fixed-TIT
(−17.7% @55 °C, conservative) and v1.5 regime-B fixed-power/floating-TIT (−8.8%, optimistic). eVinci's
negative temperature reactivity feedback (ARIS) resists the core running hotter → **v1 fixed-TIT is the
more physical baseline and stays the Phase-2 interface**; v1.5 regime-B is the optimistic bound + gives HX
component sizing (UA) for the CFD and the crossover-vs-headroom sensitivity.
**Lesson:** the adversarial workflow converted a plausible-but-wrong "regime transition" claim into a
correct, defensible bracket — worth the cost. Verify coupled-physics models before trusting them.

## Open decisions (not yet made)
- **DP1 MELCOR access** (Sandia/CSARP) — longest external lead time; ask if KACST holds a license.
- **DP2 stream assignment**, **DP3 journal target**, **DP4 site-pool final count** (see RESEARCH_OBJECTIVES.md).
- **Next build step:** CFD (v2) setup — start with the low-effort ε-NTU heat-exchanger model in Python
  (pins the mass-flow law + hot-side HX before any OpenFOAM/Docker), then the OpenFOAM campaign.
