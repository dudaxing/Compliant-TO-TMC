"""Freeze one measurement per actual saved state after terminal production."""
from pathlib import Path
import ast
import hashlib
import json
import shutil

ROOT = Path(r'D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
DATA = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_007'
STAGE = ROOT/'functional_views/native_workpiece_cycle007_20261004/boundary_saved_001'
OLD = ROOT/'functional_views/native_workpiece_cycle004_20261004/boundary_saved_001'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not STAGE.exists()
launch = json.loads((DATA/'production_launch.json').read_text(encoding='utf-8'))
assert launch['status'] in ('pass','not_pass') and 'exit_code' in launch
result = json.loads((DATA/'result/result.json').read_text(encoding='utf-8'))
expected_calls = len(result['states'])
assert expected_calls == result['accepted_states'] and expected_calls > 0
payload = (OLD/'measure_saved_once.py').read_bytes()
old = b'assert calls == completed == 3'
assert payload.count(old) == 1
payload = payload.replace(old, b"assert calls == completed == protocol['expected_geometry_calls']")
ast.parse(payload)
compile(payload, 'measure_saved_once.py', 'exec')
STAGE.mkdir(parents=True)
(STAGE/'measure_saved_once.py').write_bytes(payload)
shutil.copyfile(DATA/'launch_cycle007.py', STAGE/'launch_phase.py')
(STAGE/'sources').mkdir()
bindings = {}
for name in ('hf_repo/scripts/measure_native_workpiece_boundaries.py', 'hf_repo/src/hf_eval/boundary_geometry.py',
             'hf_repo/src/hf_eval/__init__.py'):
    path = ROOT/name
    copied = STAGE/'sources'/path.name
    shutil.copyfile(path,copied)
    for bound in (path,copied):
        bindings[bound.relative_to(ROOT).as_posix()] = sha(bound)
for path in (DATA/'result').rglob('*'):
    if path.is_file():
        bindings[path.relative_to(ROOT).as_posix()] = sha(path)
(STAGE/'README.md').write_bytes('''# Cycle007全部实际保存态的无符号外边界测量

整体目标是可检查的真实力学及接触相关观察。本卡只读007真实terminal后的全部接受态，每index各测一次（含重复目标/二分态），不按stateSHA去重，不借004测量。复用原Q1外边线段算法，排除y40镜像切口；原交叉/roundoff-near-touch/容差语义不变。partial如存在仅作未资格保存态观察，不能据测距补授力学资格。

唯一measure helper/outer120秒、8GiB采样树，含import/hash/IO，无OS硬cap或force。新wrapper只把旧固定3次调用前置改为协议中按实际接受态固定的N次；原函数/参数/返回/采样/恢复hook不变。首错停止，无修复重试/额度延长。0F/T/新模型/solver/HP，仅实际N次几何。

输出unsigned exterior boundary欧氏最短距（left组最近点可能在下角），不是signed normal gap/包容/压力或有效夹持；containment未测，不能将微小第三介质合力认定接触。源代码自有副本、实际result全部保存文件绑定，原node-window仅代理，图仅读本测量JSON显示实际距离。结果及费用写本目录RESULTS，原生产/参考/旧失败独立保留。
'''.encode('utf-8'))
for path in STAGE.iterdir():
    if path.is_file():
        bindings[path.relative_to(ROOT).as_posix()] = sha(path)
relative = STAGE.relative_to(ROOT).as_posix()
protocol = dict(schema_version='native-cycle007-saved-boundary-card-1.0', bindings=bindings,
    input_directory=(DATA/'result').relative_to(ROOT).as_posix(), expected_geometry_calls=expected_calls,
    sampled_RSS_bytes=8*1024**3,
    phases=dict(measure=dict(argv=[relative+'/measure_saved_once.py'], helper_seconds=120, outer_seconds=120)))
(STAGE/'protocol.json').write_bytes((json.dumps(protocol,indent=2,allow_nan=False)+'\n').encode('utf-8'))
print(json.dumps(dict(status='new_saved_boundary_prepared', bindings=len(bindings), expected_geometry_calls=expected_calls,
    protocol_sha256=sha(STAGE/'protocol.json'), geometry_calls=0, new_mechanics_calls=0)))
