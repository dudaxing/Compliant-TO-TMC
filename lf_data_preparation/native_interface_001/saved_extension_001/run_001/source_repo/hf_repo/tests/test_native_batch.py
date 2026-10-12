"""Batch contract tests using only temporary JSON and mocked single-case transport."""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

from hf_eval import native_batch

REPO = Path(os.environ.get('HF_BATCH_TEST_REPO', Path(__file__).resolve().parents[2])).resolve()
MOCK_TRANSPORT_COUNTS = Counter(evaluate_started=0, evaluate_returned=0, evaluate_escaped=0)


class TaggedTransportError(ValueError):
    code = 'original_transport_code'


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


@pytest.fixture
def inputs(tmp_path):
    repo = tmp_path/'inputs'
    repo.mkdir()
    geometry = json.loads((REPO/'lf_data_preparation/v2_adapter_001/converted/gripper_canonical/geometry.json').read_text(encoding='utf-8'))
    task = json.loads((REPO/'lf_data_preparation/native_mean_001/task.json').read_text(encoding='utf-8'))
    task.update(schema_version='hf-native-project-task-1.1',
                purpose='mock_batch_transport_test', description='Mock transport only; no scientific qualification',
                path={'kind':'ordered_cycle', 'targets_mm':[0., .5, 1.2, 0.]})
    task['input']['target_mm'] = 1.2
    cases = []
    for label in ('first', 'second'):
        actual = deepcopy(task)
        actual['task_id'] = 'mock_'+label
        save_json(repo/'geometry'/f'{label}.json', geometry)
        save_json(repo/'tasks'/f'{label}.json', actual)
        cases.append(dict(label=label, geometry=f'geometry/{label}.json', task=f'tasks/{label}.json', output=f'runs/{label}'))
    manifest = dict(schema_version='hf-native-batch-manifest-1.0', cases=cases, options={})
    save_json(repo/'manifest.json', manifest)
    return repo, manifest


def response(label, *, status='success', reference=False):
    peak = dict(index=2, d_mm=1.2, R_input_N=.2, workpiece=None, state_sha256=label+'_peak')
    endpoint = dict(index=3, d_mm=0., R_input_N=0., workpiece=None, state_sha256=label+'_return')
    if status == 'failed':
        endpoint = dict(index=1, d_mm=.86875, R_input_N=.1, workpiece=None, state_sha256=label+'_partial')
    return dict(schema_version='hf-native-response-1.0', status=status,
        identity={'result':{'path':f'own/{label}/result.json', 'sha256':label+'_result'}},
        path={'task_target_mm':1.2, 'requested_endpoint_mm':0., 'accepted_states':4 if status=='success' else 2,
              'completed':status=='success', 'task_target_executed':status=='success'},
        target_response=peak if status=='success' else None,
        requested_endpoint_response=endpoint if status=='success' else None,
        maximum_loading_stroke=peak if status=='success' else endpoint, last_accepted=endpoint,
        failure=None if status=='success' else {'phase':'equilibrium', 'code':'invalid_J', 'reason':'saved mock failure'},
        independent_reference={'status':'matched' if reference else 'not_provided', 'report':{'path':label+'_ref.json'} if reference else None,
            'accepted_reference_pass':reference, 'full_path_reference_pass':reference, 'HF5_qualified':False},
        views={'status':'matched' if reference else 'not_provided', 'links':[{'path':label+'_own.gif'}] if reference else []},
        producer_flags={'independent_HP_qualified':False, 'equilibrium_qualified':False, 'HF_qualified':False})


def transport(monkeypatch, replies, after_return=None):
    calls = []
    iterator = iter(replies)

    def evaluate(geometry, task, output, **options):
        MOCK_TRANSPORT_COUNTS['evaluate_started'] += 1
        calls.append((Path(geometry), Path(task), Path(output), dict(options)))
        answer = next(iterator)
        if isinstance(answer, BaseException):
            MOCK_TRANSPORT_COUNTS['evaluate_escaped'] += 1
            raise answer
        output = Path(output)
        if not output.is_absolute():
            output = Path(options.get('repo_root') or Path.cwd())/output
        save_json(output/'response.json', answer)
        MOCK_TRANSPORT_COUNTS['evaluate_returned'] += 1
        if after_return is not None:
            after_return(len(calls))
        return deepcopy(answer)

    monkeypatch.setattr(native_batch, 'evaluate_native', evaluate)
    return calls


def read_index(repo):
    return json.loads((repo/'batch/index.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('explicit', [False, True])
def test_ordered_once_transport_preserves_options_target_endpoint_and_case_qualification(inputs, monkeypatch, explicit):
    repo, manifest = inputs
    options = dict(response_mode='mechanical', tangent_mode='chunk256', initial_guess='port_projection',
                   minimum_increment=.002, time_limit_seconds=30.) if explicit else {}
    manifest['options'] = options
    save_json(repo/'manifest.json', manifest)
    replies = [response('first', reference=True), response('second')]
    calls = transport(monkeypatch, replies)
    if explicit:
        index = native_batch.evaluate_native_batch('manifest.json', 'batch', repo_root=repo)
    else:
        # Caller exception context must not turn a successful batch into interruption.
        try:
            raise LookupError('unrelated caller exception already being handled')
        except LookupError:
            index = native_batch.evaluate_native_batch('manifest.json', 'batch', repo_root=repo)
    assert index['status'] == 'success' and len(calls) == 2
    assert [call[1].stem for call in calls] == ['first','second']
    for call, label in zip(calls, ('first','second')):
        assert call[0].resolve() == (repo/'geometry'/f'{label}.json').resolve()
        assert call[1].resolve() == (repo/'tasks'/f'{label}.json').resolve()
        assert call[2].resolve() == (repo/'runs'/label).resolve()
        assert all(call[3][key] == value for key, value in options.items())
        assert call[3].get('response_mode','complete') == ('mechanical' if explicit else 'complete')
        assert call[3].get('tangent_mode','full') == ('chunk256' if explicit else 'full')
        assert call[3].get('initial_guess','tangent') == ('port_projection' if explicit else 'tangent')
    assert index == read_index(repo)
    for row, expected in zip(index['cases'], replies):
        for key in ('path','target_response','requested_endpoint_response','maximum_loading_stroke',
                    'last_accepted','failure','independent_reference','views','producer_flags'):
            assert row[key] == expected[key]
        own_file = repo/row['output']['path']/'response.json'
        assert row['response']['path_scope'] == 'repo_relative'
        assert row['response']['path'] == own_file.relative_to(repo).as_posix()
        assert row['response']['sha256'] == sha256(own_file.read_bytes()).hexdigest()
    assert index['cases'][0]['target_response']['d_mm'] == 1.2
    assert index['cases'][0]['requested_endpoint_response']['d_mm'] == 0
    assert index['cases'][0]['independent_reference']['full_path_reference_pass'] is True
    assert index['cases'][1]['independent_reference']['full_path_reference_pass'] is False


@pytest.mark.parametrize('difference', ['E', 'path'])
def test_second_task_physical_difference_rejects_the_whole_batch_before_any_evaluate(inputs, monkeypatch, difference):
    repo, _ = inputs
    task_file = repo/'tasks/second.json'
    task = json.loads(task_file.read_text(encoding='utf-8'))
    if difference == 'E':
        task['material']['E_MPa'] = .8
    else:
        task['path']['targets_mm'][1] = .4
    save_json(task_file, task)
    calls = transport(monkeypatch, [])
    with pytest.raises((OSError, ValueError, KeyError, TypeError)):
        native_batch.evaluate_native_batch('manifest.json', 'batch', repo_root=repo)
    assert calls == [] and not (repo/'batch').exists() and not (repo/'runs').exists()


@pytest.mark.parametrize('difference', ['port', 'binding'])
def test_second_geometry_port_or_task_binding_rejects_before_the_first_evaluate(inputs, monkeypatch, difference):
    repo, _ = inputs
    if difference == 'port':
        geometry_file = repo/'geometry/second.json'
        geometry = json.loads(geometry_file.read_text(encoding='utf-8'))
        geometry['region_tags']['input']['points_mm'][0][0] += .125
        save_json(geometry_file, geometry)
    else:
        task_file = repo/'tasks/second.json'
        task = json.loads(task_file.read_text(encoding='utf-8'))
        task['geometry']['geometry_id'] = '0'*64
        save_json(task_file, task)
    calls = transport(monkeypatch, [])
    with pytest.raises((OSError, ValueError, KeyError, TypeError)):
        native_batch.evaluate_native_batch('manifest.json', 'batch', repo_root=repo)
    assert calls == [] and not (repo/'batch').exists() and not (repo/'runs').exists()


@pytest.mark.parametrize('problem', ['unknown_option','invalid_mode','existing_batch','existing_case'])
def test_invalid_options_or_existing_outputs_leave_every_case_unexecuted_and_keep_old_bytes(inputs, monkeypatch, problem):
    repo, manifest = inputs
    sentinel = None
    if problem == 'unknown_option':
        manifest['options']['reference_file'] = 'old_other_reference.json'
    elif problem == 'invalid_mode':
        manifest['options']['initial_guess'] = 'unreviewed_guess'
    else:
        directory = repo/('batch' if problem=='existing_batch' else 'runs/second')
        sentinel = directory/'keep.txt'
        sentinel.parent.mkdir(parents=True)
        sentinel.write_bytes(b'original output must stay byte exact')
    save_json(repo/'manifest.json', manifest)
    calls = transport(monkeypatch, [])
    with pytest.raises((OSError, ValueError, KeyError, TypeError)):
        native_batch.evaluate_native_batch('manifest.json', 'batch', repo_root=repo)
    assert calls == [] and not (repo/'runs/first').exists()
    if sentinel is not None:
        assert sentinel.read_bytes() == b'original output must stay byte exact'
    assert not (repo/'batch/index.json').exists()


@pytest.mark.parametrize('cause', ['failed_response', 'changed_input'])
def test_first_failure_or_changed_input_stops_without_overwriting_completed_response(inputs, monkeypatch, cause):
    repo, _ = inputs
    first_response = response('first', status='failed' if cause=='failed_response' else 'success')

    def change_pending_input(call_count):
        assert call_count == 1
        task_file = repo/'tasks/second.json'
        task = json.loads(task_file.read_text(encoding='utf-8'))
        task['material']['E_MPa'] = .8
        save_json(task_file, task)

    calls = transport(monkeypatch, [first_response], change_pending_input if cause=='changed_input' else None)
    index = native_batch.evaluate_native_batch('manifest.json', 'batch', repo_root=repo)
    assert len(calls) == 1 and index['status'] != 'success'
    first, second = index['cases']
    assert first['status'] == first_response['status']
    assert first['target_response'] == first_response['target_response']
    assert first['requested_endpoint_response'] == first_response['requested_endpoint_response']
    assert first['last_accepted'] == first_response['last_accepted']
    assert first['failure'] == first_response['failure']
    if cause == 'failed_response':
        assert second['status'] == 'not_run' and second['reason']
    else:
        assert second['status'] == 'error' and second['failure']['reason']
        assert second['response'] is second['target_response'] is second['last_accepted'] is None
    assert not (repo/'runs/second').exists()
    assert json.loads((repo/'runs/first/response.json').read_text(encoding='utf-8')) == first_response
    assert index == read_index(repo)


@pytest.mark.parametrize('supervision', [False, True])
def test_escaped_error_stops_and_records_original_exception_without_fabricating_partial(inputs, monkeypatch, supervision):
    repo, _ = inputs
    error = RuntimeError('cooperative stop') if supervision else TaggedTransportError('original transport failure')
    calls = transport(monkeypatch, [error])
    if supervision:
        with pytest.raises(RuntimeError, match='cooperative stop'):
            native_batch.evaluate_native_batch('manifest.json', 'batch', repo_root=repo)
        index = read_index(repo)
        assert index['status'] == 'interrupted'
    else:
        index = native_batch.evaluate_native_batch('manifest.json', 'batch', repo_root=repo)
        assert index['status'] != 'success'
    assert len(calls) == 1 and index['cases'][1]['status'] == 'not_run'
    assert not (repo/'runs/second').exists()
    assert index['cases'][0]['target_response'] is None and index['cases'][0]['last_accepted'] is None
    assert index['cases'][0]['failure']['exception_class'] == type(error).__name__
    assert index['cases'][0]['failure']['reason'] == str(error)
    assert index['cases'][0]['failure']['code'] == getattr(error, 'code', None)


def test_cli_from_unrelated_cwd_uses_explicit_repo_and_prints_its_own_saved_index(inputs, tmp_path, monkeypatch, capsys):
    repo, _ = inputs
    calls = transport(monkeypatch, [response('first'), response('second')])
    unrelated = tmp_path/'unrelated_cwd'
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)
    script = REPO/'hf_repo/scripts/evaluate_native_batch.py'
    spec = importlib.util.spec_from_file_location('native_batch_cli_for_test', script)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setattr(sys, 'argv', [str(script),'--repo',str(repo),'--manifest','manifest.json','--output','batch'])
    assert cli.main() == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed['status'] == 'success' and printed == read_index(repo)
    assert len(calls) == 2 and all(call[0].is_absolute() and call[1].is_absolute() and call[2].is_absolute() for call in calls)
    assert not (unrelated/'batch').exists()
