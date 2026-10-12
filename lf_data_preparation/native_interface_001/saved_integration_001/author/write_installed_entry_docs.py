"""Ordinary documentation prefix update; no example or scientific code is run."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
BASE = '2b550d09f4347240ef6cb626b4c829566b638e61'
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
sha = lambda raw: sha256(raw).hexdigest()
read = lambda name: json.loads((ROOT / name).read_bytes())
git = lambda *args: subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)
assert git('rev-parse', 'HEAD').decode().strip() == BASE
outer = read(REL + '/integration_launch.json')
helper = read(REL + '/run_001/execution_receipt.json')
tests = read(REL + '/run_001/focused_test_receipt.json')
assert outer['status'] == 'pass' and outer['exit_code'] == 0 and helper['status'] == 'pass'
assert helper['installation_complete'] is True and len(helper['installed']) == 11
assert tests['status'] == 'pass' and tests['passed_calls'] == len(tests['collected_selectors']) == 25
assert '25 passed in 6.62s' in (ROOT / REL / 'run_001/focused_tests_stdout.log').read_text(encoding='utf-8')
receipt_file = ROOT / REL / 'author/installed_entry_documentation_receipt.json'
assert not receipt_file.exists()

readme = '''# 默认保存态续算已安装：Mean／API／CLI

M-INTEGRATE1 唯一执行成功：11 份候选已安装到默认 `hf_repo`，25 个精确 pytest 实例通过（pytest stdout：6.62 秒）。范围包含旧零起点、保存态合同、缓存保存、mechanical/chunk256、mock batch、CLI 接线、非法 settings 与旧参考来源迁移；真实力学测试仅临时 16 单元／50 DOF。该结果验证入口集成与有限兼容，没有重跑原夹持器或生成新 HP、变形图、压力／有效夹持／稳定性资格。

保存态入口使用原任务内的非零接受目标，重新验证锚点后执行原绝对目标后缀。`selected_state_index` 是接受记录行序号；所选行须为原目标，并至少还有一个后续目标。父任务必须是原零 lift 的 `ordered_cycle`，原几何、材料、边界、数值设置和选项保持，只使用本次新的求解时限。省略 saved 模式选项会继承父值；普通零起点仍为 complete/full/tangent。锚点从新鲜 `K=None` 开始计算 F/T，不读取旧力、切线或矩阵。

未来 CLI 用法示意（本页不执行，示例不构成新增运行许可；`<repo>` 与 `<HF Python>` 替换为本机路径，并选择全新输出目录）：

```text
<HF Python> <repo>/hf_repo/scripts/evaluate_native.py --repo <repo> --saved-result lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json --selected-state-index 13 --targets 1.20 1.15 --output jobs/new_resume_demo --time-limit 180
```

子结果成功只表示后缀完成，原 M-ALPHA1 failed/time_limit 与原完整路径未完成标记不改；不承诺递归续算子结果或 batch 保存态入口。当前源码重总结旧 right2/right4 正参考会严格 source mismatch，旧 result/reference/qualified 响应和 HP 历史字节保持。功能集成不放宽来源或物理资格门。

[完整用法与字段](../docs/NATIVE_EVALUATION_INTERFACE.md) · [本轮执行回执](../lf_data_preparation/native_interface_001/saved_integration_001/run_001/execution_receipt.json) · [25 项实际测试回执](../lf_data_preparation/native_interface_001/saved_integration_001/run_001/focused_test_receipt.json) · [原两端点实际变形与作用](../lf_data_preparation/native_interface_001/saved_continuation_001/RESULTS.md)。整体目标仍是独立 HF 有限变形／TMC 正向评价；任意新 LF 几何／任务的可靠性、连续接触压力、有效夹持、稳定性及 HF5 整体资格继续按证据推进。
'''
interface = '''# 默认保存态续算接口：已安装与有限回归通过

M-INTEGRATE1 已一次安装 11 份文件并通过 25 个精确测试实例（pytest stdout：6.62 秒）。19 项既有实例与 6 项新增实例覆盖零起点 Mean／缓存、mechanical/chunk256、split、mock batch、API／保存 JSON、CLI 传参、dict/object 非法 settings 及旧正参考源码迁移。真实计算仅临时 16 单元／50 DOF；未重做原夹持器路径、HP 或绘图。[实际执行回执](../lf_data_preparation/native_interface_001/saved_integration_001/run_001/execution_receipt.json)与[测试回执](../lf_data_preparation/native_interface_001/saved_integration_001/run_001/focused_test_receipt.json)记录实际状态与有限范围。

## 用法与范围

默认单例 API 为 `hf_eval.native_evaluate.evaluate_native`；直接求解入口为 `hf_eval.native_mean.solve_native_mean`。二者增加配对的 `saved_result` 与 `selected_state_index`。在 saved 模式中，geometry/task 为 `None` 时读取父保存的原几何和嵌入任务，选项为 `None` 时继承父实际值。零起点省略选项仍解析为 complete/full/tangent，原 batch 零起点接口保持。

所选父结果必须保留原完整目标表，来自原零 lift、零 `target_origin` 的 `ordered_cycle` 任务。`selected_state_index` 指接受记录的行序号；该记录必须对应原任务内部的非零原目标，且至少还有一个目标。它不是 Newton trial 序号，也不保证等于原目标序号；二分接受态不能随意当原目标。几何、任务、材料、边界、力／切线源身份必须匹配，不可跨任务或只凭形状相似续算。

请求目标是原目标表从锚点开始的**完整绝对后缀**。例如本项目父行 13 对应 1.20 mm，唯一原剩余后缀为 `[1.20, 1.15]`；不是 `[0, -0.05]`，不能省略中间目标或改任务。省略 `targets` 会继承该后缀。父 numerical settings 和 response/tangent/guess 选项原样保留，只有本次新 `time_limit_seconds` 可改变；不得覆盖 minimum_increment 或切换模式。该父实际选项为 mechanical/chunk256/port_projection，saved 调用不用再次填写它们。

以下 Python 示例只展示未来用法，不在本次文档更新中执行，也不构成新增计算许可。`repo` 和全新输出目录由实际使用者指定：

```python
from pathlib import Path
from hf_eval.native_evaluate import evaluate_native

repo = Path("<本机仓库根>")
response = evaluate_native(
    None, None, "jobs/new_resume_demo", repo_root=repo,
    saved_result=("lf_data_preparation/native_interface_001/"
                  "regularization_sensitivity_001/run_001/alpha_half/result.json"),
    selected_state_index=13, targets=[1.20, 1.15],
    time_limit_seconds=180.0,
)
```

`evaluate_native` 相对路径按 `repo_root`（省略时为 cwd）解析，返回并保存紧凑 response，已有输出不覆盖。传入 `settings` 时必须为 `DisplacementSettings`；不要同时传非默认独立控制限。dict/object 在输入阶段返回 `status="error"`、`code="invalid_settings"`、`exception_class="TMCError"`，不先进入父读取／构模／求解。直接 `solve_native_mean(None, None, None, saved_result=parent, selected_state_index=i, time_limit_seconds=new_limit)` 可继承原后缀与设置；如果显式传 settings，只允许与父设置相差本次时限，并且不再同时传 time_limit_seconds。

对应 CLI 示意，同样仅为未来用法；所有输出目录必须全新：

```text
<HF Python> <repo>/hf_repo/scripts/evaluate_native.py --repo <repo> --saved-result lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json --selected-state-index 13 --targets 1.20 1.15 --output jobs/new_resume_demo --time-limit 180
<HF Python> <repo>/hf_repo/scripts/solve_native_mean.py --saved-result <repo>/lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json --selected-state-index 13 --output <repo>/jobs/new_mean_resume_demo --time-limit 180
```

evaluate CLI 有 `--repo`；Mean CLI 使用自身传入路径／cwd，没有 `--repo` 参数。两 CLI 的 saved flags 必须配对，未指定 targets 时继承完整后缀；saved 模式不允许 `--minimum-increment`。API 的 time_limit 是控制器时钟，整体资源需独立外层窗口；Mean CLI 还检查启动至保存后的自身 wall time。API/CLI 默认 180 秒是新调用时限，不能继承已关闭执行卡额度，也不保证任务能在示意时限内完成。

## 续算结果的含义

恢复保持原 lift/fluctuation 和有符号输入反力 R，初始 `K=None`；新鲜 F/T 必须先满足原残差／平均约束门。若锚点不满足，`initial_state_not_equilibrated` 在纠正或提交前停止，不使用旧 CSC、切线、力或显示位移代替原状态。通过后使用原控制器 predictor/Newton/Armijo/二分，接受缓存保存不新增 F/T。

| 字段／记录 | 当前含义 |
|---|---|
| child 局部序号、original_target_index | 分别定位子后缀和原任务；本例锚点／下降为原 13／14，不借加载中同值目标 |
| continuation.parent_* | 保留父结果身份、状态、failure、完整路径／任务目标／卸载标记 |
| continuation.segment_completed | 只表示本次请求后缀完成；失败保留实际接受前缀 |
| anchor_revalidated / anchor_identity_preserved | 新 F/T 门与所选原 split/R 身份核对；锚点不是新的未变形 origin |
| full_original_path_executed_by_child / full_original_path_completed | false；子后缀不能宣称执行或完成整个原任务 |
| task_target_executed / target_response | 续算不借锚点把整个原任务判成功；任务目标响应仍受原明确语义限制 |

原 M-ALPHA1 failed/time_limit、未完成完整路径／卸载的事实保持；M-RESUME1 两端点成功不拼成完整卸载曲线。本入口不承诺递归读取续算 child，或把 saved flags 扩展到 batch；原 batch 接口仍是零起点。callback 或接受后的异常可留下真实已接受状态，只能对未接受尝试解释原 rollback，不能笼统称所有失败都恢复至父锚点。

## 旧参考与物理资格

安装后的当前源码重新总结旧 right2/right4 正参考时，native_mean/split_displacement 原 pins 不同会按原门返回独立参考 source mismatch；生产成功保持，accepted/full reference pass 为 false，原 reported pass／48 HP 和已保存 qualified 响应保持历史原字节。这是来源身份差异，不是旧 HP 数值失败，也不修改旧 pins。其他参考须按自身实际源交集核定，不笼统否定全部历史 HP。

工件 signed total/material/regularization、holding、镜像 net 与两侧幅值仍沿原语义；弱式合力不认定为连续压力或有效夹持力。新默认入口兼容不授予压力、接触、夹持、稳定性、全切线列或 HF5 资格，也不替代任意新 LF 几何／任务验证。[原保存态实际效果](../lf_data_preparation/native_interface_001/saved_continuation_001/RESULTS.md)与[当前进度](CURRENT_STATUS.md)用于判断下一步。
'''
prefixes = {'hf_repo/README.md': readme, 'docs/NATIVE_EVALUATION_INTERFACE.md': interface}
rows = []
for name, text in prefixes.items():
    path = ROOT / name
    old = git('show', BASE + ':' + name)
    assert path.read_bytes() == old
    opening = '\n<details>\n<summary>更新前完整原文：历史状态与命令仅对应当时</summary>\n\n'
    prefix = (text.rstrip() + '\n' + opening).replace('\n', '\r\n').encode('utf-8')
    suffix = b'\r\n</details>\r\n'
    new = prefix + old + suffix
    assert new.count(old) == 1 and new[len(prefix):len(prefix)+len(old)] == old
    for target in re.findall(r'!?\[[^\]]*\]\(([^\n)]+)\)', text):
        assert (path.parent / target).resolve().exists(), (name, target)
    path.write_bytes(new)
    rows.append(dict(path=name, old_bytes=len(old), old_sha256=sha(old), new_sha256=sha(new),
        history_start_byte=len(prefix), history_end_byte_exclusive=len(prefix)+len(old),
        old_body_preserved_exactly=True, original_raw_occurrences=1, example_execution=False))
receipt = dict(status='pass_installed_default_entry_documentation_update_ordinary_only',
    created_utc=datetime.now(timezone.utc).isoformat(), source_commit=BASE,
    card='M-INTEGRATE1', installation_status=helper['status'], installation_files=11,
    test_status=tests['status'], actual_passed_test_instances=25,
    test_stdout_reported_seconds='6.62',
    records=dict(outer=dict(path=REL+'/integration_launch.json',sha256=sha((ROOT/REL/'integration_launch.json').read_bytes())),
                 helper=dict(path=REL+'/run_001/execution_receipt.json',sha256=sha((ROOT/REL/'run_001/execution_receipt.json').read_bytes())),
                 tests=dict(path=REL+'/run_001/focused_test_receipt.json',sha256=sha((ROOT/REL/'run_001/focused_test_receipt.json').read_bytes()))),
    front_history=rows, documentation_files_updated=2, scientific_actions_during_documentation=dict(
        HF_import=0, CLI=0, tests=0, NPZ_decode=0, model=0, F=0, T=0, solver=0, observer=0, HP=0, render=0),
    examples_are_future_usage_not_execution_authorization=True,
    parent_NOT_PASS_and_qualification_unchanged=True, new_physical_qualification=False)
with receipt_file.open('x', encoding='utf-8', newline='\n') as output:
    output.write(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
review = dict(status=receipt['status'], receipt_sha256=sha(receipt_file.read_bytes()), front_history=rows,
    only_formal_writes=[*prefixes, REL+'/author/installed_entry_documentation_receipt.json'])
(HERE/'installed_entry_documentation_review.json').write_text(json.dumps(review, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(review, ensure_ascii=False))
