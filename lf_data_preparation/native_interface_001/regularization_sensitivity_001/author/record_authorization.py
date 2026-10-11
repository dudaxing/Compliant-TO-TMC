"""Record the actual direct human approval received for published M-ALPHA1."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/regularization_sensitivity_001'
SOURCE = '64a19f7d990d294d09f16145eae946e0edfa1580'
EXT = Path(__file__).resolve().parent
PUBLICATION = EXT.parent/'MSTAB1_preparation_001/publication_receipt.json'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == SOURCE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
protocol = read(STAGE/'protocol.json')
assert protocol['card'] == 'M-ALPHA1' and sha(STAGE/'protocol.json') == '430137c7e81cb12281937a6201519235fcc161de0503323684541c1c72b94d11'
assert not protocol['authorized'] and not protocol['executed']
assert not (STAGE/'run_001').exists() and not (STAGE/'production_launch.json').exists()
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
publication = read(PUBLICATION)
assert publication['status'] == 'published_and_incrementally_restored_pass' and publication['published_commit'] == SOURCE
assert publication['source_and_restore_clean'] and publication['remote_main_confirmed_equal']
assert not publication['authorized'] and not publication['executed']
evidence = dict(schema_version='direct-human-M-ALPHA1-reply-1.0',card='M-ALPHA1',
    authorization_from_direct_human_reply=True, direct_human_answer='批准按 M-ALPHA1 卡执行',
    approved_source_commit=SOURCE,recorded_utc=datetime.now(timezone.utc).isoformat(),
    question_item_id='["request_user_input_async","call_147bca9ced0c4c89be3282ff627217f6",0]',
    reply_context='Actual user send_user_message_question_reply after preparation/static reviews/main publication and independent restoration. It explicitly approves one M-ALPHA1 alpha-only 15-target prefix and saved-state views, controller9000/helper9600/outer9660 seconds, sampled8GiB, original gates, no repair rerun/extension/force/newHP.',
    question='是否批准按已推送 main 64a19f7 的 M-ALPHA1 卡执行？仅将 α 从 1e−6 降至 5e−7，保持其余物理条件，从零执行原15目标至1.20 mm并回撤至1.15 mm，生成实际变形、力和参数对照图。一次 controller9000秒／helper9600秒／outer9660秒（约2小时41分钟）、采样8GiB；保持原生产门，首个终端错误停止，无修复重跑、延期、force或新HP。候选已通过独立静审、推送及恢复核对。需要新批准的原因：M-BOUND1窗口已关闭，不覆盖本次新非线性路径、显示和资源额度。')

def write_new(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

write_new(STAGE/'author/direct_human_reply.json',evidence)
authorization = dict(schema_version='M-ALPHA1-actual-authorization-1.0',card='M-ALPHA1',authorized=True,
    authorization_from_direct_human_reply=True,direct_human_answer=evidence['direct_human_answer'],
    approved_source_commit=SOURCE,protocol_sha256=sha(STAGE/'protocol.json'),
    human_evidence_sha256=sha(STAGE/'author/direct_human_reply.json'),
    controller_seconds=9000,helper_seconds=9600,outer_seconds=9660,sampled_RSS_bytes=8*1024**3,
    invocations_allowed=1,source_publication_receipt_sha256=sha(PUBLICATION),
    qualification_scope='Production/saved-state sensitivity only; no new independent HP, stability, pressure, clamp or HF5 qualification')
write_new(STAGE/'author/authorization.json',authorization)
archive = STAGE/'author/M_ALPHA1_source_publication_receipt.json'
with archive.open('xb') as stream:
    stream.write(PUBLICATION.read_bytes())
write_new(EXT/'authorization_recording_receipt.json',dict(status='actual_direct_human_authorization_recorded_before_unique_launch',
    source_commit=SOURCE,protocol_sha256=authorization['protocol_sha256'],
    authorization_sha256=sha(STAGE/'author/authorization.json'),human_evidence_sha256=authorization['human_evidence_sha256'],
    source_publication_receipt_sha256=sha(archive),candidate_runs=0,new_scientific_actions=0))
print(json.dumps(dict(status='actual_M_ALPHA1_authorization_recorded',source_commit=SOURCE,bindings_checked=len(protocol['bindings']))))
