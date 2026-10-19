"""Prepare one authorized circle saved-state reference, without reading payloads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_reference_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_reference_001'
PLOT='lf_data_preparation/native_interface_001/extension_reference_001/plot_reference_observation.py'
PROD='lf_data_preparation/native_interface_001/lf_circle_tip_step_010'
ORIGIN=PROD+'/run_001/wave_circle_tip_step10'
CPREP='lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001'
BASE='8cf86e81e414866a7d5cb110e006c7088f94eb97'
REQUEST='批准按 L-CTIPREF1 计划实施并执行'
GIT=['git','-c','gc.auto=0','-c','maintenance.auto=false']
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()


def write_new(name,value):
    with (AUTHOR/name).open('x',encoding='utf-8',newline='\n') as handle:
        if isinstance(value,str):handle.write(value)
        else:json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')


def main():
    assert subprocess.check_output(GIT+['rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(GIT+['status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not (ROOT/REL).exists()
    template=read(ROOT/OLD/'protocol.json')
    result=read(ROOT/ORIGIN/'result.json');model=read(ROOT/ORIGIN/'model/model.json')
    receipt=read(ROOT/PROD/'run_001/execution_receipt.json')
    task=read(ROOT/PROD/'step_task.json');row=result['states'][1]
    assert result['status']=='success' and receipt['status']=='pass'
    assert row['d']==1.06 and row['original_target_index']==12 and row['child_original_target_index']==1
    assert row['state_sha256']=='dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6'
    assert row['R_input']==0.19568183324206792
    assert model['task']==task and task['path']['kind']=='load_only'
    refs=template['reference_sources']
    assert len(refs)==len({Path(name).name for name in refs})==11
    for name,digest in refs.items():assert pin(ROOT/name)==digest
    plot=PLOT
    ordinary=[PROD+'/protocol.json',PROD+'/author/authorization.json',PROD+'/step_launch.json',
        PROD+'/run_001/execution_receipt.json',PROD+'/step_task.json',ORIGIN+'/result.json',ORIGIN+'/response.json',
        ORIGIN+'/model/model.json',ORIGIN+'/model/source_geometry/geometry.json',ORIGIN+'/'+row['descriptor_path'],
        CPREP+'/run_001/model/model.json',CPREP+'/run_001/execution_receipt.json']
    bindings={name:pin(ROOT/name) for name in ordinary}
    payload_names=[ORIGIN+'/model/model.npz']+[ORIGIN+'/'+row[key]['path'] for key in ('state','forces','tangents','matrix')]+[ORIGIN+'/model/source_geometry/geometry.npz']
    inherited=[]
    for name in payload_names:
        seal=receipt['outputs'][name]
        assert (ROOT/name).stat().st_size==seal['bytes']
        inherited.append(dict(path=name,**seal));bindings[name]=seal['sha256']
    bindings.update(refs)
    for name,digest in result['mechanics_source_sha256'].items():
        assert pin(ROOT/name)==digest;bindings[name]=digest
    bindings[plot]=pin(ROOT/plot)
    for name in ('execute_circle_reference.py','launch_reference.py'):
        ast.parse((AUTHOR/name).read_bytes());bindings[REL+'/'+name]=pin(AUTHOR/name)
    protocol=dict(schema_version='circle-saved-state-independent-reference-card-1.0',card='L-CTIPREF1',
        prepared=True,authorized=False,executed=False,source_baseline_commit=BASE,science_version='0.5.0',
        reference_sources=deepcopy(refs),bindings=bindings,
        production_stage=PROD+'/run_001',production_result_dir='wave_circle_tip_step10',
        production_launch_file=PROD+'/step_launch.json',production_protocol_file=PROD+'/protocol.json',
        production_targets_mm=[1.05,1.06],production_original_target_indices=[11,12],production_accepted_states=2,
        production_settings=deepcopy(result['settings']),producer_mechanics_source_sha256=deepcopy(result['mechanics_source_sha256']),
        task_file=PROD+'/step_task.json',task_sha256=result['task_sha256'],
        original_targets_mm=task['path']['targets_mm'],source_task_targets_mm=result['continuation']['source_task_targets_mm'],
        source_task_sha256=result['continuation']['source_task_sha256'],targets_mm=[1.06],original_target_indices=[12],
        execution_indices=[12],top_summary_child_indices=[1],selected_child_accepted_index=1,
        selected_state_sha256=row['state_sha256'],expected_accepted_states=1,expected_new_HP_calls=2,
        gates=deepcopy(template['gates']),grid=deepcopy(model['grid']),material=deepcopy(model['material']),
        workpiece=deepcopy(task['workpiece']),expected_counts=deepcopy(model['region_metadata']['counts']),
        direction=dict(deepcopy(template['direction']),length=model['region_metadata']['counts']['dofs']),reference_output=REL+'/run_001/reference',plot_source=plot,
        circle_preparation_model_file=CPREP+'/run_001/model/model.json',
        circle_preparation_receipt_file=CPREP+'/run_001/execution_receipt.json',
        phases=dict(reference=dict(helper_seconds=900,outer_seconds=960)),sampled_RSS_bytes=8*1024**3,
        cpu_thread_limit=16,cpu_thread_environment={name:'16' for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        old_scientific_inputs=inherited,old_payload_preparation_scope='Producer seal plus stat only; no header/array read before authorized execution window.',
        decoder_scope='Five unique decoded NPZ plus source geometry raw identity; workpiece_checks rereads selected state/forces. Fifty-one descriptor fields, eighteen repeated appearances, plus CSC format/shape and optional _is_array probe.',
        source_archive_scope='Eleven unchanged dependencies with distinct basenames, plus this driver and unchanged pure plot; all original mathematics and denominators retained.',
        qualification_scope='Selected saved circular model numerical reference and one PORT direction only; no independent geometric mask, full child/path/all columns/stress-energy/pressure/effective grip/release/stability/HF5 qualification.',
        stop_policy='One invocation, first terminal error stops; actual partial retained with original-window seal only. No repair rerun/retry/extension/force or new production F/T/equilibrium/tests/API association/install.',
        plot_scope='One unchanged pure plot after reference gates pass, reading new ordinary summary only; one new PNG pixel inspection after terminal success, no redraw.',
        created_utc=datetime.now(timezone.utc).isoformat())
    write_new('protocol.proposed.json',protocol)
    write_new('authorization.json',dict(card='L-CTIPREF1',authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,direct_human_request=REQUEST,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_baseline_commit=BASE,helper_seconds=900,outer_seconds=960,sampled_RSS_bytes=8*1024**3,
        cpu_thread_limit=16,cpu_thread_environment=protocol['cpu_thread_environment'],
        scope='Direct human approval of LOCAL3 published next plan: current c80/right92 circle1.06 peak HP80/120, original conditions and fifteen gates, error visualization, records and ordinary main publication/local Git restore.',
        recorded_utc=datetime.now(timezone.utc).isoformat()))
    assert (AUTHOR/'L-CTIPREF1_CARD.md').is_file()
    write_new('preparation_receipt.json',dict(card='L-CTIPREF1',status='prepared_authorized_not_executed',source_baseline_commit=BASE,
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),bindings=len(bindings),reference_sources=len(refs),
        old_payloads_opened=0,old_inputs=inherited,HP_calls=0,production_calls=0,default_source_changes=0,
        external_files={name:dict(bytes=(AUTHOR/name).stat().st_size,sha256=pin(AUTHOR/name)) for name in ('execute_circle_reference.py','launch_reference.py','protocol.proposed.json','L-CTIPREF1_CARD.md','authorization.json')},
        created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status='prepared_authorized_not_executed',bindings=len(bindings),reference_sources=len(refs),protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
