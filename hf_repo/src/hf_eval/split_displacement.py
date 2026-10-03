"""Average-port control of split mechanics with an explicit affine lift.

The unknowns are free fluctuation and actuator multiplier. Individual port
nodes are not tied. The residual/Jacobian, force scale, Armijo and bisection
policies are those of the HF3 average controller; the default kernel is unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from math import fma, fsum
from time import perf_counter

import numpy as np

from .displacement import (DisplacementSettings, _check_support, _inputs, _kkt,
                           _linear_solve, _positive_scalar, _vector)
from .split_affine import _bitwise_equal
from .split_kernel import assemble_split
from .split_prescribed import STATE_SCHEMA, state_hash
from .split_state import SplitDisplacement
from .tmc import TMCError
from .tmc_kernel import KernelError


def _dot(arrays, vector, *offsets):
    """Compensate product rounding before summation and target subtraction."""
    terms = list(offsets)
    try:
        for array in arrays:
            for i in np.flatnonzero(vector):
                a, b = float(vector[i]), float(array[i])
                product = a*b
                terms.extend((product, fma(a, b, -product)))
        result = fsum(terms)
    except (ValueError, OverflowError) as error:
        raise TMCError("split port measurement is nonfinite", code="nonfinite") from error
    if not np.isfinite(result):
        raise TMCError("split port measurement is nonfinite", code="nonfinite")
    return result


def split_average_measurement(state, vector, *offsets):
    """Return compensated b·lift+b·fluctuation+offsets, rounded only at exit.

    Include negative target terms here for a constraint residual; do not first
    round the mean and then subtract its target. FMA product compensation is
    for the ordinary bounded mechanical range, not arbitrary-precision algebra.
    """
    if not isinstance(state, SplitDisplacement):
        raise TMCError("state must be SplitDisplacement", code="invalid_input")
    vector = _vector(vector, state.ndof, "measurement_vector")
    return _dot((state.lift, state.fluctuation), vector, *offsets)


def solve_split_displacement_path(model, b_in, b_out, targets, k_out=0., *,
                                 lift_origin=None, lift_shape=None, target_origin=0.,
                                 initial_state=None, initial_R=0., settings=None,
                                 force_scale_per_length, assembler=None, on_accept=None):
    """Solve fint(L,w)+k*b_out*q_out-b_in*R=0 and b_in·(L+w)=d0+s.

    Targets are nonnegative stage parameters s, starting at zero. The actual
    lift is stored binary64 origin+s*shape; the mean target is the exact sum
    D(target_origin)+D(s). Both lift arrays default to zero. Physical fixed DOFs
    remain zero. A warm start must match the supplied origin bit for bit;
    its multiplier and target offset are explicit. No rebase or display array
    enters mechanics, measurements, feasibility or initialization.
    """
    settings = DisplacementSettings() if settings is None else settings
    if not isinstance(settings, DisplacementSettings):
        raise TMCError("settings must be DisplacementSettings", code="invalid_settings")
    b_in, b_out, k_out = _inputs(model, b_in, b_out, k_out)
    force_scale_per_length = _positive_scalar(force_scale_per_length, "force_scale_per_length")
    target_origin = _positive_scalar(target_origin, "target_origin", allow_zero=True)
    initial_R = float(_vector([initial_R], 1, "initial_R")[0])
    raw = np.asarray(targets)
    if raw.ndim != 1 or not len(raw):
        raise TMCError("targets must be a nonempty vector", code="invalid_input")
    levels = _vector(targets, len(raw), "targets")
    if levels[0] != 0 or np.any(np.diff(levels) <= 0):
        raise TMCError("stage targets must start at zero and strictly increase", code="invalid_input")
    lift_origin = _vector(np.zeros(model.ndof) if lift_origin is None else lift_origin, model.ndof, "lift_origin")
    lift_shape = _vector(np.zeros(model.ndof) if lift_shape is None else lift_shape, model.ndof, "lift_shape")
    if np.any(lift_origin[model.fixed_dofs]) or np.any(lift_shape[model.fixed_dofs]):
        raise TMCError("average-control supports must remain at zero", code="constraint_conflict")
    if initial_state is None:
        initial = SplitDisplacement(lift_origin, np.zeros(model.ndof))
    else:
        if (not isinstance(initial_state, SplitDisplacement) or initial_state.ndof != model.ndof
                or not _bitwise_equal(initial_state.lift, lift_origin)
                or np.any(initial_state.fluctuation[model.fixed_dofs])):
            raise TMCError("warm state must preserve supplied lift and fixed zero fluctuation", code="constraint_conflict")
        initial = initial_state.copy()
    assembly = assemble_split if assembler is None else assembler
    if not callable(assembly) or (on_accept is not None and not callable(on_accept)):
        raise TMCError("assembler and callback must be callable", code="invalid_input")
    started = perf_counter()
    state_u, state_R, state_s, state_K = initial.copy(), initial_R, 0., None
    accepted, trials, failures, history, linear_solves = [], [], [], [], []
    failure, maximum_depth = None, 0
    b_free = b_in[model.free]
    pivot = model.free[int(np.argmax(np.abs(b_free)))]
    times = dict(kernel_calls=0, successful_kernel_calls=0, kernel_and_transfer=0.,
                 assembly=0., sparse_solve=0., callback=0., all_assembly_attempts_wall=0.)

    def clock():
        if perf_counter()-started > settings.time_limit_seconds:
            raise TMCError("split average path wall-time budget exceeded", code="time_limit")

    def evaluate(state, tangent):
        clock()
        begin = perf_counter()
        times["kernel_calls"] += 1
        try:
            K, internal, fields = assembly(model, state, tangent=tangent)
        finally:
            times["all_assembly_attempts_wall"] += perf_counter()-begin
        times["successful_kernel_calls"] += 1
        for key in ("kernel_and_transfer", "assembly"):
            times[key] += fields["timing_seconds"][key]
        if not np.isfinite(internal).all() or not np.isfinite(fields["J"]).all():
            raise TMCError("split average fields are nonfinite", code="nonfinite")
        if np.any(fields["J"] <= 0):
            raise TMCError("all determinants must be positive", code="invalid_J")
        clock()
        return K, internal, fields

    def split_state(lift, w):
        try:
            return SplitDisplacement(lift, w)
        except (ValueError, OverflowError) as error:
            raise TMCError("split average candidate is nonfinite", code="nonfinite") from error

    def impose(w, s):
        with np.errstate(over="ignore", invalid="ignore"):
            lift = lift_origin.copy() if s == 0 else lift_origin+s*lift_shape
        return split_state(lift, w)

    def feasible(state, s):
        w = state.fluctuation.copy()
        before = _dot((state.lift, w), b_in, -target_origin, -s)
        w[pivot] -= before/b_in[pivot]
        result = split_state(state.lift, w)
        after = _dot((result.lift, result.fluctuation), b_in, -target_origin, -s)
        bound = settings.constraint_tolerance*max(abs(target_origin+s), settings.displacement_scale_floor)
        if abs(after) > bound:
            raise TMCError("split average feasibility failed", code="constraint_failure",
                           details=dict(constraint_residual=after, constraint_bound=bound))
        return result, before, after

    def measure(state, R, s, internal):
        q_in = _dot((state.lift, state.fluctuation), b_in)
        q_out = _dot((state.lift, state.fluctuation), b_out)
        actuator, spring = b_in*R, k_out*b_out*q_out
        residual = internal+spring-actuator
        dscale = max(abs(target_origin+s), settings.displacement_scale_floor)
        floor = settings.force_scale_floor_factor*force_scale_per_length*dscale
        norms = [float(np.linalg.norm(v[model.free])) for v in (internal, actuator, spring)]
        scale = max(*norms, floor)
        error = _dot((state.lift, state.fluctuation), b_in, -target_origin, -s)
        if not np.isfinite(residual).all() or not np.isfinite(scale) or scale <= 0 or not np.isfinite(R):
            raise TMCError("split average forces are nonfinite", code="nonfinite")
        return dict(d=s, physical_mean_target_mm=target_origin+s, target_origin=target_origin,
                    R_input=R, q_in=q_in, q_out=q_out, constraint_residual=error,
                    displacement_scale=dscale, constraint_bound=settings.constraint_tolerance*dscale,
                    residual_scale=scale, force_scale_floor=floor,
                    free_force_residual_norm=float(np.linalg.norm(residual[model.free])),
                    relative_residual=float(np.linalg.norm(residual[model.free]))/scale,
                    input_force=actuator, spring_force_on_structure=-spring, force_residual=residual)

    def metrics(state, R, s, internal, fields):
        measured = measure(state, R, s, internal)
        support = np.zeros(model.ndof)
        support[model.fixed_dofs] = measured["force_residual"][model.fixed_dofs]
        balance = (support+measured["input_force"]+measured["spring_force_on_structure"]).reshape(-1, 2).sum(axis=0)
        balance_scale = max(sum(float(np.linalg.norm(v)) for v in
                                (support, measured["input_force"], measured["spring_force_on_structure"])),
                            measured["residual_scale"])
        measured.update(support_reaction=support, internal_force=internal.copy(),
                        material_internal_force=np.bincount(model.edofs.ravel(), weights=fields["material_residual"].ravel(), minlength=model.ndof),
                        regularization_internal_force=np.bincount(model.edofs.ravel(), weights=fields["regularization_residual"].ravel(), minlength=model.ndof),
                        J=fields["J"].copy(), minimum_J=float(fields["J"].min()),
                        global_force_balance=balance, global_force_balance_scale=balance_scale,
                        relative_global_force_balance=float(np.linalg.norm(balance))/balance_scale,
                        output_spring_energy=.5*k_out*measured["q_out"]**2,
                        output_spring_generalized_force=-k_out*measured["q_out"])
        if not all(np.isfinite(measured[key]).all() for key in
                   ("material_internal_force", "regularization_internal_force", "global_force_balance",
                    "global_force_balance_scale", "relative_global_force_balance", "output_spring_energy",
                    "output_spring_generalized_force")):
            raise TMCError("split average component/balance metrics are nonfinite", code="nonfinite")
        return measured

    def step(K, rhs_force, rhs_mean, phase, s, iteration=None):
        clock()
        _, free, augmented = _kkt(K, model, b_in, b_out, k_out)
        begin = perf_counter()
        try:
            dw, dR, row = _linear_solve(augmented, rhs_force, rhs_mean, free, b_free,
                                      phase=phase, target=target_origin+s, newton_check=iteration)
        finally:
            times["sparse_solve"] += perf_counter()-begin
        row.update(factorization="general sparse LU", symmetrized=False, stage_parameter=s)
        linear_solves.append(row)
        clock()
        return dw, dR, row

    def newton(start, R, old_s, K, s):
        candidate = impose(start.fluctuation, s)
        if s != old_s:
            if K is None:
                K, _, _ = evaluate(start, True)
            delta_L = candidate.lift-start.lift
            delta_q_out = _dot((candidate.lift, -start.lift), b_out)
            force_rhs = -(K@delta_L+k_out*b_out*delta_q_out)[model.free]
            mean_rhs = -_dot((candidate.lift, candidate.fluctuation), b_in, -target_origin, -s)
            dw, dR, row = step(K, force_rhs, mean_rhs, "predictor", s)
            w = start.fluctuation.copy()
            w[model.free] += dw
            candidate, before, after = feasible(impose(w, s), s)
            R += dR
            row.update(mean_error_before_projection=before, mean_error_after_projection=after)
        for iteration in range(1, settings.max_checks+1):
            K, internal, fields = evaluate(candidate, True)
            measured = measure(candidate, R, s, internal)
            history.append({k: measured[k] for k in ("d", "R_input", "q_in", "q_out", "constraint_residual", "constraint_bound", "relative_residual", "residual_scale")}
                           | dict(newton_check=iteration, minimum_J=float(fields["J"].min()), state_sha256=state_hash(candidate)))
            if (measured["relative_residual"] <= settings.tolerance
                    and abs(measured["constraint_residual"]) <= measured["constraint_bound"]):
                result = metrics(candidate, R, s, internal, fields)
                result["newton_checks"] = iteration
                return candidate, R, K, result
            if abs(measured["constraint_residual"]) > measured["constraint_bound"]:
                raise TMCError("split mean constraint failed", code="constraint_failure")
            if iteration == settings.max_checks:
                raise TMCError("Newton base-check limit reached", code="newton_limit")
            r = measured["force_residual"][model.free]
            dw, dR, row = step(K, -r, -measured["constraint_residual"], "corrector", s, iteration)
            scale = measured["residual_scale"]
            phi = .5*float(np.dot(r/scale, r/scale))
            accepted_trial = False
            for backtrack in range(settings.max_backtracks+1):
                factor = 2.**(-backtrack)
                w = candidate.fluctuation.copy()
                w[model.free] += factor*dw
                trial_R = R+factor*dR
                record = dict(target_displacement=target_origin+s, stage_parameter=s, newton_check=iteration,
                              factor=factor, fixed_residual_scale=scale, base_phi=phi, accepted=False)
                try:
                    trial, before, after = feasible(impose(w, s), s)
                    _, trial_internal, trial_fields = evaluate(trial, False)
                    trial_measured = measure(trial, trial_R, s, trial_internal)
                    trial_r = trial_measured["force_residual"][model.free]
                    trial_phi = .5*float(np.dot(trial_r/scale, trial_r/scale))
                    if not np.isfinite(trial_phi):
                        raise TMCError("trial merit is nonfinite", code="nonfinite")
                    record.update(phi=trial_phi, minimum_J=float(trial_fields["J"].min()),
                                  mean_error_before_projection=before, constraint_residual=after, R_input=trial_R)
                    if trial_phi <= (1-2*settings.armijo_c*factor)*phi:
                        record["accepted"] = accepted_trial = True
                        candidate, R = trial, trial_R
                    else:
                        record["reason"] = "armijo_insufficient_decrease"
                except (KernelError, TMCError) as error:
                    if getattr(error, "code", None) == "time_limit":
                        raise
                    record["reason"] = getattr(error, "code", "trial_error")
                trials.append(record)
                if accepted_trial:
                    break
            if not accepted_trial:
                raise TMCError("all bounded backtracking factors rejected", code="backtracking_failed")
        raise AssertionError("unreachable")

    def advance(s, depth, original):
        nonlocal state_u, state_R, state_s, state_K, maximum_depth
        before, before_R, before_s, before_K = state_u.copy(), state_R, state_s, state_K
        maximum_depth = max(maximum_depth, depth)
        try:
            solved, R, K, measured = newton(before, before_R, before_s, before_K, s)
        except (KernelError, TMCError) as error:
            assert (_bitwise_equal(state_u.lift, before.lift) and _bitwise_equal(state_u.fluctuation, before.fluctuation)
                    and _bitwise_equal(np.array([state_R]), np.array([before_R])) and state_s == before_s and state_K is before_K)
            code = getattr(error, "code", "numerical_failure")
            failures.append(dict(from_displacement=before_s, attempted_displacement=s, from_R_input=before_R,
                                 depth=depth, code=code, reason=str(error), rollback_bitwise_equal=True))
            if (code in ("time_limit", "constraint_failure") or depth >= settings.max_bisections
                    or (s-before_s)/2 < settings.minimum_increment*(1-1e-12)):
                raise
            advance(before_s+(s-before_s)/2, depth+1, original)
            advance(s, depth+1, original)
            return
        state_u, state_R, state_s, state_K = solved.copy(), float(R), float(s), K
        record = dict(measured, u_lift=solved.lift.copy(), u_fluctuation=solved.fluctuation.copy(),
                      u_display=solved.u_display, state_representation=STATE_SCHEMA, state_sha256=state_hash(solved),
                      original_target_displacement=original, is_original_target=s == original,
                      bisection_depth=depth, elapsed_seconds=perf_counter()-started)
        accepted.append(record)
        if on_accept is not None:
            begin = perf_counter()
            try:
                on_accept(deepcopy(record))
            except OSError as error:
                raise TMCError(str(error), code="persistence_failure") from error
            finally:
                times["callback"] += perf_counter()-begin
        clock()

    try:
        _check_support(model)
        for s in levels:
            advance(float(s), 0, float(s))
    except (KernelError, TMCError) as error:
        failure = dict(code=getattr(error, "code", "numerical_failure"), reason=str(error))
    times["total"] = perf_counter()-started
    return dict(status="success" if failure is None else "failed", target_reached=failure is None,
                target_displacement=float(levels[-1]), reached_displacement=state_s,
                target_origin=target_origin, physical_mean_target_mm=target_origin+float(levels[-1]),
                u_lift=state_u.lift.copy(), u_fluctuation=state_u.fluctuation.copy(), u_display=state_u.u_display,
                R_input=state_R, state_representation=STATE_SCHEMA, state_sha256=state_hash(state_u),
                target_metrics=deepcopy(accepted[-1]) if failure is None else None,
                last_accepted_state=deepcopy(accepted[-1]) if accepted else None, failure=failure,
                accepted_steps=accepted, trials=trials, failed_attempts=failures, newton_history=history,
                linear_solve_diagnostics=linear_solves, maximum_bisection_depth=maximum_depth, timing_seconds=times,
                lift_origin=lift_origin.copy(), lift_shape=lift_shape.copy(), initial_u_lift=initial.lift.copy(),
                initial_u_fluctuation=initial.fluctuation.copy(), initial_R=initial_R,
                b_in=b_in.copy(), b_out=b_out.copy(), k_out=k_out, force_scale_per_length=force_scale_per_length,
                input_force_sign="actuator_on_model", lift_scheme="affine_geometric_origin_v1",
                scope="split average-port numerical path; independent HP and task validation required")
