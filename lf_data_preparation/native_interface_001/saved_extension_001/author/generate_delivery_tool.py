"""Adapt the existing ordinary incremental publisher to an actual non-success closure."""
from pathlib import Path
import ast

HERE=Path(__file__).resolve().parent
old=(HERE.parent/'MALINK1_execution_review_001/deliver_execution.py').read_text(encoding='utf-8')
text=old.replace('1e639641625b4d0f92eb84aff4b4c6fdb05d0171','563febe92c1d04e5b1ea866f98c7d6c8b05e640d')
text=text.replace('alpha_link_001','saved_extension_001').replace('M-ALINK1','M-EXTEND1')
text=text.replace('source_publication_receipt.json','M_EXTEND1_source_publication_receipt.json')
text=text.replace("SUFFIXES = {'.json', '.py', '.md', '.log'}","SUFFIXES = {'.json', '.py', '.md', '.log', '.toml'}")
text=text.replace('== 21','== 52').replace('bindings_inherited_from_closed_sole_run=30','bindings_inherited_from_closed_sole_run=133')
text=text.replace("execution_status='pass'","execution_status='not_pass'")
text=text.replace('saved_alpha_linked_response_closed_001','saved_explicit_extension_not_pass_closed_001')
start=text.index('def check_execution(');end=text.index('\ndef main():',start)
check='''def check_execution(root, entries, old, config):
    stage=root/REL
    protocol=read(stage/'protocol.json');proof=read(stage/'author/M_EXTEND1_source_publication_receipt.json')
    auth_file,reply_file=stage/'author/authorization.json',stage/'author/direct_human_reply.json'
    auth,reply=read(auth_file),read(reply_file)
    assert protocol['card']==auth['card']==reply['card']==proof['prepared_card']=='M-EXTEND1'
    assert protocol['prepared'] is proof['prepared'] is True
    assert protocol['authorized'] is protocol['executed'] is proof['authorized'] is proof['executed'] is False
    assert proof['status']=='published_and_incrementally_restored_pass' and proof['published_commit']==BASE
    assert config['source_commit']==auth['approved_source_commit']==reply['approved_source_commit']==BASE
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['direct_human_answer']==reply['direct_human_answer']=='批准按 M-EXTEND1 卡执行' and reply['reply_context']
    assert auth['human_evidence_sha256']==sha(reply_file) and auth['source_publication_receipt_sha256']==sha(stage/'author/M_EXTEND1_source_publication_receipt.json')
    assert config['protocol_sha256']==proof['protocol_sha256']==auth['protocol_sha256']==sha(stage/'protocol.json')
    assert len(protocol['bindings'])==133 and config['execution_status']=='not_pass' and config['execution_closed'] is True
    assert all(entries[name]==old[name] and entries[name]['sha256']==pin for name,pin in protocol['bindings'].items())
    launch,helper=read(stage/'production_launch.json'),read(stage/'run_001/execution_receipt.json')
    assert launch['status']==helper['status']=='not_pass' and launch['invocations']==1 and launch['exit_code']==1
    assert launch['completed_utc'] and launch['stop_reason'] is None
    assert launch['all_bindings_unchanged'] is helper['all_bindings_unchanged'] is True
    assert launch['protocol_sha256']==helper['protocol_sha256']==config['protocol_sha256']
    assert 0<=launch['elapsed_seconds']<=launch['outer_seconds']==3060
    assert 0<=launch['helper_wall_seconds']<=launch['helper_seconds']==3000 and 0<=helper['elapsed_seconds']<=3000
    assert launch['peak_sampled_tree_RSS_bytes']<=launch['sampled_RSS_limit_bytes']==protocol['sampled_RSS_bytes']==8*1024**3
    assert helper['peak_sampled_RSS_bytes']<=8*1024**3
    assert len(helper['counts'])==24 and all(value==0 for value in helper['counts'].values())
    assert helper['accepted_states']==helper['HP_calls']==helper['JIT_calls']==0 and helper['installed_transitions']==[]
    assert helper['exception']['exception_class']=='FileNotFoundError'
    assert launch['installation_complete'] is helper['installation_complete'] is False
    for row in protocol['installation']:
        target=row['target'];assert entries[target]==old[target] and sha(root/target)==row['old_sha256']
        assert launch['actual_default_SHA256'][target]==helper['actual_default_SHA256'][target]==row['old_sha256']
    outputs=helper['outputs'];assert len(outputs)==66 and all(Path(name).suffix.lower() in ('.py','.toml') for name in outputs)
    run={path.relative_to(root).as_posix() for path in (stage/'run_001').rglob('*') if path.is_file()}
    assert run==outputs.keys()|{REL+'/run_001/execution_receipt.json'} and run<=config['closed_output_SHA256'].keys()
    assert all(entries[name]['sha256']==pin for name,pin in outputs.items())
    assert all(entries[name]['sha256']==pin for name,pin in config['closed_output_SHA256'].items())
    assert not any((stage/name).exists() for name in ('stop_requested.txt','run_001/test_results.xml','run_001/accepted_progress.jsonl','run_001/extended_alpha_half','run_001/view'))
    assert {row['path'] for row in config['front_history']}==FRONTS
    for row in config['front_history']:
        prior=git(root,'show',BASE+':'+row['path']);current=(root/row['path']).read_bytes()
        assert sha256(prior).hexdigest()==row['old_sha256'] and current.count(prior)==1
        assert current[row['history_start_byte']:row['history_end_byte_exclusive']]==prior
        assert entries[row['path']]['sha256']==row['new_sha256']
    for name in ('execution_terminal_scope_review.json','execution_input_path_review.json'):
        review=read(stage/'author'/name);assert review['execution_status']=='not_pass' and review['execution_closed'] is True
    final_name=config.get('final_review_path')
    if final_name:
        review=read(root/final_name)
        assert review['status'].startswith('pass') and review['config_sha256']==sha(stage/'author/execution_delivery_config.json')
        assert set(config['allowed_delta_paths'])-{final_name}<=review['reviewed_repository_SHA256'].keys()
        assert all(entries[name]['sha256']==pin for name,pin in review['reviewed_repository_SHA256'].items())

'''
text=text[:start]+check+text[end:]
ast.parse(text)
with (HERE/'deliver_execution.py').open('x',encoding='utf-8',newline='\n') as output:output.write(text)
