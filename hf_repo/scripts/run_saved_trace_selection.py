"""F-SELECT1: select records from one authenticated, previously accepted trace prefix.

No numerical computation or full-trace admission. The original strict parser and
SUP1 are imported unchanged; only the prefix lifecycle and selection are new.
"""
from __future__ import annotations
import time
START = time.monotonic()
import argparse
import codecs
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys

CORE_SHA = "1250415b2084cd4d52aaae2a0f996f3a905e513cbb8e1b6085ac15c143569174"
core_path = Path(__file__).with_name("run_saved_trace_census.py")
for ancestor in reversed((core_path,*core_path.parents)):
    info=ancestor.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info,"st_file_attributes",0)&0x400:
        raise RuntimeError("parser load through reparse/symlink refused")
core_bytes=core_path.read_bytes()
if len(core_bytes)!=128256 or hashlib.sha256(core_bytes).hexdigest() != CORE_SHA:
    raise RuntimeError("immutable parser source differs")
spec = importlib.util.spec_from_file_location("_fselect1_core", core_path)
c = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = c
spec.loader.exec_module(c)

PROTOCOL, RUN = "F-SELECT1", "prefix_select_001"
SUCCESS = "prefix_selection_complete"
PARSE_END, RETURN_END, EVENTS = 453448982, 453720232, 4000000
RETURN_SHA = "1964b1b99c02b4281bc63c6d0a9214c566d96331bc98ae3f3c808f7e0c0ae90b"
OLD = "hf4_c2_stable_f_validation/native_stream_001/"
TRACE = "hf4_c2_stable_f_validation/micro_trace_002/"
FIXED = (
    (OLD+"receipt_binding.json",7182,"0bba3f6663d342e3c13c7a6dc9f5098846b1f9a0bf5702df59100b0d97e5ea48"),
    (OLD+"results/stream/count.json",10209,"fa0c75a69955dc2cfca89b11536d1b7ab9f6a592b87563b6e2d39189e768bc54"),
    (OLD+"results/stream/census.json",4649,"e779021b8e5868fb6a94fc76b7c1e64c74a3b84e9bb19f31cbbdfe4009e2c6a3"),
    (OLD+"results/stream/controls.json",817637,"4c1cff870130dbdfc9621d844eb320ccff9ba50b9dfd11cd7262fa93c0b4c1d4"),
    (TRACE+"receipt_binding.json",8785,c.OLD_BINDING_SHA),
    (TRACE+"input_manifest.json",66374,"922bb4e793334b331c177e9cd8c18b472498e7ef065f70061d0df86862ed0a33"),
    (TRACE+"native_manifest.json",3098,"7d421902680efa677e2ee32a686121bae5de576cb3b8e529308105be046eed9a"),
    (TRACE+"results/trace/summary.json",190902,"1c996bfcd9688772a7404e752023b7e44e3c35d73f1a9ffaca8fa1cf9a2c96f0"),
    ("hf_repo/scripts/run_saved_trace_census.py",128256,CORE_SHA),
    ("hf_repo/scripts/windows_owned_process.py",c.SUP_BYTES,c.SUP_SHA),
    (c.RULE_SOURCE,c.RULE_BYTES,c.RULE_SHA),
)
GZIP_REL, GZIP_SIZE, GZIP_SHA = TRACE+c.NATIVE[0][0], c.NATIVE[0][1], c.NATIVE[0][2]
CROSS_KEYS = ("event_count","phase_counts","field_presence_types","metadata_fixed_counts",
              "application_name_counts","candidate_counts","trace_thread_counts",
              "required_state_items","top_level_other_values_validated","last_validated_event_end_byte")
CORE_NODES = ("strict_decoder","validate_value","Census","Framer","capacity_admit","log_admit")
NEW_GROUPS = {
    "endpoint":("exact_endpoint_and_uninterpreted_invalid_suffix","endpoint_minus_one","endpoint_plus_one"),
    "utf8":("cross_block_utf8_one_byte_reads",),
    "two_hashes":("old_sha_mismatch","returned_sha_mismatch"),
    "request":("last_request_narrowed",),
    "fields":("all_required_roles_conflicting_module","missing_null_and_nonscalar_types"),
    "counts":("wrong_required_counts",),
    "multiple_roles":("same_index_multiple_roles",),
    "diagnostics":("diagnostic_omission_required_late","diagnostic_58_full_still_counts"),
    "records":("retained_records_exact_128","retained_records_over_128"),
    "field_text":("field_text_exact_4096","field_text_over_4096"),
    "retained_text":("retained_16MiB_exact","retained_16MiB_over"),
    "eof":("early_eof",),"trailer":("bad_trailer_crc",),
    "close":("read_io_and_secondary_close","success_prefix_close_error"),
    "admission":("expired_deadline_no_open","insufficient_first_read_activity"),
    "saved_interface":("saved_selection_roundtrip","saved_selection_conflict"),
}


def identity(phase, manifest, driver):
    return dict(protocol=PROTOCOL,run_id=RUN,subject="saved_prefix_selection",phase=phase,input_manifest_sha256=manifest,
                driver_sha256=driver,parser_source_sha256=CORE_SHA,supervisor_sha256=c.SUP_SHA)


class Selection(c.Census):
    def __init__(self, rule, annotations, limits, deadline, sample_limit=58):
        # Original first-128 sampling is replaced explicitly, not inherited as a new pass.
        super().__init__(rule,annotations,dict(limits,samples=0),deadline)
        self.records=[];self.roles=dict(direct=0,marker=0,metadata=0)
        self.generic={name:0 for name in rule["native_names_with_module_arg"]}
        self.diagnostic_count=0;self.diagnostic_retained=0;self.sample_limit=sample_limit
        self.unit_parts=None

    def field(self, mapping, key):
        if type(mapping) is not dict or key not in mapping:
            return dict(present=False,type="missing",value_retained=False)
        value=mapping[key];scalar=type(value) in (str,int,float,bool) or value is None
        result=dict(present=True,type=c.typename(value),value_retained=scalar)
        if scalar:result["value"]=self.retain(value) if type(value) is str else value
        return result

    def event(self, event, start, end):
        index=self.count
        super().event(event,start,end)
        name=event.get("name");args=event.get("args")
        if type(name) is str and name in self.generic:self.generic[name]+=1
        application=type(name) is str and name.startswith("F-TRACE2:")
        direct=not application and type(args) is dict and any(
            type(args.get(k)) is str and args[k] in self.rule["exact_arg_values"] for k in self.rule["exact_arg_keys"])
        roles=[r for r,yes in (("direct",direct),("marker",type(name) is str and name in self.markers),("metadata",event.get("ph")=="M")) if yes]
        for role in roles:self.roles[role]+=1
        diagnostic=not roles and type(name) is str and name in self.generic
        if diagnostic:self.diagnostic_count+=1
        if not roles and (not diagnostic or self.diagnostic_retained>=self.sample_limit):return
        if len(self.records)>=128:c.fault("selection_capacity","retained record capacity exhausted")
        if roles and sum(self.roles.values())>70:c.fault("selection_capacity","required role capacity exhausted")
        module={k:self.field(args,k) for k in self.rule["exact_arg_keys"]}
        for field in module.values():
            field["matches"]=field.get("type")=="string" and field.get("value") in self.rule["exact_arg_values"]
            field["conflicts"]=field["present"] and (not field["value_retained"] or field.get("value") not in self.rule["exact_arg_values"])
        exact=type(name) is str and name in self.rule["exact_event_names"]
        generic=type(name) is str and name in self.generic
        self.records.append(dict(array_index=index,start_byte=start,end_byte_exclusive=end,
            unit_sha256=hashlib.sha256(b"".join(self.unit_parts)).hexdigest(),roles=roles or ["diagnostic"],
            fields={k:self.field(event,k) for k in c.FIELD_NAMES},module_fields=module,
            metadata_and_marker_args={k:self.field(args,k) for k in ("name","sort_index","graph","phase","protocol","run_id","hlo_op","hlo_instruction","op_name")},
            conflicting_module_keys=[k for k,v in module.items() if v["conflicts"]],
            original_rule_name_gate=dict(exact=exact,generic=generic,
                application_excluded=application,diagnostic_name_and_direct_match=not application and (exact or generic and direct),
                reason="application excluded" if application else "original execution name absent" if not exact and not generic else "name gate only; no interval admission")))
        if diagnostic:self.diagnostic_retained+=1

    def selection(self):
        required=[r for r in self.records if r["roles"]!=["diagnostic"]]
        return dict(role_counts=self.roles,required_unique_records=len(required),retained_records=len(self.records),
            generic_name_counts=self.generic,diagnostic_candidates=self.diagnostic_count,
            diagnostic_retained=self.diagnostic_retained,diagnostic_omitted=self.diagnostic_count-self.diagnostic_retained,
            sample_set_complete=self.diagnostic_count==self.diagnostic_retained,
            selection="all required roles plus first <=58 other exact generic-name records",
            retained_text_bytes=self.retained_text,core_first128_samples_replaced=True)


class SelectionFramer(c.Framer):
    def finish_unit(self):
        self.census.unit_parts=self.unit["parts"]
        try:super().finish_unit()
        finally:self.census.unit_parts=None


def prefix_stream(gzip, factory, deadline, rule, annotations, *, parse_end, return_end,
                  event_count, old_prefix, return_sha, expected_roles, chunk=c.CHUNK,
                  limits=None, sample_limit=58, minimum_remaining=0., progress=None):
    limits=dict(c.PARSER_LIMITS if limits is None else limits)
    c.require(0<parse_end<=return_end and 0<old_prefix[0]<=return_end and 0<chunk<=c.CHUNK,"invalid prefix endpoints/request")
    census=Selection(rule,annotations,limits,deadline,sample_limit)
    framer=SelectionFramer(census,limits,deadline);utf8=codecs.getincrementaldecoder("utf-8")("strict")
    digest=hashlib.sha256();older=hashlib.sha256();raw=reader=None;next_progress=16*1024**2
    result=dict(status="partial",scope="only predetermined accepted prefix",parse_end=parse_end,return_end=return_end,
        returned_bytes=0,read_attempts=0,raw_open_attempts=0,reader_instances=0,close_attempts=dict(reader=0,raw=0),
        last_request=None,last_return=None,prefix_sha256=None,old_prefix_actual_sha256=None,old_prefix_crosscheck=False,
        requests=dict(total=0,min=None,max=None,last=None),returns=dict(total=0,min=None,max=None,last=None,nonempty=0,empty=0),last_read=None,
        eof_verified=False,crc_isize_verified=False,utf8_final_verified=False,strict_json_complete=False,
        full_body_sha256=None,exact_body_bytes=None,parser_endpoint_verified=False,
        first_error=None,first_error_kind=None,secondary_errors=[],closed=False,progress_updates=0,
        reader_type="gzip._GzipReader directly",started_monotonic=time.monotonic(),**c.flags())
    def snapshot():
        result.update(framer.positions(),census=census.snapshot(False),selection=census.selection(),
                      prefix_sha256=digest.hexdigest(),uninterpreted_returned_bytes=result["returned_bytes"]-framer.pos,
                      utf8_pending_bytes=len(utf8.getstate()[0]))
    def aggregate(target,size):
        target["total"]+=size;target["min"]=size if target["min"] is None else min(target["min"],size)
        target["max"]=size if target["max"] is None else max(target["max"],size);target["last"]=size
    try:
        c.gate(deadline);result["raw_open_attempts"]=1;raw=factory();reader=gzip._GzipReader(raw);result["reader_instances"]=1
        snapshot()
        if progress:progress(result)
        while result["returned_bytes"]<return_end:
            c.gate(deadline)
            if result["read_attempts"]==0:
                remaining=deadline-time.monotonic() if deadline is not None else None
                if remaining is not None and remaining<minimum_remaining:raise c.BudgetError("less than minimum activity before first actual read")
                result["entry_admission"]=dict(remaining_seconds=remaining,minimum_remaining_seconds=minimum_remaining)
            request=min(chunk,return_end-result["returned_bytes"]);before=result["returned_bytes"]
            result.update(read_attempts=result["read_attempts"]+1,last_request=request,last_return=None)
            result["last_read"]=dict(index=result["read_attempts"],request_bytes=request,request_offset=before,status="not_returned",returned_bytes=None,start_monotonic=time.monotonic())
            aggregate(result["requests"],request)
            try:data=reader.read(request)
            except BaseException:
                result["last_read"].update(status="raised",end_monotonic=time.monotonic());raise
            c.require(type(data) is bytes and len(data)<=request,"reader returned invalid bounded bytes")
            result.update(last_return=len(data))
            result["last_read"].update(status="returned" if data else "eof",returned_bytes=len(data),end_monotonic=time.monotonic())
            aggregate(result["returns"],len(data));result["returns"]["nonempty" if data else "empty"]+=1
            if not data:c.fault("early_eof","source ended before predetermined returned prefix")
            digest.update(data);result["returned_bytes"]+=len(data)
            if before<old_prefix[0]:
                older.update(data[:old_prefix[0]-before])
                if result["returned_bytes"]>=old_prefix[0]:
                    result["old_prefix_actual_sha256"]=older.hexdigest()
                    result["old_prefix_crosscheck"]=older.hexdigest()==old_prefix[1]
                    if not result["old_prefix_crosscheck"]:c.fault("source_consistency","older same-stream prefix SHA mismatch")
            c.gate(deadline)
            # Slice BEFORE UTF8 decode: suffix receives no text/grammar interpretation.
            parsed=data[:max(0,parse_end-before)]
            if parsed:
                pending=len(utf8.getstate()[0])
                try:decoded=utf8.decode(parsed,final=False)
                except UnicodeDecodeError as error:c.fault("utf8","invalid prefix UTF8",position=before-pending+error.start)
                if framer.pos==0 and decoded.startswith("\ufeff"):c.fault("strict_configuration","leading BOM refused")
                framer.feed(decoded.encode("utf-8"))
            if not result["parser_endpoint_verified"] and result["returned_bytes"]>=parse_end:
                if not (framer.pos==parse_end and framer.last_validated_position==parse_end and census.last_event_end==parse_end
                    and census.count==event_count and framer.unit is None and framer.state=="event_comma" and not utf8.getstate()[0]):
                    c.fault("prefix_endpoint","parse stop is not exact complete event endpoint")
                if census.roles!=expected_roles:c.fault("selection_counts","required selection role counts differ")
                result["parser_endpoint_verified"]=True
            if result["returned_bytes"]>=next_progress:
                if result["progress_updates"]>=64:c.fault("progress_capacity","progress count cap")
                result["progress_updates"]+=1;next_progress+=16*1024**2;snapshot()
                if progress:progress(result)
        c.gate(deadline)
        if digest.hexdigest()!=return_sha:c.fault("source_consistency","returned-prefix SHA mismatch")
        if not result["old_prefix_crosscheck"] or not result["parser_endpoint_verified"]:c.fault("prefix_endpoint","missing prefix checks")
        result["status"]=SUCCESS
    except BaseException as error:
        result.update(first_error=c.error_record(error),first_error_kind=error.kind if isinstance(error,c.StreamError)
            else "resource" if isinstance(error,c.BudgetError) else "container_integrity" if isinstance(error,(gzip.BadGzipFile,EOFError,gzip.zlib.error)) else "io_or_recording")
    finally:
        for label,handle in (("reader",reader),("raw",raw)):
            if handle is None:continue
            result["close_attempts"][label]+=1
            try:handle.close()
            except BaseException as error:
                detail=dict(c.error_record(error),operation=label+".close")
                if result["first_error"] is None:result.update(first_error=detail,first_error_kind="close_io")
                else:result["secondary_errors"].append(detail)
        if result["first_error"] is not None:result["status"]="partial"
        result["closed"]=not result["secondary_errors"] and result["first_error_kind"]!="close_io"
        snapshot();result["finished_monotonic"]=time.monotonic()
    return result,census.records


def controls(gzip, deadline, rule, annotations):
    """All expectations fixed here before the sole window; no huge fixture arrays."""
    rows=[];fixture_bytes=0
    normal=dict(ph="X",name="普通é",pid=1,tid=2,ts=0,dur=1,args={})
    direct=dict(normal,name="not_execution",args={rule["exact_arg_keys"][0]:"jit_reused",rule["exact_arg_keys"][1]:"other"})
    marker=dict(normal,name=annotations[0]);metadata=dict(normal,ph="M",name="thread_name",args={"name":"worker","sort_index":2})
    def run(name, events, expected=SUCCESS, *, suffix=b"\xff INVALID SUFFIX", offset=0, chunk=17,
            old_bad=False, new_bad=False, roles=None, mutate=None, limits=None, sample_limit=58, late=False, close_error=False, io_error=False, return_extra=0, minimum_remaining=0.):
        nonlocal fixture_bytes
        body=b'{"traceEvents":['+b','.join(json.dumps(e,ensure_ascii=False,separators=(',',':')).encode() for e in events)
        fixture_bytes+=len(body)+len(suffix);c.require(fixture_bytes<=65536,"control plaintext fixture budget exceeded")
        compressed=gzip.compress(body+suffix,mtime=0)
        if mutate:compressed=mutate(compressed)
        class Raw(io.BytesIO):
            def read(self,n=-1):
                if io_error:raise OSError("controlled read error")
                return super().read(n)
            def close(self):
                super().close()
                if close_error:raise OSError("controlled close error")
        actual_roles=roles if roles is not None else dict(direct=sum(type(e.get("args")) is dict and any(e["args"].get(k)=="jit_reused" for k in rule["exact_arg_keys"]) and not e.get("name","").startswith("F-TRACE2:") for e in events),
            marker=sum(e.get("name") in annotations for e in events),metadata=sum(e.get("ph")=="M" for e in events))
        old_end=min(11,len(body));wanted_old=hashlib.sha256(body[:old_end]).hexdigest()
        value,records=prefix_stream(gzip,lambda:Raw(compressed),time.monotonic()-1 if late else deadline,rule,annotations,
            parse_end=len(body)+offset,return_end=len(body)+len(suffix)+return_extra,event_count=len(events),
            old_prefix=(old_end,"0"*64 if old_bad else wanted_old),return_sha="0"*64 if new_bad else hashlib.sha256(body+suffix).hexdigest(),
            expected_roles=actual_roles,chunk=chunk,limits=limits,sample_limit=sample_limit,minimum_remaining=minimum_remaining)
        got=value["first_error_kind"] or value["status"]
        c.require(got==expected,name+": unexpected outcome "+str(got))
        c.require(value["close_attempts"]["raw"]==1 and value["close_attempts"]["reader"]==1 or late and value["raw_open_attempts"]==0,name+": lifecycle differs")
        if value["status"]==SUCCESS:
            c.require(value["returned_bytes"]==len(body)+len(suffix) and value["framer_consumed_bytes"]==len(body) and value["utf8_pending_bytes"]==0,name+": endpoints differ")
            c.require(value["last_request"]<=chunk and not value["eof_verified"] and not value["strict_json_complete"],name+": full stream flag differs")
            c.require(value["last_request"]==len(body)+len(suffix)-value["last_read"]["request_offset"]
                and value["last_return"]==value["last_request"] and value["returns"]["empty"]==0
                and value["returns"]["total"]==len(body)+len(suffix),name+": final request/extra read differs")
        if io_error and close_error:c.require(value["secondary_errors"] and value["first_error_kind"]=="io_or_recording",name+": first error overwritten")
        rows.append(dict(name=name,status="pass",expected=expected,actual=got,read_attempts=value["read_attempts"],secondary_error_count=len(value["secondary_errors"])))
        return value,records
    run("exact_endpoint_and_uninterpreted_invalid_suffix",[normal])
    run("endpoint_minus_one",[normal],"prefix_endpoint",offset=-1)
    run("endpoint_plus_one",[normal],"utf8",offset=1)
    run("cross_block_utf8_one_byte_reads",[normal],chunk=1)
    run("old_sha_mismatch",[normal],"source_consistency",old_bad=True)
    run("returned_sha_mismatch",[normal],"source_consistency",new_bad=True)
    run("last_request_narrowed",[normal],chunk=19)
    v,r=run("all_required_roles_conflicting_module",[direct,marker,metadata])
    c.require(r[0]["conflicting_module_keys"]==[rule["exact_arg_keys"][1]],"conflict omitted")
    run("wrong_required_counts",[direct],"selection_counts",roles=dict(direct=0,marker=0,metadata=0))
    both=dict(metadata,args={"name":"worker",rule["exact_arg_keys"][0]:"jit_reused"})
    v,r=run("same_index_multiple_roles",[both]);c.require(r[0]["roles"]==["direct","metadata"],"role dedup differs")
    generic=dict(normal,name=rule["native_names_with_module_arg"][0])
    v,r=run("diagnostic_omission_required_late",[generic,generic,direct],sample_limit=1)
    c.require(v["selection"]["diagnostic_omitted"]==1 and v["selection"]["generic_name_counts"][generic["name"]]==2 and len(r)==2,"diagnostic cap affected required records/count")
    v,r=run("diagnostic_58_full_still_counts",[generic]*59+[direct])
    c.require(v["selection"]["diagnostic_retained"]==58 and v["selection"]["diagnostic_omitted"]==1 and len(r)==59,"58 diagnostic capacity differs")
    v,r=run("retained_records_exact_128",[generic]*58+[metadata]*70)
    c.require(len(r)==128,"exact record capacity differs")
    run("retained_records_over_128",[generic]*58+[metadata]*71,"selection_capacity")
    scalar=dict(metadata,args={"name":None,"sort_index":[1],rule["exact_arg_keys"][0]:{"x":1}})
    v,r=run("missing_null_and_nonscalar_types",[scalar]);fields=r[0]["metadata_and_marker_args"]
    c.require(fields["name"]["type"]=="null" and not fields["sort_index"]["value_retained"] and not fields["graph"]["present"],"missing/type retention differs")
    run("field_text_exact_4096",[dict(metadata,args={"name":"a"*4096})])
    run("field_text_over_4096",[dict(metadata,args={"name":"a"*4097})],"field_text_limit")
    # Exact 16MiB bookkeeping uses tiny strings through the very same retain API.
    for over in (False,True):
        selector=Selection(rule,annotations,c.PARSER_LIMITS,deadline)
        selector.retained_text=c.PARSER_LIMITS["retained_text_bytes"]-1
        try:selector.field({"name":"ab" if over else "a"},"name");got="pass"
        except c.StreamError as error:got=error.kind
        c.require(got==("retained_text_limit" if over else "pass"),"16MiB retained boundary differs")
        rows.append(dict(name="retained_16MiB_"+("over" if over else "exact"),status="pass",actual=got))
    run("early_eof",[normal],"early_eof",suffix=b"",return_extra=1)
    run("bad_trailer_crc",[normal],"container_integrity",suffix=b"",return_extra=1,mutate=lambda b:b[:-8]+bytes([b[-8]^1])+b[-7:],chunk=c.CHUNK)
    run("read_io_and_secondary_close",[normal],"io_or_recording",io_error=True,close_error=True)
    run("success_prefix_close_error",[normal],"close_io",close_error=True)
    run("expired_deadline_no_open",[normal],"resource",late=True)
    admission,_=run("insufficient_first_read_activity",[normal],"resource",minimum_remaining=20.)
    c.require(admission["read_attempts"]==0 and admission["reader_instances"]==1,"first-read admission allowed reading")
    validate_selection(v["selection"],r)
    rows.append(dict(name="saved_selection_roundtrip",status="pass",actual="pass"))
    try:validate_selection(dict(v["selection"],role_counts=dict(direct=1,marker=0,metadata=0)),r)
    except ValueError:rows.append(dict(name="saved_selection_conflict",status="pass",actual="ValueError"))
    else:raise ValueError("saved selection conflict accepted")
    c.require({r['name'] for r in rows}=={name for names in NEW_GROUPS.values() for name in names},"new control grouping differs")
    return dict(status="pass",new_groups=16,groups=NEW_GROUPS,new_subcases=len(rows),fixture_plaintext_bytes=fixture_bytes,rows=rows,
                inherited_saved_subcases=82,inherited_execution=False,
                inheritance_scope="unchanged pinned decoder/framer/count/capacity parts; changed sampling and prefix/selection are new",**c.flags())


def validate_selection(summary,records):
    c.require(len(records)==summary["retained_records"]<=128,"selection retained count differs")
    roles=dict(direct=0,marker=0,metadata=0);seen=set()
    for record in records:
        c.require(record["array_index"] not in seen,"duplicate selected index")
        seen.add(record["array_index"])
        for role in record["roles"]:
            if role in roles:roles[role]+=1
        c.require(record["end_byte_exclusive"]>record["start_byte"] and len(record["unit_sha256"])==64,"selected unit identity differs")
    c.require(roles==summary["role_counts"],"saved selected roles differ")
    c.require(json.loads(json.dumps(records,ensure_ascii=False,allow_nan=False))==records,"selected JSON roundtrip differs")


def source_rows(plan):
    rows={rel:dict(path=rel,bytes=size,sha256=sha,copied=True) for rel,size,sha in FIXED}
    for rel,meta in plan["author_inputs"].items():
        if rel in rows:c.require(all(rows[rel][k]==meta[k] for k in ("bytes","sha256")),"author/core identity differs")
        rows[rel]=dict(path=rel,**meta,copied=True)
    rows[GZIP_REL]=dict(path=GZIP_REL,bytes=GZIP_SIZE,sha256=GZIP_SHA,copied=False)
    return list(rows.values())


def check_sources(repo, root, deadline, *, freeze=False):
    plan=c.read(root/"plan.json");rows=[]
    for item in source_rows(plan):
        c.checked(repo/item["path"],item["bytes"],item["sha256"],deadline,within=repo)
        if item["copied"]:
            target=root/"aux"/item["path"]
            if freeze:
                data=(repo/item["path"]).read_bytes();c.admit_write(target,len(data));target.parent.mkdir(parents=True,exist_ok=True)
                with target.open("xb") as stream:c.require(stream.write(data)==len(data),"short frozen copy");stream.flush();os.fsync(stream.fileno())
            c.checked(target,item["bytes"],item["sha256"],deadline,within=root)
        rows.append(dict(item,status="verified"))
    c.pin_runtime(deadline)
    binding=c.read(repo/(OLD+"receipt_binding.json"));count=c.read(repo/(OLD+"results/stream/count.json"))
    for rel in ("results/stream/count.json","results/stream/census.json","results/stream/controls.json"):
        wanted=next(x for x in source_rows(plan) if x["path"]==OLD+rel)
        c.require(all(binding["records"][rel][k]==wanted[k] for k in ("bytes","sha256")),"FSTREAM binding differs")
    c.require(count["returned_bytes"]==RETURN_END and count["prefix_sha256"]==RETURN_SHA
        and count["last_validated_event_end_byte"]==PARSE_END and count["census"]["event_count"]==EVENTS,"old prefix source differs")
    c.require(c.read(repo/(OLD+"results/stream/census.json"))["census"]==count["census"],"old count/census conflict")
    old=c.read(repo/(TRACE+"receipt_binding.json"));native=c.read(repo/(TRACE+"native_manifest.json"))
    native_item=next(x for x in native["files"] if x["path"]==c.NATIVE[0][0])
    c.require(native_item["bytes"]==GZIP_SIZE and native_item["sha256"]==GZIP_SHA and old["status"]=="observability_not_pass","FTRACE native identity differs")
    for rel in ("input_manifest.json","native_manifest.json","results/trace/summary.json"):
        wanted=next(x for x in source_rows(plan) if x["path"]==TRACE+rel)
        c.require(all(old["records"][rel][k]==wanted[k] for k in ("bytes","sha256")),"FTRACE binding differs")
    inherited=c.read(repo/(OLD+"results/stream/controls.json"))
    c.require(inherited["status"]=="pass" and inherited["subcase_count"]==82,"old control inheritance differs")
    return dict(status="verified",rows=rows,core_source_sha256=CORE_SHA,core_actual_loader_origin=str(core_path),**c.flags())


def verify_saved(root, repo):
    value=c.read(root/"results/stream/count.json");selection=c.read(root/"results/stream/selection.json")
    prior=c.read(repo/(OLD+"results/stream/count.json"))
    for key in CROSS_KEYS:c.require(value["census"][key]==prior["census"][key],"prior census mismatch: "+key)
    c.require(value["status"]==SUCCESS and value["first_error"] is None and value["closed"] and value["parser_endpoint_verified"],"prefix selection not complete")
    c.require(value["returned_bytes"]==RETURN_END and value["prefix_sha256"]==RETURN_SHA and value["framer_consumed_bytes"]==PARSE_END
        and value["old_prefix_crosscheck"] and value["uninterpreted_returned_bytes"]==271250,"saved endpoints/SHA differ")
    c.require(value["selection"]==selection["summary"] and selection["summary"]["role_counts"]==dict(direct=56,marker=5,metadata=9)
        and len(selection["records"])==selection["summary"]["retained_records"]<=128,"saved selection counts differ")
    validate_selection(selection["summary"],selection["records"])
    c.require(all(value[k] is False for k in c.flags()) and all(value[k] is False for k in ("eof_verified","crc_isize_verified","utf8_final_verified","strict_json_complete")),"qualification boundary differs")
    ctrl=c.read(root/"results/prepare/controls.json");c.require(ctrl["status"]=="pass" and ctrl["fixture_plaintext_bytes"]<=65536,"new controls failed")
    return dict(status="verified",scope="predetermined prefix only",crosschecked_census_fields=list(CROSS_KEYS),new_subcases=ctrl["new_subcases"],**c.flags())


def verify_count(value):
    c.require(value['status'] in (SUCCESS,'partial'),'unknown prefix result')
    c.require(value['returned_bytes']<=RETURN_END and value['framer_consumed_bytes']<=PARSE_END,'prefix boundaries exceeded')
    c.require(all(value[k] is False for k in c.flags()),'scientific boundary differs')
    if value['status']==SUCCESS:
        c.require(value['returned_bytes']==RETURN_END and value['prefix_sha256']==RETURN_SHA
            and value['old_prefix_crosscheck'] and value['parser_endpoint_verified']
            and value['closed'] and value['first_error'] is None,'prefix completion lacks gates')
    return dict(status='saved_prefix_structure_verified',scope='predetermined prefix only')


def verify_saved_stream(root,expected,reference,value,ctrl):
    c.require(value['identity']==expected and value['source_reference']==reference,'saved prefix source/identity differs')
    c.require(ctrl['identity']==expected and ctrl['status']=='pass' and ctrl['new_subcases']>=20,'new controls identity/status differs')
    repo=c.extended(c.read(root/'plan.json')['repo'])
    verified=verify_saved(root,repo)
    return dict(verified,status='saved_stream_outcome_verified',source_status='verified',control_status='pass')


def references():
    return [dict(project_relative_path=GZIP_REL,bytes=GZIP_SIZE,sha256=GZIP_SHA,
                 role='saved_gzip_reference',storage_mode='external_read_only_reference',copied=False,decoded=False)]


def child(repo,root,action,deadline,manifest):
    plan=c.read(root/'plan.json');driver=plan['author_inputs']['hf_repo/scripts/'+c.DRIVER]
    phase={'prepare':'P0_prepare','stream':'P1_controls_stream','seal':'P3_seal'}[action]
    expected=identity(phase,manifest,driver['sha256'])
    c.checked(__file__,driver['bytes'],driver['sha256'],deadline)
    events=None;steps=[];payload=None
    summary=dict(identity=expected,status='partial',steps=steps,first_error=None,first_error_kind=None,**c.flags())
    def step(name,fn):
        c.require(name==c.STAGES[action][len(steps)],'stage order differs')
        row=dict(name=name,status='running',started_monotonic=time.monotonic());steps.append(row)
        events.emit('stage_started',stage=name)
        try:result=fn()
        except BaseException as error:
            detail=c.error_record(error);row.update(status='failed',error=detail)
            if summary['first_error'] is None:
                summary.update(first_error=detail,first_error_kind=error.kind if isinstance(error,c.StreamError) else 'resource' if isinstance(error,c.BudgetError) else 'source_or_execution')
            raise
        row.update(status='pass',finished_monotonic=time.monotonic());events.emit('stage_finished',stage=name)
        return result
    try:
        events=c.Events(root,phase,deadline)
        events.emit('started',action=action)
        if action=='prepare':
            c.require(c.digest(root/'plan.json',deadline)==manifest,'plan SHA differs')
            def freeze():
                pre=check_sources(repo,root,deadline,freeze=True);c.write(root/'source_precheck.json',pre)
                c.write(root/'input_manifest.json',dict(protocol=PROTOCOL,run_id=RUN,files=source_rows(plan),**c.flags()))
                c.write(root/'source_refs.json',dict(protocol=PROTOCOL,run_id=RUN,references=references(),**c.flags()))
                rule=c.extract_rule(repo/c.RULE_SOURCE,deadline);c.write(root/'rules_reference.json',rule)
                return rule
            rule=step('source_freeze',freeze)
            def new_controls():
                gzip,runtime=c.actual_runtime(deadline);c.write(root/'runtime_identity.json',runtime)
                result=controls(gzip,deadline,rule['target_rule'],rule['annotations'])
                c.write(root/'results/prepare/controls.json',result)
                return result
            result=step('new_controls',new_controls)
            summary.update(status='pass',input_manifest_sha256=c.digest(root/'input_manifest.json',deadline),new_subcases=result['new_subcases'])
        elif action=='stream':
            def source_binding():
                c.require(c.digest(root/'input_manifest.json',deadline)==manifest,'manifest SHA differs')
                check=check_sources(repo,root,deadline);rule=c.read(root/'rules_reference.json')
                c.require(rule==c.extract_rule(repo/c.RULE_SOURCE,deadline),'rule source identity differs')
                gzip,runtime=c.actual_runtime(deadline)
                ctrl=c.read(root/'results/prepare/controls.json')
                c.require(ctrl['status']=='pass','new P0 controls incomplete')
                c.write(root/'results/stream/controls.json',dict(ctrl,identity=expected))
                return rule,gzip,runtime,check
            rule,gzip,runtime,check=step('source_binding',source_binding)
            def measure():
                def progress(v):
                    c.write(root/'results/stream/progress.json',dict(identity=expected,returned_bytes=v['returned_bytes'],
                        event_count=v['census']['event_count'],parsed_bytes=v['framer_consumed_bytes'],**c.flags()),replace=(root/'results/stream/progress.json').exists())
                value,records=prefix_stream(gzip,lambda:c.safe_path(repo/GZIP_REL,within=repo).open('rb'),deadline,
                    rule['target_rule'],rule['annotations'],parse_end=PARSE_END,return_end=RETURN_END,event_count=EVENTS,
                    old_prefix=(c.PRIOR_PREFIX_BYTES,c.PRIOR_PREFIX_SHA),return_sha=RETURN_SHA,
                    expected_roles=dict(direct=56,marker=5,metadata=9),minimum_remaining=20.,progress=progress)
                summary.update(first_error=value['first_error'],first_error_kind=value['first_error_kind'],stream_outcome=value['status'])
                value.update(identity=expected,source_reference=references()[0])
                errors=[]
                for file,content in (('count.json',value),('selection.json',dict(identity=expected,summary=value['selection'],records=records,**c.flags()))):
                    try:c.write(root/('results/stream/'+file),content)
                    except BaseException as error:
                        errors.append(c.error_record(error))
                        if summary['first_error'] is None:summary.update(first_error=errors[-1],first_error_kind='resource' if isinstance(error,c.BudgetError) else 'recording')
                        else:summary.setdefault('secondary_record_errors',[]).append(errors[-1])
                if errors:raise RuntimeError('saved prefix writer failed; no retry')
                if value['first_error'] is not None:raise RuntimeError('first prefix error preserved; no extra read')
                verify_saved(root,repo)
                return value
            value=step('prefix_selection',measure)
            summary.update(status=SUCCESS,controls_count=16,runtime_status=runtime['status'],source_status=check['status'],stream_outcome=value['status'])
        else:
            issues=[]
            def observed(name,fn):
                try:return fn()
                except BaseException as error:
                    detail=c.error_record(error);issues.append(dict(stage=name,error=detail))
                    if summary['first_error'] is None:summary.update(first_error=detail,first_error_kind='resource' if isinstance(error,c.BudgetError) else 'source_or_execution')
                    return dict(status='not_verified',error=detail)
            post=step('source_postcheck',lambda:observed('source_postcheck',lambda:check_sources(repo,root,deadline)))
            c.write(root/'source_postcheck.json',post)
            resources=c.read(root/'resources.json');must_complete=resources['status']==SUCCESS
            def saved():
                for phase_name in ('P0_prepare','P1_controls_stream'):
                    file=root/('results/'+phase_name+'_supervision/receipt.json')
                    if file.exists():
                        raw=c.read(file)
                        c.require(raw['cleanup_verified'] and not raw['errors'] and raw['supervisor_sha256']==c.SUP_SHA and raw['telemetry_status']=='disabled','saved SUP1 failed')
                        if must_complete:c.require(raw['reason']=='normal_exit' and type(raw['returncode']) is int and raw['returncode']==0,'successful earlier receipt failed')
                    else:c.require(not must_complete,'missing earlier receipt')
                if must_complete:
                    value=c.read(root/'results/stream/count.json');ctrl=c.read(root/'results/stream/controls.json')
                    verified=verify_saved_stream(root,identity('P1_controls_stream',manifest,driver['sha256']),references()[0],value,ctrl)
                    c.require(post['status']=='verified','source postcheck incomplete')
                else:verified=dict(status='not_completed',source_status=post['status'],control_status='not_admitted')
                c.write(root/'diagnostic_verification.json',verified)
                value=c.read(root/'results/stream/count.json') if (root/'results/stream/count.json').exists() else {}
                lines=['Scope: predetermined prefix only; no full JSON/EOF/CRC admission',
                    'Parsed: '+str(value.get('framer_consumed_bytes'))+' bytes / returned: '+str(value.get('returned_bytes')),
                    'Required roles: '+str(value.get('selection',{}).get('role_counts')),
                    'All scientific/force/native/XPlane flags false; producer/fusion observations null']
                c.write_text(root/'selection.svg',c.svg('F-SELECT1 saved-prefix selection',lines))
                return verified
            verified=step('saved_results',lambda:observed('saved_results',saved))
            def seal():
                return {p.relative_to(root).as_posix():c.digest(p,deadline) for p in c.walk_files(root,deadline) if p.relative_to(root).as_posix() not in c.EXCLUSIONS}
            payload=step('payload_manifest',seal)
            summary.update(status='pass' if not issues else 'evidence_failure',issues=issues,
                diagnostic_status=verified['status'],payload_sealed=not issues,stream_outcome=SUCCESS if must_complete else 'partial')
        events.emit('finished',status=summary['status'])
    except BaseException as error:
        if summary['first_error'] is None:summary.update(first_error=c.error_record(error),first_error_kind='resource' if isinstance(error,c.BudgetError) else 'source_or_execution')
        else:summary.setdefault('secondary_record_errors',[]).append(c.error_record(error))
        summary['status']='execution_failure'
    finally:
        try:
            if events is not None:events.close()
        except BaseException as error:
            if summary['first_error'] is None:summary.update(first_error=c.error_record(error),first_error_kind='recording')
            else:summary.setdefault('secondary_record_errors',[]).append(c.error_record(error))
            summary.update(status='execution_failure',payload_sealed=False)
    if payload is not None:
        try:c.write(root/'output_sha256.json',dict(sorted(payload.items())))
        except BaseException as error:
            if summary['first_error'] is None:summary.update(first_error=c.error_record(error),first_error_kind='recording')
            else:summary.setdefault('secondary_record_errors',[]).append(c.error_record(error))
            summary.update(status='execution_failure',payload_sealed=False)
    try:c.write(root/('results/'+action+'/summary.json'),summary)
    except BaseException as error:
        print(json.dumps(dict(protocol=PROTOCOL,phase=phase,status='terminal_summary_write_failed',first_error=summary['first_error'] or c.error_record(error),secondary_error=c.error_record(error))),flush=True)
        return 1
    return 0 if summary['status'] in ('pass',SUCCESS) else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--action',choices=('prepare','stream','seal'));args=parser.parse_args()
    repo,root=c.extended(args.repo),c.extended(args.root)
    c.require(root==repo/'hf4_c2_stable_f_validation'/RUN,'alternate root refused')
    # Reuse the original parent with an explicit new protocol, source locator,
    # targets and saved-result gates. Its budget/cleanup/failure AST is unchanged.
    c._ENTRY_START=START;c.PROTOCOL=PROTOCOL;c.RUN_ID=RUN;c.SUBJECT='saved_prefix_selection';c.SUCCESS=SUCCESS
    c.DRIVER=Path(__file__).name;c.__file__=str(Path(__file__))
    c.DOCS=('docs/F_STREAM1_READONLY_FOLLOWUP_20260930.md','hf_repo/scripts/run_saved_trace_census.py')
    c.CONTROL_GROUPS=tuple(NEW_GROUPS)
    c.STAGES=dict(prepare=('source_freeze','new_controls'),stream=('source_binding','prefix_selection'),seal=('source_postcheck','saved_results','payload_manifest'))
    c.TARGETS=('plan.json','input_manifest.json','source_refs.json','source_precheck.json','rules_reference.json','runtime_identity.json',
        'results/prepare/summary.json','results/prepare/controls.json','results/stream/summary.json','results/stream/controls.json',
        'results/stream/progress.json','results/stream/count.json','results/stream/selection.json','source_postcheck.json','diagnostic_verification.json',
        'selection.svg','resources.json','results/seal/summary.json','results/P0_prepare_supervision/receipt.json',
        'results/P1_controls_stream_supervision/receipt.json','results/P3_seal_supervision/receipt.json',
        'events/P0_prepare.ndjson','events/P1_controls_stream.ndjson','events/P3_seal.ndjson',
        'logs/P0_prepare.log','logs/P1_controls_stream.log','logs/P3_seal.log','output_sha256.json','execution_receipt.json')
    c.identity=identity;c.fixed_references=references;c.verify_count=verify_count;c.verify_saved_stream=verify_saved_stream
    c.EVIDENCE_ROOT=root
    if args.action:
        deadline=float(os.environ['HF_STREAM1_ACTIVE_DEADLINE']);c.require(c.finite(deadline),'nonfinite deadline');c.WRITE_DEADLINE=deadline
        return child(repo,root,args.action,deadline,os.environ['HF_STREAM1_MANIFEST_SHA'])
    c.WRITE_DEADLINE=START+300.
    return c.parent(repo,root)


if __name__=='__main__':
    sys.dont_write_bytecode=True
    try:code=main()
    except BaseException as error:
        print(json.dumps(dict(protocol=PROTOCOL,status='entry_failure',error=c.error_record(error))),flush=True);code=1
    raise SystemExit(code)
