"""Prepare a concrete S5 proposal, no execution authorization or scientific reads."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
OLD='lf_data_preparation/native_interface_001/lf_circle_step_004'
REL='lf_data_preparation/native_interface_001/lf_circle_step_005'
PARENT=OLD+'/run_001/wave_circle_step'
LOCAL='lf_data_preparation/native_interface_001/lf_circle_local_001'
REF='lf_data_preparation/native_interface_001/lf_circle_reference_001'
BASE='8ac36c0f3ce4b0609c592522cb70f810635a7a9d'
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()


def write(name,value):
    with (AUTHOR/name).open('x',encoding='utf-8',newline='\n') as handle:
        if isinstance(value,str):handle.write(value)
        else:json.dump(value,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert not (ROOT/REL).exists()
    old=read(ROOT/OLD/'protocol.json');parent=read(ROOT/PARENT/'result.json')
    model_name=PARENT+'/'+parent['model']['descriptor_path'];model=read(ROOT/model_name)
    original_task=OLD+'/step_task.json';assert model['task']==read(ROOT/original_task)
    selected=parent['states'][1];local=read(ROOT/LOCAL/'run_001/summary.json')
    assert parent['status']=='success' and parent['targets_mm']==[1.25,1.35]
    assert selected['d']==1.35 and selected['original_target_index']==7
    assert selected['state_sha256']==local['state_sha256']=='0c8c5b07ad3ef5872502dede2f76cee6a152b9f78d3b0b7f831ebc6286a12455'
    assert local['J_minimum']==selected['minimum_J'] and local['Hu_max_abs_component_per_mm']==selected['max_abs_Hu_per_mm']
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_h05_alpha5em7_load140__L_CSTEP5',
        purpose='fixed_circle_LF_saved_load_only_step',
        parameter_origin='L-CSTEP5 proposal after saved-field localization: preserve complete source prefix through1.35 mm and append1.40 from accepted1/global7. No execution authorization in this preparation.',
        description='Fixed circular half-workpiece; proposed child revalidates1.35 mm and advances to1.40 mm. Complete task prefix inherited, not freshly executed.')
    task=deepcopy(model['task']);task.update(metadata)
    task['path']['targets_mm'].append(1.40);task['input']['target_mm']=1.40
    reversed_task=deepcopy(task);reversed_task.update({key:model['task'][key] for key in metadata})
    reversed_task['path']['targets_mm'].pop();reversed_task['input']['target_mm']=1.35
    assert reversed_task==model['task']
    write('step_task.json',task)
    sources={name:pin(ROOT/name) for name in old['source_bindings'] if name.startswith('hf_repo/')}
    assert all(sources[name]==old['source_bindings'][name] for name in sources)
    for name in ('execute_step.py','launch_step.py'):
        ast.parse((AUTHOR/name).read_bytes());sources[REL+'/'+name]=pin(AUTHOR/name)
    for name in (old['viewer_source'],old['convergence_source']):
        sources[name]=pin(ROOT/name);assert sources[name]==old['source_bindings'][name]
    geometry=(Path(model_name).parent/model['source_geometry']['snapshot']['descriptor']).as_posix()
    geometry_payload=(Path(geometry).parent/read(ROOT/geometry)['arrays']['path']).as_posix()
    state_descriptor=PARENT+'/'+selected['descriptor_path'];state_payload=PARENT+'/'+selected['state']['path']
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs'];inherited=[]
    for name in (geometry_payload,state_payload):
        seal=seals[name];assert (ROOT/name).stat().st_size==seal['bytes'];inherited.append(dict(path=name,**seal))
    ordinary=(PARENT+'/result.json',model_name,geometry,state_descriptor,original_task,OLD+'/protocol.json',
        REF+'/run_001/reference/summary.json',LOCAL+'/run_001/summary.json',LOCAL+'/NEXT_STEPS.md')
    inputs={name:pin(ROOT/name) for name in ordinary}
    inputs.update({row['path']:row['sha256'] for row in inherited});inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    p=deepcopy(old)
    p.update(card='L-CSTEP5',source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_step',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,original_task_file=original_task,task_file=REL+'/step_task.json',
        task_metadata=metadata,complete_task_targets_mm=[0.,.25,.5,.75,1.,1.15,1.25,1.35,1.40],targets_mm=[1.35,1.40],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in old['pure_view_bindings']},
        old_scientific_inputs=inherited,
        accepted_states_policy='Two requested child targets; original bounded bisections may add actual accepts.1.35 mm freshly revalidated; complete task prefix not re-executed.',
        qualification_scope='Only proposed1.35/1.40 child segment. No new HP or all-prefix execution, pressure, effective grip, unloading, release, stability, manufacturing or HF5 qualification. CREF1 covers ancestor1.15 only.',
        approved_plan=dict(path=LOCAL+'/NEXT_STEPS.md',sha256=inputs[LOCAL+'/NEXT_STEPS.md']),
        localization_evidence=dict(path=LOCAL+'/run_001/summary.json',sha256=inputs[LOCAL+'/run_001/summary.json'],
            scope='Ordinary source1.35 Simpson-J and cellwise-Hu positions only; not execution authorization, pressure, body-Hu force attribution or independent HP.'),
        created_utc=datetime.now(timezone.utc).isoformat())
    write('protocol.proposed.json',p)
    write('authorization.template.json',dict(card='L-CSTEP5',approval_card='L-CSTEP5',authorized=False,
        authorization_from_direct_human_request=False,one_invocation=True,direct_human_request=None,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        status='template_only_requires_explicit_new_stage_approval',
        reason='Previous S4 and L-CLOCAL1 windows closed. The project goal and localization result do not renew permission for a new physical target or resource window.',
        recorded_utc=datetime.now(timezone.utc).isoformat()))
    card=f'''# L-CSTEP5：圆形工件1.35→1.40 mm保存态延伸（待授权）

2026-10-17 Asia/Seoul。当前仅外部候选、普通元数据和静态检查，执行授权为false，正式main及默认HF未改。主干基线{BASE}，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

## 目标、依据与边界

整体目标是普通LF几何进入独立HF/TMC前向力学，得到可比较的非线性响应和接触相关观察；HF不优化、不调用/安装dmftd，MPM暂不实现。本次拟沿现有圆形任务只增加一个0.05 mm加载目标，不重开已关闭路径或原近旋转诊断。

S4原1.35态成功且新目标6检查/5线搜索全部接受/零失败二分。L-CLOCAL1定位已通过：自由第三介质minJ=0.08623624515762662位于e10394/q2的(73,31) mm介质侧角点；最近unsigned边距0.09633236207295634 mm，尖端距3.007572163198815 mm。最大Hu在左侧机构转角邻域介质e10368，中心仅代表标记；其峰值不能归因工件Hu合力。这些具体证据支持较小增量观察，不是新J阈值、接触证明或执行许可。

## 唯一输入与任务

来源{PARENT}/result.json accepted1/global7/1.35 mm，state SHA {selected['state_sha256']}，带符号R={selected['R_input']!r} N。父continuation里的1.25 mm祖锚不是本次选中状态；保整个parent_continuation。新完整任务[0,.25,.5,.75,1,1.15,1.25,1.35,1.40]，只追加1.40、更新峰值及四说明字段。实际child[1.35,1.40]/global7,8/local0,1，原前缀不从零重算。

半径9 mm、圆心(71,40) mm且工件固定ux/uy；E1MPa/nu.3/plane strain/厚20mm、h.5mm、13440元素/27378DOF、gamma1e-6/alpha5e-7/Lr80mm，原支撑/对称/平均端口与全部其余任务保持。settings原字节值保持，包括minimum_increment=.00625、max_bisections4；mechanical/chunk256/port_projection保持。

旧科学输入仅原S4 geometry.npz与选中split state.npz；准备继承producer seal/stat，不开载荷。L-CLOCAL1和CREF1仅读普通摘要作来源；不重复读取其NPZ、CSV、媒体或新增局部诊断读集。CREF1只核祖先1.15，不给父1.35或新1.40授独立参考。

## 最小执行步骤与原门

1. 新明确人类批准后，填写新的authorization.json，核本协议/候选SHA和main身份，再冻结到未存在的stage005；不把本模板改名冒充批准。
2. 单次evaluate_native(None,newtask,newout,...saved_result=原S4result,selected_state_index=1,extend_path=True)，先fresh F/T第一检查复核原1.35绝对lift/fluctuation及带符号R、SHA/R身份、原门；不复用旧力/切线/矩阵，不重新定基。
3. 仅推进新1.40目标。保relative residual1e-9、逐态constraint_bound系数1e-10、globalbalance1e-6、fixed fsum8e-11 mm及全部原GP J>0；原内部回溯/二分允许，保存全部实际接受态，不能锁定恰两态。
4. 成功后复用原S1纯viewer和收敛投影，一次生成4PNG、实际N帧GIF、反力/材料-Hu-总工件Fx/Fy/两种unsigned距离/分区J-Green-Hu/残差-约束界-回溯的原值表和人工页。坐标×1，完整结构仅视觉镜像且力不加倍；J为原九点Simpson，Hu为单元常值，meanJ图与采样最小值区分。每张新PNG最多一次像素检查；原图例轻微重叠注记保留，不重绘旧图。
5. 原窗口封存实际输出；结束后普通记录、封存/stat核对、有限实际审阅、结果解释和下一步计划、普通main推送与异目录恢复。发布逐命令gc.auto=0/maintenance.auto=false，不改Git仓库/全局配置。

## 资源、完成与停止

一次controller1800秒/显示共享600秒/helper2700秒/outer2760秒（最多46分钟），采样8GiB。显示共享含binding/viewer/收敛/表/页，seal仍在helper内。原SUP2 CPU-CLEAN1同实例终止、全部成员覆盖、句柄释放和固定5秒清理在outer内保持。

唯一启动、首个终端错误停止后续科学/成功显示，保真实partial，仅原窗口仍开放时允许部分seal。无外部重试、修复重跑、延期、force、回滚、删除、新测试、新HP或默认HF改动/安装。完成需锚点、新目标、原门、实际显示、资源/清理及记录通过；生产成功而显示失败要分别保留，不回写为全通过。

new_peak_reached和extended_segment_completed仅本子段；task_target_executed/full_original/full_extended保持False，target_response=None，requested_endpoint_response为新1.40。不到原零起点、完整路径、独立HP/全列切线、压力、有效夹持、圆形卸载/释放、稳定性、制造或HF5资格。后续只根据本次真实结果再规划最近阶段。

## 当前状态

尚未启动HF/绘图/测试；无授权执行卡窗口。需要新的明确批准，因为原S4和L-CLOCAL1均已闭卡，本次增加物理目标和资源额度。当前候选与输入身份由preparation_receipt和SOURCE_REVIEW记录；主干和冻结旧结果保持。
'''
    write('L-CSTEP5_CARD.md',card)
    write('preparation_receipt.json',dict(card='L-CSTEP5',status='prepared_pending_authorization_not_executed',
        source_baseline_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        source_bindings=len(sources),input_bindings=len(inputs),old_payloads_opened=0,new_equilibrium_paths=0,
        new_tests=0,HF_imports=0,default_source_changes=0,formal_repository_changes=0,
        files={name:dict(bytes=(AUTHOR/name).stat().st_size,sha256=pin(AUTHOR/name)) for name in
            ('execute_step.py','launch_step.py','protocol.proposed.json','step_task.json','authorization.template.json','L-CSTEP5_CARD.md')},
        created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status='prepared_pending_authorization_not_executed',
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),source_bindings=len(sources),input_bindings=len(inputs),authorized=False)))


if __name__=='__main__':main()
