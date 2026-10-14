import ast, hashlib, json, pathlib, re, subprocess
from datetime import datetime, timezone
ROOT=pathlib.Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
OUT=pathlib.Path("D:/hf-native-workpiece-api-author-20261015/LF_LINK_execution_closure_001")
S="lf_data_preparation/native_interface_001/lf_link_001/"
BASE="4fd70556402347c73029cf7070217efaf7a4ea13"
DEFAULT="hf_repo/src/hf_eval/native_response.py"
ALLOWED={".json",".py",".md",".txt",".log"}
reads={}
def raw(rel):
    p=ROOT/rel
    assert p.suffix.lower() in ALLOWED, ("forbidden byte read",rel)
    b=p.read_bytes()
    reads[rel]={"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
    return b
def j(rel): return json.loads(raw(rel).decode("utf-8"))
def sha(rel): return hashlib.sha256(raw(rel)).hexdigest()
protocol=j(S+"protocol.json")
launch=j(S+"link_launch.json")
receipt=j(S+"run_001/execution_receipt.json")
tests=j(S+"run_001/tests_summary.json")
linked=j(S+"run_001/linked_response.json")
index=j(S+"run_001/light_index.json")
test_stdout=raw(S+"run_001/tests_stdout.txt").decode("utf-8")
log=raw(S+"link_stdout.log").decode("utf-8")
original=j(protocol["original_response_file"])
reference=j(protocol["reference_file"])
production_receipt=j(protocol["production_receipt_file"])
reference_receipt=j(protocol["reference_execution_receipt_file"])
checks={}
def check(k,b):
    checks[k]=bool(b)
    assert b,k
check("protocol_sha",sha(S+"protocol.json")=="4ddc343278c59fb0532db93f6fae27c40ea2c9941e198d22fa500583405df1f1")
check("launch_helper_pass",launch["status"]==receipt["status"]=="pass" and launch["exit_code"]==0 and launch["stop_reason"] is None)
check("source_commit",launch["authorized_execution_source_commit"]==receipt["authorized_execution_source_commit"]==BASE)
check("one_launch",launch["invocations"]==1)
check("one_each_metadata_operation",all(v==1 for v in receipt["calls"].values()) and set(receipt["calls"])=={"tests_started","tests_completed","saved_summary_started","saved_summary_completed","response_writes","index_writes","installation_started","installation_completed"})
check("tests_counts",tests["status"]=="pass" and tests["unit_tests_run"]==receipt["unit_tests_run"]==16 and tests["unit_reference_calls"]==receipt["unit_reference_calls"]==23 and tests["failfast"] is True)
check("tests_methods",tests["test_methods"]==protocol["expected_test_methods"] and len(tests["test_methods"])==16)
observed_methods=re.findall(r"^(test_\w+) .* \.\.\. ok$",test_stdout.replace(chr(13),chr(10)),re.M)
check("tests_actual_stdout",observed_methods==tests["test_methods"] and "Ran 16 tests" in test_stdout and test_stdout.rstrip().endswith("OK"))
test_ast=ast.parse(raw(S+"test_partial_native_reference.py"))
source_methods=[n.name for n in ast.walk(test_ast) if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")]
check("tests_fixed_source_methods",sorted(source_methods)==tests["test_methods"])
check("windows_and_rss",tests["elapsed_seconds"]<60 and receipt["elapsed_seconds"]<180 and launch["elapsed_seconds"]<240 and receipt["helper_seconds"]==180 and launch["outer_seconds"]==240 and launch["sampled_RSS_limit_bytes"]==receipt["sampled_RSS_limit_bytes"]==8589934592 and launch["peak_sampled_tree_RSS_bytes"]<8589934592 and receipt["sampled_peak_RSS_bytes"]<8589934592)
check("no_new_scientific_calls_reported",all(receipt[k]==0 for k in ("new_NPZ_reads","new_gzip_reads","new_CSV_reads","media_decodes","new_plots","new_force_calls","new_tangent_calls","new_HP_calls","new_solver_calls","new_model_constructions")) and receipt["mechanical_hooks_monitored"] is False)
check("closed_seal",receipt["output_identity_seal"]=="complete_inside_original_helper_window")
for rel,pin in receipt["outputs"].items():
    b=raw(rel)
    check("sealed:"+rel,len(b)==pin["bytes"] and hashlib.sha256(b).hexdigest()==pin["sha256"])
check("sealed_output_count",len(receipt["outputs"])==67)
fixtures=[p for p in receipt["outputs"] if p.startswith(S+"run_001/tests/")]
check("fixture_count",len(fixtures)==63)
actual_run_files={p.relative_to(ROOT).as_posix() for p in (ROOT/S/"run_001").rglob("*") if p.is_file()}
check("run_directory_seal_complete",actual_run_files==set(receipt["outputs"])|{S+"run_001/execution_receipt.json"})
ref=linked["independent_reference"]
check("matched_partial",ref["status"]=="matched_partial" and ref["selected_reference_pass"] is True and ref["matched_state_indices"]==[13,16] and ref["matched_state_count"]==2 and ref["production_accepted_state_count"]==25 and ref["accepted_states"]==2 and ref["HP_calls_completed"]==4 and not ref["reasons"])
check("no_full_or_mechanical_upgrade",all(ref[k] is False for k in ("accepted_reference_pass","full_path_reference_pass","covers_all_accepted_states","HP_all_columns_qualified","contact_qualified","clamp_qualified","pressure_qualified","HF5_qualified")))
check("reference_inherited_two_states",reference["status"]=="pass" and reference["accepted_states"]==2 and reference["selected_accepted_indices"]==[13,16] and reference["HP_calls_started"]==reference["HP_calls_completed"]==4 and reference["production_accepted_states"]==25 and reference["public_API_association_performed"] is False)
check("reference_original_gates_unchanged",reference["gates"]==protocol["original_gates"])
common_keys=sorted((set(original)&set(linked))-{"independent_reference","views"})
check("original_common_fields_unchanged",all(linked[k]==original[k] for k in common_keys))
check("25_state_path_completed",linked["path"]["accepted_states"]==25 and linked["path"]["completed"] is True and linked["path"]["requested_endpoint_mm"]==linked["path"]["reached_displacement_mm"]==0)
check("index_response_binding",index["linked_response"]["sha256"]==sha(S+"run_001/linked_response.json") and index["independent_reference"]==ref and index["production_accepted_states"]==25 and index["selected_accepted_indices"]==index["original_target_indices"]==[13,16] and index["selected_targets_mm"]==[1.2,1.05])
check("index_physics_matches",index["physics"]==linked["physics"] and index["path"]==linked["path"] and index["source_flags"]==linked["producer_flags"])
check("four_views_and_five_index_media",linked["views"]["status"]=="matched" and len(linked["views"]["links"])==4 and index["images"][:4]==linked["views"]["links"] and len(index["images"])==5)
inherited=dict(production_receipt["outputs"])
inherited.update(reference_receipt["outputs"])
media=[]
for image in index["images"]:
    rel=image["path"]
    pin=protocol["inherited_media_bindings"][rel]
    observed_size=(ROOT/rel).stat().st_size
    check("media_seal_and_stat:"+rel,image["sha256"]==pin["sha256"]==protocol["bindings"][rel]==inherited[rel]["sha256"] and observed_size==pin["bytes"]==inherited[rel]["bytes"])
    media.append({"path":rel,"sha256":pin["sha256"],"bytes":observed_size,"review_basis":"inherited original producer seal and current stat only; no media byte read/hash/decode/pixel inspection"})
check("five_media_exact_set",{x["path"] for x in media}==set(protocol["media_files"]))
ordinary_bindings={rel:pin for rel,pin in protocol["bindings"].items() if rel not in protocol["media_files"]}
check("binding_counts",len(protocol["bindings"])==65 and len(ordinary_bindings)==60)
for rel,pin in ordinary_bindings.items(): check("ordinary_binding:"+rel,sha(rel)==pin)
candidate=raw(S+"candidate.native_response.py")
actual_default=raw(DEFAULT)
candidate_sha=hashlib.sha256(candidate).hexdigest()
check("default_installed_exact_candidate",actual_default==candidate and candidate_sha=="346a97b30f675ccf063de1720002f936adf90011e69231edd89e776ba4e70eaa" and receipt["actual_default_SHA256"]==receipt["candidate_SHA256"]==launch["actual_default_SHA256"]==candidate_sha and receipt["installation_complete"] is True and launch["installation_complete"] is True)
old=subprocess.run(["git","show",BASE+":"+DEFAULT],cwd=ROOT,check=True,stdout=subprocess.PIPE).stdout
check("old_default_source_pin",hashlib.sha256(old).hexdigest()==protocol["source_before_installation"]["sha256"]=="53bee087509f780ec5a62dae5b39a067e5f0df38f6fd7cc47311766ab3e2f14b")
def outside_reference(b):
    node=next(x for x in ast.parse(b).body if isinstance(x,ast.FunctionDef) and x.name=="_reference")
    lines=b.splitlines(keepends=True)
    return b"".join(lines[:node.lineno-1]),b"".join(lines[node.end_lineno:])
check("outside_reference_bytes_unchanged",outside_reference(old)==outside_reference(candidate))
default_changes=subprocess.run(["git","diff","--name-only","HEAD","--","hf_repo"],cwd=ROOT,check=True,stdout=subprocess.PIPE).stdout.decode().splitlines()
check("canonical_source_change_only_native_response",default_changes==[DEFAULT])
runtime_text=raw(S+"execute_lf_link.py").decode()
check("pinned_runtime_single_hf_import_boundary", "{'hf_eval','hf_eval.native_response'}" in runtime_text and "summarize_saved_native_result(" in runtime_text and "write_native_response(" in runtime_text)
root_path=OUT/"root_terminal_confirmation.json"
root_bytes=root_path.read_bytes()
root_record=json.loads(root_bytes)
check("root_ordinary_confirmation_binding",root_record["actual_tool_terminal"]["chunk"]=="ba13f2" and root_record["actual_tool_terminal"]["exit_code"]==0 and root_record["actual_helper_sealed_outputs"]==67 and root_record["actual_unit_tests"]==16 and root_record["actual_calls"]==receipt["calls"])
for rel,pin in root_record["ordinary_record_SHA256"].items(): check("root_ordinary_confirmation:"+rel,sha(rel)==pin)
check("root_record_serialization_correction_explicit","ordinary_record_correction" in root_record and (OUT/root_record["ordinary_record_correction"]["preserved_initial_record"]).is_file())
report={
 "schema_version":"L-LINK1-independent-actual-metadata-review-1.0",
 "card":"L-LINK1","status":"pass_actual_metadata_execution","blocking_findings":[],
 "reviewed_utc":datetime.now(timezone.utc).isoformat(),
 "authorized_execution_source_commit":BASE,"protocol_sha256":sha(S+"protocol.json"),
 "review_scope":"Read-only ordinary output/source/provenance audit; no test, API, scientific, plotting or installation execution by reviewer",
 "root_actual_tool_terminal_evidence":{"chunk":"ba13f2","exit_code":0,"basis":"Root-provided actual tool observation in bound root_terminal_confirmation.json; reviewer does not independently observe or backdate root tool terminal"},
 "root_terminal_confirmation_sha256":hashlib.sha256(root_bytes).hexdigest(),
 "ordinary_review_parser_correction":{"initial_tool_chunk":"500fdb","exit_code":1,"reason":"Reviewer regex omitted CRLF normalization; actual 16 ok tests unchanged. Preserved initial reviewer source. No card/API/test rerun."},
 "reviewer_tool_observation_history":[{"initial":"3987ab","exit_code":0},{"initial":"d85c51","session":29385,"terminal":"da7ae7","exit_code":0},{"initial":"b5c568","session":62758,"terminal":"6adba4","exit_code":0},{"initial":"d4666b","session":70783,"terminal":"f6da61","exit_code":0}],
 "observed_calls":receipt["calls"],"unit_tests_run":16,"unit_reference_calls":23,
 "test_methods":tests["test_methods"],"sealed_outputs":67,"test_fixture_outputs":63,
 "selected_reference":{"status":"matched_partial","indices":[13,16],"selected_states":2,"production_accepted_states":25,"existing_HP_calls":4,"selected_reference_pass":True,"accepted_reference_pass":False,"full_path_reference_pass":False},
 "timings_seconds":{"tests":tests["elapsed_seconds"],"helper_sealed":receipt["elapsed_seconds"],"child_terminal":launch["child_terminal_wall_seconds"],"outer":launch["elapsed_seconds"]},
 "sampled_RSS_bytes":{"helper":receipt["sampled_peak_RSS_bytes"],"outer_tree":launch["peak_sampled_tree_RSS_bytes"],"limit":8589934592},
 "source_installation":{"file":DEFAULT,"before_sha256":hashlib.sha256(old).hexdigest(),"candidate_and_installed_sha256":candidate_sha,"only_default_source_changed":True,"outside_reference_raw_bytes_unchanged":True},
 "unchanged_response_common_keys":common_keys,
 "original_only_response_keys":sorted(set(original)-set(linked)),
 "linked_only_response_keys":sorted(set(linked)-set(original)),
 "five_existing_media":media,"ordinary_read_identities":reads,
 "checks":checks,
 "limitations":[
 "A record/source audit does not constitute a fresh HP or mechanical run and does not re-audit NPZ or scientific gzip/CSV content.",
 "Zero new mechanics is supported by pinned stdlib-only source, receipt counters and the installed package boundary; no dynamic mechanical hook monitoring is claimed.",
 "The root tool terminal is root-provided evidence; this reviewer only owns its read-only inspection and external report write observations.",
 "Five media are checked through inherited producer SHA/size seals and current stat only; no postwindow raw media hashing, decoding, redraw or pixel inspection.",
 "Full 25-state independent reference, all-column tangent, pressure, effective clamp, release, stability and HF5 qualification remain ungranted.",
 "Original L-REF1 public_API_association_performed=false is historical original metadata; the new response association does not rewrite that original.",
 "The root ordinary count serialization correction changes the root record only; the original incorrect record is preserved and no test/API/install output was changed."
 ]
}
md="""# L-LINK1 实际结果独立审阅

审阅结论：PASS（普通元数据执行、关联与单文件安装范围），无阻断发现。

本次真实记录显示：16 个固定测试方法通过，测试私有参考入口计数 23；一次公共保存态摘要、一次响应写入、一次轻索引写入与一次安装均完成。封存 67 份普通输出，含 63 份测试夹具及 4 份其他输出；本审阅核对全部封存输出的实际 SHA256 与字节数，未重跑测试或 API。

新响应与轻索引均返回 matched_partial，索引为 13／16，两态覆盖 2／25 个生产接受态，并关联已有 4 次 HP80／120。selected_reference_pass=true；accepted_reference_pass、full_path_reference_pass 及压力、有效夹持、HF5 等资格保持 false。原 25 态前向路径及物理字段原值保持，原响应共有字段（参考与视图字段除外）逐项一致；原文件的字节身份仍与协议绑定一致。

默认安装文件仅为 hf_repo/src/hf_eval/native_response.py。实际默认文件等于候选字节，SHA256 为 346a97b30f675ccf063de1720002f936adf90011e69231edd89e776ba4e70eaa；与 4fd7055 的旧源码相比，_reference 之外的原始字节保持一致。机械源码与原门未修改。

资源实测：测试 %.12g 秒；helper 封存 %.12g 秒；child 终态 %.12g 秒；outer %.12g 秒，采样树内存峰值 %d 字节。均在 60／180／240 秒与 8 GiB 的本卡窗口内。这里沿用本卡采样与协作停止合同，不宣称 OS 硬限额。

五份既有媒体的链接身份与原生产封存、协议 SHA 一致，当前大小一致。本审阅仅读取普通 JSON／源码／日志；媒体只做 inherited seal＋stat。未读取媒体字节、像素、NPZ、科学 gzip 或 CSV；未新绘图、核力、求切线、HP 或平衡求解。原参考记录的 public_API_association_performed=false 仍保留为历史事实。

Root 的 ba13f2／exit0 工具终态来自其实际观察与绑定的确认记录，本审阅不代为背书自身未亲见的工具终态。Root 普通记录中 67 输出计数的 PowerShell 序列化错误已明确修正并保留初版；实际 helper 封存、结果、测试及安装输出均未更改。详细判断、读取身份、资源计数和限制见同名 JSON。
"""%(tests["elapsed_seconds"],receipt["elapsed_seconds"],launch["child_terminal_wall_seconds"],launch["elapsed_seconds"],launch["peak_sampled_tree_RSS_bytes"])
OUT.mkdir(parents=True,exist_ok=True)
for name,b in [("actual_execution_review.json",(json.dumps(report,ensure_ascii=False,indent=2)+"\n").encode("utf-8")),("actual_execution_review.md",md.encode("utf-8"))]:
    p=OUT/name
    with p.open("xb") as f: f.write(b)
    print(json.dumps({"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)},ensure_ascii=False))
print(json.dumps({"status":report["status"],"checks":len(checks),"blocking_findings":[],"ordinary_reads":len(reads)}))
