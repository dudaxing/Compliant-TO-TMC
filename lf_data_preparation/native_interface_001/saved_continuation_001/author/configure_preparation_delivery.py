"""Review ordinary prepared bytes and configure incremental publication."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
BASE = '01b5078acaf76fdaabfbdf214da9db16056467bc'
REL = 'lf_data_preparation/native_interface_001/saved_continuation_001'
FRONTS = {'docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md'}
sha = lambda p: sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_bytes())
git = lambda *args: subprocess.check_output(['git',*args],cwd=ROOT)


def new_json(path, value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    stage = ROOT/REL
    assert git('rev-parse','HEAD').decode().strip() == BASE
    assert not (stage/'run_001').exists()
    assert not (stage/'author/authorization.json').exists()
    assert not (stage/'author/direct_human_reply.json').exists()
    protocol = read(stage/'protocol.json')
    assert protocol['card'] == 'M-RESUME1' and protocol['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is False
    assert protocol['targets_mm'] == [1.2,1.15] and protocol['initial_parameter'] == 1.2 and protocol['target_origin'] == 0.
    assert protocol['gates'] == read(ROOT/protocol['parent_protocol'])['gates']
    parent = read(ROOT/protocol['parent_result'])
    assert protocol['settings'] == dict(parent['settings'],time_limit_seconds=1800.)
    assert parent['status'] == 'failed' and parent['failure']['code'] == 'time_limit'
    assert protocol['targets_mm'] == parent['targets_mm'][13:]
    assert len(protocol['focused_test_nodeids']) == 5
    pins = protocol['bindings']
    assert all(sha(ROOT/name) == pin for name,pin in pins.items())
    for name,spec in protocol['source_package']['files'].items():
        assert Path(name).suffix == '.py' and spec['sha256'] == pins[spec['path']]
        ast.parse((ROOT/spec['path']).read_text(encoding='utf-8'))
    assert set(protocol['pure_view_bindings']) <= set(pins)
    assert all(pins[k] == v for k,v in protocol['pure_view_bindings'].items())
    for name in ['candidate_static_review.json','wrapper_peer_review.json']:
        review = read(stage/'author'/name)
        assert review['status'].startswith('pass') and review['executed'] is False
        for source,pin in review['reviewed_external_SHA256'].items():
            assert sha(EXT/source) == pin, (name,source)
    for path in stage.rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    assert (stage/'author/deliver_resume_preparation.py').read_bytes() == (EXT/'deliver_resume_preparation.py').read_bytes()
    tool_copy = stage/'author/configure_preparation_delivery.py'
    with tool_copy.open('xb') as stream:
        stream.write(Path(__file__).read_bytes())
    prep = read(EXT/'stage_preparation_receipt.json')
    config_name = REL+'/author/preparation_delivery_config.json'
    final_name = REL+'/author/preparation_final_review.json'
    allowed = FRONTS | {p.relative_to(ROOT).as_posix() for p in stage.rglob('*') if p.is_file()} | {config_name,final_name}
    for row in prep['front_history']:
        old = git('show',BASE+':'+row['path'])
        current = (ROOT/row['path']).read_bytes()
        assert current.count(old) == 1 and sha256(old).hexdigest() == row['old_sha256']
        assert sha256(current).hexdigest() == row['new_sha256']
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']] == old
    proof = REL+'/author/M_AVIEW1_execution_publication_receipt.json'
    assert read(ROOT/proof)['published_commit'] == BASE and read(ROOT/proof)['execution_status'] == 'pass'
    config = dict(schema_version='saved-native-resume-preparation-delivery-1.0',card='M-RESUME1',
        source_baseline_commit=BASE,protocol_sha256=sha(stage/'protocol.json'),binding_pins=pins,
        front_history=prep['front_history'],allowed_delta_paths=sorted(allowed),final_review_path=final_name,
        previous_publication_receipt=dict(path=proof,sha256=sha(ROOT/proof)),
        prepared=True,authorized=False,executed=False,original_science_and_qualification_unchanged=True)
    new_json(ROOT/config_name,config)
    reviewed = (allowed-{final_name}) | set(pins)
    final = dict(status='pass_static_preparation_and_incremental_metadata_delivery_review_not_executed',
        created_utc=datetime.now(timezone.utc).isoformat(),source_baseline_commit=BASE,
        config_sha256=sha(ROOT/config_name),protocol_sha256=sha(stage/'protocol.json'),
        reviewed_repository_SHA256={name:sha(ROOT/name) for name in sorted(reviewed)},
        reviewed_external_SHA256={name:sha(EXT/name) for name in ['deliver_resume_preparation.py','configure_preparation_delivery.py']},
        semantic_review_scope='Root read modified controller/Mean/reader/API/CLI/summary/test/helper; independent math and wrapper peer reviews archived. Full package hashes/AST bind bytes, not a new science audit.',
        checks=dict(original_gates_literal_equal=True,parent_settings_except_new_clock_equal=True,
            absolute_original_suffix=True,parent_NOT_PASS_preserved=True,new_source_package_overlay_only=True,
            original_source_closure_bound=True,pure_view_separate_unchanged=True,
            focused_five_nodeids_bound=True,source_AST_only=True,front_old_body_byte_exact_once=True,
            no_run_authorization_or_fake_execution_artifacts=True,no_default_hf_repo_implementation_changes=True),
        prepared=True,authorized=False,executed=False,new_tests_or_NPZ_decodes_or_F_T_HP_solve_or_plots=0,
        qualification_unchanged=True,whole_HF5_complete=False)
    new_json(ROOT/final_name,final)
    print(json.dumps(dict(status=final['status'],allowed_delta_files=len(allowed),binding_count=len(pins))))


if __name__ == '__main__':
    main()
