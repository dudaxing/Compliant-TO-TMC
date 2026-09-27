"""Verify saved evidence and summarize this recheck; never evaluate mechanics."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify_map(directory, mapping):
    for name, digest in mapping.items():
        path = (directory / name).resolve()
        assert path.is_relative_to(directory.resolve()), name
        assert sha(path) == digest, str(path)


def main():
    target = HERE / 'acceptance_summary.json'
    assert not target.exists(), 'refusing to overwrite a summary'
    phases = ['arithmetic_001', 'manufactured_001', 'saved_001', 'saved_002']
    integration = ROOT / 'hf4_c2_stable_f_validation/independent_saved_20260927_001'
    runs = []
    for folder in [HERE / name for name in phases] + [integration]:
        receipt = read(folder / 'execution_receipt.json')
        verify_map(folder, receipt['output_sha256'])
        assert not receipt['timed_out'] and not receipt['source_changes_during_run']
        result_folder = folder / 'results'
        if result_folder.exists():
            verify_map(result_folder, read(result_folder / 'output_sha256.json'))
        runs.append(dict(path=folder.relative_to(ROOT).as_posix(),
                         receipt_sha256=sha(folder / 'execution_receipt.json'),
                         status=receipt['status'], elapsed_seconds=receipt['elapsed_seconds']))
    fields = [read(p) for p in sorted((HERE / 'manufactured_001/results').glob('*/result.json'))]
    checks = [c for field in fields for direction in field['directions'] for c in direction['checks']]
    selected = []
    for old_file in sorted((HERE / 'saved_002/results').glob('*/result.json')):
        old = read(old_file)
        new_file = integration / 'results' / old_file.parent.name / 'result.json'
        new = read(new_file)
        for key in ('case', 'status', 'force_scale', 'checks', 'original_checks', 'original_state_sha256'):
            assert old[key] == new[key], (old['case'], key)
        assert sha(old_file.parent / 'production.npz') == sha(new_file.parent / 'production.npz')
        selected.append(dict(case=old['case'], checks=len(old['checks']),
                             same_checks_and_output_bytes=True,
                             production_sha256=sha(new_file.parent / 'production.npz')))
    manifest = read(ROOT / 'hf4_c2_p1_validation/tests_002/source_manifest.json')
    for name, record in manifest.items():
        assert sha(ROOT / 'hf_repo' / name) == record['sha256'], name
    tangent_names = ('candidate_total_tangent', 'candidate_material_tangent',
                     'candidate_regularization_tangent', 'residual_only_jvp_vs_independent',
                     'returned_Kv_vs_residual_only_jvp')
    summary = dict(schema='c2-independent-recheck-1', created_utc=datetime.now(timezone.utc).isoformat(),
        overall='partial', p1='pass', arithmetic_tests=28, manufactured_cases=len(fields),
        manufactured_passed=sum(f['status'] == 'pass' for f in fields),
        manufactured_checks=len(checks),
        manufactured_failed_checks=sum(c['status'] != 'pass' for c in checks),
        failed_cases=[f['case'] for f in fields if f['status'] != 'pass'],
        manufactured_tangent_maxima={name:str(max(Decimal(c['value']) for c in checks if c['name']==name))
                                    for name in tangent_names},
        selected_saved_cases=len(selected), selected_saved_passed=len(selected),
        integrated_rerun_same_checks_and_npz=True, selected_comparison=selected,
        runs=runs, total_this_turn_numeric_seconds=sum(row['elapsed_seconds'] for row in runs),
        original_main_commit='7e007ca93a2ea776939c58cdcb1637fbac406cfe',
        frozen_reference_commit='7fea2e44b67d0eff421219ebbcac68c506fb9d2f',
        new_equilibrium_paths=0, mechanical_admission=False,
        historical_failed_path='NOT_PASS, unchanged',
        scope='This turn reruns 33 manufactured cases and 8 unique saved states; the integrated 8 repeat the same states. Main prior 63-state/full-suite records are not newly executed.',
        source_script_sha256=sha(Path(__file__)))
    target.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:summary[k] for k in ('overall','manufactured_passed','manufactured_checks',
          'manufactured_failed_checks','selected_saved_passed','total_this_turn_numeric_seconds')}))


if __name__ == '__main__':
    main()
