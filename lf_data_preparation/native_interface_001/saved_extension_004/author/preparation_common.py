"""Ordinary-only preparation helpers; no project or scientific imports."""
from pathlib import Path
from hashlib import sha256
import json
import math
import subprocess

REL = 'lf_data_preparation/native_interface_001/saved_extension_004'
CARD = 'M-UNLOAD2'
PARENT = 'lf_data_preparation/native_interface_001/saved_extension_003'
MANIFEST = 'handoff/repository_manifest.json'
ORIGIN = 'https://github.com/dudaxing/Compliant-TO-TMC.git'
APPENDED = [1.0,.9,.8,.75,.65,.5,.25,0.0]
TARGETS = [1.05]+APPENDED
ORDINARY = {'.json','.py','.md','.patch','.toml'}
git = lambda root,*args: subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=root)
names = lambda raw: {part.decode('utf-8') for part in raw.split(b'\0') if part}


def raw(path):
    assert path.suffix.lower() in ORDINARY
    return path.read_bytes()


def read(path):
    assert path.suffix.lower() == '.json'
    return json.loads(raw(path))


def sha(path):
    return sha256(raw(path)).hexdigest()


def encoded(value):
    return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')


def new(path,value):
    assert path.suffix.lower() in ORDINARY
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream: stream.write(value if isinstance(value,bytes) else encoded(value))


def canonical(value):
    if isinstance(value,dict): return {key:canonical(item) for key,item in value.items()}
    if isinstance(value,list): return [canonical(item) for item in value]
    if isinstance(value,float):
        assert math.isfinite(value)
        return (0.0 if value == 0.0 else value).hex()
    return value


def canonical_hash(value):
    return sha256(json.dumps(canonical(value),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()


def prior_base(path):
    proof = read(path)
    assert proof['status'] == 'published_and_incrementally_restored_pass'
    assert proof['executed_card'] == 'M-UNLOAD1' and proof['execution_status'] == 'pass' and proof['execution_closed'] is True
    base = proof['published_commit']; assert isinstance(base,str) and len(base) == 40
    return base,proof
