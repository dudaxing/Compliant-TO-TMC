"""Compare six pinned ordinary peak JSONs; no mechanics or old media payloads."""
from time import monotonic
STARTED = monotonic()
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import fsum, hypot, isfinite
from pathlib import Path
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
RUN = STAGE/'run_001'
CARD = 'L-CTIPAFORCE1'
PARTS = ('total','material','regularization')
GROUPS = ('physical_only','cut_only','physical_and_cut','interior')
KINDS = ('nodal','derived','geometry')
SCOPE = ('Two existing loading peaks at1.06 mm, alpha5e-7 and2.5e-7: fixed lower-half workpiece '
    'global nodal weak ON-body forces in N at actual fixed-body coordinates in mm. Preserve all565 nodes '
    'per source, all original nodal/derived/geometry objects,37 row observations, group/whole resultants, '
    'moments and total holding reaction. Match exact global node IDs, coordinates, masks and edges; '
    'no renumbering, reclassification, small-force filtering, clipping, mirror doubling or new moment integration. '
    'Node/group/whole new-minus-baseline differences and fsum/decomposition tail differences are descriptive '
    'only, without tolerance or equality gates. ON-body is negative saved internal weak force; saved total '
    'holding opposes total ON-body, while material/Hu sign reversals are bookkeeping rather than independent '
    'reaction measurements. The shared maximum norm is arrow display scaling only. No pressure, continuous '
    'face traction, radial projection, effective grip, free-body response or qualification upgrade. '
    'No new science/F/T/HP/equilibrium/tests/API/default changes or old media content/stat reads. '
    'The six ordinary JSONs cannot reconstruct the complete deformed mechanism; original manual pages link it.')


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',
                    encoding='utf-8',newline='\n')


def check():
    assert monotonic()-STARTED < 180, 'Original helper deadline reached'
    assert psutil.Process().memory_info().rss <= 1024**3, 'Original helper RSS limit reached'


def identical(a,b):
    if isinstance(a,float) or isinstance(b,float):
        return isinstance(a,(int,float)) and isinstance(b,(int,float)) and float(a).hex()==float(b).hex()
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(identical(a[key],b[key]) for key in a)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(identical(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b


def vector_sum(forces, indices):
    return [fsum(forces[i][component] for i in indices) for component in (0,1)]


def vector_comparison(baseline,new):
    return dict(baseline_value=baseline,new_value=new,
                new_minus_baseline=[new[c]-baseline[c] for c in (0,1)])


def observe(case,manual,documents,contract):
    paths = {kind:case['folder']+'/'+kind+'.json' for kind in KINDS}
    nodal,derived,geometry = [documents[paths[kind]] for kind in KINDS]
    row = derived['row']
    assert (row['index'],row['original_target_index'],row['d_mm'],row['state_sha256'],row['leg']) == (
        case['accepted_index'],case['global_index'],case['d_mm'],case['state_sha256'],'loading'), 'Selected source state identity mismatch'
    ids,xy = nodal['node_ids'],nodal['coordinates_mm']
    masks,forces = nodal['masks'],nodal['forces_on_body_N']
    n = len(ids)
    assert n == contract['node_count_per_source'] == 565
    assert len(set(ids))==n and len(xy)==n
    assert tuple(masks)==GROUPS and tuple(forces)==PARTS
    assert all(len(masks[group])==n and all(type(value) is bool for value in masks[group]) for group in GROUPS)
    assert all(len(forces[part])==n for part in PARTS)
    assert all(len(vector)==2 and all(isfinite(value) for value in vector) for vector in xy)
    assert all(len(vector)==2 and all(isfinite(value) for value in vector) for part in PARTS for vector in forces[part])
    group_counts = {group:sum(masks[group]) for group in GROUPS}
    assert group_counts == contract['mask_partition_counts']
    for group in GROUPS:
        assert group_counts[group]==nodal['summary']['groups'][group]['node_count']
    for part in PARTS:
        assert nodal['summary']['force_on_lower_body_N'][part]==[row[part+'_body_Fx_N'],row[part+'_body_Fy_N']]
    assert geometry['boundary']['groups']['all_exposed']['minimum_boundary_distance_mm']==row['minimum_boundary_distance_mm']
    assert derived['tip_surface_witness']['distance_mm']==row['tip_to_raster_boundary_mm']
    idset = set(ids)
    assert all(len(edge)==2 and set(edge)<=idset for edges in nodal['edges'].values() for edge in edges)
    memberships = [sum(masks[group][i] for group in GROUPS) for i in range(n)]
    return dict(alpha=case['alpha'],label=f"alpha={case['alpha']:g}",selected_state=case,state=row,
        paths=paths,manual_path=manual['path'],manual_bytes=manual['bytes'],
        original=dict(nodal=nodal,derived=derived,geometry=geometry),raw_indices=[],
        counts=dict(node_count=n,group_counts=group_counts,
            mask_membership_counts={str(k):memberships.count(k) for k in sorted(set(memberships))},
            mask_partition_observed=all(k==1 for k in memberships)))


def descriptive(source):
    nodal = source['original']['nodal']
    ids,masks,forces = nodal['node_ids'],nodal['masks'],nodal['forces_on_body_N']
    summary = nodal['summary']
    whole = {part:vector_sum(forces[part],range(len(ids))) for part in PARTS}
    groups = {group:{part:vector_sum(forces[part],[i for i in range(len(ids)) if masks[group][i]])
                    for part in PARTS} for group in GROUPS}
    return dict(node_force_fsum_N=whole,
        node_force_fsum_minus_original_N={part:[whole[part][c]-summary['force_on_lower_body_N'][part][c] for c in (0,1)] for part in PARTS},
        mask_group_fsum_N=groups,
        mask_group_fsum_minus_original_N={group:{part:[groups[group][part][c]-summary['groups'][group]['force_on_body_N'][part][c]
                for c in (0,1)] for part in PARTS} for group in GROUPS},
        nodal_decomposition_max_abs_difference_N=max(abs(forces['total'][i][c]-(forces['material'][i][c]+forces['regularization'][i][c]))
            for i in range(len(ids)) for c in (0,1)),
        original_holding_plus_on_body_total_N=[summary['holding_reaction_on_model_N'][c]+summary['force_on_lower_body_N']['total'][c] for c in (0,1)],
        scope='Only approved ordinary fsum and decomposition observations; no tolerance, clipping, force extrema or positive/negative-sum metrics.')


def compare(protocol,documents):
    cases = protocol['cases']
    assert [case['name'] for case in cases]==['baseline','new']
    assert [case['alpha'] for case in cases]==[5e-7,2.5e-7]
    assert len(protocol['existing_manuals'])==2
    sources = {case['name']:observe(case,manual,documents,protocol['fixed_input_contract'])
               for case,manual in zip(cases,protocol['existing_manuals'])}
    old,new = [sources[name]['original']['nodal'] for name in ('baseline','new')]
    compatibility = {field:identical(old[field],new[field]) for field in ('node_ids','coordinates_mm','masks','edges','moment_origin_mm')}
    compatible = all(compatibility.values())
    data = dict(card=CARD,schema_version='lf-circle-tip-cross-alpha-node-force-1.0',
        status='pass' if compatible else 'incomparable',scope=SCOPE,sources=sources,
        compatibility=dict(comparable=compatible,exact_fields=compatibility,
            rule='Use exact original global IDs/fixed coordinates/masks/edges and moment origin; mismatch stops without renumbering or reclassification.'),
        raw_values=[],node_pairs=[],group_pairs=[],whole_resultant_comparison={},
        provenance=dict(ordinary_JSON_bindings=protocol['ordinary_JSON_bindings'],
            definition_source_bindings=protocol['definition_source_bindings'],
            fixed_coordinate_source_contract='Inherited source-bound producers require all workpiece lift/fluctuation DOFs exactly zero before observation; no arrays reopened here.'),
        qualification=dict(new_scientific_calls=0,new_reference_pass=False,full_path_reference_pass=False,
            pressure_qualified=False,effective_grip_qualified=False,release_qualified=False,stability_qualified=False,
            alpha_independence_qualified=False,HF5_qualified=False))
    if not compatible:
        return data
    maps = {}
    points = []
    maximum = 0.
    for name in ('baseline','new'):
        source = sources[name]
        nodal,derived,geometry = [source['original'][kind] for kind in KINDS]
        source['descriptive'] = descriptive(source)
        maps[name] = {}
        for i,node in enumerate(nodal['node_ids']):
            index = len(data['raw_values'])
            source['raw_indices'].append(index)
            maps[name][node] = index
            data['raw_values'].append(dict(source=name,node_id=node,coordinates_mm=nodal['coordinates_mm'][i],
                masks={group:nodal['masks'][group][i] for group in GROUPS},
                on_body_N={part:nodal['forces_on_body_N'][part][i] for part in PARTS}))
            maximum = max(maximum,*(hypot(*nodal['forces_on_body_N'][part][i]) for part in PARTS))
        closest = geometry['boundary']['groups']['all_exposed']['closest_pair']
        points.extend(nodal['coordinates_mm'])
        points.extend([[source['state']['tip_x_mm'],source['state']['tip_y_mm']],
            derived['tip_surface_witness']['point_mm'],closest['mechanism_point_mm'],closest['workpiece_point_mm']])
        check()
    for node,baseline_index in maps['baseline'].items():
        new_index = maps['new'][node]
        old_row,new_row = [data['raw_values'][i] for i in (baseline_index,new_index)]
        data['node_pairs'].append(dict(node_id=node,coordinates_mm=old_row['coordinates_mm'],masks=old_row['masks'],
            baseline_raw_index=baseline_index,new_raw_index=new_index,
            on_body_N={part:vector_comparison(old_row['on_body_N'][part],new_row['on_body_N'][part]) for part in PARTS}))
    for group in GROUPS:
        old_group,new_group = [sources[name]['original']['nodal']['summary']['groups'][group] for name in ('baseline','new')]
        data['group_pairs'].append(dict(group=group,baseline=old_group,new=new_group,
            force_on_body_N={part:vector_comparison(old_group['force_on_body_N'][part],new_group['force_on_body_N'][part]) for part in PARTS}))
    data['whole_resultant_comparison'] = dict(force_on_lower_body_N={part:vector_comparison(
        old['summary']['force_on_lower_body_N'][part],new['summary']['force_on_lower_body_N'][part]) for part in PARTS})
    data['counts'] = dict(sources=len(sources),node_raw_rows=len(data['raw_values']),matched_node_pairs=len(data['node_pairs']),
        descriptive_node_differences=len(data['node_pairs'])*len(PARTS)*2,mask_group_original_rows=len(GROUPS)*len(sources),
        mask_group_matched_pairs=len(data['group_pairs']),mask_group_component_differences=len(data['group_pairs'])*len(PARTS)*2,
        whole_resultant_component_differences=len(PARTS)*2)
    margin = 2.6
    data['display'] = dict(arrow_mm_per_N=2./maximum if maximum else 1.,max_vector_norm_N=maximum,
        maximum_arrow_length_mm=2.,bounds_mm=dict(x=[min(p[0] for p in points)-margin,max(p[0] for p in points)+margin],
            y=[min(p[1] for p in points)-margin,max(p[1] for p in points)+margin]),
        scope='One common arrow conversion across both alpha values and all three parts; display norm/limits are not new force or physics acceptance metrics.')
    return data


def main():
    assert not RUN.exists(), 'One invocation only; preserve prior output'
    RUN.mkdir()
    raw = (STAGE/'protocol.json').read_bytes()
    protocol = json.loads(raw)
    receipt = dict(card=CARD,status='running',protocol_sha256=sha256(raw).hexdigest(),default_installations=0,
        new_tests=0,HP_calls_by_wrapper=0,new_force_calls=0,new_tangent_calls=0,new_equilibrium_solves=0,
        new_API_associations=0,scientific_payload_reads=0,old_media_content_reads=0,old_media_stat_count=0,
        old_GIF_stat_count=0,old_manual_stat_count=0,ordinary_JSON_reads=0,outputs={},
        started_utc=datetime.now(timezone.utc).isoformat())
    phase,error = 'six_bound_ordinary_inputs',None
    try:
        expected_paths = {case['folder']+'/'+kind+'.json' for case in protocol['cases'] for kind in KINDS}
        assert len(expected_paths)==len(protocol['ordinary_JSON_bindings'])==6
        assert expected_paths==set(protocol['ordinary_JSON_bindings'])
        documents = {}
        for name,pin in protocol['ordinary_JSON_bindings'].items():
            check();raw=(ROOT/name).read_bytes()
            assert len(raw)==pin['bytes'] and sha256(raw).hexdigest()==pin['sha256'],name
            documents[name]=json.loads(raw);receipt['ordinary_JSON_reads']+=1
        assert len(protocol['existing_manuals'])==2
        for manual in protocol['existing_manuals']:
            assert (ROOT/manual['path']).stat().st_size==manual['bytes']
            receipt['old_manual_stat_count']+=1
        phase = 'original_source_checks_and_descriptive_comparison'
        data = compare(protocol,documents);check()
        write(RUN/'comparison.json',data)
        if data['status']!='pass':
            raise ValueError('Node IDs/fixed coordinates/masks/edges/origin incompatible; see comparison.json; no reclassification or plot')
        receipt['counts'] = data['counts']
        phase = 'two_force_views'
        from force_views import render
        render(data,RUN,ROOT)
        check();receipt['status']='pass'
    except BaseException as exc:
        error=exc;receipt.update(status='not_pass',error=dict(type=type(exc).__name__,message=str(exc)))
    receipt['phase'] = phase
    if monotonic()-STARTED < 180:
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
    print(json.dumps({key:receipt[key] for key in ('card','status','phase','elapsed_seconds','ordinary_JSON_reads','old_manual_stat_count')},ensure_ascii=False),flush=True)
    if error is not None:raise error
    assert receipt['status']=='pass'


if __name__=='__main__':main()
