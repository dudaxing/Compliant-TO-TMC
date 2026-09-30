"""F-BYTES1: bounded volume/integrity reading of one saved gzip, no JSON decode.

Authoring is text/AST only. The sole parent entry owns a 60-second / 4-GiB
window and the original SUP1. Child prepare/volume/seal modes share this file.
"""
from __future__ import annotations
import time
_ENTRY_START = time.monotonic()

import argparse
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

PROTOCOL = "F-BYTES1"
RUN_ID = "native_volume_001"
SUBJECT = "saved_gzip_volume_diagnostic"
SUCCESS = "saved_gzip_volume_diagnostic_complete"
DRIVER = "run_native_volume_diagnostic.py"
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
CAP = 256*1024**2
CHUNK = 1024**2
SECONDS = 60.
RSS_LIMIT = 4*1024**3
LIMITS = {"P0":10., "P1":25., "P3":10., "shared":15.}
GUARD = 5.25
STAGES = {"prepare":("historical_authority", "input_freeze", "source_precheck"),
          "volume":("source_binding", "runtime_identity", "controls", "gzip_count"),
          "seal":("source_postcheck", "saved_results", "supervision_review", "visualizations", "payload_manifest")}
EXCLUSIONS = ("output_sha256.json", "receipt_binding.json", "execution_receipt.json", "ledger.json",
              "events/P3_seal.ndjson", "logs/P3_seal.log")
TARGETS = ("plan.json", "input_manifest.json", "source_authority.json", "source_refs.json", "source_precheck.json",
    "results/prepare/summary.json", "results/volume/runtime_identity.json", "results/volume/controls.json",
    "results/volume/progress.json", "results/volume/count.json", "results/volume/summary.json",
    "source_postcheck.json", "source_preservation.json", "supervision_checks.json", "diagnostic_verification.json",
    "resources.json", "payload_status.json", "volume.svg", "resources.svg", "results/seal/summary.json",
    "results/P0_prepare_supervision/receipt.json", "results/P1_volume_supervision/receipt.json",
    "results/P3_seal_supervision/receipt.json", "events/P0_prepare.ndjson", "events/P1_volume.ndjson",
    "events/P3_seal.ndjson", "logs/P0_prepare.log", "logs/P1_volume.log", "logs/P3_seal.log",
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
    def invalid(value):raise ValueError("nonfinite JSON refused: "+value)
    return json.loads(safe_path(filename).read_text(encoding="utf-8"),parse_constant=invalid)


def write(filename, value, *, replace=False):
    filename=Path(filename);filename.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8")
    target=filename.with_suffix(".pending.json") if replace else filename
    with target.open("xb") as stream:
        require(stream.write(data)==len(data), "short evidence write")
        stream.flush();os.fsync(stream.fileno())
    if replace:os.replace(target,filename)
    return dict(path=filename.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def error_record(error):
    return dict(type=type(error).__name__,module=type(error).__module__,message=str(error),traceback=traceback.format_exc())


def flags():
    return dict(scientific_admission=False,force_executed=False,runtime_native_trace_observed=False,
                native_json_parsed=False,xplane_decoded=False)


def identity(phase, manifest_sha, driver_sha):
    return dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,phase=phase,
                input_manifest_sha256=manifest_sha,driver_sha256=driver_sha,supervisor_sha256=SUP_SHA)


class Events:
    def __init__(self,root,phase):
        self.root=root;self.phase=phase;self.sequence=0;self.stream=(root/"events"/(phase+".ndjson")).open("x",encoding="utf-8",newline="\n")
    def emit(self,event,**fields):
        self.sequence+=1
        row=dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,phase=self.phase,event=event,
                 sequence=self.sequence,utc=utc(),monotonic=time.monotonic(),pid=os.getpid(),native_tid=threading.get_native_id(),**fields)
        self.stream.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+"\n");self.stream.flush();os.fsync(self.stream.fileno())
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
    import gzip
    import _compression
    import subprocess
    import psutil
    import zlib
    require(psutil.__version__=="7.2.2", "fixed psutil version differs")
    modules=[]
    for filename,_,size,wanted,name in RUNTIME:
        module=sys.modules.get(name)
        require(module is not None and extended(module.__file__)==extended(filename), "actual runtime module path differs: "+name)
        checked(module.__file__,size,wanted,deadline)
        modules.append(dict(name=name,path=str(extended(module.__file__)),bytes=size,sha256=wanted,actual_import=True))
    require(getattr(zlib,"__file__",None) is None and zlib.__spec__.origin=="built-in", "zlib is not the pinned built-in interface")
    pinned.update(status="verified",actual_modules=modules,zlib=dict(origin="built-in",has_file=False,
                  module_name=zlib.__name__),reader_type="gzip._GzipReader directly; no io.BufferedReader/GzipFile")
    return gzip,pinned


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
        histories.append(dict(original_path=name,project_relative_path=filename.relative_to(repo).as_posix(),bytes=size,sha256=wanted))
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
    return dict(protocol=PROTOCOL,run_id=RUN_ID,status="verified",old_protocol="F-TRACE2",old_run_id=OLD_RUN,
                old_outcome="observability_not_pass",binding_sha256=OLD_BINDING_SHA,histories=histories,references=references,
                old_json_bytes=339677,old_native_bytes=112391941,old_eight_bytes=112731618,**flags())


def input_specs(repo,root,old,plan):
    rows=[]
    def add(source,target,role,size,wanted):
        rows.append(dict(source=str(extended(source)),path=target,role=role,storage_mode="copied",bytes=size,sha256=wanted))
    for row in old["histories"]:add(repo/row["project_relative_path"],"provenance/"+OLD_RUN+"/"+row["original_path"],"selected_history_json",row["bytes"],row["sha256"])
    for name in ("hf_repo/scripts/"+DRIVER,*DOCS):
        meta=plan["author_inputs"][name];add(repo/name,"aux/"+name,"author_input",meta["bytes"],meta["sha256"])
    add(repo/"hf_repo/scripts/windows_owned_process.py","aux/hf_repo/scripts/windows_owned_process.py","fixed_sup1",SUP_BYTES,SUP_SHA)
    for filename,target,size,wanted,_ in RUNTIME:add(filename,target,"fixed_runtime_source",size,wanted)
    for row in old["references"]:rows.append(dict(row,path="reference/"+row["role"],source=str(repo/row["project_relative_path"])))
    require(len(rows)==18 and sum(row["storage_mode"]=="copied" for row in rows)==16
            and sum(row["storage_mode"]=="external_read_only_reference" for row in rows)==2, "18 roles / 16 copied / 2 references differ")
    require(sum(row["bytes"] for row in rows if row["role"]=="fixed_runtime_source")==322370,"six runtime bytes differ")
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
    require(manifest["protocol"]==PROTOCOL and manifest["run_id"]==RUN_ID and len(manifest["files"])==18,"input identity differs")
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
    return dict(protocol=PROTOCOL,run_id=RUN_ID,status="verified",rows=rows,count=18,
                input_manifest_sha256=actual_manifest_sha,fixed_references=fixed,
                native_reference_sha_rechecked=references_hash,live_checked=live,**flags())


def count_gzip(gzip_module,raw_factory,cap,deadline,*,minimum_remaining=0.,on_state=None):
    """The five tiny controls and the real read use this identical bounded reader.

    _GzipReader passes read(size) to zlib's max_length directly. No BufferedReader
    is allowed to produce an uncounted decompressed read-ahead buffer. Prefix
    means exactly returned bytes counted here, never internal/unreturned bytes.
    """
    require(type(cap) is int and cap>=0,"invalid body cap")
    result=dict(schema="hf-saved-gzip-count-1",status="not_returned",cap_bytes=cap,max_countable_bytes=cap+1,
        request_limit_bytes=CHUNK,reader_type="gzip._GzipReader",buffered_reader=False,returned_bytes=0,
        exact_body_bytes=None,body_bytes_lower_bound=0,full_body_sha256=None,prefix_sha256=hashlib.sha256(b"").hexdigest(),
        prefix_definition="all and only decompressed bytes returned by completed read calls and counted here",
        eof_verified=False,crc_isize_verified=False,crc_scope="all_member_body_crc32_and_isize",
        header_fhcrc_verified=False,header_fhcrc_scope="not_checked_by_fixed_stdlib",
        raw_open_attempts=0,reader_instances=0,read_attempts=0,
        read_records=[],first_error=None,first_error_kind=None,secondary_errors=[],closed=False,
        started_monotonic=time.monotonic())
    value=hashlib.sha256();raw=reader=None
    try:
        gate(deadline)
        result["raw_open_attempts"]=1;raw=raw_factory()
        reader=gzip_module._GzipReader(raw);result["reader_instances"]=1
        if on_state:on_state(result)
        while True:
            gate(deadline)
            remaining=deadline-time.monotonic() if deadline is not None else None
            if result["read_attempts"]==0:
                if remaining is not None and remaining<minimum_remaining:
                    raise BudgetError("less than five seconds remain before the real gzip read")
                result["entry_admission"]=dict(remaining_seconds=remaining,minimum_remaining_seconds=minimum_remaining)
            request=min(CHUNK,cap+1-result["returned_bytes"])
            require(request>0,"counter attempted a read after the cap+1 boundary")
            begin=time.monotonic();result["read_attempts"]+=1
            row=dict(index=result["read_attempts"],request_bytes=request,start_monotonic=begin,returned_bytes=None,status="not_returned")
            result["read_records"].append(row)
            try:data=reader.read(request)
            except BaseException as error:
                row.update(status="raised",end_monotonic=time.monotonic(),error_type=type(error).__name__)
                raise
            ended=time.monotonic();require(isinstance(data,bytes) and len(data)<=request,"reader exceeded its bounded request")
            row.update(status="returned" if data else "eof",returned_bytes=len(data),end_monotonic=ended)
            if not data:
                gate(deadline)
                result.update(status="exact_eof_crc_verified",exact_body_bytes=result["returned_bytes"],
                              full_body_sha256=value.hexdigest(),eof_verified=True,crc_isize_verified=True)
                break
            value.update(data);result["returned_bytes"]+=len(data)
            result.update(body_bytes_lower_bound=result["returned_bytes"],prefix_sha256=value.hexdigest())
            gate(deadline)
            if result["returned_bytes"]>cap:
                result["status"]="body_over_cap"
                break  # Never read again to obtain EOF, CRC or an exact size.
            if on_state:on_state(result)
    except BaseException as error:
        result["first_error"]=error_record(error)
        if isinstance(error,(gzip_module.BadGzipFile,EOFError,gzip_module.zlib.error)):
            result.update(status="integrity_failure",first_error_kind="container_integrity")
        else:
            result.update(status="not_returned",first_error_kind="resource" if isinstance(error,BudgetError) else "io_or_recording")
    finally:
        for label,handle in (("reader",reader),("raw",raw)):
            if handle is None:continue
            try:handle.close()  # _GzipReader.close never reads or finishes CRC.
            except BaseException as error:
                detail=dict(error_record(error),operation=label+".close")
                if result["first_error"] is None:
                    result.update(first_error=detail,first_error_kind="close_io",status="not_returned",
                                  exact_body_bytes=None,full_body_sha256=None,eof_verified=False,crc_isize_verified=False)
                else:result["secondary_errors"].append(detail)
        result["closed"]=not result["secondary_errors"] and result["first_error_kind"]!="close_io"
        result["finished_monotonic"]=time.monotonic()
    return result


def control_cases(gzip_module,deadline):
    cap=8;body=b"abcd";normal=gzip_module.compress(b"ab",mtime=0)+gzip_module.compress(b"cd",mtime=0)
    full=gzip_module.compress(b"abcdefgh",mtime=0);over=gzip_module.compress(b"abcdefghi",mtime=0)
    bad=bytearray(gzip_module.compress(body,mtime=0));bad[-8]^=1
    truncated=gzip_module.compress(body,mtime=0)[:-4]
    fixtures=(("normal_eof",normal,"exact_eof_crc_verified",body),
              ("exact_small_cap",full,"exact_eof_crc_verified",b"abcdefgh"),
              ("small_cap_plus_one",over,"body_over_cap",b"abcdefghi"),
              ("bad_crc_rejected",bytes(bad),"integrity_failure",body),
              ("truncation_rejected",truncated,"integrity_failure",body))
    cases=[]
    for name,encoded,expected,returned in fixtures:
        result=count_gzip(gzip_module,lambda data=encoded:io.BytesIO(data),cap,deadline)
        require(result["status"]==expected and result["returned_bytes"]==len(returned)
                and result["prefix_sha256"]==hashlib.sha256(returned).hexdigest()
                and result["raw_open_attempts"]==result["reader_instances"]==1 and result["closed"] is True,
                "same counter control failed: "+name)
        if expected=="exact_eof_crc_verified":require(result["eof_verified"] and result["crc_isize_verified"] and result["full_body_sha256"]==result["prefix_sha256"],"EOF control failed")
        else:require(not result["eof_verified"] and not result["crc_isize_verified"] and result["full_body_sha256"] is None and result["exact_body_bytes"] is None,"partial boundary control failed")
        require(all(0<row["request_bytes"]<=CHUNK and row["request_bytes"]<=cap+1-sum(r["returned_bytes"] or 0 for r in result["read_records"][:index]) for index,row in enumerate(result["read_records"])),"control request bound failed")
        cases.append(dict(name=name,status="pass",synthetic=True,small_cap_bytes=cap,compressed_fixture_bytes=len(encoded),
                          compressed_fixture_sha256=hashlib.sha256(encoded).hexdigest(),expected_status=expected,result=result))
    return dict(protocol=PROTOCOL,run_id=RUN_ID,status="pass",count=5,synthetic=True,cases=cases,
                same_count_function="count_gzip",production_cap_bytes=CAP,controls_do_not_change_production_cap=True)


def verify_count(result):
    require(isinstance(result,dict) and result["reader_type"]=="gzip._GzipReader" and result["buffered_reader"] is False
            and result["cap_bytes"]==CAP and result["max_countable_bytes"]==CAP+1
            and result["request_limit_bytes"]==CHUNK,"real counter contract differs")
    require(result["status"] in ("exact_eof_crc_verified","body_over_cap","integrity_failure","not_returned"),"unknown count outcome")
    require(type(result["read_attempts"]) is int and result["read_attempts"]==len(result["read_records"]),"read attempts/records differ")
    require(result["crc_scope"]=="all_member_body_crc32_and_isize" and result["header_fhcrc_verified"] is False
            and result["header_fhcrc_scope"]=="not_checked_by_fixed_stdlib","CRC scope differs")
    total=0
    for index,row in enumerate(result["read_records"],1):
        require(type(row["index"]) is int and row["index"]==index and row["status"] in ("returned","eof","raised","not_returned"),"read row identity/status differs")
        require(type(row["request_bytes"]) is int and 0<row["request_bytes"]<=min(CHUNK,CAP+1-total),"real request bound differs")
        if row["returned_bytes"] is not None:
            require(type(row["returned_bytes"]) is int and 0<=row["returned_bytes"]<=row["request_bytes"],"returned count differs")
            total+=row["returned_bytes"]
        if row["status"]=="returned":require(row["returned_bytes"] is not None and row["returned_bytes"]>0,"returned row has no returned body")
        elif row["status"]=="eof":require(row["returned_bytes"]==0 and index==len(result["read_records"]),"EOF row is not the last empty return")
        else:require(row["returned_bytes"] is None,"unreturned/raised row claims returned body bytes")
    require(total==result["returned_bytes"]==result["body_bytes_lower_bound"] and 0<=total<=CAP+1,"real total differs")
    require(type(result["returned_bytes"]) is int and type(result["body_bytes_lower_bound"]) is int
            and isinstance(result["prefix_sha256"],str) and len(result["prefix_sha256"])==64,"counter/prefix scalar type differs")
    if result["status"] in ("body_over_cap","exact_eof_crc_verified"):
        require(result["first_error"] is None and result["first_error_kind"] is None and result["secondary_errors"]==[]
                and result["closed"] is True and type(result["raw_open_attempts"]) is int and result["raw_open_attempts"]==1
                and type(result["reader_instances"]) is int and result["reader_instances"]==1 and result["read_records"],"successful counter lifecycle differs")
        require(all(row["status"] in ("returned","eof") and row["returned_bytes"] is not None for row in result["read_records"]),"successful count has an unreturned read")
    if result["status"]=="body_over_cap":
        require(total==CAP+1 and result["exact_body_bytes"] is None and result["full_body_sha256"] is None
                and result["eof_verified"] is False and result["crc_isize_verified"] is False
                and result["read_records"][-1]["status"]=="returned" and result["read_records"][-1]["returned_bytes"]>0,"over-cap fields differ")
    elif result["status"]=="exact_eof_crc_verified":
        require(total<=CAP and result["exact_body_bytes"]==total and result["full_body_sha256"]==result["prefix_sha256"]
                and result["eof_verified"] is True and result["crc_isize_verified"] is True
                and result["read_records"][-1]["status"]=="eof" and result["read_records"][-1]["returned_bytes"]==0,"exact EOF fields differ")
    else:
        require(result["exact_body_bytes"] is None and result["full_body_sha256"] is None
                and result["eof_verified"] is False and result["crc_isize_verified"] is False,"partial outcome claims complete fields")
    return dict(status="saved_count_structure_verified",counted_bytes=total,outcome=result["status"],not_a_json_validity_check=True)


def verify_saved_volume(root,expected,reference,saved,controls):
    """P3 checks saved bytes/reports only; no counter, controls or gzip rerun."""
    summary=read(root/"results/volume/summary.json")
    require(summary["protocol"]==PROTOCOL and summary["run_id"]==RUN_ID and summary["subject"]==SUBJECT
            and summary["identity"]==expected and summary["phase"]=="P1_volume" and summary["status"]==SUCCESS
            and summary["first_error"] is None and summary.get("first_error_kind") is None,"saved P1 summary did not succeed")
    require([item["name"] for item in summary["steps"]]==list(STAGES["volume"])
            and all(item["status"]=="pass" for item in summary["steps"]),"saved P1 successful stages differ")
    require(summary["count"]==saved and summary["volume_outcome"]==saved["status"]
            and saved["identity"]==expected and saved["protocol"]==PROTOCOL and saved["run_id"]==RUN_ID
            and saved["subject"]==SUBJECT and saved["synthetic"] is False and saved["source_reference"]==reference,
            "P1 summary/count/fixed reference conflict")
    verify_count(saved)
    require(saved["status"] in ("exact_eof_crc_verified","body_over_cap") and saved["closed"] is True
            and saved["first_error"] is None and finite(saved["entry_admission"]["remaining_seconds"])
            and saved["entry_admission"]["remaining_seconds"]>=5. and saved["entry_admission"]["minimum_remaining_seconds"]==5.,
            "saved real byte entry/outcome differs")
    names=["normal_eof","exact_small_cap","small_cap_plus_one","bad_crc_rejected","truncation_rejected"]
    require(controls["protocol"]==PROTOCOL and controls["run_id"]==RUN_ID and controls["subject"]==SUBJECT
            and controls["identity"]==expected and controls["production_source_reference"]==reference
            and controls["status"]=="pass" and type(controls["count"]) is int and controls["count"]==5
            and controls["synthetic"] is True and [case["name"] for case in controls["cases"]]==names
            and all(case["status"]=="pass" and case["synthetic"] is True and case["result"]["status"]==case["expected_status"]
                    for case in controls["cases"]),"saved five controls identity/outcomes differ")
    require(type(summary["controls_count"]) is int and summary["controls_count"]==5
            and summary["runtime_status"]==summary["source_status"]=="verified"
            and all(summary.get(key) is False and saved.get(key) is False for key in flags()),"saved P1 boundary gates differ")
    return dict(status="saved_byte_outcome_verified",P1_identity=expected,source_reference=reference,
                volume_outcome=saved["status"],five_controls_verified=True,**flags())


def svg(title,lines):
    height=70+26*len(lines)
    return '<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="'+str(height)+'"><rect width="100%" height="100%" fill="#f8fafc"/><g font-family="Segoe UI,Arial,sans-serif" fill="#16324f"><text x="24" y="35" font-size="20">'+escape(title)+'</text>'+''.join('<text x="24" y="'+str(68+26*i)+'" font-size="15">'+escape(line)+'</text>' for i,line in enumerate(lines))+'</g></svg>\n'


def write_text(filename,text):
    with Path(filename).open("x",encoding="utf-8",newline="\n") as stream:stream.write(text);stream.flush();os.fsync(stream.fileno())


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
        require(digest(root/"plan.json",deadline)==os.environ["HF_BYTES1_MANIFEST_SHA"],
                "P0 plan SHA differs from actual saved bytes")
    plan=read(root/"plan.json");phase={"prepare":"P0_prepare","volume":"P1_volume","seal":"P3_seal"}[action]
    expected=identity(phase,os.environ["HF_BYTES1_MANIFEST_SHA"],plan["author_inputs"]["hf_repo/scripts/"+DRIVER]["sha256"])
    checked(__file__,plan["author_inputs"]["hf_repo/scripts/"+DRIVER]["bytes"],expected["driver_sha256"],deadline)
    events=Events(root,phase);steps=[];output=None
    def step(name,function):
        require(name==STAGES[action][len(steps)],"stage order differs")
        begin=time.monotonic();row=dict(name=name,status="running",start_monotonic=begin);steps.append(row)
        events.emit("stage_started",stage=name)
        try:value=function()
        except BaseException as error:
            detail=error_record(error);row.update(status="failed",error=detail,end_monotonic=time.monotonic())
            if result["first_error"] is None:
                result.update(first_error=detail,first_error_kind="resource" if isinstance(error,BudgetError) else "source_or_execution")
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
                    with Path(row["source"]).open("rb") as source,target.open("xb") as out:
                        while True:
                            gate(deadline);data=source.read(CHUNK)
                            if not data:break
                            require(out.write(data)==len(data),"short freeze write")
                        out.flush();os.fsync(out.fileno())
                    checked(target,row["bytes"],row["sha256"],deadline,within=root)
                    events.emit("input_frozen",path=row["path"],bytes=row["bytes"],sha256=row["sha256"])
                write(root/"input_manifest.json",dict(schema="hf-saved-native-volume-input-1",protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,
                    repo=str(repo),files=rows,input_roles=18,copied_files=16,read_only_references=2,runtime_files=6,runtime_bytes=322370,
                    installed_only=[dict(path=path,bytes=size,sha256=sha,copied=False) for path,size,sha in BINARIES],
                    old_binding_sha256=OLD_BINDING_SHA,author_inputs=plan["author_inputs"],**flags()))
                write(root/"source_refs.json",dict(protocol=PROTOCOL,run_id=RUN_ID,references=old["references"],copied=False,**flags()))
            step("input_freeze",freeze)
            check=step("source_precheck",lambda:verify_inputs(root,repo,deadline,references_hash=True));write(root/"source_precheck.json",check)
            result.update(status="pass",input_manifest_sha256=digest(root/"input_manifest.json",deadline),verification=check)
        elif action=="volume":
            check=step("source_binding",lambda:verify_inputs(root,repo,deadline,references_hash=False,
                       expected_manifest_sha=os.environ["HF_BYTES1_MANIFEST_SHA"]))
            reference=next(row for row in check["fixed_references"] if row["role"]=="saved_gzip_reference")
            gzip_module,runtime=step("runtime_identity",lambda:actual_runtime(deadline));write(root/"results/volume/runtime_identity.json",runtime)
            controls=step("controls",lambda:control_cases(gzip_module,deadline))
            controls.update(subject=SUBJECT,identity=expected,production_source_reference=reference)
            write(root/"results/volume/controls.json",controls)
            filename=repo/reference["project_relative_path"];safe_path(filename,within=repo)
            def progress(value):
                write(root/"results/volume/progress.json",dict(protocol=PROTOCOL,run_id=RUN_ID,identity=expected,count=value),replace=(root/"results/volume/progress.json").exists())
                events.emit("count_progress",returned_bytes=value["returned_bytes"],read_attempts=value["read_attempts"])
            def measure():
                value=count_gzip(gzip_module,lambda:filename.open("rb"),CAP,deadline,minimum_remaining=5.,on_state=progress)
                # The real first error is latched immediately on return, before
                # any saving/verifying operation can itself fail.
                if value["first_error"] is not None:
                    result.update(first_error=value["first_error"],first_error_kind=value["first_error_kind"])
                value.update(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,identity=expected,source_reference=reference,synthetic=False,**flags())
                try:
                    write(root/"results/volume/count.json",value)
                    verify_count(value)
                except BaseException as save_error:
                    if result["first_error"] is not None:result.setdefault("secondary_record_errors",[]).append(error_record(save_error))
                    raise
                if value["first_error"] is not None:
                    raise RuntimeError("real gzip read failed: "+str(value["first_error"]))
                require(value["status"] in ("exact_eof_crc_verified","body_over_cap") and value["closed"] is True,"real gzip outcome did not complete")
                return value
            value=step("gzip_count",measure)
            result.update(status=SUCCESS,volume_outcome=value["status"],count=value,controls_count=5,runtime_status=runtime["status"],source_status=check["status"])
        else:
            issues=[]
            def observed(name,fn):
                try:return fn()
                except BaseException as error:
                    detail=error_record(error);issues.append(dict(stage=name,error=detail))
                    if result["first_error"] is None:result.update(first_error=detail,first_error_kind="resource" if isinstance(error,BudgetError) else "source_or_execution")
                    return dict(status="not_verified",error=detail)
            post=step("source_postcheck",lambda:observed("source_postcheck",lambda:verify_inputs(root,repo,deadline,references_hash=True,
                      expected_manifest_sha=os.environ["HF_BYTES1_MANIFEST_SHA"])))
            resources=read(root/"resources.json")
            require(resources["protocol"]==PROTOCOL and resources["run_id"]==RUN_ID,"preseal resources identity differs")
            must_complete=resources["status"]==SUCCESS
            pre=observed("pre_source_report",lambda:read(root/"source_precheck.json")) if (root/"source_precheck.json").is_file() else None
            write(root/"source_postcheck.json",post);write(root/"source_preservation.json",dict(protocol=PROTOCOL,run_id=RUN_ID,post=post,
                  pre=pre,**flags()))
            saved=step("saved_results",lambda:observed("saved_results",lambda:read(root/"results/volume/count.json")) if (root/"results/volume/count.json").is_file() else None)
            controls=observed("saved_controls",lambda:read(root/"results/volume/controls.json")) if (root/"results/volume/controls.json").is_file() else None
            checked_count=observed("count_structure",lambda:verify_count(saved)) if saved is not None else None
            def prior_supervision():
                prior=[]
                for name in ("P0_prepare","P1_volume"):
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
                volume_outcome=saved.get("status") if saved else None,source_reference=saved.get("source_reference") if saved else None,
                **flags())
            if must_complete:
                p1_expected=identity("P1_volume",os.environ["HF_BYTES1_MANIFEST_SHA"],expected["driver_sha256"])
                reference=next(row for row in fixed_references() if row["role"]=="saved_gzip_reference")
                verified=observed("successful_P1_saved_gates",lambda:verify_saved_volume(root,p1_expected,reference,saved,controls))
                require(post.get("status")=="verified" or issues,"successful P1 source postcheck lacks evidence")
                diagnostic.update(status="saved_byte_outcome_verified" if not issues and verified["status"]=="saved_byte_outcome_verified" else "evidence_failure",
                                  saved_P1_gates=verified)
            write(root/"diagnostic_verification.json",diagnostic)
            def figures():
                if saved and saved.get("status")=="exact_eof_crc_verified":line="Exact decompressed bytes: "+str(saved["exact_body_bytes"])+"; EOF/member body CRC32+ISIZE verified"
                elif saved and saved.get("status")=="body_over_cap":line="Decompressed bytes >= "+str(saved["body_bytes_lower_bound"])+"; exact size unknown; EOF/CRC not verified"
                else:line="Decompressed exact size unknown; saved returned prefix: "+str(saved.get("returned_bytes") if saved else None)
                write_text(root/"volume.svg",svg("F-BYTES1 saved gzip volume; no native event interpretation",["Compressed gzip: 24572396 bytes; original XPlane: 87819545 bytes (not decoded)",line,
                    "Production body cap: 268435456 bytes; requests <= 1048576 bytes","Prefix SHA covers returned and counted bytes only; no JSON validity claim",
                    "Header FHCRC is not checked by the fixed standard library",
                    "F-TRACE2 original 64 MiB single-file gate remains failed; scientific admission false"]))
                lines=[row["name"]+": "+format(row["elapsed_seconds"],".6f")+" s / peak sampled RSS "+str(row["peak_tree_rss_bytes"])+" bytes" for row in resources["phases"]]
                lines.extend(["This preseal snapshot contains P0/P1 only; final receipt separately records P3","Receipt totals are write-time snapshots; terminal output reports closing time","60 s / 4 GiB; original SUP1 sampled process tree, not a disk/global desktop hard limit"])
                write_text(root/"resources.svg",svg("F-BYTES1 preseal resources; original SUP1",lines))
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
                          diagnostic_status=diagnostic["status"],volume_outcome=diagnostic["volume_outcome"],payload_sealed=not issues,
                          payload_sealed_scope="child body; parent appends this terminal summary and its real SUP1 receipt")
            events.emit("preservation_complete",status=result["status"],volume_outcome=result["volume_outcome"])
        events.emit("process_finished",status=result["status"])
    except BaseException as error:
        first=result.get("first_error") or error_record(error)
        result.update(status="execution_failure",first_error=first,first_error_kind=result.get("first_error_kind") or ("resource" if isinstance(error,BudgetError) else "source_or_execution"))
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
    write(summary,result)
    return 0 if result["status"] in ("pass",SUCCESS) else 1


class Stop(RuntimeError):
    def __init__(self,status,detail):super().__init__(detail);self.status=status


def load_sup(filename):
    checked(filename,SUP_BYTES,SUP_SHA)
    require("_fbytes1_sup1" not in sys.modules,"SUP1 already loaded")
    spec=importlib.util.spec_from_file_location("_fbytes1_sup1",filename);require(spec and spec.loader,"SUP1 loader unavailable")
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
    runtime_pin=pin_runtime(deadline-20.25);supervisor=load_sup(repo/"hf_repo/scripts/windows_owned_process.py")
    checked(repo/"hf4_c2_stable_f_validation"/OLD_RUN/"receipt_binding.json",8785,OLD_BINDING_SHA,deadline-20.25,within=repo)
    author={name:dict(bytes=(repo/name).stat().st_size,sha256=digest(repo/name,deadline-20.25)) for name in ("hf_repo/scripts/"+DRIVER,*DOCS)}
    root.mkdir()
    for name in ("events","logs","results"):(root/name).mkdir()
    loaded_sup=dict(version="SUP1",path=str(extended(supervisor.__file__)),bytes=SUP_BYTES,sha256=SUP_SHA)
    phases=[];attempted=set();status="running";failure_detail=None;uncertain=False
    ledger=dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,status=status,start_monotonic=start,deadline_monotonic=deadline,
                seconds=SECONDS,rss_limit_bytes=RSS_LIMIT,limits_seconds=LIMITS,phases=phases,first_stop=None,**flags())
    write(root/"plan.json",dict(ledger,repo=str(repo),author_inputs=author,loaded_supervisor=loaded_sup,runtime_pin=runtime_pin,
         prior_binding_sha256=OLD_BINDING_SHA,nonseal_active_deadline=deadline-20.25,seal_active_deadline=deadline-10.25,
         final_binding_reserved_seconds=5.,output_manifest_exclusions=EXCLUSIONS,stages=STAGES,binding_targets=TARGETS))
    plan_sha=digest(root/"plan.json");write(root/"ledger.json",ledger);manifest_sha=plan_sha
    def shared():return time.monotonic()-start-sum(row["elapsed_seconds"] for row in phases)
    def save():
        ledger.update(status=status,error=failure_detail,elapsed_seconds=time.monotonic()-start,
                      shared_elapsed_seconds=shared(),supervision_uncertain=uncertain)
        write(root/"ledger.json",ledger,replace=True)
    def execute(name,bucket,action):
        nonlocal uncertain
        require(name not in attempted,"phase retry refused");attempted.add(name)
        if shared()>10.:raise Stop("resource_stop","preseal shared allowance exhausted")
        begin=time.monotonic();activity=LIMITS[bucket]-GUARD
        active=min(begin+activity,deadline-(10.25 if bucket=="P3" else 20.25))
        if active<=begin:raise Stop("resource_stop","no authorized phase interval remains")
        worker=root/"aux/hf_repo/scripts"/DRIVER if bucket!="P0" else repo/"hf_repo/scripts"/DRIVER
        try:checked(worker,author["hf_repo/scripts/"+DRIVER]["bytes"],author["hf_repo/scripts/"+DRIVER]["sha256"])
        except (OSError,ValueError):
            if bucket!="P3":raise
            worker=repo/"hf_repo/scripts"/DRIVER
            checked(worker,author["hf_repo/scripts/"+DRIVER]["bytes"],author["hf_repo/scripts/"+DRIVER]["sha256"])
        checked(supervisor.__file__,SUP_BYTES,SUP_SHA)
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE="1",PYTHONUNBUFFERED="1",PYTHONNOUSERSITE="1",
            HF_BYTES1_ACTIVE_DEADLINE=repr(active),HF_BYTES1_MANIFEST_SHA=manifest_sha)
        command=[sys.executable,"-u","-B",str(worker),"--repo",str(repo),"--root",str(root),"--action",action]
        print(json.dumps(dict(phase=name,active_seconds=active-begin,started_utc=utc())),flush=True)
        try:raw=supervisor.run_owned(command,cwd=str(root),env=env,log=root/"logs"/(name+".log"),deadline=active,seconds=activity,rss_limit=RSS_LIMIT)
        except BaseException:
            uncertain=True;raise
        if not isinstance(raw,dict) or raw.get("cleanup_verified") is not True:uncertain=True
        require(isinstance(raw,dict),"SUP1 returned no raw receipt")
        rawfile=root/"results"/(name+"_supervision")/"receipt.json";rawmeta=write(rawfile,raw)
        row=dict(raw,name=name,bucket=bucket,worker_path=str(worker),phase_start_monotonic=begin,phase_return_monotonic=time.monotonic(),
            owned_elapsed_seconds=raw["elapsed_seconds"],elapsed_seconds=time.monotonic()-begin,inclusive_phase_limit_seconds=LIMITS[bucket],
            active_deadline_monotonic=active,raw_receipt_path=rawfile.relative_to(root).as_posix(),raw_receipt_sha256=rawmeta["sha256"],
            supervisor_identity=loaded_sup,current_identity=identity(name,manifest_sha,author["hf_repo/scripts/"+DRIVER]["sha256"]))
        phases.append(row);save()
        print(json.dumps(dict(phase=name,reason=raw["reason"],returncode=raw["returncode"],elapsed_seconds=row["elapsed_seconds"],
                        peak_rss_bytes=raw["peak_tree_rss_bytes"],cleanup_verified=raw["cleanup_verified"])),flush=True)
        if uncertain:raise Stop("cleanup_not_pass",name+": original SUP1 cleanup failed")
        if row["elapsed_seconds"]>LIMITS[bucket] or raw["reason"] in ("global_deadline","phase_timeout","rss_limit"):
            raise Stop("resource_stop",name+": phase/resource limit")
        if raw["supervisor_sha256"]!=SUP_SHA:raise Stop("source_not_pass",name+": SUP1 SHA differs")
        if raw["errors"] or raw["reason"]=="supervision_error" or raw["telemetry_status"]!="disabled" or raw["telemetry_first_error"] is not None:
            raise Stop("supervision_not_pass",name+": original SUP1 errors/telemetry")
        summaryfile=root/"results"/action/"summary.json"
        summary=read(summaryfile) if summaryfile.is_file() else None
        if summary and summary.get("first_error_kind")=="resource":raise Stop("resource_stop",name+": self-observed active deadline")
        if raw["reason"]!="normal_exit" or type(raw["returncode"]) is not int or raw["returncode"]!=0:
            ledger[name+"_summary"]=summary
            raise Stop("gzip_integrity_failure" if summary and summary.get("first_error_kind")=="container_integrity" else "execution_failure",name+": "+str(raw["reason"]))
        require(summary and summary.get("identity")==row["current_identity"] and all(summary.get(k) is False for k in flags()),"child identity/boundary differs")
        require([item["name"] for item in summary["steps"]]==list(STAGES[action]) and all(item["status"]=="pass" for item in summary["steps"]),"child successful stage sequence differs")
        if action=="volume":
            require(summary["status"]==SUCCESS and summary["first_error"] is None and summary["controls_count"]==5
                    and summary["runtime_status"]==summary["source_status"]=="verified","volume completion lacks gates")
            saved=read(root/"results/volume/count.json");verify_count(saved)
            reference=next(row for row in fixed_references() if row["role"]=="saved_gzip_reference")
            verify_saved_volume(root,row["current_identity"],reference,saved,read(root/"results/volume/controls.json"))
            require(saved["raw_open_attempts"]==saved["reader_instances"]==1 and saved["closed"] is True
                    and saved["first_error"] is None and saved["status"]==summary["volume_outcome"]
                    and saved["entry_admission"]["remaining_seconds"]>=5.,"real read lifecycle/admission differs")
        else:
            require(summary["status"]=="pass","prepare/seal did not pass")
            if action=="seal" and status==SUCCESS:
                require(summary.get("diagnostic_status")=="saved_byte_outcome_verified" and summary.get("payload_sealed") is True
                        and summary.get("issues")==[],"successful P1 lacks complete independent P3 gates")
                diagnostic=read(root/"diagnostic_verification.json")
                require(diagnostic["status"]=="saved_byte_outcome_verified" and diagnostic["source_status"]=="verified"
                        and diagnostic["control_status"]=="pass","P3 diagnostic/source/control gate differs")
        return summary
    try:
        prepare_summary=execute("P0_prepare","P0","prepare")
        actual_manifest_sha=digest(root/"input_manifest.json",deadline-20.25)
        require(prepare_summary["input_manifest_sha256"]==actual_manifest_sha,"P0 claimed manifest SHA differs from actual saved bytes")
        manifest_sha=actual_manifest_sha
        summary=execute("P1_volume","P1","volume");ledger["volume_outcome"]=summary["volume_outcome"]
        status=SUCCESS
    except BaseException as error:
        status=error.status if isinstance(error,Stop) else "execution_failure";failure_detail=error_record(error)
        ledger["first_stop"]=dict(status=status,error=failure_detail,monotonic=time.monotonic())
    finally:
        save();write(root/"resources.json",dict(protocol=PROTOCOL,run_id=RUN_ID,status=status,scope="preseal P0/P1 only",phases=phases,
            elapsed_seconds=time.monotonic()-start,peak_tree_rss_bytes=max((r["peak_tree_rss_bytes"] for r in phases),default=0),rss_limit_bytes=RSS_LIMIT))
        if not uncertain and all(row["cleanup_verified"] for row in phases) and shared()<=10. and time.monotonic()<deadline-10.25:
            try:
                execute("P3_seal","P3","seal")
            except BaseException as error:
                ledger["seal_error"]=error_record(error)
                if status==SUCCESS:status=error.status if isinstance(error,Stop) else "evidence_failure";failure_detail=ledger["seal_error"]
        else:
            ledger["seal_skipped"]="cleanup uncertainty or shared/seal reserve exhausted"
            if status==SUCCESS:status="evidence_failure";failure_detail=ledger["seal_skipped"]
        # The final child summary and real P3 SUP1 receipt are produced after
        # the child-body inventory. Append only actual files, also on failed P3.
        # This small bookkeeping step never upgrades a failed P1 or P3 outcome.
        outputfile=root/"output_sha256.json"
        p3rows=[row for row in phases if row["name"]=="P3_seal"]
        if outputfile.is_file() and p3rows:
            try:
                output=read(outputfile);last=p3rows[0]
                output[last["raw_receipt_path"]]=last["raw_receipt_sha256"]
                seal_summary=root/"results/seal/summary.json"
                try:
                    if seal_summary.is_file():output[seal_summary.relative_to(root).as_posix()]=digest(seal_summary,deadline)
                except BaseException as summary_error:
                    ledger["late_summary_hash_error"]=error_record(summary_error)
                    if isinstance(summary_error,BudgetError):status="resource_stop";failure_detail=ledger["late_summary_hash_error"]
                    elif status==SUCCESS:status="evidence_failure";failure_detail=ledger["late_summary_hash_error"]
                    # Raw P3 already has a SHA from its exact successful write.
                    # Preserve that real entry even if the late summary hash is
                    # unavailable; never retry the summary hash or its writes.
                write(outputfile,dict(sorted(output.items())),replace=True)
            except BaseException as error:
                ledger["late_payload_error"]=error_record(error)
                if status==SUCCESS:status="evidence_failure";failure_detail=ledger["late_payload_error"]
        elif status==SUCCESS:
            ledger["late_payload_error"]="successful P3 lacks its saved output manifest or real raw receipt"
            status="evidence_failure";failure_detail=ledger["late_payload_error"]
        if time.monotonic()>=deadline or shared()>LIMITS["shared"]:status="resource_stop";failure_detail="campaign/shared allowance exhausted"
        records={};binding_errors=[];hash_allowed=True
        bind_deadline=min(deadline,start+LIMITS["shared"]+sum(row["elapsed_seconds"] for row in phases))
        for rel in TARGETS:
            if rel=="execution_receipt.json":continue
            filename=root/rel
            item=dict(path=rel,bytes=None,sha256=None,status="partial")
            try:
                info=filename.lstat()
            except FileNotFoundError:
                records[rel]=None
                continue
            except BaseException as error:
                hash_allowed=False;item.update(reason="unhashed_target_metadata_error",error=error_record(error));binding_errors.append(item)
                records[rel]=item
                continue
            item["bytes"]=info.st_size
            try:
                require(stat.S_ISREG(info.st_mode),"binding target is not a regular file")
                safe_path(filename,within=root)
                if not hash_allowed or time.monotonic()>=bind_deadline:raise BudgetError("final target hashing stopped")
                item=dict(path=rel,bytes=info.st_size,sha256=digest(filename,bind_deadline))
            except BaseException as error:
                hash_allowed=False;item.update(reason="unhashed_existing_target",error=error_record(error));binding_errors.append(item)
            records[rel]=item
        if binding_errors:
            ledger["binding_errors"]=binding_errors
            if time.monotonic()>=bind_deadline:status="resource_stop";failure_detail="final binding allowance exhausted"
            elif status==SUCCESS:status="evidence_failure";failure_detail="target hash not verified"
        incomplete=[rel for rel in TARGETS if rel!="execution_receipt.json" and
                    (records[rel] is None or records[rel].get("status")=="partial" or
                     records[rel].get("sha256") is None or records[rel].get("bytes") is None)]
        if incomplete:
            ledger["missing_or_partial_binding_targets"]=incomplete
            if status==SUCCESS:status="evidence_failure";failure_detail="required binding targets missing or partial"
        if status!=SUCCESS and ledger["first_stop"] is None:ledger["first_stop"]=dict(status=status,error=failure_detail,monotonic=time.monotonic())
        save();receipt=write(root/"execution_receipt.json",read(root/"ledger.json"));records["execution_receipt.json"]=receipt
        binding=dict(protocol=PROTOCOL,run_id=RUN_ID,subject=SUBJECT,status=status,records={rel:records[rel] for rel in TARGETS},
                     old_binding_sha256=OLD_BINDING_SHA,output_manifest_exclusions=EXCLUSIONS,
                     elapsed_before_binding_seconds=time.monotonic()-start,shared_before_binding_seconds=shared(),**flags())
        write(root/"receipt_binding.json",binding)
        if time.monotonic()>=deadline or shared()>LIMITS["shared"]:
            status="resource_stop";failure_detail="final consistency writes finished outside allowance"
            if ledger["first_stop"] is None:ledger["first_stop"]=dict(status=status,error=failure_detail,monotonic=time.monotonic())
            save();receipt=write(root/"execution_receipt.json",read(root/"ledger.json"),replace=True)
            binding.update(status=status,elapsed_before_binding_seconds=time.monotonic()-start,shared_before_binding_seconds=shared())
            binding["records"]["execution_receipt.json"]=receipt;write(root/"receipt_binding.json",binding,replace=True)
        print(json.dumps(dict(protocol=PROTOCOL,run_id=RUN_ID,status=status,volume_outcome=ledger.get("volume_outcome"),
                             elapsed_seconds=time.monotonic()-start,shared_seconds=shared(),root=str(root),**flags())),flush=True)
    return 0 if status==SUCCESS else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--repo",required=True,type=Path);parser.add_argument("--root",required=True,type=Path)
    parser.add_argument("--action",choices=("prepare","volume","seal"));args=parser.parse_args()
    repo,root=extended(args.repo),extended(args.root)
    require(root==repo/"hf4_c2_stable_f_validation"/RUN_ID,"child/parent fixed root differs")
    if args.action is None:return parent(repo,root)
    deadline=float(os.environ["HF_BYTES1_ACTIVE_DEADLINE"]);require(finite(deadline),"nonfinite child deadline")
    return child(repo,root,args.action,deadline)


if __name__=="__main__":
    sys.dont_write_bytecode=True
    raise SystemExit(main())
