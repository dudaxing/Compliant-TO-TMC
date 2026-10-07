"""Install reviewed thin batch sources and freeze one mock-only functional card."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'lf_data_preparation/native_interface_001/batch_validation_001'
BASE = '7e54e34d82b5a98191c6d777f0fc85942f03eee7'
sha = lambda p: sha256(p.read_bytes()).hexdigest()
dump = lambda p, x: p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    review = json.loads((AUTHOR/'review/batch_static_review.json').read_bytes())
    assert review['status'] == 'pass_static_only' and review['blocking_findings'] == []
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip() == BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT).strip()
    installs = {
        'candidate/native_batch.py': 'hf_repo/src/hf_eval/native_batch.py',
        'candidate/evaluate_native_batch.py': 'hf_repo/scripts/evaluate_native_batch.py',
        'review/test_native_batch.py': 'hf_repo/tests/test_native_batch.py',
    }
    selected = list(installs) + [
        'candidate/README.md','candidate/author_note.json','candidate/author_checks.json',
        'candidate/source_additions.diff','candidate/review_delta.diff','review/source_boundary_review.json',
        'review/source_boundary_review.md','review/test_author_checks.json',
        'review/batch_static_review.json','reference_facts/batch_reference_facts.json',
        'reference_facts/batch_reference_facts.md','execute_batch_tests.py',
        'install_batch_functional.py',
    ]
    for source in installs:
        assert sha(AUTHOR/source) == review['source_sha256'][source]
        assert not (ROOT/installs[source]).exists()
    assert sha(AUTHOR/'execute_batch_tests.py') == review['source_sha256']['execute_batch_tests.py']
    data = {name:(AUTHOR/name).read_bytes() for name in selected}
    stage = ROOT/STAGE
    assert not stage.exists()
    stage.mkdir()
    context = stage/'author'
    context.mkdir()
    rows = []
    for i,(source,raw) in enumerate(data.items(),1):
        target = context/(f'{i:03}'+Path(source).suffix)
        target.write_bytes(raw)
        rows.append(dict(file=target.name,source=source,sha256=sha(target)))
    dump(context/'INDEX.json',rows)
    for source,destination in installs.items():
        (ROOT/destination).write_bytes(data[source])
    worker = stage/'execute_batch_tests.py'
    worker.write_bytes(data['execute_batch_tests.py'])
    launch = stage/'launch_pose.py'
    launch.write_bytes((ROOT/'lf_data_preparation/native_interface_001/real_forward_001/launch_pose.py').read_bytes())
    prior = json.loads((ROOT/'lf_data_preparation/native_interface_001/real_forward_001/production_protocol.json').read_bytes())
    names = [name for name in prior['bindings'] if name.startswith('hf_repo/src/hf_eval/')]
    names += list(installs.values()) + [
        'lf_data_preparation/native_interface_001/api_validation_001/author/execute_interface_tests.py',
        'lf_data_preparation/native_mean_001/task.json',
        'lf_data_preparation/v2_adapter_001/converted/gripper_canonical/geometry.json',
        STAGE+'/execute_batch_tests.py', STAGE+'/launch_pose.py',
    ]
    protocol = dict(schema_version='native-batch-functional-protocol-1.0',baseline_commit=BASE,
        bindings={name:sha(ROOT/name) for name in names},sampled_RSS_bytes=8*1024**3,
        expected_tests=15,test_file='hf_repo/tests/test_native_batch.py',
        expected_mock_transport_calls=dict(evaluate_started=10,evaluate_returned=8,evaluate_escaped=2),
        guard_file='lf_data_preparation/native_interface_001/api_validation_001/author/execute_interface_tests.py',
        output_directory=STAGE+'/run_001',
        phases={'functional':dict(helper_seconds=120,outer_seconds=150,
            argv=[STAGE+'/execute_batch_tests.py','--repo','.', '--protocol',STAGE+'/functional_protocol.json'])},
        scope='Mock-only batch contracts; no new force/tangent/model/solver/HP/NPZ/plot or HF5 qualification',
        stop='First error stops; no retry, force or old-card extension',created_utc=datetime.now(timezone.utc).isoformat())
    dump(stage/'functional_protocol.json',protocol)
    dump(stage/'installation_receipt.json',dict(status='installed_not_executed',baseline_commit=BASE,
        source_review_sha256=sha(AUTHOR/'review/batch_static_review.json'),
        protocol_sha256=sha(stage/'functional_protocol.json'),installed_sources=installs,
        author_files=rows,new_scientific_calls=0))
    print(json.dumps(dict(status='installed_not_executed',stage=STAGE,
        bindings=len(protocol['bindings']),protocol_sha256=sha(stage/'functional_protocol.json'))))


if __name__ == '__main__':
    main()
