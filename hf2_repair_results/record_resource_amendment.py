"""Record a prospective bounded continuation allowance, without changing scientific gates."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path(__file__).resolve().parents[1]
out = root/'hf2_repair_results/resource_amendment_001.json'
assert not out.exists()
spec = root/'hf_repo/validation/hf2_repair/precision_spec.json'
failure = root/'hf2_repair_results/full_precision_audit_001/validation_failure.json'
rows = [json.loads(x) for x in (failure.parent/'state_progress.jsonl').read_text().splitlines()]
assert len(rows) == 299 and rows[-1]['side'] == 'matlab' and rows[-1]['source_index'] == 98
monitor = root/'hf2_repair_results/run_budgeted.py'
baseline = root/'hf2_repair_results/baseline/run_budgeted_pre_amendment.py'
assert not baseline.exists()
baseline.write_bytes(monitor.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
record = dict(schema_version='hf2-resource-amendment-1.0', created_utc=datetime.now(timezone.utc).isoformat(),
    original_precision_spec_sha256=sha(spec), original_postprocess_cumulative_seconds=600,
    amended_postprocess_cumulative_seconds=720, continuation_process_seconds=120,
    total_numerical_seconds=3000, small_cumulative_seconds=1200, corrected_python_path_attempts=1,
    continuation_job_name='full_precision_audit_resume',
    reason='The initial offline audit stopped at its internal 590-second guard after 299 of 300 states. Complete the missing historical state and recover the last ten MATLAB raw arrays in a bounded continuation; no nonlinear solve is repeated.',
    scope='Prospective resource scheduling amendment under the authorized HF2 repair. Original 600-second sub-budget was insufficient; retain its failure. Scientific tolerances, input bytes, total 3000-second budget, and one full nonlinear attempt remain unchanged.',
    cache_strategy='Reuse 290 archived state arrays; recover crosschecks from archived exact Decimal strings; recompute MATLAB indices 90..99 and compare the nine previously evaluated rows exactly except timing.',
    preserved_failure=dict(path=str(failure.relative_to(root)), sha256=sha(failure)),
    preserved_monitor=dict(path=str(baseline.relative_to(root)), sha256=sha(baseline)))
out.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False, indent=2))
