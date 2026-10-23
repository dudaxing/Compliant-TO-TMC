"""Independent preparation-only ordinary/source identity review; no HF imports."""
import ast
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess

A = Path(__file__).resolve().parent
R = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')

def plain(path):
    return json.loads(path.read_text(encoding='utf-8'))

def canonical(value):
    # Independent standard-library reproduction of data.py:44-67 for JSON values.
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, float):
        assert math.isfinite(value)
        return (0.0 if value == 0.0 else value).hex()
    assert value is None or isinstance(value, (str, int, bool))
    return value

def canonical_digest(value):
    payload = json.dumps(canonical(value), sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False, allow_nan=False).encode('utf-8')
    return sha256(payload).hexdigest()

b = plain(A/'SOURCE_BINDING.json')
c = plain(A/'CONTRACT.json')
source_names = {row['path'] for row in b['production_source_files']}
actual_names = {p.relative_to(R).as_posix() for p in (R/'hf_repo/src/hf_eval').glob('*.py')}
assert source_names == actual_names and len(source_names) == 57
for row in b['production_source_files']:
    raw = (R/row['path']).read_bytes()
    assert len(raw) == row['bytes'] and sha256(raw).hexdigest() == row['sha256']

ordinary = []
for row in b['ordinary_sources']:
    raw = Path(row['path']).read_bytes()
    assert len(raw) == row['bytes'] and sha256(raw).hexdigest() == row['sha256']
    value = json.loads(raw)
    declared = value['descriptor_sha256']
    assert canonical_digest({k: v for k, v in value.items() if k != 'descriptor_sha256'}) == declared
    ordinary.append(value)
force, fixed, model, geometry = ordinary
assert force['status'] == 'success' and force['target_reached'] is True and force['failure'] is None
selected = force['accepted_steps'][-1]
assert selected['is_original_target'] is True and selected['original_target_index'] == 1
assert force['force_task']['body_load_targets_half_N'] == [b['original_preload_half_N'], b['segment_anchor_half_N']]
assert selected['P_target_half_N'] == b['segment_anchor_half_N']
assert b['selected_force_state'] == {key: selected[key] for key in b['selected_force_state']}
assert b['settings'] == force['settings'] and b['force_settings'] == force['force_settings']
assert b['root_fixed_source'] == force['source']
assert force['source']['parent_result']['sha256'] == b['ordinary_sources'][1]['sha256']
assert force['source']['parent_model']['sha256'] == b['ordinary_sources'][2]['sha256']
assert fixed['model']['descriptor_file_sha256'] == b['ordinary_sources'][2]['sha256']
assert fixed['model']['descriptor_sha256'] == model['descriptor_sha256']
assert model['source_geometry']['descriptor_file_sha256'] == b['ordinary_sources'][3]['sha256']
assert model['source_geometry']['descriptor_sha256'] == geometry['descriptor_sha256']
for name in ('split_numpy_tangent.py', 'split_kernel_invariants_hu.py'):
    key = 'hf_repo/src/hf_eval/'+name
    actual = next(row['sha256'] for row in b['production_source_files'] if row['path'] == key)
    assert force['mechanics_source_sha256'][key] == actual

# Scientific dependencies: metadata and stat only. Do not open/read/hash archives.
for row in b['scientific_dependencies_stat_only']:
    p = Path(row['path'])
    assert p.is_file() and p.stat().st_size == row['bytes']
    assert row['current_action'] == 'stat only; content not read, hashed or decoded'

assert c['status'] == 'not_approved_not_implemented_not_executed'
assert c['tests']['methods'] == 12 and c['tests']['real_paths_max'] == 7
assert c['tests']['finite_algebra_injection_rejection_calls_max'] == sum((4,6,1,1,1,6,5,8,5)) == 37
assert c['resources']['tests_total_seconds'] == c['resources']['tests_process_seconds']+c['resources']['tests_cleanup_seconds'] == 480
assert c['resources']['helper_seconds'] == c['resources']['tests_total_seconds']+c['resources']['display_and_QA_seconds']+c['resources']['other_shared_seconds'] == 660
assert c['resources']['outer_seconds'] == 720
assert c['outputs'] == dict(PNG=1, PNG_inspections_max=1, GIF=0, new_HP=0, real_r9_paths=0)

tree = ast.parse((A/'prepare.py').read_text(encoding='utf-8'))
imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
imports |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
assert imports == {'datetime','hashlib','json','pathlib','subprocess'}
head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=R, text=True).strip()
assert head == b['baseline'] == '7ebcbf747a85e9c8bbe547bcd6e4fe600f76c12c'
assert not subprocess.check_output(['git','status','--porcelain','--','hf_repo/src/hf_eval'], cwd=R, text=True).strip()

names = ('PREPARATION.md','INTERFACE_SPEC.md','VALIDATION_PLAN.md','L-CTIPFRESUME1_CARD.md',
         'RECOVERY.md','SOURCE_BINDING.md','SOURCE_BINDING.json','CONTRACT.json',
         'prepare.py','SCHEMATIC_QA.json','MATH_AUDIT.md','MATH_AUDIT.json',
         'VALIDATION_AUDIT.md','VALIDATION_AUDIT.json')
pins = {}
for name in names:
    raw = (A/name).read_bytes()
    pins[name] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())

result = dict(status='PASS_PREPARATION_IDENTITIES_ONLY', baseline=head,
              production_source_raw_identities_verified=57, ordinary_raw_and_canonical_verified=4,
              scientific_dependencies_stat_only=3, scientific_content_reads=0,
              production_changes=0, F=0,T=0,HP=0, tests=0, equilibrium_solves=0,
              media_open=0, contract_count_and_clock_arithmetic='consistent', reviewed_pins=pins)
(A/'PREPARATION_IDENTITY_REVIEW.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k != 'reviewed_pins'}, ensure_ascii=False))
