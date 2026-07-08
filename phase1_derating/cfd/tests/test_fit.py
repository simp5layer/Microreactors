"""TDD for postprocessing.fit -- the CFD-validated Briggs-Young UA(mdot) law
that emits results/cfd_correlation.json (Option 1: no CFD sweep, the air-side
law is the CFD-validated Briggs-Young Nu correlation).
"""
import json
import math

import numpy as np

from geometry.finned_tube import REFERENCE
from postprocessing.fit import (
    fit_power_law,
    overall_surface_efficiency,
    ua_of_mdot,
    dp_of_mdot,
    write_cfd_correlation_json,
    RE_DES,
    PR,
    K_AIR_DES,
)
from cycle_model.hx_entu_v1_5 import size_design, PARAMS


def _anchors():
    """Live v1.5 design anchors so v2 matches v1.5 exactly at design."""
    dz = size_design(PARAMS)
    return float(dz["UA_heater"]), float(dz["mdot_des"])


# --------------------------------------------------------------------------
# fit_power_law
# --------------------------------------------------------------------------
def test_fit_power_law_recovers_known_coeffs():
    x = np.linspace(0.5, 5.0, 40)
    C_true, m_true = 0.3, 0.7
    y = C_true * x ** m_true
    C, m = fit_power_law(x, y)
    assert math.isclose(C, C_true, rel_tol=1e-6)
    assert math.isclose(m, m_true, rel_tol=1e-6)


# --------------------------------------------------------------------------
# overall_surface_efficiency
# --------------------------------------------------------------------------
def test_overall_surface_efficiency_bounds_and_monotone():
    e_lo = overall_surface_efficiency(50.0, REFERENCE)
    e_hi = overall_surface_efficiency(500.0, REFERENCE)
    # higher h -> larger fin temperature drop -> lower surface efficiency
    assert 0.0 < e_hi < e_lo < 1.0


# --------------------------------------------------------------------------
# ua_of_mdot -- the anchored Briggs-Young UA law
# --------------------------------------------------------------------------
def test_ua_anchor_holds_exactly():
    UA_des, mdot_des = _anchors()
    ua = ua_of_mdot(mdot_des, REFERENCE, UA_des, mdot_des, RE_DES, PR, K_AIR_DES)
    assert math.isclose(ua, UA_des, rel_tol=1e-12)


def test_ua_strictly_increasing_in_mdot():
    UA_des, mdot_des = _anchors()
    mdots = np.linspace(0.7, 1.3, 25) * mdot_des
    ua = [ua_of_mdot(md, REFERENCE, UA_des, mdot_des, RE_DES, PR, K_AIR_DES)
          for md in mdots]
    assert all(b > a for a, b in zip(ua, ua[1:]))


# --------------------------------------------------------------------------
# dp_of_mdot -- informational Robinson-Briggs scaling (NOT wired into balance)
# --------------------------------------------------------------------------
def test_dp_anchor_holds():
    _, mdot_des = _anchors()
    dp_des = 148.4
    dp = dp_of_mdot(mdot_des, REFERENCE, RE_DES, mdot_des, dp_des)
    assert math.isclose(dp, dp_des, rel_tol=1e-12)


# --------------------------------------------------------------------------
# write_cfd_correlation_json
# --------------------------------------------------------------------------
def test_write_json_effective_exponent_and_anchors(tmp_path):
    out = tmp_path / "cfd_correlation.json"
    d = write_cfd_correlation_json(out)
    assert out.exists()
    with open(out) as fh:
        j = json.load(fh)
    assert d == j

    # Briggs-Young Re exponent preserved
    assert j["m"] == 0.681
    assert j["p"] == -0.316
    assert j["Re_des"] == 8368

    # Effective air-side UA exponent.
    #
    # NOTE (deviation from the task's predicted 0.66-0.68 band): with the EXACT
    # ua_of_mdot formula specified in the task and the REFERENCE fin geometry,
    # the fin-efficiency modulation is far stronger than the task anticipated.
    # The REFERENCE fin (0.5 mm thick, 12 mm tall, k_fin=25) has a LOW design
    # fin efficiency (~0.53) sitting in the sensitive elbow of tanh(mLc)/mLc, so
    # eta_o swings ~0.62 -> 0.54 across +-30% mdot. Analytically the effective
    # exponent is 0.681 + dln(eta_o)/dln(mdot) = 0.681 - 0.229 = 0.452, which the
    # log-log fit reproduces. No physical property choice recovers 0.66 (that
    # needs eta_fin ~ 1, i.e. h ~ 11 W/m2/K, unphysical). The honest finding is
    # that including fin efficiency the effective air-side UA exponent is
    # SHALLOWER than v1.5's assumed 0.6, not steeper. We therefore assert the
    # spec-GUARANTEED invariant (below the raw Re-exponent 0.681, positive) plus
    # a regression lock on the honest value. See task-8-report.md.
    n = j["n_air_effective"]
    assert 0.0 < n < 0.681           # fin modulation always shallows below Re^m
    assert abs(n - 0.454) < 0.01     # regression lock on the honest value

    # live anchors carried through unchanged
    UA_des, mdot_des = _anchors()
    assert math.isclose(j["UA_design_kW_per_K"], UA_des, rel_tol=1e-9)
    assert math.isclose(j["mdot_des_kg_s"], mdot_des, rel_tol=1e-9)

    # n_tubes is a positive diagnostic count for the stated tube length
    assert j["L_tube_m"] == 2.0
    assert j["n_tubes"] > 0
