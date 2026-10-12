"""Freeze M-ALINK1 source/JSON pins; inherit media identity without reading it."""
from datetime import datetime, timezone
from hashlib import sha256
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/alpha_link_001'
BASE = '84c67e48ba61548a1c15d2c049870678ef58f573'
PROOF = Path('D:/hf-native-workpiece-api-author-20261012/MAREF1_execution_review_001/execution_publication_receipt.json')
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASE
    seed = read(HERE / 'input_contract_seed.json')
    old = {row['path']: row for row in read(ROOT / 'handoff/repository_manifest.json')['files']}
    media = seed['inherited_media_input_bindings']
    assert len(media) == 4 and set(media) == set(seed['media_files'])
    for name, pin in seed['input_bindings'].items():
        assert Path(name).suffix.lower() in {'.json', '.py', '.png', '.gif'}
        assert old[name]['sha256'] == pin
        if name in media:
            assert (ROOT / name).stat().st_size == old[name]['bytes'] and media[name] == pin
        else:
            assert sha(ROOT / name) == pin
    proof = read(PROOF)
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['executed_card'] == 'M-AREF1' and proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    assert proof['manifest_sha256'] == sha(ROOT / 'handoff/repository_manifest.json')
    for name in ('execute_alpha_link.py', 'launch_link.py', 'prepare_formal_stage.py', 'deliver_preparation.py'):
        ast.parse((HERE / name).read_text(encoding='utf-8'))
    keys = ('result_file', 'model_file', 'original_response_file', 'reference_file', 'raw_view_file',
        'view_case_summary_file', 'parent_result_file', 'reference_launch_file', 'reference_lifecycle_file',
        'selected_state_identity', 'media_files', 'phases', 'sampled_RSS_bytes')
    value = {key: seed[key] for key in keys}
    bindings = dict(seed['input_bindings'])
    for name in ('execute_alpha_link.py', 'launch_link.py', 'M-ALINK1_CARD.md'):
        bindings[REL + '/' + name] = sha(HERE / name)
    prior = REL + '/author/previous_publication_receipt.json'
    bindings[prior] = sha(PROOF)
    value.update(schema_version='alpha-saved-segment-linked-delivery-card-1.0', card='M-ALINK1',
        prepared=True, authorized=False, executed=False, prepared_utc=datetime.now(timezone.utc).isoformat(),
        source_baseline_commit=BASE, science_version='0.5.0', expected_accepted_states=2,
        targets_mm=[1.2, 1.15], original_target_indices=[13, 14],
        output_directory=REL + '/run_001', previous_publication_file=prior,
        bindings=dict(sorted(bindings.items())), inherited_media_bindings=media,
        expected_linked_response=seed['expected_linked_response'],
        api_import_closure_files=seed['api_import_closure_files'],
        api_JSON_read_files=seed['api_JSON_read_files'], reference_source_hash_files=seed['reference_source_hash_files'],
        expected_calls=dict(saved_summary_started=1, saved_summary_completed=1, response_writes=1, index_writes=1),
        new_NPZ_NPY_gzip_CSV_reads_HF_mechanics_tests_HP_plots=0,
        future_media_reads='Existing three PNG and one GIF raw identity only; wrappers/API can repeat hashes, no decode/render',
        no_retry_repair_rerun_extension_force=True,
        prerequisite='New direct human card approval tied to published/restored source; M-AREF1 is closed')
    assert len(bindings) == 30
    with (HERE / 'protocol.json').open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(status='prepared_not_authorized_not_executed', bindings=30,
        protocol_sha256=sha(HERE / 'protocol.json'), media_bytes_read=0, array_or_gzip_reads=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
