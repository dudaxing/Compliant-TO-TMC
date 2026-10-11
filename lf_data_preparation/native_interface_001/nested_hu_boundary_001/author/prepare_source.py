"""Prepare reviewed M-BOUND1 source/ordinary metadata, with no candidate import."""
from pathlib import Path
from hashlib import sha256
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '0d83b18b2bb320f137b1c4c3295805dc7c15aa65'
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
STAGE = ROOT/REL
CASE = 'lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square'
SUPPORT = 'lf_data_preparation/native_interface_001/nested_material_support_001'
LEDGER = 'lf_data_preparation/native_interface_001/nested_ledger_002'
VOLUME = 'lf_data_preparation/native_interface_001/nested_material_volume_001'
MODULE = 'hf_repo/src/hf_eval/saved_q1_hu_boundary.py'
PREVIOUS = Path('D:/hf-native-workpiece-api-author-20261009/MVOLUME1_execution_review_001/publication_receipt.json')
read = lambda p: json.loads(p.read_bytes())
sha = lambda p: sha256(p.read_bytes()).hexdigest()
git = lambda *a: subprocess.check_output(['git',*a],cwd=ROOT).decode().strip()

def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

assert git('rev-parse','HEAD') == BASE and not git('status','--porcelain')
assert git('branch','--show-current') == 'main'
assert git('remote','get-url','origin') == 'https://github.com/dudaxing/Compliant-TO-TMC.git'
assert not STAGE.exists() and not (ROOT/MODULE).exists()
previous = read(PREVIOUS)
assert previous['published_commit'] == BASE and previous['execution_closed'] and previous['source_and_restore_clean']
assert previous['status'] == 'published_and_incrementally_restored_pass'
review = read(EXT/'static_physics_review.json')
assert review['status'].startswith('pass')
for name, pin in review['frozen_external_sources'].items():
    assert sha(EXT/name) == pin
scope = read(EXT/'final_input_scope.json')
assert scope['status'].startswith('pass') and scope['contradictions'] == []
draft = read(EXT/'protocol_draft.json')
assert not draft['authorized'] and not draft['executed'] and 'bindings' not in draft
assert draft['selected_states'] == scope['selected_states']
for name, record in scope['runtime_files'].items():
    assert sha(ROOT/name) == record['sha256']
for plan in draft['selected_archive_plan']:
    assert sha(ROOT/plan['path']) == plan['declared_archive_sha256']

STAGE.mkdir()
(STAGE/'author').mkdir()
for name in ('execute_saved_hu_boundary.py','M-BOUND1_CARD.md'):
    (STAGE/name).write_bytes((EXT/name).read_bytes())
author_names = ('input_scope.json','final_input_scope.json','physical_basis.json','paper_formula_check.json',
    'static_physics_review.json','AUTHOR_SOURCE_NOTES.md','source_author_receipt.json','protocol_draft.json',
    'prepare_source.py','build_protocol_draft.py','inspect_boundary_inputs.py','finalize_input_scope.py','write_physical_basis.py','write_paper_formula_check.py')
for name in author_names:
    (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
(ROOT/MODULE).write_bytes((EXT/'saved_q1_hu_boundary.py').read_bytes())
(STAGE/'launch_boundary.py').write_bytes((ROOT/VOLUME/'launch_volume.py').read_bytes())
(STAGE/'author/M_VOLUME1_publication_receipt.json').write_bytes(PREVIOUS.read_bytes())

sources = {
    'hf_repo/src/hf_eval/__init__.py',MODULE,'hf_repo/src/hf_eval/tmc_kernel.py',
    'hf_repo/src/hf_eval/split_kernel_invariants_hu.py','hf_repo/src/hf_eval/compensated_invariants.py',
    'hf_repo/src/hf_eval/native_force.py','hf_repo/src/hf_eval/native_mean.py','hf_repo/src/hf_eval/native_response.py',
    f'{REL}/execute_saved_hu_boundary.py',f'{REL}/launch_boundary.py',f'{REL}/M-BOUND1_CARD.md',
    f'{REL}/author/M_VOLUME1_publication_receipt.json',
    f'{SUPPORT}/protocol.json',f'{SUPPORT}/RESULTS.md',f'{SUPPORT}/run_001/execution_receipt.json',
    f'{LEDGER}/protocol.json',f'{LEDGER}/RESULTS.md',f'{LEDGER}/run_001/execution_receipt.json',
    f'{VOLUME}/protocol.json',f'{VOLUME}/RESULTS.md',f'{VOLUME}/NEXT_STEP_REVIEW.md',f'{VOLUME}/run_001/execution_receipt.json',
}
sources.update(f'{REL}/author/{name}' for name in author_names)
runtime = set(scope['runtime_files'])
assert len(runtime) == 9
pins = {name:sha(ROOT/name) for name in sorted(runtime|sources)}
protocol = dict(draft,bindings=pins)
write(STAGE/'protocol.json',protocol)
body = '''整体目标仍是独立 HF 有限变形／TMC 前向评估，从普通 LF 几何得到结构实际变形与工件作用。main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git；HF与LF优化断开。

M-VOLUME1已唯一实际PASS闭卡、发布／独立恢复于main0d83b18。四个局部case的材料九点体积观察与原保存DD弱力接近，现有证据不要求重开DD核。固定工件total/material/Hu总力、保持反力、24态／48HP工件力参考、实际变形及三分量节点图均已实现并保留。

当前新增M-BOUND1公共入口，直接关联原Q1 Hu单元八值与原工件拓扑，显示四顶点符号、side成对平移相消、两corner_only与整体作用、owner与原节点分组差别。原论文式(6)和源码的exp(-5J)作用不等于替代能量的梯度；不引入该错误验收。原fixed_dofs字段是计数而非列表的包装假设已在运行前修正。

本卡拟仅读原6／0.85mm、13／1.20mm，两forces NPZ／2字段、2次新公共入口；每态722support单元／703工件节点／2738local出现。仅compact1406DOF按原C序scatter，数值精确对原节点；原nodal L1门保留，新local重组单独使用8eps·对应原local L1无地板。只复制原六力文本与七类表，跨分组差描述，不升格为压力。

当前仅源码、AST、普通元数据及原字节核查，未导入候选、解码NPZ、调用API／新fsum／绘图。新卡一次helper180秒／outer240秒／采样8GiB，首错停止、无重试／修复重跑／延期／force，待人类批准。预期1444cell／10group／2whole／1406node／24endpoint／14原category行和两PNG；新图均参考几何且独立尺度，实际变形复用原24帧GIF。

连续总Hu边界压力、可移动工件／摩擦、有效夹持、物理参数与网格稳定性及正式HF5标签排名仍未完成。按本卡实际结果再选择下一功能或稳定性验证，不预先扩展路径／HP／求解。
'''
links = '[具体卡](M-BOUND1_CARD.md) · [协议](protocol.json) · [公共入口](../../../hf_repo/src/hf_eval/saved_q1_hu_boundary.py) · [薄执行器](execute_saved_hu_boundary.py) · [最终输入核查](author/final_input_scope.json) · [物理依据](author/physical_basis.json) · [原论文核查](author/paper_formula_check.json) · [独立静审](author/static_physics_review.json) · [前次结果](../nested_material_volume_001/RESULTS.md) · [原实际GIF](../../../functional_views/native_nested_cycle_20261009/complete_001/run_001/view/fixed_square/actual_states.gif)'
(STAGE/'README.md').write_text('# M-BOUND1 保存Q1 Hu顶点作用候选：待批准（2026-10-11）\n\n'+body+'\n'+links+
    '\n\n批准后在真实仓库根用独立HF环境一次启动：\n\n```text\npython -X utf8 -B '+REL+'/launch_boundary.py hu_boundary --protocol '+REL+'/protocol.json\n```\n',encoding='utf-8')
histories = []
for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',f'{VOLUME}/README.md'):
    path = ROOT/name
    old = path.read_bytes()
    urlbase = '../'+REL+'/' if name.startswith('docs/') else '../nested_hu_boundary_001/'
    prefix = ('# 当前接续：M-BOUND1 保存Q1 Hu顶点作用候选待批准（2026-10-11）\n\n'+body+'\n'+
        '[具体卡]('+urlbase+'M-BOUND1_CARD.md) · [说明]('+urlbase+'README.md) · [冻结协议]('+urlbase+'protocol.json)\n\n'+
        '<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
    path.write_bytes(prefix+old+b'\n</details>\n')
    histories.append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),new_sha256=sha(path),
        history_start_byte=len(prefix),history_end_byte_exclusive=len(prefix)+len(old)))
parsed = []
for name in (MODULE,f'{REL}/execute_saved_hu_boundary.py',f'{REL}/launch_boundary.py',f'{REL}/author/prepare_source.py'):
    ast.parse((ROOT/name).read_text(encoding='utf-8'))
    parsed.append(dict(path=name,sha256=sha(ROOT/name)))
write(STAGE/'author/preparation_receipt.json',dict(status='source_prepared_not_executed',baseline_main=BASE,
    protocol_sha256=sha(STAGE/'protocol.json'),bindings=len(pins),front_history=histories,AST_parsed_without_candidate_import=parsed,
    preparation_actions=dict(AST_parse_only=4,candidate_imports=0,NPZ_decodes=0,new_contraction_fsum_render_calls=0,force_kernel_tangent_HP_solver_calls=0),
    authorized=False,executed=False))
print(json.dumps(dict(status='prepared_source_metadata_only',bindings=len(pins),selected_archives=2,selected_fields=2)))
