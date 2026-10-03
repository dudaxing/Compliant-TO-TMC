"""Native force integration on a small mixed-material grid, without JIT.

These three temporary fixtures check force/state storage and mechanics
identities. They do not repeat the six formal supplied-displacement tests.
"""
from copy import deepcopy
from hashlib import sha256
import json

import numpy as np
import pytest

from hf_eval.data import load_geometry, write_geometry
from hf_eval.native_force import evaluate_native_force, write_native_force
from hf_eval.split_state import SplitDisplacement
from hf_eval import split_kernel_invariants_hu as kernel
from hf_eval import tmc, tmc_kernel


@pytest.fixture(autouse=True)
def forbid_legacy_or_compiled_work(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Native force-only entry invoked legacy or compiled work")
    for module, names in ((kernel, ("_runtime", "_batch_with_tangent", "_batch_without_tangent", "batch_response_split", "assemble_split")),
                          (tmc, ("assemble",)), (tmc_kernel, ("_runtime", "batch_response"))):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)


@pytest.fixture
def small_native(tmp_path):
    metadata = dict(schema_version="hf-geometry-1.0", case_family="gripper",
        grid=dict(shape_yx=[4, 4], origin_mm=[0., 0.], cell_size_mm=[.5, .5], axes=[[1., 0.], [0., 1.]],
                  extent_mm=[2., 2.], array_order="C_yx_bottom_up", value_location="cell"),
        thickness_mm=2., model_extent=dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=2.)),
        region_tags=dict(support=dict(points_mm=[[0., 0.], [0., .5]], components=[0, 1]),
            symmetry=dict(points_mm=[[0., 2.], [2., 2.]], components=[1]),
            input=dict(points_mm=[[0., 1.], [0., 2.]], direction=[1., 0.], averaging="normalized_reference_arclength_trapezoid"),
            output=dict(points_mm=[[2., .5], [2., 1.5]], direction=[0., 1.], averaging="normalized_reference_arclength_trapezoid")))
    solid = np.ones((4, 4), dtype=np.uint8)
    solid[1, 1] = 0
    arrays = dict(solid=solid, design=np.ones_like(solid), passive_solid=np.zeros_like(solid), passive_void=np.zeros_like(solid))
    source = write_geometry(tmp_path / "source", metadata, arrays)
    geometry = load_geometry(source)
    task = dict(schema_version="hf-native-project-task-1.0", task_id="TEST_small_native_force", case_family="gripper",
        purpose="supplied_displacement_test_only", units=dict(length="mm", force="N", stress="MPa", energy="N mm"),
        geometry=dict(geometry_id=geometry.geometry_id, descriptor_sha256=geometry.metadata["descriptor_sha256"]),
        analysis_grid=dict(policy="native"), material=dict(E_MPa=1., nu=.3, formulation="plane_strain"),
        third_medium=dict(gamma=1e-6), regularization=dict(alpha=1e-4, length_mm=2.),
        input=dict(tag="input", control="average_displacement", target_mm=.025), output=dict(tag="output", spring_N_per_mm=0.),
        constraints=[dict(tag="support", components=[0, 1]), dict(tag="symmetry", components=[1])],
        support_selection="solid_incident_nodes_only", background_symmetry=None, input_auxiliary_spring_N_per_mm=0.,
        workpiece=None, reference_state="undeformed", qualification_criteria=dict(max_design_volume_fraction=None, min_feature_mm=None))
    return source, task


def assert_force_scope(result):
    metadata = result.metadata
    assert metadata["force_only"] is True and metadata["force_calls"] == 1
    assert metadata["tangent_calls"] == metadata["solver_calls"] == 0
    assert metadata["equilibrium_qualified"] is False and metadata["task_target_executed"] is False
    assert "tangent" not in result.arrays
    assert all(array.dtype == np.float64 and not array.flags.writeable for array in result.arrays.values())


def test_zero_state_identity_and_lossless_saved_package(small_native, tmp_path):
    source, task = small_native
    state = SplitDisplacement(np.zeros(50), np.zeros(50))
    result = evaluate_native_force(source, task, state)
    assert_force_scope(result)
    assert result.metadata["fixed_displacement_compatible"] is True
    for name, values in result.arrays.items():
        if name == "J":
            np.testing.assert_array_equal(values, np.ones((16, 9)))
        elif name == "F":
            np.testing.assert_array_equal(values, np.broadcast_to(np.eye(2), (16, 9, 2, 2)))
        else:
            np.testing.assert_array_equal(values, np.zeros_like(values), err_msg=name)
    descriptor = write_native_force(result, tmp_path / "result")
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    assert saved["state_sha256"] == result.metadata["state_sha256"]
    for key in ("state", "forces"):
        path = descriptor.parent / saved[key]["path"]
        assert sha256(path.read_bytes()).hexdigest() == saved[key]["sha256"]
        with np.load(path, allow_pickle=False) as archive:
            expected = dict(lift=state.lift, fluctuation=state.fluctuation) if key == "state" else result.arrays
            assert set(archive.files) == set(expected)
            for name, values in expected.items():
                np.testing.assert_array_equal(archive[name], values)
    copied = load_geometry(descriptor.parent / saved["source_geometry"]["snapshot"]["descriptor"])
    assert copied.path.read_bytes() == source.read_bytes()
    assert copied.geometry_id == result.project.geometry.geometry_id


def test_nonzero_split_components_scatter_and_preserve_inputs(small_native):
    source, task = small_native
    original_task = deepcopy(task)
    original_source = {p.name: p.read_bytes() for p in source.parent.iterdir() if p.is_file()}
    iy, ix = np.indices((5, 5))
    physical = np.zeros((25, 2))
    physical[:, 0] = 2.**-10 * ((ix+iy).ravel() % 2)
    physical[[0, 5], :] = 0.  # Actual two-node support, not the input port.
    state = SplitDisplacement(.25*physical.ravel(), .75*physical.ravel())
    before = (state.lift.tobytes(), state.fluctuation.tobytes())
    result = evaluate_native_force(source, task, state)
    assert_force_scope(result)
    assert result.metadata["fixed_displacement_compatible"] is True
    assert task == original_task
    assert original_source == {p.name: p.read_bytes() for p in source.parent.iterdir() if p.is_file()}
    assert before == (state.lift.tobytes(), state.fluctuation.tobytes())
    assert before == (result.state.lift.tobytes(), result.state.fluctuation.tobytes())
    assert result.arrays["J"].min() > 0. and np.any(result.arrays["Hu"])
    assert np.any(result.arrays["element_regularization_force"])
    assert result.arrays["material_energy"].sum() > 0.
    for component in ("total", "material", "regularization"):
        element = result.arrays["element_"+component+"_force"]
        force = result.arrays["global_"+component+"_force"]
        independent = np.zeros(result.project.model.ndof)
        np.add.at(independent, result.project.model.edofs.ravel(), element.ravel())
        np.testing.assert_array_equal(force, independent)
        # Constant virtual translations perform zero internal work, including
        # the Hu term. This checks all unconstrained and support DOFs together.
        net = force.reshape(-1, 2).sum(axis=0)
        np.testing.assert_allclose(net, 0., rtol=0., atol=3e-15*np.abs(force).sum())
    scale = np.max(np.abs(result.arrays["global_total_force"]))
    np.testing.assert_allclose(result.arrays["global_total_force"],
        result.arrays["global_material_force"]+result.arrays["global_regularization_force"], rtol=0., atol=8e-15*scale)


def test_rigid_translation_is_evaluated_without_silently_imposing_fixed_values(small_native):
    source, task = small_native
    lift = np.zeros((25, 2))
    fluctuation = np.zeros_like(lift)
    lift[:, 0], fluctuation[:, 0] = 2.**-8, 2.**-9
    state = SplitDisplacement(lift.ravel(), fluctuation.ravel())
    result = evaluate_native_force(source, task, state)
    assert_force_scope(result)
    assert result.metadata["fixed_displacement_compatible"] is False
    np.testing.assert_array_equal(result.state.lift, state.lift)
    np.testing.assert_array_equal(result.state.fluctuation, state.fluctuation)
    np.testing.assert_array_equal(result.arrays["J"], np.ones((16, 9)))
    for name in ("Hu", "global_total_force", "global_material_force", "global_regularization_force", "material_energy"):
        np.testing.assert_array_equal(result.arrays[name], np.zeros_like(result.arrays[name]), err_msg=name)
