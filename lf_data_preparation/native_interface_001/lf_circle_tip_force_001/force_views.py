"""Visualize already saved fixed-workpiece nodal weak vectors from dictionaries.

No scientific input, old figure, or animation is opened by this module.
The only writes are the two new scalar/vector PNGs and their Markdown page.
"""
from math import hypot
import json
import os
from pathlib import Path


PARTS = ('total', 'material', 'regularization')
LABELS = dict(total='total', material='material', regularization='Hu')
COLORS = dict(total='#205b8d', material='#207a69', regularization='#be6a28')
GROUPS = ('physical_only', 'cut_only', 'physical_and_cut', 'interior')


def _number(value):
    return format(value, '.17g')


def _link(root, outdir, path):
    return os.path.relpath(Path(root) / path, outdir).replace('\\', '/')


def _tick_formatter(axis):
    from matplotlib.ticker import FuncFormatter
    axis.yaxis.set_major_formatter(FuncFormatter(
        lambda value, position: '0' if value == 0 else format(value, '.2g')))


def _light_axis(axis):
    axis.grid(alpha=.18, linewidth=.7)
    axis.tick_params(labelsize=8)
    for side in ('top', 'right'):
        axis.spines[side].set_visible(False)


def _context(data):
    nodal = data['nodal']
    coordinates = nodal['coordinates_mm']
    positions = dict(zip(nodal['node_ids'], coordinates))
    tip = [data['state']['tip_x_mm'], data['state']['tip_y_mm']]
    witness = data['derived']['tip_surface_witness']['point_mm']
    closest = data['geometry']['boundary']['groups']['all_exposed']['closest_pair']
    points = coordinates + [tip, witness, closest['mechanism_point_mm'],
                            closest['workpiece_point_mm']]
    margin = 2.6
    bounds = ((min(point[0] for point in points) - margin,
               max(point[0] for point in points) + margin),
              (min(point[1] for point in points) - margin,
               max(point[1] for point in points) + margin))
    maximum = max(hypot(*vector) for part in PARTS
                  for vector in nodal['forces_on_body_N'][part])
    # This is a single common arrow display conversion, never a force floor.
    arrow_mm_per_N = 2. / maximum if maximum != 0 else 1.
    return positions, tip, witness, closest, bounds, maximum, arrow_mm_per_N


def _map_base(axis, data, context):
    from matplotlib.collections import LineCollection
    positions, tip, witness, closest, bounds, maximum, scale = context
    nodal = data['nodal']
    axis.add_collection(LineCollection(
        [[positions[a], positions[b]] for a, b in nodal['edges']['closed']],
        colors='#96714e', linewidths=.9, zorder=1))
    axis.scatter([point[0] for point in nodal['coordinates_mm']],
                 [point[1] for point in nodal['coordinates_mm']],
                 s=4, color='#b8c0c8', alpha=.75, zorder=2)
    axis.plot([tip[0], witness[0]], [tip[1], witness[1]],
              color='#b47e17', linestyle='--', linewidth=1.2, zorder=4)
    axis.scatter(*tip, marker='*', s=55, color='#b47e17', zorder=5)
    axis.scatter(*witness, marker='x', s=23, color='#b47e17', zorder=5)
    a, b = closest['mechanism_point_mm'], closest['workpiece_point_mm']
    axis.plot([a[0], b[0]], [a[1], b[1]], color='#864784',
              linestyle=':', linewidth=1.2, zorder=4)
    axis.scatter(*a, marker='+', s=25, color='#864784', zorder=5)
    axis.scatter(*b, marker='+', s=25, color='#864784', zorder=5)
    axis.axhline(data['nodal']['moment_origin_mm'][1],
                 color='#6b7280', linestyle=':', linewidth=.7)
    axis.set(xlim=bounds[0], ylim=bounds[1], aspect='equal',
             xlabel='Actual fixed-body x (mm)', ylabel='Actual fixed-body y (mm)')
    _light_axis(axis)


def _render_vectors(data, outdir, plt):
    context = _context(data)
    positions, tip, witness, closest, bounds, maximum, scale = context
    coordinates = data['nodal']['coordinates_mm']
    figure, axes = plt.subplots(3, 2, figsize=(16, 14))
    try:
        for row_index, part in enumerate(PARTS):
            for column, (key, title) in enumerate((
                    ('on_body_N', 'ON-body saved nodal weak vectors'),
                    ('holding_N', 'Opposite direction: -ON-body (derived display)'))):
                axis = axes[row_index, column]
                _map_base(axis, data, context)
                vectors = [row[key][part] for row in data['node_rows']]
                axis.quiver([point[0] for point in coordinates],
                            [point[1] for point in coordinates],
                            [vector[0] * scale for vector in vectors],
                            [vector[1] * scale for vector in vectors],
                            angles='xy', scale_units='xy', scale=1.,
                            color=COLORS[part], width=.0022, alpha=.8,
                            minlength=0, minshaft=1, headlength=4,
                            headaxislength=3.7, headwidth=3.2, zorder=3)
                axis.set_title(LABELS[part] + ' | ' + title,
                               loc='left', fontsize=10.5, fontweight='bold', pad=10)
        figure.suptitle('Circle-tip peak 1.06 mm: fixed lower-half workpiece node contributions',
                       fontsize=16, fontweight='bold', y=.98)
        figure.text(.07, .936,
                    f"All {len(coordinates)} body nodes are plotted in every panel; zero vectors retain their node marker. "
                    'Actual geometry x1, no mirror.\n'
                    'One common arrow conversion: ' + format(scale, '.7g') + ' mm/N; '
                    + format(maximum, '.7g') + ' N corresponds to 2 mm of displayed arrow length.',
                    fontsize=10, va='top', linespacing=1.6)
        figure.text(.07, .035,
                    'Gold star / x: actual mechanism tip / its saved nearest body point. Purple + / dotted line: saved global closest pair.\n'
                    'Both distance connectors are geometric references, not force arrows. Only fixed-body coordinates and these mechanism witness points are available.\n'
                    'Right column is a linear sign reversal for display. Its total agrees with the saved holding convention; material/Hu reversals are component bookkeeping.\n'
                    'Global nodal weak vectors are not face traction, pressure, effective clamping force, or a newly solved free-workpiece response.',
                    fontsize=8.5, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.07, right=.98, top=.865, bottom=.14,
                               hspace=.36, wspace=.23)
        figure.savefig(Path(outdir) / 'force_vectors.png', dpi=160)
    finally:
        plt.close(figure)


def _render_components(data, outdir, plt):
    from matplotlib.ticker import MaxNLocator

    rows = data['node_rows']
    ids = [row['node_id'] for row in rows]
    groups = data['groups']
    figure, axes = plt.subplots(2, 2, figsize=(16, 11))
    try:
        for axis_index, coordinate in enumerate(('x', 'y')):
            axis = axes[0, axis_index]
            for part in PARTS:
                axis.scatter(ids, [row['on_body_N'][part][axis_index] for row in rows],
                             s=9, alpha=.75, color=COLORS[part], label=LABELS[part])
            axis.axhline(0., color='#6b7280', linewidth=.7)
            axis.set(title='All saved nodal F' + coordinate + ' contributions',
                     xlabel='Original global node ID (no force filtering)',
                     ylabel='Signed ON-body F' + coordinate + ' (N)')
            axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))
            _light_axis(axis)
            _tick_formatter(axis)
            axis.legend(fontsize=9, frameon=False)

            axis = axes[1, axis_index]
            width = .24
            for part_index, part in enumerate(PARTS):
                x = [index + (part_index - 1) * width for index in range(len(GROUPS))]
                axis.bar(x, [groups[group]['force_on_body_N'][part][axis_index]
                             for group in GROUPS], width=width, color=COLORS[part],
                         alpha=.85, label=LABELS[part])
            labels = [group + '\nN=' + str(groups[group]['node_count']) for group in GROUPS]
            axis.set_xticks(range(len(GROUPS)), labels=labels, fontsize=8)
            axis.axhline(0., color='#6b7280', linewidth=.7)
            axis.set(title='Original four-mask grouped F' + coordinate + ' resultants',
                     xlabel='Original nodal mask category; signed sums retained',
                     ylabel='Signed ON-body F' + coordinate + ' (N)')
            _light_axis(axis)
            _tick_formatter(axis)
            axis.legend(fontsize=9, frameon=False)
        figure.suptitle('Circle-tip peak: signed node forces and original mask-group contributions',
                       fontsize=16, fontweight='bold', y=.98)
        figure.text(.07, .92,
                    'Upper panels keep every node and all three original components, including zero and negative values.\n'
                    'Lower panels use the saved group resultants directly. Visual overlap does not establish equality; cancellation is not removed.',
                    fontsize=10, va='top', linespacing=1.6)
        figure.text(.07, .035,
                    'The four saved nodal masks are physical_only, cut_only, physical_and_cut, and interior.\n'
                    'Physical-edge and symmetry-cut node sets themselves overlap; they must not be added as a disjoint partition.\n'
                    'Fx/Fy are global-axis weak contributions of the fixed lower-half workpiece, not local normal contact pressure.',
                    fontsize=9, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.08, right=.98, top=.815, bottom=.16,
                               hspace=.48, wspace=.25)
        figure.savefig(Path(outdir) / 'force_components.png', dpi=160)
    finally:
        plt.close(figure)


def _markdown(data, outdir, root):
    state, summary = data['state'], data['original_summary']
    context = _context(data)
    scale = context[-1]
    lines = ['# 尖端对向圆形工件：峰值固定工件节点弱力空间贡献', '',
        '本页只读取已有普通JSON，显示保存态1.06 mm的固定工件节点力，不新增构模、F/T、HP或平衡求解。',
        '半径9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm及其余物理条件保持。', '',
        f"原state SHA：`{state['state_sha256']}`；原leg：`{state['leg']}`；"
        f"原目标序号：{state['original_target_index']}；原接受行：{state['index']}；d = {_number(state['d_mm'])} mm。", '',
        '## 全部固定工件节点及保持方向', '',
        '![三分量有符号ON-body节点向量与反号方向](force_vectors.png)', '',
        f"每个面板均显示全部{data['counts']['node_count']}个工件节点；零向量仍保留节点标记，不筛选小力或只挑尖端节点。",
        f"全部六个面板共用箭头显示比例 {_number(scale)} mm/N。箭头长度为力的显示转换，不是位移或结构变形；工件几何为实际×1、下半模型，无镜像倍增。",
        '左列使用原ON-body弱力向量。右列仅逐节点线性取反以显示平衡保持方向；total对应原support holding约定，material／Hu的反号是分量账本，不冒充新保存的独立支反力数组。',
        '金色星号为真实夹持器尖端，叉号为其原最近工件点；紫色加号为原全边界最近点对。连接线表示距离见证，不表示力，也不补画完整夹持器形状。',
        '原nodal坐标来自参考网格，但原viewer已要求工件全部lift和fluctuation严格为零，所以固定工件的参考坐标等于实际坐标。', '',
        '## 全节点分量与原mask分组', '',
        '![全部节点FxFy及四类原mask有符号贡献](force_components.png)', '',
        '上排保留所有原节点的三分量Fx／Fy；下排直接使用原summary.groups的四类贡献，不重新定义分类。零值、小负值与相互抵消均保留。',
        'physical_only、cut_only、physical_and_cut、interior是原节点mask类别。physical边和cut边的节点集合另外存在交叠，不能将两个边集合直接当作互斥分区相加。', '',
        '| 原分量 | 下半工件 ON-body Fx N | 下半工件 ON-body Fy N | 原关于中心力矩 Nmm |',
        '|---|---:|---:|---:|']
    for part in PARTS:
        vector = summary['force_on_lower_body_N'][part]
        lines.append('| ' + LABELS[part] + ' | ' + _number(vector[0]) + ' | '
                     + _number(vector[1]) + ' | '
                     + _number(summary['moment_about_origin_Nmm'][part]) + ' |')
    holding = summary['holding_reaction_on_model_N']
    lines += ['', '原总holding reaction（作用于模型）[Fx,Fy] N：`['
              + ', '.join(map(_number, holding)) + ']`。', '',
        '| 原mask | 节点数 | total Fx N | total Fy N | material Fx N | material Fy N | Hu Fx N | Hu Fy N |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for group in GROUPS:
        record = data['groups'][group]
        values = [value for part in PARTS for value in record['force_on_body_N'][part]]
        lines.append('| ' + group + ' | ' + str(record['node_count']) + ' | '
                     + ' | '.join(map(_number, values)) + ' |')
    lines += ['', '原mask覆盖观察及完整描述性核对如下；只记录原值、差值和抵消，不增加接触／夹持验收门。', '',
        '```json', json.dumps(data['counts'], ensure_ascii=False, indent=2,
                             allow_nan=False), '```', '',
        '```json', json.dumps(data['descriptive'], ensure_ascii=False, indent=2,
                             allow_nan=False), '```', '',
        '## 既有实际变形入口', '',
        '[STEP10既有实际变形GIF](<'
        + _link(root, outdir, data['existing_GIF']['path']) + '>)；stat大小 '
        + str(data['existing_GIF']['bytes']) + ' bytes。', '',
        '[STEP10原人工检查页](<' + _link(root, outdir, data['existing_manual']) + '>)。', '',
        '本程序不打开、解码、复制、抽帧或重新哈希旧媒体。当前普通JSON只有工件全部坐标与少量机制距离见证点，不足以重绘完整实际变形夹持器；完整结构查看上述原动画。', '',
        '## 解释范围', '',
        '节点向量是组装后的全局弱式力，包含材料与Hu贡献，不能分配成节点某个相邻面的牵引。图中不进行径向投影，不生成压力或有效夹持力，不将physical mask的力单独认定为接触力。',
        '全部Fx／Fy为下半固定工件的有符号全局轴分量，未镜像倍增。保持反力约定与作用在工件上的力方向相反；它不代表自由工件的运动、释放或稳定性已求解。',
        '本轮不改变原峰值参考、全路径参考及压力、有效夹持、释放、稳定性、网格／域宽或HF5资格。', '',
        '### 原范围说明', '', str(data['scope']), '',
        '### 来源', '', '```json',
        json.dumps(data['provenance'], ensure_ascii=False, indent=2, allow_nan=False), '```', '']
    return '\n'.join(lines).rstrip() + '\n'


def render(data, outdir, root):
    """Write two new PNGs and one Markdown page from the supplied ordinary dict."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    with plt.rc_context({'font.family': 'DejaVu Sans', 'axes.edgecolor': '#6b7280',
                         'axes.labelcolor': '#263447', 'text.color': '#263447',
                         'xtick.color': '#4b5563', 'ytick.color': '#4b5563',
                         'figure.facecolor': 'white', 'axes.facecolor': 'white'}):
        _render_vectors(data, outdir, plt)
        _render_components(data, outdir, plt)
    with (Path(outdir) / 'REVIEW.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_markdown(data, outdir, root))
