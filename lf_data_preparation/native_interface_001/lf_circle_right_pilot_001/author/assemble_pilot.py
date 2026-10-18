"""Assemble directly authorized right-circle short pilot; ordinary input only."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_right_pilot_001'
PREP='lf_data_preparation/native_interface_001/lf_circle_right_preparation_001/run_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_first_unload_005'
BASE='0f1ba68bdf815b3818dc7711e419dfd9e0761555'
REQUEST='好的，按你的建议，从零执行右移圆形工件0→0.25→0.50 mm短行程试算。保持半径9 mm、圆心(74,40) mm、其余物理条件和原验收门不变，注意做好记录，可视化实际变形、反力和收敛情况，重点检查最右尖端的接近过程及右侧介质表现，再根据结果安排后续计算。'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists()
    names=('execute_pilot.py','circle_saved_views.py','launch_pilot.py','plot_convergence.py')
    for name in names:ast.parse((AUTHOR/name).read_bytes())
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c74_h05_alpha5em7_load05__L_CRPILOT1',
        purpose='right_circle_LF_zero_start_short_loading_pilot',
        parameter_origin='L-CRPILOT1 direct user request: zero-start load_only0/.25/.5 at fixed circle r9/(74,40), all other physical values and original gates preserved; original17task is not executed.',
        description='Short right-shifted circle trial; actual reference-tip approach and right-medium fields observed from saved arrays, no contact pressure or effective-grip qualification.')
    parent=read(ROOT/PREP/'task.json')
    task=deepcopy(parent)
    task.update(metadata)
    task['input']['target_mm']=.5
    task['path']=dict(kind='load_only',targets_mm=[0.,.25,.5])
    assert task['workpiece']==dict(kind='fixed_rigid',shape='circle',center_mm=[74.,40.],radius_mm=9.,fixed_components=[0,1])
    write(AUTHOR/'pilot_task.json',task)
    source=read(ROOT/OLD/'protocol.json')
    settings=deepcopy(source['settings']);settings['time_limit_seconds']=1800.
    assert {k:v for k,v in settings.items() if k!='time_limit_seconds'}=={k:v for k,v in source['settings'].items() if k!='time_limit_seconds'}
    geometry=PREP+'/model/source_geometry/geometry.json'
    payload=PREP+'/model/source_geometry/geometry.npz'
    inherited=read(ROOT/PREP/'execution_receipt.json')['outputs'][payload]
    assert (ROOT/payload).stat().st_size==inherited['bytes']==1603
    assert inherited['sha256']==read(ROOT/geometry)['arrays']['sha256']
    sources={name:pin(ROOT/name) for name in source['source_bindings'] if name.startswith('hf_repo/')}
    sources.update({REL+'/'+name:pin(AUTHOR/name) for name in names})
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{name}.py' for name in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    pure={name:sources[name] for name in pure_names}
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=dict(schema_version='lf-circle-right-short-pilot-card-1.0',card='L-CRPILOT1',source_baseline_commit=BASE,
        controller_seconds=1800,viewer_seconds=600,helper_seconds=2700,outer_seconds=2760,sampled_RSS_bytes=64*1024**3,
        cpu_thread_limit=16,cpu_thread_environment={name:'16' for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_right_pilot',view_directory=REL+'/run_001/view',
        geometry_file=geometry,task_file=REL+'/pilot_task.json',original_task_file=PREP+'/task.json',task_metadata=metadata,
        targets_mm=[0.,.25,.5],settings=settings,options=deepcopy(source['options']),gates=deepcopy(source['gates']),
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings={geometry:pin(ROOT/geometry),payload:inherited['sha256'],PREP+'/task.json':pin(ROOT/PREP/'task.json'),REL+'/pilot_task.json':pin(AUTHOR/'pilot_task.json'),OLD+'/protocol.json':pin(ROOT/OLD/'protocol.json')},
        source_bindings=sources,pure_view_bindings=pure,old_scientific_input=dict(path=payload,**inherited,
            scope='Sole old NPZ; original right-preparation helper seal plus stat before run. Payload reads permitted only within unique new helper. No old model/state/media read.'),
        source_binding_scope='Current default HF source closure plus study/launcher/viewer/convergence. Default sources are byte-unchanged. Pure viewer closure five files; lazy package initialization.',
        expected_PNGs=5,expected_GIFs=1,expected_requested_targets=3,
        accepted_states_policy='Actual N can increase through original bounded internal bisection; retain every accepted state and chronology.',
        viewer_payload_scope='One new model NPZ27 fields plus each actual state2/forces16 fields:1+2N archives and27+18N fields. Right-medium observations reuse same resident arrays; no new force/tangent evaluation or tangent payload decode.',
        default_installations=0,new_tests=0,new_HP_calls=0,
        display_resource_scope='One600s clock shared by clean saved viewer, added right-medium PNG/summary, convergence, table and page; original viewer internal8GiB cap retained. Whole-run seal inside helper2700.',
        right_medium_scope='Reference x83..84 two native columns across80rows; nonbody original-medium cells, not all-free nodal DOFs. Track actual coordinates, nine-point J/F-Green extrema, cellwise Hu and fixed(80,30) reference-tip node, all from saved arrays.',
        stop_policy='One launch. First terminal error closes later science/display; retain actual partial; partial seal only while original window open. No external retry, repair rerun, extension, force, rollback or delete. Original internal backtracking/bisection permitted.',
        qualification_scope='Short load-only pilot and saved observations only; no original17path, new independent reference, contact pressure, effective grip, unloading/release/stability, domain-width convergence or HF5 qualification.',
        pixel_inspection_scope='Five actual new PNGs at most once each; no extra GIF decode, framecount checked by producer.',
        direct_user_request=REQUEST,created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card='L-CRPILOT1',approval_card='L-CRPILOT1',authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        scope='Directly authorized zero-start three-target right-circle pilot, resident saved visualizations including tip/right-medium/convergence, one inspection per newPNG, records, normal main publication and restore.'))
    card='''# L-CRPILOT1：右移圆形工件零起点短行程

用户已直接授权实现和执行，无需再次询问。整体目标是独立HF读取LF结构，验证大变形第三介质接触与加载/卸载功能；本轮根据L-CRIGHT1的53/53未变形检查，实际计算右移圆的早期接近与介质响应。

新显式load_only任务[0,0.25,0.50]mm，input.target0.50，从零调用一次现有evaluate_native；不使用旧保存态或续算，不执行父文件保留的17目标长路径。半径9mm、圆心(74,40)mm、固定工件ux/uy；原h0.5、84×40下半域、E1MPa、nu0.3、plane strain、厚20mm、gamma1e-6、alpha5e-7、Lr80mm、端口/支撑/对称均保持。只改四说明字段与明确短路径/input目标，旧任务及结果保持。

原生产门：relative residual1e-9、原平均约束1e-10、global balance1e-6、fixed split位移8e-11mm；其余原settings精确保持，仅新clock1800。mechanical/chunk256/port_projection原选项。唯一controller1800s，显示共享600s，helper2700/outer2760s(最多46min)、采样64GiB、四库各16线程。原SUP2清理合同及viewer内部8GiB保持；不改变后端或使用GPU。

唯一旧NPZ为本轮父右移准备包的source_geometry/geometry.npz(1603B)，准备阶段只继承seal和stat，进入新唯一窗口才读取。无旧model/state/媒体读取、新测试、默认源码安装、HP或力核/切线修改。原内部Newton回溯/二分允许，接受态N按实际保留，不强锁三态。

成功后新干净进程一次读取本轮新model/state/forces保存数组，复用原圆形几何/节点力显示与收敛投影；5PNG(实际变形/反力、距离/工件分力、峰值场、右介质局部、收敛)与实际N帧动画。原始场/反力保持下半模型含义，完整结构图及动画镜像仅为显示。固定物质参考tip(80,30)node跟随实际位移，不动态换为背景最右节点；区分整体最近距离与tip距离。

重点观察参考x83..84两列/160个原非实体非工件介质单元，实际变形、九点J与Green主应变、cellwise Hu极值/位置、右外边界节点和原约束。复用同一驻留新数组，不多开NPZ/字段，不计算新F/T。此条带的‘自由介质’是单元分类；相接工件节点仍按原body固定，顶uy对称保留。

先静态独立审阅、冻结后唯一启动；首个终端错误停止随后科学/显示，保真实partial，仅原窗口仍开放可部分封存。无外部重试、修复重跑、延期、force、删除或回滚。五个实际新PNG各最多一次人工像素检查。包括结果记录、main普通推送和恢复核对。

几何距离/J/Hu/弱式工件力均按原定义报告，不据非零力或距离认定压力、有效夹持或域宽收敛；不授原完整路径、独参、卸载/自由释放/稳定性或HF5资格。依据本轮真实结果，再提出单目标推进或排查方案，本轮不默认继续更大行程。
'''
    (AUTHOR/'L-CRPILOT1_CARD.md').write_text(card.rstrip()+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='assembled_not_executed',protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),source_bindings=len(sources),input_bindings=5,old_payload_reads=0)))


if __name__=='__main__':main()
