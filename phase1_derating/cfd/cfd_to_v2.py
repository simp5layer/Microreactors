#!/usr/bin/env python3
"""Task 9 (the payoff): inject the CFD-validated heater UA(mdot) law into the
v1.5 cycle model and produce the v2 derating curve (Option 1).

WHAT THIS DOES
--------------
v1.5 assumed the air-side heater UA scales as UA ~ mdot^0.6 anchored at
UA_heater_des = 152.3491 kW/K (from ``cycle_model.hx_entu_v1_5.size_design``).
v2 replaces that ASSUMED scaling with the CFD-VALIDATED Briggs-Young Nu law
(``postprocessing.fit.ua_of_mdot``), still anchored to the same design magnitude
so v2 == v1.5 at the design point exactly. The Briggs-Young Nu exponent (0.681)
is modulated by the reference fin's overall surface efficiency, giving an
effective n_air ~= 0.454 -- SHALLOWER than v1.5's assumed 0.6.

EXPECTED RESULT (the honest finding)
------------------------------------
The ambient-driven air mass-flow range over 25-55 C is only ~4-5%, so the
exact UA-scaling exponent is second-order: the v2 curve lands essentially on
top of v1.5 (penalty @55 C ~= -8.8%, within a few tenths of a point). This
CONFIRMS v1.5: the derating is robust to the precise air-side UA law used.

Outputs (phase1_derating/results/):
  derating_curve_v2.csv              v2 curve with the CFD-injected heater law
  derating_curve_v1_5_vs_v2.png      v1.5 vs v2 comparison (net_MWe_frac_vs25C)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_CFD_ROOT = Path(__file__).resolve().parent               # .../phase1_derating/cfd
_PHASE1 = _CFD_ROOT.parent                                 # .../phase1_derating
for _p in (_CFD_ROOT, _PHASE1 / "cycle_model"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from postprocessing.fit import ua_of_mdot                  # noqa: E402
from geometry.finned_tube import REFERENCE                 # noqa: E402
from hx_entu_v1_5 import PARAMS, curve, size_design        # noqa: E402

RESULTS = _PHASE1 / "results"

# Fallbacks for the CFD scalars when a minimal json omits them. mdot_des falls
# back to v1.5's live size_design anchor so the design point reproduces exactly.
_RE_DES_FALLBACK = 8368
_PR_FALLBACK = 0.69
_K_AIR_DES_FALLBACK = 0.06113


def build_v2_curve(json_path: str, T_C=None) -> pd.DataFrame:
    """Build the v2 derating curve by injecting the CFD-validated heater UA law.

    Loads the CFD correlation json, constructs an anchored ``ua_law(mdot)`` from
    ``ua_of_mdot`` (magnitude = UA_design_kW_per_K, exponent = CFD Briggs-Young),
    injects it into a copy of v1.5's PARAMS, and regenerates the derating curve.
    Missing CFD scalars (mdot_des/Re_des/Pr/k_air) fall back to v1.5's design
    anchors / the CFD design values so the design point still reproduces 5 MWe.
    """
    with open(json_path) as fh:
        corr = json.load(fh)

    mdot_des_fallback = float(size_design(PARAMS)["mdot_des"])
    UA_des_kW = float(corr["UA_design_kW_per_K"])
    mdot_des = float(corr.get("mdot_des_kg_s", mdot_des_fallback))
    Re_des = float(corr.get("Re_des", _RE_DES_FALLBACK))
    Pr = float(corr.get("Pr", _PR_FALLBACK))
    k_air = float(corr.get("k_air_des", _K_AIR_DES_FALLBACK))

    ua_law = lambda mdot: ua_of_mdot(
        mdot, REFERENCE, UA_des_kW=UA_des_kW, mdot_des=mdot_des,
        Re_des=Re_des, Pr=Pr, k_air=k_air)

    params_v2 = {**PARAMS, "ua_law": ua_law}
    T = np.arange(25.0, 55.0 + 1e-9, 1.0) if T_C is None else np.asarray(T_C, dtype=float)
    df, _dz = curve(T, params_v2)
    return df


def _at(df: pd.DataFrame, T: float) -> pd.Series:
    return df.loc[np.isclose(df.ambient_temp_C, T)].iloc[0]


def main() -> None:
    corr_path = _CFD_ROOT / "results" / "cfd_correlation.json"
    df = build_v2_curve(str(corr_path))

    RESULTS.mkdir(exist_ok=True)
    out_csv = RESULTS / "derating_curve_v2.csv"
    df.to_csv(out_csv, index=False)

    v15 = pd.read_csv(RESULTS / "derating_curve_v1_5.csv")

    # ---- headline
    def slope(d):
        return (_at(d, 25).net_MWe_frac_vs25C - _at(d, 45).net_MWe_frac_vs25C) / 20 * 100

    print("=== v2 derating (CFD-validated Briggs-Young heater UA law injected into v1.5) ===")
    with open(corr_path) as fh:
        c = json.load(fh)
    print(f"injected UA law: UA_des={c['UA_design_kW_per_K']:.4f} kW/K @ mdot_des="
          f"{c['mdot_des_kg_s']:.4f} kg/s, n_air_effective~{c['n_air_effective']:.4f} "
          f"(v1.5 assumed {c['v1_5_assumed_n_air']})")
    print(f"net @25C = {_at(df, 25).net_MWe:.3f} MWe, plant_eff={_at(df, 25).plant_efficiency:.3f}, "
          f"regime {_at(df, 25).regime}")
    for T in (25, 35, 45, 55):
        r = _at(df, T)
        print(f"  @{T}C: {r.net_MWe:.3f} MWe ({r.net_MWe_frac_vs25C*100:.1f}%)  TIT={r.TIT_C:.0f}C  "
              f"regime {r.regime}  plant_eff={r.plant_efficiency:.3f}")
    pen_v2 = (1 - _at(df, 55).net_MWe_frac_vs25C) * 100
    pen_v15 = (1 - _at(v15, 55).net_MWe_frac_vs25C) * 100
    print(f"mean electric derating 25->45C: {slope(df):.2f} %/degC; penalty @55C: -{pen_v2:.1f}%")

    # ---- v1.5 vs v2 delta at 55 C
    d_mwe = _at(df, 55).net_MWe - _at(v15, 55).net_MWe
    d_pct = _at(df, 55).net_MWe_frac_vs25C * 100 - _at(v15, 55).net_MWe_frac_vs25C * 100
    print("--- v1.5 vs v2 @55C ---")
    print(f"  v1.5: {_at(v15,55).net_MWe:.3f} MWe ({_at(v15,55).net_MWe_frac_vs25C*100:.1f}%), penalty -{pen_v15:.1f}%")
    print(f"  v2  : {_at(df,55).net_MWe:.3f} MWe ({_at(df,55).net_MWe_frac_vs25C*100:.1f}%), penalty -{pen_v2:.1f}%")
    print(f"  delta v2-v1.5 @55C: {d_mwe*1000:+.1f} kWe ({d_pct:+.2f} pts of %-vs-25C; "
          f"penalty {-(pen_v2-pen_v15):+.2f} pts)")

    # ---- comparison plot (net_MWe_frac_vs25C)
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.plot(v15.ambient_temp_C, v15.net_MWe_frac_vs25C * 100, color="#c62828", lw=2.4,
            ls="--", label="v1.5 (assumed UA~mdot^0.6)")
    ax.plot(df.ambient_temp_C, df.net_MWe_frac_vs25C * 100, color="#1565c0", lw=2.0,
            label=f"v2 (CFD Briggs-Young, n~{c['n_air_effective']:.3f})")
    ax.set_xlabel("Ambient temperature (°C)")
    ax.set_ylabel("Net electric power (% of 25 °C)")
    ax.set_xlim(25, 55)
    ax.set_title("v2 CFD-injected heater UA law vs v1.5\n"
                 f"penalty @55 °C: v1.5 -{pen_v15:.1f}%  vs  v2 -{pen_v2:.1f}%  "
                 f"(delta {-(pen_v2-pen_v15):+.2f} pts) — v2 confirms v1.5", fontsize=10)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    out_png = RESULTS / "derating_curve_v1_5_vs_v2.png"
    fig.savefig(out_png, dpi=150)
    print(f"\nwrote: {out_csv}\n       {out_png}")


if __name__ == "__main__":
    main()
