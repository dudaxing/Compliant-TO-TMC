"""Close M-VOLUME1 actual records; no numerical or plot execution."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/nested_material_volume_001'
STAGE = ROOT/REL
BASE = '7ea78ce19ba066dfce8a03892395d5604707dda6'
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
assert not (STAGE/'RESULTS.md').exists()
protocol, helper, outer = (read(p) for p in (STAGE/'protocol.json',STAGE/'run_001/execution_receipt.json',STAGE/'volume_launch.json'))
assert helper['status'] == outer['status'] == 'pass' and outer['invocations'] == 1 and outer['stop_reason'] is None
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
peers = {}
for name in ('terminal_execution_review.json','physical_results_review.json','visual_review.json'):
    document = read(EXT/name)
    if name == 'physical_results_review.json':
        assert document['status'] == 'completed_actual_saved_result_interpretation_no_new_scientific_gate'
    else:
        assert document['status'].startswith('pass')
    assert not (STAGE/'author'/name).exists()
    (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
    peers[name] = sha(EXT/name)
assert all(sha(STAGE/'run_001'/name) == pin for name,pin in helper['output_SHA256'].items())
text = (EXT/'RESULTS_draft.md').read_text(encoding='utf-8')
text = text.replace('本草稿依据实际保存 JSON／CSV 与收据整理；独立终态／物理解读将在闭卡文档中关联。',
    '本报告依据实际保存 JSON／CSV 与收据整理；[独立终态核对](author/terminal_execution_review.json)通过，[独立物理解读](author/physical_results_review.json)已完成，后者是解释而非新增科学门。')
text = text.replace('本草稿整理仅读取', '闭卡文档整理仅读取')
text = text.replace('实际计算均属于这次已批准的唯一运行；独立物理解读和主任务像素审阅需由各自记录证明。',
    '实际计算均属于这次已批准的唯一运行；独立终态、物理解读与主任务像素审阅均已由上述各自记录关联。闭卡与发布工具仅处理普通文件及 Git，不续用数值窗口。')
(STAGE/'RESULTS.md').write_bytes(text.encode('utf-8'))
body = '''整体目标仍是读取普通 LF 几何的独立 HF 有限变形／TMC 前向评估，提供可解释的反力、工件载荷和实际变形；HF不优化、不调用dmftd，main开发，origin保持https://github.com/dudaxing/Compliant-TO-TMC.git。

M-VOLUME1已在直接人类批准后唯一实际PASS并闭卡：原loading6／0.85mm、13／1.20mm的10406／10407两个单元，3个既存NPZ／9字段、2次公共入口，36九点采样／12深度／4单元对照行及两PNG。31冻结绑定保持，outer2.5381053000019165秒／tree RSS132591616 B；helper2.2876966999901924秒／own RSS128356352 B是成功收据构造前快照。exit0、stopnull、一次启动，无重试／修复重跑／延期／force；本卡窗口结束。独立终态核对通过，主任务实际查看两张原2100×2400像素，物理解读已归档。

四case的Fy保存W−九点观察V全为保存0；Fx只在6/10406和13/10407出现−1.6940658945086007e−21／+2.710505431213761e−20 N。峰值10406与10407的W=V Fy分别+.037219775006120934／+.08022435531475952 N，旧上缘T分别+.004917548552353244／+.01938390857410906 N。W−T差分别+.03230222645376769／+.060840446740650464 N，V并未消去体积／上缘差；现有局部证据不支持立即重开DD核追究舍入分离。

0.85mm中层Q较大，1.20mm下层Q较大。三个Q是同批九项的可加体积贡献；Qtop不是整上缘T。唯一新增8eps×同九项L1重组门四case均通过，无地板；跨表达差只描述，原保存DD力、旧迹和原门保持。两图各panel独立尺度，只能按标签／CSV跨panel比较绝对量；图为参考采样及材料贡献，实际结构变形仍见原图／24帧GIF。protocol及card的False是准备历史，实际授权和终态另有独立记录。

下一功能选择先核当前公共API已有total/material/Hu工件载荷、半模及镜像报告合同，避免重做已有功能；再根据本次局部体积／上缘证据推进尚缺的总作用量物理解释和可用输出。这里仅记粗路线，不拟定或授权新数值卡。不扩展同类全24态账本，不把P@N加一个Hu数认定为总压力。总Hu边界作用／压力、有效夹持、自由体／摩擦、网格收敛、正式标签排名与HF5仍未完成；本卡不增加力核／切线／HP／平衡路径或压力／夹持资格。
'''
fronts = ['docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',f'{REL}/README.md',
    'lf_data_preparation/native_interface_001/nested_material_support_001/README.md']
history = []
for name in fronts:
    path = ROOT/name
    old = path.read_bytes()
    if name.startswith('docs/'):
        links = f'[完整结果](../{REL}/RESULTS.md) · [九点P图](../{REL}/run_001/nine_point_material_P.png) · [分层贡献图](../{REL}/run_001/material_depth_volume_comparison.png) · [精确对照表](../{REL}/run_001/cell_comparisons.csv) · [实际授权](../{REL}/author/authorization.json) · [终态核对](../{REL}/author/terminal_execution_review.json) · [物理解读](../{REL}/author/physical_results_review.json)'
    elif name == f'{REL}/README.md':
        links = '[完整结果](RESULTS.md) · [九点P图](run_001/nine_point_material_P.png) · [分层贡献图](run_001/material_depth_volume_comparison.png) · [精确对照表](run_001/cell_comparisons.csv) · [实际授权](author/authorization.json) · [终态核对](author/terminal_execution_review.json) · [物理解读](author/physical_results_review.json) · [原实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)'
    else:
        links = '[新九点实际结果](../nested_material_volume_001/RESULTS.md) · [九点P图](../nested_material_volume_001/run_001/nine_point_material_P.png) · [分层贡献图](../nested_material_volume_001/run_001/material_depth_volume_comparison.png) · [本阶段原实际结果](RESULTS.md) · [原实际变形](../nested_material_trace_001/run_001/actual_material_trace.png)'
    prefix = ('# 当前接续：M-VOLUME1九点材料体积诊断已通过（2026-10-11）\n\n'+body+'\n'+links+'\n\n<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
    path.write_bytes(prefix+old+b'\n</details>\n')
    history.append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),
        new_sha256=sha(path),history_start_byte=len(prefix),history_end_byte_exclusive=len(prefix)+len(old),old_body_preserved_exactly=True))
scripts = ('record_authorization.py','record_visual_review.py','close_docs.py',
    'review_terminal.py','write_physical_results_review.py')
for name in scripts:
    assert not (STAGE/'author'/name).exists()
    (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
receipt = dict(status='pass_actual_execution_documentation_closed',source_commit=BASE,front_history=history,
    peer_reports=peers,result_sha256=sha(STAGE/'RESULTS.md'),protocol_sha256=sha(STAGE/'protocol.json'),
    bindings_checked=len(protocol['bindings']),authorization_sha256=sha(STAGE/'author/authorization.json'),execution_closed=True,
    actions=dict(results_written=1,fronts_updated=4,peer_records_archived=3,raw_author_scripts_archived=len(scripts),
        new_candidate_runs=0,new_NPZ_decodes=0,new_projection_fsum_integral_render=0),
    source_card_protocol_original_bytes_unchanged=True,entire_HF5_complete=False)
with (STAGE/'author/documentation_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=receipt['status'],fronts=len(history),bindings_checked=len(protocol['bindings'])),ensure_ascii=False))
