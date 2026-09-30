"""F-CPU-CLEAN1: original workloads and CPU gates under the SUP2 contract."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import windows_owned_process_sup2 as owned
from test_windows_cleanup_contract import (
    assert_cleanup_proof, identity, record_runtime_identity,
)

pytestmark=pytest.mark.skipif(os.name!='nt',reason='Windows Job CPU accounting contract')
CANDIDATE_SHA=hashlib.sha256(Path(owned.__file__).read_bytes()).hexdigest()


def durable_json(path, value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,allow_nan=False,sort_keys=True)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


@pytest.fixture(scope='module',autouse=True)
def bind_loaded_sources():
    record_runtime_identity(__file__,'runtime_identity.json')


def begin_case(tmp_path, role, active_seconds, seconds):
    """Fix the deadline before authoring/creating a child; never reset at ready."""
    started=time.monotonic()
    try:
        phase_deadline=float(os.environ['HF_CPU_S1_ACTIVE_DEADLINE'])
        if not math.isfinite(phase_deadline):
            raise ValueError('P1 active deadline must be finite')
        record=dict(schema='hf-cpu-s1-budget-1',role=role,
                    identity=identity(role),request_monotonic=started,
                    phase_active_deadline=phase_deadline,
                    deadline_monotonic=started+active_seconds,seconds=seconds,
                    local_active_seconds=active_seconds,
                    cleanup_reserve_seconds=5.25,persist_reserve_seconds=1.,
                    remaining_at_request=phase_deadline-started,
                    required_remaining_seconds=active_seconds+6.25)
    except BaseException as error:
        durable_json(tmp_path/'budget_rejection.json',
                     dict(role=role,request_monotonic=started,status='invalid_budget',
                          exception_type=type(error).__name__,message=str(error)))
        raise
    record['ready_for_launch']=record['remaining_at_request']>=record['required_remaining_seconds']
    durable_json(tmp_path/'invocation_budget.json',record)
    if not record['ready_for_launch']:
        durable_json(tmp_path/'budget_rejection.json',
                     dict(record,status='insufficient_phase_budget',child_started=False))
        pytest.fail('P1 remaining budget cannot contain the complete synthetic scenario')
    return record


def environment():
    value=os.environ.copy()
    scripts=str(Path(owned.__file__).resolve().parent)
    value.update(PYTHONPATH=scripts+(os.pathsep+value['PYTHONPATH']
                                   if value.get('PYTHONPATH') else ''),
                 PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
    return value


def marker_preamble(filename, role, frozen_identity):
    """Child-only standard-library logging, before importing the supervisor."""
    return (
        "import json,os,time\nfrom pathlib import Path\n"
        "from datetime import datetime,timezone\n"
        f"_identity={frozen_identity!r}\n_role={role!r}\n"
        "if (os.environ['HF_S0_SOURCE_MANIFEST_SHA']!=_identity['source_manifest_sha256']"
        " or os.environ['HF_HARNESS_MANIFEST_SHA']!=_identity['harness_manifest_sha256']"
        " or os.environ['HF_HARNESS_ID']!=_identity['harness_id']):"
        " raise ValueError('child identity mismatch')\n"
        f"_markers=Path({filename!r}).open('x',encoding='utf-8',newline='\\n')\n_seq=0\n"
        "def mark(event,**fields):\n"
        "    global _seq\n"
        "    row=dict(schema='hf-cpu-s1-marker-1',sequence=_seq+1,"
        "utc=datetime.now(timezone.utc).isoformat(),monotonic=time.monotonic(),"
        "pid=os.getpid(),role=_role,identity=_identity,event=event,**fields)\n"
        "    _markers.write(json.dumps(row,allow_nan=False,separators=(',',':'))+'\\n')\n"
        "    _markers.flush();os.fsync(_markers.fileno());_seq+=1\n"
        "    return row\n"
        "def save_json(name,value):\n"
        "    with Path(name).open('x',encoding='utf-8',newline='\\n') as stream:\n"
        "        json.dump(value,stream,allow_nan=False,sort_keys=True)\n"
        "        stream.write('\\n');stream.flush();os.fsync(stream.fileno())\n"
        "mark('script_enter')\n"
    )


def workload(kind, seconds):
    action=("while time.monotonic()<_work_start+"+repr(seconds)+": pass\n"
            if kind=='busy' else "time.sleep("+repr(seconds)+")\n")
    return (f"mark('{kind}_started')\n_work_start=time.monotonic()\n"+action+
            "_work_end=time.monotonic()\n"
            f"mark('{kind}_finished',actual_start_monotonic=_work_start,"
            "actual_end_monotonic=_work_end)\n")


def invoke(tmp_path, code, budget):
    command=[sys.executable,'-u','-B','-c',code]
    request=dict(budget,schema='hf-cpu-s1-request-1',command=command,
                 command_sha256=hashlib.sha256(json.dumps(command).encode('utf-8')).hexdigest(),
                 invocation_monotonic=time.monotonic())
    durable_json(tmp_path/'request.json',request)
    try:
        receipt=owned.run_owned(command,cwd=str(tmp_path),env=environment(),
            log=tmp_path/'child.log',deadline=budget['deadline_monotonic'],
            seconds=budget['seconds'],telemetry_path=tmp_path/'cpu.ndjson',
            telemetry_identity=budget['identity'],telemetry_interval_seconds=.05,
            instance_identity=budget['identity'])
    except BaseException as error:
        durable_json(tmp_path/'call_outcome.json',
                     dict(role=budget['role'],status='raised',returned_monotonic=time.monotonic(),
                          exception_type=type(error).__name__,message=str(error)))
        raise
    returned=time.monotonic()
    durable_json(tmp_path/'receipt.json',receipt)
    durable_json(tmp_path/'call_outcome.json',
                 dict(role=budget['role'],status='returned',returned_monotonic=returned,
                      receipt_path='receipt.json'))
    return receipt


def records(path, receipt, expected_identity):
    payload=Path(path).read_bytes()
    assert payload.endswith(b'\n')
    values=[json.loads(line) for line in payload.splitlines()]
    assert values
    assert [row['sequence'] for row in values]==list(range(1,len(values)+1))
    assert receipt['supervisor_sha256']==CANDIDATE_SHA
    for row in values:
        assert row['schema']==owned.CPU_SCHEMA
        assert row['identity']==dict(expected_identity,supervisor_sha256=CANDIDATE_SHA)
        assert row['query_start_monotonic']<=row['query_end_monotonic']
        assert row['total_user_time_100ns']>=0 and row['total_kernel_time_100ns']>=0
        assert 0<=row['ActiveProcesses']<=row['TotalProcesses']
        assert row['total_user_seconds']==row['total_user_time_100ns']/10_000_000
        assert row['total_kernel_seconds']==row['total_kernel_time_100ns']/10_000_000
        assert row['cpu_scope']==owned.CPU_SCOPE
    for left,right in zip(values,values[1:]):
        assert left['query_end_monotonic']<=right['query_start_monotonic']
        for key in ('total_user_time_100ns','total_kernel_time_100ns','TotalProcesses'):
            assert right[key]>=left[key]
    assert values[0]['lifecycle']=='initial_before_resume'
    assert values[0]['ActiveProcesses']==1
    return values


def markers(path, expected_identity, receipt):
    payload=Path(path).read_bytes()
    assert payload.endswith(b'\n')
    rows=[json.loads(line) for line in payload.splitlines()]
    assert rows and rows[0]['event']=='script_enter'
    assert rows[-1]['event']=='normal_exit'
    assert [row['sequence'] for row in rows]==list(range(1,len(rows)+1))
    assert len({row['pid'] for row in rows})==1
    assert rows[0]['pid'] in receipt['owned_pids']
    for row in rows:
        assert row['schema']=='hf-cpu-s1-marker-1'
        assert row['identity']==expected_identity
        assert row['role']==expected_identity['role']
    assert all(a['monotonic']<=b['monotonic'] for a,b in zip(rows,rows[1:]))
    return rows


def event(rows, name):
    selected=[row for row in rows if row['event']==name]
    assert len(selected)==1
    return selected[0]


def work_rows(cpu_rows, marker_rows, kind):
    started=event(marker_rows,kind+'_started')
    finished=event(marker_rows,kind+'_finished')
    begin=finished['actual_start_monotonic'];end=finished['actual_end_monotonic']
    assert started['monotonic']<=begin<end<=finished['monotonic']
    # All fully contained records; never choose a favorable subinterval.
    selected=[row for row in cpu_rows if row['query_start_monotonic']>=begin
              and row['query_end_monotonic']<=end]
    assert len(selected)>=2
    return selected


def cpu(row):
    return row['total_user_time_100ns']+row['total_kernel_time_100ns']


def assert_clean(receipt, *, evidence_path, receipt_path, expected_identity):
    proof=assert_cleanup_proof(receipt)
    base=Path(evidence_path).parent.resolve()
    evidence=dict(schema='hf-cpu-clean1-proof-check-1',protocol='F-CPU-CLEAN1',
                  identity=expected_identity,candidate_supervisor_sha256=CANDIDATE_SHA,
                  cleanup_proof=proof)
    for prefix,path in [('receipt',Path(receipt_path)),('cpu',Path(receipt['telemetry_path']))]:
        resolved=path.resolve();payload=resolved.read_bytes()
        evidence[prefix+'_path']=str(resolved.relative_to(base))
        evidence[prefix+'_sha256']=hashlib.sha256(payload).hexdigest()
        evidence[prefix+'_bytes']=len(payload)
    durable_json(evidence_path,evidence)


def test_busy_sleep_and_exited_descendant_keep_cumulative_cpu(tmp_path):
    budget=begin_case(tmp_path,'busy_outer',25.,25.)
    child_identity=identity('descendant')
    child_code=(marker_preamble('descendant_markers.ndjson','descendant',child_identity)+
                workload('busy',.5)+"mark('normal_exit')\n_markers.close()\n")
    outer_deadline=budget['deadline_monotonic']
    code=(marker_preamble('outer_markers.ndjson','busy_outer',budget['identity'])+
        "import sys\nfrom windows_owned_process_sup2 import run_owned\n"
        "mark('supervisor_imported')\n"+workload('busy',.65)+workload('sleep',.65)+
        f"_outer_deadline={outer_deadline!r}\n"
        "_tn=time.monotonic()\n_phase_deadline=float(os.environ['HF_CPU_S1_ACTIVE_DEADLINE'])\n"
        f"_child_command=[sys.executable,'-u','-B','-c',{child_code!r}]\n"
        "_nested_deadline=min(_tn+8.,_outer_deadline-7.)\n"
        f"_child_identity={child_identity!r}\n"
        "_request=dict(schema='hf-cpu-s1-request-1',role='descendant',"
        "identity=_child_identity,request_monotonic=_tn,phase_active_deadline=_phase_deadline,"
        "outer_deadline_monotonic=_outer_deadline,deadline_monotonic=_nested_deadline,"
        "seconds=8.,local_active_seconds=8.,cleanup_reserve_seconds=5.25,"
        "persist_reserve_seconds=1.,outer_tail_reserve_seconds=7.,command=_child_command)\n"
        "_request['ready_for_launch']=(_tn+8.<=_outer_deadline-7."
        " and _phase_deadline-_tn>=14.25)\n"
        "save_json('descendant_request.json',_request)\n"
        "if not _request['ready_for_launch']:\n"
        "    save_json('descendant_budget_rejection.json',dict(_request,"
        "status='insufficient_nested_budget',child_started=False))\n"
        "    raise RuntimeError('complete nested activity and cleanup budget unavailable')\n"
        "mark('descendant_requested',request_monotonic=_tn,deadline_monotonic=_nested_deadline)\n"
        "try:\n"
        "    child=run_owned(_child_command,cwd=os.getcwd(),env=os.environ.copy(),"
        "log='descendant.log',deadline=_nested_deadline,seconds=8.,"
        "telemetry_path='descendant_cpu.ndjson',telemetry_identity=_child_identity,"
        "telemetry_interval_seconds=.05,instance_identity=_child_identity)\n"
        "except BaseException as error:\n"
        "    save_json('descendant_call_outcome.json',dict(role='descendant',status='raised',"
        "returned_monotonic=time.monotonic(),exception_type=type(error).__name__,message=str(error)))\n"
        "    raise\n"
        "_returned=time.monotonic()\n"
        "save_json('descendant_receipt.json',child)\n"
        "save_json('descendant_call_outcome.json',dict(role='descendant',status='returned',"
        "returned_monotonic=_returned,receipt_path='descendant_receipt.json'))\n"
        "mark('descendant_returned',returned_monotonic=_returned)\n"
        "if (child['reason']!='normal_exit' or child['returncode']!=0"
        " or not child['cleanup_verified'] or child['telemetry_status']!='complete'"
        " or child['telemetry_first_error'] is not None or child['errors']):\n"
        "    raise RuntimeError('nested scenario did not complete normally; receipt preserved')\n"
        "time.sleep(.35)\nmark('normal_exit')\n_markers.close()\n")
    receipt=invoke(tmp_path,code,budget)
    assert receipt['reason']=='normal_exit' and receipt['returncode']==0
    assert receipt['telemetry_status']=='complete' and receipt['telemetry_first_error'] is None
    assert not receipt['errors']
    assert_clean(receipt,evidence_path=tmp_path/'cleanup_check.json',
                 receipt_path=tmp_path/'receipt.json',expected_identity=budget['identity'])
    values=records(tmp_path/'cpu.ndjson',receipt,budget['identity'])
    outer_markers=markers(tmp_path/'outer_markers.ndjson',budget['identity'],receipt)
    busy_rows=work_rows(values,outer_markers,'busy')
    sleep_rows=work_rows(values,outer_markers,'sleep')
    busy_delta=cpu(busy_rows[-1])-cpu(busy_rows[0])
    sleep_delta=cpu(sleep_rows[-1])-cpu(sleep_rows[0])
    child=json.loads((tmp_path/'descendant_receipt.json').read_text(encoding='utf-8'))
    assert child['reason']=='normal_exit' and child['returncode']==0
    assert child['telemetry_status']=='complete' and child['telemetry_first_error'] is None
    assert not child['errors']
    assert_clean(child,evidence_path=tmp_path/'descendant_cleanup_check.json',
                 receipt_path=tmp_path/'descendant_receipt.json',expected_identity=child_identity)
    parent_rows=receipt['cleanup_proof']['identities']
    child_keys={(row['pid'],row['creation_filetime']) for row in child['cleanup_proof']['identities']}
    parent_keys={(row['pid'],row['creation_filetime']) for row in parent_rows}
    assert child_keys<=parent_keys
    assert any((row['pid'],row['creation_filetime']) in child_keys
               and row['handle_kind']=='owned_observation' and row['handle_closed']
               and row['handle_closed_monotonic']<receipt['cleanup_requested_monotonic']
               for row in parent_rows)
    child_rows=records(tmp_path/'descendant_cpu.ndjson',child,child_identity)
    child_markers=markers(tmp_path/'descendant_markers.ndjson',child_identity,child)
    inner_busy_rows=work_rows(child_rows,child_markers,'busy')
    inner_job_delta=cpu(child_rows[-1])-cpu(child_rows[0])
    nested_request=json.loads((tmp_path/'descendant_request.json').read_text(encoding='utf-8'))
    returned=event(outer_markers,'descendant_returned')['monotonic']
    normal_exit=event(outer_markers,'normal_exit')['monotonic']
    before=[row for row in values if row['lifecycle']=='periodic'
            and row['query_end_monotonic']<=nested_request['request_monotonic']]
    after=[row for row in values if row['lifecycle']=='periodic'
           and row['query_start_monotonic']>=returned
           and row['query_end_monotonic']<normal_exit
           and row['query_end_monotonic']<receipt['cleanup_requested_monotonic']]
    assert before and after
    baseline=before[-1]
    outer_descendant_delta=cpu(after[-1])-cpu(baseline)
    durable_json(tmp_path/'cpu_comparison.json',
        dict(busy_rows=busy_rows,sleep_rows=sleep_rows,inner_busy_rows=inner_busy_rows,
             busy_delta_ticks=busy_delta,sleep_delta_ticks=sleep_delta,
             inner_job_delta_ticks=inner_job_delta,outer_descendant_delta_ticks=outer_descendant_delta,
             before_records=before,after_records=after,baseline_sequence=baseline['sequence']))
    assert busy_delta>200_000 and busy_delta>sleep_delta
    assert inner_job_delta>200_000
    assert all(row['ActiveProcesses']>0 and row['TotalProcesses']>baseline['TotalProcesses']
               for row in after)
    assert outer_descendant_delta>=inner_job_delta
    assert child['pid'] in receipt['owned_pids']
    assert values[-1]['lifecycle']=='final_after_cleanup' and values[-1]['ActiveProcesses']==0
    assert values[-1]['TotalProcesses']>baseline['TotalProcesses']
    assert all(row['query_start_monotonic']>=receipt['cleanup_requested_monotonic']
               for row in values if row['lifecycle'] in ('pre_cleanup','final_after_cleanup'))


def test_timeout_preserves_partial_samples_and_cleans_job(tmp_path):
    budget=begin_case(tmp_path,'timeout',3.,8.)
    code=(marker_preamble('timeout_markers.ndjson','timeout',budget['identity'])+
          "time.sleep(20)\nmark('normal_exit')\n_markers.close()\n")
    receipt=invoke(tmp_path,code,budget)
    assert receipt['reason']=='global_deadline'
    assert receipt['telemetry_status']=='complete' and receipt['telemetry_first_error'] is None
    assert not receipt['errors']
    assert_clean(receipt,evidence_path=tmp_path/'cleanup_check.json',
                 receipt_path=tmp_path/'receipt.json',expected_identity=budget['identity'])
    values=records(tmp_path/'cpu.ndjson',receipt,budget['identity'])
    assert any(row['lifecycle']=='periodic' for row in values)
    assert values[-2]['lifecycle']=='pre_cleanup'
    assert values[-1]['lifecycle']=='final_after_cleanup'
    assert values[-1]['ActiveProcesses']==0 and values[-1]['cleanup_verified'] is True
    assert values[-2]['query_start_monotonic']>=receipt['cleanup_requested_monotonic']


@pytest.mark.parametrize('fault',['query','write'])
def test_observation_failure_stops_and_independent_cleanup_survives(tmp_path,monkeypatch,fault):
    budget=begin_case(tmp_path,'fault_'+fault,7.,8.)
    calls=[]
    if fault=='query':
        original=owned._query_cpu_accounting
        def broken(kernel,job):
            calls.append(dict(interface='query',index=len(calls)+1,monotonic=time.monotonic()))
            if len(calls)==2:
                raise OSError('declared synthetic CPU query failure')
            return original(kernel,job)
        monkeypatch.setattr(owned,'_query_cpu_accounting',broken)
    else:
        original=owned._write_cpu_record
        def broken(stream,record):
            calls.append(dict(interface='write',index=len(calls)+1,monotonic=time.monotonic(),
                              sequence=record['sequence'],lifecycle=record['lifecycle']))
            if len(calls)==2:
                raise OSError('declared synthetic CPU write failure')
            return original(stream,record)
        monkeypatch.setattr(owned,'_write_cpu_record',broken)
    code=(marker_preamble('fault_markers.ndjson','fault_'+fault,budget['identity'])+
          "time.sleep(20)\nmark('normal_exit')\n_markers.close()\n")
    try:
        receipt=invoke(tmp_path,code,budget)
    finally:
        durable_json(tmp_path/'fault_calls.json',
                     dict(fault=fault,count=len(calls),calls=calls,identity=budget['identity']))
    assert receipt['reason']=='supervision_error' and receipt['telemetry_status']=='failed'
    assert receipt['errors']
    assert receipt['telemetry_first_error']['type']=='OSError'
    assert receipt['telemetry_first_error']['lifecycle']=='periodic'
    assert 'synthetic CPU '+fault+' failure' in receipt['telemetry_first_error']['message']
    assert_clean(receipt,evidence_path=tmp_path/'cleanup_check.json',
                 receipt_path=tmp_path/'receipt.json',expected_identity=budget['identity'])
    assert [row['interface'] for row in calls]==[fault,fault]
    values=records(tmp_path/'cpu.ndjson',receipt,budget['identity'])
    assert len(values)==1 and values[0]['lifecycle']=='initial_before_resume'
