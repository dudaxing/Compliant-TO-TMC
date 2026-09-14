"""Preserve and package HF-2 evidence without rerunning mechanics."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'hf_repo'
DATA = ROOT / 'geometry_dataset'
RESULTS = ROOT / 'hf2_results'
RECORDS = REPO / 'validation/hf2/records'
WHEEL = REPO / 'dist/independent_hf_evaluator-0.2.0-py3-none-any.whl'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def verify(snapshot=True):
    receipt = read(RESULTS / 'detached_receipt.json')
    acceptance = read(RESULTS / 'detached/acceptance.json')
    decision = read(RESULTS / 'cshape_final_decision.json')
    assert decision['hf2_stage_status'] == 'partially_complete'
    assert decision['strict_independent_benchmark_status'] == 'not_pass'
    assert decision['source_path_agreement_status'] == 'pass'
    assert decision['common_original_targets'] == 100
    failures = decision['independent_equilibrium_failures']
    assert [(r['side'], r['target_index']) for r in failures] == [('python', 73), ('matlab', 76), ('matlab', 99)]
    assert all(float(r['independent_decimal50_relative_free_residual']) > r['tolerance'] == 1e-8 for r in failures)
    for record in decision['evidence']:
        assert digest(ROOT / record['path']) == record['sha256'], record['path']
    assert acceptance['status'] == 'pass' and len(acceptance['checks']) == 17
    assert all(acceptance['checks'].values())
    assert acceptance['installed_record_files_checked'] == 4511
    assert acceptance['small_checks'] == 976 and acceptance['small_cases'] == 16
    assert receipt['returncode'] == 0 and receipt['dataset_files_unchanged']
    assert digest(WHEEL) == receipt['wheel_sha256'] == 'd2a5840709cb11d4c4371861631c2a7be8faf4b7133861930d255aa89a446c4c'

    code_hash = hashlib.sha256()
    code_files = sorted((REPO / 'src/hf_eval').glob('*.py'))
    with zipfile.ZipFile(WHEEL) as archive:
        assert archive.testzip() is None
        names = {n for n in archive.namelist() if n.startswith('hf_eval/') and n.endswith('.py')}
        assert names == {p.relative_to(REPO / 'src').as_posix() for p in code_files}
        for path in code_files:
            assert archive.read(path.relative_to(REPO / 'src').as_posix()) == path.read_bytes()
            code_hash.update(path.name.encode('utf-8'))
            code_hash.update(b'\0')
            code_hash.update(path.read_bytes())
    assert len(code_files) == 10
    assert code_hash.hexdigest() == acceptance['source_sha256'] == read(RESULTS / 'cshape_python_001/result.json')['source_code_sha256']

    original_files = read(ROOT / 'reference_inputs/manifest.json')
    for record in original_files:
        assert digest(Path(record['original_path_record_only'])) == record['sha256'], record['file']
        assert digest(ROOT / 'reference_inputs' / record['file']) == record['sha256']
    matlab_source = read(ROOT / 'reference_validation/matlab/source_manifest.json')
    with zipfile.ZipFile(ROOT / 'reference_inputs/tmc_source.zip') as archive:
        for record in matlab_source['files']:
            path = ROOT / 'reference_validation/matlab' / record['local_path']
            assert digest(path) == record['sha256']
            assert archive.read(record['original_member']) == path.read_bytes()

    manifest = read(DATA / 'file_manifest.json')
    expected = {r['path'] for r in manifest['files']} | {'file_manifest.json'}
    actual = {p.relative_to(DATA).as_posix() for p in DATA.rglob('*') if p.is_file()}
    assert expected == actual and len(actual) == 395
    for record in manifest['files']:
        assert (DATA / record['path']).stat().st_size == record['bytes']
        assert digest(DATA / record['path']) == record['sha256'], record['path']
    initial = read(ROOT / 'hf1_results/detached_location.json')['dataset_hashes_before']
    assert len(initial) == 395 and all(digest(DATA / name) == value for name, value in initial.items())
    hf1 = read(ROOT / 'deliverables/HF1_release_manifest.json')
    assert digest(ROOT / 'deliverables' / hf1['file']) == hf1['sha256']
    assert digest(REPO / 'dist/independent_hf_evaluator-0.1.0-py3-none-any.whl') == hf1['wheel_sha256']

    comparison = read(RESULTS / 'cshape_comparison_001/summary.json')
    inputs = {
        'python_path_sha256': RESULTS / 'cshape_python_001/cshape_path.npz',
        'python_model_sha256': RESULTS / 'cshape_python_001/model.npz',
        'python_result_sha256': RESULTS / 'cshape_python_001/result.json',
        'matlab_path_sha256': ROOT / 'reference_validation/matlab/cshape_001/cshape_path.npz',
        'matlab_result_sha256': ROOT / 'reference_validation/matlab/cshape_001/cshape_path.json',
    }
    for key, path in inputs.items():
        assert digest(path) == comparison['inputs'][key], key
    for name, sha in read(RESULTS / 'residual_sensitivity_001/summary.json')['inputs_sha256'].items():
        assert digest(ROOT / name.replace('\\', '/')) == sha, name

    junit = ET.parse(RESULTS / 'full_regression.xml').getroot()
    suites = [junit] if junit.tag == 'testsuite' else list(junit.iter('testsuite'))
    counts = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
    assert counts == dict(tests=186, failures=0, errors=0, skipped=1), counts
    jobs = [read(p) for p in sorted((RESULTS / 'resource_jobs').glob('*.json'))]
    elapsed = sum(r.get('wall_seconds', 0) for r in jobs)
    assert len(jobs) == 17 and abs(elapsed - 363.52922060017187) < 1e-6
    assert elapsed < 3600 and not any(r['status'] == 'running' for r in jobs)

    documents = list((REPO / 'docs').glob('*.md')) + [REPO / 'README.md', ROOT / 'EVIDENCE_README.md']
    documents += list((ROOT / 'docs').glob('HF2*.md')) + [ROOT / 'docs/HF3_PLAN.md']
    link_count = 0
    for doc in documents:
        for raw in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            target = raw.strip('<>').split('#', 1)[0]
            if target and '://' not in target:
                assert (doc.parent / target).resolve().exists(), (doc, target)
                link_count += 1

    result = {
        'status': 'pass', 'scope': 'Release integrity only; no new numerical solve or changed scientific verdict',
        'hf2_stage_status': 'partially_complete', 'strict_equilibrium_failures': failures,
        'source_path_agreement_status': 'pass', 'wheel_sha256': digest(WHEEL),
        'runtime_source_sha256': code_hash.hexdigest(),
        'current_source_equals_wheel_equals_full_run_equals_detached': True,
        'runtime_python_files': [p.relative_to(REPO / 'src').as_posix() for p in code_files],
        'original_and_copy_files_unchanged': len(original_files),
        'uploaded_matlab_source_files_byte_identical': len(matlab_source['files']),
        'dataset_files': 395, 'dataset_manifest_sha256': digest(DATA / 'file_manifest.json'),
        'dataset_unchanged_since_HF1': True, 'HF1_archive_and_wheel_unchanged': True,
        'full_path_and_diagnostic_input_hashes_match': True, 'junit': counts,
        'detached_checks_passed': 17, 'installed_RECORD_hashes_passed': 4511,
        'third_party_archive_hashes_reverified_in_offline_replay': False,
        'numerical_jobs': len(jobs), 'numerical_wall_seconds': elapsed, 'total_budget_seconds': 3600,
        'markdown_local_targets_checked': link_count,
        'documentation_note': 'Final explanatory docs and evidence snapshots postdate numerical runs; all 10 runtime files remain byte-identical to the accepted wheel.'
    }
    if snapshot:
        copies = {
            'full_regression.xml': RESULTS / 'full_regression.xml',
            'environment_probe.json': RESULTS / 'environment_probe.json',
            'small_validation_summary.json': RESULTS / 'small_validation_001/summary.json',
            'cshape_final_decision.json': RESULTS / 'cshape_final_decision.json',
            'residual_sensitivity_summary.json': RESULTS / 'residual_sensitivity_001/summary.json',
            'detached_acceptance.json': RESULTS / 'detached/acceptance.json',
            'detached_receipt.json': RESULTS / 'detached_receipt.json',
        }
        RECORDS.mkdir(parents=True, exist_ok=True)
        for name, path in copies.items():
            shutil.copy2(path, RECORDS / name)
        write(RECORDS / 'record_index.json', [{'record': n, 'original_workspace_path': p.relative_to(ROOT).as_posix(), 'sha256': digest(p)} for n, p in copies.items()])
        write(RECORDS / 'release_integrity.json', result)
        write(RESULTS / 'release_integrity.json', result)
    return result


def package():
    integrity = verify(snapshot=False)
    assert integrity == read(RECORDS / 'release_integrity.json')
    git = lambda *args: subprocess.check_output(['git', '-C', str(REPO), *args])
    assert not git('status', '--porcelain').strip(), 'Commit the HF repository before packaging'
    revision = git('rev-parse', 'HEAD').decode().strip()
    members = {}

    def add(path):
        if path.is_file() and '__pycache__' not in path.parts:
            assert path.suffix.lower() not in {'.m', '.mat', '.zip', '.pdf', '.pyc'}
            members[path.relative_to(ROOT).as_posix()] = path

    for entry in git('ls-files', '-s', '-z').decode('utf-8').split('\0'):
        if not entry:
            continue
        info, name = entry.split('\t', 1)
        path = REPO / name
        content = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        assert blob == info.split()[1], ('Git byte mismatch', name)
        add(path)
    add(WHEEL)
    for folder in (DATA, ROOT / 'docs', RESULTS / 'small_validation_001', RESULTS / 'cshape_comparison_001',
                   RESULTS / 'residual_sensitivity_001', RESULTS / 'detached', RESULTS / 'resource_jobs'):
        for path in sorted(folder.rglob('*')):
            add(path)
    for path in (RESULTS / 'cshape_python_001').iterdir():
        # One combined all-target array archive replaces duplicate individual checkpoints.
        if not path.name.startswith('step_'):
            add(path)
    for name in ('full_regression.xml', 'environment_probe.json', 'cshape_final_decision.json',
                 'cshape_comparison_report.md', 'small_validation_report.md', 'detached_receipt.json',
                 'cshape_final_decision_initial.json', 'provenance_reconciliation.json',
                 'detached_install.log', 'detached_install_offline.log', 'detached_failed_001_receipt.json',
                 'run_budgeted.py', 'release_integrity.json'):
        add(RESULTS / name)
    for name in ('cshape_path.npz', 'cshape_path.json', 'path_index_matlab.json', 'process_record.json', 'console.log'):
        add(ROOT / 'reference_validation/matlab/cshape_001' / name)
    for name in ('reference_summary.json', 'source_manifest.json', 'source_archive_integrity_final.json'):
        add(ROOT / 'reference_validation/matlab' / name)
    add(ROOT / 'EVIDENCE_README.md')
    metadata = {
        'stage': 'HF-2', 'stage_status': 'partially_complete',
        'source_path_agreement': 'pass', 'strict_independent_equilibrium': 'not_pass', 'failed_states': 3,
        'git_commit': revision, 'wheel_sha256': digest(WHEEL), 'runtime_source_sha256': integrity['runtime_source_sha256'],
        'entry': 'EVIDENCE_README.md', 'HF3_executed': False,
        'scope': 'Source-numeric uploaded Cshape code agreement only; physical contact accuracy remains unvalidated',
        'omissions': 'No original archives, PDFs, MATLAB code/MAT drivers, LF code/exporters, virtual environments or duplicate step checkpoints. Historical audit source paths are records only.'
    }
    payloads = {'RELEASE.json': json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')}
    file_records = [{'path': name, 'bytes': path.stat().st_size, 'sha256': digest(path)} for name, path in sorted(members.items())]
    file_records += [{'path': name, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()} for name, content in payloads.items()]
    payloads['PACKAGE_FILES.json'] = json.dumps({'self_excluded': 'PACKAGE_FILES.json', 'files': file_records}, ensure_ascii=False, indent=2).encode('utf-8')
    output = ROOT / 'deliverables/HF2_independent_evaluator_and_evidence.zip'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(members.items()):
            archive.write(path, name)
        for name, content in payloads.items():
            archive.writestr(name, content)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        for record in file_records:
            content = archive.read(record['path'])
            assert len(content) == record['bytes'] and hashlib.sha256(content).hexdigest() == record['sha256']
        assert len([n for n in archive.namelist() if n.startswith('geometry_dataset/')]) == 395
        member_count = len(archive.namelist())
    release = dict(metadata, file=output.name, bytes=output.stat().st_size, sha256=digest(output),
                   members=member_count, archive_crc_and_each_member_hash='pass',
                   all_tracked_working_files_match_git_blob_bytes=True, dataset_files=395,
                   original_and_HF1_inputs_unchanged=True)
    write(ROOT / 'deliverables/HF2_release_manifest.json', release)
    return release


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('verify', 'package'))
    action = parser.parse_args().action
    print(json.dumps(verify() if action == 'verify' else package(), ensure_ascii=False, indent=2))
