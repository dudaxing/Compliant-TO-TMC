"""Analytic normal-Piola integration of saved flat Q1 top edges; no FE solve.

The stored material field's edge integral is not the assembled weak reaction,
not a Cauchy pressure sample, and not a unilateral-contact validation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
import json
import sys

import numpy as np

from contact_c2_fields import comparison, dec, point_response, shape_grad
from diagnose_contact_c2_fields import checked_sources, load, serial, sha, write_new


ZERO,ONE=Decimal(0),Decimal(1)


def analytic_moments(a,f0,f1,lam,mu,*,precision):
    """Return integrals of Pyy(t) and t Pyy(t), t in [0,1].

    All operands are Decimal. Work is performed at precisely the declared
    precision, without substituting a high-precision answer. Small slopes use
    the harmonic-number series for log(1+r*t)/(1+r*t); the supplied truncation
    bound is conservative in exact arithmetic, not an interval roundoff bound.
    """
    if precision not in (80,120): raise ValueError("only declared precision pair 80/120")
    if any(not isinstance(v,Decimal) or not v.is_finite() for v in (a,f0,f1,lam,mu)):
        raise ValueError("finite Decimal primitives required")
    if min(a,f0,f1)<=0 or lam<0 or mu<=0:
        raise ValueError("requires positive diagonal stretch/mu and nonnegative lambda")
    with localcontext() as ctx:
        ctx.prec=precision
        b=f1-f0
        L0=(a*f0).ln()
        if b==0:
            P=mu*f0+(lam*L0-mu)/f0
            return dict(A0=P,A1=P/2,method="constant",terms=1,series_tail_bound=ZERO,r=ZERO)
        r=b/f0
        if abs(r)<=Decimal(".25"):
            H,power=ZERO,ONE
            C=lam*L0-mu
            S0,S1=ZERO,ZERO
            rho=abs(r)
            for n in range(4096):
                if n: H+=ONE/n
                coefficient=((ONE if n%2==0 else -ONE)*(C-lam*H)*power)/f0
                S0+=coefficient/(n+1)
                S1+=coefficient/(n+2)
                # H_(n+k) <= H_n + k/(n+1); denominators of the moments
                # can only reduce this upper bound on the omitted terms.
                tail=rho**(n+1)/f0*((abs(C)+lam*H)/(ONE-rho)+lam/((n+1)*(ONE-rho)**2))
                scale=max(ONE,abs(S0),abs(S1),abs(mu*f0))
                if tail<=Decimal(10)**(-(precision-8))*scale:
                    return dict(A0=mu*(f0+b/2)+S0,A1=mu*(f0/2+b/3)+S1,
                                method="harmonic_series",terms=n+1,series_tail_bound=tail,r=r)
                power*=r
            raise ArithmeticError("series failed to meet its predeclared truncation target")
        L1=(a*f1).ln()
        integrated_inverse=(lam*(L0+L1)/2-mu)*(f1/f0).ln()
        return dict(A0=mu*(f0+b/2)+integrated_inverse/b,
                    A1=mu*(f0/2+b/3)+(lam*(f1*(L1-ONE)-f0*(L0-ONE))-mu*b-f0*integrated_inverse)/(b*b),
                    method="closed_form",terms=0,series_tail_bound=ZERO,r=r)


def integrate_saved(model,state,*,precision):
    xy=model["coordinates"]
    top=set(map(int,model["top_nodes"]))
    with localcontext() as ctx:
        ctx.prec=3000
        physical=[dec(l)+dec(w) for l,w in zip(state["u_lift"],state["u_fluctuation"])]
    with localcontext() as ctx:
        ctx.prec=precision
        normal=[ZERO]*len(xy)
        rows=[]
        for e,cnraw in enumerate(model["connectivity"]):
            cn=list(map(int,cnraw))
            if not {cn[2],cn[3]}<=top: continue
            hx,hy=dec(xy[cn[1],0])-dec(xy[cn[0],0]),dec(xy[cn[3],1])-dec(xy[cn[0],1])
            if hx<=0 or hy<=0: raise ValueError("invalid reference rectangle")
            un=[[physical[2*n+i] for i in (0,1)] for n in cn]
            lam,mu=dec(model["lam"][e]),dec(model["mu"][e])
            endpoints=[]
            for xi in (-ONE,ONE):
                _,g=shape_grad(xi,ONE,hx,hy)
                F,J,P=point_response(un,g,lam,mu)
                endpoints.append(dict(F=F,J=J,P=P))
            left,right=endpoints
            if left["F"][1][0]!=0 or right["F"][1][0]!=0 or left["F"][0][0]!=right["F"][0][0]:
                raise ValueError("analytic adapter requires flat top Fyx=0 and constant Fxx")
            a,f0,f1=left["F"][0][0],left["F"][1][1],right["F"][1][1]
            result=analytic_moments(a,f0,f1,lam,mu,precision=precision)
            left_force,right_force=-hx*(result["A0"]-result["A1"]),-hx*result["A1"]
            normal[cn[3]]+=left_force
            normal[cn[2]]+=right_force
            rows.append(dict(element=e,left_node=cn[3],right_node=cn[2],hx_mm=hx,
                             a=a,f0=f0,f1=f1,lam=lam,mu=mu,endpoints=endpoints,
                             moments=result,left_on_plane_N=left_force,right_on_plane_N=right_force))
        return dict(normal_on_plane_N=normal,edges=rows)


def analyze(source,previous):
    results={p:integrate_saved(source["model"],source["state"],precision=p) for p in (80,120)}
    low,high=results[80],results[120]
    checks={"nodal_normal_80_vs_120":comparison(low["normal_on_plane_N"],high["normal_on_plane_N"],unit="N")}
    for key,unit in (("a","dimensionless"),("f0","dimensionless"),("f1","dimensionless"),
                     ("left_on_plane_N","N"),("right_on_plane_N","N")):
        checks[key+"_80_vs_120"]=comparison([e[key] for e in low["edges"]],[e[key] for e in high["edges"]],unit=unit)
    for key in ("A0","A1"):
        checks[key+"_80_vs_120"]=comparison([e["moments"][key] for e in low["edges"]],[e["moments"][key] for e in high["edges"]],unit="N/mm^2")
    old_edges={e["element"]:e for e in previous["all_top_edge_summaries"]}
    for key,unit in (("F","dimensionless"),("P","N/mm^2"),("J","dimensionless")):
        checks[key+"_vs_frozen_field_endpoints"]=comparison([[p[key] for p in e["endpoints"]] for e in high["edges"]],
                    [[_decimalize(p[key]) for p in old_edges[e["element"]]["endpoints"]] for e in high["edges"]],unit=unit)
    with localcontext() as ctx:
        ctx.prec=120
        top=list(map(int,source["model"]["top_nodes"]))
        old={n["node_id"]:n for n in previous["all_top_nodes"]}
        analytic=[high["normal_on_plane_N"][n] for n in top]
        observations={}
        for method in ("simpson3","gauss8","gauss16","gauss32","gauss64"):
            values=[Decimal(old[n]["direct_material_edge_on_plane_N"][method]) for n in top]
            observations[method+"_vs_analytic"]=comparison(values,analytic,unit="N",limit="1e-8")
        nodal=[]
        for n in top:
            force=high["normal_on_plane_N"][n]
            nodal.append(dict(node_id=n,reference_x_mm=float(source["model"]["coordinates"][n,0]),
                analytic_material_edge_on_plane_N=force,weak_total_on_plane_N=old[n]["total_on_plane_N"],
                weak_material_on_plane_N=old[n]["material_weak_on_plane_N"],
                regularization_weak_on_plane_N=old[n]["regularization_weak_on_plane_N"],
                frozen_simpson_on_plane_N=old[n]["direct_material_edge_on_plane_N"]["simpson3"],
                frozen_gauss64_on_plane_N=old[n]["direct_material_edge_on_plane_N"]["gauss64"],
                weak_material_minus_analytic_N=Decimal(old[n]["material_weak_on_plane_N"])-force,
                negative_weak_total=old[n]["negative_total"]))
        aggregate=dict(analytic_net_N=sum(analytic,ZERO),
            analytic_negative_sum_N=sum((v for v in analytic if v<0),ZERO),
            weak_net_N=previous["aggregate"]["total"]["net_N"],
            frozen_gauss64_net_N=previous["aggregate"]["direct_material_edges"]["gauss64"]["net_N"],
            frozen_simpson_net_N=previous["aggregate"]["direct_material_edges"]["simpson3"]["net_N"],
            all_analytic_top_node_values_positive=all(v>0 for v in analytic))
    return dict(run=source["run"],state_id=source["row"]["state_id"],status="pass" if all(c["status"]=="pass" for c in checks.values()) else "not_pass",
        checks=checks,aggregate=aggregate,edge_quadrature_vs_analytic_observations=observations,all_top_nodes=nodal,
        analytic_edges_HP120=high["edges"],method_counts_by_precision={str(p):{method:sum(e["moments"]["method"]==method for e in results[p]["edges"])
          for method in ("constant","harmonic_series","closed_form")} for p in (80,120)})


def _decimalize(value):
    return [_decimalize(v) for v in value] if isinstance(value,list) else Decimal(value)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",default="hf4_c1_results")
    parser.add_argument("--cases")
    parser.add_argument("--fields",default="hf4_c2_diagnostics/fields_001")
    parser.add_argument("--output",default="hf4_c2_diagnostics/analytic_edge_001")
    args=parser.parse_args(argv)
    root,out,fields=Path(args.root).resolve(),Path(args.output).resolve(),Path(args.fields).resolve()
    if out.exists(): raise FileExistsError("refusing to overwrite analytic diagnostic")
    manifest=Path(args.cases).resolve() if args.cases else root/"selection_v1.json"
    sources,bindings=checked_sources(root,manifest)
    field_manifest=fields/"output_sha256.json"
    for name,digest in load(field_manifest).items():
        p=(fields/name).resolve()
        if not p.is_relative_to(fields) or sha(p)!=digest: raise ValueError("frozen field evidence changed: "+name)
        bindings[str(p)]=digest
    bindings[str(field_manifest)]=sha(field_manifest)
    scripts=Path(__file__).parent
    for name in ("diagnose_contact_c2_analytic_edge.py","diagnose_contact_c2_fields.py","contact_c2_fields.py",
                 "contact_c2_sbp.py","hf4_split_precision_reference.py","hf2_precision_reference.py"):
        bindings[str((scripts/name).resolve())]=sha(scripts/name)
    out.mkdir(parents=True)
    plan=dict(schema="contact_c2_analytic_edge_plan_v1",created_utc=datetime.now(timezone.utc).isoformat(),
        cases=[dict(run=s["run"],state_id=s["row"]["state_id"]) for s in sources],precision_pair=[80,120],
        algebra_gate=dict(limit="1e-45",normalization="norm(error)/max(norm(reference),one declared N or MPa or dimensionless unit)"),
        quadrature_observation=dict(limit="1e-8",meaning="comparison with exact saved-Q1-field edge integral; never solver/contact admission"),
        analytic_model="For t in [0,1]: Fyx=0, a=Fxx constant>0, f=Fyy=f0+(f1-f0)t>0, Pyy=mu*f+(lambda*ln(a*f)-mu)/f.",
        formulas=dict(A0="mu*(f0+b/2)+Q/b",A1="mu*(f0/2+b/3)+(lambda*(f1*(L1-1)-f0*(L0-1))-mu*b-f0*Q)/b^2",
                      Q="(lambda*(L0+L1)/2-mu)*ln(f1/f0)",L="ln(a*f)",nodes_on_plane="-hx*(A0-A1), -hx*A1, physical thickness=1 mm"),
        cancellation_policy=dict(constant="b==0",series="abs(b/f0)<=0.25",closed_form="abs(b/f0)>0.25",
            series_coefficients="c_n=(-1)^n*((lambda*L0-mu)-lambda*H_n)*(b/f0)^n/f0; inverse-stress moments sum c_n/(n+1), c_n/(n+2)",
            truncation="conservative exact-arithmetic tail estimate <=10^(-(precision-8))*max(1 MPa, partial-moment magnitudes, abs(mu*f0)); no hidden guard-digit substitution",
            maximum_terms=4096),
        limitations=["No new FE; both precisions independently reconstruct endpoints from exact sums of original binary64 split components.",
            "Analytic means a closed-form/series integral of the saved piecewise-Q1 material field, not a continuum solution or true contact pressure.",
            "This does not replace weak reactions, certify unilateral complementarity, or alter fields_001 Gauss nonconvergence observations.",
            "The series truncation estimate is not an interval bound on finite-precision roundoff."],input_and_helper_sha256=bindings)
    write_new(out/"plan.json",plan)
    cases=[]
    for source in sources:
        name=source["run"].replace("/","_").replace("\\","_")+".json"
        previous=load(fields/name)
        if previous["state_id"]!=source["row"]["state_id"] or previous["diagnostic_algebra_status"]!="pass":
            raise ValueError("frozen field endpoint differs or did not pass")
        case=analyze(source,previous)
        write_new(out/name,case)
        cases.append(case)
    for path,digest in bindings.items():
        if sha(path)!=digest: raise ValueError("input changed during analytic diagnostic: "+path)
    summary=dict(schema="contact_c2_analytic_edge_v1",status="pass" if all(c["status"]=="pass" for c in cases) else "not_pass",
                 plan_sha256=sha(out/"plan.json"),cases=[{k:v for k,v in c.items() if k!="analytic_edges_HP120"} for c in cases])
    write_new(out/"summary.json",summary)
    write_new(out/"output_sha256.json",{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    print(json.dumps(dict(status=summary["status"],cases=len(cases),output=str(out))))
    return 0 if summary["status"]=="pass" else 1


if __name__=="__main__": sys.exit(main())
