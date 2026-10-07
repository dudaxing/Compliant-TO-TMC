# 独立批量参考 V2：仅源候选，未制卡执行

V1 canonical 参考已关闭 NOT_PASS：新增节点数检查使用不存在的 `model['coords']`，真实持久化字段是 `coordinates`。失败时独立接受态和 HP 均为 0；fine 参考与视图未执行。旧源、协议、输出及失败资格保持原样。字段诊断见本目录 `load_diagnosis.json/md`。

V2 仅修正该字段名，并将参考控制移至新的 `lf_data_preparation/native_interface_001/batch_reference_v2_001`。`PRODUCTION_STAGE` 固定为原完整生产 `batch_forward_001`；原生产不重跑。新 contract/protocol/execution schema 为 2.0，新输出为 V2 stage 的 `run_001/audit/<label>`。旧失败协议、contract、launch、receipt、lifecycle 仅绑定作关闭上下文，不提供资格或承接旧卡。

直接继承原 `audit_native_mean.Audit.run/run_state`、GATES、HP80/120、Decimal scatter 和端口方向数学；不复制或修改数学。每例全部实际 N 状态均需全新 2N HP。原 `summary.json` 字节保留，`qualified_summary.json` 只复制后纠正设计别名/0.025 mm 当前任务范围并记录原摘要 SHA。无空间采样，且不授全部切线列、能量、压力、接触、HF5、排名或网格收敛资格。

V2 loader 保持真实两个生产结果、28 当前 HF 源、5 原数学源、2 新包装的身份与原数值门。生产 baseline 仍为原 `aa072bc...`，不要求当前 Git HEAD 仍等于该提交。两例均为实际 N4，未来每例需新 8HP；原成本可用于新预算依据，旧资源窗口不能继续使用。当前没有 V2 执行授权，也没有预写未来参考 PASS。

root 在新的卡范围确定、最终 source reviews 通过后，才可在独立 HF 环境调用 builder：

```text
python reference_case_builder.py --repo <absolute-clone> --case <canonical-or-native_fine> --time-limit <new-explicit-helper> --outer-seconds <new-explicit-outer> --budget-basis <actual-N-and-cost-basis> --root-review <review.json> --peer-review <review.json>
```

builder 首次建立新的 reference_author，第二例只核对同源。它把原 raw `launch_pose.py` 复制到新 stage 同一深度，ROOT 仍为 parents[3]；root 用 phase `reference_<label>` 和新协议启动。停止文件是新 stage 根 `stop_requested.txt`，不移入 author 或原生产 stage。输出与当前输出索引均不进入旧生产 case。

作者只读取源码/保存 JSON、计算文件 SHA、AST parse/compile，不导入候选或 HF，不读取数组，不构模、F/T、求解、HP、绘图、制卡或修改正式仓库。保存 JSON 的字段/shape 声明检查不替代未来原数组与数值验收门。
