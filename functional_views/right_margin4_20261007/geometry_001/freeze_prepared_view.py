"""Freeze one saved2mm/4mm layout plot after both actual preparations pass."""
from hashlib import sha256
from pathlib import Path
import argparse
import json
import shutil

AUTHOR = Path(__file__).resolve().parent
STAGE = 'functional_views/right_margin4_20261007/geometry_001'
PARENT = 'lf_data_preparation/native_workpiece_001/right_margin_preparation_001'
PREP = 'lf_data_preparation/native_workpiece_001/right_margin4_preparation_001'
LAUNCHER_SHA = 'f3a96681afc474e42ae19875579d748237235dce90f21892b016b3b3af862477'
RSS = 8*1024**3
sha = lambda p:sha256(p.read_bytes()).hexdigest()
read = lambda p:json.loads(p.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    root = parser.parse_args().repo.resolve()
    stage = root/STAGE
    assert not stage.exists(), 'One fresh view stage; no overwrite/retry'
    inputs = []
    for prep in (PARENT,PREP):
        base = root/prep
        protocol = read(base/'preparation_protocol.json')
        launch = read(base/'prepare_launch.json')
        receipt = read(base/'run_001/preparation_receipt.json')
        inventory = read(base/'run_001/input_inventory.json')
        metadata = read(base/'run_001/model/model.json')
        assert receipt['status'] == 'pass' and receipt['invocations'] == 1
        assert receipt['inputs_and_sources_unchanged'] and receipt['final_resource_check_passed']
        assert receipt['elapsed_seconds'] <= 120 and receipt['peak_sampled_helper_RSS_bytes'] <= RSS
        assert all(receipt[k] == 0 for k in ('force_calls','tangent_calls','solver_calls','HP_calls','JIT_calls','LF_imports'))
        assert launch['status'] == 'pass' and launch['exit_code'] == 0 and launch['invocations'] == 1
        assert launch['stop_reason'] is None and launch['all_bindings_unchanged']
        assert launch['elapsed_seconds'] <= 150 and launch['peak_sampled_tree_RSS_bytes'] <= RSS
        assert launch['protocol_sha256'] == sha(base/'preparation_protocol.json')
        assert launch['bindings'] == protocol['bindings']
        assert all(sha(root/p) == pin for p,pin in protocol['bindings'].items())
        assert all(sha(base/'run_001'/p) == pin for p,pin in receipt['outputs'].items())
        assert inventory['actual_counts'] == receipt['actual_counts'] == metadata['region_metadata']['counts']
        assert metadata['arrays']['sha256'] == receipt['model_sha256'] == sha(base/'run_001/model/model.npz')
        inputs += [prep+'/'+p for p in ('preparation_protocol.json','prepare_launch.json',
            'run_001/preparation_receipt.json','run_001/input_inventory.json','run_001/model/model.json','run_001/model/model.npz')]
    review = read(AUTHOR/'prepared_view_static_review.json')
    assert review['status'] == 'pass_static_only'
    assert sha(AUTHOR/'launch_pose.py') == LAUNCHER_SHA
    notes = read(AUTHOR/'author_note.json')
    assert all(sha(AUTHOR/name) == pin for name,pin in notes['candidate_sources'].items())
    selected = [AUTHOR/name for name in ('plot_prepared_domain.py','freeze_prepared_view.py',
        'launch_pose.py','README.md','author_note.json','author_checks.json','source_delta.diff',
        'prepared_view_static_review.json')]
    if (AUTHOR/'prepared_view_static_review.md').exists():selected.append(AUTHOR/'prepared_view_static_review.md')
    stage.mkdir(parents=True)
    for src in selected:
        shutil.copyfile(src,stage/src.name)
        assert sha(src) == sha(stage/src.name)
    cases = [dict(role='Parent prepared',expected_width_mm=82.,model_json=PARENT+'/run_001/model/model.json',model_file=PARENT+'/run_001/model/model.npz'),
        dict(role='New prepared',expected_width_mm=84.,model_json=PREP+'/run_001/model/model.json',model_file=PREP+'/run_001/model/model.npz')]
    bindings = {p:sha(root/p) for p in inputs}
    bindings.update({p.relative_to(root).as_posix():sha(p) for p in stage.iterdir() if p.is_file()})
    protocol = dict(schema_version='right-margin-prepared-view-card-1.0',bindings=bindings,cases=cases,sampled_RSS_bytes=RSS,
        phases=dict(view=dict(helper_seconds=60,outer_seconds=90,argv=[STAGE+'/plot_prepared_domain.py','--repo','.','--protocol',STAGE+'/protocol.json'])),
        scope='Two actual saved undeformed prepared models, one layout PNG; only actual82to84 added strip highlighted. No HF observations/response/constructor/HP',
        stop_policy='One invocation, first error stops, no retry or force; preparation status conveys no response qualification')
    with (stage/'protocol.json').open('x',encoding='utf-8') as handle:
        json.dump(protocol,handle,indent=2,ensure_ascii=False,allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status='frozen_not_run',protocol_sha256=sha(stage/'protocol.json'))))


if __name__ == '__main__':main()
