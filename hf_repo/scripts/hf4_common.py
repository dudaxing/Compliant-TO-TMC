"""Small ordinary-file helpers for HF4 evidence; no mechanics imports."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path

import numpy as np


def plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [plain(v) for v in value]
    return value


def write_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name+".tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(plain(value), f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def write_npz(path, **arrays):
    path = Path(path)
    tmp = path.with_name(path.name+".tmp")
    try:
        with tmp.open("wb") as f:
            np.savez_compressed(f, **arrays)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_npz(path):
    with np.load(path, allow_pickle=False) as a:
        result = {k:a[k] for k in a.files}
    if any(v.dtype.kind not in "biuf" or not np.all(np.isfinite(v)) for v in result.values()):
        raise ValueError(f"non-real or nonfinite evidence array in {path}")
    return result


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_record():
    repo = Path(__file__).resolve().parents[1]
    return {p.relative_to(repo).as_posix():sha(p) for root in (repo/"src/hf_eval",repo/"scripts")
            for p in sorted(root.glob("*.py"))}


def timestamp():
    return datetime.now(timezone.utc).isoformat()
