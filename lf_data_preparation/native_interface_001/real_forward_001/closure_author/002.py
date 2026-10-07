"""Record root's source review; only AST, JSON, bytes and Git are read."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())


def main():
    checks = read(AUTHOR/'author_checks.json')
    pins = {}
    for name in ('execute_real_api.py', 'install_real_api_card.py'):
        source = AUTHOR/name
        compile(ast.parse(source.read_text(encoding='utf-8')), str(source), 'exec')
        pins[str(source)] = sha(source)
        assert pins[str(source)] == checks['source_sha256'][name]
    worker = (AUTHOR/'execute_real_api.py').read_text(encoding='utf-8')
    installer = (AUTHOR/'install_real_api_card.py').read_text(encoding='utf-8')
    assert worker.count('response = native_evaluate.evaluate_native(') == 1
    assert 'callback(measured)' in worker and 'prefix.append(row)' in worker
    assert worker.index('callback(measured)') < worker.index('prefix.append(row)')
    assert 'raise RuntimeError(receipt["stop_reason"])' in worker
    assert 'assert type(value) is original' in worker
    assert 'assert not writing' in worker
    assert 'metadata["call_counts"]' in worker
    assert 'response["views"]["status"] == "not_provided"' in worker
    assert 'response["views"]["manifest"] is None and not response["views"]["links"]' in worker
    assert 'helper_seconds=180, outer_seconds=210' in installer
    assert 'sampled_RSS_bytes=8*1024**3' in installer
    assert 'assert not stage.exists()' in installer
    assert 'pass_static_only' in installer and 'blocking_findings' in installer
    assert 'dict(sources, **inputs)' in installer
    assert 'if native_result is not None:' in worker
    assert 'call_counts=dict(native_result.metadata["call_counts"])' in worker
    assert 'receipt.update(call_counts=None, accepted_states=None, task_target_executed=None)' in worker
    functional = read(ROOT/'lf_data_preparation/native_interface_001/api_validation_001/functional_protocol.json')
    closure = {name: pin for name, pin in functional['bindings'].items() if name.startswith('hf_repo/src/')}
    assert len(closure) == 27 and all(sha(ROOT/name) == pin for name, pin in closure.items())
    head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    assert head == '8330b821af1f9ab58bdd9f51c85eb2e7d3cdcb37'
    assert subprocess.check_output(['git', '-C', str(ROOT), 'branch', '--show-current'], text=True).strip() == 'main'
    launch = ROOT/'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/launch_pose.py'
    assert sha(launch) == 'f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477'
    inventory = read(ROOT/'lf_data_preparation/native_mean_001/input_inventory.json')
    task = read(ROOT/inventory['case']['task_file'])
    assert task['input']['target_mm'] == .001 and task['workpiece'] is None and 'path' not in task
    assert inventory['case']['targets_mm'] == [0., .001]
    assert inventory['settings']['time_limit_seconds'] == 180.
    report = dict(status='pass_static_only', blocking_findings=[], reviewer='root',
        created_utc=datetime.now(timezone.utc).isoformat(), baseline_commit=head,
        source_sha256=pins, review_program_sha256=sha(Path(__file__)),
        reviewed_checks=[
            'One real API invocation from unrelated cwd with explicit repository root.',
            'Real constructor returns original type; builder/controller/solve/write/format delegates preserve arguments.',
            'Original cache capture precedes existing scalar-only accepted prefix observation.',
            'Real complete/full F/T counts are started/completed; cached writing forbids additional F/T.',
            'Success gates retain original task, targets, settings, counts, production residual/J/constraint/balance/fixed gates.',
            'Default views use not_provided/manifest null/empty links; no dict truthiness gate.',
            'Actual NativeMeanResult counts are retained on terminal failures; unavailable results remain null.',
            'RuntimeError cooperative stops escape controller; no rerun, repair, force or extra HP.',
            'Whole helper 180 seconds, F3 outer 210 seconds and sampled 8 GiB include hashing; controller clock separately scoped.',
            'Installer requires fresh stage and exact separate root/peer reviewed worker+installer hashes.',
            'All 27 active product source bytes and raw F3 launcher are unchanged.',
            'Historical result/state/reference used only for cost/input context, no qualification inheritance.'
        ],
        scope='Static source review only. No worker/installer execution, HF import, NPZ numeric reading, model, F/T, solver, HP or visualization.',
        science_calls=0, formal_writes=0)
    output = AUTHOR/'root_source_static_review.json'
    assert not output.exists()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'source_sha256': pins, 'report_sha256': sha(output)}))


if __name__ == '__main__':
    main()
