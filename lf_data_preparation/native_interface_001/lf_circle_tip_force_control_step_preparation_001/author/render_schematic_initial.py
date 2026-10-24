"""One-pass conceptual control/state diagram from ordinary preparation metadata.

No FE call, saved scientific array, old media or geometry is used.  The figure
is a schematic of provenance and control, not actual gripper deformation.
"""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

AUTHOR = Path(__file__).resolve().parent
FONT = FontProperties(fname="C:/Windows/Fonts/msyh.ttc")
BOLD = FontProperties(fname="C:/Windows/Fonts/msyhbd.ttc")


def identity(path):
    raw = path.read_bytes()
    return dict(path=path.as_posix(), bytes=len(raw), sha256=sha256(raw).hexdigest())


def main():
    started = perf_counter()
    contract_file, binding_file = AUTHOR/"CONTRACT.json", AUTHOR/"SOURCE_BINDING.json"
    contract = json.loads(contract_file.read_bytes())
    binding = json.loads(binding_file.read_bytes())
    assert contract["status"] == "candidate_not_approved_not_executed"
    assert binding["status"] == "prepared_not_executed"
    P0, P1, P2 = contract["loads"]["full_targets_half_N"]
    assert P2 == P1+(P1-P0)/4
    inherited = contract["numerical_inheritance"]
    q1, R1 = inherited["initial_absolute_q_mm"], inherited["initial_signed_R_N"]
    assert inherited["held_mean_mm"] == 1.06
    png, svg, receipt = (AUTHOR/name for name in
        ("control_schematic.png", "control_schematic.svg", "SCHEMATIC_RENDER.json"))
    assert not any(p.exists() for p in (png, svg, receipt)), "Preserve the one-pass output"
    blue, teal, orange = "#245d86", "#146c62", "#a95616"
    dark, muted = "#1f3040", "#526578"
    fig = plt.figure(figsize=(16, 10), facecolor="#f4f7fa")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    def text(x, y, value, size=13, color=dark, weight=False, ha="left", va="top"):
        return ax.text(x, y, value, fontsize=size, color=color,
                       fontproperties=BOLD if weight else FONT,
                       ha=ha, va=va, transform=ax.transAxes)

    def box(x, y, w, h, face="white", edge="#d0dce5", dashed=False):
        patch = FancyBboxPatch((x, y), w, h,
            boxstyle="round,pad=0.009,rounding_size=0.012", linewidth=1.5,
            facecolor=face, edgecolor=edge, linestyle=(0, (5, 4)) if dashed else "solid",
            transform=ax.transAxes, zorder=1)
        ax.add_patch(patch)
        return patch

    text(.055, .954, "正式 r9 非零 q 保存态：下一小载荷段准备", 25, blue, True)
    text(.055, .901, "控制与状态关系示意  ·  非实际结构、变形或新有限元结果  ·  本轮尚未求解", 14, muted)
    text(.945, .949, "L-CTIPFSTEP1 / 准备", 12, orange, True, ha="right")

    for x, edge, fill, dashed in ((.055, "#97aabb", "#edf2f6", False),
                                   (.37, teal, "#edf7f4", False),
                                   (.685, orange, "#fff7ef", True)):
        box(x, .610, .26, .224, fill, edge, dashed)
    text(.072, .813, "已完成 HIGH1 · 原目标 0", 16, blue, True)
    text(.072, .768, f"P0 = {P0:.15e} N", 12)
    text(.072, .729, "q0 = 0 mm", 13)
    text(.072, .690, "R0 = 0.1952230415 N", 13)
    text(.072, .651, "历史起点，保持记录，不重新计算", 12, muted)

    text(.387, .813, "已完成 HIGH1 · 直接续载父", 16, teal, True)
    text(.387, .768, f"P1 = {P1:.15e} N", 12)
    text(.387, .729, f"q1 = {q1:.13f} mm", 13)
    text(.387, .690, f"R1 = {R1:.12f} N", 13)
    text(.387, .651, "保留原 split 与非零绝对 q / P / R", 12, teal)

    text(.702, .813, "候选新原目标 2 · 尚未执行", 16, orange, True)
    text(.702, .768, f"P2 = {P2:.15e} N", 12)
    text(.702, .729, "q2：由求解确定，未指定答案", 13, orange)
    text(.702, .690, "R2：由新平衡求解确定", 13)
    text(.702, .651, "只追加小载荷，不回放旧父路径", 12, muted)
    for x0, x1, color, label, dash in ((.320, .365, blue, "历史", False),
                                       (.635, .680, orange, "待执行", True)):
        ax.add_patch(FancyArrowPatch((x0, .721), (x1, .721),
            arrowstyle="-|>", mutation_scale=18, linewidth=2, color=color,
            linestyle=(0, (4, 3)) if dash else "solid", transform=ax.transAxes))
        text((x0+x1)/2, .752, label, 10, color, ha="center")

    text(.5, .572, "完整来源前缀 [P0, P1, P2] 保留；未来实际只算 [P1, P2]：非零 q1 fresh 检查 ＋ 新 P2", 14, blue, True, ha="center")

    box(.055, .297, .425, .238)
    box(.52, .297, .425, .238)
    text(.072, .512, "保持机构输入，工件沿原导向平移", 16, blue, True)
    lines = ["机构：加权平均输入保持 1.06 mm",
             "工件：仅原导向刚体 x 平移 q 未知",
             "继承非零 q1 / P1 / R1 / lift / fluctuation",
             "半模型 P 已含 t=20 mm；完整镜像轴向 2P",
             "q 不倍增；输入 R 与工件外载 P 分别报告"]
    for y, line in zip((.468, .431, .394, .357, .320), lines):
        text(.072, y, line, 13)
    text(.537, .512, "原 P0 尺度与原验收规则保持", 16, teal, True)
    lines = ["SP = max( |P|, |原 P0|, Ffloor )",
             "原 P0 不换成 P1；此正增段实际 SP=P",
             "原数值门不变；新 P2 无给 q 或 HP 参考",
             "q2 不设答案、夹限或指定目标",
             "Nmin 保持；该段至多 fresh＋4 叶 = 5 态"]
    for y, line in zip((.468, .431, .394, .357, .320), lines):
        text(.537, y, line, 13)

    box(.055, .105, .89, .150, "#fff9ed", "#d8bc80")
    text(.072, .237, "必须保留的困难与执行边界", 15, orange, True)
    history = ["父态 min J ≈ 4.1661×10⁻⁴；轴向 Hu 约 72.58%",
               "旧给 q 路径的 invalid_J、q=.0125 内部二分态保留",
               "导向总弱力平衡不等于压力、纯接触抗拔或承载极限"]
    windows = ["候选 controller 1800 s；helper 3000 / outer 3060 s",
               "允许原内部回溯／二分；首个终端错误停止",
               "本轮仅准备：无新求解、HP、参考误差或资格升级"]
    for y, left, right in zip((.200, .167, .134), history, windows):
        text(.072, y, left, 12)
        text(.54, y, right, 12)
    text(.055, .069, "原物理保持：r=9 mm，圆心(80,40) mm，右域界92 mm，Lr=80 mm，α=2.5e−7；其余材料、边界与非 clock 设置保持。", 12, muted)
    text(.055, .035, "数值按已绑定普通元数据列示；P2 = P1 + (P1−P0)/4。新 q2、R2、变形与收敛需另行获批试算后才能报告。", 11, muted)

    fig.savefig(png, dpi=170, facecolor=fig.get_facecolor())
    fig.savefig(svg, facecolor=fig.get_facecolor())
    plt.close(fig)
    result = dict(stage="L-CTIPFSTEPPREP1", status="rendered_pending_root_visual_check",
        render_attempts=1, new_raster_images=1, new_vector_images=1,
        concept_only=True, actual_geometry_or_deformation=False, new_FE_results=False,
        source_ordinary_files=[identity(contract_file), identity(binding_file)],
        font_files=["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"],
        figure_inches=[16, 10], dpi=170, image_outputs=[identity(png), identity(svg)],
        numerical_solver_calls=0, HF_imports=0, scientific_NPZ_reads=0, old_media_reads=0,
        pixel_inspections=0, rerenders=0, elapsed_seconds=perf_counter()-started,
        note="One conceptual render from ordinary metadata; root owns the single visual inspection. Not a real geometry, predicted q or new force result.")
    receipt.write_bytes((json.dumps(result, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))
    print(json.dumps(dict(status=result["status"], outputs=[str(png),str(svg)],
        elapsed_seconds=result["elapsed_seconds"], scientific_calls=0),ensure_ascii=False))


if __name__ == "__main__":
    main()
