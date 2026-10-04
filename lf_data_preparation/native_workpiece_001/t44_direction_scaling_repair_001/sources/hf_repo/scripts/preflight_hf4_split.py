"""Frozen HF4 split-state representation/force checks; never solves an FE path.

Uniform fixtures come from an independent scalar reference, only for fixed
state evaluation. No fixture produced here is a production initial guess.
Production imports occur only inside run(), so data builders are ordinary
NumPy/Decimal utilities. All outputs require a new directory.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
from pathlib import Path
import sys

import numpy as np

from hf4_common import read_json, read_npz, write_json, write_npz, sha, source_record, timestamp
from hf4_normal_reference import evaluate_normal_reference
from hf4_split_precision_reference import evaluate_split_prescribed_state


def D(value):
    return Decimal.from_float(float(value))


def norm(values):
    return sum((x*x for x in values), Decimal(0)).sqrt()


def flatten(values):
    if isinstance(values, (list, tuple)):
        return [item for part in values for item in flatten(part)]
    return [values]


def tabulated_model(nx, ny, h, physics, factors=None, fixed=None):
    """Independent canonical mesh and signed Q1/Lobatto tabulation."""
    coordinates = np.array([[i*h, j*h] for j in range(ny+1) for i in range(nx+1)])
    conn = np.array([[j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i]
                     for j in range(ny) for i in range(nx)])
    signs = ((-1,-1),(1,-1),(1,1),(-1,1))
    grad, points, weights = [], [], []
    thickness = float(physics["geometry"]["thickness_mm"])
    for xi, wx in ((-1.,1),(0.,4),(1.,1)):
        for eta, wy in ((-1.,1),(0.,4),(1.,1)):
            points.append([xi,eta])
            grad.append([[sx*(1+sy*eta)/(2*h),sy*(1+sx*xi)/(2*h)] for sx,sy in signs])
            weights.append(wx*wy*h*h*thickness/36)
    H = np.zeros((4,2,2))
    for i,(sx,sy) in enumerate(signs):
        H[i,0,1] = H[i,1,0] = sx*sy/(h*h)
    E, nu = physics["material"]["E_MPa"], physics["material"]["nu"]
    lam, mu = E*nu/((1+nu)*(1-2*nu)), E/(2*(1+nu))
    factors = np.ones(nx*ny) if factors is None else np.asarray(factors,dtype=float)
    reg = physics["regularization"]
    kr = reg["alpha"]*reg["length_mm"]**2*(E/(3*(1-2*nu))+4*mu/3)
    return dict(coordinates=coordinates,connectivity=conn,grad=np.array(grad),hessian=H,
        points=np.array(points),weights=np.array(weights),lam=lam*factors,mu=mu*factors,
        kr=np.array(kr),hx=np.array(h),hy=np.array(h),thickness=np.array(thickness),
        solid=factors==1.,fixed_dofs=np.array(range(2*(nx+1)) if fixed is None else fixed,dtype=np.int64))


def nonuniform_cases(physics):
    m=tabulated_model(2,2,.5,physics,[1,1e-7,1e-7,1])
    x,y=m["coordinates"].T
    L=np.column_stack((2.**-5*x*y,1/8+2.**-6*x*y)).ravel()
    w=np.column_stack((-(1-2.**-10)*2.**-5*x*y+2.**-12*x+2.**-13*y,
                       -(1-2.**-10)*2.**-6*x*y-2.**-12*y+2.**-14*x)).ravel()
    q=np.column_stack((2.**-4*x*y,-2.**-5*x*y)).ravel()
    v1=np.column_stack((2.**-7*x*y,-2.**-8*y*(1+x))).ravel()
    v2=np.column_stack((2.**-8*y*(1-x),2.**-7*x*y)).ravel()
    direction=np.zeros(len(L));direction[[1,3,5]]=1
    base=np.zeros(len(L));base[m["fixed_dofs"]]=(L+w-.125*direction)[m["fixed_dofs"]]
    groups={"bottom_y":direction.copy()}
    common=dict(model=m,d=.125,base=base,direction=direction,groups=groups,
                directions={"v1":v1,"v2":v2},equilibrium_required=False,
                fixture_role="nonuniform manufactured evaluation; not a solved state")
    return [dict(common,case_id="nonuniform",lift=L,fluctuation=w),
            dict(common,case_id="nonuniform_equivalent",lift=L+q,fluctuation=w-q)]


def tiny_case(physics):
    m=tabulated_model(1,1,1.,physics,fixed=[0,1,3])
    x,y=m["coordinates"].T
    L=np.full(2*len(x),.125)
    w=np.column_stack((2.**-60*x,-2.**-60*y)).ravel()
    base=np.zeros(len(L));base[m["fixed_dofs"]]=.125
    direction=np.zeros(len(L));direction[[1,3]]=1
    return dict(case_id="sub_ulp_fluctuation",model=m,lift=L,fluctuation=w,d=0.,base=base,
        direction=direction,groups={"bottom_y":direction.copy()},directions={},equilibrium_required=False,
        fixture_role="display-collapse diagnostic; not a solved state")


def uniform_cases(m, meta):
    """Subtract the actual geometric lift in Decimal, then round w just once."""
    dimensions=meta["task"]["geometry"]
    H1=dimensions["lower_height_mm"]; gap=dimensions["gap_mm"]
    H2=dimensions["upper_height_mm"]
    shape=np.zeros(len(m["base"]))
    for node,(_,y) in enumerate(m["coordinates"]):
        shape[2*node+1]=1. if y<=H1 else 0. if y>=H1+gap else (H1+gap-y)/gap
    groups={key[6:]:value for key,value in m.items() if key.startswith("group_")}
    cases=[]
    for d in (.125,.25,.375):
        scalar=evaluate_normal_reference(**meta["reference_inputs"],d=d,precision=80)
        L=m["base"]+d*shape
        with localcontext() as context:
            context.prec=100
            ss=Decimal(scalar["finite_gamma"]["s_s"])
            sv=Decimal(scalar["finite_gamma"]["s_v"])
            exact=[]
            for _,y64 in m["coordinates"]:
                y=D(y64)
                if y<=D(H1): value=D(d)+(ss-1)*y
                elif y<=D(H1)+D(gap): value=D(d)+(ss-1)*D(H1)+(sv-1)*(y-D(H1))
                else: value=(1-ss)*(D(H1)+D(gap)+D(H2)-y)
                exact.extend([Decimal(0),value])
            w=np.array([float(value-D(a)) for value,a in zip(exact,L)])
        cases.append(dict(case_id=f"uniform_d_{d:.3f}",model=m,lift=L,fluctuation=w,d=d,
            base=m["base"],direction=m["direction"],groups=groups,directions={},
            equilibrium_required=False,scalar_reference=scalar,ideal_reference_displacement=exact,
            fixture_role="independent scalar fixed-state fixture; prohibited as production initial guess"))
    return cases


def array_record(value):
    import hashlib
    value=np.ascontiguousarray(value)
    return dict(shape=list(value.shape),dtype=value.dtype.str,sha256=hashlib.sha256(value.tobytes()).hexdigest())


def run(output, physics_path, implementation_path, freeze_path, source_run):
    # Explicitly opt into the new production interface only when run is called.
    import os
    os.environ.setdefault("JAX_ENABLE_X64","true");os.environ.setdefault("JAX_PLATFORMS","cpu")
    repo=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(repo/"src"))
    import jax
    jax.config.update("jax_enable_x64",True)
    from hf_eval.tmc import TMCModel
    from hf_eval.split_state import SplitDisplacement
    from hf_eval.split_kernel import assemble_split,batch_response_split
    from hf4_input_audit import validate_inputs

    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    physics=read_json(physics_path);freeze=read_json(freeze_path)
    if sha(physics_path)!=freeze["physics_spec_sha256"] or sha(implementation_path)!=freeze["implementation_spec_sha256"] or not freeze["stage1_allowed"]:
        raise ValueError("Stage1 specification/freeze binding failed")
    source_run=Path(source_run).resolve()
    m=read_npz(source_run/"model.npz");meta=read_json(source_run/"metadata.json")
    if meta["gamma_index"]!=1 or meta["mesh_index"]!=1:
        raise ValueError("uniform fixtures require the frozen g1/m1 source model")
    input_audit=validate_inputs(physics,meta,m)
    paths=[Path(physics_path),Path(implementation_path),Path(freeze_path),source_run/"model.npz",source_run/"metadata.json"]
    bindings={str(path.resolve()):sha(path) for path in paths}
    write_json(output/"bindings.json",dict(files=bindings,source_files=source_record(),input_audit=input_audit,
        scope="fixed states only; no FE solve, no initial-guess export"))
    cases=uniform_cases(m,meta)+nonuniform_cases(physics)+[tiny_case(physics)]
    rows=[];saved_hp={};saved_production={}
    E=float(physics["material"]["E_MPa"]);t=float(physics["geometry"]["thickness_mm"])
    for case in cases:
        directory=output/case["case_id"];directory.mkdir()
        mm=case["model"];L=case["lift"];w=case["fluctuation"]
        arrays=dict(mm,u_lift=L,u_fluctuation=w,base=case["base"],direction=case["direction"],d=np.array(case["d"]),
            **{"group_"+key:value for key,value in case["groups"].items()},
            **{"tangent_"+key:value for key,value in case["directions"].items()})
        write_npz(directory/"inputs.npz",**arrays)
        write_json(directory/"inputs.json",dict(case_id=case["case_id"],fixture_role=case["fixture_role"],
            equilibrium_required=False,arrays={key:array_record(value) for key,value in arrays.items()},
            npz_sha256=sha(directory/"inputs.npz"),scalar_reference=case.get("scalar_reference"),
            ideal_reference_displacement=case.get("ideal_reference_displacement")))
        checks=[]
        def check(name,value,bound):
            value=Decimal(value);bound=Decimal(bound)
            checks.append(dict(name=name,value=str(value),bound=str(bound),status="pass" if value<=bound else "not_pass"))
        def vector_error(name,actual,reference,scale,indices=None,bound="1e-9"):
            actual=np.asarray(actual)
            if actual.shape!=(len(reference),) or not np.all(np.isfinite(actual)):
                raise ValueError(name+" has invalid vector shape or nonfinite values")
            selected=range(len(reference)) if indices is None else indices
            check(name,norm([D(actual[i])-reference[i] for i in selected])/scale,bound)
        try:
            kwargs=dict(fixture=mm,u_lift=L,u_fluctuation=w,d=case["d"],base=case["base"],
                direction=case["direction"],reaction_groups=case["groups"],force_scale_per_length=E*t)
            hp=evaluate_split_prescribed_state(**kwargs,precision=50)
            hp80=evaluate_split_prescribed_state(**kwargs,precision=80)
            write_json(directory/"hp50.json",hp);write_json(directory/"hp80.json",hp80)
            model=TMCModel(mm["coordinates"],mm["connectivity"],mm["lam"],mm["mu"],float(mm["kr"]),
                float(mm["hx"]),float(mm["hy"]),float(mm["thickness"]),mm["solid"],mm["fixed_dofs"])
            if any(not np.array_equal(model.ops[key],mm[key]) for key in model.ops):
                raise ValueError("production operator preparation differs from archived actual primitives")
            state=SplitDisplacement(L,w)
            prod_modes={}
            with localcontext() as context:
                context.prec=100
                sf=hp["force_scale_decimal"]
                floor_reg=Decimal("1e-12")*D(E)*D(t)*max(abs(D(case["d"])),Decimal("1e-6"))
                for label,indices in (("all",np.arange(model.ndof)),("free",model.free)):
                    check("cross50_80_force_"+label,norm([hp["internal_decimal"][i]-hp80["internal_decimal"][i] for i in indices])/sf,"1e-30")
                check("positive_J",0 if hp["positive_J"] else 1,0)
                for mode in (True,False):
                    K,f,fields=assemble_split(model,state,tangent=mode)
                    tag="tangent" if mode else "force_only"
                    material=np.bincount(model.edofs.ravel(),weights=fields["material_residual"].ravel(),minlength=model.ndof)
                    reg=np.bincount(model.edofs.ravel(),weights=fields["regularization_residual"].ravel(),minlength=model.ndof)
                    prod_modes[tag]=dict(internal=f,material=material,regularization=reg,J=fields["J"],G=fields["G"],F=fields["F"],Hu=fields["Hu"])
                    write_npz(directory/(tag+".npz"),**prod_modes[tag],material_energy=fields["material_energy"])
                    for label,indices in (("all",np.arange(model.ndof)),("free",model.free)):
                        for field,reference in ((f,hp["internal_decimal"]),(material,hp["material_internal_decimal"]),(reg,hp["regularization_internal_decimal"])):
                            component="total" if field is f else "material" if field is material else "regularization"
                            vector_error(tag+"_"+component+"_"+label,field,reference,sf,indices)
                        rs=max(norm([hp["regularization_internal_decimal"][i] for i in indices]),floor_reg)
                        vector_error(tag+"_regularization_component_"+label,reg,hp["regularization_internal_decimal"],rs,indices)
                    if fields["J"].shape!=np.asarray(hp["J"]).shape:
                        raise ValueError("J shape mismatch")
                    jref=flatten(hp["J_decimal"])
                    check(tag+"_J",norm([D(a)-b for a,b in zip(fields["J"].ravel(),jref)])/max(norm(jref),Decimal("1e-12")),"1e-9")
                    if mode:
                        tangent_matrix=K
                for direction_name,v in case["directions"].items():
                    hv=evaluate_split_prescribed_state(**kwargs,precision=50,tangent_direction=v)
                    hv80=evaluate_split_prescribed_state(**kwargs,precision=80,tangent_direction=v)
                    write_json(directory/(direction_name+"_hp50.json"),hv)
                    write_json(directory/(direction_name+"_hp80.json"),hv80)
                    action=tangent_matrix@v
                    # Zero material coefficients isolate the actual regularization
                    # Jacobian without subtracting two almost equal tangents.
                    only_reg=batch_response_split(L[model.edofs],w[model.edofs],model.ops,
                        np.zeros(model.ne),np.zeros(model.ne),model.kr,tangent=True)
                    local_action=np.einsum("eij,ej->ei",only_reg["tangent"],v[model.edofs])
                    reg_action=np.bincount(model.edofs.ravel(),weights=local_action.ravel(),minlength=model.ndof)
                    write_npz(directory/(direction_name+"_actions.npz"),direction=v,total=action,regularization=reg_action)
                    action_floor=Decimal("1e-12")*D(E)*D(t)*norm([D(x) for x in v])
                    for label,indices in (("all",np.arange(model.ndof)),("free",model.free)):
                        scale=max(norm([hv["tangent_action_decimal"][i] for i in indices]),action_floor)
                        vector_error(direction_name+"_Jv_"+label,action,hv["tangent_action_decimal"],scale,indices)
                        check(direction_name+"_cross50_80_Jv_"+label,norm([hv["tangent_action_decimal"][i]-hv80["tangent_action_decimal"][i] for i in indices])/scale,"1e-30")
                        rscale=max(norm([hv["regularization_tangent_action_decimal"][i] for i in indices]),action_floor)
                        vector_error(direction_name+"_regularization_Jv_"+label,reg_action,hv["regularization_tangent_action_decimal"],rscale,indices)
                if case["case_id"].startswith("nonuniform"):
                    # Both component Hessians, and the force at total Hu/J,
                    # must be nonzero. This is not an equilibrium assertion.
                    HL=np.einsum("eai,ajk->eijk",L[model.edofs].reshape(-1,4,2),model.ops["hessian"])
                    Hw=np.einsum("eai,ajk->eijk",w[model.edofs].reshape(-1,4,2),model.ops["hessian"])
                    check("nonzero_H_lift",0 if np.any(HL!=0) else 1,0)
                    check("nonzero_H_fluctuation",0 if np.any(Hw!=0) else 1,0)
                    check("nonzero_total_HuHu",0 if any(x!=0 for x in hp["regularization_internal_decimal"]) else 1,0)
                    if case["case_id"]=="nonuniform_equivalent":
                        original=saved_hp["nonuniform"]
                        check("exact_equivalent_physical_sum",0 if hp["physical_displacement_decimal"]==original["physical_displacement_decimal"] else 1,0)
                        for field in ("internal_decimal","material_internal_decimal","regularization_internal_decimal","J_decimal","Hu_decimal"):
                            check("exact_equivalent_HP_"+field,0 if hp[field]==original[field] else 1,0)
                if case["case_id"]=="sub_ulp_fluctuation":
                    check("display_collapses_small_motion",0 if np.array_equal(L+w,L) else 1,0)
                    check("authority_retains_small_motion",0 if hp["physical_displacement_decimal"]!=[D(x) for x in L] else 1,0)
                    check("nonzero_material_force",0 if any(x!=0 for x in hp["material_internal_decimal"]) else 1,0)
            saved_hp[case["case_id"]]=hp;saved_production[case["case_id"]]=prod_modes
            row=dict(case_id=case["case_id"],status="pass" if all(q["status"]=="pass" for q in checks) else "not_pass",checks=checks,
                fixture_role=case["fixture_role"],hp_relative_residual=str(hp["relative_residual_decimal"]),
                equilibrium_gate_applied=False,force_scale=str(hp["force_scale_decimal"]))
        except Exception as error:
            row=dict(case_id=case["case_id"],status="exception",checks=checks,exception_type=type(error).__name__,message=str(error))
        rows.append(row);write_json(directory/"summary.json",row)
        write_json(output/"summary.json",dict(status="incomplete",rows=rows,completed=len(rows)))
        print({"case":case["case_id"],"status":row["status"]},flush=True)
    summary=dict(schema_version="hf4-split-preflight-1.0",created_utc=timestamp(),
        status="pass" if len(rows)==6 and all(row["status"]=="pass" for row in rows) else "not_pass",
        rows=rows,completed=len(rows),bindings=bindings,source_files=source_record(),
        scope="frozen fixed-state evaluation only; no production solution or path acceptance")
    write_json(output/"summary.json",summary)
    return summary


if __name__=="__main__":
    repo=Path(__file__).resolve().parents[1];workspace=repo.parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--spec",type=Path,default=repo/"configs/hf4/validation_spec.json")
    p.add_argument("--implementation-spec",type=Path,default=workspace/"docs/HF4_SPLIT_IMPLEMENTATION_SPEC.md")
    p.add_argument("--freeze",type=Path,default=workspace/"hf4_repair_results/implementation_freeze.json")
    p.add_argument("--source-run",type=Path,default=workspace/"hf4_results/g1_m1_001")
    a=p.parse_args()
    result=run(a.output,a.spec,a.implementation_spec,a.freeze,a.source_run)
    raise SystemExit(0 if result["status"]=="pass" else 2)
