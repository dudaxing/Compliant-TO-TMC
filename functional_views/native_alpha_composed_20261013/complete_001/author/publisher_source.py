"""Publish M-PATH1 ordinary preparation only; inherit the closed M-UNLOAD2 manifest."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

BASE = '8e92a293a0e9c13a31312d56ece458c5c6dc3c1f'
REL = 'functional_views/native_alpha_composed_20261013/complete_001'
MANIFEST = 'handoff/repository_manifest.json'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
RUNTIME = {'compose_path.py', 'render_path.py', 'execute_path.py', 'launch_path.py'}
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
ORDINARY = {'.json', '.py', '.md', '.toml'}


def path_in(root, name):
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = (root / relative).resolve()
    path.relative_to(root)
    return path


def raw(path):
    assert path.suffix.lower() in ORDINARY, 'Ordinary files only; scientific/media bytes remain inherited'
    return path.read_bytes()


def sha(path):
    return sha256(raw(path)).hexdigest()


def read(path):
    return json.loads(raw(path))


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)


def names(value):
    return {part.decode('utf-8') for part in value.split(b'\0') if part}


def identity(root, name):
    path = path_in(root, name)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def check_preparation(root, entries, old):
    stage = root / REL
    protocol_path = stage / 'protocol.json'
    protocol = read(protocol_path)
    assert protocol['schema_version'] == 'composed-saved-path-card-1.0' and protocol['card'] == 'M-PATH1'
    assert protocol['source_baseline_commit'] == BASE and protocol['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is False
    assert (protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (180, 240, 8*1024**3)
    spec = read(stage / 'path_spec.json')
    assert spec == protocol['path_spec'] and spec['schema_version'] == 'mpath1-compose-spec-1.0'
    assert spec['source_baseline_commit'] == BASE and len(spec['segments']) == 5 and len(spec['references']) == 2
    assert (protocol['expected_raw_rows'], protocol['expected_unique_rows'], protocol['expected_shared_anchors'], protocol['expected_PNGs']) == (29, 25, 4, 2)
    assert protocol['new_F_T_HP_solver_tests_default_installations'] == protocol['new_GIF_decodes_or_generation'] == 0
    assert protocol['postrun_new_PNG_pixel_QA_maximum'] == 2
    assert all(protocol[key] is False for key in ('single_full_path_producer_run', 'full_path_reference_qualified',
        'pressure_qualified', 'effective_clamp_qualified', 'stability_qualified', 'HF5_qualified'))
    assert not any((stage / name).exists() for name in ('run_001', 'path_launch.json', 'path_stdout.log', 'stop_requested.txt'))
    assert not any((stage / 'author' / name).exists() for name in ('authorization.json', 'direct_human_reply.json', 'source_publication_receipt.json'))
    inputs = {item[key] for item in spec['segments'] for key in ('result', 'viewer_summary', 'model', 'view_descriptor')}
    inputs.update(item['summary'] for item in spec['references'])
    assert set(protocol['bindings']) == inputs | {REL+'/'+name for name in RUNTIME | {'path_spec.json'}}
    for name, pin in protocol['bindings'].items():
        assert entries[name]['sha256'] == pin == sha(path_in(root, name))
        if name in old:
            assert entries[name] == old[name]
    media = protocol['existing_GIF_identities_stat_only']
    assert len(media) == 5 and set(media) == {item['gif'] for item in spec['segments']}
    assert not media.keys() & protocol['bindings'].keys()
    for name, record in media.items():
        path = path_in(root, name)
        assert path.suffix.lower() == '.gif' and set(record) == {'sha256', 'bytes'}
        assert record == {key:old[name][key] for key in ('sha256', 'bytes')} and entries[name] == old[name]
        assert path.is_file() and path.stat().st_size == record['bytes']  # Metadata only, never a media read/hash.
    receipt = read(stage / 'author/preparation_receipt.json')
    assert receipt['card'] == 'M-PATH1' and receipt['source_baseline_commit'] == BASE
    assert receipt['authorized'] is receipt['executed'] is receipt['installed'] is False
    assert receipt['review_files'] == ['author/final_source_review.json']
    for name, pin in receipt['artifact_SHA256'].items():
        assert name.startswith(REL+'/') and entries[name]['sha256'] == pin == sha(path_in(root, name))
    assert {row['path'] for row in receipt['front_history']} == FRONTS
    for row in receipt['front_history']:
        prior = git(root, 'show', BASE+':'+row['path'])
        current = raw(root / row['path'])
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha256(current).hexdigest() == row['new_sha256'] == entries[row['path']]['sha256']
    review = read(stage / 'author/final_source_review.json')
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    assert review['authorized'] is review['executed'] is False and review['protocol_SHA256'] == sha(protocol_path)
    required = RUNTIME | {'path_spec.json', 'protocol.json', 'M-PATH1_CARD.md', 'PREPARATION_RESULTS.md'}
    assert required <= review['current_source_SHA256'].keys()
    assert all(sha(path_in(stage, name)) == pin for name, pin in review['current_source_SHA256'].items())
    assert (stage / 'author/final_source_review.md').is_file()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root, restore, external = args.repo.resolve(), args.restore.resolve(), Path(__file__).resolve().parent
    assert not external.is_relative_to(root), 'Run the external publisher; the formal copy is recovery evidence only'
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']:row for row in previous['files']}
    proof = read(root / REL / 'author/previous_execution_publication_receipt.json')
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['executed_card'] == 'M-UNLOAD2' and proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    assert proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert len(old) == len(previous['files']) == proof['ordinary_manifest_files'] == 19914
    assert sum(row['bytes'] for row in old.values()) == proof['ordinary_manifest_bytes']
    assert previous['science_version'] == '0.5.0' and previous['science_baseline_commit'] == 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
    delta_file = external / 'source_delivery_delta_verify.json'
    for tree in (root,) if args.mode == 'finalize' else (root, restore):
        assert git(tree, 'branch', '--show-current').decode().strip() == 'main'
        assert git(tree, 'remote', 'get-url', 'origin').decode().strip() == ORIGIN
        assert git(tree, 'remote', 'get-url', '--push', 'origin').decode().strip() == ORIGIN
    if args.mode == 'finalize':
        assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE and not delta_file.exists()
        assert raw(root / MANIFEST) == oldraw and not git(root, 'diff', '--name-only')
        assert not git(root, 'ls-files', '--others', '--exclude-standard', '-z')
        stage = {path.relative_to(root).as_posix() for path in (root / REL).rglob('*') if path.is_file()}
        assert stage and not stage & old.keys()
        allowed = stage | FRONTS
        paths = names(git(root, 'ls-files', '-z')) - {MANIFEST}
        assert not old.keys() - paths
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == (paths-old.keys()) | FRONTS
        delta = [identity(root, name) for name in sorted(allowed)]
        entries = dict(old, **{row['path']:row for row in delta})
        assert paths == entries.keys()
        check_preparation(root, entries, old)
        manifest = dict(previous, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
            storage_stage='composed_saved_alpha_path_source_prepared_001', files=[entries[name] for name in sorted(paths)])
        output = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        (root / MANIFEST).write_bytes(output)
        value = dict(status='incremental_preparation_delivery_pass', previous_delivery_commit=BASE,
            manifest_sha256=sha256(output).hexdigest(), ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()), delta_files=delta,
            delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(old)-len(FRONTS),
            protocol_sha256=sha(root / REL / 'protocol.json'), prepared_card='M-PATH1', prepared=True, authorized=False, executed=False,
            existing_GIF_identities_inherited_and_stat_only=5, default_changes=0, new_full_source_scan=False,
            old_scientific_or_media_byte_reads=0, new_HF_API_HP_solver_tests_pixels_or_plots=0,
            single_full_path_producer_run=False, full_path_reference_qualified=False, whole_HF5_complete=False)
        write_new(delta_file, value)
    else:
        source = read(delta_file)
        assert source['status'] == 'incremental_preparation_delivery_pass' and source['previous_delivery_commit'] == BASE
        assert source['prepared_card'] == 'M-PATH1' and source['prepared'] is True and source['authorized'] is source['executed'] is False
        commit = git(root, 'rev-parse', 'HEAD').decode().strip()
        assert git(root, 'rev-parse', 'HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root, 'ls-remote', '--heads', 'origin', 'main').decode().split() == [commit, 'refs/heads/main']
        for tree in (root, restore):
            assert git(tree, 'rev-parse', 'HEAD').decode().strip() == commit and not git(tree, 'status', '--porcelain')
        assert raw(root / MANIFEST) == raw(restore / MANIFEST) and sha(restore / MANIFEST) == source['manifest_sha256']
        current = read(restore / MANIFEST)
        entries = {row['path']:row for row in current['files']}
        assert len(entries) == len(current['files']) == source['ordinary_manifest_files']
        assert sum(row['bytes'] for row in entries.values()) == source['ordinary_manifest_bytes']
        allowed = {row['path'] for row in source['delta_files']}
        assert len(allowed) == len(source['delta_files'])
        assert names(git(root, 'diff', '--name-only', '-z', BASE, commit)) == allowed | {MANIFEST}
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        for tree in (root, restore):
            assert names(git(tree, 'ls-files', '-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree, row['path']) == row == entries[row['path']] for row in source['delta_files'])
            assert {path.relative_to(tree).as_posix() for path in (tree / REL).rglob('*') if path.is_file()} | FRONTS == allowed
            check_preparation(tree, entries, old)
        assert current['previous_delivery_commit'] == BASE
        assert current['science_version'] == previous['science_version'] and current['science_baseline_commit'] == previous['science_baseline_commit']
        value = dict(source, status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, branch='main', origin=ORIGIN, source_and_restore_clean=True, remote_main_confirmed_equal=True,
            restore_root=str(restore), delta_files_restored_and_hashed=len(allowed), new_full_source_or_restore_scan=False)
        value.pop('delta_files')
        write_new(external / 'source_publication_receipt.json', value)
    print(json.dumps({key:item for key,item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
