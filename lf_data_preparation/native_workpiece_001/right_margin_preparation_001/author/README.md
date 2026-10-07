# Actual gamma1e-6 → 右侧2列准备候选

此目录只为静态作者候选，尚未导入、执行制卡、构造或测试。正式目标为 `lf_data_preparation/native_workpiece_001/right_margin_preparation_001/run_001`；基线仅 `enlarged_square_projection_001` 的 gamma1e-6 side18 完整工况，不混入 gamma-half 系数或状态。

准备一次调用已有新 adapter 生成 x82 的 HF 派生几何，再一次 native_project 构造／保存3280单元、3403节点、6806DOF的新模型；重建 `PORT=b_in/max(abs(b_in))` direction。预算 helper120 / outer150秒、8GiB，原64行 supervisor raw复用。所有资源与源输入最终哈希后再 checkpoint；首异常停止、无重试、无 force。

原40×80四掩码子域 raw保持，新80 cells仅passive_void。原物理坐标、支撑／实体对称／工件／端口及其权重保持；显式重绑定geometry身份，task背景顶线终点80→82。E1、nu.3、gamma1e-6、alpha1e-6、Lr80、厚度20、body中心71/40 side18、原24targets和其它physics exact。task仅geometry/background与四描述字段改变。

保存cell/node/DOF row-stride mapping：j*80+i→j*82+i、j*81+i→j*83+i，DOF按component。全部27字段逐项记录 raw delta；10项标量／参考算子raw相同，另17项对照原物理子域的重建索引／扩展向量。old material在cell_map上raw保持，新列介质系数等于gamma1e-6原介质；kr必须保持Lr80的原值。新fixed严格等于mapped old fixed＋新两顶节点uy，预计450fixed/6356free；body162/190/380与顶19overlap保持。实体、端口按映射物理集合核对，不用全数组前缀或统一offset。

制卡先核 `right_margin_validation_001/adapter_test_protocol.json`、`tests_launch.json`、`run_001/test_receipt.json`：actual5/5、2 small constructors、0F/T/equilibrium/HP、120/150/8GiB及当前adapter/CLI/test SHA绑定通过。再核 gamma1e-6 基线实际资格作来源身份；两者都不赋予新域力学资格。peer review raw文件也会绑定，实际小测试通过之前禁止freeze。

安装与通过独审／小测试后，制卡命令：

```powershell
python <外部候选>/build_right_margin_card.py --repo <Git仓库根>
```

由root检查冻结卡后显式执行 `launch_pose.py prepare --protocol <该stage>/preparation_protocol.json`。当前未执行。输出仅geometry/task/model/direction/mapping、model_comparison/source_freeze/input_inventory/preparation_receipt；不复制旧接受状态、不生成labels、不运行F/T/solver/HP或变形几何／节点力观察。后续生产／新参考／视图需独立真实结果。
