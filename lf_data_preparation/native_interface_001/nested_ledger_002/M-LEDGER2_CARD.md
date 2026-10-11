# M-LEDGER2：全24保存态载荷账本与加载／卸载分支

2026-10-11（Asia/Seoul），来源准备阶段；本卡尚未获执行授权，尚未调用新账本或绘图。正式 main 基线为 `c4e9f785c3f4068479395002f7c1f3d5ae868b1a`，origin 保持 https://github.com/dudaxing/Compliant-TO-TMC.git。

## 目标、依据及边界

整体目标仍是读取普通LF几何，独立完成HF有限变形／TMC前向评估，提供可核对的反力、工件载荷、实际变形与加载／卸载响应。HF不优化、不导入或调用dmftd，MPM不实现，其他HF线的资格不能替代本项目结果。

M-CYCLE1已有h0.5细网格完整24接受态，M-VIEW1已有真实变形，M-REF2已有自身48次保存态HP参考，M-LINK1关联同一身份的数据。M-LEDGER1唯一执行PASS并已关闭窗口，取得原0／8／13／23四态的七类节点载荷。加载0.95mm时，底边Hu Fy为-0.004663838767376595N，角点为+0.005676849155230292N，整体仅+0.001079446515666051N；整体净值会隐藏局部分区抵消。当前最小下一步是沿原24态看这种抵消如何建立、随卸载如何改变，并对比已有共有位移。

本卡只扩展保存表分类／汇总与显示，不新增平衡路径、F／T／HP、模型、NPZ解码或原观察器。它不实现材料P probe、Hu总边界力、压力、有效夹持、自由工件／摩擦、圆体任务、网格／域收敛、正式标签／排名或HF5。固定下半工件节点弱式力不是连续接触压力，也不能证明释放后的稳定夹持。

## 固定输入与最小实现

保持原84×40mm下半域、h0.5、固定方形中心(71,40)mm／边长18mm、参考身体边界x62..80／y31..40，703标准工件节点，材料E1MPa／ν0.3／厚度20mm，原平均输入0→1.2→0mm。不改几何、软硬度、行程、控制端口或求解验收。

原状态索引0..23及顺序保持，输入目标为：

`0,.25,.5,.65,.75,.8,.85,.9,.95,1,1.05,1.1,1.15,1.2,1.15,1.1,1,.9,.8,.75,.65,.5,.25,0`。

复用公共[saved_workpiece_loads.py](../../../hf_repo/src/hf_eval/saved_workpiece_loads.py)原字节，唯一调用 `summarize_saved_workpiece_node_ledger(..., recorded_states=全部24记录, selected_states=None)`。新[薄caller](execute_full_saved_ledger.py)读取原nodes.csv、summary／result／model／linked_response及24份nodal.json；每个记录保留index／original_target_index／leg／d／state SHA，不能只用d作为身份。完整旧节点表的六个力文本和微小卸载量直接保留，新输出预计24×703=16872节点行、24×7=168类别行。

七类仍是bottom／left／right侧内点、physical_corner、physical_and_cut、cut_interior、body_interior；角点与物理／切面交点向量独立，不向两侧平分。原total／material／regularization(Hu) Fx/Fy均是有符号ON-body弱式力，单位N，原厚度20mm已经包含；不再乘厚度、不除面积、不裁剪、不强制total=material+Hu。公共函数原qualification字符串保留为非力核科学资格声明；caller另记录本次实际全24保存表处理范围，不能把扩展分类称为新全24力核资格。

## 对账、配对与图件

直接whole `float`＋`math.fsum`须精确复现旧nodal及case-summary六分量。七类回并旧四组，counts保持，逐态／分量／方向沿用原 `|error| ≤ 8·2^-52·fsum(abs(original node force))`，无绝对误差地板，零界要求零差。新账本的0／8／13／23完整保存态内容与M-LEDGER1账本逐项一致，只比较已算结果，不重复调用分类器或增设力核门。

共有非零位移为0.25／0.5／0.65／0.75／0.8／0.9／1.0／1.1／1.15mm，共9对；另外origin0与unloading0为1对初始基线比较，必须保留baseline_leg=origin，不能伪称loading0。配对表记录两侧原索引／leg／state SHA、d、类别与六个有符号差值（unloading减baseline），共10×7=70行。卸载没有0.85／0.95／1.05／1.2保存态，不插值或制造配对；差值保留原方向和近零量，不设占比／显著性门，也不自动解释为物理耗散或收敛。

两张Matplotlib图只在获批后生成：

- `path_branches.png`：七类Fx／Fy的total／material／Hu，2×3面板，横轴原输入d(mm)。origin+loading与实际unloading用不同线型，原保存态作点，连线只连接已有样本，不代表额外状态。unloading只画原14..23，不把峰值13伪称卸载态。
- `hu_target_path.png`：2×2面板，左列沿原0..23目标序列显示底边、两物理角点类别、单独右下角node10638与whole净值的Hu Fx／Fy；右列显示10个精确配对d的七类Hu Fx／Fy卸载减baseline差，0点明确为origin基线，全部六分量差见CSV。右下角是physical_corner类别子集，不能与角点类别相加；whole是净合力参考，也不与分区相加。保留符号，不按近零整体净值归一化。左列标明加载／卸载分界与原d，直接观察抵消。

不重画已有位置／峰值图或原24帧GIF。实际结构×1变形继续查看[既有动画](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif)。这些是保存态弱载荷路径图，尚无新的材料应力或变形求解。

## 输出、验收与停止

本阶段 `lf_data_preparation/native_interface_001/nested_ledger_002`，只写此前不存在的 `run_001`：`all_nodes.csv`、`category_loads.csv`、`ledger.json`、`paired_branch_differences.csv`、上述两PNG及`execution_receipt.json`。通用[launcher](launch_ledger.py)原字节复用，另记录`ledger_launch.json`／stdout。输入、来源及原结果／参考／图件字节不改。

PASS须取得唯一实际exit0、无stop、全部协议绑定前后SHA相同；原24身份完整有序，每态703节点完整唯一／参考坐标一致／六力文字保持，七类互斥与原四组合同通过；四态重叠与原M-LEDGER1一致；10对70行身份正确，差值方向明确；一次ledger开始／完成1／1、两PNG写入及全部输出完整，收据保留实际时间、采样RSS及范围。独立终态核对保存文件／身份／文字／绑定及输出，主Agent实际检查图像；它们不重跑分类、fsum、HP或绘图，不冒充新增独立科学参考。

首个输入／身份／分类／闭合／四态重叠／文件／绘图错误，或协作stop／时间／采样RSS越界，即not_pass并停止。无重试、修复重跑、延期或force。静态来源审阅不是上述运行通过证据。旧M-LEDGER1窗口和旧HP额度不续用。

## 资源、授权及后续

新卡建议一次helper180秒／outer240秒／采样8GiB，与既有数据账本的资源模式一致。M-LEDGER1四态实际outer4.4357795秒仅是预算依据，不能当全24运行证据或保证。协作资源／采样RSS非OS硬内存限额，末checkpoint在绑定复查后、成功收据构造前，helper记录该时点资源快照，outer记录完整终态。保持HF原环境与严格科学源码，不改依赖或编译选项。

来源、输入、卡／协议、两图设计先完成独立静审及发布／恢复，然后请求具体新范围与资源授权。本卡尚未授权或执行，启动命令仅作将来入口（cwd真实仓库根，Python路径换机器时使用自己的HF环境）：

```powershell
& 'D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe' -X utf8 -B lf_data_preparation/native_interface_001/nested_ledger_002/launch_ledger.py ledger --protocol lf_data_preparation/native_interface_001/nested_ledger_002/protocol.json
```

下一步由实际24态分区结果决定外邻材料Piola P诊断的最少态；P·N仅为材料分量，不能当Hu模型总压力。长期仍需完成可解释的接触指标、任务与适用范围，再进入本项目正式标签和外部研究比较；全项目未完成。
