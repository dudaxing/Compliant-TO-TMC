"""Explicit two-component displacement storage, with no mechanics imports.

The physical value is the exact sum of the two stored binary64 components.
``u_display`` is a lossy, newly allocated view for plotting, never a mechanics
input. There is no implicit recombination, normalization or change of lift.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import numpy as np


def _vector(value, name):
    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf" or raw.ndim != 1 or len(raw) == 0 or len(raw) % 2:
        raise ValueError(f"{name} must be a real full-DOF vector of positive even length")
    result = np.array(raw, dtype=np.float64, copy=True)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain finite binary64 values")
    result.setflags(write=False)
    return result


@dataclass(frozen=True, eq=False)
class SplitDisplacement:
    """Owned, read-only ``lift`` and ``fluctuation`` arrays in DOF order.

    Arrays are copied on construction. DOFs are interleaved ux/uy; their
    physical units are inherited from the explicit model (HF-4 uses mm).
    Comparison and rollback must inspect both arrays, not ``u_display``.
    """

    lift: np.ndarray
    fluctuation: np.ndarray
    representation: ClassVar[str] = "split_displacement_v1"

    def __post_init__(self):
        lift = _vector(self.lift, "lift")
        fluctuation = _vector(self.fluctuation, "fluctuation")
        if lift.shape != fluctuation.shape:
            raise ValueError("lift and fluctuation must have the same full-DOF shape")
        object.__setattr__(self, "lift", lift)
        object.__setattr__(self, "fluctuation", fluctuation)

    @property
    def ndof(self):
        return len(self.lift)

    @property
    def u_display(self):
        """Return a new rounded display array; neither component is changed."""
        with np.errstate(over="ignore", invalid="ignore"):
            result = self.lift + self.fluctuation
        if not np.all(np.isfinite(result)):
            raise ValueError("the rounded display displacement is nonfinite")
        return result

    def copy(self):
        """Copy both components without rounding their physical sum."""
        return SplitDisplacement(self.lift, self.fluctuation)

    @classmethod
    def from_legacy(cls, u):
        """Import the exact old binary64 state as ``(u, 0)``; no repair."""
        values = _vector(u, "legacy displacement")
        return cls(values, np.zeros_like(values))
