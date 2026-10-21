"""Compare two pinned ordinary alpha paths; no mechanics or old media payloads."""
from time import monotonic
STARTED = monotonic()
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
CARD = 'L-CTIPACOMP1'
RUN = STAGE/'run_001'
METRICS = ('R_input_N','q_out_mm','total_body_Fx_N','total_body_Fy_N',
    'material_body_Fx_N','material_body_Fy_N','regularization_body_Fx_N','regularization_body_Fy_N',
    'tip_to_raster_boundary_mm','minimum_boundary_distance_mm','solid_min_J','medium_min_J',
    'medium_max_abs_Hu_per_mm')
NUMERIC_FIELDS = ('index','original_target_index','d_mm','R_input_N','q_out_mm','tip_node',
    'tip_x_mm','tip_y_mm','tip_to_raster_boundary_mm','tip_minus_global_minimum_mm',
    'minimum_boundary_distance_mm','solid_min_J','medium_min_J','solid_Green_principal_min',
    'solid_Green_principal_max','medium_max_abs_Hu_per_mm','right_medium_min_J','right_medium_max_J',
    'right_medium_max_abs_Hu_per_mm','right_medium_Green_principal_min','right_medium_Green_principal_max',
    'right_medium_max_nodal_displacement_mm','total_body_Fx_N','total_body_Fy_N','material_body_Fx_N',
    'material_body_Fy_N','regularization_body_Fx_N','regularization_body_Fy_N')
BOOL_FIELDS = ('tip_equals_global_minimum_exact','boundary_intersects','boundary_roundoff_near_touch',
    'raw_overlap','strict_overlap','roundoff_ambiguous','containment_tested')
SCOPE = ('Two existing ordinary paths only: alpha5e-7 from fourteen segments and alpha2.5e-7 from four. '
    'Compare original target identity, display branch and exact input d, never d or SHA alone. '
    'Retain forty original rows, all37 observations and everything already embedded in the two inputs: raw anchors/bisections, diagnostics, exceptions, segments and counts. No source_history or additional Newton-history file is opened. '
    'Thirteen original scalar definitions give260 descriptive new-minus-baseline differences only. '
    'No interpolation, normalization of incompatible tasks, new mechanics/HP/tests/API/default changes, '
    'equality/zero-return/recovery/energy/stability gate or qualification. Whole CPU/count differences are not pure-alpha performance. '
    'An identical zero-state SHA never merges physical tasks or transfers HP; signed lower-body weak force is not pressure or effective grip.')


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def check():
    assert monotonic()-STARTED < 180, 'Original helper deadline reached'
    rss = psutil.Process().memory_info().rss
    assert rss <= 1024**3, 'Original helper RSS limit reached'
    return rss


def identical(a,b):
    if isinstance(a,float) or isinstance(b,float):
        return isinstance(a,(float,int)) and isinstance(b,(float,int)) and float(a).hex()==float(b).hex()
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(identical(a[key],b[key]) for key in a)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(identical(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b


def differences(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        rows = []
        for key in sorted(a.keys()|b.keys()):
            name = path+'.'+key if path else key
            if key not in a or key not in b:
                rows.append(dict(path=name,baseline_present=key in a,new_present=key in b,
                    baseline_value=a.get(key),new_value=b.get(key)))
            else:
                rows.extend(differences(a[key],b[key],name))
        return rows
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        return [row for index,(old,new) in enumerate(zip(a,b))
                for row in differences(old,new,f'{path}[{index}]')]
    return [] if identical(a,b) else [dict(path=path,baseline_value=a,new_value=b)]


def row_key(row):
    # hex retains the original binary64 d, including signed zero; identity is not d alone.
    return (row['convergence']['original_target_index'],row['display_branch'],float(row['d_mm']).hex())


def compare(protocol,documents):
    assert tuple(protocol['same_input_metrics'])==METRICS
    assert set(protocol['comparison_sources'])=={'baseline','new'}
    sources = {}
    for name in ('baseline','new'):
        item = protocol['comparison_sources'][name]
        original = documents[item['path']]
        assert original['status']=='pass' and original['schema_version']=='lf-circle-tip-ordinary-path-1.0'
        assert original['card']==('L-CTIPPATH1' if name=='baseline' else 'L-CTIPAPATH1')
        for row in original['raw_rows']+original['timeline_rows']:
            assert all(key in row for key in protocol['summary_row_fields'])
            assert all(type(row[key]) in (int,float) and math.isfinite(row[key]) for key in NUMERIC_FIELDS)
            assert all(type(row[key]) is bool for key in BOOL_FIELDS)
            for a,b in (('state_sha256','state_sha256'),('d_mm','d'),('R_input_N','R_input'),
                        ('q_out_mm','q_out'),('original_target_index','original_target_index'),('leg','leg')):
                assert identical(row[a],row['convergence'][b]), (name,row['index'],a)
        pin = protocol['ordinary_JSON_bindings'][item['path']]
        alpha = original['original_task']['regularization']['alpha']
        sources[name] = dict(item,sha256=pin['sha256'],bytes=pin['bytes'],alpha=alpha,
            label=f'alpha={alpha:g} / {len(original["segments"])} source segments',original=original)
    old_task,new_task = (sources[name]['original']['original_task'] for name in ('baseline','new'))
    task_differences = differences(old_task,new_task)
    allowed_paths = {'regularization.alpha','task_id','purpose','parameter_origin','description'}
    unexpected = [row for row in task_differences if row['path'] not in allowed_paths]
    alpha_matches = identical(old_task['regularization']['alpha'],5e-7) and identical(new_task['regularization']['alpha'],2.5e-7)
    compatibility = dict(comparable=not unexpected and alpha_matches,
        allowed_differing_paths=sorted(allowed_paths),observed_task_differences=task_differences,
        unexpected_task_differences=unexpected,alpha_contract_matches=alpha_matches,
        rule='Every task field except alpha and four descriptive metadata fields must remain exact; original tasks are preserved, never normalized.')
    data = dict(card=CARD,schema_version='lf-circle-tip-cross-alpha-comparison-1.0',
        status='pass' if compatibility['comparable'] else 'incomparable',scope=SCOPE,
        compatibility=compatibility,sources=sources,metric_fields=list(METRICS),raw_values=[],pairs=[],
        qualification=dict(new_scientific_calls=0,new_reference_pass=False,full_path_reference_pass=False,
            pressure_qualified=False,effective_grip_qualified=False,release_qualified=False,stability_qualified=False,HF5_qualified=False))
    if not compatibility['comparable']:
        return data
    maps = {}
    for name in ('baseline','new'):
        original = sources[name]['original']
        originals = [row for row in original['timeline_rows']
            if row['convergence']['is_original_target'] and not row['unmerged_boundary_anchor']]
        assert [row['convergence']['original_target_index'] for row in originals]==list(range(20))
        assert [row['display_branch'] for row in originals]==['origin']+['loading']*12+['unloading']*7
        assert len(originals)==len(original['original_task']['path']['targets_mm'])==20
        assert all(identical(row['d_mm'],d) for row,d in zip(originals,original['original_task']['path']['targets_mm']))
        maps[name] = {}
        for row in originals:
            key = row_key(row)
            assert key not in maps[name], 'Duplicate original target identity'
            maps[name][key] = len(data['raw_values'])
            data['raw_values'].append(dict(source=name,
                key=dict(original_target_index=key[0],display_branch=key[1],d_mm=row['d_mm']),
                source_display_index=row['display_index'],row=row))
    assert maps['baseline'].keys()==maps['new'].keys(), 'Original target/branch/exact-input keys are not comparable'
    for key,baseline_index in maps['baseline'].items():
        new_index = maps['new'][key]
        old,new = (data['raw_values'][index]['row'] for index in (baseline_index,new_index))
        data['pairs'].append(dict(global_index=key[0],display_branch=key[1],d_mm=old['d_mm'],
            baseline_raw_index=baseline_index,new_raw_index=new_index,
            baseline_state_sha256=old['state_sha256'],new_state_sha256=new['state_sha256'],
            metrics={metric:dict(baseline_value=old[metric],new_value=new[metric],
                new_minus_baseline=new[metric]-old[metric]) for metric in METRICS}))
    data['counts'] = dict(sources=len(sources),baseline_original_targets=len(maps['baseline']),
        new_original_targets=len(maps['new']),raw_values=len(data['raw_values']),matched_pairs=len(data['pairs']),
        metric_fields=len(METRICS),descriptive_differences=sum(len(pair['metrics']) for pair in data['pairs']))
    return data


def main():
    assert not RUN.exists(), 'One invocation only; preserve prior output'
    RUN.mkdir()
    protocol_raw = (STAGE/'protocol.json').read_bytes()
    protocol = json.loads(protocol_raw)
    receipt = dict(card=CARD,status='running',protocol_sha256=sha256(protocol_raw).hexdigest(),
        default_installations=0,new_tests=0,HP_calls_by_wrapper=0,new_force_calls=0,new_tangent_calls=0,
        new_equilibrium_solves=0,new_API_associations=0,old_media_content_reads=0,old_GIF_stat_count=0,
        old_manual_stat_count=0,ordinary_JSON_reads=0,outputs={},started_utc=datetime.now(timezone.utc).isoformat())
    phase,error = 'bound_ordinary_inputs',None
    try:
        documents = {}
        assert len(protocol['ordinary_JSON_bindings'])==len(protocol['comparison_sources'])==2
        assert {item['path'] for item in protocol['comparison_sources'].values()}==set(protocol['ordinary_JSON_bindings'])
        for name,pin in protocol['ordinary_JSON_bindings'].items():
            check();raw=(ROOT/name).read_bytes()
            assert len(raw)==pin['bytes'] and sha256(raw).hexdigest()==pin['sha256'],name
            documents[name]=json.loads(raw);receipt['ordinary_JSON_reads']+=1
        for item in protocol['comparison_sources'].values():
            assert (ROOT/item['manual_path']).stat().st_size==item['manual_bytes']
            receipt['old_manual_stat_count']+=1
        phase = 'compatibility_and_comparison'
        data = compare(protocol,documents)
        write(RUN/'comparison.json',data)
        if data['status']!='pass':
            raise ValueError('Physical tasks incomparable outside the declared alpha/metadata allowance; see comparison.json')
        receipt['counts'] = data['counts']
        phase = 'two_scalar_views'
        from comparison_views import render
        render(data,RUN,ROOT)
        check();receipt['status']='pass'
    except BaseException as exc:
        error=exc
        receipt.update(status='not_pass',error=dict(type=type(exc).__name__,message=str(exc)))
    receipt['phase']=phase
    # Only new files are sealed within this original helper window; neither old page is opened.
    if monotonic()-STARTED < 180:
        for path in sorted(RUN.iterdir()):
            if path.is_file():
                check();raw=path.read_bytes()
                receipt['outputs'][path.relative_to(ROOT).as_posix()]=dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
        receipt['output_identity_seal']='complete_inside_original_helper_window'
    else:
        receipt.update(status='not_pass',output_identity_seal='original_window_expired_no_new_seal')
    receipt.update(elapsed_seconds=monotonic()-STARTED,sampled_RSS_bytes=psutil.Process().memory_info().rss,
        completed_utc=datetime.now(timezone.utc).isoformat(),scientific_payload_reads=0,external_retries=0)
    write(RUN/'execution_receipt.json',receipt)
    print(json.dumps({key:receipt[key] for key in ('card','status','phase','elapsed_seconds','ordinary_JSON_reads','old_manual_stat_count')},ensure_ascii=False),flush=True)
    if error is not None:raise error
    assert receipt['status']=='pass'


if __name__=='__main__':main()
