"""Independent Decimal checks of tiny strain and the arithmetic branch seam."""
from pathlib import Path
import sys
from decimal import Decimal, localcontext
import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from hf2_precision_reference import DecimalQ1Reference, decimal_norm
from hf_eval.tmc import rectangular_model, assemble


@pytest.mark.parametrize('amplitude',[1e-9,1e-7,1e-5,.009999999,.010000001,.1])
def test_material_force_energy_and_actual_derivative_against_decimal(amplitude):
    model=rectangular_model(1,1,1,1,E=1,nu=.3,thickness=20)
    G=amplitude*np.array([[1.,.3],[-.2,-.4]])
    u=(model.coordinates@G.T).ravel()
    direction=np.sin(np.arange(model.ndof)+1.)
    fixture=dict(**model.ops,lam=model.lam,mu=model.mu,kr=np.array(model.kr),
                 connectivity=model.connectivity,F0=np.zeros(model.ndof),fixed_dofs=model.fixed_dofs)
    hp=DecimalQ1Reference(fixture,precision=60).evaluate(u,0,direction=direction)
    K,f,fields=assemble(model,u)
    with localcontext() as ctx:
        ctx.prec=80
        err=decimal_norm([Decimal.from_float(float(x))-y for x,y in zip(f,hp['internal_decimal'])],80)
        scale=decimal_norm(hp['internal_decimal'],80)
        assert err/scale < Decimal('1e-11')
        energy=hp['material_energy_decimal'][0]
        assert abs(Decimal.from_float(float(fields['material_energy'][0]))-energy)/abs(energy)<Decimal('1e-10')
        jv=K@direction
        difference=decimal_norm([Decimal.from_float(float(x))-y for x,y in zip(jv,hp['tangent_action_decimal'])],80)
        assert difference/decimal_norm(hp['tangent_action_decimal'],80)<Decimal('1e-10')


def test_tiny_rigid_rotation_has_no_spurious_material_energy_floor():
    model=rectangular_model(1,1,1,1,E=1,nu=.3,thickness=20)
    angle=1e-6
    G=np.array([[-2*np.sin(angle/2)**2,-np.sin(angle)],[np.sin(angle),-2*np.sin(angle/2)**2]])
    u=(model.coordinates@G.T).ravel()
    _,_,fields=assemble(model,u)
    assert abs(fields['material_energy'][0])<1e-29
