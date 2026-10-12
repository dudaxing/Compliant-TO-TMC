"""Record closed M-AREF1 JSON evidence and reuse the original two-state visuals."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/alpha_reference_001'
STAGE = ROOT / REL
BASE = 'e687bdf1ca60edbd0fd044f4f8c990b3b9ccc182'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def write_new(path, raw):
    with path.open('xb') as output:
        output.write(raw)


def sci(value):
    return format(float(value), '.4e')


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    outer = read(STAGE / 'reference_launch.json')
    reference = STAGE / 'run_001/reference'
    helper, summary = (read(reference / name) for name in ('lifecycle.json', 'summary.json'))
    assert outer['status'] == helper['status'] == summary['status'] == 'pass' and outer['exit_code'] == 0
    assert outer['invocations'] == 1 and outer['stop_reason'] is None and outer['all_bindings_unchanged'] is True
    assert helper['HP_calls_started'] == helper['HP_calls_completed'] == 4
    assert summary['accepted_states'] == helper['workpiece_states_completed'] == 2
    rows = summary['states']
    assert [row['reference_execution_index'] for row in rows] == [13, 14] and [row['index'] for row in rows] == [0, 1]
    view_rows = read(ROOT / 'lf_data_preparation/native_interface_001/saved_continuation_001/run_001/view/resumed_alpha_half/summary.json')['rows']
    assert [row['state_sha256'] for row in rows] == [row['state_sha256'] for row in view_rows]
    comparisons = []
    for group, component, name, limit in (
        ('force_checks', 'total', '全局总力', '1e−11'),
        ('force_checks', 'material', '全局材料力', '1e−9'),
        ('force_checks', 'regularization', '全局Hu力', '1e−9'),
        ('tangent_checks', 'total', 'PORT总切线作用', '1e−10'),
        ('tangent_checks', 'material', 'PORT材料切线作用', '1e−9'),
        ('tangent_checks', 'regularization', 'PORT Hu切线作用', '1e−9')):
        assert all(row[group][component]['pass_gate'] is True for row in rows)
        comparisons.append(f"| {name} | {sci(rows[0][group][component]['normalized_error'])} | {sci(rows[1][group][component]['normalized_error'])} | {limit} |")
    comparisons += [
        f"| CSC总方向作用 | {sci(rows[0]['CSC_total_action_check']['normalized_error'])} | {sci(rows[1]['CSC_total_action_check']['normalized_error'])} | 1e−10 |",
        f"| KKT自由力方向作用 | {sci(rows[0]['augmented_checks']['force']['normalized_error'])} | {sci(rows[1]['augmented_checks']['force']['normalized_error'])} | 1e−10 |",
        f"| 独立相对平衡残差 | {sci(rows[0]['metrics']['independent_relative_residual'])} | {sci(rows[1]['metrics']['independent_relative_residual'])} | 1e−8 |",
        f"| 全局总力HP80／120一致性 | {sci(rows[0]['force_checks']['total']['hp80_hp120_error'])} | {sci(rows[1]['force_checks']['total']['hp80_hp120_error'])} | 1e−40 |"]
    comparison_table = '\n'.join(comparisons)
    physical = []
    for key, name in (('R_input_N', '输入反力R（N）'), ('q_out_mm', '输出均值位移（mm）'),
                      ('total_body_Fy_N', '下半工件total Fy（N）'), ('material_body_Fy_N', '下半工件material Fy（N）'),
                      ('regularization_body_Fy_N', '下半工件Hu Fy（N）'), ('tip_to_bottom_mm', '尖端到底面有限采样间隙（mm）')):
        physical.append(f"| {name} | {view_rows[0][key]} | {view_rows[1][key]} |")
    physical_table = '\n'.join(physical)
    results = f'''# M-AREF1 实际结果：两态独立参考PASS，窗口已关闭

整体目标是独立HF有限变形／TMC前向评价：读取普通LF几何，在明确任务下给出实际变形、反力及可解释的工件作用，供外部研究层比较。HF不优化、不调用dmftd，MPM暂不实现；main、既定origin和science0.5.0保持。M-INTEGRATE1已安装默认保存态续算，有限25项兼容测试通过。

本卡为什么做：新alpha=5e−7的峰值／首次下降已保存，但旧alpha的48HP不能移植。复用已验证数学，在实际两个接受态上补独立力／声明方向切线／工件投影证据，使后续API能够区分原生产成功、独立参考和物理夹持资格。本卡没有重做加载／卸载平衡。

2026-10-12（Asia/Seoul）直接批准后唯一session54727真实terminal exit0；outer PASS、一次启动、stop=None、48不可变bindings保持。outer {outer['elapsed_seconds']}秒，child终端墙钟{outer['child_terminal_wall_seconds']}秒，helper {helper['elapsed_seconds']}秒；树RSS采样峰{outer['peak_sampled_tree_RSS_bytes']}B、helper峰{helper['sampled_peak_RSS_bytes']}B，均在900／960秒、8GiB内。实际4HP开始／4完成、2机械态／2工件态、{helper['checks_completed']}项运行检查。没有重试、修复重跑、延期、force、新生产F／T、模型、平衡、测试、API关联或绘图；未用时间不构成新许可。

每态覆盖13440单元／27378 DOF、322560局部三分量力条目、322560局部三分量方向作用条目，以及860160个总保存张量系数的CSC组装身份。HP80／120各一次，Decimal3000全局散射并trap Inexact；原十五门、原分母／floor保持。实际PORT方向由原五节点b_in给出，固定分量0、deltaR=0。完整CSC组装身份和单PORT解析方向比较不等于独立验证全部切线列。

原执行索引13／14保留在raw accepted_013／014科学summary；顶层只复制元数据到child0／1，保留原索引、state／descriptor身份、leg与continuation_anchor。子0为原1.20 mm峰值锚点，子1为原1.15 mm首次下降。原result／response／缓存及图件不改，父M-ALPHA1 NOT_PASS／14加载态／time_limit保持；不拼接为原一次完整路径通过。

| 已产普通summary中的归一化检查 | 峰值1.20 mm | 首次回撤1.15 mm | 原门 |
| --- | ---: | ---: | ---: |
{comparison_table}

数值为报告原值的显示舍入；完整Decimal、原分母与限值见下方两个原summary。误差使用原全局／分量规范，不是标量工件力的百分比。两态均值、固定、全局平衡及原局部门也由继承原方法核对；J/F/Hu rounded记录仍仅为原诊断，没有新增stress-HP／独立Hu数组门或能量梯度资格。机械辅助材料能量保持not_evaluated／unqualified／absent，独立解析材料能量仅归档。

| 原实际保存值（同两态，未新绘图／积分） | 峰值1.20 mm | 首次回撤1.15 mm |
| --- | ---: | ---: |
{physical_table}

输入反力是原保存乘子，工件数值来自原保存视图摘要；本次独立方程与aa86 signed total／material／Hu投影检查已实际完成。它们说明此固定方形任务在首次回撤时作用减小，不构成连续压力、有效夹持力或完整卸载曲线。工件固定、center(71,40) mm、side18 mm；E1MPa、ν0.3、厚度20mm、h0.5mm、gamma1e−6、alpha5e−7保持。

![原两个保存态实际变形GIF，原字节复用](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

[原位形／反力对照图](../saved_continuation_001/run_001/view/comparison.png) · [原距离／工件作用图](../saved_continuation_001/run_001/view/distances_forces.png) · [原峰值场图](../saved_continuation_001/run_001/view/peak_fields.png)

[实际顶层参考](run_001/reference/summary.json) · [原13峰值科学summary](run_001/reference/accepted_013/summary.json) · [原14回撤科学summary](run_001/reference/accepted_014/summary.json) · [helper终态](run_001/reference/lifecycle.json) · [outer终态](reference_launch.json) · [直接批准](author/direct_human_reply.json)

边界：只核这两个新alpha接受态及声明方向。未给父14加载前缀、完整原路径、全部切线列、连续总压力／有效夹持、移动／摩擦／其他形状完整验证、网格／域／参数稳定性或HF5升级资格。原producer资格及response的not_provided保持；新参考目前独立存档，尚未运行API关联。后续据本次结果最近应关联这两态现有参考与原图，先做好子段范围说明，不重做平衡／HP或扩展参数。
'''
    next_step = '''# M-AREF1之后的最近取舍

本次两态独立参考实际PASS并闭卡，原力核、切线和十五门没有修复或放宽。它补齐了alpha5e−7的原1.20／1.15 mm两接受态力与PORT方向证据，尚未把参考挂入对外摘要。原M-ALPHA1失败、父14加载前缀缺独立HP和整个原路径未一次完成保持。

最近功能步骤是复用默认 `hf_eval.native_response.summarize_saved_native_result`，为这两个保存态生成一份新的linked_response及轻索引，连接新参考和既有三PNG／两帧GIF。源码 `_reference` 要求顶层index0／1、相同state/target/result/model、每态2HP、完整DOF声明与实际reference来源；本次摘要已按真实original13／14保留并明确映射。`_views`要求原same-result/model/task与2行同态，原M-RESUME1 manifest已存在。此判断来自源码和普通记录，没有调用API。

续算scope在既有reader中明确为child accepted suffix，full_original_path_reference_pass强制false。将来必须保留父NOT_PASS和原result／response／HP／图件原字节，把child短段参考通过、父前缀覆盖缺口与物理夹持资格区分清楚。单向切线／弱式工件合力不被改名为全列HP、总压力或有效夹持。

最近卡只拟普通JSON摘要与索引关联，不新增NPZ解码、构模、F／T／HP／求解或图，不合成完整路径资格。具体输入／输出／绑定、有限资源和独立静审应在实际候选准备后冻结，再取得新直接批准；本卡余时不续用，不提前运行。最近不重做长加载、不扫新alpha、不补全父14态HP。

更远路线仍是：明确完整父子结果与覆盖；解释材料+Hu边界作用并形成压力／有效夹持定义；在用户认可任务下做网格／域／参数稳定性；推广普通LF几何／多形状任务和有限批量，再决定HF5。上述能力未实现或未完成资格，不由本次两态PASS自动取得。
'''
    write_new(STAGE / 'RESULTS.md', results.replace('\n', '\r\n').encode('utf-8'))
    write_new(STAGE / 'NEXT_STEP_REVIEW.md', next_step.replace('\n', '\r\n').encode('utf-8'))
    head = f'''# 当前接续：M-AREF1两态独立参考实际PASS，窗口已关闭

整体目标仍为独立HF有限变形／TMC前向评价，读取普通LF几何，在明确任务下给出实际变形、反力和可解释工件作用供外部研究层比较。HF不优化、不调用dmftd，MPM暂不实现；main、既定origin、science0.5.0保持。

M-AREF1经本轮直接批准唯一session54727实际terminal exit0/PASS，outer{outer['elapsed_seconds']}秒、helper{helper['elapsed_seconds']}秒、树RSS采样峰{outer['peak_sampled_tree_RSS_bytes']}B、stopNone；4HP开始/4完成、2机械/2工件态、{helper['checks_completed']}运行检查，48bindings保持。全部13440单元27378DOF三力、原PORT方向作用、保存CSC组装身份/KKT及signed工件投影经原15门通过；原数学／分母／floor／11依赖与自身source保持。无重试/修复重跑/延期/force或新生产F/T、平衡、测试、API关联、绘图，窗口关闭。

原任务13/14在raw参考summary保持，顶层只复制为child0/1并保原identity/leg/anchor。原alpha5e−7的M-ALPHA1 NOT_PASS／14加载态保持，M-RESUME1仅1.20→1.15 mm短段success；原result/response/缓存／图件不改，不拼接为原一次完整路径通过。新alpha现在仅这两个接受态有4次独立HP，旧48HP不移植。原R0.37865427196005513→0.3470376815403639 N、下半工件total Fy0.12492121630032427→0.10671287553103108 N；三PNG／两帧实际GIF原字节复用。

默认保存态续算已由M-INTEGRATE1安装，有限25兼容测试PASS保持。本次不是全部切线列独立验证、连续压力／有效夹持或完整卸载曲线；机械aux能量仍not_evaluated。新参考尚未API关联，原producer flags保持。最近拟复用已有摘要reader关联同两态参考与原图，先冻结具体候选／范围／资源再直接批准，不能续用本卡余时。

完整父子参考覆盖、连续总压力／有效夹持、一般LF几何可靠性、移动／摩擦与其他形状完整验证、网格／域／参数稳定性、全部切线列及HF5仍未完成。

[实际结果与原图](../lf_data_preparation/native_interface_001/alpha_reference_001/RESULTS.md) · [最近取舍](../lf_data_preparation/native_interface_001/alpha_reference_001/NEXT_STEP_REVIEW.md) · [默认入口用法](NATIVE_EVALUATION_INTERFACE.md)

<details>
<summary>更新前完整原文（历史状态不代表当前）</summary>

'''.replace('\n', '\r\n').encode('utf-8')
    history = []
    for name in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
        path = ROOT / name
        prior = subprocess.check_output(['git', 'show', BASE + ':' + name], cwd=ROOT)
        assert path.read_bytes() == prior
        raw = head + prior + b'\r\n</details>\r\n'
        assert raw.count(prior) == 1
        path.write_bytes(raw)
        history.append(dict(path=name, old_sha256=sha256(prior).hexdigest(), new_sha256=sha(path),
            history_start_byte=len(head), history_end_byte_exclusive=len(head)+len(prior)))
    value = dict(status='closed_execution_documentation_written', execution_status='pass', source_commit=BASE,
        scientific_session=54727, actual_outer_sha256=sha(STAGE / 'reference_launch.json'),
        actual_helper_sha256=sha(reference / 'lifecycle.json'), actual_summary_sha256=sha(reference / 'summary.json'),
        output_SHA256={REL + '/' + name: sha(STAGE / name) for name in ('RESULTS.md', 'NEXT_STEP_REVIEW.md')},
        front_history=history, old_NPZ_byte_reads_decodes_HF_HP_F_T_solver_API_plot_calls=0)
    write_new(STAGE / 'author/execution_documentation_receipt.json', (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8'))
    print(json.dumps(dict(status=value['status'], fronts=2, results_sha256=sha(STAGE / 'RESULTS.md')), ensure_ascii=False))


if __name__ == '__main__':
    main()
