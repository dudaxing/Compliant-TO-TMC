"""Two small native average-control integrations, without compiled mechanics.

These temporary 16-element mixed grids verify task integration and lossless
accepted-state storage. The controller's detailed tests are kept separate.
"""
from copy import deepcopy
from hashlib import sha256
import json

import numpy as np
from scipy import sparse

from hf_eval import native_mean
from hf_eval.data import load_geometry
from hf_eval.displacement import DisplacementSettings
from test_native_force import small_native, forbid_legacy_or_compiled_work


def settings(target):
    # The smallest permitted increment follows the declared initial step/16.
    # All residual, mean, Armijo and Newton limits retain their original values.
    return DisplacementSettings(minimum_increment=target/16., time_limit_seconds=8.)


def solve_small(source, task, target):
    task = deepcopy(task)
    task["purpose"] = "average_displacement_test_only"
    task["input"]["target_mm"] = target
    return native_mean.solve_native_mean(source, task, [0., target], settings=settings(target))


def test_task_mean_control_builds_once_and_leaves_individual_port_nodes_free(small_native, monkeypatch):
    source, task = small_native
    target = .001
    task = deepcopy(task)
    task["purpose"] = "average_displacement_test_only"
    task["input"]["target_mm"] = target
    original_task = deepcopy(task)
    original_source = {p.name: p.read_bytes() for p in source.parent.iterdir() if p.is_file()}
    builder = native_mean.build_native_project
    builds = []

    def counted_build(*args, **kwargs):
        builds.append(1)
        return builder(*args, **kwargs)

    monkeypatch.setattr(native_mean, "build_native_project", counted_build)
    result = native_mean.solve_native_mean(source, task, [0., target], settings=settings(target))
    assert len(builds) == 1
    assert result.path["status"] == "success" and result.path["target_reached"] is True
    assert result.path["target_displacement"] == task["input"]["target_mm"]
    assert result.metadata["production_converged"] is result.metadata["task_target_executed"] is True
    assert result.metadata["independent_HP_qualified"] is result.metadata["equilibrium_qualified"] is False
    assert result.metadata["call_counts"]["JIT_calls"] == result.metadata["call_counts"]["HP_calls"] == 0
    assert [state.record["d"] for state in result.accepted] == [0., target]
    model = result.project.model
    assert model.ndof == 50 and len(model.connectivity) == 16
    original_settings = DisplacementSettings()
    for accepted in result.accepted:
        np.testing.assert_array_equal(accepted.state.lift, np.zeros(model.ndof))
        np.testing.assert_array_equal(accepted.state.fluctuation[model.fixed_dofs], 0.)
        assert accepted.record["relative_residual"] <= original_settings.tolerance
        assert abs(accepted.record["constraint_residual"]) <= accepted.record["constraint_bound"]
        assert accepted.record["minimum_J"] > 0.
        np.testing.assert_array_equal(accepted.arrays["spring_force_on_structure"], 0.)
    zero, final = result.accepted
    np.testing.assert_array_equal(zero.state.fluctuation, np.zeros(model.ndof))
    inlet = np.flatnonzero(result.project.bin)
    u = final.state.lift+final.state.fluctuation
    # The weighted reference-segment mean is prescribed; the three separate
    # input ux values are actual free DOFs, not a tied displacement boundary.
    np.testing.assert_allclose(result.project.bin @ u, target, rtol=0.,
                               atol=final.record["constraint_bound"])
    assert len(inlet) == 3 and np.all(inlet % 2 == 0)
    assert np.ptp(u[inlet]) > 100*np.finfo(float).eps*target
    np.testing.assert_allclose(final.arrays["input_force"],
                               result.project.bin*final.record["R_input"], rtol=0., atol=0.)
    assert task == original_task
    assert original_source == {p.name: p.read_bytes() for p in source.parent.iterdir() if p.is_file()}


def test_accepted_state_force_and_full_tangent_package_roundtrips(small_native, tmp_path, monkeypatch):
    source, task = small_native
    original_source = {p.name: p.read_bytes() for p in source.parent.iterdir() if p.is_file()}
    result = solve_small(source, task, .0005)
    assert result.path["status"] == "success" and len(result.accepted) == 2
    counts = deepcopy(result.metadata["call_counts"])

    def no_new_evaluation(*args, **kwargs):
        raise AssertionError("Saving cached accepted states must not evaluate or rebuild mechanics")

    for name in ("_assemble_force", "_tangent", "build_native_project"):
        monkeypatch.setattr(native_mean, name, no_new_evaluation)
    descriptor = native_mean.write_native_mean(result, tmp_path/"result")
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    assert saved["call_counts"] == counts == result.metadata["call_counts"]
    assert saved["save_force_calls"] == saved["save_tangent_calls"] == 0
    assert len(saved["states"]) == len(result.accepted)
    for row, accepted in zip(saved["states"], result.accepted):
        for key, expected in (("state", dict(lift=accepted.state.lift, fluctuation=accepted.state.fluctuation)),
                              ("forces", accepted.arrays), ("tangents", accepted.tangents)):
            path = descriptor.parent/row[key]["path"]
            assert sha256(path.read_bytes()).hexdigest() == row[key]["sha256"]
            with np.load(path, allow_pickle=False) as archive:
                assert set(archive.files) == set(expected)
                for name, values in expected.items():
                    np.testing.assert_array_equal(archive[name], values)
        matrix_path = descriptor.parent/row["matrix"]["path"]
        assert sha256(matrix_path.read_bytes()).hexdigest() == row["matrix"]["sha256"]
        matrix = sparse.load_npz(matrix_path)
        assert matrix.format == "csc" and matrix.shape == (50, 50)
        for name in ("data", "indices", "indptr"):
            np.testing.assert_array_equal(getattr(matrix, name), getattr(accepted.matrix, name))
        assert matrix[result.project.model.fixed_dofs, :].nnz > 0
        assert matrix[:, result.project.model.fixed_dofs].nnz > 0
        assert accepted.arrays["J"].shape == (16, 9) and np.all(accepted.arrays["J"] > 0.)
        assert set(accepted.tangents) == {name+"_tangent" for name in ("total", "material", "regularization")}
    model_path = descriptor.parent/saved["model"]["descriptor_path"]
    assert sha256(model_path.read_bytes()).hexdigest() == saved["model"]["descriptor_file_sha256"]
    model_metadata = json.loads(model_path.read_text(encoding="utf-8"))
    model_npz = descriptor.parent/saved["model"]["arrays_path"]
    assert sha256(model_npz.read_bytes()).hexdigest() == saved["model"]["arrays_sha256"]
    with np.load(model_npz, allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["coordinates"], result.project.model.coordinates)
        np.testing.assert_array_equal(archive["fixed_dofs"], result.project.model.fixed_dofs)
        np.testing.assert_array_equal(archive["b_in"], result.project.bin)
    copied = load_geometry(model_path.parent/model_metadata["source_geometry"]["snapshot"]["descriptor"])
    assert copied.path.read_bytes() == source.read_bytes()
    assert copied.geometry_id == result.project.geometry.geometry_id
    assert original_source == {p.name: p.read_bytes() for p in source.parent.iterdir() if p.is_file()}
