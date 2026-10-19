"""Assemble one directly approved extension; ordinary inputs and old seals only."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_step_006'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_step_005'
PARENT=OLD+'/run_001/wave_circle_tip_step5'
BASE='e88979f81ece32de01abc65afc6e1cf719f219c1'
CARD='L-CTIPSTEP6'
REQUEST='批准按L-CTIPSTEP6计划实施并执行'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists()
    names=('execute_step.py','circle_saved_views.py','launch_step.py','plot_convergence.py')
    for name in names:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
    source=read(ROOT/OLD/'protocol.json')
    parent=read(ROOT/PARENT/'result.json')
    original=read(ROOT/OLD/'step_task.json')
    prefix=[0.,.25,.5,.75,.9,.95,.98,1.00]
    assert original['path']==dict(kind='load_only',targets_mm=prefix)
    assert parent['status']=='success' and parent['reached_displacement']==1.00 and len(parent['states'])==2
    selected=parent['states'][1]
    assert selected['original_target_index']==7 and selected['d']==1.00
    assert selected['state_sha256']=='af69ca8598c4ca18fcf756b16e509696ea6a0f8dfbbad8429f804e402d682b95'
    assert selected['R_input']==.1784535445979535
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c80_domain92_Lr80_h05_alpha5em7_load102__L_CTIPSTEP6',
        purpose='tip_facing_circle_LF_saved_load_only_step',
        parameter_origin='L-CTIPSTEP6 explicit user approval: preserve complete [0,.25,.5,.75,.9,.95,.98,1.00] and append 1.02 mm from the terminal 1.00 mm accepted state; all other physics and original gates unchanged.',
        description='Revalidate 1.00 mm and extend to 1.02 mm using the installed public API, preserving the complete nested history; observe actual tip/right-medium/force/convergence response without replaying earlier targets.')
    task=deepcopy(original);task.update(metadata)
    task['path']['targets_mm'].append(1.02);task['input']['target_mm']=1.02
    write(AUTHOR/'step_task.json',task)
    geometry=PARENT+'/model/source_geometry/geometry.json'
    payload=PARENT+'/model/source_geometry/geometry.npz'
    state=PARENT+'/accepted/001/state.npz'
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    old_inputs={name:dict(path=name,**seals[name]) for name in (payload,state)}
    assert old_inputs[payload]['sha256']==read(ROOT/geometry)['arrays']['sha256']
    assert old_inputs[state]['sha256']==selected['state']['sha256']
    for name,seal in old_inputs.items():assert (ROOT/name).stat().st_size==seal['bytes']
    ordinary=[PARENT+'/result.json',PARENT+'/model/model.json',geometry,
        PARENT+'/accepted/001/state.json',OLD+'/step_task.json',OLD+'/protocol.json']
    inputs={name:pin(ROOT/name) for name in ordinary}
    inputs.update({name:seal['sha256'] for name,seal in old_inputs.items()})
    inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    sources={name:pin(ROOT/name) for name in source['source_bindings'] if name.startswith('hf_repo/')}
    sources.update({REL+'/'+name:pin(AUTHOR/name) for name in names})
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{name}.py' for name in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=deepcopy(source)
    protocol.update(card=CARD,source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_step6',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,geometry_file=geometry,
        original_task_file=OLD+'/step_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=prefix+[1.02],targets_mm=[1.00,1.02],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=2,
        source_anchor=dict(accepted_index=1,original_target_index=7,d_mm=1.00,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        task_execution_scope='Only suffix [1.00,1.02] including fresh anchor F/T; complete [0,.25,.5,.75,.9,.95,.98,1.00,1.02] prefix inherited, not replayed.',
        direct_user_request=REQUEST,execution_authorization_status='explicitly_approved',
        execution_authorization_basis='Explicit human answer approving the L-CTIPSTEP6 question and published STEP5 NEXT_STEPS plan at e88979f: one 1.00 to 1.02 mm extension under the stated scope and resource window; no previous window reused.',
        created_utc=datetime.now(timezone.utc).isoformat())
    protocol.pop('preparation_basis',None)
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        status='explicitly_approved',scope='One 1.00 to 1.02 saved extension, actual saved views, records, normal main push and local Git different-path restoration under the unchanged approved plan conditions.'))
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(sources),input_bindings=len(inputs),old_payload_reads=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
