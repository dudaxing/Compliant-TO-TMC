"""One native forward evaluation, cached persistence and a compact response."""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

from .displacement import DisplacementSettings
from .native_mean import solve_native_mean, write_native_mean
from .native_response import summarize_saved_native_result, write_native_response


def resolve_native_path(path, repo_root=None):
    """Explicit relative paths belong to repo_root, or the caller's cwd."""
    path = Path(path)
    return (path if path.is_absolute() else Path(repo_root or Path.cwd()) / path).resolve()


def evaluate_native(geometry_path, task_path, output_directory, *, repo_root=None,
                    targets=None, settings=None, time_limit_seconds=180.,
                    minimum_increment=None, response_mode="complete", tangent_mode="full",
                    initial_guess="tangent") -> dict:
    """Call the existing solver once and save its accepted cache once.

    Controller failures preserve accepted states. Input/solve/persistence/summary
    exceptions retain their original class, code and reason in a failed response.
    Existing output directories are never used for a new evaluation.
    The controller's time limit covers its solve, not CLI imports or persistence.
    """
    started = perf_counter()
    geometry = resolve_native_path(geometry_path, repo_root)
    task_file = resolve_native_path(task_path, repo_root)
    output = resolve_native_path(output_directory, repo_root)
    existed = output.exists()
    stage, descriptor = "input", None
    invocation = dict(geometry_file=str(geometry), task_file=str(task_file),
                      output_directory=str(output), response_mode=response_mode,
                      tangent_mode=tangent_mode, initial_guess=initial_guess)
    try:
        if existed:
            raise FileExistsError(f"Choose a new output directory: {output}")
        task_bytes = task_file.read_bytes()
        task = json.loads(task_bytes)
        invocation["task_file_sha256"] = sha256(task_bytes).hexdigest()
        requested = list(targets) if targets is not None else task.get("path", {}).get(
            "targets_mm", [0., task["input"]["target_mm"]])
        if len(requested) < 2:
            raise ValueError("At least origin and one displacement target are required")
        if settings is None:
            increment = requested[1] / 16 if minimum_increment is None else minimum_increment
            settings = DisplacementSettings(minimum_increment=increment,
                                            time_limit_seconds=time_limit_seconds)
        elif minimum_increment is not None or time_limit_seconds != 180.:
            raise ValueError("Pass settings or individual controller limits, not both")
        invocation.update(targets_mm=requested, settings=asdict(settings),
                          time_scope="Controller time limit; through-summary elapsed is separately reported")
        stage = "solve"
        result = solve_native_mean(geometry, task, requested, settings=settings,
                                   response_mode=response_mode, tangent_mode=tangent_mode,
                                   initial_guess=initial_guess)
        stage = "persistence"
        descriptor = write_native_mean(result, output)
        stage = "summary"
        response = summarize_saved_native_result(descriptor, repo_root=repo_root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        response = dict(schema_version="hf-native-response-1.0", status="error",
                        target_response=None, last_accepted=None,
                        failure=dict(stage=stage, code=getattr(error, "code", None),
                                     exception_class=type(error).__name__, reason=str(error)),
                        result_file=str(descriptor) if descriptor is not None else None,
                        independent_reference=None,
                        qualification_scope="Failure report only; no new mechanical qualification")
    response["invocation"] = invocation
    response["evaluation_elapsed_seconds"] = perf_counter() - started
    response["evaluation_elapsed_scope"] = "Through summary; excludes response write and CLI startup/stdout"
    if not existed:
        output.mkdir(parents=True, exist_ok=True)
        write_native_response(response, output / "response.json")
    return response
