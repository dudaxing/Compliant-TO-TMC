"""One native coarse-checker tangent evaluation; no equilibrium solve."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

STARTED = perf_counter()
import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
SOURCE_PATHS = (
    'hf_repo/src/hf_eval/native_tangent.py', 'hf_repo/scripts/evaluate_native_tangent.py',
    'hf_repo/src/hf_eval/native_force.py', 'hf_repo/src/hf_eval/native_project.py',
    'hf_repo/src/hf_eval/native_map.py', 'hf_repo/src/hf_eval/data.py', 'hf_repo/src/hf_eval/regions.py',
    'hf_repo/src/hf_eval/project.py', 'hf_repo/src/hf_eval/tmc.py', 'hf_repo/src/hf_eval/tmc_kernel.py',
    'hf_repo/src/hf_eval/__init__.py', 'hf_repo/src/hf_eval/split_state.py',
    'hf_repo/src/hf_eval/split_numpy_tangent.py', 'hf_repo/src/hf_eval/split_kernel_invariants_hu.py',
    'hf_repo/src/hf_eval/split_kernel_compensated.py', 'hf_repo/src/hf_eval/compensated_invariants.py',
    'hf_repo/src/hf_eval/compensated_kinematics.py', 'hf_repo/scripts/audit_native_force.py',
    'hf_repo/scripts/hf4_split_precision_reference.py', 'hf_repo/scripts/hf2_precision_reference.py',
    'hf_repo/tests/test_native_force.py', 'hf_repo/tests/test_native_tangent.py',
    'hf_repo/scripts/audit_native_tangent.py', 'hf_repo/scripts/plot_native_tangent.py',
    'lf_data_preparation/native_tangent_001/prepare_inputs.py',
    'lf_data_preparation/native_tangent_001/execute_tangent.py',
)
SECONDS, RSS_LIMIT = 120, 8*1024**3


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    receipt = STAGE / 'execution_receipt.json'
    if receipt.exists() or (STAGE / 'result').exists() or (STAGE / 'sources').exists():
        raise RuntimeError('Production destination must be new')
    inventory = json.loads((STAGE / 'input_inventory.json').read_text(encoding='utf-8'))
    if len(inventory['cases']) != 1 or inventory['cases'][0]['alias'] != 'gripper_canonical':
        raise RuntimeError('Unexpected one-case scope')
    case = inventory['cases'][0]
    if [d['name'] for d in case['directions']] != ['vx_stripe', 'vy_checker']:
        raise RuntimeError('Unexpected two directions')
    inputs = {case[name]: case[pin] for name, pin in (
        ('geometry_file', 'geometry_file_sha256'), ('geometry_npz_file', 'geometry_npz_sha256'),
        ('task_file', 'task_file_sha256'), ('prior_model_file', 'prior_model_sha256'),
        ('state_file', 'state_file_sha256'))}
    inputs.update({row['file']: row['sha256'] for row in case['directions']})
    for name, pin in inputs.items():
        if digest(ROOT/name) != pin:
            raise RuntimeError('Changed input: '+name)
    sources = {name: digest(ROOT/name) for name in SOURCE_PATHS}
    frozen = STAGE/'sources'
    frozen.mkdir()
    for name in sources:
        (frozen/Path(name).name).write_bytes((ROOT/name).read_bytes())
    record = dict(schema_version='native-tangent-execution-1.0', status='running',
        baseline_commit=inventory['baseline_commit'], input_inventory_sha256=digest(STAGE/'input_inventory.json'),
        sources=sources, inputs=inputs, invocations=0, force_calls=0, tangent_calls=0, HP_calls=0, solver_calls=0,
        LF_imports=0, started_utc=datetime.now(timezone.utc).isoformat(), seconds_limit=SECONDS,
        sampled_RSS_limit_bytes=RSS_LIMIT, budget_mode='Cooperative checks plus external timeout; not an OS memory hard limit')
    started, peak = STARTED, 0

    def sample():
        nonlocal peak
        peak = max(peak, psutil.Process().memory_info().rss)
        if perf_counter()-started > SECONDS or peak > RSS_LIMIT:
            raise RuntimeError('Production time/RSS bound exceeded')

    try:
        sys.path.insert(0, str(ROOT/'hf_repo/src'))
        from hf_eval.native_tangent import evaluate_native_tangent, write_native_tangent
        from hf_eval.split_state import SplitDisplacement
        sample()
        with np.load(ROOT/case['state_file'], allow_pickle=False) as state:
            displacement = SplitDisplacement(state['lift'], state['fluctuation'])
        task = json.loads((ROOT/case['task_file']).read_text(encoding='utf-8'))
        record.update(invocations=1, force_calls=1, tangent_calls=1)
        result = evaluate_native_tangent(ROOT/case['geometry_file'], task, displacement)
        descriptor = write_native_tangent(result, STAGE/case['result_directory'])
        sample()
        with np.load(ROOT/case['prior_model_file'], allow_pickle=False) as prior, np.load(descriptor.parent/'model/model.npz', allow_pickle=False) as actual:
            if set(prior.files) != set(actual.files):
                raise RuntimeError('Model field count changed')
            for name in prior.files:
                if prior[name].dtype != actual[name].dtype or not np.array_equal(prior[name], actual[name]):
                    raise RuntimeError('Model changed: '+name)
        record.update(result_sha256=digest(descriptor), result_directory=case['result_directory'],
            model_sha256=digest(descriptor.parent/'model/model.npz'), state_sha256=digest(descriptor.parent/'state.npz'),
            tangents_sha256=digest(descriptor.parent/'tangents.npz'),
            matrix_sha256={component: digest(descriptor.parent/(component+'_matrix.npz'))
                          for component in ('total', 'material', 'regularization')})
        for name, pin in inputs.items():
            if digest(ROOT/name) != pin:
                raise RuntimeError('Input changed during production: '+name)
        for name, pin in sources.items():
            if digest(ROOT/name) != pin or digest(frozen/Path(name).name) != pin:
                raise RuntimeError('Source changed during production: '+name)
        sample()
        record['status'] = 'pass'
    except Exception as error:
        record.update(status='fail', error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-started, peak_sampled_RSS_bytes=peak,
                      completed_utc=datetime.now(timezone.utc).isoformat())
        with receipt.open('x', encoding='utf-8', newline='\n') as output:
            json.dump(record, output, indent=2)
            output.write('\n')
    print(json.dumps({key: record[key] for key in ('status', 'force_calls', 'tangent_calls', 'elapsed_seconds', 'peak_sampled_RSS_bytes')}))


if __name__ == '__main__':
    main()
