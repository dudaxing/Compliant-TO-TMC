"""Preserve reviewed saved-scalar reasoning and append the next functional step."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

REPORT = 'docs/WORKPIECE_ENLARGEMENT_20261007.md'
BASE = 'docs/evidence/workpiece_enlargement_20261007/right_margin4_source_context/effects_001'
PINS = {
    'matched_margin4_effects.json': 'ad649ec9a0ab035a33e355c779102e9d0958272737f8cbf378e9b786794258d4',
    'effects_note.md': 'bb5f59716319797773aa754e3a51f65cf80f058cb57043e8af891366f3affff0',
}
NOTE = '''

### 2→4 mm实际效果与最近的功能选择

24个同方向、同原目标全部匹配。峰值总Fy仅增加0.109268%，其中材料Fy减少0.482721%，正则化Fy增加86.8050%；两项部分抵消，正则化力占比从0.678205%增至1.265537%。早期加载0.25–0.85 mm的Fy增加11.66%–21.05%，绝对差为0.0000200–0.0004492 N；不能据峰值接近宣布全路径域收敛。峰值水平力幅值减少7.31162%，钳尖正间隙5.716673→5.730316 μm，介质max|Hu|增加0.0462%。Hu场与Hu力分量分别解释。

4 mm实际340次F/325完成、174次T全部完成、173次LU（23预测+150校正）；166个trial为150接受、1完整Armijo拒绝、10 invalid_J和5算术范围拒绝。首次范围拒绝ordinal324在卸载回零，原线搜索缩半后恢复；没有修复该算术范围问题，也没有授予拒绝态参考资格。0失败路径和0额外二分态。

最近先完成易用性小功能：将现有保存结果整理成紧凑响应，显式暴露现有初始化选项，明确输入/任务/结果与图的来源及失败状态，再组合一次前向评价入口。它不改变核心方程、物理任务或参考门。若随后需要可转移的全路径工件力，另设固定其余条件的一个额外域余量对照；同设计网格/α敏感性、压力/接触定义和圆体/自由体仍是后续依赖。上述选择是规划，尚未执行新科学卡或完成HF5。

[完整保存标量与计数](evidence/workpiece_enlargement_20261007/right_margin4_source_context/effects_001/001.json)；[原物理意见](evidence/workpiece_enlargement_20261007/right_margin4_source_context/effects_001/002.md)；[独立保存数据审阅](evidence/workpiece_enlargement_20261007/right_margin4_source_context/effects_001/003.json)。这次只记录既有JSON及标量判断，无新增求解、HP、观察或绘图。
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    source = Path(__file__).resolve().parent
    blobs = {name: (source / name).read_bytes() for name in PINS}
    assert all(sha256(data).hexdigest() == PINS[name] for name, data in blobs.items())
    effects = json.loads(blobs['matched_margin4_effects.json'])
    assert effects['matched_states'] == 24
    for name, digest in effects['input_sha256'].items():
        assert sha256((root / name).read_bytes()).hexdigest() == digest
    review_bytes = (source / 'effects_saved_review.json').read_bytes()
    review = json.loads(review_bytes)
    assert not review['blocking_findings']
    assert review['payload_sha256'] == PINS
    before = (root / REPORT).read_bytes()
    assert sha256(before).hexdigest() == '3f571e1ccb266cbcad8c451c8f4b74516cb0cf73916480b2753ca94838695bf5'
    target = root / BASE
    assert not target.exists()
    target.mkdir()
    archive = {'001.json': blobs['matched_margin4_effects.json'], '002.md': blobs['effects_note.md'],
               '003.json': review_bytes, '004.py': Path(__file__).read_bytes(), '005.md': NOTE.encode('utf-8')}
    for name, data in archive.items():
        (target / name).write_bytes(data)
    (root / REPORT).write_bytes(before + NOTE.encode('utf-8'))
    receipt = dict(status='pass_saved_reasoning_record', created_utc=datetime.now(timezone.utc).isoformat(),
                   new_scientific_calls=0, report_before_sha256=sha256(before).hexdigest(),
                   report_after_sha256=sha256((root / REPORT).read_bytes()).hexdigest(),
                   original_report_prefix_preserved=(root / REPORT).read_bytes().startswith(before),
                   archive={name: sha256(data).hexdigest() for name, data in archive.items()})
    (target / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (target / 'INDEX.md').write_text('001 saved-scalar comparison;002 original effects_note;003 saved-data peer review;004 file-only install helper;005 report append. Original names and rawSHA pins are in004 and receipt.json. No new scientific execution.\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
