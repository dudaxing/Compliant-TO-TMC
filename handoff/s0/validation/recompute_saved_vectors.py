"""Independent S0 readback of saved vectors and absorbing prefixes.

Imports only Python standard library and NumPy. No project, JAX, solver, or
constitutive evaluator is imported. Decimal norms compare existing saved HP
strings; they are not a new high-precision constitutive computation.
"""
from __future__ import annotations
import argparse
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

COMPONENTS = (
    ("total_force", "internal_force", "internal_decimal"),
    ("total_tangent", "production_tangent_action", "tangent_action_decimal"),
    ("material_force", "material_internal_force", "material_internal_decimal"),
    ("regularization_force", "regularization_internal_force", "regularization_internal_decimal"),
    ("material_tangent", "material_tangent_action", "material_tangent_action_decimal"),
    ("regularization_tangent", "regularization_tangent_action", "regularization_tangent_action_decimal"),
)

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def norm(values):
    return sum((value * value for value in values), Decimal(0)).sqrt()

def relation(value, limit, op):
    return {"<=": value <= limit, ">=": value >= limit, "<": value < limit,
            ">": value > limit, "==": value == limit}[op]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args=parser.parse_args()
    tree=args.tree.resolve()
    reference=json.loads(args.reference_manifest.read_text(encoding="utf-8"))
    expected={row["path"]:row for row in reference["files"]}
    inputs={}
    def bound(path):
        path=path.resolve()
        name=path.relative_to(tree).as_posix()
        if name not in inputs:
            item=expected[name]
            actual=sha(path)
            if actual!=item["sha256"] or path.stat().st_size!=item["bytes"]:
                raise ValueError(f"saved input identity mismatch: {name}")
            inputs[name]=actual
        return path
    def read(path):
        return json.loads(bound(path).read_text(encoding="utf-8"))
    rows=[]
    summaries=[]
    checks_total=checks_passed=recomputed_errors=0
    for case in ("padding_2p5", "outer_free", "mesh_h00625"):
        run=tree/"hf4_c2_diagnostics/experiments"/case
        audit=read(run/"audit.json")
        entries=read(run/"stages/uniform_tmc/steps/index.json")["steps"]
        assert len(entries)==len(audit["states"])
        active=True
        prefix_length=0
        valid_targets=[]
        state_passes=0
        invalid=[]
        for compact, entry, archived_prefix in zip(audit["states"],entries,audit["prefix"]["states"],strict=True):
            detail_path=bound(run/compact["detail_file"])
            assert inputs[detail_path.relative_to(tree).as_posix()]==compact["detail_sha256"]
            detail=json.loads(detail_path.read_text(encoding="utf-8"))
            state_path=bound(run/"stages/uniform_tmc/steps"/entry["file"])
            assert inputs[state_path.relative_to(tree).as_posix()]==entry["sha256"]
            assert compact["index"]==entry["index"]==detail["index"]
            with np.load(state_path,allow_pickle=False) as archive:
                arrays={name:archive[name].copy() for _,name,_ in COMPONENTS}
                # Preserve split data independently; never reconstruct a single
                # displacement vector as an input to a mechanics calculation.
                assert archive["u_lift"].dtype==archive["u_fluctuation"].dtype==np.dtype("float64")
                split_hashes={key:hashlib.sha256(archive[key].tobytes()).hexdigest() for key in ("u_lift","u_fluctuation")}
            calculations={}
            scalar_replay=[]
            with localcontext() as ctx:
                ctx.prec=120
                low=detail["precision_evidence_decimal"]["80"]
                high=detail["precision_evidence_decimal"]["120"]
                sf=Decimal(low["force_scale_decimal"])
                for name,key,hpkey in COMPONENTS:
                    actual=arrays[key]
                    reference_values=list(map(Decimal,low[hpkey]))
                    other=list(map(Decimal,high[hpkey]))
                    assert len(actual)==len(reference_values)==len(other)
                    assert actual.dtype==np.dtype("float64") and np.isfinite(actual).all()
                    absolute=norm([Decimal.from_float(float(a))-b for a,b in zip(actual,reference_values,strict=True)])
                    reference_norm=norm(reference_values)
                    if name=="total_force":
                        denominator=sf
                    elif name.endswith("force"):
                        denominator=max(reference_norm,Decimal("1e-12")*sf)
                    else:
                        denominator=max(reference_norm,Decimal("1e-10"))
                    relative=absolute/denominator
                    cross_absolute=norm([a-b for a,b in zip(other,reference_values,strict=True)])
                    cross=cross_absolute/denominator
                    calculated=dict(absolute_error=absolute,reference_norm=reference_norm,denominator=denominator,
                        relative_error=relative,cross_precision_absolute_error=cross_absolute,cross_precision_relative_error=cross)
                    recorded=detail["measurements"]["component_precision"][name]
                    assert all(Decimal(recorded[k])==v for k,v in calculated.items()), (case,entry["index"],name)
                    calculations["production_vs_hp80_"+name]=relative
                    calculations["hp80_vs_hp120_"+name]=cross
                for check in detail["checks"]:
                    value=calculations.get(check["name"],Decimal(check["value"]))
                    assert value==Decimal(check["value"])
                    passed=relation(value,Decimal(check["limit"]),check["relation"])
                    assert passed==(check["status"]=="pass")
                    scalar_replay.append(passed)
                    checks_total+=1
                    checks_passed+=int(passed)
                recomputed_errors+=len(calculations)
            passed=all(scalar_replay)
            assert passed==(detail["status"]==compact["status"]=="pass")
            state_passes+=int(passed)
            active=active and passed
            assert active==compact["valid_prefix_comparable"]==archived_prefix["comparable"]
            if active:
                prefix_length+=1
                assert archived_prefix["normal_force"]==detail["normal_force_raw"]
                if entry["is_original_target"]:
                    valid_targets.append(entry["d"])
            else:
                assert archived_prefix["normal_force"] is None
                invalid.append(compact["state_id"])
            rows.append(dict(case_id=case,state_id=compact["state_id"],parameter_s=entry["d"],
                status="pass" if passed else "not_pass",valid_prefix_comparable=active,
                split_array_sha256=split_hashes,errors={k:str(v) for k,v in calculations.items()},
                checks_count=len(scalar_replay),passed_checks=sum(scalar_replay)))
        assert prefix_length==audit["prefix"]["prefix_length"]
        summaries.append(dict(case_id=case,states=len(entries),passed_states=state_passes,
            prefix_length=prefix_length,valid_original_targets=valid_targets,invalid_states=invalid))
    assert len(rows)==59 and sum(x["status"]=="pass" for x in rows)==58
    assert (checks_total,checks_passed,recomputed_errors)==(1810,1809,708)
    assert not any(name=="jax" or name.startswith("hf_eval") for name in sys.modules)
    result=dict(schema="hf4-c2-s0-saved-vector-replay-1.0",status="pass",tree=str(tree),
        validation_means="Archived identities, vector errors, saved scalar comparisons and absorbing prefixes agree; the historical failing state remains failed.",
        script_sha256=sha(Path(__file__)),reference_manifest_sha256=sha(args.reference_manifest),
        no_new_fe_path=True,no_project_import=True,no_constitutive_evaluation=True,
        limitation="708 vector comparisons independently recomputed. Remaining 1102 gates replay stored scalar values and thresholds; this is not a new constitutive or geometric evaluation, nor new execution admission.",
        states=len(rows),passed_states=58,checks_replayed=checks_total,checks_passed=checks_passed,
        vector_comparisons_recomputed=recomputed_errors,cases=summaries,rows=rows,input_sha256=inputs)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
        stream.write("\n")
    print(json.dumps({k:result[k] for k in ("status","states","passed_states","checks_replayed","checks_passed","vector_comparisons_recomputed","cases")}))

if __name__=="__main__":
    main()
