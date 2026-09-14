"""Install pinned cached dependencies in a new development environment."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'hf_repo'
OUT = ROOT / 'hf2_repair_results'
env = REPO / '.venv-hf2-repair'
assert not env.exists(), 'Use a fresh environment; keep prior environments untouched'
uv = shutil.which('uv')
python = env / 'Scripts/python.exe'
runtime = [line.split('\\',1)[0].strip() for line in (REPO/'requirements.lock').read_text().splitlines()
           if re.match(r'^[A-Za-z0-9_.-]+==',line)]
dev = ['pytest==9.1.1','build==1.3.0','setuptools==80.9.0','wheel==0.45.1','psutil==7.2.2']
commands = [[uv,'venv',str(env),'--python','C:/Python313/python.exe'],
            [uv,'pip','install','--offline','--python',str(python),*runtime,*dev],
            [uv,'pip','install','--offline','--no-build-isolation','--no-deps','--python',str(python),'-e',str(REPO)]]
records=[]
with (OUT/'development_install.log').open('wb') as log:
    for command in commands:
        start=time.perf_counter()
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        records.append({'command':command,'returncode':result.returncode,'seconds':time.perf_counter()-start})
        (OUT/'development_install.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        if result.returncode:
            raise SystemExit('Development installation failed; see retained log')
print(json.dumps({'status':'installed','seconds':sum(r['seconds'] for r in records),'python':str(python),
    'method':'Exact cached package versions; third-party original wheel archive hash not reverified in this offline install'},indent=2))
