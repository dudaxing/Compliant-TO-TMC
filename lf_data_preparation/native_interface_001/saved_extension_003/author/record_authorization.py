"""Record the actual M-UNLOAD1 approval; no scientific operation."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
STAGE = ROOT / 'lf_data_preparation/native_interface_001/saved_extension_003'
COMMIT = '3cf11e92bedb791855c7b01d314668eba1116ac6'
PROTOCOL_SHA = '4980f164fdeface2839d6c0371d36a2ce4d310097d84d3991c2ba4266bc6ef5b'
ANSWER = '批准按 M-UNLOAD1 卡执行'
QUESTION = '''是否批准按已推送并恢复核对的 main 3cf11e9 的 M-UNLOAD1 卡执行？默认API单次从成功1.10 mm末态延伸到1.05 mm；仅追加此绝对目标，原16路径前缀、物理条件、设置及验收门保持。完成后原pure viewer一次生成3PNG／实际N帧变形GIF，最多对三个新PNG各一次像素检查。controller1800／viewer600／helper2700／outer2760秒（最多46分钟），采样8GiB；首错停，无修复重跑、重试、延期、force、HP、测试、候选复制、安装、回滚或删除。原内部回溯／bisection允许，保真实partial和原失败历史；不升级完整路径、压力或有效夹持资格。卡：lf_data_preparation/native_interface_001/saved_extension_003/M-UNLOAD1_CARD.md。

需要新批准的原因：M-EREF1已闭卡且仅覆盖独立参考；本次新增平衡路径、实际显示和资源窗口，按此前阶段约定不能沿用旧授权。'''


def dump_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == COMMIT
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)
    assert sha256((STAGE/'protocol.json').read_bytes()).hexdigest() == PROTOCOL_SHA
    proof_raw = (HERE/'source_publication_receipt.json').read_bytes()
    proof = json.loads(proof_raw)
    assert proof['status'] == 'published_and_incrementally_restored_pass'
    assert proof['published_commit'] == COMMIT and proof['protocol_sha256'] == PROTOCOL_SHA
    assert proof['prepared_card'] == 'M-UNLOAD1' and proof['prepared'] is True
    assert proof['authorized'] is proof['executed'] is False
    for name in ('run_001','production_launch.json','production_stdout.log','stop_requested.txt'):
        assert not (STAGE/name).exists()
    paths = {name:STAGE/'author'/name for name in ('source_publication_receipt.json','direct_human_reply.json','authorization.json')}
    assert all(not path.exists() for path in paths.values())
    stamp = datetime.now(timezone.utc).isoformat()
    reply = dict(card='M-UNLOAD1',authorization_from_direct_human_reply=True,
        approved_source_commit=COMMIT,direct_human_answer=ANSWER,recorded_utc=stamp,
        reply_context=dict(source='actual_user_send_user_message_question_reply',
            questionItemId=['request_user_input_async','call_363eb1e73c52474c92957b00b40af02a',0],
            question=QUESTION,answer=ANSWER),automatic_goal_continuation_not_used_as_approval=True)
    with paths['source_publication_receipt.json'].open('xb') as stream: stream.write(proof_raw)
    dump_new(paths['direct_human_reply.json'],reply)
    auth = dict(card='M-UNLOAD1',authorized=True,authorization_from_direct_human_reply=True,
        approved_source_commit=COMMIT,protocol_sha256=PROTOCOL_SHA,direct_human_answer=ANSWER,
        controller_seconds=1800,viewer_seconds=600,helper_seconds=2700,outer_seconds=2760,sampled_RSS_bytes=8*1024**3,
        human_evidence_sha256=sha256(paths['direct_human_reply.json'].read_bytes()).hexdigest(),
        source_publication_receipt_sha256=sha256(proof_raw).hexdigest(),recorded_utc=stamp,
        selected_state_index=1,original_target_indices=[15,16],targets_mm=[1.1,1.05],
        expected_API_calls=1,expected_accepted_states_minimum=2,expected_new_PNGs=3,
        actual_N_GIF_frames=True,postrun_new_PNG_pixel_QA_maximum=3,new_GIF_postrun_decode=0,
        tests_candidate_copies_installations_HP=0,no_retry_repair_extension_force_rollback_delete=True,
        full_original_path_completed=False,full_extended_path_completed=False,
        pressure_or_effective_grip_qualification=False)
    dump_new(paths['authorization.json'],auth)
    print(json.dumps(dict(status='actual_human_authorization_recorded',card='M-UNLOAD1',
        approved_source_commit=COMMIT,files=3,science_execution=0),ensure_ascii=False))


if __name__ == '__main__': main()
