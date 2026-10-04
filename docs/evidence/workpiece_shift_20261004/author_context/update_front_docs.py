"""Author-only front updater; run explicitly with --repo ROOT --data final.json.

Data keys: date, front_sha256, current_card_directories, paths, pose, soft,
next_step, preservation_record. paths has report/master_view/local_fit/record/
repair_report. pose/soft each has result/receipt/launch and optional reference/
reference_lifecycle/reference_launch; soft also has task and note.
All file paths are relative to the selected repository. No mechanics imports.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path


BASELINE = "38ecc77cc14fee9fd0c69d026ed8df1e32b19bc2"
FRONTS = (
    "README.md", "hf_repo/README.md", "docs/CURRENT_STATUS.md",
    "docs/RESUME_DEVELOPMENT.md", "docs/PHYSICS_AND_FUNCTION_PROGRESS_20261001.md",
    "docs/HF5_LF_V2_ADAPTER_AND_TASK_PLAN.md", "docs/NUMPY_FORCE_PROGRESS_20261002.md",
)
BINDING_MAPS = {
    "bindings", "input_bindings", "source_bindings", "inputs", "sources",
    "input_files_sha256", "independent_reference_source_bindings",
}


def digest(raw):
    return sha256(raw).hexdigest()


def local(root, relative):
    target = (root / relative.split("#", 1)[0]).resolve()
    if not target.is_relative_to(root):
        raise ValueError("File path leaves the explicit repository: " + relative)
    return target


def load(root, relative, inputs):
    path = local(root, relative)
    raw = path.read_bytes()
    inputs[path] = digest(raw)
    return json.loads(raw.decode("utf-8-sig"))


def bound_paths(value):
    if isinstance(value, dict):
        for name, child in value.items():
            if name in BINDING_MAPS and isinstance(child, dict):
                yield from child
            yield from bound_paths(child)
    elif isinstance(value, list):
        for child in value:
            yield from bound_paths(child)


def current_card_check(root, directories, inputs, targets):
    """Recheck the actual finalized cards, including future soft reference files."""
    required = {
        "lf_data_preparation/native_workpiece_001/shift_square_pose_002",
        "lf_data_preparation/native_workpiece_001/shift_square_soft_001",
    }
    if not required.issubset(set(directories)):
        raise ValueError("Both actual pose002 and soft001 card directories are required")
    checked = []
    for relative in directories:
        directory = local(root, relative)
        protocols = list(directory.rglob("*protocol*.json"))
        if not protocols:
            raise ValueError("No actual protocol in card directory: " + relative)
        for path in sorted(directory.rglob("*.json")):
            if not any(word in path.name for word in ("protocol", "freeze", "inventory", "receipt", "launch", "contract")):
                continue
            report = load(root, path.relative_to(root).as_posix(), inputs)
            for declared in bound_paths(report):
                if (root / declared.replace("\\", "/")).resolve() in targets:
                    raise ValueError("Front document is bound by current card: " + str(path))
            checked.append(path.relative_to(root).as_posix())
    return checked


def actual_case(root, declared, inputs):
    result = load(root, declared["result"], inputs)
    receipt = load(root, declared["receipt"], inputs)
    launch = load(root, declared["launch"], inputs)
    if launch.get("exit_code") is None or result["status"] not in ("success", "failed"):
        raise ValueError("A terminal actual production result is required")
    if receipt["result_sha256"] != inputs[local(root, declared["result"])]:
        raise ValueError("Production receipt does not bind the selected result")
    reference = None
    if declared.get("reference"):
        reference = load(root, declared["reference"], inputs)
        lifecycle = load(root, declared["reference_lifecycle"], inputs)
        reference_launch = load(root, declared["reference_launch"], inputs)
        if (reference["status"] != "pass" or lifecycle["status"] != "pass"
                or reference_launch["status"] != "pass"
                or reference["result_sha256"] != inputs[local(root, declared["result"])]
                or reference["accepted_states"] != result["accepted_states"]
                or reference["HP_calls_completed"] != 2 * result["accepted_states"]):
            raise ValueError("Selected independent reference is not the whole actual path pass")
    return result, receipt, launch, reference


def make_prefix(relative, data, pose, soft):
    parent = Path(relative).parent

    def link(label, destination):
        path, *anchor = destination.split("#", 1)
        target = os.path.relpath(path, parent).replace("\\", "/")
        return f"[{label}]({target}" + ("#" + anchor[0] if anchor else "") + ")"

    paths = data["paths"]
    report = link("总体目标、实际结果、成本与资格", paths["report"])
    pictures = link("完整实际路径图", paths["master_view"]) + "、" + link("局部贴合与钳尖图", paths["local_fit"])
    record = link("本轮持续总记录", paths["record"])
    repair = link("T44 v5 修正与独立验证", paths["repair_report"])
    pose_result, _, _, pose_reference = pose
    result, receipt, launch, reference = soft
    counts = result["call_counts"]
    completed = result["status"] == "success" and result.get("path_completed") is True
    outcome = (f"完整加载—卸载完成，{result['accepted_states']} 个实际接受态"
               if completed else f"{result['status']}，保留 {result['accepted_states']} 个实际接受态；失败={result['failure']}")
    ref_text = (f"独立参考全量通过：{reference['HP_calls_completed']} 次新 HP80/120、"
                f"{reference['checks_completed']} 项检查" if reference else
                "没有本阶段整路径新 HP 通过结论，不拼接旧前缀或借用 pose002 资格")
    soft_line = f"soft001：{outcome}；{ref_text}。{data['soft']['note']}"
    pose_line = (f"pose002 已完整回零：{pose_result['accepted_states']} 态、"
                 f"{pose_reference['HP_calls_completed']} 次新 HP80/120、{pose_reference['checks_completed']} 项检查通过。")
    functions = "已实现原生固体与第三介质有限变形、固定工件、平均输入/自由输出、三切线与 KKT、完整有序卸载、三分量及全节点力保存和真实 ×1 图。"
    limits = "接受态资格限机械力、声明 PORT 方向切线作用、组装/平衡与工件投影；不含压力、应力 HP、辅助能量、全切线列或自由工件夹持。"
    remaining = "LF/N4 研究层已有生成/评分资料；当前 HF 后端的同任务优化研究耦合/HF5批量评价、自由刚体平衡与摩擦、圆体完整边界及匹配细网格工件资格仍待完成。"
    common = (f"{pose_line}\n\n{soft_line}\n\n{report}；{pictures}；{record}。\n\n"
              + f"旧 pose001 失败只作成本来源；{repair} 的资格限已捕获 T44，不延伸为一般接触或全列资格。\n\n")
    if relative == "README.md":
        content = ("# Compliant-TO-TMC：独立 HF 力学评估器\n\n"
                   "目标是以普通自包含几何和显式物理任务，为既有研究层提供有单位、方向及有效范围的独立正向评价；HF 不依赖 LF 优化器运行。\n\n"
                   + common + functions + " " + limits + "\n\n"
                   + f"下一步：{data['next_step']}。开发继续在 main；异目录恢复见 "
                   + link("恢复说明", "docs/RESUME_DEVELOPMENT.md") + "，文件 verify 不等于复跑旧卡。\n\n")
    elif relative == "hf_repo/README.md":
        content = ("## 当前独立求解器功能与接口\n\n" + common
                   + "显式 `solve_native_mean(..., response_mode='mechanical', tangent_mode='chunk256')` 保存 schema1.2、16机械字段/三切线/full CSC，材料能量 not_evaluated；默认 complete/full 保持原合同。"
                   + "端口只约束加权均值，工件当前是全部 ux/uy 固定的约束覆盖。" + limits + "\n\n"
                   + "源码与调用说明见 " + link("native_mean.py", "hf_repo/src/hf_eval/native_mean.py") + "；" + repair
                   + " 只修复已捕获方向支持，不宣称任意输入或全列资格。\n\n")
    elif relative == "docs/CURRENT_STATUS.md":
        content = ("## 当前终态与下一功能\n\n" + common
                   + f"生产 F开始/完成={counts['force_calls']}/{counts['force_calls_completed']}，T={counts['tangent_calls']}/{counts['tangent_calls_completed']}；"
                   + f"helper/outer实耗={receipt['elapsed_seconds']:.3f}/{launch['elapsed_seconds']:.3f}秒。\n\n"
                   + functions + " " + limits + "\n\n" + remaining + f"\n\n下一步：{data['next_step']}。\n\n")
    elif relative == "docs/RESUME_DEVELOPMENT.md":
        content = ("## 当前可移植接续入口\n\n" + common
                   + "从任意新目录获取 main 并校验文件：\n\n```text\n"
                   + "git clone https://github.com/dudaxing/Compliant-TO-TMC.git my-hf-work\ncd my-hf-work\ngit switch main\npython tools/handoff.py verify\n```\n\n"
                   + "必要大资产按下面保留的移交说明 fetch-evidence 后 verify --full；无需创建原机器 D: 路径。"
                   + "先读本轮总报告/数值与图，再按新的明确任务和预算开发；历史命令和已闭卡不是当前同路径重跑指令。\n\n"
                   + f"下一选择：{data['next_step']}。{limits}\n\n")
    elif relative == "docs/PHYSICS_AND_FUNCTION_PROGRESS_20261001.md":
        content = ("## 当前物理与功能进度\n\n" + common + functions + "\n\n"
                   + "x71 工件更接近钳尖，但已保存 E1 峰态钳尖仍在右面外约0.167mm；底射线约0.005809mm来自边内部点，不是钳尖间隙。"
                   + "soft 只减半实体 E，并倍增 gamma/alpha以保持绝对介质 Lamé及kr，不能预判输出或夹持增强。\n\n"
                   + limits + " " + remaining + f"\n\n下一步由本轮结果选择：{data['next_step']}。\n\n")
    elif relative == "docs/HF5_LF_V2_ADAPTER_AND_TASK_PLAN.md":
        content = ("## 当前已落地功能与研究接入边界\n\n" + common
                   + "LF v2 原生数据适配、明确网格/区域/任务、普通两机构及固定方体机械路径已实施；下方旧草案中的‘未实施/待确认’只描述其历史时点。\n\n"
                   + remaining + " 原细设计无工件.025mm路径已有独立证据；不能由此转移为细工件近接触或同设计网格收敛。\n\n"
                   + limits + f"\n\n最近功能选择：{data['next_step']}；不重做已存在的 LF 优化器。\n\n")
    else:
        content = ("## 当前机械路径、实现修正与持续记录入口\n\n" + common
                   + repair + "：full/chunk 缓存切线与声明确定方向的 fresh HP 通过原门；默认 full、原控制器和范围门保持。"
                   + "旧 pose001 time_limit 失败仅作为成本来源保留，没有拼接为完整路径资格。\n\n"
                   + limits + f"\n\n本轮全部动态结果、失败/修订和后续记录定位于 {record}；下一步：{data['next_step']}。\n\n")
    return (f"<!-- current-front {data['date']}; historical baseline {BASELINE} -->\n\n"
            + content + f"---\n\n## 历史内容（截至 {BASELINE[:7]}，以下原字节保留）\n\n"
            + "以下‘最新/下一步/未完成’均指其当时时点；当前状态以本页上方和本轮总记录为准。\n\n").encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    data_bytes = args.data.read_bytes()
    data = json.loads(data_bytes.decode("utf-8-sig"))
    if set(data["front_sha256"]) != set(FRONTS):
        raise ValueError("Final JSON must bind the seven actual front filenames")
    originals = {name: local(root, name).read_bytes() for name in FRONTS}
    for name, raw in originals.items():
        if digest(raw) != data["front_sha256"][name]:
            raise ValueError("Front changed before update: " + name)
    inputs = {}
    checked = current_card_check(root, data["current_card_directories"], inputs,
                                 {local(root, name) for name in FRONTS})
    pose, soft = (actual_case(root, data[name], inputs) for name in ("pose", "soft"))
    if pose[0]["accepted_states"] != 17 or pose[3] is None or pose[3]["HP_calls_completed"] != 34:
        raise ValueError("Expected the closed actual pose002 17-state/34-HP proof")
    for destination in data["paths"].values():
        path = local(root, destination)
        inputs[path] = digest(path.read_bytes())
    load(root, data["soft"]["task"], inputs)
    output = local(root, data["preservation_record"])
    if output.exists():
        raise FileExistsError(output)
    updated = {name: make_prefix(name, data, pose, soft) + raw for name, raw in originals.items()}
    for path, expected in inputs.items():
        if digest(path.read_bytes()) != expected:
            raise ValueError("Saved source/input changed before writing: " + str(path))
    for name, raw in originals.items():
        if local(root, name).read_bytes() != raw:
            raise ValueError("Front changed before writing: " + name)
    for name, raw in updated.items():
        local(root, name).write_bytes(raw)
    record = dict(status="fronts_updated_old_bodies_preserved", baseline_commit=BASELINE,
        author_script_sha256=digest(Path(__file__).read_bytes()), final_data_sha256=digest(data_bytes),
        card_files_checked=checked, inputs_sha256={p.relative_to(root).as_posix(): h for p, h in inputs.items()},
        fronts={name: dict(old_sha256=digest(originals[name]), new_sha256=digest(raw),
            preserved_old_bytes=len(originals[name]), prefix_bytes=len(raw)-len(originals[name]),
            old_body_exact=raw.endswith(originals[name])) for name, raw in updated.items()},
        new_force_calls=0, new_tangent_calls=0, new_solver_calls=0, new_HP_calls=0,
        qualification="Documentation only; original protocols/raw/scientific flags unchanged")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(dict(status=record["status"], fronts=len(FRONTS), preservation_record=data["preservation_record"])))


if __name__ == "__main__":
    main()
