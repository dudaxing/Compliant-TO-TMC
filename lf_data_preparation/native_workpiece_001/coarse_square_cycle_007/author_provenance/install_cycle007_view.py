"""Freeze one production-only view after terminal production and saved geometry."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(r'D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
DATA = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_007'
VIEW = ROOT/'functional_views/native_workpiece_cycle007_20261004/saved_001'
MEASURE = VIEW.parent/'boundary_saved_001'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
launch = read(DATA/'production_launch.json')
assert launch['status'] in ('pass','not_pass') and 'exit_code' in launch
assert len(read(DATA/'result/result.json')['states']) > 0
assert read(MEASURE/'measure_launch.json')['status'] == 'pass'
assert not VIEW.exists()
assert all((DATA/'sources'/n).is_file() for n in ('boundary_geometry.py','measure_native_workpiece_boundaries.py'))
VIEW.mkdir(parents=True)
shutil.copyfile(AUTHOR/'plot_cycle007_saved.py',VIEW/'plot_cycle007_saved.py')
shutil.copyfile(DATA/'launch_cycle007.py',VIEW/'launch_phase.py')
for source,name in (('cycle007_saved_view_static_review.json','static_source_review.json'),
                    ('cycle007_saved_view_math_review.json','static_math_review.json')):
    shutil.copyfile(AUTHOR/source,VIEW/name)
(VIEW/'README.md').write_text('''# Cycle007实际保存路径及unsigned边界图

只读schema1.2/16force字段的实际生产记录与已经完成的保存态边界测量。保留每个实际index、重复目标及二分态；峰取argmax(d)、末态取last index，不把声明1.5mm目标当实际达到。支持生产partial：保留PARTIAL/RETURN NOT REACHED与failed标记，不能因图生成获得资格。

×1实际峰值/末态、×4辅助放大、输入/支持/固定下半体作用力、qout/minJ/材Hu分量、Newton/trial与实际unsigned最近点/距离同图。所有状态共用N力箭头与真实mm色标；×4无力箭头。每接受态一CSV行，无插值/动画/新F/T/consumer/scatter/solver/HP/geometry。节点窗口代理单独保留；left欧氏最近点可能在角点，不是水平normal gap或signed penetration，未测containment。

唯一render helper/outer120秒、8GiB采样树，含imports/IO/绑定前后hash，非OS硬cap；首错停，不修复重试/force。历史来源路径以原SHA映射至stage自有caps与保存归档。绑定全部实际生产result文件、68caps、46普通输入、数字行helper、测量JSON/原receipt及新图源。

图题PRODUCTION ONLY UNQUALIFIED：本图不读取独立reference，也不回填生产原HP/equilibrium/HF flags。若本轮另行fresh参考通过，结论限其报告声明范围，请读取coarse_square_cycle_007/RESULTS.md。能量明确未计算；图不授予能量/应力HP/全列切线/压力/有效夹持资格。
''',encoding='utf-8')
paths=[DATA/name for name in ('execution_receipt.json','input_inventory.json','source_freeze.json','accepted_progress.jsonl')]
paths.extend(p for p in (DATA/'sources').iterdir() if p.is_file())
paths.extend(p for p in (DATA/'result').rglob('*') if p.is_file())
paths.extend(ROOT/name for name in read(DATA/'input_inventory.json')['input_bindings'])
paths.append(ROOT/'functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py')
paths.extend(MEASURE/name for name in ('protocol.json','measure_launch.json','measurement_receipt.json','measurement_001/boundary_measurements.json'))
paths.extend(p for p in VIEW.iterdir() if p.is_file())
bindings={p.relative_to(ROOT).as_posix():sha(p) for p in paths}
relative=VIEW.relative_to(ROOT).as_posix()
protocol=dict(schema_version='native-cycle007-saved-production-view-card-1.0',bindings=bindings,
    sampled_RSS_bytes=8*1024**3,phases=dict(render=dict(argv=[relative+'/plot_cycle007_saved.py',
        '--stage',DATA.relative_to(ROOT).as_posix(),'--output',relative+'/render_001',
        '--protocol',relative+'/protocol.json','--measurements',
        (MEASURE/'measurement_001/boundary_measurements.json').relative_to(ROOT).as_posix()],
        helper_seconds=120,outer_seconds=120)),
    stop_policy='One render; first failure closes this separate saved-view card; no repair/retry/force')
(VIEW/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(status='saved_view_prepared',bindings=len(bindings),protocol_sha256=sha(VIEW/'protocol.json'),numerical_calls=0)))
