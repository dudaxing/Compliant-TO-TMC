"""Root's saved-source review; no product import, test or science execution."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import ast
import json

root = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
author = Path(__file__).resolve().parent
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
files = [author/'execute_batch_forward.py', author/'install_batch_forward.py']
for source in files:
    compile(ast.parse(source.read_text(encoding='utf-8')), str(source), 'exec')
functional = read(root/'lf_data_preparation/native_interface_001/batch_validation_001/functional_protocol.json')
sources = {name: pin for name, pin in functional['bindings'].items() if name.startswith('hf_repo/src/')}
assert len(sources) == 28 and all(sha(root/name) == pin for name, pin in sources.items())
manifest = read(root/'lf_data_preparation/native_interface_001/batch_validation_001/example_two_case_manifest.json')
assert manifest['options'] == dict(targets=[0., .005, .010, .025], minimum_increment=.0000625,
    time_limit_seconds=1800, response_mode='complete', tangent_mode='full', initial_guess='tangent')
tasks = [read(root/case['task']) for case in manifest['cases']]
physical = [{key: value for key, value in task.items() if key not in ('task_id', 'geometry')} for task in tasks]
assert physical[0] == physical[1] and len(physical[0]) == 19
inventories = [read(root/'lf_data_preparation'/base/'input_inventory.json') for base in
               ('native_gripper_task_025_001', 'native_fine_task_025_001')]
assert inventories[0]['gates'] == inventories[1]['gates']
assert inventories[0]['gates']['global_force_balance'] == '1e-6'
assert inventories[0]['gates']['fixed_displacement_mm'] == '8e-11'
assert inventories[0]['gates']['production_residual'] == '1e-9'
for case, inventory in zip(manifest['cases'], inventories):
    assert sha(root/case['task']) == inventory['case']['prior_task_sha256']
    assert sha(root/case['geometry']) == inventory['case']['geometry_file_sha256']
    assert sha((root/case['geometry']).with_suffix('.npz')) == inventory['case']['geometry_npz_sha256']
checks = read(author/'author_checks.json')
assert checks['status'] == 'pass_static_only' and checks['scientific_calls'] == 0
assert checks['HF_imports_performed'] == checks['tests_run'] == 0
for name, pin in checks['source_sha256'].items():
    assert sha(Path(name)) == pin
report = dict(status='pass_static_only', blocking_findings=[],
    source_sha256={str(path): sha(path) for path in files}, unchanged_hf_sources=len(sources),
    task_common_keys=19, original_gate_source='Both original .025 input inventories',
    findings=[
        'Root read the whole worker candidate and installer, then all revised callback/settings/model/GC/timing sections.',
        'Actual batch alias delegates real API once per attempted case; existing source bytes and numerical modes are unchanged.',
        'Current wrappers count actual starts/completions; no fixed 14F/9T assumption; original cached writer must have zero F/T delta.',
        'Original capture runs before scalar flush; the final callback resource checkpoint follows the saved scalar prefix.',
        'Original fixed-DOF cached gate is the sole inherited array check; no additional field/geometry/force observation.',
        'No retained NativeMeanResult collection; one guarded garbage collection after each returned API releases unreachable recursive closures.',
        'Original failures remain in original response/index; escaping RuntimeError keeps its identity, ends the batch, and cannot trigger numerical retry.',
        'Shared controller1800 is per-case solve only; helper2400 includes imports through final hashing; outer2460 covers final receipt write and exit.',
        'Stage install occurs before running at aa072 HEAD; no code or stage commit until the production window has terminated.',
        'Full settings and saved-model JSON23 fields consume protocol declarations; original gates are inherited unchanged.',
        'Two different designs and native grids; no old HP/mesh/ranking/contact/HF5 qualification transferred.'
    ], raw_checks_scope='AST/ordinary JSON and SHA only; no NPZ loads, HF imports or runtime tests',
    scientific_calls=0, functional_test_calls=0, stage_installations=0,
    author_checks_sha256=sha(author/'author_checks.json'),
    review_driver_sha256=sha(Path(__file__)),
    created_utc=datetime.now(timezone.utc).isoformat())
target=author/'review/root_batch_forward_static_review.json'
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
print(json.dumps(dict(status=report['status'], source_sha256=report['source_sha256'], review_sha256=sha(target))))
