"""Read-only C2 evidence summary. No mechanics, AD, interpolation or FE solve.

Only contiguous, hash-bound HP80 audit prefixes supply comparison values.
Unknown/unexecuted states remain null. Negative weak reactions are preserved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ZERO,ONE=Decimal(0),Decimal(1)
COLORS={"baseline_h025":"#6d7591","baseline_h0125":"#216e8b","mesh_h00625":"#248870",
        "padding_2p5":"#b27530","outer_free":"#a54b62"}
LABELS={"baseline_h025":"C1 h=0.25","baseline_h0125":"C1 h=0.125","mesh_h00625":"C2 h=0.0625",
        "padding_2p5":"C2 padding=2.5","outer_free":"C2 outer bottom free"}


class AuditUnavailable(Exception):
    """Accepted production records exist but have no independent audit yet."""


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(value):
    if value is None or isinstance(value,bool): raise ValueError("missing/boolean numeric evidence")
    result=Decimal(str(value))
    if not result.is_finite(): raise ValueError("nonfinite numeric evidence")
    return result


def exact_float(value): return Decimal.from_float(float(value))


def plain(value):
    if isinstance(value,Decimal): return str(value)
    if isinstance(value,dict): return {k:plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [plain(v) for v in value]
    if isinstance(value,np.generic): return value.item()
    return value


class Reader:
    def __init__(self,root):
        self.root=Path(root).resolve();self.bindings={}

    def path(self,base,name):
        if not isinstance(name,str) or not name or "\\" in name or Path(name).is_absolute() or ":" in name:
            raise ValueError("expected relative POSIX evidence path")
        p=(Path(base)/name).resolve()
        if not p.is_relative_to(self.root): raise ValueError("evidence escapes workspace")
        return p

    def bind(self,path,expected=None):
        path=Path(path).resolve()
        if not path.is_relative_to(self.root): raise ValueError("bound path escapes workspace")
        actual=digest(path)
        if expected is not None and actual!=expected: raise ValueError("SHA256 mismatch: "+str(path))
        self.bindings[path.relative_to(self.root).as_posix()]=actual
        return actual

    def json(self,path,expected=None):
        self.bind(path,expected)
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))

    def npz(self,path):
        self.bind(path)
        with np.load(path,allow_pickle=False) as z: result={k:z[k] for k in z.files}
        if any(a.dtype.kind not in "biuf" or not np.all(np.isfinite(a)) for a in result.values()):
            raise ValueError("NPZ must contain finite ordinary numeric primitives")
        return result

    def audit_bindings(self,audit,run):
        mapping=audit.get("input_and_helper_sha256")
        if not isinstance(mapping,dict) or not mapping: raise ValueError("audit lacks input/helper hash chain")
        covered=set()
        for name,expected in mapping.items():
            p=self.path(run,name);self.bind(p,expected);covered.add(p)
        return covered


def pwl_value(x,spec):
    xs=list(map(number,spec["x_mm"])); ys=list(map(number,spec["values"]))
    if len(xs)!=len(ys) or len(xs)<2 or any(b<=a for a,b in zip(xs,xs[1:])):
        raise ValueError("invalid prescribed PWL test function")
    if x<xs[0] or x>xs[-1]: return ZERO
    for a,b,ya,yb in zip(xs,xs[1:],ys,ys[1:]):
        if a<=x<=b: return ya+(yb-ya)*(x-a)/(b-a)
    raise ValueError("unresolved PWL point")


def state_observables(row,model,virtuals):
    """Use saved HP80 arrays; source/identity/prefix checks are caller duties."""
    hp=row["precision_evidence_decimal"]["80"]
    material=list(map(number,hp["material_internal_decimal"]))
    regularization=list(map(number,hp["regularization_internal_decimal"]))
    total=list(map(number,hp["internal_decimal"]))
    u=list(map(number,hp["physical_displacement_decimal"]))
    xy=model["coordinates"];top=list(map(int,model["top_nodes"]))
    if not top or len(set(top))!=len(top) or any(n<0 or n>=len(xy) for n in top): raise ValueError("invalid top node inventory")
    if any(len(a)!=2*len(xy) for a in (material,regularization,total,u)): raise ValueError("HP field shape mismatch")
    direction=np.asarray(model["direction"])
    fixed=np.asarray(model["fixed_dofs"])
    if (direction.shape!=(len(total),) or direction.dtype.kind not in "iuf" or not np.all(np.isfinite(direction))
            or fixed.dtype.kind not in "iu" or fixed.ndim!=1 or np.any(fixed<0) or np.any(fixed>=len(total))
            or len(np.unique(fixed))!=len(fixed)):
        raise ValueError("invalid actual prescribed direction/fixed-DOF inventory")
    if np.any(direction[np.setdiff1d(np.arange(len(total)),fixed)]!=0):
        raise ValueError("actual prescribed parameter direction must vanish on free DOFs")
    error=row["measurements"]["component_precision"]["total_force"]
    production_error=number(error["absolute_error"])
    precision_error=number(error["cross_precision_absolute_error"])
    if min(production_error,precision_error)<0: raise ValueError("negative error norm")
    with localcontext() as ctx:
        ctx.prec=120
        nodes=[]
        for n in top:
            k=2*n+1
            nodes.append(dict(node_id=n,reference_coordinate_mm=list(map(exact_float,xy[n])),
                current_coordinate_mm=[exact_float(xy[n,i])+u[2*n+i] for i in (0,1)],
                total_on_plane_N=-total[k],material_on_plane_N=-material[k],regularization_on_plane_N=-regularization[k]))
        forces={key:sum((n[key+"_on_plane_N"] for n in nodes),ZERO) for key in ("total","material","regularization")}
        declared=number(row["force_components"]["normal_top"]["total"])
        if abs(forces["total"]-declared)>Decimal("1e-60")*max(ONE,abs(declared)):
            raise ValueError("HP nodal sum differs from independent normal-top field")
        dd=list(map(exact_float,direction))
        generalized={key:sum((p*f for p,f in zip(dd,array)),ZERO)
                     for key,array in (("total",total),("material",material),("regularization",regularization))}
        declared_generalized={key:number(row["force_components"]["parameter_generalized_force"][key]) for key in generalized}
        generalized_differences={key:generalized[key]-declared_generalized[key] for key in generalized}
        if any(abs(generalized_differences[key])>Decimal("1e-60")*max(ONE,abs(declared_generalized[key])) for key in generalized):
            raise ValueError("actual direction dot HP force differs from declared parameter generalized force")
        tests={"net":dict(name="net",x_mm=[],values=[])}
        tests.update({v["name"]:v for v in virtuals})
        if len(tests)!=len(virtuals)+1: raise ValueError("duplicate/reserved virtual function name")
        functionals={}
        for name,spec in tests.items():
            phi=[ONE if name=="net" else pwl_value(n["reference_coordinate_mm"][0],spec) for n in nodes]
            phi_norm=sum((p*p for p in phi),ZERO).sqrt()
            values={key:sum((p*n[key+"_on_plane_N"] for p,n in zip(phi,nodes)),ZERO) for key in ("total","material","regularization")}
            functionals[name]=dict(values_N=values,phi_l2_norm=phi_norm,
                 numerical_error_envelope_N=phi_norm*(production_error+precision_error),
                 semantics="dimensionless reference-PWL weights; N = work per 1 mm virtual amplitude; no clipping")
        direction_norm=sum((p*p for p in dd),ZERO).sqrt()
        functionals["parameter_generalized_force"]=dict(values_N=declared_generalized,phi_l2_norm=direction_norm,
            numerical_error_envelope_N=direction_norm*(production_error+precision_error),
            semantics="actual model.direction dot internal weak force; work per 1 mm parameter increment on the model. Outer-free and driven-bottom models have different directions.")
        negative=[n for n in nodes if n["total_on_plane_N"]<0]
        drive=row["measurements"]["physical_drive"]
        return dict(authority="saved independent HP80 split-state audit arrays; Decimal summation at 120 digits",
            normal_top_N=forces,negative_node_count=len(negative),negative_sum_N=sum((n["total_on_plane_N"] for n in negative),ZERO),
            parameter_generalized_force_N=declared_generalized,
            parameter_generalized_force_dot_check_N=generalized_differences,
            negative_magnitude_N=-sum((n["total_on_plane_N"] for n in negative),ZERO),
            positive_sum_N=sum((n["total_on_plane_N"] for n in nodes if n["total_on_plane_N"]>0),ZERO),
            body_bottom_mean_mm=number(drive["body"]),whole_bottom_mean_mm=number(drive["whole_bottom"]),
            hp80_relative_residual=number(row["measurements"]["hp80_relative_residual"]),
            numerical_error_primitives_N=dict(production_absolute_error=production_error,cross_precision_absolute_error=precision_error),
            functionals=functionals,all_top_nodes=nodes)


def prefix_mask(rows,prefix):
    """A local failure/unknown is absorbing; later valid rows cannot reopen it."""
    table={}
    for p in prefix:
        if p["state_id"] in table: raise ValueError("duplicate prefix state")
        table[p["state_id"]]=p
    result=[];open_prefix=True;seen=set()
    for row in rows:
        identity=row["state_id"]
        if identity in seen: raise ValueError("duplicate audit state")
        seen.add(identity)
        p=table.get(identity,{})
        local=row.get("status")=="pass" and p.get("comparable") is True
        open_prefix=open_prefix and local
        result.append(open_prefix)
    return result


def execution_receipts(reader,run,identity,protocol_path):
    """Verify external process completion without discarding usable HP prefixes."""
    actions={};issues=[];has_invalid=False;has_missing=False
    for action in ("solve","audit"):
        path=run.parent/f"{run.name}.{action}.receipt.json"
        record=dict(status="pending",receipt=path.relative_to(reader.root).as_posix())
        if not path.exists():
            has_missing=True;record["reason"]="external receipt missing"
            actions[action]=record;issues.append(action+": external receipt missing");continue
        try:
            saved=reader.json(path)
            record["saved"]=saved
            if (saved.get("schema")!="contact_c2_external_receipt_v1" or saved.get("action")!=action
                    or saved.get("case_id")!=identity or saved.get("run_name")!=run.name):
                raise ValueError("external receipt identity/schema mismatch")
            if type(saved.get("returncode")) is not int or saved["returncode"]!=0 or saved.get("timed_out") is not False:
                raise ValueError("external subprocess unsuccessful or timed out")
            if saved.get("protocol_sha256")!=digest(protocol_path): raise ValueError("external receipt protocol hash mismatch")
            reader.bind(run.parent/f"{run.name}.{action}.log",saved["log_sha256"])
            if action=="audit":
                if not isinstance(saved.get("audit_sha256"),str): raise ValueError("external audit receipt lacks audit hash")
                reader.bind(run/"audit.json",saved["audit_sha256"])
            record["status"]="pass"
        except (OSError,KeyError,ValueError) as error:
            has_invalid=True;record.update(status="failed",reason=str(error));issues.append(action+": "+str(error))
        actions[action]=record
    return dict(status="failed" if has_invalid else "pending" if has_missing else "pass",actions=actions,issues=issues)


def load_run(reader,run,identity,spec,protocol,protocol_path,*,baseline_audit=None):
    attempted=run.exists() or any((run.parent/f"{run.name}.{action}.{suffix}").exists() for action in ("solve","audit") for suffix in ("log","receipt.json"))
    result=dict(case_id=identity,label=LABELS[identity],run=run.relative_to(reader.root).as_posix(),spec=spec,
        planned=True,executed=attempted,admitted=False,failed=False,status="planned",issues=[],states=[],targets=[],
        accepted_state_count=None,accepted_original_target_count=None,valid_prefix_state_count=None,
        admitted_original_target_count=None,source_and_detail_chain_valid=None)
    targets=list(map(number,protocol["uniform_targets_mm"]))
    if not attempted:
        result["targets"]=[dict(d_mm=d,accepted=False,comparable=False,measurement=None,reason="not_executed") for d in targets]
        return result
    result["status"]="executed_unaudited"
    raw_entries=[]
    try:
        meta=reader.json(run/"metadata.json")
        result["production_status"]=reader.json(run/"result.json").get("status") if (run/"result.json").exists() else None
        for extra in ("completion.json","exception.json"):
            if (run/extra).exists(): reader.json(run/extra)
        result["failed"]=(run/"exception.json").exists() or result["production_status"] not in (None,"success")
        if meta.get("kind")!="TMC" or meta.get("mode")!="uniform" or number(meta["h"])!=number(spec["h_mm"]):
            raise ValueError("run identity/model differs from declared case")
        if baseline_audit is None:
            if meta.get("case_id")!=identity or meta.get("case")!=spec or meta.get("protocol")!=protocol or meta.get("protocol_sha256")!=digest(protocol_path):
                raise ValueError("run differs from frozen C2 protocol")
        sources=meta.get("source_sha256")
        if not isinstance(sources,dict) or not sources: raise ValueError("run lacks source manifest")
        for name,expected in sources.items(): reader.bind(reader.path(reader.root/"hf_repo",name),expected)
        stage_index=reader.json(run/"stages/index.json")
        if len(stage_index["stages"])!=1 or stage_index["stages"][0]["phase_id"]!="uniform_tmc":
            raise ValueError("unexpected uniform stage inventory")
        stage=reader.path(run,stage_index["stages"][0]["directory"])
        index_path=stage/"steps/index.json"
        raw_entries=reader.json(index_path)["steps"]
        result["accepted_state_count"]=len(raw_entries)
        result["accepted_original_target_count"]=sum(e.get("is_original_target") is True for e in raw_entries)
        audit_path=run/"audit.json"
        if not audit_path.exists(): raise AuditUnavailable("independent audit absent; accepted records are unscored")
        audit=reader.json(audit_path,baseline_audit)
        result["audit_status"]=audit.get("status")
        expected_schema="contact-c1-independent-audit-1.0" if baseline_audit else "contact-c2-independent-audit-1.0"
        if audit.get("schema_version")!=expected_schema or audit.get("measurement_precision")!=80 or audit.get("verification_precision_pair")!=[80,120]:
            raise ValueError("unexpected audit schema/precision authority")
        covered=reader.audit_bindings(audit,run)
        for required in (run/"metadata.json",run/"stages/index.json",stage/"model.npz",index_path):
            if required.resolve() not in covered: raise ValueError("audit does not bind required inventory/primitive: "+str(required))
        model=reader.npz(stage/"model.npz")
        rows=audit.get("states",[])
        if len(rows)!=len(raw_entries): raise ValueError("audit/index accepted inventory differs")
        details={}
        for name,expected in audit.get("detail_output_sha256",{}).items():
            p=reader.path(run,name)
            if not p.is_relative_to(run): raise ValueError("detail output escapes run")
            reader.bind(p,expected);details[name]=expected
        valid=prefix_mask(rows,audit.get("prefix",{}).get("states",[]))
        prefix_open=True
        for ordinal,(compact,entry,comparable) in enumerate(zip(rows,raw_entries,valid)):
            if entry["index"]!=ordinal or compact["index"]!=ordinal or compact["state_id"]!=f"uniform_tmc:{ordinal}" or number(compact["parameter_s"])!=number(entry["d"]):
                raise ValueError("audit/index state identity or order mismatch")
            row=compact
            if "detail_file" in compact:
                if details.get(compact["detail_file"])!=compact["detail_sha256"]: raise ValueError("detail file has no matching audit output binding")
                row=reader.json(reader.path(run,compact["detail_file"]),compact["detail_sha256"])
                for key in ("state_id","index","parameter_s","status"):
                    if row[key]!=compact[key]: raise ValueError("compact/detail state mismatch")
            state_path=reader.path(stage/"steps",entry["file"])
            if state_path not in covered: raise ValueError("state NPZ not covered by audit")
            reader.bind(state_path,entry["sha256"])
            prefix_open=prefix_open and comparable
            state=dict(state_id=compact["state_id"],index=ordinal,d_mm=number(entry["d"]),
                is_original_target=entry.get("is_original_target") is True,
                audit_state_status=row.get("status"),comparable=False,measurement=None)
            if prefix_open:
                try:
                    state["measurement"]=state_observables(row,model,protocol["virtual_test_functions"])
                    state["comparable"]=True
                except (KeyError,ValueError,ArithmeticError) as error:
                    prefix_open=False;state["reason"]="unusable HP state: "+str(error)
            result["states"].append(state)
        result["source_and_detail_chain_valid"]=True
        result["failed"]|=audit.get("status")!="pass"
        complete=all(any(s["d_mm"]==d and s["is_original_target"] and s["comparable"] for s in result["states"]) for d in targets)
        result["admitted"]=(audit.get("status")=="pass" and result["production_status"]=="success" and not result["failed"]
                            and complete and all(s["comparable"] for s in result["states"]))
        result["status"]="admitted" if result["admitted"] else "failed" if result["failed"] else "executed_partial"
    except (OSError,KeyError,ValueError,ArithmeticError,AuditUnavailable) as error:
        result["issues"].append(str(error))
        result["source_and_detail_chain_valid"]=False
        # An incomplete global provenance chain invalidates all derived scores.
        result["states"]=[]
        result["failed"]|=(run/"audit.json").exists() or (run/"exception.json").exists() or isinstance(error,(KeyError,ValueError,ArithmeticError))
        result["status"]="failed" if result["failed"] else "executed_unaudited"
    if baseline_audit is None:
        external=execution_receipts(reader,run,identity,protocol_path)
        result["external_execution"]=external
        result["issues"].extend(external["issues"])
        result["admitted"]=result["admitted"] and external["status"]=="pass"
        result["failed"]|=external["status"]=="failed"
        if result["failed"]: result["status"]="failed"
        elif external["status"]=="pending": result["status"]="executed_pending_receipts"
    else:
        result["external_execution"]=dict(status="not_applicable_legacy_C1",semantics="C1 baseline is bound by its separately frozen audit, not the new C2 wrapper")
    for d in targets:
        matched=[s for s in result["states"] if s["d_mm"]==d and s["is_original_target"]]
        if len(matched)>1: raise ValueError("duplicate original target")
        accepted=any(number(e["d"])==d and e.get("is_original_target") is True for e in raw_entries)
        state=matched[0] if matched else None
        result["targets"].append(dict(d_mm=d,accepted=accepted,comparable=bool(state and state["comparable"]),
            measurement=state["measurement"] if state and state["comparable"] else None,
            reason=None if state and state["comparable"] else "outside_valid_audited_prefix_or_missing"))
    result["valid_prefix_state_count"]=sum(s["comparable"] for s in result["states"])
    result["admitted_original_target_count"]=sum(t["comparable"] for t in result["targets"])
    return result


def compare_runs(left,right):
    right_targets={t["d_mm"]:t for t in right["targets"]}
    comparisons=[]
    with localcontext() as ctx:
        ctx.prec=120
        for t in left["targets"]:
            r=right_targets.get(t["d_mm"])
            row=dict(left=left["case_id"],right=right["case_id"],d_mm=t["d_mm"],comparable=False,functionals=None)
            if r and t["comparable"] and r["comparable"]:
                values={}
                for name,lvalue in t["measurement"]["functionals"].items():
                    rvalue=r["measurement"]["functionals"][name]
                    delta=lvalue["values_N"]["total"]-rvalue["values_N"]["total"]
                    bound=lvalue["numerical_error_envelope_N"]+rvalue["numerical_error_envelope_N"]
                    values[name]=dict(left_minus_right_N=delta,numerical_difference_envelope_N=bound,
                        distinguishable_at_recorded_numerical_envelope=abs(delta)>bound,
                        component_differences_N={k:lvalue["values_N"][k]-rvalue["values_N"][k] for k in ("material","regularization")})
                row.update(comparable=True,functionals=values)
            comparisons.append(row)
    return comparisons


def saved_field_context(reader):
    root=reader.root/"hf4_c2_diagnostics"
    for directory in ("fields_001","analytic_edge_001"):
        base=root/directory
        manifest=reader.json(base/"output_sha256.json")
        for name,expected in manifest.items(): reader.bind(reader.path(base,name),expected)
    fields=reader.json(root/"fields_001/summary.json")
    analytic=reader.json(root/"analytic_edge_001/summary.json")
    if fields["status"]!="pass" or analytic["status"]!="pass": raise ValueError("saved field/analytic diagnosis not passed")
    return dict(fields=fields,analytic=analytic,
        semantics="Saved C1 endpoint material field diagnostic only; does not assert any new C2 endpoint has the same sign/decomposition")


def make_summary(root,protocol_path):
    reader=Reader(root);protocol_path=Path(protocol_path).resolve()
    protocol=reader.json(protocol_path)
    if protocol.get("schema")!="contact_c2_uniform_diagnostic_v1": raise ValueError("unsupported protocol")
    for name,expected in protocol["implementation_sha256"].items(): reader.bind(reader.path(reader.root/"hf_repo",name),expected)
    gate=protocol["saved_field_admission"]
    if reader.json(reader.path(protocol_path.parent,gate["path"]),gate["sha256"])["status"]!="pass":
        raise ValueError("saved-field admission failed")
    runs=[]
    for entry in protocol["baseline_audits"]:
        audit_path=reader.path(protocol_path.parent,entry["path"])
        reader.bind(audit_path,entry["sha256"])
        meta=reader.json(audit_path.parent/"metadata.json")
        identity={Decimal(".25"):"baseline_h025",Decimal(".125"):"baseline_h0125"}.get(number(meta["h"]))
        if identity is None or identity in {r["case_id"] for r in runs}: raise ValueError("invalid baseline inventory")
        runs.append(load_run(reader,audit_path.parent,identity,dict(h_mm=meta["h"],padding_mm=2.,outer_bottom_policy="driven"),
                             protocol,protocol_path,baseline_audit=entry["sha256"]))
    if {r["case_id"] for r in runs}!={"baseline_h025","baseline_h0125"}: raise ValueError("both baseline meshes required")
    for case in protocol["run_sequence"]:
        runs.append(load_run(reader,reader.root/"hf4_c2_diagnostics/experiments"/case,case,protocol["cases"][case],protocol,protocol_path))
    by_id={r["case_id"]:r for r in runs}
    comparisons=[row for run in runs if run["case_id"]!="baseline_h0125" for row in compare_runs(run,by_id["baseline_h0125"])]
    context=saved_field_context(reader)
    reader.bind(Path(__file__))
    result=dict(schema="contact_c2_summary_v1",created_utc=datetime.now(timezone.utc).isoformat(),
        status="complete" if all(r["admitted"] for r in runs) else "partial",
        protocol=protocol_path.relative_to(reader.root).as_posix(),protocol_sha256=digest(protocol_path),
        runs=runs,matched_original_target_comparisons=comparisons,saved_C1_field_context=context,
        counts=dict(planned_new_paths=len(protocol["run_sequence"]),executed_new_paths=sum(r["executed"] for r in runs if r["case_id"] in protocol["cases"]),
                    admitted_new_paths=sum(r["admitted"] for r in runs if r["case_id"] in protocol["cases"]),
                    failed_new_paths=sum(r["failed"] for r in runs if r["case_id"] in protocol["cases"])),
        limitations=["Only original common d targets are compared; no interpolation or resumed scoring after the first invalid/unknown state.",
            "Force authority is saved independent HP80; zero, negative, and unknown values remain distinct.",
            "Weak nodal reactions (N/node) are not Cauchy pressure; their meshwise values do not share a fixed support.",
            "Fixed physical-reference PWL hats compare the same continuous virtual test across aligned grids; weights are not trapezoidal reweighting.",
            "Numerical envelopes sum ||phi||2*(production-to-HP80 total-force norm error + HP80-to-HP120 total-force norm difference) for both states; these are measured arithmetic diagnostics, not rigorous continuum/solver/discretization error bounds.",
            "Case differences are observations, not pure contact errors; three meshes alone do not establish continuum convergence.",
            "Outer-free whole-bottom mean is observational; only the body-bottom mean is prescribed.",
            "Parameter generalized force is actual model.direction dot the weak internal force (three components, independently checked). Outer-free and C1 driven-bottom cases prescribe different directions; these are model-specific work quantities.",
            "New C2 path admission additionally requires successful, non-timeout solve and audit subprocess receipts bound to this protocol, their logs, and audit bytes. Valid numerical prefixes remain readable when an external process failed, but the path is not admitted.",
            "C1 saved-field material stress/compression evidence is not automatically transferable to new C2 fields."],
        input_and_helper_sha256=reader.bindings)
    return result,reader


def endpoint(run):
    target=next((t for t in run["targets"] if t["d_mm"]==Decimal(".5")),None)
    return target["measurement"] if target and target["comparable"] else None


def save_figure(fig,out,name):
    for suffix in ("png","svg"): fig.savefig(out/(name+"."+suffix),dpi=180)
    plt.close(fig)


def plots(payload,out):
    runs=payload["runs"];status=payload["status"].upper()
    fig,axes=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
    for run in runs:
        identity=run["case_id"];color=COLORS[identity]
        x=[float(t["d_mm"]) for t in run["targets"]]
        y=[float(t["measurement"]["normal_top_N"]["total"]) if t["comparable"] else np.nan for t in run["targets"]]
        axes[0,0].plot(x,y,"o-",ms=3,color=color,label=run["label"]+" ["+run["status"]+"]")
        rows=[r for r in payload["matched_original_target_comparisons"] if r["left"]==identity]
        if rows: axes[0,1].plot([float(r["d_mm"]) for r in rows],
                [float(r["functionals"]["net"]["left_minus_right_N"]) if r["comparable"] else np.nan for r in rows],"o-",ms=3,color=color,label=run["label"])
    available=[(r,endpoint(r)) for r in runs if endpoint(r) is not None]
    common=set.intersection(*[{n["reference_coordinate_mm"][0] for n in e["all_top_nodes"]} for _,e in available]) if available else set()
    for run,e in available:
        nodes=[n for n in e["all_top_nodes"] if n["reference_coordinate_mm"][0] in common]
        axes[1,0].plot([float(n["reference_coordinate_mm"][0]) for n in nodes],[float(n["total_on_plane_N"]) for n in nodes],
                        ".-",ms=4,color=COLORS[run["case_id"]],label=run["label"])
    axes[0,0].set(xlabel="Body drive d (mm)",ylabel="Net weak normal force (N)",title="Original shared targets; HP80 audited prefix")
    axes[0,1].set(xlabel="Body drive d (mm)",ylabel="Net force minus C1 h=0.125 (N)",title="Model/boundary/grid differences, not physical errors")
    axes[1,0].set(xlabel="Reference x (mm), common node locations",ylabel="Weak normal reaction (N per node)",title="d=0.5 only; discrete support changes with mesh")
    axes[1,0].set_yscale("symlog",linthresh=1e-6)
    axes[1,1].axis("off")
    lines=[]
    for r in runs:
        lines.append(f"{r['label']}: {r['status']}; targets {sum(t['comparable'] for t in r['targets'])}/7")
        e=endpoint(r)
        if e is not None:
            lines.append(f"  d=0.5 body / whole mean: {float(e['body_bottom_mean_mm']):.6g} / {float(e['whole_bottom_mean_mm']):.6g} mm")
    lines += ["", "Unknown/failed targets are not plotted or interpolated.","Negative values are retained. Nodal force is not pressure.",
              "Arithmetic envelopes are in JSON; no physical-agreement gate."]
    axes[1,1].text(.01,.98,"\n".join(lines),va="top",fontsize=9)
    for ax in (axes[0,0],axes[0,1],axes[1,0]): ax.axhline(0,color=".5",lw=.6);ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.suptitle(f"C2 uniform diagnostics — {status} | planned / executed / admitted remain distinct")
    save_figure(fig,out,"force_and_status")

    fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    mesh=[(r,endpoint(r)) for r in runs if r["case_id"] in ("baseline_h025","baseline_h0125","mesh_h00625") and endpoint(r) is not None]
    mesh.sort(key=lambda pair:pair[0]["spec"]["h_mm"],reverse=True)
    for ax,name in zip(axes[0],("left_hat","right_hat")):
        ax.plot([r["spec"]["h_mm"] for r,_ in mesh],[float(e["functionals"][name]["values_N"]["total"]) for _,e in mesh],"o-",color="#216e8b")
        ax.set(title=f"Fixed reference {name}: sum(phi * weak reaction)",ylabel="N (work per 1 mm virtual amplitude)")
    axes[1,0].plot([r["spec"]["h_mm"] for r,_ in mesh],[float(e["negative_magnitude_N"]) for _,e in mesh],"o-",color="#a54b62")
    axes[1,0].set(title="Magnitude of negative weak nodal sum",ylabel="N",yscale="log")
    axes[1,1].plot([r["spec"]["h_mm"] for r,_ in mesh],[e["negative_node_count"] for _,e in mesh],"o-",color="#a54b62")
    axes[1,1].set(title="Negative node count (support changes with h)",ylabel="Count")
    for ax in axes.ravel(): ax.set_xlabel("h (mm)");ax.grid(alpha=.2)
    fig.suptitle(f"C2 mesh observations at d=0.5 — {status}\nFixed physical-scale virtual tests; no continuum-convergence claim")
    save_figure(fig,out,"fixed_support_mesh_observations")

    context=payload["saved_C1_field_context"]["analytic"]["cases"]
    fig,axes=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
    palette=("#216e8b","#248870","#a54b62","#b27530")
    for case,color in zip(context,palette):
        name=case["run"];mode="uniform" if "uniform" in name else "perturbation"
        h="0.125" if "h0125" in name else "0.25";label=mode+" h="+h
        ax=axes[0,0 if mode=="uniform" else 1]
        nodes=[n for n in case["all_top_nodes"] if -.55<=n["reference_x_mm"]<=0]
        x=[n["reference_x_mm"] for n in nodes]
        ax.plot(x,[float(n["weak_material_on_plane_N"]) for n in nodes],"o-",color=color,ms=3,label=label+" weak")
        ax.plot(x,[float(n["analytic_material_edge_on_plane_N"]) for n in nodes],"x--",color=color,ms=4,label=label+" direct analytic")
        observations=case["edge_quadrature_vs_analytic_observations"]
        axes[1,0].plot([8,16,32,64],[float(observations[f"gauss{n}_vs_analytic"]["normalized_error"]) for n in (8,16,32,64)],"o-",ms=3,color=color,label=label)
    for ax in axes[0]:
        ax.set_yscale("symlog",linthresh=1e-5);ax.set(xlabel="Reference x (mm)",ylabel="Material nodal quantity (N)")
        ax.axhline(0,color=".5",lw=.6);ax.grid(alpha=.2);ax.legend(fontsize=7)
    axes[0,0].set_title("Saved C1 uniform endpoints: weak vs direct material")
    axes[0,1].set_title("Saved C1 perturbation endpoints: weak vs direct material")
    axes[1,0].axhline(1e-8,color=".4",ls="--",label="Original observation threshold 1e-8")
    axes[1,0].set(xlabel="Gauss order per element edge",ylabel="Normal-vector error vs analytic / max(norm,1 N)",yscale="log",title="Gauss64 still above original threshold in all cases")
    axes[1,0].grid(alpha=.2);axes[1,0].legend(fontsize=7)
    axes[1,1].axis("off")
    axes[1,1].text(.02,.97,"Frozen C1 field evidence only\n\n144/144 element top edges satisfy the material\ncompression sign criterion; direct normal nodal\nprojections are positive.\n\nWeak minus direct-Simpson decomposes into\nother external edges + internal jumps − projected\ndiv(P interpolant), with explicit weight correction.\n\nThis does not establish true contact pressure,\nunilateral complementarity, or the same sign for C2.",va="top",fontsize=10)
    fig.suptitle("Saved-field interpretation | original diagnostics preserved; analytic integration resolves narrow material layers")
    save_figure(fig,out,"saved_fields_and_analytic_integration")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",required=True,type=Path)
    parser.add_argument("--root",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args(argv)
    out=args.output.resolve()
    if out.exists(): raise FileExistsError("refusing to overwrite summary directory")
    payload,reader=make_summary(args.root,args.protocol)
    out.mkdir(parents=True)
    with (out/"summary.json").open("x",encoding="utf-8") as stream:
        json.dump(plain(payload),stream,indent=2,allow_nan=False);stream.write("\n")
    plots(payload,out)
    for name,expected in reader.bindings.items():
        if digest(reader.root/name)!=expected: raise ValueError("input changed during summary: "+name)
    with (out/"output_sha256.json").open("x",encoding="utf-8") as stream:
        json.dump({p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()},stream,indent=2);stream.write("\n")
    print(json.dumps(dict(status=payload["status"],counts=payload["counts"],output=str(out))))
    return 0


if __name__=="__main__": raise SystemExit(main())
