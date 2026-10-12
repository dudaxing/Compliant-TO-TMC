"""Save actual M-ALINK1 ordinary records and prepend current documentation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/alpha_link_001'
STAGE = ROOT/REL
HERE = Path(__file__).resolve().parent
BASE = '1e639641625b4d0f92eb84aff4b4c6fdb05d0171'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
def new(path, raw):
    with path.open('xb') as output:
        output.write(raw)
def json_new(path, value):
    new(path, (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8'))

assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == BASE
launch, run = read(STAGE/'link_launch.json'), read(STAGE/'run_001/execution_receipt.json')
assert launch['status'] == run['status'] == 'pass' and launch['exit_code'] == 0
assert launch['invocations'] == 1 and launch['stop_reason'] is None
assert launch['all_bindings_unchanged'] is run['all_bindings_unchanged'] is True
assert run['calls'] == dict(saved_summary_started=1,saved_summary_completed=1,response_writes=1,index_writes=1)
copies = ['record_authorization.py','prepare_execution_records.py',
    'execution_terminal_scope_review.json','execution_terminal_scope_review.md',
    'execution_input_identity_review.json','execution_input_identity_review.md']
for name in ('execution_terminal_scope_review.json','execution_input_identity_review.json'):
    review = read(HERE/name)
    assert review['status'].startswith('pass')
for name in copies:
    new(STAGE/'author'/name, (HERE/name).read_bytes())

results = '''# M-ALINK1 实际结果：两态参考与变形图关联通过

2026-10-12（Asia/Seoul），直接批准后唯一启动已终端 exit0／PASS，窗口关闭。新增响应、轻索引和执行回执均已保存。现有默认 reader、原力核、切线、数学门及物理定义没有修改。

## 目标、完成内容与效果

整体目标仍为独立 HF 有限变形／TMC 前向评价：读取普通 LF 几何，在明确任务下提供实际变形、反力和可解释工件作用，供外部研究层比较。HF 不优化、不调用 dmftd，MPM 暂不实现；main、既定 origin 与 science0.5.0 保持。

M-INTEGRATE1 已安装保存态续算入口；M-RESUME1 得到 alpha=5e−7 的原峰值1.20与首次回撤1.15 mm两态；M-AREF1 为同两态完成4次 HP80／120独立参考与原十五门核对。本次只补数据入口，使调用方通过一份新的 linked_response 与轻索引同时找到两态物理响应、已有参考及原3PNG／两帧GIF。原 producer response、参考、视图与图件保持原字节。

摘要开始／完成各1，响应写入1、索引写入1；两态 reference 与 views 均 matched。API实际读取5份普通JSON、核12份声明参考Python来源和原4份媒体字节，HF导入仅包与native_response。30份原绑定在唯一运行前后保持。没有新 NPZ／NPY、科学 gzip／CSV 读取、构模、F／T、HP、平衡求解、测试或绘图；零新力学依据冻结调用路径及纯摘要模块闭包，不是全库动态力学钩子监控。

## 实际资源与可审查响应

| 记录 | 实际值 |
| --- | ---: |
| helper记录耗时 | 0.8400699000048917 s |
| child完整终端wall | 1.0407080000150017 s |
| outer含前后核对 | 1.448175400000764 s |
| helper采样峰值RSS | 23388160 B |
| outer采样进程树峰值RSS | 41127936 B |

满足helper180／outer240秒、采样8GiB；RSS为采样，不是OS硬上限。首错停止规则未触发，没有重试、修复重跑、延期或force。

下表复用原真实保存数值，本次未生成新物理响应：

| 状态 | child／原目标 | 输入R (N) | q_out (mm) | 下半工件有符号total Fy (N) |
| --- | --- | ---: | ---: | ---: |
| 1.20 mm峰值锚点 | 0／13 | 0.37865427196005513 | 1.016934534302024 | 0.12492121630032427 |
| 1.15 mm首次回撤 | 1／14 | 0.3470376815403639 | 1.0153174242325562 | 0.10671287553103108 |

R是半模型输入反力；工件Fy是下半固定刚体弱式作用合力，包含材料与Hu贡献，尚不等于有效夹持力。q_out是加权端口位移，不是表面间隙。两个端点不构成完整卸载曲线。new linked_response.call_counts与timing_seconds仍描述原生产求解，不能把它们当本次调用；本次次数和资源以本目录执行回执／launcher为准。原evaluate专属invocation、evaluation_elapsed_seconds、evaluation_elapsed_scope不由纯summary复制，仍保存在未改原response并被轻索引链接；共有公有摘要字段只有reference／views按本卡关联，其余保持一致。

## 保留的范围与未实现功能

accepted_reference_pass=true、full_path_reference_pass=true只覆盖已完成的两态child短段；reference_scope为Child accepted suffix only。full_original_path_reference_pass与path.full_original_path_completed均false，target_response为null。父M-ALPHA1仍failed／time_limit、14加载态、NOT_PASS，不把父子拼为一次原15目标完整求解通过，也不转移两态参考到父前缀。原producer三资格flags均false。

旧view.reference_available=false保留绘制时历史事实，图件未显示新HP误差场。原连续材料＋Hu表面总压力、有效夹持定义及资格、完整原路径参考、稳定性、全部切线列、一般LF输入／更多工件与运动摩擦任务、HF5仍未完成。

## 原实际效果与可恢复入口

![原峰值与首次回撤实际变形](../saved_continuation_001/run_001/view/resumed_alpha_half/actual_states.gif)

原图件：[结构与力](../saved_continuation_001/run_001/view/comparison.png) · [距离与有符号力](../saved_continuation_001/run_001/view/distances_forces.png) · [峰值场](../saved_continuation_001/run_001/view/peak_fields.png)。本轮没有重新读取像素或绘图。

[新关联响应](run_001/linked_response.json) · [轻索引](run_001/light_index.json) · [helper回执](run_001/execution_receipt.json) · [outer终端](link_launch.json) · [终端／范围独立核对](author/execution_terminal_scope_review.md) · [输入／输出独立核对](author/execution_input_identity_review.md) · [下一步取舍](NEXT_STEP_REVIEW.md)

新索引的artifact路径相对仓库根，支持不同目录恢复；继承continuation中的原绝对路径作为历史记录不改写，可用索引中的parent_result等相对入口定位。不可变protocol／card仍保留prepared=true、authorized=false、executed=false的准备事实；本次实际直接批准与运行分别在author/authorization、direct_human_reply及run／launch中记录。
'''
next_step = '''# M-ALINK1之后的最近取舍

同两态响应、独立参考和实际变形图已经实际关联通过。默认API无需修复，不再为本次同一对状态重复关联、测试或HP；本窗口关闭。父14加载前缀、child原13／14短段及完整原任务资格已明确区分。

接下来应转回物理功能：先利用现有父子保存结果说明完整加载与首次回撤的状态覆盖、材料与Hu工件作用及仍缺失的卸载段，形成用户可直接检查的路径和力解释。现有两态弱式合力已获得独立核对，但连续表面总压力和有效夹持定义仍缺；不能用两侧法向幅值和或node-window距离代替压力／夹持资格。

最近只先做普通源码、已有记录和既有材料／Hu诊断的静态规划，决定最小功能实现及可视化范围；数值读取、新图或力学计算均在具体卡冻结后单独获批。是否继续卸载、扩展表面力重构或补参考，应由这个解释中的实际缺口决定。当前不再重复长加载、扫描alpha、补全父14态HP、宣称HF5或启动批量排名。

更远目标保持：有定义的材料＋Hu连续总压力和有效夹持、网格／域／参数稳定性、普通LF几何、多形状／运动与摩擦工件、有限批量，最后再判断HF5。此文件是后续取舍记录，不提供新的计算授权。
'''
new(STAGE/'RESULTS.md', results.encode('utf-8'))
new(STAGE/'NEXT_STEP_REVIEW.md', next_step.encode('utf-8'))
prefix = '''# 当前更新：M-ALINK1实际关联通过（2026-10-12，Asia/Seoul）

本次直接批准的唯一API关联已终端exit0／PASS，窗口关闭。alpha=5e−7的原1.20／1.15 mm两个保存态已在新linked_response和轻索引关联同态4次既有HP参考、原3PNG／两帧GIF；摘要开始／完成、响应写入、索引写入各1，30份原绑定保持。默认API／力核／切线／门／物理任务原字节保持。

资源：helper记录0.8400699000048917秒，child完整终端wall1.0407080000150017秒，outer1.448175400000764秒；helper采样23388160B、tree采样41127936B，满足180／240秒和8GiB。无新NPZ／科学gzip／CSV读取、F／T／HP／平衡求解／测试／绘图，无重试、修复重跑、延期或force。

原输入R：0.37865427196005513→0.3470376815403639N；下半工件total Fy：0.12492121630032427→0.10671287553103108N。均为原保存响应。子段reference／views matched，full_path_reference_pass只覆盖两态child；full_original_path_reference_pass=false。父M-ALPHA1仍time_limit／NOT_PASS，原完整15目标未一次完成，原producer三flags false，不升级压力／有效夹持／稳定性／全列HP或HF5。

整体目标仍为普通LF几何上的独立HF有限变形／TMC前向评价。已实现NumPy完整力、切线／组装、均值输入平衡与缓存、固定方形工件作用、保存态续算默认入口、两态独立参考和本次可恢复关联。连续材料＋Hu表面总压力、有效夹持、完整原路径参考、稳定性、一般LF输入与更多物理任务仍未完成。

最近转回现有父子路径与材料／Hu作用的可读物理解释，依据实际缺口再准备最小功能卡；本文件不授新增计算。完整记录：[实际结果](../lf_data_preparation/native_interface_001/alpha_link_001/RESULTS.md)、[响应](../lf_data_preparation/native_interface_001/alpha_link_001/run_001/linked_response.json)、[轻索引](../lf_data_preparation/native_interface_001/alpha_link_001/run_001/light_index.json)、[后续取舍](../lf_data_preparation/native_interface_001/alpha_link_001/NEXT_STEP_REVIEW.md)。

原准备protocol和卡的authorized/executed=false保留历史事实；实际授权与运行另存。以下保留之前所有记录，旧main1e63964及84c67e4的准备／执行说明不覆盖；实际发布和异地恢复proof保存到外部记录，推送后生成。

---

'''.encode('utf-8')
fronts = []
for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'):
    path = ROOT/name
    prior = subprocess.check_output(['git','show',BASE+':'+name], cwd=ROOT)
    assert path.read_bytes() == prior
    raw = prefix+prior
    path.write_bytes(raw)
    fronts.append(dict(path=name, old_sha256=hashlib.sha256(prior).hexdigest(),new_sha256=sha(path),
        history_start_byte=len(prefix),history_end_byte_exclusive=len(raw),old_history_occurrences=raw.count(prior)))
outputs = {f'{REL}/run_001/{name}':sha(STAGE/'run_001'/name) for name in
    ('linked_response.json','light_index.json','execution_receipt.json')}
json_new(STAGE/'author/execution_documentation_receipt.json', dict(status='actual_pass_records_saved',
    created_utc=datetime.now(timezone.utc).isoformat(), source_commit=BASE, executed_card='M-ALINK1',
    authorized=True,executed=True,execution_closed=True,execution_status='pass',front_history=fronts,
    closed_output_SHA256=outputs, copied_source_and_reviews={name:sha(STAGE/'author'/name) for name in copies},
    no_new_mechanics_API_tests_media_or_archive_reads=True, whole_HF5_complete=False))
print(json.dumps(dict(status='actual_execution_records_and_fronts_saved', fronts=fronts,
    original_inputs_changed=False,new_API_tests_mechanics_plots=0),ensure_ascii=False))
