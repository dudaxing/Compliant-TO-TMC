"""Record the selected next target from new ordinary results; no mechanics."""
import json
from pathlib import Path
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE=ROOT/'lf_data_preparation/native_interface_001/lf_circle_extension_001'
closure=json.loads((STAGE/'author/closure.json').read_bytes())
assert closure['execution_status']=='pass'
last=closure['last_saved_state']['view_observation']
assert last['d_mm']==.75 and last['boundary_intersects'] is False and last['raw_overlap'] is False
next_step='建议复用已安装load_only延伸接口，从成功child末态0.75 mm显式追加1.00 mm，沿用已两次成功的0.25 mm增量；保持r9/c(71,40)、其余物理和原数值门，复核锚点并显示实际变形、反力、材料/Hu工件合力、距离、分区场和收敛。本轮只记录下一步，不开启新窗口。'
closure['next_step']=next_step
closure['next_plan_status']='proposal_only_not_executed'
(STAGE/'author/closure.json').write_text(json.dumps(closure,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
(STAGE/'NEXT_STEPS.md').write_text('''# L-CEXT1之后：圆形工件0.75→1.00 mm

2026-10-16。L-CEXT1已PASS并关闭。本页记录下一步方案，不执行新求解、绘图、HP、测试或默认安装。

## 已完成的功能及物理结果

默认HF现支持成功load_only任务的非零保存末态显式append；旧前缀、身份、数值设置和物理条件受原来源核对，新加载峰值明确声明。首次和再次延伸及原ordered_cycle兼容均已通过8方法有限验证，真实小模型为16单元/50DOF。用法与字段语义见[USAGE](USAGE.md)。这不是任意失败load_only中间态恢复功能。

真实圆形r9/c(71,40)任务从0.50 mm锚点通过1次新鲜F/T检查，状态SHA与R保持；新增0.75 mm通过7次Newton检查。本段14F/8T、6次线搜索全接受、无失败增量或二分；controller约481.9秒，outer502.4秒。新增峰值和子段完成为true，整条前缀重新执行及独参资格保持false。

|实际子段d mm|输入R N|q_out mm|Q1外缘无符号最小距离 mm|实体minJ|自由介质minJ|下半工件总Fy N|
|---:|---:|---:|---:|---:|---:|---:|
|0.50锚点|0.08574820985|0.4816680041|0.6718881791|0.9879384800|0.6701213508|0.0002414251944|
|0.75新增|0.1292605635|0.7237693004|0.5043741866|0.9819298733|0.5010970321|0.0004832937699|

末态右侧参考尖端距离3.59202623 mm，仍明显大于全局最近边界距离；最接近处位于圆形下部和夹持梁之间。未观察到边界相交、跨区域单元内部重叠或roundoff不确定，完整包含与机构自重叠未测试。工件Fy约翻倍，但其中材料约0.00009626059 N、Hu约0.0003870332 N；这是弱式合力分解，不能直接改称表面压力或有效夹持力。

## 下一次计算的选择

优先选0.75→1.00 mm单一新增目标。前两次0.25 mm增量均7次Newton检查、无回溯拒绝或二分，支持继续相同步长；当前介质压缩加深，应以实际J、Hu、接近位置和力变化逐段判断，不能外推闭合行程或宣称物理稳定。原内部二分仍可按原规则细分。

复用已安装evaluate_native及extend_path=True，不再改默认源码或重复本轮小模型验证。父源使用本次成功child/result.json与accepted1（global original3）的0.75 mm保存态；新完整task前缀为[0,.25,.50,.75,1.00] mm、input.target_mm=1.00，实际子段[.75,1.00]。四说明字段的显式更新列明，其余物理、非clock设置和原门保持。新锚点仍做fresh F/T和SHA/R复核，不读取旧force/tangent/matrix；父/祖先结果保持。

沿用圆形纯保存态显示及普通JSON收敛观察，显示实际N接受态、两套目标索引、锚点来源、全局有符号材料/Hu/总Fx/Fy、实际阶梯边界距离与分区J/Green/Hu，保留x1及镜像范围。当前约束图的图例遮住末态界标记的轻微问题已记录，后续新绘图可在冻结前调整图例位置；本轮没有重绘。

拟议资源：controller1800秒、显示共享600秒、helper2700/outer2760秒、采样8GiB，无重复测试或新HP；候选读集/运行包装静审冻结后再形成具体执行卡。首个终端错误停止，保存实际partial，不外部重试、修复重跑、延期或force。

1.00 mm后再依据实际几何接近、分区场、弱式力与收敛成本决定下一目标。TMC作用可在正边界距离下增长，不以等待几何相交作为接触判据。进入更强接近响应区间后，选择最有信息量的状态安排独立参考和力学解释；完整圆形卸载/释放、连续压力、有效夹持、稳定性与HF5仍属后续功能/资格。
''',encoding='utf-8',newline='\n')
results=STAGE/'RESULTS.md'
report=results.read_text(encoding='utf-8')
report='\n'.join('下一步：'+next_step if line.startswith('下一步：') else line for line in report.split('\n'))
results.write_text(report,encoding='utf-8',newline='\n')
with results.open('a',encoding='utf-8',newline='\n') as stream:
    stream.write('\n## 审阅后的具体下一步\n\n'+next_step+'\n\n当前原步长连续两段均7次Newton检查且无回溯拒绝，最终选择1.00 mm单一新目标，详见[下一步计划](NEXT_STEPS.md)。接口说明见[USAGE](USAGE.md)；它区分新峰值/子段完成与继承前缀，保守旧target_response=None不代表新峰值未达。\n')
print('Selected next1.00 mm proposal recorded; no new execution.')
