"""Assemble ordinary approved L-CPREP1 metadata; no HF/NPZ/media imports."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/lf_circle_input_preparation_001'
STAGE = ROOT/REL
BASE = 'd2cad344a3675cc1129c4786629f56e5678cb895'
REQUEST = '好的，按照你的建议开展 L-CPREP1，先完成 wave 夹持器圆形工件的输入准备与未变形兼容性检查，半径9 mm、圆心(71,40) mm，其余物理条件保持不变。注意做好记录和可视化，再根据检查结果安排后续计算。'
read = lambda p:json.loads(p.read_bytes())
pin = lambda p:sha256(p.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8',newline='\n')

def launcher():
    parent = ROOT/'lf_data_preparation/native_interface_001/lf_batch_input_preparation_001/launch_preparation.py'
    text = parent.read_text(encoding='utf-8').replace('L-BPREP1', 'L-CPREP1').replace('_L_BPREP1_', '_L_CPREP1_')
    text = text.replace("auth['authorization_from_direct_human_reply']", "auth['authorization_from_direct_human_request']")
    text = text.replace("assert auth['direct_human_answer'] == '批准按 L-CPREP1 卡实施并执行'",
                        "assert auth['direct_human_request'] == "+repr(REQUEST))
    text = text.replace("    assert len(protocol['candidate_installations']) == 3\n", '')
    ast.parse(text)
    (AUTHOR/'launch_preparation.py').write_text(text, encoding='utf-8',newline='\n')
    return dict(path=parent.relative_to(ROOT).as_posix(), sha256=pin(parent), adaptation='Card/request/instance label only; removed former default-installation count. Original 180/240 s, 1 GiB and SUP2 lifecycle retained.')

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not STAGE.exists()
    origin = launcher()
    for name in ('execute_preparation.py','plot_circle.py'):
        ast.parse((AUTHOR/name).read_bytes())
    gp = 'lf_data_preparation/native_interface_001/lf_batch_input_preparation_001/run_001/prepared/001/derived_geometry/geometry.json'
    tp = 'lf_data_preparation/native_interface_001/lf_batch_input_preparation_001/run_001/prepared/001/task.json'
    descriptor = read(ROOT/gp)
    array = (Path(gp).parent/descriptor['arrays']['path']).as_posix()
    inherited = read(ROOT/'lf_data_preparation/native_interface_001/lf_batch_input_preparation_001/run_001/execution_receipt.json')['outputs'][array]
    assert inherited['sha256']==descriptor['arrays']['sha256']
    assert (ROOT/array).stat().st_size==inherited['bytes']
    modules = ['__init__','boundary_geometry','data','displacement','evaluation','linear','native_map',
               'native_project','plotting','project','project_evaluation','regions','tmc','tmc_kernel']
    sources = {f'hf_repo/src/hf_eval/{name}.py':pin(ROOT/f'hf_repo/src/hf_eval/{name}.py') for name in modules}
    for name in ('hf_repo/pyproject.toml','hf_repo/scripts/windows_owned_process_sup2.py'):
        sources[name]=pin(ROOT/name)
    for name in ('execute_preparation.py','plot_circle.py','launch_preparation.py'):
        sources[REL+'/'+name]=pin(AUTHOR/name)
    cwd=AUTHOR/'execution_cwd'
    cwd.mkdir(exist_ok=False)
    protocol=dict(card='L-CPREP1',schema_version='lf-circle-input-preparation-card-1.0',source_baseline_commit=BASE,
        helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=1024**3,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',geometry_file=gp,parent_task_file=tp,
        task_metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_h05_alpha5em7_load05__L_CPREP1',
            purpose='fixed_circle_LF_input_and_undeformed_compatibility',
            parameter_origin='L-CPREP1 direct user request: fixed circle r9 mm at (71,40), wave geometry and remaining physics retained; short pilot targets are instructions only.',
            description='Native staircase fixed circular half-workpiece; preparation only, no load/force/tangent/equilibrium/reference evaluation.'),
        workpiece=dict(kind='fixed_rigid',shape='circle',center_mm=[71.,40.],radius_mm=9.,fixed_components=[0,1]),
        targets_mm=[0.,.25,.5],plot_source=REL+'/plot_circle.py',
        input_bindings={gp:pin(ROOT/gp),tp:pin(ROOT/tp),array:inherited['sha256']},source_bindings=sources,
        old_scientific_input=dict(path=array,bytes=inherited['bytes'],sha256=inherited['sha256'],
            scope='Only one old NPZ, reused prepared wave geometry; inherited producer SHA plus stat at assembly, payload reads only inside the authorized helper.'),
        source_binding_scope='Conservative static relative-import closure plus study/launcher/SUP2. Not a claim that every bound module is imported; __init__.evaluate import is lazy.',
        authorized_default_installations=0,authorized_tests=0,authorized_new_F_T_HP_solver_calls=0,
        expected_model_builds=1,expected_model_writes=1,expected_PNGs=1,
        expected_elements=13440,expected_DOFs=27378,
        source_snapshot_scope='Original write_native_project stores byte-exact descriptor/NPZ snapshot; model operators are construction-only, no response.',
        stop_policy='One invocation; first error stops plot/later stages, retain actual partial; only an in-window partial seal. No retry, repair rerun, extension, force, rollback or deletion.',
        qualification_scope='Input/model/undeformed compatibility only; no equilibrium/contact/pressure/effective-grip/release/stability/HP/HF5 qualification.',
        launcher_origin=origin,approved_plan=dict(path='docs/L_BFWD1_NEXT_STEP_PLAN.md',sha256=pin(ROOT/'docs/L_BFWD1_NEXT_STEP_PLAN.md')),
        created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card='L-CPREP1',authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        approved_plan_commit=BASE,approved_plan_sha256=protocol['approved_plan']['sha256'],
        scope='Approved circle preparation/static model/one undeformed PNG and single pixel inspection, records/main publication/restoration; no loading solve.'))
    print(json.dumps(dict(status='proposed_sources_and_metadata_assembled_not_executed',source_bindings=len(sources),input_bindings=3,
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))

if __name__=='__main__':
    main()
