"""One saved-JSON association and consumption; no mechanical evaluator imports."""
from time import perf_counter
STARTED=perf_counter()
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import psutil

STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parents[2]
read=lambda p: json.loads(p.read_bytes())
protocol=read(STAGE/'protocol.json')
OUTPUT=ROOT/protocol['output_directory']
events,calls,peak=Counter(),Counter(),0
process=psutil.Process()


def checkpoint(event='resource_check'):
    global peak
    peak=max(peak,process.memory_info().rss)
    if (perf_counter()-STARTED>protocol['helper_seconds'] or peak>protocol['sampled_RSS_bytes']
            or (STAGE/'stop_requested.txt').exists()):
        raise RuntimeError('L-TUSE1 resource/stop boundary reached')
    events[event]+=1


def digest(path): return sha256(path.read_bytes()).hexdigest()


def write(path,value):
    checkpoint()
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def verify_bindings():
    for name,pin in {**protocol['input_bindings'],**protocol['source_bindings']}.items():
        checkpoint()
        assert digest(ROOT/name)==pin,name


def artifact(path):
    return dict(path=path,path_scope='repo_relative',sha256=protocol['input_bindings'][path])


def seal():
    outputs={}
    for path in sorted(OUTPUT.rglob('*')):
        if path.is_file() and path.name!='execution_receipt.json':
            checkpoint()
            outputs[path.relative_to(ROOT).as_posix()]=dict(sha256=digest(path),bytes=path.stat().st_size)
    checkpoint()
    return outputs


def main():
    auth=read(STAGE/'author/authorization.json')
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is auth['one_invocation'] is True
    assert auth['card']==protocol['card']=='L-TUSE1'
    assert auth['protocol_sha256']==digest(STAGE/'protocol.json')
    assert not OUTPUT.exists()
    OUTPUT.mkdir()
    status,error,outputs,identity_seal='not_pass',None,{},'not_complete'
    response,table=None,None
    bindings_unchanged=False
    try:
        verify_bindings()
        a=protocol['artifacts']
        prod,ref=read(ROOT/a['production_receipt_file']),read(ROOT/a['reference_execution_receipt_file'])
        for receipt in (prod,ref):
            assert receipt['status']=='pass'
            assert receipt['output_identity_seal']=='complete_inside_original_helper_window'
        reference=read(ROOT/a['reference_file'])
        assert reference['gates']==protocol['original_fifteen_gates']
        for record in protocol['media']:
            source=prod['outputs'].get(record['path'],ref['outputs'].get(record['path']))
            assert source=={key:record[key] for key in ('sha256','bytes')}
            assert (ROOT/record['path']).stat().st_size==record['bytes']
        sys.path.insert(0,str(ROOT/'hf_repo/src'))
        import hf_eval
        from hf_eval import native_response
        assert Path(hf_eval.__file__).resolve()==ROOT/'hf_repo/src/hf_eval/__init__.py'
        assert Path(native_response.__file__).resolve()==ROOT/'hf_repo/src/hf_eval/native_response.py'
        calls['saved_summary_started']+=1
        response=native_response.summarize_saved_native_result(a['result_file'],repo_root=ROOT,
            reference_file=a['reference_file'],view_manifest=a['raw_view_file'])
        calls['saved_summary_completed']+=1
        checkpoint()
        original=read(ROOT/a['original_response_file'])
        # evaluate_native adds run metadata which a saved summary does not generate.
        excluded={'views','independent_reference','invocation','evaluation_elapsed_seconds','evaluation_elapsed_scope'}
        assert {k:v for k,v in response.items() if k not in excluded}=={
            k:v for k,v in original.items() if k not in excluded}
        independent=response['independent_reference']
        assert response['status']=='success' and response['path']['completed'] is True
        assert response['path']['accepted_states']==protocol['expected_rows']==25
        assert independent['status']=='matched_partial' and independent['selected_reference_pass'] is True
        assert independent['matched_state_indices']==protocol['selected_indices']==[13,14]
        assert not any(independent[key] for key in ('covers_all_accepted_states','accepted_reference_pass',
            'full_path_reference_pass','HP_all_columns_qualified','contact_qualified','clamp_qualified',
            'pressure_qualified','HF5_qualified'))
        assert independent['reasons']==[] and independent['source_bindings_verified'] is True
        assert response['views']['status']=='matched' and len(response['views']['links'])==4
        media=protocol['media']
        for actual,expected in zip(response['views']['links'],media[:4]):
            assert all(actual[key]==expected[key] for key in ('path','path_scope','sha256','kind'))
        for extra in media[4:]:
            checkpoint()
            assert digest(ROOT/extra['path'])==extra['sha256']
            calls['extra_media_raw_SHA_verifications']+=1
        native_response.write_native_response(response,OUTPUT/'linked_response.json')
        calls['response_writes']+=1
        index=dict(schema_version='lf-selected-reference-linked-index-1.0',status='pass',
            linked_response=dict(path=(OUTPUT/'linked_response.json').relative_to(ROOT).as_posix(),
                path_scope='repo_relative',sha256=digest(OUTPUT/'linked_response.json')),
            saved_artifacts={key:artifact(path) for key,path in a.items()},images=media,
            physics=response['physics'],options=response['options'],path=response['path'],
            maximum_loading_stroke=response['maximum_loading_stroke'],
            requested_endpoint_response=response['requested_endpoint_response'],
            target_response=response['target_response'],independent_reference=independent,views=response['views'],
            source_flags=response['producer_flags'],force_semantics=response['force_semantics'],
            field_scope=response['field_scope'],production_accepted_states=25,selected_accepted_indices=[13,14],
            original_target_indices=[13,14],selected_targets_mm=[1.2,1.15],
            reference_scope=reference['reference_scope'],qualification=reference['qualification'],
            path_basis='All saved artifacts and six existing media are repository-relative; raw SHA verified, no decoding or new rendering')
        write(OUTPUT/'light_index.json',index)
        calls['index_writes']+=1
        source=ROOT/protocol['example_source']
        spec=importlib.util.spec_from_file_location('_third_lf_saved_consumer',source)
        consumer=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(consumer)
        calls['consumptions_started']+=1
        table=consumer.consume(ROOT,(OUTPUT/'light_index.json').relative_to(ROOT),
            OUTPUT/'consumer',checkpoint)
        calls['consumptions_completed']+=1
        result=read(ROOT/a['result_file'])
        assert len(table['rows'])==25 and len(table['existing_media'])==protocol['expected_media']==6
        assert [r['accepted_row_index'] for r in table['rows'] if r['has_matched_reference']]==[13,14]
        fields=dict(original_target_index='original_target_index',is_original_target='is_original_target',
            state_sha256='state_sha256',leg='leg',d_mm='d',R_input_N='R_input',q_in_mm='q_in',
            q_out_mm='q_out',minimum_J='minimum_J')
        for i,(row,saved) in enumerate(zip(table['rows'],result['states'])):
            assert row['accepted_row_index']==i and saved['original_target_index']==i
            assert all(row[key]==saved[name] for key,name in fields.items())
            assert row['force_on_lower_body_N']==saved['workpiece']['force_on_lower_body_N']
        assert table['independent_reference']==independent
        assert table['producer_flags']==original['producer_flags']
        assert all(value is False for value in table['producer_flags'].values())
        assert {k:events[k] for k in ('json_read_started','json_read_completed','table_written','review_written')}==dict(
            json_read_started=3,json_read_completed=3,table_written=1,review_written=1)
        assert {name for name in sys.modules if name=='hf_eval' or name.startswith('hf_eval.')}=={
            'hf_eval','hf_eval.native_response'}
        calls.update(table_writes=events['table_written'],review_writes=events['review_written'])
        assert all(calls[key]==value for key,value in protocol['expected_calls'].items())
        verify_bindings()
        bindings_unchanged=True
        write(OUTPUT/'delivery_summary.json',dict(status='pass',rows=25,reference_rows=[13,14],
            reference_scope=reference['reference_scope'],matched_partial=True,full_path_reference_pass=False,
            existing_media=6,original_producer_flags=table['producer_flags'],all_projected_row_fields_equal=True,
            original_response_preserved=True,default_source_changed=False,
            media_verification='Four raw SHA checks by default _views plus two extra raw SHA checks; zero decode/redraw',
            consumer_JSON_reads=3,consumer_projection='Original floats and signed component vectors; only display rounded',
            next_action='Arrange three-design same-definition comparison; not executed by this phase'))
        outputs=seal()
        identity_seal='complete_inside_original_helper_window'
        status='pass'
    except BaseException as failure:
        error=dict(type=type(failure).__name__,message=str(failure))
        if perf_counter()-STARTED<=protocol['helper_seconds'] and not (STAGE/'stop_requested.txt').exists():
            try:
                outputs=seal()
                identity_seal='actual_partial_inside_original_helper_window'
            except BaseException:
                identity_seal='not_complete_before_resource_close'
    receipt=dict(card='L-TUSE1',status=status,error=error,calls=dict(calls),consumer_events=dict(events),
        protocol_sha256=auth['protocol_sha256'],source_baseline_commit=protocol['source_baseline_commit'],
        outputs=outputs,output_identity_seal=identity_seal,all_bindings_unchanged=bindings_unchanged,
        rows_written=len(table['rows']) if table else 0,selected_indices=[13,14] if table else [],
        helper_seconds=protocol['helper_seconds'],elapsed_seconds=perf_counter()-STARTED,
        sampled_peak_RSS_bytes=peak,sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()),completed_utc=datetime.now(timezone.utc).isoformat(),
        zero_science_basis='Pinned stdlib consumer/default metadata source and HF import set; no universal mechanical hooks',
        HF_API_summary_calls=calls['saved_summary_completed'],consumer_JSON_reads=events['json_read_completed'],
        existing_media_raw_SHA_verifications=6 if status=='pass' else None,
        new_tests=0,new_F_T_HP_model_solver_calls=0,new_plots=0,media_decodes=0,pixel_checks=0,
        NPZ_reads=0,scientific_gzip_reads=0,default_installations=0)
    write(OUTPUT/'execution_receipt.json',receipt)
    print(json.dumps(dict(status=status,calls=dict(calls),rows=receipt['rows_written'],error=error)),flush=True)
    if status!='pass':
        raise RuntimeError('L-TUSE1 closed not_pass; no retry')


if __name__=='__main__':
    main()
