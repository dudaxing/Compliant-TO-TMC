"""Preflight actual project K0 states against independent Decimal arithmetic.

These fixed linear-predictor states are expression diagnostics, not nonlinear
equilibrium solutions. No material, geometry or tolerance is adjusted here.
"""
from pathlib import Path
import argparse, hashlib, json, sys
from decimal import Decimal, localcontext
import numpy as np
from hf_eval.data import load_geometry
from hf_eval.regions import active_nodes, region_nodes, port_vector
from hf_eval.tmc import rectangular_model, assemble, TMCModel
from hf_eval.linear import solve_average_system
from hf2_precision_reference import DecimalQ1Reference, decimal_norm

def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',type=Path);a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=False);rows=[]
 repo=Path(__file__).resolve().parents[1]
 spec=json.loads((repo/'configs/hf3/validation_spec.json').read_text())
 for family in ('inverter','gripper'):
  task=json.loads((repo/f'configs/hf3/{family}_pilot_v1.json').read_text())
  g=load_geometry(a.dataset/f'canonical/{family}/geometry.json');tags=g.metadata['region_tags'];active=active_nodes(g)
  fixed=[]
  for item in task['constraints']:
   n=region_nodes(g,tags[item['tag']]);n=n[active[n]];fixed.extend((2*n[:,None]+item['components']).ravel())
  n=region_nodes(g,task['background_symmetry']);fixed.extend(2*n+1);fixed=np.unique(fixed)
  bi,_,_=port_vector(g,tags['input']);bo,_,_=port_vector(g,tags['output'])
  solid=g.solid.ravel().astype(bool)
  model=rectangular_model(80,40,80,40,E=1,nu=.3,alpha=1e-6,factors=np.where(solid,1.,1e-6),solid=solid,fixed_dofs=fixed,thickness=20)
  if a.baseline:
   with np.load(a.baseline/f'{family}_fixture.npz',allow_pickle=False) as z: fixture={k:z[k] for k in z.files}
   for key in model.ops: assert np.array_equal(model.ops[key],fixture[key])
   for key in ('lam','mu','coordinates','connectivity','fixed_dofs','solid'): assert np.array_equal(getattr(model,key),fixture[key])
   assert model.kr==float(fixture['kr'])
   lin={'u':fixture['K0_u'],'R_in_N':float(fixture['K0_R'])}
  else:
   K,f,fields=assemble(model,np.zeros(model.ndof));lin=solve_average_system(K,bi,1.,fixed,b_out=bo)
   fixture=dict(**model.ops,lam=model.lam,mu=model.mu,kr=np.array(model.kr),connectivity=model.connectivity,
    coordinates=model.coordinates,F0=np.zeros(model.ndof),fixed_dofs=fixed,solid=solid,bin=bi,bout=bo,
    K0_u=lin['u'],K0_R=np.array(lin['R_in_N']))
  np.savez_compressed(a.output/f'{family}_fixture.npz',**fixture)
  hpref=DecimalQ1Reference(fixture,precision=50)
  for d in spec['bridge_amplitudes_mm']:
   u=d*lin['u'];R=d*lin['R_in_N'];_,actual,_=assemble(model,u,tangent=False);hp=hpref.evaluate(u,0)
   with localcontext() as ctx:
    ctx.prec=80; inp=[Decimal.from_float(float(b))*Decimal.from_float(R) for b in bi]
    sf=max(decimal_norm([hp['internal_decimal'][i] for i in model.free],80),decimal_norm([inp[i] for i in model.free],80),Decimal('1e-8')*20*max(Decimal.from_float(d),Decimal('1e-6')))
    delta=[Decimal.from_float(float(x))-y for x,y in zip(actual,hp['internal_decimal'])]
    ef=decimal_norm(delta,80)/sf;er=decimal_norm([delta[i] for i in model.free],80)/sf
   row=dict(case=family,d_mm=d,full_force_error_decimal=str(ef),free_force_error_decimal=str(er),force_scale_decimal=str(sf),
    evaluation_budget=spec['force_evaluation_relative_budget'],evaluation_budget_pass=max(ef,er)<=Decimal(str(spec['force_evaluation_relative_budget'])),
    scope='expression only at K0 predictor; not equilibrium certification')
   rows.append(row);print(json.dumps(row),flush=True)
   np.savez_compressed(a.output/f'{family}_{d:.0e}.npz',u=u,R=np.array(R),production_internal=actual,hp_internal=hp['internal'])
 summary=dict(status='pass' if all(r['evaluation_budget_pass'] for r in rows) else 'expression_budget_not_pass',rows=rows,baseline=None if not a.baseline else str(a.baseline.resolve()),
  kernel_sha256=hashlib.sha256((repo/'src/hf_eval/tmc_kernel.py').read_bytes()).hexdigest(),spec_sha256=hashlib.sha256((repo/'configs/hf3/validation_spec.json').read_bytes()).hexdigest())
 (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 return 0  # A diagnosed expression failure is a completed preflight, preserved above.
if __name__=='__main__':raise SystemExit(main())
