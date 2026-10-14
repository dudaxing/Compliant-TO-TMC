"""Publish closed L-FWD1 records; science/media identities use the original producer seal and stat only."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

BASE = 'e23a34b6fac803bab4be6bd35e980807291326c3'
REL = 'lf_data_preparation/native_interface_001/lf_forward_001'
LABEL = 'lf_fine_forward'
MANIFEST = 'handoff/repository_manifest.json'
OLD_MANIFEST_SHA = '6d9485f14adf9ba0606fb5ceed21ebcd16096a2344a9920de6e5a37a6f929a92'
FRONTS = {'docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'}
FINAL_JSON = REL+'/author/final_execution_review.json'
FINAL_MD = REL+'/author/final_execution_review.md'
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
ORDINARY = {'.json','.py','.md','.toml','.log','.txt','.jsonl'}
SCIENCE = {'.npz','.csv','.png','.gif'}


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
        assert set(record) == {'sha256','bytes'} and isinstance(record['sha256'],str) and len(record['sha256']) == 64
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
        assert record['path'] == name and path.is_file() and path.stat().st_size == record['bytes']
        return dict(record)
    return dict(path=name,bytes=path.stat().st_size,sha256=sha(path))


def check_closed(root,entries,old,allowed,declared):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    proof_path,reply_path = stage/'author/source_publication_receipt.json',stage/'author/direct_human_reply.json'
    proof,reply,auth = read(proof_path),read(reply_path),read(stage/'author/authorization.json')
    assert protocol['card'] == proof['prepared_card'] == auth['card'] == reply['card'] == 'L-FWD1'
    assert protocol['schema_version'] == 'prepared-native-lf-forward-card-1.0'
    assert proof['prepared'] is protocol['prepared'] is True
    assert proof['authorized'] is proof['executed'] is protocol['authorized'] is protocol['executed'] is protocol['installed'] is False
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['previous_delivery_commit'] == protocol['source_baseline_commit']
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['authorized_execution_source_commit'] == reply['authorized_execution_source_commit'] == BASE
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip() and reply['reply_context']
    assert auth['human_evidence_sha256'] == sha(reply_path) and auth['source_publication_receipt_sha256'] == sha(proof_path)
    assert sha(stage/'protocol.json') == proof['protocol_sha256'] == auth['protocol_sha256']
    phase = protocol['phases']['production']
    assert (protocol['controller_seconds'],protocol['view_seconds'],phase['helper_seconds'],phase['outer_seconds'],protocol['sampled_RSS_bytes']) == (18000,600,19000,19060,8*1024**3)
    assert (auth['helper_seconds'],auth['outer_seconds'],auth['sampled_RSS_bytes']) == (19000,19060,8*1024**3)
    assert 'install_sources' not in protocol and protocol['expected_default_changes'] == protocol['expected_HP_calls'] == protocol['expected_tests'] == 0
    assert protocol['zero_start'] is True and protocol['saved_parent_or_state_used'] is protocol['extend_path'] is False
    assert len(protocol['targets_mm']) == 25 and all(value is False for value in protocol['qualification'].values())
    inherited = protocol['inherited_NPZ_bindings']
    assert len(inherited) == 1 and {name for name in protocol['bindings'] if Path(name).suffix.lower()=='.npz'} == inherited.keys()
    for name,pin in protocol['bindings'].items():
        assert entries[name] == old[name] and old[name]['sha256'] == pin
        if name in inherited:
            record = inherited[name]
            assert record['sha256'] == pin and record['bytes'] == old[name]['bytes'] == path_in(root,name).stat().st_size
        else:
            assert sha(path_in(root,name)) == pin
    outer = read(stage/'production_launch.json')
    assert outer['completed_utc'] and outer['status'] in ('pass','not_pass') and outer['invocations'] == 1
    assert outer['card'] == 'L-FWD1' and outer['phase'] == 'production'
    assert outer['protocol_sha256'] == sha(stage/'protocol.json') and outer['bindings'] == protocol['bindings']
    output = stage/'run_001'
    production,view = path_in(root,protocol['candidate_directory']),path_in(root,protocol['view_directory'])
    assert production == output/LABEL and view == output/'view'
    helper = optional_json(output/'execution_receipt.json')
    terminal_helper = helper is not None and helper.get('status') in ('pass','not_pass') and helper.get('last_phase') == 'closure'
    assert declared_assets(root,output,helper if terminal_helper else None) == declared
    if outer['status'] == 'pass':
        assert terminal_helper and helper['status'] == 'pass'
        assert helper['authorized_execution_source_commit'] == BASE and helper['protocol_sha256'] == sha(stage/'protocol.json')
        assert isinstance(helper['accepted_states'],int) and helper['accepted_states'] >= 0
        assert all(helper[name] == 0 for name in ('HP_calls','JIT_calls','tests','candidate_copies','default_installations'))
        assert helper['zero_start'] is True and helper['saved_parent_or_state_used'] is helper['extend_path'] is False
        assert outer['exit_code'] == 0 and outer['stop_reason'] is None and outer['all_bindings_unchanged'] is True
        assert 0 <= outer['elapsed_seconds'] <= 19060 and 0 <= outer['helper_wall_seconds'] <= 19000
        assert outer['peak_sampled_tree_RSS_bytes'] <= 8*1024**3 and not (stage/'stop_requested.txt').exists()
        assert helper is not None and helper['status'] == 'pass' and 'exception' not in helper
        assert helper['output_identity_seal'] == 'complete_inside_original_helper_window' and helper['all_bindings_unchanged'] is True
        assert helper['elapsed_seconds'] <= 19000 and helper['peak_sampled_RSS_bytes'] <= 8*1024**3
        result,response = read(production/'result.json'),read(production/'response.json')
        N = result['accepted_states']
        assert N >= 25 and N == len(result['states']) == helper['accepted_states']
        assert result['status'] == response['status'] == 'success' and result['targets_mm'] == protocol['targets_mm']
        assert result['path_completed'] is result['unload_endpoint_reached'] is result['loading_peak_reached'] is result['task_target_executed'] is True
        assert result['target_origin'] == 0. and result['settings'] == protocol['settings'] and 'continuation' not in result
        originals = [row for row in result['states'] if row['is_original_target']]
        assert [row['original_target_index'] for row in originals] == list(range(25))
        assert [row['d'] for row in originals] == protocol['targets_mm']
        assert helper['cached_production_gates']['passed'] is True and helper['cached_production_gates']['actual_accepted_states'] == N
        assert all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
        assert all(helper['counts'][kind+suffix] == 1 for kind in ('api','model','solve','save','summary','view_child') for suffix in ('_started','_completed'))
        for kind in ('force','tangent'):
            assert helper['counts'][kind+'_started'] == result['call_counts'][kind+'_calls']
            assert helper['counts'][kind+'_completed'] == result['call_counts'][kind+'_calls_completed']
        assert result['call_counts']['HP_calls'] == result['call_counts']['JIT_calls'] == 0
        views,summary = read(view/'view.json'),read(view/LABEL/'summary.json')
        assert views['status'] == 'pass' and all(views[key] == N for key in ('geometry_started','geometry_completed','nodal_started','nodal_completed'))
        assert views['new_F_T_model_solver_HP_calls'] == 0 and views['mechanical_hooks_monitored'] is False
        assert views['contact_pressure_clamping_qualified'] is False and len(views['cases']) == 1
        assert views['cases'][0]['reference_available'] is False and views['cases'][0]['saved_accepted_states'] == N
        assert summary['production_status'] == 'success' and summary['reference_available'] is False and summary['accepted_states'] == len(summary['rows']) == N
        assert {name for name in declared if Path(name).suffix.lower()=='.png'} == {protocol['view_directory']+'/'+name for name in ('comparison.png','distances_forces.png','peak_fields.png')}
        assert {name for name in declared if Path(name).suffix.lower()=='.gif'} == {protocol['view_directory']+'/'+LABEL+'/actual_states.gif'}
        assert helper['actual_PNGs'] == 3 and helper['actual_GIF_frames'] == N
        terminal = helper['view_child_terminal']
        assert terminal['exit_code'] == 0 and terminal['stop_reason'] is None and terminal['elapsed_seconds'] <= terminal['limit_seconds'] <= 600
    closure = read(stage/'author/execution_documentation_receipt.json')
    assert closure['source_baseline_commit'] == BASE and closure['actual_execution_closed'] is True
    assert closure['actual_execution_status'] == outer['status'] and {row['path'] for row in closure['front_history']} == FRONTS and len(closure['front_history']) == 2
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
    return outer['status'],helper


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
    assert proof['published_commit'] == BASE and proof['manifest_sha256'] == sha256(oldraw).hexdigest() == OLD_MANIFEST_SHA
    assert len(old) == len(previous['files']) == proof['ordinary_manifest_files'] == 20171
    assert sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes'] == 10499418324 and previous['science_version'] == '0.5.0'
    actual = {path.relative_to(root).as_posix() for path in (root/REL).rglob('*') if path.is_file()}
    allowed = (actual-old.keys()) | FRONTS
    assert allowed & old.keys() == FRONTS
    assert all(Path(name).suffix.lower() in ORDINARY | SCIENCE for name in allowed)
    output = root/REL/'run_001'
    outer,helper = read(root/REL/'production_launch.json'),optional_json(output/'execution_receipt.json')
    assert outer['completed_utc'] and outer['status'] in ('pass','not_pass')
    terminal_helper = helper is not None and helper.get('status') in ('pass','not_pass') and helper.get('last_phase') == 'closure'
    try:
        declared = declared_assets(root,output,helper if terminal_helper else None)
        missing = {name for name in allowed if Path(name).suffix.lower() in SCIENCE}-declared.keys()
        assert not missing, 'Missing original producer scientific identities; no closed-window hash is permitted'
        assert declared.keys() == {name for name in allowed if Path(name).suffix.lower() in SCIENCE}
    except (AssertionError,KeyError,OSError) as exception:
        gap = dict(status='blocked_closed_producer_identity_gap_no_publication',source_baseline_commit=BASE,
            actual_execution_status=outer['status'],helper_status=(helper or {}).get('status'),
            output_identity_seal=(helper or {}).get('output_identity_seal'),reason=str(exception),
            actual_scientific_paths=sorted(name for name in allowed if Path(name).suffix.lower() in SCIENCE),
            partial_outputs_preserved=True,manifest_changed_by_this_invocation=False,scientific_late_reads_or_hashes=0)
        write_new(here/'publication_identity_gap.json',gap)
        print(json.dumps(gap,ensure_ascii=False))
        raise RuntimeError('Scientific identity gap recorded externally; preserve partials and stop before manifest write') from exception
    assert {FINAL_JSON,FINAL_MD} <= allowed
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
        status,helper = check_closed(root,entries,old,allowed,declared)
        manifest = dict(previous,created_utc=datetime.now(timezone.utc).isoformat(),previous_delivery_commit=BASE,
            storage_stage='LF_native_fine_forward_'+status+'_closed_001',files=[entries[name] for name in sorted(paths)])
        output_raw = (json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(output_raw)
        value = dict(status='incremental_execution_delivery_pass',previous_delivery_commit=BASE,
            manifest_sha256=sha256(output_raw).hexdigest(),ordinary_manifest_files=len(entries),ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta,delta_bytes=sum(row['bytes'] for row in delta),unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=sha(root/REL/'protocol.json'),executed_card='L-FWD1',authorized=True,executed=True,execution_closed=True,execution_status=status,
            actual_accepted_states=helper.get('accepted_states') if terminal_helper else None,
            helper_status=(helper or {}).get('status'),helper_snapshot_is_terminal=terminal_helper,
            output_identity_seal=(helper or {}).get('output_identity_seal'),
            immutable_input_bindings=len(read(root/REL/'protocol.json')['bindings']),old_scientific_input_stat_only=1,new_scientific_identities_from_closed_producer_stat_only=len(declared),
            scientific_or_media_bytes_headers_hash_decode_by_publisher=0,new_HF_API_HP_solver_tests_pixels_or_plots=0,
            new_default_files_installed=0,existing_default_changes=0,new_full_source_scan=False,new_independent_reference_qualified=False,whole_HF5_complete=False)
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
            assert check_closed(tree,entries,old,allowed,declared)[0] == source['execution_status']
        assert current['science_version'] == previous['science_version'] == '0.5.0' and current['science_baseline_commit'] == previous['science_baseline_commit']
        value = dict(source,status='published_and_incrementally_restored_pass',created_utc=datetime.now(timezone.utc).isoformat(),published_commit=commit,
            branch='main',origin=ORIGIN,source_and_restore_clean=True,remote_main_confirmed_equal=True,restore_root=str(restore),delta_files_restored=len(allowed),
            scientific_restore_check='stat plus original closed producer identity; no scientific rehash',new_full_source_or_restore_scan=False)
        value.pop('delta_files')
        write_new(here/'execution_publication_receipt.json',value)
    print(json.dumps({key:item for key,item in value.items() if key != 'delta_files'},ensure_ascii=False))


if __name__ == '__main__':
    main()
