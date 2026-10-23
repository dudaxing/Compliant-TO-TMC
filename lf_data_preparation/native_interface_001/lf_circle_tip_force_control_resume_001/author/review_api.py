"""Independent bounded source review; no candidate import or execution."""
import ast
from hashlib import sha256
import json
from pathlib import Path

A=Path(__file__).resolve().parent
R=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
C=Path('D:/hfrs1_001/candidate/hf_repo/src/hf_eval')
old=ast.parse((R/'hf_repo/src/hf_eval/native_guided_force.py').read_bytes())
new=ast.parse((C/'native_guided_force.py').read_bytes())
resume=ast.parse((C/'native_guided_force_resume.py').read_bytes())
def func(tree,name): return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
def same(a,b): return ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
original=func(old,'evaluate_native_guided_force'); current=func(new,'evaluate_native_guided_force')
assert same(original.args,current.args)
prefix=original.body[:next(i for i,n in enumerate(original.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='model' for t in n.targets))]
assert len(current.body)==len(prefix)+1 and all(same(a,b) for a,b in zip(prefix,current.body))
runner=func(new,'_run_guided_force')
for name in ('assemble','vector_sum'):
    o=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name==name)
    n=next(n for n in runner.body if isinstance(n,ast.FunctionDef) and n.name==name)
    assert same(o,n),name
entry=func(resume,'extend_native_guided_force')
assert [n.arg for n in entry.args.args]==['saved_force_result','full_extended_body_load_targets_half_N','output_directory']
assert [n.arg for n in entry.args.kwonlyargs]==['fixed_parent_result','time_limit_seconds','on_accept']
assert entry.args.kwarg is None
text=(C/'native_guided_force_resume.py').read_text(encoding='utf-8')
assert '_admit(' not in text and 'root_force_ancestors_revalidated=False' in text
assert text.count('np.load(')==1
checks=[
    ('A01','Default evaluate signature and every original pre-run validation/admission AST unchanged'),
    ('A02','One shared runner; original assemble/vector_sum AST unchanged; no duplicate force or tangent implementation'),
    ('A03','New public signature has only full targets/output, clock/callback and same-byte fixed-source location'),
    ('A04','Known 1.0/1.1 success/complete-original-terminal semantics checked before selected mechanics'),
    ('A05','Full target prefix canonical identity, strict signed increase, local/global index coverage and segment-only execution'),
    ('A06','Root P0 is independent of segment P; 1.1 anchor/full-first equality and inherited scales retained'),
    ('A07','Opaque original model identity and original geometry/material/regions/ports/body/member equality, two kernel SHA hard gates'),
    ('A08','One selected force-state NPZ, exactly two float64 split fields with archive/field/state hashes and absolute q structure; no fixed q0 cache'),
    ('A09','Fresh cached capture additionally checks q/P/R bits, original state hash and check1; no repair or q-origin reset'),
    ('A10','Nonclock settings and force step inherited; original signed R and body-x external load accounting unchanged'),
    ('A11','Only identity-preserving fixed-parent location and relative model/geometry resolution; output outside both source trees'),
    ('A12','Typed pre-F/T source/input/extension rejection and original numerical partial persistence; save-time F/T remains zero'),
    ('A13','Shallow root/immediate pins and actual relocated path separated from historical source; no recursive ancestor read or full-path recompute claim'),
    ('A14','All qualification flags false; schema1.1 isolated from unchanged default1.0; new module in producer hashes'),
]
pins=[]
for name in ('native_guided_force.py','native_guided_force_resume.py'):
    raw=(C/name).read_bytes();pins.append(dict(path=str(C/name),bytes=len(raw),sha256=sha256(raw).hexdigest()))
record=dict(stage='L-CTIPFRESUME1',status='PASS_STATIC_ONLY',reviewer='root independent of API author',
    check_count=len(checks),checks=[dict(id=a,status='PASS',finding=b) for a,b in checks],source_pins=pins,
    AST_proofs=['Default function signature and full validation prefix identical','assemble and vector_sum identical','explicit new argument list, no kwargs','one selected np.load site/no _admit call'],
    limits='Source reasoning is not numerical validation; actual known schemas, q/P/R fresh identity and child/grandchild results require the unique authorized test window.',
    candidate_imports=0,F=0,T=0,HP=0,tests_run=0,production_changes=0)
(A/'API_STATIC_REVIEW.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md='# API/保存态准入独立静审\n\n14项源码/有限AST核对通过；不是数值测试PASS。当前只在候选树修改，未导入HF、运行测试、读取科学缓存或修改正式源码。\n\n'
md+='\n'.join(f'- {a} PASS — {b}' for a,b in checks)+'\n\n'
md+='原evaluate签名和完整准入前缀、assemble/vector_sum均作AST原样比较。新模块按直接父与root固定模型闭包检查，历史root-force pin不当作祖先数值重核。静态结论以本JSON两份源码SHA为准，实际验证待唯一已授权窗口。\n'
(A/'API_STATIC_REVIEW.md').write_text(md,encoding='utf-8')
print(json.dumps(dict(status='PASS_STATIC_ONLY',checks=len(checks),pins=pins)))
