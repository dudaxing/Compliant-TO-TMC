"""One bounded, prereviewed 40-target project path; no automatic parameter retry."""
from pathlib import Path
import argparse
import hashlib
import json
from hf_eval import evaluate
from hf_eval.evaluation import implementation_hash

p = argparse.ArgumentParser()
p.add_argument('--dataset', type=Path, required=True)
p.add_argument('--family', choices=('inverter', 'gripper'), required=True)
p.add_argument('--spec', type=Path, required=True)
p.add_argument('--gate', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
repo = Path(__file__).resolve().parents[1]
gate = json.loads(a.gate.read_text())
spec = json.loads(a.spec.read_text())
assert gate['status'] == 'front_gate_pass_full_paths_authorized'
assert gate['source_sha256'] == implementation_hash()
assert gate['spec_sha256'] == hashlib.sha256(a.spec.read_bytes()).hexdigest()
for evidence in gate['evidence']:
    path = a.gate.parent/evidence['relative_to_gate']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence['sha256'], path
task = json.loads((repo/f'configs/hf3/{a.family}_pilot_v1.json').read_text())
solver = dict(schema_version='hf-project-solver-1.0', solver_id='hf3_full_path_v1',
    analysis='tmc_average_displacement', targets_mm=spec['full_path_targets_mm'],
    settings=dict(tolerance=spec['internal_relative_force_tolerance'],
        constraint_tolerance=spec['constraint_relative_tolerance'],
        displacement_scale_floor=spec['displacement_scale_floor_mm'],
        force_scale_floor_factor=spec['force_scale_floor_factor'], max_checks=spec['max_checks'],
        max_backtracks=spec['max_backtracks'], max_bisections=spec['max_bisections'],
        armijo_c=spec['armijo_c'], minimum_increment=spec['full_path_targets_mm'][0]/16,
        time_limit_seconds=465.))
result = evaluate(a.dataset/f'canonical/{a.family}/geometry.json', task, solver, a.output)
print(json.dumps(dict(family=a.family, numerics=result['numerics'],
    target_metrics=result['metrics_at_target'], accepted_steps=result['path']['accepted_step_count'],
    original_targets_reached=result['path']['original_targets_reached'],
    independent_precision=result['independent_precision']), allow_nan=False), flush=True)
raise SystemExit(0 if result['numerics']['status'] == 'success' else 2)
