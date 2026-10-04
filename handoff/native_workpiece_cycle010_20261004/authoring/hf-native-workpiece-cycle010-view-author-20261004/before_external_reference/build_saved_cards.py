"""Freeze saved-only cycle010 nodal observation and four actual views."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
VIEW = ROOT/'functional_views/native_workpiece_cycle010_20261004'
MECH = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010'
REGION = VIEW/'region_saved_001'
NODE = VIEW/'nodal_saved_001'
CARD = VIEW/'saved_render_001'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
digest = lambda p: sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()


def write(p, value):
    with p.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')


def terminal(stage, phase, pins):
    protocol = read(stage/'protocol.json')
    for n,v in protocol['bindings'].items():
        assert digest(ROOT/n) == v; pins[n] = v
    pins[rel(stage/'protocol.json')] = digest(stage/'protocol.json')
    receipt = read(stage/(phase+'_launch.json'))
    assert receipt['status'] == 'pass' and receipt['exit_code'] == 0 and receipt['invocations'] == 1
    assert receipt['all_bindings_unchanged'] and receipt['stop_reason'] is None
    assert receipt['protocol_sha256'] == digest(stage/'protocol.json')
    pins[rel(stage/(phase+'_launch.json'))] = digest(stage/(phase+'_launch.json'))


def copy(source, target, pins):
    shutil.copyfile(source, target)
    assert digest(source) == digest(target)
    pins[rel(target)] = digest(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('nodal','render'))
    mode = parser.parse_args().mode
    pins = {}; terminal(REGION, 'measure', pins)
    geometry = REGION/'measurement_001/regions_measurements.json'
    g = read(geometry); assert g['status'] == 'pass'
    pins[rel(geometry)] = digest(geometry)
    result = read(MECH/'result/result.json'); count = len(result['states'])
    reference = read(MECH/'reference/summary.json')
    assert result['status'] == 'success' and reference['status'] == 'pass'
    assert reference['result_sha256'] == digest(MECH/'result/result.json')
    assert reference['accepted_states'] == count and reference['HP_calls_completed'] == 2*count
    proof = ROOT/'functional_views/native_workpiece_nodal_20261004/square009_001'
    old_sources = read(proof/'source_freeze.json')
    stage = NODE if mode == 'nodal' else CARD
    assert not stage.exists(); stage.mkdir()
    copy(MECH/'launch_cycle010.py', stage/'launch_phase.py', pins)
    copy(Path(__file__), stage/'build_saved_cards.py', pins)
    (stage/'sources').mkdir()
    if mode == 'nodal':
        terminal(proof, 'tests', pins)
        assert read(proof/'tests_receipt.json')['status'] == 'pass'
        for name in ('tests_receipt.json','junit.xml','source_freeze.json'):
            pins[rel(proof/name)] = digest(proof/name)
        sources = ['hf_repo/src/hf_eval/__init__.py','hf_repo/src/hf_eval/workpiece_nodal.py',
                   'hf_repo/src/hf_eval/boundary_geometry.py','hf_repo/scripts/observe_workpiece_nodal_forces.py',
                   'hf_repo/scripts/measure_native_workpiece_regions.py']
        for n in sources:
            assert digest(ROOT/n) == old_sources[n]['sha256']
            pins[n] = digest(ROOT/n); copy(ROOT/n, stage/'sources'/Path(n).name, pins)
        phases = dict(observe=dict(helper_seconds=120, outer_seconds=150, argv=[
            sources[3], '--repo','hf_repo','--input',rel(MECH/'result'),
            '--reference',rel(MECH/'reference/summary.json'),'--output',rel(stage/'observation_001'),
            '--time-limit','120','--stop-file',rel(stage/'stop_requested.txt')]))
        extra = dict(expected_observations=count,body_nodes_per_state=len(result['workpiece']['nodes']),
            expected_csv_rows=count*len(result['workpiece']['nodes']),
            original5tests='Reuse true passing source-bound evidence; no new pytest')
    else:
        terminal(NODE,'observe',pins)
        observation = read(NODE/'observation_001/summary.json')
        assert observation['status'] == 'pass' and observation['observations_completed'] == count
        for name in ('summary.json','nodes.csv'):
            pins[rel(NODE/'observation_001'/name)] = digest(NODE/'observation_001'/name)
        for name in ('plot_workpiece_cycle010.py','animate_saved_path.py','plot_saved_J_Hu.py','plot_saved_regions.py'):
            compile((AUTHOR/name).read_bytes(),str(AUTHOR/name),'exec')
            copy(AUTHOR/name,VIEW/name,pins); copy(VIEW/name,stage/'sources'/name,pins)
        old_view = ROOT/'functional_views/native_workpiece_cycle009_20261004/saved_render_001'
        copy(old_view/'render_saved_once.py',stage/'render_saved_once.py',pins)
        copy(stage/'render_saved_once.py',stage/'sources/render_saved_once.py',pins)
        renderer = ROOT/'functional_views/native_workpiece_nodal_20261004/square009_view002/plot_saved_nodal_forces002.py'
        assert digest(renderer) == '778c08625353bfcb0273d17c134db8e90c6eb6a8302a551acdae43477c1c2edc'
        copy(renderer,stage/'plot_saved_nodal_forces002.py',pins)
        copy(renderer,stage/'sources/plot_saved_nodal_forces002.py',pins)
        helper = ROOT/'functional_views/native_workpiece_cycle_20261004/plot_workpiece_cycle.py'
        assert digest(helper) == 'd256fe2b1541505cd5315f45c4a50462670a09436ceb91ecc8d01bbb25554169'
        pins[rel(helper)] = digest(helper)
        programs = [[rel(VIEW/'plot_workpiece_cycle010.py'),'--stage',rel(MECH),'--output',rel(stage/'physical_001'),'--protocol',rel(stage/'protocol.json')],
                    [rel(VIEW/'animate_saved_path.py'),'--stage',rel(MECH),'--output',rel(stage/'animation_001')],
                    [rel(VIEW/'plot_saved_J_Hu.py'),'--stage',rel(MECH),'--output',rel(stage/'fields_001'),'--protocol',rel(stage/'protocol.json')]]
        phases = dict(render=dict(helper_seconds=120,outer_seconds=150,argv=[rel(stage/'render_saved_once.py')]),
                      node_render=dict(helper_seconds=120,outer_seconds=150,argv=[rel(stage/'plot_saved_nodal_forces002.py'),
                          '--repo','hf_repo','--input',rel(NODE/'observation_001'),'--source',rel(MECH/'result'),
                          '--reference',rel(MECH/'reference/summary.json'),'--output',rel(stage/'nodes_001'),
                          '--time-limit','120','--stop-file',rel(stage/'stop_requested.txt')]),
                      geometry_render=dict(helper_seconds=120,outer_seconds=150,argv=[rel(VIEW/'plot_saved_regions.py'),
                          '--stage',rel(MECH),'--measurements',rel(geometry),'--output',rel(stage/'geometry_001'),
                          '--protocol',rel(stage/'protocol.json')]))
        extra = dict(render_programs=programs,actual_accepted_frames=count,deformation_scale=1,
            sequential='Actual render pass before node_render before geometry_render; first error closes whole card')
    pins[rel(stage/'launch_phase.py')] = digest(stage/'launch_phase.py')
    write(stage/'protocol.json',dict(schema_version='saved-cycle010-'+mode+'-card-1.0',
        bindings=pins,phases=phases,sampled_RSS_bytes=8*1024**3,
        original_targets_mm=result['targets_mm'],actual_accepted_states=count,
        count_basis='Pinned pure saved-data sources/import closure; no mechanical hooks monitored',
        scope='All actual states; new mechanics/HP0; no pressure/clamp/energy/momentHP/face allocation or geometry replay by plotters',
        stop_policy='Each phase once; first failure closes card, no repair/retry/force/extension',**extra))
    print(json.dumps(dict(status='prepared_not_executed',mode=mode,actual_states=count,bindings=len(pins),
        protocol_sha256=digest(stage/'protocol.json'))))


if __name__ == '__main__':
    main()
