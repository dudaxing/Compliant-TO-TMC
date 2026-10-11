"""Record the actual direct human M-RESUME1 approval; stdlib only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_interface_001/saved_continuation_001'
EXT = Path(__file__).resolve().parent
COMMIT = '8b456dcdc2c0566fb2e927175a781712dd5e78ec'
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())


def new_json(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == COMMIT
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
    assert not (STAGE/'run_001').exists() and not (STAGE/'production_launch.json').exists()
    assert not (STAGE/'stop_requested.txt').exists()
    protocol_file = STAGE/'protocol.json'
    protocol = read(protocol_file)
    assert protocol['card'] == 'M-RESUME1' and protocol['authorized'] is False and protocol['executed'] is False
    assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
    proof = read(EXT/'publication_receipt.json')
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == COMMIT
    assert proof['prepared_card'] == 'M-RESUME1' and proof['authorized'] is False and proof['executed'] is False
    evidence = {
        'questionItemId':'["request_user_input_async","call_87f0127abeeb440a8952daa5d92af4a5",0]',
        'question':'是否批准按已推送 main 8b456dc 的 M-RESUME1 卡执行？先运行唯一5项局部测试，再从原 alpha=5e−7 保存态013复核峰值，沿原绝对目标1.20→1.15 mm执行首次下降；原物理任务、设置（新clock除外）及验收门保持。一次 tests120／controller1800／viewer600／helper2700／outer2760秒（最多约46分钟）、采样8GiB。成功后原纯viewer生成3PNG和N帧实际变形GIF；typed失败保存实际部分态后停止。无重试、修复重跑、延期、force或新HP，原M-ALPHA1 NOT_PASS不修改。卡、候选独立静审及发布／恢复核对已完成：lf_data_preparation/native_interface_001/saved_continuation_001/M-RESUME1_CARD.md。',
        'answer':'批准按 M-RESUME1 卡执行'}
    reply = dict(card='M-RESUME1',approved_source_commit=COMMIT,
        authorization_from_direct_human_reply=True,direct_human_answer=evidence['answer'],
        reply_context='Actual newest human send_user_message_question_reply matching the published M-RESUME1 card; not the goal auto-continuation',
        raw_question_reply=[evidence],recorded_utc=datetime.now(timezone.utc).isoformat())
    new_json(STAGE/'author/direct_human_reply.json',reply)
    proof_path = STAGE/'author/M_RESUME1_source_publication_receipt.json'
    with proof_path.open('xb') as stream:
        stream.write((EXT/'publication_receipt.json').read_bytes())
    authorization = dict(card='M-RESUME1',authorized=True,executed=False,approved_source_commit=COMMIT,
        authorization_from_direct_human_reply=True,direct_human_answer=evidence['answer'],
        human_evidence_sha256=sha(STAGE/'author/direct_human_reply.json'),
        source_publication_receipt_sha256=sha(proof_path),protocol_sha256=sha(protocol_file),
        binding_count=len(protocol['bindings']),recorded_utc=datetime.now(timezone.utc).isoformat(),
        limits=dict(tests_seconds=120,controller_seconds=1800,viewer_seconds=600,helper_seconds=2700,
            outer_seconds=2760,sampled_RSS_bytes=8*1024**3),
        scope='One focused test group, one saved-peak original absolute suffix, one cached pure view only on production success',
        retries=0,extensions=0,force=False,new_HP=False,parent_NOT_PASS_preserved=True)
    new_json(STAGE/'author/authorization.json',authorization)
    print(json.dumps(dict(status='direct_human_authorization_recorded_no_science_started',
        approved_source_commit=COMMIT,protocol_sha256=sha(protocol_file),binding_count=len(protocol['bindings']))))


if __name__ == '__main__':
    main()
