from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).parent
MECHANICAL = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_008'
VIEW = ROOT/'functional_views/native_workpiece_cycle008_20261004'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()

def write(path, value):
    with path.open('xb') as f:
        f.write((json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode())

def bind(pins, path):
    pins[rel(path)] = sha(path)

def main(mode):
    result = read(MECHANICAL/'result/result.json')
    receipt = read(MECHANICAL/'execution_receipt.json')
    outer = read(MECHANICAL/'production_launch.json')
    assert outer['status'] == receipt['status'] == 'not_pass' and outer['exit_code'] == 1
    assert outer['all_bindings_unchanged'] and receipt['sources_unchanged'] and receipt['inputs_unchanged']
    assert result['status'] == 'failed' and result['failure']['code'] == 'time_limit'
    assert result['loading_peak_reached'] and not result['path_completed'] and not result['unload_endpoint_reached']
    assert len(result['states']) == receipt['accepted_states'] == 8
    assert [row['d'] for row in result['states']] == [0.,.5,1.,1.5,1.75,1.5,1.,.5]
    assert receipt['HP_calls'] == 0 and not (MECHANICAL/'reference_launch.json').exists() and not (MECHANICAL/'reference').exists()
    assert receipt['result_sha256'] == sha(MECHANICAL/'result/result.json')
    unsigned = VIEW/'partial_boundary_saved_001'
    assert read(unsigned/'measure_launch.json')['status'] == read(unsigned/'measurement_receipt.json')['status'] == 'pass'
    pins = {}
    for path in sorted((MECHANICAL/'result').rglob('*')):
        if path.is_file() and path.suffix in ('.json','.npz'): bind(pins,path)
    for name in ['execution_receipt.json','production_launch.json','input_inventory.json',
                 'source_freeze.json','protocol.json']:
        bind(pins,MECHANICAL/name)
    for path in [unsigned/'protocol.json', unsigned/'measure_launch.json', unsigned/'measurement_receipt.json',
                 unsigned/'measurement_001/boundary_measurements.json']:
        bind(pins,path)
    files = ['hf_repo/src/hf_eval/__init__.py','hf_repo/src/hf_eval/boundary_geometry.py',
             'hf_repo/src/hf_eval/native_region_geometry.py','hf_repo/scripts/measure_native_workpiece_regions.py']
    # Existing39 analytic tests belong to the unchanged geometry implementation;
    # they are provenance, not a new test invocation or new-state qualification.
    for name in ['protocol.json','tests_launch.json','tests_001/junit.xml']:
        bind(pins,ROOT/'functional_views/native_region_geometry_20261004/square007_002'/name)
    prior_measure_sources = read(ROOT/'functional_views/native_region_geometry_20261004/square007_002/measurement_001/regions_measurements.json')['sources']
    for role,item in prior_measure_sources.items():
        path = ROOT/'hf_repo'/role
        assert sha(path) == item['sha256']
    stage = VIEW/('partial_region_saved_001' if mode == 'measure' else 'partial_region_view_001')
    assert not stage.exists()
    stage.mkdir(parents=True)
    shutil.copyfile(MECHANICAL/'launch_cycle008.py', stage/'launch_phase.py')
    if mode == 'measure':
        argv = ['hf_repo/scripts/measure_native_workpiece_regions.py','--repo','hf_repo','--input',rel(MECHANICAL/'result'),
            '--output',rel(stage/'measurement_001'),'--boundary-comparison',rel(unsigned/'measurement_001/boundary_measurements.json'),
            '--stop-file',rel(stage/'stop_requested.txt'),'--time-limit','120']
    else:
        region = VIEW/'partial_region_saved_001'
        assert read(region/'measure_launch.json')['status'] == read(region/'measurement_001/regions_measurements.json')['status'] == 'pass'
        physical = VIEW/'partial_saved_001'
        assert read(physical/'render_launch.json')['status'] == 'pass'
        for directory in [region, physical/'render_001']:
            for path in sorted(directory.rglob('*')):
                if path.is_file() and path.suffix in ('.json','.csv','.py'): bind(pins,path)
        shutil.copyfile(AUTHOR/'render_native_region_partial008.py', stage/'render_native_region_partial008.py')
        shutil.copyfile(AUTHOR/'region_partial_view_author_note.json', stage/'author_note.json')
        shutil.copyfile(AUTHOR/'partial_saved_view_cross_review.json', stage/'cross_review.json')
        assert read(stage/'cross_review.json')['status'] == 'pass'
        files = [rel(stage/'render_native_region_partial008.py')]
        argv = [files[0],'--input',rel(region/'measurement_001/regions_measurements.json'),'--result',rel(MECHANICAL/'result'),
            '--saved-view',rel(physical/'render_001/view_metadata.json'),'--output',rel(stage/'render_001'),
            '--stop-file',rel(stage/'stop_requested.txt'),'--time-limit','120']
        bind(pins,stage/'author_note.json'); bind(pins,stage/'cross_review.json')
    files.append(rel(stage/'launch_phase.py'))
    (stage/'sources').mkdir()
    sources = {}
    for name in files:
        path = ROOT/name
        sources[name] = sha(path)
        shutil.copyfile(path,stage/'sources'/path.name)
        bind(pins,path); bind(pins,stage/'sources'/path.name)
    write(stage/'source_freeze.json',dict(schema_version='saved-cycle008-source-freeze-1.0',sources=sources))
    bind(pins,stage/'source_freeze.json')
    protocol = dict(schema_version='saved-cycle008-observation-card-1.0',sampled_RSS_bytes=8*1024**3,bindings=pins,
        phases={mode: dict(argv=argv,helper_seconds=120,outer_seconds=150)},
        actual_accepted_states=len(result['states']),scope='Independent unqualified saved-partial region measurement' if mode=='measure' else 'Pure bound unqualified saved-partial region visualization',
        stop_policy='One invocation; first error closes stage; no repair/retry/force/budget extension; no force/tangent/solver/HP calls')
    write(stage/'protocol.json',protocol)
    print(json.dumps(dict(status='prepared_not_executed',stage=rel(stage),pins=len(pins),actual_accepted_states=len(result['states']),protocol_sha256=sha(stage/'protocol.json'))))

parser = argparse.ArgumentParser(); parser.add_argument('mode',choices=['measure','render'])
main(parser.parse_args().mode)
