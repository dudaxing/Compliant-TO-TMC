"""Record a saved reference-running snapshot after the 4 mm production closes."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json

STAGE = 'lf_data_preparation/native_workpiece_001/right_margin4_cycle_001'
BASE = 'docs/evidence/workpiece_enlargement_20261007'
PROGRESS = BASE+'/right_margin4_progress.json'
CONTEXT = BASE+'/right_margin4_source_context'
REPORT = 'docs/WORKPIECE_ENLARGEMENT_20261007.md'
CURRENT = 'docs/CURRENT_STATUS.md'
VIEW = 'functional_views/right_margin4_20261007/complete_001'
PROD_SHA = 'f4d6d94f38bb9e27f9afbd21d97b62410e31e8c21e83fcfa90bedfa66712cbb1'
REF_SHA = '8af4df91d1897de525eba454f2a66ec61f03f25ee5b80f46076a41255f5d06cb'
RESULT_SHA = 'b49955f7e56cd714b35283c0834757ebefc947d3ca25a4f505ed44e8947db7b6'
sha = lambda data:sha256(data).hexdigest()
read = lambda path:json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    root,author = parser.parse_args().repo.resolve(),Path(__file__).resolve().parent
    note = read(author/'reference_running_author_note.json')
    stage,context = root/STAGE,root/CONTEXT
    assert context.is_dir() and not (context/'reference_running_record_receipt.json').exists()
    before = {name:(root/name).read_bytes() for name in (PROGRESS,REPORT,CURRENT)}
    assert all(sha(data)==note['expected_preimages'][name] for name,data in before.items())
    assert all(sha((author/name).read_bytes())==pin for name,pin in note['candidate_sources'].items())
    pbytes,rbytes = (stage/'production_protocol.json').read_bytes(),(stage/'reference_protocol.json').read_bytes()
    assert sha(pbytes)==PROD_SHA and sha(rbytes)==REF_SHA
    pp,rp = json.loads(pbytes),json.loads(rbytes)
    assert pp['phases']['production']['helper_seconds']==4500 and pp['phases']['production']['outer_seconds']==4560
    assert rp['phases']['reference']['helper_seconds']==1500 and rp['phases']['reference']['outer_seconds']==1560
    assert pp['sampled_RSS_bytes']==rp['sampled_RSS_bytes']==8*1024**3
    assert rp['actual_accepted_states']==24 and rp['expected_new_HP80_120_calls']==48
    prod_launch_bytes = (stage/'production_launch.json').read_bytes()
    execution_bytes = (stage/'run_001/execution_receipt.json').read_bytes()
    result_bytes = (stage/'run_001/result/result.json').read_bytes()
    launch,execution,result = json.loads(prod_launch_bytes),json.loads(execution_bytes),json.loads(result_bytes)
    assert sha(result_bytes)==execution['result_sha256']==RESULT_SHA
    assert launch['status']==execution['status']=='pass' and launch['invocations']==execution['invocations']==1
    assert launch['exit_code']==0 and launch['stop_reason'] is None and launch['all_bindings_unchanged']
    assert launch['protocol_sha256']==PROD_SHA and launch['bindings']==pp['bindings']
    assert launch['elapsed_seconds']<=4560 and launch['peak_sampled_tree_RSS_bytes']<=8*1024**3
    assert execution['sources_unchanged'] and execution['inputs_unchanged']
    assert execution['elapsed_seconds']<=4500 and execution['sampled_peak_RSS_bytes']<=8*1024**3
    assert execution['HP_calls']==execution['JIT_calls']==execution['LF_imports']==0
    assert result['status']=='success' and result['production_converged'] and result['failure'] is None
    assert result['path_completed'] and result['loading_peak_reached'] and result['unload_endpoint_reached']
    assert execution['accepted_states']==result['accepted_states']==len(result['states'])==24
    assert result['targets_mm'][0]==result['targets_mm'][-1]==0 and max(result['targets_mm'])==1.2
    assert execution['model_sha256']==result['model']['arrays_sha256']
    contract = read(stage/'reference_contract.json')
    assert contract['production_result_sha256']==RESULT_SHA
    assert contract['production_receipt_sha256']==sha(execution_bytes) and contract['production_launch_sha256']==sha(prod_launch_bytes)
    assert contract['actual_accepted_states']==24 and contract['expected_new_HP80_120_calls']==48
    for name,key in [('input_inventory.json','input_inventory_sha256'),('source_freeze.json','source_freeze_sha256')]:
        assert sha((stage/'run_001'/name).read_bytes())==execution[key]==contract[key]

    def running():
        lb,hb = (stage/'reference_launch.json').read_bytes(),(stage/'reference/lifecycle.json').read_bytes()
        l,h = json.loads(lb),json.loads(hb)
        assert l['status']==h['status']=='running', 'Reference already terminal or not demonstrably running'
        assert l['invocations']==1 and l['protocol_sha256']==REF_SHA and l['bindings']==rp['bindings']
        assert h['error'] is None and h['time_limit_seconds']==1500 and h['sampled_RSS_limit_bytes']==8*1024**3
        assert h['elapsed_seconds']<=1500 and h['sampled_peak_RSS_bytes']<=8*1024**3
        assert 0<=h['HP_calls_completed']<=h['HP_calls_started']<=48
        assert not (stage/'reference/summary.json').exists() and not (stage/'stop_requested.txt').exists()
        assert not (root/VIEW/'view_launch.json').exists(), 'View stage already started'
        return l,h,lb,hb

    refl,life,launch_raw,life_raw = running()
    timestamp = refl['started_utc']
    source_time = datetime.fromisoformat(timestamp)
    assert source_time.tzinfo is not None
    started_utc = source_time.astimezone(timezone.utc).isoformat()
    offset = source_time.strftime('%z'); offset = offset[:3]+':'+offset[3:]
    captured = datetime.now(timezone.utc).isoformat()
    progress = json.loads(before[PROGRESS])
    progress['status'] = 'production_pass_reference_running_not_qualified'
    progress['prior_running_snapshot'] = dict(path=CONTEXT+'/013.json',sha256=sha(before[PROGRESS]))
    progress['production'] = dict(status='pass',independent_reference_qualified=False,accepted_states=24,
        result_file=STAGE+'/run_001/result/result.json',result_sha256=RESULT_SHA,
        execution_receipt_sha256=sha(execution_bytes),production_launch_sha256=sha(prod_launch_bytes),
        model_sha256=execution['model_sha256'],task_sha256=execution['task_sha256'],
        helper_elapsed_seconds=execution['elapsed_seconds'],outer_elapsed_seconds=launch['elapsed_seconds'],
        helper_seconds=4500,outer_seconds=4560,RSS_bytes=8*1024**3,
        sources_unchanged=True,inputs_unchanged=True,call_counts=result['call_counts'],
        scope='Complete production only; same-result fresh independent reference pending')
    progress['reference'] = dict(status='running_not_qualified',snapshot_utc=captured,
        protocol_file=STAGE+'/reference_protocol.json',protocol_sha256=REF_SHA,
        result_sha256=RESULT_SHA,actual_accepted_states=24,expected_fresh_HP_calls=48,
        helper_seconds=1500,outer_seconds=1560,RSS_bytes=8*1024**3,
        started_utc=started_utc,started_source_field=STAGE+'/reference_launch.json:started_utc',
        raw_started_timestamp=timestamp,source_offset=offset,
        saved_lifecycle_snapshot=life,lifecycle_path=CONTEXT+'/014.json',
        launch_path=CONTEXT+'/015.json',scope='Timestamped saved running snapshot, not liveness or reference qualification')
    progress['complete_cycle_views'] = dict(status='pending_not_started',new_scientific_calls=0,
        requirement='Actual same-result full reference pass before complete saved views')
    banner = f"4 mm当前状态（UTC {captured}）：一次生产已完成24态0→1.2→0；同结果48次新HP独立参考正在运行（保存快照已完成{life['HP_calls_completed']}/48），尚无独立参考资格，完整周期保存视图尚未启动。2 mm完整评价已完成；HF仅提供正向评估，不含优化器。\n\n"
    append = f"\n\n## 4 mm生产已完成，独立参考运行快照（UTC {captured}）\n\n生产24接受态完整0→1.2→0已闭卡通过；result SHA {RESULT_SHA}。helper {execution['elapsed_seconds']:.7f}秒，outer {launch['elapsed_seconds']:.7f}秒，在4500/4560秒、8 GiB窗口内，source/input身份保持；生产HP/JIT/LF调用为0。本次生产状态不代替独立参考资格。\n\n同结果新参考一次启动，协议SHA {REF_SHA}，24态预期48次新HP，1500/1560秒、8 GiB；启动显示UTC {started_utc}，原reference_launch.json.started_utc字段 {timestamp}（源偏移{offset}）保留未改。保存lifecycle快照started={life['HP_calls_started']}、completed={life['HP_calls_completed']}，仅表示此时间点记录，不作进程存活或最终pass证明。完整周期视图尚未启动；未来须实际同结果全N/2N参考通过。此前9态生产运行progress原字节保留013.json，参考快照见014/015.json及reference_running_record_receipt.json；零新增科学调用。\n"
    after = {PROGRESS:(json.dumps(progress,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'),
             CURRENT:banner.encode('utf-8')+before[CURRENT],REPORT:before[REPORT]+append.encode('utf-8')}
    archive = {'013.json':before[PROGRESS],'014.json':life_raw,'015.json':launch_raw}
    for short,name in [('016.py','record_reference_running.py'),('017.json','reference_running_author_note.json'),
                       ('018.md','REFERENCE_RUNNING_README.md'),('019.json','reference_running_author_checks.json'),
                       ('020.diff','reference_running_source_additions.diff')]:
        archive[short]=(author/name).read_bytes()
    assert all((root/name).read_bytes()==data for name,data in before.items())
    for name in archive:assert not (context/name).exists(),name
    running()
    for name,data in archive.items():(context/name).write_bytes(data)
    running()
    for name,data in after.items():(root/name).write_bytes(data)
    try:
        running()
    except Exception:
        for name,data in before.items():(root/name).write_bytes(data)
        raise RuntimeError('Reference closed during recording; three raw docs restored; archive retained')
    receipt = dict(status='pass_file_reference_running_snapshot',snapshot_utc=captured,new_scientific_calls=0,
        production_result_sha256=RESULT_SHA,production_accepted_states=24,reference_protocol_sha256=REF_SHA,
        HP_calls_started_snapshot=life['HP_calls_started'],HP_calls_completed_snapshot=life['HP_calls_completed'],
        started_utc=started_utc,raw_started_timestamp=timestamp,source_offset=offset,
        closure_checked_before_and_after_writes=True,
        archived={name:dict(path=CONTEXT+'/'+name,sha256=sha(data)) for name,data in archive.items()},
        installed={name:dict(before_sha256=sha(before[name]),after_sha256=sha(data)) for name,data in after.items()})
    (context/'reference_running_record_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=receipt['status'],production_states=24,reference_HP_completed=life['HP_calls_completed'])))


if __name__=='__main__':main()
