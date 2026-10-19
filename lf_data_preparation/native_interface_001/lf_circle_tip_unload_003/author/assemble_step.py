"""Prepare the approved five-target saved unload without old payload reads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_unload_003'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_unload_002'
PARENT=OLD+'/run_001/wave_circle_tip_unload2'
BASE='2fe7a5f942454ca75acc4ddd54b5926732afcb46'
CARD='L-CTIPUNLOAD3'
REQUEST='批准按 L-CTIPUNLOAD3 计划实施并执行'
APPENDED=[.90,.75,.50,.25,0.]
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
    prefix=[0.,.25,.5,.75,.9,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06,1.05,1.00]
    assert original['path']==dict(kind='ordered_cycle',targets_mm=prefix)
    assert parent['status']=='success' and parent['reached_displacement']==1.00 and len(parent['states'])==2
    selected=parent['states'][1]
    assert selected['original_target_index']==14 and selected['d']==1.00 and selected['leg']=='unloading'
    assert selected['state_sha256']=='0be638c03daaa369d3a740493f6e99bd6978e839709cf83029642fdf8abd2c0b'
    assert selected['R_input']==.17845354455643678
    task=deepcopy(original);task['path']['targets_mm'].extend(APPENDED)
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
    same_input='lf_data_preparation/native_interface_001/lf_circle_tip_pilot_001/run_001/view/wave_circle_tip_pilot/summary.json'
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
    protocol['settings']['time_limit_seconds']=5400.0
    protocol.update(schema_version='lf-circle-tip-saved-unload-card-1.0',card=CARD,source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        controller_seconds=5400,viewer_seconds=600,helper_seconds=6600,outer_seconds=6660,
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_unload3',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,geometry_file=geometry,
        original_task_file=OLD+'/step_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=prefix+APPENDED,targets_mm=[1.00]+APPENDED,same_input_reference_summary_json=same_input,
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=6,
        source_anchor=dict(accepted_index=1,original_target_index=14,d_mm=1.00,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        task_execution_scope='Only saved-unload suffix [1.00,.90,.75,.50,.25,0] including fresh anchor F/T; full original prefix inherited, not replayed. Task peak stays1.06; segment maximum1.00/loading_peak_reached false. Zero endpoint is input return only.',
        qualification_scope='One five-target saved unloading extension with actual observations; no full-prefix replay, newHP, complete original-path reference, pressure/effective grip, free release, stability, mesh/domain-width convergence or HF5 qualification.',
        display_selection_scope='Byte-exact UNLOAD2 LAST-capable viewer and convergence: compare anchor and actual LAST; fields/right-medium maps LAST, peak_index remains segment-maximum metadata. All accepted bisection states retained.',
        display_resource_scope='One600s clock shared by clean saved viewer/right-medium summary, convergence, table and page; original viewer internal8GiB cap retained. Seal inside helper6600.',
        same_input_comparison_scope='13 original scalar values and descriptive differences only: pilot summary row0/global0/rawleg origin versus newglobal19/unloading0. Old summary has no path_metadata; preserve raw origin and SHA, no loading-continuation assumption or equality/zero-force/recovery gate, no oldarray/media read.',
        direct_user_request=REQUEST,execution_authorization_status='explicitly_approved',
        execution_authorization_basis='Explicit current human approval of L-CTIPUNLOAD3 and published UNLOAD2 NEXT_STEPS at2fe7a5f: append five remaining unloading targets to zero under the new5400/600/6600/6660s window. Preserve all task metadata, physics, nonclock settings and original gates.',
        created_utc=datetime.now(timezone.utc).isoformat())
    protocol.pop('preparation_basis',None)
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        status='explicitly_approved',scope='One saved1.00 to0 five-target unload, all prior task fields unchanged except appended targets, actualLAST views and descriptive original-zero scalar comparison, records, normalmain push/localGit different-path restoration under originalphysics/gates; noHP/tests/defaultHF changes.'))
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(sources),input_bindings=len(inputs),old_payload_reads=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
