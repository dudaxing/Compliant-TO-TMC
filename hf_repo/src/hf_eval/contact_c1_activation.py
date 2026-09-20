"""Explicit, bounded A0 boundary activation; no equilibrium evaluation."""
import numpy as np

from .contact_c1 import build_problem
from .split_prescribed import state_hash
from .split_state import SplitDisplacement


def prepare_closed_initial(source_state, h, *, projection_limit_mm=1e-12):
    """Zero only newly fixed top-uy fluctuations at the declared closure.

    The exact two-component displacement change is the removed fluctuation,
    including values below an ulp of the unchanged lift. The prescribed
    1e-12 mm limit cannot be overridden. No source array is modified.
    """
    if (isinstance(projection_limit_mm, (bool, np.bool_))
            or not isinstance(projection_limit_mm, (int, float, np.integer, np.floating))
            or not np.isfinite(projection_limit_mm) or projection_limit_mm != 1e-12):
        raise ValueError("projection_limit_mm must equal the frozen 1e-12 mm limit")
    precontact = build_problem("A0", h, "uniform_precontact")
    if not isinstance(source_state, SplitDisplacement):
        raise ValueError("source_state must be a matching SplitDisplacement")
    for values in (source_state.lift, source_state.fluctuation):
        if (not isinstance(values, np.ndarray) or values.shape != (precontact.model.ndof,)
                or values.dtype != np.dtype("float64") or not np.all(np.isfinite(values))):
            raise ValueError("source components must be finite matching binary64 vectors")
    old_fixed = precontact.model.fixed_dofs
    if np.any(source_state.fluctuation[old_fixed] != 0.):
        raise ValueError("source fluctuation on old fixed DOFs must be exactly zero")
    expected_old = np.where(old_fixed % 2 == 1, .25, 0.)
    if not np.array_equal(source_state.lift[old_fixed], expected_old):
        raise ValueError("source old fixed lift must have bottom uy=.25 and anchor ux=0")
    newly_fixed = np.setdiff1d(2 * precontact.top_nodes + 1, old_fixed)
    if np.any(source_state.lift[newly_fixed] != .25):
        raise ValueError("source lift on newly fixed top uy must equal .25")
    removed = source_state.fluctuation[newly_fixed].copy()
    maximum = float(np.max(np.abs(removed), initial=0.))
    if maximum > projection_limit_mm:
        raise ValueError("newly fixed fluctuation exceeds the frozen projection limit")
    fluctuation = source_state.fluctuation.copy()
    fluctuation[newly_fixed] = 0.0
    projected = SplitDisplacement(source_state.lift, fluctuation)
    unchanged = np.ones(precontact.model.ndof, dtype=bool)
    unchanged[newly_fixed] = False
    preserved = (projected.lift.tobytes() == source_state.lift.tobytes()
                 and projected.fluctuation[unchanged].tobytes()
                 == source_state.fluctuation[unchanged].tobytes())
    receipt = dict(policy="explicit_new_fixed_projection_v1",
                   new_fixed_dofs=newly_fixed.tolist(),
                   removed_fluctuation_mm=removed.tolist(),
                   maximum_projection_mm=maximum,
                   projection_limit_mm=float(projection_limit_mm),
                   source_state_sha256=state_hash(source_state),
                   projected_state_sha256=state_hash(projected),
                   unchanged_components_bitwise=preserved)
    return projected, receipt
