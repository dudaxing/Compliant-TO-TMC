"""Source/JSON-only peer; does not import or execute the candidate mock."""
import ast
import datetime
import hashlib
import json
from pathlib import Path

root = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
author = Path(__file__).resolve().parent
expected = {
    'fixed_square_manifest.json': '01e271695b5aaf8e7e84597eb04da84ecf0dd96584055f5e12885be9bfdbba87',
    'check_fixed_square_mock.py': 'e020a48c1c599f9eecec83754807fb8918453c683719a62688c149fd17cb7663',
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(author/name) == pin for name, pin in expected.items())
ast.parse((author/'check_fixed_square_mock.py').read_text(encoding='utf-8'))
manifest = json.loads((author/'fixed_square_manifest.json').read_bytes())
case = manifest['cases'][0]
inventory_file = root/'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/run_001/input_inventory.json'
inventory = json.loads(inventory_file.read_bytes())
task = json.loads((root/case['task']).read_bytes())
geometry = json.loads((root/case['geometry']).read_bytes())
assert len(manifest['cases']) == 1 and manifest['schema_version'] == 'hf-native-batch-manifest-1.0'
assert manifest['options']['settings'] == inventory['settings'] and len(inventory['settings']) == 10
assert set(manifest['options']) == {'settings', 'response_mode', 'tangent_mode', 'initial_guess'}
assert manifest['options']['response_mode'] == inventory['response_mode'] == 'mechanical'
assert manifest['options']['tangent_mode'] == inventory['case']['tangent_mode'] == 'chunk256'
assert manifest['options']['initial_guess'] == inventory['initial_guess'] == 'port_projection'
assert case['task'] == inventory['case']['task_file'] and case['geometry'] == inventory['case']['geometry_file']
assert sha(root/case['task']) == inventory['case']['task_file_sha256']
assert sha(root/case['geometry']) == inventory['case']['geometry_file_sha256']
assert task['geometry'] == {k: geometry[k] for k in ('geometry_id', 'descriptor_sha256')}
assert task['path']['targets_mm'] == inventory['case']['targets_mm'] and len(task['path']['targets_mm']) == 24
assert case['output'] == 'lf_data_preparation/native_interface_001/workpiece_forward_001/run_001/fixed_square'
fixture_file = root/'lf_data_preparation/native_interface_001/api_validation_001/run_001/saved_right4col_response.json'
fixture = json.loads(fixture_file.read_bytes())
assert fixture['target_response']['d_mm'] == 1.2 and fixture['requested_endpoint_response']['d_mm'] == 0.
report = {
    'schema_version': 'fixed-workpiece-api-job-mock-static-peer-1.0',
    'status': 'pass_static_only', 'blocking_findings': [],
    'reviewed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_sha256': expected,
    'input_sha256': {case['task']: sha(root/case['task']), case['geometry']: sha(root/case['geometry']),
        inventory_file.relative_to(root).as_posix(): sha(inventory_file), fixture_file.relative_to(root).as_posix(): sha(fixture_file)},
    'findings': [
        'One-case manifest binds the unchanged original 4mm ordinary geometry and task; all ten controller settings match the closed original inventory exactly.',
        'Existing batch settings mutual-exclusion is respected: top-level time/minimum_increment are absent, so the actual settings use 4500s and 0.00625mm while API default limits are not mixed.',
        'Mock takes required --manifest with explicit repo path resolution. Only an external test copy changes the output directory; task, geometry, label and all options remain exact.',
        'Actual batch calls actual evaluate_native via wraps; only solve/cache writer/summary are mocked, with exact one-call assertions for all three and the actual API call. The actual JSON response writer remains used.',
        'Old target/endpoint/body values are explicit fixtures. Fixture flags, reference, views and mechanical counters are reset; receipt records actual accepted states zero separately from old fixture states 24.',
        'Elapsed includes imports and through-checks work, excludes final receipt/stdout as stated. This static review is not a mock runtime PASS or scientific qualification.'
    ],
    'future_W_API1_worker_review': 'Separate pending author revision; not approved by this manifest/mock review.',
    'activities': {'candidate_imports': 0, 'mock_runs': 0, 'HF_imports': 0, 'NPZ_loads': 0, 'model': 0, 'F': 0, 'T': 0, 'solver': 0, 'HP': 0, 'observations': 0, 'render': 0, 'formal_writes': 0}
}
output = author/'api_job_mock_peer_review.json'
output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'path': str(output), 'sha256': sha(output)}, ensure_ascii=False))
