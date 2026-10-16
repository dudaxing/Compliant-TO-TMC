"""Package and freeze approved study files; no HF import, arrays or execution."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_batch_forward_001'
BASE='ff448447a135d31314f7a0bd88e6ddd8ed449bfb'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
assert not STAGE.exists()
review=read(AUTHOR/'SOURCE_REVIEW.json')
assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
STAGE.mkdir(parents=True,exist_ok=False)
(STAGE/'author').mkdir()
(STAGE/'tasks').mkdir()
(STAGE/'example').mkdir()
for name in ['planning_record.json','CARD_REVIEW.md','CARD_REVIEW.json','COST_BASIS.md','COST_BASIS.json',
             'CONTRACT.md','CONTRACT.json','VIEWS.md','VIEWS.json','SOURCE_REVIEW.md','SOURCE_REVIEW.json']:
    (STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
(STAGE/'L-BFWD1_CARD.md').write_bytes((AUTHOR/'L_BFWD1_CARD.md').read_bytes())
for name in ['execute_batch.py','display_batch.py','launch_batch.py','example/plot_convergence.py']:
    ast.parse((AUTHOR/name).read_bytes())
    (STAGE/name).write_bytes((AUTHOR/name).read_bytes())
for i in range(2):
    (STAGE/'tasks'/f'{i:03d}.json').write_bytes((AUTHOR/f'task_{i:03d}.proposed.json').read_bytes())
(STAGE/'batch_manifest.json').write_bytes((AUTHOR/'batch_manifest.proposed.json').read_bytes())
cwd=AUTHOR/'execution_cwd'
cwd.mkdir(exist_ok=False)
planning=read(AUTHOR/'planning_record.json')
batch=read(STAGE/'batch_manifest.json')
pilot=read(ROOT/'lf_data_preparation/native_interface_001/lf_third_pilot_001/protocol.json')
views=read(AUTHOR/'VIEWS.json')
old_prefix={
    'gripper_native_fine':'lf_data_preparation/native_interface_001/lf_forward_001/run_001/lf_fine_forward/result.json',
    'gripper_wave_fine':'lf_data_preparation/native_interface_001/lf_third_pilot_001/run_001/lf_third_pilot/result.json'}
inputs={}
for row in planning['cases']:
    for key in ['parent_task','geometry']:
        inputs[row[key]['path']]=row[key]['sha256']
        assert pin(ROOT/row[key]['path'])==row[key]['sha256']
    inputs[row['geometry_NPZ']['path']]=row['geometry_NPZ']['sha256']
    assert (ROOT/row['geometry_NPZ']['path']).stat().st_size==row['geometry_NPZ']['bytes']
for path in list(old_prefix.values())+['lf_data_preparation/native_interface_001/lf_third_pilot_001/protocol.json']:
    inputs[path]=pin(ROOT/path)
for name in ['batch_manifest.json','tasks/000.json','tasks/001.json']:
    inputs[(STAGE/name).relative_to(ROOT).as_posix()]=pin(STAGE/name)
# Freeze the declared default package and entry points, without claiming every
# bound module is imported by this path. No installed source file is changed.
sources={name for name in pilot['source_bindings'] if name.startswith('hf_repo/src/hf_eval/') and name.endswith('.py')}
sources.update(views['viewer']['pure_source_bindings'])
sources.update(['hf_repo/pyproject.toml','hf_repo/src/hf_eval/native_batch.py',
                'hf_repo/src/hf_eval/native_evaluate.py','hf_repo/scripts/evaluate_native_batch.py',
                'hf_repo/scripts/windows_owned_process_sup2.py'])
sources.update((STAGE/name).relative_to(ROOT).as_posix() for name in
               ['execute_batch.py','display_batch.py','launch_batch.py','example/plot_convergence.py'])
task0=read(STAGE/'tasks/000.json')
metadata={k:task0[k] for k in ('task_id','purpose','parameter_origin','description')}
protocol=dict(schema_version='lf-prepared-batch-short-forward-card-1.0',card='L-BFWD1',
    source_baseline_commit=BASE,helper_seconds=4500,outer_seconds=4560,
    controller_seconds_per_case=1800,viewer_seconds=600,sampled_RSS_bytes=8*1024**3,
    working_directory=cwd.as_posix(),output_directory=(STAGE/'run_001').relative_to(ROOT).as_posix(),
    manifest_file=(STAGE/'batch_manifest.json').relative_to(ROOT).as_posix(),
    original_task_files=[row['parent_task']['path'] for row in planning['cases']],
    task_metadata=metadata,targets_mm=[0.,.25,.5],settings=batch['options']['settings'],
    options={k:batch['options'][k] for k in ('response_mode','tangent_mode','initial_guess')},
    gates=pilot['gates'],gates_source_protocol='lf_data_preparation/native_interface_001/lf_third_pilot_001/protocol.json',old_prefix_results=old_prefix,
    viewer_source=views['viewer']['path'],convergence_source=(STAGE/'example/plot_convergence.py').relative_to(ROOT).as_posix(),
    display_source=(STAGE/'display_batch.py').relative_to(ROOT).as_posix(),
    input_bindings=inputs,source_bindings={name:pin(ROOT/name) for name in sorted(sources)},
    source_binding_scope='Declared default execution package plus pure-view closure and study wrappers; not a claim that every module is imported',
    expected_cases=2,expected_requested_targets_per_case=3,expected_PNGs=5,expected_GIFs=2,
    accepted_states_policy='Actual N may grow through original bounded bisection; every actual accepted state is saved and viewed',
    default_installations=0,new_tests=0,new_HP_calls=0,
    scope='One current batch consumes two prepared fixed-square LF geometries under explicit independent short tasks; raw cached production gates and saved-only views',
    stop_policy='First terminal non-success stops later cases and all displays; API failure forwarded unchanged; original in-window partial seal only; no retry, repair rerun, extension, force, rollback or deletion',
    created_utc=datetime.now(timezone.utc).isoformat())
write(STAGE/'protocol.json',protocol)
write(STAGE/'author/authorization.json',dict(card='L-BFWD1',authorized=True,
    authorization_from_direct_human_reply=True,one_invocation=True,
    direct_human_answer='批准按 L-BFWD1 卡实施并执行',authorized_execution_source_commit=BASE,
    protocol_sha256=pin(STAGE/'protocol.json'),approved_card_sha256=pin(STAGE/'L-BFWD1_CARD.md'),
    scope='Approved minimal study implementation/static review/freeze, one bounded batch and saved views, up to one inspection per new PNG, records/main publication/restoration'))
print(json.dumps(dict(status='frozen_not_executed',protocol_sha256=pin(STAGE/'protocol.json'),
    input_bindings=len(inputs),source_bindings=len(sources),default_changes=0)))
