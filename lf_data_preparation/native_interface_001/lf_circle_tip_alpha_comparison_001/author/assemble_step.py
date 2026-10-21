"""Prepare the approved two-summary comparison without executing the candidate."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_comparison_001'
BASE='08d07caf6cbb1e6ebe1af6f35c8dc1b8c9d0d669'
CARD='L-CTIPACOMP1'
REQUEST='好的，按 L-CTIPACOMP1 计划实施并执行，复用 α=5e−7 和 α=2.5e−7 的两份已有汇总，对照20个原目标的反力、材料／Hu力分量、变形和介质响应。保持原物理定义和验收门，注意做好记录和可视化，再根据结果安排后续工作。'
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
    assert len(inventory['ordinary_JSON_bindings'])==len(inventory['cases'])==len(schema)==2
    fields=schema[0]['timeline_row_keys'][:37]
    assert len(fields)==37 and all(s['timeline_row_keys'][:37]==fields and s['timeline_row_key_variants']==1 for s in schema)
    assert [s['counts']['raw_rows'] for s in schema]==[33,23]
    assert all(s['original_requested_targets']==20 for s in schema)
    names=('execute_step.py','launch_step.py','comparison_views.py')
    supports=('assemble_step.py','freeze_step.py','monitor_step.py','close_step.py',
        'publish_step.py','archive_publication.py','finalize_records.py')
    for name in names+supports:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
    for name,seal in inventory['ordinary_JSON_bindings'].items():
        raw=(ROOT/name).read_bytes()
        assert len(raw)==seal['bytes'] and sha256(raw).hexdigest()==seal['sha256'],name
    for item in inventory['cases']:
        assert (ROOT/item['manual_path']).stat().st_size==item['manual_bytes']
    sources={REL+'/'+name:pin(AUTHOR/name) for name in names}
    supervisor='hf_repo/scripts/windows_owned_process_sup2.py';sources[supervisor]=pin(ROOT/supervisor)
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    comparison_sources={key:{k:case[k] for k in ('path','manual_path','manual_bytes')} for key,case in zip(('baseline','new'),inventory['cases'])}
    protocol=dict(inventory,schema_version='lf-circle-tip-alpha-comparison-protocol-1.0',
        comparison_sources=comparison_sources,summary_row_fields=fields,same_input_metrics=METRICS,
        output_directory=REL+'/run_001',working_directory=cwd.as_posix(),
        helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=1024**3,cpu_thread_limit=16,
        cpu_thread_environment=dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16'),
        source_bindings=sources,expected_new_PNGs=2,expected_original_requested_targets=20,
        expected_original_raw_rows=[33,23],expected_raw_value_rows=40,expected_pairs=20,expected_differences=260,
        match_scope='Only convergence.is_original_target rows; exact (convergence.original_target_index, display_branch, d_mm). Preserve all original37 observation fields, raw legs, sourceSHA, embedded raw diagnostics, segments, exceptions and provenance. No cross-alpha deduplication, interpolation or normalization.',
        comparison_scope='Thirteen existing metrics, new alpha2.5e-7 minus baseline5e-7; preserve old23/new13 within-alpha definitions in originals. Allow task differences only regularization.alpha and task_id/purpose/parameter_origin/description; incompatible bindings are explicit noncomparability, never normalized. No new equality, recovery, energy or physical acceptance gate.',
        scope='Exactly2 bound ordinaryJSON inputs and2 original manual page stat-links. Exactly2 new scalarPNGs and manual entry; no scientific payload or media content reads, mechanics/HF import, tests, new scientific calls, default changes, API association or qualification upgrade. Preserve only diagnostics already embedded in these two sources; complete Newton histories remain through original manual links.',
        cost_limit='Old14 segments versus new4: counts/clocks are original work context, not pure-alpha performance. Equal initial stateSHA does not merge tasks or transfer independent references. No new deformation media.',
        approved_plan='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_path_001/NEXT_STEPS.md',
        created_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'protocol.proposed.json',protocol)
    auth=dict(card=CARD,approval_card=CARD,authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        direct_human_request=REQUEST,previously_published_plan=protocol['approved_plan'],
        approval_recorded_utc=datetime.now(timezone.utc).isoformat(),
        scope='One180sec helper/240sec outer1GiB16cap two-summary comparison and two scalar plots; two old manual stat-links only, original physics/gates and qualifications preserved; records, normalmain publication and same-machine different-path localGit recovery plus receipt archive.')
    write(AUTHOR/'authorization.proposed.json',auth)
    receipt=dict(card=CARD,status='prepared_authorized_not_executed',created_utc=datetime.now(timezone.utc).isoformat(),
        source_baseline_commit=BASE,protocol_sha256=auth['protocol_sha256'],ordinary_JSONs=2,source_bindings=len(sources),
        manual_stat_links=2,old_media_content_reads=0,new_PNGs=2,scientific_payload_reads=0,
        scientific_calls=0,tests_run=0,default_HF_changes=0,formal_stage_created=False,git_mutations=0)
    write(AUTHOR/'preparation_receipt.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':main()
