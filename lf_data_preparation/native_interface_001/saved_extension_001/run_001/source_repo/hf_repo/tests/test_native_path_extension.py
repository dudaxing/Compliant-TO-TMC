"""Finite append-only extension contracts; one real 16-cell/50-DOF integration.

This is not a gripper, contact, HP or physical stability qualification. Other
cases use ordinary metadata or CLI mocks; no large saved model is a fixture.
"""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from hf_eval import native_evaluate, native_mean, native_resume
from hf_eval.data import canonical_hash
from hf_eval.displacement import DisplacementSettings
from hf_eval.tmc import TMCError
from test_native_force import small_native, forbid_legacy_or_compiled_work
from test_native_mean_mechanical import PEAK, cycle_task


def test_completed_saved_child_extension_revalidates_original_split_and_preserves_sources(small_native, tmp_path, monkeypatch):
    source, original = small_native
    task = cycle_task(original)
    task["path"]["targets_mm"] = [0., PEAK, PEAK/2.]
    settings = DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=30.)

    def stop_after_peak(snapshot):
        if snapshot.record["d"] == PEAK:
            raise TMCError("Stops after the accepted peak", code="time_limit")

    parent = native_mean.solve_native_mean(source, task, task["path"]["targets_mm"], settings=settings,
        response_mode="mechanical", tangent_mode="chunk256", initial_guess="port_projection", on_accept=stop_after_peak)
    assert parent.metadata["status"] == "failed"
    parent_file = native_mean.write_native_mean(parent, tmp_path/"parent")
    child = native_mean.solve_native_mean(None, None, None, saved_result=parent_file, selected_state_index=1,
        settings=replace(settings, time_limit_seconds=35.))
    assert child.metadata["status"] == "success" and child.metadata["continuation"]["parent_status"] == "failed"
    child_file = native_mean.write_native_mean(child, tmp_path/"child")
    saved = json.loads(child_file.read_text(encoding="utf-8"))
    selected = len(saved["states"])-1
    assert selected == 1 and saved["states"][selected]["original_target_index"] == 2
    extended_task = deepcopy(task)
    extended_task["path"]["targets_mm"].append(PEAK/4.)
    task_file = tmp_path/"extended_task.json"
    task_file.write_text(json.dumps(extended_task), encoding="utf-8")
    before = {p:p.read_bytes() for root in [parent_file.parent, child_file.parent]
              for p in root.rglob("*") if p.is_file()}
    with pytest.raises(TMCError, match="original physical task"):
        native_mean.solve_native_mean(None, extended_task, [PEAK/2., PEAK/4.],
            saved_result=child_file, selected_state_index=selected, settings=replace(settings, time_limit_seconds=40.))
    force, tangent = native_mean._assemble_mechanical_force, native_mean._tangent_chunked
    seen, tangents, captured, state_reads = [], [], [], []

    def fresh_force(model, state):
        seen.append((state.lift.tobytes(), state.fluctuation.tobytes()))
        return force(model, state)

    def fresh_tangent(*args, **kwargs):
        tangents.append(True)
        return tangent(*args, **kwargs)

    solve, raw_read, load = native_mean.solve_native_mean, Path.read_bytes, np.load

    def capture(*args, **kwargs):
        result = solve(*args, **kwargs)
        captured.append(result)
        return result

    forbidden = {p for p in before if p.name in {"forces.npz", "tangents.npz", "total_matrix.npz"}}
    state_file = child_file.parent/saved["states"][selected]["state"]["path"]

    def guarded_read(path):
        assert path not in forbidden, "Extension must not read old force/tangent/matrix bytes"
        return raw_read(path)

    def guarded_load(file, *args, **kwargs):
        path = Path(file) if isinstance(file, (str, Path)) else None
        assert path not in forbidden, "Extension must not decode old force/tangent/matrix data"
        archive = load(file, *args, **kwargs)
        if path == state_file:
            assert set(archive.files) == {"lift", "fluctuation"}
            state_reads.append(path)
        return archive

    with monkeypatch.context() as checks:
        checks.setattr(native_mean, "_assemble_mechanical_force", fresh_force)
        checks.setattr(native_mean, "_tangent_chunked", fresh_tangent)
        checks.setattr(native_evaluate, "solve_native_mean", capture)
        checks.setattr(Path, "read_bytes", guarded_read)
        checks.setattr(np, "load", guarded_load)
        response = native_evaluate.evaluate_native(None, task_file, tmp_path/"extension",
            saved_result=child_file, selected_state_index=selected, time_limit_seconds=40., extend_path=True)
    result, = captured
    assert response["status"] == "success" and seen and tangents and state_reads == [state_file]
    anchor = child.accepted[selected]
    assert seen[0] == (anchor.state.lift.tobytes(), anchor.state.fluctuation.tobytes())
    assert result.accepted[0].state.lift.tobytes() == anchor.state.lift.tobytes()
    assert result.accepted[0].state.fluctuation.tobytes() == anchor.state.fluctuation.tobytes()
    assert np.float64(result.accepted[0].record["R_input"]).tobytes() == np.float64(anchor.record["R_input"]).tobytes()
    continuation = response["continuation"]
    assert continuation["continuation_mode"] == "explicit_task_extension"
    assert continuation["parent_status"] == "success" and continuation["parent_failure"] is None
    assert continuation["parent_continuation"] == child.metadata["continuation"]
    assert continuation["parent_continuation"]["parent_status"] == "failed"
    assert continuation["parent_continuation"]["parent_failure"]["code"] == "time_limit"
    assert continuation["source_task_sha256"] == canonical_hash(task)
    assert continuation["extended_task_sha256"] == canonical_hash(extended_task)
    assert continuation["source_task_targets_mm"] == task["path"]["targets_mm"]
    assert continuation["appended_targets_mm"] == [PEAK/4.]
    assert continuation["anchor_revalidated"] and continuation["anchor_identity_preserved"]
    assert not continuation["saved_matrix_or_force_or_tangent_read"]
    assert [(r.record["original_target_index"], r.record["child_original_target_index"]) for r in result.accepted] == [(2,0),(3,1)]
    assert result.project.task == extended_task and result.metadata["settings"] == saved["settings"] | {"time_limit_seconds":40.}
    assert not response["path"]["full_original_path_completed"] and not response["path"]["full_extended_path_completed"]
    assert response["target_response"] is None and response["maximum_loading_stroke"]["d_mm"] == PEAK/2.
    assert response["path"]["maximum_loading_stroke_scope"] == "Segment maximum; not the source task loading peak"
    assert all(value is False for value in response["producer_flags"].values())
    assert result.metadata["save_force_calls"] == result.metadata["save_tangent_calls"] == 0
    assert before == {p:p.read_bytes() for p in before}


def metadata_source():
    task = {"input":{"target_mm":PEAK}, "material":{"E_MPa":1.},
            "path":{"kind":"ordered_cycle", "targets_mm":[0., PEAK, PEAK/2.]}}
    states = [dict(original_target_index=i, d=d, physical_mean_target_mm=d,
                   original_target_displacement=d, is_original_target=True, state_sha256=str(i), R_input=0.)
              for i,d in enumerate(task["path"]["targets_mm"])]
    parent = dict(status="success", path_completed=True, target_reached=True,
                  task_sha256=canonical_hash(task), targets_mm=task["path"]["targets_mm"], states=states)
    model = dict(task=task, task_sha256=canonical_hash(task),
                 region_metadata={"effective_boundary":{"task_sha256":canonical_hash(task)}})
    extension = deepcopy(task)
    extension["path"]["targets_mm"].append(PEAK/4.)
    return parent, model, extension


@pytest.mark.parametrize("case", ["changed_physics", "nonprefix", "nonterminal", "child_mapping", "task_stamp"])
def test_extension_rejects_changed_contract_before_arrays(case):
    parent, model, task = metadata_source()
    selected = 2
    if case == "changed_physics":
        task["material"]["E_MPa"] = 2.
    elif case == "nonprefix":
        task["path"]["targets_mm"][1] = PEAK*2.
    elif case == "nonterminal":
        selected = 1
    elif case == "task_stamp":
        model["region_metadata"]["effective_boundary"]["task_sha256"] = "0"*64
    else:
        parent["states"] = parent["states"][1:]
        parent["targets_mm"] = parent["targets_mm"][1:]
        for i,row in enumerate(parent["states"]):
            row.update(child_original_target_index=i, continuation_anchor=(i == 0))
        parent["continuation"] = dict(original_task_targets_mm=model["task"]["path"]["targets_mm"],
            requested_suffix_targets_mm=parent["targets_mm"], original_target_indices=[1,2],
            selected_state=dict(original_target_index=1, state_sha256="1", R_input_N=0.),
            segment_completed=True, anchor_revalidated=True, anchor_identity_preserved=True)
        parent["states"][-1]["child_original_target_index"] = 0
        selected = 1
    with pytest.raises(TMCError) as error:
        native_resume._extension_targets(parent, selected, model, task)
    assert error.value.code == ("invalid_saved_state" if case in ("child_mapping", "task_stamp") else "invalid_task_extension")


@pytest.mark.parametrize("case", ["zero_start", "missing_task", "non_boolean"])
def test_extension_api_mode_errors_are_typed_before_parent_or_mechanics(case, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid mode called saved defaults or mechanics")

    monkeypatch.setattr(native_evaluate, "saved_resume_defaults", forbidden)
    monkeypatch.setattr(native_evaluate, "solve_native_mean", forbidden)
    task = tmp_path/"task.json"
    task.write_text("{}", encoding="utf-8")
    options = dict(saved_result=tmp_path/"absent_parent.json", selected_state_index=1, extend_path=True)
    if case == "zero_start":
        options.update(saved_result=None, selected_state_index=None)
    elif case == "missing_task":
        task = None
    else:
        options["extend_path"] = 1
    response = native_evaluate.evaluate_native(None, task, tmp_path/"error", **options)
    assert response["status"] == "error" and response["failure"]["stage"] == "input"
    assert response["failure"]["code"] == "invalid_input" and response["failure"]["exception_class"] == "TMCError"
    assert json.loads((tmp_path/"error/response.json").read_text(encoding="utf-8")) == response


@pytest.mark.parametrize("entry", ["evaluate_native", "solve_native_mean"])
def test_extension_cli_flag_is_explicitly_forwarded(entry, tmp_path, monkeypatch, capsys):
    script = Path(__file__).resolve().parents[1]/"scripts"/(entry+".py")
    spec = importlib.util.spec_from_file_location("extension_cli_"+entry, script)
    cli = importlib.util.module_from_spec(spec)
    original_path = list(sys.path)
    try:
        spec.loader.exec_module(cli)
    finally:
        sys.path[:] = original_path
    parent, task_file, output = tmp_path/"parent.json", tmp_path/"task.json", tmp_path/"new"
    task = {"input":{"target_mm":PEAK}, "path":{"kind":"ordered_cycle", "targets_mm":[0., PEAK, PEAK/2., PEAK/4.]}}
    task_file.write_text(json.dumps(task), encoding="utf-8")
    calls = []
    if entry == "evaluate_native":
        def evaluate(*args, **kwargs):
            calls.append(kwargs)
            return {"status":"success"}
        monkeypatch.setattr(cli, "evaluate_native", evaluate)
    else:
        settings = DisplacementSettings(time_limit_seconds=40.)
        def defaults(*args, **kwargs):
            assert kwargs["extend_path"] is True and kwargs["extension_task"] == task
            return dict(task=task, targets=[PEAK/2., PEAK/4.], settings=settings)
        def solve(*args, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(metadata=dict(status="success", reached_displacement=PEAK/4., call_counts={}),
                                   accepted=[object(),object()], path={"target_reached":True})
        monkeypatch.setattr(cli, "saved_resume_defaults", defaults)
        monkeypatch.setattr(cli, "solve_native_mean", solve)
        monkeypatch.setattr(cli, "write_native_mean", lambda *args: output/"result.json")
        monkeypatch.setattr(cli, "STARTED", 0.)
        monkeypatch.setattr(cli, "perf_counter", lambda: 1.)
    monkeypatch.setattr(sys, "argv", [str(script), "--saved-result", str(parent), "--selected-state-index", "2",
        "--task", str(task_file), "--extend-path", "--output", str(output), "--time-limit", "40"])
    assert cli.main() == 0 and len(calls) == 1 and calls[0]["extend_path"] is True
    assert calls[0]["saved_result"] == parent and calls[0]["selected_state_index"] == 2
    assert not output.exists()
    capsys.readouterr()
