# Project Pipeline Diagrams

Rendered views of the combined derating → siting workflow. Mermaid source (paste into
GitHub / VS Code / https://mermaid.live to view). Kept in sync with `DECISIONS_LOG.md`.

## 1. Overall combined-project pipeline

```mermaid
flowchart TD
    ARIS["IAEA ARIS eVinci datasheet"]
    CLIM["NASA POWER climate (per-site T, wind)"]
    GEO["Aqueduct / WorldPop / OSM grid / site register"]

    subgraph SA["Stream A — Physics / Derating"]
        A1["A1: Reference spec sheet<br/>15 MWth / 5 MWe, open-air Brayton"]
        V1["v1: Brayton cycle model<br/>calib. net 33%, TIT 742°C<br/>−17.7% @55°C, 0.60 %/°C"]
        V15["v1.5: ε-NTU HX + energy balance<br/>(adversarially verified)<br/>UA≈152 kW/K ASSUMED"]
        CFD["CFD v2: finned-tube unit cell<br/>OpenFOAM / Docker → UA(ṁ), Δp(ṁ)"]
        V2["v2 derating curve<br/>CFD-grounded UA"]
        A1 --> V1 --> V15 --> CFD --> V2
    end

    DC{{"Derating curve<br/>net MWe & efficiency vs ambient<br/>(the ONE interface)"}}
    V2 --> DC

    subgraph SB["Stream B — Siting"]
        AHP["AHP baseline ranking"]
        RF["Random Forest + SHAP (WHY)"]
        USE["Use-case match + power class (WHAT)"]
        ECON["Economics: LCOE / LCOW"]
        AHP --> RF --> USE --> ECON
    end

    ARIS --> A1
    CLIM --> V2
    DC -->|"per-site effective capacity factor"| AHP
    GEO --> AHP
    CLIM -. "per-site wind (WS2M) — optional recirc study" .-> CFD
```

## 2. CFD v2 implementation pipeline (the 10-task plan)

```mermaid
flowchart TD
    T1["T1 · Scaffold + Docker OpenFOAM smoke test"]
    T2["T2 · Geometry module (finned_tube.py) — TDD"]
    T3["T3 · Validation correlations (Briggs–Young) — TDD"]
    T4["T4 · Parametric STL generator — TDD"]
    T5["T5 · OpenFOAM case: mesh + converge<br/>GATE: y⁺ ≤ 2, residuals < 1e-4"]
    T6["T6 · Extract h,f + Reynolds sweep (6 pts)"]
    T7["T7 · Mesh-independence GATE (<3%)"]
    T8["T8 · Fit Nu/f + validation<br/>GATE: ≤20% vs Briggs–Young"]
    T9["T9 · Inject UA law into v1.5 → v2 curve — TDD"]
    T10["T10 · Documentation (README, spec §4d, D12)"]

    T1 --> T2
    T2 --> T3
    T2 --> T4
    T4 --> T5
    T5 --> T6 --> T7 --> T8
    T3 --> T8
    T8 --> T9 --> T10

    FALLBACK["Fallback: if T8 > 20%, correlations<br/>ARE the air-side model → v2 not blocked"]
    T8 -.-> FALLBACK -.-> T9
```

## Legend
- Solid arrow = data/artifact dependency · dashed = optional/fallback path.
- `{{ }}` = the single interface artifact (`derating_curve_vN.csv`) coupling the two streams.
- GATE = a hard acceptance check that must pass before the next step is trusted.
