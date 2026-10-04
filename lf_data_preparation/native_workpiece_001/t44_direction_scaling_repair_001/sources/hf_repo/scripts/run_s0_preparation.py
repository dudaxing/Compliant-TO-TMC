"""Authorized 600-second S0 diagnostic; no equilibrium or scientific admission.

The approved baseline-failure observation is the ONLY continuation exception.
All other failures terminate this new campaign. Old campaigns are never resumed.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import psutil
from windows_owned_process import run_owned

CARD='docs/HF4_C2_NEAR_ROTATION_DIAGNOSTIC_20260928.md'
LIMITS={'P0':30.,'P1':30.,'P2':60.,'P3':90.,'P4':150.,'P5':180.,'P6':30.,'shared':30.}
FATAL={'rss_limit','global_deadline','phase_timeout','supervision_error','cleanup_failure'}
NODE='test_physical_jvp_and_vjp_match_closed_form_first_derivatives'

def utc(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
def replace(path,value):
    temporary=Path(path).with_suffix('.pending.json')
    dump(temporary,value);os.replace(temporary,path)
def extended(path):
    text=str(Path(path).resolve())
    return Path('\\\\?\\'+text) if os.name=='nt' and not text.startswith('\\\\?\\') else Path(text)


class StopCampaign(RuntimeError):
    def __init__(self,status,detail):
        super().__init__(detail);self.status=status


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    repo=extended(args.repo);root=extended(args.root)
    if root.exists(): raise RuntimeError('Refuse to reset or reuse any campaign directory')
    start=time.monotonic();deadline=start+600.
    root.mkdir(parents=True)
    (root/'events').mkdir();(root/'logs').mkdir();(root/'results').mkdir()
    phases=[];used={key:0. for key in LIMITS};status='running';error=None
    ledger={'schema':'hf-s0-preparation-campaign-1','status':status,'started_utc':utc(),
        'start_monotonic':start,'deadline_monotonic':deadline,'boot_time_estimate':psutil.boot_time(),
        'seconds':600,'rss_limit_bytes':8*1024**3,'limits_seconds':LIMITS,
        'card_sha256':sha(repo/CARD),'phases':phases,'consumed_phase_seconds':used,
        'production_identities':['B0','at most one evidence-supported C1'],
        'no_new_equilibrium':True,'scientific_matrix_authorized':False}
    dump(root/'plan.json',{**ledger,'repo':str(repo),'python':sys.version,
        'prior_campaign':'invariants_hu_campaign_001/version_002',
        'representative':'unit__near_rotation original direction_0',
        'P2_baseline_nodeid':'source/hf_repo/tests/test_compensated_invariants.py::'+NODE})
    dump(root/'ledger.json',ledger)
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',
        PYTHONNOUSERSITE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',JAX_ENABLE_X64='true',JAX_TRACEBACK_FILTERING='off',
        JAX_ENABLE_COMPILATION_CACHE='false',JAX_PLATFORMS='cpu',
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        MPLBACKEND='Agg',MPLCONFIGDIR=str(root/'matplotlib-cache'))
    aux=root/'aux/hf_repo/scripts'
    base=root/'B0/source/hf_repo'
    evidence=aux/'s0_preparation_evidence.py'
    selected={'source':str(base),'version':'B0','source_manifest':str(root/'input_manifest.json')}
    manifest_hash=None;shared_index=0

    def save_ledger():
        ledger.update(status=status,elapsed_seconds=time.monotonic()-start)
        replace(root/'ledger.json',ledger)

    def execute(name,bucket,command,*,source=None,phase_deadline=None,observe=False):
        remaining=LIMITS[bucket]-used[bucket]
        cap=deadline-(5. if bucket=='P6' else 35.)
        if phase_deadline is not None:cap=min(cap,phase_deadline)
        if remaining<=0 or time.monotonic()>=cap:
            raise StopCampaign('resource_stop','No authorized time remains for '+name)
        runenv=env.copy()
        chosen=source or selected
        runenv['PYTHONPATH']=str(Path(chosen['source'])/'src')+os.pathsep+str(aux)
        runenv.update(HF_S0_EVENT_FILE=str(root/'events'/(name+'.ndjson')),
            HF_S0_PHASE=name,HF_S0_VERSION=chosen['version'],
            HF_S0_SOURCE_MANIFEST_SHA=chosen.get('source_manifest_sha256') or manifest_hash or sha(root/'plan.json'))
        print(json.dumps({'phase':name,'started_utc':utc(),'remaining_campaign_seconds':deadline-time.monotonic()}),flush=True)
        receipt=run_owned(command,cwd=str(root),env=runenv,log=root/'logs'/(name+'.log'),
            deadline=cap,seconds=remaining,rss_limit=8*1024**3)
        receipt.update(name=name,bucket=bucket,source_version=chosen['version'])
        phases.append(receipt);used[bucket]+=receipt['elapsed_seconds'];save_ledger()
        print(json.dumps({'phase':name,'reason':receipt['reason'],'returncode':receipt['returncode'],
            'seconds':receipt['elapsed_seconds'],'peak_rss_bytes':receipt['peak_tree_rss_bytes']}),flush=True)
        if receipt['reason'] in FATAL:
            raise StopCampaign('resource_or_supervision_stop',name+': '+receipt['reason'])
        if receipt['returncode']!=0 and not(observe and receipt['returncode']==1):
            raise StopCampaign('test_failure_unclassified' if bucket in ('P1','P3') else 'execution_failure',
                name+' returned '+str(receipt['returncode']))
        return receipt

    def worker(action):
        return [sys.executable,'-u','-B',str(evidence),'--root',str(root),'--repo',str(repo),'--action',action]

    def verify():
        nonlocal shared_index
        shared_index+=1
        if manifest_hash is None or sha(root/'input_manifest.json')!=manifest_hash:
            raise StopCampaign('source_not_pass','Initial source manifest changed or absent')
        try: execute('verify_%02d'%shared_index,'shared',worker('verify'))
        except StopCampaign as exc:
            if exc.status=='execution_failure':raise StopCampaign('source_not_pass',str(exc)) from exc
            raise

    def pytest_command(name,paths,source):
        folder=root/'results'/name;folder.mkdir(parents=True,exist_ok=True)
        return [sys.executable,'-u','-B','-m','pytest','-x','--maxfail=1','-vv','--tb=long',
            '-p','no:cacheprovider','-p','hf_s0_pytest_events',
            '-o','pythonpath=',*map(str,paths),
            '--basetemp='+str(folder/'synthetic-temp'),'--junitxml='+str(folder/'pytest.xml')]

    def reports(name,expected,allow_failure=False):
        path=root/'events'/(name+'.ndjson')
        if not path.exists():raise StopCampaign('evidence_failure','Missing immediate pytest events: '+name)
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        calls=[r for r in rows if r.get('event')=='test_report' and r.get('when')=='call' and 'outcome' in r]
        expected_sha=selected.get('source_manifest_sha256') or manifest_hash
        if (not rows or [r.get('sequence') for r in rows]!=list(range(1,len(rows)+1))
            or any(r.get('source_manifest_sha256')!=expected_sha or r.get('phase')!=name
                   or r.get('version')!=selected['version'] for r in rows)):
            raise StopCampaign('evidence_failure','Event identity or sequence mismatch: '+name)
        if any(r.get('event') in ('pytest_internal_error','pytest_interrupted')
               or (r.get('event')=='collection_report' and r.get('outcome')=='failed')
               or (r.get('event')=='test_report' and r.get('when')!='call' and r.get('outcome')!='passed')
               for r in rows):
            raise StopCampaign('evidence_failure','Pytest collection/setup/teardown/internal failure: '+name)
        finished=[r for r in rows if r.get('event')=='session_finish']
        expected_exit=1 if any(r.get('outcome')=='failed' for r in calls) else 0
        if len(finished)!=1 or finished[0].get('exitstatus')!=expected_exit:
            raise StopCampaign('evidence_failure','Incomplete or inconsistent pytest session: '+name)
        if len(calls)!=expected:
            raise StopCampaign('evidence_failure',f'{name}: expected {expected} call reports, found {len(calls)}')
        if not allow_failure and any(r['outcome']!='passed' for r in calls):
            raise StopCampaign('test_failure_unclassified',name+' has a nonpassing call report')
        return calls

    try:
        prepare_command=[sys.executable,'-u','-B',str(repo/'hf_repo/scripts/s0_preparation_evidence.py'),
                         '--root',str(root),'--repo',str(repo),'--action','prepare']
        execute('P0_prepare','P0',prepare_command)
        manifest_hash=sha(root/'input_manifest.json');selected['source_manifest_sha256']=manifest_hash
        verify()
        p1paths=[base/'tests/test_windows_owned_process.py',root/'aux/hf_repo/tests/test_s0_event_logging.py']
        execute('P1_tests','P1',pytest_command('P1_tests',p1paths,selected));reports('P1_tests',8)
        verify()
        p2_deadline=time.monotonic()+60.
        target=str(base/'tests/test_compensated_invariants.py')+'::'+NODE
        baseline=execute('P2_baseline','P2',pytest_command('P2_baseline',[target],selected),
                         phase_deadline=p2_deadline,observe=True)
        baseline_reports=reports('P2_baseline',1,allow_failure=True)
        if not baseline_reports[0].get('nodeid','').replace('\\','/').endswith('tests/test_compensated_invariants.py::'+NODE):
            raise StopCampaign('evidence_failure','Wrong baseline test executed')
        observed=baseline_reports[0]
        if ((baseline['returncode']==1 and (observed['outcome']!='failed' or not observed.get('traceback')
                                           or not observed.get('exception_type')))
            or (baseline['returncode']==0 and observed['outcome']!='passed')):
            raise StopCampaign('evidence_failure','Baseline observation lacks a complete typed call report')
        verify()
        execute('P2_controls','P2',[sys.executable,'-u','-B',str(aux/'probe_s0_preparation.py'),
            '--root',str(root),'--source',str(base),'--mode','controls'],phase_deadline=p2_deadline)
        verify()
        execute('classification','shared',worker('classify_and_fix'))
        selected=read(root/'selected_source.json')
        verify()
        selected_root=Path(selected['source'])
        execute('P3_arithmetic','P3',pytest_command('P3_arithmetic',
            [selected_root/'tests/test_compensated_invariants.py'],selected))
        reports('P3_arithmetic',9);verify()
        for mode,bucket in (('force','P4'),('tangent','P5')):
            execute(bucket+'_'+mode,bucket,[sys.executable,'-u','-B',str(aux/'probe_s0_preparation.py'),
                '--root',str(root),'--source',str(selected_root),'--mode',mode])
            verify()
        status='diagnostic_complete_no_scientific_admission'
    except StopCampaign as exc:
        status=exc.status;error={'type':type(exc).__name__,'message':str(exc)}
    except BaseException as exc:
        status='parent_exception';error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    finally:
        # Only preservation/finalization follows a stop. P6 cannot restart science.
        dump(root/'resources.json',{'phases':phases,'status':status,'error':error,
            'total_elapsed_seconds':time.monotonic()-start,
            'plot_scope':'completed phases before P6; final receipt includes P6'})
        if (root/'input_manifest.json').exists() and evidence.exists() and time.monotonic()<deadline-6.:
            try: execute('P6_seal','P6',worker('seal'))
            except StopCampaign as exc:
                error={'prior':error,'seal_error':str(exc)};status=exc.status
            except BaseException as exc:
                error={'prior':error,'seal_error':repr(exc)};status='seal_failure'
        else:
            error={'prior':error,'seal_error':'No complete preparation or time for seal'}
            if status=='diagnostic_complete_no_scientific_admission':status='resource_stop'
        if time.monotonic()>deadline:status='resource_stop'
        ledger.update(status=status,error=error,finished_utc=utc(),elapsed_seconds=time.monotonic()-start,
            selected_source=selected,source_manifest_sha256=manifest_hash)
        replace(root/'ledger.json',ledger)
        dump(root/'execution_receipt.json',ledger)
        dump(root/'receipt_binding.json',{'schema':'hf-s0-receipt-binding-1',
            'plan_sha256':sha(root/'plan.json'),'input_manifest_sha256':manifest_hash,
            'receipt_sha256':sha(root/'execution_receipt.json'),
            'output_manifest_sha256':sha(root/'output_sha256.json') if (root/'output_sha256.json').exists() else None,
            'selected_source_manifest_sha256':selected.get('source_manifest_sha256'),
            'seal_event_sha256':sha(root/'events/P6_seal.ndjson') if (root/'events/P6_seal.ndjson').exists() else None,
            'seal_log_sha256':sha(root/'logs/P6_seal.log') if (root/'logs/P6_seal.log').exists() else None,
            'sealed_utc':utc(),'elapsed_campaign_seconds':time.monotonic()-start,
            'diagnostic_only':True,'scientific_admission':False})
        print(json.dumps({'status':status,'seconds':time.monotonic()-start,'error':error}),flush=True)
    return 0 if status=='diagnostic_complete_no_scientific_admission' else 1

if __name__=='__main__':raise SystemExit(main())
