"""Mocked call integration and CLI transport; never a new forward qualification."""
from copy import deepcopy
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

from hf_eval import native_evaluate, native_mean, native_project


REPO = Path(os.environ.get('HF_INTERFACE_TEST_REPO', Path(__file__).resolve().parents[2])).resolve()
FULL = 'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/run_001/result/result.json'
PARTIAL = 'lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/run_001/result/result.json'
MOCK_TRANSPORT_COUNTS = Counter(solve=0, cached_write=0)


@pytest.fixture
def cached_only(monkeypatch):
    original = Path.open

    def json_or_source_only(self, *args, **kwargs):
        assert self.suffix.lower() != '.npz', 'The thin interface must not open arrays'
        return original(self, *args, **kwargs)

    def no_science(*args, **kwargs):
        pytest.fail('The mocked interface test called real model/solver/persistence code')

    monkeypatch.setattr(Path, 'open', json_or_source_only)
    monkeypatch.setattr(native_project, 'build_native_project', no_science)
    monkeypatch.setattr(native_mean, 'build_native_project', no_science)
    monkeypatch.setattr(native_mean, 'solve_native_mean', no_science)
    monkeypatch.setattr(native_mean, 'write_native_mean', no_science)


def transport_inputs(tmp_path):
    base = tmp_path / 'input_repo'
    (base / 'tasks').mkdir(parents=True)
    task = json.loads((REPO / Path(FULL).parent / 'model/model.json').read_text(encoding='utf-8'))['task']
    (base / 'tasks/task.json').write_text(json.dumps(task), encoding='utf-8')
    (base / 'geometry.json').write_text('{}', encoding='utf-8')
    elsewhere = tmp_path / 'unrelated_cwd'
    elsewhere.mkdir()
    return base, elsewhere, task


def replace_forward(monkeypatch, saved_file):
    calls = []
    opaque_result = object()

    def solve(geometry, task, targets, **options):
        MOCK_TRANSPORT_COUNTS['solve'] += 1
        calls.append(('solve', geometry, deepcopy(task), list(targets), options))
        return opaque_result

    def cached_write(result, output):
        MOCK_TRANSPORT_COUNTS['cached_write'] += 1
        assert result is opaque_result
        calls.append(('write', output))
        return REPO / saved_file

    monkeypatch.setattr(native_evaluate, 'solve_native_mean', solve)
    monkeypatch.setattr(native_evaluate, 'write_native_mean', cached_write)
    return calls


@pytest.mark.parametrize('explicit', [False, True])
def test_once_forward_with_repo_paths_and_explicit_options(tmp_path, monkeypatch, cached_only, explicit):
    base, elsewhere, task = transport_inputs(tmp_path)
    monkeypatch.chdir(elsewhere)
    calls = replace_forward(monkeypatch, FULL)
    options = dict(initial_guess='port_projection', response_mode='mechanical', tangent_mode='chunk256',
                   minimum_increment=.01, time_limit_seconds=30.) if explicit else {}
    response = native_evaluate.evaluate_native('geometry.json', 'tasks/task.json', 'new_run',
                                               repo_root=base, **options)
    assert [call[0] for call in calls] == ['solve', 'write']
    _, geometry, passed_task, targets, passed = calls[0]
    assert geometry == (base / 'geometry.json').resolve()
    assert passed_task == task and targets == task['path']['targets_mm']
    assert calls[1][1] == (base / 'new_run').resolve()
    assert passed['initial_guess'] == ('port_projection' if explicit else 'tangent')
    assert passed['response_mode'] == ('mechanical' if explicit else 'complete')
    assert passed['tangent_mode'] == ('chunk256' if explicit else 'full')
    assert passed['settings'].time_limit_seconds == (30. if explicit else 180.)
    assert passed['settings'].minimum_increment == (.01 if explicit else .25 / 16)
    assert response['status'] == 'success'
    assert response['independent_reference']['full_path_reference_pass'] is False
    assert response['invocation']['task_file'] == str((base / 'tasks/task.json').resolve())
    persisted = json.loads((base / 'new_run/response.json').read_text(encoding='utf-8'))
    assert persisted == response


class TaggedFailure(ValueError):
    def __init__(self, stage):
        self.code = 'original_interface_test_code'
        super().__init__('original reason from ' + stage)


@pytest.mark.parametrize('stage', ['input', 'existing_output', 'solve', 'persistence', 'summary'])
def test_failure_keeps_original_phase_code_class_and_stops_downstream(tmp_path, monkeypatch, cached_only, stage):
    base, _, _ = transport_inputs(tmp_path)
    calls = replace_forward(monkeypatch, FULL)
    if stage == 'existing_output':
        (base / 'error_run').mkdir()
        sentinel = base / 'error_run/keep.txt'
        sentinel.write_text('existing output must remain intact', encoding='utf-8')
        before = sentinel.read_bytes()
        expected = dict(code=None, exception_class='FileExistsError')
    elif stage == 'input':
        (base / 'tasks/task.json').write_text('{broken', encoding='utf-8')
        with pytest.raises(json.JSONDecodeError) as original:
            json.loads('{broken')
        expected = dict(code=None, exception_class='JSONDecodeError', reason=str(original.value))
    else:
        expected = dict(code='original_interface_test_code', exception_class='TaggedFailure',
                        reason='original reason from ' + stage)

        def fail(*args, **kwargs):
            if stage == 'solve':
                MOCK_TRANSPORT_COUNTS['solve'] += 1
            elif stage == 'persistence':
                MOCK_TRANSPORT_COUNTS['cached_write'] += 1
            raise TaggedFailure(stage)

        name = {'solve':'solve_native_mean', 'persistence':'write_native_mean',
                'summary':'summarize_saved_native_result'}[stage]
        monkeypatch.setattr(native_evaluate, name, fail)
    response = native_evaluate.evaluate_native('geometry.json', 'tasks/task.json', 'error_run', repo_root=base)
    assert response['status'] == 'error' and response['target_response'] is None
    if stage == 'existing_output':
        assert response['failure']['stage'] == 'input'
        assert response['failure']['code'] == expected['code']
        assert response['failure']['exception_class'] == expected['exception_class']
        assert str((base / 'error_run').resolve()) in response['failure']['reason']
        assert sentinel.read_bytes() == before
        assert not (base / 'error_run/response.json').exists()
    else:
        assert response['failure'] == dict(stage=stage, **expected)
    assert [call[0] for call in calls] == {'input':[], 'existing_output':[], 'solve':[], 'persistence':['solve'], 'summary':['solve','write']}[stage]
    assert response['result_file'] == (str(REPO / FULL) if stage == 'summary' else None)
    if stage != 'existing_output':
        assert json.loads((base / 'error_run/response.json').read_text(encoding='utf-8')) == response


@pytest.mark.parametrize('saved_file, initial_guess, expected_exit', [(FULL,'tangent',0), (PARTIAL,'port_projection',1)])
def test_cli_from_unrelated_cwd_preserves_partial_status_and_paths(tmp_path, monkeypatch, capsys, cached_only,
                                                                 saved_file, initial_guess, expected_exit):
    base, elsewhere, task = transport_inputs(tmp_path)
    monkeypatch.chdir(elsewhere)
    calls = replace_forward(monkeypatch, saved_file)
    script = REPO / 'hf_repo/scripts/evaluate_native.py'
    spec = importlib.util.spec_from_file_location('native_evaluate_cli_for_test', script)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    argv = [str(script), '--repo', str(base), '--geometry', 'geometry.json', '--task', 'tasks/task.json',
            '--output', 'cli_run', '--time-limit', '30', '--minimum-increment', '.01',
            '--response-mode', 'mechanical', '--tangent-mode', 'chunk256']
    if initial_guess != 'tangent':
        argv += ['--initial-guess', initial_guess]
    monkeypatch.setattr(sys, 'argv', argv)
    assert cli.main() == expected_exit
    response = json.loads(capsys.readouterr().out)
    assert [call[0] for call in calls] == ['solve','write']
    assert calls[0][1] == (base / 'geometry.json').resolve()
    assert calls[0][2] == task and calls[0][3] == task['path']['targets_mm']
    assert calls[0][4]['initial_guess'] == initial_guess
    assert calls[1][1] == (base / 'cli_run').resolve()
    assert response['invocation']['initial_guess'] == initial_guess
    assert response['status'] == ('success' if expected_exit == 0 else 'failed')
    assert response['independent_reference']['full_path_reference_pass'] is False
    if expected_exit:
        assert response['target_response'] is None and response['failure']['code'] == 'invalid_J'
        assert response['last_accepted']['d_mm'] == .86875
    assert json.loads((base / 'cli_run/response.json').read_text(encoding='utf-8')) == response
