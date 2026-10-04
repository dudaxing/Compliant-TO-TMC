"""Bounded fixed-state investigation; observes original production without editing it."""
from pathlib import Path
from dataclasses import replace
from decimal import Decimal, localcontext
import argparse
import os
import sys

os.environ.setdefault("JAX_ENABLE_X64","true")
os.environ.setdefault("JAX_PLATFORMS","cpu")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import numpy as np
import jax
jax.config.update("jax_enable_x64",True)
from hf_eval.normal_contact import build_normal_contact, normal_task_from_spec
import hf_eval.prescribed as prescribed
from hf_eval.tmc import assemble
from hf_eval.tmc_kernel import batch_response
from hf4_common import read_json, write_json, write_npz, source_record, sha
from hf4_normal_reference import evaluate_normal_reference
from hf4_precision_reference import evaluate_prescribed_state


def D(v): return Decimal.from_float(float(v))
def norm(v): return sum((x*x for x in v),Decimal(0)).sqrt()


def main(specpath, output):
    output.mkdir(parents=True,exist_ok=False)
    spec=read_json(specpath)
    p=build_normal_contact(normal_task_from_spec(spec,spec['gammas'][1],spec['mesh_sizes_mm'][1]))
    m=p.model
    fixture=dict(**m.ops,lam=m.lam,mu=m.mu,kr=np.array(m.kr),connectivity=m.connectivity,
                 fixed_dofs=m.fixed_dofs,solid=m.solid)
    candidates=[]
    original=prescribed.assemble
    def observe(model,u,tangent=True):
        K,f,fields=original(model,u,tangent=tangent)
        if tangent:
            i=len(candidates)
            candidates.append((u.copy(),f.copy()))
            write_npz(output/f'candidate_{i:03d}.npz',u=u,internal_force=f,J=fields['J'])
        return K,f,fields
    prescribed.assemble=observe
    settings=replace(prescribed.PrescribedSettings(**spec['solver']),max_bisections=0)
    result=prescribed.solve_prescribed_path(m,p.base,p.direction,[0.,.125],reaction_groups=p.reaction_groups,
                                           settings=settings,force_scale_per_length=1.)
    prescribed.assemble=original
    write_json(output/'observed_result.json',result)
    reference=evaluate_normal_reference(**p.reference_inputs,d=.125,precision=80)
    write_json(output/'reference.json',reference)
    with localcontext() as ctx:
        ctx.prec=80
        ss=Decimal(reference['finite_gamma']['s_s']);sv=Decimal(reference['finite_gamma']['s_v'])
        exact=[]
        for _,y in m.coordinates:
            y=D(y)
            value=D(.125)+(ss-1)*y if y<=1 else D(.125)+(ss-1)+(sv-1)*(y-1) if y<=D(1.25) else (1-ss)*(D(2.25)-y)
            exact.extend([Decimal(0),value])
    rounded=np.array(exact,dtype=float)
    _,force,_=assemble(m,rounded,tangent=False)
    states=[('last_candidate',*candidates[-1]),('rounded_affine_reference',rounded,force)]
    rows=[]
    for name,u,f in states:
        hp=evaluate_prescribed_state(fixture,u,.125,p.base,p.direction,p.reaction_groups,1.,precision=50)
        hp80=evaluate_prescribed_state(fixture,u,.125,p.base,p.direction,p.reaction_groups,1.,precision=80)
        # Local translation subtraction changes neither ideal gradients nor Hu
        # only when the binary64 subtractions preserve their exact differences.
        eu=u[m.edofs].reshape(-1,4,2)
        centered=eu-eu[:,0:1,:]
        fields=batch_response(centered.reshape(-1,8),m.ops,m.lam,m.mu,m.kr,tangent=False)
        cf=np.bincount(m.edofs.ravel(),weights=fields['residual'].ravel(),minlength=m.ndof)
        with localcontext() as ctx:
            ctx.prec=80
            sf=hp['force_scale_decimal']
            errors=[D(x)-y for x,y in zip(f,hp['internal_decimal'])]
            cerrors=[D(x)-y for x,y in zip(cf,hp['internal_decimal'])]
            # Verify exact local translation invariance from original float primitives.
            gdiff=[];hdiff=[]
            for old,new in zip(eu,centered):
                for q in m.ops['grad']:
                    for i in range(2):
                        for j in range(2):
                            gdiff.append(sum(((D(old[a,i])-D(new[a,i]))*D(q[a,j]) for a in range(4)),Decimal(0)))
                for i in range(2):
                    for j in range(2):
                        for k in range(2):
                            hdiff.append(sum(((D(old[a,i])-D(new[a,i]))*D(m.ops['hessian'][a,j,k]) for a in range(4)),Decimal(0)))
            rows.append(dict(name=name,hp_relative_residual=str(hp['relative_residual_decimal']),
                force_scale_N=str(sf),production_evaluation_error_relative=str(norm(errors)/sf),
                production_free_evaluation_error_relative=str(norm([errors[i] for i in m.free])/sf),
                centered_evaluation_error_relative=str(norm(cerrors)/sf),
                centered_free_residual_relative=str(norm([D(cf[i]) for i in m.free])/sf),
                exact_gradient_change_max=str(max(map(abs,gdiff))),exact_Hu_change_max=str(max(map(abs,hdiff))),
                cross50_80_relative=str(norm([a-b for a,b in zip(hp['internal_decimal'],hp80['internal_decimal'])])/sf)))
        write_json(output/(name+'_hp50.json'),hp)
        write_json(output/(name+'_hp80.json'),hp80)
        write_npz(output/(name+'.npz'),u=u,internal_force=f,centered_internal_force=cf)
    write_json(output/'summary.json',dict(status='diagnostic_complete',source_files=source_record(),spec_sha256=sha(specpath),
        original_first_target_reproduced=result['status'],candidate_count=len(candidates),rows=rows,
        scope='diagnostic only; production stopping tolerance unchanged; centered values are not a new solution'))
    print(rows,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();main(a.spec,a.output)
