"""Independent stdlib-only literal-source and closed-JSON review; no HF imports."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT = Path('D:/hf-margin4-author-20261007/interface_notes')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

expected = {
    'HF5_USABLE_INTERFACE_FACTS_AND_MINIMUM_PROPOSAL.md': '5c2d65de2edcb296d8634193ff1c4e61d8787a281357a4cab17c9fcadba005a0',
    'source_facts.json': 'cb799d7383476eca305a03b92a4b6467d3e8698da0edc4b7d31cefe1c7ab46f5',
    'author_note.json': 'de610ba04149539f92eb0ff9344877356b5adeb7b88edbb370a826f5a7bc71d9',
}
for name, digest in expected.items():
    assert sha(OUT / name) == digest, name
facts = read(OUT / 'source_facts.json')
pins, trees = {}, {}
for relative, evidence in facts['source_and_closed_JSON_evidence'].items():
    path = ROOT / relative
    actual = sha(path)
    assert actual == evidence['sha256'], relative
    row = {'sha256': actual, 'raw_identity_matches': True}
    if path.suffix == '.py':
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        trees[relative] = tree
        located = {(node.name, node.lineno) for node in ast.walk(tree)
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        for name, line in evidence.get('functions', {}).items():
            assert (name, line) in located, (relative, name, line)
        row['advertised_function_lines_match'] = True
    pins[relative] = row

def function(relative, name):
    return next(n for n in trees[relative].body if isinstance(n, ast.FunctionDef) and n.name == name)

def named_calls(fn):
    return [n.func.id for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]

mean = 'hf_repo/src/hf_eval/native_mean.py'
solve = function(mean, 'solve_native_mean')
writer = function(mean, 'write_native_mean')
assert named_calls(solve).count('build_native_project') == 1
assert named_calls(writer).count('write_native_project') == 1
assert not {'solve_native_mean', 'build_native_project', 'solve_split_displacement_path',
            '_assemble_force', '_assemble_mechanical_force', '_tangent', '_tangent_chunked'} & set(named_calls(writer))
assert 'initial_guess' in [x.arg for x in solve.args.kwonlyargs]
forward = next(n for n in ast.walk(solve) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == 'solve_split_displacement_path')
assert any(k.arg == 'initial_guess' and isinstance(k.value, ast.Name) and k.value.id == 'initial_guess'
           for k in forward.keywords)
cli = trees['hf_repo/scripts/solve_native_mean.py']
cli_options = [n.value for n in ast.walk(cli) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith('--')]
assert '--initial-guess' not in cli_options
assert not any('initial_guess' in n.value or 'initial-guess' in n.value for n in ast.walk(cli)
               if isinstance(n, ast.Constant) and isinstance(n.value, str))

closed = {}
for label, result_relative, summary_relative, n, hp in [
    ('fine_no_workpiece_025', 'lf_data_preparation/native_fine_task_025_001/result/result.json',
     'lf_data_preparation/native_fine_task_025_001/audit/summary.json', 4, 8),
    ('right_margin2', 'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/run_001/result/result.json',
     'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/reference/summary.json', 24, 48),
]:
    result, reference = read(ROOT / result_relative), read(ROOT / summary_relative)
    assert result['status'] == 'success' and reference['status'] == 'pass'
    assert reference['result_sha256'] == sha(ROOT / result_relative)
    assert result['accepted_states'] == len(result['states']) == reference['accepted_states'] == len(reference['states']) == n
    assert reference['HP_calls_completed'] == hp
    for original, checked in zip(result['states'], reference['states']):
        assert original['state_sha256'] == checked['state_sha256'] and checked['status'] == 'pass'
    assert result['independent_HP_qualified'] is False and result['equilibrium_qualified'] is False and result['HF_qualified'] is False
    closed[label] = {'accepted_states': n, 'HP_calls_completed': hp, 'same_result_and_all_state_JSON_identity': True,
                     'result_sha256': sha(ROOT / result_relative), 'reference_sha256': sha(ROOT / summary_relative),
                     'scope': 'Previously closed JSON-only evidence; no new HP archive or scientific qualification.'}

report = {
    'schema_version': 'hf5-interface-literal-source-peer-review-1.0',
    'status': 'pass_literal_source_and_closed_JSON_only',
    'generated_utc': datetime.now(timezone.utc).isoformat(),
    'reviewed_author_files': expected,
    'actual_source_and_closed_JSON_pins': pins,
    'literal_findings': [
        'LF v2 converter preserves native four masks but limits the domain/origin/thickness and physical inverter/gripper profiles; source background is provenance.',
        'Native data/grid mapping uses geometry origin, cell sizes and shape. Region endpoints require exact grid coincidence to binary64 tolerance; ports use normalized reference arclength trapezoid weights.',
        'Native model task selects native geometry, explicit material/regularization/background and limited direction/support profiles; native entry does not accept a task h that changes the stored grid.',
        'Existing .5 mm test source and closed 4-state no-workpiece reference support native fine construction/path only; they do not prove same-design refinement or fine contact/clamping.',
        'solve_native_mean constructs once before the controller. port_projection is an existing API option forwarded to the controller; solve_native_mean CLI has no matching option and therefore uses default tangent.',
        'write_native_mean calls the model writer and serializes accepted cached state/force/tangent/matrix. It performs no force, tangent or equilibrium reevaluation.',
        'Settings/input/task/geometry/constructor validation can raise before returned controller partial result; mechanical controller failure and pre-result setup failure must remain distinct.',
        'Production qualification flags remain false. The closed JSON reference binds the same result and all accepted state identities; no new reference computation is implied.',
        'plot_native_mean is restricted to old 1.0 schema and gripper [0,.001] TEST. The square saved-view source selects a unique physical (80,30) reference tip; it is not an arbitrary-geometry viewer.',
        'CLI module imports are located relative to __file__, while input/output relative paths remain cwd-based. Descriptor archives are same-directory paths; repo-root path normalization is a future interface proposal.',
    ],
    'closed_JSON_identity_checks': closed,
    'proposal_scope': 'evaluate_native, compact response/manifest, CLI option and repo-relative normalization are unimplemented proposals; no HF optimizer or historical 30-case card is implemented or invoked.',
    'caveats': ['Literal source and previously closed JSON identities only; no runtime/API/test or scientific validation of proposed HF5 interface.',
                '4 mm running scientific output not read or qualified.',
                'Signed weak fixed-body force and its mirror magnitude sum do not establish pressure or free-body hard contact; saved binary64 Green/gap observation does not inherit HP strain/pressure qualification.'],
    'blocking_findings': [],
    'activity': {'HF_imports': 0, 'candidate_imports_or_execution': 0, 'NPZ_array_reads': 0,
                 'constructors': 0, 'F_T_solver_HP': 0, 'geometry_nodal_plot': 0, 'tests_executed': 0,
                 'formal_writes': 0, 'cards_or_implementation': 0},
}
target = OUT / 'source_facts_peer_review.json'
target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'report': str(target), 'report_sha256': sha(target),
                  'identity_records': len(pins), 'closed_cases': closed}, ensure_ascii=False))
