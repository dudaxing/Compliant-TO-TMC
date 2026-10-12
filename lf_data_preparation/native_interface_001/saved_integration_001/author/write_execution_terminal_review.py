"""Read already-terminal ordinary evidence; never import HF or open NPZ."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

EXT=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/saved_integration_001'
STAGE=ROOT/REL
PREP=Path('D:/hf-native-workpiece-api-author-20261012/MINTEGRATE1_preparation_001')
PIN='62396704768bd3f6cd4ec09bf2e438c126ebd1867b590b5a119d4671a26e666e'
COMMIT='2b550d09f4347240ef6cb626b4c829566b638e61'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
reviewed={}
def ordinary(name):
    p=ROOT/name
    assert p.suffix.lower()!='.npz'
    reviewed[name]=sha(p)
    return p
def read(name):return json.loads(ordinary(name).read_bytes())

protocol=read(REL+'/protocol.json')
assert reviewed[REL+'/protocol.json']==PIN
outer=read(REL+'/integration_launch.json')
helper=read(REL+'/run_001/execution_receipt.json')
tests=read(REL+'/run_001/focused_test_receipt.json')
authorization=read(REL+'/author/authorization.json')
human=read(REL+'/author/direct_human_reply.json')
proof=read(REL+'/author/source_publication_receipt.json')
assert authorization['authorized'] is authorization['authorization_from_direct_human_reply'] is True
assert human['authorization_from_direct_human_reply'] is True
assert authorization['direct_human_answer']==human['direct_human_answer']=='批准按 M-INTEGRATE1 卡执行'
assert human['reply_context'] and 'call_e31742769f9c49bda4a48588a7a0d497' in human['questionItemId']
assert authorization['approved_source_commit']==human['approved_source_commit']==proof['published_commit']==helper['approved_source_commit']==COMMIT
assert authorization['human_evidence_sha256']==reviewed[REL+'/author/direct_human_reply.json']
assert authorization['source_publication_receipt_sha256']==reviewed[REL+'/author/source_publication_receipt.json']
assert authorization['protocol_sha256']==outer['protocol_sha256']==helper['protocol_sha256']==PIN
assert proof['status']=='published_and_incrementally_restored_pass'
assert proof['prepared'] is True and proof['authorized'] is proof['executed'] is False
assert authorization['invocations_authorized']==outer['invocations']==1
assert authorization['retries']==0 and authorization['force'] is authorization['automatic_rollback'] is False
assert outer['status']==helper['status']==tests['status']=='pass'
assert outer['exit_code']==tests['exit_code']==helper['focused_tests_terminal']['exit_code']==0
assert outer['stop_reason'] is tests['stop_reason'] is helper['focused_tests_terminal']['stop_reason'] is None
assert helper['failure'] is None and helper['installation_complete'] is True
assert helper['focused_tests_started']==helper['focused_tests_completed']==1
assert outer['elapsed_seconds']<=protocol['outer_seconds']
assert outer['child_terminal_wall_seconds']<=protocol['helper_seconds']
assert helper['elapsed_seconds']<=protocol['helper_seconds']
assert tests['elapsed_seconds']<=protocol['focused_tests_seconds']
assert helper['focused_tests_terminal']['elapsed_seconds']<=protocol['focused_tests_seconds']
assert max(outer['peak_sampled_tree_RSS_bytes'],helper['peak_sampled_RSS_bytes'],tests['peak_sampled_RSS_bytes'])<=protocol['sampled_RSS_bytes']
assert outer['immutable_bindings_unchanged'] is helper['immutable_bindings_unchanged'] is True
assert helper['test_receipt_sha256']==reviewed[REL+'/run_001/focused_test_receipt.json']

assert len(protocol['bindings'])==108
for name,pin in protocol['bindings'].items():assert sha(ordinary(name))==pin
expected={row['target']:row['sha256'] for row in protocol['installation']}
assert len(expected)==11 and helper['installed_SHA256']==expected
assert helper['installed']==[dict(path=row['target'],sha256=row['sha256']) for row in protocol['installation']]
snapshots={}
for row in protocol['installation']:
    assert sha(ordinary(row['target']))==row['sha256']
    if row['previous_sha256'] is not None:
        assert sha(ordinary(row['baseline_snapshot']))==row['previous_sha256']
        oldraw=subprocess.check_output(['git','show',COMMIT+':'+row['target']],cwd=ROOT)
        assert sha256(oldraw).hexdigest()==row['previous_sha256']
        snapshots[row['target']]=dict(old_sha256=row['previous_sha256'],
            installed_sha256=row['sha256'],baseline_snapshot=row['baseline_snapshot'],
            published_pre_install_Git_commit=COMMIT)
assert len(snapshots)==6
for name,pin in protocol['installed_runtime_SHA256'].items():assert sha(ordinary(name))==pin
assert len(protocol['installed_runtime_SHA256'])==58
for name,path in tests['imported_HF_modules'].items():
    resolved=Path(path).resolve()
    resolved.relative_to(ROOT/'hf_repo/src/hf_eval')
    rel=resolved.relative_to(ROOT).as_posix()
    assert sha(ordinary(rel))==protocol['installed_runtime_SHA256'][rel]
assert len(tests['imported_HF_modules'])==26
assert len(tests['observed_models'])==7
assert all(row['cells']==16 and row['dofs']==50 for row in tests['observed_models'])

selected=protocol['focused_test_selectors']
assert len(selected)==len(set(selected))==25
assert tests['collected_selectors']==selected and tests['passed_calls']==25
assert len(tests['reports'])==75
assert tests['reports']==[dict(nodeid=name,when=when,outcome='passed')
    for name in selected for when in ('setup','call','teardown')]
xmlpath=ordinary(REL+'/run_001/test_results.xml')
xml=ET.parse(xmlpath).getroot()
suite=xml.find('testsuite')
assert suite is not None
assert {key:suite.attrib[key] for key in ('tests','errors','failures','skipped')}==dict(tests='25',errors='0',failures='0',skipped='0')
cases=suite.findall('testcase')
assert [row.attrib['name'] for row in cases]==[name.split('::',1)[1] for name in selected]
assert all(not list(row) for row in cases)
stdoutpath=ordinary(REL+'/run_001/focused_tests_stdout.log')
stdout=stdoutpath.read_text(encoding='utf-8')
assert '25 passed in 6.62s' in stdout
helperstdout=ordinary(REL+'/integration_stdout.log').read_text(encoding='utf-8')
printed=[json.loads(row) for row in helperstdout.splitlines() if row.strip()]
assert len(printed)==1 and printed[0]['status']=='pass'
assert printed[0]['focused_tests_started']==printed[0]['focused_tests_completed']==1
counts=tests['observed_native_mean_entries']
assert counts==dict(force_started=33,force_completed=33,tangent_started=22,tangent_completed=22)
bytest=tests['observed_native_mean_entries_by_test']
assert len(bytest)==4
assert all(name in selected for name in bytest)

# Historical protocol paths and records stay historical; no archived array bytes.
oldrel='lf_data_preparation/native_interface_001/saved_continuation_001'
old=read(oldrel+'/protocol.json')
assert len(old['bindings'])==100
intersection=sorted(set(old['bindings']).intersection(expected))
assert intersection==[]
old_ordinary={}
old_NPZ_declared={}
for name,pin in old['bindings'].items():
    if Path(name).suffix.lower()=='.npz':
        old_NPZ_declared[name]=pin
    else:
        assert sha(ordinary(name))==pin
        old_ordinary[name]=pin
parent=read(old['parent_result'])
assert reviewed[old['parent_result']]==old['bindings'][old['parent_result']]
assert parent['status']=='failed' and parent['failure']['code']=='time_limit'
assert parent['accepted_states']==14
assert parent['target_reached'] is parent['path_completed'] is parent['task_target_executed'] is False
assert parent['independent_HP_qualified'] is parent['equilibrium_qualified'] is parent['HF_qualified'] is False
for name in ('RESULTS.md','run_001/forward/fixed_square/result.json'):
    # Actual original forward folder is not guessed; only existing ordinary record names are included.
    if (ROOT/oldrel/name).exists() and Path(name).suffix!='.npz':ordinary(oldrel+'/'+name)
identity=read(REL+'/author/source_identity_migration_review.json')
migration={}
for label,row in identity['references'].items():
    summary=read(row['summary_path'])
    old_response=read(row['saved_response_path'])
    assert reviewed[row['summary_path']]==row['summary_sha256']
    assert reviewed[row['saved_response_path']]==row['saved_response_sha256']
    mismatches=[]
    for name,pin in summary['source_bindings'].items():
        if sha(ordinary(name))!=pin:mismatches.append(name)
    if label in ('right2','right4'):
        assert sorted(mismatches)==['hf_repo/src/hf_eval/native_mean.py','hf_repo/src/hf_eval/split_displacement.py']
    else:assert mismatches==[]
    assert old_response['independent_reference']['accepted_reference_pass'] is True
    assert old_response['independent_reference']['full_path_reference_pass'] is True
    migration[label]=dict(summary_source_binding_count=len(summary['source_bindings']),
        current_source_mismatches=mismatches,saved_qualified_response_byte_preserved=True,
        saved_summary_pass=summary['status']=='pass',saved_HP_completed=summary['HP_calls_completed'],
        runtime_test_of_current_summary=(label=='right4'),
        runtime_test_evidence='Frozen source-migration test call passed; no second summary/API invocation by reviewer.' if label=='right4' else
            'Source-byte/old ordinary response audit only; no new summary/API invocation or HP.')

md=f'''# M-INTEGRATE1 实际终态独立审阅

唯一 launcher 已由主任务的实际 handle 确认退出，本审阅读取保存回执后结论为 PASS。outer exit0、stopNone，实际 {outer['elapsed_seconds']} 秒，tree RSS {outer['peak_sampled_tree_RSS_bytes']} B；helper {helper['elapsed_seconds']} 秒／{helper['peak_sampled_RSS_bytes']} B；pytest child terminal {helper['focused_tests_terminal']['elapsed_seconds']} 秒，plugin {tests['elapsed_seconds']} 秒／{tests['peak_sampled_RSS_bytes']} B。均在原180／300／360秒与采样8GiB合同内。

11份安装实际完成，目标源码 SHA 与候选／回执一致；全部58项运行包身份（52模块、2CLI、4测试）一致。108份本卡不可变绑定和6份原源码快照保持；快照也与发布前 Git `{COMMIT}` 对应字节一致。实际26个 HF 导入模块均来自默认包，原 material／Hu／NumPy切线／组装等核源码没有改变。

实际收集顺序与25个冻结选择完全一致，75项setup／call／teardown全部passed；XML为25 tests、0 errors／failures／skipped，stdout记录“25 passed in 6.62s”。这是唯一测试调用，未重试。新增typed settings、三个CLI参数运输以及严格来源迁移断言均通过。

原记录的 NativeMean NumPy aliases 为 F started／completed=33／33，T=22／22；来自四个小模型测试，其中保存态读回／续算16／16与10／10，两个零起点／缓存测试各4／4与3／3，mechanical chunk256为9／9与6／6。共有7次受监测建模记录，均16单元／50DOF。它们不是全部底层内核调用总数；synthetic／mock callbacks另有其合同，也不是原13440单元夹持器本轮复算。

来源迁移实际 right4 测试 passed，断言原production摘要仍success、当前参考严格mismatch、原qualified响应／参考／结果字节不变。只读源 SHA也确认right2／right4均仅mean与split两条失配。right2没有额外当前摘要测试，M-REF2的12条实际参考源均仍匹配；没有额外API总结或HP。

精确核对旧 M-RESUME1 的100个 bindings路径与本次11个target：交集为0。旧 Mean／controller／CLI等pins绑定闭卡candidate路径，未被默认安装覆盖。本次核了其中{len(old_ordinary)}份非NPZ字节；{len(old_NPZ_declared)}份NPZ只复制原声明pin，不读取或复审数组。不能把这个核对说成旧100数组重新通过。原默认6份源码通过本卡baseline与Git保留，原M-RESUME1协议／候选／结果仍为历史记录。

原 M-ALPHA1 result仍failed／time_limit、14接受加载态、完整路径与task target执行false、HP／equilibrium／HF资格false。集成通过使已验证的Mean／API／CLI保存态续算进入默认入口，并支持本卡有限回归；不会修饰父NOT_PASS，也不证明完整卸载、压力、有效夹持力、网格稳定性、全部切线列或HF5。

本审阅仅普通JSON／XML／stdout与源码字节核对，没有HF导入、collect、测试重跑、NPZ读取、F/T/HP/solver/observer／绘图或正式仓库修改。
'''
mdp=EXT/'EXECUTION_TERMINAL_REVIEW.md'
with mdp.open('x',encoding='utf-8',newline='\n') as out:out.write(md)
report=dict(schema_version='MINTEGRATE1-execution-terminal-independent-review-1.0',
    status='pass_actual_terminal_and_installed_contract_review_no_new_scientific_gate',
    created_utc=datetime.now(timezone.utc).isoformat(),execution_status='pass',
    actual_source_commit=COMMIT,protocol_sha256=PIN,
    outer_sha256=reviewed[REL+'/integration_launch.json'],
    parent_root_terminal_notice='Root confirmed sole session42055 polled terminal exit0; no live conclusion from file existence.',
    outer={key:outer[key] for key in ('status','invocations','exit_code','elapsed_seconds','child_terminal_wall_seconds',
        'peak_sampled_tree_RSS_bytes','stop_reason','immutable_bindings_unchanged')},
    helper={key:helper[key] for key in ('status','focused_tests_started','focused_tests_completed','elapsed_seconds',
        'peak_sampled_RSS_bytes','installation_complete','failure','old_frozen_records_rewritten',
        'new_pressure_clamp_stability_HF5_qualified')},
    tests=dict(status=tests['status'],collected_selectors=tests['collected_selectors'],passed_calls=25,
        setup_call_teardown_reports=75,XML_suite_attributes=suite.attrib,
        stdout_saved_summary='25 passed in 6.62s',plugin_seconds=tests['elapsed_seconds'],
        child_terminal=helper['focused_tests_terminal'],peak_sampled_RSS_bytes=tests['peak_sampled_RSS_bytes'],
        imported_HF_modules=tests['imported_HF_modules'],observed_models=tests['observed_models'],
        NativeMean_alias_counts=counts,NativeMean_alias_counts_by_test=bytest,
        accounting_scope=tests['accounting_scope'],qualification_scope=tests['qualification_scope']),
    installation=dict(installed=helper['installed'],runtime_identities=protocol['installed_runtime_SHA256'],
        old_source_snapshots=snapshots,immutable_bindings_count=108),
    old_MRESUME1_binding_scope=dict(declared_count=100,installed_target_intersection=intersection,
        checked_non_NPZ_count=len(old_ordinary),NPZ_declared_only_count=len(old_NPZ_declared),
        NPZ_declared_pins_not_read=old_NPZ_declared,
        explanation='Old production candidate pins have stage-relative candidate paths; default installation does not overwrite them. No whole-100 array re-audit claim.'),
    reference_migration=migration,
    original_parent=dict(path=old['parent_result'],sha256=reviewed[old['parent_result']],
        status=parent['status'],failure_code=parent['failure']['code'],accepted_states=14,
        target_reached=False,path_completed=False,task_target_executed=False,
        independent_HP_qualified=False,equilibrium_qualified=False,HF_qualified=False),
    reviewed_repository_SHA256=reviewed,findings=[],blockers=[],
    reviewer_actions=dict(HF_import=0,collect=0,tests_or_retry=0,NPZ_byte_read_or_decode=0,
        F_T_HP_solver_observer_plot=0,formal_mutation=0),
    qualification='Actual default-source installation plus this exact finite compatibility set; no original gripper/HP/pressure/effective grip/stability/full-column/HF5 upgrade.',
    documentation_sha256=sha(mdp))
jp=EXT/'execution_terminal_review.json'
with jp.open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=report['status'],JSON_SHA256=sha(jp),MD_SHA256=sha(mdp),
    outer_sha256=report['outer_sha256'],ordinary_reviewed_files=len(reviewed),
    old_MRESUME1_bindings=dict(intersection=intersection,ordinary=len(old_ordinary),NPZ_declared_only=len(old_NPZ_declared)))))
