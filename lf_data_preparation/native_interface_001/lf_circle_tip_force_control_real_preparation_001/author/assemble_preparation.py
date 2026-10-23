"""Deliver ordinary preparation context and one existing control schematic."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

AUTHOR=Path(__file__).resolve().parent
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
REL='lf_data_preparation/native_interface_001/lf_circle_tip_force_control_real_preparation_001'
DEST=ROOT/REL
assert not DEST.exists()
review=json.loads((AUTHOR/'PREPARATION_REVIEW.json').read_bytes())
assert str(review['status']).lower().startswith('pass')
state=json.loads((AUTHOR/'PREPARATION_STATE.json').read_bytes())
state.update(status='preparation_complete_independent_review_PASS',new_r9_force_path_executed=False)
(AUTHOR/'PREPARATION_STATE.json').write_bytes((json.dumps(state,ensure_ascii=False,indent=2)+'\n').encode())
DEST.mkdir()
top={'PREPARATION.md','L-CTIPFREAL1_CARD.md','SOURCE_BINDING.md','SOURCE_BINDING.json','COMPARISON_GATES.md','COMPARISON_GATES.json','observer_binding.json','control_schematic.png','control_schematic.svg'}
for path in sorted(AUTHOR.iterdir()):
    if path.is_file() and path.name!='FINAL_PUBLICATION_ARCHIVE_RECEIPT.json':
        target=DEST/path.name if path.name in top else DEST/'author'/path.name
        target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(path.read_bytes())
base=Path('D:/hlo1_001/run_001')
for name in ('parent_fixed/result.json','parent_fixed/model/model.json','parent_fixed/accepted/002/state.json',
             'parent_fixed/model/source_geometry/geometry.json','probe_low/result.json'):
    target=DEST/'source_context'/name
    target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes((base/name).read_bytes())
for rel,prefix in [('README.md',''),('docs/CURRENT_STATUS.md','../'),('hf_repo/README.md','../')]:
    path=ROOT/rel
    banner=f'> 2026-10-23 L-CTIPFREALPREP1 **正式r9两载荷准备完成，尚未求解**：核定LOW1完整父索引2、机构保持.50 mm、绝对半模型P0/P1=3.68642113e−5／4.32723069e−5 N；q／全场差各≤1e−6 mm、R另门。原物理与验收门保持；[准备总览与示意]({prefix}{REL}/PREPARATION.md)、[下一张执行卡]({prefix}{REL}/L-CTIPFREAL1_CARD.md)。本轮只读普通描述、旧科学档仅stat，57份生产源码未改；真实力控待新授权与包装静审。下方状态保留为历史时点。\n\n'
    path.write_bytes(banner.encode()+path.read_bytes())
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>正式r9力控检查准备</title><style>body{max-width:1250px;margin:32px auto;padding:0 20px;font:16px/1.7 system-ui;color:#243440}img{width:100%}a{color:#24678c}.state{background:#edf3f7;padding:14px}</style><h1>正式r9两载荷力控交叉：准备完成</h1><p class="state">机构平均输入保持0.50 mm；只给外载P，未知q由新求解确定。正式路径尚未执行。</p><p>P0=3.686421133658022e−5 N，P1=4.3272306948756724e−5 N；半模型，含20 mm厚度。q=.025 mm只作既有位移参考。</p><img src="control_schematic.png" alt="控制示意，不是真实有限元结果"><p>保持原物理及原门；端点q／全场差各≤1e−6 mm，R使用独立N门。先冻结薄包装和来源，再按下一张卡批准范围唯一执行。</p><ul><li><a href="PREPARATION.md">准备记录、资源与恢复</a></li><li><a href="SOURCE_BINDING.md">来源与接口核查</a></li><li><a href="COMPARISON_GATES.md">数学验收与工程比较门</a></li><li><a href="L-CTIPFREAL1_CARD.md">待批准执行卡</a></li><li><a href="author/PREPARATION_REVIEW.md">独立审阅</a></li><li><a href="../lf_circle_tip_force_control_001/RESULTS.md">已完成的小模型验证</a></li></ul></html>'''
(DEST/'inspection.html').write_bytes(page.encode())
print(json.dumps(dict(status='assembled_preparation_only',directory=str(DEST),new_scientific_calls=0)))
