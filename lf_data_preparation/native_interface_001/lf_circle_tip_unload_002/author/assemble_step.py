"""Prepare the approved 1.05 to 1.00 saved unload without old payload reads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_unload_002'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_unload_001'
PARENT=OLD+'/run_001/wave_circle_tip_unload1'
BASE='52ba58df1958523c457b9db970683ed28ac483b2'
CARD='L-CTIPUNLOAD2'
REQUEST='批准按 L-CTIPUNLOAD2 计划实施并执行'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists()
    names=('execute_step.py','circle_saved_views.py','launch_step.py','plot_convergence.py')
    for name in names+('close_step.py','publish_step.py','archive_publication.py','assemble_step.py','freeze_step.py'):
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
    source=read(ROOT/OLD/'protocol.json')
    parent=read(ROOT/PARENT/'result.json')
    original=read(ROOT/OLD/'step_task.json')
    prefix=[0.,.25,.5,.75,.9,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06,1.05]
    assert original['path']==dict(kind='ordered_cycle',targets_mm=prefix)
    assert parent['status']=='success' and parent['reached_displacement']==1.05 and len(parent['states'])==2
    selected=parent['states'][1]
    assert selected['original_target_index']==13 and selected['d']==1.05 and selected['leg']=='unloading'
    assert selected['state_sha256']=='64b9301899b2599203140b634ffc5340e5d0a7c31ce75d0931203a6b72d58d1d'
    assert selected['R_input']==.1917119776052677
    task=deepcopy(original);task['path']['targets_mm'].append(1.00)
    unchanged=deepcopy(task);unchanged['path']['targets_mm']=deepcopy(prefix)
    assert unchanged==original and task['input']['target_mm']==1.06
    metadata={name:deepcopy(original[name]) for name in ('task_id','purpose','parameter_origin','description')}
    write(AUTHOR/'step_task.json',task)
    geometry=PARENT+'/model/source_geometry/geometry.json'
    payload=PARENT+'/model/source_geometry/geometry.npz'
    state=PARENT+'/accepted/001/state.npz'
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    old_inputs={name:dict(path=name,**seals[name]) for name in (payload,state)}
    assert old_inputs[payload]['sha256']==read(ROOT/geometry)['arrays']['sha256']
    assert old_inputs[state]['sha256']==selected['state']['sha256']
    for name,seal in old_inputs.items():assert (ROOT/name).stat().st_size==seal['bytes']
    same_input='lf_data_preparation/native_interface_001/lf_circle_tip_step_006/run_001/view/wave_circle_tip_step6/summary.json'
    ordinary=[same_input,PARENT+'/result.json',PARENT+'/model/model.json',geometry,
        PARENT+'/accepted/001/state.json',OLD+'/step_task.json',OLD+'/protocol.json']
    inputs={name:pin(ROOT/name) for name in ordinary}
    inputs.update({name:seal['sha256'] for name,seal in old_inputs.items()})
    inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    sources={name:pin(ROOT/name) for name in source['source_bindings'] if name.startswith('hf_repo/')}
    sources.update({REL+'/'+name:pin(AUTHOR/name) for name in names})
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{name}.py' for name in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=deepcopy(source)
    protocol.pop('expected_task_transition',None)
    protocol.update(schema_version='lf-circle-tip-saved-unload-card-1.0',card=CARD,source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_unload2',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,geometry_file=geometry,
        original_task_file=OLD+'/step_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=prefix+[1.00],targets_mm=[1.05,1.00],same_input_reference_summary_json=same_input,
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=2,
        source_anchor=dict(accepted_index=1,original_target_index=13,d_mm=1.05,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        task_execution_scope='Only saved-unload suffix [1.05,1.00] including fresh anchor F/T; full original prefix inherited, not replayed. Task input peak stays1.06; child segment maximum1.05 and loading_peak_reached false.',
        qualification_scope='One saved unloading extension with actual observations; no full-prefix replay, newHP, complete unloading/release, pressure/effective grip, stability, mesh/domain-width convergence or HF5 qualification.',
        display_selection_scope='Byte-exact UNLOAD1 LAST-capable viewer and convergence: comparison anchor versus actual LAST, fields/right-medium static maps LAST; peak_index remains segment-maximum metadata. Numerical definitions and decoder scope unchanged.',
        same_input_comparison_scope='13 available original scalar values and descriptive differences only: oldSTEP6 summary row0/global7 inherited loading1.00 anchor versus newglobal14 unloading1.00; preserve raw legs and SHA, no equality/recovery/monotonicity/hysteresis gate, no oldarray/media read.',
        direct_user_request=REQUEST,execution_authorization_status='explicitly_approved',
        execution_authorization_basis='Explicit current human approval of L-CTIPUNLOAD2 and published UNLOAD1 NEXT_STEPS at52ba58d, with two previously explained source-contract corrections: inherit all task metadata; child peak flag false and segment maximum1.05. Physics, gates and resources unchanged.',
        created_utc=datetime.now(timezone.utc).isoformat())
    protocol.pop('preparation_basis',None)
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        status='explicitly_approved',scope='One saved1.05 to1.00 unload, inherited task fields except appended target, actualLAST views and descriptive same-input scalar comparison, records, normalmain push/localGit different-path restoration under originalphysics and gates; noHP/tests/defaultHF changes.'))
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(sources),input_bindings=len(inputs),old_payload_reads=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
