"""Publish only M-EREF1 ordinary preparation; inherit previous saved binary identities."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

BASE = '43e3ba7f981b2dc44fa84bc7e78b8f5d9e106bdf'
REL = 'lf_data_preparation/native_interface_001/extension_reference_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
read = lambda path: json.loads(path.read_bytes())
git = lambda root, *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def identity(root, name):
    path = (root / name).resolve()
    path.relative_to(root)
    assert path.suffix.lower() in {'.json', '.py', '.md', '.patch'}
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def new_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def check_preparation(root, entries, old):
    stage = root / REL
    protocol = read(stage / 'protocol.json')
    assert protocol['card'] == 'M-EREF1' and protocol['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is False
    assert protocol['phases']['reference'] == dict(helper_seconds=900, outer_seconds=960)
    assert protocol['sampled_RSS_bytes'] == 8 * 1024**3
    assert protocol['targets_mm'] == [1.1] and protocol['original_target_indices'] == [15]
    assert protocol['selected_child_accepted_index'] == 1
    assert protocol['expected_accepted_states'] == 1 and protocol['expected_new_HP_calls'] == 2
    assert len(protocol['reference_sources']) == 11 and len(protocol['gates']) == 15
    assert len(protocol['bindings']) == 50 and len(protocol['inherited_NPZ_bindings']) == 6
    assert protocol['new_reference_observation_plots'] == protocol['postrun_new_PNG_pixel_QA_maximum'] == 1
    assert protocol['full_child_path_reference_pass'] is protocol['full_original_path_reference_pass'] is protocol['full_extended_path_reference_pass'] is False
    assert protocol['reference_output'] == REL + '/run_001/reference'
    assert not any((stage / name).exists() for name in ('run_001', 'reference_launch.json', 'reference_stdout.log', 'stop_requested.txt'))
    assert not any((stage / 'author' / name).exists() for name in ('authorization.json', 'direct_human_reply.json', 'source_publication_receipt.json'))
    for name, pin in protocol['bindings'].items():
        assert entries[name]['sha256'] == pin
        if name in protocol['inherited_NPZ_bindings']:
            assert entries[name] == old[name] and (root / name).stat().st_size == old[name]['bytes']
            assert protocol['inherited_NPZ_bindings'][name]['sha256'] == pin
        else:
            assert sha(root / name) == pin
    for name, pin in protocol['installed_producer_sources'].items():
        assert entries[name] == old[name] and sha(root / name) == pin
    receipt = read(stage / 'author/preparation_receipt.json')
    assert receipt['status'] == 'prepared_static_review_only' and receipt['authorized'] is receipt['executed'] is receipt['installed'] is False
    assert all(entries[name]['sha256'] == pin == sha(root / name) for name, pin in receipt['artifact_SHA256'].items())
    for row in receipt['front_history']:
        prior = git(root, 'show', BASE + ':' + row['path'])
        current = (root / row['path']).read_bytes()
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert entries[row['path']]['sha256'] == row['new_sha256']
    assert {row['path'] for row in receipt['front_history']} == FRONTS
    for name in ('reference_candidate_static_review.json', 'final_protocol_scope_review.json'):
        review = read(stage / 'author' / name)
        assert review['authorized'] is review['executed'] is False and review['blocking_findings'] == []
        assert review['protocol_SHA256'] == sha(stage / 'protocol.json')
        assert all(sha(stage / path) == pin for path, pin in review['current_source_SHA256'].items())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), Path(__file__).resolve().parent
    oldraw = git(root, 'show', BASE + ':' + MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']: row for row in previous['files']}
    prior = read(root / REL / 'author/previous_publication_receipt.json')
    assert prior['status'] == 'published_and_incrementally_restored_pass' and prior['published_commit'] == BASE
    assert prior['executed_card'] == 'M-EXTEND2' and prior['execution_status'] == 'pass' and prior['execution_closed'] is True
    assert prior['manifest_sha256'] == sha256(oldraw).hexdigest() and len(old) == prior['ordinary_manifest_files']
    assert sum(row['bytes'] for row in old.values()) == prior['ordinary_manifest_bytes']
    delta_file = external / 'preparation_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root, restore):
        assert git(tree, 'branch', '--show-current').decode().strip() == 'main'
        assert git(tree, 'remote', 'get-url', 'origin').decode().strip() == git(tree, 'remote', 'get-url', '--push', 'origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE and not delta_file.exists()
        assert (root / MANIFEST).read_bytes() == oldraw and not git(root, 'diff', '--name-only')
        assert not git(root, 'ls-files', '--others', '--exclude-standard', '-z')
        stage = {path.relative_to(root).as_posix() for path in (root / REL).rglob('*') if path.is_file()}
        allowed = stage | FRONTS
        assert not stage & old.keys()
        paths = names(git(root, 'ls-files', '-z')) - {MANIFEST}
        assert not old.keys() - paths
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == (paths - old.keys()) | FRONTS
        delta = [identity(root, name) for name in sorted(allowed)]
        entries = dict(old, **{row['path']: row for row in delta})
        check_preparation(root, entries, old)
        manifest = dict(previous, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
            storage_stage='saved_extension_selected_reference_prepared_001', files=[entries[name] for name in sorted(paths)])
        raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        (root / MANIFEST).write_bytes(raw)
        value = dict(status='incremental_preparation_delivery_pass', previous_delivery_commit=BASE,
            manifest_sha256=sha256(raw).hexdigest(), ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()), delta_files=delta,
            delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(old) - 2,
            protocol_sha256=sha(root / REL / 'protocol.json'), prepared_card='M-EREF1', prepared=True, authorized=False, executed=False,
            inherited_stat_only_NPZ=6, default_changes=0, new_full_source_scan=False,
            HF_import_tests_science_arrays_gzip_media_pixels_or_plots=0)
        new_json(delta_file, value)
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
        current = read(restore / MANIFEST)
        assert current['science_version'] == previous['science_version'] == '0.5.0'
        assert current['science_baseline_commit'] == previous['science_baseline_commit'] == 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
        value = dict(source, status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, branch='main', origin=ORIGIN, source_and_restore_clean=True, remote_main_confirmed_equal=True,
            restore_root=str(restore), delta_files_restored_and_hashed=len(allowed), new_full_source_or_restore_scan=False,
            whole_HF5_complete=False)
        value.pop('delta_files')
        new_json(external / 'source_publication_receipt.json', value)
    print(json.dumps({key: value for key, value in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
