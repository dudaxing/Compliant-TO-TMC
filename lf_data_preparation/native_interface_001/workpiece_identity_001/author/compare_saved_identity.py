"""Compare saved right4/API bytes and provenance; never decode arrays or run HF."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
from time import perf_counter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started = perf_counter()
    root = args.repo.resolve()
    output = (root / args.output).resolve()
    assert not output.exists()
    old_stage = root / 'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001'
    old_dir = old_stage / 'run_001/result'
    new_stage = root / 'lf_data_preparation/native_interface_001/workpiece_forward_001'
    new_dir = new_stage / 'run_001/fixed_square'
    checked = {}

    def identity(path):
        path = path.resolve()
        rel = path.relative_to(root).as_posix()
        if rel not in checked:
            h = sha256()
            with path.open('rb') as f:
                for block in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(block)
            checked[rel] = dict(bytes=path.stat().st_size, sha256=h.hexdigest())
        return checked[rel]['sha256']

    def read(path):
        identity(path)
        return json.loads(path.read_bytes())

    old, new = (read(p / 'result.json') for p in (old_dir, new_dir))
    ref_file = old_stage / 'reference/summary.json'
    ref = read(ref_file)
    contract_file = old_stage / 'reference_contract.json'
    contract = read(contract_file)
    assert ref['status'] == 'pass' and ref['HP_calls_started'] == ref['HP_calls_completed'] == 48
    assert ref['result_sha256'] == contract['production_result_sha256'] == identity(old_dir / 'result.json')
    assert ref['independent_reference_contract_sha256'] == identity(contract_file)
    assert old['accepted_states'] == new['accepted_states'] == len(ref['states']) == 24
    source_rows = []
    for name, pin in contract['reference_sources'].items():
        assert identity(root / name) == pin
        copy = old_stage / 'reference/reference_sources' / Path(name).name
        assert identity(copy) == pin
        source_rows.append(dict(path=name, sha256=pin))
    assert ref['independent_reference_source_bindings'] == contract['reference_sources']
    assert old['mechanics_source_sha256'] == new['mechanics_source_sha256']
    for name, pin in new['mechanics_source_sha256'].items():
        assert identity(root / name) == pin
    pairs = []

    def same_files(kind, left, right, pin):
        assert identity(left) == identity(right) == pin
        pairs.append(dict(kind=kind, old=left.relative_to(root).as_posix(),
            new=right.relative_to(root).as_posix(), sha256=pin, bytes=left.stat().st_size))

    old_model_file, new_model_file = (directory / value['model']['descriptor_path']
        for directory, value in ((old_dir, old), (new_dir, new)))
    assert old['model'] == new['model']
    same_files('model_json', old_model_file, new_model_file, old['model']['descriptor_file_sha256'])
    model = read(old_model_file)
    same_files('model_arrays', old_model_file.parent / model['arrays']['path'],
        new_model_file.parent / model['arrays']['path'], model['arrays']['sha256'])
    geometry = model['source_geometry']
    for name, pin in [('descriptor', geometry['descriptor_file_sha256']), ('arrays', geometry['arrays_sha256'])]:
        same_files('geometry_' + name, old_model_file.parent / geometry['snapshot'][name],
            new_model_file.parent / geometry['snapshot'][name], pin)
    rows = []
    state_ignored = {'elapsed_seconds', 'descriptor_sha256', 'descriptor_file_sha256'}
    for index, (a, b, reference) in enumerate(zip(old['states'], new['states'], ref['states'])):
        differences = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
        assert set(differences) <= state_ignored
        assert {k:v for k,v in a.items() if k not in state_ignored} == {k:v for k,v in b.items() if k not in state_ignored}
        assert reference['index'] == index and reference['status'] == 'pass' and reference['HP_calls'] == 2
        assert reference['state_sha256'] == a['state_sha256'] == b['state_sha256']
        assert reference['target_mm'] == b['d'] and reference['original_target_index'] == b['original_target_index']
        assert reference['leg'] == b['leg']
        for directory, value in ((old_dir, a), (new_dir, b)):
            assert identity(directory / value['descriptor_path']) == value['descriptor_file_sha256']
            stored = read(directory / value['descriptor_path'])
            assert stored == {k:v for k,v in value.items() if k not in {'descriptor_path', 'descriptor_file_sha256'}}
        for name in ('state', 'forces', 'tangents', 'matrix'):
            assert a[name] == b[name]
            same_files(name, old_dir / a[name]['path'], new_dir / b[name]['path'], a[name]['sha256'])
        raw = reference['raw_fixture']
        assert identity(old_stage / 'reference' / raw['path']) == raw['sha256']
        rows.append(dict(index=index, d_mm=b['d'], leg=b['leg'], state_sha256=b['state_sha256'],
            cached_archives_identical=4, force_fields_declared_identical=len(b['forces']['fields']),
            tangent_fields_declared_identical=len(b['tangents']['fields']), differing_state_JSON_fields=differences))
    excluded = {'states', 'timing_seconds', 'path_diagnostics', 'descriptor_sha256'}
    assert {k:v for k,v in old.items() if k not in excluded} == {k:v for k,v in new.items() if k not in excluded}
    assert {k:v for k,v in old['path_diagnostics'].items() if k != 'timing_seconds'} == {
        k:v for k,v in new['path_diagnostics'].items() if k != 'timing_seconds'}
    inventory = read(old_stage / 'run_001/input_inventory.json')
    assert identity(old_stage / 'run_001/input_inventory.json') == contract['input_inventory_sha256']
    direction = inventory['case']
    direction_file = root / direction['direction_file']
    assert identity(direction_file) == direction['direction_file_sha256']
    assert ref['input_bindings'][direction['direction_file']] == direction['direction_file_sha256']
    assert contract['direction_archive_fields'] == ['direction'] and contract['multiplier_direction'] == 0.0
    response_file = new_dir / 'response.json'
    response = read(response_file)
    assert response['independent_reference']['status'] == 'not_provided'
    assert all(v is False for v in response['producer_flags'].values())
    report = dict(schema_version='native-saved-snapshot-identity-1.0', status='identical_saved_mechanical_snapshot',
        created_utc=datetime.now(timezone.utc).isoformat(), baseline_commit='d508035fdbdbfffdc4f17eda1f26aece1e5ad700',
        old_result=old_dir.relative_to(root).as_posix() + '/result.json', new_result=new_dir.relative_to(root).as_posix() + '/result.json',
        result_files_identical=False, result_differences='Timing and timing-dependent descriptor hashes only; old and new invocation histories remain distinct',
        model_and_geometry_pairs_identical=4, accepted_states_identical=24, cached_archive_pairs_identical=96,
        cached_field_declarations_per_state=dict(state=2, force=16, tangent=3, matrix=3),
        old_reference=dict(summary=ref_file.relative_to(root).as_posix(), sha256=identity(ref_file),
            status=ref['status'], historical_HP_calls=48, qualification=ref['qualification']),
        original_reference_sources_and_copies_checked=len(source_rows), source_rows=source_rows,
        direction=dict(file=direction['direction_file'], file_sha256=direction['direction_file_sha256'],
            array_sha256_declaration=direction['direction_array_sha256'], fields=['direction'], multiplier_direction=0.,
            definition='v=b_in/max(abs(b_in)); fixed DOFs zero; inherited validated PORT direction for byte-identical model',
            fresh_direction_array_decoded_or_reconstructed=False),
        qualification_transfer=False, new_reference_supplied=False, new_producer_flags=response['producer_flags'],
        new_F_T_model_solver_HP_JIT_LF_observer_renderer_calls=0, NPZ_arrays_decoded=0,
        scope='Ordinary byte hashes and JSON equality; no new HP, no HP output re-audit, no change to admission or physical definition',
        decision='Repeating HP on the exact same mathematical snapshot adds no new state information. A separately described historical evidence link may be proposed; current fresh-reference contract and original flags remain unchanged.',
        rows=rows, pairs=pairs, checked_file_identities=checked,
        checked_distinct_files=len(checked), checked_bytes=sum(e['bytes'] for e in checked.values()),
        elapsed_seconds=perf_counter()-started)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({k:report[k] for k in ('status', 'accepted_states_identical', 'cached_archive_pairs_identical',
        'original_reference_sources_and_copies_checked', 'checked_distinct_files', 'checked_bytes', 'elapsed_seconds', 'qualification_transfer')}))


if __name__ == '__main__':
    main()
