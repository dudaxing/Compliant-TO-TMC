"""Deliver approved preparation and original ordinary metadata, never scientific data."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

A=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/lf_circle_tip_force_control_high_preparation_001'
DEST=ROOT/REL
assert not DEST.exists()
review=json.loads((A/'PREPARATION_REVIEW.json').read_bytes())
assert str(review['status']).upper().startswith('PASS')
state=json.loads((A/'PREPARATION_STATE.json').read_bytes())
state.update(status='preparation_complete_independent_review_PASS',high_force_executed=False)
(A/'PREPARATION_STATE.json').write_bytes((json.dumps(state,ensure_ascii=False,indent=2)+'\n').encode())
DEST.mkdir(parents=True)
top={'PREPARATION.md','L-CTIPFHIGH1_CARD.md','RECOVERY.md','SOURCE_BINDING.md','SOURCE_BINDING.json',
     'COMPARISON_GATES.md','COMPARISON_GATES.json','FUNCTION_PLAN.md','observer_binding.json',
     'control_schematic.png','control_schematic.svg'}
exclude={'FINAL_PUBLICATION_ARCHIVE_RECEIPT.json','SOURCE_PARENT_AUDIT.md','SOURCE_PARENT_AUDIT.json',
         'GATES_RESOURCES_AUDIT.md','GATES_RESOURCES_AUDIT.json'}
for path in sorted(A.iterdir()):
    if path.is_file() and path.name not in exclude:
        target=DEST/path.name if path.name in top else DEST/'author'/path.name
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target)
binding=json.loads((A/'SOURCE_BINDING.json').read_bytes())
for item in binding['ordinary_files']:
    source=Path(item['path'])
    if item['role']=='reference_probe_result':
        existing=ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_probe_001/run_001/science/result.json'
        raw=existing.read_bytes()
        assert len(raw)==item['bytes'] and sha256(raw).hexdigest()==item['sha256']
        continue
    assert source.suffix=='.json'
    raw=source.read_bytes()
    assert len(raw)==item['bytes'] and sha256(raw).hexdigest()==item['sha256']
    target=DEST/'source_context'/source.relative_to('D:/hpr1_001')
    target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
excerpt=dict(stage='L-CTIPFHIGHPREP1',source_result_identity=binding['reference_probe']['result_file_sha256'],
    scope='Ordinary reference excerpt only, not a new result or cached field validation',
    reference_history=binding['reference_probe'])
(DEST/'source_context/reference_history_excerpt.json').write_bytes((json.dumps(excerpt,ensure_ascii=False,indent=2)+'\n').encode())
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>高输入1.06 mm力控交叉准备</title>
<style>body{max-width:1320px;margin:32px auto;padding:0 24px;font:16px/1.7 system-ui;color:#243440;background:#f7f9fb}section,header{background:white;border:1px solid #d6dfe6;padding:24px;margin-bottom:20px}img{max-width:100%;height:auto}a{color:#24678c}table{border-collapse:collapse;width:100%}th,td{padding:8px;border-bottom:1px solid #ddd;text-align:left}.note{color:#536779}</style>
<header><p>2026-10-23 · L-CTIPFHIGHPREP1 · 准备完成／尚无新高输入force求解</p><h1>保持机构平均输入1.06 mm，只给两个绝对外载P</h1><p>从原完整固定父accepted12/original12的q0迁移split与signed R，P0必须fresh首检原样通过；P1独立求未知q，与原给q=.025参考交叉。其余物理／原门／57生产源码保持。</p>
<table><tr><th>原请求</th><th>绝对半模型P / N，含t20</th><th>参考q / mm，仅事后对照</th></tr><tr><td>P0非零预载</td><td>0.0002399800950672949</td><td>0</td></tr><tr><td>P1</td><td>0.0002561572865437846</td><td>0.025</td></tr></table>
<p class="note">旧探针第一次直接+.025曾invalid_J，内部二分接受+.0125/+.025；末态minJ约4.166e−4、轴向Hu约72.58%。保留三接受态与失败历史，新N二分态不假配旧中间q态。此为导向总弱力任务，不授压力、纯接触容量或稳定性。</p></header>
<section><h2>控制／来源示意，非有限元结果</h2><img src="control_schematic.png" alt="高输入两载荷控制示意，不是新计算变形"><p>一张新示意图已一次检查；没有重开旧动画或绘制新计算变形。未来成功后才按卡生成五图及全部实际N帧GIF。</p></section>
<section><h2>核定门与资源</h2><p>端点q／全29970DOF位移差各≤1e−6 mm，R差≤1.9536542042187397e−8 N；fresh逐位身份与工程端点分开。原ρF/ρP/mean/J/global/rigid门保持。</p><p>controller3600包含在science3900，比较60，显示/rootQA共享600，其余240，共helper4800／outer4860秒；64GiB、线程cap16，viewer8GiB。预算不是成功保证，当前未运行。</p>
<p><a href="PREPARATION.md">目标、来源、困难、门与准备结果</a> · <a href="SOURCE_BINDING.md">来源静审</a> · <a href="COMPARISON_GATES.md">精确门／资源</a> · <a href="FUNCTION_PLAN.md">接口与包装取舍</a> · <a href="L-CTIPFHIGH1_CARD.md">候选执行卡</a> · <a href="RECOVERY.md">恢复边界</a> · <a href="author/PREPARATION_REVIEW.md">独立审阅</a></p>
<p><a href="../lf_circle_tip_force_control_real_001/RESULTS.md">已通过的低输入力控</a> · <a href="../lf_circle_tip_probe_001/RESULTS.md">原高输入位移探针</a> · <a href="source_context/reference_history_excerpt.json">原三态／失败摘录</a></p></section></html>'''
(DEST/'inspection.html').write_bytes(page.encode())
for relative,prefix in [('README.md',''),('docs/CURRENT_STATUS.md','../'),('hf_repo/README.md','../')]:
    target=ROOT/relative
    banner=f'> 2026-10-23 L-CTIPFHIGHPREP1 **高输入1.06 mm两载荷力控交叉准备完成，尚未求解**：核定原固定父accepted12/original12、half P0/P1=2.39980095e−4／2.56157287e−4 N；原三态／invalid_J／内部二分及minJ约4.166e−4保留。q／全场差各≤1e−6 mm、R界1.9536542e−8 N；controller3600／helper4800／outer4860秒候选窗口。[准备与示意]({prefix}{REL}/PREPARATION.md)、[候选执行卡]({prefix}{REL}/L-CTIPFHIGH1_CARD.md)。本轮只核普通源／旧科学档stat与新控制示意，57生产源码不改；高输入force待新授权、包装冻结与静审。下方为历史时点。\n\n'
    target.write_bytes(banner.encode()+target.read_bytes())
attributes=ROOT/'.gitattributes'
entry=f'# Preserve generated Matplotlib path spacing in the high-input preparation SVG.\n{REL}/control_schematic.svg whitespace=blank-at-eof,space-before-tab,cr-at-eol,-blank-at-eol\n'
attributes.write_bytes(attributes.read_bytes()+entry.encode())
print(json.dumps(dict(status='assembled_preparation_only',directory=str(DEST),new_scientific_calls=0)))
