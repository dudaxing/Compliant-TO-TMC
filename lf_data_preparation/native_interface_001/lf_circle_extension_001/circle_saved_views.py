"""Circle saved-state geometry, nodal observations and displays; no mechanics."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
import argparse
import ast
import csv
import json
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Arc, Circle
from PIL import Image

PARTS = ('total', 'material', 'regularization')
GROUPS = ('physical_only', 'cut_only', 'physical_and_cut', 'interior')
TIP_REFERENCE_MM = (80., 30.)


def descriptor_sha(value):
    """The existing saved-descriptor canonical SHA convention."""
    def canonical(item):
        if isinstance(item, dict):
            return {key: canonical(child) for key, child in item.items()}
        if isinstance(item, list):
            return [canonical(child) for child in item]
        if isinstance(item, float):
            if not np.isfinite(item):
                raise ValueError('Non-finite descriptor number')
            return (0.0 if item == 0.0 else item).hex()
        return item
    value = {key: item for key, item in value.items() if key != 'descriptor_sha256'}
    return sha256(json.dumps(canonical(value), sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def pure_sources(repo):
    """Existing pure-import inspection, scoped to this viewer's four modules."""
    package = repo / 'src/hf_eval'
    sources = [package / name for name in ('__init__.py', 'boundary_geometry.py',
        'native_region_geometry.py', 'workpiece_nodal.py')]
    allowed = {'native_region_geometry', 'boundary_geometry', 'workpiece_nodal'}
    for path in sources[1:]:
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, ast.Import):
                if any(item.name.split('.')[0] not in {'numpy'} | sys.stdlib_module_names for item in node.names):
                    raise ValueError('Unexpected import in pure observation closure')
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level != 1 or node.module not in allowed:
                        raise ValueError('Unexpected hf_eval dependency in pure observation closure')
                elif (node.module or '').split('.')[0] not in {'numpy', '__future__'} | sys.stdlib_module_names:
                    raise ValueError('Unexpected import in pure observation closure')
    init = ast.parse(sources[0].read_text(encoding='utf-8'))
    if any(not isinstance(node, (ast.Expr, ast.Assign, ast.FunctionDef)) for node in init.body):
        raise ValueError('Unexpected package-init execution structure')
    return sources


def plain(value):
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    return value.tolist() if isinstance(value, np.ndarray) else value


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(plain(value), stream, indent=2, allow_nan=False)
        stream.write('\n')


def tip_boundary(point, xy, edges):
    """Original point/finite-segment projection, applied to actual raster edges."""
    a, delta = xy[edges[:, 0]], xy[edges[:, 1]] - xy[edges[:, 0]]
    parameter = np.clip(np.sum((point - a) * delta, axis=1) / np.sum(delta * delta, axis=1), 0., 1.)
    nearest = a + parameter[:, None] * delta
    distances = np.linalg.norm(point - nearest, axis=1)
    index = int(np.argmin(distances))
    return dict(distance_mm=float(distances[index]), point_mm=nearest[index].tolist(),
        workpiece_edge_index=index, workpiece_nodes=edges[index].tolist(),
        scope='Unsigned tip-to-actual-Q1-boundary distance; not contact or penetration')


def draw(ax, case, index, *, zoom=False, component=None, force_scale=1.):
    saved = case['cache'][index]
    model, center = case['model'], case['center']
    # Reflected coordinates are for display; no reflected DOFs or forces are solved.
    for mirror in ((False,) if zoom else (False, True)):
        xy = saved['xy'].copy()
        if mirror:
            xy[:, 1] = 2 * center[1] - xy[:, 1]
        ax.add_collection(PolyCollection(xy[model['connectivity'][model['solid']]],
            facecolors='#457b9d', edgecolors='#24455d', linewidths=.12, rasterized=True))
        ax.add_collection(PolyCollection(xy[model['connectivity'][model['workpiece_cells']]],
            facecolors='#e3d6be', edgecolors='#b7a990' if zoom else 'none', linewidths=.25))
        body_edges = np.asarray(saved['boundary']['workpiece_edges'], dtype=np.int64)
        ax.add_collection(LineCollection(xy[body_edges], colors='#9b4a29', linewidths=1.2))
        if component:
            positions = saved['nodes']['coordinates_mm'].copy()
            vectors = saved['nodes']['forces_on_body_N'][component].copy()
            if mirror:
                positions[:, 1] = 2 * center[1] - positions[:, 1]
                vectors[:, 1] *= -1
            ax.quiver(*positions.T, *(vectors * force_scale).T, angles='xy',
                scale_units='xy', scale=1., color='#b83224', width=.003, minlength=0, minshaft=1)
    ax.axhline(center[1], color='grey', ls=':', lw=.7)
    if zoom:
        ax.add_patch(Arc(center, 2 * case['radius'], 2 * case['radius'], theta1=180., theta2=360.,
            color='#207c83', linestyle='--', linewidth=1., label='Analytic circle: fixed reference only'))
        tip = saved['xy'][case['tip_node']]
        witness = np.asarray(saved['tip']['point_mm'])
        ax.scatter(*tip, c='#e09113', s=20, zorder=5)
        ax.plot([tip[0], witness[0]], [tip[1], witness[1]], '--', color='#e09113',
            label=f"Tip to actual raster: {saved['tip']['distance_mm']:.5g} mm")
        closest = saved['boundary']['groups']['all_exposed']['closest_pair']
        if closest:
            a, b = closest['mechanism_point_mm'], closest['workpiece_point_mm']
            ax.plot([a[0], b[0]], [a[1], b[1]], ':', color='#5a9552',
                label='Closest actual boundary pair; not a force')
        ax.set_xlim(center[0] - case['radius'] - 4., center[0] + case['radius'] + 4.)
        ax.set_ylim(center[1] - case['radius'] - 6., center[1] + 1.)
        ax.legend(fontsize=6, loc='lower left')
    else:
        ax.add_patch(Circle(center, case['radius'], fill=False, color='#207c83',
            linestyle='--', linewidth=.8))
        ax.set_xlim(*case['xlim'])
        ax.set_ylim(*case['ylim'])
    ax.set_aspect('equal')
    ax.set_xlabel('x (mm)')
    ax.set_ylabel('y (mm)')
    record = saved['record']
    ax.set_title(f"{index}: {record['leg']} d={record['d']:g} mm | x1"
        + (' | lower half' if zoom else ' | visual mirror'), fontsize=9)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('repo', 'protocol', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--case', action='append', required=True, metavar='LABEL=RESULT_DIRECTORY')
    parser.add_argument('--stop-file', type=Path)
    parser.add_argument('--time-limit', type=float, default=120.)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.output.resolve()
    root = repo.parent
    out.relative_to(root)
    if len(args.case) != 1:
        parser.error('This circle pilot viewer accepts exactly one case')
    out.mkdir(parents=True, exist_ok=False)
    pins, cases, failure, outputs = {}, [], None, {}
    output_identity_seal = 'not_complete'
    counts = dict(geometry_started=0, geometry_completed=0, boundary_started=0,
        boundary_completed=0, region_started=0, region_completed=0, nodal_started=0,
        nodal_completed=0, archives_decoded=0, fields_decoded=0)
    pure, peak, force_max = False, 0, None
    import psutil
    process = psutil.Process()

    def checkpoint():
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
        if (perf_counter() - STARTED > args.time_limit or peak > 8 * 1024**3
                or (args.stop_file and args.stop_file.exists())):
            raise RuntimeError('Saved circle observation/view resource window closed')

    def file_hash(path):
        digest = sha256()
        with path.open('rb') as stream:
            while chunk := stream.read(1024 * 1024):
                checkpoint()
                digest.update(chunk)
        return digest.hexdigest()

    def bind(path, expected=None):
        path = path.resolve()
        path.relative_to(root)
        digest = file_hash(path)
        if expected is not None and digest != expected:
            raise ValueError('File SHA differs: ' + str(path))
        pins[path] = digest
        return digest

    sys.path.insert(0, str(repo / 'src'))

    def read(path, expected=None, semantic=False):
        bind(path, expected)
        value = json.loads(path.read_text(encoding='utf-8'))
        if semantic and descriptor_sha(value) != value['descriptor_sha256']:
            raise ValueError('Descriptor SHA differs')
        return value

    def archive(directory, declaration):
        path = directory / declaration['path']
        bind(path, declaration['sha256'])
        with np.load(path, allow_pickle=False) as saved:
            data = {key: saved[key].copy() for key in saved.files}
        fields = {key: dict(dtype=value.dtype.name, shape=list(value.shape),
            sha256=sha256(value.tobytes()).hexdigest()) for key, value in data.items()}
        if fields != declaration['fields']:
            raise ValueError('Archive field identity differs')
        counts['archives_decoded'] += 1
        counts['fields_decoded'] += len(data)
        return data

    try:
        protocol = read(args.protocol.resolve())
        for name, digest in protocol['bindings'].items():
            bind(root / name, digest)
        sources = pure_sources(repo) + [Path(__file__).resolve()]
        for source in sources:
            bind(source, protocol['bindings'][source.relative_to(root).as_posix()])
        from hf_eval.boundary_geometry import measure_native_workpiece_boundaries
        from hf_eval.native_region_geometry import region_overlap
        from hf_eval.workpiece_nodal import observe_workpiece_nodal_forces
        allowed = {'hf_eval', 'hf_eval.native_region_geometry', 'hf_eval.boundary_geometry', 'hf_eval.workpiece_nodal'}

        def check_pure():
            nonlocal pure
            pure = False
            loaded = {name for name in sys.modules if name == 'hf_eval' or name.startswith('hf_eval.')}
            if loaded != allowed:
                raise ValueError('Unexpected hf_eval imports in pure observations')
            for name in loaded:
                expected = repo / 'src/hf_eval' / ('__init__.py' if name == 'hf_eval' else name.split('.')[-1] + '.py')
                if Path(sys.modules[name].__file__).resolve() != expected:
                    raise ValueError('Pure module came from another source')
            pure = True

        check_pure()
        pure = True
        label, path = args.case[0].split('=', 1)
        if Path(label).name != label or label in ('.', '..'):
            raise ValueError('Use a simple case label')
        directory = Path(path).resolve()
        directory = directory.parent if directory.is_file() else directory
        result = read(directory / 'result.json', semantic=True)
        model_file = directory / result['model']['descriptor_path']
        metadata = read(model_file, result['model']['descriptor_file_sha256'], True)
        if (metadata['task_sha256'] != result['task_sha256']
                or metadata['arrays']['sha256'] != result['model']['arrays_sha256']):
            raise ValueError('Path/model/task differ')
        body = metadata['task']['workpiece']
        if body['shape'] != 'circle' or body['kind'] != 'fixed_rigid':
            raise ValueError('Expected the fixed circle pilot workpiece')
        model = archive(model_file.parent, metadata['arrays'])
        tip_nodes = np.flatnonzero(np.all(model['coordinates'] == TIP_REFERENCE_MM, axis=1))
        if len(tip_nodes) != 1:
            raise ValueError('Require one saved reference node at (80,30) mm')
        if result['accepted_states'] != len(result['states']):
            raise ValueError('Saved accepted count differs')
        target = out / label
        target.mkdir()
        case = dict(label=label, model=model, tip_node=int(tip_nodes[0]),
            center=np.asarray(body['center_mm']), radius=float(body['radius_mm']),
            task=metadata['task'], model_sha256=metadata['arrays']['sha256'], result=result, cache=[])
        cases.append(case)
        with (target / 'nodes.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['index', 'original_target_index', 'leg', 'd_mm', 'state_sha256',
                'node_id', 'x_mm', 'y_mm', 'group'] + [part + '_F' + axis + '_N' for part in PARTS for axis in ('x', 'y')])
            for index, record in enumerate(result['states']):
                checkpoint()
                stored = read(directory / record['descriptor_path'], record['descriptor_file_sha256'], True)
                if stored != {key: value for key, value in record.items() if key not in ('descriptor_path', 'descriptor_file_sha256')}:
                    raise ValueError('State/path record differs')
                state = archive(directory, record['state'])
                force = archive(directory, record['forces'])
                destination = target / f'{index:03d}'
                destination.mkdir()
                if any(np.any(state[key][model['workpiece_dofs']]) for key in ('lift', 'fluctuation')):
                    raise ValueError('Saved fixed-body split arrays must both be zero')
                xy = model['coordinates'] + state['lift'].reshape(-1, 2) + state['fluctuation'].reshape(-1, 2)
                counts['geometry_started'] += 1
                counts['region_started'] += 1
                regions = region_overlap(xy, model['connectivity'], np.flatnonzero(model['solid']), model['workpiece_cells'])
                counts['region_completed'] += 1
                if not regions['geometry_valid']:
                    write(destination / 'geometry.json', dict(regions=regions, boundary=None))
                    raise ValueError('Invalid saved convex Q1 geometry; following states stopped')
                counts['boundary_started'] += 1
                boundary = measure_native_workpiece_boundaries(model, metadata, state['lift'], state['fluctuation'])
                counts['boundary_completed'] += 1
                geometry = dict(boundary=boundary, regions=regions, containment_tested=False,
                    scope='Actual Q1 boundary distance and cross-cell interior overlap only; complete set containment and mechanism self-overlap not tested')
                write(destination / 'geometry.json', geometry)
                counts['geometry_completed'] += 1
                counts['nodal_started'] += 1
                nodes = observe_workpiece_nodal_forces(model, force, symmetry_y_mm=case['center'][1],
                    moment_origin_mm=case['center'])
                counts['nodal_completed'] += 1
                write(destination / 'nodal.json', nodes)
                if nodes['summary']['force_on_lower_body_N'] != record['workpiece']['force_on_lower_body_N']:
                    raise ValueError('Nodal sum differs from cached body resultant')
                if not np.array_equal(-nodes['forces_on_body_N']['total'],
                        force['support_reaction'].reshape(-1, 2)[nodes['node_ids']]):
                    raise ValueError('Body holding vectors must oppose ON-body total weak force')
                tip = xy[case['tip_node']]
                witness = tip_boundary(tip, xy, np.asarray(boundary['workpiece_edges'], dtype=np.int64))
                medium = ~model['solid'].copy()
                medium[model['workpiece_cells']] = False
                strain = (np.swapaxes(force['F'], -1, -2) @ force['F'] - np.eye(2)) * .5
                eigen = np.linalg.eigvalsh(strain)
                distance = boundary['groups']['all_exposed']
                row = dict(index=index, original_target_index=record['original_target_index'], leg=record['leg'],
                    d_mm=record['d'], state_sha256=record['state_sha256'], R_input_N=record['R_input'],
                    q_out_mm=record['q_out'], tip_node=case['tip_node'], tip_x_mm=tip[0], tip_y_mm=tip[1],
                    tip_to_raster_boundary_mm=witness['distance_mm'],
                    minimum_boundary_distance_mm=distance['minimum_boundary_distance_mm'],
                    boundary_intersects=distance['intersects'], boundary_roundoff_near_touch=distance['roundoff_near_touch'],
                    raw_overlap=regions['raw_interior_overlap'], strict_overlap=regions['strict_interior_overlap'],
                    roundoff_ambiguous=regions['roundoff_ambiguous'], containment_tested=False,
                    solid_min_J=float(force['J'][model['solid']].min()), medium_min_J=float(force['J'][medium].min()),
                    solid_Green_principal_min=float(eigen[model['solid']].min()),
                    solid_Green_principal_max=float(eigen[model['solid']].max()),
                    medium_max_abs_Hu_per_mm=float(abs(force['Hu'][medium]).max()))
                row.update({part + '_body_F' + axis + '_N': nodes['summary']['force_on_lower_body_N'][part][j]
                    for part in PARTS for j, axis in enumerate(('x', 'y'))})
                case['cache'].append(dict(record=record, row=row, xy=xy, geometry=geometry,
                    boundary=boundary, nodes=nodes, tip=witness, J=force['J'], Hu=force['Hu'], eigen=eigen, medium=medium))
                write(destination / 'derived.json', dict(row=row, tip_surface_witness=witness,
                    scope='Binary64 saved F and actual raster geometry; no fresh HP, pressure or contact qualification'))
                for j, node in enumerate(nodes['node_ids']):
                    group = next(name for name in GROUPS if nodes['masks'][name][j])
                    writer.writerow([index, record['original_target_index'], record['leg'], record['d'],
                        record['state_sha256'], int(node), *nodes['coordinates_mm'][j], group]
                        + [float(value) for part in PARTS for value in nodes['forces_on_body_N'][part][j]])
        rows = [saved['row'] for saved in case['cache']]
        if not rows:
            raise ValueError('No saved accepted state')
        with (target / 'states.csv').open('x', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        write(target / 'summary.json', dict(production_status=result['status'], reference_available=False,
            accepted_states=len(rows), rows=rows, containment_tested=False,
            force_scope='Signed global-axis lower-body weak resultants, not circular local-normal pressure or total normal force'))

        force_max = max(float(np.linalg.norm(saved['nodes']['forces_on_body_N'][part], axis=1).max())
            for saved in case['cache'] for part in PARTS)
        force_scale = 4. / force_max if force_max else 1.
        case['xlim'] = (min(-2., min(float(saved['xy'][:, 0].min()) - 2 for saved in case['cache'])),
            max(86., max(float(saved['xy'][:, 0].max()) + 2 for saved in case['cache'])))
        case['ylim'] = (min(-2., min(float(saved['xy'][:, 1].min()) - 2 for saved in case['cache'])),
            max(82., max(2 * case['center'][1] - float(saved['xy'][:, 1].min()) + 2 for saved in case['cache'])))
        case['peak_index'] = int(np.argmax([record['d_mm'] for record in rows]))
        peak_index, last_index = case['peak_index'], len(rows) - 1
        ds = [row['d_mm'] for row in rows]
        checkpoint()
        fig, axes = plt.subplots(2, 3, figsize=(17, 10))
        for i, (index, caption) in enumerate(((peak_index, 'MAXIMUM ACCEPTED d'), (last_index, 'LAST ACCEPTED'))):
            draw(axes[i, 0], case, index)
            draw(axes[i, 1], case, index, zoom=True)
            axes[i, 0].set_title(caption + ' | ' + axes[i, 0].get_title(), fontsize=9)
        axes[0, 2].plot(ds, [row['R_input_N'] for row in rows], 'ko-', label='Half-model input R')
        axes[0, 2].set(xlabel='Mean input d (mm)', ylabel='Input R (N)', title='Actual accepted load path')
        port_axis = axes[0, 2].twinx()
        port_axis.plot(ds, [row['q_out_mm'] for row in rows], 's--', color='#2860aa', label='Weighted q_out')
        port_axis.set_ylabel('q_out (mm); not a gap', color='#2860aa')
        axes[0, 2].legend(loc='upper left', fontsize=8)
        port_axis.legend(loc='lower right', fontsize=8)
        for part in PARTS:
            axes[1, 2].plot(ds, [row[part + '_body_Fy_N'] for row in rows], 'o-', ms=3, label=part + ' Fy')
        axes[1, 2].set(xlabel='Mean input d (mm)', ylabel='Signed lower-body Fy (N)', title='Global y weak resultant; not local normal pressure')
        axes[1, 2].legend(fontsize=8)
        fig.suptitle('Circle saved-state observations | x1; full views use a visual symmetry mirror | analytic circle is reference only', fontsize=12)
        fig.tight_layout()
        fig.savefig(out / 'comparison.png', dpi=150)
        plt.close(fig)
        checkpoint()

        fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
        for key, title in (('minimum_boundary_distance_mm', 'Actual Q1 boundary minimum'),
                           ('tip_to_raster_boundary_mm', 'Tip to actual Q1 boundary')):
            axes[0].plot(ds, [row[key] for row in rows], 'o-', ms=3, label=title)
        axes[0].set(xlabel='Mean input d (mm)', ylabel='Unsigned distance (mm)', title='Distances are not signed gaps; containment not tested')
        for axis, coordinate in zip(axes[1:], ('x', 'y')):
            for part in PARTS:
                axis.plot(ds, [row[part + '_body_F' + coordinate + '_N'] for row in rows], 'o-', ms=3, label=part)
            axis.set(xlabel='Mean input d (mm)', ylabel='Signed F' + coordinate + ' (N)', title='Lower-body global-axis weak resultant')
        for axis in axes:
            axis.legend(fontsize=7)
            axis.grid(alpha=.2)
        fig.suptitle('Actual accepted order | boundary intersections and cross-cell overlap are retained in JSON; no pressure or effective-clamp qualification', fontsize=10)
        fig.tight_layout()
        fig.savefig(out / 'distances_forces.png', dpi=150)
        plt.close(fig)
        checkpoint()

        saved = case['cache'][peak_index]
        fields = [('Solid mean J', model['solid'], saved['J'].mean(axis=1)),
            ('Solid max in-plane Green principal', model['solid'], saved['eigen'][..., 1].max(axis=1)),
            ('Free-medium mean J', saved['medium'], saved['J'].mean(axis=1)),
            ('Free-medium Hu Frobenius (1/mm)', saved['medium'], np.linalg.norm(saved['Hu'].reshape(len(model['solid']), -1), axis=1))]
        field_ranges = [(float(values[mask].min()), float(values[mask].max())) for _, mask, values in fields]
        fig, axes = plt.subplots(1, 4, figsize=(18, 4.5))
        for axis, (title, mask, values), limits in zip(axes, fields, field_ranges):
            collection = PolyCollection(saved['xy'][model['connectivity'][mask]], array=values[mask], cmap='viridis')
            collection.set_clim(*limits)
            axis.add_collection(collection)
            axis.add_collection(PolyCollection(saved['xy'][model['connectivity'][model['workpiece_cells']]], facecolors='#e3d6be'))
            axis.autoscale()
            axis.set_aspect('equal')
            axis.set(xlabel='x (mm)', ylabel='y (mm)', title=title)
            axis.tick_params(labelsize=7)
            fig.colorbar(collection, ax=axis, fraction=.046, pad=.035)
        fig.suptitle(f"Maximum accepted d={rows[peak_index]['d_mm']:g} mm | lower half, x1 | saved binary64 fields; not fresh HP qualified", fontsize=11)
        fig.tight_layout()
        fig.savefig(out / 'peak_fields.png', dpi=150)
        plt.close(fig)
        checkpoint()

        frames = []
        for index, saved in enumerate(case['cache']):
            checkpoint()
            fig, axes = plt.subplots(1, 3, figsize=(14, 7))
            for axis, part in zip(axes, PARTS):
                draw(axis, case, index, component=part, force_scale=force_scale)
                axis.set_title(part + ' ON-body nodal weak vectors | ' + str(index), fontsize=9)
            glyph = f'{force_max:.5g} N = 4 mm glyph' if force_max else 'all nodal vectors zero'
            fig.suptitle(f"{label}: {index}/{len(rows)-1} {saved['record']['leg']} d={saved['record']['d']:g} mm | x1; visual mirror | {glyph}\n"
                'All body nodes including symmetry-cut/interior nodes; global weak vectors, not local pressure; no interpolation', fontsize=10)
            fig.tight_layout()
            fig.canvas.draw()
            frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()).convert('RGB'))
            plt.close(fig)
        frames[0].save(target / 'actual_states.gif', save_all=True, append_images=frames[1:],
            duration=300, loop=0, optimize=False, disposal=2)
        for frame in frames:
            frame.close()
        with Image.open(target / 'actual_states.gif') as gif:
            if gif.n_frames != len(rows):
                raise ValueError('GIF must retain every accepted index')
        checkpoint()
        check_pure()
        for path, digest in pins.items():
            if file_hash(path) != digest:
                raise ValueError('Bound source/input changed')
        for path in out.rglob('*'):
            if path.is_file():
                outputs[path.relative_to(out).as_posix()] = file_hash(path)
        checkpoint()
        output_identity_seal = 'complete_inside_view_window'
    except BaseException as error:
        failure = repr(error)
        raise
    finally:
        write(out / 'view.json', dict(schema_version='saved-circle-workpiece-views-1.0',
            status='pass' if failure is None else 'failed', failure=failure, **counts,
            new_F_T_model_solver_HP_calls=0 if pure else None, mechanical_hooks_monitored=False,
            zero_mechanics_basis='Pinned pure module origins and saved-array derivations, not dynamic mechanical hooks',
            input_source_bindings={path.relative_to(root).as_posix(): digest for path, digest in pins.items()}, outputs=outputs,
            output_identity_seal=output_identity_seal,
            cases=[dict(label=item['label'], production_status=item['result']['status'],
                production_path_completed=item['result']['path_completed'], unload_endpoint_reached=item['result']['unload_endpoint_reached'],
                reference_available=False, saved_accepted_states=item['result']['accepted_states'], observed_states=len(item['cache']),
                peak_index=item.get('peak_index'), last_index=len(item['cache']) - 1,
                tip_node=item['tip_node'], task=item['task'], model_sha256=item['model_sha256']) for item in cases],
            common_nodal_force_scale=dict(max_force_N=force_max, display_length_mm=4, all_body_nodes=True, components=PARTS),
            common_peak_field_ranges=field_ranges if 'field_ranges' in locals() else None,
            readset_scope='New model once and each new accepted state/force NPZ once decoded; all declared fields identity checked; no tangent or prior-run arrays',
            mirroring='Full-structure/GIF visualization only; reflected Fy changes sign; numerical tables retain lower-half resultants and solved DOFs',
            tip_selection=dict(reference_coordinates_mm=list(TIP_REFERENCE_MM), method='Unique exact saved reference coordinate; no snapping'),
            strain_scope='Original binary64 in-plane Green eigenvalue formula from saved F; not fresh HP qualified',
            distance_scope='Actual straight Q1 physical edges; symmetry cut excluded; unsigned boundary and tip distances, not signed gaps or contact proof',
            overlap_scope='Existing generic convex-cell cross-region overlap; complete set containment and mechanism self-overlap not tested',
            analytic_circle_scope='Fixed display reference only, never used in distance or force calculations',
            containment_tested=False, contact_pressure_clamping_qualified=False,
            elapsed_seconds=perf_counter() - STARTED, sampled_peak_RSS_bytes=peak))


if __name__ == '__main__':
    main()
