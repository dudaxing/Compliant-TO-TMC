"""Independent narrow AST/raw comparison only; candidate is never imported."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

OUT=Path('D:/hf-margin4-author-20261007/closure_candidate')
digest=lambda p:sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
final=OUT/'close_margin4_docs.py'
old=OUT/'template/001.py'
assert digest(final)=='b00729df13e2cd89118defd03204080433f6300ab5bd92ca65061dde1398003e'
assert digest(old)=='7e2e32543dd367fcadb84f8666fb32fb58cb4803aa1780adaa4ce7184ab2b1c9'
assert digest(OUT/'template/006.json')=='8d976894111d3248300f23afb8a324bd4e4cb83a0f443ffbbbf95a3362de0a00'
assert digest(OUT/'source_revision.diff')=='247e2de06a38f38383591c78e01c53b12957e0db7a1e2b705e5a63a8a4f028fd'
note=read(OUT/'author_note.json')
for name,pin in note['candidate_sources'].items():assert digest(OUT/name)==pin,name
ot,nt=ast.parse(old.read_text(encoding='utf-8-sig')),ast.parse(final.read_text(encoding='utf-8-sig'))
def fn(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
assert ast.dump(fn(ot,'collect'),include_attributes=False)==ast.dump(fn(nt,'collect'),include_attributes=False)
context_node=next(n.value for n in nt.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='SOURCE_CONTEXT' for x in n.targets))
context=ast.literal_eval(context_node)
assert context==note['source_context_identity'] and len(context)==14
context_pins={}
for name,item in context.items():
    path=OUT/item['candidate_path']
    assert digest(path)==item['sha256'],name
    context_pins[name]={'candidate_path':item['candidate_path'],'source_name':item['source_name'],'sha256':item['sha256'],'raw_identity_matches':True}
scaling_node=next(n.value for n in nt.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='SCALING_NOTE' for x in n.targets))
scaling=ast.literal_eval(scaling_node)
for required in ['尚未做本项实验','同静态解分支','固定ν/γ/α/Lr','k_out=0','无未同比缩放的独立外载','c>0','整个KKT矩阵不同比例缩放','迭代次数不保证相同','不能据此宣称']:
    assert required in scaling,required
report={
 'schema_version':'margin4-closing-documents-final-delta-peer-1.0',
 'status':'pass_static_only','generated_utc':datetime.now(timezone.utc).isoformat(),
 'candidate_sources':{**note['candidate_sources'],'author_note.json':digest(OUT/'author_note.json')},
 'prior_source_sha256':digest(old),'prior_static_review_sha256':digest(OUT/'template/006.json'),
 'collect_AST_exact':True,'context_pins':context_pins,
 'findings':[
  'Full collect AST is exactly the reviewed7e2e template: production/reference/view gates, allN2N, resource limits, scalar matching and scientific qualification are unchanged.',
  'Only uniform-E source reasoning prose/matrix plus raw context/template identity/archive metadata are added. Same static branch, fixed geometric/displacement/material-factor conditions, zero output spring and no unscaled independent loads are explicit.',
  'Force scaling does not imply more conformity; the physical stiffness block scales, whole KKT does not, and finite-precision/iteration/branch behavior is not guaranteed. The added note is explicitly not a new experiment.',
  '14 context/template entries009–022 are actual rawSHA matches, including original7e2e and8d97 peer report.023 preserves the narrow revision diff; current author/helper archive004–008 and existing prelaunch/running snapshots remain separately identifiable.',
  'SOURCE_CONTEXT identity is checked before either entry writes, repeated against proposal closed_summary during install, and included in final install receipt/index. Paths are package-relative; original names are provenance.',
  'Added E/HF5 links resolve from docs to closure_001/009.md and011.md. HF5 source/interface notes remain unimplemented proposals and are not granted experimental/runtime qualification.',
 ],
 'blocking_findings':[],
 'scope':'Narrow finalsource diff/AST/raw pin review only; no proposal generation, install or actual4mm result/view review performed.',
 'current_stage_context':'Parent reports allthree actual phases nowclosedPASS24states/48freshHP/488232checks and48geometry/48nodal. Not independently inspected in this source-delta review; actual proposals still require saved-only review.',
 'activity':{'candidate_or_HF_imports':0,'candidate_execution':0,'NPZ_or_array_reads':0,'constructors':0,'F_T_solver_HP':0,'geometry_nodal_plot':0,'formal_writes':0},
}
target=OUT/'closure_final_static_review.json'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'report':str(target),'sha256':digest(target)},ensure_ascii=False))
