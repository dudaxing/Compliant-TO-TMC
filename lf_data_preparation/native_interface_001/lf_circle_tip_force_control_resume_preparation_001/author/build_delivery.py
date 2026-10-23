"""Publish only ordinary preparation documents, source records and concept art."""
from hashlib import sha256
import html
import json
from pathlib import Path
import shutil

A = Path(__file__).resolve().parent
R = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_resume_preparation_001'
D = R/REL
assert not D.exists()
binding = json.loads((A/'SOURCE_BINDING.json').read_bytes())
review = json.loads((A/'PREPARATION_REVIEW.json').read_bytes())
assert review['status'] == 'PASS_PREPARATION_CONTRACT_ONLY'
identity = json.loads((A/'PREPARATION_IDENTITY_REVIEW.json').read_bytes())
for name, row in identity['reviewed_pins'].items():
    raw = (A/name).read_bytes()
    assert len(raw) == row['bytes'] and sha256(raw).hexdigest() == row['sha256'], name
for row in binding['production_source_files']:
    assert sha256((R/row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
assert json.loads((A/'SCHEMATIC_QA.json').read_bytes())['status'] == 'PASS'
D.mkdir(parents=True)
(D/'author').mkdir()
top = ['PREPARATION.md','SOURCE_BINDING.md','SOURCE_BINDING.json','INTERFACE_SPEC.md',
       'VALIDATION_PLAN.md','CONTRACT.json','L-CTIPFRESUME1_CARD.md','RECOVERY.md',
       'continuation_schematic.png','continuation_schematic.svg']
author = ['prepare.py','finish_spec.py','build_delivery.py','publication.py',
          'MATH_AUDIT.md','MATH_AUDIT.json','VALIDATION_AUDIT.md','VALIDATION_AUDIT.json',
          'PREPARATION_REVIEW.md','PREPARATION_REVIEW.json','SCHEMATIC_QA.json',
          'PREPARATION_IDENTITY_REVIEW.json','review_identity.py']
for name in top:
    shutil.copyfile(A/name,D/name)
for name in author:
    shutil.copyfile(A/name,D/'author'/name)
links = [('PREPARATION.md','目标、进度与准备结论'),('INTERFACE_SPEC.md','最小接口和继承合同'),
         ('VALIDATION_PLAN.md','12方法／7条小模型路径计划'),('L-CTIPFRESUME1_CARD.md','候选执行卡：未批准未执行'),
         ('SOURCE_BINDING.json','已有状态原值与来源身份'),('author/PREPARATION_REVIEW.md','准备独立审阅'),('RECOVERY.md','恢复边界')]
items = ''.join(f'<li><a href="{p}">{html.escape(t)}</a></li>' for p,t in links)
page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>力控保存态续载：准备总览</title><style>body{{max-width:1160px;margin:36px auto;padding:0 24px;font:17px/1.75 system-ui,sans-serif;color:#17324d;background:#f7f9fb}}img{{width:100%;height:auto;border:1px solid #c4d2dd;border-radius:10px}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:10px;border:1px solid #c4d2dd;text-align:left}}a{{color:#006b71}}.state{{padding:14px;background:#e0f0f0;border-radius:7px}}</style>
<h1>力控保存态续载：最小规格准备</h1><p class="state">准备完成；功能尚未实现，所有新求解／F／T／HP／测试均为0，57份生产源码保持。下图是概念示意，不是新计算结果。</p>
<img src="continuation_schematic.png" alt="绝对q、P1段锚点和root P0原尺度的继承关系"><p>原位移lift已经含q；fresh原样复核，新步覆盖绝对q。P已含厚度，机构R与工件P分别报告。</p>
<table><tr><th>关系</th><th>已明确的合同</th></tr><tr><td>当前候选父</td><td>HIGH1成功末态；P1=0.0002561572865437846 N，q1=0.025000000126731543 mm，R1=0.19536542042269825 N。</td></tr>
<tr><td>预载与原门</td><td>段起点P1不替换根P0=0.0002399800950672949 N；SP=max(|P|,|root P0|,Ffloor)。</td></tr>
<tr><td>最小实现</td><td>候选2旧改＋1新，显式续载入口；原fixed父入口、力核／切线及其余55份生产源码保持。</td></tr>
<tr><td>下一验证</td><td>12方法，最多7条16单元／50场DOF真实路径；direct对两次公开续载，先小模型后正式任务。</td></tr>
<tr><td>候选窗口</td><td>tests480／显示与QA60／helper660／outer720秒，8GiB，线程cap16；仅新卡批准后启动。</td></tr></table>
<ul>{items}</ul><p>本轮未读取或散列NPZ内容、解包旧科学档或重开旧媒体；源科学依赖只stat。新函数及候选执行卡均未执行，不能把准备审阅PASS当作数值验证PASS。</p></html>'''
(D/'inspection.html').write_bytes((page+'\n').encode('utf-8'))
for name, linkroot in [('README.md',''),('docs/CURRENT_STATUS.md','../'),('hf_repo/README.md','../')]:
    target = R/name
    banner = f'> 2026-10-23 L-CTIPFRESUMEPREP1 **力控保存态续载准备完成；尚未实现或执行**：明确非零绝对q／P／R／原split继承，段P1与root P0尺度分开，最小显式接口及12方法／7条小模型路径候选；57生产源码保持。[规格与示意]({linkroot}{REL}/PREPARATION.md)、[人工页]({linkroot}{REL}/inspection.html)、[候选卡]({linkroot}{REL}/L-CTIPFRESUME1_CARD.md)。下方HIGH1数值PASS仍保原范围，本准备不授新求解或承载资格。下方为历史状态。\r\n\r\n'
    target.write_bytes(banner.encode('utf-8')+target.read_bytes())
actual = dict(stage='L-CTIPFRESUMEPREP1', status='preparation_complete_not_implemented_not_executed',
    production_source_files_unchanged=57, ordinary_bound_source_paths=4, scientific_NPZ_stat_paths=3,
    scientific_NPZ_content_reads=0, scientific_NPZ_hashes=0, ZIP_decodes=0,
    HF_imports=0, F=0, T=0, HP=0, tests=0, equilibrium_paths=0, production_changes=0,
    conceptual_PNG_generated=1, conceptual_PNG_inspections=1, rerenders_after_inspection=0,
    preparation_review_checks=12, preparation_review_status='PASS_PREPARATION_CONTRACT_ONLY',
    current_card_execution_authorized=False,
    ordinary_packaging_note='First builder stopped before creating destination because it expected PASS rather than the actual PASS_PREPARATION_CONTRACT_ONLY review status. Builder expectation corrected; preparation copy then completed. This was ordinary document packaging, not a scientific card execution or rerun.',
    publication_restore='Pending; actual receipts added after publication, not prewritten')
raw = (json.dumps(actual,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
(A/'PREPARATION_ACTUAL_RECORD.json').write_bytes(raw)
(D/'author/PREPARATION_ACTUAL_RECORD.json').write_bytes(raw)
print(json.dumps(dict(status='assembled_preparation',source_files_copied=len(top)+len(author),new_science=0)))
