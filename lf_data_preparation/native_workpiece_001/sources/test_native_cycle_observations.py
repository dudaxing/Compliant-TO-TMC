"""Cached body-force signs and a tiny real NumPy loading/unloading path.

The traction example is algebra, not a contact solve. The real 16-cell cycle
checks continuous native integration and storage; it is not a gripper study.
"""
from copy import deepcopy
import json
from types import SimpleNamespace

import numpy as np

from hf_eval import native_mean
from hf_eval.displacement import DisplacementSettings
from hf_eval.split_state import SplitDisplacement
from test_native_force import small_native, forbid_legacy_or_compiled_work


def test_cached_body_force_matches_applied_traction_and_disjoint_holding_groups(monkeypatch):
    # Medium traction on the lower body is (1.5, 5) N. Its external holding
    # reaction must be (-1.5, -5); reflection about y leaves Fx unchanged.
    material = np.array([-.4, -1.6, -.8, -2.4, 2., 3., 0., 4.])
    regularization = np.array([-.1, -.4, -.2, -.6, 0., 0., 0., 0.])
    arrays = dict(global_total_force=material+regularization,
        global_material_force=material, global_regularization_force=regularization,
        support_reaction=material+regularization,
        F=np.broadcast_to(np.eye(2), (1, 9, 2, 2)), J=np.ones((1, 9)),
        Hu=np.zeros((1, 2, 2, 2)), stress_first_piola=np.zeros((1, 9, 2, 2)),
        element_total_force=np.zeros((1, 8)))
    project = SimpleNamespace(model=SimpleNamespace(coordinates=np.array([[2., 2.], [3., 3.], [0., 1.], [1., 2.]])),
        solid_nodes=np.array([2, 3]), region_metadata=dict(
            workpiece=dict(cells=[0], nodes=[0, 1], dofs=[0, 1, 2, 3], background_symmetry_overlap_dofs=[3]),
            support=dict(dofs=[4, 5]), entity_symmetry=dict(dofs=[7]), background_symmetry=dict(dofs=[3, 7])))

    def no_evaluation(*args, **kwargs):
        raise AssertionError("Observing a cached force must not evaluate mechanics")

    monkeypatch.setattr(native_mean, "_assemble_force", no_evaluation)
    monkeypatch.setattr(native_mean, "_tangent", no_evaluation)
    observed = native_mean._workpiece_observations(project, SplitDisplacement(np.zeros(8), np.zeros(8)), arrays)
    np.testing.assert_allclose(observed["force_on_lower_body_N"]["material"], [1.2, 4.], rtol=0., atol=3e-16)
    np.testing.assert_allclose(observed["force_on_lower_body_N"]["regularization"], [.3, 1.], rtol=0., atol=1e-16)
    np.testing.assert_array_equal(observed["force_on_lower_body_N"]["total"], [1.5, 5.])
    assert observed["holding_reaction_on_model_N"] == [-1.5, -5.]
    assert observed["mirrored_upper_force_N"] == [1.5, -5.]
    assert observed["full_workpiece_net_force_N"] == [3., 0.]
    assert observed["two_sided_normal_magnitude_sum_N"] == 10.
    assert observed["fixed_holding_reaction_partition_N"] == {
        "workpiece": [-1.5, -5.], "support": [2., 3.], "entity_symmetry": [0., 4.], "background_symmetry": [0., 0.]}
    assert observed["overlapping_background_holding_reaction_N"] == [0., -3.]
    assert all(value == 0. for value in observed["fixed_body_fields"].values())


def test_native_cycle_returns_to_zero_without_losing_peak_identity_or_recomputing_storage(small_native, tmp_path, monkeypatch):
    source, original = small_native
    task = deepcopy(original)
    task.update(schema_version="hf-native-project-task-1.1", task_id="TEST_small_native_cycle",
                path=dict(kind="ordered_cycle", targets_mm=[0., .0005, 0.]))
    task["input"]["target_mm"] = .0005
    before = deepcopy(task)
    result = native_mean.solve_native_mean(source, task, task["path"]["targets_mm"],
        settings=DisplacementSettings(minimum_increment=.0005/16, time_limit_seconds=15.))
    assert result.path["status"] == "success"
    assert result.metadata["task_target_executed"] and result.metadata["loading_peak_reached"]
    assert result.metadata["path_completed"] and result.metadata["unload_endpoint_reached"]
    assert result.metadata["reached_displacement"] == 0. and result.metadata["task_target_mm"] == .0005
    assert [row.record["d"] for row in result.accepted] == [0., .0005, 0.]
    assert [row.record["original_target_index"] for row in result.accepted] == [0, 1, 2]
    assert [row.record["leg"] for row in result.accepted] == ["origin", "loading", "unloading"]
    assert result.metadata["call_counts"]["solver_invocations"] == 1
    assert result.metadata["call_counts"]["JIT_calls"] == result.metadata["call_counts"]["HP_calls"] == 0
    for row in result.accepted:
        assert row.record["relative_residual"] <= result.metadata["settings"]["tolerance"]
        assert abs(row.record["constraint_residual"]) <= row.record["constraint_bound"]
        assert row.record["minimum_J"] > 0.
        np.testing.assert_array_equal(row.state.fluctuation[result.project.model.fixed_dofs], 0.)
    counts = deepcopy(result.metadata["call_counts"])

    def no_evaluation(*args, **kwargs):
        raise AssertionError("Saving a cached cycle must not build or evaluate mechanics")

    for name in ("build_native_project", "_assemble_force", "_tangent"):
        monkeypatch.setattr(native_mean, name, no_evaluation)
    descriptor = native_mean.write_native_mean(result, tmp_path/"cycle")
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    assert saved["call_counts"] == counts
    assert saved["task_target_executed"] and saved["path_completed"]
    assert saved["states"][0]["d"] == saved["states"][-1]["d"] == 0.
    assert saved["states"][0]["descriptor_path"] != saved["states"][-1]["descriptor_path"]
    assert saved["save_force_calls"] == saved["save_tangent_calls"] == 0
    for row in saved["states"]:
        with np.load(descriptor.parent/row["forces"]["path"], allow_pickle=False) as forces:
            assert len(forces.files) == 17  # Existing independent HP per-state math stays usable.
    assert task == before
