"""Bounded affine Dirichlet control with work-conjugate boundary reactions.

Only ``u_D = base_D + d * direction_D`` is prescribed.  Free DOFs equilibrate
the existing TMC residual with its actual unsymmetrized Jacobian; no rigid-body
framework, average port, external load, or contact-force interpretation is
introduced.  Group vectors define explicit virtual boundary translations.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from time import perf_counter
from typing import Callable

import numpy as np
from scipy.sparse.linalg import splu

from .displacement import DisplacementSettings, _check_support, _positive_scalar, _vector
from .tmc import TMCError, TMCModel, assemble
from .tmc_kernel import KernelError


@dataclass(frozen=True)
class PrescribedSettings(DisplacementSettings):
    """Same bounded Newton controls, with a task-supplied Dirichlet increment."""
    minimum_increment: float = 1e-4


def _inputs(model, base, direction, reaction_groups):
    if not isinstance(model, TMCModel):
        raise TMCError("model must be TMCModel", code="invalid_model")
    base = _vector(base, model.ndof, "base")
    direction = _vector(direction, model.ndof, "direction")
    if np.any(base[model.free]) or np.any(direction[model.free]):
        raise TMCError("base/direction must be zero on free DOFs", code="constraint_conflict")
    if not np.any(direction[model.fixed_dofs]):
        raise TMCError("prescribed direction must move at least one fixed DOF", code="constraint_conflict")
    if reaction_groups is None:
        reaction_groups = {"drive": direction}
    if not isinstance(reaction_groups, dict):
        raise TMCError("reaction_groups must map names to full virtual-motion vectors", code="invalid_input")
    groups = {}
    for name, value in reaction_groups.items():
        if not isinstance(name, str) or not name.strip():
            raise TMCError("reaction group names must be nonempty strings", code="invalid_input")
        vector = _vector(value, model.ndof, "reaction_groups." + name)
        if np.any(vector[model.free]) or not np.any(vector[model.fixed_dofs]):
            raise TMCError("reaction group motion must be nonzero only on prescribed DOFs", code="constraint_conflict",
                           details={"group": name})
        groups[name] = vector
    return base, direction, groups


def _linear_step(Kff, rhs, *, phase, target, iteration=None):
    """General sparse LU; the zero-free-DOF case has no equilibrium unknown."""
    if not len(rhs):
        solution = np.empty(0)
    else:
        try:
            solution = splu(Kff.tocsc()).solve(rhs)
        except (RuntimeError, ValueError) as error:
            raise TMCError(str(error), code="singular_tangent", details={"phase": phase}) from error
    if not np.all(np.isfinite(solution)):
        raise TMCError("free displacement solution is nonfinite", code="nonfinite")
    error = float(np.linalg.norm(Kff @ solution - rhs))
    rhs_norm = float(np.linalg.norm(rhs))
    matrix_norm = float(np.linalg.norm(Kff.data))
    backward_scale = matrix_norm * float(np.linalg.norm(solution)) + rhs_norm
    if not all(np.isfinite(v) for v in (error, rhs_norm, matrix_norm, backward_scale)):
        raise TMCError("linear diagnostics are nonfinite", code="nonfinite")
    return solution, {
        "phase": phase, "target_displacement": float(target), "newton_check": iteration,
        "force_block_residual_norm": error,
        "relative_linear_residual": error / max(rhs_norm, np.finfo(float).tiny),
        "normwise_backward_error": error / max(backward_scale, np.finfo(float).tiny),
        "relative_tangent_asymmetry": float(np.linalg.norm((Kff - Kff.T).data)) / max(matrix_norm, np.finfo(float).tiny),
        "matrix_norm": "Frobenius", "vector_norm": "Euclidean",
        "factorization": "general sparse LU" if len(rhs) else "no free DOFs", "symmetrized": False,
    }


def solve_prescribed_path(model: TMCModel, base, direction, targets, *, reaction_groups=None,
                          settings=None, force_scale_per_length, on_accept: Callable | None = None):
    """Solve a fresh, bounded path with ``u_fixed = base + d*direction``.

    ``base`` (length) and ``direction`` (dimensionless) are full vectors, zero
    on free DOFs. A nonzero base requires an explicit first target zero, so its
    initially nonequilibrated free DOFs are solved and recorded before loading.
    There are no external nodal loads. ``force_scale_per_length`` explicitly
    supplies E*t. SF=max(norm(fint_free), norm(fint_fixed), 1e-8*E*t*dscale),
    with dscale=max(abs(d),1e-6) under the default project-mm settings.

    reaction_groups maps each name to a full dimensionless virtual boundary
    motion, zero on free DOFs. It is never normalized. Overlap is permitted for
    different measurements; global balance uses each fixed DOF only once.
    ``constraint_force`` is the apparatus-on-model generalized force. Its
    opposite ``model_force`` is model-on-apparatus. ``virtual_work_generalized_force``
    is evaluated independently by summing element residual dot virtual motion;
    it is work per unit motion (force), not accumulated path work or energy.

    Numerical failure retains the last accepted state and null target metrics.
    Callback records are deep copies; an OSError preserves the newly accepted
    state but returns persistence_failure. This routine writes no files.
    """
    settings = PrescribedSettings() if settings is None else settings
    if not isinstance(settings, PrescribedSettings):
        raise TMCError("settings must be PrescribedSettings", code="invalid_settings")
    base, direction, groups = _inputs(model, base, direction, reaction_groups)
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
    state_u, state_d, state_K = base.copy(), 0.0, None
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

    def impose(u, d):
        result = u.copy()
        result[model.fixed_dofs] = prescribed_values(d)
        if not np.all(np.isfinite(result)):
            raise TMCError("candidate displacement is nonfinite", code="nonfinite")
        return result

    def evaluate(u, tangent):
        check_time()
        begin = perf_counter()
        times["kernel_calls"] += 1
        try:
            K, internal, values = assemble(model, u, tangent=tangent)
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
        error = float(np.max(np.abs(u[model.fixed_dofs] - prescribed_values(target)), initial=0.))
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
        candidate = start_u.copy()
        if target != start_d:
            K = start_K
            if K is None:
                K, _, _ = evaluate(start_u, True)
            delta_D = prescribed_values(target) - prescribed_values(start_d)
            rhs = -(K[model.free][:, model.fixed_dofs] @ delta_D)
            step = linear_step(K, rhs, phase="predictor", target=target)
            candidate[model.free] += step
            times["predictors"] += 1
        candidate = impose(candidate, target)
        for iteration in range(1, settings.max_checks + 1):
            K, internal, fields = evaluate(candidate, True)
            times["newton_base_checks"] += 1
            measured = force_state(candidate, target, internal)
            base_checks.append({**measured, "newton_check": iteration, "minimum_J": float(np.min(fields["J"]))})
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
            scale = measured["residual_scale"]
            phi = .5 * float(np.dot(r / scale, r / scale))
            accepted_trial = False
            for backtrack in range(settings.max_backtracks + 1):
                factor = 2. ** (-backtrack)
                trial = candidate.copy()
                trial[model.free] += factor * step
                record = {"target_displacement": float(target), "newton_check": iteration,
                          "factor": factor, "fixed_residual_scale": scale, "base_phi": phi,
                          "accepted": False, "minimum_J": None, "phi": None}
                try:
                    trial = impose(trial, target)
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
        before_u, before_d = state_u.copy(), state_d
        max_depth_used = max(max_depth_used, depth)
        try:
            solved, solved_K, measured = newton(before_u, before_d, state_K, target)
        except (KernelError, TMCError) as error:
            assert np.array_equal(state_u, before_u) and state_d == before_d
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
    last = accepted[-1] if accepted else None
    return {"status": "success" if failure is None else "failed", "target_reached": failure is None,
            "target_displacement": float(levels[-1]), "reached_displacement": state_d,
            "u": state_u.copy(), "drive_force": last["drive_force"] if last is not None else None,
            "target_metrics": deepcopy(last) if failure is None else None,
            "last_accepted_state": deepcopy(last), "failure": failure, "accepted_steps": accepted,
            "trials": trials, "failed_attempts": failures, "newton_history": base_checks,
            "linear_solve_diagnostics": linear_solves, "maximum_bisection_depth": max_depth_used,
            "timing_seconds": times, "base": base.copy(), "direction": direction.copy(),
            "reaction_groups": {name: value.copy() for name, value in groups.items()},
            "force_scale_per_length": force_scale_per_length,
            "reference_state": "undeformed" if not np.any(base) else "prescribed_base_at_zero_target",
            "constraint_force_sign": "apparatus_on_model", "external_nodal_loads": "none",
            "scope": "affine Dirichlet numerical path; physical contact and independent precision require separate verification"}
