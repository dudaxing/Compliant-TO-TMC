"""One force-only run of the six pinned native supplied displacement states."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]
STAGE = Path(__file__).resolve().parent
SOURCE_PATHS = (
    'hf_repo/src/hf_eval/native_force.py', 'hf_repo/scripts/evaluate_native_force.py',
    'hf_repo/src/hf_eval/native_project.py', 'hf_repo/src/hf_eval/native_map.py',
    'hf_repo/src/hf_eval/data.py', 'hf_repo/src/hf_eval/regions.py', 'hf_repo/src/hf_eval/project.py',
    'hf_repo/src/hf_eval/tmc.py', 'hf_repo/src/hf_eval/tmc_kernel.py', 'hf_repo/src/hf_eval/__init__.py',
    'hf_repo/src/hf_eval/split_state.py', 'hf_repo/src/hf_eval/split_kernel_invariants_hu.py',
    'hf_repo/src/hf_eval/split_kernel_compensated.py',
    'hf_repo/src/hf_eval/compensated_invariants.py', 'hf_repo/src/hf_eval/compensated_kinematics.py',
    'hf_repo/scripts/audit_native_force.py', 'hf_repo/scripts/hf4_split_precision_reference.py',
    'hf_repo/scripts/hf2_precision_reference.py', 'hf_repo/scripts/plot_native_force.py',
    'hf_repo/tests/test_native_force.py', 'lf_data_preparation/native_force_001/prepare_inputs.py',
    'lf_data_preparation/native_force_001/execute_forces.py',
)
SECONDS = 120
RSS_LIMIT = 8 * 1024**3


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    receipt = STAGE / 'execution_receipt.json'
    if receipt.exists() or (STAGE / 'results').exists() or (STAGE / 'sources').exists():
        raise RuntimeError('Production destination must be new')
    inventory = json.loads((STAGE / 'input_inventory.json').read_text(encoding='utf-8'))
    expected_pairs = [(alias, state) for alias in ('inverter_canonical', 'gripper_canonical', 'gripper_native_fine')
                      for state in ('stripe', 'checker')]
    if [(row['alias'], row['state_name']) for row in inventory['cases']] != expected_pairs:
        raise RuntimeError('Unexpected six-state scope')
    inputs = {}
    for row in inventory['cases']:
        for name, pin in (('geometry_file', 'geometry_file_sha256'), ('geometry_npz_file', 'geometry_npz_sha256'),
                          ('task_file', 'task_file_sha256'), ('prior_model_file', 'prior_model_sha256'),
                          ('state_file', 'state_file_sha256')):
            inputs[row[name]] = row[pin]
    for name, pin in inputs.items():
        if digest(ROOT / name) != pin:
            raise RuntimeError('Changed input: ' + name)
    sources = {name: digest(ROOT / name) for name in SOURCE_PATHS}
    frozen = STAGE / 'sources'
    frozen.mkdir()
    for name in sources:
        (frozen / Path(name).name).write_bytes((ROOT / name).read_bytes())
    record = dict(status='running', schema_version='native-force-execution-1.0',
        baseline_commit=inventory['baseline_commit'], input_inventory_sha256=digest(STAGE / 'input_inventory.json'),
        sources=sources, inputs=inputs, cases=[], force_calls=0, HP_calls=0, tangent_calls=0,
        solver_calls=0, LF_imports=0, started_utc=datetime.now(timezone.utc).isoformat(),
        production_seconds_limit=SECONDS, sampled_RSS_limit_bytes=RSS_LIMIT,
        budget_mode='Cooperative elapsed/RSS checks, plus external process timeout; no OS memory hard limit')
    started = perf_counter()
    peak = 0

    def sample():
        nonlocal peak
        peak = max(peak, psutil.Process().memory_info().rss)
        if perf_counter() - started > SECONDS or peak > RSS_LIMIT:
            raise RuntimeError('Production time/RSS bound exceeded')

    try:
        sys.path.insert(0, str(ROOT / 'hf_repo/src'))
        from hf_eval.native_force import evaluate_native_force, write_native_force
        from hf_eval.split_state import SplitDisplacement
        sample()
        for row in inventory['cases']:
            begin = perf_counter()
            task = json.loads((ROOT / row['task_file']).read_text(encoding='utf-8'))
            with np.load(ROOT / row['state_file'], allow_pickle=False) as state:
                displacement = SplitDisplacement(state['lift'], state['fluctuation'])
            record['force_calls'] += 1
            result = evaluate_native_force(ROOT / row['geometry_file'], task, displacement)
            target = STAGE / row['result_directory']
            descriptor = write_native_force(result, target)
            with np.load(ROOT / row['prior_model_file'], allow_pickle=False) as prior, np.load(target / 'model/model.npz', allow_pickle=False) as actual:
                if set(prior.files) != set(actual.files):
                    raise RuntimeError('Changed native model fields')
                for name in prior.files:
                    if prior[name].dtype != actual[name].dtype or not np.array_equal(prior[name], actual[name]):
                        raise RuntimeError('Changed native model: ' + name)
            sample()
            record['cases'].append(dict(alias=row['alias'], state_name=row['state_name'], status='pass',
                invocations=1, elapsed_seconds=perf_counter()-begin,
                result_descriptor=descriptor.relative_to(STAGE).as_posix(),
                result_sha256=digest(descriptor), forces_sha256=digest(target / 'forces.npz'),
                model_sha256=digest(target / 'model/model.npz'), state_sha256=digest(target / 'state.npz')))
        for name, pin in inputs.items():
            if digest(ROOT / name) != pin:
                raise RuntimeError('Changed input during execution: ' + name)
        for name, pin in sources.items():
            if digest(ROOT / name) != pin or digest(frozen / Path(name).name) != pin:
                raise RuntimeError('Changed source during execution: ' + name)
        sample()
        record['status'] = 'pass'
    except Exception as error:
        record.update(status='fail', error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-started, peak_sampled_RSS_bytes=peak,
            completed_utc=datetime.now(timezone.utc).isoformat())
        with receipt.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(record, stream, indent=2, ensure_ascii=False)
            stream.write('\n')
    print(json.dumps({key: record[key] for key in ('status', 'force_calls', 'elapsed_seconds', 'peak_sampled_RSS_bytes')}))


if __name__ == '__main__':
    main()
