"""Original stored-field comparison only; no geometry or mechanics imports."""
INTRINSIC = {"coordinates", "connectivity", "solid", "lam", "mu", "gamma", "edofs",
    "solid_nodes", "solid_dofs", "b_in", "b_out", "grad", "hessian", "weights", "points",
    "kr", "hx", "hy", "thickness", "k_out", "force_scale_per_length"}
OVERLAY = {"fixed_dofs", "free_dofs", "workpiece_cells", "workpiece_nodes", "workpiece_dofs",
    "workpiece_background_symmetry_overlap_dofs"}


def model_delta(saved, original):
    """Compare stored fields only; no response, operators or model reconstruction."""
    assert set(saved) == set(original) == INTRINSIC | OVERLAY
    return sorted(k for k in saved if saved[k].dtype != original[k].dtype
        or saved[k].shape != original[k].shape or saved[k].tobytes() != original[k].tobytes())
