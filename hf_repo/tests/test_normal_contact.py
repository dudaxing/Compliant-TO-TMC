from copy import deepcopy
import json
from pathlib import Path

import numpy as np
import pytest

from hf_eval.normal_contact import build_normal_contact, normal_task_from_spec
from hf_eval.tmc import TMCError


SPEC = json.loads((Path(__file__).resolve().parents[1]/"configs/hf4/validation_spec.json").read_text())


def task(h=.125, gamma=1e-6):
    return normal_task_from_spec(SPEC, gamma, h)


def test_exact_interfaces_body_identity_and_constraints():
    p = build_normal_contact(task())
    assert p.model.ne == 144
    assert len(p.model.coordinates) == 171
    assert [(p.body_ids == k).sum() for k in (0, 1, 2)] == [16, 64, 64]
    assert p.model.coordinates[p.regions["lower_interface_nodes"], 1].tolist() == [1]*9
    assert p.model.coordinates[p.regions["upper_interface_nodes"], 1].tolist() == [1.25]*9
    assert np.all(p.direction[p.model.free] == 0)
    assert np.count_nonzero(p.direction) == 9
    assert np.all(p.model.free % 2 == 1)
    assert set(np.flatnonzero(p.reaction_groups["bottom_platen"])) <= set(p.model.fixed_dofs)
    assert set(np.flatnonzero(p.reaction_groups["top_platen"])) <= set(p.model.fixed_dofs)
    assert np.all(p.model.solid == (p.body_ids != 0))


def test_refinement_preserves_geometry_material_and_physical_Lr():
    a, b, c = [build_normal_contact(t) for t in (task(), task(.0625), task(gamma=1e-7))]
    assert a.geometry_id == b.geometry_id == c.geometry_id
    assert a.mesh_id != b.mesh_id and a.mesh_id == c.mesh_id
    assert len({a.task_sha256, b.task_sha256, c.task_sha256}) == 3
    assert a.model.kr == b.model.kr == c.model.kr
    assert np.array_equal(np.repeat(np.repeat(a.body_ids.reshape(18, 8), 2, axis=0), 2, axis=1), b.body_ids.reshape(36,16))


def test_gap_measure_uses_physical_interfaces_and_new_weights():
    for h in (.125, .0625):
        p = build_normal_contact(task(h))
        u = np.zeros(p.model.ndof)
        u[2*np.array(p.regions["lower_interface_nodes"])+1] = .125
        u[2*np.array(p.regions["upper_interface_nodes"])+1] = -.0625
        assert .25 + p.gap_vector @ u == .0625
        assert sum(p.regions["interface_weights"]) == 1
        assert len(p.regions["interface_weights"]) == int(1/h)+1


@pytest.mark.parametrize("mutation", [
    lambda t: t.update(mesh_size_mm=.13),
    lambda t: t["geometry"].update(gap_mm=.26),
    lambda t: t["constraints"].update(ux="free"),
    lambda t: t["units"].update(length="m"),
    lambda t: t.update(targets_mm=[0,.25,.2]),
    lambda t: t.update(gamma=0),
    lambda t: t.update(mesh_size_mm=True),
    lambda t: t["material"].update(nu=.5),
    lambda t: t.update(workpiece={}),
])
def test_invalid_physics_rejected_without_snapping(mutation):
    t = task()
    mutation(t)
    with pytest.raises((TMCError, ValueError)):
        build_normal_contact(t)


def test_inputs_copied_and_material_primitive_is_actual_float_product():
    t = task()
    p = build_normal_contact(t)
    saved = deepcopy(p.task)
    t["geometry"]["gap_mm"] = 8
    assert p.task == saved
    assert p.reference_inputs["lam_v"] == p.model.lam[64]
    assert p.reference_inputs["mu_v"] == p.model.mu[64]
    with pytest.raises(ValueError):
        p.body_ids[0] = 3
