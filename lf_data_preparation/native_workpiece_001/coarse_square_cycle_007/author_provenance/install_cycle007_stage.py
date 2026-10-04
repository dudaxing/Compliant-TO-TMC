"""Install a new-card preparation contract; no model construction or mechanics."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess

ROOT = Path(r'D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_007'
PRIOR = STAGE.parent/'coarse_square_cycle_006'
ORIGINAL = STAGE.parent/'coarse_square_cycle_003'
BASELINE = '747f685cf6be41c6f67266005ed772d1813d62da'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, record):
    path.write_bytes((json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8'))


assert not STAGE.exists()
assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == BASELINE
assert sha(AUTHOR/'audit_cycle007.py') == '91b689bad8bb1aa5bad92ce2f62c86f08e0e1341de3d481447b47a945dc2bbb1'
sources = {
    'core_audit_mechanical.py': (PRIOR/'core_audit_mechanical.py').read_bytes(),
    'audit_cycle007.py': (AUTHOR/'audit_cycle007.py').read_bytes(),
    'prepare_cycle007.py': (AUTHOR/'prepare_cycle007.py').read_bytes(),
    'launch_cycle007.py': (PRIOR/'launch_cycle006.py').read_bytes(),
}
producer = (PRIOR/'execute_cycle006.py').read_bytes()
old_docstring = b'Execute the opt-in mechanical [0,.5,1,.5,0] path; save actual F/T range inputs.'
new_docstring = b'Execute the opt-in mechanical [0,.5,1,1.5,1,.5,0] path; save actual F/T range inputs.'
assert producer.count(old_docstring) == 1
sources['execute_cycle007.py'] = producer.replace(old_docstring, new_docstring)
for payload in sources.values():
    ast.parse(payload)
STAGE.mkdir()
for name, payload in sources.items():
    (STAGE/name).write_bytes(payload)
task = json.loads((PRIOR/'task.json').read_text(encoding='utf-8'))
task.update(task_id='EXPLORATORY_fixed_workpiece_gripper_coarse_square_cycle007_1p5mm',
    purpose='fixed_workpiece_explicit_mechanical_1p5mm_ordered_loading_return',
    parameter_origin='User delegated symmetric workpiece and larger stroke exploration; new1.5mm task chosen after actual006 complete1mm cycle, minimumJ.458189 and positive unsigned bottom exterior distance.924425mm',
    description='New continuous0/.5/1/1.5/1/.5/0 mechanical path from undeformed state; all actual accepted indices receive fresh reference; no inherited state/qualification')
task['input']['target_mm'] = 1.5
task['path'] = dict(kind='ordered_cycle', targets_mm=[0., .5, 1., 1.5, 1., .5, 0.])
write(STAGE/'task.json', task)
(STAGE/'README.md').write_bytes('''# 固定方形工件1.5 mm：新递增加载与卸载探索卡

整体目标是普通LF几何下的独立HF非线性TMC正向力、变形、平衡及接触相关指标，供外部研究比较；HF不运行LF优化/dmftd/MPM。本卡依据006真实0/.5/1/.5/0完整循环、5接受态、10新HP/96781检查，继续实现更大真实行程。006峰值minJ=.4581891642，实际unsigned底边距=.9244251793mm、左边界距=1.7901563574mm；保存几何无交叉/near-touch，未做containment测试。这些已测值只说明006，不授007接触或夹持资格。用户已授权探索对称方/圆工件和较大变形，具体1.5mm工况由Agent按上一步结果选择。

保持a2d6原27模型数组：h1mm/3200cells/6642DOFs/376fixed/6266free，固定下半方形side16mm、center(70,40)mm、原底/左初始间隔2mm。E1MPa、nu.3、plane strain、厚20mm，gamma=alpha=1e-6、Lr80mm，输出/辅助弹簧0；平均输入+x、自由输出+y。仅四描述键、input.target_mm=1.5及ordered targets[0,.5,1,1.5,1,.5,0]改变，case目标同步核对；其余物理字段/方向/源与006一致，coreD5/mean205/CLI01f6/T/CI/B52无实现更新。

机械模式schema1.2/16force/3T/full非对称CSC，辅助材料能量not_evaluated/qualified:false/field_present:false，默认complete不变。原settings、minincrement.00625mm、Newton25/Armijo/backtrack12/bisection4与原残差、约束、force/Jv/HP门、分母/CI支持域保持。不重跑旧6测试或新toy；沿用已冻结且通过的集成证据。保留所有实际接受index，重复1/.5/0及二分态不去重；从零重新连续求解，不读取006缓存作新解。

| 唯一阶段 | helper / outer秒；采样树限额 | 内容 |
|---|---|---|
| prepare | 不适用 / 60；8GiB | 保留006的39输入，再加006四前例记录与007任务/方向/README三输入，共46；原003source63的3既有转换及007五包装，共68，准备113pins |
| production | 600 / 660；8GiB | 一次连续0/.5/1/1.5/1/.5/0，保存接受缓存及首次真实F/T范围异常原输入；无额外F/T；原控制器回溯按声明算法处理；科学协议186pins |
| fresh reference | 240 / 300；8GiB | 仅production完整pass且原前置满足后，全部实际接受态各新HP80/120（至少14次），包括二分态；全部3200cells/6642DOFs、原力/Jv/CSC/KKT/工件投影门，PORT方向而非全列HP |

额度依据006真实outer生产375.0062062秒、参考102.7997052秒（helper374.0031275/102.5191004秒），31F/18T/1solver、5接受态、10HP/96781检查；七态参考约144秒仅成本估计。1.5mm收敛、压缩/minJ、算术支持与二分费用均未测，原额度不保证足够。helper含imports/构建/IO/最后hash，outer监测协同stop，无OS硬内存cap/force kill。首正式阶段失败关闭本卡，保partial/首捕/原错误，不修复重试/增加额度或放门。声明控制器内部范围拒绝、回溯与二分是原算法，不是另起外部调用；记录真实started/completed计数。

实际数据生成后再冻独立保存图/几何卡，显示真实×1结构、共用N力箭头/真实mm色条、R/qout/minJ、下半工件材/Hu/总FxFy、镜像净力及残余，全部接受index保持求解顺序。真实unsigned Q1外边界距/交叉/near-touch与node-window代理分别说明，左边界最近点可能在角点，不当侧壁法向gap。partial不自动获资格，保存图保生产/失败/未资格标签，不补算平衡。

尚未授予能量/应力HP/全列T/一般支持域、旧未知T25/拒绝trial、signed normal gap/containment/接触法向压力/有效夹持或自由工件资格。006正unsigned距不能外推1.5mm接触阈值，小第三介质合力也不能证明夹持。根据007实际结果再选择下一行程、圆r8或细工况；已构建模型不等于已求解，不称不同LF设计为网格收敛。H2/H3/HF5/完整AD/JIT及整体HF目标仍未完成。

本卡目标、实现、原因、实际结果/成本/范围与下一步写本目录RESULTS及现有CURRENT_STATUS/NUMPY_FORCE_PROGRESS，保留006/004/003及closed005原证据；后续main与origin https://github.com/dudaxing/Compliant-TO-TMC.git保持。
'''.encode('utf-8'))
base_sources = json.loads((ORIGINAL/'source_freeze.json').read_text(encoding='utf-8'))['sources']
old_inputs = json.loads((PRIOR/'input_inventory.json').read_text(encoding='utf-8'))['input_bindings']
bindings = {name: sha(ROOT/name) for name in base_sources}
bindings.update(old_inputs)
for path in (PRIOR/'input_inventory.json', PRIOR/'source_freeze.json', PRIOR/'execution_receipt.json', PRIOR/'reference/summary.json'):
    bindings[path.relative_to(ROOT).as_posix()] = sha(path)
for path in sorted(STAGE.iterdir()):
    if path.is_file():
        bindings[path.relative_to(ROOT).as_posix()] = sha(path)
assert len(bindings) == 113
write(STAGE/'prepare_protocol.json', dict(schema_version='native-mechanical-cycle-card-1.0',
    baseline_commit=BASELINE, sampled_RSS_bytes=8*1024**3, bindings=bindings,
    phases=dict(prepare=dict(argv=[(STAGE/'prepare_cycle007.py').relative_to(ROOT).as_posix()], outer_seconds=60)),
    scope='Preparation only; production/reference bindings assembled only after unique actual preparepass'))
print(json.dumps(dict(status='new_stage_installed', prepare_bindings=len(bindings),
    targets_mm=task['path']['targets_mm'], prepare_protocol_sha256=sha(STAGE/'prepare_protocol.json'), numerical_calls=0)))
