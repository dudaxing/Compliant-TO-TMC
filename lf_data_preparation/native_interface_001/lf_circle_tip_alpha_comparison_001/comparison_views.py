"""Two ordinary-scalar views of two already saved alpha responses.

Only passed dictionaries are used. Existing paths become links; no old JSON,
science, CSV, image or animation payload is opened by this module.
"""
import json
import os
from pathlib import Path


DESIGNS = (('baseline', 'old alpha=5e-7', '#205b8d'),
           ('new', 'new alpha=2.5e-7', '#be6a28'))


def _link(root, outdir, path):
    return os.path.relpath(Path(root)/path, outdir).replace('\\', '/')


def _rows(data, source):
    return [item['row'] for item in data['raw_values'] if item['source'] == source]


def _branches(rows):
    loading = [row for row in rows if row['display_branch'] in ('origin', 'loading')]
    unloading = [row for row in rows if row['display_branch'] == 'unloading']
    # Reuse the actual turning point solely to connect the plotted branches.
    # This creates neither a state nor another cross-alpha comparison pair.
    if unloading and loading:
        unloading = [loading[-1]] + unloading
    return (('-', loading), ('--', unloading))


def _axis(axis, title, xlabel, ylabel):
    from matplotlib.ticker import FuncFormatter

    axis.set_title(title, loc='left', fontsize=11, fontweight='bold', pad=11)
    axis.set_xlabel(xlabel, fontsize=9)
    axis.set_ylabel(ylabel, fontsize=9)
    axis.tick_params(labelsize=8)
    axis.grid(alpha=.22, linewidth=.7)
    # Explicit tick labels avoid scientific offset/title collisions.
    axis.yaxis.set_major_formatter(FuncFormatter(
        lambda value, position: '0' if value == 0 else format(value, '.2g')))
    for spine in ('top', 'right'):
        axis.spines[spine].set_visible(False)


def _response(data, outdir, plt):
    from matplotlib.lines import Line2D

    panels = (
        ('Signed input reaction', 'N', (('R_input_N', 'R', 'o'),)),
        ('Weighted output displacement', 'mm', (('q_out_mm', 'q_out', 'o'),)),
        ('Signed material force on lower body', 'N', (('material_body_Fy_N', 'material Fy', 'o'),)),
        ('Signed Hu force on lower body', 'N', (('regularization_body_Fy_N', 'Hu Fy', 'o'),)),
        ('Signed total force on lower body', 'N', (('total_body_Fy_N', 'total Fy', 'o'),)),
        ('Unsigned saved Q1 boundary distances', 'mm', (
            ('tip_to_raster_boundary_mm', 'tip', 'o'),
            ('minimum_boundary_distance_mm', 'all-boundary minimum', 's'))),
    )
    figure, axes = plt.subplots(3, 2, figsize=(14, 14))
    try:
        for axis, (title, unit, fields) in zip(axes.flat, panels):
            for source, label, color in DESIGNS:
                for style, rows in _branches(_rows(data, source)):
                    for metric, metric_label, marker in fields:
                        axis.plot([row['d_mm'] for row in rows], [row[metric] for row in rows],
                            color=color, linestyle=style, marker=marker, markersize=3.8,
                            linewidth=1.3, markerfacecolor=color if style == '-' else 'white')
            _axis(axis, title, 'Prescribed mean input displacement (mm)', unit)
            if len(fields) > 1:
                axis.legend(handles=[Line2D([], [], color='#596270', marker=marker,
                    linestyle='None', label=label) for metric, label, marker in fields],
                    fontsize=8, frameon=False)
        handles = [Line2D([], [], color=color, linewidth=1.7, label=label)
                   for source, label, color in DESIGNS]
        handles += [Line2D([], [], color='#596270', marker='o', linestyle=style,
                    markerfacecolor='#596270' if style == '-' else 'white', label=label)
                    for style, label in (('-', 'loading/origin display'), ('--', 'unloading display'))]
        figure.suptitle('Saved circle-tip responses: two alpha values',
            fontsize=16, fontweight='bold', y=.98)
        figure.text(.09, .943,
            'r9 mm; centre (80,40) mm; right92 mm; Lr80 mm. Old:14 source solves; new:4 source solves.\n'
            'Only corresponding original targets are compared. Lines connect saved samples; no interpolation.',
            fontsize=10, va='top', linespacing=1.5)
        figure.legend(handles=handles, loc='upper center', bbox_to_anchor=(.53, .895),
            ncol=4, fontsize=8.5, frameon=False)
        figure.text(.09, .03,
            'q_out is not a gap. Lower-body weak forces are signed and are not pressure or effective grip.\n'
            'Unsigned Q1 distances may overlay exactly; visually overlapping responses need not be equal.',
            fontsize=8.5, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.09, right=.98, top=.84, bottom=.11, hspace=.48, wspace=.29)
        figure.savefig(Path(outdir)/'response.png', dpi=160)
    finally:
        plt.close(figure)


def _quality(data, outdir, plt):
    from matplotlib.lines import Line2D
    from matplotlib.ticker import MaxNLocator

    figure, axes = plt.subplots(3, 2, figsize=(14, 14))
    try:
        for axis, title, unit, fields in (
            (axes[0, 0], 'Minimum J by saved medium region', 'J',
                (('medium_min_J', 'all non-workpiece medium', '-'),
                 ('right_medium_min_J', 'right medium strip', '--'))),
            (axes[0, 1], 'Maximum absolute Hu component by region', '1/mm',
                (('medium_max_abs_Hu_per_mm', 'all non-workpiece medium', '-'),
                 ('right_medium_max_abs_Hu_per_mm', 'right medium strip', '--'))),
        ):
            for source, label, color in DESIGNS:
                rows = _rows(data, source)
                x = [row['convergence']['original_target_index'] for row in rows]
                for field, region, style in fields:
                    axis.plot(x, [row[field] for row in rows], color=color,
                        linestyle=style, marker='o', markersize=3.5, linewidth=1.3)
            _axis(axis, title, 'Original target index (loading then unloading)', unit)
            axis.legend(handles=[Line2D([], [], color='#596270', linestyle=style,
                label=region) for field, region, style in fields], fontsize=8, frameon=False)
        for panel_row, (source, label, color) in enumerate(DESIGNS, start=1):
            raw = data['sources'][source]['original']['raw_rows']
            x = [row['raw_row_index'] for row in raw]
            axis = axes[panel_row, 0]
            axis.plot(x, [row['convergence']['relative_residual'] for row in raw],
                'o-', color=color, markersize=3.5, linewidth=1.2, label='original accepted residual')
            axis.axhline(1e-9, color='#a64b47', linestyle='--', linewidth=1.1,
                label='original tolerance 1e-9')
            axis.set_yscale('symlog', linthresh=1e-16)
            _axis(axis, label+f': residual / {len(raw)} raw accepts',
                'This source only: all raw accept indices, including anchors', 'Relative residual; symlog')
            axis.legend(fontsize=8, frameon=False)
            axis = axes[panel_row, 1]
            axis.plot(x, [row['convergence']['constraint_residual'] for row in raw],
                'o-', color=color, markersize=3.5, linewidth=1.2, label='original signed constraint residual')
            axis.plot(x, [row['convergence']['constraint_bound'] for row in raw],
                '--', color='#a64b47', linewidth=1.1, label='original per-state bound')
            axis.set_yscale('symlog', linthresh=1e-16)
            _axis(axis, label+': constraint and bound',
                'This source only: all raw accept indices, including anchors', 'mm; symlog')
            axis.legend(fontsize=8, frameon=False)
        for axis in axes.flat:
            axis.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=8))
        figure.suptitle('Saved quality observations with separate source histories',
            fontsize=16, fontweight='bold', y=.98)
        figure.text(.095, .943,
            'Top:20 matched original targets. Middle:old source raw sequence. Bottom:new source raw sequence.\n'
            'Raw indices are separate computation histories, not paired solve times or an alpha performance test.',
            fontsize=10, va='top', linespacing=1.5)
        figure.legend(handles=[Line2D([], [], color=color, linewidth=1.7, label=label)
            for source, label, color in DESIGNS], loc='upper center',
            bbox_to_anchor=(.53, .895), ncol=2, fontsize=8.5, frameon=False)
        figure.text(.095, .03,
            'Zero, tiny signed and nonmonotone values remain unchanged. Symlog is linear within +/-1e-16 only for display.\n'
            'Region Hu is not the full-model maximum. Original diagnostics and bounds do not create new qualification.',
            fontsize=8.5, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.095, right=.98, top=.84, bottom=.11, hspace=.52, wspace=.31)
        figure.savefig(Path(outdir)/'quality.png', dpi=160)
    finally:
        plt.close(figure)


def _markdown(data, outdir, root):
    lines = ['# 两种alpha的已有圆形工件响应：人工检查页', '',
        '本页只比较两份既存普通统一JSON。旧alpha=5e-7来自14段原求解，新alpha=2.5e-7来自4段；不是两次本轮新求解，原来源时钟、锚复核和计算计数不能作为纯alpha性能。', '',
        '![反力、位移、工件Fy与无符号距离](response.png)', '',
        '颜色区分alpha，实线/实心点为loading或origin显示分支，虚线/空心点为卸载。转折连接复用真实峰值点，不新增状态或配对；不插值。各Fy分面避免堆叠图例；距离用圆/方点区分，重合时仍保原值。',
        'q_out为加权端口位移；工件力是固定下半模型有符号material/Hu/total弱式合力，未镜像加倍，不是压力或合格夹持力。unsigned Q1距离不是解析圆间隙或接触/释放证明。', '',
        '![原介质与右域质量及独立来源收敛序号](quality.png)', '',
        '上排为同20原目标的原介质/右域J和Hu。中排只用旧来源全部raw接受序号；下排只用新来源全部raw接受序号，保留所有fresh anchor诊断，不能按横坐标把33/23行当成同一次计算或计算时间。',
        '残差原门1e-9及原逐态constraint bound保持；有符号constraint与零值完整保留。symlog的±1e-16只是显示线性区，不是数值地板或新门；介质区Hu与全模型最大值不同。', '',
        '## 来源、原资格与可比性', '',
        '| 来源 | 普通统一JSON | 原人工页/变形入口 | 原页stat bytes | 原计数 |',
        '|---|---|---|---:|---|']
    for source, label, color in DESIGNS:
        item = data['sources'][source]
        lines.append('| '+label+' | [原统一记录](<'+_link(root, outdir, item['path'])+'>) | '
            '[原人工页](<'+_link(root, outdir, item['manual_path'])+'>) | '+str(item['manual_bytes'])
            +' | `'+json.dumps(item['original']['counts'], ensure_ascii=False)+'` |')
    lines += ['', '这里只stat/链接两份原人工页；原页已有14段/4段实际变形入口，本程序没有打开、读取、解码、复制、重哈希或拼接旧媒体，也不新绘结构。', '',
        '原task、37字段、raw锚/二分诊断、计数、异常和来源完整保留在comparison.json的sources.original中。40条原值在raw_values，20组原目标配对及260差量在pairs。', '',
        '可比性与声明的参数/元数据差异：', '', '```json',
        json.dumps(data['compatibility'], ensure_ascii=False, indent=2, allow_nan=False), '```', '',
        '初始零态即使同SHA也不跨alpha合并或迁移HP。AREF1仅覆盖新alpha原加载1.06/global12单态及原PORT方向；旧/新任何选定态参考都不授本次全路径或卸载资格。', '',
        '## 原目标逐项原值与描述性差量', '',
        '仅按原global target index、display branch及原d匹配；origin原leg保持origin，加载/卸载同d不混配。每组同原13项，差量=new−baseline。下表17位有效数字；图中重叠不等于绝对相等，不新增归零、可逆、恢复率、耗散或alpha独立性门。', '']
    for pair in data['pairs']:
        old = data['raw_values'][pair['baseline_raw_index']]['row']
        new = data['raw_values'][pair['new_raw_index']]['row']
        lines += [f"### 原目标 {pair['global_index']} · {pair['display_branch']} · d={pair['d_mm']:.17g} mm", '',
            f"原leg：`{old['raw_leg']}` → `{new['raw_leg']}`；SHA：`{pair['baseline_state_sha256']}` / `{pair['new_state_sha256']}`。", '',
            '| 原指标 | 旧alpha原值 | 新alpha原值 | 新减旧 |', '|---|---:|---:|---:|']
        for metric, values in pair['metrics'].items():
            lines.append('| `'+metric+'` | '+' | '.join(format(values[key], '.17g')
                for key in ('baseline_value','new_value','new_minus_baseline'))+' |')
        lines.append('')
    lines += ['## 范围与后续', '',
        '本轮仅普通记录和两张标量图，无新构模/F/T/HP/平衡求解/测试、默认HF改动或API关联。原完整字段和微小有符号量不裁零，不据两条已回零路径授释放、稳定、有效夹持、网格/域收敛、alpha独立性、完整路径独立参考或HF5资格。',
        '按实际差量决定后续，不预判参数影响大小；原科学结果、失败/拒绝记录、参考和QA历史均保持。', '',
        '### 原范围说明', '', json.dumps(data['scope'], ensure_ascii=False, indent=2, allow_nan=False), '']
    return '\n'.join(lines).rstrip()+'\n'


def render(data, outdir, root):
    """Write exactly response.png, quality.png and REVIEW.md from passed dicts."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    with plt.rc_context({'font.family':'DejaVu Sans', 'figure.facecolor':'white',
                         'axes.facecolor':'white', 'axes.edgecolor':'#6b7280',
                         'text.color':'#263447', 'axes.labelcolor':'#263447',
                         'xtick.color':'#4b5563', 'ytick.color':'#4b5563'}):
        _response(data, outdir, plt)
        _quality(data, outdir, plt)
    with (Path(outdir)/'REVIEW.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_markdown(data, outdir, root))
