"""Preserve prepared saved-view sources, with unmet runtime prerequisites explicit."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json

root=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
outside=Path(__file__).resolve().parent
author=outside/'view_v2_author'
target=root/'docs/evidence/native_batch_saved_view_v2_candidate_001'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
assert not target.exists()
assert not (root/'lf_data_preparation/native_interface_001/batch_reference_v2_001').exists()
for name in ('root_review.json','peer_review.json'):
    report=read(author/name)
    assert report['status']=='pass_static_only' and not report['blocking_findings'] and not report['execution_ready']
    assert all(sha(author/file)==pin for file,pin in report['source_sha256'].items())
files=['execute_batch_view.py','cached_view_adapter.py','README.md','author_checks.json','worker_v1_to_v2.diff',
    'numerical_rows_original_excerpt.py','numerical_rows_adaptation.diff','render_original_excerpt.py',
    'render_adaptation.diff','root_review.json','peer_review.json','write_root_review.py']
target.mkdir(parents=True)
for name in files:(target/name).write_bytes((author/name).read_bytes())
for name,source in [
    ('prior_execute_batch_view.py',outside/'view_author/execute_batch_view.py'),
    ('prior_view_peer_review.json',outside/'view_author/peer_review.json'),
    ('v2_response_contract_review.json',outside/'review/v2_response_contract_review.json')]:
    (target/name).write_bytes(source.read_bytes());files.append(name)
record=dict(schema_version='native-batch-saved-view-v2-candidate-1.0',status='source_ready_reference_prerequisites_missing',
    created_utc=datetime.now(timezone.utc).isoformat(),files={name:sha(target/name) for name in files},
    production_stage='lf_data_preparation/native_interface_001/batch_forward_001',
    intended_reference_run='lf_data_preparation/native_interface_001/batch_reference_v2_001/run_001',
    execution_ready=False,freeze_allowed=False,view_protocol_created=False,execution_authorization='None granted by this source archive',
    activity=dict(candidate_imports=0,NPZ_loads=0,HF_imports=0,HP=0,F=0,T=0,solver=0,renders=0,card_freezes=0),
    purpose='Prepare actual saved-state views after fresh V2 references; keep immutable production and numerical mathematics.',
    effect='Explicit new reference paths and V2 receipts prevent reusing the closed failed V1 card; generic response provider/consumer schema is compatible in source.',
    remaining='Both actual fresh V2 references and a separately frozen saved-view card are required; no future numerical or rendering PASS.')
(target/'candidate_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
status=root/'docs/CURRENT_STATUS.md'
old=status.read_bytes();before=sha(status)
note=('视图准备更新：已将保存态视图候选适配至独立V2参考目录，作者/root/独立静审通过，'
    '通用响应接口字段交叉核对通过；绘图数学和3/5节点逻辑不变。'
    '[候选及审查](evidence/native_batch_saved_view_v2_candidate_001/README.md)仅源准备，'
    '两例新参考仍缺，未制视图卡、导入、加载数组、绘图或赋新资格；B-REF2确认仍待收到。\n\n')
status.write_bytes(note.encode('utf-8')+old)
install=dict(status='candidate_archived_only',current_status_before=before,current_status_after=sha(status),science_calls=0)
(target/'archive_install.json').write_text(json.dumps(install,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(target/'archive_view_v2_candidate.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'status':record['status'],'files':len(files),'execution_ready':False,'science_calls':0}))
