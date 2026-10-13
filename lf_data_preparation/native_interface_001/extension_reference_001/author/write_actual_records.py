"""Record closed M-EREF1 plain evidence and one actual PNG inspection."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import shutil
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
PREP = HERE.parent / 'MEREF1_preparation_001'
REL = 'lf_data_preparation/native_interface_001/extension_reference_001'
STAGE = ROOT / REL
REF = STAGE / 'run_001/reference'
BASE = '8438c55f267246b91d6b320273ecb10665f3e16f'
read = lambda path: json.loads(path.read_bytes())


def new_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    launch, life, summary, raw = [read(path) for path in
        (STAGE/'reference_launch.json', REF/'lifecycle.json', REF/'summary.json', REF/'accepted_015/summary.json')]
    assert launch['status'] == life['status'] == summary['status'] == raw['status'] == 'pass'
    assert launch['invocations'] == 1 and launch['exit_code'] == 0 and launch['stop_reason'] is None
    assert launch['all_bindings_unchanged'] is True
    assert summary['HP_calls_started'] == summary['HP_calls_completed'] == 2
    assert life['accepted_mechanical_states_completed'] == life['workpiece_states_completed'] == 1
    assert life['plot_started'] == life['plot_completed'] == 1
    assert raw['index'] == 15 and summary['states'][0]['index'] == 1
    assert raw['state_sha256'] == summary['states'][0]['state_sha256'] == '3dc492f8aef4751e643ddb1413a797ca39434d349bfed59844d46e4e730015ff'
    assert all(row['pass_gate'] for row in raw['checks'])
    observation = read(REF/'reference_observations.json')
    assert len(observation['entries']) == 10 and all(row['pass_gate'] for row in observation['entries'])
    assert not (STAGE/'RESULTS.md').exists()
    review = read(HERE/'independent_terminal_review.json')
    assert review['blocking_findings'] == []
    qa = dict(card='M-EREF1', status='pass_actual_single_pixel_inspection',
        inspected_utc=datetime.now(timezone.utc).isoformat(), inspected_by='root',
        path=REL+'/run_001/reference/reference_observations.png',
        producer_declared_sha256=summary['observation_outputs']['reference_observations.png'],
        actual_view_image_calls=1, render_retry_or_replot=0,
        title_child1_global15_input1_10_visible=True, all_10_labels_and_error_limit_annotations_legible=True,
        original_gate_at_zero_and_display_axis_visible=True, scope_footer_visible=True,
        clipping_or_covering_observed=False, independent_postrun_binary_hash=False,
        scientific_NPZ_gzip_CSV_decodes=0,
        observation='Original scalar error/limit annotations remain clear despite the wide HP agreement range; no redraw needed.')
    new_json(STAGE/'author/pixel_QA.json', qa)
    shutil.copyfile(PREP/'record_authorization.py', STAGE/'author/record_authorization.py')
    for name in ('independent_terminal_review.json','independent_terminal_review.md'):
        assert not (STAGE/'author'/name).exists()
        shutil.copyfile(HERE/name, STAGE/'author'/name)
    table = '\n'.join(f"| {row['label']} | {float(row['error']):.5e} | {row['limit']} | PASS |" for row in observation['entries'])
    text = f'''# M-EREF1：新1.10 mm保存态独立参考结果

2026-10-13（Asia/Seoul）。已按真实人类批准单次执行并闭卡，实际 **PASS**；本报告不以静审替代计算。执行源为main `{BASE}`，协议SHA `ed835ffd724ad82c3a8870fd05326baf784814fcb16e9f938a6559ad1d8e7135`。提交、推送和恢复确认在执行闭卡后独立记录，不计为新科学计算。

## 整体目标、本步作用及已完成能力

本项目独立读取LF普通几何，在一致物理任务下提供非线性TMC正向响应、输入反力、端口位移、固定工件作用、可恢复状态和真实变形，供外部研究层比较；HF不进行优化、不调用dmftd，MPM暂不实现。默认显式保存态延伸接口已安装并有36项兼容测试证据，原1.15→1.10 mm段已成功且有实际三PNG／两帧GIF。

本步先核新1.10态的生产力、同一PORT方向切线、CSC／KKT及工件投影是否与独立高精度计算一致，避免在未经核对的末态上扩大卸载路径。原B850 `CoreAudit.run_state`及aa86 `WorkpieceCycleAudit.workpiece_checks`、原十五门、分母和局部规则保持。未重做生产F／T、平衡求解、测试、API关联或默认安装，也未重复已有1.15参考。

## 实际执行与覆盖

唯一launcher调用一次、同一子进程已正常退出0，无stop信号、重试、修复重跑、延期或force。outer {launch['elapsed_seconds']:.9f}秒、child实际终止墙钟 {launch['child_terminal_wall_seconds']:.9f}秒；helper lifecycle快照 {life['elapsed_seconds']:.9f}秒。900／960秒批准额度均满足。outer采样进程树峰值 {launch['peak_sampled_tree_RSS_bytes']} B，helper独立采样峰值 {life['sampled_peak_RSS_bytes']} B，均低于8GiB；这是两种采样口径，不能视为OS硬限制。

新HP80／120各一次，共2次开始／2次完成；1个机械态、1个工件检查、1次原普通JSON误差绘图均完成。程序实际完成 {life['checks_completed']} 项检查，原十五类验收门均通过；检查计数不是十五个新门。覆盖原13440单元／27378DOF、322560局部力及同一方向局部切线条目、860160保存总CSC系数组装身份。未独立核全部切线列。

保存态为child001／global15／absolute mean input1.10 mm、unloading、非anchor，SHA `{raw['state_sha256']}`。raw报告保持index15，顶层保持child1及reference_execution_index15。50个原输入／来源绑定在launcher前后保持，六份默认生产入口不变；引用真实成功父段和保留的失败祖先，没有拼接资格。

## 数值效果

下表均为本次原摘要中的归一化误差与原阈值，显示位数仅为阅读方便；完整十进制数、局部极值、原分母及零项保存在[原单态摘要](run_001/reference/accepted_015/summary.json)。它们不是工件Fy的相对百分比。

| 原观察量 | 记录误差 | 原阈值 | 结果 |
| --- | ---: | ---: | --- |
{table}

原保存生产平衡残差约3.95170e−12（门1e−9），独立HP120残差约3.95170e−12（门1e−8）；约束和固定误差为原记录零。材料／Hu局部力与方向切线、HP80／120一致性及工件ON-body／holding分组核对通过。rounded F／J／Hu与保存binary64一致仅保原诊断，不新增应力或Hu数组资格。

## 实际可视化与物理对照

![新1.10单态独立参考误差](run_001/reference/reference_observations.png)

图在批准helper内一次生成，横轴为原误差／原阈值的log10显示，红线为原门；全部点在门内。普通JSON含原error／limit、来源字段和显示值。闭卡后root仅进行一次像素检查，十行标签、原值及资格说明可读，未重绘；见[像素记录](author/pixel_QA.json)。图的零新力学调用是固定纯源码／来源合同，不声称动态监控了全部力学hook。

已有生产实际结构／力／距离：[1.15→1.10真实变形GIF](../saved_extension_002/run_001/view/extended_alpha_half/actual_states.gif)、[局部变形图](../saved_extension_002/run_001/view/comparison.png)、[作用力与距离](../saved_extension_002/run_001/view/distances_forces.png)。本步不重新解码旧媒体或生成旧结构图。

| 保存生产物理量 | 1.15 mm | 新1.10 mm |
| --- | ---: | ---: |
| 输入端施加到模型的反力R（N） | 0.347037681540 | 0.315886016700 |
| 输出端口加权位移（mm） | 1.015317424233 | 1.012776370128 |
| 固定工件所受节点合力Fy（N） | 0.106712875531 | 0.088978471092 |
| 其中材料／Hu的Fy（N） | 0.105858421486／0.000854454045 | 0.088182724549／0.000795746543 |
| 尖端至工件底边有限段间隙（mm） | 0.001285047824 | 0.001730504605 |

物理表直接来自已有[M-EXTEND2普通viewer摘要](../saved_extension_002/run_001/view/extended_alpha_half/summary.json)，不是本轮新计算的标量HP夹持力报告。两侧镜像法向幅值之和是保存弱式节点作用的对称解释，不是净合力或连续接触压力。卸载0.05 mm后输入反力和工件Fy下降、尖端间隙增大，支持继续观察更低目标。

## 资格、局限与下一步

本轮已核新1.10保存态及声明方向。现有公开API要求整个两态result与4次新HP，本轮独立单态／2HP归档不能作为该整个result的matched参考；原response和reader保持。原1.15参考仍属于其原result来源，不重新改绑或拼成新4HP。

原M-ALPHA1及M-EXTEND1 NOT_PASS、成功父段、祖先失败、未完成完整原／延伸路径均保留。压力、有效夹持、完全释放、稳定性、全列切线、一般LF与HF5资格保持false。本次一致性通过不能证明介质参数物理准确或整个卸载路径完成。

根据本次PASS与已有作用／间隙趋势，下一步最近阶段拟从已成功的1.10末态显式追加1.05 mm，保持全部原物理字段、原路径前缀和验收门，复用默认入口及原纯viewer，取得新反力、工件作用、距离和实际变形。无需再次安装或重跑已完成36项兼容测试；新平衡路径、资源及绘图范围另成具体卡，经静审、发布／恢复核对和直接批准后执行。若新段失败保真实partial并先排查，不在旧窗口内重试。

## 代码与可恢复证据

执行入口：[唯一launcher](launch_reference.py)、[单态参考包装](execute_extension_reference.py)、[纯摘要图](plot_reference_observation.py)；数学实现来源及原15门见[M-EREF1卡](M-EREF1_CARD.md)。实际闭卡：[launcher](reference_launch.json)、[lifecycle](run_001/reference/lifecycle.json)、[顶层摘要](run_001/reference/summary.json)、[独立终态审阅](author/independent_terminal_review.md)、[真实直接批准](author/direct_human_reply.json)。新科学文件SHA继承批准窗口内producer的原记录，发布期只stat核大小和增量普通文件SHA，不在闭窗外重算数组／gzip／PNG身份或科学结果。
'''
    with (STAGE/'RESULTS.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
    prefix = '''# 最新状态：M-EREF1已实际PASS，新1.10态参考完成

2026-10-13（Asia/Seoul）。main8438c55源按真实直接批准单次执行；2HP／1机械态／1工件检查／1误差图、原十五门通过，outer99.3702秒，采样树峰值1277128704B。已正常终止并闭卡，50来源绑定及默认入口保持，原失败和完整任务未完成保留。

新参考只核child1／global15／1.10，现有两态API全段匹配及压力／有效夹持／HF5资格不升级。图已一次像素核对；最新目标／作用／限制与后续1.05建议见[M-EREF1结果](../lf_data_preparation/native_interface_001/extension_reference_001/RESULTS.md)。下一卸载仍须新具体阶段卡及批准，本卡余时不是新许可。

---

'''.encode('utf-8')
    histories = []
    for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
        previous = subprocess.check_output(['git','show',BASE+':'+name], cwd=ROOT)
        assert (ROOT/name).read_bytes() == previous
        current = prefix+previous
        assert current.count(previous) == 1
        (ROOT/name).write_bytes(current)
        histories.append(dict(path=name, old_sha256=sha256(previous).hexdigest(), new_sha256=sha256(current).hexdigest(),
            history_start_byte=len(prefix), history_end_byte_exclusive=len(current), original_history_contiguous_once=True))
    new_json(STAGE/'author/execution_documentation_receipt.json', dict(card='M-EREF1', actual_execution_closed=True,
        actual_execution_status='pass', source_baseline_commit=BASE, front_history=histories,
        postrun_new_PNG_pixel_QA_calls=1, scientific_NPZ_gzip_CSV_decodes_or_hashes=0,
        new_mechanics_HP_solver_or_plots=0, default_runtime_changes=0, full_HF5_complete=False))
    print(json.dumps(dict(status='closed_actual_records_written', card='M-EREF1', fronts=2,
        actual_HP_calls=2, pixel_QA_calls=1, new_science=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
