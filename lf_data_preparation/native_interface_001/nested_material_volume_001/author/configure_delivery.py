"""Archive final ordinary source reviews and freeze actual delivery identifiers."""
from pathlib import Path
from hashlib import sha256
import ast
import json

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/nested_material_volume_001'
STAGE=ROOT/REL
sha=lambda p:sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
assert not (STAGE/'author/delivery_config.json').exists()
protocol=read(STAGE/'protocol.json')
assert protocol['prepared'] and not protocol['authorized'] and not protocol['executed']
assert not (ROOT/protocol['output_directory']).exists()
for name in ('final_source_static_review.json','deliver_source.py','configure_delivery.py'):
    if name.endswith('.json'):
        assert read(EXT/name)['status'].startswith('pass')
    else:
        ast.parse((EXT/name).read_text(encoding='utf-8'))
    (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
peers={f'{REL}/author/{n}':sha(STAGE/'author'/n)
    for n in ('static_physics_review.json','final_source_static_review.json')}
config=dict(protocol_sha256=sha(STAGE/'protocol.json'),binding_count=len(protocol['bindings']),
    expected_calls=protocol['expected_calls'],expected_counts=protocol['expected_counts'],peer_reviews=peers)
raw=(json.dumps(config,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
(EXT/'delivery_config.json').write_bytes(raw)
(STAGE/'author/delivery_config.json').write_bytes(raw)
assert all(sha(ROOT/name)==pin for name,pin in protocol['bindings'].items())
print(json.dumps(dict(status='actual_source_delivery_configured',protocol_sha256=config['protocol_sha256'],bindings=config['binding_count'])))
