"""Build an external closed M-UNLOAD2 config from ordinary records and science stat."""
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import argparse
import ast
import json

from deliver_execution import BASE, REL, MANIFEST, FRONTS, ORIGIN, ORDINARY, SCIENCE
from deliver_execution import git, names, read, sha, optional_json, declared_assets, write_new

FINAL_JSON = REL+'/author/final_publication_review.json'
FINAL_MD = REL+'/author/final_publication_review.md'
CONFIG = REL+'/author/execution_delivery_config.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent/'execution_delivery_config.json')
    parser.add_argument('--terminal-review', type=Path, default=Path(REL)/'author/independent_terminal_review.json')
    parser.add_argument('--documentation-receipt', type=Path, default=Path(REL)/'author/execution_documentation_receipt.json')
    args = parser.parse_args()
    root, here = args.repo.resolve(), Path(__file__).resolve().parent
    output = args.output.resolve()
    assert not output.is_relative_to(root), 'Only an external config is written by this tool'
    assert output.suffix == '.json' and not output.exists()
    assert git(root, 'rev-parse', 'HEAD').decode().strip() == BASE
    assert git(root, 'branch', '--show-current').decode().strip() == 'main'
    assert git(root, 'remote', 'get-url', 'origin').decode().strip() == ORIGIN
    assert git(root, 'remote', 'get-url', '--push', 'origin').decode().strip() == ORIGIN
    oldraw = git(root, 'show', BASE+':'+MANIFEST)
    previous = json.loads(oldraw)
    old = {row['path']: row for row in previous['files']}
    assert len(old) == 19799 and previous['science_version'] == '0.5.0'
    assert (root/MANIFEST).read_bytes() == oldraw
    stage = root/REL
    protocol = read(stage/'protocol.json')
    proof = read(stage/'author/source_publication_receipt.json')
    assert proof['published_commit'] == BASE and proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert proof['ordinary_manifest_files'] == len(old) and proof['ordinary_manifest_bytes'] == sum(row['bytes'] for row in old.values())
    assert proof['prepared_card'] == protocol['card'] == 'M-UNLOAD2'
    assert proof['prepared'] is protocol['prepared'] is True
    assert proof['authorized'] is proof['executed'] is protocol['authorized'] is protocol['executed'] is False
    assert len(protocol['bindings']) == 81
    for name, pin in protocol['bindings'].items():
        assert old[name]['sha256'] == pin
        if name in protocol['inherited_NPZ_bindings']:
            assert (root/name).stat().st_size == old[name]['bytes']
        else:
            assert sha(root/name) == pin
    outer_path = stage/'production_launch.json'
    outer = read(outer_path)
    assert outer['completed_utc'] and outer['exit_code'] is not None and outer['invocations'] == 1
    assert outer['status'] in ('pass', 'not_pass') and outer['all_bindings_unchanged'] in (True,None)
    run = stage/'run_001'
    helper_path = run/'execution_receipt.json'
    helper = optional_json(helper_path)
    declared = declared_assets(root,run,helper)
    if outer['status'] == 'pass':
        assert helper is not None and helper['status'] == 'pass'
        assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
    actual = {path.relative_to(root).as_posix() for path in stage.rglob('*') if path.is_file()}
    new = actual-old.keys()
    binary = {name for name in new if Path(name).suffix.lower() in SCIENCE}
    assert binary == declared.keys(), 'Missing/conflicting producer SHA blocks delivery; do not open science bytes'
    assert all(Path(name).suffix.lower() in ORDINARY | SCIENCE for name in new)
    assert names(git(root, 'diff', '--name-only', '-z', BASE)) == FRONTS
    assert names(git(root, 'diff', '--cached', '--name-only', '-z', BASE)) <= FRONTS
    untracked = names(git(root, 'ls-files', '--others', '--exclude-standard', '-z'))
    assert all(name.startswith(REL+'/') for name in untracked)
    assert not any((root/name).exists() for name in (CONFIG, FINAL_JSON, FINAL_MD))
    for name, external in ((REL+'/author/deliver_execution.py', here/'deliver_execution.py'),
                           (REL+'/author/write_actual_records.py', here/'write_actual_records.py')):
        assert name in new and sha(root/name) == sha(external)
        ast.parse((root/name).read_text(encoding='utf-8'))
    closure_file = (root/args.documentation_receipt).resolve(); closure_file.relative_to(stage)
    closure = read(closure_file)
    assert closure['source_baseline_commit'] == BASE and closure['actual_execution_closed'] is True
    assert closure['actual_execution_status'] == outer['status']
    history = closure['front_history']
    assert {row['path'] for row in history} == FRONTS
    for row in history:
        original = git(root, 'show', BASE+':'+row['path'])
        current = (root/row['path']).read_bytes()
        assert sha256(original).hexdigest() == row['old_sha256']
        assert current.count(original) == 1 and current[row['history_start_byte']:row['history_end_byte_exclusive']] == original
        assert sha256(current).hexdigest() == row['new_sha256']
    review_file = (root/args.terminal_review).resolve(); review_file.relative_to(stage)
    review = read(review_file)
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    allowed = sorted(new | FRONTS | {CONFIG, FINAL_JSON, FINAL_MD})
    value = dict(schema='closed-saved-default-unload-delivery-config-1.0', created_utc=datetime.now(timezone.utc).isoformat(),
        card='M-UNLOAD2', source_commit=BASE, protocol_sha256=sha(stage/'protocol.json'),
        authorized=True, executed=True, execution_closed=True, execution_status=outer['status'],
        outer_sha256=sha(outer_path), helper_sha256=sha(helper_path) if helper_path.exists() else None,
        result_sha256=sha(root/protocol['candidate_directory']/'result.json') if (root/protocol['candidate_directory']/'result.json').exists() else None,
        response_sha256=sha(root/protocol['candidate_directory']/'response.json') if (root/protocol['candidate_directory']/'response.json').exists() else None,
        view_sha256=sha(root/protocol['view_directory']/'view.json') if (root/protocol['view_directory']/'view.json').exists() else None,
        declared_binary_identities=declared,
        binary_identity_sources={name:dict(producer_record=helper_path.relative_to(root).as_posix(),producer_member='/outputs/'+name) for name in declared},
        output_identity_seal=(helper or {}).get('output_identity_seal'),
        binary_byte_reads_or_hashes_by_config_builder=0, binary_scope='True closed producer SHA plus present file stat; no binary content verification',
        allowed_delta_paths=allowed, final_review_path=FINAL_JSON, final_review_markdown_path=FINAL_MD,
        front_history=history, source_manifest_sha256=sha256(oldraw).hexdigest(), inherited_manifest_entries=len(old),
        bindings=protocol['bindings'], inherited_NPZ_bindings=protocol['inherited_NPZ_bindings'],
        unchanged_bindings_basis='81 sole-launch identities; final actual status retained, ordinary metadata checked here, six old NPZ manifest+stat only',
        sole_launcher_all_bindings_unchanged=outer['all_bindings_unchanged'],
        source_publication_receipt_sha256=sha(stage/'author/source_publication_receipt.json'),
        independent_terminal_review_path=review_file.relative_to(root).as_posix(), independent_terminal_review_sha256=sha(review_file),
        execution_documentation_receipt_path=closure_file.relative_to(root).as_posix(), execution_documentation_receipt_sha256=sha(closure_file),
        configuration_builder_source_sha256=sha(Path(__file__).resolve()),
        current_segment_new_HP_reference=False, full_original_path_reference_pass=False, full_extended_path_reference_pass=False,
        new_HF_API_HP_solver_tests_plots=0, default_changes=0)
    write_new(output, value)
    print(json.dumps(dict(status='external_closed_execution_config_frozen', config_path=str(output),
        config_sha256=sha(output), allowed_delta_files=len(allowed), inherited_scientific_delta=len(declared),
        scientific_binary_byte_reads=0, formal_writes=0, publisher_execution=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
