"""Verify and package the authorized HF-1 release; no mechanics rerun."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / 'hf_repo'
DATA = ROOT / 'geometry_dataset'
EVIDENCE = REPO / 'validation/hf1'
WHEEL = REPO / 'dist/independent_hf_evaluator-0.1.0-py3-none-any.whl'

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def verify():
    checked = []
    receipt = read(ROOT / 'hf1_results/detached_receipt.json')
    assert digest(WHEEL) == receipt['wheel_sha256']
    with zipfile.ZipFile(WHEEL) as archive:
        wheel_sources = {name for name in archive.namelist() if name.startswith('hf_eval/') and name.endswith('.py')}
        repo_sources = {p.relative_to(REPO / 'src').as_posix() for p in (REPO / 'src/hf_eval').rglob('*.py')}
        assert wheel_sources == repo_sources
        for name in sorted(repo_sources):
            assert archive.read(name) == (REPO / 'src' / name).read_bytes(), name
            checked.append(name)

    references = read(ROOT / 'reference_inputs/manifest.json')
    for record in references:
        assert digest(Path(record['original_path_record_only'])) == record['sha256'], record['file']
        assert digest(ROOT / 'reference_inputs' / record['file']) == record['sha256'], record['file']

    manifest = read(DATA / 'file_manifest.json')
    files = manifest['files']
    assert len(files) == manifest['file_count'] == 394
    expected = {r['path'] for r in files} | {'file_manifest.json'}
    actual = {p.relative_to(DATA).as_posix() for p in DATA.rglob('*') if p.is_file()}
    assert actual == expected
    for record in files:
        path = DATA / record['path']
        assert path.stat().st_size == record['bytes'] and digest(path) == record['sha256'], record['path']
    forbidden_extensions = {'.py', '.pyc', '.m', '.exe', '.dll', '.bat', '.ps1', '.zip'}
    assert not [p for p in DATA.rglob('*') if p.is_file() and p.suffix.lower() in forbidden_extensions]
    initial = read(ROOT / 'hf1_results/detached_location.json')['dataset_hashes_before']
    assert all(digest(DATA / name) == value for name, value in initial.items())
    assert len(initial) == 395

    acceptance = read(ROOT / 'hf1_results/detached/acceptance.json')
    assert len(acceptance['checks']) == 12 and all(acceptance['checks'].values())
    assert receipt['dataset_files_unchanged']
    junit = ET.parse(ROOT / 'hf1_results/pytest.xml').getroot()
    suites = [junit] if junit.tag == 'testsuite' else list(junit.iter('testsuite'))
    counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ['tests', 'failures', 'errors', 'skipped']}
    assert counts == {'tests': 89, 'failures': 0, 'errors': 0, 'skipped': 1}, counts

    # Only check the new argument guard. The successful audited run used explicit forbid paths.
    command = [str(REPO / '.venv/Scripts/python.exe'), str(REPO / 'scripts/run_isolated.py'),
               '--dataset', str(DATA), '--output', str(ROOT / 'hf1_results/must_not_be_created')]
    assert not (ROOT / 'hf1_results/must_not_be_created').exists()
    rejected = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert rejected.returncode == 2 and '--forbid' in rejected.stderr
    assert not (ROOT / 'hf1_results/must_not_be_created').exists()
    empty_rejected = subprocess.run(command + ['--forbid', ''], capture_output=True, text=True, timeout=30)
    assert empty_rejected.returncode == 2 and 'nonempty' in empty_rejected.stderr
    assert not (ROOT / 'hf1_results/must_not_be_created').exists()

    cli = []
    for case in ('inverter', 'gripper'):
        output = subprocess.run([str(REPO / '.venv/Scripts/python.exe'), '-I', '-m', 'hf_eval', 'inspect',
                                 str(DATA / f'canonical/{case}/geometry.json')], cwd=ROOT / 'hf1_results',
                                capture_output=True, text=True, encoding='utf-8', timeout=30)
        assert output.returncode == 0, output.stderr
        inspection = json.loads(output.stdout)
        assert inspection['readability']['status'] == 'pass'
        cli.append({'case': case, 'geometry_id': inspection['geometry_id'], 'readability': 'pass'})

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'hf1_results/detached', EVIDENCE / 'detached', dirs_exist_ok=True)
    for name in ('pytest.xml', 'detached_receipt.json'):
        shutil.copy2(ROOT / 'hf1_results' / name, EVIDENCE / name)

    # Check Markdown artifact targets in final stage documents and the portable repo.
    documents = list((REPO / 'docs').glob('*.md')) + [REPO / 'README.md', ROOT / 'README.md',
                ROOT / 'docs/HF1_REPORT.md', ROOT / 'docs/HF1_PLAN.md', ROOT / 'docs/HF2_PLAN.md']
    targets = 0
    for document in documents:
        for raw in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            target = raw.strip('<>').split('#', 1)[0]
            if not target or '://' in target:
                continue
            assert (document.parent / target).resolve().exists(), (document, target)
            targets += 1

    result = {
        'status': 'pass', 'scope': 'HF-1 final release integrity; no new mechanics or HF-2 computation',
        'wheel_sha256': digest(WHEEL), 'wheel_source_files_match': checked,
        'original_and_reference_copy_hashes_match': len(references),
        'dataset_manifest_files': len(files), 'dataset_total_files': len(actual),
        'dataset_manifest_bytes_excluding_self': sum(r['bytes'] for r in files),
        'dataset_manifest_sha256': digest(DATA / 'file_manifest.json'),
        'dataset_unchanged_since_detached_acceptance': True,
        'dataset_no_source_or_executable_files': True,
        'junit_counts': counts, 'detached_checks': acceptance['checks'],
        'mandatory_forbid_argument_missing_and_empty_rejected': True,
        'final_installed_wheel_cli_inspections': cli, 'markdown_local_targets_checked': targets,
        'documentation_note': 'Final docs and mandatory-forbid helper guard were added after the accepted numerical run; runtime package bytes match its wheel.'
    }
    write(EVIDENCE / 'release_integrity.json', result)
    write(ROOT / 'hf1_results/release_integrity.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))

def package():
    integrity = read(EVIDENCE / 'release_integrity.json')
    assert integrity['status'] == 'pass'
    git = lambda *args: subprocess.check_output(['git', '-C', str(REPO), *args])
    assert not git('status', '--porcelain').strip(), 'Commit all HF release changes before packaging'
    revision = git('rev-parse', 'HEAD').decode().strip()
    tracked = [p for p in git('ls-files', '-z').decode('utf-8').split('\0') if p]
    for entry in git('ls-files', '-s', '-z').decode('utf-8').split('\0'):
        if not entry:
            continue
        info, name = entry.split('\t', 1)
        data_bytes = (REPO / name).read_bytes()
        git_blob = hashlib.sha1(b'blob ' + str(len(data_bytes)).encode() + b'\0' + data_bytes).hexdigest()
        assert git_blob == info.split()[1], ('Git byte mismatch', name)
    output = ROOT / 'deliverables'
    output.mkdir(exist_ok=True)
    package_path = output / 'HF1_independent_evaluator_and_dataset.zip'
    with zipfile.ZipFile(package_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(tracked):
            archive.write(REPO / name, 'hf_repo/' + name)
        archive.write(WHEEL, 'hf_repo/dist/' + WHEEL.name)
        for path in sorted(DATA.rglob('*')):
            if path.is_file():
                archive.write(path, 'geometry_dataset/' + path.relative_to(DATA).as_posix())
        archive.writestr('RELEASE.json', json.dumps({
            'stage': 'HF-1', 'git_commit': revision, 'wheel_sha256': digest(WHEEL),
            'entry': 'hf_repo/README.md', 'data_entry': 'geometry_dataset/dataset_index.json',
            'scope': 'Independent data interface and solid-only linear diagnostic; HF-2 not executed'
        }, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(package_path) as archive:
        assert archive.testzip() is None
        assert len([n for n in archive.namelist() if n.startswith('geometry_dataset/')]) == 395
        assert archive.read('hf_repo/dist/' + WHEEL.name) == WHEEL.read_bytes()
        members = len(archive.namelist())
    release = {'file': package_path.name, 'bytes': package_path.stat().st_size,
               'sha256': digest(package_path), 'members': members, 'git_commit': revision,
               'wheel_sha256': digest(WHEEL), 'archive_crc_check': 'pass',
               'source_files': len(tracked), 'dataset_files': 395,
               'all_tracked_working_files_match_git_blob_bytes': True,
               'no_environments_or_original_source_archives_included': True}
    write(output / 'HF1_release_manifest.json', release)
    print(json.dumps(release, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['verify', 'package'])
    args = parser.parse_args()
    (verify if args.action == 'verify' else package)()
