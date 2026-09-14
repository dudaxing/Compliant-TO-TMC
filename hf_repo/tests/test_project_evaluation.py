"""Project wrapper contract and persistence tests, with a mocked path solver.

Fixtures use a real Geometry, TMCModel and Project on a single artificial cell.
No nonlinear equilibrium solve, production kernel evaluation, or LF data is used.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from hf_eval.data import canonical_hash, load_geometry, write_geometry
from hf_eval.project import Project, UNITS
from hf_eval.regions import qualify_geometry
from hf_eval.tmc import TMCModel
import hf_eval.project_evaluation as entry


def sample(tmp_path, monkeypatch):
    metadata = dict(schema_version="hf-geometry-1.0", case_family="synthetic_validation",
        grid={"shape_yx": [1, 1], "origin_mm": [0, 0], "cell_size_mm": [1, 1],
              "extent_mm": [1, 1], "axes": [[1, 0], [0, 1]], "array_order": "C_yx_bottom_up", "value_location": "cell"},
        thickness_mm=2, model_extent={"kind": "full"},
        region_tags={"support": {"points_mm": [[0, 0], [0, 1]], "components": [0, 1]},
            "input": {"points_mm": [[1, 0], [1, 1]], "direction": [1, 0], "averaging": "normalized_reference_arclength_trapezoid"},
            "output": {"points_mm": [[1, 0], [1, 1]], "direction": [0, 1], "averaging": "normalized_reference_arclength_trapezoid"}})
    arrays = dict(solid=np.ones((1, 1), dtype=np.uint8), design=np.ones((1, 1), dtype=np.uint8),
                  passive_solid=np.zeros((1, 1), dtype=np.uint8), passive_void=np.zeros((1, 1), dtype=np.uint8))
    path = write_geometry(tmp_path/"geometry", metadata, arrays)
    geometry = load_geometry(path)
    coordinates = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=float)
    model = TMCModel(coordinates, np.array([[0, 1, 3, 2]]), np.array([1.25]), np.array([.75]),
                     .01, 1, 1, 2, np.array([True]), np.array([0, 1, 4, 5]))
    bin, bout = np.zeros(8), np.zeros(8)
    bin[[2, 6]], bout[[3, 7]] = .5, .5
    task = dict(schema_version="hf-project-task-1.0", task_id="artificial_mapping_mock",
                case_family="synthetic_validation", diagnostic_variant="none", units=deepcopy(UNITS),
                input={"target_mm": .02}, material={"E_MPa": 3.0},
                qualification_criteria={"max_design_volume_fraction": None, "min_feature_mm": None})
    solver = dict(schema_version="hf-project-solver-1.0", solver_id="wrapper_contract_mock",
                  analysis="tmc_average_displacement", targets_mm=[.01, .02], settings={"time_limit_seconds": 15})
    project = Project(geometry, model, bin, bout, deepcopy(task), canonical_hash(task),
        {"fixed_dofs": model.fixed_dofs.tolist(), "diagnostic_variant": "none"},
        qualify_geometry(geometry, task["qualification_criteria"]), np.ones(1), np.arange(4),
        np.arange(8), {"E_MPa": 3.0, "thickness_mm": 2.0}, 0.0)
    def mapped(received_path, received_task):
        assert Path(received_path) == path
        return replace(project, task=deepcopy(received_task), task_hash=canonical_hash(received_task))
    monkeypatch.setattr(entry, "build_project", mapped)
    return path, task, solver, project


def record(project, d, *, original=None, depth=0):
    """Manufactured finite callback data; it is not an FE reference solution."""
    original = d if original is None else original
    u = np.zeros(8)
    u[[2, 6]], u[[3, 7]] = d, -.25*d
    R = 2*d
    actuator = project.bin*R
    support = np.zeros(8)
    support[[0, 4]] = -d
    internal = actuator+support
    return dict(d=d, R_input=R, q_in=d, q_out=-.25*d,
        constraint_residual=0.0, displacement_scale=d, constraint_bound=1e-10*d,
        relative_residual=0.0, free_force_residual_norm=0.0, residual_scale=R,
        force_scale_floor=1e-8*6*d, internal_free_norm=float(np.linalg.norm(actuator)),
        input_free_norm=float(np.linalg.norm(actuator)), spring_free_norm=0.0,
        input_force=actuator, spring_force_on_structure=np.zeros(8), force_residual=support.copy(),
        support_reaction=support, internal_force=internal, material_internal_force=internal.copy(),
        regularization_internal_force=np.zeros(8), J=np.ones((1, 9)), minimum_J=1.0,
        solid_minimum_J=1.0, medium_minimum_J=None, material_energy=np.array([d*d]),
        solid_material_energy=d*d, medium_material_energy=0.0, output_spring_energy=0.0,
        output_spring_generalized_force=0.0, global_force_balance=np.zeros(2),
        global_force_balance_scale=2*R, relative_global_force_balance=0.0,
        fixed_displacement_max=0.0, newton_checks=1, u=u,
        original_target_displacement=original, is_original_target=d == original,
        bisection_depth=depth, elapsed_seconds=d)


def install_solver(monkeypatch, project, *, accepted=None, failed=False, raises=False, inspect_callback=None):
    calls = []
    states = accepted if accepted is not None else [record(project, .01), record(project, .02)]
    def solve(model, bin, bout, targets, k_out=0.0, settings=None, on_accept=None, *, force_scale_per_length):
        calls.append(dict(model=model, bin=bin.copy(), bout=bout.copy(), targets=np.array(targets),
                          k_out=k_out, settings=settings, force_scale_per_length=force_scale_per_length))
        for item in states:
            on_accept(deepcopy(item))
            if inspect_callback:
                inspect_callback(len(calls), item)
        if raises:
            raise RuntimeError("mock failure after accepted checkpoint")
        last = deepcopy(states[-1]) if states else None
        return dict(status="failed" if failed else "success", target_reached=not failed,
            target_displacement=float(targets[-1]), reached_displacement=states[-1]["d"] if states else 0.,
            u=states[-1]["u"].copy() if states else np.zeros(8), R_input=states[-1]["R_input"] if states else 0.,
            target_metrics=None if failed else last, last_accepted_state=last,
            failure={"code": "time_limit", "reason": "mock deadline", "details": {}} if failed else None,
            accepted_steps=deepcopy(states), trials=[{"accepted": False, "reason": "mock rejected trial"}],
            failed_attempts=[{"code": "mock_trial", "rollback_bitwise_equal": True}],
            newton_history=[], linear_solve_diagnostics=[], maximum_bisection_depth=1,
            timing_seconds={"total": .1}, b_in=bin.copy(), b_out=bout.copy(), k_out=k_out,
            reference_state="undeformed")
    monkeypatch.setattr(entry, "solve_displacement_path", solve)
    return calls


def test_json_api_preserves_qualification_and_explicit_project_force_scale(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    before = (path.read_bytes(), deepcopy(task), deepcopy(solver))
    calls = install_solver(monkeypatch, project)
    result = entry.evaluate_project(path, task, solver)
    json.dumps(result, allow_nan=False)
    assert result["numerics"]["status"] == "success"
    assert result["qualification"]["status"] == "pending"
    assert result["functionality"]["status"] == "not_evaluated"
    assert result["independent_precision"]["status"] == "not_evaluated"
    assert result["task_sha256"] == canonical_hash(task)
    assert result["solver_sha256"] == canonical_hash(solver)
    assert calls[0]["force_scale_per_length"] == 3*2
    assert calls[0]["settings"].tolerance == 1e-9
    assert result["path"]["accepted_step_count"] == 2
    assert np.asarray(result["path"]["arrays"]["u"]).shape == (2, 8)
    assert result["path"]["accepted_steps"][0]["medium_minimum_J"] is None
    assert "medium_minimum_J" not in result["path"]["arrays"]
    assert (path.read_bytes(), task, solver) == before


def test_atomic_step_pairs_exist_before_solver_returns_and_are_replayable(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    output = tmp_path/"output"
    def inspect_callback(_call_number, item):
        index = json.loads((output/"steps/index.json").read_text())
        descriptor = index["steps"][-1]
        scalar = json.loads((output/descriptor["metadata_file"]).read_text())
        assert scalar["d"] == item["d"]
        with np.load(output/descriptor["arrays_file"], allow_pickle=False) as archive:
            np.testing.assert_array_equal(archive["u"], item["u"])
        assert not list(output.rglob("*.tmp"))
    install_solver(monkeypatch, project, inspect_callback=inspect_callback)
    result = entry.evaluate_project(path, task, solver, output)
    assert json.loads((output/"result.json").read_text()) == result
    assert result["path"]["arrays_file"] == "path.npz"
    assert "arrays" not in result["path"]
    with np.load(output/"model.npz", allow_pickle=False) as model:
        np.testing.assert_array_equal(model["bin"], project.bin)
        np.testing.assert_array_equal(model["weights"], project.model.ops["weights"])
        assert model["thickness"] == 2
    with np.load(output/"path.npz", allow_pickle=False) as states:
        assert states["u"].shape == (2, 8)
        np.testing.assert_array_equal(states["d"], [.01, .02])
        assert all(states[name].dtype.kind in "biuf" for name in states.files)


def test_failed_target_keeps_substep_last_state_and_all_diagnostics(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    accepted = [record(project, .01), record(project, .015, original=.02, depth=1)]
    install_solver(monkeypatch, project, accepted=accepted, failed=True)
    result = entry.evaluate_project(path, task, solver, tmp_path/"failed")
    assert result["numerics"]["status"] == "failed"
    assert result["metrics_at_target"] is result["target_metrics"] is None
    assert result["last_accepted_state"]["d"] == .015
    assert result["path"]["accepted_step_count"] == 2
    assert result["path"]["original_targets_reached"] == 1
    assert result["solver_trace"]["trials"][0]["accepted"] is False
    with np.load(tmp_path/"failed/path.npz", allow_pickle=False) as states:
        np.testing.assert_array_equal(states["is_original_target"], [True, False])


def test_unexpected_exception_keeps_already_committed_state(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    install_solver(monkeypatch, project, accepted=[record(project, .01)], raises=True)
    result = entry.evaluate_project(path, task, solver, tmp_path/"exception")
    assert result["metrics_at_target"] is None
    assert result["last_accepted_state"]["d"] == .01
    assert result["numerics"]["error_type"] == "RuntimeError"
    assert (tmp_path/"exception/steps/step_0001.json").is_file()


def test_empty_failed_path_has_typed_empty_arrays_and_null_last_state(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    install_solver(monkeypatch, project, accepted=[], failed=True)
    result = entry.evaluate_project(path, task, solver, tmp_path/"empty")
    assert result["last_accepted_state"] is None
    assert result["metrics_at_target"] is None
    with np.load(tmp_path/"empty/path.npz", allow_pickle=False) as states:
        assert states["u"].shape == (0, 8)
        assert states["J"].shape == (0, 1, 9)


def test_configuration_json_paths_and_fresh_evaluation_ids(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    calls = install_solver(monkeypatch, project)
    for name, config in (("task", task), ("solver", solver)):
        (tmp_path/(name+".json")).write_text(json.dumps(config), encoding="utf-8")
    first = entry.evaluate_project(path, task, solver)
    second = entry.evaluate_project(path, tmp_path/"task.json", tmp_path/"solver.json")
    assert first["evaluation_id"] != second["evaluation_id"]
    assert first["task_sha256"] == second["task_sha256"]
    assert len(calls) == 2


@pytest.mark.parametrize("mutation", [
    lambda s: s.update(schema_version="hf-solver-1.0"),
    lambda s: s.update(analysis="solid_linear_q1"),
    lambda s: s.update(targets_mm=[.02, .01]),
    lambda s: s.update(targets_mm=[.01]),
    lambda s: s.update(targets_mm=[False, .02]),
    lambda s: s["settings"].update(unknown_setting=1),
    lambda s: s.update(force_scale_per_length=100),
])
def test_invalid_solver_never_calls_the_path_solver(tmp_path, monkeypatch, mutation):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    calls = install_solver(monkeypatch, project)
    mutation(solver)
    result = entry.evaluate_project(path, task, solver)
    assert result["readability"]["status"] == "pass"
    assert result["numerics"]["failure_stage"] == "task_or_solver_config"
    assert result["metrics_at_target"] is None and not calls


def test_background_diagnostic_cannot_be_used_as_a_nonlinear_path(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    calls = install_solver(monkeypatch, project)
    task["diagnostic_variant"] = "gripper_release_background_beyond_entity"
    result = entry.evaluate_project(path, task, solver, tmp_path/"forbidden")
    assert "initial-tangent" in result["numerics"]["reason"]
    assert not calls and result["metrics_at_target"] is None
    assert not (tmp_path/"forbidden/model.npz").exists()


def test_corrupt_geometry_has_distinct_readability_failure(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    calls = install_solver(monkeypatch, project)
    path.write_text("invalid JSON", encoding="utf-8")
    result = entry.evaluate_project(path, task, solver, tmp_path/"bad")
    assert result["readability"]["status"] == "fail"
    assert result["qualification"]["status"] == "not_evaluated"
    assert result["numerics"]["failure_stage"] == "geometry_read"
    assert not calls


def test_false_backend_success_does_not_certify_missing_targets(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    install_solver(monkeypatch, project, accepted=[record(project, .01)])
    result = entry.evaluate_project(path, task, solver)
    assert result["numerics"]["status"] == "failed"
    assert result["metrics_at_target"] is None
    assert result["last_accepted_state"]["d"] == .01


def test_invalid_accepted_array_is_not_persisted_as_a_checkpoint(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    bad = record(project, .01)
    bad["J"][0, 0] = -1
    install_solver(monkeypatch, project, accepted=[bad])
    result = entry.evaluate_project(path, task, solver, tmp_path/"invalid_state")
    assert result["numerics"]["status"] == "failed"
    assert result["path"]["accepted_step_count"] == 0
    assert not (tmp_path/"invalid_state/steps/step_0001.json").exists()


def test_existing_empty_or_populated_directory_is_never_reused(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    calls = install_solver(monkeypatch, project)
    output = tmp_path/"existing"
    output.mkdir()
    with pytest.raises(FileExistsError):
        entry.evaluate_project(path, task, solver, output)
    (output/"result.json").write_text("prior evidence")
    with pytest.raises(FileExistsError):
        entry.evaluate_project(path, task, solver, output)
    assert (output/"result.json").read_text() == "prior evidence" and not calls


def test_final_path_write_failure_returns_all_arrays_and_failed_summary(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    install_solver(monkeypatch, project)
    ordinary_npz = entry._atomic_npz

    def final_archive_unwritable(destination, arrays):
        if Path(destination).name == "path.npz":
            raise OSError("mock final archive write failure")
        return ordinary_npz(destination, arrays)

    monkeypatch.setattr(entry, "_atomic_npz", final_archive_unwritable)
    output = tmp_path/"final_archive_failure"
    result = entry.evaluate_project(path, task, solver, output)
    assert result["numerics"]["status"] == "failed"
    assert result["numerics"]["target_reached"] is False
    assert result["metrics_at_target"] is result["target_metrics"] is None
    assert result["last_accepted_state"]["d"] == .02
    assert result["path"]["arrays_file"] is None
    assert np.asarray(result["path"]["arrays"]["u"]).shape == (2, 8)
    assert len(result["path"]["step_files"]) == 2
    assert result["persistence"]["numerics_before_failure"]["status"] == "success"
    assert [error["artifact"] for error in result["persistence"]["errors"]] == ["path.npz"]
    assert json.loads((output/"result.json").read_text()) == result
    assert (output/"steps/step_0002.json").is_file()


def test_final_result_write_failure_returns_summary_without_claiming_saved_result(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    install_solver(monkeypatch, project)
    ordinary_json = entry._atomic_json

    def final_summary_unwritable(destination, value):
        if Path(destination).name == "result.json":
            raise OSError("mock result write failure")
        return ordinary_json(destination, value)

    monkeypatch.setattr(entry, "_atomic_json", final_summary_unwritable)
    output = tmp_path/"final_summary_failure"
    result = entry.evaluate_project(path, task, solver, output)
    json.dumps(result, allow_nan=False)
    assert result["numerics"]["error_code"] == "persistence_failure"
    assert result["metrics_at_target"] is result["target_metrics"] is None
    assert result["last_accepted_state"]["d"] == .02
    assert result["path"]["arrays_file"] == "path.npz" and (output/"path.npz").is_file()
    assert not (output/"result.json").exists()
    assert result["solver_trace"]["trials"][0]["reason"] == "mock rejected trial"
    assert result["persistence"]["errors"][-1]["artifact"] == "result.json"


def test_persistent_checkpoint_io_failure_retains_unsaved_state_and_solver_diagnostics(tmp_path, monkeypatch):
    path, task, solver, project = sample(tmp_path, monkeypatch)
    first = record(project, .01)

    def controller_with_real_callback_error(model, bin, bout, targets, **kwargs):
        # Match the production controller's contract: acceptance precedes the
        # callback and an OSError returns a failed path with that state retained.
        try:
            kwargs["on_accept"](deepcopy(first))
        except OSError as error:
            return dict(status="failed", target_reached=False, accepted_steps=[deepcopy(first)],
                target_metrics=None, last_accepted_state=deepcopy(first), u=first["u"].copy(),
                R_input=first["R_input"], reached_displacement=.01, target_displacement=.02,
                failure={"code": "persistence_failure", "reason": str(error), "details": {}},
                trials=[{"accepted": False, "reason": "earlier bounded trial"}],
                failed_attempts=[{"rollback_bitwise_equal": True, "code": "earlier trial"}])
        raise AssertionError("the injected checkpoint write must fail")

    monkeypatch.setattr(entry, "solve_displacement_path", controller_with_real_callback_error)
    ordinary_npz, ordinary_json = entry._atomic_npz, entry._atomic_json
    storage = {"failed": False}

    def npz_write(destination, arrays):
        if Path(destination).name.startswith("step_"):
            storage["failed"] = True
        if storage["failed"]:
            raise OSError("mock persistent storage failure")
        return ordinary_npz(destination, arrays)

    def json_write(destination, value):
        if storage["failed"]:
            raise OSError("mock persistent storage failure")
        return ordinary_json(destination, value)

    monkeypatch.setattr(entry, "_atomic_npz", npz_write)
    monkeypatch.setattr(entry, "_atomic_json", json_write)
    output = tmp_path/"persistent_io_failure"
    result = entry.evaluate_project(path, task, solver, output)
    json.dumps(result, allow_nan=False)
    assert result["numerics"]["status"] == "failed"
    assert result["metrics_at_target"] is result["target_metrics"] is None
    assert result["last_accepted_state"]["d"] == .01
    assert result["path"]["accepted_step_count"] == 1 and result["path"]["step_files"] == []
    np.testing.assert_array_equal(result["path"]["arrays"]["u"][0], first["u"])
    assert result["solver_trace"]["trials"][0]["reason"] == "earlier bounded trial"
    assert result["solver_trace"]["failed_attempts"][0]["rollback_bitwise_equal"]
    assert result["persistence"]["numerics_before_failure"]["failure"]["code"] == "persistence_failure"
    assert [item["artifact"] for item in result["persistence"]["errors"]] == ["path.npz", "result.json"]
    assert json.loads((output/"steps/index.json").read_text())["accepted_step_count"] == 0
    assert not (output/"steps/step_0001.json").exists()
    assert not (output/"result.json").exists()
