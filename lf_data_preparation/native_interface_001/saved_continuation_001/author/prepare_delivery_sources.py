"""Write future ordinary delivery sources and AST receipt; do not call them."""
import ast
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = Path("D:/hf-native-workpiece-api-author-20261009/MAVIEW1_execution_review_001")
BASE = "8b456dcdc2c0566fb2e927175a781712dd5e78ec"
REL = "lf_data_preparation/native_interface_001/saved_continuation_001"

checks = '''def execution_checks(root,external,config,entries):
    """Bind a completed outer and actual saved records; never replay science."""
    stage = root/REL
    status = config["execution_status"]
    assert config["source_commit"] == BASE and status in ("pass","not_pass")
    assert config["authorized"] is config["executed"] is config["execution_closed"] is True
    protocol_file = stage/"protocol.json"
    assert entries[REL+"/protocol.json"]["sha256"] == config["protocol_sha256"]
    protocol = read(protocol_file)
    assert protocol["card"] == "M-RESUME1" and protocol["prepared"] is True
    assert protocol["authorized"] is protocol["executed"] is False
    assert len(protocol["bindings"]) == 100 and protocol["bindings"] == config["binding_pins"]
    assert all(entries[name]["sha256"] == pin for name,pin in config["binding_pins"].items())
    assert {path.relative_to(root).as_posix() for path in stage.rglob("*") if path.is_file()} == {
        name for name in entries if name.startswith(REL+"/")}
    auth,reply = read(stage/"author/authorization.json"),read(stage/"author/direct_human_reply.json")
    assert auth["authorized"] is True and auth["card"] == reply["card"] == "M-RESUME1"
    assert auth["approved_source_commit"] == reply["approved_source_commit"] == BASE
    assert auth["protocol_sha256"] == config["protocol_sha256"]
    assert auth["authorization_from_direct_human_reply"] is reply["authorization_from_direct_human_reply"] is True
    assert auth["human_evidence_sha256"] == entries[REL+"/author/direct_human_reply.json"]["sha256"]
    assert auth["source_publication_receipt_sha256"] == config["previous_publication_receipt"]["sha256"]
    assert auth["direct_human_answer"] == reply["direct_human_answer"] and reply["direct_human_answer"].strip() and reply["reply_context"]
    outer_name = REL+"/production_launch.json"
    outer = read(root/outer_name)
    assert outer["status"] == status and outer["completed_utc"] and outer["phase"] == "production" and outer["invocations"] == 1
    assert outer["protocol_sha256"] == config["protocol_sha256"] and outer["bindings"] == protocol["bindings"]
    terminal_name = config["terminal_review_path"]
    assert terminal_name in config["review_pins"]
    terminal = read(root/terminal_name)
    assert terminal["status"].startswith("pass") and terminal["execution_status"] == status
    assert terminal["outer_sha256"] == entries[outer_name]["sha256"]
    # NOT_PASS may lack a completed helper or complete result/view. Preserve real
    # files and the independent terminal classification, rather than invent them.
    run = stage/"run_001"
    helper_file = run/"execution_receipt.json"
    if status == "pass":
        helper = read(helper_file)
        assert outer["exit_code"] == 0 and outer["stop_reason"] is None and outer["all_bindings_unchanged"] is True
        assert helper is not None and helper["status"] == "pass" and helper["all_bindings_unchanged"] is True
        assert helper["protocol_sha256"] == config["protocol_sha256"] and helper["approved_source_commit"] == BASE
        assert helper["cached_production_gates"]["passed"] is True
        assert helper["HP_calls"] == helper["JIT_calls"] == 0
        N = helper["accepted_states"]
        assert 2 <= N <= 9 and all(helper["counts"][kind+suffix] == 1
            for kind in ("focused_tests","api","model","solve","save","summary","view_child") for suffix in ("_started","_completed"))
        tests = read(run/"focused_test_receipt.json")
        assert tests["status"] == "pass" and tests["collected_nodeids"] == protocol["focused_test_nodeids"]
        result = read(root/protocol["candidate_directory"]/"result.json")
        assert result["status"] == "success" and result["path_completed"] is True and result["unload_endpoint_reached"] is True
        assert result["accepted_states"] == len(result["states"]) == N and result["targets_mm"] == [1.2,1.15]
        assert result["task_target_executed"] is result["full_original_path_completed"] is False
        continuation = result["continuation"]
        assert continuation["segment_completed"] is continuation["anchor_revalidated"] is continuation["anchor_identity_preserved"] is True
        assert continuation["parent_status"] == "failed" and continuation["parent_failure"]["code"] == "time_limit"
        assert continuation["parent_path_completed"] is continuation["parent_task_target_executed"] is continuation["parent_unload_endpoint_reached"] is False
        assert continuation["full_original_path_executed_by_child"] is False and continuation["original_target_indices"] == [13,14]
        originals = [row for row in result["states"] if row["is_original_target"]]
        assert [(row["d"],row["original_target_index"],row["leg"]) for row in originals] == [(1.2,13,"resume_origin"),(1.15,14,"unloading")]
        assert all(result[flag] is False for flag in ("independent_HP_qualified","equilibrium_qualified","HF_qualified"))
        views = read(root/protocol["view_directory"]/"view.json")
        assert views["status"] == "pass" and all(views[key] == N for key in ("geometry_started","geometry_completed","nodal_started","nodal_completed"))
        assert views["new_F_T_model_solver_HP_calls"] == 0 and views["contact_pressure_clamping_qualified"] is False
        assert helper["actual_PNGs"] == 3 and helper["actual_GIF_frames"] == N
        assert helper["production_selected_NPZ_files"] == 2 and helper["production_selected_fields"] == 6
        assert helper["original_parent_full_path_still_NOT_PASS"] is True and helper["new_HP_pressure_clamp_stability_HF5_qualified"] is False
        output_names = {path.relative_to(root).as_posix() for path in run.rglob("*") if path.is_file()}
        assert output_names == helper["outputs"].keys() | {helper_file.relative_to(root).as_posix()}
        assert all(entries[name]["sha256"] == pin for name,pin in helper["outputs"].items())
        assert helper["executed_source_package_unchanged"] is True
        assert all(entries[name]["sha256"] == pin for name,pin in helper["executed_source_package_SHA256"].items())
    else:
        assert outer["exit_code"] != 0 or outer["stop_reason"] is not None or outer["all_bindings_unchanged"] is False
        # A partial/missing/malformed helper is preserved as raw evidence and
        # classified by the independent terminal review, not parsed as success.
    assert len(config["review_pins"]) >= 3 and all(entries[name]["sha256"] == pin for name,pin in config["review_pins"].items())
    doc_name = config["documentation_receipt_path"]
    assert doc_name.startswith(REL+"/author/")
    doc = read(root/doc_name)
    assert doc["status"] == "pass_actual_execution_documentation_closed" and doc["execution_closed"] is True
    assert doc["source_commit"] == BASE and doc["protocol_sha256"] == config["protocol_sha256"] and doc["execution_status"] == status
    assert doc["result_sha256"] == entries[REL+"/RESULTS.md"]["sha256"] and doc["next_step_sha256"] == entries[REL+"/NEXT_STEP_REVIEW.md"]["sha256"]
    assert doc["front_history"] == config["front_history"]
    assert doc["actions"] and all(value == 0 for value in doc["actions"].values())
    assert doc["qualification"] and all(value is False for value in doc["qualification"].values())
    assert {row["path"] for row in config["front_history"]} == FRONTS and len(config["front_history"]) == 2
    for row in config["front_history"]:
        prior,current = git(root,"show",BASE+":"+row["path"]),(root/row["path"]).read_bytes()
        assert current.count(prior) == 1 and len(prior) == row["old_bytes"]
        assert digest(prior) == row["old_sha256"] and entries[row["path"]]["sha256"] == row["new_sha256"]
        assert row["history_end_byte_exclusive"] == row["history_start_byte"]+len(prior)
        assert current[row["history_start_byte"]:row["history_end_byte_exclusive"]] == prior
        assert row["old_body_preserved_exactly"] is True
    final_name = config["final_review_path"]
    assert final_name.startswith(REL+"/author/") and final_name in config["allowed_delta_paths"]
    final = read(root/final_name)
    assert final["status"].startswith("pass") and final["config_sha256"] == sha(root/CONFIG)
    assert final["authorized"] is final["executed"] is final["execution_closed"] is True and final["execution_status"] == status
    expected_reviewed = (set(config["allowed_delta_paths"])-{final_name}) | set(config["binding_pins"])
    assert expected_reviewed <= final["reviewed_repository_SHA256"].keys() and final_name not in final["reviewed_repository_SHA256"]
    assert final["reviewed_external_SHA256"]["deliver_execution.py"] == sha(external/"deliver_execution.py")
    for name,pin in final["reviewed_external_SHA256"].items():
        path = (external/name).resolve(); path.relative_to(external)
        assert sha(path) == pin
    for name,pin in final["reviewed_repository_SHA256"].items():
        assert entries[name]["sha256"] == pin
    assert entries[REL+"/author/deliver_execution.py"]["sha256"] == sha(external/"deliver_execution.py")
    return protocol


'''
deliver = (OLD/"deliver_execution.py").read_text(encoding="utf-8")
start,end = deliver.index("def execution_checks("),deliver.index("def main():")
deliver = deliver[:start]+checks+deliver[end:]
deliver = deliver.replace("7887aa1138f8e46a2b15f47a1060aa7d72cfe651",BASE).replace("functional_views/native_alpha_partial_20261011/complete_001",REL)
deliver = deliver.replace("M-AVIEW1","M-RESUME1").replace("alpha_partial_saved_views_execution_closed_001","saved_native_continuation_execution_closed_001")
deliver = deliver.replace("completed display delivery","completed saved-start delivery")
deliver = deliver.replace('execution_status="pass"','execution_status=config["execution_status"]')
deliver = deliver.replace('source["execution_status"] == "pass"','source["execution_status"] == config["execution_status"]')
anchor = 'assert old["science_version"] == "0.5.0"'
deliver = deliver.replace(anchor,anchor+'\n    assert len(entries) == 18915 and sum(row["bytes"] for row in entries.values()) == 9657472556\n    assert len([name for name in entries if name.startswith(REL+"/")]) == 43')
(HERE/"deliver_execution.py").write_text(deliver,encoding="utf-8")

configure = (OLD/"configure_execution_delivery.py").read_text(encoding="utf-8")
configure = configure.replace("7887aa1138f8e46a2b15f47a1060aa7d72cfe651",BASE).replace("functional_views/native_alpha_partial_20261011/complete_001",REL).replace("M-AVIEW1","M-RESUME1").replace("M_AVIEW1","M_RESUME1")
configure = configure.replace('"execution_documentation_physics_review.json",','"execution_documentation_physics_review.json",')
configure = configure.replace('        "delivery_tool_author_receipt.json", "author_delivery_source.py",','        "delivery_tool_author_receipt.json", "prepare_delivery_sources.py",')
configure = configure.replace('    protocol = read(STAGE / "protocol.json")','    protocol = read(STAGE / "protocol.json")\n    outer = read(STAGE / "production_launch.json")\n    assert outer["status"] in ("pass", "not_pass") and outer["completed_utc"]\n    execution_status = outer["status"]')
configure = configure.replace('    assert documentation["source_commit"] == BASE','    assert documentation["source_commit"] == BASE and documentation["execution_status"] == execution_status\n    assert documentation["protocol_sha256"] == sha(STAGE / "protocol.json")')
configure = configure.replace('source_commit=BASE, execution_status="pass"','source_commit=BASE, execution_status=execution_status')
configure = configure.replace('        documentation_receipt_path=','        terminal_review_path=REL + "/author/execution_terminal_review.json",\n        documentation_receipt_path=')
configure = configure.replace('original_unload_completed=False','original_parent_full_path_completed=False')
(HERE/"configure_execution_delivery.py").write_text(configure,encoding="utf-8")

files = {}
for name in ("deliver_execution.py","configure_execution_delivery.py"):
    raw = (HERE/name).read_bytes()
    tree = ast.parse(raw,filename=name)
    files[name] = dict(sha256=sha256(raw).hexdigest(),bytes=len(raw),AST="parsed_without_import_or_execution",
                      functions=sum(isinstance(n,ast.FunctionDef) for n in ast.walk(tree)))
receipt = dict(status="prepared_execution_metadata_tools_source_AST_only_not_executed",card="M-RESUME1",
    source_commit=BASE,metadata_publication_executed=False,numerical_run_status="Not inspected; no future terminal claims",
    sources=files,adapted_from={name:sha256((OLD/name).read_bytes()).hexdigest() for name in files},
    ordinary_manifest_inherited_files=18915,ordinary_manifest_inherited_bytes=9657472556,
    prior_stage_files_preserved=43,original_binding_pins_preserved=100,
    actual_actions=dict(delivery_tool_execution=0,configuration_execution=0,formal_repository_write=0,
        HF_import=0,NPZ_decode=0,tests=0,force=0,tangent=0,solver=0,observer=0,HP=0,JIT=0,render=0,Git_commit_push=0),
    limitations="Future terminal/doc/config/final review real records are required. Metadata PASS is not numerical PASS; not_pass retains actual partial files. No run or source-core integration.")
receipt["notes_sha256"] = sha256((HERE/"DELIVERY_TOOL_SOURCE_NOTES.md").read_bytes()).hexdigest()
receipt["source_generator_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
(HERE/"delivery_tool_author_receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(status=receipt["status"],sources=files,receipt_sha256=sha256((HERE/"delivery_tool_author_receipt.json").read_bytes()).hexdigest()),indent=2))
