"""Read source/AST/SHA only; no module imports, observations or plotting."""
import ast
import difflib
import json
from hashlib import sha256
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
sha=lambda p:sha256(p.read_bytes()).hexdigest()
original=HERE/'saved_shift_views_original_16d2c.py'
new=HERE/'saved_right_margin_views.py'
oldtext,newtext=original.read_text(encoding='utf-8'),new.read_text(encoding='utf-8')
oldtree,newtree=ast.parse(oldtext),ast.parse(newtext)
compile(newtree,str(new),'exec')
checks=[]
def check(name,truth,basis):
    assert truth,name
    checks.append(dict(name=name,status='pass_static_only',basis=basis))
check('raw_original_and_candidate_SHA',sha(original)=='16d2c0295d03579a32adaf321a283ad9ae6f23579c4455f688be8720bb1984b0' and sha(new)=='761a9ffd1512233ce048be364c00a86882b69e2fb3e3fe81d7f79f74ad52b166' and sha(original)==sha(ROOT/'functional_views/workpiece_gamma_20261007/complete_001/saved_shift_views.py'),'Retained originalviewer raw exact; new source reviewed as external only.')
diff=''.join(difflib.unified_diff(oldtext.splitlines(keepends=True),newtext.splitlines(keepends=True),fromfile=original.name,tofile=new.name))
check('source_delta_reproduces_exact',diff==(HERE/'viewer_delta.diff').read_text(encoding='utf-8'),'Reviewed all9 declared replacement sites; no undeclared source changes.')
def functions(t):return {n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
of,nf=functions(oldtree),functions(newtree)
check('finite_distance_and_serializers_AST_exact',all(ast.dump(of[n],include_attributes=False)==ast.dump(nf[n],include_attributes=False) for n in ('plain','write','point_segment')),'Unsigned finite-segment distance algorithm and serialization remain original.')
def calls(t,name):return [ast.dump(n,include_attributes=False) for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name]
check('observation_calls_AST_exact',all(calls(oldtree,n)==calls(newtree,n) for n in ('measure_native_workpiece_regions','observe_workpiece_nodal_forces','point_segment')),'Existing geometry/nodal observation call count and arguments untouched; no F/T/constructor/solver/HP addition.')
check('physical_tip_selection_and_reuse','TIP_REFERENCE_MM = (80., 30.)' in newtext and 'len(tip_nodes)!=1' in newtext and '[2510]' not in newtext and '[2509]' not in newtext and 'tip=xy[case["tip_node"]]' in newtext and 'row["xy"][case["tip_node"]]' in newtext,'Unique exact saved reference coordinate, per-case numbering; no nearest node/snapping. New node number is not presumed.')
check('recorded_tip_node_source','tip_node=case["tip_node"]' in newtext and 'tip_node=c["tip_node"]' in newtext and 'tip_selection=dict(reference_coordinates_mm=list(TIP_REFERENCE_MM)' in newtext,'Row is written to stateCSV/derivedJSON; case metadata records node; declared distance scope names physical(80,30).')
check('display_only_peak_layout','fraction=.046,pad=.035' in newtext and 'case["label"]+"\\n"+title' in newtext,'Peak title newline and colorbar gap; original field computation/ranges, transforms and scaling unchanged.')
check('fresh_result_reference_gate_retained',calls(oldtree,'read')==calls(newtree,'read'),'Existing savedfile hash and same-result full-reference checks remain unchanged; future wrapper must freeze actual new complete production/reference evidence.')
report=dict(schema_version='right-margin-saved-view-static-review-1.0',status='pass_static_only',checks_passed=len(checks),checks=checks,blocking_findings=[],
 source_pins={p.name:sha(p) for p in (original,new,HERE/'viewer_delta.diff',HERE/'author_note.json',HERE/'README.md')},
 reviewer_activity=dict(candidate_imports=0,NPZ_array_reads=0,constructors=0,F_T_solver_HP_calls=0,geometry_nodal_strain_render_calls=0,formal_writes=0,protocol_freezes=0),
 qualification='Future saved-view source only. No newview result or mechanical qualification; production/reference PASS and its own bounded card remain prerequisites.',review_script_sha256=sha(Path(__file__)))
out=HERE/'saved_view_static_review.json'
with out.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
print(json.dumps(dict(status=report['status'],checks=len(checks),path=str(out),sha256=sha(out))))
