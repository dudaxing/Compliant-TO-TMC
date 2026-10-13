"""Record root's already observed terminal and three one-time PNG inspections."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/saved_extension_004'
stage = ROOT / REL
outer_file = stage / 'production_launch.json'
helper_file = stage / 'run_001/execution_receipt.json'
outer_raw, helper_raw = outer_file.read_bytes(), helper_file.read_bytes()
outer, helper = json.loads(outer_raw), json.loads(helper_raw)
assert outer['status'] == helper['status'] == 'pass' and outer['exit_code'] == 0
assert outer['completed_utc'] and outer['invocations'] == 1
assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'
confirmation = dict(card='M-UNLOAD2', source_baseline_commit='21676e9bbae80505cfe719f0811fc77bc66fd55b',
    recorded_utc=datetime.now(timezone.utc).isoformat(), unified_exec_session_id=96386,
    root_observed_same_session_terminal=True, tool_terminal_exit_code=0,
    execution_status='pass', execution_closed=True, outer_sha256=sha256(outer_raw).hexdigest(),
    execution_receipt_sha256=sha256(helper_raw).hexdigest(),
    actual_HP_tests_new_solver_or_plot_calls_by_observation=0)
images = []
for name in ('comparison.png', 'distances_forces.png', 'peak_fields.png'):
    key = REL + '/run_001/view/' + name
    pin = helper['outputs'][key]
    assert (ROOT / key).stat().st_size == pin['bytes']
    images.append(dict(path=key, producer_declared_sha256=pin['sha256'], bytes=pin['bytes'],
        view_image_calls=1, detail='original', title_axes_labels_and_legends_legible=True))
qa = dict(card='M-UNLOAD2', status='pass_display_with_documented_scale_limits',
    recorded_utc=datetime.now(timezone.utc).isoformat(), inspected_by='root', images=images,
    actual_view_image_calls=3, new_GIF_postrun_decode=0, render_retry_or_replot=0,
    scientific_postrun_array_gzip_CSV_hash_or_decode=0,
    observed_segment_PEAK_input_mm=1.05, observed_LAST_input_mm=0.0,
    visual_mirror_only=True, deformation_scale=1,
    observations=[
        'The x1 mirrored comparison visibly shows the jaws withdrawing from the fixed square between the 1.05 segment start and the zero-input last state. The original loading peak remains 1.20.',
        'The distance/force graph uses input d as its horizontal coordinate; the actual saved chronological order is decreasing d. Orange distances and green rays in the geometry view are distances, not forces.',
        'The roughly 18mm left distance shares a scale with the small bottom gap. Near-contact micrometre changes should be read from the table/zoom label; the final 1mm gap is visible.',
        'The small regularization Fy curve lies near zero on the total-force scale; its actual components remain in the summary and result table. Fx is signed and is not monotone in magnitude over all targets.',
        'The field image is the 1.05 segment-PEAK snapshot. The displayed medium mean J is not the minimum Gauss-point J; Hu Frobenius colour is not the maximum absolute component.',
        'The ordinary saved summary reports tip bottom gap 0.7073049655183432mm and nonzero total body Fy 0.00016996582170512745N at d=0.25. Fixed-workpiece weak-form nodal force includes material and Hu; nonzero Fy alone is not proof of continued gripping.',
        'At zero input the ordinary summary records a 1mm tip bottom gap, body Fy -3.3446786794667874e-27N and negligible strain. These observations concern this fixed-workpiece model and do not upgrade pressure, free-object gripping, or stability qualification.'
    ], pressure_effective_grip_or_complete_release_qualified=False)
for name, value in (('root_terminal_confirmation.json', confirmation), ('pixel_QA.json', qa)):
    with (stage / 'author' / name).open('x', encoding='utf8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print(json.dumps(dict(status='root_actual_terminal_and_three_PNG_observations_recorded',
    science_reads_or_hashes=0, new_view_image_calls_by_recorder=0, new_GIF_decode=0)))
