"""Independent assembly, path and failure verification for the limited TMC API."""
import os
os.environ['JAX_ENABLE_X64'] = 'true'
os.environ['JAX_PLATFORMS'] = 'cpu'

import numpy as np
import pytest

from hf_eval.tmc import rectangular_model, assemble, solve_path, NewtonSettings, TMCError
from hf_eval.tmc_benchmark import cshape_preset


def small_model(**kwargs):
    return rectangular_model(2,1,2,1,fixed_dofs=[0,1,6,7],**kwargs)


def load_for(model, magnitude=.1):
    force=np.zeros(model.ndof)
    force[[5,11]]=-magnitude
    return force


def test_cshape_frozen_setup():
    model,force,targets,loaded,config=cshape_preset()
    assert model.ne==1860 and model.ndof==3906
    assert model.solid.sum()==828
    assert len(model.fixed_dofs)==62
    np.testing.assert_allclose(force.reshape(-1,2).sum(axis=0),[0,-3],rtol=0,atol=1e-15)
    np.testing.assert_allclose(model.coordinates[loaded,1],50,rtol=0,atol=0)
    np.testing.assert_allclose(model.coordinates[loaded,0],np.arange(55,61)*100/62,rtol=0,atol=2e-14)
    assert config['units_mode']=='source_numeric' and config['thickness_factor']==1
    assert targets[0]==.01 and targets[-1]==1 and len(targets)==100


def test_all_nodes_including_medium_are_retained_and_affine_equilibrium():
    model=small_model(factors=[1,1e-6],solid=[1,0])
    assert model.ndof==12 and len(np.unique(model.edofs))==12
    x,y=model.coordinates.T
    u=np.column_stack((.03*x+.02*y,-.01*x+.01*y)).ravel()
    K,r,fields=assemble(model,u)
    assert K.shape==(12,12) and fields['J'].shape==(2,9)
    np.testing.assert_allclose(r.reshape(-1,2).sum(axis=0),0,atol=1e-13)
    moment=np.sum(model.coordinates[:,0]*r[1::2]-model.coordinates[:,1]*r[0::2])
    # Force balance holds; angular balance uses deformed positions under finite strain.
    current=model.coordinates+u.reshape(-1,2)
    current_moment=np.sum(current[:,0]*r[1::2]-current[:,1]*r[0::2])
    assert abs(current_moment)<1e-12


def test_low_load_path_equilibrium_and_A_B_A_state_independence():
    model=small_model()
    force=load_for(model)
    a=solve_path(model,force,[.01,.02])
    b=solve_path(model,force*2,[.02])
    again=solve_path(model,force,[.01,.02])
    assert a['status']==b['status']==again['status']=='success'
    np.testing.assert_array_equal(a['u'],again['u'])
    assert not np.array_equal(a['u'],b['u'])
    for step in a['accepted_steps']:
        assert step['relative_residual']<=1e-8 and step['minimum_J']>0
        np.testing.assert_array_equal(step['u'][model.fixed_dofs],0)
        np.testing.assert_allclose(step['global_force_balance'],0,atol=1e-10)


def test_failed_later_target_keeps_verified_state_and_null_target():
    model=small_model()
    result=solve_path(model,load_for(model),[.01,1000.0],
                      NewtonSettings(max_checks=4,max_backtracks=2,max_bisections=0))
    assert result['status']=='failed' and result['target_metrics'] is None
    assert result['reached_lambda']==.01
    assert result['failed_attempts'][-1]['rollback_bitwise_equal']
    np.testing.assert_array_equal(result['u'],result['accepted_steps'][-1]['u'])
    assert len(result['accepted_steps'])==1


def test_zero_load_is_explicit_equilibrium_and_missing_support_is_failure():
    model=small_model()
    zero=solve_path(model,np.zeros(model.ndof),[0,.01,1])
    assert zero['status']=='success'
    np.testing.assert_array_equal(zero['u'],0)
    unconstrained=rectangular_model(2,1,2,1)
    failed=solve_path(unconstrained,load_for(unconstrained),[1])
    assert failed['status']=='failed'
    assert failed['failure']['code']=='insufficient_support'
    assert failed['target_metrics'] is None


def test_callback_cannot_modify_accepted_start_state():
    model=small_model()
    ordinary=solve_path(model,load_for(model),[.01,.02])
    def malicious_callback(record):
        record['u'][:]=100
        record['J'][:]=-1
    callback=solve_path(model,load_for(model),[.01,.02],on_accept=malicious_callback)
    np.testing.assert_array_equal(callback['u'],ordinary['u'])
    assert np.all(callback['accepted_steps'][0]['J']>0)


@pytest.mark.parametrize('name,value',[('max_checks',25.0),('max_backtracks',1.0),('max_bisections',False),('tolerance',float('nan'))])
def test_invalid_settings_rejected(name,value):
    with pytest.raises(TMCError):
        NewtonSettings(**{name:value})


def test_complex_displacement_and_inverted_connectivity_rejected():
    model=small_model()
    with pytest.raises(TMCError):
        assemble(model,np.zeros(model.ndof,dtype=complex)+1j)
    with pytest.raises(TMCError):
        rectangular_model(2,1,2,1,factors=1+1j)
