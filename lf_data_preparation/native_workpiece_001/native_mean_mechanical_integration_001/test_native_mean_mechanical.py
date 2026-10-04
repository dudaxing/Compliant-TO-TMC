"""Two temporary 16-cell mechanical-only mean-path integrations.

They verify energy omission, ordered-cycle integration and cached success or
partial persistence. They do not qualify a workpiece or a physical gripper.
"""
from copy import deepcopy
from hashlib import sha256
import json

import numpy as np
import pytest
from scipy import sparse

from hf_eval import native_mean, split_kernel_invariants_hu as kernel
from hf_eval.displacement import DisplacementSettings
from hf_eval.tmc_kernel import KernelError
from test_native_force import small_native, forbid_legacy_or_compiled_work


PEAK = .0005
FORCE_FIELDS = {
    "element_total_force", "element_material_force", "element_regularization_force",
    "global_total_force", "global_material_force", "global_regularization_force",
    "J", "Hu", "F", "stress_first_piola", "stress_second_piola", "input_force",
    "support_reaction", "spring_force_on_structure", "force_residual", "global_force_balance"}


def cycle_task(original):
    task = deepcopy(original)
    task.update(schema_version="hf-native-project-task-1.1", task_id="TEST_small_mechanical_cycle",
                purpose="average_displacement_test_only",
                path=dict(kind="ordered_cycle", targets_mm=[0., PEAK, 0.]))
    task["input"]["target_mm"] = PEAK
    return task


@pytest.fixture
def mechanical_only(monkeypatch):
    original = kernel._response
    seen = []

    def energy_trap(*args, **kwargs):
        assert kwargs.get("auxiliary_energy") is False, "Auxiliary energy must not be evaluated"
        seen.append(False)
        return original(*args, **kwargs)

    def no_complete_fallback(*args, **kwargs):
        raise AssertionError("Mechanical mean path fell back to the complete force entry")

    monkeypatch.setattr(kernel, "_response", energy_trap)
    monkeypatch.setattr(native_mean, "_assemble_force", no_complete_fallback)
    return seen


def assert_mechanical_contract(record):
    assert record["response_mode"] == "mechanical"
    assert record["response_contract"] == "split-numpy-mechanical-1.0"
    assert record["force_kernel_version"] == kernel.MECHANICAL_KERNEL_VERSION
    assert record["auxiliary_material_energy"] == {
        "status": "not_evaluated", "qualified": False, "field_present": False}


def save_and_check(result, directory, monkeypatch):
    counts = deepcopy(result.metadata["call_counts"])

    def no_evaluation(*args, **kwargs):
        raise AssertionError("Cached persistence must not build or evaluate mechanics")

    for name in ("build_native_project", "_assemble_force", "_assemble_mechanical_force", "_tangent"):
        monkeypatch.setattr(native_mean, name, no_evaluation)
    descriptor = native_mean.write_native_mean(result, directory)
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    assert saved["schema_version"] == "hf-native-mean-result-1.2"
    assert_mechanical_contract(saved)
    assert saved["call_counts"] == counts == result.metadata["call_counts"]
    assert saved["save_force_calls"] == saved["save_tangent_calls"] == 0
    assert len(saved["states"]) == len(result.accepted)
    for row, accepted in zip(saved["states"], result.accepted):
        assert_mechanical_contract(row)
        assert set(accepted.arrays) == FORCE_FIELDS
        assert set(accepted.tangents) == {name+"_tangent" for name in ("total", "material", "regularization")}
        for key, expected in (("state", dict(lift=accepted.state.lift, fluctuation=accepted.state.fluctuation)),
                              ("forces", accepted.arrays), ("tangents", accepted.tangents)):
            path = descriptor.parent/row[key]["path"]
            assert sha256(path.read_bytes()).hexdigest() == row[key]["sha256"]
            with np.load(path, allow_pickle=False) as archive:
                assert set(archive.files) == set(expected)
                for name, values in expected.items():
                    assert archive[name].dtype == values.dtype and archive[name].shape == values.shape
                    assert archive[name].tobytes() == values.tobytes()
        matrix_path = descriptor.parent/row["matrix"]["path"]
        assert sha256(matrix_path.read_bytes()).hexdigest() == row["matrix"]["sha256"]
        matrix = sparse.load_npz(matrix_path)
        assert matrix.format == "csc" and matrix.shape == (50, 50)
        for name in ("data", "indices", "indptr"):
            assert getattr(matrix, name).tobytes() == getattr(accepted.matrix, name).tobytes()
        assert matrix[result.project.model.fixed_dofs, :].nnz > 0
        assert matrix[:, result.project.model.fixed_dofs].nnz > 0
    return saved


def test_mechanical_cycle_omits_energy_and_saves_cached_full_dof_data(small_native, tmp_path, monkeypatch, mechanical_only):
    source, original = small_native
    task = cycle_task(original)
    before = deepcopy(task)
    source_bytes = {p.name: p.read_bytes() for p in source.parent.iterdir() if p.is_file()}
    original_builder, builds = native_mean.build_native_project, []

    def counted_build(*args, **kwargs):
        builds.append(1)
        return original_builder(*args, **kwargs)

    monkeypatch.setattr(native_mean, "build_native_project", counted_build)
    result = native_mean.solve_native_mean(source, task, task["path"]["targets_mm"], response_mode="mechanical",
        settings=DisplacementSettings(minimum_increment=PEAK/16., time_limit_seconds=15.))
    # Save before checking convergence so a failed return retains its evidence.
    saved = save_and_check(result, tmp_path/"cycle", monkeypatch)
    assert len(builds) == 1 and mechanical_only
    assert result.path["status"] == saved["status"] == "success"
    assert result.metadata["path_completed"] and result.metadata["loading_peak_reached"]
    assert result.metadata["unload_endpoint_reached"] and result.metadata["task_target_executed"]
    originals = [row for row in result.accepted if row.record["is_original_target"]]
    assert [row.record["d"] for row in originals] == [0., PEAK, 0.]
    assert [row.record["original_target_index"] for row in originals] == [0, 1, 2]
    assert [row.record["leg"] for row in originals] == ["origin", "loading", "unloading"]
    assert saved["states"][0]["descriptor_path"] != saved["states"][-1]["descriptor_path"]
    assert result.metadata["call_counts"]["solver_invocations"] == 1
    assert result.metadata["call_counts"]["JIT_calls"] == result.metadata["call_counts"]["HP_calls"] == 0
    for accepted in result.accepted:
        assert_mechanical_contract(accepted.record)
        assert accepted.record["relative_residual"] <= DisplacementSettings().tolerance
        assert abs(accepted.record["constraint_residual"]) <= accepted.record["constraint_bound"]
        assert accepted.record["minimum_J"] > 0.
        np.testing.assert_array_equal(accepted.state.lift, 0.)
        np.testing.assert_array_equal(accepted.state.fluctuation[result.project.model.fixed_dofs], 0.)
    assert task == before
    assert source_bytes == {p.name: p.read_bytes() for p in source.parent.iterdir() if p.is_file()}


def test_mechanical_partial_path_preserves_failure_and_cached_origin(small_native, tmp_path, monkeypatch, mechanical_only):
    source, original = small_native
    task = cycle_task(original)
    original_tangent, calls = native_mean._tangent, []

    def fail_second_tangent(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise KernelError("Injected tangent failure after accepted origin", code="injected_failure")
        return original_tangent(*args, **kwargs)

    monkeypatch.setattr(native_mean, "_tangent", fail_second_tangent)
    result = native_mean.solve_native_mean(source, task, task["path"]["targets_mm"], response_mode="mechanical",
        settings=DisplacementSettings(minimum_increment=PEAK/16., max_bisections=0, time_limit_seconds=15.))
    assert len(calls) == 2 and mechanical_only
    assert result.path["status"] == "failed" and result.path["failure"]["code"] == "injected_failure"
    assert result.path["failed_attempts"][-1]["rollback_bitwise_equal"] is True
    assert len(result.accepted) == 1 and result.accepted[0].record["original_target_index"] == 0
    counts = result.metadata["call_counts"]
    assert counts["tangent_calls"] == 2 and counts["tangent_calls_completed"] == 1
    saved = save_and_check(result, tmp_path/"partial", monkeypatch)
    assert saved["status"] == "failed" and saved["failure"] == result.path["failure"]
    assert saved["path_completed"] is saved["loading_peak_reached"] is saved["unload_endpoint_reached"] is False
    assert saved["task_target_executed"] is False and saved["reached_displacement"] == 0.
    assert len(saved["states"]) == 1 and saved["states"][0]["d"] == 0.
