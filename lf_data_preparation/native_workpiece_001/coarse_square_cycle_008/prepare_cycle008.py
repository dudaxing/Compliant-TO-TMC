"""Freeze a new1.75mm task while retaining the qualified physical model and rules."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
BASELINE = '39443b5ad5504101bb8a16d6ac8c6b204c2dce8b'
MODEL_SHA = 'a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049'
TARGETS = [0., .5, 1., 1.5, 1.75, 1.5, 1., .5, 0.]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, value):
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode('utf-8'))


def main():
    prior = STAGE.parent/'coarse_square_cycle_007'
    original = STAGE.parent/'coarse_square_cycle_003'
    old = json.loads((prior/'input_inventory.json').read_text(encoding='utf-8'))
    old_sources = json.loads((prior/'source_freeze.json').read_text(encoding='utf-8'))['sources']
    assert not (STAGE/'input_inventory.json').exists() and not (STAGE/'sources').exists()
    assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == BASELINE
    unit = json.loads((STAGE.parent/'native_mean_mechanical_integration_001/unit_tests_result.json').read_text(encoding='utf-8'))
    previous_run = json.loads((prior/'execution_receipt.json').read_text(encoding='utf-8'))
    previous_ref = json.loads((prior/'reference/summary.json').read_text(encoding='utf-8'))
    assert unit['status'] == 'pass' and unit['failed_tests'] == unit['skipped_tests'] == 0
    assert previous_run['status'] == previous_ref['status'] == 'pass'
    assert previous_ref['accepted_states'] == 7 and previous_ref['HP_calls_completed'] == 14
    task_file = STAGE/'task.json'
    task, old_task = (json.loads(p.read_text(encoding='utf-8')) for p in (task_file, prior/'task.json'))
    descriptive = {'task_id','purpose','parameter_origin','description'}
    allowed = descriptive | {'input', 'path'}
    assert {k:v for k,v in task.items() if k not in allowed} == {k:v for k,v in old_task.items() if k not in allowed}
    assert task['input'] == dict(old_task['input'], target_mm=1.75)
    assert task['path'] == dict(kind='ordered_cycle', targets_mm=TARGETS)
    assert sha(ROOT/old['case']['workpiece_model_file']) == MODEL_SHA
    shutil.copyfile(prior/'direction.npz', STAGE/'direction.npz')
    row = dict(old['case'], targets_mm=TARGETS)
    for name in ('task','direction'):
        path = STAGE/(name+('.json' if name == 'task' else '.npz'))
        row[name+'_file'] = path.relative_to(ROOT).as_posix()
        row[name+'_file_sha256'] = sha(path)
    assert row['targets_mm'] == task['path']['targets_mm'] and max(row['targets_mm']) == task['input']['target_mm']
    previous = json.loads((original/'source_freeze.json').read_text(encoding='utf-8'))['sources']
    assert len(previous) == 63
    allowed_sources = {'hf_repo/src/hf_eval/native_mean.py', 'hf_repo/scripts/solve_native_mean.py',
                       'hf_repo/src/hf_eval/split_kernel_invariants_hu.py'}
    sources = {name: sha(ROOT/name) for name in previous}
    assert all(sources[name] == old_sources[name] for name in previous)
    transition = {name: dict(previous_sha256=pin, current_sha256=sources[name])
                  for name,pin in previous.items() if sources[name] != pin}
    assert transition.keys() == allowed_sources
    assert sources['hf_repo/src/hf_eval/split_kernel_invariants_hu.py'] == 'd5f7d20a6ec0c92847d67f8782f4dcc89772fc4ea62797626b0beae7effabd9a'
    assert sha(STAGE/'core_audit_mechanical.py') == sha(prior/'core_audit_mechanical.py') == 'b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5'
    for name in ('core_audit_mechanical.py','audit_cycle008.py','prepare_cycle008.py','execute_cycle008.py','launch_cycle008.py'):
        path = STAGE/name
        sources[path.relative_to(ROOT).as_posix()] = sha(path)
    assert len(sources) == len({Path(name).name for name in sources}) == 68
    (STAGE/'sources').mkdir()
    for name in sources:
        shutil.copyfile(ROOT/name, STAGE/'sources'/Path(name).name)
    freeze_file = STAGE/'source_freeze.json'
    write(freeze_file, dict(schema_version='native-workpiece-cycle-source-freeze-1.0',
        baseline_commit=BASELINE, sources=sources, source_transition=transition,
        scope='Original00363 byte-pinned closure with3 unchanged declared live transitions, plus5 new-card wrappers; no numerical implementation change from007'))
    inputs = dict(old['input_bindings'])
    assert len(inputs) == 46 and all(sha(ROOT/name) == pin for name,pin in inputs.items())
    for path in (prior/'input_inventory.json', prior/'source_freeze.json', prior/'execution_receipt.json',
                 prior/'reference/summary.json', task_file, STAGE/'direction.npz', STAGE/'README.md'):
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    assert len(inputs) == 53
    observation = 'Save first actual force and first actual tangent range-exception input, without additional evaluation or altered returns; original controller handles rethrown range exceptions'
    inventory = dict(old, baseline_commit=BASELINE, case=row,
        source_freeze_sha256=sha(freeze_file), input_bindings=inputs, source_transition=transition,
        qualification='Only this new explicit-mechanical coarse fixed-square0/.5/1/1.5/1.75/1.5/1/.5/0 task and all its actual accepted states; no inherited old-state qualification',
        reference_call_rule='Fresh HP80/120 separately on every actual accepted index including repeated targets and bisections; all3200cells/6642DOFs and original force/Jv/CSC/KKT/body gates, no energy or all-column qualification',
        observation_rule=observation, range_observation_rule=observation)
    assert inventory['settings'] == old['settings'] and inventory['gates'] == old['gates']
    assert inventory['execution_limits'] == old['execution_limits']
    write(STAGE/'input_inventory.json', inventory)
    print(json.dumps(dict(status='prepared_only', sources=len(sources), input_bindings=len(inputs),
        targets_mm=row['targets_mm'], source_freeze_sha256=sha(freeze_file),
        input_inventory_sha256=sha(STAGE/'input_inventory.json'), force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0)), flush=True)


if __name__ == '__main__':
    main()
