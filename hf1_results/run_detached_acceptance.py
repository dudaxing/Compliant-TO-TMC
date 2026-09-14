"""Orchestrate environment setup and isolated verification, without shell quoting."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import time

root=Path(__file__).resolve().parents[1]
info=json.loads((root/'hf1_results/detached_location.json').read_text(encoding='utf-8'))
detached=Path(info['detached_root'])
repo=Path(info['copied_hf_repo'])
python=detached/'.venv/Scripts/python.exe'
uv=shutil.which('uv')
environment=dict(os.environ)
for key in ['PYTHONPATH','PYTHONHOME','VIRTUAL_ENV','CONDA_PREFIX']:
    environment.pop(key,None)
environment.update(PYTHONNOUSERSITE='1',MPLCONFIGDIR=str(detached/'mplconfig'),
                   OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',UV_LINK_MODE='copy')
commands=[
    [uv,'venv','--python','C:/Python313/python.exe',str(detached/'.venv')],
    [uv,'pip','sync','--python',str(python),'--require-hashes',str(repo/'requirements.lock')],
    [uv,'pip','install','--python',str(python),'--no-deps',str(repo/'dist/independent_hf_evaluator-0.1.0-py3-none-any.whl')],
    [str(python),'-I',str(repo/'scripts/run_isolated.py'),'--dataset',str(detached/'geometry_dataset'),
     '--output',str(detached/'acceptance')]+[item for p in info['forbidden_roots'] for item in ['--forbid',p]],
]
timings=[]
with (root/'hf1_results/detached_console.log').open('w',encoding='utf-8') as log:
    for index,command in enumerate(commands):
        began=time.perf_counter()
        log.write(json.dumps({'step':index,'argv':command},ensure_ascii=False)+'\n');log.flush()
        completed=subprocess.run(command,cwd=info['foreign_cwd'],env=environment,stdout=log,stderr=subprocess.STDOUT,
                                 timeout=300,check=False)
        timings.append({'step':index,'returncode':completed.returncode,'seconds':time.perf_counter()-began})
        if completed.returncode:
            raise RuntimeError(f'Detached stage {index} failed with code {completed.returncode}; see detached_console.log')
after={str(p.relative_to(detached/'geometry_dataset')).replace('\\','/'):
       hashlib.sha256(p.read_bytes()).hexdigest() for p in (detached/'geometry_dataset').rglob('*') if p.is_file()}
unchanged=after==info['dataset_hashes_before']
assert unchanged, 'Detached runtime modified its read-only input package'
assert not (root/'hf1_results/detached').exists(), 'Do not overwrite acceptance evidence'
shutil.copytree(detached/'acceptance',root/'hf1_results/detached')
summary=json.loads((root/'hf1_results/detached/acceptance.json').read_text(encoding='utf-8'))
receipt={'steps':timings,'dataset_files_unchanged':unchanged,'dataset_file_count':len(after),
         'detached_root_record_only':str(detached),'wheel_sha256':info['wheel_sha256'],
         'checks':summary['checks']}
(root/'hf1_results/detached_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
