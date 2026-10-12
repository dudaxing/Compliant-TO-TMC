"""Capture the direct M-AREF1 reply without reading scientific NPZ bytes."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT / 'lf_data_preparation/native_interface_001/alpha_reference_001'
BASE = 'e687bdf1ca60edbd0fd044f4f8c990b3b9ccc182'
PROOF = Path('D:/hf-native-workpiece-api-author-20261012/MAREF1_preparation_001/source_publication_receipt.json')
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
    protocol, proof = read(STAGE / 'protocol.json'), read(PROOF)
    assert protocol['card'] == proof['prepared_card'] == 'M-AREF1'
    assert protocol['phases']['reference'] == dict(helper_seconds=900, outer_seconds=960)
    assert protocol['sampled_RSS_bytes'] == 8 * 1024**3
    assert protocol['expected_accepted_states'] == 2 and protocol['expected_new_HP_calls'] == 4
    assert protocol['original_target_indices'] == [13, 14] and protocol['targets_mm'] == [1.2, 1.15]
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['published_commit'] == BASE
    assert proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
    assert proof['source_and_restore_clean'] is proof['remote_main_confirmed_equal'] is True
    assert proof['protocol_sha256'] == sha(STAGE / 'protocol.json') == 'b373b2cedffff1f0b93ff6426645ab6507f2b7556e90c9068110ecf883b85673'
    assert proof['manifest_sha256'] == sha(ROOT / 'handoff/repository_manifest.json')
    for name in ('execute_alpha_reference.py', 'launch_reference.py', 'M-AREF1_CARD.md'):
        assert sha(STAGE / name) == protocol['bindings'][STAGE.relative_to(ROOT).as_posix() + '/' + name]
    for name in ('reference_launch.json', 'reference_stdout.log', 'run_001', 'stop_requested.txt',
                 'author/authorization.json', 'author/direct_human_reply.json', 'author/source_publication_receipt.json'):
        assert not (STAGE / name).exists()
    captured = datetime.now(timezone.utc).isoformat()
    question = ('是否批准按已推送 main e687bdf 的 M-AREF1 卡执行？仅读 alpha=5e−7 的原1.20／1.15 mm两个保存接受态，'
        '新增4次HP80／120，保留原十五门、完整单元／DOF、三力、PORT方向切线、CSC组装身份、KKT及工件合力核对。'
        '一次helper900／outer960秒（最多16分钟）、采样8GiB；首错停止，无重试、修复重跑、延期、force、新生产F／T／平衡求解、'
        '测试、API关联或绘图。只核这两态，不授完整原路径、压力或有效夹持资格。候选已通过两份独立静审、推送及异地恢复核对。'
        '完整卡：lf_data_preparation/native_interface_001/alpha_reference_001/M-AREF1_CARD.md。'
        '\n\n需要新批准的原因：M-INTEGRATE1已闭卡，本次新增独立HP范围和资源窗口；按您此前约定不能静默续用旧授权。')
    answer = '批准按 M-AREF1 卡执行'
    reply = dict(card='M-AREF1', approved_source_commit=BASE, captured_utc=captured,
        client_date='2026-10-12', client_timezone='Asia/Seoul', authorization_from_direct_human_reply=True,
        direct_human_answer=answer, questionItemId='["request_user_input_async","call_978ab98f2b244bdfb12c8eb1a21d5086",0]',
        question=question, reply_context='Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction')
    author = STAGE / 'author'
    write_new(author / 'direct_human_reply.json', reply)
    with (author / 'source_publication_receipt.json').open('xb') as output:
        output.write(PROOF.read_bytes())
    authorization = dict(card='M-AREF1', authorized=True, authorization_from_direct_human_reply=True,
        approved_source_commit=BASE, captured_utc=captured, direct_human_answer=answer,
        protocol_sha256=sha(STAGE / 'protocol.json'), human_evidence_sha256=sha(author / 'direct_human_reply.json'),
        source_publication_receipt_sha256=sha(author / 'source_publication_receipt.json'),
        helper_seconds=900, outer_seconds=960, sampled_RSS_bytes=8 * 1024**3,
        accepted_states_authorized=2, HP_calls_authorized=4, invocations_authorized=1,
        retries=0, repair_rerun=False, extension=False, force=False,
        production_F_T_solver_tests_API_association_plots_authorized=False)
    write_new(author / 'authorization.json', authorization)
    print(json.dumps(dict(status='direct_authorization_archived', card='M-AREF1',
        authorization_sha256=sha(author / 'authorization.json'), protocol_sha256=authorization['protocol_sha256'],
        scientific_NPZ_byte_reads=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
