# L-CTIPAUNLOAD3：新α圆形工件剩余五目标卸载

准备日期2026-10-20（Asia/Seoul）。用户已明确批准按AUNLOAD2发布的计划实施并执行本卡；只在最小包装与独立有限静审通过后唯一启动。数值运行、实际显示、像素检查和发布分别记录，不预写成功。完成日期取实际时间。

## 整体目标、已有工作和本次用途

整体目标是独立HF读取普通LF几何，在一致任务下获得可恢复的非线性/TMC响应与工件作用，供外部研究层比较；HF不承担LF优化。此前已实现NumPy完整力、组装/切线、平均端口平衡、保存态延伸、独立高精度参考、普通LF输入及实际变形显示。本轮聚焦圆形工件加载后的卸载功能与同位移对照。

α=2.5e−7已从零完成原13加载目标至1.06 mm；该峰值HP80/120与原十五项门通过。AUNLOAD1完成1.06→1.05，AUNLOAD2完成1.05→1.00，保原生产门，两段均无失败/二分。1.00末态输入R=0.17707577676004574 N、下半模型工件总Fy=0.004616547361084258 N、介质minJ=0.03400285281143686；五图检查通过。同位移差很小属于描述，不据此授可逆性。

本卡完成余下0.90、0.75、0.50、0.25、0 mm请求，展示力、尖端和介质随卸载的实际表现，并与原加载/起点逐项对照。已有收敛支持在原停止规则下安排五个目标，不将前一步J回升视为后续通过保证。

## 输入与物理边界

- 正式Git根：`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`；main基线`ed9b2911f2a7ec7f2b400b7f904e4be8b708ad80`；origin`https://github.com/dudaxing/Compliant-TO-TMC.git`。
- 作者目录：`D:/hf-native-workpiece-api-author-20261020/L_CTIPAUNLOAD3_preparation_001`；新阶段`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_003`。
- 父结果：`lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_002/run_001/wave_circle_tip_alpha_unload2/result.json`。选accepted1/global14/raw leg unloading、1.00 mm；canonical split身份`0a7602917a1c49bc0950b67b604beedefc1fb8acad4c831e2fcbc46e388ea37d`，保原signedR。
- 普通参考：ALPHA1 `run_001/view/wave_circle_tip_alpha1/summary.json` rows[4,3,2,1,0]。分别匹配新global15..19的[.90,.75,.50,.25,0]；前四参考rawleg loading，零态rawleg origin。原1.00对照保历史，不计新五组。
- 旧科学输入仅父source geometry NPZ四mask与selected state NPZ lift/fluctuation两字段。准备继承原producer SHA/bytes并stat；唯一helper内才核字节和必要解码。禁止旧model/force/tangent/matrix数组、科学gzip、CSV或旧媒体输入。

保持α=2.5e−7、固定圆形r9 mm/圆心(80,40) mm、right92 mm、Lr80 mm、下半域92×40 mm、h0.5 mm、14720单元/29970DOF、厚20 mm、E1 MPa、ν0.3、plane strain、γ1e−6、原支撑/平均端口/对称条件。

task保持ordered_cycle及15目标前缀`[0,.25,.50,.75,.90,.95,.98,1.00,1.02,1.03,1.04,1.05,1.06,1.05,1.00]`，仅追加`[.90,.75,.50,.25,0]`形成20目标任务。全部其他字段/四项metadata不改，input.target_mm保持1.06。只执行suffix`[1.00,.90,.75,.50,.25,0]`、global14..19，不重放前缀。本层无新task_transition；parent_continuation是AUNLOAD2，再下一层为含first-unload转换的AUNLOAD1，其祖先parent_continuation为None。

## 实施、原门和实际显示

1. 薄适配既有同kind研究包装，绑定任务/输入/59份源码闭包。准备与独立有限静审通过后freeze并唯一启动。默认HF源码、依赖与安装保持；不新加测试。
2. 只恢复split与signedR，通过公开API鲜算1.00锚F/T并核完整canonical身份与bitwise R，再依序执行五个目标；不移植旧力、切线或矩阵。
3. 原生产门保持：相对残差≤1e−9；native均值约束原尺度规则/constraint_tolerance1e−10；global_force_balance≤1e−6；fixed split≤8e−11 mm；J>0。非clock设置不变：max_checks25、Armijo1e−4、max_backtracks12、max_bisections4、minimum_increment0.00625 mm及原二进制比较。
4. 仅成功后一次原pure viewer生成4PNG/实际N帧GIF，再投影已有Newton/线搜/二分记录生成1收敛PNG，总5PNG。保全部内部回溯、失败试探及接受二分，不硬写N=6。显示实际×1变形、输入R、工件total/material/Hu Fx/Fy、尖端与Q1边界距离、右侧介质、收敛。全机构镜像仅作显示，下半数值不翻倍。
5. 静态第二态/fields/right-medium取实际LAST0 mm；child argmax仍为1.00锚，与祖先1.06峰值分开，不以旧peak文件名重标。原viewer内部8GiB不变。q_out为加权端口位移，不是间隙；无符号Q1距离与交叉/近触/区域重叠分开，包含未测试。J单元均值与九点最小值、Hu Frobenius与最大绝对分量、右侧裁剪图与全480单元极值分别说明。
6. 五个新原目标各13项原值与“卸载−参考”差，共65行：R_input、q_out、工件total/material/Hu的Fx/Fy、尖端距离、全边界最小距离、solid minJ、medium minJ、medium maxabsHu。以is_original_target/global15..19选态；保原rawleg/index/SHA及全部N态，不按位移去重、不插值、不算新恢复率/能量，不新增相等、归零、单调或滞回门。零态参考保origin；1.00锚不重复计。
7. 原helper窗口内封存输出；五张新PNG各最多一次原分辨率检查，GIF帧数沿producer检查，不额外解码或重绘。若错误，立即停后续科学/显示，保真实partial；只有原helper窗口仍开放时允许一次部分封存。
8. 原始结果、数值门、像素限制、源码对照、实际独审、下一步依据完整记录。更新7份既有入口并保旧后缀；main普通推送，远端main身份核对，同机异目录local Git对象fetch/ff-only恢复及发布回执归档。该恢复不称作另一机器独立重算。

## 唯一资源窗口与停止规则

|项目|限制|
|---|---:|
|controller|5400秒|
|显示共享|600秒|
|helper（含核查/科学/显示/封存）|6600秒|
|outer（含清理）|6660秒，最多111分钟|
|采样进程树RSS|64 GiB|
|OMP/MKL/OpenBLAS/NumExpr|各上限16线程|
|pure viewer内部|原8 GiB|

CPU后端及SUP2同实例清理合同保持；配置16线程不等于实测16核利用。唯一启动、首个终端错误停止；原内部回溯/二分允许。无外部重试、修复重跑、延期、force、新HP、测试、默认源码/依赖修改、安装、API关联、删除、回滚。绑定失配也停止，不调整物理、门或步长下限求通过。

## 完成语义与后续

成功只表示本次suffix完成；target_reached/path_completed/unload_endpoint_reached可true，因child未经过1.06，loading_peak_reached应false；task_target_executed/full原或新路径标志保持false。父加载和两段卸载、峰值独立参考、原失败历史各保原记录。

回到输入0只代表指定回程完成，不授自由释放、几何恢复、稳定性、α独立、接触压力、有效夹持、全路径HP、网格/域宽收敛或HF5资格。工件力保持下半模型有符号弱力。本次完成后先依据真实五组差值、末态、力/J/Hu/距离和收敛，决定功能整合/周期汇总或有针对性的进一步诊断；不预授权新科学计算，不按流程例行逐点补HP。

对照源码：本卡execute_step.py/launch_step.py为研究包装；circle_saved_views.py/plot_convergence.py沿原LAST语义，仅必要身份说明改动；默认hf_repo/src/hf_eval/native_resume.py/native_evaluate.py/split_displacement.py等原字节保持。protocol、authorization、SOURCE_REVIEW、准备/执行/封存/QA/ACTUAL_REVIEW/发布回执分别留存。
