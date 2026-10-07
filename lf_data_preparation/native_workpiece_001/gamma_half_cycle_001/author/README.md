# γ 减半：生产制卡候选

本目录是外部作者提案，未安装、冻结或执行。builder只有制卡功能，不调用模型构造、F/T、solver、HP或渲染。

前提是新 `gamma_half_preparation_001` 已实际构造通过：27字段中24个原字节一致；实体`lam/mu/gamma`原字节一致、介质三项减半；源几何快照一致。builder核实际准备终态、协议与输入/源码绑定，再复制**新准备task与模型**。task包括purpose保持原字节，不重新编辑；不复制旧接受态。方向NPZ沿用原side18的原字节，端口和固定DOF不变。

新生产stage为 `lf_data_preparation/native_workpiece_001/gamma_half_cycle_001/run_001`。目标为同一24点0→1.2→0、从零开始，`port_projection`、mechanical与chunk256。settings与gates沿用，仅时间上限改为helper4500秒、outer4560秒，采样RSS8 GiB。首错停止，无重试、延期或force；采样和合作停止不是OS硬资源限制。

`execute_shift_pose.py` 原字节复用（SHA `57d18bfea972c09db4c0866bdee3413088342327e32d3926be9eaa1bdbab466a`）。同名`prepare_shift_pose.py`只提供原`INTRINSIC/OVERLAY`集合和原字节`model_delta`函数。runtime sourcefreeze是24个现有核心文件加这两个包装，共26个唯一basename；小sources副本供原worker双SHA核对，不继承70份历史脚本/caps。比较模型只用已合格projection的side18旧γ结果模型，预期变化`gamma/lam/mu`。

独立审阅与根审完成后才能运行builder；builder完成也没有启动生产。未来操作说明：

```powershell
& <HF-Python> -B <作者目录>/build_gamma_half_production.py --repo <仓库根目录>
& <HF-Python> -B <仓库根目录>/lf_data_preparation/native_workpiece_001/gamma_half_cycle_001/launch_pose.py production --protocol <仓库根目录>/lf_data_preparation/native_workpiece_001/gamma_half_cycle_001/production_protocol.json
```

完整新生产通过后才按实际N设计新2N参考；失败仅保留部分结果，没有whole-path资格。旧HP计数、接受态或测试资格不转移。参考、保存视图及右侧介质余量均不在本生产卡内。
