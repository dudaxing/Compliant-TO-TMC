"""Sequential monitored HF3 jobs; categories are frozen in validation_spec.json."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os, subprocess, sys, time, uuid
import psutil

root=Path(__file__).resolve().parents[1]
spec_path=root/'hf_repo/configs/hf3/validation_spec.json'
spec=json.loads(spec_path.read_text()); limits=spec['resource_limits']
jobs=root/'hf3_results/resource_jobs'; jobs.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--category',choices=limits['category_seconds'],required=True)
p.add_argument('--limit',type=float,default=300);p.add_argument('--cwd',type=Path,default=root/'hf_repo');p.add_argument('command',nargs=argparse.REMAINDER)
a=p.parse_args();command=a.command[1:] if a.command[:1]==['--'] else a.command
if not command: p.error('A command is required')
command[0]=str(Path(command[0]).resolve())
prior=[json.loads(x.read_text()) for x in jobs.glob('*.json')]
assert all(x['status']!='running' for x in prior), 'Numerical processes run sequentially'
used=sum(x['wall_seconds'] for x in prior)
category_used=sum(x['wall_seconds'] for x in prior if x['category']==a.category)
cap=limits['category_seconds'][a.category]
limit=min(a.limit,limits['total_seconds']-used,cap-category_used,cap if a.category.endswith('_path') else limits['small_process_seconds'])
if a.category.endswith('_path') and any(x['category']==a.category and x['process_started'] for x in prior): raise SystemExit('Full path attempt already used')
if limit<=0: raise SystemExit('Numerical budget exhausted')
identifier=a.name+'_'+uuid.uuid4().hex[:8];receipt_path=jobs/(identifier+'.json');log_path=jobs/(identifier+'.log')
r={'name':a.name,'category':a.category,'status':'running','process_started':False,'started_utc':datetime.now(timezone.utc).isoformat(),
 'command':command,'cwd':str(a.cwd.resolve()),'reserved_limit_seconds':limit,'prior_seconds':used,
 'spec_sha256':hashlib.sha256(spec_path.read_bytes()).hexdigest(),'log':log_path.name,
 'memory_method':'sampled process-tree RSS at 0.2 seconds; soft monitoring, not OS isolation'}
def save():
 q=receipt_path.with_suffix('.tmp');q.write_text(json.dumps(r,indent=2)+'\n');q.replace(receipt_path)
save(); env=os.environ.copy();env.update(JAX_ENABLE_X64='true',JAX_PLATFORMS='cpu',PYTHONIOENCODING='utf-8',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLBACKEND='Agg')
started=time.perf_counter();peak=0;stop=None;code=1
with log_path.open('wb') as log:
 try:
  process=subprocess.Popen(command,cwd=a.cwd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  r['process_started']=True;save();owner=psutil.Process(process.pid)
  while process.poll() is None:
   try:
    tree=[owner]+owner.children(recursive=True);peak=max(peak,sum(x.memory_info().rss for x in tree if x.is_running()))
   except (psutil.NoSuchProcess,psutil.AccessDenied): tree=[owner]
   if time.perf_counter()-started>limit:stop='time_limit'
   if peak>limits['memory_soft_limit_bytes']:stop='memory_soft_limit'
   if stop:
    for child in reversed(tree):
     try:child.terminate()
     except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    _,alive=psutil.wait_procs(tree,timeout=2)
    for child in alive:
     try:child.kill()
     except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    break
   time.sleep(.2)
  code=process.wait(timeout=10)
 except OSError as exc:r.update(exception_type=type(exc).__name__,message=str(exc));stop='launch_error'
r.update(status='complete' if code==0 and stop is None else 'failed',returncode=code,stop_reason=stop,wall_seconds=time.perf_counter()-started,sampled_peak_tree_rss_bytes=peak)
save();print(json.dumps(r,indent=2));print('\n'.join(log_path.read_text(encoding='utf-8',errors='replace').splitlines()[-12:]))
raise SystemExit(0 if r['status']=='complete' else 2)
