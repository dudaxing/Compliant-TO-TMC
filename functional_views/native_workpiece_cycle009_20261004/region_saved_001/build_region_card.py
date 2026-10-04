"""Prepare one saved-cycle009 region card only after production and HP pass.

This builder reads files and copies pinned sources; it never measures geometry.
The unchanged region CLI later measures each actual accepted index once.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET

DEFAULT_ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
TARGETS = [0., .5, 1., 1.5, 1.75, 1.5, 1., .5, 0.]
GEOMETRY_FILES = [
    'hf_repo/src/hf_eval/__init__.py',
    'hf_repo/src/hf_eval/boundary_geometry.py',
    'hf_repo/src/hf_eval/native_region_geometry.py',
    'hf_repo/scripts/measure_native_workpiece_regions.py',
]
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    mechanical = root/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_009'
    proof = root/'functional_views/native_region_geometry_20261004/square007_002'
    stage = root/'functional_views/native_workpiece_cycle009_20261004/region_saved_001'
    rel = lambda path: path.relative_to(root).as_posix()
    pins = {}

    def bind(path, expected=None):
        value = sha(path)
        assert expected is None or value == expected, rel(path)
        pins[rel(path)] = value
        return value

    def terminal(path, protocol_sha):
        receipt = read(path)
        assert receipt['status'] == 'pass' and receipt['exit_code'] == 0
        assert receipt['invocations'] == 1 and receipt['all_bindings_unchanged']
        assert receipt['stop_reason'] is None and receipt['protocol_sha256'] == protocol_sha
        bind(path)
        return receipt

    def archives(value, base):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                bind(base/value['path'], value['sha256'])
            for item in value.values():
                archives(item, base)
        elif isinstance(value, list):
            for item in value:
                archives(item, base)

    # Current science bindings are exact. No exception for historical chunk113
    # live-source changes is admitted by this new geometry card.
    science = read(mechanical/'protocol.json')
    science_sha = bind(mechanical/'protocol.json')
    for name, expected in science['bindings'].items():
        bind(root/name, expected)
    inventory = read(mechanical/'input_inventory.json')
    freeze = read(mechanical/'source_freeze.json')
    assert len(inventory['input_bindings']) == 63 and len(freeze['sources']) == 68
    bind(mechanical/'source_freeze.json', inventory['source_freeze_sha256'])
    for name, expected in inventory['input_bindings'].items():
        bind(root/name, expected)
    for name, expected in freeze['sources'].items():
        bind(root/name, expected)
        bind(mechanical/'sources'/Path(name).name, expected)
    terminal(mechanical/'production_launch.json', science_sha)
    terminal(mechanical/'reference_launch.json', science_sha)
    receipt = read(mechanical/'execution_receipt.json')
    result_file = mechanical/'result/result.json'
    result = read(result_file)
    reference = read(mechanical/'reference/summary.json')
    bind(mechanical/'execution_receipt.json')
    bind(result_file, receipt['result_sha256'])
    bind(mechanical/'reference/summary.json')
    assert receipt['status'] == 'pass' and receipt['invocations'] == 1
    assert receipt['sources_unchanged'] and receipt['inputs_unchanged']
    assert result['status'] == 'success' and result['schema_version'] == 'hf-native-mean-result-1.2'
    assert all(result[key] is True for key in ('target_reached', 'path_completed',
               'loading_peak_reached', 'unload_endpoint_reached', 'task_target_executed'))
    assert result['targets_mm'] == inventory['case']['targets_mm'] == TARGETS
    states = result['states']
    count = len(states)
    assert count >= len(TARGETS) and count == result['accepted_states'] == receipt['accepted_states']
    assert reference['status'] == 'pass' and reference['accepted_states'] == count
    assert reference['result_sha256'] == sha(result_file)
    assert reference['HP_calls_started'] == reference['HP_calls_completed'] == 2*count
    assert len(reference['states']) == count
    for index, (state, audited) in enumerate(zip(states, reference['states'])):
        assert audited['status'] == 'pass' and audited['index'] == index
        assert audited['state_sha256'] == state['state_sha256']
        assert audited['original_target_index'] == state['original_target_index']
        assert audited['leg'] == state['leg'] and audited['target_mm'] == state['d']
    for index, target in enumerate(TARGETS):
        assert any(row['original_target_index'] == index and row['d'] == target for row in states)
    for path in sorted((mechanical/'result').rglob('*')):
        if path.is_file() and path.suffix in ('.json', '.npz'):
            bind(path)
    for name, expected in reference['input_bindings'].items():
        bind(root/name, expected)
    archives(reference['states'], mechanical/'reference')

    # The original39 analytic tests are saved provenance for the unchanged
    # pure geometry implementation, not another test invocation or HP call.
    proof_protocol_sha = bind(proof/'protocol.json')
    terminal(proof/'tests_launch.json', proof_protocol_sha)
    bind(proof/'tests_001/junit.xml')
    suites = list(ET.parse(proof/'tests_001/junit.xml').getroot().iter('testsuite'))
    assert sum(int(row.attrib['tests']) for row in suites) == 39
    assert all(int(row.attrib[key]) == 0 for row in suites for key in ('errors', 'failures', 'skipped'))
    old_sources = read(proof/'source_freeze.json')['sources']
    bind(proof/'source_freeze.json')
    for name, item in old_sources.items():
        bind(proof/item['snapshot_path'], item['sha256'])
    for name in GEOMETRY_FILES:
        bind(root/name, old_sources[name]['sha256'])
    assert not stage.exists()
    # Every prerequisite above precedes output creation; invalid prerequisites
    # do not open a new measurement stage or reinterpret a failed old card.
    stage.mkdir(parents=True)
    shutil.copyfile(mechanical/'launch_cycle009.py', stage/'launch_phase.py')
    bind(stage/'launch_phase.py', sha(mechanical/'launch_cycle009.py'))
    shutil.copyfile(Path(__file__).resolve(), stage/'build_region_card.py')
    bind(stage/'build_region_card.py', sha(Path(__file__).resolve()))
    (stage/'sources').mkdir()
    sources = {}
    for name in GEOMETRY_FILES:
        path = root/name
        sources[name] = sha(path)
        shutil.copyfile(path, stage/'sources'/path.name)
        bind(stage/'sources'/path.name, sources[name])
    write(stage/'source_freeze.json', dict(schema_version='saved-cycle009-region-source-freeze-1.0',
        sources=sources, scope='Four unchanged pure geometry sources; launcher and builder separately bound'))
    bind(stage/'source_freeze.json')
    argv = ['hf_repo/scripts/measure_native_workpiece_regions.py', '--repo', 'hf_repo',
        '--input', rel(mechanical/'result'), '--output', rel(stage/'measurement_001'),
        '--stop-file', rel(stage/'stop_requested.txt'), '--time-limit', '120']
    protocol = dict(schema_version='saved-cycle009-region-observation-card-1.0', bindings=pins,
        sampled_RSS_bytes=8*1024**3, phases={'measure': dict(argv=argv, helper_seconds=120, outer_seconds=150)},
        declared_original_targets_mm=TARGETS, actual_accepted_states=count,
        expected_geometry_calls_started=count, expected_geometry_calls_completed=count,
        mechanical_hooks_monitored=False,
        mechanical_call_count_basis='Unchanged CLI checks pure geometry import closure; zero mechanics is not hooked telemetry',
        scope='Saved actual Q1 cell-union interior overlap and finite-square outward first-ray diagnostics; no new unsigned measurement, complete containment, pressure, self-intersection or clamping qualification',
        stop_policy='One invocation; first invalid quad/error stops with partial evidence; no repair/retry/force/budget extension; no F/T/solver/HP/consumer calls')
    write(stage/'protocol.json', protocol)
    print(json.dumps(dict(status='prepared_not_executed', stage=rel(stage), bindings=len(pins),
        own_geometry_sources=len(sources), actual_accepted_states=count, expected_geometry_calls=count,
        helper_seconds=120, outer_seconds=150, sampled_RSS_bytes=8*1024**3,
        protocol_sha256=sha(stage/'protocol.json'))))


if __name__ == '__main__':
    main()
