"""A restricted, initially closed, frictionless full-contact reference task.

This is a task builder, not a general contact solver. Its top-normal
constraints represent unilateral contact only while separately audited
normal multipliers are nonnegative and the solid is outside the obstacle.
It uses the existing O-line material/discretization and split solver.
"""
from dataclasses import dataclass

import numpy as np

from .tmc import TMCModel, rectangular_model


@dataclass
class ClosedPlaneProblem:
    model: TMCModel
    base: np.ndarray
    direction: np.ndarray
    lift_shape: np.ndarray
    top_nodes: np.ndarray
    bottom_nodes: np.ndarray
    reaction_groups: dict


def closed_plane_problem(h, amplitude):
    """Frozen 2 x 1 mm block: bottom vertical profile, top uy=0, free ux.

    h is one of the two prospectively declared mesh sizes. Amplitude changes
    the spatial profile, not the load control semantics. Bottom centre ux=0
    removes rigid horizontal translation; no other ux is prescribed.
    """
    if (isinstance(h, (bool, np.bool_)) or not np.isscalar(h)
            or not np.isreal(h) or h not in (.25, .125)):
        raise ValueError("h must be a declared mesh size: .25 or .125 mm")
    if (isinstance(amplitude, (bool, np.bool_)) or not np.isscalar(amplitude)
            or not np.isreal(amplitude) or amplitude not in (0., .125, .25)):
        raise ValueError("amplitude must be 0, .125 or .25")
    nx, ny = int(2 / h), int(1 / h)
    bottom = np.arange(nx + 1, dtype=np.int64)
    top = ny * (nx + 1) + bottom
    fixed = np.sort(np.r_[2 * bottom + 1, 2 * top + 1, 2 * (nx // 2)])
    model = rectangular_model(nx, ny, 2., 1., E=100., nu=.3, alpha=0.,
                              fixed_dofs=fixed, thickness=1.)
    x, y = model.coordinates.T
    profile = 1. + amplitude * (1. - 3. * (x - 1.) ** 2)
    base = np.zeros(model.ndof)
    direction = np.zeros(model.ndof)
    direction[2 * bottom + 1] = profile[bottom]
    lift_shape = np.zeros(model.ndof)
    lift_shape[1::2] = (1. - y) * profile
    groups = {}
    for name, nodes in (("top", top), ("bottom", bottom)):
        vector = np.zeros(model.ndof)
        vector[2 * nodes + 1] = 1.
        groups[name] = vector
    return ClosedPlaneProblem(model, base, direction, lift_shape, top, bottom, groups)
