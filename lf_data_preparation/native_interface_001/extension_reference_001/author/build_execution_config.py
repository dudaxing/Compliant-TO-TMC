"""Build an external closed M-EREF1 config from ordinary records and science stat."""
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
    assert len(old) == 19641 and previous['science_version'] == '0.5.0'
    assert (root/MANIFEST).read_bytes() == oldraw
    stage = root/REL
    protocol = read(stage/'protocol.json')
    proof = read(stage/'author/source_publication_receipt.json')
    assert proof['published_commit'] == BASE and proof['manifest_sha256'] == sha256(oldraw).hexdigest()
    assert proof['ordinary_manifest_files'] == len(old) and proof['ordinary_manifest_bytes'] == sum(row['bytes'] for row in old.values())
    assert proof['prepared_card'] == protocol['card'] == 'M-EREF1'
    assert proof['prepared'] is protocol['prepared'] is True
    assert proof['authorized'] is proof['executed'] is protocol['authorized'] is protocol['executed'] is False
    assert len(protocol['bindings']) == 50
    for name, pin in protocol['bindings'].items():
        assert old[name]['sha256'] == pin
        if name in protocol['inherited_NPZ_bindings']:
            assert (root/name).stat().st_size == old[name]['bytes']
        else:
            assert sha(root/name) == pin
    outer_path = stage/'reference_launch.json'
    outer = read(outer_path)
    assert outer['completed_utc'] and outer['exit_code'] is not None and outer['invocations'] == 1
    assert outer['status'] in ('pass', 'not_pass') and outer['all_bindings_unchanged'] is True
    reference = (root/protocol['reference_output']).resolve()
    reference.relative_to(stage)
    raw_summaries = sorted(reference.glob('accepted_*/summary.json'))
    top = reference/'summary.json'
    producer_records = raw_summaries+([top] if top.exists() else [])
    producer = declared_assets(root, reference, producer_records)
    declared = {name: row['identity'] for name, row in producer.items()}
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
    closure = read(stage/'author/execution_documentation_receipt.json')
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
    review = read(stage/'author/independent_terminal_review.json')
    assert review['status'].startswith('pass') and review['blocking_findings'] == []
    allowed = sorted(new | FRONTS | {CONFIG, FINAL_JSON, FINAL_MD})
    value = dict(schema='closed-extension-reference-delivery-config-1.0', created_utc=datetime.now(timezone.utc).isoformat(),
        card='M-EREF1', source_commit=BASE, protocol_sha256=sha(stage/'protocol.json'),
        authorized=True, executed=True, execution_closed=True, execution_status=outer['status'],
        outer_sha256=sha(outer_path),
        summary_sha256=sha(top) if top.exists() else None,
        lifecycle_sha256=sha(reference/'lifecycle.json') if (reference/'lifecycle.json').exists() else None,
        producer_summary_paths=[path.relative_to(root).as_posix() for path in producer_records],
        declared_binary_identities=declared, binary_identity_sources={name:{key:row[key] for key in ('producer_record','producer_member')} for name,row in producer.items()},
        binary_byte_reads_or_hashes_by_config_builder=0, binary_scope='True closed producer SHA plus present file stat; no binary content verification',
        allowed_delta_paths=allowed, final_review_path=FINAL_JSON, final_review_markdown_path=FINAL_MD,
        front_history=history, source_manifest_sha256=sha256(oldraw).hexdigest(), inherited_manifest_entries=len(old),
        bindings=protocol['bindings'], inherited_NPZ_bindings=protocol['inherited_NPZ_bindings'],
        unchanged_bindings_basis='50 actual sole-launch initial/final identities; ordinary metadata checked here, six old NPZ stat only',
        source_publication_receipt_sha256=sha(stage/'author/source_publication_receipt.json'),
        independent_terminal_review_sha256=sha(stage/'author/independent_terminal_review.json'),
        execution_documentation_receipt_sha256=sha(stage/'author/execution_documentation_receipt.json'),
        configuration_builder_source_sha256=sha(Path(__file__).resolve()),
        full_child_path_reference_pass=False, full_original_path_reference_pass=False, full_extended_path_reference_pass=False,
        new_HF_API_HP_solver_tests_plots=0, default_changes=0)
    write_new(output, value)
    print(json.dumps(dict(status='external_closed_execution_config_frozen', config_path=str(output),
        config_sha256=sha(output), allowed_delta_files=len(allowed), inherited_scientific_delta=len(declared),
        scientific_binary_byte_reads=0, formal_writes=0, publisher_execution=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
