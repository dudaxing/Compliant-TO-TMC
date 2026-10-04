"""Publish actual closed nodal evidence and preserve previous front bodies."""
from pathlib import Path
from hashlib import sha256
import csv
import json
import math
import posixpath
import shutil
import subprocess
from PIL import Image

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
BASE = '3f0418490b3994ad0ef7c2881bc005d237cff8e1'
STAGE = ROOT/'functional_views/native_workpiece_nodal_20261004/square009_001'
VIEW = STAGE.with_name('square009_view002')
HANDOFF = ROOT/'handoff/native_workpiece_nodal_20261004'
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
digest = lambda p:sha256(p.read_bytes()).hexdigest()
rel = lambda p:p.relative_to(ROOT).as_posix()


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')


def main():
    observation = read(STAGE/'observation_001/summary.json')
    assert observation['status'] == 'pass' and observation['observations_completed'] == 9
    notes = ('observation_readonly_review.json','phase_cost_readonly_review.json',
             'visual001_readonly_review.json','visual002_readonly_review.json')
    for name in notes:
        assert (AUTHOR/name).is_file()
    assert read(AUTHOR/'observation_readonly_review.json')['status'] == 'pass'
    assert read(AUTHOR/'visual002_readonly_review.json')['status'] == 'pass'
    phases = []
    for stage, names in ((STAGE, ('tests','observe','render')), (VIEW, ('render',))):
        protocol = read(stage/'protocol.json')
        assert all(digest(ROOT/name) == v for name,v in protocol['bindings'].items())
        for name in names:
            receipt = read(stage/(name+'_launch.json'))
            assert receipt['status'] == 'pass' and receipt['exit_code'] == 0 and receipt['invocations'] == 1
            assert receipt['all_bindings_unchanged'] and receipt['stop_reason'] is None
            phases.append(dict(stage=rel(stage), phase=name, **{k:receipt[k] for k in
                ('elapsed_seconds','peak_sampled_tree_RSS_bytes','outer_seconds')}))
    key = read(VIEW/'render_001/key_states.json')
    assert key['nodal_csv_sha256'] == digest(STAGE/'observation_001/nodes.csv')
    frames = Image.open(VIEW/'render_001/nodal_force_path.gif')
    assert frames.n_frames == 9
    durations = []
    for index in range(9):
        frames.seek(index); durations.append(frames.info['duration'])
    assert durations == [1200]*9
    frames.close()
    rows = list(csv.DictReader((STAGE/'observation_001/nodes.csv').open(newline='',encoding='utf-8')))
    assert len(rows) == 1377 and len(rows[0]) == 15
    peak = observation['states'][4]['summary']
    peak_rows = [row for row in rows if row['accepted_index'] == '4']
    strongest = max(peak_rows, key=lambda r:math.hypot(float(r['total_Fx_N']),float(r['total_Fy_N'])))
    abs_hu_y = math.fsum(abs(float(r['regularization_Fy_N'])) for r in peak_rows)
    hu_net_y = peak['force_on_lower_body_N']['regularization'][1]
    hu_moment_fraction = peak['moment_about_origin_Nmm']['regularization']/peak['moment_about_origin_Nmm']['total']
    cost_table = ['| 实际独立阶段 | outer秒 | 树RSS bytes |','|---|---:|---:|']
    cost_table += [f"| {p['stage'].split('/')[-1]}/{p['phase']} | {p['elapsed_seconds']:.7f} | {p['peak_sampled_tree_RSS_bytes']} |" for p in phases]
    state_table = ['| index | leg | 输入mm | Fx N | Fy N | 派生Mz N mm |', '|---:|---|---:|---:|---:|---:|']
    for state in observation['states']:
        fx,fy = state['summary']['force_on_lower_body_N']['total']
        mz = state['summary']['moment_about_origin_Nmm']['total']
        state_table.append(f"| {state['index']} | {state['leg']} | {state['d_mm']:g} | {fx:.12g} | {fy:.12g} | {mz:.12g} |")
    derived = dict(strongest_total_node=strongest,
        peak_hu_absolute_Fy_sum_N=abs_hu_y, peak_hu_net_Fy_N=hu_net_y,
        peak_hu_moment_fraction=hu_moment_fraction, cost=phases,
        gif_actual_frames=9,gif_durations_ms=durations,
        nodal_rows=1377,nodal_columns=15,mechanical_replay=False,HP_replay=False)
    write(STAGE/'derived_saved_statistics.json', derived)
    context = (AUTHOR/'report_context.md').read_text(encoding='utf-8')
    results = context+f'''

## 本轮实际结果与物理解释

五个解析案例一次通过，覆盖已知力/力矩、分组、缺失固定DOF、微小残余与抵消、稀疏非连续节点、平移/原点变换和正负纯力偶。观察一次9/9，CSV为1377行、15列，36份源/输入身份绑定。三个保存力分量的节点fsum与原每态工件合力逐值相同，每节点工件总力与保持反力反号；所有原目标index/leg/d/SHA逐态匹配同一009参考。31 physical_only、15 cut_only、2 physical_and_cut、105 interior，共153节点；48闭边=32物理边+16截面边。九态cut_only和interior保存的三分量节点力均严格为零，仍输出和计数。初始全部力严格零，返回仍保留微小非零力。四组重求合力误差均在声明的浮点求和界内，峰态最大分量重组差4.336808689942018e-19 N只是诊断量，未覆盖独立total。

峰态总下半体受力(Fx,Fy)=(-0.0007910899872955321,+0.0037892857813192618) N。材料为(-0.0003137551201961619,+0.0023430611778208557)，Hu为(-0.00047733486709937006,+0.0014462246034984065) N。保持反力反号。镜像上半体(Fx,-Fy)，完整镜像净力(2Fx,0)，2|Fy|只是纵向标量和，不能当完整净力或夹持资格。

最大的总节点矢量位于node {strongest['node_id']}、({strongest['x_mm']},{strongest['y_mm']}) mm底部右角，模为{key['maximum_nodal_vector_N']:.15g} N，矢量({strongest['total_Fx_N']},{strongest['total_Fy_N']}) N。该节点属于两条物理边交点，不能唯一拆给底面或侧面。该节点Hu纵向力为{strongest['regularization_Fy_N']} N。Hu全部节点|Fy|之和为{abs_hu_y:.15g} N，明显大于Hu净Fy={hu_net_y:.15g} N，说明存在方向相反的局部节点力；合力不能代表这些局部作用。绕(70,40)的总/材料/Hu派生Mz为0.06579467316655178/0.012724871252725275/0.05306980191382652 N mm，Hu约占{100*hu_moment_fraction:.4g}%。这显示正则项在此粗网格近接触作用分布中明显，值得后续通过物理参数/网格工况研究，不能直接换算为接触压力，也不能凭本图否定或宣称一般夹持。

返回总(Fx,Fy)=(-4.407897629741671e-31,+2.985672011257475e-32) N、派生Mz=-3.713643972160984e-30 N mm；并未手工置零。在全程相同的力标尺下这些残余应不可见，数值仍在CSV和标题中。

'''+ '\n'.join(state_table)+'''

## 实际可视化与显示问题保留

001测试/观察/绘图程序均实际exit0且冻结绑定不变；人工验图发现原minshaft=0把零矢量绘成固定箭头头部，导致初始、内部节点和回零图有假箭头。原九PNG、GIF、源、协议和终态日志全部保留，其渲染不作为正确力图交付。该卡已关闭，数值观察仍有效。

独立view002只改minshaft=0→1，minlength=0保持；短箭头头/杆按长度同步缩小，零矢量退化为不可见点，没有小箭头/小点的显示下限。逆替换后新旧源码逐字节相同。新卡一次重新绘相同CSV/状态，未重跑测试、节点观察、几何或力学。root和独立审阅者实际查看初始/峰值/返回PNG，初始/返回已无假力箭头。九个实际PNG和九帧1200ms GIF保留全部加载/卸载index，无插值、无去重。

'''+f'''[峰态三分量节点力图](../square009_view002/render_001/nodes_state_004.png)、[实际九态节点力动画](../square009_view002/render_001/nodal_force_path.gif)、[初始](../square009_view002/render_001/nodes_state_000.png)、[返回](../square009_view002/render_001/nodes_state_008.png)、[1377行CSV](observation_001/nodes.csv)、[完整数值观察](observation_001/summary.json)、[继承009全机构×1变形动画](../../native_workpiece_cycle009_20261004/saved_render_001/animation_001/cycle009_actual_path.gif)。

结构为实际×1局部几何，全部态/三分量统一力标尺：{key['common_N_to_display_mm']:.15g}显示mm/N，图例0.01 N；力箭头显示长度不是物理位移。PNG实际1950×754，数学截面紫虚线、共有角点金色、cut_only紫点。新显示源/观察JSON/CSV/result SHA均记录在[key_states](../square009_view002/render_001/key_states.json)。

'''+ '\n'.join(cost_table)+f'''

测试helper={read(STAGE/'tests_receipt.json')['elapsed_seconds']:.7f} s，节点观察helper={observation['elapsed_seconds']:.7f} s；绘图helper时长在各stdout日志中。本轮四个真实phase窗口（含一次独立显示修正）总outer={sum(p['elapsed_seconds'] for p in phases):.7f} s，不与历史009生产/HP成本混淆。所有outer均在150 s内、RSS在8 GiB内；各入口每阶段一次，无force、资源扩展或机械重试。原009的18fresh HP仅作继承来源，新增HP为0。

## 接口、复现与恢复范围

源码：[workpiece_nodal.py](../../../hf_repo/src/hf_eval/workpiece_nodal.py)，76行纯节点观察API；[observe_workpiece_nodal_forces.py](../../../hf_repo/scripts/observe_workpiece_nodal_forces.py)，保存NPZ/JSON/身份核对与CSV入口。现已运行的是同一009参考分支；--reference省略分支仅静态审阅，报告not_available，不另宣称运行验证或高精度资格。

从仓库根目录，以已有环境运行入口（选择新输出目录，不能覆盖证据）：

```powershell
python -B hf_repo/scripts/observe_workpiece_nodal_forces.py --repo hf_repo --input lf_data_preparation/native_workpiece_001/coarse_square_cycle_009/result --reference lf_data_preparation/native_workpiece_001/coarse_square_cycle_009/reference/summary.json --output <new-output> --time-limit 120
```

正式历史卡禁止重启；接续开发应建立新的明确任务，查看本报告、protocol/source_freeze、原009 RESULTS以及 docs/CURRENT_STATUS / RESUME_DEVELOPMENT。保存观察采用repo/input/reference相对角色，实际新目录恢复不依赖原开发绝对路径。当前绘图需要匹配的源文件字节；快照保留了来源，不能把不同未来版本悄悄替代历史源。公开恢复只核仓库文件身份，不重播任何力学/HP，不自动恢复外置旧大证据资产。
'''
    (STAGE/'RESULTS.md').write_text(results, encoding='utf-8')
    write(STAGE/'quality_closure.json', dict(status='closed_with_visual001_failure',
        tests='pass_5_once',observation='pass_9_once',original_render_terminal='pass',
        original_render_quality='rejected_zero_vector_arrows',corrected_independent_view='square009_view002_once_pass',
        source_bytes_unchanged=True,observation_reused_without_new_API=True,mechanical_replay=False))
    HANDOFF.mkdir(exist_ok=False)
    (HANDOFF/'authoring').mkdir()
    for p in AUTHOR.iterdir():
        if p.suffix in ('.py','.md','.json'):
            destination = HANDOFF/p.name if p.name in notes else HANDOFF/'authoring'/p.name
            shutil.copyfile(p,destination)
    old_fronts = read(ROOT/'handoff/native_workpiece_cycle009_20261004/document_preservation.json')['fronts']
    preservation = []
    for item in old_fronts:
        path = ROOT/item['path']
        old = subprocess.check_output(['git','show',BASE+':'+item['path']],cwd=ROOT)
        assert path.read_bytes() == old
        report_link = posixpath.relpath(rel(STAGE/'RESULTS.md'), path.parent.relative_to(ROOT).as_posix() or '.')
        figure_link = posixpath.relpath(rel(VIEW/'render_001/nodes_state_004.png'), path.parent.relative_to(ROOT).as_posix() or '.')
        prefix = (f'2026-10-04最新：**新增全工件节点力API/CLI，5解析项一次通过；009保存九态全部153节点、1377行CSV核对通过。** '
            f'见[目标、实现、效果、显示问题修正与后续]({report_link})和[峰态材料/Hu/总节点力图]({figure_link})。'
            '峰态右底角节点力模0.0127476461 N，Hu局部反向抵消显著；合力仍与009一致。派生力矩未新增HP资格，节点力不是压力。\n\n'
            '原001绘图零矢量假箭头已人工检出并保留；独立002仅改短箭头缩放，一次重绘相同数据通过。'
            '本轮无新力学/HP或更大行程求解。下一步依据底射线0.0767107 mm、介质minJ0.0280804，冻结小幅近接触峰值和完整卸载任务；'
            '圆体/尺寸位置/细网格继续作为独立工况。以下逐字节保留此前原文，当前以本条和新报告为准。\n\n').encode('utf-8')
        path.write_bytes(prefix+old)
        preservation.append(dict(path=item['path'],baseline_sha256=sha256(old).hexdigest(),
            current_sha256=digest(path),old_body_preserved=path.read_bytes()[len(prefix):]==old,
            prefix_bytes=len(prefix),appendix_bytes=0))
    write(HANDOFF/'document_preservation.json',dict(baseline_commit=BASE,fronts=preservation,
        scope='Seven old front bodies byte exact; new prefix states actual completed function and limitations'))
    print(json.dumps(dict(status='documented',report_sha256=digest(STAGE/'RESULTS.md'),
                         fronts_preserved=len(preservation),derived_saved_data_only=True)))


if __name__ == '__main__':
    main()
