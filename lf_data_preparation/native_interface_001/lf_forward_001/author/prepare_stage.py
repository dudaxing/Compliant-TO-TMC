"""Write ordinary L-FWD1 preparation; never import HF or read array/media bytes."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = '6e7d32fb52395938314a665c66993ba8d736a702'
REL = 'lf_data_preparation/native_interface_001/lf_forward_001'
CASE = 'lf_data_preparation/native_interface_001/lf_input_preparation_001/run_001/cases/gripper_native_fine'
PROFILE = 'lf_data_preparation/native_interface_001/saved_extension_004'
OLD_MANIFEST = '44503af319bdf336802276749542c584c775eac926cba7423e8fab1c5f0f30ba'
PRIOR_PROOF = Path('D:/hf-native-workpiece-api-author-20261014/LFBRIDGE_execution_publication_001/execution_publication_receipt.json')


def raw(path):
    assert path.suffix in {'.json', '.md', '.py', '.toml'}
    return path.read_bytes()


def digest(path):
    return sha256(raw(path)).hexdigest()


def read(path):
    return json.loads(raw(path))


def dump(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)


def main():
    stage = ROOT/REL
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert git('branch', '--show-current').decode().strip() == 'main'
    assert not git('status', '--porcelain') and not stage.exists()
    prior_manifest = raw(ROOT/'handoff/repository_manifest.json')
    assert sha256(prior_manifest).hexdigest() == OLD_MANIFEST
    previous, manifest = read(PRIOR_PROOF), json.loads(prior_manifest)
    old = {row['path']:row for row in manifest['files']}
    assert previous['published_commit'] == BASE and previous['manifest_sha256'] == OLD_MANIFEST
    assert previous['executed_card'] == 'L-PREP1' and previous['execution_closed'] is True and previous['execution_status'] == 'pass'
    assert len(old) == 20143 and sum(row['bytes'] for row in old.values()) == 10499224337
    author_names = [
        'forward_input_source_review.json', 'forward_input_source_review.md',
        'forward_physics_source_review.json', 'forward_physics_source_review.md',
        'resource_scope_review.json', 'resource_scope_review.md',
        'source_candidate_review.json', 'source_candidate_review.md',
        'publisher_source.py', 'publisher_source_review.json', 'publisher_source_review.md',
        'PUBLISHER_SOURCE_NOTES.md', 'publisher_source_author_receipt.json',
        'FORWARD_WRAPPER_SOURCE_NOTES.md', 'forward_wrapper_author_receipt.json',
        'source_author_receipt.json', 'SOURCE_AUTHOR_NOTES.md', 'prepare_stage.py', 'front_prefix.md',
    ]
    files = {name:name for name in ('execute_lf_forward.py', 'launch_lf_forward.py', 'L-FWD1_CARD.md', 'PREPARATION_RESULTS.md')}
    files.update({'author/'+name:name for name in author_names})
    source_author = read(HERE/'source_author_receipt.json')
    for relative, name in files.items():
        path = HERE/name
        assert path.is_file(), name
        if path.suffix == '.py': ast.parse(raw(path).decode('utf-8-sig'))
        if name in source_author['current_source_SHA256']:
            assert digest(path) == source_author['current_source_SHA256'][name]
    inputs = read(ROOT/CASE/'input_manifest.json')
    geometry_file, task_file = CASE+'/derived_geometry/geometry.json', CASE+'/task.json'
    geometry, task = read(ROOT/geometry_file), read(ROOT/task_file)
    profile = read(ROOT/PROFILE/'protocol.json')
    settings_source = PROFILE+'/run_001/unloaded_alpha_half/result.json'
    settings = dict(read(ROOT/settings_source)['settings'], time_limit_seconds=18000.0)
    assert inputs['status'] == 'success' and inputs['data_only'] is True
    assert digest(ROOT/geometry_file) == inputs['geometry']['descriptor_file_sha256']
    assert digest(ROOT/task_file) == inputs['bound_task_file_sha256']
    assert task['geometry'] == {'geometry_id':geometry['geometry_id'], 'descriptor_sha256':geometry['descriptor_sha256']}
    assert task['path']['targets_mm'] == [0,.25,.5,.65,.75,.8,.85,.9,.95,1,1.05,1.1,1.15,1.2,1.15,1.1,1.05,1,.9,.8,.75,.65,.5,.25,0]
    array = str(Path(geometry_file).with_name(geometry['arrays']['path'])).replace('\\','/')
    assert old[array]['sha256'] == geometry['arrays']['sha256'] == inputs['geometry']['arrays_sha256']
    assert (ROOT/array).is_file() and (ROOT/array).stat().st_size == old[array]['bytes']
    inherited = {array:dict(sha256=old[array]['sha256'],bytes=old[array]['bytes'],
        preparation_identity_basis='closed_L-PREP1_producer_and_published_manifest_plus_stat_only')}
    selected = {name for name in profile['bindings'] if name.startswith('hf_repo/') and Path(name).suffix in {'.py','.toml'}}
    selected.update(profile['pure_view_bindings'])
    selected.update({geometry_file,task_file,CASE+'/input_manifest.json',PROFILE+'/protocol.json',settings_source,
        'lf_data_preparation/native_interface_001/lf_input_preparation_001/run_001/execution_receipt.json'})
    bindings = {}
    for name in sorted(selected):
        pin = digest(ROOT/name)
        assert pin == old[name]['sha256']
        bindings[name] = pin
    bindings[array] = old[array]['sha256']
    stage.mkdir(parents=True)
    for relative,name in files.items():
        destination = stage/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as stream: stream.write(raw(HERE/name))
    with (stage/'author/previous_execution_publication_receipt.json').open('xb') as stream:
        stream.write(raw(PRIOR_PROOF))
    for name in ('execute_lf_forward.py','launch_lf_forward.py','L-FWD1_CARD.md','PREPARATION_RESULTS.md'):
        bindings[REL+'/'+name] = digest(stage/name)
    protocol = dict(schema_version='prepared-native-lf-forward-card-1.0',card='L-FWD1',
        source_baseline_commit=BASE,prepared=True,authorized=False,executed=False,installed=False,
        created_utc=datetime.now(timezone.utc).isoformat(),science_version='0.5.0',
        origin='https://github.com/dudaxing/Compliant-TO-TMC.git',
        geometry_file=geometry_file,task_file=task_file,input_manifest=CASE+'/input_manifest.json',
        geometry_id=geometry['geometry_id'],geometry_descriptor_sha256=geometry['descriptor_sha256'],
        geometry_file_sha256=bindings[geometry_file],task_sha256=inputs['bound_task_sha256'],task_file_sha256=bindings[task_file],
        settings_source_result=settings_source,gates_source_protocol=PROFILE+'/protocol.json',
        settings=settings,options=profile['options'],gates=profile['gates'],targets_mm=task['path']['targets_mm'],
        candidate_directory=REL+'/run_001/lf_fine_forward',view_directory=REL+'/run_001/view',
        pure_view_bindings=profile['pure_view_bindings'],viewer_source=profile['viewer_source'],
        controller_seconds=18000,view_seconds=600,sampled_RSS_bytes=8*1024**3,
        phases=dict(production=dict(helper_seconds=19000,outer_seconds=19060,
            argv=[REL+'/execute_lf_forward.py','--repo','.','--protocol',REL+'/protocol.json'])),
        bindings=bindings,inherited_NPZ_bindings=inherited,
        resource_mode='Earliest elapsed clocks; sampled process-tree RSS; cooperative stop and actual child wait, no OS hard cap or force',
        expected_API_calls=1,expected_original_targets=25,expected_model_constructions=1,
        zero_start=True,saved_parent_or_state_used=False,extend_path=False,
        production_input_NPZ_files=1,production_input_fields=4,field_reads_monitored=False,
        view_array_scope='Existing pure viewer: 1+2*N archives, 27+18*N observed fields, no saved tangents/matrix; N is actual accepted states',
        expected_HP_calls=0,expected_tests=0,expected_default_changes=0,expected_plots=3,
        plot_pixel_inspections_max=3,new_GIF_postrun_decode=0,
        first_terminal_error_stops=True,external_retries=0,repair_rerun_allowed=False,
        extension_allowed=False,force_allowed=False,automatic_rollback=False,
        scientific_reads_after_closed_window_allowed=False,source_preparation_scientific_bytes_headers_hashes_decode=0,
        qualification=dict(independent_reference_qualified=False,pressure_qualified=False,clamp_qualified=False,
            release_qualified=False,stability_qualified=False,HF5_qualified=False))
    dump(stage/'protocol.json',protocol)
    prefix, histories = raw(HERE/'front_prefix.md'), []
    for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
        path, prior = ROOT/name, git('show',BASE+':'+name)
        assert raw(path) == prior
        current = prefix+prior
        assert current.count(prior) == 1
        path.write_bytes(current)
        histories.append(dict(path=name,old_sha256=sha256(prior).hexdigest(),new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix),history_end_byte_exclusive=len(current),old_raw_contiguous_once=True))
    artifacts = {path.relative_to(ROOT).as_posix():digest(path) for path in sorted(stage.rglob('*')) if path.is_file()}
    receipt = dict(card='L-FWD1',status='source_prepared_not_executed',source_baseline_commit=BASE,
        prepared=True,authorized=False,executed=False,installed=False,artifact_SHA256=artifacts,front_history=histories,
        default_runtime_changes=0,scientific_or_media_byte_reads_hashes_headers_decode=0,
        new_HF_API_tests_plots_solver_force_tangent_HP=0,protocol_sha256=digest(stage/'protocol.json'))
    dump(stage/'author/preparation_receipt.json',receipt)
    dump(HERE/'preparation_write_receipt.json',dict(status='ordinary_stage_write_pass',stage=REL,
        protocol_sha256=receipt['protocol_sha256'],source_baseline_commit=BASE,new_stage_files=len(artifacts)+1,
        modified_fronts=2,scientific_bytes_read=False,runtime_executed=False))
    print(json.dumps(dict(status='source_prepared_not_executed',stage=REL,files=len(artifacts)+1,protocol_sha256=receipt['protocol_sha256'])))


if __name__ == '__main__':
    main()
