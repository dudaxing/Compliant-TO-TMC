"""Prepare one authorized append-only tip-circle step from ordinary records."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_step_002'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_step_001'
PARENT=OLD+'/run_001/wave_circle_tip_step1'
BASE='2ab5e503ce6220ceeeba4b413d36e39399b1dd4b'
CARD='L-CTIPSTEP2'
REQUEST='好的，按你的建议开展 L-CTIPSTEP2，从0.75 mm保存态推进到0.90 mm。保持半径9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm及其余物理条件和原验收门不变。注意做好记录，可视化实际变形、反力、尖端接近、右侧介质和收敛情况，再根据结果安排后续计算。'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists()
    names=('execute_step.py','circle_saved_views.py','launch_step.py','plot_convergence.py')
    for name in names:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
    source=read(ROOT/OLD/'protocol.json')
    parent=read(ROOT/PARENT/'result.json')
    original=read(ROOT/OLD/'step_task.json')
    assert original['path']==dict(kind='load_only',targets_mm=[0.,.25,.5,.75])
    assert parent['status']=='success' and parent['reached_displacement']==.75 and len(parent['states'])==2
    selected=parent['states'][1]
    assert selected['state_sha256']=='998ebca7375050a870e4466139732524206b151c0e7b16418f90ecc0a8d856a4'
    assert selected['R_input']==.13029373126695096
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c80_domain92_Lr80_h05_alpha5em7_load090__L_CTIPSTEP2',
        purpose='tip_facing_circle_LF_saved_load_only_step',
        parameter_origin='L-CTIPSTEP2 direct approval: preserve complete [0,.25,.5,.75] prefix and append .90 mm using terminal .75 mm accepted state; all remaining physics and original gates unchanged.',
        description='Revalidate original .75 mm anchor and extend to .90 mm; observe actual tip approach and right-medium response on unchanged92mm domain. Earlier targets are inherited, not replayed.')
    task=deepcopy(original);task.update(metadata)
    task['path']['targets_mm'].append(.9);task['input']['target_mm']=.9
    write(AUTHOR/'step_task.json',task)
    geometry=PARENT+'/model/source_geometry/geometry.json'
    payload=PARENT+'/model/source_geometry/geometry.npz'
    state=PARENT+'/accepted/001/state.npz'
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    old_inputs={name:dict(path=name,**seals[name]) for name in (payload,state)}
    assert old_inputs[payload]['sha256']==read(ROOT/geometry)['arrays']['sha256']
    assert old_inputs[state]['sha256']==selected['state']['sha256']
    for name,seal in old_inputs.items():assert (ROOT/name).stat().st_size==seal['bytes']
    ordinary=[PARENT+'/result.json',PARENT+'/model/model.json',geometry,
        PARENT+'/accepted/001/state.json',OLD+'/step_task.json',OLD+'/protocol.json']
    inputs={name:pin(ROOT/name) for name in ordinary}
    inputs.update({name:seal['sha256'] for name,seal in old_inputs.items()})
    inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    sources={name:pin(ROOT/name) for name in source['source_bindings'] if name.startswith('hf_repo/')}
    sources.update({REL+'/'+name:pin(AUTHOR/name) for name in names})
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{name}.py' for name in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=deepcopy(source)
    protocol.update(schema_version='lf-circle-tip-saved-load-step-card-1.0',card=CARD,source_baseline_commit=BASE,
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_step2',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=1,geometry_file=geometry,
        original_task_file=OLD+'/step_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=[0.,.25,.5,.75,.9],targets_mm=[.75,.9],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=2,
        source_anchor=dict(accepted_index=1,original_target_index=3,d_mm=.75,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        old_input_scope='Only the original parent geometry four masks and selected split lift/fluctuation; producer seals plus stat before helper, identity hash/decode inside sole authorized helper. No old model/force/tangent/matrix payload.',
        task_execution_scope='Only suffix [.75,.9] is newly executed, including fresh anchor F/T verification; complete [0,.25,.5,.75,.9] task prefix is inherited, not replayed.',
        qualification_scope='One saved load-only extension and actual saved observations; no complete path replay, independent HP, pressure, effective grip, unloading/release/stability, domain-width convergence or HF5 qualification.',
        direct_user_request=REQUEST,created_utc=datetime.now(timezone.utc).isoformat())
    protocol.pop('old_scientific_input',None)
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        scope='Explicit user approval for one .75 to .90 saved extension, actual deformation/reaction/tip/right-medium/convergence views, records, normal main push and different-path local Git restoration.'))
    card='''# L-CTIPSTEP2：最右尖端对向圆形工件，保存态.75→.90 mm

用户已明确批准本卡实现并执行。整体目标是独立HF读取LF结构，逐步完成可恢复的大变形/TMC接近、接触后作用力和卸载功能。本轮只延伸一个加载目标，观察更强介质压缩下尖端接近、反力与收敛。

来源为L-CTIPSTEP1成功末态accepted1/global3，d=.75 mm、state SHA998ebca7375050a870e4466139732524206b151c0e7b16418f90ecc0a8d856a4、signed R=.13029373126695096 N。原parent是合法suffix[.50,.75]，完整task为[0,.25,.50,.75]；原parent/祖先continuation与成功/失败历史保持。新task仅append.90、input.target改.90并更新四项说明身份。现有evaluate_native(saved_result=parent,selected_state_index=1,extend_path=True)复核fresh F/T锚并执行suffix[.75,.90]；实际接受态N随原内部二分全部保存，不硬锁N=2、不重放旧前缀。

r9 mm、圆心(80,40) mm固定ux/uy，右域界92、Lr80，92×40mm下半域/h.5/厚20，E1MPa/nu.3/plane strain/gamma1e-6/alpha5e-7及所有支撑、端口、对称保持。顶部uy到92；右ux及非顶uy自由。原mechanical/chunk256/port_projection、非clock设置、residual1e-9、原平均约束系数1e-10及scale、global balance1e-6、fixed split8e-11mm、正J，maxchecks25/backtracks12/bisections4/mininc.00625保持。

唯一controller1800s，显示/收敛/表页共享600s，helper2700/outer2760s（最多46min），采样64GiB、四库线程配置上限16，pure viewer原8GiB子限。配置不等于实测16核使用；CPU后端不改。唯一旧科学输入为parent snapshot source_geometry/geometry.npz四掩码和accepted/001/state.npz的lift/fluctuation；执行前仅producer seal/stat，唯一helper内才hash/decode，不读旧model/force/tangent/matrix数组或媒体。无新tests/HP/default修改/安装。

成功后一次干净pure viewer读取新model27字段及每态split2/forces16，1+2N归档、27+18N字段；输出4PNG和实际N帧GIF，原收敛投影另1PNG，共5PNG，根Agent每新PNG最多一次像素检查，GIF不额外解码。显示实际×1变形（完整结构仅视觉镜像、力不加倍）、R/qout、下半工件material/Hu/total有符号Fx/Fy、tip及完整Q1最近距离/见证/交叉/重叠、分区J/Hu、right reference x89..92的480cells J/Green/Hu/位置及split位移与收敛。tip按唯一reference(80,30)找节点，右条带动态选resident原参考ID，外角位移与tip距离分列。

独立静审通过、最终字节冻结后唯一启动，首终端错误停止后续科学/显示并保真实partial；仅原窗口开放时允许部分seal。无外部重试、修复重跑、延期、force、回滚、删除。原内部回溯/二分允许。含目的/实现/理由/实际效果/取舍/恢复说明、main普通推送及异路径local Git恢复核对；origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

保留suffix语义，task_target_executed/full_original/full_extended均不升级，new_peak/segment仅本段。无当前布局独参、连续压力、有效夹持、完整卸载/自由释放、稳定性、网格/域宽收敛或HF5资格。根据实际结果再计划，本卡不授后续更大行程。
'''
    (AUTHOR/'L-CTIPSTEP2_CARD.md').write_text(card.rstrip()+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(sources),input_bindings=len(inputs),old_payload_reads=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
