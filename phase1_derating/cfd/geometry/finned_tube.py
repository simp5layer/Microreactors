"""Staggered finned-tube geometry and derived quantities for the heater unit cell.
All lengths in metres. Reference geometry from the CFD v2 design spec."""
from __future__ import annotations
import math
from dataclasses import dataclass

@dataclass(frozen=True)
class FinnedTube:
    d_o: float          # tube outer diameter (m)
    fin_h: float        # fin height (m)
    fin_t: float        # fin thickness (m)
    fin_pitch: float    # centre-to-centre fin spacing (m)
    S_T: float          # transverse pitch (m)
    S_L: float          # longitudinal pitch (m)
    k_fin: float = 25.0 # fin conductivity (W/m/K), high-temp alloy

REFERENCE = FinnedTube(
    d_o=0.0254, fin_h=0.012, fin_t=0.0005, fin_pitch=0.004,
    S_T=2.0 * 0.0254, S_L=1.75 * 0.0254,
)

def min_flow_area_per_pitch(ft: FinnedTube) -> float:
    """Minimum air gap area over one fin pitch: transverse gap minus fin blockage."""
    gap = ft.S_T - ft.d_o                      # bare transverse gap
    # area = (transverse gap over one pitch height) minus fin material in the gap
    return gap * ft.fin_pitch - 2 * ft.fin_h * ft.fin_t

def air_area_per_pitch(ft: FinnedTube) -> float:
    """Total air-side area over one fin pitch: 2 fin faces + fin edge + exposed bare tube."""
    r_i, r_o = ft.d_o / 2, ft.d_o / 2 + ft.fin_h
    faces = 2 * math.pi * (r_o**2 - r_i**2)
    edge = 2 * math.pi * r_o * ft.fin_t
    bare = math.pi * ft.d_o * (ft.fin_pitch - ft.fin_t)
    return faces + edge + bare

def hydraulic_diameter(ft: FinnedTube) -> float:
    return 4 * min_flow_area_per_pitch(ft) * ft.S_L / air_area_per_pitch(ft)

def mass_flux_to_Re(G: float, ft: FinnedTube, mu: float) -> float:
    """Re based on tube OD and max mass flux G (kg/m2/s at min section)."""
    return G * ft.d_o / mu

def fin_efficiency(h: float, ft: FinnedTube) -> float:
    """Annular fin efficiency, tanh(m Lc)/(m Lc) with Harper length correction."""
    Lc = ft.fin_h + ft.fin_t / 2
    m = math.sqrt(2 * h / (ft.k_fin * ft.fin_t))
    x = m * Lc
    return math.tanh(x) / x
