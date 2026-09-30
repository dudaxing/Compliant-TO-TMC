"""Durable, write-once NDJSON events for one supervised S0 child process.

Only the standard library is imported. Every event is flushed and fsynced;
logging failure is fatal and must never be caught as an expected diagnostic.
One process owns one file. A runner must assign distinct files to its children.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import threading
import time


SCHEMA = "hf-s0-event-1"
RESERVED = frozenset(("schema", "sequence", "utc", "monotonic", "pid",
                      "source_manifest_sha256", "phase", "version", "event"))


class EventLogError(RuntimeError):
    """The evidence channel failed; the owning execution must stop."""


def long_path(path):
    """Absolute filesystem path, including the Windows extended-length form."""
    value=os.path.abspath(os.fspath(path))
    if os.name=="nt" and not value.startswith("\\\\?\\"):
        value="\\\\?\\UNC\\"+value[2:] if value.startswith("\\\\") else "\\\\?\\"+value
    return Path(value)


class EventLog:
    def __init__(self, path=None, *, source_manifest_sha256=None, phase=None, version=None):
        self._stream=None
        self._sequence=0
        self._failure=None
        self._lock=threading.Lock()
        self._pid=os.getpid()
        try:
            path=path if path is not None else os.environ["HF_S0_EVENT_FILE"]
            digest=(source_manifest_sha256 if source_manifest_sha256 is not None
                    else os.environ["HF_S0_SOURCE_MANIFEST_SHA"])
            self.phase=phase if phase is not None else os.environ["HF_S0_PHASE"]
            self.version=version if version is not None else os.environ["HF_S0_VERSION"]
            if not isinstance(digest,str) or re.fullmatch(r"[0-9a-f]{64}",digest) is None:
                raise ValueError("source_manifest_sha256 must be 64 lowercase hexadecimal digits")
            if not isinstance(self.phase,str) or not self.phase.strip():
                raise ValueError("phase must be a nonempty string")
            if not isinstance(self.version,str) or not self.version.strip():
                raise ValueError("version must be a nonempty string")
            if not os.fspath(path):
                raise ValueError("event file path must not be empty")
            self.source_manifest_sha256=digest
            self.path=long_path(path)
            self.path.parent.mkdir(parents=True,exist_ok=True)
            self._stream=self.path.open("x",encoding="utf-8",newline="\n",buffering=1)
        except Exception as error:
            self._failure=error
            raise EventLogError("cannot create the write-once S0 event log: "+str(error)) from error

    def emit(self, event, **fields):
        """Append one complete durable event; reserved identity fields are fixed."""
        with self._lock:
            if self._failure is not None:
                raise EventLogError("S0 event log previously failed") from self._failure
            try:
                if self._stream is None or self._stream.closed:
                    raise ValueError("S0 event log is closed")
                if os.getpid()!=self._pid:
                    raise ValueError("an S0 event log cannot be shared across processes")
                if not isinstance(event,str) or not event.strip():
                    raise ValueError("event must be a nonempty string")
                if RESERVED.intersection(fields):
                    raise ValueError("event payload cannot replace reserved identity fields")
                record=dict(schema=SCHEMA,sequence=self._sequence+1,
                    utc=datetime.now(timezone.utc).isoformat(),monotonic=time.monotonic(),
                    pid=self._pid,source_manifest_sha256=self.source_manifest_sha256,
                    phase=self.phase,version=self.version,event=event,**fields)
                encoded=json.dumps(record,ensure_ascii=False,allow_nan=False,separators=(",",":"))+"\n"
                self._stream.write(encoded)
                self._stream.flush()
                os.fsync(self._stream.fileno())
                self._sequence+=1
                return record
            except Exception as error:
                self._failure=error
                raise EventLogError("cannot durably append an S0 event: "+str(error)) from error

    def close(self):
        with self._lock:
            if self._stream is None or self._stream.closed:
                return
            try:
                self._stream.flush()
                os.fsync(self._stream.fileno())
                self._stream.close()
            except Exception as error:
                self._failure=error
                raise EventLogError("cannot close the S0 event log: "+str(error)) from error

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
        return False
