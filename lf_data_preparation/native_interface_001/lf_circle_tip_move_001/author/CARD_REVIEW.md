# L-CTIPMOVE1 独立执行卡审阅

2026-10-22；结论：**计划卡有限静审通过；尚待用户授权，尚无实际候选源码，未运行测试或科学计算。**

审阅基线为 main `1e5e9cf76480254a6a288f27fb10bc884acb4c38` 的精确普通源码文本。审阅对象为本目录当前执行卡、fixture 设计与 controller 设计，不是不存在的候选实现。只写本审阅文件及同名 JSON；未修改正式源码、旧结果或 Git。

## 实际检查

|编号|检查|证据与判断|
|---|---|---|
|1|目标与阶段范围|仅实现 held input 与 prescribed rigid +x 的独立控制合同、小模型文件入口和记录；真实 r9、HP、力控、转动、摩擦及默认固定工件切换均明确排除。与已发布负载规格的最近阶段一致。|
|2|实现闭包|只修改旧 `split_displacement.py`，新增 `native_probe.py` 与一个独立测试文件；其余旧入口、parser、核、切线及 SUP2 不改。不是复制 solver 或新增通用 MPC。若需要超范围文件则停止准备。|
|3|均值与刚体消元|原 C/F 集合保持，body ux 的 lift=q、uy=0，所有 body fluctuation 处方为零；输入仍用原单乘子 KKT、d_hold 恒定。设计定位原10处 mean target 使用点，并保旧独立 offset 补偿求和。默认 fixed lift 防护保留。|
|4|q=0 fresh anchor|旧源码275行以 initial_parameter 真值开门，q=0 确有缺口。新计划要求原 split/R 第一次新 F/T 先于任何投影／预测／修正；门失败 typed initial_state_not_equilibrated；kernel/J 等失败保实际原因。任何 typed anchor 失败均 terminal，不进入二分，成功同时核 split/R 字节身份与 solve 计数。|
|5|saved-file admission|本卡包含真实新小模型保存文件 API；核来源/model/task/geometry/material/boundary/state 字段身份；仅迁移两 split 字段及有符号 R，不用旧 K/F/T 作验证。父 controller SHA 与本次新 controller SHA 分别记录；不篡改旧 task/extend_path/资格。|
|6|fixture 材料与成员合法性|静态按 regions.py 的编号及 native_project.py 的闭圆／passive_void／solid-incidence 门复核：solid=[0..8,12]，void=[9,10,11,13,14,15]，唯一 body cell14，conn=[17,18,23,22]。body四节点均无 solid／support／port 共节点；source mask 不重分。|
|7|fixture 约束与端口|input [10,15,20] 权 [.25,.5,.25]，output [4,9] 权 [.5,.5] 均 solid-incident；顶边实体 uy=[41,43]，背景 uy=[41,43,45,47,49]。body/background 交集[45,47]去重后15处方、35 free，加1乘子为36维。两个不同位置全约束支撑静态去除整体刚体模态；不声称 Jacobian 已非奇异或实际构模已通过。|
|8|旧9项＋新6项|原 test_split_displacement.py 为8函数，split arithmetic 函数2参数展开，共9项；新卡仅6非参数化方法，共15项。原测试文件不改断言与容差。候选尚不存在，必须在唯一启动前重新静核精确展开／调用数。|
|9|路径次数合同|原源码静态控制器调用共12处：11注入、1真实2单元。总≤4真实／≤30注入或输入拒绝意味着新文件≤3真实16格、剩余注入或拒绝≤19；卡在数量上可行。原方法4次 warm 调用不可少计。实际候选如多于上限不能启动，也不把 fresh F/T、拒绝分支冒充独立物理路径。|
|10|物理与数值验收|free≤1e-9、mean≤1e-10×max(d_hold,1e-6)、J>0/有限，body逐节点／零支撑≤8e-11 mm；真实小模型承担 global≤1e-6。工件ux驱动／uy导向／其余支撑互斥，ON-body=-sum internal，drive=+sum body-x internal，半模型N已含t2。合成非守恒残差不被用来证明物理global门。|
|11|窗口、首错与显示|tests180／显示60共享helper300／outer360秒、8GiB／线程16；复用原SUP2同实例终止／成员覆盖／句柄释放。单一数值启动、pytest -x、首错停止显示/安装，无修复重跑／延期／force／删除／回滚。图仅从新小模型缓存生成一次，明确实际×1与两控制量；不重算mechanics。|
|12|安装与发布边界|全部通过且图像检查通过后才按已测字节安装 controller+probe；旧固定入口默认合同不切换、不加__init__/CLI默认接线。卡中用户批准的是这一显式 opt-in 安装范围。记录实际部分安装与失败，不自动回滚；普通 main 发布／异目录恢复不被混称新数值验证。|

## 审阅发现与关闭

原 `CONTROLLER_CHANGE_DESIGN.json` 将新测试写为 `test_native_probe.py`，执行卡采用 `test_native_guided_probe.py`。已反馈 root，root 统一 JSON 文件名；本审阅绑定修正后的当前字节。新增静态 S/M/B 格子示意与实际 fixture 表一致，明确不是计算变形。

未发现当前计划卡阻断。**以下属于实施后的启动前置，当前均未完成：** 实际候选编写、候选源闭包冻结、完整命令/短临时目录冻结、有限源码静审、精确15项与真实/注入调用次数核验。计划通过不能替代这些步骤，也不能成为当前的数值许可。

未查看实际新候选，因为它不存在；未确认实际构模、收敛、缓存读回或图像效果。小模型 q=[0,.00025,.0005]、d_hold=.0005 与真实候选 q=[0,.025]、d_hold=1.06 不是同一物理证据。

## 审阅方式与限制

本审阅只读普通 .md/.json/.py 文本并核普通文件 size/SHA，未 import HF、未执行构模/力/切线/HP/平衡/测试、未读 NPZ/CSV/gzip/媒体、未改正式 Git。一次普通源码搜索曾包含不存在的猜测文件名 `native_acceptance.py`，只产生未找到错误；随后通过实际文件清单及现有规格核清 wrapper 门来源。一次 PowerShell 读文件／取 SHA 命令因 foreach 管道语法未解析而退出，未执行其命令体；修正后仅完成文本与身份读取。两者均不涉及数值执行或重跑。

同名 JSON 绑定执行卡、两设计及 PREPARATION_STATE 的实际当前 SHA；本审阅结论只适用于这些字节。