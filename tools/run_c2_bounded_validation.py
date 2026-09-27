"""Record one bounded validation process; never retry or replace its output."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--category', choices=('p1', 'arithmetic', 'manufactured', 'saved', 'regression'), required=True)
    parser.add_argument('--timeout', type=float, default=900.)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or not 0 < args.timeout <= 900:
        parser.error('explicit command and timeout in (0, 900] required')
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(root):
        parser.error('output must be a new directory inside the candidate worktree')
    used = 0.
    for path in (root / 'hf4_c2_stable_f_validation').glob('*/execution_receipt.json'):
        receipt = json.loads(path.read_text(encoding='utf-8'))
        used += receipt['elapsed_seconds']
    scientific = args.category != 'p1'
    if scientific and used >= 3600:
        parser.error('initial 3600-second validation budget exhausted')
    seconds = min(args.timeout, 3600-used) if scientific else args.timeout
    environment = dict(os.environ)
    environment.update(JAX_ENABLE_X64='true', JAX_PLATFORMS='cpu', OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', MPLBACKEND='Agg',
        PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        PYTHONPATH=os.pathsep.join((str(root/'hf_repo/src'), str(root/'hf_repo/scripts'))))
    sources = {}
    for directory in ('hf_repo/src', 'hf_repo/scripts', 'hf_repo/tests'):
        for path in (root/directory).rglob('*.py'):
            sources[path.relative_to(root).as_posix()] = sha(path)
    output.mkdir(parents=True, exist_ok=False)
    baseline = json.loads(subprocess.check_output(['git', 'show',
        '7fea2e44b67d0eff421219ebbcac68c506fb9d2f:handoff/repository_manifest.json'], cwd=root))
    old_hashes = {row['path']:row['sha256'] for row in baseline['files']}
    snapshot = []
    for name, digest in sources.items():
        if old_hashes.get(name) != digest:
            target = output/'source_snapshot'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root/name, target)
            if sha(target) != digest:
                raise RuntimeError('source changed while freezing: '+name)
            snapshot.append(name)
    plan = dict(schema='c2-bounded-validation-process-v1', category=args.category,
        command=command, cwd=str(root), timeout_seconds=seconds, earlier_validation_seconds=used,
        source_snapshot_paths=snapshot, original_source_baseline='7fea2e44b67d0eff421219ebbcac68c506fb9d2f',
        initial_total_validation_budget_seconds=3600, source_sha256=sources,
        python=platform.python_version(), platform=platform.platform(),
        environment={key:environment[key] for key in ('JAX_ENABLE_X64','JAX_PLATFORMS','OMP_NUM_THREADS',
            'OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','PYTHONPATH','PYTEST_DISABLE_PLUGIN_AUTOLOAD')},
        scope='No equilibrium path; arithmetic, independent derivative, or mocked launch validation only.',
        created_utc=datetime.now(timezone.utc).isoformat())
    (output/'execution_plan.json').write_text(json.dumps(plan, indent=2)+'\n', encoding='utf-8')
    begin = time.perf_counter()
    timed_out = False
    with (output/'stdout.log').open('xb') as stdout, (output/'stderr.log').open('xb') as stderr:
        process = subprocess.Popen(command, cwd=root, env=environment, stdout=stdout, stderr=stderr)
        try:
            code = process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            else:
                process.kill()
            code = process.wait()
    changed = [name for name, digest in sources.items() if not (root/name).is_file() or sha(root/name) != digest]
    result = dict(schema='c2-bounded-validation-receipt-v1', category=args.category,
        returncode=code, timed_out=timed_out, elapsed_seconds=time.perf_counter()-begin,
        status='pass' if code == 0 and not timed_out and not changed else 'not_pass',
        source_changes_during_run=changed, command=command,
        completed_utc=datetime.now(timezone.utc).isoformat(),
        output_sha256={p.name:sha(p) for p in output.iterdir() if p.is_file()},
        no_equilibrium_path_requested=True)
    (output/'execution_receipt.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('status','returncode','timed_out','elapsed_seconds','source_changes_during_run')}))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
