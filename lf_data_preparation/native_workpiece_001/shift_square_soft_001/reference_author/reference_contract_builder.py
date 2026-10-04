"""Freeze an independent softened x71 accepted-state reference after genuine pose and soft production pass.

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
AUDIT_PIN = "9f3da22e8cd329ee47db413452006513c49842711bbed7b553b2640b2d36dfb3"
POSE_INTERFACE_PIN = "0fcf7f372ccdc10dbf0f66e3473ae59282b8667663e6e070f0a5a1625f87c9ea"
COUNTER_PIN = "b028dba774d430a6d082ca05be86489a56e800be1f1bd69c60148ffccd51e8b3"
LAUNCHER_PIN = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
MATH = ("audit_native_mean.py","audit_native_force.py","hf2_precision_reference.py",
        "hf4_split_precision_reference.py","audit_native_workpiece_cycle.py","run_split_average_demo.py")
TARGETS = [0.,.5,1.,1.5,1.75,1.8,1.75,1.5,1.,.5,0.]
BODY = dict(kind="fixed_rigid",shape="square",center_mm=[71.,40.],side_mm=16.,fixed_components=[0,1])
read = lambda p:json.loads(p.read_text(encoding="utf-8"))
sha = lambda p:sha256(p.read_bytes()).hexdigest()
digest = sha


def write(path,value):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write("\n")


def qualified_pose(root):
    """Read the completed pose002 proof; this function performs no mechanics."""
    control = root/"lf_data_preparation/native_workpiece_001/shift_square_pose_002"
    run = control/"run_001"
    files = [control/n for n in ("production_protocol.json", "production_launch.json",
        "reference_contract.json", "reference_protocol.json", "reference_launch.json",
        "reference/summary.json", "reference/lifecycle.json")]
    files += [run/n for n in ("task.json", "input_inventory.json", "source_freeze.json",
        "execution_receipt.json", "result/result.json", "direction.npz")]
    production, launch, contract, protocol, ref_launch, summary, lifecycle = (read(p) for p in files[:7])
    task, inventory, freeze, receipt, result = (read(p) for p in files[7:12])
    assert launch["status"] == receipt["status"] == ref_launch["status"] == summary["status"] == lifecycle["status"] == "pass"
    assert launch["exit_code"] == ref_launch["exit_code"] == 0 and launch["invocations"] == ref_launch["invocations"] == receipt["invocations"] == 1
    assert launch["stop_reason"] is ref_launch["stop_reason"] is None
    assert launch["all_bindings_unchanged"] is ref_launch["all_bindings_unchanged"] is receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
    assert launch["protocol_sha256"] == digest(files[0]) and ref_launch["protocol_sha256"] == digest(files[3])
    assert result["status"] == "success" and result["failure"] is None
    assert all(result[k] is True for k in ("production_converged", "target_reached", "task_target_executed", "path_completed", "loading_peak_reached", "unload_endpoint_reached"))
    assert result["states"][0]["d"] == result["states"][-1]["d"] == 0.
    assert result["targets_mm"] == task["path"]["targets_mm"] == inventory["case"]["targets_mm"] == summary["audited_targets_mm"]
    assert result["task_target_mm"] == task["input"]["target_mm"] == 1.8
    assert [r["d"] for r in result["states"] if r["is_original_target"]] == result["targets_mm"]
    n = len(result["states"])
    assert n == result["accepted_states"] == receipt["accepted_states"] == summary["accepted_states"] == lifecycle["accepted_states_completed"]
    assert summary["HP_calls_started"] == summary["HP_calls_completed"] == lifecycle["HP_calls_started"] == lifecycle["HP_calls_completed"] == 2*n
    assert [r["state_sha256"] for r in summary["states"]] == [r["state_sha256"] for r in result["states"]] == receipt["state_sha256"]
    assert summary["result_sha256"] == receipt["result_sha256"] == contract["production_result_sha256"] == digest(files[11])
    assert contract["production_stage"] == run.relative_to(root).as_posix()
    assert summary["independent_reference_contract_sha256"] == digest(files[2])
    assert summary["full_element_and_DOF_coverage"] is True and summary["HP_matrix_columns_exhaustively_checked"] is False
    assert summary["alias"] == inventory["case"]["alias"] == "gripper_coarse_square_x71"
    assert task["material"]["E_MPa"] == 1. and task["third_medium"]["gamma"] == task["regularization"]["alpha"] == 1e-6
    assert task["workpiece"] == summary["workpiece"] == contract["workpiece"] == dict(kind="fixed_rigid",shape="square",center_mm=[71.,40.],side_mm=16.,fixed_components=[0,1])
    assert inventory["source_freeze_sha256"] == receipt["source_freeze_sha256"] == digest(files[9])
    assert receipt["sources"] == freeze["sources"] and receipt["input_inventory_sha256"] == digest(files[8])
    assert result["call_counts"]["HP_calls"] == result["call_counts"]["JIT_calls"] == 0
    model = run/"result"/result["model"]["arrays_path"]
    descriptor = run/"result"/result["model"]["descriptor_path"]
    assert result["model"]["arrays_sha256"] == receipt["model_sha256"] == contract["production_model_sha256"] == digest(model)
    files += [model, descriptor]
    return dict(files=files, inventory=inventory, task=task, result=result, summary=summary, model=model, control=control)


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
    assert stage.name == "run_001" and control.name == "shift_square_soft_001"
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
    production_protocol,production_launch = control/"production_protocol.json",control/"production_launch.json"
    protocol,launch = read(production_protocol),read(production_launch)
    result_file = stage/case["result_directory"]/"result.json"
    result = read(result_file)
    assert launch["status"] == receipt["status"] == "pass" and result["status"] == "success"
    assert launch["exit_code"] == 0 and launch["invocations"] == receipt["invocations"] == 1
    assert launch["stop_reason"] is None and launch["all_bindings_unchanged"] is True
    assert launch["protocol_sha256"] == sha(production_protocol) and launch["bindings"] == protocol["bindings"]
    assert protocol["phases"]["production"]["helper_seconds"] == 1800
    assert protocol["phases"]["production"]["outer_seconds"] == launch["outer_seconds"] == 1860
    assert 0 <= launch["elapsed_seconds"] <= 1860 and 0 <= launch["peak_sampled_tree_RSS_bytes"] <= RSS
    assert receipt["input_inventory_sha256"] == sha(paths["input_inventory.json"])
    assert receipt["source_freeze_sha256"] == inventory["source_freeze_sha256"] == sha(paths["source_freeze.json"])
    assert receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
    assert receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
    assert case["alias"] == "gripper_coarse_square_x71_soft" and case["source_alias"] == "gripper_canonical"
    assert result["targets_mm"] == case["targets_mm"] == TARGETS and result["task_target_mm"] == 1.8
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
    assert task["workpiece"] == BODY and task["material"]["E_MPa"] == .5
    assert task["third_medium"]["gamma"] == task["regularization"]["alpha"] == 2e-6
    assert result["force_scale_per_length"] == 10. and result["settings"]["time_limit_seconds"] == 1800.
    pose = qualified_pose(root)
    qualified = inventory["prerequisite_pose_reference"]
    assert qualified["stage"] == pose["control"].relative_to(root).as_posix()
    assert qualified["files"] == {q.relative_to(root).as_posix():sha(q) for q in pose["files"]}
    for role,file in (("model",pose["model"]),("task",pose["control"]/"run_001/task.json"),
            ("result",pose["control"]/"run_001/result/result.json"),("summary",pose["control"]/"reference/summary.json")):
        assert qualified[role+"_file"] == file.relative_to(root).as_posix() and qualified[role+"_sha256"] == sha(file)
    assert case["qualified_pose_model_file"] == qualified["model_file"] and case["qualified_pose_model_sha256"] == qualified["model_sha256"]
    material = ["force_scale_per_length","gamma","lam","mu"]
    assert case["pose_expected_model_changed_fields"] == inventory["pose_model_comparison"]["actual_changed_fields"] == material
    assert len(case["pose_unchanged_model_fields"]) == 23 and len(case["unchanged_model_fields"]) == 17
    assert len(inventory["model_comparison"]["actual_changed_fields"]) == 10
    assert inventory["model_comparison"]["parameter_case"] == "explicit_softened_parameters"
    assert inventory["pose_model_comparison"]["parameter_case"] == "material_only_after_qualified_pose"
    assert receipt["result_sha256"] == sha(result_file)
    model_file = result_file.parent/result["model"]["arrays_path"]
    assert receipt["model_sha256"] == result["model"]["arrays_sha256"] == sha(model_file)
    assert sha(model_file) == case["workpiece_model_sha256"] or receipt["declared_workpiece_model_arrays_equal"] is True
    assert sha(author/"audit_shift_soft.py") == AUDIT_PIN and sha(author/"core_audit_mechanical.py") == CORE_PIN
    assert sha(author/"audit_shift_pose.py") == POSE_INTERFACE_PIN
    assert sha(author/"counter_attempts.py") == COUNTER_PIN
    launcher = control/"launch_pose.py"
    assert sha(launcher) == LAUNCHER_PIN and launcher.resolve().parents[3] == root
    source_map = freeze["sources"]
    assert len(source_map) == 70 and len({Path(n).name for n in source_map}) == 70
    pins = dict(protocol["bindings"])
    pins.update(inventory["input_bindings"])
    pins.update(source_map)
    pins.update(qualified["files"])
    counter_stage = root/"lf_data_preparation/native_workpiece_001/shift_counter_metadata_001"
    counter_files = [counter_stage/n for n in ("protocol.json","validation_launch.json","result/result.json")]
    counter_protocol,counter_launch,counter_result = map(read,counter_files)
    assert counter_launch["status"] == counter_result["status"] == "pass" and counter_launch["exit_code"] == 0
    assert counter_launch["invocations"] == 1 and counter_launch["stop_reason"] is None and counter_launch["all_bindings_unchanged"] is True
    assert counter_launch["protocol_sha256"] == sha(counter_files[0]) and counter_launch["bindings"] == counter_protocol["bindings"]
    assert counter_result["helper_sha256"] == COUNTER_PIN and len(counter_result["cases"]) == 8 and counter_result["all_bindings_unchanged"] is True
    assert counter_result["physical_qualification"] is False and all(counter_result[k] == 0 for k in
        ("force_calls","tangent_calls","HP_calls","model_constructions","solver_calls","consumer_calls"))
    counter_validation = dict(files={q.relative_to(root).as_posix():sha(q) for q in counter_files},
        result_file=counter_files[2].relative_to(root).as_posix(),result_sha256=sha(counter_files[2]),
        scope="Eight metadata cases only; no equilibrium or HP qualification")
    pins.update(counter_validation["files"])
    for name,pin in source_map.items():
        capsule = stage/"sources"/Path(name).name
        assert sha(capsule) == pin
        pins[capsule.relative_to(root).as_posix()] = pin
    for path in [*paths.values(),production_protocol,production_launch,stage/"preparation_receipt.json",
            *[q for q in result_file.parent.rglob("*") if q.is_file()],
            *[q for q in stage.glob("first_*_range_input/*") if q.is_file()]]:
        pins[path.relative_to(root).as_posix()] = sha(path)
    previous_failed = root/"lf_data_preparation/native_workpiece_001/shift_square_pose_001"
    failed_result_file = previous_failed/"run_001/result/result.json"
    failed_result = read(failed_result_file)
    assert failed_result["status"] == "failed" and failed_result["failure"]["code"] == "time_limit"
    failed_context = {}
    for path in (failed_result_file,previous_failed/"run_001/execution_receipt.json",previous_failed/"production_launch.json"):
        name,pin = path.relative_to(root).as_posix(),sha(path)
        pins[name] = pin; failed_context[name] = pin
    # Source roles remain separate; this is an import closure/superset for the reference.
    refs = {n:pin for n,pin in source_map.items() if n.startswith("hf_repo/src/hf_eval/")}
    for name in MATH: refs["hf_repo/scripts/"+name] = source_map["hf_repo/scripts/"+name]
    refs[launcher.relative_to(root).as_posix()] = LAUNCHER_PIN
    assert all(sha(root/n) == pin for n,pin in pins.items())
    installed.mkdir()
    for name in ("audit_shift_soft.py","audit_shift_pose.py","core_audit_mechanical.py","counter_attempts.py"):
        shutil.copyfile(author/name,installed/name)
        refs[(installed/name).relative_to(root).as_posix()] = sha(installed/name)
    own = Path(__file__).resolve(); copied_builder = installed/own.name
    shutil.copyfile(own,copied_builder)
    refs[copied_builder.relative_to(root).as_posix()] = sha(copied_builder)
    assert len({Path(n).name for n in refs}) == len(refs)
    contract = dict(schema_version="shift-square-softened-reference-contract-1.0",
        production_stage=stage.relative_to(root).as_posix(),baseline_commit=inventory["baseline_commit"],
        limits=dict(helper_seconds=limit,outer_seconds=limit+60,sampled_RSS_bytes=RSS),workpiece=BODY,targets_mm=TARGETS,
        reference_sources=refs,counter_schema="shift-complete-attempt-counter-1.0",counter_helper_sha256=COUNTER_PIN,
        actual_accepted_states=len(result["states"]),expected_new_HP80_120_calls=2*len(result["states"]),
        reference_budget_basis=args.budget_basis,input_inventory_sha256=sha(paths["input_inventory.json"]),
        production_receipt_sha256=sha(paths["execution_receipt.json"]),source_freeze_sha256=sha(paths["source_freeze.json"]),
        production_launch_file=production_launch.relative_to(root).as_posix(),production_launch_sha256=sha(production_launch),
        production_result_sha256=sha(result_file),production_model_sha256=sha(model_file),
        source_transition=inventory["source_transition"],qualified_pose=qualified,counter_metadata_validation=counter_validation,
        preceding_failed_pose001=failed_context,preceding_failure_scope="Cost/closed-failure context only; no prefix reuse or failed-state qualification",
        scope="Fresh exhaustive reference for all actual accepted complete softened x71 states, E0.5/gamma-alpha2e-6/Et10; prior pose is identity/prerequisite only, not new-state qualification; no failed-state, pressure/clamp, energy or all-column qualification")
    assert freeze["source_transition"] == contract["source_transition"]
    write(contract_file,contract)
    pins.update(refs); pins[contract_file.relative_to(root).as_posix()] = sha(contract_file)
    argv = [(installed/"audit_shift_soft.py").relative_to(root).as_posix(),"--repo",".",
        "--input",stage.relative_to(root).as_posix(),"--output",output.relative_to(root).as_posix(),
        "--contract",contract_file.relative_to(root).as_posix(),"--time-limit",str(limit)]
    write(protocol_file,dict(schema_version="shift-square-softened-reference-protocol-1.0",bindings=pins,
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
