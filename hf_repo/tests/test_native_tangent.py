"""Two native tangent integration tests; no repeated formal force tests.

Temporary mixed-material fixtures are shared with the force integration tests.
The tests preserve all DOFs and distinguish the non-symmetric Hu residual
Jacobian from an energy Hessian.
"""
from copy import deepcopy
from hashlib import sha256
import json

import numpy as np
from scipy import sparse

from hf_eval.data import load_geometry
from hf_eval.native_tangent import evaluate_native_tangent, write_native_tangent
from hf_eval.split_state import SplitDisplacement
from test_native_force import small_native, forbid_legacy_or_compiled_work


COMPONENTS = ("total", "material", "regularization")


def assert_scope(result):
    metadata = result.metadata
    assert metadata["matrix_units"] == "N/mm"
    assert metadata["force_calls"] == metadata["tangent_calls"] == 1
    assert metadata["solver_calls"] == metadata["HP_calls"] == metadata["JIT_calls"] == 0
    assert metadata["equilibrium_qualified"] is False and metadata["task_target_executed"] is False
    assert metadata["fixed_DOF_rows_columns_retained"] is True and metadata["matrices_symmetrized"] is False
    assert set(result.arrays) == {name+"_tangent" for name in COMPONENTS}
    assert set(result.matrices) == set(COMPONENTS)
    for name in COMPONENTS:
        tensor, matrix = result.arrays[name+"_tangent"], result.matrices[name]
        assert tensor.shape == (16, 8, 8) and tensor.dtype == np.float64
        assert not tensor.flags.writeable
        assert sparse.issparse(matrix) and matrix.format == "csc" and matrix.shape == (50, 50)


def test_zero_full_csc_translation_modes_and_lossless_saved_package(small_native, tmp_path):
    source, task = small_native
    state = SplitDisplacement(np.zeros(50), np.zeros(50))
    result = evaluate_native_tangent(source, task, state)
    assert_scope(result)
    fixed = result.project.model.fixed_dofs
    for name in COMPONENTS:
        matrix = result.matrices[name]
        # Fixed rows and columns remain physical rows/columns; a later solver
        # may reduce the system, but this force derivative must not do so.
        assert np.all(matrix.diagonal()[fixed] > 0.)
        assert matrix[fixed, :].nnz > 0 and matrix[:, fixed].nnz > 0
        scale = np.max(np.abs(matrix.data))
        for direction in ([1., 0.], [0., 1.]):
            np.testing.assert_allclose(matrix @ np.tile(direction, 25), 0., rtol=0., atol=16*np.finfo(float).eps*scale)
        asymmetry = matrix-matrix.T
        assert sparse.linalg.norm(asymmetry) <= 16*np.finfo(float).eps*sparse.linalg.norm(matrix)
    descriptor = write_native_tangent(result, tmp_path / "result")
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    assert saved["matrix_units"] == "N/mm" and saved["state_sha256"] == result.metadata["state_sha256"]
    for key, expected in (("state", dict(lift=state.lift, fluctuation=state.fluctuation)), ("tangents", result.arrays)):
        path = descriptor.parent / saved[key]["path"]
        assert sha256(path.read_bytes()).hexdigest() == saved[key]["sha256"]
        with np.load(path, allow_pickle=False) as archive:
            assert set(archive.files) == set(expected)
            for name, values in expected.items():
                assert archive[name].dtype == values.dtype and archive[name].shape == values.shape
                assert archive[name].tobytes(order="C") == values.tobytes(order="C")
    for name in COMPONENTS:
        path = descriptor.parent / saved["matrices"][name]["path"]
        assert sha256(path.read_bytes()).hexdigest() == saved["matrices"][name]["sha256"]
        copied = sparse.load_npz(path)
        assert copied.format == "csc" and copied.shape == result.matrices[name].shape
        for key in ("data", "indices", "indptr"):
            np.testing.assert_array_equal(getattr(copied, key), getattr(result.matrices[name], key))
    model_file = descriptor.parent / saved["model"]["descriptor_path"]
    assert sha256(model_file.read_bytes()).hexdigest() == saved["model"]["descriptor_file_sha256"]
    model_metadata = json.loads(model_file.read_text(encoding="utf-8"))
    assert model_metadata["task"] == task
    model_npz = descriptor.parent / saved["model"]["arrays_path"]
    assert sha256(model_npz.read_bytes()).hexdigest() == saved["model"]["arrays_sha256"]
    with np.load(model_npz, allow_pickle=False) as model:
        np.testing.assert_array_equal(model["fixed_dofs"], fixed)
        np.testing.assert_array_equal(model["coordinates"], result.project.model.coordinates)
        np.testing.assert_array_equal(model["connectivity"], result.project.model.connectivity)
    geometry = load_geometry(descriptor.parent / saved["source_geometry"]["snapshot"]["descriptor"])
    assert geometry.path.read_bytes() == source.read_bytes()
    assert geometry.geometry_id == result.project.geometry.geometry_id


def test_mixed_split_state_keeps_hu_asymmetry_and_all_local_matrix_actions(small_native):
    source, task = small_native
    original_task = deepcopy(task)
    original_source = {path.name: path.read_bytes() for path in source.parent.iterdir() if path.is_file()}
    iy, ix = np.indices((5, 5))
    physical = np.zeros((25, 2))
    physical[:, 0] = 2.**-10*((ix+iy).ravel() % 2)
    physical[[0, 5]] = 0.
    state = SplitDisplacement(.25*physical.ravel(), .75*physical.ravel())
    original_state = state.lift.tobytes(), state.fluctuation.tobytes()
    result = evaluate_native_tangent(source, task, state)
    assert_scope(result)
    assert original_task == task
    assert original_source == {path.name: path.read_bytes() for path in source.parent.iterdir() if path.is_file()}
    assert original_state == (state.lift.tobytes(), state.fluctuation.tobytes())
    assert original_state == (result.state.lift.tobytes(), result.state.fluctuation.tobytes())
    regularization = result.matrices["regularization"]
    assert sparse.linalg.norm(regularization-regularization.T) > 100*np.finfo(float).eps*sparse.linalg.norm(regularization)
    assert result.metadata["matrix_statistics"]["regularization"]["relative_asymmetry"] > 0.
    # Two distinct displacement directions, with no elimination of global
    # matrix rows. The sum of element actions is independent of CSC storage.
    vx, vy = np.zeros((25, 2)), np.zeros((25, 2))
    vx[:, 0], vy[:, 1] = ix.ravel() % 2, (ix+iy).ravel() % 2
    for direction in (vx.ravel(), vy.ravel()):
        direction[result.project.model.fixed_dofs] = 0.
        for name in COMPONENTS:
            local = result.arrays[name+"_tangent"]
            expected = np.zeros(50)
            for dofs, tangent in zip(result.project.model.edofs, local, strict=True):
                np.add.at(expected, dofs, tangent @ direction[dofs])
            actual = result.matrices[name] @ direction
            scale = np.max(np.abs(expected))
            np.testing.assert_allclose(actual, expected, rtol=0., atol=32*np.finfo(float).eps*scale)
