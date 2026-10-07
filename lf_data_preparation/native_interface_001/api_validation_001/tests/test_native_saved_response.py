"""Existing JSON fixtures verify response meaning; this does not recompute mechanics."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from hf_eval.native_response import summarize_saved_native_result


REPO = Path(os.environ.get('HF_INTERFACE_TEST_REPO', Path(__file__).resolve().parents[2])).resolve()
CASES = {
    'right2col': ('lf_data_preparation/native_workpiece_001/right_margin_cycle_001',
        'e3ee572c2181a94134c99acab6bedf5f3736d6b665b03926e1507ed52bed090b',
        'b871ff4791b296ab21d5b44c631f63b4cb81d62be1fdfeb725659379d7a68fe9'),
    'right4col': ('lf_data_preparation/native_workpiece_001/right_margin4_cycle_001',
        'b49955f7e56cd714b35283c0834757ebefc947d3ca25a4f505ed44e8947db7b6',
        '91c3ef2720e80547e13e1c84e9bfb09d132804f16d3ab819509310e2bbd080e7'),
}
NO_BODY = 'lf_data_preparation/native_fine_task_025_001/result/result.json'
FAILED = 'lf_data_preparation/native_workpiece_001/enlarged_square_contact_001/run_001/result/result.json'
SHORT = 'lf_data_preparation/native_fine_mean_001/result/result.json'
VIEW = 'functional_views/right_margin4_20261007/complete_001/view/view.json'


def read_json(relative, expected_sha=None):
    raw = (REPO / relative).read_bytes()
    if expected_sha is not None:
        assert sha256(raw).hexdigest() == expected_sha, 'The test fixture must be the actual closed JSON'
    return json.loads(raw)


@pytest.fixture(autouse=True)
def no_array_reads(monkeypatch):
    original = Path.open

    def json_or_source_only(self, *args, **kwargs):
        assert self.suffix.lower() != '.npz', 'Saved compact responses must not open arrays'
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', json_or_source_only)


def assert_state(compact, raw, index):
    assert compact['index'] == index and compact['state_sha256'] == raw['state_sha256']
    assert compact['d_mm'] == raw['d'] and compact['leg'] == raw.get('leg')
    assert compact['original_target_index'] == raw.get('original_target_index')
    for dest, source in [('R_input_N','R_input'),('q_in_mm','q_in'),('q_out_mm','q_out'),
        ('minimum_J','minimum_J'),('relative_residual','relative_residual'),
        ('relative_global_force_balance','relative_global_force_balance'),
        ('constraint_residual_mm','constraint_residual'),('max_abs_Hu_per_mm','max_abs_Hu_per_mm')]:
        assert compact[dest] == raw.get(source)
    if 'workpiece' not in raw:
        assert compact['workpiece'] is None
    else:
        for key, value in compact['workpiece'].items():
            assert value == raw['workpiece'][key]
        assert compact['workpiece']['force_on_lower_body_N'] == raw['workpiece']['force_on_lower_body_N']


@pytest.mark.parametrize('label', ['right2col','right4col'])
def test_complete_saved_cycles_keep_physics_peak_return_and_actual_all_state_reference(label):
    stage, result_sha, ref_sha = CASES[label]
    result_rel, ref_rel = stage + '/run_001/result/result.json', stage + '/reference/summary.json'
    raw = read_json(result_rel, result_sha)
    reference = read_json(ref_rel, ref_sha)
    response = summarize_saved_native_result(result_rel, repo_root=REPO, reference_file=ref_rel)
    assert response['status'] == 'success' and response['path']['completed']
    assert response['identity']['result']['sha256'] == result_sha
    assert response['identity']['result']['path'] == result_rel
    assert response['path']['accepted_states'] == len(raw['states']) == 24
    assert response['path']['requested_targets_mm'] == raw['targets_mm']
    model = read_json(str(Path(result_rel).parent / raw['model']['descriptor_path']))
    assert response['physics']['grid'] == raw['grid'] == model['grid']
    assert response['physics']['counts'] == raw['counts']
    assert response['physics']['material'] == model['material']
    assert response['physics']['workpiece'] == model['task']['workpiece']
    loading = [(i,s) for i,s in enumerate(raw['states']) if s['leg'] == 'loading']
    peak_index, peak = max(loading, key=lambda item:item[1]['d'])
    assert peak_index == 13 and raw['states'][-1]['d'] == 0
    assert_state(response['maximum_loading_stroke'], peak, peak_index)
    assert_state(response['target_response'], peak, peak_index)
    assert_state(response['last_accepted'], raw['states'][-1], 23)
    assert_state(response['requested_endpoint_response'], raw['states'][-1], 23)
    assert response['call_counts'] == raw['call_counts']
    assert response['producer_flags'] == {key:raw[key] for key in ['independent_HP_qualified','equilibrium_qualified','HF_qualified']}
    qualified = response['independent_reference']
    assert qualified['accepted_reference_pass'] and qualified['full_path_reference_pass']
    assert qualified['report']['sha256'] == ref_sha
    assert qualified['accepted_states'] == 24 and qualified['HP_calls_completed'] == 48
    assert all(reference['states'][i]['state_sha256'] == state['state_sha256'] for i,state in enumerate(raw['states']))
    assert not any(qualified[key] for key in ['HP_all_columns_qualified','contact_qualified','clamp_qualified','pressure_qualified','HF5_qualified'])
    assert response['options']['initial_guess']['value'] == 'port_projection'
    assert response['options']['response_mode']['value'] == 'mechanical'
    assert response['options']['tangent_mode']['value'] == 'chunk256'


def test_no_body_saved_response_has_null_workpiece_and_explicit_legacy_defaults():
    raw = read_json(NO_BODY, '9945ccb37d03b960949104a834b817606651bf00a615d110d41e2ad33e39b8cc')
    response = summarize_saved_native_result(NO_BODY, repo_root=REPO)
    assert response['status'] == 'success' and response['path']['accepted_states'] == len(raw['states']) == 4
    assert response['physics']['workpiece'] is None
    assert_state(response['last_accepted'], raw['states'][-1], 3)
    assert_state(response['maximum_loading_stroke'], raw['states'][-1], 3)
    assert response['last_accepted']['workpiece'] is None
    assert response['independent_reference']['accepted_reference_pass'] is False
    assert response['independent_reference']['full_path_reference_pass'] is False
    assert response['options']['initial_guess']['value'] == 'tangent'
    assert response['options']['tangent_mode']['value'] == 'full'
    assert response['options']['response_mode']['value'] == 'complete'
    assert all(value['source'].startswith('schema_default:') for value in response['options'].values())


def test_real_successful_short_path_does_not_claim_its_unexecuted_task_target():
    raw = read_json(SHORT, 'd9f2574a5de93be909a04cf2aa791e8a7afec8de502bf99f786db056004e94d7')
    response = summarize_saved_native_result(SHORT, repo_root=REPO)
    assert response['status'] == 'success' and response['path']['completed']
    assert response['path']['accepted_states'] == 2
    assert response['path']['task_target_mm'] == .025 and not response['path']['task_target_executed']
    assert response['target_response'] is None
    assert_state(response['requested_endpoint_response'], raw['states'][-1], 1)
    assert response['requested_endpoint_response']['d_mm'] == .001


def test_real_failed_prefix_preserves_last_bisected_state_and_never_returns_target_success():
    raw = read_json(FAILED, 'a68c7c2dac03b35d2456daf7b66f032e2d6f489e7f975b673b71659f2ba6706e')
    response = summarize_saved_native_result(FAILED, repo_root=REPO,
        reference_file=CASES['right4col'][0] + '/reference/summary.json')
    assert response['status'] == 'failed' and response['path']['completed'] is False
    assert response['path']['accepted_states'] == len(raw['states']) == 9
    assert response['path']['task_target_mm'] == 1.2 and response['path']['task_target_executed'] is False
    assert response['target_response'] is response['requested_endpoint_response'] is None
    assert_state(response['last_accepted'], raw['states'][-1], 8)
    assert response['last_accepted']['d_mm'] == .86875
    assert response['last_accepted']['is_original_target'] is False
    assert response['failure']['code'] == raw['failure']['code'] == 'invalid_J'
    assert response['failure']['reason'] == raw['failure']['reason']
    assert response['independent_reference']['accepted_reference_pass'] is False
    assert response['independent_reference']['full_path_reference_pass'] is False


@pytest.mark.parametrize('wrong', ['other_result','missing_state','HP_count','not_pass'])
def test_reference_cannot_borrow_other_or_incomplete_or_failed_qualification(tmp_path, wrong):
    stage, _, ref_sha = CASES['right4col']
    result_rel = stage + '/run_001/result/result.json'
    if wrong == 'other_result':
        reference_file = REPO / CASES['right2col'][0] / 'reference/summary.json'
    else:
        reference = deepcopy(read_json(stage + '/reference/summary.json', ref_sha))
        if wrong == 'missing_state':
            reference['states'].pop(7)
        elif wrong == 'HP_count':
            reference['HP_calls_completed'] -= 1
        else:
            reference['status'] = 'not_pass'
        reference_file = tmp_path / 'negative_reference.json'
        reference_file.write_text(json.dumps(reference), encoding='utf-8')
    response = summarize_saved_native_result(result_rel, repo_root=REPO, reference_file=reference_file)
    assert response['status'] == 'success', 'A reference mismatch must not rewrite production success'
    qualified = response['independent_reference']
    assert qualified['status'] == 'mismatch' and qualified['reasons']
    assert qualified['accepted_reference_pass'] is qualified['full_path_reference_pass'] is False
    assert qualified['HP_all_columns_qualified'] is False


def test_real_saved_views_link_common_figures_and_only_the_matching_case_animation():
    view = read_json(VIEW)
    directory = Path(VIEW).parent
    for label in ['right4col','right2col']:
        result = CASES[label][0] + '/run_001/result/result.json'
        response = summarize_saved_native_result(result, repo_root=REPO, view_manifest=VIEW)
        linked = response['views']
        assert linked['status'] == 'matched' and linked['case_label'] == label
        expected = {'comparison.png','distances_forces.png','peak_fields.png',label+'/actual_states.gif'}
        assert {item['path'] for item in linked['links']} == {(directory/name).as_posix() for name in expected}
        assert all(item['sha256'] == view['outputs'][str(Path(item['path']).relative_to(directory)).replace('\\','/')]
                   for item in linked['links'])
        assert sorted(item['kind'] for item in linked['links']) == ['gif','png','png','png']
        assert response['independent_reference']['full_path_reference_pass'] is False


@pytest.mark.parametrize('wrong_label', ['duplicate','swap_unique'])
def test_wrong_view_label_or_failed_result_cannot_borrow_the_fourmm_animation(tmp_path, wrong_label):
    view = read_json(VIEW)
    wrong_view = deepcopy(view)
    two_case = next(case for case in wrong_view['cases'] if case['label']=='right2col')
    four_case = next(case for case in wrong_view['cases'] if case['label']=='right4col')
    two_case['label'] = 'right4col'
    if wrong_label == 'swap_unique':
        four_case['label'] = 'right2col'
    clone = tmp_path / 'wrong_view'
    clone.mkdir()
    source_dir = REPO / Path(VIEW).parent
    for name in ['comparison.png','distances_forces.png','peak_fields.png',
                 'right4col/actual_states.gif','right2col/actual_states.gif',
                 'right4col/summary.json','right2col/summary.json']:
        raw = (source_dir/name).read_bytes()
        assert sha256(raw).hexdigest() == view['outputs'][name]
        output = clone/name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(raw)
    manifest = clone/'view.json'
    manifest.write_text(json.dumps(wrong_view), encoding='utf-8')
    two = summarize_saved_native_result(CASES['right2col'][0]+'/run_001/result/result.json',
        repo_root=REPO, view_manifest=manifest)
    assert two['views']['status'] == 'mismatch' and not two['views']['links']
    failed = summarize_saved_native_result(FAILED, repo_root=REPO, view_manifest=VIEW)
    assert failed['views']['status'] == 'mismatch' and not failed['views']['links']
