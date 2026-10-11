"""CLI argument transport only: all public evaluation/persistence calls are mocks."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from hf_eval import native_evaluate, native_mean, native_project, native_resume


@pytest.fixture(autouse=True)
def no_real_parent_or_mechanics(monkeypatch):
    original_open = Path.open

    def ordinary_files_only(path, *args, **kwargs):
        assert path.suffix.lower() != ".npz", "Mock CLI transport must not open saved arrays"
        return original_open(path, *args, **kwargs)

    def forbidden(*args, **kwargs):
        pytest.fail("Mock CLI transport called a real saved reader, model, solver or writer")

    monkeypatch.setattr(Path, "open", ordinary_files_only)
    monkeypatch.setattr(native_evaluate, "evaluate_native", forbidden)
    monkeypatch.setattr(native_resume, "saved_resume_defaults", forbidden)
    monkeypatch.setattr(native_project, "build_native_project", forbidden)
    for name in ("build_native_project", "solve_native_mean", "write_native_mean"):
        monkeypatch.setattr(native_mean, name, forbidden)


def load_cli(name, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "scripts" / (name + ".py")
    original_path = list(sys.path)
    spec = importlib.util.spec_from_file_location("integration_" + name + "_cli", script)
    cli = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(cli)
    finally:
        sys.path[:] = original_path
    if name == "solve_native_mean":
        # This verifies argument transport, not an accidental elapsed-time limit.
        monkeypatch.setattr(cli, "STARTED", 10.)
        monkeypatch.setattr(cli, "perf_counter", lambda: 11.)
    return cli, script


def fake_result(endpoint):
    return SimpleNamespace(
        metadata=dict(status="success", reached_displacement=endpoint,
                      call_counts={"mock_solver_invocations": 1}),
        accepted=[object(), object()], path={"target_reached": True})


def test_evaluate_cli_saved_flags_are_forwarded(tmp_path, monkeypatch, capsys):
    cli, script = load_cli("evaluate_native", monkeypatch)
    base = tmp_path / "explicit_repo"
    base.mkdir()
    elsewhere = tmp_path / "unrelated_cwd"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    calls = []
    expected = dict(schema_version="hf-native-response-1.0", status="success",
                    target_response=None, continuation={"parent_status": "failed"})

    def evaluate(geometry, task, output, **options):
        calls.append((geometry, task, output, options))
        return expected

    monkeypatch.setattr(cli, "evaluate_native", evaluate)
    monkeypatch.setattr(sys, "argv", [str(script), "--repo", str(base),
        "--saved-result", "parent/result.json", "--selected-state-index", "13",
        "--output", "new_child", "--targets", "1.2", "1.15", "--time-limit", "30"])
    assert cli.main() == 0
    assert len(calls) == 1
    geometry, task, output, options = calls[0]
    assert geometry is task is None and output == Path("new_child")
    assert options == dict(repo_root=base, targets=[1.2, 1.15],
        time_limit_seconds=30., minimum_increment=None, response_mode=None,
        tangent_mode=None, initial_guess=None, saved_result=Path("parent/result.json"),
        selected_state_index=13)
    assert json.loads(capsys.readouterr().out) == expected
    assert not (base / "new_child").exists() and not (elsewhere / "new_child").exists()


def test_mean_cli_zero_start_keeps_defaults(tmp_path, monkeypatch, capsys):
    cli, script = load_cli("solve_native_mean", monkeypatch)
    geometry = tmp_path / "geometry.json"
    geometry.write_text("{}", encoding="utf-8")
    task_file = tmp_path / "task.json"
    task = {"input": {"target_mm": .5}}
    task_file.write_text(json.dumps(task), encoding="utf-8")
    output = tmp_path / "new_result"
    result = fake_result(.5)
    calls = []

    def solve(actual_geometry, actual_task, targets, **options):
        calls.append(("solve", actual_geometry, actual_task, targets, options))
        return result

    def write(actual_result, directory):
        assert actual_result is result
        calls.append(("write", directory))
        return directory / "result.json"

    monkeypatch.setattr(cli, "solve_native_mean", solve)
    monkeypatch.setattr(cli, "write_native_mean", write)
    monkeypatch.setattr(sys, "argv", [str(script), "--geometry", str(geometry),
        "--task", str(task_file), "--output", str(output)])
    assert cli.main() == 0
    assert [call[0] for call in calls] == ["solve", "write"]
    _, actual_geometry, actual_task, targets, options = calls[0]
    assert actual_geometry == geometry and actual_task == task and targets == [0., .5]
    assert options["settings"] == cli.DisplacementSettings(
        minimum_increment=.03125, time_limit_seconds=180.)
    assert {key: value for key, value in options.items() if key != "settings"} == dict(
        response_mode=None, tangent_mode=None, initial_guess=None,
        saved_result=None, selected_state_index=None)
    assert calls[1][1] == output
    printed = json.loads(capsys.readouterr().out)
    assert printed["status"] == "success" and printed["accepted_states"] == 2
    assert printed["result_file"] == str(output / "result.json")
    assert printed["call_counts"] == result.metadata["call_counts"]
    assert printed["reached_displacement"] == .5 and printed["elapsed_seconds"] == 1.
    assert printed["equilibrium_qualified"] is False and not output.exists()


def test_mean_cli_saved_flags_inherit_suffix_and_settings(tmp_path, monkeypatch, capsys):
    cli, script = load_cli("solve_native_mean", monkeypatch)
    parent = tmp_path / "absent_parent" / "result.json"
    output = tmp_path / "new_child"
    task = {"input": {"target_mm": 1.2},
            "path": {"kind": "ordered_cycle", "targets_mm": [0., 1.2, 1.15]}}
    settings = cli.DisplacementSettings(minimum_increment=.00625, time_limit_seconds=45.)
    result = fake_result(1.15)
    calls = []

    def defaults(saved_file, selected_index, **options):
        calls.append(("defaults", saved_file, selected_index, options))
        return dict(task=task, targets=[1.2, 1.15], settings=settings)

    def solve(geometry, actual_task, targets, **options):
        calls.append(("solve", geometry, actual_task, targets, options))
        return result

    def write(actual_result, directory):
        assert actual_result is result
        calls.append(("write", directory))
        return directory / "result.json"

    monkeypatch.setattr(cli, "saved_resume_defaults", defaults)
    monkeypatch.setattr(cli, "solve_native_mean", solve)
    monkeypatch.setattr(cli, "write_native_mean", write)
    monkeypatch.setattr(sys, "argv", [str(script), "--saved-result", str(parent),
        "--selected-state-index", "13", "--output", str(output), "--time-limit", "45"])
    assert cli.main() == 0
    assert [call[0] for call in calls] == ["defaults", "solve", "write"]
    assert calls[0] == ("defaults", parent, 13, {"time_limit_seconds": 45.})
    _, geometry, actual_task, targets, options = calls[1]
    assert geometry is None and actual_task == task and targets == [1.2, 1.15]
    assert options == dict(settings=settings, response_mode=None, tangent_mode=None,
                          initial_guess=None, saved_result=parent, selected_state_index=13)
    assert calls[2][1] == output
    printed = json.loads(capsys.readouterr().out)
    assert printed["status"] == "success" and printed["accepted_states"] == 2
    assert printed["result_file"] == str(output / "result.json")
    assert printed["reached_displacement"] == 1.15 and printed["equilibrium_qualified"] is False
    assert not parent.exists() and not output.exists()
