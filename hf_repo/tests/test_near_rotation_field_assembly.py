"""Small algebraic contracts for assembling independently supplied Decimal fields.

Expected forces below are hand-computed from constant stress and tabulated
operators. No production kernel, geometry generator, solver, or saved experiment
is used as an oracle. These are operator tests, not physical-path admission.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/near_rotation_field_assembly.py"
SPEC = importlib.util.spec_from_file_location("near_rotation_field_assembly_under_test", SCRIPT)
assembly = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assembly)
D = Decimal
FORCES = ("total_force", "material_force", "regularization_force")


def fixture(two_elements=False):
    """Synthetic Q1 center operators with nine unit-weight contributions.

    Repeated center operators deliberately make the integral factor exactly 9;
    this is an assembly fixture, not a claim of nine-point quadrature accuracy.
    """
    connectivity = [[0, 1, 2, 3], [1, 4, 5, 2]] if two_elements else [[0, 1, 2, 3]]
    grad = [[-0.25, -0.25], [0.25, -0.25], [0.25, 0.25], [-0.25, 0.25]]
    return dict(
        connectivity=connectivity,
        F0=[0.0] * (12 if two_elements else 8),
        fixed_dofs=[0, 1],
        grad=[deepcopy(grad) for _ in range(9)],
        hessian=[[[0.0, s], [s, 0.0]] for s in (0.25, -0.25, 0.25, -0.25)],
        weights=[1.0] * 9,
        lam=[0.0] * len(connectivity),
        mu=[2.0] * len(connectivity),
        kr=2.0,
    )


def fields(ne=1, matrix=None, jacobian="1"):
    matrix = [[D(1), D(0)], [D(0), D(1)]] if matrix is None else matrix
    F = [[deepcopy(matrix) for _ in range(9)] for _ in range(ne)]
    J = [[D(jacobian) for _ in range(9)] for _ in range(ne)]
    Hu = [[[[D(0) for _ in range(2)] for _ in range(2)] for _ in range(2)] for _ in range(ne)]
    return F, J, Hu


def close_vector(actual, expected, tolerance=D("1e-65")):
    assert len(actual) == len(expected)
    with localcontext() as context:
        context.prec = 120
        assert all(isinstance(a, Decimal) and abs(a - b) <= tolerance for a, b in zip(actual, expected))


def test_identity_fields_have_zero_full_force_and_preserve_inputs():
    data, state = fixture(), fields()
    originals = deepcopy((data, state))
    result = assembly.assemble_fields(data, *state, precision=80)
    assert set(result) == set(FORCES)
    for name in FORCES:
        assert result[name] == [D(0)] * 8
        assert all(isinstance(value, Decimal) for value in result[name])
    assert (data, state) == originals


def test_supplied_j_is_not_silently_recomputed_from_f():
    # F = I but supplied J = 2: with lambda=0, mu=2, cofactor(F)/J=I/2,
    # so P=I and f_a=9*grad(N_a). Recomputing det(F)=1 would return zero.
    data = fixture()
    F, J, Hu = fields(jacobian="2")
    result = assembly.assemble_fields(data, F, J, Hu, precision=80)
    expected = [D(n) / 4 for n in (-9, -9, 9, -9, 9, 9, -9, 9)]
    assert result["material_force"] == expected
    assert result["regularization_force"] == [D(0)] * 8
    assert result["total_force"] == expected
    # With lambda=4 the same supplied J gives P=(1+2*ln(2))*I.
    data["lam"] = [4.0]
    volumetric = assembly.assemble_fields(data, F, J, Hu, precision=80)
    with localcontext() as context:
        context.prec = 120
        factor = D(1) + 2 * D(2).ln()
        close_vector(volumetric["material_force"], [factor * value for value in expected])


def test_nonsymmetric_f_uses_cofactor_transpose_indices_correctly():
    # Simple shear F=[[1,2],[0,1]], J=1, mu=2 gives
    # F^{-T}=[[1,0],[-2,1]] and P=[[0,4],[4,0]].
    state = fields(matrix=[[D(1), D(2)], [D(0), D(1)]])
    result = assembly.assemble_fields(fixture(), *state, precision=80)
    expected = [D(n) for n in (-9, -9, -9, 9, 9, 9, 9, -9)]
    assert result["material_force"] == expected
    assert result["total_force"] == expected


def test_shared_node_scatter_matches_hand_computed_stress_and_balances():
    # F=diag(2,1/2), J=1 gives P=diag(3,-3). Each local force is
    # (+/-27/4, +/-27/4); interface x forces cancel while y forces add.
    data = fixture(two_elements=True)
    F, J, Hu = fields(2, [[D(2), D(0)], [D(0), D("0.5")]])
    result = assembly.assemble_fields(data, F, J, Hu, precision=80)
    expected = [D(n) / 4 for n in (-27, 27, 0, 54, 0, -54, -27, -27, 27, 27, 27, -27)]
    assert result["material_force"] == expected
    assert result["total_force"] == expected
    assert result["regularization_force"] == [D(0)] * 12
    assert sum(result["total_force"][::2], D(0)) == 0
    assert sum(result["total_force"][1::2], D(0)) == 0
    # Fixed DOFs retain their full nodal force; the helper must not mask them.
    assert result["total_force"][:2] == [D("-6.75"), D("6.75")]


def test_hu_changes_only_regularization_with_both_mixed_terms_and_linear_scaling():
    data = fixture()
    F, J, Hu = fields(matrix=[[D(2), D(0)], [D(0), D("0.5")]])
    baseline = assembly.assemble_fields(data, F, J, Hu, precision=80)
    # The unequal mixed entries test that neither term is dropped or copied.
    Hu[0] = [[[D(0), D(3)], [D(5), D(0)]],
             [[D(0), D(-2)], [D(4), D(0)]]]
    first = assembly.assemble_fields(data, F, J, Hu, precision=80)
    twice_Hu = [[[[D(2) * value for value in row] for row in plane] for plane in element] for element in Hu]
    second = assembly.assemble_fields(data, F, J, twice_Hu, precision=80)
    assert first["material_force"] == second["material_force"] == baseline["material_force"]
    with localcontext() as context:
        context.prec = 120
        decay = D(-5).exp()
        # Au=(+/-2,+/-1/2); kr*sum(weights)=18.
        expected = [D(n) * decay for n in (36, 9, -36, -9, 36, 9, -36, -9)]
        close_vector(first["regularization_force"], expected)
        close_vector(second["regularization_force"], [2 * value for value in first["regularization_force"]])
        close_vector(first["total_force"], [a + b for a, b in zip(first["material_force"], expected)])
    assert any(value != 0 for value in first["regularization_force"])


def test_decimal_field_detail_below_binary64_resolution_is_preserved():
    # With supplied J=1, F00=1+1e-40 gives P=diag(2e-40,-2e-40).
    # Conversion through float would erase this complete stress signal.
    stretched = D("1." + "0" * 39 + "1")
    state = fields(matrix=[[stretched, D(0)], [D(0), D(1)]])
    result = assembly.assemble_fields(fixture(), *state, precision=80)
    coefficient = D("4.5e-40")
    expected = [sign * coefficient for sign in (-1, 1, 1, 1, 1, -1, -1, -1)]
    assert result["material_force"] == expected
    assert result["total_force"] == expected


def test_incomplete_field_shapes_are_rejected_instead_of_truncated():
    for which in (0, 1, 2):
        state = list(fields())
        state[which][0].pop()
        with pytest.raises(ValueError):
            assembly.assemble_fields(fixture(), *state, precision=80)


def test_nonfinite_fields_and_nonpositive_supplied_j_are_rejected():
    for which, value in ((0, D("NaN")), (1, D("Infinity")), (2, D("-Infinity")),
                         (1, D(0)), (1, D(-1))):
        F, J, Hu = fields()
        if which == 0:
            F[0][0][0][0] = value
        elif which == 1:
            J[0][0] = value
        else:
            Hu[0][0][0][0] = value
        with pytest.raises(ValueError):
            assembly.assemble_fields(fixture(), F, J, Hu, precision=80)


def test_float_field_leaves_are_rejected_instead_of_promoted_after_information_loss():
    for which in (0, 1, 2):
        F, J, Hu = fields()
        if which == 0:
            F[0][0][0][0] = 1.0
        elif which == 1:
            J[0][0] = 1.0
        else:
            Hu[0][0][0][0] = 0.0
        with pytest.raises(ValueError):
            assembly.assemble_fields(fixture(), F, J, Hu, precision=80)


def test_precision_contract_and_invalid_primitive_fixture_are_rejected():
    for precision in (50, True, 80.0):
        with pytest.raises(ValueError):
            assembly.assemble_fields(fixture(), *fields(), precision=precision)
    for issue in ("missing_weights", "nonfinite_gradient", "out_of_range_node"):
        data = fixture()
        if issue == "missing_weights":
            del data["weights"]
        elif issue == "nonfinite_gradient":
            data["grad"][0][0][0] = float("nan")
        else:
            data["connectivity"][0][0] = 99
        with pytest.raises(ValueError):
            assembly.assemble_fields(data, *fields(), precision=80)
