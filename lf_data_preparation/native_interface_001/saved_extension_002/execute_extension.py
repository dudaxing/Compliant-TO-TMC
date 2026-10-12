"""Future one-card tests, explicit saved extension, pure views, then same-byte install."""
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
from zipfile import ZipFile, ZIP_STORED

STAGE = 'lf_data_preparation/native_interface_001/saved_extension_002'
BASE = 'd7078c2e72ab6535794ff634cbb9b97325a472c6'
CARD = 'M-EXTEND2'
KINDS = ('focused_tests', 'api', 'defaults', 'model', 'reader', 'solve', 'force', 'tangent', 'save', 'summary', 'view_child', 'runtime_archive', 'installation')
MECHANICAL = ('force_started', 'force_completed', 'tangent_started', 'tangent_completed')


def sha(path):
    value = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    root, protocol_file = args.repo.resolve(), args.protocol.resolve()
    stage, run = root / STAGE, root / STAGE / 'run_001'
    protocol = read(protocol_file)
    pins, limits = protocol['bindings'], protocol['phases']['production']
    transitions = protocol['installation']
    targets, options, settings = protocol['targets_mm'], protocol['options'], protocol['settings']
    parent_file, task_file = root / protocol['parent_result'], root / protocol['task_file']
    parent, task = read(parent_file), read(task_file)
    parent_model = read(parent_file.parent / parent['model']['descriptor_path'])
    parent_protocol = read(root / protocol['parent_protocol'])
    selected = parent['states'][protocol['selected_state_index']]
    assert protocol['schema_version'] == 'saved-native-explicit-extension-card-1.0'
    assert protocol_file.parent == stage and protocol['card'] == CARD and protocol['source_baseline_commit'] == BASE
    assert protocol['selected_state_index'] == 1 and selected['original_target_index'] == 14
    assert targets == [1.15, 1.1] and selected['d'] == selected['physical_mean_target_mm'] == targets[0]
    assert selected['target_origin'] == 0.0 and selected['is_original_target'] is True
    assert parent['status'] == 'success' and parent['failure'] is None and parent['path_completed'] is True
    assert parent['continuation']['parent_status'] == 'failed' and parent['continuation']['parent_failure']['code'] == 'time_limit'
    assert (options['response_mode'], options['tangent_mode'], options['initial_guess']) == ('mechanical', 'chunk256', 'port_projection')
    assert settings['time_limit_seconds'] == 1800.0
    assert {k:v for k,v in settings.items() if k != 'time_limit_seconds'} == {k:v for k,v in parent['settings'].items() if k != 'time_limit_seconds'}
    assert (limits['helper_seconds'], limits['outer_seconds'], protocol['focused_tests_seconds'], protocol['view_seconds']) == (3000, 3060, 180, 600)
    assert protocol['sampled_RSS_bytes'] == 8 * 1024**3 and protocol['gates'] == parent_protocol['gates']
    assert {name:float(value) for name,value in protocol['gates'].items()} == dict(production_residual=1e-9,
        average_constraint=1e-10, global_force_balance=1e-6, fixed_displacement_mm=8e-11)
    assert len(transitions) == len({row['target'] for row in transitions}) == 6
    assert not {row['target'] for row in transitions} & set(pins)
    assert all(sha(root / name) == pin for name,pin in pins.items())
    assert all(sha(root / row['target']) == row['old_sha256'] and sha(root / row['candidate_source']) == row['new_sha256'] for row in transitions)
    authorization, reply = read(stage / 'author/authorization.json'), read(stage / 'author/direct_human_reply.json')
    proof_file = stage / 'author/M_EXTEND2_source_publication_receipt.json'
    proof = read(proof_file)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert authorization['authorized'] is True and authorization['card'] == reply['card'] == CARD
    assert authorization['approved_source_commit'] == reply['approved_source_commit'] == proof['published_commit'] == head
    assert authorization['protocol_sha256'] == sha(protocol_file)
    assert authorization['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert authorization['human_evidence_sha256'] == sha(stage / 'author/direct_human_reply.json')
    assert authorization['source_publication_receipt_sha256'] == sha(proof_file)
    assert reply['direct_human_answer'].strip() and reply['reply_context'] and authorization['direct_human_answer'] == reply['direct_human_answer']
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared_card'] == CARD
    assert proof['prepared'] is True and proof['authorized'] is False and proof['executed'] is False
    assert not run.exists() and not (stage / 'stop_requested.txt').exists()
    run.mkdir()
    candidate, view = root / protocol['candidate_directory'], root / protocol['view_directory']
    assert candidate == run / 'extended_alpha_half' and view == run / 'view'
    runtime = Path(protocol['runtime_root']).resolve()
    assert runtime == Path('D:/hf-extend2-runtime-20261012').resolve()
    assert not runtime.is_relative_to(root) and not root.is_relative_to(runtime) and not runtime.exists()
    capsule, source = runtime/'repo', runtime/'repo/hf_repo'
    assert protocol['runtime_archive'] == (run/'runtime_capsule.zip').relative_to(root).as_posix()
    counts = {kind+suffix:0 for kind in KINDS for suffix in ('_started', '_completed')}
    receipt_file, progress = run / 'execution_receipt.json', run / 'accepted_progress.jsonl'
    receipt = dict(schema_version='saved-native-explicit-extension-execution-1.0', status='running',
        protocol_sha256=sha(protocol_file), approved_source_commit=head,
        authorization_sha256=sha(stage / 'author/authorization.json'), human_evidence_sha256=authorization['human_evidence_sha256'],
        counts=counts, accepted_states=0, parent_result=protocol['parent_result'], selected_state_index=1,
        parent_status=parent['status'], parent_failure=parent['failure'], ancestor_continuation=deepcopy(parent['continuation']),
        requested_absolute_targets_mm=targets, target_origin=0.0, initial_parameter=targets[0],
        initial_K='None; fresh F/T anchor validation', saved_force_tangent_matrix_fields_decoded=False,
        archive_count_scope='Distinct frozen loader/archive-field contract; not dynamic np.load instrumentation',
        installed_transitions=[], HP_calls=0, JIT_calls=0, mechanical_hooks_monitored=False,
        mechanical_hook_scope='Production NativeMean aliases only; isolated test aliases separately accounted; no universal hook claim',
        qualification_scope='Explicit child extension and cached views only; no full old/new path, HP, pressure, clamp, stability or HF5 qualification',
        external_runtime_root=str(runtime), capsule_root=str(capsule), test_tmp_root=str(runtime/'test_tmp'),
        external_runtime_created=False, runtime_preserved=True, runtime_archive_cleanup_scope='One raw-byte evidence archive; no scientific decode or phase retry')
    write(receipt_file, receipt)
    error, peak = None, 0
    try:
        import psutil
        process = psutil.Process()
        def checkpoint():
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
            if (stage / 'stop_requested.txt').exists():
                raise RuntimeError('external_stop_requested')
            if peak > protocol['sampled_RSS_bytes'] or perf_counter()-STARTED > limits['helper_seconds']:
                raise RuntimeError('whole_helper_resource_limit')

        def observed(delegate, kind):
            def call(*values, **keywords):
                checkpoint(); counts[kind+'_started'] += 1
                before = tuple(counts[key] for key in MECHANICAL)
                value = delegate(*values, **keywords)
                counts[kind+'_completed'] += 1
                if kind in ('save', 'summary'):
                    assert before == tuple(counts[key] for key in MECHANICAL)
                    receipt[kind+'_extra_force_tangent_calls'] = 0
                checkpoint()
                return value
            return call

        def child(argv, cwd, name, seconds, env=None):
            checkpoint(); counts[name+'_started'] += 1
            start, child_stop, child_error = perf_counter(), None, None
            with (run / (name+'_stdout.log')).open('xb') as output:
                child_process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
                try:
                    while child_process.poll() is None:
                        try:
                            checkpoint()
                            if perf_counter()-start > seconds:
                                raise RuntimeError(name+'_elapsed_limit')
                        except RuntimeError as exception:
                            child_stop = child_stop or str(exception)
                            if not (stage / 'stop_requested.txt').exists():
                                (stage / 'stop_requested.txt').write_text(child_stop, encoding='utf-8')
                        sleep(.1)
                except BaseException as exception:
                    child_error = exception; child_stop = child_stop or type(exception).__name__
                finally:
                    if child_process.poll() is None:
                        try:
                            if not (stage / 'stop_requested.txt').exists():
                                (stage / 'stop_requested.txt').write_text(child_stop or name+'_interrupted', encoding='utf-8')
                        finally:
                            child_process.wait()  # Original cooperative child; no force and no orphan.
            elapsed = perf_counter()-start
            if elapsed > seconds: child_stop = child_stop or name+'_elapsed_limit'
            receipt[name+'_terminal'] = dict(exit_code=child_process.returncode, elapsed_seconds=elapsed,
                stop_reason=child_stop, limit_seconds=seconds, cleanup='Real child exited; no force')
            if child_error is not None: raise child_error
            if child_process.returncode != 0 or child_stop is not None: raise RuntimeError(name+'_terminal_non_success')
            counts[name+'_completed'] += 1; checkpoint()

        def archive_runtime(mode):
            # This is raw evidence closure, never a numerical phase or a retry.
            assert counts['runtime_archive_started']==0
            checkpoint(); counts['runtime_archive_started']=1
            archive = run/'runtime_capsule.zip'
            record = dict(mode=mode,status='running',path=archive.relative_to(root).as_posix(),members=[])
            receipt['runtime_archive']=record
            try:
                paths=sorted(path for path in runtime.rglob('*') if path.is_file())
                members={path.relative_to(runtime).as_posix() for path in paths}
                capsule_members={path.relative_to(capsule).as_posix() for path in capsule.rglob('*') if path.is_file()}
                if mode=='success_before_installation': assert capsule_members==set(package)==set(protocol['source_package']['files'])
                record['capsule_relative_source_SHA256']=dict(package)
                record['capsule_source_files_present']=len(capsule_members)
                assert not archive.resolve().is_relative_to(runtime)
                with ZipFile(archive,'x',compression=ZIP_STORED) as output:
                    for path in paths:
                        checkpoint(); path.resolve().relative_to(runtime)
                        name=path.relative_to(runtime).as_posix(); digest=sha256(); size=0
                        with path.open('rb') as source_stream, output.open(name,'w') as target_stream:
                            for block in iter(lambda:source_stream.read(1024*1024),b''):
                                checkpoint(); target_stream.write(block); digest.update(block); size+=len(block)
                        assert path.stat().st_size==size
                        pin=digest.hexdigest()
                        if name.startswith('repo/') and name[5:] in package: assert pin==package[name[5:]]
                        record['members'].append(dict(path=name,bytes=size,sha256=pin))
                with ZipFile(archive) as saved:
                    assert set(saved.namelist())==members and len(saved.namelist())==len(members)
                    for row in record['members']:
                        checkpoint(); digest=sha256()
                        with saved.open(row['path']) as stream:
                            for block in iter(lambda:stream.read(1024*1024),b''):
                                checkpoint(); digest.update(block)
                        assert saved.getinfo(row['path']).file_size==row['bytes'] and digest.hexdigest()==row['sha256']
                assert {path.relative_to(runtime).as_posix() for path in runtime.rglob('*') if path.is_file()}==members
                assert all(sha(runtime/row['path'])==row['sha256'] for row in record['members'])
                record.update(status='pass',sha256=sha(archive),exact_members=len(members),uncompressed_bytes=sum(row['bytes'] for row in record['members']))
                write(run/'runtime_archive_manifest.json',record)
                checkpoint(); counts['runtime_archive_completed']=1
            except BaseException as exception:
                record.update(status='not_pass',exception=dict(exception_class=type(exception).__name__,reason=str(exception)),partial_zip_exists=archive.exists())
                raise

        checkpoint()
        package = {}
        runtime.mkdir(); receipt['external_runtime_created']=True
        write(receipt_file,receipt)
        receipt['executed_source_package_SHA256']=package
        modules = {'hf_repo/src/hf_eval/'+path.name for path in (root/'hf_repo/src/hf_eval').glob('*.py')}
        files = protocol['source_package']['files']
        assert {name for name in files if name.startswith('hf_repo/src/hf_eval/')} == modules
        assert len(modules) == 52 and 'extension_focused_budget.py' in files
        assert len(protocol['focused_test_selectors']) == len(set(protocol['focused_test_selectors'])) == 36
        for name,spec in files.items():
            checkpoint(); destination = (capsule/name).resolve(); destination.relative_to(capsule.resolve())
            assert destination.suffix.lower() not in ('.npz', '.npy', '.gz', '.csv')
            assert spec['sha256'] == pins[spec['path']] == sha(root/spec['path'])
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as output: output.write((root/spec['path']).read_bytes())
            assert sha(destination) == spec['sha256']; package[destination.relative_to(capsule).as_posix()] = spec['sha256']
        receipt['executed_source_package_SHA256'] = package
        receipt['source_package_scope'] = 'Capsule-relative 90file SHA manifest plus explicit ephemeral absolute origin; unchanged source/layout/fixtures, no old arrays copied.'
        assert len(package)==90 and {path.relative_to(capsule).as_posix() for path in capsule.rglob('*') if path.is_file()}==set(package)
        remaining = min(protocol['focused_tests_seconds'], limits['helper_seconds']-(perf_counter()-STARTED))
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg',
            HF_EXTENSION_ROOT=str(capsule), HF_EXTENSION_STAGE=str(stage), HF_EXTENSION_PROTOCOL=str(protocol_file),
            HF_EXTENSION_TEST_SECONDS=str(remaining), HF_EXTENSION_TEST_RECEIPT=str(run/'focused_test_receipt.json'),
            HF_INTERFACE_TEST_REPO=str(capsule), HF_BATCH_TEST_REPO=str(capsule),
            PYTHONPATH=os.pathsep.join((str(capsule),str(source/'src'),str(source/'tests'))))
        argv = [sys.executable, '-B', '-m', 'pytest', '-q', '-x', '--rootdir='+str(capsule),
            '-c', str(source/'pyproject.toml'), '-p', 'extension_focused_budget',
            '--basetemp='+str(runtime/'test_tmp'), '--junitxml='+str(run/'test_results.xml'),
            '-o', 'cache_dir='+str(runtime/'pytest_cache'), *protocol['focused_test_selectors']]
        receipt['test_argv'] = argv
        child(argv,capsule,'focused_tests',remaining,env)
        tests = read(run/'focused_test_receipt.json')
        assert tests['status'] == 'pass' and tests['collected_selectors'] == protocol['focused_test_selectors']
        assert tests['passed_calls'] == 36 and len(tests['reports']) == 108 and all(row['outcome']=='passed' and not row['wasxfail'] for row in tests['reports'])
        receipt['focused_test_receipt_sha256'] = sha(run/'focused_test_receipt.json')
        assert all(sha(capsule/name)==pin for name,pin in package.items())
        sys.path.insert(0,str(source/'src'))
        from hf_eval import native_evaluate, native_mean
        from hf_eval.data import canonical_hash
        from hf_eval.displacement import DisplacementSettings
        assert Path(native_mean.__file__).resolve() == source/'src/hf_eval/native_mean.py'
        assert Path(native_evaluate.__file__).resolve() == source/'src/hf_eval/native_evaluate.py'
        assert canonical_hash(task) == protocol['task_sha256'] == '94671c3226afb193349324a91f15bd55923ba73e662e9ad76528c844000f74f6'
        assert canonical_hash(parent_model['task']) == parent['task_sha256'] == 'a343fbb97238fced66f57eefc8f8b8f8409f9db7168968449cf43f661769781b'
        assert task['path']['targets_mm'] == parent_model['task']['path']['targets_mm']+[1.1]
        expected_task = deepcopy(task); expected_task['path']['targets_mm'] = parent_model['task']['path']['targets_mm']
        assert expected_task == parent_model['task']
        native_evaluate.saved_resume_defaults = observed(native_evaluate.saved_resume_defaults,'defaults')
        native_mean.saved_resume_defaults = observed(native_mean.saved_resume_defaults,'defaults')
        native_mean.read_native_resume = observed(native_mean.read_native_resume,'reader')
        native_mean._assemble_mechanical_force = observed(native_mean._assemble_mechanical_force,'force')
        native_mean._tangent_chunked = observed(native_mean._tangent_chunked,'tangent')
        original_model = native_mean.build_native_project
        def checked_model(*values, **keywords):
            project = original_model(*values, **keywords)
            expected = deepcopy(parent_model['region_metadata'])
            assert expected['effective_boundary']['task_sha256'] == parent_model['task_sha256']
            expected['effective_boundary']['task_sha256'] = project.task_hash
            assert project.task == task and project.material == parent_model['material']
            assert {k:v for k,v in project.region_metadata.items() if k!='source_geometry'} == expected
            assert project.region_metadata['source_geometry'] == parent_model['source_geometry']
            assert counts['force_started'] == counts['tangent_started'] == 0
            receipt['same_model_physics_BC_material_checked_before_first_force'] = True
            return project
        native_mean.build_native_project = observed(checked_model,'model')
        native_evaluate.write_native_mean = observed(native_evaluate.write_native_mean,'save')
        native_evaluate.summarize_saved_native_result = observed(native_evaluate.summarize_saved_native_result,'summary')
        original_solve = native_evaluate.solve_native_mean
        def solve(*values, **keywords):
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
            cached = dict(actual_accepted_states=len(rows),minimum_J=minimum_J,
                maximum_relative_residual=max((row['relative_residual'] for row in rows),default=0.),
                maximum_abs_constraint_residual_mm=max((abs(row['constraint_residual']) for row in rows),default=0.),
                native_constraint_bound_pass=all(abs(row['constraint_residual'])<=row['constraint_bound'] for row in rows),
                maximum_relative_global_force_balance=max((row['relative_global_force_balance'] for row in rows),default=0.),
                maximum_fixed_split_sum_mm=fixed)
            gates = protocol['gates']
            cached['passed'] = bool(rows) and minimum_J>0 and cached['maximum_relative_residual']<=float(gates['production_residual']) and cached['native_constraint_bound_pass'] and cached['maximum_relative_global_force_balance']<=float(gates['global_force_balance']) and fixed<=float(gates['fixed_displacement_mm'])
            receipt['cached_production_gates'] = cached
            return result  # Original typed failures still persist through the single public API.
        native_evaluate.solve_native_mean = solve
        response = observed(native_evaluate.evaluate_native,'api')(None,task_file,candidate,repo_root=root,
            saved_result=parent_file,selected_state_index=1,targets=targets,extend_path=True,
            settings=DisplacementSettings(**settings),**options)
        receipt['response_status'],receipt['API_failure'] = response['status'],response.get('failure')
        if response['status']!='success': raise RuntimeError('Explicit-extension API non-success; actual partial persistence retained, no view or installation')
        result = read(candidate/'result.json'); N = result['accepted_states']
        assert N >= 2 and N == len(result['states']) == receipt['accepted_states']
        assert result['status']=='success' and result['path_completed'] and result['unload_endpoint_reached']
        assert result['targets_mm']==targets and result['target_origin']==0. and result['settings']==settings
        assert result['task_sha256']==protocol['task_sha256'] and result['scope']=='native_saved_mean_explicit_task_extension_segment'
        continuation = result['continuation']; assert response['continuation']==continuation
        assert continuation['continuation_mode']=='explicit_task_extension' and continuation['parent_continuation']==parent['continuation']
        for key in ('status','failure','path_completed','task_target_executed','unload_endpoint_reached'):
            assert continuation['parent_'+key] == parent[key]
        assert continuation['source_task_sha256']==parent['task_sha256'] and continuation['extended_task_sha256']==result['task_sha256']
        assert continuation['source_task_targets_mm']==parent_model['task']['path']['targets_mm']
        assert continuation['extended_task_targets_mm']==task['path']['targets_mm'] and continuation['appended_targets_mm']==[1.1]
        assert continuation['segment_completed'] and continuation['anchor_revalidated'] and continuation['anchor_identity_preserved']
        assert continuation['original_target_indices']==[14,15]
        assert continuation['full_original_path_executed_by_child'] is False and continuation['full_extended_path_executed_by_child'] is False
        assert result['full_original_path_completed'] is result['full_extended_path_completed'] is result['task_target_executed'] is False
        assert response['path']['full_original_path_completed'] is response['path']['full_extended_path_completed'] is False
        assert response['independent_reference']['full_extended_path_reference_pass'] is False
        originals = [row for row in result['states'] if row['is_original_target']]
        assert [row['original_target_index'] for row in originals]==[14,15] and [row['d'] for row in originals]==targets
        assert [row['child_original_target_index'] for row in originals]==[0,1]
        assert originals[0] is result['states'][0] and originals[-1] is result['states'][-1]
        assert originals[0]['state_sha256']==selected['state_sha256'] and float(originals[0]['R_input']).hex()==float(selected['R_input']).hex()
        assert originals[0]['leg']=='resume_origin' and originals[0]['continuation_anchor'] is True
        assert originals[-1]['leg']=='unloading' and originals[-1]['continuation_anchor'] is False
        assert continuation['selected_state']['accepted_index']==1 and continuation['selected_state']['original_target_index']==14
        assert receipt['cached_production_gates']['passed'] and all(value is False for value in response['producer_flags'].values())
        assert response['independent_reference']['status']==response['views']['status']=='not_provided'
        assert all(counts[kind+suffix]==1 for kind in ('api','model','reader','solve','save','summary') for suffix in ('_started','_completed'))
        assert counts['defaults_started']==counts['defaults_completed']==2
        for kind in ('force','tangent'):
            assert counts[kind+'_started']==result['call_counts'][kind+'_calls']
            assert counts[kind+'_completed']==result['call_counts'][kind+'_calls_completed']
        assert result['call_counts']['HP_calls']==result['call_counts']['JIT_calls']==0
        receipt['call_counts'] = result['call_counts']
        origins = {name:str(Path(module.__file__).resolve()) for name,module in tuple(sys.modules.items()) if name=='hf_eval' or name.startswith('hf_eval.')}
        assert all(Path(path).is_relative_to(source/'src/hf_eval') for path in origins.values())
        receipt['production_imported_HF_modules'] = origins
        checkpoint(); viewer_pins = dict(protocol['pure_view_bindings'])
        assert all(pins[name]==pin for name,pin in viewer_pins.items())
        for name in ('__init__','native_region_geometry','boundary_geometry','workpiece_nodal'):
            path = 'hf_repo/src/hf_eval/'+name+'.py'
            assert sha(root/path)==sha(capsule/path)==viewer_pins[path]
        def bind_new(path,expected=None):
            pin=sha(path); assert expected is None or pin==expected; viewer_pins[path.relative_to(root).as_posix()] = pin
        bind_new(candidate/'result.json')
        model_file = candidate/result['model']['descriptor_path']; bind_new(model_file,result['model']['descriptor_file_sha256'])
        model = read(model_file); bind_new(model_file.parent/model['arrays']['path'],model['arrays']['sha256'])
        for row in result['states']:
            bind_new(candidate/row['descriptor_path'],row['descriptor_file_sha256'])
            for key in ('state','forces'): bind_new(candidate/row[key]['path'],row[key]['sha256'])
        view_protocol = run/'view_protocol.json'; write(view_protocol,dict(bindings=viewer_pins,scope='New explicit extension segment, pure original viewer, no independent reference'))
        remaining = min(protocol['view_seconds'],limits['helper_seconds']-(perf_counter()-STARTED))
        child([sys.executable,'-B',str(root/protocol['viewer_source']),'--repo',str(root/'hf_repo'),
            '--protocol',str(view_protocol),'--output',str(view),'--case','extended_alpha_half='+str(candidate),
            '--stop-file',str(stage/'stop_requested.txt'),'--time-limit',str(remaining)],root,'view_child',remaining)
        views = read(view/'view.json')
        assert views['status']=='pass' and all(views[name]==N for name in ('geometry_started','geometry_completed','nodal_started','nodal_completed'))
        assert views['new_F_T_model_solver_HP_calls']==0 and views['mechanical_hooks_monitored'] is False
        assert views['contact_pressure_clamping_qualified'] is False and len(views['cases'])==1
        assert views['cases'][0]['reference_available'] is False and views['cases'][0]['saved_accepted_states']==N
        assert {path.relative_to(view).as_posix() for path in view.rglob('*.png')}=={'comparison.png','distances_forces.png','peak_fields.png'}
        from PIL import Image
        with Image.open(view/'extended_alpha_half/actual_states.gif') as gif: assert gif.n_frames==N
        receipt.update(view_actual_counts={name:views[name] for name in ('geometry_started','geometry_completed','nodal_started','nodal_completed')},
            view_NPZ_files=1+2*N,view_decoded_fields=27+18*N,actual_PNGs=3,actual_GIF_frames=N,
            production_selected_NPZ_files=2,production_selected_fields=6,source_pure_scope_separated=True,
            parent_and_ancestor_records_rewritten=False,new_HP_pressure_clamp_stability_HF5_qualified=False)
        checkpoint()
        assert all(sha(root/name)==pin for name,pin in pins.items()) and all(sha(capsule/name)==pin for name,pin in package.items())
        archive_runtime('success_before_installation')
        assert receipt['runtime_archive']['status']=='pass' and counts['runtime_archive_completed']==1
        for row in transitions:
            checkpoint(); target = root/row['target']; tested = capsule/row['target']
            assert sha(target)==row['old_sha256'] and sha(tested)==sha(root/row['candidate_source'])==row['new_sha256']
            counts['installation_started'] += 1
            with target.open('wb') as output: output.write(tested.read_bytes())
            installed = sha(target)
            receipt['installed_transitions'].append(dict(target=row['target'],old_sha256=row['old_sha256'],new_sha256=row['new_sha256'],actual_sha256=installed))
            assert installed==row['new_sha256']; counts['installation_completed'] += 1; checkpoint()
        assert all(sha(root/row['target'])==sha(capsule/row['target'])==row['new_sha256'] for row in transitions)
    except BaseException as exception:
        error=exception; receipt['exception']=dict(exception_class=type(exception).__name__,code=getattr(exception,'code',None),reason=str(exception))
    finally:
        if error is not None and receipt['external_runtime_created'] and counts['runtime_archive_started']==0:
            if not (stage/'stop_requested.txt').exists() and perf_counter()-STARTED<=limits['helper_seconds']:
                try: archive_runtime('failure_partial_cleanup')
                except BaseException as exception:
                    receipt['partial_archive_exception']=dict(exception_class=type(exception).__name__,reason=str(exception))
            else: receipt['partial_archive_skipped']='Original stop/whole resource window closed; external runtime partial retained, no extension'
        try:
            receipt['outputs']={path.relative_to(root).as_posix():sha(path) for path in run.rglob('*') if path.is_file() and path!=receipt_file}
            receipt['all_bindings_unchanged']=all(sha(root/name)==pin for name,pin in pins.items())
            assert receipt['all_bindings_unchanged']
            if 'executed_source_package_SHA256' in receipt:
                receipt['executed_source_package_unchanged']=all(sha(capsule/name)==pin for name,pin in package.items())
                assert receipt['executed_source_package_unchanged']
            receipt['actual_default_SHA256']={row['target']:sha(root/row['target']) for row in transitions}
            receipt['installation_complete']=all(receipt['actual_default_SHA256'][row['target']]==row['new_sha256'] for row in transitions)
            if error is None: assert receipt['installation_complete'] and counts['installation_completed']==6 and counts['runtime_archive_completed']==1
            if 'checkpoint' in locals(): checkpoint()
        except BaseException as exception:
            receipt['finalization_exception']=dict(exception_class=type(exception).__name__,reason=str(exception)); error=error or exception
        receipt.update(status='pass' if error is None else 'not_pass',elapsed_seconds=perf_counter()-STARTED,
            peak_sampled_RSS_bytes=peak,elapsed_scope='Whole helper from earliest clock including bootstrap, copy, tests, API, persistence, views, runtime archival, installation, final hash; before receipt write')
        write(receipt_file,receipt)
        try:
            if error is None: checkpoint()
        except BaseException as exception:
            error=exception; receipt.update(status='not_pass',final_write_stop=str(exception),elapsed_seconds=perf_counter()-STARTED); write(receipt_file,receipt)
        print(json.dumps({key:receipt[key] for key in ('status','accepted_states','elapsed_seconds','peak_sampled_RSS_bytes')},ensure_ascii=False),flush=True)
    if error is not None: raise error


if __name__=='__main__': main()
