"""Record the actual direct human M-AVIEW1 reply; no scientific execution."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'functional_views/native_alpha_partial_20261011/complete_001'
APPROVED = '7887aa1138f8e46a2b15f47a1060aa7d72cfe651'
PROOF = Path('D:/hf-native-workpiece-api-author-20261009/MAVIEW1_preparation_001/publication_receipt.json')
sha = lambda path: sha256(path.read_bytes()).hexdigest()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == APPROVED
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
assert not (STAGE/'run_001').exists() and not (STAGE/'view_launch.json').exists()
protocol = json.loads((STAGE/'protocol.json').read_bytes())
assert protocol['card'] == 'M-AVIEW1' and not protocol['authorized'] and not protocol['executed']
assert sha(STAGE/'protocol.json') == 'ad3d238a30aa46e02e6102c4fc215a584d2b28a71f05283ae0f2e9b2e5b9336b'
proof = json.loads(PROOF.read_bytes())
assert proof['status'] == 'published_and_incrementally_restored_pass'
assert proof['published_commit'] == APPROVED and proof['prepared_card'] == 'M-AVIEW1'
assert proof['authorized'] is False and proof['executed'] is False
question = '是否批准按已推送 main 7887aa1 的 M-AVIEW1 卡执行？仅读原 α=5e−7 的14个接受加载态：29个既存NPZ／279字段，geometry/nodal各14次；与旧α的14个共同目标对照，输出6PNG／14帧GIF及0.85、1.20 mm快照。helper180秒／outer240秒、采样8GiB，首错停止，无重试、延期、force或新F/T/HP/平衡求解。原M-ALPHA1 NOT_PASS与未完成卸载保持。卡、独立静审及发布／恢复核对均已完成：functional_views/native_alpha_partial_20261011/complete_001/M-AVIEW1_CARD.md。\n需要新批准的原因：M-ALPHA1已按首错规则闭卡，本卡新增保存态观察、绘图及独立资源窗口，不能续用旧授权。'
answer = '批准按 M-AVIEW1 卡执行'
reply = dict(card='M-AVIEW1',approved_source_commit=APPROVED,
    authorization_from_direct_human_reply=True,direct_human_answer=answer,
    reply_context=dict(questionItemId='["request_user_input_async","call_FMuXPaMBTX0vBPRpnuP5NgGJ",0]',
        question=question,answer=answer),recorded_utc=datetime.now(timezone.utc).isoformat(),
    timestamp_meaning='Record creation time; no human message timestamp inferred')


def write(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


author = STAGE/'author'
with (author/'M_AVIEW1_source_publication_receipt.json').open('xb') as stream:
    stream.write(PROOF.read_bytes())
write(author/'direct_human_reply.json',reply)
auth = dict(card='M-AVIEW1',authorized=True,approved_source_commit=APPROVED,
    authorization_from_direct_human_reply=True,direct_human_answer=answer,
    protocol_sha256=sha(STAGE/'protocol.json'),human_evidence_sha256=sha(author/'direct_human_reply.json'),
    source_publication_receipt_sha256=sha(author/'M_AVIEW1_source_publication_receipt.json'),
    helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=8589934592,
    scope='One saved14-state pure view, common14target comparison and GIF snapshots; original NOT_PASS preserved',
    first_terminal_error_stops=True,retries=0,extension=False,force=False,
    new_F_T_HP_model_equilibrium_calls=0,recorded_utc=datetime.now(timezone.utc).isoformat())
write(author/'authorization.json',auth)
print(json.dumps(dict(card='M-AVIEW1',authorized=True,approved_source_commit=APPROVED,
    protocol_sha256=auth['protocol_sha256'],human_evidence_sha256=auth['human_evidence_sha256']),ensure_ascii=False))
