"""Storage authority and ownership; no mechanics or implicit rebasing."""
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext

import numpy as np
import pytest

from hf_eval.split_state import SplitDisplacement


def test_two_components_own_copies_and_are_read_only():
    lift = np.array([0.125, -0.25, 0.5, 0.75])
    fluctuation = np.array([2.**-60, -2.**-59, 2.**-58, -2.**-57])
    state = SplitDisplacement(lift, fluctuation)
    lift[:] = 0
    fluctuation[:] = 0
    assert state.ndof == 4
    assert state.representation == "split_displacement_v1"
    assert state.lift.dtype == state.fluctuation.dtype == np.dtype("float64")
    assert state.lift.flags.owndata and state.fluctuation.flags.owndata
    assert not state.lift.flags.writeable and not state.fluctuation.flags.writeable
    np.testing.assert_array_equal(state.lift, [0.125, -0.25, 0.5, 0.75])
    np.testing.assert_array_equal(state.fluctuation, [2.**-60, -2.**-59, 2.**-58, -2.**-57])
    with pytest.raises(ValueError):
        state.fluctuation[0] = 0
    with pytest.raises(FrozenInstanceError):
        state.lift = np.zeros(4)


def test_display_is_new_lossy_storage_not_the_authoritative_sum():
    state = SplitDisplacement([0.125, 0.125], [2.**-60, -2.**-60])
    first, second = state.u_display, state.u_display
    assert not np.shares_memory(first, second)
    assert not np.shares_memory(first, state.lift)
    np.testing.assert_array_equal(first, state.lift)
    with localcontext() as context:
        context.prec = 100
        authoritative = [Decimal.from_float(float(a)) + Decimal.from_float(float(b))
                         for a, b in zip(state.lift, state.fluctuation)]
        assert all(value != Decimal.from_float(float(shown)) for value, shown in zip(authoritative, first))
    first[:] = 7
    np.testing.assert_array_equal(second, [0.125, 0.125])
    np.testing.assert_array_equal(state.fluctuation, [2.**-60, -2.**-60])


def test_copy_and_legacy_import_preserve_component_values_without_aliasing():
    original = np.array([0.125, -0.25, 0.5, -0.75])
    state = SplitDisplacement.from_legacy(original)
    copied = state.copy()
    np.testing.assert_array_equal(state.lift, original)
    np.testing.assert_array_equal(state.fluctuation, np.zeros(4))
    np.testing.assert_array_equal(copied.lift, state.lift)
    np.testing.assert_array_equal(copied.fluctuation, state.fluctuation)
    assert not np.shares_memory(copied.lift, state.lift)
    assert not np.shares_memory(copied.fluctuation, state.fluctuation)
    original[:] = 0
    assert state.lift[0] == copied.lift[0] == 0.125


@pytest.mark.parametrize("bad", [
    [], [0.0], [0., 0., 0.], [[0., 0.]], [np.nan, 0.], [0., np.inf],
    [0j, 0j], [True, False], ["0", "0"], np.array([0., 0.], dtype=object),
])
@pytest.mark.parametrize("component", ["lift", "fluctuation"])
def test_invalid_component_is_rejected(bad, component):
    components = dict(lift=np.zeros(2), fluctuation=np.zeros(2))
    components[component] = bad
    with pytest.raises(ValueError):
        SplitDisplacement(**components)


def test_different_component_lengths_are_rejected():
    with pytest.raises(ValueError):
        SplitDisplacement(np.zeros(2), np.zeros(4))


def test_display_overflow_does_not_change_or_normalize_authority():
    state = SplitDisplacement([1e308, 0.], [1e308, 0.])
    with pytest.raises(ValueError, match="display"):
        _ = state.u_display
    assert state.lift[0] == state.fluctuation[0] == 1e308
