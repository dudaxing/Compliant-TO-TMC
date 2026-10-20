"""Prepare one authorized same-kind saved unload using ordinary metadata/seal/stat."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_002'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_001'
PARENT=OLD+'/run_001/wave_circle_tip_alpha_unload1'
BASELINE='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/view/wave_circle_tip_alpha1/summary.json'
TEMPLATE='lf_data_preparation/native_interface_001/lf_circle_tip_unload_002/protocol.json'
BASE='c8c3b1c69f36d8a93bfefbad3439c8dd33dbf755'
CARD='L-CTIPAUNLOAD2'
REQUEST='好的，按 L-CTIPAUNLOAD2 计划实施并执行，仅从1.05 mm保存态卸载至1.00 mm。保持α=2.5e−7、半径9 mm、圆心(80,40) mm、右域界92 mm、Lr80 mm及其余物理条件和原验收门，注意做好记录，可视化实际变形、反力、尖端、右侧介质和收敛情况，完成同位移对照，再根据结果安排后续工作。'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists() and not (AUTHOR/'protocol.proposed.json').exists()
    names=('execute_step.py','circle_saved_views.py','launch_step.py','plot_convergence.py')
    support=('close_step.py','publish_step.py','archive_publication.py','finalize_records.py','assemble_step.py','freeze_step.py','monitor_step.py')
    for name in names+support:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
    source=read(ROOT/OLD/'protocol.json')
    parent=read(ROOT/PARENT/'result.json')
    original=read(ROOT/OLD/'step_task.json')
    prefix=[0.,.25,.5,.75,.9,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06,1.05]
    assert original['path']==dict(kind='ordered_cycle',targets_mm=prefix)
    assert original['regularization']==dict(alpha=2.5e-7,length_mm=80.)
    assert parent['status']=='success' and parent['reached_displacement']==1.05 and len(parent['states'])==2
    assert parent['targets_mm']==[1.06,1.05] and parent['task_target_executed'] is False
    assert parent['continuation']['parent_continuation'] is None
    selected=parent['states'][1]
    assert selected['original_target_index']==13 and selected['d']==1.05 and selected['leg']=='unloading'
    assert selected['state_sha256']=='e21cdc845dc3721bc32d9275f889f53e9b1560dcd7ca126a28ea8efa2254e2ee'
    assert selected['R_input']==.19075825359298318
    metadata={key:original[key] for key in ('task_id','purpose','parameter_origin','description')}
    task=deepcopy(original);task['path']['targets_mm'].append(1.00)
    assert task['input']['target_mm']==1.06
    write(AUTHOR/'step_task.json',task)
    geometry=PARENT+'/model/source_geometry/geometry.json'
    payload=PARENT+'/model/source_geometry/geometry.npz'
    state=PARENT+'/accepted/001/state.npz'
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    old_inputs={name:dict(path=name,**seals[name]) for name in (payload,state)}
    assert old_inputs[payload]['sha256']==read(ROOT/geometry)['arrays']['sha256']
    assert old_inputs[state]['sha256']==selected['state']['sha256']
    for name,seal in old_inputs.items():assert (ROOT/name).stat().st_size==seal['bytes']
    baseline=read(ROOT/BASELINE)['rows'][7]
    assert (baseline['index'],baseline['original_target_index'],baseline['d_mm'],baseline['leg'])==(7,7,1.,'loading')
    assert baseline['state_sha256']=='77d9c615291d5856c0761f49a0e8686f7f71fbd81005d689631affc78ac81840'
    ordinary=[BASELINE,PARENT+'/result.json',PARENT+'/model/model.json',geometry,
        PARENT+'/accepted/001/state.json',OLD+'/step_task.json',OLD+'/protocol.json']
    inputs={name:pin(ROOT/name) for name in ordinary}
    inputs.update({name:seal['sha256'] for name,seal in old_inputs.items()})
    inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    sources={name:pin(ROOT/name) for name in source['source_bindings'] if name.startswith('hf_repo/')}
    sources.update({REL+'/'+name:pin(AUTHOR/name) for name in names})
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{name}.py' for name in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=read(ROOT/TEMPLATE)
    protocol.update(card=CARD,source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_alpha_unload2',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,geometry_file=geometry,
        original_task_file=OLD+'/step_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=prefix+[1.00],targets_mm=[1.05,1.00],same_input_reference_summary_json=BASELINE,
        settings=source['settings']|{'time_limit_seconds':1800.},options=deepcopy(source['options']),gates=deepcopy(source['gates']),
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=2,
        source_anchor=dict(accepted_index=1,original_target_index=13,d_mm=1.05,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        task_execution_scope='Only same-kind suffix [1.05,1.00], fresh anchor F/T revalidation, original14-target prefix inherited without replay; input target remains1.06. All task fields including four metadata exact except appending1.00. No new top-level task_transition; historical first-unload transition preserved.',
        qualification_scope='One alpha2.5e-7 same-kind unloading saved extension; no full-prefix replay, newHP, complete unloading/release, pressure/effective grip, stability, alpha independence, mesh/domain-width convergence or HF5 qualification.',
        display_selection_scope='Identity-only copies of the prior LAST-capable viewer and convergence; numerical definitions, layout, decoder, masks and viewer8GiB unchanged. Comparison second state/fields/right-medium use actual LAST1.00, peak_index remains actual child argmax metadata.',
        same_input_comparison_scope='13 original scalar values and descriptive differences only: ALPHA1 summary row7/global7 raw loading1.00 versus newglobal14 unloading1.00; preserve raw legs and SHA, no equality/recovery/monotonicity/hysteresis gate, no oldarray/media read.',
        direct_user_request=REQUEST,execution_authorization_status='explicitly_approved',
        execution_authorization_basis='Current direct human approval of L-CTIPAUNLOAD2 plan implementation and execution, from1.05 only to1.00, including original physics/gates and published1800/600/2700/2760sec64GiB16cap planned window, records/visuals/same-input comparison and normalmain publication/recovery.',
        created_utc=datetime.now(timezone.utc).isoformat())
    assert 'expected_task_transition' not in protocol
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        status='explicitly_approved',approval_recorded_utc=datetime.now(timezone.utc).isoformat(),
        scope='One same-kind1.05 to1.00 saved unload with actualLAST views, descriptive13same-input scalars, records, normalmain push and same-machine different-path localGit restoration under originalphysics/gates; noHP/tests/defaultHF changes.'))
    receipt=dict(status='prepared_authorized_not_executed',created_utc=datetime.now(timezone.utc).isoformat(),
        card=CARD,source_baseline_commit=BASE,source_bindings=len(sources),input_bindings=len(inputs),
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),task_sha256=pin(AUTHOR/'step_task.json'),
        old_payload_reads=0,old_payload_hash_reads=0,new_scientific_calls=0,tests_run=0,
        formal_stage_created=False,default_HF_changes=0,git_mutations=0,authorized=True)
    write(AUTHOR/'preparation_receipt.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':main()
