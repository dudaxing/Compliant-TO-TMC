"""Saved Q1 tip closeups and nonbody-medium extrema; no mechanical evaluation."""
from hashlib import sha256
from html import escape
from io import BytesIO
import json
import os
from pathlib import Path
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection


SIMPSON_POINTS = tuple((xi, eta) for xi in (-1., 0., 1.) for eta in (-1., 0., 1.))
SHAPES = dict(coordinates=(14985, 2), connectivity=(14720, 4), solid=(14720,),
              workpiece_cells=(510,), lift=(29970,), fluctuation=(29970,),
              J=(14720, 9), Hu=(14720, 2, 2, 2))


def write_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError('L-CTIPLOCAL1 original helper deadline reached')


def sample_witness(J, cells, reference, actual, connectivity):
    values = J[cells]
    local_cell, q = np.unravel_index(int(np.argmin(values)), values.shape)
    element = int(cells[local_cell])
    xi, eta = SIMPSON_POINTS[q]
    weights = .25 * np.asarray([(1-xi)*(1-eta), (1+xi)*(1-eta),
                                (1+xi)*(1+eta), (1-xi)*(1+eta)])
    nodes = connectivity[element]
    value = float(values[local_cell, q])
    return dict(value=value, element_id=element, simpson_index=int(q),
        local_coordinates=[xi, eta],
        reference_position_mm=(weights @ reference[nodes]).tolist(),
        actual_position_mm=(weights @ actual[nodes]).tolist(),
        exact_tie_count=int(np.count_nonzero(values == value)),
        witness_rule='First C-order exact tie over ascending element IDs, then saved Simpson order; not a uniqueness claim')


def hu_witness(Hu, cells, reference, actual, connectivity):
    values = Hu[cells]
    absolute = np.abs(values)
    index = np.unravel_index(int(np.argmax(absolute)), absolute.shape)
    element = int(cells[index[0]])
    value = float(absolute[index])
    nodes = connectivity[element]
    return dict(max_abs_component_per_mm=value,
        signed_component_per_mm=float(values[index]), element_id=element,
        component_ijk=[int(i) for i in index[1:]],
        reference_cell_center_mm=reference[nodes].mean(axis=0).tolist(),
        actual_cell_center_mm=actual[nodes].mean(axis=0).tolist(),
        exact_tie_count=int(np.count_nonzero(absolute == value)),
        witness_rule='First C-order exact tie over ascending element IDs and Hu[i,j,k]; not a uniqueness claim',
        position_scope='Hu is constant per element/component; Q1 center is a representative marker, not a unique extremum point or nine-point sample')


def equal_axes(axis, bounds):
    axis.set(xlim=bounds[:2], ylim=bounds[2:], xlabel='x (mm)', ylabel='y (mm)')
    axis.set_aspect('equal', adjustable='box')
    axis.ticklabel_format(useOffset=False, style='plain')
    axis.grid(alpha=.15)


def boundary_plot(axis, cached, model, *, fill=True):
    xy, conn = cached['xy'], model['connectivity']
    if fill:
        axis.add_collection(PolyCollection(xy[conn[model['solid']]],
            facecolors='#b7cde1', edgecolors='none', zorder=1))
        axis.add_collection(PolyCollection(xy[conn[model['workpiece_cells']]],
            facecolors='#e7dac0', edgecolors='none', zorder=2))
    for key, color in (('mechanism_edges', '#285a87'), ('workpiece_edges', '#5e4b35')):
        edges = np.asarray(cached['boundary'][key], dtype=np.int64)
        axis.add_collection(LineCollection(xy[edges], colors=color, linewidths=1.1, zorder=3))


def square_bounds(caches, model, field):
    conn = model['connectivity']
    vertices = np.concatenate([saved['xy'][conn[saved[field]['element_id']]] for saved in caches])
    lower, upper = vertices.min(axis=0), vertices.max(axis=0)
    center = .5 * (lower+upper)
    side = max(float(np.max(upper-lower)) + 1.5, 2.)
    return [float(center[0]-side/2), float(center[0]+side/2),
            float(center[1]-side/2), float(center[1]+side/2)]


def plot_tips(caches, model, output, bounds, deadline):
    check_time(deadline)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.2), layout='constrained')
    for axis, saved in zip(axes, caches):
        boundary_plot(axis, saved, model)
        tip, witness = saved['tip'], np.asarray(saved['tip_surface_witness']['point_mm'])
        axis.plot([tip[0], witness[0]], [tip[1], witness[1]], color='#d17705',
                  linewidth=2, zorder=6)
        axis.scatter(*tip, c='#d17705', s=45, marker='o', zorder=7, label='Actual mechanism tip')
        axis.scatter(*witness, c='#784620', s=45, marker='x', zorder=7, label='Saved nearest Q1 point')
        distance_um = 1000*saved['tip_surface_witness']['distance_mm']
        axis.annotate(f'{distance_um:.3f} micrometers', .5*(tip+witness),
            xytext=(50, -37), textcoords='offset points', fontsize=11,
            arrowprops=dict(arrowstyle='-', color='#b16d15'), color='#7a4900', zorder=8)
        equal_axes(axis, bounds)
        axis.set_title(f"d = {saved['row']['d_mm']:.2f} mm | actual x1\n"
                       f"tip node {saved['row']['tip_node']} to fixed Q1 boundary")
        x, y, length = bounds[0]+.04, bounds[2]+.045, .05
        axis.plot([x, x+length], [y, y], color='black', linewidth=2.5, zorder=8)
        axis.text(x+length/2, y+.012, '50 micrometers', ha='center', fontsize=9)
        axis.legend(loc='upper left', fontsize=9)
    fig.suptitle('Two saved states, identical physical axes and extent; actual Q1 gap is not enlarged', fontsize=13)
    fig.get_layout_engine().set(rect=(0, .06, 1, .94))
    fig.text(.5, .018, 'Coordinates and ruler in mm; distance label in micrometers. '
        'Original unsigned tip witness, real straight Q1 workpiece edges; no analytic circle or new distance search.\n'
        'Lower-half saved geometry only; positive separation does not qualify contact pressure or effective gripping.',
        ha='center', fontsize=9)
    fig.savefig(output/'tip_closeup.png', dpi=220)
    plt.close(fig)
    check_time(deadline)


def plot_locations(caches, model, cells, output, bounds, deadline):
    check_time(deadline)
    conn, reference = model['connectivity'], model['coordinates']
    outer = np.flatnonzero(reference[:, 0] == 92.)
    strip = np.all(reference[conn, 0] >= 89., axis=1)
    strip &= np.isin(np.arange(len(conn)), cells)
    ranges = dict(J=[min(float(s['J'][cells].min()) for s in caches),
                     max(float(s['J'][cells].max()) for s in caches)],
                  Hu=[0., max(float(np.abs(s['Hu'][cells]).max()) for s in caches)])
    fig, axes = plt.subplots(2, 3, figsize=(18, 10.4), layout='constrained')
    for row_axes, saved in zip(axes, caches):
        xy, Jw, Hw = saved['xy'], saved['J_min'], saved['Hu_max']
        overview, jaxis, haxis = row_axes
        boundary_plot(overview, saved, model)
        overview.add_collection(PolyCollection(xy[conn[strip]], facecolors='#c6a7dc',
            edgecolors='none', alpha=.4, zorder=.5))
        overview.plot(xy[outer, 0], xy[outer, 1], color='#8754a6', linewidth=1, label='Actual right boundary')
        overview.scatter(*Jw['actual_position_mm'], marker='o', s=65, facecolors='none',
            edgecolors='#db302e', linewidths=1.5, label='All-medium minimum J', zorder=5)
        overview.scatter(*Hw['actual_cell_center_mm'], marker='s', s=65, facecolors='none',
            edgecolors='#00817d', linewidths=1.5, label='All-medium max |Hu| cell', zorder=5)
        overview.scatter(*saved['tip'], marker='^', s=30, c='#d17705', label='Actual tip', zorder=6)
        equal_axes(overview, [-1., 95., -1., 41.])
        overview.set_title(f"d = {saved['row']['d_mm']:.2f} mm | global locations\n"
            'Purple: fixed reference x89..92 medium strip')
        overview.legend(loc='upper left', fontsize=8)
        for axis, values, key, title, units in (
            (jaxis, saved['J'][cells].min(axis=1), 'J', 'Cell min of 9 saved Simpson J', 'dimensionless'),
            (haxis, np.abs(saved['Hu'][cells]).reshape(len(cells), -1).max(axis=1),
             'Hu', 'Cell max |Hu component|', '1/mm')):
            polygons = PolyCollection(xy[conn[cells]], array=values, cmap='viridis',
                edgecolors='#777777', linewidths=.18, zorder=1)
            polygons.set_clim(*ranges[key])
            axis.add_collection(polygons)
            boundary_plot(axis, saved, model)
            equal_axes(axis, bounds[key])
            axis.set_title(title)
            fig.colorbar(polygons, ax=axis, shrink=.73, label=units)
        jaxis.scatter(*Jw['actual_position_mm'], s=75, facecolors='none', edgecolors='red',
            linewidths=1.8, zorder=7)
        jaxis.set_title(f"Cell min of 9 saved Simpson J\n{Jw['value']:.9g}, "
            f"e{Jw['element_id']}/q{Jw['simpson_index']}, ties={Jw['exact_tie_count']}")
        haxis.scatter(*Hw['actual_cell_center_mm'], s=75, facecolors='none', edgecolors='red',
            marker='s', linewidths=1.8, zorder=7)
        haxis.set_title(f"Cell max |Hu component| (1/mm)\n{Hw['max_abs_component_per_mm']:.9g}, "
            f"e{Hw['element_id']}/{Hw['component_ijk']}, ties={Hw['exact_tie_count']}")
    fig.suptitle('Saved nonbody-medium extrema and actual x1 Q1 neighborhoods; shared field ranges across both states', fontsize=13)
    fig.get_layout_engine().set(rect=(0, .075, 1, .95))
    fig.text(.5, .018, f'Extrema cover all {len(cells)} nonbody-medium cells (~solid, excluding workpiece_cells), not just the plotted crop or right strip.\n'
        'J witnesses are original nine-point Simpson samples, including corners. Hu is cellwise constant: square marks a representative Q1 center.\n'
        'First C-order exact tie is shown; all tie counts and exact reference/actual coordinates are in localization.json. No fresh mechanics or pressure qualification.',
        ha='center', fontsize=9)
    fig.savefig(output/'medium_locations.png', dpi=200)
    plt.close(fig)
    check_time(deadline)
    return ranges


def manual_page(output, root, record, links):
    def link(name, target):
        path = os.path.relpath(root/target, output).replace('\\', '/')
        return f'<a href="{escape(path, quote=True)}">{escape(name)}</a>'
    columns = ['d (mm)', 'R input (N)', 'tip distance (micrometers)', 'medium min J',
               'medium max |Hu| (1/mm)', 'body Fy total/material/Hu (N)']
    rows = []
    for saved in record['states']:
        row = saved['source_row']
        values = [f"{row['d_mm']:.2f}", f"{row['R_input_N']:.9g}",
            f"{1000*saved['tip_surface_witness']['distance_mm']:.6f}",
            f"{saved['J_min']['value']:.12g}", f"{saved['Hu_max']['max_abs_component_per_mm']:.12g}",
            ' / '.join(f'{row[key]:.12g}' for key in ('total_body_Fy_N', 'material_body_Fy_N', 'regularization_body_Fy_N'))]
        rows.append('<tr>'+''.join('<td>'+escape(value)+'</td>' for value in values)+'</tr>')
    existing = ' | '.join(link(name, target) for name, target in links.items())
    html = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>L-CTIPLOCAL1 人工检查</title>'
    html += '<style>body{font-family:system-ui,sans-serif;max-width:1500px;margin:32px auto;line-height:1.6;padding:0 20px}img{max-width:100%}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:7px}code{overflow-wrap:anywhere}</style>'
    html += '<h1>L-CTIPLOCAL1 保存态局部观察</h1><p>仅读 STEP8 的1.03/1.04 mm保存态。保持原物理、验收门和资格；没有新平衡路径、F/T/HP、压力或有效夹持结论。</p>'
    html += '<table><thead><tr>'+''.join('<th>'+escape(c)+'</th>' for c in columns)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
    html += '<h2>实际等比例尖端近景</h2><p>两态采用相同物理坐标范围、等比例轴、实际×1，未人为放大间隙。工件采用真实Q1边，而非解析圆；微米标签来自既有unsigned tip witness，不新增距离搜索。</p><img src="tip_closeup.png" alt="实际等比例尖端近景">'
    html += '<h2>全非工件介质极值位置</h2><p>极值选择覆盖全部~solid并排除工件的介质。J为原九点Simpson值（含角点）；Hu逐单元常值，方框仅为代表中心。局部图是裁剪显示，极值不是局部范围内重新选取。精确并列保首个C-order见证及并列数量。</p><img src="medium_locations.png" alt="全介质极值与局部位置">'
    html += '<p><a href="localization.json">原值、身份、精确坐标与对账JSON</a> | '+existing+'</p>'
    html += '<p>反力、工件弱力及收敛复用既有普通记录与图。下半域signed工件力不翻倍，包含Hu贡献；q_out是端口位移而非gap。局部显示不授压力、有效夹持、自由释放、稳定性、网格/域宽收敛或HF5资格。</p></html>\n'
    with (output/'manual.html').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(html)


def run(protocol, output, deadline):
    """One authorized read/render pass, called by the bounded research helper."""
    started = time.monotonic()
    check_time(deadline)
    root, output = Path(protocol['repository_root']), Path(output)
    spec = protocol['observer']
    output.mkdir(parents=True, exist_ok=True)
    counts = dict(archives=0, fields=0, file_hashes=0)
    readset = []

    def plain(name):
        return json.loads((root/name).read_bytes())

    def archive(pin, fields):
        check_time(deadline)
        raw = (root/pin['path']).read_bytes()
        digest = sha256(raw).hexdigest()
        counts['file_hashes'] += 1
        if len(raw) != pin['bytes'] or digest != pin['sha256']:
            raise ValueError('Original producer archive identity differs: '+pin['path'])
        values = {}
        with np.load(BytesIO(raw), allow_pickle=False) as stored:
            counts['archives'] += 1
            for key in fields:
                check_time(deadline)
                values[key] = stored[key]
                counts['fields'] += 1
                if values[key].shape != SHAPES[key] or not np.all(np.isfinite(values[key])):
                    raise ValueError('Original selected field shape/finite contract differs: '+key)
        readset.append(dict(path=pin['path'], bytes=len(raw), sha256=digest, decoded_fields=list(fields)))
        check_time(deadline)
        return values

    descriptor = plain(spec['model_descriptor_json'])
    if descriptor['element_node_order'] != ['BL', 'BR', 'TR', 'TL'] or descriptor['quadrature'] != 'tensor_product_9_point_Simpson':
        raise ValueError('Original Q1/Simpson order differs')
    model = archive(spec['model_npz'], ('coordinates', 'connectivity', 'solid', 'workpiece_cells'))
    reference, conn = model['coordinates'], model['connectivity']
    if model['solid'].dtype != np.dtype('bool') or conn.dtype != np.dtype('int64'):
        raise ValueError('Original mask/connectivity dtype differs')
    medium = ~model['solid'].copy()
    medium[model['workpiece_cells']] = False
    cells = np.flatnonzero(medium)
    tips = np.flatnonzero(np.all(reference == (80., 30.), axis=1))
    if len(tips) != 1:
        raise ValueError('Require unique exact reference tip node at (80,30)')
    summary = plain(spec['summary_json'])
    caches, observations, differences = [], [], []
    for selection in spec['states']:
        check_time(deadline)
        derived = plain(selection['derived_json'])
        row = derived['row']
        if (row != summary['rows'][selection['accepted_index']]
                or row['original_target_index'] != selection['global_index']
                or row['d_mm'] != selection['d_mm'] or row['state_sha256'] != selection['state_sha256']
                or row['tip_node'] != int(tips[0])):
            raise ValueError('Original state/summary/derived identity differs')
        state = archive(selection['state_npz'], ('lift', 'fluctuation'))
        force = archive(selection['forces_npz'], ('J', 'Hu'))
        # Keep the original viewer's left-associative binary64 coordinate arithmetic.
        xy = reference + state['lift'].reshape(-1, 2) + state['fluctuation'].reshape(-1, 2)
        tip = xy[tips[0]]
        Jw = sample_witness(force['J'], cells, reference, xy, conn)
        Hw = hu_witness(force['Hu'], cells, reference, xy, conn)
        comparisons = dict(medium_min_J=Jw['value'] == row['medium_min_J'],
            medium_max_abs_Hu=Hw['max_abs_component_per_mm'] == row['medium_max_abs_Hu_per_mm'],
            actual_tip_coordinates=np.array_equal(tip, [row['tip_x_mm'], row['tip_y_mm']]),
            tip_distance_witness=derived['tip_surface_witness']['distance_mm'] == row['tip_to_raster_boundary_mm'])
        observations.append(dict(accepted_index=selection['accepted_index'], global_index=selection['global_index'],
            state_sha256=selection['state_sha256'], source_row=row,
            tip_reference_position_mm=[80., 30.], tip_actual_position_mm=tip.tolist(),
            tip_surface_witness=derived['tip_surface_witness'],
            J_min=Jw, Hu_max=Hw, exact_original_scalar_comparisons=comparisons))
        differences.extend(dict(accepted_index=selection['accepted_index'], comparison=key)
                           for key, passed in comparisons.items() if not passed)
        caches.append(dict(xy=xy, tip=tip, row=row, boundary=plain(selection['geometry_json'])['boundary'],
            tip_surface_witness=derived['tip_surface_witness'], J_min=Jw, Hu_max=Hw, **force))
    record = dict(schema_version='saved-tip-local-observation-1.0', card='L-CTIPLOCAL1',
        status='not_pass' if differences else 'pass', states=observations, differences=differences,
        readset=readset, counts=counts, observed_states=len(observations),
        nonbody_medium=dict(cell_count=len(cells), selection='~solid, then workpiece_cells excluded; ascending original element IDs'),
        actual_coordinate_definition='Left-associative coordinates + lift.reshape(-1,2) + fluctuation.reshape(-1,2), exactly as original viewer',
        simpson_order=[list(point) for point in SIMPSON_POINTS],
        existing_links=spec['existing_links'], no_new_distance_search=True,
        new_F_T_model_solver_HP_calls=0, new_tests=0, new_GIF=0,
        qualifications_unchanged=True, pressure_or_effective_gripping_qualified=False)
    if differences:
        write_json(output/'localization.json', record)
        raise ValueError('Saved observer differs from original scalar summaries; see localization.json')
    if counts != dict(archives=5, fields=12, file_hashes=5) or len(caches) != 2:
        raise ValueError('Require the approved five archives/twelve selected fields/two states')
    tip_center = np.mean([saved['tip'] for saved in caches], axis=0)
    tip_center[1] = .5*(tip_center[1] + np.mean([saved['tip_surface_witness']['point_mm'][1] for saved in caches]))
    tip_bounds = [float(tip_center[0]-.3), float(tip_center[0]+.3),
                  float(tip_center[1]-.3), float(tip_center[1]+.3)]
    map_bounds = dict(J=square_bounds(caches, model, 'J_min'), Hu=square_bounds(caches, model, 'Hu_max'))
    record['plot_definitions'] = dict(tip_common_extent_mm=tip_bounds,
        medium_local_extents_mm=map_bounds, deformation_scale=1,
        J_map='Per-cell minimum of the original nine saved Simpson J values; global extrema scope is all nonbody medium',
        Hu_map='Per-cell maximum absolute saved Hu component; center marker is representative',
        equal_physical_axes=True, original_unsigned_tip_witness_reused=True)
    # Save scalar observations before plotting so a render failure retains the actual reductions.
    write_json(output/'localization.json', record)
    plot_tips(caches, model, output, tip_bounds, deadline)
    ranges = plot_locations(caches, model, cells, output, map_bounds, deadline)
    manual_page(output, root, record, spec['existing_links'])
    check_time(deadline)
    outputs = {}
    for name in ('tip_closeup.png', 'medium_locations.png', 'localization.json', 'manual.html'):
        check_time(deadline)
        path = output/name
        raw = path.read_bytes()
        outputs[path.relative_to(root).as_posix()] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    check_time(deadline)
    return dict(status='pass', observed_states=2, **counts, outputs=outputs,
        output_identity_seal='Original observer producer seals within the authorized helper window',
        comparison_summary=dict(all_exact=True, comparisons=len(observations)*4),
        plot_paths={name: (output/name).relative_to(root).as_posix()
                    for name in ('tip_closeup.png', 'medium_locations.png')},
        plot_field_ranges=ranges, elapsed_seconds=time.monotonic()-started,
        new_F_T_model_solver_HP_calls=0, new_tests=0, new_GIF=0)
