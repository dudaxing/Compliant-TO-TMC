"""Run the frozen HF-3 prerequisite bridge, never HP or full pilot paths.

Each of six short paths calls the public evaluator from zero with its own task
target and d/16 minimum increment. Sparse matrices, unit linear responses and
all path checkpoints are retained. A passing bridge does not authorize the
full pilots: independent precision and flagged model bias still need review.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
import json
from pathlib import Path
from time import perf_counter

import jax
import numpy as np
from scipy import sparse

from hf_eval.data import canonical_hash
from hf_eval.evaluation import implementation_hash
from hf_eval.linear import analyze as hf1_analyze, element_stiffness, solve_average_system
from hf_eval.project import BACKGROUND_DIAGNOSTIC, build_project
from hf_eval.project_evaluation import evaluate_project
from hf_eval.tmc import assemble
from hf_eval.tmc_kernel import KERNEL_VERSION


REPO = Path(__file__).resolve().parents[1]
FAMILIES = ("inverter", "gripper")
AMPLITUDES = (1e-3, 1e-4, 1e-5)
METRICS = ("output_gain", "input_stiffness", "solid_displacement_gain")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def file_hash(path):
    with Path(path).open("rb") as stream:
        import hashlib
        return hashlib.file_digest(stream, "sha256").hexdigest()


def jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+".tmp")
    temporary.write_text(json.dumps(jsonable(value), ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    temporary.replace(path)


def save_arrays(path, **arrays):
    for name, value in arrays.items():
        values = np.asarray(value)
        if values.dtype.kind not in "biuf" or not np.all(np.isfinite(values)):
            raise ValueError(f"nonordinary or nonfinite array: {name}")
    np.savez_compressed(path, **arrays)


def sparse_norm(matrix):
    value = matrix.tocsc(copy=True)
    value.sum_duplicates()
    return float(np.linalg.norm(value.data))


def relative(actual, expected, floor):
    actual, expected = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    error = float(np.linalg.norm(actual-expected))
    scale = max(float(np.linalg.norm(expected)), float(floor))
    if not np.isfinite(error) or not np.isfinite(scale) or scale <= 0:
        raise ValueError("invalid response comparison scale")
    return {"absolute_error": error, "scale": scale, "relative_error": error/scale}


def responses(project, a, b, spec):
    """Compare dimensionless u/d,q/d and force/length R/d, retaining raw signs."""
    floors = {
        "output_gain": spec["bridge_displacement_gain_floor"],
        "input_stiffness": spec["bridge_stiffness_floor_factor"]*project.material["E_MPa"]*project.model.thickness,
        "solid_displacement_gain": spec["bridge_displacement_gain_floor"]*np.sqrt(len(project.solid_dofs)),
    }
    return {"output_gain": relative(a["q"], b["q"], floors["output_gain"]),
            "input_stiffness": relative(a["R"], b["R"], floors["input_stiffness"]),
            "solid_displacement_gain": relative(a["u"][project.solid_dofs], b["u"][project.solid_dofs], floors["solid_displacement_gain"])}


def assemble_cells(edofs, local, ndof, factors=None):
    edofs = np.asarray(edofs, dtype=np.int64)
    factor = np.ones(len(edofs)) if factors is None else np.asarray(factors)
    values = (factor[:, None, None]*local).ravel()
    rows = np.broadcast_to(edofs[:, :, None], (len(edofs), 8, 8)).ravel()
    cols = np.broadcast_to(edofs[:, None, :], (len(edofs), 8, 8)).ravel()
    matrix = sparse.coo_matrix((values, (rows, cols)), shape=(ndof, ndof)).tocsc()
    matrix.sum_duplicates()
    return matrix


def material_three_point(project):
    """Independent engineering-strain integral at the source 3x3 Lobatto points."""
    grad = project.model.ops["grad"]
    B = np.zeros((9, 3, 8))
    B[:, 0, 0::2], B[:, 1, 1::2] = grad[:, :, 0], grad[:, :, 1]
    B[:, 2, 0::2], B[:, 2, 1::2] = grad[:, :, 1], grad[:, :, 0]
    lam, mu = project.material["lambda_s_MPa"], project.material["mu_s_MPa"]
    D = np.array([[lam+2*mu, lam, 0.], [lam, lam+2*mu, 0.], [0., 0., mu]])
    return np.einsum("qia,ij,qjb,q->ab", B, D, B, project.model.ops["weights"])


def unit_response(matrix, project, dofs=None):
    active = np.arange(project.model.ndof) if dofs is None else np.asarray(dofs)
    mapping = np.full(project.model.ndof, -1, dtype=np.int64)
    mapping[active] = np.arange(len(active))
    fixed_full = project.model.fixed_dofs if dofs is None else np.asarray(project.region_metadata["solid_constraint_dofs"], dtype=np.int64)
    if np.any(mapping[fixed_full] < 0):
        raise ValueError("solid constraint has no active DOF in the reduced reference")
    solved = solve_average_system(matrix, project.bin[active], 1.0, mapping[fixed_full],
        k_out=project.k_out, b_out=project.bout[active],
        force_scale_floor=1e-8*project.material["E_MPa"]*project.model.thickness)
    u = np.zeros(project.model.ndof)
    u[active] = solved["u"]
    return {"u": u, "q": solved["q_out_mm"], "R": solved["R_in_N"],
            "q_in": solved["q_in_mm"], "relative_force_residual": solved["relative_force_residual"],
            "constraint_error_mm": solved["constraint_error_mm"]}


class Bridge:
    def __init__(self, args):
        self.args = args
        self.spec = read_json(args.spec)
        if self.spec.get("schema_version") != "hf3-validation-1.0" or self.spec["bridge_amplitudes_mm"] != list(AMPLITUDES):
            raise ValueError("The three frozen bridge amplitudes and validation schema are required")
        if self.spec["minimum_increment_rule"] != "initial target increment / 16":
            raise ValueError("Unsupported minimum-increment rule")
        self.output = args.output.resolve()
        self.output.mkdir(parents=True, exist_ok=False)
        self.started = perf_counter()
        self.deadline = self.started+float(self.spec["resource_limits"]["category_seconds"]["bridge"])
        self.runtime_hash = implementation_hash()
        self.checks, self.cases, self.errors = [], {}, []
        self.source_paths = [args.spec.resolve(), Path(__file__).resolve(),
            args.dataset/"file_manifest.json", args.dataset/"solvers/hf1_q1_solid_linear_v1.json"]
        for family in FAMILIES:
            self.source_paths += [args.spec.parent/f"{family}_pilot_v1.json",
                args.dataset/f"tasks/{family}_linear_interface_smoke.json",
                args.dataset/f"canonical/{family}/geometry.json", args.dataset/f"canonical/{family}/geometry.npz"]
        self.inputs = [{"path": str(path.resolve()), "sha256": file_hash(path)} for path in self.source_paths]
        self.runs = [{"case_family": family, "d_mm": d, "path": f"{family}/d_{d:.0e}", "status": "not_run",
                      "task_path": f"{family}/tasks/bridge_d_{d:.0e}.json",
                      "solver_path": f"{family}/solvers/bridge_d_{d:.0e}.json"}
                     for family in FAMILIES for d in AMPLITUDES]
        write_json(self.output/"validation_spec_used.json", self.spec)
        self.snapshot("running")

    def remaining(self):
        left = self.deadline-perf_counter()-2.0
        if left <= 0:
            raise TimeoutError("Frozen bridge process budget reached; existing evidence is retained")
        return min(left, self.spec["resource_limits"]["small_process_seconds"])

    def check(self, name, value, limit):
        passed = np.isfinite(value) and value <= limit
        self.checks.append({"check": name, "value": float(value), "tolerance": float(limit), "status": "pass" if passed else "fail"})
        return passed

    def snapshot(self, status):
        write_json(self.output/"runs.json", {"schema_version": "hf3-bridge-runs-1.0", "paths_relative_to": ".", "runs": self.runs})
        write_json(self.output/"summary.json", {
            "schema_version": "hf3-bridge-1.0", "status": status,
            "scope": "prerequisite bridge only; unit references are initial derivatives, not accepted nonlinear states at 1 mm",
            "implementation_sha256": self.runtime_hash, "kernel_version": KERNEL_VERSION,
            "inputs": self.inputs, "spec_sha256": file_hash(self.args.spec),
            "checks": self.checks, "cases": self.cases, "exceptions": self.errors,
            "independent_precision": "not_run", "full_pilot_paths": "not_run", "HF4_executed": False,
            "full_path_gate": "pending independent precision and interpretation of flagged model bias",
            "wall_seconds": perf_counter()-self.started})

    def references(self, family, project, geometry_path, folder):
        self.remaining()
        folder.mkdir(parents=True)
        before_checks = len(self.checks)
        K0, force0, fields0 = assemble(project.model, np.zeros(project.model.ndof), tangent=True)
        self.remaining()
        zero_ok = bool(np.all(force0 == 0) and np.all(fields0["J"] == 1))
        self.check(f"{family}:undeformed_internal_and_J", 0 if zero_ok else 1, 0)
        k0_response = unit_response(K0, project)
        active = project.solid_dofs
        active_map = np.full(project.model.ndof, -1, dtype=np.int64)
        active_map[active] = np.arange(len(active))
        solid_edofs = project.model.edofs[project.model.solid]
        edofs = active_map[solid_edofs]
        local2 = element_stiffness(project.material["E_MPa"], project.material["nu"],
                                  project.model.hx, project.model.hy, project.model.thickness)
        local3 = material_three_point(project)
        K2 = assemble_cells(edofs, local2, len(active))
        K3 = assemble_cells(edofs, local3, len(active))
        solid2, solid3 = unit_response(K2, project, active), unit_response(K3, project, active)
        stiffness_error = sparse_norm(K3-K2)/sparse_norm(K2)
        self.check(f"{family}:solid_3x3_vs_2x2_K", stiffness_error, self.spec["linear_stiffness_relative_tolerance"])

        # Re-run the unchanged HF-1 entry point at a derived unit reference task.
        old_task = read_json(self.args.dataset/f"tasks/{family}_linear_interface_smoke.json")
        hf1_task = deepcopy(old_task)
        hf1_task["task_id"] += "_hf3_unit_reference"
        hf1_task["input"]["displacement_mm"] = 1.0
        hf1_solver = read_json(self.args.dataset/"solvers/hf1_q1_solid_linear_v1.json")
        hf1_solver["time_limit_seconds"] = self.remaining()
        write_json(folder/"hf1_unit_task.json", hf1_task)
        write_json(folder/"hf1_unit_solver.json", hf1_solver)
        hf1, hf1_arrays = hf1_analyze(project.geometry, hf1_task, hf1_solver)
        expected_fixed = np.array(project.region_metadata["solid_constraint_dofs"], dtype=np.int64)
        mappings_match = (np.array_equal(hf1_arrays["active_dofs"], active)
            and np.array_equal(hf1_arrays["fixed_dofs"], expected_fixed)
            and np.array_equal(hf1_arrays["input_b"], project.bin) and np.array_equal(hf1_arrays["output_b"], project.bout))
        self.check(f"{family}:HF1_solid_dofs_constraints_and_ports", 0 if mappings_match else 1, 0)
        hf1_response = {"u": hf1_arrays["u"], "q": hf1["q_out_mm"], "R": hf1["R_in_N"]}
        comparisons = {"solid_3x3_vs_2x2": responses(project, solid3, solid2, self.spec),
                       "assembled_2x2_vs_HF1_entry": responses(project, solid2, hf1_response, self.spec)}
        for comparison, values in comparisons.items():
            for metric, row in values.items():
                self.check(f"{family}:{comparison}:{metric}", row["relative_error"], self.spec["linear_response_relative_tolerance"])

        # At u=0 Hu=0: derivative of exp(-5J)Hu leaves only exp(-5)H^T H.
        hessian = project.model.ops["hessian"]
        local_reg = np.einsum("ajk,bjk,im->aibm", hessian, hessian, np.eye(2)).reshape(8, 8)
        local_reg *= project.model.kr*np.sum(project.model.ops["weights"])*np.exp(-5.0)
        Ksolid = assemble_cells(solid_edofs, local3, project.model.ndof)
        Kmedium = assemble_cells(project.model.edofs[~project.model.solid], local3,
                                  project.model.ndof, project.gamma[~project.model.solid])
        Kreg = assemble_cells(project.model.edofs, local_reg, project.model.ndof)
        k0_norm = sparse_norm(K0)
        decomposition = sparse_norm(K0-Ksolid-Kmedium-Kreg)/k0_norm
        self.check(f"{family}:K0_material_and_HuHu_decomposition", decomposition, self.spec["linear_stiffness_relative_tolerance"])
        bias = responses(project, k0_response, solid3, self.spec)
        bias_flag = any(row["relative_error"] > self.spec["model_bias_flag_threshold"] for row in bias.values())
        sign_change = {name: bool(k0_response[key]*solid3[key] < 0) for name, key in (("output_gain", "q"), ("input_stiffness", "R"))}
        matrices = {"K0_full": K0, "solid_2x2_active": K2, "solid_3x3_active": K3,
                    "K0_solid_material_full": Ksolid, "K0_medium_material_full": Kmedium, "K0_HuHu_full": Kreg}
        for name, matrix in matrices.items():
            sparse.save_npz(folder/(name+".npz"), matrix)
        save_arrays(folder/"unit_responses.npz", coordinates=project.model.coordinates,
            connectivity=project.model.connectivity, solid=project.model.solid, solid_dofs=active,
            solid_element_indices=np.flatnonzero(project.model.solid), bin=project.bin, bout=project.bout,
            full_fixed_dofs=project.model.fixed_dofs, solid_fixed_dofs=expected_fixed,
            local_material_2x2=local2, local_material_3x3=local3, local_HuHu_at_zero=local_reg,
            K0_u=k0_response["u"], K0_R=np.array(k0_response["R"]), K0_q=np.array(k0_response["q"]),
            solid_2x2_u=solid2["u"], solid_2x2_R=np.array(solid2["R"]), solid_2x2_q=np.array(solid2["q"]),
            solid_3x3_u=solid3["u"], solid_3x3_R=np.array(solid3["R"]), solid_3x3_q=np.array(solid3["q"]),
            HF1_u=hf1_response["u"], HF1_R=np.array(hf1_response["R"]), HF1_q=np.array(hf1_response["q"]))
        write_json(folder/"hf1_unit_result.json", hf1)
        report = {"status": "pass" if all(row["status"] == "pass" for row in self.checks[before_checks:]) else "fail",
            "geometry_id": project.geometry.geometry_id, "geometry_descriptor_sha256": project.geometry.metadata["descriptor_sha256"],
            "task_sha256": project.task_hash, "qualification": project.qualification, "regions": project.region_metadata,
            "unit_reference": "d=1 mm linear derivative response only; no finite-deformation acceptance implied",
            "reference_scalars": {name: {"q_out_per_d": data["q"], "R_input_per_d_N_per_mm": data["R"]}
                for name, data in (("K0", k0_response), ("solid_3x3", solid3), ("solid_2x2", solid2), ("HF1", hf1_response))},
            "linear_comparisons": comparisons, "solid_stiffness_relative_error": stiffness_error,
            "K0_decomposition_relative_error": decomposition,
            "initial_stiffness_components": {name: {"frobenius_norm_N_per_mm": sparse_norm(matrix),
                "relative_to_full_K0": sparse_norm(matrix)/k0_norm} for name, matrix in
                (("solid_material", Ksolid), ("medium_material", Kmedium), ("HuHu", Kreg))},
            "A_vs_B_model_bias": {"A": "full TMC initial tangent with task background BC", "B": "solid-only 3x3 reference with entity BC",
                "comparisons": bias, "threshold": self.spec["model_bias_flag_threshold"],
                "status": "model_bias_requires_followup" if bias_flag else "below_diagnostic_flag_threshold",
                "signed_response_changes": sign_change, "not_a_numerical_acceptance_tolerance": True},
            "matrix_files": {name: {"path": name+".npz", "shape": matrix.shape, "sha256": file_hash(folder/(name+".npz"))}
                for name, matrix in matrices.items()}}
        write_json(folder/"reference_summary.json", report)
        return k0_response, report

    def diagnostic(self, project, task, geometry_path, folder, reference):
        self.remaining()
        variant_task = deepcopy(task)
        variant_task["task_id"] += "_background_initial_tangent_diagnostic"
        variant_task["diagnostic_variant"] = BACKGROUND_DIAGNOSTIC
        diagnostic = build_project(geometry_path, variant_task)
        folder.mkdir(parents=True)
        write_json(folder/"task.json", variant_task)
        K, _, _ = assemble(diagnostic.model, np.zeros(diagnostic.model.ndof), tangent=True)
        solved = unit_response(K, diagnostic)
        removed = np.setdiff1d(project.model.fixed_dofs, diagnostic.model.fixed_dofs)
        valid_change = (len(removed) == 20 and np.all(removed % 2 == 1)
            and np.array_equal(project.model.coordinates[removed//2, 0], np.arange(61, 81))
            and project.region_metadata["entity_symmetry"] == diagnostic.region_metadata["entity_symmetry"]
            and project.geometry.geometry_id == diagnostic.geometry.geometry_id)
        self.check("gripper:only_twenty_background_uy_dofs_released", 0 if valid_change else 1, 0)
        save_arrays(folder/"unit_response.npz", u=solved["u"], R=np.array(solved["R"]), q=np.array(solved["q"]),
                    fixed_dofs=diagnostic.model.fixed_dofs, released_dofs=removed)
        sparse.save_npz(folder/"K0_full.npz", K)
        report = {"scope": "single initial-tangent boundary diagnostic; no nonlinear path",
                  "task_sha256": diagnostic.task_hash, "regions": diagnostic.region_metadata,
                  "q_out_per_d": solved["q"], "R_input_per_d_N_per_mm": solved["R"],
                  "comparison_to_main_background": responses(project, solved, reference, self.spec)}
        write_json(folder/"summary.json", report)
        return report

    def short_path(self, family, task, geometry_path, project, reference, run):
        d = run["d_mm"]
        short_task = deepcopy(task)
        short_task["task_id"] += f"_bridge_d_{d:.0e}"
        short_task["purpose"] = "hf3_small_displacement_bridge"
        short_task["input"]["target_mm"] = d
        settings = {"tolerance": self.spec["internal_relative_force_tolerance"],
            "constraint_tolerance": self.spec["constraint_relative_tolerance"],
            "displacement_scale_floor": self.spec["displacement_scale_floor_mm"],
            "force_scale_floor_factor": self.spec["force_scale_floor_factor"],
            "max_checks": self.spec["max_checks"], "max_backtracks": self.spec["max_backtracks"],
            "max_bisections": self.spec["max_bisections"], "armijo_c": self.spec["armijo_c"],
            "minimum_increment": d/16, "time_limit_seconds": self.remaining()}
        solver = {"schema_version": "hf-project-solver-1.0", "solver_id": f"hf3_bridge_{family}_d_{d:.0e}",
                  "analysis": "tmc_average_displacement", "targets_mm": [d], "settings": settings}
        write_json(self.output/run["task_path"], short_task)
        write_json(self.output/run["solver_path"], solver)
        run.update(task_sha256=canonical_hash(short_task), solver_sha256=canonical_hash(solver),
                   parent_task_sha256=project.task_hash, initial_state="zero_u_and_zero_input_force", status="running")
        self.snapshot("running")
        result = evaluate_project(geometry_path, short_task, solver, self.output/run["path"])
        run.update(status=result["numerics"]["status"], accepted_step_count=result["path"]["accepted_step_count"],
                   original_targets_reached=result["path"]["original_targets_reached"],
                   result_sha256=file_hash(self.output/run["path"]/"result.json"))
        complete = (result["numerics"]["status"] == "success" and result["numerics"]["target_reached"]
                    and result["task_sha256"] == run["task_sha256"] and result["solver_sha256"] == run["solver_sha256"])
        self.check(f"{family}:d_{d:.0e}:production_target_and_config_identity", 0 if complete else 1, 0)
        if not complete:
            run["errors"] = None
            run["failure"] = result["numerics"]
            self.snapshot("running")
            return
        with np.load(self.output/run["path"]/"path.npz", allow_pickle=False) as arrays:
            originals = np.flatnonzero(arrays["is_original_target"])
            if len(originals) != 1 or arrays["d"][originals[0]] != d:
                raise ValueError("short path does not contain its exact sole original target")
            index = originals[0]
            gain = {"u": arrays["u"][index]/d, "q": float(arrays["q_out"][index]/d),
                    "R": float(arrays["R_input"][index]/d)}
        run["errors"] = responses(project, gain, reference, self.spec)
        run["q_out_per_d"], run["R_input_per_d_N_per_mm"] = gain["q"], gain["R"]
        save_arrays(self.output/run["path"]/"bridge_gain.npz", u_over_d=gain["u"],
                    q_over_d=np.array(gain["q"]), R_over_d=np.array(gain["R"]), d_mm=np.array(d),
                    reference_u_over_d=reference["u"], reference_q_over_d=np.array(reference["q"]), reference_R_over_d=np.array(reference["R"]))
        write_json(self.output/run["path"]/"bridge_comparison.json", run)
        self.snapshot("running")

    def trends(self, family):
        runs = [run for run in self.runs if run["case_family"] == family]
        if not all(run.get("errors") is not None for run in runs):
            return {"status": "not_evaluated", "reason": "one or more prescribed paths did not reach its target"}
        trend = {}
        for name in METRICS:
            first, last = (run["errors"][name]["relative_error"] for run in (runs[0], runs[-1]))
            self.check(f"{family}:{name}:smallest_amplitude", last, self.spec["bridge_relative_tolerance"])
            exempt = first <= self.spec["bridge_trend_exempt_first_error"]
            ratio = None if last == 0 else first/last
            passed = exempt or last == 0 or ratio >= self.spec["bridge_trend_ratio"]
            self.check(f"{family}:{name}:trend", 0 if passed else 1, 0)
            trend[name] = {"first_error": first, "last_error": last, "first_over_last": ratio,
                          "zero_final_error": last == 0, "rounding_plateau_exemption": exempt,
                          "required_ratio": self.spec["bridge_trend_ratio"], "status": "pass" if passed else "fail"}
        return trend

    def run(self):
        for family in FAMILIES:
            task = read_json(self.args.spec.parent/f"{family}_pilot_v1.json")
            geometry_path = self.args.dataset/f"canonical/{family}/geometry.json"
            project = build_project(geometry_path, task)
            self.cases[family] = {"qualification": project.qualification, "status": "running"}
            try:
                reference, report = self.references(family, project, geometry_path, self.output/family/"linear")
                self.cases[family]["linear_reference"] = report
                if report["status"] != "pass":
                    self.cases[family]["status"] = "blocked_by_linear_reference"
                    self.snapshot("running")
                    continue
                if family == "gripper":
                    self.cases[family]["background_diagnostic"] = self.diagnostic(project, task, geometry_path,
                        self.output/family/"background_diagnostic", reference)
                for run in [row for row in self.runs if row["case_family"] == family]:
                    self.short_path(family, task, geometry_path, project, reference, run)
                self.cases[family]["first_layer_trend"] = self.trends(family)
                self.cases[family]["status"] = "completed_prescribed_work"
            except (ValueError, OSError, RuntimeError, ArithmeticError, KeyError) as error:
                self.errors.append({"case_family": family, "type": type(error).__name__, "message": str(error)})
                self.cases[family]["status"] = "failed_or_incomplete"
                self.snapshot("running")
                if isinstance(error, TimeoutError):
                    break
            self.snapshot("running")
        if any(file_hash(Path(record["path"])) != record["sha256"] for record in self.inputs):
            raise ValueError("An original geometry/task/spec/script changed during the bridge")
        if implementation_hash() != self.runtime_hash:
            raise ValueError("Production implementation changed during the bridge")
        self.write_comparison_artifacts()
        complete = all(run["status"] == "success" for run in self.runs)
        passed = complete and not self.errors and all(row["status"] == "pass" for row in self.checks)
        self.snapshot("pass" if passed else "not_pass")
        return 0 if passed else 1

    def write_comparison_artifacts(self):
        rows = []
        for run in self.runs:
            for metric in METRICS:
                error = (run.get("errors") or {}).get(metric)
                rows.append({"case_family": run["case_family"], "d_mm": run["d_mm"], "status": run["status"],
                    "metric": metric, "absolute_error": None if error is None else error["absolute_error"],
                    "scale": None if error is None else error["scale"], "relative_error": None if error is None else error["relative_error"]})
        with (self.output/"small_displacement_bridge.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
        for axis, metric in zip(axes, METRICS):
            for family in FAMILIES:
                selected = [row for row in rows if row["case_family"] == family and row["metric"] == metric and row["relative_error"] is not None]
                axis.plot([row["d_mm"] for row in selected], [row["relative_error"] for row in selected], "o-", label=family)
            axis.set_xscale("log")
            axis.set_yscale("symlog", linthresh=1e-14)
            axis.axhline(self.spec["bridge_relative_tolerance"], linestyle="--", color="0.5", label="smallest-d limit")
            axis.set(title=metric.replace("_", " "), xlabel="Mean input d [mm]", ylabel="Relative error to own K0")
            axis.grid(True, alpha=.25)
        axes[0].legend(fontsize=8)
        fig.suptitle("HF-3 first-layer bridge; all prescribed amplitudes, no HP claim")
        fig.savefig(self.output/"small_displacement_bridge.png", dpi=170)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--spec", type=Path, default=REPO/"configs/hf3/validation_spec.json")
    parser.add_argument("--dataset", type=Path, default=REPO.parent/"geometry_dataset")
    args = parser.parse_args()
    args.spec, args.dataset = args.spec.resolve(), args.dataset.resolve()
    jax.config.update("jax_enable_x64", True)
    jax.config.update("jax_platforms", "cpu")
    bridge = Bridge(args)
    try:
        return bridge.run()
    except (ValueError, OSError, RuntimeError, ArithmeticError, KeyError) as error:
        bridge.errors.append({"type": type(error).__name__, "message": str(error)})
        bridge.snapshot("incomplete")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
