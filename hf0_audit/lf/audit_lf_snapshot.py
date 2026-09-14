"""HF-0 bounded, read-only inspection of the extracted supplied ZIP.

Does not import or execute LF code; outputs audit evidence and preview data only.
Run from this directory or any cwd with stock Python + numpy/scipy/matplotlib.
"""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from scipy import ndimage

OUT = Path(__file__).resolve().parent
ROOT = OUT / 'snapshot' / 'Diversity-TO-Compliant-O-main'

def read(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8'))

def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def ahash(a):
    a = np.asarray(a)
    return sha(json.dumps({'shape': list(a.shape), 'dtype': a.dtype.str}, sort_keys=True).encode()+b'\0'+a.tobytes(order='C'))

def rel(p):
    return p.relative_to(ROOT).as_posix()

def fields(p):
    with np.load(p, allow_pickle=False) as z:
        return {k: {'shape': list(z[k].shape), 'dtype': str(z[k].dtype), 'array_sha256': ahash(z[k]),
                    'finite': bool(np.isfinite(z[k]).all()) if z[k].dtype.kind in 'fiub' else None}
                for k in z.files}

def masks(case, shape):
    ny, nx = shape
    passive_solid=np.zeros(shape,dtype=bool); passive_void=passive_solid.copy()
    if case=='gripper':
        passive_solid[round(.70*ny):round(.75*ny),round(.75*nx):]=True
        passive_void[round(.75*ny):,round(.75*nx):]=True
    return ~(passive_solid|passive_void),passive_solid,passive_void

def attached(a, xy, hx, hy):
    result=[]
    for x,y in xy:
        ix,iy=round(x/hx),round(y/hy)
        cells=[(j,i) for j in (iy-1,iy) for i in (ix-1,ix) if 0<=i<a.shape[1] and 0<=j<a.shape[0]]
        result.append(any(bool(a[j,i]) for j,i in cells))
    return result

def measure(a, case):
    a=np.asarray(a,dtype=bool); ny,nx=a.shape; hx,hy=80/nx,40/ny
    design,ps,pv=masks(case,a.shape)
    labels4,n4=ndimage.label(a,ndimage.generate_binary_structure(2,1))
    labels8,n8=ndimage.label(a,ndimage.generate_binary_structure(2,2))
    corner=((a[:-1,:-1]&a[1:,1:]&~a[:-1,1:]&~a[1:,:-1]) |
            (a[:-1,1:]&a[1:,:-1]&~a[:-1,:-1]&~a[1:,1:]))
    sy=np.arange(0,8+hy*.5,hy)
    support=np.column_stack([np.zeros(sy.size),sy])
    iy=np.arange(38,40+hy*.5,hy)
    inp=np.column_stack([np.zeros(iy.size),iy])
    oy=np.arange(28 if case=='gripper' else 38,30+hy*.5 if case=='gripper' else 40+hy*.5,hy)
    op=np.column_stack([np.full(oy.size,80),oy])
    def common_path(labels):
        groups=[]
        for xy in (support,inp,op):
            labs=set()
            for x,y in xy:
                ix,iy=round(x/hx),round(y/hy)
                for j in (iy-1,iy):
                    for i in (ix-1,ix):
                        if 0<=i<nx and 0<=j<ny and labels[j,i]:labs.add(int(labels[j,i]))
            groups.append(labs)
        return bool(set.intersection(*groups)), [sorted(g) for g in groups]
    path4,port_components4=common_path(labels4)
    path8,port_components8=common_path(labels8)
    return {'solid_cells':int(a.sum()),'design_cells':int(design.sum()),'passive_solid_cells':int(ps.sum()),
            'passive_void_cells':int(pv.sum()),'solid_area_mm2':float(a.sum()*hx*hy),
            'solid_volume_mm3_per_half':float(a.sum()*hx*hy*20),
            'design_solid_cells':int((a&design).sum()),'design_volume_fraction':float(a[design].mean()),
            'total_envelope_volume_fraction':float(a.mean()),
            'components4':int(n4),'components8':int(n8),'load_path4':path4,'load_path8':path8,
            'component_sizes4':sorted(np.bincount(labels4.ravel())[1:].tolist(),reverse=True),
            'corner_only_local_2x2_patterns':int(corner.sum()),
            'support_nodes_xy_mm':support.tolist(),'support_nodes_attached':attached(a,support,hx,hy),
            'input_nodes_attached':attached(a,inp,hx,hy),'output_nodes_attached':attached(a,op,hx,hy),
            'support_input_output_component_ids4':port_components4,
            'passive_solid_preserved':bool(a[ps].all()),'passive_void_preserved':bool((~a[pv]).all()),
            'qualification': 'pending_shared_HF_thresholds', 'formal_HF_eligible': None}

# Every NPZ and NPY is loaded with allow_pickle=False, hashes/fields saved in full.
array_inventory=[]
for p in sorted(ROOT.rglob('*.npz')):
    array_inventory.append({'path':rel(p),'file_sha256':sha(p.read_bytes()),'fields':fields(p)})
for p in sorted(ROOT.rglob('*.npy')):
    a=np.load(p,allow_pickle=False)
    array_inventory.append({'path':rel(p),'file_sha256':sha(p.read_bytes()),'shape':list(a.shape),'dtype':str(a.dtype),'array_sha256':ahash(a)})
write('array_inventory.json',array_inventory)

# One record per stored generation/reanalysis entry: never collapse provenance.
generation=[]
for case in ['inverter','gripper']:
    for family in ['spring_sweep','refine','generation_axes']:
        mesh='160x80' if family=='refine' else '80x40'
        base=f'research/{family}_{case}_{mesh}_v1'
        index=read(base+'/index.json')
        with np.load(ROOT/base/'final_densities.npz',allow_pickle=False) as z:
            rows=index['cells' if family=='spring_sweep' else 'runs' if family=='refine' else 'rows']
            for row in rows:
                if family=='spring_sweep':
                    ident=f"{case}__sweep__{row['path']}"; key='rho_physical_final'
                    address=[index['k_hat_in'].index(row['k_hat_in']),index['k_hat_out'].index(row['k_hat_out'])]
                    rho=z[key][tuple(address)]
                    summary_path=base+'/'+row['path']+'/summary.json'
                elif family=='refine':
                    ident=f"{case}__refine__{Path(row['path']).name}"; key='rho__'+Path(row['path']).name
                    address=None;rho=z[key];summary_path=base+'/'+row['path']+'/summary.json'
                else:
                    ident=row['id'];key='rho__'+ident;address=None;rho=z[key];summary_path=None
                summary=read(summary_path) if summary_path and (ROOT/summary_path).exists() else None
                generation.append({'record_id':ident,'case':case,'family':family,'source_index':base+'/index.json',
                    'density':{'file':base+'/final_densities.npz','key':key,'index':address,'shape':list(rho.shape),'array_sha256':ahash(rho)},
                    'source_row':row,'source_summary':summary_path,
                    'source_profile':summary.get('source_profile') if summary else index.get('generation_common'),
                    'source_run_final':{k:v for k,v in summary.get('source_result',{}).items() if k!='history'} if summary else None,
                    'provenance':index.get('provenance'),
                    'operation': 'reuse_baseline_density_and_remeasure' if row.get('condition')=='baseline' else 'archived_optimization_terminal_record',
                    'clean_field': 'clean__'+ident if family=='generation_axes' else None,
                    'cost_seconds_recorded':row.get('elapsed_seconds'),
                    'cost_scope':'analysis_replay' if row.get('condition')=='baseline' else 'archived_driver_timing; may include analysis',
                    'runtime_replayed_this_audit':False})
groups=collections.defaultdict(list)
for g in generation:groups[g['density']['array_sha256']].append(g['record_id'])
write('generation_records.json',generation)
write('density_identity_groups.json',{'comparison':'dtype+shape+C-order bytes; do not erase original records/costs',
    'groups':[{'array_sha256':h,'record_ids':ids} for h,ids in groups.items()]})

# Trace authoritative data routes from both handoffs, extraction index, and density pool.
links=[]
def link(source, pointer, target, key=None, index=None):
    p=ROOT/target
    status='exists' if p.exists() else 'missing'
    item={'source':source,'pointer':pointer,'target':target,'status':status}
    if key is not None:
        item.update(npz_key=key,array_index=index)
        try:
            with np.load(p,allow_pickle=False) as z:
                a=z[key]
                if index is not None:a=a[tuple(index)]
                item.update(array_shape=list(a.shape),array_sha256=ahash(a),status='array_resolved')
        except Exception as e:item.update(status='missing_or_invalid_array',error=str(e))
    links.append(item);return item

poolpath='research/l3_interval_policy_v1/candidates_v1.json'
for i,c in enumerate(read(poolpath)['candidates']):
    ds=c['density_source'];link(poolpath,f'/candidates/{i}/density_source',ds['file'],ds['key'],ds.get('index'))
extractpath='research/geometry_extraction_v1/index.json'
extractindex=read(extractpath)
for i,c in enumerate(extractindex['rows']):
    base='research/geometry_extraction_v1/'+c['path']
    for name in ['geometry.npz','outline.json','summary.json']:link(extractpath,f'/rows/{i}/path',base+'/'+name)
    ds=read(base+'/summary.json')['density_source']
    link(base+'/summary.json','/density_source',ds['file'],ds['key'],ds.get('index'))
handoff_records=[]
for v,path in [(1,'research/diversity_selection_v1/handoff_v1.json'),(2,'research/handoff_v2/handoff_v2.json')]:
    h=read(path)
    for case,obj in h['cases'].items():
        for i,c in enumerate(obj['designs' if v==1 else 'handoff']):
            resolved={}
            for k in ['geometry','outline']:
                t=c[k];t='research/handoff_v2/'+t if v==2 and t.startswith('designs/') else t
                resolved[k]=t;link(path,f'/cases/{case}/{i}/{k}',t)
            if c.get('new_in_v2'):
                base=f'research/generation_axes_{case}_80x40_v1'
                for k in ['rho__','clean__']:link(path,f'/cases/{case}/{i}/source_inferred_from_build_handoff_set.py',base+'/final_densities.npz',k+c['id'])
                with np.load(ROOT/resolved['geometry'],allow_pickle=False) as ga,np.load(ROOT/base/'final_densities.npz',allow_pickle=False) as ax:
                    source_equal=bool(np.array_equal(ga['clean'],ax['clean__'+c['id']]))
            else: source_equal=None
            handoff_records.append({'handoff_version':v,'case':case,'entry':c,'resolved':resolved,
                                    'new_v2_clean_equals_axes_clean':source_equal})
write('data_reference_trace.json',links)
write('handoff_records.json',handoff_records)

# Scan every JSON leaf that is a path-shaped value, separately from strict data trace.
# This is a reference inventory, not execution of old paths or workflow instructions.
path_refs=[]
def walk(x,pointer=''):
    if isinstance(x,dict):
        for k,v in x.items():yield from walk(v,pointer+'/'+str(k))
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,pointer+'/'+str(i))
    elif isinstance(x,str):yield pointer,x
for p in sorted(ROOT.rglob('*.json')):
    d=json.loads(p.read_text(encoding='utf-8'))
    for pointer,s in walk(d):
        s=s.replace('\\','/')
        if s.startswith(('http:','https:')):continue
        leaf=pointer.rsplit('/',1)[-1]
        pathlike=bool(re.match(r'^(research|contracts|reference|third_party|milestones|tmp|tests|scripts|env|src|distribution|authorizations|errata|docs|designs|candidates|runs|coarse_reanalysis)/[^\n]+$',s))
        pathlike=pathlike or (leaf in ['path','file','geometry','outline','source','density_file'] and bool(re.fullmatch(r'[^\n]+\.(json|npz|npy|yaml|py|md|txt)',s)))
        pathlike=pathlike or s.startswith(('/mnt/','/home/','C:/','D:/'))
        if not pathlike:continue
        if len(s)>400 or ' (frozen' in s or ' (archiv' in s or ' and ' in s or ' are ' in s:continue
        choices=[ROOT/s,p.parent/s]
        found=[rel(c.resolve()) for c in choices if c.exists() and c.resolve().is_relative_to(ROOT.resolve())]
        path_refs.append({'source':rel(p),'pointer':pointer,'literal':s,'resolved_paths':sorted(set(found)),
                         'status':'resolved' if found else 'historical_absolute_path' if s.startswith(('/mnt/','/home/','C:/','D:/')) else 'missing_literal_path'})
write('json_path_references.json',path_refs)

# Independently measure every stored clean geometry representation and inspect outlines.
geometries=[]
for p in sorted(ROOT.rglob('geometry.npz')):
    case='gripper' if 'gripper__' in p.as_posix() else 'inverter'
    with np.load(p,allow_pickle=False) as z:a=z['clean']
    o=read(rel(p.with_name('outline.json')))
    areas=[];closed=[];repeated_endpoint=[]
    for loop in o['loops']:
        q=np.asarray(loop);repeated_endpoint.append(bool(np.array_equal(q[0],q[-1])))
        # Source outline_loops, lines 209-212, breaks before appending start again.
        # The closing edge is implicit; include it in area and edge validation.
        nxt=np.roll(q,-1,axis=0);delta=(nxt-q)/np.asarray([80/a.shape[1],40/a.shape[0]])
        closed.append(bool(np.all(np.isclose(np.abs(delta).sum(axis=1),1.))))
        areas.append(float(.5*np.sum(q[:,0]*nxt[:,1]-nxt[:,0]*q[:,1])))
    geometries.append({'path':rel(p),'case':case,'clean_array_sha256':ahash(a),'fields':fields(p),
        'measurements':measure(a,case),'outline_schema':o['schema'],'outline_explicit_units':o.get('units'),
        'outline_loops':len(areas),'outline_closed':all(closed),'outline_closure_encoding':'implicit_last_to_first',
        'outline_repeats_start_vertex':all(repeated_endpoint) if repeated_endpoint else None,'outline_signed_areas_mm2':areas,
        'outline_total_area_mm2':sum(areas),'outline_area_matches_mask':bool(abs(sum(areas)-a.sum()*80/a.shape[1]*40/a.shape[0])<1e-8)})
write('geometry_asset_measurements.json',geometries)

# Two reviewable proposed mappings, explicitly not a production data package.
selected={'inverter':'inverter__sweep__kin_1e+01__kout_1e-01','gripper':'gripper__sweep__kin_1e+01__kout_1e+00'}
preview_arrays={};mapping_summaries=[]
for case,ident in selected.items():
    base=f'research/geometry_extraction_v1/candidates/{ident}'
    summary=read(base+'/summary.json');ds=summary['density_source']
    gen=next(g for g in generation if g['record_id']==ident)
    ci=read(gen['source_index']);cr=ci['case_record']
    with np.load(ROOT/base/'geometry.npz',allow_pickle=False) as z:a=z['clean'].copy();solid=z['solid'].copy()
    with np.load(ROOT/ds['file'],allow_pickle=False) as z:rho=z[ds['key']][tuple(ds['index'])].copy();source_masks={k:z[k].copy() for k in ['design_mask','passive_solid_mask','passive_void_mask']}
    design,ps,pv=masks(case,a.shape)
    mask_check=all(np.array_equal(source_masks[k],v) for k,v in zip(source_masks,[design,ps,pv]))
    m=measure(a,case)
    mask_digest=sha(np.packbits(np.concatenate([v.ravel(order='C') for v in (design,ps,pv)])).tobytes())
    identity_header={'format':'hf.geometry.raster2d.draft1','shape_yx':list(a.shape),'origin_xy':[0.,0.],
        'axis_vectors_xy':[[1.,0.],[0.,1.]],'cell_size_xy':[1.,1.],'length_unit':'mm','thickness':20.,
        'model_extent':'lower_half','symmetry_plane':{'normal_xy':[0.,1.],'offset':40.}}
    geometry_id='sha256:'+sha(json.dumps(identity_header,sort_keys=True,separators=(',',':')).encode()+b'\0'+a.astype('uint8').tobytes(order='C'))
    mapping={'schema':'hf0.mapping.example.draft1','status':'HF-0_review_only_not_a_production_package',
      'geometry_asset':{'geometry_id':geometry_id,'source_record_ids':[ident], 'case':case,
        'authority':{'format':'NPZ','path':None,'field':'solid','dtype':'uint8','solid_value':1,'void_value':0},
        'proposed_package_path':f'geometries/{case}/geometry.npz',
        'source_to_authority_mapping':{'source_file':base+'/geometry.npz','source_key':'clean',
            'operation':'lossless bool to uint8 only; not executed as production export'},
        'coordinates':identity_header,'domain_size_xy':[80.,40.],'cell_semantics':'piecewise_constant_on_closed_cell_interior; centres at (ix+.5,iy+.5) mm',
        'masks':{'path':None,'proposed_keys':['design','passive_solid','passive_void'],
            'source_file':ds['file'],'source_keys':list(source_masks),'source_arrays_verified_against_physical_regions':mask_check,
            'source_mask_sha256_matches_case_record':mask_digest==cr['mask_sha256'],
            'passive_solid_rectangle_xy_mm':[[60.,28.],[80.,30.]] if case=='gripper' else None,
            'passive_void_rectangle_xy_mm':[[60.,30.],[80.,40.]] if case=='gripper' else None},
        'reference_attachments':{'support':{'region':{'polyline_xy_mm':[[0.,0.],[0.,8.]]},'directions':['ux','uy'],'source_attached_nodes':m['support_nodes_attached']},
            'ports':{k:{'region':{'polyline_xy_mm':[v['coordinates_mm'][0],v['coordinates_mm'][-1]]},
                     'direction_xy':v['direction'],'weights_rule':'normalized_trapezoidal_tributary_length',
                     'source_discrete_coordinates_xy_mm':v['coordinates_mm'],'source_discrete_weights':v['weights'],
                     'reference_direction_and_weights_fixed':True} for k,v in cr['ports'].items()},
            'source_symmetry_policy':cr['symmetry_policy'],'source_symmetry_region_xy_mm':[[0.,40.],[80.,40.]],
            'background_medium_symmetry_is_task_decision':True},
        'processing':{'threshold':summary['diagnostics']['threshold'],'threshold_rule':'rho >= threshold; passive solid forced 1, passive void forced 0',
             'historical_cleaning':'keep 8-connected load-path components touching support/input/output; no fill or thickening',
             'removed_island_cells':int((solid&~a).sum()),'audit_modified_geometry':False,
             'opened_arrays_are_diagnostics_only':True},
        'outline':{'role':'derived_display','source':base+'/outline.json','schema':'dmftd.outline_loops.v1','units':'mm',
            'convention':'implicit last-to-first closure (start not repeated); material left; CCW outer/CW holes; element-edge loops, corner contacts split'},
        'integrity':{'source_file_sha256':sha((ROOT/base/'geometry.npz').read_bytes()),'source_clean_array_sha256':ahash(a),
                     'identity_algorithm':'sha256(canonical compact sorted JSON coordinates header + NUL + uint8 C-order solid bytes); draft, not frozen'}},
      'generation_record':{**gen,'continuous_density_role':'provenance_only_not_geometry','seed':None,
          'seed_reason':'uniform initial field; RNG not used for selected archived run',
          'case_record':cr,'source_continuous_design_volume_fraction':float(rho[design].mean())},
      'qualification_measurement':m,
      'source_limit_comparison':{'volume_fraction_limit':.35,'source_limit_scope':'LF continuous density in design region',
          'binary_exceeds_same_numeric_limit':bool(m['design_volume_fraction']>.35),
          'binary_excess_fraction':m['design_volume_fraction']-.35,'HF_volume_fraction_limit':None},
      'physical_task':{'task_id':None,'task_version':None,'material':None,'input_displacement_path':None,
          'output_load':None,'workpiece':None,'background_medium_domain':None,'qualification_thresholds':None,
          'status':'pending_common_HF_task_definition; source LF springs are generation provenance only'},
      'evaluation_record':{'evaluation_id':None,'solver_version':None,'status':'not_evaluated','response':None}}
    write(f'mapping_{case}.draft.json',mapping)
    mapping_summaries.append({'case':case,'id':ident,'geometry_id':geometry_id,'measurements':m,
                              'mask_source_match':mask_check,'mask_digest_matches':mask_digest==cr['mask_sha256']})
    for k,v in {'clean':a,'rho_source':rho,**source_masks,'x_edges_mm':np.arange(81.),'y_edges_mm':np.arange(41.)}.items():preview_arrays[f'{case}__{k}']=v
    preview_arrays[f'{case}__input_xy_mm']=np.asarray(cr['ports']['input']['coordinates_mm'])
    preview_arrays[f'{case}__output_xy_mm']=np.asarray(cr['ports']['output']['coordinates_mm'])
np.savez_compressed(OUT/'preview_raw_data.npz',**preview_arrays)
write('preview_metadata.json',{'purpose':'HF-0 preview of archived optimized geometries, no new optimization; no mechanical result',
    'source_archive':'Diversity-TO-Compliant-O-main (6).zip','selected':mapping_summaries,
    'units':'mm','raw_arrays':'preview_raw_data.npz','source_metadata':'mapping_inverter.draft.json and mapping_gripper.draft.json'})

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
fig,axes=plt.subplots(1,2,figsize=(14,5.7),constrained_layout=True)
for ax,(case,ident) in zip(axes,selected.items()):
    a=preview_arrays[f'{case}__clean'];m=next(s['measurements'] for s in mapping_summaries if s['case']==case)
    ax.imshow(a,origin='lower',extent=[0,80,0,40],cmap='gray_r',vmin=0,vmax=1,interpolation='nearest')
    if case=='gripper':
        ax.add_patch(Rectangle((60,30),20,10,facecolor='#d4eef9',edgecolor='#4c91a8',alpha=.65))
        ax.add_patch(Rectangle((60,28),20,2,facecolor='#e9a330',edgecolor='#b8791e',alpha=.75))
        ax.text(61,35,'Passive void / jaw gap',fontsize=8,color='#32667e')
        ax.text(62,24,'Passive solid jaw',fontsize=8,color='#916014')
    ax.plot([0,0],[0,8],color='#b42318',lw=5,label='Source support region')
    support=np.asarray(m['support_nodes_xy_mm']); attached_flags=np.asarray(m['support_nodes_attached'])
    ax.scatter(support[:,0],support[:,1],s=18,facecolor=np.where(attached_flags,'#b42318','white'),edgecolor='#b42318',zorder=10)
    ax.plot([0,80],[40,40],ls='--',color='#7753a6',lw=1.4,label='LF source: top uy=0')
    inp=preview_arrays[f'{case}__input_xy_mm'];op=preview_arrays[f'{case}__output_xy_mm']
    ax.plot(inp[:,0],inp[:,1],color='#21795f',lw=4)
    ax.annotate('',xy=(10,39),xytext=(0,39),arrowprops={'arrowstyle':'->','lw':2,'color':'#21795f'})
    ax.text(3,43,'Input +x, y=38..40',fontsize=8,color='#21795f')
    ax.plot(op[:,0],op[:,1],color='#2467b0',lw=4)
    if case=='inverter':
        ax.annotate('',xy=(70,39),xytext=(80,39),arrowprops={'arrowstyle':'->','lw':2,'color':'#2467b0'})
        ax.text(51,43,'Output -x, y=38..40',fontsize=8,color='#2467b0')
    else:
        ax.annotate('',xy=(82,38),xytext=(82,29),arrowprops={'arrowstyle':'->','lw':2,'color':'#2467b0'})
        ax.text(60,43,'Output +y, y=28..30',fontsize=8,color='#2467b0')
    ax.set_xlim(-3,86);ax.set_ylim(-3,46);ax.set_aspect('equal');ax.set_xlabel('x [mm]');ax.set_ylabel('y [mm]')
    ax.set_title(f"{case.capitalize()} | archived clean geometry\n{ident.split('__sweep__')[1]}",fontsize=11)
    ax.text(.01,-.19,f"Area = {m['solid_area_mm2']:g} mm²; t = 20 mm; design fraction = {m['design_volume_fraction']:.6f}\n4-neighbour components = {m['components4']}; attached support nodes = {sum(m['support_nodes_attached'])}/9; HF qualification pending",
            transform=ax.transAxes,fontsize=9)
fig.suptitle('HF-0 source audit | 80 × 40 mm lower-half models | archived geometry, no HF analysis',fontsize=13)
fig.savefig(OUT/'two_real_geometries.png',dpi=160)
plt.close(fig)

summary={'npz_files':sum(p.suffix=='.npz' for p in ROOT.rglob('*')),'npy_files':sum(p.suffix=='.npy' for p in ROOT.rglob('*')),
    'final_densities_files':6,'generation_records_in_six_files':len(generation),'density_byte_identity_groups':len(groups),
    'baseline_replay_records':sum(g['operation']=='reuse_baseline_density_and_remeasure' for g in generation),
    'generation_by_case_family':dict(collections.Counter(g['case']+'/'+g['family'] for g in generation)),
    'geometry_npz_files':len(geometries),'outlines':len(list(ROOT.rglob('outline.json'))),
    'geometry_npz_families':dict(collections.Counter('handoff_v2' if '/handoff_v2/' in g['path'] else 'geometry_extraction_v1' for g in geometries)),
    'handoff_counts':dict(collections.Counter('v'+str(g['handoff_version'])+'/'+g['case'] for g in handoff_records)),
    'new_v2_geometry_count':sum(g['entry'].get('new_in_v2',False) for g in handoff_records),
    'strict_data_reference_count':len(links),'strict_data_reference_failures':[l for l in links if l['status'] not in ['exists','array_resolved']],
    'json_path_references':dict(collections.Counter(l['status'] for l in path_refs)),
    'outline_schema_counts':dict(collections.Counter(g['outline_schema'] for g in geometries)),
    'all_outlines_closed':all(g['outline_closed'] for g in geometries),'all_outline_areas_match_masks':all(g['outline_area_matches_mask'] for g in geometries),
    'geometry_measurement_counts':{'not_single_component4':sum(g['measurements']['components4']!=1 for g in geometries),
      'load_path4_false':sum(not g['measurements']['load_path4'] for g in geometries),'zero_clean_masks':sum(g['measurements']['solid_cells']==0 for g in geometries)},
    'selected':mapping_summaries,
    'additional_terminal_density_evidence_outside_six_files':['research/gripper_80x40_v1/final_arrays.npz:rho_physical_final',
      'reference/auto_inverter_40x20/final/reference.npz:xphys','tests/data/M4_battery_v2_m3_final_160_p3_160x80_arrays_subset.npz:measurement_rho_physical'],
    'not_done':['LF imports','LF optimization','LF tests','production exporter','HF solver','new geometry cleanup']}
write('audit_summary.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ['selected','not_done']},indent=2))
