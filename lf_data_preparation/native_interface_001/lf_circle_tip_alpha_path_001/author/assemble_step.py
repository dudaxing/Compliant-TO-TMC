"""Prepare the explicitly approved ordinary path contract without executing it."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_path_001'
BASE='8faf1542d16688f179053ae879eb1253a18f5276'
CARD='L-CTIPAPATH1'
REQUEST='好的，按 L-CTIPAPATH1 计划实施并执行，复用 α=2.5e−7 的四段已有记录，汇总20态全周期响应与同位移对照，关联既有变形动画。保持原物理条件和验收门，注意做好记录和可视化，再根据结果安排后续工作。'
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()
METRICS=['R_input_N','q_out_mm','total_body_Fx_N','total_body_Fy_N',
    'material_body_Fx_N','material_body_Fy_N','regularization_body_Fx_N','regularization_body_Fy_N',
    'tip_to_raster_boundary_mm','minimum_boundary_distance_mm','solid_min_J','medium_min_J','medium_max_abs_Hu_per_mm']


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists() and not (AUTHOR/'protocol.proposed.json').exists()
    inventory=read(AUTHOR/'input_inventory.json');schema=read(AUTHOR/'input_schema.json')
    assert inventory['card']==CARD and inventory['source_baseline_commit']==BASE
    assert len(inventory['ordinary_JSON_bindings'])==9 and len(inventory['segments'])==4
    assert [s['segment'] for s in schema]==['ALPHA1','AUNLOAD1','AUNLOAD2','AUNLOAD3']
    fields=schema[0]['row_keys']
    assert len(fields)==37 and all(s['row_keys']==fields and s['row_key_variants']==1 for s in schema)
    assert [s['rows'] for s in schema]==[13,2,2,6]
    names=('execute_step.py','launch_step.py','path_views.py')
    supports=('assemble_step.py','freeze_step.py','monitor_step.py','close_step.py',
        'publish_step.py','archive_publication.py','finalize_records.py')
    for name in names+supports:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
    for name,seal in inventory['ordinary_JSON_bindings'].items():
        raw=(ROOT/name).read_bytes()
        assert len(raw)==seal['bytes'] and sha256(raw).hexdigest()==seal['sha256'],name
    for item in inventory['segments']:
        assert (ROOT/item['paths']['GIF']).stat().st_size==item['GIF_bytes']
        assert (ROOT/item['paths']['manual']).is_file()
    sources={REL+'/'+name:pin(AUTHOR/name) for name in names}
    supervisor='hf_repo/scripts/windows_owned_process_sup2.py';sources[supervisor]=pin(ROOT/supervisor)
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=dict(inventory,schema_version='lf-circle-tip-path-protocol-1.0',
        summary_row_fields=fields,same_input_metrics=METRICS,
        output_directory=REL+'/run_001',working_directory=cwd.as_posix(),
        helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=1024**3,cpu_thread_limit=16,
        cpu_thread_environment=dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16'),
        source_bindings=sources,expected_new_PNGs=2,expected_original_requested_targets=20,
        source_row_counts=[13,2,2,6],
        merge_scope='Preserve37 original summary fields; compare35 excluding index/leg at adjacent continuation anchors only. Exact anchors may share one display row; unequal anchors remain separate with original diagnostics, not a new scientific equality gate. No d-based deduplication.',
        same_input_scope='Only original requested unloading targets pair with original loading/origin targets at exactly equal d: seven pairs, thirteen existing definitions each. Preserve raw legs and source identities; zero reference remains origin. No interpolation, equality/zero-return/recovery/energy/stability criterion.',
        scope='Explicitly approved9 ordinaryJSON inputs and4 existingGIF stat links for alpha2.5e-7 four-segment observations. Exactly2 new scalarPNGs and manual entry; no mechanics/HF import, new scientific calls, tests, default changes, API associations or qualification upgrades.',
        approved_plan='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_unload_003/NEXT_STEPS.md',
        created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    auth=dict(card=CARD,approval_card=CARD,authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        direct_human_request=REQUEST,previously_published_plan=protocol['approved_plan'],
        approval_recorded_utc=datetime.now(timezone.utc).isoformat(),
        scope='One180sec helper/240sec outer1GiB16cap ordinary association and two scalar plots; fourGIF stat links, original physics/gates and qualifications preserved; records, normalmain publication and same-machine different-path localGit recovery plus receipt archive.')
    write(AUTHOR/'authorization.proposed.json',auth)
    receipt=dict(card=CARD,status='prepared_authorized_not_executed',created_utc=datetime.now(timezone.utc).isoformat(),
        source_baseline_commit=BASE,protocol_sha256=auth['protocol_sha256'],ordinary_JSONs=9,source_bindings=len(sources),
        GIF_stat_links=4,GIF_content_reads=0,new_PNGs=2,scientific_payload_reads=0,
        scientific_calls=0,tests_run=0,default_HF_changes=0,formal_stage_created=False,git_mutations=0)
    write(AUTHOR/'preparation_receipt.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':main()
