"""Review frozen text and already-saved ordinary records only."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

EXT=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/saved_integration_001'
OLDREL='lf_data_preparation/native_interface_001/saved_continuation_001'
COMMIT='2b550d09f4347240ef6cb626b4c829566b638e61'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
reviewed={}
def ordinary(name):
    p=ROOT/name
    assert p.suffix.lower()!='.npz'
    reviewed[name]=sha(p)
    return p
def read(name):return json.loads(ordinary(name).read_bytes())
docs=[REL+'/RESULTS.md',REL+'/NEXT_STEP_REVIEW.md','docs/CURRENT_STATUS.md',
      'docs/RESUME_DEVELOPMENT.md','hf_repo/README.md','docs/NATIVE_EVALUATION_INTERFACE.md']
texts={name:ordinary(name).read_text(encoding='utf-8') for name in docs}
entry=read(REL+'/author/installed_entry_documentation_receipt.json')
closure=read(REL+'/author/execution_documentation_receipt.json')
assert closure['execution_status']=='pass' and closure['execution_closed'] is True
assert closure['results_sha256']==reviewed[REL+'/RESULTS.md']=='21d9a0fdbbd3d3989970a48cb07b9de5caf3d40ba26f3f7d27333f428872f63b'
assert closure['next_step_sha256']==reviewed[REL+'/NEXT_STEP_REVIEW.md']=='5430e68cce14bfeb3c070cb59e7314a7b1d51c35f51c381ce56e7313db0c6a83'
history=[]
prefixes={}
for row in closure['front_history']+entry['front_history']:
    name=row['path']
    old=subprocess.check_output(['git','show',COMMIT+':'+name],cwd=ROOT)
    new=(ROOT/name).read_bytes()
    assert len(old)==row['old_bytes'] and sha256(old).hexdigest()==row['old_sha256']
    assert sha256(new).hexdigest()==row['new_sha256']
    assert new.count(old)==1
    assert new[row['history_start_byte']:row['history_end_byte_exclusive']]==old
    history.append(dict(path=name,old_sha256=row['old_sha256'],new_sha256=row['new_sha256'],
        old_bytes=len(old),old_raw_occurrences=1,history_start_byte=row['history_start_byte'],
        history_end_byte_exclusive=row['history_end_byte_exclusive']))
    prefixes[name]=new[:row['history_start_byte']].decode('utf-8')
assert len(history)==4
links=[]
for name,text in texts.items():
    # Code fences are examples, not Markdown links. No targets are executed.
    visible=re.sub(r'```.*?```','',text,flags=re.S)
    for match in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)',visible):
        raw=match.group(1).strip()
        if raw.startswith('<'):
            dest=raw[1:raw.find('>')]
        else:
            dest=raw.split(' "',1)[0].split(" '",1)[0]
        if dest.startswith(('http://','https://','mailto:','codex:','chatgpt-','app:')) or dest.startswith('#'):
            continue
        dest=unquote(dest.split('#',1)[0])
        target=(ROOT/name).parent/dest
        assert target.exists(), (name,raw,str(target.resolve()))
        links.append(dict(source=name,target_literal=raw,resolved=target.resolve().relative_to(ROOT).as_posix(),exists=True))

outer=read(REL+'/integration_launch.json')
helper=read(REL+'/run_001/execution_receipt.json')
tests=read(REL+'/run_001/focused_test_receipt.json')
original=read(OLDREL+'/run_001/resumed_alpha_half/result.json')
viewer=read(OLDREL+'/run_001/view/resumed_alpha_half/summary.json')
assert len(original['states'])==len(viewer['rows'])==2
actual=[]
for i,(state,row) in enumerate(zip(original['states'],viewer['rows'])):
    fields=dict(d_mm=state['d'],R_input_N=state['R_input'],q_out_mm=state['q_out'],
        lower_body_total_Fy_N=state['workpiece']['force_on_lower_body_N']['total'][1],
        finite_tip_bottom_mm=row['tip_to_bottom_mm'])
    assert fields['d_mm']==row['d_mm']
    for key,value in fields.items():
        if key=='d_mm':continue
        assert repr(value) in texts[REL+'/RESULTS.md'],(key,value)
    actual.append(dict(index=i,original_target_index=state['original_target_index'],
        leg=state['leg'],saved_state_sha256=state['state_sha256'],fields=fields))
figures=[]
for name in ('comparison.png','distances_forces.png','peak_fields.png','resumed_alpha_half/actual_states.gif'):
    rel=OLDREL+'/run_001/view/'+name
    p=ordinary(rel)
    figures.append(dict(path=rel,sha256=reviewed[rel],exists=p.exists(),
        scope='Existing raw figure identity only; reviewer did not render, decode, or inspect pixels.'))
for value in (outer['elapsed_seconds'],outer['peak_sampled_tree_RSS_bytes'],helper['elapsed_seconds'],
    helper['peak_sampled_RSS_bytes'],tests['elapsed_seconds'],tests['peak_sampled_RSS_bytes'],
    helper['focused_tests_terminal']['elapsed_seconds']):
    assert repr(value) in texts[REL+'/RESULTS.md']
assert tests['passed_calls']==25 and len(tests['reports'])==75
assert 'F33/33、T22/22' in texts[REL+'/RESULTS.md']
assert '100个bindings路径与本次11target交集为0' in texts[REL+'/RESULTS.md']
assert '98非NPZ字节' in texts[REL+'/RESULTS.md'] and '2NPZ只保留原声明pin' in texts[REL+'/RESULTS.md']
nexttext=texts[REL+'/NEXT_STEP_REVIEW.md']
assert '先只读核查' in nexttext and '尚未形成或执行下一张计算卡' in nexttext
assert '本文件只记录下一步取舍' in nexttext
for name,prefix in prefixes.items():
    assert '未' in prefix and ('资格' in prefix or 'NOT_PASS' in prefix)
interface=prefixes['docs/NATIVE_EVALUATION_INTERFACE.md']
assert '不保证任务能在示意时限内完成' in interface
assert '不是 Newton trial 序号' in interface
assert '不能笼统称所有失败都恢复至父锚点' in interface
assert '当前源码' in prefixes['hf_repo/README.md']

md='''# M-INTEGRATE1 执行文档独立审阅

RESULTS、NEXT_STEP、两份当前状态前缀及两份默认入口说明与实际终态记录一致。25项／75阶段、11安装／58运行身份／26导入、F33/33与T22/22的有限aliases范围、6合成／15mock／4真实小模型以及资源数值没有扩张；98普通旧绑定与2份NPZ未复审的边界也保留。

峰值／首次下降表中的R、q_out、下半工件total Fy和有限tip-bottom距离逐项引用原M-RESUME1普通保存JSON及viewer摘要。三PNG与2帧GIF只核已存在原文件和raw SHA，没有新图、数组读取或像素审阅声明。原父NOT_PASS、child短段success、无新alpha HP与压力／有效夹持／稳定性／全列／HF5不升级的含义准确。

四个入口／状态front的发布前完整raw均在当前文件中精确出现一次，位置与各自journal一致。全部被审六份Markdown的本地链接（包含保留历史）均指向存在文件；代码示例未执行，路径和时间例明确为未来用法而非保证或授权。

NEXT_STEP仅选择只读审查现有参考接口、保存结构和成本；明确尚未形成或执行下一张计算卡，不声称完成新参考准备。此路线与新alpha缺独立参考的事实相符。

结论：文档静审通过，无阻断。此次仅普通文本／JSON、Git原字节、文件存在与raw SHA核对；未import HF、collect、测试、NPZ读取、总结API、F/T/HP／solver／observer或绘图，未修改正式仓库。
'''
mdp=EXT/'DOCUMENTATION_EXECUTION_REVIEW.md'
with mdp.open('x',encoding='utf-8',newline='\n') as out:out.write(md)
report=dict(schema_version='MINTEGRATE1-execution-documentation-independent-review-1.0',
    status='pass_actual_execution_documentation_static_review_ordinary_only',
    created_utc=datetime.now(timezone.utc).isoformat(),execution_status='pass',
    reviewed_repository_SHA256=reviewed,reviewed_document_paths=docs,
    front_history=history,local_links=links,local_link_count=len(links),
    actual_saved_state_table_sources=actual,existing_figure_identities=figures,
    findings=[],blockers=[],
    next_step_scope='Read-only existing independent-reference source/saved-input/cost audit only; no new card preparation or numerical/HP authorization claimed.',
    scope='Documentation consistency and preservation only; no new mechanics or qualification.',
    reviewer_actions=dict(HF_import=0,collect=0,tests=0,NPZ_read_or_decode=0,summary_API=0,
        F_T_HP_solver_observer_render=0,formal_mutation=0),documentation_sha256=sha(mdp))
jp=EXT/'documentation_execution_review.json'
with jp.open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=report['status'],JSON_SHA256=sha(jp),MD_SHA256=sha(mdp),
    local_links=len(links),preserved_fronts=len(history),ordinary_reviewed_files=len(reviewed))))
