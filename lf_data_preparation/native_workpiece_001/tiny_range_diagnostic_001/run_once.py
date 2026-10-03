"""Stop at the first rejected force; observe arithmetic without changing it."""
from pathlib import Path
import inspect
import json
import sys
import traceback

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'hf_repo/src'))
import numpy as np
from hf_eval import compensated_invariants as ci, native_mean
from hf_eval.displacement import DisplacementSettings
from hf_eval.tmc_kernel import KernelError

SOURCE = HERE.parent/'tiny_cycle_diagnostic_001'
task = json.loads((SOURCE/'task.json').read_text(encoding='utf-8'))
original_finish, original_force = ci._finish, native_mean._assemble_force
first_bad = None
counts = dict(force_started=0, force_completed=0, accepted=[])


class FirstRejectedForce(BaseException):
    pass


def finish(high, low, valid, xp):
    global first_bad
    result = original_finish(high, low, valid, xp)
    if first_bad is None and xp is np and not all(np.isfinite(x).all() for x in result):
        caller = inspect.currentframe().f_back
        arrays = dict(high=high, low=low, valid=valid, result_hi=result[0], result_lo=result[1])
        for name in ('a', 'b'):
            value = caller.f_locals.get(name)
            if isinstance(value, tuple):
                arrays.update({name+str(i): part for i, part in enumerate(value)})
            elif isinstance(value, np.ndarray):
                arrays[name] = value
        np.savez(HERE/'first_bad_primitive.npz', **arrays)
        first_bad = dict(caller=caller.f_code.co_name, caller_line=caller.f_lineno,
            stack=[dict(file=str(Path(item.filename).relative_to(ROOT)), line=item.lineno,
                        function=item.name, text=item.line) for item in traceback.extract_stack()[:-1]],
            operand_min=ci.OPERAND_MIN, operand_max=ci.OPERAND_MAX)
    return result


def force(model, state):
    counts['force_started'] += 1
    try:
        result = original_force(model, state)
    except KernelError as error:
        np.savez(HERE/'rejected_state.npz', lift=state.lift, fluctuation=state.fluctuation,
                 edofs=model.edofs, grad=model.ops['grad'], hessian=model.ops['hessian'],
                 weights=model.ops['weights'], lam=model.lam, mu=model.mu, kr=model.kr)
        report = dict(status='first_rejected_force_captured', qualification=False,
            error=dict(code=error.code, message=str(error), details=error.details),
            counts=counts, first_bad_primitive=first_bad)
        (HERE/'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        raise FirstRejectedForce from error
    counts['force_completed'] += 1
    return result


def accepted(snapshot):
    counts['accepted'].append(dict(d=snapshot.record['d'], state_sha256=snapshot.record['state_sha256']))


ci._finish, native_mean._assemble_force = finish, force
try:
    native_mean.solve_native_mean(SOURCE/'inputs/geometry.json', task, task['path']['targets_mm'],
        settings=DisplacementSettings(minimum_increment=.0005/16, time_limit_seconds=15.), on_accept=accepted)
except FirstRejectedForce:
    print((HERE/'result.json').read_text(encoding='utf-8'))
else:
    raise RuntimeError('Expected rejected force was not encountered; no diagnostic qualification')
