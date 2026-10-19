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
REL='lf_data_preparation/native_interface_001/lf_circle_tip_step_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_tip_pilot_001'
PARENT=OLD+'/run_001/wave_circle_tip_pilot'
BASE='df44e51f704fd2a9f068e977b8c3f03b49ad41d0'
CARD='L-CTIPSTEP1'
REQUEST='批准按 L-CTIPSTEP1 实施并执行，从0.50 mm保存态推进到0.75 mm。保持半径9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm及其余物理条件和原验收门不变。注意做好记录，可视化实际变形、反力、尖端接近、右侧介质和收敛情况，再根据结果安排后续计算。'
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
    original=read(ROOT/OLD/'pilot_task.json')
    assert original['path']==dict(kind='load_only',targets_mm=[0.,.25,.5])
    assert parent['status']=='success' and parent['reached_displacement']==.5 and len(parent['states'])==3
    selected=parent['states'][2]
    assert selected['state_sha256']=='c8f41107026000f09d395eb7a091ce6501b532b0a8d69210b22a94d55e8c8392'
    assert selected['R_input']==.08602790333542189
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c80_domain92_Lr80_h05_alpha5em7_load075__L_CTIPSTEP1',
        purpose='tip_facing_circle_LF_saved_load_only_step',
        parameter_origin='L-CTIPSTEP1 direct approval: preserve complete [0,.25,.5] prefix and append .75 mm using terminal .5 mm accepted state; all remaining physics and original gates unchanged.',
        description='Revalidate original .50 mm anchor and extend to .75 mm; observe actual tip approach and right-medium response on unchanged92mm domain. Earlier targets are inherited, not replayed.')
    task=deepcopy(original);task.update(metadata)
    task['path']['targets_mm'].append(.75);task['input']['target_mm']=.75
    write(AUTHOR/'step_task.json',task)
    geometry=PARENT+'/model/source_geometry/geometry.json'
    payload=PARENT+'/model/source_geometry/geometry.npz'
    state=PARENT+'/accepted/002/state.npz'
    seals=read(ROOT/OLD/'run_001/execution_receipt.json')['outputs']
    old_inputs={name:dict(path=name,**seals[name]) for name in (payload,state)}
    assert old_inputs[payload]['sha256']==read(ROOT/geometry)['arrays']['sha256']
    assert old_inputs[state]['sha256']==selected['state']['sha256']
    for name,seal in old_inputs.items():assert (ROOT/name).stat().st_size==seal['bytes']
    ordinary=[PARENT+'/result.json',PARENT+'/model/model.json',geometry,
        PARENT+'/accepted/002/state.json',OLD+'/pilot_task.json',OLD+'/protocol.json']
    inputs={name:pin(ROOT/name) for name in ordinary}
    inputs.update({name:seal['sha256'] for name,seal in old_inputs.items()})
    inputs[REL+'/step_task.json']=pin(AUTHOR/'step_task.json')
    sources={name:pin(ROOT/name) for name in source['source_bindings'] if name.startswith('hf_repo/')}
    sources.update({REL+'/'+name:pin(AUTHOR/name) for name in names})
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{name}.py' for name in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=deepcopy(source)
    protocol.update(schema_version='lf-circle-tip-saved-load-step-card-1.0',card=CARD,source_baseline_commit=BASE,
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_step1',view_directory=REL+'/run_001/view',
        parent_result=PARENT+'/result.json',selected_state_index=2,geometry_file=geometry,
        original_task_file=OLD+'/pilot_task.json',task_file=REL+'/step_task.json',task_metadata=metadata,
        complete_task_targets_mm=[0.,.25,.5,.75],targets_mm=[.5,.75],
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings=inputs,source_bindings=sources,pure_view_bindings={name:sources[name] for name in pure_names},
        old_scientific_inputs=old_inputs,expected_requested_targets=2,
        source_anchor=dict(accepted_index=2,original_target_index=2,d_mm=.5,state_sha256=selected['state_sha256'],R_input_N=selected['R_input']),
        old_input_scope='Only the original parent geometry four masks and selected split lift/fluctuation; producer seals plus stat before helper, identity hash/decode inside sole authorized helper. No old model/force/tangent/matrix payload.',
        task_execution_scope='Only suffix [.5,.75] is newly executed, including fresh anchor F/T verification; complete [0,.25,.5,.75] task prefix is inherited, not replayed.',
        qualification_scope='One saved load-only extension and actual saved observations; no complete path replay, independent HP, pressure, effective grip, unloading/release/stability, domain-width convergence or HF5 qualification.',
        direct_user_request=REQUEST,created_utc=datetime.now(timezone.utc).isoformat())
    protocol.pop('old_scientific_input',None)
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        scope='Explicit user approval for one .50 to .75 saved extension, actual deformation/reaction/tip/right-medium/convergence views, records, normal main push and different-path local Git restoration.'))
    card='''# L-CTIPSTEP1：最右尖端对向圆形工件，保存态.50→.75 mm

用户已明确批准实现并执行本卡。整体目标是独立HF读取LF结构，逐步完成大变形第三介质接触的加载/卸载分析与可用接口；本轮只延伸一个加载目标，以观察尖端接近、反力及右侧介质，不重做旧加载前缀。

源为L-CTIPPILOT1成功末态accepted2/global2，d=.50mm、state SHA c8f41107026000f09d395eb7a091ce6501b532b0a8d69210b22a94d55e8c8392、signed R=.08602790333542189N。新task保完整[0,.25,.50]前缀并仅追加.75，input.target改.75，四个说明metadata据实更新；现有evaluate_native(saved_result=parent, selected_state_index=2, extend_path=True)复核fresh F/T锚并执行suffix[.50,.75]。实际接受态N随原内部二分，全部保存，不硬锁N=2。

r9mm、圆心(80,40)mm固定ux/uy，92×40mm下半域、h.5、厚20mm；E1MPa、nu.3、plane strain、gamma1e-6、alpha5e-7、Lr80mm及全部支撑/端口/对称不变。顶部uy到92，右ux及非顶uy自由。仅原parent source_geometry NPZ四掩码及accepted/002/state.npz的lift/fluctuation为旧科学输入；执行前只继承producer seal/stat，唯一helper内才hash/decode，不读取旧model/force/tangent/matrix数组或媒体。

保持原mechanical/chunk256/port_projection、全部非clock设置与门：relative residual1e-9，平均约束系数1e-10及原scale，global balance1e-6，固定split求和8e-11mm、正J；maxchecks25/backtracks12/bisections4/mininc.00625。controller1800s、全部显示共享600s、helper2700/outer2760s，采样64GiB、四库线程上限16、原viewer内部8GiB；不更改CPU后端，不承诺实用16核或性能加速。

成功后一次干净pure viewer读取新model27fields及每态split2/forces16，1+2N归档、27+18N字段，生成4PNG及实际N帧GIF；一次原收敛投影另生成1PNG，共5PNG。根Agent各新PNG最多一次像素检查，GIF不额外解码。显示实际×1、R/qout、lower-half material/Hu/total有符号工件弱力、tip和整体无符号Q1最近距离及见证/交叉/重叠记录、分区J/Hu、right reference x89..92共480cell的J/Green/Hu与split位移及收敛。tip按唯一reference(80,30)找节点；条带从resident模型动态选，不硬码节点ID。镜像仅用于整体结构显示，力不自动翻倍；底右外角位移与tip距离分列。

独立全源静审通过、字节冻结后唯一启动；首终端错误停止后续科学/显示，保真实partial，仅原窗口开放时允许部分seal。无外部重试、修复重跑、延期、force、回滚、删除、新tests/HP或默认HF源码修改/安装。原内部回溯/二分允许。含实现/理由/实际效果/取舍/恢复记录、main普通推送与恢复核对。

必须保留suffix语义：parent success不改，task_target_executed及full_original/full_extended完成不升级，按原API报告new_peak/segment等。无新布局独参、压力、有效夹持、完整循环/自由释放、稳定性、网格/域宽收敛或HF5资格。根据实际结果再建议下一步，本卡不自动推进更大行程。
'''
    (AUTHOR/'L-CTIPSTEP1_CARD.md').write_text(card.rstrip()+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(sources),input_bindings=len(inputs),old_payload_reads=0,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'))))


if __name__=='__main__':main()
