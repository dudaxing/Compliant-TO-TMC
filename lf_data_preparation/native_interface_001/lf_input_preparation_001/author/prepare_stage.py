"""Write L-PREP1 ordinary source preparation, never import or execute HF."""
from datetime import datetime, timezone
from hashlib import sha256
import ast
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
BASE = '7e53ce4eb455b29fec2e789b6c166157728ebff8'
REL = 'lf_data_preparation/native_interface_001/lf_input_preparation_001'
STAGE = ROOT / REL
OLD_MANIFEST = '261c7d402b35cc7d0b75b71a48fada9e3ed9d81610c9fa12b2cbc58379fcbae6'
PRIOR_PROOF = Path('D:/hf-native-workpiece-api-author-20261013/MPREF1_preparation_001/execution_publication_receipt.json')

def digest(path):
    assert path.suffix in {'.py', '.md', '.json', '.toml'}
    return sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def dump(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=ROOT)

def main():
    assert git('rev-parse', 'HEAD').decode().strip() == BASE
    assert git('branch', '--show-current').decode().strip() == 'main'
    assert not git('status', '--porcelain')
    assert not STAGE.exists()
    original_manifest = (ROOT / 'handoff/repository_manifest.json').read_bytes()
    assert sha256(original_manifest).hexdigest() == OLD_MANIFEST
    previous = read(PRIOR_PROOF)
    assert previous['published_commit'] == BASE and previous['manifest_sha256'] == OLD_MANIFEST
    assert previous['executed_card'] == 'M-PREF1' and previous['execution_status'] == 'pass' and previous['execution_closed'] is True
    old = {row['path']: row for row in json.loads(original_manifest)['files']}
    assert len(old) == 20053 and sum(row['bytes'] for row in old.values()) == 10498539849
    author = read(HERE / 'source_author_receipt.json')
    targets = {
        'hf_repo/src/hf_eval/lf_native_inputs.py': 'lf_native_inputs.py',
        'hf_repo/scripts/prepare_native_lf_inputs.py': 'prepare_native_lf_inputs.py',
    }
    for target, name in targets.items():
        assert not (ROOT / target).exists() and not (ROOT / target).is_symlink()
        assert digest(HERE / name) == author['current_source_SHA256'][name]
        ast.parse((HERE / name).read_text(encoding='utf-8'))
    files = {
        'L-PREP1_CARD.md': 'L-PREP1_CARD.md',
        'PREPARATION_RESULTS.md': 'PREPARATION_RESULTS.md',
        'execute_lf_preparation.py': 'execute_lf_preparation.py',
        'launch_lf_preparation.py': 'launch_lf_preparation.py',
        **{'candidate/' + target: name for target, name in targets.items()},
    }
    author_names = (
        'input_contract_review.json', 'input_contract_review.md',
        'source_input_policy_review.json', 'source_input_policy_review.md',
        'SOURCE_AUTHOR_NOTES.md', 'source_author_receipt.json',
        'api_contract_independent_review.json', 'api_contract_independent_review.md',
        'API_CLI_AUTHOR_CONTRACT_NOTES.md',
        'EXECUTION_SOURCE_PLAN.md', 'execution_source_author_receipt.json',
        'RESOURCE_PUBLISHER_SOURCE_NOTES.md', 'resource_publisher_author_receipt.json',
        'wrapper_cross_review.json', 'wrapper_cross_review.md',
        'publisher_source.py', 'prepare_stage.py', 'front_prefix.md',
    )
    files.update({'author/' + name: name for name in author_names})
    for relative, name in files.items():
        path = HERE / name
        assert path.is_file(), name
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8'))
    cases = []
    inherited = {}
    templates = {
        'inverter_canonical': 'lf_data_preparation/native_model_001/tasks/inverter_canonical.json',
        'gripper_canonical': 'lf_data_preparation/native_model_001/tasks/gripper_canonical.json',
        'gripper_native_fine': 'lf_data_preparation/native_interface_001/saved_extension_004/proposed_task.json',
    }
    bindings = {}
    for alias, template in templates.items():
        source = f'lf_data_preparation/v2_adapter_001/inputs/{alias}/design.json'
        descriptor = read(ROOT / source)
        array = str(Path(source).with_name('design.npz')).replace('\\', '/')
        assert old[array]['sha256'] == descriptor['arrays']['sha256']
        assert (ROOT / array).stat().st_size == old[array]['bytes']
        inherited[array] = dict(sha256=old[array]['sha256'], bytes=old[array]['bytes'], preparation_identity_basis='closed_M-PREF1_manifest_plus_stat_only')
        bindings[source] = digest(ROOT / source)
        bindings[template] = digest(ROOT / template)
        bindings[array] = old[array]['sha256']
        cases.append(dict(alias=alias, source_descriptor=source, task_template=template,
            output_subdirectory='cases/' + alias, entry='CLI_runpy_same_interpreter' if alias == 'gripper_native_fine' else 'API',
            right_medium_width_mm=None if alias == 'inverter_canonical' else 4.0,
            expected_descriptor_sha256=bindings[source], source_design_id=descriptor['design_id'],
            source_geometry_id=descriptor['geometry_id'], native_mesh=descriptor['grid']['native_mesh'],
            cell_mm=descriptor['grid']['cell_mm'], task_schema=read(ROOT / template)['schema_version']))
    assert read(ROOT / templates['gripper_native_fine'])['path']['targets_mm'][-1] == 0
    assert len(read(ROOT / templates['gripper_native_fine'])['path']['targets_mm']) == 25
    for name, pin in author['inherited_preparation_sources_SHA256'].items():
        assert digest(ROOT / name) == pin == old[name]['sha256']
        bindings[name] = pin
    # The other imported source files stay byte-identical; source bindings cover
    # the task/mapping/kernel import chain without executing it during preparation.
    for name in ('native_map.py', 'tmc.py', 'tmc_kernel.py', 'q1.py'):
        path = ROOT / 'hf_repo/src/hf_eval' / name
        if path.is_file():
            relative = path.relative_to(ROOT).as_posix()
            bindings[relative] = digest(path)
            assert bindings[relative] == old[relative]['sha256']
    STAGE.mkdir(parents=True)
    for relative, name in files.items():
        destination = STAGE / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write((HERE / name).read_bytes())
    (STAGE / 'author/previous_execution_publication_receipt.json').write_bytes(PRIOR_PROOF.read_bytes())
    install_sources = {}
    for target, name in targets.items():
        candidate = REL + '/candidate/' + target
        pin = digest(ROOT / candidate)
        install_sources[target] = dict(source=candidate, sha256=pin)
        bindings[candidate] = pin
    for name in ('execute_lf_preparation.py', 'launch_lf_preparation.py'):
        bindings[REL + '/' + name] = digest(STAGE / name)
    protocol = dict(schema_version='hf-native-lf-preparation-card-1.0', card='L-PREP1',
        prepared=True, authorized=False, executed=False, installed=False,
        source_baseline_commit=BASE, created_utc=datetime.now(timezone.utc).isoformat(),
        origin='https://github.com/dudaxing/Compliant-TO-TMC.git', science_version='0.5.0',
        preparation_output=REL + '/run_001', install_sources=install_sources, cases=cases,
        phases=dict(preparation=dict(helper_seconds=180, outer_seconds=240)), sampled_RSS_bytes=8*1024**3,
        resource_mode='Elapsed checkpoints and sampled process-tree RSS; cooperative stop, no OS hard cap or force',
        expected_real_preparations=3, expected_cli_invocations=1, expected_plots=1,
        expected_instances=12, expected_negative_instances=9, expected_npz_loads=11,
        expected_HP_calls=0, expected_force_calls=0, expected_tangent_calls=0, expected_solver_calls=0, expected_model_constructions=0,
        static_distinct_npz=8, static_distinct_fields=32,
        static_field_read_occurrences=44, field_reads_monitored=False,
        array_scope_basis='11 decoders of four fields each; byte-only snapshots/sealing are additional to decode counts and occur only inside the approved window',
        inherited_NPZ_bindings=inherited, bindings=bindings,
        source_preparation_scientific_bytes_headers_hashes_decode=0,
        preparation_scope='ordinary LF conversion, explicit optional right padding, geometry-only task binding, finite exact data checks and undeformed task-declaration view',
        CLI_execution_scope='Real installed CLI __main__ and argv via runpy in the same helper; no claim of separate interpreter startup verification',
        qualification=dict(model_qualified=False, mechanical_qualified=False, full_path_qualified=False, pressure_qualified=False, clamp_qualified=False, HF5_qualified=False),
        first_unexpected_error_stops=True, external_retries=0, automatic_rollback=False,
        force_allowed=False, repair_rerun_allowed=False, extension_allowed=False,
        plot_pixel_inspections_max=1, scientific_reads_after_closed_window_allowed=False)
    dump(STAGE / 'protocol.json', protocol)
    prefix = (HERE / 'front_prefix.md').read_bytes()
    histories = []
    for relative in ('docs/CURRENT_STATUS.md', 'docs/RESUME_DEVELOPMENT.md'):
        path = ROOT / relative
        prior = git('show', BASE + ':' + relative)
        assert path.read_bytes() == prior
        combined = prefix + prior
        assert combined.count(prior) == 1
        path.write_bytes(combined)
        histories.append(dict(path=relative, old_sha256=sha256(prior).hexdigest(), new_sha256=sha256(combined).hexdigest(),
            history_start_byte=len(prefix), history_end_byte_exclusive=len(combined), old_raw_contiguous_once=True))
    artifacts = {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(STAGE.rglob('*')) if path.is_file()}
    receipt = dict(card='L-PREP1', status='source_prepared_not_executed', source_baseline_commit=BASE,
        prepared=True, authorized=False, executed=False, installed=False,
        artifact_SHA256=artifacts, front_history=histories, default_runtime_changes=0,
        scientific_or_media_byte_reads_hashes_headers_decode=0, new_HF_API_tests_plots_solver_force_tangent_HP=0,
        protocol_sha256=digest(STAGE / 'protocol.json'))
    dump(STAGE / 'author/preparation_receipt.json', receipt)
    dump(HERE / 'preparation_write_receipt.json', dict(status='ordinary_stage_write_pass',
        stage=REL, protocol_sha256=receipt['protocol_sha256'], new_stage_files=len(artifacts)+1,
        modified_fronts=2, source_baseline_commit=BASE, scientific_bytes_read=False, runtime_executed=False))
    print(json.dumps(dict(status='source_prepared_not_executed', stage=REL, protocol_sha256=receipt['protocol_sha256'], files=len(artifacts)+1)))

if __name__ == '__main__':
    main()
