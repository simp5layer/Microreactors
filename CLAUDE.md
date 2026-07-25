# Combined Microreactor Project — Penalty Curve → Siting Feasibility

This directory hosts the **combined graduation/co-op research project** merging the two proposals in this folder into one project:

1. `Microreactor_Desert_Cogeneration_Proposal.pdf` — *"The Desert Thermal Penalty on Water"*: quantify how extreme Saudi ambient heat (25–55 °C) degrades an air-cooled heat-pipe microreactor's output, and what that does to the cost of cogenerated water/power.
2. `Microreactor_Siting_Proposal_2.docx` — *"Integrated Decision-Support Platform for Microreactor Deployment in Saudi Arabia"*: an AHP + Random Forest + SHAP framework answering WHERE (site ranking), WHY (explainability), WHAT (application matching: mining / desalination / industrial / remote electrification) with a recommended power class (5/10/20 MWe) across 16 (→ 30–80) named Saudi sites.

## The combined plan

- **Phase 1 — Produce the penalty curve.** Thermal model of the reference heat-pipe microreactor across 25–55 °C ambient: OpenMC for core/decay-heat (validated against KRUSTY), OpenFOAM for the air-cooled heat-rejection path, MELCOR for the loss-of-cooling safety case. Output: the **derating/penalty curve** — net efficiency and capacity factor as a function of ambient temperature.
- **Phase 2 — Feasibility study of the siting platform, with the penalty curve embedded.** Run the Proposal-2 decision-support framework (AHP scoring → Random Forest cross-validation → SHAP explainability → use-case classification → power-class recommendation) over the candidate Saudi site pool, but replace the heuristic "climate / ambient temperature" criterion (10 % weight in the original proposal) with the **physics-grounded, site-specific derating** from Phase 1 (per-site NASA POWER climatology → per-site effective output/capacity factor). This turns the siting rankings and per-site feasibility (LCOW/LCOE where relevant, via HERON/RAVEN + IAEA DEEP) into a quantitatively defensible study — the linkage no published work provides.

## Reference designs

- **Primary anchor: Westinghouse eVinci** — heat-pipe microreactor, **15 MWth / 5 MWe** (per IAEA ARIS 2024 datasheet; supersedes the earlier ~13 MWth figure), **open-air Brayton PCS**, air-cooled (no cooling water), 8-year core, TRISO/graphite, Na heat pipes. Its water-free cooling is exactly why it suits arid Saudi siting — and the open-air Brayton (compressor breathes ambient) is exactly why the desert thermal penalty is large. See `phase1_derating/spec/A1_reference_spec_sheet.md`.
- **Comparator: USNC MMR** (HTGR, molten-salt heat store, favors MED thermal desalination). Proposal 2 also references **MARVEL** (INL) and **Oklo Aurora** for cross-class sensitivity.
- Power-class scaling: eVinci-class ~5 MWe single unit as the building block; multi-unit arrays for 10/20 MWe sites.

## Toolchain (all open/unlicensed)

OpenMC (neutronics/decay heat) → OpenFOAM (CFD/air-cooling) + MELCOR (safety) → HERON 2.0 / RAVEN / TEAL (dispatch + technoeconomics) + IAEA DEEP (desalination cost); KRUSTY as the validation benchmark; LCOW calibrated to SWCC's reported SAR 1.7/m³. Siting layer: Python — AHP, scikit-learn Random Forest, SHAP; data from NASA POWER, WRI Aqueduct, GASTAT/WorldPop, Saudi mining cadastre, MODON registry, SEC/OSM grid data. Cost inputs entered as ranges; results reported with uncertainty bands.

## Publication & framing

- Deliverables: **one combined journal paper** (integrated derating→siting story) + two graduation theses (one per stream). Target journals: *Desalination*, *Energy Conversion and Management*, *Applied Energy* (Q1); journal chosen after results land (DP3 in `RESEARCH_OBJECTIVES.md`). Optional route: contribute thermal results to the OECD-NEA heat-pipe microreactor benchmark.
- Optimized for attention from Saudi nuclear entities: KACARE, NRRC, Ministry of Energy, SNE/DNEC. Note: **DNEC (Duwaiheen Nuclear Energy Co.) is a subsidiary of SNE**, owner-operator of the first NPP at Khor Duwaiheen — not related to Dussur.
- **Avoid**: enrichment/HALEU topics (123-Agreement gated) and operational AI/digital twins (no Saudi operating-reactor data).

## Context & people

- Students: **Omar and Saud** — both Nuclear Engineering, King Abdulaziz University, same KACST co-op. Two parallel workstreams (A: physics/derating, B: data/siting) coupled only through the derating-curve interface; stream assignment still open (DP2). Supervisor: Dr. Salman Alshehri, KACST Nuclear Technologies Institute. Co-operative Training Program, 2026.
- `RESEARCH_OBJECTIVES.md` in this directory is the working roadmap: RQ1–RQ5, objectives O1–O7, work packages A1–A5/B1–B6, milestones M0–M8, decision points (DP1 MELCOR access, DP2 stream assignment, DP3 journal, DP4 site-pool cap). Site pool committed at 30–80; OpenMC scoped as a bounded package (KRUSTY validation + decay heat + temperature coefficients — no depletion).
- Background research pipeline that produced this direction lives in `../reports/` (01 entities & priorities, 02 journal hotspots, 03 convergence synthesis, 04 novel methods). An earlier siting draft (`Microreactor_Siting_Proposal_1.docx`) is also in `../reports/`.

## Working docs & current state (read these to get oriented)

Read in this order — they carry the *what*, *why*, *data*, and *results* so you can synthesize without re-deriving:
- `RESEARCH_OBJECTIVES.md` — the plan: RQ1–5, objectives, work packages A1–A5/B1–B6, milestones, decision points.
- `DECISIONS_LOG.md` — the **why** behind every choice (D1–D9), incl. the assumed-design accuracy resolution and the v1 modeling decisions. Append new decisions here; don't edit history.
- `data/DATA_INVENTORY.md` + `data/RESEARCH_SOURCES_REPORT.md` + per-folder `data/*/SOURCES.md` — what data is downloaded vs. gated, with provenance, licenses, refuted claims, and open questions.
- `phase1_derating/` — physics stream. `spec/A1_reference_spec_sheet.md` (locked reactor facts + assumptions), `cycle_model/derating_v1.py` (the model), `results/derating_curve_v1.{csv,png}` (**the interface artifact** Phase 2 consumes).

**Current state (2026-07-08):** data acquired; A1 spec locked; **the derating curve is built through v2**:
- **v1 / v1.1** (fixed-TIT Brayton, calibrated η_mech=0.93, TIT=742 °C): −17.7% power @55 °C, ≈0.60 %/°C. **This is the conservative baseline and the committed Phase-2 interface** (per D11 — negative temperature reactivity resists the core running hotter).
- **v1.5** (ε-NTU heat exchangers + reactor energy balance, D11): regime-B optimistic bound, −8.8% @55 °C.
- **v2** (CFD, D12 — done this session): an OpenFOAM staggered finned-tube unit cell **validated the heater air-side heat transfer to within −15% of the Briggs–Young correlation**, then fed a CFD-validated UA(ṁ) law back into v1.5. **v2 confirms v1.5** (−8.7% @55 °C, +0.08 pt) — headline: *the desert derating is robust to the exact air-side UA law*. Approach was "Option 1" (single-point validation + correlation-driven curve, not a full CFD sweep). Honest caveats in D12 / `cfd/README.md`: friction did not validate (informational only), fins are clipped by the unit-cell box, no formal mesh-independence study. Lasting asset: a **validated OpenFOAM air-side setup**.

CFD v2 work lives in `phase1_derating/cfd/` (read `phase1_derating/cfd/README.md`); it is committed on branch **`cfd-v2-heater-unitcell`** (16 commits, all reviewed; awaiting a merge-to-`main` decision as of this writing). **Next steps:** (a) merge the CFD branch; (b) the **intake/exhaust recirculation CFD study** — the main open CFD follow-on, which the now-validated OpenFOAM setup unlocks (needs an assumed skid external geometry; see `cfd/README.md` future work); (c) wire the derating curve into the Phase-2 siting pipeline. **Gitignore note:** `data/nuclear_benchmarks/openmc_xs/`, the large rasters/PBF, and CFD run artifacts under `phase1_derating/cfd/heater_unitcell/` (mesh, logs, processor dirs, postProcessing) are ignored; keep the `SOURCES.md` pointers and the committed OpenFOAM case *source* (dicts, 0.orig, the STL).
