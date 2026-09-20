"""C1 task contracts only: these tests never evaluate or solve FE mechanics."""
import numpy as np
import pytest

from hf_eval.contact_c1 import build_problem, OBSTACLE_RECTANGLE
from hf_eval.prescribed import _inputs
from hf_eval.split_state import SplitDisplacement


def saved_state(kind, h, *, closing=False):
    """Geometric boundary-compatible test data, deliberately not a solved state."""
    p = build_problem("TMC", h, "uniform_tmc") if kind == "TMC" else build_problem("A0", h, "uniform_precontact")
    x, y = p.model.coordinates.T
    lift = np.zeros(p.model.ndof)
    if closing:
        lift[1::2] = 0.25
    elif kind == "TMC":
        lift[1::2] = 0.375 * np.where(y <= 1, 1, 4 * (1.25 - y))
    else:
        lift[1::2] = 0.25 + 0.125 * (1 - y)
    fluctuation = np.zeros_like(lift)
    interior = np.flatnonzero((y > 0) & (y < 1))[0]
    fluctuation[2 * interior + 1] = 2.0**-60
    fluctuation[2 * interior] = -0.0
    return SplitDisplacement(lift, fluctuation)


@pytest.mark.parametrize("h", [0.25, 0.125])
@pytest.mark.parametrize("kind", ["A0", "Aalpha", "TMC"])
def test_geometry_material_and_explicit_regularization_length(kind, h):
    p = build_problem(kind, h, "perturbation", saved_state(kind, h))
    m = p.model
    np.testing.assert_array_equal(m.coordinates.min(axis=0), [-2, 0] if kind == "TMC" else [0, 0])
    np.testing.assert_array_equal(m.coordinates.max(axis=0), [4, 1.25] if kind == "TMC" else [2, 1])
    assert m.thickness == 1 and m.hx == m.hy == h
    assert m.solid.sum() * h * h == 2.0
    assert (m.ne - m.solid.sum()) * h * h == (5.5 if kind == "TMC" else 0)
    np.testing.assert_allclose(m.lam[m.solid], 750 / 13, rtol=2e-16)
    np.testing.assert_allclose(m.mu[m.solid], 500 / 13, rtol=2e-16)
    if kind == "TMC":
        np.testing.assert_array_equal(m.lam[~m.solid], np.full((~m.solid).sum(), m.lam[m.solid][0] * 1e-6))
        np.testing.assert_array_equal(m.mu[~m.solid], np.full((~m.solid).sum(), m.mu[m.solid][0] * 1e-6))
    if kind == "A0":
        assert m.kr == 0
    else:
        # Exact decimal-material fraction versus the declared binary64 formula.
        assert abs(m.kr - 7 / 13000) <= 2 * np.spacing(7 / 13000)
    assert OBSTACLE_RECTANGLE == (-4, 6, 1.25, 2.25)
    assert OBSTACLE_RECTANGLE[0] < m.coordinates[p.top_nodes, 0].min()
    assert OBSTACLE_RECTANGLE[1] > m.coordinates[p.top_nodes, 0].max()


@pytest.mark.parametrize("h", [0.25, 0.125])
def test_uniform_phase_boundary_and_target_contracts(h):
    pre = build_problem("A0", h, "uniform_precontact")
    closed = build_problem("A0", h, "uniform_closed", saved_state("A0", h, closing=True))
    tmc = build_problem("TMC", h, "uniform_tmc")
    np.testing.assert_array_equal(pre.targets, [0, .125, .21875, .25])
    np.testing.assert_array_equal(closed.targets + .25, [.25, .28125, .375, .5])
    np.testing.assert_array_equal(tmc.targets, [0, .125, .21875, .25, .28125, .375, .5])
    assert "top" not in pre.reaction_groups
    assert not np.intersect1d(2 * pre.top_nodes + 1, pre.model.fixed_dofs).size
    assert np.all(pre.lift_shape[1::2] == 1)
    assert np.all(closed.lift_origin[2 * closed.top_nodes + 1] == .25)
    assert np.all(closed.lift_shape[2 * closed.top_nodes + 1] == 0)
    assert np.all(tmc.lift_shape[2 * tmc.top_nodes + 1] == 0)
    assert np.all(tmc.lift_shape[1::2][tmc.model.coordinates[:, 1] <= 1] == 1)
    for p in (pre, closed, tmc):
        fixed = p.model.fixed_dofs
        horizontal = fixed[fixed % 2 == 0]
        assert len(horizontal) == 1
        np.testing.assert_array_equal(p.model.coordinates[horizontal[0] // 2], [1, 0])
        np.testing.assert_array_equal(p.direction[fixed], p.lift_shape[fixed])
        np.testing.assert_array_equal(p.base[fixed], p.lift_origin[fixed])
        assert not np.any(p.base[p.model.free]) and not np.any(p.direction[p.model.free])
        assert not np.any(p.lift_shape[::2])
        for vector in p.reaction_groups.values():
            assert not np.any(vector[p.model.free])


@pytest.mark.parametrize("kind", ["A0", "Aalpha", "TMC"])
def test_perturbation_is_same_nested_trace_with_two_zero_means(kind):
    cases = [build_problem(kind, h, "perturbation", saved_state(kind, h)) for h in (.25, .125)]
    for p in cases:
        assert p.measure_bottom_body.sum() == pytest.approx(1)
        assert p.measure_bottom_total.sum() == pytest.approx(1)
        assert p.measure_bottom_body @ p.lift_shape == pytest.approx(0, abs=1e-16)
        assert p.measure_bottom_total @ p.lift_shape == pytest.approx(0, abs=1e-16)
        assert p.measure_bottom_body @ p.lift_origin == pytest.approx(.375)
        assert p.measure_bottom_total @ p.lift_origin == pytest.approx(.375)
        np.testing.assert_array_equal(p.targets, [0, .015625, .03125, .046875, .0625])
        bx = p.model.coordinates[p.bottom_body_nodes, 0]
        by = p.lift_shape[2 * p.bottom_body_nodes + 1]
        np.testing.assert_array_equal(by[bx == 0], [-1])
        np.testing.assert_array_equal(by[bx == 1], [1])
        np.testing.assert_array_equal(by[bx == 2], [-1])
        assert np.all(p.lift_shape[2 * p.top_nodes + 1] == 0)
    coarse, fine = cases
    cx = coarse.model.coordinates[coarse.bottom_nodes, 0]
    fx = fine.model.coordinates[fine.bottom_nodes, 0]
    np.testing.assert_array_equal(np.interp(fx, cx, coarse.lift_shape[2 * coarse.bottom_nodes + 1]),
                                  fine.lift_shape[2 * fine.bottom_nodes + 1])


@pytest.mark.parametrize("kind", ["A0", "Aalpha", "TMC"])
def test_force_partition_is_explicit_and_is_not_a_mean(kind):
    p = build_problem(kind, .25, "perturbation", saved_state(kind, .25))
    groups = p.reaction_groups
    ends = 2 * p.bottom_body_nodes[[0, -1]] + 1
    if kind == "TMC":
        np.testing.assert_array_equal(groups["bottom_body"] + groups["bottom_outer"], groups["bottom"])
        np.testing.assert_array_equal(groups["bottom_body"][ends], [.5, .5])
        np.testing.assert_array_equal(groups["bottom_outer"][ends], [.5, .5])
    else:
        np.testing.assert_array_equal(groups["bottom_body"], groups["bottom"])
        assert "bottom_outer" not in groups
    assert not np.array_equal(groups["bottom_body"], p.measure_bottom_body)
    # Exercise the unchanged controller's input contract, without mechanics.
    _inputs(p.model, p.base, p.direction, p.reaction_groups)


@pytest.mark.parametrize("kind", ["A0", "Aalpha", "TMC"])
def test_inherited_components_keep_every_bit_and_own_their_storage(kind):
    source = saved_state(kind, .125)
    p = build_problem(kind, .125, "perturbation", source)
    for actual, expected in ((p.initial_state.lift, source.lift),
                             (p.initial_state.fluctuation, source.fluctuation),
                             (p.lift_origin, source.lift)):
        np.testing.assert_array_equal(actual.view(np.uint64), expected.view(np.uint64))
        assert not np.shares_memory(actual, expected)
        assert not actual.flags.writeable
    index = np.flatnonzero(source.fluctuation != 0)[0]
    assert source.u_display[index] == source.lift[index]
    assert p.initial_state.fluctuation[index] == 2.0**-60


@pytest.mark.parametrize("kind,phase", [("Aalpha", "uniform_precontact"), ("TMC", "uniform_closed"),
                                        ("A0", "uniform_tmc"), ("a0", "perturbation"),
                                        ("A0", "unknown"), (None, "uniform_precontact")])
def test_undeclared_combinations_rejected(kind, phase):
    with pytest.raises(ValueError):
        build_problem(kind, .25, phase)


@pytest.mark.parametrize("h", [True, np.bool_(False), .5, 0, float("nan"), float("inf"), ".25", .25 + 0j])
def test_undeclared_or_nonreal_mesh_rejected(h):
    with pytest.raises(ValueError):
        build_problem("A0", h, "uniform_precontact")


def test_initial_state_is_required_only_for_inherited_phases():
    source = saved_state("A0", .25)
    with pytest.raises(ValueError):
        build_problem("A0", .25, "perturbation")
    with pytest.raises(ValueError):
        build_problem("A0", .25, "uniform_closed")
    with pytest.raises(ValueError):
        build_problem("A0", .25, "uniform_precontact", source)
    with pytest.raises(ValueError):
        build_problem("A0", .25, "perturbation", source.u_display)
    with pytest.raises(ValueError):
        build_problem("A0", .125, "perturbation", source)


@pytest.mark.parametrize("part", ["lift", "fluctuation"])
def test_inherited_fixed_value_mismatch_is_not_silently_rebased(part):
    source = saved_state("A0", .25)
    values = {"lift": source.lift.copy(), "fluctuation": source.fluctuation.copy()}
    values[part][1] += 2.0**-40
    with pytest.raises(ValueError, match="prescribed values"):
        build_problem("A0", .25, "perturbation", SplitDisplacement(**values))


def test_preload_state_cannot_be_used_as_closure_state():
    with pytest.raises(ValueError, match="prescribed values"):
        build_problem("A0", .25, "uniform_closed", saved_state("A0", .25))
