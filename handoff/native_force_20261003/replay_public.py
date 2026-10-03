"""Replay six ordinary force CLIs from a public clone; no new HP or solve."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter, sleep

import numpy as np
import psutil

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    stage = ROOT / 'lf_data_preparation/native_force_001'
    inventory = json.loads((stage / 'input_inventory.json').read_text(encoding='utf-8'))
    record = dict(status='running', scope='same-machine independent-directory CLI recovery; no new scientific qualification',
        force_calls=0, HP_calls=0, tangent_calls=0, solver_calls=0, LF_imports=0,
        seconds_limit=120, sampled_RSS_limit_bytes=8*1024**3, cases=[])
    started = perf_counter()
    peak = 0
    try:
        for row in inventory['cases']:
            target = args.output / row['alias'] / row['state_name']
            command = [sys.executable, '-B', str(ROOT / 'hf_repo/scripts/evaluate_native_force.py'),
                '--geometry', str(ROOT / row['geometry_file']), '--task', str(ROOT / row['task_file']),
                '--state', str(ROOT / row['state_file']), '--output', str(target)]
            log = args.output / (row['alias'] + '_' + row['state_name'] + '.log')
            record['force_calls'] += 1
            with log.open('x', encoding='utf-8') as output:
                child = subprocess.Popen(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
                members = [psutil.Process(child.pid)]
                try:
                    while child.poll() is None:
                        try:
                            members = [psutil.Process(child.pid)] + psutil.Process(child.pid).children(recursive=True)
                            peak = max(peak, sum(p.memory_info().rss for p in members if p.is_running()))
                        except psutil.NoSuchProcess:
                            pass
                        if perf_counter()-started > 120 or peak > 8*1024**3:
                            raise RuntimeError('Public CLI replay budget exceeded')
                        sleep(.05)
                except Exception:
                    for member in reversed(members):
                        try:
                            member.terminate()
                        except psutil.NoSuchProcess:
                            pass
                    _, remaining = psutil.wait_procs(members, timeout=10)
                    record['cleanup_remaining_observed_pids'] = [member.pid for member in remaining]
                    if remaining:
                        record['cleanup_status'] = 'Observed members remain alive; no force termination'
                    raise
            if child.returncode != 0:
                raise RuntimeError('Public force CLI failed: ' + log.name)
            reference = stage / row['result_directory']
            equal_files = []
            for name in ('model/model.json', 'model/model.npz', 'model/source_geometry/geometry.json',
                         'model/source_geometry/geometry.npz', 'state.npz', 'forces.npz'):
                if digest(reference / name) != digest(target / name):
                    raise RuntimeError('Byte mismatch: ' + name)
                equal_files.append(name)
            equal_arrays = 0
            for name in ('model/model.npz', 'state.npz', 'forces.npz'):
                with np.load(reference / name, allow_pickle=False) as expected, np.load(target / name, allow_pickle=False) as actual:
                    if set(expected.files) != set(actual.files):
                        raise RuntimeError('Array field mismatch')
                    for field in expected.files:
                        if expected[field].dtype != actual[field].dtype or not np.array_equal(expected[field], actual[field]):
                            raise RuntimeError('Array mismatch: ' + field)
                        equal_arrays += 1
            left = json.loads((reference / 'result.json').read_text(encoding='utf-8'))
            right = json.loads((target / 'result.json').read_text(encoding='utf-8'))
            variable_keys = {'timing_seconds', 'descriptor_sha256'}
            if {k: v for k, v in left.items() if k not in variable_keys} != {k: v for k, v in right.items() if k not in variable_keys}:
                raise RuntimeError('Physical result metadata mismatch')
            record['cases'].append(dict(alias=row['alias'], state_name=row['state_name'], status='pass',
                equal_files=equal_files, equal_arrays=equal_arrays, metadata_comparison='All except timing and consequent descriptor hash',
                log_sha256=digest(log), result_sha256=digest(target / 'result.json')))
        if perf_counter()-started > 120:
            raise RuntimeError('Public replay elapsed bound exceeded')
        record['status'] = 'pass'
    except Exception as error:
        record.update(status='fail', error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-started, peak_sampled_child_tree_RSS_bytes=peak)
        with (args.output / 'replay_receipt.json').open('x', encoding='utf-8', newline='\n') as output:
            json.dump(record, output, indent=2)
            output.write('\n')
    print(json.dumps({key: record[key] for key in ('status', 'force_calls', 'elapsed_seconds', 'peak_sampled_child_tree_RSS_bytes')}))


if __name__ == '__main__':
    main()
