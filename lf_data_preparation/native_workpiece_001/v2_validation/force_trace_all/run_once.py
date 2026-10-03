"""One saved-state V2 force trace; no solver, derivative or HP call."""
from pathlib import Path
import inspect
import json
import sys
import traceback

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT/'hf_repo/src'))
import numpy as np
from hf_eval import compensated_invariants as ci
from hf_eval import split_kernel_invariants_hu as kernel
from hf_eval.split_kernel_invariants_hu import batch_response_split_numpy
from hf_eval.tmc_kernel import KernelError

original_finish = ci._finish
range_roots = []


def finish(high, low, valid, xp):
    global range_roots
    result = original_finish(high, low, valid, xp)
    if xp is np and any(np.any(np.asarray(valid) & np.isfinite(high) & np.isfinite(low) & ~np.isfinite(x)) for x in result):
        caller = inspect.currentframe().f_back
        arrays = dict(high=high, low=low, valid=valid, result_hi=result[0], result_lo=result[1])
        for name in ('a', 'b'):
            value = caller.f_locals.get(name)
            if isinstance(value, tuple):
                arrays.update({name+str(i): part for i, part in enumerate(value)})
            elif isinstance(value, np.ndarray):
                arrays[name] = value
        np.savez(HERE/f'range_root_{len(range_roots):03d}.npz', **arrays)
        range_roots.append(dict(caller=caller.f_code.co_name, caller_line=caller.f_lineno,
            stack=[dict(file=str(Path(item.filename).relative_to(ROOT)), line=item.lineno,
                        function=item.name, text=item.line) for item in traceback.extract_stack()[:-1]]))
    return result


with np.load(HERE.parent/'captured_check/candidate/fixture.npz', allow_pickle=False) as archive:
    fixture = {name: archive[name] for name in archive.files}
ci._finish = finish
original_response = kernel._response
def response(*args):
    value, fields = original_response(*args)
    np.savez(HERE/'raw_response.npz', **fields)
    return value, fields
kernel._response = response
try:
    batch_response_split_numpy(fixture['lift'][fixture['edofs']], fixture['fluctuation'][fixture['edofs']],
        {name: fixture[name] for name in ('grad', 'hessian', 'weights', 'points')},
        fixture['lam'], fixture['mu'], float(fixture['kr']))
except KernelError as error:
    report = dict(status='first_rejected_force_captured', error=dict(code=error.code, message=str(error)),
        force_started=1, force_completed=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        range_roots=range_roots, qualification=False)
    (HERE/'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
else:
    raise RuntimeError('Expected failed saved force was not reproduced; no qualification')
