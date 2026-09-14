"""Independent ordinary-data tests for the HF-3 Decimal port adapter.

No production solver/kernel is imported. Tests exercise exact input promotion,
work-conjugate signs, normalization, rank-one spring and augmented derivatives.
"""
from decimal import Decimal, localcontext
import importlib.util
from pathlib import Path

import numpy as np
import pytest


_path = Path(__file__).resolve().parents[1]/"scripts"/"hf3_precision_reference.py"
_spec = importlib.util.spec_from_file_location("hf3_precision_under_test", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
evaluate = _module.evaluate_project_state


def D(value):
    return Decimal.from_float(float(value))


def fixture(*, solid=True):
    """Analytically tabulated square Q1, local BL/BR/TR/TL, unit thickness."""
    signs = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]])
    grad = []
    weights = []
    for xi, wx in zip((-1, 0, 1), (1, 4, 1)):
        for eta, wy in zip((-1, 0, 1), (1, 4, 1)):
            grad.append([[sx*(1+sy*eta)/2, sy*(1+sx*xi)/2] for sx, sy in signs])
            weights.append(wx*wy/36)
    hessian = np.zeros((4, 2, 2))
    hessian[:, 0, 1] = hessian[:, 1, 0] = signs[:, 0]*signs[:, 1]
    return dict(grad=np.array(grad), hessian=hessian, weights=np.array(weights),
                lam=np.array([1.25]), mu=np.array([0.75]), kr=np.array(0.02),
                connectivity=np.array([[0, 1, 2, 3]]), fixed_dofs=np.array([0, 1, 6, 7]),
                solid=np.array([solid]))


def ports():
    bin = np.zeros(8)
    bout = np.zeros(8)
    bin[[2, 4]] = 0.5
    bout[[3, 5]] = 0.5
    return bin, bout


def call(u=None, *, R=0.0, d=0.0, kout=0.0, precision=50, data=None, bin=None, bout=None, **kwargs):
    original_bin, original_bout = ports()
    return evaluate(fixture() if data is None else data, np.zeros(8) if u is None else u,
                    R, d, original_bin if bin is None else bin, original_bout if bout is None else bout,
                    kout, 2.3, 4.7, precision=precision, **kwargs)


def test_zero_state_uses_specification_floor_without_division_by_zero():
    result = call()
    with localcontext() as context:
        context.prec = 50
        expected = Decimal("1e-8")*D(2.3)*D(4.7)*Decimal("1e-6")
    assert result["force_scale_decimal"] == expected
    assert result["free_residual_norm_decimal"] == 0
    assert result["relative_residual_decimal"] == 0
    assert result["constraint_decimal"] == 0
    assert result["minimum_J_decimal"] == 1
    assert result["minimum_J_medium_decimal"] is None
    assert result["solid_material_energy_decimal"] == 0
    assert result["medium_material_energy_decimal"] == 0
    assert result["relative_force_balance_decimal"] == 0


def test_port_mean_is_recomputed_before_float_rounding():
    u = np.array([0, 0, 0.001, 0.002, 0.003, 0.007, 0, 0], dtype=float)
    bin, bout = ports()
    bout[3], bout[5] = 0.1, 0.9
    result = call(u, d=0.003, R=0.2, kout=0.3, bout=bout)
    with localcontext() as context:
        context.prec = 50
        qin = sum((D(a)*D(b) for a, b in zip(bin, u)), Decimal(0))
        qout = sum((D(a)*D(b) for a, b in zip(bout, u)), Decimal(0))
        assert result["q_in_decimal"] == qin
        assert result["q_out_decimal"] == qout
        assert result["constraint_decimal"] == qin-D(0.003)
        assert result["spring_internal_decimal"][3] == D(0.3)*D(bout[3])*qout
    assert result["q_out_decimal"] != D(np.dot(bout, u))


def test_rank_one_spring_preserves_port_relative_motion():
    # Opposite displacements have zero mean: a distributed rank-one spring
    # must exert no force, unlike two independently grounded nodal springs.
    u = np.array([0, 0, 0, 0.01, 0, -0.01, 0, 0], dtype=float)
    result = call(u, kout=7.0)
    assert result["q_out_decimal"] == 0
    assert all(x == 0 for x in result["spring_internal_decimal"])
    assert np.linalg.norm(7.0*u[[3, 5]]) > 0


def test_input_multiplier_sign_reaction_and_balance():
    result = call(R=0.3)
    bin, _ = ports()
    with localcontext() as context:
        context.prec = 50
        expected = [D(x)*D(0.3) for x in bin]
        assert result["input_force_decimal"] == expected
        assert result["residual_decimal"] == [-x for x in expected]
        assert result["external_decimal"] == expected
        assert result["force_balance_decimal"] == [sum(expected, Decimal(0)), Decimal(0)]
    assert result["relative_residual_decimal"] == 1
    assert all(x == 0 for x in result["support_reaction_decimal"])


def test_support_reaction_is_restricted_to_unique_fixed_dofs():
    u = np.array([0, 0, 0.02, 0.002, 0.015, 0.008, 0, 0], dtype=float)
    result = call(u, R=0.17, kout=0.7)
    fixed = fixture()["fixed_dofs"]
    for i, reaction in enumerate(result["support_reaction_decimal"]):
        assert reaction == (result["residual_decimal"][i] if i in fixed else Decimal(0))
    with localcontext() as context:
        context.prec = 50
        external_sum = sum(result["external_action_norms_decimal"].values(), Decimal(0))
        assert result["force_balance_scale_decimal"] == max(external_sum, result["force_scale_decimal"])
        for component in (0, 1):
            expected = sum((result["support_reaction_decimal"][i]+result["external_decimal"][i]
                            for i in range(component, 8, 2)), Decimal(0))
            assert result["force_balance_decimal"][component] == expected


def test_mean_constraint_scale_handles_negative_and_tiny_targets():
    negative = call(d=-0.03)
    tiny = call(d=-1e-12)
    with localcontext() as context:
        context.prec = 50
        assert negative["d_scale_decimal"] == abs(D(-0.03))
        assert negative["constraint_decimal"] == -D(-0.03)
    assert tiny["d_scale_decimal"] == Decimal("1e-6")
    assert negative["relative_constraint_decimal"] == 1


def test_augmented_derivative_has_multiplier_and_rank_one_spring_terms():
    u = np.array([0, 0, 0.03, 0.02, 0.01, 0.05, 0, 0], dtype=float)
    v = np.array([0, 0, 0.4, -0.3, -0.1, 0.2, 0, 0], dtype=float)
    bin, bout = ports()
    result = call(u, R=0.2, kout=1.3, direction=v, dR=-0.7)
    with localcontext() as context:
        context.prec = 50
        dqout = sum((D(a)*D(b) for a, b in zip(bout, v)), Decimal(0))
        dqin = sum((D(a)*D(b) for a, b in zip(bin, v)), Decimal(0))
        expected_spring = [D(1.3)*D(b)*dqout for b in bout]
        expected_multiplier = [-D(b)*D(-0.7) for b in bin]
        expected = [a+b+c for a, b, c in zip(result["internal_tangent_action_decimal"], expected_spring, expected_multiplier)]
        assert result["spring_tangent_action_decimal"] == expected_spring
        assert result["multiplier_tangent_action_decimal"] == expected_multiplier
        assert result["residual_tangent_action_decimal"] == expected
        assert result["constraint_tangent_action_decimal"] == dqin
        assert result["augmented_tangent_action_decimal"] == expected+[dqin]


def test_pure_multiplier_direction_has_exact_kkt_sign():
    result = call(direction=np.zeros(8), dR=0.25)
    bin, _ = ports()
    assert result["residual_tangent_action_decimal"] == [-D(x)*D(0.25) for x in bin]
    assert result["constraint_tangent_action_decimal"] == 0
    assert all(x == 0 for x in result["internal_tangent_action_decimal"])


def test_rigid_translation_direction_has_no_internal_or_relative_spring_force():
    v = np.tile([0.5, 0.0], 4)
    result = call(direction=v)
    assert all(x == 0 for x in result["internal_tangent_action_decimal"])
    assert result["constraint_tangent_action_decimal"] == D(0.5)


def test_material_energy_partition_uses_canonical_solid_mask():
    u = np.array([0, 0, 0.03, 0, 0.03, 0, 0, 0], dtype=float)
    result = call(u, data=fixture(solid=False))
    assert result["solid_material_energy_decimal"] == 0
    assert result["medium_material_energy_decimal"] == result["material_energy_decimal"][0]
    assert result["minimum_J_solid_decimal"] is None
    assert result["minimum_J_medium_decimal"] > 0


def test_source_force_fixture_is_ignored_and_inputs_are_not_mutated():
    data = fixture()
    data["F0"] = np.full(8, np.nan)  # unrelated source load is not a project input
    before = {key: value.copy() for key, value in data.items()}
    result = call(data=data, R=0.1)
    assert result["relative_residual_decimal"] == 1
    for key, value in data.items():
        np.testing.assert_array_equal(value, before[key])


def test_50_and_80_digits_converge_for_near_zero_project_state():
    u = np.array([0, 0, 1e-10, 2e-11, 8e-11, -1e-11, 0, 0], dtype=float)
    lower = call(u, R=1e-9, d=1e-10, kout=0.01, precision=50)
    higher = call(u, R=1e-9, d=1e-10, kout=0.01, precision=80)
    with localcontext() as context:
        context.prec = 100
        diff = [a-b for a, b in zip(lower["residual_decimal"], higher["residual_decimal"])]
        error = sum((x*x for x in diff), Decimal(0)).sqrt()/higher["force_scale_decimal"]
    assert error < Decimal("1e-30")


@pytest.mark.parametrize("changes", [
    {"R": float("nan")}, {"d": float("inf")}, {"kout": -1.0},
    {"precision": 20}, {"precision": True}, {"dR": 1.0},
    {"direction": np.ones(7)}, {"bin": np.zeros(8)},
])
def test_invalid_inputs_are_rejected(changes):
    with pytest.raises(ValueError):
        call(**changes)


@pytest.mark.parametrize("field,value", [("E", 0), ("thickness", -1)])
def test_nonphysical_scale_parameters_are_rejected(field, value):
    kwargs = dict(fixture=fixture(), u=np.zeros(8), R=0.0, d=0.0,
                  bin=ports()[0], bout=ports()[1], kout=0.0, E=2.3, thickness=4.7)
    kwargs[field] = value
    with pytest.raises(ValueError):
        evaluate(**kwargs)


def test_invalid_solid_mask_and_duplicate_fixed_dofs_are_rejected():
    bad_solid = fixture()
    bad_solid["solid"] = np.array([2])
    with pytest.raises(ValueError, match="solid"):
        call(data=bad_solid)
    duplicate = fixture()
    duplicate["fixed_dofs"] = np.array([0, 0])
    with pytest.raises(ValueError, match="repeated"):
        call(data=duplicate)


def test_nonpositive_j_is_rejected_before_reporting_a_finite_metric():
    u = np.array([0, 0, -2, 0, -2, 0, 0, 0], dtype=float)
    with pytest.raises(ValueError, match="Nonpositive"):
        call(u)
