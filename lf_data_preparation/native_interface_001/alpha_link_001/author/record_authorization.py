"""Record the current human M-ALINK1 approval; no API or science imports."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/alpha_link_001'
PROOF = Path('D:/hf-native-workpiece-api-author-20261012/MALINK1_preparation_001/source_publication_receipt.json')
COMMIT = '1e639641625b4d0f92eb84aff4b4c6fdb05d0171'
PROTOCOL_SHA = '6da47ef3a8236eb6b7687478d5c89b44242753cfd52044825742162a104cdde7'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == COMMIT
assert sha(STAGE/'protocol.json') == PROTOCOL_SHA
proof = json.loads(PROOF.read_bytes())
assert proof['published_commit'] == COMMIT and proof['status'] == 'published_and_incrementally_restored_pass'
assert proof['prepared_card'] == 'M-ALINK1' and proof['authorized'] is proof['executed'] is False
for name in ('authorization.json','direct_human_reply.json','source_publication_receipt.json'):
    assert not (STAGE/'author'/name).exists()
for name in ('run_001','link_launch.json','link_stdout.log','stop_requested.txt'):
    assert not (STAGE/name).exists()

reply = dict(card='M-ALINK1', authorization_from_direct_human_reply=True,
    approved_source_commit=COMMIT, direct_human_answer='批准按 M-ALINK1 卡执行',
    questionItemId='["request_user_input_async","call_OgDxBp2RYpQUinSTGoTuN4mV",0]',
    question='是否批准按已推送 main 1e63964 的 M-ALINK1 卡执行？复用现有摘要 API，将 alpha=5e−7 的原1.20／1.15 mm两态、已有4次HP参考和原3PNG／两帧GIF关联到新响应与轻索引；摘要、响应写入、索引写入各一次，30份文件绑定保持。一次helper180秒／outer240秒、采样8GiB，首错停止，无重试、修复重跑、延期或force；不新增NPZ／科学gzip读取、F／T、HP、平衡求解、测试或绘图。保留原结果、父路径NOT_PASS及完整原任务未完成的状态，不升级压力或有效夹持资格。卡与两份独立静审、发布／恢复核对均已完成：lf_data_preparation/native_interface_001/alpha_link_001/M-ALINK1_CARD.md。\n\n需要新批准的原因：M-AREF1已关闭且明确不覆盖API关联；按您此前约定，本次新增范围和资源窗口不能沿用旧授权。',
    reply_context='Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction',
    recorded_utc=datetime.now(timezone.utc).isoformat())
write(STAGE/'author/direct_human_reply.json', reply)
with (STAGE/'author/source_publication_receipt.json').open('xb') as output:
    output.write(PROOF.read_bytes())
auth = dict(card='M-ALINK1', authorized=True, authorization_from_direct_human_reply=True,
    approved_source_commit=COMMIT, direct_human_answer=reply['direct_human_answer'],
    protocol_sha256=PROTOCOL_SHA, human_evidence_sha256=sha(STAGE/'author/direct_human_reply.json'),
    source_publication_receipt_sha256=sha(STAGE/'author/source_publication_receipt.json'),
    helper_seconds=180, outer_seconds=240, sampled_RSS_bytes=8*1024**3,
    invocations_authorized=1, retries=0, force=False,
    authorization_scope='Only the exact prepared M-ALINK1 API association card; no new mechanics, archive reads, tests or plots',
    recorded_utc=datetime.now(timezone.utc).isoformat())
write(STAGE/'author/authorization.json', auth)
print(json.dumps(dict(status='actual_direct_human_approval_recorded', card='M-ALINK1',
    source_commit=COMMIT, protocol_sha256=PROTOCOL_SHA, API_calls=0, science_calls=0)))
