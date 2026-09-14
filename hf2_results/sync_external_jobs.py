"""Include external MATLAB and early kernel receipts in the common budget ledger."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
jobs=root/'hf2_results/resource_jobs'
jobs.mkdir(exist_ok=True)
for path in (root/'reference_validation/matlab').glob('*/process_record.json'):
    raw=json.loads(path.read_text(encoding='utf-8'))
    if 'wall_seconds' not in raw:
        continue
    record={k:v for k,v in raw.items() if k!='rss_samples'}
    record.update(name='matlab_'+path.parent.name,category='matlab_cshape' if path.parent.name.startswith('cshape') else 'small',
                  status='complete' if raw.get('returncode')==0 else 'failed',source_receipt=str(path))
    (jobs/('external_matlab_'+path.parent.name+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
path=root/'hf2_results/kernel_unit_tests.receipt.json'
if path.exists():
    record=json.loads(path.read_text(encoding='utf-8'))
    record.update(name='kernel_unit_tests_initial',category='small',wall_seconds=record['elapsed_seconds'],
                  status='complete' if record['exit_code']==0 else 'failed',source_receipt=str(path))
    (jobs/'external_kernel_initial.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
records=[json.loads(p.read_text(encoding='utf-8')) for p in jobs.glob('*.json')]
used=sum(r.get('wall_seconds',0) for r in records)
print(json.dumps({'completed_or_running_jobs':len(records),'recorded_numerical_seconds':used,
                  'remaining_total_seconds':3600-used},indent=2))
