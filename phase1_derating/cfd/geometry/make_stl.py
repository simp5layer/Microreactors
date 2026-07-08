"""Generate an STL of a staggered-tube unit cell: a cylinder with n annular fins.
Used as snappyHexMesh input. Axis = z = tube axis / spanwise (the fins stack
along z at fin_pitch); crossflow is streamwise in y. z is cyclic/symmetry, not streamwise."""
import numpy as np
from stl import mesh as stlmesh
from geometry.finned_tube import FinnedTube

def _cylinder(r, z0, z1, n_theta):
    th = np.linspace(0, 2*np.pi, n_theta, endpoint=False)
    tris = []
    for i in range(n_theta):
        a, b = th[i], th[(i+1) % n_theta]
        p0 = [r*np.cos(a), r*np.sin(a), z0]; p1 = [r*np.cos(b), r*np.sin(b), z0]
        p2 = [r*np.cos(a), r*np.sin(a), z1]; p3 = [r*np.cos(b), r*np.sin(b), z1]
        tris += [[p0, p1, p2], [p1, p3, p2]]
    return tris

def _annulus(ri, ro, z, n_theta, flip=False):
    """Flat annular ring at height z. Default winding gives a +z outward normal;
    set flip=True for the bottom (z0) fin face so its normal points -z (into the
    air below), i.e. consistently outward from the fin solid."""
    th = np.linspace(0, 2*np.pi, n_theta, endpoint=False)
    tris = []
    for i in range(n_theta):
        a, b = th[i], th[(i+1) % n_theta]
        pi0=[ri*np.cos(a),ri*np.sin(a),z]; pi1=[ri*np.cos(b),ri*np.sin(b),z]
        po0=[ro*np.cos(a),ro*np.sin(a),z]; po1=[ro*np.cos(b),ro*np.sin(b),z]
        t = [[pi0, po0, pi1], [po0, po1, pi1]]
        if flip:                                          # reverse winding -> flip normal
            t = [[tri[0], tri[2], tri[1]] for tri in t]
        tris += t
    return tris

def write_unitcell_stl(ft: FinnedTube, path: str, n_fins: int = 3, n_theta: int = 64) -> dict:
    r_t, r_f = ft.d_o/2, ft.d_o/2 + ft.fin_h
    total_z = n_fins * ft.fin_pitch
    # Fin bands (the tube surface inside a band is interior to the fin solid and
    # must NOT be emitted, or snappy sees a coincident interior patch).
    bands = [((k + 0.5) * ft.fin_pitch - ft.fin_t/2,
              (k + 0.5) * ft.fin_pitch + ft.fin_t/2) for k in range(n_fins)]
    # Bare-tube cylinder only over the sub-intervals between fin bands.
    tris = []
    z_prev = 0.0
    for z0b, z1b in bands:
        if z0b > z_prev:
            tris += _cylinder(r_t, z_prev, z0b, n_theta)
        z_prev = z1b
    if total_z > z_prev:
        tris += _cylinder(r_t, z_prev, total_z, n_theta)
    for k in range(n_fins):                               # fins
        zc = (k + 0.5) * ft.fin_pitch
        z0, z1 = zc - ft.fin_t/2, zc + ft.fin_t/2
        tris += _annulus(r_t, r_f, z0, n_theta, flip=True)   # bottom face -> -z normal
        tris += _annulus(r_t, r_f, z1, n_theta, flip=False)  # top face    -> +z normal
        tris += _cylinder(r_f, z0, z1, n_theta)           # fin edge
    data = np.zeros(len(tris), dtype=stlmesh.Mesh.dtype)
    m = stlmesh.Mesh(data)
    for i, t in enumerate(tris):
        m.vectors[i] = np.array(t)
    m.save(path)
    return {"triangles": len(tris), "bbox": (2*r_f, 2*r_f, total_z)}
