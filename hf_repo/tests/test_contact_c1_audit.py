"""Adversarial saved-evidence and staged-contact read-back checks; no FE solves."""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
import audit_contact_c1 as audit
from hf_eval.contact_c1 import build_problem
from hf_eval.split_state import SplitDisplacement


def inventory():
    targets = [0., .125, .21875, .25]
    entries = [dict(index=i, file=f"state_{i:03d}.npz", d=s, is_original_target=True,
                    original_target_displacement=s, bisection_depth=0) for i, s in enumerate(targets)]
    result = dict(status="success", target_reached=True, reached_displacement=targets[-1],
                  target_metrics=dict(d=targets[-1]), accepted_steps=deepcopy(entries))
    return dict(steps=entries), result, targets


def test_inventory_retains_inserted_states_and_full_target_coverage():
    index, result, targets = inventory()
    index["steps"].insert(1, dict(index=1, file="inserted.npz", d=.0625,
        is_original_target=False, original_target_displacement=.125, bisection_depth=1))
    for i, entry in enumerate(index["steps"]):
        entry["index"] = i
    result["accepted_steps"] = deepcopy(index["steps"])
    verified = audit.validate_inventory(index, result, targets, "uniform_precontact")
    assert verified["status"] == "pass" and verified["accepted_count"] == 5
    index["steps"].pop()
    result["accepted_steps"].pop()
    with pytest.raises(ValueError, match="claimed success"):
        audit.validate_inventory(index, result, targets, "uniform_precontact")


@pytest.mark.parametrize("field,value", [("d", .01), ("is_original_target", False),
    ("bisection_depth", 1), ("original_target_displacement", .25)])
def test_result_identity_cannot_disagree_with_index(field, value):
    index, result, targets = inventory()
    result["accepted_steps"][1][field] = value
    with pytest.raises(ValueError, match="index/result"):
        audit.validate_inventory(index, result, targets, "uniform_precontact")


def test_local_parameter_order_does_not_impose_global_drive_order():
    states = [dict(state_id="uniform_precontact:3", phase_id="uniform_precontact", parameter_s=.25,
                   physical_mean_drive=".25", status="pass", normal_force_raw="0"),
              dict(state_id="uniform_closed:0", phase_id="uniform_closed", parameter_s=0.,
                   physical_mean_drive=".25", status="pass", normal_force_raw="0"),
              dict(state_id="perturbation:0", phase_id="perturbation", parameter_s=0.,
                   physical_mean_drive=".375", status="not_pass", normal_force_raw="12"),
              dict(state_id="perturbation:1", phase_id="perturbation", parameter_s=.015625,
                   physical_mean_drive=".375", status="pass", normal_force_raw="13")]
    result = audit.classify_prefix(states)
    assert result["prefix_length"] == 2
    assert result["states"][1]["comparable"]
    assert result["states"][3]["local_valid"] and not result["states"][3]["comparable"]
    assert result["states"][2]["normal_force"] is result["states"][3]["normal_force"] is None


def test_duplicate_phase_qualified_identity_rejected():
    row = dict(state_id="perturbation:0", phase_id="perturbation", parameter_s=0., status="pass")
    with pytest.raises(ValueError, match="duplicate"):
        audit.classify_prefix([row, row])


def test_exact_geometry_detects_crossing_when_no_quad_node_is_inside():
    F = Fraction
    quad = [(F(0), F(3, 2)), (F(3, 2), F(0)), (F(2), F(1, 2)), (F(1, 2), F(2))]
    assert all(not (0 <= x <= 1 and 0 <= y <= 1) for x, y in quad)
    assert audit.exact_rectangle_area(quad, (F(0), F(1), F(0), F(1))) == F(1, 8)


def test_split_geometry_does_not_drop_sub_ulp_penetration():
    model = dict(coordinates=np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]]),
                 connectivity=np.array([[0, 1, 2, 3]]), solid=np.array([True]))
    lift = np.zeros(8)
    fluct = np.zeros(8)
    lift[1::2] = .25
    fluct[[5, 7]] = 2.**-60
    result = audit.exact_geometry(model, dict(u_lift=lift, u_fluctuation=fluct), [-4, 6, 1.25, 2.25])
    assert 1.25+2.**-60 == 1.25
    assert result["solid_overlap_exact"] == Fraction(1, 2**60)


def test_geometry_checks_medium_convexity_but_only_solid_overlap():
    model = dict(coordinates=np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]]),
                 connectivity=np.array([[0, 1, 2, 3]]), solid=np.array([False]))
    arrays = dict(u_lift=np.zeros(8), u_fluctuation=np.zeros(8))
    assert audit.exact_geometry(model, arrays, [0, 1, 0, 1])["solid_overlap_exact"] == 0
    model["connectivity"] = np.array([[0, 2, 1, 3]])
    assert not audit.exact_geometry(model, arrays, [0, 1, 0, 1])["all_cells_convex_positive"]


def test_component_near_zero_uses_declared_dimensional_floor():
    measured = audit.component_error(np.array([1e-25]), [Decimal(0)], Decimal("2.5e-19"))
    assert measured["denominator"] == Decimal("2.5e-19")
    assert measured["relative_error"] > Decimal("1e-9")


def test_original_protocol_thresholds_cannot_be_relaxed():
    protocol = audit.read_json(audit.PROTOCOL)
    audit.validate_protocol(protocol)
    protocol["audit"]["relative_precision_agreement"] = 1e-28
    with pytest.raises(ValueError, match="frozen audit threshold"):
        audit.validate_protocol(protocol)


def test_hash_paths_remain_relative_after_run_relocation(tmp_path):
    run = tmp_path/"experiment"/"run"
    helper = tmp_path/"repo"/"scripts"/"audit.py"
    bindings = {str(run/"metadata.json"): "a", str(helper): "b"}
    assert audit.portable_bindings(run, bindings) == {"metadata.json": "a", "../../repo/scripts/audit.py": "b"}


@pytest.mark.parametrize("name", ["../state.npz", "..\\state.npz", "/state.npz", "state.json"])
def test_evidence_filenames_cannot_escape_steps(tmp_path, name):
    with pytest.raises(ValueError):
        audit.safe_state_path(tmp_path, name)


def projection_fixture():
    source = dict(u_lift=np.array([0., .25, -0., .25]), u_fluctuation=np.array([0., 0., -0., -3e-32]))
    initial = deepcopy(source)
    initial["u_fluctuation"][3] = 0.
    old = dict(fixed_dofs=np.array([0, 1]))
    new = dict(fixed_dofs=np.array([0, 1, 3]), top_nodes=np.array([1]))
    receipt = dict(policy="explicit_new_fixed_projection_v1", new_fixed_dofs=[3],
        removed_fluctuation_mm=[-3e-32], maximum_projection_mm=3e-32, projection_limit_mm=1e-12,
        source_state_sha256=audit.state_identity(source), projected_state_sha256=audit.state_identity(initial),
        unchanged_components_bitwise=True)
    return source, initial, old, new, receipt


def test_explicit_activation_preserves_all_other_bits_and_raw_source():
    source, initial, old, new, receipt = projection_fixture()
    before = deepcopy(source)
    result = audit.verify_activation_projection(source, initial, old, new, receipt)
    assert result["positive_zero_new_fixed"]
    assert audit.bitwise_equal(source["u_fluctuation"], before["u_fluctuation"])
    assert np.signbit(initial["u_fluctuation"][2]) and not np.signbit(initial["u_fluctuation"][3])


@pytest.mark.parametrize("mutation", ["other_component", "negative_zero", "receipt", "limit"])
def test_activation_rejects_unauthorized_projection(mutation):
    source, initial, old, new, receipt = projection_fixture()
    if mutation == "other_component":
        initial["u_fluctuation"][2] = 0.
    elif mutation == "negative_zero":
        initial["u_fluctuation"][3] = -0.
    elif mutation == "receipt":
        receipt["removed_fluctuation_mm"] = [0.]
    else:
        receipt["projection_limit_mm"] = 1e-6
    with pytest.raises(ValueError, match="projection bytes/receipt"):
        audit.verify_activation_projection(source, initial, old, new, receipt)


def exported_problem(phase="uniform_precontact"):
    preliminary = build_problem("A0", .25, "uniform_precontact")
    ndof = preliminary.model.ndof
    initial = None
    if phase == "perturbation":
        origin = np.zeros(ndof)
        origin[1::2] = .25+.125*(1-preliminary.model.coordinates[:, 1])
        initial = SplitDisplacement(origin, np.zeros(ndof))
    p = build_problem("A0", .25, phase, initial_state=initial)
    model = {key: np.asarray(getattr(p.model, key)).copy() for key in
             ("coordinates", "connectivity", "lam", "mu", "kr", "fixed_dofs", "solid")}
    model.update({key: np.asarray(getattr(p, key)).copy() for key in
                  ("base", "direction", "lift_origin", "lift_shape", "top_nodes", "bottom_nodes",
                   "bottom_body_nodes", "measure_bottom_body", "measure_bottom_total")})
    model.update(F0=np.zeros(ndof), **{key: np.asarray(p.model.ops[key]).copy() for key in ("grad", "hessian", "weights")},
                 **{"group_"+key: value.copy() for key, value in p.reaction_groups.items()})
    protocol = audit.read_json(audit.PROTOCOL)
    metadata = dict(schema="contact_c1_stage_v1", phase_id=phase, kind="A0", h=.25,
                    force_scale_per_length=100., targets=audit.phase_targets(phase, protocol),
                    physical_mean_drive=dict(offset=.375 if phase == "perturbation" else 0., slope=0. if phase == "perturbation" else 1.))
    groups = audit.validate_model(model, metadata, dict(kind="A0", h=.25), protocol)
    return model, metadata, groups, protocol


@pytest.fixture(scope="module")
def zero_fixture():
    model, meta, groups, protocol = exported_problem()
    ndof = len(model["base"])
    vector = np.sin(np.arange(ndof)+.37)
    vector[model["fixed_dofs"]] = 0.
    vector /= np.linalg.norm(vector)
    arrays = dict(u_lift=model["lift_origin"].copy(), u_fluctuation=np.zeros(ndof), tangent_direction=vector)
    hp = audit.evaluate_split_prescribed_state(model, arrays["u_lift"], arrays["u_fluctuation"], 0.,
         model["base"], model["direction"], groups, 100., precision=80, tangent_direction=vector)
    for key, hpkey in (("internal_force", "internal_decimal"), ("material_internal_force", "material_internal_decimal"),
            ("regularization_internal_force", "regularization_internal_decimal"), ("production_tangent_action", "tangent_action_decimal"),
            ("material_tangent_action", "material_tangent_action_decimal"), ("regularization_tangent_action", "regularization_tangent_action_decimal"),
            ("J", "J_decimal")):
        arrays[key] = np.asarray(hp[hpkey], dtype=np.float64)
    entry = dict(index=0, d=0., is_original_target=True, original_target_displacement=0., bisection_depth=0)
    record = dict(relative_residual=0., residual_scale=1e-8*100.*1e-6,
                  state_sha256=audit.state_identity(arrays), u_lift=arrays["u_lift"].tolist(), u_fluctuation=arrays["u_fluctuation"].tolist())
    return model, arrays, entry, record, meta, groups, protocol


def test_rigid_precontact_has_no_contact_multiplier_but_all_hp_gates(zero_fixture):
    answer = audit.audit_state(*deepcopy(zero_fixture))
    assert answer["status"] == "pass"
    assert answer["normal_force_raw"] == "0"
    assert "top" not in answer["force_components"]["constraint_on_model_groups"]
    assert Decimal(answer["measurements"]["precontact_rigid_translation_error"]) == 0


def test_component_jv_cannot_be_replaced_by_correct_total(zero_fixture):
    args = list(deepcopy(zero_fixture))
    args[1]["material_tangent_action"][:] = 0.
    answer = audit.audit_state(*args)
    checks = {c["name"]: c for c in answer["checks"]}
    assert checks["production_vs_hp80_total_tangent"]["status"] == "pass"
    assert checks["production_vs_hp80_material_tangent"]["status"] == "not_pass"
    assert answer["status"] == "not_pass"


def test_parameter_zero_in_perturbation_is_compressed_physical_preload():
    model, metadata, _, _ = exported_problem("perturbation")
    physical = [audit.D(v) for v in model["lift_origin"]]
    drive = audit.physical_drive(model, physical, metadata, 0.)
    assert drive["body"] == drive["whole_bottom"] == Decimal(".375")
    assert model["lift_origin"][2*model["top_nodes"][0]+1] == .25


def test_split_state_identity_includes_signed_zero():
    arrays = dict(u_lift=np.array([0., 0.]), u_fluctuation=np.array([0., 0.]))
    before = audit.state_identity(arrays)
    arrays["u_lift"][0] = -0.
    assert audit.state_identity(arrays) != before


def test_precision_increase_is_explicit_and_preserves_80_digit_authority(zero_fixture):
    assert audit.validate_precision_amendment(None) == ((50, 80), None)
    pair, amendment = audit.validate_precision_amendment(audit.REPO/"configs/contact_c1_precision_r2.json")
    assert pair == (80, 120) and amendment["changes_acceptance_thresholds"] is False
    answer = audit.audit_state(*deepcopy(zero_fixture), verification_precision_pair=pair)
    assert answer["status"] == "pass"
    assert set(answer["precision_evidence_decimal"]) == {"80", "120"}
    checks = {c["name"] for c in answer["checks"]}
    assert "hp80_vs_hp120_material_force" in checks
    assert "hp50_vs_hp80_material_force" not in checks
    assert "hp80_relative_residual" in answer["measurements"]


def test_increased_precision_cannot_use_changed_threshold(monkeypatch):
    amendment = audit.read_json(audit.REPO/"configs/contact_c1_precision_r2.json")
    amendment["relative_precision_agreement"] = 1e-30
    monkeypatch.setattr(audit, "read_json", lambda path: amendment)
    with pytest.raises(ValueError, match="frozen gate retained"):
        audit.validate_precision_amendment(audit.REPO/"configs/contact_c1_precision_r2.json")


def test_aborted_run_preserves_completed_stage_prefix_without_claiming_success(tmp_path, monkeypatch):
    # Windows' default pytest temp volume may differ from the checkout. A
    # portable evidence bundle places its run and helpers on the same volume.
    original_repo = audit.REPO
    fixture_repo = tmp_path/"repo"
    copies = ["scripts/audit_contact_c1.py", "scripts/hf4_split_precision_reference.py", "scripts/hf2_precision_reference.py",
              "scripts/audit_contact_reference_a0.py", "configs/contact_c1_v1.json", "src/hf_eval/contact_c1.py",
              "src/hf_eval/split_affine.py", "src/hf_eval/split_kernel.py", "scripts/hf4_common.py", "scripts/run_contact_c1.py"]
    for relative in copies:
        path = fixture_repo/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((original_repo/relative).read_bytes())
    monkeypatch.setattr(audit, "REPO", fixture_repo)
    monkeypatch.setattr(audit, "PROTOCOL", fixture_repo/"configs/contact_c1_v1.json")
    monkeypatch.setattr(audit, "__file__", str(fixture_repo/"scripts/audit_contact_c1.py"))
    run = tmp_path/"run"
    stage = run/"stages/uniform_precontact"
    (stage/"steps").mkdir(parents=True)
    model, sm, _, protocol = exported_problem()
    np.savez(stage/"model.npz", **model)
    np.savez(stage/"initial_state.npz", u_lift=model["lift_origin"], u_fluctuation=np.zeros(len(model["base"])))
    sm.update(model_sha256=audit.sha(stage/"model.npz"), initial_state_sha256=audit.sha(stage/"initial_state.npz"),
              source_initialization={"type": "geometric_zero"})
    index, result, _ = inventory()
    for entry in index["steps"]:
        np.savez(stage/"steps"/entry["file"], token=np.zeros(1))
        entry["sha256"] = audit.sha(stage/"steps"/entry["file"])
    def save(path, data):
        path.write_text(json.dumps(data), encoding="utf-8")
    save(stage/"metadata.json", sm)
    save(stage/"result.json", result)
    save(stage/"steps/index.json", index)
    save(stage/"completion.json", dict(status="success", accepted_states=4,
        metadata_sha256=audit.sha(stage/"metadata.json"), result_sha256=audit.sha(stage/"result.json"),
        index_sha256=audit.sha(stage/"steps/index.json")))
    sources = ["src/hf_eval/contact_c1.py", "src/hf_eval/split_affine.py", "src/hf_eval/split_kernel.py",
               "scripts/hf4_common.py", "scripts/run_contact_c1.py"]
    save(run/"metadata.json", dict(schema="contact_c1_run_v1", kind="A0", h=.25, mode="uniform",
        planned_stages=["uniform_precontact", "uniform_closed"], protocol=protocol, protocol_sha256=audit.sha(audit.PROTOCOL),
        source_sha256={name: audit.sha(audit.REPO/name) for name in sources}))
    save(run/"stages/index.json", {"stages": [dict(phase_id="uniform_precontact", directory="stages/uniform_precontact", status="success"),
        dict(phase_id="uniform_closed", directory="stages/uniform_closed", status="running")]})
    def stub_state(model, arrays, entry, record, meta, groups, protocol, pair):
        return dict(state_id=f"{meta['phase_id']}:{entry['index']}", phase_id=meta["phase_id"], parameter_s=entry["d"],
                    physical_mean_drive=str(entry["d"]), status="pass", normal_force_raw="0")
    monkeypatch.setattr(audit, "audit_state", stub_state)
    answer = audit.audit(run)
    assert answer["status"] == "not_pass" and answer["prefix"]["prefix_length"] == 4
    assert answer["run_completion"]["present"] is False
    assert answer["run_completion"]["unfinished_stage_directories"] == ["stages/uniform_closed"]
    assert all(not Path(name).is_absolute() and "\\" not in name for name in answer["input_and_helper_sha256"])
