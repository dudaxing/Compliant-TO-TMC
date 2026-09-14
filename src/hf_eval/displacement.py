"""Average-port displacement control of the actual, nonconservative TMC residual.

The actuator-on-model force is ``b_in * R_input``.  The output spring exerts
``-k_out * b_out * (b_out @ u)``.  Only the average input displacement is
constrained; individual port nodes remain free to deform.  Every path starts
from the undeformed state.  Production stopping is not independent HP approval.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from time import perf_counter
from typing import Callable

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from .tmc import TMCModel, TMCError, assemble
from .tmc_kernel import KernelError


@dataclass(frozen=True)
class DisplacementSettings:
    tolerance: float = 1e-9
    constraint_tolerance: float = 1e-10
    displacement_scale_floor: float = 1e-6
    force_scale_floor_factor: float = 1e-8
    max_checks: int = 25
    armijo_c: float = 1e-4
    max_backtracks: int = 12
    max_bisections: int = 4
    minimum_increment: float = 0.025 / 16
    time_limit_seconds: float = 1200.0

    def __post_init__(self):
        for name in ("tolerance", "constraint_tolerance", "displacement_scale_floor",
                     "force_scale_floor_factor", "armijo_c", "minimum_increment",
                     "time_limit_seconds"):
            value = getattr(self, name)
            if (isinstance(value, (bool, np.bool_, complex)) or not np.isscalar(value)
                    or not np.isrealobj(value)):
                raise TMCError(f"invalid {name}", code="invalid_settings")
            try:
                valid = np.isfinite(value) and value > 0
            except TypeError:
                valid = False
            if not valid:
                raise TMCError(f"invalid {name}", code="invalid_settings")
        if self.tolerance >= 1 or self.constraint_tolerance >= 1 or self.armijo_c >= .5:
            raise TMCError("invalid stopping/Armijo coefficient", code="invalid_settings")
        for name in ("max_checks", "max_backtracks", "max_bisections"):
            value = getattr(self, name)
            if (isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer))
                    or value < (1 if name == "max_checks" else 0)):
                raise TMCError(f"invalid {name}", code="invalid_settings")


def _vector(value, size, name):
    raw = np.asarray(value)
    if raw.shape != (size,) or np.iscomplexobj(raw) or raw.dtype.kind not in "iuf":
        raise TMCError(f"{name} must be a finite real vector of length {size}", code="invalid_input")
    result = np.array(raw, dtype=float, copy=True)
    if not np.all(np.isfinite(result)):
        raise TMCError(f"{name} must be finite", code="invalid_input")
    return result


def _positive_scalar(value, name, *, allow_zero=False):
    raw = np.asarray(value)
    if raw.ndim != 0 or raw.dtype.kind not in "iuf" or np.iscomplexobj(raw):
        raise TMCError(f"invalid {name}", code="invalid_input")
    number = float(raw)
    if not np.isfinite(number) or (number < 0 if allow_zero else number <= 0):
        raise TMCError(f"invalid {name}", code="invalid_input")
    return number


def _inputs(model, b_in, b_out, k_out):
    if not isinstance(model, TMCModel):
        raise TMCError("model must be TMCModel", code="invalid_model")
    b_in = _vector(b_in, model.ndof, "b_in")
    b_out = _vector(b_out, model.ndof, "b_out")
    k_out = _positive_scalar(k_out, "k_out", allow_zero=True)
    if not np.any(b_in[model.free]):
        raise TMCError("input average has no free DOF", code="constraint_conflict")
    if not np.any(b_out):
        raise TMCError("output vector must be nonzero", code="invalid_input")
    # Port weights and reference directions belong to the geometry/task adapter.
    # Do not silently normalize them or remove their constrained components.
    return b_in, b_out, k_out


def _check_support(model):
    rigid = np.zeros((model.ndof, 3))
    rigid[0::2, 0], rigid[1::2, 1] = 1, 1
    center = model.coordinates.mean(axis=0)
    span = max(float(np.ptp(model.coordinates, axis=0).max()), 1.0)
    rigid[0::2, 2] = -(model.coordinates[:, 1] - center[1]) / span
    rigid[1::2, 2] = (model.coordinates[:, 0] - center[0]) / span
    if len(model.fixed_dofs) < 3 or np.linalg.matrix_rank(rigid[model.fixed_dofs]) < 3:
        raise TMCError("support does not eliminate three planar rigid modes", code="insufficient_support")


def _kkt(K, model, b_in, b_out, k_out):
    output = sparse.csc_matrix(b_out[:, None])
    total = (K + k_out * (output @ output.T)).tocsc()
    total.sum_duplicates()
    free_matrix = total[model.free][:, model.free].tocsc()
    column = sparse.csc_matrix(b_in[model.free, None])
    augmented = sparse.bmat([[free_matrix, -column], [column.T, None]], format="csc")
    if not np.all(np.isfinite(augmented.data)):
        raise TMCError("KKT matrix is nonfinite", code="nonfinite")
    return total, free_matrix, augmented


def _linear_solve(augmented, rhs_force, rhs_mean, free_matrix, b_free, *, phase,
                  target, newton_check=None):
    rhs = np.r_[rhs_force, rhs_mean]
    try:
        solution = splu(augmented).solve(rhs)
    except (RuntimeError, ValueError) as error:
        raise TMCError(str(error), code="singular_tangent", details={"phase": phase}) from error
    if not np.all(np.isfinite(solution)):
        raise TMCError("KKT solution is nonfinite", code="nonfinite")
    displacement, multiplier = solution[:-1], float(solution[-1])
    force_error = free_matrix @ displacement - b_free * multiplier - rhs_force
    mean_error = float(b_free @ displacement - rhs_mean)
    residual = augmented @ solution - rhs
    force_denominator = max(float(np.linalg.norm(rhs_force)),
                            float(np.linalg.norm(free_matrix @ displacement)),
                            float(np.linalg.norm(b_free * multiplier)), np.finfo(float).tiny)
    backward_scale = float(np.linalg.norm(augmented.data) * np.linalg.norm(solution)
                           + np.linalg.norm(rhs))
    diagnostic = {
        "phase": phase, "target_displacement": float(target), "newton_check": newton_check,
        "force_block_residual_norm": float(np.linalg.norm(force_error)),
        "relative_force_block_residual": float(np.linalg.norm(force_error)) / force_denominator,
        "constraint_block_residual": mean_error,
        "normwise_backward_error": float(np.linalg.norm(residual)) / max(backward_scale, np.finfo(float).tiny),
        "matrix_norm": "Frobenius", "vector_norm": "Euclidean",
        "mixed_unit_backward_error_is_diagnostic_only": True,
    }
    return displacement, multiplier, diagnostic


def _matrix_diagnostics(K0, total, augmented, model):
    initial = K0[model.free][:, model.free]
    free_total = total[model.free][:, model.free]
    denominator = max(float(np.linalg.norm(free_total.data)), np.finfo(float).tiny)
    return {
        "n_dof": model.ndof, "free_dof_count": len(model.free),
        "fixed_dof_count": len(model.fixed_dofs), "element_count": model.ne,
        "K0_free_frobenius": float(np.linalg.norm(initial.data)),
        "K_total_free_frobenius": float(np.linalg.norm(free_total.data)),
        "relative_tangent_asymmetry": float(np.linalg.norm((free_total - free_total.T).data)) / denominator,
        "KKT_shape": list(augmented.shape), "KKT_nnz": augmented.nnz,
        "factorization": "general sparse LU", "symmetrized": False,
    }


def solve_initial_tangent(model: TMCModel, b_in, b_out, k_out=0.0):
    """Return the linear unit-average-displacement solution using K(0).

    Returned sparse ``K0``/``K_total`` are full DOF matrices; ``KKT`` is free DOFs
    then the actuator multiplier.  ``u`` is a linear reference, not a finite
    deformation state: no claim of positive J at unit displacement is made.
    """
    started = perf_counter()
    b_in, b_out, k_out = _inputs(model, b_in, b_out, k_out)
    _check_support(model)
    K0, internal_zero, fields_zero = assemble(model, np.zeros(model.ndof), tangent=True)
    total, free_matrix, augmented = _kkt(K0, model, b_in, b_out, k_out)
    begin_solve = perf_counter()
    step, reaction, linear = _linear_solve(augmented, np.zeros(len(model.free)), 1.0,
                                          free_matrix, b_in[model.free], phase="initial_tangent", target=1.0)
    solve_time = perf_counter() - begin_solve
    u = np.zeros(model.ndof)
    u[model.free] = step
    imbalance = total @ u - b_in * reaction
    support = np.zeros(model.ndof)
    support[model.fixed_dofs] = imbalance[model.fixed_dofs]
    return {
        "u": u, "R_input": reaction, "q_in": float(b_in @ u), "q_out": float(b_out @ u),
        "constraint_residual": float(b_in @ u - 1.0), "support_reaction": support,
        "K0": K0, "K_total": total, "KKT": augmented,
        "internal_force_at_zero": internal_zero.copy(), "fields_at_zero": fields_zero,
        "matrix_diagnostics": _matrix_diagnostics(K0, total, augmented, model),
        "linear_solve_diagnostics": linear,
        "timing_seconds": {"sparse_solve": solve_time, "total": perf_counter() - started},
        "reference_state": "undeformed", "scope": "linear unit average displacement reference",
    }


def solve_displacement_path(model: TMCModel, b_in, b_out, targets, k_out=0.0,
                            settings=None, on_accept: Callable | None = None, *,
                            force_scale_per_length):
    """Solve ``fint + k*b_out*q_out - b_in*R = 0``, ``b_in@u = d``.

    ``force_scale_per_length`` must explicitly supply E*t in force/length units.
    The displacement floor is 1e-6 in the project's mm units unless configured.
    Trial force merit uses the fixed current scale; every accepted state gets a
    newly computed scale and a separate mean-constraint test.  Failure returns
    the last accepted state and null target metrics.  ``on_accept`` receives a
    deep copy, including arrays and nested data, and cannot mutate the solve.
    """
    settings = DisplacementSettings() if settings is None else settings
    if not isinstance(settings, DisplacementSettings):
        raise TMCError("settings must be DisplacementSettings", code="invalid_settings")
    b_in, b_out, k_out = _inputs(model, b_in, b_out, k_out)
    force_scale_per_length = _positive_scalar(force_scale_per_length, "force_scale_per_length")
    raw = np.asarray(targets)
    if raw.ndim != 1 or not len(raw):
        raise TMCError("targets must be a nonempty vector", code="invalid_input")
    levels = _vector(targets, len(raw), "targets")
    if np.any(levels < 0) or np.any(np.diff(levels) <= 0):
        raise TMCError("targets must be nonnegative and strictly increasing", code="invalid_input")
    if on_accept is not None and not callable(on_accept):
        raise TMCError("on_accept must be callable", code="invalid_input")
    started = perf_counter()
    state_u, state_R, state_d, state_K = np.zeros(model.ndof), 0.0, 0.0, None
    accepted, trials, failures, linear_solves, base_checks = [], [], [], [], []
    failure, max_depth_used = None, 0
    b_free = b_in[model.free]
    # This pivot enforces only the scalar mean, to floating-point roundoff.  It
    # never imposes a common displacement on the other port DOFs.
    pivot = model.free[int(np.argmax(np.abs(b_free)))]
    times = {"kernel_and_transfer": 0.0, "assembly": 0.0, "sparse_solve": 0.0,
             "all_assembly_attempts_wall": 0.0, "callback": 0.0,
             "first_kernel_including_compile": None, "kernel_calls": 0,
             "successful_kernel_calls": 0, "newton_base_checks": 0, "predictors": 0}

    def check_time():
        if perf_counter() - started > settings.time_limit_seconds:
            raise TMCError("displacement path wall-time budget exceeded", code="time_limit")

    def evaluate(u, tangent):
        check_time()
        begin = perf_counter()
        times["kernel_calls"] += 1
        try:
            K, internal, values = assemble(model, u, tangent=tangent)
        finally:
            times["all_assembly_attempts_wall"] += perf_counter() - begin
        timing = values["timing_seconds"]
        for key in ("kernel_and_transfer", "assembly"):
            times[key] += timing[key]
        if times["first_kernel_including_compile"] is None:
            times["first_kernel_including_compile"] = timing["kernel_and_transfer"]
        times["successful_kernel_calls"] += 1
        J = values["J"]
        if not np.all(np.isfinite(J)) or np.any(J <= 0):
            raise TMCError("all quadrature determinants must be finite and positive", code="invalid_J")
        check_time()
        return K, internal, values

    def feasible(u, target):
        result = u.copy()
        result[model.fixed_dofs] = 0.0
        before = float(b_in @ result - target)
        result[pivot] -= before / b_in[pivot]
        error = float(b_in @ result - target)
        bound = settings.constraint_tolerance * max(abs(target), settings.displacement_scale_floor)
        if not np.all(np.isfinite(result)) or not np.isfinite(error):
            raise TMCError("feasible displacement is nonfinite", code="nonfinite")
        if abs(error) > bound:
            raise TMCError("floating-point mean feasibility failed", code="constraint_failure",
                           details={"constraint_residual": error, "constraint_bound": bound})
        return result, before, error

    def force_state(u, reaction, target, internal):
        if not np.isfinite(reaction) or not np.all(np.isfinite(internal)):
            raise TMCError("state forces are nonfinite", code="nonfinite")
        q_in, q_out = float(b_in @ u), float(b_out @ u)
        actuator, spring = b_in * reaction, k_out * b_out * q_out
        imbalance = internal + spring - actuator
        d_scale = max(abs(target), settings.displacement_scale_floor)
        floor = settings.force_scale_floor_factor * force_scale_per_length * d_scale
        norms = [float(np.linalg.norm(part[model.free])) for part in (internal, actuator, spring)]
        scale = max(*norms, floor)
        numerator = float(np.linalg.norm(imbalance[model.free]))
        constraint = q_in - target
        if (not all(np.isfinite(x) for x in (q_in, q_out, scale, numerator, constraint))
                or scale <= 0 or not np.all(np.isfinite(imbalance))):
            raise TMCError("force/constraint normalization is nonfinite", code="nonfinite")
        return {"d": float(target), "R_input": float(reaction), "q_in": q_in, "q_out": q_out,
                "constraint_residual": constraint, "displacement_scale": d_scale,
                "constraint_bound": settings.constraint_tolerance * d_scale,
                "relative_residual": numerator / scale, "free_force_residual_norm": numerator,
                "residual_scale": scale, "force_scale_floor": floor,
                "internal_free_norm": norms[0], "input_free_norm": norms[1], "spring_free_norm": norms[2],
                "input_force": actuator, "spring_force_on_structure": -spring,
                "force_residual": imbalance}

    def metrics(u, reaction, target, internal, values):
        measured = force_state(u, reaction, target, internal)
        support = np.zeros(model.ndof)
        support[model.fixed_dofs] = measured["force_residual"][model.fixed_dofs]
        material = np.bincount(model.edofs.ravel(), weights=values["material_residual"].ravel(), minlength=model.ndof)
        regularization = np.bincount(model.edofs.ravel(), weights=values["regularization_residual"].ravel(), minlength=model.ndof)
        energy = values["material_energy"].copy()
        if not all(np.all(np.isfinite(x)) for x in (material, regularization, energy)):
            raise TMCError("component forces or energy are nonfinite", code="nonfinite")
        external = support + measured["input_force"] + measured["spring_force_on_structure"]
        balance = external.reshape(-1, 2).sum(axis=0)
        balance_scale = max(sum(float(np.linalg.norm(x)) for x in
                                (support, measured["input_force"], measured["spring_force_on_structure"])),
                            measured["residual_scale"])
        J = values["J"]
        measured.update({
            "support_reaction": support, "internal_force": internal.copy(),
            "material_internal_force": material, "regularization_internal_force": regularization,
            "J": J.copy(), "minimum_J": float(np.min(J)),
            "solid_minimum_J": float(np.min(J[model.solid])) if np.any(model.solid) else None,
            "medium_minimum_J": float(np.min(J[~model.solid])) if np.any(~model.solid) else None,
            "material_energy": energy, "solid_material_energy": float(np.sum(energy[model.solid])),
            "medium_material_energy": float(np.sum(energy[~model.solid])),
            "output_spring_energy": .5 * k_out * measured["q_out"] ** 2,
            "output_spring_generalized_force": -k_out * measured["q_out"],
            "global_force_balance": balance, "global_force_balance_scale": balance_scale,
            "relative_global_force_balance": float(np.linalg.norm(balance)) / balance_scale,
            "fixed_displacement_max": float(np.max(np.abs(u[model.fixed_dofs]), initial=0)),
        })
        if not all(np.isfinite(measured[key]) for key in
                   ("solid_material_energy", "medium_material_energy", "output_spring_energy",
                    "global_force_balance_scale", "relative_global_force_balance")):
            raise TMCError("state energy/balance is nonfinite", code="nonfinite")
        return measured

    def kkt_step(K, rhs_force, rhs_mean, *, phase, target, iteration=None):
        check_time()
        _, free_matrix, augmented = _kkt(K, model, b_in, b_out, k_out)
        begin = perf_counter()
        try:
            step, delta_R, record = _linear_solve(augmented, rhs_force, rhs_mean, free_matrix,
                                                  b_free, phase=phase, target=target, newton_check=iteration)
        finally:
            times["sparse_solve"] += perf_counter() - begin
        linear_solves.append(record)
        check_time()
        return step, delta_R, record

    def newton(start_u, start_R, start_d, start_K, target):
        K = start_K
        if K is None:
            K, _, _ = evaluate(start_u, True)
        candidate, reaction = start_u.copy(), float(start_R)
        if target != start_d:
            step, delta_R, predictor_record = kkt_step(K, np.zeros(len(model.free)), target - start_d,
                                                       phase="predictor", target=target)
            candidate[model.free] += step
            reaction += delta_R
            candidate, before, after = feasible(candidate, target)
            predictor_record.update(mean_error_before_projection=before, mean_error_after_projection=after)
            times["predictors"] += 1
        for iteration in range(1, settings.max_checks + 1):
            K, internal, values = evaluate(candidate, True)
            times["newton_base_checks"] += 1
            measured = force_state(candidate, reaction, target, internal)
            base_checks.append({key: measured[key] for key in
                                ("d", "R_input", "q_in", "q_out", "constraint_residual", "constraint_bound",
                                 "relative_residual", "free_force_residual_norm", "residual_scale")}
                               | {"newton_check": iteration, "minimum_J": float(np.min(values["J"]))})
            if (measured["relative_residual"] <= settings.tolerance
                    and abs(measured["constraint_residual"]) <= measured["constraint_bound"]):
                measured = metrics(candidate, reaction, target, internal, values)
                measured["newton_checks"] = iteration
                return candidate, reaction, K, measured
            if abs(measured["constraint_residual"]) > measured["constraint_bound"]:
                raise TMCError("mean constraint left feasible manifold", code="constraint_failure",
                               details={"d": target, "constraint_residual": measured["constraint_residual"]})
            if iteration == settings.max_checks:
                raise TMCError("Newton base-check limit reached", code="newton_limit",
                               details={"d": target, "relative_residual": measured["relative_residual"]})
            r = measured["force_residual"][model.free]
            step, delta_R, correction_record = kkt_step(K, -r, 0.0, phase="corrector", target=target, iteration=iteration)
            correction_record["mean_correction"] = float(b_free @ step)
            # Hold S_F fixed during this line search.  The multiplier is updated
            # with the same factor as u; g is separately constrained throughout.
            scale = measured["residual_scale"]
            phi = .5 * float(np.dot(r / scale, r / scale))
            accepted_trial = False
            for backtrack in range(settings.max_backtracks + 1):
                factor = 2.0 ** (-backtrack)
                trial = candidate.copy()
                trial[model.free] += factor * step
                trial_R = reaction + factor * delta_R
                record = {"target_displacement": float(target), "newton_check": iteration,
                          "factor": factor, "fixed_residual_scale": scale, "base_phi": phi,
                          "accepted": False, "minimum_J": None, "phi": None}
                try:
                    trial, before, after = feasible(trial, target)
                    record.update(mean_error_before_projection=before, constraint_residual=after)
                    _, trial_internal, trial_fields = evaluate(trial, False)
                    trial_measured = force_state(trial, trial_R, target, trial_internal)
                    trial_r = trial_measured["force_residual"][model.free]
                    trial_phi = .5 * float(np.dot(trial_r / scale, trial_r / scale))
                    if not np.isfinite(trial_phi):
                        raise TMCError("trial merit is nonfinite", code="nonfinite")
                    record.update(minimum_J=float(np.min(trial_fields["J"])), phi=trial_phi,
                                  recomputed_trial_scale=trial_measured["residual_scale"], R_input=trial_R)
                    if trial_phi <= (1 - 2 * settings.armijo_c * factor) * phi:
                        record["accepted"] = accepted_trial = True
                        candidate, reaction = trial, trial_R
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
        nonlocal state_u, state_R, state_d, state_K, max_depth_used
        before_u, before_R, before_d = state_u.copy(), state_R, state_d
        max_depth_used = max(max_depth_used, depth)
        try:
            solved, solved_R, solved_K, measured = newton(before_u, before_R, before_d, state_K, target)
        except (KernelError, TMCError) as error:
            assert np.array_equal(state_u, before_u) and state_R == before_R and state_d == before_d
            code = getattr(error, "code", "numerical_failure")
            failures.append({"from_displacement": before_d, "attempted_displacement": float(target),
                             "from_R_input": before_R, "depth": depth, "code": code,
                             "details": deepcopy(getattr(error, "details", {})), "rollback_bitwise_equal": True})
            increment = target - before_d
            if (code in ("time_limit", "constraint_failure") or depth >= settings.max_bisections
                    or increment / 2 < settings.minimum_increment * (1 - 1e-12)):
                raise
            midpoint = before_d + increment / 2
            advance(midpoint, depth + 1, original_target)
            advance(target, depth + 1, original_target)
            return
        state_u, state_R, state_d, state_K = solved.copy(), float(solved_R), float(target), solved_K
        record = {**measured, "u": solved.copy(), "original_target_displacement": float(original_target),
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
    return {
        "status": "success" if failure is None else "failed", "target_reached": failure is None,
        "target_displacement": float(levels[-1]), "reached_displacement": state_d,
        "u": state_u.copy(), "R_input": state_R,
        "target_metrics": deepcopy(accepted[-1]) if failure is None else None,
        "last_accepted_state": deepcopy(accepted[-1]) if accepted else None, "failure": failure,
        "accepted_steps": accepted, "trials": trials, "failed_attempts": failures,
        "newton_history": base_checks, "linear_solve_diagnostics": linear_solves,
        "maximum_bisection_depth": max_depth_used, "timing_seconds": times,
        "force_scale_per_length": force_scale_per_length,
        "b_in": b_in.copy(), "b_out": b_out.copy(), "k_out": k_out,
        "reference_state": "undeformed", "input_force_sign": "actuator_on_model",
        "scope": "production numerical path; independent high-precision acceptance is separate",
    }
