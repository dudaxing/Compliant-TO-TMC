"""Explicit two-component prescribed motion, with the original HF4 stopping gates."""
from __future__ import annotations

from copy import deepcopy
from math import fsum
import hashlib
from time import perf_counter
from typing import Callable

import numpy as np
from .displacement import _check_support, _positive_scalar, _vector
from .prescribed import PrescribedSettings, _inputs, _linear_step
from .tmc import TMCModel, TMCError
from .tmc_kernel import KernelError
from .split_state import SplitDisplacement
from .split_kernel import assemble_split

STATE_SCHEMA = "split_displacement_v1"
LIFT_SCHEME = "normal_geometric_piecewise_v1"


def state_hash(state):
    """Bind schema, shape and the two actual little-endian binary64 arrays."""
    h = hashlib.sha256(STATE_SCHEMA.encode("ascii"))
    h.update(np.asarray([state.ndof], dtype="<i8").tobytes())
    for array in (state.lift, state.fluctuation):
        h.update(np.asarray(array, dtype="<f8").tobytes())
    return h.hexdigest()


def normal_lift_shape(problem):
    """Geometry-only lift; no material, force or equilibrium reference input."""
    y = problem.model.coordinates[:, 1]
    g = problem.task["geometry"]
    H1, gap = g["lower_height_mm"], g["gap_mm"]
    shape = np.zeros(problem.model.ndof)
    shape[1::2] = np.where(y <= H1, 1., np.where(y >= H1 + gap, 0., (H1 + gap - y) / gap))
    if not np.array_equal(shape[problem.model.fixed_dofs], problem.direction[problem.model.fixed_dofs]):
        raise TMCError("geometric lift does not match prescribed motion", code="constraint_conflict")
    shape.setflags(write=False)
    return shape


def split_linear_measurement(state, vector, offset=0.0):
    """Accurate summation of a linear measurement; no rounded display state."""
    vector = _vector(vector, state.ndof, "measurement_vector")
    values = [float(offset)]
    values.extend(float(a)*float(b) for a, b in zip(vector, state.lift))
    values.extend(float(a)*float(b) for a, b in zip(vector, state.fluctuation))
    value = fsum(values)
    if not np.isfinite(value):
        raise TMCError("split measurement is nonfinite", code="nonfinite")
    return value


def solve_split_prescribed_path(model: TMCModel, base, direction, lift_shape, targets, *, reaction_groups=None,
                          settings=None, force_scale_per_length, on_accept: Callable | None = None):
    """Equilibrate two stored displacement components at prescribed targets.

    The actual state is D(lift)+D(fluctuation). The target lift is the actual
    binary64 base+d*lift_shape. Fixed fluctuation is zero. Only fluctuation
    is corrected. This entry has no implicit rebase, no analytic solution
    initialization, and no access to LF. Old U-only APIs retain their meaning.
    """
    settings = PrescribedSettings() if settings is None else settings
    if not isinstance(settings, PrescribedSettings):
        raise TMCError("settings must be PrescribedSettings", code="invalid_settings")
    base, direction, groups = _inputs(model, base, direction, reaction_groups)
    lift_shape = _vector(lift_shape, model.ndof, "lift_shape")
    if not np.array_equal(lift_shape[model.fixed_dofs], direction[model.fixed_dofs]):
        raise TMCError("lift shape must match prescribed direction on fixed DOFs", code="constraint_conflict")
    force_scale_per_length = _positive_scalar(force_scale_per_length, "force_scale_per_length")
    raw = np.asarray(targets)
    if raw.ndim != 1 or not len(raw):
        raise TMCError("targets must be a nonempty vector", code="invalid_input")
    levels = _vector(targets, len(raw), "targets")
    if np.any(levels < 0) or np.any(np.diff(levels) <= 0):
        raise TMCError("targets must be nonnegative and strictly increasing", code="invalid_input")
    if np.any(base) and levels[0] != 0:
        raise TMCError("nonzero base requires first target zero", code="invalid_input")
    if on_accept is not None and not callable(on_accept):
        raise TMCError("on_accept must be callable", code="invalid_input")
    started = perf_counter()
    state_u, state_d, state_K = SplitDisplacement(base, np.zeros(model.ndof)), 0.0, None
    failed_candidate = None
    last_correction = None
    accepted, trials, failures, linear_solves, base_checks = [], [], [], [], []
    failure, max_depth_used = None, 0
    times = {"kernel_and_transfer": 0.0, "assembly": 0.0, "sparse_solve": 0.0,
             "all_assembly_attempts_wall": 0.0, "callback": 0.0,
             "first_kernel_including_compile": None, "kernel_calls": 0,
             "successful_kernel_calls": 0, "newton_base_checks": 0, "predictors": 0}

    def check_time():
        if perf_counter() - started > settings.time_limit_seconds:
            raise TMCError("prescribed path wall-time budget exceeded", code="time_limit")

    def prescribed_values(d):
        with np.errstate(over="ignore", invalid="ignore"):
            values = base[model.fixed_dofs] + d * direction[model.fixed_dofs]
        if not np.all(np.isfinite(values)):
            raise TMCError("prescribed displacement overflowed", code="nonfinite")
        return values

    def impose(w, d):
        try:
            result = np.array(w, dtype=np.float64, copy=True)
            result[model.fixed_dofs] = 0.0
            with np.errstate(over="ignore", invalid="ignore"):
                lift = base + d * lift_shape
            return SplitDisplacement(lift, result)
        except (ValueError, OverflowError) as error:
            raise TMCError("invalid split candidate: " + str(error), code="nonfinite") from error

    def evaluate(u, tangent):
        check_time()
        begin = perf_counter()
        times["kernel_calls"] += 1
        try:
            K, internal, values = assemble_split(model, u, tangent=tangent)
        finally:
            times["all_assembly_attempts_wall"] += perf_counter() - begin
        for key in ("kernel_and_transfer", "assembly"):
            times[key] += values["timing_seconds"][key]
        if times["first_kernel_including_compile"] is None:
            times["first_kernel_including_compile"] = values["timing_seconds"]["kernel_and_transfer"]
        times["successful_kernel_calls"] += 1
        if not np.all(np.isfinite(internal)):
            raise TMCError("internal force is nonfinite", code="nonfinite")
        if not np.all(np.isfinite(values["J"])) or np.any(values["J"] <= 0):
            raise TMCError("all determinants must be finite and positive", code="invalid_J")
        check_time()
        return K, internal, values

    def force_state(u, target, internal):
        free_norm = float(np.linalg.norm(internal[model.free]))
        fixed_norm = float(np.linalg.norm(internal[model.fixed_dofs]))
        dscale = max(abs(target), settings.displacement_scale_floor)
        floor = settings.force_scale_floor_factor * force_scale_per_length * dscale
        scale = max(free_norm, fixed_norm, floor)
        # Fixed fluctuation is zero by construction; no rounded display vector
        # enters this check. Independent HP compares to the ideal base+d*motion.
        error = float(np.max(np.abs((u.lift[model.fixed_dofs] - prescribed_values(target))
                                   + u.fluctuation[model.fixed_dofs]), initial=0.))
        if not all(np.isfinite(v) for v in (free_norm, fixed_norm, scale, error, floor)) or scale <= 0:
            raise TMCError("residual/constraint normalization is nonfinite", code="nonfinite")
        return {"d": float(target), "relative_residual": free_norm / scale,
                "free_force_residual_norm": free_norm, "internal_free_norm": free_norm,
                "reaction_fixed_norm": fixed_norm, "residual_scale": scale,
                "force_scale_floor": floor, "displacement_scale": dscale,
                "prescribed_displacement_error_max": error,
                "constraint_bound": settings.constraint_tolerance * dscale}

    def measurements(vector, internal, material, regularization, fields):
        local_motion = vector[model.edofs]
        constraint = float(vector[model.fixed_dofs] @ internal[model.fixed_dofs])
        material_constraint = float(vector[model.fixed_dofs] @ material[model.fixed_dofs])
        regularization_constraint = float(vector[model.fixed_dofs] @ regularization[model.fixed_dofs])
        virtual = float(np.sum(fields["residual"] * local_motion))
        material_virtual = float(np.sum(fields["material_residual"] * local_motion))
        regularization_virtual = float(np.sum(fields["regularization_residual"] * local_motion))
        result = {"constraint_force": constraint, "model_force": -constraint,
                  "material_constraint_force": material_constraint,
                  "regularization_constraint_force": regularization_constraint,
                  "virtual_work_generalized_force": virtual,
                  "material_virtual_work_generalized_force": material_virtual,
                  "regularization_virtual_work_generalized_force": regularization_virtual,
                  "reaction_virtual_work_difference": constraint - virtual}
        if not all(np.isfinite(v) for v in result.values()):
            raise TMCError("group reaction or virtual work is nonfinite", code="nonfinite")
        return result

    def metrics(u, target, internal, fields):
        measured = force_state(u, target, internal)
        material = np.bincount(model.edofs.ravel(), weights=fields["material_residual"].ravel(), minlength=model.ndof)
        regularization = np.bincount(model.edofs.ravel(), weights=fields["regularization_residual"].ravel(), minlength=model.ndof)
        energy = fields["material_energy"].copy()
        if not all(np.all(np.isfinite(v)) for v in (material, regularization, energy)):
            raise TMCError("component force or material energy is nonfinite", code="nonfinite")
        reaction = np.zeros(model.ndof)
        reaction[model.fixed_dofs] = internal[model.fixed_dofs]
        material_reaction, regularization_reaction = np.zeros(model.ndof), np.zeros(model.ndof)
        material_reaction[model.fixed_dofs] = material[model.fixed_dofs]
        regularization_reaction[model.fixed_dofs] = regularization[model.fixed_dofs]
        drive = measurements(direction, internal, material, regularization, fields)
        group_values = {name: measurements(v, internal, material, regularization, fields) for name, v in groups.items()}
        balance = reaction.reshape(-1, 2).sum(axis=0)
        balance_scale = max(float(np.linalg.norm(reaction)), measured["residual_scale"])
        J = fields["J"]
        measured.update({
            "drive_force": drive["constraint_force"], "drive_force_model_on_device": drive["model_force"],
            "material_drive_force": drive["material_constraint_force"],
            "regularization_drive_force": drive["regularization_constraint_force"],
            "drive_virtual_work_generalized_force": drive["virtual_work_generalized_force"],
            "drive_measurement": drive, "group_reactions": group_values,
            "internal_force": internal.copy(), "force_residual": internal.copy(),
            "material_internal_force": material, "regularization_internal_force": regularization,
            "support_reaction": reaction, "material_support_reaction": material_reaction,
            "regularization_support_reaction": regularization_reaction,
            "element_internal_force": fields["residual"].copy(),
            "element_material_force": fields["material_residual"].copy(),
            "element_regularization_force": fields["regularization_residual"].copy(),
            "J": J.copy(), "minimum_J": float(np.min(J)),
            "solid_minimum_J": float(np.min(J[model.solid])) if np.any(model.solid) else None,
            "medium_minimum_J": float(np.min(J[~model.solid])) if np.any(~model.solid) else None,
            "material_energy": energy, "solid_material_energy": float(np.sum(energy[model.solid])),
            "medium_material_energy": float(np.sum(energy[~model.solid])),
            "prescribed_values": prescribed_values(target).copy(),
            "global_force_balance": balance, "global_force_balance_scale": balance_scale,
            "relative_global_force_balance": float(np.linalg.norm(balance)) / balance_scale,
        })
        if "F" in fields:
            measured["F"] = fields["F"].copy()
        if not all(np.isfinite(measured[k]) for k in
                   ("solid_material_energy", "medium_material_energy", "global_force_balance_scale", "relative_global_force_balance")):
            raise TMCError("integrated state values are nonfinite", code="nonfinite")
        return measured

    def linear_step(K, rhs, *, phase, target, iteration=None):
        check_time()
        matrix = K[model.free][:, model.free].tocsc()
        begin = perf_counter()
        try:
            step, diagnostic = _linear_step(matrix, rhs, phase=phase, target=target, iteration=iteration)
        finally:
            times["sparse_solve"] += perf_counter() - begin
        linear_solves.append(diagnostic)
        check_time()
        return step

    def newton(start_u, start_d, start_K, target):
        nonlocal failed_candidate, last_correction
        failed_candidate, last_correction = None, None
        # Direct parameter advance. Do NOT first subtract the lift difference
        # from w: the full K*delta_lift predictor already accounts for it.
        candidate = impose(start_u.fluctuation, target)
        if target != start_d:
            K = start_K
            if K is None:
                K, _, _ = evaluate(start_u, True)
            delta_lift = candidate.lift - start_u.lift
            rhs = -(K @ delta_lift)[model.free]
            step = linear_step(K, rhs, phase="predictor", target=target)
            trial_w = start_u.fluctuation.copy()
            trial_w[model.free] += step
            candidate = impose(trial_w, target)
            times["predictors"] += 1
        for iteration in range(1, settings.max_checks + 1):
            # A direction belongs only to the base on which it was computed.
            # If this new base fails before a solve, no old direction is saved.
            last_correction = None
            failed_candidate = {"d": float(target), "u_lift": candidate.lift.copy(),
                                "u_fluctuation": candidate.fluctuation.copy(),
                                "state_representation": STATE_SCHEMA,
                                "state_sha256": state_hash(candidate), "newton_check": iteration}
            K, internal, fields = evaluate(candidate, True)
            times["newton_base_checks"] += 1
            measured = force_state(candidate, target, internal)
            base_checks.append({**measured, "newton_check": iteration, "minimum_J": float(np.min(fields["J"])),
                                "state_sha256": state_hash(candidate)})
            if (measured["relative_residual"] <= settings.tolerance
                    and measured["prescribed_displacement_error_max"] <= measured["constraint_bound"]):
                measured = metrics(candidate, target, internal, fields)
                measured["newton_checks"] = iteration
                return candidate, K, measured
            if measured["prescribed_displacement_error_max"] > measured["constraint_bound"]:
                raise TMCError("prescribed displacement constraint failed", code="constraint_failure",
                               details={"d": target, "error_max": measured["prescribed_displacement_error_max"]})
            if iteration == settings.max_checks:
                raise TMCError("Newton base-check limit reached", code="newton_limit",
                               details={"d": target, "relative_residual": measured["relative_residual"]})
            r = internal[model.free]
            step = linear_step(K, -r, phase="corrector", target=target, iteration=iteration)
            last_correction = np.zeros(model.ndof)
            last_correction[model.free] = step
            scale = measured["residual_scale"]
            phi = .5 * float(np.dot(r / scale, r / scale))
            accepted_trial = False
            for backtrack in range(settings.max_backtracks + 1):
                factor = 2. ** (-backtrack)
                trial = candidate.fluctuation.copy()
                trial[model.free] += factor * step
                record = {"target_displacement": float(target), "newton_check": iteration,
                          "factor": factor, "fixed_residual_scale": scale, "base_phi": phi,
                          "accepted": False, "minimum_J": None, "phi": None,
                          "base_state_sha256": state_hash(candidate),
                          "changed_free_fluctuations": int(np.count_nonzero(trial[model.free] != candidate.fluctuation[model.free]))}
                try:
                    trial = impose(trial, target)
                    record["trial_state_sha256"] = state_hash(trial)
                    _, trial_internal, trial_fields = evaluate(trial, False)
                    state = force_state(trial, target, trial_internal)
                    trial_r = trial_internal[model.free]
                    trial_phi = .5 * float(np.dot(trial_r / scale, trial_r / scale))
                    if not np.isfinite(trial_phi):
                        raise TMCError("trial merit is nonfinite", code="nonfinite")
                    record.update(minimum_J=float(np.min(trial_fields["J"])), phi=trial_phi,
                                  recomputed_trial_scale=state["residual_scale"],
                                  prescribed_displacement_error_max=state["prescribed_displacement_error_max"])
                    if trial_phi <= (1 - 2 * settings.armijo_c * factor) * phi:
                        record["accepted"] = accepted_trial = True
                        candidate = trial
                    else:
                        record["reason"] = "armijo_insufficient_decrease"
                except (KernelError, TMCError) as error:
                    if getattr(error, "code", None) == "time_limit":
                        raise
                    record["reason"] = getattr(error, "code", "trial_error")
                    record["details"] = deepcopy(getattr(error, "details", {}))
                trials.append(record)
                if accepted_trial:
                    break
            if not accepted_trial:
                raise TMCError("all bounded backtracking factors rejected", code="backtracking_failed",
                               details={"d": target, "newton_check": iteration})
        raise AssertionError("unreachable")

    def advance(target, depth, original_target):
        nonlocal state_u, state_d, state_K, max_depth_used
        before_u, before_d, before_K = state_u.copy(), state_d, state_K
        max_depth_used = max(max_depth_used, depth)
        try:
            solved, solved_K, measured = newton(before_u, before_d, state_K, target)
        except (KernelError, TMCError) as error:
            assert (np.array_equal(state_u.lift, before_u.lift)
                    and np.array_equal(state_u.fluctuation, before_u.fluctuation)
                    and state_d == before_d and state_K is before_K)
            code = getattr(error, "code", "numerical_failure")
            failures.append({"from_displacement": before_d, "attempted_displacement": float(target),
                             "depth": depth, "code": code, "reason": str(error),
                             "details": deepcopy(getattr(error, "details", {})), "rollback_bitwise_equal": True})
            increment = target - before_d
            if (code in ("time_limit", "constraint_failure") or depth >= settings.max_bisections
                    or increment / 2 < settings.minimum_increment * (1 - 1e-12)):
                raise
            midpoint = before_d + increment / 2
            advance(midpoint, depth + 1, original_target)
            advance(target, depth + 1, original_target)
            return
        state_u, state_d, state_K = solved.copy(), float(target), solved_K
        record = {**measured, "u_lift": solved.lift.copy(), "u_fluctuation": solved.fluctuation.copy(),
                  "u_display": solved.u_display, "state_representation": STATE_SCHEMA,
                  "state_sha256": state_hash(solved), "original_target_displacement": float(original_target),
                  "is_original_target": bool(target == original_target), "bisection_depth": depth,
                  "elapsed_seconds": perf_counter() - started}
        accepted.append(record)
        if on_accept is not None:
            begin = perf_counter()
            try:
                on_accept(deepcopy(record))
            except OSError as error:
                raise TMCError(str(error), code="persistence_failure",
                               details={"last_equilibrated_displacement": state_d}) from error
            finally:
                times["callback"] += perf_counter() - begin
            check_time()

    try:
        _check_support(model)
        for target in levels:
            advance(float(target), 0, float(target))
    except (KernelError, TMCError) as error:
        failure = {"code": getattr(error, "code", "numerical_failure"), "reason": str(error),
                   "details": deepcopy(getattr(error, "details", {}))}
    times["total"] = perf_counter() - started
    last = accepted[-1] if accepted else None
    return {"status": "success" if failure is None else "failed", "target_reached": failure is None,
            "target_displacement": float(levels[-1]), "reached_displacement": state_d,
            "u_lift": state_u.lift.copy(), "u_fluctuation": state_u.fluctuation.copy(),
            "u_display": state_u.u_display, "state_representation": STATE_SCHEMA,
            "drive_force": last["drive_force"] if last is not None else None,
            "target_metrics": deepcopy(last) if failure is None else None,
            "last_accepted_state": deepcopy(last), "failure": failure, "accepted_steps": accepted,
            "trials": trials, "failed_attempts": failures, "newton_history": base_checks,
            "linear_solve_diagnostics": linear_solves, "maximum_bisection_depth": max_depth_used,
            "last_attempt_candidate": deepcopy(failed_candidate) if failure is not None else None,
            "last_corrector": last_correction.copy() if failure is not None and last_correction is not None else None,
            "lift_shape": lift_shape.copy(),
            "timing_seconds": times, "base": base.copy(), "direction": direction.copy(),
            "reaction_groups": {name: value.copy() for name, value in groups.items()},
            "force_scale_per_length": force_scale_per_length,
            "reference_state": "undeformed" if not np.any(base) else "prescribed_base_at_zero_target",
            "constraint_force_sign": "apparatus_on_model", "external_nodal_loads": "none",
            "scope": "split-state affine Dirichlet numerical path; requires independent precision and physical validation"}
