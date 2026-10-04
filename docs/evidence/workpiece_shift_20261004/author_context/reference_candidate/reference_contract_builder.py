"""Freeze a fresh x71 accepted-state reference card only after production passes.

This program copies source bytes and hashes stored files. It never starts a
reference, constructs a model, or evaluates a force/tangent/geometry routine.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil

RSS = 8*1024**3
CORE_PIN = "b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5"
AUDIT_PIN = "7c714091af20aa6175310d1ddf74e84467df762d61ea6d2a3c440b4dc4bcdb8c"
COUNTER_PIN = "547a76f7d1b750a2f423fdce043a90e4b6754c6148167bb350d36f2852ced32e"
LAUNCHER_PIN = "f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477"
MATH = ("audit_native_mean.py","audit_native_force.py","hf2_precision_reference.py",
        "hf4_split_precision_reference.py","audit_native_workpiece_cycle.py","run_split_average_demo.py")
TARGETS = [0.,.5,1.,1.5,1.75,1.8,1.75,1.5,1.,.5,0.]
BODY = dict(kind="fixed_rigid",shape="square",center_mm=[71.,40.],side_mm=16.,fixed_components=[0,1])
read = lambda p:json.loads(p.read_text(encoding="utf-8"))
sha = lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--input",type=Path,required=True,help="Actual casecontrol/run_001")
    parser.add_argument("--author",type=Path,default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root,stage,author = args.repo.resolve(),args.input.resolve(),args.author.resolve()
    control = stage.parent
    assert stage.name == "run_001" and control.parent == root/"lf_data_preparation/native_workpiece_001"
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
    assert protocol["phases"]["production"]["helper_seconds"] == 900
    assert protocol["phases"]["production"]["outer_seconds"] == launch["outer_seconds"] == 960
    assert 0 <= launch["elapsed_seconds"] <= 960 and 0 <= launch["peak_sampled_tree_RSS_bytes"] <= RSS
    assert receipt["input_inventory_sha256"] == sha(paths["input_inventory.json"])
    assert receipt["source_freeze_sha256"] == inventory["source_freeze_sha256"] == sha(paths["source_freeze.json"])
    assert receipt["sources"] == freeze["sources"] and receipt["inputs"] == inventory["input_bindings"]
    assert receipt["sources_unchanged"] is receipt["inputs_unchanged"] is True
    assert case["alias"] == "gripper_coarse_square_x71" and case["source_alias"] == "gripper_canonical"
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
    assert read(root/case["task_file"])["workpiece"] == BODY
    assert receipt["result_sha256"] == sha(result_file)
    model_file = result_file.parent/result["model"]["arrays_path"]
    assert receipt["model_sha256"] == result["model"]["arrays_sha256"] == sha(model_file)
    assert sha(model_file) == case["workpiece_model_sha256"] or receipt["declared_workpiece_model_arrays_equal"] is True
    assert sha(author/"audit_shift_pose.py") == AUDIT_PIN and sha(author/"core_audit_mechanical.py") == CORE_PIN
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
    # Source roles remain separate; this is an import closure/superset for the reference.
    refs = {n:pin for n,pin in source_map.items() if n.startswith("hf_repo/src/hf_eval/")}
    for name in MATH: refs["hf_repo/scripts/"+name] = source_map["hf_repo/scripts/"+name]
    counter = root/"lf_data_preparation/native_workpiece_001/coarse_square_cycle010_ref_003/counter_contract.py"
    assert sha(counter) == COUNTER_PIN
    refs[counter.relative_to(root).as_posix()] = COUNTER_PIN
    refs[launcher.relative_to(root).as_posix()] = LAUNCHER_PIN
    assert all(sha(root/n) == pin for n,pin in pins.items())
    installed.mkdir()
    for name in ("audit_shift_pose.py","core_audit_mechanical.py"):
        shutil.copyfile(author/name,installed/name)
        refs[(installed/name).relative_to(root).as_posix()] = sha(installed/name)
    own = Path(__file__).resolve(); copied_builder = installed/own.name
    shutil.copyfile(own,copied_builder)
    refs[copied_builder.relative_to(root).as_posix()] = sha(copied_builder)
    assert len({Path(n).name for n in refs}) == len(refs)
    contract = dict(schema_version="shift-square-reference-contract-1.0",
        production_stage=stage.relative_to(root).as_posix(),baseline_commit=inventory["baseline_commit"],
        limits=dict(helper_seconds=600,outer_seconds=660,sampled_RSS_bytes=RSS),workpiece=BODY,targets_mm=TARGETS,
        reference_sources=refs,input_inventory_sha256=sha(paths["input_inventory.json"]),
        production_receipt_sha256=sha(paths["execution_receipt.json"]),source_freeze_sha256=sha(paths["source_freeze.json"]),
        production_launch_file=production_launch.relative_to(root).as_posix(),production_launch_sha256=sha(production_launch),
        production_result_sha256=sha(result_file),production_model_sha256=sha(model_file),
        source_transition=inventory["source_transition"],
        scope="Fresh exhaustive reference for all accepted x71 pose-only states; no failed-state, pressure/clamp, energy or all-column qualification")
    assert freeze["source_transition"] == contract["source_transition"]
    write(contract_file,contract)
    pins.update(refs); pins[contract_file.relative_to(root).as_posix()] = sha(contract_file)
    argv = [(installed/"audit_shift_pose.py").relative_to(root).as_posix(),"--repo",str(root),
        "--input",stage.relative_to(root).as_posix(),"--output",output.relative_to(root).as_posix(),
        "--contract",contract_file.relative_to(root).as_posix(),"--time-limit","600"]
    write(protocol_file,dict(schema_version="shift-square-reference-protocol-1.0",bindings=pins,
        sampled_RSS_bytes=RSS,phases=dict(reference=dict(helper_seconds=600,outer_seconds=660,argv=argv)),
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
