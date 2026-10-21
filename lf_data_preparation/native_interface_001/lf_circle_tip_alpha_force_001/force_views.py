"""Two views of already saved two-alpha fixed-body nodal weak vectors.

Only supplied ordinary dictionaries are used. No original JSON, scientific
array, CSV, image or animation is opened. Arrow scaling is supplied by producer.
"""
import json
import os
from pathlib import Path

SOURCES = ('baseline', 'new')
PARTS = ('total', 'material', 'regularization')
LABELS = dict(total='total', material='material', regularization='Hu')
COLORS = dict(total='#205b8d', material='#207a69', regularization='#be6a28')
GROUPS = ('physical_only', 'cut_only', 'physical_and_cut', 'interior')


def _number(value):
    return format(value, '.17g')


def _link(root, outdir, path):
    return os.path.relpath(Path(root)/path, outdir).replace('\\', '/')


def _rows(data, key):
    return [data['raw_values'][index] for index in data['sources'][key]['raw_indices']]


def _axis(axis):
    axis.grid(alpha=.18, linewidth=.7)
    axis.tick_params(labelsize=8)
    for side in ('top', 'right'):
        axis.spines[side].set_visible(False)


def _ticks(axis):
    from matplotlib.ticker import FuncFormatter
    axis.yaxis.set_major_formatter(FuncFormatter(
        lambda value, position: '0' if value == 0 else format(value, '.2g')))


def _map_base(axis, source, display):
    from matplotlib.collections import LineCollection

    nodal = source['original']['nodal']
    positions = dict(zip(nodal['node_ids'], nodal['coordinates_mm']))
    tip = [source['state']['tip_x_mm'], source['state']['tip_y_mm']]
    witness = source['original']['derived']['tip_surface_witness']['point_mm']
    closest = source['original']['geometry']['boundary']['groups']['all_exposed']['closest_pair']
    axis.add_collection(LineCollection(
        [[positions[a], positions[b]] for a, b in nodal['edges']['closed']],
        colors='#96714e', linewidths=.9, zorder=1))
    axis.scatter([point[0] for point in nodal['coordinates_mm']],
                 [point[1] for point in nodal['coordinates_mm']],
                 s=4, color='#b8c0c8', alpha=.75, zorder=2)
    axis.plot([tip[0], witness[0]], [tip[1], witness[1]],
              color='#b47e17', linestyle='--', linewidth=1.1, zorder=4)
    axis.scatter(*tip, marker='*', s=50, color='#b47e17', zorder=5)
    axis.scatter(*witness, marker='x', s=22, color='#b47e17', zorder=5)
    a, b = closest['mechanism_point_mm'], closest['workpiece_point_mm']
    axis.plot([a[0], b[0]], [a[1], b[1]], color='#864784', linestyle=':', linewidth=1.1, zorder=4)
    axis.scatter(*a, marker='+', s=24, color='#864784', zorder=5)
    axis.scatter(*b, marker='+', s=24, color='#864784', zorder=5)
    axis.axhline(nodal['moment_origin_mm'][1], color='#6b7280', linestyle=':', linewidth=.7)
    axis.set(xlim=display['bounds_mm']['x'], ylim=display['bounds_mm']['y'],
             aspect='equal', xlabel='Actual fixed-body x (mm)', ylabel='Actual fixed-body y (mm)')
    _axis(axis)


def _vectors(data, outdir, plt):
    display = data['display']
    scale = display['arrow_mm_per_N']
    figure, axes = plt.subplots(2, 3, figsize=(21, 12))
    try:
        for row_index, key in enumerate(SOURCES):
            source = data['sources'][key]
            rows = _rows(data, key)
            for column, part in enumerate(PARTS):
                axis = axes[row_index, column]
                _map_base(axis, source, display)
                axis.quiver([row['coordinates_mm'][0] for row in rows],
                    [row['coordinates_mm'][1] for row in rows],
                    [row['on_body_N'][part][0]*scale for row in rows],
                    [row['on_body_N'][part][1]*scale for row in rows],
                    angles='xy', scale_units='xy', scale=1., color=COLORS[part],
                    width=.0022, alpha=.8, minlength=0, minshaft=1,
                    headlength=4, headaxislength=3.7, headwidth=3.2, zorder=3)
                axis.set_title(source['label']+' | '+LABELS[part]+' ON-body',
                    loc='left', fontsize=11, fontweight='bold', pad=10)
            holding = source['original']['nodal']['summary']['holding_reaction_on_model_N']
            figure.text(.055, .54 if row_index == 0 else .17,
                source['label']+' saved total holding on model [Fx,Fy] = ['
                +', '.join(map(_number, holding))+'] N = -saved ON-body total.\n'
                'Material/Hu sign reversals are algebraic bookkeeping, not independent measured reactions.',
                fontsize=9, va='top', linespacing=1.5)
        figure.suptitle('Saved loading peak 1.06 mm: two-alpha fixed-body nodal weak forces',
            fontsize=16, fontweight='bold', y=.98)
        figure.text(.055, .94,
            'All 565 nodes and vectors in every panel; actual lower-half geometry x1, no mirror.\n'
            'One common arrow conversion: '+format(scale, '.8g')+' mm/N; '
            +format(display['max_vector_norm_N'], '.8g')+' N maps to '
            +format(display['maximum_arrow_length_mm'], '.8g')+' mm of displayed arrow length.',
            fontsize=10, va='top', linespacing=1.6)
        figure.text(.055, .035,
            'Gold star/x: saved mechanism tip / nearest body point. Purple + / dotted line: saved global closest pair. Distance connectors are not forces.\n'
            'Only fixed-body geometry and these mechanism witness points are available; no full mechanism deformation is reconstructed.\n'
            'Zero vectors keep a node marker, not a finite arrow. Nodal weak vectors are not face traction, pressure or qualified grip.',
            fontsize=9, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.055, right=.98, top=.85, bottom=.22, hspace=.58, wspace=.22)
        figure.savefig(Path(outdir)/'force_vectors.png', dpi=160)
    finally:
        plt.close(figure)


def _components(data, outdir, plt):
    from matplotlib.patches import Patch
    from matplotlib.ticker import MaxNLocator

    rows_by_source = {key: _rows(data, key) for key in SOURCES}
    all_rows = data['raw_values']
    id_min = min(row['node_id'] for row in all_rows)
    id_max = max(row['node_id'] for row in all_rows)
    id_pad = .02*(id_max-id_min)
    # These extrema determine common display limits only, not new force metrics.
    extents = [max(abs(row['on_body_N'][part][component]) for row in all_rows for part in PARTS)
               for component in (0, 1)]
    figure, axes = plt.subplots(3, 2, figsize=(18, 15))
    try:
        for component, coordinate in enumerate(('x', 'y')):
            for column, key in enumerate(SOURCES):
                source = data['sources'][key]
                rows = rows_by_source[key]
                axis = axes[component, column]
                for part in PARTS:
                    axis.scatter([row['node_id'] for row in rows],
                        [row['on_body_N'][part][component] for row in rows],
                        s=9, alpha=.75, color=COLORS[part])
                axis.axhline(0., color='#6b7280', linewidth=.7)
                axis.set(xlim=(id_min-id_pad, id_max+id_pad),
                    ylim=(-1.08*extents[component], 1.08*extents[component]),
                    xlabel='Original global node ID (all 565, no force filtering)',
                    ylabel='Signed ON-body F'+coordinate+' (N)')
                axis.set_title(source['label']+' | all-node F'+coordinate,
                    loc='left', fontsize=11, fontweight='bold', pad=11)
                axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))
                _axis(axis)
                _ticks(axis)
            axis = axes[2, component]
            width = .13
            for part_index, part in enumerate(PARTS):
                for source_index, key in enumerate(SOURCES):
                    groups = data['sources'][key]['original']['nodal']['summary']['groups']
                    x = [index+(2*part_index+source_index-2.5)*width for index in range(len(GROUPS))]
                    axis.bar(x, [groups[group]['force_on_body_N'][part][component] for group in GROUPS],
                        width=width, color=COLORS[part], alpha=.85,
                        hatch=None if key == 'baseline' else '//', edgecolor='#35404d', linewidth=.55)
            labels = []
            for group in GROUPS:
                counts = [data['sources'][key]['original']['nodal']['summary']['groups'][group]['node_count']
                          for key in SOURCES]
                labels.append(group+'\nold N='+str(counts[0])+' / new N='+str(counts[1]))
            axis.set_xticks(range(len(GROUPS)), labels=labels, fontsize=8)
            axis.axhline(0., color='#6b7280', linewidth=.7)
            axis.set(xlabel='Original mutually exclusive nodal masks', ylabel='Signed group F'+coordinate+' (N)')
            axis.set_title('Original grouped F'+coordinate+' | old solid / new hatched',
                loc='left', fontsize=11, fontweight='bold', pad=11)
            _axis(axis)
            _ticks(axis)
        handles = [Patch(facecolor=COLORS[part], label=LABELS[part]) for part in PARTS]
        handles += [Patch(facecolor='white', edgecolor='#35404d', hatch=hatch, label=label)
                    for hatch, label in ((None, 'old alpha=5e-7'), ('//', 'new alpha=2.5e-7'))]
        figure.suptitle('All saved node components and original four-mask resultants',
            fontsize=16, fontweight='bold', y=.98)
        figure.text(.07, .94,
            'Upper rows:all original nodes, same Fx range across sources and same Fy range across sources; Fx and Fy ranges differ.\n'
            'Lower row:original signed group resultants. Zero, negative and cancelling contributions remain in the source data.',
            fontsize=10, va='top', linespacing=1.6)
        figure.legend(handles=handles, loc='upper center', bbox_to_anchor=(.53, .885),
            ncol=5, fontsize=9, frameon=False)
        figure.text(.07, .035,
            'Four nodal masks partition 565 nodes:physical_only71 / cut_only35 / physical_and_cut2 / interior457.\n'
            'The physical-edge and cut-edge node sets separately overlap at2 nodes; they are not a disjoint partition.\n'
            'Global-axis nodal and grouped weak forces are not local normal pressure. Dense/tiny values may need the exact ordinary JSON.',
            fontsize=9, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.075, right=.98, top=.815, bottom=.15, hspace=.60, wspace=.25)
        figure.savefig(Path(outdir)/'force_components.png', dpi=160)
    finally:
        plt.close(figure)


def _markdown(data, outdir, root):
    display = data['display']
    lines = ['# 两种alpha同峰固定工件节点弱力空间对照', '',
        '本页复用原FORCE1的ON-body定义，仅读六份已有普通节点JSON，不新增力核、切线、HP或平衡求解，不改变生产alpha。只核原加载1.06 mm峰，解释material/Hu分量重分配；不冒充覆盖全程最大R/q/距离/总Fy差。', '',
        '![两alpha三分量全部节点ON-body向量](force_vectors.png)', '',
        '图1为两alpha行、total/material/Hu三列。每面板保留565个节点与全部向量，零节点仍有浅色点位；minlength=0避免零向量出现有限箭头，不筛选或截断小力。',
        '共同实际轴与等比例，固定下半工件×1、无镜像。共同箭头换算为 '+_number(display['arrow_mm_per_N'])
        +' mm/N，原两alpha三分量共同最大模 '+_number(display['max_vector_norm_N'])+' N 对应 '
        +_number(display['maximum_arrow_length_mm'])+' mm显示长度；该换算不是结构变形、力地板或新指标。',
        '只画固定工件闭边与原tip/最近点/global closest pair见证。金色与紫色连接线是几何距离而非力；普通JSON不足以重建完整机构。约8–10微米距离在该全工件尺度不可凭图分辨，以原数值为准。', '',
        '![全部节点FxFy及原四mask组贡献](force_components.png)', '',
        '图2旧/新source按列，前两行分别全部节点Fx和Fy，同分量共享范围，Fx/Fy范围独立；下排是原四mask分组Fx/Fy。三色代表分量，实填/斜线柱代表alpha。原正负、零、抵消和极小量均保留，显式科学刻度不使用offset。',
        '四个节点mask是互斥完整分区：physical_only71、cut_only35、physical_and_cut2、interior457；另一个概念是physical/cut边节点集合，其交集为2，不能重复相加当互斥分区。', '',
        '## 精确来源身份与原合力', '']
    for key in SOURCES:
        source = data['sources'][key]
        state = source['state']
        summary = source['original']['nodal']['summary']
        lines += ['### '+source['label'], '',
            'alpha=`'+_number(source['alpha'])+'`；原SHA `'+state['state_sha256']+'`；原leg `'+state['leg']
            +'`；原accepted row '+str(state['index'])+'；global target '+str(state['original_target_index'])
            +'；d='+_number(state['d_mm'])+' mm。', '',
            'selected_state原身份：`'+json.dumps(source['selected_state'], ensure_ascii=False)+'`。', '',
            '|原分量|ON-body Fx N|ON-body Fy N|原保存矩 Nmm|', '|---|---:|---:|---:|']
        for part in PARTS:
            vector = summary['force_on_lower_body_N'][part]
            lines.append('|'+LABELS[part]+'|'+_number(vector[0])+'|'+_number(vector[1])+'|'
                +_number(summary['moment_about_origin_Nmm'][part])+'|')
        holding = summary['holding_reaction_on_model_N']
        lines += ['', '原保存total holding（作用于模型）[Fx,Fy] N：`['+', '.join(map(_number, holding))
            +']`，与工件ON-body total方向相反。material/Hu反号仅代数分量，不是独立测得反力或新保存数组。原矩只保留，不新增积分或移动原点。', '',
            '|原mask|节点数|total Fx N|total Fy N|material Fx N|material Fy N|Hu Fx N|Hu Fy N|',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
        for group in GROUPS:
            item = summary['groups'][group]
            values = [value for part in PARTS for value in item['force_on_body_N'][part]]
            lines.append('|'+group+'|'+str(item['node_count'])+'|'+'|'.join(map(_number, values))+'|')
        lines += ['', '原unsigned tip/Q1距离：'+_number(state['tip_to_raster_boundary_mm'])+' / '
            +_number(state['minimum_boundary_distance_mm'])+' mm；不作为接触/释放证明。', '',
            '[原人工页与既有实际变形入口](<'+_link(root, outdir, source['manual_path'])+'>)，stat '
            +str(source['manual_bytes'])+' bytes；本程序不读取旧媒体。', '',
            '绑定普通来源：', '```json', json.dumps(source['paths'], ensure_ascii=False, indent=2, allow_nan=False), '```', '']
    lines += ['## 原值、3390项差量与描述性账本', '',
        '[完整普通比较JSON](comparison.json)保存两source的原nodal/derived/geometry对象、原三力/holding/矩/37项row、1130条节点原值、565组节点配对及3390项new−baseline节点差量。',
        '`raw_values`保留原坐标/ID/mask/三向量；`node_pairs[*].on_body_N`按total/material/regularization保留baseline_value、new_value、new_minus_baseline二维向量，差量不裁零、不更名为压力。人工页不重复3390行大表。',
        '`group_pairs`保4组原值与24分量差，`whole_resultant_comparison`保三种合力的6分量差；两source的`descriptive`保存fsum全体/原mask与原summary之差、total−(material+Hu)尾差及原holding+ON-body total。它们只描述原值重组，不增加容差、吸零、相等或接触门。', '',
        '实际输出计数：', '```json', json.dumps(data['counts'], ensure_ascii=False, indent=2, allow_nan=False), '```', '',
        '原三合力描述性对照：', '```json', json.dumps(data['whole_resultant_comparison'], ensure_ascii=False, indent=2, allow_nan=False), '```', '',
        '## 解释边界', '',
        '工件固定坐标等于实际坐标，依据各producer已绑定的工件lift/fluctuation为零合同；本卡不另读数组重验。所有力为下半模型有符号全局弱力，不镜像倍增，不分配为某邻面的牵引，不径向投影成法向压力，不授有效夹持。',
        '仅stat/链接两份原人工页；无旧PNG/GIF读取、解码、复制、抽帧、重哈希或拼接，不新增完整机构变形图。两张新图的密集箭头和微小量若看不清，记录可见性限制，不临时补绘。',
        '不因峰图新增全路径独立参考、压力、有效夹持、释放、稳定性、alpha独立性、网格/域宽收敛或HF5资格。两source原峰HP各保原态/方向，不互相转移；1.02/1.03仍只是峰图后的候选。', '',
        '原范围说明：', '', str(data['scope']), '']
    return '\n'.join(lines).rstrip()+'\n'


def render(data, outdir, root):
    """Write exactly two new PNGs and one Markdown page from supplied dicts."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    with plt.rc_context({'font.family':'DejaVu Sans', 'axes.edgecolor':'#6b7280',
                         'axes.labelcolor':'#263447', 'text.color':'#263447',
                         'xtick.color':'#4b5563', 'ytick.color':'#4b5563',
                         'figure.facecolor':'white', 'axes.facecolor':'white'}):
        _vectors(data, outdir, plt)
        _components(data, outdir, plt)
    with (Path(outdir)/'REVIEW.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_markdown(data, outdir, root))
