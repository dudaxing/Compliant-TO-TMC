"""Independent arithmetic checks for the optional bounded DD implementation.

Fraction is an exact oracle for stored binary64 primitives. Decimal is used
only in these tests, never by the production candidate. These checks do not
replace the frozen 69-field/63-state scientific matrix.
"""
from decimal import Decimal, localcontext
from fractions import Fraction

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from hf_eval import compensated_invariants as ci


@pytest.fixture(autouse=True)
def explicit_x64_cpu():
    assert jax.default_backend() == "cpu"
    with jax.enable_x64(True):
        yield


def f(value):
    return Fraction.from_float(float(value))


def pair_fraction(pair, index=()):
    return f(np.asarray(pair[0])[index])+f(np.asarray(pair[1])[index])


def exact_array(pair, expected, *, relative=Fraction(1, 2**96)):
    expected=np.asarray(expected,dtype=object)
    assert np.asarray(pair[0]).shape==np.asarray(pair[1]).shape==expected.shape
    assert bool(ci.pair_supported(pair,np))
    for index in np.ndindex(expected.shape):
        assert abs(pair_fraction(pair,index)-expected[index]) <= relative*max(Fraction(1),abs(expected[index]))


def decimal_value(pair):
    return Decimal.from_float(float(pair[0]))+Decimal.from_float(float(pair[1]))


def test_exact_products_and_low_parts_survive_cancellation():
    a=np.array([1.+2.**-27, 1.-2.**-26, 2.**100+2.**48, -3./8])
    b=np.array([1.-2.**-27, 1.+2.**-28, 2.**-80+2.**-132, 7./16])
    products=ci.dd_product(a,b,np)
    exact_array(products,np.array([f(x)*f(y) for x,y in zip(a,b)],dtype=object),relative=Fraction(0))
    retained=ci.dd_sub(ci.dd_product(1.+2.**-27,1.-2.**-27,np),ci.dd_const(1.,np),np)
    assert pair_fraction(retained)==-Fraction(1,2**54)
    accumulated=ci.dd_sum(ci.dd_from(np.array([1.,2.**-60,-1.]),np),xp=np)
    assert pair_fraction(accumulated)==Fraction(1,2**60)


def test_pair_algebra_matches_independent_rationals():
    a=(np.asarray(1.),np.asarray(2.**-54))
    b=(np.asarray(-3./4),np.asarray(2.**-55))
    av,bv=pair_fraction(a),pair_fraction(b)
    for operation,expected in ((ci.dd_add,av+bv),(ci.dd_sub,av-bv),
                               (ci.dd_mul,av*bv),(ci.dd_div,av/bv)):
        exact_array(operation(a,b,np),np.asarray(expected,dtype=object))
    # Nonzero low*low is within the supported arithmetic range and is not
    # allowed to disappear merely because both high parts cancel elsewhere.
    square=ci.dd_mul(a,a,np)
    assert abs(pair_fraction(square)-av*av) <= Fraction(1,2**104)


def independent_fields(lift,w,grad,hessian):
    """Definition-level rational contractions, independent of DD routines."""
    u=[[f(lift[a,i])+f(w[a,i]) for i in range(2)] for a in range(4)]
    G=np.empty((9,2,2),dtype=object); F=np.empty_like(G)
    B=np.empty_like(G); J=np.empty(9,dtype=object); delta=np.empty_like(J)
    Hu=np.empty((2,2,2),dtype=object)
    for q in range(9):
        for i in range(2):
            for j in range(2):
                G[q,i,j]=sum(u[a][i]*f(grad[q,a,j]) for a in range(4))
                F[q,i,j]=G[q,i,j]+int(i==j)
        for i in range(2):
            for j in range(2):
                B[q,i,j]=sum(F[q,i,k]*F[q,j,k] for k in range(2))-int(i==j)
        J[q]=F[q,0,0]*F[q,1,1]-F[q,0,1]*F[q,1,0]
        delta[q]=J[q]-1
    for i in range(2):
        for j in range(2):
            for k in range(2):
                Hu[i,j,k]=sum(u[a][i]*f(hessian[a,j,k]) for a in range(4))
    return dict(F=F,G=G,B=B,J=J,delta=delta,Hu=Hu)


def synthetic_inputs():
    # Explicitly declared operators, with no call into a production model.
    grad=np.broadcast_to(np.array([[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]]),(9,4,2)).copy()
    hessian=np.zeros((4,2,2));hessian[:,0,1]=hessian[:,1,0]=[1.,-1.,1.,-1.]
    lift=np.array([[.125,-.25],[.125,-.25],[.125,-.25],[.125,-.25]])
    w=np.array([[0.,0.],[2.**-60,0.],[2.**-60+2.**-65,2.**-61],[0.,2.**-61]])
    return lift,w,grad,hessian


def test_kinematics_and_hessian_contraction_have_rational_oracles():
    lift,w,grad,hessian=synthetic_inputs()
    reference=independent_fields(lift,w,grad,hessian)
    values=ci.kinematics_pairs(lift,w,grad,hessian,np)
    assert bool(values["supported"])
    for name,target in reference.items():
        exact_array(values[name],target)
    assert np.all(values["F"][0][:,0,0]==1.)
    assert np.all(values["F"][1][:,0,0]!=0.)
    assert np.any(reference["B"]!=0)
    expected=np.empty((4,2),dtype=object)
    for a in range(4):
        for i in range(2):
            expected[a,i]=sum(f(hessian[a,j,k])*reference["Hu"][i,j,k] for j in range(2) for k in range(2))
    exact_array(ci.hessian_action_pair(values["Hu"],hessian,np),expected)


def test_rotation_invariants_use_stored_binary64_not_ideal_identity():
    angle=.03125
    xy=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
    lift,w,grad,hessian=synthetic_inputs();lift[:]=0
    x,y=xy.T
    w[:,0]=(np.cos(angle)-1)*x-np.sin(angle)*y
    w[:,1]=np.sin(angle)*x+(np.cos(angle)-1)*y
    reference=independent_fields(lift,w,grad,hessian)
    assert any(value!=0 for value in reference["B"].ravel())
    values=ci.kinematics_pairs(lift,w,grad,hessian,np)
    for name in ("B","delta","J","Hu"):
        exact_array(values[name],reference[name])


def test_numpy_and_strict_jit_retain_identical_field_pairs():
    inputs=synthetic_inputs()
    expected=ci.kinematics_pairs(*inputs,np)
    function=jax.jit(lambda a,b,g,h:ci.kinematics_pairs(a,b,g,h,jnp),compiler_options=ci.COMPILER_OPTIONS)
    actual=function(*(jnp.asarray(v) for v in inputs))
    for name in ("F","G","B","delta","J","Hu"):
        for a,b in zip(actual[name],expected[name]):
            np.testing.assert_array_equal(np.asarray(a).view(np.uint64),np.asarray(b).view(np.uint64))
    np.testing.assert_array_equal(actual["near"],expected["near"])
    assert bool(actual["supported"])


def test_transcendentals_respect_libm_accuracy_and_retained_input_low():
    # General transcendental values have binary64 libm error, not 106-bit
    # accuracy. Near log(1), retained low input has a separately sharp test.
    with localcontext() as context:
        context.prec=100
        one=(np.asarray(1.),np.asarray(2.**-60))
        exact=decimal_value(one).ln()
        actual=decimal_value(ci.dd_log(one,np))
        assert abs(actual-exact) <= Decimal(2)**-116
        x=(np.asarray(.25),np.asarray(2.**-60))
        for operation,target in ((ci.dd_log,decimal_value(x).ln()),
                                 (ci.dd_log1p,(1+decimal_value(x)).ln()),
                                 (ci.dd_exp,decimal_value(x).exp())):
            value=decimal_value(operation(x,np))
            assert abs(value-target) <= Decimal("8e-16")*max(abs(target),Decimal(1))
        base=ci.dd_exp(ci.dd_const(1.,np),np)
        changed=ci.dd_exp(one,np)
        difference=decimal_value(changed)-decimal_value(base)
        expected=Decimal.from_float(float(base[0]))*(Decimal(2)**-60).exp()-Decimal.from_float(float(base[0]))
        assert abs(difference-expected) <= Decimal("2e-33")


def test_physical_jvp_and_vjp_match_closed_form_first_derivatives():
    low=2.**-55
    def function(x):
        a=ci.dd_add(ci.dd_from(x[0],jnp),ci.dd_const(low,jnp),jnp)
        b=ci.dd_add(ci.dd_from(x[1],jnp),ci.dd_const(-low,jnp),jnp)
        pairs=(ci.dd_mul(a,b,jnp),ci.dd_div(a,b,jnp),ci.dd_log(a,jnp),
               ci.dd_log1p(b,jnp),ci.dd_exp(b,jnp))
        return jnp.stack([ci.dd_value(p,jnp) for p in pairs])
    x=np.array([1.25,.375]);direction=np.array([.75,-.25]);cotangent=np.array([.5,-.75,.25,1.25,-.5])
    with localcontext() as context:
        context.prec=100
        a=Decimal.from_float(x[0])+Decimal.from_float(low)
        b=Decimal.from_float(x[1])-Decimal.from_float(low)
        derivative=np.array([[float(b),float(a)],[float(1/b),float(-a/b**2)],
                             [float(1/a),0.],[0.,float(1/(1+b))],[0.,float(b.exp())]])
    def jvp_evaluate(z, v):
        return jax.jvp(function, (z,), (v,))

    def vjp_evaluate(z, c):
        y, pullback = jax.vjp(function, z)
        return y, pullback(c)[0]

    _,action=jax.jit(jvp_evaluate,compiler_options=ci.COMPILER_OPTIONS)(
        jnp.asarray(x),jnp.asarray(direction))
    _,reverse_array=jax.jit(vjp_evaluate,compiler_options=ci.COMPILER_OPTIONS)(
        jnp.asarray(x),jnp.asarray(cotangent))
    reverse=np.asarray(reverse_array)
    np.testing.assert_allclose(action,derivative@direction,rtol=2e-14,atol=2e-15)
    np.testing.assert_allclose(reverse,derivative.T@cotangent,rtol=2e-14,atol=2e-15)
    np.testing.assert_allclose(cotangent@np.asarray(action),reverse@direction,rtol=2e-14,atol=2e-15)


def test_kinematic_jvp_holds_lift_fixed_and_uses_both_hessian_indices():
    lift,w,grad,hessian=synthetic_inputs()
    direction=np.array([[0.,0.],[1./8,-1./16],[3./16,1./32],[-1./16,1./8]])
    def fields(z):
        result=ci.kinematics_pairs(jnp.asarray(lift),z,jnp.asarray(grad),jnp.asarray(hessian),jnp)
        return tuple(ci.dd_value(result[name],jnp) for name in ("F","Hu"))
    _,(dF,dHu)=jax.jvp(fields,(jnp.asarray(w),),(jnp.asarray(direction),))
    # Derivatives are exactly these dyadic finite sums, independent of lift.
    expectedF=np.array([[[sum(direction[a,i]*grad[q,a,j] for a in range(4)) for j in range(2)] for i in range(2)] for q in range(9)])
    expectedHu=np.array([[[sum(direction[a,i]*hessian[a,j,k] for a in range(4)) for k in range(2)] for j in range(2)] for i in range(2)])
    np.testing.assert_array_equal(dF,expectedF)
    np.testing.assert_array_equal(dHu,expectedHu)
    assert expectedHu[0,0,1]!=0 and expectedHu[0,1,0]!=0


def test_executable_range_and_domain_rejection_do_not_clip():
    assert bool(ci.operand_domain(0.,ci.OPERAND_MIN,ci.OPERAND_MAX,xp=np))
    for value in (2.**-401,2.**401,np.nan,np.inf):
        assert not bool(ci.operand_domain(value,xp=np))
        assert not bool(ci.pair_supported(ci.dd_from(value,np),np))
    assert not bool(ci.pair_supported((np.asarray(1.),np.asarray(.5)),np))
    operations=(ci.dd_div(ci.dd_const(1.,np),ci.dd_const(0.,np),np),
                ci.dd_log(ci.dd_const(-1.,np),np),
                ci.dd_log1p(ci.dd_const(-1.,np),np),
                ci.dd_exp(ci.dd_const(257.,np),np),
                ci.dd_product(2.**400,2.**400,np),
                ci.dd_product(2.**-400,2.**-400,np))
    for value in operations:
        assert not bool(ci.pair_supported(value,np))
        assert np.isnan(np.asarray(value[0])).all() and np.isnan(np.asarray(value[1])).all()
    lift,w,grad,hessian=synthetic_inputs()
    with pytest.raises(ValueError):
        ci.kinematics_pairs(lift,w,grad[:8],hessian,np)
