"""Prepare the approved new-alpha single-state reference without payload reads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_reference_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_reference_001'
PROD='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001'
ORIGIN=PROD+'/run_001/wave_circle_tip_alpha1'
CPREP='lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001'
BASE='9bed9811a34befdda01bd37a49796e89a5bd0255'
REQUEST='好的，按你的建议开展 L-CTIPAREF1，仅核对新α=2.5e−7、1.06 mm峰值保存态的HP80/120独立参考，保持原物理条件和15项验收门，注意做好记录和误差可视化，再根据结果安排后续工作。'
RUNTIME=('execute_circle_reference.py','launch_reference.py','plot_reference_observation.py')
GIT=['git','-c','gc.auto=0','-c','maintenance.auto=false']
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()


def write_new(name,value):
    with (AUTHOR/name).open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')


def main():
    assert subprocess.check_output(GIT+['rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(GIT+['status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not (ROOT/REL).exists()
    template=read(ROOT/OLD/'protocol.json')
    result=read(ROOT/ORIGIN/'result.json');model=read(ROOT/ORIGIN/'model/model.json')
    receipt=read(ROOT/PROD/'run_001/execution_receipt.json')
    task=read(ROOT/PROD/'alpha_task.json');row=result['states'][12]
    targets=[0.,.25,.5,.75,.9,.95,.98,1.,1.02,1.03,1.04,1.05,1.06]
    assert result['status']=='success' and receipt['status']=='pass'
    assert result['accepted_states']==len(result['states'])==13 and result['targets_mm']==targets
    assert result['scope']=='native_explicit_mean_displacement_path' and 'continuation' not in result
    assert receipt['zero_start'] is True and receipt['saved_parent_or_state_used'] is receipt['extend_path'] is False
    assert row['d']==1.06 and row['original_target_index']==12 and row['leg']=='loading'
    assert row['state_sha256']=='e71c06973b7dc7aff7e5ee4a801b595cb3f054e907cc6e1ad52188e858500a68'
    assert row['R_input']==0.19522304147728387
    assert model['task']==task and task['path']==dict(kind='load_only',targets_mm=targets)
    assert task['regularization']==dict(alpha=2.5e-7,length_mm=80.)
    prep=read(ROOT/CPREP/'run_001/model/model.json')
    expected_material=deepcopy(prep['material'])
    expected_material['alpha']/=2;expected_material['kr_MPa_mm2']/=2
    assert model['material']==expected_material
    assert model['material']['alpha']==2.5e-7 and model['material']['kr_MPa_mm2']==0.0021538461538461533
    refs=deepcopy(template['reference_sources'])
    assert len(refs)==len({Path(name).name for name in refs})==11
    for name,digest in refs.items():assert pin(ROOT/name)==digest
    ordinary=[PROD+'/protocol.json',PROD+'/author/authorization.json',PROD+'/step_launch.json',
        PROD+'/run_001/execution_receipt.json',PROD+'/alpha_task.json',ORIGIN+'/result.json',ORIGIN+'/response.json',
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
    for name in RUNTIME:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
        bindings[REL+'/'+name]=pin(AUTHOR/name)
    protocol=dict(schema_version='circle-saved-state-independent-reference-card-1.0',card='L-CTIPAREF1',
        prepared=True,authorized=False,executed=False,source_baseline_commit=BASE,science_version='0.5.0',
        reference_sources=refs,bindings=bindings,
        production_stage=PROD+'/run_001',production_result_dir='wave_circle_tip_alpha1',
        production_launch_file=PROD+'/step_launch.json',production_protocol_file=PROD+'/protocol.json',
        production_targets_mm=targets,production_original_target_indices=list(range(13)),production_accepted_states=13,
        production_settings=deepcopy(result['settings']),producer_mechanics_source_sha256=deepcopy(result['mechanics_source_sha256']),
        task_file=PROD+'/alpha_task.json',task_sha256=result['task_sha256'],original_targets_mm=targets,
        targets_mm=[1.06],original_target_indices=[12],execution_indices=[12],top_summary_child_indices=[12],
        selected_child_accepted_index=12,selected_state_sha256=row['state_sha256'],
        selected_index_semantics='Legacy child-named summary keys retain schema compatibility; here they mean actual accepted ordinal12 in the fresh zero-start producer, not a resumed child segment.',
        expected_accepted_states=1,expected_new_HP_calls=2,
        gates=deepcopy(template['gates']),grid=deepcopy(model['grid']),material=deepcopy(model['material']),
        workpiece=deepcopy(task['workpiece']),expected_counts=deepcopy(model['region_metadata']['counts']),
        direction=dict(deepcopy(template['direction']),length=model['region_metadata']['counts']['dofs']),
        reference_output=REL+'/run_001/reference',plot_source=REL+'/plot_reference_observation.py',
        plot_identity_adaptation='Copy original pure plot; only title and returned accepted index change to accepted12/new alpha. All error entries, normalization, gates, logarithms and layout unchanged.',
        circle_preparation_model_file=CPREP+'/run_001/model/model.json',
        circle_preparation_receipt_file=CPREP+'/run_001/execution_receipt.json',
        phases=dict(reference=dict(helper_seconds=900,outer_seconds=960)),sampled_RSS_bytes=8*1024**3,
        cpu_thread_limit=16,cpu_thread_environment=dict.fromkeys(('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16'),
        old_scientific_inputs=inherited,
        old_payload_preparation_scope='Original ALPHA1 helper producer seals plus stat only; no header/array read or payload hash before this unique reference window.',
        decoder_scope=template['decoder_scope'],source_archive_scope='Eleven unchanged reference dependencies with distinct basenames, this thin driver and the identity-adapted pure plot. All original mathematics and denominators retained.',
        qualification_scope='Only new-alpha saved accepted12/global12 numerical reference and one PORT direction; no independent geometric mask, full13-state/path/all-columns/stress-energy/pressure/effective-grip/release/stability/alpha-convergence/HF5 qualification.',
        stop_policy=template['stop_policy'],plot_scope='One identity-adapted pure plot after all original reference gates pass; reads new ordinary summary only. One new PNG pixel inspection after terminal success, no redraw; old media only linked.',
        created_utc=datetime.now(timezone.utc).isoformat())
    write_new('protocol.proposed.json',protocol)
    write_new('authorization.json',dict(card='L-CTIPAREF1',authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,direct_human_request=REQUEST,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_baseline_commit=BASE,helper_seconds=900,outer_seconds=960,sampled_RSS_bytes=8*1024**3,
        cpu_thread_limit=16,cpu_thread_environment=protocol['cpu_thread_environment'],
        scope='Direct approval of published ALPHA1 next plan: only new-alpha2.5e-7 saved1.06 peak, HP80/120 original fifteen gates, one error visualization, records, ordinary main publication and local Git restore.',
        recorded_utc=datetime.now(timezone.utc).isoformat()))
    assert (AUTHOR/'L-CTIPAREF1_CARD.md').is_file()
    names=RUNTIME+('protocol.proposed.json','L-CTIPAREF1_CARD.md','authorization.json')
    write_new('preparation_receipt.json',dict(card='L-CTIPAREF1',status='prepared_authorized_not_executed',source_baseline_commit=BASE,
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),bindings=len(bindings),reference_sources=len(refs),
        old_payloads_opened=0,old_inputs=inherited,HP_calls=0,production_calls=0,default_source_changes=0,
        external_files={name:dict(bytes=(AUTHOR/name).stat().st_size,sha256=pin(AUTHOR/name)) for name in names},
        created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status='prepared_authorized_not_executed',bindings=len(bindings),reference_sources=len(refs),
        old_scientific_inputs=len(inherited),protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
