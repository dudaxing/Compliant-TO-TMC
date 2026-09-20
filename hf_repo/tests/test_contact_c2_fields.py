"""Manufactured saved fields: independent force and boundary contracts, no FE."""
from decimal import Decimal, localcontext
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from contact_c2_fields import comparison, gauss_legendre, reconstruct
from hf4_split_precision_reference import DecimalSplitQ1Reference
from contact_c2_sbp import decompose_material


def fixture():
    xy=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
    points=np.array([(x,y) for x in (-1.,0.,1.) for y in (-1.,0.,1.)])
    x,y=points.T
    grad=np.empty((9,4,2))
    grad[:,:,0]=np.column_stack((y-1,1-y,1+y,-1-y))/2
    grad[:,:,1]=np.column_stack((x-1,-1-x,1+x,1-x))/2
    hessian=np.zeros((4,2,2))
    hessian[:,0,1]=hessian[:,1,0]=[1.,-1.,1.,-1.]
    return dict(coordinates=xy,connectivity=np.array([[0,1,2,3]]),grad=grad,hessian=hessian,
        weights=np.outer([1.,4.,1.],[1.,4.,1.]).ravel()/36,
        lam=np.array([2.]),mu=np.array([3.]),kr=np.array(.1),F0=np.zeros(8),fixed_dofs=np.array([0,1]),
        solid=np.array([True]),top_nodes=np.array([2,3]))


def fields():
    return dict(translation=np.tile([0.,1.],4),top=np.array([0.,0.,0.,0.,0.,1.,0.,1.]),
                local=np.array([0.,0.,0.,0.,0.,1.,0.,0.]))


def test_gauss_exact_polynomial_moments_at_declared_precision():
    with localcontext() as ctx:
        ctx.prec=80
        for order in (8,16,32,64):
            rule=gauss_legendre(order,80)
            for degree in (0,1,2,7,2*order-2):
                expected=Decimal(0) if degree%2 else Decimal(2)/(degree+1)
                actual=sum((weight*x**degree for x,weight in rule),Decimal(0))
                assert abs(actual-expected)<Decimal("1e-75")


def test_rigid_split_translation_has_zero_stress_and_weak_force():
    f=fixture(); lift=np.tile([.25,.5],4); w=np.zeros(8)
    result=reconstruct(f,lift,w,fields())
    assert all(x==0 for x in result["total"])
    assert all(abs(x)<Decimal("1e-75") for x in result["edge_projections"]["gauss64"])
    assert result["current"][2]==[Decimal("1.25"),Decimal("1.5")]


def test_affine_compression_direct_top_sign_and_half_nodal_projection():
    f=fixture(); u=np.zeros((4,2));u[:,1]=-.25*f["coordinates"][:,1]
    result=reconstruct(f,np.zeros(8),u.ravel(),fields())
    assert all(x==0 for x in result["regularization"])
    assert result["edge_elements"][0]["full_edge_material_compression_certificate"]["certified"]
    with localcontext() as ctx:
        ctx.prec=80
        expected=Decimal(3)*Decimal(".75")+(Decimal(2)*Decimal(".75").ln()-3)/Decimal(".75")
        for node in (2,3):
            internal=result["edge_projections"]["gauss64"][2*node+1]
            assert abs(internal-expected/2)<Decimal("1e-75")
            assert -internal>0 # model on plane compressive force
            assert abs(internal-result["material"][2*node+1])<Decimal("1e-14")


def test_bilinear_field_reassembles_reference_and_nonzero_virtual_work():
    f=fixture(); u=np.array([0.,0.,0.,0.,.125,-.25,0.,-.125])
    result=reconstruct(f,np.zeros(8),u,fields())
    hp=DecimalSplitQ1Reference(f,precision=80).evaluate(np.zeros(8),u,derivative=False)
    for key in ("material","regularization"):
        assert comparison(result[key],hp[key+"_internal_decimal"],unit="N")["status"]=="pass"
    assert result["virtual_work"]["local"]["integrated_N_mm"]["regularization"]!=0
    assert result["virtual_work"]["top"]["integrated_N_mm"]["regularization"]==0
    assert all(c["status"]=="pass" for v in result["virtual_work"].values() for c in v["checks"].values())
    # This is deliberately not an equality: a top weak nodal value includes
    # interior divergence and contributions from the other cell boundaries.
    assert abs(result["material"][5]-result["edge_projections"]["gauss64"][5])>Decimal(".01")


def test_new_boundary_quantities_cross_precision():
    f=fixture(); u=np.array([0.,0.,0.,0.,.125,-.25,0.,-.125])
    low=reconstruct(f,np.zeros(8),u,fields(),precision=80)
    high=reconstruct(f,np.zeros(8),u,fields(),precision=120)
    for key in low["edge_projections"]:
        assert comparison(low["edge_projections"][key],high["edge_projections"][key],unit="N")["status"]=="pass"


def test_field_to_sbp_pipeline_preserves_physical_and_consistent_edge_rules():
    f=fixture(); u=np.array([0.,0.,0.,0.,.125,-.25,0.,-.125])
    result=reconstruct(f,np.zeros(8),u,fields())
    sbp=decompose_material(f,result["elements"],precision=80)
    assert sbp["status"]=="pass"
    vectors=sbp["fields"]
    assert comparison(vectors["material_N"],result["material"],unit="N")["status"]=="pass"
    assert comparison(vectors["top_edge_physical_simpson_N"],result["edge_projections"]["simpson3"],unit="N")["status"]=="pass"
    assert any(v!=0 for v in vectors["top_weight_correction_N"])


@pytest.mark.parametrize("case",["nonfinite","inverted","nonrectangle"])
def test_invalid_reconstruction_is_not_silent(case):
    f=fixture(); u=np.zeros(8)
    if case=="nonfinite": u[1]=np.nan
    if case=="inverted": u[[5,7]]=-2.
    if case=="nonrectangle": f["coordinates"][2,0]=1.1
    with pytest.raises(ValueError): reconstruct(f,np.zeros(8),u,fields())
