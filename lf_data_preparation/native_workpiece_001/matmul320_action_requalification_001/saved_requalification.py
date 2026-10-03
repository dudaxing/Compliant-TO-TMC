"""Requalify a changed tangent-action consumer using immutable saved F/T and HP.

This is a new data requalification, not a retry of the failed reference phase.
No fresh force, tangent, Decimal reference, equilibrium or contact qualification.
"""
from time import perf_counter
STARTED = perf_counter()
import argparse
from decimal import Decimal, Inexact, localcontext
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import psutil
from scipy import sparse

STAGE = "lf_data_preparation/native_workpiece_001/matmul320_candidate_001"
HELPER_SHA = "3e302022c0f5e253daa38cdfdf9ef900c27b52d804f08f173fbd3db12a9098a9"
ORIGINAL_FILES = {
    "check/candidate/result.json": "320f26bb219a884e697ebd534868e96dab17570de05352c8b3cc60ae8fcae997",
    "check/candidate/fixture.npz": "b69a0b1aa0cb22f0f5fd8dbad37026d136e35d75a37cb44e3abc637cfcdcb38b",
    "check/candidate/arrays.npz": "b7b455a36651416594c4f5f8086907ab5e0357e5bfa3db3eccf6994b37596db7",
    "check/candidate/force_fields.npz": "dd0f022712c123f97cd163b63bd8fddd390616d7c990493b27cdb8b046295e97",
    "check/reference/result.json": "1c3aaf8b67efba42958b91eab7b951fee948d3c4590d774a5bb09b1afb71b707",
    "check/reference/reference_fixture.npz": "67ba48eb995736c0a98313108c3c429e595f5c3fd2bbfb1a4901d1bc0d85172f",
    "check/reference/hp80.json.gz": "7a11e6ca1075a39dacee6c1d218c180534fe1e4fff65f737cb420245f55bd839",
    "check/reference/hp120.json.gz": "cd44231efc6ae292f8a670fff3c5499933a250cc073ace23f56b1f143b09a976",
    "reference_launch.json": "a679d5a9480882c1f213962146859203419d556fcb35f481a4b5582b204d9d71"}
PEAK, OUTPUT = 0, None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checkpoint():
    global PEAK
    process, memory = psutil.Process(), 0
    for member in [process, *process.children(recursive=True)]:
        try:
            info = member.memory_info()
            memory += max(info.rss, getattr(info, "peak_wset", info.rss))
        except psutil.NoSuchProcess:
            pass
    PEAK = max(PEAK, memory)
    if PEAK > 8*1024**3 or perf_counter()-STARTED > 120 or (OUTPUT.parent/"stop_requested.txt").exists():
        raise RuntimeError("Cooperative requalification resource/stop limit reached")


def run(args, report, checks, differences):
    root, repo = args.production_root.resolve(), args.repo.resolve()
    stage = root/STAGE
    candidate, reference = stage/"check/candidate", stage/"check/reference"
    helper_file = candidate/"sources/validate_matmul320.py"
    assert sha(helper_file) == HELPER_SHA, "Frozen pure comparison helper changed"
    spec = importlib.util.spec_from_file_location("saved_comparison_helpers", helper_file)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)  # Pure utilities only; candidate/reference functions never called.
    metadata, old = h.read(candidate/"result.json"), h.read(reference/"result.json")
    launch = h.read(stage/"reference_launch.json")
    assert metadata["status"] == "pass" and old["status"] == "fail" and launch["exit_code"] == 1 and launch["invocations"] == 1
    assert old["call_counts"]["HP_started"] == old["call_counts"]["HP_completed"] == 2
    pins = {root/k:v for k,v in metadata["bindings"].items()}
    pins.update({candidate/"sources"/k:v for k,v in metadata["source_bindings"].items()})
    pins.update({stage/k:v for k,v in ORIGINAL_FILES.items()})
    for name,pin in h.HP_HASHES.items(): pins[reference/"sources"/(name+".py")] = pin
    consumer = repo/"src/hf_eval/tangent_action.py"
    for path in [Path(__file__).resolve(), consumer, *[repo/"src/hf_eval"/name for name in ("compensated_invariants.py","tmc_kernel.py","__init__.py")]]:
        pins[path] = sha(path)
    for name in ("compensated_invariants.py","tmc_kernel.py","__init__.py"): assert sha(repo/"src/hf_eval"/name) == metadata["source_bindings"][name]
    for item in [metadata[k] for k in ("fixture","arrays","force_fields")]+list(metadata["matrices"].values()): pins[candidate/item["path"]] = item["sha256"]
    assert all(sha(path)==pin for path,pin in pins.items()), "Before-call immutable bindings failed"
    report.update(bindings={p.resolve().relative_to(root).as_posix():v for p,v in pins.items()}, inherited_candidate_counts=metadata["call_counts"],
        inherited_reference_counts=old["call_counts"], inherited_reference_status="fail_preserved", inherited_reference_error=old["error"],
        inherited_HP_source_hashes=h.HP_HASHES, original_HP_is_fresh_for_this_phase=False)
    fixture, actual, saved_hp_fixture = h.npz(candidate/"fixture.npz"), h.npz(candidate/"arrays.npz"), h.npz(reference/"reference_fixture.npz")
    ne, ndof, edofs = len(fixture["edofs"]), len(fixture["direction"]), fixture["edofs"]
    assert (ne,ndof)==(3200,6642) and float(fixture["force_scale_per_length"])==20.
    for key in ("fixture","arrays","force_fields"): assert h.fields(h.npz(candidate/metadata[key]["path"]))==metadata[key]["fields"]
    for key in ("grad","hessian","weights","lam","mu","kr"): h.same(fixture[key],saved_hp_fixture[key],"HP fixture "+key)
    for key in ("lift","fluctuation","direction"): h.same(fixture[key][edofs].ravel(),saved_hp_fixture[key],"HP local "+key)
    h.same(edofs,saved_hp_fixture["actual_edofs"],"HP shared numbering")
    h.same(np.arange(4*ne,dtype=np.int64).reshape(ne,4),saved_hp_fixture["connectivity"],"HP disconnected numbering")
    hp = {}
    for precision in (80,120):
        with gzip.open(reference/f"hp{precision}.json.gz","rt",encoding="utf-8") as stream: stored = json.load(stream)
        assert stored["precision"]==precision
        hp[precision] = {key:[Decimal(x) for x in stored["values"][key]] for key in (*h.HP_FORCES,*h.HP_ACTIONS)}
        assert all(len(values)==8*ne and all(x.is_finite() for x in values) for values in hp[precision].values())
    sys.path.insert(0,str(repo/"src"))
    from hf_eval.tangent_action import apply_element_tangent_numpy
    actions = {}
    for part in h.PARTS:
        checkpoint()
        report["action_consumer_started"] += 1
        value = apply_element_tangent_numpy(actual[part+"_tangent"],fixture["local_direction"])
        report["action_consumer_completed"] += 1
        assert value.shape==(ne,8) and value.dtype==np.float64 and np.isfinite(value).all()
        actions[part+"_action"] = value
        full = np.zeros(ndof)
        np.add.at(full,edofs.ravel(),value.ravel())
        actions["global_"+part+"_action"] = full
    np.savez_compressed(OUTPUT/"actions.npz",**actions)
    report["actions"] = h.archive(OUTPUT/"actions.npz",actions)
    with localcontext() as context:
        context.prec = 120
        floor = Decimal("1e-8")*Decimal.from_float(float(fixture["force_scale_per_length"]))*Decimal("1e-6")
        assert floor==Decimal(metadata["force_scale_floor_N"])==Decimal("2e-13")
        for element in range(ne):
            if element%128==0: checkpoint()
            span = slice(8*element,8*element+8)
            scale = max(h.norm(hp[80][h.HP_FORCES[0]][span]),floor)
            for i,part in enumerate(h.PARTS):
                for kind,key,value,limit in (("force",h.HP_FORCES[i],actual[h.FORCES[i]][element],Decimal("1e-11" if i==0 else "1e-9")),("action",h.HP_ACTIONS[i],actions[part+"_action"][element],Decimal("1e-10" if i==0 else "1e-9"))):
                    expected, other = hp[80][key][span], hp[120][key][span]
                    denominator = (scale if i==0 else max(h.norm(expected),Decimal("1e-12")*scale)) if kind=="force" else max(h.norm(expected),Decimal("1e-10"))
                    gate,delta = h.compare(value,expected,other,denominator,limit)
                    checks.append(dict(scope="local",element=element,component=part,kind=kind,**gate))
                    differences.append(dict(scope="local",element=element,component=part,kind=kind,values=list(map(str,delta))))
                    assert gate["pass_gate"], f"First local gate failed: element{element} {part} {kind}"
    globals_hp = {precision:{} for precision in (80,120)}
    with localcontext() as context:
        context.prec, context.traps[Inexact] = 3000, True
        for precision in (80,120):
            for key,values in hp[precision].items():
                full = [Decimal(0)]*ndof
                for element,dofs in enumerate(edofs):
                    if element%256==0: checkpoint()
                    for local,dof in enumerate(dofs): full[int(dof)] += values[8*element+local]
                globals_hp[precision][key] = full
    h.gzip_write(OUTPUT/"inherited_HP_globals.json.gz",globals_hp)
    with localcontext() as context:
        context.prec = 120
        scale = max(h.norm(globals_hp[80][h.HP_FORCES[0]]),floor)
        for i,part in enumerate(h.PARTS):
            record = metadata["matrices"][part]
            matrix = sparse.load_npz(candidate/record["path"])
            assert matrix.format=="csc" and matrix.shape==(ndof,ndof) and h.fields({k:getattr(matrix,k) for k in ("data","indices","indptr")})==record["fields"]
            shape = (ne,8,8)
            rebuilt = sparse.coo_matrix((actual[part+"_tangent"].ravel(),(np.broadcast_to(edofs[:,:,None],shape).ravel(),np.broadcast_to(edofs[:,None,:],shape).ravel())),shape=(ndof,ndof)).tocsc()
            rebuilt.sum_duplicates()
            for key in ("data","indices","indptr"): h.same(getattr(matrix,key),getattr(rebuilt,key),"Full CSC "+part+key)
            force = np.zeros(ndof)
            np.add.at(force,edofs.ravel(),actual[h.FORCES[i]].ravel())
            h.same(force,actual["global_"+part+"_force"],"Saved global force "+part)
            h.same(matrix@fixture["direction"],actual["CSC_"+part+"_action"],"Saved CSC action "+part)
            for kind,key,value,limit in (("force",h.HP_FORCES[i],force,Decimal("1e-11" if i==0 else "1e-9")),("action",h.HP_ACTIONS[i],actions["global_"+part+"_action"],Decimal("1e-10" if i==0 else "1e-9")),("CSC_action",h.HP_ACTIONS[i],actual["CSC_"+part+"_action"],Decimal("1e-10" if i==0 else "1e-9"))):
                expected, other = globals_hp[80][key], globals_hp[120][key]
                denominator = (scale if i==0 else max(h.norm(expected),Decimal("1e-12")*scale)) if kind=="force" else max(h.norm(expected),Decimal("1e-10"))
                gate,delta = h.compare(value,expected,other,denominator,limit)
                checks.append(dict(scope="global",component=part,kind=kind,**gate))
                differences.append(dict(scope="global",component=part,kind=kind,values=list(map(str,delta))))
                assert gate["pass_gate"], "First global gate failed: "+part+" "+kind
    checkpoint()
    assert all(sha(path)==pin for path,pin in pins.items()), "Final immutable bindings failed"
    report.update(status="pass",local_gate_count=6*ne,global_gate_count=9,CSC_storage_coefficients_checked=3*64*ne,
        force_floor_N=str(floor),action_floor_N_per_mm="1e-10",reference_agreement_limit="1e-40",
        worst={kind:{part:max((r for r in checks if r["kind"]==kind and r["component"]==part),key=lambda r:Decimal(r["normalized_error"])) for part in h.PARTS} for kind in ("force","action","CSC_action")},
        maximum_inherited_HP_agreement=max((r["hp80_hp120_error"] for r in checks),key=Decimal),all_bindings_unchanged=True)


def main():
    global OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("production-root","repo","output"): parser.add_argument("--"+name,required=True,type=Path)
    args = parser.parse_args()
    OUTPUT = args.output.resolve()
    OUTPUT.mkdir()
    report = dict(status="running",schema_version="saved-tangent-action-requalification-1.0",invocations=1,
        seconds_limit=120,outer_seconds=150,sampled_RSS_limit_bytes=8*1024**3,action_consumer_started=0,action_consumer_completed=0,
        new_call_counts=dict(force=0,tangent=0,HP=0,solver=0,JIT=0),changed_method="Compensated consumer of saved binary64 element tangent tensors",
        scope="New action method and data requalification; original failed phase unchanged, no fresh HP or physical solve",
        equilibrium_qualified=False,contact_qualified=False,all_tangent_columns_HP_qualified=False,stress_HP_qualified=False)
    checks, differences = [], []
    try:
        checkpoint()
        run(args,report,checks,differences)
    except Exception as error:
        report.update(status="fail",error=dict(type=type(error).__name__,message=str(error)))
    for name,value in (("checks",checks),("differences",differences)):
        with gzip.open(OUTPUT/(name+".json.gz"),"xt",encoding="utf-8") as stream: json.dump(value,stream)
    try:
        checkpoint()
        assert all(sha(args.production_root.resolve()/path)==pin for path,pin in report.get("bindings",{}).items()), "After-save immutable bindings failed"
    except Exception as error: report.update(status="fail",final_resource_error=str(error))
    report.update(elapsed_seconds=perf_counter()-STARTED,peak_sampled_tree_bytes=PEAK,files={p.name:sha(p) for p in OUTPUT.iterdir() if p.is_file()})
    (OUTPUT/"result.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({key:report[key] for key in ("status","new_call_counts","action_consumer_completed","elapsed_seconds")}),flush=True)
    return 0 if report["status"]=="pass" else 1


if __name__=="__main__":
    raise SystemExit(main())
