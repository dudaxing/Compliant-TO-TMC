"""Prepare M-VOLUME1 source and metadata; never import or execute its API."""
from pathlib import Path
from hashlib import sha256
import ast
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '1671e2d01db3f96718d76ca985199bf3fc65873f'
REL = 'lf_data_preparation/native_interface_001/nested_material_volume_001'
STAGE = ROOT/REL
CASE = 'lf_data_preparation/native_interface_001/nested_cycle_001/run_001/fixed_square'
TRACE = 'lf_data_preparation/native_interface_001/nested_material_trace_001'
SUPPORT = 'lf_data_preparation/native_interface_001/nested_material_support_001'
MODULE = 'hf_repo/src/hf_eval/saved_material_volume.py'
PREVIOUS = Path('D:/hf-native-workpiece-api-author-20261009/MSUPPORT1_execution_review_001/publication_receipt.json')
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
assert read(EXT/'static_physics_review.json')['status'].startswith('pass')
(EXT/'M_SUPPORT1_publication_receipt.json').write_bytes(PREVIOUS.read_bytes())
STAGE.mkdir()
(STAGE/'author').mkdir()
for name in ('execute_saved_material_volume.py','M-VOLUME1_CARD.md'):
    (STAGE/name).write_bytes((EXT/name).read_bytes())
for name in ('input_scope.json','physical_basis.json','static_physics_review.json','prepare_source.py'):
    (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
(ROOT/MODULE).write_bytes((EXT/'saved_material_volume.py').read_bytes())
(STAGE/'launch_volume.py').write_bytes((ROOT/SUPPORT/'launch_support.py').read_bytes())
(STAGE/'author/M_SUPPORT1_publication_receipt.json').write_bytes(PREVIOUS.read_bytes())
metadata = read(ROOT/CASE/'model/model.json')
result = read(ROOT/CASE/'result.json')
states = {i:read(ROOT/CASE/f'accepted/{i:03d}/state.json') for i in (6,13)}
selected = [dict(index=i,original_target_index=states[i]['original_target_index'],leg=states[i]['leg'],
                 d_mm=states[i]['d'],state_sha256=states[i]['state_sha256']) for i in (6,13)]
plans = []
model_names = ('coordinates','connectivity','points','grad','weights')
model_path = f'{CASE}/model/'+metadata['arrays']['path']
plans.append(dict(path=model_path,path_base=f'{CASE}/model',declared_archive_sha256=metadata['arrays']['sha256'],
    selected_fields={n:metadata['arrays']['fields'][n] for n in model_names},array_fields_decoded=False))
for i,state in states.items():
    plans.append(dict(path=f'{CASE}/'+state['forces']['path'],path_base=CASE,declared_archive_sha256=state['forces']['sha256'],
        selected_fields={n:state['forces']['fields'][n] for n in ('stress_first_piola','element_material_force')},array_fields_decoded=False))
scope = read(EXT/'input_scope.json')
assert scope['selected_states'] == selected and scope['selected_bottom_owner_cells'] == [10406,10407]
assert [(a['path'],a['declared_archive_sha256'],a['selected_fields']) for a in plans] == [
    (a['path'],a['declared_archive_sha256'],a['selected_fields']) for a in scope['recommended_minimum_selected_archive_plan']]
runtime = {f'{CASE}/model/model.json',f'{CASE}/result.json',f'{TRACE}/run_001/material_trace.json',f'{SUPPORT}/run_001/cells.csv'}
runtime.update(f'{CASE}/accepted/{i:03d}/state.json' for i in states)
runtime.update(plan['path'] for plan in plans)
sources = {
    'hf_repo/src/hf_eval/__init__.py',MODULE,'hf_repo/src/hf_eval/tmc_kernel.py',
    'hf_repo/src/hf_eval/split_kernel_invariants_hu.py','hf_repo/src/hf_eval/compensated_invariants.py',
    'hf_repo/src/hf_eval/native_mean.py','hf_repo/src/hf_eval/saved_material_trace.py',
    'hf_repo/src/hf_eval/saved_material_support.py',f'{REL}/execute_saved_material_volume.py',f'{REL}/launch_volume.py',
    f'{REL}/M-VOLUME1_CARD.md',f'{REL}/author/input_scope.json',f'{REL}/author/physical_basis.json',
    f'{REL}/author/static_physics_review.json',f'{REL}/author/M_SUPPORT1_publication_receipt.json',
    f'{SUPPORT}/protocol.json',f'{SUPPORT}/RESULTS.md',f'{SUPPORT}/run_001/execution_receipt.json',
    f'{SUPPORT}/support_launch.json',f'{TRACE}/protocol.json',f'{TRACE}/RESULTS.md',f'{TRACE}/run_001/execution_receipt.json',
}
pins = {name:sha(ROOT/name) for name in sorted(runtime|sources)}
for plan in plans:
    assert sha(ROOT/plan['path']) == plan['declared_archive_sha256']
protocol = dict(schema_version='saved-bottom-material-volume-card-1.0',prepared=True,authorized=False,executed=False,
    baseline_main=BASE,card=f'{REL}/M-VOLUME1_CARD.md',model_file=f'{CASE}/model/model.json',result_file=f'{CASE}/result.json',
    state_files={str(i):f'{CASE}/accepted/{i:03d}/state.json' for i in states},material_trace_file=f'{TRACE}/run_001/material_trace.json',
    material_support_cells_file=f'{SUPPORT}/run_001/cells.csv',selected_states=selected,selected_cell_ids=[10406,10407],
    output_directory=f'{REL}/run_001',sampled_RSS_bytes=8589934592,
    phases=dict(volume=dict(helper_seconds=180,outer_seconds=240,argv=[f'{REL}/execute_saved_material_volume.py',
        '--repo','.','--protocol',f'{REL}/protocol.json','--time-limit','180'])),
    bindings=pins,selected_archive_plan=plans,
    expected_counts=dict(samples_total=36,depth_rows_total=12,cells_total=4),
    expected_calls=dict(NPZ_read_started=3,NPZ_read_completed=3,selected_array_fields=9,volume_started=2,volume_completed=2,PNG_writes=2),
    expected_output_files=['material_volume.json','samples.csv','depths.csv','cell_comparisons.csv','nine_point_material_P.png','material_depth_volume_comparison.png','execution_receipt.json'],
    observation_rules=dict(row_regrouping='8eps times same nine computed q-term L1, no floor; observation grouping only',
        original_force='Exact identity/connectivity and original selected-local fsum versus saved support CSV; original force remains authoritative',
        rounded_P='Direct saved P/grad/weight contraction; not original DD contraction replay',
        comparisons='Geometric C rows, V_geometry and D_geometry compared descriptively; no equality gate with original DD force or old trace line',
        old_gates='Original M1/M2/SUPPORT/TRACE/HP rules unchanged'),
    qualification_scope='Four saved cell-state material-volume observations only; no force kernel, tangent, HP, equilibrium, Hu total pressure or effective-grip qualification',
    prepared_scope='Source/AST/ordinary JSON CSV and raw bytes only; no API import, NPZ decode, new contraction/fsum or render')
write(STAGE/'protocol.json',protocol)
body = '''整体目标仍是独立 HF 有限变形／TMC 前向评估，读取普通 LF 几何，为外部研究提供反力、工件载荷和实际变形。HF不优化、不调用dmftd；main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

M-SUPPORT1已唯一实际PASS闭卡并发布／恢复于main1671e2d。峰值bottom-owner弱Fy与旧bottom线差+0.09415598535141824 N，大差主要来自同一owner的体积与面迹表达；corner_only不能解释该量级。最近新候选M-VOLUME1聚焦原6/0.85mm和13/1.20mm的10406／10407两个单元。

新入口读取3个既存NPZ／9字段，对九点保存P／原grad和含厚度weights做材料体积重构，并按η三层显示；保留原DD收缩后的保存元素力及旧上缘迹。保存P已舍入，重构不是原DD重播；两者差单独报告，不设相等门。只对同一批九点观察项的行重组使用8eps·L1无地板新代数门，原门保持。

当前仅编码、AST、普通元数据和字节静审；尚未导入候选、解码NPZ、积分／fsum或绘图。新卡拟一次helper180秒／outer240秒／采样8GiB、首错停止、无重试／修复重跑／延期／force，待人类批准。预期36九点行／12深度行／4单元对照行及两PNG；新图显示参考单元采样和有符号材料贡献，实际变形复用原图。未证明差值连续物理原因。

总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛及正式HF5标签排名仍未完成。最近只执行该小范围观察，按实际结果再决定原收缩核查或Hu边界功能，不预先扩展全24态或新平衡路径。
'''
links = '[具体卡](M-VOLUME1_CARD.md) · [协议](protocol.json) · [公共入口](../../../hf_repo/src/hf_eval/saved_material_volume.py) · [薄执行器](execute_saved_material_volume.py) · [输入核查](author/input_scope.json) · [物理依据](author/physical_basis.json) · [独立静审](author/static_physics_review.json) · [前次结果](../nested_material_support_001/RESULTS.md) · [既存实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)'
(STAGE/'README.md').write_text('# M-VOLUME1 四个保存单元状态材料体积分候选：待批准（2026-10-11）\n\n'+body+'\n'+links+
    '\n\n批准后在真实仓库根使用独立HF环境一次启动：\n\n```text\npython -X utf8 -B '+REL+'/launch_volume.py volume --protocol '+REL+'/protocol.json\n```\n',encoding='utf-8')
histories = []
for name in ('docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',f'{SUPPORT}/README.md'):
    path = ROOT/name
    old = path.read_bytes()
    urlbase = '../'+REL+'/' if name.startswith('docs/') else '../nested_material_volume_001/'
    prefix = ('# 当前接续：M-VOLUME1 九点材料体积候选待批准（2026-10-11）\n\n'+body+'\n'+
        '[具体卡]('+urlbase+'M-VOLUME1_CARD.md) · [说明]('+urlbase+'README.md) · [冻结协议]('+urlbase+'protocol.json)\n\n'+
        '<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
    path.write_bytes(prefix+old+b'\n</details>\n')
    histories.append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),new_sha256=sha(path),
        history_start_byte=len(prefix),history_end_byte_exclusive=len(prefix)+len(old)))
parsed = []
for name in (MODULE,f'{REL}/execute_saved_material_volume.py',f'{REL}/launch_volume.py',f'{REL}/author/prepare_source.py'):
    ast.parse((ROOT/name).read_text(encoding='utf-8'))
    parsed.append(dict(path=name,sha256=sha(ROOT/name)))
write(STAGE/'author/preparation_receipt.json',dict(status='source_prepared_not_executed',baseline_main=BASE,
    protocol_sha256=sha(STAGE/'protocol.json'),bindings=len(pins),front_history=histories,AST_parsed_without_candidate_import=parsed,
    preparation_actions=dict(AST_parse_only=4,candidate_imports=0,NPZ_decodes=0,new_contraction_fsum_render_calls=0,force_kernel_tangent_HP_solver_calls=0),
    authorized=False,executed=False))
print(json.dumps(dict(status='prepared_source_metadata_only',bindings=len(pins),selected_archives=len(plans),selected_fields=9)))
