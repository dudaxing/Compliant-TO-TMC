"""Archive real M-BOUND1 results/reviews after its authorized unique execution.

Draft prose must be written from the actual saved results. This tool never
generates scientific numbers, renders images or imports the candidate. It is
not to be invoked during preparation or after a failed numerical run.
"""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
EXT = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/nested_hu_boundary_001'
STAGE = ROOT/REL
BASE = 'eb68c00d50b28de89a475c18a0879be4a4482f68'
sha = lambda path: sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_bytes())

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == BASE
    assert not (STAGE/'RESULTS.md').exists() and not (STAGE/'NEXT_STEP_REVIEW.md').exists()
    protocol = read(STAGE/'protocol.json')
    helper, outer = read(STAGE/'run_001/execution_receipt.json'), read(STAGE/'hu_boundary_launch.json')
    auth, evidence = read(STAGE/'author/authorization.json'), read(STAGE/'author/direct_human_reply.json')
    assert auth['authorized'] and auth['approved_source_commit'] == BASE
    assert evidence['authorization_from_direct_human_reply'] and evidence['card'] == 'M-BOUND1'
    assert auth['human_evidence_sha256'] == sha(STAGE/'author/direct_human_reply.json')
    assert helper['status'] == outer['status'] == 'pass'
    assert outer['invocations'] == 1 and outer['exit_code'] == 0 and outer['stop_reason'] is None
    assert helper['calls'] == protocol['expected_calls'] and helper['counts'] == protocol['expected_counts']
    assert helper['protocol_sha256'] == outer['protocol_sha256'] == sha(STAGE/'protocol.json')
    assert helper['all_bindings_unchanged'] and outer['all_bindings_unchanged']
    assert set(path.name for path in (STAGE/'run_001').iterdir()) == set(protocol['expected_output_files'])
    assert set(helper['output_SHA256']) == set(protocol['expected_output_files'])-{'execution_receipt.json'}
    assert all(sha(STAGE/'run_001'/name) == pin for name,pin in helper['output_SHA256'].items())
    assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
    peers = {}
    for name in ('terminal_execution_review.json','physical_results_review.json','visual_review.json'):
        report = read(EXT/name)
        if name == 'physical_results_review.json':
            assert report['status'] == 'completed_actual_saved_result_interpretation_no_new_scientific_gate'
        else:
            assert report['status'].startswith('pass')
        assert not (STAGE/'author'/name).exists()
        (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
        peers[name] = sha(EXT/name)
    for source,target in (('RESULTS_draft.md','RESULTS.md'),('NEXT_STEP_REVIEW_draft.md','NEXT_STEP_REVIEW.md')):
        raw = (EXT/source).read_bytes()
        assert raw and b'\xef\xbf\xbd' not in raw
        (STAGE/target).write_bytes(raw)
    body = (EXT/'CURRENT_BODY_draft.md').read_text(encoding='utf-8')
    assert body.strip() and '\ufffd' not in body
    fronts = ['docs/CURRENT_STATUS.md','docs/RESUME_DEVELOPMENT.md',f'{REL}/README.md']
    history = []
    for name in fronts:
        path = ROOT/name
        old = path.read_bytes()
        urlbase = '../'+REL+'/' if name.startswith('docs/') else ''
        links = ('[实际结果]('+urlbase+'RESULTS.md) · [后续判断]('+urlbase+'NEXT_STEP_REVIEW.md) · '+
            '[端点作用图]('+urlbase+'run_001/Q1_Hu_endpoint_actions.png) · '+
            '[owner／节点对比]('+urlbase+'run_001/Hu_owner_node_comparison.png) · '+
            '[实际授权]('+urlbase+'author/authorization.json) · '+
            '[终态核对]('+urlbase+'author/terminal_execution_review.json) · '+
            '[物理解读]('+urlbase+'author/physical_results_review.json) · '+
            '[像素检查]('+urlbase+'author/visual_review.json)')
        prefix = ('# 当前接续：M-BOUND1保存Q1 Hu顶点作用实际执行已闭卡\n\n'+body+'\n'+links+
            '\n\n<details>\n<summary>更新前完整原文（历史状态不代表当前）</summary>\n\n').encode('utf-8')
        path.write_bytes(prefix+old+b'\n</details>\n')
        history.append(dict(path=name,old_bytes=len(old),old_sha256=sha256(old).hexdigest(),new_sha256=sha(path),
            history_start_byte=len(prefix),history_end_byte_exclusive=len(prefix)+len(old),old_body_preserved_exactly=True))
    scripts = ('record_authorization.py','review_terminal.py','close_docs.py','PHYSICAL_REVIEW_CHECKLIST.md')
    for name in scripts:
        assert not (STAGE/'author'/name).exists()
        (STAGE/'author'/name).write_bytes((EXT/name).read_bytes())
    assert all(sha(ROOT/name) == pin for name,pin in protocol['bindings'].items())
    receipt = dict(status='pass_actual_execution_documentation_closed',source_commit=BASE,front_history=history,
        peer_reports=peers,result_sha256=sha(STAGE/'RESULTS.md'),protocol_sha256=sha(STAGE/'protocol.json'),
        next_step_sha256=sha(STAGE/'NEXT_STEP_REVIEW.md'),bindings_checked=len(protocol['bindings']),
        authorization_sha256=sha(STAGE/'author/authorization.json'),execution_closed=True,
        actions=dict(results_written=1,next_step_written=1,fronts_updated=3,peer_records_archived=3,
            raw_author_scripts_archived=len(scripts),new_candidate_runs=0,new_NPZ_decodes=0,new_projection_fsum_integral_render=0),
        source_card_protocol_original_bytes_unchanged=True,entire_HF5_complete=False)
    with (STAGE/'author/documentation_receipt.json').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=receipt['status'],fronts=len(history),bindings_checked=len(protocol['bindings']))))

if __name__ == '__main__':
    main()
