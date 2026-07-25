#!/usr/bin/env python3
"""Generate the two summary figures (vector PDF) for the Phase-1 results summary."""
import math
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = Path(__file__).resolve().parent.parent / "phase1_derating" / "results"
OUT = Path(__file__).resolve().parent

plt.rcParams.update({
    "font.family": "serif", "font.size": 11,
    "axes.linewidth": 0.8, "axes.grid": True,
    "grid.color": "#dddddd", "grid.linewidth": 0.6,
    "axes.edgecolor": "#444444", "figure.dpi": 150,
})
C_V1, C_V2, C_CAR = "#c0561f", "#20699f", "#8a8a8a"

# ---- Fig 1: the derating band (v1 conservative, v2 validated, Carnot floor) ----
v1 = pd.read_csv(RES / "derating_curve_v1.csv")
v2 = pd.read_csv(RES / "derating_curve_v2.csv")
T = v1.ambient_temp_C.values
p_v1 = v1.net_MWe_frac_vs25C.values * 100
p_v2 = np.interp(T, v2.ambient_temp_C.values, v2.net_MWe_frac_vs25C.values) * 100
car = v1.carnot_eta.values
car = car / car[0] * 100  # normalize Carnot ceiling to 25 C

fig, ax = plt.subplots(figsize=(6.4, 4.0))
ax.fill_between(T, p_v1, p_v2, color="#d9b48f", alpha=0.30, label="control-strategy band")
ax.plot(T, car, color=C_CAR, lw=1.4, ls=":", label="Carnot ceiling ($-4\\%$)")
ax.plot(T, p_v2, color=C_V2, lw=2.6, label="v2 (CFD-validated, optimistic): $-8.7\\%$")
ax.plot(T, p_v1, color=C_V1, lw=2.6, label="v1 (conservative baseline): $-17.7\\%$")
ax.scatter([55, 55], [p_v1[-1], p_v2[-1]], color=[C_V1, C_V2], s=28, zorder=5)
ax.annotate("$-17.7\\%$", (55, p_v1[-1]), xytext=(-6, 6), textcoords="offset points",
            ha="right", color=C_V1, fontsize=10, fontweight="bold")
ax.annotate("$-8.7\\%$", (55, p_v2[-1]), xytext=(-6, 6), textcoords="offset points",
            ha="right", color=C_V2, fontsize=10, fontweight="bold")
ax.set_xlim(25, 55); ax.set_ylim(80, 101)
ax.set_xlabel("Ambient (compressor-inlet) temperature  [$^\\circ$C]")
ax.set_ylabel("Net electric power  [% of 25 $^\\circ$C]")
ax.legend(loc="lower left", fontsize=8.5, framealpha=0.95)
fig.tight_layout(); fig.savefig(OUT / "fig_derating.pdf"); plt.close(fig)

# ---- Fig 2: CFD Nu validation vs Briggs-Young ----
Re = np.linspace(3000, 15000, 200)
Nu_by = 54.1 * (Re / 8368.0) ** 0.681
fig, ax = plt.subplots(figsize=(6.4, 3.7))
ax.fill_between(Re, 0.8 * Nu_by, 1.2 * Nu_by, color="#cfe0ee", alpha=0.6, label="$\\pm20\\%$ band")
ax.plot(Re, Nu_by, color=C_V2, lw=2.0, label="Briggs--Young  $Nu \\propto Re^{0.681}$")
ax.axvline(8368, color=C_CAR, lw=0.9, ls=":")
ax.scatter([8368], [54.1], facecolors="none", edgecolors=C_V2, s=55, lw=1.6, zorder=5)
ax.scatter([8368], [45.9], color=C_V1, s=55, zorder=6, label="CFD  $Nu = 45.9$  ($-15.2\\%$)")
ax.annotate("correlation 54.1", (8368, 54.1), xytext=(10, 2), textcoords="offset points", fontsize=8.5, color="#555")
ax.annotate("CFD 45.9", (8368, 45.9), xytext=(10, -3), textcoords="offset points", fontsize=8.5, color=C_V1, fontweight="bold")
ax.set_xlim(3000, 15000); ax.set_ylim(20, 95)
ax.set_xlabel("Reynolds number  $Re$  (tube OD, min-flow section)")
ax.set_ylabel("Nusselt number  $Nu$")
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
fig.tight_layout(); fig.savefig(OUT / "fig_cfd_validation.pdf"); plt.close(fig)

print("wrote:", OUT / "fig_derating.pdf", "and", OUT / "fig_cfd_validation.pdf")
print(f"check: v1@55={p_v1[-1]:.1f}%  v2@55={p_v2[-1]:.1f}%  carnot@55={car[-1]:.1f}%")
