"""Review this actual PASS document-writer source and ordinary saved records."""
import ast
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
REL = "lf_data_preparation/native_interface_001/saved_continuation_001"
STAGE = ROOT/REL
raw = (HERE/"close_resume_docs.py").read_bytes()
ast.parse(raw,filename="close_resume_docs.py")
names = ("production_launch.json","run_001/execution_receipt.json","run_001/focused_test_receipt.json",
         "run_001/resumed_alpha_half/result.json","run_001/resumed_alpha_half/response.json","run_001/view/view.json")
records = {name:json.loads((STAGE/name).read_bytes()) for name in names}
outer,helper,tests,result,response,view = (records[name] for name in names)
assert outer["status"] == helper["status"] == tests["status"] == view["status"] == "pass"
assert outer["exit_code"] == 0 and outer["completed_utc"]
assert result["status"] == response["status"] == "success" and len(result["states"]) == 2
assert result["failure"] is response["failure"] is None
assert [(row["d"],row["leg"],row["original_target_index"],row["newton_checks"],row["bisection_depth"])
        for row in result["states"]] == [(1.2,"resume_origin",13,1,0),(1.15,"unloading",14,8,0)]
assert result["path_diagnostics"]["maximum_bisection_depth"] == 0
trials = result["path_diagnostics"]["trials"]
assert len(trials) == 8 and trials[0]["accepted"] is False and trials[0]["reason"] == "invalid_J"
assert trials[0]["factor"] == 1. and trials[1]["factor"] == .5 and all(row["accepted"] is True for row in trials[1:])
assert (helper["counts"]["force_started"],helper["counts"]["force_completed"],helper["counts"]["tangent_started"],helper["counts"]["tangent_completed"]) == (17,16,9,9)
assert helper["actual_PNGs"] == 3 and helper["actual_GIF_frames"] == 2
assert helper["save_extra_force_tangent_calls"] == helper["summary_extra_force_tangent_calls"] == 0
pixel = json.loads((HERE/"root_pixel_review.json").read_bytes())
assert pixel["status"] == "pass_actual_three_PNG_pixel_inspection_no_new_render" and pixel["actual_PNGs_inspected"] == 3
for name,pin in pixel["inspected_repository_SHA256"].items():
    assert sha256((ROOT/name).read_bytes()).hexdigest() == pin
assert result["full_original_path_completed"] is result["task_target_executed"] is False
assert result["continuation"]["parent_status"] == "failed" and result["continuation"]["anchor_identity_preserved"] is True
report = dict(status="pass_static_actual_success_documentation_writer_and_pixel_record_no_execution",
    card="M-RESUME1",document_tool_executed=False,formal_repository_written=False,
    reviewed_external_SHA256={name:sha256((HERE/name).read_bytes()).hexdigest() for name in ("close_resume_docs.py","root_pixel_review.json")},
    reviewed_repository_SHA256={REL+"/"+name:sha256((STAGE/name).read_bytes()).hexdigest() for name in names},
    actual_saved_record_facts=dict(saved_states=2,initial_anchor_newton_checks=1,descending_newton_checks=8,
        accepted_line_search_corrections=7,rejected_invalid_J_trial=1,maximum_bisection_depth=0,
        force_started=17,force_completed=16,tangent_started=9,tangent_completed=9,PNG=3,GIF_frames=2),
    checks=[
        "The revised writer is explicitly one-off actualPASS/exit0/completed; it does not claim general NOT_PASS or malformed-partial closure support.",
        "Required helper/test/progress/result/view artifacts and actualN2/3PNG/2frame are prerequisites, so previous generic missing-link/default0 findings do not apply to these real present records.",
        "Visualization requires rawview statuspass, actual artifact presence and root's threePNG pixel report; GIF all-frame manual inspection is explicitly not claimed.",
        "Eight descending Newton checks/seven accepted corrections/zero bisections match ordinary saved diagnostics; rejected invalidJ trial is not a saved acceptedstate or terminal failure/retry.",
        "Failure remains actual null; started/completed F17/16 and T9/9 and save/summary extraF/T0 match existing receipts, separate from tinytest accounting.",
        "Only RESULTS/NEXT/author archives and two oldfronts are written. BASE oldfront raw bytes are included once with SHA and exact history offsets; frozen prepared docs/core remain untouched.",
        "Candidate remains isolated/not installed; rawsource history falseprepared flags remain history. Parent failed/fullpath/task flags and new child suffix are distinct.",
        "Existing native geometry/API/Mean/fullmatrix/batch/view capabilities are separated from arbitrary new LF-task qualification; no new HP/pressure/clamp/stability/HF5 qualification is awarded."
    ],
    remaining_blockers=[],prerequisites="Actual terminal and physical review files must exist before root runs this source. At this review time their external files were still pending and are not claimed inspected; final produced docs/packet need later actual ordinary review.",
    actual_actions=dict(document_tool_execution=0,HF_import=0,NPZ_decode=0,new_scientific_metrics=0,
                        tests=0,force=0,tangent=0,solver=0,observer=0,HP=0,render=0,formal_repository_mutation=0))
(HERE/"DOC_TOOL_FINAL_STATIC_REVIEW.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
md = """# M-RESUME1 实际PASS封账工具最终源码静审

结论：修订后的单次 actualPASS 文档工具静审通过。它明确要求真实完成／exit0、实际2接受态、3PNG／2帧及所需产物；不再声称一般失败／缺失字段／malformed封账能力。先前findings作为旧源审阅历史保留。

普通JSON核对：锚点1次fresh检查、下降8次Newton检查和7次接受修正，无二分；最初factor1的invalid_J trial被拒绝后factor.5接受。F17started／16completed和T9／9是实际迭代计数，trial不当作保存接受态，失败null保留，save／summary额外F/T0。没有计算新科学差值或重做机械门。

root_pixel_review原字节绑定三张既存PNG，像素检查归属于root；未声称本审阅者亲看像素或人工检查GIF所有帧。显示分支与真实完成图件相符。父NOT_PASS／childsuffix／资格分开；默认候选仍未安装，已有接口与更广几何／任务验证范围区分。

旧准备文档和core不写；仅两front保留BASE完整原字节一次并记录SHA／偏移，新RESULTS/NEXT和普通归档承载实际进度。本次只source／AST／普通JSON与图原字节SHA，不执行封账、NPZ、HF、测试或绘图，不修改正式仓库。

实际terminal／physical外部报告此时仍待生成，需先存在再由root运行工具；本审阅不声称已看过它们或封账已运行，后续实际文档／发布packet仍需最终普通审阅。精确源与记录绑定见DOC_TOOL_FINAL_STATIC_REVIEW.json。
"""
(HERE/"DOC_TOOL_FINAL_STATIC_REVIEW.md").write_text(md,encoding="utf-8")
print(json.dumps(dict(status=report["status"],source_sha256=report["reviewed_external_SHA256"]["close_resume_docs.py"],
    JSON_sha256=sha256((HERE/"DOC_TOOL_FINAL_STATIC_REVIEW.json").read_bytes()).hexdigest(),
    MD_sha256=sha256((HERE/"DOC_TOOL_FINAL_STATIC_REVIEW.md").read_bytes()).hexdigest()),indent=2))
