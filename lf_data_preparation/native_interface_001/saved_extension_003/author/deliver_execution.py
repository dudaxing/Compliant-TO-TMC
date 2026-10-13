"""Incrementally deliver closed M-UNLOAD1 records; never byte-read science assets."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = '3cf11e92bedb791855c7b01d314668eba1116ac6'
REL = 'lf_data_preparation/native_interface_001/saved_extension_003'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
ORDINARY = {'.json', '.jsonl', '.py', '.md', '.log', '.toml', '.xml', '.txt', '.patch'}
SCIENCE = {'.npz', '.npy', '.gz', '.png', '.gif', '.csv', '.zip'}
git = lambda root, *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}


def sha(path):
    assert path.suffix.lower() in ORDINARY, 'Ordinary bytes only: '+str(path)
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    assert path.suffix.lower() == '.json'
    return json.loads(path.read_bytes())


def optional_json(path):
    if not path.exists():
        return None
    try:
        value = read(path)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def declared_assets(root, run, helper):
    """Only true helper outputs SHA/size records plus stat; never open science bytes."""
    found = {}
    for name, declaration in (helper or {}).get('outputs', {}).items():
        if Path(name).suffix.lower() not in SCIENCE:
            continue
        path = (root/name).resolve()
        path.relative_to(run.resolve())
        assert path.relative_to(root).as_posix() == name
        assert isinstance(declaration, dict) and len(declaration['sha256']) == 64
        assert path.stat().st_size == declaration['bytes']
        found[name] = dict(path=name, bytes=declaration['bytes'], sha256=declaration['sha256'])
    return found


def identity(root, name, config):
    path = (root/name).resolve()
    path.relative_to(root)
    if path.suffix.lower() in SCIENCE:
        declared = config['declared_binary_identities'][name]
        assert declared['path'] == name and path.stat().st_size == declared['bytes']
        return dict(declared)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def check_closed(root, entries, old, config):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    proof_path, reply_path = stage/'author/source_publication_receipt.json', stage/'author/direct_human_reply.json'
    proof, reply, auth = read(proof_path), read(reply_path), read(stage/'author/authorization.json')
    assert protocol['card'] == proof['prepared_card'] == auth['card'] == reply['card'] == 'M-UNLOAD1'
    assert protocol['prepared'] is proof['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is proof['authorized'] is proof['executed'] is False
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['approved_source_commit'] == reply['approved_source_commit'] == config['source_commit'] == BASE
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'] and reply['reply_context']
    assert auth['human_evidence_sha256'] == sha(reply_path) and auth['source_publication_receipt_sha256'] == sha(proof_path)
    assert config['protocol_sha256'] == auth['protocol_sha256'] == proof['protocol_sha256'] == sha(stage/'protocol.json')
    assert len(protocol['bindings']) == 84
    for name, pin in protocol['bindings'].items():
        assert entries[name] == old[name] and old[name]['sha256'] == pin
        if name in protocol['inherited_NPZ_bindings']:
            assert (root/name).stat().st_size == old[name]['bytes']
        else:
            assert sha(root/name) == pin
    launch_path = stage/'production_launch.json'
    outer = read(launch_path)
    assert outer['completed_utc'] and outer['invocations'] == 1 and outer['exit_code'] is not None
    assert outer['status'] == config['execution_status'] in ('pass', 'not_pass')
    assert config['execution_closed'] is True and sha(launch_path) == config['outer_sha256']
    assert outer['all_bindings_unchanged'] in (True, None)
    run = stage/'run_001'
    helper_path = run/'execution_receipt.json'
    helper = optional_json(helper_path)
    assert (sha(helper_path) if helper_path.exists() else None) == config['helper_sha256']
    declared = declared_assets(root, run, helper)
    assert declared == config['declared_binary_identities']
    for name, row in declared.items():
        assert identity(root, name, config) == entries[name] == row
    production, view = root/protocol['candidate_directory'], root/protocol['view_directory']
    for key, path in [('result',production/'result.json'),('response',production/'response.json'),('view',view/'view.json')]:
        assert (sha(path) if path.exists() else None) == config[key+'_sha256']
    if config['execution_status'] == 'pass':
        assert outer['exit_code'] == 0 and outer['stop_reason'] is None and outer['all_bindings_unchanged'] is True
        assert 0 <= outer['elapsed_seconds'] <= 2760 and 0 <= outer['helper_wall_seconds'] <= 2700
        assert outer['peak_sampled_tree_RSS_bytes'] <= 8*1024**3
        assert helper is not None and helper['status'] == 'pass' and helper['all_bindings_unchanged'] is True
        assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
        assert helper['elapsed_seconds'] <= 2700 and helper['peak_sampled_RSS_bytes'] <= 8*1024**3
        counts = helper['counts']
        assert all(counts[kind+suffix] == 1 for kind in ('api','model','reader','solve','save','summary','view_child') for suffix in ('_started','_completed'))
        assert counts['defaults_started'] == counts['defaults_completed'] == 2
        assert all(helper[key] == 0 for key in ('HP_calls','JIT_calls','tests','candidate_copies','default_installations'))
        assert helper['cached_production_gates']['passed'] is True
        result, response, views = read(production/'result.json'), read(production/'response.json'), read(view/'view.json')
        N = result['accepted_states']
        assert N >= 2 and N == helper['accepted_states'] == len(result['states'])
        assert result['status'] == response['status'] == 'success' and result['path_completed'] is result['unload_endpoint_reached'] is True
        assert result['targets_mm'] == [1.1,1.05] and result['task_sha256'] == protocol['task_sha256']
        originals = [row for row in result['states'] if row['is_original_target']]
        assert [row['original_target_index'] for row in originals] == [15,16] and [row['d'] for row in originals] == [1.1,1.05]
        assert result['continuation']['parent_status'] == 'success' and result['continuation']['segment_completed'] is True
        assert result['continuation']['anchor_revalidated'] is result['continuation']['anchor_identity_preserved'] is True
        assert result['full_original_path_completed'] is result['full_extended_path_completed'] is result['task_target_executed'] is False
        assert response['path']['full_original_path_completed'] is response['path']['full_extended_path_completed'] is False
        assert all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
        assert response['independent_reference']['full_extended_path_reference_pass'] is False
        for kind in ('force','tangent'):
            assert counts[kind+'_started'] == result['call_counts'][kind+'_calls']
            assert counts[kind+'_completed'] == result['call_counts'][kind+'_calls_completed']
        assert views['status'] == 'pass' and all(views[key] == N for key in ('geometry_started','geometry_completed','nodal_started','nodal_completed'))
        assert views['new_F_T_model_solver_HP_calls'] == 0 and views['mechanical_hooks_monitored'] is False
        assert views['contact_pressure_clamping_qualified'] is False and len(views['cases']) == 1
        assert views['cases'][0]['reference_available'] is False and views['cases'][0]['saved_accepted_states'] == N
        assert helper['actual_PNGs'] == 3 and helper['actual_GIF_frames'] == N
    for row in config['front_history']:
        previous = git(root, 'show', BASE+':'+row['path'])
        current = (root/row['path']).read_bytes()
        assert sha256(previous).hexdigest() == row['old_sha256'] and current.count(previous) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == previous
        assert entries[row['path']]['sha256'] == row['new_sha256']
    assert {row['path'] for row in config['front_history']} == FRONTS
    review = read(root/config['final_review_path'])
    assert review['status'].startswith('pass') and review['config_sha256'] == sha(stage/'author/execution_delivery_config.json')
    assert review['execution_status'] == config['execution_status'] and review['execution_closed'] is True
    assert {name for name in config['allowed_delta_paths'] if Path(name).suffix.lower() in ORDINARY}-{config['final_review_path']} <= review['reviewed_repository_SHA256'].keys()
    assert all(entries[name]['sha256'] == pin for name, pin in review['reviewed_repository_SHA256'].items())
    assert review['declared_binary_identities'] == declared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root, restore, here = args.repo.resolve(), args.restore.resolve(), Path(__file__).resolve().parent
    assert not here.is_relative_to(root), 'Run the reviewed external tool; formal source copy is recovery evidence only'
    config = read(root/REL/'author/execution_delivery_config.json')
    assert config['source_commit'] == BASE and config['execution_closed'] is True
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']: row for row in previous['files']}
    proof = read(root/REL/'author/source_publication_receipt.json')
    assert proof['published_commit'] == BASE and proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert proof['ordinary_manifest_files'] == len(old) == 19712 and proof['ordinary_manifest_bytes'] == sum(row['bytes'] for row in old.values())
    assert previous['science_version'] == '0.5.0'
    allowed = set(config['allowed_delta_paths'])
    assert allowed & old.keys() == FRONTS and all(name in FRONTS or name.startswith(REL+'/') for name in allowed)
    assert all(Path(name).suffix.lower() in ORDINARY | SCIENCE for name in allowed)
    assert set(config['declared_binary_identities']) == {name for name in allowed if Path(name).suffix.lower() in SCIENCE}, 'Any unrecorded scientific asset blocks delivery; no extra byte-read is permitted'
    delta_file = here/'execution_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root, restore):
        assert git(tree, 'branch', '--show-current').decode().strip() == 'main'
        assert git(tree, 'remote', 'get-url', 'origin').decode().strip() == git(tree, 'remote', 'get-url', '--push', 'origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE and not delta_file.exists()
        assert (root/MANIFEST).read_bytes() == oldraw and not git(root, 'diff', '--name-only')
        assert not git(root, 'ls-files', '--others', '--exclude-standard', '-z')
        paths = names(git(root, 'ls-files', '-z'))-{MANIFEST}
        assert not old.keys()-paths
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == (paths-old.keys()) | FRONTS
        delta = [identity(root, name, config) for name in sorted(allowed)]
        entries = dict(old, **{row['path']: row for row in delta})
        assert set(entries) == paths
        check_closed(root, entries, old, config)
        manifest = dict(previous, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
                        storage_stage='saved_default_unload_'+config['execution_status']+'_closed_001',
                        files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(raw)
        value = dict(status='incremental_execution_delivery_pass', previous_delivery_commit=BASE,
                     manifest_sha256=sha256(raw).hexdigest(), ordinary_manifest_files=len(entries), ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
                     delta_files=delta, delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(old)-2,
                     protocol_sha256=config['protocol_sha256'], executed_card='M-UNLOAD1', authorized=True, executed=True,
                     execution_status=config['execution_status'], execution_closed=True, bindings_inherited_from_closed_sole_run=84,
                     declared_scientific_delta_stat_only=len(config['declared_binary_identities']), scientific_binary_rehashed=False,
                     old_science_binary_byte_reads=0, default_changes=0, new_segment_independent_reference=False, new_full_source_scan=False, new_HF_API_HP_tests_plots=0)
        write_new(delta_file, value)
    else:
        source = read(delta_file)
        commit = git(root, 'rev-parse', 'HEAD').decode().strip()
        assert git(root, 'rev-parse', 'HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root, 'ls-remote', '--heads', 'origin', 'main').decode().split() == [commit, 'refs/heads/main']
        for tree in (root, restore):
            assert git(tree, 'rev-parse', 'HEAD').decode().strip() == commit and not git(tree, 'status', '--porcelain')
        assert (root/MANIFEST).read_bytes() == (restore/MANIFEST).read_bytes() and sha(restore/MANIFEST) == source['manifest_sha256']
        current = read(restore/MANIFEST)
        entries = {row['path']: row for row in current['files']}
        assert {row['path'] for row in source['delta_files']} == allowed
        assert names(git(root, 'diff', '--name-only', '-z', BASE, commit)) == allowed | {MANIFEST}
        for tree in (root, restore):
            assert names(git(tree, 'ls-files', '-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree, row['path'], config) == row == entries[row['path']] for row in source['delta_files'])
            check_closed(tree, entries, old, config)
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        assert current['science_version'] == previous['science_version'] == '0.5.0' and current['science_baseline_commit'] == previous['science_baseline_commit']
        value = dict(source, status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
                     published_commit=commit, branch='main', origin=ORIGIN, source_and_restore_clean=True, remote_main_confirmed_equal=True,
                     restore_root=str(restore), delta_files_restored=len(allowed), scientific_restore_check='stat + true producer record identity; no binary rehash',
                     new_full_source_or_restore_scan=False, whole_HF5_complete=False, current_segment_new_HP_reference=False)
        value.pop('delta_files')
        write_new(here/'execution_publication_receipt.json', value)
    print(json.dumps({key: item for key, item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
