#!/usr/bin/env python3
"""Generate every figure used by CFD_Report/report.tex, as vector PDF into figs/.

Data sources (all real project artifacts -- nothing here is a sketch):
  geometry            phase1_derating/cfd/geometry/finned_tube.py  (REFERENCE dimensions)
  residuals           phase1_derating/cfd/heater_unitcell/log.{rhoSimpleFoam,resume,resolve}
  Nu validation       phase1_derating/cfd/validation/single_point_check.py (frozen CFD scalars)
  UA law              phase1_derating/cfd/postprocessing/fit.py -> results/cfd_correlation.json
  derating curves     phase1_derating/results/derating_curve_{v1,v1_5,v2}.csv
  exponent sweep      re-runs cycle_model/hx_entu_v1_5.py with a power-law ua_law injected

Run:  python3 CFD_Report/make_figs.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

ROOT = Path(__file__).resolve().parent.parent
PHASE1 = ROOT / "phase1_derating"
CFD = PHASE1 / "cfd"
CASE = CFD / "heater_unitcell"
RES = PHASE1 / "results"
OUT = Path(__file__).resolve().parent / "figs"
OUT.mkdir(exist_ok=True)

for _p in (CFD, PHASE1, PHASE1 / "cycle_model"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from geometry.finned_tube import REFERENCE, air_area_per_pitch, fin_efficiency  # noqa: E402
from correlations.finned_tube_corr import briggs_young_nu                        # noqa: E402
from postprocessing.fit import ua_of_mdot, overall_surface_efficiency            # noqa: E402
from hx_entu_v1_5 import PARAMS, curve, size_design                              # noqa: E402

plt.rcParams.update({
    "font.family": "serif", "font.size": 10,
    "axes.linewidth": 0.8, "axes.grid": True,
    "grid.color": "#dddddd", "grid.linewidth": 0.6,
    "axes.edgecolor": "#444444", "figure.dpi": 150,
    "legend.framealpha": 0.95,
})
C_V1, C_V15, C_V2, C_GREY = "#c0561f", "#8a6d3b", "#20699f", "#8a8a8a"
C_METAL, C_AIR = "#b0b7bd", "#eaf2f8"

CORR = json.loads((CFD / "results" / "cfd_correlation.json").read_text())
FT = REFERENCE


# ---------------------------------------------------------------- fig 1: geometry
def fig_geometry():
    """Unit-cell geometry: streamwise-plane section (shows fin clipping) + spanwise fin stack."""
    ft = FT
    r_t, r_f = ft.d_o / 2, ft.d_o / 2 + ft.fin_h
    hx, hy = ft.S_T / 2, ft.S_L / 2
    mm = 1e3  # plot in mm

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.9),
                                   gridspec_kw={"width_ratios": [1.25, 1]})

    # -- (a) x-y plane: the background box vs the finned envelope
    ax1.add_patch(Rectangle((-hx * mm, -hy * mm), ft.S_T * mm, ft.S_L * mm,
                            facecolor=C_AIR, edgecolor="#444", lw=1.2, zorder=1))
    # fin metal that survives inside the box
    ax1.add_patch(Circle((0, 0), r_f * mm, facecolor=C_V1, alpha=0.18,
                         edgecolor="none", zorder=2))
    ax1.add_patch(Circle((0, 0), r_f * mm, facecolor="none", edgecolor=C_V1,
                         lw=1.3, ls="--", zorder=4))
    # the clipped fin caps: {x^2+y^2 <= r_f^2} outside |y| <= S_L/2
    xc = math.sqrt(r_f ** 2 - hy ** 2) * mm
    xs = np.linspace(-xc, xc, 200)
    ytop = np.sqrt((r_f * mm) ** 2 - xs ** 2)
    ax1.fill_between(xs, hy * mm, ytop, color=C_V1, alpha=0.55, zorder=3, hatch="///",
                     edgecolor=C_V1, lw=0)
    ax1.fill_between(xs, -ytop, -hy * mm, color=C_V1, alpha=0.55, zorder=3, hatch="///",
                     edgecolor=C_V1, lw=0)
    ax1.add_patch(Circle((0, 0), r_t * mm, facecolor=C_METAL, edgecolor="#444",
                         lw=1.0, zorder=5))
    ax1.text(0, 0, "tube", ha="center", va="center", fontsize=8, color="#333", zorder=6)

    ax1.annotate("", xy=(-hx * mm, -hy * mm - 6), xytext=(hx * mm, -hy * mm - 6),
                 arrowprops=dict(arrowstyle="<->", lw=0.8, color="#444"))
    ax1.text(0, -hy * mm - 11.5, f"$S_T = {ft.S_T*mm:.1f}$ mm  (cyclic)",
             ha="center", fontsize=8.5)
    ax1.annotate("", xy=(hx * mm + 6, -hy * mm), xytext=(hx * mm + 6, hy * mm),
                 arrowprops=dict(arrowstyle="<->", lw=0.8, color="#444"))
    ax1.text(hx * mm + 9, 0, f"$S_L = {ft.S_L*mm:.1f}$ mm", rotation=90,
             va="center", fontsize=8.5)
    ax1.annotate(f"fin tip $r_f = {r_f*mm:.1f}$ mm\n$>S_L/2 = {hy*mm:.1f}$ mm\n"
                 r"$\Rightarrow$ clipped (hatched)",
                 xy=(6, hy * mm + 1.2), xytext=(-46, 15), textcoords="offset points",
                 fontsize=8, color=C_V1, ha="left",
                 arrowprops=dict(arrowstyle="->", lw=0.8, color=C_V1))
    ax1.annotate("air in ($+y$)", xy=(-14, -hy * mm), xytext=(-14, -hy * mm - 15),
                 fontsize=8.5, color=C_V2, ha="center",
                 arrowprops=dict(arrowstyle="->", lw=1.5, color=C_V2))
    ax1.set_xlim(-hx * mm - 14, hx * mm + 20)
    ax1.set_ylim(-hy * mm - 20, hy * mm + 30)
    ax1.set_aspect("equal"); ax1.grid(False)
    ax1.set_xlabel("$x$ — transverse [mm]"); ax1.set_ylabel("$y$ — streamwise [mm]")
    ax1.set_title("(a) unit cell, $x$–$y$ plane", fontsize=9.5, pad=6)

    # -- (b) y-z plane: the 3-fin stack along the tube axis
    zmax = 3 * ft.fin_pitch * mm
    ax2.add_patch(Rectangle((0, -hy * mm), zmax, ft.S_L * mm,
                            facecolor=C_AIR, edgecolor="#444", lw=1.2, zorder=1))
    for k in range(3):
        zc = (k + 0.5) * ft.fin_pitch * mm
        ax2.add_patch(Rectangle((zc - ft.fin_t * mm / 2, -r_f * mm), ft.fin_t * mm,
                                2 * r_f * mm, facecolor=C_V1, edgecolor=C_V1,
                                lw=0.8, alpha=0.85, zorder=4))
    ax2.add_patch(Rectangle((0, -r_t * mm), zmax, 2 * r_t * mm,
                            facecolor=C_METAL, edgecolor="#444", lw=1.0, zorder=3))
    ytop = hy * mm
    for zc in (0, zmax):
        ax2.plot([zc, zc], [-ytop, ytop + 4], color=C_V2, lw=1.8, ls="-.", zorder=5)
    ax2.text(zmax / 2, ytop + 12, "symmetryPlane\nat mid-fin-gap",
             ha="center", fontsize=8, color=C_V2)
    ax2.annotate("", xy=(0.4, ytop + 5), xytext=(zmax / 2 - 3.0, ytop + 10.5),
                 arrowprops=dict(arrowstyle="->", lw=0.7, color=C_V2))
    ax2.annotate("", xy=(zmax - 0.4, ytop + 5), xytext=(zmax / 2 + 3.0, ytop + 10.5),
                 arrowprops=dict(arrowstyle="->", lw=0.7, color=C_V2))
    # fin pitch, measured between two fin centres, drawn just under the bare tube
    ypit = -hy * mm - 3.5
    ax2.annotate("", xy=(0.5 * ft.fin_pitch * mm, ypit), xytext=(1.5 * ft.fin_pitch * mm, ypit),
                 arrowprops=dict(arrowstyle="<->", lw=0.9, color="#333"))
    ax2.text(ft.fin_pitch * mm, ypit - 6.0, f"pitch {ft.fin_pitch*mm:.0f} mm",
             ha="center", fontsize=8.5)
    ax2.annotate(f"fin: $t={ft.fin_t*mm:.1f}$ mm\n$h={ft.fin_h*mm:.0f}$ mm",
                 xy=(2.5 * ft.fin_pitch * mm, r_f * mm * 0.55), xytext=(6, 26),
                 textcoords="offset points", fontsize=8, color=C_V1,
                 arrowprops=dict(arrowstyle="->", lw=0.8, color=C_V1))
    ax2.set_xlim(-1.2, zmax + 5.5)
    ax2.set_ylim(-hy * mm - 12, hy * mm + 26)
    ax2.grid(False)   # ponytail: z exaggerated (aspect auto) -- 12 mm of z vs 49 mm of y is
    ax2.set_xlabel("$z$ — tube axis (spanwise) [mm]")   # unreadable at true scale; caption says so
    ax2.set_ylabel("$y$ [mm]")
    ax2.set_title("(b) 3-fin unit cell, $y$–$z$ plane", fontsize=9.5, pad=6)

    fig.tight_layout(); fig.savefig(OUT / "fig_geometry.pdf"); plt.close(fig)


# ---------------------------------------------------------------- fig 2: residuals
_RE_TIME = re.compile(r"^Time = (\d+)")
_RE_RES = re.compile(r"Solving for (\w+),\s+Initial residual = ([0-9.eE+-]+)")


def parse_residuals(*logs) -> pd.DataFrame:
    """First initial-residual per field per SIMPLE iteration, merged across restart logs."""
    rows: dict[int, dict] = {}
    for log in logs:
        if not log.exists():
            continue
        t = None
        for line in log.read_text(errors="ignore").splitlines():
            m = _RE_TIME.match(line)
            if m:
                t = int(m.group(1))
                rows.setdefault(t, {})
                continue
            m = _RE_RES.search(line)
            if m and t is not None:
                fld, val = m.group(1), float(m.group(2))
                rows[t].setdefault(fld, val)      # keep first solve of the iteration
    df = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    df.index.name = "iteration"
    return df


def fig_residuals():
    df = parse_residuals(CASE / "log.rhoSimpleFoam", CASE / "log.resume", CASE / "log.resolve")
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    styles = {"Ux": (C_V2, "-"), "Uy": ("#4a9fd8", "-"), "Uz": ("#8fc4e8", "-"),
              "p": (C_V1, "-"), "h": ("#5b8c3e", "-"), "k": (C_GREY, "--"),
              "omega": ("#b07aa1", "--")}
    for fld, (c, ls) in styles.items():
        if fld in df.columns:
            s = df[fld].dropna()
            ax.semilogy(s.index, s.values, color=c, ls=ls, lw=1.1,
                        label=f"${fld}$" if fld != "omega" else r"$\omega$")
    ax.axhline(1e-4, color="#000", lw=0.9, ls=":")
    ax.text(8, 1.35e-4, "residualControl $10^{-4}$", fontsize=8, color="#000")
    ax.axvline(464, color=C_GREY, lw=0.9, ls="-.")
    ax.annotate("converged at iter 464\n(max $9.8\\times10^{-5}$)", xy=(464, 2.2e-6),
                xytext=(-116, -6), textcoords="offset points", fontsize=8, color="#444",
                arrowprops=dict(arrowstyle="->", lw=0.7, color="#444"))
    # 465-466: the 2-iteration restart that wrote the measured fields (restart transient in p)
    ax.axvspan(464.5, df.index.max(), color="#f0d9a8", alpha=0.7, zorder=0)
    ax.annotate("restart to write\nfields (465--466)", xy=(465.5, 3.5e-3), xytext=(-104, 22),
                textcoords="offset points", fontsize=7.5, color="#8a6d1f",
                arrowprops=dict(arrowstyle="->", lw=0.7, color="#8a6d1f"))
    ax.set_xlabel("SIMPLE iteration"); ax.set_ylabel("initial residual")
    ax.set_xlim(0, df.index.max() + 6); ax.set_ylim(1e-7, 2)
    ax.legend(ncol=4, fontsize=8, loc="upper right")
    fig.tight_layout(); fig.savefig(OUT / "fig_residuals.pdf"); plt.close(fig)
    return df


# ---------------------------------------------------------------- fig 3: Nu validation
def fig_nu_validation():
    Re_des, Nu_cfd, Nu_by, Nu_inlet = 8368, 45.9, 54.1, 40.3
    Re = np.linspace(3000, 15000, 300)
    Nu_curve = Nu_by * (Re / Re_des) ** 0.681

    fig, ax = plt.subplots(figsize=(6.6, 3.7))
    ax.fill_between(Re, 0.8 * Nu_curve, 1.2 * Nu_curve, color="#cfe0ee", alpha=0.65,
                    label=r"$\pm$20% validation gate")
    ax.plot(Re, Nu_curve, color=C_V2, lw=2.0,
            label=r"Briggs--Young $Nu = C_{\nu}Re^{0.681}Pr^{1/3}$")
    ax.axvline(Re_des, color=C_GREY, lw=0.9, ls=":")
    ax.scatter([Re_des], [Nu_by], facecolors="none", edgecolors=C_V2, s=60, lw=1.6, zorder=5)
    ax.scatter([Re_des], [Nu_cfd], color=C_V1, s=60, zorder=6,
               label="CFD, LMTD $\\Delta T$: $Nu=45.9$ ($-$15.2%) — validated"
               .replace(r"\textbf{→ validated}", "— validated"))
    ax.scatter([Re_des], [Nu_inlet], marker="x", color="#999", s=55, lw=1.6, zorder=6,
               label="CFD, inlet $\\Delta T$: $Nu=40.3$ ($-$25.5%) — rejected")
    for y, txt, c in ((Nu_by, "correlation 54.1", "#555"),
                      (Nu_cfd, "CFD 45.9", C_V1),
                      (Nu_inlet, "40.3 (wrong $\\Delta T$)", "#999")):
        ax.annotate(txt, (Re_des, y), xytext=(11, -2), textcoords="offset points",
                    fontsize=8.5, color=c)
    ax.text(Re_des, 22, f"  design point\n  $Re={Re_des}$", fontsize=8, color="#444")
    ax.set_xlim(3000, 15000); ax.set_ylim(20, 95)
    ax.set_xlabel("Reynolds number $Re$ (tube OD, minimum-flow section)")
    ax.set_ylabel("Nusselt number $Nu$")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig_nu_validation.pdf"); plt.close(fig)


# ---------------------------------------------------------------- fig 4: the UA law
def fig_ua_law():
    dz = size_design(PARAMS)
    UA_des, mdot_des = float(dz["UA_heater"]), float(dz["mdot_des"])
    Re_des, Pr, k_air = CORR["Re_des"], CORR["Pr"], CORR["k_air_des"]
    n_eff = CORR["n_air_effective"]

    md = np.linspace(0.70, 1.30, 120) * mdot_des
    ua_cfd = np.array([ua_of_mdot(m, FT, UA_des, mdot_des, Re_des, Pr, k_air) for m in md])
    ua_v15 = UA_des * (md / mdot_des) ** 0.6
    ua_raw = UA_des * (md / mdot_des) ** 0.681

    # the ambient-driven operating range actually swept by the cycle (25-55 C)
    v2 = pd.read_csv(RES / "derating_curve_v2.csv")
    md_lo, md_hi = v2.mdot.min(), v2.mdot.max()

    h = np.array([briggs_young_nu(Re_des * m / mdot_des, Pr, FT) * k_air / FT.d_o for m in md])
    eta_f = np.array([fin_efficiency(hh, FT) for hh in h])
    eta_o = np.array([overall_surface_efficiency(hh, FT) for hh in h])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.4))

    ax1.axvspan(md_lo, md_hi, color="#f0d9a8", alpha=0.55, zorder=0)
    ax1.plot(md, ua_raw, color=C_GREY, lw=1.3, ls=":",
             label=r"raw $Nu\propto Re^{0.681}$ (no $\eta_o$)")
    ax1.plot(md, ua_v15, color=C_V15, lw=2.0, ls="--",
             label=r"v1.5 assumed $UA\propto\dot m^{0.6}$")
    ax1.plot(md, ua_cfd, color=C_V2, lw=2.2,
             label=rf"v2 CFD-validated ($n_{{\rm eff}}={n_eff:.3f}$)")
    ax1.scatter([mdot_des], [UA_des], color="#000", s=26, zorder=6)
    ax1.annotate(f"anchor\n{UA_des:.1f} kW/K", (mdot_des, UA_des), xytext=(-46, -30),
                 textcoords="offset points", fontsize=8,
                 arrowprops=dict(arrowstyle="->", lw=0.7, color="#000"))
    ax1.text((md_lo + md_hi) / 2, ua_cfd.min() * 1.02, "25--55 $^\\circ$C\noperating range",
             ha="center", fontsize=7.5, color="#8a6d1f")
    ax1.set_xlabel(r"air mass flow $\dot m$ [kg/s]")
    ax1.set_ylabel(r"heater conductance $UA$ [kW/K]")
    ax1.legend(fontsize=7.5, loc="upper left")
    ax1.set_title("(a) the injected $UA(\\dot m)$ law", fontsize=9.5)

    ax2.axvspan(md_lo, md_hi, color="#f0d9a8", alpha=0.55, zorder=0)
    ax2.plot(md, eta_f, color=C_V1, lw=2.0, label=r"fin efficiency $\eta_{\rm fin}$")
    ax2.plot(md, eta_o, color=C_V2, lw=2.0, label=r"overall surface eff.\ $\eta_o$")
    ax2.scatter([mdot_des], [fin_efficiency(
        briggs_young_nu(Re_des, Pr, FT) * k_air / FT.d_o, FT)], color=C_V1, s=26, zorder=6)
    ax2.annotate(r"$\eta_{\rm fin}\approx0.53$ at design", (mdot_des, 0.5334),
                 xytext=(-30, -34), textcoords="offset points", fontsize=8, color=C_V1,
                 arrowprops=dict(arrowstyle="->", lw=0.7, color=C_V1))
    ax2.text(md[10], 0.585,
             r"$\dfrac{d\ln\eta_o}{d\ln\dot m}\approx-0.23$" + "\n"
             r"$\Rightarrow 0.681-0.23\approx0.454$",
             fontsize=8.5, color="#333")
    ax2.set_xlabel(r"air mass flow $\dot m$ [kg/s]")
    ax2.set_ylabel("efficiency [--]")
    ax2.set_ylim(0.45, 0.70)
    ax2.legend(fontsize=8, loc="lower left")
    ax2.set_title(r"(b) why $n$ lands $below$ 0.6", fontsize=9.5)

    fig.tight_layout(); fig.savefig(OUT / "fig_ua_law.pdf"); plt.close(fig)


# ---------------------------------------------------------------- fig 5: derating curves
def fig_derating():
    v1 = pd.read_csv(RES / "derating_curve_v1.csv")
    v15 = pd.read_csv(RES / "derating_curve_v1_5.csv")
    v2 = pd.read_csv(RES / "derating_curve_v2.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.4),
                                   gridspec_kw={"width_ratios": [1.35, 1]})
    ax1.fill_between(v1.ambient_temp_C, v1.net_MWe_frac_vs25C * 100,
                     np.interp(v1.ambient_temp_C, v2.ambient_temp_C,
                               v2.net_MWe_frac_vs25C) * 100,
                     color="#d9b48f", alpha=0.30, label="control-strategy band")
    ax1.plot(v1.ambient_temp_C, v1.net_MWe_frac_vs25C * 100, color=C_V1, lw=2.4,
             label="v1 conservative: $-$17.7%")
    ax1.plot(v15.ambient_temp_C, v15.net_MWe_frac_vs25C * 100, color=C_V15, lw=2.4, ls="--",
             label="v1.5 assumed $\\dot m^{0.6}$: $-$8.8%")
    ax1.plot(v2.ambient_temp_C, v2.net_MWe_frac_vs25C * 100, color=C_V2, lw=2.0,
             label="v2 CFD-validated: $-$8.7%")
    ax1.set_xlim(25, 55); ax1.set_ylim(80, 101)
    ax1.set_xlabel("ambient (compressor-inlet) temperature  [$^\\circ$C]")
    ax1.set_ylabel("net electric power  [% of 25 $^\\circ$C]")
    ax1.legend(loc="lower left", fontsize=8)
    ax1.set_title("(a) the derating curve, three model generations", fontsize=9.5)

    # zoom: v1.5 vs v2 -- the whole point is that they overlap
    ax2.plot(v15.ambient_temp_C, v15.net_MWe_frac_vs25C * 100, color=C_V15, lw=2.6, ls="--",
             label="v1.5 (assumed)")
    ax2.plot(v2.ambient_temp_C, v2.net_MWe_frac_vs25C * 100, color=C_V2, lw=1.8,
             label="v2 (CFD)")
    d = (v2.net_MWe_frac_vs25C.values[-1] - v15.net_MWe_frac_vs25C.values[-1]) * 100
    ax2.annotate(f"$\\Delta = {d:+.2f}$ pt at 55 $^\\circ$C",
                 (55, v2.net_MWe_frac_vs25C.values[-1] * 100), xytext=(-96, 26),
                 textcoords="offset points", fontsize=8.5,
                 arrowprops=dict(arrowstyle="->", lw=0.8, color="#000"))
    ax2.set_xlim(44, 55.4); ax2.set_ylim(90.5, 97.6)
    ax2.set_xlabel("ambient temperature  [$^\\circ$C]")
    ax2.legend(loc="lower left", fontsize=8)
    ax2.set_title("(b) zoom: v2 confirms v1.5", fontsize=9.5)

    fig.tight_layout(); fig.savefig(OUT / "fig_derating.pdf"); plt.close(fig)


# ------------------------------------------------- fig 6: sensitivity to the UA exponent
def fig_sensitivity():
    """Re-run the v1.5 cycle with UA proportional to mdot^n over a wide n, and plot the
    55 C penalty. This is the quantitative form of the robustness claim."""
    dz = size_design(PARAMS)
    UA_des, mdot_des = float(dz["UA_heater"]), float(dz["mdot_des"])
    T = np.arange(25.0, 55.0 + 1e-9, 1.0)

    ns = np.linspace(0.0, 1.2, 25)
    pens = []
    for n in ns:
        p = {**PARAMS, "ua_law": (lambda m, n=n: UA_des * (m / mdot_des) ** n)}
        df, _ = curve(T, p)
        pens.append((1 - df.net_MWe_frac_vs25C.values[-1]) * 100)
    pens = np.array(pens)

    n_v2 = CORR["n_air_effective"]
    p_v2 = np.interp(n_v2, ns, pens)
    p_v15 = np.interp(0.6, ns, pens)

    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    ax.plot(ns, pens, color=C_V2, lw=2.2)
    ax.axvspan(n_v2, 0.6, color="#f0d9a8", alpha=0.6, zorder=0)
    ax.scatter([0.6], [p_v15], color=C_V15, s=55, zorder=6,
               label=rf"v1.5 assumed $n=0.6$: $-${p_v15:.2f}%")
    ax.scatter([n_v2], [p_v2], color=C_V2, s=55, zorder=6,
               label=rf"v2 CFD $n={n_v2:.3f}$: $-${p_v2:.2f}%")
    ax.annotate(rf"the CFD moved $n$ by ${0.6-n_v2:.3f}$" + "\n"
                rf"and the penalty by ${abs(p_v2-p_v15):.2f}$ pt",
                xy=((n_v2 + 0.6) / 2, (p_v2 + p_v15) / 2), xytext=(0.72, 8.55),
                fontsize=8.5, arrowprops=dict(arrowstyle="->", lw=0.8, color="#000"))
    ax.set_xlim(0, 1.2)
    ax.set_xlabel(r"assumed air-side exponent $n$ in $UA\propto\dot m^{\,n}$")
    ax.set_ylabel("net-power penalty at 55 $^\\circ$C  [%]")
    ax.legend(fontsize=8.5, loc="upper right")
    fig.tight_layout(); fig.savefig(OUT / "fig_sensitivity.pdf"); plt.close(fig)
    return ns, pens


if __name__ == "__main__":
    fig_geometry()
    res = fig_residuals()
    fig_nu_validation()
    fig_ua_law()
    fig_derating()
    ns, pens = fig_sensitivity()

    print(f"residual log: {len(res)} iterations parsed, fields {list(res.columns)}")
    print(f"  final residuals: " +
          ", ".join(f"{c}={res[c].dropna().values[-1]:.2e}" for c in res.columns))
    print(f"penalty@55C across n=0..1.2: {pens.min():.2f}% .. {pens.max():.2f}% "
          f"(spread {pens.max()-pens.min():.2f} pt)")
    print("wrote:", ", ".join(sorted(p.name for p in OUT.glob("*.pdf"))))
