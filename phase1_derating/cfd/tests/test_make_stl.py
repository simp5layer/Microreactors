from pathlib import Path
from geometry.finned_tube import REFERENCE
from geometry.make_stl import write_unitcell_stl

def test_writes_nonempty_stl(tmp_path):
    p = tmp_path / "tube.stl"
    info = write_unitcell_stl(REFERENCE, str(p), n_fins=3)
    assert p.exists() and p.stat().st_size > 0
    assert info["triangles"] > 100
    lx, ly, lz = info["bbox"]
    assert lz >= 3 * REFERENCE.fin_pitch * 0.9  # spans the fins
