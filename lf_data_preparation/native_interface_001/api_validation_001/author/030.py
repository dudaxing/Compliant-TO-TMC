"""Install a reviewed native interface and freeze one saved-only functional card."""
from hashlib import sha256
from pathlib import Path
import argparse
import ast
import json
import subprocess

HEAD = 'bbb73e74c9eacd6cd326f08379dcf79a665449e2'
STAGE = 'lf_data_preparation/native_interface_001/api_validation_001'
BASELINE_PROTOCOL = 'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/production_protocol.json'
LAUNCHER = 'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001/launch_pose.py'
OLD_CLI = 'd457783d3818f3f4c5fe2ce558df9cd9a14245880198aaa6907e7b3541d54888'
PRODUCTS = {
    'native_evaluate.py': 'hf_repo/src/hf_eval/native_evaluate.py',
    'response_candidate/native_response.py': 'hf_repo/src/hf_eval/native_response.py',
    'evaluate_native_cli.py': 'hf_repo/scripts/evaluate_native.py',
    'summarize_native_mean_cli.py': 'hf_repo/scripts/summarize_native_mean.py',
    'solve_native_mean.py': 'hf_repo/scripts/solve_native_mean.py'}
TESTS = ['test_native_evaluate_interface.py', 'test_native_saved_response.py']
sha = lambda data:sha256(data).hexdigest()
read = lambda path:json.loads(path.read_bytes())
dump = lambda value:(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')


def reviewed(path, sources):
    report = read(path)
    assert report['status']=='pass_static_only' and not report['blocking_findings'], path
    for name, expected in sources.items():
        pins = {pin for source, pin in report['source_sha256'].items() if Path(source).name==Path(name).name}
        assert pins=={expected}, name
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--tests-review', type=Path, required=True, help='Actual final worker/tests/fixture peer review')
    args = parser.parse_args();root = args.repo.resolve();author = Path(__file__).resolve().parent
    assert not author.is_relative_to(root)
    current = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'], text=True).strip()
    branch = subprocess.check_output(['git','-C',str(root),'branch','--show-current'], text=True).strip()
    assert current==HEAD and branch=='main'
    stage = root/STAGE;assert not stage.exists()
    old_cli = (root/'hf_repo/scripts/solve_native_mean.py').read_bytes()
    assert sha(old_cli)==OLD_CLI and (author/'solve_native_mean_before.py').read_bytes()==old_cli
    raw_products = {name:(author/name).read_bytes() for name in PRODUCTS}
    for name, destination in PRODUCTS.items():
        if destination!='hf_repo/scripts/solve_native_mean.py':assert not (root/destination).exists()
        compile(ast.parse(raw_products[name].decode('utf-8')), name, 'exec')
    test_root = author/'tests_candidate'
    raw_tests = {name:(test_root/name).read_bytes() for name in TESTS}
    worker_name, fixture_name = 'execute_interface_tests.py', 'test_fixture_inventory.json'
    worker, fixture_bytes = (test_root/worker_name).read_bytes(),(test_root/fixture_name).read_bytes()
    fixture = json.loads(fixture_bytes)
    assert fixture['schema_version']=='native-interface-functional-fixtures-1.0'
    assert set(fixture['fixtures'])=={'right2col','right4col','no_workpiece','failed_prefix','short_path'}
    assert fixture['expected_exports']==4
    compile(ast.parse(worker.decode('utf-8')), worker_name, 'exec')
    for name, raw in raw_tests.items():compile(ast.parse(raw.decode('utf-8')), name, 'exec')
    evaluate_review = author/'review_notes/evaluate_draft_static_review.json'
    response_review = author/'review_notes/response_static_review.json'
    tests_review = args.tests_review.resolve()
    reviewed(evaluate_review, {name:sha(raw) for name,raw in raw_products.items() if name!='response_candidate/native_response.py'})
    reviewed(response_review, {'native_response.py':sha(raw_products['response_candidate/native_response.py'])})
    reviewed(tests_review, {**{name:sha(raw) for name,raw in raw_tests.items()},
        worker_name:sha(worker),fixture_name:sha(fixture_bytes)})
    baseline = read(root/BASELINE_PROTOCOL)
    core = {name:pin for name,pin in baseline['bindings'].items() if name.startswith('hf_repo/src/')}
    assert len(core)==25 and all(sha((root/name).read_bytes())==pin for name,pin in core.items())
    inputs = {}
    for key in ('json_bindings','declared_image_bindings','reference_source_bindings'):
        for name,pin in fixture[key].items():
            suffix=Path(name).suffix.lower()
            assert suffix=='.json' if key=='json_bindings' else suffix in {'.png','.gif'} if key=='declared_image_bindings' else suffix=='.py'
            assert sha((root/name).read_bytes())==pin, name
            if name in inputs:assert inputs[name]==pin
            inputs[name]=pin
    launcher = (root/LAUNCHER).read_bytes()
    assert sha(launcher)=='f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477'
    # All gates above are file/source checks. No import, pytest, constructor or scientific entry.
    author_names = [
        'response_candidate/author_note.json','response_candidate/author_checks.json',
        'response_candidate/README.md','response_candidate/source_additions.diff',
        'response_candidate/column_scope_delta.diff','tests_candidate/VERIFICATION_PLAN.md']
    archive = {'001.py':old_cli,'002.json':evaluate_review.read_bytes(),
               '003.json':response_review.read_bytes(),'004.json':tests_review.read_bytes()}
    source_names = {'001.py':'hf_repo/scripts/solve_native_mean.py before CLI option',
        '002.json':str(evaluate_review),'003.json':str(response_review),'004.json':str(tests_review)}
    for name in author_names:
        short=f'{len(archive)+1:03d}{Path(name).suffix}'
        archive[short]=(author/name).read_bytes();source_names[short]=name
    installer_short=f'{len(archive)+1:03d}.py';archive[installer_short]=Path(__file__).read_bytes();source_names[installer_short]='install_interface_card.py'
    stage.mkdir(parents=True);(stage/'author').mkdir();(stage/'tests').mkdir()
    installed, bindings = {}, dict(core)
    for name,destination in PRODUCTS.items():
        (root/destination).parent.mkdir(parents=True,exist_ok=True)
        (root/destination).write_bytes(raw_products[name])
        installed[destination]=dict(source_name=name,sha256=sha(raw_products[name]),before_sha256=OLD_CLI if destination.endswith('/solve_native_mean.py') else None)
        bindings[destination]=sha(raw_products[name])
    for name,raw in raw_tests.items():
        destination=STAGE+'/tests/'+name;(root/destination).write_bytes(raw);bindings[destination]=sha(raw)
        installed[destination]=dict(source_name='tests_candidate/'+name,sha256=sha(raw),before_sha256=None)
    for name,raw in [(worker_name,worker),(fixture_name,fixture_bytes)]:
        destination=STAGE+'/author/'+name;(root/destination).write_bytes(raw);bindings[destination]=sha(raw)
        installed[destination]=dict(source_name='tests_candidate/'+name,sha256=sha(raw),before_sha256=None)
    (stage/'launch_pose.py').write_bytes(launcher);bindings[STAGE+'/launch_pose.py']=sha(launcher)
    for short,raw in archive.items():
        (stage/'author'/short).write_bytes(raw);bindings[STAGE+'/author/'+short]=sha(raw)
    bindings.update(inputs)
    assert all(sha((root/name).read_bytes())==pin for name,pin in bindings.items())
    protocol = dict(schema_version='native-interface-functional-protocol-1.0',baseline_commit=HEAD,
        bindings=bindings,sampled_RSS_bytes=8*1024**3,
        phases=dict(functional=dict(helper_seconds=120,outer_seconds=150,
            argv=[STAGE+'/author/'+worker_name,'--repo','.', '--protocol',STAGE+'/functional_protocol.json'])),
        fixture_manifest_file=STAGE+'/author/'+fixture_name,tests_directory=STAGE+'/tests',
        output_directory=STAGE+'/run_001',expected_tests=20,expected_exports=4,
        scope='Saved JSON response exports and mocked transport only; no actual HF, NPZ, construction, F/T/solver/HP or geometry/nodal observation',
        mock_call_counts_role='Controlled success/failure test transport; never scientific evaluation counts',
        stop_policy='One functional invocation; first error closes; no retry or force')
    (stage/'functional_protocol.json').write_bytes(dump(protocol))
    receipt = dict(status='installed_functional_card_not_executed',baseline_commit=HEAD,new_scientific_calls=0,
        product_files=installed,original_core_sha256=core,original_cli_before_sha256=OLD_CLI,
        protocol_sha256=sha((stage/'functional_protocol.json').read_bytes()),
        archive={short:dict(source_name=source_names[short],path=STAGE+'/author/'+short,sha256=sha(raw)) for short,raw in archive.items()},
        launcher_sha256=sha(launcher),bindings_count=len(bindings),source_checks_only=True,
        qualification='Installation is not functional test pass or new mechanical/reference/physical qualification')
    (stage/'installation_receipt.json').write_bytes(dump(receipt))
    index='Selected interface sources and reviews; original CLI raw001.py. Current source-only author notes retain their historical roles. No historical model/state/NPZ/HP archive copied. Paths in original source notes are provenance, not runtime dependencies.\n\n'
    index+='\n'.join(f'- [{short}]({short}): {source_names[short]}' for short in archive)+'\n'
    (stage/'author/INDEX.md').write_text(index,encoding='utf-8')
    print(json.dumps(dict(status=receipt['status'],stage=STAGE,bindings=len(bindings))))


if __name__=='__main__':main()
