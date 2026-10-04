"""Windows owned-process supervision; no scientific imports.

A suspended child enters a kill-on-close Job before it can create descendants.
RSS is sampled (not a hard instantaneous OS RSS reservation). Every exit kills
and verifies the whole owned Job, including grandchildren orphaned by its root.
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


def _api():
    if os.name != 'nt':
        raise RuntimeError('This supervisor requires Windows Job Objects')
    k = C.WinDLL('kernel32', use_last_error=True)
    signatures = {
        'CreateJobObjectW':([C.c_void_p,W.LPCWSTR],W.HANDLE),
        'SetInformationJobObject':([W.HANDLE,C.c_int,C.c_void_p,W.DWORD],W.BOOL),
        'AssignProcessToJobObject':([W.HANDLE,W.HANDLE],W.BOOL),
        'QueryInformationJobObject':([W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.c_void_p],W.BOOL),
        'TerminateJobObject':([W.HANDLE,W.UINT],W.BOOL),
        'CloseHandle':([W.HANDLE],W.BOOL),
    }
    for name,(args,result) in signatures.items():
        getattr(k,name).argtypes=args
        getattr(k,name).restype=result
    n=C.WinDLL('ntdll')
    n.NtResumeProcess.argtypes=[W.HANDLE]
    n.NtResumeProcess.restype=C.c_long
    return k,n


def run_owned(command, *, cwd, env, log, deadline, seconds=300.,
              rss_limit=8*1024**3, poll_seconds=.025, telemetry_path=None,
              telemetry_identity=None, telemetry_interval_seconds=1.0):
    """Return a receipt. Any supervision/cleanup error is fatal to a campaign."""
    k,n=_api()
    start=time.monotonic()
    supervisor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    local_deadline=min(deadline, start+seconds)
    job=k.CreateJobObjectW(None,None)
    if not job:
        raise C.WinError(C.get_last_error())
    proc=None
    assigned=False
    peak=0
    seen=set()
    reason='normal_exit'
    errors=[]
    cleanup_ok=False
    code=None
    telemetry=None
    telemetry_first_error=None
    cleanup_requested_monotonic=None
    next_cpu=None
    def remember_telemetry_error(error, lifecycle):
        nonlocal reason,telemetry_first_error
        reason='supervision_error'
        if telemetry_first_error is None:
            telemetry_first_error=(telemetry.first_error if telemetry is not None
                and telemetry.first_error is not None else getattr(error,'detail',None) or dict(
                    type=type(error).__name__,module=type(error).__module__,
                    message=str(error),lifecycle=lifecycle,monotonic=time.monotonic(),
                    traceback=''.join(traceback.format_exception(error))))
        errors.append('telemetry '+lifecycle+' '+type(error).__name__+': '+str(error))
    def active():
        a=ACCOUNTING()
        if not k.QueryInformationJobObject(job,1,C.byref(a),C.sizeof(a),None):
            raise C.WinError(C.get_last_error())
        return a.ActiveProcesses
    def members():
        # Native membership includes grandchildren after their parent exits.
        count=4096
        buf=C.create_string_buffer(8+count*C.sizeof(C.c_size_t))
        if not k.QueryInformationJobObject(job,3,buf,len(buf),None):
            raise C.WinError(C.get_last_error())
        listed=C.c_uint32.from_buffer(buf,4).value
        if listed>count:
            raise RuntimeError('Job membership exceeds supervisor capacity')
        ids=(C.c_size_t*listed).from_buffer(buf,8)
        return list(ids)
    try:
        Path(log).parent.mkdir(parents=True,exist_ok=True)
        if telemetry_path is not None:
            if (isinstance(telemetry_interval_seconds,bool) or
                    not isinstance(telemetry_interval_seconds,(int,float)) or
                    not math.isfinite(telemetry_interval_seconds) or telemetry_interval_seconds<=0):
                raise ValueError('telemetry_interval_seconds must be finite and positive')
            telemetry=_CpuTelemetry(telemetry_path,telemetry_identity,supervisor_sha256)
        limits=EXT_LIMIT()
        limits.BasicLimitInformation.LimitFlags=0x2000
        if not k.SetInformationJobObject(job,9,C.byref(limits),C.sizeof(limits)):
            raise C.WinError(C.get_last_error())
        with open(log,'xb',buffering=0) as output:
            proc=subprocess.Popen(command,cwd=cwd,env=env,stdin=subprocess.DEVNULL,
                stdout=output,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW|0x00000004)
            if not k.AssignProcessToJobObject(job,W.HANDLE(int(proc._handle))):
                raise C.WinError(C.get_last_error())
            assigned=True
            seen.add(proc.pid)
            if telemetry is not None:
                telemetry.sample(k,job,'initial_before_resume')
                next_cpu=time.monotonic()+telemetry_interval_seconds
            status=n.NtResumeProcess(W.HANDLE(int(proc._handle)))
            if status!=0:
                raise RuntimeError('NtResumeProcess failed: '+str(status))
            while True:
                pids=members()
                seen.update(pids)
                rss=psutil.Process().memory_info().rss
                for pid in pids:
                    try:
                        rss+=psutil.Process(pid).memory_info().rss
                    except psutil.NoSuchProcess:
                        pass
                peak=max(peak,rss)
                if rss>rss_limit:
                    reason='rss_limit'
                    break
                if time.monotonic()>=local_deadline:
                    reason='global_deadline' if deadline<=start+seconds else 'phase_timeout'
                    break
                code=proc.poll()
                if code is not None:
                    reason='normal_exit' if code==0 else 'nonzero_exit'
                    break
                if telemetry is not None and time.monotonic()>=next_cpu:
                    telemetry.sample(k,job,'periodic')
                    # No catch-up: a delayed read leaves its real sampling gap.
                    next_cpu=time.monotonic()+telemetry_interval_seconds
                time.sleep(poll_seconds)
    except BaseException as exc:
        reason='supervision_error'
        errors.append(type(exc).__name__+': '+str(exc))
        if telemetry_path is not None and (isinstance(exc,CpuTelemetryError)
                or telemetry is None):
            remember_telemetry_error(exc,'run')
    finally:
        cleanup_deadline=time.monotonic()+5.
        # This boundary excludes pre-cleanup/final observation CPU from the
        # scientific interval; it precedes both the snapshot and first kill.
        if assigned:
            cleanup_requested_monotonic=time.monotonic()
        if assigned and telemetry is not None and telemetry.first_error is None:
            try:
                telemetry.sample(k,job,'pre_cleanup')
            except BaseException as exc:
                remember_telemetry_error(exc,'pre_cleanup')
        try:
            if assigned:
                if not k.TerminateJobObject(job,125):
                    raise C.WinError(C.get_last_error())
                while active() and time.monotonic()<cleanup_deadline:
                    time.sleep(.01)
                cleanup_ok=active()==0
            elif proc is not None:
                proc.kill()  # still suspended, so it cannot have descendants
                proc.wait(timeout=max(.001,cleanup_deadline-time.monotonic()))
                cleanup_ok=True
            else:
                cleanup_ok=True
            if proc is not None:
                proc.wait(timeout=max(.001,cleanup_deadline-time.monotonic()))
                if code is None:
                    code=proc.returncode
        except BaseException as exc:
            errors.append('cleanup '+type(exc).__name__+': '+str(exc))
            cleanup_ok=False
        finally:
            try:
                if assigned and telemetry is not None and telemetry.first_error is None:
                    try:
                        telemetry.sample(k,job,'final_after_cleanup',cleanup_verified=cleanup_ok)
                    except BaseException as exc:
                        remember_telemetry_error(exc,'final_after_cleanup')
                if telemetry is not None:
                    try:
                        telemetry.close()
                    except BaseException as exc:
                        remember_telemetry_error(exc,'close')
            finally:
                k.CloseHandle(job)  # independent kill-on-close fallback
    if not cleanup_ok:
        reason='cleanup_failure'
    return {'command':list(command),'cwd':str(cwd),'pid':proc.pid if proc else None,
        'owned_pids':sorted(seen),'reason':reason,'returncode':code,
        'cleanup_verified':cleanup_ok,'errors':errors,
        'elapsed_seconds':time.monotonic()-start,'peak_tree_rss_bytes':peak,
        'rss_limit_bytes':rss_limit,'rss_sample_interval_seconds':poll_seconds,
        'timeout_seconds':seconds,'deadline_monotonic':deadline,
        'ownership':'suspended child assigned to kill-on-close Windows Job',
        'rss_scope':'supervisor plus all Job members; sampled RSS',
        'cleanup_requested_monotonic':cleanup_requested_monotonic,
        'telemetry_status':('disabled' if telemetry_path is None else
                            'failed' if telemetry_first_error is not None else
                            'complete' if telemetry is not None and telemetry.previous is not None
                            and telemetry.previous['lifecycle']=='final_after_cleanup' else 'incomplete'),
        'telemetry_path':None if telemetry_path is None else os.path.abspath(os.fspath(telemetry_path)),
        'telemetry_interval_seconds':None if telemetry_path is None else telemetry_interval_seconds,
        'telemetry_first_error':telemetry_first_error,
        'supervisor_sha256':supervisor_sha256,'cpu_scope':CPU_SCOPE}
