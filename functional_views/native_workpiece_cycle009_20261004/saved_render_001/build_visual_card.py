"""Freeze one three-program saved-only view after the complete fresh audit."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
MECH = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_009'
VIEW = ROOT/'functional_views/native_workpiece_cycle009_20261004'
CARD = VIEW/'saved_render_001'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
pins = {}

def bind(p, expected=None):
    value = sha(p)
    assert expected is None or value == expected, rel(p)
    pins[rel(p)] = value
    return value

def archives(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            bind(MECH/'reference'/value['path'], value['sha256'])
        for item in value.values():
            archives(item)
    elif isinstance(value, list):
        for item in value:
            archives(item)

assert not (CARD/'protocol.json').exists()
science = read(MECH/'protocol.json')
science_sha = bind(MECH/'protocol.json')
for name, expected in science['bindings'].items():
    bind(ROOT/name, expected)
for name in ('production_launch.json', 'reference_launch.json'):
    receipt = read(MECH/name)
    assert receipt['status'] == 'pass' and receipt['exit_code'] == 0
    assert receipt['invocations'] == 1 and receipt['all_bindings_unchanged']
    assert receipt['protocol_sha256'] == science_sha and receipt['stop_reason'] is None
    bind(MECH/name)
execution = read(MECH/'execution_receipt.json')
assert execution['status'] == 'pass' and execution['invocations'] == 1
bind(MECH/'execution_receipt.json')
bind(MECH/'result/result.json', execution['result_sha256'])
result = read(MECH/'result/result.json')
reference = read(MECH/'reference/summary.json')
assert result['status'] == 'success' and result['unload_endpoint_reached']
assert result['targets_mm'] == [0., .5, 1., 1.5, 1.75, 1.5, 1., .5, 0.]
assert reference['status'] == 'pass' and reference['result_sha256'] == execution['result_sha256']
assert len(result['states']) == reference['accepted_states'] == 9
assert reference['HP_calls_started'] == reference['HP_calls_completed'] == 18
for index, (state, checked) in enumerate(zip(result['states'], reference['states'])):
    assert checked['status'] == 'pass' and checked['index'] == index
    assert checked['state_sha256'] == state['state_sha256']
    assert checked['original_target_index'] == state['original_target_index']
    assert checked['target_mm'] == state['d'] and checked['leg'] == state['leg']
bind(MECH/'reference/summary.json')
for name, expected in reference['input_bindings'].items():
    bind(ROOT/name, expected)
archives(reference['states'])
for path in sorted((MECH/'result').rglob('*')):
    if path.is_file() and path.suffix in ('.json', '.npz'):
        bind(path)
bind(MECH/'accepted_progress.jsonl')
for name in ('comparison_receipt.json', 'comparison_launch.json'):
    path = ROOT/'lf_data_preparation/native_workpiece_001/numpy_tangent_chunk_001'/name
    assert read(path)['status'] == 'pass'
    bind(path)
programs = [VIEW/'plot_workpiece_cycle009.py', VIEW/'plot_tangent_cost.py', VIEW/'animate_saved_path.py']
sources = programs + [CARD/'render_saved_once.py', CARD/'launch_phase.py',
    ROOT/'functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py']
for source in sources:
    compile(source.read_bytes(), str(source), 'exec')
source_dir = CARD/'sources'
source_dir.mkdir(exist_ok=False)
for source in sources:
    value = bind(source)
    target = source_dir/source.name
    shutil.copyfile(source, target)
    bind(target, value)
shutil.copyfile(Path(__file__), CARD/'build_visual_card.py')
bind(CARD/'build_visual_card.py')
protocol = dict(schema_version='saved-complete-cycle009-three-view-card-1.0', bindings=pins,
    sampled_RSS_bytes=8*1024**3,
    phases={'render': dict(argv=[rel(CARD/'render_saved_once.py')], helper_seconds=120, outer_seconds=150)},
    render_programs=[
        [rel(programs[0]), '--stage', rel(MECH), '--output', rel(CARD/'physical_001'), '--protocol', rel(CARD/'protocol.json')],
        [rel(programs[1]), '--output', rel(CARD/'cost_001')],
        [rel(programs[2]), '--stage', rel(MECH), '--output', rel(CARD/'animation_001')]],
    actual_accepted_frames=9, deformation_scale=1,
    new_mechanics_or_geometry_calls=0, mechanical_hooks_monitored=False,
    call_count_basis='Saved-only source paths; not hooked mechanical telemetry',
    scope='Actual nine states, force components and cached production fields; saved single-pass cost; no new unsigned measurement or contact/clamp/pressure/energy qualification',
    stop_policy='One invocation; first error stops; no repair/retry/force/budget extension')
with (CARD/'protocol.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(protocol, stream, indent=2, ensure_ascii=False, allow_nan=False)
    stream.write('\n')
print(json.dumps(dict(status='prepared_not_executed', bindings=len(pins), actual_accepted_frames=9,
    protocol_sha256=sha(CARD/'protocol.json'), helper_seconds=120, outer_seconds=150)))
