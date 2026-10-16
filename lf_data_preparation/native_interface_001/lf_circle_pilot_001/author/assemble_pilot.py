"""Assemble ordinary pilot metadata without opening scientific payloads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_pilot_001'
PREP='lf_data_preparation/native_interface_001/lf_circle_input_preparation_001/run_001'
OLD='lf_data_preparation/native_interface_001/lf_batch_forward_001'
BASE='f4a681c8acbae9f91637b052f793109c45af3dcc'
REQUEST='好的，按照你的建议开展 L-CPILOT1，配套完成圆形保存态显示，从零执行 0→0.25→0.50 mm 试算。保持工件半径9 mm、圆心(71,40) mm、其余物理条件和原验收门不变，注意做好记录，可视化实际变形、反力和收敛情况，再根据结果安排后续计算。'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not (ROOT/REL).exists()
    source=ROOT/OLD/'launch_batch.py'
    text=source.read_text(encoding='utf-8').replace('L-BFWD1','L-CPILOT1').replace('_L_BFWD1_','_L_CPILOT1_')
    text=text.replace("auth['authorization_from_direct_human_reply']","auth['authorization_from_direct_human_request']")
    text=text.replace("assert auth['direct_human_answer'] == '批准按 L-CPILOT1 卡实施并执行'", "assert auth['direct_human_request'] == "+repr(REQUEST))
    text=text.replace('execute_batch.py','execute_pilot.py').replace('batch_launch.json','pilot_launch.json').replace('batch_stdout.log','pilot_stdout.log').replace('batch_instances.ndjson','pilot_instances.ndjson')
    text=text.replace('4500','2700').replace('4560','2760')
    text=text.replace('# The two old prepared geometry NPZ bindings belong only to the helper\'s', '# The one prepared geometry NPZ binding belongs only to the helper\'s')
    (AUTHOR/'launch_pilot.py').write_text(text,encoding='utf-8',newline='\n')
    (AUTHOR/'plot_convergence.py').write_bytes((ROOT/OLD/'example/plot_convergence.py').read_bytes())
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_h05_alpha5em7_load05__L_CPILOT1',
        purpose='fixed_circle_LF_zero_start_short_loading_pilot',
        parameter_origin='L-CPILOT1 direct user request: execute prepared L-CPREP1 wave circle [0,.25,.5] from zero; all physical and path values preserved.',
        description='Fixed circular half-workpiece, native staircase; independent 0/.25/.5 loading. No pressure/effective-grip qualification.')
    task=deepcopy(read(ROOT/PREP/'task.json')); task.update(metadata)
    write(AUTHOR/'pilot_task.json',task)
    original=read(ROOT/OLD/'protocol.json')
    geometry=PREP+'/model/source_geometry/geometry.json'
    payload=PREP+'/model/source_geometry/geometry.npz'
    inherited=read(ROOT/PREP/'execution_receipt.json')['outputs'][payload]
    assert (ROOT/payload).stat().st_size==inherited['bytes']
    assert inherited['sha256']==read(ROOT/geometry)['arrays']['sha256']
    sources={name:pin(ROOT/name) for name in original['source_bindings'] if name.startswith('hf_repo/src/hf_eval/') or name in ('hf_repo/pyproject.toml','hf_repo/scripts/windows_owned_process_sup2.py')}
    names=('execute_pilot.py','circle_saved_views.py','launch_pilot.py','plot_convergence.py')
    for name in names:
        ast.parse((AUTHOR/name).read_bytes())
        sources[REL+'/'+name]=pin(AUTHOR/name)
    pure={name:sources[name] for name in [REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{part}.py' for part in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]}
    cwd=AUTHOR/'execution_cwd'; cwd.mkdir(exist_ok=True)
    protocol=dict(schema_version='lf-circle-short-pilot-card-1.0',card='L-CPILOT1',source_baseline_commit=BASE,
        controller_seconds=1800,viewer_seconds=600,helper_seconds=2700,outer_seconds=2760,sampled_RSS_bytes=8*1024**3,
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_pilot',view_directory=REL+'/run_001/view',
        geometry_file=geometry,task_file=REL+'/pilot_task.json',original_task_file=PREP+'/task.json',task_metadata=metadata,
        targets_mm=[0.,.25,.5],settings=original['settings'],options=original['options'],gates=original['gates'],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings={geometry:pin(ROOT/geometry),payload:inherited['sha256'],PREP+'/task.json':pin(ROOT/PREP/'task.json'),REL+'/pilot_task.json':pin(AUTHOR/'pilot_task.json'),OLD+'/protocol.json':pin(ROOT/OLD/'protocol.json')},
        source_bindings=sources,pure_view_bindings=pure,
        old_scientific_input=dict(path=payload,**inherited,scope='Sole old NPZ. Producer SHA and stat only during preparation; payload identity/read only in unique helper window. Old model/state/media not read.'),
        source_binding_scope='Conservative default package closure plus study/SUP2. Not all modules imported. Pure view closure is exactly five source files, with lazy __init__.evaluate.',
        expected_PNGs=4,expected_GIFs=1,expected_requested_targets=3,accepted_states_policy='Actual N can grow through original bounded internal bisection; preserve chronology and every accepted state.',
        viewer_payload_scope='One new model NPZ with 27 fields; each actual new state/forces NPZ 2+16 fields. Unique 1+2N archives and 27+18N fields. No tangent payload decoding. Full output seal includes all produced artifacts.',
        default_installations=0,new_tests=0,new_HP_calls=0,
        display_resource_scope='One shared 600 s clock for binding, clean circle viewer, convergence, table and page; final whole-run seal remains inside helper2700, not a separate display-only seal.',
        stop_policy='Unique launch, first terminal error closes later science/display; only original-window partial seal allowed. No external retry, repair rerun, extension, force, rollback or delete. Original internal backtracking/bisection allowed.',
        qualification_scope='Only circle 0/.25/.5 load-only pilot. Unsigned Q1 distance and convex-cell overlap are observations; no set containment, physical pressure, effective grip, unloading, release, stability, full25, independent HP or HF5 qualification.',
        pixel_inspection_scope='Four new PNGs, each at most once. No extra GIF decode; original viewer checks actual frame count N.',
        launcher_origin=dict(path=source.relative_to(ROOT).as_posix(),sha256=pin(source),adaptation='Request/card/names and 2700/2760 limits only; SUP2 lifecycle unchanged.'),created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card='L-CPILOT1',authorized=True,authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),scope='Direct authorized implementation and one zero-start circle pilot, saved views/convergence, four bounded pixel inspections, records, normal main publication/restoration.'))
    print(json.dumps(dict(status='ordinary_candidate_assembled_not_executed',protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),sources=len(sources),old_payloads_opened=0)))

if __name__=='__main__': main()
