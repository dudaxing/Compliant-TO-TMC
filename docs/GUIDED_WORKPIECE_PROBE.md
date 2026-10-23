> 2026-10-23 L-CTIPLOWPREP1 **低输入对照准备完成，尚未试算**：新固定工件父任务从零[0,.25,.50] mm，成功末峰后保持机构均值.50，仅推进工件q=[0,.025] mm；[任务、接口核查与控制示意](../lf_data_preparation/native_interface_001/lf_circle_tip_low_input_preparation_001/PREPARATION.md)已记录。其余物理和原门保持，生产源码未改；候选L-CTIPLOW1待新授权实施与执行。下方为较早阶段历史状态。

> 2026-10-22 L-CTIPPROBE1 **真实探针数值PASS**：input mean保持1.06 mm，工件q=0→.025 mm，经原内部二分共3接受态；3PNG／3帧实际动画及[结果与证据](../lf_data_preparation/native_interface_001/lf_circle_tip_probe_001/RESULTS.md)已记录。生产源码保持；轴向Hu分量较大，尚不授纯接触／承载／释放资格。近期先准备同定义低输入对照。下方较早阶段状态保留为历史时点。

# 导向刚体工件探针：显式API

2026-10-22。L-CTIPMOVE1已完成受限小模型验证并安装。入口为`hf_eval.native_probe.evaluate_native_guided_probe`；原默认固定工件入口保持。实际范围与数值见[阶段记录](../lf_data_preparation/native_interface_001/lf_circle_tip_move_001/RESULTS.md)。

该函数解决“保持机构输入均值，同时规定刚体工件沿+x移动”。它给出驱动反力，不等同指定外载下的自由工件承载测试。

```python
from hf_eval.native_probe import evaluate_native_guided_probe

# 例示小模型参数，不是运行许可；parent必须由完整固定工件加载成功产生。
response = evaluate_native_guided_probe(
    saved_result=parent_result_file,
    selected_state_index=terminal_accepted_index,
    body_q_targets_mm=[0.0, 0.00025, 0.0005],
    output_directory=new_output_directory,
    time_limit_seconds=60.0,
)
```

`parent_result_file`可位于任意克隆／恢复路径，但内部文件及声明身份须完整。父任务必须是成功完整的fixed_rigid／load_only加载，所选态是最后一个原请求峰值，不能把普通旧suffix／extension或现有probe结果伪装成来源。d_hold、材料／厚度、原边界、几何及非clock数值设置从该源绑定继承；新q目标必须从0严格增加，工件节点／单元不重选。输出目录必须全新且在父结果树之外。

新任务q0用原split两数组及有符号R，先执行fresh F/T；不平衡初态拒绝，不投影、修复或继承旧参考资格。新probe状态仅body ux=q、uy=0，保持转角；其他支撑为零，机构只约束原加权平均输入。q=0.025 mm的真实r9实验尚未执行，不能把例示小模型参数换上就称已有结果。

`response`及新`result.json`提供：

|字段|含义|
|---|---|
|status／failure／target_reached|当前新任务成功或真实部分失败，不是夹持／释放资格|
|probe_task|held_input_mean_mm、body_q_targets_mm、运动与单位合同|
|accepted_steps[i].body_q_mm／input_mean_mm|独立的工件位移和机构输入均值，均为mm|
|R_input_N／Q_drive_half_N|机构输入乘子与工件驱动力分开，均为有符号N|
|force_on_body_N|total／material／regularization两分量；是节点弱力合力，不是压力|
|ledger|互斥body-x驱动、body-y导向、其余支撑、输入和global balance|
|state／fields|本态新缓存归档、字段dtype／shape／SHA；state只有lift／fluctuation|
|positions_mm／body_nodes|新实际位置和不变成员；不再用固定旧坐标冒充运动|
|newton_history等|原控制器诊断，其中内部d是stage q，q_in是机构mean；accepted记录已分列命名|
|source／mechanics_source_sha256|原来源身份和本次实际执行源码；不篡改父controller或原资格|

ON-body x为负的body内力之和；没有另加工件外载时，Q_drive_half等于其反号。**力已含来源厚度，不再次乘厚度；API返回半模型N，不自动乘2。** 若向完整对称装配换算，q不变、轴向力2×半模型，完整已知外载进入半模型则除2。原y对称／导向仍可提供反力和矩；不能据此认为自由体已平衡。

保存使用接受态缓存，不重新F/T。身份错误在新F/T之前以invalid_saved_state拒绝；数值终端失败保存已接受partial。timeout／非收敛／零模不标释放。所有新机械资格标记保持false；原选定态HP不转移为可动路径参考。

当前支持单个导向刚体+x、常量正input mean、从q0向正方向推进；未实现probe的保存态延伸、力控制、自由y／转动、摩擦或动力学。小模型通过不证明真实工件可行或域／α独立。近期研究安排沿用[任务规格](WORKPIECE_LOAD_TASK_SPEC.md)。
