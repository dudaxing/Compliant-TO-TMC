"""Publish L-REF1 ordinary source preparation; inherit scientific/media identities."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import ast
import json
import subprocess

BASE = 'b5a59417fe58989922a6ba42993708917fecafe1'
REL = 'lf_data_preparation/native_interface_001/lf_reference_001'
PRODUCTION = 'lf_data_preparation/native_interface_001/lf_forward_001'
CORE_PIN = 'b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5'
BODY_PIN = 'aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
RUNTIME = {'execute_partial_reference.py', 'launch_reference.py', 'plot_partial_reference_observation.py'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
OLD_MANIFEST_SHA = '6543470760c73c6f18dfa7258822e57644da132dc85195743e8994ac9d6f7d86'
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
    assert proof['executed_card'] == 'L-FWD1' and proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    assert proof['authorized'] is proof['executed'] is True
    assert proof['manifest_sha256'] == sha256(oldraw).hexdigest() == OLD_MANIFEST_SHA
    assert len(old) == len(previous['files']) == proof['ordinary_manifest_files'] == 20423
    assert sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes'] == 11141402568
    assert previous['science_version'] == '0.5.0'
    return oldraw, previous, old


def check_protocol(root, protocol, old):
    """Only ordinary bytes; ten reference inputs inherit closed L-FWD1 identities/stat."""
    assert protocol['schema_version'] == 'partial-saved-state-independent-reference-card-1.0' and protocol['card'] == 'L-REF1'
    assert protocol['source_baseline_commit'] == BASE and protocol['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is False and protocol.get('installed',False) is False
    assert protocol.get('protocol_seed_only',False) is False and 'install_sources' not in protocol
    phase = protocol['phases']['reference']
    assert (phase['helper_seconds'],phase['outer_seconds'],protocol['sampled_RSS_bytes']) == (900,960,8*1024**3)
    assert phase['argv'][0] == REL+'/execute_partial_reference.py'
    assert protocol['reference_output'] == REL+'/run_001/reference'
    assert protocol['production_stage'] == PRODUCTION+'/run_001' and protocol['production_result_dir'] == 'lf_fine_forward'
    assert protocol['production_launch_file'] == PRODUCTION+'/production_launch.json'
    assert protocol['production_protocol_file'] == PRODUCTION+'/protocol.json'
    assert all(protocol[key] == [13,16] for key in ('selected_accepted_indices','original_target_indices','execution_indices','top_summary_source_accepted_indices'))
    assert protocol['targets_mm'] == [1.2,1.05]
    assert (protocol['expected_accepted_states'],protocol['expected_new_HP_calls'],protocol['production_accepted_states']) == (2,4,25)
    assert protocol['new_production_F_T_model_solver_tests'] == 0 and protocol['new_reference_observation_plots'] == 1
    assert protocol['postrun_new_PNG_pixel_QA_maximum'] == 1 and protocol['no_postrun_science_array_or_gzip_decode'] is True
    assert all(protocol[key] is False for key in ('full_production_path_reference_pass','full_original_path_reference_pass','pressure_clamp_release_stability_HF5_or_all_columns_qualified'))
    assert len(protocol['gates']) == 15 and protocol['scatter_precision'] == 3000 and protocol['scatter_Inexact_trap'] is True
    assert protocol['direction']['definition'] == 'actual b_in/max(abs(b_in)), fixed components zero'
    assert protocol['direction']['length'] == 27378 and protocol['direction']['multiplier_direction'] == 0.
    inherited = protocol['inherited_NPZ_bindings']
    assert len(inherited) == 10 and {name for name in protocol['bindings'] if Path(name).suffix.lower()=='.npz'} == inherited.keys()
    helper_name = PRODUCTION+'/run_001/execution_receipt.json'
    assert sha(path_in(root,helper_name)) == old[helper_name]['sha256']
    helper = read(path_in(root,helper_name))
    assert helper['status'] == 'pass' and helper['last_phase'] == 'closure' and helper['output_identity_seal'] == 'complete_inside_original_helper_window'
    assert helper['accepted_states'] == 25
    for name,pin in protocol['bindings'].items():
        path = path_in(root,name)
        if name in inherited:
            entry = inherited[name]
            assert entry['sha256'] == helper['outputs'][name]['sha256'] == old[name]['sha256'] == pin
            assert path.is_file() and path.stat().st_size == entry['bytes'] == helper['outputs'][name]['bytes'] == old[name]['bytes']
        else:
            assert sha(path) == pin
            if name in old: assert old[name]['sha256'] == pin
    origin = root/protocol['production_stage']/protocol['production_result_dir']
    result,model = read(origin/'result.json'),read(origin/'model/model.json')
    assert result['status'] == 'success' and result['accepted_states'] == len(result['states']) == 25
    assert result['path_completed'] is result['task_target_executed'] is True and 'continuation' not in result
    assert result['targets_mm'] == protocol['original_targets_mm'] == protocol['production_targets_mm']
    assert result['settings'] == protocol['production_settings'] and result['counts'] == protocol['expected_counts']
    selected = [result['states'][i] for i in protocol['selected_accepted_indices']]
    assert [r['state_sha256'] for r in selected] == protocol['selected_state_sha256']
    assert [r['original_target_index'] for r in selected] == [13,16] and [r['d'] for r in selected] == [1.2,1.05]
    assert [r['leg'] for r in selected] == ['loading','unloading']
    assert model['task_sha256'] == result['task_sha256'] == protocol['task_sha256']
    assert model['grid'] == protocol['grid'] and model['material'] == protocol['material'] and model['task']['workpiece'] == protocol['workpiece']
    assert result['mechanics_source_sha256'] == protocol['producer_mechanics_source_sha256']
    assert model['source_geometry']['geometry_id'] == protocol['geometry_identity']['geometry_id']
    references = protocol['reference_sources']
    assert len(references) == 11 and len({Path(n).name for n in references}) == 11
    assert references['lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference_author/core_audit_mechanical.py'] == CORE_PIN
    assert references['hf_repo/scripts/audit_native_workpiece_cycle.py'] == BODY_PIN
    for name,pin in references.items():
        assert old[name]['sha256'] == pin == sha(path_in(root,name))
        assert sha(root/REL/'reference_sources'/Path(name).name) == pin
    tree = ast.parse(raw(root/REL/'reference_sources/core_audit_mechanical.py').decode('utf-8-sig'))
    gates = {item.arg:ast.literal_eval(item.value) for node in tree.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id == 'GATES' for target in node.targets) for item in node.value.keywords}
    assert protocol['gates'] == gates
    assert protocol['plot_source'] == REL+'/plot_partial_reference_observation.py'
    assert sha(path_in(root,protocol['plot_source'])) == protocol['plot_source_SHA256']


def identity(root, name):
    path = path_in(root,name)
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path))


def check_preparation(root, entries, old):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    check_protocol(root,protocol,old)
    assert not any((stage/name).exists() for name in ('run_001','reference_launch.json','reference_stdout.log','stop_requested.txt'))
    assert not any((stage/'author'/name).exists() for name in ('authorization.json','direct_human_reply.json','source_publication_receipt.json'))
    receipt = read(stage/'author/preparation_receipt.json')
    assert receipt['card'] == 'L-REF1' and receipt['source_baseline_commit'] == BASE
    assert receipt['prepared'] is True and receipt['authorized'] is receipt['executed'] is False and receipt.get('installed',False) is False
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
    assert RUNTIME | {'protocol.json','L-REF1_CARD.md','PREPARATION_RESULTS.md','author/final_source_review.md'} <= files
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
            storage_stage='native_lf_selected_reference_source_prepared_001',files=[entries[name] for name in sorted(paths)])
        output = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(output)
        value = dict(status='incremental_preparation_delivery_pass',previous_delivery_commit=BASE,
            manifest_sha256=sha256(output).hexdigest(),ordinary_manifest_files=len(entries),ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta,delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=sha(root/REL/'protocol.json'),prepared_card='L-REF1',prepared=True,authorized=False,executed=False,
            planned_default_evaluate_invocations=0,planned_pure_viewer_invocations=0,planned_HP_calls=4,planned_reference_states=2,planned_reference_observation_plots=1,
            planned_new_default_files=0,inherited_stat_only_NPZ=10,default_changes=0,new_full_source_scan=False,
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
