"""Original ordinary cost records and symbolic source/AST review only."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

EXT=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/nested_reference_002'
CORE='lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/reference_author/core_audit_mechanical.py'
sha=lambda p:sha256(p.read_bytes()).hexdigest()
reviewed={}
def ordinary(name):
    p=ROOT/name
    assert p.suffix.lower() not in ('.npz','.gz')
    reviewed[name]=sha(p)
    return p
def read(name):return json.loads(ordinary(name).read_bytes())
def source(name):return ordinary(name).read_text(encoding='utf-8')
protocol=read(REL+'/protocol.json')
summary=read(REL+'/run_001/reference/summary.json')
life=read(REL+'/run_001/reference/lifecycle.json')
launch=read(REL+'/reference_launch.json')
assert life['status']==summary['status']==launch['status']=='pass'
assert life['HP_calls_started']==life['HP_calls_completed']==summary['HP_calls_started']==summary['HP_calls_completed']==48
assert life['accepted_mechanical_states_completed']==life['workpiece_states_completed']==summary['accepted_states']==24
assert launch['exit_code']==0 and launch['stop_reason'] is None

core_text=source(CORE)
core_tree=ast.parse(core_text,filename=CORE)
gates_node=next(n.value for n in core_tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='GATES' for t in n.targets))
gates={n.arg:ast.literal_eval(n.value) for n in gates_node.keywords}
assert len(gates)==15 and gates==protocol['gates']==summary['gates']
availability_node=next(n.value for n in core_tree.body if isinstance(n,ast.Assign)
    and any(isinstance(t,ast.Name) and t.id=='MECHANICAL_AVAILABILITY' for t in n.targets))
availability={}
for item in availability_node.keywords:
    if isinstance(item.value,ast.Call):
        availability[item.arg]={n.arg:ast.literal_eval(n.value) for n in item.value.keywords}
    else:availability[item.arg]=ast.literal_eval(item.value)
assert availability['response_mode']=='mechanical'
assert availability['auxiliary_material_energy']==dict(status='not_evaluated',qualified=False,field_present=False)
assert all(summary[key]==value for key,value in availability.items())
assert summary['global_scatter_precision']==3000 and summary['global_scatter_inexact_trap'] is True
assert summary['HP_matrix_columns_exhaustively_checked'] is False
assert summary['full_element_and_DOF_coverage'] is True
assert 'no candidate energy comparison or qualification' in summary['analytic_HP_energy_scope']
for name,pin in protocol['reference_sources'].items():
    assert sha(ordinary(name))==pin
assert len(protocol['reference_sources'])==11
for name in (REL+'/execute_nested_reference.py','hf_repo/scripts/audit_native_workpiece_cycle.py',
    'hf_repo/scripts/audit_native_mean.py','hf_repo/scripts/hf4_split_precision_reference.py',
    'hf_repo/scripts/hf2_precision_reference.py','hf_repo/src/hf_eval/tangent_action.py'):
    ast.parse(source(name),filename=name)

def timing_fields(value,path=''):
    found=[]
    if isinstance(value,dict):
        for key,item in value.items():
            loc=path+'.'+key if path else key
            if any(term in key.lower() for term in ('elapsed','seconds','duration','timing')):
                found.append(dict(field=loc,value=item))
            found.extend(timing_fields(item,loc))
    elif isinstance(value,list):
        for index,item in enumerate(value):found.extend(timing_fields(item,path+f'[{index}]'))
    return found
states={}
all_state_cost_fields={}
for index in range(24):
    name=REL+f'/run_001/reference/accepted_{index:03d}/summary.json'
    record=read(name)
    assert record['index']==index and record['status']=='pass' and record['HP_calls']==2
    all_state_cost_fields[str(index)]=timing_fields(record)
    if index in (13,14):
        assert record==summary['states'][index]
        states[str(index)]={key:record[key] for key in ('index','status','state_sha256','target_mm',
            'original_target_index','leg','HP_calls','elements_compared','global_DOFs_compared',
            'local_force_entries_compared','local_tangent_entries_compared','full_matrix_entries_assembly_checked',
            'metrics','force_checks','tangent_checks','CSC_total_action_check','augmented_checks')}
assert all(not fields for fields in all_state_cost_fields.values())
run_state=next(n for n in ast.walk(core_tree) if isinstance(n,ast.FunctionDef) and n.name=='run_state')
assert 'index != 0 or' in core_text
worker_text=source(REL+'/execute_nested_reference.py')
body_text=source('hf_repo/scripts/audit_native_workpiece_cycle.py')
ref_text=source('hf_repo/scripts/hf4_split_precision_reference.py')
assert 'record = self.rows[-1]' in body_text
assert 'for precision in (80, 120)' in core_text
assert 'context.prec = 3000' in core_text and 'context.traps[Inexact] = True' in core_text
assert 'if element % 256 == 0:' in core_text and 'if element % 128 == 0:' in core_text
assert 'self.checkpoint()' not in ref_text

scope=[
    dict(item='Full local/global total, material and Hu force',coverage='All 13440 elements and 27378 real DOFs, HP80/120 and exact global scatter; original component norms/floors.'),
    dict(item='PORT analytic tangent action',coverage='All elements/DOFs in the single declared five-node input direction; three components, saved CSC action, deltaR=0.'),
    dict(item='Full CSC assembly',coverage='All 860160 saved tensor coefficients reconstructed into the full unsymmetrized matrix; assembly identity, not independent analytic HP verification of every column.'),
    dict(item='KKT action and equilibrium',coverage='Same PORT free-force action incl. output spring, mean row; signed actuator/support/spring/residual, mean/fixed/balance gates.'),
    dict(item='Fixed workpiece and holding projections',coverage='Same HP force projected to signed total/material/Hu ON-body resultants, deduplicated holding groups, overlap, mirror and magnitude; global/component denominator rules retained.'),
    dict(item='Energy availability',coverage='Candidate mechanical auxiliary energy stays not_evaluated/unqualified/absent; independently calculated material energy archived only, no total-Hu energy-gradient or candidate-energy qualification.'),
]
md='''# 两态独立参考复用：成本与十五原门审阅

此次只读原M-REF2普通JSON与Python源码／AST，没有解码NPZ、读取gzip科学档案、HF导入、试算、HP、计时测试或正式仓库修改。新alpha两态尚无独立HP；旧alpha的结果不可移用为新资格。

## 原实际成本及预算依据

原M-REF2唯一完整24态／48HP80+120实际PASS：helper2067.204527899972秒，outer2068.5294668000424秒；helper采样RSS1390268416B，tree RSS1398767616B。原额度helper4500／outer4560秒、采样8GiB。13峰值1.20及14首次下降1.15的小summary分别记2次HP、13440元素、27378DOF，但没有逐态或逐HP耗时。实际24份小summary均没有elapsed／seconds／duration／timing字段；lifecycle仅保留全窗终态，源码record也没有逐态时钟。不能给出两态各自“实测耗时”。

新范围若严格为两个完整保存态、4次新HP，仍每态计算全部元素、全DOF散射、原力／方向切线／CSC／方程／工件检查。可以把“旧全窗耗时 × 2/24”仅作为规模启发式，不据此保证线性速度或删减原检查。单态全模型的峰值内存和两个精度结果仍需保留，RSS不可除以12。建议新具体卡可考虑helper900／outer960秒、采样8GiB的有界窗口；这只是基于既有完整窗口和缩小态数的保守规划提议，未授权、不是试算或精确预计。若未来超限应首错结束，不按旧窗口剩余额度续算或延期。

原checkpoint在HP前后、精确scatter每256元素、local gate每128元素及输出／lifecycle后检查。Decimal参考evaluate本身的元素循环没有stop检查，因此这仍是协作停止；一次HP可运行至下一检查点，必须记录真实elapsed，不能声称OS硬时限或force清理。

## 原十五门全部继承

| gate | 原值 |
|---|---|
| production_residual | 1e-9 |
| independent_residual | 1e-8 |
| force_evaluation | 1e-9 |
| average_constraint | 1e-10 |
| global_force_balance | 1e-6 |
| fixed_displacement_mm | 8e-11 |
| hp80_hp120 | 1e-40 |
| total_force | 1e-11 |
| material_force | 1e-9 |
| regularization_force | 1e-9 |
| total_tangent | 1e-10 |
| material_tangent | 1e-9 |
| regularization_tangent | 1e-9 |
| augmented_force_tangent | 1e-10 |
| augmented_constraint_tangent | 1e-10 |

B850原GATES、M-REF2协议和实际摘要完全相同。HP80／120、3000位精确散射与Inexact trap保持；总力全局scale与原残差floor、材料／Hu force的1e-12 component floor、切线action的1e-10 norm floor、KKT mean的1e-6 displacement floor等均沿原式。不选更容易的方向、标量工件百分比或新的门来替代原完整检查。

方向仍为实际五节点 `b_in/max(abs(b_in))`，fixed分量零、27378长、deltaR=0，实际port权重[1/8,1/4,1/4,1/4,1/8]。方向由未来获批读取实际模型生成并绑定，不在此次重新计算。总／材料／Hu力覆盖全部元素和真实DOF；切线是此单一PORT方向的独立解析action。保存全部860160系数与CSC组装身份检查，不等于所有切线列独立HP。KKT检验同方向free force＋spring与mean row，未测试其它方向或deltaR列。

同一HP全局力进一步核signed工件总／材料／Hu作用、去重holding分区、背景对称重叠、镜像和双侧幅值；工件比较的原denominator规则保持，不能把归一化误差称为工件标量的百分比。没有压力、有效夹持力、全切线列、网格稳定性、拒绝trial、解唯一性或HF5资格。

mechanical模式的辅助材料能量仍not_evaluated、qualified=false、field_present=false。独立解析材料能量只归档，不作candidate能量比较；Hu总残差不能偷换为总势能梯度来加虚功资格。

## 最小复用合同

原B850 `run_state(index,row)`的index0要求未变形／R0；child局部0是原1.20峰值，不能直接enumerate0/1重用该条件。用绑定原execution index13/14运行原methods，可保留原检查与raw accepted013／014目录。工件检查实际读`self.rows[-1]`，支持两条追加record，无需填假的已完成行。最终新增普通摘要可映射local index0/1并另存reference_execution_index13/14；原stateSHA、绝对d、row descriptor、目录与原目标关系须清楚绑定。该映射只改变报告索引，不修改15门或声称新的未变形origin。

M-REF2旧loader／run wrapper硬绑定alpha1e-6完整24态／48HP、production full success及旧任务，不能直接调用。新loader应针对已保存alpha5e-7两态、其原任务及continuation身份作最小输入／元数据适配；保留父NOT_PASS、segment成功与完整原路径未完成，明确仅这两态的参考范围。新具体候选／卡仍需源审与新直接批准，本报告不执行或给出数值通过结论。
'''
mdp=EXT/'COST_AND_GATES_REVIEW.md'
with mdp.open('x',encoding='utf-8',newline='\n') as out:out.write(md)
report=dict(schema_version='MAREF1-cost-and-original-gates-source-review-1.0',
    status='completed_existing_reference_cost_and_15_gate_review_no_new_scientific_execution',
    created_utc=datetime.now(timezone.utc).isoformat(),authorized=False,executed=False,
    reviewed_repository_SHA256=reviewed,
    original_actual_cost=dict(helper_seconds=life['elapsed_seconds'],outer_seconds=launch['elapsed_seconds'],
        helper_sampled_RSS_bytes=life['sampled_peak_RSS_bytes'],tree_sampled_RSS_bytes=launch['peak_sampled_tree_RSS_bytes'],
        accepted_states=24,HP_started=48,HP_completed=48,helper_limit_seconds=4500,outer_limit_seconds=4560),
    actual_selected_old_state_records=states,
    per_state_timing_available=False,all_24_small_summary_timing_fields=all_state_cost_fields,
    cost_proposal=dict(helper_seconds=900,outer_seconds=960,sampled_RSS_bytes=8589934592,
        scope='If future card remains exactly two full-model states/4HP with all original comparisons.',
        basis='Existing 24-state total only; total_seconds*2/24 is a scale heuristic, not a measured target-state duration or guarantee.',
        assigned_or_authorized=False,new_timing_trial=0,memory_not_scaled_by_state_count=True),
    gates=gates,direction=protocol['direction'],global_scatter_precision=3000,global_scatter_Inexact_trap=True,
    mechanical_availability=availability,analytic_HP_energy_scope=summary['analytic_HP_energy_scope'],
    coverage=scope,
    source_evidence=dict(core_run_state_lines=[run_state.lineno,run_state.end_lineno],
        GATES_lines=[40,44],normalization_lines=[77,86,398,433],
        fresh_HP_and_scatter_lines=[354,380],full_CSC_identity_vs_single_direction_lines=[322,344],
        core_origin_guard_line=299,workpiece_last_record_lines=[269,276],
        workpiece_projections_lines=[278,327],HP_evaluate_no_internal_checkpoint_lines=[95,176],
        old_wrapper_fixed_scope_lines=[69,77,217,249]),
    minimal_adapter='Keep original mathematical methods; execution indices13/14 avoid treating resumed peak as undeformed index0. Map only new summary local indices0/1 with explicit execution-index/source-state identities; no fake completed placeholder rows.',
    qualifiers=dict(all_tangent_columns=False,pressure=False,effective_clamp=False,mesh_stability=False,
        HF5=False,rejected_trials=False,total_energy_gradient_qualification=False),
    actions=dict(HF_import=0,tests=0,NPZ_byte_read_or_decode=0,gzip_scientific_archive_read=0,
        F_T_solver_HP_observer_plot=0,new_scientific_arithmetic=0,timing_trial=0,formal_mutation=0),
    findings=['No per-state/per-HP cost record in the existing ordinary summaries.',
        'Old full-path loader is task/alpha/count/success-specific and needs a new minimal adapter; scientific gates cannot be weakened.',
        'Budget proposal is planning only and still needs a concrete frozen card and direct approval.'],
    documentation_sha256=sha(mdp))
jp=EXT/'cost_and_gates_review.json'
with jp.open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=report['status'],JSON_SHA256=sha(jp),MD_SHA256=sha(mdp),
    gates=len(gates),ordinary_or_source_files=len(reviewed),per_state_timing_available=False)))
