"""One-time, data-only export of the explicitly authorized LF snapshot subset.

This script belongs outside the HF runtime. It never imports LF packages.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import platform
import sys
import zipfile

import numpy as np
from hf_eval.data import write_geometry

SELECTED = {
    'inverter': 'inverter__sweep__kin_1e+01__kout_1e-01',
    'gripper': 'gripper__sweep__kin_1e+01__kout_1e+00',
}
ARRAYS = ('solid', 'design', 'passive_solid', 'passive_void')

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def array_digest(a):
    a=np.asarray(a)
    head=json.dumps({'dtype':a.dtype.str,'shape':list(a.shape)},sort_keys=True,separators=(',',':')).encode()
    return digest(head+b'\0'+a.tobytes(order='C'))

class Snapshot:
    def __init__(self,path):
        self.path=path;self.z=zipfile.ZipFile(path)
        roots={PurePosixPath(n).parts[0] for n in self.z.namelist()}
        if len(roots)!=1:raise ValueError('Expected one top-level directory in LF snapshot')
        self.prefix=roots.pop()+'/'
    def bytes(self,name):return self.z.read(self.prefix+name)
    def json(self,name):return json.loads(self.bytes(name))
    def arrays(self,name):
        with np.load(io.BytesIO(self.bytes(name)),allow_pickle=False) as z:
            return {k:z[k].copy() for k in z.files}
    def close(self):self.z.close()

def source_records(s: Snapshot):
    records=[]
    for case in SELECTED:
        for family in ('spring_sweep','refine','generation_axes'):
            mesh='160x80' if family=='refine' else '80x40'
            base=f'research/{family}_{case}_{mesh}_v1'
            d=s.json(base+'/index.json');data=s.arrays(base+'/final_densities.npz')
            rows=d['cells' if family=='spring_sweep' else 'runs' if family=='refine' else 'rows']
            for row in rows:
                if family=='spring_sweep':
                    ident=f"{case}__sweep__{row['path']}";key='rho_physical_final'
                    idx=[d['k_hat_in'].index(row['k_hat_in']),d['k_hat_out'].index(row['k_hat_out'])]
                    rho=data[key][tuple(idx)];summary=base+'/'+row['path']+'/summary.json'
                elif family=='refine':
                    ident=f"{case}__refine__{PurePosixPath(row['path']).name}"
                    key='rho__'+PurePosixPath(row['path']).name;idx=None;rho=data[key]
                    summary=base+'/'+row['path']+'/summary.json'
                else:
                    ident=row['id'];key='rho__'+ident;idx=None;rho=data[key];summary=None
                records.append({'record_id':ident,'case_family':case,'family':family,
                    'operation':'baseline_density_reuse_and_reanalysis' if row.get('condition')=='baseline' else 'archived_optimization_terminal_record',
                    'source_index':f'source_members/{base}/index.json',
                    'density_asset':{'path':f'source_members/{base}/final_densities.npz','field':key,'index':idx,
                        'shape_yx':list(rho.shape),'array_sha256':array_digest(rho)},
                    'source_summary':f'source_members/{summary}' if summary else None,
                    'source_row':row,'source_provenance':d.get('provenance'),
                    'source_cost_seconds':row.get('elapsed_seconds'),
                    'source_cost_scope':'baseline_reanalysis' if row.get('condition')=='baseline' else 'recorded_driver_time_including_analysis',
                    'historical_paths_in_original_fields':'inert_provenance_only_never_runtime_dependencies',
                    'new_optimization_in_HF1':False})
    return records

def archive_data(s: Snapshot,out: Path,archive_hash: str):
    """Retain complete data asset inventory while excluding every LF code file."""
    allowed={'.json','.npz','.npy','.yaml','.png','.jpg','.jpeg'}
    roots=('research/','reference/','tests/data/','contracts/')
    attribution={'THIRD_PARTY_NOTICES.md','third_party/AuTO_frozen/LICENSE',
                 'third_party/AuTO_frozen/PROVENANCE.md','reference/README.md',
                 'reference/source_geometry/SOURCE.md','tests/data/README.md'}
    manifest=[]
    for info in s.z.infolist():
        if info.is_dir():continue
        name=info.filename.removeprefix(s.prefix);p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe ZIP member')
        if not ((name.startswith(roots) and p.suffix.lower() in allowed) or name in attribution):continue
        data=s.z.read(info)
        if p.suffix=='.npz':
            with np.load(io.BytesIO(data),allow_pickle=False) as z:
                for key in z.files:
                    if z[key].dtype.kind=='O':raise ValueError('Object field in source NPZ')
        elif p.suffix=='.npy':
            if np.load(io.BytesIO(data),allow_pickle=False).dtype.kind=='O':raise ValueError('Object field in source NPY')
        dest=out/'archive'/'source_members'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        manifest.append({'path':'source_members/'+name,'original_zip_member':info.filename,
                         'sha256':digest(data),'bytes':len(data),'role':'inert_original_data_or_attribution'})
    records=source_records(s)
    write_json(out/'archive'/'generation_records.json',{'schema_version':'hf-source-archive-1.0',
        'stored_record_count':len(records),'records':records,'deduplication_policy':'preserve_every_record_and_cost'})
    groups=collections.defaultdict(list)
    for rec in records:groups[rec['density_asset']['array_sha256']].append(rec['record_id'])
    write_json(out/'archive'/'density_identity_groups.json',{'identity_scope':'dtype+shape+C-order density bytes; not HF geometry identity',
        'groups':[{'array_sha256':h,'record_ids':ids} for h,ids in groups.items()]})
    supplementary=[]
    for p,key,role,metadata in [
        ('research/gripper_80x40_v1/final_arrays.npz','rho_physical_final','separate_archived_pilot','research/gripper_80x40_v1/summary.json'),
        ('reference/auto_inverter_40x20/final/reference.npz','xphys','AuTO_reference_different_physical_profile','reference/auto_inverter_40x20/final/reference.json'),
        ('tests/data/M4_battery_v2_m3_final_160_p3_160x80_arrays_subset.npz','measurement_rho_physical','historical_test_fixture_original_full_record_not_supplied','tests/data/M4_battery_v2_m3_final_160_p3_160x80_metrics.json')]:
        a=s.arrays(p)[key]
        supplementary.append({'record_id':'supplementary:'+p+':'+key,'role':role,
            'density_asset':{'path':'source_members/'+p,'field':key,'shape_yx':list(a.shape),'array_sha256':array_digest(a)},
            'source_metadata':'source_members/'+metadata,'new_optimization_in_HF1':False})
    write_json(out/'archive'/'supplementary_terminal_records.json',supplementary)
    geometry_files=[m for m in manifest if m['path'].endswith('/geometry.npz')]
    handoffs={}
    for version,path in [('v1','research/diversity_selection_v1/handoff_v1.json'),('v2','research/handoff_v2/handoff_v2.json')]:
        h=s.json(path);entries=[]
        for case,c in h['cases'].items():
            for row in c['designs' if version=='v1' else 'handoff']:
                d={'record_id':row['id'],'case_family':case}
                for k in ('geometry','outline'):
                    t=row[k]
                    if t.startswith('designs/'):t='research/handoff_v2/'+t
                    d[k]='source_members/'+t
                    if not (out/'archive'/d[k]).is_file():raise ValueError('Missing archived handoff dependency')
                entries.append(d)
        handoffs[version]={'source':'source_members/'+path,'count':len(entries),'entries':entries}
    write_json(out/'archive'/'handoff_subsets.json',handoffs)
    write_json(out/'archive'/'source_index.json',{'schema_version':'hf-source-archive-1.0','source_archive_sha256':archive_hash,
        'source_archive_basename':s.path.name,'member_root':s.prefix,'asset_count':len(manifest),'assets':manifest,
        'data_retention':{'all_six_density_containers':True,'generation_records':len(records),
            'baseline_replay_records':sum(r['operation']=='baseline_density_reuse_and_reanalysis' for r in records),
            'byte_identity_groups':len(groups),'supplementary_terminal_records':len(supplementary),
            'geometry_npz_files':len(geometry_files),'outline_files':sum(x['path'].endswith('/outline.json') for x in manifest)},
        'path_policy':'Only manifest and normalized archive links are package paths. Paths/commands inside byte-exact original records are inert history.',
        'known_historical_detail_gaps':['generation_axes per-run directories and raw design histories absent in supplied ZIP; consolidated rho/clean and index rows retained',
            'archived milestones absent; not restored as runtime dependencies','full AuTO submodule absent; no LF execution required']})
    return manifest,records

def export_real(s:Snapshot,out:Path,case:str,ident:str,archive_hash:str,records):
    base=f'research/geometry_extraction_v1/candidates/{ident}'
    summary=s.json(base+'/summary.json');ds=summary['density_source']
    original=s.arrays(base+'/geometry.npz');density_container=s.arrays(ds['file'])
    density=density_container[ds['key']][tuple(ds['index'])]
    clean=original['clean'];ny,nx=clean.shape
    if (ny,nx)!=(40,80):raise ValueError('Selected geometry changed native grid')
    arrays={'solid':clean,'design':density_container['design_mask'],
            'passive_solid':density_container['passive_solid_mask'],'passive_void':density_container['passive_void_mask']}
    record=next(r for r in records if r['record_id']==ident)
    index_path=record['source_index'].removeprefix('source_members/');index=s.json(index_path);cr=index['case_record']
    run_summary_path=record['source_summary'].removeprefix('source_members/');run=s.json(run_summary_path)
    ports={k:{'points_mm':[v['coordinates_mm'][0],v['coordinates_mm'][-1]],'direction':v['direction'],
               'averaging':'normalized_reference_arclength_trapezoid'} for k,v in cr['ports'].items()}
    metadata={'schema_version':'hf-geometry-1.0','case_family':case,
        'grid':{'shape_yx':[ny,nx],'origin_mm':[0.,0.],'cell_size_mm':cr['element_mm'],
            'axes':[[1,0],[0,1]],'extent_mm':cr['domain_mm'],'array_order':'C_yx_bottom_up','value_location':'cell'},
        'thickness_mm':cr['thickness_mm'],'model_extent':{'kind':'lower_half','symmetry_axis':{'normal':[0,1],'offset_mm':40.}},
        'region_tags':{'support':{'points_mm':cr['fixed_segment_mm'],'components':[0,1]},
                       'symmetry':{'points_mm':[[0,40],[60 if case=='gripper' else 80,40]],'components':[1]},**ports},
        'source_record_ids':[ident],
        'processing':{'source_kind':'archived_LF_optimization_budget_terminal','authority_source_key':'clean',
            'source_native_grid_preserved':True,'lossless_bool_to_uint8':True,'new_threshold_or_cleanup_applied':False,
            'original_threshold':summary['diagnostics']['threshold'],
            'historical_cleaning':'eight-neighbor load-path selection; opened arrays diagnostic only',
            'historical_removed_island_cells':int((original['solid']&~clean).sum()),
            'source_symmetry_policy':cr['symmetry_policy'],
            'source_symmetry_points_mm':[[0,40],[80,40]],
            'imported_entity_symmetry_points_mm':[[0,40],[60 if case=='gripper' else 80,40]],
            'source_symmetry_note':'full_midline includes LF soft gap; gripper canonical tag retains entity symmetry segment x0..60 only; source void constraints are not copied',
            'provenance_record':'provenance/source_record.json','role':'diagnostic_HF1_candidate_qualification_pending'}}
    directory=out/'canonical'/case
    geometry_path=write_geometry(directory,metadata,arrays)
    provenance=directory/'provenance';provenance.mkdir(parents=True,exist_ok=True)
    for source,target in [(base+'/geometry.npz','original_geometry.npz'),(base+'/outline.json','outline.json'),
                          (base+'/summary.json','geometry_extraction_summary.json'),(run_summary_path,'source_run_summary.json')]:
        (provenance/target).write_bytes(s.bytes(source))
    np.savez_compressed(provenance/'continuous_source.npz',rho_physical=density,
        raw_design=density_container['raw_design_final'][tuple(ds['index'])],
        design_mask=arrays['design'],passive_solid_mask=arrays['passive_solid'],passive_void_mask=arrays['passive_void'])
    write_json(provenance/'source_case_profile.json',{'case_record':cr,'source_profile_common':index['source_profile_common'],
        'reference':index['reference'],'source_provenance':index['provenance'],
        'geometry_extraction_provenance':s.json('research/geometry_extraction_v1/index.json')['provenance'],
        'handoff_v2_provenance':s.json('research/handoff_v2/handoff_v2.json')['provenance']})
    assets=[]
    for p in sorted(provenance.iterdir()):
        if p.is_file() and p.name!='source_record.json':assets.append({'path':p.name,'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size})
    write_json(provenance/'source_record.json',{'schema_version':'hf-generation-1.0','record_id':ident,
        'source_archive_sha256':archive_hash,'source_archive_basename':s.path.name,
        'original_geometry_member':s.prefix+base+'/geometry.npz','original_geometry_sha256':digest(s.bytes(base+'/geometry.npz')),
        'original_density_member':s.prefix+ds['file'],'original_density_sha256':digest(s.bytes(ds['file'])),
        'original_density_key':ds['key'],'original_density_index':ds['index'],
        'continuous_density_role':'provenance_only_not_authoritative_geometry','assets':assets,
        'optimization_status':{'stop_reason':run['source_profile']['stop_reason'],'converged':run['source_profile']['converged'],
            'updates':run['source_profile']['updates'],'initial_design':run['source_profile']['initial_design'],'random_seed':None,
            'seed_reason':'selected uniform initial field does not use RNG'},
        'source_metrics':run['source_result']['final'],'source_lf_profile':run['source_profile'],
        'source_cost_seconds':record['source_cost_seconds'],'source_cost_scope':record['source_cost_scope'],
        'new_optimization_in_HF1':False,'paths_and_commands_in_source_documents':'inert_history_only'})
    saved=json.loads(Path(geometry_path).read_text())
    return {'case_family':case,'source_record_id':ident,'geometry_id':saved['geometry_id'],
            'geometry':Path(geometry_path).relative_to(out).as_posix(),'task':f'tasks/{case}_linear_interface_smoke.json',
            'source_record':(provenance/'source_record.json').relative_to(out).as_posix(),'evaluation_role':'linear_interface_smoke_only'}

def export_marker(out:Path):
    a=np.array([[1,1,1,0,0,0,0],[1,0,0,0,0,0,0],[1,1,0,0,0,0,0],
                [0,0,0,0,0,0,0],[0,0,0,0,0,1,1]],dtype=np.uint8)
    arrays={'solid':a,'design':np.ones_like(a),'passive_solid':np.zeros_like(a),'passive_void':np.zeros_like(a)}
    meta={'schema_version':'hf-geometry-1.0','case_family':'synthetic',
        'grid':{'shape_yx':[5,7],'origin_mm':[10.,20.],'cell_size_mm':[2.,3.],'axes':[[1,0],[0,1]],
                'extent_mm':[14.,15.],'array_order':'C_yx_bottom_up','value_location':'cell'},
        'thickness_mm':1.,'model_extent':{'kind':'full'},
        'region_tags':{'support':{'points_mm':[[10,20],[10,26]],'components':[0,1]},
            'input':{'points_mm':[[10,20],[10,23]],'direction':[1,0],'averaging':'normalized_reference_arclength_trapezoid'},
            'output':{'points_mm':[[24,32],[24,35]],'direction':[-1,0],'averaging':'normalized_reference_arclength_trapezoid'}},
        'source_record_ids':['synthetic_asymmetric_marker_v1'],
        'processing':{'source_kind':'synthetic_validation_fixture','author':'Codex HF-1 implementation',
            'purpose':'expose vertical flip, transpose, origin and anisotropic scale errors; no mechanics analysis',
            'optimized_LF_candidate':False,'expected_solid_indices_yx':np.argwhere(a).tolist(),
            'expected_centres_xy_mm':[[10+(ix+.5)*2,20+(iy+.5)*3] for iy,ix in np.argwhere(a)],
            'expected_solid_area_mm2':48.,'expected_components4':2}}
    p=write_geometry(out/'validation'/'asymmetric_marker',meta,arrays)
    saved=json.loads(Path(p).read_text())
    return {'geometry':Path(p).relative_to(out).as_posix(),'geometry_id':saved['geometry_id'],
            'source_kind':'synthetic_validation_fixture','evaluate_by_default':False}

def task_configs(out:Path):
    for case in SELECTED:
        task={'schema_version':'hf-task-1.0','task_id':f'hf1_{case}_linear_interface_smoke_v1','case_family':case,
            'purpose':'linear_interface_smoke_only','parameter_origin':'authorized_pilot_not_research_task',
            'material':{'E_MPa':1.,'nu':.3,'formulation':'plane_strain'},'input':{'tag':'input','displacement_mm':1e-6},
            'output':{'tag':'output','spring_N_per_mm':0.},
            'constraints':[{'tag':'support','components':[0,1]},{'tag':'symmetry','components':[1]}],
            'support_selection':'solid_incident_nodes_only','input_auxiliary_spring_N_per_mm':0.,'workpiece':None,'third_medium':None,
            'qualification_criteria':{'max_design_volume_fraction':None,'min_feature_mm':None},'reference_state':'undeformed'}
        write_json(out/'tasks'/f'{case}_linear_interface_smoke.json',task)
    write_json(out/'solvers'/'hf1_q1_solid_linear_v1.json',{'schema_version':'hf-solver-1.0','solver_id':'hf1_q1_solid_linear_v1',
        'analysis':'solid_linear_q1','quadrature':'gauss_2x2','dtype':'float64','linear_solver':'scipy_superlu',
        'relative_force_tolerance':1e-9,'constraint_relative_tolerance':1e-10,'constraint_scale_floor_mm':1e-6,'time_limit_seconds':300})

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-zip',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--rebuild',action='store_true');args=parser.parse_args()
    src=args.source_zip.resolve();out=args.output.resolve()
    if (out/'dataset_index.json').exists() and not args.rebuild:raise SystemExit('Dataset exists; use --rebuild only for an intentional deterministic rewrite')
    if src.is_relative_to(out):raise SystemExit('Original ZIP must stay outside geometry_dataset')
    archive_hash=digest(src.read_bytes());out.mkdir(parents=True,exist_ok=True);s=Snapshot(src)
    try:
        archived,records=archive_data(s,out,archive_hash)
        subset=[export_real(s,out,case,ident,archive_hash,records) for case,ident in SELECTED.items()]
        marker=export_marker(out);task_configs(out)
        if digest(src.read_bytes())!=archive_hash:raise RuntimeError('Source ZIP changed during read-only export')
        write_json(out/'dataset_index.json',{'schema_version':'hf-dataset-1.0','dataset_id':'hf1_lf_snapshot_native_pair_v1',
            'source_archive_sha256':archive_hash,'authority_representation':'native_grid_binary_cells',
            'current_canonical_subset':subset,'synthetic_validation':[marker],
            'canonical_subset':[{'case_family':x['case_family'],'geometry_path':x['geometry'],'task_path':x['task'],
                                 'geometry_id':x['geometry_id'],'source_record_id':x['source_record_id']} for x in subset],
            'synthetic_samples':[{'geometry_path':marker['geometry'],'case_family':'synthetic','evaluate_by_default':False}],
            'solver_path':'solvers/hf1_q1_solid_linear_v1.json','archive_index':'archive/source_index.json',
            'all_generation_records':'archive/generation_records.json','supplementary_records':'archive/supplementary_terminal_records.json',
            'archived_handoff_subsets':'archive/handoff_subsets.json','solver':'solvers/hf1_q1_solid_linear_v1.json',
            'file_manifest':'file_manifest.json','scope':'data and authorized diagnostic tasks; research qualification pending',
            'new_LF_optimization_runs':0,'geometry_changes':0,'historical_paths':'inert provenance only'})
        write_json(out/'evidence'/'export_report.json',{'schema_version':'hf-export-evidence-1.0','source_sha256_before':archive_hash,
            'source_sha256_after':digest(src.read_bytes()),'source_unchanged':True,'archive_data_files':len(archived),
            'source_records':len(records),'canonical_real_geometries':len(subset),'synthetic_markers':1,
            'LF_imports':False,'LF_optimization_runs':0,'HF_writer':'hf_eval.data.write_geometry',
            'python':platform.python_version(),'platform':platform.platform(),'numpy':np.__version__,
            'exporter_sha256':digest(Path(__file__).read_bytes()),'geometry_changes':0})
        print(json.dumps({'output':str(out),'archive_files':len(archived),'source_records':len(records),'canonical_ids':[x['geometry_id']for x in subset]}))
    finally:s.close()

if __name__=='__main__':main()
