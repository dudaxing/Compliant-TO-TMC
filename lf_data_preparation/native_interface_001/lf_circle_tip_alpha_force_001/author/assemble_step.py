"""Prepare the explicitly approved six-JSON force comparison without running it."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR=Path(__file__).resolve().parent
REL='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_force_001'
BASE='289450a8d27d915e1832beef9c75ca4fcc168232'
CARD='L-CTIPAFORCE1'
REQUEST='批准按 L-CTIPAFORCE1 整卡实施并执行'
read=lambda path:json.loads(path.read_bytes())
pin=lambda path:sha256(path.read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def main():
    git=lambda *a:subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a],cwd=ROOT,text=True).strip()
    assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists() and not (AUTHOR/'protocol.proposed.json').exists()
    inventory=read(AUTHOR/'input_inventory.json');schema=read(AUTHOR/'input_schema.json')
    plan=read(AUTHOR/'proposed_plan.json');review=read(AUTHOR/'PLAN_REVIEW.json')
    provenance=read(AUTHOR/'producer_provenance.json')
    assert inventory['card']==CARD and inventory['source_baseline_commit']==BASE
    assert len(inventory['ordinary_JSON_bindings'])==6 and len(inventory['cases'])==2 and len(schema)==6
    assert plan['fixed_input_contract']['matched_node_pairs']==565
    assert review['status'].startswith('pass') and not review['blockers']
    assert pin(AUTHOR/'proposed_plan.json')==review['proposed_plan_sha256']
    for name,expected in review['reviewed_preparation_sha256'].items():assert pin(AUTHOR/name)==expected,name
    names=('execute_step.py','launch_step.py','force_views.py')
    supports=('assemble_step.py','freeze_step.py','monitor_step.py','close_step.py',
        'publish_step.py','archive_publication.py','finalize_records.py')
    for name in names+supports:
        raw=(AUTHOR/name).read_bytes();ast.parse(raw)
        assert all(line.rstrip(b' \t')==line for line in raw.splitlines()),name
    for name,seal in inventory['ordinary_JSON_bindings'].items():
        raw=(ROOT/name).read_bytes()
        assert len(raw)==seal['bytes'] and sha256(raw).hexdigest()==seal['sha256'],name
    for item in inventory['existing_manuals']:
        assert (ROOT/item['path']).stat().st_size==item['bytes']
    sources={REL+'/'+name:pin(AUTHOR/name) for name in names}
    for name,expected in provenance['definition_source_bindings'].items():
        assert pin(ROOT/name)==expected,name
        sources[name]=expected
    cwd=AUTHOR/'execution_cwd';cwd.mkdir(exist_ok=False)
    protocol=dict(inventory,schema_version='lf-circle-tip-alpha-force-protocol-1.0',
        fixed_input_contract=plan['fixed_input_contract'],definition_source_bindings=provenance['definition_source_bindings'],
        output_directory=REL+'/run_001',working_directory=cwd.as_posix(),
        helper_seconds=180,outer_seconds=240,sampled_RSS_bytes=1024**3,cpu_thread_limit=16,
        cpu_thread_environment=dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16'),
        source_bindings=sources,expected_new_PNGs=2,
        approved_plan_sha256=pin(AUTHOR/'proposed_plan.json'),
        scope='Exactly6 pinned ordinary peak JSONs and2 original manual stat-links. All original objects/1130 node rows preserved;565 same-ID node pairs/3390 signed component differences,4 original group pairs/24 differences,6 whole-resultant differences. Original FORCE1 identity/finite/summary/distance rules, ordinary fsum/decomposition tail observations only without new tolerances. No science/CSV/gzip/media payload reads, HF import, new model/F/T/HP/equilibrium/tests/default/API changes or qualification upgrades.',
        display_scope='Exactly2PNG: twoalpha x three ON-body components, common all565-node maxnorm mapped2mm, fixedbody actualxy, minlength0; originaltotal holding text, no fabricated full mechanism. Signed Fx/Fy/raw groups in separate second figure. EachPNG root inspection at most once; no redraw.',
        approved_plan='lf_data_preparation/native_interface_001/lf_circle_tip_alpha_comparison_001/NEXT_STEPS.md',
        current_authorization='User explicitly approved the complete new AFORCE1 card after read-only plan review; old pending flags in preparation files are historical snapshots, not current authorization.',
        created_utc=datetime.now(timezone.utc).isoformat())
    protocol['status']='authorized_prepared_not_executed'
    write(AUTHOR/'protocol.proposed.json',protocol)
    auth=dict(card=CARD,approval_card=CARD,authorized=True,authorization_from_direct_human_request=True,
        one_invocation=True,authorized_execution_source_commit=BASE,protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        direct_human_request=REQUEST,approved_plan_sha256=protocol['approved_plan_sha256'],
        explicit_approved_scope='Implement minimal wrapper and source review, one six-JSON comparison,2 new force PNGs/once root QA, actual records and next decision, normal main publication/different-path localGit recovery plus receipt archive;180/240sec1GiB16cap and original first-error stop. No new science/tests/default/API.',
        approval_recorded_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'authorization.proposed.json',auth)
    receipt=dict(card=CARD,status='prepared_authorized_not_executed',created_utc=datetime.now(timezone.utc).isoformat(),
        source_baseline_commit=BASE,protocol_sha256=auth['protocol_sha256'],ordinary_JSONs=6,source_bindings=len(sources),
        manual_stat_links=2,old_media_content_reads=0,new_PNGs=2,scientific_payload_reads=0,
        scientific_calls=0,tests_run=0,default_HF_changes=0,formal_stage_created=False,git_mutations=0,
        historical_pending_plan_preserved=True)
    write(AUTHOR/'preparation_receipt.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':main()
