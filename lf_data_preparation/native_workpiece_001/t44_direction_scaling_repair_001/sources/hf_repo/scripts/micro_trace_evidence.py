"""F-TRACE1 selective evidence, bounded native trace parsing, and failure sealing.
Only standard-library code and frozen standard-library helpers are imported.
No scientific import, array decoding, native API call, profiler call or subprocess.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import gzip
import hashlib
from html import escape
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import time
import traceback
import zipfile
from s0_event_log import EventLog, EventLogError
from s0_preparation_evidence import bound, checked, copy_row, path, read, require, sha, utc, write
from force_cost_evidence import analyze_cpu_interval

PROTOCOL = "F-TRACE1"
RUN_ID = "micro_trace_001"
PRIOR_RUN = "force_cost_001"
PREFIX = "provenance/" + PRIOR_RUN + "/"
PRIOR_BINDING_SHA = "c0a3fb3a9405f33328211a201ecff6048c3020f416b3da50d018b88bace3be2b"
SOURCE = "R1/source/hf_repo"
HR1_TEST = "aux/hf_repo/tests/test_force_reuse_contract.py"
H1_TEST = "H1/tests/test_compensated_invariants.py"
REFERENCE_OLD = "provenance/force_reuse_002/results/local/micro_valid_first_three.npz"
REFERENCE = "data/micro_valid_first_three.npz"
CPU_FILE = "events/P1_trace_cpu.ndjson"
PROBE_EVENTS = "events/P1_trace.ndjson"
NATIVE = "results/trace/native"
COST_HELPER_SHA = "1374b365fdc21d462fc40a9e52193250f1c5370405dab255aa07ad3b77709b16"
R1_SHA = "630babc9c299ef2336835df18a50521f51d439dc09e3353ae6d0776d91937970"
CI_SHA = "6a0144a92bf323951594a0d677b7558cf2a6501667f4b076dd13e2df6bba3897"
HR1_SHA = "28e696175d572379527e6a021365dacf445fa4dd28f73cb381925d95bfb383d5"
H1_SHA = "15a81049f3fadcf0a0391f702db8444c33856f1116055d26e6ffca686821e946"
INPUT_SHA = "2ba110b878186e52996c25f4aad44cb81858be15303c21579c4f5e8ccc013448"
REFERENCE_SHA = "ee053018a911b45e78e9f821d9bf25f870fb9a81e3b17ee72dc4d27ae3868d4e"
SUP1_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
SUP2_SHA = "b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499"
HELPER_SHA = "2d378c64705461d58fa966528a347b6e411431402877663fd546f3fec8912f45"
FIXED_AUX = {
    "windows_owned_process.py": SUP1_SHA, "windows_owned_process_sup2.py": SUP2_SHA,
    "cpu_supervision_evidence.py": HELPER_SHA,
    "probe_s0_preparation.py": "bdd3d6c1f3b933de9268f9a7a64e67d7ddc96697f15ac8e237047fdc74abfd98",
    "s0_preparation_evidence.py": "666540e91569bfabef88a48399a80c6d5809401d39660231c2e6a203f2640ec9",
    "s0_event_log.py": "7f305d479d3f19216a7339eeb25c8c7ce24372a0f68c6492b265f90ac1b62c90",
    "s0_ad_exception.py": "03107b0b6f7142837833a4ad367550dbbbb523e0222316093624d66d939acb7d",
}
PACKAGES = {"numpy": "2.4.6", "jax": "0.11.0", "jaxlib": "0.11.0", "pytest": "9.1.1", "psutil": "7.2.2"}
EXCLUDED = {"output_sha256.json", "receipt_binding.json", "execution_receipt.json", "ledger.json",
    "events/P3_seal.ndjson", "logs/P3_seal.log"}

CURRENT_AUX = ("hf_repo/scripts/run_micro_trace.py", "hf_repo/scripts/probe_micro_trace.py",
 "hf_repo/scripts/micro_trace_evidence.py", "docs/CURRENT_STATUS.md", "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md")
HISTORY = ("receipt_binding.json", "execution_receipt.json", "output_sha256.json", "input_manifest.json",
 "selected_source.json", "loaded_supervisors.json", "results/cost/summary.json", "results/cost/environment.json",
 "results/cost/runtime_config.json", "results/cost/interval_controls.json", "results/cost/micro_first.npz",
 "results/cost/micro_repeat.npz", "results/cost/micro_optimized_hlo.txt", "cpu_observation.json", "supervision_proof.json",
 "results/P1_supervision/request.json", "results/P1_supervision/receipt.json", "results/P1_supervision/instances.ndjson",
 "events/P1_cost.ndjson", "events/P1_cost_cpu.ndjson", "R1/source_manifest.json", "HR1/manifest.json",
 "H1/manifest.json", "inheritance_manifest.json")
PROFILE_PINS = {
 "jax/profiler.py": (1324,"efc7b40958bb005fc2ce10c75fd934cdb61b6cd3744291572f5653a490462596"),
 "jax/_src/profiler.py": (19711,"abb2a2b16a34a060d581dccc0acecd655b20d60313377af3f727cce50a9c2a83"),
 "jax/_src/lib/__init__.py": (7333,"9438b64103846020c1414a01c2b83f00b80ea35e16032646b3f3850e8ceb8868"),
 "jaxlib/_profiler.pyd": (8704,"8469b4201e97fe42c8f9c01ad41f3c829db3462b991f33a9e3c2b2e097d04dea"),
 "jaxlib/_profile_data.pyd": (8704,"346df67a860c13b64236e7f817ba630ab09f34dab5155e787006a23490396e5e"),
 "jaxlib/jax_common.dll": (237296640,"cb392e3e87d292dc1db7cc88efd41f2f5b44ab0bb025cb5644b1eb1842e6ee14")}
STAGES = ("trace_controls", "source_binding", "environment_snapshot", "runtime_import", "kernel_import",
 "harness_import", "input_prepare", "input_ready") + tuple("micro."+s for s in
 ("trace","export_jaxpr","lower","export_stablehlo","compile","export_optimized_hlo")) + ("profiler_binding","profiler.start") + tuple(
 n+"."+s for n in ("micro_first","micro_repeat") for s in
 (("call","synchronize","ready_only","transfer","save_output","compare") if n=="micro_first" else
 ("call","synchronize","transfer","save_output","compare"))) + ("profiler.stop","native.collect","native.analyze","source_preservation")
ANNOTATION_STAGES = ("micro_first.call","micro_first.synchronize","micro_first.ready_only","micro_repeat.call","micro_repeat.synchronize")
ANNOTATIONS = tuple(PROTOCOL+":"+n for n in ANNOTATION_STAGES)
CAPS = dict(max_files=64,max_file_bytes=64*1024**2,max_total_bytes=128*1024**2,max_json_body_bytes=256*1024**2)
TARGET_RULE = {"version":"f-trace1-target-1", "module":"jit_reused",
 "exact_event_names":["Execute(jit_reused)","Execute: jit_reused"],
 "native_names_with_module_arg":["Execute","CpuExecutable::Execute","CpuExecutable::ExecuteAsyncOnStream",
     "PjRtCpuExecutable::Execute","PjRtCpuExecutable::ExecuteWithExecutionInputs","ThunkExecutor::Execute"],
 "exact_arg_keys":["hlo_module","hlo_module_name","module_name","program_name","executable_name"],
 "exact_arg_values":["jit_reused"], "generic_names_require_explicit_module_arg":True,
 "application_annotations_never_internal":True, "time_unit":"Chrome trace microseconds"}


def historical_authority(get):
    checked(get("receipt_binding.json"), PRIOR_BINDING_SHA)
    binding = read(get("receipt_binding.json"))
    require(binding["protocol"] == "F-COST1" and binding["run_id"] == PRIOR_RUN
            and binding["status"] == "runtime_cost_diagnostic_complete", "historical authority differs")
    for name in ("execution_receipt.json", "input_manifest.json", "output_sha256.json"):
        row = binding["records"][name]
        checked(get(name), row["sha256"], row["bytes"])
    output = read(get("output_sha256.json")); rows = []
    require(len(output) == 122, "predecessor inventory metadata differs")
    for name in HISTORY:
        target = get(name)
        if name not in ("receipt_binding.json", "execution_receipt.json", "output_sha256.json"):
            checked(target, output[name])
        entry = binding["records"].get(name)
        if entry is not None:
            require(entry["path"] == name, "historical binding path differs")
            checked(target, entry["sha256"], entry["bytes"])
        rows.append(dict(original_path=name, path=PREFIX+name, bytes=target.stat().st_size, sha256=sha(target)))
    require(len(rows) == 24, "selected historical count differs")
    return rows, read(get("input_manifest.json")), output


def source_specs(root, repo, *, archived=False):
    old = root.parent/PRIOR_RUN
    get = (lambda n: bound(root, PREFIX+n)) if archived else (lambda n: bound(old, n))
    history, previous, output = historical_authority(get)
    specs = []
    def add(name, source, digest=None, size=None, role="inherited_original"):
        specs.append(dict(path=name, source=str(path(source)), sha256=digest, bytes=size, role=role))
    for row in history:
        add(row["path"], old/row["original_path"], row["sha256"], row["bytes"], "selected_history")
    inherited = [r for r in previous["files"] if r["role"] == "inherited_R1"]
    require(previous["derived_files"] == [] and previous["new_patch_applications"] == 0
            and len(inherited) == 32 and sum(r["bytes"] for r in inherited) == 380009, "R1 inventory differs")
    for row in inherited:
        require(row["path"].startswith(SOURCE+"/") and output[row["path"]] == row["sha256"], "R1 authority differs")
        add(row["path"], old/row["path"], row["sha256"], row["bytes"], "inherited_R1")
    for name, digest in ((HR1_TEST,HR1_SHA),(H1_TEST,H1_SHA),("data/inputs.npz",INPUT_SHA)):
        require(output[name] == digest, "fixed harness/input differs")
        add(name,old/name,digest)
    require(output[REFERENCE_OLD] == REFERENCE_SHA, "fixed 48-member reference differs")
    add(REFERENCE,old/REFERENCE_OLD,REFERENCE_SHA,None,"inherited_reference")
    for filename, digest in {**FIXED_AUX,"force_cost_evidence.py":COST_HELPER_SHA}.items():
        name = "aux/hf_repo/scripts/"+filename
        require(output[name] == digest, "fixed auxiliary authority differs")
        add(name,old/name,digest,None,"fixed_auxiliary")
    runtime = []
    require(len(previous["runtime_files"]) == 15, "prior runtime inventory differs")
    for row in previous["runtime_files"]:
        require(output[row["frozen_path"]] == row["sha256"], "prior runtime authority differs")
        add(row["frozen_path"],old/row["frozen_path"],row["sha256"],row["bytes"],"frozen_runtime_source")
        runtime.append(dict(row))
    site = path(previous["python"]["executable"]).parent.parent/"Lib/site-packages"
    pins = []; binaries = []
    for relative,(size,digest) in PROFILE_PINS.items():
        item = dict(path=str(site/relative), package_relative_path=relative, bytes=size, sha256=digest)
        pins.append(item)
        if relative.endswith(".dll"):
            binaries.append(dict(item, copied=False))
        else:
            destination = "aux/runtime/"+relative
            add(destination,site/relative,digest,size,"new_profiler_dependency")
            runtime.append(dict(path=str(site/relative),frozen_path=destination,bytes=size,sha256=digest))
    for name in CURRENT_AUX:
        add("aux/"+name,repo/name,None,None,"current_diagnostic_auxiliary")
    require(len(specs) == len({r["path"] for r in specs}) == 93, "exact input inventory differs")
    return specs,history,previous,runtime,binaries,pins


def selected_metadata(root, manifest):
    return dict(schema="hf-micro-trace-selected-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,
        source_version="R1",source=SOURCE,hr1_test=HR1_TEST,reference_npz=REFERENCE,fixture="data/inputs.npz",
        input_manifest_sha256=sha(root/"input_manifest.json"),source_manifest_sha256=sha(root/"input_manifest.json"),
        harness=harness_metadata(root,"HR1"),arithmetic_harness=harness_metadata(root,"H1"),
        **roles(root,path(manifest["repo"])),scientific_admission=False)


def runtime_checks(manifest):
    require(path(sys.executable) == path(manifest["python"]["executable"])
            and sys.version == manifest["python"]["version"], "Python runtime differs")
    require(manifest["packages"] == PACKAGES, "package contract differs")
    for name, version in PACKAGES.items():
        require(importlib.metadata.version(name) == version, "installed package differs: "+name)
    for row in manifest["runtime_files"]+manifest["installed_binary_checks"]:
        checked(row["path"],row["sha256"],row["bytes"])


def prepare(root, repo, events):
    require(not any((root/n).exists() for n in ("input_manifest.json","selected_source.json","R1","H1","HR1")),
            "preparation must be write-once")
    specs,history,previous,runtime,binaries,pins = source_specs(root,repo)
    rows = [copy_row(root,r["source"],r["path"],expected=r["sha256"],size=r["bytes"],role=r["role"]) for r in specs]
    write(root/"inheritance_manifest.json",dict(schema="hf-micro-trace-selective-inheritance-1",protocol=PROTOCOL,run_id=RUN_ID,
        previous_binding_sha256=PRIOR_BINDING_SHA,historical_files=24,historical_bytes=sum(r["bytes"] for r in history),
        rows=history,predecessor_payload_total=122,full_predecessor_payload_verified=False,
        limitation="Only listed originals and explicit sources checked; old live source paths and uncopied upstreams not traversed."))
    r1_rows = [r for r in rows if r["role"] == "inherited_R1"]
    write(root/"R1/source_manifest.json",dict(schema="hf-micro-trace-source-relocation-1",version="R1",source=SOURCE,
        files=[{k:r[k] for k in ("path","bytes","sha256")} for r in r1_rows],new_patch_applications=0,
        upstream=dict(path=PREFIX+"R1/source_manifest.json",sha256=sha(root/PREFIX/"R1/source_manifest.json")),
        archived_upstream_references_not_traversed=True,scientific_admission=False))
    for version,test,digest in (("H1",H1_TEST,H1_SHA),("HR1",HR1_TEST,HR1_SHA)):
        write(root/version/"manifest.json",dict(schema="hf-micro-trace-harness-relocation-1",version=version,
            test_path=test,test_sha256=digest,test_bytes_changed=False,globals_rewritten=False,
            upstream=dict(path=PREFIX+version+"/manifest.json",sha256=sha(root/PREFIX/version/"manifest.json")),
            full_harness_executed=False,scientific_admission=False))
    ast_result = assert_micro_ast(root/HR1_TEST,root/"aux/hf_repo/scripts/probe_micro_trace.py")
    generated = [record(root,root/n) for n in ("inheritance_manifest.json","R1/source_manifest.json","HR1/manifest.json","H1/manifest.json")]
    manifest = dict(schema="hf-micro-trace-inputs-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,
        created_utc=utc(),repo=str(repo),files=rows,generated_metadata=generated,derived_files=[],new_patch_applications=0,
        inherited_candidate_files=32,historical_files=24,historical_bytes=sum(r["bytes"] for r in history),**roles(root,repo),
        science=dict(version="R1",source=SOURCE,kernel_sha256=R1_SHA,arithmetic_sha256=CI_SHA),
        harness=harness_metadata(root,"HR1"),arithmetic_harness=harness_metadata(root,"H1"),
        canonical_files=previous["canonical_files"],python=previous["python"],packages=PACKAGES,runtime_files=runtime,
        installed_binary_checks=binaries,profile_pins=pins,inherited_supervision=previous["inherited_supervision"],
        micro_ast=ast_result,target_rule=TARGET_RULE,native_caps=CAPS,scientific_admission=False)
    plan = read(root/"plan.json")
    require(plan["protocol"] == plan["campaign_protocol"] == PROTOCOL and plan["run_id"] == RUN_ID
            and plan["seconds"] == 180 and all(plan[k] == v for k,v in roles(root,repo).items()),"parent plan differs")
    require(plan["runner_sha256"] == sha(root/"aux/hf_repo/scripts/run_micro_trace.py")
            and plan["evidence_worker_sha256"] == sha(root/"aux/hf_repo/scripts/micro_trace_evidence.py"),"parent auxiliary pins differ")
    write(root/"input_manifest.json",manifest)
    write(root/"selected_source.json",selected_metadata(root,manifest))
    result = verify_inputs(root,include_live=True)
    events.emit("preparation_complete",files=93,input_manifest_sha256=result["input_manifest_sha256"])
    return dict(status="pass",source_verification=result,scientific_admission=False)


def verify_inputs(root, include_live=False):
    root=path(root);manifest=read(root/"input_manifest.json");repo=path(manifest["repo"])
    require(manifest["schema"] == "hf-micro-trace-inputs-1" and manifest["protocol"] == manifest["campaign_protocol"] == PROTOCOL
            and manifest["run_id"] == RUN_ID and root == repo/"hf4_c2_stable_f_validation"/RUN_ID,"input identity differs")
    specs,history,previous,runtime,binaries,pins = source_specs(root,repo,archived=True)
    expected={r["path"]:r for r in specs};rows=manifest["files"]
    require(len(rows) == len({r["path"] for r in rows}) == 93 and {r["path"] for r in rows} == set(expected),"input set differs")
    for row in rows:
        spec=expected[row["path"]]
        require(path(row["source"]) == path(spec["source"]) and row["role"] == spec["role"],"source mapping differs")
        require((spec["sha256"] is None or row["sha256"] == spec["sha256"])
                and (spec["bytes"] is None or row["bytes"] == spec["bytes"]),"fixed source identity differs")
        checked(bound(root,row["path"]),row["sha256"],row["bytes"])
        if include_live:checked(row["source"],row["sha256"],row["bytes"])
    require(manifest["derived_files"] == [] and manifest["new_patch_applications"] == 0 and manifest["inherited_candidate_files"] == 32
            and manifest["runtime_files"] == runtime and manifest["installed_binary_checks"] == binaries
            and manifest["profile_pins"] == pins and manifest["target_rule"] == TARGET_RULE and manifest["native_caps"] == CAPS,
            "candidate/runtime/parser contract differs")
    for row in manifest["generated_metadata"]:checked(bound(root,row["path"]),row["sha256"],row["bytes"])
    require(len(manifest["generated_metadata"]) == 4 and {r["path"] for r in manifest["generated_metadata"]} ==
        {"inheritance_manifest.json","R1/source_manifest.json","HR1/manifest.json","H1/manifest.json"},"generated metadata differs")
    require({f.relative_to(root).as_posix() for f in (root/SOURCE).rglob("*") if f.is_file()} ==
            {r["path"] for r in rows if r["role"] == "inherited_R1"},"R1 inventory differs")
    checked(root/SOURCE/"src/hf_eval/split_kernel_invariants_hu.py",R1_SHA)
    checked(root/SOURCE/"src/hf_eval/compensated_invariants.py",CI_SHA)
    require(read(root/"selected_source.json") == selected_metadata(root,manifest),"selected metadata differs")
    require(manifest["harness"] == harness_metadata(root,"HR1") and manifest["arithmetic_harness"] == harness_metadata(root,"H1"),"harness differs")
    require(all(manifest[k] == v for k,v in roles(root,repo).items()),"supervisor roles differ")
    require(assert_micro_ast(root/HR1_TEST,root/"aux/hf_repo/scripts/probe_micro_trace.py") == manifest["micro_ast"],"micro AST differs")
    require(read(root/"inheritance_manifest.json")["rows"] == history,"history selection differs")
    if include_live:
        require(manifest["canonical_files"] == previous["canonical_files"] and len(manifest["canonical_files"]) == 30,"canonical set differs")
        for name,row in manifest["canonical_files"].items():
            require(path(row["path"]) == repo/"hf_repo"/name,"canonical source escaped repo")
            checked(row["path"],row["sha256"])
        canonical={"src/"+f.relative_to(repo/"hf_repo/src").as_posix() for f in (repo/"hf_repo/src").rglob("*")
                   if f.is_file() and "__pycache__" not in f.parts}
        require(canonical == {n for n in manifest["canonical_files"] if n.startswith("src/")},"canonical inventory differs")
        old_rows={r["path"]:r for r in previous["files"]}
        for name in ("run_force_cost.py","probe_force_cost.py","force_cost_evidence.py"):
            checked(repo/"hf_repo/scripts"/name,old_rows["aux/hf_repo/scripts/"+name]["sha256"])
        for name,digest in FIXED_AUX.items():checked(repo/"hf_repo/scripts"/name,digest)
        checked(repo/"hf_repo/tests/test_force_reuse_contract.py",HR1_SHA)
        runtime_checks(manifest)
    return dict(status="verified",input_manifest_sha256=sha(root/"input_manifest.json"),file_count=93,
        bytes=sum(r["bytes"] for r in rows),historical_files=24,historical_bytes=sum(r["bytes"] for r in history),
        inherited_R1_files=32,derived_files=0,new_patch_applications=0,include_live=bool(include_live),scientific_admission=False)


def time_remaining(deadline):
    require(deadline is None or (finite(deadline) and time.monotonic() < deadline), "evidence deadline reached")


def regular_no_reparse(filename):
    info = os.lstat(filename)
    require(not stat.S_ISLNK(info.st_mode) and not (getattr(info,"st_file_attributes",0) & 0x400),
            "reparse/symlink is not an admissible evidence source: "+str(filename))
    return info


def walk_no_reparse(folder, *, deadline=None, maximum=None):
    """Lexical child walk, never resolving/following reparse entries."""
    folder=Path(folder);regular_no_reparse(folder);stack=[folder];count=0
    while stack:
        time_remaining(deadline);directory=stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                time_remaining(deadline);name=Path(entry.path);info=regular_no_reparse(name)
                if stat.S_ISDIR(info.st_mode):stack.append(name)
                elif stat.S_ISREG(info.st_mode):
                    count+=1
                    yield name,info
                    if maximum is not None and count >= maximum:return
                else:raise ValueError("nonregular evidence entry: "+str(name))


def streamed_record(root, filename, *, deadline=None, flush=False):
    before=regular_no_reparse(filename)
    require(stat.S_ISREG(before.st_mode), "evidence is not a regular file")
    digest=hashlib.sha256();size=0
    with open(filename,"r+b" if flush else "rb") as stream:
        if flush:os.fsync(stream.fileno())
        while True:
            time_remaining(deadline);chunk=stream.read(1024*1024)
            if not chunk:break
            digest.update(chunk);size+=len(chunk)
    after=regular_no_reparse(filename)
    require(size == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            "evidence changed during read")
    return dict(path=Path(filename).relative_to(root).as_posix(),bytes=size,sha256=digest.hexdigest())


def collect_native(root, log_dir, *, deadline=None):
    """Post-export acceptance caps. Oversize bytes are never deleted/truncated."""
    root=path(root);folder=Path(log_dir)
    require(os.path.normcase(os.path.abspath(folder)) == os.path.normcase(os.path.abspath(root/NATIVE)),"native log_dir differs")
    result=dict(schema="hf-micro-trace-native-inventory-1",protocol=PROTOCOL,run_id=RUN_ID,
        status="partial",files=[],issues=[],caps=CAPS,json_record=None,xplane_records=[],
        enumeration_complete=False,all_enumerated_hashes_complete=False,scientific_admission=False)
    if not folder.exists():result["issues"].append("native_directory_not_created");return result
    # Every ancestor below the authorized root is checked before any descent.
    cursor=root
    for component in Path(NATIVE).parts:
        cursor=cursor/component;regular_no_reparse(cursor)
    try:
        entries=[]
        for filename,info in walk_no_reparse(folder,deadline=deadline,maximum=CAPS["max_files"]+1):
            entries.append((filename,info))
        entries.sort(key=lambda item: str(item[0]))
        result["enumeration_complete"]=len(entries) <= CAPS["max_files"]
        if not result["enumeration_complete"]:result["issues"].append("native_file_count_over_64_enumeration_stopped_at_65")
        total=sum(info.st_size for _,info in entries)
        if total > CAPS["max_total_bytes"]:result["issues"].append("native_total_bytes_over_acceptance_cap")
        for filename,info in entries:
            item=dict(path=filename.relative_to(root).as_posix(),bytes=info.st_size,sha256=None,status="unhashed")
            if info.st_size > CAPS["max_file_bytes"]:result["issues"].append(dict(path=item["path"],reason="native_file_over_acceptance_cap"))
            result["files"].append(item)
            try:item.update(streamed_record(root,filename,deadline=deadline,flush=True),status="hashed")
            except Exception as error:
                item["error"]=failure(error);result["issues"].append(dict(path=item["path"],error=item["error"]));break
        result["all_enumerated_hashes_complete"]=(len(result["files"]) == len(entries) and all(r["status"] == "hashed" for r in result["files"]))
        result["unhashed_enumerated_paths"]=[name.relative_to(root).as_posix() for name,_ in entries
            if not any(r["path"] == name.relative_to(root).as_posix() and r["status"] == "hashed" for r in result["files"])]
        result["enumerated_files"]=len(entries);result["enumerated_bytes"]=total
        sessions=set()
        for filename,_ in entries:
            rel=filename.relative_to(folder).parts
            if len(rel) < 4 or rel[:2] != ("plugins","profile"):
                result["issues"].append(dict(path=filename.relative_to(root).as_posix(),reason="unexpected_native_layout"))
            else:sessions.add(rel[2])
        result["sessions"]=sorted(sessions)
        if len(sessions) != 1:result["issues"].append("expected_exactly_one_native_session")
        jsons=[r for r in result["files"] if r["path"].endswith(".trace.json.gz")]
        xplanes=[r for r in result["files"] if r["path"].endswith(".xplane.pb")]
        if len(jsons) != 1:result["issues"].append("expected_exactly_one_native_trace_json_gz")
        if not xplanes:result["issues"].append("missing_native_xplane_original")
        result["json_record"]=jsons[0] if len(jsons)==1 else None
        result["xplane_records"]=xplanes
        if not result["issues"] and result["all_enumerated_hashes_complete"]:result["status"]="complete"
    except Exception as error:result["issues"].append(failure(error))
    result["parser_permitted"]=result["status"] == "complete"
    return result


def parse_native_json(filename, *, deadline=None):
    regular_no_reparse(filename);body=bytearray();limit=CAPS["max_json_body_bytes"]
    with gzip.open(filename,"rb") as stream:
        while len(body) <= limit:
            time_remaining(deadline);chunk=stream.read(min(1024*1024,limit+1-len(body)))
            if not chunk:break
            body.extend(chunk)
    require(len(body) <= limit,"native JSON uncompressed body exceeds 256 MiB")
    def invalid_constant(value):raise ValueError("nonfinite JSON constant: "+value)
    document=json.loads(body.decode("utf-8"),parse_constant=invalid_constant)
    require(isinstance(document,dict) and isinstance(document.get("traceEvents"),list),"unsupported native trace JSON schema")
    return document,len(body)


def interval_union(intervals):
    """Union in one native clock; never sum overlapping/nested thread spans."""
    merged=[]
    for a,b in sorted(intervals):
        require(finite(a) and finite(b) and b >= a,"invalid coverage interval")
        if merged and a <= merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    return dict(intervals=merged,duration_us=sum(b-a for a,b in merged),input_count=len(intervals))


def analyze_trace_events(events, expected_annotations=ANNOTATIONS, target_identity=None):
    """Pure parser and fixed attribution rule used by controls and real evidence."""
    rule=TARGET_RULE if target_identity is None else target_identity
    require(rule == TARGET_RULE, "native source rule must not be relaxed after capture")
    result=dict(schema="hf-micro-trace-analysis-1",protocol=PROTOCOL,run_id=RUN_ID,
        status="observability_not_pass",predeclared_rule=rule,issues=[],annotations={},native_regions=[],
        rejected_regions=[],metadata=[],other_events=[],intervals=[],call_windows=[],
        raw_reference="Original JSON bytes retained; indices refer to traceEvents in exact file order.",
        timestamp_unit="microseconds",trace_identifiers_are_not_windows_ids=True,scientific_admission=False)
    require(isinstance(events,list),"traceEvents must be a list")
    stacks={};intervals=result["intervals"];issues=result["issues"];thread_names={}
    for index,event in enumerate(events):
        if not isinstance(event,dict):issues.append(dict(index=index,reason="nonobject_event"));continue
        phase=event.get("ph");name=event.get("name");pid=event.get("pid");tid=event.get("tid")
        if phase == "M":
            result["metadata"].append(dict(index=index,event=event))
            if name == "thread_name" and isinstance(event.get("args"),dict) and isinstance(event["args"].get("name"),str):
                thread_names[(str(pid),str(tid))]=event["args"]["name"]
            continue
        if phase not in ("X","B","E"):
            kind="instant" if phase in ("i","I","R") else "counter" if phase == "C" else "flow" if phase in ("s","t","f") else "uninterpreted"
            result["other_events"].append(dict(index=index,phase=phase,kind=kind,name=name))
            continue
        ts=event.get("ts")
        if not finite(ts) or pid is None or tid is None:
            issues.append(dict(index=index,reason="invalid_timed_event_timestamp_or_trace_identity"));continue
        key=(str(pid),str(tid))
        if phase == "B":
            if not isinstance(name,str):issues.append(dict(index=index,reason="begin_missing_name"));continue
            stacks.setdefault(key,[]).append((index,event));continue
        if phase == "E":
            if not stacks.get(key):issues.append(dict(index=index,reason="unmatched_end"));continue
            begin_index,begin=stacks[key].pop()
            if name is not None and name != begin["name"]:
                issues.append(dict(index=index,reason="begin_end_name_mismatch"));continue
            duration=ts-begin["ts"];base=begin;origin=[begin_index,index]
        else:duration=event.get("dur");base=event;origin=[index]
        if not finite(duration) or duration < 0 or not finite(base["ts"]+duration) or not isinstance(base.get("name"),str):
            issues.append(dict(index=index,reason="invalid_duration_or_name"));continue
        intervals.append(dict(indices=origin,phase=phase,pid=pid,tid=tid,name=base["name"],args=base.get("args",{}),
            ts=base["ts"],dur=duration,end=base["ts"]+duration))
    for key,stack in stacks.items():
        if stack:issues.append(dict(trace_thread=list(key),reason="unclosed_begin",indices=[v[0] for v in stack]))
    result["event_count"]=len(events)
    for name in expected_annotations:
        matches=[r for r in intervals if r["name"] == name]
        if len(matches) != 1:issues.append(dict(annotation=name,reason="annotation_missing_or_repeated",count=len(matches)))
        else:result["annotations"][name]=matches[0]
    if len(result["annotations"]) != 5:return result
    markers=[result["annotations"][n] for n in expected_annotations]
    if len({(str(r["pid"]),str(r["tid"])) for r in markers}) != 1:
        issues.append("application_annotations_not_on_one_trace_thread")
    if any(a["end"] > b["ts"] for a,b in zip(markers,markers[1:])):issues.append("application_annotation_order_or_overlap")
    for r in markers:
        if (str(r["pid"]),str(r["tid"])) not in thread_names:issues.append("annotation_thread_metadata_missing")
    for name in ("micro_first","micro_repeat"):
        a=result["annotations"][PROTOCOL+":"+name+".call"]
        b=result["annotations"][PROTOCOL+":"+name+".synchronize"]
        result["call_windows"].append(dict(name=name,trace_pid=a["pid"],start_us=a["ts"],end_us=b["end"],regions=[]))
    for item in intervals:
        name=item["name"]
        if name.startswith(PROTOCOL+":"):continue
        args=item["args"] if isinstance(item["args"],dict) else {}
        source=(name in rule["exact_event_names"] or (name in rule["native_names_with_module_arg"] and
                any(args.get(k) in rule["exact_arg_values"] for k in rule["exact_arg_keys"])))
        rejection=None
        if not source:rejection="not_a_predeclared_execution_name_and_module_identity"
        elif item["dur"] <= 0:rejection="zero_duration_execution_region"
        elif (str(item["pid"]),str(item["tid"])) not in thread_names:rejection="native_thread_metadata_missing"
        matching=[w for w in result["call_windows"] if str(w["trace_pid"]) == str(item["pid"])
                  and w["start_us"] <= item["ts"] <= item["end"] <= w["end_us"]]
        if source and len(matching) != 1:rejection="execution_region_not_wholly_in_one_same_plane_call_sync_window"
        if rejection:
            result["rejected_regions"].append(dict(indices=item["indices"],name=name,reason=rejection));continue
        accepted=dict(item,window=matching[0]["name"],thread_label=thread_names[(str(item["pid"]),str(item["tid"]))])
        result["native_regions"].append(accepted);matching[0]["regions"].append(item["indices"])
    for window in result["call_windows"]:
        spans=[(r["ts"],r["end"]) for r in result["native_regions"] if r["window"] == window["name"]]
        window["observed_union"]=interval_union(spans)
        if not spans:issues.append(dict(window=window["name"],reason="no_uniquely_bound_native_execution_interval"))
    if not issues:result["status"]="runtime_native_trace_observed"
    result["limitation"]="Observed runtime regions may include scheduling or waiting; unions are not arithmetic-work percentages."
    return result


def trace_controls():
    """Exactly three synthetic controls, invoking this real parser/union code."""
    base=[dict(ph="M",name="thread_name",pid=1,tid=t,args=dict(name="synthetic_"+str(t))) for t in (7,8,9)]
    for name,ts,dur in zip(ANNOTATIONS,(0,12,115,200,212),(10,100,10,10,100)):
        base.append(dict(ph="X",name=name,pid=1,tid=7,ts=ts,dur=dur,args={}))
    work=[dict(ph="X",name="CpuExecutable::Execute",pid=1,tid=8,ts=t,dur=108,args=dict(hlo_module="jit_reused")) for t in (2,202)]
    overlap=[dict(ph="B",name="ThunkExecutor::Execute",pid=1,tid=9,ts=20,args=dict(module_name="jit_reused")),
             dict(ph="E",pid=1,tid=9,ts=30)]
    cases=[]
    for name,rows,status in (("identified_native_regions",base+work,"runtime_native_trace_observed"),
        ("applications_only",base,"observability_not_pass"),("cross_thread_nested_overlap",base+work+overlap,"runtime_native_trace_observed")):
        result=analyze_trace_events(rows)
        require(result["status"] == status,"trace control classification differs: "+name)
        if name == "cross_thread_nested_overlap":
            require([w["observed_union"]["duration_us"] for w in result["call_windows"]] == [108,108],"cross-thread intervals were double counted")
        cases.append(dict(name=name,status="pass",expected_status=status,records=rows,analysis=result))
    return dict(schema="hf-micro-trace-controls-1",protocol=PROTOCOL,run_id=RUN_ID,status="pass",count=3,
        synthetic=True,cases=cases,scientific_admission=False)


def hlo_mapping(root, analysis):
    filename=root/"results/trace/micro_optimized_hlo.txt"
    text=filename.read_text(encoding="utf-8");first=text.splitlines()[0]
    match=re.match(r"HloModule\s+([A-Za-z0-9_.-]+),",first)
    require(match is not None and match.group(1) == TARGET_RULE["module"],"current optimized HLO target differs")
    entry=False;producers=[]
    for line_number,line in enumerate(text.splitlines(),1):
        if line.startswith("ENTRY "):entry=True
        if entry and " fusion(" in line:
            m=re.search(r"^\s*(?:ROOT )?%?([\w.-]+)\s*=.*\bfusion\(.*\bcalls=%?([\w.-]+)",line)
            if m:producers.append(dict(producer=m.group(1),computation=m.group(2),line=line_number))
    mapped=[]
    for row in producers:
        matches=[]
        for event in analysis.get("intervals",[]):
            args=event["args"] if isinstance(event["args"],dict) else {}
            exact=(event["name"] == row["producer"] or any(args.get(k) == row["producer"] for k in ("hlo_op","hlo_instruction","op_name")))
            if not exact:continue
            region=[r for r in analysis.get("native_regions",[]) if str(r["pid"]) == str(event["pid"])
                    and r["ts"] <= event["ts"] <= event["end"] <= r["end"]]
            if region:matches.append(dict(indices=event["indices"],window=region[0]["window"],ts=event["ts"],dur=event["dur"],pid=event["pid"],tid=event["tid"]))
        mapped.append(dict(**row,observations=matches or None))
    return dict(schema="hf-micro-trace-hlo-mapping-1",protocol=PROTOCOL,run_id=RUN_ID,module=match.group(1),
        optimized_hlo=record(root,filename),entry_fusions=mapped,producer_count=len(producers),
        status="some_producers_observed" if any(r["observations"] for r in mapped) else "fusion_attribution_inconclusive",
        rule="Exact current ENTRY producer name or explicit hlo_op/hlo_instruction/op_name inside a bound native module region.",
        all_six_pairs_claimed=False,scientific_admission=False)


def analyze_native(root, inventory, summary):
    root=path(root)
    result=dict(schema="hf-micro-trace-analysis-1",protocol=PROTOCOL,run_id=RUN_ID,status="observability_not_pass",
        predeclared_rule=TARGET_RULE,issues=[],scientific_admission=False)
    if inventory.get("status") != "complete":result["issues"].append("native_inventory_not_complete_or_over_cap");return result
    lifecycle=summary.get("profiler",{})
    if not (lifecycle.get("start_returned") is True and lifecycle.get("stop_returned") is True
            and lifecycle.get("start_attempts") == lifecycle.get("stop_attempts") == 1):
        result["issues"].append("native_session_did_not_complete_single_start_stop");return result
    try:
        filename=verify_record(root,inventory["json_record"])
        document,body_size=parse_native_json(filename)
        result=analyze_trace_events(document["traceEvents"])
        result.update(json_record=inventory["json_record"],uncompressed_bytes=body_size,
            display_time_unit=document.get("displayTimeUnit"),display_time_unit_used_for_scaling=False)
        steps={r["stage"]:r for r in summary.get("steps",[])}
        measurements=[]
        for stage in ANNOTATION_STAGES:
            step=steps.get(stage,{});measurement=step.get("value",{}).get("function_measurement",{})
            expected_name=PROTOCOL+":"+stage;marker=result.get("annotations",{}).get(expected_name)
            if not marker or step.get("status") != "pass":result["issues"].append(dict(stage=stage,reason="missing_complete_measured_stage"));continue
            a,b,c,d=(measurement.get(k) for k in ("annotation_outer_start_monotonic","monotonic_start","monotonic_end","annotation_outer_end_monotonic"))
            require(all(finite(v) for v in (a,b,c,d)) and a <= b <= c <= d,"measurement/annotation brackets invalid")
            require(measurement["annotation_name"] == expected_name and b == step["execution_start_monotonic"]
                    and c == step["completed_monotonic"],"annotation function measurement differs")
            require((c-b)*1e6 <= marker["dur"]+1. and marker["dur"] <= (d-a)*1e6+1.,"native/body/outer relative durations do not close")
            for key in ("pid","native_tid"):
                require(type(measurement[key]) is int and measurement[key] > 0,"actual native caller identity absent")
            for key in ("thread_time_ns","process_time_ns"):
                require(type(measurement[key+"_start"]) is int and type(measurement[key+"_end"]) is int
                        and 0 <= measurement[key+"_start"] <= measurement[key+"_end"],"CPU time counter reversed")
            measurements.append(dict(stage=stage,function_measurement=measurement,native_annotation=marker))
        require(len({(m["function_measurement"]["pid"],m["function_measurement"]["native_tid"]) for m in measurements}) == 1,
                "measured application caller changed")
        result["measurements"]=measurements;result["duration_rounding_tolerance_us"]=1.
        result["hlo_mapping"]=hlo_mapping(root,result)
        require(summary.get("micro_hlo_module") == result["hlo_mapping"]["module"],"probe/current HLO module differs")
        if result["issues"]:result["status"]="observability_not_pass"
    except Exception as error:
        result["status"]="observability_not_pass";result["issues"].append(failure(error))
    return result


def verify_numerical_reports(root, summary):
    """Only saved comparisons and ZIP central directories, never array decoding."""
    with zipfile.ZipFile(root/REFERENCE) as archive:members=archive.namelist()
    require(len(members) == len(set(members)) == 48,"historical NPZ member inventory differs")
    keys={n.removeprefix("R1__").removesuffix(".npy") for n in members if n.startswith("R1__") and n.endswith(".npy")}
    require(len(keys) == 24,"historical R1 leaf inventory differs")
    steps={r["stage"]:r for r in summary.get("steps",[])};comparisons=summary.get("comparisons",{})
    historical=read(root/PREFIX/"results/cost/summary.json")["comparisons"]
    require(set(comparisons) == {"micro_first","micro_repeat"},"two numerical reports not complete")
    for name,row in comparisons.items():
        require(row["status"] == "pass" and row["field_count"] == len(row["fields"]) == 24
                and set(row["fields"]) == keys and all(v["status"] == "pass" for v in row["fields"].values()),"original 24-leaf gate failed or incomplete")
        require(row["fields"] == historical[name]["fields"],"shape/dtype/signed-zero report differs from the original identical micro gate")
        item=summary["artifacts"][name+".npz"]
        require(item == row["artifact"] and item["status"] == "complete"
                and item["path"] == "results/trace/"+name+".npz","numerical artifact binding differs")
        target=verify_record(root,item)
        with zipfile.ZipFile(target) as archive:actual=archive.namelist()
        require(len(actual) == len(set(actual)) == 24 and {n.removesuffix(".npy") for n in actual} == keys,
                "saved output ZIP leaf inventory differs")
        saved=steps[name+".save_output"];compared=steps[name+".compare"]
        require(saved["status"] == compared["status"] == "pass" and saved["value"] == item and compared["value"] == row
                and saved["completed_monotonic"] <= compared["execution_start_monotonic"],"comparison preceded durable output")
    return dict(status="saved_original_24_leaf_gates_verified",comparisons=2,leaves_each=24,arrays_decoded=False,
        force_executed=False,scientific_admission=False)


def verify_probe_summary(root, *, native_analysis=None):
    root=path(root);summary=read(root/"results/trace/summary.json");selected=read(root/"selected_source.json")
    require(summary["schema"] == "hf-micro-trace-probe-1" and summary["protocol"] == summary["campaign_protocol"] == PROTOCOL
            and summary["run_id"] == RUN_ID and summary["mode"] == "trace" and summary["source_version"] == "R1","probe identity differs")
    require(path(summary["source"]) == root/SOURCE and summary["source_manifest_sha256"] == selected["input_manifest_sha256"]
            and summary["harness"] == selected["harness"] and summary["arithmetic_harness"] == selected["arithmetic_harness"],"probe source differs")
    require(summary["status"] in ("runtime_native_trace_observed","observability_not_pass")
            and summary["scientific_admission"] is False and not summary["errors"] and summary["first_error"] is None,
            "probe did not complete fixed observation")
    for name in ("parent_supervisor","candidate_supervisor","loaded_parent_supervisor"):
        require(summary[name] == selected[name],"probe role differs")
    steps=summary["steps"]
    require([r["stage"] for r in steps] == list(STAGES) and len(steps) == 31,"probe stage set/order differs")
    counts=dict(graph_count=1,trace=1,lower=1,compile=1,compiled_call=2,output_synchronization=2,ready_only=1,input_ready=1,
        micro_leaf_count=24,profiler_start=1,profiler_stop=1,annotations=5)
    require(summary["completed_counts"] == counts and summary["execution_contract"] ==
        dict(counts,warmup=0,retries=0,force_calls=0,ad_calls=0),"execution counts differ")
    previous=None
    for row in steps:
        a,b,c=row["started_monotonic"],row["execution_start_monotonic"],row["completed_monotonic"]
        require(row["status"] == "pass" and all(finite(v) for v in (a,b,c,row["elapsed_seconds"]))
                and a <= b <= c and (previous is None or previous <= a) and row["elapsed_seconds"] == c-b,"invalid stage timing")
        previous=c
    events=read_ndjson(root/PROBE_EVENTS);actions=[];prior=None
    for index,row in enumerate(events,1):
        require(row["schema"] == "hf-s0-event-1" and row["sequence"] == index and row["phase"] == "P1_trace"
                and row["version"] == "R1" and row["source_manifest_sha256"] == selected["input_manifest_sha256"]
                and row["protocol"] == row["campaign_protocol"] == PROTOCOL and row["run_id"] == RUN_ID
                and row["harness_id"] == "HR1" and row["harness_manifest_sha256"] == selected["harness"]["manifest_sha256"],"probe event identity differs")
        require(finite(row["monotonic"]) and (prior is None or prior <= row["monotonic"]),"event clock reversed")
        prior=row["monotonic"]
        if row["event"] in ("stage_started","stage_finished"):
            actions.append((row["event"],row["stage"]));step=steps[STAGES.index(row["stage"])]
            if row["event"] == "stage_started":require(row["stage_start_monotonic"] == step["started_monotonic"],"stage marker differs")
            else:
                require(row["outcome"] == "pass" and row["duration"] == step["elapsed_seconds"]
                        and row["execution_start_monotonic"] == step["execution_start_monotonic"]
                        and row["completed_monotonic"] == step["completed_monotonic"],"event timing differs")
                if row["stage"] in ANNOTATION_STAGES:
                    require(row["function_measurement"] == step["value"]["function_measurement"],"event/function measurement differs")
    expected=[(event,stage) for stage in STAGES for event in ("stage_started","stage_finished")]
    require(actions == expected and len(events) == 84 and Counter(r["event"] for r in events) ==
        dict(probe_started=1,stage_started=31,stage_finished=31,artifact_started=10,artifact_complete=10,probe_finished=1),"event sequence/count differs")
    require(events[0]["event"] == "probe_started" and events[-1]["event"] == "probe_finished"
            and events[-1]["outcome"] == summary["status"],"probe terminal differs")
    artifacts=summary["artifacts"]
    stages={"trace_controls.json":"trace_controls","environment.json":"environment_snapshot","runtime_config.json":"runtime_import",
        "native_inventory.json":"native.collect","native_analysis.json":"native.analyze","micro_raw_jaxpr.txt":"micro.export_jaxpr",
        "micro_stablehlo.mlir":"micro.export_stablehlo","micro_optimized_hlo.txt":"micro.export_optimized_hlo",
        "micro_first.npz":"micro_first.save_output","micro_repeat.npz":"micro_repeat.save_output"}
    require(set(artifacts) == set(stages),"artifact set differs")
    for name,item in artifacts.items():
        require(item["status"] == "complete" and item["path"] == "results/trace/"+name,"artifact identity differs")
        verify_record(root,item)
        starts=[r for r in events if r["event"] == "artifact_started" and r["artifact"] == name]
        finishes=[r for r in events if r["event"] == "artifact_complete" and r["artifact"] == name]
        require(len(starts) == len(finishes) == 1 and starts[0]["sequence"] < finishes[0]["sequence"]
                and starts[0]["path"] == item["path"]+".partial" and starts[0]["artifact_status"] == "partial"
                and finishes[0]["artifact_status"] == "complete" and all(finishes[0][k] == item[k] for k in ("path","bytes","sha256")),
                "artifact event binding differs")
        step=steps[STAGES.index(stages[name])]
        require(step["execution_start_monotonic"] <= starts[0]["monotonic"] <= finishes[0]["monotonic"] <= step["completed_monotonic"],
                "artifact not durable inside declared stage")
    numeric=verify_numerical_reports(root,summary)
    controls=read(root/"results/trace/trace_controls.json")
    require(controls["status"] == "pass" and controls["count"] == 3 and controls["synthetic"] is True
            and [r["name"] for r in controls["cases"]] == ["identified_native_regions","applications_only","cross_thread_nested_overlap"],"controls differ")
    require(summary["trace_controls"] == dict(result=controls,artifact=artifacts["trace_controls.json"]),"controls binding differs")
    # Reparse saved synthetic records only; no scientific calculation or new control case.
    for control in controls["cases"]:
        actual=analyze_trace_events(control["records"])
        require(control["status"] == "pass" and actual == control["analysis"] and actual["status"] == control["expected_status"],"saved parser control differs")
    profile=summary["profiler"]
    require(profile["start_attempts"] == profile["stop_attempts"] == 1 and profile["start_returned"] is True
            and profile["stop_returned"] is True and profile["first_error"] is None and profile["shutdown_error"] is None
            and profile["requested_options"] is None and profile["effective_defaults"] == "native_not_exposed"
            and profile["create_perfetto_link"] is False and profile["create_perfetto_trace"] is False
            and profile["log_dir"] == NATIVE,"native lifecycle differs")
    verify_runtime_and_profiler(root,summary,artifacts,steps)
    inventory=read(root/"results/trace/native_inventory.json")
    native=read(root/"results/trace/native_analysis.json")
    require(summary["native_inventory"] == dict(result=inventory,artifact=artifacts["native_inventory.json"])
            and summary["native_analysis"] == dict(result=native,artifact=artifacts["native_analysis.json"]),"native result bindings differ")
    require(inventory["status"] == "complete" and native["status"] == summary["status"]
            and summary["runtime_native_trace_observed"] == (native["status"] == "runtime_native_trace_observed"),"native outcome differs")
    current=analyze_native(root,inventory,summary) if native_analysis is None else native_analysis
    require(current == native,"saved native attribution differs from fixed parser")
    return dict(schema="hf-micro-trace-probe-verification-1",status=summary["status"],numerical=numeric,
        summary=record(root,root/"results/trace/summary.json"),events=record(root,root/PROBE_EVENTS),
        stages=31,events_count=84,graphs=1,compiled_calls=2,synchronizations=2,ready_only=1,input_ready=1,
        artifacts=10,comparisons=2,profiler_start=1,profiler_stop=1,annotations=5,scientific_admission=False)


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


def harness_metadata(root, version):
    relative = HR1_TEST if version == "HR1" else H1_TEST
    return dict(version=version, manifest_path=str(root/version/"manifest.json"),
        manifest_sha256=sha(root/version/"manifest.json"), test_path=str(root/relative),
        test_sha256=HR1_SHA if version == "HR1" else H1_SHA)


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


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
    return dict(campaign_protocol=PROTOCOL,run_id=RUN_ID,phase="P1_trace",version="R1",science_version="R1",source_version="R1",
        source_manifest_sha256=selected["input_manifest_sha256"],harness_id="HR1",
        harness_manifest_sha256=selected["harness"]["manifest_sha256"],arithmetic_harness_id="H1",
        candidate_supervisor=selected["candidate_supervisor"],supervisor_version="SUP2",supervisor_sha256_role="P1_candidate")


def verify_supervision(root):
    """Validate the saved direct-SUP2 request/receipt/raw instance proof only."""
    root=path(root);selected=read(root/"selected_source.json");manifest=read(root/"input_manifest.json")
    repo=path(manifest["repo"]);folder=root/"results/P1_supervision"
    request,receipt=read(folder/"request.json"),read(folder/"receipt.json")
    expected=supervision_identity(root)
    require(request["schema"] == "hf-micro-trace-supervision-request-1" and request["campaign_protocol"] == PROTOCOL
            and request["run_id"] == RUN_ID and request["identity"] == expected,"P1 request identity differs")
    require(all(request[k] == v for k,v in roles(root,repo).items()),"request supervisor roles differ")
    require(path(request["cwd"]) == root and request["seconds"] == 99.75 and request["rss_limit_bytes"] == 8*1024**3
            and request["telemetry_interval_seconds"] == 1.0 and request["telemetry_enabled"] is True,"P1 request budget differs")
    require(request["command"] == receipt["command"] and path(receipt["cwd"]) == root,"native request binding differs")
    require(receipt["deadline_monotonic"] == request["deadline_monotonic"] and receipt["timeout_seconds"] == 99.75
            and receipt["rss_limit_bytes"] == request["rss_limit_bytes"],"native limits differ from request")
    ledger=read(root/"ledger.json")
    require(ledger["protocol"] == PROTOCOL and ledger["run_id"] == RUN_ID and ledger["seconds"] == 180
            and ledger["scientific_admission"] is False,"parent ledger identity differs")
    phases=[p for p in ledger["phases"] if p.get("name") == "P1_trace"]
    require(len(phases) == 1,"P1 parent receipt missing or repeated")
    parent=phases[0]
    require(parent["native_receipt_sha256"] == sha(folder/"receipt.json")
            and parent["command"] == request["command"] and parent["active_deadline_monotonic"] == request["deadline_monotonic"]
            and parent["source_manifest_sha256"] == selected["input_manifest_sha256"]
            and parent["harness_manifest_sha256"] == selected["harness"]["manifest_sha256"]
            and parent["inclusive_phase_limit_seconds"] == 105 and parent["bucket"] == "P1","parent/native binding differs")
    require(request["deadline_monotonic"] == min(parent["phase_start_monotonic"]+99.75,ledger["deadline_monotonic"]-35.25),
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
    return dict(schema="hf-micro-trace-supervision-proof-1",protocol=PROTOCOL,run_id=RUN_ID,status="verified_all_instances",
        native_protocol="F-CPU-CLEAN1",cleanup_contract="CPU-CLEAN1",request=record(root,folder/"request.json"),
        receipt=record(root,folder/"receipt.json"),instances=record(root,folder/"instances.ndjson"),
        identity=expected,proof=proof,parent_phase="P1_trace",scientific_admission=False)


def verify_record(root, item):
    require(isinstance(item,dict) and isinstance(item.get("bytes"),int) and item["bytes"] >= 0,"bad artifact metadata")
    target=bound(root,item["path"])
    checked(target,item["sha256"],item["bytes"])
    return target


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
    require(path(analyze_cpu_interval.__code__.co_filename) == root/"aux/hf_repo/scripts/force_cost_evidence.py",
            "CPU analysis helper is not the frozen original")
    checked(analyze_cpu_interval.__code__.co_filename,COST_HELPER_SHA,60098)
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
        if row.get("stage") not in {name+"."+action for name in ("micro_first","micro_repeat")
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
    return dict(schema="hf-micro-trace-cpu-observation-1",protocol=PROTOCOL,run_id=RUN_ID,status="complete_acquisition",
        raw=record(root,root/CPU_FILE),records=len(records),integrity_valid=True,actual_telemetry_failure=False,
        intervals=intervals,raw_integrity=integrity_only,scientific_admission=False,
        limitation="Short/no internal sample intervals remain inconclusive; Job CPU cannot distinguish useful work, spin or scheduling.")


def svg_document(title, body, height=410):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="'+str(height)+'" viewBox="0 0 1100 '+str(height)+'">'
        '<rect width="100%" height="100%" fill="#f4f7fa"/><g font-family="Segoe UI,Arial,sans-serif" fill="#122235">'
        '<text x="32" y="40" font-size="23">'+escape(title)+'</text>'+body+'</g></svg>').encode("utf-8")


def resources_svg(resources):
    body='<text x="32" y="78" font-size="14">Pre-seal snapshot; final parent receipt separately includes seal and final binding.</text>'
    for i,row in enumerate(resources.get("phases",[])):
        text=str(row.get("name"))+': '+str(row.get("elapsed_seconds"))+' s | '+str(row.get("reason"))+' | cleanup '+str(row.get("cleanup_verified"))
        body+=f'<text x="32" y="{123+i*48}" font-size="15">{escape(text)}</text>'
    peak=resources.get("peak_tree_rss_bytes")
    body+='<text x="32" y="310" font-size="15">Sampled tree RSS: '+escape(str(peak))+' bytes / limit 8589934592 bytes</text>'
    body+='<text x="32" y="355" font-size="13">180 s total: prepare 25 / trace 105 / seal 25 / shared 25; no phase borrowing.</text>'
    return svg_document(PROTOCOL+' resource accounting',body)


def verify_runtime_and_profiler(root, summary, artifacts, steps):
    selected=read(root/"selected_source.json")
    runtime=summary["runtime"]
    require(read(root/"results/trace/runtime_config.json") == runtime
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
            and actual["jax_cpu_enable_async_dispatch"] is True and actual["jax_debug_nans"] is False and actual["jax_debug_infs"] is False
            and actual["compiler_options"] == {"xla_cpu_enable_fast_math":False,"xla_cpu_ftz":False}
            and runtime["config_mutations"] == runtime["environment_mutations"] == 0,"actual runtime contract differs")
    manifest=read(root/"input_manifest.json")
    require(runtime["python"] == manifest["python"]["version"] and path(runtime["executable"]) == path(manifest["python"]["executable"])
            and path(runtime["arithmetic"]["path"]) == root/SOURCE/"src/hf_eval/compensated_invariants.py"
            and runtime["arithmetic"]["sha256"] == CI_SHA,"actual runtime source differs")
    environment=read(root/"results/trace/environment.json")
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
    old_environment=read(root/PREFIX/"results/cost/environment.json")
    require(environment["variables"] == old_environment["variables"],"environment raw whitelist differs from F-COST1")
    reference=summary["environment_reference"]
    require(reference["path"] == PREFIX+"results/cost/environment.json" and reference["variable_count"] == 15
            and reference["exact_raw_variables_match"] is True,"environment reference assertion differs")
    verify_record(root,reference)
    profile=summary["profiler_runtime"]
    expected={r["package_relative_path"]:r for r in manifest["profile_pins"]}
    require(set(profile["installed_modules"]) == set(PROFILE_PINS)-{"jaxlib/jax_common.dll"},"profiler module set differs")
    for relative,item in profile["installed_modules"].items():
        original=expected[relative]
        require(path(item["path"]) == path(original["path"]) and item["sha256"] == original["sha256"]
                and item["bytes"] == original["bytes"] and item["actual_import"] is True,"actual profiler import identity differs")
    binary=profile["installed_binary"];original=expected["jaxlib/jax_common.dll"]
    require(path(binary["path"]) == path(original["path"]) and binary["bytes"] == original["bytes"]
            and binary["sha256"] == original["sha256"] and binary["copied"] is False,"profiler DLL pin differs")
    require(profile["preexisting_session"] is False and profile["options_requested"] is None
            and profile["effective_defaults"] == "native_not_exposed" and profile["extra_native_sessions"] == 0
            and profile["options_mutated"] is False and profile["source_verification"]["status"] == "verified"
            and profile["source_verification"]["input_manifest_sha256"] == selected_metadata(root,manifest)["input_manifest_sha256"],
            "profiler default/interface contract differs")


def stages_svg(summary):
    steps={r.get("stage"):r for r in summary.get("steps",[])}
    names=("micro_first.call","micro_first.synchronize","micro_first.ready_only",
           "micro_repeat.call","micro_repeat.synchronize","profiler.start","profiler.stop")
    body='<text x="32" y="74" font-size="12">Five micro intervals exclude annotation/persistence; profiler stages include setup/bookkeeping. Open markers are not returns.</text>'
    maximum=max([steps.get(n,{}).get("elapsed_seconds",0) for n in names if finite(steps.get(n,{}).get("elapsed_seconds"))]+[.001])
    for i,name in enumerate(names):
        row=steps.get(name,{});value=row.get("elapsed_seconds");complete=row.get("status") == "pass" and finite(value)
        label=name+": "+(format(value,".7g")+" s" if complete else row.get("status","not_reached"))
        y=110+i*35;body+=f'<text x="32" y="{y}" font-size="14">{escape(label)}</text>'
        if complete:body+=f'<rect x="500" y="{y-12}" width="{530*value/maximum:.2f}" height="15" fill="#287ca3"/>'
    return svg_document(PROTOCOL+" recorded function / profiler timeline",body)


def coverage_svg(native, cpu):
    body='<text x="32" y="77" font-size="15">Native status: '+escape(str(native.get("status","not_reached")))+'</text>'
    for i,row in enumerate(native.get("call_windows",[])):
        coverage=row.get("observed_union",{});value=coverage.get("duration_us")
        label=row["name"]+": observed union "+str(value)+" us; distinct bound regions "+str(len(row.get("regions",[])))
        body+=f'<text x="32" y="{112+i*35}" font-size="14">{escape(label)}</text>'
    body+='<text x="32" y="208" font-size="13">Native duration includes possible scheduling/waiting; never sum overlapping threads as arithmetic work.</text>'
    for i,row in enumerate(cpu.get("intervals",[])):
        analysis=row.get("analysis",{});label=row["stage"]+": "+str(analysis.get("classification") or row.get("status") or "inconclusive")
        aggregate=analysis.get("aggregate") or {}
        if aggregate:label+='; contained dt_min='+format(aggregate["dt_min"],".6g")+' s'
        body+=f'<text x="32" y="{248+i*32}" font-size="14">{escape(label)}</text>'
    body+='<text x="32" y="382" font-size="12">Original CPU threshold: ≥30 s contained coverage; adjacent dt_max ≤2.5 s. No scientific admission.</text>'
    return svg_document(PROTOCOL+" native / Job CPU coverage",body)


def seal(root, repo, events):
    problems=[]
    def observe(label, function):
        try:return function()
        except EventLogError:raise
        except Exception as error:
            detail=failure(error);problems.append(dict(stage=label,error=detail));return dict(status="incomplete_or_failed",error=detail)
    preservation=observe("sources",lambda:verify_inputs(root,include_live=True))
    write(root/"source_preservation.json",preservation)
    resources=observe("resources",lambda:read(root/"resources.json"))
    summary_path=root/"results/trace/summary.json"
    summary=observe("probe_summary",lambda:read(summary_path)) if summary_path.is_file() else dict(status="not_reached",steps=[],artifacts={})
    artifacts=observe("artifacts",lambda:saved_artifacts(root,summary));write(root/"artifact_status.json",artifacts)
    if artifacts.get("issues"):problems.extend(artifacts["issues"])
    folder=root/"results/P1_supervision"
    supervision=observe("supervision",lambda:verify_supervision(root)) if (folder/"receipt.json").is_file() else dict(status="not_reached")
    proof_file=root/"supervision_proof.json"
    if proof_file.exists():
        if observe("parent_proof",lambda:read(proof_file)) != supervision:problems.append(dict(stage="supervision",reason="parent saved proof differs"))
    else:write(proof_file,supervision)
    cpu=observe("CPU",lambda:cpu_observation(root,summary,supervision)) if (root/CPU_FILE).is_file() else dict(status="not_reached",intervals=[])
    write(root/"cpu_observation.json",cpu)
    # Incomplete native export is a diagnostic outcome, never an entrance gate to sealing.
    plan=observe("plan",lambda:read(root/"plan.json"))
    deadline=plan.get("deadline_monotonic")
    if finite(deadline):deadline-=10.25
    inventory=observe("native_inventory",lambda:collect_native(root,root/NATIVE,deadline=deadline))
    write(root/"native_manifest.json",inventory)
    native=analyze_native(root,inventory,summary) if inventory.get("status") == "complete" else dict(
        schema="hf-micro-trace-analysis-1",protocol=PROTOCOL,run_id=RUN_ID,status="observability_not_pass",
        predeclared_rule=TARGET_RULE,issues=["native_export_absent_partial_or_over_acceptance_cap"],scientific_admission=False)
    write(root/"trace_analysis.json",native)
    mapping=native.get("hlo_mapping")
    if mapping is None:
        mapping=dict(schema="hf-micro-trace-hlo-mapping-1",protocol=PROTOCOL,run_id=RUN_ID,
            status="not_observed",entry_fusions=None,optimized_hlo=None,scientific_admission=False)
        target=root/"results/trace/micro_optimized_hlo.txt"
        if target.is_file():
            try:mapping=hlo_mapping(root,{})
            except Exception as error:mapping["error"]=failure(error)
    write(root/"hlo_mapping.json",mapping)
    # Two comparisons can be complete before a failed collector/parser; preserve that separate fact.
    numeric=dict(status="not_completed",comparisons_present=list(summary.get("comparisons",{})),scientific_admission=False)
    if set(summary.get("comparisons",{})) == {"micro_first","micro_repeat"}:
        try:numeric=verify_numerical_reports(root,summary)
        except Exception as error:numeric.update(status="saved_numerical_gate_not_pass",error=failure(error))
    write(root/"numerical_verification.json",numeric)
    verification=dict(status="not_completed",probe_status=summary.get("status"),numerical=numeric,scientific_admission=False)
    completed=(summary.get("status") in ("runtime_native_trace_observed","observability_not_pass")
               and [r.get("stage") for r in summary.get("steps",[])] == list(STAGES)
               and all(r.get("status") == "pass" for r in summary.get("steps",[])))
    if completed:
        verification=observe("complete_probe",lambda:verify_probe_summary(root,native_analysis=native))
        saved_inventory=observe("probe_native_inventory",lambda:read(root/"results/trace/native_inventory.json"))
        if inventory != saved_inventory:problems.append(dict(stage="native_inventory",reason="post-cleanup native bytes or inventory differ"))
    if summary.get("status") == "runtime_native_trace_observed":
        if not (verification.get("status") == "runtime_native_trace_observed" and native.get("status") == "runtime_native_trace_observed"
                and numeric.get("status") == "saved_original_24_leaf_gates_verified"
                and supervision.get("status") == "verified_all_instances" and cpu.get("status") == "complete_acquisition"):
            problems.append(dict(stage="complete_probe",reason="claimed observation lacks numeric/native/source/CPU/instance gates"))
        receipt=observe("normal_receipt",lambda:read(folder/"receipt.json"))
        if receipt.get("reason") != "normal_exit" or receipt.get("returncode") != 0:
            problems.append(dict(stage="complete_probe",reason="claimed observation lacks normal zero exit"))
        phases=[p for p in resources.get("phases",[]) if p.get("name") == "P1_trace"]
        if len(phases) != 1 or phases[0]["elapsed_seconds"] > 105 or phases[0]["phase_return_monotonic"]-phases[0]["phase_start_monotonic"] > 105:
            problems.append(dict(stage="complete_probe",reason="claimed observation exceeded inclusive P1 budget"))
    write(root/"diagnostic_verification.json",verification)
    binary_write(root/"stages.svg",stages_svg(summary));binary_write(root/"resources.svg",resources_svg(resources))
    binary_write(root/"coverage.svg",coverage_svg(native,cpu))
    output={};enumeration_complete=True
    try:
        for filename,_ in walk_no_reparse(root,deadline=deadline):
            relative=filename.relative_to(root).as_posix()
            if relative in EXCLUDED:continue
            output[relative]=streamed_record(root,filename,deadline=deadline)["sha256"]
    except Exception as error:
        enumeration_complete=False;problems.append(dict(stage="payload_inventory",error=failure(error)))
    parent_status=resources.get("parent_status",resources.get("status"))
    diagnostic=summary.get("status","not_reached")
    if parent_status not in (None,"runtime_native_trace_observed") and diagnostic == "runtime_native_trace_observed":diagnostic=parent_status
    result=dict(schema="hf-micro-trace-evidence-worker-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,action="seal",
        status="pass" if not problems else "evidence_failure",diagnostic_status=diagnostic,
        scientific_admission=False,payload_sealed=enumeration_complete,source_preservation=preservation,
        numerical_status=numeric.get("status"),native_status=native.get("status"),supervision_status=supervision.get("status"),
        cpu_status=cpu.get("status"),issues=problems,first_probe_error=summary.get("first_error"),
        profiler=summary.get("profiler"),verification=record(root,root/"diagnostic_verification.json"),excluded=sorted(EXCLUDED),
        resources_scope="pre-seal only; final parent receipt includes seal",closed_utc=utc())
    write(root/"results/seal/summary.json",result)
    output["results/seal/summary.json"]=sha(root/"results/seal/summary.json")
    write(root/"output_sha256.json",dict(sorted(output.items())))
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
            write(destination/"summary.json",dict(schema="hf-micro-trace-evidence-worker-1",protocol=PROTOCOL,run_id=RUN_ID,
                action=args.action,elapsed_seconds=time.monotonic()-started,**result))
        events.emit("worker_finished",action=args.action,status=result["status"])
        return 0 if result["status"] == "pass" else 2
    except EventLogError:raise
    except Exception as error:
        detail=failure(error)
        if not (destination/"summary.json").exists():write(destination/"summary.json",dict(schema="hf-micro-trace-evidence-worker-1",
            protocol=PROTOCOL,run_id=RUN_ID,action=args.action,status="evidence_failure",error=detail,scientific_admission=False))
        events.emit("worker_failed",action=args.action,exception=detail);return 2
    finally:events.close()


if __name__ == "__main__":
    raise SystemExit(main())
