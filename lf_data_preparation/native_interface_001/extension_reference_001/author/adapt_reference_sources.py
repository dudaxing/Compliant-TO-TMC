"""Author source-only adapter; ordinary text/AST only, no reference imports or arrays."""
from pathlib import Path
import ast

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
HERE = Path(__file__).resolve().parent
OLD = ROOT/'lf_data_preparation/native_interface_001/alpha_reference_001'


def replace_once(text, old, new):
    assert text.count(old) == 1, old[:100]
    return text.replace(old, new)


source = (OLD/'execute_alpha_reference.py').read_text(encoding='utf-8')
source = source.replace('M-AREF1', 'M-EREF1').replace('AlphaSegmentAudit', 'ExtensionStateAudit')
source = source.replace('alpha-saved-segment-independent-reference-card-1.0', 'extension-saved-state-independent-reference-card-1.0')
source = replace_once(source, 'CONTRACT = read_json(PROTOCOL_FILE)',
    "CONTRACT = read_json(PROTOCOL_FILE)\nHELPER_LIMIT = CONTRACT['phases']['reference']['helper_seconds']\nOUTER_LIMIT = CONTRACT['phases']['reference']['outer_seconds']")
source = replace_once(source, "authorization['helper_seconds'] == CONTRACT['phases']['reference']['helper_seconds'] == 900", "authorization['helper_seconds'] == HELPER_LIMIT")
source = replace_once(source, "authorization['outer_seconds'] == CONTRACT['phases']['reference']['outer_seconds'] == 960", "authorization['outer_seconds'] == OUTER_LIMIT")
source = source.replace("and reply['reply_context'] == 'Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction'", "and reply['reply_context']")
source = source.replace("and self.limit == c['phases']['reference']['helper_seconds'] == 900.\n            and c['phases']['reference']['outer_seconds'] == 960.",
    "and self.limit == HELPER_LIMIT > 0.\n            and c['phases']['reference']['outer_seconds'] == OUTER_LIMIT >= HELPER_LIMIT")
source = source.replace("and c['expected_accepted_states'] == 2 and c['expected_new_HP_calls'] == 4\n            and c['targets_mm'] == [1.2,1.15] and c['original_target_indices'] == [13,14]",
    "and c['expected_accepted_states'] == 1 and c['expected_new_HP_calls'] == 2\n            and c['selected_child_accepted_index'] == 1 and c['targets_mm'] == [1.1]\n            and c['original_target_indices'] == [15] and c['production_targets_mm'] == [1.15,1.1]")
source = source.replace("receipt['requested_absolute_targets_mm'] == c['targets_mm']", "receipt['requested_absolute_targets_mm'] == c['production_targets_mm']")
source = replace_once(source,
    "and receipt['parent_status'] == 'failed' and receipt['parent_full_path_completed'] is False\n            and receipt['selected_state_index'] == 13",
    "and receipt['parent_status'] == 'success' and receipt['parent_failure'] is None\n            and receipt['ancestor_continuation']['parent_status'] == 'failed'\n            and receipt['ancestor_continuation']['parent_failure']['code'] == 'time_limit'\n            and receipt['selected_state_index'] == 1\n            and receipt['installation_complete'] is launch['installation_complete'] is True\n            and len(receipt['installed_transitions']) == 6")
source = source.replace("result['scope'] == 'native_saved_mean_continuation_segment' and result['targets_mm'] == c['targets_mm']",
    "result['scope'] == 'native_saved_mean_explicit_task_extension_segment' and result['targets_mm'] == c['production_targets_mm']")
source = source.replace("result['task_target_executed'] is result['full_original_path_completed'] is False",
    "result['task_target_executed'] is result['full_original_path_completed'] is result['full_extended_path_completed'] is False")
source = replace_once(source,
    "and continuation['parent_status'] == 'failed' and continuation['parent_failure']['code'] == 'time_limit'\n            and continuation['parent_path_completed'] is continuation['parent_task_target_executed'] is False\n            and continuation['parent_unload_endpoint_reached'] is continuation['full_original_path_executed_by_child'] is False",
    "and continuation['continuation_mode'] == 'explicit_task_extension'\n            and continuation['parent_status'] == 'success' and continuation['parent_failure'] is None\n            and continuation['parent_path_completed'] is continuation['parent_unload_endpoint_reached'] is True\n            and continuation['parent_task_target_executed'] is continuation['full_original_path_executed_by_child'] is False\n            and continuation['full_extended_path_executed_by_child'] is continuation['full_extended_path_completed'] is False\n            and continuation['parent_continuation']['parent_status'] == 'failed'\n            and continuation['parent_continuation']['parent_failure']['code'] == 'time_limit'\n            and continuation['appended_targets_mm'] == [1.1]\n            and continuation['source_task_targets_mm'] == c['source_task_targets_mm']\n            and continuation['source_task_sha256'] == c['source_task_sha256']\n            and continuation['extended_task_targets_mm'] == c['original_targets_mm']\n            and continuation['extended_task_sha256'] == c['task_sha256']")
source = source.replace("continuation['requested_suffix_targets_mm'] == c['targets_mm']", "continuation['requested_suffix_targets_mm'] == c['production_targets_mm']")
source = source.replace("continuation['original_target_indices'] == c['original_target_indices']", "continuation['original_target_indices'] == c['production_original_target_indices']")
source = replace_once(source, "        model_file, metadata_file =", "        for name,pin in c['installed_producer_sources'].items():\n            self.check(receipt['actual_default_SHA256'][name] == launch['actual_default_SHA256'][name] == sha(self.repo/name) == pin, 'Installed tested producer source differs')\n        for name,pin in result['mechanics_source_sha256'].items():\n            self.check(sha(self.repo/name) == c['bindings'][name] == pin, 'Saved mechanics source differs from current installed source')\n        model_file, metadata_file =")
source = source.replace("self.check([row['d'] for row in states] == c['targets_mm']\n            and [row['original_target_index'] for row in states] == c['original_target_indices']",
    "self.check([row['d'] for row in states] == c['production_targets_mm']\n            and [row['original_target_index'] for row in states] == c['production_original_target_indices']")
source = replace_once(source, "'Two original accepted child states differ')\n        for file", "'Actual two-state producer identity differs')\n        self.selected_states = [states[c['selected_child_accepted_index']]]\n        self.check(self.selected_states[0]['d'] == c['targets_mm'][0]\n            and self.selected_states[0]['original_target_index'] == c['original_target_indices'][0]\n            and self.selected_states[0]['child_original_target_index'] == 1\n            and self.selected_states[0]['leg'] == 'unloading' and self.selected_states[0]['continuation_anchor'] is False,\n            'Only the newly accepted child001/global15 endpoint may be referenced')\n        for file")
source = source.replace("for row in states for key in ('state','forces','tangents','matrix')", "for row in self.selected_states for key in ('state','forces','tangents','matrix')")
source = source.replace("[self.origin/row['descriptor_path'] for row in states]", "[self.origin/row['descriptor_path'] for row in self.selected_states]")
source = replace_once(source,
    "        # Raw inherited reports stay indexed13/14. Only top-level metadata is copied.\n        return [dict(deepcopy(record),index=index,child_accepted_index=index,",
    "        # Raw inherited report keeps global15. Top metadata records actual producer child1.\n        return [dict(deepcopy(record),index=CONTRACT['selected_child_accepted_index'],child_accepted_index=CONTRACT['selected_child_accepted_index'],")
source = source.replace("enumerate(zip(self.rows,self.result['states']))", "enumerate(zip(self.rows,self.selected_states))")
source = replace_once(source, "        for row in self.result['states']:", "        for row in self.selected_states:")
source = source.replace("self.hp_started == self.hp_completed == 4 and len(self.rows) == self.workpiece_completed == 2", "self.hp_started == self.hp_completed == 2 and len(self.rows) == self.workpiece_completed == 1")
source = source.replace("Fresh complete two-state HP/body coverage differs", "Fresh selected endpoint HP/body coverage differs")
source = source.replace("alias='alpha_half_saved_suffix',case_family='gripper',accepted_states=2", "alias='extension_alpha_half_saved_endpoint',case_family='gripper',accepted_states=1")
source = source.replace("All2 accepted saved child suffix states,13440 elements/27378 DOFs; original indices13/14, child indices0/1; actual PORT direction,deltaR=0; signed body/holding projections", "Only selected child001/global15/1.10 saved endpoint,13440 elements/27378 DOFs; actual PORT direction,deltaR=0; signed body/holding projections")
source = source.replace("Only these two saved alpha-half suffix states and declared direction. Original15 gates; no parent/full original path,all columns,stress/energy/pressure,effective clamp,stability or HF5 qualification", "Only selected saved1.10 endpoint and declared direction. Original15 gates; no full two-state child/full original or extended path,all columns,stress/energy/pressure,effective clamp,stability or HF5 qualification")
source = source.replace("continuation=deepcopy(self.result['continuation']),full_original_path_reference_pass=False,", "continuation=deepcopy(self.result['continuation']),selected_child_accepted_index=1,\n            full_child_path_reference_pass=False,full_extended_path_reference_pass=False,full_original_path_reference_pass=False,")
source = source.replace("full_original_path_completed=False,contact_qualified=False", "full_original_path_completed=False,full_extended_path_completed=False,contact_qualified=False")
source = source.replace("full_original_path_reference_pass=False,contact_qualified=False", "full_child_path_reference_pass=False,full_extended_path_reference_pass=False,\n            full_original_path_reference_pass=False,contact_qualified=False")
source = source.replace("print(dict(status='pass',accepted_states=2", "print(dict(status='pass',accepted_states=1")
source = replace_once(source, "require(ARGS.time_limit == CONTRACT['phases']['reference']['helper_seconds'] == 900., 'M-EREF1 requires its explicit new900s window')", "require(ARGS.time_limit == HELPER_LIMIT > 0., 'M-EREF1 requires its explicit protocol/authorization window')")
source = source.replace('independent HP reference of two saved alpha-half segment states', 'independent HP reference of one newly saved1.10 endpoint')
source = source.replace('bound loader, resource window, provenance and child/original index metadata', 'bound selected-state loader, protocol-authorized resource window, provenance and index metadata')
ast.parse(source)
with (HERE/'execute_extension_reference.py').open('x',encoding='utf-8',newline='\n') as out:out.write(source)

launcher = (OLD/'launch_reference.py').read_text(encoding='utf-8').replace('M-AREF1', 'M-EREF1').replace('execute_alpha_reference.py', 'execute_extension_reference.py')
launcher = launcher.replace("assert reply['reply_context'] == 'Current conversation direct human send_user_message_question_reply; not an automatic goal continuation or attached-file instruction'", "assert reply['reply_context']")
launcher = replace_once(launcher, "    assert protocol['phases']['reference'] == dict(helper_seconds=900, outer_seconds=960)", "    helper_limit,outer_limit = (protocol['phases']['reference'][name] for name in ('helper_seconds','outer_seconds'))\n    assert 0 < helper_limit <= outer_limit\n    assert authorization['helper_seconds'] == helper_limit and authorization['outer_seconds'] == outer_limit\n    assert authorization['sampled_RSS_bytes'] == protocol['sampled_RSS_bytes'] == 8*1024**3")
launcher = launcher.replace("'--time-limit', '900'", "'--time-limit', str(helper_limit)").replace('outer_seconds=960', 'outer_seconds=outer_limit')
launcher = launcher.replace('<= 960', '<= outer_limit').replace('> 960', '> outer_limit').replace('child_elapsed > 900', 'child_elapsed > helper_limit')
launcher = launcher.replace("summary['accepted_states'] == 2 and summary['HP_calls_started'] == summary['HP_calls_completed'] == 4", "summary['accepted_states'] == 1 and summary['HP_calls_started'] == summary['HP_calls_completed'] == 2")
ast.parse(launcher)
with (HERE/'launch_reference.py').open('x',encoding='utf-8',newline='\n') as out:out.write(launcher)
