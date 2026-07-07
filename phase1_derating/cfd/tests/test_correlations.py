import math
from geometry.finned_tube import REFERENCE
from correlations.finned_tube_corr import briggs_young_nu, briggs_young_f

def test_nu_increases_with_Re():
    ft = REFERENCE
    assert briggs_young_nu(5000, 0.7, ft) < briggs_young_nu(20000, 0.7, ft)

def test_nu_reasonable_magnitude():
    # staggered finned tube at Re=10k should give Nu ~ O(50-120)
    nu = briggs_young_nu(10000, 0.7, REFERENCE)
    assert 30 < nu < 200

def test_f_decreases_with_Re():
    ft = REFERENCE
    assert briggs_young_f(20000, ft) < briggs_young_f(5000, ft)
