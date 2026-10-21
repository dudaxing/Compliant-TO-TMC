"""Run the saved-study CLI once in-process and seal only its two ordinary outputs."""
from time import monotonic
STARTED = monotonic()
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import psutil

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[2]
RUN = STAGE/'run_001'
CARD = 'L-CTIPAREPORT1'


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def check():
    assert monotonic()-STARTED < 180, 'Original helper deadline reached'
    assert psutil.Process().memory_info().rss <= 1024**3, 'Original helper RSS limit reached'


def main():
    assert not RUN.exists(), 'One invocation only; preserve prior output'
    RUN.mkdir()
    raw=(STAGE/'protocol.json').read_bytes();protocol=json.loads(raw)
    receipt=dict(card=CARD,status='running',protocol_sha256=sha256(raw).hexdigest(),default_installations=0,
        new_tests=0,HP_calls_by_wrapper=0,new_force_calls=0,new_tangent_calls=0,new_equilibrium_solves=0,
        new_API_associations=0,default_HF_API_calls=0,scientific_payload_reads=0,old_media_content_reads=0,
        old_GIF_stat_count=0,new_PNGs=0,new_media_QA=0,function_calls=0,ordinary_JSON_reads=0,
        asset_stat_count=0,old_manual_stat_count=0,old_PNG_stat_count=0,outputs={},
        control_read_scope='Protocol/auth/source/resource controls are separate from the two saved business JSON reads',
        started_utc=datetime.now(timezone.utc).isoformat())
    phase,error,reader = 'single_saved_report_CLI',None,None
    try:
        check()
        import saved_study_report as reader
        view=reader.main(['--repo',str(ROOT),'--protocol',str(STAGE/'protocol.json'),'--output',str(RUN)])
        receipt['returned_keys']=list(view)
        receipt['returned_object_aliases']={
            'cycles_baseline_is_original':view['cycles']['baseline'] is view['scalar_comparison']['sources']['baseline']['original'],
            'cycles_new_is_original':view['cycles']['new'] is view['scalar_comparison']['sources']['new']['original']}
        assert all(receipt['returned_object_aliases'].values())
        assert view['report']['status']=='linked_existing_saved_reports'
        receipt['preserved_counts']={key:view['report'][key]['counts'] for key in ('scalar_comparison','peak_node_comparison')}
        check();receipt['status']='pass'
    except BaseException as exc:
        error=exc;receipt.update(status='not_pass',error=dict(type=type(exc).__name__,message=str(exc)))
    if reader is not None:
        receipt.update(reader.LAST_BUSINESS_IO)
    receipt['phase']=phase
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
    print(json.dumps({key:receipt[key] for key in ('card','status','phase','function_calls','ordinary_JSON_reads','asset_stat_count')},ensure_ascii=False),flush=True)
    if error is not None:raise error
    assert receipt['status']=='pass'


if __name__=='__main__':main()
