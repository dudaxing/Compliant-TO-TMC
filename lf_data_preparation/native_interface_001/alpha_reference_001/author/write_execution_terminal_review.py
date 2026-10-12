"""Verify already-saved ordinary terminal records, not scientific archives."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

EXT=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/alpha_reference_001'
OUT=REL+'/run_001/reference'
PIN='b373b2cedffff1f0b93ff6426645ab6507f2b7556e90c9068110ecf883b85673'
COMMIT='e687bdf1ca60edbd0fd044f4f8c990b3b9ccc182'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
reviewed={}
declared_scientific={}
def ordinary(name):
    p=ROOT/name
    assert p.suffix.lower() not in ('.npz','.npy','.gz')
    reviewed[name]=sha(p)
    return p
def read(name):return json.loads(ordinary(name).read_bytes())
protocol=read(REL+'/protocol.json')
assert reviewed[REL+'/protocol.json']==PIN
outer=read(REL+'/reference_launch.json')
life=read(OUT+'/lifecycle.json')
summary=read(OUT+'/summary.json')
authorization=read(REL+'/author/authorization.json')
reply=read(REL+'/author/direct_human_reply.json')
proof=read(REL+'/author/source_publication_receipt.json')
assert authorization['authorized'] is authorization['authorization_from_direct_human_reply'] is True
assert reply['authorization_from_direct_human_reply'] is True
assert authorization['card']==reply['card']==proof['prepared_card']==outer['card']=='M-AREF1'
assert authorization['direct_human_answer']==reply['direct_human_answer']=='批准按 M-AREF1 卡执行'
assert reply['reply_context']=='Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction'
assert authorization['approved_source_commit']==reply['approved_source_commit']==proof['published_commit']==outer['approved_source_commit']==COMMIT
assert authorization['protocol_sha256']==proof['protocol_sha256']==outer['protocol_sha256']==PIN
assert authorization['human_evidence_sha256']==reviewed[REL+'/author/direct_human_reply.json']
assert authorization['source_publication_receipt_sha256']==reviewed[REL+'/author/source_publication_receipt.json']
assert authorization['invocations_authorized']==outer['invocations']==1
assert authorization['accepted_states_authorized']==2 and authorization['HP_calls_authorized']==4
assert authorization['retries']==0
assert authorization['force'] is authorization['extension'] is authorization['repair_rerun'] is False
assert outer['status']==life['status']==summary['status']=='pass'
assert outer['exit_code']==0 and outer['stop_reason'] is None and life['error'] is None
assert outer['helper_status']=='pass' and outer['all_bindings_unchanged'] is True
assert life['HP_calls_started']==life['HP_calls_completed']==summary['HP_calls_started']==summary['HP_calls_completed']==4
assert life['accepted_mechanical_states_completed']==life['workpiece_states_completed']==summary['accepted_states']==2
assert life['checks_completed']==summary['checks_completed']==161495
assert life['time_limit_seconds']==summary['time_limit_seconds']==900
assert outer['outer_seconds']==960 and outer['elapsed_seconds']<=960
assert outer['child_terminal_wall_seconds']<=900 and life['elapsed_seconds']<=900 and summary['elapsed_seconds']<=900
assert max(outer['peak_sampled_tree_RSS_bytes'],life['sampled_peak_RSS_bytes'],summary['sampled_peak_RSS_bytes'])<=8589934592
assert life['sampled_RSS_limit_bytes']==summary['sampled_RSS_limit_bytes']==outer['sampled_RSS_limit_bytes']==8589934592
assert len(protocol['bindings'])==48
for name,pin in protocol['bindings'].items():
    assert summary['input_bindings'][name]==pin
    if Path(name).suffix.lower() in ('.npz','.gz','.npy'):
        declared_scientific[name]=dict(sha256=pin,scope='Declared only; no raw read/hash/decode by reviewer.',exists=(ROOT/name).is_file())
        assert declared_scientific[name]['exists']
    else:assert sha(ordinary(name))==pin
assert len(protocol['reference_sources'])==11 and len(summary['source_bindings'])==12
for name,pin in summary['source_bindings'].items():
    assert sha(ordinary(name))==pin
    copy_name=OUT+'/sources/'+Path(name).name
    assert sha(ordinary(copy_name))==pin
assert {name:pin for name,pin in summary['source_bindings'].items() if name in protocol['reference_sources']}==protocol['reference_sources']
assert sha(ordinary(OUT+'/protocol.json'))==PIN
for name,pin in summary['input_bindings'].items():
    if Path(name).suffix.lower() in ('.npz','.gz','.npy'):
        assert (ROOT/name).is_file()
        declared_scientific[name]=dict(sha256=pin,exists=True,scope='Declared only; no raw read/hash/decode by reviewer.')
    else:assert sha(ordinary(name))==pin

core='lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference_author/core_audit_mechanical.py'
tree=ast.parse(ordinary(core).read_text(encoding='utf-8'))
gate_node=next(n.value for n in tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='GATES' for t in n.targets))
gates={n.arg:ast.literal_eval(n.value) for n in gate_node.keywords}
assert len(gates)==15 and summary['gates']==protocol['gates']==gates
assert summary['global_scatter_precision']==3000 and summary['global_scatter_inexact_trap'] is True
assert summary['direction']==protocol['direction']
assert summary['full_element_and_DOF_coverage'] is True
for key in ('HP_matrix_columns_exhaustively_checked','full_original_path_reference_pass',
    'full_original_path_completed','contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified'):
    assert summary[key] is False
assert summary['auxiliary_material_energy']==dict(status='not_evaluated',qualified=False,field_present=False)
assert summary['response_mode']=='mechanical'
assert 'no candidate energy comparison' in summary['analytic_HP_energy_scope']
assert summary['production_response_unchanged'] is True
assert all(summary[key]==0 for key in ('candidate_force_calls','tangent_calls','solver_calls','model_constructions','JIT_calls','LF_calls'))

origin=ROOT/protocol['production_stage']/protocol['production_result_dir']
result_name=(origin/'result.json').relative_to(ROOT).as_posix()
result=read(result_name)
assert reviewed[result_name]==summary['result_sha256']==protocol['bindings'][result_name]
assert summary['continuation']==result['continuation']
assert result['status']=='success' and result['full_original_path_completed'] is result['task_target_executed'] is False
parent_name='lf_data_preparation/native_interface_001/regularization_sensitivity_001/run_001/alpha_half/result.json'
parent=read(parent_name)
assert parent['status']=='failed' and parent['failure']['code']=='time_limit' and parent['accepted_states']==14
assert parent['path_completed'] is parent['task_target_executed'] is False
mapping=[]
def check_saved_gate(record, expected_limit=None):
    assert record['pass_gate'] is True
    value,limit=Decimal(record['normalized_error']),Decimal(record['limit'])
    assert value.is_finite() and value<=limit
    if expected_limit is not None:assert limit==Decimal(expected_limit)
    if 'hp80_hp120_error' in record:
        agreement=Decimal(record['hp80_hp120_error'])
        assert agreement.is_finite() and agreement<=Decimal(record['reference_limit'])==Decimal(gates['hp80_hp120'])
    if 'maximum_hp80_hp120_error' in record:
        assert Decimal(record['maximum_hp80_hp120_error'])<=Decimal(gates['hp80_hp120'])

for child,(record,row,execution) in enumerate(zip(summary['states'],result['states'],(13,14))):
    assert record['index']==record['child_accepted_index']==child
    assert record['reference_execution_index']==record['original_target_index']==execution
    assert record['child_original_target_index']==child
    assert record['target_mm']==row['d']==protocol['targets_mm'][child]
    assert record['state_sha256']==row['state_sha256']
    assert record['descriptor_file_sha256']==row['descriptor_file_sha256']
    assert record['leg']==row['leg']==('resume_origin' if child==0 else 'unloading')
    assert record['continuation_anchor']==(child==0)
    assert record['status']=='pass' and record['HP_calls']==2
    assert record['elements_compared']==13440 and record['global_DOFs_compared']==27378
    assert record['local_force_entries_compared']==record['local_tangent_entries_compared']==322560
    assert record['full_matrix_entries_assembly_checked']==860160
    raw=read(OUT+f'/accepted_{execution:03d}/summary.json')
    assert raw['index']==execution and raw['original_target_index']==execution
    metadata_added={'child_accepted_index','reference_execution_index','descriptor_file_sha256',
        'child_original_target_index','continuation_anchor'}
    compare={key:value for key,value in record.items() if key not in metadata_added}
    compare['index']=execution
    assert compare==raw
    for part in ('total','material','regularization'):
        check_saved_gate(record['force_checks'][part],gates[part+'_force'])
        check_saved_gate(record['tangent_checks'][part],gates[part+'_tangent'])
    for group,kind in (('local_force_worst','force'),('local_tangent_worst','tangent')):
        assert len(record[group])==3
        for error in record[group]:check_saved_gate(error,gates[error['component']+'_'+kind])
    check_saved_gate(record['CSC_total_action_check'],gates['total_tangent'])
    check_saved_gate(record['augmented_checks']['force'],gates['augmented_force_tangent'])
    check_saved_gate(record['augmented_checks']['constraint'],gates['augmented_constraint_tangent'])
    for error in record['checks']:check_saved_gate(error)
    assert Decimal(record['metrics']['minimum_J'])>0
    assert [ref['path'] for ref in record['references']]==[f'accepted_{execution:03d}/hp{precision}_full_local.json.gz' for precision in (80,120)]
    for key,value in record.items():
        if isinstance(value,dict) and 'path' in value and 'sha256' in value:
            name=OUT+'/'+value['path']
            assert (ROOT/name).is_file()
            if Path(name).suffix.lower() in ('.npz','.npy','.gz'):
                declared_scientific[name]=dict(sha256=value['sha256'],exists=True,scope='Ordinary summary declaration only; scientific archive not read/hash/decode.')
    for ref in record['references']:
        name=OUT+'/'+ref['path']
        assert (ROOT/name).is_file()
        declared_scientific[name]=dict(sha256=ref['sha256'],exists=True,scope='Ordinary summary declaration only; HP archive not read/hash/decode.')
    mapping.append(deepcopy(record))

stdout_name=REL+'/reference_stdout.log'
stdout=ordinary(stdout_name).read_text(encoding='utf-8')
printed=[ast.literal_eval(line) for line in stdout.splitlines() if line.strip()]
assert printed==[dict(status='pass',accepted_states=2,HP_calls=4,checks_completed=161495)]

def abbrev(value):
    """Text prefix only, no numerical rounding or new physical calculation."""
    value=str(value)
    if 'E' in value:
        coefficient,exponent=value.split('E')
        return coefficient[:13]+'…E'+exponent if len(coefficient)>13 else value
    return value[:28]+'…' if len(value)>28 else value
error_rows=[]
for kind,label in (('force_checks','全局力'),('tangent_checks','全局PORT切线action')):
    for part in ('total','material','regularization'):
        error_rows.append('| '+label+' '+part+' | '+abbrev(mapping[0][kind][part]['normalized_error'])+' | '+
            abbrev(mapping[1][kind][part]['normalized_error'])+' | '+mapping[0][kind][part]['limit']+' |')
md=f'''# M-AREF1 两态独立参考实际终态审阅

唯一session54727已由主任务handle确认terminal exit0；本审阅核保存普通记录后结论PASS。outer一次调用、stopNone、{outer['elapsed_seconds']}秒，child实际终止壁钟{outer['child_terminal_wall_seconds']}秒；lifecycle {life['elapsed_seconds']}秒、summary {summary['elapsed_seconds']}秒。tree采样峰{outer['peak_sampled_tree_RSS_bytes']}B，helper峰{life['sampled_peak_RSS_bytes']}B；900／960秒、采样8GiB原窗口满足。原代码检查计数{life['checks_completed']}与本审阅的普通身份／门值核对不同。

新HP开始／完成4／4，两个mechanical／body态完成。每态HP80／120各一次，全13440元素／27378DOF，局部三分量力及方向action各322560项、完整CSC组装身份860160项。raw accepted013／014的index保持13／14，新顶层child0／1附reference_execution_index13／14，与原stateSHA、descriptor、绝对d1.20／1.15及resume_origin／unloading身份一致。首态是已保存峰的复核，不是新未变形origin。

## 已保存实际误差

下表只截取原Decimal字符串前缀（省略号），没有重算或数值圆整。完整字符串、分母、HP80／120 agreement、局部最坏记录和KKT／CSC保存在本报告JSON的actual_states及原两份普通summary；这些是原归一化误差，不能说成工件标量百分比。

| 检查 | 峰值原13 | 首次下降原14 | 原限值 |
|---|---|---|---|
'''+ '\n'.join(error_rows)+f'''

两态独立HP120残差分别为{abbrev(mapping[0]['metrics']['independent_relative_residual'])}、{abbrev(mapping[1]['metrics']['independent_relative_residual'])}，原门1e−8；最低J分别{abbrev(mapping[0]['metrics']['minimum_J'])}、{abbrev(mapping[1]['metrics']['minimum_J'])}，原正J检查通过。局部regularization PORT最坏误差为{abbrev(mapping[0]['local_tangent_worst'][2]['normalized_error'])}／{abbrev(mapping[1]['local_tangent_worst'][2]['normalized_error'])}，原1e−9；该记录不是新的Hu primitive误差门。

原十五GATES与冻结协议及B850声明相同。每个普通记录的pass_gate、原error／limit／HP agreement值都按原门核对，包括单态local每分量已保存maximum_hp80_hp120_error；未增加门、换方向或放宽floor。工件body检查完成2态，源程序在同一HP力上执行signed总／材料／Hu、去重holding／重叠／镜像和dummy内部门；其数值明细只在gz，因此本审阅没有读这些body误差值或伪称重审其全文。

## 来源、关闭与资格

直接人类批准、源发布proof／提交{COMMIT}、协议和实际outer身份一致。48原bindings中38普通文件／源码原字节核对，10NPZ只核普通声明与存在，不读取／hash数组。十一原依赖与自身driver合计12 source_bindings及其12个归档源码副本逐字节相同。额外科学产物只检查普通summary声明和存在；NPZ／gz未打开，也不声称原HP全文／数组重新审计。

本次PASS支持这两个精确alpha5e−7保存接受态的三分量力、声明PORT解析切线作用、完整保存CSC组装身份、KKT／平均约束／固定／平衡与工件弱式投影。全CSC identity不等于所有列独立HP；不授压力、有效夹持、stress-HP、energy-gradient、稳定性、拒绝trial、整个原路径或HF5。机械辅助材料能量仍not_evaluated／qualified=false／absent，独立解析材料能量仅归档。

原父M-ALPHA1仍failed／time_limit、14加载态且path/task false；child短段成功不拼成一次完整原路径通过。生产result／response原字节不改，本卡没有调用API关联、原模型F/T／构模／平衡求解、LF或新图。“JIT_calls0”按已冻结科学scope仅指无AD数据求值／JIT编译／本构执行；import会注册JAX变换wrappers。该零额外科学执行结论来自冻结源闭包及记录，不是全库动态hook计数。

此次审阅只有已产普通JSON／stdout和源码原字节、保存值与原门比较，没有HF import、测试、NPZ／gz读取、HP或F/T重跑、solver／observer／绘图，也没有正式仓库修改。卡窗口已关闭；后续关联或展示需另定明确范围。
'''
mdp=EXT/'EXECUTION_TERMINAL_REVIEW.md'
with mdp.open('x',encoding='utf-8',newline='\n') as out:out.write(md)
report=dict(schema_version='MAREF1-actual-terminal-independent-ordinary-review-1.0',
    status='pass_actual_saved_two_state_reference_terminal_review_no_new_scientific_gate',
    created_utc=datetime.now(timezone.utc).isoformat(),execution_status='pass',execution_closed=True,
    outer_sha256=reviewed[REL+'/reference_launch.json'],protocol_sha256=PIN,approved_source_commit=COMMIT,
    actual_terminal_notice='Root polled sole session54727 terminal exit0; no live or terminal inference from file existence.',
    outer=outer,lifecycle=life,summary_sha256=reviewed[OUT+'/summary.json'],summary_elapsed_seconds=summary['elapsed_seconds'],
    gates=gates,actual_states=mapping,
    source_bindings=summary['source_bindings'],source_capsule_count=11,source_with_driver_count=12,
    original_input_binding_count=48,inherited_NPZ_declared_only_count=10,
    input_bindings=summary['input_bindings'],scientific_artifact_declarations_not_read=declared_scientific,
    qualification_scope=summary['qualification'],reference_scope=summary['reference_scope'],
    flags={key:summary[key] for key in ('full_element_and_DOF_coverage','HP_matrix_columns_exhaustively_checked',
        'full_original_path_reference_pass','full_original_path_completed','contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified')},
    mechanical_availability={key:summary[key] for key in ('response_mode','response_contract','force_kernel_version','auxiliary_material_energy')},
    analytic_HP_energy_scope=summary['analytic_HP_energy_scope'],production_response_unchanged=True,
    original_parent=dict(status=parent['status'],failure=parent['failure']['code'],accepted_states=parent['accepted_states'],
        path_completed=parent['path_completed'],task_target_executed=parent['task_target_executed']),
    JAX_registration_scope='Import registers jacfwd/jit/vmap/custom_jvp wrappers; zero scientific JIT/AD means no data evaluation, JIT compilation or constitutive execution, not zero wrapper registration calls.',
    saved_body_check_review_scope='Two actual workpiece completions plus unchanged checker source; gz body numerical details not read.',
    reviewed_repository_SHA256=reviewed,findings=[],blockers=[],
    reviewer_actions=dict(HF_import=0,tests_collect_retry=0,NPZ_raw_read_hash_header_decode=0,gzip_scientific_read=0,
        new_HP_F_T_solver_observer_plot=0,new_physical_difference_ratio_or_gate=0,formal_mutation=0),
    documentation_sha256=sha(mdp))
jp=EXT/'execution_terminal_review.json'
with jp.open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=report['status'],JSON_SHA256=sha(jp),MD_SHA256=sha(mdp),outer_sha256=report['outer_sha256'],
    ordinary_reviewed_files=len(reviewed),scientific_declared_only=len(declared_scientific))))
