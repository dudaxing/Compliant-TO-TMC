"""Synthetic, grid-aligned two-block normal-contact task (mm/N/MPa).

This task is independent of LF and HF-1 geometry. Both blocks are elastic;
the two exterior platens are prescribed boundaries, not stiff material cells.
The entire domain has ux=0. This deliberate one-dimensional deformation mode
has zero HuHu on its exact piecewise-affine solution; it is not a cylinder test.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from .data import canonical_hash
from .tmc import TMCModel, TMCError


SCHEMA = "hf-normal-contact-task-1.0"
UNITS = {"length": "mm", "force": "N", "stress": "MPa", "energy": "N mm"}


@dataclass(frozen=True)
class NormalContactProblem:
    model: TMCModel
    task: dict
    task_sha256: str
    geometry_id: str
    mesh_id: str
    body_ids: np.ndarray
    base: np.ndarray
    direction: np.ndarray
    reaction_groups: dict
    regions: dict
    gap_vector: np.ndarray
    reference_inputs: dict


def _number(value, name, positive=True):
    if isinstance(value, (bool, str, complex)) or not np.isscalar(value):
        raise TMCError(f"{name} must be a real number")
    result = float(value)
    if not np.isfinite(result) or (positive and result <= 0):
        raise TMCError(f"invalid {name}")
    return result


def _keys(obj, names, name):
    if not isinstance(obj, dict) or set(obj) != set(names):
        raise TMCError(f"{name} has missing or unsupported fields")


def _freeze(a):
    a.setflags(write=False)
    return a


def build_normal_contact(task_dict):
    """Validate an explicit synthetic task and build the full-domain Q1 mesh.

    Material interfaces must be aligned exactly to an integer number of cells.
    Physical identity excludes discretization and gamma; task and mesh hashes
    identify those choices separately. No geometric snapping or smoothing.
    """
    _keys(task_dict, {"schema_version", "units", "geometry", "material", "gamma",
                      "regularization", "mesh_size_mm", "targets_mm", "constraints"}, "task")
    task = deepcopy(task_dict)
    if task["schema_version"] != SCHEMA or task["units"] != UNITS:
        raise TMCError("unsupported normal-contact schema or units")
    if task["constraints"] != {"ux": "all_zero", "top_uy": "zero", "bottom_uy": "d"}:
        raise TMCError("uniform benchmark requires all ux=0, top uy=0, bottom uy=d")
    geom = task["geometry"]
    _keys(geom, {"width_mm", "lower_height_mm", "upper_height_mm", "gap_mm", "thickness_mm"}, "geometry")
    geom = {k: _number(v, k) for k, v in geom.items()}
    material = task["material"]
    _keys(material, {"E_MPa", "nu", "formulation"}, "material")
    E, nu = _number(material["E_MPa"], "E"), _number(material["nu"], "nu", False)
    if not 0 <= nu < .5 or material["formulation"] != "plane_strain":
        raise TMCError("expected compressible plane strain, 0<=nu<.5")
    _keys(task["regularization"], {"alpha", "length_mm"}, "regularization")
    alpha = _number(task["regularization"]["alpha"], "alpha", False)
    Lr = _number(task["regularization"]["length_mm"], "Lr")
    gamma = _number(task["gamma"], "gamma")
    if alpha < 0 or gamma > 1:
        raise TMCError("alpha must be nonnegative and 0<gamma<=1")
    h = _number(task["mesh_size_mm"], "mesh size")
    counts = {}
    for k in ("width_mm", "lower_height_mm", "gap_mm", "upper_height_mm"):
        ratio = geom[k] / h
        if ratio != int(ratio) or int(ratio) < 1 or int(ratio)*h != geom[k]:
            raise TMCError(f"{k} must align exactly to this uniform mesh")
        counts[k] = int(ratio)
    nx = counts["width_mm"]
    nlow, ngap, nup = [counts[k] for k in ("lower_height_mm", "gap_mm", "upper_height_mm")]
    ny = nlow + ngap + nup
    raw_targets = np.asarray(task["targets_mm"])
    if raw_targets.dtype.kind not in "iuf" or raw_targets.ndim != 1:
        raise TMCError("targets must be real, finite and increasing")
    targets = np.asarray(raw_targets, dtype=float)
    total_height = geom["lower_height_mm"] + geom["gap_mm"] + geom["upper_height_mm"]
    if (len(targets) < 2 or not np.all(np.isfinite(targets)) or targets[0] != 0
            or np.any(np.diff(targets) <= 0) or targets[-1] >= total_height):
        raise TMCError("targets must start at zero and increase below total height")
    # Avoid allocating unsupported accidentally enormous synthetic fixtures.
    if nx*ny > 100000:
        raise TMCError("synthetic normal benchmark exceeds 100000 cells")
    xx, yy = np.meshgrid(np.arange(nx+1)*h, np.arange(ny+1)*h)
    coordinates = np.column_stack((xx.ravel(), yy.ravel()))
    ll = (np.arange(ny)[:, None]*(nx+1) + np.arange(nx)).ravel()
    connectivity = ll[:, None] + [0, 1, nx+2, nx+1]
    # 1=lower elastic block, 0=third medium, 2=upper elastic block.
    body = np.repeat(np.r_[np.ones(nlow, int), np.zeros(ngap, int), np.full(nup, 2)], nx)
    solid = body != 0
    factors = np.where(solid, 1., gamma)
    lam_s, mu_s = E*nu/((1+nu)*(1-2*nu)), E/(2*(1+nu))
    lam, mu = lam_s*factors, mu_s*factors
    kr = alpha*Lr**2*(E/(3*(1-2*nu)) + 4*mu_s/3)
    bottom = np.arange(nx+1)
    top = np.arange(ny*(nx+1), (ny+1)*(nx+1))
    low_interface = np.arange(nlow*(nx+1), (nlow+1)*(nx+1))
    up_interface = np.arange((nlow+ngap)*(nx+1), (nlow+ngap+1)*(nx+1))
    ndof = 2*len(coordinates)
    fixed = np.unique(np.r_[np.arange(0, ndof, 2), 2*bottom+1, 2*top+1])
    model = TMCModel(coordinates, connectivity, lam, mu, kr, h, h, geom["thickness_mm"], solid, fixed)
    base, direction = np.zeros(ndof), np.zeros(ndof)
    direction[2*bottom+1] = 1
    top_vector = np.zeros(ndof)
    top_vector[2*top+1] = 1
    groups = {"bottom_platen": _freeze(direction.copy()), "top_platen": _freeze(top_vector)}
    # Reference arclength trapezoid weights, sum exactly 1 for these dyadic grids.
    weights = np.ones(nx+1)/nx
    weights[[0, -1]] *= .5
    gap_vector = np.zeros(ndof)
    gap_vector[2*up_interface+1] = weights
    gap_vector[2*low_interface+1] = -weights
    regions = dict(bottom_nodes=bottom.tolist(), top_nodes=top.tolist(),
                   lower_interface_nodes=low_interface.tolist(), upper_interface_nodes=up_interface.tolist(),
                   interface_weights=weights.tolist(), body_labels={"0":"third_medium", "1":"lower_elastic", "2":"upper_elastic"},
                   reference_normal=[0, 1], all_ux_zero=True, full_model=True, force_multiplier=1)
    reference = dict(lam_s=float(lam[0]), mu_s=float(mu[0]),
                     lam_v=float(lam[nlow*nx]), mu_v=float(mu[nlow*nx]),
                     width=geom["width_mm"], H1=geom["lower_height_mm"], H2=geom["upper_height_mm"],
                     gap=geom["gap_mm"], thickness=geom["thickness_mm"])
    identity = {"schema_version":"hf-normal-geometry-1.0", "units":UNITS, "geometry":geom}
    mesh = {"geometry":identity, "hx":h, "hy":h, "nx":nx, "ny":ny, "ordering":"x_fast_bottom_up_BL_BR_TR_TL"}
    return NormalContactProblem(model, task, canonical_hash(task), canonical_hash(identity),
                                canonical_hash(mesh), _freeze(body), _freeze(base), _freeze(direction),
                                groups, regions, _freeze(gap_vector), reference)


def normal_task_from_spec(spec, gamma, mesh_size):
    """Extract one ordinary JSON task; no solver or validation settings hidden."""
    return dict(schema_version=SCHEMA, units=deepcopy(UNITS), geometry=deepcopy(spec["geometry"]),
                material=deepcopy(spec["material"]), gamma=gamma,
                regularization=deepcopy(spec["regularization"]), mesh_size_mm=mesh_size,
                targets_mm=list(spec["targets_mm"]), constraints={"ux":"all_zero", "top_uy":"zero", "bottom_uy":"d"})
