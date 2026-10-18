"""Assemble the directly authorized right-circle geometry preparation; ordinary files only."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/lf_circle_right_preparation_001'
BASE = 'e509330e5db82eced1b92a20dda02a24fb3e3ae6'
REQUEST = '好的，按你的建议先做面向最右尖端的圆形工件右移布置与未变形兼容性检查，核清域边界和右侧介质，其余物理条件保持不变。注意做好记录和可视化，再根据检查结果安排短行程试算。'
read = lambda p: json.loads(p.read_bytes())
pin = lambda p: sha256(p.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def main():
    git = lambda *a: subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD') == BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists()
    for name in ('execute_preparation.py','layout_analysis.py','launch_preparation.py'):
        ast.parse((AUTHOR/name).read_bytes())
    gp = 'lf_data_preparation/native_interface_001/lf_batch_input_preparation_001/run_001/prepared/001/derived_geometry/geometry.json'
    tp = 'lf_data_preparation/native_interface_001/lf_circle_first_unload_005/unload_task.json'
    descriptor = read(ROOT/gp)
    array = (Path(gp).parent/descriptor['arrays']['path']).as_posix()
    inherited = read(ROOT/'lf_data_preparation/native_interface_001/lf_circle_input_preparation_001/protocol.json')['old_scientific_input']
    assert inherited['path'] == array and inherited['sha256'] == descriptor['arrays']['sha256']
    assert inherited['bytes'] == (ROOT/array).stat().st_size == 1603
    # Bind current source bytes conservatively; no import/test or scientific payload read.
    prior_sources = read(ROOT/'lf_data_preparation/native_interface_001/lf_circle_first_unload_005/protocol.json')['source_bindings']
    source_names = [name for name in prior_sources if name.startswith('hf_repo/')]
    sources = {name:pin(ROOT/name) for name in source_names}
    for name in ('execute_preparation.py','layout_analysis.py','launch_preparation.py'):
        sources[REL+'/'+name] = pin(AUTHOR/name)
    cwd = AUTHOR/'execution_cwd'
    cwd.mkdir(exist_ok=False)
    protocol = dict(card='L-CRIGHT1',schema_version='lf-circle-right-preparation-card-1.0',source_baseline_commit=BASE,
        helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=64*1024**3,cpu_thread_limit=16,
        cpu_thread_environment={name:'16' for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},
        working_directory=cwd.as_posix(),output_directory=REL+'/run_001',case_label='wave_circle_right',
        geometry_file=gp,baseline_task_file=tp,
        workpiece=dict(kind='fixed_rigid',shape='circle',center_mm=[74.,40.],radius_mm=9.,fixed_components=[0,1]),
        task_metadata=dict(task_id='EXPLORATORY_wave_fixed_circle_r9_c74_h05_alpha5em7__L_CRIGHT1',
            purpose='right_circle_LF_input_and_undeformed_compatibility',
            parameter_origin='L-CRIGHT1 direct user request: shift the fixed r9 circle right by3mm to(74,40); preserve all other physical conditions. Parent17targets/input1.4 remain unexecuted instructions.',
            description='One undeformed native model; compare fixed reference tip(80,30), physical Q1 edges, actual84mm domain and remaining right medium. No loading or force response.'),
        analysis_source=REL+'/layout_analysis.py',
        input_bindings={gp:pin(ROOT/gp),tp:pin(ROOT/tp),array:inherited['sha256']},source_bindings=sources,
        old_scientific_input=dict(path=array,bytes=inherited['bytes'],sha256=inherited['sha256'],
            identity_basis='Inherited original producer seal plus stat at preparation/freeze; sole old NPZ payload may be read only within this unique helper window.'),
        source_binding_scope='Conservative current default sources inherited from C5 source list plus new study/launcher; not every module is necessarily imported.',
        expected_model_builds=1,expected_model_writes=1,expected_PNGs=1,
        authorized_default_installations=0,authorized_tests=0,authorized_new_F_T_HP_solver_calls=0,
        source_snapshot_scope='Original write_native_project stores original descriptor/NPZ snapshot; no old model or state arrays read and no second model built.',
        stop_policy='Unique invocation; first terminal error stops subsequent analysis/plot. Retain actual partial; only a remaining-window partial seal. No retry, repair rerun, extension, force, rollback or deletion.',
        qualification_scope='Input/model/undeformed geometry compatibility only; no pressure, effective-grip, release, stability, new independent-reference or HF5 qualification. A right-medium strip does not demonstrate domain-width convergence.',
        direct_user_request=REQUEST,created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    write(AUTHOR/'authorization.proposed.json',dict(card='L-CRIGHT1',approval_card='L-CRIGHT1',authorized=True,
        authorization_from_direct_human_request=True,one_invocation=True,direct_human_request=REQUEST,
        authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        scope='One new right-circle input/model preparation, undeformed comparison PNG and one pixel inspection, records, ordinary main publication and restore. Short-stroke solve is excluded.'))
    card = '''# L-CRIGHT1：面向最右尖端的圆形工件右移准备

用户已直接授权本轮输入准备与未变形检查。整体目标是使独立HF分析器接收LF几何，并逐步验证大变形接触、反力及加载/卸载功能；本轮只解决布置、域与运动学兼容性，不推进平衡路径。

候选：圆形固定工件r9mm，圆心从(71,40)右移至(74,40)mm；其余物理条件逐值保持。h0.5mm、84×40mm下半HF域、E1MPa、nu0.3、plane strain、厚20mm、gamma1e-6、alpha5e-7、Lr80mm、原端口/支撑/背景对称及固定工件保持。C5原17目标ordered_cycle及input1.4仅保存在新任务，全部未执行；只修改center_x及四项说明metadata，旧任务/结果不改。

80mm是原LF域右界，也是固定参考尖端(80,30)的x坐标；实际HF域右界是84mm。选择74而非75，使解析圆与实际Q1边界有望保留1mm右侧余量；必须以真实数组核验，不以解析包络代替介质检查。

唯一helper180秒，outer240秒；采样RSS64GiB，OMP/MKL/OpenBLAS/NumExpr线程上限均16，在依赖导入前设置。沿用原SUP2同实例终止、成员覆盖与句柄释放清理合同。一次构模、一次保存、一张未变形四面板PNG；同驻留网格重建旧圆，无第二模型。唯一旧科学输入为原wave的1603B geometry.npz；不读旧model/state NPZ或媒体。

检查四掩码、网格/坐标/连接、ports/方向/权重、支撑/对称、固定和自由DOF、工件非空/原passive_void/不碰机构和端口/顶部覆盖、实际Q1暴露边；比较两圆的有限边最近距离与固定参考尖端距离；核右侧完整自由介质列及x84节点约束。距离只表示未变形几何，不代表接触起点或有效夹持。

先完成静态独立审阅和冻结，再唯一启动；首个终端错误即停止后续阶段，保真实partial，原窗口仍开放时仅允许部分封存。无外部重试、修复重跑、延期、force、删除或回滚。无新默认源码、测试、F/T/HP/平衡求解或GPU计算。成功后新PNG只检查一次；记录实际结果、下一步建议，普通main推送及异地恢复。

本轮不启动短行程试算。根据实际兼容性/介质余量决定后续新0→0.25→0.50mm任务与资源；即使几何通过，仍须观察真实变形、反力和收敛，且不能据此认定右侧域宽度已收敛、压力或有效夹持合格。
'''
    (AUTHOR/'L-CRIGHT1_CARD.md').write_text(card.rstrip()+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='assembled_not_executed',source_bindings=len(sources),protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),old_payload_reads=0)))


if __name__ == '__main__':
    main()
