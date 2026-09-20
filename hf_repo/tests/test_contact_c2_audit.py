"""Independent C2 contracts and adversarial storage fixtures; no FE solves."""
from copy import deepcopy
from decimal import Decimal
import gzip
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import audit_contact_c2 as audit
from hf_eval.contact_c2 import build_problem


def protocol():
    p = audit.read_json(audit.REPO/"configs/contact_c1_v1.json")
    p.update(schema="contact_c2_uniform_diagnostic_v1",
             cases={name: dict(h_mm=h, padding_mm=padding, outer_bottom_policy=policy)
                    for name, (h, padding, policy) in audit.CASES.items()})
    p["audit"]["precisions"] = [80, 120]
    return p


def model_fixture(case="outer_free"):
    problem = build_problem(case)  # Construction only; independent audit rebuilds all arrays.
    p = protocol()
    h, padding, policy = audit.CASES[case]
    meta = dict(schema="contact_c2_stage_v1", phase_id="uniform_tmc", kind="TMC", h=h,
                padding=padding, outer_bottom_policy=policy, targets=audit.TARGETS,
                force_scale_per_length=100., physical_mean_drive=dict(offset=0., slope=1.))
    run_meta = dict(case_id=case, case=p["cases"][case], h=h)
    return deepcopy(problem.arrays), meta, run_meta, p


@pytest.mark.parametrize("case", list(audit.CASES))
def test_independent_geometry_bc_material_and_operator_reconstruction(case):
    model, meta, run_meta, p = model_fixture(case)
    audit.validate_protocol(p)
    groups = audit.validate_model(model, meta, run_meta, p)
    free = np.setdiff1d(np.arange(len(model["base"])), model["fixed_dofs"])
    assert set(groups) == {"top", "bottom"}
    assert not np.any(groups["bottom"][free])
    assert not np.any(model["direction"][free])


@pytest.mark.parametrize("key", ["fixed_dofs", "coordinates", "lam", "mu", "kr", "grad", "hessian",
                                 "weights", "measure_bottom_total", "direction", "group_bottom"])
def test_model_primitive_tampering_is_rejected(key):
    model, meta, run_meta, p = model_fixture()
    if key == "fixed_dofs":
        model[key] = model[key][:-1]
    else:
        model[key].flat[0] = np.nextafter(float(model[key].flat[0]), np.inf)
    with pytest.raises(ValueError):
        audit.validate_model(model, meta, run_meta, p)


def test_outer_free_retains_lift_on_free_bottom_without_prescribing_it():
    model, meta, run_meta, p = model_fixture()
    audit.validate_model(model, meta, run_meta, p)
    outer = np.setdiff1d(model["bottom_nodes"], model["bottom_body_nodes"])
    dofs = 2*outer+1
    assert np.all(model["lift_shape"][dofs] == 1.)
    assert not np.any(model["direction"][dofs])
    assert not np.intersect1d(dofs, model["fixed_dofs"]).size
    assert not np.any(model["group_bottom"][dofs])


@pytest.fixture
def manufactured_state(monkeypatch):
    """Synthetic force/Jv reference isolates policy gates, not mechanics accuracy."""
    model, meta, run_meta, p = model_fixture()
    groups = audit.validate_model(model, meta, run_meta, p)
    ndof, ne = len(model["base"]), len(model["connectivity"])
    vector = np.sin(np.arange(ndof)+.37)
    vector[model["fixed_dofs"]] = 0.
    vector /= np.linalg.norm(vector)
    lift, fluctuation = np.zeros(ndof), np.zeros(ndof)
    fluctuation[1] = .01  # Free exterior bottom node; body mean remains zero.
    arrays = dict(u_lift=lift, u_fluctuation=fluctuation, tangent_direction=vector,
                  internal_force=np.zeros(ndof), material_internal_force=np.zeros(ndof),
                  regularization_internal_force=np.zeros(ndof), production_tangent_action=vector.copy(),
                  material_tangent_action=vector.copy(), regularization_tangent_action=np.zeros(ndof),
                  J=np.ones((ne, 9)))
    zero = Decimal(0)
    hp = dict(internal_decimal=[zero]*ndof, material_internal_decimal=[zero]*ndof,
              regularization_internal_decimal=[zero]*ndof, tangent_action_decimal=list(map(audit.D, vector)),
              material_tangent_action_decimal=list(map(audit.D, vector)), regularization_tangent_action_decimal=[zero]*ndof,
              J_decimal=[[Decimal(1)]*9 for _ in range(ne)], constraint_decimal=[zero]*len(model["fixed_dofs"]),
              physical_displacement_decimal=list(map(audit.D, fluctuation)),
              force_scale_decimal=Decimal("1e-12"), relative_residual_decimal=zero,
              relative_constraint_decimal=zero, relative_force_balance_decimal=zero,
              minimum_J_decimal=Decimal(1), minimum_J_solid_decimal=Decimal(1), minimum_J_medium_decimal=Decimal(1),
              group_reactions_decimal={key:zero for key in groups},
              group_material_reactions_decimal={key:zero for key in groups},
              group_regularization_reactions_decimal={key:zero for key in groups},
              drive_force_decimal=zero, drive_material_force_decimal=zero, drive_regularization_force_decimal=zero)
    monkeypatch.setattr(audit, "evaluate_split_prescribed_state", lambda *_args, **_kwargs: deepcopy(hp))
    entry = dict(index=0, d=0., is_original_target=True, original_target_displacement=0., bisection_depth=0)
    record = dict(relative_residual=0., residual_scale=1e-8*100.*1e-6,
                  state_sha256=audit.state_identity(arrays), u_lift=lift.tolist(), u_fluctuation=fluctuation.tolist())
    return model, arrays, entry, record, meta, groups, p


def test_outer_free_whole_mean_is_observed_without_false_prescribed_gate(manufactured_state):
    row = audit.audit_state(*manufactured_state)
    assert row["status"] == "pass"
    drive = row["measurements"]["physical_drive"]
    assert Decimal(drive["body_error"]) == 0 and Decimal(drive["whole_bottom_error"]) > 0
    assert drive["whole_bottom_mean_is_prescribed"] is False
    assert "whole_bottom_mean_drive_mapping_error_mm" not in {check["name"] for check in row["checks"]}
    assert row["verification_precision_pair"] == [80, 120]
    assert set(row["precision_evidence_decimal"]) == {"80", "120"}
    measurements = row["measurements"]
    assert measurements["top_weak_normal_reactions"] == measurements["top_normal_multipliers"]
    assert measurements["minimum_weak_normal_reaction"] == measurements["minimum_normal_multiplier"]


def test_driven_policy_still_requires_whole_bottom_mean(manufactured_state):
    args = list(manufactured_state)
    args[4] = {**args[4], "outer_bottom_policy": "driven"}
    row = audit.audit_state(*args)
    checks = {check["name"]:check for check in row["checks"]}
    assert checks["body_mean_drive_mapping_error_mm"]["status"] == "pass"
    assert checks["whole_bottom_mean_drive_mapping_error_mm"]["status"] == "not_pass"
    assert row["status"] == "not_pass"


def test_component_tangent_is_checked_even_when_total_is_correct(manufactured_state):
    manufactured_state[1]["material_tangent_action"][:] = 0.
    row = audit.audit_state(*manufactured_state)
    checks = {check["name"]:check for check in row["checks"]}
    assert checks["production_vs_hp80_total_tangent"]["status"] == "pass"
    assert checks["production_vs_hp80_material_tangent"]["status"] == "not_pass"


def test_old_precision_pair_is_rejected_by_c2_state_evaluator(manufactured_state):
    with pytest.raises(ValueError, match="precision pair"):
        audit.audit_state(*manufactured_state, verification_precision_pair=(50,80))


@pytest.mark.parametrize("mutation", ["precision", "threshold", "material", "case", "solver"])
def test_protocol_cannot_relax_or_blend_factors(mutation):
    p = protocol()
    if mutation == "precision":
        p["audit"]["precisions"] = [50, 80]
    elif mutation == "threshold":
        p["audit"]["relative_precision_agreement"] = 1e-20
    elif mutation == "material":
        p["material"]["Lref_mm"] = 7
    elif mutation == "case":
        p["cases"]["outer_free"]["padding_mm"] = 2.5
    else:
        p["solver"]["tolerance"] = 1e-6
    with pytest.raises(ValueError):
        audit.validate_protocol(p)


def write_gzip(path, value):
    with gzip.open(path, "wt", encoding="utf-8") as stream:
        json.dump(value, stream, allow_nan=False)


@pytest.fixture
def controller(tmp_path):
    stage = tmp_path/"stage"
    (stage/"steps").mkdir(parents=True)
    zero = np.zeros(4)
    model = dict(base=zero.copy(), direction=np.array([0., 1., 0., 0.]),
                 lift_origin=zero.copy(), lift_shape=np.array([0., 1., 0., 0.]))
    groups = dict(top=np.array([0., 0., 0., 1.]), bottom=np.array([0., 1., 0., 0.]))
    initial = dict(u_lift=zero.copy(), u_fluctuation=zero.copy())
    np.savez(stage/"initial_state.npz", **initial)
    entries, records = [], []
    for i, d in enumerate(audit.TARGETS):
        arrays = dict(u_lift=d*model["lift_shape"], u_fluctuation=zero.copy())
        record = dict(d=d, is_original_target=True, original_target_displacement=d, bisection_depth=0,
                      u_lift=arrays["u_lift"].tolist(), u_fluctuation=arrays["u_fluctuation"].tolist(),
                      state_sha256=audit.state_identity(arrays))
        name = f"state_{i:03d}.record.json.gz"
        write_gzip(stage/"steps"/name, record)
        entries.append(dict(index=i, file=f"state_{i:03d}.npz", record_file=name,
                            record_sha256=audit.sha(stage/"steps"/name),
                            **{k:record[k] for k in ("d", "is_original_target", "original_target_displacement", "bisection_depth")}))
        records.append(record)
    last = records[-1]
    full = dict(status="success", target_reached=True, reached_displacement=.5,
                accepted_steps=records, last_accepted_state=deepcopy(last), target_metrics=deepcopy(last), failure=None,
                initial_state_provided=True, initial_state_sha256=audit.state_identity(initial),
                initial_u_lift=zero.tolist(), initial_u_fluctuation=zero.tolist(),
                lift_scheme="affine_geometric_origin_v1", force_scale_per_length=100., target_displacement=.5,
                reaction_groups={k:v.tolist() for k,v in groups.items()},
                **{k:v.tolist() for k,v in model.items()},
                u_lift=last["u_lift"], u_fluctuation=last["u_fluctuation"], state_sha256=last["state_sha256"])
    write_gzip(stage/"controller_full.json.gz", full)
    digest = audit.sha(stage/"controller_full.json.gz")
    compact = dict(status="success", target_reached=True, reached_displacement=.5,
                   accepted_states=len(entries), controller_full_sha256=digest)
    completion = dict(accepted_states=len(entries), controller_full_sha256=digest)
    return stage, compact, completion, dict(steps=entries), model, groups, full


def test_gzip_full_controller_and_record_files_are_losslessly_bound(controller):
    stage, compact, completion, index, model, groups, expected = controller
    bindings = {}
    full, inventory = audit.load_controller(stage, compact, completion, index, model, groups, bindings)
    assert full == expected and inventory["status"] == "pass"
    assert len(bindings) == 8  # Full gzip plus seven record gzip files.


@pytest.mark.parametrize("mutation", ["compact_hash", "completion_hash", "compact_count", "scalar",
                                    "record_bytes", "record_signed_zero", "record_escape", "unindexed_record",
                                    "initial_identity", "final_identity"])
def test_controller_and_per_record_corruptions_are_rejected(controller, mutation):
    stage, compact, completion, index, model, groups, full = controller
    if mutation == "compact_hash":
        compact["controller_full_sha256"] = "0"*64
    elif mutation == "completion_hash":
        completion["controller_full_sha256"] = "0"*64
    elif mutation == "compact_count":
        compact["accepted_states"] -= 1
    elif mutation == "scalar":
        compact["reached_displacement"] = .375
    elif mutation in ("record_bytes", "record_signed_zero"):
        record = deepcopy(full["accepted_steps"][2])
        record["u_fluctuation"][0] = -0.0 if mutation.endswith("zero") else .01
        path = stage/"steps"/index["steps"][2]["record_file"]
        write_gzip(path, record)
        index["steps"][2]["record_sha256"] = audit.sha(path)
    elif mutation == "record_escape":
        index["steps"][0]["record_file"] = "../controller_full.json.gz"
    elif mutation == "unindexed_record":
        write_gzip(stage/"steps/unindexed.record.json.gz", {})
    else:
        full["initial_state_sha256" if mutation == "initial_identity" else "state_sha256"] = "0"*64
        write_gzip(stage/"controller_full.json.gz", full)
        compact["controller_full_sha256"] = completion["controller_full_sha256"] = audit.sha(stage/"controller_full.json.gz")
    with pytest.raises(ValueError):
        audit.load_controller(stage, compact, completion, index, model, groups, {})


def test_failed_full_controller_keeps_inventory_without_success(controller):
    stage, compact, completion, index, model, groups, full = controller
    full.update(status="failed", target_reached=False, target_metrics=None, failure=dict(code="time_budget"))
    compact.update(status="failed", target_reached=False)
    write_gzip(stage/"controller_full.json.gz", full)
    compact["controller_full_sha256"] = completion["controller_full_sha256"] = audit.sha(stage/"controller_full.json.gz")
    _, inventory = audit.load_controller(stage, compact, completion, index, model, groups, {})
    assert inventory["complete"] and inventory["status"] == "not_pass"


@pytest.mark.parametrize("failed", [False, True])
def test_streamed_state_details_and_failed_run_cannot_be_upgraded(tmp_path, monkeypatch, failed):
    run = tmp_path/"run"
    run.mkdir()
    source = tmp_path/"bound_input.json"
    source.write_text("{}")
    states = [dict(state_id=f"uniform_tmc:{i}", phase_id="uniform_tmc", index=i, parameter_s=float(i),
                   status="pass", normal_force_raw="0", checks=[dict(status="pass")],
                   measurements=dict(marker="full detail"), precision_evidence_decimal={"80":{}, "120":{}})
              for i in range(2)]
    data = dict(entries=[dict(index=i,d=float(i)) for i in range(2)],
                full=dict(accepted_steps=[{},{}]), paths=[source,source], model={}, groups={}, stage_metadata={},
                protocol={}, completed=True, top_result=dict(status="failed" if failed else "success"),
                inventory=dict(status="not_pass" if failed else "pass"),
                metadata=dict(case_id="outer_free", case={}, h=.125, source_sha256={}))
    def load(_run, _protocol, bindings):
        bindings[str(source)] = audit.sha(source)
        return data
    monkeypatch.setattr(audit, "load_run", load)
    monkeypatch.setattr(audit, "read_npz", lambda _path: {})
    monkeypatch.setattr(audit, "audit_state", lambda _m, _a, entry, *_rest: deepcopy(states[entry["index"]]))
    result = audit.audit(run, run/"audit.json", tmp_path/"protocol.json")
    assert result["status"] == ("not_pass" if failed else "pass")
    assert result["prefix"]["prefix_length"] == 2
    assert result["measurement_semantics"] == audit.MEASUREMENT_SEMANTICS
    assert "not a verified unilateral contact" in result["measurement_semantics"]["top_weak_normal_reactions"]
    assert len(result["detail_output_sha256"]) == 2
    assert "measurements" not in result["states"][0]
    for compact in result["states"]:
        path = run/compact["detail_file"]
        assert audit.sha(path) == compact["detail_sha256"] == result["detail_output_sha256"][compact["detail_file"]]
        assert audit.read_json(path)["measurements"]["marker"] == "full detail"
    with pytest.raises(ValueError, match="already exists"):
        audit.audit(run, run/"audit.json", tmp_path/"protocol.json")


@pytest.fixture
def full_tree(tmp_path, monkeypatch):
    """Full portable failed-run chain, with one geometrical zero record."""
    original_repo = audit.REPO
    repo = tmp_path/"tree/hf_repo"
    sources = ["src/hf_eval/contact_c2.py", "src/hf_eval/split_affine.py", "src/hf_eval/split_kernel.py",
               "src/hf_eval/split_state.py", "scripts/run_contact_c2.py", "scripts/run_contact_c1_r2.py",
               "scripts/hf4_common.py"]
    helpers = ["scripts/"+name for name in ("audit_contact_c2.py", "audit_contact_c1.py",
               "audit_contact_reference_a0.py", "hf4_split_precision_reference.py", "hf2_precision_reference.py")]
    for name in sources+helpers+["configs/contact_c1_v1.json"]:
        target = repo/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original_repo/name, target)
    model, meta, run_meta, p = model_fixture()
    gate = repo.parent/"diagnostics/admission.json"
    gate.parent.mkdir()
    admission_input = gate.parent/"saved_field_check.json"
    admission_input.write_text('{"status":"pass","observed_cases":4}')
    gate.write_text(json.dumps(dict(status="pass", input_sha256_from_workspace_root={
        "diagnostics/saved_field_check.json": audit.sha(admission_input)})))
    p["saved_field_admission"] = dict(path="../../diagnostics/admission.json", sha256=audit.sha(gate))
    p["implementation_sha256"] = {name:audit.sha(repo/name) for name in sources+helpers}
    protocol_path = repo/"configs/contact_c2_v1.json"
    protocol_path.write_text(json.dumps(p))
    run = repo.parent/"results/outer_free"
    stage = run/"stages/uniform_tmc"
    (stage/"steps").mkdir(parents=True)
    def write(path, value):
        path.write_text(json.dumps(audit.plain(value)))
    ndof = len(model["base"])
    initial = dict(u_lift=np.zeros(ndof), u_fluctuation=np.zeros(ndof))
    np.savez(stage/"initial_state.npz", **initial)
    np.savez(stage/"model.npz", **model)
    np.savez(stage/"steps/state_000.npz", **initial)
    record = dict(d=0., is_original_target=True, original_target_displacement=0., bisection_depth=0,
                  **{k:v.tolist() for k,v in initial.items()}, state_sha256=audit.state_identity(initial))
    write_gzip(stage/"steps/state_000.record.json.gz", record)
    entry = {k:record[k] for k in ("d", "is_original_target", "original_target_displacement", "bisection_depth")}
    entry.update(index=0, file="state_000.npz", sha256=audit.sha(stage/"steps/state_000.npz"),
                 record_file="state_000.record.json.gz", record_sha256=audit.sha(stage/"steps/state_000.record.json.gz"))
    groups = {k[6:]:v for k,v in model.items() if k.startswith("group_")}
    full = dict(status="failed", target_reached=False, reached_displacement=0.,
                target_metrics=None, accepted_steps=[record], last_accepted_state=record,
                failure=dict(code="manufactured_stop"), initial_state_provided=True,
                initial_state_sha256=audit.state_identity(initial),
                initial_u_lift=initial["u_lift"].tolist(), initial_u_fluctuation=initial["u_fluctuation"].tolist(),
                lift_scheme="affine_geometric_origin_v1", force_scale_per_length=100., target_displacement=.5,
                reaction_groups={k:v.tolist() for k,v in groups.items()},
                **{k:model[k].tolist() for k in ("base", "direction", "lift_origin", "lift_shape")},
                **{k:v.tolist() for k,v in initial.items()}, state_sha256=audit.state_identity(initial))
    write_gzip(stage/"controller_full.json.gz", full)
    digest = audit.sha(stage/"controller_full.json.gz")
    write(stage/"result.json", dict(status="failed", target_reached=False, reached_displacement=0.,
                                   accepted_states=1, controller_full_sha256=digest))
    meta.update(source_initialization=dict(type="geometric_zero"), model_sha256=audit.sha(stage/"model.npz"),
                initial_state_sha256=audit.sha(stage/"initial_state.npz"))
    write(stage/"metadata.json", meta)
    write(stage/"steps/index.json", dict(steps=[entry]))
    write(stage/"completion.json", dict(status="failed", accepted_states=1, controller_full_sha256=digest,
        metadata_sha256=audit.sha(stage/"metadata.json"), result_sha256=audit.sha(stage/"result.json"),
        index_sha256=audit.sha(stage/"steps/index.json")))
    write(run/"metadata.json", dict(schema="contact_c2_run_v1", kind="TMC", mode="uniform", **run_meta,
          protocol=p, protocol_sha256=audit.sha(protocol_path), protocol_path="Z:/missing/old/protocol.json",
          source_sha256={name:audit.sha(repo/name) for name in sources}))
    stages = [dict(phase_id="uniform_tmc", directory="stages/uniform_tmc", status="failed")]
    write(run/"stages/index.json", dict(stages=stages))
    write(run/"result.json", dict(status="failed", stages=stages))
    write(run/"completion.json", dict(status="failed", metadata_sha256=audit.sha(run/"metadata.json"),
          result_sha256=audit.sha(run/"result.json"), index_sha256=audit.sha(run/"stages/index.json")))
    monkeypatch.setattr(audit, "REPO", repo)
    return repo, run, protocol_path


def test_full_storage_chain_is_bound_and_relocatable_without_historical_protocol_path(full_tree, tmp_path, monkeypatch):
    repo, run, protocol_path = full_tree
    bindings = {}
    data = audit.load_run(run, protocol_path, bindings)
    assert data["inventory"]["accepted_count"] == 1
    assert data["inventory"]["status"] == "not_pass" and data["completed"]
    assert str(run/"stages/uniform_tmc/controller_full.json.gz") in bindings
    assert str(run/"stages/uniform_tmc/steps/state_000.record.json.gz") in bindings
    assert str(repo/"scripts/audit_contact_c2.py") in bindings
    assert str(repo.parent/"diagnostics/saved_field_check.json") in bindings
    moved = tmp_path/"relocated"
    shutil.copytree(repo.parent, moved)
    monkeypatch.setattr(audit, "REPO", moved/"hf_repo")
    monkeypatch.chdir(tmp_path)
    second = {}
    restored = audit.load_run(moved/"results/outer_free", moved/"hf_repo/configs/contact_c2_v1.json", second)
    assert restored["inventory"] == data["inventory"]
    assert audit.portable_bindings(run, bindings) == audit.portable_bindings(moved/"results/outer_free", second)


@pytest.mark.parametrize("name", ["metadata.json", "result.json", "stages/index.json",
    "stages/uniform_tmc/model.npz", "stages/uniform_tmc/initial_state.npz",
    "stages/uniform_tmc/controller_full.json.gz", "stages/uniform_tmc/steps/state_000.npz"])
def test_run_chain_rejects_changed_bytes(full_tree, name):
    _, run, protocol_path = full_tree
    with (run/name).open("ab") as stream:
        stream.write(b" \n")
    with pytest.raises(ValueError, match="hash mismatch"):
        audit.load_run(run, protocol_path, {})


def test_hard_interruption_is_explicitly_outside_full_inventory_certification(full_tree):
    _, run, protocol_path = full_tree
    (run/"completion.json").unlink()
    (run/"stages/uniform_tmc/completion.json").unlink()
    with pytest.raises(ValueError, match="standalone NPZ/record data remain readable"):
        audit.load_run(run, protocol_path, {})


@pytest.mark.parametrize("manifest", ["implementation", "admission"])
@pytest.mark.parametrize("mutation", ["changed_bytes", "false_hash", "escape", "absolute", "empty", "not_dict"])
def test_frozen_source_and_admission_input_manifests_reject_tampering(full_tree, manifest, mutation):
    repo, run, protocol_path = full_tree
    p = audit.read_json(protocol_path)
    gate = repo.parent/"diagnostics/admission.json"
    admission = audit.read_json(gate)
    if manifest == "implementation":
        document, key, root = p, "implementation_sha256", repo
    else:
        document, key, root = admission, "input_sha256_from_workspace_root", repo.parent
    hashes = document[key]
    name = next(iter(hashes))
    if mutation == "changed_bytes":
        with (root/name).open("ab") as stream:
            stream.write(b"\n# changed source evidence\n")
    elif mutation == "false_hash":
        hashes[name] = "0"*64
    elif mutation in ("escape", "absolute"):
        hashes[("../" if mutation == "escape" else "C:/")+name] = hashes.pop(name)
    elif mutation == "empty":
        document[key] = {}
    else:
        document[key] = []
    gate.write_text(json.dumps(admission))
    p["saved_field_admission"]["sha256"] = audit.sha(gate)
    protocol_path.write_text(json.dumps(p))
    with pytest.raises(ValueError, match="hash mismatch|path|hash dictionary"):
        audit.load_run(run, protocol_path, {})
