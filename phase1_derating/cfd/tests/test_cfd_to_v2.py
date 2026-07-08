import json, numpy as np
from cfd_to_v2 import build_v2_curve


def test_v2_reproduces_design_point(tmp_path):
    corr = {"C_nu": 0.13, "m": 0.68, "C_f": 9.0, "p": -0.316,
            "n_tubes": 800, "UA_design_kW_per_K": 152.0}
    p = tmp_path / "c.json"
    p.write_text(json.dumps(corr))
    df = build_v2_curve(str(p))
    row25 = df[np.isclose(df.ambient_temp_C, 25)].iloc[0]
    assert abs(row25.net_MWe - 5.0) < 0.05   # still 5 MWe at 25C


def test_v2_ua_law_actually_affects_regime_A(tmp_path):
    """At 25C the reactor is regime B (reactor-power-limited): net_MWe is set by the
    15 MWth energy balance and is INDEPENDENT of the heater UA magnitude, so
    test_v2_reproduces_design_point above would pass even if ua_law were silently
    never injected (or 5x wrong). Prove the injection path is actually exercised by
    checking a heater-limited (regime A) ambient, 55C, where UA magnitude DOES move
    net power: two curves differing only in UA_design_kW_per_K must give different
    net_MWe at 55C. If the injection were dropped, both would fall back to v1.5's
    default heater UA (independent of the json) and be identical -> this would fail.
    """
    base = {"C_nu": 0.13, "m": 0.68, "C_f": 9.0, "p": -0.316,
            "n_tubes": 800, "UA_design_kW_per_K": 152.0}

    def net_at(TC, ua_des):
        corr = {**base, "UA_design_kW_per_K": ua_des}
        p = tmp_path / f"c_{ua_des}.json"
        p.write_text(json.dumps(corr))
        df = build_v2_curve(str(p))
        row = df[np.isclose(df.ambient_temp_C, TC)].iloc[0]
        assert row.regime == "A"   # sanity: 55C must actually be heater-limited
        return row.net_MWe

    # regime A at 55C: heater UA magnitude changes net power -> proves ua_law is invoked
    assert abs(net_at(55, 152.0) - net_at(55, 100.0)) > 0.01
