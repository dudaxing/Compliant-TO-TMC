"""One authorized ordinary-JSON comparison and two scalar figures."""
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
read=lambda path:json.loads(path.read_bytes())
protocol=read(STAGE/'protocol.json')
OUTPUT=ROOT/protocol['output_directory']
events,calls,peak=Counter(),Counter(),0
process=psutil.Process()


def checkpoint(event='resource_check'):
    global peak
    peak=max(peak,process.memory_info().rss)
    if (perf_counter()-STARTED>protocol['helper_seconds'] or peak>protocol['sampled_RSS_bytes']
            or (STAGE/'stop_requested.txt').exists()):
        raise RuntimeError('L-TCOMP1 resource/stop boundary reached')
    events[event]+=1


def bindings():
    for name,pin in (protocol['input_bindings']|protocol['source_bindings']).items():
        checkpoint()
        assert sha256((ROOT/name).read_bytes()).hexdigest()==pin,name


def seal():
    outputs={}
    for name in ('comparison.json','responses.png','geometry_quality.png','REVIEW.md'):
        checkpoint()
        path=OUTPUT/name
        if path.exists():
            raw=path.read_bytes()
            outputs[path.relative_to(ROOT).as_posix()]=dict(sha256=sha256(raw).hexdigest(),bytes=len(raw))
    checkpoint()
    return outputs


def main():
    auth=read(STAGE/'author/authorization.json')
    assert auth['card']==protocol['card']=='L-TCOMP1'
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is auth['one_invocation'] is True
    assert auth['protocol_sha256']==sha256((STAGE/'protocol.json').read_bytes()).hexdigest()
    assert not OUTPUT.exists()
    status,error,data,outputs,identity_seal='not_pass',None,None,{},'not_complete'
    unchanged=False
    try:
        bindings()
        spec=importlib.util.spec_from_file_location('_three_saved_comparison',ROOT/protocol['example_source'])
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        calls['comparisons_started']+=1
        data=module.run(ROOT,protocol['inputs'],protocol['media'],OUTPUT,checkpoint)
        calls['comparisons_completed']+=1
        assert [len(d['rows']) for d in data['designs']]==protocol['expected_rows']==[25,25,25]
        assert len(data['pairs'])==protocol['expected_pairs']==25
        assert events['json_read_started']==events['json_read_completed']==protocol['expected_JSON_reads']==10
        assert events['plot_started']==events['plot_completed']==protocol['expected_plots']==2
        assert events['comparison_written']==events['review_written']==1
        assert events['media_stat_started']==events['media_stat_completed']==protocol['expected_media_stat_checks']==18
        assert all(value is False for value in data['qualification'].values())
        assert not any(name=='hf_eval' or name.startswith('hf_eval.') for name in sys.modules)
        bindings()
        unchanged=True
        outputs=seal()
        assert len(outputs)==4
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
    OUTPUT.mkdir(parents=True,exist_ok=True)
    receipt=dict(card='L-TCOMP1',status=status,error=error,calls=dict(calls),events=dict(events),
        protocol_sha256=auth['protocol_sha256'],source_baseline_commit=protocol['source_baseline_commit'],
        design_rows=[len(d['rows']) for d in data['designs']] if data else [],pairs=len(data['pairs']) if data else 0,
        outputs=outputs,output_identity_seal=identity_seal,all_bindings_unchanged=unchanged,
        elapsed_seconds=perf_counter()-STARTED,helper_seconds=protocol['helper_seconds'],
        sampled_peak_RSS_bytes=peak,sampled_RSS_limit_bytes=protocol['sampled_RSS_bytes'],
        working_directory=str(Path.cwd()),completed_utc=datetime.now(timezone.utc).isoformat(),
        JSON_read_scope='10 example JSON reads; wrapper SHA byte reads are separate',
        zero_science_basis='Pinned study source and no HF package imported; no universal mechanical hooks',
        new_HF_API_calls=0,new_F_T_HP_model_solver_calls=0,new_tests=0,default_installations=0,
        new_plots=events['plot_completed'],old_media_reads=0,old_media_decodes=0,
        NPZ_reads=0,scientific_gzip_reads=0,CSV_reads=0,pixel_checks_by_helper=0,
        full_path_reference_upgraded=False,formal_labels=False,ranking=False)
    with (OUTPUT/'execution_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    checkpoint()
    print(json.dumps(dict(status=status,calls=dict(calls),rows=receipt['design_rows'],pairs=receipt['pairs'],error=error)),flush=True)
    if status!='pass':
        raise RuntimeError('L-TCOMP1 closed not_pass; no retry')


if __name__=='__main__':
    main()
