"""Opt-in guided body-x force control with an unknown rigid translation.

The reduced unknowns are the original free fluctuation, one body coordinate q,
and the input multiplier R.  The actual nonsymmetric tangent is retained.  A
saved absolute-q anchor is freshly checked, never projected or repaired.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import fsum
from time import perf_counter

import numpy as np
from scipy import sparse

from .displacement import (DisplacementSettings, _check_support, _inputs,
                           _linear_solve, _positive_scalar, _vector)
from .split_affine import _bitwise_equal
from .split_displacement import split_average_measurement
from .split_kernel import assemble_split
from .split_prescribed import STATE_SCHEMA, state_hash
from .split_state import SplitDisplacement
from .tmc import TMCError
from .tmc_kernel import KernelError


@dataclass(frozen=True)
class GuidedForceSettings:
    """Only the new force increment is configured here; its unit is half N."""

    minimum_force_increment_half_N: float

    def __post_init__(self):
        value = self.minimum_force_increment_half_N
        if (isinstance(value, (bool, np.bool_, complex)) or not np.isscalar(value)
                or not np.isrealobj(value)):
            raise TMCError("invalid minimum_force_increment_half_N", code="invalid_settings")
        try:
            valid = np.isfinite(value) and value > 0
        except TypeError:
            valid = False
        if not valid:
            raise TMCError("minimum_force_increment_half_N must be positive half N",
                           code="invalid_settings")


def solve_split_guided_force_path(model, b_in, b_out, body_load_targets_half_N,
                                  k_out=0., *, initial_state, initial_R, settings,
                                  force_settings, force_scale_per_length,
                                  body_contract, initial_body_q_mm=0.,
                                  force_scale_anchor_half_N=None,
                                  assembler=None, on_accept=None):
    """Hold the input mean, apply absolute half-model P, and solve unknown q.

    All original body ux equal q, uy remain zero, and body fluctuation remains
    zero.  The c vector has ones, not averaged weights: its residual is
    sum(body internal x force)-P.  Loads strictly increase from a freshly
    checked saved anchor.  q is absolute; a supplied root force-scale anchor
    remains independent of the current segment's first P.  Full-model load is 2P;
    thickness is already included by the original mechanical assembler.
    """
    if not isinstance(settings, DisplacementSettings):
        raise TMCError("settings must be DisplacementSettings", code="invalid_settings")
    if not isinstance(force_settings, GuidedForceSettings):
        raise TMCError("force_settings must be GuidedForceSettings", code="invalid_settings")
    b_in, b_out, k_out = _inputs(model, b_in, b_out, k_out)
    force_scale_per_length = _positive_scalar(force_scale_per_length, "force_scale_per_length")
    initial_R = float(_vector([initial_R], 1, "initial_R")[0])
    initial_q = float(_vector([initial_body_q_mm], 1, "initial_body_q_mm")[0])
    raw = np.asarray(body_load_targets_half_N)
    if raw.ndim != 1 or len(raw) < 2:
        raise TMCError("body loads must contain at least two absolute half-N targets",
                       code="invalid_input")
    levels = _vector(body_load_targets_half_N, len(raw), "body_load_targets_half_N")
    if np.any(np.diff(levels) <= 0):
        raise TMCError("absolute half-N targets must strictly increase", code="invalid_input")
    P_anchor = float(levels[0])
    P_scale_anchor = (P_anchor if force_scale_anchor_half_N is None else
        float(_vector([force_scale_anchor_half_N], 1, "force_scale_anchor_half_N")[0]))
    if (not isinstance(body_contract, dict)
            or set(body_contract) != {"nodes", "d_hold", "zero_dofs", "background_dofs"}):
        raise TMCError("invalid guided body contract", code="constraint_conflict")

    def indices(value, limit):
        values = np.asarray(value)
        if (values.ndim != 1 or (values.size and values.dtype.kind not in "iu")
                or np.any(values < 0) or np.any(values >= limit)
                or len(np.unique(values)) != len(values)):
            raise TMCError("invalid guided body indices", code="constraint_conflict")
        return values.astype(np.int64)

    nodes = indices(body_contract["nodes"], model.ndof//2)
    zero = indices(body_contract["zero_dofs"], model.ndof)
    background = indices(body_contract["background_dofs"], model.ndof)
    body_x, body_y = 2*nodes, 2*nodes+1
    body_dofs = np.union1d(body_x, body_y)
    d_hold = _positive_scalar(body_contract["d_hold"], "d_hold")
    overlap = np.intersect1d(zero, body_dofs)
    if (not len(nodes) or k_out != 0
            or not np.array_equal(np.union1d(zero, body_dofs), model.fixed_dofs)
            or not np.all(np.isin(background, zero)) or np.any(background % 2 != 1)
            or not np.all(np.isin(overlap, np.intersect1d(body_y, background)))
            or np.any(b_in[body_dofs]) or np.any(b_out[body_dofs])):
        raise TMCError("guided force control conflicts with body, supports or ports",
                       code="constraint_conflict")
    if (not isinstance(initial_state, SplitDisplacement) or initial_state.ndof != model.ndof
            or np.any(initial_state.lift[body_x] != initial_q)
            or np.any(initial_state.lift[np.setdiff1d(np.arange(model.ndof), body_x)])
            or np.any(initial_state.fluctuation[model.fixed_dofs])):
        raise TMCError("force anchor must preserve its absolute-q split state and fixed zeros",
                       code="constraint_conflict")
    initial = initial_state.copy()
    assembly = assemble_split if assembler is None else assembler
    if not callable(assembly) or (on_accept is not None and not callable(on_accept)):
        raise TMCError("assembler and callback must be callable", code="invalid_input")
    free, b_free = model.free, b_in[model.free]
    b_reduced = np.r_[b_free, 0.]
    pivot = free[int(np.argmax(np.abs(b_free)))]
    support_dofs = np.setdiff1d(model.fixed_dofs, body_x)
    dscale = max(abs(d_hold), settings.displacement_scale_floor)
    force_floor = settings.force_scale_floor_factor*force_scale_per_length*dscale
    mean_bound = settings.constraint_tolerance*dscale
    started = perf_counter()
    state_u, state_R, state_P, state_q, state_K = initial.copy(), initial_R, P_anchor, initial_q, None
    accepted, trials, failures, history, linear_solves = [], [], [], [], []
    failure, maximum_depth = None, 0
    times = dict(kernel_calls=0, successful_kernel_calls=0, kernel_and_transfer=0.,
                 assembly=0., sparse_solve=0., callback=0., all_assembly_attempts_wall=0.)

    def clock():
        if perf_counter()-started > settings.time_limit_seconds:
            raise TMCError("guided force path wall-time budget exceeded", code="time_limit")

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
        if (not np.isfinite(internal).all() or not np.isfinite(fields["J"]).all()
                or any(not np.isfinite(fields[name]).all()
                       for name in ("Hu", "F") if name in fields)):
            raise TMCError("guided force fields are nonfinite", code="nonfinite")
        if np.any(fields["J"] <= 0):
            raise TMCError("all determinants must be positive", code="invalid_J")
        clock()
        return K, internal, fields

    def impose(w, q):
        lift = initial.lift.copy()
        lift[body_x] = q
        try:
            return SplitDisplacement(lift, w)
        except (ValueError, OverflowError) as error:
            raise TMCError("guided force candidate is nonfinite", code="nonfinite") from error

    def mean_error(state):
        return split_average_measurement(state, b_in, -d_hold)

    def feasible(state):
        # Only the original nonbody input port is compensated.  q is unknown
        # and is never projected, clipped, or replaced by a reference answer.
        w = state.fluctuation.copy()
        before = mean_error(state)
        w[pivot] -= before/b_in[pivot]
        result = SplitDisplacement(state.lift, w)
        after = mean_error(result)
        if abs(after) > mean_bound:
            raise TMCError("guided force mean feasibility failed", code="constraint_failure",
                           details=dict(constraint_residual=after, constraint_bound=mean_bound))
        return result, before, after

    def measure(state, R, P, q, internal):
        q_in = split_average_measurement(state, b_in)
        q_out = split_average_measurement(state, b_out)
        actuator, spring = b_in*R, k_out*b_out*q_out
        residual = internal+spring-actuator
        scale = max(*(float(np.linalg.norm(v[free])) for v in (internal, actuator, spring)),
                    force_floor)
        generalized = fsum(float(internal[dof]) for dof in body_x)
        g = fsum((generalized, -P))
        pscale = max(abs(P), abs(P_scale_anchor), force_floor)
        if (not np.isfinite(residual).all() or not np.isfinite(R)
                or not np.isfinite(scale) or scale <= 0
                or not np.isfinite(g) or not np.isfinite(pscale) or pscale <= 0):
            raise TMCError("guided body forces are nonfinite", code="nonfinite")
        residual_norm = float(np.linalg.norm(residual[free]))
        return dict(d=d_hold, physical_mean_target_mm=d_hold, target_origin=0.,
                    input_mean_mm=q_in, body_q_mm=q, P_target_half_N=P,
                    segment_anchor_half_N=P_anchor,
                    force_scale_anchor_half_N=P_scale_anchor,
                    load_increment_from_anchor_half_N=P-P_anchor,
                    load_increment_from_root_half_N=P-P_scale_anchor,
                    generalized_body_internal_force_half_N=generalized,
                    generalized_force_residual_half_N=g,
                    generalized_force_scale_half_N=pscale,
                    generalized_force_bound_half_N=settings.tolerance*pscale,
                    relative_generalized_force_residual=abs(g)/pscale,
                    R_input=R, q_in=q_in, q_out=q_out,
                    constraint_residual=mean_error(state), constraint_bound=mean_bound,
                    displacement_scale=dscale, residual_scale=scale, force_scale_floor=force_floor,
                    free_force_residual_norm=residual_norm, relative_residual=residual_norm/scale,
                    input_force=actuator, spring_force_on_structure=-spring, force_residual=residual)

    def metrics(state, R, P, q, internal, fields):
        measured = measure(state, R, P, q, internal)
        support = np.zeros(model.ndof)
        support[support_dofs] = measured["force_residual"][support_dofs]
        externals = support+measured["input_force"]+measured["spring_force_on_structure"]
        balance = np.array([fsum(float(value) for value in externals[component::2])
                            for component in (0, 1)]) + np.array([P, 0.])
        balance_scale = max(sum(float(np.linalg.norm(v)) for v in
                                (support, measured["input_force"], measured["spring_force_on_structure"]))
                            + abs(P), measured["residual_scale"])
        measured.update(support_reaction=support, internal_force=internal.copy(),
            material_internal_force=np.bincount(model.edofs.ravel(),
                weights=fields["material_residual"].ravel(), minlength=model.ndof),
            regularization_internal_force=np.bincount(model.edofs.ravel(),
                weights=fields["regularization_residual"].ravel(), minlength=model.ndof),
            J=fields["J"].copy(), minimum_J=float(fields["J"].min()),
            global_force_balance=balance, global_force_balance_scale=balance_scale,
            relative_global_force_balance=float(np.linalg.norm(balance))/balance_scale,
            explicit_body_load_half_N=np.array([P, 0.]),
            support_reaction_dofs=support_dofs.copy(),
            output_spring_energy=.5*k_out*measured["q_out"]**2,
            output_spring_generalized_force=-k_out*measured["q_out"])
        if not all(np.isfinite(measured[key]).all() for key in
                   ("material_internal_force", "regularization_internal_force", "global_force_balance",
                    "global_force_balance_scale", "relative_global_force_balance")):
            raise TMCError("guided force component/balance metrics are nonfinite", code="nonfinite")
        return measured

    def step(K, rhs_force, rhs_mean, phase, P, iteration=None):
        clock()
        K = K.tocsc()
        # Independent row/column sums retain the actual nonsymmetric Jacobian.
        Kff = K[free][:, free].tocsc()
        Kfc = sparse.csc_matrix(np.asarray(K[free][:, body_x].sum(axis=1)))
        Kcf = sparse.csc_matrix(np.asarray(K[body_x][:, free].sum(axis=0)))
        Kcc = sparse.csc_matrix([[float(K[body_x][:, body_x].sum())]])
        reduced = sparse.bmat([[Kff, Kfc], [Kcf, Kcc]], format="csc")
        column = sparse.csc_matrix(b_reduced[:, None])
        augmented = sparse.bmat([[reduced, -column], [column.T, None]], format="csc")
        if not np.isfinite(augmented.data).all():
            raise TMCError("guided force Jacobian is nonfinite", code="nonfinite")
        begin = perf_counter()
        try:
            dz, dR, row = _linear_solve(augmented, rhs_force, rhs_mean, reduced, b_reduced,
                phase=phase, target=d_hold, newton_check=iteration)
        finally:
            times["sparse_solve"] += perf_counter()-begin
        norm = float(np.linalg.norm(reduced.data))
        row.update(target_force_half_N=P, factorization="general sparse LU", symmetrized=False,
            reduced_unknown_order="original_free_fluctuation,body_q_mm,input_R_N",
            reduced_displacement_shape=list(reduced.shape), reduced_tangent_nnz=reduced.nnz,
            reduced_tangent_frobenius=norm,
            relative_reduced_tangent_asymmetry=float(np.linalg.norm((reduced-reduced.T).data))
                / max(norm, np.finfo(float).tiny),
            body_free_couplings_assembled_independently=True,
            generalized_force_row_is_sum=True)
        linear_solves.append(row)
        clock()
        return dz[:-1], float(dz[-1]), dR, row

    def newton(start, R, old_P, old_q, K, P):
        candidate, q = start.copy(), old_q
        if P != old_P:
            if K is None:
                K, _, _ = evaluate(start, True)
            rhs = np.r_[np.zeros(len(free)), P-old_P]
            dw, dq, dR, row = step(K, rhs, -mean_error(start), "predictor", P)
            w = start.fluctuation.copy()
            w[free] += dw
            q += dq
            candidate, before, after = feasible(impose(w, q))
            R += dR
            row.update(mean_error_before_projection=before, mean_error_after_projection=after,
                       predicted_body_delta_q_mm=dq,
                       predictor_body_sensitivity_mm_per_N=dq/(P-old_P))
        for iteration in range(1, settings.max_checks+1):
            K, internal, fields = evaluate(candidate, True)
            measured = measure(candidate, R, P, q, internal)
            history.append({key: measured[key] for key in
                ("d", "body_q_mm", "P_target_half_N", "R_input", "q_in", "q_out",
                 "constraint_residual", "constraint_bound", "relative_residual", "residual_scale",
                 "generalized_force_residual_half_N", "generalized_force_scale_half_N",
                 "generalized_force_bound_half_N", "relative_generalized_force_residual")}
                | dict(newton_check=iteration, minimum_J=float(fields["J"].min()),
                       state_sha256=state_hash(candidate)))
            if (measured["relative_residual"] <= settings.tolerance
                    and measured["relative_generalized_force_residual"] <= settings.tolerance
                    and abs(measured["constraint_residual"]) <= measured["constraint_bound"]):
                result = metrics(candidate, R, P, q, internal, fields)
                result["newton_checks"] = iteration
                return candidate, R, q, K, result
            if not accepted and old_P == P == P_anchor:
                raise TMCError("force anchor failed its fresh equilibrium check",
                               code="initial_state_not_equilibrated")
            if abs(measured["constraint_residual"]) > mean_bound:
                raise TMCError("guided force mean constraint failed", code="constraint_failure")
            if iteration == settings.max_checks:
                raise TMCError("Newton base-check limit reached", code="newton_limit")
            r = measured["force_residual"][free]
            g = measured["generalized_force_residual_half_N"]
            dw, dq, dR, row = step(K, np.r_[-r, -g], -measured["constraint_residual"],
                                  "corrector", P, iteration)
            scale, pscale = measured["residual_scale"], measured["generalized_force_scale_half_N"]
            phi = .5*(float(np.dot(r/scale, r/scale))+(g/pscale)**2)
            accepted_trial = False
            for backtrack in range(settings.max_backtracks+1):
                factor = 2.**(-backtrack)
                w = candidate.fluctuation.copy()
                w[free] += factor*dw
                trial_R, trial_q = R+factor*dR, q+factor*dq
                record = dict(target_displacement=d_hold, target_force_half_N=P,
                    newton_check=iteration, factor=factor, fixed_residual_scale=scale,
                    fixed_generalized_force_scale_half_N=pscale, base_phi=phi, accepted=False)
                try:
                    trial, before, after = feasible(impose(w, trial_q))
                    _, trial_internal, trial_fields = evaluate(trial, False)
                    trial_measured = measure(trial, trial_R, P, trial_q, trial_internal)
                    trial_r = trial_measured["force_residual"][free]
                    trial_g = trial_measured["generalized_force_residual_half_N"]
                    trial_phi = .5*(float(np.dot(trial_r/scale, trial_r/scale))+(trial_g/pscale)**2)
                    if not np.isfinite(trial_phi):
                        raise TMCError("guided force trial merit is nonfinite", code="nonfinite")
                    record.update(phi=trial_phi, minimum_J=float(trial_fields["J"].min()),
                        mean_error_before_projection=before, constraint_residual=after,
                        R_input=trial_R, body_q_mm=trial_q,
                        generalized_force_residual_half_N=trial_g,
                        relative_generalized_force_residual=abs(trial_g)/pscale)
                    if trial_phi <= (1-2*settings.armijo_c*factor)*phi:
                        record["accepted"] = accepted_trial = True
                        candidate, R, q = trial, trial_R, trial_q
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
                raise TMCError("all bounded force backtracking factors rejected",
                               code="backtracking_failed")
        raise AssertionError("unreachable")

    def advance(P, depth, original, original_index):
        nonlocal state_u, state_R, state_P, state_q, state_K, maximum_depth
        before, before_R, before_P = state_u.copy(), state_R, state_P
        before_q, before_K = state_q, state_K
        maximum_depth = max(maximum_depth, depth)
        try:
            solved, R, q, K, measured = newton(before, before_R, before_P, before_q, before_K, P)
        except (KernelError, TMCError) as error:
            assert (_bitwise_equal(state_u.lift, before.lift)
                    and _bitwise_equal(state_u.fluctuation, before.fluctuation)
                    and _bitwise_equal(np.array([state_R]), np.array([before_R]))
                    and state_P == before_P and state_q == before_q and state_K is before_K)
            code = getattr(error, "code", "numerical_failure")
            failures.append(dict(from_force_half_N=before_P, attempted_force_half_N=P,
                from_body_q_mm=before_q, from_R_input=before_R, depth=depth, code=code,
                reason=str(error), rollback_bitwise_equal=True))
            if (not accepted or code in ("time_limit", "constraint_failure")
                    or depth >= settings.max_bisections
                    or abs(P-before_P)/2 < force_settings.minimum_force_increment_half_N*(1-1e-12)):
                raise
            advance(before_P+(P-before_P)/2, depth+1, original, original_index)
            advance(P, depth+1, original, original_index)
            return
        state_u, state_R, state_P, state_q, state_K = solved.copy(), float(R), float(P), float(q), K
        record = dict(measured, u_lift=solved.lift.copy(), u_fluctuation=solved.fluctuation.copy(),
            u_display=solved.u_display, state_representation=STATE_SCHEMA,
            state_sha256=state_hash(solved), original_target_force_half_N=original,
            is_original_target=P == original, original_target_index=original_index,
            bisection_depth=depth, elapsed_seconds=perf_counter()-started,
            leg="anchor" if not accepted else "force_loading", force_anchor=not accepted)
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
        for index, P in enumerate(levels):
            advance(float(P), 0, float(P), index)
    except (KernelError, TMCError) as error:
        failure = dict(code=getattr(error, "code", "numerical_failure"), reason=str(error))
    times["total"] = perf_counter()-started
    return dict(status="success" if failure is None else "failed", target_reached=failure is None,
        target_force_half_N=float(levels[-1]), reached_force_half_N=state_P,
        body_load_targets_half_N=levels.tolist(), input_hold_mm=d_hold, reached_body_q_mm=state_q,
        target_displacement=d_hold, physical_mean_target_mm=d_hold,
        u_lift=state_u.lift.copy(), u_fluctuation=state_u.fluctuation.copy(), u_display=state_u.u_display,
        R_input=state_R, state_representation=STATE_SCHEMA, state_sha256=state_hash(state_u),
        target_metrics=deepcopy(accepted[-1]) if failure is None else None,
        last_accepted_state=deepcopy(accepted[-1]) if accepted else None, failure=failure,
        accepted_steps=accepted, trials=trials, failed_attempts=failures, newton_history=history,
        linear_solve_diagnostics=linear_solves, maximum_bisection_depth=maximum_depth,
        timing_seconds=times, initial_u_lift=initial.lift.copy(),
        initial_u_fluctuation=initial.fluctuation.copy(), initial_R=initial_R,
        b_in=b_in.copy(), b_out=b_out.copy(), k_out=k_out,
        force_scale_per_length=force_scale_per_length, anchor_force_half_N=P_anchor,
        initial_body_q_mm=initial_q, segment_anchor_half_N=P_anchor,
        force_scale_anchor_half_N=P_scale_anchor,
        input_force_sign="actuator_on_model", body_force_sign="external_dead_load_on_body_plus_x",
        body_q_is_unknown=True, scope="Guided rigid-x total-force numerical path; no bearing qualification")
