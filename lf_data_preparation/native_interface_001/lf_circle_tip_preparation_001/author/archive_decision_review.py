"""Archive the ordinary physical decision; never touch scientific/media payloads."""
from hashlib import sha256
from pathlib import Path

AUTHOR=Path(__file__).resolve().parent
STAGE=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC/lf_data_preparation/native_interface_001/lf_circle_tip_preparation_001')
pins={'PHYSICAL_DECISION_REVIEW.json':'1fa5870632be44744d9f21d93be81b1725bd1ce83a8a72db4f4932bda1e8d1e4',
      'PHYSICAL_DECISION_REVIEW.md':'ffb9fb8ec1afb5dd57d21aa6c4cad7242f457e561ed0d55a122222913b6a6433'}
for name,pin in pins.items():
    raw=(AUTHOR/name).read_bytes()
    assert sha256(raw).hexdigest()==pin,name
    target=STAGE/'author'/name
    assert not target.exists()
    target.write_bytes(raw)
for name in ('RESULTS.md','NEXT_STEPS.md'):
    path=STAGE/name
    raw=path.read_bytes()
    path.write_bytes(raw+b'\n'+('[独立物理取舍与下一步观察项](author/PHYSICAL_DECISION_REVIEW.md)\n').encode('utf-8'))
(STAGE/'author/archive_decision_review.py').write_bytes(Path(__file__).read_bytes())
print('Ordinary physical decision archived and linked; no science or media read.')
