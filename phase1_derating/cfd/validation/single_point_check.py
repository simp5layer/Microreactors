"""Single-point validation of the converged CFD v2 heater unit cell against the
Briggs-Young (heat transfer) and Robinson-Briggs (friction) correlations.

All CFD numbers below are MEASURED from the converged rhoSimpleFoam solve
(Time 466) in ``phase1_derating/cfd/heater_unitcell`` -- OpenFOAM is NOT re-run
here. The postProcessing tree is gitignored, so the measured values are frozen
as documented constants (they match postprocessing.extract on the live case).

Run:  cd phase1_derating/cfd && python3 -m validation.single_point_check
"""
from __future__ import annotations

import math

from geometry.finned_tube import REFERENCE, min_flow_area_per_pitch
from correlations.finned_tube_corr import briggs_young_nu, briggs_young_f

# --------------------------------------------------------------------------
# MEASURED CFD values (converged case, Time 466)
# --------------------------------------------------------------------------
Q        = 256.30      # wallHeatFlux integral over `tube` patch (W)
A_WETTED = 9.0165e-3   # actual tube patch area (m^2); 329016 faces, fins clipped
DP       = 148.4       # p_in - p_out = 200148.4 - 200000.0 (Pa)
T_WALL   = 1033.0      # isothermal tube wall temperature (K)
T_IN     = 740.0       # air inlet temperature (K)
P_HEAT   = 2.0e5       # heater-side static pressure (Pa)
U_IN     = 6.3623      # inlet approach velocity (m/s)
A_INLET  = 5.773e-4    # inlet patch flow area (m^2)
N_ROWS   = 1           # single tube row in the streamwise direction
YPLUS_MEAN = 0.244     # tube-patch mean y+ (well-resolved)
YPLUS_MAX  = 4.63      # tube-patch max y+

d_o = REFERENCE.d_o    # tube outer diameter (m)

# --------------------------------------------------------------------------
# Property models  (STATED explicitly)
#   rho   : ideal gas, rho = p/(R T),  R = 287 J/kg/K
#   mu    : Sutherland, mu = 1.458e-6 T^1.5 / (T + 110.4)
#   cp    : 1080 J/kg/K, representative high-temperature air (JANAF-band value)
#   k_air : self-consistent with a fixed high-T air Prandtl, Pr = 0.69,
#           via k = mu*cp/Pr. This makes Pr an explicit modelling choice rather
#           than a derived number, and keeps Nu = h*d_o/k consistent with the
#           Pr fed to Briggs-Young.
# --------------------------------------------------------------------------
R_AIR = 287.0
CP    = 1080.0
PR    = 0.69


def mu_sutherland(T: float) -> float:
    return 1.458e-6 * T ** 1.5 / (T + 110.4)


def k_air(T: float) -> float:
    return mu_sutherland(T) * CP / PR      # from Pr = mu*cp/k


def rho_ideal(T: float, p: float = P_HEAT) -> float:
    return p / (R_AIR * T)


def _pct(a: float, b: float) -> float:
    return 100.0 * (a - b) / b


def _band(dev_pct: float, tol: float = 20.0) -> str:
    return "within +-%.0f%%" % tol if abs(dev_pct) <= tol else "OUTSIDE +-%.0f%%" % tol


def main() -> None:
    # ---- (1) inlet density + mass flow --------------------------------------
    rho_in = rho_ideal(T_IN)
    mdot = rho_in * U_IN * A_INLET

    # ---- (3) outlet temperature, bulk-mean, film temperature ----------------
    T_out = T_IN + Q / (mdot * CP)
    T_bulk_mean = 0.5 * (T_IN + T_out)
    T_film = 0.5 * (T_WALL + T_bulk_mean)

    # Properties at the film temperature (single, physically-standard choice).
    mu_f = mu_sutherland(T_film)
    k_f = k_air(T_film)
    Pr_f = mu_f * CP / k_f                  # = PR by construction (diagnostic)

    # ---- (3) h two ways -----------------------------------------------------
    q_avg = Q / A_WETTED                    # area-averaged wall heat flux (W/m^2)

    dT_inlet = T_WALL - T_IN
    h_inlet = q_avg / dT_inlet

    dT_in = T_WALL - T_IN
    dT_out = T_WALL - T_out
    lmtd = (dT_in - dT_out) / math.log(dT_in / dT_out)
    h_lmtd = q_avg / lmtd

    # ---- (4) Nu_CFD (both h's), evaluated at T_film -------------------------
    Nu_inlet = h_inlet * d_o / k_f
    Nu_lmtd = h_lmtd * d_o / k_f

    # ---- (5) Reynolds number at the minimum-flow section --------------------
    A_min = 3.0 * min_flow_area_per_pitch(REFERENCE)   # domain = 3 fin pitches
    G_max = mdot / A_min                                # max mass flux (kg/m^2/s)
    U_max = mdot / (rho_in * A_min)                     # max velocity (ref. rho_in)
    Re = G_max * d_o / mu_f

    # ---- (6) f_CFD ----------------------------------------------------------
    f_cfd = DP / (0.5 * rho_in * U_max ** 2 * N_ROWS)

    # ---- (7) correlations at that Re ----------------------------------------
    Nu_by = briggs_young_nu(Re, Pr_f, REFERENCE)
    f_rb = briggs_young_f(Re, REFERENCE)

    # ---- (8) deviations -----------------------------------------------------
    dev_Nu_inlet = _pct(Nu_inlet, Nu_by)
    dev_Nu_lmtd = _pct(Nu_lmtd, Nu_by)
    dev_f = _pct(f_cfd, f_rb)

    # ---- report -------------------------------------------------------------
    line = "-" * 66
    print(line)
    print("CFD v2 heater unit cell -- single-point validation (Time 466)")
    print(line)
    print("MEASURED CFD inputs")
    print("  Q (wallHeatFlux integral, tube)      = %10.3f  W" % Q)
    print("  A_wetted (actual tube patch)         = %10.4e  m^2" % A_WETTED)
    print("  dp = p_in - p_out                    = %10.3f  Pa" % DP)
    print("  T_wall / T_in                        = %6.1f / %6.1f  K" % (T_WALL, T_IN))
    print("  p_heater                             = %10.4e  Pa" % P_HEAT)
    print("  U_in / A_inlet                       = %6.4f m/s / %8.4e m^2" % (U_IN, A_INLET))
    print("  y+ tube  mean / max                  = %6.3f / %6.3f" % (YPLUS_MEAN, YPLUS_MAX))
    print("  N_rows                               = %10d" % N_ROWS)
    print(line)
    print("PROPERTY MODEL   rho=p/RT (R=287) | mu=Sutherland | cp=%.0f | Pr=%.2f, k=mu*cp/Pr" % (CP, PR))
    print("  rho_in  = p/(R T_in)                 = %10.5f  kg/m^3" % rho_in)
    print("  mdot    = rho_in U_in A_inlet        = %10.5e  kg/s" % mdot)
    print("  T_out   = T_in + Q/(mdot cp)         = %10.3f  K" % T_out)
    print("  T_bulk_mean = (T_in+T_out)/2         = %10.3f  K" % T_bulk_mean)
    print("  T_film  = (T_wall+T_bulk_mean)/2     = %10.3f  K" % T_film)
    print("  mu(T_film)                           = %10.5e  Pa.s" % mu_f)
    print("  k_air(T_film)                        = %10.5f  W/m/K" % k_f)
    print("  Pr(T_film)  (diagnostic)             = %10.4f" % Pr_f)
    print(line)
    print("HEAT TRANSFER")
    print("  q''_avg = Q/A_wetted                 = %10.2f  W/m^2" % q_avg)
    print("  h_inlet = q''/(T_wall-T_in)          = %10.3f  W/m^2/K  (dT=%.1f)" % (h_inlet, dT_inlet))
    print("  LMTD                                 = %10.3f  K" % lmtd)
    print("  h_LMTD  = q''/LMTD                   = %10.3f  W/m^2/K" % h_lmtd)
    print("  Nu_CFD(inlet) = h_inlet d_o/k        = %10.3f" % Nu_inlet)
    print("  Nu_CFD(LMTD)  = h_LMTD  d_o/k        = %10.3f" % Nu_lmtd)
    print(line)
    print("FRICTION / REYNOLDS")
    print("  A_min(domain) = 3*min_flow_area      = %10.4e  m^2" % A_min)
    print("  G_max = mdot/A_min                   = %10.4f  kg/m^2/s" % G_max)
    print("  U_max = mdot/(rho_in A_min)          = %10.4f  m/s" % U_max)
    print("  Re = G_max d_o / mu(T_film)          = %10.1f" % Re)
    print("  f_CFD = dp/(0.5 rho_in U_max^2 N)    = %10.4f" % f_cfd)
    print(line)
    print("CORRELATIONS at Re = %.0f" % Re)
    print("  Nu_BY  (Briggs-Young, Pr=%.2f)       = %10.3f" % (Pr_f, Nu_by))
    print("  f_RB   (Robinson-Briggs, per row)    = %10.4f" % f_rb)
    print(line)
    print("DEVIATIONS  (CFD - corr)/corr")
    print("  Nu_CFD(inlet) vs Nu_BY : %+7.1f %%   [%s]" % (dev_Nu_inlet, _band(dev_Nu_inlet)))
    print("  Nu_CFD(LMTD)  vs Nu_BY : %+7.1f %%   [%s]" % (dev_Nu_lmtd, _band(dev_Nu_lmtd)))
    print("  f_CFD         vs f_RB  : %+7.1f %%   [%s]" % (dev_f, _band(dev_f)))
    print(line)


if __name__ == "__main__":
    main()
