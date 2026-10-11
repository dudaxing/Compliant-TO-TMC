"""Apply the peer's ordinary wording clarification before delivery freeze."""
from hashlib import sha256
import json
from pathlib import Path

stage = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/saved_continuation_001')
target = stage/'NEXT_STEP_REVIEW.md'
old = target.read_bytes()
before = '下一阶段依据实际卸载曲线和作用力'.encode('utf-8')
after = '下一阶段依据此次局部卸载响应和作用力'.encode('utf-8')
assert old.count(before) == 1
new = old.replace(before,after)
receipt_file = stage/'author/execution_documentation_receipt.json'
receipt = json.loads(receipt_file.read_bytes())
assert receipt['next_step_sha256'] == sha256(old).hexdigest()
target.write_bytes(new)
receipt['next_step_sha256'] = sha256(new).hexdigest()
receipt['next_step_wording_clarification'] = 'Peer review: two accepted endpoints support a local unload response, not a continuous unload curve.'
receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
with (stage/'author/clarify_next_step_text.py').open('xb') as stream:
    stream.write(Path(__file__).read_bytes())
record = dict(status='pass_ordinary_peer_wording_clarification',old_next_step_sha256=sha256(old).hexdigest(),
    new_next_step_sha256=sha256(new).hexdigest(),executed_new_science=False,
    source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
with (stage/'author/next_step_text_clarification.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record))
