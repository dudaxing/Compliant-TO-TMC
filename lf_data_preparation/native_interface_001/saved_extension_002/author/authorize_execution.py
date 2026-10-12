"""Record actual M-EXTEND2 direct approval without importing HF or reading scientific inputs."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
STAGE = ROOT / 'lf_data_preparation/native_interface_001/saved_extension_002'
APPROVED = '781f408cce5704817ebb67f2defcafc047af3820'
PROTOCOL = '30b5e7f28b3c2987b984bfab10d432f6666faf757fd20377a47e3f716f76cfe6'
QUESTION = '''是否批准按已推送并恢复核对的 main 781f408 的 M-EXTEND2 卡执行？只修订短测试目录与证据封存，保持原物理条件、36项测试、七份核心候选及验收门；一次测试→从成功末态延伸1.15→1.10 mm→原viewer生成3PNG／实际N帧GIF→原字节ZIP封存→全部PASS才安装六份生产入口。tests180／controller1800／viewer600／helper3000／outer3060秒（最多51分钟），采样8GiB；首错停止后续科学／显示／安装，仅原窗口仍开放时允许一次部分证据封存。无重试、修复重跑、延期、force、新HP、删除或自动回滚。原M-EXTEND1 NOT_PASS与祖先NOT_PASS保留，不升级完整路径、压力或有效夹持资格。完整卡：lf_data_preparation/native_interface_001/saved_extension_002/M-EXTEND2_CARD.md。

需要新批准的原因：M-EXTEND1已闭卡；按此前约定，本次修改包装及封存范围不能沿用旧授权。'''


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == APPROVED
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
    assert sha(STAGE / 'protocol.json') == PROTOCOL and not (STAGE / 'run_001').exists()
    proof_file = HERE / 'source_publication_receipt.json'
    proof = json.loads(proof_file.read_bytes())
    assert proof['published_commit'] == APPROVED and proof['status'] == 'published_and_incrementally_restored_pass'
    assert proof['prepared_card'] == 'M-EXTEND2' and proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    saved_proof = STAGE / 'author/M_EXTEND2_source_publication_receipt.json'
    with saved_proof.open('xb') as output:
        output.write(proof_file.read_bytes())
    reply = dict(card='M-EXTEND2', approved_source_commit=APPROVED, authorization_from_direct_human_reply=True,
        direct_human_answer='批准按 M-EXTEND2 卡执行',
        reply_context=dict(questionItemId=['request_user_input_async', 'call_179049de1ad443e490b9e78502f69f65', 0],
            received_message_type='send_user_message_question_reply', approved_question=QUESTION),
        recorded_utc=datetime.now(timezone.utc).isoformat())
    reply_file = STAGE / 'author/direct_human_reply.json'
    new(reply_file, reply)
    authorization = dict(card='M-EXTEND2', authorized=True, approved_source_commit=APPROVED,
        authorization_from_direct_human_reply=True, direct_human_answer=reply['direct_human_answer'],
        human_evidence_sha256=sha(reply_file), source_publication_receipt_sha256=sha(saved_proof),
        protocol_sha256=PROTOCOL, recorded_utc=datetime.now(timezone.utc).isoformat(),
        execution_window='One continuous launcher invocation, exact frozen card only; closes at first terminal non-success or success.',
        no_retry_repair_rerun_extension_force_or_rollback=True)
    new(STAGE / 'author/authorization.json', authorization)
    print(json.dumps(dict(status='actual_direct_human_approval_recorded', card='M-EXTEND2', approved_source_commit=APPROVED,
        protocol_sha256=PROTOCOL, HF_collect_tests_science_arrays_media_reads=0)))


if __name__ == '__main__':
    main()
