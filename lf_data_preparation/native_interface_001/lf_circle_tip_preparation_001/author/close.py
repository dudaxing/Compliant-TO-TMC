"""Close tip-facing input preparation from ordinary records, seals and stat."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001'
BASE='48c16edf92de67643b253a5005720782d6fcad10'
FRONTS=['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/PHYSICAL_FUNCTION_PROGRESS.md',
        'docs/RESUME_DEVELOPMENT.md','docs/L_USE1_NEXT_STEP_PLAN.md','docs/L_BFWD1_NEXT_STEP_PLAN.md']


def read(name,optional=False):
    path=ROOT/REL/name
    return {} if optional and not path.is_file() else json.loads(path.read_bytes())


def put(name,value):
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False) if isinstance(value,dict) else value
    (ROOT/REL/name).write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')


def main():
    protocol,launch=read('protocol.json'),read('preparation_launch.json')
    receipt,diag,layout=read('run_001/execution_receipt.json',True),read('run_001/diagnostics.json',True),read('run_001/layout.json',True)
    review,pixel=read('author/ACTUAL_REVIEW.json'),read('author/pixel_QA.json',True)
    assert protocol['card']==launch['card']=='L-CTIPPREP1' and protocol['source_baseline_commit']==BASE
    assert launch['invocations']==1 and launch['cleanup_verified'] is True
    assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
    assert not receipt or receipt['protocol_sha256']==launch['protocol_sha256']
    outcome='pass' if launch['status']==receipt.get('status')=='pass' else 'not_pass'
    a,b=layout.get('baseline',{}),layout.get('candidate',{})
    historical=layout.get('historical_geometry_margin',{})
    right=b.get('right_medium',{})
    relation=b.get('distance_relation',{})
    nearest=lambda item:item.get('boundary',{}).get('minimum_boundary_distance_mm')
    tip=lambda item:item.get('tip',{}).get('distance_mm')
    seals=receipt.get('outputs',{})
    for name,row in seals.items():assert (ROOT/name).stat().st_size==row['bytes'],name
    calls={key:receipt.get(key) for key in ('tests','force_calls','tangent_calls','HP_calls','solver_calls','default_installations')}
    if outcome=='pass':
        assert diag['status']=='pass' and all(diag['checks'].values())
        assert receipt['checks_completed']==receipt['checks_passed']==len(diag['checks'])
        assert all(value==1 for value in receipt['counts'].values()) and len(receipt['counts'])==10
        assert all(value==0 for value in calls.values())
        assert pixel.get('card')=='L-CTIPPREP1' and pixel['status'].startswith('pass') and pixel['inspections']==1
        assert pixel['media']==[dict(path=REL+'/run_001/tip_prepared.png',inspections=1)]
        assert REL+'/run_001/tip_prepared.png' in seals
    next_step=('根据已通过的新92mm域与r9/(80,40)输入，另行安排一次零起点load_only[0,.25,.5]mm短试算及实际变形/反力/收敛/右介质显示；不预设tip唯一先触或域宽充分。' if outcome=='pass' else
        '先从已保存普通错误记录定位首个终端错误；不重试本窗口，也不开始短程求解。')
    closure=dict(card='L-CTIPPREP1',status=outcome+'_closed',execution_status=outcome,execution_closed=True,
        created_utc=datetime.now(timezone.utc).isoformat(),source_baseline_commit=BASE,protocol_sha256=launch['protocol_sha256'],
        terminal=review.get('terminal'),checks_completed=receipt.get('checks_completed'),checks_passed=receipt.get('checks_passed'),
        execution_counts=receipt.get('counts'),model_counts=diag.get('counts'),calls=calls,
        helper_elapsed_seconds=receipt.get('elapsed_seconds'),outer_elapsed_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),cleanup_verified=True,
        geometry=diag.get('derived_geometry_descriptor',{}).get('geometry_id'),
        historical_margin=historical,candidate_right_medium=right,
        comparison=dict(old_center_mm=[74,40],new_center_mm=[80,40],radius_mm=9,
            baseline_nearest_mm=nearest(a),baseline_tip_mm=tip(a),candidate_nearest_mm=nearest(b),candidate_tip_mm=tip(b),
            candidate_distance_relation=relation),
        inherited_production_gates=protocol['inherited_production_gates'],production_gates_executed=False,
        target_execution=False,mechanical_qualification=False,boundary_width_convergence=False,
        sealed_output_files=len(seals),sealed_output_bytes=sum(row['bytes'] for row in seals.values()),output_identity_seal=receipt.get('output_identity_seal'),
        actual_review_status=review['status'],pixel_QA_status=pixel.get('status'),next_step=next_step,
        closure_read_scope='Ordinary records plus producer seals/stat only; no scientific/media payload hash/decode or regeneration.')
    checks=f"{receipt.get('checks_passed')}/{receipt.get('checks_completed')}"
    counts=diag.get('counts',{})
    results=f'''# L-CTIPPREP1：圆底面向最右尖端的92mm域准备

本轮 **{outcome.upper()}**，{checks}项检查。只准备输入、构造参考模型及未变形图，未执行加载。默认HF力核、切线及控制器无修改。

## 目标、依据与实现

整体目标是用独立HF第三介质分析器接收LF结构，逐步验证大变形接触、位移/反力和加载/卸载。前一r9/(74,40)、84mm域短程通过，但.5mm时整体最近处仍在x76横梁、tip距仍2.039mm，右介质也参与压缩。因此本轮先把圆底对向最右tip，并扩出明确的右侧介质空间，再决定下一次计算。

本轮圆心从(74,40)改到(80,40)mm、半径9mm；参考域右界84→92mm。调用现有write_right_medium_geometry一次，在旧84mm子域右侧新增16列h.5、共1280介质单元；旧168列四掩码按field身份逐一保持，新列仅passive_void为1，其余为0。原LF机构右端80mm；全92mm网格为HF派生分析域，未重采样、未新做LF优化。

复用原build_native_project/write_native_project各一次，绑定实际新geometry身份；旧模型仅读取普通descriptor核语义，不读取其数组或保存态。节点stride169→185后，原坐标/连接/实体分类、支撑/实体对称与端口的节点、方向、权重、vector均按物理位置映射核对。tip由唯一参考坐标(80,30)重查并核solid/output节点，未沿用旧编号10300。

E1MPa、nu.3、plane strain、厚20mm、gamma1e-6、alpha5e-7、h.5及正则化物理长度Lr80mm保持，原材料常数/kr逐值核对。全域顶部只施加uy对称至92mm；右边界ux和非顶uy保持自由类型。新task改变center_x、背景顶端、新几何绑定及四说明metadata；load_only[0,.25,.5]/input.5仍只是保存的未执行指令。原生产门/settings/options原值记录，本轮未运行这些力学门。

![未变形圆底对向与右侧介质](run_001/tip_prepared.png)

## 实际几何与约束结果

| 同定义的未变形量 | 旧圆心74 | 新圆心80 |
|---|---:|---:|
| 全机构到实际Q1边最近距离 mm | {nearest(a)} | {nearest(b)} |
| 固定参考tip(80,30)到实际Q1边距离 mm | {tip(a)} | {tip(b)} |
| 工件覆盖单元/节点 | {a.get('counts',{}).get('cells')}/{a.get('counts',{}).get('nodes')} | {b.get('counts',{}).get('cells')}/{b.get('counts',{}).get('nodes')} |

两圆仅用同一新92mm驻留网格重建几何，没有构造第二个旧84mm有限元模型或重算旧反力。历史旧74/84域的右介质宽为{historical.get('width_mm')}mm；新80/92候选的实际宽为{right.get('width_mm')}mm。不能把圆心74放入92域的假想9mm余量当作旧结果。

新tip节点信息见[诊断](run_001/diagnostics.json)；tip/整体距离关系原值：`{relation}`。原public函数返回一个最近见证，不穷举全部正距离并列对；tip自身的精确并列边保留。若两距离精确相同，只能说明指定tip进入最短距离层级，不能据此断言唯一最先接触、加载后一定先触或有效夹持。实际边界是Q1阶梯，解析圆只作参考。

工件实际右端x={right.get('actual_body_right_mm')}mm，新外界x={right.get('outer_right_mm')}mm；{right.get('column_count')}列×{right.get('row_count')}行={right.get('cell_count')}个完整非实体、非工件介质单元连续到外界。所谓自由介质是单元分类，不表示相接工件节点或顶部uy也自由；x92逐节点ux/非顶uy自由和原顶uy对称另行核对。3mm余量与完整介质存在不证明域宽已收敛。

实际模型计数：{counts}。完整body、边、节点、DOF、距离见证及右介质逐项见[layout](run_001/layout.json)。制造阈值pending与原资格保持。

## 执行、效果与后续

helper {receipt.get('elapsed_seconds')}秒／180，outer {launch.get('elapsed_seconds')}秒／240，进程树采样峰值{launch.get('peak_sampled_tree_RSS_bytes')}B／64GiB，四库各16线程配置、清理确认true；不是声称实际用满16核。实际调用计数{calls}；参考构模可导入/注册JAX，不声称全局动态机械hook或零依赖导入。原窗口封存{len(seals)}文件/{closure['sealed_output_bytes']}B，后续仅继承seal并核stat。

本轮效果是把位置/域变化转为明确的新HF输入，并实际核查tip对向、右介质及全部关键语义；没有生成变形、反力或收敛结果。独立源审、实际普通记录审阅和一次新PNG像素检查均已留档；像素状态`{pixel.get('status')}`。

下一步：{next_step} 本轮不启动短程、HP或更大行程，不升级压力、有效夹持、释放、稳定性、完整路径或HF5资格。

[人工检查页](run_001/REVIEW.md) · [布局](run_001/layout.json) · [检查](run_001/diagnostics.json) · [新任务](run_001/task.json) · [新几何](run_001/derived_geometry/geometry.json) · [模型](run_001/model/model.json) · [helper](run_001/execution_receipt.json) · [outer](preparation_launch.json) · [闭卡](author/closure.json) · [后续计划](NEXT_STEPS.md)
'''
    plan=f'''# L-CTIPPREP1后的功能计划

本轮实际未变形检查{outcome.upper()}；{next_step}

若准备通过，建议下一L-CTIPPILOT1复用新derived_geometry/task与现evaluate_native，从零执行[0,.25,.5]mm；半径9、圆心(80,40)、92×40mm域、Lr80及其余物理保持。原残差1e-9、平均约束1e-10、全局力平衡1e-6、固定位移8e-11mm门和非clock设置继续逐值保持。

配套显示实际×1变形/全部N接受态动画、输入反力、工件有符号材料/Hu/总力、同reference tip与最近边界见证、全Newton/回溯/二分历史及右侧6列介质J/Hu/Green应变。几何编号须按新stride动态查；显示代码不得沿用旧x83..84两列/160cell观察器，也不得沿用旧tip ID。优先把已有viewer中的域/strip选择改为依据新模型的真实定义，并复用同一驻留保存数组，保原纯显示/读集及无新增力学调用原则。

建议试算资源controller1800、显示共享600、helper2700/outer2760秒，采样64GiB、四库16，原viewer内部8GiB；候选有限静审冻结后唯一执行，首错停、保partial、无外部重试/修复重跑/延期/force，新HP或默认源码改动不包含。具体读取/图表/资源在新卡明确后执行；当前准备窗口已关闭，本页不启动新计算。

依据真实接近位置、接触/重叠观察、分区J、右介质与收敛，再确定进一步单目标加载或排查。圆底对向tip不预授tip首触、有效夹持、压力或域宽充分性。当前历史74/84路径及全部旧结果/资格保留。
'''
    if outcome!='pass':
        diagnostic_link=('[诊断](run_001/diagnostics.json) · ' if (ROOT/REL/'run_001/diagnostics.json').is_file() else '')
        results=f'''# L-CTIPPREP1：NOT_PASS实际记录

唯一窗口已关闭，首个终端错误保留；完成检查{checks}，输出封存{len(seals)}个/{closure['sealed_output_bytes']}B。实际错误：{receipt.get('error',launch.get('error'))}。新布局r9/(80,40)、右域92及Lr80是本轮目标，只有实际完成的部分可用，不能预授几何或媒体通过。未执行短程或重试。

{diagnostic_link}[outer](preparation_launch.json) · [闭卡](author/closure.json)。缺失字段/产物保持缺失，不补造模型、图或结果。下一步：{next_step}
'''
        plan='# L-CTIPPREP1后续\n\n'+next_step+'\n'
    old_fronts={name:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',BASE+':'+name],cwd=ROOT) for name in FRONTS}
    assert all((ROOT/name).read_bytes()==old for name,old in old_fronts.items())
    put('RESULTS.md',results);put('NEXT_STEPS.md',plan);put('author/closure.json',closure)
    history=dict(source_baseline_commit=BASE,files=[])
    for name,old in old_fronts.items():
        link=os.path.relpath(ROOT/REL/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        prefix=(f'> 2026-10-18 L-CTIPPREP1 **{outcome.upper()}**：r9/(80,40)、右域84→92mm、Lr80输入与未变形检查{checks}；无加载。见[tip对向及右介质记录]({link})。原历史正文保留如下。\n\n').encode('utf-8')
        (ROOT/name).write_bytes(prefix+old)
        current=(ROOT/name).read_bytes();assert current.endswith(old) and current.count(old)==1
        history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    put('author/front_history.json',history)
    for name in ('close.py','publish.py','archive_publication.py'):(ROOT/REL/'author'/name).write_bytes((AUTHOR/name).read_bytes())
    print(json.dumps(dict(status='closed',execution_status=outcome,checks=checks,outputs=len(seals),fronts=len(FRONTS))))


if __name__=='__main__':main()
