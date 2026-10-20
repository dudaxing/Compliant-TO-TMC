"""One alpha-comparison figure from dictionaries already read by the wrapper.

The baseline is a composed historical loading path, whereas the new trial starts
from zero.  This is a descriptive parameter experiment, not an alpha-independent
qualification or a controlled comparison of total runtime.
"""
from copy import deepcopy
import json
import os
from pathlib import Path


METRICS = (
    'R_input_N', 'q_out_mm', 'tip_x_mm', 'tip_y_mm',
    'tip_to_raster_boundary_mm', 'minimum_boundary_distance_mm',
    'solid_min_J', 'medium_min_J', 'solid_Green_principal_min',
    'solid_Green_principal_max', 'medium_max_abs_Hu_per_mm',
    'right_medium_min_J', 'right_medium_max_J',
    'right_medium_max_abs_Hu_per_mm', 'right_medium_Green_principal_min',
    'right_medium_Green_principal_max', 'right_medium_max_nodal_displacement_mm',
    'total_body_Fx_N', 'total_body_Fy_N', 'material_body_Fx_N',
    'material_body_Fy_N', 'regularization_body_Fx_N', 'regularization_body_Fy_N',
)
BASELINE_PATH = ('lf_data_preparation/native_interface_001/'
                 'lf_circle_tip_path_001/run_001/unified_response.json')
NEW_LABEL = 'wave_circle_tip_alpha1'
SCOPE = (
    'Descriptive saved ordinary observations: baseline alpha=5e-7 versus new '
    'alpha=2.5e-7, with the other physical conditions fixed by the execution '
    'protocol. Historical baseline loading was composed from separately solved '
    'segments; the new case is one zero-start load-only run. Original source '
    'legs, accepted bisection states, residuals and computational work are '
    'retained. No interpolation, alpha-independent gate, pressure, effective '
    'clamp, stability, release, full-path-reference or HF5 qualification is '
    'introduced. An old reference does not qualify the new alpha.'
)


def _same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return (isinstance(a, (float, int)) and isinstance(b, (float, int))
                and float(a).hex() == float(b).hex())
    return type(a) is type(b) and a == b


def _number(value):
    return format(value, '.17g')


def _diagnostic_differences(old, new):
    return {key: new[key] - value for key, value in old.items()
            if key in new and type(value) in (int, float)
            and type(new[key]) in (int, float)}


def _comparison(baseline, summary, convergence):
    old_rows = [row for row in baseline['timeline_rows']
                if row['display_branch'] in ('origin', 'loading')
                and row['convergence']['is_original_target'] is True]
    if (len(old_rows) != 13
            or [row['original_target_index'] for row in old_rows] != list(range(13))):
        raise ValueError('The fixed historical thirteen-target loading baseline differs')
    new_rows = summary['rows']
    accepted = convergence['accepted_states']
    if (summary['accepted_states'] != len(new_rows)
            or len(new_rows) != len(accepted)):
        raise ValueError('New viewer and convergence accepted-state counts differ')
    joined = []
    originals = []
    for index, (row, diagnostic) in enumerate(zip(new_rows, accepted)):
        if row['index'] != index:
            raise ValueError('New summary does not retain accepted-state order')
        for row_key, diagnostic_key in (
                ('state_sha256', 'state_sha256'), ('d_mm', 'd'),
                ('R_input_N', 'R_input'), ('q_out_mm', 'q_out'),
                ('original_target_index', 'original_target_index'), ('leg', 'leg')):
            if not _same(row[row_key], diagnostic[diagnostic_key]):
                raise ValueError('New summary/convergence state identity differs: '
                                 + str(index) + '/' + row_key)
        joined.append(dict(accepted_index=index, row=deepcopy(row),
                           convergence=deepcopy(diagnostic)))
        if diagnostic['is_original_target'] is True:
            originals.append(joined[-1])
    if ([entry['row']['original_target_index'] for entry in originals]
            != list(range(13))):
        raise ValueError('New original targets do not match the thirteen-target contract')
    pairs = []
    for old, entry in zip(old_rows, originals):
        new = entry['row']
        if not _same(old['d_mm'], new['d_mm']):
            raise ValueError('Original-target displacement differs; no interpolation permitted')
        metrics = {key: dict(baseline_value=old[key], new_value=new[key],
                            new_minus_baseline=new[key] - old[key]) for key in METRICS}
        pairs.append(dict(original_target_index=new['original_target_index'],
            d_mm=new['d_mm'], baseline_display_index=old['display_index'],
            baseline_raw_leg=old['raw_leg'], new_accepted_index=entry['accepted_index'],
            new_raw_leg=new['leg'], baseline_state_sha256=old['state_sha256'],
            new_state_sha256=new['state_sha256'], baseline_sources=deepcopy(old['sources']),
            metrics=metrics, baseline_convergence=deepcopy(old['convergence']),
            new_convergence=deepcopy(entry['convergence']),
            diagnostic_new_minus_baseline=_diagnostic_differences(
                old['convergence'], entry['convergence'])))
    return dict(schema_version='saved-circle-alpha-comparison-1.0', scope=SCOPE,
        baseline_alpha=5e-7, new_alpha=2.5e-7,
        physical_context='r9 mm; centre (80,40) mm; right92 mm; Lr80 mm; lower-half model',
        counts=dict(baseline_rows=len(old_rows), new_rows=len(new_rows),
                    matched_pairs=len(pairs), new_original_target_rows=len(originals),
                    new_bisection_rows=len(new_rows) - len(originals)),
        baseline_source=dict(path=BASELINE_PATH,
            scope=deepcopy(baseline['scope']),
            historical_full_path_counts=deepcopy(baseline['counts']),
            counts_scope='Historical whole-path counts are source context, not loading-only CPU costs.'),
        baseline_rows=deepcopy(old_rows), new_rows=joined, pairs=pairs,
        new_summary=deepcopy(summary), new_convergence=deepcopy(convergence),
        metric_fields=list(METRICS), difference_definition='new minus historical baseline',
        reference_scope='Only original historical states retain their existing reference; new alpha has no new HP reference.',
        cost_scope='Segmented baseline versus one zero-start run; total counts or CPU time are not a pure-alpha performance comparison.')


def _figure(data, outdir):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    from matplotlib.ticker import FuncFormatter

    panels = (
        ('Input reaction', 'N', (('R_input_N', 'input R', '#205b8d'),)),
        ('Weighted output displacement; not a gap', 'mm',
         (('q_out_mm', 'q_out', '#7256a4'),)),
        ('Signed lower-workpiece global Fy', 'N', (
            ('total_body_Fy_N', 'total Fy', '#205b8d'),
            ('material_body_Fy_N', 'material Fy', '#207a69'),
            ('regularization_body_Fy_N', 'Hu Fy', '#be6a28'))),
        ('Unsigned saved raster/Q1 distances', 'mm', (
            ('tip_to_raster_boundary_mm', 'tip distance', '#7256a4'),
            ('minimum_boundary_distance_mm', 'all-boundary minimum', '#207a69'))),
        ('Medium-region minimum J', 'J (dimensionless)', (
            ('medium_min_J', 'all non-workpiece medium', '#205b8d'),
            ('right_medium_min_J', 'right medium strip', '#be6a28'))),
        ('Medium-region maximum absolute Hu component', '1/mm', (
            ('medium_max_abs_Hu_per_mm', 'all non-workpiece medium', '#205b8d'),
            ('right_medium_max_abs_Hu_per_mm', 'right medium strip', '#be6a28'))),
    )
    styles = ((data['baseline_rows'], 'alpha=5e-7 historical', '-', 'o'),
              ([entry['row'] for entry in data['new_rows']],
               'alpha=2.5e-7 new zero-start', '--', 's'))
    figure, axes = plt.subplots(3, 2, figsize=(16, 15))
    try:
        for axis, (title, unit, fields) in zip(axes.flat, panels):
            for rows, alpha_label, style, marker in styles:
                for key, metric_label, color in fields:
                    axis.plot([row['d_mm'] for row in rows], [row[key] for row in rows],
                              color=color, linestyle=style, marker=marker,
                              markerfacecolor=color if style == '-' else 'white',
                              markersize=3.8, linewidth=1.3,
                              label=metric_label + ' / ' + alpha_label)
            axis.set_title(title, loc='left', fontsize=11, fontweight='bold', pad=12)
            axis.set_xlabel('Prescribed mean input displacement (mm)', fontsize=9)
            axis.set_ylabel(unit, fontsize=9)
            axis.yaxis.set_major_formatter(FuncFormatter(
                lambda value, position: '0' if value == 0 else format(value, '.2g')))
            axis.tick_params(labelsize=8)
            axis.grid(alpha=.22)
            axis.legend(fontsize=7.2, ncol=2 if len(fields) > 1 else 1,
                        frameon=False, loc='best')
            for side in ('top', 'right'):
                axis.spines[side].set_visible(False)
        figure.suptitle('Circle-tip layout: one changed regularization coefficient',
                       fontsize=17, fontweight='bold', y=.98)
        figure.text(.08, .935,
                    'r9 mm; centre (80,40) mm; right92 mm; Lr80 mm. All other physical conditions retained.\n'
                    'Historical thirteen-target loading baseline versus one new zero-start load-only run. All new accepted bisection states remain visible.',
                    fontsize=10.3, va='top', linespacing=1.6)
        figure.text(.08, .035,
                    'Line connections show recorded order only; no mechanical interpolation. Exact paired values and small differences remain in the tables.\n'
                    'Overlapping curves do not establish equality or alpha independence. Medium Hu is not full-model Hu; nodal weak Fy is not pressure.\n'
                    'The new alpha does not inherit the old selected-state HP reference or acquire effective-grip, release, stability, or HF5 qualification.',
                    fontsize=9, va='bottom', linespacing=1.5)
        figure.subplots_adjust(left=.08, right=.98, top=.865, bottom=.13,
                               hspace=.46, wspace=.27)
        figure.savefig(Path(outdir) / 'comparison.png', dpi=160)
    finally:
        plt.close(figure)


def _markdown(data, outdir, root):
    counts = data['counts']
    lines = ['# 圆形尖端对向布置：α单参数加载对照', '',
        '新试算仅将α从5e-7降至2.5e-7。r9 mm、圆心(80,40) mm、右域界92 mm、Lr80 mm及其余物理条件按原执行合同保持。',
        '基线来自已有分段加载关联后的13个原目标；新试算从零一次执行load_only。两者的来源组织不同，不以总CPU或计数宣称纯α性能变化。', '',
        f"原基线{counts['baseline_rows']}态，新接受态{counts['new_rows']}态，精确同目标同输入配对{counts['matched_pairs']}组；"
        f"新二分接受态{counts['new_bisection_rows']}态全部保留。", '',
        '![原α与新α的六类原值对照](comparison.png)', '',
        '实线圆点：原α=5e-7；虚线方点：新α=2.5e-7。图仅连接原接受点，不插值。零、小负值及非单调量均保留；曲线重合不证明绝对相等或α独立。',
        'R为下半模型输入反力，q_out是加权输出端口位移，不是间隙。工件Fx／Fy是下半固定工件的有符号弱式合力；不镜像倍增，不解释为局部压力或合格夹持力。',
        '距离为离散Q1边界无符号距离，不能代替解析圆的有符号间隙；介质区max|Hu|不代表全模型max|Hu|。', '',
        '## 新试算全部接受态', '',
        '| 接受行 | 原目标 | 原目标态 | raw leg | d mm | R N | q_out mm | 原相对残差 | 原约束残差 mm | 原约束界 mm | 状态SHA |',
        '|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|']
    for entry in data['new_rows']:
        row, diagnostic = entry['row'], entry['convergence']
        values = [row['d_mm'], row['R_input_N'], row['q_out_mm'],
                  diagnostic['relative_residual'], diagnostic['constraint_residual'],
                  diagnostic['constraint_bound']]
        lines.append(f"| {entry['accepted_index']} | {row['original_target_index']} | "
                     + str(diagnostic['is_original_target']) + ' | ' + row['leg'] + ' | '
                     + ' | '.join(map(_number, values)) + ' | `'
                     + row['state_sha256'] + '` |')
    lines += ['', '## 精确同输入原值及差值', '',
        '下表统一采用new − historical baseline，不计算相对变化率，避免零位与近零分母。表内17位有效数字，原始完整行和诊断同时保存在comparison.json。',
        '最初零态的raw leg保持origin；子段的原resume_origin与全部来源也原样保留，不用绘图身份改写来源。', '']
    for pair in data['pairs']:
        lines += [f"### 原目标{pair['original_target_index']}，d={_number(pair['d_mm'])} mm", '',
            f"原显示行{pair['baseline_display_index']}（raw leg `{pair['baseline_raw_leg']}`）"
            f"与新接受行{pair['new_accepted_index']}（raw leg `{pair['new_raw_leg']}`）。", '',
            '| 原物理标量 | 原α原值 | 新α原值 | 新−原 |', '|---|---:|---:|---:|']
        for key, values in pair['metrics'].items():
            lines.append('| `' + key + '` | ' + ' | '.join(
                _number(values[field]) for field in
                ('baseline_value', 'new_value', 'new_minus_baseline')) + ' |')
        lines += ['', '对应原收敛诊断（来源不同，不作纯α成本结论）：', '',
                  '```json', json.dumps(dict(
                      baseline=pair['baseline_convergence'], new=pair['new_convergence'],
                      new_minus_baseline=pair['diagnostic_new_minus_baseline']),
                      ensure_ascii=False, indent=2, allow_nan=False), '```', '']
    baseline_link = os.path.relpath(Path(root) / BASELINE_PATH, outdir).replace('\\', '/')
    lines += ['## 收敛、实际变形与来源', '',
        '[已有分段路径普通基线JSON](<' + baseline_link + '>)；只使用其origin/loading的13个原目标。',
        '[新实际保存态普通摘要](../view/' + NEW_LABEL + '/summary.json)；'
        '[新原始收敛普通JSON](../convergence/convergence.json)；'
        '[新收敛图](../convergence/convergence.png)；'
        '[新实际变形动画](../view/' + NEW_LABEL + '/actual_states.gif)。', '',
        '上述新动画路径及新观察产品由原viewer生成，comparison模块不打开、解码或哈希任何媒体。所有新接受态与二分态按原顺序保留，原拒绝／失败历史与计算计数见新收敛JSON。', '',
        '新试算原计数如下，不扣除真实内部工作，不拿来与分段基线作纯α性能排名：', '',
        '```json', json.dumps(data['new_convergence']['counts'], ensure_ascii=False,
                             indent=2, allow_nan=False), '```', '',
        '## 资格与后续判断', '',
        '本对照模块不导入力学入口、不重新读取JSON／数组、不新增F/T、HP或平衡求解，只处理包装已解析的普通dict并生成一张新图。',
        '旧α峰值的已有HP只覆盖原α原保存态，不能迁移给新α。新生产收敛不自动授独立参考、α独立、压力、有效夹持、自由释放、稳定性、完整路径或HF5资格。',
        '需依据实际同输入差值和局部场变化决定下一步；不预设参数敏感或不敏感，不用正则化系数变化掩盖原物理限制。', '',
        data['scope'], '']
    return '\n'.join(lines).rstrip() + '\n'


def render(baseline, summary, convergence, outdir, root, checkpoint):
    """Write one PNG, comparison JSON and Markdown using only supplied dicts."""
    checkpoint('alpha_comparison_projection_started')
    data = _comparison(baseline, summary, convergence)
    checkpoint('alpha_comparison_projection_completed')
    output = Path(outdir)
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'comparison.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    checkpoint('alpha_comparison_plot_started')
    _figure(data, output)
    checkpoint('alpha_comparison_plot_completed')
    with (output / 'REVIEW.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_markdown(data, output, root))
    checkpoint('alpha_comparison_written')
    return dict(status='pass', baseline_rows=13, new_rows=len(summary['rows']),
                matched_pairs=13, outputs=['comparison.png', 'comparison.json', 'REVIEW.md'])
