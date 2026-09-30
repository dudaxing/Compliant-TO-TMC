"""F-STREAM1: bounded volume/integrity reading of one saved gzip: strict bounded JSON census, no interval analysis.

Authoring is text/AST only. The sole parent entry owns a 300-second / 4-GiB
window and the original SUP1. Child prepare/stream/seal modes share this file.
"""
from __future__ import annotations
import time
_ENTRY_START = time.monotonic()

import argparse
import ast
import codecs
import re
from datetime import datetime, timezone
import hashlib
from html import escape
import importlib.util
import io
import json
import math
import ntpath
import os
from pathlib import Path
import stat
import sys
import threading
import traceback

PROTOCOL = "F-STREAM1"
RUN_ID = "native_stream_001"
SUBJECT = "saved_gzip_stream_census"
SUCCESS = "saved_gzip_stream_census_complete"
DRIVER = "run_saved_trace_census.py"
OLD_RUN = "micro_trace_002"
OLD_BINDING_SHA = "43a0436b5aec9911c3e678fb2874813780bced5538520aaf9574f1b328ef8281"
SUP_SHA = "9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32"
SUP_BYTES = 15838
PYTHON = "D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe"
PYTHON_VERSION = "3.13.6 (tags/v3.13.6:4e66535, Aug  6 2025, 14:36:00) [MSC v.1944 64 bit (AMD64)]"
DOCS = ("docs/CURRENT_STATUS.md", "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md")
HISTORY = ("receipt_binding.json", "execution_receipt.json", "output_sha256.json", "input_manifest.json",
           "native_manifest.json", "results/trace/summary.json")
NATIVE = (
    ("native/plugins/profile/2026_09_30_07_15_43/LAPTOP-F1SA5QHI.trace.json.gz", 24572396,
     "e5a40ab0916e6b39f08e3c61a5c702d151f5e745553a4277c969ef69284eae40", "saved_gzip_reference"),
    ("native/plugins/profile/2026_09_30_07_15_43/LAPTOP-F1SA5QHI.xplane.pb", 87819545,
     "39992eb34a704ca01ffca2c1e65b56e499d7ddfcbd52c5fc43cb6ffd80f19dfe", "saved_xplane_reference"))
SITE = "D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Lib/site-packages/"
RUNTIME = (
    (SITE+"psutil/__init__.py", "aux/runtime/psutil/__init__.py", 92363, "7b6a0675824eb1fa2ff0cb1eb36e358dc454703e51dfa4e9a0e6ccd26a159f0c", "psutil"),
    (SITE+"psutil/_pswindows.py", "aux/runtime/psutil/_pswindows.py", 36466, "0bbd52dcb214735be4168d11a2ae192d5bc7265c8cf72c611179476479687f54", "psutil._pswindows"),
    (SITE+"psutil/_psutil_windows.pyd", "aux/runtime/psutil/_psutil_windows.pyd", 70656, "0035450801bd7d938e9e146c5ec28e619cb5a5f4a18cdc53ac7e9734c7f94f78", "psutil._psutil_windows"),
    ("C:/Python313/Lib/subprocess.py", "aux/runtime/stdlib/subprocess.py", 91718, "970207fdd712c92f7dc14d1623d2574f7e0910ceb0b5c37652a7a0850f35a396", "subprocess"),
    ("C:/Python313/Lib/gzip.py", "aux/runtime/stdlib/gzip.py", 25324, "a9793ac60271964c2efb9f94ccd3b6e39e41312b84d9cfeb37c49d310842f7cd", "gzip"),
    ("C:/Python313/Lib/_compression.py", "aux/runtime/stdlib/_compression.py", 5843, "a10cf1a317374641bcdb8252499e9cb9d4d6e774ac724edfdddd0433ead771d9", "_compression"))
BINARIES = (
    (PYTHON, 255320, "d21e2337a4734864e3d9c266834247ee2a8d5e8ed3583c44474f341907bf49ab"),
    ("C:/Python313/python.exe", 104928, "91566dc8bb9a336c36c607ee0d5a5135e54ddce2418e2cd7728a49c8f098904a"),
    ("C:/Python313/python313.dll", 6124376, "dd05f134a2f8126a8cfe8d797b87fa966537b894dd49f93336566f9e8d21d4bd"))
RULE_SOURCE = "hf_repo/scripts/micro_trace_v2_evidence.py"
RULE_BYTES = 106549
RULE_SHA = "7acd278ff379c06ab1e44e1f288fa9e6e3cc82c7952383c16417270ed5d7613e"
BYTES_RUN = "native_volume_001"
BYTES_HISTORY = (
    ("receipt_binding.json",6479,"fb43ced8f5fe2560f63c54d74efd590215da77dceea90833900259fadfae48c1"),
    ("execution_receipt.json",10609,"ca1575789e186eb36668a28c087440f425bccc6e2a287406999838bf75dbc37a"),
    ("input_manifest.json",9352,"2efda0ce7bbd7048a970bc637cbcf8630e97e3b4a3b50de3c4bb334f7e163804"),
    ("results/volume/count.json",62265,"48a37a521aed568b20c2aa11ac14b3be7d8495800b4871a07f822da031060a68"))
PRIOR_PREFIX_BYTES = 268435457
PRIOR_PREFIX_SHA = "7a6f358825b281d5c59f58824eb77a93f7972a11e3bc2794a98919a084d0ec90"
RUNTIME += (
    ("C:/Python313/Lib/json/__init__.py","aux/runtime/stdlib/json/__init__.py",14379,"feb17670e443e5db2723f217727dcc5d5e155c40e4e6935b16061c88542f24e7","json"),
    ("C:/Python313/Lib/json/decoder.py","aux/runtime/stdlib/json/decoder.py",13236,"9c1530bb0b07f7435161f1005c14fc458b973f35f6e1802e4c175494c06891b0","json.decoder"),
    ("C:/Python313/Lib/json/scanner.py","aux/runtime/stdlib/json/scanner.py",2507,"b2577f9db9f69a0a27f251776349238b17b8b214a01128e7477b0f7d8e24a186","json.scanner"),
    ("C:/Python313/Lib/json/encoder.py","aux/runtime/stdlib/json/encoder.py",16592,"955cb7cc721e3881f084c2e334eb66d6a1f0fc08457b3e06cccbea218b3819fe","json.encoder"),
    ("C:/Python313/Lib/encodings/__init__.py","aux/runtime/stdlib/encodings/__init__.py",6058,"8b997e9f7beef09de01c34ac34191866d3ab25e17164e08f411940b070bc3e74","encodings"),
    ("C:/Python313/Lib/encodings/aliases.py","aux/runtime/stdlib/encodings/aliases.py",16265,"486d5a2f3172d22e6d1e6205d807da13d9839a48e96fadbd4071484d16b793f1","encodings.aliases"),
    ("C:/Python313/Lib/encodings/utf_8.py","aux/runtime/stdlib/encodings/utf_8.py",1047,"9c54c7db8ce0722ca4ddb5f45d4e170357e37991afb3fcdc091721bf6c09257e","encodings.utf_8"),
    ("C:/Python313/Lib/re/__init__.py","aux/runtime/stdlib/re/__init__.py",18304,"af6b51360592d5b38a256a19e717061fa2656d80c112fac578b742b4773edd76","re"),
    ("C:/Python313/Lib/re/_compiler.py","aux/runtime/stdlib/re/_compiler.py",27058,"d7ef020125816e25ef2ca687267c620e4662b8f0845ad118dbadbf0154a65543","re._compiler"),
    ("C:/Python313/Lib/re/_parser.py","aux/runtime/stdlib/re/_parser.py",42318,"b133abc2964b936e0aed859dc3e315cac8b5cb05d48e44ac0acfdbcb40971271","re._parser"),
    ("C:/Python313/Lib/re/_constants.py","aux/runtime/stdlib/re/_constants.py",6161,"ef5f6b04831fcff51f1637316b832d28af860d6d67736edad036ad3ffb059858","re._constants"),
    ("C:/Python313/Lib/re/_casefix.py","aux/runtime/stdlib/re/_casefix.py",5550,"b0dee234e5f8096fc9c1b035ec52d0b1b50cc1f3aea20b360b8be902e53ac752","re._casefix"),
    ("C:/Python313/Lib/enum.py","aux/runtime/stdlib/enum.py",87774,"03c53d7c1baea4afc19daaeb19fc18b928f69f2dfe2752aaf2d5c2d033dececa","enum"))
PARSER_LIMITS = dict(unit_bytes=1048576,depth=64,object_keys=4096,key_bytes=4096,event_count=4000000,
                     state_items=4096,samples=128,field_text_bytes=4096,retained_text_bytes=16777216,
                     progress_updates=64,progress_bytes=65536,generated_bytes=33554432,
                     generated_file_bytes=4194304,root_files=128,log_rows=128,log_bytes=1048576)
CONTROL_GROUPS = ("legal_root_positions","utf8_keys_unicode","string_escapes","scalar_values",
    "multi_member","body_cap","crc_trailer","utf8_configuration","json_grammar","tail",
    "duplicate_keys","numeric_configuration","root_trace_contract","unit_key_limits",
    "depth_event_state_limits","lifecycle_record_capacity")
EVIDENCE_ROOT = None
WRITE_DEADLINE = None
INVENTORY_CACHE = None
WRITE_FAILED_PATHS = set()
TERMINAL_RESERVE_BYTES = 2*1024**2
TERMINAL_RESERVE_FILES = 8
TERMINAL_PATHS = ("ledger.json","execution_receipt.json","receipt_binding.json","resources.json",
    "payload_status.json","output_sha256.json","results/seal/summary.json","results/P3_seal_supervision/receipt.json")
FAILURE_CLOSING_PATHS = ("ledger.json","execution_receipt.json","receipt_binding.json")

CAP = 1024**3
CHUNK = 1024**2
SECONDS = 300.
RSS_LIMIT = 4*1024**3
LIMITS = {"P0":15., "P1":240., "P3":15., "shared":30.}
GUARD = 5.25
STAGES = {"prepare":("historical_authority", "input_freeze", "source_precheck"),
          "stream":("source_binding", "runtime_identity", "controls", "gzip_stream"),
          "seal":("source_postcheck", "saved_results", "supervision_review", "visualizations", "payload_manifest")}
EXCLUSIONS = ("output_sha256.json", "receipt_binding.json", "execution_receipt.json", "ledger.json",
              "events/P3_seal.ndjson", "logs/P3_seal.log")
TARGETS = ("plan.json", "input_manifest.json", "source_authority.json", "source_refs.json", "source_precheck.json",
    "rules_reference.json", "results/prepare/summary.json", "results/stream/runtime_identity.json", "results/stream/controls.json",
    "results/stream/census.json", "results/stream/samples.json", "results/stream/progress.json", "results/stream/count.json", "results/stream/summary.json",
    "source_postcheck.json", "source_preservation.json", "supervision_checks.json", "diagnostic_verification.json",
    "resources.json", "payload_status.json", "census.svg", "resources.svg", "results/seal/summary.json",
    "results/P0_prepare_supervision/receipt.json", "results/P1_controls_stream_supervision/receipt.json",
    "results/P3_seal_supervision/receipt.json", "events/P0_prepare.ndjson", "events/P1_controls_stream.ndjson",
    "events/P3_seal.ndjson", "logs/P0_prepare.log", "logs/P1_controls_stream.log", "logs/P3_seal.log",
    "output_sha256.json", "execution_receipt.json")


class BudgetError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def utc():
    return datetime.now(timezone.utc).isoformat()


def extended(value):
    value=ntpath.normpath(os.fspath(value)) if os.name=="nt" else str(Path(value).resolve())
    if os.name=="nt" and not value.startswith("\\\\?\\"):
        require(not value.startswith("\\\\"), "UNC source refused")
        value="\\\\?\\"+value
    return Path(value)


def safe_path(filename, *, within=None):
    filename=extended(filename)
    if within is not None:
        require(filename.is_relative_to(extended(within)), "source outside explicit repository boundary")
    for ancestor in reversed((filename,*filename.parents)):
        info=ancestor.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info,"st_file_attributes",0)&0x400,
                "reparse/symlink refused: "+str(ancestor))
    return filename


def gate(deadline):
    if deadline is not None and time.monotonic()>=deadline:
        raise BudgetError("active deadline exhausted")


def digest(filename, deadline=None):
    filename=safe_path(filename)
    value=hashlib.sha256()
    with filename.open("rb") as stream:
        while True:
            gate(deadline)
            data=stream.read(CHUNK)
            if not data:break
            value.update(data)
    gate(deadline)
    return value.hexdigest()


def checked(filename, size, expected, deadline=None, *, within=None):
    filename=safe_path(filename,within=within)
    require(filename.is_file() and filename.stat().st_size==size, "source size/type differs: "+str(filename))
    require(digest(filename,deadline)==expected, "source SHA differs: "+str(filename))
    return dict(path=str(filename),bytes=size,sha256=expected)


def read(filename):
    gate(WRITE_DEADLINE)
    def invalid(value):raise ValueError("nonfinite JSON refused: "+value)
    value=json.loads(safe_path(filename).read_text(encoding="utf-8"),parse_constant=invalid)
    gate(WRITE_DEADLINE);return value


def encode_json(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8")


def cache_file(filename,size,*,remove=False):
    global INVENTORY_CACHE
    if INVENTORY_CACHE is None or EVIDENCE_ROOT is None:return
    relative=Path(filename).relative_to(EVIDENCE_ROOT).as_posix()
    files=INVENTORY_CACHE["files"]
    if remove:files.pop(relative,None)
    else:files[relative]=size
    INVENTORY_CACHE["root_files"]=len(files)
    INVENTORY_CACHE["generated_bytes"]=sum(n for name,n in files.items() if not name.startswith(("aux/","provenance/")))


def exact_write(filename,data,*,replace=False,closing=False):
    filename=Path(filename);filename.parent.mkdir(parents=True,exist_ok=True)
    target=filename.with_suffix(".pending.json") if replace else filename
    # Reserve the whole attempted new inode in the cache before any I/O. A
    # partial/open/fsync error keeps this pessimistic allocation, never frees it.
    cache_file(target,max(len(data),INVENTORY_CACHE["files"].get(target.relative_to(EVIDENCE_ROOT).as_posix(),0)))
    with target.open("xb") as stream:
        require(stream.write(data)==len(data),"short evidence write")
        stream.flush();os.fsync(stream.fileno())
    cache_file(target,len(data))
    if replace:
        os.replace(target,filename);cache_file(target,0,remove=True);cache_file(filename,len(data))
    metadata=dict(path=filename.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if not closing:
        try:gate(WRITE_DEADLINE)
        except BudgetError as error:
            error.written_metadata=metadata # exact successful bytes, late clock only
            raise
    return metadata


def write(filename,value,*,replace=False):
    filename=Path(filename);relative=filename.relative_to(EVIDENCE_ROOT).as_posix()
    require(relative not in WRITE_FAILED_PATHS,"prior failed evidence writer cannot retry: "+relative)
    gate(WRITE_DEADLINE);data=encode_json(value)
    if filename.name=="progress.json" and len(data)>PARSER_LIMITS["progress_bytes"]:fault("progress_capacity","saved progress exceeds declared cap")
    admit_write(filename,len(data));gate(WRITE_DEADLINE)
    try:return exact_write(filename,data,replace=replace)
    except BaseException as error:
        if not getattr(error,"written_metadata",None):WRITE_FAILED_PATHS.add(relative)
        raise


def failure_close_write(filename,value):
    """Once-only necessary FAILED terminal preservation, never an activity permit.

    Uses the last complete bounded inventory plus pessimistically tracked writes.
    No walk/read/file hash/source checks or new phase occur here. Elapsed time is
    still counted against the original card; an overrun remains resource_stop.
    """
    filename=Path(filename);relative=filename.relative_to(EVIDENCE_ROOT).as_posix()
    require(relative in FAILURE_CLOSING_PATHS and value.get("status")!=SUCCESS,"failure closing cannot grant success")
    require(relative not in WRITE_FAILED_PATHS,"failed terminal writer cannot retry")
    require(INVENTORY_CACHE is not None and INVENTORY_CACHE["complete"] is True,"no conservative closing inventory available")
    data=encode_json(value)
    capacity_admit(INVENTORY_CACHE["generated_bytes"],INVENTORY_CACHE["root_files"],len(data))
    try:return exact_write(filename,data,replace=True,closing=True)
    except BaseException:
        WRITE_FAILED_PATHS.add(relative);raise


def error_record(error):
    row=dict(type=type(error).__name__,module=type(error).__module__,message=str(error)[:4096],traceback=traceback.format_exc()[-16384:])
    if isinstance(error,StreamError):row.update(kind=error.kind,byte_offset=error.byte_offset,unit_start_byte=error.unit_start,character_offset=error.character_offset)
    return row


def flags():
    return dict(scientific_admission=False,force_executed=False,runtime_native_trace_observed=False,
                native_json_parsed=False,xplane_decoded=False)


def identity(phase, manifest_sha, driver_sha):
    return dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,phase=phase,
                input_manifest_sha256=manifest_sha,driver_sha256=driver_sha,supervisor_sha256=SUP_SHA)


class Events:
    def __init__(self,root,phase,deadline):
        self.root=root;self.phase=phase;self.deadline=deadline;self.sequence=0;self.bytes=0
        filename=root/"events"/(phase+".ndjson");admit_write(filename,0)
        self.stream=filename.open("x",encoding="utf-8",newline="\n")
    def emit(self,event,**fields):
        gate(self.deadline)
        row=dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,phase=self.phase,event=event,
            sequence=self.sequence+1,utc=utc(),monotonic=time.monotonic(),pid=os.getpid(),native_tid=threading.get_native_id(),**fields)
        text=json.dumps(row,ensure_ascii=False,allow_nan=False)+"\n";size=len(text.encode("utf-8"))
        log_admit(self.sequence,self.bytes,size);admit_write(self.root/"events"/(self.phase+".ndjson"),size,append=True)
        filename=self.root/"events"/(self.phase+".ndjson")
        cache_file(filename,self.bytes+size)
        require(self.stream.write(text)==len(text),"short event recording")
        self.stream.flush();os.fsync(self.stream.fileno());self.sequence+=1;self.bytes+=size
    def close(self):self.stream.close()


def pin_runtime(deadline=None):
    require(sys.version==PYTHON_VERSION and extended(sys.executable)==extended(PYTHON), "fixed HF Python differs")
    sources=[checked(filename,size,wanted,deadline) for filename,_,size,wanted,_ in RUNTIME]
    installed=[dict(checked(filename,size,wanted,deadline),copied=False,
                    interpretation="installed-only file identity; no DLL loading assertion") for filename,size,wanted in BINARIES]
    return dict(protocol=PROTOCOL,run_id=RUN_ID,python=dict(executable=sys.executable,version=sys.version),
                runtime_sources=sources,installed_only=installed,zlib_expected_origin="built-in")


def actual_runtime(deadline):
    pinned=pin_runtime(deadline)
    import importlib
    import gzip
    import psutil
    require(psutil.__version__=="7.2.2","fixed psutil version differs")
    modules=[]
    for filename,_,size,wanted,name in RUNTIME:
        module=importlib.import_module(name)
        require(extended(module.__file__)==extended(filename),"actual runtime module path differs: "+name)
        checked(module.__file__,size,wanted,deadline)
        modules.append(dict(name=name,path=str(extended(module.__file__)),bytes=size,sha256=wanted,actual_import=True))
    interfaces=[]
    for name in ("_json","_codecs","_io","_sre","zlib"):
        module=importlib.import_module(name)
        require(getattr(module,"__file__",None) is None and module.__spec__.origin=="built-in","pinned built-in interface differs: "+name)
        interfaces.append(dict(name=name,origin="built-in",has_file=False))
    for name in ("codecs","io"):
        module=importlib.import_module(name)
        require(module.__spec__.origin=="frozen","pinned frozen interface differs: "+name)
        interfaces.append(dict(name=name,origin="frozen",disk_py_not_asserted_as_executed_source=True))
    pinned.update(status="verified",actual_modules=modules,interfaces=interfaces,
        reader_type="gzip._GzipReader directly; no io.BufferedReader/GzipFile",
        qualification="selected module/file interface identity only; not full stdlib or loaded-DLL closure")
    return gzip,pinned


def extract_rule(filename,deadline):
    checked(filename,RULE_BYTES,RULE_SHA,deadline)
    tree=ast.parse(Path(filename).read_text(encoding="utf-8"),filename=str(filename));gate(deadline)
    literals={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in ("PROTOCOL","ANNOTATION_STAGES","TARGET_RULE"):
                require(name not in literals,"duplicate source rule assignment")
                literals[name]=ast.literal_eval(node.value)
    require(literals["PROTOCOL"]=="F-TRACE2" and len(literals["ANNOTATION_STAGES"])==5,"five original application names differ")
    rule=literals["TARGET_RULE"]
    require(rule["version"]=="f-trace1-target-1" and rule["module"]=="jit_reused"
            and rule["application_annotations_never_internal"] is True,"original target-rule identity differs")
    return dict(protocol=PROTOCOL,run_id=RUN_ID,source_sha256=RULE_SHA,source_bytes=RULE_BYTES,
        extraction="stdlib AST literal_eval only; old helper never imported or invoked",target_rule=rule,
        annotations=[literals["PROTOCOL"]+":"+n for n in literals["ANNOTATION_STAGES"]],**flags())


def authority(repo,deadline):
    old=repo/"hf4_c2_stable_f_validation"/OLD_RUN
    checked(old/"receipt_binding.json",8785,OLD_BINDING_SHA,deadline,within=repo)
    binding=read(old/"receipt_binding.json")
    require(binding["protocol"]=="F-TRACE2" and binding["run_id"]==OLD_RUN and binding["status"]=="observability_not_pass", "old outcome/identity differs")
    for name in ("execution_receipt.json","output_sha256.json","input_manifest.json"):
        item=binding["records"][name];checked(old/name,item["bytes"],item["sha256"],deadline,within=repo)
    output=read(old/"output_sha256.json")
    histories=[]
    for name in HISTORY:
        filename=old/name
        if name=="receipt_binding.json":size,wanted=8785,OLD_BINDING_SHA
        else:
            item=binding["records"][name];size,wanted=item["bytes"],item["sha256"]
            if name in output:require(output[name]==wanted,"old binding/output conflict: "+name)
        checked(filename,size,wanted,deadline,within=repo)
        histories.append(dict(historical_run=OLD_RUN,original_path=name,project_relative_path=filename.relative_to(repo).as_posix(),bytes=size,sha256=wanted))
    require(sum(row["bytes"] for row in histories)==339677, "six old JSON bytes differ")
    # Decode only after the entire selected small metadata set is authenticated.
    native=read(old/"native_manifest.json")
    references=[]
    for name,size,wanted,role in NATIVE:
        require(output[name]==wanted, "native reference output SHA differs")
        matching=[row for row in native["files"] if row["path"]==name]
        require(len(matching)==1 and matching[0]["bytes"]==size and matching[0]["sha256"]==wanted
                and matching[0]["status"]=="hashed", "native reference original metadata differs")
        filename=old/name;checked(filename,size,wanted,deadline,within=repo)
        references.append(dict(project_relative_path=filename.relative_to(repo).as_posix(),bytes=size,sha256=wanted,
            role=role,storage_mode="external_read_only_reference",copied=False,decoded=False))
    require(sum(row["bytes"] for row in histories+references)==112731618,"old eight source bytes differ")
    bytesroot=repo/"hf4_c2_stable_f_validation"/BYTES_RUN
    for name,size,wanted in BYTES_HISTORY:
        checked(bytesroot/name,size,wanted,deadline,within=repo)
        histories.append(dict(historical_run=BYTES_RUN,original_path=name,project_relative_path=(bytesroot/name).relative_to(repo).as_posix(),bytes=size,sha256=wanted))
    prior_binding=read(bytesroot/"receipt_binding.json")
    require(prior_binding["protocol"]=="F-BYTES1" and prior_binding["run_id"]==BYTES_RUN
            and prior_binding["status"]=="saved_gzip_volume_diagnostic_complete","old BYTES identity differs")
    for name,size,wanted in BYTES_HISTORY[1:]:
        row=prior_binding["records"][name]
        require(row["bytes"]==size and row["sha256"]==wanted,"old BYTES direct binding differs")
    prior=read(bytesroot/"results/volume/count.json")
    require(prior["status"]=="body_over_cap" and prior["returned_bytes"]==PRIOR_PREFIX_BYTES
            and prior["body_bytes_lower_bound"]==PRIOR_PREFIX_BYTES and prior["prefix_sha256"]==PRIOR_PREFIX_SHA
            and prior["eof_verified"] is False and prior["full_body_sha256"] is None,"old BYTES prefix/lower bound differs")
    require(sum(row["bytes"] for row in histories)==428382,"ten historical JSON bytes differ")
    return dict(protocol=PROTOCOL,run_id=RUN_ID,status="verified",old_protocol="F-TRACE2",old_run_id=OLD_RUN,
                old_outcome="observability_not_pass",binding_sha256=OLD_BINDING_SHA,histories=histories,references=references,
                old_json_bytes=339677,old_native_bytes=112391941,old_eight_bytes=112731618,selected_history_bytes=112820323,history_json_bytes=428382,
                prior_prefix_bytes=PRIOR_PREFIX_BYTES,prior_prefix_sha256=PRIOR_PREFIX_SHA,
                bytes_binding_sha256=BYTES_HISTORY[0][2],**flags())


def input_specs(repo,root,old,plan):
    rows=[]
    def add(source,target,role,size,wanted):
        rows.append(dict(source=str(extended(source)),path=target,role=role,storage_mode="copied",bytes=size,sha256=wanted))
    for row in old["histories"]:add(repo/row["project_relative_path"],"provenance/"+row["historical_run"]+"/"+row["original_path"],"selected_history_json",row["bytes"],row["sha256"])
    for name in ("hf_repo/scripts/"+DRIVER,*DOCS):
        meta=plan["author_inputs"][name];add(repo/name,"aux/"+name,"author_input",meta["bytes"],meta["sha256"])
    add(repo/RULE_SOURCE,"aux/"+RULE_SOURCE,"fixed_rule_reference",RULE_BYTES,RULE_SHA)
    add(repo/"hf_repo/scripts/windows_owned_process.py","aux/hf_repo/scripts/windows_owned_process.py","fixed_sup1",SUP_BYTES,SUP_SHA)
    for filename,target,size,wanted,_ in RUNTIME:add(filename,target,"fixed_runtime_source",size,wanted)
    for row in old["references"]:rows.append(dict(row,path="reference/"+row["role"],source=str(repo/row["project_relative_path"])))
    require(len(rows)==36 and sum(row["storage_mode"]=="copied" for row in rows)==34
            and sum(row["storage_mode"]=="external_read_only_reference" for row in rows)==2, "36 roles / 34 copied / 2 references differ")
    require(sum(row["bytes"] for row in rows if row["role"]=="fixed_runtime_source")==579619,"nineteen runtime bytes differ")
    return rows


def fixed_references():
    return [dict(project_relative_path="hf4_c2_stable_f_validation/"+OLD_RUN+"/"+name,
                 bytes=size,sha256=wanted,role=role,storage_mode="external_read_only_reference",copied=False,decoded=False)
            for name,size,wanted,role in NATIVE]


def verify_inputs(root,repo,deadline,*,references_hash,live=True,expected_manifest_sha=None):
    actual_manifest_sha=digest(root/"input_manifest.json",deadline)
    if expected_manifest_sha is not None:
        require(actual_manifest_sha==expected_manifest_sha,"fixed parent input_manifest SHA differs")
    manifest=read(root/"input_manifest.json")
    require(manifest["protocol"]==PROTOCOL and manifest["run_id"]==RUN_ID and len(manifest["files"])==36,"input identity differs")
    fixed=fixed_references()
    reference_rows=[row for row in manifest["files"] if row["storage_mode"]=="external_read_only_reference"]
    require(len(reference_rows)==2,"fixed two external references differ")
    for wanted in fixed:
        matches=[row for row in reference_rows if row["role"]==wanted["role"]]
        require(len(matches)==1 and all(matches[0].get(key)==value for key,value in wanted.items()),"manifest reference differs from fixed source")
        require(extended(matches[0]["source"])==repo/wanted["project_relative_path"],"manifest reference source location differs")
    refs=read(root/"source_refs.json")
    require(refs["protocol"]==PROTOCOL and refs["run_id"]==RUN_ID and refs["references"]==fixed
            and refs["copied"] is False,"source_refs does not equal the fixed manifest references")
    rows=[]
    for row in manifest["files"]:
        gate(deadline)
        if row["storage_mode"]=="copied":
            checked(root/row["path"],row["bytes"],row["sha256"],deadline,within=root)
            if live:checked(row["source"],row["bytes"],row["sha256"],deadline)
            rows.append(dict(path=row["path"],status="verified",bytes=row["bytes"],sha256=row["sha256"]))
        else:
            filename=repo/row["project_relative_path"];safe_path(filename,within=repo)
            require(filename.stat().st_size==row["bytes"],"native reference size changed")
            if references_hash:checked(filename,row["bytes"],row["sha256"],deadline,within=repo)
            rows.append(dict(path=row["project_relative_path"],status="sha_verified" if references_hash else "location_and_size_verified",
                             bytes=row["bytes"],sha256=row["sha256"] if references_hash else None))
    pin_runtime(deadline)
    return dict(protocol=PROTOCOL,run_id=RUN_ID,status="verified",rows=rows,count=36,
                input_manifest_sha256=actual_manifest_sha,fixed_references=fixed,
                native_reference_sha_rechecked=references_hash,live_checked=live,**flags())


class StreamError(RuntimeError):
    def __init__(self,kind,message,*,byte_offset=None,unit_start=None,character_offset=None):
        super().__init__(message);self.kind=kind;self.byte_offset=byte_offset
        self.unit_start=unit_start;self.character_offset=character_offset


def fault(kind,message,*,position=None,unit_start=None,character_offset=None):
    raise StreamError(kind,message,byte_offset=position,unit_start=unit_start,character_offset=character_offset)


_SURROGATE = re.compile("[\\ud800-\\udfff]")
_WHITESPACE = re.compile(br"[ \t\r\n]*")
_STRING_TOKEN = re.compile(br'["\\]')
_STRUCTURAL_TOKEN = re.compile(br'["\\{}\[\]]')
_SCALAR_END = re.compile(br'[ \t\r\n,}\]]')
FIELD_NAMES = ("ph","name","pid","tid","ts","dur","args","cat")
TYPE_NAMES = ("missing","null","boolean","integer","float","string","array","object")
PHASE_NAMES = ("X","B","E","M","i","I","R","C","s","t","f","other","missing","wrong_type")
METADATA_NAMES = ("process_name","process_sort_index","thread_name","thread_sort_index","other","missing","wrong_type")


def typename(value):
    if value is None:return "null"
    if type(value) is bool:return "boolean"
    if type(value) is int:return "integer"
    if type(value) is float:return "float"
    if type(value) is str:return "string"
    if type(value) is list:return "array"
    if type(value) is dict:return "object"
    raise ValueError("unexpected decoded value type")


def strict_decoder(limits):
    def constant(value):fault("strict_configuration","nonfinite constant refused: "+value)
    def integer(value):
        if len(value.lstrip("-"))>256:fault("strict_configuration","integer exceeds 256 absolute digits")
        return int(value)
    def floating(value):
        number=float(value)
        if not math.isfinite(number):fault("strict_configuration","float conversion is not finite")
        return number
    def pairs(items):
        if len(items)>limits["object_keys"]:fault("key_count_limit","object key count exceeds declared limit")
        output={}
        for key,value in items:
            if _SURROGATE.search(key):fault("strict_configuration","decoded key has lone surrogate")
            if len(key.encode("utf-8"))>limits["key_bytes"]:fault("key_length_limit","decoded key UTF8 length exceeds limit")
            if key in output:fault("duplicate_key","decoded-equivalent duplicate object key")
            output[key]=value
        return output
    return json.JSONDecoder(object_pairs_hook=pairs,parse_constant=constant,parse_int=integer,parse_float=floating,strict=True)


def validate_value(value,base_depth,limits,deadline=None):
    """Bounded DFS iterator stack, never one state entry per array element."""
    stack=[(iter((value,)),base_depth)]
    while stack:
        gate(deadline)
        iterator,base=stack[-1]
        try:current=next(iterator)
        except StopIteration:stack.pop();continue
        if type(current) is str:
            if _SURROGATE.search(current):fault("strict_configuration","decoded string has lone surrogate")
        elif type(current) in (dict,list):
            depth=base+1
            if depth>limits["depth"]:fault("depth_limit","total object/array depth exceeds limit")
            if type(current) is dict:
                if len(current)>limits["object_keys"]:fault("key_count_limit","object key count exceeds limit")
                for key in current:
                    if _SURROGATE.search(key):fault("strict_configuration","decoded key has lone surrogate")
                    if len(key.encode("utf-8"))>limits["key_bytes"]:fault("key_length_limit","decoded key length exceeds limit")
                stack.append((iter(current.values()),depth))
            else:stack.append((iter(current),depth))
    return value


class Census:
    def __init__(self,rule,annotations,limits,deadline):
        self.rule=rule;self.annotations=annotations;self.limits=limits;self.deadline=deadline
        self.count=0;self.last_event_end=None;self.retained_text=0;self.threads={};self.samples=[]
        self.phases={key:0 for key in PHASE_NAMES};self.metadata={key:0 for key in METADATA_NAMES}
        self.fields={key:{kind:0 for kind in TYPE_NAMES} for key in FIELD_NAMES}
        self.markers={key:0 for key in annotations}
        self.candidates=dict(exact_event_name=0,generic_name_with_direct_module_arg=0,
            direct_module_arg_any_nonapplication_name=0,exact_name_with_conflicting_module_arg=0,
            application_annotations_excluded=True)
        self.top_values=0
    def retain(self,text):
        size=len(text.encode("utf-8"))
        if size>self.limits["field_text_bytes"]:fault("field_text_limit","retained field/identifier text exceeds limit")
        if self.retained_text+size>self.limits["retained_text_bytes"]:fault("retained_text_limit","cumulative retained text exceeds limit")
        self.retained_text+=size;return text
    def event(self,event,start,end):
        gate(self.deadline)
        if type(event) is not dict:fault("trace_contract","traceEvents entry is not an object",position=start)
        if self.count>=self.limits["event_count"]:fault("event_count_limit","complete event count exceeds limit",position=start)
        index=self.count;self.count+=1
        phase=event.get("ph")
        bucket="missing" if "ph" not in event else "wrong_type" if type(phase) is not str else phase if phase in self.phases and phase not in ("other","missing","wrong_type") else "other"
        self.phases[bucket]+=1
        for field in FIELD_NAMES:self.fields[field][typename(event[field]) if field in event else "missing"]+=1
        name=event.get("name");args=event.get("args")
        if phase=="M":
            bucket="missing" if "name" not in event else "wrong_type" if type(name) is not str else name if name in METADATA_NAMES[:-3] else "other"
            self.metadata[bucket]+=1
        if type(name) is str and name in self.markers:self.markers[name]+=1
        application=type(name) is str and name.startswith("F-TRACE2:")
        if not application:
            exact=type(name) is str and name in self.rule["exact_event_names"]
            direct=type(args) is dict and any(type(args.get(key)) is str and args[key] in self.rule["exact_arg_values"] for key in self.rule["exact_arg_keys"])
            conflicting=type(args) is dict and any(key in args and args[key] not in self.rule["exact_arg_values"] for key in self.rule["exact_arg_keys"])
            if exact:self.candidates["exact_event_name"]+=1
            if direct:self.candidates["direct_module_arg_any_nonapplication_name"]+=1
            if direct and type(name) is str and name in self.rule["native_names_with_module_arg"]:self.candidates["generic_name_with_direct_module_arg"]+=1
            if exact and conflicting:self.candidates["exact_name_with_conflicting_module_arg"]+=1
        pid=event.get("pid");tid=event.get("tid")
        if type(pid) in (str,int,float) and type(tid) in (str,int,float):
            # Canonical typed IDs preserve distinctions and are not Windows IDs.
            key=(typename(pid),str(pid),typename(tid),str(tid))
            if key not in self.threads:
                if len(self.threads)>=self.limits["state_items"]:fault("state_capacity","required trace-thread census table exceeds limit",position=start)
                self.retain(key[1]);self.retain(key[3]);self.threads[key]=0
            self.threads[key]+=1
        if len(self.samples)<self.limits["samples"]:
            sample=dict(array_index=index,start_byte=start,end_byte_exclusive=end,fields={})
            for field in FIELD_NAMES:
                if field not in event:continue
                value=event[field]
                if type(value) in (str,int,float,bool) or value is None:
                    sample["fields"][field]=self.retain(value) if type(value) is str else value
            if type(args) is dict:
                selected={}
                for key in ("name","sort_index",*self.rule["exact_arg_keys"]):
                    if key in args and (type(args[key]) in (str,int,float,bool) or args[key] is None):
                        selected[key]=self.retain(args[key]) if type(args[key]) is str else args[key]
                if selected:sample["fields"]["args_selected"]=selected
            self.samples.append(sample)
        self.last_event_end=end
    def snapshot(self,complete=False):
        return dict(schema="hf-saved-trace-census-1",status="complete" if complete else "partial",event_count=self.count,
            phase_counts=self.phases,field_presence_types=self.fields,metadata_fixed_counts=self.metadata,
            application_name_counts=self.markers,candidate_counts=self.candidates,
            trace_thread_counts=[dict(pid_type=k[0],pid=k[1],tid_type=k[2],tid=k[3],count=v) for k,v in self.threads.items()],
            required_state_items=len(self.threads),state_limit=self.limits["state_items"],retained_text_bytes=self.retained_text,
            top_level_other_values_validated=self.top_values,sample_count=len(self.samples),omitted_sample_count=self.count-len(self.samples),
            sample_set_complete=self.count==len(self.samples),samples_are_deterministic_prefix=True,
            last_validated_event_end_byte=self.last_event_end,intervals_constructed=False,metadata_uniqueness_not_admitted=True,
            candidate_counts_are_diagnostic_only=True,**flags())


class Framer:
    """Byte-oriented C-backed scans; only one <=1MiB value is materialized.

    Regex scanning identifies delimiters, never validates JSON by itself. Each
    complete unit is decoded once with the strict stdlib decoder. The root and
    traceEvents container retain grammar/depth rather than entire value lists.
    """
    def __init__(self,census,limits,deadline):
        self.census=census;self.limits=limits;self.deadline=deadline;self.decoder=strict_decoder(limits)
        self.state="root";self.pos=0;self.root_keys=set();self.current_key=None;self.trace_seen=False
        self.unit=None;self.last_validated_position=0
    def fail(self,kind,message,position=None):fault(kind,message,position=self.pos if position is None else position,unit_start=self.unit["start"] if self.unit else None)
    def begin(self,role,first):
        if role=="key" and first!=34:self.fail("json_grammar","top-level object key must begin with quote")
        if role=="event" and first!=123:self.fail("trace_contract","traceEvents entry must begin with object")
        kind="container" if first in (123,91) else "string" if first==34 else "scalar"
        base=2 if role=="event" else 1
        stack=[first] if kind=="container" else []
        if base+len(stack)>self.limits["depth"]:self.fail("depth_limit","total depth exceeds limit at unit entry")
        self.unit=dict(role=role,kind=kind,start=self.pos,parts=[],size=0,stack=stack,string=kind=="string",escaped=False,base=base)
    def add(self,data,a,b):
        if b<=a:return
        unit=self.unit;size=unit["size"]+b-a
        if size>self.limits["unit_bytes"]:self.fail("unit_size_limit","raw JSON unit exceeds limit",unit["start"]+self.limits["unit_bytes"])
        unit["parts"].append(data[a:b]);unit["size"]=size;self.pos+=b-a
    def finish_unit(self):
        gate(self.deadline);unit=self.unit;raw=b"".join(unit["parts"])
        try:
            text=raw.decode("utf-8","strict")
            value=self.decoder.decode(text)
            validate_value(value,unit["base"],self.limits,self.deadline)
        except json.JSONDecodeError as error:
            fault("json_grammar","strict bounded unit JSON decode failed: "+error.msg,
                position=unit["start"]+len(text[:error.pos].encode("utf-8")),unit_start=unit["start"],character_offset=error.pos)
        except StreamError as error:
            if error.unit_start is None:error.unit_start=unit["start"]
            raise
        role=unit["role"]
        if role=="key":
            if type(value) is not str:self.fail("json_grammar","root key is not a string")
            if len(value.encode("utf-8"))>self.limits["key_bytes"]:self.fail("key_length_limit","root decoded key exceeds limit")
            if value in self.root_keys:self.fail("duplicate_key","duplicate decoded-equivalent root key")
            if len(self.root_keys)>=self.limits["object_keys"]:self.fail("key_count_limit","root key count exceeds limit")
            self.census.retain(value);self.root_keys.add(value);self.current_key=value;self.state="colon"
        elif role=="event":
            self.census.event(value,unit["start"],self.pos);self.state="event_comma"
        else:
            self.census.top_values+=1;self.state="root_comma"
        self.last_validated_position=self.pos;self.unit=None
    def scan_unit(self,data,a):
        unit=self.unit;begin=a;end=len(data)
        if unit["kind"]=="scalar":
            match=_SCALAR_END.search(data,a)
            b=match.start() if match else end
            self.add(data,a,b)
            if match:self.finish_unit()
            return b
        while a<end:
            if unit["escaped"]:
                unit["escaped"]=False;a+=1;continue
            regex=_STRING_TOKEN if unit["string"] else _STRUCTURAL_TOKEN
            match=regex.search(data,a)
            if match is None:a=end;break
            a=match.start();token=data[a];a+=1
            if unit["string"]:
                if token==92:unit["escaped"]=True
                else:
                    unit["string"]=False
                    if unit["kind"]=="string":
                        self.add(data,begin,a);self.finish_unit();return a
            elif token==34:unit["string"]=True
            elif token in (123,91):
                unit["stack"].append(token)
                if unit["base"]+len(unit["stack"])>self.limits["depth"]:self.fail("depth_limit","total depth exceeds limit",self.pos+a-begin-1)
            elif token in (125,93):
                if not unit["stack"] or unit["stack"][-1]!=(123 if token==125 else 91):self.fail("json_grammar","mismatched JSON brackets",self.pos+a-begin-1)
                unit["stack"].pop()
                if not unit["stack"]:
                    self.add(data,begin,a);self.finish_unit();return a
            # A backslash outside strings remains part of the unit; strict
            # decoder later rejects it, without accepting a temporary prefix.
        self.add(data,begin,a);return a
    def feed(self,data):
        a=0;end=len(data)
        while a<end:
            gate(self.deadline)
            if self.unit is not None:
                a=self.scan_unit(data,a);continue
            match=_WHITESPACE.match(data,a);b=match.end();self.pos+=b-a;a=b
            if a==end:break
            token=data[a]
            if self.state=="root":
                if token!=123:self.fail("trace_contract","document root must be an object")
                if self.limits["depth"]<1:self.fail("depth_limit","root exceeds depth limit")
                self.state="key_or_end"
            elif self.state in ("key_or_end","key_required"):
                if token==125 and self.state=="key_or_end":
                    if not self.trace_seen:self.fail("trace_contract","traceEvents root key missing")
                    self.state="done"
                else:
                    self.begin("key",token);self.add(data,a,a+1);a+=1;continue
            elif self.state=="colon":
                if token!=58:self.fail("json_grammar","root key requires colon")
                self.state="trace_start" if self.current_key=="traceEvents" else "value"
            elif self.state=="trace_start":
                if token!=91:self.fail("trace_contract","traceEvents must be an array")
                if self.limits["depth"]<2:self.fail("depth_limit","traceEvents container exceeds depth limit")
                self.trace_seen=True;self.state="event_or_end"
            elif self.state in ("event_or_end","event_required"):
                if token==93 and self.state=="event_required":self.fail("json_grammar","trailing comma in traceEvents")
                if token==93 and self.state=="event_or_end":self.state="root_comma"
                else:
                    self.begin("event",token);self.add(data,a,a+1);a+=1;continue
            elif self.state=="value":
                self.begin("top",token);self.add(data,a,a+1);a+=1;continue
            elif self.state=="event_comma":
                if token==44:self.state="event_required"
                elif token==93:self.state="root_comma"
                else:self.fail("json_grammar","event requires comma or closing array")
            elif self.state=="root_comma":
                if token==44:self.state="key_required"
                elif token==125:self.state="done"
                else:self.fail("json_grammar","root member requires comma or closing object")
            elif self.state=="done":self.fail("tail","nonwhitespace trailing bytes or second document")
            else:self.fail("json_grammar","unknown framing state")
            a+=1;self.pos+=1
    def final(self):
        gate(self.deadline)
        if self.unit and self.unit["kind"]=="scalar":self.finish_unit()
        if self.unit or self.state!="done" or not self.trace_seen:self.fail("json_grammar","truncated JSON document or unit")
        return True
    def positions(self):
        return dict(framer_consumed_bytes=self.pos,last_validated_unit_end_byte=self.last_validated_position,
            last_validated_event_end_byte=self.census.last_event_end,
            incomplete_unit_start_byte=self.unit["start"] if self.unit else None,
            incomplete_unit_bytes=self.unit["size"] if self.unit else 0,grammar_state=self.state)


def stream_gzip(gzip_module,raw_factory,cap,deadline,rule,annotations,*,minimum_remaining=0.,on_state=None,
                limits=None,chunk=CHUNK,expected_prefix=None,checkpoint=None,progress_stride=16*1024**2):
    """Same reader/framer/strict decoder/lifecycle path for all controls and real input."""
    limits=dict(PARSER_LIMITS if limits is None else limits)
    require(type(cap) is int and cap>=0 and type(chunk) is int and 0<chunk<=CHUNK,"invalid stream cap/request")
    census=Census(rule,annotations,limits,deadline);framer=Framer(census,limits,deadline)
    utf8=codecs.getincrementaldecoder("utf-8")("strict")
    result=dict(schema="hf-saved-gzip-stream-1",status="not_returned",cap_bytes=cap,max_countable_bytes=cap+1,
        request_limit_bytes=chunk,reader_type="gzip._GzipReader",buffered_reader=False,returned_bytes=0,
        exact_body_bytes=None,body_bytes_lower_bound=0,full_body_sha256=None,prefix_sha256=hashlib.sha256(b"").hexdigest(),
        prefix_definition="all and only decompressed bytes returned by completed read calls and counted here",
        eof_verified=False,crc_isize_verified=False,utf8_final_verified=False,strict_json_complete=False,
        crc_scope="all_member_body_crc32_and_isize",header_fhcrc_verified=False,header_fhcrc_scope="not_checked_by_fixed_stdlib",
        raw_open_attempts=0,reader_instances=0,read_attempts=0,close_attempts=dict(reader=0,raw=0),
        requests=dict(total=0,min=None,max=None,last=None),returns=dict(total=0,min=None,max=None,last=None,nonempty=0,empty=0),
        last_read=None,prefix_crosscheck=None,prior_prefix_bytes=expected_prefix[0] if expected_prefix else None,
        prior_prefix_expected_sha256=expected_prefix[1] if expected_prefix else None,
        first_error=None,first_error_kind=None,secondary_errors=[],closed=False,limits=limits,
        progress_updates=0,started_monotonic=time.monotonic(),**flags())
    value=hashlib.sha256();prefix=hashlib.sha256();raw=reader=None;next_progress=progress_stride
    def summary_count():
        result.update(framer.positions());result["pending_unconsumed_suffix_bytes"]=result["returned_bytes"]-framer.pos
        result["census"]=census.snapshot(result["strict_json_complete"] and result["eof_verified"] and result["first_error"] is None)
    def aggregate(target,size):
        target["total"]+=size;target["min"]=size if target["min"] is None else min(target["min"],size)
        target["max"]=size if target["max"] is None else max(target["max"],size);target["last"]=size
    try:
        gate(deadline)
        result["raw_open_attempts"]=1;raw=raw_factory();reader=gzip_module._GzipReader(raw);result["reader_instances"]=1
        summary_count()
        if on_state:on_state(result) # Last potentially slow checkpoint before admission.
        while True:
            gate(deadline)
            if result["read_attempts"]==0:
                remaining=deadline-time.monotonic() if deadline is not None else None
                if remaining is not None and remaining<minimum_remaining:raise BudgetError("insufficient activity remains before first actual gzip read")
                result["entry_admission"]=dict(remaining_seconds=remaining,minimum_remaining_seconds=minimum_remaining)
            request=min(chunk,cap+1-result["returned_bytes"])
            require(request>0,"read after cap+1 refused")
            begin=time.monotonic();result["read_attempts"]+=1;aggregate(result["requests"],request)
            result["last_read"]=dict(index=result["read_attempts"],request_bytes=request,status="not_returned",returned_bytes=None,start_monotonic=begin)
            try:data=reader.read(request)
            except BaseException:
                result["last_read"].update(status="raised",end_monotonic=time.monotonic());raise
            require(type(data) is bytes and len(data)<=request,"reader exceeded bounded positive request")
            result["last_read"].update(status="returned" if data else "eof",returned_bytes=len(data),end_monotonic=time.monotonic())
            aggregate(result["returns"],len(data));result["returns"]["nonempty" if data else "empty"]+=1
            if not data:
                gate(deadline);result.update(eof_verified=True,crc_isize_verified=True)
                try:utf8.decode(b"",final=True)
                except UnicodeDecodeError as error:fault("utf8","truncated UTF8 codepoint at final flush",unit_start=framer.unit["start"] if framer.unit else None)
                result["utf8_final_verified"]=True;framer.final();result["strict_json_complete"]=True
                if expected_prefix and result["prefix_crosscheck"] is not True:fault("source_consistency","complete new body did not reach the old proven prefix")
                result.update(status="stream_complete",exact_body_bytes=result["returned_bytes"],full_body_sha256=value.hexdigest());break
            before=result["returned_bytes"]
            # Count EVERY returned byte and hash the old prefix boundary before
            # any UTF8/framing/progress operation can raise.
            value.update(data);result["returned_bytes"]+=len(data)
            result.update(body_bytes_lower_bound=result["returned_bytes"],prefix_sha256=value.hexdigest())
            if expected_prefix and before<expected_prefix[0]:
                portion=data[:min(len(data),expected_prefix[0]-before)];prefix.update(portion)
                if result["returned_bytes"]>=expected_prefix[0]:
                    result["prior_prefix_actual_sha256"]=prefix.hexdigest()
                    result["prefix_crosscheck"]=prefix.hexdigest()==expected_prefix[1]
                    if result["prefix_crosscheck"] is not True:fault("source_consistency","old returned-prefix SHA crosscheck failed")
            gate(deadline)
            if result["returned_bytes"]>cap:fault("body_over_cap","returned body crossed the diagnostic cap+1 boundary")
            pending=len(utf8.getstate()[0])
            try:decoded=utf8.decode(data,final=False)
            except UnicodeDecodeError as error:
                fault("utf8","strict incremental UTF8 decode failed",position=before-pending+error.start,character_offset=None)
            if framer.pos==0 and decoded.startswith("\ufeff"):fault("strict_configuration","leading BOM refused",position=0)
            # Reencoding completed strict UTF8 characters preserves the exact
            # original bytes, while pending multibyte bytes stay in the decoder.
            framer.feed(decoded.encode("utf-8"))
            if checkpoint:checkpoint(result,census,framer)
            if result["returned_bytes"]>=next_progress:
                if result["progress_updates"]>=limits["progress_updates"]:fault("progress_capacity","progress update count exceeds declared limit")
                result["progress_updates"]+=1;next_progress+=progress_stride;summary_count()
                if on_state:on_state(result)
    except BaseException as error:
        result["first_error"]=error_record(error)
        kind=error.kind if isinstance(error,StreamError) else "container_integrity" if isinstance(error,(gzip_module.BadGzipFile,EOFError,gzip_module.zlib.error)) else "resource" if isinstance(error,BudgetError) else "io_or_recording"
        result.update(status="partial",first_error_kind=kind)
    finally:
        for label,handle in (("reader",reader),("raw",raw)):
            if handle is None:continue
            result["close_attempts"][label]+=1
            try:handle.close() # No read/EOF completion is performed by close.
            except BaseException as error:
                detail=dict(error_record(error),operation=label+".close")
                if result["first_error"] is None:result.update(first_error=detail,first_error_kind="close_io",status="partial")
                else:result["secondary_errors"].append(detail)
        result["closed"]=not result["secondary_errors"] and result["first_error_kind"]!="close_io"
        if result["first_error"] is not None:
            result.update(exact_body_bytes=None,full_body_sha256=None,strict_json_complete=False)
            # EOF/container CRC facts may be true on a later grammar/config
            # failure; they do not grant exact/full-body diagnostic qualification.
        summary_count();result["finished_monotonic"]=time.monotonic()
    return result,census.samples


def progress_snapshot(value,limits=PARSER_LIMITS):
    census=value["census"]
    row=dict(protocol=PROTOCOL,run_id=RUN_ID,returned_bytes=value["returned_bytes"],read_attempts=value["read_attempts"],
        prefix_crosscheck=value["prefix_crosscheck"],progress_updates=value["progress_updates"],
        framer_consumed_bytes=value["framer_consumed_bytes"],last_validated_event_end_byte=value["last_validated_event_end_byte"],
        incomplete_unit_start_byte=value["incomplete_unit_start_byte"],incomplete_unit_bytes=value["incomplete_unit_bytes"],
        event_count=census["event_count"],required_state_items=census["required_state_items"],sample_count=census["sample_count"],
        omitted_sample_count=census["omitted_sample_count"],phase_counts=census["phase_counts"],
        candidate_counts=census["candidate_counts"],status="in_progress",**flags())
    if len(encode_json(row))>limits["progress_bytes"]:
        fault("progress_capacity","progress snapshot exceeds declared byte limit")
    return row


def capacity_admit(generated_bytes,root_files,new_bytes,limits=PARSER_LIMITS,*,new_files=1):
    if new_bytes>limits["generated_file_bytes"]:fault("output_capacity","new generated file exceeds byte limit")
    if generated_bytes+new_bytes>limits["generated_bytes"]:fault("output_capacity","total generated bytes exceed limit")
    if root_files+new_files>limits["root_files"]:fault("output_capacity","new root file count exceeds limit")


def log_admit(rows,byte_count,new_bytes,limits=PARSER_LIMITS):
    if rows+1>limits["log_rows"] or byte_count+new_bytes>limits["log_bytes"]:
        fault("log_capacity","stage event log exceeds rows/bytes limit")


def generated_inventory(root,*,allow_existing_violations=False):
    global INVENTORY_CACHE
    count=0;total=0;files={};violations=[]
    if INVENTORY_CACHE is not None:INVENTORY_CACHE["complete"]=False
    if root is not None and root.exists():
        for filename in walk_files(root,WRITE_DEADLINE):
            count+=1;relative=filename.relative_to(root).as_posix();size=filename.stat().st_size;files[relative]=size
            if not relative.startswith(("aux/","provenance/")):
                total+=size
                if size>PARSER_LIMITS["generated_file_bytes"]:violations.append(dict(path=relative,kind="single_generated_file",bytes=size))
            if relative.startswith(("events/","logs/")):
                if size>PARSER_LIMITS["log_bytes"]:violations.append(dict(path=relative,kind="log_bytes",bytes=size))
                else:
                    data=filename.read_bytes();rows=data.count(b"\n")+(1 if data and not data.endswith(b"\n") else 0)
                    if rows>PARSER_LIMITS["log_rows"]:violations.append(dict(path=relative,kind="log_rows",rows=rows))
            if count>PARSER_LIMITS["root_files"]:fault("output_capacity","root exceeds hard file count; complete inventory unavailable")
    gate(WRITE_DEADLINE) # Final stat/log read must finish inside the original deadline.
    INVENTORY_CACHE=dict(files=files,generated_bytes=total,root_files=count,violations=violations,complete=True)
    if total>PARSER_LIMITS["generated_bytes"]:fault("output_capacity","existing generated total exceeds hard cap")
    if violations and not allow_existing_violations:fault("output_capacity","existing per-file/log capacity violation")
    return count,total


def admit_write(filename,new_bytes,*,append=False):
    if EVIDENCE_ROOT is None:return
    relative=Path(filename).relative_to(EVIDENCE_ROOT).as_posix();terminal=relative in TERMINAL_PATHS
    count,total=generated_inventory(EVIDENCE_ROOT,allow_existing_violations=terminal)
    limits=PARSER_LIMITS if terminal else dict(PARSER_LIMITS,generated_bytes=PARSER_LIMITS["generated_bytes"]-TERMINAL_RESERVE_BYTES,
        root_files=PARSER_LIMITS["root_files"]-TERMINAL_RESERVE_FILES)
    capacity_admit(total,count,new_bytes,limits,new_files=0 if append else 1)


def oracle(body,limits,rule,annotations):
    value=strict_decoder(limits).decode(body.decode("utf-8"));validate_value(value,0,limits)
    require(type(value) is dict and type(value.get("traceEvents")) is list,"positive oracle root/array differs")
    events=value["traceEvents"];require(all(type(event) is dict for event in events),"oracle event object differs")
    phases={key:0 for key in PHASE_NAMES}
    for event in events:
        ph=event.get("ph")
        key="missing" if "ph" not in event else "wrong_type" if type(ph) is not str else ph if ph in PHASE_NAMES[:-3] else "other"
        phases[key]+=1
    names={key:sum(type(event.get("name")) is str and event["name"]==key for event in events) for key in annotations}
    nonapplication=[event for event in events if not (type(event.get("name")) is str and event["name"].startswith("F-TRACE2:"))]
    def direct(event):
        args=event.get("args")
        return type(args) is dict and any(type(args.get(k)) is str and args[k] in rule["exact_arg_values"] for k in rule["exact_arg_keys"])
    candidate=dict(exact_event_name=sum(type(e.get("name")) is str and e["name"] in rule["exact_event_names"] for e in nonapplication),
        generic_name_with_direct_module_arg=sum(type(e.get("name")) is str and e["name"] in rule["native_names_with_module_arg"] and direct(e) for e in nonapplication),
        direct_module_arg_any_nonapplication_name=sum(direct(e) for e in nonapplication),
        exact_name_with_conflicting_module_arg=sum(type(e.get("name")) is str and e["name"] in rule["exact_event_names"] and type(e.get("args")) is dict and any(k in e["args"] and e["args"][k] not in rule["exact_arg_values"] for k in rule["exact_arg_keys"]) for e in nonapplication),
        application_annotations_excluded=True)
    metadata={key:sum(e.get("ph")=="M" and ("missing" if "name" not in e else "wrong_type" if type(e["name"]) is not str else e["name"] if e["name"] in METADATA_NAMES[:-3] else "other")==key for e in events) for key in METADATA_NAMES}
    fields={field:{kind:sum((typename(e[field]) if field in e else "missing")==kind for e in events) for kind in TYPE_NAMES} for field in FIELD_NAMES}
    return dict(event_count=len(events),phase_counts=phases,application_name_counts=names,
        candidate_counts=candidate,metadata_fixed_counts=metadata,field_presence_types=fields,other_top_values=len(value)-1)


class SyntheticRaw(io.BytesIO):
    def __init__(self,data,*,read_error=False,close_error=False):
        super().__init__(data);self.read_error=read_error;self.close_error=close_error;self.close_calls=0
    def read(self,size=-1):
        if self.read_error:raise OSError("synthetic raw read failure")
        return super().read(size)
    def close(self):
        self.close_calls+=1
        super().close()
        if self.close_error:raise OSError("synthetic raw close failure")


def control_cases(gzip_module,deadline,rule,annotations):
    groups=[];fixture_bytes=0;subcases=0;last_result=None
    try:
        def group(name):
            require(name==CONTROL_GROUPS[len(groups)],"control group order differs")
            row=dict(name=name,status="running",cases=[]);groups.append(row);return row
        def case(group,name,body,expected="stream_complete",*,overrides=None,chunk=3,cap=None,
                 encoded=None,minimum_remaining=0.,local_deadline=None,raw_flags=None,on_state=None,checkpoint=None,progress_stride=16*1024**2,expected_prefix=None):
            nonlocal fixture_bytes,subcases,last_result
            gate(deadline);fixture_bytes+=len(body);subcases+=1
            require(fixture_bytes<=65536,"aggregate raw control fixtures exceed 64KiB")
            limits=dict(PARSER_LIMITS);limits.update(overrides or {})
            compressed=gzip_module.compress(body,mtime=0) if encoded is None else encoded
            stream_deadline=deadline if local_deadline is None else min(deadline,local_deadline)
            result,samples=stream_gzip(gzip_module,lambda:SyntheticRaw(compressed,**(raw_flags or {})),
                len(body)+8 if cap is None else cap,stream_deadline,rule,annotations,
                minimum_remaining=minimum_remaining,limits=limits,chunk=chunk,on_state=on_state,checkpoint=checkpoint,progress_stride=progress_stride,expected_prefix=expected_prefix)
            last_result=result
            actual=result["status"] if result["first_error_kind"] is None else result["first_error_kind"]
            if actual!=expected:
                mismatch=StreamError("control_failure","same stream control outcome differs: "+name+" actual="+str(actual))
                mismatch.original_first_error=result["first_error"];mismatch.original_first_error_kind=result["first_error_kind"]
                raise mismatch
            require(result["raw_open_attempts"]==result["reader_instances"]==1 and result["close_attempts"]==dict(reader=1,raw=1),"control lifecycle attempts differ")
            require(result["closed"] is (not bool((raw_flags or {}).get("close_error"))),"control close-state differs")
            require(result["returned_bytes"]==result["returns"]["total"] and result["returned_bytes"]<=result["cap_bytes"]+1
                and (result["requests"]["max"] is None or result["requests"]["max"]<=chunk),"control read bound differs")
            expected_oracle=None
            if expected=="stream_complete":
                expected_oracle=oracle(body,limits,rule,annotations)
                require(result["eof_verified"] and result["crc_isize_verified"] and result["utf8_final_verified"] and result["strict_json_complete"],"positive full-stream facts differ")
                require(result["exact_body_bytes"]==len(body) and result["full_body_sha256"]==hashlib.sha256(body).hexdigest(),"positive exact bytes/SHA differ")
                require(all(result["census"][key]==expected_oracle[key] for key in ("event_count","phase_counts","application_name_counts","candidate_counts","metadata_fixed_counts","field_presence_types")),"independent census oracle differs")
                require(result["census"]["top_level_other_values_validated"]==expected_oracle["other_top_values"],"oracle top-value count differs")
                require(result["census"]["omitted_sample_count"]==expected_oracle["event_count"]-len(samples),"omitted sample count differs")
            else:
                require(result["exact_body_bytes"] is None and result["full_body_sha256"] is None and not result["strict_json_complete"],"negative control claims complete qualification")
            row=dict(name=name,status="pass",expected=expected,synthetic=True,raw_fixture_bytes=len(body),
                raw_fixture_sha256=hashlib.sha256(body).hexdigest(),compressed_fixture_bytes=len(compressed),
                compressed_fixture_sha256=hashlib.sha256(compressed).hexdigest(),oracle=expected_oracle,result=result,
                sample_array_indices=[sample["array_index"] for sample in samples])
            group["cases"].append(row);return result
        def checks(group,name,fn,expected):
            try:fn()
            except StreamError as error:actual=error.kind
            else:actual="pass"
            require(actual==expected,"shared capacity branch differs: "+name)
            group["cases"].append(dict(name=name,status="pass",expected=expected,actual=actual,synthetic=True,raw_fixture_bytes=0))
        basic=b'{"traceEvents":[]}'
        g=group("legal_root_positions")
        case(g,"empty",basic,chunk=1)
        case(g,"trace_first",b'{"traceEvents":[{"ph":"X","name":"A","ts":1,"dur":2}],"other":{"a":[1,true,null]}}')
        case(g,"trace_last",b'{"first":false,"middle":[{"ok":null}],"traceEvents":[{}]}')
        selected_key=rule["exact_arg_keys"][0]
        candidate_events=[dict(ph="X",name=rule["exact_event_names"][0]),
            dict(ph="B",name=rule["native_names_with_module_arg"][0],args={selected_key:rule["module"]}),
            dict(ph="E",name=rule["exact_event_names"][1],args={selected_key:"conflicting"}),
            dict(ph="C",name="arbitrary_other",args={selected_key:rule["module"]}),
            dict(ph="M",name="process_name",args=dict(name="/host:CPU")),dict(ph="M",name=None),dict(ph="M"),
            dict(ph=[],name="wrong_phase_type"),{}]+[dict(ph="X",name=name,args={selected_key:rule["module"]}) for name in annotations]
        case(g,"fixed_candidates_metadata_types",json.dumps(dict(traceEvents=candidate_events),ensure_ascii=False).encode("utf-8"))
        g["status"]="pass"
        g=group("utf8_keys_unicode")
        case(g,"multibyte_and_keys",'{"é":["中"],"traceEvents":[{"name":"𝄞é"}]}'.encode("utf-8"),chunk=1)
        case(g,"legal_surrogate_pair",b'{"traceEvents":[{"name":"\\ud834\\udd1e"}]}',chunk=1)
        g["status"]="pass"
        g=group("string_escapes")
        escaped=json.dumps(dict(traceEvents=[dict(name='quote" slash\\ brackets{}[], : newline\n')]),ensure_ascii=False).encode("utf-8")
        case(g,"escaped_delimiters",escaped,chunk=1);g["status"]="pass"
        g=group("scalar_values")
        case(g,"numeric_boolean_null",b'{"a":-12.3e-2,"b":true,"c":null,"d":false,"traceEvents":[{"args":{"n":0,"v":-0.0,"yes":true}}]}',chunk=1);g["status"]="pass"
        g=group("multi_member")
        body='{ "traceEvents":[{"name":"中"}],"done":true }'.encode("utf-8");split=body.index("中".encode("utf-8"))+1
        encoded=gzip_module.compress(body[:split],mtime=0)+gzip_module.compress(body[split:split+1],mtime=0)+gzip_module.compress(body[split+1:],mtime=0)
        case(g,"three_members_across_codepoint",body,encoded=encoded,chunk=1);g["status"]="pass"
        g=group("body_cap")
        case(g,"exact_cap",basic,cap=len(basic),chunk=4)
        result=case(g,"cap_plus_one",basic,"body_over_cap",cap=len(basic)-1,chunk=4)
        require(result["returned_bytes"]==len(basic) and not result["eof_verified"],"over-cap did not stop at exact cap+1")
        g["status"]="pass"
        g=group("crc_trailer")
        encoded=bytearray(gzip_module.compress(basic,mtime=0));encoded[-8]^=1
        case(g,"bad_body_crc",basic,"container_integrity",encoded=bytes(encoded),chunk=2)
        case(g,"trailer_truncated",basic,"container_integrity",encoded=gzip_module.compress(basic,mtime=0)[:-4],chunk=2);g["status"]="pass"
        g=group("utf8_configuration")
        case(g,"invalid_utf8",b'{"traceEvents":[{"name":"\xff"}]}',"utf8",chunk=1)
        case(g,"truncated_utf8",basic+b' \xe2\x82',"utf8",chunk=1)
        case(g,"split_bom",b'\xef\xbb\xbf'+basic,"strict_configuration",chunk=1)
        case(g,"lone_high_surrogate",b'{"traceEvents":[{"name":"\\ud800"}]}',"strict_configuration",chunk=1)
        case(g,"lone_low_key",b'{"traceEvents":[{"\\udfff":0}]}',"strict_configuration",chunk=1);g["status"]="pass"
        g=group("json_grammar")
        for name,body in (("wrong_bracket",b'{"traceEvents":[{]}'),("missing_comma",b'{"traceEvents":[{}{}]}'),("trailing_comma",b'{"traceEvents":[{},]}'),("truncated_object",b'{"traceEvents":[{"a":1'),("bad_colon",b'{"traceEvents" []}')):
            case(g,name,body,"json_grammar")
        g["status"]="pass"
        g=group("tail")
        case(g,"four_json_whitespaces",basic+b' \t\r\n',chunk=1)
        case(g,"trailing_garbage",basic+b'x',"tail",chunk=1)
        case(g,"second_document",basic+b'{}',"tail",chunk=1);g["status"]="pass"
        g=group("duplicate_keys")
        case(g,"root_duplicate",b'{"traceEvents":[],"traceEvents":[]}',"duplicate_key")
        case(g,"root_escaped_equivalent",b'{"traceEvents":[],"trace\\u0045vents":[]}',"duplicate_key")
        case(g,"nested_duplicate",b'{"traceEvents":[{"args":{"x":1,"x":2}}]}',"duplicate_key")
        case(g,"escaped_equivalent",b'{"traceEvents":[{"x":1,"\\u0078":2}]}',"duplicate_key");g["status"]="pass"
        g=group("numeric_configuration")
        for name,number in (("nan",b'NaN'),("infinity",b'Infinity'),("negative_infinity",b'-Infinity'),("overflow",b'1e999')):
            case(g,name,b'{"traceEvents":[{"v":'+number+b'}]}',"strict_configuration",chunk=1)
        case(g,"integer_256",b'{"traceEvents":[{"v":'+b'9'*256+b'}]}',chunk=1)
        case(g,"negative_integer_256",b'{"traceEvents":[{"v":-'+b'9'*256+b'}]}',chunk=1)
        case(g,"integer_257",b'{"traceEvents":[{"v":'+b'9'*257+b'}]}',"strict_configuration",chunk=1);g["status"]="pass"
        g=group("root_trace_contract")
        for name,body,expected in (("root_array",b'[]',"trace_contract"),("missing_trace",b'{}',"trace_contract"),("wrong_trace_type",b'{"traceEvents":{}}',"trace_contract"),("duplicate_trace",b'{"traceEvents":[],"traceEvents":[]}',"duplicate_key"),("nonobject_event",b'{"traceEvents":[0]}',"trace_contract")):
            case(g,name,body,expected)
        g["status"]="pass"
        g=group("unit_key_limits")
        unit=b'{"name":"abcdefghijklmnop"}';body=b'{"traceEvents":['+unit+b']}'
        case(g,"unit_exact",body,overrides=dict(unit_bytes=len(unit)))
        case(g,"unit_over",body,"unit_size_limit",overrides=dict(unit_bytes=len(unit)-1))
        case(g,"other_top_unit_exact",b'{"traceEvents":[],"v":"abcdefghijklmnop"}',overrides=dict(unit_bytes=18))
        case(g,"other_top_unit_over",b'{"traceEvents":[],"v":"abcdefghijklmnopq"}',"unit_size_limit",overrides=dict(unit_bytes=18))
        case(g,"key_length_exact",b'{"traceEvents":[],"abcdefghijk":0}',overrides=dict(key_bytes=11))
        case(g,"utf8_key_length_exact",json.dumps({"traceEvents":[],"éééééa":0},ensure_ascii=False).encode("utf-8"),overrides=dict(key_bytes=11))
        case(g,"utf8_key_length_over",json.dumps({"traceEvents":[],"éééééé":0},ensure_ascii=False).encode("utf-8"),"key_length_limit",overrides=dict(key_bytes=11))
        case(g,"key_length_over",b'{"traceEvents":[],"abcdefghijkl":0}',"key_length_limit",overrides=dict(key_bytes=11))
        case(g,"nested_key_count_exact",b'{"traceEvents":[{"a":1,"b":2}]}',overrides=dict(object_keys=2))
        case(g,"nested_key_count_over",b'{"traceEvents":[{"a":1,"b":2,"c":3}]}',"key_count_limit",overrides=dict(object_keys=2))
        case(g,"root_key_count_over",b'{"traceEvents":[],"a":1,"b":2}',"key_count_limit",overrides=dict(object_keys=2));g["status"]="pass"
        g=group("depth_event_state_limits")
        case(g,"depth_exact_root_array_event",b'{"traceEvents":[{}]}',overrides=dict(depth=3))
        case(g,"depth_over",b'{"traceEvents":[{"args":{}}]}',"depth_limit",overrides=dict(depth=3))
        case(g,"event_count_exact",b'{"traceEvents":[{},{}]}',overrides=dict(event_count=2))
        case(g,"event_count_over",b'{"traceEvents":[{},{},{}]}',"event_count_limit",overrides=dict(event_count=2))
        case(g,"state_exact",b'{"traceEvents":[{"pid":1,"tid":1},{"pid":1,"tid":2}]}',overrides=dict(state_items=2))
        case(g,"state_over",b'{"traceEvents":[{"pid":1,"tid":1},{"pid":1,"tid":2},{"pid":1,"tid":3}]}',"state_capacity",overrides=dict(state_items=2));g["status"]="pass"
        g=group("lifecycle_record_capacity")
        prefix_end=13
        result=case(g,"prefix_crosses_return_boundary",basic,chunk=8,expected_prefix=(prefix_end,hashlib.sha256(basic[:prefix_end]).hexdigest()))
        require(result["prefix_crosscheck"] is True,"same-stream prefix crosscheck not performed")
        result=case(g,"prefix_mismatch_before_utf8",b'\xff'+basic,"source_consistency",chunk=8,expected_prefix=(1,"0"*64))
        require(result["returned_bytes"]==8 and result["prefix_crosscheck"] is False and result["framer_consumed_bytes"]==0,"prefix mismatch did not account all returned bytes before stopping")
        result=case(g,"entry_insufficient",basic,"resource",minimum_remaining=20.,local_deadline=time.monotonic()+10.)
        require(result["read_attempts"]==0,"entry stop performed a read")
        def deadline_fault(*args):raise BudgetError("synthetic shared-deadline checkpoint")
        case(g,"deadline_checkpoint",basic,"resource",checkpoint=deadline_fault,chunk=8)
        result=case(g,"raw_io_and_close_first_error",basic,"io_or_recording",raw_flags=dict(read_error=True,close_error=True))
        require(result["first_error"]["type"]=="OSError" and len(result["secondary_errors"])==1 and result["secondary_errors"][0]["operation"]=="raw.close","first read/secondary close error contract differs")
        case(g,"successful_body_close_failure",basic,"close_io",raw_flags=dict(close_error=True))
        case(g,"progress_update_over",basic,"progress_capacity",overrides=dict(progress_updates=0),progress_stride=16)
        result=case(g,"sample_prefix_omission",b'{"traceEvents":[{},{},{},{}]}',overrides=dict(samples=2))
        require(result["census"]["event_count"]==4 and result["census"]["omitted_sample_count"]==2 and result["census"]["sample_set_complete"] is False,"sample retention stopped census")
        case(g,"field_text_exact",b'{"traceEvents":[{"name":"abcdefghijk"}]}',overrides=dict(field_text_bytes=11))
        case(g,"field_text_over",b'{"traceEvents":[{"name":"abcdefghijkl"}]}',"field_text_limit",overrides=dict(field_text_bytes=11))
        case(g,"retained_text_exact",b'{"traceEvents":[{"name":"abcd"}]}',overrides=dict(retained_text_bytes=15))
        case(g,"retained_text_over",b'{"traceEvents":[{"name":"abcd"},{"name":"abcd"}]}',"retained_text_limit",overrides=dict(retained_text_bytes=15))
        empty=Census(rule,annotations,PARSER_LIMITS,deadline).snapshot(False)
        progress_value=dict(census=empty,returned_bytes=0,read_attempts=0,prefix_crosscheck=None,progress_updates=0,
            framer_consumed_bytes=0,last_validated_event_end_byte=None,incomplete_unit_start_byte=None,incomplete_unit_bytes=0)
        row=progress_snapshot(progress_value);size=len(encode_json(row))
        checks(g,"progress_bytes_exact",lambda:progress_snapshot(progress_value,dict(PARSER_LIMITS,progress_bytes=size)),"pass")
        checks(g,"progress_bytes_over",lambda:progress_snapshot(progress_value,dict(PARSER_LIMITS,progress_bytes=size-1)),"progress_capacity")
        small=dict(PARSER_LIMITS,generated_file_bytes=10,generated_bytes=20,root_files=2,log_rows=2,log_bytes=10)
        checks(g,"output_single_exact",lambda:capacity_admit(0,0,10,small),"pass")
        checks(g,"output_single_over",lambda:capacity_admit(0,0,11,small),"output_capacity")
        checks(g,"output_total_exact",lambda:capacity_admit(10,0,10,small),"pass")
        checks(g,"output_total_over",lambda:capacity_admit(11,0,10,small),"output_capacity")
        checks(g,"root_files_exact",lambda:capacity_admit(0,1,1,small),"pass")
        checks(g,"root_files_over",lambda:capacity_admit(0,2,1,small),"output_capacity")
        checks(g,"log_rows_bytes_exact",lambda:log_admit(1,5,5,small),"pass")
        checks(g,"log_rows_over",lambda:log_admit(2,0,1,small),"log_capacity")
        checks(g,"log_bytes_over",lambda:log_admit(0,6,5,small),"log_capacity")
        g["status"]="pass"
        require(len(groups)==16 and all(g["status"]=="pass" for g in groups),"16 control groups not complete")
        return dict(protocol=PROTOCOL,run_id=RUN_ID,status="pass",count=16,subcase_count=sum(len(g["cases"]) for g in groups),
            stream_case_count=subcases,fixture_raw_bytes=fixture_bytes,fixture_raw_limit=65536,synthetic=True,cases=groups,
            same_stream_function="stream_gzip",positive_oracle="strict stdlib complete tiny fixture decode + independent fixed-bin counts",
            production_limits=PARSER_LIMITS,production_cap_bytes=CAP,controls_do_not_change_production_limits=True)
    
    except BaseException as error:
        error.control_state=dict(protocol=PROTOCOL,run_id=RUN_ID,status="partial",count=len(groups),cases=groups,
            fixture_raw_bytes=fixture_bytes,fixture_raw_limit=65536,stream_case_count=subcases,
            last_stream_result=last_result,synthetic=True,first_error=error_record(error),production_limits=PARSER_LIMITS)
        raise


def verify_count(result):
    require(type(result) is dict and result["reader_type"]=="gzip._GzipReader" and result["buffered_reader"] is False
        and result["cap_bytes"]==CAP and result["max_countable_bytes"]==CAP+1 and result["request_limit_bytes"]==CHUNK
        and result["limits"]==PARSER_LIMITS,"real reader/parser contract differs")
    require(result["status"] in ("stream_complete","partial","not_returned"),"unknown saved stream outcome")
    total=result["returned_bytes"]
    require(type(total) is int and 0<=total<=CAP+1 and total==result["body_bytes_lower_bound"]==result["returns"]["total"],"saved returned count differs")
    require(type(result["read_attempts"]) is int and result["read_attempts"]==result["returns"]["empty"]+result["returns"]["nonempty"]+(1 if result["last_read"] and result["last_read"]["status"] in ("raised","not_returned") else 0),"saved read aggregates differ")
    for key in ("requests","returns"):
        summary=result[key]
        if summary["max"] is not None:require(0<=summary["min"]<=summary["max"]<=CHUNK,"read aggregate bound differs")
    if result["requests"]["min"] is not None:require(result["requests"]["min"]>0,"nonpositive request recorded")
    require(result["requests"]["total"]>=total and result["framer_consumed_bytes"]<=total
        and result["pending_unconsumed_suffix_bytes"]==total-result["framer_consumed_bytes"],"returned/framing positions differ")
    require(result["crc_scope"]=="all_member_body_crc32_and_isize" and result["header_fhcrc_verified"] is False
        and result["header_fhcrc_scope"]=="not_checked_by_fixed_stdlib","CRC/FHCRC scope differs")
    require(result["prior_prefix_bytes"]==PRIOR_PREFIX_BYTES and result["prior_prefix_expected_sha256"]==PRIOR_PREFIX_SHA,"old prefix identity differs")
    if total>=PRIOR_PREFIX_BYTES:
        require(type(result["prefix_crosscheck"]) is bool and result["prior_prefix_actual_sha256"] is not None,"reached old prefix without contemporaneous crosscheck")
    else:require(result["prefix_crosscheck"] is None,"unreached prefix falsely crosschecked")
    census=result["census"]
    require(type(census["event_count"]) is int and 0<=census["event_count"]<=PARSER_LIMITS["event_count"]
        and census["required_state_items"]<=PARSER_LIMITS["state_items"]
        and census["sample_count"]<=128 and census["omitted_sample_count"]==census["event_count"]-census["sample_count"]
        and census["sample_set_complete"] is (census["omitted_sample_count"]==0),"census/sample capacity fields differ")
    if result["status"]=="stream_complete":
        require(result["first_error"] is None and result["first_error_kind"] is None and result["secondary_errors"]==[]
            and result["closed"] is True and result["raw_open_attempts"]==result["reader_instances"]==1
            and result["close_attempts"]==dict(reader=1,raw=1),"complete real stream lifecycle differs")
        require(result["prefix_crosscheck"] is True and result["eof_verified"] is True and result["crc_isize_verified"] is True
            and result["utf8_final_verified"] is True and result["strict_json_complete"] is True
            and result["exact_body_bytes"]==total and total<=CAP and result["full_body_sha256"]==result["prefix_sha256"]
            and result["last_read"]["status"]=="eof" and result["returns"]["empty"]==1,"complete stream facts differ")
        require(result["framer_consumed_bytes"]==total and result["grammar_state"]=="done" and census["status"]=="complete"
            and sum(census["phase_counts"].values())==census["event_count"]
            and all(sum(row.values())==census["event_count"] for row in census["field_presence_types"].values()),"complete census/framing sums differ")
    else:require(result["exact_body_bytes"] is None and result["full_body_sha256"] is None and not result["strict_json_complete"] and census["status"]=="partial","partial stream claims complete qualification")
    return dict(status="saved_stream_structure_verified",returned_bytes=total,outcome=result["status"],event_count=census["event_count"],**flags())


def verify_saved_stream(root,expected,reference,saved,controls):
    """P3 checks persisted reports only; never reopens gzip or executes controls."""
    summary=read(root/"results/stream/summary.json")
    require(summary["protocol"]==PROTOCOL and summary["run_id"]==RUN_ID and summary["subject"]==SUBJECT
        and summary["identity"]==expected and summary["phase"]=="P1_controls_stream" and summary["status"]==SUCCESS
        and summary["first_error"] is None and summary.get("first_error_kind") is None,"saved P1 did not complete")
    require([item["name"] for item in summary["steps"]]==list(STAGES["stream"])
        and all(item["status"]=="pass" for item in summary["steps"]),"saved P1 stage sequence differs")
    require(summary["count"]==saved and summary["stream_outcome"]==saved["status"] and saved["identity"]==expected
        and saved["protocol"]==PROTOCOL and saved["run_id"]==RUN_ID and saved["subject"]==SUBJECT
        and saved["synthetic"] is False and saved["source_reference"]==reference,"P1/count/fixed reference conflict")
    verify_count(saved)
    require(saved["status"]=="stream_complete" and finite(saved["entry_admission"]["remaining_seconds"])
        and saved["entry_admission"]["remaining_seconds"]>=20. and saved["entry_admission"]["minimum_remaining_seconds"]==20.,"real stream admission differs")
    require(controls["protocol"]==PROTOCOL and controls["run_id"]==RUN_ID and controls["subject"]==SUBJECT
        and controls["identity"]==expected and controls["production_source_reference"]==reference
        and controls["status"]=="pass" and controls["count"]==16 and controls["fixture_raw_bytes"]<=65536
        and controls["synthetic"] is True and tuple(group["name"] for group in controls["cases"])==CONTROL_GROUPS
        and all(group["status"]=="pass" and all(case["status"]=="pass" for case in group["cases"]) for group in controls["cases"]),"saved sixteen controls differ")
    census=read(root/"results/stream/census.json");samples=read(root/"results/stream/samples.json")
    require(census["census"]==saved["census"] and census["identity"]==expected and samples["identity"]==expected
        and samples["sample_count"]==len(samples["samples"])==saved["census"]["sample_count"]
        and samples["omitted_sample_count"]==saved["census"]["omitted_sample_count"]
        and samples["sample_set_complete"]==saved["census"]["sample_set_complete"]
        and [row["array_index"] for row in samples["samples"]]==list(range(len(samples["samples"]))),"census/sample artifacts conflict")
    require(summary["controls_count"]==16 and summary["runtime_status"]==summary["source_status"]=="verified"
        and all(summary.get(key) is False and saved.get(key) is False for key in flags()),"saved P1 boundary gates differ")
    return dict(status="saved_stream_outcome_verified",P1_identity=expected,source_reference=reference,
        stream_outcome=saved["status"],sixteen_controls_verified=True,event_count=saved["census"]["event_count"],**flags())


def svg(title,lines):
    height=70+26*len(lines)
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="'+str(height)+'"><rect width="100%" height="100%" fill="#f8fafc"/><g font-family="Segoe UI,Arial,sans-serif" fill="#16324f"><text x="24" y="35" font-size="20">'+escape(title)+'</text>'+''.join('<text x="24" y="'+str(68+26*i)+'" font-size="15">'+escape(line)+'</text>' for i,line in enumerate(lines))+'</g></svg>\n'


def write_text(filename,text):
    gate(WRITE_DEADLINE);data=text.encode("utf-8");admit_write(filename,len(data));gate(WRITE_DEADLINE)
    with Path(filename).open("xb") as stream:
        require(stream.write(data)==len(data),"short SVG write");stream.flush();os.fsync(stream.fileno())
    gate(WRITE_DEADLINE)


def walk_files(root,deadline):
    stack=[root]
    while stack:
        folder=stack.pop();gate(deadline);safe_path(folder,within=root)
        for name in sorted(folder.iterdir(),key=lambda p:p.name):
            gate(deadline);safe_path(name,within=root)
            if name.is_dir():stack.append(name)
            elif name.is_file():yield name
            else:raise ValueError("nonregular evidence entry")


def child(repo,root,action,deadline):
    if action=="prepare":
        require(digest(root/"plan.json",deadline)==os.environ["HF_STREAM1_MANIFEST_SHA"],
                "P0 plan SHA differs from actual saved bytes")
    plan=read(root/"plan.json");phase={"prepare":"P0_prepare","stream":"P1_controls_stream","seal":"P3_seal"}[action]
    expected=identity(phase,os.environ["HF_STREAM1_MANIFEST_SHA"],plan["author_inputs"]["hf_repo/scripts/"+DRIVER]["sha256"])
    checked(__file__,plan["author_inputs"]["hf_repo/scripts/"+DRIVER]["bytes"],expected["driver_sha256"],deadline)
    events=Events(root,phase,deadline);steps=[];output=None
    def step(name,function):
        require(name==STAGES[action][len(steps)],"stage order differs")
        begin=time.monotonic();row=dict(name=name,status="running",start_monotonic=begin);steps.append(row)
        events.emit("stage_started",stage=name)
        try:value=function()
        except BaseException as error:
            detail=error_record(error);row.update(status="failed",error=detail,end_monotonic=time.monotonic())
            if result["first_error"] is None:
                result.update(first_error=detail,first_error_kind=error.kind if isinstance(error,StreamError) else "resource" if isinstance(error,BudgetError) else "source_or_execution")
            try:events.emit("stage_failed",stage=name,error=detail)
            except BaseException as record_error:result.setdefault("secondary_record_errors",[]).append(error_record(record_error))
            raise
        row.update(status="pass",end_monotonic=time.monotonic());events.emit("stage_finished",stage=name);return value
    result=dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,identity=expected,phase=phase,status="not_returned",steps=steps,first_error=None,**flags())
    summary=root/"results"/action/"summary.json"
    try:
        events.emit("process_started",action=action)
        if action=="prepare":
            old=step("historical_authority",lambda:authority(repo,deadline));write(root/"source_authority.json",old)
            rows=input_specs(repo,root,old,plan)
            def freeze():
                for row in rows:
                    gate(deadline)
                    if row["storage_mode"]!="copied":continue
                    checked(row["source"],row["bytes"],row["sha256"],deadline)
                    target=root/row["path"];target.parent.mkdir(parents=True,exist_ok=True)
                    file_count,total_generated=generated_inventory(root)
                    capacity_admit(total_generated,file_count,0)
                    with Path(row["source"]).open("rb") as source,target.open("xb") as out:
                        while True:
                            gate(deadline);data=source.read(CHUNK)
                            if not data:break
                            require(out.write(data)==len(data),"short freeze write")
                        out.flush();os.fsync(out.fileno())
                    checked(target,row["bytes"],row["sha256"],deadline,within=root)
                    events.emit("input_frozen",path=row["path"],bytes=row["bytes"],sha256=row["sha256"])
                write(root/"input_manifest.json",dict(schema="hf-saved-native-stream-input-1",protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,
                    repo=str(repo),files=rows,input_roles=36,copied_files=34,read_only_references=2,runtime_files=19,runtime_bytes=579619,
                    installed_only=[dict(path=path,bytes=size,sha256=sha,copied=False) for path,size,sha in BINARIES],
                    old_binding_sha256=OLD_BINDING_SHA,author_inputs=plan["author_inputs"],**flags()))
                write(root/"source_refs.json",dict(protocol=PROTOCOL,run_id=RUN_ID,references=old["references"],copied=False,**flags()))
                write(root/"rules_reference.json",extract_rule(root/"aux"/RULE_SOURCE,deadline))
            step("input_freeze",freeze)
            check=step("source_precheck",lambda:verify_inputs(root,repo,deadline,references_hash=True));write(root/"source_precheck.json",check)
            result.update(status="pass",input_manifest_sha256=digest(root/"input_manifest.json",deadline),verification=check)
        elif action=="stream":
            check=step("source_binding",lambda:verify_inputs(root,repo,deadline,references_hash=False,
                expected_manifest_sha=os.environ["HF_STREAM1_MANIFEST_SHA"]))
            reference=next(row for row in check["fixed_references"] if row["role"]=="saved_gzip_reference")
            rule_record=extract_rule(root/"aux"/RULE_SOURCE,deadline)
            require(rule_record==read(root/"rules_reference.json"),"persisted AST rule reference differs")
            rule=rule_record["target_rule"];annotations=rule_record["annotations"]
            gzip_module,runtime=step("runtime_identity",lambda:actual_runtime(deadline));write(root/"results/stream/runtime_identity.json",runtime)
            def controls_stage():
                try:return control_cases(gzip_module,deadline,rule,annotations)
                except BaseException as error:
                    result.update(first_error=getattr(error,"original_first_error",None) or error_record(error),
                        first_error_kind=getattr(error,"original_first_error_kind",None) or (error.kind if isinstance(error,StreamError) else "resource" if isinstance(error,BudgetError) else "control_failure"))
                    partial=getattr(error,"control_state",None)
                    if partial is not None:
                        partial.update(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,identity=expected,production_source_reference=reference)
                        try:write(root/"results/stream/controls.json",partial)
                        except BaseException as recording_error:result.setdefault("secondary_record_errors",[]).append(error_record(recording_error))
                    raise
            controls=step("controls",controls_stage)
            controls.update(subject=SUBJECT,identity=expected,production_source_reference=reference)
            write(root/"results/stream/controls.json",controls)
            filename=repo/reference["project_relative_path"];safe_path(filename,within=repo)
            def progress(value):
                row=progress_snapshot(value);row["identity"]=expected
                write(root/"results/stream/progress.json",row,replace=(root/"results/stream/progress.json").exists())
                events.emit("stream_progress",returned_bytes=value["returned_bytes"],read_attempts=value["read_attempts"],
                    framer_consumed_bytes=value["framer_consumed_bytes"],event_count=value["census"]["event_count"])
            def measure():
                value,samples=stream_gzip(gzip_module,lambda:filename.open("rb"),CAP,deadline,rule,annotations,
                    minimum_remaining=20.,on_state=progress,expected_prefix=(PRIOR_PREFIX_BYTES,PRIOR_PREFIX_SHA))
                # Latch the real first error BEFORE writes or saved-result checks.
                if value["first_error"] is not None:result.update(first_error=value["first_error"],first_error_kind=value["first_error_kind"])
                value.update(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,identity=expected,source_reference=reference,synthetic=False,**flags())
                result.update(count=value,stream_outcome=value["status"],controls_count=16,runtime_status=runtime["status"],source_status=check["status"])
                try:
                    write(root/"results/stream/count.json",value)
                    write(root/"results/stream/census.json",dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,identity=expected,census=value["census"],**flags()))
                    write(root/"results/stream/samples.json",dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,identity=expected,samples=samples,
                        sample_count=len(samples),omitted_sample_count=value["census"]["omitted_sample_count"],
                        sample_set_complete=value["census"]["sample_set_complete"],selection="deterministic first <=128 original array objects",**flags()))
                    verify_count(value)
                except BaseException as save_error:
                    if result["first_error"] is not None:result.setdefault("secondary_record_errors",[]).append(error_record(save_error))
                    raise
                if value["first_error"] is not None:raise RuntimeError("real saved-gzip stream stopped; first error remains in saved result")
                require(value["status"]=="stream_complete" and value["closed"] is True,"real stream did not complete")
                return value
            value=step("gzip_stream",measure)
            result.update(status=SUCCESS,stream_outcome=value["status"],count=value,controls_count=16,runtime_status=runtime["status"],source_status=check["status"])

        else:
            issues=[]
            def observed(name,fn):
                try:return fn()
                except BaseException as error:
                    detail=error_record(error);issues.append(dict(stage=name,error=detail))
                    if result["first_error"] is None:result.update(first_error=detail,first_error_kind=error.kind if isinstance(error,StreamError) else "resource" if isinstance(error,BudgetError) else "source_or_execution")
                    return dict(status="not_verified",error=detail)
            post=step("source_postcheck",lambda:observed("source_postcheck",lambda:verify_inputs(root,repo,deadline,references_hash=True,
                      expected_manifest_sha=os.environ["HF_STREAM1_MANIFEST_SHA"])))
            resources=read(root/"resources.json")
            require(resources["protocol"]==PROTOCOL and resources["run_id"]==RUN_ID,"preseal resources identity differs")
            must_complete=resources["status"]==SUCCESS
            pre=observed("pre_source_report",lambda:read(root/"source_precheck.json")) if (root/"source_precheck.json").is_file() else None
            write(root/"source_postcheck.json",post);write(root/"source_preservation.json",dict(protocol=PROTOCOL,run_id=RUN_ID,post=post,
                  pre=pre,**flags()))
            saved=step("saved_results",lambda:observed("saved_results",lambda:read(root/"results/stream/count.json")) if (root/"results/stream/count.json").is_file() else None)
            controls=observed("saved_controls",lambda:read(root/"results/stream/controls.json")) if (root/"results/stream/controls.json").is_file() else None
            checked_count=observed("count_structure",lambda:verify_count(saved)) if saved is not None else None
            def prior_supervision():
                prior=[]
                for name in ("P0_prepare","P1_controls_stream"):
                    filename=root/"results"/(name+"_supervision")/"receipt.json"
                    if not filename.is_file():
                        require(not must_complete,"successful P1 lacks an earlier raw SUP1 receipt")
                        prior.append(dict(phase=name,raw=None));continue
                    raw=read(filename);prior.append(dict(phase=name,raw=raw))
                    require(raw["supervisor_sha256"]==SUP_SHA and raw["cleanup_verified"] is True and raw["errors"]==[]
                            and raw["telemetry_status"]=="disabled", "saved SUP1 cleanup/source/telemetry failed")
                    if must_complete:require(raw["reason"]=="normal_exit" and type(raw["returncode"]) is int and raw["returncode"]==0,"successful P1 lacks normal-zero SUP1 receipts")
                return dict(status="verified_available_sup1_receipts",phases=prior,
                            proof_scope="original SUP1 raw cleanup_verified only; no SUP2 same-instance proof",P3_receipt="parent records after this child returns")
            supervision=step("supervision_review",lambda:observed("supervision_review",prior_supervision));write(root/"supervision_checks.json",supervision)
            diagnostic=dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,status="not_completed",count_verification=checked_count,
                source_status=post.get("status"),control_status=controls.get("status") if controls else None,
                stream_outcome=saved.get("status") if saved else None,source_reference=saved.get("source_reference") if saved else None,
                **flags())
            if must_complete:
                p1_expected=identity("P1_controls_stream",os.environ["HF_STREAM1_MANIFEST_SHA"],expected["driver_sha256"])
                reference=next(row for row in fixed_references() if row["role"]=="saved_gzip_reference")
                verified=observed("successful_P1_saved_gates",lambda:verify_saved_stream(root,p1_expected,reference,saved,controls))
                require(post.get("status")=="verified" or issues,"successful P1 source postcheck lacks evidence")
                diagnostic.update(status="saved_stream_outcome_verified" if not issues and verified["status"]=="saved_stream_outcome_verified" else "evidence_failure",
                                  saved_P1_gates=verified)
            write(root/"diagnostic_verification.json",diagnostic)
            def figures():
                complete=bool(saved and saved.get("status")=="stream_complete" and checked_count
                    and checked_count.get("status")=="saved_stream_structure_verified"
                    and diagnostic.get("status")=="saved_stream_outcome_verified")
                count=saved.get("census",{}) if saved else {}
                line="Exact body: "+str(saved["exact_body_bytes"])+" bytes; full EOF/body CRC32+ISIZE/UTF8/strict JSON verified" if complete else "Saved returned body: "+str(saved.get("returned_bytes") if saved else None)+" bytes; full verification not established"
                lines=[line,"Saved census status: "+str(count.get("status"))+"; verified full census: "+str(complete)+"; decoded objects: "+str(count.get("event_count")),
                    "Phases X/B/E/M: "+"; ".join(k+"="+str(count.get("phase_counts",{}).get(k)) for k in ("X","B","E","M")),
                    "Phases i/I/R/C/s/t/f: "+"; ".join(k+"="+str(count.get("phase_counts",{}).get(k)) for k in ("i","I","R","C","s","t","f")),
                    "Other/missing/wrong phase: "+"; ".join(k+"="+str(count.get("phase_counts",{}).get(k)) for k in ("other","missing","wrong_type")),
                    "Diagnostic target candidates: exact="+str(count.get("candidate_counts",{}).get("exact_event_name"))+"; generic/direct="+str(count.get("candidate_counts",{}).get("generic_name_with_direct_module_arg")),
                    "Samples retained: "+str(count.get("sample_count"))+"; omitted: "+str(count.get("omitted_sample_count"))+"; sample complete: "+str(count.get("sample_set_complete")),
                    "Original prefix crosscheck: "+str(saved.get("prefix_crosscheck") if saved else None)+"; header FHCRC unchecked",
                    "New offline body cap: 1073741824 bytes; per request <=1048576; no intervals/union/cost attribution",
                    "F-TRACE2 original failure retained; native/scientific/force/XPlane qualification false"]
                write_text(root/"census.svg",svg("F-STREAM1 saved gzip census; diagnostic counts only",lines))
                lines=[row["name"]+": "+format(row["elapsed_seconds"],".6f")+" s / peak sampled RSS "+str(row["peak_tree_rss_bytes"])+" bytes" for row in resources["phases"]]
                lines.extend(["This preseal snapshot contains P0/P1 only; final receipt separately records P3",
                    "Receipt totals are write-time snapshots; terminal output reports closing time",
                    "300 s / 4 GiB; original SUP1 sampled process tree, not a desktop hard limit"])
                write_text(root/"resources.svg",svg("F-STREAM1 preseal resources; original SUP1",lines))

            step("visualizations",figures)
            write(root/"payload_status.json",dict(protocol=PROTOCOL,run_id=RUN_ID,scope="P3 child before return",issues=issues,
                parent_late_payload_files=["results/seal/summary.json","results/P3_seal_supervision/receipt.json"],exclusions=EXCLUSIONS,**flags()))
            def payload():
                output={}
                for filename in walk_files(root,deadline):
                    rel=filename.relative_to(root).as_posix()
                    if rel not in EXCLUSIONS:output[rel]=digest(filename,deadline)
                return output
            output=step("payload_manifest",payload)
            result.update(status="pass" if not issues else "evidence_failure",issues=issues,
                          diagnostic_status=diagnostic["status"],stream_outcome=diagnostic["stream_outcome"],payload_sealed=not issues,
                          payload_sealed_scope="child body; parent appends this terminal summary and its real SUP1 receipt")
            events.emit("preservation_complete",status=result["status"],stream_outcome=result["stream_outcome"])
        events.emit("process_finished",status=result["status"])
    except BaseException as error:
        first=result.get("first_error") or error_record(error)
        result.update(status="execution_failure",first_error=first,first_error_kind=result.get("first_error_kind") or (error.kind if isinstance(error,StreamError) else "resource" if isinstance(error,BudgetError) else "source_or_execution"))
        try:events.emit("process_failed",error=first)
        except BaseException as record_error:result["secondary_record_error"]=error_record(record_error)
    finally:
        # One close attempt, guarded so a recording error never replaces an
        # earlier real read/source error or leaves a pre-close pass summary.
        try:events.close()
        except BaseException as close_error:
            detail=error_record(close_error)
            if result["first_error"] is None:result.update(first_error=detail,first_error_kind="recording")
            else:result.setdefault("secondary_record_errors",[]).append(detail)
            result.update(status="execution_failure",payload_sealed=False)
            if action=="seal":result.setdefault("issues",[]).append(dict(stage="events.close",error=detail))
    result["finished_monotonic"]=time.monotonic()
    if action=="seal" and output is not None:
        # Only already written payload is declared here. The terminal summary
        # is written once below; the parent adds its actual SHA after return.
        try:write(root/"output_sha256.json",dict(sorted(output.items())))
        except BaseException as payload_error:
            detail=error_record(payload_error)
            if result["first_error"] is None:result.update(first_error=detail,first_error_kind="recording")
            else:result.setdefault("secondary_record_errors",[]).append(detail)
            result.update(status="execution_failure",payload_sealed=False)
            result.setdefault("issues",[]).append(dict(stage="final_payload_write",error=detail))
    try:write(summary,result)
    except BaseException as summary_error:
        detail=error_record(summary_error)
        if result["first_error"] is None:result.update(first_error=detail,first_error_kind="recording")
        else:result.setdefault("secondary_record_errors",[]).append(detail)
        # One bounded line in the owned stdout log; no summary retry and no
        # unbounded default exception traceback. An absent summary cannot pass.
        print(json.dumps(dict(protocol=PROTOCOL,run_id=RUN_ID,phase=phase,status="terminal_summary_write_failed",
            first_error=result["first_error"],secondary_error=detail),ensure_ascii=True),flush=True)
        return 1
    return 0 if result["status"] in ("pass",SUCCESS) else 1


class Stop(RuntimeError):
    def __init__(self,status,detail):super().__init__(detail);self.status=status


def load_sup(filename):
    checked(filename,SUP_BYTES,SUP_SHA)
    require("_fstream1_sup1" not in sys.modules,"SUP1 already loaded")
    spec=importlib.util.spec_from_file_location("_fstream1_sup1",filename);require(spec and spec.loader,"SUP1 loader unavailable")
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    require(extended(module.__file__)==extended(filename),"actual SUP1 path differs");checked(module.__file__,SUP_BYTES,SUP_SHA)
    for filename,_,size,wanted,name in RUNTIME[:4]:
        actual=sys.modules.get(name);require(actual is not None and extended(actual.__file__)==extended(filename),"actual SUP1 runtime differs: "+name)
        checked(actual.__file__,size,wanted)
    return module


def parent(repo,root):
    start=_ENTRY_START;deadline=start+SECONDS
    require(os.name=="nt" and sys.dont_write_bytecode,"fixed Windows/no-bytecode entry required")
    repo=safe_path(repo);root=extended(root)
    require(root==repo/"hf4_c2_stable_f_validation"/RUN_ID and not root.exists(),"alternate/existing/reset root refused")
    safe_path(root.parent,within=repo)
    require(extended(__file__)==repo/"hf_repo/scripts"/DRIVER,"driver belongs to another project")
    runtime_pin=pin_runtime(deadline-25.25);supervisor=load_sup(repo/"hf_repo/scripts/windows_owned_process.py")
    checked(repo/"hf4_c2_stable_f_validation"/OLD_RUN/"receipt_binding.json",8785,OLD_BINDING_SHA,deadline-25.25,within=repo)
    author={name:dict(bytes=(repo/name).stat().st_size,sha256=digest(repo/name,deadline-25.25)) for name in ("hf_repo/scripts/"+DRIVER,*DOCS)}
    root.mkdir()
    for name in ("events","logs","results"):(root/name).mkdir()
    loaded_sup=dict(version="SUP1",path=str(extended(supervisor.__file__)),bytes=SUP_BYTES,sha256=SUP_SHA)
    phases=[];attempted=set();status="running";failure_detail=None;uncertain=False;records={};closing=[]
    ledger=dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,status=status,start_monotonic=start,deadline_monotonic=deadline,
        seconds=SECONDS,rss_limit_bytes=RSS_LIMIT,limits_seconds=LIMITS,phases=phases,first_stop=None,**flags())
    write(root/"plan.json",dict(ledger,repo=str(repo),author_inputs=author,loaded_supervisor=loaded_sup,runtime_pin=runtime_pin,
        prior_binding_sha256=OLD_BINDING_SHA,prior_bytes_binding_sha256=BYTES_HISTORY[0][2],parser_limits=PARSER_LIMITS,
        control_groups=CONTROL_GROUPS,nonseal_active_deadline=deadline-25.25,seal_active_deadline=deadline-10.25,
        final_binding_reserved_seconds=5.,output_manifest_exclusions=EXCLUSIONS,stages=STAGES,binding_targets=TARGETS,
        terminal_capacity_reserve=dict(bytes=TERMINAL_RESERVE_BYTES,files=TERMINAL_RESERVE_FILES,paths=TERMINAL_PATHS),
        failure_closing=dict(paths=FAILURE_CLOSING_PATHS,once_only=True,no_walk_read_or_file_hash=True,
            consumes_actual_original_clock=True,never_activity_permission_or_success=True)))
    plan_sha=digest(root/"plan.json");write(root/"ledger.json",ledger);manifest_sha=plan_sha
    def shared():return time.monotonic()-start-sum(row["elapsed_seconds"] for row in phases)
    def record_failure(error,where,kind="evidence_failure"):
        nonlocal status,failure_detail
        detail=error_record(error) if isinstance(error,BaseException) else dict(type="parent_stop",message=str(error)[:4096])
        if isinstance(error,BudgetError) or (isinstance(error,StreamError) and error.kind in ("output_capacity","log_capacity","progress_capacity","body_over_cap")):kind="resource_stop"
        if ledger["first_stop"] is None:
            ledger["first_stop"]=dict(status=kind,stage=where,error=detail,monotonic=time.monotonic());failure_detail=detail
        else:
            errors=ledger.setdefault("secondary_parent_errors",[])
            if len(errors)<16:errors.append(dict(stage=where,error=detail))
        if status in ("running",SUCCESS) or kind=="resource_stop":status=kind
        return detail
    def snapshot():
        ledger.update(status=status,error=failure_detail,elapsed_seconds=time.monotonic()-start,
            shared_elapsed_seconds=shared(),supervision_uncertain=uncertain)
        return ledger
    def guarded(where,function):
        try:return function()
        except BaseException as error:
            record_failure(error,where)
            return None
    def save():return write(root/"ledger.json",snapshot(),replace=True)
    def execute(name,bucket,action):
        nonlocal uncertain,failure_detail
        require(name not in attempted,"phase retry refused");attempted.add(name)
        if shared()>25.:raise Stop("resource_stop","preseal shared allowance exhausted")
        begin=time.monotonic();activity=LIMITS[bucket]-GUARD
        active=min(begin+activity,deadline-(10.25 if bucket=="P3" else 25.25))
        if active<=begin:raise Stop("resource_stop","no authorized activity interval remains")
        worker=root/"aux/hf_repo/scripts"/DRIVER if bucket!="P0" else repo/"hf_repo/scripts"/DRIVER
        try:checked(worker,author["hf_repo/scripts/"+DRIVER]["bytes"],author["hf_repo/scripts/"+DRIVER]["sha256"])
        except (OSError,ValueError):
            if bucket!="P3":raise
            worker=repo/"hf_repo/scripts"/DRIVER;checked(worker,author["hf_repo/scripts/"+DRIVER]["bytes"],author["hf_repo/scripts/"+DRIVER]["sha256"])
        checked(supervisor.__file__,SUP_BYTES,SUP_SHA)
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE="1",PYTHONUNBUFFERED="1",PYTHONNOUSERSITE="1",
            HF_STREAM1_ACTIVE_DEADLINE=repr(active),HF_STREAM1_MANIFEST_SHA=manifest_sha)
        command=[sys.executable,"-u","-B",str(worker),"--repo",str(repo),"--root",str(root),"--action",action]
        print(json.dumps(dict(phase=name,active_seconds=active-begin,started_utc=utc())),flush=True)
        # A child can create/write files and the SUP1 redirects its stdout log.
        # Parent cached inventory is therefore invalid until refreshed in time.
        if INVENTORY_CACHE is not None:INVENTORY_CACHE["complete"]=False
        try:raw=supervisor.run_owned(command,cwd=str(root),env=env,log=root/"logs"/(name+".log"),deadline=active,seconds=activity,rss_limit=RSS_LIMIT)
        except BaseException as error:
            uncertain=True;returned=time.monotonic()
            phases.append(dict(name=name,bucket=bucket,phase_start_monotonic=begin,phase_return_monotonic=returned,
                elapsed_seconds=returned-begin,cleanup_verified=False,raw=None,reason="supervision_exception",returncode=None,
                peak_tree_rss_bytes=0,error=error_record(error),raw_receipt_path=None,raw_receipt_sha256=None))
            raise
        returned=time.monotonic()
        if not isinstance(raw,dict) or raw.get("cleanup_verified") is not True:uncertain=True
        # Lock the REAL raw result/return/cleanup BEFORE its first write. Its
        # entire inclusive interval remains this phase even if saving fails.
        row=dict(raw if isinstance(raw,dict) else {},raw=raw,name=name,bucket=bucket,worker_path=str(worker),
            phase_start_monotonic=begin,phase_return_monotonic=returned,elapsed_seconds=returned-begin,
            owned_elapsed_seconds=raw.get("elapsed_seconds") if isinstance(raw,dict) else None,
            inclusive_phase_limit_seconds=LIMITS[bucket],active_deadline_monotonic=active,
            cleanup_verified=raw.get("cleanup_verified") is True if isinstance(raw,dict) else False,
            peak_tree_rss_bytes=raw.get("peak_tree_rss_bytes",0) if isinstance(raw,dict) else 0,
            raw_receipt_path="results/"+name+"_supervision/receipt.json",raw_receipt_sha256=None,
            raw_receipt_status="not_saved",supervisor_identity=loaded_sup,
            current_identity=identity(name,manifest_sha,author["hf_repo/scripts/"+DRIVER]["sha256"]))
        phases.append(row);record_error=None
        try:
            require(isinstance(raw,dict),"SUP1 returned no raw receipt")
            metadata=write(root/row["raw_receipt_path"],raw)
            row.update(raw_receipt_sha256=metadata["sha256"],raw_receipt_status="saved")
        except BaseException as error:
            record_error=error;row["raw_receipt_record_error"]=record_failure(error,name+".raw_receipt")
            exact=getattr(error,"written_metadata",None)
            if exact:row.update(raw_receipt_sha256=exact["sha256"],raw_receipt_status="exact_bytes_saved_late_clock")
            else:row["raw_receipt_status"]="failed_no_retry"
        finally:row["elapsed_seconds"]=time.monotonic()-begin
        phase_ledger=guarded(name+".ledger",save)
        if phase_ledger is None and record_error is None:record_error=Stop("evidence_failure","phase ledger writer failed; no next phase")
        print(json.dumps(dict(phase=name,reason=raw.get("reason") if isinstance(raw,dict) else None,
            returncode=raw.get("returncode") if isinstance(raw,dict) else None,elapsed_seconds=row["elapsed_seconds"],
            peak_rss_bytes=row["peak_tree_rss_bytes"],cleanup_verified=row["cleanup_verified"],raw_receipt_status=row["raw_receipt_status"])),flush=True)
        if record_error:raise Stop("resource_stop" if isinstance(record_error,(BudgetError,StreamError)) else "evidence_failure",name+": raw receipt was not normally saved")
        if uncertain:raise Stop("cleanup_not_pass",name+": original SUP1 cleanup failed")
        if row["elapsed_seconds"]>LIMITS[bucket] or raw["reason"] in ("global_deadline","phase_timeout","rss_limit"):raise Stop("resource_stop",name+": phase/resource limit")
        if raw["supervisor_sha256"]!=SUP_SHA:raise Stop("source_not_pass",name+": SUP1 SHA differs")
        if raw["errors"] or raw["reason"]=="supervision_error" or raw["telemetry_status"]!="disabled" or raw["telemetry_first_error"] is not None:raise Stop("supervision_not_pass",name+": original SUP1 error/telemetry")
        summaryfile=root/"results"/action/"summary.json";summary=read(summaryfile) if summaryfile.is_file() else None
        if action=="stream" and summary:ledger["stream_outcome"]=summary.get("stream_outcome")
        if summary and summary.get("first_error") is not None and ledger["first_stop"] is None:
            ledger["first_stop"]=dict(status="resource_stop" if summary.get("first_error_kind")=="resource" else "execution_failure",
                stage=name,error=summary["first_error"],error_kind=summary.get("first_error_kind"),monotonic=time.monotonic())
            failure_detail=summary["first_error"]
            # Retain the ORIGINAL read/control error, not its wrapper exception.
        if summary and summary.get("first_error_kind")=="resource":raise Stop("resource_stop",name+": self-observed deadline")
        if raw["reason"]!="normal_exit" or type(raw["returncode"]) is not int or raw["returncode"]!=0:
            if summary:ledger[name+"_summary"]=dict(status=summary.get("status"),identity=summary.get("identity"),
                first_error=summary.get("first_error"),first_error_kind=summary.get("first_error_kind"),
                stream_outcome=summary.get("stream_outcome"),steps=[dict(name=x.get("name"),status=x.get("status")) for x in summary.get("steps",[])])
            raise Stop("gzip_integrity_failure" if summary and summary.get("first_error_kind")=="container_integrity" else "execution_failure",name+": "+str(raw["reason"]))
        require(summary and summary.get("identity")==row["current_identity"] and all(summary.get(k) is False for k in flags()),"child identity/boundary differs")
        require([item["name"] for item in summary["steps"]]==list(STAGES[action]) and all(item["status"]=="pass" for item in summary["steps"]),"child successful stage sequence differs")
        if action=="stream":
            require(summary["status"]==SUCCESS and summary["first_error"] is None and summary["controls_count"]==16
                and summary["runtime_status"]==summary["source_status"]=="verified","stream completion lacks gates")
            saved=read(root/"results/stream/count.json");verify_count(saved)
            reference=next(item for item in fixed_references() if item["role"]=="saved_gzip_reference")
            verify_saved_stream(root,row["current_identity"],reference,saved,read(root/"results/stream/controls.json"))
        else:
            require(summary["status"]=="pass","prepare/seal did not pass")
            if action=="seal" and status==SUCCESS:
                require(summary.get("diagnostic_status")=="saved_stream_outcome_verified" and summary.get("payload_sealed") is True and summary.get("issues")==[],"successful P1 lacks complete P3 gates")
                diagnostic=read(root/"diagnostic_verification.json")
                require(diagnostic["status"]=="saved_stream_outcome_verified" and diagnostic["source_status"]=="verified" and diagnostic["control_status"]=="pass","P3 saved/source/control gate differs")
        return summary
    try:
        prepared=execute("P0_prepare","P0","prepare")
        actual=digest(root/"input_manifest.json",deadline-25.25);require(prepared["input_manifest_sha256"]==actual,"P0 saved manifest SHA differs")
        manifest_sha=actual
        streamed=execute("P1_controls_stream","P1","stream");ledger["stream_outcome"]=streamed["stream_outcome"]
        require(ledger["first_stop"] is None,"an earlier parent recording failure prevents success")
        status=SUCCESS
    except BaseException as error:record_failure(error,"campaign",error.status if isinstance(error,Stop) else "execution_failure")
    finally:
        guarded("preseal_ledger",save)
        guarded("preseal_resources",lambda:write(root/"resources.json",dict(protocol=PROTOCOL,run_id=RUN_ID,status=status,scope="preseal P0/P1 only",
            phases=phases,elapsed_seconds=time.monotonic()-start,peak_tree_rss_bytes=max((row.get("peak_tree_rss_bytes",0) for row in phases),default=0),rss_limit_bytes=RSS_LIMIT,**flags())))
        if not uncertain and all(row.get("cleanup_verified") is True for row in phases) and shared()<=25. and time.monotonic()<deadline-10.25:
            try:execute("P3_seal","P3","seal")
            except BaseException as error:record_failure(error,"P3_seal",error.status if isinstance(error,Stop) else "evidence_failure")
        else:record_failure("cleanup uncertainty or shared/seal reserve exhausted","seal_skipped")
        def late_payload():
            outputfile=root/"output_sha256.json";p3=[row for row in phases if row["name"]=="P3_seal"]
            if not outputfile.is_file() or not p3:
                if status==SUCCESS:raise ValueError("successful P3 lacks actual output map/raw")
                return None
            output=read(outputfile);last=p3[0]
            if last.get("raw_receipt_sha256") is not None:output[last["raw_receipt_path"]]=last["raw_receipt_sha256"]
            else:require(status!=SUCCESS,"successful P3 lacks normally written raw receipt")
            summaryfile=root/"results/seal/summary.json"
            try:
                if summaryfile.is_file():output[summaryfile.relative_to(root).as_posix()]=digest(summaryfile,deadline)
                else:require(status!=SUCCESS,"successful P3 lacks terminal summary")
            except BaseException as error:record_failure(error,"late_P3_summary_hash")
            return write(outputfile,dict(sorted(output.items())),replace=True)
        guarded("late_P3_payload",late_payload)
        if time.monotonic()>=deadline or shared()>LIMITS["shared"]:record_failure("original campaign/shared allowance exhausted","terminal_budget","resource_stop")
        bind_deadline=min(deadline,start+LIMITS["shared"]+sum(row["elapsed_seconds"] for row in phases));hash_allowed=True
        for rel in TARGETS:
            if rel=="execution_receipt.json":continue
            filename=root/rel;item=dict(path=rel,bytes=None,sha256=None,status="partial",reason="not_metadata_checked")
            if time.monotonic()>=deadline:
                records[rel]=item;hash_allowed=False;continue # no new late metadata or hash
            try:info=filename.lstat()
            except FileNotFoundError:records[rel]=None;continue
            except BaseException as error:
                record_failure(error,"binding_metadata:"+rel);records[rel]=dict(item,error=error_record(error));hash_allowed=False;continue
            item.update(bytes=info.st_size,reason="unhashed_existing_target")
            try:
                require(stat.S_ISREG(info.st_mode),"binding target is not regular");safe_path(filename,within=root)
                if not hash_allowed or time.monotonic()>=bind_deadline:raise BudgetError("final target hashing stopped")
                require(info.st_size<=PARSER_LIMITS["generated_file_bytes"],"oversize binding target cannot be hashed")
                if rel.startswith(("events/","logs/")):require(info.st_size<=PARSER_LIMITS["log_bytes"],"oversize log target cannot be hashed")
                item=dict(path=rel,bytes=info.st_size,sha256=digest(filename,bind_deadline))
            except BaseException as error:
                hash_allowed=False;item["error"]=error_record(error);record_failure(error,"binding_hash:"+rel)
            records[rel]=item
        missing=[rel for rel in TARGETS if rel!="execution_receipt.json" and (records.get(rel) is None or records[rel].get("status")=="partial" or records[rel].get("sha256") is None)]
        if missing:
            ledger["missing_or_partial_binding_targets"]=missing
            if status==SUCCESS:record_failure("mandatory binding targets absent/partial","binding_targets")
        # All normal final writes have independent guards. A real I/O failure
        # marks its writer closed permanently; that target is never retried.
        saved_ledger=guarded("final_ledger",save)
        receipt=guarded("execution_receipt",lambda:write(root/"execution_receipt.json",snapshot()))
        if receipt:records["execution_receipt.json"]=receipt
        else:records["execution_receipt.json"]=dict(path="execution_receipt.json",bytes=None,sha256=None,status="partial",reason="receipt_not_normally_written")
        binding=dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,status=status,records={rel:records.get(rel) for rel in TARGETS},
            old_binding_sha256=OLD_BINDING_SHA,prior_bytes_binding_sha256=BYTES_HISTORY[0][2],output_manifest_exclusions=EXCLUSIONS,
            elapsed_before_binding_seconds=time.monotonic()-start,shared_before_binding_seconds=shared(),**flags())
        bound=guarded("receipt_binding",lambda:write(root/"receipt_binding.json",binding))
        overrun=time.monotonic()>=deadline or shared()>LIMITS["shared"]
        if overrun:record_failure("terminal writes finished outside the original allowance","late_terminal_budget","resource_stop")
        terminal_closed=bool(saved_ledger and receipt and bound and not overrun)
        if not terminal_closed or binding["status"]!=status:
            if status==SUCCESS:record_failure("terminal evidence not closed","terminal_evidence")
            # One necessary FAILED closing transition. The clock is NOT reset
            # or extended, and no walk/read/file hash/new phase is attempted.
            failed_snapshot=dict(snapshot(),terminal_closing="necessary failure preservation; original cost still counted")
            closure_values=(("ledger.json",failed_snapshot),("execution_receipt.json",failed_snapshot))
            for rel,value in closure_values:
                attempt=dict(path=rel,attempted=True,saved=False)
                try:
                    require(not uncertain,"cleanup uncertainty forbids file closing")
                    meta=failure_close_write(root/rel,value);attempt.update(saved=True,bytes=meta["bytes"],sha256=meta["sha256"])
                    if rel=="execution_receipt.json":records[rel]=meta
                except BaseException as error:attempt["error"]=error_record(error)
                closing.append(attempt)
            failure_binding=dict(binding,status=status,records={rel:records.get(rel) for rel in TARGETS},
                elapsed_before_binding_seconds=time.monotonic()-start,shared_before_binding_seconds=shared(),
                closing_scope="necessary failure preservation only; no activity permit or success",closing_ledger_receipt=closing)
            attempt=dict(path="receipt_binding.json",attempted=True,saved=False)
            try:
                require(not uncertain,"cleanup uncertainty forbids file closing")
                meta=failure_close_write(root/"receipt_binding.json",failure_binding);attempt.update(saved=True,bytes=meta["bytes"],sha256=meta["sha256"])
            except BaseException as error:attempt["error"]=error_record(error)
            closing.append(attempt);terminal_closed=all(row["saved"] for row in closing)
        print(json.dumps(dict(protocol=PROTOCOL,run_id=RUN_ID,status=status,stream_outcome=ledger.get("stream_outcome"),
            elapsed_seconds=time.monotonic()-start,shared_seconds=shared(),root=str(root),terminal_evidence_closed=terminal_closed,
            failure_closing=closing,prior_success_binding_stale_or_unverified=not terminal_closed,
            original_deadline_monotonic=deadline,actual_terminal_monotonic=time.monotonic(),first_stop=ledger["first_stop"],**flags()),ensure_ascii=True),flush=True)
    return 0 if status==SUCCESS and terminal_closed else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--repo",required=True,type=Path);parser.add_argument("--root",required=True,type=Path)
    parser.add_argument("--action",choices=("prepare","stream","seal"));args=parser.parse_args()
    global EVIDENCE_ROOT,WRITE_DEADLINE
    repo,root=extended(args.repo),extended(args.root)
    EVIDENCE_ROOT=root
    require(root==repo/"hf4_c2_stable_f_validation"/RUN_ID,"child/parent fixed root differs")
    if args.action is None:
        WRITE_DEADLINE=_ENTRY_START+SECONDS
        return parent(repo,root)
    deadline=float(os.environ["HF_STREAM1_ACTIVE_DEADLINE"]);require(finite(deadline),"nonfinite child deadline")
    WRITE_DEADLINE=deadline
    return child(repo,root,args.action,deadline)


if __name__=="__main__":
    sys.dont_write_bytecode=True
    try:code=main()
    except BaseException as error:
        print(json.dumps(dict(protocol=PROTOCOL,run_id=RUN_ID,status="entry_or_recording_failure",error=error_record(error)),ensure_ascii=True),flush=True)
        code=1
    raise SystemExit(code)
