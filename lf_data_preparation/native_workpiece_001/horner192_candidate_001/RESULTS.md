# Horner192 001：测试启动失败，执行卡已关闭

本阶段没有进入候选完整力入口。唯一测试启动以 `exit_code=1` 结束；测试收集数和实际启动数均为0。失败来自测试包装的 pytest hook 参数，不能据此判断候选力、切线或数值门是否通过。


## 为什么做这一步

整个项目仍要完成可独立读取普通几何与任务、计算非线性力与切线、求解加载和卸载、测量工件反力并可视化的 HF 评估器。本次候选针对粗方形工件循环003保存的真实 F16 范围失败输入，先用原有20例、3例 matmul 检查和2例未选分支逐字节回归检查验证代码，再计划执行全3200单元的力、缓存切线和独立参考。此阶段不改模型、网格、材料、工件、端口或旧门。

## 实际结果

| 保存字段 | 实际值 |
| --- | --- |
| `unit_tests_result.status` / `invocations` | `failed` / 1 |
| `collected_tests` / `started_tests` | 0 / 0 |
| `passed_tests` / `failed_tests` / `skipped_tests` | 0 / 0 / 0 |
| `unit_tests_launch.status` / `exit_code` | `not_pass` / 1 |
| 包装记录 `elapsed_seconds` | 0.26469290000386536 s |
| 外层记录 `elapsed_seconds` | 0.5263281000079587 s |
| 包装采样峰值 / 外层进程树采样峰值 | 35450880 / 41701376 B |
| protocol bindings | 234项，前后相同 |

`PluginValidationError` 指向 `pytest_runtest_logreport(result)`：参数 `result` 不属于该 hookspec，所需参数名为 `report`。错误发生在测试插件注册期间，测试主体没有启动。原回执内通用的 `numerical_call_counts` 文案是预定测试套件的范围说明，不应把它解释成已经发生的力学调用，也不能用测试主体未启动的事实覆盖回执原文。

候选、reference及完整模型HP阶段均未启动；也没有新增真实物理路径。按首错停止规则，此卡保持失败并关闭，没有在原目录修复、重试或把后续新卡结果追记为001通过。

## 可复核证据

- [unit_tests_result.json](unit_tests_result.json)，SHA256 `70ea999e93184258fa7187b97c976ae5a8827a6e5db1564a726987ca8869d663`。
- [unit_tests_launch.json](unit_tests_launch.json)，SHA256 `25962f91e49ab80a3917bcd82e6c7eb92ff56ac9c77d9265ef9d54fd472b7b59`。
- [protocol.json](protocol.json)，SHA256 `1bf2db62aa8c88a47dd4b67265b2c0041c6bf430d5685c853be10cd016745b13`。
- [只读实际审阅](actual_saved_review.json)，SHA256 `457d5e887ab4eebf8cc941d2aca2b22b7bae43d36626c524f243daa07212a0f4`。其 `saved_identity_review_pass` 只表示保存身份核查一致，`qualification=false`。

测试合同为包装60 s、外层90 s、采样进程树8 GiB；它是协同检查与采样合同，不能声称操作系统硬性限额或强制清理资格。计划中的候选90/120 s和reference180/210 s窗口没有被使用。

production 内核仍为 `7fff354270a276764445b45a281a5924fd9f0356236b89e0dbd4f00088b383ce`；隔离 Horner192 候选为 `1d18a5512396649200de908cc5106c17d7c9a9f7c3fa62ba518cbe7d5659517e`，未合入。下一新卡只修测试包装接口并复用封存数学来源，不复活001。
