"""Prepare the approved finite ordinary-input contract without executing candidates."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_path_001'
STAGE=ROOT/REL
BASE='0afa58b4e263bbad8ec5912b6bafb13a500e782a'

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def main():
    assert subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not STAGE.exists()
    inventory=json.loads((AUTHOR/'input_inventory.json').read_bytes())
    schema=json.loads((AUTHOR/'input_schema.json').read_bytes())
    fields=schema[0]['row_keys']
    assert all(x['row_keys']==fields and x['row_key_variants']==1 for x in schema)
    for name in ('execute_step.py','launch_step.py','path_views.py','close_step.py','publish_step.py',
                 'archive_publication.py','finalize_records.py','monitor_step.py','assemble_step.py','freeze_step.py'):
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(x.rstrip(b' \t')==x for x in raw.splitlines()),name
    (STAGE/'author').mkdir(parents=True)
    (AUTHOR/'execution_cwd').mkdir(exist_ok=True)
    for name in ('execute_step.py','launch_step.py','path_views.py'):
        (STAGE/name).write_bytes((AUTHOR/name).read_bytes())
    for name in ('assemble_step.py','freeze_step.py','input_inventory.json','input_schema.json'):
        (STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
    bindings={}
    for name in [REL+'/'+n for n in ('execute_step.py','launch_step.py','path_views.py')]+['hf_repo/scripts/windows_owned_process_sup2.py']:
        bindings[name]=sha256((ROOT/name).read_bytes()).hexdigest()
    protocol=dict(inventory,schema_version='lf-circle-tip-path-protocol-1.0',
        summary_row_fields=fields,output_directory=REL+'/run_001',working_directory=(AUTHOR/'execution_cwd').as_posix(),
        helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=1024**3,cpu_thread_limit=16,
        cpu_thread_environment=dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16'),
        source_bindings=bindings,scope='Approved29 ordinary JSON inputs and14 existing GIF stat links; two new scalar PNGs; no scientific calls or qualification upgrades')
    write(STAGE/'protocol.json',protocol)
    protocol_sha=sha256((STAGE/'protocol.json').read_bytes()).hexdigest()
    auth=dict(card='L-CTIPPATH1',approval_card='L-CTIPPATH1',authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,authorized_execution_source_commit=BASE,protocol_sha256=protocol_sha,
        direct_human_request='批准按 L-CTIPPATH1 计划实施并执行，汇总已有14段加载与卸载结果，做好同位移对照、记录和可视化，再根据结果安排后续工作。',
        previously_published_plan='lf_data_preparation/native_interface_001/lf_circle_tip_unload_003/NEXT_STEPS.md')
    write(STAGE/'author/authorization.json',auth)
    (STAGE/'L-CTIPPATH1_CARD.md').write_bytes((AUTHOR/'L-CTIPPATH1_CARD.md').read_bytes())
    print(json.dumps(dict(status='prepared_not_executed',protocol_sha256=protocol_sha,ordinary_JSONs=29,GIF_stat_links=14,new_PNGs=2)))

if __name__=='__main__':main()
