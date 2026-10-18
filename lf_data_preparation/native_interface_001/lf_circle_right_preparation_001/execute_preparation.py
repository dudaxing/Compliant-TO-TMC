"""Prepare one right-shifted circle model and resident undeformed comparison."""
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
CARD = 'L-CRIGHT1'
BASE = 'e509330e5db82eced1b92a20dda02a24fb3e3ae6'
THREAD_ENV = dict.fromkeys(('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16')
META_FIELDS = ('task_id','purpose','parameter_origin','description')


def read(path):
    return json.loads(path.read_bytes())


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    protocol_file,auth_file=STAGE/'protocol.json',STAGE/'author/authorization.json'
    protocol,auth=read(protocol_file),read(auth_file)
    assert auth['card']==protocol['card']==CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert auth['approval_card']==CARD and isinstance(auth['direct_human_request'],str) and auth['direct_human_request'].strip()
    assert auth['protocol_sha256']==sha256(protocol_file.read_bytes()).hexdigest()
    assert auth['authorized_execution_source_commit']==protocol['source_baseline_commit']==BASE
    assert (protocol['helper_seconds'],protocol['outer_seconds'],protocol['sampled_RSS_bytes'])==(180,240,64*1024**3)
    assert protocol['cpu_thread_limit']==16 and protocol['cpu_thread_environment']==THREAD_ENV
    assert {name:os.environ.get(name) for name in THREAD_ENV}==THREAD_ENV
    run,stop=ROOT/protocol['output_directory'],STAGE/'stop_requested.txt'
    assert not run.exists() and not stop.exists()
    run.mkdir(parents=True,exist_ok=False)
    receipt_file=run/'execution_receipt.json'
    process,peak=psutil.Process(),0
    events,binding_reads=Counter(),Counter()
    phase,outputs,seal_scope='bootstrap',{},'not_complete'
    diagnostics=dict(card=CARD,status='in_progress',checks={},
        scope='Candidate undeformed native-circle geometry/constraint compatibility and resident baseline comparison only; no mechanics')
    receipt=dict(card=CARD,status='running',protocol_sha256=auth['protocol_sha256'],
        authorization_sha256=sha256(auth_file.read_bytes()).hexdigest(),source_baseline_commit=BASE,
        counts=dict(model_build_started=0,model_build_completed=0,model_write_started=0,model_write_completed=0,
            layout_analysis_started=0,layout_analysis_completed=0,plot_calls_started=0,plot_calls_completed=0),
        tests=0,force_calls=0,tangent_calls=0,HP_calls=0,solver_calls=0,default_installations=0,
        baseline_model_builds=0,mechanical_hooks_monitored=False,
        zero_mechanics_basis='Frozen build/write and geometry-only resident analysis/plot; no universal kernel hooks',
        dependency_import_scope='Existing geometry/project dependencies may import or register JAX; no zero-import claim',
        cpu_thread_limit=16,cpu_thread_environment={name:os.environ[name] for name in THREAD_ENV},
        cpu_resource_scope='Per-library thread configuration before HF imports; not measured use of16 cores; CPU backend unchanged',
        qualification_scope='Undeformed candidate preparation only; no equilibrium, pressure, effective clamp, release, stability, reference or HF5 qualification')

    def checkpoint(event='resource_check'):
        nonlocal peak
        memory=process.memory_info()
        peak=max(peak,memory.rss,getattr(memory,'peak_wset',memory.rss))
        reason=('external_stop_requested' if stop.exists() else 'sampled_RSS_limit' if peak>protocol['sampled_RSS_bytes'] else
            'helper_elapsed_limit' if perf_counter()-STARTED>protocol['helper_seconds'] else None)
        if reason:
            receipt['resource_stop_reason']=reason
            raise RuntimeError(reason)
        events[event]+=1

    def digest(path):
        value=sha256()
        checkpoint()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):
                checkpoint();value.update(block)
        checkpoint()
        return value.hexdigest()

    def bindings():
        for name,pin in (protocol['input_bindings']|protocol['source_bindings']).items():
            binding_reads[name]+=1
            assert digest(ROOT/name)==pin,name

    def check(name,condition):
        diagnostics['checks'][name]=bool(condition)
        if not condition:
            raise ValueError('Right-circle preparation check failed: '+name)
        checkpoint('compatibility_check')

    def array_info(array):
        return dict(dtype=array.dtype.name,shape=list(array.shape),sha256=sha256(array.tobytes(order='C')).hexdigest())

    def seal():
        sealed={}
        for path in sorted(run.rglob('*')):
            if path.is_file() and path!=receipt_file:
                sealed[path.relative_to(ROOT).as_posix()]=dict(sha256=digest(path),bytes=path.stat().st_size)
        checkpoint()
        return sealed

    write(receipt_file,receipt)
    try:
        phase='input_and_task_binding'
        geometry_file=ROOT/protocol['geometry_file']
        descriptor=read(geometry_file)
        sole_old_npz=geometry_file.with_name(descriptor['arrays']['path']).relative_to(ROOT).as_posix()
        all_pins=protocol['input_bindings']|protocol['source_bindings']
        payload_suffixes={'.npz','.npy','.png','.gif','.zip','.gz','.csv'}
        assert {name for name in all_pins if Path(name).suffix.lower() in payload_suffixes}=={sole_old_npz}
        bindings()
        baseline=read(ROOT/protocol['baseline_task_file'])
        assert baseline['workpiece']==dict(kind='fixed_rigid',shape='circle',center_mm=[71.,40.],radius_mm=9.,fixed_components=[0,1])
        assert baseline['path']==dict(kind='ordered_cycle',targets_mm=[0.,.25,.5,.75,1.,1.15,1.25,1.35,1.4,1.35,1.25,1.15,1.,.75,.5,.25,0.])
        assert baseline['input']['target_mm']==1.4
        assert protocol['workpiece']==dict(kind='fixed_rigid',shape='circle',center_mm=[74.,40.],radius_mm=9.,fixed_components=[0,1])
        assert set(protocol['task_metadata'])==set(META_FIELDS)
        task=deepcopy(baseline)
        task.update(deepcopy(protocol['task_metadata']))
        task['workpiece']=deepcopy(protocol['workpiece'])
        unchanged=deepcopy(task)
        unchanged['workpiece']=deepcopy(baseline['workpiece'])
        for name in META_FIELDS:
            if name in baseline:unchanged[name]=deepcopy(baseline[name])
            else:unchanged.pop(name,None)
        check('only_center_x_and_informational_metadata_changed',unchanged==baseline)
        write(run/'task.json',task)
        diagnostics.update(baseline_workpiece=deepcopy(baseline['workpiece']),candidate_workpiece=deepcopy(task['workpiece']),
            source_geometry_file=protocol['geometry_file'],source_geometry_descriptor=deepcopy(descriptor),
            baseline_task_file=protocol['baseline_task_file'],task_file=(run/'task.json').relative_to(ROOT).as_posix(),
            task_file_sha256=digest(run/'task.json'),stored_path=deepcopy(task['path']),input_target_mm=task['input']['target_mm'],
            requested_targets_executed=False,baseline_model_built=False,
            baseline_scope='Cell-centre shape and constraints reconstructed on candidate resident coordinates/connectivity; no second model or old state read')
        sys.path.insert(0,str(ROOT/'hf_repo/src'))
        import numpy as np
        from hf_eval.native_project import build_native_project,write_native_project
        from hf_eval.regions import node_coordinates,element_connectivity
        from hf_eval.data import canonical_hash
        check('task_canonical_identity_outside_allowed_changes',canonical_hash(unchanged)==canonical_hash(baseline))
        phase='single_candidate_model_construction'
        receipt['counts']['model_build_started']+=1
        checkpoint('model_build_started')
        project=build_native_project(geometry_file,task)
        receipt['counts']['model_build_completed']+=1
        checkpoint('model_build_completed')
        geometry,model,regions=project.geometry,project.model,project.region_metadata
        check('bound_task_exact',project.task==task)
        check('source_grid_exact',geometry.grid==descriptor['grid'])
        check('source_geometry_identity_exact',geometry.geometry_id==descriptor['geometry_id'] and geometry.metadata['descriptor_sha256']==descriptor['descriptor_sha256'])
        masks={name:array_info(array) for name,array in geometry.arrays.items()}
        check('all_four_source_masks_exact',masks==descriptor['arrays']['fields'])
        check('model_solid_preserves_source',np.array_equal(model.solid,geometry.solid.ravel(order='C').astype(bool)))
        check('coordinates_preserve_source_grid',np.array_equal(model.coordinates,node_coordinates(geometry)))
        check('connectivity_preserves_source_grid',np.array_equal(model.connectivity,element_connectivity(geometry)))
        check('native_counts_unchanged',model.ne==13440 and len(model.coordinates)==13689 and model.ndof==27378)
        body=regions['workpiece']
        cells,nodes,dofs=(np.asarray(body[name],dtype=np.int64) for name in ('cells','nodes','dofs'))
        centres=model.coordinates[model.connectivity].mean(axis=1)
        circle_cells=np.flatnonzero(np.sum((centres-np.asarray(task['workpiece']['center_mm']))**2,axis=1)<=81.)
        expected_nodes=np.unique(model.connectivity[cells])
        expected_dofs=np.column_stack((2*expected_nodes,2*expected_nodes+1)).ravel()
        check('candidate_circle_cell_centres_exact',len(cells)>0 and np.array_equal(cells,circle_cells))
        check('candidate_original_passive_void',np.all(geometry.arrays['passive_void'].ravel()[cells]==1))
        check('candidate_disjoint_source_solid_nodes',np.intersect1d(nodes,project.solid_nodes).size==0)
        check('candidate_disjoint_support_and_ports',all(np.intersect1d(nodes,np.asarray(selected)).size==0 for selected in
            (regions['support']['selected_nodes'],regions['ports']['input']['nodes'],regions['ports']['output']['nodes'])))
        check('candidate_nodes_and_fixed_components_exact',np.array_equal(nodes,expected_nodes) and np.array_equal(dofs,expected_dofs))
        top=geometry.grid['origin_mm'][1]+geometry.grid['extent_mm'][1]
        check('candidate_centre_on_symmetry',task['workpiece']['center_mm'][1]==top==40.)
        top_nodes=nodes[model.coordinates[nodes,1]==top]
        background=regions['background_symmetry']
        check('candidate_symmetry_cut_covered',np.all(np.isin(top_nodes,background['selected_nodes'])))
        check('candidate_background_overlap_exact',np.array_equal(np.intersect1d(dofs,np.asarray(background['dofs'])),body['background_symmetry_overlap_dofs']))
        fixed=np.unique(np.concatenate([np.asarray(regions[name]['dofs'],dtype=np.int64) for name in ('support','entity_symmetry','background_symmetry','workpiece')]))
        check('all_constraint_dofs_exact',np.array_equal(fixed,model.fixed_dofs))
        check('all_free_dofs_exact',np.array_equal(model.free,np.setdiff1d(np.arange(model.ndof),fixed)))
        check('port_vectors_avoid_fixed_dofs',not np.any(project.bin[fixed]) and not np.any(project.bout[fixed]))
        diagnostics.update(source_mask_fields=masks,grid=deepcopy(geometry.grid),counts=deepcopy(regions['counts']),
            workpiece=deepcopy(body),qualification=deepcopy(project.qualification),initial_gap_scope=body['initial_gap_scope'],
            mechanical_qualified=False,independent_reference_qualified=False,HF5_qualified=False)
        phase='resident_layout_analysis'
        spec=importlib.util.spec_from_file_location('_right_preparation_layout',ROOT/protocol['analysis_source'])
        analysis=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analysis)
        receipt['counts']['layout_analysis_started']+=1
        layout=analysis.analyze_layout(project,deepcopy(baseline['workpiece']),check,checkpoint)
        receipt['counts']['layout_analysis_completed']+=1
        write(run/'layout.json',layout)
        diagnostics['layout_file']=(run/'layout.json').relative_to(ROOT).as_posix()
        phase='single_candidate_model_persistence'
        receipt['counts']['model_write_started']+=1
        model_file=write_native_project(project,run/'model')
        receipt['counts']['model_write_completed']+=1
        checkpoint('model_write_completed')
        saved=read(model_file)
        expected_saved=dict(coordinates=model.coordinates,connectivity=model.connectivity,solid=model.solid,fixed_dofs=model.fixed_dofs,
            workpiece_cells=cells,workpiece_nodes=nodes,workpiece_dofs=dofs,
            workpiece_background_symmetry_overlap_dofs=np.asarray(body['background_symmetry_overlap_dofs'],dtype=np.int64))
        check('saved_task_and_grid_exact',saved['task']==task and saved['grid']==geometry.grid and not saved['response_evaluated'])
        check('saved_coordinate_connectivity_body_fixed_fields_exact',all(saved['arrays']['fields'][name]==array_info(array) for name,array in expected_saved.items()))
        diagnostics.update(model_file=model_file.relative_to(ROOT).as_posix(),model_file_sha256=digest(model_file),
            coordinate_connectivity_fields={name:array_info(array) for name,array in expected_saved.items()})
        phase='single_undeformed_plot'
        receipt['counts']['plot_calls_started']+=1
        receipt['plot']=analysis.plot_layout(project,layout,run/'right_prepared.png',checkpoint)
        receipt['counts']['plot_calls_completed']+=1
        check('one_undeformed_png_exists',(run/'right_prepared.png').is_file())
        diagnostics.update(status='pass',geometry_compatibility_passed=True)
        write(run/'diagnostics.json',diagnostics)
        page=['# 圆形工件右移：未变形兼容性准备','',
            '仅构建和保存一个candidate；旧中心(71,40)与新中心(74,40)，r9 mm。baseline从同一resident网格重建，不做第二模型。',
            '17目标ordered_cycle及input1.40仅作为任务保存，没有执行任何加载或卸载；除center_x及四说明字段，其余任务物理保持。','',
            '![同网格基准与右移候选的未变形四面板](right_prepared.png)','',
            '网格域右界84 mm、机构固定尖端参考(80,30)和原LF背景provenance到80 mm分别解释；不把背景最右节点选成机构尖端。',
            '实际圆由cell-centre选择形成Q1阶梯边界；解析圆仅参考。nearest与tip-to-boundary均unsigned，不是signed gap或接触开始。',
            '端口箭头只声明方向，未计算变形、反力、应力、压力或接触力。右侧介质/边界约束和全部原build门见layout与diagnostics。',
            '本轮不授力学、有效夹持、释放、稳定性、独参或HF5资格；后续是否短程求解由本次实际准备结果另行安排。','',
            '[完整检查](diagnostics.json) · [驻留几何对照](layout.json) · [新任务](task.json) · [唯一候选模型](model/model.json)','',
            '|检查|通过|','|---|---|']
        page += ['|'+name+'|'+str(passed)+'|' for name,passed in diagnostics['checks'].items()]
        (run/'REVIEW.md').write_text('\n'.join(page).rstrip()+'\n',encoding='utf-8',newline='\n')
        phase='final_binding_and_seal'
        bindings()
        receipt['all_bindings_unchanged']=True
        outputs=seal()
        seal_scope='complete_inside_original_helper_window'
        checkpoint()
        receipt['status']='pass'
    except BaseException as error:
        diagnostics.update(status='not_pass',failure=dict(phase=phase,exception_class=type(error).__name__,code=getattr(error,'code',None),reason=str(error)))
        receipt.update(status='not_pass',error=deepcopy(diagnostics['failure']))
        write(run/'diagnostics.json',diagnostics)
        if not stop.exists() and perf_counter()-STARTED<=protocol['helper_seconds'] and process.memory_info().rss<=protocol['sampled_RSS_bytes']:
            try:
                outputs=seal();seal_scope='actual_partial_inside_original_helper_window'
            except BaseException:
                seal_scope='not_complete_before_resource_close'
    receipt.update(phase=phase,events=dict(events),checks_completed=len(diagnostics['checks']),checks_passed=sum(diagnostics['checks'].values()),
        outputs=outputs,output_identity_seal=seal_scope,wrapper_binding_file_reads=dict(binding_reads),
        read_scope='Only one unique old LF geometry NPZ allowed; builder/loader/writer may reread its original bytes. No old model/state/scientific-results input; no helper NPZ decoding or universal file-open hook.',
        helper_seconds=protocol['helper_seconds'],elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak,sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()),completed_utc=datetime.now(timezone.utc).isoformat(),requested_targets_executed=False,
        old_records_rewritten=False,source_bindings=protocol['source_bindings'])
    write(receipt_file,receipt)
    print(json.dumps(dict(status=receipt['status'],phase=phase,counts=receipt['counts'],checks=receipt['checks_completed'],error=receipt.get('error'))),flush=True)
    if receipt['status']!='pass':
        raise RuntimeError('L-CRIGHT1 closed not_pass; no retry or following phase')


if __name__=='__main__':
    main()
