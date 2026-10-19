# L-CTIPLOCAL3：1.05/1.06 mm保存态尖端与介质极值定位

用户已明确批准“批准按 L-CTIPLOCAL3 计划实施并执行”，对应main 6e77bf0的STEP10/NEXT_STEPS。整体目标是把LF几何接入独立、可恢复的TMC大变形分析，审查接近工件、结构变形和作用力；当前补足强压缩区的空间证据，再决定HP或后续加载。

本卡只观察STEP10真实scientific result的accepted0/global11/d1.05与accepted1/global12/d1.06，后者SHA dd9288140ae51ff3cfcc7f7f6d6811b2242a55054454002bd7c06ff88a4b6bc6。保持r9 mm、圆心(80,40) mm、固定工件ux/uy、right92 mm、Lr80 mm及全部材料、网格、边界、端口、原设置和验收门；保完整嵌套历史。不推进1.07 mm，不重放旧路径或构模。

一次helper180秒／outer240秒、采样8GiB、四库线程上限16。仅5份既存NPZ／12字段：model.npz的coordinates/connectivity/solid/workpiece_cells；两state.npz各lift/fluctuation；两forces.npz各J/Hu。准备与闭卡只用原producer seal/stat；NPZ hash和所选字段各一次解码仅在唯一新helper窗口内。普通result/summary/描述/derived/geometry复用原身份、尖端和最近边界见证，不新增距离搜索。不读F、应力、力数组、切线、矩阵、旧媒体或CSV。

复用LOCAL1观察算法及LOCAL2已修布局：medium rect=(0,.075,1,.85)，suptitle y=.985。坐标保持原左结合coordinates+lift+fluctuation，实际×1等比例；掩码~solid排除workpiece_cells。J九点Simpson包括角点，xi慢/eta快；保原单元/采样点/参考与实际坐标及第一C-order精确并列数。Hu逐单元常值，保绝对最大组件、符号/ijk/并列，Q1中心只作代表标记。每态medium minJ、maxabsHu、tip坐标与原tip距离见证四项精确对账，共8项，无新阈值。

输出tip_closeup.png、medium_locations.png、localization.json和manual.html共四份。只链接既有反力和收敛图，核普通记录及存在大小，不解码旧媒体；无新GIF。两个新PNG最多各一次实际像素检查，不自动重绘。执行状态、视觉QA和阶段完成分别记录；LOCAL1原视觉失败、LOCAL2修复及所有原结果/历史保留。

先完成包装和有限独立静审，再唯一启动；首个终端错误停止并保实际partial，仅原窗口内封存。无外部重试、修复重跑、延期、force、回滚、删除、新构模/F/T/HP/Newton/平衡求解、测试、默认HF修改或安装。

记录整体目标、本轮原因、实际位置与原值、完成内容和效果；普通main推送及同机异目录local Git对象恢复核对，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。此观察不授完整路径、独立参考、连续压力、有效夹持、自由释放、稳定性、网格/域宽收敛或HF5资格。新位置产生后再安排下一范围，本卡不自动继续。
