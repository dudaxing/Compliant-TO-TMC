"""Prepare ordinary L-CEXT1 metadata; no HF imports or scientific payload reads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_extension_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_pilot_001'
PARENT=OLD+'/run_001/wave_circle_pilot'
BASE='09c3495c1a4dfc30ec58143ae192d851ac7d3283'
REQUEST='好的，按你的建议先补齐 load_only 保存态延伸功能并完成小模型兼容验证，再从圆形工件0.50 mm保存态推进到0.75 mm。保持半径9 mm、圆心(71,40) mm、其余物理条件和原验收门不变，注意做好记录，可视化实际变形、反力和收敛情况，再根据结果安排后续计算。'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not (ROOT/REL).exists()
    old=read(ROOT/OLD/'protocol.json'); parent=read(ROOT/PARENT/'result.json')
    model_name=PARENT+'/'+parent['model']['descriptor_path']; model=read(ROOT/model_name)
    original_task_file=OLD+'/pilot_task.json'
    assert model['task']==read(ROOT/original_task_file)
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_h05_alpha5em7_load075__L_CEXT1',
        purpose='fixed_circle_LF_explicit_load_only_extension',
        parameter_origin='L-CEXT1 direct request: preserve [0,.25,.5] source prefix and append explicit .75 mm peak from accepted .5 mm anchor.',
        description='Fixed circular half-workpiece; child revalidates .5 mm and advances to .75 mm. Complete source prefix is inherited, not freshly executed.')
    task=deepcopy(model['task']); task.update(metadata)
    task['path']['targets_mm'].append(.75); task['input']['target_mm']=.75
    write(AUTHOR/'extension_task.json',task)
    defaults={name:pin(ROOT/name) for name in old['source_bindings'] if name.startswith('hf_repo/')}
    transitions=[]
    for stem in ('native_resume','split_displacement','native_mean'):
        target=f'hf_repo/src/hf_eval/{stem}.py'; source=REL+'/candidate/'+target
        candidate=AUTHOR/'candidate'/target; ast.parse(candidate.read_bytes())
        transitions.append(dict(target=target,source=source,before_sha256=defaults[target],after_sha256=pin(candidate),bytes=candidate.stat().st_size))
        defaults[source]=pin(candidate)
    for name in ('execute_extension.py','launch_extension.py','circle_saved_views.py','plot_convergence.py','test_load_only_extension.py'):
        ast.parse((AUTHOR/name).read_bytes()); defaults[REL+'/'+name]=pin(AUTHOR/name)
    installed=deepcopy(defaults)
    for row in transitions: installed[row['target']]=row['after_sha256']
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{part}.py' for part in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    pure={name:installed[name] for name in pure_names}
    source_geometry=(Path(model_name).parent/model['source_geometry']['snapshot']['descriptor']).as_posix()
    geometry_payload=(Path(source_geometry).parent/read(ROOT/source_geometry)['arrays']['path']).as_posix()
    selected=parent['states'][2]
    state_descriptor=PARENT+'/'+selected['descriptor_path']; state_payload=PARENT+'/'+selected['state']['path']
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    inherited=[]
    for name in (geometry_payload,state_payload):
        seal=seals[name]; assert (ROOT/name).stat().st_size==seal['bytes']
        inherited.append(dict(path=name,**seal))
    inputs={name:pin(ROOT/name) for name in (PARENT+'/result.json',model_name,source_geometry,state_descriptor,original_task_file,OLD+'/protocol.json')}
    inputs.update({row['path']:row['sha256'] for row in inherited})
    inputs[REL+'/extension_task.json']=pin(AUTHOR/'extension_task.json')
    cwd=AUTHOR/'execution_cwd'; cwd.mkdir(exist_ok=True)
    protocol=dict(schema_version='lf-circle-load-only-extension-card-1.0',card='L-CEXT1',source_baseline_commit=BASE,
        tests_seconds=180,controller_seconds=1800,viewer_seconds=600,helper_seconds=3000,outer_seconds=3060,sampled_RSS_bytes=8*1024**3,
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_extension',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=2,original_task_file=original_task_file,task_file=REL+'/extension_task.json',task_metadata=metadata,
        complete_task_targets_mm=[0.,.25,.5,.75],targets_mm=[.5,.75],settings=old['settings'],options=old['options'],gates=old['gates'],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        test_source=REL+'/test_load_only_extension.py',expected_test_methods=8,
        test_scope='Five real 16-element/50-DOF solves, two linear controller paths and finite metadata rejections. Shared180s includes imports; failfast, cooperative boundaries, original owned Job overall supervision. No gripper test repeat or HP.',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,baseline_source_bindings=defaults,source_bindings=installed,pure_view_bindings=pure,candidate_installations=transitions,
        old_scientific_inputs=inherited,
        old_input_scope='Exactly two old NPZ identities inherited from parent producer seal plus preparation stat. Original reader decodes geometry and selected lift/fluctuation only; no old model/force/tangent/matrix/media payload.',
        installation_scope='Unique helper installs exactly three reviewed default Python sources before fresh test child. On first failure keep actual installation and partial output; no automatic rollback. All other default sources and mechanical numerical kernels unchanged.',
        source_binding_scope='Conservative default package closure plus candidates/tests/study/SUP2. Separate before/after maps bind exact three transitions; no universal import/read hook claim.',
        expected_PNGs=4,expected_GIFs=1,accepted_states_policy='Two requested child targets; actual N can grow through original internal bounded bisection. First .5 is revalidated anchor; old0/.25 are inherited, not new accepted states.',
        viewer_payload_scope='Pure five-source closure; one new model27fields plus each actual state/forces2+16 fields =1+2N unique NPZ and27+18N fields. No tangent decode; whole run seal includes all produced test/production/display artifacts.',
        new_HP_calls=0,default_installations=3,
        display_resource_scope='Shared600s covers new binding, one clean circle viewer, original convergence, exact table/page; final whole-run seal stays inside helper3000.',
        qualification_scope='Child .5/.75 segment only; new_peak_reached/extended_segment_completed explicit, full_original/full_extended/task_target_executed remain false; no full-prefix fresh execution, HP, pressure, effective clamp, release, stability or HF5 qualification.',
        stop_policy='One launch; first terminal error stops later install/tests/science/display as applicable, actual partial kept; in-window partial seal only. No retry, repair rerun, extension, force, rollback or delete. Original internal backtracking/bisection allowed.',
        pixel_inspection_scope='Four new PNGs each at most once after success; GIF frame count checked only by original viewer, no extra decode.',
        user_authorized_plan=dict(path=OLD+'/NEXT_STEPS.md',sha256=pin(ROOT/OLD/'NEXT_STEPS.md')),
        created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card='L-CEXT1',authorized=True,authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),scope='Direct authorization implements load-only extension, finite tests, one circle .5/.75 child, saved actual displays/convergence, records and normal main publication/restoration under recorded plan bounds.'))
    print(json.dumps(dict(status='ordinary_metadata_assembled_not_executed',sources=len(defaults),inputs=len(inputs),old_NPZ_payloads_opened=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))

if __name__=='__main__':main()
