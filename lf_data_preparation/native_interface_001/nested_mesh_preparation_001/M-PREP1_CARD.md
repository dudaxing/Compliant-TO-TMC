# M-PREP1：同设计派生细网格构模与显示卡

2026-10-09（Asia/Seoul）。状态：候选源码及协议已准备；源静审归档后待明确批准，只执行一次。原W-API1/W-VIEW1窗口已关闭。此卡没有授权细网格平衡、HP或接触资格。

## 目标与具体输入

将W-API1保存的h=1 mm几何精确细分为h=0.5 mm，验证同一物理结构可供现有构模入口读取。只新增[nested_geometry.py](../../../hf_repo/src/hf_eval/nested_geometry.py)及本阶段[执行脚本](author/prepare_nested_model.py)，复用原native构模、geometry writer和Q1算子；原生产/参考/响应入口保持。

父几何为`lf_data_preparation/native_interface_001/workpiece_forward_001/run_001/fixed_square/model/source_geometry/geometry.json`及相邻NPZ；父任务和模型字段取自该模型的`model.json`、`model.npz`。精确身份冻结在[protocol.json](protocol.json)。任意clone目录以显式repo为根，不访问LF环境或历史绝对路径。

只细分四掩码的每个父格为2×2同值子格，不插值、不重新阈值、不清理或优化。物理单元并集、域、厚度、半模型、所有region tags与原材料保持。派生包记录父哈希及`whole_grid_is_LF_native=false`；task的`native`指供应的派生HF网格，构模器不再改变该输入。更新task ID/geometry绑定及说明，逐项严格比较其他所有物理字段。

保持84×40 mm域；方形固定工件center(71,40)、side18、下半范围[62,80]×[31,40]；E=1 MPa、nu=.3、thickness=20 mm、gamma=alpha=1e-6、Lr=80 mm、plane strain。支持[0,0]→[0,8]只选solid incident；实体对称[0,40]→[60,40]，任务背景对称[0,40]→[84,40]；原输入[0,38]→[0,40]、输出[80,28]→[80,30]。输入仍为平均位移，输出弹簧0。原24个0→1.2→0 mm目标保存在task中，**本卡不执行它们**。

## 唯一一次执行

1. 核对绑定与新输出目录；生成一个HF-derived几何包。
2. 验证四掩码每个子格、面积、连续边界、父身份、派生身份和网格所有权；准备派生task。
3. 一次`build_native_project`和一次`write_native_project`，仅参考算子、材料数组、端口与位移集合。
4. 检查13,440单元、13,689节点、27,378 DOF；独立物理方框选择应有648工件单元、703节点、1,406 body DOFs；实际合并fixed/free数量写出。
5. 同一2mm端口重新积分，应为5节点及[.125,.25,.25,.25,.125]；用独立仿射位移场验证归一化线积分，确认端口方向不交固定DOF。验证材料父子值、物理kr/Lr、单元积分测度和保存字段哈希。
6. 一次生成包含父几何、细几何、尖端细网格/端口节点的三联PNG，标明未变形。最终核对原绑定，保存检查与终态。

输出只在本阶段`run_001/`：派生geometry、task、model、`checks.json`、`phase.json`、`nested_geometry.png`；外层启动回执与stdout属于本阶段。源审阅属于静态证据，数值和图只有实际执行后才成立。

预算：helper连续180秒、outer240秒、采样进程树RSS≤8 GiB，一次窗口。预计工作量是四倍粗单元的构模/存储及一张小PNG，远小于完整求解；该预期不是实际计时。沿用已验证的启动包装，协作检查点和采样RSS；无OS硬内存上限、无force终止。同步库调用只能在返回后检查helper限时；超限即NOT_PASS，不能宣称绝对硬截止。

具体命令（**尚未执行**）：

```text
<HF-python> -X utf8 -B lf_data_preparation/native_interface_001/nested_mesh_preparation_001/launch_prepare.py prepare --protocol lf_data_preparation/native_interface_001/nested_mesh_preparation_001/protocol.json
```

## 门、停止条件与后续

任一绑定、物理不变量、选择/形状/哈希、资源或保存检查失败，立即结束本卡，保留已生成输出和异常，无修复重试。原机械门不变，本卡没有新机械响应，不能据构模检查声称平衡或接触通过。仿射积分及积分测度绝对误差≤1e-12，掩码/物理元数据/材料字段保持精确相等；这些是本次新构模不变量，不能替代旧生产门。

新力/切线/平衡/HP/JIT执行/LF调用为0；仅HF构模所需导入，JAX模块被导入不代表执行JIT。未调用保存态观察器；一次PNG只显示未变形几何。没有新qualified response、压力、夹持力结果或全列切线资格。

通过后独立审阅真实模型与PNG，再依据实际数量/构模内存和既有h1成本制定h0.5完整路径卡。未来比较按原目标与加载/卸载分支匹配；维持物理Lr，不随h缩放。两网格只报告敏感性；完整参考、保存观察与收敛需要各自的新证据和具体预算，不借本卡剩余时间启动。

需新的明确批准，是因为此前用户要求资源授权和阶段范围不能静默改变：本卡新增派生数组、构模和绘图，已有关闭窗口不覆盖它们。源码、协议与静审先完成，批准后执行一次。
