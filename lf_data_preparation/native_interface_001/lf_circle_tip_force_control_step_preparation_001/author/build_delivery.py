# Ordinary preparation delivery only: no HF, scientific arrays or media decoder.
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_step_preparation_001'
BASELINE = '6c333a825e0c6b90be5b32b38bfe0a7677378384'

def read(p):
    return json.loads(p.read_bytes())
def identity(p):
    raw = p.read_bytes()
    return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
def write_new(p, raw):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(raw)
def table(rows):
    return '<table>' + ''.join('<tr>' + ''.join('<td>' + escape(str(v)) + '</td>' for v in row) + '</tr>' for row in rows) + '</table>'

def main():
    dest = ROOT/REL
    assert not dest.exists(), 'Preserve an existing delivery'
    assert (AUTHOR/'PREPARATION_REVIEW.md').is_file()
    review = read(AUTHOR/'PREPARATION_REVIEW.json')
    assert review['status'].upper().startswith('PASS'), review['status']
    qa = read(AUTHOR/'SCHEMATIC_QA.json')
    assert qa['status'] == 'PASS_revision_2_concept_schematic'
    assert qa['revisions'][-1]['revision'] == 2 and qa['revisions'][-1]['status'] == 'PASS'
    binding, contract = read(AUTHOR/'SOURCE_BINDING.json'), read(AUTHOR/'CONTRACT.json')
    assert binding['baseline'] == BASELINE and binding['status'] == 'prepared_not_executed'
    assert contract['status'] == 'candidate_not_approved_not_executed'
    actual = read(AUTHOR/'PREPARATION_ACTUAL_RECORD.json')
    assert actual['numerical_launched'] is False and actual['production_modified'] is False
    head = subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    assert head == BASELINE
    sources = binding['production_source_files']
    assert len(sources) == 58
    assert {(ROOT/r['path']).resolve() for r in sources} == {p.resolve() for p in (ROOT/'hf_repo/src/hf_eval').rglob('*.py')}
    for r in sources:
        assert identity(ROOT/r['path']) == {k:r[k] for k in ('bytes', 'sha256')}, r['path']
    render = read(AUTHOR/'SCHEMATIC_RENDER.json')
    assert render['current_revision'] == 2 and render['render_attempts'] == 2
    assert identity(AUTHOR/'control_schematic.png') == qa['revisions'][-1]['image_identity']
    for r in render['image_outputs']:
        assert identity(Path(r['path'])) == {k:r[k] for k in ('bytes', 'sha256')}
    docs = ('PREPARATION.md', 'TASK_SPEC.md', 'L-CTIPFSTEP1_CARD.md', 'RECOVERY.md', 'SOURCE_BINDING.md')
    roots = docs + ('SOURCE_BINDING.json', 'CONTRACT.json', 'HISTORY.json', 'observer_binding.json', 'PREPARATION_ACTUAL_RECORD.json', 'control_schematic.png', 'control_schematic.svg')
    authors = ('SOURCE_AUDIT.md', 'SOURCE_AUDIT.json', 'MATH_RESOURCE_AUDIT.md', 'MATH_RESOURCE_AUDIT.json', 'PREPARATION_REVIEW.md', 'PREPARATION_REVIEW.json', 'SCHEMATIC_RENDER.json', 'SCHEMATIC_RENDER_INITIAL.json', 'SCHEMATIC_QA.json', 'render_schematic.py', 'render_schematic_initial.py', 'prepare.py', 'finish_spec.py', 'build_delivery.py', 'publication.py')
    copies = [(AUTHOR/n, n) for n in roots] + [(AUTHOR/n, 'author/'+n) for n in authors]
    assert len(copies) == 27 and all(p.is_file() for p, _ in copies)
    fronts = (('README.md', REL+'/'), ('docs/CURRENT_STATUS.md', '../'+REL+'/'), ('hf_repo/README.md', '../'+REL+'/'))
    old = {n:(ROOT/n).read_bytes() for n, _ in fronts}
    assert all(b'L-CTIPFSTEPPREP1 **' not in raw[:2000] for raw in old.values())
    attributes = ROOT/'.gitattributes'
    old_attributes = attributes.read_bytes()
    svg_spaces = any(line.endswith((b' ', b'\t')) for line in (AUTHOR/'control_schematic.svg').read_bytes().splitlines())
    dest.mkdir(parents=True)
    for p, name in copies:
        write_new(dest/name, p.read_bytes())
        assert (dest/name).read_bytes() == p.read_bytes(), name
    load, inherit, state = contract['loads'], contract['numerical_inheritance'], binding['selected_force_state']
    budget = contract['resources']
    rows = [('P0 / root half N', load['root_P0_half_N']), ('P1 / segment half N', load['segment_P1_half_N']), ('P2 / candidate half N', load['P2_half_N']), ('q1 / mm', inherit['initial_absolute_q_mm']), ('R1 / N', inherit['initial_signed_R_N']), ('q2 / mm', '未知，未求解'), ('R2 / N', '未知，未求解'), ('mean / mm', inherit['held_mean_mm']), ('ΔP / half N', load['new_increment_half_N']), ('原Nmin / half N', load['minimum_force_increment_half_N']), ('实际ΔP/Nmin', load['new_increment_over_Nmin'])]
    resource_keys = ('controller_seconds', 'science_total_seconds', 'ordinary_check_total_seconds', 'display_and_root_QA_shared_seconds', 'helper_seconds', 'outer_seconds')
    nav = ' · '.join('<a href="'+n+'">'+n+'</a>' for n in docs+('HISTORY.json', 'CONTRACT.json', 'author/PREPARATION_REVIEW.md'))
    force = state['force_on_body_N']
    ratio = abs(force['regularization'][0])/abs(force['total'][0])
    page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>正式非零q小载荷续载准备</title><style>body{font:16px/1.7 system-ui;max-width:1180px;margin:30px auto;padding:0 20px;color:#203244}img{width:100%;height:auto}table{border-collapse:collapse;width:100%}td{padding:8px;border-bottom:1px solid #d1dce5;overflow-wrap:anywhere}section{margin:28px 0}a{color:#075d94}</style>'
    page += '<h1>L-CTIPFSTEPPREP1：准备完成，正式续载未执行</h1><p>2026-10-24。核定mean1.06 mm正式r9非零q父、P2、原P0尺度、原门和资源；58生产源码不改。无新q2/R2、真实变形、参考误差或资格升级。</p><nav>'+nav+'</nav>'
    page += '<section><h2>控制与状态示意</h2><img src="control_schematic.png" alt="已完成P0/P1与未来P1/P2的概念示意"><p>非实际几何/变形或新FE结果。初版minJ负号缺字未接受，改ASCII e-4后第二版通过；两次概念渲染/两次root检查均保记录。初版receipt和源码在author，初版坏图仅留本机作者历史，不作当前恢复依赖。</p></section>'
    page += '<section><h2>原值与唯一新目标</h2>'+table(rows)+'<p>完整来源[P0,P1,P2]保留，未来只算[P1,P2]；非零绝对q/P/R与split原样继承，fresh check1且身份保持。半模型P已含20mm厚度，完整镜像轴向2P、q不倍增；输入R独立于工件P。q2由求解确定，不指定答案。</p><p>root P0与segment P1分开，本正增段实际SP=P，不能独证根尺度重置行为；保留原负P小模型证据。P2无给q/HP参考，不套旧P1工程误差界或造零差。原maxdepth4/Nmin保持；有效二分最多两级、至多fresh+4叶=5态是算术界，非实际路径。</p></section>'
    page += '<section><h2>原验收门</h2>'+table(contract['production_gates'].items())+'<p>适用全部fresh/内部/末态；本准备仅普通源核定与科学stat，实际payload准入及fresh力学尚待执行。</p></section>'
    page += '<section><h2>保留的低J/Hu与历史</h2><p>直接父minJ='+repr(state['minimum_J'])+'，max|Hu|='+repr(state['max_abs_Hu_per_mm'])+' /mm，轴向Hu约'+f'{ratio*100:.6f}'+'%。力控父2态/0失败/0二分；旧给q路径首次+.025 invalid_J回滚并接受0/.0125/.025三态，历史分开保留。<a href="HISTORY.json">原值历史</a>、<a href="observer_binding.json">尖端/右介质原ID</a>。导向总弱力平衡不授压力、纯接触抗拔、极限承载、稳定性或释放资格。</p></section>'
    page += '<section><h2>候选资源与停止</h2>'+table((k, budget[k]) for k in resource_keys)+'<p>controller包含于science2100=2085进程+15清理；普通核对60=45+15；显示/QA共享600，viewer510+15、QA585秒前；helper3000=2100+60+600+240调度/清理/一次封存，outer3060最多51分钟。CPU/采样64GiB/四库cap16，viewer原8GiB。先例398.93秒不保证小步更快；原内部回溯/有界二分允许，首个终端错误停，保partial，无外部重试/延期/force/新HP/测试/生产修改。</p></section>'
    page += '<section><h2>下一步与恢复</h2><p>候选卡待新授权、薄包装冻结和静审后才试算。成功后按卡输出实际×1变形、P–q与R、total/material/Hu与账本、尖端/右介质及保存J/Hu、全部Newton/trial/二分和真实N帧动画；当前无这些新实际结果。本交付不复制科学包/58源整树/旧媒体，恢复依赖见RECOVERY；stat可用不等于payload/fresh通过。</p></section></html>'
    write_new(dest/'inspection.html', page.encode('utf-8'))
    banner = '> 2026-10-24 L-CTIPFSTEPPREP1 **准备完成，尚未正式续载**：mean1.06 mm正式r9非零q父、P2=0.000260201584412907 half N、原root P0/原门及候选51分钟窗口已核；58生产源码保持。[准备/示意]({p}PREPARATION.md) · [人工页]({p}inspection.html) · [候选卡]({p}L-CTIPFSTEP1_CARD.md)。无新q2或正式求解，执行待新授权及冻结静审。下方为历史状态。\n\n'
    for name, prefix in fronts:
        (ROOT/name).write_bytes(banner.format(p=prefix).encode('utf-8')+old[name])
    if svg_spaces:
        entry = REL+'/control_schematic.svg whitespace=blank-at-eof,space-before-tab,cr-at-eol,-blank-at-eol\n'
        if entry.encode() not in old_attributes:
            attributes.write_bytes(old_attributes+(b'' if old_attributes.endswith(b'\n') else b'\n')+b'# Preserve generated path spacing in bound FSTEP preparation SVG.\n'+entry.encode())
    print(json.dumps(dict(status='PASS_PREPARATION_DELIVERY_ONLY', files=len(copies)+1, production_unchanged=58, science=0, media_decode=0, stage_commit_push=0)))

if __name__ == '__main__':
    main()
