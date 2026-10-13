"""L-PREP1: prepare/verify three LF input packages and show undeformed declarations."""
import time
MODULE_STARTED = time.monotonic()
import argparse
from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import runpy
import sys
from unittest.mock import patch


CASES = [
    dict(alias='inverter_canonical', source_descriptor='lf_data_preparation/v2_adapter_001/inputs/inverter_canonical/design.json',
         task_template='lf_data_preparation/native_model_001/tasks/inverter_canonical.json', right_medium_width_mm=None, entry='API'),
    dict(alias='gripper_canonical', source_descriptor='lf_data_preparation/v2_adapter_001/inputs/gripper_canonical/design.json',
         task_template='lf_data_preparation/native_model_001/tasks/gripper_canonical.json', right_medium_width_mm=4., entry='API'),
    dict(alias='gripper_native_fine', source_descriptor='lf_data_preparation/v2_adapter_001/inputs/gripper_native_fine/design.json',
         task_template='lf_data_preparation/native_interface_001/saved_extension_004/proposed_task.json', right_medium_width_mm=4., entry='CLI_runpy_same_interpreter'),
]
TARGETS = ('hf_repo/src/hf_eval/lf_native_inputs.py', 'hf_repo/scripts/prepare_native_lf_inputs.py')
EXPECTED = dict(installation=2, real_preparations=3, API_preparations=2, CLI_entry=1,
                negative_instances=9, verification=3, npz_load=11, plot=1)
LF_FIELDS = ('solid', 'passive_solid', 'passive_void', 'design_domain')
MASK_MAP = dict(solid='solid', passive_solid='passive_solid', passive_void='passive_void', design_domain='design')


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_bytes())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def draw_prepared(verified, output, checkpoint):
    """Use already verified in-memory masks; do not reopen arrays or apply a task."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Rectangle
    checkpoint()
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.4), constrained_layout=True)
    views = []
    for ax, item in zip(axes, verified):
        geometry, task = item['geometry'], item['task']
        x, y = geometry.grid['origin_mm']
        width, height = geometry.grid['extent_mm']
        codes = geometry.arrays['solid'].copy()
        codes[geometry.arrays['passive_solid'].astype(bool)] = 2
        codes[geometry.arrays['passive_void'].astype(bool)] = 3
        ax.imshow(codes, origin='lower', interpolation='nearest', extent=[x, x + width, y, y + height],
                  vmin=0, vmax=3, cmap=ListedColormap(['#f4f5f7', '#344054', '#8c566f', '#dcedf8']))
        native_width = item['native_extent_mm'][0]
        if width > native_width:
            ax.axvline(x + native_width, color='#2478a0', linestyle='--', linewidth=1)
            ax.text(x + native_width + .5, y + 2, 'HF medium\n+4 mm', fontsize=8, color='#155675', rotation=90)
        for name, tag in geometry.metadata['region_tags'].items():
            points = tag['points_mm']
            ax.plot([p[0] for p in points], [p[1] for p in points],
                    color={'support':'#b54708', 'symmetry':'#667085', 'input':'#00805a', 'output':'#b42318'}[name], linewidth=2)
            if name in ('input', 'output'):
                a, b = points
                midpoint = [(a[i] + b[i]) / 2 for i in range(2)]
                direction = tag['direction']
                ax.annotate('', xy=(midpoint[0] + 4 * direction[0], midpoint[1] + 4 * direction[1]), xytext=midpoint,
                            arrowprops=dict(arrowstyle='->', color='#00805a' if name == 'input' else '#b42318'))
        background = task.get('background_symmetry')
        if background:
            a, b = background['points_mm']
            ax.plot([a[0], b[0]], [a[1], b[1]], ':', color='#8d6eb4', linewidth=1.7)
        body = task.get('workpiece')
        if body:
            assert body['shape'] == 'square'
            cx, cy = body['center_mm']
            side = body['side_mm']
            ax.add_patch(Rectangle((cx - side / 2, cy - side / 2), side, side, fill=False,
                                  edgecolor='#9b51e0', linestyle='--', linewidth=1.6))
            ax.text(cx, cy - side / 2 - 2, 'square declaration\nnot applied', ha='center', fontsize=8, color='#7834a8')
        ax.set(xlim=(-3, 87), ylim=(-2, 51), aspect='equal', xlabel='x (mm)', ylabel='y (mm)',
               title=item['alias'] + '\n' + task['schema_version'] + f"; h={geometry.grid['cell_size_mm'][0]:g} mm")
        ax.text(2, 44, 'model domain: y ≤ 40; above: declaration only', fontsize=7, color='#667085')
        ax.text(x + 2, y + 2, 'Undeformed masks\nBC / ports: declarations', fontsize=8,
                bbox=dict(facecolor='white', alpha=.86, edgecolor='none'))
        views.append(dict(alias=item['alias'], grid=geometry.grid, geometry_id=geometry.geometry_id,
                          geometry_file=item['paths']['geometry_file'], task_file=item['paths']['task_file'],
                          native_extent_mm=item['native_extent_mm'], region_tags=geometry.metadata['region_tags'],
                          background_symmetry_declaration=background, workpiece_declaration=body,
                          declarations_applied=False, arrows='reference directions only; not force or displacement'))
    fig.suptitle('PREPARATION ONLY — NO MECHANICS\nsolid: dark; passive solid: mauve; passive void / medium: light blue\ninput: green; output: red; support: brown; symmetry: grey; dotted purple: task background declaration', fontsize=10)
    checkpoint()
    fig.savefig(output / 'prepared_inputs.png', dpi=160)
    plt.close(fig)
    checkpoint()
    write_json(output / 'view.json', dict(schema_version='lf-native-preparation-view-1.0', status='pass', cases=views,
        image='prepared_inputs.png', undeformed=True, geometry_task_model_consistency_evaluated=False,
        model_created=False, force_evaluated=False, tangent_evaluated=False, solver_executed=False,
        HP_evaluated=False, mechanical_qualified=False, HF5_qualified=False))


def execute(repo, protocol_file):
    started = MODULE_STARTED
    protocol = read_json(protocol_file)
    limit = protocol['phases']['preparation']['helper_seconds']
    output = repo / protocol['preparation_output']
    stop_file = output.parent / 'stop_requested.txt'
    counts = {name + suffix: 0 for name in EXPECTED for suffix in ('_started', '_completed')}
    record = dict(schema_version='lf-native-preparation-execution-1.0', card='L-PREP1', status='running', execution_closed=False,
        counts=counts, source_baseline_commit=protocol['source_baseline_commit'], protocol_sha256=digest(protocol_file),
        installed_source_sha256={}, cases=[], negative_instances=[], npz_load_events=[], outputs={},
        field_reads_monitored=False, static_field_read_occurrences=44, static_distinct_decoded_NPZ=8,
        static_distinct_decoded_fields=32, field_count_basis='3 converters + 2 padding loads + 6 independent LF/HF verification loads; four fields per load',
        mechanical_hooks_monitored=False, model_constructions=0, force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        mechanics_zero_basis='Preparation API/converter/padding/task validation, mask verification and one undeformed display only; no dynamic mechanics hooks',
        independent_reference_associated=False, mechanical_qualified=False, HF5_qualified=False,
        CLI_scope='One installed CLI __main__ entry via runpy in this interpreter, with actual argv/stdout/SystemExit; not interpreter startup validation')
    phase = 'binding'

    def checkpoint():
        if stop_file.exists():
            raise RuntimeError('cooperative stop requested')
        if time.monotonic() - started > limit:
            raise TimeoutError('original helper window exhausted')

    def bindings():
        for relative, expected in protocol['bindings'].items():
            checkpoint()
            assert digest(repo / relative) == expected, 'binding changed: ' + relative

    def begin(name):
        checkpoint()
        counts[name + '_started'] += 1

    def complete(name):
        checkpoint()
        counts[name + '_completed'] += 1

    def seal():
        checkpoint()
        identities = {}
        for path in sorted(output.rglob('*')):
            if path.is_file() and path.name != 'execution_receipt.json':
                checkpoint()
                identities[path.relative_to(repo).as_posix()] = dict(sha256=digest(path), bytes=path.stat().st_size)
        checkpoint()
        record['outputs'] = identities
        record['output_identity_seal'] = 'complete_inside_original_helper_window'

    try:
        assert protocol['card'] == 'L-PREP1'
        assert [{key: row[key] for key in case} for row, case in zip(protocol['cases'], CASES)] == CASES
        assert len(protocol['cases']) == len(CASES)
        for row, case in zip(protocol['cases'], CASES):
            assert row['output_subdirectory'] == 'cases/' + case['alias']
            assert row['expected_descriptor_sha256'] == protocol['bindings'][case['source_descriptor']]
        assert set(protocol['install_sources']) == set(TARGETS)
        assert not output.exists()
        bindings()
        output.mkdir(parents=True, exist_ok=False)
        write_json(output / 'execution_receipt.json', record)
        phase = 'installation'
        for target in TARGETS:
            begin('installation')
            entry = protocol['install_sources'][target]
            source, destination = repo / entry['source'], repo / target
            assert digest(source) == entry['sha256']
            assert not destination.exists() and not destination.is_symlink()
            with destination.open('xb') as stream:
                stream.write(source.read_bytes())
            assert digest(destination) == entry['sha256']
            record['installed_source_sha256'][target] = entry['sha256']
            complete('installation')
            write_json(output / 'installation_receipt.json', dict(installed_source_sha256=record['installed_source_sha256'], rollback=False))
        sys.path.insert(0, str(repo / 'hf_repo/src'))
        import numpy as np
        from hf_eval import data, lf_v2, lf_native_inputs
        assert Path(lf_native_inputs.__file__).resolve() == (repo / TARGETS[0]).resolve()
        prepare = lf_native_inputs.prepare_native_lf_inputs
        verified = []
        original_load = np.load

        def observed_load(*args, **kwargs):
            begin('npz_load')
            frame = sys._getframe(1)
            caller = frame.f_code.co_name
            if caller == 'convert_lf_v2':
                opened_path = frame.f_locals['source_descriptor'].with_name('design.npz')
            elif caller == 'load_geometry':
                opened_path = frame.f_locals['array_path']
            else:
                opened_path = Path(args[0]) if not hasattr(args[0], 'read') else None
            del frame
            event = dict(phase=phase, input_kind='byte_buffer' if hasattr(args[0], 'read') else 'path',
                         path=str(opened_path.resolve()) if opened_path is not None else None, caller=caller,
                         field_count_basis='four declared fields; accesses not instrumented')
            record['npz_load_events'].append(event)
            archive = original_load(*args, **kwargs)
            complete('npz_load')
            event['opened'] = True
            return archive

        with patch.object(np, 'load', observed_load):
            for case in CASES:
                phase = 'prepare_' + case['alias']
                begin('real_preparations')
                case_dir = output / 'cases' / case['alias']
                source, template = repo / case['source_descriptor'], repo / case['task_template']
                source_pin = protocol['bindings'][case['source_descriptor']]
                if case['entry'] == 'API':
                    begin('API_preparations')
                    if case['alias'] == 'inverter_canonical':
                        # An ordinary alternate cwd proves explicit repo_root controls all relative inputs.
                        with patch.object(Path, 'cwd', return_value=output):
                            paths = prepare(case['source_descriptor'], case['task_template'], case_dir.relative_to(repo), repo_root=repo,
                                right_medium_width_mm=case['right_medium_width_mm'], expected_descriptor_sha256=source_pin)
                    else:
                        previous_cwd = Path.cwd()
                        try:
                            os.chdir(repo)
                            paths = prepare(case['source_descriptor'], case['task_template'], case_dir.relative_to(repo),
                                right_medium_width_mm=case['right_medium_width_mm'], expected_descriptor_sha256=source_pin)
                        finally:
                            os.chdir(previous_cwd)
                    complete('API_preparations')
                else:
                    begin('CLI_entry')
                    old_argv, old_path = sys.argv[:], sys.path[:]
                    stdout = StringIO()
                    sys.argv = [str(repo / TARGETS[1]), '--repo', str(repo), '--source-descriptor', case['source_descriptor'],
                        '--task-template', case['task_template'], '--output', case_dir.relative_to(repo).as_posix(), '--right-medium-width-mm', '4',
                        '--expected-descriptor-sha256', source_pin]
                    try:
                        with redirect_stdout(stdout):
                            try:
                                runpy.run_path(str(repo / TARGETS[1]), run_name='__main__')
                            except SystemExit as error:
                                assert error.code == 0, 'CLI did not exit zero'
                            else:
                                raise AssertionError('CLI __main__ did not terminate through SystemExit')
                        paths = json.loads(stdout.getvalue())
                    finally:
                        sys.argv, sys.path = old_argv, old_path
                    (output / 'CLI_stdout.txt').write_text(stdout.getvalue(), encoding='utf-8')
                    complete('CLI_entry')
                complete('real_preparations')
                phase = 'verify_' + case['alias']
                begin('verification')
                assert set(paths) == {'geometry_file', 'task_file', 'input_manifest'}
                for path in paths.values():
                    assert Path(path).is_absolute() and Path(path).is_relative_to(case_dir)
                geometry = data.load_geometry(paths['geometry_file'])
                source_record, template_record = read_json(source), read_json(template)
                ny, nx = reversed(source_record['grid']['native_mesh'])
                with np.load(source.with_name('design.npz'), allow_pickle=False) as archive:
                    assert set(archive.files) == set(LF_FIELDS)
                    for lf_name, hf_name in MASK_MAP.items():
                        array = archive[lf_name]
                        assert array.dtype == np.dtype(bool) and array.shape == (ny, nx)
                        assert np.array_equal(geometry.arrays[hf_name][:, :nx], array)
                expected_columns = {'inverter_canonical': 0, 'gripper_canonical': 4, 'gripper_native_fine': 8}[case['alias']]
                assert geometry.grid['shape_yx'] == [ny, nx + expected_columns]
                assert geometry.grid['origin_mm'] == source_record['grid']['origin_mm']
                assert geometry.grid['cell_size_mm'] == source_record['grid']['cell_mm']
                assert geometry.grid['extent_mm'] == [80. + (4. if expected_columns else 0.), 40.]
                assert geometry.grid['axes'] == [[1., 0.], [0., 1.]] and geometry.grid['array_order'] == 'C_yx_bottom_up'
                assert geometry.metadata['thickness_mm'] == source_record['grid']['thickness_mm'] == 20.
                assert geometry.metadata['model_extent'] == dict(kind='lower_half', symmetry_axis=dict(normal=[0., 1.], offset_mm=40.))
                for name in data.ARRAY_NAMES:
                    assert geometry.arrays[name].dtype == np.dtype('uint8')
                    assert np.all(geometry.arrays[name][:, nx:] == (1 if name == 'passive_void' else 0))
                tags = geometry.metadata['region_tags']
                for tag_name, lf_name in (('support', 'support'), ('symmetry', 'symmetry_solid'), ('input', 'input_port'), ('output', 'output_port')):
                    original = source_record['regions_mm'][lf_name]
                    assert tags[tag_name]['points_mm'] == original['points']
                    if tag_name in ('input', 'output'):
                        assert tags[tag_name]['direction'] == original['direction_reference']
                        assert tags[tag_name]['averaging'] == original['averaging']
                    else:
                        assert tags[tag_name]['components'] == [{'ux':0, 'uy':1}[v] for v in original['components']]
                task, manifest = read_json(paths['task_file']), read_json(paths['input_manifest'])
                assert {k:v for k,v in task.items() if k != 'geometry'} == {k:v for k,v in template_record.items() if k != 'geometry'}
                assert task['geometry'] == dict(geometry_id=geometry.geometry_id, descriptor_sha256=geometry.metadata['descriptor_sha256'])
                assert task['schema_version'] == ('hf-native-project-task-1.1' if case['alias'] == 'gripper_native_fine' else 'hf-native-project-task-1.0')
                assert manifest['status'] == 'success' and manifest['bound_task_sha256'] == data.canonical_hash(task)
                for key, path in paths.items():
                    relative = Path(manifest['outputs'][key])
                    assert not relative.is_absolute() and '..' not in relative.parts
                    assert case_dir / manifest['outputs'][key] == Path(path)
                for key in ('descriptor_path', 'array_path'):
                    relative = Path(manifest['LF_source'][key])
                    assert not relative.is_absolute() and '..' not in relative.parts
                assert digest(case_dir / manifest['LF_source']['descriptor_path']) == source_pin
                assert digest(case_dir / manifest['LF_source']['array_path']) == source_record['arrays']['sha256']
                assert manifest['geometry']['arrays_sha256'] == geometry.metadata['arrays']['sha256']
                assert manifest['analysis_domain']['right_columns'] == expected_columns
                assert manifest['analysis_domain']['actual_right_medium_width_mm'] == (4. if expected_columns else 0.)
                assert manifest['analysis_domain']['status'] == ('derived_right_medium' if expected_columns else 'native_unchanged')
                assert manifest['analysis_domain']['whole_grid_is_LF_native'] is (not bool(expected_columns))
                assert manifest['analysis_domain']['parent_native_subdomain_preserved'] is True
                assert all(manifest['analysis_domain'][key] is False for key in ('resampling_applied', 'new_threshold_or_cleanup_applied', 'LF_optimization_applied'))
                assert manifest['task_template']['file_sha256'] == protocol['bindings'][case['task_template']]
                assert manifest['bound_task_file_sha256'] == digest(paths['task_file'])
                assert manifest['geometry']['descriptor_file_sha256'] == digest(paths['geometry_file'])
                for relative, expected in manifest['preparation_source_sha256'].items():
                    assert digest(repo / relative) == expected
                    assert expected == (record['installed_source_sha256'].get(relative) or protocol['bindings'][relative])
                assert not manifest['geometry_task_model_consistency_evaluated'] and not manifest['independent_reference_associated']
                assert not manifest['mechanical_qualified'] and not manifest['HF5_qualified']
                assert all(manifest[key] is False for key in ('model_created', 'force_evaluated', 'tangent_evaluated', 'solver_executed', 'HP_evaluated', 'evaluation_executed', 'constraints_applied', 'material_assigned', 'geometry_workpiece_compatibility_qualified'))
                assert all(manifest[key] == 0 for key in ('model_constructions', 'force_calls', 'tangent_calls', 'solver_calls', 'HP_calls'))
                complete('verification')
                record['cases'].append(dict(alias=case['alias'], paths=paths, entry=case['entry'],
                    relative_path_base='explicit repo_root with mocked alternate cwd' if case['alias'] == 'inverter_canonical'
                        else 'default actual cwd=repo' if case['alias'] == 'gripper_canonical' else 'explicit CLI --repo',
                    geometry_id=geometry.geometry_id, grid=geometry.grid, mask_exact=True, task_non_geometry_exact=True,
                    task_file_sha256=digest(paths['task_file']), manifest_file_sha256=digest(paths['input_manifest'])))
                verified.append(dict(alias=case['alias'], geometry=geometry, task=task, paths=paths,
                                     native_extent_mm=source_record['grid']['domain_mm']))
        phase = 'negative_instances'
        negatives = output / 'negative_cases'
        source = repo / CASES[1]['source_descriptor']
        template = repo / CASES[1]['task_template']
        source_pin = protocol['bindings'][CASES[1]['source_descriptor']]

        def reject(label, *, width=None, source_arg=source, template_arg=template, pin=source_pin,
                   existing=False, fractional=False):
            begin('negative_instances')
            destination = negatives / label
            if existing:
                destination.mkdir(parents=True)
                (destination / 'sentinel.txt').write_bytes(b'KEEP EXACT\n')
            before_loads = counts['npz_load_started']

            def stub_converter(_source, target, **_kwargs):
                target.mkdir(parents=True, exist_ok=False)
                native = dict(schema_version='hf-geometry-1.0', geometry_id='ordinary-mock', descriptor_sha256='ordinary-mock',
                    grid=dict(cell_size_mm=[1., 1.], shape_yx=[40, 80], extent_mm=[80., 40.]), arrays=dict(sha256='not-read'),
                    provenance=dict(lf_v2=dict(schema='dmftd.hf_export.v2', design_id='ordinary-mock', geometry_id='ordinary-mock',
                        descriptor_sha256=source_pin, array_file_sha256='not-read', descriptor_path='sources/design.json', array_path='sources/design.npz')))
                path = target / 'geometry.json'
                write_json(path, native)
                return path

            with patch.object(lf_v2, 'convert_lf_v2', side_effect=stub_converter if fractional else AssertionError('converter must not run')) as converter, \
                 patch.object(np, 'load', side_effect=AssertionError('negative cases must not decode arrays')):
                try:
                    prepare(source_arg, template_arg, destination, repo_root=repo,
                            right_medium_width_mm=width, expected_descriptor_sha256=pin)
                except (ValueError, FileExistsError) as error:
                    assert converter.call_count == (1 if fractional else 0)
                    assert counts['npz_load_started'] == before_loads
                    if existing:
                        assert (destination / 'sentinel.txt').read_bytes() == b'KEEP EXACT\n'
                        assert sorted(p.name for p in destination.iterdir()) == ['sentinel.txt']
                    elif fractional:
                        failed = read_json(destination / 'input_manifest.json')
                        assert failed['status'] == 'not_pass' and failed['partial_artifacts_retained']
                        assert (destination / 'native_geometry/geometry.json').is_file()
                        assert not list(destination.rglob('*.npz'))
                    else:
                        assert not destination.exists()
                    record['negative_instances'].append(dict(label=label, exception_class=type(error).__name__,
                        reason=str(error), converter_calls=converter.call_count, array_decodes=0, partial_retained=fractional or existing))
                else:
                    raise AssertionError('negative case unexpectedly accepted: ' + label)
            complete('negative_instances')

        for label, width in [('width_bool', True), ('width_nan', float('nan')), ('width_infinity', float('inf')), ('width_negative', -1.)]:
            reject(label, width=width)
        reject('width_fractional', width=.25, fractional=True)
        reject('existing_output', existing=True)
        reject('family_mismatch', template_arg=repo / CASES[0]['task_template'])
        reject('descriptor_pin_mismatch', pin='0' * 64)
        invalid_template = output / 'invalid_task_template.json'
        invalid = read_json(template)
        invalid['schema_version'] = 'unsupported-native-task'
        write_json(invalid_template, invalid)
        reject('invalid_task_schema', template_arg=invalid_template)
        assert all(counts[name + '_started'] == counts[name + '_completed'] == value for name, value in EXPECTED.items() if name != 'plot')
        record['observed_distinct_decoded_NPZ'] = len({event['path'] for event in record['npz_load_events']})
        phase = 'plot'
        begin('plot')
        draw_prepared(verified, output, checkpoint)
        complete('plot')
        bindings()
        for target, expected in record['installed_source_sha256'].items():
            assert digest(repo / target) == expected
        seal()
        record.update(status='pass', error=None, bindings_unchanged=True)
    except Exception as error:
        record.update(status='not_pass', error=dict(phase=phase, exception_class=type(error).__name__, reason=str(error)),
                      actual_partial_retained=True, retry_attempted=False, rollback_attempted=False)
        if output.exists():
            try:
                seal()
            except Exception as sealing_error:
                record['output_identity_seal'] = 'incomplete_no_late_seal'
                record['seal_error'] = dict(exception_class=type(sealing_error).__name__, reason=str(sealing_error))
    record.update(execution_closed=True, helper_wall_seconds=time.monotonic() - started)
    if output.exists():
        write_json(output / 'execution_receipt.json', record)
    try:
        checkpoint()
    except Exception as error:
        final_error = dict(phase='final_checkpoint', exception_class=type(error).__name__, reason=str(error))
        if record['status'] == 'pass':
            record.update(status='not_pass', error=final_error)
        else:
            record['final_checkpoint_error'] = final_error
        if output.exists():
            write_json(output / 'execution_receipt.json', record)
    print(json.dumps(dict(card='L-PREP1', status=record['status'], receipt=str(output / 'execution_receipt.json'))))
    return 0 if record['status'] == 'pass' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    return execute(args.repo.resolve(), args.protocol.resolve())


if __name__ == '__main__':
    raise SystemExit(main())
