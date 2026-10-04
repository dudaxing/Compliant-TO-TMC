"""Versioned project evaluation with atomic accepted-state checkpoints.

This is a production-path wrapper, not an independent high-precision validator.
It keeps readability, research qualification, numerical completion and undefined
functionality separate. No LF/MATLAB preparation code is imported.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, fields
from datetime import datetime, timezone
from hashlib import sha256
from importlib import metadata as package_metadata
import json
import os
from pathlib import Path
import platform
from time import perf_counter
from uuid import uuid4

import numpy as np

from . import __version__
from .data import canonical_hash, load_geometry
from .displacement import DisplacementSettings, solve_displacement_path
from .evaluation import implementation_hash
from .project import UNITS, build_project
from .regions import qualify_geometry
from .tmc_kernel import KERNEL_VERSION


SOLVER_SCHEMA = "hf-project-solver-1.0"
STATE_ARRAYS = ("u", "J", "input_force", "spring_force_on_structure", "force_residual",
                "support_reaction", "internal_force", "material_internal_force",
                "regularization_internal_force", "material_energy", "global_force_balance")


def _jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _config(value):
    if isinstance(value, dict):
        result = deepcopy(value)
    else:
        result = json.loads(Path(value).read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError("task and solver configurations must be JSON objects")
    canonical_hash(result)
    return result


def _solver_config(config, task):
    required = {"schema_version", "solver_id", "analysis", "targets_mm", "settings"}
    optional = {"description", "purpose", "parameter_origin"}
    if not required <= config.keys() or config.keys()-required-optional:
        raise ValueError("project solver has missing or unsupported fields")
    if config["schema_version"] != SOLVER_SCHEMA or config["analysis"] != "tmc_average_displacement":
        raise ValueError("expected hf-project-solver-1.0 / tmc_average_displacement")
    if not isinstance(config["solver_id"], str) or not config["solver_id"].strip():
        raise ValueError("solver_id must be a nonempty string")
    values = config["targets_mm"]
    if not isinstance(values, list) or not values or any(type(v) not in (int, float) for v in values):
        raise ValueError("targets_mm must be a nonempty JSON number list")
    targets = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(targets)) or np.any(targets < 0) or np.any(np.diff(targets) <= 0):
        raise ValueError("targets_mm must be finite, nonnegative and strictly increasing")
    if targets[-1] != task["input"]["target_mm"]:
        raise ValueError("last solver target must equal the declared task input target exactly")
    settings = config["settings"]
    allowed = {field.name for field in fields(DisplacementSettings)}
    if not isinstance(settings, dict) or settings.keys()-allowed:
        raise ValueError("settings contains unsupported DisplacementSettings fields")
    return targets.copy(), DisplacementSettings(**settings)


def _atomic_json(path, value):
    path = Path(path)
    data = json.dumps(_jsonable(value), ensure_ascii=False, indent=2, allow_nan=False)+"\n"
    temporary = path.with_name(path.name+".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_npz(path, arrays):
    path = Path(path)
    for key, value in arrays.items():
        a = np.asarray(value)
        if a.dtype.kind not in "biuf" or not np.all(np.isfinite(a)):
            raise ValueError(f"NPZ field {key} must be finite ordinary real data")
    temporary = path.with_name(path.name+".tmp")
    try:
        with temporary.open("wb") as stream:
            np.savez_compressed(stream, **arrays)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _state_arrays(record, model):
    arrays = {}
    for key in STATE_ARRAYS:
        expected = ((model.ne, 9) if key == "J" else (model.ne,) if key == "material_energy"
                    else (2,) if key == "global_force_balance" else (model.ndof,))
        value = np.asarray(record[key])
        if value.shape != expected or value.dtype.kind not in "iuf" or not np.all(np.isfinite(value)):
            raise ValueError(f"accepted state {key} has invalid shape/type or nonfinite values")
        arrays[key] = value.copy()
    if np.any(arrays["J"] <= 0):
        raise ValueError("accepted state contains nonpositive J")
    return arrays


def _brief(record):
    result = {key: _jsonable(value) for key, value in record.items() if key not in STATE_ARRAYS}
    json.dumps(result, allow_nan=False)
    return result


def _model_arrays(project, targets):
    model = project.model
    return dict(coordinates=model.coordinates, connectivity=model.connectivity,
        solid=model.solid, gamma=project.gamma, fixed_dofs=model.fixed_dofs, free_dofs=model.free,
        solid_nodes=project.solid_nodes, solid_dofs=project.solid_dofs,
        bin=project.bin, bout=project.bout, k_out=np.array(project.k_out), targets_mm=targets,
        lam=model.lam, mu=model.mu, kr=np.array(model.kr), hx=np.array(model.hx),
        hy=np.array(model.hy), thickness=np.array(model.thickness), **model.ops)


def _path_arrays(records, model):
    arrays = {}
    for name in STATE_ARRAYS:
        shape = ((model.ne, 9) if name == "J" else (model.ne,) if name == "material_energy"
                 else (2,) if name == "global_force_balance" else (model.ndof,))
        arrays[name] = np.stack([r[name] for r in records]) if records else np.empty((0,)+shape)
    # Every scalar remains in accepted_steps JSON. Numeric scalar columns are
    # also stored in NPZ; nullable region minima are never encoded as fake zero.
    omitted = []
    scalar_names = list(_brief(records[0])) if records else [
        "d", "R_input", "q_in", "q_out", "relative_residual", "residual_scale", "minimum_J",
        "original_target_displacement", "is_original_target", "bisection_depth", "elapsed_seconds"]
    for name in scalar_names:
        values = [r[name] for r in records]
        if all(isinstance(value, (bool, int, float, np.number)) for value in values):
            arrays[name] = np.asarray(values, dtype=bool if name == "is_original_target" else None)
        else:
            omitted.append(name)
    # Keep one canonical u key, shared with each single-state NPZ.
    return arrays, omitted


def evaluate_project(geometry_file, task_config, solver_config, output_directory=None):
    """Return a JSON-compatible summary of one fresh project evaluation.

    With output_directory, write metadata.json, model.npz, path.npz, result.json
    and atomic per-step NPZ/JSON pairs. The step JSON is the commit marker; its
    arrays_file is relative to the evaluation directory. index.json advertises
    only committed pairs. Existing directories, even empty ones, are rejected.

    Without output_directory, ``result['path']['arrays']`` carries the same
    complete ordinary-data columns as path.npz, converted to JSON lists. Model
    and solver objects are never returned. Failed targets have null metrics;
    previously accepted states and rejection diagnostics remain available.
    If final persistence fails, return a failed summary even when that summary
    cannot be written. Failed path.npz writes retain the arrays in that returned
    summary; committed step files remain separately identified.
    """
    started = perf_counter()
    output = None if output_directory is None else Path(output_directory)
    if output is not None:
        output.mkdir(parents=True, exist_ok=False)
    result = dict(schema_version="hf-project-result-1.0", evaluation_id=str(uuid4()),
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        scope="HF-3 modeled-half average-displacement production path; independent precision validation is separate",
        geometry_id=None, geometry_descriptor_sha256=None, geometry_file_sha256=None,
        task_id=None, task_sha256=None, solver_id=None, solver_sha256=None,
        implementation={"package_version": __version__, "source_sha256": implementation_hash(),
            "kernel_version": KERNEL_VERSION, "python": platform.python_version(), "platform": platform.platform(),
            "dependencies": {name: package_metadata.version(name) for name in ("numpy", "scipy", "jax", "jaxlib", "matplotlib")}},
        readability={"status": "not_evaluated"}, qualification={"status": "not_evaluated"},
        numerics={"status": "not_run", "target_reached": False, "failure_stage": None, "reason": None},
        functionality={"status": "not_evaluated", "reason": "No research functionality thresholds frozen for this pilot"},
        independent_precision={"status": "not_evaluated", "reason": "Production completion does not replace independent high-precision acceptance"},
        units=deepcopy(UNITS), metrics_at_target=None, target_metrics=None, last_accepted_state=None,
        path={"kind": "average_displacement", "model_file": None, "arrays_file": None,
              "state_index_file": None, "accepted_step_count": 0, "original_targets_reached": 0,
              "accepted_steps": []},
        signs={"R_input": "actuator generalized force ON modeled structure",
               "spring_force": "-k_out*b_out*(b_out.T*u) ON modeled structure",
               "force_energy_extent": "modeled lower half; no implicit factor of two",
               "reference_directions": "fixed normalized reference-arclength port weights"})
    stage = "geometry_read"
    project = None
    records, state_files = [], []
    solver_result = None
    metadata = None

    def persistence_failure(artifact, error):
        # Finalization must not replace an already available numerical failure
        # or accepted-state history with an uncaught I/O exception.
        if "persistence" not in result:
            result["persistence"] = {"status": "failed", "errors": [],
                "numerics_before_failure": deepcopy(result["numerics"])}
        detail = {"artifact": artifact, "reason": str(error), "error_type": type(error).__name__}
        result["persistence"]["errors"].append(detail)
        result["numerics"].update(status="failed", target_reached=False,
            failure_stage="result_persistence", reason=str(error), error_type=type(error).__name__,
            error_code="persistence_failure", reached_input_mm=float(records[-1]["d"]) if records else None,
            failure={"code": "persistence_failure", "reason": str(error), "details": {"artifact": artifact}})
        result["metrics_at_target"] = result["target_metrics"] = None

    try:
        geometry = load_geometry(geometry_file)
        result.update(geometry_id=geometry.geometry_id,
            geometry_descriptor_sha256=geometry.metadata["descriptor_sha256"],
            geometry_file_sha256=sha256(Path(geometry_file).read_bytes()).hexdigest(),
            model_extent=deepcopy(geometry.metadata["model_extent"]))
        result["readability"] = {"status": "pass"}
        stage = "task_or_solver_config"
        task, solver = _config(task_config), _config(solver_config)
        result.update(task_id=task.get("task_id"), task_sha256=canonical_hash(task),
            solver_id=solver.get("solver_id"), solver_sha256=canonical_hash(solver),
            task_config=task, solver_config=solver)
        if task.get("diagnostic_variant", "none") != "none":
            raise ValueError("diagnostic_variant is restricted to initial-tangent diagnosis; nonlinear project paths are forbidden")
        targets, settings = _solver_config(solver, task)
        result["path"]["targets_mm"] = targets.tolist()
        result["effective_settings"] = asdict(settings)
        stage = "geometry_qualification"
        result["qualification"] = qualify_geometry(geometry, task.get("qualification_criteria"))
        if result["qualification"]["status"] == "fail":
            raise ValueError("geometry failed declared qualification checks; no nonlinear path performed")
        stage = "project_mapping"
        project = build_project(geometry_file, task)
        if (project.geometry.geometry_id != geometry.geometry_id or
                project.geometry.metadata["descriptor_sha256"] != result["geometry_descriptor_sha256"] or
                project.task_sha256 != result["task_sha256"]):
            raise ValueError("project mapping changed geometry or task identity")
        result["qualification"] = deepcopy(project.qualification)
        if project.qualification["status"] == "fail":
            raise ValueError("mapped project failed declared qualification checks")
        result["material"] = deepcopy(project.material)
        result["regions"] = deepcopy(project.region_metadata)
        force_scale_per_length = float(project.material["E_MPa"]*project.model.thickness)
        result["force_scale_per_length_N_per_mm"] = force_scale_per_length
        metadata = deepcopy(result)
        if output is not None:
            (output/"steps").mkdir()
            _atomic_npz(output/"model.npz", _model_arrays(project, targets))
            result["path"].update(model_file="model.npz", state_index_file="steps/index.json")
            metadata["path"] = deepcopy(result["path"])
            _atomic_json(output/"metadata.json", metadata)
            _atomic_json(output/"steps/index.json", {"accepted_step_count": 0, "steps": []})

        def on_accept(received):
            record = deepcopy(received)
            arrays = _state_arrays(record, project.model)
            brief = _brief(record)
            if (type(brief["is_original_target"]) is not bool or
                    brief["is_original_target"] != (brief["d"] == brief["original_target_displacement"]) or
                    brief["original_target_displacement"] not in targets or
                    brief["d"] > brief["original_target_displacement"] or brief["d"] < 0 or
                    (records and brief["d"] <= records[-1]["d"])):
                raise ValueError("accepted state has inconsistent original-target/substep identity")
            record.update(arrays)
            records.append(record)
            if output is not None:
                index = len(records)
                name = f"step_{index:04d}"
                array_file, scalar_file = "steps/"+name+".npz", "steps/"+name+".json"
                _atomic_npz(output/array_file, {**arrays, "d": np.array(record["d"]),
                    "R_input": np.array(record["R_input"]), "is_original_target": np.array(record["is_original_target"])})
                scalar = {**brief, "arrays_file": array_file,
                          "arrays_sha256": sha256((output/array_file).read_bytes()).hexdigest()}
                _atomic_json(output/scalar_file, scalar)  # Commit after the complete NPZ.
                state_files.append({"state_index": index-1, "d_mm": record["d"],
                    "metadata_file": scalar_file, "arrays_file": array_file, "arrays_sha256": scalar["arrays_sha256"]})
                _atomic_json(output/"steps/index.json", {"accepted_step_count": len(state_files), "steps": state_files})

        stage = "displacement_path"
        solver_result = solve_displacement_path(project.model, project.bin, project.bout, targets,
            k_out=project.k_out, settings=settings, on_accept=on_accept,
            force_scale_per_length=force_scale_per_length)
        if len(solver_result["accepted_steps"]) != len(records):
            raise ValueError("solver accepted-state count differs from callback history")
        for returned, recorded in zip(solver_result["accepted_steps"], records):
            if _brief(returned) != _brief(recorded) or any(not np.array_equal(returned[key], recorded[key]) for key in STATE_ARRAYS):
                raise ValueError("solver result differs from immutable accepted callback history")
        succeeded = solver_result["status"] == "success" and solver_result["target_reached"] is True
        original_levels = np.array([r["d"] for r in records if r["is_original_target"]])
        if succeeded and (not np.array_equal(original_levels, targets) or not records or records[-1]["d"] != targets[-1]):
            raise ValueError("solver completion flag does not cover all exact original targets")
        result["numerics"] = dict(status="success" if succeeded else "failed", target_reached=succeeded,
            target_input_mm=float(targets[-1]), reached_input_mm=float(records[-1]["d"]) if records else 0.0,
            failure_stage=None if succeeded else "displacement_path",
            reason=None if succeeded else (solver_result.get("failure") or {}).get("reason", "path incomplete"),
            failure=deepcopy(solver_result.get("failure")))
        if succeeded:
            result["metrics_at_target"] = result["target_metrics"] = _brief(records[-1])
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, ArithmeticError) as error:
        if stage == "geometry_read":
            result["readability"] = {"status": "fail", "reason": str(error)}
        result["numerics"] = dict(status="failed", target_reached=False, failure_stage=stage,
            reason=str(error), error_type=type(error).__name__, error_code=getattr(error, "code", None),
            details=_jsonable(getattr(error, "details", {})),
            reached_input_mm=float(records[-1]["d"]) if records else None)
        result["metrics_at_target"] = result["target_metrics"] = None
    if project is not None:
        arrays, omitted = _path_arrays(records, project.model)
        result["path"].update(accepted_step_count=len(records),
            original_targets_reached=sum(bool(r["is_original_target"]) for r in records),
            accepted_steps=[_brief(r) for r in records], nullable_or_nonnumeric_columns_in_json_only=omitted,
            step_files=state_files)
        result["last_accepted_state"] = _brief(records[-1]) if records else None
        if output is None:
            result["path"]["arrays"] = _jsonable(arrays)
        else:
            try:
                _atomic_npz(output/"path.npz", arrays)
                result["path"]["arrays_file"] = "path.npz"
            except OSError as error:
                persistence_failure("path.npz", error)
                # A callback may have accepted a state immediately before its
                # step write failed. Do not lose its U/J/forces if this final
                # archive also fails, and do not advertise an uncommitted file.
                result["path"]["arrays_file"] = None
                result["path"]["arrays"] = _jsonable(arrays)
    if solver_result is not None:
        excluded = {"u", "accepted_steps", "last_accepted_state", "target_metrics", "b_in", "b_out"}
        result["solver_trace"] = _jsonable({key: value for key, value in solver_result.items() if key not in excluded})
    result["wall_seconds"] = perf_counter()-started
    result = _jsonable(result)
    json.dumps(result, allow_nan=False)
    if output is not None:
        if metadata is None:
            try:
                _atomic_json(output/"metadata.json", {key: value for key, value in result.items() if key not in {"solver_trace", "path"}})
            except OSError as error:
                persistence_failure("metadata.json", error)
        try:
            _atomic_json(output/"result.json", result)
        except OSError as error:
            persistence_failure("result.json", error)
    return result
