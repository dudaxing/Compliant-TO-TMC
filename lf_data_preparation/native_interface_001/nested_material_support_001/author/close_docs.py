"""Close actual M-SUPPORT1 documentation, preserving old evidence/source bytes."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
WORK = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/nested_material_support_001'
STAGE = ROOT/REL
BASE = 'fa872739247a2a5d96043b1c05d28e9f08a77b88'
sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
assert not (STAGE/'RESULTS.md').exists()
protocol, helper, outer = (read(p) for p in (STAGE/'protocol.json',STAGE/'run_001/execution_receipt.json',STAGE/'support_launch.json'))
assert helper['status'] == outer['status'] == 'pass' and outer['invocations'] == 1 and outer['stop_reason'] is None
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
peers={}
for name in ('terminal_execution_review.json','physical_results_review.json','visual_review.json'):
    document = read(WORK/name)
    if name != 'physical_results_review.json':
        assert document['status'].startswith('pass')
    assert not (STAGE/'author'/name).exists()
    (STAGE/'author'/name).write_bytes((WORK/name).read_bytes())
    peers[name] = sha(WORK/name)
assert all(sha(STAGE/'run_001'/name) == pin for name,pin in helper['output_SHA256'].items())
(STAGE/'RESULTS.md').write_bytes((WORK/'RESULTS_draft.md').read_bytes())
body = '''整体目标仍是读取普通 LF 几何的独立 HF 有限变形／TMC 前向评估，输出可解释的反力、工件载荷与实际变形；HF不优化、不调用dmftd，继续main，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

人类明确批准后，M-SUPPORT1唯一实际运行PASS并闭卡：3个既存NPZ／8字段，2个入口／2次原C-order材料global组装精确数值重播，5476局部出现／1444单元／1406节点／10组／2整体行及两PNG。36原绑定保持，outer2.116422799997963秒／tree RSS129019904 B；helper1.9246779000095557秒／own RSS113950720 B为成功收据构造前快照。exit0、stopnull，无重试／修复重跑／延期／force。独立终态审阅通过，两图实际像素已看；物理报告是解释，不是新增科学验收门。

原6/loading0.85mm与13/loading1.20mm的底边owner材料弱Fy为+0.0033910508870495064／+0.12182859983276352 N，对应旧底边材料line为+0.0029375878559500844／+0.02767261448134528 N；support−side-line为+0.00045346303109942195／+0.09415598535141824 N。峰值corner_only合Fy仅+0.00009348741040979886 N，body组保存贡献为0；大差主要定位于同一底边owner的体积弱式与面迹表达，不能归因两个对角支撑单元或用Hu补平材料差。右角节点10638材料Fy+.06463699536344664 N主要来自底边owner10407的局部TR项，不能当右面压力。

原global精确重播与节点身份／材料向量对账通过；整体新局部重组在0.85mm的Fy误差4.336808689942018e−19 N，小于6.236745013039355e−18 N局部L1界，峰值误差为0。原M1/M2节点L1门保留。protocol的False字段是冻结准备历史；当前批准、一次实际终态和结果另有记录。新图是参考支撑位置／有符号材料贡献，原实际变形与24帧GIF继续用于对照。共同尺度会隐藏很小的条／色差，应看CSV精确值。

最近下一步聚焦峰值底边末端10406／10407等单元的九点保存材料P／原体积弱收缩与上缘迹局部对照，解释已定位差值的离散来源；这只是依据实际结果的粗路线，未新增卡或授权新读取／计算。总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛、正式标签排名与HF5仍未完成。本卡不产生新力核／切线／HP／平衡路径资格。
'''
fronts = ['docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',f'{REL}/README.md',
    'lf_data_preparation/native_interface_001/nested_material_trace_001/README.md']
history=[]
for name in fronts:
    path=ROOT/name
    old=path.read_bytes()
    if name.startswith('docs/'):
        links=f'[本次完整结果](../{REL}/RESULTS.md) · [支撑位置图](../{REL}/run_001/reference_support_map.png) · [有符号贡献图](../{REL}/run_001/material_support_comparison.png) · [精确分组表](../{REL}/run_001/groups.csv) · [当前批准](../{REL}/author/authorization.json) · [终态审阅](../{REL}/author/terminal_execution_review.json) · [物理解读](../{REL}/author/physical_results_review.json)'
    elif name == f'{REL}/README.md':
        links='[本次完整结果](RESULTS.md) · [支撑位置图](run_001/reference_support_map.png) · [有符号贡献图](run_001/material_support_comparison.png) · [精确分组表](run_001/groups.csv) · [当前批准](author/authorization.json) · [终态审阅](author/terminal_execution_review.json) · [物理解读](author/physical_results_review.json) · [原实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)'
    else:
        links='[新支撑诊断实际结果](../nested_material_support_001/RESULTS.md) · [新支撑位置图](../nested_material_support_001/run_001/reference_support_map.png) · [新有符号贡献图](../nested_material_support_001/run_001/material_support_comparison.png) · [本阶段已实际通过的材料迹结果](RESULTS.md) · [原实际变形](run_001/actual_material_trace.png)'
    prefix=('# 当前接续：M-SUPPORT1两态材料支撑诊断已通过（2026-10-11）\n\n'+body+'\n'+links+'\n\n<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
    path.write_bytes(prefix+old+b'\n</details>\n')
    history.append(dict(path=name,old_bytes=len(old),old_sha256=hashlib.sha256(old).hexdigest(),
        new_sha256=sha(path),history_start_byte=len(prefix),history_end_byte_exclusive=len(prefix)+len(old),
        old_body_preserved_exactly=True))
for name in ('record_authorization.py','close_docs.py'):
    assert not (STAGE/'author'/name).exists()
    (STAGE/'author'/name).write_bytes((WORK/name).read_bytes())
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
receipt=dict(status='pass_actual_execution_documentation_closed',source_commit=BASE,front_history=history,peer_reports=peers,
    result_sha256=sha(STAGE/'RESULTS.md'),protocol_sha256=sha(STAGE/'protocol.json'),bindings_checked=len(protocol['bindings']),
    authorization_sha256=sha(STAGE/'author/authorization.json'),execution_closed=True,
    actions=dict(results_written=1,fronts_updated=4,peer_records_archived=3,raw_author_scripts_archived=2,
        new_candidate_runs=0,new_NPZ_decodes=0,new_projection_fsum_integral_render=0),
    source_card_protocol_original_bytes_unchanged=True,new_candidate_run_NPZ_decode_projection_render_in_documentation=0,
    entire_HF5_complete=False)
with (STAGE/'author/documentation_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=receipt['status'],fronts=len(history),bindings_checked=len(protocol['bindings'])),ensure_ascii=False))
