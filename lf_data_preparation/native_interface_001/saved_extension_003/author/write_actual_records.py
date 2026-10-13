"""Candidate ordinary-record closure writer; do not run before root terminal confirmation.

No HF/scientific module, array, gzip, CSV, image or ZIP is imported or opened.
The only future formal writes are RESULTS, two complete-history fronts and one
ordinary documentation receipt. Root must review this source before invoking it.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess


BASE = "3cf11e92bedb791855c7b01d314668eba1116ac6"
PROTOCOL_SHA = "4980f164fdeface2839d6c0371d36a2ce4d310097d84d3991c2ba4266bc6ef5b"
REVIEW_JSON_SHA = "ee0593a3fcac4f1fa137377c24071e65b0b6442e77fb26c5f77d8be73fafe388"
REVIEW_MD_SHA = "6ee5481e40385896f29f0b62c9e0b83b96a5456be000c955a23accd626817b92"
REL = "lf_data_preparation/native_interface_001/saved_extension_003"
LABEL = "unloaded_alpha_half"
FRONTS = ("docs/CURRENT_STATUS.md", "docs/RESUME_DEVELOPMENT.md")


def read_json(path):
    path = Path(path)
    if path.suffix.lower() != ".json":
        raise ValueError("Only explicitly named ordinary JSON inputs are allowed")
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Expected an ordinary JSON object: " + str(path))
    return value, sha256(raw).hexdigest()


def display(value):
    if value is None:
        return "未记录"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return format(value, ".12g")  # Display formatting only, no new physics.
    return str(value).replace("|", "\\|").replace("\n", " ")


def recorded(record, *names):
    return next((record[name] for name in names if name in record), None)


def gate_text(receipt):
    cached = receipt.get("cached_production_gates", {})
    return json.dumps(cached, ensure_ascii=False, indent=2, allow_nan=False)


def state_tables(result, summary):
    states, rows = result["states"], summary["rows"]
    n = result["accepted_states"]
    assert n == len(states) == summary["accepted_states"] == len(rows) and n >= 2
    required = ("R_input_N", "q_out_mm", "tip_to_bottom_mm", "solid_min_J", "medium_max_abs_Hu_per_mm",
                "solid_Green_principal_max", "total_body_Fx_N", "total_body_Fy_N",
                "material_body_Fx_N", "material_body_Fy_N",
                "regularization_body_Fx_N", "regularization_body_Fy_N")
    joined = []
    for index, (state, row) in enumerate(zip(states, rows)):
        assert row["index"] == index
        assert row["state_sha256"] == state["state_sha256"] and row["d_mm"] == state["d"]
        assert row["original_target_index"] == state["original_target_index"]
        assert all(key in row for key in required) and "q_in" in state
        assert row["R_input_N"] == state["R_input"] and row["q_out_mm"] == state["q_out"]
        joined.append(dict(row, q_in_mm=state["q_in"]))
    assert states[0]["original_target_index"] == 15 and states[0]["d"] == 1.1
    assert states[-1]["original_target_index"] == 16 and states[-1]["d"] == 1.05
    assert states[-1]["is_original_target"] and not states[-1]["continuation_anchor"]
    headings = [
        (["child/global", "输入d mm", "qin mm", "R N", "qout mm", "有限底边间隙 mm", "solid minJ", "solid最大Green主应变", "medium最大abs Hu /mm"],
         [("q_in_mm",), ("R_input_N",), ("q_out_mm",), ("tip_to_bottom_mm",), ("solid_min_J",), ("solid_Green_principal_max",), ("medium_max_abs_Hu_per_mm",)]),
        (["child/global", "total Fx N", "total Fy N", "material Fx N", "material Fy N", "Hu Fx N", "Hu Fy N"],
         [("total_body_Fx_N",), ("total_body_Fy_N",), ("material_body_Fx_N",), ("material_body_Fy_N",), ("regularization_body_Fx_N",), ("regularization_body_Fy_N",)])
    ]
    tables = []
    for group, (labels, fields) in enumerate(headings):
        lines = ["| " + " | ".join(labels) + " |", "| " + " | ".join(["---"] * len(labels)) + " |"]
        for row in joined:
            values = [str(row["index"]) + "/" + str(row["original_target_index"])]
            if group == 0:
                values.append(display(row["d_mm"]))
            values.extend(display(row[name[0]]) for name in fields)
            lines.append("| " + " | ".join(values) + " |")
        tables.append("\n".join(lines))
    return "\n\n".join(tables), n


def partial_text(result):
    if result is None:
        return "唯一API未留下可读取的result.json；这里只保留真实异常，未补造接受态或1.05终点。"
    states = result.get("states", [])
    rows = []
    for index, state in enumerate(states):
        rows.append({key: state.get(key) for key in ("d", "q_in", "R_input", "q_out", "original_target_index", "leg", "state_sha256")} | {"accepted_index": index})
    return "原保存result状态为 " + display(result.get("status")) + "；以下仅列实际保存接受态，不把partial补为新终点：\n\n```json\n" + json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n```"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--confirmation", type=Path, required=True)
    parser.add_argument("--terminal-review", type=Path, required=True)
    parser.add_argument("--terminal-review-md", type=Path)
    parser.add_argument("--pixel-qa", type=Path)
    args = parser.parse_args()
    root = args.repo.resolve()
    stage, run = root / REL, root / REL / "run_001"
    confirmation, confirmation_sha = read_json(args.confirmation)
    assert confirmation["card"] == "M-UNLOAD1" and confirmation["unified_exec_session_id"] == 20354
    assert confirmation["root_observed_same_session_terminal"] is True and confirmation["execution_closed"] is True
    assert type(confirmation["tool_terminal_exit_code"]) is int and confirmation["recorded_utc"]
    assert confirmation["source_baseline_commit"] == BASE
    assert confirmation["execution_status"] in {"pass", "not_pass"}
    assert confirmation["actual_HP_tests_new_solver_or_plot_calls_by_observation"] == 0
    receipt, receipt_sha = read_json(run / "execution_receipt.json")
    outer, outer_sha = read_json(stage / "production_launch.json")
    review, review_sha = read_json(args.terminal_review)
    assert confirmation["execution_receipt_sha256"] == receipt_sha
    assert confirmation["outer_sha256"] == outer_sha
    assert review_sha == REVIEW_JSON_SHA
    assert outer["exit_code"] == confirmation["tool_terminal_exit_code"] and outer["status"] != "running"
    assert confirmation["execution_status"] == outer["status"]
    assert receipt["status"] != "running" and review.get("status")
    assert outer["invocations"] == 1
    assert receipt["approved_source_commit"] == review["approved_source_commit"] == BASE
    assert receipt["protocol_sha256"] == outer["protocol_sha256"] == review["protocol_SHA256"] == PROTOCOL_SHA
    assert review["outer_sha256"] == outer_sha and review["execution_closed"] is True
    assert review["authorized"] is review["executed"] is True
    review_md_file = args.terminal_review_md or args.terminal_review.with_suffix(".md")
    assert review_md_file.suffix.lower() == ".md"
    review_md_raw = review_md_file.read_bytes()
    assert sha256(review_md_raw).hexdigest() == REVIEW_MD_SHA
    protocol, protocol_sha = read_json(stage / "protocol.json")
    assert protocol_sha == PROTOCOL_SHA and protocol["card"] == "M-UNLOAD1"
    passed = (confirmation["execution_status"] == "pass"
              and review["execution_status"] == "pass"
              and str(review["status"]).startswith("pass") and review.get("blocking_findings", []) == [])
    if passed:
        assert outer["status"] == receipt["status"] == "pass" and outer["exit_code"] == 0
        assert review["execution_status"] == "pass" and str(review["status"]).startswith("pass")
        assert outer.get("stop_reason") is None and review.get("blocking_findings", []) == []
        assert receipt["cached_production_gates"]["passed"] is True
        assert receipt["all_bindings_unchanged"] is outer["all_bindings_unchanged"] is True
        assert all(receipt[name] == 0 for name in ("HP_calls", "tests", "candidate_copies", "default_installations"))
    else:
        assert confirmation["execution_status"] == "not_pass" or review["execution_status"] != "pass" or review.get("blocking_findings", [])
    input_pins = {"execution_receipt.json": receipt_sha, "production_launch.json": outer_sha,
                  "independent_terminal_review.json": review_sha, "independent_terminal_review.md": REVIEW_MD_SHA,
                  "root_terminal_confirmation.json": confirmation_sha}
    def reviewed_ordinary_identity(path, pin):
        name = path.resolve().relative_to(root).as_posix()
        assert review["reviewed_repository_SHA256"][name] == pin
    result_file = run / LABEL / "result.json"
    result = None
    if result_file.exists():
        result, pin = read_json(result_file)
        input_pins["result.json"] = pin
        reviewed_ordinary_identity(result_file, pin)
    qa, qa_sha = None, None
    if args.pixel_qa is not None:
        qa, qa_sha = read_json(args.pixel_qa)
        input_pins["pixel_QA.json"] = qa_sha
    body, n = "", len(result.get("states", [])) if result is not None else 0
    if passed:
        assert result is not None and result["status"] == "success" and result["path_completed"] is True
        summary, summary_sha = read_json(run / "view" / LABEL / "summary.json")
        view, view_sha = read_json(run / "view" / "view.json")
        input_pins.update(view_summary=summary_sha, view_manifest=view_sha)
        reviewed_ordinary_identity(run / "view" / LABEL / "summary.json", summary_sha)
        reviewed_ordinary_identity(run / "view" / "view.json", view_sha)
        assert view["status"] == "pass" and view["new_F_T_model_solver_HP_calls"] == 0
        assert view["contact_pressure_clamping_qualified"] is False and len(view["cases"]) == 1
        assert summary["production_status"] == "success" and summary["reference_available"] is False
        body, n = state_tables(result, summary)
        case = view["cases"][0]
        assert case["label"] == LABEL and case["saved_accepted_states"] == case["observed_states"] == n
        assert receipt["actual_PNGs"] == 3 and receipt["actual_GIF_frames"] == n
        outputs = view["outputs"]
        assert all(name in outputs for name in ("comparison.png", "distances_forces.png", "peak_fields.png", LABEL + "/actual_states.gif"))
        assert receipt["counts"]["api_started"] == receipt["counts"]["api_completed"] == 1
        for kind in ("force", "tangent"):
            assert receipt["counts"][kind + "_started"] == result["call_counts"][kind + "_calls"]
            assert receipt["counts"][kind + "_completed"] == result["call_counts"][kind + "_calls_completed"]
    else:
        body = partial_text(result)
    status = "PASS" if passed else "NOT_PASS"
    physical = ("以下两表列出实际全部 " + str(n) + " 个接受态，q_in按同态身份取原result，其余原值来自pure viewer普通summary。显示舍入不构成新计算；不计算新差值、比例或压力。\n\n" + body) if passed else body
    count_record = result.get("call_counts", {}) if result is not None else receipt.get("call_counts", {})
    counts = receipt.get("counts", {})
    error_record = {"outer_stop_reason": outer.get("stop_reason"),
                    "original_helper_error_fields": {key: receipt[key] for key in ("error", "exception", "exception_class", "exception_code", "reason", "failure", "API_failure") if key in receipt},
                    "saved_failure": result.get("failure") if result is not None else None,
                    "independent_review_status": review.get("status"), "independent_review_findings": review.get("blocking_findings", [])}
    resources = "outer " + display(outer.get("elapsed_seconds")) + "秒；实际helper终止墙钟 " + display(outer.get("helper_wall_seconds")) + "秒；helper回执快照 " + display(receipt.get("elapsed_seconds")) + "秒。树RSS采样峰 " + display(recorded(outer, "peak_sampled_tree_RSS_bytes", "sampled_peak_tree_RSS_bytes")) + "B；helper采样峰 " + display(recorded(receipt, "peak_sampled_RSS_bytes", "sampled_peak_RSS_bytes")) + "B。两种采样口径分别保留，不宣称OS硬限制。"
    visual = ("原viewer记录3PNG和实际N=" + str(n) + "帧GIF，未在闭卡记录步骤读取或核媒体字节。\n\n![实际新保存段变形](run_001/view/" + LABEL + "/actual_states.gif)\n\n[结构与端口](run_001/view/comparison.png) · [力与有限距离](run_001/view/distances_forces.png) · [本段起点场](run_001/view/peak_fields.png)\n\nsegment PEAK是本段1.10起点，原加载峰仍为1.20；1.05不是完全释放。") if passed else "本卡未通过；这里只保留实际已存在的生产／viewer partial，不宣称三PNG或N帧已全部完成，不嵌入未确认媒体。"
    qa_text = "原PNG像素QA尚未提供；本写入器未查看像素。" if qa is None else "root像素QA普通记录状态为 " + display(qa.get("status")) + "；原记录view_image_calls=" + display(qa.get("actual_view_image_calls")) + "，replot=" + display(qa.get("render_retry_or_replot")) + "。仅读[实际QA](author/pixel_QA.json)，本写入器未看PNG/GIF或重绘。\n\n原QA限制如下，按root文本保留：\n\n" + "\n\n".join("> " + str(note).replace("\n", " ") for note in qa.get("observations", []))
    effect = ("原请求1.05末态已接受并保存，实际R=" + display(summary["rows"][-1]["R_input_N"]) + " N，工件total Fy=" + display(summary["rows"][-1]["total_body_Fy_N"]) + " N，有限底边间隙=" + display(summary["rows"][-1]["tip_to_bottom_mm"]) + " mm；新响应及真实变形作为下一段判断依据。") if passed else "本段未形成可宣称通过的新终点；效果仅限实际保留下来的partial与原错误证据。"
    report = f"""# M-UNLOAD1实际闭卡：{status}

2026-10-13（Asia/Seoul）。root确认唯一session20354真实终止，exit{outer['exit_code']}；实际outer状态{outer['status']}，独立terminal审阅状态{display(review.get('status'))}。执行源为main `{BASE}`、协议 `{PROTOCOL_SHA}`。本文件依据真实普通记录写入，静审或余时没有被当成新数值许可。

整体目标是独立HF读取普通LF几何，提供有限变形／TMC前向反力、端口位移、固定工件作用、可恢复状态与实际变形，服务外部研究层；HF不优化、不调用dmftd，MPM暂不实现。本步从成功1.10末态只追加绝对1.05，保完整旧16目标前缀及全部物理字段，复用已验证默认入口和原pure viewer，逐段观察卸载作用与间隙，不重做原加载路径或36项兼容测试。

实际阶段状态：helper={receipt['status']}，新保存接受态记录数={n}。本段的完成仅由真实result/closure给出；成功parent和更早failed/time_limit祖先继续保留，原M-ALPHA1／M-EXTEND1 NOT_PASS没有被改写。默认实现0改动，新HP／测试／候选复制／安装／外部重试均0，由root确认与独立闭卡审阅支持；本记录步骤科学postread为0。

{effect}

{physical}

R为原actuator-on-model反力；工件Fx/Fy为固定下半工件signed weak-form节点合力，含material与Hu；端口加权位移不是表面间隙。有限底边距离沿原采样合同；solid J和Green主应变为原保存viewer观察，不是独立应力HP或连续压力。

实际调用：F开始／完成{display(count_record.get('force_calls'))}／{display(count_record.get('force_calls_completed'))}，T开始／完成{display(count_record.get('tangent_calls'))}／{display(count_record.get('tangent_calls_completed'))}。正常invalid_J／回溯拒绝与原bisection按原控制器记录，开始数可大于完成数。其他真实阶段计数及原缓存门如下，未重核科学阈值：

```json
{json.dumps(counts, ensure_ascii=False, indent=2, allow_nan=False)}
```

```json
{gate_text(receipt)}
```

资源合同controller1800／viewer600／helper2700／outer2760秒、采样8GiB；whole clock包含身份、导入、构模、API、保存、viewer及封存，viewer只获得原helper剩余窗口。{resources} 无force、修复重跑、延期或回滚；关闭后不补科学hash、复制、ZIP、GIF解码或绘图。

{visual}

{qa_text}

真实停止／错误记录：

```json
{json.dumps(error_record, ensure_ascii=False, indent=2, allow_nan=False)}
```

当前进度为本段实际{status}；完整原／延伸路径、连续总压力、自由工件有效夹持、完全释放、稳定性、全部切线列、一般LF和HF5资格均未升级。已有M-EREF1仍是旧result的1.10点2HP，不改绑本段或合成新全段参考。下一步据真实保存反力、工件作用、距离、变形或原错误选择必要参考／更低卸载；任何新科学阶段另成具体卡并直接批准，闭卡余时不是许可。

[实际执行回执](run_001/execution_receipt.json) · [唯一outer](production_launch.json) · [独立实际terminal审阅](author/independent_terminal_review.md) · [root真实终态确认](author/root_terminal_confirmation.json) · [本卡](M-UNLOAD1_CARD.md) · [父成功段](../saved_extension_002/RESULTS.md) · [既有1.10点参考](../extension_reference_001/RESULTS.md)。本记录不替代独立实际审阅或出版核对。
"""
    prefix = f"""# 最新实际闭卡：M-UNLOAD1 {status}，1.10→1.05请求

2026-10-13（Asia/Seoul）。唯一session20354已真实终止exit{outer['exit_code']}，helper={receipt['status']}，实际保存接受态N={n}，独立审阅状态{display(review.get('status'))}。默认入口与原pure viewer用于仅追加1.05的本段；原物理／门／settings/options保持，没有新HP、测试、候选复制、安装或外部重试。实际反力／工件作用／有限距离／变形及错误见[M-UNLOAD1结果](../{REL}/RESULTS.md)。

成功parent和failed/time_limit祖先、完整原／延伸路径及压力／有效夹持／完全释放／稳定性／全列／HF5缺口保持。闭卡余时不转为新许可，后续科学阶段另成具体卡并直接批准。以下完整3cf准备与历史记录保留原raw连续一次；历史未执行文字不代替顶部真实状态。

---

""".encode("utf-8")
    prior_docs = {}
    for name in FRONTS:
        previous = subprocess.check_output(["git", "show", BASE + ":" + name], cwd=root)
        assert (root / name).read_bytes() == previous
        assert (prefix + previous).count(previous) == 1
        prior_docs[name] = previous
    result_doc = stage / "RESULTS.md"
    documentation_receipt = stage / "author" / "execution_documentation_receipt.json"
    assert not result_doc.exists() and not documentation_receipt.exists()
    terminal_json_target = stage / "author" / "independent_terminal_review.json"
    terminal_md_target = stage / "author" / "independent_terminal_review.md"
    assert not terminal_json_target.exists() and not terminal_md_target.exists()
    terminal_json_raw = args.terminal_review.read_bytes()
    assert sha256(terminal_json_raw).hexdigest() == review_sha
    with terminal_json_target.open("xb") as stream:
        stream.write(terminal_json_raw)
    with terminal_md_target.open("xb") as stream:
        stream.write(review_md_raw)
    with result_doc.open("xb") as stream:
        stream.write(report.encode("utf-8"))
    histories = []
    for name, previous in prior_docs.items():
        current = prefix + previous
        (root / name).write_bytes(current)
        histories.append(dict(path=name, old_sha256=sha256(previous).hexdigest(), new_sha256=sha256(current).hexdigest(),
                              history_start_byte=len(prefix), history_end_byte_exclusive=len(current), old_raw_contiguous_once=True))
    written = dict(schema_version="MUNLOAD1-execution-documentation-receipt-1.0", status="ordinary_documentation_written_after_real_terminal",
                   card="M-UNLOAD1", execution_status="pass" if passed else "not_pass", execution_closed=True,
                   source_baseline_commit=BASE, actual_execution_closed=True, actual_execution_status=outer["status"],
                   approved_source_commit=BASE, protocol_sha256=PROTOCOL_SHA, real_terminal_exit_code=outer["exit_code"],
                   source_inputs_SHA256=input_pins, actual_saved_states=n, front_history=histories,
                   copied_independent_reports_SHA256={"author/independent_terminal_review.json": review_sha, "author/independent_terminal_review.md": REVIEW_MD_SHA},
                   results_sha256=sha256(report.encode("utf-8")).hexdigest(), created_utc=datetime.now(timezone.utc).isoformat(),
                   default_runtime_changes=0, new_HP_tests_copies_installations_external_retries=0,
                   scientific_postrun_reads_hashes_decodes_imports_tests_solver_plot_pixels=0,
                   root_QA_ordinary_record_only=qa is not None, publication_confirmed_by_this_writer=False)
    with documentation_receipt.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(written, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: written[key] for key in ("status", "execution_status", "actual_saved_states", "real_terminal_exit_code", "scientific_postrun_reads_hashes_decodes_imports_tests_solver_plot_pixels")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
