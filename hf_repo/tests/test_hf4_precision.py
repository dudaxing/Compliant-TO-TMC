"""Ordinary-data checks for the independent HF-4 prescribed-motion audit.

No production kernel or solver is imported. Analytic affine forces, actual
binary64 input promotion and an independent centered difference cover the
adapter's reaction, constraint, normalization and HuHu derivative semantics.
"""
from decimal import Decimal, localcontext
import importlib.util
from pathlib import Path

import numpy as np
import pytest


_path = Path(__file__).resolve().parents[1]/"scripts"/"hf4_precision_reference.py"
_spec = importlib.util.spec_from_file_location("hf4_precision_under_test", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
evaluate = _module.evaluate_prescribed_state


def D(value):
    return Decimal.from_float(float(value))


def fixture(*, fixed=None, solid=True):
    """Unit-square Q1 operators tabulated without the production FE package."""
    signs = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]])
    grad, weights = [], []
    for xi, wx in zip((-1, 0, 1), (1, 4, 1)):
        for eta, wy in zip((-1, 0, 1), (1, 4, 1)):
            grad.append([[sx*(1+sy*eta)/2, sy*(1+sx*xi)/2] for sx, sy in signs])
            weights.append(wx*wy/36)
    hessian = np.zeros((4, 2, 2))
    hessian[:, 0, 1] = hessian[:, 1, 0] = signs[:, 0]*signs[:, 1]
    return dict(grad=np.array(grad), hessian=hessian, weights=np.array(weights),
                lam=np.array([1.25]), mu=np.array([0.75]), kr=np.array(0.02),
                connectivity=np.array([[0, 1, 2, 3]]),
                fixed_dofs=np.arange(8) if fixed is None else np.array(fixed),
                solid=np.array([solid]))


def motion_and_groups():
    bottom, top = np.zeros(8), np.zeros(8)
    bottom[[1, 3]], top[[5, 7]] = 1.0, 1.0
    return bottom.copy(), {"bottom": bottom, "top": top}


def call(u=None, *, data=None, d=0.0, base=None, direction=None,
         reaction_groups=None, force_scale_per_length=2.3, precision=50, **kwargs):
    motion, groups = motion_and_groups()
    return evaluate(fixture() if data is None else data, np.zeros(8) if u is None else u,
                    d, np.zeros(8) if base is None else base,
                    motion if direction is None else direction,
                    groups if reaction_groups is None else reaction_groups,
                    force_scale_per_length, precision=precision, **kwargs)


def test_zero_state_uses_positive_specification_floor_without_fictitious_load():
    result = call()
    with localcontext() as context:
        context.prec = 50
        expected = Decimal("1e-8")*D(2.3)*Decimal("1e-6")
    assert result["force_scale_decimal"] == expected
    assert result["relative_residual_decimal"] == 0
    assert result["relative_constraint_decimal"] == 0
    assert result["relative_force_balance_decimal"] == 0
    assert all(value == 0 for value in result["external_decimal"])
    assert result["drive_force_decimal"] == 0
    assert result["group_reactions_decimal"] == {"bottom": Decimal(0), "top": Decimal(0)}
    assert result["minimum_J_decimal"] == 1
    assert result["positive_J"]
    assert result["solid_material_energy_decimal"] == 0
    assert result["medium_material_energy_decimal"] == 0
    assert result["minimum_J_medium_decimal"] is None


def test_affine_compression_has_analytic_nominal_force_and_zero_huhu():
    motion, _ = motion_and_groups()
    data = fixture()
    result = call(0.125*motion, d=0.125, data=data)
    with localcontext() as context:
        context.prec = 50
        stretch = Decimal(1)-D(0.125)
        lam, mu = D(data["lam"][0]), D(data["mu"][0])
        weight_sum = sum((D(value) for value in data["weights"]), Decimal(0))
        # Use the actual quadrature weights; their exact promoted sum need not
        # equal geometric area, even though the binary64 sum can round to one.
        pressure = mu*(1/stretch-stretch)-lam*stretch.ln()/stretch
        expected_force = weight_sum*pressure
        energy_density = (lam*stretch.ln()**2+mu*(stretch**2-1-2*stretch.ln()))/2
        assert abs(result["group_reactions_decimal"]["bottom"]-expected_force) < Decimal("1e-45")
        assert abs(result["group_reactions_decimal"]["top"]+expected_force) < Decimal("1e-45")
        assert abs(result["material_energy_decimal"][0]-weight_sum*energy_density) < Decimal("1e-45")
        assert result["drive_force_decimal"] == result["group_reactions_decimal"]["bottom"]
    assert result["group_reactions_decimal"]["bottom"] > 0
    assert result["group_reactions_decimal"]["top"] < 0
    assert all(value == 0 for value in result["regularization_internal_decimal"])
    assert all(value == Decimal("0.875") for row in result["J_decimal"] for value in row)
    assert result["constraint_error_decimal"] == 0
    assert result["relative_force_balance_decimal"] < Decimal("1e-45")


def test_nonzero_prescription_is_promoted_before_product_and_saved_u_is_unchanged():
    motion, groups = motion_and_groups()
    motion *= 0.2
    base = np.zeros(8)
    base[[1, 3]] = 0.1
    u = base+0.3*motion
    result = call(u, d=0.3, base=base, direction=motion, reaction_groups=groups)
    with localcontext() as context:
        context.prec = 50
        exact = D(0.1)+D(0.3)*D(0.2)
        expected_error = D(u[1])-exact
        assert result["prescribed_displacement_decimal"][1] == exact
        assert result["constraint_decimal"][1] == expected_error
        assert result["constraint_error_decimal"] == abs(expected_error)
        assert result["relative_constraint_decimal"] == abs(expected_error)/D(0.3)
        assert expected_error != 0
        # The audit evaluates the stored state, not the ideal prescribed state.
        assert all(abs(value-(1-D(u[1]))) < Decimal("1e-47")
                   for row in result["J_decimal"] for value in row)
        assert result["J_decimal"][0][0] != 1-exact


def test_group_products_are_decimal_and_signs_are_explicit():
    u = np.array([0, 0.125, 0, 0.125, 0, 0.03125, 0, 0], dtype=float)
    _, groups = motion_and_groups()
    weighted = np.zeros(8)
    weighted[[1, 3]] = [0.1, 0.9]
    groups.update(weighted=weighted, weighted_reverse=-weighted)
    result = call(u, d=0.125, reaction_groups=groups)
    with localcontext() as context:
        context.prec = 50
        expected = sum((D(v)*r for v, r in zip(weighted, result["support_reaction_decimal"])), Decimal(0))
        assert result["group_reactions_decimal"]["weighted"] == expected
        assert result["group_reactions_decimal"]["weighted_reverse"] == -expected
    assert result["group_reactions_decimal"]["weighted"] != D(np.dot(weighted, result["support_reaction"]))


def test_overlapping_groups_do_not_duplicate_the_global_reaction():
    motion, groups = motion_and_groups()
    original = call(0.125*motion, d=0.125)
    groups["same_bottom_again"] = groups["bottom"].copy()
    repeated = call(0.125*motion, d=0.125, reaction_groups=groups)
    assert repeated["group_reactions_decimal"]["same_bottom_again"] == original["group_reactions_decimal"]["bottom"]
    assert repeated["support_reaction_decimal"] == original["support_reaction_decimal"]
    assert repeated["force_balance_decimal"] == original["force_balance_decimal"]
    assert repeated["force_scale_decimal"] == original["force_scale_decimal"]


def test_free_internal_force_is_residual_and_not_constraint_reaction():
    data = fixture(fixed=[0, 1, 2, 3, 4, 6])
    motion, groups = motion_and_groups()
    result = call(0.125*motion, d=0.125, data=data, reaction_groups={"bottom": groups["bottom"]})
    fixed, free = set(data["fixed_dofs"]), [5, 7]
    assert any(result["internal_decimal"][i] != 0 for i in free)
    for i in range(8):
        assert result["support_reaction_decimal"][i] == (result["internal_decimal"][i] if i in fixed else Decimal(0))
        if i in free:
            assert result["constraint_decimal"][i] == 0
    assert result["residual_decimal"] == result["internal_decimal"]
    with localcontext() as context:
        context.prec = 50
        nfree = sum((result["internal_decimal"][i]**2 for i in free), Decimal(0)).sqrt()
        nfixed = sum((result["internal_decimal"][i]**2 for i in fixed), Decimal(0)).sqrt()
        floor = Decimal("1e-8")*D(2.3)*D(0.125)
        assert result["force_scale_decimal"] == max(nfree, nfixed, floor)
        assert result["relative_residual_decimal"] == nfree/max(nfree, nfixed, floor)
        assert result["relative_force_balance_decimal"] == result["force_balance_norm_decimal"]/result["force_scale_decimal"]
    assert result["relative_force_balance_decimal"] > 0


def test_negative_and_tiny_targets_use_absolute_floored_displacement_scale():
    negative, tiny = call(d=-0.125), call(d=-1e-12)
    assert negative["d_scale_decimal"] == D(0.125)
    assert negative["relative_constraint_decimal"] == 1
    assert tiny["d_scale_decimal"] == Decimal("1e-6")


def test_nonaffine_huhu_and_directional_derivative_have_independent_fd_check():
    data = fixture()
    u = np.array([0, 0.125, 0, 0.125, 0, 0.03125, 0, 0], dtype=float)
    v = np.array([0, 0, 0.2, 0.1, 0.1, -0.3, 0.4, 0.2], dtype=float)
    result = call(u, d=0.125, data=data, tangent_direction=v)
    assert any(value != 0 for value in result["regularization_internal_decimal"])
    assert any(value != 0 for value in result["regularization_tangent_action_decimal"])
    primitives = dict(data, F0=np.zeros(8))
    reference = _module._reference_class()(primitives, precision=80)
    plus = reference.evaluate(u, 0.0, direction=v, offset=1e-10, derivative=False)
    minus = reference.evaluate(u, 0.0, direction=v, offset=-1e-10, derivative=False)
    motion, groups = motion_and_groups()
    with localcontext() as context:
        context.prec = 80
        fd = [(a-b)/(2*D(1e-10)) for a, b in zip(plus["internal_decimal"], minus["internal_decimal"])]
        error = sum(((a-b)**2 for a, b in zip(result["tangent_action_decimal"], fd)), Decimal(0)).sqrt()
        scale = max(sum((a*a for a in fd), Decimal(0)).sqrt(), Decimal(1))
        assert error/scale < Decimal("1e-17")
    with localcontext() as context:
        context.prec = 50
        assert result["tangent_action_decimal"] == [a+b for a, b in zip(
            result["material_tangent_action_decimal"], result["regularization_tangent_action_decimal"])]
        for name, vector in groups.items():
            assert result["group_reaction_tangent_actions_decimal"][name] == sum(
                (D(x)*a for x, a in zip(vector, result["support_reaction_tangent_action_decimal"])), Decimal(0))
        assert result["drive_force_tangent_action_decimal"] == sum(
            (D(x)*a for x, a in zip(motion, result["support_reaction_tangent_action_decimal"])), Decimal(0))
    assert result["constraint_tangent_action_decimal"] == [D(x) for x in v]


def test_rigid_translation_direction_has_zero_internal_action():
    v = np.tile([0.5, -0.25], 4)
    result = call(tangent_direction=v)
    assert all(value == 0 for value in result["tangent_action_decimal"])
    assert all(value == 0 for value in result["regularization_tangent_action_decimal"])
    assert result["drive_force_tangent_action_decimal"] == 0
    assert result["constraint_tangent_action_decimal"] == [D(x) for x in v]


def test_optional_solid_partition_does_not_change_internal_force():
    motion, _ = motion_and_groups()
    medium = call(0.125*motion, d=0.125, data=fixture(solid=False))
    unlabelled = fixture()
    del unlabelled["solid"]
    all_values = call(0.125*motion, d=0.125, data=unlabelled)
    assert medium["solid_material_energy_decimal"] == 0
    assert medium["medium_material_energy_decimal"] == medium["material_energy_decimal"][0]
    assert medium["minimum_J_solid_decimal"] is None
    assert medium["minimum_J_medium_decimal"] == Decimal("0.875")
    assert all_values["solid_material_energy_decimal"] is None
    assert all_values["solid"] is None
    assert medium["internal_decimal"] == all_values["internal_decimal"]


def test_unrelated_source_load_is_ignored_and_inputs_are_not_mutated():
    data = fixture()
    data["F0"] = np.full(8, np.nan)
    motion, groups = motion_and_groups()
    base, u = np.zeros(8), 0.125*motion
    data_before = {key: value.copy() for key, value in data.items()}
    u_before, base_before, motion_before = u.copy(), base.copy(), motion.copy()
    groups_before = {key: value.copy() for key, value in groups.items()}
    result = call(u, d=0.125, data=data, base=base, direction=motion, reaction_groups=groups)
    assert all(value == 0 for value in result["external_decimal"])
    for key, value in data.items():
        np.testing.assert_array_equal(value, data_before[key])
    for actual, expected in ((u, u_before), (base, base_before), (motion, motion_before)):
        np.testing.assert_array_equal(actual, expected)
    for key, value in groups.items():
        np.testing.assert_array_equal(value, groups_before[key])


def test_50_and_80_digits_agree_on_actual_binary64_primitives():
    data = fixture()
    data["lam"], data["mu"] = np.array([0.5769230769230769e-7]), np.array([0.3846153846153846e-7])
    u = np.array([0, 0.2, 0, 0.2, 0, 0.003, 0, 0], dtype=float)
    lower = call(u, d=0.2, data=data, precision=50)
    higher = call(u, d=0.2, data=data, precision=80)
    with localcontext() as context:
        context.prec = 100
        error = sum(((a-b)**2 for a, b in zip(lower["internal_decimal"], higher["internal_decimal"])), Decimal(0)).sqrt()
        assert error/higher["force_scale_decimal"] < Decimal("1e-30")


@pytest.mark.parametrize("changes", [
    {"d": float("nan")}, {"d": float("inf")}, {"force_scale_per_length": 0},
    {"force_scale_per_length": -1}, {"force_scale_per_length": float("nan")},
    {"precision": 20}, {"precision": True}, {"precision": 50.0},
    {"u": np.zeros(7)}, {"u": np.zeros(8, dtype=complex)},
    {"base": np.zeros(7)}, {"direction": np.full(8, np.nan)},
    {"tangent_direction": np.zeros(7)}, {"reaction_groups": {}},
    {"reaction_groups": {"bad": np.ones(7)}}, {"reaction_groups": {"bad": np.zeros(8)}},
    {"reaction_groups": {"": np.ones(8)}}, {"reaction_groups": {1: np.ones(8)}},
])
def test_invalid_inputs_are_rejected(changes):
    with pytest.raises(ValueError):
        call(**changes)


@pytest.mark.parametrize("field", ["base", "direction", "reaction_groups"])
def test_prescription_and_reaction_groups_cannot_contain_free_dofs(field):
    data = fixture(fixed=[0, 1, 2, 3, 4, 6])
    motion, groups = motion_and_groups()
    changes = dict(data=data, reaction_groups={"bottom": groups["bottom"]})
    illegal = motion.copy()
    illegal[5] = 1
    changes[field] = {"bad": illegal} if field == "reaction_groups" else illegal
    with pytest.raises(ValueError, match="zero on free DOFs"):
        call(**changes)


def test_duplicate_fixed_dofs_and_invalid_solid_mask_are_rejected():
    duplicate = fixture(fixed=[0, 0])
    with pytest.raises(ValueError, match="repeated"):
        call(data=duplicate)
    bad_solid = fixture()
    bad_solid["solid"] = np.array([2])
    with pytest.raises(ValueError, match="solid"):
        call(data=bad_solid)


def test_nonpositive_j_is_rejected_before_any_metric_can_be_accepted():
    motion, _ = motion_and_groups()
    with pytest.raises(ValueError, match="Nonpositive"):
        call(2*motion, d=2)
