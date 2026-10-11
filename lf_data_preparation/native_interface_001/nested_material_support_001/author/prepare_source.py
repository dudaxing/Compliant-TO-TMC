"""Prepare ordinary M-SUPPORT1 source/metadata only; never import its candidate."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
WORK = Path(__file__).resolve().parent
STAGE_NAME = 'lf_data_preparation/native_interface_001/nested_material_support_001'
STAGE = ROOT/STAGE_NAME
BASE = '96bfea73ebb538d413dd01b722fa1f3a6d43913d'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

assert subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip() == BASE
assert subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True) == ''
assert not STAGE.exists()
scope, basis, peer = (read(WORK/name) for name in ('support_input_scope.json','support_physical_basis.json','support_static_physics_review.json'))
assert peer['status'].startswith('pass')
STAGE.mkdir()
(STAGE/'author').mkdir()
copies = {
    'saved_material_support.py': ROOT/'hf_repo/src/hf_eval/saved_material_support.py',
    'execute_saved_material_support.py': STAGE/'execute_saved_material_support.py',
    'M-SUPPORT1_CARD.md': STAGE/'M-SUPPORT1_CARD.md',
    'support_input_scope.json': STAGE/'author/support_input_scope.json',
    'support_physical_basis.json': STAGE/'author/support_physical_basis.json',
    'support_static_physics_review.json': STAGE/'author/support_static_physics_review.json',
    'prepare_source.py': STAGE/'author/prepare_source.py',
}
for name, target in copies.items():
    assert not target.exists()
    target.write_bytes((WORK/name).read_bytes())
old_receipt = Path('D:/hf-native-workpiece-api-author-20261009/MPTRACE1_execution_review_001/publication_receipt.json')
assert sha(old_receipt) == scope['prior_actual_provenance']['sha256']
(STAGE/'author/MPTRACE1_publication_receipt.json').write_bytes(old_receipt.read_bytes())
launcher = ROOT/'lf_data_preparation/native_interface_001/nested_material_trace_001/launch_trace.py'
(STAGE/'launch_support.py').write_bytes(launcher.read_bytes())
data = scope['proposed_runtime_input_plan']['runtime_data_files']
bindings = {row['path']:row['sha256'] for row in data}
sources = sorted(set(row['path'] for row in basis['source_bindings']) | {
    'hf_repo/src/hf_eval/__init__.py','hf_repo/src/hf_eval/native_map.py','hf_repo/src/hf_eval/native_force.py',
    'hf_repo/src/hf_eval/saved_material_support.py',
    f'{STAGE_NAME}/execute_saved_material_support.py',f'{STAGE_NAME}/launch_support.py',
    f'{STAGE_NAME}/M-SUPPORT1_CARD.md',f'{STAGE_NAME}/author/support_input_scope.json',
    f'{STAGE_NAME}/author/support_physical_basis.json',f'{STAGE_NAME}/author/support_static_physics_review.json',
    f'{STAGE_NAME}/author/MPTRACE1_publication_receipt.json',
    'lf_data_preparation/native_interface_001/nested_material_trace_001/protocol.json',
    'lf_data_preparation/native_interface_001/nested_material_trace_001/run_001/execution_receipt.json',
    'lf_data_preparation/native_interface_001/nested_material_trace_001/RESULTS.md',
})
bindings.update({name:sha(ROOT/name) for name in sources})
assert all(sha(ROOT/name) == pin for name,pin in bindings.items())
case = 'lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square'
view = 'functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square'
trace = 'lf_data_preparation/native_interface_001/nested_material_trace_001'
protocol = dict(schema_version='saved-fixed-square-material-support-card-1.0', prepared=True, authorized=False, executed=False,
    baseline_main=BASE, card=f'{STAGE_NAME}/M-SUPPORT1_CARD.md', model_file=f'{case}/model/model.json',
    result_file=f'{case}/result.json', state_files={str(i):f'{case}/accepted/{i:03d}/state.json' for i in (6,13)},
    nodal_files={str(i):f'{view}/{i:03d}/nodal.json' for i in (6,13)},
    material_trace_file=f'{trace}/run_001/material_trace.json', material_trace_sides_file=f'{trace}/run_001/sides.csv',
    material_trace_whole_file=f'{trace}/run_001/whole_material_comparison.csv',
    selected_states=[row['identity'] for row in scope['selected_states']], output_directory=f'{STAGE_NAME}/run_001',
    sampled_RSS_bytes=8589934592, phases=dict(support=dict(helper_seconds=180, outer_seconds=240,
        argv=[f'{STAGE_NAME}/execute_saved_material_support.py','--repo','.','--protocol',f'{STAGE_NAME}/protocol.json','--time-limit','180'])),
    bindings=bindings, selected_archive_plan=scope['selected_archive_plan'],
    expected_counts=dict(occurrences_per_state=2738,cells_per_state=722,nodes_per_state=703,
        group_cell_counts=dict(body=648,bottom_owner=36,left_owner=18,right_owner=18,corner_only=2),
        occurrences_total=5476,cells_total=1444,nodes_total=1406,groups_total=10,whole_total=2),
    expected_calls=dict(NPZ_read_started=3,NPZ_read_completed=3,selected_array_fields=8,support_started=2,support_completed=2,global_replay=2,PNG_writes=2),
    expected_output_files=['support.json','occurrences.csv','cells.csv','nodes.csv','groups.csv','whole_material_comparison.csv',
        'reference_support_map.png','material_support_comparison.png','execution_receipt.json'],
    projection_rules=dict(global_replay='Original C-order material bincount; exact numeric array_equal, not byte or signed-zero equality',
        regrouping='Scalar math.fsum; at most four original local terms per body node; 8eps selected-local elemental L1, no absolute floor',
        old_nodal_gate='Original M1/M2 8eps nodal L1 unchanged; not applied to element regrouping',
        trace='Saved side/whole material line values copied/compared; no new P/integral or line-versus-support equality gate'),
    qualification_scope='Two saved material assembly/support diagnostics only; no new force-kernel/HP/pressure/grip/equilibrium or full-project qualification',
    prepared_scope='Source/AST and ordinary metadata/raw SHA only; no candidate import, NPZ decode, material scatter/projection/fsum or plot')
write(STAGE/'protocol.json', protocol)

body = '''整体目标仍是读取普通 LF 几何，在独立 HF 有限变形／TMC 前向任务下给出可解释的反力、工件载荷和实际变形。HF不优化、不调用dmftd；main开发，origin保持 https://github.com/dudaxing/Compliant-TO-TMC.git。

M-PTRACE1 已唯一实际通过并闭卡，结果发布／恢复于 main 96bfea73。峰值1.20mm材料线Fy为+0.027662985836060965 N，原材料弱Fy为+0.12191255705872141 N，差−0.09424957122266045 N。该差需要追溯完整Q1节点支撑，不能按舍入噪声或Hu补平解释。

最近新候选 M-SUPPORT1 已编码，仅读同loading0.85／1.20mm的3个既存NPZ／8字段，重播2次原材料C-order组装并按body／bottom-owner／left-owner／right-owner／corner-only五类追溯局部节点贡献。每态预期722支撑单元／2738局部出现／703节点。两个仅角点相连的对角单元可能有弱式贡献，其phase未读取。N力已含厚度；支撑类别不是面压力。新局部L1舍入规则与原M1/M2节点L1门分开，旧门保持。

目前仅源码／AST、普通JSON/CSV与原字节核查：候选未导入、NPZ未解码、组装／投影／新fsum／图均未运行，尚无实际支撑贡献值或差值原因结论。拟一次helper180秒／outer240秒／采样8GiB，首错停止、无重试／修复重跑／延期／force；两PNG显示参考支撑位置与有符号材料贡献，实际变形复用原图链接。本卡待人类批准，不能续用已闭M-PTRACE1窗口。

总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛、正式标签排名与HF5仍未完成。批准后仅运行这两个保存态，根据实际支撑结果再规划最近一步。
'''
links_stage = '[具体卡](M-SUPPORT1_CARD.md) · [冻结协议](protocol.json) · [公共入口](../../../hf_repo/src/hf_eval/saved_material_support.py) · [薄执行器](execute_saved_material_support.py) · [输入核查](author/support_input_scope.json) · [物理依据](author/support_physical_basis.json) · [独立物理静审](author/support_static_physics_review.json) · [前次实际发布恢复](author/MPTRACE1_publication_receipt.json) · [前次实际结果](../nested_material_trace_001/RESULTS.md) · [既存实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)'
readme = '# M-SUPPORT1 两态保存材料支撑候选：待批准（2026-10-11）\n\n'+body+'\n'+links_stage+'''\n\n批准后从真实仓库根一次启动（使用本项目独立HF环境）：

```text
python -X utf8 -B lf_data_preparation/native_interface_001/nested_material_support_001/launch_support.py support --protocol lf_data_preparation/native_interface_001/nested_material_support_001/protocol.json
```
'''
(STAGE/'README.md').write_text(readme, encoding='utf-8')
fronts = ['docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',f'{trace}/README.md']
previous = []
for name in fronts:
    path = ROOT/name
    old = path.read_bytes()
    if name.startswith('docs/'):
        links = f'[具体卡](../{STAGE_NAME}/M-SUPPORT1_CARD.md) · [协议](../{STAGE_NAME}/protocol.json) · [候选说明](../{STAGE_NAME}/README.md) · [公共入口](../hf_repo/src/hf_eval/saved_material_support.py) · [已实际通过的材料迹](../{trace}/RESULTS.md)'
    else:
        links = '[新支撑候选](../nested_material_support_001/README.md) · [新卡](../nested_material_support_001/M-SUPPORT1_CARD.md) · [本阶段已实际通过的结果](RESULTS.md) · [既存实际变形](run_001/actual_material_trace.png)'
    prefix = ('# 当前接续：M-SUPPORT1 两态保存材料支撑候选待批准（2026-10-11）\n\n'+body+'\n'+links+'\n\n<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
    path.write_bytes(prefix+old+b'\n</details>\n')
    previous.append(dict(path=name, old_sha256=hashlib.sha256(old).hexdigest(), old_bytes=len(old),
        new_sha256=sha(path), history_start_byte=len(prefix), history_end_byte_exclusive=len(prefix)+len(old),
        old_body_preserved_exactly=True))
parsed=[]
for path in (ROOT/'hf_repo/src/hf_eval/saved_material_support.py',STAGE/'execute_saved_material_support.py',STAGE/'launch_support.py',STAGE/'author/prepare_source.py'):
    ast.parse(path.read_text(encoding='utf-8'))
    parsed.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),bytes=path.stat().st_size))
write(STAGE/'author/preparation_receipt.json',dict(status='source_prepared_not_executed',baseline_main=BASE,
    AST_parsed_without_candidate_import=parsed,front_history=previous,bindings=len(bindings),
    protocol_sha256=sha(STAGE/'protocol.json'),
    preparation_actions=dict(AST_parse_only=len(parsed),candidate_imports=0,NPZ_decodes=0,
        new_material_scatter_projection_fsum_plot_calls=0,force_kernel_tangent_HP_solver_calls=0),
    authorized=False,executed=False))
print(json.dumps(dict(status='prepared_source_metadata_only',stage=STAGE_NAME,bindings=len(bindings)),ensure_ascii=False))
