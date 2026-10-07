"""Record actual closed production and the running reference; no response work."""
from hashlib import sha256
from pathlib import Path
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
BASE = 'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/'
PROGRESS = ROOT/'docs/evidence/workpiece_enlargement_20261007/right_margin_progress.json'
CTX = PROGRESS.parent/'right_margin_source_context'
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
sha = lambda p:sha256(p.read_bytes()).hexdigest()

def main():
    proof = read(ROOT/BASE/'production_launch.json')
    receipt = read(ROOT/BASE/'run_001/execution_receipt.json')
    assert proof['status'] == receipt['status'] == 'pass'
    binding_names = set(read(ROOT/BASE/'reference_protocol.json')['bindings'])
    docs = ['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md']
    assert not set(docs)&binding_names
    history = CTX/'source_phase_progress_snapshot.json'
    assert not history.exists()
    history.write_bytes(PROGRESS.read_bytes())
    progress = read(PROGRESS)
    progress.update(status='production_complete_reference_running',source_phase_progress_snapshot_sha256=sha(history),
        completed_production=dict(receipt=receipt,launch=proof),
        reference=dict(status='running_not_qualified',stage=BASE+'reference',helper_seconds=1500,outer_seconds=1560,
            expected_new_HP_calls=48,actual_states=24,protocol_sha256=sha(ROOT/BASE/'reference_protocol.json')),
        next='Complete the one fresh all-state reference; only then freeze saved-response views',
        qualification='Complete production passed; fresh independent reference and response visualization remain pending')
    PROGRESS.write_text(json.dumps(progress,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    for name in docs:
        path = ROOT/name
        raw = path.read_bytes()
        banner,suffix = raw.split(b'\n\n',1)
        assert banner.startswith('> 当前执行状态：'.encode('utf-8'))
        (CTX/(name.replace('/','__')+'.construction_banner.txt')).write_bytes(banner+b'\n\n')
        new = '> 当前执行状态：右侧2mm介质域完整24目标夹持—卸载路径通过并返回零位移；新48次全态高精度参考正在1500/1560秒8GiB预算下执行，尚未取得本次完整独立资格。构造、模型映射及未变形图已通过；当前记录见right_margin_progress.json与WORKPIECE_ENLARGEMENT_20261007.md。下方为此前已交付的γ敏感性状态。\n\n'
        path.write_bytes(new.encode('utf-8')+suffix)
    (CTX/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(status=progress['status'],progress_sha256=sha(PROGRESS))))

if __name__ == '__main__':main()
