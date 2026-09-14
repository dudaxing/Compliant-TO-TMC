"""Build and install a fresh HF3 wheel; file/install work only, no mechanics."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
import numpy as np

root = Path(__file__).resolve().parents[1]
repo, out = root/'hf_repo', root/'hf3_results'
wheel = repo/'dist/independent_hf_evaluator-0.3.0-py3-none-any.whl'
assert not wheel.exists()
operations = []
log = (out/'installation.log').open('wb')
def run(command, cwd=None):
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=180,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    operations.append(dict(command=command, returncode=result.returncode, seconds=time.perf_counter()-start))
    (out/'installation.json').write_text(json.dumps(operations, indent=2)+'\n')
    if result.returncode:
        raise RuntimeError('Installation/build failed; preserved installation.log')
run([str(repo/'.venv-hf2-repair/Scripts/python.exe'), '-m', 'build', '--wheel', '--no-isolation'], repo)
with zipfile.ZipFile(wheel) as z:
    names = {n for n in z.namelist() if n.startswith('hf_eval/') and n.endswith('.py')}
    assert names == {p.relative_to(repo/'src').as_posix() for p in (repo/'src/hf_eval').glob('*.py')}
    for name in names:
        assert z.read(name) == (repo/'src'/name).read_bytes()
temporary = Path(tempfile.mkdtemp(prefix='hf3_detached_'))
copy = temporary/'hf_repo'
def ignore(directory, names):
    return {n for n in names if n.startswith('.venv') or n in {'.git', 'build', 'dist', '__pycache__', '.pytest_cache'} or n.endswith('.egg-info')}
shutil.copytree(repo, copy, ignore=ignore)
shutil.copytree(root/'geometry_dataset', temporary/'geometry_dataset')
(copy/'dist').mkdir()
shutil.copy2(wheel, copy/'dist'/wheel.name)
reference = {}
freeze = json.loads((out/'production_source_freeze.json').read_text())
reference['source_sha256'] = np.array(freeze['source_sha256'])
for family in ('inverter', 'gripper'):
    found = []
    for path in (out/'bridge_001').rglob('result.json'):
        result = json.loads(path.read_text())
        task = result.get('task_config', {})
        if task.get('case_family') == family and task.get('input', {}).get('target_mm') == 1e-5:
            if result['numerics']['status'] == 'success':
                found.append((path, result))
    assert len(found) == 1, found
    path, result = found[0]
    assert result['implementation']['source_sha256'] == freeze['source_sha256']
    with np.load(path.parent/'path.npz', allow_pickle=False) as z:
        for key in ('u', 'R_input', 'q_out', 'J'):
            reference[family+'_'+key] = z[key][-1]
np.savez_compressed(temporary/'development_reference.npz', **reference)
shutil.copy2(temporary/'development_reference.npz', out/'detached_development_reference.npz')
uv, python = shutil.which('uv'), temporary/'.venv/Scripts/python.exe'
run([uv, 'venv', str(temporary/'.venv'), '--python', 'C:/Python313/python.exe'])
versions = [line.split('\\', 1)[0].strip() for line in (copy/'requirements.lock').read_text().splitlines()
            if re.match(r'^[A-Za-z0-9_.-]+==', line)]
run([uv, 'pip', 'install', '--offline', '--python', str(python), *versions])
run([uv, 'pip', 'install', '--no-deps', '--python', str(python), str(copy/'dist'/wheel.name)])
log.close()
foreign = temporary/'foreign_cwd'; foreign.mkdir()
forbidden = [str(root), 'C:/Users/Lenovo/Downloads/Diversity-TO-Compliant-O-main (6).zip',
    'C:/Users/Lenovo/Zotero/storage/AAXN3GZJ', 'C:/Users/Lenovo/Zotero/storage/RQ982KG5',
    'C:/Users/Lenovo/Zotero/storage/PMK9MVG8']
command = [str(python), '-I', str(copy/'scripts/run_hf3_isolated.py'), '--repository', str(copy),
    '--dataset', str(temporary/'geometry_dataset'), '--reference', str(temporary/'development_reference.npz'),
    '--output', str(temporary/'acceptance')]
for item in forbidden:
    command += ['--forbid', item]
location = dict(detached_root=str(temporary), command=command, cwd=str(foreign),
    wheel_sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(), operations=operations,
    dependency_method='exact lock versions from offline uv cache; third-party original wheel hashes not reverified at install, installed RECORD verification follows',
    source_files_match_wheel=sorted(names))
(out/'detached_location.json').write_text(json.dumps(location, indent=2)+'\n')
print(json.dumps(dict(status='prepared_no_mechanics_run', wheel_sha256=location['wheel_sha256'],
    file_install_seconds=sum(x['seconds'] for x in operations), detached_root=str(temporary))))
