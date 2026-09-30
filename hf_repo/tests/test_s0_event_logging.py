"""Three bounded synthetic evidence tests, run only inside the S0 window."""
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

import psutil
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from s0_event_log import long_path
from s0_ad_exception import is_declared_transpose
from windows_owned_process import run_owned


pytestmark=pytest.mark.skipif(os.name!="nt",reason="Windows Job/long-path evidence contract")


def environment(event_file, phase):
    result=os.environ.copy()
    scripts=str(Path(__file__).resolve().parents[1]/"scripts")
    result.update(HF_S0_EVENT_FILE=str(event_file),HF_S0_PHASE="synthetic_"+phase,
        HF_S0_SOURCE_MANIFEST_SHA=os.environ.get("HF_S0_SOURCE_MANIFEST_SHA","0"*64),
        HF_S0_VERSION=os.environ.get("HF_S0_VERSION","synthetic"),
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",PYTHONUNBUFFERED="1",PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=scripts+(os.pathsep+result["PYTHONPATH"] if result.get("PYTHONPATH") else ""))
    return result


def complete_events(path):
    if not path.exists():
        return []
    data=path.read_bytes()
    # An observer may race a write; only newline-terminated records count.
    return [json.loads(line) for line in data.split(b"\n")[:-1] if line]


def pytest_command(test_file, xml_file=None):
    command=[sys.executable,"-u","-B","-m","pytest","-x","--maxfail=1","-vv","--tb=long",
             "-p","no:cacheprovider","-p","hf_s0_pytest_events",str(test_file)]
    if xml_file is not None:
        command.append("--junitxml="+str(xml_file))
    return command


def test_first_failure_is_durable_before_exit_and_sentinel_never_starts(tmp_path):
    tmp_path=long_path(tmp_path)
    events=tmp_path/"first_failure.ndjson";ack=tmp_path/"observer_ack";sentinel=tmp_path/"sentinel"
    test_file=tmp_path/"test_synthetic_first_failure.py"
    test_file.write_text(
        "from pathlib import Path\nimport time\nimport pytest\n"
        "@pytest.fixture\ndef wait_for_observer():\n    yield\n    deadline=time.monotonic()+5\n"
        f"    while not Path({str(ack)!r}).exists() and time.monotonic()<deadline: time.sleep(.01)\n"
        f"    assert Path({str(ack)!r}).exists(), 'failure was not observed before teardown'\n"
        "def test_00_first(wait_for_observer):\n    assert False, 'hf-s0-synthetic-first-failure'\n"
        f"def test_01_sentinel():\n    Path({str(sentinel)!r}).write_text('unexpected')\n",encoding="utf-8")
    observed=[];observer_errors=[];stop=threading.Event()
    def observe():
        try:
            deadline=time.monotonic()+7
            while not stop.is_set() and time.monotonic()<deadline:
                for row in complete_events(events):
                    if row["event"]=="test_report" and row.get("when")=="call" and row.get("outcome")=="failed":
                        observed.append(dict(event=row,process_alive=psutil.pid_exists(row["pid"])))
                        ack.write_text("observed complete durable failure",encoding="utf-8")
                        return
                time.sleep(.01)
        except Exception as error:
            observer_errors.append(repr(error))
    watcher=threading.Thread(target=observe,daemon=True);watcher.start()
    try:
        receipt=run_owned(pytest_command(test_file),cwd=str(tmp_path),env=environment(events,"first_failure"),
                          log=tmp_path/"pytest.log",deadline=time.monotonic()+9,seconds=8)
    finally:
        stop.set();watcher.join(timeout=.5)
    assert not watcher.is_alive() and not observer_errors
    assert receipt["returncode"]==1 and receipt["reason"]=="nonzero_exit" and receipt["cleanup_verified"]
    assert len(observed)==1 and observed[0]["process_alive"]
    failure=observed[0]["event"]
    assert failure["exception"]["type"]=="AssertionError"
    detail=failure["exception"]
    assert detail["frames"] and detail["terminal"]==detail["frames"][-1]
    assert detail["terminal"]["function"]=="test_00_first"
    assert long_path(detail["terminal"]["filename"])==test_file
    assert detail["terminal"]["source_sha256"]==hashlib.sha256(test_file.read_bytes()).hexdigest()
    assert long_path(failure["test_file_path"])==test_file
    assert not is_declared_transpose(detail)
    # Rendered AD keywords cannot turn this actual synthetic test frame into
    # the installed module's terminal XOR assertion.
    misleading=dict(detail,traceback="jax/_src/interpreters/ad.py fancy_bilinear_transpose GradAccum AssertionError")
    assert not is_declared_transpose(misleading)
    assert failure["nodeid"].endswith("test_synthetic_first_failure.py::test_00_first")
    assert "hf-s0-synthetic-first-failure" in failure["longreprtext"]
    assert "test_00_first" in failure["traceback"]
    rows=complete_events(events)
    assert not sentinel.exists()
    assert not any(row["event"]=="test_start" and "test_01_sentinel" in row["nodeid"] for row in rows)
    assert rows[-1]["event"]=="session_finish" and rows[-1]["exitstatus"]==1
    assert [row["sequence"] for row in rows]==list(range(1,len(rows)+1))


def test_event_remains_readable_after_forced_job_termination(tmp_path):
    tmp_path=long_path(tmp_path);events=tmp_path/"killed.ndjson"
    code=("from s0_event_log import EventLog\nimport time\n"
          "log=EventLog()\nlog.emit('stage_started',stage='synthetic_sleep',outcome='started')\n"
          "time.sleep(20)\nlog.emit('stage_ended',stage='synthetic_sleep')\n")
    receipt=run_owned([sys.executable,"-u","-B","-c",code],cwd=str(tmp_path),
        env=environment(events,"forced_termination"),log=tmp_path/"child.log",
        deadline=time.monotonic()+1.5,seconds=8)
    assert receipt["reason"]=="global_deadline" and receipt["cleanup_verified"]
    rows=complete_events(events)
    assert len(rows)==1 and rows[0]["event"]=="stage_started"
    assert rows[0]["stage"]=="synthetic_sleep" and rows[0]["sequence"]==1
    assert events.read_bytes().endswith(b"\n")


def test_long_path_event_xml_and_seal_chain(tmp_path):
    tmp_path=long_path(tmp_path)
    deep=tmp_path/("a"*85)/("b"*85)/("c"*85)
    deep.mkdir(parents=True)
    events=deep/"events.ndjson";xml=deep/"junit.xml";seal=deep/"seal.json"
    assert all(len(str(path))>260 for path in (events,xml,seal))
    test_file=tmp_path/"test_synthetic_long_path.py"
    test_file.write_text("def test_success():\n    assert 2+2==4\n",encoding="utf-8")
    receipt=run_owned(pytest_command(test_file,xml),cwd=str(tmp_path),env=environment(events,"long_path"),
                      log=deep/"pytest.log",deadline=time.monotonic()+8,seconds=7)
    assert receipt["reason"]=="normal_exit" and receipt["returncode"]==0 and receipt["cleanup_verified"]
    rows=complete_events(events)
    assert rows[-1]["event"]=="session_finish" and rows[-1]["exitstatus"]==0
    assert 'failures="0"' in xml.read_text(encoding="utf-8")
    bindings={path.name:dict(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
              for path in (events,xml)}
    with seal.open("x",encoding="utf-8",newline="\n") as stream:
        json.dump(bindings,stream,sort_keys=True);stream.write("\n");stream.flush();os.fsync(stream.fileno())
    for name,row in json.loads(seal.read_text(encoding="utf-8")).items():
        path=deep/name
        assert path.stat().st_size==row["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row["sha256"]
