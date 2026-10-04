"""Prepare two independent saved-only cards for the closed cycle008 time-limit failure; never launch."""
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
    card = view/('partial_boundary_saved_001' if args.mode == 'unsigned' else 'partial_saved_001')
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
    forbidden_reference = [stage/name for name in ('reference', 'reference_launch.json', 'reference_stdout.log')]
    if any(path.exists() for path in forbidden_reference):
        raise ValueError('This closed partial card requires no reference/HP phase')
    if not (production_launch['status'] == 'not_pass' and production_launch['exit_code'] == 1
            and production_launch.get('completed_utc') and production_launch['all_bindings_unchanged']):
        raise ValueError('The original production failure is not terminal')
    receipt = read(stage/'execution_receipt.json')
    bind(stage/'execution_receipt.json', '05a0337c48e036085aec03252a5462af07bb33bd3bd35f274ae30938fe19c06a')
    bind(stage/'input_inventory.json', receipt['input_inventory_sha256'])
    bind(stage/'source_freeze.json', receipt['source_freeze_sha256'])
    inventory, freeze = read(stage/'input_inventory.json'), read(stage/'source_freeze.json')
    if not (receipt['status'] == 'not_pass' and receipt['sources_unchanged'] and receipt['inputs_unchanged']
            and receipt['sources'] == freeze['sources'] and receipt['inputs'] == inventory['input_bindings']
            and len(freeze['sources']) == 68 and len(inventory['input_bindings']) == 53):
        raise ValueError('Closed cycle008 production/source/input contract differs')
    for name, pin in freeze['sources'].items():
        bind(stage/'sources'/Path(name).name, pin)
    for name, pin in inventory['input_bindings'].items():
        bind(root/name, pin)
    for name in ('protocol.json', 'production_launch.json', 'accepted_progress.jsonl'):
        bind(stage/name)
    if production_launch['protocol_sha256'] != bindings[(stage/'protocol.json').relative_to(root).as_posix()]:
        raise ValueError('Production protocol identity differs')
    bind(stage/'production_launch.json', 'e6104abb3e929681ea113b7193a8b45ee0c059807b8323b2460b2550f24f69da')
    result_dir = stage/inventory['case']['result_directory']
    bind(result_dir/'result.json', receipt['result_sha256'])
    bind(result_dir/'result.json', 'ab363868f489ae8d80e5477e320ca22f55191b71438e6b46c1e9584b2924b8a4')
    result = read(result_dir/'result.json')
    rows = result['states']
    if not (result['schema_version'] == 'hf-native-mean-result-1.2' and result['status'] == 'failed'
            and result['failure']['code'] == receipt['failure']['code'] == 'time_limit'
            and receipt['returned_status'] == 'failed' and receipt['invocations'] == 1
            and result['path_completed'] is False and result['unload_endpoint_reached'] is False
            and result['loading_peak_reached'] is True and result['task_target_executed'] is False
            and result['targets_mm'] == inventory['case']['targets_mm'] == [0., .5, 1., 1.5, 1.75, 1.5, 1., .5, 0.]
            and len(rows) == result['accepted_states'] == receipt['accepted_states'] == 8
            and [row['d'] for row in rows] == [0., .5, 1., 1.5, 1.75, 1.5, 1., .5]
            and [row['original_target_index'] for row in rows] == list(range(8))
            and result['call_counts'] == receipt['call_counts']
            and result['call_counts']['force_calls'] == result['call_counts']['force_calls_completed'] == 63
            and result['call_counts']['tangent_calls'] == result['call_counts']['tangent_calls_completed'] == 36
            and result['call_counts']['solver_invocations'] == 1
            and result['call_counts']['HP_calls'] == receipt['HP_calls'] == 0
            and receipt['first_force_range_input'] is None and receipt['first_tangent_range_input'] is None):
        raise ValueError('Saved data differ from the specific closed eight-state time-limit failure')
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
    measurement_file = view/'partial_boundary_saved_001/measurement_001/boundary_measurements.json'
    if args.mode == 'render':
        unsigned = view/'partial_boundary_saved_001'
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
    copy(Path(__file__).resolve(), card/'sources/build_partial_saved_card.py', sha(Path(__file__).resolve()))
    source_records.update(launch_phase=LAUNCH_PIN, build_partial_saved_card=sha(Path(__file__).resolve()), numeric_helper=HELPER_PIN)
    readme = ('# Cycle008 closed-failure partial saved '+args.mode+' card\n\n'
        'The original production card is closed: time_limit, eight accepted states, no reference/HP phase.\n'
        'This separate pure saved-data card is not a mechanical repair, retry or qualification. No phase is launched by the builder.\n'
        'One helper window 120 seconds, one outer window 120 seconds, sampled RSS 8 GiB.\n'
        'These are the exact old007 saved-card budgets; the region cards use separate budgets.\n'
        'First error closes this card; retain partial evidence, no repair, retry or force.\n'
        'Eight actual accepted indices are retained: 0,.5,1,1.5,1.75,1.5,1,.5 mm. Requested return0 was not reached.\n'
        'Unsigned boundary distance is not signed penetration, pressure or contact qualification.\n'
        'The physical view stays PRODUCTION ONLY / FAILED / PARTIAL; no fresh or inherited HP qualification.\n')
    with (card/'README.md').open('x', encoding='utf-8') as stream:
        stream.write(readme)
    bind(card/'README.md')
    write(card/'source_freeze.json', dict(schema_version='native-cycle008-partial-saved-source-freeze-1.0',
        sources=source_records, production_capsules=freeze['sources'], scope='Separate saved-only visualization of closed time-limit failure; no repair/retry or mechanical qualification'))
    bind(card/'source_freeze.json')
    protocol = dict(schema_version='native-cycle008-partial-saved-'+args.mode+'-card-1.0',
        sampled_RSS_bytes=8*1024**3, bindings=bindings,
        phases={phase:dict(argv=argv, helper_seconds=120, outer_seconds=120)},
        stop_policy='One phase; first failure closes card; no repair/retry/force',
        reference_started=False, mechanical_phase_closed=True, production_status='failed', accepted_states=len(rows),
        no_new_mechanics=True, displayed_HP_qualification=False, partial_saved_visualization=True,
        original_production_call_counts=result['call_counts'], return_zero_present=False)
    if args.mode == 'unsigned':
        protocol.update(input_directory=result_dir.relative_to(root).as_posix(), expected_geometry_calls=len(rows))
    if any(path.exists() for path in forbidden_reference) or not all(sha(root/name) == pin for name, pin in bindings.items()):
        raise ValueError('Inputs changed while preparing saved card; retain incomplete card')
    write(card/'protocol.json', protocol)
    print(json.dumps(dict(mode=args.mode, card=card.relative_to(root).as_posix(), bindings=len(bindings),
                         accepted_states=len(rows), protocol_sha256=sha(card/'protocol.json'), launched=False)))


if __name__ == '__main__':
    main()
