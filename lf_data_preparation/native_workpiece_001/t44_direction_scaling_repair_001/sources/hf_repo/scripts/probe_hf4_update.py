"""One fixed-candidate correction/ULP diagnostic, no new nonlinear path."""
from pathlib import Path
import argparse
from decimal import Decimal, localcontext
import os,sys
os.environ.setdefault('JAX_ENABLE_X64','true');os.environ.setdefault('JAX_PLATFORMS','cpu')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import jax
jax.config.update('jax_enable_x64',True)
from scipy.sparse.linalg import splu
from hf_eval.normal_contact import build_normal_contact,normal_task_from_spec
from hf_eval.tmc import assemble
from hf4_common import read_json,read_npz,write_json,write_npz,sha
from hf4_precision_reference import evaluate_prescribed_state


def main(specpath,source,output):
    output.mkdir(parents=True,exist_ok=False)
    spec=read_json(specpath)
    p=build_normal_contact(normal_task_from_spec(spec,spec['gammas'][1],spec['mesh_sizes_mm'][1]))
    m=p.model;u=read_npz(source)['u']
    K,f,values=assemble(m,u,tangent=True)
    matrix=K[m.free][:,m.free]
    delta=np.zeros(m.ndof);delta[m.free]=splu(matrix).solve(-f[m.free])
    fixture=dict(**m.ops,lam=m.lam,mu=m.mu,kr=np.array(m.kr),connectivity=m.connectivity,fixed_dofs=m.fixed_dofs,solid=m.solid)
    hp=evaluate_prescribed_state(fixture,u,.125,p.base,p.direction,p.reaction_groups,1.,precision=50)
    lower_nodes=np.flatnonzero(m.coordinates[:,1]<=1)
    lower_free=np.intersect1d(2*lower_nodes+1,m.free)
    rows=[]
    for alpha in (1.,.5,.0625,2**-16):
        trial=u+alpha*delta
        _,tf,_=assemble(m,trial,tangent=False)
        thp=evaluate_prescribed_state(fixture,trial,.125,p.base,p.direction,p.reaction_groups,1.,precision=50)
        with localcontext() as ctx:
            ctx.prec=80
            D=lambda x:Decimal.from_float(float(x))
            lost=[abs(D(trial[i])-D(u[i])-D(alpha)*D(delta[i])) for i in m.free]
        ratios=np.abs(alpha*delta[lower_free])/np.abs(np.spacing(u[lower_free]))
        row=dict(alpha=alpha,changed_free=int(np.count_nonzero(trial[m.free]!=u[m.free])),free_count=len(m.free),
                 changed_lower_free=int(np.count_nonzero(trial[lower_free]!=u[lower_free])),lower_free_count=len(lower_free),
                 lower_update_ulp_min=float(ratios.min()),lower_update_ulp_max=float(ratios.max()),lower_update_ulp_median=float(np.median(ratios)),
                 max_update_rounding_loss_mm=str(max(lost)),
                 hp_relative_residual=str(thp['relative_residual_decimal']),
                 production_merit_fixed_scale=float(.5*np.dot(tf[m.free],tf[m.free])/float(hp['force_scale_decimal'])**2))
        rows.append(row)
        write_npz(output/f'trial_{len(rows):02d}.npz',u=trial,internal_force=tf)
        write_json(output/f'trial_{len(rows):02d}_hp.json',thp)
    write_npz(output/'fixed_correction.npz',u=u,delta=delta,internal_force=f,lower_free=lower_free)
    linear_residual=np.linalg.norm(matrix@delta[m.free]+f[m.free])
    write_json(output/'summary.json',dict(status='diagnostic_complete',input_sha256=sha(source),spec_sha256=sha(specpath),
        base_hp_relative_residual=str(hp['relative_residual_decimal']),linear_relative_residual=float(linear_residual/np.linalg.norm(f[m.free])),
        rows=rows,scope='single saved Newton candidate; does not prove impossibility of every binary64 state'))
    print(rows,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--spec',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.spec,a.source,a.output)
