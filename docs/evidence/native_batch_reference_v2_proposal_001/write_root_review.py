"""V2 source/AST/declared-field review only; no scientific imports."""
from pathlib import Path
import ast
import hashlib
import json
from datetime import datetime, timezone

author=Path(__file__).resolve().parent
root=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
production=root/'lf_data_preparation/native_interface_001/batch_forward_001'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
pins={'audit_batch_case.py':'e9642a3e00d62ba0728dbe95e9214cd4771dbfbc2ad8f9ce115f8157e4a41588',
      'reference_case_builder.py':'8744a981d1ec7d17a79ef4788701870d16bbf636a059b69144159a41de3d83f9'}
trees={}
for name,pin in pins.items():
    assert sha(author/name)==pin
    trees[name]=ast.parse((author/name).read_bytes())
cls=next(n for n in trees['audit_batch_case.py'].body if isinstance(n,ast.ClassDef))
assert {n.name for n in cls.body if isinstance(n,ast.FunctionDef)}=={'__init__','checkpoint','lifecycle','load'}
original_cls=next(n for n in ast.parse((production/'reference_author/audit_batch_case.py').read_bytes()).body if isinstance(n,ast.ClassDef))
for method in ('checkpoint','lifecycle'):
    current=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method)
    original=next(n for n in original_cls.body if isinstance(n,ast.FunctionDef) and n.name==method)
    assert ast.dump(current,include_attributes=False)==ast.dump(original,include_attributes=False)
used={n.slice.value for n in ast.walk(trees['audit_batch_case.py']) if isinstance(n,ast.Subscript)
      and isinstance(n.value,ast.Name) and n.value.id=='model'
      and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str)}
assert 'coords' not in used and 'coordinates' in used
cases={}
for label in ('canonical','native_fine'):
    directory=production/'run_001'/label
    result=read(directory/'result.json')
    metadata=read(directory/result['model']['descriptor_path'])
    fields=metadata['arrays']['fields']
    assert len(fields)==23 and not used-set(fields)
    assert fields['coordinates']['shape']==[result['counts']['nodes'],2]
    assert fields['edofs']['shape']==[result['counts']['cells'],8]
    assert fields['b_in']['shape']==[result['counts']['dofs']]
    cases[label]=dict(actual_states=len(result['states']),fresh_HP_required=2*len(result['states']),
        model_subscripts=sorted(used),missing_subscripts=[],model_field_count=len(fields))
failure=read(production/'run_001/audit/canonical/execution_receipt.json')
assert failure['status']=='not_pass' and failure['HP_calls_started']==failure['HP_calls_completed']==0
assert read(production/'run_001/execution_receipt.json')['status']=='pass'
report=dict(schema_version='native-batch-case-reference-v2-static-root-1.0',status='pass_static_only',
    blocking_findings=[],reviewed_utc=datetime.now(timezone.utc).isoformat(),source_sha256=pins,cases=cases,
    full_load_diagnosis_sha256=sha(author/'load_diagnosis.json'),
    decisions=[
        'Read the exact V1-to-V2 source diff and complete field/state/attribute diagnosis; added model subscript names were compared with both actual23-field declarations.',
        'The only mechanics-adjacent loading correction is coords to coordinates; original Audit.run/run_state/80-120 precision/scatter/port direction/GATES remain inherited.',
        'Checkpoint/lifecycle ASTs match V1 exactly; the new stage/output/rootstop separate future execution from the closed failure.',
        'PRODUCTION_STAGE retains complete raw production and its aa072 baseline; current HEAD need not equal that historical producer baseline.',
        'Closed V1 failure is pinned as context only, with HP0 and no numerical qualification. No closed source/card/output is modified.',
        'Each new case still requires fresh2N (actualN4 gives8HP); fine starts only after the new canonical terminal pass.',
        'Original summary is preserved; qualified summary cannot be used without matching worker receipt and outer F3 terminal/resource pass.'
    ],
    explicit_proposed_budgets={'canonical':{'helper_seconds':240,'outer_seconds':270},
                               'native_fine':{'helper_seconds':900,'outer_seconds':960}},
    sampled_RSS_limit_bytes=8*1024**3,execution_authorized=False,
    limitations=['Declared JSON and source compatibility only; no NumPy/NPZ/HP execution or new numerical qualification.',
                 'No production rerun, all tangent columns, energy, contact, pressure, mesh convergence, ranking or HF5 qualification.'],
    activity=dict(candidate_imports=0,builder_calls=0,NPZ_loads=0,HF_imports=0,HP=0,F=0,T=0,solver=0,renders=0))
(author/'root_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'root_review_sha256':sha(author/'root_review.json'),'cases':cases}))
