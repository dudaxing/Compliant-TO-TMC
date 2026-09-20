"""Fixed-state arithmetic attribution for the failed C2 fine endpoint; no solve.

Deliberately reads a NOT_PASS endpoint. Every output is diagnostic only and
cannot be substituted for a production state, tangent or mechanical admission.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import math
import os
import sys

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import jax
jax.config.update("jax_enable_x64", True)
import numpy as np

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/"src"))
from hf_eval.contact_c2 import build_problem
from hf_eval.split_state import SplitDisplacement
from hf_eval.split_kernel import assemble_split
from audit_contact_c2 import load_run, bind, require, read_npz
from hf4_split_precision_reference import DecimalSplitQ1Reference
from hf4_common import sha, read_json, write_json, plain

ZERO, ONE=Decimal(0),Decimal(1)
def D(x):return Decimal.from_float(float(x))
def norm(v):return sum((x*x for x in v),ZERO).sqrt()
def sub(a,b):return [x-y for x,y in zip(a,b)]
def flat(value):
    if isinstance(value,(list,tuple,np.ndarray)):
        return [x for row in value for x in flat(row)]
    return [value]


def stress_from_kinematics(model,F,J,Hu,*,precision=120):
    """Independent Decimal constitutive/weak assembly for given kinematics."""
    with localcontext() as ctx:
        ctx.prec=precision
        ndof=len(model["F0"]); mat=[ZERO]*ndof;reg=[ZERO]*ndof
        grad=[[[D(v) for v in row] for row in q] for q in model["grad"]]
        hess=[[[D(v) for v in row] for row in a] for a in model["hessian"]]
        weights=list(map(D,model["weights"]));kr=D(model["kr"])
        for e,conn in enumerate(model["connectivity"]):
            lam,mu=D(model["lam"][e]),D(model["mu"][e])
            for q,w in enumerate(weights):
                f=F[e][q];j=J[e][q]
                require(j>0,"nonpositive prescribed J in arithmetic diagnostic")
                inv=[[f[1][1]/j,-f[1][0]/j],[-f[0][1]/j,f[0][0]/j]]
                c=lam*j.ln()-mu
                p=[[mu*f[i][k]+c*inv[i][k] for k in range(2)] for i in range(2)]
                scale=kr*w*(-5*j).exp()
                for a,n in enumerate(conn):
                    for i in range(2):
                        mat[2*n+i]+=w*sum((p[i][k]*grad[q][a][k] for k in range(2)),ZERO)
                        reg[2*n+i]+=scale*sum((Hu[e][i][j][k]*hess[a][j][k] for j in range(2) for k in range(2)),ZERO)
        return dict(material=mat,regularization=reg,total=[a+b for a,b in zip(mat,reg)])


def rounded(values):
    if isinstance(values,(list,tuple,np.ndarray)):return [rounded(v) for v in values]
    return D(values)


def determinant(F):
    return [[f[0][0]*f[1][1]-f[0][1]*f[1][0] for f in row] for row in F]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run",required=True,type=Path)
    parser.add_argument("--protocol",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args();run=args.run.resolve();out=args.output.resolve()
    require(not out.exists(),"preserve old diagnostic output")
    bindings={};data=load_run(run,args.protocol,bindings)
    require(data["metadata"]["case_id"]=="mesh_h00625","bounded fine-mesh failure only")
    audit_path=run/"audit.json";audit=read_json(audit_path);bind(audit_path,bindings)
    require(audit["status"]=="not_pass","failure must remain NOT_PASS")
    compact=audit["states"][-1]; detail=run/compact["detail_file"]
    bind(detail,bindings,compact["detail_sha256"]);row=read_json(detail)
    require(row["state_id"]=="uniform_tmc:20" and row["parameter_s"]==.5,"unexpected failure identity")
    failed=[c for c in row["checks"] if c["status"]!="pass"]
    require(len(failed)==1 and failed[0]["name"]=="production_vs_hp80_total_force","unexpected failure scope")
    model=data["model"];stage=run/"stages/uniform_tmc"
    entry=read_json(stage/"steps/index.json")["steps"][-1]
    state=read_npz(stage/"steps"/entry["file"])
    for p in (Path(__file__),REPO/"scripts/hf4_split_precision_reference.py",REPO/"scripts/hf2_precision_reference.py"):
        bind(p,bindings)
    out.mkdir(parents=True)
    write_json(out/"plan.json",dict(schema="c2-fixed-failure-arithmetic-plan-v1",created_utc=datetime.now(timezone.utc).isoformat(),
        state_id=row["state_id"],source_status="not_pass",failed_gate=failed[0],
        scope="Same saved state only; no FE, Newton update, retuning, tangent certification, source-state replacement or admission",
        precision=120,rounding_stages=["saved/unchanged JAX tangent=True reproduction",
        "Decimal constitutive and assembly with production F/J/Hu",
        "same with determinant recomputed exactly from production F",
        "same with correctly rounded exact split F; production Hu retained",
        "same correctly rounded F with exact split Hu",
        "exact split independent reference"],
        secondary_observation="math.fsum of identity and eight displacement-gradient products; compare with correctly rounded exact F, not a production repair",
        algebra_limit="1e-60 relative to max(1 N, reference norm)",
        input_sha256_from_workspace_root={str(Path(p).relative_to(REPO.parent).as_posix()):h for p,h in bindings.items()}))
    print("Frozen plan; reproducing the unchanged production evaluation",flush=True)
    problem=build_problem("mesh_h00625")
    _,force,prod=assemble_split(problem.model,SplitDisplacement(state["u_lift"],state["u_fluctuation"]),tangent=True)
    require(np.array_equal(force.view(np.uint64),state["internal_force"].view(np.uint64)),"production force not bitwise reproducible")
    print("Production force bitwise reproduced; reconstructing exact split reference",flush=True)
    hp=DecimalSplitQ1Reference(model,precision=120).evaluate(state["u_lift"],state["u_fluctuation"],derivative=False)
    with localcontext() as ctx:
        ctx.prec=120
        ref=hp["internal_decimal"];sf=Decimal(row["measurements"]["force_scale"])
        saved120=list(map(Decimal,row["precision_evidence_decimal"]["120"]["internal_decimal"]))
        ref_error=norm(sub(ref,saved120))/max(ONE,norm(ref))
        require(ref_error<=Decimal("1e-60"),"reference differs from frozen HP120 evidence")
        pf,pj,ph=rounded(prod["F"]),rounded(prod["J"]),rounded(prod["Hu"])
        exactj=determinant(pf);rf=rounded(hp["F_decimal"]);rj=determinant(rf)
        variants={"saved_production":dict(total=list(map(D,state["internal_force"])),
            material=list(map(D,state["material_internal_force"])),regularization=list(map(D,state["regularization_internal_force"])))}
        experiments=[("decimal_at_production_F_J_Hu",pf,pj,ph),
                     ("decimal_exact_determinant_of_production_F",pf,exactj,ph),
                     ("decimal_at_rounded_exact_F_production_Hu",rf,rj,ph),
                     ("decimal_at_rounded_exact_F_exact_Hu",rf,rj,hp["Hu_decimal"])]
        for name,f,j,h in experiments:
            print(name,flush=True);variants[name]=stress_from_kinematics(model,f,j,h)
        reconstructed=stress_from_kinematics(model,hp["F_decimal"],hp["J_decimal"],hp["Hu_decimal"])
        formula_error=norm(sub(reconstructed["total"],ref))/max(ONE,norm(ref))
        require(formula_error<=Decimal("1e-60"),"kinematics-to-force formula failed independent reference check")
        variants["exact_split_reference"]={k:hp[v] for k,v in (("total","internal_decimal"),("material","material_internal_decimal"),("regularization","regularization_internal_decimal"))}
        metrics={name:{k:dict(absolute_error_N=norm(sub(value[k],variants["exact_split_reference"][k])),
                     error_over_frozen_SF=norm(sub(value[k],variants["exact_split_reference"][k]))/sf) for k in value} for name,value in variants.items()}
        transitions=[];names=list(variants)
        for left,right in zip(names,names[1:]):
            delta=sub(variants[left]["total"],variants[right]["total"])
            transitions.append(dict(left=left,right=right,change_norm_N=norm(delta),change_over_SF=norm(delta)/sf))
        # A diagnostic summation route. Its products are also rounded binary64;
        # exact equality is an observed property of this dyadic Q1 fixture only.
        fs=np.empty_like(prod["F"])
        edofs=problem.model.edofs
        L=state["u_lift"][edofs].reshape(-1,4,2);w=state["u_fluctuation"][edofs].reshape(-1,4,2)
        for e in range(len(L)):
            for q,g in enumerate(model["grad"]):
                for i in range(2):
                    for j in range(2):
                        fs[e,q,i,j]=math.fsum([float(i==j)]+[float(L[e,a,i]*g[a,j]) for a in range(4)]+[float(w[e,a,i]*g[a,j]) for a in range(4)])
        differences=np.abs(prod["F"]-hp["F"])
        maximum=np.unravel_index(np.argmax(differences),differences.shape)
        e,q,i,j=map(int,maximum)
        kine=dict(production_F_max_absolute_difference_from_rounded_reference=str(D(prod["F"][maximum])-hp["F_decimal"][e][q][i][j]),
            maximum_location=list(maximum),reference_element_coordinates=model["coordinates"][model["connectivity"][e]],
            production_F=prod["F"][e,q],exact_split_F=hp["F_decimal"][e][q],production_J=prod["J"][e,q],exact_split_J=hp["J_decimal"][e][q],
            fsum_matches_correctly_rounded_exact_F_all_entries=bool(np.array_equal(fs,hp["F"])),
            differing_production_F_entries=int(np.count_nonzero(prod["F"]!=hp["F"])),
            total_F_entries=int(prod["F"].size),near_identity_point_count=int(np.count_nonzero(np.max(np.abs(prod["G"]),axis=(-1,-2))<=.01)))
        write_json(out/"vectors.json",dict(authority="diagnostic variants at an unchanged failed state; not replacement state or force",variants=variants))
        result=dict(schema="c2-fixed-failure-arithmetic-v1",diagnostic_completed=True,mechanical_admission="not_pass_unchanged",
            plan_sha256=sha(out/"plan.json"),source_failed_gate=failed[0],production_bitwise_reproduced=True,
            independent_reference_relative_reproduction_error=ref_error,force_scale_N=sf,variants=metrics,successive_changes=transitions,kinematics=kine,
            kinematics_to_force_formula_relative_check=formula_error,
            limitations=["Successive vector changes are an arithmetic attribution, not independent stochastic error bars.",
            "Correctly rounded exact F and fsum are diagnostic counterfactuals, not a deployed kernel or consistent tangent.",
            "No new equilibrium path was solved and no failed endpoint was admitted."])
        write_json(out/"summary.json",result)
    require(all(sha(Path(p))==h for p,h in bindings.items()),"source changed during diagnostic")
    write_json(out/"output_sha256.json",{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    print({"diagnostic_completed":True,"mechanical_admission":"not_pass_unchanged","output":str(out)},flush=True)


if __name__=="__main__":main()
