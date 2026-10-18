"""Close right-circle preparation using ordinary records; no scientific payload reads."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
STAGE='lf_data_preparation/native_interface_001/lf_circle_right_preparation_001'
BASE='e509330e5db82eced1b92a20dda02a24fb3e3ae6'
FRONTS=['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/PHYSICAL_FUNCTION_PROGRESS.md',
        'docs/RESUME_DEVELOPMENT.md','docs/L_USE1_NEXT_STEP_PLAN.md','docs/L_BFWD1_NEXT_STEP_PLAN.md']
read=lambda name:json.loads((ROOT/STAGE/name).read_bytes())


def put(name,value):
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False) if isinstance(value,dict) else value
    (ROOT/STAGE/name).write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')


def main():
    receipt,launch,diag=map(read,('run_001/execution_receipt.json','preparation_launch.json','run_001/diagnostics.json'))
    review=read('author/ACTUAL_REVIEW.json')
    pixel=read('author/pixel_QA.json') if (ROOT/STAGE/'author/pixel_QA.json').is_file() else dict(status='not_produced',note='No completed pixel inspection.')
    assert receipt['card']==launch['card']=='L-CRIGHT1'
    assert launch['invocations']==1 and launch['cleanup_verified'] is True
    assert review['status'].startswith('pass') and not review.get('blocking_findings',[])
    assert receipt['protocol_sha256']==launch['protocol_sha256']
    assert receipt['status'] in ('pass','not_pass') and launch['status'] in ('pass','not_pass')
    outcome='pass' if receipt['status']==launch['status']=='pass' else 'not_pass'
    layout=read('run_001/layout.json') if (ROOT/STAGE/'run_001/layout.json').exists() else {}
    a,b=layout.get('baseline',{}),layout.get('candidate',{})
    nearest=lambda item:item.get('boundary',{}).get('minimum_boundary_distance_mm')
    tip=lambda item:item.get('tip',{}).get('distance_mm')
    right=lambda item:item.get('right_medium',{})
    counts=diag.get('counts',{})
    calls={k:receipt.get(k) for k in ('tests','force_calls','tangent_calls','HP_calls','solver_calls','default_installations')}
    seals=receipt.get('outputs',{})
    for name,row in seals.items():
        assert (ROOT/name).stat().st_size==row['bytes'],name
    if outcome=='pass':
        assert diag['status']=='pass' and all(diag['checks'].values())
        assert receipt['checks_completed']==receipt['checks_passed']==len(diag['checks'])
        assert all(receipt['counts'][name]==1 for name in ('model_build_started','model_build_completed','model_write_started','model_write_completed','layout_analysis_started','layout_analysis_completed','plot_calls_started','plot_calls_completed'))
        assert all(value==0 for value in calls.values())
        assert STAGE+'/run_001/right_prepared.png' in seals
        assert pixel.get('card')=='L-CRIGHT1' and pixel['status'].startswith('pass') and pixel['inspections']==1
    old_fronts={name:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show',BASE+':'+name],cwd=ROOT) for name in FRONTS}
    assert all((ROOT/name).read_bytes()==old for name,old in old_fronts.items())
    closure=dict(card='L-CRIGHT1',status=outcome+'_closed',execution_status=outcome,execution_closed=True,
        source_baseline_commit=BASE,protocol_sha256=receipt['protocol_sha256'],
        created_utc=datetime.now(timezone.utc).isoformat(),checks_completed=receipt.get('checks_completed'),checks_passed=receipt.get('checks_passed'),
        helper_seconds=receipt.get('elapsed_seconds'),outer_seconds=launch.get('elapsed_seconds'),
        peak_sampled_tree_RSS_bytes=launch.get('peak_sampled_tree_RSS_bytes'),cleanup_verified=True,
        terminal=review.get('terminal'),calls=calls,counts=counts,execution_counts=receipt.get('counts'),
        comparison=dict(baseline_center_mm=[71,40],candidate_center_mm=[74,40],radius_mm=9,
            baseline_nearest_mm=nearest(a),candidate_nearest_mm=nearest(b),baseline_tip_mm=tip(a),candidate_tip_mm=tip(b),
            baseline_right_medium_width_mm=right(a).get('width_mm'),candidate_right_medium_width_mm=right(b).get('width_mm'),
            candidate_right_medium_columns=right(b).get('column_count'),candidate_right_medium_cells=right(b).get('cell_count')),
        sealed_output_files=len(seals),sealed_output_bytes=sum(row['bytes'] for row in seals.values()),
        output_identity_seal=receipt.get('output_identity_seal'),actual_review_status=review['status'],pixel_QA_status=pixel['status'],
        target_execution=False,mechanical_qualification=False,boundary_width_convergence=False,
        closure_read_scope='Ordinary records only; original scientific/media seals plus stat. No payload hash/decode or re-render.')
    success=outcome=='pass'
    next_step=('Prepare a separately authorized zero-start load_only [0,.25,.5] mm pilot and circle-aware resident saved-state views; preserve r9/(74,40), all other physics, settings and original production gates.' if success else
               'Investigate the recorded first terminal error from ordinary records; do not start a pilot or rerun the closed preparation.')
    closure['next_step']=next_step
    checks=f"{receipt.get('checks_passed')}/{receipt.get('checks_completed')}"
    results=f'''# L-CRIGHT1：圆形工件右移与未变形兼容性

实际执行 **{outcome.upper()}**，几何/约束检查 {checks}；一次模型构建、保存和一张未变形图的实际计数见运行回执。科学窗口已关闭。本轮没有加载、变形或反力结果。

## 整体目标与本轮目的

整体目标是建立与LF求解断开的独立HF第三介质接触分析器：接收LF结构，求大变形加载/卸载，报告位移、反力和工件作用，并以独立参考和可视化验证。此前完成原wave圆形工件r9/(71,40)的分段加载至1.40mm及输入回零，记录历史收敛和变形；这不授压力、有效夹持、自由释放、稳定性或HF5资格。

本轮针对“工件应面向最右尖端”的物理需求，将圆心x从71移到74mm，检查该变化是否在原分析域内、与原机构/端口/支撑分离，且保有右侧第三介质。其余条件逐值保持，未尝试用更大行程弥补布置。原17目标ordered_cycle/input1.4在新task中只作未执行指令，旧结果原样保留。

## 实现与检查

复用现有build_native_project/write_native_project，各一次；不改默认HF源码。不读取旧模型/保存态，只在新唯一窗口读取原wave geometry.npz。对照圆由同一驻留网格、连接及原选择规则重建，不构建第二模型。检查四掩码、坐标/连接、工件原passive_void覆盖、固定与自由DOF、端口/权重、原背景对称和源身份。

保持h0.5mm、84×40mm下半HF域、厚20mm、E1MPa、nu0.3、plane strain、gamma1e-6、alpha5e-7、Lr80mm、输入+x/输出+y、原支撑与顶部uy背景对称、固定圆形工件ux/uy。80mm是原LF右界及参考尖端x；HF右界实际为84mm。半径9mm、y40保持。

![同尺度未变形布置及右侧介质](run_001/right_prepared.png)

| 同一定义的未变形量 | 原圆心(71,40) | 新圆心(74,40) |
|---|---:|---:|
| 整个机构到实际Q1边的最近距离 mm | {nearest(a)} | {nearest(b)} |
| 同一参考尖端(80,30)到实际Q1边距离 mm | {tip(a)} | {tip(b)} |
| 工件实际右端到HF右界的介质宽 mm | {right(a).get('width_mm')} | {right(b).get('width_mm')} |
| 工件单元/节点 | {a.get('counts',{}).get('cells')}/{a.get('counts',{}).get('nodes')} | {b.get('counts',{}).get('cells')}/{b.get('counts',{}).get('nodes')} |

距离采用真实Q1阶梯有限边，不拟合解析圆；最近距离与固定尖端距离均为无符号几何量，不是接触起点、压力或夹持力。见证端点、边号、全部body索引和固定参考tip节点在layout.json。解析圆仅作为虚线参考。

本轮右移缩短了尖端距离，但全机构最近距离没有缩短：原最近见证{a.get('boundary',{}).get('closest_pair',{}).get('mechanism_point_mm')}→{a.get('boundary',{}).get('closest_pair',{}).get('workpiece_point_mm')}mm，新见证{b.get('boundary',{}).get('closest_pair',{}).get('mechanism_point_mm')}→{b.get('boundary',{}).get('closest_pair',{}).get('workpiece_point_mm')}mm。因此“更面向最右尖端”有几何依据，仍不能预设尖端将先接触；应在短试算中追踪实际最近位置及同一尖端。

候选右端实际x={right(b).get('actual_body_right_mm')}mm，HF右界x={right(b).get('outer_right_mm')}mm，保留{right(b).get('column_count')}个完整0.5mm列×{right(b).get('row_count')}行，共{right(b).get('cell_count')}个原passive_void非实体、非工件介质单元，连续到域右界。x84各节点ux自由；除原y40顶角uy对称外，右边界uy自由。没有新增右侧夹固。介质条带存在不代表1mm域余量已足够或域宽收敛，后续需观察其变形与受力影响。

“自由介质”在这里仅指非实体、未被工件单元覆盖的原介质；与工件相接的x83节点仍承受原工件固定约束，不能理解为条带所有节点DOF都自由。外边界x84的逐节点约束检查已单独列出。

模型实际计数：{counts}。工件只是原介质上的固定运动学覆盖，不改源材料掩码。制造资格与机械资格遵循原声明。

## 实际执行、记录与效果

helper {receipt.get('elapsed_seconds')}秒，outer {launch.get('elapsed_seconds')}秒，进程树采样峰值{launch.get('peak_sampled_tree_RSS_bytes')}B，清理确认true；上限180/240秒、64GiB、四库各16线程。调用记录{calls}；依赖可导入或注册JAX，零力学结论依据冻结调用路径，不声称全局动态hook。原窗口封存{len(seals)}输出/{closure['sealed_output_bytes']}B；此后科学/媒体身份只继承seal并核stat。

本轮效果是把右移布置变成明确、可恢复的HF输入，并核清84mm域和右侧介质，给短试算提供几何依据；不预报接触后夹持效果。独立源审、实际普通记录审阅及一次新PNG像素检查均记录在author目录。{pixel.get('note','')}

## 下一步与审查入口

{next_step}

后续若开展短试算，应使用显式新load_only任务，不执行本轮保存的1.40mm长路径；重点显示真实×1变形、同一tip/最近距离、输入反力及工件总/材料/Hu有符号力、J/Hu位置、右侧介质及实际solver history。保持原生产门，首个终端错误停止，依据真实结果决定继续或排查。本轮不新增HP，也不自动继承旧布置的参考资格。

[人工检查页](run_001/REVIEW.md) · [布局与距离见证](run_001/layout.json) · [全部检查](run_001/diagnostics.json) · [新任务](run_001/task.json) · [模型描述](run_001/model/model.json) · [执行回执](run_001/execution_receipt.json) · [外层记录](preparation_launch.json) · [闭卡](author/closure.json) · [后续计划](NEXT_STEPS.md)
'''
    plan=f'''# L-CRIGHT1后的功能计划

当前未变形检查：{outcome.upper()}。{next_step}

1. 短行程若获授权，创建明确新task：load_only，[0,0.25,0.50]mm，input.target0.50，独立身份；仅这些路径/说明字段区别于本轮保存的原17目标任务，r9/(74,40)及其余物理条件保持。默认HF入口和圆形保存态显示已具备，优先复用，不安装新力核或切线。
2. 一次从零使用现有evaluate_native及原数值门。沿用原非clock设置：残差1e-9、平均约束1e-10、全局力平衡1e-6、固定位移8e-11mm；候选资源controller1800、显示600、helper2700/outer2760秒、采样64GiB、四库16，原viewer内部8GiB保留。内部原回溯/二分允许；首个终端错误停止，保真实partial，无外部重试/修复重跑/延期/force。此处是计划，没有打开新计算窗口。
3. 成功后一次保存态显示：实际×1变形/动画、输入反力与工件有符号总力和材料/Hu分量、最近及同tip距离、收敛图；显示新布置与未变形参考，检查右侧1mm介质条带和x84边界附近J/Hu。不得将工件节点反力或Hu主导总力直接认定为表面压力或有效夹持。
4. 依据实际变形、J、反力/方向、右侧介质和收敛，再决定继续到0.75、调整域宽或定位异常。不预设必须接触，不因短程未接触而放宽门或盲目加行程。此新布置需自己的保存态参考，旧圆心71的HP不转授；只在具体不确定性需要时安排HP。

本轮已完成记录与未变形可视化；尚未启动任何短行程、独立参考或力学求解。整体项目尚未完成压力、有效夹持、自由释放、稳定性或HF5资格。
'''
    if not success:
        results=f'''# L-CRIGHT1：实际NOT_PASS记录

唯一窗口已经关闭；保留首个终端错误，不重试、不做短行程。目标是核清右移r9/(74,40)的未变形布置，原17目标/input1.4未执行，旧任务/结果保持。检查完成{checks}，已产生{len(seals)}个封存输出；几何/右侧介质/图像是否完成只看实际记录，不授通过资格。

错误：{receipt.get('error',launch.get('error'))}。实际调用计数{calls}，helper{receipt.get('elapsed_seconds')}秒、outer{launch.get('elapsed_seconds')}秒，清理true。{pixel.get('note','')}

[实际诊断](run_001/diagnostics.json) · [运行回执](run_001/execution_receipt.json) · [外层记录](preparation_launch.json) · [闭卡](author/closure.json)。布局、模型、图与人工页仅在原窗口实际产生时存在，不生成替代数据。下一步：{next_step}
'''
        plan='# L-CRIGHT1后续\n\n'+next_step+'\n\n本轮NOT_PASS保留；不开始短行程。\n'
    put('RESULTS.md',results)
    put('NEXT_STEPS.md',plan)
    put('author/closure.json',closure)
    history=dict(source_baseline_commit=BASE,files=[])
    for name,old in old_fronts.items():
        link=os.path.relpath(ROOT/STAGE/'RESULTS.md',(ROOT/name).parent).replace('\\','/')
        observation='已核实际84mm域、右侧1mm两列介质与原约束。' if success else '首个终端错误已保留，几何通过与媒体情况按实际记录。'
        prefix=(f'> 2026-10-18 L-CRIGHT1 **{outcome.upper()}**：圆形工件r9从(71,40)右移至(74,40)mm，未变形检查{checks}；{observation}无力学求解，短行程尚未执行。见[实际记录]({link})。历史原文保留如下。\n\n').encode('utf-8')
        (ROOT/name).write_bytes(prefix+old)
        current=(ROOT/name).read_bytes()
        assert current.endswith(old) and current.count(old)==1
        history['files'].append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),prefix_bytes=len(prefix),raw_suffix_preserved_once=True))
    put('author/front_history.json',history)
    for name in ('close.py','publish.py','archive_publication.py'):
        (ROOT/STAGE/'author'/name).write_bytes((AUTHOR/name).read_bytes())
    print(json.dumps(dict(status='closed',outcome=outcome,checks=checks,fronts=len(FRONTS),outputs=len(seals))))


if __name__=='__main__':
    main()
