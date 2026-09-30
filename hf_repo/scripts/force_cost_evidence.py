"""Standard-library-only preparation and saved-evidence checks for F-COST1.

No scientific import, subprocess, array decoding, patch application or profiling.
The parent owns the only wall/RSS window. Historical recovery is selective.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
from html import escape
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
import zipfile

from s0_event_log import EventLog, EventLogError
from s0_preparation_evidence import bound, checked, copy_row, path, read, require, sha, utc, write

PROTOCOL = "F-COST1"
RUN_ID = "force_cost_001"
PRIOR_RUN = "force_reuse_002"
PREFIX = "provenance/" + PRIOR_RUN + "/"
PRIOR_BINDING_SHA = "b223ad7b85c9b3f561ffcb609fd8155866cee9e4f368dc4cd2dde3da00f4f856"
R1_SHA = "630babc9c299ef2336835df18a50521f51d439dc09e3353ae6d0776d91937970"
CI_SHA = "6a0144a92bf323951594a0d677b7558cf2a6501667f4b076dd13e2df6bba3897"
HR1_SHA = "28e696175d572379527e6a021365dacf445fa4dd28f73cb381925d95bfb383d5"
H1_SHA = "15a81049f3fadcf0a0391f702db8444c33856f1116055d26e6ffca686821e946"
INPUT_SHA = "2ba110b878186e52996c25f4aad44cb81858be15303c21579c4f5e8ccc013448"
REFERENCE_SHA = "ee053018a911b45e78e9f821d9bf25f870fb9a81e3b17ee72dc4d27ae3868d4e"
SUP1_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
SUP2_SHA = "b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499"
HELPER_SHA = "2d378c64705461d58fa966528a347b6e411431402877663fd546f3fec8912f45"
SOURCE = "R1/source/hf_repo"
HR1_TEST = "aux/hf_repo/tests/test_force_reuse_contract.py"
H1_TEST = "H1/tests/test_compensated_invariants.py"
REFERENCE = PREFIX + "results/local/micro_valid_first_three.npz"
CPU_FILE = "events/P1_cost_cpu.ndjson"
PROBE_EVENTS = "events/P1_cost.ndjson"
HISTORY = (
    "receipt_binding.json", "execution_receipt.json", "output_sha256.json", "input_manifest.json",
    "plan.json", "selected_source.json", "local_verification.json", "results/local/summary.json",
    "results/local/contract.json", "results/local/contract_binding.json", "results/local/micro_valid_first_three.npz",
    "events/P1_local.ndjson", "results/P1_supervision/receipt.json", "results/P1_supervision/instances.ndjson",
    "supervision_proof.json",
)
FIXED_AUX = {
    "windows_owned_process.py": SUP1_SHA, "windows_owned_process_sup2.py": SUP2_SHA,
    "cpu_supervision_evidence.py": HELPER_SHA,
    "probe_s0_preparation.py": "bdd3d6c1f3b933de9268f9a7a64e67d7ddc96697f15ac8e237047fdc74abfd98",
    "s0_preparation_evidence.py": "666540e91569bfabef88a48399a80c6d5809401d39660231c2e6a203f2640ec9",
    "s0_event_log.py": "7f305d479d3f19216a7339eeb25c8c7ce24372a0f68c6492b265f90ac1b62c90",
    "s0_ad_exception.py": "03107b0b6f7142837833a4ad367550dbbbb523e0222316093624d66d939acb7d",
}
CURRENT_AUX = ("hf_repo/scripts/run_force_cost.py", "hf_repo/scripts/probe_force_cost.py",
    "hf_repo/scripts/force_cost_evidence.py", "docs/CURRENT_STATUS.md", "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md")
SUPPLEMENTAL = {
    "jax/_src/config.py": (85756, "988855751b42308e6074da3c575c258a25c242e1082707e958d5af435ebc02d1"),
    "jax/_src/xla_bridge.py": (45866, "0fc3de635a0e78e94bebf0187ce3068ed1499504eda7e936f1f1dd8f6fb40d87"),
}
PACKAGES = {"numpy": "2.4.6", "jax": "0.11.0", "jaxlib": "0.11.0", "pytest": "9.1.1", "psutil": "7.2.2"}
EXCLUDED = {"output_sha256.json", "receipt_binding.json", "execution_receipt.json", "ledger.json",
    "events/P3_seal.ndjson", "logs/P3_seal.log"}
STAGES = ("interval_controls", "source_binding", "environment_snapshot", "runtime_import", "kernel_import",
    "harness_import", "input_prepare", "input_ready") + tuple(
    graph + "." + action for graph in ("tiny", "micro")
    for action in ("trace", "export_jaxpr", "lower", "export_stablehlo", "compile", "export_optimized_hlo")) + tuple(
    name + "." + action for name in ("tiny_before", "micro_first", "micro_repeat", "tiny_after")
    for action in (("call", "synchronize", "ready_only", "transfer", "save_output", "compare")
                   if name in ("tiny_before", "micro_first") else
                   ("call", "synchronize", "transfer", "save_output", "compare"))) + ("source_preservation",)


def failure(error):
    return dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())


def binary_write(filename, data):
    filename = path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("xb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def record(root, filename):
    filename = path(filename)
    return dict(path=filename.relative_to(root).as_posix(), bytes=filename.stat().st_size, sha256=sha(filename))


def roles(root, repo):
    return dict(parent_supervisor=dict(version="SUP1", path=str(root/"aux/hf_repo/scripts/windows_owned_process.py"), sha256=SUP1_SHA),
        candidate_supervisor=dict(version="SUP2", path=str(root/"aux/hf_repo/scripts/windows_owned_process_sup2.py"), sha256=SUP2_SHA),
        loaded_parent_supervisor=dict(version="SUP1", path=str(repo/"hf_repo/scripts/windows_owned_process.py"), sha256=SUP1_SHA))


def assert_micro_ast(hr1_path, probe_path):
    """Compare the entire nested reused function, without compiling/importing it."""
    nodes = []
    for filename in (hr1_path, probe_path):
        tree = ast.parse(path(filename).read_text(encoding="utf-8"))
        found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "reused"]
        require(len(found) == 1, "expected exactly one reused function in " + str(filename))
        nodes.append(ast.dump(found[0], include_attributes=False))
    require(nodes[0] == nodes[1], "diagnostic reused function AST differs from frozen HR1")
    return dict(status="pass", ast_sha256=hashlib.sha256(nodes[0].encode()).hexdigest(),
        hr1_sha256=sha(hr1_path), probe_sha256=sha(probe_path), globals_rewritten=False)


def historical_authority(get):
    checked(get("receipt_binding.json"), PRIOR_BINDING_SHA)
    binding = read(get("receipt_binding.json"))
    for key, name in (("output_manifest_sha256", "output_sha256.json"), ("input_manifest_sha256", "input_manifest.json"),
                      ("receipt_sha256", "execution_receipt.json")):
        checked(get(name), binding[key])
    output = read(get("output_sha256.json"))
    rows = []
    for name in HISTORY:
        file = get(name)
        if name not in ("receipt_binding.json", "output_sha256.json", "execution_receipt.json"):
            checked(file, output[name])
        rows.append(dict(original_path=name, path=PREFIX+name, bytes=file.stat().st_size, sha256=sha(file)))
    require(len(rows) == 15 and sum(r["bytes"] for r in rows) == 1172966, "selected historical subset differs")
    return rows, read(get("input_manifest.json")), output


def source_specs(root, repo, *, archived=False):
    """Construct exact mappings from selected frozen authority, never old row.source."""
    old = root.parent/PRIOR_RUN
    get = (lambda n: bound(root, PREFIX+n)) if archived else (lambda n: bound(old, n))
    history, previous, output = historical_authority(get)
    specs = []
    def add(name, source, digest=None, size=None, role="inherited_original"):
        specs.append(dict(path=name, source=str(path(source)), sha256=digest, bytes=size, role=role))
    for row in history:
        add(row["path"], old/row["original_path"], row["sha256"], row["bytes"], "selected_history")
    inherited = previous["inherited_candidate_files"]
    require(previous["derived_files"] == [] and previous["new_patch_applications"] == 0
            and len(inherited) == 32 and sum(r["bytes"] for r in inherited) == 380009, "prior R1 inventory differs")
    old_inputs = {r["path"]: r for r in previous["files"]}
    for row in inherited:
        require(row["path"].startswith(SOURCE+"/") and all(row[k] == old_inputs[row["path"]][k] for k in ("bytes", "sha256")),
                "R1 not bound by predecessor original inputs")
        add(row["path"], old/row["path"], row["sha256"], row["bytes"], "inherited_R1")
    for name in ("R1/source_manifest.json", "HR1/manifest.json", "H1/manifest.json"):
        add(PREFIX+name, old/name, output[name], None, "archived_position_metadata")
    for name, digest in ((HR1_TEST, HR1_SHA), (H1_TEST, H1_SHA), ("data/inputs.npz", INPUT_SHA)):
        require(output[name] == digest, "fixed scientific/harness source differs")
        add(name, old/name, digest)
    for filename, digest in FIXED_AUX.items():
        name = "aux/hf_repo/scripts/" + filename
        require(output[name] == digest, "fixed auxiliary source differs")
        add(name, old/name, digest, None, "fixed_auxiliary")
    runtime = []
    site = path(previous["python"]["executable"]).parent.parent/"Lib/site-packages"
    old_runtime_prefix = "provenance/force_cpu_observe_001/aux/runtime/"
    runtime_rows = [r for r in previous["files"] if r["path"].startswith(old_runtime_prefix+"jax/")]
    require(len(runtime_rows) == 9, "prior JAX source count differs")
    for row in runtime_rows:
        rel = row["path"].removeprefix(old_runtime_prefix)
        destination = "aux/runtime/"+rel
        add(destination, old/row["path"], row["sha256"], row["bytes"], "frozen_JAX_source")
        runtime.append(dict(path=str(site/rel), frozen_path=destination, bytes=row["bytes"], sha256=row["sha256"]))
    for row in previous["runtime_file_checks"] + previous["stdlib_file_checks"]:
        rel = ("psutil/"+row["package_relative_path"]) if row.get("package") == "psutil" else "stdlib/subprocess.py"
        destination = "aux/runtime/"+rel
        add(destination, row["path"], row["sha256"], row["bytes"], "fixed_installed_source")
        runtime.append(dict(path=row["path"], frozen_path=destination, bytes=row["bytes"], sha256=row["sha256"]))
    for rel, (size, digest) in SUPPLEMENTAL.items():
        destination = "aux/runtime/"+rel
        add(destination, site/rel, digest, size, "new_supplemental_config_source")
        runtime.append(dict(path=str(site/rel), frozen_path=destination, bytes=size, sha256=digest))
    for name in CURRENT_AUX:
        add("aux/"+name, repo/name, None, None, "current_diagnostic_auxiliary")
    require(len(specs) == len({r["path"] for r in specs}) == 80, "diagnostic source inventory differs")
    return specs, history, previous, runtime


def harness_metadata(root, version):
    relative = HR1_TEST if version == "HR1" else H1_TEST
    return dict(version=version, manifest_path=str(root/version/"manifest.json"),
        manifest_sha256=sha(root/version/"manifest.json"), test_path=str(root/relative),
        test_sha256=HR1_SHA if version == "HR1" else H1_SHA)


def selected_metadata(root, manifest):
    return dict(schema="hf-force-cost-selected-1", protocol=PROTOCOL, campaign_protocol=PROTOCOL, run_id=RUN_ID,
        source_version="R1", source=SOURCE, hr1_test=HR1_TEST, reference_npz=REFERENCE, fixture="data/inputs.npz",
        input_manifest_sha256=sha(root/"input_manifest.json"), source_manifest_sha256=sha(root/"input_manifest.json"),
        harness=harness_metadata(root,"HR1"), arithmetic_harness=harness_metadata(root,"H1"),
        **roles(root,path(manifest["repo"])), scientific_admission=False)


def runtime_checks(manifest):
    require(path(sys.executable) == path(manifest["python"]["executable"])
            and sys.version == manifest["python"]["version"], "Python runtime differs")
    require(manifest["packages"] == PACKAGES, "package contract differs")
    for name, version in PACKAGES.items():
        require(importlib.metadata.version(name) == version, "installed package version differs: "+name)
    for row in manifest["runtime_files"]:
        checked(row["path"], row["sha256"], row["bytes"])


def prepare(root, repo, events):
    require(not any((root/n).exists() for n in ("input_manifest.json", "selected_source.json", "R1", "H1", "HR1")),
            "preparation must be write-once")
    specs, history, previous, runtime = source_specs(root,repo)
    rows = [copy_row(root, r["source"], r["path"], expected=r["sha256"], size=r["bytes"], role=r["role"]) for r in specs]
    inheritance = dict(schema="hf-force-cost-selective-inheritance-1", protocol=PROTOCOL, run_id=RUN_ID,
        previous_binding_sha256=PRIOR_BINDING_SHA, historical_files=15, historical_bytes=1172966, rows=history,
        predecessor_payload_total=407, full_predecessor_payload_verified=False,
        limitation="Only listed files and separately listed inherited sources are copied and checked; old row.source is not followed.")
    write(root/"inheritance_manifest.json", inheritance)
    r1_rows = [r for r in rows if r["role"] == "inherited_R1"]
    write(root/"R1/source_manifest.json", dict(schema="hf-force-cost-source-relocation-1",version="R1",source=SOURCE,
        files=[{k:r[k] for k in ("path","bytes","sha256")} for r in r1_rows], new_patch_applications=0,
        upstream=dict(path=PREFIX+"R1/source_manifest.json",sha256=sha(root/PREFIX/"R1/source_manifest.json")),
        archived_upstream_references_not_traversed=True,scientific_admission=False))
    for version, test, digest in (("H1",H1_TEST,H1_SHA),("HR1",HR1_TEST,HR1_SHA)):
        write(root/version/"manifest.json",dict(schema="hf-force-cost-harness-relocation-1",version=version,
            test_path=test,test_sha256=digest,test_bytes_changed=False,globals_rewritten=False,
            upstream=dict(path=PREFIX+version+"/manifest.json",sha256=sha(root/PREFIX/version/"manifest.json")),
            full_harness_executed=False,scientific_admission=False))
    ast_result = assert_micro_ast(root/HR1_TEST,root/"aux/hf_repo/scripts/probe_force_cost.py")
    config_tree=ast.parse((root/"aux/runtime/jax/_src/config.py").read_text(encoding="utf-8"))
    config_classes=[n for n in config_tree.body if isinstance(n,ast.ClassDef) and n.name == "Config"]
    require(len(config_classes) == 1 and any(isinstance(n,ast.FunctionDef) and n.name == "read"
            for n in config_classes[0].body),"pinned actual-config read API absent")
    generated = [record(root,root/name) for name in ("inheritance_manifest.json","R1/source_manifest.json","HR1/manifest.json","H1/manifest.json")]
    manifest = dict(schema="hf-force-cost-inputs-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,
        created_utc=utc(),repo=str(repo),files=rows,generated_metadata=generated,derived_files=[],new_patch_applications=0,
        inherited_candidate_files=32,historical_files=15,historical_bytes=1172966,**roles(root,repo),
        science=dict(version="R1",source=SOURCE,kernel_sha256=R1_SHA,arithmetic_sha256=CI_SHA),
        harness=harness_metadata(root,"HR1"),arithmetic_harness=harness_metadata(root,"H1"),
        canonical_files=previous["canonical_files"],python=previous["python"],packages=PACKAGES,runtime_files=runtime,
        inherited_supervision=previous["inherited_supervision"],micro_ast=ast_result,scientific_admission=False)
    plan=read(root/"plan.json")
    require(plan["protocol"] == plan["campaign_protocol"] == PROTOCOL and plan["run_id"] == RUN_ID
            and plan["seconds"] == 240 and all(plan[k] == v for k,v in roles(root,repo).items()),"parent prepare plan differs")
    require(plan["runner_sha256"] == sha(root/"aux/hf_repo/scripts/run_force_cost.py")
            and plan["evidence_worker_sha256"] == sha(root/"aux/hf_repo/scripts/force_cost_evidence.py"),"parent auxiliary pins differ")
    write(root/"input_manifest.json",manifest)
    write(root/"selected_source.json",selected_metadata(root,manifest))
    result = verify_inputs(root,include_live=True)
    events.emit("preparation_complete",files=80,input_manifest_sha256=result["input_manifest_sha256"])
    return dict(status="pass",source_verification=result,scientific_admission=False)


def verify_inputs(root, include_live=False):
    """Read-only SHA/metadata/AST checks; no obsolete upstream traversal."""
    root=path(root);manifest=read(root/"input_manifest.json");repo=path(manifest["repo"])
    require(manifest["schema"] == "hf-force-cost-inputs-1" and manifest["protocol"] == manifest["campaign_protocol"] == PROTOCOL
            and manifest["run_id"] == RUN_ID and root == repo/"hf4_c2_stable_f_validation"/RUN_ID,"input identity differs")
    specs, history, previous, runtime = source_specs(root,repo,archived=True)
    expected={r["path"]:r for r in specs};rows=manifest["files"]
    require(len(rows) == len({r["path"] for r in rows}) == 80 and {r["path"] for r in rows} == set(expected),"input set differs")
    for row in rows:
        spec=expected[row["path"]]
        require(path(row["source"]) == path(spec["source"]) and row["role"] == spec["role"],"source mapping differs")
        require((spec["sha256"] is None or row["sha256"] == spec["sha256"])
                and (spec["bytes"] is None or row["bytes"] == spec["bytes"]),"fixed source identity differs")
        checked(bound(root,row["path"]),row["sha256"],row["bytes"])
        if include_live:checked(row["source"],row["sha256"],row["bytes"])
    require(manifest["derived_files"] == [] and manifest["new_patch_applications"] == 0
            and manifest["inherited_candidate_files"] == 32 and manifest["runtime_files"] == runtime,"candidate/runtime contract differs")
    for row in manifest["generated_metadata"]:checked(bound(root,row["path"]),row["sha256"],row["bytes"])
    require({r["path"] for r in manifest["generated_metadata"]} == {"inheritance_manifest.json","R1/source_manifest.json","HR1/manifest.json","H1/manifest.json"},"generated metadata set differs")
    actual={f.relative_to(root).as_posix() for f in (root/SOURCE).rglob("*") if f.is_file()}
    require(actual == {r["path"] for r in rows if r["role"] == "inherited_R1"},"R1 inventory differs")
    checked(root/SOURCE/"src/hf_eval/split_kernel_invariants_hu.py",R1_SHA)
    checked(root/SOURCE/"src/hf_eval/compensated_invariants.py",CI_SHA)
    require(read(root/"selected_source.json") == selected_metadata(root,manifest),"selected source differs")
    require(manifest["harness"] == harness_metadata(root,"HR1") and manifest["arithmetic_harness"] == harness_metadata(root,"H1"),"harness metadata differs")
    require(all(manifest[k] == v for k,v in roles(root,repo).items()),"supervisor roles differ")
    require(assert_micro_ast(root/HR1_TEST,root/"aux/hf_repo/scripts/probe_force_cost.py") == manifest["micro_ast"],"micro AST binding differs")
    require(read(root/"inheritance_manifest.json")["rows"] == history,"historical selection differs")
    if include_live:
        require(manifest["canonical_files"] == previous["canonical_files"] and len(manifest["canonical_files"]) == 30,"canonical source set differs")
        for name,row in manifest["canonical_files"].items():
            require(path(row["path"]) == repo/"hf_repo"/name,"canonical source escaped repo")
            checked(row["path"],row["sha256"])
        canonical_inventory={"src/"+p.relative_to(repo/"hf_repo/src").as_posix()
                             for p in (repo/"hf_repo/src").rglob("*") if p.is_file() and "__pycache__" not in p.parts}
        require(canonical_inventory == {n for n in manifest["canonical_files"] if n.startswith("src/")},"canonical source inventory differs")
        previous_rows={r["path"]:r for r in previous["files"]}
        for name in ("run_force_cpu.py","probe_force_cpu.py","force_cpu_evidence.py"):
            checked(repo/"hf_repo/scripts"/name,previous_rows["aux/hf_repo/scripts/"+name]["sha256"])
        for name,digest in FIXED_AUX.items():checked(repo/"hf_repo/scripts"/name,digest)
        checked(repo/"hf_repo/tests/test_force_reuse_contract.py",HR1_SHA)
        runtime_checks(manifest)
    return dict(status="verified",input_manifest_sha256=sha(root/"input_manifest.json"),file_count=80,
        bytes=sum(r["bytes"] for r in rows),historical_files=15,historical_bytes=1172966,inherited_R1_files=32,
        derived_files=0,new_patch_applications=0,include_live=bool(include_live),scientific_admission=False)


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def analyze_cpu_interval(records, start, end):
    """Use all wholly contained consecutive query brackets; never rescue a sub-run."""
    result=dict(schema="hf-force-cost-cpu-interval-1",start=start,end=end,status="inconclusive",classification=None,
        integrity_valid=True,issues=[],quality_issues=[],segments=[],aggregate=None,
        thresholds=dict(min_dt_min_seconds=30,max_adjacent_dt_max_seconds=2.5,high_ratio=.5,low_ratio=.05))
    issues=result["issues"];quality=result["quality_issues"]
    if not finite(start) or not finite(end) or end <= start:issues.append("invalid_interval_boundary")
    if not isinstance(records,list) or not records:issues.append("missing_cpu_records");records=[]
    identity=records[0].get("identity") if records and isinstance(records[0],dict) else None
    observer=records[0].get("pid") if records and isinstance(records[0],dict) else None
    valid=[]
    for index,row in enumerate(records,1):
        errors=[]
        if not isinstance(row,dict):issues.append(dict(sequence=index,reason="nonobject_record"));valid.append(False);continue
        if row.get("schema") != "hf-job-cpu-telemetry-1" or row.get("sequence") != index:errors.append("schema_or_sequence")
        if (row.get("identity") != identity or not isinstance(identity,dict) or row.get("pid") != observer
                or not isinstance(observer,int) or isinstance(observer,bool) or observer <= 0):errors.append("observer_identity")
        a,b=row.get("query_start_monotonic"),row.get("query_end_monotonic")
        if not finite(a) or not finite(b) or a > b:errors.append("query_bracket")
        for key in ("total_user_time_100ns","total_kernel_time_100ns","ActiveProcesses","TotalProcesses"):
            value=row.get(key)
            if not isinstance(value,int) or isinstance(value,bool) or value < 0:errors.append(key)
        if not errors and row["ActiveProcesses"] > row["TotalProcesses"]:errors.append("active_exceeds_total")
        valid.append(not errors)
        if errors:issues.append(dict(sequence=index,reasons=errors))
    contained=[]
    if finite(start) and finite(end) and end > start:
        contained=[i for i,row in enumerate(records) if valid[i] and row["query_start_monotonic"] >= start and row["query_end_monotonic"] < end]
    for i in range(1,len(records)):
        if not valid[i-1] or not valid[i]:continue
        a,b=records[i-1],records[i]
        dt_min=b["query_start_monotonic"]-a["query_end_monotonic"]
        dt_max=b["query_end_monotonic"]-a["query_start_monotonic"]
        du=b["total_user_time_100ns"]-a["total_user_time_100ns"]
        dk=b["total_kernel_time_100ns"]-a["total_kernel_time_100ns"]
        inside=(i-1 in contained and i in contained)
        if dt_min <= 0:issues.append(dict(sequence=i+1,reason="query_brackets_overlap_or_reverse"))
        if du < 0 or dk < 0:issues.append(dict(sequence=i+1,reason="counter_reversed"))
        if b["TotalProcesses"] < a["TotalProcesses"]:issues.append(dict(sequence=i+1,reason="process_count_reversed"))
        if inside:
            result["segments"].append(dict(first_sequence=i,last_sequence=i+1,dt_min=dt_min,dt_max=dt_max,
                user_delta_100ns=du,kernel_delta_100ns=dk))
            if dt_max > 2.5:quality.append(dict(sequence=i+1,reason="gap_exceeds_2_5_seconds"))
    if len(contained) < 2:quality.append("fewer_than_two_contained_samples")
    else:
        first,last=contained[0],contained[-1]
        if contained != list(range(first,last+1)):issues.append("invalid_or_noncontained_internal_sample")
        a,b=records[first],records[last]
        dt_min=b["query_start_monotonic"]-a["query_end_monotonic"]
        dt_max=b["query_end_monotonic"]-a["query_start_monotonic"]
        dt=b["query_end_monotonic"]-a["query_end_monotonic"]
        ticks=(b["total_user_time_100ns"]-a["total_user_time_100ns"])+(b["total_kernel_time_100ns"]-a["total_kernel_time_100ns"])
        aggregate=dict(first_sequence=first+1,last_sequence=last+1,sample_count=len(contained),
            dt_min=dt_min,dt_max=dt_max,wall_seconds=dt,cpu_ticks_100ns=ticks)
        result["aggregate"]=aggregate
        if dt_min < 30:quality.append("coverage_under_30_seconds")
        if dt_min > 0 and dt > 0 and ticks >= 0:
            low,high=ticks*1e-7/dt_max,ticks*1e-7/dt_min
            aggregate.update(ratio_interval=[low,high],cpu_seconds_per_wall_second=ticks*1e-7/dt)
            if not issues and not quality:
                if low >= .5:result["classification"]="clear_cpu_consumption"
                elif high <= .05:result["classification"]="low_cpu"
                elif low > .05 and high < .5:result["classification"]="intermediate"
                else:quality.append("ratio_interval_crosses_threshold")
    result["integrity_valid"]=not issues
    result["status"]="invalid" if issues else ("classified" if result["classification"] else "inconclusive")
    return result


def interval_controls():
    """Four pure-record controls run by the same function used for real intervals."""
    def samples(count, gap=False):
        return [dict(schema="hf-job-cpu-telemetry-1",sequence=i+1,pid=1,identity=dict(synthetic=True),
            query_start_monotonic=float(i+(3 if gap and i >= 15 else 0)),
            query_end_monotonic=float(i+(3 if gap and i >= 15 else 0))+.001,
            total_user_time_100ns=i*10000000,total_kernel_time_100ns=0,ActiveProcesses=1,TotalProcesses=1) for i in range(count)]
    long=samples(34);short=samples(10);gap=samples(34,True);reverse=samples(34)
    reverse[16]["total_user_time_100ns"]=reverse[15]["total_user_time_100ns"]-1
    cases=[]
    for name,rows,end,status in (("long_coverage",long,35.,"classified"),("short_coverage",short,11.,"inconclusive"),
            ("long_gap",gap,38.,"inconclusive"),("counter_reversal",reverse,35.,"invalid")):
        actual=analyze_cpu_interval(rows,-1.,end)
        require(actual["status"] == status,"CPU interval control failed: "+name)
        require(actual["integrity_valid"] == (name != "counter_reversal"),"CPU control integrity classification differs")
        if name == "long_coverage":require(actual["classification"] == "clear_cpu_consumption","long control threshold differs")
        cases.append(dict(name=name,status="pass",expected_status=status,records=rows,analysis=actual))
    return dict(schema="hf-force-cost-interval-controls-1",status="pass",count=4,cases=cases,synthetic=True,
        scientific_admission=False,real_telemetry_failure=False)


def read_ndjson(filename):
    """Reject partial lines and bad records; preserve original bytes on failure."""
    data=path(filename).read_bytes()
    require(data and data.endswith(b"\n"),"missing or partial NDJSON: "+str(filename))
    rows=[]
    for line in data.decode("utf-8").splitlines():
        require(bool(line.strip()),"blank NDJSON record")
        row=json.loads(line)
        require(isinstance(row,dict),"nonobject NDJSON record")
        rows.append(row)
    return rows


def supervision_identity(root):
    selected=read(root/"selected_source.json")
    return dict(campaign_protocol=PROTOCOL,run_id=RUN_ID,phase="P1_cost",version="R1",science_version="R1",source_version="R1",
        source_manifest_sha256=selected["input_manifest_sha256"],harness_id="HR1",
        harness_manifest_sha256=selected["harness"]["manifest_sha256"],arithmetic_harness_id="H1",
        candidate_supervisor=selected["candidate_supervisor"],supervisor_version="SUP2",supervisor_sha256_role="P1_candidate")


def verify_supervision(root):
    """Validate the saved direct-SUP2 request/receipt/raw instance proof only."""
    root=path(root);selected=read(root/"selected_source.json");manifest=read(root/"input_manifest.json")
    repo=path(manifest["repo"]);folder=root/"results/P1_supervision"
    request,receipt=read(folder/"request.json"),read(folder/"receipt.json")
    expected=supervision_identity(root)
    require(request["schema"] == "hf-force-cost-supervision-request-1" and request["campaign_protocol"] == PROTOCOL
            and request["run_id"] == RUN_ID and request["identity"] == expected,"P1 request identity differs")
    require(all(request[k] == v for k,v in roles(root,repo).items()),"request supervisor roles differ")
    require(path(request["cwd"]) == root and request["seconds"] == 159.75 and request["rss_limit_bytes"] == 8*1024**3
            and request["telemetry_interval_seconds"] == 1.0 and request["telemetry_enabled"] is True,"P1 request budget differs")
    require(request["command"] == receipt["command"] and path(receipt["cwd"]) == root,"native request binding differs")
    require(receipt["deadline_monotonic"] == request["deadline_monotonic"] and receipt["timeout_seconds"] == 159.75
            and receipt["rss_limit_bytes"] == request["rss_limit_bytes"],"native limits differ from request")
    ledger=read(root/"ledger.json")
    require(ledger["protocol"] == PROTOCOL and ledger["run_id"] == RUN_ID and ledger["seconds"] == 240
            and ledger["scientific_admission"] is False,"parent ledger identity differs")
    phases=[p for p in ledger["phases"] if p.get("name") == "P1_cost"]
    require(len(phases) == 1,"P1 parent receipt missing or repeated")
    parent=phases[0]
    require(parent["native_receipt_sha256"] == sha(folder/"receipt.json")
            and parent["command"] == request["command"] and parent["active_deadline_monotonic"] == request["deadline_monotonic"]
            and parent["source_manifest_sha256"] == selected["input_manifest_sha256"]
            and parent["harness_manifest_sha256"] == selected["harness"]["manifest_sha256"]
            and parent["inclusive_phase_limit_seconds"] == 165 and parent["bucket"] == "P1","parent/native binding differs")
    require(request["deadline_monotonic"] == min(parent["phase_start_monotonic"]+159.75,ledger["deadline_monotonic"]-35.25),
            "P1 deadline differs from single-window reservation")
    for key,value in receipt.items():
        if key == "elapsed_seconds":require(parent["owned_elapsed_seconds"] == value,"native elapsed binding differs")
        else:require(parent[key] == value,"parent native receipt differs: "+key)
    require(path(receipt["cleanup_proof"]["journal"]["path"]) == folder/"instances.ndjson","instance path differs")
    require(receipt["supervisor_sha256"] == SUP2_SHA and receipt["cleanup_verified"] is True,"native cleanup/source failure")
    cleanup_start,cleanup_deadline=receipt["cleanup_requested_monotonic"],receipt["cleanup_deadline_monotonic"]
    require(finite(cleanup_start) and finite(cleanup_deadline) and 0 < cleanup_deadline-cleanup_start <= 5.
            and receipt["cleanup_proof"]["final_accounting"]["query_end_monotonic"] <= cleanup_deadline,
            "cleanup proof exceeded its same five-second deadline")
    import cpu_supervision_evidence as cleanup
    require(path(cleanup.__file__) == root/"aux/hf_repo/scripts/cpu_supervision_evidence.py","proof helper is not frozen")
    checked(cleanup.__file__,HELPER_SHA,71013)
    proof=cleanup.proof_evidence(root,folder,"receipt.json",receipt,expected)
    return dict(schema="hf-force-cost-supervision-proof-1",protocol=PROTOCOL,run_id=RUN_ID,status="verified_all_instances",
        native_protocol="F-CPU-CLEAN1",cleanup_contract="CPU-CLEAN1",request=record(root,folder/"request.json"),
        receipt=record(root,folder/"receipt.json"),instances=record(root,folder/"instances.ndjson"),
        identity=expected,proof=proof,parent_phase="P1_cost",scientific_admission=False)


def verify_record(root, item):
    require(isinstance(item,dict) and isinstance(item.get("bytes"),int) and item["bytes"] >= 0,"bad artifact metadata")
    target=bound(root,item["path"])
    checked(target,item["sha256"],item["bytes"])
    return target


def verify_probe_summary(root):
    """Strict success gate over saved statements/hashes; no array decoding."""
    root=path(root);summary=read(root/"results/cost/summary.json");selected=read(root/"selected_source.json")
    require(summary["schema"] == "hf-force-cost-probe-1" and summary["protocol"] == summary["campaign_protocol"] == PROTOCOL
            and summary["run_id"] == RUN_ID and summary["mode"] == "cost" and summary["source_version"] == "R1","probe identity differs")
    require(path(summary["source"]) == root/SOURCE and summary["source_manifest_sha256"] == selected["input_manifest_sha256"]
            and summary["harness"] == selected["harness"] and summary["arithmetic_harness"] == selected["arithmetic_harness"],"probe source binding differs")
    require(summary["status"] == "runtime_cost_diagnostic_complete" and summary["runtime_cost_diagnostic_complete"] is True
            and summary["scientific_admission"] is False and not summary["errors"],"probe did not complete diagnosis")
    steps=summary["steps"]
    require([r["stage"] for r in steps] == list(STAGES) and len(steps) == 43,"probe stage set/order differs")
    names=[r["stage"] for r in steps]
    counts=dict(graph_count=sum(n.endswith(".trace") for n in names),trace=sum(n.endswith(".trace") for n in names),
        lower=sum(n.endswith(".lower") for n in names),compile=sum(n.endswith(".compile") for n in names),
        compiled_call=sum(n.endswith(".call") for n in names),output_synchronization=sum(n.endswith(".synchronize") for n in names),
        ready_only=sum(n.endswith(".ready_only") for n in names),input_ready=names.count("input_ready"),micro_leaf_count=24)
    require(counts == dict(graph_count=2,trace=2,lower=2,compile=2,compiled_call=4,output_synchronization=4,ready_only=2,input_ready=1,micro_leaf_count=24)
            and summary["completed_counts"] == counts and summary["execution_contract"] == dict(counts,warmup=0,retries=0,force_calls=0,ad_calls=0),
            "declared/observed execution counts differ")
    previous=None
    for row in steps:
        a,b,c=row["started_monotonic"],row["execution_start_monotonic"],row["completed_monotonic"]
        require(row["status"] == "pass" and all(finite(x) for x in (a,b,c,row["elapsed_seconds"]))
                and a <= b <= c and (previous is None or previous <= a)
                and row["elapsed_seconds"] == c-b,"invalid stage completion/timing")
        previous=c
    events=read_ndjson(root/PROBE_EVENTS);expected_actions=[]
    for stage in STAGES:expected_actions.extend((("stage_started",stage),("stage_finished",stage)))
    observed=[];prior=None
    for index,row in enumerate(events,1):
        require(row["schema"] == "hf-s0-event-1" and row["sequence"] == index and row["phase"] == "P1_cost"
                and row["version"] == "R1" and row["source_manifest_sha256"] == selected["input_manifest_sha256"]
                and row["protocol"] == row["campaign_protocol"] == PROTOCOL and row["run_id"] == RUN_ID
                and row["harness_id"] == "HR1" and row["harness_manifest_sha256"] == selected["harness"]["manifest_sha256"],"probe event identity differs")
        require(finite(row["monotonic"]) and (prior is None or row["monotonic"] >= prior),"probe event clock reversed")
        prior=row["monotonic"]
        require(row["event"] not in ("stage_failed","probe_failed"),"success event stream contains a failure")
        if row["event"] in ("stage_started","stage_finished"):
            observed.append((row["event"],row["stage"]))
            step=steps[STAGES.index(row["stage"])]
            if row["event"] == "stage_finished":
                require(row["outcome"] == "pass" and row["duration"] == step["elapsed_seconds"]
                        and row["execution_start_monotonic"] == step["execution_start_monotonic"]
                        and row["completed_monotonic"] == step["completed_monotonic"],"event completion differs from summary")
            else:require(row["stage_start_monotonic"] == step["started_monotonic"],"stage marker differs")
    require(observed == expected_actions,"probe event stage count/order differs")
    require(events[0]["event"] == "probe_started" and events[-1]["event"] == "probe_finished"
            and events[-1]["outcome"] == "runtime_cost_diagnostic_complete","probe event terminal missing")
    require(len(events) == 114 and Counter(r["event"] for r in events) == dict(probe_started=1,stage_started=43,
            stage_finished=43,artifact_started=13,artifact_complete=13,probe_finished=1),"probe event counts differ")
    artifacts=summary["artifacts"]
    expected_artifacts={"interval_controls.json","environment.json","runtime_config.json",
        *(name+".npz" for name in ("tiny_before","micro_first","micro_repeat","tiny_after")),
        *(name+suffix for name in ("tiny","micro") for suffix in ("_raw_jaxpr.txt","_stablehlo.mlir","_optimized_hlo.txt"))}
    require(isinstance(artifacts,dict) and set(artifacts) == expected_artifacts,"expected six IR/four NPZ/three metadata artifacts")
    paths=[]
    for name,item in artifacts.items():
        require(item["status"] == "complete","diagnostic artifact incomplete")
        require(item["path"] == "results/cost/"+name,"artifact location differs")
        paths.append(verify_record(root,item).relative_to(root).as_posix())
        starts=[r for r in events if r["event"] == "artifact_started" and r["artifact"] == name]
        finishes=[r for r in events if r["event"] == "artifact_complete" and r["artifact"] == name]
        require(len(starts) == len(finishes) == 1 and starts[0]["sequence"] < finishes[0]["sequence"]
                and starts[0]["path"] == item["path"]+".partial" and starts[0]["artifact_status"] == "partial"
                and finishes[0]["artifact_status"] == "complete"
                and all(finishes[0][k] == item[k] for k in ("path","bytes","sha256")),"artifact event binding differs")
        if name in ("interval_controls.json","environment.json","runtime_config.json"):
            stage={"interval_controls.json":"interval_controls","environment.json":"environment_snapshot","runtime_config.json":"runtime_import"}[name]
        elif name.endswith(".npz"):stage=name.removesuffix(".npz")+".save_output"
        else:
            suffix=next(s for s in ("_raw_jaxpr.txt","_stablehlo.mlir","_optimized_hlo.txt") if name.endswith(s))
            stage=name.removesuffix(suffix)+{"_raw_jaxpr.txt":".export_jaxpr","_stablehlo.mlir":".export_stablehlo","_optimized_hlo.txt":".export_optimized_hlo"}[suffix]
        step=steps[STAGES.index(stage)]
        require(step["execution_start_monotonic"] <= starts[0]["monotonic"] <= finishes[0]["monotonic"] <= step["completed_monotonic"],
                "artifact did not finish inside its declared export/save stage")
    require(len(set(paths)) == len(paths),"duplicate artifact path")
    require(sum(name.endswith(".npz") for name in paths) == 4
            and sum(name.endswith(".json") for name in paths) == 3,"artifact kind counts differ")
    comparisons=summary["comparisons"]
    require(set(comparisons) == {"tiny_before","micro_first","micro_repeat","tiny_after"},"comparison set differs")
    with zipfile.ZipFile(root/REFERENCE) as archive:
        members=archive.namelist()
    require(len(members) == len(set(members)) == 48,"historical NPZ central directory differs")
    micro_keys={n.removeprefix("R1__").removesuffix(".npy") for n in members if n.startswith("R1__") and n.endswith(".npy")}
    require(len(micro_keys) == 24,"historical R1 leaf mapping differs")
    for name,row in comparisons.items():
        require(row["status"] == "pass" and row["field_count"] == len(row["fields"]) == (24 if name.startswith("micro") else 1),"comparison completeness differs")
        require(all(v["status"] == "pass" for v in row["fields"].values()),"saved numeric comparison failed")
        require(set(row["fields"]) == (micro_keys if name.startswith("micro") else {"value"}),"saved compared leaf keys differ")
        target=verify_record(root,row["artifact"])
        require(target.relative_to(root).as_posix() == "results/cost/"+name+".npz","comparison NPZ not in artifact set")
        item=artifacts[name+".npz"]
        require(row["artifact"] == item,"comparison/NPZ record differs")
        saved_step=steps[STAGES.index(name+".save_output")];compare_step=steps[STAGES.index(name+".compare")]
        require(saved_step["value"] == item and compare_step["value"] == row
                and saved_step["completed_monotonic"] <= compare_step["execution_start_monotonic"],"save/compare receipt differs")
        artifact_finish=next(r for r in events if r["event"] == "artifact_complete" and r["artifact"] == name+".npz")
        require(artifact_finish["monotonic"] <= compare_step["execution_start_monotonic"],"comparison preceded durable output")
    controls_path=next(bound(root,p) for p in paths if p.endswith("/interval_controls.json"))
    controls=read(controls_path)
    require(controls["status"] == "pass" and controls["count"] == 4 and len(controls["cases"]) == 4
            and controls["synthetic"] is True and controls["real_telemetry_failure"] is False,"pure CPU controls did not pass")
    require([r["name"] for r in controls["cases"]] == ["long_coverage","short_coverage","long_gap","counter_reversal"],"control names/order differ")
    require(summary["interval_controls"] == dict(result=controls,artifact=artifacts["interval_controls.json"]),"control artifact/summary differs")
    for row in controls["cases"]:
        actual=analyze_cpu_interval(row["records"],row["analysis"]["start"],row["analysis"]["end"])
        require(actual == row["analysis"] and row["status"] == "pass" and actual["status"] == row["expected_status"],"saved control analysis differs")
    runtime=summary["runtime"]
    require(read(root/"results/cost/runtime_config.json") == runtime
            and summary["runtime_config_record"] == artifacts["runtime_config.json"],"runtime artifact/summary differs")
    actual=runtime["actual_config"]
    require(set(actual) == {"jax_cpu_enable_async_dispatch","jax_debug_nans","jax_debug_infs","jax_disable_jit",
        "jax_enable_pgle","jax_pgle_profiling_runs","jax_enable_x64","jax_enable_compilation_cache",
        "jax_traceback_filtering","backend","compiler_options"},"actual config set differs")
    require(all(type(actual[k]) is bool for k in ("jax_cpu_enable_async_dispatch","jax_debug_nans","jax_debug_infs",
        "jax_disable_jit","jax_enable_pgle","jax_enable_x64","jax_enable_compilation_cache")),"actual boolean config not recorded")
    require(runtime["numpy"] == PACKAGES["numpy"] and runtime["jax"] == runtime["jaxlib"] == PACKAGES["jax"]
            and actual["backend"] == "cpu" and actual["jax_enable_x64"] is True and actual["jax_enable_compilation_cache"] is False
            and actual["jax_disable_jit"] is False and actual["jax_enable_pgle"] is False
            and actual["compiler_options"] == {"xla_cpu_enable_fast_math":False,"xla_cpu_ftz":False}
            and runtime["config_mutations"] == runtime["environment_mutations"] == 0,"actual runtime contract differs")
    manifest=read(root/"input_manifest.json")
    require(runtime["python"] == manifest["python"]["version"] and path(runtime["executable"]) == path(manifest["python"]["executable"])
            and path(runtime["arithmetic"]["path"]) == root/SOURCE/"src/hf_eval/compensated_invariants.py"
            and runtime["arithmetic"]["sha256"] == CI_SHA,"actual runtime source differs")
    environment=read(root/"results/cost/environment.json")
    require(summary["environment"] == dict(environment,artifact=artifacts["environment.json"])
            and environment["scientific_imports_started"] is False and environment["protocol"] == PROTOCOL
            and environment["run_id"] == RUN_ID and runtime["protocol"] == PROTOCOL and runtime["run_id"] == RUN_ID,"environment snapshot differs")
    expected_variables={"XLA_FLAGS","JAX_DEBUG_NANS","JAX_DEBUG_INFS","JAX_DISABLE_JIT","JAX_ENABLE_PGLE","JAX_PGLE_PROFILING_RUNS",
        "JAX_CPU_ENABLE_ASYNC_DISPATCH","JAX_ENABLE_X64","JAX_ENABLE_COMPILATION_CACHE","JAX_PLATFORMS",
        "OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","JAX_TRACEBACK_FILTERING","PYTHONDONTWRITEBYTECODE"}
    require(set(environment["variables"]) == expected_variables,"environment allowlist differs")
    for key,row in environment["variables"].items():
        require(set(row) == {"present","value"} and type(row["present"]) is bool
                and (isinstance(row["value"],str) if row["present"] else row["value"] is None),"environment presence/value invalid: "+key)
    values={k:r["value"] for k,r in environment["variables"].items()}
    require(values["JAX_ENABLE_X64"].lower() == "true" and values["JAX_ENABLE_COMPILATION_CACHE"].lower() == "false"
            and values["JAX_PLATFORMS"] == "cpu" and all(values[k] == "1" for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS")),
            "saved fixed environment values differ")
    require(environment["captured_monotonic"] < steps[STAGES.index("runtime_import")]["execution_start_monotonic"],"environment recorded after scientific imports")
    require(summary["source_preservation"]["status"] == "verified"
            and summary["source_preservation"]["input_manifest_sha256"] == selected["input_manifest_sha256"],"final source check absent")
    return dict(schema="hf-force-cost-probe-verification-1",status="runtime_cost_diagnostic_complete",
        summary=record(root,root/"results/cost/summary.json"),events=record(root,root/PROBE_EVENTS),
        stages=43,graphs=2,compiled_calls=4,synchronizations=4,ready_only=2,input_ready=1,
        artifacts=13,comparisons=4,scientific_admission=False)


def saved_artifacts(root, summary):
    observations=[];issues=[]
    artifacts=summary.get("artifacts",{}) if isinstance(summary,dict) else {}
    if not isinstance(artifacts,dict):return dict(status="invalid",issues=["artifact table is not a mapping"],artifacts=[])
    for name,row in artifacts.items():
        observation=dict(name=name,declared=row)
        try:
            if row.get("status") == "complete":verify_record(root,row);observation["verified"]=True
            else:
                observation["verified"]=False
                for key in ("path","partial_path"):
                    if row.get(key):
                        target=bound(root,row[key])
                        if target.is_file():observation[key+"_actual"]=record(root,target)
        except Exception as error:
            observation["error"]=failure(error);issues.append(dict(name=name,error=observation["error"]))
        observations.append(observation)
    return dict(status="verified_present_bytes" if not issues else "invalid",issues=issues,artifacts=observations)


def cpu_observation(root, summary, supervision):
    receipt=read(root/"results/P1_supervision/receipt.json")
    records=read_ndjson(root/CPU_FILE);expected=dict(supervision_identity(root),supervisor_sha256=SUP2_SHA)
    require(all(r["identity"] == expected for r in records),"CPU identity differs")
    instances=read_ndjson(root/"results/P1_supervision/instances.ndjson")
    require(all(r["observer_pid"] == records[0]["pid"] for r in instances),"CPU and instance observer PID differ")
    require(receipt["telemetry_status"] == "complete" and receipt.get("telemetry_first_error") is None
            and receipt["errors"] == [] and receipt["telemetry_interval_seconds"] == 1.
            and path(receipt["telemetry_path"]) == root/CPU_FILE,"CPU acquisition not complete")
    require(supervision["status"] == "verified_all_instances","CPU observation lacks same-instance cleanup")
    lifecycle=[r.get("lifecycle") for r in records]
    require(len(records) >= 3 and lifecycle[0] == "initial_before_resume"
            and lifecycle[-2:] == ["pre_cleanup","final_after_cleanup"]
            and all(x == "periodic" for x in lifecycle[1:-2]),"CPU lifecycle incomplete")
    require(records[-1]["cleanup_verified"] is True,"CPU final row does not confirm cleanup")
    require(all(isinstance(r.get("utc"),str) and r["utc"] for r in records),"CPU UTC metadata absent")
    cleanup=receipt["cleanup_requested_monotonic"]
    require(finite(cleanup) and records[-2]["query_start_monotonic"] >= cleanup,"tail snapshot precedes cleanup request")
    whole=analyze_cpu_interval(records,records[0]["query_start_monotonic"]-1.,records[-1]["query_end_monotonic"]+1.)
    require(whole["integrity_valid"],"CPU raw integrity failure")
    intervals=[];steps=summary.get("steps",[]) if isinstance(summary,dict) else []
    for row in steps:
        if row.get("stage") not in {name+"."+action for name in ("tiny_before","micro_first","micro_repeat","tiny_after")
                                   for action in ("synchronize","ready_only")}:
            continue
        if row.get("status") == "pass":
            start,end=row["execution_start_monotonic"],row["completed_monotonic"]
            require(end <= cleanup,"completed measured stage extends beyond cleanup request")
            analysis=analyze_cpu_interval(records,start,end)
            require(analysis["integrity_valid"],"CPU interval integrity failure")
            intervals.append(dict(stage=row["stage"],boundary="actual_function_entry_and_return",analysis=analysis))
        else:
            intervals.append(dict(stage=row["stage"],boundary="stage_marker_to_cleanup_observation_upper_bound",
                started_marker_monotonic=row.get("started_monotonic"),cleanup_requested_monotonic=cleanup,
                classification=None,status="open_at_stop",actual_function_entry_unknown=True))
    integrity_only=dict(integrity_only=True,integrity_valid=whole["integrity_valid"],issues=whole["issues"],record_count=len(records),
        classification_not_computed_for_admission=True,whole_campaign_cpu_aggregate_not_reported=True)
    return dict(schema="hf-force-cost-cpu-observation-1",protocol=PROTOCOL,run_id=RUN_ID,status="complete_acquisition",
        raw=record(root,root/CPU_FILE),records=len(records),integrity_valid=True,actual_telemetry_failure=False,
        intervals=intervals,raw_integrity=integrity_only,scientific_admission=False,
        limitation="Short/no internal sample intervals remain inconclusive; Job CPU cannot distinguish useful work, spin or scheduling.")


def svg_document(title, body, height=410):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="'+str(height)+'" viewBox="0 0 1100 '+str(height)+'">'
        '<rect width="100%" height="100%" fill="#f4f7fa"/><g font-family="Segoe UI,Arial,sans-serif" fill="#122235">'
        '<text x="32" y="40" font-size="23">'+escape(title)+'</text>'+body+'</g></svg>').encode("utf-8")


def stages_svg(summary):
    steps={r.get("stage"):r for r in summary.get("steps",[])};body=''
    names=("tiny_before","micro_first","micro_repeat","tiny_after")
    actions=("call","synchronize","ready_only","transfer")
    values=[steps.get(name+"."+action,{}).get("elapsed_seconds") for name in names for action in actions]
    maximum=max([v for v in values if finite(v)]+[.001])
    for col,name in enumerate(names):
        x=32+col*265;body+=f'<text x="{x}" y="82" font-size="16">{name}</text>'
        for j,action in enumerate(actions):
            y=117+j*58;row=steps.get(name+"."+action,{});v=row.get("elapsed_seconds")
            text=f'{action}: {v:.6g} s' if row.get("status") == "pass" and finite(v) else action+': '+('not scheduled' if action == "ready_only" and col >= 2 else row.get("status","not reached"))
            body+=f'<text x="{x}" y="{y}" font-size="13">{escape(text)}</text>'
            if row.get("status") == "pass" and finite(v):body+=f'<rect x="{x}" y="{y+8}" width="{220*v/maximum:.3f}" height="12" fill="#287ca3"/>'
    body+='<text x="32" y="382" font-size="13">Completed callback wall time; open markers are not completed measurements. No scientific admission.</text>'
    return svg_document(PROTOCOL+' recorded execution stages',body)


def cpu_svg(observation):
    body='<text x="32" y="75" font-size="13">Classification requires contained coverage ≥30 s and adjacent dt_max ≤2.5 s.</text>'
    intervals=observation.get("intervals",[])
    for i,row in enumerate(intervals):
        a=row.get("analysis",{});agg=a.get("aggregate") or {};ratio=agg.get("ratio_interval")
        text=row["stage"]+': '+str(a.get("classification") or row.get("status") or 'inconclusive')
        if ratio and a.get("classification"):text+=' | CPU/wall bounds '+format(ratio[0],'.5g')+'–'+format(ratio[1],'.5g')
        elif agg:text+=' | '+str(agg["cpu_ticks_100ns"])+' CPU ticks / '+format(agg["wall_seconds"],'.5g')+' s observed'
        body+=f'<text x="32" y="{112+i*37}" font-size="14">{escape(text)}</text>'
    if not intervals:body+='<text x="32" y="112" font-size="15">No completed interval available; raw evidence remains separate.</text>'
    body+='<text x="32" y="382" font-size="13">Inconclusive is not zero CPU. Parent observer excluded from Job CPU; useful work/spin remain unresolved.</text>'
    return svg_document(PROTOCOL+' Job CPU interval evidence',body)


def resources_svg(resources):
    body='<text x="32" y="78" font-size="14">Pre-seal snapshot; final parent receipt separately includes seal and final binding.</text>'
    for i,row in enumerate(resources.get("phases",[])):
        text=str(row.get("name"))+': '+str(row.get("elapsed_seconds"))+' s | '+str(row.get("reason"))+' | cleanup '+str(row.get("cleanup_verified"))
        body+=f'<text x="32" y="{123+i*48}" font-size="15">{escape(text)}</text>'
    peak=resources.get("peak_tree_rss_bytes")
    body+='<text x="32" y="310" font-size="15">Sampled tree RSS: '+escape(str(peak))+' bytes / limit 8589934592 bytes</text>'
    body+='<text x="32" y="355" font-size="13">240 s total: prepare 25 / cost 165 / seal 25 / shared 25; no phase borrowing.</text>'
    return svg_document(PROTOCOL+' resource accounting',body)


def seal(root, repo, events):
    problems=[]
    def observe(label, function):
        try:return function()
        except EventLogError:raise
        except Exception as error:
            item=failure(error);problems.append(dict(stage=label,error=item));return dict(status="incomplete_or_failed",error=item)
    preservation=observe("sources",lambda:verify_inputs(root,include_live=True))
    write(root/"source_preservation.json",preservation)
    resources=observe("resources",lambda:read(root/"resources.json"))
    summary_path=root/"results/cost/summary.json"
    summary=observe("probe_summary",lambda:read(summary_path)) if summary_path.is_file() else dict(status="not_reached",steps=[],artifacts={})
    artifact_status=saved_artifacts(root,summary);write(root/"artifact_status.json",artifact_status)
    if artifact_status["issues"]:problems.extend(artifact_status["issues"])
    supervisor_folder=root/"results/P1_supervision"
    if (supervisor_folder/"receipt.json").is_file():
        supervision=observe("supervision",lambda:verify_supervision(root))
    else:supervision=dict(status="not_reached",scientific_admission=False)
    proof_file=root/"supervision_proof.json"
    if proof_file.exists():
        saved=observe("parent_supervision",lambda:read(proof_file))
        if saved != supervision:problems.append(dict(stage="supervision",reason="parent saved proof differs"))
    else:write(proof_file,supervision)
    if (root/CPU_FILE).is_file():analysis=observe("CPU",lambda:cpu_observation(root,summary,supervision))
    else:analysis=dict(status="not_reached",intervals=[],scientific_admission=False)
    write(root/"cpu_observation.json",analysis)
    verification=dict(status="not_completed",scientific_admission=False,probe_status=summary.get("status"))
    if summary.get("status") == "runtime_cost_diagnostic_complete":
        verification=observe("complete_probe",lambda:verify_probe_summary(root))
        if not (supervision.get("status") == "verified_all_instances" and analysis.get("status") == "complete_acquisition"):
            problems.append(dict(stage="complete_probe",reason="completion lacks cleanup/CPU evidence"))
        receipt=read(supervisor_folder/"receipt.json")
        if receipt.get("reason") != "normal_exit" or receipt.get("returncode") != 0:
            problems.append(dict(stage="complete_probe",reason="completion lacks normal child exit"))
        parent_phases=[p for p in resources.get("phases",[]) if p.get("name") == "P1_cost"]
        if len(parent_phases) != 1 or parent_phases[0]["elapsed_seconds"] > 165 or (
                parent_phases[0]["phase_return_monotonic"]-parent_phases[0]["phase_start_monotonic"] > 165):
            problems.append(dict(stage="complete_probe",reason="completion exceeded inclusive P1 allowance"))
    write(root/"diagnostic_verification.json",verification)
    binary_write(root/"stages.svg",stages_svg(summary))
    binary_write(root/"cpu.svg",cpu_svg(analysis))
    binary_write(root/"resources.svg",resources_svg(resources))
    parent_status=resources.get("parent_status",resources.get("status"))
    complete=(verification.get("status") == "runtime_cost_diagnostic_complete" and not problems
              and parent_status == "runtime_cost_diagnostic_complete")
    result=dict(schema="hf-force-cost-evidence-worker-1",protocol=PROTOCOL,run_id=RUN_ID,action="seal",
        status="pass" if not problems else "evidence_failure",diagnostic_status="runtime_cost_diagnostic_complete" if complete else "not_completed",
        scientific_admission=False,payload_sealed=True,source_preservation=preservation,
        supervision_status=supervision.get("status"),cpu_status=analysis.get("status"),issues=problems,
        verification=record(root,root/"diagnostic_verification.json"),excluded=sorted(EXCLUDED),
        resources_scope="pre-seal only; final parent receipt includes seal",closed_utc=utc())
    write(root/"results/seal/summary.json",result)
    output={f.relative_to(root).as_posix():sha(f) for f in sorted(root.rglob("*"))
            if f.is_file() and f.relative_to(root).as_posix() not in EXCLUDED}
    write(root/"output_sha256.json",output)
    events.emit("seal_complete",status=result["status"],diagnostic_status=result["diagnostic_status"],output_manifest_sha256=sha(root/"output_sha256.json"))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",required=True,type=Path);parser.add_argument("--repo",required=True,type=Path)
    parser.add_argument("--action",required=True,choices=("prepare","seal"))
    args=parser.parse_args();root,repo=path(args.root),path(args.repo)
    require(root == repo/"hf4_c2_stable_f_validation"/RUN_ID and root.is_dir(),"parent must create exact authorized root")
    destination=root/"results"/args.action
    require(not destination.exists(),"worker phase cannot be repeated")
    events=EventLog();started=time.monotonic()
    try:
        events.emit("worker_started",action=args.action)
        if args.action == "seal":result=seal(root,repo,events)
        else:
            result=prepare(root,repo,events)
            write(destination/"summary.json",dict(schema="hf-force-cost-evidence-worker-1",protocol=PROTOCOL,run_id=RUN_ID,
                action=args.action,elapsed_seconds=time.monotonic()-started,**result))
        events.emit("worker_finished",action=args.action,status=result["status"])
        return 0 if result["status"] == "pass" else 2
    except EventLogError:raise
    except Exception as error:
        detail=failure(error)
        if not (destination/"summary.json").exists():
            write(destination/"summary.json",dict(schema="hf-force-cost-evidence-worker-1",protocol=PROTOCOL,run_id=RUN_ID,
                action=args.action,status="evidence_failure",error=detail,scientific_admission=False))
        events.emit("worker_failed",action=args.action,exception=detail)
        return 2
    finally:events.close()


if __name__ == "__main__":
    raise SystemExit(main())
