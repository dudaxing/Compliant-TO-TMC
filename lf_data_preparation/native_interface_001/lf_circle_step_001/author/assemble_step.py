"""Assemble ordinary saved-step metadata; no HF imports or scientific reads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_step_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_extension_001'
PARENT=OLD+'/run_001/wave_circle_extension'
BASE='ec0d958f81db06777457aeaadd0a29b971da8457'
REQUEST='好的，按你的建议复用已安装的 load_only 保存态延伸接口，从圆形工件0.75 mm保存态推进到1.00 mm。保持半径9 mm、圆心(71,40) mm、其余物理条件和原验收门不变，注意做好记录，可视化实际变形、反力和收敛情况，再根据结果安排后续计算。'
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
    original_task_file=OLD+'/extension_task.json'; assert model['task']==read(ROOT/original_task_file)
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_h05_alpha5em7_load100__L_CSTEP1',
        purpose='fixed_circle_LF_saved_load_only_step',
        parameter_origin='L-CSTEP1 direct request: preserve [0,.25,.5,.75] source prefix and append explicit1.00 mm peak from accepted .75 mm terminal anchor.',
        description='Fixed circular half-workpiece; child revalidates .75 mm and advances to1.00 mm. Complete prefix is inherited, not freshly executed.')
    task=deepcopy(model['task']);task.update(metadata)
    task['path']['targets_mm'].append(1.);task['input']['target_mm']=1.
    write(AUTHOR/'step_task.json',task)
    (AUTHOR/'circle_saved_views.py').write_bytes((ROOT/OLD/'circle_saved_views.py').read_bytes())
    plot=(ROOT/OLD/'plot_convergence.py').read_text(encoding='utf-8')
    before='axes[2].legend(fontsize=8, loc="best")'
    after='axes[2].legend(fontsize=8, loc="upper left", bbox_to_anchor=(0., 1.17), borderaxespad=0.)'
    assert plot.count(before)==1
    plot=plot.replace(before,after)
    plot=plot.replace('Only the case/title and explicit observer provenance metadata are generalized.',
        'Case/title, observer provenance and constraint-legend placement are generalized.')
    plot=plot.replace('Case/title and observer provenance only; original data and plotting algorithms retained',
        'Case/title, provenance and constraint legend placement only; original scalar projection, plot values and symlog retained')
    (AUTHOR/'plot_convergence.py').write_text(plot,encoding='utf-8',newline='\n')
    sources={name:pin(ROOT/name) for name in old['source_bindings'] if name.startswith('hf_repo/')}
    for name in ('execute_step.py','launch_step.py','circle_saved_views.py','plot_convergence.py'):
        ast.parse((AUTHOR/name).read_bytes());sources[REL+'/'+name]=pin(AUTHOR/name)
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{part}.py' for part in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    source_geometry=(Path(model_name).parent/model['source_geometry']['snapshot']['descriptor']).as_posix()
    geometry_payload=(Path(source_geometry).parent/read(ROOT/source_geometry)['arrays']['path']).as_posix()
    selected=parent['states'][1]
    assert selected['d']==.75 and selected['original_target_index']==3
    state_descriptor=PARENT+'/'+selected['descriptor_path'];state_payload=PARENT+'/'+selected['state']['path']
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    inherited=[]
    for name in (geometry_payload,state_payload):
        seal=seals[name];assert (ROOT/name).stat().st_size==seal['bytes'];inherited.append(dict(path=name,**seal))
    inputs={name:pin(ROOT/name) for name in (PARENT+'/result.json',model_name,source_geometry,state_descriptor,original_task_file,OLD+'/protocol.json')}
    inputs.update({row['path']:row['sha256'] for row in inherited})
    inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=True)
    p=dict(schema_version='lf-circle-saved-load-step-card-1.0',card='L-CSTEP1',source_baseline_commit=BASE,
        controller_seconds=1800,viewer_seconds=600,helper_seconds=2700,outer_seconds=2760,sampled_RSS_bytes=8*1024**3,
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_step',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,original_task_file=original_task_file,task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=[0.,.25,.5,.75,1.],targets_mm=[.75,1.],settings=old['settings'],options=old['options'],gates=old['gates'],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},old_scientific_inputs=inherited,
        old_input_scope='Exactly two old NPZ: parent source geometry and selected001 lift/fluctuation. Preparation inherits producer SHA+stat only; no model/force/tangent/matrix/media payload reading.',
        source_binding_scope='Installed default package plus study/SUP2 and pure view sources. No default changes, installations or repeated tests; not a universal import/read hook claim.',
        expected_PNGs=4,expected_GIFs=1,accepted_states_policy='Two requested child targets, actual N includes original bounded bisection accepts. .75 is freshly revalidated parent-terminal state; old prefix not re-executed.',
        viewer_payload_scope='Pure five sources; one new model27 fields and each new state/forces2+16 =1+2N unique NPZ,27+18N fields. No tangent payload decode; whole new-output seal includes all produced artifacts.',
        default_installations=0,new_tests=0,new_HP_calls=0,
        display_resource_scope='One shared600s for new binding, clean circle viewer, convergence, exact table/page. Final whole-output seal inside helper2700.',
        convergence_adaptation='Only constraint-panel legend moved outside data axes; raw scalar projection, plotted values, symlog, all other plot calls and scientific gates unchanged.',
        qualification_scope='Only .75/1.00 child segment; full/task_target execution and original producer qualification false. No new HP, full prefix/cycle, pressure/effective clamp, release, stability, manufacturing or HF5 qualification.',
        stop_policy='Unique launch; first terminal error stops later science/display, actual partial preserved, original-window partial seal only. No retry, repair rerun, extension, force, rollback or delete. Original internal backtracking/bisection permitted.',
        pixel_inspection_scope='Four new PNGs each at most once after success; GIF frame count from original viewer only, no extra decode.',
        approved_plan=dict(path=OLD+'/NEXT_STEPS.md',sha256=pin(ROOT/OLD/'NEXT_STEPS.md')),
        created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',p)
    write(AUTHOR/'authorization.proposed.json',dict(card='L-CSTEP1',authorized=True,authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),scope='User directly authorizes installed-interface .75/1.00 circle extension, saved actual views/convergence, four bounded pixel inspections, records and normal main publication/restoration within approved plan bounds.'))
    print(json.dumps(dict(status='ordinary_metadata_assembled_not_executed',sources=len(sources),inputs=len(inputs),old_payloads_opened=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))

if __name__=='__main__':main()
