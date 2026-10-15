"""Prepare one distinct LF gripper and inspect its undeformed native model."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from zipfile import ZipFile


def _hash_file(path, checkpoint):
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            checkpoint('checkpoint')
    return digest.hexdigest()


def _write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def _draw(project, old_geometries, differences, output, checkpoint):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch, Rectangle
    import numpy as np

    checkpoint('plot_started')
    geometry, model, regions = project.geometry, project.model, project.region_metadata
    x0, y0 = geometry.grid['origin_mm']
    width, height = geometry.grid['extent_mm']
    extent = (x0, x0+width, y0, y0+height)
    body = regions['workpiece']['definition']
    radius = body['side_mm']/2
    bx, by = body['center_mm'][0]-radius, body['center_mm'][1]-radius
    body_height = y0+height-by
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
    for ax in axes.flat[:2]:
        ax.imshow(geometry.solid, origin='lower', extent=extent, interpolation='nearest',
                  cmap=ListedColormap(['#edf3f7', '#244867']), vmin=0, vmax=1)
        ax.add_patch(Rectangle((bx, by), body['side_mm'], body_height, facecolor='#bfc4cc',
                               edgecolor='#555d69', linewidth=1.5, label='Fixed lower-body overlay'))
        for name, color in (('input', '#078457'), ('output', '#b62b37')):
            port = regions['ports'][name]
            points = model.coordinates[port['nodes']]
            ax.plot(points[:, 0], points[:, 1], 'o-', color=color, markersize=4, label=name+' port nodes')
        ax.set(aspect='equal', xlabel='x (mm)', ylabel='y (mm)')
    ax = axes[0, 0]
    for name, color, marker in (('support', '#bd650f', '^'), ('entity_symmetry', '#715694', '.')):
        points = model.coordinates[regions[name]['attached_nodes']]
        ax.scatter(points[:, 0], points[:, 1], color=color, marker=marker, s=28,
                   label=name+' attached nodes', zorder=4)
    background = project.task['background_symmetry']['points_mm']
    ax.plot([p[0] for p in background], [p[1] for p in background], ':', color='#715694',
            linewidth=1.5, label='Applied background uy=0')
    for name, color in (('input', '#078457'), ('output', '#b62b37')):
        port = regions['ports'][name]
        centre = np.asarray(port['points_mm']).mean(axis=0)
        direction = np.asarray(port['direction'])
        ax.annotate('', xy=centre+4*direction, xytext=centre,
                    arrowprops=dict(arrowstyle='->', color=color, linewidth=1.7))
    ax.axvline(80, linestyle='--', color='#7195ad', linewidth=1)
    ax.set(xlim=(-2, 86), ylim=(-2, 43), title='New wave design: actual undeformed constraints and ports')
    ax.legend(fontsize=7, loc='lower right')
    ax = axes[0, 1]
    hx, hy = geometry.grid['cell_size_mm']
    for x in np.arange(60, 84+hx, hx):
        ax.axvline(x, color='#bac2ca', linewidth=.4, alpha=.65)
    for y in np.arange(26, 40+hy, hy):
        ax.axhline(y, color='#bac2ca', linewidth=.4, alpha=.65)
    port = regions['ports']['output']
    points = model.coordinates[port['nodes']]
    for point, weight in zip(points, port['weights']):
        ax.annotate(format(weight, '.3g'), point, xytext=(5, 0), textcoords='offset points', fontsize=7)
    ax.set(xlim=(59, 84), ylim=(26, 40.5), title='Tip / fixed lower body: native grid and output weights')
    ax.legend(fontsize=8, loc='lower left')
    colors = ['#f7f9fb', '#a5adb6', '#3f83b1', '#d98732']
    legend = [Patch(facecolor=colors[0], edgecolor='#d5dbe1', label='Common void'),
              Patch(facecolor=colors[1], label='Common solid'),
              Patch(facecolor=colors[2], label='-: removed from old solid'),
              Patch(facecolor=colors[3], label='+: added new solid')]
    for ax, (label, old) in zip(axes[1], old_geometries.items()):
        new_solid, old_solid = geometry.solid.astype(bool), old.solid.astype(bool)
        categories = np.zeros_like(geometry.solid, dtype=np.uint8)
        categories[new_solid & old_solid] = 1
        categories[old_solid & ~new_solid] = 2
        categories[new_solid & ~old_solid] = 3
        ax.imshow(categories, origin='lower', extent=extent, interpolation='nearest',
                  cmap=ListedColormap(colors), vmin=0, vmax=3)
        counts = differences[label]
        ax.set(aspect='equal', xlabel='x (mm)', ylabel='y (mm)',
               title=f"New minus {label}: +{counts['added_solid_cells']} / -{counts['removed_solid_cells']} cells")
        ax.legend(handles=legend, fontsize=8, loc='lower right')
    fig.suptitle('UNDEFORMED x1: geometry / compatibility only\nArrows are reference port directions; no force, displacement or contact result', fontsize=12)
    fig.savefig(output/'undeformed_compatibility.png', dpi=160)
    plt.close(fig)
    checkpoint('plot_completed')


def prepare_third(repo, protocol, output, checkpoint=lambda event: None):
    """Convert, construct and save once; caller owns the bounded resource window."""
    repo, output = Path(repo).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = dict(status='running', checks={}, force_calls=0, tangent_calls=0, solver_calls=0,
        HP_calls=0, response_evaluated=False, mechanical_hooks_monitored=False,
        zero_mechanics_basis='LF conversion/right padding, native map/model reference operators, geometry qualification, storage and undeformed plotting only; no response entry called',
        dependency_scope='HF imports may import JAX and register jit functions; no force/tangent/JIT execution',
        path_executed=False, mechanical_qualified=False, HF5_qualified=False)

    def check(name, condition):
        if not bool(condition):
            raise ValueError('Compatibility check failed: '+name)
        report['checks'][name] = True
        checkpoint('checkpoint')

    def relative(path):
        return Path(path).resolve().relative_to(repo).as_posix()

    try:
        source = protocol['source_zip']
        archive_path = Path(source['path'])
        checkpoint('zip_hash_started')
        check('source_archive_size', archive_path.stat().st_size == source['bytes'])
        check('source_archive_sha256', _hash_file(archive_path, checkpoint) == source['sha256'])
        checkpoint('zip_hash_completed')
        sources = output/'sources'
        sources.mkdir()
        extracted = {}
        checkpoint('source_extract_started')
        with ZipFile(archive_path) as archive:
            for kind in ('json', 'npz'):
                member = source['members'][kind]
                raw = archive.read(member['name'])
                check('source_'+kind+'_sha256', sha256(raw).hexdigest() == member['sha256'])
                destination = sources/('design.'+kind)
                with destination.open('xb') as stream:
                    stream.write(raw)
                extracted[kind] = dict(path=relative(destination), member=member['name'],
                                       sha256=member['sha256'], bytes=len(raw))
        checkpoint('source_extract_completed')
        descriptor = json.loads((sources/'design.json').read_bytes())
        check('selected_LF_geometry_id', descriptor['geometry_id'] == protocol['lf_geometry_id'])
        template_record = protocol['task_template']
        template_file = repo/template_record['path']
        template_raw = template_file.read_bytes()
        check('task_template_sha256', sha256(template_raw).hexdigest() == template_record['sha256'])
        template = json.loads(template_raw)
        sys.path.insert(0, str(repo/'hf_repo/src'))
        import numpy as np
        from hf_eval.data import ARRAY_NAMES, load_geometry
        from hf_eval.lf_native_inputs import prepare_native_lf_inputs
        from hf_eval.native_project import build_native_project, write_native_project

        checkpoint('input_prepare_started')
        paths = prepare_native_lf_inputs(sources/'design.json', template_file, output/'case',
            repo_root=repo, right_medium_width_mm=4.0,
            expected_descriptor_sha256=source['members']['json']['sha256'])
        checkpoint('input_prepare_completed')
        task = json.loads(Path(paths['task_file']).read_bytes())
        check('task_non_geometry_exact', {k:v for k,v in task.items() if k != 'geometry'} ==
              {k:v for k,v in template.items() if k != 'geometry'})
        checkpoint('model_build_started')
        project = build_native_project(paths['geometry_file'], task)
        checkpoint('model_build_completed')
        geometry, model, regions = project.geometry, project.model, project.region_metadata
        report.update(source_archive=dict(path=source['path'], sha256=source['sha256'], bytes=source['bytes']),
            extracted_source=extracted, LF_design_id=descriptor['design_id'], LF_geometry_id=descriptor['geometry_id'],
            geometry_id=geometry.geometry_id, source_geometry=regions['source_geometry'],
            grid=geometry.grid, counts=regions['counts'], material=project.material, ports=regions['ports'],
            fixed_workpiece=regions['workpiece'], qualification=project.qualification,
            support=regions['support'], entity_symmetry=regions['entity_symmetry'],
            background_symmetry=regions['background_symmetry'], task_sha256=project.task_hash,
            task=task, case_paths={key: relative(path) for key, path in paths.items()})
        checkpoint('model_write_started')
        model_file = write_native_project(project, output/'model')
        report['model_file'] = relative(model_file)
        checkpoint('model_write_completed')
        check('new_h05_grid', geometry.grid['shape_yx'] == [80, 168] and
              geometry.grid['cell_size_mm'] == [.5, .5] and geometry.grid['extent_mm'] == [84., 40.])
        check('no_resampling_original_native', descriptor['grid']['native_mesh'] == [160, 80]
              and descriptor['grid']['cell_mm'] == [.5, .5])
        checkpoint('source_array_read_started')
        mask_checks = {}
        with np.load(sources/'design.npz', allow_pickle=False) as archive:
            for hf_name in ARRAY_NAMES:
                lf_name = 'design_domain' if hf_name == 'design' else hf_name
                original = archive[lf_name]
                check(hf_name+'_lossless_mask', np.array_equal(
                    geometry.arrays[hf_name][:, :160], original.astype(np.uint8)))
                check(hf_name+'_right_columns', np.all(geometry.arrays[hf_name][:, 160:] ==
                      (1 if hf_name == 'passive_void' else 0)))
                mask_checks[hf_name] = dict(source_field=lf_name, source_shape=list(original.shape),
                    source_dtype=original.dtype.name, native_cells=int(original.sum()),
                    final_cells=int(geometry.arrays[hf_name].sum()))
        report['mask_comparison'] = mask_checks
        checkpoint('source_array_read_completed')
        old_geometries, differences = {}, {}
        check('two_comparison_geometries', set(protocol['comparison_geometries']) == {'M', 'LF'})
        for label, record in protocol['comparison_geometries'].items():
            checkpoint('geometry_read_started')
            path = repo/record['path']
            check(label+'_descriptor_sha256', sha256(path.read_bytes()).hexdigest() == record['descriptor_file_sha256'])
            old = load_geometry(path)
            check(label+'_arrays_sha256', old.metadata['arrays']['sha256'] == record['arrays_sha256'])
            check(label+'_geometry_id', old.geometry_id == record['geometry_id'])
            check(label+'_same_grid', old.grid == geometry.grid)
            check(label+'_same_physical_tags', old.metadata['region_tags'] == geometry.metadata['region_tags'])
            added = int(np.count_nonzero(geometry.solid.astype(bool) & ~old.solid.astype(bool)))
            removed = int(np.count_nonzero(old.solid.astype(bool) & ~geometry.solid.astype(bool)))
            check(label+'_different_solid_mask', added+removed > 0)
            differences[label] = dict(old_geometry_id=old.geometry_id, added_solid_cells=added,
                removed_solid_cells=removed, xor_solid_cells=added+removed,
                xor_area_mm2=(added+removed)*model.hx*model.hy,
                scope='Geometric cell difference only; no performance or mechanical ranking')
            old_geometries[label] = old
            checkpoint('geometry_read_completed')
        report['differences'] = differences
        for name in ('shared_edge_connectivity', 'support_attachment', 'input_attachment',
                     'output_attachment', 'port_support_component_link'):
            check('geometry_'+name, project.qualification['checks'][name]['status'] == 'pass')
        check('body_shape', regions['workpiece']['definition'] == template['workpiece'])
        check('body_counts', regions['workpiece']['selected_cells'] == 648 and
              regions['workpiece']['incident_nodes'] == 703 and regions['workpiece']['fixed_dofs'] == 1406)
        check('body_dofs_fixed', np.all(np.isin(regions['workpiece']['dofs'], model.fixed_dofs)))
        check('fixed_free_partition', len(np.intersect1d(model.fixed_dofs, model.free)) == 0 and
              np.array_equal(np.union1d(model.fixed_dofs, model.free), np.arange(model.ndof)))
        for name, direction in (('input', [1., 0.]), ('output', [0., 1.])):
            port = regions['ports'][name]
            check(name+'_port_contract', port['direction'] == direction and
                  port['weights'] == [.125, .25, .25, .25, .125] and
                  port['averaging'] == 'normalized_reference_arclength_trapezoid')
        report['initial_gap_scope'] = regions['workpiece']['initial_gap_scope']
        report['compatibility_scope'] = 'Undeformed geometry, attached boundaries, weighted ports and fixed-body overlay; no stiffness nonsingularity, equilibrium, pressure or effective-clamp result'
        report['JAX_module_loaded'] = 'jax' in sys.modules
        _draw(project, old_geometries, differences, output, checkpoint)
        report.update(status='pass', figure=relative(output/'undeformed_compatibility.png'))
    except Exception as error:
        report.update(status='not_pass', error=dict(exception_class=type(error).__name__, reason=str(error)),
                      partial_outputs_retained=True)
        _write(output/'compatibility.json', report)
        raise
    _write(output/'compatibility.json', report)
    checkpoint('report_written')
    return report


def main(argv=None, checkpoint=lambda event: None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    protocol_file = (repo/args.protocol).resolve()
    protocol = json.loads(protocol_file.read_bytes())
    report = prepare_third(repo, protocol, repo/protocol['output_directory'], checkpoint)
    print(json.dumps(dict(status=report['status'], geometry_id=report['geometry_id'], counts=report['counts'])))
    return report


if __name__ == '__main__':
    main()
