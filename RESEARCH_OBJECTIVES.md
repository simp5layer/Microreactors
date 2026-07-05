# Research Objectives — Desert Thermal Penalty & Microreactor Siting Feasibility in Saudi Arabia

**Type:** Internal working roadmap (reformat later for KACST / KAU committee as needed)
**Team:** Omar & Saud — Nuclear Engineering, King Abdulaziz University; KACST Co-operative Training Program 2026
**Supervisor:** Dr. Salman Alzahrani, KACST Nuclear Technologies Institute
**Status:** v1 — objectives locked; stream assignment and calendar dates deliberately open
**Source proposals:** `Microreactor_Desert_Cogeneration_Proposal.pdf` (Phase 1) + `Microreactor_Siting_Proposal_2.docx` (Phase 2)

---

## 1. Project statement

Quantify how extreme Saudi ambient heat (25–55 °C) derates an air-cooled heat-pipe microreactor
(eVinci-class), and embed that physics-grounded, site-specific derating inside an explainable
decision-support framework (AHP → Random Forest → SHAP) that ranks 30–80 named Saudi sites,
matches each to an application (mining / desalination / industrial / remote electrification), and
recommends a power class (5 / 10 / 20 MWe) with defensible economics (LCOE/LCOW).

**The gap we fill:** published siting studies score "climate" heuristically (Proposal 2 gave it a
10 % AHP weight); published derating studies stop at the plant fence. No study closes the loop —
*physics-derived per-site effective output driving the siting decision*. That closed loop is the
paper.

## 2. Research questions

| # | Question | Stream |
|---|----------|--------|
| RQ1 | How much net power and efficiency does an eVinci-class air-cooled heat-pipe microreactor lose across 25–55 °C ambient — and where does the loss come from (cycle thermodynamics vs. air-side heat rejection vs. hard capacity limits)? | A |
| RQ2 | Does the passive safety case still close at extreme ambient — i.e., under loss of forced cooling on a 55 °C day, do decay heat and heat-pipe limits stay inside safe margins? | A |
| RQ3 | How do site rankings change when the heuristic climate criterion is replaced by physics-grounded per-site derating — heuristic vs. literature-slope vs. our curve? | A + B |
| RQ4 | Which Saudi sites (pool of 30–80) are most feasible, for which application, at which power class — and *why* (SHAP attribution)? | B |
| RQ5 | What is the economic penalty of desert heat at the top-ranked sites — ΔLCOE and ΔLCOW relative to design-point performance (benchmark: SWCC ≈ SAR 1.7/m³)? | B |

## 3. Objectives

- **O1 — Derating curve.** Produce a validated net-output/efficiency vs. ambient-temperature curve
  for the reference reactor over 25–55 °C, built in three fidelity tiers (thermodynamic cycle →
  CFD-corrected → safety-bounded), with uncertainty bands. *(RQ1)*
- **O2 — Bounded neutronics package (OpenMC).** A simplified eVinci-class core model whose three
  deliverables are: (i) validation against the published KRUSTY benchmark, (ii) decay-heat input
  for the safety case (cross-checked against ANS-5.1), (iii) temperature reactivity coefficients
  supporting the self-regulation argument. Explicitly *not* a depletion/core-life study. *(RQ1, RQ2)*
- **O3 — Extreme-ambient safety case.** Loss-of-forced-cooling transient at 55 °C ambient
  (MELCOR if access granted; lumped-parameter fallback), showing passive decay-heat removal margins. *(RQ2)*
- **O4 — Site pool & database.** Assemble 30–80 named candidate sites across four application
  categories with a per-site feature vector (climatology, water stress, demand proxies, grid,
  logistics, seismic/regulatory). *(RQ4)*
- **O5 — Siting pipeline with embedded physics.** AHP baseline → Random Forest cross-validation →
  SHAP explainability → application matching → power-class recommendation, run twice: once with the
  heuristic climate criterion (baseline reproduction), once with per-site effective capacity factor
  from O1. The ranking delta is the headline result. *(RQ3, RQ4)*
- **O6 — Technoeconomics.** LCOE/LCOW with uncertainty bands at the top-ranked sites
  (HERON/RAVEN/TEAL dispatch + IAEA DEEP desalination costing), with and without the thermal
  penalty. *(RQ5)*
- **O7 — Dissemination.** One combined journal paper (integrated derating-to-siting story) +
  two graduation theses (one per stream, see §7) + open code/data repository.

## 4. The interface contract (the one coupling between streams)

Everything Stream A produces reduces to one artifact consumed by Stream B:

```
derating_curve_vN.csv
ambient_temp_C, net_MWe, net_efficiency, heat_rejection_capacity_frac
```

- **v0 (day 1):** literature placeholder, ~0.5 %/°C output loss above design point — lets Stream B
  build and test everything without waiting.
- **v1:** thermodynamic cycle model (Carnot bound + Curzon–Ahlborn + recuperated Brayton with fixed
  component efficiencies).
- **v2:** v1 corrected by OpenFOAM air-side heat-rejection results (density/mass-flow effects,
  approach-temperature growth, hard derating cap).
- **Per-site application (Stream B):** NASA POWER hourly temperature series × curve → hourly net
  output → annual **effective capacity factor** per site. This replaces the 10 % heuristic climate
  weight in the AHP and becomes a feature in the RF.

Curve versions are drop-in swaps; every Stream B result is rerun per version — that rerun *is* RQ3.

## 5. Work packages — Stream A (physics: reactor → curve → safety)

| WP | Content | Deliverable | Est. effort |
|----|---------|-------------|-------------|
| A1 | **Reference reactor spec sheet.** Assemble the "reference eVinci-class unit" from public sources (Westinghouse NRC pre-application docs, IAEA ARIS, published papers), KRUSTY as validation anchor. Every number sourced. | Spec table (paper Table 1) | 2 wk |
| A2 | **Derating curve v1 — cycle model.** Carnot / Curzon–Ahlborn / Brayton over 25–55 °C; sensitivity to design-point assumption. | `derating_curve_v1.csv` + plot + memo | 2 wk |
| A3 | **OpenMC bounded package (O2).** Simplified core model; KRUSTY benchmark reproduction (target: k-eff within ~500 pcm of published value); temperature coefficients; decay-heat curve vs. ANS-5.1. | Validated model + coefficients + decay-heat input | 3–4 wk |
| A4 | **OpenFOAM air-side model.** Air-cooled condenser/heat-rejection CFD at 25/35/45/55 °C: hot-thin-air mass-flow degradation, approach temperature, capacity cliff. | `derating_curve_v2.csv` + CFD report | 5–6 wk |
| A5 | **Safety case (O3).** 55 °C loss-of-forced-cooling transient; MELCOR if licensed by decision point DP1, else lumped-parameter model with A3's decay heat. | Transient results + margin statement | 3–4 wk |

## 6. Work packages — Stream B (data → siting → economics)

| WP | Content | Deliverable | Est. effort |
|----|---------|-------------|-------------|
| B1 | **Site pool (O4).** Expand 16 named sites to 30–80: mining cadastre operations, MODON industrial cities, coastal desal-adjacent zones, off-grid settlements, giga-projects. Inclusion criteria documented. | Site register (30–80 rows) | 2–3 wk |
| B2 | **Per-site database.** Feature vector per site: NASA POWER climatology (scripted pull), WRI Aqueduct water stress, GASTAT/WorldPop demand proxies, SEC/OSM grid distance, logistics, seismic/exclusion layers. | `sites.parquet` + data dictionary | 3–4 wk |
| B3 | **Derating applicator.** Hourly temp series × curve vN → per-site effective capacity factor (the interface consumer). | Per-site ECF table, auto-regenerated per curve version | 1 wk |
| B4 | **AHP baseline.** Reproduce Proposal-2 weighting on the full pool with the heuristic climate criterion — the defensible before-picture. | Baseline ranking | 2 wk |
| B5 | **RF + SHAP + application matching.** Random Forest cross-validation of AHP scores; SHAP attribution (the WHY); classify sites to application; recommend power class (5/10/20 MWe as 1/2/4 eVinci-class units). | Ranked, explained, classified site list | 3–4 wk |
| B6 | **Economics (O6).** HERON/RAVEN dispatch + IAEA DEEP at top ~5 sites; LCOE/LCOW with/without penalty; inputs as ranges → uncertainty bands; calibrate vs. SAR 1.7/m³. | Economics chapter + figures | 3–4 wk |

## 7. Team structure

Stream ownership **deliberately unassigned** — decide at kickoff (DP2). Skills profile:
Stream A wants thermal/reactor-physics comfort (OpenMC, OpenFOAM, cycle analysis);
Stream B wants Python/data/ML comfort (pandas, scikit-learn, SHAP, geodata).

Both students are KAU Nuclear Engineering, so **both theses need visible nuclear content**:
- Stream A thesis: reactor modeling, validation, safety case — inherently nuclear.
- Stream B thesis: absorbs the *application* of the nuclear physics (per-site derating methodology,
  reactor-technology matching eVinci vs. MMR, power-class scaling) and co-ownership of the safety-case
  interpretation. Frame as "nuclear siting engineering," not generic ML.

The combined paper is joint first-authorship-worthy from both streams; theses partition by stream.

## 8. Milestones (relative — no calendar dates yet)

| M | Gate | Exit criteria |
|---|------|---------------|
| M0 | Kickoff | Interface contract agreed; repo + environment set up; curve **v0** committed; streams assigned (DP2) |
| M1 | Tooling & scope locked | OpenMC runs locally with cross-section data; spec sheet (A1) locked; site register (B1) ≥ 30 sites; MELCOR request sent |
| M2 | First real results | Curve **v1** (A2); site database (B2) assembled; **DP1: MELCOR go/no-go** |
| M3 | Validation & baseline | KRUSTY validation passed (A3); AHP baseline ranking on full pool (B4) |
| M4 | Full fidelity | Curve **v2** (A4); RF + SHAP + classification done (B5) |
| M5 | Integration | Safety case done (A5); physics curve embedded, rankings rerun; **RQ3 sensitivity figure produced** |
| M6 | Economics | LCOE/LCOW at top sites with uncertainty bands (B6) |
| M7 | Writing | Combined paper draft + both thesis drafts |
| M8 | Submission | Paper submitted; theses defended |

Total estimated effort: ~16–19 person-weeks per stream — fits a co-op window with margin if run in parallel.

## 9. Decision points & risks

| # | Decision / risk | Trigger & fallback |
|---|-----------------|--------------------|
| DP1 | **MELCOR access** (Sandia/CSARP agreement — longest external lead time; ask if KACST already holds a license, week 1) | No license by M2 → lumped-parameter safety model; MELCOR becomes future work |
| DP2 | **Stream assignment** | Decide at M0 by preference + skills; swap is cheap before M2, expensive after |
| DP3 | **Journal target** | Decide after M5 from where the strongest result lands: *Applied Energy* / *Energy Conversion & Management* (energy story) vs. *Desalination* (water story) |
| DP4 | **Site pool final count** | If data audit at M2 shows >~50 sites with complete features, cap there; quality of feature vector beats count |
| R1 | eVinci public data too sparse for spec sheet | Fall back to "generic heat-pipe microreactor" anchored harder on KRUSTY + open literature; state assumptions as ranges |
| R2 | OpenFOAM condenser model too heavy | Reduce to 2-D/porous-media representation or correlation-based HX model; v1→v2 delta still reportable |
| R3 | RF overfits small site pool | Regularize, use k-fold CV honestly, lean on AHP + SHAP as primary; RF as cross-validation only (as Proposal 2 intended) |
| — | **Out of scope (hard constraints):** enrichment/HALEU analysis (123-Agreement sensitivity); operational AI / digital twins (no Saudi operating-reactor data) | |

## 10. Toolchain summary

| Layer | Tool | Role |
|-------|------|------|
| Neutronics | **OpenMC** + ENDF/B data | Bounded package: KRUSTY validation, decay heat, temperature coefficients (O2) |
| Cycle | Python (CoolProp) | Derating curve v1 |
| CFD | **OpenFOAM** | Air-side heat rejection → curve v2 |
| Safety | **MELCOR** (DP1) / lumped fallback | 55 °C loss-of-cooling transient |
| Siting | Python: AHP, scikit-learn RF, SHAP | Ranking, explanation, classification |
| Economics | HERON 2.0 / RAVEN / TEAL + IAEA DEEP | Dispatch + LCOE/LCOW |
| Data | NASA POWER, WRI Aqueduct, GASTAT/WorldPop, mining cadastre, MODON, SEC/OSM | Site feature vectors |

All open/unlicensed except MELCOR (agreement-gated, DP1).

## 11. First actions (this week, regardless of stream assignment)

1. Ask Dr. Alzahrani whether KACST holds a MELCOR license → else start CSARP paperwork (only long-lead item).
2. Write the NASA POWER extraction script for the initial 16 sites (an afternoon; produces real data immediately).
3. Commit `derating_curve_v0.csv` (placeholder) + this document to a shared repo — the interface exists from day 1.
4. Begin A1 spec sheet and B1 site-pool expansion in parallel.
