"""Bind the actual human approval; preserve the pending preparation unchanged."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

P=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
pin=lambda p:sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
review=read(P/'SOURCE_REVIEW.json')
assert review['status']=='ready_pending_execution_approval'
for name,expected in review['reviewed_author_sha256'].items():assert pin(P/name)==expected,name
archive=P/'pending_records';archive.mkdir(exist_ok=False)
names=('SOURCE_REVIEW.json','SOURCE_REVIEW.md','protocol.proposed.json','authorization.proposed.json',
       'step_task.json','L-CTIPSTEP3_CARD.md','freeze_step.py','PREPARATION_STATUS.json','BLOCKED_AUDIT.json')
for name in names:(archive/name).write_bytes((P/name).read_bytes())
answer='批准按 L-CTIPSTEP3 执行'
request_id='call_d126440529dd4847b41259b55dacdc3e'
task=read(P/'step_task.json')
task['parameter_origin']='L-CTIPSTEP3 explicitly approved by the user: preserve [0,.25,.5,.75,.9] and append .95 mm from the terminal .90 mm accepted state; all remaining physics and original gates unchanged.'
task['description']='Revalidate the original .90 mm anchor and extend to .95 mm, preserving all nested provenance; observe actual tip approach and right-medium response without replaying previous targets.'
write(P/'step_task.json',task)
protocol=read(P/'protocol.proposed.json')
protocol['task_metadata']={name:task[name] for name in ('task_id','purpose','parameter_origin','description')}
protocol['input_bindings'][protocol['task_file']]=pin(P/'step_task.json')
protocol.update(direct_user_request=answer,execution_authorization_status='explicitly_approved',
                execution_authorization_basis='Actual user reply to '+request_id)
write(P/'protocol.proposed.json',protocol)
auth=read(P/'authorization.proposed.json')
auth.update(authorized=True,authorization_from_direct_human_request=True,direct_human_request=answer,
            protocol_sha256=pin(P/'protocol.proposed.json'),status='explicitly_approved',question_call_id=request_id,
            scope='Approved one .90 to .95 saved extension under the unchanged card, actual saved views, records, normal main push and local-Git different-path recovery.')
write(P/'authorization.proposed.json',auth)
card=(P/'L-CTIPSTEP3_CARD.md').read_text(encoding='utf-8')
card=card.replace('（候选，待授权）','（已批准，尚未执行）')
card=card.replace('本轮只准备下一步可审查候选，不修改默认HF实现，不启动求解、HP、测试、冻结、提交或推送。',
                  '用户已明确批准按本卡实施并执行。复用已审候选，不修改默认HF实现；按下述唯一窗口计算和显示，保留原门与资格限制。')
card=card.replace('获批后绑定真实批准消息，重核最终授权记录和受影响SHA，再冻结并唯一启动。',
                  '已收到真实批准消息；完成最终授权记录和受影响SHA复核后，冻结并唯一启动。')
(P/'L-CTIPSTEP3_CARD.md').write_text(card,encoding='utf-8',newline='\n')
record=dict(status='actual_human_approval_bound_not_executed',card='L-CTIPSTEP3',answer=answer,
    question_call_id=request_id,created_utc=datetime.now(timezone.utc).isoformat(),
    pending_records={name:pin(archive/name) for name in names},protocol_sha256=pin(P/'protocol.proposed.json'),
    changed_scope='Explanatory metadata, explicit approval record and card status only. Numerical code, physical task, targets, settings, gates and budgets unchanged.',
    scientific_calls=0,formal_freeze=0)
write(P/'AUTHORIZATION_BINDING.json',record)
print(json.dumps(dict(status=record['status'],protocol_sha256=record['protocol_sha256'])))
