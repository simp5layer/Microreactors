"""Generate an STL of a staggered-tube unit cell: a cylinder with n annular fins.
Used as snappyHexMesh input. Axis = z (streamwise-vertical fin stack)."""
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

def _annulus(ri, ro, z, n_theta):
    th = np.linspace(0, 2*np.pi, n_theta, endpoint=False)
    tris = []
    for i in range(n_theta):
        a, b = th[i], th[(i+1) % n_theta]
        pi0=[ri*np.cos(a),ri*np.sin(a),z]; pi1=[ri*np.cos(b),ri*np.sin(b),z]
        po0=[ro*np.cos(a),ro*np.sin(a),z]; po1=[ro*np.cos(b),ro*np.sin(b),z]
        tris += [[pi0, po0, pi1], [po0, po1, pi1]]
    return tris

def write_unitcell_stl(ft: FinnedTube, path: str, n_fins: int = 3, n_theta: int = 64) -> dict:
    r_t, r_f = ft.d_o/2, ft.d_o/2 + ft.fin_h
    total_z = n_fins * ft.fin_pitch
    tris = _cylinder(r_t, 0.0, total_z, n_theta)          # tube surface
    for k in range(n_fins):                               # fins
        zc = (k + 0.5) * ft.fin_pitch
        z0, z1 = zc - ft.fin_t/2, zc + ft.fin_t/2
        tris += _annulus(r_t, r_f, z0, n_theta)
        tris += _annulus(r_t, r_f, z1, n_theta)
        tris += _cylinder(r_f, z0, z1, n_theta)           # fin edge
    data = np.zeros(len(tris), dtype=stlmesh.Mesh.dtype)
    m = stlmesh.Mesh(data)
    for i, t in enumerate(tris):
        m.vectors[i] = np.array(t)
    m.save(path)
    return {"triangles": len(tris), "bbox": (2*r_f, 2*r_f, total_z)}
