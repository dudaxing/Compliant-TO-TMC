"""Prepare the approved saved-report reader; do not execute it."""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
REL = 'lf_data_preparation/native_interface_001/lf_circle_tip_alpha_report_001'
BASE = '035eaef93324d2bdb4767e5b6c0b5850e51cd766'
CARD = 'L-CTIPAREPORT1'
REQUEST = '批准按 L-CTIPAREPORT1 整卡实施并执行'
read = lambda path: json.loads(path.read_bytes())
pin = lambda path: sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def main():
    git = lambda *a: subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false',*a], cwd=ROOT, text=True).strip()
    assert git('rev-parse','HEAD') == BASE and not git('status','--porcelain')
    assert not (ROOT/REL).exists() and not (AUTHOR/'protocol.proposed.json').exists()
    inventory = read(AUTHOR/'input_inventory.json')
    schema = read(AUTHOR/'input_schema.json')
    plan = read(AUTHOR/'proposed_plan.json')
    review = read(AUTHOR/'PLAN_REVIEW.json')
    assert inventory['card'] == CARD and inventory['source_baseline_commit'] == BASE
    assert len(inventory['ordinary_JSON_bindings']) == 2 and len(inventory['existing_links']) == 12
    assert review['status'].startswith('pass') and not review['blockers']
    assert pin(AUTHOR/'proposed_plan.json') == review['proposed_plan_sha256']
    for name, expected in review['reviewed_preparation_sha256'].items():
        assert pin(AUTHOR/name) == expected, name
    names = ('execute_step.py','launch_step.py','saved_study_report.py')
    supports = ('assemble_step.py','freeze_step.py','monitor_step.py','close_step.py',
                'publish_step.py','archive_publication.py','finalize_records.py')
    for name in names+supports:
        raw = (AUTHOR/name).read_bytes()
        ast.parse(raw)
        assert all(line.rstrip(b' \t') == line for line in raw.splitlines()), name
    for name, seal in inventory['ordinary_JSON_bindings'].items():
        raw = (ROOT/name).read_bytes()
        assert len(raw) == seal['bytes'] and sha256(raw).hexdigest() == seal['sha256'], name
    for item in inventory['existing_links']:
        assert (ROOT/item['path']).stat().st_size == item['bytes'], item['path']
    sources = {REL+'/'+name:pin(AUTHOR/name) for name in names}
    for name, expected in plan['source_definition_bindings'].items():
        assert pin(ROOT/name) == expected, name
        sources[name] = expected
    cwd = AUTHOR/'execution_cwd'
    cwd.mkdir(exist_ok=False)
    protocol = dict(inventory, schema_version='lf-saved-study-report-protocol-1.0',
        input_schema=schema, associated_peak_identities=plan['associated_peak_identities'],
        source_definition_bindings=plan['source_definition_bindings'], source_bindings=sources,
        output_directory=REL+'/run_001', working_directory=cwd.as_posix(),
        helper_seconds=180, outer_seconds=240, sampled_RSS_bytes=1024**3, cpu_thread_limit=16,
        cpu_thread_environment=dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'),'16'),
        approved_plan_sha256=pin(AUTHOR/'proposed_plan.json'),
        scope=plan['business_io'], outputs=plan['outputs'], expected_new_PNGs=0,
        new_tests=0, new_scientific_calls=0, media_content_reads=0,
        current_authorization='Direct whole-card human approval received. Pending flags in the preserved preparation files describe their historical preparation time, not current authorization.',
        created_utc=datetime.now(timezone.utc).isoformat())
    protocol['status'] = 'authorized_prepared_not_executed'
    write(AUTHOR/'protocol.proposed.json', protocol)
    auth = dict(card=CARD, approval_card=CARD, authorized=True,
        authorization_from_direct_human_request=True, one_invocation=True,
        authorized_execution_source_commit=BASE, protocol_sha256=pin(AUTHOR/'protocol.proposed.json'),
        direct_human_request=REQUEST, approved_plan_sha256=protocol['approved_plan_sha256'],
        explicit_approved_scope='Implement pure-stdlib research reader and CLI, finite source review, one two-JSON/twelve-stat CLI, actual records, normal main publication and different-path local-Git restore with receipt archive. helper180/outer240 seconds, sampled1GiB, four-library16 caps. First terminal error stops; no retry/repair rerun/extension/force/rollback/delete, new science/tests/media reads/plots/default HF changes or qualification upgrades.',
        approval_recorded_utc=datetime.now(timezone.utc).isoformat())
    write(AUTHOR/'authorization.proposed.json', auth)
    receipt = dict(card=CARD, status='prepared_authorized_not_executed',
        created_utc=datetime.now(timezone.utc).isoformat(), source_baseline_commit=BASE,
        protocol_sha256=auth['protocol_sha256'], ordinary_JSONs=2, source_bindings=len(sources),
        old_artifact_stat_links=12, old_media_content_reads=0, new_PNGs=0,
        scientific_calls=0, tests_run=0, default_HF_changes=0,
        formal_stage_created=False, git_mutations=0, historical_pending_plan_preserved=True)
    write(AUTHOR/'preparation_receipt.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
