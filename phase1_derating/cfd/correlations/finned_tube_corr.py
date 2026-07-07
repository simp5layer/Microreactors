"""Published staggered finned-tube correlations for CFD validation.
Briggs & Young (1963) heat transfer; Robinson & Briggs (1966) friction."""
from geometry.finned_tube import FinnedTube

def briggs_young_nu(Re: float, Pr: float, ft: FinnedTube) -> float:
    s = ft.fin_pitch - ft.fin_t          # inter-fin gap
    return (0.134 * Re**0.681 * Pr**(1/3)
            * (s / ft.fin_h)**0.2 * (s / ft.fin_t)**0.1134)

def briggs_young_f(Re: float, ft: FinnedTube) -> float:
    # Robinson-Briggs friction (Euler number per tube row)
    return 9.465 * Re**(-0.316) * (ft.S_T / ft.d_o)**(-0.927)
