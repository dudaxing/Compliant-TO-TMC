"""Full-domain Q1 TMC assembly and bounded load control in source numeric units.

This module is independent of MATLAB and LF. It does not interpret HF-1 geometry
qualification or task units. The nonconservative residual uses its own Jacobian.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Callable

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from .tmc_kernel import operators, batch_response, KernelError


class TMCError(ValueError):
    def __init__(self, message, *, code="invalid_model", details=None):
        super().__init__(message)
        self.code = code
        self.details = {} if details is None else details


def _array(value, dtype, name):
    raw = np.asarray(value)
    if np.iscomplexobj(raw) or not np.all(np.isfinite(raw)):
        raise TMCError(f"{name} must be finite and real")
    if np.issubdtype(np.dtype(dtype), np.integer) and not np.all(raw == np.floor(raw)):
        raise TMCError(f"{name} must contain integers")
    result = np.array(raw, dtype=dtype, copy=True)
    result.setflags(write=False)
    return result


@dataclass
class TMCModel:
    coordinates: np.ndarray
    connectivity: np.ndarray
    lam: np.ndarray
    mu: np.ndarray
    kr: float
    hx: float
    hy: float
    thickness: float = 1.0
    solid: np.ndarray | None = None
    fixed_dofs: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=int))

    def __post_init__(self):
        self.coordinates = _array(self.coordinates, float, "coordinates")
        self.connectivity = _array(self.connectivity, np.int64, "connectivity")
        if self.coordinates.ndim != 2 or self.coordinates.shape[1] != 2:
            raise TMCError("coordinates must have shape (nn,2)")
        if self.connectivity.ndim != 2 or self.connectivity.shape[1] != 4 or not len(self.connectivity):
            raise TMCError("connectivity must have shape (ne,4), with at least one cell")
        if np.any(self.connectivity < 0) or np.any(self.connectivity >= len(self.coordinates)):
            raise TMCError("connectivity node outside coordinates")
        for name in ("hx", "hy", "thickness", "kr"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or (value <= 0 if name != "kr" else value < 0):
                raise TMCError(f"invalid {name}")
            setattr(self, name, value)
        corner = self.coordinates[self.connectivity]
        expected = np.array([[0, 0], [self.hx, 0], [self.hx, self.hy], [0, self.hy]])
        tolerance = 1e-12 * max(self.hx, self.hy, np.max(np.abs(self.coordinates)), 1.0)
        if not np.allclose(corner - corner[:, :1], expected, atol=tolerance, rtol=0):
            raise TMCError("cells must be equal axis-aligned BL BR TR TL rectangles")
        for name in ("lam", "mu"):
            value = np.broadcast_to(np.asarray(getattr(self, name)), (self.ne,))
            value = _array(value, float, name)
            if np.any(value < 0):
                raise TMCError(f"{name} must be nonnegative for this baseline")
            setattr(self, name, value)
        if self.solid is None:
            self.solid = np.ones(self.ne, dtype=bool)
        raw_solid = np.asarray(self.solid)
        if raw_solid.shape != (self.ne,) or not np.all((raw_solid == 0) | (raw_solid == 1)):
            raise TMCError("solid flags must be binary with shape (ne,)")
        self.solid = _array(raw_solid, bool, "solid")
        self.fixed_dofs = _array(self.fixed_dofs, np.int64, "fixed_dofs")
        if self.fixed_dofs.ndim != 1 or len(np.unique(self.fixed_dofs)) != len(self.fixed_dofs):
            raise TMCError("fixed DOFs must be a unique vector")
        if np.any(self.fixed_dofs < 0) or np.any(self.fixed_dofs >= self.ndof):
            raise TMCError("fixed DOF outside model")
        self.edofs = (2 * self.connectivity[..., None] + np.arange(2)).reshape(self.ne, 8)
        self.free = np.setdiff1d(np.arange(self.ndof), self.fixed_dofs)
        self.ops = operators(self.hx, self.hy, self.thickness)
        self._rows = np.repeat(self.edofs, 8, axis=1).ravel()
        self._cols = np.tile(self.edofs, (1, 8)).ravel()
        for value in (self.edofs, self.free, self._rows, self._cols):
            value.setflags(write=False)

    @property
    def ne(self):
        return len(self.connectivity)

    @property
    def ndof(self):
        return 2 * len(self.coordinates)


def rectangular_model(nx, ny, Lx, Ly, *, E=100.0, nu=0.3, alpha=1e-6,
                      factors=1.0, solid=None, fixed_dofs=(), thickness=1.0):
    """Create a full-domain canonical x-fast/bottom-up reference mesh."""
    if isinstance(nx, bool) or isinstance(ny, bool) or int(nx) != nx or int(ny) != ny or nx < 1 or ny < 1:
        raise TMCError("nx and ny must be positive integers")
    nx, ny = int(nx), int(ny)
    if not all(np.isfinite(x) for x in (Lx, Ly, E, nu, alpha)) or min(Lx, Ly, E) <= 0 or not 0 <= nu < 0.5 or alpha < 0:
        raise TMCError("invalid dimensions/material parameters for source baseline")
    xx, yy = np.meshgrid(np.linspace(0, Lx, nx + 1), np.linspace(0, Ly, ny + 1))
    coordinates = np.column_stack((xx.ravel(), yy.ravel()))
    ll = (np.arange(ny)[:, None] * (nx + 1) + np.arange(nx)).ravel()
    connectivity = ll[:, None] + np.array([0, 1, nx + 2, nx + 1])
    factor = np.broadcast_to(_array(factors, float, "factors"), (nx * ny,))
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    kr = alpha * Lx**2 * (E / (3 * (1 - 2 * nu)) + 4 * mu / 3)
    return TMCModel(coordinates, connectivity, lam * factor, mu * factor, kr,
                    Lx / nx, Ly / ny, thickness, solid, fixed_dofs)


def assemble(model: TMCModel, u, tangent=True):
    """Return K (or None), internal force and element fields/timing."""
    displacement = _array(u, float, "displacement")
    if displacement.shape != (model.ndof,) or not np.all(np.isfinite(displacement)):
        raise TMCError("displacement must be a finite full-DOF vector", code="invalid_displacement")
    begin = perf_counter()
    fields = batch_response(displacement[model.edofs], model.ops, model.lam, model.mu, model.kr, tangent=tangent)
    kernel_time = perf_counter() - begin
    begin_assembly = perf_counter()
    residual = np.bincount(model.edofs.ravel(), weights=fields["residual"].ravel(), minlength=model.ndof)
    matrix = None
    if tangent:
        matrix = sparse.coo_matrix((fields["tangent"].ravel(), (model._rows, model._cols)),
                                   shape=(model.ndof, model.ndof)).tocsc()
        matrix.sum_duplicates()
    if not np.all(np.isfinite(residual)) or (matrix is not None and not np.all(np.isfinite(matrix.data))):
        raise TMCError("assembled values are nonfinite", code="nonfinite")
    fields["timing_seconds"] = {"kernel_and_transfer": kernel_time, "assembly": perf_counter() - begin_assembly}
    return matrix, residual, fields


@dataclass(frozen=True)
class NewtonSettings:
    tolerance: float = 1e-8
    max_checks: int = 25
    armijo_c: float = 1e-4
    max_backtracks: int = 12
    max_bisections: int = 4
    minimum_increment: float = 0.000625
    time_limit_seconds: float = 1200.0

    def __post_init__(self):
        if not 0 < self.tolerance < 1 or not 0 < self.armijo_c < 0.5:
            raise TMCError("invalid Newton tolerance/Armijo constant")
        if not np.isfinite(self.minimum_increment) or self.minimum_increment <= 0:
            raise TMCError("minimum increment must be positive")
        if not np.isfinite(self.time_limit_seconds) or self.time_limit_seconds <= 0:
            raise TMCError("time budget must be positive")
        for name in ("max_checks", "max_backtracks", "max_bisections"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < (1 if name == "max_checks" else 0):
                raise TMCError(f"invalid {name}")


def _check_support(model):
    rigid = np.zeros((model.ndof, 3))
    rigid[0::2, 0] = 1
    rigid[1::2, 1] = 1
    span = max(np.ptp(model.coordinates, axis=0).max(), 1.0)
    center = model.coordinates.mean(axis=0)
    rigid[0::2, 2] = -(model.coordinates[:, 1] - center[1]) / span
    rigid[1::2, 2] = (model.coordinates[:, 0] - center[0]) / span
    if np.linalg.matrix_rank(rigid[model.fixed_dofs]) < 3:
        raise TMCError("support does not eliminate three planar rigid modes", code="insufficient_support")


def solve_path(model: TMCModel, F0, targets, settings=None, on_accept: Callable | None = None):
    """Bounded safeguarded Newton path, always starting from undeformed U=0.

    Only equilibrated states enter accepted_steps. Trial failure does not overwrite
    the last accepted state. Returned target_metrics is None unless all targets pass.
    """
    settings = NewtonSettings() if settings is None else settings
    if not isinstance(settings, NewtonSettings):
        raise TMCError("settings must be NewtonSettings")
    load = _array(F0, float, "F0")
    levels = _array(targets, float, "targets")
    if load.shape != (model.ndof,) or levels.ndim != 1 or not len(levels):
        raise TMCError("invalid force or target shape")
    if np.any(levels < 0) or np.any(np.diff(levels) <= 0):
        raise TMCError("targets must be nonnegative, finite and strictly increasing")
    started = perf_counter()
    state_u, state_lambda = np.zeros(model.ndof), 0.0
    accepted, trials, failures = [], [], []
    times = {"kernel_and_transfer": 0.0, "assembly": 0.0, "sparse_solve": 0.0,
             "all_assembly_attempts_wall": 0.0, "callback": 0.0,
             "first_kernel_including_compile": None, "kernel_calls": 0, "successful_kernel_calls": 0,
             "newton_base_checks": 0}
    failure = None
    max_depth_used = 0

    def check_time():
        if perf_counter() - started > settings.time_limit_seconds:
            raise TMCError("path wall-time budget exceeded", code="time_limit")

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
        check_time()
        return K, internal, values

    def metrics(u, level, internal, values):
        external = level * load
        scale = float(np.linalg.norm(external))
        if scale == 0:
            scale = max(float(np.linalg.norm(load)), 1.0)
        imbalance = internal - external
        residual_norm = float(np.linalg.norm(imbalance[model.free]))
        if not np.isfinite(scale) or not np.isfinite(residual_norm):
            raise TMCError("force normalization is nonfinite", code="nonfinite")
        reaction = np.zeros(model.ndof)
        reaction[model.fixed_dofs] = imbalance[model.fixed_dofs]
        solid_energy = float(np.sum(values["material_energy"][model.solid]))
        medium_energy = float(np.sum(values["material_energy"][~model.solid]))
        if not np.isfinite(solid_energy) or not np.isfinite(medium_energy):
            raise TMCError("integrated material energy is nonfinite", code="nonfinite")
        return {"lambda": float(level), "relative_residual": residual_norm / scale,
                "residual_scale": scale, "minimum_J": float(np.min(values["J"])),
                "solid_material_energy": solid_energy,
                "medium_material_energy": medium_energy,
                "global_force_balance": (reaction.reshape(-1, 2).sum(axis=0) + external.reshape(-1, 2).sum(axis=0)).tolist(),
                "fixed_displacement_max": float(np.max(np.abs(u[model.fixed_dofs]), initial=0)),
                "support_reaction": reaction, "J": values["J"].copy()}

    def newton(start_u, target):
        candidate = start_u.copy()
        for iteration in range(1, settings.max_checks + 1):
            K, internal, values = evaluate(candidate, True)
            times["newton_base_checks"] += 1
            measured = metrics(candidate, target, internal, values)
            if measured["relative_residual"] <= settings.tolerance:
                measured["newton_checks"] = iteration
                return candidate, measured
            if iteration == settings.max_checks:
                raise TMCError("Newton base-check limit reached", code="newton_limit",
                               details={"lambda": target, "relative_residual": measured["relative_residual"]})
            r = (internal - target * load)[model.free]
            begin_solve = perf_counter()
            try:
                step = splu(K[model.free][:, model.free]).solve(-r)
            except RuntimeError as error:
                raise TMCError(str(error), code="singular_tangent") from error
            times["sparse_solve"] += perf_counter() - begin_solve
            if not np.all(np.isfinite(step)):
                raise TMCError("Newton solution is nonfinite", code="nonfinite")
            phi = 0.5 * float(r @ r)
            accepted_trial = False
            for backtrack in range(settings.max_backtracks + 1):
                factor = 2.0 ** (-backtrack)
                trial = candidate.copy()
                trial[model.free] += factor * step
                record = {"target_lambda": float(target), "newton_check": iteration, "factor": factor,
                          "accepted": False, "minimum_J": None, "phi": None}
                try:
                    _, trial_internal, trial_fields = evaluate(trial, False)
                    trial_r = (trial_internal - target * load)[model.free]
                    trial_phi = 0.5 * float(trial_r @ trial_r)
                    if not np.isfinite(trial_phi):
                        raise TMCError("trial residual merit is nonfinite", code="nonfinite")
                    record.update(minimum_J=float(np.min(trial_fields["J"])), phi=trial_phi)
                    if trial_phi <= (1 - 2 * settings.armijo_c * factor) * phi:
                        record["accepted"] = True
                        accepted_trial = True
                        candidate = trial
                    else:
                        record["reason"] = "armijo_insufficient_decrease"
                except (KernelError, TMCError) as error:
                    if getattr(error, "code", None) == "time_limit":
                        raise
                    record["reason"] = getattr(error, "code", "trial_error")
                    record["details"] = getattr(error, "details", {})
                trials.append(record)
                if accepted_trial:
                    break
            if not accepted_trial:
                raise TMCError("all bounded backtracking factors rejected", code="backtracking_failed",
                               details={"lambda": target, "newton_check": iteration})
        raise AssertionError("unreachable")

    def advance(target, depth, original_target):
        nonlocal state_u, state_lambda, max_depth_used
        before_u, before_lambda = state_u.copy(), state_lambda
        max_depth_used = max(max_depth_used, depth)
        try:
            solved, measured = newton(before_u, target)
        except (KernelError, TMCError) as error:
            assert np.array_equal(state_u, before_u) and state_lambda == before_lambda
            failures.append({"from_lambda": float(before_lambda), "attempted_lambda": float(target),
                             "depth": depth, "code": getattr(error, "code", "numerical_failure"),
                             "details": getattr(error, "details", {}), "rollback_bitwise_equal": True})
            increment = target - before_lambda
            if (getattr(error, "code", None) == "time_limit" or depth >= settings.max_bisections or
                    increment / 2 < settings.minimum_increment * (1 - 1e-12)):
                raise
            midpoint = before_lambda + increment / 2
            advance(midpoint, depth + 1, original_target)
            advance(target, depth + 1, original_target)
            return
        state_u, state_lambda = solved.copy(), float(target)
        record = {**measured, "u": solved.copy(), "original_target_lambda": float(original_target),
                  "is_original_target": bool(target == original_target), "bisection_depth": depth,
                  "elapsed_seconds": perf_counter() - started}
        accepted.append(record)
        if on_accept is not None:
            # Separate arrays prevent a callback from mutating future starting states.
            begin_callback = perf_counter()
            try:
                on_accept({k: v.copy() if isinstance(v, np.ndarray) else v for k, v in record.items()})
            except OSError as error:
                raise TMCError(str(error),code="persistence_failure",
                               details={"last_equilibrated_lambda":state_lambda}) from error
            finally:
                times["callback"] += perf_counter() - begin_callback
            check_time()

    try:
        _check_support(model)
        for target in levels:
            advance(float(target), 0, float(target))
    except (KernelError, TMCError) as error:
        failure = {"code": getattr(error, "code", "numerical_failure"), "reason": str(error),
                   "details": getattr(error, "details", {})}
    times["total"] = perf_counter() - started
    return {"status": "success" if failure is None else "failed", "target_reached": failure is None,
            "target_lambda": float(levels[-1]), "reached_lambda": state_lambda, "u": state_u.copy(),
            "target_metrics": accepted[-1] if failure is None else None, "failure": failure,
            "accepted_steps": accepted, "trials": trials, "failed_attempts": failures,
            "maximum_bisection_depth": max_depth_used, "timing_seconds": times,
            "units_mode": "source_numeric", "reference_state": "undeformed",
            "scope": "specified code benchmark; not independent contact-accuracy validation"}
