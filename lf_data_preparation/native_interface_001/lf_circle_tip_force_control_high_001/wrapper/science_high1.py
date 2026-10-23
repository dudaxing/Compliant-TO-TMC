"""One authorized force-control API call from the original fixed 1.06 mm high peak."""
import time
START=time.monotonic()

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

BASE=Path(__file__).resolve().parent
RUN=BASE/'run_001'
def read(path): return json.loads(Path(path).read_bytes())
def write(path,row):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(row,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')
def progress(row):
    path=RUN/'science_progress.pending.json'
    path.write_text(json.dumps(row,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    os.replace(path,RUN/'science_progress.json')
def identity(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def main():
    if len(sys.argv)!=1 or (RUN/'science_receipt.json').exists() or (RUN/'force').exists():
        raise ValueError('Only the unique frozen run is authorized')
    p=read(BASE/'protocol.json'); bound=read(p['source_binding_file'])
    receipt=dict(stage='L-CTIPFHIGH1',status='not_pass',api_attempts=0,api_returns=0,
        started_utc=datetime.now(timezone.utc).isoformat(),external_retries=0,
        new_tests=0,new_HP=0,production_modifications=0,accepted_callbacks=[])
    allowed={os.path.normcase(str(Path(row['path']).resolve())) for row in bound['scientific_payloads_stat_only']
             if row['role'].startswith('admission_')}
    if len(allowed)!=3:
        raise ValueError('Frozen admission requires precisely three old NPZ paths')
    reads=[]
    def audit(event,args):
        if event!='open' or not isinstance(args[0],(str,bytes)):
            return
        path=Path(os.fsdecode(args[0]))
        if path.suffix.lower()!='.npz':
            return
        normalized=os.path.normcase(str(path.resolve()))
        access=args[2] & (os.O_WRONLY | os.O_RDWR)
        if access!=os.O_RDONLY and not path.resolve().is_relative_to(RUN/'force'):
            raise RuntimeError('NPZ write outside the new force output: '+str(path))
        if access==os.O_WRONLY:
            return
        row=dict(path=str(path.resolve()),elapsed_worker_seconds=time.monotonic()-START,allowed=normalized in allowed)
        reads.append(row)
        if normalized not in allowed:
            raise RuntimeError('NPZ read outside the three frozen admission paths: '+str(path))
    sys.addaudithook(audit)
    try:
        for item in p['bindings']:
            if identity(item['path'])!={k:item[k] for k in ('bytes','sha256')}:
                raise ValueError('Frozen ordinary source changed: '+item['path'])
        progress(dict(stage='L-CTIPFHIGH1',phase='import_and_source_admission_pending',accepted_count=0,
            elapsed_worker_seconds=time.monotonic()-START))
        from hf_eval.native_guided_force import GuidedForceSettings, evaluate_native_guided_force
        import hf_eval.native_guided_force as implementation
        if Path(implementation.__file__).resolve()!=Path(p['production_src'])/'hf_eval/native_guided_force.py':
            raise ValueError('Imported implementation is not the bound installed module')
        def on_accept(row):
            measured={key:row[key] for key in ('P_target_half_N','body_q_mm','input_mean_mm','R_input_N',
                'relative_residual','relative_generalized_force_residual','minimum_J',
                'max_abs_Hu_per_mm','relative_global_force_balance','newton_checks',
                'is_original_target','original_target_index','bisection_depth','state_sha256')}
            measured['elapsed_worker_seconds']=time.monotonic()-START
            receipt['accepted_callbacks'].append(measured)
            progress(dict(stage='L-CTIPFHIGH1',phase='accepted_force_state',
                accepted_count=len(receipt['accepted_callbacks']),last=measured))
            print(json.dumps(dict(phase='accepted',index=len(receipt['accepted_callbacks'])-1,**measured)),flush=True)
        receipt['api_attempts']=1
        result=evaluate_native_guided_force(p['parent_result'],p['selected_state_index'],
            p['loads_half_N'],RUN/'force',
            force_settings=GuidedForceSettings(minimum_force_increment_half_N=p['nmin_half_N']),
            time_limit_seconds=p['controller_seconds'],on_accept=on_accept)
        receipt['api_returns']=1
        receipt.update(production_status=result['status'],production_failure=result['failure'],
            target_reached=result['target_reached'],accepted_states=len(result['accepted_steps']),
            call_counts=result['call_counts'],result_identity=identity(RUN/'force/result.json'),
            API_decoded_fields=6,
            decoded_field_count_basis='Successful completed _admit control flow in byte-frozen source: geometry four masks and selected split two fields. Open events monitored; field accesses not dynamically hooked.')
        if result['status']!='success' or result['target_reached'] is not True:
            raise RuntimeError('Unique force-control path did not complete; preserve its actual result/partial')
        selected=bound['parent_binding']
        if (result['source']['parent_result']['sha256']!=selected['result_file_sha256']
                or result['source']['selected_state']['accepted_index']!=12
                or result['force_task']['held_input_mean_mm']!=1.06
                or result['force_task']['body_load_targets_half_N']!=p['loads_half_N']
                or result['force_task']['known_q_target_supplied'] is not False
                or result['response_mode']!='mechanical' or result['tangent_mode']!='chunk256'
                or result['initial_guess']!='guided_reduced_tangent'
                or result['parent_initial_guess']!='port_projection'
                or result['model']['body_nodes']!=bound['physics']['body_nodes']
                or len(result['model']['coordinates_mm'])!=14985
                or len(result['model']['connectivity'])!=14720
                or len(result['accepted_steps'])>17
                or len(receipt['accepted_callbacks'])!=len(result['accepted_steps'])
                or result['settings']!={**selected['settings_nonclock'],'time_limit_seconds':3600.0}
                or result['call_counts']['solver_invocations']!=1
                or result['call_counts']['HP_calls']!=0
                or result['call_counts']['save_force_calls']!=0
                or result['call_counts']['save_tangent_calls']!=0):
            raise ValueError('Completed result differs from the frozen physical/execution contract')
        actual={os.path.normcase(str(Path(row['path']).resolve())) for row in reads}
        if actual!=allowed:
            raise ValueError('Actual admission NPZ open set differs from the three bound paths')
        receipt['status']='pass'
    except BaseException as error:
        receipt['error']=dict(type=type(error).__name__,code=getattr(error,'code',None),
            message=str(error),traceback=traceback.format_exc())
    finally:
        receipt.update(elapsed_worker_seconds=time.monotonic()-START,npz_read_open_events=reads,
            unique_NPZ_read_paths=sorted({row['path'] for row in reads}),npz_open_audit_does_not_patch_HF_or_numpy=True)
        write(RUN/'science_receipt.json',receipt)
        progress(dict(stage='L-CTIPFHIGH1',phase='science_worker_closed',status=receipt['status'],
            accepted_count=len(receipt['accepted_callbacks']),elapsed_worker_seconds=receipt['elapsed_worker_seconds']))
        print(json.dumps(dict(status=receipt['status'],elapsed=receipt['elapsed_worker_seconds'])),flush=True)
    return 0 if receipt['status']=='pass' else 1

if __name__=='__main__':
    raise SystemExit(main())
