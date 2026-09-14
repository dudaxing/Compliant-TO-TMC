"""Small independent analytic tests of the development Decimal reference.

No archived C-shape state or full path is evaluated by this test module.
"""
from decimal import Decimal, localcontext
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from hf2_precision_reference import DecimalQ1Reference, compare_float_to_decimal


def fixture(lam=2.,mu=3.,kr=.125):
    # A 2x2 reference square gives exactly representable gradient/Hessian data.
    points = np.array([(x,y) for x in (-1.,0.,1.) for y in (-1.,0.,1.)])
    signs = np.array([[-1.,-1.],[1.,-1.],[1.,1.],[-1.,1.]])
    grad = np.empty((9,4,2))
    for a,(sx,sy) in enumerate(signs):
        grad[:,a,0]=sx*(1+sy*points[:,1])/4
        grad[:,a,1]=sy*(1+sx*points[:,0])/4
    hessian=np.zeros((4,2,2))
    hessian[:,0,1]=signs[:,0]*signs[:,1]/4
    hessian[:,1,0]=hessian[:,0,1]
    return dict(grad=grad,hessian=hessian,weights=np.outer([1.,4.,1.],[1.,4.,1.]).ravel()/9,
                lam=np.array([lam]),mu=np.array([mu]),kr=np.array(kr),
                connectivity=np.array([[0,1,2,3]],dtype=np.int64),F0=np.zeros(8),fixed_dofs=np.array([],dtype=np.int64))


def coordinates():
    return np.array([[0.,0.],[2.,0.],[2.,2.],[0.,2.]])


def analytic_force(P,data):
    # Constant first Piola traction integrated against known reference gradients.
    D=Decimal.from_float
    return [sum((D(float(data['weights'][q]))*P[i][j]*D(float(data['grad'][q,a,j]))
                 for q in range(9) for j in range(2)),Decimal(0)) for a in range(4) for i in range(2)]


def test_identity_translation_and_translation_derivative_are_exactly_zero():
    data=fixture()
    response=DecimalQ1Reference(data).evaluate(np.tile([.125,-.25],4),0.,direction=np.tile([.5,.25],4))
    assert all(x==0 for x in response['internal_decimal'])
    assert all(x==0 for x in response['tangent_action_decimal'])
    assert all(x==0 for x in response['material_energy_decimal'])
    assert all(x==1 for x in response['J_decimal'][0])
    assert Decimal(response['relative_residual'])==0


def test_affine_piola_force_and_energy_match_constant_field_analytic_solution():
    data=fixture()
    F=np.diag([1.125,.875])
    u=(coordinates()@(F-np.eye(2)).T).ravel()
    response=DecimalQ1Reference(data).evaluate(u,0.)
    with localcontext() as context:
        context.prec=50
        a,b=Decimal('1.125'),Decimal('.875')
        J=a*b
        c=2*J.ln()-3
        P=[[3*a+c/a,Decimal(0)],[Decimal(0),3*b+c/b]]
        expected=analytic_force(P,data)
        assert max(abs(x-y) for x,y in zip(expected,response['material_internal_decimal']))<Decimal('1e-45')
        assert all(x==0 for x in response['regularization_internal_decimal'])
        W=(2*J.ln()**2+3*(a*a+b*b-2-2*J.ln()))/2
        energy=W*sum((Decimal.from_float(float(w)) for w in data['weights']),Decimal(0))
        assert abs(response['material_energy_decimal'][0]-energy)<Decimal('1e-45')


def test_identity_affine_direction_derivative_matches_linear_isotropic_formula():
    data=fixture()
    dF=np.array([[.125,.25],[.5,-.0625]])
    direction=(coordinates()@dF.T).ravel()
    response=DecimalQ1Reference(data).evaluate(np.zeros(8),0.,direction=direction)
    with localcontext() as context:
        context.prec=50
        d=[[Decimal.from_float(float(x)) for x in row] for row in dF]
        tr=d[0][0]+d[1][1]
        dP=[[3*(d[i][j]+d[j][i])+(2*tr if i==j else 0) for j in range(2)] for i in range(2)]
        expected=analytic_force(dP,data)
        assert max(abs(a-b) for a,b in zip(expected,response['tangent_action_decimal']))<Decimal('1e-45')
        assert all(x==0 for x in response['regularization_tangent_action_decimal'])


@pytest.mark.parametrize('lam,mu,kr',[(2.,3.,.125),(0.,0.,.125),(2.,3.,0.)])
def test_analytic_direction_derivative_matches_decimal_ideal_central_difference(lam,mu,kr):
    reference=DecimalQ1Reference(fixture(lam,mu,kr))
    u=np.array([0.,0.,.0625,0.,.125,-.0625,0.,.03125])
    v=np.array([.125,-.0625,0.,.125,-.0625,.25,.03125,0.])
    base=reference.evaluate(u,0.,direction=v)
    h=1e-5
    plus=reference.evaluate(u,0.,direction=v,offset=h,derivative=False)
    minus=reference.evaluate(u,0.,direction=v,offset=-h,derivative=False)
    assert 'tangent_action' not in plus
    with localcontext() as context:
        context.prec=50
        fd=[(a-b)/(2*Decimal.from_float(h)) for a,b in zip(plus['internal_decimal'],minus['internal_decimal'])]
        error=sum(((a-b)**2 for a,b in zip(fd,base['tangent_action_decimal'])),Decimal(0)).sqrt()
        scale=sum((a*a for a in base['tangent_action_decimal']),Decimal(0)).sqrt()
        assert error/scale<Decimal('1e-9')


def test_external_product_is_subtracted_before_float_rounding():
    data=fixture()
    data['F0'][0]=.3
    response=DecimalQ1Reference(data).evaluate(np.zeros(8),.1)
    with localcontext() as context:
        context.prec=50
        expected=-(Decimal.from_float(.1)*Decimal.from_float(.3))
        assert response['residual_decimal'][0]==expected
        assert response['residual_decimal'][0]!=-Decimal.from_float(.1*.3)


def test_float_comparison_retains_sub_float_reference_difference():
    with localcontext() as context:
        context.prec=50
        reference=[Decimal(1)+Decimal('1e-30')]
        result=compare_float_to_decimal(np.array([1.]),reference,Decimal(1))
    assert Decimal(result['absolute_error_decimal'])==Decimal('1e-30')
    assert result['absolute_error']>0


def test_reference_precision_increase_preserves_nonaffine_force():
    data=fixture()
    u=np.array([0.,0.,.0625,0.,.125,-.0625,0.,.03125])
    a=DecimalQ1Reference(data,precision=50).evaluate(u,.75)
    b=DecimalQ1Reference(data,precision=80).evaluate(u,.75)
    assert max(abs(x-y) for x,y in zip(a['internal_decimal'],b['internal_decimal']))<Decimal('1e-30')


@pytest.mark.parametrize('F',[np.diag([0.,1.]),np.diag([-1.,1.])])
def test_nonpositive_J_is_rejected_before_logarithm(F):
    u=(coordinates()@(F-np.eye(2)).T).ravel()
    with pytest.raises(ValueError,match='Nonpositive'):
        DecimalQ1Reference(fixture()).evaluate(u,1.)


def test_invalid_fixture_or_perturbation_is_rejected():
    data=fixture()
    data['weights']=data['weights'].astype(complex)
    with pytest.raises(ValueError,match='real numeric'):
        DecimalQ1Reference(data)
    reference=DecimalQ1Reference(fixture())
    with pytest.raises(ValueError,match='requires a direction'):
        reference.evaluate(np.zeros(8),1.,offset=.1)
    with pytest.raises(ValueError,match='finite'):
        reference.evaluate(np.full(8,np.nan),1.)
