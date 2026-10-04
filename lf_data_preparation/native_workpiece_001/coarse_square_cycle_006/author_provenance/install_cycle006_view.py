"""Freeze one saved-only cycle006 view, including already measured boundaries."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(r'D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(r'D:/hf-native-workpiece-cycle006-author-20261004')
DATA = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_006'
VIEW = ROOT/'functional_views/native_workpiece_cycle006_20261004/saved_001'
MEASURE = ROOT/'functional_views/native_workpiece_cycle006_20261004/boundary_saved_001'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
assert read(DATA/'production_launch.json')['status'] == 'pass'
assert read(DATA/'reference_launch.json')['status'] == 'pass'
assert read(MEASURE/'measure_launch.json')['status'] == 'pass'
assert not VIEW.exists()
assert all((DATA/'sources'/n).is_file() for n in ('boundary_geometry.py','measure_native_workpiece_boundaries.py'))
VIEW.mkdir(parents=True)
shutil.copyfile(AUTHOR/'plot_cycle006_saved.py', VIEW/'plot_cycle006_saved.py')
shutil.copyfile(DATA/'launch_cycle006.py', VIEW/'launch_phase.py')
for source,name in (('cycle006_saved_view_static_review.json','static_source_review.json'),
                    ('cycle006_saved_view_math_review.json','static_math_review.json')):
    shutil.copyfile(AUTHOR/source, VIEW/name)
(VIEW/'README.md').write_text('''# Cycle006实际五态路径与保存边界图

只读schema1.2/16force字段的实际生产记录和已经完成的五次边界测量。保留全部接受index及重复目标，实际峰值取argmax(d)；×1峰值/卸载返回、4×辅助放大、输入/支持/固定下半体作用力、输出/minJ/材Hu分量及实际Newton/trial顺序同图展示。共同N箭头比例、真实mm色标；4×图无力箭头。CSV每实际态一行。无插值/动画/新F/T/consumer/scatter/solver/HP/几何调用。

曲线和峰值最近点线来自保存的unsigned Q1外边界测量；排除y=40对称切口，left最近点可能是下角，不是水平normal gap。节点窗口代理在CSV单独保留，边界距不能当signed penetration、压力或有效夹持判据。

唯一render helper/outer120秒、8GiB采样树，含imports/IO/绑定前后hash，非OS硬cap；首错停，不修复重试/force。历史绝对来源路径映射至stage自有caps与保存归档，核对原SHA。所有实际生产与测量文件、普通输入、纯数字行helper及新图源码绑定。

图题PRODUCTION ONLY UNQUALIFIED表示本查看器不加载独立参考且不回填原生产资格flags。本轮已另行完成10次fresh HP80/120和96781项原门检查，具体范围见coarse_square_cycle_006/RESULTS.md与reference/summary.json。辅助材料能量明确未计算；图不授予能量/应力HP/全列切线/压力/有效夹持资格。
''', encoding='utf-8')
paths = [DATA/name for name in ('execution_receipt.json','input_inventory.json','source_freeze.json','accepted_progress.jsonl')]
paths.extend(p for p in (DATA/'sources').iterdir() if p.is_file())
paths.extend(p for p in (DATA/'result').rglob('*') if p.is_file())
paths.extend(ROOT/name for name in read(DATA/'input_inventory.json')['input_bindings'])
paths.append(ROOT/'functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py')
paths.extend(MEASURE/name for name in ('protocol.json','measure_launch.json','measurement_receipt.json','measurement_001/boundary_measurements.json'))
paths.extend(p for p in VIEW.iterdir() if p.is_file())
bindings = {p.relative_to(ROOT).as_posix():sha(p) for p in paths}
relative = VIEW.relative_to(ROOT).as_posix()
protocol = dict(schema_version='native-cycle006-saved-production-view-card-1.0', bindings=bindings,
    sampled_RSS_bytes=8*1024**3, phases=dict(render=dict(argv=[relative+'/plot_cycle006_saved.py',
        '--stage',DATA.relative_to(ROOT).as_posix(),'--output',relative+'/render_001',
        '--protocol',relative+'/protocol.json','--measurements',
        (MEASURE/'measurement_001/boundary_measurements.json').relative_to(ROOT).as_posix()],
        helper_seconds=120,outer_seconds=120)),
    stop_policy='One render; first failure closes this view card; no repair/retry/force')
(VIEW/'protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(dict(status='saved_view_prepared',bindings=len(bindings),protocol_sha256=sha(VIEW/'protocol.json'),numerical_calls=0)))
