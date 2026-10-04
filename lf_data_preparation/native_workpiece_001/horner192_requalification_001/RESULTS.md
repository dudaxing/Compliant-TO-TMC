# Horner192 002：25例测试通过，真实 F16 完整力入口失败

新测试包装实际完成25/25例；随后唯一候选完整力调用在原 F16 状态上再次返回 `unsupported_arithmetic_range`。力调用启动1次、完成0次，因此切线、action consumer及HP参考均未启动。此卡已失败关闭，测试通过没有授予 F16 或循环求解资格。


## 本次改变与输入

新卡只修测试 callback接口和包装位置引用。数学候选、测试用例及验证器复用001封存版本；隔离42文件 runtime 不代表 production 内核升级。真实输入仍来自 `coarse_square_cycle_003/first_force_range_input`：3200单元、6642 DOF、376固定DOF，原27字段模型不变。

| 身份 | SHA256 |
| --- | --- |
| 原 F16 16字段 `input.npz` | `47824b835a70f6eef7ab1d3712d92958040877c4451a3b06902ddb997082248e` |
| 原 split state | `9dbd3c951d322e14fde9734838108af6f4237816f1e9054ad40ada8aafa764e2` |
| 原27字段模型 | `a2d6e141fecb5f34efa66455c19ee67f47f476e019f760feb685f1a091266049` |
| 隔离候选内核 | `1d18a5512396649200de908cc5106c17d7c9a9f7c3fa62ba518cbe7d5659517e` |

旧端口方向保存为历史对照；实际验证方向为固定DOF清零的全自由域 dyadic witness。其3072个非零单元方向包含原诊断失败位置。模型的 `E*t=20`，原力标度规则给出当前状态 floor `2e-13 N`；没有搬用另一物理模型的 `2e-14 N` 字面量或改变门。

## 实际执行

| 阶段 | 状态与次数 | 内部时间 | 外层时间 | 保存采样峰值 |
| --- | --- | --- | --- | --- |
| unit tests | pass，25收集/25启动/25通过，1次启动 | 6.159413199988194 s | 7.8258611999917775 s | 包装159514624 B；外层树158224384 B |
| candidate | fail，exit1，1次启动 | 6.211225799983367 s | 7.168411599996034 s | helper64114688 B；外层树230629376 B |
| reference | 未启动 | 未使用 | 未使用 | 无 |

pytest stdout 自身显示 `25 passed in 5.49s`。这个时间、包装时间和外层时间覆盖的范围不同，分别保留，不采用先前口头估计的7.56 s代替正式回执。

候选实际计数为 `force_started=1, force_completed=0`，`tangent_started/completed=0/0`、`action_consumer_started/completed=0/0`、`HP_started/completed=0/0`、`solver_calls=0`、`JIT_calls=0`。错误类型为 `KernelError`，code为 `unsupported_arithmetic_range`，message为 `NumPy response exceeded the declared compensated arithmetic support range`。只留下20字段fixture和43份来源capsule，没有完整force_fields、即时切线档案或CSC；不得由已声明的计划推断这些阶段已执行。

246项protocol绑定、原输入、原模型和42文件runtime均保持前后相同。独立保存核查读取295个文件，确认上述失败部分包一致，没有补算任何力、切线、consumer、HP或求解。

## 结论与下一步

Horner循环的共用尺度候选没有让原 F16 的完整返回合同通过。测试结果支持已运行的25例范围；它没有替代全域 F16、切线或HP参考验证。原001启动失败与本002完整力失败均永久保留，不修复原卡、不在原目录重跑；随后另开独立观察卡定位首次范围拒绝。

资源合同为测试60/90 s、候选90/120 s、reference180/210 s，每阶段采样进程树8 GiB，计时含各自声明的导入、调用、保存和身份检查。协同检查与采样不代表OS硬限，也没有强制终止或通用进程树清理资格。reference因候选失败未启动。

production内核仍为 `7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce`；候选 `1d18...9517e` 未合入。下一目标仍是让原 F16 的完整机械力/切线入口在新显式合同下返回，再用fresh80/120独立参考按原门验证。

## 可复核证据

- [unit_tests_result.json](unit_tests_result.json)，SHA256 `dea8650a5d9cff8d06e65fa39eca78bac1ad09005dab66416998817dd382033d`。
- [unit_tests_launch.json](unit_tests_launch.json)，SHA256 `2cb4ef90623e440df342f6707cdffd170ed2ab9674906ac30db1e38f13b482e3`。
- [check/candidate/result.json](check/candidate/result.json)，SHA256 `658cff6edc8efb7334dcb74a20bc7c868eb5a516a36333b81cb53f8211e41ed7`。
- [candidate_launch.json](candidate_launch.json)，SHA256 `20cd13bd33baa0ecfbe8963868a31cb64f107258321225f2c4f5a8551a9fb4f2`。
- [protocol.json](protocol.json)，SHA256 `834b67ec36f4c0c2f4fa0d9c4fc2fc0c84e1f6aa6ac581b1188206559d651e90`。
- [只读实际审阅](actual_saved_review.json)，SHA256 `9517c5fd7c3b26aeab9165470058cce4af2d582d24528665d4a14837f6f5dafd`；保存身份核查pass，数值候选仍fail且无资格。
