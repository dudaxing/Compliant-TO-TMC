"""One approved saved-array observation; no mechanics or default installation."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

ROOT = Path('D:/Coding/Diversity TO/Compliant-Nonlinear-TMC-O/.github_handoff/Compliant-TO-TMC')
STAGE = 'lf_data_preparation/native_interface_001/lf_circle_tip_local_001'


def main():
    started = time.monotonic()
    stage = ROOT / STAGE
    raw = (stage / 'protocol.json').read_bytes()
    protocol = json.loads(raw)
    deadline = started + protocol['helper_seconds']
    auth = json.loads((stage / 'author/authorization.json').read_bytes())
    assert auth['authorized'] and auth['one_invocation']
    assert auth['protocol_sha256'] == sha256(raw).hexdigest()
    assert protocol['card'] == auth['card'] == 'L-CTIPLOCAL1'
    output = ROOT / protocol['output_directory']
    output.mkdir(parents=True, exist_ok=False)
    receipt = dict(card=protocol['card'], status='running', phase='bindings_before',
        protocol_sha256=sha256(raw).hexdigest(), outputs={}, elapsed_seconds=0,
        call_counts=dict(observer_started=0, observer_completed=0),
        default_installations=0, new_tests=0, HP_calls_by_wrapper=0,
        mechanics_calls=dict(model=0, force=0, tangent=0, HP=0, Newton=0, equilibrium=0),
        error=None, output_identity_seal='not_complete')

    def clock():
        if time.monotonic() >= deadline:
            raise TimeoutError('Original helper180s window exhausted')

    def save():
        receipt['elapsed_seconds'] = time.monotonic() - started
        (output / 'execution_receipt.json').write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False)+'\n',
            encoding='utf-8', newline='\n')

    def bindings():
        for name, expected in {**protocol['source_bindings'], **protocol['input_bindings']}.items():
            clock()
            assert sha256((ROOT/name).read_bytes()).hexdigest() == expected, name

    save()
    try:
        bindings()
        receipt['phase'] = 'saved_array_observation'
        receipt['call_counts']['observer_started'] = 1
        save()
        sys.path.insert(0, str(stage))
        from observe_local import run
        observation = run(protocol, output, deadline)
        receipt['observation'] = observation
        receipt['outputs'] = observation['outputs']
        receipt['call_counts']['observer_completed'] = 1
        assert observation['status'] == 'pass'
        assert (observation['observed_states'], observation['archives'], observation['fields']) == (2, 5, 12)
        receipt['phase'] = 'bindings_after'
        save()
        bindings()
        clock()
        receipt.update(status='pass', phase='complete',
            output_identity_seal='complete_inside_original_helper_window')
        save()
        print(json.dumps(dict(status='pass', elapsed_seconds=receipt['elapsed_seconds'],
            archives=5, fields=12, outputs=len(receipt['outputs']))), flush=True)
    except BaseException as error:
        receipt.update(status='not_pass', error=dict(exception_class=type(error).__name__, reason=str(error)))
        save()
        # Preserve actual partial outputs only within this original window.
        if time.monotonic() < deadline:
            for name in ('tip_closeup.png', 'medium_locations.png', 'localization.json', 'manual.html'):
                path = output/name
                if path.is_file() and path.relative_to(ROOT).as_posix() not in receipt['outputs']:
                    clock()
                    payload = path.read_bytes()
                    receipt['outputs'][path.relative_to(ROOT).as_posix()] = dict(bytes=len(payload), sha256=sha256(payload).hexdigest())
            receipt['output_identity_seal'] = 'partial_inside_original_helper_window'
        save()
        raise


if __name__ == '__main__':
    main()
