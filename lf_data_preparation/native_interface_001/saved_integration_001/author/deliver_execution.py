"""Incremental closed M-INTEGRATE1 delivery, installed sources and raw evidence."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = '2b550d09f4347240ef6cb626b4c829566b638e61'
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md', 'hf_repo/README.md', 'docs/NATIVE_EVALUATION_INTERFACE.md'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
read = lambda path: json.loads(path.read_bytes())
digest = lambda raw: sha256(raw).hexdigest()
git = lambda root, *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}


def sha(path):
    value = sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def identity(root, name):
    path = (root / name).resolve()
    path.relative_to(root)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def check_execution(root, config, entries):
    stage = root / REL
    protocol, outer = read(stage / 'protocol.json'), read(stage / 'integration_launch.json')
    helper, tests = read(stage / 'run_001/execution_receipt.json'), read(stage / 'run_001/focused_test_receipt.json')
    assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert sha(stage / 'protocol.json') == config['protocol_sha256']
    assert outer['status'] == helper['status'] == tests['status'] == 'pass'
    assert outer['invocations'] == 1 and outer['exit_code'] == 0 and outer['stop_reason'] is None
    assert outer['completed_utc'] and outer['immutable_bindings_unchanged'] is True
    assert helper['focused_tests_started'] == helper['focused_tests_completed'] == 1 and helper['installation_complete']
    assert helper['failure'] is None and helper['automatic_rollback'] is False
    assert helper['approved_source_commit'] == BASE and helper['test_receipt_sha256'] == sha(stage / 'run_001/focused_test_receipt.json')
    assert helper['elapsed_seconds'] <= 300 and outer['elapsed_seconds'] <= 360
    assert helper['focused_tests_terminal']['elapsed_seconds'] <= 180 and helper['focused_tests_terminal']['exit_code'] == 0
    assert outer['peak_sampled_tree_RSS_bytes'] <= protocol['sampled_RSS_bytes'] and tests['peak_sampled_RSS_bytes'] <= protocol['sampled_RSS_bytes']
    assert tests['collected_selectors'] == protocol['focused_test_selectors'] and tests['passed_calls'] == 25
    assert len(tests['reports']) == 75 and all(row['outcome'] == 'passed' for row in tests['reports'])
    assert len(helper['installed']) == 11 and helper['installed_SHA256'] == {row['target']: row['sha256'] for row in protocol['installation']}
    assert all(entries[name]['sha256'] == pin == sha(root / name) for name, pin in protocol['bindings'].items())
    assert all(entries[name]['sha256'] == pin == sha(root / name) for name, pin in protocol['installed_runtime_SHA256'].items())
    authorization, reply = read(stage / 'author/authorization.json'), read(stage / 'author/direct_human_reply.json')
    source_file = stage / 'author/source_publication_receipt.json'
    proof = read(source_file)
    assert authorization['authorized'] is True and authorization['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert authorization['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit'] == BASE
    assert authorization['protocol_sha256'] == config['protocol_sha256']
    assert authorization['human_evidence_sha256'] == sha(stage / 'author/direct_human_reply.json')
    assert authorization['source_publication_receipt_sha256'] == sha(source_file)
    assert authorization['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip()
    for row in config['front_history']:
        prior = git(root, 'show', BASE + ':' + row['path'])
        current = (root / row['path']).read_bytes()
        assert digest(prior) == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert entries[row['path']]['sha256'] == row['new_sha256']
    assert {row['path'] for row in config['front_history']} == FRONTS
    for name, pin in config['closed_output_SHA256'].items():
        assert entries[name]['sha256'] == pin
    actual_stage = {path.relative_to(root).as_posix() for path in stage.rglob('*') if path.is_file()}
    assert actual_stage == {name for name in entries if name.startswith(REL + '/')}
    review = read(root / config['final_review_path'])
    assert review['status'] == 'pass_static_execution_delivery_closed'
    assert review['config_sha256'] == sha(stage / 'author/execution_delivery_config.json')
    assert set(config['allowed_delta_paths']) - {config['final_review_path']} <= review['reviewed_repository_SHA256'].keys()
    for name, pin in review['reviewed_repository_SHA256'].items():
        assert entries[name]['sha256'] == pin
    return protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    parser.add_argument('--external-base', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), args.external_base.resolve()
    config = read(root / REL / 'author/execution_delivery_config.json')
    proof = read(root / REL / 'author/source_publication_receipt.json')
    oldraw = git(root, 'show', BASE + ':' + MANIFEST)
    old = json.loads(oldraw)
    previous = {row['path']: row for row in old['files']}
    assert proof['published_commit'] == BASE and proof['status'] == 'published_and_incrementally_restored_pass'
    assert proof['prepared_card'] == 'M-INTEGRATE1' and proof['authorized'] is proof['executed'] is False
    assert digest(oldraw) == proof['manifest_sha256'] and len(previous) == proof['ordinary_manifest_files']
    assert sum(row['bytes'] for row in previous.values()) == proof['ordinary_manifest_bytes']
    allowed = set(config['allowed_delta_paths'])
    installation = read(root / REL / 'protocol.json')['installation']
    targets = {row['target'] for row in installation}
    changed_old = FRONTS | {row['target'] for row in installation if row['previous_sha256'] is not None}
    assert len(changed_old) == 10 and len(allowed) == len(config['allowed_delta_paths'])
    assert changed_old | targets <= allowed
    assert all(name in FRONTS | targets or name.startswith(REL + '/') for name in allowed)
    assert sha(root / REL / 'author/deliver_execution.py') == sha(external / 'deliver_execution.py')
    delta_file = external / 'execution_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root, restore):
        assert git(tree, 'branch', '--show-current').decode().strip() == 'main'
        assert git(tree, 'remote', 'get-url', 'origin').decode().strip() == ORIGIN
        assert git(tree, 'remote', 'get-url', '--push', 'origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE and not delta_file.exists()
        assert (root / MANIFEST).read_bytes() == oldraw
        assert not git(root, 'diff', '--name-only') and not git(root, 'ls-files', '--others', '--exclude-standard', '-z')
        paths = names(git(root, 'ls-files', '-z')) - {MANIFEST}
        new = paths - previous.keys()
        assert not (previous.keys() - paths)
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == new | changed_old
        delta = [identity(root, name) for name in sorted(allowed)]
        entries = dict(previous, **{row['path']: row for row in delta})
        protocol = check_execution(root, config, entries)
        manifest = dict(old, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
            storage_stage='saved_native_default_integration_executed_001', files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        (root / MANIFEST).write_bytes(raw)
        value = dict(status='incremental_execution_delivery_pass', previous_delivery_commit=BASE,
            manifest_sha256=digest(raw), ordinary_manifest_files=len(entries), ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta, delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(previous) - 10,
            protocol_sha256=sha(root / REL / 'protocol.json'), executed_card='M-INTEGRATE1', execution_status='pass', execution_closed=True,
            authorized=True, executed=True, default_core_installed=True,
            new_full_source_scan=False, new_NPZ_decodes_or_HF_or_tests_or_plots=0)
        write_new(delta_file, value)
    else:
        source = read(delta_file)
        commit = git(root, 'rev-parse', 'HEAD').decode().strip()
        assert git(root, 'rev-parse', 'HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root, 'ls-remote', '--heads', 'origin', 'main').decode().split() == [commit, 'refs/heads/main']
        for tree in (root, restore):
            assert git(tree, 'rev-parse', 'HEAD').decode().strip() == commit and not git(tree, 'status', '--porcelain')
        assert (root / MANIFEST).read_bytes() == (restore / MANIFEST).read_bytes() and sha(restore / MANIFEST) == source['manifest_sha256']
        manifest = read(restore / MANIFEST)
        entries = {row['path']: row for row in manifest['files']}
        assert len(entries) == source['ordinary_manifest_files'] and sum(row['bytes'] for row in entries.values()) == source['ordinary_manifest_bytes']
        assert names(git(root, 'diff', '--name-only', '-z', BASE, commit)) == allowed | {MANIFEST}
        assert {row['path'] for row in source['delta_files']} == allowed
        for tree in (root, restore):
            assert names(git(tree, 'ls-files', '-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree, row['path']) == row == entries[row['path']] for row in source['delta_files'])
            check_execution(tree, config, entries)
        assert all(entries[name] == previous[name] for name in previous.keys() - allowed)
        assert manifest['science_version'] == old['science_version'] == '0.5.0'
        assert manifest['science_baseline_commit'] == old['science_baseline_commit']
        value = dict(status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, previous_delivery_commit=BASE, branch='main', origin=ORIGIN,
            source_and_restore_clean=True, remote_main_confirmed_equal=True, restore_root=str(restore),
            manifest_sha256=source['manifest_sha256'], ordinary_manifest_files=len(entries), ordinary_manifest_bytes=source['ordinary_manifest_bytes'],
            delta_files_restored_and_hashed=len(allowed), delta_bytes=source['delta_bytes'],
            unchanged_manifest_entries_inherited=source['unchanged_manifest_entries_inherited'],
            protocol_sha256=source['protocol_sha256'], executed_card='M-INTEGRATE1', authorized=True, executed=True,
            execution_status='pass', execution_closed=True, default_core_installed=True,
            new_full_source_or_restore_scan=False, new_NPZ_decodes_or_HF_or_tests_or_plots=0, whole_HF5_complete=False)
        write_new(external / 'execution_publication_receipt.json', value)
    print(json.dumps({key: item for key, item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
