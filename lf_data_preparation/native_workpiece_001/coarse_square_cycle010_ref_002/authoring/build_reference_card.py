"""Install/freeze a new saved-state reference card after the closed010 failure."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import shutil

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
MECH = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010'
CARD = MECH.with_name('coarse_square_cycle010_ref_002')
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
digest = lambda p:sha256(p.read_bytes()).hexdigest()
rel = lambda p:p.relative_to(ROOT).as_posix()


def write(p,value):
    with p.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')


def install():
    assert read(AUTHOR/'reference_card_readiness.json')['status'] == 'pass'
    original = read(MECH/'protocol.json'); pins = dict(original['bindings'])
    for n,v in pins.items():
        assert digest(ROOT/n) == v
    for name in ('protocol.json','execution_receipt.json','production_launch.json','reference_launch.json',
                 'reference/summary.json','reference/lifecycle.json','reference_stdout.log'):
        pins[rel(MECH/name)] = digest(MECH/name)
    production = read(MECH/'production_launch.json'); receipt = read(MECH/'execution_receipt.json')
    result = read(MECH/'result/result.json'); old = read(MECH/'reference/summary.json')
    assert production['status'] == receipt['status'] == 'pass' and production['exit_code'] == 0
    assert production['invocations'] == receipt['invocations'] == 1 and production['stop_reason'] is None
    assert production['all_bindings_unchanged'] and receipt['sources_unchanged'] and receipt['inputs_unchanged']
    assert result['status'] == 'success' and result['accepted_states'] == len(result['states']) == 12
    assert old['status'] == 'not_pass' and old['HP_calls_started'] == old['HP_calls_completed'] == 0
    assert read(MECH/'reference_launch.json')['status'] == 'not_pass'
    assert receipt['result_sha256'] == digest(MECH/'result/result.json')
    for p in (MECH/'result').rglob('*'):
        if p.is_file(): pins[rel(p)] = digest(p)
    for name in ('first_tangent_range_input','first_force_range_input'):
        for p in (MECH/name).iterdir():
            if p.is_file(): pins[rel(p)] = digest(p)
    assert not CARD.exists();CARD.mkdir();(CARD/'sources').mkdir();(CARD/'authoring').mkdir()
    for name in ('audit_cycle010_ref002.py','counter_contract.py','tests_counter_once.py','README.md'):
        shutil.copyfile(AUTHOR/name,CARD/name);pins[rel(CARD/name)] = digest(CARD/name)
        if name.endswith('.py'):
            compile((CARD/name).read_bytes(),str(CARD/name),'exec')
            shutil.copyfile(CARD/name,CARD/'sources'/name);pins[rel(CARD/'sources'/name)] = digest(CARD/name)
    for oldpath,newname in ((MECH/'core_audit_mechanical.py','core_audit_mechanical.py'),
                           (MECH/'launch_cycle010.py','launch_phase.py')):
        shutil.copyfile(oldpath,CARD/newname);pins[rel(CARD/newname)] = digest(oldpath)
        shutil.copyfile(oldpath,CARD/'sources'/newname);pins[rel(CARD/'sources'/newname)] = digest(oldpath)
    for p in AUTHOR.iterdir():
        if p.name not in ('audit_cycle010_ref002.py','counter_contract.py','tests_counter_once.py','README.md') and p.suffix in ('.py','.json','.md','.diff'):
            shutil.copyfile(p,CARD/'authoring'/p.name);pins[rel(CARD/'authoring'/p.name)] = digest(p)
    write(CARD/'tests_protocol.json',dict(schema_version='independent-cycle010-trace-test-card-1.0',bindings=pins,
        sampled_RSS_bytes=8*1024**3,phases=dict(tests=dict(helper_seconds=60,outer_seconds=90,argv=[rel(CARD/'tests_counter_once.py'),'--output',rel(CARD/'tests_001')])),
        scope='Once pure saved chronology and corruption rejection; no NumPy/FE/HP/API evaluation',
        stop_policy='First formal failure closes this new card; no retry/repair/force/extension'))
    print(json.dumps(dict(status='installed_not_tested',bindings=len(pins))))


def freeze():
    launch = read(CARD/'tests_launch.json'); tested = read(CARD/'tests_001/tests_receipt.json')
    assert launch['status'] == tested['status'] == 'pass' and launch['exit_code'] == 0 and launch['invocations'] == 1
    assert launch['stop_reason'] is None and launch['all_bindings_unchanged']
    pins = dict(read(CARD/'tests_protocol.json')['bindings'])
    for n,v in pins.items():
        assert digest(ROOT/n) == v
    for name in ('tests_protocol.json','tests_launch.json','tests_001/tests_receipt.json','tests_stdout.log'):
        pins[rel(CARD/name)] = digest(CARD/name)
    write(CARD/'protocol.json',dict(schema_version='independent-cycle010-accepted-reference-card-1.0',bindings=pins,
        sampled_RSS_bytes=8*1024**3,phases=dict(reference=dict(helper_seconds=300,outer_seconds=360,
            argv=[rel(CARD/'audit_cycle010_ref002.py'),'--input',rel(MECH),'--output',rel(CARD/'reference'),'--time-limit','300'])),
        actual_accepted_states=12,expected_HP80_120_calls=24,original_targets_mm=read(MECH/'result/result.json')['targets_mm'],
        production_rerun=False,original_production_inputs_and68sources_unchanged=True,
        scope='Same accepted states and original force/PORT-Jv/CSC/KKT/body gates; captured failedT/trial only file identity, no reevaluation/qualification',
        original_card='coarse_square_cycle_010 closed reference preflight with HP0; not extended or repaired',
        stop_policy='One fresh reference invocation; first formal failure closes this new card; no retry/repair/force/extension'))
    print(json.dumps(dict(status='frozen_not_audited',bindings=len(pins),expected_HP_calls=24,
                         protocol_sha256=digest(CARD/'protocol.json'))))


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode',choices=('install','freeze'))
install() if parser.parse_args().mode == 'install' else freeze()
