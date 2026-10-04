"""Analytic cached nodal-force observations; no kernel, assembly or solve."""
import numpy as np
import pytest

from hf_eval.workpiece_nodal import observe_workpiece_nodal_forces


BASE_FORCES = np.array([[1., 2.], [3., -1.], [-2., 4.], [0., -3.],
                        [5., 6.], [-4., 1.], [2., -2.], [-1., 3.], [4., -5.]])
LOCAL_GROUPS = {"physical_only": [0, 1, 2, 3, 5], "cut_only": [7],
                "physical_and_cut": [6, 8], "interior": [4]}


def rectangle(on_body, *, sparse=False, shift=(0., 0.)):
    """Four literal Q1 cells; unused global nodes carry distracting forces."""
    nodes = np.array([19, 2, 29, 7, 17, 5, 13, 23, 11] if sparse else list(range(9)),
                     dtype=np.int64)
    xy = np.full((int(nodes.max())+1, 2), 1000.)
    xy[nodes] = np.array([[0., 0.], [2., 0.], [4., 0.], [0., 1.], [2., 1.],
                         [4., 1.], [0., 2.], [2., 2.], [4., 2.]]) + shift
    conn = nodes[np.array([[0, 1, 4, 3], [1, 2, 5, 4], [3, 4, 7, 6], [4, 5, 8, 7]])]
    dofs = (2*nodes[:, None]+[0, 1]).ravel()
    model = dict(coordinates=xy, connectivity=conn, workpiece_nodes=nodes,
                 workpiece_cells=np.arange(4, dtype=np.int64), workpiece_dofs=dofs,
                 fixed_dofs=dofs.copy())
    force = {}
    for name, fraction in (("total", 1.), ("material", .25), ("regularization", .75)):
        values = np.full((len(xy), 2), 7e30)
        values[nodes] = -fraction*on_body
        force["global_"+name+"_force"] = values.ravel()
    force["support_reaction"] = force["global_total_force"].copy()
    return model, force, nodes


def edge_set(edges):
    return {tuple(sorted(map(int, edge))) for edge in edges}


def test_half_rectangle_groups_force_sign_and_reference_moment():
    model, forces, nodes = rectangle(BASE_FORCES)
    observed = observe_workpiece_nodal_forces(model, forces, symmetry_y_mm=2.)
    np.testing.assert_array_equal(observed["node_ids"], nodes)
    np.testing.assert_array_equal(observed["coordinates_mm"], model["coordinates"][nodes])
    np.testing.assert_array_equal(observed["moment_origin_mm"], [2., 1.])
    closed = {(0, 1), (1, 2), (2, 5), (5, 8), (7, 8), (6, 7), (3, 6), (0, 3)}
    cut = {(6, 7), (7, 8)}
    assert edge_set(observed["edges"]["closed"]) == closed
    assert edge_set(observed["edges"]["cut"]) == cut
    assert edge_set(observed["edges"]["physical"]) == closed-cut
    mask_sum = np.zeros(9, dtype=int)
    group_answers = {"physical_only": ([-2., 3.], 14.), "cut_only": ([-1., 3.], 1.),
                     "physical_and_cut": ([6., -7.], -12.), "interior": ([5., 6.], 0.)}
    for name, positions in LOCAL_GROUPS.items():
        mask = np.zeros(9, dtype=bool)
        mask[positions] = True
        np.testing.assert_array_equal(observed["masks"][name], mask)
        mask_sum += observed["masks"][name]
        group = observed["summary"]["groups"][name]
        assert group["node_count"] == len(positions)
        force, moment = group_answers[name]
        for component, fraction in (("total", 1.), ("material", .25), ("regularization", .75)):
            np.testing.assert_array_equal(group["force_on_body_N"][component], fraction*np.array(force))
            assert group["moment_about_origin_Nmm"][component] == fraction*moment
    np.testing.assert_array_equal(mask_sum, np.ones(9))
    for component, fraction in (("total", 1.), ("material", .25), ("regularization", .75)):
        np.testing.assert_array_equal(observed["forces_on_body_N"][component], fraction*BASE_FORCES)
        np.testing.assert_array_equal(observed["summary"]["force_on_lower_body_N"][component], [8.*fraction, 5.*fraction])
        assert observed["summary"]["moment_about_origin_Nmm"][component] == 3.*fraction
    np.testing.assert_array_equal(observed["summary"]["holding_reaction_on_model_N"], [-8., -5.])
    with pytest.raises(ValueError):
        observe_workpiece_nodal_forces(dict(model, fixed_dofs=model["fixed_dofs"][:-1]),
                                      forces, symmetry_y_mm=2.)


def test_tiny_signed_values_fsum_cancellation_and_independent_total():
    tiny = 2.**-200
    nodal = np.zeros((9, 2))
    nodal[0, 0], nodal[1, 0], nodal[2, 0] = 1., tiny, -1.
    nodal[6, 1], nodal[8, 1] = -tiny, tiny
    model, forces, nodes = rectangle(nodal)
    # These are three independent saved vectors: total must never be reconstructed.
    forces["global_material_force"][2*nodes[1]] = 0.
    forces["global_regularization_force"][2*nodes[1]] = 0.
    observed = observe_workpiece_nodal_forces(model, forces, symmetry_y_mm=2.)
    np.testing.assert_array_equal(observed["forces_on_body_N"]["total"], nodal)
    np.testing.assert_array_equal(observed["summary"]["force_on_lower_body_N"]["total"], [tiny, 0.])
    assert observed["summary"]["moment_about_origin_Nmm"]["total"] == 5.*tiny
    assert observed["forces_on_body_N"]["material"][1, 0] == 0.
    assert observed["forces_on_body_N"]["regularization"][1, 0] == 0.
    np.testing.assert_array_equal(observed["summary"]["force_on_lower_body_N"]["material"], [0., 0.])
    np.testing.assert_array_equal(observed["summary"]["force_on_lower_body_N"]["regularization"], [0., 0.])
    assert observed["summary"]["moment_about_origin_Nmm"]["material"] == tiny
    assert observed["summary"]["moment_about_origin_Nmm"]["regularization"] == 3.*tiny
    np.testing.assert_array_equal(observed["summary"]["holding_reaction_on_model_N"], [-tiny, 0.])


def test_sparse_body_ids_translation_and_explicit_moment_origin():
    model, forces, nodes = rectangle(BASE_FORCES, sparse=True, shift=(8., 16.))
    observed = observe_workpiece_nodal_forces(model, forces, symmetry_y_mm=18.)
    np.testing.assert_array_equal(observed["node_ids"], nodes)
    np.testing.assert_array_equal(observed["coordinates_mm"], model["coordinates"][nodes])
    np.testing.assert_array_equal(observed["moment_origin_mm"], [10., 17.])
    for name, positions in LOCAL_GROUPS.items():
        np.testing.assert_array_equal(observed["node_ids"][observed["masks"][name]], nodes[positions])
    assert edge_set(observed["edges"]["cut"]) == {tuple(sorted(nodes[[6, 7]])), tuple(sorted(nodes[[7, 8]]))}
    np.testing.assert_array_equal(observed["summary"]["force_on_lower_body_N"]["total"], [8., 5.])
    assert observed["summary"]["moment_about_origin_Nmm"]["total"] == 3.
    moved_origin = observe_workpiece_nodal_forces(model, forces, symmetry_y_mm=18., moment_origin_mm=[11., 15.])
    np.testing.assert_array_equal(moved_origin["moment_origin_mm"], [11., 15.])
    # tau(new) = tau(old) - dx*Fy + dy*Fx = 3 - 1*5 - 2*8.
    assert moved_origin["summary"]["moment_about_origin_Nmm"]["total"] == -18.


@pytest.mark.parametrize("sign", [1., -1.])
def test_pure_couple_has_zero_force_and_signed_origin_independent_torque(sign):
    nodal = np.zeros((9, 2))
    nodal[3, 1], nodal[5, 1] = -3.*sign, 3.*sign
    model, forces, _ = rectangle(nodal)
    observed = observe_workpiece_nodal_forces(model, forces, symmetry_y_mm=2., moment_origin_mm=[17., 23.])
    for component, fraction in (("total", 1.), ("material", .25), ("regularization", .75)):
        np.testing.assert_array_equal(observed["summary"]["force_on_lower_body_N"][component], [0., 0.])
        assert observed["summary"]["moment_about_origin_Nmm"][component] == 12.*sign*fraction
