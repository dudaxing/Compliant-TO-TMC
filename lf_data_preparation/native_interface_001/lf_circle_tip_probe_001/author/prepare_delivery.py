"""Publish only closed PROBE1 bytes and ordinary metadata; root runs explicitly.

No scientific imports, archive decoding, image opening, solver or Git commands.
The original execution ZIP remains opaque and is copied without recompression.
"""
from datetime import datetime, timedelta, timezone
import argparse
import json
from pathlib import Path
import shutil


AUTHOR = Path(__file__).resolve().parent
BASE = Path("D:/hpr1_001")
ROOT = Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC")
TARGET = ROOT/"lf_data_preparation/native_interface_001/lf_circle_tip_probe_001"


def read_if(path):
    return json.loads(path.read_bytes()) if path.is_file() else None


def code(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)


def cell(value):
    return ("null" if value is None else str(value)).replace("|", "\\|").replace("\n", " ")


def cleanup_status(receipt):
    if receipt is None:
        return "not_run_or_no_receipt"
    proof = receipt.get("cleanup_proof", {})
    return "PASS" if (receipt.get("cleanup_verified") is True and proof.get("pass") is True
        and proof.get("job_handle_closed") is True) else "NOT_PASS"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Required explicit root command after termination and figure QA")
    parser.add_argument("--figure-qa", type=Path, default=AUTHOR/"FIGURE_QA.json")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("No action. Root must explicitly pass --execute after the unique run terminates.")
    if TARGET.exists():
        raise FileExistsError("Delivery directory already exists; do not overwrite or create another run.")
    if not (BASE/"root_outer_supervision.json").is_file() or not (BASE/"seal_receipt.json").is_file():
        raise RuntimeError("The original outer process has not produced its terminal supervision/seal receipts.")
    run = BASE/"run_001"
    protocol = read_if(BASE/"protocol.json")
    outer = read_if(BASE/"root_outer_supervision.json")
    seal = read_if(BASE/"seal_receipt.json")
    helper = read_if(run/"helper_receipt.json")
    launch = read_if(run/"launch_receipt.json")
    scientific = read_if(run/"science_child_receipt.json")
    numerical = read_if(run/"numerical_validation.json")
    result = read_if(run/"science/result.json")
    renderer = read_if(run/"view/renderer_receipt.json")
    table = read_if(run/"view/state_table.json")
    qa = read_if(args.figure_qa)
    if renderer is not None and qa is None:
        raise RuntimeError("Rendered output exists; root FIGURE_QA.json is required before delivery.")
    rows = (table or {}).get("states", (result or {}).get("accepted_steps", []))
    numerical_status = "PASS" if numerical is not None and numerical.get("status") == "pass" else "NOT_PASS"
    display_status = (renderer or {}).get("status", "not_run_or_no_receipt")
    qa_status = (qa or {}).get("status", (qa or {}).get("overall_status", "recorded_see_QA" if qa is not None else "not_run_or_no_receipt"))
    partial = (helper or {}).get("actual_partial_observation", (launch or {}).get("actual_partial_observation"))
    callbacks = (scientific or {}).get("callback_accepted_states", (partial or {}).get("progress_records"))
    now = datetime.now(timezone.utc)
    local_date = now.astimezone(timezone(timedelta(hours=9))).date().isoformat()
    TARGET.mkdir(parents=True, exist_ok=False)
    shutil.copytree(AUTHOR, TARGET/"author")
    if qa is not None and args.figure_qa.resolve() != (AUTHOR/"FIGURE_QA.json").resolve():
        shutil.copy2(args.figure_qa, TARGET/"author/FIGURE_QA.json")

    copied = []
    def copy(source, relative):
        if source.is_file():
            destination = TARGET/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append(relative.as_posix())

    for name in ("run_probe1.py", "launch_probe1.py", "outer_probe1.py", "render_probe1.py",
                 "protocol.json", "observer_definition.json", "root_outer_supervision.json",
                 "root_outer.instances.ndjson", "root_outer.log", "EVIDENCE_MANIFEST.json",
                 "seal_receipt.json", "execution_evidence.zip"):
        copy(BASE/name, Path(name))
    # NPZ contents remain in the byte-exact execution ZIP. Only existing plain
    # records and generated media are exposed outside it for convenient review.
    ordinary = {".json", ".jsonl", ".ndjson", ".log", ".md", ".png", ".gif"}
    if run.is_dir():
        for source in sorted(run.rglob("*")):
            if source.is_file() and source.suffix.lower() in ordinary:
                copy(source, Path("run_001")/source.relative_to(run))

    initial = (result or {}).get("source", {}).get("selected_state", {})
    actual_counts = (result or {}).get("call_counts", (scientific or {}).get("call_counts"))
    original_card = (AUTHOR/"L-CTIPPROBE1_CARD.md").read_bytes()
    prefix = ("# L-CTIPPROBE1 已授权执行记录入口\n\n"
        f"{local_date}（Asia/Seoul）。用户明确批准本卡实施与执行。以下保留原卡全文；其中“待授权”描述原准备时状态。"
        f"实际数值验收={numerical_status}，显示生成={display_status}，root像素检查={qa_status}。"
        "各状态分别依据原凭证，不跨范围替代。原卡原字节另存author/L-CTIPPROBE1_CARD.md。\n\n---\n\n")
    (TARGET/"L-CTIPPROBE1_CARD.md").write_bytes(prefix.encode("utf-8")+original_card)

    text = ["# L-CTIPPROBE1：真实导向工件位移探针", "",
        f"{local_date}（Asia/Seoul）。数值验收 **{numerical_status}**；显示生成 `{display_status}`；"
        f"root图像检查 `{qa_status}`。本页只汇总唯一运行的实际证据。", "",
        "整体目标是HF独立读取LF普通几何，在一致的大变形／Third Medium Contact任务下计算响应供研究比较。HF不优化、不调用dmftd、不实现MPM。本轮将已验证的小模型移动工件入口用于既有真实夹持器，以观察在机构输入保持时，工件沿+x小幅移动所需的有符号驱动力及介质响应。", "",
        "本次采用导向夹具的位移控制，不是自由工件的指定外载承载认证。机构平均输入保持1.06 mm，工件全部ux=q、uy=0、转角0，q请求仅[0,.025] mm。保持α2.5e−7、γ1e−6、r9 mm、圆心(80,40) mm、right92 mm、Lr80 mm、E1 MPa、ν.3、plane strain、厚度20 mm、h=.5 mm及原边界／材料／验收门；原510工件单元／565节点不重mask。", "",
        "入口为已安装的 `evaluate_native_guided_probe`，唯一调用从原完整load_only的accepted12／original12／1.06 mm峰值迁移两份split和原有符号R；不重做加载，不读旧力／矩阵作为新验证。继承mechanical／chunk256／port_projection，仅新增controller时钟。", "",
        "## 实际终态与证据范围", "",
        "|层次|实际记录|", "|---|---|",
        f"|数值门核查|{numerical_status}；原生产status={cell((result or {}).get('status'))}；failure={cell((result or {}).get('failure'))}|",
        f"|唯一API|attempts={cell((scientific or {}).get('api_call_attempts'))}；returned={cell((scientific or {}).get('api_returned'))}|",
        f"|接受态|{cell(len(rows) if result is not None or table is not None else None)}；实际回调记录={cell(callbacks)}|",
        f"|显示|{display_status}；PNG={cell((renderer or {}).get('new_png_count'))}；实际GIF帧={cell((renderer or {}).get('gif_frame_count'))}|",
        f"|root像素检查|{qa_status}；详见author/FIGURE_QA.json原记录|",
        f"|封存|{cell((seal or {}).get('status'))}；attempts={cell((seal or {}).get('attempts'))}|", "",
        "数值PASS须由原包装numerical_validation证据证明，不能仅用API返回success替代。没有返回result时，未知接受态／调用计数保留null；已有回调与partial文件按原记录报告，不等同完整结果。没有运行或完成显示时不伪造图像。", "",
        "原包装的实际部分状态观察：", "", "```json", code(partial), "```", "",
        "## 实际保存态", "",
        "Q_drive_half=Σbody f_int,x=−ON-body Fx；保留q0预载和符号。下表均为半模型N，已含20 mm厚度；对称完整装配轴向换算才取2Q，位移q不倍增。material／Hu为原节点弱力分量，不能称纯压力或摩擦；负Q表示需要制动，不能认定正抗拔容量。", "",
        "|接受态|body q mm|input mean mm|Q half N|R input N|ON-body Fy total N|Fy material N|Fy Hu N|min J|relative residual|Newton checks|", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for index, row in enumerate(rows):
        forces = row.get("force_on_body_N", {})
        fy = lambda name: forces.get(name, [None, None])[1]
        text.append("|"+"|".join(cell(value) for value in (index, row.get("body_q_mm"), row.get("input_mean_mm"),
            row.get("Q_drive_half_N"), row.get("R_input_N"), fy("total"), fy("material"), fy("regularization"),
            row.get("minimum_J"), row.get("relative_residual"), row.get("newton_checks")))+"|")
    if not rows:
        text += ["", "没有可据以报告的普通接受态结果；保留部分文件与原异常凭证，不补写数值。"]
    if table is not None:
        text += ["", "逐态Q−Q(0)、material／Hu尾差、互斥反力账本、原门、尖端到物理阶梯边界距离、body到实际右界距离、全介质／右480格J与Hu及定位见 [state_table.json](run_001/view/state_table.json)。几何距离排除参考y40对称切边，只是binary64保存坐标观察。J为原九点采样；Hu为Q1 cell常量，其定位点为实际cell质心。", ""]
    text += ["", "## 新q0与来源身份", "", "```json", code(initial if initial else None), "```", "",
        "q0必须fresh F/T直接通过、保持原split两字段及R身份且checks=1；该证明以数值包装和原科学结果为准，不由本汇总脚本重新计算。", "",
        "基线提交：`"+protocol["baseline_commit"]+"`；远程origin维持`https://github.com/dudaxing/Compliant-TO-TMC.git`。研究包装、观察定义及68项冻结依赖见protocol.json、author中的CANDIDATE_FREEZE和静审记录。原七份来源只按字节复制；原父任务／参考／失败与资格没有改写。", "",
        "实际执行力学源码身份：", "", "```json", code((result or {}).get("mechanics_source_sha256")), "```", "",
        "## 调用、资源及清理", "", "实际调用计数（未有权威结果则null）：", "", "```json", code(actual_counts), "```", "",
        "一次controller3600秒／显示共享600秒／helper4500秒／outer4560秒；采样64GiB、四库各16线程、viewer8GiB。不使用GPU、不升级依赖。原minimum_increment=.00625 mm、25 checks／12回溯／4二分及原残差／平均位移／J／global balance／处方位移门保持。没有外部重试、修复重跑、延期、force、HP或测试。", "",
        "|监督层|终止原因|returncode|清理证明|elapsed seconds|", "|---|---|---|---|---|"]
    for label, supervision in (("outer", outer), ("helper", read_if(run/"helper_supervision.json")),
            ("science", read_if(run/"science_supervision.json")), ("viewer", read_if(run/"viewer_supervision.json"))):
        text.append("|"+"|".join(cell(value) for value in (label, (supervision or {}).get("reason"),
            (supervision or {}).get("returncode"), cleanup_status(supervision), (supervision or {}).get("elapsed_seconds")))+"|")
    text += ["", "清理只依据原SUP2同实例／成员覆盖／句柄释放证明；正常退出、数值成功与清理分别记录，不能互相替代。详见原监督JSON与NDJSON。", "",
        "## 可视化与恢复", ""]
    for name, title in (("01_actual_geometry.png", "实际×1结构与尖端"),
                        ("02_force_and_convergence.png", "有符号力、输入保持与全部Newton检查"),
                        ("03_right_medium.png", "右480参考介质格与全介质极值"),
                        ("animation.gif", "本次全部实际接受态动画")):
        if (TARGET/"run_001/view"/name).is_file():
            text += [f"![{title}](run_001/view/{name})", ""]
    archive_note = ("原封存ZIP按字节复制，未解压／重压。新科学NPZ保留在execution_evidence.zip中，含实际源码、最小父来源及新缓存。"
        if seal.get("status") == "pass" else
        "原窗口没有完整PASS封存；只保存实际存在的归档／普通凭证，不声称ZIP完整覆盖新科学缓存。未在关闭窗口后补读或重压科学载荷。")
    text += [archive_note+"公开的普通result内原运行路径是历史上下文。要读取已封存的科学缓存，应显式恢复到隔离位置，不把本页当作已重跑或已补齐完整父路径。此交付脚本只复制文件和汇总普通元数据，没有科学导入、NPZ解码或图像像素读取。", "",
        "本卡仅回答受导向位移探针的实际响应；不授新的HP参考、压力、自由承载、有效夹持、释放、稳定性、参数／域独立性或HF最终标签。下一步由root结合本轮实际结果另写NEXT_STEPS.md，本程序不预写下一物理实验。", ""]
    (TARGET/"RESULTS.md").write_text("\n".join(text), encoding="utf-8")
    receipt = dict(status="ordinary_delivery_prepared_for_root_review", created_utc=now.isoformat(),
        target=TARGET.as_posix(), numerical_validation_status=numerical_status,
        renderer_status=display_status, root_figure_QA_status=qa_status,
        copied_runtime_files=copied, original_archive_recompressed=False,
        archive_status=(seal or {}).get("status"), numerical_recomputations=0, scientific_imports=0,
        NPZ_decodes=0, image_pixel_reads=0, git_commands=0, next_steps_written=False)
    (TARGET/"author/delivery_preparation_receipt.json").write_text(code(receipt)+"\n", encoding="utf-8")
    print(code(receipt))


if __name__ == "__main__":
    main()
