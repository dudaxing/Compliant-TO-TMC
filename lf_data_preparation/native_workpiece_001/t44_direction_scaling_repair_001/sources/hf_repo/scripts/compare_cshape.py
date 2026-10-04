"""Offline comparison of every common original C-shape target; no nonlinear solve.

Both paths and their completion status are retained. A partial common path can
agree while the full benchmark remains not_pass. Only NumPy postprocessing is
used, independent of the production JAX element and global assembler.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(a):
    return float(np.linalg.norm(np.asarray(a).ravel()))


def read_npz(path):
    with np.load(path, allow_pickle=False) as source:
        arrays = {name: source[name] for name in source.files}
    if any(value.dtype.kind not in "biuf" or not np.all(np.isfinite(value)) for value in arrays.values()):
        raise ValueError(f"Nonfinite or nonnumeric input array in {path}")
    return arrays


def independent_state(u, model, spec):
    """Direct analytic Piola force and mixed-Hessian residual, no kernel calls."""
    nx, ny = spec["cshape"]["cells"]
    Lx, Ly = spec["cshape"]["domain"]
    hx, hy = Lx/nx, Ly/ny
    t = spec["cshape"]["thickness_factor"]
    E, nu, alpha = (spec["material"][k] for k in ("E", "nu", "alpha"))
    gamma = model["gamma"]
    lam = E*nu/((1+nu)*(1-2*nu))*gamma
    mu = E/(2*(1+nu))*gamma
    kr = alpha*Lx**2*(E/(3*(1-2*nu))+4*(E/(2*(1+nu)))/3)
    signs = np.array([[-1., -1.], [1., -1.], [1., 1.], [-1., 1.]])
    points = np.array([(x, y) for x in (-1., 0., 1.) for y in (-1., 0., 1.)])
    gradients = np.empty((9, 4, 2))
    for a, (sx, sy) in enumerate(signs):
        gradients[:, a, 0] = sx*(1+sy*points[:, 1])/(2*hx)
        gradients[:, a, 1] = sy*(1+sx*points[:, 0])/(2*hy)
    univariate = {-1.: 1/3, 0.: 4/3, 1.: 1/3}
    weights = np.array([univariate[x]*univariate[y]*hx*hy*t/4 for x, y in points])
    nodal = u.reshape(-1, 2)[model["connectivity"]]
    F = np.eye(2)+np.einsum("eai,qaj->eqij", nodal, gradients)
    J = F[..., 0, 0]*F[..., 1, 1]-F[..., 0, 1]*F[..., 1, 0]
    if not np.all(np.isfinite(J)) or np.min(J) <= 0:
        raise ValueError("Independent postprocessing rejects nonpositive or nonfinite J")
    # P = mu F + (lambda log J - mu) F^{-T}, independent of second-Piola code.
    inverse_transpose = np.empty_like(F)
    inverse_transpose[..., 0, 0] = F[..., 1, 1]/J
    inverse_transpose[..., 0, 1] = -F[..., 1, 0]/J
    inverse_transpose[..., 1, 0] = -F[..., 0, 1]/J
    inverse_transpose[..., 1, 1] = F[..., 0, 0]/J
    logJ = np.log(J)
    P = mu[:, None, None, None]*F+(lam[:, None]*logJ-mu[:, None])[..., None, None]*inverse_transpose
    material = np.einsum("q,qaj,eqij->eai", weights, gradients, P)
    mixed_signs = signs[:, 0]*signs[:, 1]
    mixed = np.einsum("a,eai->ei", mixed_signs, nodal)/(hx*hy)
    integral = np.exp(-5*J) @ weights
    regularization = 2*kr/(hx*hy)*integral[:, None, None]*mixed_signs[None, :, None]*mixed[:, None, :]
    edofs = (2*model["connectivity"][..., None]+np.arange(2)).reshape(-1, 8)
    internal = np.zeros(len(u))
    np.add.at(internal, edofs.ravel(), (material+regularization).ravel())
    trace_C = np.sum(F*F, axis=(-1, -2))
    W = .5*(lam[:, None]*logJ**2+mu[:, None]*(trace_C-2-2*logJ))
    energy = W @ weights
    return dict(J=J, internal=internal, energy=energy)


def error_measure(actual, reference, floor):
    absolute = norm(np.asarray(actual)-np.asarray(reference))
    denominator = max(norm(reference), float(floor))
    return absolute, denominator, absolute/denominator


def compare_paths(python_dir, matlab_dir, spec_path, output):
    started = perf_counter()
    python_dir, matlab_dir, output = map(Path, (python_dir, matlab_dir, output))
    output.mkdir(parents=True, exist_ok=True)
    (output/"validation_spec_used.json").write_bytes(Path(spec_path).read_bytes())
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8-sig"))
    target_spec = spec["cshape"]
    py = read_npz(python_dir/"cshape_path.npz")
    py_model = read_npz(python_dir/"model.npz")
    py_meta = json.loads((python_dir/"result.json").read_text(encoding="utf-8-sig"))
    ma = read_npz(matlab_dir/"cshape_path.npz")
    ma_meta = json.loads((matlab_dir/"cshape_path.json").read_text(encoding="utf-8-sig"))
    model = {k: ma[k] for k in ("coordinates", "connectivity", "gamma", "F0", "fixed_dofs", "loaded_nodes")}
    model["connectivity"] = model["connectivity"].astype(np.int64)
    model["fixed_dofs"] = model["fixed_dofs"].astype(np.int64).ravel()
    model["loaded_nodes"] = model["loaded_nodes"].astype(np.int64).ravel()
    model["gamma"] = model["gamma"].ravel()
    model["F0"] = model["F0"].ravel()
    targets = ma["original_targets"].ravel()
    nx, ny = target_spec["cells"]
    Lx, Ly = target_spec["domain"]
    hx, hy = Lx/nx, Ly/ny
    ne, ndof = nx*ny, 2*(nx+1)*(ny+1)
    t, E = target_spec["thickness_factor"], spec["material"]["E"]
    fixed, loaded = model["fixed_dofs"], model["loaded_nodes"]
    free = np.setdiff1d(np.arange(ndof), fixed)
    solid = model["gamma"] == 1.
    medium = model["gamma"] == 1e-6
    # Independently bind both models to the frozen benchmark, not only each other.
    expected_X = np.array([(ix*hx, iy*hy) for iy in range(ny+1) for ix in range(nx+1)])
    ll = np.array([iy*(nx+1)+ix for iy in range(ny) for ix in range(nx)])
    expected_conn = ll[:, None]+np.array([0, 1, nx+2, nx+1])
    expected_fixed = np.array([2*iy*(nx+1)+c for iy in range(ny+1) for c in (0, 1)])
    expected_loaded = ny*(nx+1)+np.arange(55, 61)
    expected_gamma = np.array([1. if (((iy < 6 or iy >= 24) and ix < 60) or ix < 6) else 1e-6
                               for iy in range(ny) for ix in range(nx)])
    expected_force = np.zeros(ndof)
    expected_force[2*expected_loaded+1] = [-.3, -.6, -.6, -.6, -.6, -.3]
    setup_checks = []
    def setup_check(name, passed):
        setup_checks.append(dict(check=name, status="pass" if passed else "fail"))
    for name, expected in (("connectivity", expected_conn), ("gamma", expected_gamma),
                           ("fixed_dofs", expected_fixed), ("loaded_nodes", expected_loaded)):
        actual = np.sort(model[name]) if name == "fixed_dofs" else model[name]
        setup_check("matlab_frozen_"+name, np.array_equal(actual, expected))
        other_key = "factors" if name == "gamma" else name
        actual_py = np.sort(py_model[other_key]) if name == "fixed_dofs" else py_model[other_key]
        setup_check("python_frozen_"+name, np.array_equal(actual_py, expected))
    for name, expected in (("coordinates", expected_X), ("F0", expected_force)):
        setup_check("matlab_frozen_"+name, np.allclose(model[name], expected, atol=1e-12, rtol=0))
        setup_check("python_frozen_"+name, np.allclose(py_model[name], expected, atol=1e-12, rtol=0))
    setup_check("original_100_targets", len(targets) == 100 and np.allclose(targets, np.linspace(.01, 1., 100), atol=2e-15, rtol=0))
    setup_check("python_exact_source_targets", np.array_equal(py_model["targets"], targets))
    setup_check("python_source_hash", py_meta["benchmark_config"]["source_zip_sha256"] == spec["source_zip_sha256"])
    reference_source_hash = ma_meta.get("source_zip_sha256", ma_meta.get("source_hash"))
    setup_check("matlab_source_hash", reference_source_hash == spec["source_zip_sha256"])
    setup_check("model_region_counts", int(solid.sum()) == target_spec["solid_cells"] and int(medium.sum()) == target_spec["medium_cells"])
    rows, validity, delta_arrays, failures = [], [], {}, []
    py_levels, ma_levels = py["lambda"].ravel(), ma["targets"].ravel()
    if len(np.unique(py_levels)) != len(py_levels) or len(np.unique(ma_levels)) != len(ma_levels):
        raise ValueError("Repeated accepted multipliers make target correspondence ambiguous")
    common = []
    for target_index, level in enumerate(targets, 1):
        py_indices = np.flatnonzero((py_levels == level) & py["original_target"].astype(bool))
        ma_indices = np.flatnonzero(ma_levels == level)
        if len(py_indices) == len(ma_indices) == 1:
            common.append((target_index, float(level), int(py_indices[0]), int(ma_indices[0])))
    # Metrics at every common original target; no endpoint-only selection.
    compared = {key: [] for key in ("lambda", "delta_U", "delta_loaded_displacements", "delta_reaction", "delta_J",
                                   "python_independent_internal", "matlab_independent_internal")}
    for target_index, level, pi, mi in common:
        row = dict(target_index=target_index, load_multiplier=level, python_index=pi, matlab_index=mi)
        try:
            pu, mu = py["U"][pi], ma["U"][mi]
            pj, mj = py["J"][pi], ma["J"][mi]
            pr, mr = py["support_reaction"][pi], ma["reaction"][mi]
            measurements = [
                ("U", pu, mu, 1e-6*Lx, target_spec["U_and_loaded_nodes_relative_tolerance"]),
                ("loaded_displacements", pu.reshape(-1,2)[loaded], mu.reshape(-1,2)[loaded], 1e-6*Lx, target_spec["U_and_loaded_nodes_relative_tolerance"]),
                ("support_reaction", pr[fixed], mr[fixed], 1e-8*3*level, target_spec["reaction_relative_tolerance"]),
                ("solid_material_energy", py["solid_material_energy"][pi], ma["material_energy_solid"][mi], 1e-8*E*t*solid.sum()*hx*hy, target_spec["region_material_energy_relative_tolerance"]),
                ("medium_material_energy", py["medium_material_energy"][pi], ma["material_energy_medium"][mi], 1e-8*E*1e-6*t*medium.sum()*hx*hy, target_spec["region_material_energy_relative_tolerance"]),
                ("J_field", pj, mj, 1e-8*np.sqrt(9*ne), target_spec["J_field_relative_tolerance"])]
            for name, actual, reference, floor, tolerance in measurements:
                absolute, denominator, relative = error_measure(actual, reference, floor)
                row.update({name+"_absolute_error": absolute, name+"_denominator": denominator,
                            name+"_relative_error": relative, name+"_tolerance": tolerance,
                            name+"_pass": relative <= tolerance})
            min_error = abs(float(pj.min())-float(mj.min()))
            row.update(min_J_absolute_error=min_error, min_J_tolerance=target_spec["min_J_absolute_tolerance"],
                       min_J_pass=min_error <= target_spec["min_J_absolute_tolerance"])
            for n, node in enumerate(loaded):
                for c, name in enumerate(("ux", "uy")):
                    row[f"loaded_node_{n}_{name}_absolute_difference"] = abs(pu[2*node+c]-mu[2*node+c])
            for side, u, stored_j, reaction, payload, index, energy_keys, residual_key in (
                ("python", pu, pj, pr, py, pi, ("solid_material_energy", "medium_material_energy"), "relative_residual"),
                ("matlab", mu, mj, mr, ma, mi, ("material_energy_solid", "material_energy_medium"), "relative_free_residual")):
                state = independent_state(u, model, spec)
                external = level*model["F0"]
                residual = state["internal"]-external
                independent_reaction = np.zeros(ndof)
                independent_reaction[fixed] = residual[fixed]
                force_scale = norm(external)
                force_balance_scale = max(force_scale, 3*level)
                balance = reaction.reshape(-1,2).sum(axis=0)+external.reshape(-1,2).sum(axis=0)
                independent_balance = independent_reaction.reshape(-1,2).sum(axis=0)+external.reshape(-1,2).sum(axis=0)
                record = dict(target_index=target_index, load_multiplier=level, side=side,
                              stored_relative_free_residual=float(payload[residual_key][index]),
                              independent_relative_free_residual=norm(residual[free])/force_scale,
                              fixed_displacement_max=float(np.max(np.abs(u[fixed]))),
                              stored_force_balance_absolute=norm(balance),
                              independent_force_balance_absolute=norm(independent_balance),
                              force_balance_scale=force_balance_scale,
                              force_balance_absolute_tolerance=target_spec["global_force_balance_tolerance"]*force_balance_scale,
                              independent_minimum_J=float(state["J"].min()),
                              stored_minimum_J=float(stored_j.min()))
                record["free_residual_pass"] = max(record["stored_relative_free_residual"], record["independent_relative_free_residual"]) <= target_spec["free_residual_tolerance"]
                record["fixed_displacement_pass"] = record["fixed_displacement_max"] <= 1e-12*Lx
                record["balance_pass"] = max(record["stored_force_balance_absolute"], record["independent_force_balance_absolute"]) <= record["force_balance_absolute_tolerance"]
                record["positive_J_pass"] = record["independent_minimum_J"] > 0 and record["stored_minimum_J"] > 0
                # Recomputed quantities diagnose postprocessing consistency using the
                # already frozen path thresholds, not newly tuned local tolerances.
                _, _, j_error = error_measure(state["J"], stored_j, 1e-8*np.sqrt(9*ne))
                _, _, r_error = error_measure(independent_reaction[fixed], reaction[fixed], 1e-8*3*level)
                record.update(independent_J_relative_error=j_error, independent_reaction_relative_error=r_error,
                              independent_J_pass=j_error <= target_spec["J_field_relative_tolerance"],
                              independent_reaction_pass=r_error <= target_spec["reaction_relative_tolerance"])
                for region, mask, key, factor in (("solid", solid, energy_keys[0], 1.), ("medium", medium, energy_keys[1], 1e-6)):
                    _, _, e_error = error_measure(state["energy"][mask].sum(), payload[key][index], 1e-8*E*factor*t*mask.sum()*hx*hy)
                    record["independent_"+region+"_energy_relative_error"] = e_error
                    record["independent_"+region+"_energy_pass"] = e_error <= target_spec["region_material_energy_relative_tolerance"]
                record["status"] = "pass" if all(v for k, v in record.items() if k.endswith("_pass")) else "fail"
                validity.append(record)
                row[side+"_validity_pass"] = record["status"] == "pass"
                compared[side+"_independent_internal"].append(state["internal"])
            compared["lambda"].append(level)
            compared["delta_U"].append(pu-mu)
            compared["delta_loaded_displacements"].append(pu.reshape(-1,2)[loaded]-mu.reshape(-1,2)[loaded])
            compared["delta_reaction"].append(pr-mr)
            compared["delta_J"].append(pj-mj)
            row["status"] = "pass" if all(v for k, v in row.items() if k.endswith("_pass")) else "fail"
        except Exception as exc:
            row["status"] = "fail"
            failures.append(dict(target_index=target_index, load_multiplier=level, exception=type(exc).__name__, message=str(exc)))
        rows.append(row)
    for key, values in compared.items():
        delta_arrays[key] = np.asarray(values)
    np.savez_compressed(output/"per_target_arrays.npz", **delta_arrays)
    for filename, records in (("per_target_errors.csv", rows), ("independent_validity.csv", validity)):
        if records:
            fields = list(dict.fromkeys(key for record in records for key in record))
            with (output/filename).open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(records)
    py_complete = py_meta["status"] == "success" and py_meta["target_reached"] is True and py_meta["original_targets_reached"] == 100
    ma_complete = ma_meta["status"] == "completed" and ma_meta["accepted_count"] == 100
    setup_pass = all(c["status"] == "pass" for c in setup_checks)
    common_pass = bool(rows) and all(row["status"] == "pass" for row in rows)
    full_pass = py_complete and ma_complete and len(common) == 100 and setup_pass and common_pass
    summary = dict(schema_version="hf2-cshape-path-comparison-1.0", full_benchmark_status="pass" if full_pass else "not_pass",
                   common_targets_status="pass" if common_pass else "fail_or_empty", common_original_targets=len(common),
                   expected_original_targets=100, python_status=py_meta["status"], matlab_status=ma_meta["status"],
                   python_original_targets_reached=py_meta["original_targets_reached"], matlab_accepted_count=ma_meta["accepted_count"],
                   python_failure=py_meta.get("failure"), matlab_failure={k:ma_meta[k] for k in ("failed_target_index", "failed_lambda", "error_identifier", "error_message") if k in ma_meta},
                   setup_checks=setup_checks, per_target_errors=rows, independent_validity=validity, failures=failures,
                   norm_convention="Euclidean vectors, Frobenius all tensor components",
                   balance_acceptance="norm(sum support reactions + sum external force) <= 1e-6*max(norm(lambda*F0),3*lambda)",
                   loaded_region="six physical nodes, both ux/uy: twelve displacement components; full vector gated, each component absolute difference retained",
                   units_mode="source_numeric", scope="Specified code benchmark agreement; no independent contact accuracy or mesh-convergence claim",
                   validation_spec_sha256=digest(spec_path), source_zip_sha256=spec["source_zip_sha256"],
                   inputs={"python_path_sha256":digest(python_dir/"cshape_path.npz"), "python_model_sha256":digest(python_dir/"model.npz"),
                           "python_result_sha256":digest(python_dir/"result.json"), "matlab_path_sha256":digest(matlab_dir/"cshape_path.npz"),
                           "matlab_result_sha256":digest(matlab_dir/"cshape_path.json")})
    if rows:
        make_plots(rows, common, py, ma, loaded, output)
    summary["wall_seconds"] = perf_counter()-started
    (output/"summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    return summary


def make_plots(rows, common, py, ma, loaded, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    levels = [item[1] for item in common]
    pi, mi = [item[2] for item in common], [item[3] for item in common]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    pairs = [("Mean loaded-node uy (source length)", py["U"][pi][:, 2*loaded+1].mean(axis=1), ma["U"][mi][:, 2*loaded+1].mean(axis=1)),
             ("Solid material energy (source energy)", py["solid_material_energy"][pi], ma["material_energy_solid"][mi]),
             ("Medium material energy (source energy)", py["medium_material_energy"][pi], ma["material_energy_medium"][mi]),
             ("Support resultant y (source force)", py["support_reaction"][pi][:, 1::2].sum(axis=1), ma["reaction"][mi][:, 1::2].sum(axis=1)),
             ("Minimum determinant J", py["minimum_J"][pi], ma["min_J"][mi]),
             ("Stored relative free residual", py["relative_residual"][pi], ma["relative_free_residual"][mi])]
    for i, (ax, (label, a, b)) in enumerate(zip(axes.ravel(), pairs)):
        ax.plot(levels, b, color="#bd5a29", lw=2, label="MATLAB source")
        ax.plot(levels, a, color="#1b6984", ls="--", lw=1.3, label="Python HF")
        if i in (4, 5):
            ax.set_yscale("log")
        ax.set_ylabel(label)
        ax.set_xlabel("Original load multiplier")
        ax.grid(alpha=.2)
    axes[0, 0].legend()
    fig.suptitle("C-shape: all common original targets; source numeric units")
    fig.tight_layout()
    fig.savefig(output/"response_parity.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for name in ("U", "loaded_displacements", "support_reaction", "solid_material_energy", "medium_material_energy", "J_field"):
        ax.semilogy([r["load_multiplier"] for r in rows], [max(r.get(name+"_relative_error", np.nan)/r.get(name+"_tolerance", 1), 1e-16) for r in rows], label=name.replace("_", " "))
    ax.semilogy([r["load_multiplier"] for r in rows], [max(r.get("min_J_absolute_error", np.nan)/r.get("min_J_tolerance", 1), 1e-16) for r in rows], label="min J absolute")
    ax.axhline(1, color="black", ls="--", label="acceptance limit")
    ax.set_xlabel("Original load multiplier")
    ax.set_ylabel("Measured error / frozen tolerance")
    ax.set_title("Every common original target and every frozen parity metric")
    ax.grid(alpha=.2)
    ax.legend(loc="best", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(output/"error_vs_load.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--matlab", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = compare_paths(args.python, args.matlab, args.spec, args.output)
    print(json.dumps({k: summary[k] for k in ("full_benchmark_status", "common_targets_status", "common_original_targets", "python_status", "matlab_status", "failures", "wall_seconds")}, indent=2))
    return 0 if summary["full_benchmark_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
