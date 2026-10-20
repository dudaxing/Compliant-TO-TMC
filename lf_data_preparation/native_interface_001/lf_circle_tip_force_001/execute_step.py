"""Observe three pinned ordinary peak JSONs; no mechanics or scientific arrays."""
from time import monotonic
STARTED=monotonic()
from datetime import datetime,timezone
from hashlib import sha256
import json
from math import fsum,hypot,isfinite
from pathlib import Path
import psutil

STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parents[2]
RUN=STAGE/'run_001'
CARD='L-CTIPFORCE1'
PARTS=('total','material','regularization')
GROUPS=('physical_only','cut_only','physical_and_cut','interior')
SCOPE=('Existing peak fixed lower-half workpiece node weak forces in N, at fixed body coordinates in mm. '
       'ON-body vectors are the original negative internal weak force. The original total holding reaction '
       'opposes ON-body total; component-wise holding glyphs are algebraic negatives for display, not '
       'independent reaction measurements. No pressure, continuous face traction, radial pressure projection, '
       'mirror doubling or qualified effective grip. Raw node/mask/group values retained. New sums/differences '
       'are descriptive only, without a tolerance or acceptance gate. No new F/T/HP/equilibrium/tests/default '
       'or API association. These three JSONs do not contain full deformed gripper coordinates.')

def write(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')

def check():
    assert monotonic()-STARTED<180,'Original helper deadline reached'
    assert psutil.Process().memory_info().rss<=1024**3,'Original helper RSS limit reached'

def vector_sum(forces,indices):
    return [fsum(forces[i][c] for i in indices) for c in (0,1)]

def observe(protocol,documents):
    nodal,derived,geometry=[documents[protocol['paths'][key]] for key in ('nodal','derived','geometry')]
    row=derived['row'];selected=protocol['selected_state']
    assert (row['index'],row['original_target_index'],row['d_mm'],row['state_sha256'],row['leg'])==(
        selected['accepted_index'],selected['original_target_index'],selected['d_mm'],selected['state_sha256'],'loading')
    ids,xy=nodal['node_ids'],nodal['coordinates_mm']
    masks,forces=nodal['masks'],nodal['forces_on_body_N']
    n=len(ids)
    assert len(set(ids))==n and len(xy)==n
    assert tuple(masks)==GROUPS and tuple(forces)==PARTS
    assert all(len(masks[g])==n and all(type(v) is bool for v in masks[g]) for g in GROUPS)
    assert all(len(forces[p])==n for p in PARTS)
    assert all(len(v)==2 and all(isfinite(a) for a in v) for v in xy)
    assert all(len(v)==2 and all(isfinite(a) for a in v) for p in PARTS for v in forces[p])
    for group in GROUPS:
        assert sum(masks[group])==nodal['summary']['groups'][group]['node_count']
    for part,prefix in [('total','total'),('material','material'),('regularization','regularization')]:
        assert nodal['summary']['force_on_lower_body_N'][part]==[row[prefix+'_body_Fx_N'],row[prefix+'_body_Fy_N']]
    assert geometry['boundary']['groups']['all_exposed']['minimum_boundary_distance_mm']==row['minimum_boundary_distance_mm']
    assert derived['tip_surface_witness']['distance_mm']==row['tip_to_raster_boundary_mm']
    idset=set(ids)
    assert all(len(edge)==2 and set(edge)<=idset for edges in nodal['edges'].values() for edge in edges)
    node_rows=[dict(node_id=node,coordinates_mm=xy[i],masks={g:masks[g][i] for g in GROUPS},
        on_body_N={p:forces[p][i] for p in PARTS},holding_N={p:[-v for v in forces[p][i]] for p in PARTS})
        for i,node in enumerate(ids)]
    membership=[sum(masks[g][i] for g in GROUPS) for i in range(n)]
    group_counts={g:sum(masks[g]) for g in GROUPS}
    all_sums={p:vector_sum(forces[p],range(n)) for p in PARTS}
    group_sums={g:{p:vector_sum(forces[p],[i for i in range(n) if masks[g][i]]) for p in PARTS} for g in GROUPS}
    extrema={}
    for part in PARTS:
        values=forces[part]
        norms=[hypot(*v) for v in values]
        maximum=max(norms);witness=norms.index(maximum)
        extrema[part]=dict(max_norm_N=maximum,max_norm_node_id=ids[witness],max_norm_coordinates_mm=xy[witness],
            max_norm_vector_N=values[witness],max_norm_exact_tie_count=sum(v==maximum for v in norms),
            component_min_N=[min(v[c] for v in values) for c in (0,1)],
            component_max_N=[max(v[c] for v in values) for c in (0,1)],
            exact_zero_vectors=sum(v[0]==0. and v[1]==0. for v in values),
            positive_component_sum_N=[fsum(v[c] for v in values if v[c]>0) for c in (0,1)],
            negative_component_sum_N=[fsum(v[c] for v in values if v[c]<0) for c in (0,1)])
    descriptive=dict(node_force_fsum_N=all_sums,
        node_force_fsum_minus_original_N={p:[all_sums[p][c]-nodal['summary']['force_on_lower_body_N'][p][c] for c in (0,1)] for p in PARTS},
        mask_group_fsum_N=group_sums,
        mask_group_fsum_minus_original_N={g:{p:[group_sums[g][p][c]-nodal['summary']['groups'][g]['force_on_body_N'][p][c] for c in (0,1)] for p in PARTS} for g in GROUPS},
        nodal_decomposition_max_abs_difference_N=max(abs(forces['total'][i][c]-(forces['material'][i][c]+forces['regularization'][i][c])) for i in range(n) for c in (0,1)),
        original_holding_plus_on_body_total_N=[nodal['summary']['holding_reaction_on_model_N'][c]+nodal['summary']['force_on_lower_body_N']['total'][c] for c in (0,1)],
        extrema=extrema,
        scope='New ordinary arithmetic observations only. Signed positive/negative sums and differences retained; no clipping or numerical acceptance tolerance.')
    return dict(card=CARD,status='pass',schema_version='lf-circle-tip-peak-node-observation-1.0',
        state=row,nodal=nodal,derived=derived,geometry=geometry,node_rows=node_rows,
        original_summary=nodal['summary'],groups=nodal['summary']['groups'],descriptive=descriptive,
        counts=dict(node_count=n,group_counts=group_counts,
            mask_membership_counts={str(k):membership.count(k) for k in sorted(set(membership))},
            mask_partition_observed=all(k==1 for k in membership)),
        selected_state=selected,provenance=dict(paths=protocol['paths'],ordinary_JSON_bindings=protocol['ordinary_JSON_bindings'],
            fixed_coordinate_source_contract=protocol['fixed_coordinate_source_contract']),
        existing_GIF=protocol['existing_GIF'],existing_manual=protocol['existing_manual'],scope=SCOPE,
        qualification=dict(new_scientific_calls=0,new_reference_pass=False,full_path_reference_pass=False,
            pressure_qualified=False,effective_grip_qualified=False,release_qualified=False,stability_qualified=False,HF5_qualified=False))

def main():
    assert not RUN.exists(),'One invocation only; preserve previous output'
    RUN.mkdir()
    raw=(STAGE/'protocol.json').read_bytes();protocol=json.loads(raw)
    receipt=dict(card=CARD,status='running',protocol_sha256=sha256(raw).hexdigest(),default_installations=0,
        new_tests=0,HP_calls_by_wrapper=0,new_force_calls=0,new_tangent_calls=0,new_equilibrium_solves=0,
        new_API_associations=0,scientific_payload_reads=0,old_media_content_reads=0,old_GIF_stat_count=0,
        ordinary_JSON_reads=0,outputs={},started_utc=datetime.now(timezone.utc).isoformat())
    phase='three_bound_ordinary_inputs';error=None
    try:
        assert len(protocol['ordinary_JSON_bindings'])==3
        documents={}
        for name,pin in protocol['ordinary_JSON_bindings'].items():
            check();raw=(ROOT/name).read_bytes()
            assert len(raw)==pin['bytes'] and sha256(raw).hexdigest()==pin['sha256'],name
            documents[name]=json.loads(raw);receipt['ordinary_JSON_reads']+=1
        gif=protocol['existing_GIF']
        assert (ROOT/gif['path']).stat().st_size==gif['bytes']
        receipt['old_GIF_stat_count']=1
        phase='original_nodes_and_descriptive_arithmetic'
        data=observe(protocol,documents);check()
        write(RUN/'force_response.json',data)
        write(RUN/'nodes.json',dict(card=CARD,state=data['state'],rows=data['node_rows'],scope=SCOPE))
        write(RUN/'groups.json',dict(card=CARD,original_summary=data['original_summary'],counts=data['counts'],
            descriptive=data['descriptive'],scope=SCOPE))
        receipt['counts']=data['counts']
        phase='two_force_views'
        from force_views import render
        render(data,RUN,ROOT)
        check();receipt['status']='pass'
    except BaseException as exc:
        error=exc;receipt.update(status='not_pass',error=dict(type=type(exc).__name__,message=str(exc)))
    receipt['phase']=phase
    if monotonic()-STARTED<180:
        for path in sorted(RUN.iterdir()):
            if path.is_file():
                check();raw=path.read_bytes()
                receipt['outputs'][path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
        receipt['output_identity_seal']='complete_inside_original_helper_window'
    else:
        receipt.update(status='not_pass',output_identity_seal='original_window_expired_no_new_seal')
    receipt.update(elapsed_seconds=monotonic()-STARTED,sampled_RSS_bytes=psutil.Process().memory_info().rss,
        external_retries=0,completed_utc=datetime.now(timezone.utc).isoformat())
    write(RUN/'execution_receipt.json',receipt)
    print(json.dumps({k:receipt[k] for k in ('card','status','phase','elapsed_seconds','ordinary_JSON_reads','old_GIF_stat_count')},ensure_ascii=False),flush=True)
    if error is not None:raise error
    assert receipt['status']=='pass'

if __name__=='__main__':main()
