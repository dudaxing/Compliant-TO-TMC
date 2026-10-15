"""Compare three saved LF cases using ordinary JSON and existing media links."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path


LEGACY_SOURCE = 'lf_data_preparation/native_interface_001/lf_saved_comparison_001/example/compare_saved_designs.py'
INPUT_ALIASES = (
    'baseline_comparison', 'baseline_receipt', 'third_table', 'third_index',
    'third_response', 'third_delivery_receipt', 'third_result', 'third_model',
    'third_viewer', 'third_reference',
)
COLORS = ('#1f5e99', '#b35b27', '#247a58')


def _typed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def _same(left, right, message):
    if _typed(left) != _typed(right):
        raise ValueError(message)


def _path(repo, name):
    path = (repo / name).resolve()
    path.relative_to(repo)
    return path


def _record_matches(record, identity):
    return (record['path'] == identity['path']
            and record['sha256'] == identity['sha256'])


def _seal_matches(receipt, identity):
    record = receipt['outputs'][identity['path']]
    return record == {key: identity[key] for key in ('sha256', 'bytes')}


def _coverage(design):
    primary, alias = set(), set()
    for row in design['rows']:
        for reference in row['references']:
            (primary if reference['applies_to_primary_source'] else alias).add(
                row['original_target_index'])
    return dict(primary_original_target_indices=sorted(primary),
                alias_only_original_target_indices=sorted(alias - primary))


def _third(legacy, loaded, identities):
    table, index, response, receipt, result, model, viewer, reference = (
        loaded['third_' + key] for key in
        ('table', 'index', 'response', 'delivery_receipt', 'result', 'model', 'viewer', 'reference'))
    if not (receipt['status'] == 'pass'
            and receipt['output_identity_seal'] == 'complete_inside_original_helper_window'
            and receipt['rows_written'] == 25 and receipt['selected_indices'] == [13, 14]
            and all(_seal_matches(receipt, identities['third_' + key])
                    for key in ('table', 'index', 'response'))):
        raise ValueError('The closed third-case delivery seal differs')
    for member, alias in (('index', 'third_index'), ('response', 'third_response'),
                          ('result', 'third_result')):
        if not _record_matches(table['inputs'][member], identities[alias]):
            raise ValueError('Third consumption input identity differs: ' + member)
    if not _record_matches(index['linked_response'], identities['third_response']):
        raise ValueError('Third linked response identity differs')
    for member, alias in (('result_file', 'third_result'), ('model_file', 'third_model'),
                          ('view_case_summary_file', 'third_viewer'), ('reference_file', 'third_reference')):
        if not _record_matches(index['saved_artifacts'][member], identities[alias]):
            raise ValueError('Third index input identity differs: ' + member)
    if not (index['status'] == 'pass'
            and index['selected_accepted_indices'] == index['original_target_indices'] == [13, 14]
            and index['selected_targets_mm'] == [1.2, 1.15]
            and _record_matches(response['identity']['result'], identities['third_result'])
            and _record_matches(response['identity']['model'], identities['third_model'])
            and result['model']['descriptor_file_sha256'] == identities['third_model']['sha256']
            and model['task_sha256'] == result['task_sha256']
            and model['task']['path'] == dict(kind='ordered_cycle', targets_mm=result['targets_mm'])
            and model['region_metadata']['counts'] == result['counts']
            and model['grid'] == result['grid']):
        raise ValueError('Third case result/model/index identity differs')
    if not (result['status'] == response['status'] == viewer['production_status'] == 'success'
            and result['path_completed'] and result['loading_peak_reached']
            and result['unload_endpoint_reached'] and result['task_target_executed']
            and result['reached_displacement'] == 0. and 'continuation' not in result
            and response['path']['completed'] and response['path']['accepted_states'] == 25
            and result['accepted_states'] == viewer['accepted_states'] == 25
            and len(result['states']) == len(table['rows']) == len(viewer['rows']) == 25):
        raise ValueError('Third full zero-start cycle context differs')
    for key in ('identity', 'physics', 'options', 'path', 'independent_reference',
                'producer_flags', 'force_semantics', 'field_scope'):
        _same(table[key], response[key], 'Third table/response field differs: ' + key)
    for key in ('physics', 'options', 'path', 'independent_reference', 'views'):
        _same(index[key], response[key], 'Third index/response field differs: ' + key)
    _same(table['existing_media'], index['images'], 'Third table/index media declarations differ')
    _same(index['source_flags'], response['producer_flags'], 'Third producer flags differ')
    matched = response['independent_reference']
    if not (matched['status'] == 'matched_partial' and matched['selected_reference_pass'] is True
            and matched['source_bindings_verified'] is True
            and matched['matched_state_indices'] == [13, 14]
            and matched['matched_state_count'] == 2 and matched['HP_calls_completed'] == 4
            and matched['production_accepted_state_count'] == 25
            and all(matched[key] is False for key in (
                'covers_all_accepted_states', 'accepted_reference_pass', 'full_path_reference_pass',
                'HP_all_columns_qualified', 'contact_qualified', 'clamp_qualified',
                'pressure_qualified', 'HF5_qualified'))
            and all(value is False for value in response['producer_flags'].values())
            and response['views']['status'] == 'matched'
            and response['views']['case_label'] == 'lf_third_cycle'
            and reference['status'] == 'pass' and reference['selected_accepted_indices'] == [13, 14]
            and reference['HP_calls_started'] == reference['HP_calls_completed'] == 4
            and reference['production_accepted_states'] == 25 and reference['accepted_states'] == 2):
        raise ValueError('Third selected reference or original qualification differs')
    source = legacy._source(result, identities['third_result'], model)
    source.update(label='L-CYCLE1', viewer=deepcopy(identities['third_viewer']))
    design = dict(label='LF wave', identity=deepcopy(table['identity']), rows=[],
        contract=legacy._contract(model, result), source_history=[source], reference_summaries=[],
        media=deepcopy(table['existing_media']),
        original_independent_reference=deepcopy(table['independent_reference']),
        original_producer_flags=deepcopy(table['producer_flags']),
        original_reference_scope=reference['reference_scope'])
    for child, (raw, saved, observed) in enumerate(zip(result['states'], table['rows'], viewer['rows'])):
        if raw['is_original_target'] is not True or raw['original_target_index'] != child:
            raise ValueError('Third saved row is not its original requested target')
        state = legacy._state(raw, child)
        fields = ('accepted_row_index', 'original_target_index', 'is_original_target',
                  'state_sha256', 'leg', 'd_mm', 'R_input_N', 'q_in_mm', 'q_out_mm',
                  'force_on_lower_body_N')
        expected = {key: deepcopy(state[key]) for key in fields}
        expected.update(minimum_J=raw['minimum_J'], has_matched_reference=child in (13, 14))
        _same(saved, expected, 'Third consumer row differs from saved result: ' + str(child))
        row = legacy._row(raw, child, observed, source)
        row.update(source_aliases=[], original_consumption_row=deepcopy(saved))
        design['rows'].append(row)
    legacy._add_reference(design, reference, identities['third_reference'],
                          result, identities['third_result'], 'L-CYCLE1')
    return design


def _render(data, output, checkpoint):
    """Two original four-field figures, now with all three designs."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    assert len(data['designs']) == len(COLORS) == 3
    response_fields = (
        ('state', 'R_input_N', 'Half-model input reaction (N)'),
        ('state', 'q_out_mm', 'Weighted output displacement (mm)'),
        ('force', 'material_total', 'Lower-body material / total Fy (N)'),
        ('force', 'regularization', 'Lower-body signed Hu Fy (N)'))
    geometry_fields = (
        ('observation', 'bottom_first_ray_mm', 'Bottom outward first-ray distance (mm)'),
        ('observation', 'solid_min_J', 'Solid minimum J'),
        ('observation', 'medium_min_J', 'Free-medium minimum J'),
        ('observation', 'strain_range', 'Solid Green principal strain bounds'))
    for filename, fields in (('responses.png', response_fields), ('geometry_quality.png', geometry_fields)):
        checkpoint('plot_started')
        figure, axes = plt.subplots(2, 2, figsize=(13, 9))
        try:
            for axis, (location, key, title) in zip(axes.flat, fields):
                for design_index, design in enumerate(data['designs']):
                    color = COLORS[design_index]
                    loading = [row for row in design['rows'] if row['leg'] in ('origin', 'loading')]
                    unloading = [row for row in design['rows'] if row['leg'] == 'unloading']
                    for leg, style, rows in (('loading', '-', loading),
                                              ('unloading', '--', loading[-1:] + unloading)):
                        x = [row['d_mm'] for row in rows]
                        series = ([('material', 'o'), ('total', 's')] if key == 'material_total'
                                  else [('solid_Green_principal_min', 'v'), ('solid_Green_principal_max', '^')]
                                  if key == 'strain_range' else [(key, 'o')])
                        for field, marker in series:
                            y = ([row['state']['force_on_lower_body_N'][field][1] for row in rows]
                                 if location == 'force' else [row[location][field] for row in rows])
                            if key == 'medium_min_J' and any(value <= 0 for value in y):
                                raise ValueError('Positive saved free-medium J required for the original log display')
                            suffix = ' / ' + field if len(series) > 1 else ''
                            axis.plot(x, y, linestyle=style, color=color, marker=marker, markersize=3,
                                      label=design['label'] + ' / ' + leg + suffix)
                axis.set_title(title)
                axis.set_xlabel('Prescribed mean input displacement (mm)')
                axis.grid(alpha=.25)
                if key == 'medium_min_J':
                    axis.set_yscale('log')
                axis.legend(fontsize=6.4)
            figure.suptitle('Three LF grippers: saved same-task observations\n'
                           'Historical M retains composed sources; selected-state references only')
            figure.tight_layout(rect=(0, 0, 1, .94))
            figure.savefig(output / filename, dpi=150)
        finally:
            plt.close(figure)
        checkpoint('plot_completed')


def _markdown(data, repo, output):
    lines = ['# 三个 LF 夹持器：同定义保存结果对照', '',
        '本次读取十份普通 JSON，继承原值并生成两张标量图，没有新的 HF 评价或科学参考。',
        '同 h0.5 mm、84×40 mm 下半域、E1 MPa、nu0.3、厚20 mm、gamma1e-6、alpha5e-7、Lr80 mm，固定边18 mm方体中心(71,40) mm。',
        'Historical M保留五段来源与原ALPHA failed/time_limit；另两例各有一次完整25目标生产。来源epoch不同，不构成新的全路径同源码实验或正式排名。', '',
        data['force_scope'], data['distance_scope'], data['field_scope'], '',
        '完整75条原值、25组三方索引与各自源result/state SHA见 [comparison.json](comparison.json)。没有派生差值、比例、压力、标签或评分。', '',
        '![反力、输出位移与工件作用](responses.png)', '',
        '![有限射线与分区场](geometry_quality.png)', '',
        '| 原目标 | 路段 | d mm | M R N | LF2 R N | wave R N | M qout mm | LF2 qout mm | wave qout mm | M total Fy N | LF2 total Fy N | wave total Fy N |',
        '|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for pair in data['pairs']:
        states = [design['rows'][pair['row_indices'][i]]['state']
                  for i, design in enumerate(data['designs'])]
        values = [pair['d_mm']] + [state['R_input_N'] for state in states]
        values += [state['q_out_mm'] for state in states]
        values += [state['force_on_lower_body_N']['total'][1] for state in states]
        lines.append('| ' + str(pair['original_target_index']) + ' | ' + pair['leg'] + ' | '
                     + ' | '.join(format(value, '.10g') for value in values) + ' |')
    lines += ['', '## 来源与参考范围', '',
        'M主来源参考只覆盖14/15/18/19；13的RESUME child0是alias，不授ALPHA父态资格。LF native fine覆盖13/16；wave覆盖13/14。',
        '全部原producer flags与全路径参考、压力、有效夹持、稳定性、HF5未通过状态保持。',
        '加载实线、卸载虚线；三例各固定一种颜色。卸载显示复用原加载峰值作为起点，不增加状态或配对行；连线表示原采样顺序，不插值或测定耗散能。自由介质J对数仅作显示，不裁剪、不加floor。',
        '0.85/0.95 mm没有原卸载配对，不用邻态替代。node-window、单尖端距离和finite-ray不互换；q_out不是表面间隙。',
        'wave controller的source SHA与LF2不同：已记录的静态改动仅让load_only也写原目标/leg元数据，不是新的动态数值等价证明。M早期源码epoch及原失败保持。',
        '第三例task的M-ALPHA1/prefix15等历史文字只作来源；实际实验由绑定几何与完整25目标result解释，不改原封存文字。', '']
    for design in data['designs']:
        lines += ['### ' + design['label'], '',
            '| 来源 | 原状态 | 源result SHA | controller SHA |', '|---|---|---|---|']
        for source in design['source_history']:
            lines.append('| ' + source['label'] + ' | ' + source['original_status'] + ' | `'
                         + source['result']['sha256'] + '` | `'
                         + source['mechanics_source_sha256']['hf_repo/src/hf_eval/split_displacement.py'] + '` |')
        lines += ['', '| 原目标 | 主来源child | 原参考来源child | 匹配主来源 |', '|---:|---|---|---|']
        for row in design['rows']:
            for reference in row['references']:
                lines.append('| ' + str(row['original_target_index']) + ' | '
                    + row['source']['label'] + ':' + str(row['state']['accepted_row_index']) + ' | '
                    + reference['source_segment'] + ':' + str(reference['source_child_index']) + ' | '
                    + str(reference['applies_to_primary_source']) + ' |')
        lines += ['', '其余原目标未被上述所选参考覆盖。', '']
    lines += ['## 并列检查既有实际变形与参考媒体', '',
        '以下18份旧媒体仅沿封存清单stat大小并提供链接，未读取payload、解码、抽帧、合成或重绘。',
        'M全局峰值13在ALPHA来源，回零24在UNLOAD2 child8；不能把某个卸载子段的局部最大值当作全局峰值。另两例链接各自完整循环。',
        '变形为原x1与显示镜像；箭头保持各原图尺度，不能跨媒体直接用箭头长度比较力。', '']
    for design in data['designs']:
        lines += ['### ' + design['label'], '']
        for media in data['media']:
            if media['design'] != design['label']:
                continue
            link = os.path.relpath(_path(repo, media['path']), output).replace('\\', '/')
            role = ' — ' + media['role'] if media.get('role') else ''
            lines.append('- [' + Path(media['path']).name + '](<' + link + '>)' + role
                         + '；来源：`' + media['path'] + '`')
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def run(repo, inputs, media, output, checkpoint=lambda event: None):
    """Read exactly ten bound JSON inputs, retain 75 rows, and render once."""
    repo = Path(repo).resolve()
    output = (repo / output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    if set(inputs) != set(INPUT_ALIASES) or len(media) != 18:
        raise ValueError('The ten-input/eighteen-media scope differs')
    loaded = {}
    for alias in INPUT_ALIASES:
        identity = inputs[alias]
        checkpoint('json_read_started')
        raw = _path(repo, identity['path']).read_bytes()
        if len(raw) != identity['bytes'] or sha256(raw).hexdigest() != identity['sha256']:
            raise ValueError('Ordinary JSON input identity differs: ' + alias)
        loaded[alias] = json.loads(raw)
        checkpoint('json_read_completed')
    spec = importlib.util.spec_from_file_location('_three_saved_legacy', _path(repo, LEGACY_SOURCE))
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    baseline = loaded['baseline_comparison']
    receipt = loaded['baseline_receipt']
    if not (receipt['status'] == 'pass'
            and receipt['output_identity_seal'] == 'complete_inside_original_helper_window'
            and _seal_matches(receipt, inputs['baseline_comparison'])
            and baseline['schema_version'] == 'lf-saved-design-comparison-1.0'
            and len(baseline['designs']) == 2):
        raise ValueError('The inherited two-case comparison seal differs')
    designs = deepcopy(baseline['designs'])
    designs.append(_third(legacy, loaded, inputs))
    if [design['label'] for design in designs] != ['Historical M', 'LF native fine', 'LF wave']:
        raise ValueError('The three design identities differ')
    for design in designs:
        if len(design['rows']) != 25:
            raise ValueError('Every design must retain its 25 original rows')
        legacy.require_same_contract(designs[0]['contract'], design['contract'])
        _same(designs[0]['contract'], design['contract'], 'Typed physical contracts differ')
    coverage = [_coverage(design) for design in designs]
    _same(coverage, [dict(primary_original_target_indices=[14, 15, 18, 19], alias_only_original_target_indices=[13]),
                     dict(primary_original_target_indices=[13, 16], alias_only_original_target_indices=[]),
                     dict(primary_original_target_indices=[13, 14], alias_only_original_target_indices=[])],
          'The three original reference coverage sets differ')
    paired = legacy.pair_rows(designs[0]['rows'], designs[1]['rows'])
    third_pairs = legacy.pair_rows(designs[0]['rows'], designs[2]['rows'])
    _same(paired, baseline['pairs'], 'Inherited two-case ordered pair identities differ')
    if len(paired) != 25 or len(third_pairs) != 25:
        raise ValueError('Require 25 unique ordered three-way target keys')
    pairs = [dict(pair, third_row_index=third['right_row_index'],
                  row_indices=[pair['left_row_index'], pair['right_row_index'], third['right_row_index']])
             for pair, third in zip(paired, third_pairs)]
    for record in media:
        checkpoint('media_stat_started')
        if (record['design'] not in [design['label'] for design in designs]
                or _path(repo, record['path']).stat().st_size != record['bytes']):
            raise ValueError('Declared existing media stat differs')
        checkpoint('media_stat_completed')
    wave_media = [record for record in media if record['design'] == 'LF wave']
    _same({record['path']: (record['sha256'], record['bytes']) for record in wave_media},
          {record['path']: (record['sha256'], record['bytes']) for record in designs[2]['media']},
          'Third media scope differs from delivered declarations')
    data = dict(schema_version='lf-saved-design-comparison-1.1', inputs=deepcopy(inputs),
        inherited_baseline_inputs=deepcopy(baseline['inputs']), designs=designs, pairs=pairs,
        reference_coverage=coverage, media=deepcopy(media),
        counts=dict(original_design_rows=75, design_rows=[25, 25, 25], paired_targets=25,
                    historical_M_raw_rows=baseline['counts']['historical_M_raw_rows'],
                    ordinary_JSON_inputs=10, existing_media_links=18, existing_media_stat_checks=18),
        force_scope=baseline['force_scope'], distance_scope=baseline['distance_scope'],
        field_scope=baseline['field_scope'], comparison_scope=baseline['comparison_scope'],
        qualification=deepcopy(baseline['qualification']),
        media_identity_scope='Inherited declared SHA plus current stat size only; no existing media payload read or hash',
        source_history_scope='M five historical sources and primary/alias qualification retained. Wave additive load_only metadata source epoch is declared; no new equivalence experiment.')
    _same(data['designs'][:2], baseline['designs'], 'Inherited original designs were modified')
    if not all(value is False for value in data['qualification'].values()):
        raise ValueError('Original unqualified comparison flags changed')
    with (output / 'comparison.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False).rstrip() + '\n')
    checkpoint('comparison_written')
    _render(data, output, checkpoint)
    with (output / 'REVIEW.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_markdown(data, repo, output).rstrip() + '\n')
    checkpoint('review_written')
    return data
