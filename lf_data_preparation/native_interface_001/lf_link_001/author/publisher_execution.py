"""Publish closed L-LINK1 ordinary metadata; inherit all old science and media identities."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess

BASE = '4fd70556402347c73029cf7070217efaf7a4ea13'
REL = 'lf_data_preparation/native_interface_001/lf_link_001'
MANIFEST = 'handoff/repository_manifest.json'
MANIFEST_SHA = '1907289933f4f45315c39554644d19b972801e5cf9bbd920af3e827f2533ea8b'
PROTOCOL_SHA = '4ddc343278c59fb0532db93f6fae27c40ea2c9941e198d22fa500583405df1f1'
DEFAULT = 'hf_repo/src/hf_eval/native_response.py'
CANDIDATE_SHA = '346a97b30f675ccf063de1720002f936adf90011e69231edd89e776ba4e70eaa'
FRONTS = {'docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'}
FINAL_JSON = REL+'/author/final_execution_review.json'
FINAL_MD = REL+'/author/final_execution_review.md'
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
SCIENCE_BASE = 'b1334bb6a83ba9a0efab7bdba7bd39722146f024'
ORDINARY = {'.json', '.py', '.md', '.toml', '.log', '.txt', '.jsonl'}
EXPECTED_CALLS = dict(tests_started=1, tests_completed=1, saved_summary_started=1,
    saved_summary_completed=1, response_writes=1, index_writes=1,
    installation_started=1, installation_completed=1)


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
    proof_path, reply_path = stage/'author/source_publication_receipt.json', stage/'author/direct_human_reply.json'
    proof, reply, auth = read(proof_path), read(reply_path), read(stage/'author/authorization.json')
    assert protocol['card'] == proof['prepared_card'] == auth['card'] == reply['card'] == 'L-LINK1'
    assert protocol['schema_version'] == 'lf-selected-reference-linked-delivery-card-1.0'
    assert protocol['prepared'] is proof['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is proof['authorized'] is proof['executed'] is False
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['manifest_sha256'] == MANIFEST_SHA and proof['ordinary_manifest_files'] == 20573 and proof['ordinary_manifest_bytes'] == 11310175674
    assert auth['authorized'] is auth['one_invocation'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['authorized_execution_source_commit'] == reply['authorized_execution_source_commit'] == BASE
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip() and reply['reply_context']
    assert auth['human_evidence_sha256'] == sha(reply_path) and auth['source_publication_receipt_sha256'] == sha(proof_path)
    assert old[REL+'/protocol.json']['sha256'] == auth['protocol_sha256'] == proof['protocol_sha256'] == PROTOCOL_SHA
    phase = protocol['phases']['link']
    assert (phase['helper_seconds'], phase['outer_seconds'], phase['tests_seconds'], protocol['sampled_RSS_bytes']) == (180, 240, 60, 8*1024**3)
    assert (auth['helper_seconds'], auth['outer_seconds'], auth['sampled_RSS_bytes']) == (180, 240, 8*1024**3)
    assert len(protocol['bindings']) == 65 and len(protocol['inherited_media_bindings']) == 5
    assert protocol['source_before_installation']['path'] == DEFAULT and DEFAULT not in protocol['bindings']
    assert old[DEFAULT]['sha256'] == protocol['source_before_installation']['sha256']
    # The sole authorized run checked these identities. Do not reopen old source,
    # science or media content to repeat its checks after the execution window.
    assert all(entries[name] == old[name] and old[name]['sha256'] == pin for name, pin in protocol['bindings'].items())
    producers = [read(root/protocol[key]) for key in ('production_receipt_file', 'reference_execution_receipt_file')]
    sealed = {name: record for producer in producers for name, record in producer['outputs'].items()}
    assert all(producer['status'] == 'pass' and producer['output_identity_seal'] == 'complete_inside_original_helper_window' for producer in producers)
    for name, pin in protocol['inherited_media_bindings'].items():
        assert set(pin) == {'sha256', 'bytes'} and sealed[name] == pin
        assert old[name] == dict(path=name, **pin) and path_in(root, name).stat().st_size == pin['bytes']
    outer = read(stage/'link_launch.json')
    assert outer['completed_utc'] and outer['status'] in ('pass', 'not_pass') and outer['invocations'] in (0, 1)
    assert outer['card'] == 'L-LINK1' and outer['authorized_execution_source_commit'] == BASE and outer['protocol_sha256'] == PROTOCOL_SHA
    assert outer['actual_default_SHA256'] == entries[DEFAULT]['sha256'] == sha(root/DEFAULT)
    helper_path = stage/'run_001/execution_receipt.json'
    helper = read(helper_path) if helper_path.exists() else None
    if helper is not None:
        assert helper['status'] in ('pass', 'not_pass') and helper['protocol_sha256'] == PROTOCOL_SHA
        assert helper['authorized_execution_source_commit'] == BASE and helper['actual_default_SHA256'] == outer['actual_default_SHA256']
        assert all(helper[key] == 0 for key in ('new_NPZ_reads', 'new_gzip_reads', 'new_CSV_reads', 'media_decodes',
            'new_plots', 'new_force_calls', 'new_tangent_calls', 'new_HP_calls', 'new_solver_calls', 'new_model_constructions'))
        assert helper['mechanical_hooks_monitored'] is False
        for name, pin in helper['outputs'].items():
            path_in(root, name).relative_to(stage/'run_001')
            assert set(pin) == {'sha256', 'bytes'} and entries[name] == dict(path=name, **pin)
    if outer['status'] == 'pass':
        assert outer['invocations'] == 1 and outer['exit_code'] == 0 and outer['stop_reason'] is None
        assert outer['all_bindings_unchanged'] is outer['installation_complete'] is True
        assert 0 <= outer['elapsed_seconds'] <= 240 and 0 <= outer['child_terminal_wall_seconds'] <= 180
        assert outer['peak_sampled_tree_RSS_bytes'] <= 8*1024**3 and not (stage/'stop_requested.txt').exists()
        assert helper is not None and helper['status'] == outer['helper_status'] == 'pass' and helper['error'] is None
        assert helper['all_bindings_unchanged'] is helper['installation_complete'] is True
        assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
        assert helper['installed_file'] == DEFAULT and helper['candidate_SHA256'] == entries[DEFAULT]['sha256'] == CANDIDATE_SHA
        assert 0 <= helper['elapsed_seconds'] <= helper['helper_seconds'] == 180
        assert helper['sampled_peak_RSS_bytes'] <= helper['sampled_RSS_limit_bytes'] == 8*1024**3
        assert helper['unit_tests_run'] == 16 and helper['unit_reference_calls'] == 23 and helper['calls'] == EXPECTED_CALLS
        tests = read(stage/'run_001/tests_summary.json')
        assert tests['status'] == 'pass' and tests['failfast'] is True and tests['elapsed_seconds'] <= 60
        assert tests['unit_tests_run'] == 16 and tests['unit_reference_calls'] == 23
        assert tests['test_methods'] == protocol['expected_test_methods']
        output_names = {path.relative_to(root).as_posix() for path in (stage/'run_001').rglob('*') if path.is_file()}
        assert output_names == set(helper['outputs']) | {REL+'/run_001/execution_receipt.json'}
        linked, index = read(stage/'run_001/linked_response.json'), read(stage/'run_001/light_index.json')
        reference = linked['independent_reference']
        assert linked['status'] == 'success' and linked['failure'] is None
        assert linked['path']['completed'] is True and linked['path']['accepted_states'] == 25
        assert reference['status'] == 'matched_partial' and reference['selected_reference_pass'] is reference['source_bindings_verified'] is True
        assert reference['matched_state_indices'] == [13, 16] and reference['matched_state_count'] == 2
        assert reference['production_accepted_state_count'] == 25 and reference['HP_calls_completed'] == 4
        assert reference['covers_all_accepted_states'] is reference['accepted_reference_pass'] is reference['full_path_reference_pass'] is False
        assert all(reference[key] is False for key in ('HP_all_columns_qualified', 'contact_qualified', 'clamp_qualified', 'pressure_qualified', 'HF5_qualified'))
        assert all(flag is False for flag in linked['producer_flags'].values())
        assert linked['views']['status'] == 'matched' and len(linked['views']['links']) == 4
        original = read(root/protocol['original_response_file'])
        assert all(original.get(key) == value for key, value in linked.items() if key not in {'independent_reference', 'views'})
        assert index['status'] == 'pass' and index['independent_reference'] == reference
        assert index['source_flags'] == linked['producer_flags'] and index['selected_accepted_indices'] == [13, 16]
        assert index['production_accepted_states'] == 25 and len(index['images']) == 5
        assert {row['path'] for row in index['images']} == set(protocol['inherited_media_bindings'])
        assert all(row['sha256'] == protocol['bindings'][row['path']] for row in index['images'])
        assert index['linked_response']['sha256'] == entries[REL+'/run_001/linked_response.json']['sha256']
    closure = read(stage/'author/execution_documentation_receipt.json')
    assert closure['source_baseline_commit'] == BASE and closure['actual_execution_closed'] is True
    assert closure['actual_execution_status'] == outer['status'] and {row['path'] for row in closure['front_history']} == FRONTS
    for row in closure['front_history']:
        prior = git(root, 'show', BASE+':'+row['path'])
        current = raw(root/row['path'])
        assert sha256(prior).hexdigest() == row['old_sha256'] and current.count(prior) == 1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == prior
        assert sha256(current).hexdigest() == row['new_sha256'] == entries[row['path']]['sha256']
    review = read(root/FINAL_JSON)
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    assert review['authorized'] is review['executed'] is review['execution_closed'] is True
    assert review['execution_status'] == outer['status'] and review['protocol_SHA256'] == PROTOCOL_SHA
    assert FINAL_JSON not in review['reviewed_repository_SHA256'] and FINAL_MD in review['reviewed_repository_SHA256']
    assert allowed-{FINAL_JSON} <= review['reviewed_repository_SHA256'].keys()
    assert all(name in allowed and entries[name]['sha256'] == pin for name, pin in review['reviewed_repository_SHA256'].items())
    return outer['status']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preview', 'finalize', 'verify'))
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--restore', type=Path, default=Path('D:/hf-restore-20260930'))
    args = parser.parse_args()
    root, restore, here = args.repo.resolve(), args.restore.resolve(), Path(__file__).resolve().parent
    assert not here.is_relative_to(root), 'Run external publisher; formal copy is recovery source only'
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']: row for row in previous['files']}
    assert sha256(oldraw).hexdigest() == MANIFEST_SHA and len(old) == len(previous['files']) == 20573
    assert sum(row['bytes'] for row in old.values()) == 11310175674
    assert previous['science_version'] == '0.5.0' and previous['science_baseline_commit'] == SCIENCE_BASE
    actual = {path.relative_to(root).as_posix() for path in (root/REL).rglob('*') if path.is_file()}
    assert {name for name in old if name.startswith(REL+'/')} <= actual
    default_changed = sha(root/DEFAULT) != old[DEFAULT]['sha256']
    allowed = (actual-old.keys()) | FRONTS | ({DEFAULT} if default_changed else set())
    assert allowed & old.keys() == FRONTS | ({DEFAULT} if default_changed else set())
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
        assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) == allowed == (paths-old.keys()) | FRONTS | ({DEFAULT} if default_changed else set())
        delta = [identity(root, name) for name in sorted(allowed)]
        entries = dict(old, **{row['path']: row for row in delta})
        assert entries.keys() == paths
        status = check_closed(root, entries, old, allowed)
        manifest = dict(previous, created_utc=datetime.now(timezone.utc).isoformat(), previous_delivery_commit=BASE,
            storage_stage='saved_lf_selected_reference_link_'+status+'_closed_001', files=[entries[name] for name in sorted(paths)])
        output_raw = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        value = dict(status='incremental_execution_delivery_pass', previous_delivery_commit=BASE,
            manifest_sha256=sha256(output_raw).hexdigest(), ordinary_manifest_files=len(entries),
            ordinary_manifest_bytes=sum(row['bytes'] for row in entries.values()), delta_files=delta,
            delta_bytes=sum(row['bytes'] for row in delta), unchanged_manifest_entries_inherited=len(old)-(3 if default_changed else 2),
            protocol_sha256=PROTOCOL_SHA, executed_card='L-LINK1', authorized=True, executed=True, execution_closed=True, execution_status=status,
            immutable_input_bindings=65, old_media_identities_from_original_producer_stat_only=5,
            scientific_or_media_bytes_headers_hash_decode_by_publisher=0, new_HF_API_HP_solver_tests_pixels_or_plots=0,
            default_changes=int(default_changed), default_source_SHA256=entries[DEFAULT]['sha256'],
            new_full_source_scan=False, full25_LF_path_reference_qualified=False, whole_HF5_complete=False)
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
            assert ({path.relative_to(tree).as_posix() for path in (tree/REL).rglob('*') if path.is_file()}-old.keys()) | FRONTS | ({DEFAULT} if default_changed else set()) == allowed
            assert check_closed(tree, entries, old, allowed) == source['execution_status']
        assert current['science_version'] == previous['science_version'] and current['science_baseline_commit'] == SCIENCE_BASE
        value = dict(source, status='published_and_incrementally_restored_pass', created_utc=datetime.now(timezone.utc).isoformat(),
            published_commit=commit, branch='main', origin=ORIGIN, source_and_restore_clean=True,
            remote_main_confirmed_equal=True, restore_root=str(restore), delta_files_restored=len(allowed),
            old_media_restore_check='stat plus original closed producer identity; no media rehash', new_full_source_or_restore_scan=False)
        value.pop('delta_files')
        write_new(here/'execution_publication_receipt.json', value)
    print(json.dumps({key: item for key, item in value.items() if key != 'delta_files'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
