"""Close the pre-child CreateProcess failure using its observed tool receipt."""
from pathlib import Path
import json

folder = Path(__file__).resolve().parent/'resource_jobs'
path = folder/'full_precision_audit_resume_f9e2d6ad.json'
record = json.loads(path.read_text())
assert record['status'] == 'running'
assert (folder/record['log']).stat().st_size == 0
assert not (folder.parent/'full_precision_audit_resumed_001').exists()
record.update(status='launch_failed', returncode=1, stop_reason='launch_error',
    process_started=False, wall_seconds=3.8126554, sampled_peak_tree_rss_bytes=0, memory_samples=0,
    exception_type='FileNotFoundError', windows_error=2,
    message='subprocess.Popen/CreateProcess could not locate the relative executable; no child was created.',
    timing_method='Conservative accounting using the exec_command reported wall_time_seconds 3.8126554; the runner did not finalize its timer after Popen raised.',
    correction='Use an absolute executable path; preserve this pre-child launch failure in the resource ledger.')
path.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
(folder/record['log']).write_text('FileNotFoundError: [WinError 2] raised by subprocess.Popen/CreateProcess before a child process was created. See the JSON receipt for the observed launch command and conservative timing.\n', encoding='utf-8')
print(json.dumps(record, indent=2))
