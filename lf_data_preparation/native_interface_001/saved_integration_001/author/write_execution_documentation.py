"""Record closed actual integration; examples and old visuals are not executed."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = '2b550d09f4347240ef6cb626b4c829566b638e61'
REL = 'lf_data_preparation/native_interface_001/saved_integration_001'
STAGE = ROOT / REL
read = lambda path: json.loads(path.read_bytes())


def sha(path):
    value = sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def new_bytes(path, raw):
    with path.open('xb') as output:
        output.write(raw)


def new_json(path, value):
    new_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    protocol = read(STAGE / 'protocol.json')
    outer, helper, tests = (read(STAGE / name) for name in ('integration_launch.json', 'run_001/execution_receipt.json', 'run_001/focused_test_receipt.json'))
    assert outer['status'] == helper['status'] == tests['status'] == 'pass'
    assert outer['invocations'] == 1 and outer['exit_code'] == 0 and outer['stop_reason'] is None
    assert helper['installation_complete'] and tests['passed_calls'] == 25
    assert tests['collected_selectors'] == protocol['focused_test_selectors']
    assert all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
    assert all(sha(ROOT / name) == pin for name, pin in protocol['installed_runtime_SHA256'].items())
    for name in ('execution_terminal_review.json', 'EXECUTION_TERMINAL_REVIEW.md',
                 'focused_execution_review.json', 'FOCUSED_EXECUTION_REVIEW.md', 'TERMINAL_REVIEW_PLAN.md'):
        new_bytes(STAGE / 'author' / name, (HERE / name).read_bytes())
    for path in HERE.glob('*.py'):
        new_bytes(STAGE / 'author' / path.name, path.read_bytes())
    result = '''# M-INTEGRATE1 实际结果：默认保存态续算集成通过

2026-10-12（Asia/Seoul），直接批准后唯一启动已终端exit0／PASS；默认hf_repo已经安装11份绑定文件。25个冻结参数实例实际收集并全部通过，75个setup/call/teardown全部passed，XML 25项／0失败／0错误／0跳过，stdout为 `25 passed in 6.62s`。没有重试、修复重跑、延期、force或自动回滚；窗口已关闭。

## 目标、改变与效果

整体仍为独立HF有限变形／TMC前向评价，读取普通LF几何、在明确任务下提供实际变形、反力和可解释工件作用给外部研究层。HF不做优化、不调用dmftd，MPM暂不实现；main、既定origin和science0.5.0保持。

前一步M-RESUME1已实际验证原alpha5e−7保存峰值013复核与首次1.20→1.15 mm下降。此前候选只能在隔离包运行；本步把同一Mean/controller/reader/response续算合同安装到默认库与两个CLI，调用方可从原保存接受态继续同任务后缀。有效输入力核／NumPy切线／组装原字节保持。另加入settings类型检查，使非法dict/object在读取父数据和力学前保存typed invalid_settings；两个CLI帮助文字已修正。核心实现未因测试扩展加入新的物理算法。

安装共7份生产源码＋4份测试：6旧文件修改、5新文件，均与protocol候选逐字节一致；6原源码快照与Git2b550d0保存原值。运行身份58份（52 HF模块、2CLI、4测试）一致，26个实际HF导入均来自默认hf_repo/src，108不可变bindings保持。原prepare card/protocol的authorized/executed=false是历史准备字段，实际批准在author/authorization.json，执行在integration_launch和run_001记录，不能用旧准备字段否认本次执行。

## 有限验证与实际资源

| 范围 | 实际结果 | 含义 |
| --- | --- | --- |
| 4个真实小模型实例 | 7条建模记录，均16单元／50DOF；F33/33、T22/22 | NativeMean NumPy aliases计数，保存态测试含输入身份负分支构建；不是全部内核调用总数 |
| 6个controller实例 | 单单元8DOF合成代数响应，断言通过 | 均值／R、零起点warm、锚点复核失败及回滚合同 |
| 15个mock／普通记录实例 | API、CLI、错误、旧响应／视图链接和来源迁移通过 | 不把mock次数当真实力学；旧JSON测试拒绝旧NPZ |
| XML／plugin／pytest child | 6.601／6.705872099992121／8.018545099999756秒 | 三种计时范围分开；plugin采样155664384B |
| helper／outer | 8.505939700000454／9.125265299982857秒 | helper自身采样24649728B、outer进程树184213504B；exit0、stopNone |

本卡180／300／360秒和采样8GiB门满足，RSS是采样而非OS硬上限。原零起点complete/full/tangent、mechanical/chunk256、缓存保存、保存态选项和设置继承、新时钟、CLI接线及typed错误所选断言通过。HP/JIT/原夹持器路径／新观察绘图未执行，零额外调用依据冻结源闭包、测试guards与小模型记录；不是全库机械钩子监测声明。

## 旧来源与资格

right4来源迁移用例实际passed：生产摘要仍success／原24态，当前reader按原门对旧参考strict mismatch，原result/reference/qualified response原字节保持。right2的同两条mean/split来源失配是本次只读源核对，没有额外总结API实测；M-REF2实际12参考源没有交集且仍匹配。这不等于旧48HP数值失败，也不能更新旧pins来制造matched。

旧M-RESUME1的100个bindings路径与本次11target交集为0，旧候选并未被默认安装覆盖。终审核98非NPZ字节，另外2NPZ只保留原声明pin，未新读取／复审数组。本卡108普通绑定保持与旧100全数组重新审计不同。

原M-ALPHA1仍failed/time_limit、14加载态，full path/task flags false；M-RESUME1新段success和父NOT_PASS分开。默认集成通过不拼接为一次原完整路径通过，不转移参考，不增加连续总压力、有效夹持、稳定性、全部切线列或HF5资格。

## 可人工检查的既有实际效果

本步不产生新物理图。下面复用前一步实际峰值／首次下降的2帧GIF；原数组、数值和图件没有改变。

![原M-RESUME1峰值与首次下降实际变形和工件力](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

| 原保存实际状态 | 输入R (N) | q_out (mm) | 下半工件total Fy (N) | 有限tip-bottom距离 (mm) |
| --- | ---: | ---: | ---: | ---: |
| loading 1.20 | 0.37865427196005513 | 1.016934534302024 | 0.12492121630032427 | 0.0009696602064828141 |
| unloading 1.15 | 0.3470376815403639 | 1.0153174242325562 | 0.10671287553103108 | 0.0012850478242718566 |

两个端点不是连续卸载曲线；弱式工件合力和几何距离不是压力或合格夹持力。三PNG见[结构／力](../saved_continuation_001/run_001/view/comparison.png)、[距离／signed Fx](../saved_continuation_001/run_001/view/distances_forces.png)、[峰值场](../saved_continuation_001/run_001/view/peak_fields.png)。原像素人工核查覆盖三PNG，未声称人工逐帧检查GIF。本轮没有重新渲染。

[默认入口用法](../../../docs/NATIVE_EVALUATION_INTERFACE.md) · [实际测试stdout](run_001/focused_tests_stdout.log) · [执行回执](run_001/execution_receipt.json) · [独立终审](author/EXECUTION_TERMINAL_REVIEW.md) · [有限测试审阅](author/FOCUSED_EXECUTION_REVIEW.md) · [下一步取舍](NEXT_STEP_REVIEW.md)
'''
    new_bytes(STAGE / 'RESULTS.md', result.encode('utf-8'))
    next_step = '''# 集成通过后的最近取舍：核查新alpha保存态的独立参考复用

默认保存态Mean/API/CLI已实际安装并通过25有限兼容；原同任务峰值复核／首次下降已有实际生产和图件，没必要为接口再重复13440单元长加载。M-INTEGRATE1窗口关闭，不追加测试、HP、求解或图。

最近优先只读核查现有独立参考入口能否复用原alpha5e−7的1.20峰值与1.15首次下降两态，核对实际保存结构、原门和原HP成本，再据此准备唯一具体卡。新alpha尚无HP，旧alpha的48HP不能移用；新的参考阶段即使通过也只支持其实际态和力范围，不能代替压力／有效夹持判据、全部切线列或稳定性。

这项选择把注意力转回实际作用力的可核验性。后续粗路线是明确父子保存态关联和观察路径、接触作用解释／夹持定义，再按同任务推进一般LF输入与外部研究层比较；不把两段拼成原一次求解PASS、不静默改变物理任务或门。若独立参考源码／输入不兼容，先记录具体问题并做最小修订，不能重开已闭卡或用剩余时间计算。

本文件只记录下一步取舍，不是新HP、求解、资源或范围的授权。本轮尚未形成或执行下一张计算卡，也未标记项目完成。
'''
    new_bytes(STAGE / 'NEXT_STEP_REVIEW.md', next_step.encode('utf-8'))
    prefix = '''# 当前接续：M-INTEGRATE1实际PASS，默认保存态续算已安装

整体目标仍为独立HF有限变形／TMC前向评价，读取普通LF几何，在明确任务下提供实际变形、反力和可解释工件作用给外部研究层；HF不优化、不调用dmftd，MPM暂不实现，main与既定origin、science0.5.0保持。

2026-10-12（Asia/Seoul）直接批准后唯一安装11份（6旧改、5新）并执行25冻结测试，实际25passed／75阶段报告全passed／XML0失败错误跳过；outer9.125265299982857秒、exit0、tree采样184213504B、stopNone。默认Mean/API/CLI支持同原任务保存内部非零原目标接受态的绝对后缀续算；new clock外设置／选项保持，K=None必须复核锚点。非法settings返回typed invalid_settings。11安装／58运行身份／26实际默认HF导入／108不可变bindings核对通过，无重试／修复重跑／延期／force／自动回滚，卡已关闭。

真实测试仅4个小模型实例、7条16单元50DOF建模记录，NativeMean aliases F33/33、T22/22；另6合成／15mock或普通记录。这个有限兼容PASS不等于全部项目测试或物理资格。旧MRESUME100与安装11路径零交集；旧候选、协议、结果保持，98非NPZ重核而2NPZ未新读。right4旧参考当前source strict mismatch的实际测试通过，原qualified响应不改；right2只读源核同两失配，MREF2来源仍匹配，旧HP数值不被改写。

原alpha5e−7的M-ALPHA1仍14加载态／NOT_PASS，M-RESUME1的原1.20→1.15短段success保持，父与child不拼为原一次完整路径通过；新alpha无HP。原实际R0.37865427196005513→0.3470376815403639 N，下半工件total Fy0.12492121630032427→0.10671287553103108 N；3PNG与一份2帧GIF复用，无新夹持器路径／HP／绘图。

最近取舍转向新alpha峰值／首次下降保存态的独立力参考：先只读核现有入口与成本，再形成具体卡，不重做长加载或掃alpha。父子明确关联、可解释接触／有效夹持、一般LF输入、稳定性和HF5仍未完成。默认API/CLI未来用法已记录；文档示例没有运行，也不是新运行许可。

[实际结果与原图](../lf_data_preparation/native_interface_001/saved_integration_001/RESULTS.md) · [默认入口用法](../docs/NATIVE_EVALUATION_INTERFACE.md) · [最近取舍](../lf_data_preparation/native_interface_001/saved_integration_001/NEXT_STEP_REVIEW.md)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

'''.encode('utf-8')
    history = []
    for name in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
        prior = subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)
        assert (ROOT / name).read_bytes() == prior
        current = prefix + prior + b'\n</details>\n'
        assert current.count(prior) == 1
        (ROOT / name).write_bytes(current)
        history.append(dict(path=name, old_bytes=len(prior), old_sha256=sha256(prior).hexdigest(),
            new_sha256=sha256(current).hexdigest(), history_start_byte=len(prefix), history_end_byte_exclusive=len(prefix) + len(prior), old_body_preserved_exactly=True))
    new_json(STAGE / 'author/execution_documentation_receipt.json', dict(status='pass_closed_actual_execution_documentation',
        source_commit=BASE, card='M-INTEGRATE1', authorized=True, executed=True, execution_status='pass', execution_closed=True,
        recorded_utc=datetime.now(timezone.utc).isoformat(), protocol_sha256=sha(STAGE / 'protocol.json'),
        outer_sha256=sha(STAGE / 'integration_launch.json'), helper_sha256=sha(STAGE / 'run_001/execution_receipt.json'),
        results_sha256=sha(STAGE / 'RESULTS.md'), next_step_sha256=sha(STAGE / 'NEXT_STEP_REVIEW.md'),
        default_core_installed=True, front_history=history, new_tests_or_NPZ_decodes_or_HF_or_plots=0))
    print(json.dumps(dict(status='actual_closed_integration_documented', results_sha256=sha(STAGE / 'RESULTS.md'), next_step_sha256=sha(STAGE / 'NEXT_STEP_REVIEW.md')), ensure_ascii=False))


if __name__ == '__main__':
    main()
