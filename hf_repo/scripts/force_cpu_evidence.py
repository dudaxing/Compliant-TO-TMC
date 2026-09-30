"""Read/copy/hash-only evidence and saved Job-CPU analysis for F-REUSE2.

No scientific imports, subprocesses, test execution or profiling.
Preparation copies the sealed R1 bytes; no patch is applied or reconstructed.
verify_snapshot is a read-only interface. The parent owns timing and final binding.
"""
from __future__ import annotations

import argparse
import ast
import re
from collections import Counter
from decimal import Decimal
import hashlib
from html import escape
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

from s0_event_log import EventLog
from s0_preparation_evidence import (
    INPUT_SHA, bound, checked, copy_row, path, read, require, sha, utc, write,
)
from force_observation_evidence import (
    ARITHMETIC, ARITHMETIC_SHA, KERNEL, KERNEL_SHA, TEST, H1_TEST, H1_TEST_SHA,
    H1_MANIFEST, RUNTIME_FILES, FORCE_STAGES, FORCE_ARTIFACTS,
    binary_write, inventory, read_probe,
    artifact_observations, resource_svg as old_resource_svg, stages_svg as old_stages_svg,
)

PROTOCOL = "F-REUSE2"
RUN_ID = "force_reuse_002"
NATIVE_PROTOCOL = "F-REUSE1"
PRIOR_RUN = "force_reuse_001"
PRIOR_PREFIX = "provenance/"+PRIOR_RUN+"/"
PRIOR_ANCHOR = "c4cd4303e584eea5d5579496f0fc123e47b51aad05f2ed9be72be683f6df6eb8"
PRIOR_INPUT_SHA = "e0667118faabf39dc34edb6ddaadde5c5766c796050cf6c363b108d343ece759"
PRIOR_OUTPUT_SHA = "eec9ae46b1bd429a6bee70ac129be8ebd531c41d33884fbd303046d5b05ea513"
PRIOR_R1_SHA = "83aac2b7dd38b85aafbc6d6693b544b160a6cc003604caa54ec970bbb20ea902"
PRIOR_PROOF_SHA = "5c71bb5c85227428bd842652dfca378bbf9a0a864064e74a81007a7f2b4eb8be"
PRIOR_RECEIPT_SHA = "7b5f606e11481c491fd2c3ffb195ff42a85913ee8ffeb1653af794a06c9eb549"
R1_KERNEL_SHA = "630babc9c299ef2336835df18a50521f51d439dc09e3353ae6d0776d91937970"
HR1_TEST_SHA = "28e696175d572379527e6a021365dacf445fa4dd28f73cb381925d95bfb383d5"
PATCH_SHA = "b5f8612604cbb15935b3e87434075f93ee6e2f1f95b221c0892c159669a15e9d"
PARENT_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
CANDIDATE_SHA = "b5f149e1cd3d6d9b4ad392123e410b786606f120f2e078139b7bacc97f2d9499"
PROOF_HELPER_SHA = "2d378c64705461d58fa966528a347b6e411431402877663fd546f3fec8912f45"
OLD_C1_SHA = "384708b23842d9d4c9d3324d57c854911772ca3eb9ab15ac9edb7efd6a1c4564"
OLD_H1_SHA = "0999cf0e0270aa08c630569a7cb7136655910370b80a6e0fc6f68382fbadf358"
OBS_RUN = "force_cpu_observe_001"
OBS_PREFIX = "provenance/"+OBS_RUN+"/"
SCIENCE_MANIFEST = OBS_PREFIX+"provenance/jit_ad_ready_001/C1/source_manifest.json"
CPU_PATH = "events/P2_force_cpu.ndjson"
FORCE_EVENTS = "events/P2_force.ndjson"
SUPERVISION = "results/P2_supervision"
LOCAL_TEST = "hf_repo/tests/test_force_reuse_contract.py"
PATCH = "hf_repo/scripts/force_reuse_candidate.patch"
HR1_MANIFEST = "HR1/manifest.json"
R1_MANIFEST = "R1/source_manifest.json"
REFERENCE_DIR = "provenance/force_reference/unit__near_rotation"
REFERENCE_SOURCE = "hf4_c2_stable_f_validation/near_rotation_segments_001/inputs/unit__near_rotation"
REFERENCES = {
    "hp_0.json": (47008,"af5fedf386fea8e77474363abd5798932250830f8c6d6b09b319c8d7c4f72869"),
    "result.json": (11792,"f05123413d64a93a1535d6e6c30a67dfa799de6e0e5565d8903211c9bf14028e"),
}
REFERENCE_INDEX_SHA = "47657b4851f1a0bb8039c96a67b2ec10cab98c48f2934ea953e58eb207873f43"
PRIOR_BINDINGS = {
    "plan_sha256":"plan.json", "input_manifest_sha256":"input_manifest.json",
    "harness_manifest_sha256":"HR1/manifest.json", "arithmetic_harness_manifest_sha256":"H1/manifest.json",
    "selected_source_sha256":"selected_source.json", "receipt_sha256":"execution_receipt.json",
    "output_manifest_sha256":"output_sha256.json", "cpu_observation_sha256":"cpu_observation.json",
    "cpu_trace_sha256":"events/P2_force_cpu.ndjson", "supervision_receipt_sha256":"results/P2_supervision/receipt.json",
    "instance_trace_sha256":"results/P2_supervision/instances.ndjson", "supervision_proof_sha256":"supervision_proof.json",
    "loaded_supervisors_sha256":"loaded_supervisors.json",
    "local_supervision_receipt_sha256":"results/P1_supervision/receipt.json",
    "local_instance_trace_sha256":"results/P1_supervision/instances.ndjson",
    "local_contract_sha256":"results/local/summary.json", "local_contract_details_sha256":"results/local/contract.json",
    "force_reference_checks_sha256":"results/force/three_force_gates.json",
    "candidate_derivation_sha256":"R1/proof.json", "candidate_manifest_sha256":"R1/source_manifest.json",
    "inheritance_manifest_sha256":"inheritance_manifest.json",
    "seal_event_sha256":"events/P3_seal.ndjson", "seal_log_sha256":"logs/P3_seal.log",
}
PRIOR_NULL_BINDINGS = {"cpu_trace_sha256","supervision_receipt_sha256","instance_trace_sha256","force_reference_checks_sha256"}
PRIOR_EXTRA_FILES = {"output_sha256.json","receipt_binding.json","execution_receipt.json","events/P3_seal.ndjson","logs/P3_seal.log"}
AUX_FILES = tuple("hf_repo/scripts/"+name+".py" for name in (
    "run_force_cpu","probe_force_cpu","force_cpu_evidence","force_observation_evidence",
    "probe_s0_preparation","s0_preparation_evidence","s0_event_log","s0_ad_exception",
    "windows_owned_process","windows_owned_process_sup2","cpu_supervision_evidence")) + (
    "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md","docs/CURRENT_STATUS.md",PATCH,LOCAL_TEST)
FIXED_AUX = {
    PATCH:PATCH_SHA,
    LOCAL_TEST:HR1_TEST_SHA,
    "hf_repo/scripts/windows_owned_process.py":PARENT_SHA,
    "hf_repo/scripts/windows_owned_process_sup2.py":CANDIDATE_SHA,
    "hf_repo/scripts/cpu_supervision_evidence.py":PROOF_HELPER_SHA,
    "hf_repo/scripts/force_observation_evidence.py":"5cf32343b9c7ec481dcf8cd7a0f683b7980815798981a3649b35bbca806750d1",
    "hf_repo/scripts/probe_s0_preparation.py":"bdd3d6c1f3b933de9268f9a7a64e67d7ddc96697f15ac8e237047fdc74abfd98",
    "hf_repo/scripts/s0_preparation_evidence.py":"666540e91569bfabef88a48399a80c6d5809401d39660231c2e6a203f2640ec9",
    "hf_repo/scripts/s0_event_log.py":"7f305d479d3f19216a7339eeb25c8c7ce24372a0f68c6492b265f90ac1b62c90",
    "hf_repo/scripts/s0_ad_exception.py":"03107b0b6f7142837833a4ad367550dbbbb523e0222316093624d66d939acb7d",
}
OUTPUT_FIELD_NAMES = {"residual","material_residual","regularization_residual","material_energy",
    "stress_first_piola","stress_second_piola","small_branch","arithmetic_supported"} | {
    name+suffix for name in ("F","G","Hu","J","B","delta") for suffix in ("","_hi","_lo")}
PACKAGES = {"numpy":"2.4.6","jax":"0.11.0","jaxlib":"0.11.0","pytest":"9.1.1","psutil":"7.2.2"}


def roles(root, repo):
    return dict(
        parent_supervisor=dict(version="SUP1",path=str(root/"aux/hf_repo/scripts/windows_owned_process.py"),sha256=PARENT_SHA),
        candidate_supervisor=dict(version="SUP2",path=str(root/"aux/hf_repo/scripts/windows_owned_process_sup2.py"),sha256=CANDIDATE_SHA),
        loaded_parent_supervisor=dict(version="SUP1",path=str(repo/"hf_repo/scripts/windows_owned_process.py"),sha256=PARENT_SHA))


def history_destination(name):
    """Relocate only this immediate sealed predecessor, never any old row.source."""
    if name.startswith(("C1/source/hf_repo/","R1/source/hf_repo/","data/","provenance/")) or name in (H1_TEST,"H1/proof.json","H1/patch.diff"):
        return name
    return PRIOR_PREFIX+name


def selected_history(get):
    checked(get("receipt_binding.json"),PRIOR_ANCHOR)
    binding=read(get("receipt_binding.json"))
    require(binding["protocol"] == binding["campaign_protocol"] == NATIVE_PROTOCOL
            and binding["run_id"] == PRIOR_RUN,"F-REUSE1 anchor identity differs")
    require({k for k in binding if k.endswith("_sha256")} == set(PRIOR_BINDINGS),"unhandled predecessor binding")
    require({k for k in PRIOR_BINDINGS if binding[k] is None} == PRIOR_NULL_BINDINGS,"predecessor null targets differ")
    authority={"receipt_binding.json":PRIOR_ANCHOR}
    for key,name in PRIOR_BINDINGS.items():
        if key in PRIOR_NULL_BINDINGS:
            require(not get(name).exists(),"unreached predecessor binding target exists")
        else:
            checked(get(name),binding[key]);authority[name]=binding[key]
    require(binding["input_manifest_sha256"] == PRIOR_INPUT_SHA and binding["output_manifest_sha256"] == PRIOR_OUTPUT_SHA
            and binding["candidate_manifest_sha256"] == PRIOR_R1_SHA and binding["candidate_derivation_sha256"] == PRIOR_PROOF_SHA
            and binding["receipt_sha256"] == PRIOR_RECEIPT_SHA,"fixed predecessor anchors differ")
    old=read(get("input_manifest.json"));outputs=read(get("output_sha256.json"))
    oldrows={r["path"]:r for r in old["files"]};derived={r["path"]:r for r in old["derived_files"]}
    require(old["protocol"] == old["campaign_protocol"] == NATIVE_PROTOCOL and old["run_id"] == PRIOR_RUN
            and len(old["files"]) == len(oldrows) == 248 and len(old["derived_files"]) == len(derived) == 32
            and not set(oldrows).intersection(derived) and len(outputs) == 327,"predecessor inventories differ")
    active={n for n in oldrows if not n.startswith("aux/")} | set(derived)
    require(len(active) == 265 and len(active-set(derived)) == 233,"predecessor active inventory differs")
    selected=set(outputs)|PRIOR_EXTRA_FILES
    require(len(selected) == 332 and not set(outputs).intersection(PRIOR_EXTRA_FILES)
            and set(authority) <= selected and (set(oldrows)|set(derived)) <= set(outputs),"direct recovery inventory differs")
    rows=[]
    for name in sorted(selected):
        digest=authority.get(name,outputs.get(name))
        require(digest and (name not in outputs or outputs[name] == digest),"predecessor authority conflict")
        checked(get(name),digest);size=get(name).stat().st_size
        for inventory_rows in (oldrows,derived):
            if name in inventory_rows:
                require(inventory_rows[name]["sha256"] == digest and inventory_rows[name]["bytes"] == size,"predecessor input/candidate differs")
        destination=history_destination(name)
        require(destination == (name if name in active else PRIOR_PREFIX+name),"recovery destination differs from declared mapping")
        rows.append(dict(original_path=name,path=destination,bytes=size,sha256=digest))
    require(len({r["path"] for r in rows}) == 332 and sum(r["bytes"] for r in rows) == 8732392
            and sum(r["bytes"] for r in rows if r["path"] == r["original_path"]) == 6755017,"recovery count or bytes differ")
    candidate=read(get(R1_MANIFEST));proof=read(get("R1/proof.json"))
    require(candidate["files"] == old["derived_files"] and candidate["schema"] == "hf-force-reuse-candidate-1"
            and candidate["version"] == "R1" and candidate["changed_paths"] == [KERNEL]
            and candidate["patch"] == dict(path="aux/"+PATCH,sha256=PATCH_SHA)
            and candidate["proof"] == dict(path="R1/proof.json",sha256=PRIOR_PROOF_SHA),"predecessor candidate provenance differs")
    require(proof["patch_applications"] == 1 and proof["candidate_kernel_sha256"] == R1_KERNEL_SHA
            and proof["parent_kernel_sha256"] == KERNEL_SHA and proof["patch_sha256"] == PATCH_SHA,"original derivation proof differs")
    require(old["science"]["candidate_manifest_sha256"] == PRIOR_R1_SHA
            and old["science"]["kernel_sha256"] == R1_KERNEL_SHA
            and old["harness"]["manifest_sha256"] == sha(get(HR1_MANIFEST))
            and old["arithmetic_harness"]["manifest_sha256"] == sha(get(H1_MANIFEST))
            and old["inheritance_manifest"]["sha256"] == sha(get("inheritance_manifest.json")),"predecessor internal bindings differ")
    require(read(get("results/seal/summary.json"))["status"] == "pass"
            and read(get("source_preservation.json"))["status"] == "pass"
            and read(get("execution_receipt.json"))["status"] == "resource_or_supervision_stop","predecessor closure differs")
    require(old["inherited_supervision"]["tests"] == 21 and old["inherited_supervision"]["proofs"] == 10
            and old["inherited_supervision"]["executed_in_this_card"] is False,"inherited CLEAN1 identity differs")
    require(read(get(HR1_MANIFEST))["test_sha256"] == HR1_TEST_SHA and read(get(H1_MANIFEST))["test_sha256"] == H1_TEST_SHA,
            "inherited harness bytes differ")
    return dict(schema="hf-force-reuse-inheritance-1",protocol=PROTOCOL,run_id=RUN_ID,root=PRIOR_RUN,
        binding_sha256=PRIOR_ANCHOR,files=332,bytes=8732392,rows=rows,payload_count=327,carried_payload_count=327,
        active_files=265,active_bytes=6755017,archived_files=67,archived_bytes=1977375,
        omitted_payloads=[],omitted_duplicate_ledger=dict(path="ledger.json",same_as="execution_receipt.json",bytes=22142,
            sha256=PRIOR_RECEIPT_SHA,rechecked_at_direct_origin_during_preparation=True),
        obsolete_absolute_sources_dereferenced=False,full_old_payload_reverified=True,
        earlier_omitted_IR_status="metadata only; no earlier omitted IR payload reverified")


def structural_proof(before, after):
    """AST admission for this finite patch; no scientific module is executed."""
    old,new = ast.parse(before),ast.parse(after)
    dump=lambda n:ast.dump(n,include_attributes=False)
    functions=lambda tree:{n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    a,b=functions(old),functions(new)
    require(set(b)-set(a) == {"_kinematics_vmap_axes","_without_tangent_reusing"}
            and set(a)-set(b) == set(),"candidate added/removed unexpected functions")
    changed={name for name in a if dump(a[name]) != dump(b[name])}
    require(changed == {"_response","_guarded_batch"},"candidate changed unrelated functions")
    require([dump(x) for x in a["_response"].body[2:]] == [dump(x) for x in b["_response"].body[2:]],
            "response body after kinematics changed")
    args=b["_response"].args
    require([x.arg for x in args.kwonlyargs] == ["_kinematics_values"] and len(args.kw_defaults) == 1
            and isinstance(args.kw_defaults[0],ast.Constant) and args.kw_defaults[0].value is None,
            "optional cache default differs")
    require(dump(a["_response"].args) == dump(ast.arguments(posonlyargs=args.posonlyargs,args=args.args,vararg=args.vararg,
            kwonlyargs=[],kw_defaults=[],kwarg=args.kwarg,defaults=args.defaults)),"response positional signature changed")
    oldguard,newguard=a["_guarded_batch"],b["_guarded_batch"]
    require(dump(oldguard.args) == dump(newguard.args),"guard signature changed")
    stripped=lambda f:[dump(x) for x in f.body if not isinstance(x,ast.FunctionDef) or x.name != "evaluate"]
    require(stripped(oldguard) == stripped(newguard),"guard/valid/reject/cond changed")
    evold=next(x for x in oldguard.body if isinstance(x,ast.FunctionDef) and x.name == "evaluate")
    evnew=next(x for x in newguard.body if isinstance(x,ast.FunctionDef) and x.name == "evaluate")
    require(len(evnew.body) == len(evold.body)+1 and isinstance(evnew.body[0],ast.If)
            and ast.unparse(evnew.body[0].test) == "not tangent"
            and not evnew.body[0].orelse and [dump(x) for x in evnew.body[1:]] == [dump(x) for x in evold.body],
            "tangent path changed")
    def top_rest(tree):
        result=[]
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id == "KERNEL_VERSION" for t in n.targets):continue
            result.append(dump(n))
        return result
    require(top_rest(old) == top_rest(new),"candidate changed module definitions outside version/functions")
    versions=[n.value.value for n in new.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id == "KERNEL_VERSION" for t in n.targets) and isinstance(n.value,ast.Constant)]
    require(versions == ["p26_q1_split_invariants_hu_force_reuse_r1"],"candidate version differs")
    require("stop_gradient" not in after,"candidate stop_gradient is forbidden")
    return dict(status="pass",changed_functions=sorted(changed),added_functions=sorted(set(b)-set(a)),
        response_tail_ast_unchanged=True,guard_reject_cond_ast_unchanged=True,tangent_path_ast_unchanged=True,
        full_ad_executed=False,scientific_admission=False)


def arithmetic_harness_metadata(root):
    m=read(root/H1_MANIFEST)
    require(m["version"] == "H1" and m["test_path"] == H1_TEST and m["test_sha256"] == H1_TEST_SHA,
            "H1 relocation identity differs")
    checked(root/H1_TEST,H1_TEST_SHA)
    require(m["upstream_manifest_path"] == PRIOR_PREFIX+H1_MANIFEST
            and m["upstream_manifest_sha256"] == sha(root/PRIOR_PREFIX/H1_MANIFEST),"H1 upstream differs")
    for n,digest in m["proof_artifacts"].items():checked(bound(root,n),digest)
    return dict(version="H1",manifest_path=str(root/H1_MANIFEST),manifest_sha256=sha(root/H1_MANIFEST),
                test_path=str(root/H1_TEST),test_sha256=H1_TEST_SHA)


def harness_metadata(root):
    m=read(root/HR1_MANIFEST);test="aux/"+LOCAL_TEST
    require(m["version"] == "HR1" and m["test_path"] == test and m["protocol"] == PROTOCOL
            and m["arithmetic_harness"] == arithmetic_harness_metadata(root) and m["test_sha256"] == HR1_TEST_SHA
            and m["relocation_only"] is True and m["native_protocol"] == NATIVE_PROTOCOL and m["native_run_id"] == PRIOR_RUN
            and m["upstream_manifest"] == dict(path=PRIOR_PREFIX+HR1_MANIFEST,sha256=sha(root/PRIOR_PREFIX/HR1_MANIFEST)),"HR1 identity differs")
    checked(root/test,m["test_sha256"])
    return dict(version="HR1",manifest_path=str(root/HR1_MANIFEST),manifest_sha256=sha(root/HR1_MANIFEST),
                test_path=str(root/test),test_sha256=m["test_sha256"])


def selected_metadata(root):
    m=read(root/"input_manifest.json")
    return dict(schema="hf-force-cpu-selected-source-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,
        version="R1",source=str(root/"R1/source/hf_repo"),source_manifest=str(root/"input_manifest.json"),
        source_manifest_sha256=sha(root/"input_manifest.json"),harness=harness_metadata(root),
        arithmetic_harness=arithmetic_harness_metadata(root),original_science_manifest_sha256=OLD_C1_SHA,
        **roles(root,path(m["repo"])),scientific_admission=False)


def runtime_checks(manifest):
    from importlib.metadata import version
    require(sys.version == manifest["python"]["version"] and manifest["packages"] == PACKAGES,"Python/runtime metadata differs")
    require({name:version(name) for name in PACKAGES} == PACKAGES,"runtime package metadata differs")
    for key,count in (("runtime_file_checks",3),("stdlib_file_checks",1)):
        require(len(manifest[key]) == count,"runtime primary-source count differs")
        for row in manifest[key]:checked(row["path"],row["sha256"],row["bytes"])


def reference_bindings(root):
    checked(root/"data/original_output_sha256.json",REFERENCE_INDEX_SHA)
    original=read(root/"data/original_output_sha256.json");freeze=read(root/"data/input_freeze.json")
    checked(root/"data/inputs.npz",INPUT_SHA)
    require(original["unit__near_rotation/inputs.npz"] == INPUT_SHA and freeze["case"] == "unit__near_rotation"
            and freeze["input_sha256"] == INPUT_SHA and original["unit__near_rotation/input_freeze.json"] == sha(root/"data/input_freeze.json"),
            "reference/input authority differs")
    rows=[]
    for name,(size,digest) in REFERENCES.items():
        require(original["unit__near_rotation/"+name] == digest,"reference is not bound by original output")
        checked(root/REFERENCE_DIR/name,digest,size)
        rows.append(dict(path=REFERENCE_DIR+"/"+name,bytes=size,sha256=digest))
    return dict(case="unit__near_rotation",direction=0,input_sha256=INPUT_SHA,output_index_sha256=REFERENCE_INDEX_SHA,files=rows,
                hp_recomputed=False)


def candidate_relocation_metadata(root):
    """Describe unchanged inherited bytes; this function neither patches nor writes."""
    inherited=read(root/PRIOR_PREFIX/R1_MANIFEST)["files"]
    return dict(schema="hf-force-reuse-candidate-relocation-1",protocol=PROTOCOL,run_id=RUN_ID,version="R1",
        source=str(root/"R1/source/hf_repo"),baseline_source=str(root/"C1/source/hf_repo"),
        upstream_manifest_sha256=OLD_C1_SHA,
        upstream_manifest=dict(path=PRIOR_PREFIX+R1_MANIFEST,sha256=PRIOR_R1_SHA),
        proof=dict(path=PRIOR_PREFIX+"R1/proof.json",sha256=PRIOR_PROOF_SHA),
        patch=dict(path="aux/"+PATCH,sha256=PATCH_SHA),files=inherited,changed_paths=[KERNEL],
        relocation_only=True,new_patch_applications=0,inherited_candidate_files=32,
        scientific_admission=False)


def science_metadata(root):
    return dict(version="R1",source=str(root/"R1/source/hf_repo"),baseline_source=str(root/"C1/source/hf_repo"),
        upstream_manifest_sha256=OLD_C1_SHA,upstream_manifest_path=SCIENCE_MANIFEST,
        arithmetic_sha256=ARITHMETIC_SHA,kernel_sha256=R1_KERNEL_SHA,
        candidate_manifest_path=R1_MANIFEST,candidate_manifest_sha256=sha(root/R1_MANIFEST))


def prepare(root, repo, events):
    require(not any((root/n).exists() for n in ("input_manifest.json","C1","R1","H1","HR1","selected_source.json")),"preparation is write-once")
    plan=read(root/"plan.json");declared=roles(root,repo)
    require(all(plan[k] == v for k,v in declared.items()),"parent plan supervisor roles differ")
    old=root.parent/PRIOR_RUN;get=lambda n:bound(old,n)
    inheritance=selected_history(get);rows=[]
    checked(get("ledger.json"),PRIOR_RECEIPT_SHA,22142)
    require(get("ledger.json").read_bytes() == get("execution_receipt.json").read_bytes(),"omitted predecessor ledger is not the exact receipt duplicate")
    for row in inheritance["rows"]:
        copied=copy_row(root,get(row["original_path"]),row["path"],expected=row["sha256"],size=row["bytes"],role="direct_FREUSE1_original")
        copied["original_path"]=row["original_path"];rows.append(copied)
    write(root/"inheritance_manifest.json",inheritance)
    events.emit("historical_subset_verified",root=PRIOR_RUN,files=332,bytes=8732392,binding_sha256=PRIOR_ANCHOR)
    for name in AUX_FILES:
        rows.append(copy_row(root,repo/name,"aux/"+name,expected=FIXED_AUX.get(name),role="current_execution_auxiliary"))
    require(len(rows) == len({r["path"] for r in rows}) == 347,"source original count differs")
    write(root/H1_MANIFEST,dict(schema="hf-force-reuse-arithmetic-harness-1",version="H1",test_path=H1_TEST,test_sha256=H1_TEST_SHA,
        relocation_only=True,test_bytes_changed=False,upstream_manifest_path=PRIOR_PREFIX+H1_MANIFEST,
        upstream_manifest_sha256=sha(root/PRIOR_PREFIX/H1_MANIFEST),inherited_test_count=9,tests_executed_in_this_card=False,
        proof_artifacts={n:sha(root/n) for n in ("H1/proof.json","H1/patch.diff")}))
    write(root/HR1_MANIFEST,dict(schema="hf-force-reuse-local-harness-1",protocol=PROTOCOL,version="HR1",test_path="aux/"+LOCAL_TEST,
        test_sha256=HR1_TEST_SHA,arithmetic_harness=arithmetic_harness_metadata(root),full_ad_admission=False,
        relocation_only=True,native_protocol=NATIVE_PROTOCOL,native_run_id=PRIOR_RUN,
        upstream_manifest=dict(path=PRIOR_PREFIX+HR1_MANIFEST,sha256=sha(root/PRIOR_PREFIX/HR1_MANIFEST))))
    baseline=root/"C1/source/hf_repo";source=root/"R1/source/hf_repo"
    candidate=candidate_relocation_metadata(root)
    write(root/R1_MANIFEST,candidate)
    canonical={}
    require(inventory(repo/"hf_repo/src") == inventory(baseline/"src") and len(inventory(baseline/"src")) == 29,"canonical inventory differs")
    for name in sorted(inventory(baseline/"src")):
        rel="src/"+name;checked(repo/"hf_repo"/rel,sha(baseline/rel));canonical[rel]=dict(path=str(repo/"hf_repo"/rel),sha256=sha(baseline/rel))
    checked(repo/"hf_repo"/TEST,H1_TEST_SHA);canonical[TEST]=dict(path=str(repo/"hf_repo"/TEST),sha256=H1_TEST_SHA)
    oldmanifest=read(root/PRIOR_PREFIX/"input_manifest.json")
    manifest=dict(schema="hf-force-cpu-inputs-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,created_utc=utc(),repo=str(repo),
        files=rows,derived_files=[],inherited_candidate_files=candidate["files"],new_patch_applications=0,**declared,
        science=science_metadata(root),harness=harness_metadata(root),arithmetic_harness=arithmetic_harness_metadata(root),canonical_files=canonical,
        inheritance_manifest=dict(path="inheritance_manifest.json",sha256=sha(root/"inheritance_manifest.json")),
        force_reference=reference_bindings(root),original_input=dict(case="unit__near_rotation",direction=0,input_sha256=INPUT_SHA),
        python=dict(executable=sys.executable,version=oldmanifest["python"]["version"]),packages=PACKAGES,
        runtime_file_checks=oldmanifest["runtime_file_checks"],stdlib_file_checks=oldmanifest["stdlib_file_checks"],
        inherited_supervision=oldmanifest["inherited_supervision"],current_tests="HR1_local_only",scientific_admission=False)
    runtime_checks(manifest);write(root/"input_manifest.json",manifest);write(root/"selected_source.json",selected_metadata(root))
    result=verify_snapshot(root,repo)
    events.emit("preparation_complete",input_manifest_sha256=sha(root/"input_manifest.json"),selected=read(root/"selected_source.json"))
    return dict(status="pass",files=347,derived_files=0,inherited_candidate_files=32,new_patch_applications=0,
        copied_bytes=sum(r["bytes"] for r in rows),source_verification=result,scientific_admission=False)


def verify_snapshot(root, repo=None, *, require_live=True):
    """Read/hash/AST only; no patch reconstruction and no obsolete source traversal."""
    root=path(root);manifest=read(root/"input_manifest.json");repo=path(repo if repo is not None else manifest["repo"])
    require(manifest["schema"] == "hf-force-cpu-inputs-1" and manifest["protocol"] == manifest["campaign_protocol"] == PROTOCOL
            and manifest["run_id"] == RUN_ID and repo == path(manifest["repo"]),"manifest identity differs")
    rows=manifest["files"];names={r["path"] for r in rows}
    require(len(rows) == len(names) == 347,"frozen input count differs")
    copied_history=selected_history(lambda n:bound(root,history_destination(n)))
    require(manifest["inheritance_manifest"]["path"] == "inheritance_manifest.json","inheritance path differs")
    checked(root/"inheritance_manifest.json",manifest["inheritance_manifest"]["sha256"])
    require(read(root/"inheritance_manifest.json") == copied_history,"inheritance mapping differs")
    expected={r["path"]:(root.parent/PRIOR_RUN/r["original_path"],r["sha256"],r["bytes"],"direct_FREUSE1_original") for r in copied_history["rows"]}
    expected.update({"aux/"+n:(repo/n,FIXED_AUX.get(n),None,"current_execution_auxiliary") for n in AUX_FILES})
    require(names == set(expected),"input set differs")
    for row in rows:
        source,digest,size,role=expected[row["path"]]
        require(path(row["source"]) == path(source) and row["role"] == role,"source mapping escaped direct originals")
        require((digest is None or row["sha256"] == digest) and (size is None or row["bytes"] == size),"input authority differs")
        checked(bound(root,row["path"]),row["sha256"],row["bytes"])
        if require_live:checked(source,row["sha256"],row["bytes"])
    if require_live:
        checked(root.parent/PRIOR_RUN/"ledger.json",PRIOR_RECEIPT_SHA,22142)
        require((root.parent/PRIOR_RUN/"ledger.json").read_bytes() == (root.parent/PRIOR_RUN/"execution_receipt.json").read_bytes(),
                "omitted predecessor ledger changed")
    declared=roles(root,repo);plan=read(root/"plan.json")
    require(all(manifest[k] == v == plan[k] for k,v in declared.items()),"supervisor role binding differs")
    checked(root/SCIENCE_MANIFEST,OLD_C1_SHA)
    baseline=root/"C1/source/hf_repo";source=root/"R1/source/hf_repo";candidate=read(root/R1_MANIFEST)
    checked(root/R1_MANIFEST,manifest["science"]["candidate_manifest_sha256"])
    require(candidate == candidate_relocation_metadata(root),"candidate relocation metadata differs")
    inherited=candidate["files"]
    require(manifest["derived_files"] == [] and manifest["new_patch_applications"] == 0
            and inherited == manifest["inherited_candidate_files"] and len(inherited) == len({r["path"] for r in inherited}) == 32,
            "candidate is not solely inherited")
    original=read(root/SCIENCE_MANIFEST)["files"]
    require(len(original) == 32 and inventory(baseline) == {r["path"].removeprefix("C1/source/hf_repo/") for r in original}
            and inventory(source) == inventory(baseline),"baseline/candidate files changed")
    inputrows={r["path"]:r for r in rows}
    for row in original:checked(bound(root,row["path"]),row["sha256"],row["bytes"])
    require(sum(r["bytes"] for r in inherited) == 380009,"inherited candidate bytes differ")
    for row in inherited:
        require(row["path"].startswith("R1/source/hf_repo/") and row["baseline_path"] == row["path"].replace("R1/","C1/",1)
                and row["path"] in inputrows and all(row[k] == inputrows[row["path"]][k] for k in ("bytes","sha256")),"inherited candidate row escaped inputs")
        checked(bound(root,row["path"]),row["sha256"],row["bytes"])
        if row["path"] != "R1/source/hf_repo/"+KERNEL:checked(root/row["baseline_path"],row["sha256"],row["bytes"])
    checked(root/"aux"/PATCH,PATCH_SHA,1873);checked(source/KERNEL,R1_KERNEL_SHA,15191)
    checked(root/PRIOR_PREFIX/R1_MANIFEST,PRIOR_R1_SHA);checked(root/PRIOR_PREFIX/"R1/proof.json",PRIOR_PROOF_SHA)
    before=(baseline/KERNEL).read_text(encoding="utf-8");after=(source/KERNEL).read_text(encoding="utf-8")
    checks=structural_proof(before,after)
    proof=read(root/PRIOR_PREFIX/"R1/proof.json")
    require(all(proof[k] == v for k,v in checks.items()) and proof["patch_applications"] == 1
            and proof["candidate_kernel_sha256"] == R1_KERNEL_SHA and proof["parent_kernel_sha256"] == KERNEL_SHA
            and proof["patch_sha256"] == PATCH_SHA,"inherited original derivation proof differs")
    require(manifest["science"] == science_metadata(root),"science identity differs")
    checked(baseline/KERNEL,KERNEL_SHA);checked(source/ARITHMETIC,ARITHMETIC_SHA)
    require(manifest["harness"] == harness_metadata(root) and manifest["arithmetic_harness"] == arithmetic_harness_metadata(root),"harness differs")
    require(manifest["force_reference"] == reference_bindings(root),"reference binding differs")
    require(read(root/"selected_source.json") == selected_metadata(root),"selected source differs")
    if require_live:
        require(len(manifest["canonical_files"]) == 30 and inventory(repo/"hf_repo/src") == inventory(baseline/"src"),"canonical inventory differs")
        for name,row in manifest["canonical_files"].items():
            require(path(row["path"]) == repo/"hf_repo"/name,"canonical path escaped")
            checked(row["path"],row["sha256"]);checked(root/H1_TEST if name == TEST else baseline/name,row["sha256"])
    runtime_checks(manifest)
    return dict(status="pass",input_files=347,input_bytes=sum(r["bytes"] for r in rows),derived_files=0,
        inherited_candidate_files=32,new_patch_applications=0,C1_files=32,historical_files=332,historical_bytes=8732392,
        canonical_files=30,missing=0,mismatches=0,live_new_sources_checked=bool(require_live),obsolete_historical_live_sources_checked=False,
        input_manifest_sha256=sha(root/"input_manifest.json"),harness_manifest_sha256=sha(root/HR1_MANIFEST),
        arithmetic_harness_manifest_sha256=sha(root/H1_MANIFEST),upstream_science_manifest_sha256=OLD_C1_SHA,scientific_admission=False)


def read_ndjson(filename):
    """Retain every readable row and report corruption; never drop bad lines silently."""
    def finite_float(text):
        value = float(text)
        require(math.isfinite(value),"nonfinite JSON number")
        return value
    def invalid_constant(text):
        raise ValueError("nonstandard JSON constant: "+text)
    rows, problems = [], []
    if not filename.exists():
        return rows,[dict(reason="missing",path=str(filename))]
    raw = filename.read_bytes()
    for number,line in enumerate(raw.splitlines(keepends=True),1):
        if not line.endswith(b"\n"):
            problems.append(dict(line=number,reason="incomplete_line"))
        try:
            value = json.loads(line,parse_float=finite_float,parse_constant=invalid_constant)
            require(isinstance(value,dict),"row is not an object")
            rows.append(dict(line=number,record=value))
        except Exception as error:
            problems.append(dict(line=number,reason="unparseable",error=str(error)))
    return rows,problems


def finite_number(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def supervision_identity(root, phase="P2_force"):
    selected=read(root/"selected_source.json")
    require(phase in ("P1_local","P2_force"),"unexpected supervision phase")
    return dict(campaign_protocol=PROTOCOL,run_id=RUN_ID,phase=phase,version="R1",science_version="R1",source_version="R1",
        source_manifest_sha256=selected["source_manifest_sha256"],harness_id="HR1",
        harness_manifest_sha256=selected["harness"]["manifest_sha256"],arithmetic_harness_id="H1",
        candidate_supervisor=selected["candidate_supervisor"],supervisor_version="SUP2",
        supervisor_sha256_role="P1_P2_candidate")


def supervision_phase(root, repo, resources, phase):
    """Read a saved native receipt with the immutable CLEAN1 proof checker."""
    result=dict(phase=phase,status="not_reached",native_protocol="F-CPU-CLEAN1",cleanup_contract="CPU-CLEAN1",
        scientific_admission=False,issues=[],artifacts={})
    folder=root/("results/P1_supervision" if phase == "P1_local" else SUPERVISION)
    for name in ("request.json","receipt.json","instances.ndjson"):
        p=folder/name
        if p.is_file():result["artifacts"][name]=dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
    if not result["artifacts"]:return result
    try:
        require(set(result["artifacts"]) == {"request.json","receipt.json","instances.ndjson"},"saved supervision artifacts incomplete")
        request,receipt=read(folder/"request.json"),read(folder/"receipt.json");expected=supervision_identity(root,phase)
        require(request["schema"] == "hf-force-cpu-supervision-request-1" and request["campaign_protocol"] == PROTOCOL
                and request["run_id"] == RUN_ID and request["identity"] == expected,"phase request identity differs")
        require(all(request[k] == v for k,v in roles(root,repo).items()),"phase request roles differ")
        require(path(request["cwd"]) == root and request["seconds"] == (294.75 if phase == "P1_local" else 239.75)
                and request["rss_limit_bytes"] == 8*1024**3,"phase request limits differ")
        if phase == "P2_force":
            require(request["telemetry_interval_seconds"] == 1. and request["telemetry_enabled"] is True,"CPU interval differs")
        else:
            require(request["telemetry_interval_seconds"] is None and request["telemetry_enabled"] is False
                    and receipt.get("telemetry_status") == "disabled","P1 unexpectedly collected CPU")
        phases=[p for p in resources.get("phases",[]) if p.get("name") == phase]
        require(len(phases) == 1,"parent phase receipt absent or repeated");parent=phases[0]
        require(parent["native_receipt_sha256"] == sha(folder/"receipt.json")
                and parent["command"] == request["command"] == receipt["command"]
                and parent["active_deadline_monotonic"] == request["deadline_monotonic"]
                and path(receipt["cwd"]) == root,"request/native/parent binding differs")
        require(path(receipt["cleanup_proof"]["journal"]["path"]) == folder/"instances.ndjson","journal path differs")
        import cpu_supervision_evidence as cleanup
        require(path(cleanup.__file__) == root/"aux/hf_repo/scripts/cpu_supervision_evidence.py","proof helper outside frozen aux")
        checked(cleanup.__file__,PROOF_HELPER_SHA,71013)
        proof=cleanup.proof_evidence(root,folder,"receipt.json",receipt,expected)
        result.update(status="verified_all_instances",proof=proof,request_sha256=sha(folder/"request.json"),
            native_receipt_sha256=sha(folder/"receipt.json"),instance_trace_sha256=sha(folder/"instances.ndjson"),helper_sha256=PROOF_HELPER_SHA)
    except Exception as error:
        result.update(status="incomplete_or_failed");result["issues"].append(dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
        try:result["raw_receipt"]=read(folder/"receipt.json") if (folder/"receipt.json").is_file() else None
        except Exception as problem:result["raw_receipt_parse_error"]=dict(type=type(problem).__name__,message=str(problem))
    return result


def supervision_evidence(root, repo, resources):
    phases={name:supervision_phase(root,repo,resources,name) for name in ("P1_local","P2_force")}
    reached=[p for p in phases.values() if p["status"] != "not_reached"]
    okay=bool(reached) and all(p["status"] == "verified_all_instances" for p in reached)
    return dict(schema="hf-force-cpu-supervision-proof-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,
        **roles(root,repo),status="verified_all_instances" if okay else ("not_reached" if not reached else "incomplete_or_failed"),
        complete_two_phases=all(p["status"] == "verified_all_instances" for p in phases.values()),phases=phases,
        scientific_admission=False,issues=[dict(phase=n,issues=p["issues"]) for n,p in phases.items() if p["issues"]])


def partial_preservation(root, repo, error):
    """Preserve actual bytes after incomplete preparation, without claiming identity."""
    result = dict(status="evidence_failure",scientific_admission=False,
        original_error=dict(type=type(error).__name__,message=str(error)),observations=[],issues=[],uncommitted_input_files=[])
    rows = []
    try:
        rows = read(root/"input_manifest.json")["files"]
    except Exception as problem:
        result["issues"].append(dict(stage="read_manifest",type=type(problem).__name__,message=str(problem)))
    known = set()
    for row in rows:
        name = row.get("path");known.add(name)
        observation = dict(path=name,expected_sha256=row.get("sha256"),expected_bytes=row.get("bytes"))
        for kind,value in (("copy",bound(root,name)),("live",path(row["source"]))):
            try:
                observation[kind] = dict(bytes=value.stat().st_size,sha256=sha(value))
            except Exception as problem:observation[kind] = dict(error=str(problem))
        result["observations"].append(observation)
    for prefix in ("C1","R1","H1","HR1","data","aux","provenance"):
        folder = root/prefix
        if not folder.exists():continue
        for p in sorted(folder.rglob("*")):
            if p.is_file() and p.relative_to(root).as_posix() not in known:
                result["uncommitted_input_files"].append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p),
                                                            status="uncommitted_actual_bytes_not_verified_source"))
    return result


def cpu_analysis(root, resources, supervision, source_status):
    """Analyze already saved counters only; no process query, interpolation or experiment."""
    raw_rows, problems = read_ndjson(root/CPU_PATH)
    event_rows,event_problems = read_ndjson(root/FORCE_EVENTS)
    problems.extend(dict(kind="force_event",**p) for p in event_problems)
    force_receipts = [r for r in resources.get("phases",[]) if r.get("name") == "P2_force"]
    receipt = force_receipts[0] if len(force_receipts) == 1 else {}
    if len(force_receipts) != 1:
        problems.append(dict(reason="unique_force_receipt_missing"))
    telemetry_error = receipt.get("telemetry_first_error")
    if receipt.get("telemetry_status") != "complete":
        problems.append(dict(reason="telemetry_not_complete",status=receipt.get("telemetry_status"),error=telemetry_error))
    expected_identity = {}
    try:
        expected_identity = dict(supervision_identity(root),supervisor_sha256=CANDIDATE_SHA)
        require(supervision["phases"]["P2_force"]["status"] == "verified_all_instances","P2 instance proof is not verified")
        require(source_status == "pass","current sources are not verified")
    except Exception as error:
        problems.append(dict(reason="source_identity_unavailable",error=str(error)))
    samples = []
    for index,item in enumerate(raw_rows,1):
        row = item["record"]
        errors = []
        if row.get("schema") != "hf-job-cpu-telemetry-1" or row.get("sequence") != index or item["line"] != index:
            errors.append("schema_or_sequence")
        identity = row.get("identity",{})
        if not isinstance(identity,dict) or not expected_identity or identity != expected_identity:
            errors.append("identity")
        a,b = row.get("query_start_monotonic"),row.get("query_end_monotonic")
        if not finite_number(a) or not finite_number(b) or a > b:
            errors.append("query_bracket")
        for key in ("total_user_time_100ns","total_kernel_time_100ns","ActiveProcesses","TotalProcesses"):
            if not isinstance(row.get(key),int) or isinstance(row.get(key),bool) or row[key] < 0:
                errors.append("invalid_"+key)
        if (isinstance(row.get("ActiveProcesses"),int) and isinstance(row.get("TotalProcesses"),int)
                and row["ActiveProcesses"] > row["TotalProcesses"]):
            errors.append("active_exceeds_total_processes")
        if not isinstance(row.get("pid"),int) or isinstance(row.get("pid"),bool) or row["pid"] <= 0:
            errors.append("observer_pid")
        if not isinstance(row.get("utc"),str) or not row["utc"]:
            errors.append("utc")
        if row.get("lifecycle") not in ("initial_before_resume","periodic","pre_cleanup","final_after_cleanup"):
            errors.append("lifecycle")
        sample = dict(line=item["line"],record=row,quality_errors=errors)
        samples.append(sample)
        if errors:
            problems.append(dict(reason="invalid_sample",line=item["line"],details=errors))
    lifecycles = [s["record"].get("lifecycle") for s in samples]
    if receipt.get("telemetry_status") == "complete":
        if (len(lifecycles) < 3 or lifecycles[0] != "initial_before_resume"
                or lifecycles[-2:] != ["pre_cleanup","final_after_cleanup"]
                or any(value != "periodic" for value in lifecycles[1:-2])):
            problems.append(dict(reason="completed_telemetry_lifecycle_incomplete"))
    starts,ends = [],[]
    for index,item in enumerate(event_rows,1):
        row = item["record"]
        if (row.get("schema") != "hf-s0-event-1" or row.get("sequence") != index or item["line"] != index
                or row.get("phase") != "P2_force" or row.get("version") != "R1"
                or row.get("source_manifest_sha256") != expected_identity.get("source_manifest_sha256")):
            problems.append(dict(reason="force_event_identity",line=item["line"]))
        if row.get("stage") == "force.synchronize":
            if row.get("event") == "stage_started":
                starts.append(row.get("monotonic"))
            elif row.get("event") == "stage_finished":
                # Actual callback return, not the later log/checkpoint emission.
                ends.append(row.get("completed_monotonic"))
    start = starts[0] if len(starts) == 1 and finite_number(starts[0]) else None
    cleanup = receipt.get("cleanup_requested_monotonic")
    end = None
    if len(ends) == 1 and finite_number(ends[0]):
        end = ends[0]
        if finite_number(cleanup):
            end = min(end,cleanup)
    elif not ends and finite_number(cleanup):
        end = cleanup
    if start is None or end is None or end <= start or len(ends) > 1:
        problems.append(dict(reason="synchronization_boundary_incomplete",start=start,end=end,cleanup=cleanup))
    segments = []
    for left,right in zip(samples,samples[1:]):
        a,b = left["record"],right["record"]
        seg = dict(first_line=left["line"],last_line=right["line"],quality_errors=[],inside_sync=False)
        if left["quality_errors"] or right["quality_errors"]:
            seg["quality_errors"].append("invalid_endpoint")
        else:
            dt_min = b["query_start_monotonic"]-a["query_end_monotonic"]
            dt_max = b["query_end_monotonic"]-a["query_start_monotonic"]
            dt = b["query_end_monotonic"]-a["query_end_monotonic"]
            du = b["total_user_time_100ns"]-a["total_user_time_100ns"]
            dk = b["total_kernel_time_100ns"]-a["total_kernel_time_100ns"]
            if dt_min <= 0 or dt <= 0:
                seg["quality_errors"].append("overlapping_or_reversed_query_brackets")
            if du < 0 or dk < 0:
                seg["quality_errors"].append("negative_cpu_delta")
            if b["TotalProcesses"] < a["TotalProcesses"] or b["pid"] != a["pid"]:
                seg["quality_errors"].append("job_or_observer_identity_changed")
            if dt_max > 2.5:
                seg["quality_errors"].append("long_gap")
            inside = start is not None and end is not None and a["query_start_monotonic"] >= start and b["query_end_monotonic"] < end
            seg.update(query_end_monotonic=b["query_end_monotonic"],wall_seconds=dt,dt_min=dt_min,dt_max=dt_max,
                user_delta_100ns=du,kernel_delta_100ns=dk,inside_sync=inside)
            if dt > 0 and du >= 0 and dk >= 0:
                seg["cpu_seconds_per_wall_second"] = (du+dk)*1e-7/dt
                if dt_min > 0:
                    seg["ratio_interval"] = [(du+dk)*1e-7/dt_max,(du+dk)*1e-7/dt_min]
        segments.append(seg)
        # Counter/order errors anywhere invalidate evidence. Gaps outside sync remain visible only.
        serious = [e for e in seg["quality_errors"] if e != "long_gap"]
        if serious or (seg["inside_sync"] and seg["quality_errors"]):
            problems.append(dict(reason="segment_quality",first_line=seg["first_line"],details=seg["quality_errors"]))
    inside = [s for s in samples if not s["quality_errors"] and start is not None and end is not None
              and s["record"]["query_start_monotonic"] >= start and s["record"]["query_end_monotonic"] < end]
    aggregate = None
    category = "inconclusive"
    if len(inside) >= 2:
        a,b = inside[0]["record"],inside[-1]["record"]
        dt_min = b["query_start_monotonic"]-a["query_end_monotonic"]
        dt_max = b["query_end_monotonic"]-a["query_start_monotonic"]
        dt = b["query_end_monotonic"]-a["query_end_monotonic"]
        du = (b["total_user_time_100ns"]-a["total_user_time_100ns"])*1e-7
        dk = (b["total_kernel_time_100ns"]-a["total_kernel_time_100ns"])*1e-7
        all_between = samples[inside[0]["line"]-1:inside[-1]["line"]]
        if len(all_between) != len(inside):
            problems.append(dict(reason="invalid_or_noncontained_record_inside_selected_extent"))
        aggregate = dict(first_line=inside[0]["line"],last_line=inside[-1]["line"],sample_count=len(inside),
            wall_seconds=dt,dt_min=dt_min,dt_max=dt_max,user_cpu_seconds=du,kernel_cpu_seconds=dk,
            max_query_seconds=max(s["record"]["query_end_monotonic"]-s["record"]["query_start_monotonic"] for s in inside))
        if dt_min < 30:
            problems.append(dict(reason="coverage_under_30_seconds",dt_min=dt_min))
        if dt_min > 0 and dt > 0 and du >= 0 and dk >= 0:
            low,high = (du+dk)/dt_max,(du+dk)/dt_min
            aggregate.update(cpu_seconds_per_wall_second=(du+dk)/dt,ratio_interval=[low,high])
            if not problems:
                if low >= .5:
                    category = "clear_cpu_consumption"
                elif high <= .05:
                    category = "low_cpu"
                elif low > .05 and high < .5:
                    category = "intermediate"
                else:
                    problems.append(dict(reason="ratio_interval_crosses_diagnostic_threshold"))
    else:
        problems.append(dict(reason="fewer_than_two_contained_samples"))
    # Continuous runs are descriptive only; none is selected to rescue the overall category.
    runs,current = [],[]
    for seg in segments:
        if seg["inside_sync"] and not seg["quality_errors"]:
            current.append(dict(first_line=seg["first_line"],last_line=seg["last_line"]))
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    allowed_quality = {"coverage_under_30_seconds","fewer_than_two_contained_samples","ratio_interval_crosses_diagnostic_threshold"}
    integrity_issues = [p for p in problems if not (p.get("reason") in allowed_quality
        or (p.get("reason") == "segment_quality" and p.get("details") == ["long_gap"]))]
    return dict(schema="hf-force-cpu-observation-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,classification=category,
        integrity_valid=not integrity_issues,integrity_issues=integrity_issues,supervision_proof_status=supervision["status"],
        status="valid_observation" if category != "inconclusive" else "inconclusive",scientific_admission=False,
        parent_status=resources.get("status"),force_receipt=receipt,
        actual_telemetry_failure=receipt.get("telemetry_status") == "failed" or telemetry_error is not None,
        raw_sha256=sha(root/CPU_PATH) if (root/CPU_PATH).is_file() else None,
        force_event_sha256=sha(root/FORCE_EVENTS) if (root/FORCE_EVENTS).is_file() else None,
        sync_start_monotonic=start,sync_upper_boundary_monotonic=end,cleanup_requested_monotonic=cleanup,
        sample_records=samples,all_segments=segments,continuous_sync_segments=runs,aggregate=aggregate,issues=problems,
        thresholds=dict(min_dt_min_seconds=30,max_adjacent_dt_max_seconds=2.5,high_ratio=.5,low_ratio=.05),
        units="raw CPU counters: 100ns ticks; CPU seconds/wall second is equivalent average logical cores, not machine percent",
        scope="Job CPU includes native backend/Python/descendants, excludes parent observer; RSS includes parent and Job",
        uncertainty="query bracket interval only; not an error bound for counter granularity/update lag",
        limitation="CPU use can include spin/postprocessing; low CPU can include scheduling starvation/wait; neither proves physics progress, deadlock or root cause")


def cpu_svg(observation, root):
    """Render saved values only; gaps and incomplete observations remain visible."""
    good = [s["record"] for s in observation["sample_records"] if not s["quality_errors"]]
    times = [s["query_end_monotonic"] for s in good]
    origin = min(times) if times else 0.
    span = max(max(times)-origin,1.) if times else 1.
    ymax = max([1.]+[(s["total_user_time_100ns"]+s["total_kernel_time_100ns"])*1e-7 for s in good])
    ratios = [s.get("cpu_seconds_per_wall_second",0.) for s in observation["all_segments"]]
    rmax = max([1.]+[r for r in ratios if finite_number(r) and r >= 0])
    x = lambda t: 105.+980.*(t-origin)/span
    cy = lambda value: 320.-210.*value/ymax
    ry = lambda value: 625.-210.*value/rmax
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="770">',
        '<rect width="100%" height="100%" fill="white"/><g font-family="Arial,sans-serif" font-size="12">',
        f'<text x="20" y="25">{PROTOCOL} | Job CPU observations; no scientific admission</text>',
        f'<text x="20" y="48">Classification: {escape(observation["classification"])} | parent: {escape(str(observation["parent_status"]))}</text>',
        '<text x="20" y="69">CPU includes Job backend/Python/descendants, excludes parent observer. RSS includes parent + Job.</text>',
        '<text x="20" y="92">Cumulative CPU seconds: blue user, green kernel, black total</text>',
        '<text x="20" y="391">Adjacent CPU seconds / wall second (average cores, can exceed 1); orange = gap/quality warning</text>',
        '<path d="M105 110 V320 H1085 M105 415 V625 H1085" fill="none" stroke="#555"/>',
        f'<text x="40" y="118">{ymax:.2f}</text><text x="40" y="425">{rmax:.2f}</text>',
        '<text x="60" y="322">0</text><text x="60" y="627">0</text>']
    byline = {s["line"]:s["record"] for s in observation["sample_records"] if not s["quality_errors"]}
    for seg in observation["all_segments"]:
        a,b = byline.get(seg["first_line"]),byline.get(seg["last_line"])
        if a is None or b is None:
            continue
        color = "#ca842e" if seg["quality_errors"] else "#356c9b"
        if not seg["quality_errors"]:
            for key,stroke in (("total_user_time_100ns","#356c9b"),("total_kernel_time_100ns","#497f65"),(None,"#222")):
                va = a[key]*1e-7 if key else (a["total_user_time_100ns"]+a["total_kernel_time_100ns"])*1e-7
                vb = b[key]*1e-7 if key else (b["total_user_time_100ns"]+b["total_kernel_time_100ns"])*1e-7
                parts.append(f'<line x1="{x(a["query_end_monotonic"]):.2f}" y1="{cy(va):.2f}" x2="{x(b["query_end_monotonic"]):.2f}" y2="{cy(vb):.2f}" stroke="{stroke}"/>')
        ratio = seg.get("cpu_seconds_per_wall_second")
        if finite_number(ratio) and ratio >= 0:
            xx = (x(a["query_end_monotonic"])+x(b["query_end_monotonic"]))/2
            parts.append(f'<circle cx="{xx:.2f}" cy="{ry(ratio):.2f}" r="2.5" fill="{color}"><title>lines {seg["first_line"]}-{seg["last_line"]}: ratio {ratio:.8g}; {escape(str(seg["quality_errors"]))}</title></circle>')
    for value,color in ((.05,"#777"),(.5,"#777")):
        parts.append(f'<path d="M105 {ry(value):.2f} H1085" stroke="{color}" stroke-dasharray="3 5"/><text x="1090" y="{ry(value)+4:.2f}">{value}</text>')
    event_rows,_ = read_ndjson(root/FORCE_EVENTS)
    boundary_index = 0
    for item in event_rows:
        row = item["record"]
        t = row.get("monotonic")
        if row.get("event") == "stage_started" and finite_number(t) and origin <= t <= origin+span:
            xx = x(t)
            label = escape(str(row.get("stage")))
            parts.append(f'<path d="M{xx:.2f} 110 V320 M{xx:.2f} 415 V625" stroke="#bbb" stroke-dasharray="2 3"><title>{label}</title></path>')
            parts.append(f'<text x="{xx:.2f}" y="{342+14*(boundary_index%3)}" font-size="9" transform="rotate(-10 {xx:.2f} {342+14*(boundary_index%3)})">{label}</text>')
            boundary_index += 1
    aggregate = observation.get("aggregate") or {}
    description = "No aggregate supported" if not aggregate else (
        f'coverage dt_min={aggregate["dt_min"]:.6f}s; CPU user={aggregate["user_cpu_seconds"]:.6f}s, '
        f'kernel={aggregate["kernel_cpu_seconds"]:.6f}s; ratio interval={aggregate.get("ratio_interval")}')
    parts.extend((f'<text x="105" y="652">0</text><text x="1000" y="652">{span:.3f} s</text>',
        '<text x="390" y="674">Time since first saved query endpoint; no interpolation across gaps</text>',
        f'<text x="20" y="699">{escape(description)}</text>',
        f'<text x="20" y="721">Quality issues: {len(observation["issues"])}. All readable samples and segments are in cpu_observation.json.</text>',
        '<text x="20" y="744">Query-bracket range excludes counter-resolution/update-lag uncertainty; CPU use does not prove progress or deadlock.</text>'))
    return "".join(parts)+"</g></svg>\n"


def stage_timings(root, resources, summary, summary_error):
    cutoff = None
    try:
        cutoff = read(root/"plan.json")["start_monotonic"]+resources["total_elapsed_seconds"]
    except (OSError,ValueError,KeyError,TypeError):
        pass
    events,issues = read_ndjson(root/FORCE_EVENTS)
    starts = {item["record"]["stage"]:item["record"]["monotonic"] for item in events
              if item["record"].get("event") == "stage_started" and "stage" in item["record"] and "monotonic" in item["record"]}
    steps = {row["stage"]:row for row in (summary or {}).get("steps",[])}
    rows = []
    for name in list(FORCE_STAGES)+[n for n in steps if n not in FORCE_STAGES]:
        row = steps.get(name,{})
        state = row.get("status","not_reached")
        if state in ("pass","failed") and "elapsed_seconds" in row:
            seconds,basis = row["elapsed_seconds"],"complete saved record"
        elif name in starts and finite_number(starts[name]) and finite_number(cutoff):
            state,seconds,basis = "open_at_stop",max(0.,cutoff-starts[name]),"upper observation includes cleanup/dispatch; NOT completed duration"
        else:
            seconds,basis = None,"no completed saved duration"
        rows.append(dict(stage=name,status=state,seconds=seconds,timing_basis=basis))
    return dict(schema="hf-force-cpu-stage-timings-1",rows=rows,observation_cutoff_monotonic=cutoff,
        source_sha256={n:sha(root/n) for n in (FORCE_EVENTS,"results/force/summary.json") if (root/n).is_file()},
        call_to_synchronize=(summary or {}).get("call_to_synchronize"),summary_error=summary_error,event_issues=issues,
        scope="P2 saved observations; call/readiness are not pure kernel timings")


def record_binding(root, record, expected_name):
    require(record["path"] == expected_name and record["bytes"] > 0,"report path/size differs")
    p=bound(root,expected_name);checked(p,record["sha256"],record["bytes"])
    return read(p)


def verify_harness_report_binding(root, summary, *, phase):
    """Bind an unchanged HR1 native declaration to this fresh execution identity."""
    require(phase in ("P1_local","P2_force"),"unexpected native report phase")
    local=phase == "P1_local"
    native_name="results/local/contract.json" if local else "results/force/three_force_gates.json"
    binding_name="results/local/contract_binding.json" if local else "results/force/three_force_gates_binding.json"
    native_key="contract_record" if local else "force_reference_gates"
    binding_key="contract_binding_record" if local else "force_reference_gates_binding"
    schema="hf-force-reuse-contract-1" if local else "hf-force-reuse-reference-gates-1"
    native_record=summary[native_key];native=record_binding(root,native_record,native_name)
    require(native["protocol"] == NATIVE_PROTOCOL and native["run_id"] == PRIOR_RUN and native["schema"] == schema
            and native_record["status"] == native["status"],"native HR1 declaration differs")
    selected=read(root/"selected_source.json")
    require(path(native["source"]) == root/"R1/source/hf_repo"
            and native["source_manifest_sha256"] == sha(root/"input_manifest.json")
            and native["harness"] == selected["harness"] and native["arithmetic_harness"] == selected["arithmetic_harness"]
            and native["scientific_admission"] is False,"native report/current source identity differs")
    expected=dict(schema="hf-force-reuse-harness-binding-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,
        phase=phase,source_version="R1",source=str(root/"R1/source/hf_repo"),
        source_manifest_sha256=sha(root/"input_manifest.json"),harness=selected["harness"],
        arithmetic_harness=selected["arithmetic_harness"],status=native["status"],scientific_admission=False,
        native=dict(protocol=NATIVE_PROTOCOL,run_id=PRIOR_RUN,schema=schema,path=native_name,
            bytes=native_record["bytes"],sha256=native_record["sha256"],status=native["status"]))
    record=summary[binding_key];binding=record_binding(root,record,binding_name)
    require(binding == expected and record["status"] == native["status"],"native report/current execution binding differs")
    return dict(status="verified",path=binding_name,sha256=record["sha256"],bytes=record["bytes"],native=expected["native"])


def checked_decimal_checks(rows, *, reference=False):
    names=("total_force","material_force","regularization_force")
    require(isinstance(rows,list) and len(rows) == 3 and {r["name"] for r in rows} == set(names),"three force check names differ")
    for row in rows:
        limit=Decimal("1E-40") if reference else Decimal("1E-11" if row["name"] == "total_force" else "1E-9")
        value=Decimal(row["value_decimal"]);denominator=Decimal(row["denominator_decimal"])
        require(value.is_finite() and value >= 0 and denominator.is_finite() and denominator > 0
                and Decimal(row["limit_decimal"]) == limit and value <= limit
                and row["status"] == "pass" and row["pass"] is True,"saved force check did not pass its unchanged limit")


def verify_local_contract(root):
    p=root/"results/local/summary.json";summary=read(p);selected=read(root/"selected_source.json")
    require(summary["schema"] == "hf-force-reuse-local-1" and summary["status"] == "pass"
            and summary["protocol"] == summary["campaign_protocol"] == PROTOCOL and summary["run_id"] == RUN_ID
            and summary["source_version"] == "R1" and summary["mode"] == "local" and not summary["errors"]
            and summary["local_structure_equivalence_pass"] is True and summary["scientific_admission"] is False,
            "local terminal summary does not claim the declared finite contract")
    require(path(summary["source"]) == root/"R1/source/hf_repo" and summary["source_manifest_sha256"] == sha(root/"input_manifest.json")
            and summary["harness"] == selected["harness"] and summary["arithmetic_harness"] == selected["arithmetic_harness"]
            and all(summary[k] == selected[k] for k in ("parent_supervisor","candidate_supervisor","loaded_parent_supervisor")),"local source/harness differs")
    details=record_binding(root,summary["contract_record"],"results/local/contract.json")
    report_binding=verify_harness_report_binding(root,summary,phase="P1_local")
    require(details["schema"] == "hf-force-reuse-contract-1" and details["status"] == "local_structure_equivalence_pass"
            and details["local_structure_equivalence_pass"] is True and details["micro_graph_count"] == 2
            and details["micro_call_count"] == 16 and details["group_count"] == len(details["groups"]) == 8,
            "local matrix or fixed micro-call count differs")
    require(details["protocol"] == NATIVE_PROTOCOL and details["run_id"] == PRIOR_RUN
            and details["source_manifest_sha256"] == summary["source_manifest_sha256"]
            and path(details["source"]) == root/"R1/source/hf_repo"
            and details["harness"] == selected["harness"] and details["arithmetic_harness"] == selected["arithmetic_harness"],"contract identity differs")
    runtime=summary["runtime_identity"];require(details["runtime_identity"] == runtime,"runtime declaration differs")
    manifest=read(root/"input_manifest.json")
    for key,filename,digest in (("C1",root/"C1/source/hf_repo"/KERNEL,KERNEL_SHA),
            ("R1",root/"R1/source/hf_repo"/KERNEL,manifest["science"]["kernel_sha256"]),
            ("arithmetic",root/"R1/source/hf_repo"/ARITHMETIC,ARITHMETIC_SHA),
            ("harness",root/"aux"/LOCAL_TEST,selected["harness"]["test_sha256"])):
        require(path(runtime[key]["path"]) == filename and runtime[key]["sha256"] == digest,"actual loaded source differs: "+key)
        checked(filename,digest)
    require(runtime["same_arithmetic_module"] is True and runtime["baseline_module_name"] != runtime["candidate_module_name"],"baseline was not separately loaded")
    numeric=details["numpy"];selector=details["selector"];micro=details["micro"]
    require(details["static"]["status"] == "pass" and numeric["status"] == "pass" and len(numeric["rows"]) == 7,
            "local NumPy/static coverage differs")
    for row in [*numeric["rows"],numeric["material_rejection"]]:
        require(row["status"] == "pass" and set(row["fields"]) == OUTPUT_FIELD_NAMES
                and all(v["status"] == "pass" for v in row["fields"].values()),"local 26-field comparison failed")
    require(selector["status"] == "pass" and selector["extra_jit_count"] == 0 and len(selector["rows"]) == 4
            and all(r["status"] == "pass" for r in selector["rows"]),"NumPy selector boundaries incomplete")
    groups=("valid_first_three","valid_last_three","original_mixed","mixed_negative_J","mixed_large_input",
            "mixed_nan_input","mixed_large_coefficient","mixed_nan_coefficient")
    require(micro["status"] == "pass" and (micro["micro_graph_count"],micro["micro_call_count"],micro["group_count"]) == (2,16,8)
            and tuple(row["name"] for row in micro["groups"]) == groups and details["groups"] == micro["groups"],"micro-group coverage differs")
    micro_fields={name+suffix for name in ("F","G","Hu","J","B","delta") for suffix in ("","_hi","_lo")}|{"near","pairs_near"}
    require(all(row["status"] == "pass" and set(row["fields"]) == micro_fields
            and all(v["status"] == "pass" for v in row["fields"].values()) for row in micro["groups"]),"micro-field comparisons incomplete")
    expected_micro=["local."+v+"."+o for v in ("C1","R1") for o in ("trace","lower","compile")]
    expected_micro += ["local."+g+"."+v+"."+o for g in groups for v in ("C1","R1") for o in ("call","synchronize")]
    actual_micro=[r["stage"] for r in summary["steps"] if r["stage"].startswith("local.")
                  and r["stage"].rsplit(".",1)[-1] in {"trace","lower","compile","call","synchronize"}]
    require(actual_micro == expected_micro and all(r["status"] == "pass" for r in summary["steps"]),"fixed micro stages incomplete")
    artifacts=summary["local_artifacts"]
    require(len(artifacts) == len({r["path"] for r in artifacts}) == 16,"local array evidence count differs")
    for record in artifacts:
        require(record["status"] == "pass" and record["path"].endswith(".npz"),"local evidence record failed")
        checked(bound(root/"results/local",record["path"]),record["sha256"],record["bytes"])
    reference=details["reference"]
    require(reference["status"] == "pass" and reference["precision"] == 120 and reference["new_hp_evaluations"] == 0
            and Decimal(reference["force_scale_decimal"]) == Decimal("1.2500E-7")
            and reference["hp_sha256"] == REFERENCES["hp_0.json"][1] and reference["result_sha256"] == REFERENCES["result.json"][1]
            and reference["input_sha256"] == INPUT_SHA,"saved reference identity/precision differs")
    checked_decimal_checks(reference["reference_checks"],reference=True)
    expected_stages=["source_binding","local.static_contract","runtime_import_and_prepare","kernel_import",
        "local.baseline_import","local.input_read","local.numpy26","local.selector_numpy","local.reference_agreement"]
    expected_stages += expected_micro+["source_preservation"]
    require(len(expected_stages) == 48 and [r["stage"] for r in summary["steps"]] == expected_stages,
            "complete local stage sequence differs")
    require(summary["source_preservation"]["status"] == "pass"
            and summary["source_preservation"]["input_manifest_sha256"] == sha(root/"input_manifest.json"),"local source preservation differs")
    events,issues=read_ndjson(root/"events/P1_local.ndjson")
    require(not issues and events,"local event stream incomplete")
    for index,item in enumerate(events,1):
        row=item["record"]
        require(row["schema"] == "hf-s0-event-1" and row["sequence"] == index and row["phase"] == "P1_local"
                and row["version"] == "R1" and row["source_manifest_sha256"] == sha(root/"input_manifest.json"),"local event identity differs")
    records=[x["record"] for x in events]
    require(records[0]["event"] == "probe_started" and records[-1]["event"] == "probe_finished"
            and records[0]["protocol"] == records[0]["campaign_protocol"] == PROTOCOL and records[0]["run_id"] == RUN_ID
            and records[0]["mode"] == "local" and records[-1]["outcome"] == "pass" and records[-1]["mode"] == "local"
            and sum(r["event"] == "probe_started" for r in records) == 1
            and sum(r["event"] == "probe_finished" for r in records) == 1
            and not any(e["event"] in ("stage_failed","probe_failed") for e in records),"local terminal events differ")
    starts=[(i,r) for i,r in enumerate(records) if r["event"] == "stage_started"]
    ends=[(i,r) for i,r in enumerate(records) if r["event"] == "stage_finished"]
    require([r["stage"] for _,r in starts] == [r["stage"] for _,r in ends] == expected_stages,
            "local events do not contain every stage exactly once")
    for index,((start,a),(end,b),record) in enumerate(zip(starts,ends,summary["steps"])):
        require(start < end and (index == len(starts)-1 or end < starts[index+1][0])
                and a["outcome"] == "running" and b["outcome"] == "pass" and record["status"] == "pass",
                "local stage order or outcome differs")
        require(all(finite_number(record[k]) for k in ("started_monotonic","execution_start_monotonic","completed_monotonic","elapsed_seconds"))
                and record["started_monotonic"] <= record["execution_start_monotonic"] <= record["completed_monotonic"]
                and record["elapsed_seconds"] == record["completed_monotonic"]-record["execution_start_monotonic"]
                and a["stage_start_monotonic"] == record["started_monotonic"]
                and b["completed_monotonic"] == record["completed_monotonic"] and b["duration"] == record["elapsed_seconds"],
                "local event/summary timings differ")
    return dict(status="local_structure_equivalence_pass",summary_sha256=sha(p),contract_sha256=summary["contract_record"]["sha256"],
        harness_binding=report_binding,event_sha256=sha(root/"events/P1_local.ndjson"),scientific_admission=False,details=details)



def verify_force_reference_report(root, summary):
    record=summary["force_reference_gates"]
    report=record_binding(root,record,"results/force/three_force_gates.json")
    report_binding=verify_harness_report_binding(root,summary,phase="P2_force")
    selected=read(root/"selected_source.json")
    require(record["status"] == report["status"] == "fixed_force_three_reference_gates_pass"
            and report["schema"] == "hf-force-reuse-reference-gates-1" and report["scientific_admission"] is False,
            "three force gates did not pass")
    require(report["edofs"] == [0,1,2,3,6,7,4,5] and Decimal(report["force_scale_decimal"]) == Decimal("1.2500E-7")
            and report["source_manifest_sha256"] == sha(root/"input_manifest.json")
            and report["harness"] == selected["harness"] and report["arithmetic_harness"] == selected["arithmetic_harness"]
            and path(report["source"]) == root/"R1/source/hf_repo" and report["protocol"] == NATIVE_PROTOCOL and report["run_id"] == PRIOR_RUN
            and report["precision"] == 120 and report["new_hp_evaluations"] == 0 and report["includes_fixed_dofs"] is True
            and report["hp_sha256"] == REFERENCES["hp_0.json"][1] and report["result_sha256"] == REFERENCES["result.json"][1]
            and report["input_sha256"] == INPUT_SHA and report["count"] == 3,"force-reference input/scale/harness differs")
    checked_decimal_checks(report["checks"]);checked_decimal_checks(report["reference_checks"],reference=True)
    return dict(status="fixed_force_three_reference_gates_pass",path="results/force/three_force_gates.json",sha256=record["sha256"],
        checks=report["checks"],reference_checks=report["reference_checks"],harness_binding=report_binding,scientific_admission=False)


def saved_local_observation(root):
    result=dict(status="not_reached",scientific_admission=False,files={},errors=[])
    for name in ("summary.json","contract.json","contract_binding.json"):
        p=root/"results/local"/name
        if p.is_file():
            result["files"][name]=dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
            try:result[name]=read(p)
            except Exception as error:result["errors"].append(dict(path=str(p),type=type(error).__name__,message=str(error)))
    if result["files"]:
        try:result.update(verify_local_contract(root))
        except Exception as error:
            result["status"]="incomplete_or_failed";result["errors"].append(dict(type=type(error).__name__,message=str(error)))
    return result


def saved_force_gate_observation(root, summary):
    p=root/"results/force/three_force_gates.json"
    result=dict(status="not_reached",scientific_admission=False)
    if not p.is_file():return result
    result["artifact"]=dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
    try:
        result["raw_report"]=read(p)
        result["harness_binding"]=verify_harness_report_binding(root,summary,phase="P2_force")
        if result["raw_report"].get("status") == "fixed_force_three_reference_gates_pass":
            result.update(verify_force_reference_report(root,summary))
        else:result["status"]="saved_not_pass"
    except Exception as error:result.update(status="incomplete_or_failed",error=dict(type=type(error).__name__,message=str(error)))
    return result


def comparison_table(local, force):
    rows=["# F-REUSE2 saved comparisons", "", "No numerical recomputation is performed during sealing.", "",
          "| Scope | Saved status |", "|---|---|", "| Local structure | "+local["status"]+" |", "| Three force gates | "+force["status"]+" |"]
    details=local.get("details",{})
    for row in details.get("numpy",{}).get("rows",[]):rows.append("| NumPy: "+", ".join(row["cases"])+" | "+row["status"]+" |")
    for row in details.get("groups",[]):rows.append("| Micro: "+row["name"]+" | "+row["status"]+" |")
    raw=force.get("raw_report",{})
    rows.extend(("", "| Force | Saved error ratio | Original limit |", "|---|---|---|"))
    for row in raw.get("checks",[]):rows.append("| "+row["name"]+" | "+row["value_decimal"]+" | "+row["limit_decimal"]+" |")
    rows.extend(("", "These are finite local gates; full AD, full scientific admission and speedup remain unclaimed.", ""))
    return "\n".join(rows).encode("utf-8")


def hlo_structure(root, summary):
    """Saved text only. Counts definitions once, with no graph execution or recursive expansion."""
    artifact=(summary or {}).get("artifacts",{}).get("force_optimized_hlo.txt")
    result=dict(schema="hf-force-reuse-hlo-structure-1",status="not_reached",scientific_admission=False,
        baseline=dict(computations=204,instructions=191329,fusion=167,conditional=1,while_count=0,call=0),
        limitation="Static HLO is not machine code, runtime progress, speedup or full scientific admission.")
    if not artifact:return result
    try:
        require(artifact["status"] == "complete" and artifact["path"] == "force_optimized_hlo.txt","optimized HLO is partial")
        filename=root/"results/force/force_optimized_hlo.txt";checked(filename,artifact["sha256"],artifact["bytes"])
        counts=Counter();computations=[];current=None;entry=[];unparsed=[]
        with filename.open(encoding="utf-8") as stream:
            for lineno,line in enumerate(stream,1):
                line=line.rstrip("\r\n")
                if re.match(r"^(ENTRY )?%\S+ \(.*\) -> .* \{$",line):
                    current=dict(name=line.split(" (")[0],start_line=lineno,instructions=0);computations.append(current)
                match=re.match(r"^  (ROOT )?(%[\w.-]+) = (.*)$",line)
                if match:
                    op=re.search(r"\s([a-z][a-z0-9_-]*)\(",match[3])
                    if op is None:unparsed.append(lineno);continue
                    counts[op[1]]+=1
                    if current is None:unparsed.append(lineno)
                    else:
                        current["instructions"]+=1
                        if current["name"].startswith("ENTRY "):
                            # Keep only the small entry's exact textual operation and operand references.
                            expression=match[3].split(", metadata=",1)[0]
                            entry.append(dict(line=lineno,name=match[2],opcode=op[1],expression=expression))
                if line == "}" and current is not None:current["end_line"]=lineno;current=None
        require(not unparsed,"unparsed HLO instructions")
        table={row["name"]:row for row in entry};cond=[r for r in entry if r["opcode"] == "conditional"]
        dependency=dict(status="unable_to_confirm",conditionals=len(cond))
        if len(cond) == 1:
            expression=cond[0]["expression"];m=re.search(r"conditional\((.*?)\), branch_computations=\{(.*?)\}",expression)
            if m:
                operands=re.findall(r"%[\w.-]+",m[1]);branches=re.findall(r"%[\w.-]+",m[2])
                dependency.update(conditional_line=cond[0]["line"],branch_computations=branches,conditional_operands=operands)
                if len(operands) == 3 and operands[2] in table and table[operands[2]]["opcode"] == "tuple":
                    pack=table[operands[2]];mm=re.search(r" tuple\((.*)\)",pack["expression"])
                    if mm:
                        names=re.findall(r"%[\w.-]+",mm[1]);kinds=[table.get(n,{}).get("opcode","unknown") for n in names]
                        dependency.update(status="computed_values_passed_to_valid_branch" if any(k not in ("parameter","constant") for k in kinds) else "raw_inputs_only_or_unconfirmed",
                            valid_pack_line=pack["line"],valid_pack_operands=names,valid_pack_producer_opcodes=kinds,
                            note="Producer kinds prove tuple data dependence, not elimination of every repeated calculation.")
        total=sum(counts.values())
        result.update(status="counted",sha256=artifact["sha256"],bytes=artifact["bytes"],computations=len(computations),
            instructions=total,opcodes=dict(counts),instruction_change=total-191329,
            structural_size="reduced" if total < 191329 else "not_reduced",entry=entry,entry_dependency=dependency,
            largest_computations=sorted(computations,key=lambda c:c["instructions"],reverse=True)[:8])
    except Exception as error:result.update(status="unable_to_confirm",error=dict(type=type(error).__name__,message=str(error)))
    return result


def seal(root, repo, events):
    try:
        preservation = verify_snapshot(root,repo)
    except Exception as error:
        preservation = partial_preservation(root,repo,error)
    write(root/"source_preservation.json",preservation)
    try:
        resources = read(root/"resources.json")
    except Exception as error:
        resources = dict(phases=[],resource_record_error=str(error))
    summary,summary_error = read_probe(root)
    artifacts = artifact_observations(root,summary)
    artifacts["schema"] = "hf-force-cpu-artifacts-1"
    write(root/"artifact_status.json",artifacts)
    timings = stage_timings(root,resources,summary,summary_error)
    write(root/"stage_timings.json",timings)
    try:
        supervision = supervision_evidence(root,repo,resources)
    except Exception as error:
        supervision = dict(schema="hf-force-cpu-supervision-proof-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,
            **roles(root,repo),status="incomplete_or_failed",scientific_admission=False,
            issues=[dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())])
    write(root/"supervision_proof.json",supervision)
    local=saved_local_observation(root);write(root/"local_verification.json",local)
    force_gates=saved_force_gate_observation(root,summary);write(root/"force_reference_verification.json",force_gates)
    binary_write(root/"local_comparison.md",comparison_table(local,force_gates))
    graph=hlo_structure(root,summary);write(root/"hlo_structure.json",graph)
    try:
        analysis = cpu_analysis(root,resources,supervision,preservation["status"])
    except Exception as error:
        analysis = dict(schema="hf-force-cpu-observation-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,classification="inconclusive",
            status="analysis_failure",scientific_admission=False,parent_status=resources.get("status"),integrity_valid=False,
            sample_records=[],all_segments=[],continuous_sync_segments=[],aggregate=None,
            actual_telemetry_failure=None,issues=[dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())],
            raw_sha256=sha(root/CPU_PATH) if (root/CPU_PATH).is_file() else None,
            limitation="raw files are preserved; analysis failure provides no accepted observation")
    write(root/"cpu_observation.json",analysis)
    binary_write(root/"cpu.svg",cpu_svg(analysis,root).encode())
    binary_write(root/"resources.svg",old_resource_svg(resources).replace("F-OBS-1",PROTOCOL).replace("BEFORE F2","BEFORE P3").replace("includes F2","includes P3").encode())
    binary_write(root/"stages.svg",old_stages_svg(timings).replace("F-OBS-1 saved F1",PROTOCOL+" saved P2").encode())
    phase = os.environ["HF_S0_PHASE"]
    excluded = {"output_sha256.json","receipt_binding.json","execution_receipt.json","ledger.json",
                "logs/"+phase+".log","events/"+phase+".ndjson"}
    completion = dict(status="not_claimed_parent_stopped",parent_status=resources.get("status"),scientific_admission=False)
    complete = (preservation["status"] == "pass" and not artifacts["problems"]
                and "resource_record_error" not in resources and analysis["status"] != "analysis_failure")
    if resources.get("status") in ("fixed_force_three_reference_gates_pass_no_scientific_admission",):
        try:
            completion = verify_complete_force(root,summary)
            require(supervision["complete_two_phases"] and supervision["status"] == "verified_all_instances","force completion lacks both raw SUP2 cleanup proofs")
            require(local["status"] == "local_structure_equivalence_pass","force completion lacks local acceptance")
            completion["force_reference_gates"] = verify_force_reference_report(root,summary)
            require(analysis.get("force_receipt",{}).get("telemetry_status") == "complete"
                    and not analysis["actual_telemetry_failure"] and analysis["integrity_valid"],
                    "force claim conflicts with telemetry acquisition/source/identity failure")
        except Exception as error:
            complete = False
            completion = dict(status="completion_not_supported",scientific_admission=False,error=dict(type=type(error).__name__,message=str(error)))
    result = dict(schema="hf-force-cpu-evidence-worker-1",protocol=PROTOCOL,campaign_protocol=PROTOCOL,run_id=RUN_ID,
        action="seal",status="pass" if complete else "evidence_failure",
        supervision_proof=dict(path="supervision_proof.json",sha256=sha(root/"supervision_proof.json"),status=supervision["status"]),
        payload_sealed=True,scientific_admission=False,source_preservation=preservation,force_observation=completion,
        local_verification=dict(path="local_verification.json",sha256=sha(root/"local_verification.json"),status=local["status"]),
        hlo_structure=dict(path="hlo_structure.json",sha256=sha(root/"hlo_structure.json"),status=graph["status"]),
        force_reference_verification=dict(path="force_reference_verification.json",sha256=sha(root/"force_reference_verification.json"),status=force_gates["status"]),
        cpu_observation=dict(path="cpu_observation.json",sha256=sha(root/"cpu_observation.json"),classification=analysis["classification"],
                             actual_telemetry_failure=analysis["actual_telemetry_failure"]),
        artifact_status_path="artifact_status.json",resources_scope="before P3 only; parent final receipt includes P3",
        excluded_live_or_final_bindings=sorted(excluded),limitation="source/partial payload preservation is not force completion or scientific admission")
    write(root/"results/seal/summary.json",result)
    files = {f.relative_to(root).as_posix():sha(f) for f in sorted(root.rglob("*"))
             if f.is_file() and f.relative_to(root).as_posix() not in excluded}
    write(root/"output_sha256.json",files)
    events.emit("seal_complete",status=result["status"],output_manifest_sha256=sha(root/"output_sha256.json"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--action",choices=("prepare","seal"),required=True)
    args = parser.parse_args()
    root,repo = path(args.root),path(args.repo)
    require(root == repo/"hf4_c2_stable_f_validation"/RUN_ID and root.is_dir(),"parent must create the exact authorized root")
    output = root/"results"/args.action
    events,begin = EventLog(),time.perf_counter()
    try:
        require(not output.exists(),"worker action cannot be repeated")
        events.emit("worker_started",action=args.action)
        if args.action == "seal":
            result = seal(root,repo,events)
            return 0 if result["status"] == "pass" else 2
        result = prepare(root,repo,events)
        write(output/"summary.json",dict(schema="hf-force-cpu-evidence-worker-1",action=args.action,
            elapsed_seconds=time.perf_counter()-begin,**result))
        events.emit("worker_finished",action=args.action,status=result["status"])
        return 0
    except Exception as error:
        failure = dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        if not (output/"summary.json").exists():
            write(output/"summary.json",dict(schema="hf-force-cpu-evidence-worker-1",action=args.action,
                status="evidence_failure",elapsed_seconds=time.perf_counter()-begin,scientific_admission=False,error=failure))
        events.emit("worker_failed",action=args.action,**failure)
        return 2
    finally:
        events.close()


def verify_complete_force(root, summary):
    """Validate saved observations only, without importing arrays or a kernel."""
    require(isinstance(summary,dict) and summary["schema"] == "hf-force-cpu-probe-1"
            and summary["protocol"] == PROTOCOL and summary["campaign_protocol"] == PROTOCOL and summary["run_id"] == RUN_ID and summary["mode"] == "force"
            and summary["source_version"] == "R1" and summary["status"] == "pass"
            and not summary["errors"] and not summary["scientific_admission"],
            "force terminal summary does not support completion")
    selected = read(root/"selected_source.json")
    require(all(summary[k] == selected[k] for k in ("parent_supervisor","candidate_supervisor","loaded_parent_supervisor")),"force supervisor roles differ")
    require(path(summary["source"]) == root/"R1/source/hf_repo"
            and summary["source_manifest_sha256"] == selected["source_manifest_sha256"]
            and summary["harness"] == selected["harness"] and summary["arithmetic_harness"] == selected["arithmetic_harness"], "force terminal identity differs")
    require(summary["expected_stages"] == list(FORCE_STAGES)
            and [s["stage"] for s in summary["steps"]] == list(FORCE_STAGES)
            and all(s["status"] == "pass" and s["elapsed_seconds"] >= 0 for s in summary["steps"]),
            "force fixed stage sequence is incomplete or repeated")
    contract = summary["execution_contract"]
    require(all(contract[n] == 1 for n in ("trace","lower","compile","compiled_call","output_synchronization"))
            and contract["warmup"] == contract["retries"] == 0, "force execution contract differs")
    require(set(summary["artifacts"]) == set(FORCE_ARTIFACTS), "force artifact inventory differs")
    for name in FORCE_ARTIFACTS:
        record = summary["artifacts"][name]
        require(record["status"] == "complete" and record["path"] == name and record["bytes"] > 0,
                "required force artifact is incomplete")
        checked(root/"results/force"/name,record["sha256"],record["bytes"])
    validation = summary["output_validation"]
    require(validation["status"] == "pass" and validation["finite_binary64"]
            and validation["positive_J"] and validation["arithmetic_supported"] and validation["min_J"] > 0
            and set(validation["fields"]) == set(contract["force_output_fields"]) == OUTPUT_FIELD_NAMES
            and len(validation["fields"]) == 26 and all(v["dtype"] == "float64" for v in validation["fields"].values()),
            "force original output gates were not recorded as passed")
    require(summary["source_preservation"]["status"] == "pass"
            and summary["source_preservation"]["input_manifest_sha256"] == sha(root/"input_manifest.json"),
            "force final source preservation is absent or mismatched")
    interval = summary["call_to_synchronize"]
    require(interval["status"] == "complete" and interval["call_returned"]
            and interval["start_monotonic"] <= interval["call_return_monotonic"] <= interval["end_monotonic"]
            and interval["elapsed_seconds"] == interval["end_monotonic"]-interval["start_monotonic"],
            "force continuous call/synchronization interval is incomplete")
    filename = root/"events/P2_force.ndjson"
    raw = filename.read_bytes()
    require(raw.endswith(b"\n"), "complete force event stream is truncated")
    rows = [json.loads(line) for line in raw.splitlines()]
    for index,row in enumerate(rows,1):
        require(row["schema"] == "hf-s0-event-1" and row["sequence"] == index and row["phase"] == "P2_force"
                and row["version"] == "R1" and row["source_manifest_sha256"] == sha(root/"input_manifest.json"),
                "force event identity or sequence differs")
    require(rows and rows[0]["event"] == "probe_started" and rows[-1]["event"] == "probe_finished"
            and rows[-1]["outcome"] == "pass" and rows[-1]["mode"] == "force"
            and sum(r["event"] == "probe_started" for r in rows) == 1
            and sum(r["event"] == "probe_finished" for r in rows) == 1
            and not any(r["event"] in ("stage_failed","probe_failed") for r in rows),
            "force event terminal outcome is incomplete")
    starts = [(i,r) for i,r in enumerate(rows) if r["event"] == "stage_started"]
    ends = [(i,r) for i,r in enumerate(rows) if r["event"] == "stage_finished"]
    require([r["stage"] for _,r in starts] == list(FORCE_STAGES)
            and [r["stage"] for _,r in ends] == list(FORCE_STAGES)
            and all(r["outcome"] == "pass" for _,r in ends), "force event stages differ")
    for index,((start,_),(end,_)) in enumerate(zip(starts,ends)):
        require(start < end and (index == len(starts)-1 or end < starts[index+1][0]),
                "force stage event ordering differs")
    artifact_events = [(i,r) for i,r in enumerate(rows) if r["event"] == "artifact_complete"]
    require([r["artifact"] for _,r in artifact_events] == list(FORCE_ARTIFACTS),
            "complete force artifact events differ")
    for (index,row),stage in zip(artifact_events,("force.export_jaxpr","force.export_stablehlo",
                                                "force.export_optimized_hlo","force.save_output")):
        artifact = summary["artifacts"][row["artifact"]]
        stage_index = FORCE_STAGES.index(stage)
        require(starts[stage_index][0] < index < ends[stage_index][0]
                and row["artifact_status"] == "complete"
                and all(row[k] == artifact[k] for k in ("path","bytes","sha256")),
                "force artifact event and saved bytes differ")
    return dict(status="complete_fixed_force_no_scientific_admission",stages=14,artifacts=4,
                event_sha256=sha(filename),summary_sha256=sha(root/"results/force/summary.json"),
                scientific_admission=False)



if __name__ == "__main__":
    raise SystemExit(main())
