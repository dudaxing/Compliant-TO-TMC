"""Read current ordinary progress and owned-process statistics, without payloads."""
from datetime import datetime
import json
from pathlib import Path
import psutil

STAGE=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_001')
read=lambda path:json.loads(path.read_bytes())
launch=read(STAGE/'step_launch.json')
rows=[]
progress=STAGE/'run_001/accepted_progress.jsonl'
if progress.is_file():
    data=progress.read_bytes()
    for line in data.splitlines(keepends=True):
        if line.endswith(b'\n'):rows.append(json.loads(line))
instances=[json.loads(line) for line in (STAGE/'step_instances.ndjson').read_bytes().splitlines() if line]
bound=[row for row in instances if row.get('event')=='instance_bound' and row.get('handle_kind')=='borrowed_root']
statistics=[]
if bound:
    pid=bound[0]['pid']
    try:
        process=psutil.Process(pid)
        for member in [process]+process.children(recursive=True):
            try:
                cpu=member.cpu_times()
                statistics.append(dict(pid=member.pid,status=member.status(),RSS_bytes=member.memory_info().rss,cpu_user_seconds=cpu.user,cpu_system_seconds=cpu.system))
            except psutil.NoSuchProcess:pass
    except psutil.NoSuchProcess:pass
keys=('index','d','R_input','q_out','minimum_J','relative_residual','newton_checks','bisection_depth','elapsed_seconds')
print(json.dumps(dict(status=launch['status'],elapsed_seconds=(datetime.now().astimezone()-datetime.fromisoformat(launch['started_utc'])).total_seconds(),
    accepted=[{k:row[k] for k in keys} for row in rows],live_owned_process_statistics=statistics,
    total_sampled_RSS_bytes=sum(row['RSS_bytes'] for row in statistics)),allow_nan=False))
