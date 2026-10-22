# L-CTIPMOVE1 probe 候选实现说明

2026-10-22。文件为 `D:/hmv1_001/candidate/hf_repo/src/hf_eval/native_probe.py`；本说明阶段仅编写与静态 AST／compile，不 import HF，不运行测试、F/T 或平衡路径。正式源码尚未安装。

公开签名：

```python
evaluate_native_guided_probe(saved_result, selected_state_index,
    body_q_targets_mm, output_directory, *, time_limit_seconds=120., on_accept=None)
```

返回普通 dict，并在新输出目录写 `result.json`。来源错误以 `invalid_saved_state` 拒绝且发生在新 F/T 前；数值失败由原 controller 记录并返回真实 partial。输出不得位于原父结果目录下。

## 来源与新控制

- 只准入完整 `load_only`、成功、fixed_rigid 的末个原目标；保留原 task/geometry/model/material/boundary/settings/options。
- 复用原 `native_resume` 的普通描述符 SHA／路径读取帮助，但不调用旧 resume 或 extend_path。
- 绑定 parent/model 描述符、model archive 字节、重构项目的 source/region/grid/material、selected descriptor；仅解码一份 state NPZ 的 lift/fluctuation 两字段，逐 dtype／shape／SHA 和 state hash 检查。
- parent 力核与切线源码必须相同；旧 controller SHA 保留为来源，实际新 controller SHA 另存。
- 不读原力、切线或矩阵作为新验证。`d_hold`、原 split、原有符号 R 明确传递；原 prescribed body 节点成员保持。
- 窄合同为 nodes/d_hold/zero_dofs/background_dofs，body-x lift shape=1，其余 shape=0；调用原 controller 唯一路径。
- q0 接受时再核两 split 和 R 字节身份及首次单检查；实际 fresh F/T／禁止修正由 controller 强制。

## 观察、保存与图像来源

每个接受态只使用最后一次同态新 F/T 的缓存。新字段明确 body_q_mm、input_mean_mm、R_input_N、Q_drive_half_N；ON-body total/material/regularization 都是负节点弱力和。分组使用 `math.fsum`；body-x驱动／body-y导向／去body后的零支撑互斥，原背景重叠不重复。

在接受回调内核 prescribed ≤8e−11 mm、J>0、relative global balance≤1e−6；原自由残差与平均位移门保持。写 `accepted/NNN/state.npz`（仅两split字段）、`fields.npz`（global total/material/Hu、输入/处方反力/残差、J/Hu/F、实际坐标），每档含字段和归档 SHA。保存不新增 F/T。

result.accepted_steps 含实际坐标和各普通数值，result.model 含参考坐标、连接、solid mask、body节点、fixed/zero DOF；pure viewer 无需重新构模或读取科学缓存。result.newton_history 保留原普通控制器收敛记录。

原任务和资格保留；新结果明确不授 HP／有效夹持／释放／HF 资格。这里只实现导向位移探针，不实现自由刚体承载或力控。

## 静态语法核查

初稿 287 行，18910 bytes，SHA256 `447326844de3bb0c240ce66e0fa220da1a12638ffbf052805bd793a3c8bf5ba9`。纯标准库 `ast.parse` 和 `compile(..., 'exec')` 通过；没有执行生成的 code object，未 import 候选模块。最终冻结以 root 的候选清单为准。
