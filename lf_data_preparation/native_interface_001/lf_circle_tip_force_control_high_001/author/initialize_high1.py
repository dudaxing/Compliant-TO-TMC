"""Initialize approved high-input execution context with ordinary/source bytes only."""
from hashlib import sha256
import json
from pathlib import Path
import shutil

A=Path(__file__).resolve().parent
BASE=Path('D:/hfh1_001')
ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
PREP=ROOT/'lf_data_preparation/native_interface_001/lf_circle_tip_force_control_high_preparation_001'
assert not any((BASE/name).exists() for name in ('authorization.json','protocol.json','run_001','top_start.json','helper_start.json','execution_evidence.zip'))
BASE.mkdir(exist_ok=True)
for source,name in ((PREP/'L-CTIPFHIGH1_CARD.md','approved_card.md'),
                    (PREP/'SOURCE_BINDING.json','source_binding.json'),
                    (PREP/'observer_binding.json','observer_binding.json'),
                    (Path('D:/hfr1_001/windows_owned_process_sup2.py'),'windows_owned_process_sup2.py')):
    shutil.copyfile(source,BASE/name)
raw=(BASE/'approved_card.md').read_bytes()
auth=dict(stage='L-CTIPFHIGH1',status='authorized_implementation_freeze_static_review_then_unique_execution',
    user_answer='批准按 L-CTIPFHIGH1 卡实施并执行',
    approved_question_scope='main3a9a59d card; wrappers/freeze/independent review then unique original high fixed parent12 P0->P1; hold1.06, samephysics/gates; controller3600/science3900/compare60/shared displayQA600/helper4800/outer4860/64GiB/threads16/viewer8GiB; no retries or newHP/tests/production edits; records/main/restore included',
    baseline='3a9a59dea0b55848814baef252018550249cefaa',
    approved_card_sha256=sha256(raw).hexdigest(),
    historical_header_note='Original approved card bytes retain their preparation-time pending header; this actual user approval supersedes that historical status only.',
    numerical_launched=False,production_modifications=0)
for path in (BASE/'authorization.json',A/'authorization.json'):
    path.write_bytes((json.dumps(auth,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(stage='L-CTIPFHIGH1',status='initialized_not_launched',scientific_reads=0,
                     original_card_SHA=auth['approved_card_sha256'])))
