"""Record actual physical observations and the next unexecuted circle reference plan."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/lf_circle_step_002'
p = STAGE/'author/closure.json'
closure = json.loads(p.read_bytes())
assert closure['status']=='pass_closed' and closure['execution_status']=='pass'
last = closure['last_saved_state']
assert last['d_mm']==1.15 and last['index']==1 and last['original_target_index']==5
body = last['workpiece']['force_on_lower_body_N']
fraction = body['regularization'][1]/body['total'][1]
next_text = ('建议下一阶段L-CREF1只对本次1.15 mm圆形新峰值做独立数值参考：'
    'accepted1/global5，HP80/120各一次，保持既有十五门和全部13440单元/27378DOF。'
    '这是首次圆形路径的较强第三介质压缩态（minJ0.225154、Hu约81.4%弱Fy），'
    '先核对保存模型的数值一致性，再据结果决定继续加载。新参考不授圆周压力、有效夹持或完整路径资格。'
    '该阶段仅为未执行计划，需新卡、新授权和独立资源窗口。')
decision = dict(proposed_stage='L-CREF1',status='proposed_not_executed',
    source_result='lf_data_preparation/native_interface_001/lf_circle_step_002/run_001/wave_circle_step/result.json',
    selected_accepted_index=1,selected_global_target_index=5,selected_d_mm=1.15,
    state_sha256=last['state_sha256'],new_HP80_calls=1,new_HP120_calls=1,
    information_gain='First selected-state independent reference on the saved circular-workpiece path, now at stronger medium compression; not a routine all-state repeat.',
    scope='Saved circular model numerical reference, whole mesh/DOF and original fifteen gates; body forces are signed global-axis weak resultants.',
    not_in_scope='New production F/T or equilibrium, complete path/reference, independent geometric mask qualification, surface pressure, effective grip, release or stability.',
    proposed_resources=dict(helper_seconds=900,outer_seconds=960,sampled_RSS_bytes=8*1024**3),
    existing_generic_core='lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference_author/core_audit_mechanical.py::Audit.run_state',
    existing_projection='hf_repo/scripts/audit_native_workpiece_cycle.py::WorkpieceCycleAudit.workpiece_checks',
    wrapper_template='lf_data_preparation/native_interface_001/extension_reference_001/execute_extension_reference.py',
    adaptation_required='Bind S2 load_only source chain and selected1/global5, receipt/schema, circle and saved overlay. Do not inherit WorkpieceCycleAudit.load(), which hardcodes a square selection.',
    geometry_evidence='Inherit L-CPREP1 circle preparation; this proposal does not independently rebuild the circle mask or grant new geometric qualification.',
    outputs='Ordinary single-state numerical error summary and one reference-error PNG after original gates pass; no rerun of deformation views.',
    completion='All original gates and source identities pass; first error stops, no repair rerun/retry/extension/force.',
    observed_Hu_fraction_of_signed_lower_body_Fy=fraction)
closure.update(next_step=next_text,next_step_decision=decision,next_step_recorded_utc=datetime.now(timezone.utc).isoformat())
p.write_text(json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
results_path = STAGE/'RESULTS.md'
results = results_path.read_text(encoding='utf-8')
overview = '''实际效果摘要：1.00→1.15 mm后，R由0.173350升至0.200224 N，q_out由0.966288升至1.111617 mm。最小实际Q1边界无符号距离由0.334737降至0.232258 mm；最右尖端距离仅由3.349195降至3.202515 mm，真正最近位置在圆下方横梁附近，不能把两者混称为尖端贴合。

自由介质minJ由0.329300降至0.225154，solid minJ由0.975949降至0.972384；全部原门通过。下半工件Fy=0.001487188 N，其中材料0.000276164 N、Hu0.001211025 N（约81.4%）。它是有符号全局y弱式传力，不是圆周总法向压力或合格夹持力。相交/近触/跨区域重叠/数值不确定观察均为False；完整包含和机构自重叠未检查，不能从False扩大解释。

收敛与成本：锚点1检查、新目标6检查，合计7；5次线搜索全部接受，0失败、0二分，F12/T7、一次求解。实际含显示449.90秒（约7分30秒），进程树采样峰值831434752 B，清理通过。4PNG与2帧实际变形GIF齐全。原收敛图外侧图例仍遮挡右面板标题的一部分，数据及两条约束界可见，保留原图未重绘。

'''
position = results.index('整体目标仍是')
results = results[:position]+overview+results[position:]
start = results.index('下一步：')
end = results.index('\n\n审查入口：',start)
results = results[:start]+'下一步：'+next_text+' 具体计划及复用边界见[NEXT_STEPS.md](NEXT_STEPS.md)。'+results[end:]
results_path.write_text(results,encoding='utf-8',newline='\n')
plan = '''# L-CSTEP2结果驱动的下一步

本轮1.00→1.15 mm子段、原门、显示及清理均PASS；7检查/5接受线搜索/0失败/0二分。默认HF未修改；新测试、HP、安装均0。原父结果及完整路径尚未从零执行的事实保持。

''' + next_text + '''

## 最近一个拟定阶段：L-CREF1

1. 来源：仅本轮wave_circle_step/result.json中accepted1/global5、loading1.15 mm，按原state SHA、保存模型/任务/工件overlay和producer seal绑定，不能使用旧方体同值态或continuation里的1.00 mm祖锚。
2. 最小计算：HP80/120各一次，覆盖全部13440单元/27378DOF、材料/Hu/总力、逐元及全局同一PORT方向切线、CSC全系数组装身份、KKT与工件/支撑弱式力投影。保留原十五门；不是全部切线列、应力、能量或压力资格。
3. 复用边界：通用core_audit_mechanical.py::Audit.run_state与workpiece_checks按实际数组/DOF计算，可处理保存圆形模型。单态模板extension_reference_001/execute_extension_reference.py仍需更新本次load_only、父链、receipt字段、索引与circle/overlay绑定；不能直接执行旧包装，尤其不能继承硬编码square的WorkpieceCycleAudit.load()。L-CPREP1圆形准备证据可继承，本卡不新增独立圆mask/边界重建资格。
4. 原门：production residual1e-9/independent1e-8、force_eval1e-9、constraint1e-10、global balance1e-6、fixed8e-11 mm、HP80/120一致1e-40；材料/Hu/总力相应1e-9/1e-9/1e-11、三切线方向相应1e-9/1e-9/1e-10、KKT force/mean各1e-10。最终可执行卡必须与原实现逐项核对，不能在包装中放宽门。
5. 输出：全部通过后生成单态误差普通JSON及一张误差PNG，最多一次像素检查；不重算加载路径或变形图。工件legacy normal字段若出现，解释为全局y投影，不认定为圆周局部法向压力。
6. 拟用helper900秒/outer960秒、采样8 GiB；单次、首错停止、无修复重跑/重试/延期/force。不新增生产F/T或平衡求解。以上仅为拟定范围，需要新候选静审和新授权，本轮不执行HP。

## 后续能力依赖

参考通过后，再据真实几何、介质压缩、材料/Hu弱式力和收敛成本选择下一加载目标或参数诊断；更远目标暂不锁定。接触相关指标定义与压力/有效夹持验证仍需完成，随后才能安排有解释依据的圆形卸载及同定义设计比较。正式批量标签/排名、稳定性、释放、制造及HF5均不因本轮子段成功而取得资格。

审查：[实际结果](RESULTS.md)、[原值人工页](run_001/REVIEW.md)、[闭卡及计划来源](author/closure.json)、[已安装接口用法](../lf_circle_extension_001/USAGE.md)。
'''
(STAGE/'NEXT_STEPS.md').write_text(plan,encoding='utf-8',newline='\n')
target=STAGE/'author/record_next_plan.py'
assert not target.exists()
shutil.copyfile(Path(__file__),target)
print(json.dumps(dict(status='recorded_proposed_not_executed',next_stage='L-CREF1',selected_d_mm=1.15,Hu_Fy_fraction=fraction)))
