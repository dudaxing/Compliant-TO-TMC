"""F-TRACE2 selective evidence, bounded native trace parsing, and failure sealing.
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
import ntpath
import copy
import os
from pathlib import Path
import re
import stat
import sys
import time
import traceback
import zipfile

PROTOCOL = "F-TRACE2"
RUN_ID = "micro_trace_002"
PRIOR_RUN = "micro_trace_001"
PREFIX = "provenance/" + PRIOR_RUN + "/"
PRIOR_BINDING_SHA = "ea89c28be4d1acfff1a11fba8f1a51b139cf6625101f5df98e5951eec8d53cf7"
SOURCE = "R1/source/hf_repo"
HR1_TEST = "aux/hf_repo/tests/test_force_reuse_contract.py"
H1_TEST = "H1/tests/test_compensated_invariants.py"
REFERENCE_OLD = "data/micro_valid_first_three.npz"
REFERENCE = "data/micro_valid_first_three.npz"
CPU_FILE = "events/P1_trace_cpu.ndjson"
PROBE_EVENTS = "events/P1_trace.ndjson"
NATIVE = "native"
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

CURRENT_AUX = ("hf_repo/scripts/run_micro_trace_v2.py", "hf_repo/scripts/probe_micro_trace_v2.py",
 "hf_repo/scripts/micro_trace_v2_evidence.py", "docs/CURRENT_STATUS.md", "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md")

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


SUBJECT = "micro_native_observation"
PATH_RUN = "native_path_001"
PATH_PREFIX = "provenance/" + PATH_RUN + "/"
PATH_BINDING_SHA = "71f85687db21f5d4ce4f1b7aecf2013e3492ddf187d1591f55398e3e04e706e3"
MICRO_HELPER_SHA = "1483f2d0c31b86cce38522aefcbedae7c511197cacfb0afe12d3916db16ef8cc"
OLD_RUN_SHA = "7904a5d0e3fdfaa4107fe8716c246d5bfdc89853f8486e25d5a68d07ca6aef72"
OLD_PROBE_SHA = "5912b6ac9d717423f9d82f352ef71d7d8cf331058d856381d24c818948dfe0f6"
PATH_DRIVER_SHA = "ba82047203b9b34926bcb5aad48a04c16e877514a1f63da146643d702c764ad8"
FIXED_AUX.update({"force_cost_evidence.py":COST_HELPER_SHA,"micro_trace_evidence.py":MICRO_HELPER_SHA})
HISTORY = ("receipt_binding.json","execution_receipt.json","output_sha256.json","input_manifest.json",
 "selected_source.json","loaded_supervisors.json","results/trace/summary.json","results/trace/trace_controls.json",
 "results/trace/environment.json","results/trace/runtime_config.json","results/trace/micro_raw_jaxpr.txt",
 "results/trace/micro_stablehlo.mlir","results/trace/micro_optimized_hlo.txt","results/trace/micro_first.npz",
 "results/trace/micro_repeat.npz","cpu_observation.json","supervision_proof.json",
 "results/P1_supervision/request.json","results/P1_supervision/receipt.json","results/P1_supervision/instances.ndjson",
 "events/P1_trace.ndjson","events/P1_trace_cpu.ndjson","logs/P1_trace.log","native_manifest.json")
PATH_HISTORY = ("receipt_binding.json","execution_receipt.json","input_manifest.json","output_sha256.json",
 "results/native/summary.json","results/native/inventory.json","results/native/marker.json","diagnostic_verification.json")

def _prepin_helpers():
    folder=Path(__file__).parent
    for name,wanted in FIXED_AUX.items():
        filename=folder/name;before=os.lstat(filename)
        if stat.S_ISLNK(before.st_mode) or getattr(before,"st_file_attributes",0)&0x400:
            raise ValueError("helper reparse refused: "+str(filename))
        if hashlib.sha256(filename.read_bytes()).hexdigest() != wanted:
            raise ValueError("fixed helper SHA differs: "+name)
    for name in ("s0_event_log","s0_preparation_evidence","force_cost_evidence","s0_ad_exception","cpu_supervision_evidence"):
        loaded=sys.modules.get(name)
        if loaded is not None and Path(loaded.__file__).resolve() != (folder/(name+".py")).resolve():
            raise ValueError("preexisting helper location differs: "+name)
    return folder

_HELPER_FOLDER=_prepin_helpers()
from s0_event_log import EventLog, EventLogError
from s0_preparation_evidence import bound, checked, copy_row, path, read, require, sha, utc, write
from force_cost_evidence import analyze_cpu_interval


def active_deadline():
    raw=os.environ.get("HF_TRACE2_ACTIVE_DEADLINE")
    if raw is None:return None
    value=float(raw)
    require(finite(value),"active deadline is nonfinite")
    return value


def record_loaded_helpers(root, *, allow_canonical=False):
    root=path(root);folder=root/"aux/hf_repo/scripts";actual_folder=path(_HELPER_FOLDER)
    if allow_canonical:
        manifest=read(root/"input_manifest.json") if (root/"input_manifest.json").is_file() else None
        canonical=path(manifest["repo"])/"hf_repo/scripts" if manifest else actual_folder
        require(actual_folder in (folder,canonical),"helper directory neither frozen nor canonical")
    else:require(actual_folder == folder,"helper directory is not frozen")
    rows=[]
    for name,wanted in FIXED_AUX.items():
        filename=actual_folder/name;checked(filename,wanted)
        loaded=[]
        for module_name,module in list(sys.modules.items()):
            actual=getattr(module,"__file__",None)
            if not actual or Path(actual).name!=name:continue
            actual=path(actual);expected=filename;role="frozen_helper"
            if name=="windows_owned_process.py" and actual!=filename:
                plan=read(root/"plan.json")
                expected=path(plan["loaded_parent_supervisor"]["path"]);role="canonical_parent_control"
            require(actual==expected,"loaded helper actual path differs: "+module_name)
            checked(actual,wanted)
            loaded.append(dict(module_name=module_name,actual_import=True,path=str(actual),sha256=sha(actual),role=role))
        rows.append(dict(name=name,path=str(filename),sha256=wanted,loaded=loaded or None))
    return dict(protocol=PROTOCOL,run_id=RUN_ID,status="verified",actual_folder=str(actual_folder),helpers=rows)


def native_argument(plain_root, candidate=None):
    def normalized(value):
        require(isinstance(value,str) and not value.startswith("\\\\")
                and re.match(r"^[A-Za-z]:[\\/]",value) is not None,"ordinary drive-absolute path required")
        require(".." not in value.replace("/","\\").split("\\"),"parent traversal refused")
        return ntpath.normpath(value)
    wanted=ntpath.join(normalized(plain_root),"native")
    actual=normalized(candidate) if candidate is not None else wanted
    require(ntpath.normcase(actual) == ntpath.normcase(wanted),"native path outside fixed root/native")
    return wanted


def actual_native_path(root, plan, *, create=False):
    value=native_argument(plan["plain_root"])
    require(os.path.samefile(plan["plain_root"],root),"ordinary/extended root are not same directory")
    cursor=Path(plan["plain_root"])
    for ancestor in reversed((cursor,*cursor.parents)):regular_no_reparse(ancestor)
    folder=root/NATIVE
    if create:
        require(not folder.exists(),"native directory already exists")
        folder.mkdir()
    if folder.exists():
        require(stat.S_ISDIR(regular_no_reparse(folder).st_mode) and os.path.samefile(value,folder),
                "native ordinary path differs from frozen directory")
    return value

def historical_authority(get, *, run=PRIOR_RUN, prefix=PREFIX, names=HISTORY, digest=PRIOR_BINDING_SHA):
    checked(get("receipt_binding.json"),digest);binding=read(get("receipt_binding.json"))
    expected_protocol="F-TRACE1" if run==PRIOR_RUN else "F-PATH1"
    require(binding["protocol"] == expected_protocol and binding["run_id"] == run,"historical authority differs")
    if run==PATH_RUN:require(binding["status"] == "native_path_interface_pass","saved path qualification differs")
    for name in ("execution_receipt.json","input_manifest.json","output_sha256.json"):
        row=binding["records"][name];checked(get(name),row["sha256"],row["bytes"])
    output=read(get("output_sha256.json"));rows=[]
    for name in names:
        target=get(name)
        if name!="receipt_binding.json":
            row=binding["records"].get(name)
            if row is not None:checked(target,row["sha256"],row["bytes"])
            elif name in output:checked(target,output[name])
            else:raise ValueError("selected history lacks bound SHA: "+name)
        rows.append(dict(original_path=name,path=prefix+name,bytes=target.stat().st_size,sha256=sha(target)))
    expected_count,expected_bytes=(24,5272551) if run==PRIOR_RUN else (8,83820)
    require(len(rows)==expected_count and sum(x["bytes"] for x in rows)==expected_bytes,"selected historical inventory differs")
    return rows,read(get("input_manifest.json")),output


def source_specs(root, repo, *, archived=False):
    old=root.parent/PRIOR_RUN;old_path=root.parent/PATH_RUN
    get=(lambda n:bound(root,PREFIX+n)) if archived else (lambda n:bound(old,n))
    history,previous,output=historical_authority(get)
    get_path=(lambda n:bound(root,PATH_PREFIX+n)) if archived else (lambda n:bound(old_path,n))
    path_history,path_previous,path_output=historical_authority(get_path,run=PATH_RUN,prefix=PATH_PREFIX,names=PATH_HISTORY,digest=PATH_BINDING_SHA)
    specs=[]
    def add(name,source,digest=None,size=None,role="inherited_original"):
        specs.append(dict(path=name,source=str(path(source)),sha256=digest,bytes=size,role=role))
    for rows,folder in ((history,old),(path_history,old_path)):
        for row in rows:add(row["path"],folder/row["original_path"],row["sha256"],row["bytes"],"selected_history")
    inherited=[r for r in previous["files"] if r["role"]=="inherited_R1"]
    require(previous["derived_files"]==[] and previous["new_patch_applications"]==0 and len(inherited)==32
            and sum(r["bytes"] for r in inherited)==380009,"R1 inventory differs")
    prior_rows={r["path"]:r for r in previous["files"]}
    for row in inherited:
        require(row["path"].startswith(SOURCE+"/") and output[row["path"]]==row["sha256"],"R1 authority differs")
        add(row["path"],old/row["path"],row["sha256"],row["bytes"],"inherited_R1")
    for name,digest in ((HR1_TEST,HR1_SHA),(H1_TEST,H1_SHA),("data/inputs.npz",INPUT_SHA),(REFERENCE,REFERENCE_SHA)):
        require(output[name]==digest,"fixed harness/reference differs")
        add(name,old/name,digest,prior_rows[name]["bytes"],"inherited_reference" if name==REFERENCE else "inherited_original")
    for filename,digest in FIXED_AUX.items():
        name="aux/hf_repo/scripts/"+filename;require(output[name]==digest,"fixed auxiliary authority differs")
        add(name,old/name,digest,prior_rows[name]["bytes"],"fixed_auxiliary")
    runtime=previous["runtime_files"]
    require(len(runtime)==20 and runtime==path_previous["runtime_files"],"runtime inventory differs")
    for row in runtime:
        require(output[row["frozen_path"]]==row["sha256"],"runtime authority differs")
        add(row["frozen_path"],old/row["frozen_path"],row["sha256"],row["bytes"],"frozen_runtime_source")
    for filename,digest in (("run_micro_trace.py",OLD_RUN_SHA),("probe_micro_trace.py",OLD_PROBE_SHA)):
        name="aux/hf_repo/scripts/"+filename;require(output[name]==digest,"old author identity differs")
        add(name,old/name,digest,prior_rows[name]["bytes"],"historical_author_source")
    name="aux/hf_repo/scripts/run_native_path_diagnostic.py"
    old_row=next(r for r in path_previous["files"] if r["path"]==name)
    require(old_row["sha256"]==PATH_DRIVER_SHA and path_output[name]==PATH_DRIVER_SHA,"path driver identity differs")
    add(name,old_path/name,PATH_DRIVER_SHA,63144,"historical_author_source")
    require(len(specs)==100 and sum(r["bytes"] for r in specs)==7832416,"100 old input inventory differs")
    for name in CURRENT_AUX:add("aux/"+name,repo/name,None,None,"current_diagnostic_auxiliary")
    require(len(specs)==len({r["path"] for r in specs})==105,"exact current input inventory differs")
    return specs,history+path_history,previous,runtime,previous["installed_binary_checks"],previous["profile_pins"]


def selected_metadata(root, manifest):
    return dict(schema="hf-micro-trace-selected-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,
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
        time_remaining(active_deadline())
        checked(row["path"],row["sha256"],row["bytes"])


def prepare(root, repo, events):
    require(not any((root/n).exists() for n in ("input_manifest.json","selected_source.json","R1","H1","HR1")),"preparation must be write-once")
    deadline=active_deadline();specs,history,previous,runtime,binaries,pins=source_specs(root,repo)
    rows=[]
    for item in specs:
        time_remaining(deadline)
        rows.append(copy_row(root,item["source"],item["path"],expected=item["sha256"],size=item["bytes"],role=item["role"]))
    write(root/"inheritance_manifest.json",dict(schema="hf-micro-trace-selective-inheritance-2",protocol=PROTOCOL,run_id=RUN_ID,
        previous_binding_sha256=PRIOR_BINDING_SHA,path_binding_sha256=PATH_BINDING_SHA,historical_files=32,
        historical_bytes=5356371,rows=history,full_predecessor_payload_verified=False,
        limitation="Selected originals only; uncopied upstream references are not traversed."))
    prior_selected=read(root/PREFIX/"selected_source.json")
    descriptor=dict(path=PREFIX+"selected_source.json",sha256=sha(root/PREFIX/"selected_source.json"),
        role="carried original identity descriptor; described older manifest bodies were not carried")
    r1=[{k:r[k] for k in ("path","bytes","sha256")} for r in rows if r["role"]=="inherited_R1"]
    write(root/"R1/source_manifest.json",dict(schema="hf-micro-trace-source-relocation-2",version="R1",source=SOURCE,
        files=r1,new_patch_applications=0,upstream=dict(binding_sha256=PRIOR_BINDING_SHA,input_manifest_path=PREFIX+"input_manifest.json"),
        archived_upstream_references_not_traversed=True,identity_descriptor=dict(descriptor,source=prior_selected["source"],source_version=prior_selected["source_version"]),scientific_admission=False))
    for version,test,digest in (("H1",H1_TEST,H1_SHA),("HR1",HR1_TEST,HR1_SHA)):
        write(root/version/"manifest.json",dict(schema="hf-micro-trace-harness-relocation-2",version=version,test_path=test,
            test_sha256=digest,test_bytes_changed=False,globals_rewritten=False,upstream=dict(binding_sha256=PRIOR_BINDING_SHA),
            identity_descriptor=dict(descriptor,historical_description=prior_selected["harness" if version=="HR1" else "arithmetic_harness"]),
            full_harness_executed=False,scientific_admission=False))
    micro_ast=assert_micro_ast(root/HR1_TEST,root/"aux/hf_repo/scripts/probe_micro_trace_v2.py")
    scientific_ast=assert_scientific_ast(root)
    generated=[record(root,root/n) for n in ("inheritance_manifest.json","R1/source_manifest.json","HR1/manifest.json","H1/manifest.json")]
    manifest=dict(schema="hf-micro-trace-inputs-2",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,
        created_utc=utc(),repo=str(repo),files=rows,generated_metadata=generated,derived_files=[],new_patch_applications=0,
        inherited_candidate_files=32,historical_files=32,historical_bytes=5356371,**roles(root,repo),
        science=dict(version="R1",source=SOURCE,kernel_sha256=R1_SHA,arithmetic_sha256=CI_SHA),
        harness=harness_metadata(root,"HR1"),arithmetic_harness=harness_metadata(root,"H1"),canonical_files=previous["canonical_files"],
        python=previous["python"],packages=PACKAGES,runtime_files=runtime,installed_binary_checks=binaries,profile_pins=pins,
        inherited_supervision=previous["inherited_supervision"],micro_ast=micro_ast,scientific_ast=scientific_ast,
        target_rule=TARGET_RULE,native_caps=CAPS,scientific_admission=False)
    plan=read(root/"plan.json")
    require(plan["protocol"]==plan["campaign_protocol"]==PROTOCOL and plan["run_id"]==RUN_ID and plan["seconds"]==180
        and all(plan[k]==v for k,v in roles(root,repo).items()),"parent plan differs")
    require(plan["runner_sha256"]==sha(root/"aux/hf_repo/scripts/run_micro_trace_v2.py")
        and plan["evidence_worker_sha256"]==sha(root/"aux/hf_repo/scripts/micro_trace_v2_evidence.py"),"parent author pins differ")
    for name in CURRENT_AUX:
        item=next(r for r in rows if r["path"]=="aux/"+name)
        require(item["sha256"]==plan["author_sha256"][name],"parent author snapshot differs: "+name)
    write(root/"input_manifest.json",manifest);write(root/"selected_source.json",selected_metadata(root,manifest))
    result=verify_inputs(root,include_live=True,deadline=deadline)
    result["actual_loaded_helpers"]=record_loaded_helpers(root,allow_canonical=True)
    events.emit("preparation_complete",files=105,input_manifest_sha256=result["input_manifest_sha256"])
    return dict(status="pass",source_verification=result,scientific_admission=False)


def verify_inputs(root, include_live=False, deadline=None):
    root=path(root);manifest=read(root/"input_manifest.json");repo=path(manifest["repo"])
    require(manifest["schema"]=="hf-micro-trace-inputs-2" and manifest["protocol"]==manifest["campaign_protocol"]==PROTOCOL
        and manifest["run_id"]==RUN_ID and root==repo/"hf4_c2_stable_f_validation"/RUN_ID,"input identity differs")
    specs,history,previous,runtime,binaries,pins=source_specs(root,repo,archived=True)
    expected={r["path"]:r for r in specs};rows=manifest["files"]
    require(len(rows)==len({r["path"] for r in rows})==105 and {r["path"] for r in rows}==set(expected),"input set differs")
    for row in rows:
        time_remaining(deadline);spec=expected[row["path"]]
        require(path(row["source"])==path(spec["source"]) and row["role"]==spec["role"],"source mapping differs")
        require((spec["sha256"] is None or row["sha256"]==spec["sha256"]) and (spec["bytes"] is None or row["bytes"]==spec["bytes"]),"fixed identity differs")
        checked(bound(root,row["path"]),row["sha256"],row["bytes"])
        if include_live:checked(row["source"],row["sha256"],row["bytes"])
    plan=read(root/"plan.json")
    for name in CURRENT_AUX:
        row=next(r for r in rows if r["path"]=="aux/"+name)
        require(row["sha256"]==plan["author_sha256"][name],"author freeze differs: "+name)
    require(manifest["derived_files"]==[] and manifest["new_patch_applications"]==0 and manifest["inherited_candidate_files"]==32
        and manifest["runtime_files"]==runtime and manifest["installed_binary_checks"]==binaries and manifest["profile_pins"]==pins
        and manifest["target_rule"]==TARGET_RULE and manifest["native_caps"]==CAPS,"candidate/runtime/parser contract differs")
    require(len(manifest["generated_metadata"])==4 and {r["path"] for r in manifest["generated_metadata"]}==
        {"inheritance_manifest.json","R1/source_manifest.json","HR1/manifest.json","H1/manifest.json"},"generated metadata differs")
    for row in manifest["generated_metadata"]:checked(bound(root,row["path"]),row["sha256"],row["bytes"])
    actual={f.relative_to(root).as_posix() for f,_ in walk_no_reparse(root/SOURCE,deadline=deadline)}
    require(actual=={r["path"] for r in rows if r["role"]=="inherited_R1"},"R1 inventory differs")
    checked(root/SOURCE/"src/hf_eval/split_kernel_invariants_hu.py",R1_SHA);checked(root/SOURCE/"src/hf_eval/compensated_invariants.py",CI_SHA)
    require(read(root/"selected_source.json")==selected_metadata(root,manifest),"selected metadata differs")
    require(manifest["harness"]==harness_metadata(root,"HR1") and manifest["arithmetic_harness"]==harness_metadata(root,"H1"),"harness differs")
    require(all(manifest[k]==v for k,v in roles(root,repo).items()),"supervisor roles differ")
    require(assert_micro_ast(root/HR1_TEST,root/"aux/hf_repo/scripts/probe_micro_trace_v2.py")==manifest["micro_ast"],"micro AST differs")
    require(assert_scientific_ast(root)==manifest["scientific_ast"],"scientific AST differs")
    require(read(root/"inheritance_manifest.json")["rows"]==history,"history selection differs")
    if include_live:
        require(manifest["canonical_files"]==previous["canonical_files"] and len(manifest["canonical_files"])==30,"canonical set differs")
        for name,row in manifest["canonical_files"].items():
            time_remaining(deadline);require(path(row["path"])==repo/"hf_repo"/name,"canonical escaped repo");checked(row["path"],row["sha256"])
        canonical={"src/"+f.relative_to(repo/"hf_repo/src").as_posix() for f in (repo/"hf_repo/src").rglob("*") if f.is_file() and "__pycache__" not in f.parts}
        require(canonical=={n for n in manifest["canonical_files"] if n.startswith("src/")},"canonical inventory differs")
        for filename,digest in FIXED_AUX.items():checked(repo/"hf_repo/scripts"/filename,digest)
        for filename,digest in (("run_micro_trace.py",OLD_RUN_SHA),("probe_micro_trace.py",OLD_PROBE_SHA),("run_native_path_diagnostic.py",PATH_DRIVER_SHA)):
            checked(repo/"hf_repo/scripts"/filename,digest)
        checked(repo/"hf_repo/tests/test_force_reuse_contract.py",HR1_SHA);runtime_checks(manifest)
    return dict(status="verified",input_manifest_sha256=sha(root/"input_manifest.json"),file_count=105,bytes=sum(r["bytes"] for r in rows),
        historical_files=32,historical_bytes=5356371,inherited_R1_files=32,derived_files=0,new_patch_applications=0,
        include_live=bool(include_live),scientific_admission=False)


def time_remaining(deadline):
    deadline=active_deadline() if deadline is None else deadline
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
    deadline=active_deadline() if deadline is None else deadline
    plan=read(root/"plan.json");ordinary=actual_native_path(root,plan)
    require(os.path.normcase(os.path.abspath(folder)) == os.path.normcase(os.path.abspath(root/NATIVE)),"native log_dir differs")
    result=dict(schema="hf-micro-trace-native-inventory-1",protocol=PROTOCOL,run_id=RUN_ID,
        status="partial",files=[],issues=[],caps=CAPS,json_record=None,xplane_records=[],
        ordinary_native_argument=ordinary,ordinary_native_argument_chars=len(ordinary),
        caps_scope="post-export acceptance; not a realtime disk hard limit",
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
            relative=filename.relative_to(folder).as_posix()
            full=ntpath.join(ordinary,*Path(relative).parts)
            item=dict(path=filename.relative_to(root).as_posix(),bytes=info.st_size,sha256=None,status="unhashed",
                ordinary_full_path=full,ordinary_full_path_chars=len(full))
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



def thread_metadata(metadata, pid, tid):
    """CPU-plane admission, with exact unique legal name/sort metadata."""
    same_pid=[r for r in metadata if str(r["event"].get("pid"))==str(pid)]
    processes=[r for r in same_pid if r["event"].get("name")=="process_name"]
    issues=[]
    if len(processes)!=1:issues.append("cpu_process_name_missing_or_repeated")
    elif not isinstance(processes[0]["event"].get("args"),dict) or processes[0]["event"]["args"].get("name")!="/host:CPU":
        issues.append("not_cpu_trace_plane")
    same_thread=[r for r in same_pid if str(r["event"].get("tid"))==str(tid)]
    names=[r for r in same_thread if r["event"].get("name")=="thread_name"]
    sorts=[r for r in same_thread if r["event"].get("name")=="thread_sort_index"]
    if not names and not sorts:issues.append("thread_name_and_sort_missing")
    if len(names)>1:issues.append("thread_name_repeated")
    if len(sorts)>1:issues.append("thread_sort_index_repeated")
    for row in names:
        args=row["event"].get("args")
        if not isinstance(args,dict) or not isinstance(args.get("name"),str) or not args["name"]:
            issues.append("thread_name_invalid")
    for row in sorts:
        args=row["event"].get("args")
        if not isinstance(args,dict) or not finite(args.get("sort_index")):issues.append("thread_sort_index_invalid")
    return dict(valid=not issues,issues=issues,trace_pid=pid,trace_tid=tid,
        thread_label=names[0]["event"]["args"]["name"] if len(names)==1 and not issues else None,
        process_records=processes,thread_name_records=names,thread_sort_records=sorts,
        process_sort_records=[r for r in same_pid if r["event"].get("name")=="process_sort_index"],
        trace_identifiers_are_not_windows_ids=True)

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
    stacks={};intervals=result["intervals"];issues=result["issues"];thread_records={}
    for index,event in enumerate(events):
        if not isinstance(event,dict):issues.append(dict(index=index,reason="nonobject_event"));continue
        phase=event.get("ph");name=event.get("name");pid=event.get("pid");tid=event.get("tid")
        if phase == "M":
            result["metadata"].append(dict(index=index,event=event))
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
        key=(str(r["pid"]),str(r["tid"]))
        metadata=thread_metadata(result["metadata"],r["pid"],r["tid"]);thread_records[key]=metadata
        if not metadata["valid"]:issues.append(dict(reason="annotation_thread_metadata_invalid",details=metadata["issues"]))
    result["annotation_thread_metadata"]=[thread_records[k] for k in sorted(thread_records)]
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
        else:
            metadata=thread_metadata(result["metadata"],item["pid"],item["tid"])
            thread_records[(str(item["pid"]),str(item["tid"]))]=metadata
            if not metadata["valid"]:rejection="native_thread_metadata_invalid"
        matching=[w for w in result["call_windows"] if str(w["trace_pid"]) == str(item["pid"])
                  and w["start_us"] <= item["ts"] <= item["end"] <= w["end_us"]]
        if source and len(matching) != 1:rejection="execution_region_not_wholly_in_one_same_plane_call_sync_window"
        if rejection:
            result["rejected_regions"].append(dict(indices=item["indices"],name=name,reason=rejection));continue
        accepted=dict(item,window=matching[0]["name"],thread_label=thread_records[(str(item["pid"]),str(item["tid"]))]["thread_label"],thread_metadata=thread_records[(str(item["pid"]),str(item["tid"]))])
        result["native_regions"].append(accepted);matching[0]["regions"].append(item["indices"])
    for window in result["call_windows"]:
        spans=[(r["ts"],r["end"]) for r in result["native_regions"] if r["window"] == window["name"]]
        window["observed_union"]=interval_union(spans)
        if not spans:issues.append(dict(window=window["name"],reason="no_uniquely_bound_native_execution_interval"))
    if not issues:result["status"]="runtime_native_trace_observed"
    result["native_plane_metadata_rule"]="Unique /host:CPU process_name; unique legal nonempty thread_name or finite nonbool thread_sort_index."
    result["attribution_status"]="current_micro_windows_bound" if result["status"]=="runtime_native_trace_observed" else "attribution_inconclusive"
    result["limitation"]="Observed runtime regions may include scheduling or waiting; unions are not arithmetic-work percentages."
    return result


def trace_controls(root):
    """Exactly sixteen groups call the same real path/classifier/parser code."""
    root=path(root);cases=[];plan=read(root/"plan.json");plain=plan["plain_root"]
    wanted=native_argument(plain)
    require(wanted==ntpath.join(ntpath.normpath(plain),"native"),"ordinary path control differs")
    cases.append(dict(name="ordinary_path_admitted",status="pass",result=wanted))
    try:native_argument(plain,ntpath.join(ntpath.dirname(plain),"outside"))
    except ValueError as error:cases.append(dict(name="outside_path_rejected",status="pass",rejected=True,error=str(error)))
    else:raise ValueError("outside path control admitted")
    filename=root/"aux/hf_repo/scripts/run_micro_trace_v2.py"
    row=next(r for r in read(root/"input_manifest.json")["files"] if r["path"]=="aux/hf_repo/scripts/run_micro_trace_v2.py")
    checked(filename,row["sha256"],row["bytes"])
    import importlib.util
    spec=importlib.util.spec_from_file_location("_ftrace2_control_driver",filename)
    driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
    require(path(driver.__file__)==filename,"control driver actual file differs")
    checked(driver.__file__,row["sha256"],row["bytes"])
    expected=supervision_identity(root)
    counts=dict(graph_count=1,trace=1,lower=1,compile=1,compiled_call=2,output_synchronization=2,ready_only=1,input_ready=1,
        micro_leaf_count=24,profiler_start=1,profiler_stop=1,annotations=5,warmup=0,retries=0,force_calls=0,ad_calls=0)
    golden=dict(schema="hf-micro-trace-probe-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,
        identity=expected,mode="trace",phase="P1_trace",source_version="R1",source_manifest_sha256=expected["source_manifest_sha256"],
        expected_stages=list(STAGES),secondary_record_errors=[],compiler_options_execution=dict(jax_jit={"xla_cpu_enable_fast_math":False,"xla_cpu_ftz":False},
            lowered_compile={"xla_cpu_enable_fast_math":False,"xla_cpu_ftz":False},jax_jit_returned=True,lowered_compile_returned=True,frozen_ast_verified=True),
        status="runtime_native_trace_observed",scientific_admission=False,
        force_executed=False,first_error=None,first_error_kind=None,errors=[],controls_passed=16,trace_controls=dict(result=dict(status="pass",count=16,synthetic=True,cases=[dict(status="pass")]*16)),
        completed_counts=counts,execution_contract=counts,
        steps=[dict(stage=n,status="pass") for n in STAGES],
        comparisons={n:dict(status="pass",field_count=24,fields={str(i):dict(status="pass",signed_zero_checked=True,dtype="float64" if i<18 else "bool") for i in range(24)}) for n in ("micro_first","micro_repeat")},
        artifacts={n:dict(status="complete") for n in ("trace_controls.json","environment.json","runtime_config.json","native_inventory.json",
            "native_analysis.json","micro_raw_jaxpr.txt","micro_stablehlo.mlir","micro_optimized_hlo.txt","micro_first.npz","micro_repeat.npz")},
        native_inventory=dict(result=dict(status="complete")),native_analysis=dict(result=dict(status="runtime_native_trace_observed")),
        runtime_native_trace_observed=True,numerical_contract_pass=True,
        profiler=dict(start_attempts=1,start_returned=True,body_attempts=1,body_returned=True,stop_attempts=1,stop_returned=True,
            start_error=None,body_error=None,stop_error=None,pre_body_error=None,first_error=None,shutdown_error=None,
            native_start_error=None,native_stop_error=None,shutdown_errors=[],requested_options=None,create_perfetto_link=False,
            create_perfetto_trace=False,log_dir="native"))
    raw=dict(reason="normal_exit",returncode=0,cleanup_verified=True,cleanup_proof={"pass":True},errors=[],
        telemetry_status="complete",telemetry_first_error=None,protocol="F-CPU-CLEAN1",cleanup_contract="CPU-CLEAN1",
        candidate_supervisor=expected["candidate_supervisor"],supervisor_sha256=SUP2_SHA)
    err=dict(type="JaxRuntimeError",module="jax.errors",message="synthetic native stop failure",traceback="control-only")
    negative=copy.deepcopy(golden);negative.update(status="observability_not_pass",runtime_native_trace_observed=False,first_error=err,first_error_kind="native_interface",errors=[err])
    negative["profiler"].update(stop_returned=False,stop_error=err,native_stop_error=err,first_error=err,shutdown_error=err)
    nonzero=dict(raw,reason="nonzero_exit",returncode=1);inconsistent=copy.deepcopy(negative);inconsistent["profiler"]["stop_attempts"]=2
    variants=(("successful_phase",raw,golden,"runtime_native_trace_observed"),
        ("nonzero_native_error",nonzero,negative,"observability_not_pass"),
        ("nonzero_missing_summary",nonzero,None,"execution_failure"),
        ("nonzero_inconsistent_lifecycle",nonzero,inconsistent,"execution_failure"),
        ("resource_stop_preserved",dict(nonzero,reason="global_deadline"),negative,"resource_stop"),
        ("supervision_error_preserved",dict(nonzero,reason="supervision_error",errors=["synthetic"]),negative,"supervision_not_pass"),
        ("cleanup_failure_preserved",dict(raw,cleanup_verified=False,cleanup_proof={"pass":False}),golden,"cleanup_not_pass"))
    for name,receipt,summary,status in variants:
        actual=driver.classify(receipt,summary,expected,source_ok=True,proof_ok=True)
        require(actual["status"]==status and actual["passed"] is (status=="runtime_native_trace_observed")
                and actual["raw_reason"]==receipt["reason"] and actual["raw_returncode"]==receipt["returncode"],"classification control differs: "+name)
        cases.append(dict(name=name,status="pass",result=actual,expected_status=status))
    base=[dict(ph="M",name="process_name",pid=1,args=dict(name="/host:CPU"))]
    base += [dict(ph="M",name="thread_name",pid=1,tid=t,args=dict(name="synthetic_"+str(t))) for t in (7,8,9)]
    for name,ts,dur in zip(ANNOTATIONS,(0,12,115,200,212),(10,100,10,10,100)):
        base.append(dict(ph="X",name=name,pid=1,tid=7,ts=ts,dur=dur,args={}))
    work=[dict(ph="X",name="CpuExecutable::Execute",pid=1,tid=8,ts=t,dur=108,args=dict(hlo_module="jit_reused")) for t in (2,202)]
    overlap=[dict(ph="B",name="ThunkExecutor::Execute",pid=1,tid=9,ts=20,args=dict(module_name="jit_reused")),dict(ph="E",pid=1,tid=9,ts=30)]
    for name,rows,status in (("identified_native_regions",base+work,"runtime_native_trace_observed"),
        ("applications_only",base,"observability_not_pass"),("cross_thread_nested_overlap",base+work+overlap,"runtime_native_trace_observed")):
        analysis=analyze_trace_events(rows);require(analysis["status"]==status,"trace control differs: "+name)
        if name=="cross_thread_nested_overlap":require([w["observed_union"]["duration_us"] for w in analysis["call_windows"]]==[108,108],"interval double count")
        cases.append(dict(name=name,status="pass",records=rows,analysis=analysis,expected_status=status))
    sorted_base=[r for r in base if r.get("name")!="thread_name"]
    sorted_base += [dict(ph="M",name="thread_sort_index",pid=1,tid=t,args=dict(sort_index=t)) for t in (7,8)]
    legal=analyze_trace_events(sorted_base+work)
    require(legal["status"]=="runtime_native_trace_observed" and all(x["thread_label"] is None for x in legal["native_regions"]),"sort-only CPU plane not recognized")
    cases.append(dict(name="cpu_plane_sort_only",status="pass",records=sorted_base+work,analysis=legal,expected_status="runtime_native_trace_observed"))
    for name,rows in (("thread_metadata_missing",[r for r in sorted_base if r.get("name")!="thread_sort_index"]+work),
        ("duplicate_thread_metadata",sorted_base+work+[dict(ph="M",name="thread_sort_index",pid=1,tid=7,args=dict(sort_index=7))])):
        analysis=analyze_trace_events(rows);require(analysis["status"]=="observability_not_pass","illegal metadata admitted: "+name)
        cases.append(dict(name=name,status="pass",records=rows,analysis=analysis,expected_status="observability_not_pass"))
    rejected=[]
    for label,value in (("bool",True),("NaN",float("nan")),("Inf",float("inf"))):
        rows=copy.deepcopy(sorted_base+work)
        next(r for r in rows if r.get("name")=="thread_sort_index" and r.get("tid")==7)["args"]["sort_index"]=value
        analysis=analyze_trace_events(rows);require(analysis["status"]=="observability_not_pass","illegal sort admitted: "+label)
        rejected.append(dict(input_kind=label,rejected=True,status=analysis["status"],issues=analysis["issues"]))
    cases.append(dict(name="illegal_sort_values",status="pass",rejections=rejected,nonfinite_values_serialized=False))
    require(len(cases)==16,"control group count differs")
    return dict(schema="hf-micro-trace-controls-2",protocol=PROTOCOL,run_id=RUN_ID,status="pass",count=16,
        groups=dict(path=2,classification=7,trace=3,metadata=4),synthetic=True,cases=cases,
        classifier_source=dict(path=row["path"],sha256=row["sha256"]),native_sessions=0,scientific_admission=False)


def hlo_mapping(root, analysis):
    filename=root/"results/trace/micro_optimized_hlo.txt";text=filename.read_text(encoding="utf-8")
    match=re.match(r"HloModule\s+([A-Za-z0-9_.-]+),",text.splitlines()[0])
    require(match is not None and match.group(1)==TARGET_RULE["module"],"current optimized HLO target differs")
    entry=False;producers=[]
    for line_number,line in enumerate(text.splitlines(),1):
        if line.startswith("ENTRY "):entry=True
        if not entry:continue
        if line.strip()=="}":break
        m=re.search(r"^\s*(?:ROOT )?%?([\w.-]+)\s*=",line)
        if m:
            computation=re.search(r"\bfusion\(.*\bcalls=%?([\w.-]+)",line)
            producers.append(dict(producer=m.group(1),computation=computation.group(1) if computation else None,line=line_number,
                is_fusion=computation is not None))
    whole_pass=analysis.get("status")=="runtime_native_trace_observed" and not analysis.get("issues")
    mapped=[]
    for row in producers:
        accepted=[];candidates=[]
        for event in analysis.get("intervals",[]):
            args=event["args"] if isinstance(event["args"],dict) else {}
            exact=event["name"]==row["producer"] or any(args.get(k)==row["producer"] for k in ("hlo_op","hlo_instruction","op_name"))
            if not exact:continue
            candidate=dict(indices=event["indices"],name=event["name"],ts=event["ts"],dur=event["dur"],pid=event["pid"],tid=event["tid"],args=event["args"])
            reason=None;association=None;window=None
            if not whole_pass:reason="overall_native_source_annotation_timing_gate_not_pass"
            elif any(k in args and args[k]!=TARGET_RULE["module"] for k in TARGET_RULE["exact_arg_keys"]):
                reason="conflicting_direct_module_identity"
            else:
                contained=[r for r in analysis.get("native_regions",[]) if str(r["pid"])==str(event["pid"])
                    and str(r["tid"])==str(event["tid"]) and r["ts"]<=event["ts"]<=event["end"]<=r["end"]]
                container_conflicts=[r for r in contained if isinstance(r.get("args"),dict)
                    and any(k in r["args"] and r["args"][k]!=TARGET_RULE["module"] for k in TARGET_RULE["exact_arg_keys"])]
                nested_windows={r["window"] for r in contained}
                windows=[w for w in analysis.get("call_windows",[]) if str(w["trace_pid"])==str(event["pid"])
                    and w["start_us"]<=event["ts"]<=event["end"]<=w["end_us"]]
                direct=any(args.get(k)==TARGET_RULE["module"] for k in TARGET_RULE["exact_arg_keys"])
                if container_conflicts:reason="containing_native_region_conflicting_direct_module_identity"
                elif len(nested_windows)==1:
                    window=next(iter(nested_windows));association="same_plane_same_thread_nested_in_current_module"
                elif len(nested_windows)>1:reason="multiple_call_windows_or_module_association"
                elif direct and len(windows)==1:
                    window=windows[0]["name"];association="own_direct_current_module_and_unique_call_window"
                else:reason="no_unique_same_thread_or_explicit_direct_module_association"
                if window is not None and len(windows)!=1:reason="producer_not_in_unique_current_call_window"
            candidate.update(rejection_reason=reason,module_association=association,window=window);candidates.append(candidate)
            if reason is None:accepted.append(dict(candidate,module=TARGET_RULE["module"],observed_interval=[event["ts"],event["end"]]))
        unions={}
        for name in ("micro_first","micro_repeat"):
            spans=[r["observed_interval"] for r in accepted if r["window"]==name]
            if spans:unions[name]=interval_union(spans)
        mapped.append(dict(**row,observations=accepted or None,candidate_events=candidates,
            observation_null_reason=None if accepted else ("overall_native_gate_not_pass" if not whole_pass else "no_uniquely_associated_exact_producer"),
            observed_union_by_window=unions if accepted else None))
    return dict(schema="hf-micro-trace-hlo-mapping-2",protocol=PROTOCOL,run_id=RUN_ID,module=match.group(1),
        optimized_hlo=record(root,filename),entry_producers=mapped,entry_fusions=[r for r in mapped if r["is_fusion"]],producer_count=len(producers),
        overall_native_gate_pass=whole_pass,status="some_producers_observed" if any(r["observations"] for r in mapped) else "fusion_attribution_inconclusive",
        rule="Exact current ENTRY name/direct producer metadata, then unique current-module/call association; whole native gate required.",
        limitation="Union is observed coverage including possible scheduling/waiting; not arithmetic work or exclusive compute cost.",
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
        document,body_size=parse_native_json(filename,deadline=active_deadline())
        result=analyze_trace_events(document["traceEvents"])
        result.update(json_record=inventory["json_record"],uncompressed_bytes=body_size,native_interface_status="single_session_originals_and_json_verified",
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
        require(len(measurements)==5,"five measured annotations incomplete")
        require(summary.get("micro_hlo_module")==TARGET_RULE["module"],"probe/current HLO module differs")
        if result["issues"]:result["status"]="observability_not_pass"
        result["hlo_mapping"]=hlo_mapping(root,result)
    except Exception as error:
        result["status"]="observability_not_pass";result["issues"].append(failure(error))
        if (root/"results/trace/micro_optimized_hlo.txt").is_file():
            try:result["hlo_mapping"]=hlo_mapping(root,result)
            except Exception as mapping_error:result["hlo_mapping_error"]=failure(mapping_error)
    return result


def verify_numerical_reports(root, summary):
    """Only saved comparisons and ZIP central directories, never array decoding."""
    with zipfile.ZipFile(root/REFERENCE) as archive:members=archive.namelist()
    require(len(members) == len(set(members)) == 48,"historical NPZ member inventory differs")
    keys={n.removeprefix("R1__").removesuffix(".npy") for n in members if n.startswith("R1__") and n.endswith(".npy")}
    require(len(keys) == 24,"historical R1 leaf inventory differs")
    steps={r["stage"]:r for r in summary.get("steps",[])};comparisons=summary.get("comparisons",{})
    historical=read(root/PREFIX/"results/trace/summary.json")["comparisons"]
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
            and summary["run_id"] == RUN_ID and summary["mode"] == "trace" and summary["source_version"] == "R1"
            and summary["subject"]==SUBJECT and summary["identity"]==supervision_identity(root),"probe identity differs")
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
    counts.update(warmup=0,retries=0,force_calls=0,ad_calls=0)
    require(summary["completed_counts"]==counts and summary["execution_contract"]==counts
        and all(type(v) is int for v in summary["completed_counts"].values()),"execution counts differ")
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
    stop=steps[STAGES.index("profiler.stop")]
    stop_events=[r for r in events if r.get("stage")=="profiler.stop"]
    require(len(stop_events)==2 and stop["stage_events_written_after_native_completion"] is True
        and stop["started_utc"] is None and all(r["written_after_native_completion"] is True
            and r["monotonic"]>=stop["completed_monotonic"] for r in stop_events),"stop event writes precede actual completion")
    require(stop_events[0]["actual_api_start_monotonic"]==stop["execution_start_monotonic"]
        and stop_events[0]["actual_api_end_monotonic"]==stop["completed_monotonic"],"stop API interval event differs")
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
    require(controls["status"]=="pass" and controls["count"]==len(controls["cases"])==16 and controls["synthetic"] is True
        and controls["groups"]==dict(path=2,classification=7,trace=3,metadata=4)
        and all(r["status"]=="pass" for r in controls["cases"]),"sixteen control groups differ")
    expected_names=("ordinary_path_admitted","outside_path_rejected","successful_phase","nonzero_native_error",
        "nonzero_missing_summary","nonzero_inconsistent_lifecycle","resource_stop_preserved","supervision_error_preserved",
        "cleanup_failure_preserved","identified_native_regions","applications_only","cross_thread_nested_overlap",
        "cpu_plane_sort_only","thread_metadata_missing","duplicate_thread_metadata","illegal_sort_values")
    require(tuple(r["name"] for r in controls["cases"])==expected_names,"control group identity differs")
    require(summary["trace_controls"]==dict(result=controls,artifact=artifacts["trace_controls.json"])
        and summary["controls_passed"]==16,"controls binding differs")
    # Reparse already saved finite synthetic records; no new control invocation.
    for control in controls["cases"]:
        if "records" in control:
            actual=analyze_trace_events(control["records"])
            require(actual==control["analysis"] and actual["status"]==control["expected_status"],"saved parser control differs")
    rejects=controls["cases"][-1]["rejections"]
    require([r["input_kind"] for r in rejects]==["bool","NaN","Inf"]
        and all(r["rejected"] is True and r["status"]=="observability_not_pass" for r in rejects)
        and controls["cases"][-1]["nonfinite_values_serialized"] is False,"illegal sort saved rejection record differs")
    profile=summary["profiler"]
    require(all(type(profile[k]) is int and profile[k]==1 for k in ("start_attempts","body_attempts","stop_attempts"))
            and profile["body_returned"] is True and profile["start_returned"] is True
            and profile["stop_returned"] is True and profile["first_error"] is None and profile["shutdown_error"] is None
            and all(profile[k] is None for k in ("start_error","body_error","stop_error","pre_body_error"))
            and profile["requested_options"] is None and profile["effective_defaults"] == "native_not_exposed"
            and profile["create_perfetto_link"] is False and profile["create_perfetto_trace"] is False
            and profile["log_dir"] == NATIVE,"native lifecycle differs")
    require(summary["compiler_options_execution"]==dict(jax_jit={"xla_cpu_enable_fast_math":False,"xla_cpu_ftz":False},
        lowered_compile={"xla_cpu_enable_fast_math":False,"xla_cpu_ftz":False},jax_jit_returned=True,lowered_compile_returned=True,frozen_ast_verified=True),"two actual strict compilation options differ")
    require(summary["numerical_contract_pass"] is True and summary["force_executed"] is False,"numeric/force scope differs")
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



def assert_scientific_ast(root):
    names=("micro_function","compile_graph","load_kernel","prepare_inputs","compare_output","observe_output")
    trees=[ast.parse((root/name).read_text(encoding="utf-8")) for name in
        ("aux/hf_repo/scripts/probe_micro_trace.py","aux/hf_repo/scripts/probe_micro_trace_v2.py")]
    rows=[]
    for name in names:
        dumps=[]
        for tree in trees:
            nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
            require(len(nodes)==1,"science function missing/duplicate: "+name)
            dumps.append(ast.dump(nodes[0],include_attributes=False))
        require(dumps[0]==dumps[1],"original scientific AST differs: "+name)
        rows.append(dict(name=name,ast_sha256=hashlib.sha256(dumps[0].encode()).hexdigest()))
    return dict(status="pass",functions=rows,scientific_operations_changed=False)

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
    return dict(campaign_protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,phase="P1_trace",version="R1",science_version="R1",source_version="R1",
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
    _prepin_helpers()
    import cpu_supervision_evidence as cleanup
    require(path(cleanup.__file__) == root/"aux/hf_repo/scripts/cpu_supervision_evidence.py","proof helper is not frozen")
    checked(cleanup.__file__,HELPER_SHA,71013)
    proof=cleanup.proof_evidence(root,folder,"receipt.json",receipt,expected)
    return dict(schema="hf-micro-trace-supervision-proof-1",protocol=PROTOCOL,run_id=RUN_ID,status="verified_all_instances",
        native_protocol="F-CPU-CLEAN1",cleanup_contract="CPU-CLEAN1",request=record(root,folder/"request.json"),
        receipt=record(root,folder/"receipt.json"),instances=record(root,folder/"instances.ndjson"),
        identity=expected,proof=proof,parent_phase="P1_trace",scientific_admission=False)



def proof_report(root):
    return verify_supervision(root)

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
    old_environment=read(root/PREFIX/"results/trace/environment.json")
    require(environment["variables"] == old_environment["variables"],"environment raw whitelist differs from F-TRACE1")
    reference=summary["environment_reference"]
    require(reference["path"] == PREFIX+"results/trace/environment.json" and reference["variable_count"] == 15
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


def stages_svg(summary, native=None):
    native=native or {};steps={r.get("stage"):r for r in summary.get("steps",[])}
    names=("micro_first.call","micro_first.synchronize","micro_first.ready_only","micro_repeat.call","micro_repeat.synchronize","profiler.start","profiler.stop")
    body='<text x="32" y="74" font-size="12">Application function wall (blue); each bar has its own origin. Open records are not returns.</text>'
    maximum=max([steps.get(n,{}).get("elapsed_seconds",0) for n in names if finite(steps.get(n,{}).get("elapsed_seconds"))]+[.001])
    for i,name in enumerate(names):
        row=steps.get(name,{});value=row.get("elapsed_seconds");complete=row.get("status")=="pass" and finite(value)
        label=name+": "+(format(value,".7g")+" s" if complete else row.get("status","not_reached"))
        y=110+i*35;body+=f'<text x="32" y="{y}" font-size="14">{escape(label)}</text>'
        if complete:body+=f'<rect x="500" y="{y-12}" width="{530*value/maximum:.2f}" height="15" fill="#287ca3"/>'
    body+='<text x="32" y="386" font-size="13">Native call-window coverage (green) uses only the native clock; grey is unobserved/unknown.</text>'
    passed=native.get("status")=="runtime_native_trace_observed" and not native.get("issues")
    windows=native.get("call_windows",[])
    for i,name in enumerate(("micro_first","micro_repeat")):
        y=430+i*55;body+=f'<text x="32" y="{y}" font-size="14">{escape(name)}</text>'
        body+=f'<rect x="500" y="{y-13}" width="530" height="18" fill="#d2d6db"/>'
        rows=[w for w in windows if w["name"]==name]
        if passed and len(rows)==1:
            w=rows[0];span=w["end_us"]-w["start_us"]
            if span>0:
                for a,b in w["observed_union"]["intervals"]:
                    x=500+530*(a-w["start_us"])/span;size=530*(b-a)/span
                    body+=f'<rect x="{x:.2f}" y="{y-13}" width="{size:.2f}" height="18" fill="#318b68"/>'
            label='bound native regions; may include waiting or scheduling'
        else:label='unknown / no complete current-module observation gate'
        body+=f'<text x="500" y="{y+22}" font-size="12">{escape(label)}</text>'
    body+='<text x="32" y="552" font-size="12">Native and monotonic clocks are not origin-aligned; producer intervals are not exclusive compute time.</text>'
    return svg_document(PROTOCOL+" application / saved native evidence",body,height=590)


def coverage_svg(native, cpu, *, numeric=None, inventory=None, supervision=None):
    numeric=numeric or {};inventory=inventory or {};supervision=supervision or {}
    mapping=native.get("hlo_mapping",{})
    layers=(('Numerical saved original 24-leaf gates',numeric.get("status","not_reached")),
        ('Native export / original inventory',inventory.get("status","not_reached")),
        ('Internal current-micro source / annotations / timing',native.get("status","not_reached")),
        ('ENTRY producer / fusion association',mapping.get("status","not_observed")),
        ('Same-instance coverage / handle cleanup',supervision.get("status","not_reached")))
    body=''
    for i,(name,status) in enumerate(layers):
        body+=f'<text x="32" y="{86+i*37}" font-size="14">{escape(name+": "+str(status))}</text>'
    body+='<text x="32" y="286" font-size="12">Layers stay separate: export and numerical pass do not prove native costs or scientific admission.</text>'
    for i,row in enumerate(cpu.get("intervals",[])):
        analysis=row.get("analysis",{});label=row["stage"]+": "+str(analysis.get("classification") or row.get("status") or "inconclusive")
        aggregate=analysis.get("aggregate") or {}
        if aggregate:label+='; contained dt_min='+format(aggregate["dt_min"],".6g")+' s'
        body+=f'<text x="32" y="{328+i*34}" font-size="14">{escape(label)}</text>'
    body+='<text x="32" y="464" font-size="12">Job CPU gate: ≥30 s contained samples, adjacent dt_max ≤2.5 s. No sum of two waits.</text>'
    body+='<text x="32" y="491" font-size="12">Observed unions can include waiting/scheduling; missing producer observations remain null.</text>'
    return svg_document(PROTOCOL+" independent evidence coverage",body,height=520)


def seal(root, repo, events):
    problems=[]
    def observe(label, function):
        try:return function()
        except EventLogError:raise
        except Exception as error:
            detail=failure(error);problems.append(dict(stage=label,error=detail));return dict(status="incomplete_or_failed",error=detail)
    preservation=observe("sources",lambda:verify_inputs(root,include_live=True))
    try:preservation["actual_loaded_helpers"]=record_loaded_helpers(root,allow_canonical=True)
    except Exception as error:
        detail=failure(error);preservation["helper_location_error"]=detail;problems.append(dict(stage="loaded_helpers",error=detail))
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
    deadline=active_deadline()
    if deadline is None:
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
            try:mapping=hlo_mapping(root,native)
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
    binary_write(root/"stages.svg",stages_svg(summary,native));binary_write(root/"resources.svg",resources_svg(resources))
    binary_write(root/"coverage.svg",coverage_svg(native,cpu,numeric=numeric,inventory=inventory,supervision=supervision))
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
        profiler=summary.get("profiler"),verification=record(root,root/"diagnostic_verification.json"),excluded=sorted(EXCLUDED),actual_loaded_helpers=preservation.get("actual_loaded_helpers"),
        resources_scope="pre-seal only; final parent receipt includes seal",closed_utc=utc())
    write(root/"results/seal/summary.json",result)
    output["results/seal/summary.json"]=sha(root/"results/seal/summary.json")
    write(root/"output_sha256.json",dict(sorted(output.items())))
    events.emit("seal_complete",status=result["status"],diagnostic_status=result["diagnostic_status"],output_manifest_sha256=sha(root/"output_sha256.json"))
    return result


def main():
    time_remaining(active_deadline())
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
