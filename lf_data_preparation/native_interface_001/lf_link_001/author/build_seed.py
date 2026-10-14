"""Create the ordinary L-LINK1 seed and explicit source-copy plan, not runtime."""
from pathlib import Path
from hashlib import sha256
import json

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/lf_link_001'


def read(path):
    assert path.suffix in {'.json', '.py', '.md'}
    return json.loads(path.read_bytes())


def main():
    audit = read(HERE / 'evidence_scope_audit.json')
    author = read(HERE / 'candidate/source_author_receipt.json')
    records = audit['ordinary_evidence_read_and_verified']
    default = 'hf_repo/src/hf_eval/native_response.py'
    bindings = {name: record['sha256'] for name, record in records.items()
                if name not in {'handoff/repository_manifest.json', default}}
    media = {record['path']: {key: record[key] for key in ('sha256', 'bytes')}
             for record in audit['five_existing_media_inherited_only_for_preparation']}
    bindings.update({name: record['sha256'] for name, record in media.items()})
    files = {
        'candidate.native_response.py': 'candidate/native_response.py',
        'test_partial_native_reference.py': 'candidate/test_partial_native_reference.py',
        'execute_lf_link.py': 'candidate/execute_lf_link.py',
        'launch_link.py': 'candidate/launch_link.py',
        'L-LINK1_CARD.md': 'L-LINK1_CARD.md', 'PREPARATION_RESULTS.md': 'PREPARATION_RESULTS.md',
    }
    author_files = {
        'input_contract_seed.json': 'input_contract_seed.json',
        'API_SOURCE_SCOPE.md': 'API_SOURCE_SCOPE.md', 'API_SOURCE_PINS.json': 'API_SOURCE_PINS.json',
        'evidence_scope_audit.json': 'evidence_scope_audit.json', 'evidence_scope_audit.md': 'evidence_scope_audit.md',
        'SOURCE_AUTHOR_NOTES.md': 'candidate/SOURCE_AUTHOR_NOTES.md',
        'source_author_receipt.json': 'candidate/source_author_receipt.json',
        'candidate_api_source_review.json': 'candidate_api_source_review.json',
        'candidate_api_source_review.md': 'candidate_api_source_review.md',
        'candidate_contract_source_review.json': 'candidate_contract_source_review.json',
        'candidate_contract_source_review.md': 'candidate_contract_source_review.md',
        'publisher_source.py': 'publisher_source.py', 'PUBLISHER_SOURCE_NOTES.md': 'PUBLISHER_SOURCE_NOTES.md',
        'publisher_source_author_receipt.json': 'publisher_source_author_receipt.json',
        'publisher_source_review.json': 'publisher_source_review.json', 'publisher_source_review.md': 'publisher_source_review.md',
        'prepare_stage.py': 'prepare_stage.py', 'front_prefix.md': 'front_prefix.md',
        'file_plan.json': 'file_plan.json', 'build_seed.py': 'build_seed.py',
    }
    files.update({'author/' + name: source for name, source in author_files.items()})
    for relative in ('candidate.native_response.py', 'test_partial_native_reference.py', 'execute_lf_link.py', 'launch_link.py'):
        source = HERE / files[relative]
        pin = sha256(source.read_bytes()).hexdigest()
        assert pin == author['files'][source.name]['sha256']
        bindings[REL + '/' + relative] = pin
    base = 'lf_data_preparation/native_interface_001/lf_forward_001/run_001'
    producer = base + '/lf_fine_forward'
    reference = 'lf_data_preparation/native_interface_001/lf_reference_001/run_001/reference'
    seed = dict(schema_version='lf-selected-reference-linked-delivery-card-1.0', card='L-LINK1',
        source_baseline_commit='909f8acee95279e449e09961fd4fe68fed9d688f', protocol_seed_only=True,
        prepared=True, authorized=False, executed=False, installed=False,
        phases={'link': {'helper_seconds':180, 'outer_seconds':240, 'tests_seconds':60,
            'argv':[REL+'/execute_lf_link.py','--repo','.', '--protocol',REL+'/protocol.json','--time-limit','180']}},
        sampled_RSS_bytes=8*1024**3, bindings=bindings, inherited_media_bindings=media,
        media_files=sorted(media), source_before_installation={'path':default,'sha256':records[default]['sha256']},
        candidate_source=REL+'/candidate.native_response.py', tests_source=REL+'/test_partial_native_reference.py',
        expected_test_methods=author['expected_test_methods'], planned_unit_methods=16, planned_unit_reference_calls=23,
        planned_saved_summary_calls=1, planned_response_writes=1, planned_index_writes=1,
        planned_default_metadata_file_changes=1, expected_new_mechanics_calls=0,
        output_directory=REL+'/run_001', production_stage=base, production_result_dir='lf_fine_forward',
        reference_stage=reference, result_file=producer+'/result.json', model_file=producer+'/model/model.json',
        original_response_file=producer+'/response.json', reference_file=reference+'/summary.json',
        raw_view_file=base+'/view/view.json', view_case_summary_file=base+'/view/lf_fine_forward/summary.json',
        reference_observation_file=reference+'/reference_observations.json',
        reference_observation_media_file=reference+'/reference_observations.png',
        production_receipt_file=base+'/execution_receipt.json', reference_execution_receipt_file=reference+'/execution_receipt.json',
        selected_accepted_indices=[13,16], original_target_indices=[13,16], targets_mm=[1.2,1.05],
        selected_state_identity=audit['states'], production_accepted_states=25, expected_reference_states=2,
        production_path_completed=True, full_production_path_reference_pass=False, full_original_path_reference_pass=False,
        HF5_qualified=False, HP_matrix_columns_exhaustively_checked=False, contact_qualified=False,
        clamp_qualified=False, pressure_qualified=False, original_gates=audit['original_gates'],
        previous_publication_file=REL+'/author/previous_publication_receipt.json',
        scope='Only selected-reference metadata API matching, fixed metadata tests and saved same-result association. No new mechanics, scientific arrays/reference archive read, media decode or new plot.',
        retries=0, repair_rerun_allowed=False, extension_allowed=False, force_allowed=False,
        rollback_allowed=False, delete_allowed=False)
    for name, value in (('input_contract_seed.json', seed), ('file_plan.json', {'files':files})):
        with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status':'ordinary_seed_created_not_executed','bindings':len(bindings),'source_plan_files':len(files),'media_stat_only':5}))


if __name__ == '__main__':
    main()
