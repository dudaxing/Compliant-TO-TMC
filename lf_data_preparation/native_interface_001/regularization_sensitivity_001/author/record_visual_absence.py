"""Record the genuine absence of candidate views from ordinary metadata only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/regularization_sensitivity_001'
EXTERNAL = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_bytes())

stage = ROOT / REL
outer = read(stage / 'production_launch.json')
helper = read(stage / 'run_001/execution_receipt.json')
result = read(stage / 'run_001/alpha_half/result.json')
assert outer['status'] == helper['status'] == 'not_pass'
assert outer['completed_utc'] and outer['stop_reason'] is None
assert helper['counts']['view_child_started'] == helper['counts']['view_child_completed'] == 0
assert result['failure']['code'] == 'time_limit'
assert result['accepted_states'] == 14
view = stage / 'run_001/view'
assert not view.exists()
expected = ['comparison.png', 'distances_forces.png', 'peak_fields.png',
            'alpha_response_comparison.png', 'alpha_half/actual_states.gif']
assert all(not (view / name).exists() for name in expected)
metadata = ['production_launch.json', 'run_001/execution_receipt.json',
            'run_001/alpha_half/result.json']
report = dict(
    schema_version='M-ALPHA1-visual-availability-review-1.0',
    status='not_available_candidate_views_not_started',
    execution_status='not_pass', created_utc=datetime.now(timezone.utc).isoformat(),
    source_commit='64a19f7d990d294d09f16145eae946e0edfa1580',
    protocol_sha256=outer['protocol_sha256'],
    reviewed_repository_JSON_SHA256={REL+'/'+name: sha256((stage/name).read_bytes()).hexdigest() for name in metadata},
    accepted_states=14, loading_peak_reached=True, unload_endpoint_reached=False,
    view_child_started=0, view_child_completed=0, candidate_view_directory_exists=False,
    expected_candidate_outputs={REL+'/run_001/view/'+name: 'not_generated' for name in expected},
    actual_candidate_PNG_count=0, actual_candidate_GIF_count=0,
    candidate_pixel_review='not_available_no_candidate_image',
    reason='The original controller returned time_limit before the 15-target path completed. The unchanged worker raised Batch terminal non-success before starting the saved-state viewer. The execution window is closed.',
    old_visuals='Existing baseline images are historical evidence only and were not substituted for new alpha views.',
    next_visual_scope='Review the 14 saved accepted states in a separately prepared and authorized saved-state view step; do not rerun the nonlinear path for display.',
    actions=dict(new_candidate_runs=0, new_NPZ_decodes=0, new_HF_calls=0, new_scientific_sums_or_differences=0, new_renders=0),
    qualification=dict(new_stability=False, new_pressure=False, new_effective_clamp=False, new_HP=False, whole_HF5=False))
target = EXTERNAL / 'visual_results_review.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
print(json.dumps(dict(status=report['status'], execution_status=report['execution_status'],
                     sha256=sha256(target.read_bytes()).hexdigest(), actual_candidate_images=0)))
