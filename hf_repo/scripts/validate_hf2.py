"""Independent, bounded HF-2 numerical validation; never runs C-shape.

Run with the HF package installed (or an explicit HF-only development path),
CPU JAX/x64 enabled, and a process timeout of at most 300 seconds. Numerical
fixtures contain no MATLAB executable source and are verified before loading.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import threading
from time import perf_counter

import numpy as np


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(a):
    """Euclidean/Frobenius over all entries, including batched tensors."""
    return float(np.linalg.norm(np.asarray(a).ravel()))


def case_definitions(spec):
    E, nu, alpha = (spec["material"][key] for key in ("E", "nu", "alpha"))
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    result = []
    for size_id, (hx, hy) in zip("ab", spec["local_sizes"]):
        for field in range(len(spec["nonaffine_fields"])):
            for label, gamma in zip(("solid", "tm"), spec["material"]["factors"]):
                result.append(dict(case_id=f"element_{size_id}_field{field}_{label}",
                                   kind="element", nx=1, ny=1, hx=hx, hy=hy,
                                   Lx=hx, Ly=hy, field_id=field, gamma=np.array([gamma])))
    for nx, ny in spec["small_meshes_nx_ny"]:
        Lx, Ly = spec["small_mesh_domain"]
        gamma = np.where(np.arange(nx * ny) % 2 == 0, 1., 1e-6)
        result.append(dict(case_id=f"mesh_{nx}x{ny}_field0_alternating", kind="global",
                           nx=nx, ny=ny, hx=Lx / nx, hy=Ly / ny, Lx=Lx, Ly=Ly,
                           field_id=spec["small_mesh_field_index"], gamma=gamma))
    for case in result:
        case.update(E=E, nu=nu, alpha=alpha, lam_solid=lam, mu_solid=mu, thickness=1.)
        case["kr"] = alpha * case["Lx"] ** 2 * (E / (3 * (1 - 2 * nu)) + 4 * mu / 3)
    return result


def independent_mesh(case):
    nx, ny, hx, hy = (case[k] for k in ("nx", "ny", "hx", "hy"))
    coordinates = np.array([(ix * hx, iy * hy) for iy in range(ny + 1) for ix in range(nx + 1)])
    connectivity = np.array([[iy*(nx+1)+ix, iy*(nx+1)+ix+1,
                              (iy+1)*(nx+1)+ix+1, (iy+1)*(nx+1)+ix]
                             for iy in range(ny) for ix in range(nx)], dtype=np.int64)
    edofs = np.array([[2*n+c for n in cell for c in (0, 1)] for cell in connectivity])
    return coordinates, connectivity, edofs


def field_displacement(coordinates, field):
    x, y = coordinates.T
    monomials = np.column_stack((x, y, x*y))
    return np.column_stack((monomials @ field["ux_x_y_xy"],
                            monomials @ field["uy_x_y_xy"])).ravel()


def independent_operators(hx, hy, thickness=1.):
    """Different construction: nodal signs and tensor-product shape derivatives."""
    signs = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]])
    pts = np.array([(x, y) for x in (-1., 0., 1.) for y in (-1., 0., 1.)])
    grad = np.zeros((9, 4, 2))
    hessian = np.zeros((4, 2, 2))
    for a, (sx, sy) in enumerate(signs):
        grad[:, a, 0] = sx * (1 + sy*pts[:, 1]) / (2*hx)
        grad[:, a, 1] = sy * (1 + sx*pts[:, 0]) / (2*hy)
        hessian[a, 0, 1] = hessian[a, 1, 0] = sx*sy/(hx*hy)
    univariate = {-1.: 1/3, 0.: 4/3, 1.: 1/3}
    weights = np.array([univariate[x]*univariate[y]*hx*hy*thickness/4 for x, y in pts])
    return dict(grad=grad, hessian=hessian, weights=weights, points=pts)


def independent_fields(ue, ops, lam, mu):
    F = np.empty((len(ue), 9, 2, 2))
    for e, local in enumerate(ue):
        for q in range(9):
            F[e, q] = np.eye(2) + local.reshape(4, 2).T @ ops["grad"][q]
    J = np.linalg.det(F)
    C = np.swapaxes(F, -1, -2) @ F
    inverse = np.linalg.inv(C)
    S = lam[:, None, None, None]*np.log(J)[..., None, None]*inverse + mu[:, None, None, None]*(np.eye(2)-inverse)
    W = .5*(lam[:, None]*np.log(J)**2 + mu[:, None]*(np.trace(C, axis1=-2, axis2=-1)-2-2*np.log(J)))
    return dict(F=F, J=J, stress_second_piola=S, material_energy=W @ ops["weights"])


class Checks:
    def __init__(self):
        self.rows = []

    def compare(self, case_id, name, actual, expected, tolerance, scale=1., *, zero=False):
        a, b = np.asarray(actual), np.asarray(expected)
        if a.shape != b.shape:
            raise ValueError(f"{case_id}/{name}: shape {a.shape} != {b.shape}")
        denominator = float(scale) if zero else max(norm(b), 1e-8*float(scale))
        error = norm(a-b)/denominator if denominator > 0 else (0. if norm(a-b) == 0 else float("inf"))
        passed = bool(np.all(np.isfinite(a)) and np.all(np.isfinite(b)) and error <= tolerance)
        self.rows.append(dict(case_id=case_id, check=name, status="pass" if passed else "fail",
                              error=error, tolerance=float(tolerance), physical_scale=float(scale),
                              denominator=denominator, absolute_error=norm(a-b)))
        return passed

    def condition(self, case_id, name, passed, **details):
        self.rows.append(dict(case_id=case_id, check=name, status="pass" if passed else "fail", **details))


def load_fixtures(directory, spec_path):
    directory, spec_path = Path(directory).resolve(), Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    index_path = directory / "small_reference_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8-sig"))
    if index["source_zip_sha256"] != spec["source_zip_sha256"]:
        raise ValueError("reference source ZIP hash does not match frozen spec")
    if index["validation_spec_sha256"] != sha256(spec_path):
        raise ValueError("reference validation spec hash does not match frozen spec")
    expected = {c["case_id"] for c in case_definitions(spec)}
    entries = index["cases"]
    if len(entries) != len(expected) or {e["case_id"] for e in entries} != expected:
        raise ValueError("reference must contain all and only the 16 predefined cases")
    loaded = {}
    for entry in entries:
        relative = Path(entry["npz_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("reference path must be relative without traversal")
        path = (directory / relative).resolve()
        if not path.is_relative_to(directory):
            raise ValueError("reference symlink escapes fixture root")
        digest = entry.get("npz_sha256", entry.get("sha256"))
        if not digest or sha256(path) != digest:
            raise ValueError(f"reference hash mismatch: {entry['case_id']}")
        with np.load(path, allow_pickle=False) as archive:
            arrays = {key: archive[key] for key in archive.files}
        if any(a.dtype.kind not in "biuf" or not np.all(np.isfinite(a)) for a in arrays.values()):
            raise ValueError("reference arrays must be finite real numeric arrays")
        loaded[entry["case_id"]] = (entry, arrays)
    return spec, index, loaded


def dense_sum(edofs, fields, ndof):
    R = np.zeros(ndof)
    K = np.zeros((ndof, ndof)) if "tangent" in fields else None
    for e, dofs in enumerate(edofs):
        for a, i in enumerate(dofs):
            R[i] += fields["residual"][e, a]
            if K is not None:
                for b, j in enumerate(dofs):
                    K[i, j] += fields["tangent"][e, a, b]
    return K, R


def validate_case(case, reference, spec, checks, *, finite_differences=True):
    from hf_eval.tmc_kernel import operators, batch_response, determinants
    from hf_eval.tmc import TMCModel, assemble

    started = perf_counter()
    cid = case["case_id"]
    meta, ref = reference
    X, conn, edofs = independent_mesh(case)
    ne, ndof = len(conn), 2*len(X)
    U = field_displacement(X, spec["nonaffine_fields"][case["field_id"]])
    ue = U[edofs]
    hx, hy, t = case["hx"], case["hy"], case["thickness"]
    hstar = np.sqrt(hx*hy)
    gamma = case["gamma"]
    lam, mu = case["lam_solid"]*gamma, case["mu_solid"]*gamma
    kr = case["kr"]
    ops = operators(hx, hy, t)
    expected_ops = independent_operators(hx, hy, t)
    op_tol, parity_tol = spec["matlab_operator_J_tolerance"], spec["matlab_residual_tangent_tolerance"]
    checks.condition(cid, "declared_inputs", meta["field_id"] == case["field_id"] and
                     meta["kind"] == case["kind"] and meta["mesh"] == [case["nx"], case["ny"]] and
                     np.array_equal(np.asarray(meta["domain"]), [case["Lx"], case["Ly"]]) and
                     meta["E"] == case["E"] and meta["nu"] == case["nu"] and
                     meta["alpha"] == case["alpha"] and meta["thickness_factor"] == t)
    checks.compare(cid, "canonical_coordinates", ref["coordinates"].reshape(X.shape), X, op_tol, max(hx, hy))
    checks.condition(cid, "canonical_connectivity", np.array_equal(ref["connectivity"].reshape(conn.shape), conn))
    checks.condition(cid, "canonical_dof_connectivity", np.array_equal(ref["dof_connectivity"].reshape(edofs.shape), edofs))
    checks.compare(cid, "prescribed_displacement", ref["u_canonical"].ravel(), U, op_tol, hstar)
    checks.compare(cid, "local_displacement", ref["element_u"].reshape(ne, 8), ue, op_tol, hstar)
    checks.condition(cid, "material_factors", np.array_equal(ref["gamma"].ravel(), gamma))
    for name in ("lam_solid", "mu_solid", "kr"):
        checks.compare(cid, name, np.asarray(ref[name]).reshape(()), np.asarray(case[name]), op_tol, max(case[name], 1e-30))
    # Verify the exported permutations against coordinates, not only against each other.
    source_X = ref["coordinates_source"].reshape(X.shape)
    s2c = ref["source_to_canonical_nodes"].astype(int).ravel()
    c2s = ref["canonical_to_source_nodes"].astype(int).ravel()
    valid = np.array_equal(np.sort(s2c), np.arange(len(X))) and np.array_equal(s2c[c2s], np.arange(len(X)))
    checks.condition(cid, "node_permutation_bijection", valid)
    checks.compare(cid, "node_permutation_coordinates", source_X[c2s], X, op_tol, max(hx, hy))
    c2d = ref["canonical_to_source_dofs"].astype(int).ravel()
    expected_c2d = np.array([2*n+c for n in c2s for c in (0, 1)])
    checks.condition(cid, "dof_permutation", np.array_equal(c2d, expected_c2d))
    source_R, source_K = ref["residual_source"].ravel(), ref["tangent_source"].reshape(ndof, ndof)
    checks.compare(cid, "source_to_canonical_residual", source_R[c2d], ref["residual_canonical"].ravel(), op_tol, case["E"]*t*hstar)
    checks.compare(cid, "source_to_canonical_tangent", source_K[np.ix_(c2d, c2d)], ref["tangent_canonical"].reshape(ndof, ndof), op_tol, case["E"]*t)
    for key in ops:
        scale = {"grad": 1/hstar, "hessian": 1/hstar**2, "weights": hx*hy*t, "points": 1.}[key]
        checks.compare(cid, "independent_"+key, ops[key], expected_ops[key], spec["operator_tolerance"], scale)
        checks.compare(cid, "matlab_"+key, ops[key], ref[key].reshape(ops[key].shape), op_tol, scale)

    response_start = perf_counter()
    fields = batch_response(ue, ops, lam, mu, kr)
    first_response_seconds = perf_counter()-response_start
    material = batch_response(ue, ops, lam, mu, 0.)
    regularization = batch_response(ue, ops, 0., 0., kr)
    analytic = independent_fields(ue, expected_ops, lam, mu)
    gamma_scale = norm(gamma)
    scales = dict(force=case["E"]*gamma_scale*t*hstar,
                  tangent=case["E"]*gamma_scale*t,
                  stress=case["E"]*gamma_scale,
                  energy=case["E"]*gamma_scale*t*hx*hy,
                  reg_force=kr*t/hstar*np.sqrt(ne), reg_tangent=kr*t/hstar**2*np.sqrt(ne))
    checks.condition(cid, "base_minimum_J", float(fields["J"].min()) >= spec["fd_min_J"], minimum_J=float(fields["J"].min()))
    for key in ("F", "J", "stress_second_piola", "material_energy"):
        scale = {"F": np.sqrt(ne*9), "J": np.sqrt(ne*9), "stress_second_piola": scales["stress"], "material_energy": scales["energy"]}[key]
        checks.compare(cid, "analytic_"+key, fields[key], analytic[key], spec["affine_rigid_tolerance"], scale)
        checks.compare(cid, "matlab_"+key, fields[key], ref[key].reshape(fields[key].shape), op_tol if key in ("F", "J") else parity_tol, scale)
    local_names = [("residual", fields, "force"), ("tangent", fields, "tangent"),
                   ("material_residual", material, "force"), ("material_tangent", material, "tangent"),
                   ("regularization_residual", regularization, "reg_force"), ("regularization_tangent", regularization, "reg_tangent")]
    for name, source, scale in local_names:
        key = "tangent" if name.endswith("tangent") else "residual"
        expected = ref["element_"+name].reshape(source[key].shape)
        checks.compare(cid, "matlab_element_"+name, source[key], expected, parity_tol, scales[scale])
    checks.compare(cid, "residual_decomposition", fields["residual"], material["residual"]+regularization["residual"], parity_tol, scales["force"]+scales["reg_force"])
    checks.compare(cid, "tangent_decomposition", fields["tangent"], material["tangent"]+regularization["tangent"], parity_tol, scales["tangent"]+scales["reg_tangent"])

    model = TMCModel(X, conn, lam, mu, kr, hx, hy, t, gamma == 1.)
    global_K, global_R, global_fields = assemble(model, U)
    dense_K, dense_R = dense_sum(edofs, fields, ndof)
    for name, actual, direct, expected, scale in (
        ("residual", global_R, dense_R, ref["residual_canonical"].ravel(), scales["force"]+scales["reg_force"]),
        ("tangent", global_K.toarray(), dense_K, ref["tangent_canonical"].reshape(ndof, ndof), scales["tangent"]+scales["reg_tangent"])):
        checks.compare(cid, "dense_vs_sparse_"+name, actual, direct, parity_tol, scale)
        checks.compare(cid, "matlab_global_"+name, actual, expected, parity_tol, scale)
    for name, values, scale_key in (("material", material, "force"), ("regularization", regularization, "reg_force")):
        dk, dr = dense_sum(edofs, values, ndof)
        checks.compare(cid, "matlab_global_"+name+"_residual", dr, ref[name+"_residual_canonical"].ravel(), parity_tol, scales[scale_key])
        checks.compare(cid, "matlab_global_"+name+"_tangent", dk, ref[name+"_tangent_canonical"].reshape(ndof, ndof), parity_tol, scales["tangent" if name == "material" else "reg_tangent"])
    checks.compare(cid, "global_J_order", global_fields["J"], fields["J"], op_tol, np.sqrt(ne*9))

    fd_rows = []
    is_local = case["kind"] == "element"
    base_u = ue[0] if is_local else U
    K = fields["tangent"][0] if is_local else global_K.toarray()
    def response(v):
        if is_local:
            return batch_response(v[None], ops, lam, mu, kr, tangent=False)["residual"][0]
        return assemble(model, v, tangent=False)[1]
    def min_j(v):
        return float(determinants(v if is_local else v[edofs], ops).min())
    if finite_differences:
        for direction_name, fn in (("sin", np.sin), ("cos", np.cos)):
            direction = fn(np.arange(1, len(base_u)+1))
            direction *= hstar/norm(direction)
            kv = K @ direction
            errors = []
            for h in spec["fd_steps"]:
                minus, plus = base_u-h*direction, base_u+h*direction
                jm, jp = min_j(minus), min_j(plus)
                valid = min(jm, jp) >= spec["fd_min_J"]
                error = None
                if valid:
                    fd = (response(plus)-response(minus))/(2*h)
                    denominator = max(norm(kv), 1e-8*(scales["force"]+scales["reg_force"]))
                    error = norm(fd-kv)/denominator
                fd_rows.append(dict(case_id=cid, direction=direction_name, h=h, relative_error=error,
                                    minimum_J_minus=jm, minimum_J_plus=jp, admissible=valid,
                                    direction_length=hstar, tangent_direction_norm=norm(kv)))
                errors.append(error)
            complete = all(error is not None for error in errors)
            checks.condition(cid, "fd_"+direction_name+"_admissibility", complete,
                             required_minimum_J=spec["fd_min_J"])
            if complete:
                best, early = min(errors), errors[0] <= spec["fd_early_reduction_applies_above"] or errors[1]*spec["fd_early_reduction_required"] <= errors[0]
                checks.condition(cid, "fd_"+direction_name+"_best", best <= spec["fd_best_relative_tolerance"], error=best, tolerance=spec["fd_best_relative_tolerance"])
                checks.condition(cid, "fd_"+direction_name+"_early_reduction", early, error_at_1e_2=errors[0], error_at_1e_3=errors[1], required_factor=spec["fd_early_reduction_required"])
    arrays = {cid+"__"+key: value for key, value in fields.items()}
    arrays[cid+"__global_residual"] = global_R
    arrays[cid+"__global_tangent"] = global_K.toarray()
    timing = dict(case_id=cid, wall_seconds=perf_counter()-started,
                  first_response_including_possible_compilation_seconds=first_response_seconds,
                  tangent_asymmetry_ratio=norm(K-K.T)/norm(K))
    return fd_rows, arrays, timing


def validate_analytic(spec, checks):
    from hf_eval.tmc_kernel import operators, element_response
    from hf_eval.linear import element_stiffness
    E, nu = spec["material"]["E"], spec["material"]["nu"]
    lam, mu = E*nu/((1+nu)*(1-2*nu)), E/(2*(1+nu))
    for size_id, (hx, hy) in zip("ab", spec["local_sizes"]):
        cid, hstar = "analytic_"+size_id, np.sqrt(hx*hy)
        X = np.array([[0., 0.], [hx, 0.], [hx, hy], [0., hy]])
        ops = operators(hx, hy)
        x, y = ops["points"].T
        moments = np.array([ops["weights"] @ f for f in (np.ones(9), x, y, x*x, y*y, x*y)])
        exact = hx*hy*np.array([1, 0, 0, 1/3, 1/3, 0])
        checks.compare(cid, "lobatto_moments", moments, exact, spec["operator_tolerance"], hx*hy)
        laplacian = np.trace(ops["hessian"], axis1=1, axis2=2)
        checks.compare(cid, "Q1_Laplacian_zero", laplacian, np.zeros(4), spec["operator_tolerance"], 1/hstar**2, zero=True)
        checks.compare(cid, "gradient_partition_unity", ops["grad"].sum(axis=1), np.zeros((9, 2)), spec["operator_tolerance"], 1/hstar, zero=True)
        theta = .37
        rotation = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
        states = [("translation", np.eye(2), np.array([.31, -.27])*hstar),
                  ("rotation", rotation, np.zeros(2)), ("extension", np.diag([1.1, .9]), np.zeros(2)),
                  ("shear", np.array([[1., .2], [0., 1.]]), np.zeros(2))]
        for gamma in spec["material"]["factors"]:
            kr = spec["material"]["alpha"]*hx**2*(E/(3*(1-2*nu))+4*mu/3)
            for name, F, translation in states:
                state_id = f"{cid}_{name}_gamma{gamma:g}"
                u = (X@(F-np.eye(2)).T+translation).ravel()
                response = element_response(u, ops, gamma*lam, gamma*mu, kr)
                Hu = np.tensordot(u.reshape(4, 2).T, ops["hessian"], axes=(1, 0))
                tol = spec["affine_rigid_tolerance"]
                checks.compare(state_id, "Hu_zero", Hu, np.zeros((2, 2, 2)), tol, 1/hstar, zero=True)
                checks.compare(state_id, "regularization_zero", response["regularization_residual"], np.zeros(8), tol, kr/hstar, zero=True)
                J = np.linalg.det(F)
                invC = np.linalg.inv(F.T@F)
                S = gamma*(lam*np.log(J)*invC+mu*(np.eye(2)-invC))
                W = .5*gamma*(lam*np.log(J)**2+mu*(np.trace(F.T@F)-2-2*np.log(J)))*hx*hy
                checks.compare(state_id, "affine_F", response["F"], np.broadcast_to(F, (9,2,2)), tol)
                checks.compare(state_id, "analytic_stress", response["stress_second_piola"], np.broadcast_to(S, (9,2,2)), tol, E*gamma, zero=name in ("translation", "rotation"))
                checks.compare(state_id, "analytic_energy", response["material_energy"], np.asarray(W), tol, E*gamma*hx*hy, zero=name in ("translation", "rotation"))
                if name in ("translation", "rotation"):
                    checks.compare(state_id, "rigid_residual_zero", response["residual"], np.zeros(8), tol, E*gamma*hstar, zero=True)
        initial = element_response(np.zeros(8), ops, lam, mu, 0.)
        linear = element_stiffness(E, nu, hx, hy, 1.)
        checks.compare(cid, "initial_3x3_vs_HF1_2x2_tangent", initial["tangent"], linear, spec["initial_linear_tangent_tolerance"], E)


def write_plot(rows, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(4, 4, figsize=(16, 12), sharex=True, sharey=True)
    cases = list(dict.fromkeys(row["case_id"] for row in rows))
    for ax, cid in zip(axes.ravel(), cases):
        for direction in ("sin", "cos"):
            selected = [row for row in rows if row["case_id"] == cid and row["direction"] == direction]
            ax.loglog([r["h"] for r in selected], [r["relative_error"] for r in selected], "o-", label=direction)
        ax.axhline(1e-6, color="0.5", ls="--", lw=.8)
        ax.set_title(cid.replace("element_", "el ").replace("_", " "), fontsize=9)
        ax.grid(True, which="both", alpha=.2)
    axes[0, 0].legend()
    fig.supxlabel("Dimensionless central-difference step h")
    fig.supylabel("Euclidean relative directional error")
    fig.suptitle("All 16 frozen cases · both predefined directions · no curve selection")
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def run_validation(fixtures, spec_path, output, *, finite_differences=True):
    started = perf_counter()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/"validation_spec_used.json").write_bytes(Path(spec_path).read_bytes())
    checks, curves, arrays, timings, failures = Checks(), [], {}, [], []
    spec, index, loaded = load_fixtures(fixtures, spec_path)
    for case in case_definitions(spec):
        try:
            rows, data, timing = validate_case(case, loaded[case["case_id"]], spec, checks, finite_differences=finite_differences)
            curves.extend(rows)
            arrays.update(data)
            timings.append(timing)
        except Exception as exc:
            failures.append(dict(case_id=case["case_id"], exception_type=type(exc).__name__, message=str(exc)))
            checks.condition(case["case_id"], "case_execution", False, exception=str(exc))
    try:
        validate_analytic(spec, checks)
    except Exception as exc:
        failures.append(dict(case_id="analytic", exception_type=type(exc).__name__, message=str(exc)))
        checks.condition("analytic", "execution", False, exception=str(exc))
    summary = dict(schema_version="hf2-small-validation-1.0", status="pass" if all(c["status"] == "pass" for c in checks.rows) else "fail",
                   scope="Implementation/source-code agreement; not independent physical contact accuracy validation",
                   units_mode="source_numeric", source_zip_sha256=spec["source_zip_sha256"], validation_spec_sha256=sha256(spec_path),
                   reference_index_sha256=sha256(Path(fixtures)/"small_reference_index.json"),
                   finite_differences_enabled=finite_differences, expected_cases=16, completed_cases=len(timings),
                   checks=checks.rows, finite_difference_rows=len(curves), failures=failures, case_timings=timings,
                   runtime=dict(python=sys.version, platform=platform.platform(),
                                explicit_environment={k: os.environ.get(k) for k in ("JAX_ENABLE_X64", "JAX_PLATFORMS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                   wall_seconds_before_artifact_write=perf_counter()-started)
    np.savez_compressed(output/"numeric_outputs.npz", **arrays)
    if curves:
        with (output/"directional_errors.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(curves[0]))
            writer.writeheader()
            writer.writerows(curves)
        np.savez_compressed(output/"directional_errors.npz",
                            case_id=np.array([r["case_id"] for r in curves]),
                            direction=np.array([r["direction"] for r in curves]),
                            h=np.array([r["h"] for r in curves]),
                            relative_error=np.array([r["relative_error"] if r["relative_error"] is not None else np.nan for r in curves]),
                            admissible=np.array([r["admissible"] for r in curves]),
                            minimum_J_minus=np.array([r["minimum_J_minus"] for r in curves]),
                            minimum_J_plus=np.array([r["minimum_J_plus"] for r in curves]),
                            direction_length=np.array([r["direction_length"] for r in curves]))
        write_plot(curves, output/"directional_error_curves.png")
    summary["wall_seconds"] = perf_counter()-started
    (output/"summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Optional development measurement; runtime HF package does not depend on psutil.
    peak = {"sampled_process_tree_rss_bytes": 0, "monitor": "unavailable"}
    stop = threading.Event()
    def monitor():
        try:
            import psutil
            process = psutil.Process()
            peak["monitor"] = "psutil sampled every 0.1 s; soft observation, not OS hard cap"
            while not stop.is_set():
                rss = sum(p.memory_info().rss for p in [process]+process.children(recursive=True) if p.is_running())
                peak["sampled_process_tree_rss_bytes"] = max(peak["sampled_process_tree_rss_bytes"], rss)
                stop.wait(.1)
        except (ImportError, OSError):
            pass
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    begin = perf_counter()
    try:
        summary = run_validation(args.fixtures, args.spec, args.output)
    finally:
        stop.set()
        thread.join(timeout=1)
        args.output.mkdir(parents=True, exist_ok=True)
        receipt = dict(wall_seconds=perf_counter()-begin, **peak)
        (args.output/"timing_receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    failed = [c for c in summary["checks"] if c["status"] != "pass"]
    print(json.dumps(dict(status=summary["status"], completed_cases=summary["completed_cases"],
                          checks=len(summary["checks"]), failed_checks=failed, failures=summary["failures"],
                          finite_difference_rows=summary["finite_difference_rows"], **receipt), indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
