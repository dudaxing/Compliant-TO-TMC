"""Record closed construction phases and the running, unqualified new cycle."""
from hashlib import sha256
from pathlib import Path
import json
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
sha = lambda p:sha256(p.read_bytes()).hexdigest()
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
PREFIX = 'lf_data_preparation/native_workpiece_001/'
EVIDENCE = ROOT/'docs/evidence/workpiece_enlargement_20261007'


def main():
    progress = EVIDENCE/'right_margin_progress.json'
    assert not progress.exists()
    production = read(ROOT/PREFIX/'right_margin_cycle_001/production_protocol.json')
    docs = ['README.md','hf_repo/README.md','docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md','docs/WORKPIECE_ENLARGEMENT_20261007.md']
    assert not set(docs)&set(production['bindings'])
    context = EVIDENCE/'right_margin_source_context'
    context.mkdir()
    prior = {}
    for name in docs:
        destination = context/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,destination)
        prior[name] = sha(destination)
    tests = read(ROOT/PREFIX/'right_margin_validation_001/run_001/test_receipt.json')
    prep = read(ROOT/PREFIX/'right_margin_preparation_001/run_001/preparation_receipt.json')
    view_path = 'functional_views/right_margin_20261007/geometry_001/view/receipt.json'
    view = read(ROOT/view_path)
    assert tests['status'] == prep['status'] == view['status'] == 'pass'
    data = dict(schema_version='right-margin-progress-1.0',baseline_commit='abf62b04d0a384f3c9cfa352dd6232ad1d4ab3d1',
        objective='Independent HF finite-deformation TMC forward evaluation of LF geometries; test contact response and fixed-workpiece force; no HF optimizer',
        reason='Original enlarged square right face x80 touches analysis boundary; independently test right-medium-domain sensitivity with same body/ports/material/path',
        physical_delta=dict(right_columns=2,domain_mm=[82.,40.],right_margin_mm=2.,body_center_mm=[71.,40.],side_mm=18.,initial_gap_mm=1.,gamma=1e-6,Lr_mm=80.),
        implementation=['Additive analysis_domain API and CLI; original four-mask physical subdomain and LF provenance retained','Rebuild cell/node/DOF/PORT indices from physical coordinates; preserve original physics'],
        closed_phases=dict(tests=tests,preparation=prep,prepared_view=view),prepared_view_file=view_path,
        production=dict(status='running_not_qualified',stage=PREFIX+'right_margin_cycle_001',protocol_sha256=sha(ROOT/PREFIX/'right_margin_cycle_001/production_protocol.json'),
            helper_seconds=4500,outer_seconds=4560,sampled_RSS_bytes=8*1024**3,original_targets=24,HP_calls=0),
        qualification='No new right-margin equilibrium/contact/force qualification until complete production and its fresh independent reference pass',
        prior_document_sha256=prior,next='Observe the single running cycle; after actual completion freeze reference and saved-response views separately')
    progress.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    report = ROOT/docs[-1]
    text = '''

## 右侧第三介质余量：已完成构造，完整路径执行中

本项目仍以独立 HF 正向分析为目标：读取 LF 普通几何，计算大变形 TMC 响应、固定工件受力及卸载过程，供外部研究层比较。此轮检查的是分析域边界的影响。已采用的右移大工件为边长18 mm、中心(71,40) mm的固定方体，半模型覆盖[62,80]×[31,40] mm，钳尖(80,30)与底面初始间隙1 mm。原工件右面恰为x80外边界，故新增右侧2列介质，将HF分析域延到x82；原LF80×40合同、结构掩码、工件、E1/ν.3/厚20、γ=α=1e-6、Lr80、端口及24目标保持。

新增源码为`hf_repo/src/hf_eval/analysis_domain.py`及`hf_repo/scripts/prepare_analysis_domain.py`；它只生成声明的HF派生几何，不进行LF优化、材料赋值或求解。父包四掩码逐行保留，来源记录明确全域已是HF派生，原LF provenance仍是历史来源。独立5项小测试通过，实际2次小构造，0F/T/solver/HP，helper5.7181554/outer8.1710136秒（120/150秒8GiB卡已关闭）。

实际完整模型准备通过：3280单元/3403节点/6806DOF，结构1086/介质2194，450固定/6356自由；工件162单元/190节点/380DOF，顶部uy交集19。27字段中10个算子与标量raw相等，17个索引/域字段经逐行cell/node/DOF映射核对；原物理子域byte精确保持。PORT重新生成，旧钳尖2510→新2570，但物理坐标不变。一次几何写出与一次模型构造/写出，0F/T/solver/HP，helper6.6963458/outer6.9985329秒（120/150秒8GiB卡已关闭）。

保存模型的未变形布局图通过，实际读取两个模型并记录工件盒子、钳尖与1mm初始间隙；不计算力或变形，60/90秒8GiB卡关闭。图见`functional_views/right_margin_20261007/geometry_001/view/prepared_domain.png`。这些结果只证明输入与构造正确，不能代替新的夹持力资格。

下一步正在执行一次从零开始的同24目标0→1.2→0mm完整路径，内部4500/外部4560秒、8GiB。原worker、24数学源码、port_projection、chunk256和原收敛/J/Armijo门保持；域扩展adapter另入来源记录。预算根据原同body2839.9813743秒、单元数比3280/3200和1.5系数加90秒估算约4456.22秒，取4500秒；这不是完成时间承诺。失败关闭，无重试、延长或force；只有实际完整通过后才冻结独立新参考。新Fy或间隙尚无结论，不宣称域收敛、连续压力或自由体稳定夹持。

完整原始记录见`docs/evidence/workpiece_enlargement_20261007/right_margin_progress.json`及所列三个关闭阶段；原主干abf62b04的五个入口文档raw保存于同目录`right_margin_source_context/`。既有γ减半结果仍保留，本轮物理对照专用原γ1e-6完整路径，不能混借参数或旧状态。
'''
    report.write_bytes(report.read_bytes()+text.encode('utf-8'))
    intro = '''> 当前执行状态：右移18mm方体保持，HF右侧介质域已扩展到x82（2mm余量）。独立5项构造测试、3280单元模型的27字段物理映射及未变形布局图通过；新24目标夹持—卸载路径正在一次4500/4560秒8GiB预算下执行，尚无新的力学资格。详见[工作记录](WORKPIECE_ENLARGEMENT_20261007.md)与right_margin_progress.json；下方为此前已交付的γ敏感性状态。

'''
    for name in docs[:-1]:
        path = ROOT/name
        correct_intro = intro.replace('(WORKPIECE_ENLARGEMENT_20261007.md)','(docs/WORKPIECE_ENLARGEMENT_20261007.md)' if name == 'README.md' else '(../docs/WORKPIECE_ENLARGEMENT_20261007.md)' if name == 'hf_repo/README.md' else '(WORKPIECE_ENLARGEMENT_20261007.md)')
        path.write_bytes(correct_intro.encode('utf-8')+path.read_bytes())
    print(json.dumps(dict(status='construction_recorded_production_running_not_qualified',progress_sha256=sha(progress),report_sha256=sha(report))))


if __name__ == '__main__':main()
