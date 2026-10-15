"""Six finite batch-preparation contracts using JSON and mocked preparation.

No test converts LF arrays, constructs a model, or evaluates mechanics. Each
method retains its own new short fixture directory, including failure partials.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO = Path(os.environ.get('HF_BATCH_TEST_REPO', Path(__file__).resolve().parents[2])).resolve()
sys.path.insert(0, str(REPO / 'hf_repo' / 'src'))
from hf_eval import lf_native_batch_inputs as batch_inputs


MOCK_PREPARATION_COUNTS = dict(started=0, returned=0, raised=0)
OPTIONS = dict(response_mode='mechanical', tangent_mode='chunk256', initial_guess='port_projection')
FINE_SOURCE = 'lf_data_preparation/v2_adapter_001/inputs/gripper_native_fine/design.json'
FINE_CASE = 'lf_data_preparation/native_interface_001/lf_input_preparation_001/run_001/cases/gripper_native_fine/'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n',
                    encoding='utf-8', newline='\n')


class ExpectedSecondPreparationError(ValueError):
    code = 'mock_second_preparation_stop'


class NativeLFBatchInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        expected = REPO / 'hf_repo/src/hf_eval/lf_native_batch_inputs.py'
        if Path(batch_inputs.__file__).resolve() != expected.resolve():
            raise AssertionError('Tests must import the new module from the explicit repository')
        cls.source_fixture = read_json(REPO / FINE_SOURCE)
        cls.task_fixture = read_json(REPO / (FINE_CASE + 'task.json'))
        cls.geometry_fixture = read_json(REPO / (FINE_CASE + 'derived_geometry/geometry.json'))

    def setUp(self):
        short_root = Path(os.environ.get(
            'L_BPREP_TEST_ROOT', str(Path(tempfile.gettempdir()) / 'hf-lbp-tests'))).resolve()
        short_root.mkdir(parents=True, exist_ok=True)
        self.directory = short_root / self._testMethodName.split('_')[1]
        self.directory.mkdir(exist_ok=False)
        self.repo = self.directory / 'r'
        self.repo.mkdir()
        self.template = deepcopy(self.task_fixture)
        save_json(self.repo / 't.json', self.template)
        self.manifest_file = self.repo / 'l/m.json'
        self.prepare_calls = []
        self.fail_on = None
        self.failure = None

    def manifest(self, labels=('first', 'second')):
        cases = []
        for number, label in enumerate(labels):
            source = deepcopy(self.source_fixture)
            source['design_id'] = 'mock-source-' + str(number)
            path = self.repo / 's' / str(number) / 'design.json'
            save_json(path, source)
            cases.append(dict(label=label, source_descriptor=path.relative_to(self.repo).as_posix(),
                              expected_descriptor_sha256=sha256(path.read_bytes()).hexdigest()))
        return dict(schema_version='hf-native-lf-source-manifest-1.0', task_template='t.json',
                    right_medium_width_mm=4., options=deepcopy(OPTIONS), cases=cases)

    def call(self, manifest, output='p'):
        save_json(self.manifest_file, manifest)
        return batch_inputs.prepare_native_lf_batch_inputs(
            self.manifest_file.relative_to(self.repo), output, repo_root=self.repo)

    def artifact_path(self, record):
        self.assertEqual(record['path_scope'], 'repo_relative')
        path = (self.repo / record['path']).resolve()
        self.assertTrue(path.is_relative_to(self.repo))
        return path

    def mock_prepare(self, source_descriptor, task_template_path, output_directory, **options):
        """Write only three ordinary JSON outputs; never create/read a NPZ."""
        number = len(self.prepare_calls)
        output = Path(output_directory).resolve()
        self.prepare_calls.append(dict(source=Path(source_descriptor).resolve(),
            template=Path(task_template_path).resolve(), output=output, options=deepcopy(options)))
        MOCK_PREPARATION_COUNTS['started'] += 1
        output.mkdir(parents=True, exist_ok=False)
        if number == self.fail_on:
            save_json(output / 'partial.json', dict(scope='mock preparation partial; no arrays', status='not_pass'))
            MOCK_PREPARATION_COUNTS['raised'] += 1
            raise self.failure
        geometry = deepcopy(self.geometry_fixture)
        geometry['geometry_id'] = format(number + 1, '064x')
        geometry['descriptor_sha256'] = format(number + 17, '064x')
        task = deepcopy(self.template)
        task['geometry'] = {key: geometry[key] for key in ('geometry_id', 'descriptor_sha256')}
        source = read_json(source_descriptor)
        preparation = dict(status='success', data_only=True,
            fixture_scope='Mock ordinary metadata; no LF conversion or scientific array',
            LF_source=dict(schema=source['schema'], design_id=source['design_id'],
                           geometry_id=source['geometry_id']),
            native_geometry=dict(grid=deepcopy(source['grid'])),
            geometry={key: geometry[key] for key in ('geometry_id', 'descriptor_sha256')},
            preparation_source_sha256={})
        paths = dict(geometry_file=output / 'geometry.json', task_file=output / 'task.json',
                     input_manifest=output / 'input_manifest.json')
        for key, value in (('geometry_file', geometry), ('task_file', task), ('input_manifest', preparation)):
            save_json(paths[key], value)
        MOCK_PREPARATION_COUNTS['returned'] += 1
        return {key: str(path) for key, path in paths.items()}

    def test_01_invalid_manifest_and_empty_or_duplicate_labels_reject_before_prepare(self):
        original = self.manifest()
        invalid = []
        wrong_schema = deepcopy(original)
        wrong_schema['schema_version'] = 'not-the-LF-source-schema'
        invalid.append(wrong_schema)
        empty = deepcopy(original)
        empty['cases'] = []
        invalid.append(empty)
        blank = deepcopy(original)
        blank['cases'][0]['label'] = ' '
        invalid.append(blank)
        duplicate = deepcopy(original)
        duplicate['cases'][1]['label'] = duplicate['cases'][0]['label']
        invalid.append(duplicate)
        with patch.object(batch_inputs, 'prepare_native_lf_inputs', side_effect=self.mock_prepare) as prepare:
            for number, manifest in enumerate(invalid):
                with self.subTest(invalid=number):
                    with self.assertRaises(ValueError):
                        self.call(manifest, 'bad' + str(number))
                    prepare.assert_not_called()

    def test_02_later_source_pin_mismatch_rejects_before_first_prepare(self):
        manifest = self.manifest()
        manifest['cases'][1]['expected_descriptor_sha256'] = '0' * 64
        with patch.object(batch_inputs, 'prepare_native_lf_inputs', side_effect=self.mock_prepare) as prepare:
            with self.assertRaises(ValueError):
                self.call(manifest)
            prepare.assert_not_called()
        self.assertFalse((self.repo / 'p/batch_manifest.json').exists())

    def test_03_existing_output_preserves_sentinel(self):
        manifest = self.manifest()
        output = self.repo / 'p'
        output.mkdir()
        sentinel = output / 'sentinel.txt'
        original = b'existing output must remain unchanged\n'
        sentinel.write_bytes(original)
        with patch.object(batch_inputs, 'prepare_native_lf_inputs', side_effect=self.mock_prepare) as prepare:
            with self.assertRaises(FileExistsError):
                self.call(manifest)
            prepare.assert_not_called()
        self.assertEqual(sentinel.read_bytes(), original)
        self.assertEqual([path.name for path in output.iterdir()], ['sentinel.txt'])

    def test_04_success_preserves_shared_task_options_and_explicit_repo_paths(self):
        manifest = self.manifest(labels=('first/../logical', 'second:logical'))
        outside = self.directory / 'cwd'
        outside.mkdir()
        original_cwd = Path.cwd()
        try:
            os.chdir(outside)
            with patch.object(batch_inputs, 'prepare_native_lf_inputs', side_effect=self.mock_prepare) as prepare:
                with patch.object(batch_inputs, '_preflight', wraps=batch_inputs._preflight) as preflight:
                    returned = self.call(manifest)
                    prepare.assert_called()
                    self.assertEqual(prepare.call_count, 2)
                    preflight.assert_called_once()
        finally:
            os.chdir(original_cwd)
        self.assertEqual(set(returned), {'batch_manifest_file', 'index_file', 'evaluation_directory'})
        self.assertTrue(all(Path(path).is_absolute() for path in returned.values()))
        batch = read_json(returned['batch_manifest_file'])
        index = read_json(returned['index_file'])
        self.assertEqual(batch['schema_version'], 'hf-native-batch-manifest-1.0')
        self.assertEqual(index['schema_version'], 'hf-native-lf-batch-inputs-index-1.0')
        self.assertEqual(index['status'], 'prepared')
        self.assertEqual(batch['options'], manifest['options'])
        self.assertEqual(index['options'], manifest['options'])
        self.assertEqual([row['label'] for row in batch['cases']], [case['label'] for case in manifest['cases']])
        self.assertEqual([row['status'] for row in index['cases']], ['success', 'success'])
        self.assertEqual(self.artifact_path(index['future_evaluation_directory']), Path(returned['evaluation_directory']))
        self.assertFalse(Path(returned['evaluation_directory']).exists())
        self.assertTrue(index['data_only'])
        self.assertTrue(all(index[key] is False for key in (
            'evaluation_executed', 'mechanical_qualified', 'independent_HP_qualified', 'HF5_qualified')))
        for case, row, actual, declared in zip(manifest['cases'], index['cases'], self.prepare_calls, batch['cases']):
            self.assertEqual(actual['source'], (self.repo / case['source_descriptor']).resolve())
            self.assertEqual(actual['template'], self.repo / 't.json')
            self.assertEqual(actual['options']['repo_root'], self.repo)
            self.assertEqual(actual['options']['right_medium_width_mm'], 4.)
            self.assertEqual(actual['options']['expected_descriptor_sha256'], case['expected_descriptor_sha256'])
            prepared_directory = self.artifact_path(row['prepared_directory'])
            self.assertTrue(prepared_directory.name.isdecimal())
            self.assertEqual(actual['output'], prepared_directory)
            for key in ('geometry', 'task'):
                path = self.artifact_path(row[key])
                self.assertEqual((self.repo / declared[key]).resolve(), path)
                self.assertTrue(path.is_relative_to(prepared_directory))
                self.assertEqual(sha256(path.read_bytes()).hexdigest(), row[key]['sha256'])
            self.assertEqual((self.repo / declared['output']).resolve(), self.artifact_path(row['future_output']))
            self.assertFalse(self.artifact_path(row['future_output']).exists())
            task = read_json(self.artifact_path(row['task']))
            geometry = read_json(self.artifact_path(row['geometry']))
            self.assertEqual({key: value for key, value in task.items() if key != 'geometry'},
                             {key: value for key, value in self.template.items() if key != 'geometry'})
            self.assertEqual(task['geometry'], {key: geometry[key] for key in ('geometry_id', 'descriptor_sha256')})

    def test_05_second_prepare_error_retains_first_partial_and_unrun_third(self):
        manifest = self.manifest(labels=('first', 'second', 'third'))
        self.fail_on = 1
        self.failure = ExpectedSecondPreparationError('Deliberate second mocked preparation stop')
        with patch.object(batch_inputs, 'prepare_native_lf_inputs', side_effect=self.mock_prepare) as prepare:
            with self.assertRaises(ExpectedSecondPreparationError) as caught:
                self.call(manifest)
            self.assertIs(caught.exception, self.failure)
            self.assertEqual(prepare.call_count, 2)
        index = read_json(self.repo / 'p/index.json')
        self.assertEqual(index['status'], 'not_pass')
        self.assertTrue(index['partial_artifacts_retained'])
        self.assertEqual([row['status'] for row in index['cases']], ['success', 'not_pass', 'not_run'])
        self.assertTrue(self.artifact_path(index['cases'][0]['geometry']).is_file())
        self.assertEqual(read_json(self.prepare_calls[1]['output'] / 'partial.json')['status'], 'not_pass')
        error = index['cases'][1]['error']
        self.assertEqual(error['stage'], 'prepare')
        self.assertEqual(error['exception_class'], 'ExpectedSecondPreparationError')
        self.assertEqual(error['code'], self.failure.code)
        self.assertEqual(error['reason'], str(self.failure))
        self.assertFalse(self.artifact_path(index['cases'][2]['prepared_directory']).exists())
        self.assertFalse((self.repo / 'p/batch_manifest.json').exists())

    def test_06_mixed_complete_native_grid_rejects_without_ready_manifest(self):
        manifest = self.manifest()
        second = self.repo / manifest['cases'][1]['source_descriptor']
        source = read_json(second)
        source['grid'].update(native_mesh=[80, 40], analysis_mesh=[80, 40], cell_mm=[1., 1.])
        save_json(second, source)
        manifest['cases'][1]['expected_descriptor_sha256'] = sha256(second.read_bytes()).hexdigest()
        with patch.object(batch_inputs, 'prepare_native_lf_inputs', side_effect=self.mock_prepare) as prepare:
            with self.assertRaises(ValueError):
                self.call(manifest)
            prepare.assert_not_called()
        self.assertFalse((self.repo / 'p/batch_manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
