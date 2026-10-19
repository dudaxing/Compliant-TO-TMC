"""Prepare a pending-approval extension using ordinary records and old seals only."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_step_003'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_step_002'
PARENT=OLD+'/run_001/wave_circle_tip_step2'
BASE='bdadd1ac846a96106cd022b2b80dd7e694cc79d2'
CARD='L-CTIPSTEP3'
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
    assert original['path']==dict(kind='load_only',targets_mm=[0.,.25,.5,.75,.9])
    assert parent['status']=='success' and parent['reached_displacement']==.9 and len(parent['states'])==2
    selected=parent['states'][1]
    assert selected['state_sha256']=='7dde449c7c36ed3963c2ee97616d706f08dff553426565b0c91007f4f4410ccf'
    assert selected['R_input']==.1580782308108174
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c80_domain92_Lr80_h05_alpha5em7_load095__L_CTIPSTEP3',
        purpose='tip_facing_circle_LF_saved_load_only_step',
        parameter_origin='Proposed L-CTIPSTEP3: retain complete [0,.25,.5,.75,.9] prefix and append .95 mm using terminal .90 mm state; pending explicit execution approval.',
        description='Proposed revalidation of .90 mm anchor and extension to .95 mm; same physics and gates, actual tip and right-medium observations, no earlier target replay.')
    task=deepcopy(original);task.update(metadata)
    task['path']['targets_mm'].append(.95);task['input']['target_mm']=.95
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
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_step3',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,geometry_file=geometry,
        original_task_file=OLD+'/step_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=[0.,.25,.5,.75,.9,.95],targets_mm=[.9,.95],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=2,
        source_anchor=dict(accepted_index=1,original_target_index=4,d_mm=.9,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        task_execution_scope='Proposed suffix [.9,.95] including fresh anchor F/T; full [0,.25,.5,.75,.9,.95] prefix inherited, never replayed.',
        direct_user_request=None,execution_authorization_status='pending_explicit_user_approval',
        preparation_basis='STEP2 published NEXT_STEPS plus active project goal; preparation only, no new scientific window.',
        created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=False,
        authorization_from_direct_human_request=False,one_invocation=True,direct_human_request=None,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        status='pending_explicit_user_approval',scope='Preparation only; no scientific execution, freeze, default installation, commit or push authorized by this record.'))
    print(json.dumps(dict(status='candidate_prepared_pending_approval',source_bindings=len(sources),input_bindings=len(inputs),old_payload_reads=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
