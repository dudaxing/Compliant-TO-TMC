"""Two scalar views of four accepted alpha=2.5e-7 circle-tip source segments.

This module receives ordinary dictionaries.  It never opens scientific inputs,
old figures, or animation payloads; old paths are used only to form links.
"""
import json
import os
from pathlib import Path


def _number(value):
    """Readable signed scalars, including tiny nonzero values, without snapping."""
    return format(value, '.10g')


def _link(root, outdir, path):
    return os.path.relpath(Path(root) / path, outdir).replace('\\', '/')


def _branches(rows):
    loading = [row for row in rows if row['display_branch'] in ('origin', 'loading')]
    unloading = [row for row in rows if row['display_branch'] == 'unloading']
    if unloading:
        first = unloading[0]['display_index']
        # The already present turning point joins the two visual lines only.
        # No row or same-input pair is created by this display operation.
        unloading = [rows[first - 1]] + unloading
    return (('loading display', '-', loading),
            ('unloading display', '--', unloading))


def _style_axis(axis, title, xlabel, ylabel):
    from matplotlib.ticker import FuncFormatter

    axis.set_title(title, loc='left', fontsize=12, fontweight='bold', pad=12)
    axis.set_xlabel(xlabel, fontsize=9)
    axis.set_ylabel(ylabel, fontsize=9)
    axis.grid(alpha=.22, linewidth=.7)
    axis.tick_params(labelsize=8)
    # Explicit per-tick notation avoids an offset text colliding with titles.
    axis.yaxis.set_major_formatter(FuncFormatter(
        lambda value, position: '0' if value == 0 else format(value, '.2g')))
    for spine in ('top', 'right'):
        axis.spines[spine].set_visible(False)


def _render_response(data, outdir, plt):
    panels = (
        ('Input reaction', 'N', (
            ('R_input_N', 'input R', '#205b8d'),)),
        ('Weighted output displacement', 'mm', (
            ('q_out_mm', 'q_out', '#7256a4'),)),
        ('Signed weak force on fixed lower workpiece body', 'N', (
            ('material_body_Fy_N', 'material Fy', '#207a69'),
            ('regularization_body_Fy_N', 'Hu Fy', '#be6a28'),
            ('total_body_Fy_N', 'total Fy', '#205b8d'))),
        ('Unsigned distances to the saved Q1 boundary', 'mm', (
            ('tip_to_raster_boundary_mm', 'tip distance', '#7256a4'),
            ('minimum_boundary_distance_mm', 'all-boundary minimum', '#207a69'))),
    )
    figure, axes = plt.subplots(2, 2, figsize=(14, 11))
    try:
        for axis, (title, unit, fields) in zip(axes.flat, panels):
            for label, style, rows in _branches(data['timeline_rows']):
                for metric, metric_label, color in fields:
                    axis.plot([row['d_mm'] for row in rows],
                              [row[metric] for row in rows],
                              color=color, linestyle=style, marker='o',
                              markersize=4, linewidth=1.4,
                              markerfacecolor=color if style == '-' else 'white',
                              label=metric_label + ' / ' + label)
            _style_axis(axis, title, 'Prescribed mean input displacement (mm)', unit)
            axis.legend(fontsize=7.4, ncol=2 if len(fields) > 1 else 1,
                        frameon=False, loc='best')
        figure.suptitle('Circle-tip layout: saved cycle at alpha = 2.5e-7',
                       fontsize=16, fontweight='bold', y=.975)
        figure.text(.09, .915,
                    'r = 9 mm; centre (80, 40) mm; right boundary 92 mm; Lr = 80 mm; four source solves.\n'
                    'Lines join accepted samples in order. This association is not a new single full-cycle solve.',
                    fontsize=10, va='top', linespacing=1.6)
        figure.text(.09, .035,
                    'q_out is a weighted port displacement, not a gap. Fy is a signed lower-half weak resultant.\n'
                    'Distances are unsigned saved raster/Q1 observations, not analytic-circle clearance or contact proof.',
                    fontsize=8.5, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.09, right=.98, top=.835, bottom=.13,
                               hspace=.48, wspace=.28)
        figure.savefig(Path(outdir) / 'response.png', dpi=160)
    finally:
        plt.close(figure)


def _render_quality(data, outdir, plt):
    from matplotlib.ticker import MaxNLocator

    rows = data['timeline_rows']
    raw = data['raw_rows']
    timeline_x = [row['display_index'] for row in rows]
    raw_x = [row['raw_row_index'] for row in raw]
    figure, axes = plt.subplots(2, 2, figsize=(14, 11))
    try:
        axis = axes[0, 0]
        for key, label, color in (
                ('medium_min_J', 'all non-workpiece medium', '#205b8d'),
                ('right_medium_min_J', 'right medium strip', '#be6a28')):
            axis.plot(timeline_x, [row[key] for row in rows], 'o-',
                      color=color, markersize=4, linewidth=1.4, label=label)
        _style_axis(axis, 'Saved minimum J by medium region',
                    'Unified accepted display index', 'J (dimensionless)')
        axis.legend(fontsize=8, frameon=False)

        axis = axes[0, 1]
        for key, label, color in (
                ('medium_max_abs_Hu_per_mm', 'all non-workpiece medium', '#205b8d'),
                ('right_medium_max_abs_Hu_per_mm', 'right medium strip', '#be6a28')):
            axis.plot(timeline_x, [row[key] for row in rows], 'o-',
                      color=color, markersize=4, linewidth=1.4, label=label)
        _style_axis(axis, 'Saved maximum absolute Hu component',
                    'Unified accepted display index', 'max |Hu component| (1/mm)')
        axis.legend(fontsize=8, frameon=False)

        axis = axes[1, 0]
        axis.plot(raw_x, [row['convergence']['relative_residual'] for row in raw],
                  'o-', color='#205b8d', markersize=4, linewidth=1.3,
                  label='original accepted relative residual')
        axis.axhline(1e-9, color='#b54e45', linestyle='--', linewidth=1.2,
                     label='original tolerance 1e-9')
        axis.set_yscale('symlog', linthresh=1e-16)
        _style_axis(axis, 'Original accepted equilibrium diagnostic',
                    'All source accepts, including revalidated anchors',
                    'Relative residual; symlog (linear within +/-1e-16)')
        axis.legend(fontsize=8, frameon=False)

        axis = axes[1, 1]
        axis.plot(raw_x, [row['convergence']['constraint_residual'] for row in raw],
                  'o-', color='#207a69', markersize=4, linewidth=1.3,
                  label='original constraint residual')
        axis.plot(raw_x, [row['convergence']['constraint_bound'] for row in raw],
                  '--', color='#b54e45', linewidth=1.3,
                  label='original per-state constraint bound')
        axis.set_yscale('symlog', linthresh=1e-16)
        _style_axis(axis, 'Original mean-input constraint and bound',
                    'All source accepts, including revalidated anchors',
                    'mm; symlog (linear within +/-1e-16)')
        axis.legend(fontsize=8, frameon=False)
        for axis in axes.flat:
            axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=9))
        figure.suptitle('Alpha = 2.5e-7: saved field and convergence observations',
                       fontsize=16, fontweight='bold', y=.975)
        figure.text(.09, .915,
                    'Upper panels: unified display order, retaining both loading and unloading states.\n'
                    'Lower panels: every original source accept, including each fresh anchor diagnostic.',
                    fontsize=10, va='top', linespacing=1.6)
        figure.text(.09, .035,
                    'All zero, tiny signed, and nonmonotone values are retained. Symlog changes only axis coordinates.\n'
                    'Medium-region Hu is not the full-model maximum; no new acceptance or qualification criterion is applied.',
                    fontsize=8.5, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.105, right=.98, top=.835, bottom=.13,
                               hspace=.50, wspace=.31)
        figure.savefig(Path(outdir) / 'quality.png', dpi=160)
    finally:
        plt.close(figure)


def _markdown(data, outdir, root):
    counts = data['counts']
    lines = [
        '# alpha=2.5e-7 尖端对向圆形工件：已有加载与卸载路径人工检查页', '',
        '本页关联ALPHA1与AUNLOAD1–3共4段普通标量记录；各段来自原独立窗口，不构成一次新的从零完整周期求解。',
        '布置保持半径9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm、alpha=2.5e-7；原物理条件、数值门和来源资格保持。', '',
        f"原来源接受行 **{counts['raw_rows']}**，统一展示行 **{counts['timeline_rows']}**，"
        f"合并相邻重复锚 **{counts['merged_boundary_anchors']}**，同位移对照 **{counts['same_input_pairs']}**。", '',
        '仅相邻子段边界锚的原状态标量和SHA逐位一致时合并展示；不一致则保留两行并记录差异，不新增科学相等门。每份原始行、fresh anchor收敛诊断、来源及计算计数均保留；不按输入位移去重。',
        'display branch仅用于绘图；raw leg保留原origin、loading、resume_origin或unloading，不能用显示分支改写原来源。', '',
        '## 加载与卸载的实际保存标量', '',
        '![反力、输出位移、工件Fy及无符号距离](response.png)', '',
        '实线为加载显示分支，虚线为卸载显示分支。虚线为显示连续性复用原转折点；该操作不新增状态或同位移对照。连线只连接原采样点，不插值。',
        'q_out为加权输出端口位移，不是间隙。工件material／Hu／total Fx/Fy均为固定工件下半部的有符号弱式合力，不作镜像倍增，不等同局部压力或合格夹持力。',
        'tip与全Q1边界距离均无符号，基于保存的离散边界；不能当作解析圆间隙或接触／释放证明。', '',
        '| 展示行 | 显示分支 | 原leg（按来源） | d mm | R N | q_out mm | 工件总Fy N | 尖端距离 mm | 全Q1最小距 mm | 来源 |',
        '|---:|---|---|---:|---:|---:|---:|---:|---:|---|',
    ]
    for row in data['timeline_rows']:
        source_text = '; '.join(
            f"{source['segment']}:{source['source_row_index']}"
            for source in row['sources'])
        raw_legs = '; '.join(
            data['raw_rows'][source['raw_row_index']]['raw_leg']
            for source in row['sources'])
        values = [row[key] for key in (
            'd_mm', 'R_input_N', 'q_out_mm', 'total_body_Fy_N',
            'tip_to_raster_boundary_mm', 'minimum_boundary_distance_mm')]
        lines.append(f"| {row['display_index']} | {row['display_branch']} | {raw_legs} | "
                     + ' | '.join(map(_number, values)) + ' | ' + source_text + ' |')
    lines += ['', '## 原场与收敛观察', '',
        '![介质与右条带J、Hu及原收敛诊断](quality.png)', '',
        '上排横轴为统一展示序号；下排横轴为全部来源接受行号，包含每次续算重新核对的锚。两种序号不能互换。',
        '上排分别展示全非工件介质与右条带原minimum J和max|Hu component|；不把介质区Hu与全模型最大Hu混列，也不要求其相等。',
        '下排保留各来源原relative residual、constraint residual及原逐态constraint bound；原残差门为1e-9。symlog的±1e-16仅为坐标显示的线性区，不是截断、数值地板或新门。零值、微小负值及非单调值保持原值。',
        '下表保留每段原计数与原异常／拒绝历史的完整JSON链接；统一展示不扣除重复锚的实际计算工作。', '',
        '| 原段 | 原计数（不扣重复锚） | 原summary | 原收敛记录 | 原人工页 |',
        '|---|---|---|---|---|',
    ]
    for segment in data['segments']:
        paths = segment['paths']
        count_text = '; '.join(f'{key}={value}' for key, value in segment['counts'].items())
        links = []
        for key, label in (('summary', 'summary'), ('convergence', 'convergence'), ('manual', '人工页')):
            links.append(f'[{label}](<{_link(root, outdir, paths[key])}>)')
        lines.append('| ' + segment['segment'] + ' | ' + count_text + ' | '
                     + ' | '.join(links) + ' |')
    lines += ['', '原4段计数汇总（计数求和、最大深度取原最大值，不扣重复锚）：', '',
              '```json', json.dumps(data['convergence_totals'], ensure_ascii=False,
                                   indent=2, allow_nan=False), '```', '',
              '原拒绝／失败历史摘录（保留原值及来源；不改变原判定）：', '',
              '```json', json.dumps(data['exceptions'], ensure_ascii=False,
                                   indent=2, allow_nan=False), '```', '',
        '## 同输入的原值与差值', '',
        '仅对已有原目标进行同输入配对，每对保留原13项标量；其余原37项观察仍完整保存在统一响应。二分态和重新核验的锚不新增配对；不插值，不引入相等性、恢复率、零残力、滞回能量或稳定性门。',
        '下表差值定义为unloading − loading/origin参考。初始零态的对照来源若为origin，其raw leg仍为origin，不伪造loading。配对表用17位有效数字显示原值与差值，曲线重叠不代表绝对相等或无滞回。', '']
    for pair in data['same_input_pairs']:
        lines += [f"### d = {_number(pair['d_mm'])} mm", '',
            f"展示行 {pair['loading_display_index']} → {pair['unloading_display_index']}；"
            f"raw leg：{pair['loading_raw_leg']} → {pair['unloading_raw_leg']}。", '']
        if 'reference_role' in pair:
            lines += ['原对照角色：`' + str(pair['reference_role']) + '`。', '']
        lines += ['| 原指标 | loading/origin参考原值 | unloading原值 | unloading−参考 |',
                  '|---|---:|---:|---:|']
        for metric, values in pair['metrics'].items():
            lines.append('| `' + metric + '` | ' + ' | '.join(
                format(values[key], '.17g') for key in
                ('loading_value', 'unloading_value', 'unloading_minus_loading')) + ' |')
        lines.append('')
    lines += ['## 4段既有实际变形动画', '',
        '以下仅提供已有GIF链接。程序只依据既有声明核对文件大小，不打开、解码、抽帧、复制、重哈希或拼接旧媒体。动画仍属于各自原段，不伪装成一次完整新路径动画。',
        '原图／动画的×1实际变形及其原箭头尺度保持。原图的可见性限制与QA记录保留，本轮不修补已关闭窗口的旧图。', '',
        '| 原段 | 既有动画 | stat大小 bytes |', '|---|---|---:|']
    for segment in data['segments']:
        lines.append('| ' + segment['segment'] + ' | [原实际变形GIF](<'
                     + _link(root, outdir, segment['paths']['GIF']) + '>) | '
                     + str(segment['GIF_bytes']) + ' |')
    reference = 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_reference_001/RESULTS.md'
    lines += ['', '## 原单峰独立参考', '',
        '[AREF1原独立参考记录](<' + _link(root, outdir, reference) + '>)仅覆盖当前alpha的原加载1.06 mm／global12单态及原PORT方向；本页不读取其科学输出，也不迁移为卸载或全路径资格。', '',
        '## 本轮边界与后续判断', '',
        '只新增两张普通标量图及关联记录，不新增构模、F/T、HP、平衡求解、测试、物理目标、默认HF源码或API关联。',
        '输入回程到零和跨子段统一展示，不授整条路径独立参考、压力、有效夹持、自由释放、稳定性、网格／域宽或HF5资格。原成功、失败、视觉QA和参考历史均保持。',
        '原记录保留的极小残余值不会截为零；图中接近零或曲线重合不新增归零／恢复结论。本轮不进行旧alpha与新alpha的跨参数比较；下一步应依据实际汇总结果单独记录和规划。', '',
        '### 原数据范围说明', '']
    scope = data['scope']
    if isinstance(scope, dict):
        for key, value in scope.items():
            lines.append('- **' + str(key) + '：** ' + str(value))
    else:
        lines.append(str(scope))
    return '\n'.join(lines).rstrip() + '\n'


def render(data, outdir, root):
    """Write exactly two new PNGs and one Markdown page from passed dictionaries."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    with plt.rc_context({'font.family': 'DejaVu Sans', 'axes.edgecolor': '#6b7280',
                         'axes.labelcolor': '#263447', 'text.color': '#263447',
                         'xtick.color': '#4b5563', 'ytick.color': '#4b5563',
                         'figure.facecolor': 'white', 'axes.facecolor': 'white'}):
        _render_response(data, outdir, plt)
        _render_quality(data, outdir, plt)
    with (Path(outdir) / 'REVIEW.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_markdown(data, outdir, root))
