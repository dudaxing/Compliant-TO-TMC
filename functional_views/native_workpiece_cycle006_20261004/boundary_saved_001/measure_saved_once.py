"""One saved-geometry window; wrap the unchanged reader with resource checks."""
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
import hashlib
import json
import runpy
import sys

STARTED = perf_counter()
STAGE = Path(__file__).resolve().parent
ROOT = next(p for p in STAGE.parents if (p/'hf_repo').is_dir())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
REPORT = STAGE/'measurement_receipt.json'

def main():
    import psutil
    sys.path.insert(0, str(ROOT/'hf_repo/src'))
    from hf_eval import boundary_geometry
    protocol = json.loads((STAGE/'protocol.json').read_text(encoding='utf-8'))
    assert not REPORT.exists() and all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
    original = boundary_geometry.measure_native_workpiece_boundaries
    peak, calls, completed = 0, 0, 0
    record = dict(status='running', invocations=1, force_calls=0, tangent_calls=0, solver_calls=0,
                  HP_calls=0, scope='Saved accepted-state unsigned Q1 geometry only; no new mechanics or contact qualification')
    def checkpoint():
        nonlocal peak
        memory = psutil.Process().memory_info()
        peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
        if perf_counter()-STARTED > 120 or peak > 8*1024**3 or (STAGE/'stop_requested.txt').exists():
            raise RuntimeError('Saved geometry resource window closed')
    def measured(*args, **kwargs):
        nonlocal calls, completed
        calls += 1
        checkpoint()
        value = original(*args, **kwargs)
        completed += 1
        checkpoint()
        return value
    boundary_geometry.measure_native_workpiece_boundaries = measured
    try:
        sys.argv = [str(ROOT/'hf_repo/scripts/measure_native_workpiece_boundaries.py'),
                    '--input',str(ROOT/protocol['input_directory']), '--output',str(STAGE/'measurement_001')]
        try:
            runpy.run_path(sys.argv[0], run_name='__main__')
        except SystemExit as terminal:
            if terminal.code not in (None, 0):
                raise RuntimeError('Saved geometry CLI failed: '+str(terminal.code)) from terminal
        checkpoint()
        assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
        assert calls == completed == protocol['expected_geometry_calls']
        record.update(status='pass', all_bindings_unchanged=True,
            measurement_sha256=sha(STAGE/'measurement_001/boundary_measurements.json'))
    except BaseException as error:
        record.update(status='not_pass', error=repr(error))
        raise
    finally:
        boundary_geometry.measure_native_workpiece_boundaries = original
        record.update(geometry_calls_started=calls, geometry_calls_completed=completed,
            hook_restored=boundary_geometry.measure_native_workpiece_boundaries is original,
            elapsed_seconds=perf_counter()-STARTED, peak_sampled_RSS_bytes=peak,
            completed_utc=datetime.now(timezone.utc).isoformat())
        with REPORT.open('x',encoding='utf-8') as stream:
            json.dump(record,stream,indent=2)
            stream.write('\n')
    print(json.dumps(record))

if __name__ == '__main__':
    main()
