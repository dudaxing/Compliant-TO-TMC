"""Analytic HF-2 element checks; tolerances frozen before the first kernel run."""

import jax
import numpy as np
import pytest

from hf_eval.linear import element_stiffness
from hf_eval import tmc_kernel as kernel


@pytest.fixture(autouse=True)
def explicit_float64_cpu_runtime():
    # Local context, restored after each test. The test launcher selects CPU.
    assert jax.default_backend() == "cpu"
    with jax.enable_x64(True):
        yield


def _xy(hx, hy):
    return np.array([[0., 0.], [hx, 0.], [hx, hy], [0., hy]])


def _parameters(hx, factor=1.):
    E, nu, alpha = 100., .3, 1e-6
    lam = E*nu/((1+nu)*(1-2*nu))
    mu = E/(2*(1+nu))
    bulk = E/(3*(1-2*nu))
    return lam*factor, mu*factor, alpha*hx**2*(bulk+4*mu/3)


def _nonaffine(hx, hy):
    x, y = _xy(hx, hy).T
    return np.column_stack((-.15*x+.08*x*y, .04*x-.20*y+.06*x*y)).ravel()


@pytest.mark.parametrize("hx,hy", [(2., 1.), (.6, 3.1)])
def test_lobatto_order_moments_gradients_and_mixed_hessian(hx, hy):
    t = .7
    ops = kernel.operators(hx, hy, t)
    points = np.array([[-1,-1],[-1,0],[-1,1],[0,-1],[0,0],[0,1],[1,-1],[1,0],[1,1]])
    np.testing.assert_array_equal(ops["points"], points)
    volume = hx*hy*t
    assert abs(ops["weights"].sum()-volume) <= 1e-12*volume
    xi, eta = points.T
    for values, expected in [(xi,0.),(eta,0.),(xi*eta,0.),(xi**2,1/3),(eta**2,1/3)]:
        assert abs(ops["weights"]@values-volume*expected) <= 1e-12*volume
    assert np.linalg.norm(ops["grad"].sum(axis=1)) <= 1e-12/np.sqrt(hx*hy)
    np.testing.assert_array_equal(ops["hessian"][:,0,0], np.zeros(4))
    np.testing.assert_array_equal(ops["hessian"][:,1,1], np.zeros(4))
    np.testing.assert_allclose(ops["hessian"][:,0,1], [1/(hx*hy),-1/(hx*hy),1/(hx*hy),-1/(hx*hy)], rtol=1e-12, atol=0)
    np.testing.assert_array_equal(ops["hessian"][:,0,1],ops["hessian"][:,1,0])
    # Coordinate fields have their exact reference gradients and no Hessian.
    coordinate_gradient=np.einsum("ai,qaj->qij",_xy(hx,hy),ops["grad"])
    np.testing.assert_allclose(coordinate_gradient,np.broadcast_to(np.eye(2),(9,2,2)),rtol=0,atol=1e-12)
    assert np.linalg.norm(np.einsum("ai,ajk->ijk",_xy(hx,hy),ops["hessian"])) <= 1e-12/np.sqrt(hx*hy)
    assert all(value.dtype==np.dtype("float64") for value in ops.values())
    assert all(not value.flags.writeable for value in ops.values())


@pytest.mark.parametrize("hx,hy", [(2.,1.),(.6,3.1)])
@pytest.mark.parametrize("factor", [1.,1e-6])
@pytest.mark.parametrize("motion", ["translation","rotation"])
def test_finite_rigid_motion_has_zero_material_and_regularization(hx,hy,factor,motion):
    lam,mu,kr=_parameters(hx,factor)
    ops=kernel.operators(hx,hy)
    if motion=="translation":
        u=np.tile([.17,-.09],4)
    else:
        theta=.37; R=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        u=(_xy(hx,hy)@(R-np.eye(2)).T).ravel()
    response=kernel.element_response(u,ops,lam,mu,kr)
    hstar=np.sqrt(hx*hy)
    assert np.linalg.norm(response["material_residual"]) <= 1e-10*100*factor*hstar
    assert np.linalg.norm(response["regularization_residual"]) <= 1e-10*kr/hstar
    assert abs(response["material_energy"]) <= 1e-10*100*factor*hx*hy
    np.testing.assert_allclose(response["J"],1.,rtol=0,atol=1e-12)


@pytest.mark.parametrize("hx,hy", [(2.,1.),(.6,3.1)])
@pytest.mark.parametrize("factor", [1.,1e-6])
@pytest.mark.parametrize("F", [np.diag([1.1,.9]),np.array([[1.,.2],[0.,1.]])])
def test_affine_material_stress_energy_and_exact_nodal_tractions(hx,hy,factor,F):
    t=.7; lam,mu,kr=_parameters(hx,factor)
    u=(_xy(hx,hy)@(F-np.eye(2)).T).ravel()
    response=kernel.element_response(u,kernel.operators(hx,hy,t),lam,mu,kr)
    J=np.linalg.det(F); C=F.T@F; inv_C=np.linalg.inv(C)
    expected_S=lam*np.log(J)*inv_C+mu*(np.eye(2)-inv_C)
    P=F@expected_S
    W=.5*lam*np.log(J)**2+.5*mu*(np.trace(C)-2-2*np.log(J))
    E_scale=100*factor
    assert np.linalg.norm(response["stress_second_piola"]-expected_S) <= 1e-10*max(np.linalg.norm(np.broadcast_to(expected_S,(9,2,2))),1e-8*E_scale)
    assert abs(response["material_energy"]-hx*hy*t*W) <= 1e-10*max(abs(hx*hy*t*W),1e-8*E_scale*hx*hy*t)
    # Uniform nominal traction integrated over each node's adjacent edges.
    integrated_grad=np.array([[-hy,-hx],[hy,-hx],[hy,hx],[-hy,hx]])/2
    expected_force=(t*integrated_grad@P.T).ravel()
    assert np.linalg.norm(response["material_residual"]-expected_force) <= 1e-10*max(np.linalg.norm(expected_force),1e-8*E_scale*t*np.sqrt(hx*hy))
    assert np.linalg.norm(response["regularization_residual"]) <= 1e-10*kr*t/np.sqrt(hx*hy)


@pytest.mark.parametrize("hx,hy,t",[(2.,1.,1.),(.6,3.1,.7)])
def test_initial_material_tangent_matches_independent_hf1_linear_element(hx,hy,t):
    lam,mu,_=_parameters(hx)
    response=kernel.element_response(np.zeros(8),kernel.operators(hx,hy,t),lam,mu,0.)
    expected=element_stiffness(100.,.3,hx,hy,t)
    assert np.linalg.norm(response["tangent"]-expected) <= 1e-10*np.linalg.norm(expected)
    assert np.linalg.norm(response["tangent"]-response["tangent"].T) <= 1e-10*np.linalg.norm(expected)


@pytest.mark.parametrize("hx,hy,factor",[(2.,1.,1.),(2.,1.,1e-6),(.6,3.1,1.),(.6,3.1,1e-6)])
def test_actual_residual_directional_derivative_has_predefined_step_convergence(hx,hy,factor):
    ops=kernel.operators(hx,hy); lam,mu,kr=_parameters(hx,factor)
    u=_nonaffine(hx,hy)
    direction=np.sin(np.arange(1,9)) if hx==2. else np.cos(np.arange(1,9))
    direction=np.sqrt(hx*hy)*direction/np.linalg.norm(direction)
    response=kernel.element_response(u,ops,lam,mu,kr)
    exact=response["tangent"]@direction
    errors=[]
    for h in (1e-2,1e-3,1e-4,1e-5,1e-6):
        plus=u+h*direction; minus=u-h*direction
        assert min(kernel.determinants(plus,ops).min(),kernel.determinants(minus,ops).min()) >= .4
        rp=kernel.element_response(plus,ops,lam,mu,kr,tangent=False)["residual"]
        rm=kernel.element_response(minus,ops,lam,mu,kr,tangent=False)["residual"]
        scale=100*factor*np.sqrt(hx*hy)+kr/np.sqrt(hx*hy)
        errors.append(np.linalg.norm((rp-rm)/(2*h)-exact)/max(np.linalg.norm(exact),1e-8*scale))
    assert min(errors) <= 1e-6
    if errors[0] > 1e-9:
        assert errors[0]/errors[1] >= 20


def test_huhu_jacobian_matches_weak_derivative_and_is_not_symmetric():
    hx,hy=2.,1.; ops=kernel.operators(hx,hy); u=_nonaffine(hx,hy)
    _,_,kr=_parameters(hx)
    response=kernel.element_response(u,ops,0.,0.,kr)
    A=np.kron(np.einsum("ajk,bjk->ab",ops["hessian"],ops["hessian"]),np.eye(2))
    expected=np.zeros((8,8))
    for q,F in enumerate(response["F"]):
        J=response["J"][q]
        dJ=J*np.einsum("ij,aj->ai",np.linalg.inv(F).T,ops["grad"][q]).ravel()
        expected+=ops["weights"][q]*kr*np.exp(-5*J)*(A-5*np.outer(A@u,dJ))
    assert np.linalg.norm(response["tangent"]-expected) <= 1e-10*np.linalg.norm(expected)
    assert np.linalg.norm(expected-expected.T)/np.linalg.norm(expected) > 1e-3
    # The regularization remains when both interpolated material moduli are zero.
    np.testing.assert_array_equal(response["material_residual"],np.zeros(8))
    assert np.linalg.norm(response["regularization_residual"]) > 0
    material_case=kernel.element_response(u,ops,*_parameters(hx,1e-6))
    np.testing.assert_allclose(material_case["regularization_residual"],response["regularization_residual"],rtol=1e-12,atol=0)


def test_batch_singleton_mixed_material_and_no_tangent_consistency():
    ops=kernel.operators(2.,1.)
    ue=np.stack((np.zeros(8),_nonaffine(2.,1.),.5*_nonaffine(2.,1.)))
    lam,mu,kr=_parameters(2.)
    factors=np.array([1.,1e-6,1.])
    batch=kernel.batch_response(ue,ops,lam*factors,mu*factors,kr)
    residual_only=kernel.batch_response(ue,ops,lam*factors,mu*factors,kr,tangent=False)
    assert "tangent" not in residual_only
    for index in range(3):
        single=kernel.element_response(ue[index],ops,lam*factors[index],mu*factors[index],kr)
        for name in single:
            np.testing.assert_allclose(batch[name][index],single[name],rtol=1e-12,atol=1e-14)
    for name in residual_only:
        np.testing.assert_allclose(batch[name],residual_only[name],rtol=1e-12,atol=1e-14)
        assert residual_only[name].dtype==np.dtype("float64")
    one=kernel.batch_response(ue[:1],ops,lam,mu,kr)
    assert one["tangent"].shape==(1,8,8)
    assert one["material_energy"].shape==(1,)


def test_thickness_multiplies_integrated_quantities_once():
    u=_nonaffine(2.,1.); pars=_parameters(2.,1e-6)
    a=kernel.element_response(u,kernel.operators(2.,1.,1.),*pars)
    b=kernel.element_response(u,kernel.operators(2.,1.,3.2),*pars)
    for name in ("residual","tangent","material_residual","regularization_residual","material_energy"):
        np.testing.assert_allclose(b[name],3.2*a[name],rtol=1e-12,atol=1e-18)
    for name in ("J","F","stress_second_piola"):
        np.testing.assert_array_equal(a[name],b[name])


@pytest.mark.parametrize("F",[np.diag([-1.,1.]),np.diag([0.,1.])])
def test_invalid_J_rejected_before_differentiable_function(monkeypatch,F):
    ops=kernel.operators(2.,1.)
    u=(_xy(2.,1.)@(F-np.eye(2)).T).ravel()
    assert np.all(kernel.determinants(u,ops) <= 0)
    def must_not_run(*args,**kwargs):
        raise AssertionError("The log/inverse kernel was called for invalid J")
    monkeypatch.setattr(kernel,"_batch_with_tangent",must_not_run)
    monkeypatch.setattr(kernel,"_batch_without_tangent",must_not_run)
    for tangent in (True,False):
        with pytest.raises(kernel.KernelError) as caught:
            kernel.element_response(u,ops,*_parameters(2.),tangent=tangent)
        assert caught.value.code=="invalid_J"


def test_nonfinite_inputs_and_bad_shapes_rejected():
    ops=kernel.operators(2.,1.)
    with pytest.raises(kernel.KernelError) as caught:
        kernel.determinants(np.full(8,np.nan),ops)
    assert caught.value.code=="nonfinite"
    with pytest.raises(kernel.KernelError,match="shape"):
        kernel.batch_response(np.zeros(8),ops,*_parameters(2.))
    with pytest.raises(kernel.KernelError):
        kernel.element_response(np.zeros(8),ops,float("inf"),1.,0.)
    with pytest.raises(kernel.KernelError):
        kernel.operators(0.,1.)


def test_disabled_float64_is_an_error_not_a_silent_precision_change():
    ops=kernel.operators(2.,1.)
    with jax.enable_x64(False):
        with pytest.raises(kernel.KernelError) as caught:
            kernel.element_response(np.zeros(8),ops,*_parameters(2.))
    assert caught.value.code=="runtime_configuration"
