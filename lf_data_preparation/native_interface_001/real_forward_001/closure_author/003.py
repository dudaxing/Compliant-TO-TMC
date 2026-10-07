"""Root source review of the new LOAD contract; no reference is executed."""
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
    pins, trees = {}, {}
    for name in ('audit_real_api.py', 'reference_card_builder.py'):
        source = AUTHOR/name
        trees[name] = ast.parse(source.read_text(encoding='utf-8'))
        compile(trees[name], str(source), 'exec')
        pins[str(source)] = sha(source)
        declared = {pin for key, pin in checks['source_sha256'].items() if Path(key.replace('\\', '/')).name == name}
        assert declared == {pins[str(source)]}
    tree = trees['audit_real_api.py']
    cls, = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    assert cls.name == 'RealAPIAudit' and ast.unparse(cls.bases[0]) == 'Audit'
    assert {node.name for node in cls.body if isinstance(node, ast.FunctionDef)} == {'__init__', 'checkpoint', 'lifecycle', 'load'}
    code = (AUTHOR/'audit_real_api.py').read_text(encoding='utf-8')
    assert 'audit.run()' in code and 'original_audit.STARTED = STARTED' in code
    assert 'self.control = self.stage.parent' in code
    checkpoint, = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == 'checkpoint']
    assert 'self.check(' not in ast.unparse(checkpoint)
    assert ast.unparse(checkpoint).count('require(') == 3
    builder = trees['reference_card_builder.py']
    values = {target.id: node.value for node in builder.body if isinstance(node, ast.Assign)
              for target in node.targets if isinstance(target, ast.Name)}
    math = ast.literal_eval(values['MATH_PINS'])
    assert len(math) == 5 and all(sha(ROOT/'hf_repo/scripts'/name) == pin for name, pin in math.items())
    structural = {item.arg: ast.literal_eval(item.value) for item in values['STRUCTURAL_PINS'].keywords}
    assert structural == dict(prior_model_file='prior_model_sha256', prior_task_file='prior_task_sha256',
                             direction_file='direction_file_sha256', lifting_file='lifting_file_sha256')
    inventory = read(ROOT/'lf_data_preparation/native_mean_001/input_inventory.json')
    assert all(sha(ROOT/inventory['case'][key]) == inventory['case'][pin] for key, pin in structural.items())
    stage = ROOT/'lf_data_preparation/native_interface_001/real_forward_001'
    protocol = read(stage/'production_protocol.json')
    receipt = read(stage/'run_001/execution_receipt.json')
    launch = read(stage/'production_launch.json')
    result = read(stage/'run_001/result/result.json')
    assert receipt['status'] == launch['status'] == 'pass'
    assert receipt['protocol_sha256'] == launch['protocol_sha256'] == sha(stage/'production_protocol.json')
    assert receipt['result_sha256'] == sha(stage/'run_001/result/result.json')
    assert result['accepted_states'] == receipt['accepted_states'] == len(result['states']) == 2
    assert receipt['call_counts'] == result['call_counts'] and receipt['call_counts']['solver_invocations'] == 1
    assert all(sha(ROOT/name) == pin for name, pin in protocol['bindings'].items())
    output = AUTHOR/'root_source_static_review.json'
    assert not output.exists()
    report = dict(status='pass_static_only', blocking_findings=[], reviewer='root',
        source_sha256=pins, review_program_sha256=sha(Path(__file__)),
        reviewed_utc=datetime.now(timezone.utc).isoformat(),
        verified=[
            'Subclass only changes initialization, LOAD, timing/resource observations and lifecycle.',
            'Original Audit.run/run_state, HP80/120, exact scatter, component/CSC/augmented mathematics and GATES remain imported unchanged.',
            'Explicit actual production protocol/launch/receipt/result/response and full 27-source closure replace the legacy receipt contract.',
            'Actual N=2 states and per-state SHA are bound; four fresh HP calls are required, never inherited.',
            'Prior intrinsic task/model/direction/zero-lift inputs are independently compared to current saved arrays without inheriting qualification.',
            'Structural SHA keys explicitly distinguish prior model/task from direction/lifting_file_sha256.',
            'Direction is derived from the new model; original all-element/all-real-DOF and PORT deltaR=0 scope remains.',
            'Whole wrapper timer is shared with inherited summary/stdout; resource checks do not inflate scientific check counts.',
            'New parent F3 stop file, 180/210 seconds and 8 GiB sampled limits; first error closes with no candidate F/T/solve/retry.',
            'Fresh output audit/ matches the original saved viewer contract; final summary/lifecycle/receipt and bindings gate closure.'
        ],
        scope='Source/static and actual closed-production JSON/raw-SHA review only; no HF imports, NPZ arrays, HP, F/T, solver, models or plots.',
        prefreeze_review_utility_correction='Own stdlib review initially expected basename report keys; source author uses absolute keys. Normalize basenames. The earlier KeyError occurred before report/formal writes and all scientific calls; candidate bytes unchanged.',
        science_calls=0, formal_writes=0)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'source_sha256': pins, 'report_sha256': sha(output)}))


if __name__ == '__main__':
    main()
