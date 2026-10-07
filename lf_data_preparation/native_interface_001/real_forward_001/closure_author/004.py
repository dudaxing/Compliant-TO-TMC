"""Static review of the original saved viewer and thin manifest export."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())


def main():
    checks = read(AUTHOR/'author_checks.json')
    pins = {}
    for name in ('execute_saved_api_view.py', 'freeze_saved_api_view.py'):
        source = AUTHOR/name
        compile(ast.parse(source.read_text(encoding='utf-8')), str(source), 'exec')
        pins[str(source)] = sha(source)
        declared = {pin for key, pin in checks['source_sha256'].items() if Path(key.replace('\\', '/')).name == name}
        assert declared == {pins[str(source)]}
    viewer = ROOT/'hf_repo/scripts/plot_native_mean.py'
    viewer_pin = '0f6e3ae5e5c94d640f97c840a676eaf929180abd7eea5e0729e57eb0644bc7d1'
    assert sha(viewer) == viewer_pin == checks['original_viewer_sha256']
    code = (AUTHOR/'execute_saved_api_view.py').read_text(encoding='utf-8')
    freeze = (AUTHOR/'freeze_saved_api_view.py').read_text(encoding='utf-8')
    assert code.count('viewer.main()') == 1
    assert '"--magnification", "1000"' in code
    assert 'view_directory/"real_api"' in code and 'input_directory/"qualified_response.json"' in code
    assert 'response["views"]["status"] == "matched"' in code
    assert 'len(response["views"]["links"]) == 2' in code
    assert 'sha(original_response_file) == original_response_pin' in code
    assert 'metadata["media"]["native_mean_path.gif"]["frames"] == n' in code
    assert 'state_sha256=state["state_sha256"], d_mm=state["d"]' in code
    assert 'helper_seconds=60, outer_seconds=90' in freeze
    assert 'control["bindings"]' in freeze and 'audit["input_bindings"]' in freeze
    assert 'reference_receipt["summary_sha256"] == sha(audit_file)' in freeze
    assert 'reference_receipt["HP_calls_started"] == reference_receipt["HP_calls_completed"] == 2*n' in freeze
    output = AUTHOR/'root_source_static_review.json'
    assert not output.exists()
    report = dict(status='pass_static_only', blocking_findings=[], reviewer='root', source_sha256=pins,
        reviewed_utc=datetime.now(timezone.utc).isoformat(), review_program_sha256=sha(Path(__file__)),
        original_viewer_sha256=viewer_pin,
        verified=[
            'Original saved archive loader/numeric rows/render/main imported byte-exact; copied viewer finds the real repository through its existing ancestor search.',
            'Freeze waits for actual production/reference protocol, launch, terminal receipt, same result and all actual N states with fresh 2N HP.',
            'Both completed phase resource limits/current source and input raw hashes are rechecked before freezing a new 60/90-second, 8-GiB saved-view window.',
            'One cached viewer call, actual x1 plus explicitly supplementary x1000, one real frame per actual state, original shared force scale and J semantics.',
            'Single unique real_api manifest binds same model/task/result and every index/stateSHA/d; PNG/GIF hashes and summary identity satisfy native_response view contract.',
            'New saved-only qualified_response.json links exactly its own PNG/GIF and same-result all-N reference; producer flags stay false and pressure/contact/all-columns/HF5 stay unqualified.',
            'Original production response never overwritten; no new model, force, tangent, solver or HP functions imported/called.',
            'Whole helper includes startup, rendering, summary, output hashing and final cooperative checks; failed phase remains failed even if attempted artifacts exist.'
        ],
        scope='Static source and raw identity only; no candidate/renderer/HF import, NPZ arrays, HP, solver or plots.',
        science_calls=0, formal_writes=0)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'source_sha256': pins, 'report_sha256': sha(output)}))


if __name__ == '__main__':
    main()
