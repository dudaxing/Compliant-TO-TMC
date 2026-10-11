"""Future pytest plugin: finite focused selection and cooperative checkpoints."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
import json
import os
import sys
import pytest
import psutil

SOURCE = Path(os.environ['HF_RESUME_SOURCE_ROOT']).resolve()
STOP = Path(os.environ['HF_RESUME_STAGE_STOP'])
RECEIPT = Path(os.environ['HF_RESUME_TEST_RECEIPT'])
LIMIT = float(os.environ['HF_RESUME_TEST_SECONDS'])
EXPECTED = json.loads(os.environ['HF_RESUME_TEST_NODEIDS'])
process = psutil.Process()
peak, stopped, collected, reports = 0, None, [], []
sys.path.insert(0, str(SOURCE / 'src'))


def checkpoint():
    global peak, stopped
    memory = process.memory_info()
    peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
    if STOP.exists() or perf_counter() - STARTED > LIMIT or peak > 8 * 1024**3:
        stopped = stopped or 'Focused test cooperative resource window closed'
        pytest.exit(stopped, returncode=1)


def pytest_collection_finish(session):
    global collected
    collected = [item.nodeid for item in session.items]
    if collected != EXPECTED:
        pytest.exit('Focused node identities differ from frozen selection', returncode=1)
    checkpoint()


def pytest_runtest_setup(item):
    checkpoint()


def pytest_runtest_teardown(item):
    checkpoint()


def pytest_runtest_logreport(report):
    reports.append(dict(nodeid=report.nodeid, when=report.when, outcome=report.outcome))


def pytest_sessionfinish(session, exitstatus):
    global peak, stopped
    memory = process.memory_info()
    peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
    for name, module in tuple(sys.modules.items()):
        if name == 'hf_eval' or name.startswith('hf_eval.'):
            if not Path(module.__file__).resolve().is_relative_to(SOURCE / 'src/hf_eval'):
                exitstatus = 1
                stopped = stopped or 'Focused HF module came from outside the pinned runtime package: ' + name
    if STOP.exists() or perf_counter() - STARTED > LIMIT or peak > 8 * 1024**3:
        exitstatus, stopped = 1, 'Focused test resource window closed at finish'
    value = dict(status='pass' if int(exitstatus) == 0 else 'not_pass', exit_code=int(exitstatus),
        collected_nodeids=collected, reports=reports, stop_reason=stopped,
        elapsed_seconds=perf_counter() - STARTED, peak_sampled_RSS_bytes=peak,
        source_root=str(SOURCE), scope='Four synthetic/algebra controller contracts plus one tiny 16-cell NumPy/TMC public persistence/resume integration; no original parent mechanics, isolated test accounting, no retries')
    with RECEIPT.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    session.exitstatus = exitstatus
