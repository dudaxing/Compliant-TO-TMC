"""Publish L-FWD1 ordinary source preparation; inherit scientific/media identities."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

BASE = '6e7d32fb52395938314a665c66993ba8d736a702'
REL = 'lf_data_preparation/native_interface_001/lf_forward_001'
PREP = 'lf_data_preparation/native_interface_001/lf_input_preparation_001'
CASE = PREP+'/run_001/cases/gripper_native_fine'
INPUT_NPZ = CASE+'/derived_geometry/geometry.npz'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
RUNTIME = {'execute_lf_forward.py', 'launch_lf_forward.py'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
OLD_MANIFEST_SHA = '44503af319bdf336802276749542c584c775eac926cba7423e8fab1c5f0f30ba'
ORDINARY = {'.json', '.py', '.md', '.toml'}


def path_in(root, name):
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = (root/relative).resolve()
    path.relative_to(root)
    return path


def raw(path):
    assert path.suffix.lower() in ORDINARY, 'Ordinary files only; science/media bytes remain inherited'
    return path.read_bytes()


def sha(path):
    return sha256(raw(path)).hexdigest()


def read(path):
    assert path.suffix.lower() == '.json'
    return json.loads(raw(path))


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)


def names(value):
    return {part.decode('utf-8') for part in value.split(b'\0') if part}


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def old_manifest(root, proof):
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']:row for row in previous['files']}
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['executed_card'] == 'L-PREP1' and proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    assert proof['authorized'] is proof['executed'] is True
    assert proof['manifest_sha256'] == sha256(oldraw).hexdigest() == OLD_MANIFEST_SHA
    assert len(old) == len(previous['files']) == proof['ordinary_manifest_files'] == 20143
    assert sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes'] == 10499224337
    assert previous['science_version'] == '0.5.0'
    return oldraw, previous, old


def check_protocol(root, protocol, old):
    """Read ordinary bindings; the one prepared HF NPZ uses closed producer/manifest/stat."""
    assert protocol['schema_version'] == 'prepared-native-lf-forward-card-1.0' and protocol['card'] == 'L-FWD1'
    assert protocol['source_baseline_commit'] == BASE and protocol['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is protocol['installed'] is False
    assert 'install_sources' not in protocol
    phase = protocol['phases']['production']
    assert (protocol['controller_seconds'],protocol['view_seconds'],phase['helper_seconds'],phase['outer_seconds'],
        protocol['sampled_RSS_bytes']) == (18000,600,19000,19060,8*1024**3)
    assert phase['argv'] == [REL+'/execute_lf_forward.py','--repo','.', '--protocol',REL+'/protocol.json']
    assert protocol['candidate_directory'] == REL+'/run_001/lf_fine_forward'
    assert protocol['view_directory'] == REL+'/run_001/view'
    assert (protocol['geometry_file'],protocol['task_file'],protocol['input_manifest']) == (
        CASE+'/derived_geometry/geometry.json',CASE+'/task.json',CASE+'/input_manifest.json')
    inherited = protocol['inherited_NPZ_bindings']
    assert set(inherited) == {INPUT_NPZ} and inherited.keys() <= protocol['bindings'].keys()
    assert {name for name in protocol['bindings'] if Path(name).suffix.lower()=='.npz'} == inherited.keys()
    producer_name = PREP+'/run_001/execution_receipt.json'
    assert sha(path_in(root,producer_name)) == old[producer_name]['sha256']
    producer = read(path_in(root,producer_name))
    assert producer['card'] == 'L-PREP1' and producer['status'] == 'pass' and producer['execution_closed'] is True
    for name,pin in protocol['bindings'].items():
        path = path_in(root,name)
        if name in inherited:
            entry = inherited[name]
            assert entry['preparation_identity_basis'] == 'closed_L-PREP1_producer_and_published_manifest_plus_stat_only'
            assert old[name]['sha256'] == entry['sha256'] == producer['outputs'][name]['sha256'] == pin
            assert path.is_file() and path.stat().st_size == old[name]['bytes'] == entry['bytes'] == producer['outputs'][name]['bytes']
        else:
            assert sha(path) == pin
            if name in old:
                assert old[name]['sha256'] == pin
    required = {protocol[key] for key in ('geometry_file','task_file','input_manifest','settings_source_result',
        'gates_source_protocol','viewer_source')}
    assert required <= protocol['bindings'].keys()
    geometry,task,manifest = (read(path_in(root,protocol[key])) for key in ('geometry_file','task_file','input_manifest'))
    assert manifest['status'] == 'success' and manifest['data_only'] is True
    assert protocol['geometry_file_sha256'] == old[protocol['geometry_file']]['sha256'] == manifest['geometry']['descriptor_file_sha256']
    assert protocol['geometry_id'] == geometry['geometry_id'] == task['geometry']['geometry_id'] == manifest['geometry']['geometry_id']
    assert task['geometry']['descriptor_sha256'] == geometry['descriptor_sha256'] == manifest['geometry']['descriptor_sha256']
    assert protocol['geometry_descriptor_sha256'] == geometry['descriptor_sha256']
    assert protocol['task_file_sha256'] == protocol['bindings'][protocol['task_file']]
    assert protocol['task_sha256'] == manifest['bound_task_sha256']
    assert protocol['bindings'][protocol['task_file']] == manifest['bound_task_file_sha256']
    assert geometry['arrays']['sha256'] == protocol['bindings'][INPUT_NPZ] and geometry['arrays']['path'] == 'geometry.npz'
    assert task['path']['kind'] == 'ordered_cycle' and protocol['targets_mm'] == task['path']['targets_mm']
    assert protocol['targets_mm'] == [0.,.25,.5,.65,.75,.8,.85,.9,.95,1.,1.05,1.1,1.15,1.2,1.15,1.1,1.05,1.,.9,.8,.75,.65,.5,.25,0.]
    old_settings = read(path_in(root,protocol['settings_source_result']))['settings']
    assert protocol['settings']['time_limit_seconds'] == 18000.
    assert {key:value for key,value in protocol['settings'].items() if key != 'time_limit_seconds'} == {key:value for key,value in old_settings.items() if key != 'time_limit_seconds'}
    assert protocol['options'] == dict(response_mode='mechanical',tangent_mode='chunk256',initial_guess='port_projection')
    assert protocol['gates'] == read(path_in(root,protocol['gates_source_protocol']))['gates']
    assert protocol['pure_view_bindings'].keys() <= protocol['bindings'].keys()
    assert protocol['viewer_source'] in protocol['pure_view_bindings']
    assert all(protocol['bindings'][name] == pin for name,pin in protocol['pure_view_bindings'].items())
    assert protocol['zero_start'] is True and protocol['saved_parent_or_state_used'] is protocol['extend_path'] is False
    assert (protocol['expected_API_calls'],protocol['expected_model_constructions'],protocol['expected_original_targets'],
        protocol['production_input_NPZ_files'],protocol['production_input_fields'],protocol['expected_plots']) == (1,1,25,1,4,3)
    assert all(protocol[name] == 0 for name in ('expected_HP_calls','expected_tests','expected_default_changes','new_GIF_postrun_decode'))
    assert protocol['field_reads_monitored'] is False and protocol['plot_pixel_inspections_max'] == 3
    assert protocol['first_terminal_error_stops'] is True and protocol['external_retries'] == 0
    assert all(protocol[name] is False for name in ('repair_rerun_allowed','extension_allowed','force_allowed',
        'automatic_rollback','scientific_reads_after_closed_window_allowed'))
    assert all(value is False for value in protocol['qualification'].values())


def identity(root, name):
    path = path_in(root,name)
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path))


def check_preparation(root, entries, old):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    check_protocol(root,protocol,old)
    assert not any((stage/name).exists() for name in ('run_001','production_launch.json','production_stdout.log','stop_requested.txt'))
    assert not any((stage/'author'/name).exists() for name in ('authorization.json','direct_human_reply.json','source_publication_receipt.json'))
    receipt = read(stage/'author/preparation_receipt.json')
    assert receipt['card'] == 'L-FWD1' and receipt['source_baseline_commit'] == BASE
    assert receipt['prepared'] is True and receipt['authorized'] is receipt['executed'] is receipt['installed'] is False
    for name,pin in receipt['artifact_SHA256'].items():
        assert name.startswith(REL+'/') and entries[name]['sha256'] == pin == sha(path_in(root,name))
    assert REL+'/author/final_source_review.json' not in receipt['artifact_SHA256']
    assert {row['path'] for row in receipt['front_history']} == FRONTS and len(receipt['front_history']) == 2
    for row in receipt['front_history']:
        prior = git(root,'show',BASE+':'+row['path'])
        current = raw(root/row['path'])
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha256(current).hexdigest() == row['new_sha256'] == entries[row['path']]['sha256']
    review = read(stage/'author/final_source_review.json')
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    assert review['authorized'] is review['executed'] is False and review.get('installed',False) is False
    assert review['protocol_SHA256'] == sha(stage/'protocol.json')
    files = {path.relative_to(stage).as_posix() for path in stage.rglob('*') if path.is_file()}
    assert set(review['current_source_SHA256']) == files-{'author/final_source_review.json'}
    assert RUNTIME | {'protocol.json','L-FWD1_CARD.md','PREPARATION_RESULTS.md','author/final_source_review.md'} <= files
    assert all(sha(path_in(stage,name)) == pin for name,pin in review['current_source_SHA256'].items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('finalize','verify'))
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--restore',type=Path,default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root,restore,here = args.repo.resolve(),args.restore.resolve(),Path(__file__).resolve().parent
    assert not here.is_relative_to(root), 'Run the external publisher; the formal copy is recovery evidence only'
    proof = read(root/REL/'author/previous_execution_publication_receipt.json')
    oldraw,previous,old = old_manifest(root,proof)
    delta_file = here/'source_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root,restore):
        assert git(tree,'branch','--show-current').decode().strip() == 'main'
        assert git(tree,'remote','get-url','origin').decode().strip() == git(tree,'remote','get-url','--push','origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root,'rev-parse','HEAD').decode().strip() == BASE and not delta_file.exists()
        assert raw(root/MANIFEST) == oldraw and not git(root,'diff','--name-only')
        assert not git(root,'ls-files','--others','--exclude-standard','-z')
        stage = {path.relative_to(root).as_posix() for path in (root/REL).rglob('*') if path.is_file()}
        assert stage and not stage & old.keys()
        allowed = stage | FRONTS
        paths = names(git(root,'ls-files','-z'))-{MANIFEST}
        assert not old.keys()-paths
        assert names(git(root,'diff','--cached','--name-only','-z',BASE)) == allowed == (paths-old.keys()) | FRONTS
        delta = [identity(root,name) for name in sorted(allowed)]
        entries = dict(old, **{row['path']:row for row in delta})
        assert paths == entries.keys()
        check_preparation(root,entries,old)
        manifest = dict(previous,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage='native_lf_fine_forward_source_prepared_001',files=[entries[name] for name in sorted(paths)])
        output = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(output)
        value = dict(status='incremental_preparation_delivery_pass',previous_delivery_commit=BASE,
            manifest_sha256=sha256(output).hexdigest(),ordinary_manifest_files=len(entries),ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta,delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=sha(root/REL/'protocol.json'),prepared_card='L-FWD1',prepared=True,authorized=False,executed=False,
            planned_default_evaluate_invocations=1,planned_pure_viewer_invocations=1,planned_HP_calls=0,
            planned_new_default_files=0,inherited_stat_only_NPZ=1,default_changes=0,new_full_source_scan=False,
            scientific_or_media_byte_reads_hashes_headers_decode=0,new_HF_API_HP_solver_tests_pixels_or_plots=0,whole_HF5_complete=False)
        write_new(delta_file,value)
    else:
        source = read(delta_file)
        assert source['status'] == 'incremental_preparation_delivery_pass' and source['previous_delivery_commit'] == BASE
        commit = git(root,'rev-parse','HEAD').decode().strip()
        assert git(root,'rev-parse','HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root,'ls-remote','--heads','origin','main').decode().split() == [commit,'refs/heads/main']
        for tree in (root,restore):
            assert git(tree,'rev-parse','HEAD').decode().strip() == commit and not git(tree,'status','--porcelain')
        assert raw(root/MANIFEST) == raw(restore/MANIFEST) and sha(restore/MANIFEST) == source['manifest_sha256']
        current = read(restore/MANIFEST)
        entries = {row['path']:row for row in current['files']}
        allowed = {row['path'] for row in source['delta_files']}
        assert len(entries) == len(current['files']) == source['ordinary_manifest_files']
        assert sum(row['bytes'] for row in entries.values()) == source['ordinary_manifest_bytes']
        assert names(git(root,'diff','--name-only','-z',BASE,commit)) == allowed | {MANIFEST}
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        for tree in (root,restore):
            assert names(git(tree,'ls-files','-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree,row['path']) == row == entries[row['path']] for row in source['delta_files'])
            assert {path.relative_to(tree).as_posix() for path in (tree/REL).rglob('*') if path.is_file()} | FRONTS == allowed
            check_preparation(tree,entries,old)
        assert current['science_version'] == previous['science_version'] == '0.5.0' and current['science_baseline_commit'] == previous['science_baseline_commit']
        value = dict(source,status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),published_commit=commit,
            branch='main',origin=ORIGIN,source_and_restore_clean=True,remote_main_confirmed_equal=True,restore_root=str(restore),
            delta_files_restored_and_hashed=len(allowed),new_full_source_or_restore_scan=False)
        value.pop('delta_files')
        write_new(here/'source_publication_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key != 'delta_files'},ensure_ascii=False))


if __name__ == '__main__':
    main()
