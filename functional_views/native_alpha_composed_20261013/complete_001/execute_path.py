"""Compose saved JSON observations and draw two curves in one approved window."""
from time import perf_counter
STARTED = perf_counter()
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import argparse
import json
import subprocess
import sys

CARD = 'M-PATH1'


def read(path):
    assert path.suffix == '.json'
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def digest(path, checkpoint):
    checkpoint()
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            checkpoint()
            digest.update(block)
    checkpoint()
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    repo, protocol_path = args.repo.resolve(), args.protocol.resolve()
    stage = Path(__file__).resolve().parent
    assert protocol_path.parent == stage and stage.is_relative_to(repo)
    protocol = read(protocol_path)
    assert protocol['card'] == CARD and protocol['schema_version'] == 'composed-saved-path-card-1.0'
    assert (protocol['helper_seconds'], protocol['outer_seconds'], protocol['sampled_RSS_bytes']) == (180,240,8*1024**3)
    run, stop = stage/'run_001', stage/'stop_requested.txt'
    assert not run.exists() and not stop.exists()
    auth, reply = read(stage/'author/authorization.json'), read(stage/'author/direct_human_reply.json')
    proof = read(stage/'author/source_publication_receipt.json')
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    assert auth['card'] == reply['card'] == proof['prepared_card'] == CARD
    assert auth['authorized'] is auth['authorization_from_direct_human_reply'] is reply['authorization_from_direct_human_reply'] is True
    assert auth['authorized_execution_source_commit'] == reply['authorized_execution_source_commit'] == proof['published_commit'] == head
    assert proof['status'] == 'published_and_incrementally_restored_pass' and proof['prepared'] is True
    assert proof['authorized'] is proof['executed'] is False
    assert proof['previous_delivery_commit'] == protocol['source_baseline_commit']
    assert auth['direct_human_answer'] == reply['direct_human_answer'] and reply['direct_human_answer'].strip() and reply['reply_context']
    assert sha256(protocol_path.read_bytes()).hexdigest() == auth['protocol_sha256'] == proof['protocol_sha256']
    assert sha256((stage/'author/direct_human_reply.json').read_bytes()).hexdigest() == auth['human_evidence_sha256']
    assert sha256((stage/'author/source_publication_receipt.json').read_bytes()).hexdigest() == auth['source_publication_receipt_sha256']
    run.mkdir()
    receipt = dict(schema_version='composed-saved-path-execution-1.0', card=CARD, status='running',
        authorized_execution_source_commit=head, protocol_sha256=auth['protocol_sha256'],
        started_utc=datetime.now(timezone.utc).isoformat(), compose_started=0,compose_completed=0,
        render_started=0,render_completed=0,outputs={}, HF_imports=0,F_T_HP_solver_tests=0,
        old_scientific_or_media_byte_reads=0,new_GIF_decode_or_generation=0,default_changes=0,
        pressure_clamp_stability_HF5_qualification=False)
    write(run/'started.json',receipt)
    peak, error = 0, None
    try:
        import psutil
        process = psutil.Process()
        def checkpoint():
            nonlocal peak
            memory = process.memory_info()
            peak = max(peak,memory.rss,getattr(memory,'peak_wset',memory.rss))
            if stop.exists():
                raise RuntimeError('external_stop_requested')
            if perf_counter()-STARTED > protocol['helper_seconds']:
                raise RuntimeError('whole_helper_elapsed_limit')
            if peak > protocol['sampled_RSS_bytes']:
                raise RuntimeError('sampled_RSS_limit')
        checkpoint()
        for name,pin in protocol['bindings'].items():
            path = repo/name
            assert path.suffix in ('.json','.py','.md','.toml')
            assert digest(path,checkpoint) == pin
        from compose_path import compose_path, build_index, markdown
        from render_path import render_path
        receipt['compose_started'] += 1
        data = compose_path(repo,protocol['path_spec'],checkpoint)
        receipt['compose_completed'] += 1
        checkpoint()
        write(run/'composed_path.json',data)
        write(run/'path_index.json',build_index(data))
        with (run/'OBSERVATIONS.md').open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(markdown(data))
        receipt['source_rows'] = len(data['raw_rows'])
        receipt['unique_states'] = len(data['unique_rows'])
        receipt['shared_anchors'] = len(data['anchor_join_ledger'])
        receipt['render_started'] += 1
        paths = render_path(data,run,checkpoint)
        receipt['render_completed'] += 1
        assert len(paths) == 2 and all(path.parent == run and path.suffix == '.png' for path in paths)
        checkpoint()
        for path in [run/'composed_path.json',run/'path_index.json',run/'OBSERVATIONS.md']+paths:
            name = path.relative_to(repo).as_posix()
            receipt['outputs'][name] = dict(bytes=path.stat().st_size,sha256=digest(path,checkpoint))
        receipt['status'] = 'pass'
        receipt['output_identity_seal'] = 'complete_inside_original_helper_window'
        checkpoint()
    except BaseException as exception:
        error = exception
        receipt.update(status='not_pass',error=dict(type=type(exception).__name__,message=str(exception)))
    receipt.update(elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=peak,
        completed_utc=datetime.now(timezone.utc).isoformat())
    if stop.exists() or receipt['elapsed_seconds'] > protocol['helper_seconds']:
        receipt.update(status='not_pass',resource_stop_reason='original_window_or_stop_closed')
    write(run/'execution_receipt.json',receipt)
    try:
        checkpoint()
    except BaseException as exception:
        error = error or exception
        receipt.update(status='not_pass',final_write_stop=dict(type=type(exception).__name__,message=str(exception)),
            elapsed_seconds=perf_counter()-STARTED,peak_sampled_RSS_bytes=peak)
        (run/'execution_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({key:receipt.get(key) for key in ('status','source_rows','unique_states','shared_anchors','elapsed_seconds','error')},ensure_ascii=False),flush=True)
    if error is not None:
        raise error
    if receipt['status'] != 'pass':
        raise RuntimeError('M-PATH1 closed non-success; no retry or extension')


if __name__ == '__main__':
    main()
