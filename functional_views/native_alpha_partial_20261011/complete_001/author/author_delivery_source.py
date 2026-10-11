"""Ordinary text adaptation of the reviewed preparation tool; never executes it."""
import ast
from pathlib import Path

root = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
external = Path(__file__).resolve().parent
source = (root/"functional_views/native_alpha_partial_20261011/complete_001/author/deliver_view_preparation.py").read_text(encoding="utf-8")
changes = {
    'Incremental M-AVIEW1 source preparation delivery; ordinary metadata only.': 'Incremental M-AVIEW1 completed display delivery; ordinary metadata only.',
    'BASE = "9e2e37cce7f0441af042337d1c26c50ae660acc0"': 'BASE = "7887aa1138f8e46a2b15f47a1060aa7d72cfe651"',
    'CONFIG = REL+"/author/preparation_delivery_config.json"': 'CONFIG = REL+"/author/execution_delivery_config.json"',
    'assert proof["execution_status"] == "not_pass" and proof["execution_closed"] is True': 'assert proof["prepared_card"] == "M-AVIEW1" and proof["prepared"] is True\n    assert proof["authorized"] is False and proof["executed"] is False',
    '    assert not any(name.startswith(REL+"/") for name in entries)\n': '',
    'preparation_delivery_delta_verify.json': 'execution_delivery_delta_verify.json',
    'protocol = preparation_checks(root,external,config,entries)': 'protocol = execution_checks(root,external,config,entries)',
    'protocol = preparation_checks(restore,external,config,entries)': 'protocol = execution_checks(restore,external,config,entries)',
    'alpha_partial_saved_views_prepared_001': 'alpha_partial_saved_views_execution_closed_001',
    'incremental_preparation_delivery_pass': 'incremental_execution_delivery_pass',
    'prepared=True,authorized=False,executed=False,new_full_source_scan=False': 'execution_status="pass",authorized=True,executed=True,execution_closed=True,new_full_source_scan=False',
    'assert source["prepared_card"] == "M-AVIEW1" and source["authorized"] is False and source["executed"] is False': 'assert source["executed_card"] == "M-AVIEW1" and source["execution_status"] == "pass"\n        assert source["authorized"] is True and source["executed"] is True and source["execution_closed"] is True',
    'previous_publication_receipt=config["previous_publication_receipt"],prepared_card="M-AVIEW1"': 'previous_publication_receipt=config["previous_publication_receipt"],executed_card="M-AVIEW1"',
    'prepared_card="M-AVIEW1",prepared=True,authorized=False,executed=False': 'executed_card="M-AVIEW1",execution_status="pass",authorized=True,executed=True,execution_closed=True',
    'write_new(external/"publication_receipt.json",receipt)': 'write_new(external/"execution_publication_receipt.json",receipt)',
}
for before,after in changes.items():
    assert source.count(before) >= 1, before
    source = source.replace(before,after)
start,end = source.index('def preparation_checks('),source.index('\n\ndef main():')
checks = '''def execution_checks(root,external,config,entries):
    """Bind already-completed view records and closure; no scientific replay."""
    stage = root/REL
    assert config["source_commit"] == BASE and config["execution_status"] == "pass"
    protocol_file = stage/"protocol.json"
    assert entries[REL+"/protocol.json"]["sha256"] == config["protocol_sha256"]
    protocol = read(protocol_file)
    assert protocol["card"] == "M-AVIEW1" and protocol["prepared"] is True
    assert protocol["authorized"] is False and protocol["executed"] is False
    assert len(protocol["bindings"]) == 77 and protocol["bindings"] == config["binding_pins"]
    assert all(entries[name]["sha256"] == pin for name,pin in config["binding_pins"].items())
    assert {path.relative_to(root).as_posix() for path in stage.rglob("*") if path.is_file()} == {
        name for name in entries if name.startswith(REL+"/")}
    auth,reply = read(stage/"author/authorization.json"),read(stage/"author/direct_human_reply.json")
    assert auth["authorized"] is True and auth["card"] == reply["card"] == "M-AVIEW1"
    assert auth["approved_source_commit"] == reply["approved_source_commit"] == BASE
    assert auth["protocol_sha256"] == config["protocol_sha256"]
    assert auth["authorization_from_direct_human_reply"] is True and reply["authorization_from_direct_human_reply"] is True
    assert auth["human_evidence_sha256"] == entries[REL+"/author/direct_human_reply.json"]["sha256"]
    assert auth["source_publication_receipt_sha256"] == config["previous_publication_receipt"]["sha256"]
    assert auth["direct_human_answer"] == reply["direct_human_answer"] and reply["direct_human_answer"].strip() and reply["reply_context"]
    outer = read(stage/"view_launch.json")
    out = root/protocol["view_directory"]
    helper,raw = read(out/"alpha_partial_view_receipt.json"),read(out/"view.json")
    assert outer["status"] == helper["status"] == raw["status"] == "pass"
    assert outer["phase"] == "view" and outer["invocations"] == 1 and outer["exit_code"] == 0 and outer["completed_utc"]
    assert outer["protocol_sha256"] == helper["protocol_sha256"] == config["protocol_sha256"]
    assert outer["bindings"] == protocol["bindings"] and outer["all_bindings_unchanged"] is True and helper["all_bindings_unchanged"] is True
    assert helper["accepted_states"] == helper["matched_original_targets"] == helper["gif_frames"] == 14
    assert all(value == 14 for value in helper["actual_observation_counts"].values())
    assert all(raw[name] == 14 for name in ("geometry_started","geometry_completed","nodal_started","nodal_completed"))
    assert helper["original_production_status"] == "failed" and helper["original_failure"]["code"] == "time_limit"
    assert helper["original_path_completed"] is False and helper["original_unload_endpoint_reached"] is False
    assert helper["new_mechanical_calls"] == helper["new_baseline_observer_calls"] == raw["new_F_T_model_solver_HP_calls"] == 0
    assert helper["stability_pressure_clamp_HF5_qualified"] is False and raw["contact_pressure_clamping_qualified"] is False
    assert helper["mechanical_hooks_monitored"] is False and raw["mechanical_hooks_monitored"] is False
    output_names = {path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file()}
    assert output_names == helper["outputs"].keys() | {"alpha_partial_view_receipt.json"}
    assert all(entries[(out/name).relative_to(root).as_posix()]["sha256"] == pin for name,pin in helper["outputs"].items())
    assert len(config["review_pins"]) >= 3
    assert all(entries[name]["sha256"] == pin for name,pin in config["review_pins"].items())
    doc_name = config["documentation_receipt_path"]
    assert doc_name.startswith(REL+"/author/")
    doc = read(root/doc_name)
    assert doc["status"] == "pass_actual_execution_documentation_closed" and doc["execution_closed"] is True
    assert doc["source_commit"] == BASE and doc["protocol_sha256"] == config["protocol_sha256"] and doc["execution_status"] == "pass"
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
    assert final["authorized"] is True and final["executed"] is True and final["execution_closed"] is True and final["execution_status"] == "pass"
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
source = source[:start]+checks+source[end:]
ast.parse(source,filename=str(external/"deliver_execution.py"))
with (external/"deliver_execution.py").open("x",encoding="utf-8",newline="\n") as stream:
    stream.write(source)
print("source written and AST parsed; deliver tool not executed")
