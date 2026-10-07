"""Freeze a fresh x71 side18 port-projection reference card only after complete production passes.

This program copies source bytes and hashes stored files. It never starts a
reference, constructs a model, or evaluates a force/tangent/geometry routine.
"""
from pathlib import Path
from hashlib import sha256
from math import isfinite
import argparse
import json
import shutil

RSS = 8*1024**3
CORE_PIN = "b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5"
AUDIT_PIN = "82c650d57ca5e2ccb07791b28bf2f9be743d025430d70a276f0cc9e7cba68028"
COUNTER_PIN = "a751fe07a682ff89c88b16d8d69325b1990d45c26114b8715414116580737ed9"
ORIGINAL_COUNTER_PIN = "b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3"
COUNTER_SCHEMA = "shift-complete-attempt-counter-recovered-invalid-J-1.1"
ACCOUNTING_EVIDENCE = dict(saved_report="saved_report.json",saved_accounting="saved_accounting.json",
    peer_review="peer_review.json",independent_chronology="independent_chronology.json",
    preflight_report="preflight_report.json",preflight_helper="preflight_helper.py",
    validation_helper="validation_helper.py",source_author_note="source_author_note.json",
    source_delta="source_delta.diff",source_author_helper="source_author_helper.py")
LAUNCHER_PIN = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
MATH = ("audit_native_mean.py","audit_native_force.py","hf2_precision_reference.py",
        "hf4_split_precision_reference.py","audit_native_workpiece_cycle.py","run_split_average_demo.py")
read = lambda p:json.loads(p.read_text(encoding="utf-8"))
sha = lambda p:sha256(p.read_bytes()).hexdigest()


BASELINE = "3305fe0c3a640bf22e0f89ea4386a41bdef96aa4"
CONTROL = "lf_data_preparation/native_workpiece_001/right_margin4_cycle_001"
PREPARATION = "lf_data_preparation/native_workpiece_001/right_margin4_preparation_001"
COMPARISON = "lf_data_preparation/native_workpiece_001/right_margin_cycle_001"
PROOF_CONTROL = "lf_data_preparation/native_workpiece_001/enlarged_square_projection_001"
ALIAS = "gripper_coarse_square_x71_side18_right_margin4"
RAW_FIELDS = {"grad", "hessian", "weights", "points", "kr", "hx", "hy", "thickness", "k_out", "force_scale_per_length"}
COUNTS = dict(cells=3360,nodes=3485,dofs=6970,solid_cells=1086,medium_cells=2274,solid_incident_nodes=1337,fixed_dofs=452,free_dofs=6518)
INITIAL_GUESS = "port_projection"
PREDICTOR_INITIALIZATION = dict(displacement_mode=INITIAL_GUESS, applied_dw=False, applied_dR=True,
    port_adjustment="distributed normalized free-port weights", predictor_LU_role="reaction increment estimator",
    linear_residual_scope="Actual computed KKT solution; not the applied displacement seed.")
TARGETS = [0.,.25,.5,.65,.75,.8,.85,.9,.95,1.,1.05,1.1,1.15,1.2,1.15,1.1,1.,.9,.8,.75,.65,.5,.25,0.]
BODY = dict(kind="fixed_rigid",shape="square",center_mm=[71.,40.],side_mm=18.,fixed_components=[0,1])
PLACEMENT = dict(body_box_mm=[62.,80.,31.,40.],right_outer_boundary_mm=84.,
    right_medium_margin_mm=4.,workpiece_touches_analysis_boundary=False)


def verify_complete_production(root, stage, bind):
    """Bind only the new preparation/production and the current comparison baseline."""
    assert stage == root/CONTROL/"run_001"
    control = stage.parent
    assert not (control/"stop_requested.txt").exists() and not (stage/"stop_requested.txt").exists()
    paths = [stage/n for n in ("input_inventory.json","execution_receipt.json","source_freeze.json")]
    inventory,receipt,freeze = map(read,paths)
    protocol_file,launch_file = control/"production_protocol.json",control/"production_launch.json"
    protocol,launch = read(protocol_file),read(launch_file)
    row = inventory["case"]
    result_file = stage/row["result_directory"]/"result.json"
    result = read(result_file)
    assert inventory["baseline_commit"] == receipt["baseline_commit"] == BASELINE
    assert row["alias"] == ALIAS and row["source_alias"] == "gripper_canonical"
    assert (row["elements"],row["dofs"],row["fixed_DOFs"],row["free_DOFs"]) == (3360,6970,452,6518)
    assert inventory["schema_version"] == "native-workpiece-cycle-input-inventory-1.0"
    assert freeze["schema_version"] == "right-margin-cycle-source-freeze-1.0"
    assert inventory["source_count"] == len(freeze["sources"]) == 27
    assert len({Path(p).name for p in freeze["sources"]}) == 27
    assert len([p for p in freeze["sources"] if p.startswith("hf_repo/src/hf_eval/")]) == 25
    assert freeze["sources"][CONTROL+"/author/execute_shift_pose.py"] == "57d18bfea972c09db4c0866bdee3413088342327e32d3926be9eaa1bdbab466a"
    assert freeze["sources"][CONTROL+"/author/prepare_shift_pose.py"] == "fbb3e1975a7054599eb7d9fde5bf771805a698fe54015ac3d934e43cba2262ac"
    assert receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
    assert receipt["status"] == launch["status"] == "pass" and result["status"] == "success"
    assert launch["exit_code"] == 0 and launch["invocations"] == receipt["invocations"] == 1
    assert launch["stop_reason"] is None and launch["all_bindings_unchanged"] is True
    assert launch["protocol_sha256"] == sha(protocol_file) and launch["bindings"] == protocol["bindings"]
    assert protocol["phases"]["production"]["helper_seconds"] == receipt["seconds_limit"] == 4500
    assert protocol["phases"]["production"]["outer_seconds"] == launch["outer_seconds"] == 4560
    assert 0 <= launch["elapsed_seconds"] <= 4560 and 0 <= receipt["elapsed_seconds"] <= 4500
    assert launch["sampled_RSS_limit_bytes"] == receipt["sampled_RSS_limit_bytes"] == protocol["sampled_RSS_bytes"] == RSS
    assert 0 <= launch["peak_sampled_tree_RSS_bytes"] <= RSS and 0 <= receipt["sampled_peak_RSS_bytes"] <= RSS
    assert receipt["force_hook_restored"] is receipt["tangent_hook_restored"] is True
    assert receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
    assert receipt["input_inventory_sha256"] == sha(paths[0])
    assert receipt["source_freeze_sha256"] == inventory["source_freeze_sha256"] == sha(paths[2])
    assert receipt["result_sha256"] == sha(result_file)
    assert inventory["settings"] == result["settings"] and result["settings"]["time_limit_seconds"] == 4500.
    baseline_inventory = read(root/COMPARISON/"run_001/input_inventory.json")
    expected_settings = dict(baseline_inventory["settings"],time_limit_seconds=4500.)
    assert inventory["settings"] == expected_settings and inventory["gates"] == baseline_inventory["gates"]
    assert inventory["tangent_execution"] == result["tangent_execution"] == dict(mode="chunk256",element_block_size=256,global_selector_scope="full_batch")
    assert inventory["initial_guess"] == result["initial_guess"] == INITIAL_GUESS
    assert inventory["predictor_initialization"] == PREDICTOR_INITIALIZATION
    predictors = [r for r in result["path_diagnostics"]["linear_solve_diagnostics"] if r["phase"] == "predictor"]
    assert receipt["predictor_initialization"] == dict(PREDICTOR_INITIALIZATION,actual_predictor_LU_records=len(predictors),actual_predictor_flags_match=True)
    assert all(r["displacement_mode"] == INITIAL_GUESS and r["applied_dw"] is False and r["applied_dR"] is True for r in predictors)
    assert result["targets_mm"] == row["targets_mm"] == TARGETS and result["task_target_mm"] == 1.2
    assert all(result[k] is True for k in ("production_converged","target_reached","path_completed","task_target_executed","loading_peak_reached","unload_endpoint_reached","lift_origin_zero","lift_shape_zero"))
    assert result["failure"] is None and result["save_force_calls"] == result["save_tangent_calls"] == 0
    assert result["call_counts"] == receipt["call_counts"] and result["call_counts"]["HP_calls"] == result["call_counts"]["JIT_calls"] == 0
    assert all(result[k] is False for k in ("equilibrium_qualified","independent_HP_qualified","HF_qualified"))
    states = result["states"]
    assert len(states) == result["accepted_states"] == receipt["accepted_states"] >= len(TARGETS)
    assert states[0]["d"] == states[-1]["d"] == 0. and states[0]["leg"] == "origin"
    assert [r["d"] for r in states if r["is_original_target"]] == TARGETS
    assert [r["state_sha256"] for r in states] == receipt["state_sha256"]
    task = read(root/row["task_file"])
    baseline_task = read(root/COMPARISON/"run_001/task.json")
    descriptive = {"task_id","purpose","parameter_origin","description"}
    expected_task = dict(baseline_task,geometry=task["geometry"],background_symmetry=dict(points_mm=[[0.,40.],[84.,40.]],components=[1]))
    assert {k:v for k,v in task.items() if k not in descriptive} == {k:v for k,v in expected_task.items() if k not in descriptive}
    assert task["workpiece"] == BODY and task["path"]["targets_mm"] == TARGETS
    assert task["third_medium"]["gamma"] == 1e-6 and task["regularization"]["alpha"] == 1e-6
    assert task["regularization"]["length_mm"] == 80. and task["material"]["E_MPa"] == 1.
    comparison = inventory["model_comparison"]
    assert comparison["total_fields"] == 27 and comparison["parameter_case"] == "right_medium_domain_margin2_to4mm"
    assert comparison["parent_physical_subdomain_byte_exact"] is True
    assert len(comparison["actual_changed_fields"]) == 17 and len(comparison["unchanged_fields"]) == 10
    assert comparison["actual_changed_fields"] == row["expected_model_changed_fields"]
    assert comparison["unchanged_fields"] == row["unchanged_model_fields"] == sorted(RAW_FIELDS)
    assert receipt["model_arrays_compared"] == 27 and receipt["declared_workpiece_model_arrays_equal"] is True
    assert receipt["model_comparison"] == comparison and receipt["declared_workpiece_model_sha256"] == row["workpiece_model_sha256"]
    assert row["comparison_model_file"] == COMPARISON+"/run_001/result/model/model.npz"
    prep = root/PREPARATION
    prep_protocol,prep_launch,prep_receipt = [read(prep/p) for p in ("preparation_protocol.json","prepare_launch.json","run_001/preparation_receipt.json")]
    assert prep_launch["status"] == prep_receipt["status"] == "pass" and prep_launch["exit_code"] == 0
    assert prep_launch["invocations"] == prep_receipt["invocations"] == 1 and prep_launch["stop_reason"] is None
    assert prep_launch["all_bindings_unchanged"] is prep_receipt["inputs_and_sources_unchanged"] is True
    assert prep_launch["protocol_sha256"] == sha(prep/"preparation_protocol.json")
    assert prep_receipt["model_constructions"] == prep_receipt["model_constructions_completed"] == prep_receipt["model_writes"] == 1
    assert all(prep_receipt[k] == 0 for k in ("force_calls","tangent_calls","solver_calls","HP_calls","JIT_calls","LF_imports"))
    assert prep_protocol["phases"]["prepare"]["helper_seconds"] == prep_receipt["helper_seconds"] == 120
    assert prep_protocol["phases"]["prepare"]["outer_seconds"] == prep_launch["outer_seconds"] == 150
    assert prep_launch["argv"][1] == "-B" and prep_launch["argv"][2:] == prep_protocol["phases"]["prepare"]["argv"]
    assert prep_protocol["sampled_RSS_bytes"] == prep_receipt["sampled_RSS_limit_bytes"] == prep_launch["sampled_RSS_limit_bytes"] == RSS
    assert 0 <= prep_receipt["elapsed_seconds"] <= 120 and 0 <= prep_launch["elapsed_seconds"] <= 150
    assert 0 <= prep_receipt["peak_sampled_helper_RSS_bytes"] <= RSS and 0 <= prep_launch["peak_sampled_tree_RSS_bytes"] <= RSS
    assert sha(root/row["task_file"]) == sha(prep/"run_001/task.json")
    assert sha(root/row["workpiece_model_file"]) == prep_receipt["model_sha256"]
    assert prep_receipt["final_resource_check_passed"] is True
    assert prep_launch["bindings"] == prep_protocol["bindings"]
    assert prep_receipt["geometry_constructions"] == prep_receipt["geometry_constructions_completed"] == prep_receipt["geometry_writes"] == prep_receipt["direction_writes"] == 1
    assert prep_receipt["actual_counts"] == result["counts"] == COUNTS
    for name,pin in prep_receipt["outputs"].items(): bind(prep/"run_001"/name,pin)
    prepared_comparison = read(prep/"run_001/model_comparison.json")
    assert prepared_comparison == prep_receipt["model_comparison"]
    assert prepared_comparison["total_fields"] == len(prepared_comparison["fields"]) == 27
    assert prepared_comparison["raw_equal_fields"] == comparison["unchanged_fields"]
    assert prepared_comparison["physically_mapped_fields"] == sorted(set(prepared_comparison["fields"])-RAW_FIELDS)
    assert prepared_comparison["parent_physical_subdomain_byte_exact"] is True
    assert all(v["physical_comparison"] == "pass" for v in prepared_comparison["fields"].values())
    assert sorted(n for n,v in prepared_comparison["fields"].items() if not v["raw_equal"]) == comparison["actual_changed_fields"]
    assert comparison["preparation_comparison_file"] == PREPARATION+"/run_001/model_comparison.json"
    assert comparison["preparation_comparison_sha256"] == sha(prep/"run_001/model_comparison.json")
    assert comparison["physical_mapping_file"] == PREPARATION+"/run_001/mapping.npz"
    assert comparison["physical_mapping_sha256"] == sha(prep/"run_001/mapping.npz")
    pins = dict(protocol["bindings"])
    pins.update(inventory["input_bindings"]); pins.update(freeze["sources"]); pins.update(prep_protocol["bindings"])
    for path in [*paths,protocol_file,launch_file,*[p for p in result_file.parent.rglob("*") if p.is_file()],*[p for p in stage.glob("first_*_range_input/*") if p.is_file()]]:
        pins[path.relative_to(root).as_posix()] = sha(path)
    for name,pin in pins.items(): bind(root/name,pin)
    for name,pin in freeze["sources"].items(): bind(stage/"sources"/Path(name).name,pin)
    return inventory,receipt,freeze,result

def verify_padding_arrays(np, old, new, old_meta, new_meta):
    """Compare saved physical subdomains; stored indices use the new row strides."""
    assert set(old) == set(new) and len(new) == 27
    assert all(old[k].dtype == new[k].dtype for k in old)
    assert new["coordinates"].shape == (3485, 2) and new["connectivity"].shape == (3360, 4)
    assert new["edofs"].shape == (3360, 8) and new["b_in"].shape == new["b_out"].shape == (6970,)
    assert all(new[k].shape == (3360,) for k in ("solid", "lam", "mu", "gamma"))
    cell_map = (np.arange(40, dtype=np.int64)[:, None] * 84 + np.arange(82, dtype=np.int64)).ravel()
    node_map = (np.arange(41, dtype=np.int64)[:, None] * 85 + np.arange(83, dtype=np.int64)).ravel()
    dof_map = (2 * node_map[:, None] + np.arange(2, dtype=np.int64)).ravel()
    added_cells = (np.arange(40, dtype=np.int64)[:, None] * 84 + np.array([82, 83])).ravel()
    added_dofs = np.setdiff1d(np.arange(6970), dof_map)
    same = lambda a, b: a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
    for name in RAW_FIELDS:
        assert same(new[name], old[name]), name
    assert new["thickness"] == old["thickness"] == 20.
    assert same(new["coordinates"][node_map], old["coordinates"])
    old_tip = np.flatnonzero(np.all(old["coordinates"] == [80.,30.], axis=1))
    new_tip = np.flatnonzero(np.all(new["coordinates"] == [80.,30.], axis=1))
    assert old_tip.tolist() == [2570] and new_tip.tolist() == [2630]
    assert node_map[old_tip].tolist() == new_tip.tolist()
    assert same(new["connectivity"][cell_map], node_map[old["connectivity"]])
    assert same(new["edofs"][cell_map], dof_map[old["edofs"]])
    for name in ("solid", "lam", "mu", "gamma"):
        assert same(new[name][cell_map], old[name]), name
    assert not new["solid"][added_cells].any()
    for name in ("lam", "mu", "gamma"):
        assert np.all(new[name][added_cells] == old[name][~old["solid"]][0]), name
    for name in ("solid_nodes", "workpiece_nodes"):
        assert same(new[name], node_map[old[name]]), name
    for name in ("solid_dofs", "workpiece_dofs", "workpiece_background_symmetry_overlap_dofs"):
        assert same(new[name], dof_map[old[name]]), name
    assert same(new["workpiece_cells"], cell_map[old["workpiece_cells"]])
    extra_top_uy = 2 * np.array([40 * 85 + 83, 40 * 85 + 84], dtype=np.int64) + 1
    assert extra_top_uy.tolist() == [6967,6969]
    assert same(new["fixed_dofs"], np.union1d(dof_map[old["fixed_dofs"]], extra_top_uy))
    assert same(new["free_dofs"], np.setdiff1d(np.arange(6970, dtype=np.int64), new["fixed_dofs"]))
    assert len(new["fixed_dofs"]) == 452 and len(new["free_dofs"]) == 6518
    for name in ("b_in", "b_out"):
        assert same(new[name][dof_map], old[name]) and not new[name][added_dofs].any(), name
    for name in ("support", "entity_symmetry"):
        a, b = old_meta["region_metadata"][name], new_meta["region_metadata"][name]
        for key in a:
            if key in ("selected_nodes", "attached_nodes", "excluded_unattached_nodes"):
                assert b[key] == node_map[np.asarray(a[key], dtype=np.int64)].tolist()
            elif key == "dofs":
                assert b[key] == dof_map[np.asarray(a[key], dtype=np.int64)].tolist()
            else:
                assert b[key] == a[key]
    for name in ("input", "output"):
        a, b = old_meta["region_metadata"]["ports"][name], new_meta["region_metadata"]["ports"][name]
        assert b == {**a, "nodes": node_map[a["nodes"]].tolist(), "nonzero_dofs": dof_map[a["nonzero_dofs"]].tolist()}
    body = new_meta["region_metadata"]["workpiece"]
    assert (body["selected_cells"], body["incident_nodes"], body["fixed_dofs"]) == (162, 190, 380)
    assert len(new["workpiece_background_symmetry_overlap_dofs"]) == 19
    fields = {k: dict(old_shape=list(old[k].shape), new_shape=list(new[k].shape), dtype=new[k].dtype.name,
        old_array_sha256=sha256(old[k].tobytes()).hexdigest(), new_array_sha256=sha256(new[k].tobytes()).hexdigest(),
        raw_equal=same(new[k], old[k]), physical_comparison="pass") for k in sorted(new)}
    assert {k for k, v in fields.items() if v["raw_equal"]} == RAW_FIELDS
    return dict(cell_map=cell_map, node_map=node_map, dof_map=dof_map), dict(total_fields=27,
        raw_equal_fields=sorted(k for k, v in fields.items() if v["raw_equal"]),
        physically_mapped_fields=sorted(set(fields) - RAW_FIELDS), fields=fields,
        new_top_uy_dofs=extra_top_uy.tolist(), tip_coordinate_mm=[80.,30.], parent_tip_node=2570, new_tip_node=2630, parent_physical_subdomain_byte_exact=True)

def verify_accounting_transition(root, control, transition, bind):
    """Verify copied source and saved proof identities only; never run a counter or mechanics."""
    installed = control/"reference_author"
    proof_control = root/PROOF_CONTROL
    assert transition["proof_origin_stage"] == PROOF_CONTROL+"/run_001"
    assert transition["schema_version"] == "recovered-invalid-J-saved-accounting-transition-1.1"
    assert transition["proof_kind"] == "recovered_invalid_J_saved_accounting"
    assert transition["path"] == (installed/"counter_attempts.py").relative_to(root).as_posix()
    assert transition["previous_sha256"] == ORIGINAL_COUNTER_PIN and transition["current_sha256"] == COUNTER_PIN
    expected = dict(original_counter=installed/"counter_original_B028.py",counter=installed/"counter_attempts.py")
    expected.update({role:proof_control/"reference_author/accounting_evidence"/name for role,name in ACCOUNTING_EVIDENCE.items()})
    evidence = transition["evidence"]
    assert set(evidence) == set(expected)
    for role,path in expected.items():
        assert evidence[role]["file"] == path.relative_to(root).as_posix() and evidence[role]["sha256"] == sha(path)
        bind(path,evidence[role]["sha256"])
    assert evidence["original_counter"]["sha256"] == ORIGINAL_COUNTER_PIN and evidence["counter"]["sha256"] == COUNTER_PIN
    proof,accounting,peer,independent,preflight = (read(expected[role]) for role in
        ("saved_report","saved_accounting","peer_review","independent_chronology","preflight_report"))
    assert proof["status"] == "saved_only_reproduction_pass" and proof["all_bindings_unchanged"]
    assert proof["source_transition"] == dict(path="counter_attempts.py",previous_sha256=ORIGINAL_COUNTER_PIN,
        current_sha256=COUNTER_PIN,proof_kind=transition["proof_kind"])
    assert proof["current_accounting_sha256"] == evidence["saved_accounting"]["sha256"] and proof["checks_completed"] == 1817
    assert proof["complete_current_states"] == independent["actual_states"] == 24
    assert proof["independent_counts"] == accounting["counts"] == independent["counters"]
    assert len(accounting["rejected_invalid_J_trials"]) == len(independent["incomplete_invalid_J_trials"]) == 14
    assert len(accounting["rejected_range_trials"]) == proof["actual_rejected_range_trials"] == 10
    assert proof["first_range_force_ordinal"] == accounting["rejected_range_trials"][0]["force_call"] == 325
    assert len(proof["regressions"]) == 3 and len(proof["tampered_chronologies"]) == 2
    assert all(value == 0 for value in proof["calls"].values())
    assert peer["status"] == "pass_static_and_saved_ledger_only" and peer["unchanged_rest"] is True
    assert independent["status"] == "pure_saved_chronology_pass" and all(value == 0 for value in peer["activity"].values())
    assert preflight["status"] == "saved_accounting_unsupported" and preflight["source_sha256"] == ORIGINAL_COUNTER_PIN
    assert proof["preflight_sha256"] == evidence["preflight_report"]["sha256"]
    by_name = {Path(name.replace("\\","/")).name:pin for name,pin in peer["source_pins"].items()}
    for name,role in (("counter_original_B028.py","original_counter"),("counter_attempts.py","counter"),
        ("validate_saved_accounting.py","validation_helper"),("report.json","saved_report"),
        ("current_accounting.json","saved_accounting"),("projection_counter_saved_evidence.json","independent_chronology")):
        assert by_name[name] == evidence[role]["sha256"]
    for name,pin in proof["input_bindings"].items(): bind(root/name,pin)
    for name,pin in independent["input_pins"].items(): bind(root/name,pin)
    result_file = root/transition["proof_origin_stage"]/"result/result.json"
    assert proof["input_bindings"][result_file.relative_to(root).as_posix()] == sha(result_file)
    assert read(result_file)["call_counts"] == accounting["counts"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--author",type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument("--reference-seconds",type=float,required=True)
    parser.add_argument("--budget-basis",required=True)
    args = parser.parse_args()
    root,stage,author = args.repo.resolve(),args.input.resolve(),args.author.resolve()
    assert isfinite(args.reference_seconds) and args.reference_seconds == 1500. and args.budget_basis.strip()
    control = stage.parent
    assert stage == root/CONTROL/"run_001"
    installed,output = control/"reference_author",control/"reference"
    contract_file,protocol_file = control/"reference_contract.json",control/"reference_protocol.json"
    assert all(not p.exists() for p in (installed,output,contract_file,protocol_file,control/"reference_launch.json",control/"reference_stdout.log"))
    pins = {}
    def bind(path,pin):
        assert sha(path) == pin
        pins[path.relative_to(root).as_posix()] = pin
    inventory,receipt,freeze,result = verify_complete_production(root,stage,bind)
    old_contract = read(root/COMPARISON/"reference_contract.json")
    bind(root/COMPARISON/"reference_contract.json",sha(root/COMPARISON/"reference_contract.json"))
    old_summary_file = root/COMPARISON/"reference/summary.json"
    bind(old_summary_file,sha(old_summary_file))
    old_summary = read(old_summary_file)
    baseline_result = root/COMPARISON/"run_001/result/result.json"
    assert old_summary["status"] == "pass" and old_summary["result_sha256"] == sha(baseline_result)
    assert old_summary["accepted_states"] == 24 and old_summary["HP_calls_started"] == old_summary["HP_calls_completed"] == 48
    old_freeze_file = root/COMPARISON/"run_001/source_freeze.json"
    bind(old_freeze_file,sha(old_freeze_file))
    old_freeze = read(old_freeze_file)
    core = {p:pin for p,pin in freeze["sources"].items() if p.startswith("hf_repo/src/hf_eval/")}
    old_core = {p:pin for p,pin in old_freeze["sources"].items() if p.startswith("hf_repo/src/hf_eval/")}
    assert len(old_core) == len(core) == 25 and core == old_core
    assert core["hf_repo/src/hf_eval/analysis_domain.py"] == "f0929fb8949ca3155b32badf8eabe4b6a563a2541a220a6616c96efc26f179e6"
    refs = dict(core)
    for name in MATH:
        path = "hf_repo/scripts/"+name
        refs[path] = old_contract["reference_sources"][path]
        bind(root/path,refs[path])
    launcher = control/"launch_pose.py"
    assert sha(launcher) == LAUNCHER_PIN and launcher.resolve().parents[3] == root
    refs[launcher.relative_to(root).as_posix()] = LAUNCHER_PIN
    assert sha(author/"audit_enlarged_square.py") == AUDIT_PIN and sha(author/"core_audit_mechanical.py") == CORE_PIN
    assert sha(author/"counter_attempts.py") == COUNTER_PIN and sha(author/"counter_original_B028.py") == ORIGINAL_COUNTER_PIN
    installed.mkdir()
    for name in ("audit_enlarged_square.py","core_audit_mechanical.py","counter_attempts.py","counter_original_B028.py","reference_contract_builder.py"):
        shutil.copyfile(author/name,installed/name)
        refs[(installed/name).relative_to(root).as_posix()] = sha(installed/name)
    evidence = dict(old_contract["accounting_source_transition"]["evidence"])
    for role,name in (("counter","counter_attempts.py"),("original_counter","counter_original_B028.py")):
        evidence[role] = dict(file=(installed/name).relative_to(root).as_posix(),sha256=sha(installed/name))
    transition = dict(old_contract["accounting_source_transition"],
        path=(installed/"counter_attempts.py").relative_to(root).as_posix(),evidence=evidence,
        proof_origin_stage=PROOF_CONTROL+"/run_001")
    verify_accounting_transition(root,control,transition,bind)
    model_file = stage/"result"/result["model"]["arrays_path"]
    contract = dict(schema_version="right-margin4-reference-contract-1.0",production_stage=stage.relative_to(root).as_posix(),
        baseline_commit=BASELINE,initial_guess=INITIAL_GUESS,predictor_initialization=PREDICTOR_INITIALIZATION,
        limits=dict(helper_seconds=1500.,outer_seconds=1560.,sampled_RSS_bytes=RSS),workpiece=BODY,targets_mm=TARGETS,
        reference_sources=refs,counter_schema=COUNTER_SCHEMA,counter_helper_sha256=COUNTER_PIN,accounting_source_transition=transition,
        actual_accepted_states=len(result["states"]),expected_new_HP80_120_calls=2*len(result["states"]),reference_budget_basis=args.budget_basis,
        input_inventory_sha256=sha(stage/"input_inventory.json"),production_receipt_sha256=sha(stage/"execution_receipt.json"),source_freeze_sha256=sha(stage/"source_freeze.json"),
        production_launch_file=(control/"production_launch.json").relative_to(root).as_posix(),production_launch_sha256=sha(control/"production_launch.json"),
        production_result_sha256=sha(stage/"result/result.json"),production_model_sha256=sha(model_file),
        comparison_baseline_stage=COMPARISON+"/run_001",preparation_stage=PREPARATION+"/run_001",boundary_placement=PLACEMENT,
        parameter_case="right_medium_domain_margin2_to4mm",gamma=1e-6,direction_archive_fields=["direction"],multiplier_direction=0.,
        scope="Fresh all-actual-state4mm right-medium-margin mechanical reference only; old accounting proof is source-validation context, no state/HP/contact/pressure/clamp qualification inherited.")
    with contract_file.open("x",encoding="utf-8") as handle:
        json.dump(contract,handle,indent=2,allow_nan=False);handle.write("\n")
    pins.update(refs);pins[contract_file.relative_to(root).as_posix()] = sha(contract_file)
    assert len({Path(p).name for p in refs}) == len(refs)
    assert all(sha(root/p) == pin for p,pin in pins.items())
    argv = [(installed/"audit_enlarged_square.py").relative_to(root).as_posix(),"--repo",".","--input",stage.relative_to(root).as_posix(),
        "--output",output.relative_to(root).as_posix(),"--contract",contract_file.relative_to(root).as_posix(),"--time-limit","1500.0"]
    protocol = dict(schema_version="right-margin4-reference-protocol-1.0",bindings=pins,sampled_RSS_bytes=RSS,
        phases=dict(reference=dict(helper_seconds=1500.,outer_seconds=1560.,argv=argv)),
        actual_accepted_states=len(result["states"]),expected_new_HP80_120_calls=2*len(result["states"]),production_rerun=False,reference_started=False,
        stop_policy="First failure closes reference; all actual states fresh, no prefix reuse/production retry",
        stop_file_contract="Original F3 launcher writes control/stop_requested.txt; reference checks between actual stages.")
    with protocol_file.open("x",encoding="utf-8") as handle:
        json.dump(protocol,handle,indent=2,allow_nan=False);handle.write("\n")
    print(json.dumps(dict(status="frozen_only_not_executed",actual_states=len(result["states"]),expected_HP_calls=2*len(result["states"]),protocol_sha256=sha(protocol_file))))


if __name__ == "__main__":
    main()
