# L-PREP1 源准备说明

2026-10-14（Asia/Seoul）。当前状态：SOURCE_PREPARED_NOT_EXECUTED；两个新入口候选尚未安装，未导入或执行 HF，没有新数组读取、测试、求解、HP 或图像。执行须取得本卡直接批准。

## 目标、工作、理由与效果

整体目标是独立 HF 接收普通 LF 几何并完成 TMC 非线性前向评价，供外部研究层消费。已有转换、明确任务、从零／续算／延伸、小批量入口、保存态与真实变形显示；当前探索路径已到输入零，保留早先失败和所有来源。M-PREF1 两卸载态四 HP 实际通过原十五门，工件弱节点合力仍不等于连续压力或有效夹持力。MPM、一般 LF／HF5 资格和完整研究消费流程仍待推进。

本轮实读现有转换、任务、扩域、前向／批量源码与普通输入说明，确认应复用已有研究层和入口。实际不足是新 geometry 与显式 task 的手动接线，而不是缺少转换器或批量代码。本轮写两个薄候选、有限对账／显示 wrapper 和一次 launcher，并记录来源、静审、协议与 main 恢复资料。尚无运行效果可报告，只有源码及 AST 级证据；成功效果须待执行的三套准备包、十二实例和一张图验证。

## 排查与实现取舍

- 原 LF 网格、掩码和物理标签直接保留；扩域必须显式，以整数原列新增 passive_void，不自动细分或阈值化。
- 完整模板只改两个 geometry 身份，不推断载荷、工件、背景条件或正规化 task_id。fine 原二十五目标和工件只用于 task1.1 接线测试，不据此构模。
- 已有输出不覆盖；非法 family／pin／任务／数值宽度提前拒绝；非整数列宽度须经过原转换器的网格校验，再保留真实 partial。
- 静审发现最初宽度判定接受任意 Real，而 manifest 不能序列化其中的 Fraction 等类型。候选已收敛为有限 int／float／None 的 JSON 数值合同，提前拒绝其他类型，避免错误记录再次触发同一序列化错误；此次为执行前源码修正，尚无运行或测试证据。
- manifest 提供 case 相对位置与实际源／任务身份；返回绝对路径以便当前调用。准备状态与力学、参考、资格分开。
- 异机恢复应携带整个 case（native_geometry、可选 derived_geometry、task.json 和 input_manifest.json）。原 LF 快照在 native_geometry/sources；扩域函数继承的旧 provenance 路径不重写，LF 快照位置以本输入 manifest 为准。
- native_response 实际只核 reference 已声明的 source_bindings；新增准备模块本身不令旧参考失配，也不迁移旧参考。已变更历史源的旧参考继续保持其原来源和状态。
- 不重写 solver、native_batch、优化器或排名；不把库存数量摘要当作完整可恢复的 LF 库。

## 批准后用法

```python
from hf_eval.lf_native_inputs import prepare_native_lf_inputs
from hf_eval.native_evaluate import evaluate_native

paths = prepare_native_lf_inputs(
    "ordinary_lf/design.json", "explicit_task.json", "new_prepared_case",
    repo_root=repo, right_medium_width_mm=4.0,
)
# 前向计算属于另外明确的物理任务及资源窗口。
response = evaluate_native(
    paths["geometry_file"], paths["task_file"],
    repo_root=repo, output_directory="new_response",
)
```

```text
python hf_repo/scripts/prepare_native_lf_inputs.py --repo REPO --source-descriptor ordinary_lf/design.json --task-template explicit_task.json --output new_prepared_case --right-medium-width-mm 4
```

L-PREP1 不执行示例中的 evaluate_native。关于实际有限输入、测试、显示和资源，请以 [L-PREP1_CARD.md](L-PREP1_CARD.md) 与冻结 protocol.json 为准。旧代码／结果保持，新阶段失败不自动重试或回滚。
