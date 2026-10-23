"""Summarize immutable new ordinary receipts after the unique window closed."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

AUTHOR=Path(__file__).resolve().parent
BASE=Path('D:/hfl1_001')
def read(path): return json.loads(Path(path).read_bytes())
def identity(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def write(path,row): path.write_bytes((json.dumps(row,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
p=read(BASE/'protocol.json')
layers=[]
for name in ('top_supervision.json','outer_supervision.json','run_001/tests_supervision.json','run_001/viewer_supervision.json'):
    row=read(BASE/name); proof=row['cleanup_proof']
    assert row['reason']=='normal_exit' and row['returncode']==0 and row['cleanup_verified'] is True
    assert proof['pass'] and proof['coverage_verified'] and proof['termination_verified'] and proof['job_handle_closed']
    assert proof['final_accounting']['ActiveProcesses']==0
    layers.append(dict(path=name,reason=row['reason'],returncode=0,cleanup_verified=True,
        identity=identity(BASE/name),elapsed_seconds=row['elapsed_seconds'],
        sampled_peak_tree_rss_bytes=row['peak_tree_rss_bytes'],
        all_instances=proof['unique_bound_identity_count'],job_handle_closed=True))
cases=ET.parse(BASE/'run_001/pytest.xml').findall('.//testcase')
assert len(cases)==17 and not any(c.find(k) is not None for c in cases for k in ('failure','error','skipped'))
installation=read(BASE/'installation_receipt.json')
assert installation['status']=='pass' and len(installation['installed'])==2
for item in p['install_files']:
    assert identity(item['target'])==identity(item['source'])=={k:item[k] for k in ('bytes','sha256')}
for item in p['original_production']:
    assert identity(item['path'])=={k:item[k] for k in ('bytes','sha256')}
seal=read(BASE/'seal_receipt.json')
assert seal['status']=='pass' and seal['attempts']==1 and seal['elapsed_helper_seconds']<480 and seal['elapsed_outer_seconds']<540
assert identity(BASE/'execution_evidence.zip')==seal['archive']
assert read(BASE/'execution_receipt.json')['status']=='pass'
qa=read(BASE/'root_qa.json'); assert qa['status']=='pass' and qa['pixel_inspections']==1
summary=read(BASE/'run_001/artifacts/validation_summary.json')
force=read(summary['force_result_file']); rows=force['accepted_steps']
assert force['status']=='success' and force['target_reached'] and len(rows)==3
result=dict(stage='L-CTIPFLOAD1',status='PASS',scientific_window_closed=True,
    created_utc=datetime.now(timezone.utc).isoformat(),baseline=p['baseline'],
    pytest_items_passed=17,new_methods_passed=8,new_real_paths=4,legacy_real_paths=1,
    new_control_calls=30,legacy_control_calls=11,controlled_partial_overlap=1,
    supervised_layers=layers,installation=installation,original_production_unchanged=55,
    root_pixel_inspections=1,rerenders=0,seal=seal,archive_identity_verified_without_decode=True,
    cross_checks=summary['cross_checks'],force_call_counts=force['call_counts'],
    accepted_scalar_rows=[{k:r[k] for k in ('P_target_half_N','body_q_mm','input_mean_mm','R_input_N',
        'relative_residual','relative_generalized_force_residual','constraint_residual','constraint_bound',
        'relative_global_force_balance','minimum_J','max_abs_Hu_per_mm','max_abs_prescribed_error_mm','newton_checks')} for r in rows],
    qualification='Small-model guided signed axial total-force control only; no formal r9/HP/pressure/capacity/release/stability qualification',
    new_science_in_this_closure_audit=0,NPZ_decodes_in_this_closure_audit=0)
with (AUTHOR/'EXECUTION_RESULT.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2); stream.write('\n')
live=read(AUTHOR/'LIVE_HANDOFF.json')
live.update(status='closed_PASS_no_reopen',unique_exec_exit_code=0,
    elapsed_outer_seconds=seal['elapsed_outer_seconds'],new_modules_installed=2,
    scientific_window_closed=True,next_action='Record and publish; future real r9 science requires its own approved scope/window.')
write(AUTHOR/'LIVE_HANDOFF.json',live)
print(json.dumps(dict(status='PASS',tests=17,old55='unchanged',installed=2,cleanup_layers=4,
    elapsed=seal['elapsed_outer_seconds'],NPZ_decodes=0)))
