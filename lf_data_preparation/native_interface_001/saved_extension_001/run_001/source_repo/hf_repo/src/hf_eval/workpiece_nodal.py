"""Saved fixed-body nodal weak forces, in N; not face traction or pressure."""
from __future__ import annotations

from math import fsum
import numpy as np

from .boundary_geometry import exposed_q1_edges

COMPONENTS = ("total", "material", "regularization")
GROUPS = ("physical_only", "cut_only", "physical_and_cut", "interior")


def observe_workpiece_nodal_forces(model, force_arrays, *, symmetry_y_mm,
                                  moment_origin_mm=None):
    """Select all fixed body nodes from saved global forces without assembly.

    Body force is minus the internal weak force; holding reaction is opposite.
    The physical/cut intersection has its own group, so corner nodes occur once.
    A nodal vector is not attributable to either incident face. The moment is a
    derived nodal sum, about the supplied point or the body-node mean by default.
    Neither vectors nor moments reconstruct a continuous contact traction.
    """
    xy = np.asarray(model["coordinates"], dtype=float)
    conn = np.asarray(model["connectivity"])
    nodes = np.asarray(model["workpiece_nodes"], dtype=np.int64)
    cells = np.asarray(model["workpiece_cells"], dtype=np.int64)
    if (xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all()
            or np.ndim(symmetry_y_mm) != 0 or not np.isfinite(symmetry_y_mm) or not len(nodes)):
        raise ValueError("Require finite 2D coordinates, a symmetry coordinate and a nonempty body")
    if not np.array_equal(np.sort(nodes), np.unique(conn[cells])):
        raise ValueError("Workpiece nodes must be exactly the selected cell nodes")
    dofs = (2*nodes[:, None]+np.arange(2)).ravel()
    if (not np.array_equal(np.sort(dofs), np.sort(model["workpiece_dofs"]))
            or not np.all(np.isin(dofs, model["fixed_dofs"]))):
        raise ValueError("Both components of every workpiece node must be fixed")
    closed = exposed_q1_edges(conn, cells, xy)
    cut = closed[np.all(xy[closed, 1] == symmetry_y_mm, axis=1)]
    physical = closed[~np.all(xy[closed, 1] == symmetry_y_mm, axis=1)]
    on_physical = np.isin(nodes, np.unique(physical))
    on_cut = np.isin(nodes, np.unique(cut))
    masks = dict(physical_only=on_physical & ~on_cut, cut_only=on_cut & ~on_physical,
                 physical_and_cut=on_physical & on_cut, interior=~(on_physical | on_cut))
    positions = xy[nodes].copy()
    origin = (positions.mean(axis=0) if moment_origin_mm is None
              else np.asarray(moment_origin_mm, dtype=float))
    if origin.shape != (2,) or not np.isfinite(origin).all():
        raise ValueError("Moment origin must be a finite point in mm")
    forces = {}
    for component in COMPONENTS:
        saved = np.asarray(force_arrays["global_"+component+"_force"])
        if saved.shape != (2*len(xy),) or not np.isfinite(saved).all():
            raise ValueError("Saved global forces must be finite full-DOF vectors")
        forces[component] = -saved.reshape(-1, 2)[nodes].copy()
    holding = np.asarray(force_arrays["support_reaction"])
    if holding.shape != (2*len(xy),) or not np.isfinite(holding).all():
        raise ValueError("Saved holding reaction must be a finite full-DOF vector")
    lever = positions-origin

    def measure(selected):
        vectors = {name: [fsum(float(v) for v in values[selected, axis])
                          for axis in (0, 1)] for name, values in forces.items()}
        moments = {name: fsum(float(x)*float(fy)-float(y)*float(fx)
                             for (x, y), (fx, fy) in zip(lever[selected], values[selected]))
                   for name, values in forces.items()}
        return dict(force_on_body_N=vectors, moment_about_origin_Nmm=moments)

    complete = measure(np.ones(len(nodes), dtype=bool))
    groups = {name: dict(node_count=int(mask.sum()), **measure(mask))
              for name, mask in masks.items()}
    summary = dict(force_on_lower_body_N=complete["force_on_body_N"],
                   moment_about_origin_Nmm=complete["moment_about_origin_Nmm"],
                   holding_reaction_on_model_N=[fsum(float(v) for v in holding[dofs[axis::2]])
                                                for axis in (0, 1)], groups=groups)
    return dict(node_ids=nodes.copy(), coordinates_mm=positions, masks=masks,
                edges=dict(closed=closed, physical=physical, cut=cut),
                forces_on_body_N=forces, moment_origin_mm=origin.copy(), summary=summary)
