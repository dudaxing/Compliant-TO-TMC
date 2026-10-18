"""Assemble the directly authorized tip-facing pilot using ordinary records only."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_pilot_001'
PREP='lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001/run_001'
OLD='lf_data_preparation/native_interface_001/lf_circle_right_pilot_001'
BASE='036fd5d9298525894b5f90a37dab8f258d6cc9b1'
CARD='L-CTIPPILOT1'
REQUEST='好的，按你的建议，从零执行新布置0→0.25→0.50 mm短行程试算。保持半径9 mm、圆心(80,40) mm、右域界92 mm、正则化长度80 mm，其余物理条件和原验收门不变。注意做好记录，可视化实际变形、反力和收敛情况，重点检查最右尖端的接近过程及右侧介质表现，再根据结果安排后续计算。'
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
    metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c80_domain92_Lr80_h05_alpha5em7_load05__L_CTIPPILOT1',
        purpose='tip_facing_circle_LF_zero_start_short_loading_pilot',
        parameter_origin='L-CTIPPILOT1 direct user request: zero-start load_only0/.25/.5 at fixed circle r9/(80,40), right92, regularization length80; all other physical values and original gates preserved.',
        description='Short tip-facing circle trial in extended92mm domain; actual reference-tip approach and six-column right-medium fields observed from saved arrays.')
    parent=read(ROOT/PREP/'task.json')
    assert parent['path']==dict(kind='load_only',targets_mm=[0.,.25,.5]) and parent['input']['target_mm']==.5
    task=deepcopy(parent);task.update(metadata)
    assert task['workpiece']==dict(kind='fixed_rigid',shape='circle',center_mm=[80.,40.],radius_mm=9.,fixed_components=[0,1])
    assert task['regularization']['length_mm']==80.
    write(AUTHOR/'pilot_task.json',task)
    source=read(ROOT/OLD/'protocol.json')
    settings=deepcopy(source['settings']);settings['time_limit_seconds']=1800.
    assert settings==source['settings']
    geometry=PREP+'/model/source_geometry/geometry.json'
    payload=PREP+'/model/source_geometry/geometry.npz'
    inherited=read(ROOT/PREP/'execution_receipt.json')['outputs'][payload]
    assert (ROOT/payload).stat().st_size==inherited['bytes']==1636
    assert inherited['sha256']==read(ROOT/geometry)['arrays']['sha256']
    sources={name:pin(ROOT/name) for name in source['source_bindings'] if name.startswith('hf_repo/')}
    sources.update({REL+'/'+name:pin(AUTHOR/name) for name in names})
    pure_names=[REL+'/circle_saved_views.py']+[f'hf_repo/src/hf_eval/{name}.py' for name in ('__init__','boundary_geometry','native_region_geometry','workpiece_nodal')]
    pure={name:sources[name] for name in pure_names}
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=dict(schema_version='lf-circle-tip-short-pilot-card-1.0',card=CARD,source_baseline_commit=BASE,
        controller_seconds=1800,viewer_seconds=600,helper_seconds=2700,outer_seconds=2760,sampled_RSS_bytes=64*1024**3,
        cpu_thread_limit=16,cpu_thread_environment={name:'16' for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',production_directory=REL+'/run_001/wave_circle_tip_pilot',view_directory=REL+'/run_001/view',
        geometry_file=geometry,task_file=REL+'/pilot_task.json',original_task_file=PREP+'/task.json',task_metadata=metadata,
        targets_mm=[0.,.25,.5],settings=settings,options=deepcopy(source['options']),gates=deepcopy(source['gates']),
        settings_source_protocol=OLD+'/protocol.json',gates_source_protocol=OLD+'/protocol.json',
        viewer_source=REL+'/circle_saved_views.py',convergence_source=REL+'/plot_convergence.py',
        input_bindings={geometry:pin(ROOT/geometry),payload:inherited['sha256'],PREP+'/task.json':pin(ROOT/PREP/'task.json'),REL+'/pilot_task.json':pin(AUTHOR/'pilot_task.json'),OLD+'/protocol.json':pin(ROOT/OLD/'protocol.json')},
        source_bindings=sources,pure_view_bindings=pure,old_scientific_input=dict(path=payload,**inherited,
            scope='Sole old NPZ, derived HF analysis geometry; original TIPPREP helper seal plus stat before run. Payload reads only in unique new helper; no old model/state/media.'),
        source_binding_scope='Current default HF source closure plus study/launcher/viewer/convergence; default bytes unchanged. Pure viewer closure five files with lazy package initialization.',
        expected_grid=dict(shape_yx=[80,184],extent_mm=[92.,40.],cell_size_mm=[.5,.5]),
        tip_reference_mm=[80.,30.],right_medium_reference=dict(x_min_mm=89.,x_max_mm=92.,columns=6,rows=80,cells=480),
        expected_PNGs=5,expected_GIFs=1,expected_requested_targets=3,
        accepted_states_policy='Actual N may increase through original bounded internal bisection; retain every accepted state and chronology.',
        viewer_payload_scope='One new model NPZ27 fields plus each actual state2/forces16 fields:1+2N archives and27+18N fields. Right-medium observations reuse resident arrays; no new F/T or tangent payload decode.',
        default_installations=0,new_tests=0,new_HP_calls=0,
        display_resource_scope='One600s clock shared by clean saved viewer/right-medium summary, convergence, table and page; original viewer internal8GiB cap retained. Seal inside helper2700.',
        right_medium_scope='Actual reference body right89 to domain right92: six native columns over80rows,480 nonbody medium cells; select dynamically from saved model. Track nine-point J/F-Green extrema, cellwise Hu, displacement and coordinate-located reference tip(80,30).',
        stop_policy='One launch. First terminal error closes later science/display; retain actual partial, partial seal only while original window open. No external retry, repair rerun, extension, force, rollback or delete. Original internal backtracking/bisection permitted.',
        qualification_scope='New-layout short load-only pilot and saved observations; no original full cycle, independent reference, pressure, effective grip, unloading/release/stability, domain-width convergence or HF5 qualification.',
        pixel_inspection_scope='Five actual new PNGs at most once each; no extra GIF decode; actual frame count checked by producer.',
        direct_user_request=REQUEST,created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card=CARD,approval_card=CARD,authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        scope='Directly authorized zero-start three-target tip-circle pilot; resident saved deformation/reaction/convergence/tip/right-medium views, one inspection per newPNG, records, normal main publication and restore.'))
    card='''# L-CTIPPILOT1：新92mm域、圆底对向tip的零起点短程

用户已直接授权本轮实现与执行，无需再次询问。依据L-CTIPPREP1的72/72准备检查，从零用一次现有evaluate_native执行明确load_only[0,0.25,0.50]mm/input0.50。整体目标是独立HF读取LF结构并逐步完成大变形第三介质接触与加载/卸载功能；本轮验证新布置的真实接近、反力、收敛和右介质。

r9mm、圆心(80,40)mm固定ux/uy，92×40mm下半域、h.5；正则化物理长度Lr80mm、alpha5e-7、gamma1e-6、E1MPa、nu.3、plane strain、厚20mm及原支撑/端口/对称保持。顶部uy已在准备中明确延至92，右ux/非顶uy自由；不新加边界夹持。prepared task本来就是三目标短路径，本轮仅改四个任务说明metadata；新geometry实际身份绑定保持。不搬用旧84mm保存态。

原生产门relative residual1e-9、平均约束1e-10、global balance1e-6、固定split位移8e-11mm保持；所有原settings/options逐值不变（clock1800同前pilot）。唯一controller1800s、全部显示共享600s、helper2700/outer2760s（最多46min），采样64GiB、四库各16线程，原SUP2清理与纯viewer内部8GiB门保持；CPU后端不改。

唯一旧NPZ是已准备的新92域source_geometry/geometry.npz，1636B；执行前只继承原seal/stat，进入唯一helper窗口后才读。不读旧model/state/媒体，无新测试、默认源码安装、HP、力核/切线更改。原内部Newton回溯/二分允许，按实际接受态N保存，不硬锁三态。

成功后新干净进程一次读取本轮新model/state/forces，1+2N归档、27+18N字段；复用resident数组。尖端按唯一(80,30)物质坐标查节点并跟踪实际位移，不用旧10300或硬码新ID。整体unsigned Q1最近距离与tip投影分列，global函数firstpair不穷举正距ties，tip精确并列边保留；不据同距声称唯一首触。

新右条带由实际body右端和domain右界动态确定，期望reference x89..92、6列×80行=480个非实体非body介质单元。用保存九点J/F计算Green应变、per-cell Hu、ties/位置与split位移、实际x92边界观察；不沿用旧x83..84/160cell选择器，不增加数组/字段读取或新F/T。相接body节点和顶部uy仍固定，介质单元分类不等于所有节点自由。

输出5PNG（实际×1变形/反力、距离/工件分力、峰值场、右介质局部、收敛）、实际N帧动画、状态表与人工页；镜像只用于完整结构显示，力值保持原下半模型有符号material/Hu/total弱力。五张新PNG各至多一次root像素检查，GIF实际帧数由原producer核对，不另解码。

最终源码独立静审冻结后唯一启动，首个终端错误停止后续科学/显示并保真实partial；只在原窗口开放时允许部分seal，无外部重试、修复重跑、延期、force、删除或回滚。含完整结果/取舍记录、main普通推送与恢复核对。原结果/资格保持；本轮不授整循环、独参、连续压力、有效夹持、卸载/自由释放、稳定性、域宽收敛或HF5资格。根据实际距离/分区J/介质/收敛成本再规划下一步，不自动更大行程。
'''
    (AUTHOR/'L-CTIPPILOT1_CARD.md').write_text(card.rstrip()+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='assembled_not_executed',protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),source_bindings=len(sources),input_bindings=5,old_payload_reads=0)))


if __name__=='__main__':main()
