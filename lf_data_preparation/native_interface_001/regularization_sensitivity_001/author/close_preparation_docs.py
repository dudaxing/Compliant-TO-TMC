"""Write ordinary preparation documentation; preserve both front histories."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/regularization_sensitivity_001'
BASE = '5af8b5eb3d6780065075b8a331b774d8dad57d67'
STAGE = ROOT / REL
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASE
assert not (STAGE/'author/documentation_receipt.json').exists()
protocol = read(STAGE/'protocol.json')
assert not protocol['authorized'] and not protocol['executed']
assert not (STAGE/'run_001').exists() and not (STAGE/'author/authorization.json').exists()
assert all(sha(ROOT/name) == pin for name, pin in protocol['bindings'].items())
peers = {}
for name in ('input_scope_static_review.json', 'physics_static_review.json'):
    path = STAGE/'author'/name
    assert read(path)['status'].startswith('pass')
    peers[name] = sha(path)
for source, target in (('PREPARATION_RESULTS_draft.md', 'PREPARATION_RESULTS.md'), ('README_draft.md', 'README.md')):
    raw = (EXT/source).read_bytes()
    assert raw and b'\xef\xbf\xbd' not in raw and not (STAGE/target).exists()
    (STAGE/target).write_bytes(raw)
body = (EXT/'CURRENT_BODY_draft.md').read_text(encoding='utf-8')
history = []
for name in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
    path = ROOT/name
    old = path.read_bytes()
    old_commit_bytes = subprocess.check_output(['git', 'show', BASE+':'+name], cwd=ROOT)
    assert old == old_commit_bytes
    url = '../'+REL+'/'
    prefix = ('# 当前接续：M-ALPHA1同任务alpha对照已准备、未批准／未执行\n\n'+body+'\n'+
              '[本轮说明与既有可视化]('+url+'PREPARATION_RESULTS.md) · [具体卡]('+url+'M-ALPHA1_CARD.md) · '+
              '[准备协议]('+url+'protocol.json) · [输入／合同静审]('+url+'author/input_scope_static_review.json) · '+
              '[物理静审]('+url+'author/physics_static_review.json)\n\n'+
              '<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
    path.write_bytes(prefix+old+b'\n</details>\n')
    history.append(dict(path=name, old_bytes=len(old), old_sha256=sha256(old).hexdigest(),
                        new_sha256=sha(path), history_start_byte=len(prefix),
                        history_end_byte_exclusive=len(prefix)+len(old), old_body_preserved_exactly=True))
(STAGE/'author/close_preparation_docs.py').write_bytes(Path(__file__).read_bytes())
receipt = dict(status='pass_preparation_documentation_no_execution', source_baseline_commit=BASE,
               front_history=history, peer_reports=peers, protocol_sha256=sha(STAGE/'protocol.json'),
               report_sha256=sha(STAGE/'PREPARATION_RESULTS.md'), README_sha256=sha(STAGE/'README.md'),
               actions=dict(new_HF_imports=0,new_NPZ_decodes=0,new_models=0,new_F_T=0,new_solves=0,new_HP=0,new_renders=0),
               authorized=False, executed=False, whole_HF5_complete=False)
with (STAGE/'author/documentation_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status=receipt['status'],fronts=len(history),bindings=len(protocol['bindings']))))
