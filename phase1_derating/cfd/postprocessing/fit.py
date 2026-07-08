"""CFD-validated air-side UA(mdot) law for the v2 open-air Brayton heater
-> ``results/cfd_correlation.json``  (Option 1).

WHY THIS SHAPE (no CFD sweep is fitted here)
--------------------------------------------
Under Option 1 there is no multi-point CFD sweep to regress. Instead, the CFD
unit cell (``phase1_derating/cfd/heater_unitcell``, converged Time 466) was used
to VALIDATE the published Briggs-Young air-side heat-transfer correlation at the
single design Reynolds number:

    Re = 8368 :  Nu_CFD(LMTD) = 45.9   vs   Nu_BY = 54.1   (-15.2 %, within +-20 %)

Heat transfer therefore validated, so we ADOPT the (now CFD-validated) Briggs-
Young Nu law as the air-side model and use it to build UA(mdot). Friction did
NOT validate (f_CFD = 1.688 vs f_RB = 0.287, +488.7 %), so the Robinson-Briggs
Delta-p scaling below is an order-of-magnitude estimate only and is deliberately
NOT wired into the v2 power balance.

RELATION TO v1.5
----------------
v1.5 assumed the heater UA scales as UA ~ mdot^0.6 anchored at
UA_heater_des = 152.3491 kW/K, mdot_des = 54.3699 kg/s (from
``cycle_model.hx_entu_v1_5.size_design``). v2 keeps that 152.3491 magnitude
(computed live so v2 == v1.5 at the design point exactly) but replaces the
assumed 0.6 exponent with the CFD-validated Briggs-Young Nu law, modulated by
the overall fin/surface efficiency eta_o. The result: the effective UA~mdot^n
exponent lands n_air_effective ~= 0.45 -- SHALLOWER than v1.5's assumed 0.6,
not steeper. Heat transfer alone scales steeper (h ~ Re^0.681), but the
reference fin's low, h-sensitive efficiency (eta_fin ~= 0.53 at design) means
eta_o FALLS as mdot rises (dln(eta_o)/dln(mdot) ~= -0.23), and that
modulation dominates: 0.681 - 0.23 ~= 0.45. Practically this is second-order:
the ambient-driven mdot range over 25-55 C is only ~4-5%, so the v2 curve
stays essentially on top of v1.5 -- this CONFIRMS v1.5, for the subtler
reason that the derating is robust to the exact UA scaling law used.

PROPERTY MODEL (reused from ``validation.single_point_check`` for consistency)
-----------------------------------------------------------------------------
    R_air = 287 J/kg/K ; cp = 1080 J/kg/K ; Pr = 0.69 (explicit modelling choice)
    mu    = Sutherland  1.458e-6 * T^1.5 / (T + 110.4)
    k_air = mu * cp / Pr
k_air is evaluated at the CFD design FILM temperature (same construction the
single-point validation used), so the design point here is exactly the CFD
validation point.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

# --- make both the cfd package tree and the phase1_derating tree importable,
#     independent of the caller's cwd (cfd/ has geometry|correlations|validation;
#     phase1_derating/ has cycle_model) -------------------------------------
_CFD_ROOT = Path(__file__).resolve().parent.parent          # .../phase1_derating/cfd
_PHASE1 = _CFD_ROOT.parent                                   # .../phase1_derating
for _p in (_CFD_ROOT, _PHASE1):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from geometry.finned_tube import (                           # noqa: E402
    FinnedTube, REFERENCE, air_area_per_pitch, fin_efficiency,
)
from correlations.finned_tube_corr import (                  # noqa: E402
    briggs_young_nu, briggs_young_f,
)
from validation.single_point_check import (                  # noqa: E402
    PR, CP, k_air, rho_ideal,
    Q as Q_CFD, T_WALL, T_IN, U_IN, A_INLET,
)

# --------------------------------------------------------------------------
# Frozen scalars
# --------------------------------------------------------------------------
RE_DES = 8368        # CFD design/validation Reynolds number (tube-OD, min section)
M_NU = 0.681         # Briggs-Young Re-exponent in Nu = C_nu * Re^m * Pr^(1/3)
P_F = -0.316         # Robinson-Briggs Re-exponent in f = C_f * Re^p
L_TUBE_M = 2.0       # stated tube length for the n_tubes DIAGNOSTIC (not a fit)
DP_DES_PA = 148.4    # p_in - p_out at the CFD design point (informational only)

# Frozen single-point validation outcome (measured, converged Time 466; matches
# ``validation.single_point_check``). Heat transfer validated; friction did not.
VALIDATION = {
    "Re": 8368,
    "Nu_cfd": 45.9, "Nu_by": 54.1, "Nu_dev_pct": -15.2,
    "f_cfd": 1.688, "f_rb": 0.287, "f_dev_pct": 488.7,
}


def design_film_temperature_K() -> float:
    """CFD design film temperature, reconstructed exactly as the single-point
    validation does: T_film = (T_wall + T_bulk_mean)/2 with the measured inlet
    velocity/area giving mdot and hence T_out."""
    rho_in = rho_ideal(T_IN)
    mdot = rho_in * U_IN * A_INLET
    T_out = T_IN + Q_CFD / (mdot * CP)
    T_bulk_mean = 0.5 * (T_IN + T_out)
    return 0.5 * (T_WALL + T_bulk_mean)


K_AIR_DES = k_air(design_film_temperature_K())   # W/m/K at the CFD design film T


# --------------------------------------------------------------------------
# General power-law fit utility
# --------------------------------------------------------------------------
def fit_power_law(x, y) -> tuple[float, float]:
    """Least-squares fit y = C * x^m via a log-log linear regression.

    Returns (C, m). Uses ``np.polyfit(log x, log y, 1)`` -> [m, ln C].
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m, lnC = np.polyfit(np.log(x), np.log(y), 1)
    return float(np.exp(lnC)), float(m)


# --------------------------------------------------------------------------
# Overall (fin + bare) surface efficiency
# --------------------------------------------------------------------------
def _fin_area_per_pitch(ft: FinnedTube) -> float:
    """Fin-only air-side area over one pitch: 2 annular faces + fin edge
    (the finned fraction of ``air_area_per_pitch``; excludes the bare tube)."""
    r_i, r_o = ft.d_o / 2, ft.d_o / 2 + ft.fin_h
    faces = 2 * math.pi * (r_o ** 2 - r_i ** 2)
    edge = 2 * math.pi * r_o * ft.fin_t
    return faces + edge


def overall_surface_efficiency(h: float, ft: FinnedTube) -> float:
    """eta_o = 1 - (A_fin/A_tot) * (1 - eta_fin(h)).

    A_fin = 2 fin faces + fin edge over one pitch; A_tot = air_area_per_pitch(ft)
    (fins + edge + bare tube). Falls with h because a hotter/harder-driven fin
    develops a larger root-to-tip temperature drop (lower fin efficiency)."""
    A_fin = _fin_area_per_pitch(ft)
    A_tot = air_area_per_pitch(ft)
    return 1.0 - (A_fin / A_tot) * (1.0 - fin_efficiency(h, ft))


# --------------------------------------------------------------------------
# The anchored, CFD-validated Briggs-Young UA(mdot) law
# --------------------------------------------------------------------------
def ua_of_mdot(mdot: float, ft: FinnedTube, UA_des_kW: float, mdot_des: float,
               Re_des: float, Pr: float, k_air: float) -> float:
    """Air-side heater UA [kW/K] at mass flow ``mdot``.

    Re tracks mass flow linearly (Re = Re_des * mdot/mdot_des). The Briggs-Young
    Nu ratio gives the raw ~Re^0.681 (~mdot^0.681) scaling; the overall surface
    efficiency ratio modulates it (eta_o rises as mdot falls). Anchored so that
    ``ua_of_mdot(mdot_des, ...) == UA_des_kW`` exactly.
    """
    ratio = mdot / mdot_des
    Re = Re_des * ratio
    Nu = briggs_young_nu(Re, Pr, ft)
    Nu_des = briggs_young_nu(Re_des, Pr, ft)
    h = Nu * k_air / ft.d_o
    h_des = Nu_des * k_air / ft.d_o
    return (UA_des_kW * (Nu / Nu_des)
            * (overall_surface_efficiency(h, ft)
               / overall_surface_efficiency(h_des, ft)))


def dp_of_mdot(mdot: float, ft: FinnedTube, Re_des: float, mdot_des: float,
               dp_des_Pa: float) -> float:
    """INFORMATIONAL air-side Delta-p [Pa] from the Robinson-Briggs friction
    factor: Delta-p ~ f(Re) * (mdot/mdot_des)^2, anchored at the design point.

    WARNING: friction did NOT validate against the CFD (f_CFD = 1.688 vs
    f_RB = 0.287, +489 %). This is an order-of-magnitude estimate only and is
    NOT used in the v2 power balance.
    """
    ratio = mdot / mdot_des
    Re = Re_des * ratio
    return dp_des_Pa * (briggs_young_f(Re, ft) / briggs_young_f(Re_des, ft)) * ratio ** 2


# --------------------------------------------------------------------------
# Correlation-coefficient closed forms (for the emitted json)
# --------------------------------------------------------------------------
def C_nu(ft: FinnedTube) -> float:
    """Re^0.681 coefficient in Nu = C_nu * Re^m * Pr^(1/3) for this geometry."""
    s = ft.fin_pitch - ft.fin_t
    return 0.134 * (s / ft.fin_h) ** 0.2 * (s / ft.fin_t) ** 0.1134


def C_f(ft: FinnedTube) -> float:
    """Re^-0.316 coefficient in f = C_f * Re^p (Robinson-Briggs, per row)."""
    return 9.465 * (ft.S_T / ft.d_o) ** (-0.927)


# --------------------------------------------------------------------------
# Emit results/cfd_correlation.json
# --------------------------------------------------------------------------
def write_cfd_correlation_json(path, ft: FinnedTube = REFERENCE) -> dict:
    """Compute and write ``cfd_correlation.json``; return the dict written."""
    # live v1.5 design anchors (imported lazily: pulls in pandas/matplotlib)
    from cycle_model.hx_entu_v1_5 import size_design, PARAMS
    dz = size_design(PARAMS)
    UA_des_kW = float(dz["UA_heater"])
    mdot_des = float(dz["mdot_des"])

    # effective air-side exponent: regress the anchored law over +-30% mdot
    mdots = np.linspace(0.7, 1.3, 25) * mdot_des
    ua = np.array([ua_of_mdot(md, ft, UA_des_kW, mdot_des, RE_DES, PR, K_AIR_DES)
                   for md in mdots])
    _, n_air_effective = fit_power_law(mdots, ua)

    # n_tubes DIAGNOSTIC: how many L_TUBE_M tubes reproduce UA_des at design h
    Nu_des = briggs_young_nu(RE_DES, PR, ft)
    h_des = Nu_des * K_AIR_DES / ft.d_o
    eta_o_des = overall_surface_efficiency(h_des, ft)
    A_air_per_tube = air_area_per_pitch(ft) * L_TUBE_M / ft.fin_pitch  # m^2/tube
    n_tubes = (UA_des_kW * 1000.0) / (A_air_per_tube * eta_o_des * h_des)

    out = {
        "C_nu": C_nu(ft),
        "m": M_NU,
        "C_f": C_f(ft),
        "p": P_F,
        "Re_des": RE_DES,
        "Pr": PR,
        "k_air_des": K_AIR_DES,
        "UA_design_kW_per_K": UA_des_kW,
        "mdot_des_kg_s": mdot_des,
        "n_air_effective": float(n_air_effective),
        "v1_5_assumed_n_air": 0.6,
        "n_air_effective_note": (
            "Effective UA~mdot^n from a log-log fit of the anchored Briggs-Young "
            "law over mdot=0.7-1.3*mdot_des. It is BELOW the raw Re-exponent "
            "m=0.681 AND below v1.5's assumed 0.6 because the REFERENCE fin "
            "(0.5 mm thick, 12 mm tall, k_fin=25) has a low, h-sensitive fin "
            "efficiency (~0.53 at design): eta_o swings ~0.62->0.54 across the "
            "range, giving dln(eta_o)/dln(mdot) ~ -0.23. Finding: including fin "
            "efficiency, the air-side UA scaling is SHALLOWER than v1.5's 0.6, "
            "not the steeper 0.66-0.68 originally anticipated."
        ),
        "n_tubes": float(n_tubes),
        "n_tubes_is_diagnostic": True,
        "L_tube_m": L_TUBE_M,
        "notes": (
            "Option 1: air-side law = CFD-VALIDATED Briggs-Young Nu (no CFD sweep "
            "fit). UA anchored to v1.5 152.3491 kW/K @ mdot_des; exponent m=0.681 "
            "modulated by overall surface efficiency -> n_air_effective. Friction "
            "did NOT validate (+488.7%); C_f/p and dp_of_mdot are informational "
            "only and NOT wired into the v2 power balance. n_tubes is a diagnostic "
            "count for L_tube_m."
        ),
        "validation": dict(VALIDATION),
    }

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")
    return out


def main() -> None:
    out_path = _CFD_ROOT / "results" / "cfd_correlation.json"
    d = write_cfd_correlation_json(out_path)
    print("wrote", out_path)
    print("  UA_design      = %.4f kW/K  (v1.5 anchor)" % d["UA_design_kW_per_K"])
    print("  mdot_des       = %.4f kg/s  (v1.5 anchor)" % d["mdot_des_kg_s"])
    print("  Re_des         = %d" % d["Re_des"])
    print("  Pr / k_air_des = %.2f / %.5f W/m/K" % (d["Pr"], d["k_air_des"]))
    print("  m (Briggs-Young Re-exponent) = %.3f" % d["m"])
    print("  n_air_effective = %.4f   (v1.5 assumed %.1f; SHALLOWER, not steeper --"
          % (d["n_air_effective"], d["v1_5_assumed_n_air"]))
    print("                          strong fin-efficiency modulation, see note)")
    print("  n_tubes (diagnostic, L=%.1f m) = %.1f" % (d["L_tube_m"], d["n_tubes"]))


if __name__ == "__main__":
    main()
