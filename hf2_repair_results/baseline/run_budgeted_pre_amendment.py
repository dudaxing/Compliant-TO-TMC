"""Development-only bounded process runner with sampled process-tree memory.

Uses psutil from the HF development environment, never a production dependency.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import os
import subprocess
import sys
import time
import uuid

import psutil

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / 'hf2_repair_results/resource_jobs'
JOBS.mkdir(exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument('--category', choices=['small','compile','python_cshape','isolated','postprocess'], required=True)
parser.add_argument('--limit', type=float, required=True)
parser.add_argument('--cwd', required=True)
parser.add_argument('command', nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command[1:] if args.command[:1] == ['--'] else args.command
if not command or args.limit <= 0:
    parser.error('command and positive limit required')
prior = []
for path in JOBS.glob('*.json'):
    prior.append(json.loads(path.read_text(encoding='utf-8')))
used = sum(j.get('wall_seconds', j.get('reserved_limit_seconds', 0)) for j in prior)
small_used = sum(j.get('wall_seconds', j.get('reserved_limit_seconds', 0)) for j in prior if j['category'] in ['small','compile','isolated'])
category_cap = 300 if args.category in ['small','compile','isolated'] else 600 if args.category == 'postprocess' else 1200
limit = min(args.limit, category_cap, 3000 - used)
if args.category in ['small','compile','isolated']:
    limit = min(limit, 1200 - small_used)
if args.category == 'postprocess':
    limit = min(limit, 600 - sum(j.get('wall_seconds', j.get('reserved_limit_seconds',0)) for j in prior if j['category']=='postprocess'))
if args.category == 'python_cshape' and any(j['category']=='python_cshape' for j in prior):
    raise SystemExit('The single corrected full-path attempt has already been used')
if limit <= 0:
    raise SystemExit('Numerical budget exhausted; no process started')
identifier = args.name + '_' + uuid.uuid4().hex[:8]
receipt_path = JOBS / (identifier + '.json')
log_path = JOBS / (identifier + '.log')
receipt = {'name':args.name, 'category':args.category, 'status':'running',
           'started_utc':datetime.now(timezone.utc).isoformat(), 'command':command,
           'cwd':str(Path(args.cwd).resolve()), 'reserved_limit_seconds':limit,
           'prior_recorded_or_reserved_seconds':used, 'log':log_path.name,
           'memory_method':'sampled sum of process-tree RSS/Windows WorkingSet at 0.2 s; not OS sandbox',
           'memory_soft_limit_bytes':4*1024**3}
def save():
    temporary = receipt_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(receipt_path)
save()
env = os.environ.copy()
env.update(JAX_ENABLE_X64='true', JAX_PLATFORMS='cpu', PYTHONIOENCODING='utf-8', OMP_NUM_THREADS='1',
           OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', MPLBACKEND='Agg')
started = time.perf_counter()
peak = 0
samples = 0
stopped = None
with log_path.open('wb') as log:
    process = subprocess.Popen(command, cwd=args.cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    owner = psutil.Process(process.pid)
    while process.poll() is None:
        try:
            descendants = owner.children(recursive=True)
            processes = [owner] + descendants
            rss = sum(p.memory_info().rss for p in processes if p.is_running())
            peak = max(peak, rss)
            samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            processes = [owner]
        elapsed = time.perf_counter() - started
        if elapsed > limit:
            stopped = 'time_limit'
        if peak > receipt['memory_soft_limit_bytes']:
            stopped = 'memory_soft_limit'
        if stopped:
            for child in reversed(processes):
                try:
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            _, alive = psutil.wait_procs(processes, timeout=3)
            for child in alive:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            break
        time.sleep(0.2)
    code = process.wait(timeout=10)
receipt.update(status='complete' if code == 0 and stopped is None else 'failed', returncode=code,
               stop_reason=stopped, wall_seconds=time.perf_counter()-started,
               sampled_peak_tree_rss_bytes=peak, memory_samples=samples)
save()
print(json.dumps(receipt, ensure_ascii=False, indent=2))
tail = log_path.read_text(encoding='utf-8', errors='replace').splitlines()[-12:]
print('\n'.join(tail))
raise SystemExit(0 if receipt['status']=='complete' else 2)
