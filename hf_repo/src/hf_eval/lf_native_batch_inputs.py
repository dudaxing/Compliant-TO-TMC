"""Prepare native batch inputs from ordinary LF sources, without evaluation."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from . import lf_native_inputs, native_batch

prepare_native_lf_inputs = lf_native_inputs.prepare_native_lf_inputs
_preflight = native_batch._preflight

SOURCE_MANIFEST_SCHEMA = 'hf-native-lf-source-manifest-1.0'
INDEX_SCHEMA = 'hf-native-lf-batch-inputs-index-1.0'


def _path(value, root):
    path = Path(value)
    return (path if path.is_absolute() else root / path).resolve()


def _artifact(path, root, digest=None):
    path = Path(path).resolve()
    relative = path.is_relative_to(root)
    record = dict(path=path.relative_to(root).as_posix() if relative else path.as_posix(),
                  path_scope='repo_relative' if relative else 'absolute')
    if digest is not None:
        record['sha256'] = digest
    return record


def _read(path):
    raw = path.read_bytes()
    return json.loads(raw), sha256(raw).hexdigest()


def _write(path, record):
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


def prepare_native_lf_batch_inputs(source_manifest_path, output_directory, *, repo_root=None):
    """Prepare each source once, then preflight one existing native batch manifest.

    All input paths are based on explicit repo_root (or caller cwd), never on the
    source-manifest directory. Sources must share their complete native grid and
    physical region declarations; no resampling is performed. Only geometry
    identities in the task are rebound.
    The future evaluation directories are declarations and are not created here.
    An error retains prepared cases and index.json, stops, and raises unchanged.
    """
    root = Path(repo_root or Path.cwd()).resolve()
    output = Path(output_directory)
    output = output if output.is_absolute() else root / output
    if output.exists() or output.is_symlink():
        raise FileExistsError(f'Choose a new batch-input directory: {output}')
    output = output.resolve()
    manifest_file = _path(source_manifest_path, root)
    manifest, manifest_pin = _read(manifest_file)
    allowed = {'schema_version', 'task_template', 'right_medium_width_mm', 'options', 'cases'}
    if (not isinstance(manifest, dict) or manifest.get('schema_version') != SOURCE_MANIFEST_SCHEMA
            or manifest.keys() - allowed):
        raise ValueError(f'Expected {SOURCE_MANIFEST_SCHEMA}')
    cases = manifest['cases']
    if not isinstance(cases, list) or not cases:
        raise ValueError('Declare at least one source case')
    labels = []
    for case in cases:
        if (not isinstance(case, dict) or set(case) - {'label', 'source_descriptor', 'expected_descriptor_sha256'}
                or not {'label', 'source_descriptor'} <= case.keys()):
            raise ValueError('Every source case needs label and source_descriptor')
        label = case['label']
        if not isinstance(label, str) or not label.strip() or label in labels:
            raise ValueError('Source case labels must be nonempty and unique')
        labels.append(label)
    template_file = _path(manifest['task_template'], root)
    template, template_pin = _read(template_file)
    task = native_batch._validate_task(template)[0]
    options = deepcopy(manifest.get('options', {}))
    normalized_options = native_batch._options(options)
    native_batch._requested_targets(task, normalized_options)
    width = manifest.get('right_medium_width_mm')
    lf_native_inputs._validate_width(width)
    plans, common_declaration = [], None
    for number, case in enumerate(cases):
        source_file = _path(case['source_descriptor'], root)
        source, source_pin = _read(source_file)
        expected = case.get('expected_descriptor_sha256')
        if expected is not None and source_pin != expected:
            raise ValueError('LF source descriptor SHA256 mismatch: ' + case['label'])
        if (not isinstance(source, dict) or source.get('schema') != 'dmftd.hf_export.v2'
                or source.get('case') != task['case_family']):
            raise ValueError('LF source schema/case family differs from the task')
        declaration = dict(case_family=source['case'], grid=source['grid'], regions_mm=source['regions_mm'])
        declaration_pin = native_batch._json_hash(declaration)
        if common_declaration is not None and declaration_pin != common_declaration:
            raise ValueError('Source cases must share the complete native grid and physical declarations')
        common_declaration = declaration_pin
        lf_native_inputs._padding_columns(width, source['grid']['cell_mm'][0])
        plans.append(dict(label=case['label'], source=source_file, source_sha256=source_pin,
                          source_record=source, prepared=output / 'prepared' / f'{number:03d}',
                          future=output / 'evaluations' / f'{number:03d}'))

    index_file = output / 'index.json'
    batch_file = output / 'batch_manifest.json'
    evaluation_directory = output / 'evaluation_index'
    index = dict(schema_version=INDEX_SCHEMA, status='preparing', data_only=True,
        source_manifest=_artifact(manifest_file, root, manifest_pin),
        task_template=_artifact(template_file, root, template_pin), options=deepcopy(options),
        requested_right_medium_width_mm=width,
        path_base=dict(path=root.as_posix(), source='explicit_repo' if repo_root is not None else 'caller_cwd'),
        future_evaluation_directory=_artifact(evaluation_directory, root),
        preparation_source_sha256={
            'hf_repo/src/hf_eval/lf_native_batch_inputs.py': sha256(Path(__file__).read_bytes()).hexdigest(),
            'hf_repo/src/hf_eval/lf_native_inputs.py': sha256(Path(lf_native_inputs.__file__).read_bytes()).hexdigest(),
            'hf_repo/src/hf_eval/native_batch.py': sha256(Path(native_batch.__file__).read_bytes()).hexdigest()},
        evaluation_executed=False, mechanical_qualified=False, independent_HP_qualified=False, HF5_qualified=False,
        qualification_scope='Input preparation and declared batch compatibility only; no mechanics or inherited qualifications',
        cases=[dict(label=plan['label'], status='not_run',
                    source_descriptor=_artifact(plan['source'], root, plan['source_sha256']),
                    source_LF_identity={key: plan['source_record'].get(key) for key in ('schema', 'design_id', 'geometry_id')},
                    prepared_directory=_artifact(plan['prepared'], root),
                    future_output=_artifact(plan['future'], root)) for plan in plans])
    output.mkdir(parents=True, exist_ok=False)
    current, stage = None, 'initial_index'
    try:
        _write(index_file, index)
        batch_cases, full_grid = [], None
        for plan, row in zip(plans, index['cases']):
            current, stage = row, 'prepare'
            row['status'] = 'preparing'
            _write(index_file, index)
            prepared = prepare_native_lf_inputs(plan['source'], template_file, plan['prepared'],
                repo_root=root, right_medium_width_mm=width,
                expected_descriptor_sha256=plan['source_sha256'])
            stage = 'prepared_metadata'
            geometry_file, task_file, input_file = [Path(prepared[key]).resolve()
                for key in ('geometry_file', 'task_file', 'input_manifest')]
            geometry, geometry_pin = _read(geometry_file)
            bound_task, task_pin = _read(task_file)
            preparation, input_pin = _read(input_file)
            grid_pin = native_batch._json_hash(geometry['grid'])
            if full_grid is not None and grid_pin != full_grid:
                raise ValueError('Prepared cases must share their complete analysis grid')
            full_grid = grid_pin
            if (native_batch._json_hash({k: v for k, v in bound_task.items() if k != 'geometry'})
                    != native_batch._json_hash({k: v for k, v in template.items() if k != 'geometry'})):
                raise ValueError('Prepared task changed outside its geometry binding')
            if preparation['status'] != 'success':
                raise ValueError('Single-case input preparation did not succeed')
            row.update(status='success', geometry=_artifact(geometry_file, root, geometry_pin),
                task=_artifact(task_file, root, task_pin), input_manifest=_artifact(input_file, root, input_pin),
                LF_source=deepcopy(preparation.get('LF_source', {})),
                native_geometry=deepcopy(preparation.get('native_geometry', {})),
                geometry_identity=deepcopy(preparation.get('geometry', {})),
                preparation_source_sha256=deepcopy(preparation.get('preparation_source_sha256', {})))
            batch_cases.append(dict(label=plan['label'], geometry=row['geometry']['path'],
                                    task=row['task']['path'], output=row['future_output']['path']))
            _write(index_file, index)
        current, stage = None, 'batch_preflight'
        batch = dict(schema_version=native_batch.MANIFEST_SCHEMA, cases=batch_cases, options=deepcopy(options))
        _preflight(batch, root, evaluation_directory)
        stage = 'ready_manifest'
        with batch_file.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(batch, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        index.update(status='prepared', batch_manifest=_artifact(batch_file, root, sha256(batch_file.read_bytes()).hexdigest()),
                     batch_preflight=dict(status='pass', declarations_only=True, model_created=False),
                     shared_analysis_grid_sha256=full_grid)
        _write(index_file, index)
    except Exception as error:
        failure = dict(stage=stage, exception_class=type(error).__name__,
                       code=getattr(error, 'code', None), reason=str(error))
        if current is not None:
            current.update(status='not_pass', error=deepcopy(failure))
        index.update(status='not_pass', error=failure, partial_artifacts_retained=True)
        try:
            _write(index_file, index)
        except OSError:
            pass  # Preserve the original error and actual partial artifacts.
        raise
    return dict(batch_manifest_file=str(batch_file), index_file=str(index_file),
                evaluation_directory=str(evaluation_directory))
