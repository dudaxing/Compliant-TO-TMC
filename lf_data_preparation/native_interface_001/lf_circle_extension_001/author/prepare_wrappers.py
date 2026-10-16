"""Adapt the reviewed circle study wrapper; AST only, no HF imports."""
import ast
from pathlib import Path

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
OLD=ROOT/'lf_data_preparation/native_interface_001/lf_circle_pilot_001'
REQUEST='好的，按你的建议先补齐 load_only 保存态延伸功能并完成小模型兼容验证，再从圆形工件0.50 mm保存态推进到0.75 mm。保持半径9 mm、圆心(71,40) mm、其余物理条件和原验收门不变，注意做好记录，可视化实际变形、反力和收敛情况，再根据结果安排后续计算。'

def main():
    text=(OLD/'execute_pilot.py').read_text(encoding='utf-8')
    text=text.replace('One circular-workpiece pilot','One explicit load-only extension').replace('L-CPILOT1','L-CEXT1').replace('wave_circle_pilot','wave_circle_extension')
    text=text.replace('(1800, 600, 2700, 2760, 8*1024**3)','(1800, 600, 3000, 3060, 8*1024**3)')
    text=text.replace('accepted_states=0, zero_start=True, saved_parent_or_state_used=False, extend_path=False,','accepted_states=0, zero_start=False, saved_parent_or_state_used=True, extend_path=True,')
    text=text.replace('Only independent circle 0/.25/.5 load-only pilot;', 'Only explicit circle .5/.75 load-only extension segment;')
    text=text.replace('    def bindings():\n        for name, pin in (protocol[\'input_bindings\'] | protocol[\'source_bindings\']).items():',
        '    def bindings(before_install=False):\n        sources = protocol["baseline_source_bindings" if before_install else "source_bindings"]\n        for name, pin in (protocol["input_bindings"] | sources).items():')
    text=text.replace('def child_once(argv, limit):','def child_once(argv, limit, kind="view_child"):')
    text=text.replace("calls['view_child_started']",'calls[kind+"_started"]').replace("calls['view_child_completed']",'calls[kind+"_completed"]')
    text=text.replace("run/'view_child_stdout.log'",'run/(kind+"_stdout.log")').replace("receipt['view_child_terminal']",'receipt[kind+"_terminal"]')
    start=text.index("        phase = 'bindings_and_task_contract'")
    end=text.index("        sys.path.insert(0, str(ROOT/'hf_repo/src'))",start)
    text=text[:start]+'''        phase = 'baseline_bindings_and_installation'
        bindings(before_install=True)
        assert protocol['tests_seconds'] == 180
        receipt['installed_transitions'] = []
        for transition in protocol['candidate_installations']:
            source, target = ROOT/transition['source'], ROOT/transition['target']
            assert digest(target) == transition['before_sha256']
            raw = source.read_bytes()
            assert sha256(raw).hexdigest() == transition['after_sha256']
            target.write_bytes(raw)
            assert digest(target) == transition['after_sha256']
            receipt['installed_transitions'].append(transition)
            receipt['default_installations'] += 1
            write(receipt_file, receipt)
        assert receipt['default_installations'] == 3
        bindings()
        phase = 'focused_tests'
        receipt['new_tests'] = None
        try:
            child_once([sys.executable, '-X', 'utf8', '-B', str(ROOT/protocol['test_source']),
                '--repo', str(ROOT/'hf_repo'), '--output', str(run/'t'),
                '--stop-file', str(stop), '--time-limit', str(protocol['tests_seconds'])],
                protocol['tests_seconds'], kind='tests_child')
        finally:
            test_file = run/'t/test_report.json'
            if test_file.exists():
                tests = read(test_file)
                receipt.update(new_tests=tests['methods_run'], tests_report=tests)
        assert tests['successful'] is True and tests['methods_run'] == protocol['expected_test_methods']
        phase = 'task_and_parent_contract'
        task_file, parent_file = ROOT/protocol['task_file'], ROOT/protocol['parent_result']
        task, parent_task = read(task_file), read(ROOT/protocol['original_task_file'])
        parent = read(parent_file)
        selected = parent['states'][protocol['selected_state_index']]
        assert set(protocol['task_metadata']) == {'task_id', 'purpose', 'parameter_origin', 'description'}
        expected = deepcopy(parent_task)
        expected.update(protocol['task_metadata'])
        expected['path']['targets_mm'].append(.75)
        expected['input']['target_mm'] = .75
        assert task == expected
        assert task['path'] == dict(kind='load_only', targets_mm=[0., .25, .5, .75])
        assert protocol['targets_mm'] == [.5, .75] and protocol['selected_state_index'] == 2
        assert task['workpiece'] == dict(kind='fixed_rigid', shape='circle', center_mm=[71., 40.],
                                        radius_mm=9., fixed_components=[0, 1])
        assert parent['status'] == 'success' and parent['path_completed'] and parent['path_kind'] == 'load_only'
        assert selected['d'] == selected['physical_mean_target_mm'] == .5 and selected['original_target_index'] == 2
        assert protocol['settings'] == parent['settings'] == read(ROOT/protocol['settings_source_protocol'])['settings']
        assert protocol['settings']['time_limit_seconds'] == 1800.
        assert protocol['gates'] == read(ROOT/protocol['gates_source_protocol'])['gates']
        assert protocol['options'] == dict(response_mode='mechanical', tangent_mode='chunk256', initial_guess='port_projection')
        receipt.update(parent_result=protocol['parent_result'], selected_state_index=2,
            task_file_sha256=digest(task_file), parent_result_sha256=digest(parent_file),
            task_scope='Explicit appended .75 peak and four metadata fields; old [0,.25,.5] prefix and all remaining physics preserved')
''' + text[end:]
    a=text.index('response = native_evaluate.evaluate_native(geometry_file, task_file, production, repo_root=ROOT,')
    b=text.index("            calls['api_completed']",a)
    text=text[:a]+'''response = native_evaluate.evaluate_native(None, task_file, production, repo_root=ROOT,
                saved_result=parent_file, selected_state_index=2, extend_path=True,
                settings=DisplacementSettings(**protocol['settings']), **protocol['options'])
''' +text[b:]
    a=text.index("        assert N >= 3")
    b=text.index("        checkpoint()\n\n        phase = 'viewer_binding'",a)
    text=text[:a]+'''        assert N >= 2 and N == len(saved['states']) == receipt['accepted_states']
        assert saved['status'] == 'success' and saved['path_kind'] == 'load_only' and saved['path_completed']
        assert saved['unload_endpoint_reached'] is None and saved['reached_displacement'] == .75
        assert saved['new_peak_reached'] and saved['extended_segment_completed'] and saved['loading_peak_reached']
        assert saved['task_target_executed'] is False and saved['full_extended_path_completed'] is False
        assert saved['targets_mm'] == protocol['targets_mm'] and saved['target_origin'] == 0.
        assert saved['settings'] == receipt['actual_settings'] == protocol['settings']
        continuation = saved['continuation']
        assert continuation['continuation_mode'] == 'explicit_task_extension'
        assert continuation['segment_completed'] and continuation['anchor_revalidated'] and continuation['anchor_identity_preserved']
        assert continuation['extended_segment_completed'] and continuation['new_peak_reached']
        assert continuation['full_original_path_executed_by_child'] is False
        assert continuation['original_task_targets_mm'] == [0., .25, .5, .75]
        assert continuation['appended_targets_mm'] == [.75] and continuation['requested_suffix_targets_mm'] == [.5, .75]
        originals = [row for row in saved['states'] if row['is_original_target']]
        assert [row['original_target_index'] for row in originals] == [2, 3]
        assert [row['child_original_target_index'] for row in originals] == [0, 1]
        assert [row['d'] for row in originals] == [.5, .75]
        assert [row['leg'] for row in originals] == ['resume_origin', 'loading']
        first = saved['states'][0]
        assert first['continuation_anchor'] and first['newton_checks'] == 1
        assert first['state_sha256'] == selected['state_sha256']
        assert float(first['R_input']).hex() == float(selected['R_input']).hex()
        assert all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
        assert response['target_response'] is None
        assert response['requested_endpoint_response']['d_mm'] == .75 and response['continuation'] == continuation
        assert response['path']['full_extended_path_completed'] is False
        assert all(calls[kind+suffix] == 1 for kind in ('api', 'solve') for suffix in ('_started', '_completed'))
        assert saved['call_counts'] == receipt['production_call_counts']
        assert saved['call_counts']['solver_invocations'] == 1
        assert saved['call_counts']['HP_calls'] == saved['call_counts']['JIT_calls'] == 0
        for key, value in protocol['options'].items():
            assert response['invocation'][key] == value
''' +text[b:]
    text=text.replace('# Circular workpiece pilot: saved-state review', '# Circular workpiece explicit extension: saved-state review')
    text=text.replace('Solved lower-half wave mechanism, fixed raster circle r9 at (71,40) mm.',
        'Saved-terminal extension of lower-half wave mechanism: fixed raster circle r9 at (71,40) mm. The .50 mm first state is a freshly revalidated source anchor; only .75 mm is appended. Old zero-start prefix is inherited, not re-executed.')
    text=text.replace('Input zero-start 0/.25/.5 mm does not complete the original25 cycle, unloading, release, stability, ',
        'This .5/.75 mm child segment does not newly execute the complete 0/.25/.5/.75 prefix or original25 cycle, unloading, release, stability, ')
    text=text.replace("old_records_rewritten=False, new_mechanical_kernels=0, new_tests=0,", "old_records_rewritten=False, new_mechanical_kernels=0,")
    ast.parse(text)
    (AUTHOR/'execute_extension.py').write_text(text,encoding='utf-8',newline='\n')
    launch=(OLD/'launch_pilot.py').read_text(encoding='utf-8')
    old_request=launch.split("assert auth['direct_human_request'] == ",1)[1].split('\n',1)[0]
    launch=launch.replace(old_request,repr(REQUEST)).replace('L-CPILOT1','L-CEXT1').replace('_L_CPILOT1_','_L_CEXT1_')
    launch=launch.replace('execute_pilot.py','execute_extension.py').replace('pilot_launch.json','extension_launch.json').replace('pilot_stdout.log','extension_stdout.log').replace('pilot_instances.ndjson','extension_instances.ndjson')
    launch=launch.replace('2700','3000').replace('2760','3060').replace("protocol['source_bindings']","protocol['baseline_source_bindings']")
    launch=launch.replace('one prepared geometry NPZ binding belongs', 'prepared geometry and selected split NPZ bindings belong')
    launch=launch.replace('default_installations=0, new_tests=0','planned_default_installations=3, tests_seconds=180')
    ast.parse(launch)
    (AUTHOR/'launch_extension.py').write_text(launch,encoding='utf-8',newline='\n')
    for name in ('circle_saved_views.py','plot_convergence.py'):
        (AUTHOR/name).write_bytes((OLD/name).read_bytes())
    print('Study wrapper prepared; AST only. No default HF installation or tests/science.')

if __name__=='__main__': main()
