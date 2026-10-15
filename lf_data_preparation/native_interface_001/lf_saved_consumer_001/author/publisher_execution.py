"""Incrementally publish the closed L-USE1 ordinary saved-result consumer."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

BASE = 'c9ca9a23464bed01aff3ee7a6a0410a09c933d9e'
REL = 'lf_data_preparation/native_interface_001/lf_saved_consumer_001'
MANIFEST = 'handoff/repository_manifest.json'
MANIFEST_SHA = '6e6cd66da5fea65b339ea91993b8d66bc8ce6942b379796a9732407d043757bb'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
FINAL_JSON = REL+'/author/final_execution_review.json'
FINAL_MD = REL+'/author/final_execution_review.md'
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
SCIENCE_BASE = 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
ORDINARY = {'.json', '.py', '.md', '.log', '.txt'}
EXPECTED_CALLS = dict(consumptions_started=1, consumptions_completed=1,
    json_reads_started=3, json_reads_completed=3, table_writes=1, review_writes=1)


def path_in(root, name):
    relative = Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = (root/relative).resolve()
    path.relative_to(root)
    return path


def raw(path):
    assert path.suffix.lower() in ORDINARY, 'Ordinary metadata only: '+str(path)
    return path.read_bytes()


def sha(path):
    return sha256(raw(path)).hexdigest()


def read(path):
    assert path.suffix.lower() == '.json'
    return json.loads(raw(path))


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=root)


def names(value):
    return {part.decode('utf-8') for part in value.split(b'\0') if part}


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def identity(root, name):
    path = path_in(root, name)
    return dict(path=name, bytes=path.stat().st_size, sha256=sha(path))


def check_closed(root, entries, old, allowed):
    stage = root/REL
    protocol = read(stage/'protocol.json')
    protocol_sha = sha(stage/'protocol.json')
    authorization = read(stage/'author/authorization.json')
    assert protocol['card'] == authorization['card'] == 'L-USE1'
    assert authorization['authorization_from_direct_human_reply'] is True
    assert authorization['direct_human_answer'] == '批准按 L-USE1 执行'
    assert authorization['authorized_execution_source_commit'] == BASE
    assert authorization['protocol_sha256'] == protocol_sha
    for name, pin in protocol['bindings'].items():
        assert entries[name]['sha256'] == pin
        if name in old:
            assert entries[name] == old[name]
    outer = read(stage/'use_launch.json')
    helper = read(stage/'run_001/execution_receipt.json')
    assert outer['card'] == helper['card'] == 'L-USE1'
    assert outer['protocol_sha256'] == helper['protocol_sha256'] == protocol_sha
    assert outer['authorized_execution_source_commit'] == helper['authorized_execution_source_commit'] == BASE
    assert outer['status'] == helper['status'] and outer['status'] in ('pass', 'not_pass')
    assert outer['invocations'] == 1 and outer['completed_utc']
    for name, pin in helper['outputs'].items():
        path_in(root, name).relative_to(stage/'run_001')
        assert set(pin) == {'sha256', 'bytes'} and entries[name] == dict(path=name, **pin)
    # No old science or media is hashed. Its closed producer identity remains
    # inherited; only the five declared media sizes are observed here.
    for name, pin in protocol['inherited_media_bindings'].items():
        assert set(pin) == {'sha256', 'bytes'} and old[name] == dict(path=name, **pin)
        assert entries[name] == old[name] and path_in(root, name).stat().st_size == pin['bytes']
    assert len(protocol['inherited_media_bindings']) == 5
    if outer['status'] == 'pass':
        assert outer['exit_code'] == 0 and outer['stop_reason'] is None
        assert 0 <= outer['elapsed_seconds'] <= 180
        assert outer['peak_sampled_tree_RSS_bytes'] <= 1024**3
        assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
        assert 0 <= helper['elapsed_seconds'] <= 120
        assert helper['sampled_peak_RSS_bytes'] <= 1024**3
        assert helper['calls'] == EXPECTED_CALLS and helper['rows_written'] == 25
        assert helper['selected_indices'] == [13, 16] and helper['matched_reference_rows'] == 2
        assert set(helper['outputs']) == {REL+'/run_001/states_table.json', REL+'/run_001/REVIEW.md'}
        output_names = {path.relative_to(root).as_posix() for path in (stage/'run_001').rglob('*') if path.is_file()}
        assert output_names == set(helper['outputs']) | {REL+'/run_001/execution_receipt.json'}
    closure = read(stage/'author/execution_documentation_receipt.json')
    assert closure['source_baseline_commit'] == BASE and closure['actual_execution_closed'] is True
    assert closure['actual_execution_status'] == outer['status']
    assert {row['path'] for row in closure['front_history']} == FRONTS
    for row in closure['front_history']:
        prior = git(root, 'show', BASE+':'+row['path'])
        current = raw(root/row['path'])
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha256(current).hexdigest() == row['new_sha256'] == entries[row['path']]['sha256']
    review = read(root/FINAL_JSON)
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    assert review['authorized'] is review['executed'] is review['execution_closed'] is True
    assert review['execution_status'] == outer['status'] and review['protocol_SHA256'] == protocol_sha
    assert FINAL_JSON not in review['reviewed_repository_SHA256'] and FINAL_MD in review['reviewed_repository_SHA256']
    assert allowed-{FINAL_JSON} == review['reviewed_repository_SHA256'].keys()
    assert all(entries[name]['sha256'] == pin for name, pin in review['reviewed_repository_SHA256'].items())
    return outer['status'], protocol_sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preview', 'finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root, restore, here = args.repo.resolve(), args.restore.resolve(), Path(__file__).resolve().parent
    assert not here.is_relative_to(root), 'Use the external publisher; formal copy is recovery source only'
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']: row for row in previous['files']}
    assert sha256(oldraw).hexdigest() == MANIFEST_SHA and len(old) == len(previous['files']) == 20672
    assert sum(row['bytes'] for row in old.values()) == 11310476880
    assert previous['science_version'] == '0.5.0' and previous['science_baseline_commit'] == SCIENCE_BASE
    actual = {path.relative_to(root).as_posix() for path in (root/REL).rglob('*') if path.is_file()}
    assert not old.keys() & actual
    allowed = actual | FRONTS
    assert allowed & old.keys() == FRONTS
    assert {FINAL_JSON, FINAL_MD} <= allowed and all(Path(name).suffix.lower() in ORDINARY for name in allowed)
    delta_file = here/'execution_delivery_delta_verify.json'
    for tree in (root,) if args.mode != 'verify' else (root, restore):
        assert git(tree, 'branch', '--show-current').decode().strip() == 'main'
        assert git(tree, 'remote', 'get-url', 'origin').decode().strip() == git(tree, 'remote', 'get-url', '--push', 'origin').decode().strip() == ORIGIN
    if args.mode in ('preview', 'finalize'):
        assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE
        assert raw(root/MANIFEST) == oldraw and not git(root, 'diff', '--name-only')
        assert not git(root, 'ls-files', '--others', '--exclude-standard', '-z')
        paths = names(git(root, 'ls-files', '-z'))-{MANIFEST}
        assert not old.keys()-paths
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == (paths-old.keys()) | FRONTS
        delta = [identity(root, name) for name in sorted(allowed)]
        entries = dict(old, **{row['path']: row for row in delta})
        assert entries.keys() == paths
        status, protocol_sha = check_closed(root, entries, old, allowed)
        manifest = dict(previous, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
            storage_stage='saved_lf_external_consumer_'+status+'_closed_001', files=[entries[name] for name in sorted(paths)])
        output_raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        value = dict(status='incremental_execution_delivery_pass', previous_delivery_commit=BASE,
            manifest_sha256=sha256(output_raw).hexdigest(), ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()), delta_files=delta,
            delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(old)-2,
            protocol_sha256=protocol_sha, executed_card='L-USE1', authorized=True, executed=True,
            execution_closed=True, execution_status=status,
            old_media_identities_from_closed_input_stat_only=5,
            scientific_or_media_bytes_headers_hash_decode_by_publisher=0, new_HF_API_HP_solver_tests_pixels_or_plots=0,
            default_changes=0, new_full_source_scan=False,
            full25_LF_path_reference_qualified=False, whole_HF5_complete=False)
        if args.mode == 'preview':
            value['status'] = 'preview_pass_not_finalized'
            value['manifest_writes'] = 0
            write_new(here/'execution_delivery_preview.json', value)
        else:
            assert not delta_file.exists()
            (root/MANIFEST).write_bytes(output_raw)
            write_new(delta_file, value)
    else:
        source = read(delta_file)
        assert source['status'] == 'incremental_execution_delivery_pass' and source['previous_delivery_commit'] == BASE
        assert {row['path'] for row in source['delta_files']} == allowed
        commit = git(root, 'rev-parse', 'HEAD').decode().strip()
        assert git(root, 'rev-parse', 'HEAD^').decode().strip() == BASE and commit != BASE
        assert git(root, 'ls-remote', '--heads', 'origin', 'main').decode().split() == [commit, 'refs/heads/main']
        for tree in (root, restore):
            assert git(tree, 'rev-parse', 'HEAD').decode().strip() == commit and not git(tree, 'status', '--porcelain')
        assert raw(root/MANIFEST) == raw(restore/MANIFEST) and sha(restore/MANIFEST) == source['manifest_sha256']
        current = read(restore/MANIFEST)
        entries = {row['path']: row for row in current['files']}
        assert len(entries) == len(current['files']) == source['ordinary_manifest_files']
        assert sum(row['bytes'] for row in entries.values()) == source['ordinary_manifest_bytes']
        assert names(git(root, 'diff', '--name-only', '-z', BASE, commit)) == allowed | {MANIFEST}
        assert all(entries[name] == old[name] for name in old.keys()-allowed)
        for tree in (root, restore):
            assert names(git(tree, 'ls-files', '-z')) == entries.keys() | {MANIFEST}
            assert all(identity(tree, row['path']) == row == entries[row['path']] for row in source['delta_files'])
            assert {path.relative_to(tree).as_posix() for path in (tree/REL).rglob('*') if path.is_file()} | FRONTS == allowed
            assert check_closed(tree, entries, old, allowed) == (source['execution_status'], source['protocol_sha256'])
        assert current['science_version'] == previous['science_version'] and current['science_baseline_commit'] == SCIENCE_BASE
        value = dict(source, status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, branch='main', origin=ORIGIN, source_and_restore_clean=True,
            remote_main_confirmed_equal=True, restore_root=str(restore), delta_files_restored=len(allowed),
            old_media_restore_check='stat plus inherited closed input identity; no media rehash', new_full_source_or_restore_scan=False)
        value.pop('delta_files')
        write_new(here/'execution_publication_receipt.json', value)
    print(json.dumps({key: item for key, item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
