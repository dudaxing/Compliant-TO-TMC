"""Record the one completed window using new ordinary receipts only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

AUTHOR=Path(__file__).resolve().parent
BASE=Path('D:/hfr1_001')
RUN=BASE/'run_001'
def read(path): return json.loads(Path(path).read_bytes())
def identity(path):
    raw=path.read_bytes(); return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
def write(path,row): path.write_bytes((json.dumps(row,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
p=read(BASE/'protocol.json'); seal=read(BASE/'seal_receipt.json')
layers=[]
for name in ('top_supervision.json','run_001/science_supervision.json','run_001/comparison_supervision.json','run_001/viewer_supervision.json'):
    path=BASE/name
    if path.exists():
        row=read(path); proof=row.get('cleanup_proof',{})
        layers.append(dict(path=name,**identity(path),reason=row['reason'],returncode=row['returncode'],
            cleanup_verified=row['cleanup_verified'],job_handle_closed=proof.get('job_handle_closed'),
            complete_instance_proof=proof.get('pass'),active_processes=proof.get('final_accounting',{}).get('ActiveProcesses'),
            elapsed_seconds=row['elapsed_seconds'],sampled_peak_tree_rss_bytes=row['peak_tree_rss_bytes']))
if seal['status']=='pass': assert identity(BASE/'execution_evidence.zip')==seal['archive']
if seal['execution_pass']:
    assert len(layers)==4 and all(x['reason']=='normal_exit' and x['returncode']==0
        and x['cleanup_verified'] and x['job_handle_closed'] and x['complete_instance_proof'] and x['active_processes']==0 for x in layers)
for pin in p['production']:
    assert identity(Path(pin['path']))=={key:pin[key] for key in ('bytes','sha256')}
def optional(path): return read(path) if path.exists() else None
science=optional(RUN/'science_receipt.json'); force=optional(RUN/'force/result.json')
comparison=optional(RUN/'comparison.json'); renderer=optional(RUN/'view/renderer_receipt.json')
geometry=optional(RUN/'view/geometry_metrics.json'); qa=optional(BASE/'root_qa.json')
status='PASS' if seal['execution_pass'] and seal['status']=='pass' else 'NOT_PASS'
result=dict(stage='L-CTIPFREAL1',status=status,scientific_window_closed=True,
    created_utc=datetime.now(timezone.utc).isoformat(),baseline=p['baseline'],
    seal=seal,supervised_layers=layers,production_sources_unchanged=57,
    new_HP=0,new_tests=0,new_production_modifications=0,external_retries=0,
    science_receipt=science,comparison=comparison,renderer=renderer,root_QA=qa,
    geometry_metrics=geometry,new_science_in_this_recording=0,NPZ_decodes_in_this_recording=0,
    force_summary=None if force is None else dict(status=force['status'],failure=force['failure'],
        target_reached=force['target_reached'],force_task=force['force_task'],settings=force['settings'],
        force_settings=force['force_settings'],response_mode=force['response_mode'],tangent_mode=force['tangent_mode'],
        initial_guess=force['initial_guess'],parent_initial_guess=force['parent_initial_guess'],
        call_counts=force['call_counts'],path_summary=force['path_summary'],
        scalar_rows=[{key:row[key] for key in ('P_target_half_N','body_q_mm','input_mean_mm','R_input_N',
            'force_on_body_N','ledger','relative_residual','relative_generalized_force_residual',
            'generalized_force_residual_half_N','generalized_force_scale_half_N','generalized_force_bound_half_N',
            'constraint_residual','constraint_bound','minimum_J','max_abs_Hu_per_mm','relative_global_force_balance',
            'max_abs_prescribed_error_mm','newton_checks','is_original_target','original_target_index','bisection_depth','state_sha256')}
            for row in force['accepted_steps']],
        Newton_base_checks=len(force['newton_history']),trials=len(force['trials']),failed_attempts=force['failed_attempts']),
    qualification='Only the current two-load guided TMC total-force task and its separately recorded comparisons; no pressure, pure contact, capacity, release, stability, full-path HP or HF qualification')
with (AUTHOR/'EXECUTION_RESULT.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False); stream.write('\n')
live=read(AUTHOR/'LIVE_HANDOFF.json'); live.update(status='closed_'+status+'_no_reopen',
    scientific_window_closed=True,elapsed_outer_seconds=seal['elapsed_outer_seconds'],
    next_action='Record, inspect ordinary scalar evidence and publish; no further science under this closed window.')
write(AUTHOR/'LIVE_HANDOFF.json',live)
print(json.dumps(dict(status=status,supervised_layers=len(layers),elapsed=seal['elapsed_outer_seconds'],
    production_unchanged=57,recording_scientific_calls=0)))
