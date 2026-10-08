"""Saved JSON/raw-byte closure only; never reruns mock or science."""
from pathlib import Path
import datetime
import hashlib
import json

root = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
author = Path(__file__).resolve().parent
stage = root/'lf_data_preparation/native_interface_001/workpiece_api_preparation_001'
validation = stage/'validation_001'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
manifest_file = root/'hf_repo/configs/native/fixed_square_cycle.json'
mock_file = stage/'author/check_fixed_square_mock.py'
assert sha(manifest_file) == '01e271695b5aaf8e7e84597eb04da84ecf0dd96584055f5e12885be9bfdbba87'
assert sha(mock_file) == 'e020a48c1c599f9eecec83754807fb8918453c683719a62688c149fd17cb7663'
manifest, tested = read(manifest_file), read(validation/'test_manifest.json')
assert tested['options'] == manifest['options']
assert {k: v for k, v in tested['cases'][0].items() if k != 'output'} == {k: v for k, v in manifest['cases'][0].items() if k != 'output'}
response, index, receipt = [read(validation/p) for p in ('fixed_square/response.json', 'batch/index.json', 'mock_check_receipt.json')]
assert receipt['status'] == 'pass_mock_transport_only' and receipt['new_qualification'] is False
assert all(receipt[k] == 1 for k in ('real_batch_calls', 'real_API_calls', 'mocked_solve_calls', 'mocked_save_calls', 'mocked_summary_calls'))
assert all(receipt[k] == 0 for k in ('scientific_solver_calls', 'F', 'T', 'HP', 'NPZ_loads', 'actual_accepted_states'))
assert receipt['fixture_accepted_states'] == 24 and receipt['through_helper_elapsed_seconds'] == 1.3861648000311106
assert receipt['source_manifest_sha256'] == sha(manifest_file)
fixture_file = root/'lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_right4col_response.json'
fixture = read(fixture_file)
assert sha(fixture_file) == receipt['fixture_response_sha256'] == response['mock_fixture']['sha256']
assert response['mock_response'] is response['fixture_only'] is True
assert response['mock_fixture']['new_scientific_result'] is False
assert index['status'] == 'success' and len(index['cases']) == 1
assert index['HF5_qualified'] is index['ranking_qualified'] is False
entry = index['cases'][0]
assert entry['response']['sha256'] == sha(validation/'fixed_square/response.json')
assert index['manifest']['sha256'] == sha(validation/'test_manifest.json')
assert entry['status'] == 'success'
for key in ('target_response', 'requested_endpoint_response', 'maximum_loading_stroke', 'last_accepted'):
    assert response[key] == entry[key] == fixture[key]
    assert response[key]['workpiece'] == fixture[key]['workpiece']
assert response['target_response']['d_mm'] == 1.2 and response['requested_endpoint_response']['d_mm'] == 0.
assert response['invocation']['settings'] == receipt['observed']['settings'] == manifest['options']['settings']
assert response['invocation']['targets_mm'] == receipt['observed']['targets'] == fixture['path']['requested_targets_mm']
assert all(v is False for v in response['producer_flags'].values())
assert all(v == 0 for v in response['call_counts'].values())
assert response['independent_reference'] == entry['independent_reference']
assert response['independent_reference']['status'] == 'not_provided'
assert all(v is False for k, v in response['independent_reference'].items() if k.endswith('_pass') or k.endswith('_qualified'))
assert response['views'] == entry['views'] and response['views']['status'] == 'not_provided'
assert response['views']['manifest'] is None and not response['views']['links']
preimages = read(stage/'source_preimages.json')
assert len(preimages['bindings']) == preimages['current_HF_source_files'] == 28
assert all(sha(root/p) == pin for p, pin in preimages['bindings'].items())
assert not (root/'lf_data_preparation/native_interface_001/workpiece_forward_001').exists()
files = [manifest_file, mock_file, stage/'source_preimages.json', fixture_file,
    *[validation/p for p in ('test_manifest.json', 'fixed_square/response.json', 'batch/index.json', 'mock_check_receipt.json')]]
report = {
    'schema_version': 'fixed-workpiece-api-mock-saved-closure-1.0',
    'status': 'pass_saved_only', 'blocking_findings': [],
    'reviewed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'file_sha256': {p.relative_to(root).as_posix(): sha(p) for p in files},
    'actual_receipt': receipt,
    'checks': {'archived_four_JSON_identities_match': True, 'all_28_product_sources_unchanged': True,
        'original_body_target_and_endpoint_fields_copied_exactly': True, 'all_ten_settings_passed_exactly': True,
        'reference_view_HF5_ranking_qualification_not_borrowed': True, 'science_stage_not_created': True},
    'qualification_scope': 'Actual mock transport only: real batch/API entry, mocked solver/cache writer/formatter. Zero new scientific accepted states. All body values are explicitly old fixtures, not a new forward equilibrium.',
    'zero_science_basis': 'Saved receipt plus pinned three mock delegates and previously reviewed source call path; not a new dynamic mechanical profiling run.',
    'operator_exit': {'reported_by_parent': 0, 'standalone_stdout_exit_receipt_archived_here': False},
    'activities': {'mock_reruns': 0, 'HF_imports': 0, 'NPZ_loads': 0, 'model': 0, 'F': 0, 'T': 0, 'solver': 0, 'HP': 0, 'observations': 0, 'render': 0, 'formal_writes': 0}
}
output = author/'mock_saved_closure_review.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'path': str(output), 'sha256': sha(output)}, ensure_ascii=False))
