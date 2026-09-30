"""CLEAN1 controlled contract cases; execution belongs to the single campaign."""
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import windows_owned_process_sup2 as owned

PARENT_SHA='9f3da2f22bec869d069278058aa8502bd5f73c4b977b01ec5daa7b26ff1aec32'
pytestmark=pytest.mark.skipif(os.name!='nt',reason='Windows SUP2 cleanup contract')


def durable_json(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,allow_nan=False,sort_keys=True)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())


def identity(role):
    source=os.environ['HF_S0_SOURCE_MANIFEST_SHA']
    harness=os.environ['HF_HARNESS_MANIFEST_SHA']
    for digest in (source,harness):
        if len(digest)!=64 or any(letter not in '0123456789abcdef' for letter in digest):
            raise ValueError('invalid frozen manifest SHA')
    if source!=harness or os.environ['HF_HARNESS_ID']!='CPU-CLEAN1':
        raise ValueError('CPU-CLEAN1 manifest/harness identity mismatch')
    return dict(source_manifest_sha256=source,harness_manifest_sha256=harness,
                harness_id='CPU-CLEAN1',version='SUP2',source_version='SUP2',
                phase=os.environ['HF_S0_PHASE'],role=role)


def record_runtime_identity(test_file,output_name):
    test=Path(test_file).resolve()
    scripts=test.parents[1]/'scripts'
    candidate=Path(owned.__file__).resolve()
    parent=(scripts/'windows_owned_process.py').resolve()
    loaded_parent=Path(os.environ['HF_CLEAN1_PARENT_PATH']).resolve()
    def source(path,version):
        return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    version=version)
    data=dict(schema='hf-cpu-clean1-runtime-identity-1',protocol='F-CPU-CLEAN1',
              run_id='cpu_cleanup_contract_001',
              parent_supervisor=source(parent,'SUP1'),
              candidate_supervisor=source(candidate,'SUP2'),
              loaded_parent_supervisor=source(loaded_parent,'SUP1'),
              loaded_parent_provenance='actual parent path declared by campaign runner; bytes checked here',
              test_path=str(test),test_sha256=hashlib.sha256(test.read_bytes()).hexdigest(),
              **identity('pytest_module'))
    data.update(supervisor_path=str(candidate),
                supervisor_sha256=data['candidate_supervisor']['sha256'],
                supervisor_sha256_role='candidate')
    durable_json(Path(os.environ['HF_CPU_S1_RESULT_DIR'])/output_name,data)
    assert candidate==(scripts/'windows_owned_process_sup2.py').resolve()
    assert data['candidate_supervisor']['sha256']==os.environ['HF_CLEAN1_CANDIDATE_SHA']
    assert data['parent_supervisor']['sha256']==PARENT_SHA==os.environ['HF_CLEAN1_PARENT_SHA']
    assert data['loaded_parent_supervisor']['sha256']==PARENT_SHA


@pytest.fixture(scope='module',autouse=True)
def bind_contract_sources():
    record_runtime_identity(__file__,'runtime_identity_contract.json')


def assert_cleanup_proof(receipt):
    """Test-side assertions on raw evidence, separate from SUP2's predicate."""
    assert receipt['cleanup_verified']
    assert receipt['cleanup_requested_monotonic'] is not None
    assert receipt['pid'] in receipt['owned_pids']
    assert receipt['cleanup_contract']=='CPU-CLEAN1'
    assert receipt['protocol']=='F-CPU-CLEAN1'
    candidate=receipt['candidate_supervisor']
    assert candidate==dict(version='SUP2',path=str(Path(owned.__file__).resolve()),
                           sha256=os.environ['HF_CLEAN1_CANDIDATE_SHA'])
    assert receipt['supervisor_sha256']==candidate['sha256']
    proof=receipt['cleanup_proof']
    assert proof['pass'] is True
    assert proof['coverage_verified'] is True and proof['termination_verified'] is True
    assert proof['observation_handles_closed'] is True and proof['job_handle_closed'] is True
    assert proof['errors']==[]
    assert proof['final_accounting']['ActiveProcesses']==0
    assert proof['root_wait_completed'] is True
    assert proof['root_handle_close_verified'] is True
    rows=proof['identities']
    keys={(row['pid'],row['creation_filetime']) for row in rows}
    assert len(keys)==len(rows)==proof['unique_bound_identity_count']
    assert len(rows)==proof['signaled_identity_count']==proof['final_accounting']['TotalProcesses']
    assert rows and any(row['pid']==receipt['pid'] and row['handle_kind']=='borrowed_root'
                        for row in rows)
    for row in rows:
        assert isinstance(row['creation_filetime'],int) and row['creation_filetime']>0
        assert row['signaled'] is True and row['handle_closed'] is True
        assert row['bound_monotonic']<=row['signaled_monotonic']<=row['handle_closed_monotonic']
        assert row['handle_closed_monotonic']<=receipt['cleanup_deadline_monotonic']
    journal=proof['journal']
    assert journal['closed'] is True and journal['failed'] is False
    payload=Path(journal['path']).read_bytes()
    assert len(payload)==journal['bytes']<=16*1024*1024
    assert hashlib.sha256(payload).hexdigest()==journal['sha256']
    return proof


class FakeClock:
    def __init__(self):
        self.now=100.
        self.sleeps=[]
    def __call__(self):
        return self.now
    def sleep(self,seconds):
        if seconds<0:
            raise AssertionError('negative synthetic wait')
        self.sleeps.append(seconds)
        self.now+=seconds


class FakeNative:
    """Only the declared control seam; no OS objects or runtime PID queries."""
    def __init__(self,clock):
        self.clock=clock
        self.objects={}
        self.handles={}
        self.closed=set()
        self.faults=set()
        self.calls=[]
        self.next_handle=1000
    def add(self,pid,creation,*,wait=258,in_job=True,exit_code=125):
        self.objects[pid]=dict(pid=pid,creation=creation,wait=wait,in_job=in_job,exit_code=exit_code)
    def borrow(self,pid):
        self.next_handle+=1
        self.handles[self.next_handle]=self.objects[pid]
        return self.next_handle
    def _record(self,operation,*,pid=None,handle=None,**fields):
        if handle is not None:
            if handle in self.closed:
                raise AssertionError('control double-close or use-after-close')
            pid=self.handles[handle]['pid']
        row=dict(operation=operation,pid=pid,handle=handle,monotonic=self.clock(),**fields)
        self.calls.append(row)
        if (operation,pid) in self.faults:
            row['error']='declared '+operation+' failure'
            raise OSError(row['error'])
        return row
    def open(self,pid):
        row=self._record('open',pid=pid)
        handle=self.borrow(pid);row['return_value']=handle
        return handle
    def is_in_job(self,handle):
        self._record('is_in_job',handle=handle)
        return self.handles[handle]['in_job']
    def creation_time(self,handle):
        self._record('creation_time',handle=handle)
        return self.handles[handle]['creation']
    def wait(self,handle):
        row=self._record('wait',handle=handle)
        row['return_value']=self.handles[handle]['wait']
        return row['return_value']
    def close(self,handle):
        self._record('close',handle=handle)
        self.closed.add(handle)


class ControlCase:
    def __init__(self,tmp_path,*,root_signaled=True,observer_limit=64,history_limit=256):
        self.path=tmp_path/'control_result.json'
        self.clock=FakeClock()
        self.native=FakeNative(self.clock)
        self.events=[]
        self.proof=owned._InstanceProof(self.native,self.emit,clock=self.clock,
                                       observer_limit=observer_limit,history_limit=history_limit)
        self.native.add(101,10001,wait=0 if root_signaled else 258,exit_code=0)
        self.root=self.native.borrow(101)
        self.proof.bind_root(101,self.root)
        self.root_finished=root_signaled
        if root_signaled:
            self.proof.sweep()
            self.proof.note_root_wait(0,begin=self.clock(),end=self.clock())
            self.proof.note_root_closed()
    def emit(self,event,**fields):
        row=dict(fields)
        row.setdefault('monotonic',self.clock())
        row['event']=event
        self.events.append(row)
    def finish(self,total,active=0):
        return self.proof.finish(dict(ActiveProcesses=active,TotalProcesses=total),
            root_wait_completed=self.root_finished,root_handle_closed=self.root_finished)
    def save(self,result,**fields):
        durable_json(self.path,dict(schema='hf-clean1-controlled-case-1',
            protocol='F-CPU-CLEAN1',case_role='controlled_interface_substitute',
            case_kind='controlled_interface',
            nodeid=os.environ['PYTEST_CURRENT_TEST'].rsplit(' ',1)[0],
            identity=identity('controlled_case'),proof=result,events=self.events,
            native_calls=self.native.calls,closed_handles=sorted(self.native.closed),
            native_objects=list(self.native.objects.values()),
            elapsed_synthetic_seconds=self.clock.now-100.,sleeps=self.clock.sleeps,**fields))


def test_active_zero_with_history_gap_fails_closed(tmp_path):
    case=ControlCase(tmp_path)
    result=case.finish(total=2)
    case.save(result)
    assert result['final_accounting']['ActiveProcesses']==0
    assert result['unique_bound_identity_count']==1 and result['signaled_identity_count']==1
    assert result['pass'] is False


def test_duplicate_identity_does_not_inflate_coverage(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002,wait=0)
    case.proof.discover([202],assigned_count=1);case.proof.sweep()
    case.proof.discover([202],assigned_count=1);case.proof.sweep()
    result=case.finish(total=2)
    case.save(result)
    assert result['pass'] is True and result['unique_bound_identity_count']==2
    assert len([r for r in case.native.calls if r['operation']=='open' and r['pid']==202])==2
    assert len({(r['pid'],r['creation_filetime']) for r in result['identities']})==2


def test_reused_pid_with_new_creation_time_is_bound(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002,wait=0)
    case.proof.discover([202],assigned_count=1);case.proof.sweep()
    case.native.add(202,20003,wait=0)
    case.proof.discover([202],assigned_count=1);case.proof.sweep()
    result=case.finish(total=3)
    case.save(result)
    assert result['pass'] is True and result['unique_bound_identity_count']==3
    assert {(r['pid'],r['creation_filetime']) for r in result['identities']}=={
        (101,10001),(202,20002),(202,20003)}


def test_wrong_job_cannot_fill_coverage(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002,in_job=False)
    with pytest.raises(owned.InstanceProofError):
        case.proof.discover([202],assigned_count=1)
    result=case.finish(total=2)
    case.save(result)
    assert result['pass'] is False and result['unique_bound_identity_count']==1
    assert case.proof.errors
    opened=[r['return_value'] for r in case.native.calls if r['operation']=='open']
    assert opened and set(opened)<=case.native.closed


def test_open_failure_is_recorded_without_false_coverage(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002);case.native.faults.add(('open',202))
    with pytest.raises(owned.InstanceProofError):
        case.proof.discover([202],assigned_count=1)
    result=case.finish(total=2)
    case.save(result)
    assert result['pass'] is False and result['unique_bound_identity_count']==1
    assert case.proof.errors
    assert any(r['operation']=='open' and r.get('error') for r in case.native.calls)
    assert not any(r['operation']=='close' and r['pid']==202 for r in case.native.calls)


def test_creation_time_failure_releases_opened_handle(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002);case.native.faults.add(('creation_time',202))
    with pytest.raises(owned.InstanceProofError):
        case.proof.discover([202],assigned_count=1)
    result=case.finish(total=2)
    case.save(result)
    assert result['pass'] is False and result['unique_bound_identity_count']==1
    assert case.proof.errors
    opened=[r['return_value'] for r in case.native.calls if r['operation']=='open']
    assert len(opened)==1 and opened[0] in case.native.closed


def test_wait_failure_does_not_prove_termination(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002);case.native.faults.add(('wait',202))
    case.proof.discover([202],assigned_count=1);case.proof.sweep()
    case.proof.release_remaining()
    result=case.finish(total=2)
    case.save(result)
    assert result['pass'] is False and case.proof.errors
    row=next(r for r in result['identities'] if r['pid']==202)
    assert row['signaled'] is False
    assert any(r['operation']=='close' and r['pid']==202 for r in case.native.calls)


def test_close_failure_does_not_skip_other_handles(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002,wait=0);case.native.add(203,20003,wait=0)
    case.native.faults.add(('close',202))
    case.proof.discover([202,203],assigned_count=2);case.proof.sweep()
    result=case.finish(total=3)
    case.save(result)
    assert result['pass'] is False and case.proof.errors
    first=next(r for r in result['identities'] if r['pid']==202)
    other=next(r for r in result['identities'] if r['pid']==203)
    assert first['handle_closed'] is False
    assert other['signaled'] is True and other['handle_closed'] is True
    assert any(r['operation']=='close' and r['pid']==203 for r in case.native.calls)


def test_timeout_with_exit_code_125_is_not_termination(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002,wait=258,exit_code=125)
    case.proof.discover([202],assigned_count=1);case.proof.sweep()
    case.proof.release_remaining()
    result=case.finish(total=2)
    case.save(result,exit_code_is_not_a_signal_oracle=125)
    assert result['pass'] is False and result['signaled_identity_count']==1
    row=next(r for r in result['identities'] if r['pid']==202)
    assert row['signaled'] is False


def test_capacity_exhaustion_fails_closed(tmp_path):
    case=ControlCase(tmp_path,observer_limit=1)
    case.native.add(202,20002);case.native.add(203,20003)
    with pytest.raises(owned.InstanceProofError):
        case.proof.discover([202,203],assigned_count=2)
    case.proof.release_remaining()
    result=case.finish(total=3)
    case.save(result)
    assert result['pass'] is False and case.proof.errors
    assert result['unique_bound_identity_count']<3


def test_multiple_handles_share_one_cleanup_deadline(tmp_path):
    case=ControlCase(tmp_path,root_signaled=False)
    case.native.add(202,20002);case.native.add(203,20003)
    case.proof.discover([202,203],assigned_count=2)
    deadline=case.clock()+.03
    def accounting():
        case.native.calls.append(dict(operation='accounting',monotonic=case.clock()))
        return dict(ActiveProcesses=3,TotalProcesses=3)
    case.proof.drain(deadline,accounting,case.clock.sleep)
    case.proof.release_remaining()
    result=case.finish(total=3,active=3)
    case.save(result,shared_absolute_deadline=deadline)
    assert result['pass'] is False
    assert 0<=case.clock.now-100.<=.030000001
    assert sum(case.clock.sleeps)<=.030000001
    assert {r['pid'] for r in case.native.calls if r['operation']=='wait'}=={101,202,203}
    assert all(r['monotonic']<=deadline+1e-9 for r in case.native.calls)


def test_signaled_handle_is_released_before_accounting(tmp_path):
    case=ControlCase(tmp_path)
    case.native.add(202,20002,wait=0)
    case.proof.discover([202],assigned_count=1)
    def accounting():
        case.native.calls.append(dict(operation='accounting',monotonic=case.clock()))
        return dict(ActiveProcesses=0,TotalProcesses=2)
    case.proof.drain(case.clock()+.03,accounting,case.clock.sleep)
    result=case.finish(total=2)
    case.save(result)
    assert result['pass'] is True
    closed=next(i for i,r in enumerate(case.native.calls) if r['operation']=='close' and r['pid']==202)
    accounted=next(i for i,r in enumerate(case.native.calls) if r['operation']=='accounting')
    assert closed<accounted
