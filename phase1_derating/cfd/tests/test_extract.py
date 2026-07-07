"""Tests for postprocessing.extract — OpenFOAM function-object output parsing.

Synthetic fixtures mimic the ESI wallHeatFlux and surfaceFieldValue .dat formats
so the parsing/derivation is exercised without a live OpenFOAM run.
"""
import pytest
from geometry.finned_tube import REFERENCE
from postprocessing.extract import extract_h, extract_dp_and_f


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_extract_h_positive_and_sign(tmp_path):
    # Columns: Time patch min max integral(=Q, W). Q<0 = heat leaving wall to fluid.
    d = tmp_path / "postProcessing/wallHeatFlux1/0"
    _write(d / "wallHeatFlux.dat",
           "# Wall heat-flux\n"
           "# Time  patch  min  max  integral\n"
           "3000 tube -5e4 -1e4 -30000\n")
    h = extract_h(str(tmp_path), REFERENCE, T_wall=1033.0, T_bulk=740.0,
                  A_wetted=9.0165e-3)
    assert h > 0  # sign handled -> positive coefficient
    assert h == pytest.approx((30000 / 9.0165e-3) / (1033.0 - 740.0))


def test_extract_h_uses_last_row_and_latest_dir(tmp_path):
    # An older time directory that must be ignored in favour of the latest.
    _write(tmp_path / "postProcessing/wallHeatFlux1/0/wallHeatFlux.dat",
           "# Time patch min max integral\n100 tube 0 0 -10000\n")
    # Latest time directory with two rows -> the LAST row is the converged one.
    _write(tmp_path / "postProcessing/wallHeatFlux1/300/wallHeatFlux.dat",
           "# Time patch min max integral\n"
           "465 tube 27 1.2e6 -200.0\n"
           "466 tube 27 1.2e6 -256.30\n")
    h = extract_h(str(tmp_path), REFERENCE, T_wall=1033.0, T_bulk=740.0,
                  A_wetted=9.0165e-3)
    assert h == pytest.approx((256.30 / 9.0165e-3) / 293.0)


def test_extract_dp_and_f(tmp_path):
    _write(tmp_path / "postProcessing/pIn/0/surfaceFieldValue.dat",
           "# Region type : patch inlet\n"
           "# Time  areaAverage(p)\n"
           "465 200150.0\n"
           "466 200148.4\n")
    _write(tmp_path / "postProcessing/pOut/0/surfaceFieldValue.dat",
           "# Region type : patch outlet\n"
           "# Time  areaAverage(p)\n"
           "465 200000.0\n"
           "466 200000.0\n")
    rho, U_max = 0.9417, 13.665
    dp, f = extract_dp_and_f(str(tmp_path), REFERENCE, rho, U_max, n_rows=1)
    assert dp == pytest.approx(148.4)
    assert f == pytest.approx(148.4 / (0.5 * rho * U_max**2 * 1))
