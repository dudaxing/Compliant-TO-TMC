"""Input binding tests; the builder supplies ordinary arrays, never a solve.

The audit itself imports no production module. Deliberate coordinated errors
in the FE coefficients and its scalar reference must fail against the frozen
specification even when those two corrupted records agree with one another.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from hf_eval.normal_contact import build_normal_contact, normal_task_from_spec


_repo = Path(__file__).resolve().parents[1]
_path = _repo/"scripts/hf4_input_audit.py"
_spec = importlib.util.spec_from_file_location("hf4_input_audit_under_test", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
validate = _module.validate_inputs
SPEC = json.loads((_repo/"configs/hf4/validation_spec.json").read_text())


def ordinary_inputs(gamma_index=0, mesh_index=0):
    spec = deepcopy(SPEC)
    task = normal_task_from_spec(spec, spec["gammas"][gamma_index], spec["mesh_sizes_mm"][mesh_index])
    p = build_normal_contact(task)
    m = p.model
    arrays = dict(coordinates=m.coordinates, connectivity=m.connectivity, body_ids=p.body_ids,
        lam=m.lam, mu=m.mu, kr=np.array(m.kr), hx=np.array(m.hx), hy=np.array(m.hy),
        thickness=np.array(m.thickness), solid=m.solid, fixed_dofs=m.fixed_dofs,
        base=p.base, direction=p.direction, gap_vector=p.gap_vector, **m.ops,
        **{"group_"+name:vector for name, vector in p.reaction_groups.items()})
    meta = dict(spec=deepcopy(spec), task=deepcopy(task), task_sha256=p.task_sha256,
        geometry_id=p.geometry_id, mesh_id=p.mesh_id, gamma_index=gamma_index, mesh_index=mesh_index,
        settings=deepcopy(spec["solver"]), reference_inputs=deepcopy(p.reference_inputs), regions=deepcopy(p.regions),
        force_scale_per_length=task["material"]["E_MPa"]*task["geometry"]["thickness_mm"],
        source_files={"src/hf_eval/normal_contact.py":"a"*64, "scripts/development.py":"b"*64})
    return spec, meta, {key: np.array(value, copy=True) for key, value in arrays.items()}


@pytest.fixture
def saved():
    return ordinary_inputs()


@pytest.mark.parametrize("gamma_index,mesh_index", [(0,0), (0,1), (1,0), (1,1)])
def test_all_four_frozen_combinations_have_exact_input_binding(gamma_index, mesh_index):
    spec, meta, arrays = ordinary_inputs(gamma_index, mesh_index)
    result = validate(spec, meta, arrays)
    assert result["status"] == "pass"
    assert all(check["status"] == "pass" for check in result["checks"])
    assert result["element_count"] == (144 if mesh_index == 0 else 576)
    assert result["node_count"] == (171 if mesh_index == 0 else 629)
    assert result["source_binding"] == "not_requested"
    json.dumps(result, allow_nan=False)


def test_correlated_fe_and_scalar_reference_material_error_cannot_pass(saved):
    spec, meta, arrays = saved
    arrays["lam"] *= 2
    arrays["mu"] *= 2
    for name in ("lam_s", "mu_s", "lam_v", "mu_v"):
        meta["reference_inputs"][name] *= 2
    with pytest.raises(ValueError, match="values_lam"):
        validate(spec, meta, arrays)


@pytest.mark.parametrize("field", ["base", "direction", "group_top_platen", "gap_vector"])
def test_missing_full_vector_is_rejected(saved, field):
    spec, meta, arrays = saved
    del arrays[field]
    with pytest.raises(ValueError):
        validate(spec, meta, arrays)


@pytest.mark.parametrize("field", ["lam", "base", "group_bottom_platen", "weights"])
def test_shortened_array_is_rejected_before_elementwise_comparison(saved, field):
    spec, meta, arrays = saved
    arrays[field] = arrays[field][:-1]
    with pytest.raises(ValueError, match="shape_"+field):
        validate(spec, meta, arrays)


@pytest.mark.parametrize("mutation", [
    lambda s,m,a: m.update(gamma_index=True),
    lambda s,m,a: m.update(mesh_index=-1),
    lambda s,m,a: m["task"].update(gamma=1e-7),
    lambda s,m,a: m["settings"].update(tolerance=1e-6),
    lambda s,m,a: m.update(force_scale_per_length=2.0),
    lambda s,m,a: m["regions"]["upper_interface_nodes"].reverse(),
    lambda s,m,a: m["regions"].update(force_multiplier=2),
    lambda s,m,a: m["regions"]["interface_weights"].__setitem__(0, 1.0),
    lambda s,m,a: m["reference_inputs"].update(gap=0.5),
    lambda s,m,a: m.update(geometry_id="0"*64),
    lambda s,m,a: m.update(mesh_id="0"*64),
    lambda s,m,a: m.update(task_sha256="0"*64),
    lambda s,m,a: a["coordinates"].__setitem__((1, 0), 0.2),
    lambda s,m,a: a["connectivity"].__setitem__((0, 1), 3),
    lambda s,m,a: a["body_ids"].__setitem__(0, 0),
    lambda s,m,a: a["solid"].__setitem__(0, False),
    lambda s,m,a: a["fixed_dofs"].__setitem__(1, 0),
    lambda s,m,a: a["direction"].__setitem__(1, -1),
    lambda s,m,a: a["group_top_platen"].__imul__(-1),
    lambda s,m,a: a["gap_vector"].__imul__(2),
    lambda s,m,a: a["weights"].__imul__(2),
    lambda s,m,a: a["grad"].__setitem__((0, 0, 0), 0),
    lambda s,m,a: a["hessian"].__setitem__((0, 1, 0), 0),
    lambda s,m,a: a["points"].__setitem__((1, 0), 1),
    lambda s,m,a: a["kr"].__imul__(1e-6),
])
def test_wrong_mapping_units_order_and_operators_are_rejected(saved, mutation):
    spec, meta, arrays = saved
    mutation(spec, meta, arrays)
    with pytest.raises(ValueError):
        validate(spec, meta, arrays)


def test_runtime_source_binding_is_exact_and_development_scripts_are_separate(saved):
    spec, meta, arrays = saved
    freeze = dict(files={"src/hf_eval/normal_contact.py":"a"*64, "scripts/development.py":"c"*64})
    result = validate(spec, meta, arrays, freeze)
    assert result["source_binding"] == "checked"
    meta["source_files"]["src/hf_eval/normal_contact.py"] = "d"*64
    with pytest.raises(ValueError, match="runtime_source_freeze"):
        validate(spec, meta, arrays, freeze)


def test_source_omission_is_not_treated_as_vacuous_success(saved):
    spec, meta, arrays = saved
    with pytest.raises(ValueError, match="source_runtime_nonempty"):
        validate(spec, meta, arrays, {"files":{"scripts/only.py":"a"*64}})
    with pytest.raises(ValueError, match="runtime_source_freeze"):
        validate(spec, meta, arrays, {"files":{"src/hf_eval/missing.py":"a"*64}})


def test_nonzero_force_control_load_is_not_permitted(saved):
    spec, meta, arrays = saved
    arrays["F0"] = np.ones_like(arrays["base"])
    with pytest.raises(ValueError, match="values_F0"):
        validate(spec, meta, arrays)


def test_validation_keeps_saved_primitives_and_metadata_unchanged(saved):
    spec, meta, arrays = saved
    before_spec, before_meta = deepcopy(spec), deepcopy(meta)
    before_arrays = {key: value.copy() for key, value in arrays.items()}
    validate(spec, meta, arrays)
    assert spec == before_spec and meta == before_meta
    for key in arrays:
        np.testing.assert_array_equal(arrays[key], before_arrays[key])
