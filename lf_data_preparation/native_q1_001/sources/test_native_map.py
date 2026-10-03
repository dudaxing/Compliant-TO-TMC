"""Native Q1 data mapping: indices, port work and portable source snapshots.

Historical models are read only for geometry/port arrays; no mechanics module,
material, applied constraint policy or equilibrium qualification is imported.
"""
from hashlib import sha256
import json
from pathlib import Path
import shutil

import numpy as np
import pytest

from hf_eval.data import ARRAY_NAMES, GeometryError, load_geometry, write_geometry
from hf_eval.native_map import prepare_native_geometry, write_native_geometry_map


ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / "lf_data_preparation" / "v2_adapter_001"
ALIASES = ("inverter_canonical", "gripper_canonical", "gripper_native_fine")
HISTORICAL_MODELS = {
    "inverter_canonical": ("hf4_c2_stable_f_validation/numpy_inverter_prefix_001/solve/model.npz",
                           "f6537e80717d3fab79711fccc735b9513e88777b50497fed6089e49cb4518f5a"),
    "gripper_canonical": ("hf4_c2_stable_f_validation/numpy_gripper_prefix_001/solve/model.npz",
                          "274969a04f3cb1e794737b91fd99608360187b24d7d4760de1e3d44b7b6c862b"),
}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def assert_affine_mean_and_work(mapping):
    arrays = mapping.arrays
    coordinates = arrays["coordinates_mm"]
    x, y = coordinates.T
    displacement = np.column_stack((1. + .25*x - .5*y, -2. + .75*x + .125*y))
    for name in ("input", "output"):
        vector = arrays[name + "_vector"]
        nodes = arrays[name + "_nodes"]
        weights = arrays[name + "_weights"]
        tag = mapping.geometry.metadata["region_tags"][name]
        direction = np.array(tag["direction"])
        midpoint = np.mean(tag["points_mm"], axis=0)
        expected_mean = direction @ np.array([1. + .25*midpoint[0] - .5*midpoint[1],
                                              -2. + .75*midpoint[0] + .125*midpoint[1]])
        assert vector @ displacement.ravel() == pytest.approx(expected_mean, rel=2e-15, abs=5e-14)
        # An independent nodal virtual-work sum must match the generalized
        # port work; this checks component and weight placement in the vector.
        reaction = -7.25
        nodal_load = reaction * weights[:, None] * direction
        nodal_work = np.sum(nodal_load * displacement[nodes])
        assert nodal_work == pytest.approx(reaction * expected_mean, rel=3e-15, abs=5e-13)
        assert (reaction * vector) @ displacement.ravel() == pytest.approx(nodal_work, rel=3e-15, abs=5e-13)


@pytest.mark.parametrize("alias", ALIASES)
def test_real_native_indices_port_means_and_lossless_saved_mapping(alias, tmp_path):
    source = PREVIOUS / "converted" / alias / "geometry.json"
    pins = json.loads((PREVIOUS / "execution_receipt.json").read_text(encoding="utf-8"))
    pin = next(item for item in pins["cases"] if item["alias"] == alias)
    assert digest(source) == pin["descriptor_sha256"]
    assert digest(source.with_name("geometry.npz")) == pin["array_sha256"]
    mapping = prepare_native_geometry(source)
    arrays, geometry = mapping.arrays, mapping.geometry
    ny, nx = geometry.grid["shape_yx"]
    dx, dy = geometry.grid["cell_size_mm"]
    x0, y0 = geometry.grid["origin_mm"]
    nodes = np.arange((ny+1)*(nx+1))
    expected_coordinates = np.column_stack((x0 + (nodes % (nx+1))*dx, y0 + (nodes // (nx+1))*dy))
    np.testing.assert_array_equal(arrays["coordinates_mm"], expected_coordinates)
    # Each element occupies its original C_yx cell and has counterclockwise
    # local nodes BL, BR, TR, TL; the signed shoelace area must be positive.
    cells = np.arange(ny*nx)
    bottom_left = (cells // nx)*(nx+1) + cells % nx
    expected_connectivity = np.column_stack((bottom_left, bottom_left+1, bottom_left+nx+2, bottom_left+nx+1))
    np.testing.assert_array_equal(arrays["connectivity"], expected_connectivity)
    xy = arrays["coordinates_mm"][arrays["connectivity"]]
    area = .5*np.sum(xy[:, :, 0]*np.roll(xy[:, :, 1], -1, axis=1) - xy[:, :, 1]*np.roll(xy[:, :, 0], -1, axis=1), axis=1)
    np.testing.assert_array_equal(area, np.full(nx*ny, dx*dy))
    for name in ARRAY_NAMES:
        assert arrays[name].dtype == np.dtype("uint8")
        np.testing.assert_array_equal(arrays[name], geometry.arrays[name])
    if alias == "gripper_native_fine":
        assert arrays["connectivity"].shape == (12800, 4)
        assert arrays["coordinates_mm"].shape == (13041, 2)
        assert arrays["input_vector"].shape == (26082,)
        for name in ("input", "output"):
            np.testing.assert_array_equal(arrays[name+"_weights"], [.125, .25, .25, .25, .125])
    else:
        model_path, model_sha = HISTORICAL_MODELS[alias]
        assert digest(ROOT / model_path) == model_sha
        with np.load(ROOT / model_path, allow_pickle=False) as old:
            for new, previous in (("coordinates_mm", "coordinates"), ("connectivity", "connectivity"),
                                  ("input_vector", "b_in"), ("output_vector", "b_out")):
                np.testing.assert_array_equal(arrays[new], old[previous])
            np.testing.assert_array_equal(arrays["solid"].ravel(), old["solid"])
    assert_affine_mean_and_work(mapping)
    metadata = mapping.metadata
    assert metadata["counts"]["elements"] == nx*ny
    assert metadata["counts"]["nodes"] == (nx+1)*(ny+1)
    assert metadata["counts"]["dofs"] == 2*(nx+1)*(ny+1)
    assert metadata["geometry_metadata"] == geometry.metadata
    assert metadata["source_geometry_file_sha256"] == digest(source)
    assert metadata["source_geometry_descriptor_sha256"] == geometry.metadata["descriptor_sha256"]
    assert metadata["source_geometry_npz_sha256"] == digest(source.with_name("geometry.npz"))
    assert metadata["constraints_applied"] is False
    assert metadata["material_assigned"] is False
    assert metadata["task_created"] is False
    assert metadata["analysis_grid_policy"] == "not_selected"
    assert not {"fixed_dofs", "free_dofs", "lam", "mu", "gamma"}.intersection(arrays)
    descriptor = write_native_geometry_map(mapping, tmp_path / alias)
    saved = json.loads(descriptor.read_text(encoding="utf-8"))
    with np.load(descriptor.parent / saved["arrays"]["path"], allow_pickle=False) as archive:
        assert set(archive.files) == set(arrays)
        for name, values in arrays.items():
            np.testing.assert_array_equal(archive[name], values)
    snapshot = load_geometry(descriptor.parent / saved["source_geometry_snapshot"]["descriptor_path"])
    assert snapshot.geometry_id == geometry.geometry_id
    assert snapshot.path.read_bytes() == source.read_bytes()
    for name in ARRAY_NAMES:
        np.testing.assert_array_equal(snapshot.arrays[name], geometry.arrays[name])


@pytest.mark.parametrize("alias,attached,background_count", [
    ("inverter_canonical", 4, 0), ("gripper_canonical", 3, 20), ("gripper_native_fine", 4, 40),
])
def test_source_region_sets_are_closed_and_not_applied(alias, attached, background_count):
    mapping = prepare_native_geometry(PREVIOUS / "converted" / alias / "geometry.json")
    arrays = mapping.arrays
    incident = arrays["solid_incident"].astype(bool)
    for name in ("support", "symmetry"):
        np.testing.assert_array_equal(arrays[name+"_solid_nodes"], arrays[name+"_nodes"][incident[arrays[name+"_nodes"]]])
    assert len(arrays["support_solid_nodes"]) == attached
    support_coordinates = arrays["coordinates_mm"][arrays["support_nodes"]]
    np.testing.assert_array_equal(support_coordinates[[0, -1]], [[0., 0.], [0., 8.]])
    background = arrays["background_source_nodes"]
    assert len(background) == background_count
    np.testing.assert_array_equal(arrays["background_source_solid_nodes"], background[incident[background]])
    if background_count:
        coordinates = arrays["coordinates_mm"][background]
        assert np.all(coordinates[:, 0] > 60.) and np.all(coordinates[:, 0] <= 80.)
        assert coordinates[0, 0] == 60. + mapping.geometry.grid["cell_size_mm"][0]
        assert coordinates[-1, 0] == 80. and np.all(coordinates[:, 1] == 40.)
        assert not np.intersect1d(background, arrays["symmetry_nodes"]).size


def rectangular_geometry(directory, *, reverse=False, off_grid=False):
    metadata = dict(schema_version="hf-geometry-1.0", case_family="synthetic_native",
        grid=dict(shape_yx=[2, 3], origin_mm=[10., -3.], cell_size_mm=[2., .5], axes=[[1., 0.], [0., 1.]],
                  extent_mm=[6., 1.], array_order="C_yx_bottom_up", value_location="cell"),
        thickness_mm=2., model_extent=dict(kind="lower_half", symmetry_axis=dict(normal=[0., 1.], offset_mm=-2.)),
        region_tags=dict(support=dict(points_mm=[[10., -3.], [10., -2.]], components=[0, 1]),
            symmetry=dict(points_mm=[[10., -2.], [16., -2.]], components=[1]),
            input=dict(points_mm=[[10., -3.], [10., -2.]], direction=[1., 0.], averaging="normalized_reference_arclength_trapezoid"),
            output=dict(points_mm=[[16., -3.], [16., -2.]], direction=[0., 1.], averaging="normalized_reference_arclength_trapezoid")))
    if reverse:
        for tag in metadata["region_tags"].values():
            tag["points_mm"].reverse()
    if off_grid:
        metadata["region_tags"]["input"]["points_mm"][1][1] = -2.75
    ones = np.ones((2, 3), dtype=np.uint8)
    arrays = dict(solid=ones, design=ones, passive_solid=np.zeros_like(ones), passive_void=np.zeros_like(ones))
    return write_geometry(directory, metadata, arrays)


def test_nonzero_origin_rectangular_cells_and_reversed_endpoints(tmp_path):
    forward = prepare_native_geometry(rectangular_geometry(tmp_path / "forward"))
    backward = prepare_native_geometry(rectangular_geometry(tmp_path / "backward", reverse=True))
    assert forward.geometry.geometry_id == backward.geometry.geometry_id
    np.testing.assert_array_equal(forward.arrays["connectivity"][0], [0, 1, 5, 4])
    np.testing.assert_array_equal(forward.arrays["coordinates_mm"][[0, 1, 5, 4]],
                                  [[10., -3.], [12., -3.], [12., -2.5], [10., -2.5]])
    assert forward.arrays["coordinates_mm"].shape == (12, 2)
    assert forward.arrays["connectivity"].shape == (6, 4)
    assert_affine_mean_and_work(forward)
    assert_affine_mean_and_work(backward)
    for name in ("input", "output"):
        np.testing.assert_array_equal(forward.arrays[name+"_vector"], backward.arrays[name+"_vector"])
        np.testing.assert_array_equal(forward.arrays[name+"_nodes"], backward.arrays[name+"_nodes"][::-1])
    assert forward.arrays["background_source_nodes"].size == 0


def test_off_grid_port_is_rejected_without_snapping(tmp_path):
    source = rectangular_geometry(tmp_path / "source", off_grid=True)
    with pytest.raises(GeometryError, match="endpoints must coincide with grid nodes"):
        prepare_native_geometry(source)


def test_bad_source_array_sha_is_rejected(tmp_path):
    source = PREVIOUS / "converted" / "gripper_native_fine" / "geometry.json"
    copied = tmp_path / "copied"
    shutil.copytree(source.parent, copied)
    payload = bytearray((copied / "geometry.npz").read_bytes())
    payload[-1] ^= 1
    (copied / "geometry.npz").write_bytes(payload)
    with pytest.raises(GeometryError, match="NPZ file sha256 mismatch"):
        prepare_native_geometry(copied / "geometry.json")


def test_existing_output_is_rejected_and_successful_snapshot_is_unchanged(tmp_path):
    mapping = prepare_native_geometry(rectangular_geometry(tmp_path / "source"))
    output = tmp_path / "mapped"
    descriptor = write_native_geometry_map(mapping, output)
    before = {path.relative_to(output): digest(path) for path in output.rglob("*") if path.is_file()}
    with pytest.raises(FileExistsError):
        write_native_geometry_map(mapping, output)
    after = {path.relative_to(output): digest(path) for path in output.rglob("*") if path.is_file()}
    assert after == before and descriptor.exists()
