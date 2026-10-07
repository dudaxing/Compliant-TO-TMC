"""Record the narrow V2 saved-view source adaptation; never import it."""
from pathlib import Path
import ast
import hashlib
import json
from datetime import datetime, timezone

author=Path(__file__).resolve().parent
old=author.parent/'view_author'
root=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
stage=root/'lf_data_preparation/native_interface_001/batch_forward_001'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={'execute_batch_view.py':'14f761eaa8bc40a9daa75a6412a1d00f2320725b339a9ee7bd0384fb29dea5ad',
      'cached_view_adapter.py':'a9c1b5f0dd1b3e326b773d3af4efdb5a17cddbb509133428b1e567540f23a341'}
for name,pin in pins.items():
    assert sha(author/name)==pin
    ast.parse((author/name).read_bytes())
assert (author/'cached_view_adapter.py').read_bytes()==(old/'cached_view_adapter.py').read_bytes()
for name in ('numerical_rows_original_excerpt.py','numerical_rows_adaptation.diff',
             'render_original_excerpt.py','render_adaptation.diff'):
    assert (author/name).read_bytes()==(old/name).read_bytes()
adapter_tree=ast.parse((author/'cached_view_adapter.py').read_bytes())
model_keys={n.slice.value for n in ast.walk(adapter_tree) if isinstance(n,ast.Subscript)
    and isinstance(n.value,ast.Name) and n.value.id=='model' and isinstance(n.slice,ast.Constant)
    and isinstance(n.slice.value,str)}
model_keys.update(('coordinates','connectivity','solid'))
cases={}
for label in ('canonical','native_fine'):
    directory=stage/'run_001'/label
    result=read(directory/'result.json')
    metadata=read(directory/result['model']['descriptor_path'])
    fields=metadata['arrays']['fields']
    assert not model_keys-set(fields)
    port=metadata['region_metadata']['ports']['input']
    assert len(port['nonzero_dofs'])=={'canonical':3,'native_fine':5}[label]
    assert len(result['states'])==4
    cases[label]=dict(actual_N=4,input_nodes=len(port['nonzero_dofs']),
        model_keys=sorted(model_keys),missing_model_keys=[])
new_stage=root/'lf_data_preparation/native_interface_001/batch_reference_v2_001'
assert not new_stage.exists()
report=dict(schema_version='native-batch-view-v2-static-root-1.0',status='pass_static_only',
    blocking_findings=[],reviewed_utc=datetime.now(timezone.utc).isoformat(),source_sha256=pins,cases=cases,
    exact_worker_delta_sha256=sha(author/'worker_v1_to_v2.diff'),
    original_math_evidence_unchanged=True,new_reference_run='lf_data_preparation/native_interface_001/batch_reference_v2_001/run_001',
    source_contract_review_sha256=sha(author.parent/'review/v2_response_contract_review.json'),
    decisions=[
        'Read the original adapter and narrow worker diff. Drawing formulas, curves, force scale, x1/x40 display, actual-state loops, 3/5 port cardinality and captions remain unchanged.',
        'New protocol reference_run explicitly separates V2 audit output from the immutable production input directory.',
        'Both reference prerequisites require V2 protocol/execution2.0, same case, actualN, fresh2N, result/qualified/raw-summary identities, and matching worker plus F3 terminal/resource pass.',
        'Each old response remains raw; future own qualified responses use the generic saved formatter, which has compatible provider/consumer keys and does not promote contact/HF5 flags.',
        'Actual declared model and port names were checked directly; no coordinate alias or assumed three-node fine port is introduced.'
    ],
    execution_ready=False,freeze_allowed=False,
    current_missing_prerequisites=['canonical fresh V2 reference terminal PASS','native_fine fresh V2 reference terminal PASS'],
    limitations=['Source/JSON compatibility only; no actual reference summary exists or is synthesized here.',
                 'No render/media output, mechanics evaluation or scientific qualification is produced.'],
    activities=dict(candidate_imports=0,NPZ_loads=0,HF_imports=0,F=0,T=0,HP=0,solver=0,tests=0,renders=0,card_freezes=0))
(author/'root_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'root_review_sha256':sha(author/'root_review.json'),'execution_ready':False,'cases':cases}))
