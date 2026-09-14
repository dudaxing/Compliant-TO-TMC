"""Single-geometry entry point with explicit result validity and immutable inputs."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from importlib import metadata as package_metadata
import json
from pathlib import Path
import platform
import time
from uuid import uuid4

import numpy as np

from . import __version__
from .data import canonical_hash, load_geometry
from .regions import qualify_geometry
from .linear import analyze


def _config(value):
    if isinstance(value, dict):
        return deepcopy(value)
    with Path(value).open(encoding="utf-8") as stream:
        result = json.load(stream)
    if not isinstance(result, dict):
        raise ValueError("Task and solver configuration must be JSON objects")
    return result


def implementation_hash():
    digest = sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def inspect_geometry(path):
    """Read and qualify one geometry; schema failures remain distinct from geometry failures."""
    try:
        geometry = load_geometry(path)
        return {"readability": {"status": "pass"},
                "geometry_id": geometry.geometry_id,
                "case_family": geometry.metadata["case_family"],
                "qualification": qualify_geometry(geometry)}
    except (ValueError, OSError, KeyError, TypeError) as error:
        return {"readability": {"status": "fail", "reason": str(error)},
                "qualification": {"status": "not_evaluated"}}


def evaluate(geometry_file, task_config, solver_config, output_directory=None):
    """Return structured diagnostics, saving fresh result files when requested.

    Failure is represented by null target metrics and a stage/reason, never by
    a zero-valued performance result. A populated output directory is not reused.
    """
    # Dispatch before allocating output: the project wrapper owns atomic files.
    # Preserve the existing structured HF-1 error path for unreadable configs.
    try:
        declared_task = _config(task_config)
    except (ValueError, OSError, TypeError):
        declared_task = {}
    if declared_task.get("schema_version") == "hf-project-task-1.0":
        from .project_evaluation import evaluate_project
        return evaluate_project(geometry_file, declared_task, solver_config, output_directory)
    start = time.perf_counter()
    output = None
    if output_directory is not None:
        output = Path(output_directory)
        if output.exists() and any(output.iterdir()):
            raise FileExistsError(f"Refusing to overwrite evaluation directory: {output}")
        output.mkdir(parents=True, exist_ok=True)
    result = {
        "schema_version": "hf-result-1.0",
        "evaluation_id": str(uuid4()),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "HF-1 solid-only small-strain linear interface diagnostic; not nonlinear/contact fidelity",
        "geometry_id": None, "geometry_descriptor_sha256": None,
        "task_id": None, "task_sha256": None, "solver_id": None, "solver_sha256": None,
        "implementation": {"package_version": __version__, "source_sha256": implementation_hash(),
                           "python": platform.python_version(), "platform": platform.platform(),
                           "dependencies": {n: package_metadata.version(n) for n in ("numpy", "scipy", "matplotlib")}},
        "readability": {"status": "not_evaluated"},
        "qualification": {"status": "not_evaluated"},
        "numerics": {"status": "not_run", "target_reached": False, "reached_input_mm": None,
                     "failure_stage": None, "reason": None},
        "functionality": {"status": "not_assessed", "reason": "No research functionality criteria frozen in HF-1"},
        "metrics_at_target": None,
        "units": {"length": "mm", "force": "N", "stress": "MPa", "energy": "N mm"},
        "signs": {"R_in": "Actuator generalized force ON the structure, conjugate to positive input q",
                  "output_load": "Generalized spring force ON the structure = -k_out*q_out",
                  "displacement": "Reference-fixed port directions and normalized arclength weights",
                  "force_energy_extent": "All force and energy outputs refer to the modeled domain; no implicit doubling"},
        "path": {"kind": "linear_reference_to_target", "target_file": None,
                 "note": "No nonlinear increments or contact path were computed"},
    }
    arrays = None
    stage = "geometry_read"
    try:
        geometry = load_geometry(geometry_file)
        result["readability"] = {"status": "pass"}
        result["geometry_id"] = geometry.geometry_id
        result["geometry_descriptor_sha256"] = geometry.metadata["descriptor_sha256"]
        result["model_extent"] = deepcopy(geometry.metadata["model_extent"])
        stage = "task_or_solver_config"
        task, solver = _config(task_config), _config(solver_config)
        result.update(task_id=task.get("task_id"), task_sha256=canonical_hash(task),
                      solver_id=solver.get("solver_id"), solver_sha256=canonical_hash(solver),
                      task_config=task, solver_config=solver)
        stage = "geometry_qualification"
        result["qualification"] = qualify_geometry(geometry, task.get("qualification_criteria"))
        if result["qualification"]["status"] == "fail":
            raise ValueError("Geometry failed explicit qualification checks; no analysis performed")
        stage = "linear_analysis"
        metrics, arrays = analyze(geometry, task, solver)
        # Refuse non-finite numeric results even if a future backend forgets a guard.
        json.dumps(_jsonable(metrics), allow_nan=False)
        result["metrics_at_target"] = metrics
        result["numerics"] = {"status": "success", "target_reached": True,
                              "reached_input_mm": metrics["reached_input_mm"],
                              "failure_stage": None, "reason": None}
    except (ValueError, OSError, KeyError, TypeError, RuntimeError, ArithmeticError) as error:
        if stage == "geometry_read":
            result["readability"] = {"status": "fail", "reason": str(error)}
        result["numerics"] = {"status": "failed", "target_reached": False,
                              "reached_input_mm": None, "failure_stage": getattr(error, "stage", stage),
                              "reason": str(error), "error_type": type(error).__name__,
                              "error_code": getattr(error, "code", None), "details": getattr(error, "details", {})}
        result["metrics_at_target"] = None
        arrays = None
    if output is not None and arrays is not None:
        np.savez_compressed(output / "fields.npz", **arrays)
        result["path"]["target_file"] = "fields.npz"
        from .plotting import plot_result
        try:
            result["visualization"] = plot_result(geometry, result, arrays, output)
        except (ValueError, OSError, RuntimeError) as error:
            result["visualization"] = {"status": "failed", "reason": str(error)}
    result["wall_seconds"] = time.perf_counter() - start
    result = _jsonable(result)
    if output is not None:
        with (output / "result.json").open("w", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return result
