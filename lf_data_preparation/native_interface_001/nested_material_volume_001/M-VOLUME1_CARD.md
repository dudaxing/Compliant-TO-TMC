# M-VOLUME1：两态、两底边外邻单元的九点保存材料体积诊断卡

2026-10-11，基线为已实际发布／增量恢复的 main `1671e2d01db3f96718d76ca985199bf3fc65873f`。本卡是源码候选和待批准执行方案；M-SUPPORT1 已实际 PASS 并闭卡，本卡本身不是新执行授权。

## 目标与当前证据

整体目标仍是读取普通 LF 几何，在独立 HF 有限变形／TMC 正向任务下提供可解释的反力、工件载荷和实际变形，供外部研究比较。HF 不优化、不调用 dmftd；main 开发，origin 保持 `https://github.com/dudaxing/Compliant-TO-TMC.git`。

M-SUPPORT1 已将峰值材料 weak 与旧 line 的主要差定位到底边外邻支撑：loading 1.20 mm 的 bottom_owner Fy 为 +0.12182859983276352 N，旧 bottom line 为 +0.02767261448134528 N；差 +0.09415598535141824 N。corner_only 合计 +0.00009348741040979886 N 不能解释该量级。这些是既存数值，不是本卡新计算。

最近一步只研究原 index／original_target_index 6（loading、0.85 mm、state SHA `2d19d368d255e5966c880502f444386c2d56336e7201a017e849f3fcd7ae61dd`）和 13（loading、1.20 mm、state SHA `b9024263e887e0f0813c8ef64c6686f0b65899555bad19cf67a98f293958d7ed`）中底边外邻 **10406／10407** 两单元。两单元分别与身体底边 [79.0,31.0]—[79.5,31.0]／[79.5,31.0]—[80.0,31.0] mm 相邻。峰值保存选中材料弱 Fy 为 +0.037219775006120934／+0.08022435531475952 N，旧同 owner 上缘 line 为 +0.004917548552353244／+0.01938390857410906 N。

本次回答九点 P 的哪些 eta 层形成材料体积贡献，以及保存 weak、舍入后 P 体积观察和上缘迹之间的实际差。它是接续功能的局部解释步骤，不重新求解、扩大到 24 态或预判连续物理原因。

## 输入、读取范围与源码

来源和字节 SHA 冻结于 `protocol.json`；输入核查／物理依据分别为 `author/input_scope.json`、`author/physical_basis.json`。新公共入口 `hf_repo/src/hf_eval/saved_material_volume.py` 只接收普通 NumPy 数组；本目录薄 worker 不导入旧核、模型加载器或观察器。

仅解码 **3 个既存 NPZ／9 个指定数组字段**：model.npz 一次取 coordinates、connectivity、points、grad、weights；两份原 forces.npz 各取 stress_first_piola、element_material_force。逐字段核原 dtype、shape、C-order raw SHA。完整存储字段按既存格式读取一次；新计算／输出仅限四个 state/cell 组合。原 body cell/node IDs 来自 model.json，原 state/result、旧材料 trace JSON、原 M-SUPPORT1 `cells.csv` 作身份和原值关联；不读取其大 `support.json`。

不解码 solid、workpiece_nodes、lift／fluctuation、F／J／Hu、全局力、总力／正则力、切线；不重建 F/Hu，不重播原 DD 收缩。原 top trace T 复制原记录，不调用旧观察器重算该记录；C_+ 仍是本卡新计算的几何层观察。不得调用 force/kernel、本构、切线、HP、Newton／平衡或 LF 优化。保存 P 已经舍入，原 element_material_force 也在原补偿收缩完成后独立舍入，二者不能静默换成同一数值定义。

## 最小算法与对账

每态一次 API。核原 BL／BR／TR／TL、xi 慢／eta 快的九点顺序、正向轴对齐 h=0.5 mm 矩形、厚度 20 mm、原 NumPy `grad`／`weights` 表达。核选中局部节点正好 TR=2／TL=3，并与旧 trace owner/top/body node pair、旧 support cell 连通性和身份精确关联。保存原八个局部材料内力分量；`W_i = -fsum(r_TR,i, r_TL,i)` 须精确数值等于原 M-SUPPORT1 同 cell 的材料 ON-body 投影，不增加厚度因子。

选中基函数和 `chi = N_TR + N_TL = (1+eta)/2`，原梯度和须精确为 `(0,1/hy)=(0,2/mm)`。计算只用保存 P 的 **Y 列两个分量**；九点全 P 字段已声明读取，原 top 三个完整 P／PN 仅作旧 trace 身份检查，输出采样保留 36×2 个有符号 P_iY 值。

每点 `q_i(q) = -w_q * P_iY(q) * (grad_TR,Y + grad_TL,Y)`，其中原保存 w 已含厚度。`V_i = fsum(九个同批 q_i)`；每固定 eta 的 `Q_eta,i = fsum(同层三个同批 q_i)`。三个 Q 是可加的体积分贡献。**唯一新增算术门**是 `abs(fsum(Q_-,Q_0,Q_+) - V) <= 8×2^-52×fsum(abs(同九个 q))`，逐分量、无绝对地板。它只核同批计算项的求和重组，不是材料力精度或物理验收门。

另作描述性的几何层观察：`C_eta,i = -t*hx/6 * fsum([1,4,1]*P_iY(xi,eta))`，`V_geometry=(C_-+4C_0+C_+)/6`，`D_geometry=(C_-+4C_0-5C_+)/6`。原 top line T 精确复制旧 trace，不调用旧观察器重算该记录；C_+ 仍是新计算的几何层观察。在实数代数中 C_+ 是 top 表达、D_geometry 是几何体积与 top 表达的差；实际独立浮点系数与原保存 w 有不同舍入，不能要求同字节。

保留七个 **有符号、描述性** 差：W−V、V_geometry−V、C_+−T、V−T、D_geometry−(V_geometry−C_+)、W−T、D_geometry−(V−T)。这些差不设相等、百分比、近零或 16／32eps 跨公式门。尤其不要求舍入 P 体积 V 等于原补偿 weak W，不把 line 与 volume 的差当舍入噪声或用 Hu 补平。原 M1/M2/SUPPORT/TRACE/HP 规则和资格保持。

## 输出与可视化

新 `run_001` 保存 `material_volume.json`；三 CSV 为 `samples.csv` **36 行**、`depths.csv` **12 行**、`cell_comparisons.csv` **4 行**。保留态身份、cell／body node IDs、九点顺序和位置、P_iY、原体积权重、基函数梯度、每点贡献、每层 Q/C、原八内力分量、W／T／V／V_geometry／D_geometry、同项重组误差／界及七个描述性差。CSV 保留实际 float 值，不以图上的格式化数字代替。

仅新绘 **2 PNG**：`nine_point_material_P.png` 显示四 case 各九点保存 P_iY，两分量各自有符号色标、原 xi/eta 顺序和数值注释；`material_depth_volume_comparison.png` 显示每 case、每分量的 Q_-／Q_0／Q_+ 三个可加贡献，以及单独 V／W／T 对比。每 panel 独立量级并标数字，图上明确仅前三 Q 柱可相加。C_eta 保留于表／JSON，不误当体积贡献直接相加。保持符号、不平滑、不截负值；参考采样不是实际变形、层值不是压力。

另存 `execution_receipt.json`，合计 **7 个输出文件**。实际结构／变形通过原 M-PTRACE1 `actual_material_trace.png` 和既存 24 帧 GIF 链接对照，不解码未经本卡批准的位移字段或重画结构。

## 检查、预算、完成与停止

先完成源码／AST、普通 JSON／CSV 身份、原字段声明与字节、owner／梯度／符号、最小代数门和图用途的独立静审；静审不声称已解码数组、积分或绘图。批准后唯一运行核全部冻结绑定、3 档案／9 字段、2 API 完成、四 cell 的精确原值关联和同项重组、36／12／4 行、六产物文件名、2 PNG 与进程终态收据。

复用原通用 launcher 字节，helper **180 秒**、outer **240 秒**、采样 RSS **8 GiB**。当前既存两态读取／观察均为秒级证据，本卡字段包括完整 P 与 grad/weights，但只处理四 cell；保留明确的连续小窗口和原采样合同。child 在读／处理／写之间核停止／资源。输出 SHA 后末 checkpoint；helper 时间／RSS 为成功收据构造前快照，outer 覆盖完整进程终态。采样不是 OS 硬限，段内工作可能下一 checkpoint 才停止。

**一次启动，首错停止，无重试、修复重跑、延期或 force。** 身份、字段、拓扑、原对账、新同项重组、资源或输出异常按实保留并闭卡，不放宽门或修原保存值。剩余时间不扩 cell／状态／功能。成功后独立核实际收据／CSV、人工查看两图像素，记录目标、行动、理由、结果、效果与限制，再提交推送 main 和增量恢复核对。

若实际 V 接近 W，只报告实际有符号余差及 Q 分层解释；若二者有明显分离，先停在实际差异，再准备独立的原收缩来源诊断，不能静默重建 P 高／低字或新跑力核。九点不能提供真实连续应力场及其 DivP；本卡不计算其它面通量或应力跳跃，也不证明这些因素或求解器缺陷。总 Hu 边界作用／压力、有效夹持、自由体／摩擦、网格收敛和正式 HF5 标签排名仍未完成。
