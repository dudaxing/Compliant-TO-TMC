"""Clarify the client-local completion date in new ordinary closure documents."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_unload_003'
date = '2026-10-20'
closure_file = STAGE/'author/closure.json'
closure = json.loads(closure_file.read_bytes())
assert closure['card'] == 'L-CTIPUNLOAD3' and closure['execution_closed']
assert 'report_client_local_date' not in closure
assert not (STAGE/'author/CLIENT_DATE_CLARIFICATION.json').exists()
history = json.loads((STAGE/'author/front_history.json').read_bytes())
changed = []
for row in history['files']:
    path = ROOT/row['path']
    raw = path.read_bytes()
    prefix, old = raw[:row['prefix_bytes']], raw[row['prefix_bytes']:]
    assert prefix.startswith(b'> 2026-10-19 L-CTIPUNLOAD3 ')
    assert sha256(old).hexdigest() == row['old_sha256'] and raw.count(old) == 1
    revised = prefix.replace(b'> 2026-10-19 ', b'> 2026-10-20 ', 1)+old
    assert len(revised) == len(raw)
    changed.append((path, revised))
results = STAGE/'RESULTS.md'
text = results.read_text(encoding='utf-8')
assert text.count('2026-10-19；执行 **') == 1
text = text.replace('2026-10-19；执行 **', date+'；执行 **', 1)
closure['report_client_local_date'] = date
closure['report_timezone'] = 'Asia/Seoul'
closure['date_clarification'] = 'Completion report uses the client-local date. Prepared card/source paths retain historical20261019 identities; original UTC receipts and sealed run outputs are unchanged.'
for path, raw in changed:
    path.write_bytes(raw)
results.write_text(text, encoding='utf-8', newline='\n')
closure_file.write_text(json.dumps(closure, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')
record = dict(status='pass_ordinary_client_date_clarification', created_utc=datetime.now(timezone.utc).isoformat(), report_client_local_date=date, report_timezone='Asia/Seoul', revised_new_front_prefixes=len(changed), original_front_suffixes_preserved=True, original_UTC_receipts_unchanged=True, sealed_run_outputs_unchanged=True, scientific_or_media_payload_reads=0)
(STAGE/'author/CLIENT_DATE_CLARIFICATION.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
(STAGE/'author/finalize_client_date.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(record, ensure_ascii=False))
