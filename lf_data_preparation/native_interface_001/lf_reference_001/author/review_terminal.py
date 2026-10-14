"""Ordinary-record-only independent terminal audit; no science/media opens."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
OUT = Path('D:/hf-native-workpiece-api-author-20261014/LF_REFERENCE_execution_001')
STAGE = ROOT/'lf_data_preparation/native_interface_001/lf_reference_001'
RUN = STAGE/'run_001/reference'
EXPECTED_SOURCE = '799bdc9709fa2fc92f573f3801b243f24e370983'
EXPECTED_PROTOCOL = 'd6512016bc169183e6f857d0bab18185aa66e1aec3847ccbdb30a9450b9a2125'
ordinary = {}
blocking = []
checks = []
def science(p):
    return p.suffix.lower() in {'.npz','.gz','.png','.gif','.csv','.jpg','.jpeg','.webp','.pdf'}
def raw(p):
    assert not science(p), 'Science/media bytes are prohibited in terminal review'
    data=p.read_bytes()
    ordinary[p.relative_to(ROOT).as_posix()]=hashlib.sha256(data).hexdigest()
    return data
def read(p):
    return json.loads(raw(p))
def ck(condition, name):
    checks.append(dict(name=name,passed=bool(condition)))
    if not condition: blocking.append(name)
def decimal_gate(value, limit):
    d=Decimal(str(value)); g=Decimal(str(limit))
    return d.is_finite() and g.is_finite() and Decimal(0)<=d<=g

protocol=read(STAGE/'protocol.json')
outer=read(STAGE/'reference_launch.json')
receipt=read(RUN/'execution_receipt.json')
lifecycle=read(RUN/'lifecycle.json')
summary=read(RUN/'summary.json')
observation=read(RUN/'reference_observations.json')
auth=read(STAGE/'author/authorization.json')
reply=read(STAGE/'author/direct_human_reply.json')
proof=read(STAGE/'author/source_publication_receipt.json')
stdout=raw(STAGE/'reference_stdout.log').decode('utf8')
source=raw(STAGE/'execute_partial_reference.py').decode('utf8')
launcher_source=raw(STAGE/'launch_reference.py').decode('utf8')
raw(STAGE/'plot_partial_reference_observation.py')
raw(STAGE/'L-REF1_CARD.md')

ck(ordinary[(STAGE/'protocol.json').relative_to(ROOT).as_posix()]==EXPECTED_PROTOCOL,'actual frozen protocol SHA')
ck(outer['status']=='pass' and outer['completed_utc'] and outer['invocations']==1 and outer['exit_code']==0 and outer['stop_reason'] is None,'actual single outer terminal PASS')
ck(outer['protocol_sha256']==receipt['protocol_sha256']==auth['protocol_sha256']==proof['protocol_sha256']==EXPECTED_PROTOCOL,'protocol identity chain')
ck(outer['authorized_execution_source_commit']==receipt['authorized_execution_source_commit']==auth['authorized_execution_source_commit']==reply['authorized_execution_source_commit']==proof['published_commit']==EXPECTED_SOURCE,'authorized source identity chain')
ck(auth['authorized'] is True and auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True and auth['direct_human_answer']==reply['direct_human_answer']=='批准','actual direct human approval recorded')
ck(auth['human_evidence_sha256']==ordinary[(STAGE/'author/direct_human_reply.json').relative_to(ROOT).as_posix()] and auth['source_publication_receipt_sha256']==ordinary[(STAGE/'author/source_publication_receipt.json').relative_to(ROOT).as_posix()],'actual authority ordinary byte bindings')
ck(proof['status']=='published_and_incrementally_restored_pass' and proof['prepared_card']=='L-REF1','published restored card proof')
ck(receipt['status']==lifecycle['status']==summary['status']=='pass' and receipt['error'] is lifecycle['error'] is None and receipt['output_identity_seal']=='complete_inside_original_helper_window','actual closed helper complete seal PASS')
ck(outer['all_bindings_unchanged'] is True and outer['helper_status']=='pass','outer final bound identity unchanged')
ck(outer['outer_seconds']==960 and outer['sampled_RSS_limit_bytes']==8589934592 and Decimal(str(outer['elapsed_seconds']))<=960 and Decimal(str(outer['child_terminal_wall_seconds']))<=900 and outer['peak_sampled_tree_RSS_bytes']<=8589934592,'outer original time and sampled tree RSS budget')
ck(receipt['elapsed_seconds']<=900 and lifecycle['elapsed_seconds']<=900 and summary['elapsed_seconds']<=900 and receipt['sampled_peak_RSS_bytes']<=8589934592 and lifecycle['time_limit_seconds']==summary['time_limit_seconds']==900.0,'helper original resource budget')
ck(not (STAGE/'stop_requested.txt').exists(),'no terminal stop request')
ck(receipt['HP_calls_started']==receipt['HP_calls_completed']==lifecycle['HP_calls_started']==lifecycle['HP_calls_completed']==summary['HP_calls_started']==summary['HP_calls_completed']==4,'four actual new HP80/120 starts and completions')
ck(receipt['accepted_mechanical_states_completed']==receipt['workpiece_states_completed']==lifecycle['accepted_mechanical_states_completed']==lifecycle['workpiece_states_completed']==summary['accepted_states']==2,'two completed mechanical and inherited workpiece checks')
ck(receipt['plot_started']==receipt['plot_completed']==lifecycle['plot_started']==lifecycle['plot_completed']==summary['plot_started']==summary['plot_completed']==1,'one pure plot starts and completes')
ck(receipt['production_F_T_solver_tests_API_calls']==0 and all(summary[k]==0 for k in ('candidate_force_calls','tangent_calls','solver_calls','model_constructions','JIT_calls','LF_calls','AD_or_JIT_calls_by_wrapper')) and lifecycle['AD_or_JIT_calls_by_wrapper']==0,'reported zero prohibited mechanics operations, bounded pinned wrapper basis')
ck(summary['plot_mechanical_hooks_monitored'] is lifecycle['plot_mechanical_hooks_monitored'] is observation['mechanical_hooks_monitored'] is False and observation['new_mechanics_calls']==0,'pure plot basis does not claim dynamic mechanics hook coverage')
ck(summary['checks_completed']==lifecycle['checks_completed']==161528 and "'HP_calls': 4" in stdout and "'status': 'pass'" in stdout,'ordinary check counts and actual stdout agreement')
ck(summary['gates']==protocol['gates'] and len(summary['gates'])==15,'all original fifteen gate constants retained')
ck(summary['global_scatter_precision']==3000 and summary['global_scatter_inexact_trap'] is True,'original Decimal3000 scatter and Inexact-trap evidence')
ck(summary['private_run_state_source_sha256']=='b850308dd35a0c74a42a1900bfb643cb9731fcb8ab6cb8e65a3cc7b2f87412b5' and summary['inherited_workpiece_checker_sha256']=='aa86bb162632f8c660ae0f547ad1ec16b9d655bcb99693b807381a6ddeafd938','original inherited B850/aa86 checker identity')
ck(summary['full_element_and_DOF_coverage'] is True and summary['HP_matrix_columns_exhaustively_checked'] is False and summary['direction']==protocol['direction'],'full declared coverage and PORT-only direction scope')
ck(summary['production_path_completed'] is summary['production_task_target_executed'] is True and summary['production_accepted_states']==25,'parent actual full 25 production path preserved')
ck(all(summary[k] is False for k in ('full_production_path_reference_pass','full_original_path_reference_pass','public_API_association_performed','contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified')) and receipt['full25_LF_path_reference_qualified'] is False,'qualification and public API association remain restricted')
ck(summary['auxiliary_material_energy']==dict(status='not_evaluated',qualified=False,field_present=False),'mechanical candidate auxiliary energy unqualified unchanged')

science_identities={}
for name, seal in receipt['outputs'].items():
    p=ROOT/name
    ck(p.is_file() and p.stat().st_size==seal['bytes'],'closed producer output stat: '+name)
    if science(p):
        science_identities[name]=dict(seal,identity_basis='actual closed helper output seal plus stat only; no byte/header/decode/hash read')
    else:
        raw(p)
        ck(ordinary[name]==seal['sha256'],'closed producer ordinary SHA: '+name)
ck(len(receipt['outputs'])==42 and len(science_identities)==23,'actual complete output inventory 42 total and 23 science/media stat-only')
states=[]
gate_counts=[]
expected_legs=['loading','unloading']
for position,(index,target) in enumerate(zip([13,16],[1.2,1.05])):
    record=summary['states'][position]
    raw_state=read(RUN/f'accepted_{index:03d}/summary.json')
    ck(record['index']==record['source_accepted_index']==record['original_target_index']==record['reference_execution_index']==index and record['leg']==expected_legs[position] and record['target_mm']==target and record['status']=='pass','actual selected state index/leg/target '+str(index))
    ck(record['state_sha256']==protocol['selected_state_sha256'][position] and raw_state['state_sha256']==record['state_sha256'],'actual selected saved state SHA '+str(index))
    ck(all(raw_state.get(k)==v for k,v in record.items() if k not in ('source_accepted_index','reference_execution_index','descriptor_file_sha256')),'raw selected summary matches top ordinary state '+str(index))
    ck(record['elements_compared']==13440 and record['global_DOFs_compared']==27378 and record['local_force_entries_compared']==record['local_tangent_entries_compared']==322560 and record['full_matrix_entries_assembly_checked']==860160 and record['HP_calls']==2,'full saved coverage '+str(index))
    metric=record['metrics'];g=protocol['gates']
    ck(decimal_gate(metric['production_relative_residual'],g['production_residual']) and decimal_gate(metric['independent_relative_residual'],g['independent_residual']) and decimal_gate(metric['relative_constraint'],g['average_constraint']) and decimal_gate(metric['relative_force_balance'],g['global_force_balance']) and decimal_gate(metric['fixed_displacement_mm'],g['fixed_displacement_mm']) and Decimal(metric['minimum_J'])>0,'ordinary equation metrics satisfy declared gates '+str(index))
    gate_records=[]
    def collect(value):
        if isinstance(value,dict):
            if 'normalized_error' in value and 'limit' in value: gate_records.append(value)
            for item in value.values():collect(item)
        elif isinstance(value,list):
            for item in value:collect(item)
    collect(record)
    ck(all(decimal_gate(v['normalized_error'],v['limit']) and v['pass_gate'] is True for v in gate_records),'all ordinary summary numerical gate entries '+str(index))
    hp_records=[v for v in gate_records if 'hp80_hp120_error' in v]
    ck(all(decimal_gate(v['hp80_hp120_error'],g['hp80_hp120']) and ('maximum_hp80_hp120_error' not in v or decimal_gate(v['maximum_hp80_hp120_error'],g['hp80_hp120'])) for v in hp_records),'all ordinary HP80/120 comparisons '+str(index))
    for family, suffix in (('force_checks','force'),('tangent_checks','tangent')):
        for comp in ('total','material','regularization'):
            ck(Decimal(record[family][comp]['limit'])==Decimal(g[comp+'_'+suffix]),f'original {comp} {suffix} gate '+str(index))
    ck(Decimal(record['CSC_total_action_check']['limit'])==Decimal(g['total_tangent']) and Decimal(record['augmented_checks']['force']['limit'])==Decimal(g['augmented_force_tangent']) and Decimal(record['augmented_checks']['constraint']['limit'])==Decimal(g['augmented_constraint_tangent']),'original CSC/KKT gates '+str(index))
    for k in ('references','raw_fixture','global_references','exact_element_gates','global_differences','equations','actions','rounded_kinematics','independent_total_matrix','workpiece_checks'):
        links=record[k] if isinstance(record[k],list) else [record[k]]
        for link in links:
            name=(RUN/link['path']).relative_to(ROOT).as_posix()
            ck(name in receipt['outputs'] and receipt['outputs'][name]['sha256']==link['sha256'],'ordinary output pointer agrees with closed seal: '+name)
    obs=observation['states'][position]
    ck(obs['accepted_source_index']==obs['original_target_index']==index and obs['target_mm']==target and obs['leg']==expected_legs[position] and obs['state_sha256']==record['state_sha256'] and len(obs['entries'])==10,'observation ordinary source metadata '+str(index))
    ck(all(v['pass_gate'] is True and decimal_gate(v['error'],v['limit']) for v in obs['entries']),'ten display observations stay inside original gates '+str(index))
    gate_counts.append(dict(index=index,ordinary_gate_entries=len(gate_records),hp80_hp120_entries=len(hp_records)))
    states.append(dict(index=index,target_mm=target,leg=record['leg'],state_sha256=record['state_sha256'],metrics=metric,force_checks=record['force_checks'],tangent_checks=record['tangent_checks'],CSC_total_action_check=record['CSC_total_action_check'],augmented_checks=record['augmented_checks']))

ck(observation['original_gates_unchanged'] is True and observation['full_production_path_reference_pass'] is False,'observation cannot replace all fifteen gates or enlarge scope')
for name,pin in summary['source_bindings'].items():
    raw(ROOT/name);ck(ordinary[name]==pin,'actual ordinary source binding '+name)
for name,pin in summary['input_bindings'].items():
    p=ROOT/name
    if not science(p):raw(p);ck(ordinary[name]==pin,'actual ordinary input binding '+name)
parent_stage=ROOT/'lf_data_preparation/native_interface_001/lf_forward_001/run_001'
parent_receipt=read(parent_stage/'execution_receipt.json')
parent_result=read(parent_stage/'lf_fine_forward/result.json')
parent_response=read(parent_stage/'lf_fine_forward/response.json')
parent_view=read(parent_stage/'view/lf_fine_forward/summary.json')
parent_view_header=read(parent_stage/'view/view.json')
for p in (parent_stage/'lf_fine_forward/result.json',parent_stage/'lf_fine_forward/response.json',parent_stage/'view/lf_fine_forward/summary.json',parent_stage/'view/view.json'):
    name=p.relative_to(ROOT).as_posix()
    ck(ordinary[name]==parent_receipt['outputs'][name]['sha256'] and p.stat().st_size==parent_receipt['outputs'][name]['bytes'],'actual original LF ordinary producer seal '+name)
ck(parent_receipt['status']=='pass' and parent_receipt['output_identity_seal']=='complete_inside_original_helper_window' and parent_result['status']=='success' and parent_result['accepted_states']==parent_view['accepted_states']==25 and parent_response['status']=='success','actual original LF result/response/view completed identity')
ck(parent_response['identity']['result']['sha256']==summary['result_sha256']==ordinary[(parent_stage/'lf_fine_forward/result.json').relative_to(ROOT).as_posix()],'new reference to original LF result ordinary identity')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
ck(head==EXPECTED_SOURCE,'actual repository HEAD still authorized source')
default_diff=subprocess.run(['git','diff','--quiet',EXPECTED_SOURCE,'--','hf_repo'],cwd=ROOT)
ck(default_diff.returncode==0,'default hf_repo source unchanged')
md_path=OUT/'execution_terminal_review.md'
result=dict(schema_version='ordinary-independent-execution-terminal-review-1.0',card='L-REF1',status='pass_ordinary_terminal_review' if not blocking else 'blocking_ordinary_terminal_review',blocking=blocking,blocking_findings=blocking,authorized=True,executed=True,
    created_utc=datetime.now(timezone.utc).isoformat(),execution_closed=True,execution_status=outer['status'],authorized_execution_source_commit=EXPECTED_SOURCE,protocol_sha256=EXPECTED_PROTOCOL,
    protocol_SHA256=EXPECTED_PROTOCOL,outer_sha256=ordinary[(STAGE/'reference_launch.json').relative_to(ROOT).as_posix()],outer_file_sha256=ordinary[(STAGE/'reference_launch.json').relative_to(ROOT).as_posix()],
    helper_receipt_sha256=ordinary[(RUN/'execution_receipt.json').relative_to(ROOT).as_posix()],actual_tool_terminal=dict(session_id=53525,initial_chunk_id='aaf33b',terminal_chunk_id='0ead02',exit_code=0,evidence_basis='Root actual tool terminal supplied directly to independent reviewer; ordinary closed records corroborate'),
    actual_execution=dict(invocations=outer['invocations'],HP_calls_started=receipt['HP_calls_started'],HP_calls_completed=receipt['HP_calls_completed'],mechanical_states=receipt['accepted_mechanical_states_completed'],workpiece_states=receipt['workpiece_states_completed'],plot_started=receipt['plot_started'],plot_completed=receipt['plot_completed'],checks_completed=summary['checks_completed'],elapsed_outer_seconds=outer['elapsed_seconds'],elapsed_helper_seconds=receipt['elapsed_seconds'],child_terminal_wall_seconds=outer['child_terminal_wall_seconds'],sampled_tree_RSS_bytes=outer['peak_sampled_tree_RSS_bytes']),
    scope='Only ordinary terminal/source records and stat. No independent repeat of mathematical arrays, compressed element/body details or media pixels; inherited checker pass/counters are actual evidence for those checks.',
    default_changes=0,science_or_media_byte_reads=0,science_or_media_header_reads=0,science_or_media_hash_reads=0,pixel_inspections=0,HP_executions=0,production_mechanics_calls=0,solver_calls=0,tests=0,plots=0,
    fifteen_gate_contract=summary['gates'],ordinary_gate_counts=gate_counts,state_observations=states,checks=checks,reviewed_repository_SHA256=ordinary,read_repository_SHA256=dict(ordinary),science_media_identities_stat_only=science_identities,declared_binary_identities={name:dict(sha256=value['sha256'],bytes=value['bytes']) for name,value in science_identities.items()},
    observation_path_error=dict(chunk_id='2b735d',exit_code=1,attempted_path='run_001/reference_stdout.log',actual_path='reference_stdout.log',interpretation='Root ordinary postterminal observation path error; no scientific invocation or retry. Correct ordinary actual log was read in this review.'),
    qualification=dict(full_production_path_reference_pass=False,public_API_association_performed=False,HP_matrix_columns_exhaustively_checked=False,pressure_qualified=False,clamp_qualified=False,contact_qualified=False,HF5_qualified=False),
    pixel_QA='Not performed by independent terminal reviewer; root may perform at most one approved fresh PNG inspection separately')
md='''# L-REF1 独立普通终态核查\n\n仅审阅既有普通 JSON／日志／源码与科学、媒体文件 stat；没有重算、解压、数组读取、媒体解码或像素检查。实际工具终态由 root 提供，session53525 初始 aaf33b，终态0ead02，exit0；已与闭合记录交叉核对。\n\n'''
md+=f"结果：{result['status']}；阻断项 {len(blocking)}。实际一次 launcher，4／4 HP，2／2材料与工件态，1／1纯绘图，161528项原核查。outer {outer['elapsed_seconds']}秒，helper {receipt['elapsed_seconds']}秒，child实际退出墙钟 {outer['child_terminal_wall_seconds']}秒，采样进程树RSS {outer['peak_sampled_tree_RSS_bytes']}字节，均在900／960秒与8GiB内。\n\n"
md+='两态保留 accepted／original13 loading1.20 mm和16 unloading1.05 mm；每态13440单元、27378DOF、322560局部力条目、322560局部PORT切线作用条目与860160保存CSC系数组装条目。原十五门及Decimal3000散射／Inexact trap保持，普通摘要内所有记录误差和HP80／120一致性值均满足原阈值。工件压缩详细检查未再次读取；其完成计数与继承aa86代码先检查后计数的实际PASS路径、闭合seal共同支撑两态检查已完成。\n\n'
md+='完整42项输出均有实际闭窗producer身份及匹配stat，23项科学／媒体仅继承producer SHA＋stat，19项普通输出核对实际SHA。两态输入与实际生产25态出处一致，源包和默认hf_repo未变。十项观察图的数据与源态索引一致；本审查没有检查图像像素。\n\n'
md+='L-FWD1全25生产路径完成状态保留；本卡只授两态及原PORT方向参考，不授全25参考、所有切线列、压力、有效夹持、释放、稳定性、一般LF或HF5资格，也未关联公开API。\n\n'
md+='root终态后 2b735d 的普通读取路径错误（run_001/reference_stdout.log不存在）独立记录；真实日志为stage/reference_stdout.log，已核其PASS计数。这是普通观察错误，不是科学失败、重试或新执行。\n\n'
md+='阻断项：'+('无。' if not blocking else '\n'+ '\n'.join('- '+v for v in blocking))+'\n'
OUT.mkdir(parents=True,exist_ok=True)
md_path.write_text(md,encoding='utf8')
result['external_report_MD_sha256']=hashlib.sha256(md_path.read_bytes()).hexdigest()
(OUT/'execution_terminal_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(status=result['status'],blocking=blocking,json_path=str(OUT/'execution_terminal_review.json'),md_path=str(md_path),ordinary_files=len(ordinary),science_stat_only=len(science_identities),output_inventory=len(receipt['outputs'])),ensure_ascii=False))
raise SystemExit(0 if not blocking else 1)
