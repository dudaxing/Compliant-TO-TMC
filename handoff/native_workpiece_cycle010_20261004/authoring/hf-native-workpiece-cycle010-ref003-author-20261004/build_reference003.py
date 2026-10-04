"""Freeze a fresh24-HP card using measured Ref002 cost; no production rerun."""
from pathlib import Path
from hashlib import sha256
import json
import shutil
import difflib

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
AUTHOR = Path(__file__).resolve().parent
MECH = ROOT/'lf_data_preparation/native_workpiece_001/coarse_square_cycle_010'
OLD = MECH.with_name('coarse_square_cycle010_ref_002')
CARD = MECH.with_name('coarse_square_cycle010_ref_003')
read = lambda p:json.loads(p.read_text(encoding='utf-8'))
digest = lambda p:sha256(p.read_bytes()).hexdigest()
rel = lambda p:p.relative_to(ROOT).as_posix()


def write(p,value):
    with p.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')


def candidate():
    raw = (OLD/'audit_cycle010_ref002.py').read_bytes(); new = raw
    edits = [(b'default=300.',b'default=600.'),
             (b'reference_seconds=300,',b'reference_seconds=600,'),
             (b'reference_outer_seconds=360,',b'reference_outer_seconds=660,'),
             (b'declared 300 seconds',b'declared 600 seconds'),
             (b'and inventory["execution_limits"] == LIMITS,',
              b'and inventory["execution_limits"] == dict(LIMITS,reference_seconds=300,reference_outer_seconds=360),')]
    for a,b in edits:
        assert new.count(a) == 1;new = new.replace(a,b)
    restored = new
    for a,b in reversed(edits):
        assert restored.count(b) == 1;restored = restored.replace(b,a)
    assert restored == raw
    compile(new,'audit_cycle010_ref003.py','exec')
    (AUTHOR/'audit_cycle010_ref003.py').open('xb').write(new)
    (AUTHOR/'budget_only.diff').open('xb').write(''.join(difflib.unified_diff(raw.decode().splitlines(True),new.decode().splitlines(True),fromfile='Ref002',tofile='Ref003')).encode())
    for name in ('counter_contract.py','core_audit_mechanical.py','launch_phase.py'):
        shutil.copyfile(OLD/name,AUTHOR/name)
    write(AUTHOR/'candidate.json',dict(status='authored_not_executed',inverse_bytes_exact=True,
        original_sha256=sha256(raw).hexdigest(),candidate_sha256=sha256(new).hexdigest(),
        substitutions=len(edits),scope='Four reference resource literals300/360->600/660 plus explicit unchanged production inventory reference300/360 role; no math/gates/chronology/production changes'))
    print('Authored budget-only candidate; zero modules evaluated')


def install():
    assert read(AUTHOR/'readiness.json')['status'] == 'pass'
    terminal = read(OLD/'reference_launch.json'); failed = read(OLD/'reference/summary.json')
    assert terminal['status'] == 'not_pass' and terminal['exit_code'] == 1 and terminal['invocations'] == 1
    assert terminal['stop_reason'] is None and terminal['all_bindings_unchanged']
    assert failed['status'] == 'not_pass' and failed['error'] == "ValueError('Eleven-target cycle reference time limit exceeded')"
    assert failed['accepted_states'] == 7 and failed['HP_calls_started'] == failed['HP_calls_completed'] == 16
    assert read(OLD/'tests_001/tests_receipt.json')['status'] == 'pass'
    assert read(OLD/'tests_001/tests_receipt.json')['tests_passed'] == 12
    pins = dict(read(OLD/'protocol.json')['bindings'])
    for n,v in pins.items():assert digest(ROOT/n) == v
    pins[rel(OLD/'protocol.json')] = digest(OLD/'protocol.json')
    for p in OLD.rglob('*'):
        if p.is_file():
            pins[rel(p)] = digest(p)
    assert not CARD.exists();CARD.mkdir();(CARD/'sources').mkdir();(CARD/'authoring').mkdir()
    for name in ('audit_cycle010_ref003.py','counter_contract.py','core_audit_mechanical.py','launch_phase.py','README.md'):
        shutil.copyfile(AUTHOR/name,CARD/name);pins[rel(CARD/name)] = digest(CARD/name)
        if name.endswith('.py'):
            shutil.copyfile(CARD/name,CARD/'sources'/name);pins[rel(CARD/'sources'/name)] = digest(CARD/name)
    for p in AUTHOR.iterdir():
        if p.name not in ('audit_cycle010_ref003.py','counter_contract.py','core_audit_mechanical.py','launch_phase.py','README.md'):
            shutil.copyfile(p,CARD/'authoring'/p.name);pins[rel(CARD/'authoring'/p.name)] = digest(p)
    write(CARD/'protocol.json',dict(schema_version='independent-cycle010-reference003-cost-card-1.0',bindings=pins,
        sampled_RSS_bytes=8*1024**3,phases=dict(reference=dict(helper_seconds=600,outer_seconds=660,
            argv=[rel(CARD/'audit_cycle010_ref003.py'),'--input',rel(MECH),'--output',rel(CARD/'reference'),'--time-limit','600'])),
        actual_accepted_states=12,expected_new_HP80_120_calls=24,production_rerun=False,
        cost_basis='Ref002301.4867s/16HP including interrupted state8: proportional24/16=452.2301s, estimate only',
        original_refs='010 preflightHP0 and Ref002time_limit16HP/7recorded states remain closed; no prefix qualification拼接',
        scope='Same12 accepted arrays, originalmath/gates, one new full fresh reference; failedT/trial file identity only',
        stop_policy='One invocation, first formal error closes this new card; no retry/repair/force/window extension'))
    print(json.dumps(dict(status='prepared_not_executed',bindings=len(pins),helper_seconds=600,outer_seconds=660,
        expected_HP_calls=24,protocol_sha256=digest(CARD/'protocol.json'))))


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('candidate','install'))
    candidate() if parser.parse_args().mode == 'candidate' else install()
