"""Record the actual direct human reply; no science or candidate changes."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
STAGE = ROOT / 'lf_data_preparation/native_interface_001/extension_reference_001'
COMMIT = '8438c55f267246b91d6b320273ecb10665f3e16f'
PROTOCOL_SHA = 'ed835ffd724ad82c3a8870fd05326baf784814fcb16e9f938a6559ad1d8e7135'
ANSWER = '批准按 M-EREF1 卡执行'
QUESTION = '''是否批准按已推送并恢复核对的 main 8438c55 的 M-EREF1 卡执行？仅核新1.10 mm保存态（child1／global15），新增2次HP80／120，保持原十五门、全13440单元／27378DOF、三力及同一PORT方向切线、CSC／KKT和工件合力检查；通过后一次读取新普通摘要生成参考误差PNG／JSON，并允许一次像素检查。helper900秒／outer960秒（最多16分钟）、采样8GiB；首错停，无重试、修复重跑、延期、force、新生产F／T、平衡求解、测试、API关联或安装。只核这一态，不升级整段参考、压力或有效夹持资格。卡：lf_data_preparation/native_interface_001/extension_reference_001/M-EREF1_CARD.md。

需要新批准的原因：M-EXTEND2已闭卡，本次增加独立参考、绘图及资源窗口；按此前阶段约定不能续用旧授权。'''


def dump_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == COMMIT
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
    protocol = (STAGE / 'protocol.json').read_bytes()
    assert sha256(protocol).hexdigest() == PROTOCOL_SHA
    proof_raw = (HERE / 'source_publication_receipt.json').read_bytes()
    proof = json.loads(proof_raw)
    assert proof['status'] == 'published_and_incrementally_restored_pass'
    assert proof['published_commit'] == COMMIT and proof['protocol_sha256'] == PROTOCOL_SHA
    assert proof['prepared_card'] == 'M-EREF1' and proof['prepared'] is True
    assert proof['authorized'] is proof['executed'] is False
    for name in ('run_001', 'reference_launch.json', 'reference_stdout.log', 'stop_requested.txt'):
        assert not (STAGE / name).exists()
    paths = {name: STAGE / 'author' / name for name in ('source_publication_receipt.json', 'direct_human_reply.json', 'authorization.json')}
    assert all(not path.exists() for path in paths.values())
    stamp = datetime.now(timezone.utc).isoformat()
    reply = dict(card='M-EREF1', authorization_from_direct_human_reply=True,
        approved_source_commit=COMMIT, direct_human_answer=ANSWER, recorded_utc=stamp,
        reply_context=dict(source='actual_user_send_user_message_question_reply',
            questionItemId=['request_user_input_async', 'call_b5447721f9fc4f2db02cd5d22d629e03', 0],
            question=QUESTION, answer=ANSWER),
        automatic_goal_continuation_not_used_as_approval=True)
    with paths['source_publication_receipt.json'].open('xb') as stream:
        stream.write(proof_raw)
    dump_new(paths['direct_human_reply.json'], reply)
    authorization = dict(card='M-EREF1', authorized=True, authorization_from_direct_human_reply=True,
        approved_source_commit=COMMIT, protocol_sha256=PROTOCOL_SHA, direct_human_answer=ANSWER,
        helper_seconds=900, outer_seconds=960, sampled_RSS_bytes=8*1024**3,
        human_evidence_sha256=sha256(paths['direct_human_reply.json'].read_bytes()).hexdigest(),
        source_publication_receipt_sha256=sha256(proof_raw).hexdigest(), recorded_utc=stamp,
        accepted_states=1, selected_child_accepted_index=1, original_target_index=15,
        target_mm=1.1, new_HP_calls=2, new_reference_observation_plots=1,
        postrun_new_PNG_pixel_QA_maximum=1, production_F_T_solver_tests_API_install=0,
        no_retry_repair_extension_force=True, full_child_path_reference_pass=False,
        full_original_path_reference_pass=False, full_extended_path_reference_pass=False,
        pressure_or_effective_grip_qualification=False)
    dump_new(paths['authorization.json'], authorization)
    print(json.dumps(dict(status='actual_human_authorization_recorded', card='M-EREF1',
        approved_source_commit=COMMIT, files=3, science_execution=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
