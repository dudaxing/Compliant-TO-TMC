"""Prepare, but never launch, the two cycle008 saved-data cards after terminal science."""
from pathlib import Path
import argparse
import hashlib
import json

MEASURE_PIN = '33dc17e7ce96bbd075d37fa6e7a0232dbe7dbda18280423770058e120a9ac56a'
LAUNCH_PIN = 'f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477'
PLOT_PIN = 'ba14de8876130f8bee0e97c7056092982a499611c717a7dbc0d233be831d46f7'
HELPER_PIN = 'd256fe2b1541505cd5315f45c4a50462670a09436ceb91ecc8d01bbb25554169'
BOUNDARY_SOURCES = {
    'hf_repo/scripts/measure_native_workpiece_boundaries.py': '2a3c3e2d67a00fa9372f4befe2a44645f0234ee4f3ebcf31bcab6df08512937f',
    'hf_repo/src/hf_eval/boundary_geometry.py': 'b22a9efe9bb29cdf94746f694a721df42bd0f867ba8c2252915e072b6a73fb31',
    'hf_repo/src/hf_eval/__init__.py': '112503f3077d6b8e2ba6f28c8895eb907065c2a5718084048af77893b05eb73b',
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8'))


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--mode', choices=('unsigned', 'render'), required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    stage = root/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_008'
    view = root/'functional_views/native_workpiece_cycle008_20261004'
    card = view/('boundary_saved_001' if args.mode == 'unsigned' else 'saved_001')
    bindings = {}

    def bind(path, expected=None):
        path = path.resolve()
        key = path.relative_to(root).as_posix()
        actual = sha(path)
        if expected is not None and actual != expected:
            raise ValueError('Saved source/input SHA differs: '+key)
        if key in bindings and bindings[key] != actual:
            raise ValueError('Binding changed during preparation: '+key)
        bindings[key] = actual
        return actual

    def copy(source, destination, expected):
        payload = source.read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError('Copied source differs: '+str(source))
        with destination.open('xb') as stream:
            stream.write(payload)
        bind(destination, expected)

    # Read terminal records before creating a card; do not prepare against a live result.
    production_launch = read(stage/'production_launch.json')
    reference_launch = read(stage/'reference_launch.json')
    if not (production_launch['status'] == 'pass' and production_launch['exit_code'] == 0
            and production_launch.get('completed_utc') and production_launch['all_bindings_unchanged']):
        raise ValueError('Production has not terminally passed')
    if reference_launch['status'] not in ('pass', 'not_pass') or not reference_launch.get('completed_utc'):
        raise ValueError('Reference must be terminal before preparing a saved card')
    receipt = read(stage/'execution_receipt.json')
    bind(stage/'execution_receipt.json')
    bind(stage/'input_inventory.json', receipt['input_inventory_sha256'])
    bind(stage/'source_freeze.json', receipt['source_freeze_sha256'])
    inventory, freeze = read(stage/'input_inventory.json'), read(stage/'source_freeze.json')
    if not (receipt['status'] == 'pass' and receipt['sources_unchanged'] and receipt['inputs_unchanged']
            and receipt['sources'] == freeze['sources'] and receipt['inputs'] == inventory['input_bindings']
            and len(freeze['sources']) == 68 and len(inventory['input_bindings']) == 53):
        raise ValueError('Cycle008 terminal production/source/input contract differs')
    for name, pin in freeze['sources'].items():
        bind(stage/'sources'/Path(name).name, pin)
    for name, pin in inventory['input_bindings'].items():
        bind(root/name, pin)
    for name in ('protocol.json', 'production_launch.json', 'reference_launch.json', 'accepted_progress.jsonl'):
        bind(stage/name)
    if production_launch['protocol_sha256'] != bindings[(stage/'protocol.json').relative_to(root).as_posix()]:
        raise ValueError('Production protocol identity differs')
    if reference_launch['protocol_sha256'] != production_launch['protocol_sha256']:
        raise ValueError('Reference protocol identity differs')
    if (stage/'reference/summary.json').is_file():
        bind(stage/'reference/summary.json')
    result_dir = stage/inventory['case']['result_directory']
    bind(result_dir/'result.json', receipt['result_sha256'])
    result = read(result_dir/'result.json')
    rows = result['states']
    if not (result['schema_version'] == 'hf-native-mean-result-1.2' and result['status'] == 'success'
            and result['path_completed'] and result['unload_endpoint_reached']
            and result['task_target_executed'] and result['targets_mm'] == inventory['case']['targets_mm']
            and len(rows) == result['accepted_states'] == receipt['accepted_states'] and len(rows) >= 2):
        raise ValueError('Saved result is not the completed cycle008 path')
    model_decl = result['model']
    bind(result_dir/model_decl['descriptor_path'], model_decl['descriptor_file_sha256'])
    bind(result_dir/model_decl['arrays_path'], model_decl['arrays_sha256'])
    geometry = result['source_geometry']
    bind(result_dir/geometry['snapshot']['descriptor'], geometry['descriptor_file_sha256'])
    bind(result_dir/geometry['snapshot']['arrays'], geometry['arrays_sha256'])
    for row in rows:
        bind(result_dir/row['descriptor_path'], row['descriptor_file_sha256'])
        for field in ('state', 'forces', 'tangents', 'matrix'):
            bind(result_dir/row[field]['path'], row[field]['sha256'])
    helper = root/'functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py'
    bind(helper, HELPER_PIN)
    old_card = root/'functional_views/native_workpiece_cycle007_20261004/boundary_saved_001'
    measurement_file = view/'boundary_saved_001/measurement_001/boundary_measurements.json'
    if args.mode == 'render':
        unsigned = view/'boundary_saved_001'
        measured, launched = read(unsigned/'measurement_receipt.json'), read(unsigned/'measure_launch.json')
        if not (measured['status'] == launched['status'] == 'pass' and launched['exit_code'] == 0
                and measured['all_bindings_unchanged'] and launched['all_bindings_unchanged']
                and measured['geometry_calls_started'] == measured['geometry_calls_completed'] == len(rows)):
            raise ValueError('The separate saved unsigned-geometry card has not passed')
        bind(measurement_file, measured['measurement_sha256'])
        measurement = read(measurement_file)
        if not (measurement['schema_version'] == 'native-workpiece-boundary-path-1.0'
                and measurement['production_status'] == result['status']
                and measurement['task_sha256'] == result['task_sha256'] and measurement['input_files_unchanged']
                and len(measurement['accepted_states']) == len(rows)):
            raise ValueError('Measurement state coverage differs')
        for index, (saved, row) in enumerate(zip(measurement['accepted_states'], rows)):
            if not (saved['accepted_index'] == index and saved['state_sha256'] == row['state_sha256']
                    and saved['d_mm'] == row['d'] and saved['leg'] == row['leg']
                    and saved['original_target_index'] == row['original_target_index']):
                raise ValueError('Measurement state identity/order differs')
        for name in ('protocol.json', 'measure_launch.json', 'measurement_receipt.json', 'source_freeze.json'):
            bind(unsigned/name)
        for name, pin in read(unsigned/'protocol.json')['bindings'].items():
            bind(root/name, pin)
    else:
        for name, pin in BOUNDARY_SOURCES.items():
            bind(root/name, pin)
    card.mkdir(parents=True, exist_ok=False)
    (card/'sources').mkdir()
    copy(old_card/'launch_phase.py', card/'launch_phase.py', LAUNCH_PIN)
    source_records = {}
    if args.mode == 'unsigned':
        copy(old_card/'measure_saved_once.py', card/'measure_saved_once.py', MEASURE_PIN)
        source_records['measure_saved_once.py'] = MEASURE_PIN
        for name, pin in BOUNDARY_SOURCES.items():
            copy(root/name, card/'sources'/Path(name).name, pin)
            source_records[Path(name).name] = pin
        phase, argv = 'measure', [(card/'measure_saved_once.py').relative_to(root).as_posix()]
    else:
        copy(Path(__file__).resolve().parent/'plot_workpiece_cycle008.py', card/'plot_workpiece_cycle008.py', PLOT_PIN)
        source_records['plot_workpiece_cycle008.py'] = PLOT_PIN
        phase = 'render'
        argv = [(card/'plot_workpiece_cycle008.py').relative_to(root).as_posix(),
                '--stage', stage.relative_to(root).as_posix(), '--output', (card/'render_001').relative_to(root).as_posix(),
                '--protocol', (card/'protocol.json').relative_to(root).as_posix(),
                '--measurements', measurement_file.relative_to(root).as_posix()]
    copy(Path(__file__).resolve(), card/'sources/build_saved_card.py', sha(Path(__file__).resolve()))
    source_records.update(launch_phase=LAUNCH_PIN, build_saved_card=sha(Path(__file__).resolve()), numeric_helper=HELPER_PIN)
    readme = ('# Cycle008 saved '+args.mode+' card\n\n'
        'Prepared only after production success and terminal reference. No phase is launched by the builder.\n'
        'One helper window 120 seconds, one outer window 120 seconds, sampled RSS 8 GiB.\n'
        'These are the exact old007 saved-card budgets; the region cards use separate budgets.\n'
        'First error closes this card; retain partial evidence, no repair, retry or force.\n'
        'Actual accepted indices, including repeated zero and bisections, remain separate.\n'
        'Unsigned boundary distance is not signed penetration, pressure or contact qualification.\n'
        'The physical view stays PRODUCTION ONLY; reference outcome is bound separately.\n')
    with (card/'README.md').open('x', encoding='utf-8') as stream:
        stream.write(readme)
    bind(card/'README.md')
    write(card/'source_freeze.json', dict(schema_version='native-cycle008-saved-source-freeze-1.0',
        sources=source_records, production_capsules=freeze['sources'], scope='Saved-data card; no constitutive or equilibrium execution'))
    bind(card/'source_freeze.json')
    protocol = dict(schema_version='native-cycle008-saved-'+args.mode+'-card-1.0',
        sampled_RSS_bytes=8*1024**3, bindings=bindings,
        phases={phase:dict(argv=argv, helper_seconds=120, outer_seconds=120)},
        stop_policy='One phase; first failure closes card; no repair/retry/force',
        reference_terminal_status=reference_launch['status'], accepted_states=len(rows),
        no_new_mechanics=True, displayed_HP_qualification=False)
    if args.mode == 'unsigned':
        protocol.update(input_directory=result_dir.relative_to(root).as_posix(), expected_geometry_calls=len(rows))
    if not all(sha(root/name) == pin for name, pin in bindings.items()):
        raise ValueError('Inputs changed while preparing saved card; retain incomplete card')
    write(card/'protocol.json', protocol)
    print(json.dumps(dict(mode=args.mode, card=card.relative_to(root).as_posix(), bindings=len(bindings),
                         accepted_states=len(rows), protocol_sha256=sha(card/'protocol.json'), launched=False)))


if __name__ == '__main__':
    main()
