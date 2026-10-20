"""Prepare the approved alpha experiment from ordinary metadata; no science run."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001'
STAGE=ROOT/REL
BASE='0687a138ca60ac09f6555b09132646e8a30bd5d7'
RUNTIME=('execute_step.py','launch_step.py','circle_saved_views.py','plot_convergence.py','compare_alpha.py')
SUPPORT=('assemble_step.py','freeze_step.py','close_step.py','monitor_step.py','publish_step.py',
         'archive_publication.py','finalize_records.py')

def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def main():
    git=['git','-c','gc.auto=0','-c','maintenance.auto=false']
    assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not STAGE.exists()
    inventory=json.loads((AUTHOR/'input_inventory.json').read_bytes())
    for name in RUNTIME+SUPPORT:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(x.rstrip(b' \t')==x for x in raw.splitlines()),name
    (STAGE/'author').mkdir(parents=True)
    (AUTHOR/'execution_cwd').mkdir(exist_ok=True)
    for name in RUNTIME+('alpha_task.json','L-CTIPALPHA1_CARD.md'):
        (STAGE/name).write_bytes((AUTHOR/name).read_bytes())
    for name in ('assemble_step.py','freeze_step.py','input_inventory.json'):
        (STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
    bindings={name:sha256((ROOT/name).read_bytes()).hexdigest()
        for name in inventory['source_binding_names']+[REL+'/'+n for n in RUNTIME]}
    pure_names=inventory['pure_view_binding_names']+[REL+'/circle_saved_views.py']
    protocol=dict(inventory,schema_version='lf-circle-tip-alpha-protocol-1.0',
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_alpha1',
        view_directory=REL+'/run_001/view',working_directory=(AUTHOR/'execution_cwd').as_posix(),
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        comparison_source=REL+'/compare_alpha.py',source_bindings=bindings,
        pure_view_bindings={name:bindings[name] for name in pure_names},
        controller_seconds=14400,viewer_seconds=900,helper_seconds=16200,outer_seconds=16260,
        sampled_RSS_bytes=64*1024**3,cpu_thread_limit=16,
        cpu_thread_environment=dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16'),
        scope='One fresh zero-start13-target alpha2.5e-7 loading experiment; original physical conditions and gates except alpha; six new PNGs and actualN GIF; no old-state resume, HP, tests, default HF edits or qualification transfer')
    write(STAGE/'protocol.json',protocol)
    pin=sha256((STAGE/'protocol.json').read_bytes()).hexdigest()
    write(STAGE/'author/authorization.json',dict(card='L-CTIPALPHA1',approval_card='L-CTIPALPHA1',authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,authorized_execution_source_commit=BASE,
        protocol_sha256=pin,direct_human_request='批准按 L-CTIPALPHA1 实施并执行',
        previously_published_plan='lf_data_preparation/native_interface_001/lf_circle_tip_force_001/NEXT_STEPS.md'))
    print(json.dumps(dict(status='prepared_not_executed',protocol_sha256=pin,requested_targets=13,
        baseline_rows=13,old_scientific_inputs=1,new_PNGs=6)))

if __name__=='__main__':main()
