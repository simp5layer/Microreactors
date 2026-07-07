"""Parse OpenFOAM function-object output for the CFD v2 finned-tube validation.

Reads the ``postProcessing`` tree written by rhoSimpleFoam:
  * ``wallHeatFlux1/<t>/wallHeatFlux.dat`` -> integral heat rate Q over ``tube``
  * ``pIn/<t>/surfaceFieldValue.dat`` / ``pOut/<t>/...`` -> streamwise Δp

Conventions: temperatures in K, areas in m², heat rate in W, pressure in Pa.
The latest time directory is used, and the last data row within it (the
converged step). Header lines beginning with ``#`` are skipped.
"""
from __future__ import annotations
from pathlib import Path

from geometry.finned_tube import FinnedTube

# Actual wetted area of the CFD `tube` patch (m²): 329016 faces. The fins are
# clipped by the streamwise domain boundary, so this is below the analytical
# 3 x air_area_per_pitch = 9.530e-3 m². Use this for the real converged case;
# callers may override for testing or other meshes.
A_WETTED_CFD = 9.0165e-3


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _latest_pp_dir(case_dir, func_name: str) -> Path:
    """Highest-numbered time directory under postProcessing/<func_name>."""
    base = Path(case_dir) / "postProcessing" / func_name
    subs = [d for d in base.iterdir() if d.is_dir() and _is_number(d.name)]
    if not subs:
        raise FileNotFoundError(f"no time directories under {base}")
    return max(subs, key=lambda d: float(d.name))


def _last_data_row(dat_path: Path) -> list[str]:
    """Whitespace-split fields of the last non-comment, non-blank row."""
    with open(dat_path) as fh:
        rows = [ln.split() for ln in fh
                if ln.strip() and not ln.lstrip().startswith("#")]
    if not rows:
        raise ValueError(f"no data rows in {dat_path}")
    return rows[-1]


def extract_h(case_dir, ft: FinnedTube, T_wall: float = 1033.0,
              T_bulk: float = 740.0, A_wetted: float = A_WETTED_CFD) -> float:
    """Convective coefficient h = q''_avg / (T_wall - T_bulk).

    Parses ``wallHeatFlux1/<latest>/wallHeatFlux.dat`` (columns
    ``Time patch min max integral``); ``integral`` (last column) is the total
    heat rate Q [W] over the tube patch. q''_avg = |Q| / A_wetted, so the sign
    convention of the wall-flux output does not affect the returned coefficient.

    ``ft`` is accepted for interface symmetry; ``A_wetted`` defaults to the
    measured tube-patch area of the converged case.
    """
    row = _last_data_row(
        _latest_pp_dir(case_dir, "wallHeatFlux1") / "wallHeatFlux.dat")
    Q = float(row[-1])                       # integral column = heat rate (W)
    q_avg = abs(Q) / A_wetted                # area-averaged wall heat flux (W/m²)
    return q_avg / (T_wall - T_bulk)


def extract_dp_and_f(case_dir, ft: FinnedTube, rho: float, U_max: float,
                     n_rows: int = 1) -> tuple[float, float]:
    """Streamwise Δp and Euler number per row.

    Δp = p_in - p_out from the ``pIn``/``pOut`` surfaceFieldValue probes (each
    ``.dat``: columns ``Time areaAverage(p)``; last row used). The friction
    factor (Euler number per row) is f = Δp / (0.5 * rho * U_max**2 * n_rows).
    """
    p_in = float(_last_data_row(
        _latest_pp_dir(case_dir, "pIn") / "surfaceFieldValue.dat")[-1])
    p_out = float(_last_data_row(
        _latest_pp_dir(case_dir, "pOut") / "surfaceFieldValue.dat")[-1])
    dp = p_in - p_out
    f = dp / (0.5 * rho * U_max ** 2 * n_rows)
    return dp, f
