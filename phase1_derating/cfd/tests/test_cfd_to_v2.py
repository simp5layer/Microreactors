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
