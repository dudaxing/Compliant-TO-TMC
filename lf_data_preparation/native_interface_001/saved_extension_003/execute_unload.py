"""One installed saved-path extension and one original pure viewer; no tests or install."""
from time import perf_counter, sleep
STARTED = perf_counter()
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
from math import fsum
import argparse
import json
import os
import subprocess
import sys

REL = 'lf_data_preparation/native_interface_001/saved_extension_003'
CARD = 'M-UNLOAD1'
SCHEMA = 'saved-native-default-unload-card-1.0'
LABEL = 'unloaded_alpha_half'
KINDS = ('api','defaults','model','reader','solve','force','tangent','save','summary','view_child')
MECHANICAL = ('force_started','force_completed','tangent_started','tangent_completed')


def sha(path, checkpoint=lambda: None):
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            checkpoint(); digest.update(block)
    checkpoint()
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    root, protocol_file = args.repo.resolve(), args.protocol.resolve()
    stage, run = root/REL, root/REL/'run_001'
    protocol = read(protocol_file)
    pins, limits = protocol['bindings'], protocol['phases']['production']
    assert protocol['schema_version'] == SCHEMA and protocol['card'] == CARD and protocol_file.parent == stage
    assert isinstance(protocol['source_baseline_commit'], str) and len(protocol['source_baseline_commit']) == 40
    assert (protocol['controller_seconds'],protocol['view_seconds'],limits['helper_seconds'],limits['outer_seconds'],protocol['sampled_RSS_bytes']) == (1800,600,2700,2760,8*1024**3)
    assert not run.exists() and not (stage/'stop_requested.txt').exists()
    proof_file = stage/'author/source_publication_receipt.json'
    auth, reply, proof = read(stage/'author/authorization.json'), read(stage/'author/direct_human_reply.json'), read(proof_file)
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert auth['card'] == reply['card'] == proof['prepared_card'] == CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit'] == head
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared'] is True
    assert proof['authorized'] is proof['executed'] is False
    assert proof['previous_delivery_commit'] == protocol['source_baseline_commit']
    assert proof['protocol_sha256'] == auth['protocol_sha256'] == sha(protocol_file)
    assert auth['human_evidence_sha256'] == sha(stage/'author/direct_human_reply.json')
    assert auth['source_publication_receipt_sha256'] == sha(proof_file)
    assert reply['direct_human_answer'].strip() and reply['reply_context'] and auth['direct_human_answer'] == reply['direct_human_answer']
    run.mkdir()
    production, view = root/protocol['candidate_directory'], root/protocol['view_directory']
    assert production == run/LABEL and view == run/'view'
    counts = {kind+suffix:0 for kind in KINDS for suffix in ('_started','_completed')}
    receipt_file, progress = run/'execution_receipt.json', run/'accepted_progress.jsonl'
    receipt = dict(schema_version='saved-native-default-unload-execution-1.0',status='running',
        protocol_sha256=sha(protocol_file),approved_source_commit=head,counts=counts,accepted_states=0,
        authorization_sha256=sha(stage/'author/authorization.json'),human_evidence_sha256=auth['human_evidence_sha256'],
        requested_absolute_targets_mm=[1.1,1.05],selected_state_index=1,selected_global_original_index=15,
        initial_K='None; original fresh F/T anchor validation',saved_force_tangent_matrix_fields_decoded=False,
        archive_count_scope='Frozen two-archive/six-field loader contract, not dynamic np.load hooks',
        HP_calls=0,JIT_calls=0,tests=0,candidate_copies=0,default_installations=0,
        mechanical_hooks_monitored=False,mechanical_hook_scope='Installed NativeMean aliases only; no universal hook claim',
        qualification_scope='New actual saved suffix and pure views only; no full path/reference/pressure/clamp/stability/HF5')
    write(receipt_file,receipt)
    error, peak, phase, TMCErrorClass = None, 0, 'bootstrap', None
    try:
        import psutil
        process = psutil.Process()
        def checkpoint():
            nonlocal peak
            memory = process.memory_info(); peak = max(peak,memory.rss,getattr(memory,'peak_wset',memory.rss))
            reason = ('external_stop_requested' if (stage/'stop_requested.txt').exists() else
                'sampled_RSS_limit' if peak > protocol['sampled_RSS_bytes'] else
                'whole_helper_elapsed_limit' if perf_counter()-STARTED > limits['helper_seconds'] else None)
            if reason is not None:
                receipt['resource_stop_reason'] = reason
                if TMCErrorClass is not None: raise TMCErrorClass(reason,code='time_limit')
                raise RuntimeError(reason)
        def observed(delegate, kind):
            def call(*values, **keywords):
                checkpoint(); counts[kind+'_started'] += 1
                before = tuple(counts[key] for key in MECHANICAL)
                value = delegate(*values,**keywords)
                counts[kind+'_completed'] += 1
                if kind in ('save','summary'):
                    assert before == tuple(counts[key] for key in MECHANICAL)
                    receipt[kind+'_extra_force_tangent_calls'] = 0
                checkpoint(); return value
            return call
        checkpoint()
        assert all(sha(root/name,checkpoint) == pin for name,pin in pins.items())
        parent_file, task_file = root/protocol['parent_result'], root/protocol['task_file']
        parent, task = read(parent_file), read(task_file)
        model = read(parent_file.parent/parent['model']['descriptor_path'])
        parent_protocol = read(root/protocol['parent_protocol'])
        selected = parent['states'][protocol['selected_state_index']]
        assert protocol['selected_state_index'] == 1 and len(parent['states']) == 2
        assert selected['original_target_index'] == 15 and selected['child_original_target_index'] == 1
        assert selected['d'] == selected['physical_mean_target_mm'] == 1.1 and selected['target_origin'] == 0.
        assert selected['is_original_target'] and selected['leg'] == 'unloading' and not selected['continuation_anchor']
        assert parent['status'] == 'success' and parent['failure'] is None and parent['path_completed']
        assert parent['continuation']['parent_status'] == 'success'
        assert parent['continuation']['parent_continuation']['parent_status'] == 'failed'
        assert parent['continuation']['parent_continuation']['parent_failure']['code'] == 'time_limit'
        assert protocol['targets_mm'] == [1.1,1.05] and task['path']['targets_mm'] == model['task']['path']['targets_mm']+[1.05]
        assert len(model['task']['path']['targets_mm']) == 16 and task['input']['target_mm'] == 1.2
        expected = deepcopy(task); expected['path']['targets_mm'] = model['task']['path']['targets_mm']
        assert expected == model['task'] and protocol['gates'] == parent_protocol['gates']
        assert protocol['options'] == dict(response_mode=parent['response_mode'],tangent_mode=parent['tangent_execution']['mode'],initial_guess=parent['initial_guess'])
        assert protocol['settings']['time_limit_seconds'] == 1800.
        assert {key:value for key,value in protocol['settings'].items() if key != 'time_limit_seconds'} == {key:value for key,value in parent['settings'].items() if key != 'time_limit_seconds'}
        receipt.update(parent_result=protocol['parent_result'],parent_status=parent['status'],parent_failure=parent['failure'],
            ancestor_continuation=deepcopy(parent['continuation']),selected_state_sha256=selected['state_sha256'])
        source = root/'hf_repo'
        sys.path.insert(0,str(source/'src'))
        from hf_eval import native_evaluate, native_mean
        from hf_eval.data import canonical_hash
        from hf_eval.tmc import TMCError
        TMCErrorClass = TMCError
        assert Path(native_evaluate.__file__).resolve() == source/'src/hf_eval/native_evaluate.py'
        assert Path(native_mean.__file__).resolve() == source/'src/hf_eval/native_mean.py'
        assert canonical_hash(task) == protocol['task_sha256'] and canonical_hash(model['task']) == parent['task_sha256'] == protocol['source_task_sha256']
        native_evaluate.saved_resume_defaults = observed(native_evaluate.saved_resume_defaults,'defaults')
        native_mean.saved_resume_defaults = observed(native_mean.saved_resume_defaults,'defaults')
        native_mean.read_native_resume = observed(native_mean.read_native_resume,'reader')
        native_mean._assemble_mechanical_force = observed(native_mean._assemble_mechanical_force,'force')
        native_mean._tangent_chunked = observed(native_mean._tangent_chunked,'tangent')
        original_model = native_mean.build_native_project
        def checked_model(*values,**keywords):
            project = original_model(*values,**keywords)
            expected_regions = deepcopy(model['region_metadata'])
            assert expected_regions['effective_boundary']['task_sha256'] == model['task_sha256']
            expected_regions['effective_boundary']['task_sha256'] = project.task_hash
            assert project.task == task and project.material == model['material']
            assert {key:value for key,value in project.region_metadata.items() if key != 'source_geometry'} == expected_regions
            assert project.region_metadata['source_geometry'] == model['source_geometry']
            assert counts['force_started'] == counts['tangent_started'] == 0
            receipt['same_model_physics_BC_material_checked_before_first_force'] = True
            return project
        native_mean.build_native_project = observed(checked_model,'model')
        native_evaluate.write_native_mean = observed(native_evaluate.write_native_mean,'save')
        native_evaluate.summarize_saved_native_result = observed(native_evaluate.summarize_saved_native_result,'summary')
        original_solve = native_evaluate.solve_native_mean
        def solve(*values,**keywords):
            def accepted(snapshot):
                row = {key:snapshot.record[key] for key in ('d','R_input','q_in','q_out','relative_residual',
                    'state_sha256','leg','original_target_index','is_original_target','child_original_target_index')}
                row.update(index=receipt['accepted_states'],elapsed_seconds=perf_counter()-STARTED)
                with progress.open('a',encoding='utf-8') as output: output.write(json.dumps(row,allow_nan=False)+'\n')
                receipt['accepted_states'] += 1; checkpoint()
            keywords['on_accept'] = accepted
            result = observed(original_solve,'solve')(*values,**keywords)
            rows = [snapshot.record for snapshot in result.accepted]
            minimum_J = min((float(snapshot.arrays['J'].min()) for snapshot in result.accepted),default=None)
            fixed = max((abs(fsum((float(snapshot.state.lift[i]),float(snapshot.state.fluctuation[i]))))
                for snapshot in result.accepted for i in result.project.model.fixed_dofs),default=0.)
            cached = dict(actual_accepted_states=len(rows),minimum_J=minimum_J,maximum_fixed_split_sum_mm=fixed,
                maximum_relative_residual=max((row['relative_residual'] for row in rows),default=0.),
                native_constraint_bound_pass=all(abs(row['constraint_residual']) <= row['constraint_bound'] for row in rows),
                maximum_relative_global_force_balance=max((row['relative_global_force_balance'] for row in rows),default=0.))
            gates = protocol['gates']
            cached['passed'] = bool(rows) and minimum_J > 0 and cached['maximum_relative_residual'] <= float(gates['production_residual']) and cached['native_constraint_bound_pass'] and cached['maximum_relative_global_force_balance'] <= float(gates['global_force_balance']) and fixed <= float(gates['fixed_displacement_mm'])
            receipt['cached_production_gates'] = cached
            return result  # Original typed controller failures continue through the single API saver.
        native_evaluate.solve_native_mean = solve
        phase = 'production'
        response = observed(native_evaluate.evaluate_native,'api')(None,task_file,production,repo_root=root,
            saved_result=parent_file,selected_state_index=1,extend_path=True,time_limit_seconds=protocol['controller_seconds'])
        receipt['response_status'], receipt['API_failure'] = response['status'], response.get('failure')
        if response['status'] != 'success': raise RuntimeError('Default extension API non-success; retain actual partial, no viewer')
        result = read(production/'result.json'); N = result['accepted_states']
        assert N >= 2 and N == len(result['states']) == receipt['accepted_states']
        assert result['status'] == 'success' and result['path_completed'] and result['unload_endpoint_reached']
        assert result['targets_mm'] == [1.1,1.05] and result['target_origin'] == 0.
        assert result['settings'] == protocol['settings'] and result['settings']['time_limit_seconds'] == 1800.
        for key in ('response_mode','tangent_mode','initial_guess'): assert response['invocation'][key] == protocol['options'][key]
        assert {key:value for key,value in result['settings'].items() if key != 'time_limit_seconds'} == {key:value for key,value in parent['settings'].items() if key != 'time_limit_seconds'}
        continuation = result['continuation']; assert response['continuation'] == continuation
        assert continuation['continuation_mode'] == 'explicit_task_extension' and continuation['parent_continuation'] == parent['continuation']
        for key in ('status','failure','path_completed','task_target_executed','unload_endpoint_reached'): assert continuation['parent_'+key] == parent[key]
        assert continuation['source_task_targets_mm'] == model['task']['path']['targets_mm'] and continuation['extended_task_targets_mm'] == task['path']['targets_mm']
        assert continuation['appended_targets_mm'] == [1.05] and continuation['original_target_indices'] == [15,16]
        assert continuation['segment_completed'] and continuation['anchor_revalidated'] and continuation['anchor_identity_preserved']
        assert continuation['full_original_path_executed_by_child'] is continuation['full_extended_path_executed_by_child'] is False
        assert result['full_original_path_completed'] is result['full_extended_path_completed'] is result['task_target_executed'] is False
        assert response['path']['full_original_path_completed'] is response['path']['full_extended_path_completed'] is False
        originals = [row for row in result['states'] if row['is_original_target']]
        assert [row['original_target_index'] for row in originals] == [15,16] and [row['d'] for row in originals] == [1.1,1.05]
        assert [row['child_original_target_index'] for row in originals] == [0,1]
        assert originals[0] is result['states'][0] and originals[-1] is result['states'][-1]
        assert originals[0]['state_sha256'] == selected['state_sha256'] and float(originals[0]['R_input']).hex() == float(selected['R_input']).hex()
        assert originals[0]['leg'] == 'resume_origin' and originals[0]['continuation_anchor']
        assert originals[-1]['leg'] == 'unloading' and not originals[-1]['continuation_anchor']
        assert receipt['cached_production_gates']['passed'] and all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status'] == response['views']['status'] == 'not_provided'
        assert response['independent_reference']['full_extended_path_reference_pass'] is False
        assert all(counts[kind+suffix] == 1 for kind in ('api','model','reader','solve','save','summary') for suffix in ('_started','_completed'))
        assert counts['defaults_started'] == counts['defaults_completed'] == 2
        for kind in ('force','tangent'):
            assert counts[kind+'_started'] == result['call_counts'][kind+'_calls']
            assert counts[kind+'_completed'] == result['call_counts'][kind+'_calls_completed']
        assert result['call_counts']['HP_calls'] == result['call_counts']['JIT_calls'] == 0
        receipt['call_counts'] = result['call_counts']
        origins = {name:str(Path(module.__file__).resolve()) for name,module in tuple(sys.modules.items()) if name == 'hf_eval' or name.startswith('hf_eval.')}
        assert all(Path(path).is_relative_to(source/'src/hf_eval') for path in origins.values())
        receipt['production_imported_HF_modules'] = origins
        checkpoint(); phase = 'viewer_binding'
        viewer_pins = dict(protocol['pure_view_bindings'])
        assert all(pins[name] == pin for name,pin in viewer_pins.items())
        def bind_new(path,expected=None):
            pin = sha(path,checkpoint); assert expected is None or expected == pin
            viewer_pins[path.relative_to(root).as_posix()] = pin
        bind_new(production/'result.json')
        model_file = production/result['model']['descriptor_path']; bind_new(model_file,result['model']['descriptor_file_sha256'])
        saved_model = read(model_file); bind_new(model_file.parent/saved_model['arrays']['path'],saved_model['arrays']['sha256'])
        for row in result['states']:
            bind_new(production/row['descriptor_path'],row['descriptor_file_sha256'])
            for key in ('state','forces'): bind_new(production/row[key]['path'],row[key]['sha256'])
        view_protocol = run/'view_protocol.json'
        write(view_protocol,dict(bindings=viewer_pins,scope='New actual default extension suffix; original pure viewer without reference'))
        remaining = min(protocol['view_seconds'],limits['helper_seconds']-(perf_counter()-STARTED))
        checkpoint(); assert remaining > 0
        argv = [sys.executable,'-B',str(root/protocol['viewer_source']),'--repo',str(source),'--protocol',str(view_protocol),
            '--output',str(view),'--case',LABEL+'='+str(production),'--stop-file',str(stage/'stop_requested.txt'),'--time-limit',str(remaining)]
        phase = 'viewer'; counts['view_child_started'] += 1; viewer_started = perf_counter(); child_stop = child_error = None
        env = dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',MPLBACKEND='Agg')
        with (run/'view_child_stdout.log').open('xb') as output:
            child = subprocess.Popen(argv,cwd=root,env=env,stdout=output,stderr=subprocess.STDOUT)
            try:
                while child.poll() is None:
                    try:
                        checkpoint()
                        if perf_counter()-viewer_started > remaining: raise RuntimeError('viewer_elapsed_limit')
                    except (RuntimeError,TMCError) as exception:
                        child_stop = child_stop or str(exception)
                        if not (stage/'stop_requested.txt').exists(): (stage/'stop_requested.txt').write_text(child_stop,encoding='utf-8')
                    sleep(.1)
            except BaseException as exception:
                child_error = exception; child_stop = child_stop or type(exception).__name__
            finally:
                if child.poll() is None:
                    try:
                        if not (stage/'stop_requested.txt').exists(): (stage/'stop_requested.txt').write_text(child_stop or 'viewer_interrupted',encoding='utf-8')
                    finally: child.wait()
        viewer_elapsed = perf_counter()-viewer_started
        if viewer_elapsed > remaining: child_stop = child_stop or 'viewer_elapsed_limit'
        if (stage/'stop_requested.txt').exists(): child_stop = child_stop or 'external_stop_requested'
        receipt['view_child_terminal'] = dict(exit_code=child.returncode,elapsed_seconds=viewer_elapsed,limit_seconds=remaining,stop_reason=child_stop,cleanup='Real cooperative child waited; no force or orphan')
        if child_error is not None: raise child_error
        if child.returncode != 0 or child_stop is not None: raise RuntimeError('Viewer non-success; production retained, whole card not_pass')
        counts['view_child_completed'] += 1; checkpoint()
        views = read(view/'view.json')
        assert views['status'] == 'pass' and all(views[key] == N for key in ('geometry_started','geometry_completed','nodal_started','nodal_completed'))
        assert views['new_F_T_model_solver_HP_calls'] == 0 and views['mechanical_hooks_monitored'] is False
        assert views['contact_pressure_clamping_qualified'] is False and len(views['cases']) == 1
        assert not views['cases'][0]['reference_available'] and views['cases'][0]['saved_accepted_states'] == N
        assert {path.relative_to(view).as_posix() for path in view.rglob('*.png')} == {'comparison.png','distances_forces.png','peak_fields.png'}
        assert LABEL+'/actual_states.gif' in views['outputs']
        receipt.update(view_actual_counts={key:views[key] for key in ('geometry_started','geometry_completed','nodal_started','nodal_completed')},
            view_NPZ_files=1+2*N,view_decoded_fields=27+18*N,actual_PNGs=3,actual_GIF_frames=N,
            GIF_frame_count_basis='Original successful viewer checks GIF n_frames against every actual accepted row',
            production_selected_NPZ_files=2,production_selected_fields=6,parent_and_ancestor_records_rewritten=False,
            new_HP_pressure_clamp_stability_HF5_qualified=False)
    except BaseException as exception:
        error = exception
        receipt['exception'] = dict(phase=phase,exception_class=type(exception).__name__,code=getattr(exception,'code',None),reason=str(exception))
    finally:
        phase = 'closure'
        # One seal in the original open resource window; never hash science after it closes.
        try:
            checkpoint()
            receipt['outputs'] = {}
            for path in run.rglob('*'):
                if path.is_file() and path != receipt_file:
                    receipt['outputs'][path.relative_to(root).as_posix()] = dict(sha256=sha(path,checkpoint),bytes=path.stat().st_size)
            receipt['all_bindings_unchanged'] = all(sha(root/name,checkpoint) == pin for name,pin in pins.items())
            assert receipt['all_bindings_unchanged']
            checkpoint()
            receipt['output_identity_seal'] = 'complete_inside_original_helper_window'
        except BaseException as exception:
            receipt['output_identity_seal'] = 'incomplete_or_skipped; preserve existing files, no closed-window hash retry'
            receipt['closure_exception'] = dict(exception_class=type(exception).__name__,code=getattr(exception,'code',None),reason=str(exception))
            error = error or exception
        receipt.update(status='pass' if error is None else 'not_pass',elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=peak,
            last_phase=phase,elapsed_scope='Whole helper earliest clock through imports, bootstrap, one API, cache/response save, one view and identity seal; before receipt write')
        write(receipt_file,receipt)
        try:
            if error is None: checkpoint()
        except BaseException as exception:
            error = exception; receipt.update(status='not_pass',final_write_stop=str(exception),elapsed_seconds=perf_counter()-STARTED); write(receipt_file,receipt)
        print(json.dumps({key:receipt[key] for key in ('status','accepted_states','elapsed_seconds','peak_sampled_RSS_bytes')},ensure_ascii=False),flush=True)
    if error is not None: raise error


if __name__ == '__main__': main()
