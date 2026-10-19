"""Prepare one approved 1.06 to 1.05 first unload; no existing payload reads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_unload_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_step_010'
PARENT=OLD+'/run_001/wave_circle_tip_step10'
BASE='6cac08b4a9ea30bf295d9e4da3fddb8d55e94ba5'
CARD='L-CTIPUNLOAD1'
REQUEST='批准按 L-CTIPUNLOAD1 计划实施并执行'
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
    prefix=[0.,.25,.5,.75,.9,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06]
    assert original['path']==dict(kind='load_only',targets_mm=prefix)
    assert parent['status']=='success' and parent['reached_displacement']==1.06 and len(parent['states'])==2
    selected=parent['states'][1]
    assert selected['original_target_index']==12 and selected['d']==1.06
    assert selected['state_sha256']=='dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6'
    assert selected['R_input']==.19568183324206792
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c80_domain92_Lr80_h05_alpha5em7_unload106_105__L_CTIPUNLOAD1',
        purpose='tip_facing_circle_LF_saved_first_unload',
        parameter_origin='L-CTIPUNLOAD1 explicit user approval: retain the complete loading prefix through 1.06 mm, change only path kind to ordered_cycle and append first unload1.05 mm; input peak1.06 and all original physics/settings/gates unchanged.',
        description='Freshly revalidate true1.06 mm peak, then unload to1.05 using the installed API. Observe actual LAST state and descriptively compare prior revalidated loading1.05 scalars without new equality gates.')
    task=deepcopy(original);task.update(metadata)
    task['path']['kind']='ordered_cycle';task['path']['targets_mm'].append(1.05)
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
    same_input=OLD+'/run_001/view/wave_circle_tip_step10/summary.json'
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
    protocol.update(schema_version='lf-circle-tip-first-unload-card-1.0',card=CARD,source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_unload1',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,geometry_file=geometry,
        original_task_file=OLD+'/step_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=prefix+[1.05],targets_mm=[1.06,1.05],
        same_input_reference_summary_json=same_input,
        expected_task_transition=dict(source_path_kind='load_only',extended_path_kind='ordered_cycle',first_unload=True,loading_peak_mm=1.06,first_unload_target_mm=1.05),
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=2,
        source_anchor=dict(accepted_index=1,original_target_index=12,d_mm=1.06,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        task_execution_scope='Only first-unload suffix [1.06,1.05] including fresh peak F/T; full original loading prefix inherited, not replayed. Input target remains1.06.',
        qualification_scope='One first-unload saved extension with actual observations; no full-prefix replay, newHP, complete unloading/release, pressure/effective grip, stability, mesh/domain-width convergence or HF5 qualification.',
        display_selection_scope='Comparison anchor versus actual LAST accepted state; field/right-medium static maps use LAST with matching captions, while true peak_index remains peak metadata. Numerical definitions and decoder scope unchanged.',
        same_input_comparison_scope='13 available original scalar values and descriptive differences only: oldSTEP10 summary row0/global11 inherited loading1.05 anchor versus newglobal13 unloading1.05; preserve raw legs and SHA, no equality/recovery/monotonicity/hysteresis gate, no oldarray/media read.',
        direct_user_request=REQUEST,execution_authorization_status='explicitly_approved',
        execution_authorization_basis='Explicit current human approval of L-CTIPUNLOAD1 and published REF1 NEXT_STEPS at6cac08b; one first1.06 to1.05 mm unloading target, actual LAST views and same-input scalar comparison under its stated new resource window.',
        created_utc=datetime.now(timezone.utc).isoformat())
    protocol.pop('preparation_basis',None)
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        status='explicitly_approved',scope='One first1.06 to1.05 saved unload, actualLAST views and descriptive same-input scalar comparison, records, normalmain push/localGit different-path restoration under originalphysics and gates; noHP/tests/defaultHF changes.'))
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(sources),input_bindings=len(inputs),old_payload_reads=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
