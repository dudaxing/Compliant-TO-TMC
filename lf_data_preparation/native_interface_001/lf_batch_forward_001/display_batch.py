"""One saved two-case display after successful L-BFWD1 production only."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep


STATE_FIELDS = (
    'original_target_index', 'leg', 'd', 'R_input', 'q_in', 'q_out',
    'relative_residual', 'constraint_residual', 'constraint_bound', 'minimum_J',
    'relative_global_force_balance', 'newton_checks', 'bisection_depth',
    'is_original_target', 'original_target_displacement', 'state_sha256', 'workpiece',
)
PURE_SOURCES = (
    'hf_repo/scripts/measure_native_workpiece_regions.py',
    'hf_repo/src/hf_eval/__init__.py',
    'hf_repo/src/hf_eval/boundary_geometry.py',
    'hf_repo/src/hf_eval/native_region_geometry.py',
    'hf_repo/src/hf_eval/workpiece_nodal.py',
)


def run_display(ROOT, STAGE, protocol, index, checkpoint):
    """Use one shared display clock; propagate every error without a rerun.

    The helper supplies runtime_helper_deadline as a monotonic deadline in the
    in-memory protocol. No clock or scientific data are inferred from old files.
    Only the original clean viewer child decodes new saved NPZ/media payloads.
    """
    ROOT, STAGE = Path(ROOT).resolve(), Path(STAGE).resolve()
    run = (ROOT/protocol['output_directory']).resolve()
    started = monotonic()
    assert protocol['viewer_seconds'] == 600
    deadline = min(started+protocol['viewer_seconds'], protocol['runtime_helper_deadline'])
    assert index['status'] == 'success' and len(index['cases']) == 2
    assert all(case['status'] == 'success' for case in index['cases'])
    stop_file = STAGE/'stop_requested.txt'
    cache = {}

    def check(event='resource_check'):
        checkpoint(event)
        if monotonic() >= deadline:
            raise RuntimeError('L-BFWD1 shared display window exhausted')

    def relative(path):
        return Path(path).resolve().relative_to(ROOT).as_posix()

    def read_json(path, expected=None):
        path = Path(path).resolve()
        if path not in cache:
            check('display_json_read_started')
            raw = path.read_bytes()
            cache[path] = (json.loads(raw), sha256(raw).hexdigest())
            check('display_json_read_completed')
        value, pin = cache[path]
        if expected is not None and pin != expected:
            raise ValueError('Display ordinary JSON identity differs: '+str(path))
        return value

    def write_json(path, value, event):
        check()
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        check(event)

    def projection(row):
        return {key: row[key] for key in STATE_FIELDS if key in row}

    check('display_started')
    viewer_source = protocol['viewer_source']
    bindings = {name: protocol['source_bindings'][name] for name in (viewer_source,)+PURE_SOURCES}
    manifest_file = (ROOT/protocol['manifest_file']).resolve()
    manifest = read_json(manifest_file)
    assert [row['label'] for row in manifest['cases']] == [row['label'] for row in index['cases']]
    cases, arrays = [], set()
    for ordinal, entry in enumerate(index['cases']):
        check()
        directory = (ROOT/entry['output']['path']).resolve()
        assert directory == run/'cases'/f'{ordinal:03d}'
        result_file, response_file = directory/'result.json', directory/'response.json'
        result, response = read_json(result_file), read_json(response_file)
        assert result['status'] == response['status'] == 'success'
        N = result['accepted_states']
        assert N == len(result['states']) and N >= 3
        assert response['identity']['result']['sha256'] == cache[result_file][1]
        model_file = directory/result['model']['descriptor_path']
        model = read_json(model_file, result['model']['descriptor_file_sha256'])
        bindings[relative(result_file)] = cache[result_file][1]
        bindings[relative(model_file)] = cache[model_file.resolve()][1]
        model_array = model_file.parent/model['arrays']['path']
        bindings[relative(model_array)] = model['arrays']['sha256']
        arrays.add(relative(model_array))
        decoded_fields = len(model['arrays']['fields'])
        for row in result['states']:
            bindings[relative(directory/row['descriptor_path'])] = row['descriptor_file_sha256']
            for name in ('state', 'forces'):
                path = relative(directory/row[name]['path'])
                bindings[path] = row[name]['sha256']
                arrays.add(path)
                decoded_fields += len(row[name]['fields'])
        old_path = (ROOT/protocol['old_prefix_results'][entry['label']]).resolve()
        old = read_json(old_path, protocol['input_bindings'][relative(old_path)])
        old_rows = {(row['original_target_index'], row['leg'], row['d']): projection(row)
                    for row in old['states'] if row['is_original_target'] and row['original_target_index'] < 3}
        cases.append(dict(label=entry['label'], ordinal=ordinal, directory=directory,
            result_file=result_file, response_file=response_file, model_file=model_file,
            result=result, response=response, model=model, accepted_states=N,
            decoded_fields=decoded_fields, old_result=old, old_result_file=old_path, old_rows=old_rows))
    view_protocol = run/'view_protocol.json'
    write_json(view_protocol, dict(bindings=bindings,
        scope='New two-design short loading saved observations only; no independent reference'),
        'view_protocol_written')
    check()
    remaining = deadline-monotonic()
    assert remaining > 0
    view = run/'view'
    argv = [sys.executable, '-X', 'utf8', '-B', str(ROOT/viewer_source),
        '--repo', str(ROOT/'hf_repo'), '--protocol', str(view_protocol), '--output', str(view),
        '--stop-file', str(stop_file), '--time-limit', str(remaining)]
    for case in cases:
        argv += ['--case', case['label']+'='+str(case['directory'])]
    cwd = Path(protocol['working_directory']).resolve()
    assert cwd.is_dir() and not cwd.is_relative_to(ROOT)
    check('viewer_started')
    viewer_started = monotonic()
    with (run/'viewer_stdout.log').open('xb') as log:
        child = subprocess.Popen(argv, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', MPLBACKEND='Agg'))
        try:
            while child.poll() is None:
                check()
                sleep(.05)
        except BaseException as error:
            if not stop_file.exists():
                stop_file.write_text(type(error).__name__+': '+str(error), encoding='utf-8')
            child.wait()  # Original cooperative viewer; outer SUP2 retains owned-Job cleanup.
            raise
    viewer_elapsed = monotonic()-viewer_started
    if child.returncode != 0:
        raise RuntimeError('Original saved viewer returned nonzero; no convergence/page follows')
    check('viewer_completed')
    views = read_json(view/'view.json')
    total_N = sum(case['accepted_states'] for case in cases)
    assert views['status'] == 'pass' and views['new_F_T_model_solver_HP_calls'] == 0
    assert views['contact_pressure_clamping_qualified'] is False
    assert all(views[key] == total_N for key in
        ('geometry_started', 'geometry_completed', 'nodal_started', 'nodal_completed'))
    assert [case['label'] for case in views['cases']] == [case['label'] for case in cases]
    assert {name for name in views['outputs'] if name.endswith('.png')} == {
        'comparison.png', 'distances_forces.png', 'peak_fields.png'}
    convergence_file = (ROOT/protocol['convergence_source']).resolve()
    assert sha256(convergence_file.read_bytes()).hexdigest() == protocol['source_bindings'][relative(convergence_file)]
    spec = importlib.util.spec_from_file_location('_L_BFWD1_labelled_convergence', convergence_file)
    convergence = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(convergence)
    table_cases, case_outputs = [], []
    PNGs = [view/name for name in ('comparison.png', 'distances_forces.png', 'peak_fields.png')]
    GIFs = []
    for case, manifest_case, observed_case in zip(cases, manifest['cases'], views['cases']):
        check()
        label, result = case['label'], case['result']
        assert observed_case['saved_accepted_states'] == observed_case['observed_states'] == case['accepted_states']
        assert observed_case['reference_available'] is False and observed_case['unload_endpoint_reached'] is None
        summary_file = view/label/'summary.json'
        summary = read_json(summary_file)
        assert len(summary['rows']) == case['accepted_states']
        convergence_result = convergence.plot_convergence(case['result_file'],
            run/'convergence'/f"{case['ordinal']:03d}", check, label=label,
            title=label+': actual short-loading convergence')
        assert convergence_result['mechanics_re_evaluated'] is False
        assert convergence_result['source_result_sha256'] == cache[case['result_file']][1]
        rows = []
        for accepted_index, (state, observed) in enumerate(zip(result['states'], summary['rows'])):
            assert (observed['index'], observed['original_target_index'], observed['leg'], observed['d_mm'], observed['state_sha256']) == (
                accepted_index, state['original_target_index'], state['leg'], state['d'], state['state_sha256'])
            key = (state['original_target_index'], state['leg'], state['d'])
            rows.append(dict(accepted_state_index=accepted_index, state=projection(state), observation=observed,
                old_prefix_state=case['old_rows'].get(key) if state['is_original_target'] else None))
        old = case['old_result']
        table_cases.append(dict(label=label, status=case['response']['status'], accepted_states=case['accepted_states'],
            declared_case=manifest_case, response_identity=case['response']['identity'],
            path=case['response']['path'], options=case['response']['options'],
            producer_flags=case['response']['producer_flags'], independent_reference=case['response']['independent_reference'],
            old_prefix_source=dict(path=relative(case['old_result_file']), sha256=cache[case['old_result_file']][1],
                status=old['status'], targets_mm=old['targets_mm'], task_sha256=old['task_sha256'],
                mechanics_source_sha256=old.get('mechanics_source_sha256', {}),
                scope='First three original targets only; descriptive original scalars, no equivalence gate or qualification transfer'),
            convergence=convergence_result, rows=rows))
        gif = view/label/'actual_states.gif'
        assert label+'/actual_states.gif' in views['outputs']
        GIFs.append(gif)
        PNGs.append(Path(convergence_result['png_file']))
        case_outputs.append(dict(label=label, accepted_states=case['accepted_states'],
            result_file=relative(case['result_file']), response_file=relative(case['response_file']),
            summary_file=relative(summary_file), convergence_json=relative(convergence_result['json_file']),
            convergence_png=relative(convergence_result['png_file']), GIF_file=relative(gif),
            convergence_counts=convergence_result['counts']))
    readset = dict(NPZ_files=len(arrays), decoded_fields=sum(case['decoded_fields'] for case in cases),
        geometry_calls=views['geometry_completed'], nodal_calls=views['nodal_completed'],
        basis='New saved archive cardinalities/field declarations and completed pure-observer counts; not payload-open instrumentation',
        different_files_are_not_read_operations=True)
    table = dict(schema_version='hf-batch-short-loading-display-1.0', status='success',
        scope='Two successful new short-loading paths; saved original values only',
        batch_manifest=dict(path=relative(manifest_file), sha256=cache[manifest_file][1]),
        batch_status=index['status'], cases=table_cases, readset_counts=readset,
        comparison_scope='Old first-three-target values are placed alongside new original values only; no differences, ratios, ranking or independent-reference transfer',
        qualification=dict(manufacturing='pending',pressure=False,effective_clamp=False,release=False,stability=False,HF5=False,ranking=False))
    table_file, review_file = run/'states_table.json', run/'REVIEW.md'
    write_json(table_file, table, 'table_written')
    link = lambda path: os.path.relpath(path, run).replace('\\', '/')
    text = ['# L-BFWD1：双LF短加载实际结果', '',
        '两例按清单顺序完成0→0.25→0.50 mm短加载。以下图及动画来自本次保存接受态；没有插值或旧媒体重绘。', '',
        'R是半模型输入反力；q_out是加权端口位移，不是间隙。下半工件total/material/Hu为有符号弱式作用，不是压力或已认证有效夹持。', '',
        '制造pending；无新独立参考，不授完整25目标、卸载、释放、稳定性、HF5或正式排名。旧前三目标仅作原值并列，来源/源码epoch各自保留，不据此宣称同源码全路径或资格传递。', '',
        '[原值状态表](states_table.json) · [批量清单](<'+link(manifest_file)+'>) · [保存态显示记录](view/view.json)', '']
    for name in ('comparison.png', 'distances_forces.png', 'peak_fields.png'):
        text += ['!['+name+'](view/'+name+')', '']
    for case, output in zip(table_cases, case_outputs):
        text += ['## '+case['label'], '', 'status=success；实际接受态数='+str(case['accepted_states'])+'。peak/last是本短加载的实际最大接受态，非1.20 mm完整循环峰值。', '',
            '[result](<'+link(ROOT/output['result_file'])+'>) · [response](<'+link(ROOT/output['response_file'])+'>) · [有限距离/分区场原值](<'+link(ROOT/output['summary_file'])+'>) · [实际N帧GIF](<'+link(ROOT/output['GIF_file'])+'>) · [旧前三目标来源](<'+link(ROOT/case['old_prefix_source']['path'])+'>)', '',
            '!['+case['label']+'收敛](<'+link(ROOT/output['convergence_png'])+'>)', '',
            '| 原目标 | leg | d mm | 新R N | 旧R N | 新q_out mm | 旧q_out mm | 新下半工件Fy N | 旧下半工件Fy N |',
            '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
        for row in case['rows']:
            state, old = row['state'], row['old_prefix_state']
            values = [state['original_target_index'], state['leg'], state['d'], state['R_input'],
                old['R_input'] if old else None, state['q_out'], old['q_out'] if old else None,
                state['workpiece']['force_on_lower_body_N']['total'][1],
                old['workpiece']['force_on_lower_body_N']['total'][1] if old else None]
            text.append('| '+' | '.join('—' if value is None else repr(value) if isinstance(value, float) else str(value) for value in values)+' |')
        text += ['', '内部二分态保实际接受顺序；旧列缺失保持空，不填零。所有材料/Hu/总量与有限距离、分区J及应变原值保存在状态表。', '']
    check()
    with review_file.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(text).rstrip()+'\n')
    check('review_written')
    check('display_seal_started')
    display_files = [view_protocol, table_file, review_file, run/'viewer_stdout.log']
    for directory in (view, run/'convergence'):
        display_files += sorted(path for path in directory.rglob('*') if path.is_file())
    display_outputs = {}
    for path in display_files:
        check()
        digest, size = sha256(), 0
        with path.open('rb') as stream:
            while True:
                check()
                block = stream.read(1024*1024)
                if not block:
                    break
                digest.update(block)
                size += len(block)
        check()
        display_outputs[relative(path)] = dict(sha256=digest.hexdigest(), bytes=size)
    check('display_seal_completed')
    answer = dict(status='pass', cases=case_outputs, viewer_elapsed_seconds=viewer_elapsed,
        readset_counts=readset, PNG_files=[relative(path) for path in PNGs], GIF_files=[relative(path) for path in GIFs],
        state_table_file=relative(table_file), review_file=relative(review_file),
        view_protocol=relative(view_protocol), view_manifest=relative(view/'view.json'),
        display_outputs=display_outputs, display_identity_seal='complete_inside_shared_display_window',
        display_identity_scope='Stream SHA/size of all new display products within the shared display deadline; separate from the helper full-run seal',
        wrapper_ordinary_JSON_reads=len(cache),
        ordinary_JSON_read_scope='This wrapper cache only; original viewer reads and two convergence result reads are separate',
        display_elapsed_seconds=monotonic()-started,
        display_seconds_limit=protocol['viewer_seconds'], source_scope='Original pure viewer child and labelled ordinary-JSON convergence copy only',
        GIF_frame_count_basis='Pinned original viewer verifies each GIF n_frames against actual accepted rows; this wrapper does not decode media')
    check('display_completed')
    return answer
