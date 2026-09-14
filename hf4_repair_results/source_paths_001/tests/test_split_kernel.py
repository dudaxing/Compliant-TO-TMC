"""Frozen manufactured split-state checks, independent of HF-4 path solving.

Thresholds/fields come from docs/HF4_SPLIT_IMPLEMENTATION_SPEC.md. XML test
properties retain numerical comparisons and every predefined FD sample.
Actual HF-4 fixed-field/path gates are separate monitored validation jobs.
"""
from decimal import Decimal, localcontext
from functools import lru_cache
import importlib.util
import json
from pathlib import Path

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from hf_eval import split_kernel as kernel
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import TMCError, TMCModel
from hf_eval.tmc_kernel import KernelError, operators, batch_response


LAM, MU, KR = 2., 3., 1./8
SIZES = [(1., 1.), (1./8, 1./16)]
V = np.array([1., -2., 3., -1., -2., 4., -3., -1.])/8
CASES = ["legacy", "translation", "small", "compression", "overclosed_lift",
         "huhu", "near_inside", "near_outside"]


@pytest.fixture(autouse=True)
def explicit_runtime():
    assert jax.default_backend() == "cpu"
    with jax.enable_x64(True):
        yield


@lru_cache(maxsize=1)
def reference_class():
    path = Path(__file__).resolve().parents[1]/"scripts"/"hf4_split_precision_reference.py"
    spec = importlib.util.spec_from_file_location("split_hp_for_kernel_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DecimalSplitQ1Reference


def D(value):
    return Decimal.from_float(float(value))


def flat(values):
    return list(np.asarray(values, dtype=object).ravel())


def norm(values):
    return sum((x*x for x in flat(values)), Decimal(0)).sqrt()


def error(actual, expected):
    actual, expected = np.asarray(actual), np.asarray(expected, dtype=object)
    assert actual.shape == expected.shape
    return norm([D(a)-b for a, b in zip(actual.ravel(), expected.ravel())])


def check(checks, name, value, bound):
    checks.append(dict(name=name, value=str(value), bound=str(bound), passed=bool(value <= bound)))


def finish(checks, record_property):
    record_property("frozen_comparisons", json.dumps(checks, separators=(",", ":")))
    assert all(c["passed"] for c in checks), checks


def xy(hx, hy):
    return np.array([[0., 0.], [hx, 0.], [hx, hy], [0., hy]])


def fields(case, coordinates):
    x, y = coordinates.T
    zero = np.zeros_like(x)
    L = np.column_stack((np.full_like(x, 1./8), np.full_like(x, -1./4)))
    w = np.zeros_like(L)
    if case == "legacy":
        L = np.column_stack((x/64+y/128, -x/256+y/32))
    elif case == "translation":
        w[:] = [2.**-45, -2.**-44]
    elif case == "small":
        w = np.column_stack((2.**-45*x+2.**-46*x*y, -2.**-44*y+2.**-47*x*y))
    elif case == "compression":
        L = np.column_stack((zero, -y))
        w = np.column_stack((zero, float(2.**-17+2.**-60)*y))
    elif case == "overclosed_lift":
        L = np.column_stack((zero, -1.5*y))
        w = np.column_stack((zero, (.5+2.**-17)*y))
    elif case == "huhu":
        L = np.column_stack((x*y/8, -x*y/16))
        w = np.column_stack((-x*y/8+x/32+x*y/128, x*y/16-y/64-x*y/256))
    elif case in ("near_inside", "near_outside"):
        a = .01*(1+(-1 if case == "near_inside" else 1)*2.**-10)
        w = np.column_stack((a*x, zero))
    else:
        raise ValueError(case)
    return L.ravel(), w.ravel()


def fixture(ops, *, connectivity=None, lam=LAM, mu=MU, kr=KR, ndof=8):
    connectivity = np.array([[0, 1, 2, 3]]) if connectivity is None else connectivity
    return dict(**ops, connectivity=connectivity, lam=np.broadcast_to(lam, (len(connectivity),)),
                mu=np.broadcast_to(mu, (len(connectivity),)), kr=np.array(kr),
                F0=np.zeros(ndof), fixed_dofs=np.empty(0, dtype=int))


def component_actions(lift, w, ops, lam, mu, kr, direction):
    """Differentiate the production residual-only branch, including both parts."""
    args = (jnp.asarray(lift), jnp.asarray(ops["grad"]), jnp.asarray(ops["hessian"]),
            jnp.asarray(ops["weights"]), jnp.asarray(lam), jnp.asarray(mu), jnp.asarray(kr))
    function = lambda varied: kernel._batch_without_tangent(
        args[0], varied, args[1], args[2], args[3], args[4], args[5], args[6])
    _, actions = jax.jvp(function, (jnp.asarray(w),), (jnp.asarray(direction),))
    return {key: np.asarray(value) for key, value in actions.items()}


@pytest.mark.parametrize("hx,hy", SIZES)
@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("tangent", [True, False])
def test_frozen_split_element_against_independent_decimal(hx, hy, case, tangent, record_property):
    ops = operators(hx, hy)
    lift, w = fields(case, xy(hx, hy))
    data = fixture(ops)
    hp50 = reference_class()(data, precision=50).evaluate(lift, w, tangent_direction=V)
    hp80 = reference_class()(data, precision=80).evaluate(lift, w, tangent_direction=V)
    actual = kernel.batch_response_split(lift[None], w[None], ops, LAM, MU, KR, tangent=tangent)
    guard_J = kernel.determinants_split(lift, w, ops)
    checks = []
    with localcontext() as context:
        context.prec = 100
        force_floor = D(MU)*D(min(hx, hy))*D(2.**-45)
        for actual_key, hp_key in (("residual", "internal"), ("material_residual", "material_internal"),
                                   ("regularization_residual", "regularization_internal")):
            expected = hp80[hp_key+"_decimal"]
            scale = max(norm(expected), force_floor)
            check(checks, actual_key, error(actual[actual_key][0], expected), Decimal("1e-9")*scale)
        for key in ("G", "F", "Hu"):
            expected = hp80[key+"_decimal"]
            assert actual[key].shape == np.asarray(expected, dtype=object).shape
            diff = max(abs(D(a)-b) for a, b in zip(actual[key].ravel(), flat(expected)))
            scale = max(Decimal(1), max(map(abs, flat(expected))))
            check(checks, key, diff, Decimal("5e-15")*scale)
        for name, values in (("JAX_J", actual["J"][0]), ("NumPy_J", guard_J)):
            assert np.all(values > 0)
            expected = hp80["J_decimal"][0]
            check(checks, name, max(abs(D(a)-b)/b for a, b in zip(values, expected)), Decimal("1e-9"))
        energy = hp80["material_energy_decimal"][0]
        check(checks, "material_energy", abs(D(actual["material_energy"][0])-energy),
              Decimal("1e-8")*max(abs(energy), D(MU)*D(hx)*D(hy)*D(2.**-100)))
        scale = max(norm(hp80["internal_decimal"]), force_floor)
        check(checks, "reference_50_80", norm([a-b for a, b in zip(hp50["internal_decimal"], hp80["internal_decimal"])]),
              Decimal("1e-30")*scale)
        if tangent:
            actions = component_actions(lift[None], w[None], ops, np.array([LAM]), np.array([MU]), KR, V[None])
            action_floor = D(MU)*norm([D(x) for x in V])*Decimal("1e-12")
            for actual_key, hp_key in (("residual", "tangent_action"), ("material_residual", "material_tangent_action"),
                                       ("regularization_residual", "regularization_tangent_action")):
                expected = hp80[hp_key+"_decimal"]
                scale_v = max(norm(expected), action_floor)
                check(checks, actual_key+"_Jv", error(actions[actual_key][0], expected), Decimal("1e-8")*scale_v)
            expected = hp80["tangent_action_decimal"]
            check(checks, "returned_tangent_Jv", error(actual["tangent"][0]@V, expected),
                  Decimal("1e-8")*max(norm(expected), action_floor))
    if case == "translation":
        for name in ("residual", "material_residual", "regularization_residual", "Hu", "material_energy"):
            np.testing.assert_array_equal(actual[name], np.zeros_like(actual[name]))
        np.testing.assert_array_equal(actual["J"], np.ones((1, 9)))
    if case == "compression":
        expected_J = float(2.**-17+2.**-60)
        np.testing.assert_array_equal(actual["J"], np.full((1, 9), expected_J))
        # This detects accidentally using I+(GL+Gw) in the non-near branch.
        assert expected_J != float(1. + (-1. + expected_J))
    assert ("tangent" in actual) == tangent
    finish(checks, record_property)


@pytest.mark.parametrize("hx,hy", SIZES)
def test_exactly_equivalent_nonzero_hessian_decompositions(hx, hy, record_property):
    coordinates = xy(hx, hy)
    lift, w = fields("huhu", coordinates)
    x, y = coordinates.T
    q = np.column_stack((x*y/32, x*y/64)).ravel()
    alternative = SplitDisplacement(lift+q, w-q)
    with localcontext() as context:
        context.prec = 100
        assert [D(a)+D(b) for a, b in zip(lift, w)] == [D(a)+D(b) for a, b in zip(alternative.lift, alternative.fluctuation)]
    ops = operators(hx, hy)
    assert np.any(np.einsum("ai,ajk->ijk", lift.reshape(4, 2), ops["hessian"]))
    assert np.any(np.einsum("ai,ajk->ijk", w.reshape(4, 2), ops["hessian"]))
    hp = reference_class()(fixture(ops), precision=80).evaluate(lift, w, tangent_direction=V)
    result = kernel.batch_response_split(alternative.lift[None], alternative.fluctuation[None], ops, LAM, MU, KR)
    checks = []
    with localcontext() as context:
        context.prec = 100
        for key, target in (("residual", "internal_decimal"), ("material_residual", "material_internal_decimal"),
                            ("regularization_residual", "regularization_internal_decimal")):
            check(checks, key, error(result[key][0], hp[target]),
                  Decimal("1e-9")*max(norm(hp[target]), D(MU)*D(min(hx, hy))*D(2.**-45)))
        check(checks, "same_state_Jv", error(result["tangent"][0]@V, hp["tangent_action_decimal"]),
              Decimal("1e-8")*max(norm(hp["tangent_action_decimal"]), D(MU)*norm([D(x) for x in V])*Decimal("1e-12")))
    finish(checks, record_property)


@pytest.mark.parametrize("hx,hy", SIZES)
@pytest.mark.parametrize("case", ["huhu", "compression"])
def test_all_frozen_directional_difference_samples(hx, hy, case, record_property):
    ops = operators(hx, hy)
    lift, w = fields(case, xy(hx, hy))
    reference = reference_class()(fixture(ops), precision=50)
    hp = reference.evaluate(lift, w, tangent_direction=V)
    steps = [1e-5, 1e-6, 1e-7, 1e-8, 1e-9] if case == "huhu" else [2.**-26*x for x in (1., .1, .01, .001, .0001)]
    rows = []
    with localcontext() as context:
        context.prec = 100
        scale = max(norm(hp["tangent_action_decimal"]), D(MU)*norm([D(x) for x in V])*Decimal("1e-12"))
        for h in steps:
            plus, minus = w+h*V, w-h*V
            jp, jm = kernel.determinants_split(lift, plus, ops), kernel.determinants_split(lift, minus, ops)
            assert min(jp.min(), jm.min()) > 0
            rp = kernel.batch_response_split(lift[None], plus[None], ops, LAM, MU, KR, tangent=False)["residual"][0]
            rm = kernel.batch_response_split(lift[None], minus[None], ops, LAM, MU, KR, tangent=False)["residual"][0]
            hp_plus = reference.evaluate(lift, w, tangent_direction=V, fluctuation_offset=h, derivative=False)
            hp_minus = reference.evaluate(lift, w, tangent_direction=V, fluctuation_offset=-h, derivative=False)
            assert min(min(flat(hp_plus["J_decimal"])), min(flat(hp_minus["J_decimal"]))) > 0
            fd = (rp-rm)/(2*h)
            ideal = [(a-b)/(2*D(h)) for a, b in zip(hp_plus["internal_decimal"], hp_minus["internal_decimal"])]
            rows.append(dict(h=h, double_error=str(error(fd, hp["tangent_action_decimal"])/scale),
                             decimal_error=str(norm([a-b for a, b in zip(ideal, hp["tangent_action_decimal"])])/scale),
                             minimum_double_J=float(min(jp.min(), jm.min())),
                             minimum_decimal_J=str(min(min(flat(hp_plus["J_decimal"])), min(flat(hp_minus["J_decimal"])))),
                             double_plus_residual=rp.tolist(), double_minus_residual=rm.tolist(),
                             decimal_plus_residual=[str(x) for x in hp_plus["internal_decimal"]],
                             decimal_minus_residual=[str(x) for x in hp_minus["internal_decimal"]]))
    record_property("frozen_fd_curve", json.dumps(rows, separators=(",", ":")))
    assert len(rows) == 5
    assert min(Decimal(r["double_error"]) for r in rows) <= Decimal("1e-6")
    assert min(Decimal(r["decimal_error"]) for r in rows) <= Decimal("1e-8")


def test_mixed_two_by_two_assembly_against_independent_hp(record_property):
    h = 1./8
    xx, yy = np.meshgrid(np.arange(3)*h, np.arange(3)*h)
    coordinates = np.column_stack((xx.ravel(), yy.ravel()))
    connectivity = np.array([[0, 1, 4, 3], [1, 2, 5, 4], [3, 4, 7, 6], [4, 5, 8, 7]])
    factors = np.array([1., 1e-7, 1e-7, 1.])
    model = TMCModel(coordinates, connectivity, LAM*factors, MU*factors, KR, h, h,
                     solid=factors == 1, fixed_dofs=np.array([], dtype=int))
    lift, w = fields("huhu", coordinates)
    state = SplitDisplacement(lift, w)
    direction = ((np.arange(18) % 7)-3)/8
    data = fixture(model.ops, connectivity=connectivity, lam=model.lam, mu=model.mu, ndof=18)
    hp50 = reference_class()(data, precision=50).evaluate(lift, w, tangent_direction=direction)
    hp = reference_class()(data, precision=80).evaluate(lift, w, tangent_direction=direction)
    K, internal, result = kernel.assemble_split(model, state)
    none, residual_only, _ = kernel.assemble_split(model, state, tangent=False)
    assert none is None and K.shape == (18, 18)
    assert np.linalg.norm((K-K.T).data) > 1e-12*np.linalg.norm(K.data)
    actions = component_actions(lift[model.edofs], w[model.edofs], model.ops,
                                model.lam, model.mu, KR, direction[model.edofs])
    checks = []
    with localcontext() as context:
        context.prec = 100
        force_floor = D(MU)*D(h)*D(2.**-45)
        action_floor = D(MU)*norm([D(x) for x in direction])*Decimal("1e-12")
        for name, actual in (("total_assembled", internal), ("residual_only_assembled", residual_only)):
            check(checks, name, error(actual, hp["internal_decimal"]), Decimal("1e-9")*max(norm(hp["internal_decimal"]), force_floor))
        for name, target in (("material", "material_internal_decimal"), ("regularization", "regularization_internal_decimal")):
            assembled = np.bincount(model.edofs.ravel(), weights=result[name+"_residual"].ravel(), minlength=18)
            check(checks, name+"_assembled", error(assembled, hp[target]), Decimal("1e-9")*max(norm(hp[target]), force_floor))
        for name, target in (("residual", "tangent_action_decimal"), ("material_residual", "material_tangent_action_decimal"),
                             ("regularization_residual", "regularization_tangent_action_decimal")):
            action = np.bincount(model.edofs.ravel(), weights=actions[name].ravel(), minlength=18)
            check(checks, name+"_Jv", error(action, hp[target]), Decimal("1e-8")*max(norm(hp[target]), action_floor))
        check(checks, "returned_sparse_Kv", error(K@direction, hp["tangent_action_decimal"]),
              Decimal("1e-8")*max(norm(hp["tangent_action_decimal"]), action_floor))
        check(checks, "reference_50_80", norm([a-b for a, b in zip(hp50["internal_decimal"], hp["internal_decimal"])]),
              Decimal("1e-30")*max(norm(hp["internal_decimal"]), force_floor))
    record_property("matrix_relative_nonsymmetry", np.linalg.norm((K-K.T).data)/np.linalg.norm(K.data))
    finish(checks, record_property)


@pytest.mark.parametrize("tangent", [True, False])
@pytest.mark.parametrize("negative", [False, True])
def test_total_invalid_J_is_rejected_in_both_numpy_and_jax_guards(tangent, negative):
    ops = operators(1., 1.)
    coordinates = xy(1., 1.)
    lift = np.column_stack((np.zeros(4), -coordinates[:, 1])).ravel()[None]
    w = np.column_stack((np.zeros(4), -2.**-17*coordinates[:, 1] if negative else np.zeros(4))).ravel()[None]
    assert np.all(kernel.determinants_split(lift, w, ops) <= 0)
    with pytest.raises(KernelError) as caught:
        kernel.batch_response_split(lift, w, ops, LAM, MU, KR, tangent=tangent)
    assert caught.value.code == "invalid_J"
    # Direct private guard invocation verifies the JAX rejection branch too;
    # this branch has no log/inverse and must preserve the raw invalid J.
    function = kernel._batch_with_tangent if tangent else kernel._batch_without_tangent
    raw = function(lift, w, ops["grad"], ops["hessian"], ops["weights"], np.array([LAM]), np.array([MU]), KR)
    assert np.all(np.asarray(raw["J"]) <= 0)
    assert np.all(np.isnan(np.asarray(raw["residual"])))


@pytest.mark.parametrize("bad", [np.zeros(8), np.zeros((0, 8)), np.zeros((1, 7)),
                                np.full((1, 8), np.nan), np.zeros((1, 8), dtype=complex)])
def test_batch_rejects_invalid_component_shapes_or_values(bad):
    with pytest.raises(KernelError):
        kernel.batch_response_split(bad, np.zeros((1, 8)), operators(1., 1.), LAM, MU, KR)


def test_model_assembly_rejects_implicit_collapsed_array():
    coordinates = xy(1., 1.)
    model = TMCModel(coordinates, np.array([[0, 1, 2, 3]]), LAM, MU, KR, 1., 1.)
    with pytest.raises(TMCError):
        kernel.assemble_split(model, np.zeros(8))
    with pytest.raises(TMCError):
        kernel.assemble_split(model, SplitDisplacement(np.zeros(2), np.zeros(2)))


def test_legacy_import_retains_old_physical_response(record_property):
    ops = operators(1., 1.)
    u, _ = fields("legacy", xy(1., 1.))
    state = SplitDisplacement.from_legacy(u)
    old = batch_response(u[None], ops, LAM, MU, KR)
    new = kernel.batch_response_split(state.lift[None], state.fluctuation[None], ops, LAM, MU, KR)
    hp = reference_class()(fixture(ops), precision=80).evaluate(state.lift, state.fluctuation)
    checks = []
    with localcontext() as context:
        context.prec = 100
        bound = Decimal("1e-9")*max(norm(hp["internal_decimal"]), D(MU)*D(2.**-45))
        for name, values in (("old", old), ("split", new)):
            check(checks, name, error(values["residual"][0], hp["internal_decimal"]), bound)
    finish(checks, record_property)
