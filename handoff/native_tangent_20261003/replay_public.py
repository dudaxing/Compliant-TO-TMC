"""One public ordinary-file tangent CLI replay; no new HP or solve."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter, sleep

STARTED = perf_counter()
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
    stage = ROOT/'lf_data_preparation/native_tangent_001'
    case = json.loads((stage/'input_inventory.json').read_text(encoding='utf-8'))['cases'][0]
    record = dict(status='running', scope='same-machine independent-directory recovery, not new scientific qualification',
        force_calls=1, tangent_calls=1, HP_calls=0, solver_calls=0, LF_imports=0,
        seconds_limit=120, sampled_RSS_limit_bytes=8*1024**3)
    command = [sys.executable, '-B', str(ROOT/'hf_repo/scripts/evaluate_native_tangent.py'),
        '--geometry', str(ROOT/case['geometry_file']), '--task', str(ROOT/case['task_file']),
        '--state', str(ROOT/case['state_file']), '--output', str(args.output/'result')]
    started, peak = STARTED, 0
    try:
        with (args.output/'cli.log').open('x', encoding='utf-8') as log:
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            members = [psutil.Process(child.pid)]
            try:
                while child.poll() is None:
                    try:
                        members = [psutil.Process(child.pid)]+psutil.Process(child.pid).children(recursive=True)
                        peak = max(peak, sum(p.memory_info().rss for p in members if p.is_running()))
                    except psutil.NoSuchProcess:
                        pass
                    if perf_counter()-started > 120 or peak > 8*1024**3:
                        raise RuntimeError('Public replay time/RSS budget exceeded')
                    sleep(.05)
            except Exception:
                for member in reversed(members):
                    try:
                        member.terminate()
                    except psutil.NoSuchProcess:
                        pass
                _, remaining = psutil.wait_procs(members, timeout=10)
                record['cleanup_remaining_observed_pids'] = [p.pid for p in remaining]
                raise
        if child.returncode:
            raise RuntimeError('Public tangent CLI failed')
        expected, actual = stage/case['result_directory'], args.output/'result'
        names = ('model/model.json', 'model/model.npz', 'model/source_geometry/geometry.json',
                 'model/source_geometry/geometry.npz', 'state.npz', 'tangents.npz',
                 'total_matrix.npz', 'material_matrix.npz', 'regularization_matrix.npz')
        record['equal_files'] = []
        record['equal_arrays'] = 0
        for name in names:
            if digest(expected/name) != digest(actual/name):
                raise RuntimeError('Public byte mismatch: '+name)
            record['equal_files'].append(dict(path=name, sha256=digest(actual/name)))
            if name.endswith('.npz') and not name.startswith('model/source_geometry'):
                with np.load(expected/name, allow_pickle=False) as left, np.load(actual/name, allow_pickle=False) as right:
                    if set(left.files) != set(right.files):
                        raise RuntimeError('Public archive names differ: '+name)
                    for field in left.files:
                        if left[field].dtype != right[field].dtype or not np.array_equal(left[field], right[field]):
                            raise RuntimeError('Public array mismatch: '+name+'/'+field)
                        record['equal_arrays'] += 1
        left, right = (json.loads((path/'result.json').read_text(encoding='utf-8')) for path in (expected, actual))
        variable = {'timing_seconds', 'descriptor_sha256'}
        if {k: v for k, v in left.items() if k not in variable} != {k: v for k, v in right.items() if k not in variable}:
            raise RuntimeError('Public physical result metadata differs')
        if perf_counter()-started > 120:
            raise RuntimeError('Public replay elapsed budget exceeded')
        record.update(status='pass', result_sha256=digest(actual/'result.json'), cli_log_sha256=digest(args.output/'cli.log'),
            metadata_comparison='All fields except timing and consequent descriptor hash')
    except Exception as error:
        record.update(status='fail', error=repr(error))
        raise
    finally:
        record.update(elapsed_seconds=perf_counter()-started, peak_sampled_child_tree_RSS_bytes=peak)
        with (args.output/'replay_receipt.json').open('x', encoding='utf-8', newline='\n') as output:
            json.dump(record, output, indent=2)
            output.write('\n')
    print(json.dumps({key: record[key] for key in ('status', 'equal_arrays', 'elapsed_seconds', 'peak_sampled_child_tree_RSS_bytes')}))


if __name__ == '__main__':
    main()
