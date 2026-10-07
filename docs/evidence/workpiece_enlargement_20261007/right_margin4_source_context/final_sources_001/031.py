"""Pre-freeze source-only correction of saved mapping report fields."""
import ast
import copy
import difflib
import json
from hashlib import sha256
from pathlib import Path

OUT = Path(__file__).resolve().parent/'reference_candidate'
PREP = Path(__file__).resolve().parent/'preparation_candidate/prepare_margin4.py'
sha = lambda p:sha256(p.read_bytes()).hexdigest()
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
write = lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
before = OUT/'pre_mapping_schema_correction'; before.mkdir(exist_ok=False)
for name in ('reference_contract_builder.py','author_note.json','source_author_checks.json','source_delta.diff','README.md'):
    (before/name).write_bytes((OUT/name).read_bytes())
audit_file,builder_file = OUT/'audit_enlarged_square.py',OUT/'reference_contract_builder.py'
audit_sha = sha(audit_file)
assert audit_sha == '82c650d57ca5e2ccb07791b28bf2f9be743d025430d70a276f0cc9e7cba68028'
prep_source = PREP.read_text(encoding='utf-8')
prep_node = next(n for n in ast.parse(prep_source).body if isinstance(n,ast.FunctionDef) and n.name=='compare_models')
adapted = ast.get_source_segment(prep_source,prep_node).replace('def compare_models(', 'def verify_padding_arrays(').replace('old.files','old').replace('new.files','new')
builder_source = builder_file.read_text(encoding='utf-8')
builder_node = next(n for n in ast.parse(builder_source).body if isinstance(n,ast.FunctionDef) and n.name=='verify_padding_arrays')
old_segment = ast.get_source_segment(builder_source,builder_node)
assert builder_source.count(old_segment)==1
builder_source = builder_source.replace(old_segment,adapted)
builder_file.write_text(builder_source,encoding='utf-8',newline='\n')

class DictArrays(ast.NodeTransformer):
    def visit_Attribute(self,node):
        if node.attr=='files' and isinstance(node.value,ast.Name) and node.value.id in {'old','new'}:
            return ast.copy_location(node.value,node)
        return self.generic_visit(node)
expected = DictArrays().visit(copy.deepcopy(prep_node)); expected.name='verify_padding_arrays'
actual = next(n for n in ast.parse(builder_source).body if isinstance(n,ast.FunctionDef) and n.name=='verify_padding_arrays')
assert ast.dump(expected,include_attributes=False)==ast.dump(actual,include_attributes=False)
compile(ast.parse(builder_source),str(builder_file),'exec')
for path in (OUT/'core_audit_mechanical.py',OUT/'counter_attempts.py',OUT/'counter_original_B028.py'):
    assert sha(path)==read(OUT/'author_note.json')['candidate_pins'][path.name]
assert sha(audit_file)==audit_sha
diff=''
for path in (audit_file,builder_file):
    original=(OUT/'template'/path.name).read_text(encoding='utf-8')
    changed=path.read_text(encoding='utf-8')
    diff+=''.join(difflib.unified_diff(original.splitlines(keepends=True),changed.splitlines(keepends=True),fromfile='right_margin_cycle_001/reference_author/'+path.name,tofile='right_margin4_cycle_001/reference_author/'+path.name))
(OUT/'source_delta.diff').write_text(diff,encoding='utf-8',newline='\n')
readme=(OUT/'README.md').read_text(encoding='utf-8')
readme+='\nPre-freeze correction: independent static review found that the preparation mapping report added tip_coordinate_mm, parent_tip_node and new_tip_node. verify_padding_arrays now copies the final preparation compare_models source exactly, changing only its function name and NPZ .files collections to dictionary keys. Thickness20, unique physical tip mapping2570→2630, new top uy6967/6969 and exact RAW_FIELDS assertions are retained. This aligns saved report metadata; no HP formula, source gate, force/tangent or all-state loop changed. The pre-correction source and records are preserved in pre_mapping_schema_correction/.\n'
(OUT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
checks=read(OUT/'source_author_checks.json')
checks.update(preparation_mapping_function_AST_exact_after_name_and_files_adapter=True,
    saved_mapping_report_tip_fields_present=True,preparation_source_sha256=sha(PREP),
    pre_freeze_correction=True,correction_helper_sha256=sha(Path(__file__)))
checks['source_pins']={p.name:sha(p) for p in (audit_file,builder_file,OUT/'source_delta.diff',OUT/'README.md')}
write(OUT/'source_author_checks.json',checks)
note=read(OUT/'author_note.json')
note['pre_freeze_correction']=dict(reason='Independent static review found three saved mapping report keys absent from reference, causing LOAD exact dictionary mismatch.',
    source_file=str(PREP),source_sha256=sha(PREP),function='compare_models',
    adaptations=['Function name compare_models to verify_padding_arrays','old/new.files to old/new dictionary keys'],
    aligned_fields=['tip_coordinate_mm','parent_tip_node','new_tip_node'],
    additional_original_assertions_retained=['thickness20','unique coordinate tip2570 to2630 and node_map','new_top_uy6967/6969','raw_equal field set exact RAW_FIELDS'],
    audit_source_unchanged=audit_sha,HP_math_and_allN_loop_unchanged=True,
    scope='External source author correction before freeze; no preparation/production/reference/card execution, no scientific activity or formal writes.',
    previous_pins={p.name:sha(p) for p in before.iterdir()},helper_sha256=sha(Path(__file__)))
note['protected_AST']['preparation_mapping_function_exact_after_name_and_files_adapter']=True
note['candidate_pins']={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='author_note.json'}
write(OUT/'author_note.json',note)
print(json.dumps(dict(status='pass_static_source_only_after_mapping_schema_correction',pins={p.name:sha(p) for p in OUT.iterdir() if p.is_file()})))
