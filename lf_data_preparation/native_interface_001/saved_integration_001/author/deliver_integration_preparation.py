"""Incremental ordinary M-INTEGRATE1 preparation publication; never science."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = 'd45f6ee92d8a0d6ca740772a1762abdc691489fa'
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
read = lambda path: json.loads(path.read_bytes())
digest = lambda raw: sha256(raw).hexdigest()
sha = lambda path: digest(path.read_bytes())
git = lambda root, *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def identity(root, name):
    path = (root / name).resolve()
    path.relative_to(root)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def check_preparation(root, config, entries):
    protocol = read(root / REL / 'protocol.json')
    assert protocol['card'] == 'M-INTEGRATE1' and protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert sha(root / REL / 'protocol.json') == config['protocol_sha256']
    assert not (root / REL / 'run_001').exists() and not (root / REL / 'integration_launch.json').exists()
    assert all(entries[name]['sha256'] == pin == sha(root / name) for name, pin in protocol['bindings'].items())
    for row in protocol['installation']:
        path = root / row['target']
        assert (sha(path) if path.exists() else None) == row['previous_sha256']
    for row in config['front_history']:
        prior = git(root, 'show', BASE + ':' + row['path'])
        current = (root / row['path']).read_bytes()
        assert digest(prior) == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert entries[row['path']]['sha256'] == row['new_sha256']
    review = read(root / config['final_review_path'])
    assert review['status'] == 'pass_static_preparation_delivery_not_executed'
    assert review['config_sha256'] == sha(root / REL / 'author/preparation_delivery_config.json')
    for name, pin in review['reviewed_repository_SHA256'].items():
        assert entries[name]['sha256'] == pin
    assert set(config['allowed_delta_paths']) - {config['final_review_path']} <= review['reviewed_repository_SHA256'].keys()
    return protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    parser.add_argument('--external-base', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), args.external_base.resolve()
    config = read(root / REL / 'author/preparation_delivery_config.json')
    proof_file = root / REL / 'author/M_RESUME1_execution_publication_receipt.json'
    proof = read(proof_file)
    oldraw = git(root, 'show', BASE + ':' + MANIFEST)
    old = json.loads(oldraw)
    previous = {row['path']: row for row in old['files']}
    assert proof['published_commit'] == BASE and proof['status'] == 'published_and_incrementally_restored_pass'
    assert proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    assert digest(oldraw) == proof['manifest_sha256'] and len(previous) == proof['ordinary_manifest_files']
    assert sum(row['bytes'] for row in previous.values()) == proof['ordinary_manifest_bytes']
    allowed = set(config['allowed_delta_paths'])
    assert len(allowed) == len(config['allowed_delta_paths']) and FRONTS <= allowed
    assert all(name in FRONTS or name.startswith(REL + '/') for name in allowed)
    assert sha(root / REL / 'author/deliver_integration_preparation.py') == sha(external / 'deliver_integration_preparation.py')
    delta_file = external / 'preparation_delivery_delta_verify.json'
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
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == new | FRONTS
        delta = [identity(root, name) for name in sorted(allowed)]
        entries = dict(previous, **{row['path']: row for row in delta})
        protocol = check_preparation(root, config, entries)
        manifest = dict(old, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
            storage_stage='saved_native_integration_prepared_001', files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        (root / MANIFEST).write_bytes(raw)
        value = dict(status='incremental_preparation_delivery_pass', previous_delivery_commit=BASE,
            manifest_sha256=digest(raw), ordinary_manifest_files=len(entries), ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()),
            delta_files=delta, delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(previous) - 2,
            protocol_sha256=sha(root / REL / 'protocol.json'), prepared_card='M-INTEGRATE1', prepared=True, authorized=False, executed=False,
            new_full_source_scan=False, new_NPZ_or_HF_or_tests_or_plots=0)
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
            check_preparation(tree, config, entries)
        assert all(entries[name] == previous[name] for name in previous.keys() - allowed)
        assert manifest['science_version'] == old['science_version'] == '0.5.0'
        assert manifest['science_baseline_commit'] == old['science_baseline_commit']
        value = dict(status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, previous_delivery_commit=BASE, branch='main', origin=ORIGIN,
            source_and_restore_clean=True, remote_main_confirmed_equal=True, restore_root=str(restore),
            manifest_sha256=source['manifest_sha256'], ordinary_manifest_files=len(entries), ordinary_manifest_bytes=source['ordinary_manifest_bytes'],
            delta_files_restored_and_hashed=len(allowed), delta_bytes=source['delta_bytes'],
            unchanged_manifest_entries_inherited=source['unchanged_manifest_entries_inherited'],
            protocol_sha256=source['protocol_sha256'], prepared_card='M-INTEGRATE1', prepared=True, authorized=False, executed=False,
            default_core_installed=False, new_full_source_or_restore_scan=False, new_NPZ_or_HF_or_tests_or_plots=0, whole_HF5_complete=False)
        write_new(external / 'publication_receipt.json', value)
    print(json.dumps({key: item for key, item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
