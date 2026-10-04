"""SUP2 bounded same-instance cleanup proof; no scientific imports.

A suspended child enters a kill-on-close Job before it can create descendants.
RSS is sampled (not a hard instantaneous OS RSS reservation). Every exit kills
the owned Job. SUP2 additionally requires a complete same-instance termination proof.
"""
from __future__ import annotations
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import traceback
import psutil


class IO_COUNTERS(C.Structure):
    _fields_ = [(n, C.c_ulonglong) for n in ('ReadOperationCount','WriteOperationCount',
        'OtherOperationCount','ReadTransferCount','WriteTransferCount','OtherTransferCount')]


class BASIC_LIMIT(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit',C.c_longlong),('PerJobUserTimeLimit',C.c_longlong),
        ('LimitFlags',W.DWORD),('MinimumWorkingSetSize',C.c_size_t),
        ('MaximumWorkingSetSize',C.c_size_t),('ActiveProcessLimit',W.DWORD),
        ('Affinity',C.c_size_t),('PriorityClass',W.DWORD),('SchedulingClass',W.DWORD)]


class EXT_LIMIT(C.Structure):
    _fields_ = [('BasicLimitInformation',BASIC_LIMIT),('IoInfo',IO_COUNTERS),
        ('ProcessMemoryLimit',C.c_size_t),('JobMemoryLimit',C.c_size_t),
        ('PeakProcessMemoryUsed',C.c_size_t),('PeakJobMemoryUsed',C.c_size_t)]


class ACCOUNTING(C.Structure):
    _fields_ = [(n,C.c_longlong) for n in ('TotalUserTime','TotalKernelTime',
        'ThisPeriodTotalUserTime','ThisPeriodTotalKernelTime')] + [
        (n,W.DWORD) for n in ('TotalPageFaultCount','TotalProcesses',
        'ActiveProcesses','TotalTerminatedProcesses')]


CPU_SCHEMA = 'hf-job-cpu-telemetry-1'
CPU_SCOPE = 'owned Windows Job including active and exited members; excludes supervisor'


def _query_cpu_accounting(kernel, job):
    """Observation-only seam; cleanup deliberately uses its independent query."""
    value=ACCOUNTING()
    if not kernel.QueryInformationJobObject(job,1,C.byref(value),C.sizeof(value),None):
        raise C.WinError(C.get_last_error())
    return value


def _write_cpu_record(stream, record):
    encoded=(json.dumps(record,ensure_ascii=False,allow_nan=False,
                        separators=(',',':'))+'\n').encode('utf-8')
    if stream.write(encoded)!=len(encoded):
        raise OSError('short CPU telemetry write')
    stream.flush()
    os.fsync(stream.fileno())


class CpuTelemetryError(RuntimeError):
    """Observation failed: stop work without weakening independent cleanup."""


class _CpuTelemetry:
    def __init__(self, path, identity, supervisor_sha256):
        self.stream=None
        self.sequence=0
        self.previous=None
        self.first_error=None
        self.path=os.path.abspath(os.fspath(path))
        self.identity={}
        try:
            if identity is not None and not isinstance(identity,dict):
                raise ValueError('telemetry_identity must be a dict or None')
            self.identity=json.loads(json.dumps(identity or {},allow_nan=False))
            if ('supervisor_sha256' in self.identity and
                    self.identity['supervisor_sha256']!=supervisor_sha256):
                raise ValueError('telemetry supervisor identity mismatch')
            self.identity['supervisor_sha256']=supervisor_sha256
            target=Path(self.path)
            target.parent.mkdir(parents=True,exist_ok=True)
            self.stream=target.open('xb',buffering=0)
        except BaseException as error:
            self.fail(error,'open')

    def fail(self, error, lifecycle):
        if self.first_error is None:
            self.first_error=dict(type=type(error).__name__,module=type(error).__module__,
                message=str(error),lifecycle=lifecycle,monotonic=time.monotonic(),
                traceback=''.join(traceback.format_exception(error)))
        failure=CpuTelemetryError('CPU telemetry failed during '+lifecycle+': '+str(error))
        failure.detail=self.first_error
        raise failure from error

    def sample(self, kernel, job, lifecycle, *, cleanup_verified=None):
        if self.first_error is not None:
            raise CpuTelemetryError('CPU telemetry already failed; no retry')
        try:
            begin=time.monotonic()
            value=_query_cpu_accounting(kernel,job)
            end=time.monotonic()
            user=int(value.TotalUserTime)
            system=int(value.TotalKernelTime)
            total=int(value.TotalProcesses)
            active=int(value.ActiveProcesses)
            if not all(math.isfinite(t) for t in (begin,end)) or end<begin:
                raise ValueError('CPU query interval is invalid or reversed')
            if user<0 or system<0 or total<0 or active<0 or active>total:
                raise ValueError('invalid Job accounting counters')
            if self.previous is not None:
                previous=self.previous
                if (begin<previous['query_end_monotonic'] or
                        user<previous['total_user_time_100ns'] or
                        system<previous['total_kernel_time_100ns'] or
                        total<previous['TotalProcesses']):
                    raise ValueError('CPU accounting or query time moved backwards')
            record=dict(schema=CPU_SCHEMA,sequence=self.sequence+1,
                utc=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),
                identity=self.identity,lifecycle=lifecycle,
                query_start_monotonic=begin,query_end_monotonic=end,
                total_user_time_100ns=user,total_kernel_time_100ns=system,
                total_user_seconds=user/10_000_000,total_kernel_seconds=system/10_000_000,
                ActiveProcesses=active,TotalProcesses=total,
                counter_unit='100 ns ticks; unit is not measurement resolution',
                cpu_scope=CPU_SCOPE,cleanup_verified=cleanup_verified)
            _write_cpu_record(self.stream,record)
            self.sequence+=1
            self.previous=record
            return record
        except BaseException as error:
            self.fail(error,lifecycle)

    def close(self):
        # Each record was fsynced already. Never retry a failed write at close.
        if self.stream is not None:
            self.stream.close()


PROTOCOL = 'F-CPU-CLEAN1'
CLEANUP_CONTRACT = 'CPU-CLEAN1'
INSTANCE_SCHEMA = 'hf-job-instance-proof-1'
OBSERVER_LIMIT = 64
HISTORY_LIMIT = 256
JOURNAL_LIMIT = 16 * 1024 * 1024
WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258


class InstanceProofError(RuntimeError):
    """A missing proof is a failure, never permission to infer termination."""


class _InstanceJournal:
    def __init__(self, path, identity, *, limit_bytes=JOURNAL_LIMIT):
        self.path = os.path.abspath(os.fspath(path))
        self.identity = json.loads(json.dumps(identity, allow_nan=False))
        self.limit_bytes = limit_bytes
        self.sequence = 0
        self.bytes_written = 0
        self.closed = False
        self.failed = False
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.stream = open(self.path, 'xb', buffering=0)

    def emit(self, event, **fields):
        if self.failed or self.closed:
            raise InstanceProofError('instance journal unavailable; no retry')
        try:
            record = dict(schema=INSTANCE_SCHEMA, sequence=self.sequence + 1,
                utc=datetime.now(timezone.utc).isoformat(), monotonic=time.monotonic(),
                observer_pid=os.getpid(), identity=self.identity, event=event, **fields)
            encoded = (json.dumps(record, ensure_ascii=False, allow_nan=False,
                separators=(',', ':')) + '\n').encode('utf-8')
            if self.bytes_written + len(encoded) > self.limit_bytes:
                raise InstanceProofError('instance journal capacity exhausted')
            if self.stream.write(encoded) != len(encoded):
                raise OSError('short instance journal write')
            self.stream.flush()
            os.fsync(self.stream.fileno())
            self.bytes_written += len(encoded)
            self.sequence += 1
        except BaseException:
            self.failed = True
            raise

    def close(self):
        if not self.closed:
            self.stream.close()
            self.closed = True

    def summary(self):
        # Read actual persisted bytes, including any incomplete failed write.
        data = Path(self.path).read_bytes()
        return dict(path=self.path, sha256=hashlib.sha256(data).hexdigest(),
            bytes=len(data), closed=self.closed, failed=self.failed,
            limit_bytes=self.limit_bytes, records=self.sequence)


class _InstanceProof:
    """Small native seam shared by real supervision and finite control tests.

    Native methods: open(pid), is_in_job(handle), creation_time(handle),
    wait(handle), close(handle). All methods raise on native errors; wait is
    always zero-duration and returns only OBJECT_0 or TIMEOUT. No PID-only
    liveness or exit-code test participates in this proof.
    """
    def __init__(self, native, emit, *, clock=time.monotonic,
                 observer_limit=OBSERVER_LIMIT, history_limit=HISTORY_LIMIT):
        self.native = native
        self.emit = emit
        self.clock = clock
        self.observer_limit = observer_limit
        self.history_limit = history_limit
        self.identities = {}
        self.errors = []
        self.root_key = None
        self.journal_failed = False
        self.root_wait_completed = False
        self.root_handle_close_verified = False

    def _error(self, stage, error, *, begin=None, end=None):
        detail = dict(stage=stage, type=type(error).__name__,
            module=type(error).__module__, message=str(error),
            monotonic=self.clock(), query_start_monotonic=begin,
            query_end_monotonic=end,
            traceback=''.join(traceback.format_exception(error)))
        self.errors.append(detail)
        if not self.journal_failed:
            try:
                self.emit('proof_error', stage=stage, error=detail,
                    query_start_monotonic=begin, query_end_monotonic=end)
            except BaseException as journal_error:
                self.journal_failed = True
                self.errors.append(dict(stage='instance_journal',
                    type=type(journal_error).__name__,
                    module=type(journal_error).__module__, message=str(journal_error),
                    monotonic=self.clock(),
                    traceback=''.join(traceback.format_exception(journal_error))))

    def _emit(self, event, **fields):
        if self.journal_failed:
            return False
        try:
            self.emit(event, **fields)
            return True
        except BaseException as error:
            self.journal_failed = True
            self._error('instance_journal', error)
            return False

    @staticmethod
    def _identity(row):
        return {name: row[name] for name in ('pid', 'creation_filetime', 'handle_kind')}

    def _check_deadline(self, deadline, stage):
        if deadline is not None and self.clock() >= deadline:
            error = InstanceProofError('fixed deadline exhausted during ' + stage)
            self._error(stage, error)
            raise error

    def _call(self, method, *args, deadline=None):
        self._check_deadline(deadline, 'native_deadline')
        begin = self.clock()
        try:
            value = method(*args)
        except BaseException as error:
            self._error(getattr(method, '__name__', 'native_call'), error,
                        begin=begin, end=self.clock())
            raise InstanceProofError('native instance observation failed') from error
        end = self.clock()
        return value, dict(query_start_monotonic=begin, query_end_monotonic=end)

    def _close_unregistered(self, handle, *, pid, purpose):
        begin = self.clock()
        try:
            self.native.close(handle)
        except BaseException as error:
            self._error('close_unregistered', error, begin=begin, end=self.clock())
            return False
        self._emit('unregistered_handle_closed', pid=pid, purpose=purpose,
            query_start_monotonic=begin, query_end_monotonic=self.clock())
        return True

    def _bind(self, pid, handle, *, borrowed, deadline=None):
        begin = self.clock()
        kind = 'borrowed_root' if borrowed else 'owned_observation'
        member, membership_query = self._call(self.native.is_in_job, handle, deadline=deadline)
        if member is not True:
            error = InstanceProofError('handle does not belong to the exact Job')
            self._error('job_membership', error, begin=begin, end=self.clock())
            raise error
        creation, creation_query = self._call(self.native.creation_time, handle, deadline=deadline)
        if isinstance(creation, bool) or not isinstance(creation, int) or creation <= 0:
            error = InstanceProofError('raw creation FILETIME is missing or invalid')
            self._error('creation_identity', error, begin=begin, end=self.clock())
            raise error
        key = (int(pid), creation)
        if key in self.identities:
            if borrowed:
                error = InstanceProofError('root registered twice')
                self._error('root_binding', error)
                raise error
            self._emit('duplicate_identity_observed', pid=int(pid),
                creation_filetime=creation, handle_kind=kind,
                membership_query=membership_query, creation_query=creation_query,
                query_start_monotonic=begin, query_end_monotonic=self.clock())
            return None
        if len(self.identities) >= self.history_limit:
            error = InstanceProofError('unique instance history capacity exhausted')
            self._error('history_capacity', error)
            raise error
        row = dict(pid=int(pid), creation_filetime=creation, handle_kind=kind,
            bound_monotonic=self.clock(), signaled=False, signaled_monotonic=None,
            handle_closed=False, handle_closed_monotonic=None,
            handle_close_attempted=False, close_error=None,
            wait_failed=False,
            wait_timeouts=dict(count=0, first_query=None, last_query=None),
            membership_query=membership_query, creation_query=creation_query,
            _handle=handle)
        self.identities[key] = row
        if borrowed:
            self.root_key = key
        self._emit('instance_bound', **self._identity(row),
            membership_query=membership_query, creation_query=creation_query,
            query_start_monotonic=begin, query_end_monotonic=row['bound_monotonic'])
        return row

    def bind_root(self, pid, borrowed_handle, *, deadline=None):
        row = self._bind(pid, borrowed_handle, borrowed=True, deadline=deadline)
        if self.errors:
            raise InstanceProofError('root binding proof failed')
        return row

    def discover(self, pids, *, assigned_count=None, deadline=None):
        if self.errors:
            raise InstanceProofError('instance collection already failed; no retry')
        pids = list(pids)
        if (assigned_count is not None and assigned_count != len(pids)) or \
                len(set(pids)) != len(pids):
            error = InstanceProofError('incomplete or duplicate Job member list')
            self._error('member_list', error)
            raise error
        for pid in pids:
            self._check_deadline(deadline, 'member_discovery_deadline')
            if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
                error = InstanceProofError('invalid Job process identifier')
                self._error('member_list', error)
                raise error
            # Only an OPEN same-instance handle permits this shortcut. Closed
            # PID values are always opened and bound afresh, including reuse.
            if any(row['pid'] == pid and not row['handle_close_attempted']
                   for row in self.identities.values()):
                continue
            observers = sum(row['handle_kind'] == 'owned_observation' and
                            not row['handle_close_attempted']
                            for row in self.identities.values())
            if observers >= self.observer_limit:
                error = InstanceProofError('active observation handle capacity exhausted')
                self._error('observer_capacity', error)
                raise error
            handle, _ = self._call(self.native.open, pid, deadline=deadline)
            # Ownership starts at successful open, before membership or CT.
            retained = False
            try:
                row = self._bind(pid, handle, borrowed=False, deadline=deadline)
                retained = row is not None
            finally:
                if not retained:
                    self._close_unregistered(handle, pid=pid, purpose='binding_not_retained')
            if self.errors:
                raise InstanceProofError('instance binding proof failed')

    def _close_row(self, row, *, purpose):
        if row['handle_kind'] != 'owned_observation' or row['handle_close_attempted']:
            return
        row['handle_close_attempted'] = True
        begin = self.clock()
        try:
            self.native.close(row['_handle'])
        except BaseException as error:
            row['close_error'] = str(error)
            self._error('observation_handle_close', error, begin=begin, end=self.clock())
            return
        end = self.clock()
        row['handle_closed'] = True
        row['handle_closed_monotonic'] = end
        self._emit('observation_handle_closed', **self._identity(row),
            signaled=row['signaled'], purpose=purpose,
            query_start_monotonic=begin, query_end_monotonic=end)

    def sweep(self, deadline=None):
        """Zero-wait each held instance, release signaled observers promptly."""
        for row in self.identities.values():
            if row['signaled'] or row['handle_close_attempted'] or row['wait_failed']:
                continue
            if deadline is not None and self.clock() >= deadline:
                break
            begin = self.clock()
            try:
                status = self.native.wait(row['_handle'])
                end = self.clock()
                if status == WAIT_OBJECT_0:
                    row['signaled'] = True
                    row['signaled_monotonic'] = end
                    self._emit('instance_signaled', **self._identity(row),
                        wait_result=status, query_start_monotonic=begin,
                        query_end_monotonic=end)
                    self._close_row(row, purpose='same_instance_signaled')
                elif status == WAIT_TIMEOUT:
                    interval = dict(query_start_monotonic=begin, query_end_monotonic=end)
                    aggregate = row['wait_timeouts']
                    aggregate['count'] += 1
                    if aggregate['first_query'] is None:
                        aggregate['first_query'] = interval
                    aggregate['last_query'] = interval
                else:
                    raise InstanceProofError('unexpected zero-wait result: ' + str(status))
            except BaseException as error:
                row['wait_failed'] = True
                self._error('same_instance_wait', error, begin=begin, end=self.clock())
                # This instance stays unproven; other handles still get swept.
                self._close_row(row, purpose='wait_error_reference_release')

    def drain(self, deadline, accounting, sleep, *, after_sweep=None):
        """One shared cleanup deadline, sweep/release BEFORE each Job query."""
        last = None
        while self.clock() < deadline:
            self.sweep(deadline)
            if self.clock() >= deadline:
                break
            try:
                if after_sweep is not None:
                    after_sweep(deadline)
                if self.clock() >= deadline:
                    break
                last = accounting()
            except BaseException as error:
                self._error('cleanup_accounting', error)
                break
            if (last['ActiveProcesses'] == 0 and self.root_key is not None and
                    all(row['signaled'] for row in self.identities.values())):
                break
            remaining = deadline - self.clock()
            if remaining <= 0:
                break
            sleep(min(.01, remaining))
        return last

    def release_remaining(self):
        # Release references even when unproven. Never mark them signaled.
        for row in self.identities.values():
            self._close_row(row, purpose='failure_or_deadline_release')

    def note_root_wait(self, returncode, *, begin, end):
        if self.root_key is None or not self.identities[self.root_key]['signaled']:
            self._error('root_wait', InstanceProofError('root lacks same-handle signal'))
            return
        self.root_wait_completed = True
        self._emit('root_wait_completed', **self._identity(self.identities[self.root_key]),
            returncode=returncode, query_start_monotonic=begin, query_end_monotonic=end)

    def note_root_closed(self, *, begin=None, end=None):
        if self.root_key is None or not self.root_wait_completed:
            self._error('root_handle_close', InstanceProofError('root wait not completed'))
            return
        row = self.identities[self.root_key]
        if row['handle_closed']:
            self._error('root_handle_close', InstanceProofError('root close recorded twice'))
            return
        row['handle_close_attempted'] = True
        row['handle_closed'] = True
        row['handle_closed_monotonic'] = self.clock() if end is None else end
        self.root_handle_close_verified = True
        self._emit('root_handle_closed', **self._identity(row),
            query_start_monotonic=begin, query_end_monotonic=row['handle_closed_monotonic'])

    def finish(self, accounting, *, root_wait_completed, root_handle_closed):
        rows = [{k: v for k, v in row.items() if not k.startswith('_')}
                for row in self.identities.values()]
        count = len(rows)
        signaled = sum(row['signaled'] for row in rows)
        observers_closed = all(row['handle_closed'] for row in rows
                               if row['handle_kind'] == 'owned_observation')
        coverage = (isinstance(accounting, dict) and
                    accounting.get('TotalProcesses') == count and count > 0)
        termination = signaled == count and count > 0
        root_signal = self.root_key is not None and self.identities[self.root_key]['signaled']
        root_row_closed = self.root_key is not None and self.identities[self.root_key]['handle_closed']
        waited = bool(root_wait_completed and self.root_wait_completed)
        root_closed = bool(root_handle_closed and self.root_handle_close_verified and root_row_closed)
        passed = bool(not self.errors and not self.journal_failed and coverage and
            termination and accounting.get('ActiveProcesses') == 0 and root_signal and
            waited and root_closed and observers_closed)
        return dict(status='verified_all_instances' if passed else 'incomplete_or_failed',
            **{'pass': passed}, coverage_verified=coverage,
            termination_verified=termination, observation_handles_closed=observers_closed,
            unique_bound_identity_count=count, signaled_identity_count=signaled,
            final_accounting=accounting, root_wait_completed=waited,
            root_handle_close_verified=root_closed, identities=rows,
            errors=list(self.errors), limits=dict(observation_handles=self.observer_limit,
                unique_history=self.history_limit, instance_journal_bytes=JOURNAL_LIMIT))


def _api():
    if os.name != 'nt':
        raise RuntimeError('This supervisor requires Windows Job Objects')
    k = C.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateJobObjectW': ([C.c_void_p, W.LPCWSTR], W.HANDLE),
        'SetInformationJobObject': ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
        'AssignProcessToJobObject': ([W.HANDLE, W.HANDLE], W.BOOL),
        'QueryInformationJobObject': ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p], W.BOOL),
        'TerminateJobObject': ([W.HANDLE, W.UINT], W.BOOL),
        'OpenProcess': ([W.DWORD, W.BOOL, W.DWORD], W.HANDLE),
        'IsProcessInJob': ([W.HANDLE, W.HANDLE, C.POINTER(W.BOOL)], W.BOOL),
        'GetProcessTimes': ([W.HANDLE] + [C.POINTER(W.FILETIME)] * 4, W.BOOL),
        'WaitForSingleObject': ([W.HANDLE, W.DWORD], W.DWORD),
        'CloseHandle': ([W.HANDLE], W.BOOL),
    }
    for name, (args, result) in signatures.items():
        getattr(k, name).argtypes = args
        getattr(k, name).restype = result
    n = C.WinDLL('ntdll')
    n.NtResumeProcess.argtypes = [W.HANDLE]
    n.NtResumeProcess.restype = C.c_long
    return k, n


class _NativeInstances:
    def __init__(self, kernel, job):
        self.kernel = kernel
        self.job = job

    def open(self, pid):
        value = self.kernel.OpenProcess(0x00100000 | 0x1000, False, pid)
        if not value:
            raise C.WinError(C.get_last_error())
        return value

    def is_in_job(self, handle):
        result = W.BOOL()
        if not self.kernel.IsProcessInJob(W.HANDLE(int(handle)), self.job, C.byref(result)):
            raise C.WinError(C.get_last_error())
        return bool(result.value)

    def creation_time(self, handle):
        creation, exited, kernel, user = (W.FILETIME() for _ in range(4))
        if not self.kernel.GetProcessTimes(W.HANDLE(int(handle)), C.byref(creation),
                C.byref(exited), C.byref(kernel), C.byref(user)):
            raise C.WinError(C.get_last_error())
        # No interpretation of exit FILETIME before signal. Identity is raw.
        return (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)

    def wait(self, handle):
        value = int(self.kernel.WaitForSingleObject(W.HANDLE(int(handle)), 0))
        if value == 0xFFFFFFFF:
            raise C.WinError(C.get_last_error())
        if value not in (WAIT_OBJECT_0, WAIT_TIMEOUT):
            raise InstanceProofError('unexpected process wait result: ' + str(value))
        return value

    def close(self, handle):
        if not self.kernel.CloseHandle(W.HANDLE(int(handle))):
            raise C.WinError(C.get_last_error())


def run_owned(command, *, cwd, env, log, deadline, seconds=300.,
              rss_limit=8*1024**3, poll_seconds=.025, telemetry_path=None,
              telemetry_identity=None, telemetry_interval_seconds=1.0,
              instance_log_path=None, instance_identity=None):
    """SUP2 always requires complete same-instance cleanup, including failures.

    The CPU observation seam remains independent of cleanup. The new instance
    proof journal is mandatory even when CPU telemetry is disabled.
    """
    k, n = _api()
    start = time.monotonic()
    candidate_path = str(Path(__file__).resolve())
    supervisor_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    candidate_supervisor = dict(version='SUP2', path=candidate_path, sha256=supervisor_sha256)
    local_deadline = min(deadline, start + seconds)
    job = k.CreateJobObjectW(None, None)
    if not job:
        raise C.WinError(C.get_last_error())
    proc = None
    assigned = False
    peak = 0
    seen = set()
    reason = 'normal_exit'
    errors = []
    cleanup_ok = False
    code = None
    telemetry = None
    telemetry_first_error = None
    cleanup_requested_monotonic = None
    next_cpu = None
    journal = None
    journal_summary = None
    final_accounting = None
    root_wait_completed = False
    root_wait_attempted = False
    root_handle_closed = False
    job_handle_closed = False
    proof = _InstanceProof(_NativeInstances(k, job), lambda *args, **kwargs: None)

    def remember_telemetry_error(error, lifecycle):
        nonlocal reason, telemetry_first_error
        reason = 'supervision_error'
        if telemetry_first_error is None:
            telemetry_first_error = (telemetry.first_error if telemetry is not None
                and telemetry.first_error is not None else getattr(error, 'detail', None) or dict(
                    type=type(error).__name__, module=type(error).__module__,
                    message=str(error), lifecycle=lifecycle, monotonic=time.monotonic(),
                    traceback=''.join(traceback.format_exception(error))))
        errors.append('telemetry ' + lifecycle + ' ' + type(error).__name__ + ': ' + str(error))

    def accounting():
        begin = time.monotonic()
        value = ACCOUNTING()
        if not k.QueryInformationJobObject(job, 1, C.byref(value), C.sizeof(value), None):
            raise C.WinError(C.get_last_error())
        end = time.monotonic()
        return dict(ActiveProcesses=int(value.ActiveProcesses),
            TotalProcesses=int(value.TotalProcesses),
            TotalTerminatedProcesses=int(value.TotalTerminatedProcesses),
            query_start_monotonic=begin, query_end_monotonic=end)

    def members():
        begin = time.monotonic()
        capacity = 4096
        buf = C.create_string_buffer(8 + capacity*C.sizeof(C.c_size_t))
        if not k.QueryInformationJobObject(job, 3, buf, len(buf), None):
            raise C.WinError(C.get_last_error())
        assigned_count = C.c_uint32.from_buffer(buf, 0).value
        listed = C.c_uint32.from_buffer(buf, 4).value
        if assigned_count != listed or listed > capacity:
            raise InstanceProofError('Job member enumeration incomplete or over capacity')
        pids = list((C.c_size_t*listed).from_buffer(buf, 8))
        # The fixed list buffer is not an observation-handle/history allowance.
        return pids, assigned_count, dict(query_start_monotonic=begin,
                                         query_end_monotonic=time.monotonic())

    def finish_root_owner(cleanup_deadline):
        nonlocal code, root_wait_attempted, root_wait_completed, root_handle_closed
        if proc is None or root_wait_attempted or time.monotonic() >= cleanup_deadline:
            return
        root_signaled = (proof.root_key is not None and
                        proof.identities[proof.root_key]['signaled'])
        if proof.root_key is not None and not root_signaled:
            return
        root_wait_attempted = True
        begin = time.monotonic()
        try:
            # Root signal precedes wait on every possible passing path. A
            # binding/assignment failure still releases its original owner,
            # but cannot manufacture the missing Job proof.
            proc.wait(timeout=max(0., cleanup_deadline - time.monotonic()))
            code = proc.returncode
            if code is None:
                raise InstanceProofError('Popen.wait returned without a cached real exit code')
            if root_signaled:
                root_wait_completed = True
                proof.note_root_wait(code, begin=begin, end=time.monotonic())
            close_begin = time.monotonic()
            if proof.root_key is not None:
                proof.identities[proof.root_key]['handle_close_attempted'] = True
            try:
                # Wrapper.Close returns successfully or this proof fails;
                # its _closed flag is deliberately never used as evidence.
                proc._handle.Close()
            except BaseException as error:
                if proof.root_key is not None:
                    proof.identities[proof.root_key]['close_error'] = str(error)
                proof._error('root_handle_close', error,
                    begin=close_begin, end=time.monotonic())
            else:
                if root_signaled:
                    root_handle_closed = True
                    proof.note_root_closed(begin=close_begin, end=time.monotonic())
        except BaseException as error:
            proof._error('root_wait', error, begin=begin, end=time.monotonic())

    try:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        identity = json.loads(json.dumps(instance_identity or {}, allow_nan=False))
        if not isinstance(identity, dict):
            raise ValueError('instance_identity must be a dict or None')
        identity.update(protocol=PROTOCOL, cleanup_contract=CLEANUP_CONTRACT,
                        candidate_supervisor=candidate_supervisor)
        journal = _InstanceJournal(instance_log_path or (os.fspath(log) + '.instances.ndjson'), identity)
        proof.emit = journal.emit
        proof._emit('supervision_started', candidate_supervisor=candidate_supervisor)
        if proof.errors:
            raise InstanceProofError('cannot establish instance evidence')
        if telemetry_path is not None:
            if (isinstance(telemetry_interval_seconds, bool) or
                    not isinstance(telemetry_interval_seconds, (int, float)) or
                    not math.isfinite(telemetry_interval_seconds) or telemetry_interval_seconds <= 0):
                raise ValueError('telemetry_interval_seconds must be finite and positive')
            telemetry = _CpuTelemetry(telemetry_path, telemetry_identity, supervisor_sha256)
        limits = EXT_LIMIT()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        if not k.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)):
            raise C.WinError(C.get_last_error())
        with open(log, 'xb', buffering=0) as output:
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW | 0x00000004)
            if not k.AssignProcessToJobObject(job, W.HANDLE(int(proc._handle))):
                raise C.WinError(C.get_last_error())
            assigned = True
            seen.add(proc.pid)
            proof.bind_root(proc.pid, int(proc._handle), deadline=local_deadline)
            if telemetry is not None:
                telemetry.sample(k, job, 'initial_before_resume')
                next_cpu = time.monotonic() + telemetry_interval_seconds
            status = n.NtResumeProcess(W.HANDLE(int(proc._handle)))
            if status != 0:
                raise RuntimeError('NtResumeProcess failed: ' + str(status))
            while True:
                if time.monotonic() >= local_deadline:
                    reason = 'global_deadline' if deadline <= start + seconds else 'phase_timeout'
                    break
                proof.sweep(local_deadline)
                if proof.errors:
                    raise InstanceProofError('same-instance poll proof failed')
                if time.monotonic() >= local_deadline:
                    reason = 'global_deadline' if deadline <= start + seconds else 'phase_timeout'
                    break
                pids, assigned_count, _ = members()
                seen.update(pids)
                proof.discover(pids, assigned_count=assigned_count, deadline=local_deadline)
                rss = psutil.Process().memory_info().rss
                for pid in pids:
                    try:
                        rss += psutil.Process(pid).memory_info().rss
                    except psutil.NoSuchProcess:
                        pass
                peak = max(peak, rss)
                if rss > rss_limit:
                    reason = 'rss_limit'
                    break
                if time.monotonic() >= local_deadline:
                    reason = 'global_deadline' if deadline <= start + seconds else 'phase_timeout'
                    break
                code = proc.poll()
                if code is not None:
                    reason = 'normal_exit' if code == 0 else 'nonzero_exit'
                    break
                if telemetry is not None and time.monotonic() >= next_cpu:
                    telemetry.sample(k, job, 'periodic')
                    next_cpu = time.monotonic() + telemetry_interval_seconds
                time.sleep(poll_seconds)
    except BaseException as error:
        reason = 'supervision_error'
        errors.append(type(error).__name__ + ': ' + str(error))
        if telemetry_path is not None and (isinstance(error, CpuTelemetryError) or telemetry is None):
            remember_telemetry_error(error, 'run')
        # CPU observer failures do not falsify the independently collected proof.
        if not isinstance(error, CpuTelemetryError):
            proof._error('supervision', error)
    finally:
        cleanup_deadline = time.monotonic() + 5.
        cleanup_requested_monotonic = time.monotonic()
        proof._emit('cleanup_requested', cleanup_deadline_monotonic=cleanup_deadline,
                    cleanup_requested_monotonic=cleanup_requested_monotonic)
        if assigned and telemetry is not None and telemetry.first_error is None:
            try:
                telemetry.sample(k, job, 'pre_cleanup')
            except BaseException as error:
                remember_telemetry_error(error, 'pre_cleanup')
        try:
            if assigned:
                # One final complete discovery can catch members born between
                # the last normal poll and root exit. Errors still cannot skip kill.
                if not proof.errors and time.monotonic() < cleanup_deadline:
                    try:
                        proof.sweep(cleanup_deadline)
                        proof._check_deadline(cleanup_deadline, 'cleanup_discovery_deadline')
                        pids, assigned_count, _ = members()
                        seen.update(pids)
                        proof.discover(pids, assigned_count=assigned_count, deadline=cleanup_deadline)
                    except BaseException as error:
                        proof._error('cleanup_member_discovery', error)
                begin = time.monotonic()
                try:
                    if not k.TerminateJobObject(job, 125):
                        raise C.WinError(C.get_last_error())
                    proof._emit('job_termination_requested', exit_code=125,
                        query_start_monotonic=begin, query_end_monotonic=time.monotonic())
                except BaseException as error:
                    proof._error('job_termination', error, begin=begin, end=time.monotonic())
                proof.drain(cleanup_deadline, accounting, time.sleep,
                            after_sweep=finish_root_owner)
            elif proc is not None:
                # Assignment failed while the child was suspended. It cannot
                # have descendants, but this is never a passing SUP2 proof.
                try:
                    proc.kill()
                except BaseException as error:
                    proof._error('unassigned_root_kill', error)

            finish_root_owner(cleanup_deadline)
            if proc is not None and not root_wait_completed:
                proof._error('root_wait_unconfirmed', InstanceProofError(
                    'root owner remains responsible; no fabricated return code or destructor proof'))
        except BaseException as error:
            proof._error('cleanup', error)
        finally:
            # Independent close attempts continue after native/evidence failures.
            proof.release_remaining()
            if assigned:
                try:
                    final_accounting = accounting()
                    proof._emit('final_accounting', **final_accounting)
                except BaseException as error:
                    proof._error('final_accounting', error)
            if time.monotonic() > cleanup_deadline:
                proof._error('cleanup_deadline', InstanceProofError('shared cleanup deadline exhausted'))
            preliminary = proof.finish(final_accounting,
                root_wait_completed=root_wait_completed, root_handle_closed=root_handle_closed)
            if assigned and telemetry is not None and telemetry.first_error is None:
                try:
                    telemetry.sample(k, job, 'final_after_cleanup', cleanup_verified=preliminary['pass'])
                except BaseException as error:
                    remember_telemetry_error(error, 'final_after_cleanup')
            if telemetry is not None:
                try:
                    telemetry.close()
                except BaseException as error:
                    remember_telemetry_error(error, 'close')
            try:
                if not k.CloseHandle(job):
                    raise C.WinError(C.get_last_error())
                job_handle_closed = True
            except BaseException as error:
                proof._error('job_handle_close', error)
            if journal is not None:
                try:
                    journal.close()
                    journal_summary = journal.summary()
                except BaseException as error:
                    proof._error('instance_journal_finalize', error)
            if journal is None:
                proof._error('instance_journal_missing', InstanceProofError('mandatory journal was not established'))
            if time.monotonic() > cleanup_deadline:
                proof._error('cleanup_deadline', InstanceProofError('shared cleanup deadline exhausted at finalization'))
    cleanup_proof = proof.finish(final_accounting,
        root_wait_completed=root_wait_completed, root_handle_closed=root_handle_closed)
    cleanup_proof['journal'] = journal_summary
    cleanup_proof['job_handle_closed'] = job_handle_closed
    cleanup_ok = cleanup_proof['pass']
    if not cleanup_ok:
        reason = 'cleanup_failure'
    return dict(command=list(command), cwd=str(cwd), pid=proc.pid if proc else None,
        owned_pids=sorted(seen), reason=reason, returncode=code,
        cleanup_verified=cleanup_ok, cleanup_proof=cleanup_proof,
        cleanup_contract=CLEANUP_CONTRACT, protocol=PROTOCOL,
        candidate_supervisor=candidate_supervisor, errors=errors,
        elapsed_seconds=time.monotonic()-start, peak_tree_rss_bytes=peak,
        rss_limit_bytes=rss_limit, rss_sample_interval_seconds=poll_seconds,
        timeout_seconds=seconds, deadline_monotonic=deadline,
        ownership='suspended root borrowed from Popen; same-instance owned Job proof',
        rss_scope='supervisor plus all Job members; sampled RSS',
        cleanup_requested_monotonic=cleanup_requested_monotonic,
        cleanup_deadline_monotonic=cleanup_deadline,
        telemetry_status=('disabled' if telemetry_path is None else
            'failed' if telemetry_first_error is not None else
            'complete' if telemetry is not None and telemetry.previous is not None and
                telemetry.previous['lifecycle']=='final_after_cleanup' else 'incomplete'),
        telemetry_path=None if telemetry_path is None else os.path.abspath(os.fspath(telemetry_path)),
        telemetry_interval_seconds=None if telemetry_path is None else telemetry_interval_seconds,
        telemetry_first_error=telemetry_first_error,
        supervisor_sha256=supervisor_sha256, cpu_scope=CPU_SCOPE)


