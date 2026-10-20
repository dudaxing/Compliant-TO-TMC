"""Unify pinned ordinary saved observations; no mechanics or scientific arrays."""
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
CARD = 'L-CTIPPATH1'
RUN = STAGE/'run_001'
METRICS = ('R_input_N','q_out_mm','tip_x_mm','tip_y_mm',
    'tip_to_raster_boundary_mm','minimum_boundary_distance_mm','solid_min_J','medium_min_J',
    'solid_Green_principal_min','solid_Green_principal_max','medium_max_abs_Hu_per_mm',
    'right_medium_min_J','right_medium_max_J','right_medium_max_abs_Hu_per_mm',
    'right_medium_Green_principal_min','right_medium_Green_principal_max',
    'right_medium_max_nodal_displacement_mm','total_body_Fx_N','total_body_Fy_N',
    'material_body_Fx_N','material_body_Fy_N','regularization_body_Fx_N','regularization_body_Fy_N')
SCOPE = ('Existing saved ordinary observations only. Chronological display across fourteen separately solved '
    'segments is not one complete solve or full-path independent reference. Original origin/resume_origin/loading/'
    'unloading legs and all source accepts/diagnostics are retained. Signed lower-body weak forces are not '
    'circular local pressure or qualified effective grip; q_out is a weighted port displacement, not a gap; '
    'Q1 distances are unsigned raster-boundary diagnostics, not analytic-circle signed gaps. '
    'No new force/tangent/HP/equilibrium/tests/default changes/API association, zero/recovery/energy/stability '
    'criterion or qualification. Whole-model Hu is not available in these inputs and is not inferred from medium Hu.')


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def check():
    assert monotonic()-STARTED < 180, 'Original helper deadline reached'
    rss = psutil.Process().memory_info().rss
    assert rss <= 1024**3, 'Original helper RSS limit reached'
    return rss


def identical(a, b):
    if isinstance(a,float) or isinstance(b,float):
        return isinstance(a,(float,int)) and isinstance(b,(float,int)) and float(a).hex()==float(b).hex()
    if isinstance(a,dict) and isinstance(b,dict):
        return a.keys()==b.keys() and all(identical(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):
        return len(a)==len(b) and all(identical(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b


def consolidate(protocol, documents):
    raw_rows, timeline, segments, history, exceptions, merges = [], [], [], [], [], []
    totals = {}
    previous_result_seal = None
    for item in protocol['segments']:
        summary = documents[item['paths']['summary']]
        convergence = documents[item['paths']['convergence']]
        rows, accepts = summary['rows'], convergence['accepted_states']
        assert summary['schema_version']=='saved-circle-right-workpiece-summary-1.0'
        assert convergence['schema_version']=='hf-labelled-convergence-observation-1.0'
        assert summary['production_status']==convergence['result_metadata']['status']=='success'
        assert len(rows)==len(accepts)==summary['accepted_states']==convergence['counts']['accepted_states']
        metadata = convergence['result_metadata']
        if previous_result_seal is not None:
            cont = metadata['continuation']
            assert cont['parent_result']['sha256']==previous_result_seal['sha256']
            assert cont['selected_state']['state_sha256']==rows[0]['state_sha256']
            assert identical(cont['selected_state']['R_input_N'],rows[0]['R_input_N'])
        for index,(row,accept) in enumerate(zip(rows,accepts)):
            assert list(row)==protocol['summary_row_fields'] and row['index']==index
            for a,b in [('state_sha256','state_sha256'),('d_mm','d'),('R_input_N','R_input'),
                        ('q_out_mm','q_out'),('original_target_index','original_target_index'),('leg','leg')]:
                assert identical(row[a],accept[b]), (item['segment'],index,a)
            assert all(math.isfinite(row[k]) for k in METRICS)
            source = dict(segment=item['segment'],source_row_index=index,summary_path=item['paths']['summary'],
                          convergence_path=item['paths']['convergence'],raw_row_index=len(raw_rows))
            boundary_anchor = index==0 and bool(timeline)
            if boundary_anchor:
                compare = {k:v for k,v in row.items() if k not in ('index','leg')}
                prior = {k:timeline[-1][k] for k in compare}
                assert row['leg']=='resume_origin'
                merge = identical(compare,prior)
            else:
                merge = False
            if merge:
                display_index = timeline[-1]['display_index']
                timeline[-1]['sources'].append(source)
                merges.append(dict(display_index=display_index,source=source,
                    rule='Adjacent boundary only; every summary field except local index/raw leg agrees exactly, including signed binary64 values'))
            else:
                display_index = len(timeline)
                branch = timeline[-1]['display_branch'] if boundary_anchor else row['leg']
                assert branch in ('origin','loading','unloading')
                timeline.append(dict(row,display_index=display_index,display_branch=branch,
                    unmerged_boundary_anchor=boundary_anchor,
                    raw_leg=row['leg'],sources=[source],convergence=accept))
            raw_rows.append(dict(row,raw_row_index=len(raw_rows),segment=item['segment'],display_index=display_index,
                                 raw_leg=row['leg'],convergence=accept))
        counts = convergence['counts']
        for key,value in counts.items():
            totals[key] = max(totals.get(key,0),value) if key=='maximum_bisection_depth' else totals.get(key,0)+value
        for trial_index,trial in enumerate(convergence['raw_line_search_trials']):
            if not trial['accepted']:
                exceptions.append(dict(segment=item['segment'],kind='rejected_internal_trial',source_index=trial_index,record=trial))
        for failure_index,failure in enumerate(convergence['raw_failed_attempts']):
            exceptions.append(dict(segment=item['segment'],kind='original_failed_attempt',source_index=failure_index,record=failure))
        # Retain all original diagnostics, including revalidated anchors and bounded rejects.
        history.append(dict(segment=item['segment'],paths=item['paths'],convergence=convergence))
        segments.append(dict(item,counts=counts,result_metadata={k:v for k,v in metadata.items() if k!='continuation'},
            reference_available=summary['reference_available'],source_result_declared_seal=convergence['source'],
            force_scope=summary['force_scope'],right_medium_definition=summary['right_medium']['definition']))
        previous_result_seal = convergence['source']
    task = documents[protocol['task']]
    assert task['path']['kind']=='ordered_cycle' and task['input']['target_mm']==1.06
    requests = [r for r in timeline if r['convergence']['is_original_target'] and not r['unmerged_boundary_anchor']]
    assert [r['original_target_index'] for r in requests]==list(range(len(task['path']['targets_mm'])))
    assert [r['d_mm'] for r in requests]==task['path']['targets_mm']
    pairs = []
    for unload in (r for r in timeline if r['display_branch']=='unloading' and not r['unmerged_boundary_anchor']):
        refs = [r for r in timeline if not r['unmerged_boundary_anchor'] and r['display_branch'] in ('origin','loading') and identical(r['d_mm'],unload['d_mm'])]
        assert len(refs)==1, 'Missing or ambiguous exact-input reference'
        ref = refs[0]
        pairs.append(dict(d_mm=unload['d_mm'],reference_role='original_origin' if ref['raw_leg']=='origin' else 'loading',
            loading_display_index=ref['display_index'],unloading_display_index=unload['display_index'],
            loading_raw_leg=ref['raw_leg'],unloading_raw_leg=unload['raw_leg'],
            loading=dict(state_sha256=ref['state_sha256'],sources=ref['sources']),
            unloading=dict(state_sha256=unload['state_sha256'],sources=unload['sources']),
            metrics={key:dict(loading_value=ref[key],unloading_value=unload[key],
                unloading_minus_loading=unload[key]-ref[key]) for key in METRICS}))
    return dict(card=CARD,status='pass',schema_version='lf-circle-tip-ordinary-path-1.0',scope=SCOPE,
        original_task=task,raw_rows=raw_rows,timeline_rows=timeline,segments=segments,
        same_input_pairs=pairs,merged_boundary_anchors=merges,convergence_totals=totals,
        exceptions=exceptions,original_history=history,
        counts=dict(raw_rows=len(raw_rows),timeline_rows=len(timeline),merged_boundary_anchors=len(merges),
                    same_input_pairs=len(pairs),segments=len(segments),requested_targets=len(task['path']['targets_mm'])),
        qualification=dict(new_scientific_calls=0,new_reference_pass=False,full_path_reference_pass=False,
            pressure_qualified=False,effective_grip_qualified=False,release_qualified=False,stability_qualified=False,HF5_qualified=False))


def main():
    assert not RUN.exists(), 'One invocation only; preserve prior output'
    RUN.mkdir()
    protocol_raw = (STAGE/'protocol.json').read_bytes()
    protocol = json.loads(protocol_raw)
    receipt = dict(card=CARD,status='running',protocol_sha256=sha256(protocol_raw).hexdigest(),
        default_installations=0,new_tests=0,HP_calls_by_wrapper=0,new_force_calls=0,new_tangent_calls=0,
        new_equilibrium_solves=0,new_API_associations=0,old_media_content_reads=0,old_GIF_stat_count=0,
        ordinary_JSON_reads=0,outputs={},started_utc=datetime.now(timezone.utc).isoformat())
    phase = 'bound_ordinary_inputs'
    error = None
    try:
        documents = {}
        assert len(protocol['ordinary_JSON_bindings'])==29 and len(protocol['segments'])==14
        for name,pin in protocol['ordinary_JSON_bindings'].items():
            check()
            raw=(ROOT/name).read_bytes()
            assert len(raw)==pin['bytes'] and sha256(raw).hexdigest()==pin['sha256'],name
            documents[name]=json.loads(raw);receipt['ordinary_JSON_reads']+=1
        for item in protocol['segments']:
            assert (ROOT/item['paths']['GIF']).stat().st_size==item['GIF_bytes']
            receipt['old_GIF_stat_count']+=1
        phase = 'ordinary_association'
        data = consolidate(protocol,documents)
        history = data.pop('original_history')
        check()
        write(RUN/'unified_response.json',data)
        write(RUN/'source_history.json',dict(card=CARD,segments=history,scope='Original complete ordinary convergence records, no count subtraction'))
        write(RUN/'same_input_comparison.json',dict(card=CARD,scope='Descriptive raw values and subtraction only; loading_value at zero references the original raw-leg origin, no added equality/energy/recovery criterion',pairs=data['same_input_pairs']))
        receipt.update(counts=data['counts'],accepted_states=data['counts']['timeline_rows'],convergence_totals=data['convergence_totals'])
        phase = 'two_scalar_views'
        from path_views import render
        render(data,RUN,ROOT)
        check()
        receipt['status']='pass'
    except BaseException as exc:
        error=exc
        receipt.update(status='not_pass',error=dict(type=type(exc).__name__,message=str(exc)))
    receipt['phase']=phase
    # No old media is opened. Seal only new outputs, inside this unique helper window.
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
    print(json.dumps({k:receipt[k] for k in ('card','status','phase','elapsed_seconds','ordinary_JSON_reads','old_GIF_stat_count')},ensure_ascii=False),flush=True)
    if error is not None: raise error
    assert receipt['status']=='pass'


if __name__=='__main__':
    main()
