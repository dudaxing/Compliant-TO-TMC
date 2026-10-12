"""Freeze ordinary metadata and source pins; no NPZ byte reads or scientific imports."""
from datetime import datetime, timezone
from hashlib import sha256
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/alpha_reference_001'
BASE = '6c17633c59315490b825fdcc289e49f58e27fcef'
read = lambda path: json.loads(path.read_bytes())
sha = lambda path: sha256(path.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASE
    seed = read(HERE / 'input_contract_seed.json')
    old = {row['path']: row for row in read(ROOT / 'handoff/repository_manifest.json')['files']}
    inherited = seed['NPZ_binding_inheritance']
    assert len(inherited) == 10 and {name for name in seed['input_bindings'] if name.endswith('.npz')} == set(inherited)
    for name, pin in seed['input_bindings'].items():
        assert old[name]['sha256'] == pin
        if name in inherited:
            info = inherited[name]
            evidence = read(ROOT / info['pin_source_file'])
            assert sha(ROOT / info['pin_source_file']) == info['pin_source_file_sha256']
            assert evidence[info['source_JSON_member']][info['source_JSON_key']] == pin == info['sha256']
            assert (ROOT / name).stat().st_size == old[name]['bytes']
        else:
            assert sha(ROOT / name) == pin
    for name in ('execute_alpha_reference.py', 'launch_reference.py', 'deliver_preparation.py'):
        ast.parse((HERE / name).read_text(encoding='utf-8'))
    keys = ('reference_sources', 'production_stage', 'production_launch_file', 'production_protocol_file',
        'task_file', 'reference_output', 'expected_accepted_states', 'expected_new_HP_calls', 'targets_mm',
        'original_target_indices', 'grid', 'expected_counts', 'material', 'workpiece', 'production_settings',
        'direction', 'gates', 'phases', 'sampled_RSS_bytes')
    protocol = {key: seed[key] for key in keys}
    bindings = dict(seed['input_bindings'])
    for name in ('execute_alpha_reference.py', 'launch_reference.py', 'M-AREF1_CARD.md'):
        bindings[REL + '/' + name] = sha(HERE / name)
    protocol.update(schema_version='alpha-saved-segment-independent-reference-card-1.0', card='M-AREF1',
        prepared=True, authorized=False, executed=False, prepared_utc=datetime.now(timezone.utc).isoformat(),
        source_baseline_commit=BASE, science_version='0.5.0', production_result_dir='resumed_alpha_half',
        original_targets_mm=seed['original_task_targets_mm'], bindings=dict(sorted(bindings.items())),
        inherited_NPZ_bindings=inherited, array_read_scope=seed['array_read_scope'],
        execution_indices=[13, 14], top_summary_child_indices=[0, 1],
        unchanged_mathematical_methods=['CoreAudit.run_state', 'WorkpieceCycleAudit.workpiece_checks'],
        scatter_precision=3000, scatter_Inexact_trap=True, independent_reference_only=True,
        new_production_F_T_model_solver_tests_plots=0, new_HP_calls=4,
        no_retry_repair_rerun_extension_force=True,
        full_original_path_qualified=False, pressure_qualified=False, clamp_qualified=False,
        HF5_qualified=False, all_tangent_columns_qualified=False,
        preparation_NPZ_read_bytes_headers_hashes_decodes=0,
        prerequisite='New direct human approval tied to this published/restored protocol; M-INTEGRATE1 is closed')
    with (HERE / 'protocol.json').open('x', encoding='utf-8', newline='\n') as output:
        output.write(json.dumps(protocol, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status='prepared_not_authorized_not_executed', bindings=len(bindings),
        protocol_sha256=sha(HERE / 'protocol.json'), inherited_NPZ=10, NPZ_byte_reads=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
