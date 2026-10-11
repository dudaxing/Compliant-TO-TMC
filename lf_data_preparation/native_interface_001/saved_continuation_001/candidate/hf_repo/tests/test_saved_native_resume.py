"""Focused continuation tests: controller transport and one tiny public path.

The linear controller fixture is not a TMC material validation. The 16-cell
integration checks public persistence/options/parent semantics, not contact,
pressure, a gripper, exhaustive tangent columns or physical HF qualification.
"""
from dataclasses import replace
import json

import numpy as np
import pytest

from hf_eval import native_mean
from hf_eval.displacement import DisplacementSettings
from hf_eval.native_evaluate import evaluate_native
from hf_eval.split_displacement import solve_split_displacement_path
from hf_eval.split_state import SplitDisplacement
from hf_eval.tmc import TMCError
from hf_eval.tmc_kernel import KernelError
from test_native_force import small_native, forbid_legacy_or_compiled_work
from test_native_mean_mechanical import PEAK, cycle_task
from test_split_cycle import dense_port_solution
from test_split_displacement import one_cell, physical, synthetic


def linear_anchor():
    model,port = one_cell()
    matrix,assembler = synthetic(model)
    shape = np.zeros(model.ndof)
    shape[[2,6]] = [.5,.25]
    cold = solve_split_displacement_path(model,port,port,[0.,.15625,.3125,.15625,0.],
        lift_shape=shape,assembler=assembler,force_scale_per_length=20.,path_mode="ordered_cycle")
    assert cold["status"] == "success"
    row = cold["accepted_steps"][2]
    state = SplitDisplacement(row["u_lift"],row["u_fluctuation"])
    return model,port,matrix,assembler,shape,cold,row,state


def test_absolute_anchor_fresh_tangent_and_linear_suffix():
    model,port,matrix,assembler,shape,cold,anchor,state = linear_anchor()
    seen = []

    def record(actual_model,candidate,*,tangent=True):
        seen.append((candidate.lift.tobytes(),candidate.fluctuation.tobytes(),tangent))
        return assembler(actual_model,candidate,tangent=tangent)

    warm = solve_split_displacement_path(model,port,port,[.3125,.15625,0.],
        initial_state=state,initial_R=anchor["R_input"],initial_parameter=.3125,
        lift_shape=shape,assembler=record,force_scale_per_length=20.,path_mode="ordered_cycle")
    assert warm["status"] == "success" and warm["initial_parameter"] == .3125
    assert seen[0] == (state.lift.tobytes(),state.fluctuation.tobytes(),True)
    first = warm["accepted_steps"][0]
    assert first["leg"] == "resume_origin" and first["newton_checks"] == 1
    assert first["state_sha256"] == anchor["state_sha256"]
    assert np.float64(first["R_input"]).tobytes() == np.float64(anchor["R_input"]).tobytes()
    assert [row["original_target_index"] for row in warm["accepted_steps"]] == [0,1,2]
    assert [row["stage_parameter"] for row in warm["linear_solve_diagnostics"]] == [.15625,0.]
    for target,row in zip([.3125,.15625,0.],warm["accepted_steps"]):
        expected,R = dense_port_solution(model,matrix,port,target)
        np.testing.assert_allclose(physical(row),expected,rtol=1e-12,atol=1e-14)
        assert row["R_input"] == pytest.approx(R,rel=1e-12,abs=1e-14)
    # Explicit p0=0 follows the old zero-start arithmetic and result schema.
    zero = solve_split_displacement_path(model,port,port,[0.,.15625,.3125,.15625,0.],
        initial_parameter=0.,lift_shape=shape,assembler=assembler,force_scale_per_length=20.,path_mode="ordered_cycle")
    assert "initial_parameter" not in zero
    assert [(r["state_sha256"],r["R_input"],r["leg"]) for r in zero["accepted_steps"]] == [
        (r["state_sha256"],r["R_input"],r["leg"]) for r in cold["accepted_steps"]]


def test_non_equilibrated_anchor_stops_before_correction_or_commit():
    model,port,_,assembler,shape,_,anchor,state = linear_anchor()
    accepted = []
    wrong_R = anchor["R_input"]+1.
    result = solve_split_displacement_path(model,port,port,[.3125,0.],
        initial_state=state,initial_R=wrong_R,initial_parameter=.3125,lift_shape=shape,
        assembler=assembler,force_scale_per_length=20.,path_mode="ordered_cycle",on_accept=accepted.append)
    assert result["failure"]["code"] == "initial_state_not_equilibrated"
    assert not accepted and not result["accepted_steps"] and not result["linear_solve_diagnostics"]
    assert not result["trials"] and result["timing_seconds"]["kernel_calls"] == 1
    assert result["u_lift"].tobytes() == state.lift.tobytes()
    assert result["u_fluctuation"].tobytes() == state.fluctuation.tobytes()
    assert result["R_input"] == wrong_R and result["reached_displacement"] == .3125
    assert result["failed_attempts"][0]["rollback_bitwise_equal"]


def test_unaccepted_descending_attempt_rolls_back_revalidated_anchor():
    model,port,_,assembler,shape,_,anchor,state = linear_anchor()

    def reject_unloading(actual_model,candidate,*,tangent=True):
        if not np.array_equal(candidate.lift,state.lift):
            raise KernelError("Injected descending failure",code="invalid_J")
        return assembler(actual_model,candidate,tangent=tangent)

    result = solve_split_displacement_path(model,port,port,[.3125,0.],
        initial_state=state,initial_R=anchor["R_input"],initial_parameter=.3125,lift_shape=shape,
        assembler=reject_unloading,force_scale_per_length=20.,path_mode="ordered_cycle",
        settings=DisplacementSettings(minimum_increment=.01,max_bisections=0))
    assert result["failure"]["code"] == "invalid_J" and len(result["accepted_steps"]) == 1
    assert result["failed_attempts"][-1]["rollback_bitwise_equal"]
    assert result["u_lift"].tobytes() == state.lift.tobytes()
    assert result["u_fluctuation"].tobytes() == state.fluctuation.tobytes()
    assert np.float64(result["R_input"]).tobytes() == np.float64(anchor["R_input"]).tobytes()


def test_nonzero_parameter_requires_finite_matching_ordered_saved_anchor():
    model,port,_,assembler,shape,_,anchor,state = linear_anchor()
    kwargs = dict(initial_state=state,initial_R=anchor["R_input"],lift_shape=shape,
        assembler=assembler,force_scale_per_length=20.,path_mode="ordered_cycle")
    for parameter,targets in ((float("nan"),[.3125,0.]),(float("inf"),[.3125,0.]),(.25,[.3125,0.])):
        with pytest.raises(TMCError):
            solve_split_displacement_path(model,port,port,targets,initial_parameter=parameter,**kwargs)
    for changed in (dict(initial_state=None),dict(path_mode="load_only"),dict(lift_shape=np.zeros(model.ndof))):
        with pytest.raises(TMCError):
            solve_split_displacement_path(model,port,port,[.3125,0.],initial_parameter=.3125,**(kwargs|changed))


def test_public_saved_partial_resume_inherits_options_and_preserves_parent(small_native,tmp_path,monkeypatch):
    source,original = small_native
    task = cycle_task(original)
    settings = DisplacementSettings(minimum_increment=PEAK/16.,time_limit_seconds=30.)

    def stop_after_peak(snapshot):
        if snapshot.record["d"] == PEAK:
            raise TMCError("Test stops after accepted peak",code="time_limit")

    parent = native_mean.solve_native_mean(source,task,task["path"]["targets_mm"],settings=settings,
        response_mode="mechanical",tangent_mode="chunk256",initial_guess="port_projection",on_accept=stop_after_peak)
    assert parent.metadata["status"] == "failed" and parent.metadata["failure"]["code"] == "time_limit"
    parent_file = native_mean.write_native_mean(parent,tmp_path/"parent")
    before = {p.relative_to(parent_file.parent).as_posix():p.read_bytes() for p in parent_file.parent.rglob("*") if p.is_file()}
    selected = next(i for i,row in enumerate(parent.accepted) if row.record["d"] == PEAK and row.record["is_original_target"])
    with pytest.raises(TMCError,match="explicit time limit"):
        native_mean.solve_native_mean(None,None,None,saved_result=parent_file,selected_state_index=selected)
    with pytest.raises(TMCError,match="settings/options"):
        native_mean.solve_native_mean(None,None,None,saved_result=parent_file,selected_state_index=selected,
            settings=replace(settings,time_limit_seconds=35.),tangent_mode="full")
    with pytest.raises(TMCError,match="exact nonzero original-task suffix"):
        native_mean.solve_native_mean(None,None,[PEAK,PEAK/2.,0.],saved_result=parent_file,selected_state_index=selected,
            settings=replace(settings,time_limit_seconds=35.))
    original_solve,captured = native_mean.solve_native_mean,[]

    def capture(*args,**kwargs):
        result = original_solve(*args,**kwargs)
        captured.append(result)
        return result

    monkeypatch.setattr("hf_eval.native_evaluate.solve_native_mean",capture)
    response = evaluate_native(None,None,tmp_path/"child",saved_result=parent_file,selected_state_index=selected,
        time_limit_seconds=35.)
    child, = captured
    assert response["status"] == "success" and response["path"]["completed"]
    assert response["target_response"] is None and not response["path"]["task_target_executed"]
    assert not response["path"]["full_original_path_completed"]
    assert response["requested_endpoint_response"]["d_mm"] == 0.
    assert {key:part["value"] for key,part in response["options"].items()} == dict(
        response_mode="mechanical",tangent_mode="chunk256",initial_guess="port_projection")
    assert child.metadata["settings"] == parent.metadata["settings"] | {"time_limit_seconds":35.}
    assert child.metadata["continuation"]["anchor_revalidated"] and child.metadata["continuation"]["anchor_identity_preserved"]
    assert child.metadata["continuation"]["parent_status"] == "failed"
    assert not child.metadata["continuation"]["parent_path_completed"]
    assert child.project.task == task and child.project.task_hash == parent.project.task_hash
    originals = [row.record for row in child.accepted if row.record["is_original_target"]]
    assert [(r["original_target_index"],r["child_original_target_index"],r["leg"]) for r in originals] == [(1,0,"resume_origin"),(2,1,"unloading")]
    assert originals[0]["state_sha256"] == parent.accepted[selected].record["state_sha256"]
    assert child.metadata["call_counts"]["solver_invocations"] == 1
    assert child.metadata["save_force_calls"] == child.metadata["save_tangent_calls"] == 0
    assert child.metadata["call_counts"]["HP_calls"] == child.metadata["call_counts"]["JIT_calls"] == 0
    assert before == {p.relative_to(parent_file.parent).as_posix():p.read_bytes() for p in parent_file.parent.rglob("*") if p.is_file()}
    saved = json.loads((tmp_path/"child"/"result.json").read_text(encoding="utf-8"))
    assert saved["continuation"]["parent_result"]["sha256"] == response["continuation"]["parent_result"]["sha256"]
