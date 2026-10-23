"""Assemble only closed LOW1 bytes and ordinary records after root QA.

Root must explicitly pass --execute. This module never imports mechanics,
decodes NPZ, opens image pixels, recompresses the execution ZIP, or runs Git.
It never writes BASE or production source. Unknown actual results remain null.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import shutil


AUTHOR = Path(__file__).resolve().parent
BASE = Path("D:/hlo1_001")
ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
TARGET = ROOT / "lf_data_preparation/native_interface_001/lf_circle_tip_low_probe_001"
PNG_NAMES = ("01_actual_geometry.png", "02_force_and_convergence.png",
             "03_right_medium.png", "04_same_q_comparison.png")
MEDIA_NAMES = PNG_NAMES + ("animation.gif",)
PLAIN_SUFFIXES = {".json", ".jsonl", ".ndjson", ".log", ".md", ".txt"}
AUTHOR_SUFFIXES = PLAIN_SUFFIXES | {".py", ".ps1", ".svg"}
ARCHIVE_REVIEW_BYTES = 90 * 1024**2


def read_if(path):
    return json.loads(path.read_bytes()) if path.is_file() else None


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


def write_json(path, value):
    path.write_text(json_text(value) + "\n", encoding="utf-8")


def cell(value):
    return ("null" if value is None else str(value)).replace("|", "\\|").replace("\n", " ")


def markdown_row(values):
    return "|" + "|".join(cell(value) for value in values) + "|"


def identity(path):
    """Opaque whole-file bytes only; no archive or media interpretation."""
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024**2), b""):
            digest.update(block)
    return dict(path=path.as_posix(), bytes=path.stat().st_size, sha256=digest.hexdigest())


def cleanup_status(receipt):
    if receipt is None:
        return "not_run_or_no_receipt"
    proof = receipt.get("cleanup_proof", {})
    return "PASS" if (receipt.get("cleanup_verified") is True and proof.get("pass") is True
        and proof.get("job_handle_closed") is True) else "NOT_PASS"


def validation_status(validation):
    if validation is None:
        return "not_run_or_no_validation_receipt"
    return "PASS" if (validation or {}).get("status") == "pass" else "NOT_PASS"


def vector_component(row, name, axis):
    vector = row.get("force_on_body_N", {}).get(name)
    return vector[axis] if isinstance(vector, list) and len(vector) > axis else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
        help="Explicit root assembly after actual terminal state and each available new PNG's one QA inspection")
    parser.add_argument("--figure-qa", type=Path, default=AUTHOR / "FIGURE_QA.json")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("No assembly performed. Root must explicitly pass --execute after terminal state and QA.")
    if TARGET.exists():
        raise FileExistsError("Delivery stage already exists; preserve it rather than overwrite.")
    if not (BASE / "root_outer_supervision.json").is_file() or not (BASE / "seal_receipt.json").is_file():
        raise RuntimeError("Terminal original outer supervision and seal/skip receipts are required.")
    run, view = BASE / "run_001", BASE / "run_001/view"
    protocol = read_if(BASE / "protocol.json")
    outer = read_if(BASE / "root_outer_supervision.json")
    seal = read_if(BASE / "seal_receipt.json")
    manifest = read_if(BASE / "EVIDENCE_MANIFEST.json")
    helper = read_if(run / "helper_receipt.json")
    launch = read_if(run / "launch_receipt.json")
    parent_child = read_if(run / "parent_child_receipt.json")
    probe_child = read_if(run / "probe_child_receipt.json")
    parent_validation = read_if(run / "parent_validation.json")
    probe_validation = read_if(run / "probe_validation.json")
    parent = read_if(run / "parent_fixed/result.json")
    probe = read_if(run / "probe_low/result.json")
    renderer = read_if(view / "renderer_receipt.json")
    table = read_if(view / "state_table.json")
    comparison = read_if(view / "comparison.json")
    qa = read_if(args.figure_qa)
    available_pngs = [name for name in PNG_NAMES if (view / name).is_file()]
    if available_pngs:
        if qa is None:
            raise RuntimeError("Available new PNGs require root's ordinary FIGURE_QA record before assembly.")
        qa_images = {Path(row["path"]).name: row for row in qa.get("images", [])}
        if any(name not in qa_images or qa_images[name].get("pixel_inspections") != 1 for name in available_pngs):
            raise RuntimeError("Root must record exactly one inspection for each available original new PNG.")
        if qa.get("root_pixel_inspections") != len(available_pngs) or qa.get("rerenders") != 0:
            raise RuntimeError("QA counts/rerender status differ from the one-pass figure policy.")
        for name in available_pngs:
            actual = identity(view / name)
            if any(actual[key] != qa_images[name].get(key) for key in ("bytes", "sha256")):
                raise ValueError("Root QA does not bind the original new PNG bytes: " + name)

    archive = BASE / "execution_evidence.zip"
    archive_identity = identity(archive) if archive.is_file() else None
    if archive_identity is not None and archive_identity["bytes"] > ARCHIVE_REVIEW_BYTES:
        transport = dict(status="requires_root_transport_decision", target=TARGET.as_posix(),
            archive=archive_identity, threshold_bytes=ARCHIVE_REVIEW_BYTES,
            stage_assembled=False, archive_split=False, archive_recompressed=False,
            scientific_recomputations=0, instruction="Stop for root transport review; do not split/recompress or stage the large ZIP automatically.")
        write_json(AUTHOR / "DELIVERY_TRANSPORT_REQUIRED.json", transport)
        print(json_text(transport))
        return 3
    if seal.get("status") == "pass":
        declared = (manifest or {}).get("archive", {})
        if archive_identity is None or any(archive_identity[key] != declared.get(key) for key in ("bytes", "sha256")):
            raise ValueError("PASS seal lacks its byte-identical original execution archive and manifest.")

    parent_status = validation_status(parent_validation)
    probe_status = validation_status(probe_validation)
    both_status = ("PASS" if parent_status == probe_status == "PASS" else
                   "NOT_PASS" if "NOT_PASS" in (parent_status, probe_status) else "not_fully_validated")
    display_status = (renderer or {}).get("status", "not_run_or_no_receipt")
    qa_status = (qa or {}).get("status", (qa or {}).get("overall_status",
        "recorded_see_QA" if qa is not None else "not_run_or_no_receipt"))
    parent_rows = (parent or {}).get("states", [])
    probe_rows = (table or {}).get("states", (probe or {}).get("accepted_steps", []))
    paired = (comparison or {}).get("paired_states", [])
    partial = (helper or {}).get("actual_partial_observation", (launch or {}).get("actual_partial_observation"))
    now = datetime.now(timezone.utc)
    local_date = now.astimezone(timezone(timedelta(hours=9))).date().isoformat()
    TARGET.mkdir(parents=True, exist_ok=False)
    copied = []

    def copy(source, relative):
        if source.is_file():
            destination = TARGET / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append(relative.as_posix())

    # Only ordinary author/source records; no unpacked scientific archive or
    # media can leak from an unexpected author file into the published stage.
    for source in sorted(AUTHOR.rglob("*")):
        if source.is_file() and source.suffix.lower() in AUTHOR_SUFFIXES:
            copy(source, Path("author") / source.relative_to(AUTHOR))
    if qa is not None and args.figure_qa.resolve() != (AUTHOR / "FIGURE_QA.json").resolve():
        copy(args.figure_qa, Path("author/FIGURE_QA.json"))
    for name in ("run_low1.py", "launch_low1.py", "outer_low1.py", "render_low1.py",
                 "windows_owned_process_sup2.py", "protocol.json", "observer_definition.json",
                 "high_state_table.json", "task.json", "approved_card.md", "authorization.json",
                 "RUNNER_INTERFACE.md", "SUPERVISION_INTERFACE.md", "root_outer_start.json",
                 "root_outer_supervision.json", "root_outer.instances.ndjson", "root_outer.log",
                 "EVIDENCE_MANIFEST.json", "seal_receipt.json", "execution_evidence.zip"):
        copy(BASE / name, Path(name))
    copy(BASE / "geometry/geometry.json", Path("geometry/geometry.json"))
    if run.is_dir():
        for source in sorted(run.rglob("*")):
            if source.is_file() and source.suffix.lower() in PLAIN_SUFFIXES:
                copy(source, Path("run_001") / source.relative_to(run))
    for name in MEDIA_NAMES:
        copy(view / name, Path("run_001/view") / name)
    if archive_identity is not None:
        copied_archive = identity(TARGET / "execution_evidence.zip")
        if any(copied_archive[key] != archive_identity[key] for key in ("bytes", "sha256")):
            raise ValueError("Opaque archive copy identity differs; preserve actual copy and stop.")

    original_card = (AUTHOR / "L-CTIPLOW1_CARD.md").read_bytes()
    prefix = ("# L-CTIPLOW1 已授权执行记录入口\n\n"
        f"{local_date}（Asia/Seoul）。用户已明确批准实施与执行。本页保留原卡全文；其中“待授权”是原准备状态。"
        f"实际父门={parent_status}，探针门={probe_status}，显示生成={display_status}，root图像检查={qa_status}。"
        "不同层次分别依据原回执，不互相代替。原卡字节另存author/L-CTIPLOW1_CARD.md。\n\n---\n\n")
    (TARGET / "L-CTIPLOW1_CARD.md").write_bytes(prefix.encode("utf-8") + original_card)

    text = ["# L-CTIPLOW1：从零低输入父加载与同q导向探针对照", "",
        f"{local_date}（Asia/Seoul）。两段原数值门 **{both_status}**（父 {parent_status}／probe {probe_status}）；"
        f"显示 `{display_status}`；root图像检查 `{qa_status}`。以下只汇总唯一运行实际凭证，不重新计算科学量。", "",
        "## 目标、目的与本次功能", "",
        "整体目标是HF独立读取LF普通几何，在一致的大变形／Third Medium Contact物理任务下计算力学响应供研究比较；HF不做LF优化、不调用dmftd、不实现MPM。现已能从零加载、保存态迁移、导向刚体工件位移并显示实际缓存。本轮用较低机构输入检查已观察到的导向力及Hu分量是否随夹持机构输入改变。", "",
        "先用现有evaluate_native从零完成固定工件短父任务：机构平均输入[0,.25,.50] mm。只有原任务完整成功和全部原门通过，才用真实最后原目标态进入evaluate_native_guided_probe；q0必须fresh F/T直接通过并保持原split及有符号R，随后机构平均输入保持.50 mm，工件仅q[0,.025] mm。未将旧13态路径的.50中间态冒充新父末态。", "",
        "其余物理保持：α2.5e−7、γ1e−6、r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、E1 MPa、ν.3、plane strain、厚度20 mm、h=.5 mm及原边界；原510工件单元／565节点不重mask。全部工件ux=q、uy=0、转角0，仍由导向夹具控制。模式mechanical／chunk256／port_projection、原非clock设置及验收门保持，没有生产源码安装。", "",
        "为什么要从零建立新父任务：现有probe准入要求原完整load_only最后峰值；这样既保留真实零起点加载历史，也复用现有接口，不伪造任务完成状态或改宽默认准入。为什么比较同q：只在实际共同接受位移下保留原力、材料／Hu、各自q0增量和介质响应，避免把不同位移或插值值当作相同工况。", "",
        "## 实际两段执行", "", "|层次|实际父加载|实际低输入probe|", "|---|---|---|",
        markdown_row(("原门核查", parent_status, probe_status)),
        markdown_row(("原production status", (parent or {}).get("status"), (probe or {}).get("status"))),
        markdown_row(("原failure", (parent or {}).get("failure"), (probe or {}).get("failure"))),
        markdown_row(("API attempts", (parent_child or {}).get("api_call_attempts"), (probe_child or {}).get("api_call_attempts"))),
        markdown_row(("API returned", (parent_child or {}).get("api_returned"), (probe_child or {}).get("api_returned"))),
        markdown_row(("实际接受态", len(parent_rows) if parent is not None else None,
                      len(probe_rows) if probe is not None or table is not None else None)),
        markdown_row(("实际回调数", (parent_child or {}).get("callback_accepted_states"), (probe_child or {}).get("callback_accepted_states"))),
        "", "这里的PASS由原parent_validation／probe_validation证明，不能只用API success或绘图完成代替。未知数值／调用数保持null，已有回调与实际partial保留，不补写未返回结果。原进程部分状态观察：", "", "```json", json_text(partial), "```", "",
        "### 父加载实际接受态", "", "|态|input target mm|actual mean mm|R input N|min J|relative residual|Newton checks|二分深度|原目标索引|", "|---|---|---|---|---|---|---|---|---|"]
    for index, row in enumerate(parent_rows):
        text.append(markdown_row((index, row.get("d"), row.get("q_in"), row.get("R_input"), row.get("minimum_J"),
            row.get("relative_residual"), row.get("newton_checks"), row.get("bisection_depth"), row.get("original_target_index"))))
    if not parent_rows:
        text += ["", "无可报告的父普通保存态；以原partial／异常记录为准。"]
    text += ["", "### 低输入probe实际接受态", "",
        "Q_drive_half=−ON-body Fx。所有力为半模型N，已经包含20 mm厚度；只有对称完整装配轴向换算取2Q，q不倍增。保留q0预载和符号；材料／Hu为节点弱力分量，不是纯接触压力。负Q表示制动，不能改称正抗拔容量。", "",
        "|态|q mm|held input mean mm|Q total N|Q material N|Q Hu N|R input N|ON-body Fy N|min J|relative residual|Newton checks|", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for index, row in enumerate(probe_rows):
        material_x, Hu_x = vector_component(row, "material", 0), vector_component(row, "regularization", 0)
        text.append(markdown_row((index, row.get("body_q_mm"), row.get("input_mean_mm"), row.get("Q_drive_half_N"),
            -material_x if material_x is not None else None, -Hu_x if Hu_x is not None else None,
            row.get("R_input_N"), vector_component(row, "total", 1), row.get("minimum_J"),
            row.get("relative_residual"), row.get("newton_checks"))))
    if not probe_rows:
        text += ["", "无可报告的probe普通保存态；不推断其已完成或生成图像。"]
    text += ["", "### 原验收门的实际回执", "",
        "保留原relative free residual≤1e−9、原尺度相关mean constraint、J>0、relative global balance≤1e−6、处方位移误差≤8e−11 mm；minincrement=.00625 mm，maxchecks25／backtracks12／bisections4。以下直接展示原包装记录，不由交付脚本重验科学数组。", "",
        "父门回执：", "", "```json", json_text(parent_validation), "```", "",
        "probe门回执：", "", "```json", json_text(probe_validation), "```", "",
        "真实来源和fresh q0身份：", "", "```json", json_text((probe or {}).get("source", {}).get("selected_state")), "```", "",
        "## 高低输入同q原值、分量和增量", "",
        "高输入1.06 mm只使用原绑定state_table普通JSON；不读取旧NPZ或媒体，不插值。下表差值方向low−high，各自ΔQ=Q(q)−Q(0)，与原预载同时保留；低输入没有预先被认定为无接触。", "",
        "|q mm|条件|Q total N|Q material N|Q Hu N|各自ΔQ total N|ON-body Fy N|R input N|", "|---|---|---|---|---|---|---|---|"]
    for pair in paired:
        for condition in ("low", "high"):
            raw, increment = pair.get(condition + "_raw", {}), pair.get(condition + "_Q_increment_from_own_q0_N", {})
            text.append(markdown_row((pair.get("body_q_mm"), condition, raw.get("Q_total_N"), raw.get("Q_material_N"),
                raw.get("Q_Hu_N"), increment.get("Q_total_N"), raw.get("ON_body_Fy_total_N"), raw.get("R_input_N"))))
    text += ["", "|q mm|原Q差 total N|原Q差 material N|原Q差 Hu N|ΔQ差 total N|ΔQ差 material N|ΔQ差 Hu N|", "|---|---|---|---|---|---|---|"]
    for pair in paired:
        raw, increment = pair.get("low_minus_high_raw", {}), pair.get("low_minus_high_Q_increment_N", {})
        text.append(markdown_row((pair.get("body_q_mm"), raw.get("Q_total_N"), raw.get("Q_material_N"), raw.get("Q_Hu_N"),
            increment.get("Q_total_N"), increment.get("Q_material_N"), increment.get("Q_Hu_N"))))
    text += ["", "### 同q几何与介质响应", "", "|q mm|条件|tip/body mm|body/actual right mm|全体min J|非body介质min J|非body介质max abs Hu 1/mm|右480 min J|右480 max abs Hu 1/mm|", "|---|---|---|---|---|---|---|---|---|"]
    for pair in paired:
        for condition in ("low", "high"):
            raw = pair.get(condition + "_raw", {})
            text.append(markdown_row((pair.get("body_q_mm"), condition, raw.get("tip_to_body_boundary_mm"),
                raw.get("body_to_right_boundary_mm"), raw.get("global_minimum_J"), raw.get("nonbody_medium_minimum_J"),
                raw.get("nonbody_medium_maximum_abs_Hu_per_mm"), raw.get("right480_minimum_J"), raw.get("right480_maximum_abs_Hu_per_mm"))))
    text += ["", "精确共同q：`" + cell((comparison or {}).get("exact_common_q_mm")) + "` mm；高输入额外实际q：`"
        + cell((comparison or {}).get("high_unmatched_q_mm")) + "`；低输入额外实际q：`"
        + cell((comparison or {}).get("low_unmatched_q_mm")) + "`。额外内部态完整保留，不丢弃或插值。", ""]
    if comparison is not None:
        text += ["完整原态对象、有符号原力／材料／Hu、Fy与导向账本、全部标量差和各自增量、两段收敛及原高输入历史见[comparison.json](run_001/view/comparison.json)。", ""]
    if table is not None:
        text += ["低输入逐态定位和完整新父普通记录见[state_table.json](run_001/view/state_table.json)。J定位是原九点采样，Hu为Q1单元常量、标记实际单元质心；物理距离排除参考y40对称切边，画图仍保留完整半模型轮廓。右480成员固定为原参考格，右界ux自由。几何距离／交叉／严格内部节点只是binary64保存坐标观察，不能升级为接触或自交完备认证。", ""]
    if not paired:
        text += ["尚无本轮权威同q比较表；对照值保持null，不用原任务草案或未运行数据补齐。", ""]
    text += ["高低输入会改变整体平衡；原力差和增量差都不能自动解释为纯接触／摩擦／有效抗拔力。物理判断应结合原值、Hu比例、间距和介质定位，不能仅看总Q是否为正。", "",
        "## 调用计数、失败历史与资源", "",
        "父调用计数：", "", "```json", json_text((parent or {}).get("call_counts")), "```", "",
        "probe调用计数：", "", "```json", json_text((probe or {}).get("call_counts")), "```", "",
        "实际父原内部失败尝试：", "", "```json", json_text((parent or {}).get("path_diagnostics", {}).get("failed_attempts")), "```", "",
        "实际probe原内部失败尝试：", "", "```json", json_text((probe or {}).get("failed_attempts")), "```", "",
        "原内部回溯／二分与首个终端错误分别记录；没有外部重试、修复重跑、延期或force。异常发生后后续科学／显示停止，真实partial与原失败历史不覆盖。完整Newton／line-search／linear-solve在原result和state_table／comparison普通JSON中保留。", "",
        "一次父controller3600秒＋probe controller3600秒＋纯显示共享900秒；helper9000秒／outer9060秒。采样64GiB、四库各16线程，viewer8GiB；GPU未用，无依赖升级、HP、新测试、默认源码安装或API关联。源冻结、导入、构模、持久化、检查、清理和原窗口一次byte seal都计入原卡范围。", "",
        "|监督层|reason|returncode|同实例清理|elapsed seconds|sampled peak bytes|", "|---|---|---|---|---|---|"]
    for label, record in (("outer", outer), ("helper", read_if(run / "helper_supervision.json")),
            ("parent", read_if(run / "parent_supervision.json")), ("probe", read_if(run / "probe_supervision.json")),
            ("viewer", read_if(run / "viewer_supervision.json"))):
        text.append(markdown_row((label, (record or {}).get("reason"), (record or {}).get("returncode"), cleanup_status(record),
            (record or {}).get("elapsed_seconds"), (record or {}).get("peak_tree_rss_bytes"))))
    text += ["", "清理依据原SUP2同实例终止信号、全部成员覆盖及句柄释放证明；进程exit、数值门和清理分别保留，不能互相替代。原监督JSON和NDJSON均按字节公开。若实际清理回执未证明通过，本交付只记录读取时实际快照，不能据此认定进程已closed或缓存稳定；没有追加清理尝试、科学执行或补封。未运行／没有验收回执与实际验收未通过分开报告。", "",
        "helper／launcher原异常（若无则null）：", "", "```json", json_text(dict(helper_error=(helper or {}).get("error"), launch_error=(launch or {}).get("error"))), "```", "",
        "## 可视化、图像检查与恢复", "",
        "结构和尖端使用实际×1缓存坐标，参考轮廓是未变形坐标；q0是新父真实末态，不展示或伪造父中间变形。合力箭头按明确mm/N尺度绘制，不称局部牵引。GIF每帧对应真实新probe接受态，实际帧数由原renderer一次元数据读取确认。", "",
        "原renderer回执计数：", "", "```json", json_text({key: (renderer or {}).get(key) for key in
            ("status", "accepted_states", "archives_decoded", "fields_decoded", "new_png_count", "gif_frame_count", "new_gif_metadata_reads", "scientific_calls", "elapsed_seconds")}), "```", "",
        "root检查记录：", "", "```json", json_text(qa), "```", ""]
    for name, title in ((PNG_NAMES[0], "实际×1结构与尖端"), (PNG_NAMES[1], "有符号力与全部父／probe收敛"),
            (PNG_NAMES[2], "右480介质格和全非body介质J／Hu定位"), (PNG_NAMES[3], "高低输入精确同q对照"),
            ("animation.gif", "新probe全部真实接受态动画")):
        if (TARGET / "run_001/view" / name).is_file():
            text += [f"![{title}](run_001/view/{name})", ""]
    archive_note = ("原byte seal为PASS；execution_evidence.zip与其原manifest整包身份一致，按字节复制，未解压／重压。新科学NPZ及完整执行源码／输入／实际缓存都仅以该原ZIP保留。"
        if seal.get("status") == "pass" else
        "原窗口byte seal不是PASS；只交付实际存在的普通凭证和原部分归档，不声称ZIP完整覆盖源码／输入／新缓存。没有在关闭窗口后补封、读科学数组或重压。")
    text += [archive_note, "", "原封存状态：", "", "```json", json_text(seal), "```", "",
        "公开result内的原运行绝对路径是历史上下文；需另行显式恢复原封存到隔离位置才能消费其中科学缓存，本页不冒称已恢复／重算。本交付脚本没有科学导入、NPZ解码、图像像素读取或Git命令。", "",
        "基线提交：`" + cell((protocol or {}).get("baseline_commit")) + "`；origin维持`https://github.com/dudaxing/Compliant-TO-TMC.git`。冻结协议、原授权、全部字节绑定、三份静审及来源说明见本目录protocol.json与author记录。原准备文件中numerical_launched=false／待授权等字样是冻结前历史快照，当前执行状态以本页及原终态回执为准。", "",
        "## 资格与后续决定边界", "",
        "本卡只建立规定从零父加载和受导向位移探针的数值响应／同q对照；未授独立HP、纯压力、摩擦、自由工件承载、有效夹持、释放、稳定性、α／域独立性或HF5资格。原高输入结果、原失败与原资格均未改写。", "",
        "下一步由root依据本轮实际结果另写NEXT_STEPS.md；本程序不预写下一物理目标、不启动额外实验。", ""]
    (TARGET / "RESULTS.md").write_text("\n".join(text), encoding="utf-8")
    receipt = dict(status="ordinary_delivery_prepared_for_root_review", created_utc=now.isoformat(),
        target=TARGET.as_posix(), parent_validation_status=parent_status, probe_validation_status=probe_status,
        renderer_status=display_status, root_figure_QA_status=qa_status, copied_files=copied,
        original_archive_identity=archive_identity, original_archive_recompressed=False,
        archive_status=seal.get("status"), archive_transport_review_required=False,
        unpacked_NPZ_copied=0, numerical_recomputations=0, scientific_imports=0,
        NPZ_decodes=0, image_pixel_reads=0, git_commands=0, next_steps_written=False)
    write_json(TARGET / "author/delivery_preparation_receipt.json", receipt)
    print(json_text(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
