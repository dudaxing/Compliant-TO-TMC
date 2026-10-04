"""Bind prepared new1mm inputs before the unique production/reference phases."""
from pathlib import Path
import hashlib
import json

ROOT = Path(r'D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_006'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
assert not (STAGE/'protocol.json').exists()
assert read(STAGE/'prepare_launch.json')['status'] == 'pass'
inventory = read(STAGE/'input_inventory.json')
freeze = read(STAGE/'source_freeze.json')
assert inventory['case']['targets_mm'] == [0., .5, 1., .5, 0.]
bindings = dict(inventory['input_bindings'])
bindings.update(freeze['sources'])
for name,pin in freeze['sources'].items():
    bindings[(STAGE/'sources'/Path(name).name).relative_to(ROOT).as_posix()] = pin
for name in ('input_inventory.json','source_freeze.json','prepare_protocol.json','prepare_launch.json'):
    path = STAGE/name
    bindings[path.relative_to(ROOT).as_posix()] = sha(path)
assert len(bindings) == 179 and all(sha(ROOT/name) == pin for name,pin in bindings.items())
relative = STAGE.relative_to(ROOT).as_posix()
record = dict(schema_version='native-mechanical-cycle-card-1.0',
    baseline_commit=inventory['baseline_commit'], sampled_RSS_bytes=8*1024**3, bindings=bindings,
    phases=dict(production=dict(argv=[relative+'/execute_cycle006.py'], helper_seconds=600, outer_seconds=660),
                reference=dict(argv=[relative+'/audit_cycle006.py','--input',relative,'--output',relative+'/reference',
                                     '--time-limit','240'], helper_seconds=240, outer_seconds=300)),
    prerequisite='Entire productionpass and original accounting/source/task preconditions before any HP; no reference replay of failed partial on this card',
    stop_policy='One invocation per phase; first formal failure closes the card; no retry/repair/force or clock extension')
(STAGE/'protocol.json').write_bytes((json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8'))
print(json.dumps(dict(status='production_reference_protocol_frozen', bindings=len(bindings),
    protocol_sha256=sha(STAGE/'protocol.json'), numerical_calls=0)))
