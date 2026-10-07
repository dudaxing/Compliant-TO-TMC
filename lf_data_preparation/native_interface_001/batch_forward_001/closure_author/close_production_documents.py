"""Save a closed-production record from actual JSON and independent saved-only review."""
from pathlib import Path
from datetime import datetime, timezone
from hashlib import sha256
import json

root=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
author=Path(__file__).resolve().parent
stage=root/'lf_data_preparation/native_interface_001/batch_forward_001'
read=lambda path:json.loads(path.read_bytes())
sha=lambda path:sha256(path.read_bytes()).hexdigest()
worker=read(stage/'run_001/execution_receipt.json')
launch=read(stage/'production_launch.json')
protocol=read(stage/'production_protocol.json')
review_file=author/'review/batch_forward_closure_review.json'
review=read(review_file)
assert worker['status']==launch['status']=='pass' and launch['exit_code']==0 and launch['stop_reason'] is None
assert worker['all_bindings_unchanged'] is launch['all_bindings_unchanged'] is True
assert all(sha(root/name)==pin for name,pin in protocol['bindings'].items())
assert not (stage/'stop_requested.txt').exists()
assert sha(review_file)=='504bc2e3a3026d1982b4de9736fa9c14ba4bfcf0f58e2ae7cf59a2005d3f6300'
(stage/'production_closure_review.json').write_bytes(review_file.read_bytes())
(stage/'closure_author').mkdir()
for name,source in [('verify_batch_forward_saved.py',author/'review/verify_batch_forward_saved.py'),
                    ('record_running_snapshot.py',author/'record_running_snapshot.py'),
                    ('close_production_documents.py',Path(__file__))]:
    (stage/'closure_author'/name).write_bytes(source.read_bytes())
case_rows=[]
for label,case in worker['cases'].items():
    result=read(root/case['result_file'])
    assert len(result['states'])==4 and result['task_target_executed'] is True
    assert case['observed_F_T']==dict(force_calls=14,force_calls_completed=14,tangent_calls=9,tangent_calls_completed=9)
    row=result['states'][-1]
    case_rows.append(dict(label=label,accepted_states=4,d_mm=row['d'],R_input_N=row['R_input'],
        q_out_mm=row['q_out'],minimum_J=row['minimum_J'],relative_residual=row['relative_residual'],
        case_elapsed_seconds=case['elapsed_seconds'],result_sha256=case['result_sha256'],
        response_sha256=case['response_sha256']))
now=datetime.now(timezone.utc).isoformat()
progress=dict(schema_version='native-batch-forward-progress-1.0',status='production_pass_reference_and_views_pending',
    baseline_commit=protocol['baseline_commit'],protocol_sha256=sha(stage/'production_protocol.json'),
    terminal_session_id=95337,actual_terminal_exit_code=0,actual_batch_invocations=1,
    cases=case_rows,helper_seconds=worker['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
    helper_peak_sampled_RSS_bytes=worker['peak_sampled_RSS_bytes'],outer_peak_sampled_tree_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
    actual_new_HP_calls=0,actual_new_physical_views=0,HF5_qualified=False,ranking_qualified=False,
    production_closure_review_sha256=sha(stage/'production_closure_review.json'),
    next='Fresh per-case2N independent reference (actualN4), then original-scale and explicit40x saved-state views',
    created_utc=now)
(stage/'closure_progress.json').write_text(json.dumps(progress,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
table=['| 例 | 原生网格 | 末态输入 mm | 输入反力 N | 输出端口位移 mm | min J | API整例秒 |',
       '|---|---|---:|---:|---:|---:|---:|']
for row,h in zip(case_rows,(1.,.5)):
    table.append(f"| {row['label']} | h={h:g} mm | {row['d_mm']:.9g} | {row['R_input_N']:.9g} | {row['q_out_mm']:.9g} | {row['minimum_J']:.9g} | {row['case_elapsed_seconds']:.6f} |")
report=f'''# 两例真实 batch：生产阶段完成

UTC {now}：一次生产已实际终止，exit0；不是观察超时，也不再有本卡计算。独立saved-only闭卡核对通过。独立HP和新图仍待下一阶段，HF5与排名未完成。

整体目标是读取LF/N4普通几何，在明确一致的独立HF任务下给外部研究层提供非线性响应和接触相关观察；HF不包含优化器，不调用dmftd。本步验证同任务批量分析功能，不生成正式标签。

已做：使用发布版本aa072的28项HF执行源，冻结source/input/包装/审阅共52项绑定；原两例task及geometry保留，只有身份与各自设计/网格不同，19共同物理键不变。新批量API从无关cwd、显式repo顺序执行两例各一次，构模、求解、缓存写出、formatter和responsewriter各一次。源码、complete/full/tangent、四点0/.005/.010/.025 mm、min_increment6.25e-5及原门保持。为什么：让mock通过的薄入口确实产生两套可对照的真实结果和index，同时保留LF研究层。

实际效果：每例4原目标态、无额外二分态，14F/14完成、9T/9完成、1solve；8项once delegate逐例1次，callback4次，cached writer新增F/T为0。原J>0、production residual1e-9、native constraint bound、globalbalance1e-6及fixed8e-11 mm门通过；23 model fields/完整JSON与54份原saved outputs身份核对一致。

'''+'\n'.join(table)+f'''

资源实际：helper {worker['elapsed_seconds']:.9f}秒，outer {launch['elapsed_seconds']:.9f}秒；helper采样峰RSS {worker['peak_sampled_RSS_bytes']} bytes，outer采样child-tree峰RSS {launch['peak_sampled_tree_RSS_bytes']} bytes，均在原2400/2460秒、8GiB内。helper elapsed覆盖imports至最终hash/checkpoint；最后receipt写出由outer计时覆盖。每case一次GC清理不可达递归闭包；不声称OS RSS必然立即下降。52 bindings前后不变、无stop signal。

两例是两个不同LF设计在各自原生网格上的同任务分析。q_out是加权端口位移；任务无工件，因此没有夹持力/接触/压力资格。即使两个响应可并列查看，也不能当作同设计网格收敛或正式排名。原response/index producer/reference/view资格保持未验证，HP_all_columns/contact/clamp/pressure/HF5/ranking不扩。

可审查：[执行卡](EXECUTION_CARD.md)、production_protocol.json、production_launch.json、run_001/execution_receipt.json、run_001/accepted_progress.jsonl、run_001/batch/index.json及production_closure_review.json。closure_author保存stdlib核对与文档recipe。progress_snapshot_001.json/live_observation_001.json只保留历史运行时刻，不再表示进程存活。

下一步：实际N均4；分别新卡fresh8HP80/120覆盖所有接受态/全单元DOF和既有PORT方向切线，预算coarse240/270秒、fine900/960秒各采样8GiB（旧同N成本只用于预算，不继承HP资格）。然后新saved-view卡生成每例4真实帧PNG/GIF、x1与明确40x补充、力/位移/J/平衡曲线，并保存自有qualified_response。当前这些尚未执行。
'''
(stage/'RESULTS.md').write_text(report,encoding='utf-8')
front=f'''## 当前：两例真实 batch 生产阶段已完成

UTC {now}：新顺序batch实际terminal exit0，canonical/native_fine各完成原0/.005/.010/.025 mm四态，各14F/9T/1solve、8项真实入口各一次、cached save新增F/T=0。整段helper950.6635555秒/outer951.8787648秒，采样RSS在8GiB内，52绑定不变，独立saved-only闭卡核对通过。

末态canonical R=0.00521459203 N/q_out=0.0286037185 mm/minJ=0.996581260；native_fine R=0.00375627879 N/q_out=0.0238778244 mm/minJ=0.997535854。原生产门保持；两设计不同且网格各自native，不授网格收敛/排名。新独立HP与图尚未执行，HF5整体未完成。

[实际阶段报告](../lf_data_preparation/native_interface_001/batch_forward_001/RESULTS.md)。新参考候选只在外部source-only准备；按实际N4新卡各8HP后再生成自己的图，不重跑已闭生产卡。以下原字节保留为运行历史；当前以上方及实际terminal记录为准。

---

'''
changes={}
for logical,prefix in [('docs/CURRENT_STATUS.md',front),('docs/NATIVE_BATCH_INTERFACE.md',
    '当前更新：两例原示例已经实际完成生产计算；各4态，缓存保存零新增F/T，独立HP和新图仍待执行。详细结果见[真实阶段报告](../lf_data_preparation/native_interface_001/batch_forward_001/RESULTS.md)。下文原字节保留为aa072功能阶段说明，其中“尚未执行”描述当时状态。\n\n---\n\n')]:
    path=root/logical
    old=path.read_bytes()
    path.write_bytes(prefix.encode('utf-8')+old)
    changes[logical]=dict(before_sha256=sha256(old).hexdigest(),after_sha256=sha(path))
(stage/'production_documentation_install.json').write_text(json.dumps(dict(created_utc=now,
    changes=changes,results_sha256=sha(stage/'RESULTS.md'),progress_sha256=sha(stage/'closure_progress.json'),
    scientific_recomputation_calls=0,source_protocol_changed=False,scope='Saved actual terminal production documentation only'),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=progress['status'],cases=case_rows,scientific_recomputation_calls=0)))
