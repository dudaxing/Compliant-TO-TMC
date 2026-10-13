"""Prepare ordinary LF v2 data and an explicit native task, without mechanics.

The original converter and optional right-domain derivation retain their policies.
Task validation imports existing dependencies lazily; imports may register JAX.
This API does not construct a model or invoke force, tangent, solver or HP kernels.
"""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import math
from pathlib import Path


def _path(value, repo_root):
    path = Path(value)
    return path if path.is_absolute() else Path(repo_root or Path.cwd()) / path


def _validate_width(width):
    if width is None:
        return
    if isinstance(width, bool) or not isinstance(width, (int, float)) or not math.isfinite(width) or width < 0:
        raise ValueError('right_medium_width_mm must be a finite nonnegative int/float or None; bool is not accepted')


def _padding_columns(width, dx):
    _validate_width(width)
    if width is None:
        return 0
    if width == 0:
        return 0
    ratio = Fraction(str(width)) / Fraction(str(dx))
    if ratio.denominator != 1:
        raise ValueError('right_medium_width_mm must equal an integer number of native dx columns; no rounding')
    return ratio.numerator


def _write_manifest(path, record):
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def prepare_native_lf_inputs(source_descriptor, task_template_path, output_directory, *,
                             repo_root=None, right_medium_width_mm=None,
                             expected_descriptor_sha256=None):
    """Return absolute geometry_file/task_file/input_manifest paths for evaluate_native.

    A complete native task1.0/1.1 is required. Only its two geometry identities
    are rebound. No LF load, physics, background constraint or body is inferred.
    A case directory must be new. Errors retain partial artifacts and a failure
    manifest if the directory has been created; no retry or cleanup is attempted.
    Width accepts finite int/float or None, never bool or arbitrary Real objects;
    its exact decimal ratio to native dx uses no snapping or refinement.
    """
    output = _path(output_directory, repo_root)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f'Choose a new input directory: {output}')
    output = output.resolve()
    source = _path(source_descriptor, repo_root).resolve()
    template_file = _path(task_template_path, repo_root).resolve()
    source_raw, template_raw = source.read_bytes(), template_file.read_bytes()
    source_pin, template_pin = sha256(source_raw).hexdigest(), sha256(template_raw).hexdigest()
    if expected_descriptor_sha256 is not None and source_pin != expected_descriptor_sha256:
        raise ValueError('LF source descriptor SHA256 mismatch')
    source_record, template = json.loads(source_raw), json.loads(template_raw)
    from . import data, lf_v2, native_project, project, regions
    task = native_project._validate_task(template)[0]
    if not isinstance(source_record, dict) or source_record.get('case') != task['case_family']:
        raise ValueError('LF source case family and task template must match')
    # Validate the numeric width before creating a directory; column alignment
    # is checked against the converter's actually validated native geometry.
    _validate_width(right_medium_width_mm)
    modules = [data, lf_v2, native_project, project, regions]
    record = dict(schema_version='hf-native-lf-inputs-1.0', status='preparing', phase='convert',
        data_only=True, model_created=False, force_evaluated=False, tangent_evaluated=False,
        solver_executed=False, HP_evaluated=False, evaluation_executed=False,
        model_constructions=0, force_calls=0, tangent_calls=0, solver_calls=0, HP_calls=0,
        mechanical_hooks_monitored=False,
        zero_mechanics_basis='Original LF converter, optional geometry padding and native task validator only; no dynamic mechanics hooks',
        dependency_import_scope='Existing preparation/task validation dependencies may import/register JAX; no claim of zero JAX imports',
        case_family=task['case_family'], LF_source_descriptor_file_sha256=source_pin,
        task_template=dict(file_sha256=template_pin, task_id=task['task_id'], geometry_binding=deepcopy(task['geometry'])),
        task_template_validated=True, geometry_task_model_consistency_evaluated=False,
        geometry_workpiece_compatibility_qualified=False, constraints_applied=False, material_assigned=False,
        task_policy='All template fields preserved except geometry.geometry_id and geometry.descriptor_sha256',
        outputs={}, requested_right_medium_width_mm=right_medium_width_mm)
    output.mkdir(parents=True, exist_ok=False)
    manifest_file = output / 'input_manifest.json'
    try:
        _write_manifest(manifest_file, record)
        native_file = lf_v2.convert_lf_v2(source, output / 'native_geometry', expected_descriptor_sha256=source_pin)
        native = json.loads(native_file.read_bytes())
        native_pin = sha256(native_file.read_bytes()).hexdigest()
        record['outputs']['native_geometry_file'] = native_file.relative_to(output).as_posix()
        record['native_geometry'] = dict(geometry_id=native['geometry_id'], descriptor_sha256=native['descriptor_sha256'],
            descriptor_file_sha256=native_pin, arrays_sha256=native['arrays']['sha256'], grid=deepcopy(native['grid']),
            source_native_grid_preserved=True)
        provenance = native['provenance']['lf_v2']
        record['LF_source'] = dict(schema=provenance['schema'], design_id=provenance['design_id'], geometry_id=provenance['geometry_id'],
            descriptor_file_sha256=provenance['descriptor_sha256'], array_file_sha256=provenance['array_file_sha256'],
            descriptor_path='native_geometry/' + provenance['descriptor_path'], array_path='native_geometry/' + provenance['array_path'])
        record['phase'] = 'padding'
        columns = _padding_columns(right_medium_width_mm, native['grid']['cell_size_mm'][0])
        geometry_file, geometry = native_file, native
        if columns:
            from . import analysis_domain
            modules.append(analysis_domain)
            geometry_file = analysis_domain.write_right_medium_geometry(native_file, output / 'derived_geometry', columns)
            geometry = json.loads(geometry_file.read_bytes())
            actual_margin = geometry['provenance']['hf_analysis_domain_derivations'][-1]['margin_mm']
        else:
            actual_margin = 0.
        record['outputs']['geometry_file'] = geometry_file.relative_to(output).as_posix()
        record['analysis_domain'] = dict(status='derived_right_medium' if columns else 'native_unchanged',
            right_columns=columns, actual_right_medium_width_mm=actual_margin,
            whole_grid_is_LF_native=not bool(columns), parent_native_subdomain_preserved=True,
            resampling_applied=False, new_threshold_or_cleanup_applied=False, LF_optimization_applied=False)
        record['phase'] = 'task_binding'
        task['geometry'] = dict(geometry_id=geometry['geometry_id'], descriptor_sha256=geometry['descriptor_sha256'])
        native_project._validate_task(task)
        if {key:value for key,value in task.items() if key != 'geometry'} != {key:value for key,value in template.items() if key != 'geometry'}:
            raise ValueError('Task template fields changed outside geometry binding')
        task_file = output / 'task.json'
        task_raw = (json.dumps(task, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
        with task_file.open('xb') as stream:
            stream.write(task_raw)
        epoch = {'hf_repo/src/hf_eval/lf_native_inputs.py': sha256(Path(__file__).read_bytes()).hexdigest()}
        epoch.update({'hf_repo/src/hf_eval/' + Path(module.__file__).name: sha256(Path(module.__file__).read_bytes()).hexdigest() for module in modules})
        record.update(status='success', phase='complete',
            geometry=dict(geometry_id=geometry['geometry_id'], descriptor_sha256=geometry['descriptor_sha256'],
                descriptor_file_sha256=sha256(geometry_file.read_bytes()).hexdigest(), arrays_sha256=geometry['arrays']['sha256']),
            bound_task_sha256=data.canonical_hash(task), bound_task_file_sha256=sha256(task_raw).hexdigest(),
            preparation_source_sha256=epoch, preparation_source_epoch_scope='Only actual preparation modules; no inherited HP or mechanical qualification',
            geometry_bound_task_created=True, geometry_task_model_consistency_evaluated=False,
            independent_reference_associated=False, mechanical_qualified=False, HF5_qualified=False)
        record['outputs'].update(geometry_file=geometry_file.relative_to(output).as_posix(),
            task_file=task_file.relative_to(output).as_posix(), input_manifest='input_manifest.json')
        _write_manifest(manifest_file, record)
    except Exception as error:
        record.update(status='not_pass', error=dict(exception_class=type(error).__name__,
            code=getattr(error, 'code', None), reason=str(error)), partial_artifacts_retained=True)
        try:
            _write_manifest(manifest_file, record)
        except OSError:
            pass  # Preserve the original business error and any existing partial files.
        raise
    return dict(geometry_file=str(geometry_file.resolve()), task_file=str(task_file.resolve()),
        input_manifest=str(manifest_file.resolve()))
