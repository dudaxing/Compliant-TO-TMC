"""Ordinary metadata/source-only preparation; no HF/scientific imports or NPZ reads."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import importlib.metadata
import json
import math
import subprocess
import sys

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).parent
PARENT = ROOT / 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/wave_circle_tip_alpha1/result.json'
VIEW = ROOT / 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_001/run_001/view/wave_circle_tip_alpha1/012'

def read(path):
    return json.loads(path.read_bytes())

def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, float):
        assert math.isfinite(value)
        return (0.0 if value == 0.0 else value).hex()
    return value

def canonical_sha(value):
    data = json.dumps(canonical(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    return sha256(data).hexdigest()

def pin(path):
    data = path.read_bytes()
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': sha256(data).hexdigest(), 'method': 'actual_ordinary_file_bytes'}

parent = read(PARENT)
model_file = PARENT.parent / parent['model']['descriptor_path']
model = read(model_file)
selected = parent['states'][12]
state_file = PARENT.parent / selected['descriptor_path']
state = read(state_file)
geometry_file = model_file.parent / model['source_geometry']['snapshot']['descriptor']
geometry = read(geometry_file)
for obj in (parent, model, state, geometry):
    assert canonical_sha({k: v for k, v in obj.items() if k != 'descriptor_sha256'}) == obj['descriptor_sha256']
assert state == {k: v for k, v in selected.items() if k not in ('descriptor_path', 'descriptor_file_sha256')}
assert pin(model_file)['sha256'] == parent['model']['descriptor_file_sha256']
assert pin(state_file)['sha256'] == selected['descriptor_file_sha256']
assert pin(geometry_file)['sha256'] == model['source_geometry']['descriptor_file_sha256']
assert canonical_sha(model['task']) == parent['task_sha256'] == model['task_sha256']
assert parent['status'] == 'success' and parent['path_kind'] == 'load_only'
assert parent['target_reached'] and parent['path_completed'] and parent['loading_peak_reached']
assert len(parent['states']) == 13 and parent['states'][-1] == selected
assert [s['d'] for s in parent['states'] if s['is_original_target']] == parent['targets_mm'] == model['task']['path']['targets_mm']
assert selected['d'] == selected['physical_mean_target_mm'] == selected['original_target_displacement'] == model['task']['input']['target_mm'] == 1.06
assert selected['original_target_index'] == 12 and selected['leg'] == 'loading'
assert parent['target_origin'] == 0 and parent['lift_origin_zero'] and parent['lift_shape_zero']

regions = model['region_metadata']
body = regions['workpiece']
grid = model['grid']
ny, nx = grid['shape_yx']
hx, hy = grid['cell_size_mm']
origin = grid['origin_mm']
coordinates = [[origin[0]+(i % (nx+1))*hx, origin[1]+(i // (nx+1))*hy] for i in body['nodes']]
nodal_file = VIEW / 'nodal.json'
nodal = read(nodal_file)
assert nodal['node_ids'] == body['nodes'] and nodal['coordinates_mm'] == coordinates
bbox = [[min(x[c] for x in coordinates), max(x[c] for x in coordinates)] for c in (0, 1)]
zero = set().union(*(regions[k]['dofs'] for k in ('support', 'entity_symmetry', 'background_symmetry')))
fixed = set(regions['fixed_dofs'])
bdofs = set(body['dofs'])
background = set(regions['background_symmetry']['dofs'])
assert fixed == zero | bdofs
assert all(d % 2 == 1 and d in background for d in zero & bdofs)
for port in ('input', 'output'):
    assert not set(regions['ports'][port]['nodes']) & set(body['nodes'])
right_nodes = [j*(nx+1)+nx for j in range(ny+1)]
assert not any(2*i in fixed for i in right_nodes)
assert [i for i in right_nodes if 2*i+1 in fixed] == [14984]

ordinary = [pin(p) for p in (PARENT, model_file, state_file, geometry_file, nodal_file, VIEW/'derived.json')]
archives = []
for path, declaration, role in (
        (model_file.parent/model['arrays']['path'], model['arrays'], 'byte identity only; no model cache decoding by probe API'),
        (geometry_file.parent/geometry['arrays']['path'], geometry['arrays'], 'future source geometry four fields'),
        (PARENT.parent/state['state']['path'], state['state'], 'future selected lift/fluctuation only')):
    archives.append({'path': path.relative_to(ROOT).as_posix(), 'bytes_by_stat': path.stat().st_size,
                     'declared_sha256': declaration['sha256'], 'bytes_rehashed_now': False,
                     'decoded_now': False, 'future_role': role,
                     'declared_fields': {k: {'shape': v['shape'], 'dtype': v['dtype']} for k, v in declaration['fields'].items()} if role != 'byte identity only; no model cache decoding by probe API' else {}})
sources = []
for name in ('native_probe.py', 'split_displacement.py', 'split_numpy_tangent.py', 'split_kernel_invariants_hu.py', 'native_project.py', 'data.py', 'native_resume.py'):
    item = pin(ROOT/'hf_repo/src/hf_eval'/name)
    if name in ('split_numpy_tangent.py', 'split_kernel_invariants_hu.py'):
        assert item['sha256'] == parent['mechanics_source_sha256']['hf_repo/src/hf_eval/'+name]
    sources.append(item)
derived = read(VIEW/'derived.json')['row']
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == '18f3589d406861bde9a34176567b59e23844a39a'
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
record = {
    'stage': 'L-CTIPPROBE1_preparation_only', 'created_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'ordinary_metadata_source_candidate_verified_runtime_admission_not_run',
    'git': {'root': ROOT.as_posix(), 'head': head, 'branch': 'main', 'origin': 'https://github.com/dudaxing/Compliant-TO-TMC.git', 'worktree_clean': True, 'fetch_succeeded': True, 'main_vs_origin_main_difference': []},
    'ordinary_file_bindings': ordinary, 'NPZ_declared_identity_and_stat_only': archives,
    'source_bindings': sources, 'parent_task_sha256': model['task_sha256'],
    'selected': {'accepted_index': 12, 'original_target_index': 12, 'd_mm': 1.06,
                 'state_sha256': selected['state_sha256'], 'R_input_N': selected['R_input'],
                 'relative_residual_historical': selected['relative_residual'], 'minimum_J_historical': selected['minimum_J']},
    'geometry_metadata_check': {'source': 'Pinned model ordinary member IDs/grid checked exactly against pinned old fixed-body nodal ordinary coordinates; no NPZ decoded.',
        'bbox_x_y_mm': bbox, 'workpiece_cell_count': len(body['cells']), 'body_node_count': len(body['nodes']),
        'body_node_ids_sha256': canonical_sha(body['nodes']), 'body_cell_ids_sha256': canonical_sha(body['cells']),
        'body_dofs': len(bdofs), 'zero_dofs': len(zero), 'fixed_dofs': len(fixed),
        'free_dofs': parent['counts']['free_dofs'], 'KKT_dimension': parent['counts']['free_dofs']+1,
        'zero_body_overlap': len(zero & bdofs), 'overlap_only_background_uy': True,
        'right_boundary_node_count': len(right_nodes), 'right_fixed_ux_nodes': [], 'right_fixed_uy_nodes': [14984],
        'reference_right_margin_mm': 92-bbox[0][1], 'q025_nominal_margin_to_reference_x92_mm': 92-(bbox[0][1]+0.025),
        'nominal_margin_scope': 'Reference-coordinate extent arithmetic, not actual deformed medium thickness or permitted-travel qualification.',
        'tip_node_historical': derived['tip_node'], 'tip_distance_historical_mm': derived['tip_to_raster_boundary_mm'],
        'right_strip_definition': 'Fixed reference cell IDs:80 rows, columns178 through183,480 nonbody-medium cells; actual phase membership must be checked from admitted new model.solid, not inferred as passed here.'},
    'inherited': {'settings': parent['settings'], 'response_mode': parent['response_mode'], 'tangent_execution': parent['tangent_execution'], 'initial_guess': parent['initial_guess'], 'material': model['material']},
    'runtime_metadata_only': {'python': sys.version, 'packages': {n: importlib.metadata.version(n) for n in ('numpy','scipy','matplotlib','jax','jaxlib','psutil')}},
    'new_HF_imports': 0, 'new_model_builds': 0, 'new_F_T_HP_equilibrium_calls': 0,
    'new_tests': 0, 'NPZ_content_reads': 0, 'media_content_reads': 0,
    'implementation_modified': False, 'formal_repository_modified': False,
    'remaining_runtime_requirements': ['Rehash the three actual NPZ byte identities', 'Decode original geometry four fields and selected split two fields only', 'Rebuild original project and verify source/region/material identity', 'Fresh q0 F/T passes without projection/Newton repair', 'Only then attempt q=.025 with original settings/gates']}
target = AUTHOR/'SOURCE_PREPARATION.json'
assert not target.exists()
target.write_bytes((json.dumps(record, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
print(json.dumps({'status': record['status'], 'ordinary_files': len(ordinary), 'NPZ_stat_only': len(archives), 'bbox': bbox, 'record': str(target)}, ensure_ascii=False))
