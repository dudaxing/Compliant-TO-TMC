"""Supervise one approved default unload helper; cooperative stop and real child wait."""
from time import perf_counter, sleep
STARTED = perf_counter()
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import argparse
import json
import os
import subprocess
import sys
import psutil

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent


def sha(path, checkpoint=lambda: None):
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            checkpoint(); digest.update(block)
    checkpoint(); return digest.hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('production',))
    parser.add_argument('--protocol',type=Path,default=STAGE/'protocol.json')
    args = parser.parse_args()
    protocol_file = args.protocol.resolve(); protocol = json.loads(protocol_file.read_bytes())
    row = protocol['phases'][args.phase]
    assert protocol_file.parent == STAGE and protocol['schema_version'] == 'saved-native-default-unload-card-1.0' and protocol['card'] == 'M-UNLOAD1'
    assert (row['helper_seconds'],row['outer_seconds'],protocol['sampled_RSS_bytes']) == (2700,2760,8*1024**3)
    receipt_file = STAGE/'production_launch.json'; assert not receipt_file.exists()
    def identity_checkpoint():
        if perf_counter()-STARTED > row['outer_seconds'] or (STAGE/'stop_requested.txt').exists():
            raise RuntimeError('Original outer identity-check window closed; no scientific hash extension')
    pins = protocol['bindings']
    assert all(sha(ROOT/name,identity_checkpoint) == pin for name,pin in pins.items())
    receipt = dict(phase=args.phase,card='M-UNLOAD1',status='running',invocations=1,
        argv=[sys.executable,'-B']+row['argv'],protocol_sha256=sha(protocol_file),bindings=pins,
        helper_seconds=row['helper_seconds'],outer_seconds=row['outer_seconds'],sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        started_utc=datetime.now(timezone.utc).isoformat(),
        budget_mode='Earliest whole clock and actual child wall; sampled process-tree RSS; cooperative stop, no force or OS hard cap')
    write(receipt_file,receipt)
    env = dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',MPLBACKEND='Agg')
    peak, stop_reason, launch_error = 0, None, None
    with (STAGE/'production_stdout.log').open('xb') as output:
        child_started = perf_counter()
        child = subprocess.Popen(receipt['argv'],cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT)
        try:
            process = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    members = [process]+process.children(recursive=True)
                    peak = max(peak,sum(member.memory_info().rss for member in members if member.is_running()))
                except psutil.NoSuchProcess: pass
                if stop_reason is None and (perf_counter()-STARTED > row['outer_seconds'] or perf_counter()-child_started > row['helper_seconds'] or peak > protocol['sampled_RSS_bytes']):
                    stop_reason = ('external_elapsed_limit' if perf_counter()-STARTED > row['outer_seconds'] else
                        'helper_elapsed_limit' if perf_counter()-child_started > row['helper_seconds'] else 'sampled_RSS_limit')
                    (STAGE/'stop_requested.txt').write_text(stop_reason,encoding='utf-8')
                sleep(.1)
        except BaseException as exception:
            launch_error = exception; stop_reason = stop_reason or type(exception).__name__
        finally:
            if child.poll() is None:
                try:
                    if not (STAGE/'stop_requested.txt').exists(): (STAGE/'stop_requested.txt').write_text(stop_reason or 'launcher_interrupted',encoding='utf-8')
                finally: child.wait()
    child_elapsed = perf_counter()-child_started
    if child_elapsed > row['helper_seconds']: stop_reason = stop_reason or 'helper_elapsed_limit'
    if (STAGE/'stop_requested.txt').exists(): stop_reason = stop_reason or 'external_stop_requested'
    unchanged = None
    try:
        unchanged = all(sha(ROOT/name,identity_checkpoint) == pin for name,pin in pins.items())
    except RuntimeError as exception:
        stop_reason = stop_reason or str(exception)
        receipt['final_identity_check_skipped_or_incomplete'] = 'Closed original outer window; no science hash retry'
    if perf_counter()-STARTED > row['outer_seconds']: stop_reason = stop_reason or 'external_elapsed_limit'
    if (STAGE/'stop_requested.txt').exists(): stop_reason = stop_reason or 'external_stop_requested'
    receipt.update(status='pass' if child.returncode == 0 and stop_reason is None and unchanged is True else 'not_pass',
        exit_code=child.returncode,elapsed_seconds=perf_counter()-STARTED,helper_wall_seconds=child_elapsed,
        peak_sampled_tree_RSS_bytes=peak,stop_reason=stop_reason,all_bindings_unchanged=unchanged,
        completed_utc=datetime.now(timezone.utc).isoformat(),cleanup='Actual helper and its pure child waited; partial outputs retained, no force/rollback')
    write(receipt_file,receipt)
    if receipt['status'] == 'pass' and ((STAGE/'stop_requested.txt').exists() or perf_counter()-STARTED > row['outer_seconds']):
        reason = 'external_stop_requested' if (STAGE/'stop_requested.txt').exists() else 'external_elapsed_limit_after_receipt_write'
        receipt.update(status='not_pass',stop_reason=reason,elapsed_seconds=perf_counter()-STARTED); write(receipt_file,receipt)
    print(json.dumps({key:receipt[key] for key in ('phase','status','exit_code','elapsed_seconds','peak_sampled_tree_RSS_bytes','stop_reason','all_bindings_unchanged')}),flush=True)
    if launch_error is not None: raise launch_error
    if receipt['status'] != 'pass': raise RuntimeError('M-UNLOAD1 closed non-success; no retry, repair, extension, force or rollback')


if __name__ == '__main__': main()
