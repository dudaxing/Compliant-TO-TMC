"""Frozen C1 task construction; no contact search or equilibrium solve.

The solid and TMC share the solid-bottom displacement trace. TMC also drives
its exterior bottom, an explicit background-medium boundary condition. Its
finite numerical domain is distinct from the wider physical rigid plane.
All lengths are mm and forces N. HuHu retains the existing broken-Q1 weak
form, with a solid-derived coefficient acting throughout each model.
"""
from dataclasses import dataclass

import numpy as np

from .split_state import SplitDisplacement
from .tmc import TMCModel


E = 100.0
NU = 0.3
THICKNESS = 1.0
GAP = 0.25
PRELOAD = 0.375
GAMMA = 1e-6
ALPHA = 1e-6
REFERENCE_LENGTH = 2.0
OBSTACLE_RECTANGLE = (-4.0, 6.0, 1.25, 2.25)


@dataclass(frozen=True)
class C1Problem:
    model: TMCModel
    base: np.ndarray
    direction: np.ndarray
    lift_origin: np.ndarray
    lift_shape: np.ndarray
    initial_state: SplitDisplacement
    top_nodes: np.ndarray
    bottom_nodes: np.ndarray
    bottom_body_nodes: np.ndarray
    reaction_groups: dict
    measure_bottom_body: np.ndarray
    measure_bottom_total: np.ndarray
    targets: np.ndarray


def _readonly(value):
    result = np.array(value, copy=True)
    result.setflags(write=False)
    return result


def _profile(x):
    """Continuous PWL trace, with zero reference mean on body and full base."""
    return np.where(x < 0.0, -x - 1.0,
                    np.where(x > 2.0, x - 3.0, 1.0 - 2.0 * np.abs(x - 1.0)))


def build_problem(kind, h, phase, initial_state=None):
    """Build one declared phase, preserving an inherited split state exactly.

    ``kind`` is A0, Aalpha or TMC. The allowed phases are:
    * A0/uniform_precontact: absolute bottom displacement 0 through GAP;
    * A0/uniform_closed: additional compression after GAP;
    * TMC/uniform_tmc: absolute bottom displacement;
    * any kind/perturbation: PWL amplitude about the PRELOAD state.

    Closed and perturbation phases require a stored SplitDisplacement. Only
    its shape and prescribed values are checked here; provenance, equilibrium,
    branch admissibility and material-specific warm-start admission belong
    to the runner and independent audit. No free displacement is collapsed
    into ``base``. Every returned initial component is an owned copy.

    Reaction groups are nodal force-sum conventions, not contact-force
    partitions: TMC body/outer groups split shared interface nodes equally.
    Reference-arclength mean measurements are separate normalized vectors.
    """
    if not isinstance(kind, str) or kind not in ("A0", "Aalpha", "TMC"):
        raise ValueError("kind must be A0, Aalpha or TMC")
    if (isinstance(h, (bool, np.bool_))
            or not isinstance(h, (int, float, np.integer, np.floating))
            or not np.isfinite(h) or h not in (0.25, 0.125)):
        raise ValueError("h must be a declared mesh size: .25 or .125 mm")
    allowed = {"uniform_precontact": ("A0",), "uniform_closed": ("A0",),
               "uniform_tmc": ("TMC",), "perturbation": ("A0", "Aalpha", "TMC")}
    if not isinstance(phase, str) or phase not in allowed or kind not in allowed[phase]:
        raise ValueError("undeclared kind/phase combination")
    needs_initial = phase in ("uniform_closed", "perturbation")
    if needs_initial != (initial_state is not None):
        raise ValueError("only closed and perturbation phases require an initial state")

    h = float(h)
    xmin, xmax, height = (-2.0, 4.0, 1.25) if kind == "TMC" else (0.0, 2.0, 1.0)
    nx, ny = int((xmax - xmin) / h), int(height / h)
    xx, yy = np.meshgrid(xmin + h * np.arange(nx + 1), h * np.arange(ny + 1))
    coordinates = np.column_stack((xx.ravel(), yy.ravel()))
    lower_left = (np.arange(ny)[:, None] * (nx + 1) + np.arange(nx)).ravel()
    connectivity = lower_left[:, None] + np.array([0, 1, nx + 2, nx + 1])
    centres = coordinates[connectivity].mean(axis=1)
    solid = (centres[:, 0] > 0.0) & (centres[:, 0] < 2.0) & (centres[:, 1] < 1.0)
    factors = np.where(solid, 1.0, GAMMA)
    lam, mu = E * NU / ((1 + NU) * (1 - 2 * NU)), E / (2 * (1 + NU))
    kr = 0.0 if kind == "A0" else ALPHA * REFERENCE_LENGTH**2 * (E / (3 * (1 - 2 * NU)) + 4 * mu / 3)
    bottom = np.arange(nx + 1, dtype=np.int64)
    top = ny * (nx + 1) + bottom
    bottom_x = coordinates[bottom, 0]
    body_bottom = bottom[(bottom_x >= 0.0) & (bottom_x <= 2.0)]
    anchor = bottom[bottom_x == 1.0].item()
    fixed = np.r_[2 * bottom + 1, 2 * anchor]
    if phase != "uniform_precontact":
        fixed = np.r_[fixed, 2 * top + 1]
    fixed = np.sort(fixed)
    model = TMCModel(coordinates, connectivity, lam * factors, mu * factors, kr,
                     h, h, THICKNESS, solid, fixed)

    if needs_initial:
        if not isinstance(initial_state, SplitDisplacement) or initial_state.ndof != model.ndof:
            raise ValueError("initial_state must be a matching SplitDisplacement")
        state = initial_state.copy()
        expected = np.zeros(model.ndof)
        expected[2 * bottom + 1] = GAP if phase == "uniform_closed" else PRELOAD
        expected[2 * top + 1] = 0.0 if kind == "TMC" else GAP
        if (not np.array_equal(state.lift[fixed], expected[fixed])
                or np.any(state.fluctuation[fixed] != 0.0)):
            raise ValueError("initial split state does not satisfy this phase's prescribed values")
    else:
        state = SplitDisplacement(np.zeros(model.ndof), np.zeros(model.ndof))
    origin = state.lift.copy()
    x, y = coordinates.T
    if phase == "uniform_precontact":
        vertical = np.ones(len(coordinates))
        targets = [0.0, 0.125, 0.21875, 0.25]
    elif phase == "uniform_closed":
        vertical = 1.0 - y
        targets = [0.0, 0.03125, 0.125, 0.25]
    else:
        vertical = np.where(y <= 1.0, 1.0, 4.0 * (1.25 - y)) if kind == "TMC" else 1.0 - y
        if phase == "perturbation":
            vertical = vertical * _profile(x)
            targets = [0.0, 0.015625, 0.03125, 0.046875, 0.0625]
        else:
            targets = [0.0, 0.125, 0.21875, 0.25, 0.28125, 0.375, 0.5]
    shape = np.zeros(model.ndof)
    shape[1::2] = vertical
    base, direction = np.zeros(model.ndof), np.zeros(model.ndof)
    base[fixed], direction[fixed] = origin[fixed], shape[fixed]

    bottom_group = np.zeros(model.ndof)
    bottom_group[2 * bottom + 1] = 1.0
    body_group = np.zeros(model.ndof)
    body_group[2 * body_bottom + 1] = 1.0
    if kind == "TMC":
        body_group[2 * body_bottom[[0, -1]] + 1] = 0.5
    groups = {"bottom": bottom_group, "bottom_body": body_group}
    if kind == "TMC":
        groups["bottom_outer"] = bottom_group - body_group
    if phase != "uniform_precontact":
        top_group = np.zeros(model.ndof)
        top_group[2 * top + 1] = 1.0
        groups["top"] = top_group

    def mean_vector(nodes, length):
        vector = np.zeros(model.ndof)
        vector[2 * nodes + 1] = h / length
        vector[2 * nodes[[0, -1]] + 1] *= 0.5
        return _readonly(vector)

    return C1Problem(model=model, base=_readonly(base), direction=_readonly(direction),
                     lift_origin=_readonly(origin), lift_shape=_readonly(shape), initial_state=state,
                     top_nodes=_readonly(top), bottom_nodes=_readonly(bottom),
                     bottom_body_nodes=_readonly(body_bottom),
                     reaction_groups={key: _readonly(value) for key, value in groups.items()},
                     measure_bottom_body=mean_vector(body_bottom, 2.0),
                     measure_bottom_total=mean_vector(bottom, xmax - xmin),
                     targets=_readonly(np.array(targets)))
