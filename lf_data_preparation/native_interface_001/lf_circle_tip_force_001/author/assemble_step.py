"""Prepare the approved finite peak ordinary-input contract without executing candidates."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_force_001'
STAGE=ROOT/REL
BASE='58dd121f5026ecc2b8f0d8375479155dcb8f671c'

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def main():
    assert subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not STAGE.exists()
    inventory=json.loads((AUTHOR/'input_inventory.json').read_bytes())
    for name in ('execute_step.py','launch_step.py','force_views.py','close_step.py','publish_step.py',
                 'archive_publication.py','finalize_records.py','monitor_step.py','assemble_step.py','freeze_step.py'):
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(x.rstrip(b' \t')==x for x in raw.splitlines()),name
    (STAGE/'author').mkdir(parents=True)
    (AUTHOR/'execution_cwd').mkdir(exist_ok=True)
    for name in ('execute_step.py','launch_step.py','force_views.py'):
        (STAGE/name).write_bytes((AUTHOR/name).read_bytes())
    for name in ('assemble_step.py','freeze_step.py','input_inventory.json','input_schema.json'):
        (STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
    bindings={}
    viewer='lf_data_preparation/native_interface_001/lf_circle_tip_step_010/circle_saved_views.py'
    nodal='hf_repo/src/hf_eval/workpiece_nodal.py'
    for name in [REL+'/'+n for n in ('execute_step.py','launch_step.py','force_views.py')]+[
            'hf_repo/scripts/windows_owned_process_sup2.py',viewer,nodal]:
        bindings[name]=sha256((ROOT/name).read_bytes()).hexdigest()
    protocol=dict(inventory,schema_version='lf-circle-tip-force-protocol-1.0',
        output_directory=REL+'/run_001',working_directory=(AUTHOR/'execution_cwd').as_posix(),
        helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=1024**3,cpu_thread_limit=16,
        cpu_thread_environment=dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16'),
        source_bindings=bindings,
        fixed_coordinate_source_contract=dict(viewer_source=viewer,viewer_sha256=bindings[viewer],
            viewer_lines='480-482: both lift/fluctuation on all workpiece DOFs must be exactly zero before observations',
            nodal_source=nodal,nodal_sha256=bindings[nodal],
            nodal_semantics='All fixed body nodes, four mutually exclusive masks with physical/cut intersection separate; ON-body=-saved internal weak vectors; original holding total opposes total; positions copied from reference coordinates, therefore actual for this fixed body'),
        scope='Approved3 ordinary saved peak JSONs and1 existing GIF stat link; two new force PNGs; no scientific calls or qualification upgrades')
    write(STAGE/'protocol.json',protocol)
    pin=sha256((STAGE/'protocol.json').read_bytes()).hexdigest()
    write(STAGE/'author/authorization.json',dict(card='L-CTIPFORCE1',approval_card='L-CTIPFORCE1',authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,authorized_execution_source_commit=BASE,
        protocol_sha256=pin,direct_human_request='批准按 L-CTIPFORCE1 实施并执行',
        previously_published_plan='lf_data_preparation/native_interface_001/lf_circle_tip_path_001/NEXT_STEPS.md'))
    (STAGE/'L-CTIPFORCE1_CARD.md').write_bytes((AUTHOR/'L-CTIPFORCE1_CARD.md').read_bytes())
    print(json.dumps(dict(status='prepared_not_executed',protocol_sha256=pin,ordinary_JSONs=3,GIF_stat_links=1,new_PNGs=2)))

if __name__=='__main__':main()
