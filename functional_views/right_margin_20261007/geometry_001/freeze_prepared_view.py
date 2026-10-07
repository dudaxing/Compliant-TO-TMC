"""Freeze one saved-model layout plot after the actual preparation passes."""
from hashlib import sha256
from pathlib import Path
import json
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
STAGE = 'functional_views/right_margin_20261007/geometry_001'
PREP = 'lf_data_preparation/native_workpiece_001/right_margin_preparation_001'
OLD = 'lf_data_preparation/native_workpiece_001/enlarged_square_projection_001'
sha = lambda p:sha256(p.read_bytes()).hexdigest()
read = lambda p:json.loads(p.read_text(encoding='utf-8'))


def main():
    assert read(ROOT/PREP/'run_001/preparation_receipt.json')['status'] == 'pass'
    assert read(ROOT/PREP/'prepare_launch.json')['status'] == 'pass'
    assert read(AUTHOR/'prepared_view_static_review.json')['status'] == 'pass_static_only'
    helper = AUTHOR/'plot_prepared_domain.py'
    assert sha(helper) == 'bf084687184de46339aafff5f514e29ea78f4f9123db3fe39424a03a4e006b89'
    stage = ROOT/STAGE
    assert not stage.exists()
    stage.mkdir(parents=True)
    for src in [helper,Path(__file__).resolve(),AUTHOR/'prepared_view_static_review.json',AUTHOR/'prepared_view_static_review.md']:
        shutil.copyfile(src,stage/src.name)
    shutil.copyfile(ROOT/PREP/'launch_pose.py',stage/'launch_pose.py')
    cases = [dict(label='Original domain x=80 | right margin 0 mm',width_mm=80.,model_file=OLD+'/run_001/result/model/model.npz'),
        dict(label='Derived domain x=82 | right margin 2 mm',width_mm=82.,model_file=PREP+'/run_001/model/model.npz')]
    inputs = [PREP+'/'+p for p in ('preparation_protocol.json','prepare_launch.json','run_001/preparation_receipt.json','run_001/input_inventory.json')]
    inputs += [row['model_file'] for row in cases]
    bindings = {p:sha(ROOT/p) for p in inputs}
    bindings.update({p.relative_to(ROOT).as_posix():sha(p) for p in stage.iterdir() if p.is_file()})
    protocol = dict(schema_version='right-margin-prepared-view-card-1.0',bindings=bindings,cases=cases,sampled_RSS_bytes=8*1024**3,
        phases=dict(view=dict(helper_seconds=60,outer_seconds=90,argv=[STAGE+'/plot_prepared_domain.py','--repo','.','--protocol',STAGE+'/protocol.json'])),
        scope='Two actual saved undeformed models, one layout PNG; no HF observations/response/constructor/HP',
        stop_policy='One invocation, first error stops, no retry or force; preparation status conveys no response qualification')
    (stage/'protocol.json').write_text(json.dumps(protocol,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='frozen_not_run',protocol_sha256=sha(stage/'protocol.json'))))


if __name__ == '__main__':main()
