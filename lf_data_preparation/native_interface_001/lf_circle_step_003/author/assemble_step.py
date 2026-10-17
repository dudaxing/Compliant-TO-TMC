"""Assemble this authorized saved-step metadata; no HF imports or payload reads."""
import ast
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
OLD='lf_data_preparation/native_interface_001/lf_circle_step_002'
REL='lf_data_preparation/native_interface_001/lf_circle_step_003'
PARENT=OLD+'/run_001/wave_circle_step'
REF='lf_data_preparation/native_interface_001/lf_circle_reference_001'
BASE='260d4b86ee87ab3dd12c04dbcccef7ffa4c31eac'
REQUEST='好的，按你的建议复用已安装的 load_only 保存态延伸接口，从圆形工件1.15 mm保存态推进到1.25 mm。保持半径9 mm、圆心(71,40) mm、其余物理条件和原验收门不变，注意做好记录，可视化实际变形、反力和收敛情况，再根据结果安排后续计算。'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


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
    selected=parent['states'][1];reference=read(ROOT/REF/'run_001/reference/summary.json')
    assert parent['status']=='success' and parent['targets_mm']==[1.,1.15]
    assert selected['d']==1.15 and selected['original_target_index']==5
    assert reference['status']=='pass' and reference['HP_calls_completed']==2 and reference['accepted_states']==1
    assert reference['states'][0]['state_sha256']==selected['state_sha256']
    assert reference['result_sha256']==pin(ROOT/PARENT/'result.json')
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_h05_alpha5em7_load125__L_CSTEP3',
        purpose='fixed_circle_LF_saved_load_only_step',
        parameter_origin='L-CSTEP3 direct request: preserve complete source prefix through1.15 mm and append1.25 mm from accepted1/global5. Selected1.15 reference is existing evidence only.',
        description='Fixed circular half-workpiece; child revalidates1.15 mm and advances to1.25 mm. Complete prefix is inherited, not freshly executed.')
    task=deepcopy(model['task']);task.update(metadata);task['path']['targets_mm'].append(1.25);task['input']['target_mm']=1.25
    reversed_task=deepcopy(task);reversed_task.update({key:model['task'][key] for key in metadata})
    reversed_task['path']['targets_mm'].pop();reversed_task['input']['target_mm']=1.15
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
    inputs={name:pin(ROOT/name) for name in (PARENT+'/result.json',model_name,geometry,state_descriptor,original_task,OLD+'/protocol.json',REF+'/run_001/reference/summary.json')}
    inputs.update({row['path']:row['sha256'] for row in inherited});inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    p=deepcopy(old)
    p.update(card='L-CSTEP3',source_baseline_commit=BASE,working_directory=cwd.as_posix(),
        output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_step',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,original_task_file=original_task,task_file=REL+'/step_task.json',
        task_metadata=metadata,complete_task_targets_mm=[0.,.25,.5,.75,1.,1.15,1.25],targets_mm=[1.15,1.25],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in old['pure_view_bindings']},
        old_scientific_inputs=inherited,
        accepted_states_policy='Two requested child targets; original bounded bisections may add actual accepts.1.15 mm is freshly revalidated, complete prefix not re-executed.',
        qualification_scope='Only1.15/1.25 child segment. Existing1.15 selected reference not transferred to new1.25 or full child/path. No HP, pressure/effective grip/unloading/release/stability/manufacturing/HF5 qualification.',
        approved_plan=dict(path=REF+'/NEXT_STEPS.md',sha256=pin(ROOT/REF/'NEXT_STEPS.md')),
        existing_selected_reference=dict(path=REF+'/run_001/reference/summary.json',selected_d_mm=1.15,global_target_index=5,state_sha256=selected['state_sha256'],scope='Source1.15 saved model and one PORT direction only; evidence not a continuation input or new target qualification.'),
        created_utc=datetime.now(timezone.utc).isoformat())
    write('protocol.proposed.json',p)
    write('authorization.json',dict(card='L-CSTEP3',approval_card='L-CSTEP3',authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,direct_human_request=REQUEST,authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        scope='Direct human approval of the published L-CSTEP3 proposal: installed1.15/1.25 load_only extension, original conditions/gates/settings, bounded actual views/pixels, records and ordinary main publication/restoration.',recorded_utc=datetime.now(timezone.utc).isoformat()))
    card=f'''# L-CSTEP3：圆形工件1.15→1.25 mm保存态延伸

2026-10-17 Asia/Seoul，用户直接批准已发布L-CREF1/NEXT_STEPS建议。main基线{BASE}，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。准备/静审快照，未执行。

整体目标为普通LF夹持器几何的独立HF/TMC非线性前向分析，输出可检查的变形、力与接触相关量；HF不优化、不导入/安装/调用dmftd，MPM暂不实现。1.15态已成功且单态2HP原十五门通过；自由介质minJ0.225154、unsigned最近边距0.232258 mm、尖端距3.202515 mm。当前只追加1.25，以0.10 mm增量观察更强压缩及传力；这不是接触或稳定性预测。

父源{PARENT}/result.json的accepted1/global5/1.15 mm，stateSHA{selected['state_sha256']}，R={selected['R_input']!r} N；不能误用continuation内1.00 mm祖锚。新完整task[0,.25,.5,.75,1,1.15,1.25]，inputpeak1.25，实际child[1.15,1.25]/global5,6/child0,1；只更新四说明字段、追加目标与峰值，其余任务严格保持。

原圆形r9/c(71,40) mm固定ux/uy，E1MPa/nu.3/plane strain/厚20mm、h.5mm、13440元素/27378DOF、gamma1e-6/alpha5e-7/Lr80mm、原支撑/对称/平均端口及mechanical/chunk256/port_projection保持。settings完全继承（含minimum_increment=.00625、max_bisections4、controller1800）。默认HF与绘图实现不改，无新测试、HP或安装。

一次evaluate_native(None,newtask,newout,...saved_result=父result,selected_state_index=1,extend_path=True)。先fresh F/T第一检查复核1.15绝对lift/fluctuation/带符号R，SHA/R字节身份保持，不复用旧力/T/矩阵，再推进新目标。保原relative residual1e-9、逐态constraint_bound系数1e-10、globalbalance1e-6、fixed fsum8e-11mm和所有GP J>0；原内部回溯/二分允许且所有真实接受态保留。

成功后复用原S1纯viewer与收敛投影，一次新进程生成4PNG、实际N帧GIF、逐态表与人工页：×1变形/全结构视觉镜像、R/qout、下半工件有符号Fx/Fy的材料/Hu/总分解、unsigned边界/尖端距离、分区J/Green/Hu场、残差/约束界/线搜索/二分。镜像不加倍数值；原图例/标题轻微重叠注记保留，不修改或重绘旧图。

旧科学读集仅父geometry.npz和selected001 split state.npz；准备继承原seal/stat，不开载荷。已有1.15参考只绑定普通summary作来源证据，不读其gzip/NPZ/旧媒体。新viewer纯五源，解码1+2N份新NPZ/27+18N字段，无切线解码；全新输出在原helper窗口封存。成功后四新PNG各最多一次像素检查，GIF帧数由原viewer核，不另解码。

一次controller1800/共享显示600/helper2700/outer2760秒（最多46分钟）、采样8GiB。共享显示含binding/viewer/收敛/表/页，seal仍限helper。原SUP2 CPU-CLEAN1同实例终止、全成员覆盖、句柄释放及固定5秒清理在outer内保持。唯一启动、首个终端错误停止后续科学/显示，保真实partial，仅原窗口仍开时允许部分seal；无外部重试、修复重跑、延期、force、回滚或删除。

new_peak_reached/extended_segment_completed仅本子段；task_target/full_original/full_extended仍False，target_response=None，requested_endpoint_response1.25。已有单态参考不转授新态，未取得全路径/全列切线/独立圆mask/压力/有效夹持/卸载/释放/稳定性/制造/HF5资格。圆形legacy normal字段仅global Fy，非圆周局部压力。

包括实际结果、图表、来源/资源/清理回执、后续决策记录、普通main推送及异目录恢复核对。完成条件为锚点、新目标、原门及实际显示/记录通过；失败不改写为通过，不静默扩大范围。后续根据实际误差、压缩、几何、力及成本只规划最近一个阶段，不预定更远加载。
'''
    write('L-CSTEP3_CARD.md',card)
    write('preparation_receipt.json',dict(card='L-CSTEP3',status='prepared_authorized_not_executed',source_baseline_commit=BASE,
        protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),source_bindings=len(sources),input_bindings=len(inputs),old_payloads_opened=0,scientific_invocations=0,
        files={name:dict(bytes=(AUTHOR/name).stat().st_size,sha256=pin(AUTHOR/name)) for name in ('execute_step.py','launch_step.py','protocol.proposed.json','step_task.json','authorization.json','L-CSTEP3_CARD.md')},created_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(dict(status='prepared_authorized_not_executed',protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),source_bindings=len(sources),input_bindings=len(inputs))))


if __name__=='__main__':main()
