# HF-3 验收记录（0.3.0）

2026-09-14。指定 HF3 数值验收通过：311 自动测试通过、1 Windows 实际符号链接权限项跳过；原小参考 976 项及强压缩 192 项通过；两例三幅值 39 项桥接通过；两条 40 目标平均位移路径完成，6+80 个状态独立高精度验收通过，8 态 50/80 位交叉核验通过；独立安装 39 项通过。

这说明指定离散模型的项目映射、求解、数值精度与独立重放得到验证。几何研究资格 pending，功能性未评估；无工件的夹持器自由运动不验证接触或夹持力。旧 HF2 全路径仍绑定旧版本，0.3.0 未另行重跑完整 C-shape。

完整叙述、修正原因、失败记录、物理参数、图和资源见[阶段报告](../../docs/HF3_REPORT.md)。当前生产源聚合哈希 `9104789cb567681bbbe17b9f145e127be17cfa6113b045972aace0ccf1c99a01`，wheel 哈希 `e5ed49e671176aad0fbf607718aebc1e6c501732ced392d8f8bb2a4bca3c9c1f`。

本仓库的紧凑证据快照在 [validation/hf3/records](../validation/hf3/records)。完整发布包另含 `hf3_results` 逐态模型/位移/反力/J/材料能量/Decimal参考与原始日志，可搬迁的395文件几何包，以及未经改写的上一版HF2修正发布包。

## 运行普通文件接口

从本仓库目录运行（result目录须不存在）：

```powershell
.venv\Scripts\python -m hf_eval evaluate ../geometry_dataset/canonical/inverter/geometry.json --task configs/hf3/inverter_pilot_v1.json --solver configs/hf3/full_path_solver_v1.json --output new-inverter-result
```

夹持器使用对应几何及 `gripper_pilot_v1.json`，solver相同。solver JSON从本轮实际调用逐项导出，不回改计算前冻结的 validation_spec。Python接口仍为 `hf_eval.evaluate(geometry, task_config, solver_config, output_directory)`；在调用JAX前显式设置CPU/x64。CLI负责这项配置。

验收证据不会因一次新运行成功而自动继承；新输入、物理配置或源码需要相应重新验收。完整80态HP分批的初始 incomplete 快照和全部失败日志保留。
