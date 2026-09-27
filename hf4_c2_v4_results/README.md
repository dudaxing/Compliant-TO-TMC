# HF4-C2 v4 补测记录

v4（补偿内核）对原失败细网格路径 `mesh_h00625` 的冻结、启动检查、一次求解、一次独立审计及其存储。结论与范围见 [v4 补测报告](../docs/HF4_C2_V4_RETEST_REPORT.md)；实现与冻结见 [v4 冻结报告](../docs/HF4_C2_V4_FREEZE_REPORT.md)。

| 位置 | 内容 |
| --- | --- |
| `prelaunch/` | 冻结候审时的只读启动检查（10/10）与全量测试（1467 passed） |
| `experiments/` | 守卫管理的实验根：`mesh_h00625_v4` 运行目录，以及求解、审计各自的日志、回执与启动计划。只放守卫产生的文件，否则守卫会拒绝启动 |
| `storage/` | 外置大载荷的清单（相对路径、字节、SHA-256、绑定记录、归档位置、恢复方法）与空目录还原核对 |
| `comparison_001/` | 与 v3 历史的逐态对照、误差图、输出哈希（`compare_v4_with_v3.py` 生成，只读） |
| `postrun/` | 运行后守卫检查：再求解、再审计、换名求解都被拒绝（`postrun_guard_check.py` 生成，只读） |
| `external_payloads.py`、`test_external_payloads.py` | 外置归档的打包与还原工具及其合成数据测试 |

运行目录中的逐态 NPZ、逐态与完整控制器记录、逐态审计详情（64 个文件，235.3 MB）不在 Git 中，由 `.gitignore` 逐文件列出。还原：

```text
python hf4_c2_v4_results/external_payloads.py restore --manifest hf4_c2_v4_results/storage/mesh_h00625_v4.external_payloads.json --archive <hf4-c2-v4-mesh_h00625_v4-payloads-v1.zip 的路径> --into .
```

归档目前只在所有者本机的 `Compliant-TO-TMC-evidence/hf4-c2-v4-v1/`；是否作为 Release 附件公开由所有者决定。
