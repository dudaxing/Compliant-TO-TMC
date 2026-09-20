"""Bounded provenance/readback tests: no FE or high-precision state evaluation."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import audit_contact_c2 as frozen
import audit_contact_c2_readback as readback
import run_contact_c2_isolated as isolated


def ordinary_manifest(root):
    manifest = dict(readback.EXTERNAL_HISTORICAL_SOURCES)
    for index in range(164):
        name = f"ordinary/{index:03d}.txt"
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"retained numerical evidence {index}".encode())
        manifest[name] = frozen.sha(path)
    return manifest


def test_exact_two_absent_sources_never_enter_verified_bindings(tmp_path):
    manifest, bindings = ordinary_manifest(tmp_path), {}
    records = readback.bind_historical_admission(tmp_path, manifest, bindings)
    assert len(bindings) == 164
    assert readback.historical_status(records) == "not_reverified_external_source"
    assert {r["path"] for r in records} == set(readback.EXTERNAL_HISTORICAL_SOURCES)
    for row in records:
        assert row["status"] == "not_reverified_external_source"
        assert row["actual_sha256"] is None
        assert str((tmp_path / row["path"]).resolve()) not in bindings


def test_present_historical_sources_are_verified_when_available(tmp_path):
    """A public checkout intentionally need not contain private source bytes."""
    paths = [REPO.parent / name for name in readback.EXTERNAL_HISTORICAL_SOURCES]
    if not all(p.is_file() for p in paths):
        pytest.skip("external historical source bytes are intentionally optional")
    manifest, bindings = ordinary_manifest(tmp_path), {}
    for source in paths:
        target = tmp_path / source.relative_to(REPO.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    records = readback.bind_historical_admission(tmp_path, manifest, bindings)
    assert len(bindings) == 166
    assert readback.historical_status(records) == "verified"
    assert all(r["status"] == "verified" and r["actual_sha256"] == r["expected_sha256"] for r in records)


@pytest.mark.parametrize("mutation", ["changed_expected_hash", "renamed_exception", "extra_entry",
                                      "missing_ordinary", "changed_ordinary", "present_corrupt_external",
                                      "invalid_hash", "path_traversal", "polluted_absent_binding",
                                      "conflicting_present_binding"])
def test_no_other_missing_changed_or_polluted_evidence_is_accepted(tmp_path, mutation):
    manifest, bindings = ordinary_manifest(tmp_path), {}
    historical = next(iter(readback.EXTERNAL_HISTORICAL_SOURCES))
    ordinary = "ordinary/000.txt"
    if mutation == "changed_expected_hash":
        manifest[historical] = "0" * 64
    elif mutation == "renamed_exception":
        manifest["./" + historical] = manifest.pop(historical)
    elif mutation == "extra_entry":
        manifest["third_external_source.txt"] = "0" * 64
    elif mutation == "missing_ordinary":
        (tmp_path / ordinary).unlink()
    elif mutation == "changed_ordinary":
        (tmp_path / ordinary).write_bytes(b"tampered")
    elif mutation == "present_corrupt_external":
        target = tmp_path / historical
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"not the historical MATLAB source")
    elif mutation == "invalid_hash":
        manifest[ordinary] = "invalid"
    elif mutation == "path_traversal":
        manifest["../outside.txt"] = manifest.pop(ordinary)
    elif mutation == "polluted_absent_binding":
        bindings[str((tmp_path / historical).resolve())] = manifest[historical]
    elif mutation == "conflicting_present_binding":
        bindings[str((tmp_path / ordinary).resolve())] = "0" * 64
    with pytest.raises((ValueError, OSError)):
        readback.bind_historical_admission(tmp_path, manifest, bindings)


def replace_once(source, before, after):
    assert source.count(before) == 1, "frozen source/approved edit changed"
    return source.replace(before, after, 1)


def test_load_run_ast_has_only_the_declared_provenance_differences():
    source = inspect.getsource(frozen.load_run)
    source = replace_once(source, '    protocol = read_json(protocol_path)',
        '    bind(REPO/"scripts/audit_contact_c2.py", bindings, FROZEN_AUDITOR_SHA256)\n'
        '    bind(protocol_path, bindings, PROTOCOL_SHA256)\n'
        '    protocol = read_json(protocol_path)')
    source = replace_once(source,
        '    if "input_sha256_from_workspace_root" in admission:\n'
        '        bind_manifest(REPO.parent, admission["input_sha256_from_workspace_root"], bindings,\n'
        '                      "saved-field admission input manifest")',
        '    historical_sources = bind_historical_admission(\n'
        '        REPO.parent, admission["input_sha256_from_workspace_root"], bindings)')
    source = replace_once(source, '                entries=index["steps"], paths=paths)',
        '                entries=index["steps"], paths=paths, historical_sources=historical_sources)')
    assert ast.dump(ast.parse(source), include_attributes=False) == ast.dump(
        ast.parse(inspect.getsource(readback.load_run)), include_attributes=False)


def test_audit_ast_preserves_arithmetic_thresholds_inventory_and_prefix():
    source = inspect.getsource(frozen.audit)
    source = replace_once(source, '    require(not output.exists(), "audit output already exists")',
        '    require(not output.exists(), "audit output already exists")\n'
        '    require(output.name != "audit.json", "numerical readback must use a distinct output name")')
    source = replace_once(source, '    data = load_run(run, protocol_path, bindings)',
        '    data = load_run(run, protocol_path, bindings)\n    bind(Path(__file__), bindings)')
    source = replace_once(source,
        'result = dict(schema_version="contact-c2-independent-audit-1.0", status="pass" if passed else "not_pass",',
        'result = dict(schema_version=SCHEMA_VERSION, status="numerical_pass" if passed else "numerical_not_pass",\n'
        '        numerical_status="pass" if passed else "not_pass", valid_for_execution_admission=False,\n'
        '        historical_source_status=historical_status(data["historical_sources"]),\n'
        '        historical_sources=data["historical_sources"], historical_source_scope=HISTORICAL_SOURCE_SCOPE,\n'
        '        frozen_auditor_sha256=FROZEN_AUDITOR_SHA256, physical_protocol_sha256=PROTOCOL_SHA256,')
    assert ast.dump(ast.parse(source), include_attributes=False) == ast.dump(
        ast.parse(inspect.getsource(readback.audit)), include_attributes=False)
    for name in ("audit_state", "THRESHOLDS", "validate_model", "validate_protocol",
                 "load_controller", "classify_prefix", "bind_completion", "bind_manifest"):
        assert getattr(readback, name) is getattr(frozen, name)


def test_fixed_protocol_auditor_and_manifest_scope_are_exact():
    protocol = REPO / "configs/contact_c2_v3.json"
    assert frozen.sha(protocol) == readback.PROTOCOL_SHA256
    assert frozen.sha(REPO / "scripts/audit_contact_c2.py") == readback.FROZEN_AUDITOR_SHA256
    p = frozen.read_json(protocol)
    gate = (protocol.parent / p["saved_field_admission"]["path"]).resolve()
    assert frozen.sha(gate) == p["saved_field_admission"]["sha256"]
    admission = frozen.read_json(gate)["input_sha256_from_workspace_root"]
    assert len(p["implementation_sha256"]) == 33
    assert len(admission) == 166
    assert {k: admission[k] for k in readback.EXTERNAL_HISTORICAL_SOURCES} == readback.EXTERNAL_HISTORICAL_SOURCES


def test_changed_protocol_rejected_before_any_state_evaluation():
    # Same repository tree and disk are required by the unchanged loader.
    with tempfile.TemporaryDirectory(prefix="readback-protocol-test-", dir=REPO) as directory:
        changed = Path(directory) / "contact_c2_v3.json"
        changed.write_bytes((REPO / "configs/contact_c2_v3.json").read_bytes() + b" ")
        with pytest.raises(ValueError, match="evidence hash mismatch"):
            readback.load_run(Path(directory) / "no-run", changed, {})


@pytest.mark.parametrize("status", ["numerical_pass", "pass"])
def test_frozen_execution_guard_rejects_readback_schema_even_with_success_receipts(tmp_path, status):
    experiments = tmp_path / "experiments"
    run = experiments / "padding_2p5"
    run.mkdir(parents=True)
    protocol = tmp_path / "protocol.json"
    protocol.write_text("{}")
    audit = dict(schema_version=readback.SCHEMA_VERSION, status=status, numerical_status="pass",
                 valid_for_execution_admission=False, case_id="padding_2p5")
    (run / "audit.json").write_text(json.dumps(audit))
    receipts = {}
    for action in ("solve", "audit"):
        log = experiments / f"padding_2p5.{action}.log"
        log.write_text("completed")
        receipt = dict(schema="contact_c2_external_receipt_v1", action=action, case_id="padding_2p5",
                       run_name=run.name, returncode=0, timed_out=False,
                       protocol_sha256=frozen.sha(protocol), log_sha256=frozen.sha(log))
        if action == "audit":
            receipt["audit_sha256"] = frozen.sha(run / "audit.json")
        (experiments / f"padding_2p5.{action}.receipt.json").write_text(json.dumps(receipt))
        receipts[action] = receipt
    with pytest.raises(ValueError, match="not independently admitted"):
        isolated.validate_previous([receipts["solve"]], experiments, protocol)


def test_input_error_is_nonzero_with_only_new_schema_and_no_admission(tmp_path):
    output = tmp_path / "numerical_readback.json"
    code = readback.main(["--run", str(tmp_path / "missing-run"), "--output", str(output),
                          "--protocol", str(tmp_path / "missing-protocol.json")])
    result = json.loads(output.read_text())
    assert code == 1
    assert result["schema_version"] == readback.SCHEMA_VERSION
    assert result["status"] == "numerical_not_pass" and result["numerical_status"] == "not_pass"
    assert result["valid_for_execution_admission"] is False
    assert result["historical_source_status"] == "not_assessed_due_to_input_error"
    assert result["states"] == []


def test_reserved_execution_audit_name_is_rejected_without_writing(tmp_path):
    output = tmp_path / "audit.json"
    with pytest.raises(SystemExit):
        readback.main(["--run", str(tmp_path), "--output", str(output),
                       "--protocol", str(REPO / "configs/contact_c2_v3.json")])
    assert not output.exists()


def test_fresh_import_uses_no_jax_or_production_kernel():
    command = [sys.executable, "-B", "-c",
               "import sys;sys.path.insert(0, 'scripts');import audit_contact_c2_readback;"
               "assert 'jax' not in sys.modules;assert 'hf_eval.split_kernel' not in sys.modules"]
    completed = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr
