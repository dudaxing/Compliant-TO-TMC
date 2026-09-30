"""Standard-library evidence for the one declared JAX transpose exception.

Classification uses the current exception's real terminal traceback frame,
the installed source bytes and its exact assertion. Text in messages, causes
or formatted traceback strings never establishes the mechanism.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import sysconfig
import tokenize
import traceback as traceback_module
from types import TracebackType


AD_SOURCE_SHA256 = "3e54a02d0e2f45c42e0ed0bf9489ab58b6bcf360653539a44864a211b9d601b4"
AD_MODULE = "jax._src.interpreters.ad"
ASSERTIONS = {
    "fancy_bilinear_transpose": "assert isinstance(x, GradAccum) ^ isinstance(y, GradAccum), (x, y)",
    "bilinear_transpose": "assert is_undefined_primal(x) ^ is_undefined_primal(y)",
}


def _canonical(filename):
    value=os.path.realpath(os.path.abspath(os.fspath(filename)))
    if value.startswith("\\\\?\\UNC\\"):
        value="\\\\"+value[8:]
    elif value.startswith("\\\\?\\"):
        value=value[4:]
    return os.path.normcase(os.path.normpath(value))


def _read_source(filename):
    data=Path(filename).read_bytes()
    encoding,_=tokenize.detect_encoding(io.BytesIO(data).readline)
    return hashlib.sha256(data).hexdigest(),data.decode(encoding).splitlines()


def exception_details(error, tb=None):
    """Serialize real traceback frames, allowing extra top-level stage metadata."""
    if not isinstance(error,BaseException):
        raise TypeError("error must be an actual BaseException")
    tb=error.__traceback__ if tb is None else tb
    if tb is not None and not isinstance(tb,TracebackType):
        raise TypeError("tb must be the native traceback, not a rendered/wrapped stack")
    formatted="".join(traceback_module.format_exception(type(error),error,tb,chain=True))
    frames=[];source_cache={};current=tb
    while current is not None:
        code=current.tb_frame.f_code
        filename=code.co_filename
        row=dict(filename=filename,lineno=current.tb_lineno,function=code.co_name,
                 module=current.tb_frame.f_globals.get("__name__"),
                 code_firstlineno=code.co_firstlineno,source_line=None,source_sha256=None)
        if filename not in source_cache:
            try:
                source_cache[filename]=_read_source(filename)
            except (OSError,UnicodeError,SyntaxError,LookupError,ValueError) as source_error:
                source_cache[filename]=source_error
        source=source_cache[filename]
        if isinstance(source,Exception):
            row["source_read_error"]=type(source).__name__+": "+str(source)
        else:
            digest,lines=source
            row["source_sha256"]=digest
            if 1<=current.tb_lineno<=len(lines):
                row["source_line"]=lines[current.tb_lineno-1].strip()
        frames.append(row)
        current=current.tb_next
    return dict(type=type(error).__name__,module=type(error).__module__,message=str(error),
                traceback=formatted,frames=frames,terminal=frames[-1] if frames else None)


def is_declared_transpose(detail):
    """True only for the pinned installed AD module's terminal XOR assertion.

    The caller separately limits which diagnostic stage may observe it. A
    qualifying mechanism does not itself authorize continuation or a repair.
    Extra top-level keys, such as ``stage``, do not affect this predicate.
    """
    try:
        if not isinstance(detail,dict) or detail.get("type")!="AssertionError" or detail.get("module")!="builtins":
            return False
        frames=detail.get("frames");terminal=detail.get("terminal")
        if not isinstance(frames,list) or not frames or not isinstance(terminal,dict) or terminal!=frames[-1]:
            return False
        name=terminal.get("function")
        if name not in ASSERTIONS or terminal.get("module")!=AD_MODULE:
            return False
        installed=Path(sysconfig.get_path("purelib"))/"jax/_src/interpreters/ad.py"
        if _canonical(terminal["filename"])!=_canonical(installed):
            return False
        digest,lines=_read_source(installed)
        if digest!=AD_SOURCE_SHA256 or terminal.get("source_sha256")!=digest:
            return False
        assertion=ASSERTIONS[name]
        positions=[index+1 for index,line in enumerate(lines) if line.strip()==assertion]
        if len(positions)!=1:
            return False
        lineno=positions[0]
        # Both pinned functions have their XOR assertion as the first body
        # statement. Check the real terminal line and function start as well.
        return (type(terminal.get("lineno")) is int and terminal["lineno"]==lineno
                and terminal.get("source_line")==assertion
                and terminal.get("code_firstlineno")==lineno-1
                and lines[lineno-2].startswith("def "+name+"("))
    except (KeyError,TypeError,OSError,UnicodeError,SyntaxError,LookupError,ValueError):
        return False
