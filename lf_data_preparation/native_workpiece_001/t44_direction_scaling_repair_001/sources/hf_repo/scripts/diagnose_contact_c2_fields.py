"""Read audited saved endpoints and diagnose fields; never run a FE solve.

--cases accepts {"cases":[{"run":"relative/path", "state_id":"phase:index"}]}
relative to --root. Omit state_id to use the final audited prefix state.
Default selection is the four TMC C1 endpoints in selection_v1.json.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from contact_c2_fields import comparison, dec, flatten, reconstruct
from contact_c2_sbp import decompose_material


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def arrays(path):
    with np.load(path,allow_pickle=False) as source:
        return {k:source[k] for k in source.files}


def serial(value):
    if isinstance(value,Decimal): return str(value)
    if isinstance(value,dict): return {k:serial(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [serial(v) for v in value]
    if isinstance(value,np.generic): return value.item()
    return value


def write_new(path,value):
    with Path(path).open("x",encoding="utf-8") as stream:
        json.dump(serial(value),stream,indent=2,allow_nan=False)
        stream.write("\n")


def checked_sources(root,manifest):
    data=load(manifest)
    choices=data.get("cases")
    if choices is None:
        choices=[dict(run=c["run"]) for c in data["runs"] if c["kind"]=="TMC"]
        if len(choices)!=4: raise ValueError("default selection requires four TMC paths")
    if not choices: raise ValueError("empty endpoint selection")
    bindings={str(manifest):sha(manifest)}
    sources=[]
    for choice in choices:
        run=(root/choice["run"]).resolve()
        if not run.is_relative_to(root): raise ValueError("run escapes selected root")
        audit_path=run/choice.get("audit","audit.json")
        if not audit_path.resolve().is_relative_to(run): raise ValueError("audit escapes run")
        audit=load(audit_path)
        if audit.get("status")!="pass" or audit.get("measurement_precision")!=80:
            raise ValueError("requires passing audit with HP80 measurements")
        for name,digest in audit["input_and_helper_sha256"].items():
            p=(run/name).resolve()
            if not p.is_relative_to(root.parent) or sha(p)!=digest:
                raise ValueError("audit input/helper hash mismatch: "+name)
            bindings[str(p)]=digest
        selected_id=choice.get("state_id",audit["prefix"]["states"][-1]["state_id"])
        matches=[s for s in audit["states"] if s["state_id"]==selected_id]
        prefixes=[s for s in audit["prefix"]["states"] if s["state_id"]==selected_id]
        if len(matches)!=1 or len(prefixes)!=1 or matches[0]["status"]!="pass" or prefixes[0].get("comparable") is not True:
            raise ValueError("selected state must be a unique admitted prefix state")
        row=matches[0]
        if "detail_file" in row:
            detail_path=(run/row["detail_file"]).resolve()
            if not detail_path.is_relative_to(run) or sha(detail_path)!=row["detail_sha256"]:
                raise ValueError("audit state detail path/hash mismatch")
            detail_bindings=audit.get("detail_output_sha256",{})
            if detail_bindings.get(row["detail_file"])!=row["detail_sha256"]:
                raise ValueError("state detail is not bound by audit output manifest")
            detailed=load(detail_path)
            if detailed["state_id"]!=selected_id or detailed["status"]!="pass":
                raise ValueError("state detail identity/admission mismatch")
            bindings[str(detail_path)]=sha(detail_path)
            row=detailed
        stage_index=run/"stages/index.json"
        stages=[s for s in load(stage_index)["stages"] if s["phase_id"]==row["phase_id"]]
        if len(stages)!=1: raise ValueError("missing unique stage")
        stage=(run/stages[0]["directory"]).resolve()
        if not stage.is_relative_to(run): raise ValueError("stage path escapes run")
        model_path=stage/"model.npz"
        index_path=stage/"steps/index.json"
        entries=[s for s in load(index_path)["steps"] if s["index"]==row["index"]]
        if len(entries)!=1 or entries[0]["d"]!=row["parameter_s"]:
            raise ValueError("state index/parameter mismatch")
        state_path=(stage/"steps"/entries[0]["file"]).resolve()
        if not state_path.is_relative_to(stage/"steps") or sha(state_path)!=entries[0]["sha256"]:
            raise ValueError("state path/hash mismatch")
        for p in (audit_path,stage_index,model_path,index_path,state_path,stage/"metadata.json",run/"metadata.json"):
            bindings[str(p)]=sha(p)
        # Every mechanics primitive must have been included in the admitted audit.
        audit_bound={(run/name).resolve() for name in audit["input_and_helper_sha256"]}
        if any(p.resolve() not in audit_bound for p in (model_path,state_path,index_path)):
            raise ValueError("model/state/index not bound by passing audit")
        model=arrays(model_path)
        metadata=load(stage/"metadata.json")
        if metadata.get("kind")!="TMC": raise ValueError("C2 field adapter is restricted to TMC")
        sources.append(dict(run=choice["run"],audit=audit,row=row,model=model,state=arrays(state_path),metadata=metadata))
    return sources,bindings


def virtual_fields(model,negative):
    n=len(model["coordinates"])
    fields={name:np.zeros(2*n) for name in ("translation_x_1mm","translation_y_1mm","top_y_1mm","negative_top_y_1mm","first_negative_top_y_1mm","affine_y")}
    fields["translation_x_1mm"][::2]=1
    fields["translation_y_1mm"][1::2]=1
    fields["top_y_1mm"][2*model["top_nodes"]+1]=1
    fields["negative_top_y_1mm"][[2*i+1 for i in negative]]=1
    if negative: fields["first_negative_top_y_1mm"][2*negative[0]+1]=1
    fields["affine_y"][1::2]=model["coordinates"][:,1]
    return fields


def analyze(source):
    model,row=source["model"],source["row"]
    hp=row["precision_evidence_decimal"]["80"]
    raw={key:[Decimal(v) for v in hp[field]] for key,field in
         (("total","internal_decimal"),("material","material_internal_decimal"),("regularization","regularization_internal_decimal"))}
    top=list(map(int,model["top_nodes"]))
    negative=[n for n in top if raw["total"][2*n+1]>0] # on-plane sign is negative internal.
    virtuals=virtual_fields(model,negative)
    results={}
    decompositions={}
    sbp_evidence={}
    for precision in (80,120):
        print(f"{source['run']} {precision} digits",flush=True)
        results[precision]=reconstruct(model,source["state"]["u_lift"],source["state"]["u_fluctuation"],
                                      virtuals,precision=precision,thickness=1.0)
        sbp_evidence[precision]=decompose_material(model,results[precision]["elements"],precision=precision,thickness=1.0)
        decompositions[precision]=sbp_evidence[precision]["fields"]
    lo,hi=results[80],results[120]
    checks={}
    for key in ("total","material","regularization"):
        checks["assembly_vs_saved_HP80_"+key]=comparison(lo[key],raw[key],unit="N")
        checks["cross_precision_"+key]=comparison(lo[key],hi[key],unit="N")
    checks["kinematics_vs_saved_HP80_J"]=comparison([[q["J"] for q in e["quadrature"]] for e in lo["elements"]],
             [[Decimal(v) for v in e] for e in hp["J_decimal"]],unit="dimensionless")
    for name,unit,getter in (("F","dimensionless",lambda e:[q["F"] for q in e["quadrature"]]),
                             ("J","dimensionless",lambda e:[q["J"] for q in e["quadrature"]]),
                             ("P","N/mm^2",lambda e:[q["P"] for q in e["quadrature"]]),
                             ("Hu","1/mm",lambda e:e["Hu"])):
        checks["cross_precision_"+name]=comparison([getter(e) for e in lo["elements"]],[getter(e) for e in hi["elements"]],unit=unit)
    for key in lo["edge_projections"]:
        checks["cross_precision_edge_"+key]=comparison(lo["edge_projections"][key],hi["edge_projections"][key],unit="N")
        for field,unit in (("minimum_J","dimensionless"),("maximum_J","dimensionless"),("normal_Pyy_range","N/mm^2")):
            checks["cross_precision_edge_"+key+"_"+field]=comparison([e[field][key] for e in lo["edge_elements"]],
                                                   [e[field][key] for e in hi["edge_elements"]],unit=unit)
    for field,unit in (("F","dimensionless"),("P","N/mm^2"),("J","dimensionless")):
        checks["cross_precision_edge_endpoint_"+field]=comparison([[q[field] for q in e["endpoints"]] for e in lo["edge_elements"]],
                                                       [[q[field] for q in e["endpoints"]] for e in hi["edge_elements"]],unit=unit)
    decomposition_keys=("material_N","top_edge_consistent_N","other_external_edge_consistent_N",
                        "internal_interface_jump_N","minus_projected_div_N","top_edge_physical_simpson_N","top_weight_correction_N")
    for key in decomposition_keys:
        checks["cross_precision_SBP_"+key]=comparison(decompositions[80][key],decompositions[120][key],unit="N")
    for precision in (80,120):
        sbp=decompositions[precision]
        checks[f"SBP_{precision}_all_local_and_global_identities"]=dict(status=sbp_evidence[precision]["status"],
                     meaning="Every element material reassembly/SBP and both global identities must pass 1e-45")
        checks[f"SBP_{precision}_material_reassembly"]=comparison(sbp["material_N"],results[precision]["material"],unit="N")
        checks[f"SBP_{precision}_physical_top_simpson"]=comparison(sbp["top_edge_physical_simpson_N"],results[precision]["edge_projections"]["simpson3"],unit="N")
        with localcontext() as ctx:
            ctx.prec=precision
            left=[m-t for m,t in zip(sbp["material_N"],sbp["top_edge_physical_simpson_N"])]
            right=[o+j+d+w for o,j,d,w in zip(sbp["other_external_edge_consistent_N"],
                   sbp["internal_interface_jump_N"],sbp["minus_projected_div_N"],sbp["top_weight_correction_N"])]
            checks[f"SBP_{precision}_physical_top_difference_identity"]=comparison(left,right,unit="N",precision=precision)
    for name in virtuals:
        for key in ("material","regularization","total"):
            checks["cross_precision_work_"+name+"_"+key]=comparison([lo["virtual_work"][name]["integrated_N_mm"][key]],
                    [hi["virtual_work"][name]["integrated_N_mm"][key]],unit="N mm")
            for p in (80,120):
                checks[f"virtual_work_{p}_{name}_{key}"]=results[p]["virtual_work"][name]["checks"][key]
    with localcontext() as ctx:
        ctx.prec=120
        node_rows=[]
        for n in top:
            dof=2*n+1
            neighbors=[e["element"] for e in hi["elements"] if n in e["connectivity"]]
            projections={key:-values[dof] for key,values in hi["edge_projections"].items()}
            sbp=decompositions[120]
            terms={key:-sbp[key][dof] for key in ("other_external_edge_consistent_N","internal_interface_jump_N",
                                                "minus_projected_div_N","top_weight_correction_N")}
            node_rows.append(dict(node_id=n,reference_coordinate_mm=list(map(float,model["coordinates"][n])),
                current_coordinate_mm=hi["current"][n],in_initial_solid_xspan=0<=model["coordinates"][n,0]<=2,
                adjacent_elements=neighbors,total_on_plane_N=-hi["total"][dof],
                material_weak_on_plane_N=-hi["material"][dof],regularization_weak_on_plane_N=-hi["regularization"][dof],
                direct_material_edge_on_plane_N=projections,
                material_weak_minus_direct_gauss64_N=-hi["material"][dof]-projections["gauss64"],
                material_weak_minus_direct_simpson_N=-hi["material"][dof]-projections["simpson3"],
                interpolated_stress_SBP_difference_terms_on_plane_N=terms,
                SBP_terms_sum_N=sum(terms.values(),Decimal(0)),
                negative_total=n in negative))
        adjacent=sorted({e for n in node_rows if n["negative_total"] for e in n["adjacent_elements"]})
        convergence={}
        for first,second in (("gauss8","gauss16"),("gauss16","gauss32"),("gauss32","gauss64"),("simpson3","gauss64")):
            convergence[first+"_vs_"+second]=comparison(hi["edge_projections"][first],hi["edge_projections"][second],
                                                      unit="N",limit="1e-8")
        def stats(values):
            return dict(negative_sum_N=sum((v for v in values if v<0),Decimal(0)),
                        positive_sum_N=sum((v for v in values if v>0),Decimal(0)),net_N=sum(values,Decimal(0)))
        aggregates={key:stats([-hi[key][2*n+1] for n in top]) for key in ("total","material","regularization")}
        aggregates["direct_material_edges"]={key:stats([-values[2*n+1] for n in top]) for key,values in hi["edge_projections"].items()}
        edge_rows=hi["edge_elements"]
        quantities=dict(minimum_J_solid=min(q["J"] for e in hi["elements"] if e["solid"] for q in e["quadrature"]),
                        minimum_J_medium=min(q["J"] for e in hi["elements"] if not e["solid"] for q in e["quadrature"]),
                        top_edge_gauss64_Pyy_min_N_per_mm2=min(e["normal_Pyy_range"]["gauss64"][0] for e in edge_rows),
                        top_edge_gauss64_Pyy_max_N_per_mm2=max(e["normal_Pyy_range"]["gauss64"][1] for e in edge_rows))
        quantities["top_edges_with_full_edge_material_compression_certificate"]=sum(e["full_edge_material_compression_certificate"]["certified"] for e in edge_rows)
        quantities["total_top_edges"]=len(edge_rows)
    status="pass" if all(v["status"]=="pass" for v in checks.values()) else "not_pass"
    return dict(run=source["run"],h=source["metadata"]["h"],phase_id=row["phase_id"],state_id=row["state_id"],
        parameter_s=row["parameter_s"],physical_mean_drive=row["physical_mean_drive"],
        source_audit_status="pass",source_verification_precision_pair=source["audit"]["verification_precision_pair"],
        diagnostic_algebra_status=status,checks=checks,quantities=quantities,aggregate=aggregates,
        edge_quadrature_observations=convergence,all_top_nodes=node_rows,
        negative_node_adjacent_elements=[e for e in hi["elements"] if e["element"] in adjacent],
        negative_node_adjacent_SBP_elements=[e for e in sbp_evidence[120]["elements"] if e["element"] in adjacent],
        all_top_edge_summaries=[{k:v for k,v in e.items() if k!="projection"} for e in edge_rows],
        virtual_work=hi["virtual_work"])


def plot(cases,out):
    fig,axes=plt.subplots(len(cases),2,figsize=(13,3.0*len(cases)),squeeze=False,constrained_layout=True)
    for row,case in zip(axes,cases):
        nodes=case["all_top_nodes"]
        x=[n["reference_coordinate_mm"][0] for n in nodes]
        for ax in row:
            ax.axhline(0,color=".5",lw=.6);ax.axvspan(0,2,color=".9",alpha=.5)
            ax.set_yscale("symlog",linthresh=1e-5)
            ax.set(xlabel="Reference top-node x (mm)",ylabel="N per node",title=f"{case['phase_id']}, h={case['h']} mm")
            ax.grid(alpha=.2)
        for key,label,color in (("total_on_plane_N","Weak total","#273746"),("material_weak_on_plane_N","Weak material","#3274a1"),
                                ("regularization_weak_on_plane_N","Weak regularization","#b66c36")):
            row[0].plot(x,[float(n[key]) for n in nodes],".-",ms=3,label=label,color=color)
        row[1].plot(x,[float(n["material_weak_on_plane_N"]) for n in nodes],".-",ms=3,label="Weak material",color="#3274a1")
        for key,label,style in (("simpson3","Direct edge Simpson 3","x--"),("gauss64","Direct edge Gauss 64",".-")):
            row[1].plot(x,[float(n["direct_material_edge_on_plane_N"][key]) for n in nodes],style,ms=3,label=label)
        for ax in row: ax.legend(fontsize=7,loc="upper right")
    fig.suptitle("Saved TMC endpoint field diagnostics | on-plane sign = minus internal sign\n"
                 "Weak nodal forces and direct material edge projections are different quantities; neither is a Cauchy pressure sample",fontsize=11)
    for ext in ("png","svg"): fig.savefig(out/("field_comparison."+ext),dpi=170)
    plt.close(fig)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",default="hf4_c1_results")
    parser.add_argument("--cases")
    parser.add_argument("--output",default="hf4_c2_diagnostics/fields_001")
    args=parser.parse_args(argv)
    root,out=Path(args.root).resolve(),Path(args.output).resolve()
    manifest=Path(args.cases).resolve() if args.cases else root/"selection_v1.json"
    if out.exists(): raise FileExistsError("refusing to overwrite diagnostic directory")
    sources,bindings=checked_sources(root,manifest)
    scripts=[Path(__file__).resolve(),Path(__file__).with_name("contact_c2_fields.py").resolve(),
             Path(__file__).with_name("hf4_split_precision_reference.py").resolve(),Path(__file__).with_name("hf2_precision_reference.py").resolve(),
             Path(__file__).with_name("contact_c2_sbp.py").resolve()]
    bindings.update({str(p):sha(p) for p in scripts})
    out.mkdir(parents=True)
    plan=dict(schema="contact_c2_fields_plan_v1",created_utc=datetime.now(timezone.utc).isoformat(),
        cases=[dict(run=s["run"],state_id=s["row"]["state_id"]) for s in sources],
        precision_pair=[80,120],measurement_precision=120,physical_thickness_mm=1,
        algebra_gate=dict(limit="1e-45",metric="norm(error)/max(norm(reference), one specified unit)",
                          units=["N", "N/mm^2", "dimensionless", "1/mm", "N mm"]),
        edge_quadrature=dict(rules=["Simpson3", "Gauss8", "Gauss16", "Gauss32", "Gauss64"],
            maximum_order=64,observation_threshold="1e-8",threshold_role="quadrature observation only; not C1 admission or truth",
            volume_weights="Exact binary64 saved quadrature primitives",edge_weights="Declared thickness 1 mm and exact reference edge length; independent Decimal quadrature"),
        sign="Internal residual is +int gradN:P + regularization; displayed on-plane normal forces negate y entries. Direct edge internal traction is +int N P*(0,1) dS0.",
        limitations=["No FE solve or source state modification.","Direct material boundary projection is not the assembled material weak nodal residual.",
            "Their difference includes element/interelement equilibrium and quadrature effects; not automatically physical tensile contact.",
            "SBP decomposition uses the biquadratic interpolant of the nine saved volume-quadrature Piola samples, not the continuous constitutive stress divergence.",
            "Consistent SBP edge weights inherit saved binary64 volume weights; the difference from physical thickness Simpson weights is explicitly retained.",
            "Regularization is kr exp(-5J) Hu:H(delta u) weak residual; no added variation of exp and no substitute energy.",
            "No independent equilibrium is assumed for material or regularization components.",
            "Reference x-span classification is not the deformed contact region.",
            "Boundary integration refinement is not mesh convergence or verification of a unilateral law."],
        input_and_helper_sha256=bindings)
    write_new(out/"plan.json",plan) # Written BEFORE any new field/force evaluation.
    cases=[]
    for source in sources:
        case=analyze(source)
        filename=source["run"].replace("/","_").replace("\\","_")+".json"
        write_new(out/filename,case)
        cases.append(case)
    for p,digest in bindings.items():
        if sha(p)!=digest: raise ValueError("input changed during diagnostic: "+p)
    payload=dict(schema="contact_c2_saved_field_diagnostic_v1",status="pass" if all(c["diagnostic_algebra_status"]=="pass" for c in cases) else "not_pass",
        status_meaning="new algebra/precision consistency only; source admission is unchanged",plan_sha256=sha(out/"plan.json"),
        cases=[{k:v for k,v in c.items() if k not in ("negative_node_adjacent_elements","negative_node_adjacent_SBP_elements","virtual_work","all_top_edge_summaries")} for c in cases])
    write_new(out/"summary.json",payload)
    plot(cases,out)
    write_new(out/"output_sha256.json",{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    print(json.dumps(dict(status=payload["status"],cases=len(cases),output=str(out)),ensure_ascii=False))
    return 0 if payload["status"]=="pass" else 1


if __name__=="__main__": sys.exit(main())
