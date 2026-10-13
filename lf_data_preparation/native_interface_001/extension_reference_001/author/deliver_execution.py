"""Incrementally deliver closed M-EREF1 records; never byte-read science assets."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = '8438c55f267246b91d6b320273ecb10665f3e16f'
REL = 'lf_data_preparation/native_interface_001/extension_reference_001'
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


def declared_assets(root, output, summaries):
    """Read only supplied ordinary producer records; collect real record/path SHA pairs."""
    output = output.resolve()
    output.relative_to(root)
    found = {}

    def add(relative, pin, source, member):
        relative = Path(relative)
        if relative.suffix.lower() not in SCIENCE:
            return
        assert not relative.is_absolute()
        path = (output/relative).resolve()
        path.relative_to(output)
        name = path.relative_to(root).as_posix()
        assert isinstance(pin, str) and len(pin) == 64
        row = dict(path=name, bytes=path.stat().st_size, sha256=pin)
        if name in found:
            assert found[name]['identity'] == row, 'Conflicting saved producer identities: '+name
        else:
            found[name] = dict(identity=row, producer_record=source, producer_member=member)

    def visit(value, source, member):
        if isinstance(value, dict):
            if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
                add(value['path'], value['sha256'], source, member)
            for key, item in value.items():
                visit(item, source, member+'/'+str(key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, source, member+'/'+str(index))

    for path in summaries:
        path.resolve().relative_to(output)
        value = read(path)
        source = path.relative_to(root).as_posix()
        visit(value, source, '')
        for relative, pin in value.get('observation_outputs', {}).items():
            add(relative, pin, source, '/observation_outputs/'+relative)
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
    assert protocol['card'] == proof['prepared_card'] == auth['card'] == reply['card'] == 'M-EREF1'
    assert protocol['prepared'] is proof['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is proof['authorized'] is proof['executed'] is False
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['approved_source_commit'] == reply['approved_source_commit'] == config['source_commit'] == BASE
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'] and reply['reply_context']
    assert auth['human_evidence_sha256'] == sha(reply_path) and auth['source_publication_receipt_sha256'] == sha(proof_path)
    assert config['protocol_sha256'] == auth['protocol_sha256'] == proof['protocol_sha256'] == sha(stage/'protocol.json')
    assert len(protocol['bindings']) == 50
    for name, pin in protocol['bindings'].items():
        assert entries[name] == old[name] and old[name]['sha256'] == pin
        if name in protocol['inherited_NPZ_bindings']:
            assert (root/name).stat().st_size == old[name]['bytes']
        else:
            assert sha(root/name) == pin
    launch_path = stage/'reference_launch.json'
    outer = read(launch_path)
    assert outer['completed_utc'] and outer['invocations'] == 1 and outer['exit_code'] is not None
    assert outer['status'] == config['execution_status'] in ('pass', 'not_pass')
    assert config['execution_closed'] is True and sha(launch_path) == config['outer_sha256']
    assert outer['all_bindings_unchanged'] is True
    output = root/protocol['reference_output']
    summary, helper = optional_json(output/'summary.json'), optional_json(output/'lifecycle.json')
    assert (sha(output/'summary.json') if (output/'summary.json').exists() else None) == config['summary_sha256']
    assert (sha(output/'lifecycle.json') if (output/'lifecycle.json').exists() else None) == config['lifecycle_sha256']
    records = [root/name for name in config['producer_summary_paths']]
    observed = declared_assets(root, output, records)
    declared = {name: row['identity'] for name, row in observed.items()}
    assert declared == config['declared_binary_identities']
    for name, row in declared.items():
        assert identity(root, name, config) == entries[name] == row
    if config['execution_status'] == 'pass':
        assert outer['exit_code'] == 0 and outer['stop_reason'] is None
        assert 0 <= outer['elapsed_seconds'] <= 960 and 0 <= outer['child_terminal_wall_seconds'] <= 900
        assert outer['peak_sampled_tree_RSS_bytes'] <= 8*1024**3
        assert summary is not None and helper is not None and summary['status'] == helper['status'] == 'pass'
        assert summary['accepted_states'] == helper['accepted_mechanical_states_completed'] == helper['workpiece_states_completed'] == 1
        assert summary['HP_calls_started'] == summary['HP_calls_completed'] == helper['HP_calls_started'] == helper['HP_calls_completed'] == 2
        assert summary['plot_started'] == summary['plot_completed'] == helper['plot_started'] == helper['plot_completed'] == 1
        assert summary['states'][0]['index'] == summary['states'][0]['child_accepted_index'] == 1
        assert summary['states'][0]['reference_execution_index'] == summary['states'][0]['original_target_index'] == 15
        assert summary['full_child_path_reference_pass'] is summary['full_original_path_reference_pass'] is summary['full_extended_path_reference_pass'] is False
        assert summary['pressure_qualified'] is summary['clamp_qualified'] is summary['HF5_qualified'] is False
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
    config = read(root/REL/'author/execution_delivery_config.json')
    assert config['source_commit'] == BASE and config['execution_closed'] is True
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']: row for row in previous['files']}
    proof = read(root/REL/'author/source_publication_receipt.json')
    assert proof['published_commit'] == BASE and proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert proof['ordinary_manifest_files'] == len(old) == 19641 and proof['ordinary_manifest_bytes'] == sum(row['bytes'] for row in old.values())
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
                        storage_stage='saved_extension_single_state_reference_'+config['execution_status']+'_closed_001',
                        files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        (root/MANIFEST).write_bytes(raw)
        value = dict(status='incremental_execution_delivery_pass', previous_delivery_commit=BASE,
                     manifest_sha256=sha256(raw).hexdigest(), ordinary_manifest_files=len(entries), ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
                     delta_files=delta, delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(old)-2,
                     protocol_sha256=config['protocol_sha256'], executed_card='M-EREF1', authorized=True, executed=True,
                     execution_status=config['execution_status'], execution_closed=True, bindings_inherited_from_closed_sole_run=50,
                     declared_scientific_delta_stat_only=len(config['declared_binary_identities']), scientific_binary_rehashed=False,
                     old_science_binary_byte_reads=0, default_changes=0, new_full_source_scan=False, new_HF_API_HP_tests_plots=0)
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
                     new_full_source_or_restore_scan=False, whole_HF5_complete=False)
        value.pop('delta_files')
        write_new(here/'execution_publication_receipt.json', value)
    print(json.dumps({key: item for key, item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
