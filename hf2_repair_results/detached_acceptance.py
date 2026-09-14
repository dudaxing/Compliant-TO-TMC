"""Create a new HF-only environment, install wheel, and audit independent replay."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

root=Path(__file__).resolve().parents[1]
repo=root/'hf_repo'
wheel=repo/'dist/independent_hf_evaluator-0.2.1-py3-none-any.whl'
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()
with zipfile.ZipFile(wheel) as archive:
    sources={n for n in archive.namelist() if n.startswith('hf_eval/') and n.endswith('.py')}
    assert sources=={p.relative_to(repo/'src').as_posix() for p in (repo/'src/hf_eval').glob('*.py')}
    for name in sources:
        assert archive.read(name)==(repo/'src'/name).read_bytes()
temporary=Path(tempfile.mkdtemp(prefix='hf2_repair_detached_'))
copy=temporary/'hf_repo'
def ignore(directory,names):
    return {n for n in names if n.startswith('.venv') or n in {'.git','build','dist','__pycache__','.pytest_cache'} or n.endswith('.egg-info')}
shutil.copytree(repo,copy,ignore=ignore)
shutil.copytree(root/'geometry_dataset',temporary/'geometry_dataset')
(copy/'dist').mkdir()
shutil.copy2(wheel,copy/'dist'/wheel.name)
foreign=temporary/'foreign_cwd';foreign.mkdir()
before={p.relative_to(temporary/'geometry_dataset').as_posix():sha(p) for p in (temporary/'geometry_dataset').rglob('*') if p.is_file()}
python=temporary/'.venv/Scripts/python.exe'
uv=shutil.which('uv')
installations=[]
commands=[[uv,'venv',str(temporary/'.venv'),'--python','C:/Python313/python.exe'],
          [uv,'pip','install','--offline','--python',str(python),
           *[line.split('\\',1)[0].strip() for line in (copy/'requirements.lock').read_text().splitlines() if re.match(r'^[A-Za-z0-9_.-]+==',line)]],
          [uv,'pip','install','--python',str(python),'--no-deps',str(copy/'dist'/wheel.name)]]
with (root/'hf2_repair_results/detached_install_offline.log').open('wb') as log:
    for command in commands:
        start=time.perf_counter()
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        installations.append({'command':command,'seconds':time.perf_counter()-start,'returncode':result.returncode})
        if result.returncode:
            raise RuntimeError('Detached dependency installation failed; see log')
forbidden=[str(root),'C:/Users/Lenovo/Downloads/Diversity-TO-Compliant-O-main (6).zip',
           'C:/Users/Lenovo/Zotero/storage/AAXN3GZJ','C:/Users/Lenovo/Zotero/storage/RQ982KG5',
           'C:/Users/Lenovo/Zotero/storage/PMK9MVG8']
command=[str(python),'-I',str(copy/'scripts/run_hf2_repair_isolated.py'),'--repository',str(copy),
         '--dataset',str(temporary/'geometry_dataset'),'--output',str(temporary/'acceptance')]
for item in forbidden:
    command += ['--forbid',item]
location={'detached_root_record_only':str(temporary),'copied_repository':str(copy),
          'copied_dataset':str(temporary/'geometry_dataset'),'forbidden_roots':forbidden,
          'installations':installations,'wheel_sha256':sha(wheel),'source_files_match_wheel':sorted(sources),
          'dependency_install_method':'exact runtime lock versions from offline uv cache; third-party original archive hashes not reverified in this offline replay; installed RECORD hashes checked'}
(root/'hf2_repair_results/detached_location.json').write_text(json.dumps(location,indent=2),encoding='utf-8')
monitor=[sys.executable,str(root/'hf2_repair_results/run_budgeted.py'),'--name','hf2_repair_detached',
         '--category','isolated','--limit','300','--cwd',str(foreign),'--',*command]
result=subprocess.run(monitor,timeout=330)
if (temporary/'acceptance').exists():
    shutil.copytree(temporary/'acceptance',root/'hf2_repair_results/detached',dirs_exist_ok=False)
after={p.relative_to(temporary/'geometry_dataset').as_posix():sha(p) for p in (temporary/'geometry_dataset').rglob('*') if p.is_file()}
assert before==after
receipt={'returncode':result.returncode,'wheel_sha256':sha(wheel),'dataset_files_unchanged':before==after,
         'dataset_file_count':len(before),'source_files_match_wheel':sorted(sources),
         'detached_root_record_only':str(temporary),'installation_seconds':sum(r['seconds'] for r in installations),
         'dependency_install_method':location['dependency_install_method']}
(root/'hf2_repair_results/detached_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
raise SystemExit(result.returncode)
