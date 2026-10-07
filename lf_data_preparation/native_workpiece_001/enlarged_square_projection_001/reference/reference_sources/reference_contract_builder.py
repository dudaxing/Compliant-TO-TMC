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
AUDIT_PIN = "3988cc5e6e923784a3014cb74970fe83ebac4a5052d0093721392576f20cb17d"
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
PREDECESSOR_TARGETS = [0.,.5,1.,1.5,1.75,1.8,1.75,1.5,1.,.5,0.]
TARGETS = [0., .25, .5, .65, .75, .8, .85, .9, .95, 1., 1.05, 1.1, 1.15, 1.2, 1.15, 1.1, 1., .9, .8, .75, .65, .5, .25, 0.]
BODY = dict(kind="fixed_rigid",shape="square",center_mm=[71.,40.],side_mm=18.,fixed_components=[0,1])
INITIAL_GUESS = "port_projection"
PREDICTOR_INITIALIZATION = dict(displacement_mode=INITIAL_GUESS, applied_dw=False, applied_dR=True,
    port_adjustment="distributed normalized free-port weights", predictor_LU_role="reaction increment estimator",
    linear_residual_scope="Actual computed KKT solution; not the applied displacement seed.")
read = lambda p:json.loads(p.read_text(encoding="utf-8"))
sha = lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write("\n")


def verify_qualified_prerequisites(root, roles):
    """Check completed baseline identities/costs, never transfer their state qualification."""
    assert set(roles) == {"pose002","soft001"}
    for label,role in roles.items():
        control = root/"lf_data_preparation/native_workpiece_001"/(
            "shift_square_pose_002" if label == "pose002" else "shift_square_soft_001")
        run = control/"run_001"
        assert role["stage"] == control.relative_to(root).as_posix()
        assert role["run_stage"] == run.relative_to(root).as_posix()
        assert all(sha(root/name) == pin for name,pin in role["files"].items())
        files = [control/n for n in ("production_protocol.json","production_launch.json",
            "reference_contract.json","reference_protocol.json","reference_launch.json",
            "reference/summary.json","reference/lifecycle.json")]
        files += [run/n for n in ("task.json","input_inventory.json","source_freeze.json",
            "execution_receipt.json","result/result.json")]
        assert all(role["files"].get(p.relative_to(root).as_posix()) == sha(p) for p in files)
        production,launch,contract,protocol,ref_launch,summary,life = (read(p) for p in files[:7])
        task,inventory,freeze,receipt,result = (read(p) for p in files[7:])
        assert launch["status"] == receipt["status"] == ref_launch["status"] == summary["status"] == life["status"] == "pass"
        assert launch["exit_code"] == ref_launch["exit_code"] == 0 and launch["stop_reason"] is ref_launch["stop_reason"] is None
        assert launch["invocations"] == ref_launch["invocations"] == receipt["invocations"] == 1
        assert launch["all_bindings_unchanged"] is ref_launch["all_bindings_unchanged"] is receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
        assert launch["protocol_sha256"] == sha(files[0]) and ref_launch["protocol_sha256"] == sha(files[3])
        assert result["status"] == "success" and result["failure"] is None
        assert all(result[k] is True for k in ("production_converged","target_reached","task_target_executed",
            "path_completed","loading_peak_reached","unload_endpoint_reached"))
        assert result["states"][0]["d"] == result["states"][-1]["d"] == 0.
        assert result["targets_mm"] == task["path"]["targets_mm"] == inventory["case"]["targets_mm"] == summary["audited_targets_mm"] == PREDECESSOR_TARGETS
        assert [r["d"] for r in result["states"] if r["is_original_target"]] == PREDECESSOR_TARGETS
        n = len(result["states"])
        assert role["accepted_states"] == n == result["accepted_states"] == receipt["accepted_states"] == summary["accepted_states"] == life["accepted_states_completed"]
        assert role["HP_calls"] == summary["HP_calls_started"] == summary["HP_calls_completed"] == life["HP_calls_started"] == life["HP_calls_completed"] == 2*n
        assert [r["state_sha256"] for r in summary["states"]] == [r["state_sha256"] for r in result["states"]] == receipt["state_sha256"]
        assert summary["result_sha256"] == receipt["result_sha256"] == contract["production_result_sha256"] == sha(files[11])
        assert summary["independent_reference_contract_sha256"] == sha(files[2])
        assert summary["full_element_and_DOF_coverage"] is True and summary["HP_matrix_columns_exhaustively_checked"] is False
        assert receipt["sources"] == freeze["sources"] and receipt["source_freeze_sha256"] == inventory["source_freeze_sha256"] == sha(files[9])
        assert receipt["input_inventory_sha256"] == sha(files[8])
        model = run/"result"/result["model"]["arrays_path"]
        assert result["model"]["arrays_sha256"] == receipt["model_sha256"] == contract["production_model_sha256"] == sha(model)
        expected = {"model":model,"task":files[7],"result":files[11],"summary":files[5]}
        for name,path in expected.items():
            pin_key = "task_file_sha256" if name == "task" else name+"_sha256"
            assert role[name+"_file"] == path.relative_to(root).as_posix() and role[pin_key] == sha(path)
            assert role["files"].get(path.relative_to(root).as_posix()) == sha(path)
        assert task["workpiece"] == summary["workpiece"] == contract["workpiece"] == dict(
            kind="fixed_rigid",shape="square",center_mm=[71.,40.],side_mm=16.,fixed_components=[0,1])
        assert task["material"]["E_MPa"] == (1. if label == "pose002" else .5)
        assert task["third_medium"]["gamma"] == task["regularization"]["alpha"] == (1e-6 if label == "pose002" else 2e-6)


def verify_initialization(root, inventory, freeze, receipt, result):
    """Bind classified source transitions and saved predictor flags, without numerical evaluation."""
    assert inventory["initial_guess"] == receipt["initial_guess"] == result["initial_guess"] == INITIAL_GUESS
    assert inventory["predictor_initialization"] == PREDICTOR_INITIALIZATION
    predictors = [item for item in result["path_diagnostics"]["linear_solve_diagnostics"] if item["phase"] == "predictor"]
    assert receipt["predictor_initialization"] == dict(PREDICTOR_INITIALIZATION,
        actual_predictor_LU_records=len(predictors), actual_predictor_flags_match=True)
    assert all(item["displacement_mode"] == INITIAL_GUESS and item["applied_dw"] is False and item["applied_dR"] is True for item in predictors)
    previous = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle_010"
    old = read(previous/"source_freeze.json")["sources"]
    transitions = inventory["source_transition"]
    controller_keys = {"hf_repo/src/hf_eval/native_mean.py","hf_repo/src/hf_eval/split_displacement.py"}
    tangent_key = "hf_repo/src/hf_eval/split_numpy_tangent.py"
    assert set(transitions) == controller_keys|{tangent_key} and freeze["source_transition"] == transitions
    assert transitions[tangent_key]["proof_kind"] == "tangent_direction_scaling"
    assert transitions[tangent_key]["qualification_protocol_file"] == "lf_data_preparation/native_workpiece_001/t44_direction_scaling_repair_001/protocol.json"
    for name,item in transitions.items():
        assert item["previous_sha256"] == item["previous_capsule_sha256"] == old[name]
        assert item["current_sha256"] == freeze["sources"][name] == sha(root/name)
        assert sha(root/item["previous_capsule_file"]) == old[name]
        for role in ("qualification_protocol","qualification_launch","qualification_receipt"):
            assert sha(root/item[role+"_file"]) == item[role+"_sha256"]
    control = root/"lf_data_preparation/native_workpiece_001/port_projection_validation_001"
    files = [control/name for name in ("protocol.json","validation_launch.json","result/receipt.json")]
    protocol,launch,proof = map(read,files)
    assert protocol["schema_version"] == "port-projection-initialization-proof-1.0" and protocol["initial_guess"] == INITIAL_GUESS
    assert isinstance(protocol["source_transition"],list) and len(protocol["source_transition"]) == 2
    assert protocol["source_transition"] == proof["source_transition"] and {item["path"] for item in protocol["source_transition"]} == controller_keys
    for entry in protocol["source_transition"]:
        name,item = entry["path"],transitions[entry["path"]]
        assert item["proof_kind"] == "port_projection_initialization"
        assert entry == dict(path=name,previous_sha256=old[name],current_sha256=freeze["sources"][name],proof_kind=item["proof_kind"])
        assert [item["qualification_"+role+"_file"] for role in ("protocol","launch","receipt")] == [file.relative_to(root).as_posix() for file in files]
    assert launch["status"] == proof["status"] == "pass" and launch["exit_code"] == 0 and launch["invocations"] == 1
    assert launch["stop_reason"] is None and launch["all_bindings_unchanged"] and launch["protocol_sha256"] == sha(files[0])
    assert proof["pytest_invocations"] == 1 and proof["pytest_exit_code"] == 0
    assert protocol["expected_tests"] == proof["tests_passed"] == proof["tests"]["tests"] == 15
    assert all(proof["tests"][key] == 0 for key in ("errors","failures","skipped"))
    assert all(proof[key] == 0 for key in ("tests_failed","tests_errors","tests_skipped","full_HF_solver_calls","HP_calls"))
    assert proof["all_bindings_unchanged"] and proof["default_initial_guess_preserved"]
    assert proof["production_force_changed"] is False and proof["force_tangent_gates_changed"] is False
    assert protocol["phases"]["validation"]["helper_seconds"] == 180 and protocol["phases"]["validation"]["outer_seconds"] == launch["outer_seconds"] == 240
    assert protocol["sampled_RSS_bytes"] == launch["sampled_RSS_limit_bytes"] == RSS
    assert 0 <= proof["elapsed_seconds"] <= 180 and 0 <= launch["elapsed_seconds"] <= 240
    assert 0 <= proof["peak_sampled_RSS_bytes"] <= RSS and 0 <= launch["peak_sampled_tree_RSS_bytes"] <= RSS
    assert all(sha(root/name) == pin for name,pin in protocol["bindings"].items())


def verify_accounting_transition(root, control, transition, bind):
    """Verify copied source and saved proof identities only; never run a counter or mechanics."""
    installed = control/"reference_author"
    assert transition["schema_version"] == "recovered-invalid-J-saved-accounting-transition-1.1"
    assert transition["proof_kind"] == "recovered_invalid_J_saved_accounting"
    assert transition["path"] == (installed/"counter_attempts.py").relative_to(root).as_posix()
    assert transition["previous_sha256"] == ORIGINAL_COUNTER_PIN and transition["current_sha256"] == COUNTER_PIN
    expected = dict(original_counter=installed/"counter_original_B028.py",counter=installed/"counter_attempts.py")
    expected.update({role:installed/"accounting_evidence"/name for role,name in ACCOUNTING_EVIDENCE.items()})
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
    result_file = control/"run_001/result/result.json"
    assert proof["input_bindings"][result_file.relative_to(root).as_posix()] == sha(result_file)
    assert read(result_file)["call_counts"] == accounting["counts"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--input",type=Path,required=True,help="Actual casecontrol/run_001")
    parser.add_argument("--author",type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument("--reference-seconds",type=float,required=True,help="Explicit future window selected from actual full-path N before freezing")
    parser.add_argument("--budget-basis",required=True,help="Recorded actual-N/cost basis; never extends a running window")
    args = parser.parse_args()
    root,stage,author = args.repo.resolve(),args.input.resolve(),args.author.resolve()
    assert isfinite(args.reference_seconds) and args.reference_seconds > 0. and args.budget_basis.strip()
    limit = args.reference_seconds
    control = stage.parent
    assert stage.name == "run_001" and control.name == "enlarged_square_projection_001"
    assert control.parent == root/"lf_data_preparation/native_workpiece_001"
    stage.relative_to(root)
    installed,output = control/"reference_author",control/"reference"
    contract_file,protocol_file = control/"reference_contract.json",control/"reference_protocol.json"
    assert all(not q.exists() for q in (installed,output,contract_file,protocol_file,
        control/"reference_launch.json",control/"reference_stdout.log"))
    assert not (control/"stop_requested.txt").exists() and not (stage/"stop_requested.txt").exists()
    paths = {n:stage/n for n in ("input_inventory.json","execution_receipt.json","source_freeze.json")}
    inventory,receipt,freeze = (read(paths[n]) for n in paths)
    case = inventory["case"]
    prerequisites = inventory["qualified_prerequisites"]
    verify_qualified_prerequisites(root,prerequisites)
    failed_context = inventory["failed_predecessor_context"]
    failed_stage = root/"lf_data_preparation/native_workpiece_001/shift_square_tip_align_001"
    failed_paths = [failed_stage/n for n in ("production_protocol.json","production_launch.json",
        "run_001/execution_receipt.json","run_001/result/result.json")]
    assert failed_context["stage"] == failed_stage.relative_to(root).as_posix()
    assert failed_context["files"] == {p.relative_to(root).as_posix():sha(p) for p in failed_paths}
    assert failed_context["scope"] == "Closed x72 side16 failed physical path retained as context only; no qualification, prefix reuse or repair of that card."
    closed_protocol,closed_launch,closed_receipt,closed_result = (read(p) for p in failed_paths)
    assert failed_context["status"] == closed_launch["status"] == closed_receipt["status"] == "not_pass"
    assert closed_result["status"] == "failed" and closed_result["failure"]["code"] == "invalid_J"
    assert failed_context["accepted_states"] == closed_result["accepted_states"] == 8
    assert failed_context["path_completed"] is closed_result["path_completed"] is False
    assert failed_context["unload_endpoint_reached"] is closed_result["unload_endpoint_reached"] is False
    assert closed_result["call_counts"]["HP_calls"] == 0
    assert closed_launch["protocol_sha256"] == sha(failed_paths[0]) and closed_receipt["result_sha256"] == sha(failed_paths[3])
    enlarged_context = inventory["failed_enlarged_context"]
    enlarged_stage = root/"lf_data_preparation/native_workpiece_001/enlarged_square_contact_001"
    enlarged_files = [enlarged_stage/name for name in ("production_protocol.json","production_launch.json",
        "run_001/execution_receipt.json","run_001/result/result.json")]
    assert enlarged_context["stage"] == enlarged_stage.relative_to(root).as_posix()
    assert enlarged_context["files"] == {file.relative_to(root).as_posix():sha(file) for file in enlarged_files}
    assert enlarged_context["scope"] == "Closed same side18/center71/24-target tangent-initialization failure only; no qualification, prefix reuse or repair of that card."
    enlarged_protocol,enlarged_launch,enlarged_receipt,enlarged_result = map(read,enlarged_files)
    assert enlarged_context["status"] == enlarged_launch["status"] == enlarged_receipt["status"] == "not_pass"
    assert enlarged_result["status"] == "failed" and enlarged_result["failure"]["code"] == "invalid_J"
    assert enlarged_context["accepted_states"] == enlarged_result["accepted_states"] == enlarged_receipt["accepted_states"] == 9
    assert enlarged_context["path_completed"] is enlarged_result["path_completed"] is False
    assert enlarged_context["unload_endpoint_reached"] is enlarged_result["unload_endpoint_reached"] is False
    assert enlarged_receipt["HP_calls"] == 0 and enlarged_launch["all_bindings_unchanged"] is True
    assert enlarged_launch["protocol_sha256"] == sha(enlarged_files[0]) and enlarged_receipt["result_sha256"] == sha(enlarged_files[-1])

    production_protocol,production_launch = control/"production_protocol.json",control/"production_launch.json"
    protocol,launch = read(production_protocol),read(production_launch)
    result_file = stage/case["result_directory"]/"result.json"
    result = read(result_file)
    assert launch["status"] == receipt["status"] == "pass" and result["status"] == "success"
    assert launch["exit_code"] == 0 and launch["invocations"] == receipt["invocations"] == 1
    assert launch["stop_reason"] is None and launch["all_bindings_unchanged"] is True
    assert launch["protocol_sha256"] == sha(production_protocol) and launch["bindings"] == protocol["bindings"]
    assert protocol["phases"]["production"]["helper_seconds"] == 3000
    assert protocol["phases"]["production"]["outer_seconds"] == launch["outer_seconds"] == 3060
    assert 0 <= launch["elapsed_seconds"] <= 3060 and 0 <= launch["peak_sampled_tree_RSS_bytes"] <= RSS
    assert receipt["input_inventory_sha256"] == sha(paths["input_inventory.json"])
    assert receipt["source_freeze_sha256"] == inventory["source_freeze_sha256"] == sha(paths["source_freeze.json"])
    assert receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
    assert receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
    assert case["alias"] == "gripper_coarse_square_x71_side18" and case["source_alias"] == "gripper_canonical"
    assert (case["elements"],case["dofs"],case["fixed_DOFs"],case["free_DOFs"]) == (3200,6642,448,6194)
    assert inventory["settings"] == result["settings"] and inventory["settings"]["time_limit_seconds"] == 3000.
    assert result["targets_mm"] == case["targets_mm"] == TARGETS and result["task_target_mm"] == 1.2
    assert all(result[k] is True for k in ("production_converged","target_reached","path_completed",
        "task_target_executed","loading_peak_reached","unload_endpoint_reached"))
    assert result["failure"] is None and result["save_force_calls"] == result["save_tangent_calls"] == 0
    assert result["states"][0]["d"] == result["states"][-1]["d"] == 0.
    assert [r["d"] for r in result["states"] if r["is_original_target"]] == TARGETS
    assert len(result["states"]) == result["accepted_states"] == receipt["accepted_states"]
    assert [r["state_sha256"] for r in result["states"]] == receipt["state_sha256"]
    assert result["call_counts"] == receipt["call_counts"]
    assert result["call_counts"]["HP_calls"] == result["call_counts"]["JIT_calls"] == 0
    assert all(result[k] is False for k in ("equilibrium_qualified","independent_HP_qualified","HF_qualified"))
    assert result["schema_version"] == "hf-native-mean-result-1.2" and result["response_mode"] == "mechanical"
    assert result["auxiliary_material_energy"] == dict(status="not_evaluated",qualified=False,field_present=False)
    task = read(root/case["task_file"])
    assert task["workpiece"] == BODY and task["material"]["E_MPa"] == 1.
    assert task["third_medium"]["gamma"] == task["regularization"]["alpha"] == 1e-6
    assert result["force_scale_per_length"] == 20.
    failed_task = enlarged_stage/"run_001/task.json"
    assert sha(root/case["task_file"]) == sha(failed_task) == "385cce960696b8c01e1323fc43d98f4ee28a392214c44a8f3609006324cde2e0"
    assert inventory["input_bindings"].get(failed_task.relative_to(root).as_posix()) == sha(failed_task)
    verify_initialization(root,inventory,freeze,receipt,result)
    assert inventory["boundary_placement"]["body_box_mm"] == [62.,80.,31.,40.]
    assert inventory["boundary_placement"]["right_outer_boundary_mm"] == 80.
    assert inventory["boundary_placement"]["right_medium_margin_mm"] == 0.
    assert inventory["boundary_placement"]["workpiece_touches_analysis_boundary"] is True

    assert receipt["result_sha256"] == sha(result_file)
    model_file = result_file.parent/result["model"]["arrays_path"]
    assert receipt["model_sha256"] == result["model"]["arrays_sha256"] == sha(model_file)
    assert sha(model_file) == case["workpiece_model_sha256"] or receipt["declared_workpiece_model_arrays_equal"] is True
    assert sha(author/"audit_enlarged_square.py") == AUDIT_PIN and sha(author/"core_audit_mechanical.py") == CORE_PIN
    assert sha(author/"counter_attempts.py") == COUNTER_PIN
    launcher = control/"launch_pose.py"
    assert sha(launcher) == LAUNCHER_PIN and launcher.resolve().parents[3] == root
    source_map = freeze["sources"]
    assert len(source_map) == 70 and len({Path(n).name for n in source_map}) == 70
    pins = dict(protocol["bindings"])
    pins.update(inventory["input_bindings"])
    pins.update(source_map)
    for name,pin in source_map.items():
        capsule = stage/"sources"/Path(name).name
        assert sha(capsule) == pin
        pins[capsule.relative_to(root).as_posix()] = pin
    for path in [*paths.values(),production_protocol,production_launch,stage/"preparation_receipt.json",
            *[q for q in result_file.parent.rglob("*") if q.is_file()],
            *[q for q in stage.glob("first_*_range_input/*") if q.is_file()]]:
        pins[path.relative_to(root).as_posix()] = sha(path)
    for role in prerequisites.values(): pins.update(role["files"])
    pins.update(failed_context["files"])
    pins.update(enlarged_context["files"])
    previous_failed = root/"lf_data_preparation/native_workpiece_001/shift_square_pose_001"
    failed_result_file = previous_failed/"run_001/result/result.json"
    failed_result = read(failed_result_file)
    assert failed_result["status"] == "failed" and failed_result["failure"]["code"] == "time_limit"
    pose001_failed_files = {}
    for path in (failed_result_file,previous_failed/"run_001/execution_receipt.json",previous_failed/"production_launch.json"):
        name,pin = path.relative_to(root).as_posix(),sha(path)
        pins[name] = pin; pose001_failed_files[name] = pin
    # Source roles remain separate; this is an import closure/superset for the reference.
    refs = {n:pin for n,pin in source_map.items() if n.startswith("hf_repo/src/hf_eval/")}
    for name in MATH: refs["hf_repo/scripts/"+name] = source_map["hf_repo/scripts/"+name]
    refs[launcher.relative_to(root).as_posix()] = LAUNCHER_PIN
    assert all(sha(root/n) == pin for n,pin in pins.items())
    installed.mkdir()
    for name in ("audit_enlarged_square.py","core_audit_mechanical.py","counter_attempts.py","counter_original_B028.py"):
        shutil.copyfile(author/name,installed/name)
        refs[(installed/name).relative_to(root).as_posix()] = sha(installed/name)
    own = Path(__file__).resolve(); copied_builder = installed/own.name
    shutil.copyfile(own,copied_builder)
    refs[copied_builder.relative_to(root).as_posix()] = sha(copied_builder)
    shutil.copytree(author/"accounting_evidence",installed/"accounting_evidence")
    evidence_files = dict(original_counter=installed/"counter_original_B028.py",counter=installed/"counter_attempts.py")
    evidence_files.update({role:installed/"accounting_evidence"/name for role,name in ACCOUNTING_EVIDENCE.items()})
    accounting_transition = dict(schema_version="recovered-invalid-J-saved-accounting-transition-1.1",
        proof_kind="recovered_invalid_J_saved_accounting",path=(installed/"counter_attempts.py").relative_to(root).as_posix(),
        previous_sha256=ORIGINAL_COUNTER_PIN,current_sha256=COUNTER_PIN,
        evidence={role:dict(file=path.relative_to(root).as_posix(),sha256=sha(path)) for role,path in evidence_files.items()})
    def bind_accounting(path,pin):
        assert sha(path) == pin
        pins[path.relative_to(root).as_posix()] = pin
    verify_accounting_transition(root,control,accounting_transition,bind_accounting)
    assert len({Path(n).name for n in refs}) == len(refs)
    contract = dict(schema_version="shift-square-reference-contract-1.1",
        production_stage=stage.relative_to(root).as_posix(),baseline_commit=inventory["baseline_commit"],
        initial_guess=INITIAL_GUESS,predictor_initialization=PREDICTOR_INITIALIZATION,
        limits=dict(helper_seconds=limit,outer_seconds=limit+60,sampled_RSS_bytes=RSS),workpiece=BODY,targets_mm=TARGETS,
        reference_sources=refs,counter_schema=COUNTER_SCHEMA,counter_helper_sha256=COUNTER_PIN,
        accounting_source_transition=accounting_transition,
        actual_accepted_states=len(result["states"]),expected_new_HP80_120_calls=2*len(result["states"]),
        reference_budget_basis=args.budget_basis,input_inventory_sha256=sha(paths["input_inventory.json"]),
        production_receipt_sha256=sha(paths["execution_receipt.json"]),source_freeze_sha256=sha(paths["source_freeze.json"]),
        production_launch_file=production_launch.relative_to(root).as_posix(),production_launch_sha256=sha(production_launch),
        production_result_sha256=sha(result_file),production_model_sha256=sha(model_file),
        source_transition=inventory["source_transition"],
        qualified_prerequisites=prerequisites,boundary_placement=inventory["boundary_placement"],
        failed_predecessor_context=failed_context,
        failed_enlarged_context=enlarged_context,
        prerequisite_scope="Identity and cost contexts only; no reference or new-state qualification is inherited",
        preceding_failed_pose001=pose001_failed_files,preceding_failure_scope="Cost/closed-failure context only; no prefix reuse or failed-state qualification",
        scope="Fresh exhaustive reference for all actual accepted complete x71 side18 port-projection states; same physical task, no failed-state, prefix, pressure/clamp, energy or all-column qualification")
    assert freeze["source_transition"] == contract["source_transition"]
    write(contract_file,contract)
    pins.update(refs); pins[contract_file.relative_to(root).as_posix()] = sha(contract_file)
    argv = [(installed/"audit_enlarged_square.py").relative_to(root).as_posix(),"--repo",".",
        "--input",stage.relative_to(root).as_posix(),"--output",output.relative_to(root).as_posix(),
        "--contract",contract_file.relative_to(root).as_posix(),"--time-limit",str(limit)]
    write(protocol_file,dict(schema_version="shift-square-reference-protocol-1.1",bindings=pins,
        sampled_RSS_bytes=RSS,phases=dict(reference=dict(helper_seconds=limit,outer_seconds=limit+60,argv=argv)),
        actual_accepted_states=len(result["states"]),expected_new_HP80_120_calls=2*len(result["states"]),
        production_rerun=False,reference_started=False,
        stop_policy="First failure closes reference; all states fresh, no prefix reuse/production retry",
        stop_file_contract="F3 writes control/stop_requested.txt; reference output.parent is this same control"))
    assert all(sha(root/n) == pin for n,pin in pins.items())
    print(json.dumps(dict(status="reference_card_frozen_unstarted",contract_sha256=sha(contract_file),
        protocol_sha256=sha(protocol_file),actual_states=len(result["states"]),expected_fresh_HP=2*len(result["states"]),
        reference_source_count=len(refs),bindings=len(pins),new_HP=0,new_force=0,new_tangent=0)))


if __name__ == "__main__":
    main()
