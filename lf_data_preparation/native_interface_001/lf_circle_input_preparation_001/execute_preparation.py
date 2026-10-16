"""Prepare one undeformed circular-workpiece model; no force or path evaluation."""
from time import perf_counter
STARTED = perf_counter()
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
CARD = 'L-CPREP1'


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n',
                    encoding='utf-8', newline='\n')


def main():
    protocol_file = STAGE/'protocol.json'
    protocol = read(protocol_file)
    auth_file = STAGE/'author/authorization.json'
    auth = read(auth_file)
    assert auth['card'] == protocol['card'] == CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert isinstance(auth['direct_human_request'], str) and auth['direct_human_request'].strip()
    assert auth['protocol_sha256'] == sha256(protocol_file.read_bytes()).hexdigest()
    assert auth['authorized_execution_source_commit'] == protocol['source_baseline_commit']
    assert (protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (180, 240, 1024**3)
    run = ROOT/protocol['output_directory']
    stop = STAGE/'stop_requested.txt'
    assert not run.exists() and not stop.exists()
    run.mkdir(parents=True, exist_ok=False)
    receipt_file = run/'execution_receipt.json'
    process, peak = psutil.Process(), 0
    events, binding_reads = Counter(), Counter()
    phase, outputs, seal_scope = 'bootstrap', {}, 'not_complete'
    diagnostics = dict(card=CARD, status='in_progress', checks={},
        scope='Undeformed native-grid model and circular overlay compatibility only; no load, force, tangent, HP or equilibrium solve')
    receipt = dict(card=CARD, status='running', protocol_sha256=auth['protocol_sha256'],
        authorization_sha256=sha256(auth_file.read_bytes()).hexdigest(),
        source_baseline_commit=protocol['source_baseline_commit'],
        counts=dict(model_build_started=0, model_build_completed=0, model_write_started=0,
                    model_write_completed=0, plot_calls_started=0, plot_calls_completed=0),
        tests=0, force_calls=0, tangent_calls=0, HP_calls=0, solver_calls=0,
        default_installations=0, mechanical_hooks_monitored=False,
        zero_mechanics_basis='Frozen native project construction/writer and in-memory plot only; no universal kernel hooks',
        dependency_import_scope='Existing geometry/project dependencies may import or register JAX; no zero-import claim',
        qualification_scope='Geometric/model preparation only; no mechanical, pressure, effective-clamp, release, stability, independent-reference or HF5 qualification')

    def checkpoint(event='resource_check'):
        nonlocal peak
        memory = process.memory_info()
        peak = max(peak, memory.rss, getattr(memory, 'peak_wset', memory.rss))
        reason = ('external_stop_requested' if stop.exists() else
                  'sampled_RSS_limit' if peak > protocol['sampled_RSS_bytes'] else
                  'helper_elapsed_limit' if perf_counter()-STARTED > protocol['helper_seconds'] else None)
        if reason:
            receipt['resource_stop_reason'] = reason
            raise RuntimeError(reason)
        events[event] += 1

    def digest(path):
        value = sha256()
        checkpoint()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                checkpoint()
                value.update(block)
        checkpoint()
        return value.hexdigest()

    def bindings():
        for name, pin in (protocol['input_bindings'] | protocol['source_bindings']).items():
            binding_reads[name] += 1
            assert digest(ROOT/name) == pin, name

    def check(name, condition):
        diagnostics['checks'][name] = bool(condition)
        if not condition:
            raise ValueError('Circle preparation check failed: '+name)
        checkpoint('compatibility_check')

    def array_info(array):
        return dict(dtype=array.dtype.name, shape=list(array.shape), sha256=sha256(array.tobytes(order='C')).hexdigest())

    def seal():
        sealed = {}
        for path in sorted(run.rglob('*')):
            if path.is_file() and path != receipt_file:
                sealed[path.relative_to(ROOT).as_posix()] = dict(sha256=digest(path), bytes=path.stat().st_size)
        checkpoint()
        return sealed

    write(receipt_file, receipt)
    try:
        phase = 'input_and_task_binding'
        geometry_file = ROOT/protocol['geometry_file']
        descriptor = read(geometry_file)
        sole_old_npz = geometry_file.with_name(descriptor['arrays']['path']).relative_to(ROOT).as_posix()
        all_pins = protocol['input_bindings'] | protocol['source_bindings']
        old_payloads = {name for name in all_pins if Path(name).suffix.lower() in ('.npz', '.png', '.gif', '.zip', '.gz', '.csv')}
        assert old_payloads == {sole_old_npz}
        bindings()
        parent = read(ROOT/protocol['parent_task_file'])
        task = deepcopy(parent)
        assert parent['workpiece'] == dict(kind='fixed_rigid', shape='square', center_mm=[71., 40.], side_mm=18., fixed_components=[0, 1])
        assert parent['path']['kind'] == 'ordered_cycle' and len(parent['path']['targets_mm']) == 25
        assert parent['input']['target_mm'] == 1.2
        assert protocol['workpiece'] == dict(kind='fixed_rigid', shape='circle', center_mm=[71., 40.], radius_mm=9., fixed_components=[0, 1])
        assert protocol['targets_mm'] == [0., .25, .5]
        assert set(protocol['task_metadata']) == {'task_id', 'purpose', 'parameter_origin', 'description'}
        task.update(deepcopy(protocol['task_metadata']))
        task['input']['target_mm'] = .5
        task['path'] = dict(kind='load_only', targets_mm=deepcopy(protocol['targets_mm']))
        task['workpiece'] = deepcopy(protocol['workpiece'])
        changed = {'task_id', 'purpose', 'parameter_origin', 'description', 'input', 'path', 'workpiece'}
        assert {k:v for k,v in task.items() if k not in changed} == {k:v for k,v in parent.items() if k not in changed}
        assert {k:v for k,v in task['input'].items() if k != 'target_mm'} == {k:v for k,v in parent['input'].items() if k != 'target_mm'}
        task_file = run/'task.json'
        write(task_file, task)
        diagnostics.update(circle=deepcopy(task['workpiece']), old_square=deepcopy(parent['workpiece']),
            task_file=task_file.relative_to(ROOT).as_posix(), task_file_sha256=digest(task_file),
            source_geometry_file=protocol['geometry_file'], source_geometry_descriptor=deepcopy(descriptor),
            changed_task_fields=sorted(changed), targets_executed=False)
        sys.path.insert(0, str(ROOT/'hf_repo/src'))
        import numpy as np
        from hf_eval.native_project import build_native_project, write_native_project
        from hf_eval.regions import node_coordinates, element_connectivity
        phase = 'single_model_construction'
        receipt['counts']['model_build_started'] += 1
        checkpoint('model_build_started')
        project = build_native_project(geometry_file, task)
        receipt['counts']['model_build_completed'] += 1
        checkpoint('model_build_completed')
        geometry, model, regions = project.geometry, project.model, project.region_metadata
        check('bound_task_exact', project.task == task)
        check('source_grid_exact', geometry.grid == descriptor['grid'])
        check('source_geometry_identity_exact', geometry.geometry_id == descriptor['geometry_id'] and geometry.metadata['descriptor_sha256'] == descriptor['descriptor_sha256'])
        mask_records = {name:array_info(array) for name,array in geometry.arrays.items()}
        check('all_four_source_masks_exact', mask_records == descriptor['arrays']['fields'])
        check('model_solid_preserves_source', np.array_equal(model.solid, geometry.solid.ravel(order='C').astype(bool)))
        check('coordinates_preserve_source_grid', np.array_equal(model.coordinates, node_coordinates(geometry)))
        check('connectivity_preserves_source_grid', np.array_equal(model.connectivity, element_connectivity(geometry)))
        check('native_counts', model.ne == 13440 and len(model.coordinates) == 13689 and model.ndof == 27378)
        body = regions['workpiece']
        coords, conn = model.coordinates, model.connectivity
        centres = coords[conn].mean(axis=1)
        centre = np.asarray(task['workpiece']['center_mm'])
        circle_cells = np.flatnonzero(np.sum((centres-centre)**2, axis=1) <= task['workpiece']['radius_mm']**2)
        square_cells = np.flatnonzero((np.abs(centres-np.asarray(parent['workpiece']['center_mm'])) <= parent['workpiece']['side_mm']/2).all(axis=1))
        cells = np.asarray(body['cells'], dtype=np.int64)
        nodes = np.asarray(body['nodes'], dtype=np.int64)
        dofs = np.asarray(body['dofs'], dtype=np.int64)
        expected_nodes = np.unique(conn[cells])
        expected_dofs = np.column_stack((2*expected_nodes, 2*expected_nodes+1)).ravel()
        check('circle_selection_matches_cell_centres', len(cells) > 0 and np.array_equal(cells, circle_cells))
        check('circle_cells_subset_old_square', np.all(np.isin(cells, square_cells)))
        check('circle_nodes_subset_old_square', np.all(np.isin(nodes, np.unique(conn[square_cells]))))
        check('circle_cells_original_passive_void', np.all(geometry.arrays['passive_void'].ravel()[cells] == 1))
        check('circle_nodes_disjoint_source_solid', np.intersect1d(nodes, project.solid_nodes).size == 0)
        check('circle_nodes_disjoint_support_and_ports', all(np.intersect1d(nodes, np.asarray(selected)).size == 0 for selected in (
            regions['support']['selected_nodes'], regions['ports']['input']['nodes'], regions['ports']['output']['nodes'])))
        check('circle_nodes_and_both_fixed_components_exact', np.array_equal(nodes, expected_nodes) and np.array_equal(dofs, expected_dofs))
        top = geometry.grid['origin_mm'][1]+geometry.grid['extent_mm'][1]
        check('circle_centred_on_symmetry', centre[1] == top == 40.)
        top_nodes = nodes[coords[nodes,1] == top]
        background = regions['background_symmetry']
        check('circle_symmetry_cut_covered', np.all(np.isin(top_nodes, background['selected_nodes'])))
        overlap = np.intersect1d(dofs, np.asarray(background['dofs']))
        check('circle_background_overlap_exact', np.array_equal(overlap, body['background_symmetry_overlap_dofs']))
        fixed = np.unique(np.concatenate([np.asarray(regions[name]['dofs'],dtype=np.int64)
                                         for name in ('support','entity_symmetry','background_symmetry','workpiece')]))
        check('all_constraint_dofs_exact', np.array_equal(fixed, model.fixed_dofs))
        check('all_free_dofs_exact', np.array_equal(model.free, np.setdiff1d(np.arange(model.ndof), fixed)))
        check('port_vectors_avoid_fixed_dofs', not np.any(project.bin[fixed]) and not np.any(project.bout[fixed]))
        edge_counts = Counter()
        for number, cell in enumerate(conn[cells]):
            if number % 128 == 0:
                checkpoint()
            for a,b in zip(cell, np.roll(cell,-1)):
                edge_counts[tuple(sorted((int(a),int(b))))] += 1
        check('workpiece_edges_have_manifold_incidence', all(n in (1,2) for n in edge_counts.values()))
        exposed = sorted(edge for edge,count in edge_counts.items() if count == 1)
        cut = [edge for edge in exposed if all(coords[node,1] == top for node in edge)]
        boundary = [edge for edge in exposed if edge not in cut]
        check('nonempty_surface_and_symmetry_cut_edges', bool(boundary) and bool(cut))
        diagnostics.update(counts=dict(regions['counts'], workpiece_cells=len(cells), workpiece_nodes=len(nodes),
            workpiece_fixed_dofs=len(dofs), old_square_cells=len(square_cells), boundary_edges=len(boundary), symmetry_cut_edges=len(cut)),
            workpiece=deepcopy(body), boundary_edges=[list(e) for e in boundary],
            boundary_edges_including_symmetry_cut=[list(e) for e in exposed], symmetry_cut_edges=[list(e) for e in cut],
            boundary_scope='Cell-staircase exposed edges; boundary_edges exclude y40 symmetry cut, not a fitted analytic circle',
            original_square_scope='Cell-centre selection reconstructed from this same native coordinate/connectivity memory, not an old model read or second model construction',
            source_mask_fields=mask_records, grid=deepcopy(geometry.grid),
            qualification=deepcopy(project.qualification), initial_gap_scope=body['initial_gap_scope'],
            geometry_compatibility_passed=True, mechanical_qualified=False, independent_reference_qualified=False, HF5_qualified=False)
        phase = 'single_model_persistence'
        receipt['counts']['model_write_started'] += 1
        model_file = write_native_project(project, run/'model')
        receipt['counts']['model_write_completed'] += 1
        checkpoint('model_write_completed')
        saved = read(model_file)
        expected_saved = dict(coordinates=model.coordinates, connectivity=model.connectivity, solid=model.solid,
            fixed_dofs=model.fixed_dofs, workpiece_cells=cells, workpiece_nodes=nodes, workpiece_dofs=dofs,
            workpiece_background_symmetry_overlap_dofs=np.asarray(body['background_symmetry_overlap_dofs'],dtype=np.int64))
        check('saved_task_and_grid_exact', saved['task'] == task and saved['grid'] == geometry.grid and not saved['response_evaluated'])
        check('saved_coordinate_connectivity_body_fixed_fields_exact', all(saved['arrays']['fields'][name] == array_info(array) for name,array in expected_saved.items()))
        diagnostics['model_file'] = model_file.relative_to(ROOT).as_posix()
        diagnostics['model_file_sha256'] = digest(model_file)
        diagnostics['coordinate_connectivity_fields'] = {name:array_info(array) for name,array in expected_saved.items()}
        phase = 'single_undeformed_plot'
        spec = importlib.util.spec_from_file_location('_circle_preparation_plot', ROOT/protocol['plot_source'])
        plot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plot)
        receipt['counts']['plot_calls_started'] += 1
        receipt['plot'] = plot.plot_circle(project, run/'circle_prepared.png', diagnostics, checkpoint)
        receipt['counts']['plot_calls_completed'] += 1
        assert events['plot_started'] == events['plot_completed'] == 1 and (run/'circle_prepared.png').is_file()
        diagnostics['status'] = 'pass'
        write(run/'diagnostics.json', diagnostics)
        link = lambda path:os.path.relpath(path,run).replace('\\','/')
        page = ['# 圆形固定工件：未变形输入与模型准备', '',
            '本次只构建并保存一次原生模型；新0/.25/.5 mm任务只保存，未施加载荷或求解。',
            'wave原四掩码、grid、坐标与连接保持；固定圆r9 mm、center(71,40) mm，只有下半域。',
            '圆形覆盖由单元中心选取，实际边界为网格阶梯；解析圆线仅参考，不是拟合接触面。', '',
            '![未变形circle overlay与实际固定节点](circle_prepared.png)', '',
            f"单元{model.ne}，DOF{model.ndof}；圆覆盖{len(cells)}单元/{len(nodes)}节点/{len(dofs)}固定DOF。",
            f"相同内存方体参考覆盖{len(square_cells)}单元；实体外露边{len(boundary)}条，y40对称切口{len(cut)}条。", '',
            '端口箭头仅声明方向；没有变形、反力或应力结果。初始node-window距离不等于表面间隙或接触开始。',
            '几何/约束兼容不授平衡、压力、有效夹持、释放、稳定性、独参或HF5资格；制造阈值pending按原资格声明保留。', '',
            '[完整检查、边与固定DOF](diagnostics.json) · [新短任务](task.json) · [保存模型](model/model.json)',
            '[原wave geometry](<'+link(geometry_file)+'>) · [原25目标task](<'+link(ROOT/protocol['parent_task_file'])+'>)', '',
            '| 检查 | 通过 |', '|---|---|']
        page += ['| '+name+' | '+str(passed)+' |' for name,passed in diagnostics['checks'].items()]
        (run/'REVIEW.md').write_text('\n'.join(page).rstrip()+'\n',encoding='utf-8',newline='\n')
        phase = 'final_binding_and_seal'
        bindings()
        receipt['all_bindings_unchanged'] = True
        outputs = seal()
        seal_scope = 'complete_inside_original_helper_window'
        checkpoint()
        receipt['status'] = 'pass'
    except BaseException as error:
        diagnostics.update(status='not_pass', failure=dict(phase=phase, exception_class=type(error).__name__, code=getattr(error,'code',None),reason=str(error)))
        receipt.update(status='not_pass', error=deepcopy(diagnostics['failure']))
        write(run/'diagnostics.json', diagnostics)
        if not stop.exists() and perf_counter()-STARTED <= protocol['helper_seconds'] and process.memory_info().rss <= protocol['sampled_RSS_bytes']:
            try:
                outputs = seal()
                seal_scope = 'actual_partial_inside_original_helper_window'
            except BaseException:
                seal_scope = 'not_complete_before_resource_close'
    receipt.update(phase=phase, events=dict(events), checks_completed=len(diagnostics['checks']),
        checks_passed=sum(diagnostics['checks'].values()), outputs=outputs, output_identity_seal=seal_scope,
        wrapper_binding_file_reads=dict(binding_reads),
        read_scope='Only one old geometry NPZ allowed; binding SHA passes counted here; original builder/loader/writer source-snapshot reads delegated, no universal file-open hook. No helper NPZ decode.',
        helper_seconds=protocol['helper_seconds'], elapsed_seconds=perf_counter()-STARTED,
        sampled_peak_RSS_bytes=peak,sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()), completed_utc=datetime.now(timezone.utc).isoformat(),
        requested_targets_executed=False, old_records_rewritten=False, source_bindings=protocol['source_bindings'])
    write(receipt_file,receipt)
    print(json.dumps(dict(status=receipt['status'],phase=phase,counts=receipt['counts'],checks=receipt['checks_completed'],error=receipt.get('error'))),flush=True)
    if receipt['status'] != 'pass':
        raise RuntimeError('L-CPREP1 closed not_pass; no retry or following phase')


if __name__ == '__main__':
    main()
