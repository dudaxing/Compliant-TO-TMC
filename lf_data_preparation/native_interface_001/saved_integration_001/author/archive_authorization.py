"""Archive the direct M-INTEGRATE1 reply and prior actual publication proof."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT / 'lf_data_preparation/native_interface_001/saved_integration_001'
HEAD = '2b550d09f4347240ef6cb626b4c829566b638e61'
PROOF = Path('D:/hf-native-workpiece-api-author-20261012/MINTEGRATE1_preparation_001/publication_receipt.json')
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == HEAD
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
    proof, protocol = read(PROOF), read(STAGE / 'protocol.json')
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == HEAD
    assert proof['protocol_sha256'] == sha(STAGE / 'protocol.json')
    assert proof['source_and_restore_clean'] and proof['remote_main_confirmed_equal']
    assert protocol['card'] == 'M-INTEGRATE1' and len(protocol['installation']) == 11
    assert len(protocol['focused_test_selectors']) == 25 and len(protocol['bindings']) == 108
    assert all(sha(ROOT / name) == pin for name, pin in protocol['bindings'].items())
    for row in protocol['installation']:
        path = ROOT / row['target']
        assert (sha(path) if path.exists() else None) == row['previous_sha256']
    assert not (STAGE / 'run_001').exists() and not (STAGE / 'integration_launch.json').exists()
    assert not (STAGE / 'stop_requested.txt').exists()
    captured = datetime.now(timezone.utc).isoformat()
    question = ('是否批准按已推送 main 2b550d0 的 M-INTEGRATE1 卡执行？一次将已验证的续算候选安装到默认 hf_repo（11份文件：6旧改、5新），'
        '再运行唯一25项有限兼容测试，覆盖零起点、保存态、CLI、typed settings错误及旧参考来源迁移；真实测试仅16单元50DOF，'
        '不重做原夹持器路径、新HP或绘图。tests180／helper300／outer360秒（最多约6分钟）、采样8GiB；首错停，无重试、'
        '修复重跑、延期、force或自动回滚，保留实际已安装字节及测试部分结果。原力核、切线、门、结果与资格保持。'
        '卡及独立静审、发布／恢复核对已完成：lf_data_preparation/native_interface_001/saved_integration_001/M-INTEGRATE1_CARD.md。'
        '\n\n需要新批准的原因：M-RESUME1已闭卡，本次新增默认安装、测试范围和资源窗口，按此前约定不能续用旧授权。')
    answer = '批准按 M-INTEGRATE1 卡执行'
    reply = dict(card='M-INTEGRATE1', approved_source_commit=HEAD, captured_utc=captured,
        client_date='2026-10-12', client_timezone='Asia/Seoul', authorization_from_direct_human_reply=True,
        direct_human_answer=answer,
        questionItemId='["request_user_input_async","call_e31742769f9c49bda4a48588a7a0d497",0]',
        question=question, reply_context='Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction')
    author = STAGE / 'author'
    write_new(author / 'direct_human_reply.json', reply)
    with (author / 'source_publication_receipt.json').open('xb') as output:
        output.write(PROOF.read_bytes())
    value = dict(card='M-INTEGRATE1', authorized=True, authorization_from_direct_human_reply=True,
        approved_source_commit=HEAD, captured_utc=captured, direct_human_answer=answer,
        protocol_sha256=sha(STAGE / 'protocol.json'), human_evidence_sha256=sha(author / 'direct_human_reply.json'),
        source_publication_receipt_sha256=sha(author / 'source_publication_receipt.json'),
        focused_tests_seconds=180, helper_seconds=300, outer_seconds=360, sampled_RSS_bytes=8 * 1024**3,
        install_files=11, focused_test_instances=25, invocations_authorized=1, retries=0, force=False,
        automatic_rollback=False, original_gripper_or_HP_or_plots_authorized=False)
    write_new(author / 'authorization.json', value)
    print(json.dumps(dict(status='direct_authorization_archived_preflight_pass', card=value['card'],
        authorization_sha256=sha(author / 'authorization.json'), protocol_sha256=value['protocol_sha256']), ensure_ascii=False))


if __name__ == '__main__':
    main()
