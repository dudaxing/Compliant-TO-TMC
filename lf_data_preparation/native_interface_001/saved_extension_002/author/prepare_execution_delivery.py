"""Save root-supplied closed execution prose and configure its exact metadata delta."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

from deliver_execution import BASE, REL, FRONTS, ORDINARY, DECLARED, KINDS, read, sha, git, names, read_helper, write_new


def copy_ordinary(source, destination):
    assert source.suffix.lower() in ORDINARY and destination.suffix.lower() in ORDINARY
    raw = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        assert destination.read_bytes() == raw, 'Existing ordinary evidence must retain original bytes'
    else:
        with destination.open('xb') as output:
            output.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True, help='Root-supplied actual closed prose/file mapping')
    args = parser.parse_args()
    root = args.repo.resolve()
    payload_file = args.input.resolve()
    payload = read(payload_file)
    assert payload['source_commit'] == BASE and payload['execution_closed'] is True
    assert payload['execution_status'] in ('pass', 'not_pass')
    assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE
    stage = root/REL
    protocol_file, launch_file, helper_file = stage/'protocol.json', stage/'production_launch.json', stage/'run_001/execution_receipt.json'
    protocol, launch = read(protocol_file), read(launch_file)
    helper, condition = read_helper(helper_file)
    assert launch['completed_utc'] and launch['exit_code'] is not None and launch['invocations'] == 1
    assert launch['status'] == payload['execution_status'] and launch['protocol_sha256'] == sha(protocol_file)
    assert protocol['card'] == 'M-EXTEND2' and len(protocol['bindings']) == 148
    if payload['execution_status'] == 'pass':
        assert helper is not None and helper['status'] == 'pass' and launch['exit_code'] == 0
    terminal_name = payload['terminal_review_name']
    author_files = payload['author_files']
    assert terminal_name in author_files and Path(terminal_name).name == terminal_name
    terminal = read(Path(author_files[terminal_name]))
    assert terminal['status'].startswith('pass') and terminal['execution_status'] == launch['status'] and terminal['execution_closed'] is True
    final_json, final_md = REL+'/author/execution_delivery_final_review.json', REL+'/author/execution_delivery_final_review.md'
    config_path = stage/'author/execution_delivery_config.json'
    assert not config_path.exists() and not (root/final_json).exists() and not (root/final_md).exists()
    tracked = names(git(root, 'ls-tree', '-r', '--name-only', '-z', BASE))
    declared = {}
    for path in stage.rglob('*'):
        if path.is_file() and path.suffix.lower() in DECLARED:
            name = path.relative_to(root).as_posix()
            if name not in tracked:
                assert helper is not None and name in helper.get('outputs', {}), 'Unrecorded binary output: report actual gap; do not byte-read or invent identity'
                declared[name] = dict(path=name, bytes=path.stat().st_size, sha256=helper['outputs'][name])
    defaults = {row['target']: sha(root/row['target']) for row in protocol['installation']}
    assert defaults == launch['actual_default_SHA256']
    changed = {row['target'] for row in protocol['installation'] if defaults[row['target']] != row['old_sha256']}
    counts = helper.get('counts') if helper is not None else None
    if counts is not None:
        assert set(counts) == {kind+suffix for kind in KINDS for suffix in ('_started', '_completed')}
    for name, source in author_files.items():
        assert Path(name).name == name and name not in ('execution_delivery_config.json', 'execution_delivery_final_review.json', 'execution_delivery_final_review.md')
        copy_ordinary(Path(source), stage/'author'/name)
    copy_ordinary(payload_file, stage/'author/execution_closure_input.json')
    copy_ordinary(Path(payload['results_file']), stage/'RESULTS.md')
    copy_ordinary(Path(payload['next_file']), stage/'EXECUTION_NEXT_STEP_REVIEW.md')
    assert Path(payload['front_file']).suffix.lower() == '.md'
    prefix = Path(payload['front_file']).read_bytes()
    assert prefix
    copy_ordinary(Path(payload['front_file']), stage/'author/execution_front_prefix.md')
    history = []
    for name in sorted(FRONTS):
        previous = git(root, 'show', BASE+':'+name)
        assert (root/name).read_bytes() == previous
        current = prefix+previous
        assert current.count(previous) == 1
        (root/name).write_bytes(current)
        history.append(dict(path=name, old_sha256=sha256(previous).hexdigest(), new_sha256=sha(root/name),
                            history_start_byte=len(prefix), history_end_byte_exclusive=len(current)))
    paths = {path.relative_to(root).as_posix() for path in stage.rglob('*') if path.is_file()}
    new_paths = paths-tracked
    assert all(Path(name).suffix.lower() in ORDINARY | DECLARED for name in new_paths)
    assert set(declared) == {name for name in new_paths if Path(name).suffix.lower() in DECLARED}
    allowed = new_paths | FRONTS | changed | {config_path.relative_to(root).as_posix(), final_json, final_md}
    config = dict(schema_version='MEXTEND2-closed-incremental-delivery-config-1.0', source_commit=BASE,
                  card='M-EXTEND2', protocol_sha256=sha(protocol_file), execution_status=launch['status'], execution_closed=True,
                  outer_sha256=sha(launch_file), helper_sha256=sha(helper_file) if helper_file.exists() else None,
                  helper_condition=condition, helper_counts=counts, actual_default_SHA256=defaults,
                  allowed_delta_paths=sorted(allowed), declared_output_identities=declared, front_history=history,
                  terminal_review_path=REL+'/author/'+terminal_name, final_review_path=final_json,
                  binary_identity_scope='Closed sole helper.outputs SHA + file stat, no postclosure binary/CSV/media byte read or rehash',
                  actual_partial_installation_preserved=True, external_runtime_not_deleted=True,
                  published=False, new_science_tests_views_or_retry=False)
    write_new(config_path, config)
    print(json.dumps(dict(status='closed_actual_prose_and_incremental_config_saved', execution_status=launch['status'],
                          allowed_delta_files=len(allowed), actual_changed_defaults=len(changed), binary_declared_stat_only=len(declared),
                          config_sha256=sha(config_path), new_science_tests_views_or_retry=False)))


if __name__ == '__main__':
    main()
