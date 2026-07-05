#!/usr/bin/env python3
"""
v1 derating curve (calibration v1.1) — eVinci-class heat-pipe microreactor, open-air Brayton PCS.

Physics (why the desert penalty is real, and larger than Carnot):
  The core delivers a fixed 15 MWth via Na heat pipes regardless of weather. ALL ambient
  sensitivity is in the OPEN-AIR Brayton power-conversion system (ARIS 2024), which breathes
  ambient air. Two compounding effects as ambient T rises:
    (1) Compressor inlet temperature = ambient  -> compressor work rises, net specific work falls.
    (2) Intake air density falls (rho ~ 1/T) -> at fixed corrected speed the machine swallows
        less MASS flow.  Power = mdot * w_net, so BOTH factors cut output -> the classic
        gas-turbine "hot-day derating", ~0.5-0.9 %/degC, several times the Carnot slope.

Modeling choices (locked with the user):
  * Anchor / normalize the curve to 25 degC (report output relative to 25 degC).
  * Electricity-only (CHP is a later extension).
  * Air-standard constant properties (cp, gamma). CoolProp variable-property air = a later refinement.

CALIBRATION v1.1 (2026-07-04) — the tune:
  v1.0 fixed TIT and solved eta_mech, which landed at 0.971 (only ~3% balance-of-plant loss = too
  optimistic). v1.1 inverts it on the principle "pin the well-characterized quantity, solve for the
  unknown one":
    * FIX eta_mech = 0.93 (generator+mechanical+parasitic, documented small-genset value).
    * SOLVE turbine-inlet temperature (TIT) so net efficiency = 33% (= 5 MWe / 15 MWth) at 25 degC.
    * VERIFY the solved TIT lands in the Na heat-pipe band (650-750 degC) -> physical consistency check.
    * Baseline PR lowered 3.5 -> 3.0: recuperated cycles gain efficiency at low PR, and PR=3.5 pushed
      the solved TIT to ~756 degC (just over the heat-pipe ceiling) -> PR=3.0 keeps it in-band.
  TIT is genuinely non-public and design-specific, so solving for it (rather than assuming it) is the
  honest calibration; BOP losses are well-known, so fixing them is safe.

Every remaining non-public parameter is swept -> SENSITIVITY. Absolute numbers carry that uncertainty;
the *shape* (%/degC) is robust, which the band shows.

Outputs (results/):
  derating_curve_v1.csv              baseline curve (interface schema for Phase 2 / CFD)
  derating_curve_v1_sensitivity.csv  min/max envelope over the assumption sweep
  derating_curve_v1.png              publication-style figure
"""

from __future__ import annotations
import itertools
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------- constants / anchors
T0_C = 25.0                     # design anchor: normalize the curve to 25 degC
T0_K = T0_C + 273.15
P_ATM = 101.325                 # kPa, sea-level intake (site elevation = a per-site refinement in Phase 2)
Q_REACTOR_MW = 15.0             # ARIS nameplate thermal (heat into the cycle at design)
P_NET_NAMEPLATE_MWE = 5.0       # ARIS nameplate electric
ETA_NET_TARGET = P_NET_NAMEPLATE_MWE / Q_REACTOR_MW   # 0.3333...

CP = 1.005                      # kJ/kg-K, air
GAMMA = 1.40
K = (GAMMA - 1.0) / GAMMA

HEATPIPE_BAND_C = (650.0, 750.0)  # Na heat-pipe TIT plausibility band (physical consistency gate)

# ----------------------------------------------------------------------------- baseline assumptions
# eta_mech is now FIXED (calibration input); TIT is SOLVED (calibration output).
PARAMS = dict(
    eta_mech=0.93,   # generator+mechanical+parasitic, lumped (small-genset literature ~0.90-0.94)
    PR=3.0,          # compressor pressure ratio (recuperated microturbine; low PR favours efficiency)
    eta_c=0.82,      # compressor isentropic efficiency (small machine)
    eta_t=0.85,      # turbine isentropic efficiency
    eps_recup=0.88,  # recuperator effectiveness
    mdot_law="corrected",   # "corrected": mdot ~ p/sqrt(T) (compressor similarity); "density": mdot ~ p/T
    TIT_C=None,      # SOLVED by calibrate(); placeholder
)

# assumption ranges for the sensitivity envelope (TIT is re-solved for each combo)
SENSITIVITY = dict(
    eta_mech=[0.90, 0.93, 0.95],
    PR=[2.5, 3.0, 3.5],
    mdot_law=["corrected", "density"],
)


# ----------------------------------------------------------------------------- cycle
def brayton_specific(T1_K: float, TIT_C: float, p: dict) -> dict:
    """Open recuperated Brayton per unit mass at compressor inlet temp T1_K. Returns kJ/kg + etas."""
    TIT_K = TIT_C + 273.15
    PR = p["PR"]
    # compressor 1->2
    T2s = T1_K * PR**K
    T2 = T1_K + (T2s - T1_K) / p["eta_c"]
    w_c = CP * (T2 - T1_K)
    # turbine 4->5 (TIT fixed by heat-pipe limit, independent of ambient)
    T4 = TIT_K
    T5s = T4 * (1.0 / PR) ** K
    T5 = T4 - p["eta_t"] * (T4 - T5s)
    w_t = CP * (T4 - T5)
    # recuperator: cold side (T2) preheated by hot exhaust (T5)
    T3 = T2 + p["eps_recup"] * (T5 - T2)
    T3 = min(T3, T4)                       # cannot exceed turbine inlet
    q_in = CP * (T4 - T3)                  # heat added from heat-pipe HX
    w_net = w_t - w_c
    eta_th = w_net / q_in if q_in > 0 else 0.0
    return dict(w_net=w_net, q_in=q_in, eta_th=eta_th, w_c=w_c, w_t=w_t,
                T2=T2, T3=T3, T4=T4, T5=T5)


def mass_flow_factor(T1_K: float, law: str) -> float:
    """mdot(T)/mdot(T0). Fixed-geometry machine at fixed corrected speed."""
    if law == "corrected":
        return np.sqrt(T0_K / T1_K)        # compressor similarity mdot ~ p/sqrt(T)
    return T0_K / T1_K                      # pure density mdot ~ p/T (steeper)


def solve_TIT(p: dict) -> float:
    """Solve turbine-inlet temp so net efficiency = 33% at 25 degC, given fixed eta_mech."""
    def f(TIT_C):
        return p["eta_mech"] * brayton_specific(T0_K, TIT_C, p)["eta_th"] - ETA_NET_TARGET
    return brentq(f, 400.0, 1000.0, xtol=1e-4)


def calibrate(p: dict) -> dict:
    """v1.1: fix eta_mech, solve TIT to hit net 33% @ 25 degC, set mdot_des from 15 MWth."""
    TIT_C = solve_TIT(p)
    d0 = brayton_specific(T0_K, TIT_C, p)
    mdot_des = Q_REACTOR_MW * 1000.0 / d0["q_in"]      # kg/s so cycle absorbs 15 MWth at design
    return dict(TIT_C=TIT_C, eta_mech=p["eta_mech"], mdot_des=mdot_des,
                eta_th0=d0["eta_th"], q_in0=d0["q_in"])


def curve(T_C: np.ndarray, p: dict) -> tuple[pd.DataFrame, dict]:
    cal = calibrate(p)
    TIT_C = cal["TIT_C"]
    rows = []
    for Tc in T_C:
        T1 = Tc + 273.15
        d = brayton_specific(T1, TIT_C, p)
        mf = mass_flow_factor(T1, p["mdot_law"])
        mdot = cal["mdot_des"] * mf
        p_net = cal["eta_mech"] * mdot * d["w_net"] / 1000.0     # MWe
        eta_net = cal["eta_mech"] * d["eta_th"]
        q_cycle = mdot * d["q_in"] / 1000.0                      # MW absorbed by cycle
        rows.append(dict(ambient_temp_C=Tc, net_MWe=p_net, net_efficiency=eta_net,
                         heat_rejection_capacity_frac=min(q_cycle / Q_REACTOR_MW, 1.0),
                         mdot_frac=mf, w_net_kJkg=d["w_net"], q_cycle_MW=q_cycle,
                         TIT_C=TIT_C))
    df = pd.DataFrame(rows)
    p25 = df.loc[np.isclose(df.ambient_temp_C, T0_C), "net_MWe"].iloc[0]
    df["net_MWe_frac_vs25C"] = df.net_MWe / p25
    return df, cal


# ----------------------------------------------------------------------------- reference bounds
def carnot(T_C, T_hot_C):
    return 1.0 - (np.asarray(T_C) + 273.15) / (T_hot_C + 273.15)

def curzon_ahlborn(T_C, T_hot_C):
    return 1.0 - np.sqrt((np.asarray(T_C) + 273.15) / (T_hot_C + 273.15))


# ----------------------------------------------------------------------------- run
def main():
    T_C = np.arange(25.0, 55.0 + 1e-9, 1.0)
    base, cal = curve(T_C, PARAMS)

    lo, hi = HEATPIPE_BAND_C
    assert lo <= cal["TIT_C"] <= hi, (
        f"solved TIT={cal['TIT_C']:.0f} degC outside Na heat-pipe band {HEATPIPE_BAND_C} "
        f"-> revisit PR / component-eff assumptions")

    # sensitivity envelope: re-solve TIT for each combo, keep only physically in-band ones
    stack, dropped = [], []
    for em, pr, law in itertools.product(SENSITIVITY["eta_mech"], SENSITIVITY["PR"], SENSITIVITY["mdot_law"]):
        p = {**PARAMS, "eta_mech": em, "PR": pr, "mdot_law": law}
        try:
            df, c = curve(T_C, p)
            if lo <= c["TIT_C"] <= hi:
                stack.append(df[["ambient_temp_C", "net_MWe_frac_vs25C", "net_efficiency"]]
                             .rename(columns={"net_MWe_frac_vs25C": "frac", "net_efficiency": "eta"}))
            else:
                dropped.append((em, pr, law, c["TIT_C"]))
        except Exception:
            dropped.append((em, pr, law, "solve-failed"))
    allf = pd.concat(stack)
    env = allf.groupby("ambient_temp_C").agg(frac_min=("frac", "min"), frac_max=("frac", "max"),
                                             eta_min=("eta", "min"), eta_max=("eta", "max")).reset_index()

    # reference etas on the same grid (T_hot = solved TIT)
    base["carnot_eta"] = carnot(T_C, cal["TIT_C"])
    base["curzon_ahlborn_eta"] = curzon_ahlborn(T_C, cal["TIT_C"])

    base.to_csv(OUT / "derating_curve_v1.csv", index=False)
    env.to_csv(OUT / "derating_curve_v1_sensitivity.csv", index=False)

    # ---- headline metrics
    def at(T):
        return base.loc[np.isclose(base.ambient_temp_C, T)].iloc[0]
    slope = (at(25).net_MWe_frac_vs25C - at(45).net_MWe_frac_vs25C) / 20.0 * 100  # %/degC 25->45
    carnot_slope = (carnot(25, cal["TIT_C"]) - carnot(45, cal["TIT_C"])) / carnot(25, cal["TIT_C"]) * 100 / 20
    print("=== v1 derating (open-air Brayton, calibration v1.1: fix eta_mech, solve TIT) ===")
    print(f"calibration: eta_mech={cal['eta_mech']:.3f} (FIXED), TIT_solved={cal['TIT_C']:.0f} degC "
          f"(band {HEATPIPE_BAND_C}), eta_thermal(25C)={cal['eta_th0']:.3f}, mdot_des={cal['mdot_des']:.2f} kg/s")
    print(f"net power @25C = {at(25).net_MWe:.3f} MWe (nameplate 5.0), eta_net@25C = {at(25).net_efficiency:.3f}")
    for T in (35, 45, 55):
        r = at(T)
        print(f"  @{T}C: {r.net_MWe:.3f} MWe  ({r.net_MWe_frac_vs25C*100:.1f}% of 25C)  "
              f"eta_net={r.net_efficiency:.3f}  cycle absorbs {r.q_cycle_MW:.1f}/15 MWth")
    print(f"mean electric derating slope 25->45C: {slope:.2f} %/degC (Carnot-only ~{carnot_slope:.2f} %/degC)")
    print(f"penalty @55C vs 25C: -{(1-at(55).net_MWe_frac_vs25C)*100:.1f}% power, "
          f"-{(at(25).net_efficiency-at(55).net_efficiency)*100:.1f} pts efficiency")
    if dropped:
        print(f"sensitivity: {len(stack)} in-band combos; dropped {len(dropped)} out-of-band "
              f"(e.g. {dropped[0][:3]} -> TIT {dropped[0][3] if isinstance(dropped[0][3],str) else round(dropped[0][3])})")

    # ---- figure
    fig, ax1 = plt.subplots(figsize=(8, 5.2))
    ax1.fill_between(env.ambient_temp_C, env.frac_min * 100, env.frac_max * 100,
                     color="#c62828", alpha=0.15, label="assumption sensitivity band")
    ax1.plot(base.ambient_temp_C, base.net_MWe_frac_vs25C * 100, color="#c62828", lw=2.4,
             label="net power (open-air Brayton, v1)")
    ax1.axhline(100, color="#999", lw=0.8, ls=":")
    ax1.set_xlabel("Ambient temperature (°C)")
    ax1.set_ylabel("Net electric power (% of 25 °C)", color="#c62828")
    ax1.tick_params(axis="y", labelcolor="#c62828")
    ax1.set_xlim(25, 55)
    ax1.set_ylim(bottom=min(80, env.frac_min.min() * 100 - 2), top=102)

    ax2 = ax1.twinx()
    ax2.plot(base.ambient_temp_C, base.net_efficiency * 100, color="#1565c0", lw=2.0,
             label="net efficiency (v1)")
    ax2.plot(base.ambient_temp_C, base.curzon_ahlborn_eta * 100, color="#1565c0", lw=1.2, ls="--",
             label="Curzon–Ahlborn bound")
    ax2.plot(base.ambient_temp_C, base.carnot_eta * 100, color="#555", lw=1.0, ls=":",
             label="Carnot bound")
    ax2.set_ylabel("Efficiency (%)", color="#1565c0")
    ax2.tick_params(axis="y", labelcolor="#1565c0")

    ax1.set_title(f"Desert thermal derating v1 — eVinci-class open-air Brayton\n"
                  f"electric penalty ≈ {slope:.2f} %/°C (25–45 °C); net 33% @ 25 °C, solved TIT {cal['TIT_C']:.0f} °C",
                  fontsize=10)
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=7.5, loc="lower left", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(OUT / "derating_curve_v1.png", dpi=150)
    print(f"\nwrote: {OUT/'derating_curve_v1.csv'}\n       {OUT/'derating_curve_v1_sensitivity.csv'}"
          f"\n       {OUT/'derating_curve_v1.png'}")


if __name__ == "__main__":
    main()
