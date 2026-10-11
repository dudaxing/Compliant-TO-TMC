"""Finalize an independent ordinary-byte/JSON/AST review, not installation."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

EXT=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/saved_integration_001'
STAGE=ROOT/REL
sha=lambda p:sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
PROTOCOL_PIN='62396704768bd3f6cd4ec09bf2e438c126ebd1867b590b5a119d4671a26e666e'
assert sha(STAGE/'protocol.json')==PROTOCOL_PIN
protocol=read(STAGE/'protocol.json')
assert protocol['card']=='M-INTEGRATE1'
assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
assert (protocol['focused_tests_seconds'],protocol['helper_seconds'],protocol['outer_seconds'],protocol['sampled_RSS_bytes'])==(180,300,360,8589934592)
assert protocol['automatic_rollback'] is False and protocol['retries']==0
bindings=protocol['bindings']
assert len(bindings)==108
formal={REL+'/protocol.json':PROTOCOL_PIN}
ast_records={}
for name,pin in bindings.items():
    p=ROOT/name
    assert p.suffix.lower()!='.npz'
    assert sha(p)==pin
    formal[name]=pin
    if p.suffix=='.py':
        tree=ast.parse(p.read_text(encoding='utf-8'),filename=name)
        ast_records[name]=dict(top_functions=[n.name for n in tree.body if isinstance(n,ast.FunctionDef)])

install=protocol['installation']
assert len(install)==11 and len({r['target'] for r in install})==11
changes={r['target']:r for r in install}
old=[r for r in install if r['previous_sha256'] is not None]
new=[r for r in install if r['previous_sha256'] is None]
assert len(old)==6 and len(new)==5
external={}
for row in install:
    target=(ROOT/row['target']).resolve()
    target.relative_to(ROOT/'hf_repo')
    assert sha(ROOT/row['candidate'])==row['sha256']
    extname='candidate/'+row['target']
    assert sha(EXT/extname)==row['sha256']
    external[extname]=row['sha256']
    assert (sha(target) if target.exists() else None)==row['previous_sha256']
    if row['previous_sha256'] is not None:
        assert sha(ROOT/row['baseline_snapshot'])==row['previous_sha256']
        assert (ROOT/row['baseline_snapshot']).read_bytes()==target.read_bytes()
    else:
        assert row['baseline_snapshot'] is None and not target.exists()
assert not set(changes).intersection(bindings)
runtime=protocol['installed_runtime_SHA256']
modules={name:pin for name,pin in runtime.items() if name.startswith('hf_repo/src/hf_eval/')}
assert len(modules)==52 and len(runtime)==58
present={p.relative_to(ROOT).as_posix() for p in (ROOT/'hf_repo/src/hf_eval').glob('*.py')}
assert set(modules)==present|{'hf_repo/src/hf_eval/native_resume.py'}
unchanged=[]
for name,pin in runtime.items():
    if name in changes:
        assert changes[name]['sha256']==pin
    else:
        assert sha(ROOT/name)==pin==bindings[name]
        unchanged.append(name)
assert len(unchanged)==47
kernel_names=['hf_repo/src/hf_eval/'+name for name in ('native_project.py','native_force.py',
    'native_tangent.py','split_kernel_invariants_hu.py','split_numpy_tangent.py',
    'compensated_invariants.py','compensated_kinematics.py','tmc_kernel.py','split_state.py','displacement.py')]
assert all(name in unchanged for name in kernel_names)

selected=protocol['focused_test_selectors']
scope=read(STAGE/'author/test_scope_final.json')
assert len(selected)==len(set(selected))==25 and selected==scope['focused_test_selectors']
assert scope['authorized'] is scope['executed'] is False and scope['collected'] is False
for rel in ('M-INTEGRATE1_CARD.md','README.md','PREPARATION_RESULTS.md'):
    formal[REL+'/'+rel]=sha(STAGE/rel)
assert (STAGE/'M-INTEGRATE1_CARD.md').read_bytes()==(EXT/'M-INTEGRATE1_CARD.md').read_bytes()
card=(STAGE/'M-INTEGRATE1_CARD.md').read_text(encoding='utf-8')
assert 'NumPy切线' in card and '一份2帧GIF' in card and 'NOT_PASS' in card
assert 'AD切线' not in card and '两份2帧GIF' not in card
for name in ('execute_integration.py','integration_focused_budget.py','launch_integration.py'):
    assert (STAGE/name).read_bytes()==(EXT/name).read_bytes()
    external[name]=sha(EXT/name)
    ast.parse((EXT/name).read_text(encoding='utf-8'),filename=name)
external['M-INTEGRATE1_CARD.md']=sha(EXT/'M-INTEGRATE1_CARD.md')
for name in ('controller_compatibility_review.json','source_identity_migration_review.json','mock_test_source_review.json','test_scope_final.json'):
    external[name]=sha(EXT/name)
    assert (STAGE/'author'/name).read_bytes()==(EXT/name).read_bytes()

# Static type/catch placement and unchanged strict source matching; no callable evaluation.
api_name='candidate/hf_repo/src/hf_eval/native_evaluate.py'
api=ast.parse((EXT/api_name).read_text(encoding='utf-8'))
fun=next(n for n in api.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_native')
trial=next(n for n in fun.body if isinstance(n,ast.Try))
guard_index=next(i for i,n in enumerate(trial.body) if isinstance(n,ast.If)
    and 'isinstance(settings, DisplacementSettings)' in ast.unparse(n.test))
default_index=next(i for i,n in enumerate(trial.body) if any(isinstance(sub,ast.Call)
    and isinstance(sub.func,ast.Name) and sub.func.id=='saved_resume_defaults' for sub in ast.walk(n)))
assert guard_index<default_index
assert 'ValueError' in ast.unparse(trial.handlers[0].type)
tmc=ast.parse((ROOT/'hf_repo/src/hf_eval/tmc.py').read_text(encoding='utf-8'))
error_class=next(n for n in tmc.body if isinstance(n,ast.ClassDef) and n.name=='TMCError')
assert any(isinstance(n,ast.Name) and n.id=='ValueError' for n in error_class.bases)
identity=read(EXT/'source_identity_migration_review.json')
assert identity['status'].startswith('pass_')
for name,pin in identity['reviewed_external_SHA256'].items():assert sha(EXT/name)==pin
for name in ('native_mean.py','native_response.py','native_resume.py','split_displacement.py'):
    closed=ROOT/'lf_data_preparation/native_interface_001/saved_continuation_001/candidate/hf_repo/src/hf_eval'/name
    current=EXT/'candidate/hf_repo/src/hf_eval'/name
    assert closed.read_bytes()==current.read_bytes()

helper=(STAGE/'execute_integration.py').read_text(encoding='utf-8')
launcher=(STAGE/'launch_integration.py').read_text(encoding='utf-8')
plugin=(STAGE/'integration_focused_budget.py').read_text(encoding='utf-8')
assert 'window_closed = stop.exists()' in helper
assert 'Resource boundary reached during receipt write' in helper
assert 'started, peak, reason = STARTED' in launcher
assert 'child_terminal_wall_seconds=child_elapsed' in launcher
assert 'closed_resource_window_at_receipt_write' in launcher
assert 'collected != EXPECTED' in plugin and 'len(calls) != 25' in plugin
assert 'outside the installed default package' in plugin
assert 'synthetic/mocked callbacks separate, no universal kernel-call claim' in plugin
assert not (STAGE/'run_001').exists()
assert not (STAGE/'integration_launch.json').exists()
assert not (STAGE/'author/authorization.json').exists()
assert not (STAGE/'author/direct_human_reply.json').exists()

checks=[
    'All 108 immutable bindings match ordinary/source/image bytes; no binding is NPZ and no arrays were opened.',
    'Eleven installation rows are unique: six exact old-source snapshots and five absent new paths; default source remains uninstalled.',
    'Proposed runtime covers all 52 hf_eval modules, two CLI files and four installed test files; 47 unchanged modules retain exact current pins.',
    'Original material/Hu kernels, force/tangent assembly, project, split state, compensation and settings source bytes are unchanged.',
    'Twenty-five unique frozen selectors match the independently prepared AST selection; no collection or test execution.',
    'Typed invalid_settings guard precedes saved defaults, TMCError inherits ValueError, original catch remains; six additional mock/JSON instances independently reviewed.',
    'Closed validated controller/Mean/response/reader bytes are inherited; zero-default, nonzero fresh validation-only anchor, signed unsymmetric augmented solve and rollback contracts are retained.',
    'Old reference source matching remains strict: coarse current-source mismatch is expected, original matched responses/HP are retained, M-REF2 11 protocol/12 actual source entries have no installed-production intersection.',
    'The sole helper installs once then runs one -x pytest child; failed partial installation is retained without automatic rollback or retry.',
    'Authorization checks bind actual direct human reply/context/source publication/protocol/HEAD; preparation does not create authorization.',
    'Focused 180s/helper 300s/outer 360s and sampled 8 GiB apply to whole relevant windows; final hashes/receipt writes can downgrade PASS, cooperative stop never force-terminates.',
    'Default HF import paths and NativeMean NumPy alias started/completed accounting are explicit; synthetic callbacks are not claimed as universally monitored kernels.',
    'Prepared Card/README/PREP distinguish source preparation from actual PASS and keep parent NOT_PASS, incomplete full path, no new HP/pressure/grip/stability/HF5 qualification.',
]
md='''# M-INTEGRATE1 协议与执行包装：独立静审

正式协议 SHA `62396704768bd3f6cd4ec09bf2e438c126ebd1867b590b5a119d4671a26e666e` 的 108 份不可变绑定与实际字节一致。11 条安装映射为 6 份原源码精确快照和 5 个尚不存在的新路径；拟运行包覆盖全部 52 个 hf_eval 模块、2 个 CLI 和 4 个新安装测试文件。47 个保留模块，以及原力核、Hu 核、切线／组装、补偿、状态和设置源码，均保持原字节。

25 个唯一选择与冻结 AST 选择报告一致。六个新增 mock／普通 JSON 实例已经独立源码审阅；settings 类型门位于 saved defaults 前，原 TMCError／ValueError 错误合同保持。Mean、controller、reader、response 继承已闭 M-RESUME1 字节。旧零起点分支、非零锚点 fresh F／T 复核且复核失败不修正、未对称增广系统的均值／R 符号和未接受尝试回滚，没有新的数值门或力学核改变。

三个执行包装与冻结外部字节一致：一次安装、一次 `-x` pytest，HF 导入必须来自正式默认包；NativeMean NumPy aliases 计数保持其限定范围。tests 180／helper 300／outer 360 秒及采样 8 GiB 覆盖各自整窗，末尾 hashes／receipt 写入检查可使结果降为 NOT_PASS。触发停止时保留实际 partial，不重试、force 或自动回滚。此前发现的末端窗口判定缺口已经最小收口。

来源迁移严格门保持。right2／right4 原参考与安装路径仅 mean／split 两交集，未来 current-source 重总结会 mismatch，原保存 matched 响应和 HP 数值证据保留。M-REF2 的协议 11 项、实际摘要 12 项没有该交集；不笼统撤销其原机械参考范围。

本报告只做普通文本、JSON、原字节和 AST 核查，没有安装、HF 导入、collect、测试、NPZ 读取、科学调用或绘图。当前仍未授权／未执行；静审通过不构成实际测试通过、完整卸载、压力、有效夹持力、稳定性或 HF5 资格。
'''
mdp=EXT/'INTEGRATION_PROTOCOL_REVIEW.md'
with mdp.open('x',encoding='utf-8',newline='\n') as o:o.write(md)
report=dict(schema_version='MINTEGRATE1-integration-protocol-static-review-1.0',
    status='pass_static_formal_integration_protocol_and_wrappers_not_executed',
    created_utc=datetime.now(timezone.utc).isoformat(), authorized=False,executed=False,
    protocol_sha256=PROTOCOL_PIN,reviewed_formal_SHA256=formal,reviewed_external_SHA256=external,
    counts=dict(immutable_bindings=108,installation_rows=11,existing_snapshots=6,new_absent_targets=5,
        installed_HF_modules=52,installed_CLI=2,installed_test_files=4,unchanged_HF_modules=47,
        selected_unique_test_instances=25,additional_mock_JSON_instances=6,AST_sources=len(ast_records)),
    original_kernel_SHA256={name:runtime[name] for name in kernel_names},
    windows=dict(focused_tests_seconds=180,helper_seconds=300,outer_seconds=360,sampled_RSS_bytes=8589934592),
    checks=checks,findings=[],blockers=[],
    inherited_evidence=dict(controller_static_review_sha256=sha(EXT/'controller_compatibility_review.json'),
        source_migration_review_sha256=sha(EXT/'source_identity_migration_review.json'),
        mock_test_source_review_sha256=sha(EXT/'mock_test_source_review.json')),
    actions=dict(HF_or_candidate_import=0,test_collect=0,pytest=0,NPZ_byte_read_or_decode=0,
        model_force_tangent_solver_HP_observer_render=0,installation=0,formal_mutation=0),
    limits=['Actual future collection, test outcomes, counts and resources remain unobserved.',
        'Only finite installed-interface compatibility is proposed; no original large-model solve or qualification upgrade.'],
    documentation_sha256=sha(mdp))
jp=EXT/'integration_protocol_review.json'
with jp.open('x',encoding='utf-8',newline='\n') as o:o.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=report['status'],JSON_SHA256=sha(jp),MD_SHA256=sha(mdp),counts=report['counts'],tools={name:external[name] for name in ('execute_integration.py','integration_focused_budget.py','launch_integration.py')})))
