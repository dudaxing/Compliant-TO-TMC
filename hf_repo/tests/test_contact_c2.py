"""Mechanically meaningful preflight for the isolated C2 factors (no solve)."""
import numpy as np
import pytest
from hf_eval.contact_c1 import build_problem as c1
from hf_eval.contact_c2 import build_problem, CASES


def test_baseline_preserves_the_existing_task_bitwise():
    old = c1("TMC", .125, "uniform_tmc")
    new = build_problem("baseline_h0125")
    for key in ("coordinates", "connectivity", "lam", "mu", "solid", "fixed_dofs", "edofs"):
        assert np.array_equal(getattr(old.model, key), getattr(new.model, key))
    assert old.model.kr == new.model.kr
    for key in ("base", "direction", "lift_origin", "lift_shape", "top_nodes", "bottom_nodes",
                "bottom_body_nodes", "measure_bottom_body", "measure_bottom_total"):
        a, b = getattr(old, key), new.arrays[key]
        assert a.dtype == b.dtype and a.tobytes() == b.tobytes(), key
    for key in ("top", "bottom"):
        assert np.array_equal(old.reaction_groups[key], new.groups[key])
    assert np.array_equal(old.targets, new.targets)


@pytest.mark.parametrize("case,ne,ndof,nfixed", [
    ("baseline_h0125", 480, 1078, 99),
    ("mesh_h00625", 1920, 4074, 195),
    ("padding_2p5", 560, 1254, 115),
    ("outer_free", 480, 1078, 67),
])
def test_declared_mesh_and_constraints(case, ne, ndof, nfixed):
    p = build_problem(case)
    assert (p.model.ne, p.model.ndof, len(p.model.fixed_dofs)) == (ne, ndof, nfixed)
    # Two translations plus in-plane rigid rotation are all excluded by BCs.
    modes = np.zeros((ndof, 3))
    modes[0::2, 0], modes[1::2, 1] = 1., 1.
    modes[0::2, 2] = -p.model.coordinates[:, 1]
    modes[1::2, 2] = p.model.coordinates[:, 0]
    assert np.linalg.matrix_rank(modes[p.model.fixed_dofs]) == 3


@pytest.mark.parametrize("case", CASES)
def test_shared_physics_and_no_free_dof_reaction_groups(case):
    p = build_problem(case)
    baseline = build_problem("baseline_h0125")
    assert p.model.kr == baseline.model.kr
    for key in ("lam", "mu"):
        assert np.array_equal(np.unique(getattr(p.model, key)), np.unique(getattr(baseline.model, key)))
    for v in p.groups.values():
        assert np.any(v != 0) and np.all(v[p.model.free] == 0)
    assert np.all(p.arrays["direction"][p.model.free] == 0)
    assert np.isclose(p.arrays["measure_bottom_body"].sum(), 1., atol=1e-15)
    assert np.isclose(p.arrays["measure_bottom_total"].sum(), 1., atol=1e-15)
    assert p.arrays["measure_bottom_body"] @ p.arrays["lift_shape"] == 1.
    assert np.all(p.initial_state.lift == 0) and np.all(p.initial_state.fluctuation == 0)


def test_release_changes_only_declared_outer_constraints_and_force_group():
    a, b = build_problem("baseline_h0125"), build_problem("outer_free")
    for key in a.arrays:
        if key not in ("fixed_dofs", "direction", "group_bottom"):
            assert np.array_equal(a.arrays[key], b.arrays[key]), key
    outer = np.setdiff1d(a.arrays["bottom_nodes"], a.arrays["bottom_body_nodes"])
    released = 2*outer+1
    assert np.array_equal(np.setdiff1d(a.model.fixed_dofs, b.model.fixed_dofs), released)
    assert np.all(b.arrays["lift_shape"][released] == 1.)
    assert np.all(b.arrays["direction"][released] == 0.)
    assert np.all(np.isin(released, b.model.free))


def test_padding_keeps_common_coordinates_and_materials():
    a, b = build_problem("baseline_h0125"), build_problem("padding_2p5")
    x = b.model.coordinates[:, 0]
    subset = b.model.coordinates[(x >= -2) & (x <= 4)]
    assert np.array_equal(a.model.coordinates, subset)
    assert b.model.hx == a.model.hx
    assert b.model.kr == a.model.kr  # domain width is not the regularization Lref


def test_undeclared_factor_cannot_be_run():
    with pytest.raises(ValueError, match="undeclared"):
        build_problem("tune_gamma")
