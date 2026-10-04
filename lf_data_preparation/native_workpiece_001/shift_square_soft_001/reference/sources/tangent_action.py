"""Compensated action of an already computed Q1 element Jacobian."""
from __future__ import annotations

import numpy as np

from . import compensated_invariants as ci
from .tmc_kernel import KernelError, _array


ACTION_VERSION = "q1_saved_tangent_dd_action_v1"


def apply_element_tangent_numpy(tangent, direction):
    """Apply (..., 8, 8) tensors to matching (..., 8) nodal directions.

    Products and their fixed-order sum retain both arithmetic words before
    rounding the action once. The original compensated support bounds apply.
    This consumes a tensor; it does not evaluate a constitutive Jacobian.
    """
    tensor = _array(tangent, "tangent")
    vector = _array(direction, "direction")
    if tensor.ndim < 2 or tensor.shape[-2:] != (8, 8) or vector.shape != tensor.shape[:-1]:
        raise KernelError("Tangent and direction require matching (...,8,8) and (...,8) shapes.",
                          code="invalid_shape")
    action = ci.dd_matmul(ci.dd_from(tensor), ci.dd_from(vector[..., None]))
    if not bool(ci.pair_supported(action)):
        raise KernelError("Tangent action exceeded the declared compensated arithmetic support range.",
                          code="unsupported_arithmetic_range")
    return ci.dd_value(action)[..., 0]
