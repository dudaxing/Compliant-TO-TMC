"""Future M-INTEGRATE1 pytest accounting on the installed default package."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
import json
import os
import sys
import psutil
import pytest

ROOT = Path(os.environ['HF_INTEGRATION_ROOT']).resolve()
SOURCE = ROOT / 'hf_repo'
STAGE = Path(os.environ['HF_INTEGRATION_STAGE']).resolve()
PROTOCOL = json.loads((STAGE / 'protocol.json').read_bytes())
STOP = STAGE / 'stop_requested.txt'
RECEIPT = Path(os.environ['HF_INTEGRATION_TEST_RECEIPT'])
LIMIT = PROTOCOL['focused_tests_seconds']
EXPECTED = PROTOCOL['focused_test_selectors']
sys.path[:0] = [str(SOURCE / 'src'), str(SOURCE / 'tests')]
process = psutil.Process()
peak, stopped, collected, reports, current = 0, None, [], [], None
counts = dict(force_started=0, force_completed=0, tangent_started=0, tangent_completed=0)
by_test, models = {}, []


def checkpoint():
    global peak, stopped
    memory = process.memory_info()
    peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
    if STOP.exists() or perf_counter() - STARTED > LIMIT or peak > PROTOCOL['sampled_RSS_bytes']:
        stopped = stopped or 'Focused test cooperative resource window closed'
        pytest.exit(stopped, returncode=1)


def selector(item):
    return item.path.resolve().relative_to(ROOT).as_posix() + '::' + item.name


def pytest_collection_finish(session):
    global collected
    collected = [selector(item) for item in session.items]
    if collected != EXPECTED:
        pytest.exit('Collected test identities differ from the frozen 25 selections', returncode=1)
    checkpoint()
    from hf_eval import native_mean

    def observed(delegate, kind):
        def call(*args, **kwargs):
            checkpoint()
            local = by_test.setdefault(current, {key: 0 for key in counts})
            counts[kind + '_started'] += 1
            local[kind + '_started'] += 1
            value = delegate(*args, **kwargs)
            counts[kind + '_completed'] += 1
            local[kind + '_completed'] += 1
            checkpoint()
            return value
        return call

    for name, kind in (('_assemble_force', 'force'), ('_assemble_mechanical_force', 'force'),
                       ('_tangent', 'tangent'), ('_tangent_chunked', 'tangent')):
        setattr(native_mean, name, observed(getattr(native_mean, name), kind))
    builder = native_mean.build_native_project

    def checked_model(*args, **kwargs):
        checkpoint()
        project = builder(*args, **kwargs)
        row = dict(test=current, cells=len(project.model.connectivity), dofs=project.model.ndof)
        models.append(row)
        if row['cells'] > 16 or row['dofs'] > 50:
            pytest.exit('Selected real fixture exceeded its declared 16-cell scope', returncode=1)
        checkpoint()
        return project

    native_mean.build_native_project = checked_model


def pytest_runtest_setup(item):
    global current
    current = selector(item)
    checkpoint()


def pytest_runtest_teardown(item):
    checkpoint()


def pytest_runtest_logreport(report):
    reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome))


def pytest_sessionfinish(session, exitstatus):
    global peak, stopped
    memory = process.memory_info()
    peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
    modules = {}
    for name, module in tuple(sys.modules.items()):
        if name == 'hf_eval' or name.startswith('hf_eval.'):
            path = Path(module.__file__).resolve()
            if not path.is_relative_to(SOURCE / 'src/hf_eval'):
                exitstatus, stopped = 1, 'HF module came from outside the installed default package: ' + name
            modules[name] = str(path)
    if STOP.exists() or perf_counter() - STARTED > LIMIT or peak > PROTOCOL['sampled_RSS_bytes']:
        exitstatus, stopped = 1, 'Focused test resource window closed at finish'
    calls = [row for row in reports if row['when'] == 'call']
    if len(calls) != 25 or any(row['outcome'] != 'passed' for row in calls):
        exitstatus = 1
    value = dict(status='pass' if int(exitstatus) == 0 else 'not_pass', exit_code=int(exitstatus),
        collected_selectors=collected, reports=reports, passed_calls=sum(row['outcome'] == 'passed' for row in calls),
        stop_reason=stopped, elapsed_seconds=perf_counter() - STARTED, peak_sampled_RSS_bytes=peak,
        installed_source_root=str(SOURCE), imported_HF_modules=modules, observed_models=models,
        observed_native_mean_entries=counts, observed_native_mean_entries_by_test=by_test,
        accounting_scope='NativeMean NumPy force/tangent aliases only; synthetic/mocked callbacks separate, no universal kernel-call claim',
        qualification_scope='Default-entry compatibility and small test fixtures; no new original gripper, HP, pressure, clamp, stability or HF5 qualification')
    with RECEIPT.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    session.exitstatus = exitstatus
