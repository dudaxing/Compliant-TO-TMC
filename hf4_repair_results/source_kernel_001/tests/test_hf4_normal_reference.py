"""Independent material/contact reference checks, without production FE code.

Test execution is a separately budgeted operation; import only defines tests.
"""
from decimal import Decimal, localcontext
import importlib.util
import json
from pathlib import Path

import pytest


_path = Path(__file__).resolve().parents[1]/"scripts"/"hf4_normal_reference.py"
_spec = importlib.util.spec_from_file_location("hf4_normal_under_test", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
evaluate = _module.evaluate_normal_reference
crosscheck = _module.crosscheck_normal_reference
stress = _module.compressive_nominal_stress


def parameters(**changes):
    # Dyadic geometry isolates coefficient promotion from geometry rounding.
    lam, mu = 1.0*0.3/((1+0.3)*(1-2*0.3)), 1.0/(2*(1+0.3))
    result = dict(lam_s=lam, mu_s=mu, lam_v=1e-6*lam, mu_v=1e-6*mu,
                  width=1.0, H1=1.0, H2=1.0, gap=0.25, thickness=1.0, d=0.28125)
    result.update(changes)
    return result


def D(value):
    return Decimal.from_float(float(value))


def test_zero_motion_is_exactly_stress_free_in_both_references():
    result = evaluate(**parameters(d=0.0))
    for model in ("finite_gamma", "hard_contact"):
        assert Decimal(result[model]["force_N"]) == 0
        assert Decimal(result[model]["s_s"]) == 1
        assert Decimal(result[model]["gap_mm"]) == Decimal("0.25")
        assert Decimal(result[model]["length_residual_mm"]) == 0
    assert Decimal(result["finite_gamma"]["traction_residual_MPa"]) == 0
    assert result["finite_gamma"]["root"]["iterations"] == 0


@pytest.mark.parametrize("d,phase", [(0.125, "separated"), (0.25, "touching_zero_force"),
                                     (0.28125, "compressed_contact")])
def test_hard_contact_branch_and_complementarity_are_independent_of_medium(d, phase):
    first = evaluate(**parameters(d=d))
    second = evaluate(**parameters(d=d, lam_v=0.03125, mu_v=0.0625))
    assert first["hard_contact"] == second["hard_contact"]
    hard = first["hard_contact"]
    assert hard["phase"] == phase
    assert Decimal(hard["gap_mm"]) >= 0
    assert Decimal(hard["force_N"]) >= 0
    assert Decimal(hard["complementarity_MPa_mm"]) == 0
    with localcontext() as context:
        context.prec = 80
        if d <= 0.25:
            assert Decimal(hard["force_N"]) == 0
            assert Decimal(hard["gap_mm"]) == D(0.25)-D(d)
        else:
            # Direct closed form at a dyadic prescribed solid stretch, not an
            # invocation of the reference's material helper.
            s = Decimal(1)-(D(d)-D(0.25))/2
            expected = D(parameters()["mu_s"])*(1/s-s)-D(parameters()["lam_s"])*s.ln()/s
            assert abs(Decimal(hard["force_N"])-expected) < Decimal("1e-48")


def test_identical_three_layers_recover_homogeneous_closed_form():
    p = parameters(lam_s=0.5, mu_s=0.25, lam_v=0.5, mu_v=0.25, d=0.28125)
    result = evaluate(**p, precision=50)["finite_gamma"]
    with localcontext() as context:
        context.prec = 80
        s = Decimal(1)-D(p["d"])/(D(p["H1"])+D(p["H2"])+D(p["gap"]))
        expected = Decimal("0.25")*(1/s-s)-Decimal("0.5")*s.ln()/s
        assert abs(Decimal(result["s_s"])-s) < Decimal("1e-49")
        assert abs(Decimal(result["s_v"])-s) < Decimal("1e-49")
        assert abs(Decimal(result["force_N"])-expected) < Decimal("1e-48")


def test_actual_medium_coefficients_are_promoted_not_reconstructed_from_gamma():
    p = parameters(lam_v=0.00000031, mu_v=0.00000027)
    result = evaluate(**p)
    assert result["inputs"]["decimal"]["lam_v"] == str(D(p["lam_v"]))
    assert result["inputs"]["decimal"]["mu_v"] == str(D(p["mu_v"]))
    assert result["inputs"]["binary64_hex"]["lam_v"] == p["lam_v"].hex()
    with localcontext() as context:
        context.prec = 80
        finite = result["finite_gamma"]
        s = Decimal(finite["s_v"])
        independent_pv = D(p["mu_v"])*(1/s-s)-D(p["lam_v"])*s.ln()/s
        assert abs(Decimal(finite["p_medium_MPa"])-independent_pv) < Decimal("1e-48")
        assert abs(Decimal(finite["traction_residual_MPa"])) < Decimal("1e-45")


def test_dimensional_force_and_energy_scale_with_area_but_stretches_do_not():
    base = evaluate(**parameters())["finite_gamma"]
    scaled = evaluate(**parameters(width=2.0, thickness=3.0))["finite_gamma"]
    for field in ("s_s", "s_v", "gap_mm", "p_nominal_MPa"):
        assert scaled[field] == base[field]
    with localcontext() as context:
        context.prec = 80
        for field in ("force_N", "material_energy_solid_Nmm", "material_energy_medium_Nmm"):
            assert abs(Decimal(scaled[field])-6*Decimal(base[field])) < Decimal("1e-48")


def test_height_split_does_not_change_same_material_series_response():
    a = evaluate(**parameters(H1=0.5, H2=1.5))
    b = evaluate(**parameters(H1=1.25, H2=0.75))
    assert a["finite_gamma"] == b["finite_gamma"]
    assert set(a["hard_contact"]) == set(b["hard_contact"])
    for field in a["hard_contact"]:
        if field in ("model", "phase"):
            assert a["hard_contact"][field] == b["hard_contact"][field]
        else:
            # Decimal retains meaningful input exponents; physically equal
            # shortenings need not serialize with identical trailing zeros.
            assert Decimal(a["hard_contact"][field]) == Decimal(b["hard_contact"][field])


@pytest.mark.parametrize("d", [0.125, 0.21875, 0.25, 0.28125, 0.375])
def test_finite_medium_transmits_precontact_force_and_retains_positive_gap(d):
    result = evaluate(**parameters(d=d))
    finite, hard = result["finite_gamma"], result["hard_contact"]
    assert Decimal(finite["force_N"]) > 0
    assert 0 < Decimal(finite["s_s"]) < 1
    assert 0 < Decimal(finite["s_v"]) < 1
    assert Decimal(finite["gap_mm"]) > Decimal(hard["gap_mm"])
    assert Decimal(finite["force_N"]) > Decimal(hard["force_N"])
    assert abs(Decimal(finite["normalized_length_residual"])) < Decimal("1e-48")
    assert abs(Decimal(finite["normalized_traction_residual"])) < Decimal("1e-44")


@pytest.mark.parametrize("gamma", [1e-6, 1e-7])
@pytest.mark.parametrize("d", [0.0, 0.25, 0.375])
def test_two_precisions_agree_without_a_zero_force_denominator(gamma, d):
    p = parameters(d=d)
    p.update(lam_v=gamma*p["lam_s"], mu_v=gamma*p["mu_s"])
    result = crosscheck(p)
    assert result["threshold_applied"] is False
    for model in result["errors"].values():
        for field in model.values():
            assert Decimal(field["scale"]) > 0
            assert Decimal(field["normalized_error"]) < Decimal("1e-40")


def test_serialized_stretches_reproduce_exported_residuals():
    p = parameters()
    result = evaluate(**p)
    finite = result["finite_gamma"]
    with localcontext() as context:
        context.prec = 80
        ss, sv = Decimal(finite["s_s"]), Decimal(finite["s_v"])
        mismatch = stress(ss, D(p["lam_s"]), D(p["mu_s"]))-stress(sv, D(p["lam_v"]), D(p["mu_v"]))
        length = (D(p["H1"])+D(p["H2"]))*ss+D(p["gap"])*sv-(D(p["H1"])+D(p["H2"])+D(p["gap"])-D(p["d"]))
        assert abs(mismatch-Decimal(finite["traction_residual_MPa"])) < Decimal("1e-70")
        assert length == Decimal(finite["length_residual_mm"])
    json.dumps(result, allow_nan=False)


def test_pure_mu_stress_and_compression_monotonicity():
    with localcontext() as context:
        context.prec = 80
        assert stress(Decimal("0.5"), Decimal(0), Decimal(2)) == Decimal(3)
        pressures = [stress(Decimal(s), Decimal("0.75"), Decimal("0.5"))
                     for s in ("1", "0.9", "0.5", "0.01")]
        assert pressures == sorted(pressures)
        assert len(set(pressures)) == len(pressures)


def test_caller_decimal_context_cannot_change_reference():
    normal = evaluate(**parameters())
    with localcontext() as context:
        context.prec = 6
        low_caller = evaluate(**parameters())
    assert normal == low_caller


@pytest.mark.parametrize("field,value", [("width", 0.0), ("gap", -1.0), ("mu_v", 0.0),
                                        ("lam_s", -0.5), ("d", -0.125), ("d", 2.25),
                                        ("d", float("inf")), ("d", float("nan")),
                                        ("d", True), ("d", "0.25"), ("d", Decimal("0.25"))])
def test_invalid_physical_inputs_fail_explicitly(field, value):
    with pytest.raises(ValueError):
        evaluate(**parameters(**{field: value}))


@pytest.mark.parametrize("precision", [True, 20, 50.0])
def test_invalid_precision_is_rejected(precision):
    with pytest.raises(ValueError):
        evaluate(**parameters(), precision=precision)


def test_crossprecision_order_is_explicit():
    with pytest.raises(ValueError):
        crosscheck(parameters(), low_precision=80, high_precision=50)
