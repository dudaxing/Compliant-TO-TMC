"""Archive a reviewable unexecuted proposal; do not invoke its builder."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json

root=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
author=Path(__file__).resolve().parent/'reference_v2_author'
target=root/'docs/evidence/native_batch_reference_v2_proposal_001'
assert not target.exists()
assert not (root/'lf_data_preparation/native_interface_001/batch_reference_v2_001').exists()
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:sha256(p.read_bytes()).hexdigest()
reviews=[read(author/name) for name in ('root_review.json','peer_review.json')]
for review in reviews:
    assert review['status']=='pass_static_only' and not review['blocking_findings']
    assert all(sha(author/name)==pin for name,pin in review['source_sha256'].items())
files=['audit_batch_case.py','reference_case_builder.py','README.md','author_note.json','author_checks.json',
    'source_additions.diff','load_diagnosis.json','load_diagnosis.md','root_review.json','peer_review.json',
    'write_root_review.py','B-REF2_CARD.md']
target.mkdir(parents=True)
for name in files:(target/name).write_bytes((author/name).read_bytes())
record=dict(schema_version='native-batch-reference-v2-proposal-1.0',status='reviewed_pending_execution_authorization',
    created_utc=datetime.now(timezone.utc).isoformat(),card='B-REF2',files={name:sha(target/name) for name in files},
    activity=dict(candidate_imports=0,builder_calls=0,card_freezes=0,NPZ_loads=0,HP=0,F=0,T=0,solver=0,renders=0),
    resource_proposal=dict(canonical={'helper_seconds':240,'outer_seconds':270},native_fine={'helper_seconds':900,'outer_seconds':960},sampled_RSS_bytes=8*1024**3),
    qualification='No new numerical qualification; old V1 closed NOT_PASS and complete production PASS retained.')
(target/'proposal_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for file,link in [(root/'README.md','docs/evidence/native_batch_reference_v2_proposal_001/B-REF2_CARD.md'),
                  (root/'docs/CURRENT_STATUS.md','evidence/native_batch_reference_v2_proposal_001/B-REF2_CARD.md'),
                  (root/'docs/RESUME_DEVELOPMENT.md','evidence/native_batch_reference_v2_proposal_001/B-REF2_CARD.md')]:
    old=file.read_bytes()
    note=f'B-REF2 更新：最小V2候选已完成作者、root与独立静审，尚未制卡、导入或执行；[具体新卡与源码]({link})待新授权。原生产PASS、V1参考失败HP0及未生成批量图的状态保持。\n\n'
    file.write_bytes(note.encode('utf-8')+old)
(target/'archive_reference_v2_proposal.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'status':record['status'],'files':len(files),'card':str(target/'B-REF2_CARD.md')}))
