"""Independent raw-ZIP to exported-package checks, without invoking the writer.

This stays in preparation; it is not an HF runtime dependency or required HF test.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
import numpy as np
from hf_eval.data import load_geometry
from hf_eval.regions import node_coordinates, port_vector, qualify_geometry, region_nodes

def sha(b):return hashlib.sha256(b).hexdigest()

def write_json(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-zip',type=Path,required=True)
    p.add_argument('--dataset',type=Path,required=True);args=p.parse_args();root=args.dataset.resolve()
    source_hash=sha(args.source_zip.read_bytes());index=json.loads((root/'dataset_index.json').read_text())
    assert source_hash==index['source_archive_sha256']
    rows=[];raw={}
    with zipfile.ZipFile(args.source_zip) as z:
        prefix=z.namelist()[0].split('/')[0]+'/'
        def j(name):return json.loads(z.read(prefix+name))
        def arr(name):
            with np.load(io.BytesIO(z.read(prefix+name)),allow_pickle=False) as d:return {k:d[k].copy()for k in d.files}
        for entry in index['canonical_subset']:
            case=entry['case_family'];ident=entry['source_record_id']
            base=f'research/geometry_extraction_v1/candidates/{ident}'
            source=arr(base+'/geometry.npz')['clean'];meta=j(base+'/summary.json');ds=meta['density_source']
            original=arr(ds['file']);cr=j(f'research/spring_sweep_{case}_80x40_v1/index.json')['case_record']
            expected={'solid':source,'design':original['design_mask'],'passive_solid':original['passive_solid_mask'],
                      'passive_void':original['passive_void_mask']}
            g=load_geometry(root/entry['geometry_path']);delta={}
            for name,a in expected.items():
                assert g.arrays[name].shape==a.shape
                delta[name]=int(np.count_nonzero(g.arrays[name]!=a));assert delta[name]==0
            grid=g.grid;assert grid['shape_yx']==list(source.shape)
            assert grid['origin_mm']==[0.,0.] and grid['cell_size_mm']==cr['element_mm'] and grid['extent_mm']==cr['domain_mm']
            assert grid['axes']==[[1,0],[0,1]] and grid['array_order']=='C_yx_bottom_up' and grid['value_location']=='cell'
            assert g.metadata['thickness_mm']==cr['thickness_mm']
            xy=node_coordinates(g);ports={}
            for name,old in cr['ports'].items():
                b,nodes,weights=port_vector(g,g.metadata['region_tags'][name])
                np.testing.assert_array_equal(nodes,np.asarray(old['node_ids']))
                np.testing.assert_array_equal(xy[nodes],np.asarray(old['coordinates_mm']))
                np.testing.assert_array_equal(weights,np.asarray(old['weights']))
                np.testing.assert_array_equal(g.metadata['region_tags'][name]['direction'],old['direction'])
                assert abs(float(weights.sum())-1.)<=1e-15
                expected_b=np.zeros_like(b)
                for n,w in zip(nodes,weights):expected_b[2*n:2*n+2]=w*np.asarray(old['direction'])
                np.testing.assert_array_equal(b,expected_b)
                ports[name]={'nodes_identical':True,'coordinates_identical':True,'weights_identical':True,
                             'direction_identical':True,'weights':weights.tolist()}
                raw[case+'__'+name+'_xy_mm']=xy[nodes];raw[case+'__'+name+'_weights']=weights
            supports=region_nodes(g,g.metadata['region_tags']['support'])
            support_expected=np.column_stack([np.zeros(9),np.arange(9)])
            np.testing.assert_array_equal(xy[supports],support_expected)
            symmetry=region_nodes(g,g.metadata['region_tags']['symmetry'])
            # Preserve actual entity symmetry geometry, while retaining LF soft-gap
            # full_midline in provenance only; excluded gap nodes are not HF tags.
            entity_symmetry_count=61 if case=='gripper' else 81
            np.testing.assert_array_equal(xy[symmetry],np.column_stack([np.arange(entity_symmetry_count),np.full(entity_symmetry_count,40)]))
            assert cr['symmetry_uy_node_count']==81
            area=float(source.sum()*cr['element_mm'][0]*cr['element_mm'][1])
            imported_area=float(g.solid.sum()*np.prod(grid['cell_size_mm']))
            assert abs(imported_area-area)<=1e-12*area
            q=qualify_geometry(g,{'max_design_volume_fraction':None,'min_feature_mm':None})
            rows.append({'case_family':case,'source_record_id':ident,'geometry_id':g.geometry_id,
                'geometry_path':entry['geometry_path'],'array_changed_cell_counts':delta,
                'shape_yx':list(source.shape),'source_area_mm2':area,'imported_area_mm2':imported_area,
                'relative_area_error':abs(imported_area-area)/area,'thickness_mm':g.metadata['thickness_mm'],
                'solid_volume_mm3_per_half':area*g.metadata['thickness_mm'],'ports':ports,
                'support_region_nodes_identical':True,'entity_symmetry_tag_matches_physical_segment':True,
                'source_symmetry_uy_node_count':81,'imported_entity_symmetry_tag_node_count':entity_symmetry_count,
                'source_symmetry_top_nodes_identical':case!='gripper',
                'source_void_constraints_not_copied':case=='gripper',
                'symmetry_policy_note':'gripper original full_midline x0..80 retained as provenance; canonical physical entity segment x0..60 used for task',
                'qualification':q,'status':'pass_data_identity_and_physical_mapping'})
            raw[case+'__source_solid']=source.astype('uint8');raw[case+'__imported_solid']=g.solid
            raw[case+'__difference']=g.solid.astype('int8')-source.astype('int8')
            raw[case+'__design']=g.arrays['design'];raw[case+'__passive_solid']=g.arrays['passive_solid'];raw[case+'__passive_void']=g.arrays['passive_void']
            raw[case+'__x_edges_mm']=np.arange(81.);raw[case+'__y_edges_mm']=np.arange(41.)
        # Check every copied archive file byte-for-byte against the same supplied ZIP.
        archives=json.loads((root/'archive/source_index.json').read_text());archived_files=0
        for item in archives['assets']:
            target=root/'archive'/item['path'];original=z.read(item['original_zip_member'])
            assert target.read_bytes()==original and sha(original)==item['sha256'];archived_files+=1
        # Verify normalized generation and handoff references stay within package.
        records=json.loads((root/'archive/generation_records.json').read_text())['records']
        for r in records:
            a=r['density_asset'];target=root/'archive'/a['path']
            assert target.resolve().is_relative_to(root)
            with np.load(target,allow_pickle=False) as d:
                value=d[a['field']]
                if a['index'] is not None:value=value[tuple(a['index'])]
                assert list(value.shape)==a['shape_yx']
            assert (root/'archive'/r['source_index']).is_file()
            if r['source_summary'] is not None:assert (root/'archive'/r['source_summary']).is_file()
        handoffs=json.loads((root/'archive/handoff_subsets.json').read_text());links=0
        for h in handoffs.values():
            for e in h['entries']:
                for k in ('geometry','outline'):
                    assert (root/'archive'/e[k]).is_file();links+=1
    marker=load_geometry(root/index['synthetic_samples'][0]['geometry_path'])
    expected_marker=np.array([[1,1,1,0,0,0,0],[1,0,0,0,0,0,0],[1,1,0,0,0,0,0],
                              [0,0,0,0,0,0,0],[0,0,0,0,0,1,1]],dtype='uint8')
    np.testing.assert_array_equal(marker.solid,expected_marker)
    assert marker.grid['origin_mm']==[10.,20.] and marker.grid['cell_size_mm']==[2.,3.]
    centres=np.asarray([[10+(ix+.5)*2,20+(iy+.5)*3]for iy,ix in np.argwhere(marker.solid)])
    expected_centres=np.array([[11,21.5],[13,21.5],[15,21.5],[11,24.5],[11,27.5],[13,27.5],[21,33.5],[23,33.5]])
    np.testing.assert_array_equal(centres,expected_centres)
    assert float(marker.solid.sum()*2*3)==48.
    marker_report={'status':'pass','shape_yx':[5,7],'origin_mm':[10.,20.],'cell_size_mm':[2.,3.],
        'centres_xy_mm':centres.tolist(),'area_mm2':48.,'sensitive_to_vertical_flip':not np.array_equal(marker.solid,np.flipud(marker.solid)),
        'sensitive_to_horizontal_flip':not np.array_equal(marker.solid,np.fliplr(marker.solid)),
        'sensitive_to_transpose':marker.solid.shape!=marker.solid.T.shape,'mechanics_evaluated':False}
    evidence=root/'evidence';evidence.mkdir(exist_ok=True)
    raw['marker__source_solid']=expected_marker;raw['marker__imported_solid']=marker.solid
    raw['marker__difference']=marker.solid.astype('int8')-expected_marker.astype('int8')
    raw['marker__x_edges_mm']=np.arange(10,25,2.);raw['marker__y_edges_mm']=np.arange(20,36,3.)
    raw['marker__expected_centres_xy_mm']=expected_centres
    np.savez_compressed(evidence/'roundtrip_plot_data.npz',**raw)
    plot(raw,evidence)
    assert sha(args.source_zip.read_bytes())==source_hash
    report={'schema_version':'hf-roundtrip-evidence-1.0','status':'pass','source_sha256_before':source_hash,
        'source_sha256_after':sha(args.source_zip.read_bytes()),'source_unchanged':True,
        'comparison_origin':'direct original ZIP read independent of exporter/writer internals','canonical_samples':rows,
        'asymmetric_marker':marker_report,'archive_files_compared_byte_exact':archived_files,
        'generation_record_array_refs_resolved':len(records),'normalized_handoff_file_refs_resolved':links,
        'runtime_provenance_paths':'package_relative; old literal paths never dereferenced',
        'raw_plot_data':'roundtrip_plot_data.npz','figures':['source_import_difference.png','asymmetric_marker_roundtrip.png'],
        'verification_script_sha256':sha(Path(__file__).read_bytes()),'LF_imports':False,'HF_nonlinear_validation':False}
    write_json(evidence/'roundtrip_report.json',report)
    print(json.dumps({'status':'pass','real_samples':len(rows),'archive_files_byte_exact':archived_files,
                      'generation_refs':len(records),'handoff_refs':links,'changed_cells':0}))

def plot(raw,evidence):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig,axes=plt.subplots(2,3,figsize=(15,7.4),constrained_layout=True)
    for i,case in enumerate(('inverter','gripper')):
        for col,(field,title) in enumerate((('source_solid','Archived source clean'),('imported_solid','Imported authority'),('difference','Imported - source'))):
            ax=axes[i,col];d=raw[case+'__'+field]
            if field=='difference':ax.imshow(d,origin='lower',extent=[0,80,0,40],cmap='coolwarm',vmin=-1,vmax=1,interpolation='nearest')
            else:ax.imshow(d,origin='lower',extent=[0,80,0,40],cmap='gray_r',vmin=0,vmax=1,interpolation='nearest')
            ax.set_title(case.capitalize()+' | '+title,fontsize=10);ax.set_xlabel('x [mm]');ax.set_ylabel('y [mm]');ax.set_aspect('equal')
            if field=='difference':
                ax.text(40,20,'0 changed cells\nAll four masks identical',ha='center',va='center',fontsize=11)
            else:
                ax.plot([0,0],[0,8],lw=3,color='#b42318')
                top_end=60 if case=='gripper' and field=='imported_solid' else 80
                ax.plot([0,top_end],[40,40],lw=1.5,ls='--',color='#7753a6')
                ax.annotate('',xy=(11,39),xytext=(1,39),arrowprops={'arrowstyle':'->','color':'#26795f','lw':2})
                if case=='gripper':
                    ax.add_patch(Rectangle((60,28),20,2,facecolor='#d99920',alpha=.8))
                    ax.annotate('',xy=(79,37),xytext=(79,29),arrowprops={'arrowstyle':'->','color':'#2467b0','lw':2})
                else:ax.annotate('',xy=(69,39),xytext=(79,39),arrowprops={'arrowstyle':'->','color':'#2467b0','lw':2})
        axes[i,0].text(0,-.29,'Native 1 × 1 mm cells; t = 20 mm; lower half at y ≤ 40 mm',transform=axes[i,0].transAxes,fontsize=9)
    fig.suptitle('HF-1 exact data transfer | two archived optimized geometries | no geometry changes',fontsize=14)
    fig.savefig(evidence/'source_import_difference.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(11,4.8),constrained_layout=True)
    for ax,(key,title) in zip(axes,[('source_solid','Defined marker'),('imported_solid','Imported marker'),('difference','Difference: 0 cells')]):
        ax.imshow(raw['marker__'+key],origin='lower',extent=[10,24,20,35],cmap='gray_r' if key!='difference' else 'coolwarm',
                  vmin=0 if key!='difference' else -1,vmax=1,interpolation='nearest')
        ax.set_title(title);ax.set_xlabel('x [mm]');ax.set_ylabel('y [mm]');ax.set_aspect('equal')
    fig.suptitle('Synthetic asymmetric marker | 5 × 7 cells; dx=2 mm, dy=3 mm; origin=(10,20) mm\nValidation fixture only; no mechanics analysis',fontsize=11)
    fig.savefig(evidence/'asymmetric_marker_roundtrip.png',dpi=150);plt.close(fig)

if __name__=='__main__':main()
