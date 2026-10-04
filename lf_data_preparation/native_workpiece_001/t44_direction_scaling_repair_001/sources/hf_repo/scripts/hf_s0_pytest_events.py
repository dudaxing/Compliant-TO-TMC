"""Explicit pytest plugin for immediate, durable S0 failure evidence.

Load with ``-p hf_s0_pytest_events`` and disable automatic external plugins.
This plugin records evidence; the runner must also select ``-x --maxfail=1``.
"""
from __future__ import annotations

import os
import pytest

from s0_event_log import EventLog
from s0_ad_exception import exception_details


_active=None
_test_paths={}


def _emit(event, **fields):
    if _active is None:
        raise RuntimeError("S0 pytest event log was not initialized")
    return _active.emit(event,harness_id=os.environ.get("HF_HARNESS_ID"),
        harness_manifest_sha256=os.environ.get("HF_HARNESS_MANIFEST_SHA"),**fields)


def pytest_configure(config):
    global _active,_test_paths
    if _active is not None:
        raise RuntimeError("S0 pytest event log is already active")
    _active=EventLog()
    _test_paths={}
    _emit("session_configured",pytest_version=pytest.__version__,
          invocation=list(config.invocation_params.args),maxfail=config.option.maxfail,
          rootdir=str(config.rootpath),rootpath=str(config.rootpath),
          invocation_dir=str(config.invocation_params.dir),
          declared_harness_test=os.environ.get("HF_JIT_AD_HARNESS_TEST"),
          declared_harness_manifest=os.environ.get("HF_JIT_AD_HARNESS_MANIFEST"),
          declared_harness_sha256=os.environ.get("HF_JIT_AD_HARNESS_SHA"))


def pytest_sessionstart(session):
    _emit("session_start",outcome="started")


def pytest_collection_finish(session):
    _test_paths.update({item.nodeid:str(item.path.resolve()) for item in session.items})
    _emit("collection_finish",nodeids=[item.nodeid for item in session.items],
          collected=len(session.items),outcome="passed" if session.testsfailed==0 else "failed")


def pytest_collectreport(report):
    _emit("collection_report",nodeid=report.nodeid,when="collect",outcome=report.outcome,
          longreprtext=report.longreprtext if report.failed else None,
          traceback=report.longreprtext if report.failed else None)


def pytest_runtest_logstart(nodeid, location):
    _emit("test_start",nodeid=nodeid,location=list(location),outcome="started",
          test_file_path=_test_paths[nodeid],source_path=_test_paths[nodeid])


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_makereport(item, call):
    outcome=yield
    report=outcome.get_result()
    exception=None
    if call.excinfo is not None:
        exception=exception_details(call.excinfo.value,call.excinfo.tb)
    text=report.longreprtext if report.failed else None
    _emit("test_report",nodeid=report.nodeid,when=report.when,outcome=report.outcome,
          test_file_path=str(item.path.resolve()),source_path=str(item.path.resolve()),
          duration_seconds=report.duration,exception=exception,
          exception_type=exception["type"] if exception else None,
          longreprtext=text,traceback=text,captured_stdout=report.capstdout,
          captured_stderr=report.capstderr,sections=list(report.sections),
          skipped_reason=str(report.longrepr) if report.skipped else None)


def pytest_runtest_logfinish(nodeid, location):
    _emit("test_finish",nodeid=nodeid,location=list(location))


def pytest_internalerror(excrepr, excinfo):
    # If logging itself failed, a second write also fails loudly rather than
    # silently changing the evidence failure into a scientific observation.
    _emit("pytest_internal_error",outcome="error",exception=exception_details(excinfo.value,excinfo.tb),
        exception_type=excinfo.type.__name__,traceback=str(excrepr),longreprtext=str(excrepr))


def pytest_keyboard_interrupt(excinfo):
    _emit("pytest_interrupted",outcome="error",exception=exception_details(excinfo.value,excinfo.tb),
        exception_type=excinfo.type.__name__,traceback=str(excinfo.getrepr(style="long")))


def pytest_sessionfinish(session, exitstatus):
    _emit("session_finish",exitstatus=int(exitstatus),testsfailed=session.testsfailed,
          testscollected=session.testscollected,outcome="passed" if int(exitstatus)==0 else "failed")


def pytest_unconfigure(config):
    global _active
    if _active is not None:
        logger=_active
        _active=None
        logger.close()
