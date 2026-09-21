"""Read-only-source wrapper probe: every subprocess API is intercepted.

Only fresh fixture copies/log placeholders and this diagnostic JSON are
written. Reaching subprocess.run means a dry-run sentinel, never a solver
execution, returned success, completed receipt, or scientific admission.
"""
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "hf_repo"
HERE = Path(__file__).resolve().parent
WRAPPER = REPO / "scripts/run_contact_c2_isolated.py"
PROTOCOL = REPO / "configs/contact_c2_v3.json"
EXPECTED_PROTOCOL = "b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d"
EXPECTED_WRAPPER = "80ddbcdfedfbd9dbd22a9cf43a291f8f6f324a8366070adfbf3f82f921c7d82b"
EXPECTED_AUDITOR = "50bcbe18d67d62ea1bce621c9bfd2c1c6247dbe2b095a965dab42c00bc47e543"
SOURCE_BINDINGS = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(path, expected=None):
    path = Path(path).resolve()
    digest = sha(path)
    assert path.is_relative_to(ROOT)
    assert expected is None or expected == digest, str(path)
    SOURCE_BINDINGS[path.relative_to(ROOT).as_posix()] = digest
    return digest


def read(path):
    bind(path)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


class DryRunDispatchBoundary(BaseException):
    pass


class ProhibitedProcessCreation(BaseException):
    pass


def run_case(name, protocol, validate_protocol, unchanged_bytes=False):
    fixture = HERE / name
    assert not fixture.exists(), "preserve previous probe evidence"
    protocol_path = fixture / "hf_repo/configs/contact_c2_v3.json"
    protocol_path.parent.mkdir(parents=True)
    if unchanged_bytes:
        protocol_path.write_bytes(PROTOCOL.read_bytes())
    else:
        write_new(protocol_path, protocol)
    # This is a true byte copy, keeping the original relative admission path
    # resolvable. It is not a fabricated source or an execution authorization.
    admission_source = (PROTOCOL.parent / protocol["saved_field_admission"]["path"]).resolve()
    admission_target = (protocol_path.parent / protocol["saved_field_admission"]["path"]).resolve()
    assert admission_target.is_relative_to(fixture)
    admission_target.parent.mkdir(parents=True)
    admission_target.write_bytes(admission_source.read_bytes())
    assert sha(admission_target) == protocol["saved_field_admission"]["sha256"]
    try:
        validate_protocol(protocol)
        semantic = dict(status="accepted_by_frozen_validate_protocol", error=None)
    except (ValueError, KeyError, ArithmeticError) as error:
        semantic = dict(status="rejected_by_frozen_validate_protocol", error=str(error))
    run = fixture / "runs/padding_2p5"
    captured = []
    output, errors = io.StringIO(), io.StringIO()

    def dispatch_boundary(*args, **kwargs):
        command = args[0] if args else kwargs["args"]
        assert Path(command[2]).resolve() == REPO / "scripts/run_contact_c2.py"
        assert command[3:] == ["--output", str(run.resolve()), "--case", "padding_2p5",
                               "--protocol", str(protocol_path.resolve())]
        captured.append(dict(command=command, timeout=kwargs["timeout"], cwd=str(kwargs["cwd"]),
                             meaning="dryrun sentinel at dispatch boundary; command not executed"))
        raise DryRunDispatchBoundary()

    mocks = {}
    argv = [str(WRAPPER), "--action", "solve", "--run", str(run), "--case", "padding_2p5",
            "--protocol", str(protocol_path)]
    with ExitStack() as stack:
        for api in ("Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"):
            mocks[api] = stack.enter_context(patch.object(
                subprocess, api, side_effect=ProhibitedProcessCreation("prohibited subprocess API: " + api)))
        mocks["run"] = stack.enter_context(patch.object(subprocess, "run", side_effect=dispatch_boundary))
        stack.enter_context(patch.object(sys, "argv", argv))
        stack.enter_context(redirect_stdout(output))
        stack.enter_context(redirect_stderr(errors))
        try:
            runpy.run_path(str(WRAPPER), run_name="__main__")
            raise AssertionError("wrapper returned without a rejection or dryrun boundary")
        except DryRunDispatchBoundary:
            status, exit_code = "dryrun_dispatch_boundary_reached", None
        except SystemExit as error:
            status, exit_code = "rejected_before_dispatch", error.code
    counts = {api: mock.call_count for api, mock in mocks.items()}
    assert all(count == 0 for api, count in counts.items() if api != "run")
    assert not run.exists(), "a solver-created run must not exist"
    assert not list(fixture.rglob("*.receipt.json")), "no production receipt may be created"
    assert not list(fixture.rglob("*.npz")), "no state or model may be created"
    return dict(name=name, protocol_sha256=bind(protocol_path), solver_tolerance=protocol["solver"]["tolerance"],
                semantic_validation=semantic, wrapper_status=status, wrapper_exit_code=exit_code,
                intercepted_dispatches=captured, intercepted_api_counts=counts,
                stdout=output.getvalue(), stderr=errors.getvalue(),
                real_subprocesses_started=0, solver_called=False, hp_evaluated=False,
                run_directory_created=False, production_receipt_created=False,
                fixture_files=[dict(path=p.relative_to(HERE).as_posix(), sha256=sha(p), bytes=p.stat().st_size)
                               for p in sorted(fixture.rglob("*")) if p.is_file()])


def main():
    destination = HERE / "protocol_dispatch_probe.json"
    assert not destination.exists(), "preserve previous probe receipt"
    bind(WRAPPER, EXPECTED_WRAPPER)
    bind(PROTOCOL, EXPECTED_PROTOCOL)
    bind(REPO / "scripts/audit_contact_c2.py", EXPECTED_AUDITOR)
    bind(REPO / "scripts/run_contact_c2.py")
    bind(REPO / "scripts/hf4_common.py")
    original = read(PROTOCOL)
    gate = (PROTOCOL.parent / original["saved_field_admission"]["path"]).resolve()
    bind(gate, original["saved_field_admission"]["sha256"])
    bind(REPO / "configs/contact_c1_v1.json")
    for name, digest in original["implementation_sha256"].items():
        bind(REPO / name, digest)
    sys.path.insert(0, str(REPO / "scripts"))
    # Import only a pure readback module, under a process prohibition. The
    # function called below is a dictionary validator, never audit/audit_state.
    with ExitStack() as stack:
        for api in ("Popen", "run", "call", "check_call", "check_output", "getoutput", "getstatusoutput"):
            stack.enter_context(patch.object(subprocess, api, side_effect=ProhibitedProcessCreation(api)))
        from audit_contact_c2 import validate_protocol
    altered = deepcopy(original)
    altered["solver"]["tolerance"] = 1e-3
    restored = deepcopy(altered)
    restored["solver"]["tolerance"] = original["solver"]["tolerance"]
    assert restored == original, "counterexample must change exactly one semantic field"
    bad_implementation = deepcopy(original)
    bad_implementation["implementation_sha256"]["scripts/run_contact_c2.py"] = "0" * 64
    cases = [run_case("original_protocol_control", original, validate_protocol, True),
             run_case("relaxed_solver_counterexample", altered, validate_protocol),
             run_case("bad_implementation_rejection_control", bad_implementation, validate_protocol)]
    assert cases[0]["semantic_validation"]["status"] == "accepted_by_frozen_validate_protocol"
    assert cases[0]["wrapper_status"] == "dryrun_dispatch_boundary_reached"
    assert cases[1]["semantic_validation"]["status"] == "rejected_by_frozen_validate_protocol"
    assert cases[1]["wrapper_status"] == "dryrun_dispatch_boundary_reached"
    assert cases[2]["wrapper_status"] == "rejected_before_dispatch" and cases[2]["intercepted_api_counts"]["run"] == 0
    histories = []
    for case_id in original["run_sequence"]:
        run = ROOT / "hf4_c2_diagnostics/experiments" / case_id
        metadata = read(run / "metadata.json")
        completion = read(run / "completion.json")
        assert completion["metadata_sha256"] == sha(run / "metadata.json")
        assert metadata["protocol"] == original and metadata["protocol_sha256"] == EXPECTED_PROTOCOL
        assert metadata["source_sha256"]["scripts/run_contact_c2.py"] == sha(REPO / "scripts/run_contact_c2.py")
        receipts = {action: read(run.parent / f"{case_id}.{action}.receipt.json") for action in ("solve", "audit")}
        assert all(receipt["protocol_sha256"] == EXPECTED_PROTOCOL for receipt in receipts.values())
        audit = read(run / "audit.json")
        assert receipts["audit"]["audit_sha256"] == sha(run / "audit.json")
        histories.append(dict(case_id=case_id, protocol_sha256=metadata["protocol_sha256"],
                              solver_tolerance=metadata["protocol"]["solver"]["tolerance"],
                              audit_status=audit["status"], solve_returncode=receipts["solve"]["returncode"],
                              audit_returncode=receipts["audit"]["returncode"], evidence_scope="saved metadata, completion and external receipt hashes; no state reevaluation"))
    bind(__file__)
    assert all(sha(ROOT / name) == digest for name, digest in SOURCE_BINDINGS.items())
    write_new(destination, dict(schema="c2-protocol-predispatch-readonly-probe-v1",
        created_utc=datetime.now(timezone.utc).isoformat(), status="dryrun_finding_confirmed",
        no_FE=True, no_HP=True, real_subprocesses_started=0, cases=cases, original_path_evidence=histories,
        finding="Frozen wrapper can reach the subprocess dispatch boundary with solver.tolerance=1e-3 although the frozen semantic validator rejects it. This is a prospective pre-execution contract gap, not evidence of incorrect settings in the three archived paths.",
        scope_limit="The solver process is never imported or executed. Boundary interception is not a solve, audit pass, numerical observation, or proof that all downstream checks would admit the altered protocol.",
        minimum_future_repair="In a new version, validate the full physical/solver contract before directory/log creation and dispatch, retain all source/order/budget guards, bind the authorized protocol identity and validate at the direct runner entry too. Preserve the v3 original bytes and historical runs.",
        unchanged_physics=True, input_sha256=SOURCE_BINDINGS, script_sha256=sha(__file__)))
    print(json.dumps(dict(status="dryrun_finding_confirmed", real_subprocesses_started=0,
                         results=[dict(name=c["name"], validation=c["semantic_validation"]["status"],
                                       boundary=c["wrapper_status"]) for c in cases],
                         output=str(destination), sha256=sha(destination)), indent=2))


if __name__ == "__main__":
    main()
