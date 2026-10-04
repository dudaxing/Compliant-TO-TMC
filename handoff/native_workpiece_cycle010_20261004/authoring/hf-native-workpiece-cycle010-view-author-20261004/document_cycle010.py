"""Write new delivery prose from actual saved receipts; preserve prior doc bytes."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
BASE = '07134ea6cd9aa0ab2de4bf97f80a8e8ca44c241e'
MECH = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010'
VIEW = ROOT/'functional_views/native_workpiece_cycle010_20261004'
HANDOFF = ROOT/'handoff/native_workpiece_cycle010_20261004'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
digest = lambda p: sha256(p.read_bytes()).hexdigest()

def write_new(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream: stream.write(content.encode('utf-8'))

def main():
    facts = read(AUTHOR/'root_delivery_facts.json')
    physics = read(AUTHOR/'saved_physics_comparison.json')
    result = read(MECH/'result/result.json')
    reference = read(MECH.with_name('coarse_square_cycle010_ref_003')/'reference/summary.json')
    assert result['status'] == 'success' and reference['status'] == 'pass'
    assert reference['accepted_states'] == 12 and reference['HP_calls_completed'] == 24
    assert all(r['launch']['status'] == ('not_pass' if r['phase']=='reference' and
        r['stage'].split('/')[-1] in ('coarse_square_cycle_010','coarse_square_cycle010_ref_002') else 'pass')
        for r in facts['phase_receipts'])
    rows = physics['new010']['rows']; peak,returned = rows[5],rows[11]
    numeric_table = '\n'.join('| '+ ' | '.join((str(r['accepted_index']),r['leg'],f"{r['d_mm']:g}",
        str(r['original_target_index']),str(r['bisection_depth']),f"{r['R_input_N']:.10g}",
        f"{r['q_out_mm']:.10g}",f"{r['J_min_all']:.10g}",
        f"{r['region']['faces']['bottom']['minimum_first_ray_hit_mm']:.10g}",
        f"{r['region']['faces']['left']['minimum_first_ray_hit_mm']:.10g}"))+' |' for r in rows)
    budgets = [('60 / 90',157),('900 / 960',230),('300 / 360',230),('60 / 90',327),
        ('300 / 360',331),('600 / 660',524),('120 / 150',951),('120 / 150',1289),
        ('120 / 150',1307),('120 / 150',1307),('120 / 150',1307)]
    cost_table = '\n'.join('| '+ ' | '.join((r['stage'].split('/')[-1]+'/'+r['phase'],r['launch']['status'],
        '—' if r['helper_elapsed_seconds'] is None else f"{r['helper_elapsed_seconds']:.9f}",
        f"{r['launch']['elapsed_seconds']:.9f}",str(r['launch']['peak_sampled_tree_RSS_bytes']),
        budget,str(pins)))+' |' for r,(budget,pins) in zip(facts['phase_receipts'],budgets))
    report = f'''# Cycle010：1.8 mm完整循环、参考计数修正和实际作用位置

## 整体目标与本轮目标

整体目标是实现独立 HF 非线性正向力学评估器：读取 LF 导出的普通几何数据，在明确的原生网格、材料、支承、平均位移端口和工件任务下，以 Third Medium Contact 求解加载与卸载，输出可追溯的位移、力、切线、平衡和接触相关诊断，供外部研究层比较。HF 不承担优化，不导入、安装或子进程调用 dmftd；本轮没有正式批量标签、排名或 MPM。

用户已授权探索对称方体、圆体及尺寸/位置/更大行程。本轮继承009的网格和固定方体，以小幅增加峰值到1.8 mm观察近接触变化，并保留完整卸载。目的是看功能的真实效果，不把测试数量当成开发完成度。

已完成完整路径、每个实际接受态的新参考核查、几何和全工件节点力观测，以及人工可检查的实际倍率图。整体HF项目仍未完成；有效夹持、压力及其它未实现能力见下文。

## 做了什么，为什么这样做

009在1.75 mm时底面首次法向射线仅0.07671066678990902 mm，非工件介质minJ=0.02808043969551585，节点力集中在右下角。此次保持同一物理模型和原数值门，只将原路径增加1.8 mm峰值及卸载1.75 mm观察点；没有直接跳到2或3 mm。

原请求11个目标：

`[0, .5, 1, 1.5, 1.75, 1.8, 1.75, 1.5, 1, .5, 0] mm`

实际12个接受态：

`[0, .5, 1, 1.5, 1.75, 1.8, 1.75, 1.5, 1, .5, .25, 0] mm`

额外.25 mm来自原控制器最后卸载步失败后的原规则二分，属于此次一次求解，不是另启生产或重试关闭卡。原11目标及次序全部完成，origin与return zero单独保存，没有去重、删点或拼接旧009前缀。

机械公式、默认响应/切线、原Armijo、KKT、25次检查、12次回溯、4层二分和最小增量0.00625 mm保持。生产900/960 s和参考资源在新协议中显式声明。生产从独立零状态开始，原27模型数组逐字节相同；前5个加载态的4种整档共20文件与009逐字节相同。

本轮新增的实现仅是保存轨迹的准确审计计数合同、独立参考的身份/资源包装及图示。HF核心未改变，几何与节点力API复用此前已通过的源码和39/5解析测试证据，没有重跑这些测试。

## 实际物理模型和效果

1 mm原生Q1网格，3200单元、3321节点、6642 DOF，固定376、自由6266。实体1086单元、非工件介质1986、工件128单元/153节点。固定16 mm方体中心(70,40) mm，只算对称下半，工件为[62,78]×[32,40] mm；底/左初始间隙2 mm。E=1 MPa、nu=.3、plane strain、厚度20 mm，gamma=alpha=1e−6、Lr=80 mm。三节点平均+x输入权重[.25,.5,.25]，自由三节点平均+y输出，输入/输出辅助弹簧为零。工件为固定运动学叠加，不是求解其自由刚体平衡。

| 量 | 1.8 mm峰态 index5 | 返回零 index11 |
|---|---:|---:|
| 输入反力R / N | {peak['R_input_N']!r} | {returned['R_input_N']!r} |
| 自由平均+y输出 / mm | {peak['q_out_mm']!r} | {returned['q_out_mm']!r} |
| 最大节点位移范数 / mm | {peak['maximum_node_displacement_mm']!r} | {returned['maximum_node_displacement_mm']!r} |
| 原机构实体minJ | {peak['J_min_mechanism_solid']['value']!r} | 1 |
| 非工件介质minJ | {peak['J_min_nonbody_medium']['value']!r} | 1 |
| 全域最大绝对Hu / mm⁻¹ | {peak['Hu_max_abs_all_per_mm']!r} | {returned['Hu_max_abs_all_per_mm']!r} |
| 底面有限外向首次射线 / mm | {peak['region']['faces']['bottom']['minimum_first_ray_hit_mm']!r} | 2 |
| 左面有限外向首次射线 / mm | {peak['region']['faces']['left']['minimum_first_ray_hit_mm']!r} | 2 |
| 保存生产相对残量 | {peak['production_relative_residual']!r} | {returned['production_relative_residual']!r} |

相对009峰态，输入反力增加4.40%、输出增加2.24%，但介质minJ下降76.42%、底法向射线缩短58.56%。仅0.05 mm输入增量已使局部介质压缩很强；实体minJ仍约.95525。这是下一步不继续盲增方体行程的实际依据，不以J推断压力或夹持。

底面最短射线在工件右底角(78,32) mm，机构点(78,31.968209028446413) mm；左面见证从(62,32)到(59.146569427192844,32) mm。封闭区域最短无符号边界距为0.03164386665647688 mm；旧节点窗口bottom/left代理为0.11601410729835138/2.8565891753758876 mm。这三种量不同，节点窗口值不是表面间隙，正距离不是有符号穿透或接触证明。

介质最小保存J位于单元2558、样本2、自然坐标(−1,+1)，靠近右底角；最大绝对Hu位于单元2540、分量(0,0,1)，在另一侧底部转折附近。机构实体两项极值均在单元1717，Hu=.043919787011376 mm⁻¹。J读取9个保存参考点，实际点集含Q1角点；Hu是单元常数u_i,JK，无积分点索引。图中红/青框标出各列的介质/实体极值单元；不声称连续域极值或应力HP。

## 工件受力与位置

峰态下半工件总(Fx,Fy)=(-0.0012160325586449507,+0.008127015649979884) N；材料项(-0.0006486496824310876,+0.005528806840212045)，Hu项(-0.0005673828762138631,+0.002598208809767841) N。这对应负保存内力，保持反力取相反号。

镜像上半体为(Fx,−Fy)，完整镜像净力(2Fx,0)=(-0.0024320651172899015,0) N；2|Fy|=.016254031299959767 N是两侧法向分量的标量和，不是完整装配净力或已经合格的夹持力。这里只声明现有约定，不把不同方向的力混加。

节点2670即(78,32) mm总力模0.0181035417239031 N，向量(-0.0011423615313819495,+0.01806746338257585) N。其材料模.004426791363123766 N、Hu模.013681836496219546 N；边界其它节点有反向作用，所以局部峰值大于工件净Fy。

每态保留全部153节点，包括31 physical_only、15 cut_only、2 physical_and_cut和105 interior。总力直接取保存total向量，未以材料+Hu重建；零节点保留，微小带符号数值不裁剪。12态共1836行CSV，逐项与保存三分量全局向量对应。角点/shared节点没有唯一面分配，节点力不是压力。

关于(70,40) mm的派生Mz：total=.10145226877960661，material=.03539500731329261，Hu=.06605726146631402 Nmm。它是已有节点力的普通汇总，不是新增独立HP力矩资格。卸载末态最大节点位移3.0232885689266874e−20 mm、工件总力(-2.580222315182282e−23,+1.1248127719477308e−24) N；原值保留，没有手动归零，也不据此声称物理滞回。

## 排查：控制器事件与审计器假设

生产一次完整通过：F94开始/93完成，T53开始/52完成，1 solver，0 JIT/HP。52个完成Newton base、41个trial（40完成+1范围失败）之外，还有一次F完成但T失败的base。因此53base+41trial=94F，完整组装次数为92而不是93F；不能将所有T开始都当成完成history。

T44绑定F77，出现在最后.5→0卸载尝试的第四个base，错误`unsupported_arithmetic_range`。原观察器已保存17输入数组与25已返回force字段，来源/模型/状态/序号匹配；失败state SHA为058bd50e0dd329595b324e185f793036733b72c887218fb26801091a49d54bd8。F90为另一个范围拒绝trial，之后half trial完成。原控制器实际逐字节回滚、二分.25，随后达到零。

失败T没有出现在完成history或任何接受缓存；.25对应T48/F84、返回零T53/F94均完成。**切线原始算术support-range问题仍未定位或修复。** 保存Gmax只排除了全局tiny分支，不构成原始primitive根因。没有重评失败T/F输入，没有为拒绝态授予HP资格，不能因接受路径完成而宣布内核全部范围问题解决。

原010参考器预设所有T都完成，24项预检后计数首错，HP0；该卡正式关闭。独立Ref002新增117行纯stdlib计数合同，只接受此保存事件的完整身份/回滚/二分/缓存链，未知缺失事件仍拒绝；一次12元数据测试（1真轨迹+11篡改负例）通过1092项记录检查，不调用力学、NumPy或HP。10项审计包装修订可逆恢复原010检查器，原B850数学参考、方向、门值保持。

Ref002按300/360 s执行全新参考，达到16HP完成/7完整状态后超时关闭；第8态两次HP虽完成，整态检查未完成，不能报8态或全路径通过。全部199旧文件、55份压缩详情和来源胶囊保留。

随后另建Ref003，显式600/660 s、8 GiB；依据Ref002实际301.4867 s/16调用作约452 s成本估计，不保证完成，也不在运行中扩预算。四处资源文字/参数与一处旧production inventory参考预算身份角色修订，共五处字面改动可逆恢复Ref002。重新对所有12态执行24新HP，不借用16调用前缀、009资格或仅合并已通过态。实际459.3966203 s终态exit0，全部原门通过。

## 验证范围与功能进度

新的外部Ref003只覆盖本声明源/任务的12个接受机械态：全部3200单元/6642 DOF的三分量力、固定lift的声明PORT方向Jv、完整CSC组装身份、平均约束/平衡及工件弱式合力。24新HP80/120、232272项检查全部完成。原生产HP/equilibrium/HF flags仍false，外部资格另列；没有给失败T、拒绝trial或旧关闭参考回授资格。

| 功能 | 当前实现 | 当前边界 |
|---|---|---|
| 普通LF几何读取与原生模型 | 数据适配、粗/细Q1和方/圆构建已有 | 不优化，不偷改几何；全部批量HF5尚未完成 |
| NumPy机械力入口 | split材料/Hu/total，16机械字段 | 默认完整模式仍保留；辅助能量not_evaluated |
| 切线与组装 | 显式chunk256、三切线、完整CSC | 独立导数参考为PORT方向，非全列；范围失败根因仍待处理 |
| 平均位移平衡路径 | 本方体1.8 mm完整加载/卸载 | 一固定工况，不等于圆/细网格全部通过 |
| 几何与作用位置 | 保存Q1跨域内部重叠、有限方体射线、全部节点力 | 完整包含、自重叠、压力/有效夹持尚未证明 |
| 其它研究能力 | 保留旧受限参考与阶段证据 | 自由刚体/完整接触压力、能量/应力HP、H2/H3/HF5、AD/JIT全部目标及正式标签/排名未完成 |

几何12次高层调用各一次完成，全部quad有效、raw/strict跨域内部重叠及roundoff ambiguity均false；所有AABB候选和实际SAT观察均0。此工况没有触发SAT候选分类，不把解析测试的覆盖算作本路径实测。封闭边界含数学cut，物理首次射线排除cut；完整集合包含和机构自重叠没有测试。

## 全部实际状态与可视化

| index | leg | input mm | 原目标index | 二分层 | R N | output+y mm | minJ | bottom ray mm | left ray mm |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
{numeric_table}

- [完整×1变形动画：12帧、每帧1000 ms](../../../functional_views/native_workpiece_cycle010_20261004/saved_render_001/animation_001/cycle010_actual_path.gif)
- [结构、反力、输出、三分量工件力及实际控制器过程](../../../functional_views/native_workpiece_cycle010_20261004/saved_render_001/physical_001/cycle010_saved_path.png)
- [×1峰态J/Hu全域和局部极值位置](../../../functional_views/native_workpiece_cycle010_20261004/saved_render_001/fields_001/peak_saved_J_Hu.png)
- [×1初始/峰值/返回几何与有限面射线](../../../functional_views/native_workpiece_cycle010_20261004/saved_render_001/geometry_001/cycle010_saved_regions.png)
- [峰态全部工件节点三力](../../../functional_views/native_workpiece_cycle010_20261004/saved_render_001/nodes_001/nodes_state_005.png)、[12帧节点力动画：1200 ms/帧](../../../functional_views/native_workpiece_cycle010_20261004/saved_render_001/nodes_001/nodal_force_path.gif)
- [12态数值CSV](../../../functional_views/native_workpiece_cycle010_20261004/saved_render_001/physical_001/accepted_numeric_states.csv)、[1836行节点力CSV](../../../functional_views/native_workpiece_cycle010_20261004/nodal_saved_001/observation_001/nodes.csv)、[3200单元峰态字段CSV](../../../functional_views/native_workpiece_cycle010_20261004/saved_render_001/fields_001/peak_elements.csv)

实际变形和位置均x1；综合物理图另列清楚标记的x4展示，无力箭头。所有节点力图跨态/分量共用.01N比例尺，采用此前已修正的minshaft=1渲染源778c，微小箭头随幅值缩小。没有插值、去重或人工制造零状态。root实际查看综合图、J/Hu、几何、节点峰态/返回；独立审阅者实际看后三类峰图。GIF真实帧数/时长已文件级核对；未宣称逐像素检查所有其它节点帧。

## 成本、来源与完整过程记录

| 阶段 | 终态 | helper s | outer s | 树采样RSS bytes | helper/outer预算 s，均8GiB | pins |
|---|---|---:|---:|---:|---|---:|
{cost_table}

prepare实际helper1.1010873 s；表内—表示未从该helper记录抽取耗时，不表示零。参考lifecycle与summary终态写盘时刻不同，表用lifecycle。F/T开始、完成、组装、已接受保存态和HP/检查数分开；生产保存F/T调用0。各原stdout/launch/receipt均保留，root已消费实际terminal exit后才进入依赖阶段。

010准备157pins、science230pins，source68/input73；新Ref002测试327/参考331pins，Ref003524pins，后处理951/1289/1307pins。本轮生产/辅助层没有改原模型/门/核心；静审与实际运行区分，晚到Ref003数学审阅单列为额外交付材料，未伪称它在运行524绑定中。

作者阶段曾出现CLI必选output遗漏/错误receipt路径、独立参考迁移匹配次数断言、旧inventory预算角色、旧参考文件后缀收集遗漏。均在相应正式新卡安装/运行前修正，原候选字节与说明留存，新F/T/HP/solver0；已关闭010/Ref002失败阶段没有改写。新J/Hu极值框是冻结前的5行显示定位，无字段/公式/门修改；对应pre_outline与独立可逆静审保留。

源码/数据主身份：result SHA `{digest(MECH/'result/result.json')}`；Ref003 summary SHA `{digest(MECH.with_name('coarse_square_cycle010_ref_003')/'reference/summary.json')}`；science protocol SHA `{digest(MECH/'protocol.json')}`；Ref003 protocol SHA `{digest(MECH.with_name('coarse_square_cycle010_ref_003')/'protocol.json')}`。全部细项由协议、当前repository manifest和作者/只读审查回执索引核对。

## 代码与证据入口

- [任务与原数值门](input_inventory.json)、[一次生产回执](execution_receipt.json)、[全部保存态](result/result.json)、[T44捕获](first_tangent_range_input/observation.json)
- [旧010参考首错](reference/summary.json)、[Ref002时间失败](../coarse_square_cycle010_ref_002/reference/summary.json)、[新Ref003完整参考](../coarse_square_cycle010_ref_003/reference/summary.json)
- [计数合同117行](../coarse_square_cycle010_ref_002/counter_contract.py)、[12元数据项一次回执](../coarse_square_cycle010_ref_002/tests_001/tests_receipt.json)
- [HF平均位移入口](../../../hf_repo/src/hf_eval/native_mean.py)、[CLI](../../../hf_repo/scripts/solve_native_mean.py)、[显式分块切线](../../../hf_repo/src/hf_eval/split_numpy_tangent.py)
- [纯保存工件节点力API](../../../hf_repo/src/hf_eval/workpiece_nodal.py)、[节点力CLI](../../../hf_repo/scripts/observe_workpiece_nodal_forces.py)、[当前固定方体几何诊断](../../../hf_repo/src/hf_eval/native_region_geometry.py)
- [009完整循环](../coarse_square_cycle_009/RESULTS.md)、[009节点力实现/显示修正](../../../functional_views/native_workpiece_nodal_20261004/square009_001/RESULTS.md)、[从开始延续的当前状态](../../../docs/CURRENT_STATUS.md)
- [作者候选/失败/静审/实际数值与视觉复核归档](../../../handoff/native_workpiece_cycle010_20261004/)

## 下一步依据与恢复

优先用本次T44/F77捕获做源码与原始primitive范围定位，解释为何近零返回存在范围失败；若确需计算，只设计一次针对已捕获输入的最小独立诊断，不重跑完整路径、不放宽门、不把Gmax当根因。此根因诊断尚未执行，内核尚未修复。依据其结果决定必要修复，避免新的无边界profiling链。

物理上随后优先匹配固定下半圆体R8 mm、中心(70,40)与本1.8 mm完整路径，观察方体角点作用是否主导；尺寸/位置和细网格再按结果逐步展开。当前圆体模型为原生单元中心判定的阶梯边界，不是贴体圆网格；固定方体有限bottom/left诊断明确拒绝circle，因此先扩展/明确适合单元并集的物理边界观察，不能直接复用方体射线当圆面结论。新圆工况/更大峰值未运行，不预先保证收敛、夹持或更低失真。

正式Git根为`D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC`，HF运行环境`D:/Coding/Diversity TO/Compliant-TO-TMC/.venv-handoff/Scripts/python.exe`，main唯一开发主干，origin=`https://github.com/dudaxing/Compliant-TO-TMC.git`。其它机器可在任意克隆路径恢复：先读本报告/最新CURRENT_STATUS，核分支/远端/清单，再用现有Python执行`python -B tools/handoff.py verify --output <新的仓库外JSON>`。旧绝对argv只记录实际环境，不是跨机器重播入口；已关闭目录不能复跑覆盖。公开恢复记录只核文件身份，不能当异机数值再验收或全部外部历史资产展开。
'''
    write_new(MECH/'RESULTS.md',report)
    write_new(VIEW/'README.md','''# Cycle010 保存可视化

最新物理结论、整体目标、全部状态、原失败与修正范围、代码入口和后续见[主报告](../../lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/RESULTS.md)。

本目录只读新010实际12个接受态和独立Ref003完整24HP证据。region_saved_001测量一次，nodal_saved_001观察一次；saved_render_001三个阶段顺序各一次通过。它们没有新的力学/HP求解。几何线不是力，节点力不是压力，派生力矩没有新增HP资格。
''')
    docs = ['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',
        'docs/PHYSICS_AND_FUNCTION_PROGRESS_20261001.md','docs/HF5_LF_V2_ADAPTER_AND_TASK_PLAN.md','docs/NUMPY_FORCE_PROGRESS_20261002.md']
    preservation = []
    for name in docs:
        path = ROOT/name
        previous = subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        assert path.read_bytes() == previous
        prefix = '' if name == 'README.md' else '../'
        text = f'''2026-10-04最新：**010的1.8 mm完整加载—卸载已完成，原11目标全部达到，包含原控制器额外.25 mm的12实际态；新Ref003全24 HP/232272项检查通过。** 输入峰反力.414394469 N、输出+y=2.08019363 mm，底/左有限法向射线.0317909716/2.85343057 mm，介质minJ=.00662089875、实体minJ=.955246548。见[整体目标、实现、排查、效果、全部失败/资源/资格与后续]({prefix}lf_data_preparation/native_workpiece_001/coarse_square_cycle_010/RESULTS.md)、[实际12帧×1动画]({prefix}functional_views/native_workpiece_cycle010_20261004/saved_render_001/animation_001/cycle010_actual_path.gif)、[J/Hu位置图]({prefix}functional_views/native_workpiece_cycle010_20261004/saved_render_001/fields_001/peak_saved_J_Hu.png)。

新12次几何/12次全节点力观察、1836行节点CSV和位置图完成，右下角节点峰力模.0181035417 N。原010参考因错误完整计数假设在HP前失败、Ref002在16HP/7完整态后超时，均关闭保留；Ref003新预算独立全量重新计算，没有拼接旧前缀。T44/F77范围失败虽已按原控制器回滚二分，primitive根因仍未修复；新资格只覆盖接受机械态，不含失败trial、压力/夹持、能量、应力HP或切线全列。原生产flags保持false。下一优先定位已捕获范围问题，再补圆体边界观察并开展匹配形状工况；本轮圆/细网格/更大峰值未运行，整体项目仍未完成。以下逐字节保留先前记录，当前以本条和新报告为准。

'''.encode('utf-8')
        path.write_bytes(text+previous)
        assert path.read_bytes()[len(text):] == previous
        preservation.append(dict(path=name,previous_commit=BASE,previous_sha256=sha256(previous).hexdigest(),
            prefix_bytes=len(text),current_sha256=digest(path),old_body_byte_identical=True))
    HANDOFF.mkdir(exist_ok=False)
    write_new(HANDOFF/'document_preservation.json',json.dumps(preservation,indent=2,ensure_ascii=False)+'\n')
    authors = [Path('D:/hf-native-workpiece-cycle010-author-20261004'),
        Path('D:/hf-native-workpiece-cycle010-counter-author-20261004'),
        Path('D:/hf-native-workpiece-cycle010-ref003-author-20261004'),AUTHOR]
    copies = []
    for directory in authors:
        for source in sorted(directory.rglob('*')):
            if source.is_file() and '__pycache__' not in source.parts:
                target = HANDOFF/'authoring'/directory.name/source.relative_to(directory)
                target.parent.mkdir(parents=True,exist_ok=True)
                assert not target.exists(); shutil.copyfile(source,target)
                assert source.read_bytes() == target.read_bytes()
                copies.append(dict(path=target.relative_to(ROOT).as_posix(),sha256=digest(target)))
    write_new(HANDOFF/'authoring_copies.json',json.dumps(dict(files=copies,scope='Exact author candidates/reviews; formal freeze roles are separate; late reviews do not acquire earlier runtime binding'),indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(status='written',report_sha256=digest(MECH/'RESULTS.md'),documents_preserved=7,author_files=len(copies))))

if __name__ == '__main__': main()
