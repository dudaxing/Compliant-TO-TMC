from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(r'D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_005'
AUTHOR = Path(r'D:/hf-native-workpiece-cycle005-author-20261004')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not (STAGE/'preproduction_closure.json').exists()
protocol = json.loads((STAGE/'protocol.json').read_text())
assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
absent = ['production_launch.json','execution_receipt.json','result','reference_launch.json','reference']
assert all(not (STAGE/name).exists() for name in absent)
for src, dest in [('cycle005_preproduction_fixture_review.json','preproduction_fixture_review.json'),
                  ('cycle005_preproduction_static_review.json','preproduction_static_review.json')]:
    assert not (STAGE/dest).exists()
    shutil.copyfile(AUTHOR/src, STAGE/dest)
prepare = json.loads((STAGE/'prepare_launch.json').read_text())
assert prepare['status'] == 'pass' and prepare['exit_code'] == 0
record = dict(status='closed_before_production', reason='Frozen audit stage predicate requires004 but actual new card is005; caught by independent static checks before production',
    actual_stage='coarse_square_cycle_005', frozen_auditor_stage_predicate='coarse_square_cycle_004',
    frozen_auditor_sha256=sha(STAGE/'audit_cycle005.py'), protocol_sha256=sha(STAGE/'protocol.json'),
    all179_bindings_unchanged=True, prepare=prepare,
    production_and_reference_artifacts_absent=absent,
    new_calls=dict(force=0,tangent=0,solver=0,HP=0,geometry=0,tests=0),
    scope='Preparation and static identity only; no new physical state, partial equilibrium, reference qualification or formal production/reference failure.',
    next_action='Separate006 card with correct strict identity and same1mm task/numerical gates/resources;005 frozen source and protocol unchanged.')
(STAGE/'preproduction_closure.json').write_bytes((json.dumps(record, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
text = '''# 005执行前关闭：审计阶段身份遗漏，0新力学

整体目标是独立HF真实非线性加载、工件力与卸载。本卡拟在已完成0040→.5→0mm基础上探索0→.5→1→.5→0mm，保持原物理模型、机械1.2入口、数值门及预算。任务/case目标同步正确，原27模型a2d6/方向/39输入/68source均通过静态核对。

实际唯一prepare terminal exit0/pass，outer.3866747999563813秒、峰值26644480字节，106pins不变；随后179项生产/参考协议已冻结。独立审阅发现audit_cycle005.py第135行仍要求`self.stage.name == "coarse_square_cycle_004"`，实际是005，会在reference load身份门拒绝新卡。作者第一次静审遗漏此谓词；AST/compile通过不能证明所有新身份正确。

在生产前关闭，生产/参考launcher、execution receipt、result/reference目录均实际不存在；新F/T/solver/HP/geometry/test各0。本卡没有实际平衡状态、数值失败、partial或新参考资格。未借用004结果作本卡执行，未调用错误包装去人为制造形式失败。

保留原冻结audit/source_freeze/protocol与输入字节，两个独立blocked审阅及[关闭回执](preproduction_closure.json)在本目录，不修复或重跑本卡。新006卡仅修正严格阶段身份及其角色名字，复用同1mm物理任务、原settings/GATES及600/660生产、240/300参考、8GiB采样限额；1mm生产额度在005未使用。任何下一卡运行与资格需分别记录，不归入本卡。

006安装前另有作者路径替换遗漏：installer/builder仍指005。该问题由安装前静审捕获，作者v1字节保留于外部.author_v1文件，未运行安装器/未准备006时修正；不是006正式调用重试。以后身份核对应检查实际AST字段值，不能仅凭新文件名。主实现未改，旧004成功/003失败与旧T25输入未知事实保留。当前真实1mm效果仍待006执行，后续同现有记录/图查看。
'''
assert not (STAGE/'RESULTS.md').exists()
(STAGE/'RESULTS.md').write_bytes(text.encode('utf-8'))
print(json.dumps({'status':'closed_before_production','all179_bindings_unchanged':True,'new_numerical_calls':0}))
