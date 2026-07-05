#!/usr/bin/env python3
"""
v1.5 derating curve — open-air recuperated Brayton with epsilon-NTU heat exchangers.

WHY v1.5 exists (what it adds over v1.1):
  v1 treated the turbine-inlet temperature (TIT) as a FIXED heat-pipe-limited constant. This model
  replaces the assumed recuperator effectiveness and the implicit heater approach with epsilon-NTU
  components, then couples them to the reactor's fixed-power energy balance. That exposes two regimes:

    Regime B (reactor-power-limited): the reactor pins 15 MWth. At a given ambient the heater passes
      that heat into the air; TIT = T3 + Q/(mdot*cp). As ambient rises, air mass flow falls, so the
      same 15 MWth heats less air -> TIT FLOATS UP. Higher firing temp partly offsets the mass-flow
      loss -> derating is SHALLOWER than the fixed-TIT assumption. Requires heat-pipe source headroom.

    Regime A (heat-pipe-source-limited): once the source temperature the heater would need exceeds the
      sodium heat-pipe ceiling T_hp_max, TIT is capped. The heater can no longer pass all 15 MWth, so
      the reactor SHEDS the excess (thermal derating) and electric power falls faster.

  The B->A crossover ambient is a COMPUTED result that depends on the design heat-pipe headroom
  (T_hp_max - T_hp_design). It is NOT pinned to the design point (that was a v1.5-draft bug found in
  adversarial review: sizing eps_h from T_hp_max forced the anchor onto the knife-edge; fixed here by
  sizing the heater to an independent design approach, leaving genuine headroom below the ceiling).

Heat-exchanger physics (verified):
  * Recuperator (air-air, balanced counterflow, C_r = 1):  eps = NTU/(1+NTU).
  * Heater (condensing Na heat pipes -> air, C_min/C_max -> 0):  eps = 1 - exp(-NTU).
  * Air-side UA ~ mdot^n (n~0.6, turbulent finned-tube h ~ Re^0.6) — the hook the CFD (v2) pins.

Efficiency reporting (fixed after review): two efficiencies are distinct once heat is shed —
  * plant_efficiency = net_MWe / 15 MWth  (fuel-to-electric; the meaningful one, = nameplate 33% @ 25C)
  * cycle_efficiency = net_MWe / q_absorbed_by_air  (higher than plant eff when heat is shed)

Calibration anchored to v1.1 (net 33% @ 25 degC, TIT ~742 degC, eta_mech=0.93, PR=3.0). Normalized to
25 degC, electricity-only, air-standard properties.

Outputs (results/):
  derating_curve_v1_5.csv        v1.5 curve + regime flag + TIT + both efficiencies + shed heat
  derating_curve_v1_vs_v1_5.png  v1 (fixed TIT) vs v1.5 (eps-NTU), with the computed B->A crossover
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

T0_C, T0_K = 25.0, 298.15
CP, GAMMA = 1.005, 1.40
K = (GAMMA - 1.0) / GAMMA
Q_REACTOR_MW = 15.0
P_NAMEPLATE_MWE = 5.0
ETA_NET_TARGET = P_NAMEPLATE_MWE / Q_REACTOR_MW

PARAMS = dict(
    eta_mech=0.93, PR=3.0, eta_c=0.82, eta_t=0.85,
    eps_recup_design=0.88,   # recuperator effectiveness at design mdot -> sizes UA_recup
    TIT_design_C=742.0,      # v1.1 anchor: TIT at 25 degC
    approach_design_C=18.0,  # heater approach at design (source - TIT) -> sizes UA_heater INDEPENDENT of the cap
    T_hp_max_C=800.0,        # sodium heat-pipe SOURCE ceiling (governs regime A); independent of design sizing
    n_air=0.6,               # air-side UA ~ mdot^n; CFD refines
    mdot_law="corrected",    # mdot ~ p/sqrt(T); note: shallow bound for a constant-physical-speed genset
)


def mass_flow_factor(T1_K, law):
    return np.sqrt(T0_K / T1_K) if law == "corrected" else (T0_K / T1_K)


def compressor(T1_K, p):
    T2s = T1_K * p["PR"] ** K
    T2 = T1_K + (T2s - T1_K) / p["eta_c"]
    return T2, CP * (T2 - T1_K)


def turbine(TIT_K, p):
    T5s = TIT_K * (1.0 / p["PR"]) ** K
    T5 = TIT_K - p["eta_t"] * (TIT_K - T5s)
    return T5, CP * (TIT_K - T5)


def size_design(p):
    """Size mdot_des, UA_heater, UA_recup at 25 degC. Heater sized to an INDEPENDENT design approach so
    the design source temp sits BELOW the ceiling T_hp_max (genuine headroom -> regime B reachable)."""
    T2, _ = compressor(T0_K, p)
    TIT = p["TIT_design_C"] + 273.15
    eps_r = p["eps_recup_design"]
    NTU_r = eps_r / (1.0 - eps_r)
    T5, _ = turbine(TIT, p)
    T3 = T2 + eps_r * (T5 - T2)
    mdot_des = Q_REACTOR_MW * 1000.0 / (CP * (TIT - T3))
    UA_recup = NTU_r * mdot_des * CP
    # heater sized to the DESIGN source temp = TIT + approach_design (NOT the ceiling)
    T_hp_design = TIT + p["approach_design_C"]
    eps_h_des = (TIT - T3) / (T_hp_design - T3)
    UA_heater = -np.log(1.0 - eps_h_des) * mdot_des * CP
    return dict(mdot_des=mdot_des, UA_recup=UA_recup, UA_heater=UA_heater, T3_des=T3 - 273.15,
                T_hp_design_C=T_hp_design - 273.15, eps_h_des=eps_h_des)


def solve_state(T1_K, p, dz):
    mdot = dz["mdot_des"] * mass_flow_factor(T1_K, p["mdot_law"])
    scale = (mdot / dz["mdot_des"]) ** p["n_air"]
    UA_heater, UA_recup = dz["UA_heater"] * scale, dz["UA_recup"] * scale
    C = mdot * CP
    T2, w_c = compressor(T1_K, p)
    eps_r = (UA_recup / C) / (1.0 + UA_recup / C)
    eps_h = 1.0 - np.exp(-UA_heater / C)
    T_hp_max = p["T_hp_max_C"] + 273.15

    T5 = T1_K + 400.0
    TIT = T5
    regime, q_shed = "B", 0.0
    for _ in range(80):
        T3 = T2 + eps_r * (T5 - T2)
        TIT_B = T3 + Q_REACTOR_MW * 1000.0 / C           # regime B: energy balance, reactor pins 15 MWth
        T_hp_req = T3 + (TIT_B - T3) / eps_h             # source temp needed to reach TIT_B
        if T_hp_req <= T_hp_max:
            TIT, regime, q_shed = TIT_B, "B", 0.0
        else:                                            # regime A: source capped -> heater-limited TIT
            TIT = T3 + eps_h * (T_hp_max - T3)
            q_shed = Q_REACTOR_MW - C * (TIT - T3) / 1000.0
            regime = "A"
        T5_new, _ = turbine(TIT, p)
        if abs(T5_new - T5) < 1e-6:
            T5 = T5_new
            break
        T5 = T5_new
    T3 = T2 + eps_r * (T5 - T2)
    _, w_t = turbine(TIT, p)
    w_net = w_t - w_c
    q_cycle = C * (TIT - T3) / 1000.0
    p_net = p["eta_mech"] * mdot * w_net / 1000.0
    return dict(mdot=mdot, TIT_C=TIT - 273.15, T3_C=T3 - 273.15, regime=regime,
                T_hp_req_C=(T3 + (TIT - T3) / eps_h) - 273.15, q_cycle_MW=q_cycle,
                q_shed_MW=max(q_shed, 0.0), net_MWe=p_net,
                plant_efficiency=p_net / Q_REACTOR_MW,          # fuel-to-electric (primary)
                cycle_efficiency=(p_net / q_cycle if q_cycle > 0 else 0.0))


def curve(T_C, p):
    dz = size_design(p)
    df = pd.DataFrame([dict(ambient_temp_C=Tc, **solve_state(Tc + 273.15, p, dz)) for Tc in T_C])
    p25 = df.loc[np.isclose(df.ambient_temp_C, T0_C), "net_MWe"].iloc[0]
    df["net_MWe_frac_vs25C"] = df.net_MWe / p25
    return df, dz


def crossover_C(p):
    """Ambient at which regime switches B->A (NaN if none in 25-70 range)."""
    T = np.arange(25.0, 70.01, 0.5)
    df, _ = curve(T, p)
    a = df[df.regime == "A"].ambient_temp_C
    return float(a.min()) if len(a) else float("nan")


def main():
    T_C = np.arange(25.0, 55.0 + 1e-9, 1.0)
    df, dz = curve(T_C, PARAMS)

    def at(T):
        return df.loc[np.isclose(df.ambient_temp_C, T)].iloc[0]
    slope = (at(25).net_MWe_frac_vs25C - at(45).net_MWe_frac_vs25C) / 20 * 100
    cross = crossover_C(PARAMS)

    print("=== v1.5 derating (eps-NTU HX + reactor energy balance; headroom-corrected) ===")
    print(f"design: mdot_des={dz['mdot_des']:.1f} kg/s, UA_heater={dz['UA_heater']:.1f} kW/K, "
          f"UA_recup={dz['UA_recup']:.1f} kW/K, T3_des={dz['T3_des']:.0f}C, "
          f"T_hp_design={dz['T_hp_design_C']:.0f}C (ceiling {PARAMS['T_hp_max_C']:.0f}C)")
    print(f"net @25C = {at(25).net_MWe:.3f} MWe, plant_eff={at(25).plant_efficiency:.3f}, regime {at(25).regime}")
    for T in (30, 35, 45, 55):
        r = at(T)
        print(f"  @{T}C: {r.net_MWe:.3f} MWe ({r.net_MWe_frac_vs25C*100:.1f}%)  TIT={r.TIT_C:.0f}C  "
              f"regime {r.regime}  T_hp_req={r.T_hp_req_C:.0f}C  plant_eff={r.plant_efficiency:.3f}  "
              f"cycle_eff={r.cycle_efficiency:.3f}  shed={r.q_shed_MW:.1f}MW")
    print(f"computed B->A crossover: {'none in range' if np.isnan(cross) else f'{cross:.1f} C'}")
    print(f"mean electric derating 25->45C: {slope:.2f} %/degC; penalty @55C: -{(1-at(55).net_MWe_frac_vs25C)*100:.1f}%")

    # non-degeneracy check: crossover MUST now move with the heat-pipe ceiling (draft bug pinned it at 26C)
    print("crossover vs T_hp_max ceiling (was degenerate @26C in the draft):")
    for thp in (780, 800, 820, 850):
        print(f"   T_hp_max={thp}C -> crossover {crossover_C({**PARAMS, 'T_hp_max_C': float(thp)}):.1f} C")

    df.to_csv(OUT / "derating_curve_v1_5.csv", index=False)

    # ---- comparison plot vs v1
    v1 = pd.read_csv(OUT / "derating_curve_v1.csv")
    fig, ax = plt.subplots(figsize=(8, 5.2))
    ax.plot(v1.ambient_temp_C, v1.net_MWe_frac_vs25C * 100, color="#999", lw=1.8, ls="--", label="v1 (fixed TIT)")
    ax.plot(df.ambient_temp_C, df.net_MWe_frac_vs25C * 100, color="#c62828", lw=2.4, label="v1.5 (ε-NTU + energy balance)")
    if not np.isnan(cross) and 25 <= cross <= 55:
        ax.axvline(cross, color="#1565c0", lw=1.0, ls=":")
        ax.text(cross + 0.3, 83, f"B→A crossover\n@{cross:.0f} °C", fontsize=7.5, color="#1565c0")
        ax.text(0.30, 0.93, "regime B: reactor at full power, TIT floats up (shallower derating)",
                transform=ax.transAxes, fontsize=7, color="#2e7d32")
        ax.text(0.30, 0.88, "regime A: TIT capped at heat-pipe ceiling, reactor sheds heat",
                transform=ax.transAxes, fontsize=7, color="#8d6e00")
    ax.set_xlabel("Ambient temperature (°C)")
    ax.set_ylabel("Net electric power (% of 25 °C)")
    ax.set_xlim(25, 55)
    ax.set_title(f"v1.5 ε-NTU refinement vs v1 fixed-TIT — derating ≈ {slope:.2f} %/°C (25–45 °C)\n"
                 f"B→A crossover {cross:.0f} °C (moves with heat-pipe headroom)", fontsize=10)
    ax.legend(fontsize=8, loc="lower left")
    ax2 = ax.twinx()
    ax2.plot(df.ambient_temp_C, df.TIT_C, color="#ef6c00", lw=1.3, label="TIT (°C)")
    ax2.set_ylabel("Turbine inlet temp (°C)", color="#ef6c00")
    ax2.tick_params(axis="y", labelcolor="#ef6c00")
    ax2.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT / "derating_curve_v1_vs_v1_5.png", dpi=150)
    print(f"\nwrote: {OUT/'derating_curve_v1_5.csv'}\n       {OUT/'derating_curve_v1_vs_v1_5.png'}")


if __name__ == "__main__":
    main()
