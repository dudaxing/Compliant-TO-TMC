"""Record observed L-FWD1 terminal and the three actual root pixel inspections."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/lf_forward_001'
stage = ROOT / REL

def ordinary_pin(path):
    assert path.suffix.lower() in {'.json', '.py', '.md', '.jsonl', '.log'}
    return sha256(path.read_bytes()).hexdigest()

def write_new(name, value):
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

outer_path = stage / 'production_launch.json'
helper_path = stage / 'run_001/execution_receipt.json'
outer = json.loads(outer_path.read_text(encoding='utf-8'))
helper = json.loads(helper_path.read_text(encoding='utf-8'))
assert outer['status'] == helper['status'] == 'pass'
assert outer['exit_code'] == 0 and outer['invocations'] == 1 and outer['completed_utc']
assert helper['last_phase'] == 'closure'
assert helper['output_identity_seal'] == 'complete_inside_original_helper_window'

confirmation = dict(
    card='L-FWD1', status='actual_root_terminal_confirmed_pass',
    created_utc=datetime.now(timezone.utc).isoformat(),
    execution_closed=True, execution_status='pass',
    actual_terminal_exit_code=0, actual_launch_session_id=85185,
    actual_initial_launch_chunk_id='fea24c', actual_terminal_chunk_id='aa1850',
    actual_log_read_chunk_id='2891be',
    authorized_execution_source_commit='e23a34b6fac803bab4be6bd35e980807291326c3',
    protocol_SHA256=ordinary_pin(stage / 'protocol.json'),
    launch_sha256=ordinary_pin(outer_path), execution_receipt_sha256=ordinary_pin(helper_path),
    actual_single_original_invocation=True, external_retries=0,
    controller_limit_seconds=18000, helper_limit_seconds=19000, outer_limit_seconds=19060,
    sampled_RSS_limit_bytes=8 * 1024**3,
    actual_outer_seconds=outer['elapsed_seconds'], actual_helper_seconds=helper['elapsed_seconds'],
    actual_tree_RSS_bytes=outer['peak_sampled_tree_RSS_bytes'],
    actual_helper_RSS_bytes=helper['peak_sampled_RSS_bytes'],
    actual_accepted_states=helper['accepted_states'],
    production_gates=helper['cached_production_gates'],
    actual_PNGs=helper['actual_PNGs'], actual_GIF_frames=helper['actual_GIF_frames'],
    default_installations=0, new_HP_calls=0, new_tests=0,
    monitor_format_correction=dict(
        erroneous_PowerShell_UTC_monitor_chunk='d71c3f',
        corrected_timezone_aware_ordinary_monitor_chunk='72447b',
        actual_resource_clocks='Original perf_counter clocks; unchanged',
        not_a_scientific_failure=True),
    actual_live_process_snapshot_chunk='ab0ef7',
    scientific_late_bytes_headers_hashes_read=0,
    root_pixel_inspections=3, root_GIF_postdecode=0)
write_new('root_terminal_confirmation.json', confirmation)

notes = {
    'comparison.png': '峰值1.20 mm、最终回零变形、尖端局部和力曲线均可见，轴与图例可读；实际比例x1与显示镜像明确，距离/射线标为几何见证。',
    'distances_forces.png': '无符号有限表面距离、射线距离及有符号下半体Fx两面板可读，单位及三力图例清楚；不把几何距离认定为压力。',
    'peak_fields.png': '实体Green主应变、自由介质mean J和Hu Frobenius三面板、色条和单位可读；mean J图不替代九点minimum J门。',
}
inspections = []
for name, note in notes.items():
    relative = REL + '/run_001/view/' + name
    entry = helper['outputs'][relative]
    assert (ROOT / relative).stat().st_size == entry['bytes']
    inspections.append(dict(path=relative, actual_invocations=1, tool='view_image', detail='original',
        pixel_observation=note, result='pass_readable',
        producer_SHA256=entry['sha256'], bytes=entry['bytes'], identity_basis='Original closed helper seal plus stat only'))
write_new('pixel_QA.json', dict(card='L-FWD1', status='pass_actual_root_pixels', actual_invocations=3,
    authorized_maximum_each_PNG=1, inspections=inspections,
    GIF_frames_from_original_producer=25, GIF_postdecode=0, replot=0,
    scientific_hashes_or_headers_read=0, physics_qualification_upgraded=False))
print(json.dumps({'status': 'actual_root_terminal_and_pixel_records_written', 'actual_invocations': 3}))
