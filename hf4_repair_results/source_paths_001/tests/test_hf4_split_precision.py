"""Independent split-state HP semantics; no production solve/kernel import."""
from copy import deepcopy
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sys

import numpy as np
import pytest

_repo=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(_repo/"scripts"))
from hf4_split_precision_reference import DecimalSplitQ1Reference, evaluate_split_prescribed_state
from hf2_precision_reference import DecimalQ1Reference
from preflight_hf4_split import tabulated_model, nonuniform_cases, tiny_case

PHYSICS=json.loads((_repo/"configs/hf4/validation_spec.json").read_text())


def D(value): return Decimal.from_float(float(value))


def primitive(model):
    return dict(model,F0=np.zeros(2*len(model["coordinates"])))


def case_kwargs(case):
    return dict(fixture=case["model"],u_lift=case["lift"],u_fluctuation=case["fluctuation"],
                d=case["d"],base=case["base"],direction=case["direction"],
                reaction_groups=case["groups"],force_scale_per_length=1.)


def test_legacy_import_retains_original_independent_force_energy_and_action():
    m=tabulated_model(1,1,1.,PHYSICS)
    x,y=m["coordinates"].T
    u=np.column_stack((x/64+y/128,-x/256+y/32)).ravel()
    v=np.arange(len(u),dtype=float)/32
    original=DecimalQ1Reference(primitive(m),precision=50).evaluate(u,0.,direction=v)
    split=DecimalSplitQ1Reference(primitive(m),precision=50).evaluate(u,np.zeros_like(u),tangent_direction=v)
    for name in ("internal_decimal","material_internal_decimal","regularization_internal_decimal",
                 "material_energy_decimal","J_decimal","tangent_action_decimal",
                 "material_tangent_action_decimal","regularization_tangent_action_decimal"):
        assert split[name]==original[name]
    assert split["physical_displacement_decimal"]==[D(x) for x in u]


def test_authority_preserves_motion_lost_from_the_display_array():
    case=tiny_case(PHYSICS)
    L,w=case["lift"],case["fluctuation"]
    assert np.array_equal(L+w,L)
    hp=evaluate_split_prescribed_state(**case_kwargs(case))
    with localcontext() as context:
        context.prec=100
        assert hp["physical_displacement_decimal"]==[D(a)+D(b) for a,b in zip(L,w)]
    assert hp["physical_displacement_decimal"]!=[D(x) for x in L+w]
    assert any(x!=0 for x in hp["material_internal_decimal"])
    assert hp["constraint_error_decimal"]==0
    assert hp["state_representation"]=="split_displacement_v1"
    assert hp["G"].shape==(1,9,2,2)
    assert hp["F"].shape==(1,9,2,2)
    assert hp["Hu"].shape==(1,2,2,2)


def test_offset_changes_only_fluctuation_without_collapsing_either_component():
    case=nonuniform_cases(PHYSICS)[0]
    v=case["directions"]["v1"]
    hp=evaluate_split_prescribed_state(**case_kwargs(case),tangent_direction=v,
        fluctuation_offset=2.**-20,derivative=False)
    with localcontext() as context:
        context.prec=150
        expected=[D(a)+D(b)+D(2.**-20)*D(c) for a,b,c in zip(case["lift"],case["fluctuation"],v)]
    assert hp["physical_displacement_decimal"]==expected
    assert hp["lift_decimal"]==[D(x) for x in case["lift"]]
    assert "tangent_action_decimal" not in hp
    assert hp["constraint_error_decimal"]==0  # v=0 on the fixed bottom edge.


def test_nonzero_component_hessians_cancel_to_the_declared_nonzero_total():
    case=nonuniform_cases(PHYSICS)[0]
    hp=evaluate_split_prescribed_state(**case_kwargs(case))
    for element in hp["Hu_decimal"]:
        assert element[0][0][1]==element[0][1][0]==D(2.**-15)
        assert element[1][0][1]==element[1][1][0]==D(2.**-16)
    assert any(x!=0 for x in hp["regularization_internal_decimal"])
    ref=DecimalSplitQ1Reference(primitive(case["model"]))
    left=ref.evaluate(case["lift"],np.zeros_like(case["lift"]))
    right=ref.evaluate(np.zeros_like(case["lift"]),case["fluctuation"])
    assert any(x!=0 for row in left["Hu_decimal"] for plane in row for axis in plane for x in axis)
    assert any(x!=0 for row in right["Hu_decimal"] for plane in row for axis in plane for x in axis)
    # Each component has a different J. Separate nonlinear regularization
    # forces must not be substituted for exp(-5 J_total)*A*Hu_total.
    with localcontext() as context:
        context.prec=50
        separate=[a+b for a,b in zip(left["regularization_internal_decimal"],right["regularization_internal_decimal"])]
    assert separate!=hp["regularization_internal_decimal"]


def test_exactly_equivalent_decompositions_have_identical_hp_fields_and_jv():
    first,second=nonuniform_cases(PHYSICS)
    a=evaluate_split_prescribed_state(**case_kwargs(first),tangent_direction=first["directions"]["v2"])
    b=evaluate_split_prescribed_state(**case_kwargs(second),tangent_direction=second["directions"]["v2"])
    for field in ("physical_displacement_decimal","G_decimal","F_decimal","Hu_decimal","J_decimal",
                  "internal_decimal","material_internal_decimal","regularization_internal_decimal",
                  "tangent_action_decimal","regularization_tangent_action_decimal","material_energy_decimal"):
        assert a[field]==b[field]


def test_analytic_fluctuation_direction_matches_ideal_decimal_difference():
    case=nonuniform_cases(PHYSICS)[0]
    v=case["directions"]["v1"]
    ref=DecimalSplitQ1Reference(primitive(case["model"]),precision=80)
    h=2.**-20
    base=ref.evaluate(case["lift"],case["fluctuation"],tangent_direction=v)
    plus=ref.evaluate(case["lift"],case["fluctuation"],tangent_direction=v,fluctuation_offset=h,derivative=False)
    minus=ref.evaluate(case["lift"],case["fluctuation"],tangent_direction=v,fluctuation_offset=-h,derivative=False)
    with localcontext() as context:
        context.prec=100
        fd=[(a-b)/(2*D(h)) for a,b in zip(plus["internal_decimal"],minus["internal_decimal"])]
        error=sum(((a-b)**2 for a,b in zip(base["tangent_action_decimal"],fd)),Decimal(0)).sqrt()
        scale=max(sum((x*x for x in base["tangent_action_decimal"]),Decimal(0)).sqrt(),Decimal("1e-12"))
    assert error/scale < Decimal("1e-8")


def test_only_total_j_controls_the_domain():
    m=tabulated_model(1,1,1.,PHYSICS)
    x,y=m["coordinates"].T
    L=np.column_stack((0*x,-1.5*y)).ravel()
    w=np.column_stack((0*x,(.5+2.**-17)*y)).ravel()
    hp=DecimalSplitQ1Reference(primitive(m)).evaluate(L,w)
    assert all(x==D(2.**-17) for row in hp["J_decimal"] for x in row)
    for scale in (0.,-2.**-17):
        singular=np.column_stack((0*x,-y)).ravel()
        correction=np.column_stack((0*x,scale*y)).ravel()
        with pytest.raises(ValueError,match="Nonpositive"):
            DecimalSplitQ1Reference(primitive(m)).evaluate(singular,correction)


def test_50_and_80_digits_resolve_small_authoritative_force():
    case=tiny_case(PHYSICS)
    low=evaluate_split_prescribed_state(**case_kwargs(case),precision=50)
    high=evaluate_split_prescribed_state(**case_kwargs(case),precision=80)
    with localcontext() as context:
        context.prec=100
        error=sum(((a-b)**2 for a,b in zip(low["internal_decimal"],high["internal_decimal"])),Decimal(0)).sqrt()
        assert error/high["force_scale_decimal"] < Decimal("1e-30")


def test_lift_fluctuation_and_primitive_arrays_are_not_modified():
    case=nonuniform_cases(PHYSICS)[0]
    before=deepcopy(case)
    evaluate_split_prescribed_state(**case_kwargs(case),tangent_direction=case["directions"]["v1"])
    for name in ("lift","fluctuation","base","direction"):
        np.testing.assert_array_equal(case[name],before[name])
    for name in case["model"]:
        np.testing.assert_array_equal(case["model"][name],before["model"][name])


@pytest.mark.parametrize("updates", [
    {"u_lift":np.zeros(7)}, {"u_fluctuation":np.zeros(7)},
    {"u_lift":np.full(8,np.nan)}, {"fluctuation_offset":1.},
    {"tangent_direction":np.zeros(7)}, {"derivative":1},
    {"precision":True}, {"precision":20},
])
def test_invalid_split_or_perturbation_inputs_are_rejected(updates):
    kwargs=case_kwargs(tiny_case(PHYSICS));kwargs.update(updates)
    with pytest.raises(ValueError):
        evaluate_split_prescribed_state(**kwargs)
