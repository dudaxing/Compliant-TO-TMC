"""Compare two explicitly named saved designs using ordinary JSON observations."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path


def require_same_contract(left, right):
    """Require the same declared physical/discretization contract, without tolerance."""
    if left != right:
        raise ValueError('The declared comparison contracts differ')


def bind_observation(state, observed):
    """Bind a viewer row by accepted index, state identity, target and branch."""
    if state['accepted_row_index'] != observed['index'] or any(
            state[key] != observed[key] for key in
            ('state_sha256', 'original_target_index', 'leg', 'd_mm')):
        raise ValueError('The saved state and viewer observation identities differ')
    return dict(state=deepcopy(state), observation=deepcopy(observed))


def pair_rows(left, right):
    """Pair chronological targets; equal displacements on different legs stay separate."""
    def keys(rows):
        return [(row['original_target_index'], row['leg'], row['d_mm']) for row in rows]
    a, b = keys(left), keys(right)
    if a != b or len(set(a)) != len(a):
        raise ValueError('Ordered target/branch/displacement keys differ or repeat')
    return [dict(pair_index=i, original_target_index=key[0], leg=key[1], d_mm=key[2],
                 left_row_index=i, right_row_index=i) for i, key in enumerate(a)]


def _repo_path(repo, name):
    path = (repo / name).resolve()
    path.relative_to(repo)
    return path


def _read_inputs(repo, spec, checkpoint):
    cache, loaded, identities = {}, {}, {}
    for alias, record in spec['inputs'].items():
        path = _repo_path(repo, record['path'])
        if path not in cache:
            checkpoint('json_read_started')
            raw = path.read_bytes()
            pin = sha256(raw).hexdigest()
            if pin != record['sha256']:
                raise ValueError('Saved JSON SHA differs: ' + record['path'])
            cache[path] = json.loads(raw)
            checkpoint('json_read_completed')
        loaded[alias] = cache[path]
        identities[alias] = deepcopy(record)
    return loaded, identities


def _contract(model, result):
    task = {key: deepcopy(value) for key, value in model['task'].items()
            if key not in ('geometry', 'task_id', 'purpose', 'description', 'parameter_origin')}
    return dict(task=task, grid=deepcopy(model['grid']), material=deepcopy(model['material']),
        model_extent=deepcopy(model['model_extent']),
        ports=deepcopy(model['region_metadata']['ports']),
        boundary_declarations={name: {key: value for key, value in model['region_metadata'][name].items()
                                     if key in ('tag', 'points_mm', 'components', 'selection')}
                               for name in ('support', 'entity_symmetry')},
        settings={key: value for key, value in result['settings'].items()
                  if key != 'time_limit_seconds'},
        options=dict(response_mode=result['response_mode'],
                     tangent_mode=result['tangent_execution']['mode'], initial_guess=result['initial_guess']))


def _state(raw, index):
    return dict(accepted_row_index=index, original_target_index=raw['original_target_index'],
        is_original_target=raw['is_original_target'], state_sha256=raw['state_sha256'],
        leg=raw['leg'], d_mm=raw['d'], R_input_N=raw['R_input'], q_in_mm=raw['q_in'],
        q_out_mm=raw['q_out'], global_minimum_J=raw['minimum_J'],
        force_on_lower_body_N=deepcopy(raw['workpiece']['force_on_lower_body_N']),
        original_saved_state=deepcopy(raw))


def _row(raw, index, observed, source):
    state = _state(raw, index)
    answer = bind_observation(state, observed)
    answer.update(original_target_index=state['original_target_index'], leg=state['leg'],
                  d_mm=state['d_mm'], source=deepcopy(source), references=[])
    return answer


def _source(result, identity, model):
    return dict(result=deepcopy(identity), original_status=result['status'],
        original_failure=deepcopy(result['failure']),
        geometry=deepcopy(model['source_geometry']), task_sha256=result['task_sha256'],
        counts=deepcopy(result['counts']),
        boundary_attachment={name: deepcopy(model['region_metadata'][name])
                             for name in ('support', 'entity_symmetry')},
        original_path_flags={key: result.get(key) for key in
                             ('target_reached', 'path_completed', 'unload_endpoint_reached',
                              'full_original_path_completed', 'full_extended_path_completed')},
        original_task=deepcopy(model['task']), original_settings=deepcopy(result['settings']),
        mechanics_source_sha256=deepcopy(result['mechanics_source_sha256']),
        producer_flags={key: result.get(key) for key in
                        ('independent_HP_qualified', 'equilibrium_qualified', 'HF_qualified')},
        continuation=deepcopy(result.get('continuation')))


def _add_reference(design, ref, ref_identity, producer, producer_identity, segment):
    if ref['status'] != 'pass' or ref['result_sha256'] != producer_identity['sha256']:
        raise ValueError('Reference summary does not identify its declared producer')
    design['reference_summaries'].append(dict(summary=deepcopy(ref_identity),
        source_segment=segment, original_summary=deepcopy(ref)))
    for saved in ref['states']:
        child = saved.get('child_accepted_index', saved['index'])
        raw = producer['states'][child]
        if (saved['status'] != 'pass' or saved['state_sha256'] != raw['state_sha256']
                or saved['index'] != child or saved['leg'] != raw['leg']
                or saved['original_target_index'] != raw['original_target_index']
                or saved['target_mm'] != raw['d']):
            raise ValueError('Reference source child/state/target identity differs')
        row = next(row for row in design['rows'] if
                   row['original_target_index'] == raw['original_target_index'])
        if row['state']['state_sha256'] != raw['state_sha256']:
            raise ValueError('Reference state differs from the displayed original target')
        exact = (row['source']['result']['sha256'] == producer_identity['sha256']
                 and row['state']['accepted_row_index'] == child)
        if not exact and not any(alias['source_result_SHA256'] == producer_identity['sha256']
                                 and alias['accepted_index'] == child for alias in row['source_aliases']):
            raise ValueError('Reference source is not a recorded display alias')
        row['references'].append(dict(summary=deepcopy(ref_identity), source_segment=segment,
            source_result=deepcopy(producer_identity), source_child_index=child,
            original_target_index=raw['original_target_index'], state_sha256=raw['state_sha256'],
            original_reference_record=deepcopy(saved), applies_to_primary_source=exact,
            scope='Exact original source result/child/state only; display aliases acquire no qualification'))


def compare_saved(repo, spec, checkpoint=lambda event: None):
    """Read the frozen ordinary inputs once; retain 50 rows and pair 25 targets."""
    repo = Path(repo).resolve()
    if spec['schema_version'] != 'lf-saved-comparison-spec-1.0':
        raise ValueError('Unsupported comparison spec')
    loaded, identities = _read_inputs(repo, spec, checkpoint)
    m, lf = spec['M'], spec['LF']
    composed, index = loaded[m['composed']], loaded[m['index']]
    if index['counts'] != composed['counts'] or len(index['rows']) != len(composed['unique_rows']):
        raise ValueError('M saved composition and point index differ')
    segments, history = {}, []
    for item, recorded in zip(m['segments'], composed['sources']):
        result, model, viewer = [loaded[item[key]] for key in ('result', 'model', 'viewer')]
        if (item['label'] != recorded['label']
                or identities[item['result']]['sha256'] != recorded['result_SHA256']
                or identities[item['model']]['sha256'] != recorded['model_SHA256']
                or identities[item['viewer']]['sha256'] != recorded['viewer_summary_SHA256']
                or result['model']['descriptor_file_sha256'] != identities[item['model']]['sha256']
                or len(result['states']) != viewer['accepted_states']):
            raise ValueError('M declared source differs from the saved composition')
        source = _source(result, identities[item['result']], model)
        source.update(label=item['label'], viewer=deepcopy(identities[item['viewer']]))
        history.append(source)
        segments[item['label']] = (item, result, model, viewer, source)
    if len(segments) != len(composed['sources']):
        raise ValueError('M segment inventory differs')
    left = dict(label='Historical M', identity=deepcopy(history[-1]['geometry']), rows=[],
        source_history=history, reference_summaries=[], media=[dict(path=s['gif']['repo_relative_path'],
            path_scope='repo_relative', scope='Existing animation link only; not read or stat checked')
            for s in composed['sources']], original_composition_claims=deepcopy(composed['composition_claims']))
    for entry, point in zip(composed['unique_rows'], index['rows']):
        origin = entry['source']
        item, result, model, viewer, source = segments[origin['segment']]
        child = origin['accepted_index']
        raw, observed = result['states'][child], viewer['rows'][child]
        if (point['state_sha256'] != raw['state_sha256']
                or entry['result_state'] != raw or entry['observations'] != observed
                or point['global_target_index'] != raw['original_target_index']):
            raise ValueError('M indexed source state or viewer row differs')
        row = _row(raw, child, observed, source)
        row['source_aliases'] = deepcopy(point['source_aliases'])
        left['rows'].append(row)
    last = m['segments'][-1]
    left['contract'] = _contract(loaded[last['model']], loaded[last['result']])
    for item in m['references']:
        segment = segments[item['segment']]
        _add_reference(left, loaded[item['summary']], identities[item['summary']],
                       segment[1], identities[segment[0]['result']], item['segment'])

    table, result, model, viewer = [loaded[lf[key]] for key in ('table', 'result', 'model', 'viewer')]
    if (table['identity']['result']['sha256'] != identities[lf['result']]['sha256']
            or table['identity']['model']['sha256'] != identities[lf['model']]['sha256']
            or result['model']['descriptor_file_sha256'] != identities[lf['model']]['sha256']
            or len(table['rows']) != len(result['states']) or len(viewer['rows']) != len(result['states'])):
        raise ValueError('LF consumption table/model/result/viewer bindings differ')
    source = _source(result, identities[lf['result']], model)
    source.update(label='L-FWD1', viewer=deepcopy(identities[lf['viewer']]))
    right = dict(label='LF native fine', identity=deepcopy(table['identity']), rows=[],
        contract=_contract(model, result), source_history=[source], reference_summaries=[],
        media=deepcopy(table['existing_media']), original_independent_reference=deepcopy(table['independent_reference']),
        original_producer_flags=deepcopy(table['producer_flags']))
    for child, (raw, saved, observed) in enumerate(zip(result['states'], table['rows'], viewer['rows'])):
        state = _state(raw, child)
        # minimum_J has its original global scope in the existing consumption table.
        expected = {key: (raw['minimum_J'] if key == 'minimum_J' else state[key])
                    for key in saved if key != 'has_matched_reference'}
        if expected != {key: value for key, value in saved.items() if key != 'has_matched_reference'}:
            raise ValueError('LF consumption row differs from its original result')
        row = _row(raw, child, observed, source)
        row.update(source_aliases=[], original_consumption_row=deepcopy(saved))
        right['rows'].append(row)
    _add_reference(right, loaded[lf['reference']], identities[lf['reference']],
                   result, identities[lf['result']], 'L-FWD1')
    require_same_contract(left['contract'], right['contract'])
    # Earlier M tasks are path prefixes, while all non-clock numeric settings stay declared.
    for source in left['source_history']:
        n = len(source['original_task']['path']['targets_mm'])
        if source['original_task']['path']['targets_mm'] != left['contract']['task']['path']['targets_mm'][:n]:
            raise ValueError('An M source task is not the declared chronological path prefix')
        segment = segments[source['label']]
        contract = _contract(segment[2], segment[1])
        contract['task']['path'] = deepcopy(left['contract']['task']['path'])
        require_same_contract(contract, left['contract'])
    pairs = pair_rows(left['rows'], right['rows'])
    if len(pairs) != spec['expected_pairs']:
        raise ValueError('The requested 25 paired targets are not present')
    return dict(schema_version='lf-saved-design-comparison-1.0', inputs=identities,
        designs=[left, right], pairs=pairs,
        counts=dict(original_design_rows=len(left['rows'])+len(right['rows']), paired_targets=len(pairs),
                    historical_M_raw_rows=composed['counts']['raw_rows']),
        force_scope='Signed fixed lower-body weak-form resultants; material and Hu retained; no pressure or effective-clamp qualification',
        distance_scope='Saved viewer bottom_first_ray_mm: first ray along the finite bottom-face outward normal; not node-window clearance or tip_to_bottom_mm',
        field_scope='Saved global minimum_J, solid_min_J and free-medium medium_min_J remain separate; Green principal bounds belong to solid',
        comparison_scope='Descriptive same-task saved observations across different geometry and source histories; no new mechanics, reference, differences, ratios, labels or ranking',
        qualification=dict(full_path_reference_pass=False, pressure_qualified=False,
                           effective_clamp_qualified=False, stability_qualified=False, HF5_qualified=False))


def render_comparison(data, output, checkpoint=lambda event: None):
    """Plot existing scalar values only; Matplotlib is imported at actual rendering."""
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    colors = ('#1f5e99', '#b35b27')
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
        fig, axes = plt.subplots(2, 2, figsize=(13, 9))
        for axis, (location, key, title) in zip(axes.flat, fields):
            for design, color in zip(data['designs'], colors):
                for leg, style in (('loading', '-'), ('unloading', '--')):
                    loading = [row for row in design['rows'] if row['leg'] in ('origin', 'loading')]
                    unloading = [row for row in design['rows'] if row['leg'] == 'unloading']
                    rows = loading if leg == 'loading' else loading[-1:] + unloading
                    x = [row['d_mm'] for row in rows]
                    if key == 'material_total':
                        series = [('material', 'o'), ('total', 's')]
                    elif key == 'strain_range':
                        series = [('solid_Green_principal_min', 'v'), ('solid_Green_principal_max', '^')]
                    else:
                        series = [(key, 'o')]
                    for field, marker in series:
                        if location == 'force':
                            y = [row['state']['force_on_lower_body_N'][field][1] for row in rows]
                        else:
                            y = [row[location][field] for row in rows]
                        suffix = ' / ' + field if len(series) > 1 else ''
                        axis.plot(x, y, linestyle=style, color=color, marker=marker, markersize=3,
                                  label=design['label']+' / '+leg+suffix)
            axis.set_title(title)
            axis.set_xlabel('Prescribed mean input displacement (mm)')
            axis.grid(alpha=.25)
            if key == 'medium_min_J':
                axis.set_yscale('log')
            axis.legend(fontsize=7)
        fig.suptitle('Saved observations: M composed sources versus LF single run; partial references only')
        fig.tight_layout(rect=(0, 0, 1, .96))
        fig.savefig(output / filename, dpi=150)
        plt.close(fig)
        checkpoint('plot_completed')


def _markdown(data, repo, output):
    lines = ['# 已有两设计：同任务保存态对照', '',
        '目标是让外部研究层比较已有物理响应；本次只读取普通JSON并画标量，没有重新求解或计算参考。',
        '两例同h0.5、84×40 mm域、E1 MPa、nu0.3、厚20 mm、gamma1e-6、alpha5e-7、Lr80 mm、固定side18方体center(71,40)。',
        'Historical M是五段保存观测，原加载failed/time_limit保留；LF是一次完整25目标生产。两者不是全路径同源码实验或正式排名。', '',
        data['force_scope'], data['distance_scope'], data['field_scope'], '',
        '读取后的50条原值及25对身份保存在 [comparison.json](comparison.json)。没有派生差值、比例、压力或接触门。', '',
        '![反力、位移与工件作用](responses.png)', '',
        '![有限底面射线距离及分区场](geometry_quality.png)', '',
        '| 目标 | 路段 | d mm | M R N | LF R N | M qout mm | LF qout mm | M total Fy N | LF total Fy N |',
        '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    left, right = data['designs']
    for pair in data['pairs']:
        a, b = left['rows'][pair['left_row_index']]['state'], right['rows'][pair['right_row_index']]['state']
        numbers = [pair['d_mm'], a['R_input_N'], b['R_input_N'], a['q_out_mm'], b['q_out_mm'],
                   a['force_on_lower_body_N']['total'][1], b['force_on_lower_body_N']['total'][1]]
        lines.append('| '+str(pair['original_target_index'])+' | '+pair['leg']+' | '+
                     ' | '.join(format(value, '.10g') for value in numbers)+' |')
    lines += ['', '## 来源与参考范围', '',
        'M的global13参考属于RESUME child0锚点，只列原result/state出处，不授ALPHA父结果资格。',
        'LF只有13/16两态已有参考；M的13/14/15及18/19也只属于所列原子段。全路径参考、压力、有效夹持、稳定性及HF5均未通过。',
        '加载实线、卸载虚线；两设计固定配色。连线保留采样顺序，不插值、不从不同采样连线判断滞回。J对数仅作显示。', '']
    lines += ['卸载曲线复用原最后加载峰值点作为显示起点，使1.20→1.15 mm真实段可见；不新增保存态或配对行。', '']
    for design in data['designs']:
        lines += ['### '+design['label'], '', '| 来源 | 原状态 | 源result SHA | native_mean SHA |', '|---|---|---|---|']
        for source in design['source_history']:
            lines.append('| '+source['label']+' | '+source['original_status']+' | `'+source['result']['sha256']+'` | `'+
                         source['mechanics_source_sha256']['hf_repo/src/hf_eval/native_mean.py']+'` |')
        lines += ['', '| 目标 | 主来源child | 原参考来源child | 匹配主来源 |', '|---:|---|---|---|']
        for row in design['rows']:
            refs = row['references'] or [None]
            for ref in refs:
                lines.append('| '+str(row['original_target_index'])+' | '+row['source']['label']+':'+str(row['state']['accepted_row_index'])+
                    ' | '+('未覆盖' if ref is None else ref['source_segment']+':'+str(ref['source_child_index']))+
                    ' | '+('否' if ref is None else str(ref['applies_to_primary_source']))+' |')
        lines += ['', '已有实际变形／参考媒体只提供链接，本次未读取或stat检查：', '']
        for media in design['media']:
            link = os.path.relpath(_repo_path(repo, media['path']), output).replace('\\', '/')
            lines.append('- ['+Path(media['path']).name+'](<'+link+'>)')
        lines.append('')
    return '\n'.join(lines).rstrip()+'\n'


def main(argv=None, checkpoint=lambda event: None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New output directory')
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    checkpoint('json_read_started')
    spec = json.loads(_repo_path(repo, args.spec).read_bytes())
    checkpoint('json_read_completed')
    output = (repo / args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    data = compare_saved(repo, spec, checkpoint)
    with (output / 'comparison.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    checkpoint('comparison_written')
    render_comparison(data, output, checkpoint)
    with (output / 'REVIEW.md').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(_markdown(data, repo, output))
    checkpoint('review_written')
    print(json.dumps(data['counts']))
    return data


if __name__ == '__main__':
    main()
