"""Supervise one approved composition/display helper and wait for its real exit."""
from time import perf_counter, sleep
STARTED = perf_counter()
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import json
import os
import subprocess
import sys
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    protocol_file = STAGE/'protocol.json'
    protocol = json.loads(protocol_file.read_bytes())
    assert protocol['schema_version'] == 'composed-saved-path-card-1.0' and protocol['card'] == 'M-PATH1'
    assert (protocol['helper_seconds'],protocol['outer_seconds'],protocol['sampled_RSS_bytes']) == (180,240,8*1024**3)
    receipt_file,stop = STAGE/'path_launch.json',STAGE/'stop_requested.txt'
    assert not receipt_file.exists() and not stop.exists()
    def checkpoint():
        if perf_counter()-STARTED > protocol['outer_seconds'] or stop.exists():
            raise RuntimeError('Original outer window closed')
    def identity():
        for name,pin in protocol['bindings'].items():
            checkpoint()
            path = ROOT/name
            assert path.suffix in ('.json','.py','.md','.toml')
            assert sha256(path.read_bytes()).hexdigest() == pin
        for name,declaration in protocol['existing_GIF_identities_stat_only'].items():
            checkpoint()
            assert (ROOT/name).suffix == '.gif' and (ROOT/name).stat().st_size == declaration['bytes']
        checkpoint()
    identity()
    receipt = dict(card='M-PATH1',status='running',invocations=1,
        argv=[sys.executable,'-X','utf8','-B',str(STAGE/'execute_path.py'),'--repo',str(ROOT),'--protocol',str(protocol_file)],
        protocol_sha256=sha256(protocol_file.read_bytes()).hexdigest(),
        started_utc=datetime.now(timezone.utc).isoformat(),
        budget_mode='Earliest whole clock; sampled tree RSS; cooperative stop and real child wait, no force')
    write(receipt_file,receipt)
    peak,reason,error = 0,None,None
    env = dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',MPLBACKEND='Agg')
    with (STAGE/'path_stdout.log').open('xb') as output:
        child_started = perf_counter()
        child = subprocess.Popen(receipt['argv'],cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
        try:
            process = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    members = [process]+process.children(recursive=True)
                    peak = max(peak,sum(member.memory_info().rss for member in members if member.is_running()))
                except psutil.NoSuchProcess:
                    pass
                if reason is None:
                    if perf_counter()-STARTED > protocol['outer_seconds']:
                        reason = 'outer_elapsed_limit'
                    elif perf_counter()-child_started > protocol['helper_seconds']:
                        reason = 'helper_elapsed_limit'
                    elif peak > protocol['sampled_RSS_bytes']:
                        reason = 'sampled_RSS_limit'
                    elif stop.exists():
                        reason = 'external_stop_requested'
                    if reason is not None and not stop.exists():
                        stop.write_text(reason,encoding='utf-8')
                sleep(.1)
        except BaseException as exception:
            error = exception
            reason = reason or type(exception).__name__
        finally:
            if child.poll() is None:
                try:
                    if not stop.exists():
                        stop.write_text(reason or 'launcher_interrupted',encoding='utf-8')
                finally:
                    child.wait()
    child_elapsed = perf_counter()-child_started
    if child_elapsed > protocol['helper_seconds']:
        reason = reason or 'helper_elapsed_limit'
    unchanged = None
    try:
        identity()
        unchanged = True
    except Exception as exception:
        reason = reason or str(exception)
    if stop.exists():
        reason = reason or 'external_stop_requested'
    if perf_counter()-STARTED > protocol['outer_seconds']:
        reason = reason or 'outer_elapsed_limit'
    receipt.update(status='pass' if child.returncode == 0 and reason is None and unchanged else 'not_pass',
        exit_code=child.returncode,elapsed_seconds=perf_counter()-STARTED,helper_wall_seconds=child_elapsed,
        peak_sampled_tree_RSS_bytes=peak,stop_reason=reason,all_bindings_unchanged=unchanged,
        completed_utc=datetime.now(timezone.utc).isoformat(),cleanup='Actual helper waited; partial files retained; no force or rollback')
    write(receipt_file,receipt)
    if receipt['status'] == 'pass' and (stop.exists() or perf_counter()-STARTED > protocol['outer_seconds']):
        receipt.update(status='not_pass',stop_reason='Original outer window closed after receipt write',elapsed_seconds=perf_counter()-STARTED)
        write(receipt_file,receipt)
    print(json.dumps({key:receipt[key] for key in ('status','exit_code','elapsed_seconds','peak_sampled_tree_RSS_bytes','stop_reason','all_bindings_unchanged')}),flush=True)
    if error is not None:
        raise error
    if receipt['status'] != 'pass':
        raise RuntimeError('M-PATH1 closed non-success; no retry, repair, extension, or force')


if __name__ == '__main__':
    main()
