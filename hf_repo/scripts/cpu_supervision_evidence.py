"""Portable, standard-library evidence for the authorized F-CPU-CLEAN1 card.

Only EventLog is imported from the frozen auxiliary bundle. No force worker,
scientific module, subprocess, test or process observation is called here.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from s0_event_log import EventLog

PROTOCOL = "F-CPU-CLEAN1"
RUN_ID = "cpu_cleanup_contract_001"
DIAGNOSTIC_FOCUS = "instance_termination_coverage"
SUBJECT = "windows_job_supervision"
VERSION = "SUP2"
HARNESS = "CPU-CLEAN1"
PARENT_SUPERVISOR_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
OLD_ROOT = "hf4_c2_stable_f_validation/cpu_pid_diagnostic_001"
OLD_BINDING_SHA = "f46ddbfddea48bc46b465776f3f44705978e859f14ecc1fc36b5ea445b5dd021"
PROVENANCE = "provenance/cpu_pid_diagnostic_001/"
PARENT_FILE = "hf_repo/scripts/windows_owned_process.py"
CANDIDATE_FILE = "hf_repo/scripts/windows_owned_process_sup2.py"
SUBPROCESS_FILE = "C:/Python313/Lib/subprocess.py"
SUBPROCESS_BYTES = 91718
SUBPROCESS_SHA = "970207fdd712c92f7dc14d1623d2574f7e0910ceb0b5c37652a7a0850f35a396"
FAILURE_DIR = "results/P1_tests/synthetic-temp/test_busy_sleep_and_exited_des0/"
BINDING_PATHS = {
    "plan_sha256":"plan.json", "input_manifest_sha256":"input_manifest.json",
    "harness_manifest_sha256":"input_manifest.json", "selected_source_sha256":"selected_source.json",
    "receipt_sha256":"execution_receipt.json", "output_manifest_sha256":"output_sha256.json",
    "test_coverage_sha256":"test_coverage.json", "synthetic_lifecycle_sha256":"synthetic_lifecycle.json",
    "pid_diagnostic_sha256":"pid_diagnostic.json",
    "seal_event_sha256":"events/P2_seal.ndjson", "seal_log_sha256":"logs/P2_seal.log",
}
HISTORY_PATHS = ("receipt_binding.json", *dict.fromkeys(BINDING_PATHS.values()),
    "events/P1_tests.ndjson", "logs/P1_tests.log", "results/P1_tests/pytest.xml",
    "results/P1_tests/runtime_identity.json", "source_preservation.json", "inheritance_manifest.json", "results/seal/summary.json",
    "aux/hf_repo/scripts/windows_owned_process.py",
    "aux/hf_repo/tests/test_windows_owned_process.py", "aux/hf_repo/tests/test_windows_owned_cpu.py",
    "aux/hf_repo/scripts/run_cpu_supervision.py", "aux/hf_repo/scripts/cpu_supervision_evidence.py",
    *(FAILURE_DIR+n for n in ("invocation_budget.json","request.json","receipt.json","call_outcome.json",
        "outer_markers.ndjson","descendant_markers.ndjson","descendant_request.json","descendant_receipt.json",
        "descendant_call_outcome.json","cpu.ndjson","descendant_cpu.ndjson","child.log","descendant.log","pid_check.json")))
AUX_FILES = (
    "hf_repo/scripts/run_cpu_supervision.py", "hf_repo/scripts/cpu_supervision_evidence.py",
    "hf_repo/scripts/windows_owned_process.py", "hf_repo/scripts/hf_s0_pytest_events.py",
    CANDIDATE_FILE,
    "hf_repo/scripts/s0_event_log.py", "hf_repo/scripts/s0_ad_exception.py",
    "hf_repo/tests/test_windows_owned_process.py", "hf_repo/tests/test_windows_owned_cpu.py",
    "hf_repo/tests/test_windows_cleanup_contract.py",
    "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md", "docs/CURRENT_STATUS.md",
)
EXPECTED_TESTS = (
    "tests/test_windows_owned_process.py::test_exit[0]", "tests/test_windows_owned_process.py::test_exit[7]",
    "tests/test_windows_owned_process.py::test_timeout", "tests/test_windows_owned_process.py::test_resource_trigger",
    "tests/test_windows_owned_process.py::test_orphan_grandchild",
    "tests/test_windows_owned_cpu.py::test_busy_sleep_and_exited_descendant_keep_cumulative_cpu",
    "tests/test_windows_owned_cpu.py::test_timeout_preserves_partial_samples_and_cleans_job",
    "tests/test_windows_owned_cpu.py::test_observation_failure_stops_and_independent_cleanup_survives[query]",
    "tests/test_windows_owned_cpu.py::test_observation_failure_stops_and_independent_cleanup_survives[write]",
    "tests/test_windows_cleanup_contract.py::test_active_zero_with_history_gap_fails_closed",
    "tests/test_windows_cleanup_contract.py::test_duplicate_identity_does_not_inflate_coverage",
    "tests/test_windows_cleanup_contract.py::test_reused_pid_with_new_creation_time_is_bound",
    "tests/test_windows_cleanup_contract.py::test_wrong_job_cannot_fill_coverage",
    "tests/test_windows_cleanup_contract.py::test_open_failure_is_recorded_without_false_coverage",
    "tests/test_windows_cleanup_contract.py::test_creation_time_failure_releases_opened_handle",
    "tests/test_windows_cleanup_contract.py::test_wait_failure_does_not_prove_termination",
    "tests/test_windows_cleanup_contract.py::test_close_failure_does_not_skip_other_handles",
    "tests/test_windows_cleanup_contract.py::test_timeout_with_exit_code_125_is_not_termination",
    "tests/test_windows_cleanup_contract.py::test_capacity_exhaustion_fails_closed",
    "tests/test_windows_cleanup_contract.py::test_multiple_handles_share_one_cleanup_deadline",
    "tests/test_windows_cleanup_contract.py::test_signaled_handle_is_released_before_accounting",
)
SCIENCE_IDENTITIES = {
    "hf_repo/src/hf_eval/compensated_invariants.py":"6a0144a92bf323951594a0d677b7558cf2a6501667f4b076dd13e2df6bba3897",
    "hf_repo/src/hf_eval/split_kernel_invariants_hu.py":"88d57ed77565963d8cc367c18398b11b30f8f1e0e335c7dcdbc3d68702ecb6bf",
    "hf_repo/tests/test_compensated_invariants.py":"15a81049f3fadcf0a0391f702db8444c33856f1116055d26e6ffca686821e946",
    "hf4_c2_stable_f_validation/force_cpu_001/data/inputs.npz":"2ba110b878186e52996c25f4aad44cb81858be15303c21579c4f5e8ccc013448",
}
PSUTIL_FILES = {
    "__init__.py":(92363,"7b6a0675824eb1fa2ff0cb1eb36e358dc454703e51dfa4e9a0e6ccd26a159f0c"),
    "_pswindows.py":(36466,"0bbd52dcb214735be4168d11a2ae192d5bc7265c8cf72c611179476479687f54"),
    "_psutil_windows.pyd":(70656,"0035450801bd7d938e9e146c5ec28e619cb5a5f4a18cdc53ac7e9734c7f94f78"),
}


def path(value):
    value = os.path.abspath(os.fspath(value))
    if os.name == "nt" and not value.startswith("\\\\?\\"):
        value = "\\\\?\\UNC\\"+value[2:] if value.startswith("\\\\") else "\\\\?\\"+value
    return Path(value)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(filename):
    with path(filename).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def read(filename):
    return json.loads(path(filename).read_text(encoding="utf-8"))


def bound(root, name):
    require(isinstance(name,str) and name and not Path(name).is_absolute()
            and ".." not in Path(name).parts and "\\" not in name,"unsafe relative evidence path")
    target = path(root/name)
    require(target.resolve().is_relative_to(root.resolve()),"path escaped evidence root")
    return target


def checked(filename, digest, size=None):
    filename = path(filename)
    require(filename.is_file(),"missing: "+str(filename))
    require(size is None or filename.stat().st_size == size,"size differs: "+str(filename))
    require(sha(filename) == digest,"SHA256 differs: "+str(filename))


def write(filename, value):
    filename = path(filename)
    filename.parent.mkdir(parents=True,exist_ok=True)
    with filename.open("x",encoding="utf-8",newline="\n") as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def binary_write(filename, value):
    filename = path(filename)
    filename.parent.mkdir(parents=True,exist_ok=True)
    with filename.open("xb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    checked(filename,hashlib.sha256(value).hexdigest(),len(value))


def journal(root, value):
    with (root/"prepare_journal.ndjson").open("a",encoding="utf-8",newline="\n") as stream:
        stream.write(json.dumps(dict(utc=utc(),**value),ensure_ascii=False,allow_nan=False)+"\n")
        stream.flush()
        os.fsync(stream.fileno())


def copy_row(root, source, name, *, role, expected=None):
    source = path(source)
    digest,size = sha(source),source.stat().st_size
    require(expected is None or digest == expected,"copy source identity differs: "+str(source))
    target = bound(root,name)
    target.parent.mkdir(parents=True,exist_ok=True)
    row = dict(path=name,source=str(source),bytes=size,sha256=digest,role=role)
    journal(root,dict(event="copy_intent",**row))
    with source.open("rb") as left,target.open("xb") as right:
        shutil.copyfileobj(left,right,1024*1024)
        right.flush()
        os.fsync(right.fileno())
    checked(source,digest,size)
    checked(target,digest,size)
    journal(root,dict(event="copy_verified",**row))
    return row


def inventory(directory):
    return {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}


def historical_subset(old):
    """Verify precisely the approved 37 files; do not recurse into older history."""
    checked(old/"receipt_binding.json",OLD_BINDING_SHA)
    binding = read(old/"receipt_binding.json")
    expected = {"receipt_binding.json":OLD_BINDING_SHA}
    for key,name in BINDING_PATHS.items():
        require(isinstance(binding[key],str),"old bound identity missing")
        checked(old/name,binding[key])
        if name in expected:
            require(expected[name] == binding[key],"old shared input/harness binding differs")
        expected[name] = binding[key]
    require(binding["force_executed"] is False and binding["scientific_admission"] is False,"old no-force scope differs")
    payload = read(old/"output_sha256.json")
    require(isinstance(payload,dict) and len(payload) == 87,"old output index differs")
    require(len(HISTORY_PATHS) == len(set(HISTORY_PATHS)) == 37,"historical subset programming error")
    selected_payload = set(HISTORY_PATHS)&set(payload)
    require(len(selected_payload) == 32 and len(set(payload)-selected_payload) == 55,"history selection differs")
    rows = []
    for name in HISTORY_PATHS:
        digest = payload.get(name,expected.get(name))
        require(digest is not None,"history item lacks bound authority: "+name)
        if name in expected:
            require(digest == expected[name],"history binding and output disagree")
        checked(bound(old,name),digest)
        rows.append(dict(path=name,bytes=(old/name).stat().st_size,sha256=digest,
                         authority="old_output_payload" if name in payload else "final_binding_or_fixed_binding_SHA"))
    require(sum(r["bytes"] for r in rows) == 901532,"historical subset byte count differs")
    return dict(schema="hf-cpu-supervision-inheritance-1",protocol=PROTOCOL,subject=SUBJECT,
        upstream_binding_sha256=OLD_BINDING_SHA,scope="selected_payload_only",files=rows,
        run_id=RUN_ID,diagnostic_focus=DIAGNOSTIC_FOCUS,
        selected_files=37,selected_bytes=901532,old_payload_count=87,carried_payload_count=32,
        carried_payload_paths=sorted(selected_payload),omitted_payload_count=55,
        omitted_payloads=[dict(path=name,sha256=payload[name],verified_in_this_card=False) for name in sorted(set(payload)-selected_payload)],
        obsolete_absolute_sources_dereferenced=False,full_old_payload_reverified=False,
        force_executed=False,scientific_admission=False)


def supervisor_roles(root):
    """Declared frozen paths; this does not claim the parent loaded a frozen file."""
    return dict(parent_supervisor=dict(version="SUP1",path=str(root/"aux"/PARENT_FILE),sha256=PARENT_SUPERVISOR_SHA),
                candidate_supervisor=dict(version=VERSION,path=str(root/"aux"/CANDIDATE_FILE),sha256=sha(root/"aux"/CANDIDATE_FILE)))


def selected_metadata(root):
    digest = sha(root/"input_manifest.json")
    return dict(schema="hf-cpu-supervision-selected-source-1",protocol=PROTOCOL,subject=SUBJECT,version=VERSION,
        run_id=RUN_ID,diagnostic_focus=DIAGNOSTIC_FOCUS,**supervisor_roles(root),
        source=str(root/"aux/hf_repo"),source_manifest=str(root/"input_manifest.json"),source_manifest_sha256=digest,
        harness=dict(id=HARNESS,version=VERSION,manifest_sha256=digest),force_executed=False,scientific_admission=False)


def prepare(root, repo, events):
    require(not any((root/n).exists() for n in ("input_manifest.json","aux","provenance","selected_source.json")),"prepare is write-once")
    old = repo/OLD_ROOT
    history = historical_subset(old)
    rows = []
    for item in history["files"]:
        rows.append(copy_row(root,old/item["path"],PROVENANCE+item["path"],
            role="historical_"+item["authority"],expected=item["sha256"]))
    write(root/"inheritance_manifest.json",history)
    for name in AUX_FILES:
        expected = PARENT_SUPERVISOR_SHA if name == PARENT_FILE else None
        rows.append(copy_row(root,repo/name,"aux/"+name,
            role="fixed_parent_supervisor" if expected else "candidate_or_harness_or_auxiliary",expected=expected))
    roles = supervisor_roles(root)
    require(os.environ["HF_CLEAN1_CANDIDATE_SHA"] == roles["candidate_supervisor"]["sha256"]
            and os.environ["HF_CLEAN1_PARENT_SHA"] == PARENT_SUPERVISOR_SHA,"parent-declared supervisor identities differ")
    loaded_parent = dict(version="SUP1",path=str(path(os.environ["HF_CLEAN1_PARENT_PATH"])),
                         sha256=PARENT_SUPERVISOR_SHA)
    require(path(loaded_parent["path"]) == repo/PARENT_FILE,"parent loaded from a different repository")
    checked(loaded_parent["path"],PARENT_SUPERVISOR_SHA)
    science = []
    for name,digest in SCIENCE_IDENTITIES.items():
        filename = repo/name
        checked(filename,digest)
        science.append(dict(path=str(filename),repo_relative_path=name,sha256=digest,bytes=filename.stat().st_size,
                            copied=False,imported=False,role="unchanged_scientific_context_only"))
    runtime = dict(executable=sys.executable,python=sys.version,platform=sys.platform,
                   packages={name:importlib.metadata.version(name) for name in ("psutil","pytest")})
    require(runtime == read(old/"input_manifest.json")["runtime"] and runtime["packages"]["psutil"] == "7.2.2",
            "runtime metadata changed")
    runtime_files = []
    installed = path(sys.executable).parent.parent/"Lib/site-packages/psutil"
    for name,(size,digest) in PSUTIL_FILES.items():
        filename = installed/name
        checked(filename,digest,size)
        runtime_files.append(dict(path=str(filename),package="psutil",package_relative_path=name,
            bytes=size,sha256=digest,copied=False,imported=False,
            read_scope="evidence worker hashes files without importing; parent supervisor and tests still import psutil"))
    checked(SUBPROCESS_FILE,SUBPROCESS_SHA,SUBPROCESS_BYTES)
    stdlib_files = [dict(path=str(path(SUBPROCESS_FILE)),module="subprocess",bytes=SUBPROCESS_BYTES,
        sha256=SUBPROCESS_SHA,copied=False,imported=False,
        read_scope="evidence worker checks library bytes only; parent and candidate use subprocess")]
    manifest = dict(schema="hf-cpu-supervision-inputs-1",protocol=PROTOCOL,subject=SUBJECT,version=VERSION,harness_id=HARNESS,
        run_id=RUN_ID,diagnostic_focus=DIAGNOSTIC_FOCUS,**roles,loaded_parent_supervisor=loaded_parent,
        supervisor_sha256=roles["candidate_supervisor"]["sha256"],supervisor_sha256_role="candidate",
        repo=str(repo),created_utc=utc(),files=rows,
        inheritance_manifest=dict(path="inheritance_manifest.json",sha256=sha(root/"inheritance_manifest.json")),
        harness_binding="The input manifest binds SUP2 and CPU-CLEAN1; fixed SUP1 is the parent control, not scientific H1",
        expected_tests=list(EXPECTED_TESTS),science_identity_checks=science,
        runtime=runtime,runtime_file_checks=runtime_files,stdlib_file_checks=stdlib_files,
        force_executed=False,scientific_admission=False)
    write(root/"input_manifest.json",manifest)
    write(root/"selected_source.json",selected_metadata(root))
    result = verify_snapshot(root,repo)
    events.emit("preparation_complete",input_manifest_sha256=sha(root/"input_manifest.json"),source_verification=result)
    return dict(status="pass",files=len(rows),copied_bytes=sum(r["bytes"] for r in rows),source_verification=result,
                force_executed=False,scientific_admission=False)


def verify_snapshot(root, repo=None, *, require_live=True):
    """Read-only verification; relocated payload uses require_live=False."""
    root = path(root)
    manifest = read(root/"input_manifest.json")
    require(manifest["schema"] == "hf-cpu-supervision-inputs-1" and manifest["protocol"] == PROTOCOL
            and manifest["subject"] == SUBJECT and manifest["version"] == VERSION and manifest["harness_id"] == HARNESS
            and manifest["run_id"] == RUN_ID and manifest["diagnostic_focus"] == DIAGNOSTIC_FOCUS,"input identity differs")
    repo = path(repo if repo is not None else manifest["repo"])
    if require_live:
        require(repo == path(manifest["repo"]),"canonical repository identity differs")
    names = set()
    for row in manifest["files"]:
        require(row["path"] not in names,"duplicate input path")
        names.add(row["path"])
        checked(bound(root,row["path"]),row["sha256"],row["bytes"])
        if require_live:
            checked(row["source"],row["sha256"],row["bytes"])
    require(len(names) == len(HISTORY_PATHS)+len(AUX_FILES),"input inventory count differs")
    require({n.removeprefix("aux/") for n in names if n.startswith("aux/")} == set(AUX_FILES),"auxiliary inventory differs")
    require({n.removeprefix(PROVENANCE) for n in names if n.startswith(PROVENANCE)} == set(HISTORY_PATHS),"historical inventory differs")
    for folder in ("aux","provenance"):
        require(inventory(root/folder) == {name.removeprefix(folder+"/") for name in names if name.startswith(folder+"/")},
                "unexpected or missing "+folder+" file")
    roles = supervisor_roles(root)
    checked(root/"aux"/PARENT_FILE,PARENT_SUPERVISOR_SHA)
    require(manifest["supervisor_sha256"] == roles["candidate_supervisor"]["sha256"]
            and manifest["supervisor_sha256_role"] == "candidate","candidate digest role differs")
    for role in ("parent_supervisor","candidate_supervisor"):
        require(manifest[role]["version"] == roles[role]["version"] and manifest[role]["sha256"] == roles[role]["sha256"],"supervisor role differs")
        if require_live:
            require(manifest[role] == roles[role],"declared frozen supervisor path differs")
    if require_live:
        loaded = manifest["loaded_parent_supervisor"]
        require(loaded == dict(version="SUP1",path=str(repo/PARENT_FILE),sha256=PARENT_SUPERVISOR_SHA),
                "actual parent source differs")
        checked(loaded["path"],loaded["sha256"])
    checked(root/"inheritance_manifest.json",manifest["inheritance_manifest"]["sha256"])
    inherit = read(root/"inheritance_manifest.json")
    require(inherit["selected_files"] == 37 and inherit["selected_bytes"] == 901532
            and inherit["carried_payload_count"] == 32 and inherit["omitted_payload_count"] == 55
            and not inherit["full_old_payload_reverified"],"inheritance scope differs")
    checked(root/PROVENANCE/"receipt_binding.json",OLD_BINDING_SHA)
    for row in inherit["files"]:
        checked(bound(root,PROVENANCE+row["path"]),row["sha256"],row["bytes"])
    require(manifest["expected_tests"] == list(EXPECTED_TESTS),"declared test set differs")
    selected = read(root/"selected_source.json")
    if require_live:
        require(selected == selected_metadata(root),"selected auxiliary source differs")
    else:
        require(selected["source_manifest_sha256"] == sha(root/"input_manifest.json")
                and selected["harness"] == dict(id=HARNESS,version=VERSION,manifest_sha256=sha(root/"input_manifest.json")),
                "portable selected identity differs")
    require({r["repo_relative_path"]:r["sha256"] for r in manifest["science_identity_checks"]} == SCIENCE_IDENTITIES,
            "historical science-only identity set differs")
    if require_live:
        for row in manifest["science_identity_checks"]:
            require(path(row["path"]) == repo/row["repo_relative_path"],"science context path differs")
            checked(row["path"],row["sha256"],row["bytes"])
    runtime_rows = manifest["runtime_file_checks"]
    require(len(runtime_rows) == 3 and {r["package_relative_path"]:(r["bytes"],r["sha256"]) for r in runtime_rows} == PSUTIL_FILES,
            "psutil source/binary identity set differs")
    require(manifest["runtime"]["packages"]["psutil"] == "7.2.2","declared psutil version differs")
    standard = manifest["stdlib_file_checks"]
    require(len(standard) == 1 and standard[0]["module"] == "subprocess"
            and (standard[0]["bytes"],standard[0]["sha256"]) == (SUBPROCESS_BYTES,SUBPROCESS_SHA),"subprocess identity differs")
    if require_live:
        installed = path(sys.executable).parent.parent/"Lib/site-packages/psutil"
        require(sys.version == manifest["runtime"]["python"] and sys.executable == manifest["runtime"]["executable"]
                and {name:importlib.metadata.version(name) for name in ("psutil","pytest")} == manifest["runtime"]["packages"],
                "runtime metadata changed")
        for row in runtime_rows:
            require(row["package"] == "psutil" and path(row["path"]) == installed/row["package_relative_path"],"runtime file path differs")
            checked(row["path"],row["sha256"],row["bytes"])
        require(path(standard[0]["path"]) == path(SUBPROCESS_FILE),"subprocess path differs")
        checked(standard[0]["path"],SUBPROCESS_SHA,SUBPROCESS_BYTES)
    return dict(status="pass",input_files=len(names),input_bytes=sum(r["bytes"] for r in manifest["files"]),
        historical_selected_files=37,historical_carried_payload=32,historical_omitted_payload=55,
        live_sources_checked=bool(require_live),science_context_hashes_checked=4 if require_live else 0,
        psutil_files_checked=3 if require_live else 0,stdlib_files_checked=1 if require_live else 0,
        run_id=RUN_ID,diagnostic_focus=DIAGNOSTIC_FOCUS,**roles,
        scientific_package_copied=False,missing=0,mismatches=0,input_manifest_sha256=sha(root/"input_manifest.json"),
        supervisor_sha256=roles["candidate_supervisor"]["sha256"],force_executed=False,scientific_admission=False)


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def read_ndjson(filename):
    rows,errors = [],[]
    if not filename.is_file():
        return rows,[dict(reason="missing",path=str(filename))]
    def number(text):
        value = float(text)
        require(math.isfinite(value),"nonfinite JSON number")
        return value
    def bad_constant(text):
        raise ValueError("nonstandard JSON constant: "+text)
    for line_number,line in enumerate(filename.read_bytes().splitlines(keepends=True),1):
        if not line.endswith(b"\n"):
            errors.append(dict(line=line_number,reason="incomplete_line"))
        try:
            row = json.loads(line,parse_float=number,parse_constant=bad_constant)
            require(isinstance(row,dict),"NDJSON row is not an object")
            rows.append(dict(line=line_number,record=row))
        except Exception as error:
            errors.append(dict(line=line_number,reason="unparseable",error=str(error)))
    return rows,errors


def partial_preservation(root, repo, error):
    result = dict(status="evidence_failure",error=dict(type=type(error).__name__,message=str(error)),
                  recorded_files=[],uncommitted_files=[],issues=[],force_executed=False,scientific_admission=False)
    rows = []
    if (root/"input_manifest.json").exists():
        try:
            rows = read(root/"input_manifest.json")["files"]
        except Exception as problem:
            result["issues"].append(dict(path="input_manifest.json",error=str(problem)))
    if not rows:
        journal_rows,issues = read_ndjson(root/"prepare_journal.ndjson")
        result["issues"].extend(issues)
        rows = [item["record"] for item in journal_rows if item["record"].get("event") == "copy_verified"]
    seen = set()
    for row in rows:
        observed = dict(path=row["path"],expected_sha256=row["sha256"],expected_bytes=row["bytes"])
        seen.add(row["path"])
        for side,filename in (("copy",bound(root,row["path"])),("source",path(row["source"]))):
            try:
                observed[side] = dict(exists=filename.is_file(),bytes=filename.stat().st_size if filename.is_file() else None,
                                      sha256=sha(filename) if filename.is_file() else None)
                checked(filename,row["sha256"],row["bytes"])
                observed[side]["matches"] = True
            except Exception as problem:
                observed.setdefault(side,{})["matches"] = False
                observed[side]["error"] = str(problem)
        result["recorded_files"].append(observed)
    for folder in ("aux","provenance"):
        for filename in sorted((root/folder).rglob("*")):
            if filename.is_file() and filename.relative_to(root).as_posix() not in seen:
                result["uncommitted_files"].append(dict(path=filename.relative_to(root).as_posix(),bytes=filename.stat().st_size,
                    sha256=sha(filename),status="not_in_verified_copy_records",accepted_source_identity=False))
    result["limitation"] = "Raw partial bytes are preserved; hashes alone do not establish an accepted source state"
    return result


def test_coverage(root):
    filename = root/"events/P1_tests.ndjson"
    items,issues = read_ndjson(filename)
    rows = [item["record"] for item in items]
    result = []
    for nodeid in EXPECTED_TESTS:
        reports = [r for r in rows if r.get("event") == "test_report" and r.get("nodeid") == nodeid]
        calls = [r for r in reports if r.get("when") == "call"]
        phases = {kind:[r for r in reports if r.get("when") == kind] for kind in ("setup","call","teardown")}
        if not reports:
            status = "not_executed"
        elif any(r.get("outcome") == "failed" for r in reports):
            status = "failed"
        elif any(r.get("outcome") != "passed" for r in reports):
            status = "not_passed"
        elif all(len(phases[k]) == 1 for k in phases):
            status = "passed"
        else:
            status = "incomplete"
        elapsed = sum(r.get("duration_seconds",0.) for r in reports if finite(r.get("duration_seconds")))
        result.append(dict(nodeid=nodeid,status=status,duration_seconds=elapsed,
            group="controlled_interface" if "test_windows_cleanup_contract.py" in nodeid else "real_windows_scenario",
            elapsed_scope="saved setup+call+teardown durations; not entire Job or test session wall time",
            reports=reports,call_count=len(calls)))
    expected_set = set(EXPECTED_TESTS)
    extras = sorted({r.get("nodeid","") for r in rows if r.get("event") == "test_report" and r.get("nodeid") not in expected_set})
    return dict(schema="hf-cpu-supervision-test-coverage-1",protocol=PROTOCOL,subject=SUBJECT,
        expected=list(EXPECTED_TESTS),rows=result,extra_nodeids=extras,event_parse_issues=issues,
        event_sha256=sha(filename) if filename.is_file() else None,
        first_failure=next((r for r in rows if r.get("event") == "test_report" and r.get("outcome") == "failed"),None),
        session_records=[r for r in rows if r.get("event") == "session_finish"],
        force_executed=False,scientific_admission=False)


def verify_synthetic_completion(root, resources, preservation, coverage):
    require(preservation["status"] == "pass","sources did not pass")
    require(resources.get("status") == "synthetic_supervision_pass_no_force","parent did not report synthetic pass")
    phases = resources.get("phases",[])
    require([p.get("name") for p in phases] == ["P0_prepare","P1_tests"]
            and all(p.get("returncode") == 0 and p.get("cleanup_verified") and not p.get("errors")
                    and p.get("supervisor_sha256") == PARENT_SUPERVISOR_SHA
                    and p.get("source_version") == "SUP1" for p in phases),"parent SUP1 phases did not pass and clean")
    manifest = read(root/"input_manifest.json")
    roles = supervisor_roles(root)
    verification = read(root/"results/P1_tests/verification.json")
    digest = sha(root/"input_manifest.json")
    expected_pairs = {(Path(n.split("::",1)[0]).name,n.split("::",1)[1]) for n in EXPECTED_TESTS}
    require(isinstance(verification.get("expected"),list)
            and all(isinstance(pair,list) and len(pair) == 2 and all(isinstance(v,str) for v in pair)
                    for pair in verification["expected"]),"verification test-pair schema differs")
    require(verification["status"] == "pass" and verification["count"] == 21
            and len(verification["expected"]) == 21 and {tuple(pair) for pair in verification["expected"]} == expected_pairs,
            "verification does not identify the exact 21 tests")
    require(verification["source_manifest_sha256"] == digest and verification["harness_manifest_sha256"] == digest,
            "verification source/harness identity differs")
    require(all(verification[role] == roles[role] for role in roles),"verification dual supervisor identity differs")
    require(verification["protocol"] == PROTOCOL and verification["run_id"] == RUN_ID
            and verification["subject"] == SUBJECT,"verification protocol/subject differs")
    checked(root/"events/P1_tests.ndjson",verification["event_sha256"])
    checked(root/"results/P1_tests/pytest.xml",verification["xml_sha256"])
    require(not coverage["event_parse_issues"] and not coverage["extra_nodeids"]
            and len(coverage["rows"]) == 21 and all(r["status"] == "passed" and r["call_count"] == 1 for r in coverage["rows"]),
            "test reports incomplete, duplicated, skipped or failed")
    items,errors = read_ndjson(root/"events/P1_tests.ndjson")
    require(not errors,"incomplete pytest events")
    rows = [item["record"] for item in items]
    for index,row in enumerate(rows,1):
        require(row.get("schema") == "hf-s0-event-1" and row.get("sequence") == index
                and row.get("phase") == "P1_tests" and row.get("version") == VERSION
                and row.get("source_manifest_sha256") == digest and row.get("harness_id") == HARNESS
                and row.get("harness_manifest_sha256") == digest,"pytest event identity differs")
        require(row.get("event") not in ("internal_error","internalerror","collection_failed","pytest_internal_error","pytest_interrupted"),
                "pytest internal/collection error")
        if row.get("event") == "collection_report":
            require(row.get("outcome") == "passed","collection report failed or skipped")
        if row.get("event") in ("test_report","test_start"):
            nodeid = row["nodeid"]
            require(nodeid in EXPECTED_TESTS,"unexpected test nodeid")
            filename = root/"aux/hf_repo"/nodeid.split("::",1)[0]
            require(path(row["source_path"]) == filename and path(row["test_file_path"]) == filename,"test loaded path differs")
        if row.get("event") == "test_report":
            require(not row.get("wasxfail") and row.get("outcome") == "passed","xfail or failed report")
    collections = [r for r in rows if r.get("event") == "collection_finish"]
    sessions = [r for r in rows if r.get("event") == "session_finish"]
    configurations = [r for r in rows if r.get("event") == "session_configured"]
    require(len(collections) == 1 and collections[0]["outcome"] == "passed"
            and len(collections[0]["nodeids"]) == 21 and set(collections[0]["nodeids"]) == set(EXPECTED_TESTS),"collection differs")
    require(len(sessions) == 1 and sessions[0]["exitstatus"] == 0 and sessions[0]["testsfailed"] == 0
            and sessions[0]["testscollected"] == 21,"session did not complete 21 tests")
    require(len(configurations) == 1 and path(configurations[0]["rootpath"]) == root/"aux/hf_repo"
            and path(configurations[0]["rootdir"]) == root/"aux/hf_repo"
            and path(configurations[0]["invocation_dir"]) == root,"pytest execution root differs")
    cases = ET.parse(root/"results/P1_tests/pytest.xml").getroot().findall(".//testcase")
    require(len(cases) == 21 and all(not any(child.tag in ("failure","error","skipped") for child in case) for case in cases),
            "JUnit does not report 21 passes")
    xml_pairs = {(case.get("classname"),case.get("name")) for case in cases}
    expected_pairs = {(n.split("::",1)[0].removesuffix(".py").replace("/","."),n.split("::",1)[1]) for n in EXPECTED_TESTS}
    require(xml_pairs == expected_pairs,"JUnit testcase identities differ")
    runtime_files = {"runtime_identity_contract.json":"test_windows_cleanup_contract.py",
                     "runtime_identity_process.json":"test_windows_owned_process.py",
                     "runtime_identity.json":"test_windows_owned_cpu.py"}
    loaded = {}
    loaded_hashes = {}
    for name,test_name in runtime_files.items():
        filename = root/"results/P1_tests"/name
        runtime = read(filename)
        loaded[name] = runtime
        loaded_hashes[name] = sha(filename)
        require(runtime["source_manifest_sha256"] == digest and runtime["harness_manifest_sha256"] == digest
                and runtime["version"] == VERSION and runtime["harness_id"] == HARNESS,"loaded harness identity differs")
        require(all(runtime[role] == roles[role] for role in roles),"runtime dual supervisor identity differs")
        require(runtime["loaded_parent_supervisor"] == manifest["loaded_parent_supervisor"],"actual parent source declaration differs")
        require(path(runtime["test_path"]) == root/"aux/hf_repo/tests"/test_name
                and runtime["test_sha256"] == sha(root/"aux/hf_repo/tests"/test_name),"runtime test identity differs")
    require(verification["loaded_sources"] == loaded and verification["loaded_sources_sha256"] == loaded_hashes,
            "parent loaded-source map differs from actual saved identities")
    return dict(status="synthetic_supervision_pass_no_force",contract=HARNESS,tests=21,**roles,
        verification_sha256=sha(root/"results/P1_tests/verification.json"),runtime_identity_sha256=loaded_hashes,
        force_executed=False,scientific_admission=False)


def lifecycle_evidence(root):
    """Preserve all new-case saved records; plots describe evidence, not a new test."""
    base = root/"results/P1_tests/synthetic-temp"
    cases,issues = [],[]
    if base.exists():
        for directory in sorted(p for p in base.iterdir() if p.is_dir() and not p.is_symlink() and not p.is_junction()):
            # Original five also have logs; only the revised instances emit these records.
            if not any((directory/name).exists() for name in ("request.json","receipt.json","invocation_budget.json","budget_rejection.json","control_result.json")):
                continue
            case = dict(path=directory.relative_to(root).as_posix(),json_records={},streams={},files=[],issues=[])
            for filename in sorted(directory.rglob("*")):
                if not filename.is_file():
                    continue
                name = filename.relative_to(directory).as_posix()
                case["files"].append(dict(path=filename.relative_to(root).as_posix(),bytes=filename.stat().st_size,sha256=sha(filename)))
                if filename.suffix == ".ndjson":
                    rows,errors = read_ndjson(filename)
                    case["streams"][name] = dict(rows=rows,issues=errors)
                    case["issues"].extend(dict(path=name,**error) for error in errors)
                elif filename.suffix == ".json":
                    try:
                        case["json_records"][name] = read(filename)
                    except Exception as error:
                        case["issues"].append(dict(path=name,error=str(error)))
            cases.append(case)
    else:
        issues.append(dict(reason="synthetic_directory_not_reached"))
    return dict(schema="hf-cpu-supervision-lifecycle-1",protocol=PROTOCOL,subject=SUBJECT,cases=cases,issues=issues,
        force_executed=False,scientific_admission=False,
        limitation="Partial/missing records remain visible. Graphs do not manufacture process creation, normal exit, completed work or test acceptance.")


def proof_evidence(root, directory, receipt_name, receipt, expected_identity):
    """Check saved SUP2 statements and raw journal; no native/process calls."""
    roles = supervisor_roles(root)
    candidate = roles["candidate_supervisor"]
    require(receipt["protocol"] == PROTOCOL and receipt["cleanup_contract"] == HARNESS,
            "receipt uses another cleanup contract")
    require(receipt["candidate_supervisor"] == candidate and receipt["supervisor_sha256"] == candidate["sha256"],
            "receipt candidate source differs")
    proof = receipt["cleanup_proof"]
    require(proof["pass"] is True and proof["status"] == "verified_all_instances"
            and receipt["cleanup_verified"] is True and proof["errors"] == [],"instance cleanup did not pass")
    require(proof["root_wait_completed"] is True and proof["root_handle_close_verified"] is True,
            "root wait/handle closure not proved")
    require(proof["coverage_verified"] is True and proof["termination_verified"] is True
            and proof["observation_handles_closed"] is True and proof["job_handle_closed"] is True,
            "coverage/termination/Job closure flags are incomplete")
    require(proof["limits"] == dict(observation_handles=64,unique_history=256,instance_journal_bytes=16*1024**2),
            "real scenario changed the declared observer/history/journal limits")
    identities = proof["identities"]
    require(isinstance(identities,list) and 0 < len(identities) <= 256,"invalid identity count")
    keys = [(row["pid"],row["creation_filetime"]) for row in identities]
    require(len(keys) == len(set(keys)),"duplicate instance identity inflated coverage")
    require(all(isinstance(pid,int) and not isinstance(pid,bool) and pid > 0
                and isinstance(ct,int) and not isinstance(ct,bool) and ct > 0 for pid,ct in keys),"invalid raw instance identity")
    final = proof["final_accounting"]
    require(final["ActiveProcesses"] == 0 and final["TotalProcesses"] == len(keys)
            == proof["unique_bound_identity_count"] == proof["signaled_identity_count"],"history/termination counts do not close")
    require(finite(final["query_start_monotonic"]) and finite(final["query_end_monotonic"])
            and final["query_start_monotonic"] <= final["query_end_monotonic"],"final accounting lacks a valid bracket")
    require(sum(row["handle_kind"] == "borrowed_root" for row in identities) == 1,"root identity not unique")
    require(next(row["pid"] for row in identities if row["handle_kind"] == "borrowed_root") == receipt["pid"],
            "borrowed root identity differs from launched root")
    for row in identities:
        require(row["handle_kind"] in ("borrowed_root","owned_observation")
                and row["signaled"] is True and row["handle_closed"] is True,"instance termination/release incomplete")
        times = [row[name] for name in ("bound_monotonic","signaled_monotonic","handle_closed_monotonic")]
        require(all(finite(t) for t in times) and times == sorted(times)
                and times[-1] <= final["query_start_monotonic"]
                and times[-1] <= receipt["cleanup_deadline_monotonic"],"instance ordering or final accounting precedes release")
    journal_info = proof["journal"]
    require(journal_info["closed"] is True and journal_info["failed"] is False and journal_info["limit_bytes"] == 16*1024**2
            and 0 < journal_info["bytes"] <= journal_info["limit_bytes"],"instance journal not closed or capacity exceeded")
    journal_path = path(journal_info["path"])
    if not Path(journal_info["path"]).is_absolute():
        journal_path = path(directory/journal_info["path"])
    require(journal_path.resolve().is_relative_to(directory.resolve()),"instance journal escaped its scenario directory")
    checked(journal_path,journal_info["sha256"],journal_info["bytes"])
    parsed,parse_errors = read_ndjson(journal_path)
    require(not parse_errors and parsed,"instance journal missing/truncated/unparseable")
    events = [item["record"] for item in parsed]
    require(journal_info["records"] == len(events),"journal record count differs from persisted records")
    expected_journal_identity = dict(expected_identity,protocol=PROTOCOL,cleanup_contract=HARNESS,
                                     candidate_supervisor=candidate)
    previous = None
    for index,event in enumerate(events,1):
        require(event["schema"] == "hf-job-instance-proof-1" and event["sequence"] == index,
                "instance journal schema/sequence differs")
        require(event["identity"] == expected_journal_identity,"instance journal harness identity differs")
        require(finite(event["monotonic"]) and (previous is None or event["monotonic"] >= previous),"journal clock moved backwards")
        previous = event["monotonic"]
        if "query_start_monotonic" in event or "query_end_monotonic" in event:
            require(finite(event.get("query_start_monotonic")) and finite(event.get("query_end_monotonic"))
                    and event["query_start_monotonic"] <= event["query_end_monotonic"],"invalid instance API bracket")
        require(event["event"] != "proof_error","pass proof journal contains an error")
    finals = [event for event in events if event["event"] == "final_accounting"]
    require(finals,"journal lacks final accounting")
    last_final = finals[-1]
    require(all(last_final[key] == value for key,value in final.items()),"raw final accounting differs from receipt")
    root_waits = [event for event in events if event["event"] == "root_wait_completed"]
    root_closes = [event for event in events if event["event"] == "root_handle_closed"]
    require(len(root_waits) == len(root_closes) == 1
            and root_waits[0]["sequence"] < root_closes[0]["sequence"] < last_final["sequence"],
            "root wait/close/final accounting sequence incomplete")
    require(root_waits[0]["returncode"] == receipt["returncode"],"saved root wait exit code differs")
    table = []
    for item in identities:
        key = (item["pid"],item["creation_filetime"])
        local = [event for event in events if (event.get("pid"),event.get("creation_filetime")) == key]
        binds = [event for event in local if event["event"] == "instance_bound"]
        signals = [event for event in local if event["event"] == "instance_signaled"]
        name = "root_handle_closed" if item["handle_kind"] == "borrowed_root" else "observation_handle_closed"
        closes = [event for event in local if event["event"] == name]
        require(len(binds) == len(signals) == len(closes) == 1
                and binds[0]["sequence"] < signals[0]["sequence"] < closes[0]["sequence"],
                "raw binding/signal/release chain incomplete")
        bind,signal,closed = binds[0],signals[0],closes[0]
        require(all(event["handle_kind"] == item["handle_kind"] for event in (bind,signal,closed)),
                "raw handle ownership differs from instance summary")
        require(signal["wait_result"] == 0 and signal["query_end_monotonic"] == item["signaled_monotonic"]
                and bind["query_end_monotonic"] == item["bound_monotonic"]
                and closed["query_end_monotonic"] == item["handle_closed_monotonic"],
                "raw API signal or instance timestamps differ")
        membership,creation = bind["membership_query"],bind["creation_query"]
        require(membership == item["membership_query"] and creation == item["creation_query"],
                "saved identity query brackets differ")
        chain = [bind["query_start_monotonic"],membership["query_start_monotonic"],membership["query_end_monotonic"],
                 creation["query_start_monotonic"],creation["query_end_monotonic"],bind["query_end_monotonic"],
                 signal["query_start_monotonic"],signal["query_end_monotonic"],closed["query_start_monotonic"],closed["query_end_monotonic"]]
        require(all(finite(t) for t in chain) and chain == sorted(chain),"raw instance query intervals are reversed/overlapping")
        require(item["wait_failed"] is False and item["handle_close_attempted"] is True and item["close_error"] is None,
                "saved instance contains a wait/close failure")
        if item["handle_kind"] == "borrowed_root":
            require(signal["sequence"] < root_waits[0]["sequence"] < closed["sequence"],
                    "root owner wait precedes same-handle signal")
        else:
            require(closed["signaled"] is True and closed["purpose"] == "same_instance_signaled",
                    "observer was merely released without a signal proof")
        table.append(dict(pid=key[0],creation_filetime=key[1],handle_kind=item["handle_kind"],
            bound_monotonic=item["bound_monotonic"],signaled_monotonic=item["signaled_monotonic"],
            handle_closed_monotonic=item["handle_closed_monotonic"]))
    receipt_path = directory/receipt_name
    return dict(status="verified_all_instances",receipt_path=receipt_path.relative_to(root).as_posix(),
        receipt_bytes=receipt_path.stat().st_size,receipt_sha256=sha(receipt_path),
        journal_path=journal_path.relative_to(root).as_posix(),journal_bytes=journal_info["bytes"],
        journal_sha256=journal_info["sha256"],journal_records=len(events),identity=expected_identity,
        proof=proof,time_table=table)


def cleanup_evidence(root, lifecycle, coverage, resources):
    """Keep original outcomes, real-instance proof and evidence preservation distinct."""
    records,issues = [],[]
    digest = sha(root/"input_manifest.json") if (root/"input_manifest.json").is_file() else None
    try:
        roles = supervisor_roles(root)
    except Exception as error:
        roles = dict(parent_supervisor=None,candidate_supervisor=None)
        issues.append(dict(stage="source_identity",type=type(error).__name__,message=str(error)))
    actual_cases = []
    control_cases = []
    real_nodes,control_nodes = [],[]
    cpu_nodes = {
        "busy_outer":"tests/test_windows_owned_cpu.py::test_busy_sleep_and_exited_descendant_keep_cumulative_cpu",
        "timeout":"tests/test_windows_owned_cpu.py::test_timeout_preserves_partial_samples_and_cleans_job",
        "fault_query":"tests/test_windows_owned_cpu.py::test_observation_failure_stops_and_independent_cleanup_survives[query]",
        "fault_write":"tests/test_windows_owned_cpu.py::test_observation_failure_stops_and_independent_cleanup_survives[write]",
    }
    def check_identity(identity):
        require(identity["source_manifest_sha256"] == digest and identity["harness_manifest_sha256"] == digest
                and identity["harness_id"] == HARNESS and identity["version"] == VERSION
                and identity["source_version"] == VERSION and identity["phase"] == "P1_tests",
                "saved request/control harness identity differs")
    for case in lifecycle["cases"]:
        directory = bound(root,case["path"])
        saved = case["json_records"]
        if "control_result.json" in saved:
            item = saved["control_result.json"]
            control_cases.append(dict(path=case["path"],record=item))
            try:
                require(item["schema"] == "hf-clean1-controlled-case-1" and item["protocol"] == PROTOCOL
                        and item["case_kind"] == "controlled_interface","controlled-case schema differs")
                check_identity(item["identity"])
                require(item["nodeid"] in EXPECTED_TESTS and "test_windows_cleanup_contract.py" in item["nodeid"],
                        "controlled result identifies another testcase")
                require(item["nodeid"] not in control_nodes,"duplicate controlled-case result")
                control_nodes.append(item["nodeid"])
            except Exception as error:
                issues.append(dict(path=case["path"],type=type(error).__name__,message=str(error)))
            continue
        if "receipt.json" not in saved and "request.json" not in saved:
            continue
        actual_cases.append(case["path"])
        try:
            request = saved["request.json"]
            nodeid = request.get("test_nodeid") or cpu_nodes[request["identity"]["role"]]
            require(nodeid in EXPECTED_TESTS and "test_windows_cleanup_contract.py" not in nodeid,
                    "real request identifies another testcase")
            require(nodeid not in real_nodes,"duplicate real scenario")
            real_nodes.append(nodeid)
        except Exception as error:
            issues.append(dict(path=case["path"],type=type(error).__name__,message=str(error)))
        for receipt_name,request_name in (("receipt.json","request.json"),("descendant_receipt.json","descendant_request.json")):
            if receipt_name not in saved:
                if receipt_name == "receipt.json":
                    issues.append(dict(path=case["path"],reason="request_without_returned_receipt"))
                continue
            receipt = saved[receipt_name]
            record = dict(path=(directory/receipt_name).relative_to(root).as_posix(),
                          status="incomplete_or_failed",raw_proof=receipt.get("cleanup_proof"),issues=[])
            try:
                request = saved[request_name]
                identity = request["identity"]
                check_identity(identity)
                record.update(proof_evidence(root,directory,receipt_name,receipt,identity))
            except Exception as error:
                issue = dict(type=type(error).__name__,message=str(error))
                record["issues"].append(issue)
                issues.append(dict(path=record["path"],**issue))
            records.append(record)
    real_rows = [row for row in coverage["rows"] if row["group"] == "real_windows_scenario"]
    controls = [row for row in coverage["rows"] if row["group"] == "controlled_interface"]
    complete = (resources.get("status") == "synthetic_supervision_pass_no_force"
                and len(real_rows) == 9 and len(controls) == 12
                and all(row["status"] == "passed" for row in coverage["rows"])
                and len(actual_cases) == len(real_nodes) == 9 and len(control_cases) == len(control_nodes) == 12
                and len(records) == 10 and not issues
                and all(record["status"] == "verified_all_instances" for record in records))
    if complete:
        status = "verified_all_instances"
    elif not actual_cases:
        status = "not_reached" if not control_cases else "controlled_checks_only"
    else:
        status = "incomplete_or_failed"
    return dict(schema="hf-cpu-supervision-cleanup-contract-1",protocol=PROTOCOL,run_id=RUN_ID,
        diagnostic_focus=DIAGNOSTIC_FOCUS,subject=SUBJECT,version=VERSION,harness_id=HARNESS,contract=HARNESS,
        source_manifest_sha256=digest,harness_manifest_sha256=digest,**roles,status=status,
        real_case_count=len(actual_cases),control_case_count=len(control_cases),proof_count=len(records),
        records=records,control_records=control_cases,issues=issues,
        original_test_outcomes=[dict(nodeid=row["nodeid"],group=row["group"],status=row["status"]) for row in coverage["rows"]],
        parent_test_status=resources.get("status"),force_executed=False,scientific_admission=False,
        interpretation="Saved instance termination and release proofs are distinct from expected injected failures, original test outcomes and payload sealing; no force/scientific admission")


def tests_svg(coverage):
    rows = coverage["rows"]
    maximum = max([r["duration_seconds"] for r in rows]+[1.])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1480" height="{100+38*len(rows)}"><rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial,sans-serif" font-size="12"><text x="20" y="26">Synthetic supervision tests, NOT force CPU | F-CPU-CLEAN1: 12 controlled + 9 real scenarios</text>',
        '<text x="20" y="48">Recorded setup + call + teardown seconds; missing/incomplete tests are not passes.</text>']
    for index,row in enumerate(rows):
        y = 78+38*index
        color = "#497f65" if row["status"] == "passed" else "#a84040" if row["status"] == "failed" else "#888"
        label = row["nodeid"].removeprefix("tests/")
        parts.extend((f'<text x="20" y="{y+12}">{escape(label)}</text>',
            f'<rect x="940" y="{y}" width="{290*row["duration_seconds"]/maximum:.2f}" height="15" fill="{color}"/>',
            f'<text x="1240" y="{y+12}">{row["duration_seconds"]:.6f}s | {escape(row["status"])}</text>'))
    return "".join(parts)+"</g></svg>\n"


def seal(root, repo, events):
    try:
        preservation = verify_snapshot(root,repo)
    except Exception as error:
        preservation = partial_preservation(root,repo,error)
    write(root/"source_preservation.json",preservation)
    errors = []
    try:
        resources = read(root/"resources.json")
    except Exception as error:
        resources = dict(phases=[],status="unknown")
        errors.append(dict(stage="read_resources",type=type(error).__name__,message=str(error)))
    coverage = test_coverage(root)
    write(root/"test_coverage.json",coverage)
    lifecycle = lifecycle_evidence(root)
    write(root/"synthetic_lifecycle.json",lifecycle)
    try:
        contract = cleanup_evidence(root,lifecycle,coverage,resources)
    except Exception as error:
        detail = dict(stage="cleanup_proof_aggregation",type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        errors.append(detail)
        contract = dict(schema="hf-cpu-supervision-cleanup-contract-1",protocol=PROTOCOL,run_id=RUN_ID,
            diagnostic_focus=DIAGNOSTIC_FOCUS,subject=SUBJECT,version=VERSION,harness_id=HARNESS,contract=HARNESS,
            status="partial_or_unreadable",real_case_count=0,control_case_count=0,proof_count=0,records=[],issues=[detail],
            force_executed=False,scientific_admission=False)
    write(root/"cleanup_contract.json",contract)
    for name,producer in (("tests.svg",lambda:tests_svg(coverage)),("cpu_lifecycle.svg",lambda:lifecycle_svg(lifecycle)),
                          ("resources.svg",lambda:resources_svg(resources))):
        try:
            binary_write(root/name,producer().encode("utf-8"))
        except Exception as error:
            errors.append(dict(stage="plot",path=name,type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
    completion = dict(status="not_claimed_parent_stopped",parent_status=resources.get("status"),contract=HARNESS,
                      force_executed=False,scientific_admission=False)
    complete = preservation["status"] == "pass" and not errors
    if resources.get("status") == "synthetic_supervision_pass_no_force":
        try:
            completion = verify_synthetic_completion(root,resources,preservation,coverage)
            require(contract["status"] == "verified_all_instances" and contract["proof_count"] == 10
                    and contract["real_case_count"] == 9 and contract["control_case_count"] == 12 and not contract["issues"],
                    "21-pass claim lacks the ten complete real-instance proofs")
            require(not lifecycle["issues"] and all(not case["issues"] for case in lifecycle["cases"]),
                    "saved scenario records incomplete or unreadable")
            real = [case for case in lifecycle["cases"] if "receipt.json" in case["json_records"]]
            require(len(real) == 9,"real scenario inventory differs")
            cpu_cases = []
            for case in real:
                require(all(name in case["json_records"] for name in ("request.json","receipt.json","call_outcome.json")),
                        "real scenario missing declared request/receipt/outcome")
                if "cpu.ndjson" not in case["streams"]:
                    continue
                cpu_cases.append(case)
                require("invocation_budget.json" in case["json_records"] and case["streams"]["cpu.ndjson"]["rows"],
                        "CPU scenario lacks budget/initial CPU evidence")
                if "test_busy_sleep" in case["path"]:
                    require(all(name in case["json_records"] for name in ("descendant_request.json","descendant_receipt.json",
                                "descendant_call_outcome.json","cpu_comparison.json")),"busy scenario lacks saved nested accounting proof")
                    require(all(name in case["streams"] and case["streams"][name]["rows"]
                                for name in ("outer_markers.ndjson","descendant_markers.ndjson","descendant_cpu.ndjson")),
                            "busy scenario lacks marker/CPU evidence")
                    outer = case["json_records"]["receipt.json"]
                    child = case["json_records"]["descendant_receipt.json"]
                    require(outer["reason"] == child["reason"] == "normal_exit" and outer["returncode"] == child["returncode"] == 0,
                            "busy normal-exit proof incomplete")
                    parent_ids = {(r["pid"],r["creation_filetime"]) for r in outer["cleanup_proof"]["identities"]}
                    child_ids = {(r["pid"],r["creation_filetime"]) for r in child["cleanup_proof"]["identities"]}
                    require(child_ids <= parent_ids,"nested instance identities absent in outer history")
                    require(any(row["handle_kind"] == "owned_observation"
                                and (row["pid"],row["creation_filetime"]) in child_ids
                                and row["handle_closed_monotonic"] < outer["cleanup_requested_monotonic"]
                                for row in outer["cleanup_proof"]["identities"]),"no nested observer released during normal outer polling")
                if "test_observation_failure" in case["path"]:
                    require("fault_calls.json" in case["json_records"],"declared fault calls evidence missing")
            require(len(cpu_cases) == 4,"CPU scenario inventory differs")
            completion["cleanup_contract_status"] = "verified_all_instances"
        except Exception as error:
            complete = False
            detail = dict(stage="completion",type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
            errors.append(detail)
            completion = dict(status="completion_not_supported",contract=HARNESS,error=detail,force_executed=False,scientific_admission=False)
    excluded = {"output_sha256.json","receipt_binding.json","execution_receipt.json","ledger.json",
                "events/P2_seal.ndjson","logs/P2_seal.log"}
    write(root/"errors.json",dict(parent_error=resources.get("error"),first_test_failure=coverage["first_failure"],
        evidence_errors=errors,cleanup_record_issues=contract["issues"],source_status=preservation["status"],
        force_executed=False,scientific_admission=False))
    result = dict(schema="hf-cpu-supervision-evidence-worker-1",protocol=PROTOCOL,subject=SUBJECT,action="seal",
        run_id=RUN_ID,diagnostic_focus=DIAGNOSTIC_FOCUS,status="pass" if complete else "evidence_failure",
        payload_sealed=True,synthetic_result=completion,
        cleanup_contract=dict(path="cleanup_contract.json",sha256=sha(root/"cleanup_contract.json"),
            status=contract["status"],proof_count=contract["proof_count"]),
        source_preservation=preservation,test_coverage_path="test_coverage.json",lifecycle_path="synthetic_lifecycle.json",
        resources_scope="pre-seal only; parent final receipt binds seal resources and cleanup",
        excluded_live_or_final_bindings=sorted(excluded),force_executed=False,scientific_admission=False,
        limitation="Payload sealing, expected injected faults and candidate test acceptance are distinct; no force/science executed")
    write(root/"results/seal/summary.json",result)
    outputs = {filename.relative_to(root).as_posix():sha(filename) for filename in sorted(root.rglob("*"))
               if filename.is_file() and filename.relative_to(root).as_posix() not in excluded}
    write(root/"output_sha256.json",outputs)
    events.emit("seal_complete",status=result["status"],output_manifest_sha256=sha(root/"output_sha256.json"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--action",choices=("prepare","seal"),required=True)
    args = parser.parse_args()
    root,repo = path(args.root),path(args.repo)
    require(root != repo and not repo.is_relative_to(root),"evidence root must not contain repository")
    require(root == repo/"hf4_c2_stable_f_validation"/RUN_ID and root.is_dir(),
            "only the campaign parent may create the authorized unique evidence root")
    output = root/"results"/args.action
    events,begin = EventLog(),time.perf_counter()
    try:
        require(not output.exists(),"worker action is write-once")
        events.emit("worker_started",action=args.action,subject=SUBJECT)
        if args.action == "seal":
            result = seal(root,repo,events)
            return 0 if result["status"] == "pass" else 2
        result = prepare(root,repo,events)
        write(output/"summary.json",dict(schema="hf-cpu-supervision-evidence-worker-1",protocol=PROTOCOL,
            subject=SUBJECT,action=args.action,elapsed_seconds=time.perf_counter()-begin,**result))
        events.emit("worker_finished",action=args.action,status=result["status"])
        return 0
    except Exception as error:
        failure = dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        if not (output/"summary.json").exists():
            write(output/"summary.json",dict(schema="hf-cpu-supervision-evidence-worker-1",protocol=PROTOCOL,
                subject=SUBJECT,action=args.action,status="evidence_failure",elapsed_seconds=time.perf_counter()-begin,
                force_executed=False,scientific_admission=False,error=failure))
        events.emit("worker_failed",action=args.action,**failure)
        return 2
    finally:
        events.close()


def lifecycle_svg(evidence):
    busy = next((case for case in evidence["cases"] if "test_busy_sleep" in case["path"]),None)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1340" height="760"><rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial,sans-serif" font-size="12"><text x="20" y="26">Synthetic supervision tests, NOT force CPU | busy case, two owned Jobs</text>',
        '<text x="20" y="48">Blue user, green kernel, black total CPU; query endpoints shown without filling missing data.</text>',
        '<text x="20" y="68">Job accounting includes active/exited descendants; markers are Python observations, not OS creation times.</text>']
    if busy is None:
        return "".join(parts)+'<text x="20" y="115">Busy scenario not reached: no synthetic CPU curve available.</text></g></svg>\n'
    all_times = []
    for stream in busy["streams"].values():
        for item in stream["rows"]:
            row = item["record"]
            for key in ("query_end_monotonic","monotonic","actual_start_monotonic","actual_end_monotonic"):
                if finite(row.get(key)):
                    all_times.append(row[key])
    for record in busy["json_records"].values():
        if isinstance(record,dict):
            all_times.extend(record[k] for k in ("request_monotonic","cleanup_requested_monotonic") if finite(record.get(k)))
    origin = min(all_times) if all_times else 0.
    span = max(max(all_times)-origin,1.) if all_times else 1.
    x = lambda t: 105.+1050.*(t-origin)/span
    annotations = []
    for level,(cpu_name,marker_name,request_name,receipt_name) in enumerate((
        ("cpu.ndjson","outer_markers.ndjson","request.json","receipt.json"),
        ("descendant_cpu.ndjson","descendant_markers.ndjson","descendant_request.json","descendant_receipt.json"))):
        top,bottom = 115.+280.*level,305.+280.*level
        stream = busy["streams"].get(cpu_name,dict(rows=[],issues=[dict(reason="missing")]))
        rows = [item["record"] for item in stream["rows"]]
        valid = lambda row: (finite(row.get("query_start_monotonic")) and finite(row.get("query_end_monotonic"))
            and row["query_start_monotonic"] <= row["query_end_monotonic"]
            and all(isinstance(row.get(k),int) and not isinstance(row.get(k),bool) and row[k] >= 0
                    for k in ("total_user_time_100ns","total_kernel_time_100ns")))
        usable = [row for row in rows if valid(row)]
        ymax = max([.01]+[(r["total_user_time_100ns"]+r["total_kernel_time_100ns"])/1e7 for r in usable])
        y = lambda value: bottom-(bottom-top)*value/ymax
        parts.extend((f'<text x="20" y="{top-12}">{"Outer" if level == 0 else "Descendant"} Job | {escape(cpu_name)}</text>',
            f'<path d="M105 {top} V{bottom} H1155" stroke="#555" fill="none"/>',
            f'<text x="40" y="{top+8}">{ymax:.4f}s</text><text x="65" y="{bottom+4}">0</text>'))
        if not usable:
            parts.append(f'<text x="130" y="{top+35}">No readable CPU samples; scenario incomplete/not reached.</text>')
        for left,right in zip(rows,rows[1:]):
            if not valid(left) or not valid(right):
                continue
            gap = right["query_end_monotonic"]-left["query_start_monotonic"]
            monotone = (right.get("sequence") == left.get("sequence",-1)+1
                        and right["query_start_monotonic"] >= left["query_end_monotonic"]
                        and all(right[k] >= left[k] for k in ("total_user_time_100ns","total_kernel_time_100ns")))
            # A 50ms target is not a promise. Show observed long gaps, never bridge them.
            if not monotone or gap > .25:
                parts.append(f'<text x="{x(right["query_end_monotonic"]):.2f}" y="{top+18}" fill="#a84040" font-size="10">gap/quality</text>')
                continue
            for key,color in (("total_user_time_100ns","#356c9b"),("total_kernel_time_100ns","#497f65"),(None,"#222")):
                a = left[key]/1e7 if key else (left["total_user_time_100ns"]+left["total_kernel_time_100ns"])/1e7
                b = right[key]/1e7 if key else (right["total_user_time_100ns"]+right["total_kernel_time_100ns"])/1e7
                parts.append(f'<line x1="{x(left["query_end_monotonic"]):.2f}" y1="{y(a):.2f}" x2="{x(right["query_end_monotonic"]):.2f}" y2="{y(b):.2f}" stroke="{color}"/>')
        for row in usable:
            total = (row["total_user_time_100ns"]+row["total_kernel_time_100ns"])/1e7
            parts.append(f'<circle cx="{x(row["query_end_monotonic"]):.2f}" cy="{y(total):.2f}" r="1.8" fill="#222"><title>{escape(str(row.get("lifecycle")))}</title></circle>')
        marks = busy["streams"].get(marker_name,dict(rows=[]))["rows"]
        boundaries = [(item["record"].get("monotonic"),str(item["record"].get("event"))) for item in marks]
        for item in marks:
            row = item["record"]
            for key in ("actual_start_monotonic","actual_end_monotonic"):
                if finite(row.get(key)):
                    boundaries.append((row[key],str(row.get("event"))+":"+key.removesuffix("_monotonic")))
        req,rec = busy["json_records"].get(request_name,{}),busy["json_records"].get(receipt_name,{})
        if isinstance(req,dict):
            boundaries.append((req.get("request_monotonic"),"request"))
        if isinstance(rec,dict):
            boundaries.append((rec.get("cleanup_requested_monotonic"),"cleanup_request"))
            annotations.append(f'{"outer" if level == 0 else "descendant"}: reason={rec.get("reason","missing")}; returncode={rec.get("returncode")}; cleanup={rec.get("cleanup_verified")}')
        for index,(moment,label) in enumerate(boundaries):
            if not finite(moment):
                continue
            xx = x(moment)
            parts.append(f'<path d="M{xx:.2f} {top} V{bottom}" stroke="#b8b8b8" stroke-dasharray="2 3"><title>{escape(label)}</title></path>')
            parts.append(f'<text x="{xx:.2f}" y="{bottom+16+11*(index%4)}" font-size="8" transform="rotate(-12 {xx:.2f} {bottom+16+11*(index%4)})">{escape(label)}</text>')
    parts.extend((f'<text x="105" y="662">0</text><text x="1070" y="662">{span:.4f} s</text>',
        '<text x="340" y="683">Wall time since earliest saved request/query/marker; 0.25s plot-gap marker is not an acceptance threshold.</text>',
        f'<text x="20" y="706">{escape(" | ".join(annotations))}</text>',
        f'<text x="20" y="730">Saved parsing issues: {len(busy["issues"])}. Exact counters, brackets, all markers and partial records: synthetic_lifecycle.json.</text>'))
    return "".join(parts)+"</g></svg>\n"


def resources_svg(resources):
    rows = resources.get("phases",[])
    tmax = max([r.get("elapsed_seconds",0.) for r in rows]+[1.])
    rmax = max([r.get("peak_tree_rss_bytes",0) for r in rows]+[1])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{100+44*len(rows)}"><rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial,sans-serif" font-size="12"><text x="20" y="25">Synthetic supervision tests, NOT force CPU | pre-seal resources</text>',
        '<text x="20" y="48">Parent final receipt includes seal and cleanup. RSS is sampled parent + owned Job, not a hard instantaneous bound.</text>']
    for index,row in enumerate(rows):
        yy = 73+44*index
        seconds,rss = row.get("elapsed_seconds",0.),row.get("peak_tree_rss_bytes",0)
        parts.extend((f'<text x="20" y="{yy+12}">{escape(str(row.get("name")))} | {escape(str(row.get("reason")))}</text>',
            f'<rect x="380" y="{yy}" width="{240*seconds/tmax:.3f}" height="15" fill="#356c9b"/><text x="630" y="{yy+12}">{seconds:.6f}s</text>',
            f'<rect x="810" y="{yy}" width="{220*rss/rmax:.3f}" height="15" fill="#497f65"/><text x="1040" y="{yy+12}">{rss/1024**2:.3f} MiB</text>'))
    return "".join(parts)+"</g></svg>\n"


if __name__ == "__main__":
    raise SystemExit(main())
