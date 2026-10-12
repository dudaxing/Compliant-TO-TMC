"""Deliver only a closed M-EXTEND2 metadata delta; inherit saved binary identities."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = '781f408cce5704817ebb67f2defcafc047af3820'
REL = 'lf_data_preparation/native_interface_001/saved_extension_002'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
SCIENCE_BASE = 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
ORDINARY = {'.json', '.jsonl', '.py', '.md', '.log', '.toml', '.xml', '.txt', '.patch'}
DECLARED = {'.npz', '.npy', '.png', '.gif', '.zip', '.gz', '.csv'}
KINDS = ('focused_tests', 'api', 'defaults', 'model', 'reader', 'solve', 'force',
         'tangent', 'save', 'summary', 'view_child', 'runtime_archive', 'installation')
read = lambda path: json.loads(path.read_bytes())
git = lambda root, *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}


def sha(path):
    assert path.suffix.lower() in ORDINARY, 'Only ordinary records may be byte-read: '+str(path)
    return sha256(path.read_bytes()).hexdigest()


def identity(root, name, config):
    path = (root/name).resolve()
    path.relative_to(root)
    if path.suffix.lower() in DECLARED:
        declared = config['declared_output_identities'][name]
        assert declared['path'] == name and path.stat().st_size == declared['bytes']
        assert len(declared['sha256']) == 64
        return dict(declared)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def read_helper(path):
    if not path.exists():
        return None, 'missing'
    try:
        value = read(path)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, 'malformed_preserved_as_ordinary_bytes'
    return (value, 'valid_json') if isinstance(value, dict) else (None, 'non_object_json')


def check_execution(root, entries, old, config):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    proof_file = stage/'author/M_EXTEND2_source_publication_receipt.json'
    proof = read(proof_file)
    auth_file, reply_file = stage/'author/authorization.json', stage/'author/direct_human_reply.json'
    auth, reply = read(auth_file), read(reply_file)
    assert protocol['card'] == auth['card'] == reply['card'] == proof['prepared_card'] == 'M-EXTEND2'
    assert protocol['prepared'] is proof['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is proof['authorized'] is proof['executed'] is False
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert config['source_commit'] == auth['approved_source_commit'] == reply['approved_source_commit'] == BASE
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'] and reply['reply_context']
    assert auth['human_evidence_sha256'] == sha(reply_file)
    assert auth['source_publication_receipt_sha256'] == sha(proof_file)
    assert config['protocol_sha256'] == auth['protocol_sha256'] == proof['protocol_sha256'] == sha(stage/'protocol.json')
    assert len(protocol['bindings']) == 148
    for name, pin in protocol['bindings'].items():
        assert entries[name] == old[name] and entries[name]['sha256'] == pin
        if name in protocol['inherited_byte_input_identities']:
            assert entries[name] == protocol['inherited_byte_input_identities'][name]
            assert (root/name).stat().st_size == entries[name]['bytes']
        else:
            assert sha(root/name) == pin
    launch_file, helper_file = stage/'production_launch.json', stage/'run_001/execution_receipt.json'
    launch = read(launch_file)
    helper, condition = read_helper(helper_file)
    assert launch['completed_utc'] and launch['invocations'] == 1 and launch['exit_code'] is not None
    assert launch['status'] == config['execution_status'] in ('pass', 'not_pass')
    assert config['execution_closed'] is True and sha(launch_file) == config['outer_sha256']
    assert condition == config['helper_condition']
    assert (sha(helper_file) if helper_file.exists() else None) == config['helper_sha256']
    assert launch['protocol_sha256'] == config['protocol_sha256']
    assert launch['outer_seconds'] == 3060 and launch['helper_seconds'] == 3000
    assert launch['sampled_RSS_limit_bytes'] == protocol['sampled_RSS_bytes'] == 8*1024**3
    assert launch['all_bindings_unchanged'] is True
    target_rows = {row['target']: row for row in protocol['installation']}
    assert len(target_rows) == 6 and set(config['actual_default_SHA256']) == set(target_rows)
    for target, row in target_rows.items():
        actual = sha(root/target)
        assert actual == entries[target]['sha256'] == launch['actual_default_SHA256'][target] == config['actual_default_SHA256'][target]
        assert old[target]['sha256'] == row['old_sha256']
        assert sha(root/row['candidate_source']) == row['new_sha256']
        if helper is not None and 'actual_default_SHA256' in helper:
            assert helper['actual_default_SHA256'][target] == actual
    if helper is not None and 'counts' in helper:
        assert set(helper['counts']) == {kind+suffix for kind in KINDS for suffix in ('_started', '_completed')}
        assert helper['counts'] == config['helper_counts']
    else:
        assert config['helper_counts'] is None
    declared = config['declared_output_identities']
    for name, row in declared.items():
        assert name.startswith(REL+'/run_001/') and Path(name).suffix.lower() in DECLARED
        assert helper is not None and helper.get('outputs', {}).get(name) == row['sha256']
        assert identity(root, name, config) == entries[name]
    if helper is not None:
        for name, pin in helper.get('outputs', {}).items():
            assert name.startswith(REL+'/run_001/') and entries[name]['sha256'] == pin
        if 'all_bindings_unchanged' in helper:
            assert helper['all_bindings_unchanged'] is True
    if config['execution_status'] == 'pass':
        assert helper is not None and helper['status'] == 'pass' and launch['exit_code'] == 0 and launch['stop_reason'] is None
        assert 0 <= launch['elapsed_seconds'] <= 3060 and 0 <= launch['helper_wall_seconds'] <= 3000
        assert launch['peak_sampled_tree_RSS_bytes'] <= 8*1024**3 and helper['peak_sampled_RSS_bytes'] <= 8*1024**3
        assert helper['installation_complete'] is launch['installation_complete'] is True
        assert all(config['actual_default_SHA256'][name] == row['new_sha256'] for name, row in target_rows.items())
        counts = helper['counts']
        assert all(counts[kind+suffix] == 1 for kind in ('focused_tests', 'api', 'model', 'reader', 'solve', 'save', 'summary', 'view_child', 'runtime_archive') for suffix in ('_started', '_completed'))
        assert counts['defaults_started'] == counts['defaults_completed'] == 2
        assert counts['installation_started'] == counts['installation_completed'] == 6
        assert helper['accepted_states'] >= 2 and helper['cached_production_gates']['passed'] is True
        assert helper['runtime_archive']['status'] == 'pass'
        assert helper['runtime_archive']['sha256'] == declared[REL+'/run_001/runtime_capsule.zip']['sha256']
        assert not (stage/'stop_requested.txt').exists()
    else:
        assert launch['exit_code'] != 0 or launch['stop_reason'] is not None or not launch['installation_complete'] or not launch['all_bindings_unchanged']
    assert {row['path'] for row in config['front_history']} == FRONTS
    for row in config['front_history']:
        prior = git(root, 'show', BASE+':'+row['path'])
        current = (root/row['path']).read_bytes()
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert entries[row['path']]['sha256'] == row['new_sha256']
    terminal = read(root/config['terminal_review_path'])
    assert terminal['status'].startswith('pass') and terminal['execution_status'] == config['execution_status'] and terminal['execution_closed'] is True
    final_name = config['final_review_path']
    review = read(root/final_name)
    assert review['status'].startswith('pass') and review['config_sha256'] == sha(stage/'author/execution_delivery_config.json')
    assert review['execution_status'] == config['execution_status'] and review['execution_closed'] is True
    ordinary_delta = {name for name in config['allowed_delta_paths'] if Path(name).suffix.lower() in ORDINARY}
    assert ordinary_delta-{final_name} <= review['reviewed_repository_SHA256'].keys()
    assert all(entries[name]['sha256'] == pin for name, pin in review['reviewed_repository_SHA256'].items())
    assert review['declared_binary_identities'] == declared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), Path(__file__).resolve().parent
    config = read(root/REL/'author/execution_delivery_config.json')
    assert config['schema_version'] == 'MEXTEND2-closed-incremental-delivery-config-1.0' and config['source_commit'] == BASE
    assert config['execution_status'] in ('pass', 'not_pass') and config['execution_closed'] is True
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']: row for row in previous['files']}
    proof = read(root/REL/'author/M_EXTEND2_source_publication_receipt.json')
    assert proof['published_commit'] == BASE and proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert len(old) == proof['ordinary_manifest_files'] and sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes']
    assert previous['science_version'] == '0.5.0' and previous['science_baseline_commit'] == SCIENCE_BASE
    protocol = read(root/REL/'protocol.json')
    targets = {row['target'] for row in protocol['installation']}
    changed_targets = {name for name in targets if config['actual_default_SHA256'][name] != old[name]['sha256']}
    allowed = set(config['allowed_delta_paths'])
    assert FRONTS <= allowed and allowed & old.keys() == FRONTS | changed_targets
    assert all(name in FRONTS | changed_targets or name.startswith(REL+'/') for name in allowed)
    assert all(Path(name).suffix.lower() in ORDINARY | DECLARED for name in allowed)
    assert set(config['declared_output_identities']) == {name for name in allowed if Path(name).suffix.lower() in DECLARED}
    delta_file = external/'execution_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root, restore):
        assert git(tree, 'branch', '--show-current').decode().strip() == 'main'
        assert git(tree, 'remote', 'get-url', 'origin').decode().strip() == git(tree, 'remote', 'get-url', '--push', 'origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE and not delta_file.exists()
        assert (root/MANIFEST).read_bytes() == oldraw and not git(root, 'diff', '--name-only')
        assert not git(root, 'ls-files', '--others', '--exclude-standard', '-z')
        paths = names(git(root, 'ls-files', '-z'))-{MANIFEST}
        assert not old.keys()-paths
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == (paths-old.keys()) | FRONTS | changed_targets
        delta = [identity(root, name, config) for name in sorted(allowed)]
        entries = dict(old, **{row['path']: row for row in delta})
        assert set(entries) == paths
        check_execution(root, entries, old, config)
        manifest = dict(previous, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
                        storage_stage='saved_explicit_short_path_extension_'+config['execution_status']+'_closed_002',
                        files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(raw)
        value = dict(status='incremental_execution_delivery_pass', previous_delivery_commit=BASE,
                     manifest_sha256=sha256(raw).hexdigest(), ordinary_manifest_files=len(entries),
                     ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()), delta_files=delta,
                     delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(old)-len(allowed & old.keys()),
                     protocol_sha256=config['protocol_sha256'], executed_card='M-EXTEND2', authorized=True, executed=True,
                     execution_status=config['execution_status'], execution_closed=True, default_changed_files=len(changed_targets),
                     bindings_inherited_from_closed_sole_run=148, binary_delta_declared_stat_only=len(config['declared_output_identities']),
                     binary_delta_rehashed=False, old_science_media_byte_reads=0, new_full_source_scan=False, new_HF_API_NPZ_HP_tests_plots=0)
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
            check_execution(tree, entries, old, config)
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        assert current['science_version'] == '0.5.0' and current['science_baseline_commit'] == SCIENCE_BASE
        value = dict(source, status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
                     published_commit=commit, branch='main', origin=ORIGIN, source_and_restore_clean=True,
                     remote_main_confirmed_equal=True, restore_root=str(restore), delta_files_restored=len(allowed),
                     ordinary_delta_hashed=len(allowed)-source['binary_delta_declared_stat_only'],
                     binary_delta_restore_checked='stat + producer receipt/declared identity; not binary rehash',
                     new_full_source_or_restore_scan=False, whole_HF5_complete=False)
        value.pop('delta_files')
        write_new(external/'execution_publication_receipt.json', value)
    print(json.dumps({key: item for key, item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
