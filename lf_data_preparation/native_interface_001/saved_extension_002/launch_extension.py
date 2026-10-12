"""Launch the single approved extension phase; retain actual partial install and cleanup."""
from time import perf_counter,sleep
STARTED = perf_counter()
from datetime import datetime,timezone
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import psutil

ROOT=Path(__file__).resolve().parents[3]
STAGE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('production',))
    parser.add_argument('--protocol',type=Path,default=STAGE/'protocol.json')
    args=parser.parse_args(); protocol_file=args.protocol.resolve()
    protocol=json.loads(protocol_file.read_bytes()); row=protocol['phases'][args.phase]
    assert protocol['schema_version']=='saved-native-explicit-extension-card-1.0' and protocol['card']=='M-EXTEND2'
    assert (row['helper_seconds'],row['outer_seconds'],protocol['sampled_RSS_bytes'])==(3000,3060,8*1024**3)
    receipt_file=STAGE/(args.phase+'_launch.json'); assert not receipt_file.exists()
    pins,transitions=protocol['bindings'],protocol['installation']
    assert not {item['target'] for item in transitions}&set(pins)
    assert all(sha(ROOT/name)==expected for name,expected in pins.items())
    assert all(sha(ROOT/item['target'])==item['old_sha256'] for item in transitions)
    receipt=dict(phase=args.phase,status='running',invocations=1,argv=[sys.executable,'-B']+row['argv'],
        protocol_sha256=sha(protocol_file),bindings=pins,installation=transitions,helper_seconds=row['helper_seconds'],outer_seconds=row['outer_seconds'],
        sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],started_utc=datetime.now(timezone.utc).isoformat(),
        budget_mode='Whole clock before imports/bootstrap; cooperative children and sampled tree RSS, no force/OS hard cap')
    write(receipt_file,receipt)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',MPLBACKEND='Agg')
    peak,stop_reason,launch_error=0,None,None
    with (STAGE/(args.phase+'_stdout.log')).open('xb') as output:
        child_started=perf_counter()
        child=subprocess.Popen(receipt['argv'],cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
        try:
            process=psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    members=[process]+process.children(recursive=True)
                    peak=max(peak,sum(p.memory_info().rss for p in members if p.is_running()))
                except psutil.NoSuchProcess: pass
                if stop_reason is None and (perf_counter()-STARTED>row['outer_seconds'] or perf_counter()-child_started>row['helper_seconds'] or peak>protocol['sampled_RSS_bytes']):
                    stop_reason=('external_elapsed_limit' if perf_counter()-STARTED>row['outer_seconds'] else
                        'helper_elapsed_limit' if perf_counter()-child_started>row['helper_seconds'] else 'sampled_RSS_limit')
                    (STAGE/'stop_requested.txt').write_text(stop_reason,encoding='utf-8')
                sleep(.1)
        except BaseException as exception:
            launch_error=exception; stop_reason=stop_reason or type(exception).__name__
        finally:
            if child.poll() is None:
                try:
                    if not (STAGE/'stop_requested.txt').exists():
                        (STAGE/'stop_requested.txt').write_text(stop_reason or 'launcher_interrupted',encoding='utf-8')
                finally: child.wait()  # Helper waits its children; no force or orphan.
    child_elapsed=perf_counter()-child_started
    if stop_reason is None and child_elapsed>row['helper_seconds']: stop_reason='helper_elapsed_limit'
    if stop_reason is None and (STAGE/'stop_requested.txt').exists(): stop_reason='external_stop_requested'
    unchanged=all(sha(ROOT/name)==expected for name,expected in pins.items())
    actual={item['target']:sha(ROOT/item['target']) for item in transitions}
    installed=all(actual[item['target']]==item['new_sha256'] for item in transitions)
    if stop_reason is None and perf_counter()-STARTED>row['outer_seconds']: stop_reason='external_elapsed_limit'
    if stop_reason is None and (STAGE/'stop_requested.txt').exists(): stop_reason='external_stop_requested'
    receipt.update(status='pass' if child.returncode==0 and stop_reason is None and unchanged and installed else 'not_pass',
        exit_code=child.returncode,elapsed_seconds=perf_counter()-STARTED,helper_wall_seconds=child_elapsed,peak_sampled_tree_RSS_bytes=peak,
        stop_reason=stop_reason,all_bindings_unchanged=unchanged,actual_default_SHA256=actual,installation_complete=installed,
        completed_utc=datetime.now(timezone.utc).isoformat(),cleanup='Actual helper termination waited; partial install retained, no rollback')
    write(receipt_file,receipt)
    if receipt['status']=='pass' and ((STAGE/'stop_requested.txt').exists() or perf_counter()-STARTED>row['outer_seconds']):
        reason='external_stop_requested' if (STAGE/'stop_requested.txt').exists() else 'external_elapsed_limit_after_receipt_write'
        receipt.update(status='not_pass',stop_reason=reason,elapsed_seconds=perf_counter()-STARTED); write(receipt_file,receipt)
    print(json.dumps({key:receipt[key] for key in ('phase','status','exit_code','elapsed_seconds','peak_sampled_tree_RSS_bytes','stop_reason','all_bindings_unchanged','installation_complete')}),flush=True)
    if launch_error is not None: raise launch_error
    if receipt['status']!='pass': raise RuntimeError('M-EXTEND2 closed non-success; no retry, repair, extension, force or rollback')


if __name__=='__main__': main()
