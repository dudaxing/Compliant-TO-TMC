from pathlib import Path
from hashlib import sha256
import difflib
import json

base=Path(__file__).resolve().parent
new,old=base/"pose002_candidate",base/"pose_candidate"
readme=(old/"README.md").read_text(encoding="utf-8").replace("shift_square_pose_001", "shift_square_pose_002").replace("900", "1500").replace("960", "1560")
readme+="\n## Independent resource revision\n\nThe closed900s pose001 card is preserved as failed complete-task evidence. This new card repeats all eleven targets from zero once, with explicit settings.time_limit_seconds1500 and helper/outer1500/1560s,8GiB. Task and producer bytes, mechanics, original numerical gates and max bisections remain exact. Old001 contributes cost/rejection provenance only; no accepted prefix or HP qualification is inherited. Historical author diffs and notes retain their original role; current resource_revision_note and resource_delta diffs describe this card.\n"
(new/"README.md").write_text(readme,encoding="utf-8")
for name in ("prepare_shift_pose.py", "build_pose_card.py"):
    (new/(name+".resource_delta.diff")).write_text("".join(difflib.unified_diff(
        (old/name).read_text(encoding="utf-8").splitlines(keepends=True),
        (new/name).read_text(encoding="utf-8").splitlines(keepends=True),fromfile="pose001/"+name,tofile="pose002/"+name)),encoding="utf-8")
note=json.loads((new/"resource_revision_note.json").read_text(encoding="utf-8"))
note["author_sha256"]={p.name:sha256(p.read_bytes()).hexdigest() for p in new.iterdir() if p.is_file() and p.name!="resource_revision_note.json" and "review" not in p.name}
(new/"resource_revision_note.json").write_text(json.dumps(note,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
doc=Path("D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/docs/WORKPIECE_SHIFT_AND_SOFTNESS_20261004.md")
body=doc.read_text(encoding="utf-8").replace("旧失败、源胶囊和诊断未覆盖。", "旧失败、源胶囊和诊断未覆写。")
body=body.replace("右移生产已按独立900/960秒、8GiB卡唯一启动。", "右移001的900/960秒、8GiB卡已按time_limit关闭：13实际接受态至峰值1.8和卸载1.75，完整返回0未达；helper908.25396390/outer910.05984970秒，F108/102、T58/57、HP0。六个invalid_J预测均原样回滚并二分；终末T58未返回由时间窗口停止引起，无range capture。旧卡不延时、不重跑、不执行完整态参考。独立002将从零求同11目标，仅明确把settings/helper/outer时间改为1500/1500/1560秒，8GiB保持，旧001仅作为实际成本与拒绝原因来源。")
doc.write_text(body,encoding="utf-8")
print(json.dumps(dict(status="author_finalized",producer_sha256=sha256((new/"execute_shift_pose.py").read_bytes()).hexdigest())))
