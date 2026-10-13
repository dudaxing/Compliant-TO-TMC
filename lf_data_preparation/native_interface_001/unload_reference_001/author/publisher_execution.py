"""Publish closed M-PREF1 records; scientific bytes use the original producer seal and stat only."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

BASE = 'ea5b55cc4f2ace87a78ed512d6bb14382e826a5d'
REL = 'lf_data_preparation/native_interface_001/unload_reference_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'}
FINAL_JSON = REL+'/author/final_execution_review.json'
FINAL_MD = REL+'/author/final_execution_review.md'
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
ORDINARY = {'.json','.py','.md','.toml','.log','.txt','.jsonl'}
SCIENCE = {'.npz','.gz','.png'}


def path_in(root,name):
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = (root/relative).resolve()
    path.relative_to(root)
    return path


def raw(path):
    assert path.suffix.lower() in ORDINARY, 'Ordinary bytes only; no scientific/media content or late hash'
    return path.read_bytes()


def sha(path):
    return sha256(raw(path)).hexdigest()


def read(path):
    assert path.suffix.lower() == '.json'
    return json.loads(raw(path))


def optional_json(path):
    if not path.exists():
        return None
    try:
        value = read(path)
    except (json.JSONDecodeError,UnicodeDecodeError):
        return None
    return value if isinstance(value,dict) else None


def git(root,*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=root)


def names(value):
    return {part.decode('utf-8') for part in value.split(b'\0') if part}


def write_new(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def declared_assets(root,output,helper):
    declared = {}
    for name,record in (helper or {}).get('outputs',{}).items():
        path = path_in(root,name)
        path.relative_to(output.resolve())
        assert path.suffix.lower() in ORDINARY | SCIENCE
        assert set(record) == {'sha256','bytes'} and len(record['sha256']) == 64
        assert path.is_file() and path.stat().st_size == record['bytes']
        if path.suffix.lower() in SCIENCE:
            declared[name] = dict(path=name,**record)
        else:
            assert sha(path) == record['sha256']
    return declared


def identity(root,name,declared):
    path = path_in(root,name)
    if path.suffix.lower() in SCIENCE:
        record = declared[name]
        assert record['path'] == name and path.stat().st_size == record['bytes']
        return dict(record)
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path))


def check_closed(root,entries,old,allowed,declared):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    proof_path,reply_path = stage/'author/source_publication_receipt.json',stage/'author/direct_human_reply.json'
    proof,reply,auth = read(proof_path),read(reply_path),read(stage/'author/authorization.json')
    assert protocol['card'] == proof['prepared_card'] == auth['card'] == reply['card'] == 'M-PREF1'
    assert protocol['schema_version'] == 'partial-saved-state-independent-reference-card-1.0'
    assert proof['prepared'] is protocol['prepared'] is True
    assert proof['authorized'] is proof['executed'] is protocol['authorized'] is protocol['executed'] is False
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['previous_delivery_commit'] == protocol['source_baseline_commit']
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['authorized_execution_source_commit'] == reply['authorized_execution_source_commit'] == BASE
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip() and reply['reply_context']
    assert auth['human_evidence_sha256'] == sha(reply_path) and auth['source_publication_receipt_sha256'] == sha(proof_path)
    assert sha(stage/'protocol.json') == proof['protocol_sha256'] == auth['protocol_sha256']
    phase = protocol['phases']['reference']
    assert (phase['helper_seconds'],phase['outer_seconds'],protocol['sampled_RSS_bytes']) == (900,960,8*1024**3)
    assert (auth['helper_seconds'],auth['outer_seconds'],auth['sampled_RSS_bytes']) == (900,960,8*1024**3)
    assert len(protocol['bindings']) == 55 and len(protocol['inherited_NPZ_bindings']) == 10
    for name,pin in protocol['bindings'].items():
        assert entries[name] == old[name] and old[name]['sha256'] == pin
        if name in protocol['inherited_NPZ_bindings']:
            record = protocol['inherited_NPZ_bindings'][name]
            assert record['sha256'] == pin and record['bytes'] == old[name]['bytes'] == path_in(root,name).stat().st_size
        else:
            assert sha(path_in(root,name)) == pin
    outer = read(stage/'reference_launch.json')
    assert outer['completed_utc'] and outer['status'] in ('pass','not_pass') and outer['invocations'] in (0,1)
    assert outer['authorized_execution_source_commit'] == BASE and outer['protocol_sha256'] == sha(stage/'protocol.json')
    output = path_in(root,protocol['reference_output'])
    assert output == stage/'run_001/reference'
    helper = optional_json(output/'execution_receipt.json')
    assert declared_assets(root,output,helper) == declared
    if outer['status'] == 'pass':
        assert outer['invocations'] == 1 and outer['exit_code'] == 0 and outer['stop_reason'] is None and outer['all_bindings_unchanged'] is True
        assert 0 <= outer['elapsed_seconds'] <= 960 and 0 <= outer['child_terminal_wall_seconds'] <= 900
        assert outer['peak_sampled_tree_RSS_bytes'] <= 8*1024**3 and not (stage/'stop_requested.txt').exists()
        assert helper is not None and helper['status'] == 'pass' and helper['error'] is None
        assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
        assert helper['protocol_sha256'] == sha(stage/'protocol.json') and helper['authorized_execution_source_commit'] == BASE
        assert helper['elapsed_seconds'] <= 900 and helper['sampled_peak_RSS_bytes'] <= 8*1024**3
        assert helper['selected_child_accepted_indices'] == [2,3] and helper['original_target_indices'] == [18,19]
        assert helper['HP_calls_started'] == helper['HP_calls_completed'] == 4
        assert helper['accepted_mechanical_states_completed'] == helper['workpiece_states_completed'] == 2
        assert helper['plot_started'] == helper['plot_completed'] == 1
        assert helper['production_F_T_solver_tests_API_calls'] == 0 and helper['full9_or_composed25_reference_qualified'] is False
        summary,lifecycle = read(output/'summary.json'),read(output/'lifecycle.json')
        assert summary['status'] == lifecycle['status'] == 'pass' and summary['accepted_states'] == 2
        assert summary['HP_calls_started'] == summary['HP_calls_completed'] == lifecycle['HP_calls_started'] == lifecycle['HP_calls_completed'] == 4
        assert summary['gates'] == protocol['gates'] and summary['selected_child_accepted_indices'] == [2,3]
        assert [(row['index'],row['child_accepted_index'],row['reference_execution_index'],row['original_target_index']) for row in summary['states']] == [(2,2,18,18),(3,3,19,19)]
        assert [row['target_mm'] for row in summary['states']] == [.9,.8] and [row['state_sha256'] for row in summary['states']] == protocol['selected_state_sha256']
        assert all(summary[key] is False for key in ('full_production_segment_reference_pass','full_composed_path_reference_pass','public_API_association_performed',
            'full_child_path_reference_pass','full_original_path_reference_pass','full_extended_path_reference_pass','HP_matrix_columns_exhaustively_checked',
            'contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified','plot_mechanical_hooks_monitored'))
        assert sum(Path(name).suffix.lower() == '.png' for name in declared) == 1
    closure = read(stage/'author/execution_documentation_receipt.json')
    assert closure['source_baseline_commit'] == BASE and closure['actual_execution_closed'] is True
    assert closure['actual_execution_status'] == outer['status'] and {row['path'] for row in closure['front_history']} == FRONTS
    for row in closure['front_history']:
        prior = git(root,'show',BASE+':'+row['path'])
        current = raw(root/row['path'])
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha256(current).hexdigest() == row['new_sha256'] == entries[row['path']]['sha256']
    review = read(root/FINAL_JSON)
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    assert review['authorized'] is review['executed'] is review['execution_closed'] is True and review['execution_status'] == outer['status']
    assert review['protocol_SHA256'] == sha(stage/'protocol.json') and review['declared_binary_identities'] == declared
    ordinary = {name for name in allowed if Path(name).suffix.lower() in ORDINARY}-{FINAL_JSON}
    assert FINAL_MD in ordinary and ordinary <= review['reviewed_repository_SHA256'].keys()
    assert FINAL_JSON not in review['reviewed_repository_SHA256']
    assert all(entries[name]['sha256'] == pin == sha(path_in(root,name)) for name,pin in review['reviewed_repository_SHA256'].items())
    return outer['status']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('finalize','verify'))
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--restore',type=Path,default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root,restore,here = args.repo.resolve(),args.restore.resolve(),Path(__file__).resolve().parent
    assert not here.is_relative_to(root), 'Run the external publisher; the formal copy is recovery evidence only'
    proof = read(root/REL/'author/source_publication_receipt.json')
    oldraw = git(root,'show',BASE+':'+MANIFEST)
    previous = json.loads(oldraw);old = {row['path']:row for row in previous['files']}
    assert proof['published_commit'] == BASE and proof['manifest_sha256'] == sha256(oldraw).hexdigest() == 'f2acf429784db5e5f85a8c763d40323311ebadcb1cfb5820951b53f9bac1d9a7'
    assert len(old) == len(previous['files']) == proof['ordinary_manifest_files'] == 19987
    assert sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes'] == 10330502684 and previous['science_version'] == '0.5.0'
    actual = {path.relative_to(root).as_posix() for path in (root/REL).rglob('*') if path.is_file()}
    allowed = (actual-old.keys()) | FRONTS
    assert allowed & old.keys() == FRONTS and {FINAL_JSON,FINAL_MD} <= allowed
    assert all(Path(name).suffix.lower() in ORDINARY | SCIENCE for name in allowed)
    protocol = read(root/REL/'protocol.json');output = path_in(root,protocol['reference_output'])
    helper = optional_json(output/'execution_receipt.json')
    declared = declared_assets(root,output,helper)
    assert declared.keys() == {name for name in allowed if Path(name).suffix.lower() in SCIENCE}, 'Missing producer scientific identities block publication; no late scientific hash is permitted'
    delta_file = here/'execution_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root,restore):
        assert git(tree,'branch','--show-current').decode().strip() == 'main'
        assert git(tree,'remote','get-url','origin').decode().strip() == git(tree,'remote','get-url','--push','origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root,'rev-parse','HEAD').decode().strip() == BASE and not delta_file.exists()
        assert raw(root/MANIFEST) == oldraw and not git(root,'diff','--name-only')
        assert not git(root,'ls-files','--others','--exclude-standard','-z')
        paths = names(git(root,'ls-files','-z'))-{MANIFEST}
        assert not old.keys()-paths
        assert names(git(root,'diff','--cached','--name-only','-z',BASE)) == allowed == (paths-old.keys()) | FRONTS
        delta = [identity(root,name,declared) for name in sorted(allowed)]
        entries = dict(old, **{row['path']:row for row in delta});assert entries.keys() == paths
        status = check_closed(root,entries,old,allowed,declared)
        manifest = dict(previous,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage='saved_unload_selected_reference_'+status+'_closed_001',files=[entries[name] for name in sorted(paths)])
        output_raw = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(output_raw)
        value = dict(status='incremental_execution_delivery_pass',previous_delivery_commit=BASE,
            manifest_sha256=sha256(output_raw).hexdigest(),ordinary_manifest_files=len(entries),ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta,delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=sha(root/REL/'protocol.json'),executed_card='M-PREF1',authorized=True,executed=True,execution_closed=True,execution_status=status,
            immutable_input_bindings=55,old_scientific_input_stat_only=10,new_scientific_identities_from_closed_producer_stat_only=len(declared),
            scientific_or_media_bytes_headers_hash_decode_by_publisher=0,new_HF_API_HP_solver_tests_pixels_or_plots=0,
            default_changes=0,new_full_source_scan=False,full9_or_composed25_reference_qualified=False,whole_HF5_complete=False)
        write_new(delta_file,value)
    else:
        source = read(delta_file)
        assert source['status'] == 'incremental_execution_delivery_pass' and source['previous_delivery_commit'] == BASE
        assert {row['path'] for row in source['delta_files']} == allowed
        commit = git(root,'rev-parse','HEAD').decode().strip()
        assert git(root,'rev-parse','HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root,'ls-remote','--heads','origin','main').decode().split() == [commit,'refs/heads/main']
        for tree in (root,restore):
            assert git(tree,'rev-parse','HEAD').decode().strip() == commit and not git(tree,'status','--porcelain')
        assert raw(root/MANIFEST) == raw(restore/MANIFEST) and sha(restore/MANIFEST) == source['manifest_sha256']
        current = read(restore/MANIFEST);entries = {row['path']:row for row in current['files']}
        assert len(entries) == len(current['files']) == source['ordinary_manifest_files']
        assert sum(row['bytes'] for row in entries.values()) == source['ordinary_manifest_bytes']
        assert names(git(root,'diff','--name-only','-z',BASE,commit)) == allowed | {MANIFEST}
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        for tree in (root,restore):
            assert names(git(tree,'ls-files','-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree,row['path'],declared) == row == entries[row['path']] for row in source['delta_files'])
            assert ({path.relative_to(tree).as_posix() for path in (tree/REL).rglob('*') if path.is_file()}-old.keys()) | FRONTS == allowed
            assert check_closed(tree,entries,old,allowed,declared) == source['execution_status']
        assert current['science_version'] == previous['science_version'] == '0.5.0' and current['science_baseline_commit'] == previous['science_baseline_commit']
        value = dict(source,status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),published_commit=commit,
            branch='main',origin=ORIGIN,source_and_restore_clean=True,remote_main_confirmed_equal=True,restore_root=str(restore),delta_files_restored=len(allowed),
            scientific_restore_check='stat plus original closed producer identity; no scientific rehash',new_full_source_or_restore_scan=False)
        value.pop('delta_files')
        write_new(here/'execution_publication_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key != 'delta_files'},ensure_ascii=False))


if __name__ == '__main__':
    main()
