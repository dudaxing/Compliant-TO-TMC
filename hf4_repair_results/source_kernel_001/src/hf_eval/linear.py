"""Independent HF-1 solid-only linear diagnostics, in mm, N and MPa.

This module does not implement finite deformation, TMC, contact or optimization.
Port directions and normalized averaging weights stay in the reference frame.
"""

from __future__ import annotations

from numbers import Real
from time import perf_counter

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from .regions import (
    active_nodes,
    element_connectivity,
    node_coordinates,
    port_vector,
    region_nodes,
)


class AnalysisError(ValueError):
    """A diagnosed failure, with fields suitable for a result wrapper."""

    def __init__(self, message, *, code="analysis_failed", stage="analysis", details=None):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.details = {} if details is None else details


def _fail(message, *, code="unsupported_configuration", stage="validation", **details):
    raise AnalysisError(message, code=code, stage=stage, details=details)


def _scalar(value, name, *, positive=False, nonnegative=False):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        _fail(f"{name} must be a real number.")
    value = float(value)
    if not np.isfinite(value):
        _fail(f"{name} must be finite.")
    if positive and value <= 0:
        _fail(f"{name} must be positive.")
    if nonnegative and value < 0:
        _fail(f"{name} must be nonnegative.")
    return value


def _material(E, nu):
    E = _scalar(E, "E_MPa", positive=True)
    nu = _scalar(nu, "nu")
    if not -1 < nu < 0.5:
        _fail("Plane-strain Poisson ratio must satisfy -1 < nu < 0.5.")
    factor = E / ((1 + nu) * (1 - 2 * nu))
    return factor * np.array(
        [[1 - nu, nu, 0], [nu, 1 - nu, 0], [0, 0, (1 - 2 * nu) / 2]],
        dtype=np.float64,
    )


def _quadrature(hx, hy):
    hx = _scalar(hx, "cell_size_x_mm", positive=True)
    hy = _scalar(hy, "cell_size_y_mm", positive=True)
    points = (-1 / np.sqrt(3.0), 1 / np.sqrt(3.0))
    operators = []
    for eta in points:
        for xi in points:
            nx = np.array([-(1 - eta), 1 - eta, 1 + eta, -(1 + eta)]) / (2 * hx)
            ny = np.array([-(1 - xi), -(1 + xi), 1 + xi, 1 - xi]) / (2 * hy)
            B = np.zeros((3, 8), dtype=np.float64)
            B[0, 0::2] = nx
            B[1, 1::2] = ny
            B[2, 0::2] = ny
            B[2, 1::2] = nx
            operators.append(B)
    return np.asarray(operators), hx * hy / 4


def element_stiffness(E, nu, hx, hy, thickness):
    """Return rectangular Q1 plane-strain stiffness; local nodes BL BR TR TL.

    Four 2x2 Gauss points integrate the linear material stiffness. Engineering
    strain is [epsilon_xx, epsilon_yy, gamma_xy]; stress is [xx, yy, xy].
    """
    D = _material(E, nu)
    thickness = _scalar(thickness, "thickness_mm", positive=True)
    B, area_weight = _quadrature(hx, hy)
    return np.einsum("qia,ij,qjb->ab", B, D, B) * area_weight * thickness


def _vector(value, n, name):
    raw = np.asarray(value)
    if raw.shape != (n,) or np.iscomplexobj(raw):
        _fail(f"{name} must be a real vector of length {n}.")
    try:
        result = raw.astype(np.float64)
    except (TypeError, ValueError):
        _fail(f"{name} must contain real numbers.")
    if not np.all(np.isfinite(result)):
        _fail(f"{name} must be finite.")
    return result


def solve_average_system(K, b, d, fixed_dofs, k_out=0, b_out=None, force_scale_floor=1e-12):
    """Solve K u + k_out b_out q_out - b R = 0 on free DOFs, b.T u=d.

    Fixed DOFs have zero displacement. R is the actuator force ON the structure;
    the output spring applies -k_out*q_out along b_out. The port constraint is
    one scalar equation and does not bind its nodes to equal displacements.
    K may be a dense array or a SciPy sparse matrix, in full DOF coordinates.
    """
    solve_start = perf_counter()
    if sparse.issparse(K):
        if np.iscomplexobj(K.data):
            _fail("K must be real.")
        K = sparse.csc_matrix(K, dtype=np.float64, copy=True)
    else:
        raw = np.asarray(K)
        if np.iscomplexobj(raw):
            _fail("K must be real.")
        try:
            K = sparse.csc_matrix(raw, dtype=np.float64)
        except (TypeError, ValueError):
            _fail("K must be a real square matrix.")
    if K.shape[0] == 0 or K.shape[0] != K.shape[1] or not np.all(np.isfinite(K.data)):
        _fail("K must be a nonempty finite square matrix.")
    K.sum_duplicates()
    n = K.shape[0]
    b = _vector(b, n, "b")
    d = _scalar(d, "input displacement")
    k_out = _scalar(k_out, "output spring stiffness", nonnegative=True)
    force_scale_floor = _scalar(force_scale_floor, "force_scale_floor", positive=True)
    if b_out is None:
        if k_out != 0:
            _fail("A positive output spring requires b_out.")
        b_out = np.zeros(n)
    b_out = _vector(b_out, n, "b_out")
    if k_out and not np.any(b_out):
        _fail("A positive output spring requires a nonzero b_out.")
    fixed_raw = np.asarray(fixed_dofs)
    if fixed_raw.ndim != 1 or (
        fixed_raw.size and (fixed_raw.dtype.kind not in "iu" or fixed_raw.dtype.kind == "b")
    ):
        _fail("fixed_dofs must be an integer vector.")
    if np.any(fixed_raw < 0) or np.any(fixed_raw >= n):
        _fail("fixed_dofs contains an out-of-range index.")
    fixed = np.unique(fixed_raw.astype(np.int64))
    free = np.setdiff1d(np.arange(n), fixed, assume_unique=True)
    if free.size == 0 or not np.any(b[free]):
        _fail("The input average has no free degree of freedom.", code="input_constrained")
    # A sparse outer product preserves the one generalized spring, rather than
    # replacing it with independent springs on each port node.
    bout_column = sparse.csc_matrix(b_out[:, None])
    K_total = K + k_out * (bout_column @ bout_column.T)
    K_free = K_total[free, :][:, free]
    b_free = sparse.csc_matrix(b[free, None])
    system = sparse.bmat([[K_free, -b_free], [b_free.T, None]], format="csc")
    rhs = np.zeros(free.size + 1)
    rhs[-1] = d
    try:
        solution = splu(system).solve(rhs)
    except (RuntimeError, ValueError) as exc:
        _fail(
            "The constrained linear system could not be factorized or solved.",
            code="singular_or_invalid_system", stage="linear_solve", reason=str(exc),
        )
    if not np.all(np.isfinite(solution)):
        _fail("The linear solve returned nonfinite values.", code="nonfinite_solution", stage="linear_solve")
    u = np.zeros(n)
    u[free] = solution[:-1]
    R = float(solution[-1])
    q_in = float(b @ u)
    q_out = float(b_out @ u)
    material_force = K @ u
    input_force = b * R
    balance = material_force + k_out * b_out * q_out - input_force
    if not np.all(np.isfinite(balance)) or not np.all(np.isfinite(material_force)):
        _fail("Force recovery returned nonfinite values.", code="nonfinite_recovery", stage="verification")
    support_reaction = np.zeros(n)
    support_reaction[fixed] = balance[fixed]
    force_norm = float(np.linalg.norm(balance[free]))
    force_scale = max(float(np.linalg.norm(material_force)), float(np.linalg.norm(input_force)), force_scale_floor)
    strain_energy = float(0.5 * u @ material_force)
    spring_energy = float(0.5 * k_out * q_out**2)
    input_work = float(0.5 * R * d)
    if not np.all(np.isfinite([force_norm, force_scale, strain_energy, spring_energy, input_work, q_in, q_out])):
        _fail("Recovered metrics contain nonfinite values.", code="nonfinite_recovery", stage="verification")
    return {
        "u": u, "free_dofs": free, "fixed_dofs": fixed,
        "support_reaction_N": support_reaction,
        "q_in_mm": q_in, "q_out_mm": q_out, "R_in_N": R,
        "output_load_N": float(-k_out * q_out),
        "strain_energy_N_mm": strain_energy, "spring_energy_N_mm": spring_energy,
        "input_work_N_mm": input_work,
        "energy_balance_error_N_mm": input_work - strain_energy - spring_energy,
        "force_residual_norm_N": force_norm, "force_scale_N": force_scale,
        "force_scale_floor_N": force_scale_floor,
        "relative_force_residual": force_norm / force_scale,
        "constraint_error_mm": abs(q_in - d),
        "linear_solve_seconds": perf_counter() - solve_start,
    }


def _keys(obj, expected, name):
    if not isinstance(obj, dict) or set(obj) != set(expected):
        actual = set(obj) if isinstance(obj, dict) else set()
        _fail(f"{name} has missing or unsupported fields.", missing=sorted(set(expected)-actual), extra=sorted(actual-set(expected)))


def _literal(obj, key, value, label):
    if obj.get(key) != value:
        _fail(f"{label}.{key} must be {value!r} for this diagnostic.")


def _validate_configs(geometry, task, solver):
    _keys(task, (
        "schema_version", "task_id", "case_family", "purpose", "parameter_origin", "material",
        "input", "output", "constraints", "support_selection", "input_auxiliary_spring_N_per_mm",
        "workpiece", "third_medium", "qualification_criteria", "reference_state",
    ), "task")
    for key, value in {
        "schema_version": "hf-task-1.0", "purpose": "linear_interface_smoke_only",
        "parameter_origin": "authorized_pilot_not_research_task",
        "support_selection": "solid_incident_nodes_only", "reference_state": "undeformed",
        "workpiece": None, "third_medium": None,
    }.items():
        _literal(task, key, value, "task")
    if not isinstance(task["task_id"], str) or not task["task_id"]:
        _fail("task_id must be a nonempty string.")
    if task["case_family"] != geometry.metadata["case_family"]:
        _fail("Task case_family does not match the geometry.")
    if _scalar(task["input_auxiliary_spring_N_per_mm"], "input auxiliary spring") != 0:
        _fail("An auxiliary input spring is unsupported by this diagnostic.")
    _keys(task["material"], ("E_MPa", "nu", "formulation"), "material")
    _literal(task["material"], "formulation", "plane_strain", "material")
    _material(task["material"]["E_MPa"], task["material"]["nu"])
    _keys(task["input"], ("tag", "displacement_mm"), "input")
    _keys(task["output"], ("tag", "spring_N_per_mm"), "output")
    _scalar(task["input"]["displacement_mm"], "input displacement")
    _scalar(task["output"]["spring_N_per_mm"], "output spring", nonnegative=True)
    tags = geometry.metadata["region_tags"]
    for port in ("input", "output"):
        if task[port]["tag"] != port or port not in tags:
            _fail(f"HF-1 {port} must use the qualified geometry tag {port!r}.")
    if not isinstance(task["constraints"], list) or not task["constraints"]:
        _fail("constraints must be a nonempty list.")
    constrained_tags = set()
    for constraint in task["constraints"]:
        _keys(constraint, ("tag", "components"), "constraint")
        if not isinstance(constraint["tag"], str) or constraint["tag"] not in tags:
            _fail("Unknown constraint region tag.")
        comps = constraint["components"]
        if not isinstance(comps, list) or not comps or any(type(c) is not int or c not in (0, 1) for c in comps):
            _fail("Constraint components must list 0 (x) and/or 1 (y).")
        name = constraint["tag"]
        expected_components = {"support": {0, 1}, "symmetry": {1}}
        if name not in expected_components or set(comps) != expected_components[name] or len(comps) != len(set(comps)):
            _fail("HF-1 supports fixed x/y support and y-only symmetry constraints.")
        if name in constrained_tags:
            _fail("Each constraint tag must be declared once.")
        constrained_tags.add(name)
    required_tags = {"support"} | ({"symmetry"} if "symmetry" in tags else set())
    if constrained_tags != required_tags:
        _fail("HF-1 constraints must include the support and every declared symmetry tag.")
    criteria = task["qualification_criteria"]
    if not isinstance(criteria, dict):
        _fail("qualification_criteria must be an object.")
    if set(criteria) - {"max_design_volume_fraction", "min_feature_mm"}:
        _fail("qualification_criteria contains unsupported fields.")
    for name, value in criteria.items():
        if value is None:
            continue
        number = _scalar(value, name, positive=name == "min_feature_mm")
        if name == "max_design_volume_fraction" and not 0 <= number <= 1:
            _fail("max_design_volume_fraction must lie between 0 and 1.")
    _keys(solver, (
        "schema_version", "solver_id", "analysis", "quadrature", "dtype", "linear_solver",
        "relative_force_tolerance", "constraint_relative_tolerance", "constraint_scale_floor_mm", "time_limit_seconds",
    ), "solver")
    for key, value in {
        "schema_version": "hf-solver-1.0", "solver_id": "hf1_q1_solid_linear_v1",
        "analysis": "solid_linear_q1", "quadrature": "gauss_2x2",
        "dtype": "float64", "linear_solver": "scipy_superlu",
    }.items():
        _literal(solver, key, value, "solver")
    for key in ("relative_force_tolerance", "constraint_relative_tolerance", "constraint_scale_floor_mm", "time_limit_seconds"):
        _scalar(solver[key], key, positive=True)


def analyze(geometry, task, solver):
    """Analyze a validated geometry without writing files or mutating inputs."""
    start = perf_counter()
    _validate_configs(geometry, task, solver)
    E = float(task["material"]["E_MPa"])
    nu = float(task["material"]["nu"])
    hx, hy = geometry.grid["cell_size_mm"]
    thickness = _scalar(geometry.metadata["thickness_mm"], "thickness_mm", positive=True)
    d = float(task["input"]["displacement_mm"])
    k_out = float(task["output"]["spring_N_per_mm"])
    coordinates = node_coordinates(geometry)
    active = active_nodes(geometry)
    if not np.any(active):
        _fail("The geometry has no solid elements.", code="empty_solid")
    active_dofs = np.flatnonzero(np.repeat(active, 2))
    n_full = 2 * len(coordinates)
    dof_map = np.full(n_full, -1, dtype=np.int64)
    dof_map[active_dofs] = np.arange(len(active_dofs))
    solid_indices = np.flatnonzero(geometry.solid.ravel(order="C"))
    solid_conn = element_connectivity(geometry)[solid_indices]
    full_edofs = (2 * solid_conn[:, :, None] + np.array([0, 1])).reshape(-1, 8)
    edofs = dof_map[full_edofs]
    ke = element_stiffness(E, nu, hx, hy, thickness)
    rows = np.broadcast_to(edofs[:, :, None], (len(edofs), 8, 8)).ravel()
    cols = np.broadcast_to(edofs[:, None, :], (len(edofs), 8, 8)).ravel()
    values = np.broadcast_to(ke, (len(edofs), 8, 8)).ravel()
    K = sparse.coo_matrix((values, (rows, cols)), shape=(len(active_dofs), len(active_dofs))).tocsc()
    tags = geometry.metadata["region_tags"]
    input_b, input_nodes, input_weights = port_vector(geometry, tags[task["input"]["tag"]])
    output_b, output_nodes, output_weights = port_vector(geometry, tags[task["output"]["tag"]])
    for name, nodes in (("input", input_nodes), ("output", output_nodes)):
        if len(nodes) == 0 or not np.all(active[nodes]):
            _fail(f"Every {name} port node must touch a solid element; weights were not changed.", code="port_not_attached", port=name)
    fixed_parts = []
    for constraint in task["constraints"]:
        selected = region_nodes(geometry, tags[constraint["tag"]])
        attached = selected[active[selected]]
        if len(attached) == 0:
            _fail("A constraint region has no solid-incident nodes.", code="constraint_not_attached", tag=constraint["tag"])
        fixed_parts.append((2 * attached[:, None] + np.asarray(constraint["components"])).ravel())
    fixed_full = np.unique(np.concatenate(fixed_parts)) if fixed_parts else np.empty(0, dtype=np.int64)
    assembly_seconds = perf_counter() - start
    if assembly_seconds > solver["time_limit_seconds"]:
        _fail("Analysis time limit exceeded during assembly.", code="time_limit_exceeded", stage="assembly")
    # E [N/mm²] * t [mm] * d [mm] supplies a task-based nonzero force scale.
    # At exactly zero input the declared displacement floor keeps 0/0 impossible.
    force_displacement_scale = abs(d) if d != 0 else float(solver["constraint_scale_floor_mm"])
    force_floor = E * thickness * force_displacement_scale
    solved = solve_average_system(
        K, input_b[active_dofs], d, dof_map[fixed_full], k_out,
        output_b[active_dofs], force_scale_floor=force_floor,
    )
    post_start = perf_counter()
    constraint_scale = max(abs(d), float(solver["constraint_scale_floor_mm"]))
    relative_constraint = solved["constraint_error_mm"] / constraint_scale
    if solved["relative_force_residual"] > solver["relative_force_tolerance"] or relative_constraint > solver["constraint_relative_tolerance"]:
        _fail(
            "The linear solution did not meet the force or average-constraint tolerance.",
            code="equilibrium_tolerance_not_met", stage="verification",
            relative_force_residual=solved["relative_force_residual"],
            constraint_relative_error=relative_constraint,
        )
    u = np.zeros(n_full)
    u[active_dofs] = solved["u"]
    reaction = np.zeros(n_full)
    reaction[active_dofs] = solved["support_reaction_N"]
    B, area_weight = _quadrature(hx, hy)
    strain = np.einsum("qij,ej->eqi", B, u[full_edofs])
    stress = np.einsum("ij,eqj->eqi", _material(E, nu), strain)
    integrated_energy = float(0.5 * area_weight * thickness * np.sum(strain * stress))
    result = {
        key: value for key, value in solved.items()
        if key not in ("u", "free_dofs", "fixed_dofs", "support_reaction_N", "linear_solve_seconds")
    }
    result.update({
        "analysis": "solid_linear_q1", "status": "success",
        "model_scope": "HF-1 solid-only linear interface diagnostic; no TMC or contact",
        "units": {"length": "mm", "force": "N", "stress": "MPa", "energy": "N mm"},
        "element_count": int(len(solid_indices)), "active_node_count": int(np.count_nonzero(active)),
        "n_dof": int(len(active_dofs)), "fixed_count": int(len(fixed_full)),
        "reached_input_mm": solved["q_in_mm"],
        "constraint_scale_mm": constraint_scale, "constraint_relative_error": relative_constraint,
        "integrated_strain_energy_N_mm": integrated_energy,
        "strain_components": ["epsilon_xx", "epsilon_yy", "gamma_xy"],
        "stress_components": ["sigma_xx", "sigma_yy", "tau_xy"],
        "quadrature_order": "eta outer, xi inner; each coordinate [-1/sqrt(3),+1/sqrt(3)]",
        "output_force_sign": "force on structure = -k_out*q_out along output reference direction",
        "support_reaction_sign": "force on structure at zero prescribed-displacement DOFs",
    })
    result["timing_seconds"] = {
        "assembly": assembly_seconds, "linear_solve": solved["linear_solve_seconds"],
        "postprocess": perf_counter() - post_start, "total": perf_counter() - start,
    }
    if result["timing_seconds"]["total"] > solver["time_limit_seconds"]:
        _fail("Analysis time limit exceeded.", code="time_limit_exceeded", stage="verification", elapsed_seconds=result["timing_seconds"]["total"])
    arrays = {
        "u": u, "active_nodes": active, "active_dofs": active_dofs,
        "coordinates": coordinates, "solid_connectivity": solid_conn,
        "solid_element_indices": solid_indices,
        "input_b": input_b, "output_b": output_b,
        "input_nodes": input_nodes, "output_nodes": output_nodes,
        "input_weights": input_weights, "output_weights": output_weights,
        "fixed_dofs": fixed_full, "support_reaction_N": reaction,
        "strain_gauss": strain, "stress_gauss_MPa": stress,
    }
    return result, arrays
