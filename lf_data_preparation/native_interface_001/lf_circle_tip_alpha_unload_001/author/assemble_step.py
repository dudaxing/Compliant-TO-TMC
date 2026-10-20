"""Prepare a pending first-unload candidate using ordinary metadata and NPZ stat only."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001'
PARENT=OLD+'/run_001/wave_circle_tip_alpha1'
TEMPLATE='lf_data_preparation/native_interface_001/lf_circle_tip_unload_001/protocol.json'
BASE='eecd5c6ddfcfe01da46a37d0d0b980068eb930ec'
CARD='L-CTIPAUNLOAD1'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists()
    assert not (AUTHOR/'protocol.proposed.json').exists()
    names=('execute_step.py','circle_saved_views.py','launch_step.py','plot_convergence.py')
    support=('close_step.py','publish_step.py','archive_publication.py','finalize_records.py','assemble_step.py','freeze_step.py','monitor_step.py')
    for name in names+support:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
    source=read(ROOT/OLD/'protocol.json')
    parent=read(ROOT/PARENT/'result.json')
    original=read(ROOT/OLD/'alpha_task.json')
    prefix=[0.,.25,.5,.75,.9,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06]
    assert original['path']==dict(kind='load_only',targets_mm=prefix)
    assert original['regularization']['alpha']==2.5e-7
    assert parent['status']=='success' and parent['reached_displacement']==1.06 and len(parent['states'])==13
    assert parent['task_target_executed'] is True and parent.get('continuation') is None
    selected=parent['states'][12]
    assert selected['original_target_index']==12 and selected['d']==1.06
    assert selected['state_sha256']=='e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68'
    assert selected['R_input']==.19522304147728387
    metadata={key:original[key] for key in ('task_id','purpose','parameter_origin','description')}
    task=deepcopy(original)
    task['path']['kind']='ordered_cycle';task['path']['targets_mm'].append(1.05)
    assert task['input']['target_mm']==1.06
    write(AUTHOR/'step_task.json',task)
    geometry=PARENT+'/model/source_geometry/geometry.json'
    payload=PARENT+'/model/source_geometry/geometry.npz'
    state=PARENT+'/accepted/012/state.npz'
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    old_inputs={name:dict(path=name,**seals[name]) for name in (payload,state)}
    assert old_inputs[payload]['sha256']==read(ROOT/geometry)['arrays']['sha256']
    assert old_inputs[state]['sha256']==selected['state']['sha256']
    for name,seal in old_inputs.items():assert (ROOT/name).stat().st_size==seal['bytes']
    same_input=OLD+'/run_001/view/wave_circle_tip_alpha1/summary.json'
    baseline=read(ROOT/same_input)['rows'][11]
    assert baseline['d_mm']==1.05 and baseline['leg']=='loading'
    assert baseline['state_sha256']==parent['states'][11]['state_sha256']
    ordinary=[same_input,PARENT+'/result.json',PARENT+'/model/model.json',geometry,
        PARENT+'/accepted/012/state.json',OLD+'/alpha_task.json',OLD+'/protocol.json']
    inputs={name:pin(ROOT/name) for name in ordinary}
    inputs.update({name:seal['sha256'] for name,seal in old_inputs.items()})
    inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    sources={name:pin(ROOT/name) for name in source['source_bindings'] if name.startswith('hf_repo/')}
    sources.update({REL+'/'+name:pin(AUTHOR/name) for name in names})
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{name}.py' for name in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=read(ROOT/TEMPLATE)
    protocol.update(card=CARD,source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_alpha_unload1',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=12,geometry_file=geometry,
        original_task_file=OLD+'/alpha_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=prefix+[1.05],targets_mm=[1.06,1.05],
        same_input_reference_summary_json=same_input,
        expected_task_transition=dict(source_path_kind='load_only',extended_path_kind='ordered_cycle',first_unload=True,loading_peak_mm=1.06,first_unload_target_mm=1.05),
        settings=source['settings']|{'time_limit_seconds':1800.},options=deepcopy(source['options']),gates=deepcopy(source['gates']),
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=2,
        source_anchor=dict(accepted_index=12,original_target_index=12,d_mm=1.06,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        task_execution_scope='Only first-unload suffix [1.06,1.05], fresh peak F/T revalidation, original 13-target prefix inherited without replay; input target remains1.06. Four task metadata copied exactly; only task.path kind and appended1.05 differ.',
        qualification_scope='One alpha2.5e-7 first-unload saved extension with actual observations; no full-prefix replay, newHP, complete unloading/release, pressure/effective grip, stability, alpha independence, mesh/domain-width convergence or HF5 qualification.',
        same_input_comparison_scope='13 original scalar values and descriptive differences only: ALPHA1 summary row11/global11 raw loading1.05 versus newglobal13 unloading1.05; preserve raw legs and SHA, no equality/recovery/monotonicity/hysteresis gate, no oldarray/media read.',
        direct_user_request=None,execution_authorization_status='awaiting_separate_explicit_approval',
        execution_authorization_basis='Preparation only. Closed AREF1 approval does not cover new equilibrium or resource window. This planned protocol requires a separate true one-invocation human authorization record before freeze or launch.',
        created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=False,
        authorization_from_direct_human_request=False,one_invocation=True,direct_human_request=None,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        status='awaiting_explicit_approval',scope='Proposed one first1.06 to1.05 saved unload, actualLAST views and descriptive same-input comparison, records, normalmain push and same-machine different-path localGit restoration under originalphysics/gates; noHP/tests/defaultHF changes.'))
    receipt=dict(status='prepared_pending_approval_not_executed',created_utc=datetime.now(timezone.utc).isoformat(),
        card=CARD,source_baseline_commit=BASE,source_bindings=len(sources),input_bindings=len(inputs),
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),task_sha256=pin(AUTHOR/'step_task.json'),
        old_payload_reads=0,old_payload_hash_reads=0,new_scientific_calls=0,tests_run=0,
        formal_stage_created=False,default_HF_changes=0,git_mutations=0,authorized=False)
    write(AUTHOR/'preparation_receipt.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':main()
