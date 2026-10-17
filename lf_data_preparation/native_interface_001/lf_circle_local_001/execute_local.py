"""Locate saved free-medium Simpson-J and cellwise Hu extrema; no HF imports."""
from time import perf_counter
STARTED = perf_counter()
from datetime import datetime, timezone
from hashlib import sha256
import csv
import json
from pathlib import Path
import sys
import psutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
CARD = 'L-CLOCAL1'
BASE = 'e30d1024d0e8f1f5c03cbe1752cbd03baf5e70a6'
STATE = '0c8c5b07ad3ef5872502dede2f76cee6a152b9f78d3b0b7f831ebc6286a12455'
POINTS = np.array([(xi,eta) for xi in (-1.,0.,1.) for eta in (-1.,0.,1.)])
XI, ETA = POINTS[:,0], POINTS[:,1]
N = np.column_stack(((1-XI)*(1-ETA),(1+XI)*(1-ETA),(1+XI)*(1+ETA),(1-XI)*(1+ETA)))/4


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    protocol_file, auth_file = STAGE/'protocol.json', STAGE/'author/authorization.json'
    protocol, auth = read(protocol_file), read(auth_file)
    assert protocol['card'] == auth['card'] == auth['approval_card'] == CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_request'] is auth['one_invocation'] is True
    assert isinstance(auth['direct_human_request'],str) and auth['direct_human_request'].strip()
    assert auth['protocol_sha256'] == sha256(protocol_file.read_bytes()).hexdigest()
    assert auth['authorized_execution_source_commit'] == protocol['source_baseline_commit'] == BASE
    assert (protocol['helper_seconds'],protocol['outer_seconds'],protocol['sampled_RSS_bytes']) == (180,240,8*1024**3)
    assert (protocol['selected_accepted_index'],protocol['original_target_index'],protocol['selected_state_sha256']) == (1,7,STATE)
    assert protocol['local_bounds_mm'] == [58,84,25,40.5]
    run, stop = ROOT/protocol['output_directory'], STAGE/'stop_requested.txt'
    assert run == STAGE/'run_001' and not run.exists() and not stop.exists()
    run.mkdir(parents=True,exist_ok=False)
    receipt_file = run/'execution_receipt.json'
    process, peak, phase, outputs = psutil.Process(),0,'bindings',{}
    calls = dict(model_constructions=0,force_calls=0,tangent_calls=0,HP_calls=0,solver_calls=0,
        tests=0,default_installations=0,boundary_searches=0,plots_started=0,plots_completed=0)
    receipt = dict(card=CARD,status='running',protocol_sha256=auth['protocol_sha256'],
        source_baseline_commit=BASE,archives_decoded=0,fields_decoded=0,call_counts=calls)

    def checkpoint():
        nonlocal peak
        memory=process.memory_info()
        peak=max(peak,memory.rss,getattr(memory,'peak_wset',memory.rss))
        if stop.exists() or perf_counter()-STARTED > protocol['helper_seconds'] or peak > protocol['sampled_RSS_bytes']:
            raise RuntimeError('Local observation resource/stop limit')

    def digest(path):
        value=sha256()
        with path.open('rb') as source:
            for block in iter(lambda:source.read(1024*1024),b''):
                checkpoint(); value.update(block)
        checkpoint()
        return value.hexdigest()

    def archive(key,names,declared):
        checkpoint()
        path=ROOT/protocol[key]
        result={}
        with np.load(path,allow_pickle=False) as payload:
            receipt['archives_decoded']+=1
            for name in names:
                value=payload[name]
                info=declared[name]
                assert value.dtype.name==info['dtype'] and list(value.shape)==info['shape']
                assert sha256(value.tobytes(order='C')).hexdigest()==info['sha256']
                result[name]=value
                receipt['fields_decoded']+=1
                checkpoint()
        return result

    def seal():
        sealed={}
        for path in sorted(run.rglob('*')):
            if path.is_file() and path!=receipt_file:
                sealed[path.relative_to(ROOT).as_posix()]=dict(sha256=digest(path),bytes=path.stat().st_size)
        checkpoint()
        return sealed

    write(receipt_file,receipt)
    seal_status='not_complete'
    try:
        all_bindings=protocol['source_bindings']|protocol['input_bindings']
        sizes={}
        for name,pin in all_bindings.items():
            path=ROOT/name
            assert digest(path)==pin,name
            sizes[name]=path.stat().st_size
        metadata=read(ROOT/protocol['model_descriptor_file'])
        point_info=metadata['arrays']['fields']['points']
        assert point_info['dtype']=='float64' and point_info['shape']==[9,2]
        assert sha256(POINTS.tobytes(order='C')).hexdigest()==point_info['sha256']
        selected=read(ROOT/protocol['selected_state_file'])
        production=read(ROOT/protocol['production_result_file'])
        geometry=read(ROOT/protocol['geometry_observation_file'])
        derived=read(ROOT/protocol['derived_observation_file'])
        assert selected['state_sha256']==derived['row']['state_sha256']==STATE
        assert selected['original_target_index']==derived['row']['original_target_index']==7
        assert selected['d']==derived['row']['d_mm']==1.35 and selected['leg']=='loading'
        original=production['states'][1]
        assert all(original[key]==selected[key] for key in selected)
        assert metadata['task']['workpiece']==dict(kind='fixed_rigid',shape='circle',center_mm=[71.,40.],radius_mm=9.,fixed_components=[0,1])
        phase='three_archives_eight_fields'
        model=archive('model_file',('coordinates','connectivity','solid','workpiece_cells'),metadata['arrays']['fields'])
        state=archive('state_file',('lift','fluctuation'),selected['state']['fields'])
        forces=archive('forces_file',('J','Hu'),selected['forces']['fields'])
        coords,conn,solid,body=(model[key] for key in ('coordinates','connectivity','solid','workpiece_cells'))
        J,Hu=forces['J'],forces['Hu']
        assert coords.shape==(13689,2) and conn.shape==(13440,4) and solid.dtype==np.dtype('bool')
        assert J.shape==(len(conn),9) and Hu.shape==(len(conn),2,2,2)
        medium=~solid.copy()
        medium[body]=False
        cells=np.flatnonzero(medium)
        xy=coords+state['lift'].reshape(-1,2)+state['fluctuation'].reshape(-1,2)
        gp_reference=np.einsum('qa,eac->eqc',N,coords[conn])
        gp_actual=np.einsum('qa,eac->eqc',N,xy[conn])
        centers_reference=coords[conn].mean(axis=1)
        centers_actual=xy[conn].mean(axis=1)
        scores=np.abs(Hu).max(axis=(1,2,3))
        minimum=float(J[medium].min())
        maximum=float(scores[medium].max())
        assert minimum==derived['row']['medium_min_J']
        assert maximum==derived['row']['medium_max_abs_Hu_per_mm']
        assert float(J.min())==selected['minimum_J']
        assert float(np.abs(Hu).max())==selected['max_abs_Hu_per_mm']
        phase='exact_extrema_and_ranked_locations'
        j_threshold=float(np.sort(J[medium].ravel())[9])
        hu_threshold=float(np.sort(scores[medium])[-10])
        low_e,low_q=np.where(J[medium]<=j_threshold)
        low=[(int(cells[e]),int(q)) for e,q in zip(low_e,low_q)]
        low.sort(key=lambda item:(float(J[item]),item[0],item[1]))
        high=[int(e) for e in cells[scores[medium]>=hu_threshold]]
        high.sort(key=lambda e:(-float(scores[e]),e))
        nearest=geometry['boundary']['groups']['all_exposed']
        closest=nearest['closest_pair']
        mechanism_nodes=set(closest['mechanism_nodes'])
        workpiece_nodes=set(closest['workpiece_nodes'])
        tip_node=derived['row']['tip_node']
        mechanism_cells=set(np.flatnonzero((conn==closest['mechanism_nodes'][0]).any(axis=1)&(conn==closest['mechanism_nodes'][1]).any(axis=1)).tolist())
        workpiece_cells=set(np.flatnonzero((conn==closest['workpiece_nodes'][0]).any(axis=1)&(conn==closest['workpiece_nodes'][1]).any(axis=1)).tolist())

        def relation(e):
            nodes=set(map(int,conn[e]))
            return dict(same_cell_as_nearest_mechanism_edge=e in mechanism_cells,
                same_cell_as_nearest_workpiece_edge=e in workpiece_cells,
                shared_nodes_with_nearest_mechanism_edge=len(nodes&mechanism_nodes),
                shared_nodes_with_nearest_workpiece_edge=len(nodes&workpiece_nodes),tip_incident=tip_node in nodes)

        j_rows=[]
        for e,q in low:
            j_rows.append(dict(element_id=e,simpson_point_index=q,xi=float(POINTS[q,0]),eta=float(POINTS[q,1]),
                J=float(J[e,q]),global_minimum_tie=bool(J[e,q]==minimum),
                reference_position_mm=gp_reference[e,q].tolist(),actual_position_mm=gp_actual[e,q].tolist(),
                relation=relation(e)))
        hu_rows=[]
        hu_components=[]
        for e in high:
            ties=[dict(component_index=list(map(int,index)),signed_value_per_mm=float(Hu[(e,*index)]))
                for index in zip(*np.where(np.abs(Hu[e])==scores[e]))]
            hu_rows.append(dict(element_id=e,max_abs_component_per_mm=float(scores[e]),global_maximum_tie=bool(scores[e]==maximum),
                reference_center_marker_mm=centers_reference[e].tolist(),actual_center_marker_mm=centers_actual[e].tolist(),
                component_ties=ties,relation=relation(e)))
            for tie in ties:
                hu_components.append(dict(element_id=e,Hu_max_abs_per_mm=float(scores[e]),
                    global_maximum_tie=bool(scores[e]==maximum),i=tie['component_index'][0],J_index=tie['component_index'][1],
                    K_index=tie['component_index'][2],signed_Hu_per_mm=tie['signed_value_per_mm'],
                    reference_center_x_mm=float(centers_reference[e,0]),reference_center_y_mm=float(centers_reference[e,1]),
                    actual_center_x_mm=float(centers_actual[e,0]),actual_center_y_mm=float(centers_actual[e,1])))
        j_csv=[]
        for row in j_rows:
            j_csv.append(dict(element_id=row['element_id'],simpson_point_index=row['simpson_point_index'],xi=row['xi'],eta=row['eta'],
                J=row['J'],global_minimum_tie=row['global_minimum_tie'],reference_x_mm=row['reference_position_mm'][0],
                reference_y_mm=row['reference_position_mm'][1],actual_x_mm=row['actual_position_mm'][0],actual_y_mm=row['actual_position_mm'][1]))
        for filename,rows in (('j_locations.csv',j_csv),('hu_locations.csv',hu_components)):
            with (run/filename).open('x',encoding='utf-8',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
        summary=dict(card=CARD,status='observed_saved_fields',selected_accepted_index=1,original_target_index=7,
            state_sha256=STATE,d_mm=1.35,source_files={key:protocol[key] for key in
                ('model_file','state_file','forces_file','geometry_observation_file','derived_observation_file')},
            decoded_archives=3,decoded_fields=8,free_medium_cells=len(cells),free_medium_Simpson_samples=len(cells)*9,
            mask_definition='~solid, then workpiece_cells=False; includes medium adjacent to fixed boundaries',
            point_order=POINTS.tolist(),point_order_definition='Original nine-point tensor Simpson; xi slow, eta fast; BL BR TR TL Q1 basis',
            point_order_descriptor_sha256=point_info['sha256'],point_order_descriptor_match=True,model_points_decoded=False,
            J_minimum=minimum,J_minimum_ties=[row for row in j_rows if row['global_minimum_tie']],
            J_top10_threshold=j_threshold,J_top10_with_cutoff_ties=j_rows,J_top10_sample_count=len(j_rows),
            Hu_max_abs_component_per_mm=maximum,Hu_maximum_ties=[row for row in hu_rows if row['global_maximum_tie']],
            Hu_top10_threshold_per_mm=hu_threshold,Hu_top10_cells_with_cutoff_ties=hu_rows,
            Hu_top10_cell_count=len(hu_rows),Hu_component_csv_rows=len(hu_components),
            Hu_definition='Saved Hu[i,J,K] is Q1 reference-Hessian cellwise constant; score=max abs of eight components, not Frobenius norm; all exact maximizing component ties retained; centers are representative markers, not unique extrema points',
            source_scalar_exact_matches=dict(free_medium_minJ=True,free_medium_max_abs_Hu=True,global_minJ=True,global_max_abs_Hu=True),
            nearest_saved_observation=nearest,tip_saved_observation=derived['tip_surface_witness'],
            tip_actual_position_mm=[derived['row']['tip_x_mm'],derived['row']['tip_y_mm']],
            nearest_incident_cells=dict(mechanism_edge=sorted(mechanism_cells),workpiece_edge=sorted(workpiece_cells)),
            relation_scope='Only saved witness coordinates and connectivity incidence/shared-node relations; no new boundary search',
            local_bounds_mm=protocol['local_bounds_mm'],coordinate_scope='Actual lower half at scale one; Q1 interpolate saved coordinates+lift+fluctuation; display only',
            qualification='Saved-field localization only; no new mechanics/HP/contact/pressure/effective grip/stability qualification')
        write(run/'summary.json',summary)
        checkpoint()
        phase='two_location_figures'
        for filename,bounds,title in (('overview.png',None,'Saved free-medium extrema: entire lower-half model'),
                ('local.png',protocol['local_bounds_mm'],'Saved free-medium extrema: workpiece and beam detail')):
            calls['plots_started']+=1
            checkpoint()
            fig,ax=plt.subplots(figsize=(12,6.5))
            field=PolyCollection(xy[conn[medium]],array=J[medium].mean(axis=1),cmap='viridis',edgecolors='none')
            ax.add_collection(field)
            ax.add_collection(PolyCollection(xy[conn[solid]],facecolors='#65686b',edgecolors='none'))
            ax.add_collection(PolyCollection(xy[conn[body]],facecolors='#ddccb0',edgecolors='#baaa90',linewidths=.15))
            ax.add_collection(PolyCollection(xy[conn[np.unique([e for e,q in low])]],facecolors='none',edgecolors='#df3b36',linewidths=.8))
            ax.add_collection(PolyCollection(xy[conn[high]],facecolors='none',edgecolors='#e359ce',linewidths=1.0))
            jp=np.array([row['actual_position_mm'] for row in j_rows])
            hp=centers_actual[high]
            ax.scatter(jp[:,0],jp[:,1],marker='v',s=27,color='#e73532',edgecolors='white',linewidths=.3,
                label=f"J lowest10 + cutoff ties ({len(j_rows)} Simpson samples); minimum={minimum:.6g}",zorder=5)
            ax.scatter(hp[:,0],hp[:,1],marker='x',s=35,color='#f565d5',linewidths=1.2,
                label=f"Hu highest10 + cutoff ties ({len(high)} cells); max abs component={maximum:.6g} /mm",zorder=6)
            exact_j=np.array([row['actual_position_mm'] for row in j_rows if row['global_minimum_tie']])
            exact_hu=centers_actual[[e for e in high if scores[e]==maximum]]
            ax.scatter(exact_j[:,0],exact_j[:,1],marker='*',s=65,color='#d92120',edgecolors='white',linewidths=.4,
                label=f'Exact minimum J: {len(exact_j)} sample ties',zorder=8)
            ax.scatter(exact_hu[:,0],exact_hu[:,1],marker='D',s=35,color='#ec35c9',edgecolors='white',linewidths=.4,
                label=f'Exact maximum Hu: {len(exact_hu)} cell ties, representative centers',zorder=8)
            pair=np.array([closest['mechanism_point_mm'],closest['workpiece_point_mm']])
            ax.plot(pair[:,0],pair[:,1],'-o',color='#00c6d8',lw=1.8,ms=4,
                label=f"Saved nearest edge witness: {nearest['minimum_boundary_distance_mm']:.6g} mm",zorder=7)
            tip=np.array(summary['tip_actual_position_mm'])
            tip_pair=np.array([tip,derived['tip_surface_witness']['point_mm']])
            ax.plot(tip_pair[:,0],tip_pair[:,1],'--o',color='#ef951d',lw=1.2,ms=4,
                label=f"Saved tip witness: {derived['tip_surface_witness']['distance_mm']:.6g} mm",zorder=7)
            ax.scatter(*tip,marker='*',s=75,color='#ef951d',zorder=8)
            ax.autoscale(); ax.set_aspect('equal')
            if bounds is not None:
                ax.set_xlim(bounds[:2]); ax.set_ylim(bounds[2:])
            ax.set(xlabel='Actual x (mm), scale 1',ylabel='Actual y (mm), scale 1',title=title)
            fig.colorbar(field,ax=ax,fraction=.032,pad=.02,label='Cell mean J background; not the sampled minimum J')
            fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.035),ncol=2,fontsize=7)
            fig.text(.5,.015,'Hu is constant per Q1 cell: x denotes a center marker. Exact ties retain element/sample identities. No contact or pressure qualification.',ha='center',fontsize=8)
            fig.tight_layout(rect=(0,.16,1,1))
            fig.savefig(run/filename,dpi=150)
            plt.close(fig)
            calls['plots_completed']+=1
            checkpoint()
        phase='review_and_final_bindings'
        (run/'REVIEW.md').write_text('\n'.join([
            '# L-CLOCAL1：圆形1.35 mm保存场空间定位','',
            f'accepted1/global7，state SHA `{STATE}`。仅读三NPZ的八个原字段，不重做F/T、HP、求解或边界搜索。','',
            f'自由第三介质{len(cells)}单元／{len(cells)*9}个原九点Simpson样本。最小J={minimum!r}；最大Hu绝对分量={maximum!r} /mm。原保存标量均精确一致。','',
            f'J保留最低十个样本及边界exact ties，共{len(j_rows)}行。Hu按单元max(abs8components)保留最高十单元及边界exact ties，共{len(hu_rows)}单元、{len(hu_components)}个最大分量并列行。','',
            'J九点按xi慢、eta快的(-1,0,1)原Simpson顺序。Hu无九点轴，Q1参考Hessian在单元内常值；中心只作代表标记，不是唯一极值空间点，也不是Frobenius范数。跨单元重合采样点保留原身份。','',
            '颜色底图是单元meanJ，红三角是独立的低J采样位置，粉色叉是Hu高值单元中心；轮廓显示相关单元。最近边界与尖端两类见证来自原普通JSON，未经新搜索，不能混作一条间隙或接触证明。','',
            '[原值与精确并列JSON](summary.json) · [低J位置CSV](j_locations.csv) · [Hu单元及最大分量并列CSV](hu_locations.csv)','',
            '![整体实际位置](overview.png)','', '![工件梁段局部](local.png)','',
            '保持半径9 mm、中心(71,40) mm及原物理任务和资格；本步骤只有保存场定位，无新压力、有效夹持或稳定性资格。','']),encoding='utf-8',newline='\n')
        for name,pin in all_bindings.items():
            path=ROOT/name
            if path.suffix.lower()=='.npz':
                assert path.stat().st_size==sizes[name]
            else:
                assert digest(path)==pin,name
        assert receipt['archives_decoded']==3 and receipt['fields_decoded']==8 and calls['plots_completed']==2
        phase='final_output_seal'
        outputs=seal(); seal_status='complete_inside_original_helper_window'
        receipt['status']='pass'
    except BaseException as error:
        receipt.update(status='not_pass',error=dict(phase=phase,exception_class=type(error).__name__,reason=str(error)))
        if not stop.exists() and perf_counter()-STARTED<=protocol['helper_seconds'] and process.memory_info().rss<=protocol['sampled_RSS_bytes']:
            try:
                outputs=seal(); seal_status='actual_partial_inside_original_helper_window'
            except BaseException:
                seal_status='not_complete_before_resource_close'
    receipt.update(phase=phase,outputs=outputs,output_identity_seal=seal_status,
        call_counts=calls,elapsed_seconds=perf_counter()-STARTED,sampled_peak_RSS_bytes=peak,
        helper_seconds=protocol['helper_seconds'],sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        mechanical_hooks_monitored=False,forced_GC_calls=0,external_retries=0,
        input_identity_scope='One initial raw SHA per bound input, exactly eight decoded fields checked against descriptors; final NPZ stat only, ordinary bindings rehashed',
        completed_utc=datetime.now(timezone.utc).isoformat())
    write(receipt_file,receipt)
    print(json.dumps(dict(status=receipt['status'],phase=phase,archives_decoded=receipt['archives_decoded'],fields_decoded=receipt['fields_decoded'],error=receipt.get('error'))),flush=True)
    if receipt['status']!='pass':
        raise RuntimeError('L-CLOCAL1 closed not_pass; no retry or following phase')


if __name__=='__main__':
    main()
