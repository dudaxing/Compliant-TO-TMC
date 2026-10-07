"""One fail-fast JSON/mock functional phase; no real forward or array reads."""
from time import perf_counter
STARTED = perf_counter()
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


SCIENCE = Counter(model_constructions=0, force_calls=0, tangent_calls=0, solver_calls=0,
                  HP_calls=0, geometry_calls=0, nodal_calls=0, NPZ_reads=0, real_cached_writer_calls=0)
POINTS = {
    'native_project.py': ('model_constructions', {'build_native_project'}),
    'project.py': ('model_constructions', {'build_project'}),
    'native_mean.py': ('solver_calls', {'solve_native_mean'}),
    'split_displacement.py': ('solver_calls', {'solve_split_displacement_path'}),
    'displacement.py': ('solver_calls', {'solve_initial_tangent','solve_displacement_path'}),
    'split_kernel_invariants_hu.py': ('force_calls', {'_response','_numpy_response','batch_response_split_numpy',
        'batch_response_split_mechanical_numpy','assemble_split_numpy','assemble_split_mechanical_numpy','assemble_split'}),
    'split_numpy_tangent.py': ('tangent_calls', {'_tangent','_tangent_chunked','batch_tangent_components_split_numpy',
        'batch_tangent_split_numpy','assemble_tangent_split_numpy','assemble_split_numpy'}),
    'tmc.py': ('force_calls', {'assemble','solve_path'}),
}
NP_LOAD_CODE = None


def forbid(kind, point):
    SCIENCE[kind] += 1
    raise AssertionError(f'Forbidden real scientific activity: {kind} at {point}')


def profile_guard(frame, event, arg):
    if event != 'call':
        return
    code = frame.f_code
    filename = code.co_filename.replace('\\','/')
    name = code.co_name
    if code is NP_LOAD_CODE:
        forbid('NPZ_reads', 'numpy.load')
    if name == '__init__' and type(frame.f_locals.get('self')).__name__ == 'TMCModel':
        forbid('model_constructions', 'TMCModel.__init__')
    if '/reference_author/' in filename or '/hf0_audit/' in filename:
        if name != '<module>':
            forbid('HP_calls', filename + ':' + name)
    if '/hf_eval/' not in filename:
        return
    basename = Path(filename).name
    if basename == 'native_mean.py' and name == 'write_native_mean':
        forbid('real_cached_writer_calls', name)
    if basename in {'native_region_geometry.py','boundary_geometry.py'} and name != '<module>':
        forbid('geometry_calls', name)
    if basename == 'workpiece_nodal.py' and name != '<module>':
        forbid('nodal_calls', name)
    point = POINTS.get(basename)
    if point is not None and name in point[1]:
        forbid(point[0], basename + ':' + name)


def digest(path):
    if path.suffix.lower() == '.npz':
        forbid('NPZ_reads', str(path))
    return sha256(path.read_bytes()).hexdigest()


def main():
    global NP_LOAD_CODE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    protocol_file = (args.protocol if args.protocol.is_absolute() else repo/args.protocol).resolve()
    protocol = json.loads(protocol_file.read_text(encoding='utf-8'))
    output = repo/protocol['output_directory']
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(schema_version='native-interface-functional-execution-1.0', status='not_pass',
        scope='JSON response semantics and mocked integration only; no new forward/HP/contact/pressure/HF5 qualification',
        protocol_sha256=digest(protocol_file), invocations=1, expected_tests=protocol['expected_tests'],
        scientific_calls=dict(SCIENCE), formatter_calls_started=0, formatter_calls_completed=0,
        response_exports={}, started_utc=datetime.now(timezone.utc).isoformat())
    before, peak, failure = {}, 0, None
    old_profile = sys.getprofile()
    process = None

    def check_limits():
        nonlocal peak
        if (protocol_file.parent/'stop_requested.txt').exists():
            raise RuntimeError('Cooperative F3 stop requested')
        if perf_counter()-STARTED > protocol['phases']['functional']['helper_seconds']:
            raise RuntimeError('Whole-helper functional time limit exceeded')
        if process is not None:
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory,'peak_wset',0))
            if peak > protocol['sampled_RSS_bytes']:
                raise RuntimeError('Sampled helper RSS limit exceeded')

    class Limits:
        def pytest_runtest_setup(self, item):
            check_limits()
        def pytest_runtest_teardown(self, item, nextitem):
            check_limits()

    try:
        check_limits()
        before = {name:digest(repo/name) for name in protocol['bindings']}
        assert before == protocol['bindings'], 'Frozen source/fixture bindings differ before import'
        inventory_file = repo/protocol['fixture_manifest_file']
        inventory = json.loads(inventory_file.read_text(encoding='utf-8'))
        assert inventory['expected_tests'] == protocol['expected_tests']
        assert inventory['expected_exports'] == inventory['expected_formatter_calls'] == 4
        (output/'source_preimages.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
        sys.setprofile(profile_guard)
        import psutil
        process = psutil.Process()
        import numpy
        NP_LOAD_CODE = numpy.load.__code__
        os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
        os.environ['HF_INTERFACE_TEST_REPO'] = str(repo)
        sys.path.insert(0,str(repo/'hf_repo/src'))
        import pytest
        from hf_eval.native_response import summarize_saved_native_result, write_native_response
        check_limits()
        tests_dir = repo/protocol['tests_directory']
        junit = output/'test_results.xml'
        code = pytest.main(['-q','-x','--disable-warnings','--junitxml='+str(junit),str(tests_dir)],plugins=[Limits()])
        suites = ET.parse(junit).getroot()
        rows = list(suites) if suites.tag == 'testsuites' else [suites]
        counts = {key:sum(int(row.attrib.get(key,0)) for row in rows) for key in ['tests','errors','failures','skipped']}
        receipt.update(pytest_exit_code=int(code),tests=counts,tests_passed=counts['tests']-counts['errors']-counts['failures']-counts['skipped'],
                       tests_errors=counts['errors'],tests_failed=counts['failures'],tests_skipped=counts['skipped'])
        test_module = sys.modules.get('test_native_evaluate_interface')
        receipt['mock_transport_calls'] = dict(test_module.MOCK_TRANSPORT_COUNTS) if test_module is not None else {}
        receipt['mock_transport_scope'] = 'Stub entry calls (including intentional errors); never real solver/model/cached-array persistence activity'
        assert code == 0 and counts == {'tests':protocol['expected_tests'],'errors':0,'failures':0,'skipped':0}, 'Functional tests did not all pass'
        check_limits()
        for name,pin in inventory['json_bindings'].items():
            assert digest(repo/name) == pin
        for label,fixture in inventory['fixtures'].items():
            if fixture['export_filename'] is None:
                continue
            check_limits()
            receipt['formatter_calls_started'] += 1
            response = summarize_saved_native_result(fixture['result_file'],repo_root=repo,
                reference_file=fixture['reference_file'],view_manifest=fixture['view_manifest_file'])
            saved = write_native_response(response,output/fixture['export_filename'])
            receipt['formatter_calls_completed'] += 1
            assert response['identity']['result']['sha256'] == fixture['result_sha256']
            assert response['status'] == fixture['expected_status']
            assert response['path']['accepted_states'] == fixture['actual_states']
            receipt['response_exports'][label] = dict(file=saved.relative_to(repo).as_posix(),sha256=digest(saved),
                source_result_sha256=fixture['result_sha256'],status=response['status'],actual_states=response['path']['accepted_states'],
                task_target_executed=response['path']['task_target_executed'],
                full_path_reference_pass=response['independent_reference']['full_path_reference_pass'],
                linked_views=len(response['views']['links']))
        assert receipt['formatter_calls_completed'] == inventory['expected_formatter_calls'] == inventory['expected_exports'] == 4
        check_limits()
        assert not any(SCIENCE.values()), 'A scientific guard was triggered'
        after = {name:digest(repo/name) for name in before}
        receipt['all_bindings_unchanged'] = after == before
        assert receipt['all_bindings_unchanged']
        check_limits()
        receipt['status'] = 'pass'
    except BaseException as error:
        failure = dict(exception_class=type(error).__name__,reason=str(error))
    finally:
        sys.setprofile(old_profile)
        receipt.update(failure=failure,scientific_calls=dict(SCIENCE),elapsed_seconds=perf_counter()-STARTED,
                       peak_sampled_RSS_bytes=peak,seconds_limit=protocol['phases']['functional']['helper_seconds'],
                       sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],completed_utc=datetime.now(timezone.utc).isoformat())
        (output/'execution_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:receipt.get(key) for key in ['status','tests_passed','formatter_calls_completed','scientific_calls','elapsed_seconds','failure']},ensure_ascii=False),flush=True)
    return 0 if receipt['status']=='pass' else 1


if __name__=='__main__':
    raise SystemExit(main())
