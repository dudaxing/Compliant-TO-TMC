from copy import deepcopy

import numpy as np
import pytest

from hf_eval.data import Geometry, GeometryError, load_geometry, write_geometry
from hf_eval.regions import active_nodes, element_connectivity, node_coordinates, port_vector, qualify_geometry, region_nodes


def rectangle(tmp_path, solid=None, dx=1.0, dy=1.0):
    if solid is None:
        solid = np.ones((2, 3), dtype=np.uint8)
    ny, nx = solid.shape
    metadata = {
        "schema_version": "hf-geometry-1.0", "case_family": "synthetic",
        "grid": {"shape_yx": [ny, nx], "origin_mm": [0, 0], "cell_size_mm": [dx, dy],
                 "extent_mm": [nx * dx, ny * dy], "axes": [[1, 0], [0, 1]],
                 "array_order": "C_yx_bottom_up", "value_location": "cell"},
        "thickness_mm": 2, "model_extent": {"kind": "full"},
        "region_tags": {
            "support": {"points_mm": [[0, 0], [0, ny * dy]], "components": [0, 1]},
            "input": {"points_mm": [[0, 0], [0, ny * dy]], "direction": [1, 0],
                      "averaging": "normalized_reference_arclength_trapezoid"},
            "output": {"points_mm": [[nx * dx, 0], [nx * dx, ny * dy]], "direction": [0, -1],
                       "averaging": "normalized_reference_arclength_trapezoid"},
        },
    }
    arrays = {"solid": solid, "design": np.ones_like(solid),
              "passive_solid": np.zeros_like(solid), "passive_void": np.zeros_like(solid)}
    return load_geometry(write_geometry(tmp_path, metadata, arrays))


def test_x_fast_bottom_up_nodes_and_positive_connectivity(tmp_path):
    geometry = rectangle(tmp_path, dx=2, dy=3)
    coords = node_coordinates(geometry)
    np.testing.assert_array_equal(coords[:5], [[0, 0], [2, 0], [4, 0], [6, 0], [0, 3]])
    conn = element_connectivity(geometry)
    np.testing.assert_array_equal(conn[0], [0, 1, 5, 4])
    np.testing.assert_array_equal(conn[-1], [6, 7, 11, 10])
    xy = coords[conn]
    area = 0.5 * np.sum(xy[:, :, 0] * np.roll(xy[:, :, 1], -1, axis=1) - xy[:, :, 1] * np.roll(xy[:, :, 0], -1, axis=1), axis=1)
    np.testing.assert_allclose(area, 6.0)


def test_nonzero_origin_asymmetric_cell_marker(tmp_path):
    geometry = rectangle(tmp_path, solid=np.array([[1, 0, 0], [1, 1, 0]], dtype=np.uint8), dx=2, dy=3)
    metadata = deepcopy(geometry.metadata)
    metadata["grid"]["origin_mm"] = [10, 20]
    for tag in metadata["region_tags"].values():
        tag["points_mm"] = (np.array(tag["points_mm"]) + [10, 20]).tolist()
    moved = load_geometry(write_geometry(tmp_path / "moved", metadata, geometry.arrays))
    conn = element_connectivity(moved)[moved.solid.ravel().astype(bool)]
    centroids = node_coordinates(moved)[conn].mean(axis=1)
    np.testing.assert_array_equal(centroids, [[11, 21.5], [11, 24.5], [13, 24.5]])
    assert active_nodes(moved).sum() == 8


def test_port_weights_reference_average_and_virtual_work(tmp_path):
    geometry = rectangle(tmp_path)
    vector, nodes, weights = port_vector(geometry, geometry.metadata["region_tags"]["input"])
    np.testing.assert_array_equal(nodes, [0, 4, 8])
    np.testing.assert_array_equal(weights, [0.25, 0.5, 0.25])
    coords = node_coordinates(geometry)
    displacement = np.zeros(2 * len(coords))
    displacement[0::2] = 3 + 2 * coords[:, 1]
    assert vector @ displacement == 5.0
    force = 7.0 * vector
    assert force @ displacement == 7.0 * (vector @ displacement)
    assert np.linalg.matrix_rank(11 * np.outer(vector, vector)) == 1
    reverse = deepcopy(geometry.metadata["region_tags"]["input"])
    reverse["points_mm"].reverse()
    np.testing.assert_array_equal(port_vector(geometry, reverse)[0], vector)


def test_refinement_rebuilds_weights_for_same_physical_segment(tmp_path):
    coarse = rectangle(tmp_path / "coarse")
    fine = rectangle(tmp_path / "fine", solid=np.ones((4, 6), dtype=np.uint8), dx=0.5, dy=0.5)
    bc, _, wc = port_vector(coarse, coarse.metadata["region_tags"]["input"])
    bf, _, wf = port_vector(fine, coarse.metadata["region_tags"]["input"])
    np.testing.assert_array_equal(wc, [0.25, 0.5, 0.25])
    np.testing.assert_array_equal(wf, [0.125, 0.25, 0.25, 0.25, 0.125])
    for geometry, vector in ((coarse, bc), (fine, bf)):
        u = np.zeros(len(vector))
        u[0::2] = 4 + node_coordinates(geometry)[:, 1]
        assert vector @ u == 5.0
    # Separate input grids retain distinct authority identities; production
    # refinement references coarse geometry_id plus its own discretization_id.
    assert coarse.geometry_id != fine.geometry_id


@pytest.mark.parametrize("points", [
    [[0, 0], [0, 1.1]], [[0, 0], [1, 1]], [[0, 0], [0, 0]],
    [[-1, 0], [0, 0]], [[0, 0], [0, 3]], [[0, 0], [float("nan"), 1]],
])
def test_region_rejects_snapping_diagonal_and_outside(tmp_path, points):
    geometry = rectangle(tmp_path)
    with pytest.raises(GeometryError):
        region_nodes(geometry, {"points_mm": points})


def test_region_ulp_tolerance_is_not_geometric_snapping(tmp_path):
    geometry = rectangle(tmp_path, solid=np.ones((3, 4), dtype=np.uint8), dx=0.1, dy=0.1)
    nodes = region_nodes(geometry, {"points_mm": [[0, 0], [0.3, 0]]})
    np.testing.assert_array_equal(nodes, [0, 1, 2, 3])
    with pytest.raises(GeometryError, match="coincide"):
        region_nodes(geometry, {"points_mm": [[0, 0], [0.3000001, 0]]})


def test_qualification_pending_thresholds_and_volume_failure(tmp_path):
    geometry = rectangle(tmp_path, dx=2, dy=3)
    result = qualify_geometry(geometry)
    assert result["status"] == "pending"
    assert result["measurements"]["solid_area_mm2"] == 36
    assert result["measurements"]["solid_volume_mm3"] == 72
    assert result["measurements"]["components_4"] == 1
    assert result["measurements"]["common_support_port_component_ids_4"] == [1]
    assert result["checks"]["support_attachment"]["status"] == "pass"
    assert qualify_geometry(geometry, {"max_design_volume_fraction": 0.9})["status"] == "fail"
    assert qualify_geometry(geometry, {"max_design_volume_fraction": 1.0, "min_feature_mm": 0.1})["status"] == "pending"


def test_design_fraction_excludes_passive_regions(tmp_path):
    geometry = rectangle(tmp_path, solid=np.array([[1, 1, 0], [1, 1, 0]], dtype=np.uint8))
    arrays = {name: array.copy() for name, array in geometry.arrays.items()}
    arrays["design"][:, 0] = 0
    arrays["passive_solid"][:, 0] = 1
    arrays["design"][:, 2] = 0
    arrays["passive_void"][:, 2] = 1
    qualified = load_geometry(write_geometry(tmp_path / "partition", geometry.metadata, arrays))
    measurements = qualify_geometry(qualified)["measurements"]
    assert measurements["design_volume_fraction"] == 1
    assert measurements["envelope_volume_fraction"] == pytest.approx(2 / 3)
    assert measurements["design_solid_cells"] == 2


def test_diagonal_only_contact_cannot_pass_shared_edge_body_check(tmp_path):
    geometry = rectangle(tmp_path, solid=np.eye(2, dtype=np.uint8))
    result = qualify_geometry(geometry)
    assert result["status"] == "fail"
    assert result["measurements"]["components_4"] == 2
    assert result["measurements"]["components_8"] == 1
    assert result["measurements"]["local_diagonal_only_patterns"] == 1


def test_ports_do_not_silently_drop_unattached_nodes(tmp_path):
    solid = np.ones((2, 3), dtype=np.uint8)
    solid[1, 0] = 0
    geometry = rectangle(tmp_path, solid=solid)
    vector, nodes, weights = port_vector(geometry, geometry.metadata["region_tags"]["input"])
    np.testing.assert_array_equal(weights, [0.25, 0.5, 0.25])
    assert not active_nodes(geometry)[nodes[-1]]
    assert vector[2 * nodes[-1]] == 0.25
    result = qualify_geometry(geometry)
    assert result["checks"]["input_attachment"]["status"] == "fail"
    assert result["regions"]["support"]["attached_node_count"] == 2
    assert result["checks"]["support_attachment"]["status"] == "pass"


def test_empty_geometry_and_unsupported_criteria_are_explicit(tmp_path):
    geometry = rectangle(tmp_path, solid=np.zeros((2, 3), dtype=np.uint8))
    assert not active_nodes(geometry).any()
    assert qualify_geometry(geometry)["status"] == "fail"
    with pytest.raises(GeometryError, match="Unsupported qualification"):
        qualify_geometry(geometry, {"secret_threshold": 1})
