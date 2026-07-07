import math
from geometry.finned_tube import (
    FinnedTube, REFERENCE, min_flow_area_per_pitch, air_area_per_pitch,
    hydraulic_diameter, mass_flux_to_Re, fin_efficiency,
)

def test_reference_values():
    ft = REFERENCE
    assert ft.d_o == 0.0254
    assert ft.S_T == 2.0 * ft.d_o
    assert ft.S_L == 1.75 * ft.d_o

def test_min_flow_area_positive_and_below_frontal():
    ft = REFERENCE
    a_min = min_flow_area_per_pitch(ft)
    frontal = ft.S_T * ft.fin_pitch
    assert 0 < a_min < frontal  # fins+tube block part of the gap

def test_air_area_dominated_by_fins():
    ft = REFERENCE
    a = air_area_per_pitch(ft)
    # two fin annulus faces alone:
    r_o = ft.d_o/2 + ft.fin_h
    two_faces = 2 * math.pi * (r_o**2 - (ft.d_o/2)**2)
    assert a > two_faces  # includes edge + bare tube

def test_reynolds_scales_linearly_with_G():
    ft = REFERENCE
    mu = 3.7e-5  # air at ~600C
    assert math.isclose(mass_flux_to_Re(20.0, ft, mu),
                        2 * mass_flux_to_Re(10.0, ft, mu), rel_tol=1e-9)

def test_fin_efficiency_between_0_and_1_and_falls_with_h():
    ft = REFERENCE
    e_lo = fin_efficiency(50.0, ft)
    e_hi = fin_efficiency(500.0, ft)
    assert 0.0 < e_hi < e_lo < 1.0  # higher h -> lower efficiency
