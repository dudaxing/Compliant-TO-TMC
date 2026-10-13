"""Freeze M-PREF1 ordinary protocol; no scientific file reads or execution."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import ast
import json

HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/unload_reference_001'
FILES = ('execute_partial_reference.py','launch_reference.py','plot_partial_reference_observation.py',
    'M-PREF1_CARD.md','PREPARATION_RESULTS.md','author/front_prefix.md',
    'author/input_scope_review.json','author/input_scope_review.md',
    'author/physical_gate_review.json','author/physical_gate_review.md',
    'author/SOURCE_AUTHOR_NOTES.md','author/source_author_receipt.json','author/input_contract_seed.json',
    'author/prepare_stage.py','author/publisher_source.py','author/record_authorization.py',
    'author/METADATA_TOOL_SOURCE_NOTES.md','author/metadata_tools_author_receipt.json','author/freeze_protocol.py')


def main():
    seedraw = (HERE/'input_contract_seed.json').read_bytes()
    protocol = json.loads(seedraw)
    author = json.loads((HERE/'source_author_receipt.json').read_bytes())
    assert protocol['schema_version'] == 'partial-saved-state-independent-reference-card-1.0'
    assert protocol['card'] == author['card'] == 'M-PREF1'
    assert protocol['source_baseline_commit'] == author['source_baseline_commit'] == 'eb92b41fd58547640d2c2a8381f98aa5012154df'
    assert protocol['prepared'] is True and protocol['authorized'] is protocol['executed'] is False
    assert author['blocking_findings'] == [] and author['authorized'] is author['executed'] is False
    pins = {}
    for name in FILES:
        source = HERE / name.removeprefix('author/')
        assert source.suffix in ('.json','.py','.md')
        value = source.read_bytes()
        if source.suffix == '.py':
            ast.parse(value.decode('utf-8'))
        pins[REL+'/'+name] = sha256(value).hexdigest()
    for name,pin in author['current_source_SHA256'].items():
        assert sha256((HERE/name).read_bytes()).hexdigest() == pin
    protocol['protocol_seed_only'] = False
    protocol['production_accepted_states'] = 9
    protocol['bindings'].update(pins)
    protocol['new_card_source_bindings'] = pins
    protocol['binding_finalization'] = 'Actual ordinary card, runtime and author/tool sources frozen; final review and future human/publication records remain separate to avoid self-reference.'
    protocol['frozen_utc'] = datetime.now(timezone.utc).isoformat()
    value = (json.dumps(protocol,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
    with (HERE/'protocol.json').open('xb') as stream:
        stream.write(value)
    receipt = dict(status='protocol_frozen_ordinary_sources_only',card='M-PREF1',
        source_baseline_commit=protocol['source_baseline_commit'],prepared=True,authorized=False,executed=False,
        created_utc=protocol['frozen_utc'],input_seed_sha256=sha256(seedraw).hexdigest(),
        protocol_SHA256=sha256(value).hexdigest(),source_SHA256=pins,
        final_review_in_protocol_bindings=False,future_publication_or_authorization_fabricated=False,
        scientific_file_reads_hashes_headers_decode=0,new_HF_tests_HP_solver_or_plot_calls=0)
    with (HERE/'protocol_freeze_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=receipt['status'],protocol_SHA256=receipt['protocol_SHA256'],
        mixed_bindings=len(protocol['bindings']),inherited_stat_only_NPZ=len(protocol['inherited_NPZ_bindings']),executed=False)))


if __name__ == '__main__':
    main()
