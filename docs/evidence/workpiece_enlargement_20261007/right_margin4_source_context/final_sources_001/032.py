"""Align external reference metadata with the actual production source, without imports or execution."""
import ast
import copy
import difflib
import json
from hashlib import sha256
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
BASE = ROOT/'lf_data_preparation/native_workpiece_001/right_margin_cycle_001/reference_author'
OUT = Path(__file__).resolve().parent/'reference_candidate'
PRODUCTION = Path(__file__).resolve().parent/'production_candidate/build_right_margin_production.py'
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
write = lambda p,v: p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

audit_file, builder_file = [OUT/n for n in ('audit_enlarged_square.py','reference_contract_builder.py')]
a, b = [p.read_text(encoding='utf-8') for p in (audit_file,builder_file)]
assert a.count('"right_medium_domain_margin"') == 2 and b.count('"right_medium_domain_margin"') == 2
a = a.replace('"right_medium_domain_margin"','"right_medium_domain_margin2_to4mm"')
b = b.replace('"right_medium_domain_margin"','"right_medium_domain_margin2_to4mm"')
assert b.count('"right-margin4-cycle-source-freeze-1.0"') == 1
b = b.replace('"right-margin4-cycle-source-freeze-1.0"','"right-margin-cycle-source-freeze-1.0"')
previous_audit_sha = sha(audit_file)
audit_file.write_text(a,encoding='utf-8',newline='\n')
assert b.count('AUDIT_PIN = "'+previous_audit_sha+'"') == 1
b = b.replace('AUDIT_PIN = "'+previous_audit_sha+'"','AUDIT_PIN = "'+sha(audit_file)+'"')
builder_file.write_text(b,encoding='utf-8',newline='\n')
template = OUT/'template'; template.mkdir(exist_ok=False)
for name in ('audit_enlarged_square.py','reference_contract_builder.py'):
    (template/name).write_bytes((BASE/name).read_bytes())

def methods(source):
    return {n.name:n for c in ast.parse(source).body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef)}
old_a,old_b = [(BASE/n).read_text(encoding='utf-8') for n in ('audit_enlarged_square.py','reference_contract_builder.py')]
om,nm = methods(old_a),methods(a)
unchanged = sorted(om.keys()-{'load','run'})
for name in unchanged: assert ast.dump(om[name],include_attributes=False) == ast.dump(nm[name],include_attributes=False)
class RemoveSummaryMetadata(ast.NodeTransformer):
    def visit_Call(self,node):
        node = self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id == 'dict':
            node.keywords = [k for k in node.keywords if k.arg not in {'alias','qualification','parameter_case'}]
        return node
assert ast.dump(RemoveSummaryMetadata().visit(copy.deepcopy(om['run'])),include_attributes=False) == ast.dump(RemoveSummaryMetadata().visit(copy.deepcopy(nm['run'])),include_attributes=False)
functions = lambda s:{n.name:n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
assert ast.dump(functions(old_b)['verify_accounting_transition'],include_attributes=False) == ast.dump(functions(b)['verify_accounting_transition'],include_attributes=False)
for path in (audit_file,builder_file): compile(ast.parse(path.read_text(encoding='utf-8')),str(path),'exec')
for name in ('core_audit_mechanical.py','counter_attempts.py','counter_original_B028.py'): assert sha(OUT/name) == sha(BASE/name)
production_source = PRODUCTION.read_text(encoding='utf-8')
assert 'schema_version="right-margin-cycle-source-freeze-1.0"' in production_source
assert 'parameter_case="right_medium_domain_margin2_to4mm"' in production_source
assert 'alias="gripper_coarse_square_x71_side18_right_margin4"' in production_source
assert 'BASELINE = "3305fe0c3a640bf22e0f89ea4386a41bdef96aa4"' in production_source
assert '6806' not in a+b and '6356' not in a+b
diff = ''.join(difflib.unified_diff(old_a.splitlines(keepends=True),a.splitlines(keepends=True),fromfile='right_margin_cycle_001/reference_author/audit_enlarged_square.py',tofile='right_margin4_cycle_001/reference_author/audit_enlarged_square.py'))
diff += ''.join(difflib.unified_diff(old_b.splitlines(keepends=True),b.splitlines(keepends=True),fromfile='right_margin_cycle_001/reference_author/reference_contract_builder.py',tofile='right_margin4_cycle_001/reference_author/reference_contract_builder.py'))
(OUT/'source_delta.diff').write_text(diff,encoding='utf-8',newline='\n')
note = read(OUT/'author_note.json')
assert all(sha(ROOT/path)==pin for path,pin in note['raw_math_pins'].items())
note['future_schema_assumptions']['production_source_freeze'] = 'right-margin-cycle-source-freeze-1.0'
note['future_schema_assumptions']['model_comparison_parameter_case'] = 'right_medium_domain_margin2_to4mm'
note['schema_alignment'] = dict(source_file=str(PRODUCTION),source_sha256=sha(PRODUCTION),root_confirmed=True,
    production_source_freeze='right-margin-cycle-source-freeze-1.0',parameter_case='right_medium_domain_margin2_to4mm',
    scope='Source metadata alignment only; no future preparation or production result exists or is qualified.')
note['protected_AST'].pop('run_exact_after_only_alias_qualification_removed')
note['protected_AST']['run_exact_after_only_alias_qualification_parameter_case_removed'] = True
note['template_copy_pins'] = {p.name:sha(p) for p in template.iterdir()}
note['source_finalizer_sha256'] = sha(Path(__file__))
readme = (OUT/'README.md').read_text(encoding='utf-8')
readme += '\nProduction source alignment retains generic right-margin-cycle-source-freeze-1.0 and declares parameter_case right_medium_domain_margin2_to4mm. The reference contract/protocol have separate right-margin4 identities. The two original source templates are preserved as raw bytes in template/. Run changes only alias, qualification and parameter_case summary values; every calculation and all-state HP loop remains exact.\n'
(OUT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
checks = dict(schema_version='margin4-reference-source-author-checks-1.0',status='pass_static_source_only',
    unchanged_nonLOAD_methods=unchanged,run_AST_exact_except_summary_keys=['alias','qualification','parameter_case'],
    all_actualN_HPloop_exact=True,accounting_transition_verifier_AST_exact=True,
    three_private_math_files_raw_exact=True,six_math_and_B52_raw_exact=True,
    actual_production_source_schema_alias_parameter_case_baseline_match=True,
    expected_dimensions_only=dict(cells=3360,nodes=3485,dofs=6970,fixed=452,free=6518),
    no_future_SHA_or_actualN_fabricated=True,activity=note['activity'],finalizer_sha256=sha(Path(__file__)),
    source_pins={p.name:sha(p) for p in (audit_file,builder_file,OUT/'source_delta.diff',OUT/'README.md')})
write(OUT/'source_author_checks.json',checks)
note['candidate_pins'] = {p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name != 'author_note.json'}
write(OUT/'author_note.json',note)
print(json.dumps(dict(status=checks['status'],pins={p.name:sha(p) for p in OUT.iterdir() if p.is_file()})))
