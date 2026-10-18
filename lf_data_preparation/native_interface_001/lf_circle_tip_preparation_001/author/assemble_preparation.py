"""Assemble the directly authorized tip-facing domain preparation; ordinary inputs only."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001'
BASE='48c16edf92de67643b253a5005720782d6fcad10'
PARENT='lf_data_preparation/native_interface_001/lf_circle_right_preparation_001/run_001'
PILOT='lf_data_preparation/native_interface_001/lf_circle_right_pilot_001'
REQUEST='好的，按你的建议，先完成半径9 mm、圆心(80,40) mm、右域界92 mm的新布置输入准备与未变形兼容性检查。正则化长度保持80 mm，其余物理条件和原验收门不变，注意做好记录和可视化，重点核对最右尖端的对向关系及右侧介质，再根据检查结果安排短行程试算。'
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists()
    for name in ('execute_preparation.py','layout_analysis.py','launch_preparation.py'):ast.parse((AUTHOR/name).read_bytes())
    geometry=PARENT+'/model/source_geometry/geometry.json'
    descriptor=read(ROOT/geometry)
    payload=(Path(geometry).parent/descriptor['arrays']['path']).as_posix()
    seal=read(ROOT/PARENT/'execution_receipt.json')['outputs'][payload]
    assert seal['bytes']==(ROOT/payload).stat().st_size==1603
    assert seal['sha256']==descriptor['arrays']['sha256']
    task_file=PILOT+'/pilot_task.json'
    model_file=PILOT+'/run_001/wave_circle_right_pilot/model/model.json'
    inherited_file=PILOT+'/protocol.json'
    inherited=read(ROOT/inherited_file)
    assert read(ROOT/model_file)['task']==read(ROOT/task_file)
    sources={name:pin(ROOT/name) for name in inherited['source_bindings'] if name.startswith('hf_repo/')}
    for name in ('execute_preparation.py','layout_analysis.py','launch_preparation.py'):sources[REL+'/'+name]=pin(AUTHOR/name)
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=dict(card='L-CTIPPREP1',schema_version='lf-circle-tip-preparation-card-1.0',source_baseline_commit=BASE,
        helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=64*1024**3,cpu_thread_limit=16,
        cpu_thread_environment={name:'16' for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',case_label='wave_circle_tip',
        geometry_file=geometry,baseline_task_file=task_file,baseline_model_descriptor_file=model_file,
        baseline_production_protocol_file=inherited_file,right_columns=16,
        workpiece=dict(kind='fixed_rigid',shape='circle',center_mm=[80.,40.],radius_mm=9.,fixed_components=[0,1]),
        background_symmetry=dict(points_mm=[[0.,40.],[92.,40.]],components=[1]),
        task_metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c80_domain92_h05_alpha5em7__L_CTIPPREP1',
            purpose='tip_facing_circle_input_and_undeformed_compatibility',
            parameter_origin='L-CTIPPREP1 direct user request: circle r9 at(80,40), explicit HF right-domain extension84 to92mm; Lr80 and remaining physics/gates preserved. Stored short load_only0/.25/.5 is unexecuted.',
            description='One derived92mm geometry and one undeformed model; fixed reference tip(80,30), physical Q1 distance witnesses and complete right-medium/constraint checks. No loading solve.'),
        analysis_source=REL+'/layout_analysis.py',
        inherited_production_gates=inherited['gates'],inherited_solver_settings=inherited['settings'],
        inherited_solver_options=inherited['options'],inherited_solver_contract_scope='Recorded unchanged for future short trial only; no production/equilibrium gates are executed by this preparation.',
        input_bindings={geometry:pin(ROOT/geometry),payload:seal['sha256'],task_file:pin(ROOT/task_file),model_file:pin(ROOT/model_file),inherited_file:pin(ROOT/inherited_file)},source_bindings=sources,
        old_scientific_input=dict(path=payload,**seal,scope='Sole unique old NPZ. Original producer seal plus stat before run; payload reads only in unique new helper. Old model descriptor is ordinary JSON; old model/state arrays and media excluded.'),
        expected_geometry_derivations=1,expected_model_builds=1,expected_model_writes=1,expected_PNGs=1,
        expected_grid=dict(shape_yx=[80,184],origin_mm=[0.,0.],cell_size_mm=[.5,.5],extent_mm=[92.,40.]),
        expected_cells=14720,expected_nodes=14985,expected_DOFs=29970,
        authorized_default_installations=0,authorized_tests=0,authorized_new_F_T_HP_solver_calls=0,
        source_binding_scope='Conservative current default HF sources plus study/layout/launcher; not every module is necessarily imported.',
        extension_scope='Original84mm HF-derived parent gains16 passive-void columns/8mm. Source LF mechanism ends at80mm; whole92mm grid is HF-derived, without resampling or LF optimization.',
        baseline_scope='Old circle74 reconstructed on the same resident92mm grid for geometry only. Historical84mm boundary is a labelled reference, not a current boundary or an old FE solve.',
        stop_policy='Unique invocation, first terminal error stops subsequent analysis/plot; retain actual partial. Partial seal only inside still-open original helper. No retry, repair rerun, extension, force, rollback or deletion.',
        qualification_scope='Input/undeformed geometry compatibility only; tip matching shortest distance is not uniqueness or contact prediction. No new independent reference, pressure, effective grip, release, stability, boundary-width convergence or HF5 qualification.',
        direct_user_request=REQUEST,created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card='L-CTIPPREP1',approval_card='L-CTIPPREP1',authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        scope='One new derived geometry/model input preparation, one undeformed PNG and one pixel inspection, records, ordinary main publication and restore. No short-stroke solve.'))
    card='''# L-CTIPPREP1：圆底面向最右尖端的扩域准备

本轮已由用户直接授权。整体目标是用独立HF第三介质分析器接收LF结构，逐步验证大变形加载/卸载、工件作用和实际变形。前一r9/(74,40)、84mm域短程通过，但.5mm时最近点在x76横梁、tip距仍2.039mm；本轮用明确新布置核查圆底对向最右tip的假设。

候选r9/(80,40)mm；调用原write_right_medium_geometry一次，从84mm参考域追加16列h.5介质到92mm。原LF机构右端80mm，当前84mm为HF派生域；新92mm保持旧84mm子域并新增1280个介质单元，不改阈值、不重采样、不运行LF。生成独立新geometry身份，不冒用旧绑定。新网格14720cell/14985node/29970DOF为声明网格计数，圆覆盖计数以实际为准。

原E1MPa、nu.3、plane strain、厚20mm、gamma1e-6、alpha5e-7、正则化长度Lr80mm、h.5、支撑、端口物理位置/权重/方向、工件固定ux/uy保持。顶部全域uy显式延至92mm，右界ux及非顶uy沿原自由类型。新task只改变circle.center_x、background顶端、新geometry绑定及四说明metadata，保原短load_only[0,.25,.5]/input.5为未执行指令；原生产四门/settings/options原值记录并保持，本轮不运行力学验收。

一次derive、一次build、一次write、一张未变形四面板PNG。唯一旧NPZ为CRIGHT的source_geometry1603B；准备期只seal+stat，唯一helper窗口才读取。允许旧普通model.json用于节点/端口语义映射，不读旧model/state数组或媒体。原节点stride169→新185，所有旧物理端口/支撑映射重核；新tip按唯一参考(80,30)坐标查，不沿用旧ID10300。

检查四mask旧168列逐字节/field hash保持、新16列仅passive_void、网格/材料/Lr/端口/全部约束、完整圆Q1覆盖与solid/support/ports冲突、顶部覆盖、实际右介质六列及x92边界。baseline圆74在同新网格重建仅作几何对照，旧x84域界单列历史参考。两次现有public边界距离，固定tip点/有限边投影与其并列边记录；若tip距等于整体最小，只能说明它属于最短距离层级，不能声称唯一最先接触。整体正距离并列对不额外穷举。

helper180/outer240秒，采样64GiB，四库各16线程；沿原SUP2清理合同。独立静审、冻结后唯一启动，首个终端错误停后续阶段，保真实partial，仅原窗口仍开可部分封存。无外部重试、修复重跑、延期、force、删除或回滚；无新F/T/HP/平衡、测试、默认源码修改或GPU计算。新PNG最多一次人工像素检查；包含记录、普通main推送和恢复核对。

本轮只核输入和未变形兼容；解析89→92的3mm余量须以真实六列介质核实，不代表域宽收敛。依据实际tip/整体距离、对向和介质结果安排下一短程，不在本轮启动。旧通过/失败历史及压力、有效夹持、释放、稳定性、完整路径、HF5资格均保原状态。
'''
    (AUTHOR/'L-CTIPPREP1_CARD.md').write_text(card.rstrip()+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='assembled_not_executed',protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),source_bindings=len(sources),input_bindings=5,old_payload_reads=0)))


if __name__=='__main__':main()
