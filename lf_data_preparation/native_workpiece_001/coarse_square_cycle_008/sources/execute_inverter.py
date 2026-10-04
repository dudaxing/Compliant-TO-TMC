"""One coarse inverter mean path, preserving the frozen native NumPy API.

The source capsule retains all 33 earlier byte pins plus four new sources.
The two historical stage wrappers are context snapshots, not executed here.
"""
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
    'hf_repo/src/hf_eval/native_mean.py', 'hf_repo/scripts/solve_native_mean.py',
    'hf_repo/src/hf_eval/native_project.py', 'hf_repo/src/hf_eval/native_force.py',
    'hf_repo/src/hf_eval/native_map.py', 'hf_repo/src/hf_eval/data.py', 'hf_repo/src/hf_eval/regions.py',
    'hf_repo/src/hf_eval/project.py', 'hf_repo/src/hf_eval/tmc.py', 'hf_repo/src/hf_eval/tmc_kernel.py',
    'hf_repo/src/hf_eval/__init__.py', 'hf_repo/src/hf_eval/split_displacement.py',
    'hf_repo/src/hf_eval/displacement.py', 'hf_repo/src/hf_eval/split_affine.py',
    'hf_repo/src/hf_eval/split_prescribed.py', 'hf_repo/src/hf_eval/split_kernel.py',
    'hf_repo/src/hf_eval/prescribed.py', 'hf_repo/src/hf_eval/split_state.py',
    'hf_repo/src/hf_eval/split_numpy_tangent.py', 'hf_repo/src/hf_eval/split_kernel_invariants_hu.py',
    'hf_repo/src/hf_eval/split_kernel_compensated.py', 'hf_repo/src/hf_eval/compensated_invariants.py',
    'hf_repo/src/hf_eval/compensated_kinematics.py', 'hf_repo/tests/test_native_force.py',
    'hf_repo/tests/test_native_mean.py', 'hf_repo/scripts/audit_native_force.py',
    'hf_repo/scripts/audit_native_mean.py', 'hf_repo/scripts/hf4_split_precision_reference.py',
    'hf_repo/scripts/hf2_precision_reference.py', 'hf_repo/scripts/run_split_average_demo.py',
    'hf_repo/scripts/plot_native_mean.py', 'lf_data_preparation/native_mean_001/prepare_inputs.py',
    'lf_data_preparation/native_mean_001/execute_mean.py',
    'lf_data_preparation/native_inverter_mean_001/prepare_inverter.py',
    'lf_data_preparation/native_inverter_mean_001/execute_inverter.py',
    'hf_repo/scripts/audit_native_mean_inverter.py', 'hf_repo/scripts/plot_native_mean_inverter.py',
)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    receipt = STAGE/'execution_receipt.json'
    if any(path.exists() for path in (receipt, STAGE/'result', STAGE/'sources', STAGE/'accepted_progress.jsonl')):
        raise RuntimeError('Production destination must be new')
    inventory_path = STAGE/'input_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    case, limits = inventory['case'], inventory['execution_limits']
    if case['alias'] != 'inverter_canonical' or case['targets_mm'] != [0., .001]:
        raise RuntimeError('Unexpected native small-path scope')
    inputs = {case[name]: case[pin] for name, pin in (
        ('geometry_file','geometry_file_sha256'), ('geometry_npz_file','geometry_npz_sha256'),
        ('task_file','task_file_sha256'), ('prior_model_file','prior_model_sha256'),
        ('prior_task_file','prior_task_sha256'), ('direction_file','direction_file_sha256'),
        ('lifting_file','lifting_file_sha256'))}
    for name, pin in inputs.items():
        if digest(ROOT/name) != pin:
            raise RuntimeError('Changed input: '+name)
    sources = {name: digest(ROOT/name) for name in SOURCE_PATHS}
    frozen = STAGE/'sources'
    frozen.mkdir()
    for name in sources:
        (frozen/Path(name).name).write_bytes((ROOT/name).read_bytes())
    record = dict(schema_version='native-mean-execution-1.0', status='running',
        baseline_commit=inventory['baseline_commit'], input_inventory_sha256=digest(inventory_path),
        sources=sources, inputs=inputs, invocations=0, force_calls=0, tangent_calls=0, solver_calls=0,
        HP_calls=0, JIT_calls=0, LF_imports=0, accepted_states=0,
        started_utc=datetime.now(timezone.utc).isoformat(), seconds_limit=limits['production_seconds'],
        sampled_RSS_limit_bytes=limits['sampled_RSS_bytes'],
        budget_mode='Cooperative elapsed/RSS checks and external timeout; not an OS memory hard cap',
        source_capsule_scope='37 byte pins; historical native_mean_001 wrappers are retained context, not executed; full Git root and runtime required')
    process, peak = psutil.Process(), 0

    def sample():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
        if perf_counter()-STARTED > limits['production_seconds'] or peak > limits['sampled_RSS_bytes']:
            raise RuntimeError('Production time/RSS bound exceeded')

    def accepted(snapshot):
        sample()
        index = record['accepted_states']
        row = dict(index=index, state_sha256=snapshot.record['state_sha256'],
            d=snapshot.record['d'], R_input=snapshot.record['R_input'], q_in=snapshot.record['q_in'],
            q_out=snapshot.record['q_out'], relative_residual=snapshot.record['relative_residual'],
            assembler_force_call=snapshot.record['assembler_force_call'],
            assembler_tangent_call=snapshot.record['assembler_tangent_call'],
            elapsed_seconds=perf_counter()-STARTED)
        with (STAGE/'accepted_progress.jsonl').open('a', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(row)+'\n')
        record['accepted_states'] += 1
        print(json.dumps(row), flush=True)

    try:
        sample()
        sys.path.insert(0, str(ROOT/'hf_repo/src'))
        from hf_eval.displacement import DisplacementSettings
        from hf_eval.native_mean import solve_native_mean, write_native_mean
        sample()
        task = json.loads((ROOT/case['task_file']).read_text(encoding='utf-8'))
        with np.load(ROOT/case['lifting_file'], allow_pickle=False) as saved:
            if set(saved.files) != {'lift_origin','lift_shape'} or any(np.any(saved[name]) for name in saved.files):
                raise RuntimeError('Declared zero lift differs')
        record.update(invocations=1, solver_calls=None, force_calls=None, tangent_calls=None,
            counter_semantics='Returned API counts are authoritative; unavailable if API raises before returning')
        result = solve_native_mean(ROOT/case['geometry_file'], task, case['targets_mm'],
            settings=DisplacementSettings(**inventory['settings']), on_accept=accepted)
        record['call_counts'] = result.metadata['call_counts']
        record.update(force_calls=record['call_counts']['force_calls'], tangent_calls=record['call_counts']['tangent_calls'],
            solver_calls=record['call_counts']['solver_invocations'])
        descriptor = write_native_mean(result, STAGE/case['result_directory'])
        sample()
        with np.load(ROOT/case['prior_model_file'], allow_pickle=False) as prior, np.load(descriptor.parent/'model/model.npz', allow_pickle=False) as actual:
            if set(prior.files) != set(actual.files):
                raise RuntimeError('Model field count changed')
            for name in prior.files:
                if prior[name].dtype != actual[name].dtype or prior[name].tobytes() != actual[name].tobytes():
                    raise RuntimeError('Physical model changed: '+name)
        record.update(result_sha256=digest(descriptor), result_directory=case['result_directory'],
            model_sha256=digest(descriptor.parent/'model/model.npz'), production_status=result.metadata['status'],
            production_converged=result.metadata['production_converged'], task_target_executed=result.metadata['task_target_executed'],
            accepted_states=len(result.accepted), state_sha256=[snapshot.record['state_sha256'] for snapshot in result.accepted],
            save_force_calls=result.metadata['save_force_calls'], save_tangent_calls=result.metadata['save_tangent_calls'])
        for name, pin in inputs.items():
            if digest(ROOT/name) != pin:
                raise RuntimeError('Input changed during production: '+name)
        for name, pin in sources.items():
            if digest(ROOT/name) != pin or digest(frozen/Path(name).name) != pin:
                raise RuntimeError('Source changed during production: '+name)
        sample()
        if not result.path['target_reached']:
            raise RuntimeError('Numerical path did not reach target: '+repr(result.path['failure']))
        record['status'] = 'pass'
    except Exception as error:
        record.update(status='fail', error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=peak,
            completed_utc=datetime.now(timezone.utc).isoformat())
        with receipt.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(record, stream, indent=2)
            stream.write('\n')
    print(json.dumps({key:record[key] for key in ('status','accepted_states','force_calls','tangent_calls','elapsed_seconds','peak_sampled_RSS_bytes')}))


if __name__ == '__main__':
    main()
