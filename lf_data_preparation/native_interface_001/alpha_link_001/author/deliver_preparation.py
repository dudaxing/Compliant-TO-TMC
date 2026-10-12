"""Publish the explicit M-ALINK1 preparation delta; no science or media reread."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

BASE = '84c67e48ba61548a1c15d2c049870678ef58f573'
REL = 'lf_data_preparation/native_interface_001/alpha_link_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
read = lambda path: json.loads(path.read_bytes())
git = lambda root, *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def identity(root, name):
    path = (root / name).resolve()
    path.relative_to(root)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def check_preparation(root, entries, old):
    stage = root / REL
    protocol = read(stage / 'protocol.json')
    assert protocol['card'] == 'M-ALINK1' and protocol['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is False
    assert protocol['expected_accepted_states'] == 2 and len(protocol['bindings']) == 30
    assert protocol['phases']['link'] == dict(helper_seconds=180, outer_seconds=240)
    assert protocol['original_target_indices'] == [13, 14] and protocol['targets_mm'] == [1.2, 1.15]
    assert not (stage / 'run_001').exists() and not (stage / 'link_launch.json').exists()
    assert not any((stage / 'author' / name).exists() for name in
        ('authorization.json', 'direct_human_reply.json', 'source_publication_receipt.json'))
    media = set(protocol['inherited_media_bindings'])
    assert len(media) == 4 and set(protocol['media_files']) == media
    assert {name for name in protocol['bindings'] if Path(name).suffix.lower() in ('.png', '.gif')} == media
    for name, pin in protocol['bindings'].items():
        assert Path(name).suffix.lower() in ('.json', '.py', '.md', '.png', '.gif')
        assert entries[name]['sha256'] == pin
        if name in media:
            assert old[name] == entries[name] and (root / name).stat().st_size == old[name]['bytes']
        else:
            assert sha(root / name) == pin
    receipt = read(stage / 'author/preparation_receipt.json')
    assert receipt['status'] == 'prepared_static_review_only' and receipt['authorized'] is receipt['executed'] is False
    for name, pin in receipt['artifact_SHA256'].items():
        assert entries[name]['sha256'] == pin == sha(root / name)
    for row in receipt['front_history']:
        prior = git(root, 'show', BASE + ':' + row['path'])
        current = (root / row['path']).read_bytes()
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert entries[row['path']]['sha256'] == row['new_sha256']
    assert {row['path'] for row in receipt['front_history']} == FRONTS
    for name in ('candidate_scope_resource_review.json', 'candidate_input_protocol_review.json'):
        review = read(stage / 'author' / name)
        assert review['status'] == 'pass_static_candidate_review_not_executed'
        assert review['candidate_SHA256'] == sha(stage / 'execute_alpha_link.py')
        assert review['protocol_SHA256'] == sha(stage / 'protocol.json')
        assert review['launcher_SHA256'] == sha(stage / 'launch_link.py')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), Path(__file__).resolve().parent
    oldraw = git(root, 'show', BASE + ':' + MANIFEST)
    old_manifest = json.loads(oldraw)
    old = {row['path']: row for row in old_manifest['files']}
    prior = read(root / REL / 'author/previous_publication_receipt.json')
    assert prior['status'] == 'published_and_incrementally_restored_pass' and prior['published_commit'] == BASE
    assert prior['executed_card'] == 'M-AREF1' and prior['execution_status'] == 'pass' and prior['execution_closed'] is True
    assert prior['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert len(old) == prior['ordinary_manifest_files'] and sum(row['bytes'] for row in old.values()) == prior['ordinary_manifest_bytes']
    delta_file = external / 'preparation_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root, restore):
        assert git(tree, 'branch', '--show-current').decode().strip() == 'main'
        assert git(tree, 'remote', 'get-url', 'origin').decode().strip() == ORIGIN
        assert git(tree, 'remote', 'get-url', '--push', 'origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE and not delta_file.exists()
        assert (root / MANIFEST).read_bytes() == oldraw
        assert not git(root, 'diff', '--name-only') and not git(root, 'ls-files', '--others', '--exclude-standard', '-z')
        stage = {path.relative_to(root).as_posix() for path in (root / REL).rglob('*') if path.is_file()}
        allowed = stage | FRONTS
        assert all(Path(name).suffix.lower() in ('.json', '.py', '.md') for name in allowed)
        assert not stage & old.keys()
        paths = names(git(root, 'ls-files', '-z')) - {MANIFEST}
        assert not old.keys() - paths
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == (paths - old.keys()) | FRONTS
        delta = [identity(root, name) for name in sorted(allowed)]
        entries = dict(old, **{row['path']: row for row in delta})
        check_preparation(root, entries, old)
        manifest = dict(old_manifest, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
            storage_stage='saved_alpha_linked_response_prepared_001', files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        (root / MANIFEST).write_bytes(raw)
        value = dict(status='incremental_preparation_delivery_pass', previous_delivery_commit=BASE,
            manifest_sha256=sha256(raw).hexdigest(), ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()), delta_files=delta,
            delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=sha(root / REL / 'protocol.json'), prepared_card='M-ALINK1', prepared=True,
            authorized=False, executed=False, media_bindings_inherited_not_byte_reread=4,
            new_full_source_scan=False, media_byte_reads_NPZ_gzip_HF_API_tests_HP_plots=0)
        write_new(delta_file, value)
    else:
        source = read(delta_file)
        commit = git(root, 'rev-parse', 'HEAD').decode().strip()
        assert git(root, 'rev-parse', 'HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root, 'ls-remote', '--heads', 'origin', 'main').decode().split() == [commit, 'refs/heads/main']
        for tree in (root, restore):
            assert git(tree, 'rev-parse', 'HEAD').decode().strip() == commit and not git(tree, 'status', '--porcelain')
        assert (root / MANIFEST).read_bytes() == (restore / MANIFEST).read_bytes() and sha(restore / MANIFEST) == source['manifest_sha256']
        entries = {row['path']: row for row in read(restore / MANIFEST)['files']}
        allowed = {row['path'] for row in source['delta_files']}
        assert names(git(root, 'diff', '--name-only', '-z', BASE, commit)) == allowed | {MANIFEST}
        for tree in (root, restore):
            assert names(git(tree, 'ls-files', '-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree, row['path']) == row == entries[row['path']] for row in source['delta_files'])
            check_preparation(tree, entries, old)
        assert all(entries[name] == old[name] for name in old.keys() - allowed)
        current_manifest = read(restore / MANIFEST)
        assert current_manifest['science_version'] == old_manifest['science_version'] == '0.5.0'
        assert current_manifest['science_baseline_commit'] == old_manifest['science_baseline_commit']
        value = dict(status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, previous_delivery_commit=BASE, branch='main', origin=ORIGIN,
            source_and_restore_clean=True, remote_main_confirmed_equal=True, restore_root=str(restore),
            manifest_sha256=source['manifest_sha256'], ordinary_manifest_files=len(entries), ordinary_manifest_bytes=source['ordinary_manifest_bytes'],
            delta_files_restored_and_hashed=len(allowed), delta_bytes=source['delta_bytes'],
            unchanged_manifest_entries_inherited=source['unchanged_manifest_entries_inherited'], protocol_sha256=source['protocol_sha256'],
            prepared_card='M-ALINK1', prepared=True, authorized=False, executed=False,
            media_bindings_inherited_not_byte_reread=4, new_full_source_or_restore_scan=False,
            media_byte_reads_NPZ_gzip_HF_API_tests_HP_plots=0, whole_HF5_complete=False)
        write_new(external / 'source_publication_receipt.json', value)
    print(json.dumps({key: item for key, item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
