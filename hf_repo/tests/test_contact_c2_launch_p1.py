"""P1 launch tests: all process and mechanics boundaries are test doubles.

The synthetic trusted fixture deliberately patches the module SHA constant in
Python. No production CLI accepts an expected SHA or substitutes this fixture
for the immutable historical v3 identity. No test solves an FE state or runs HP.
"""
import builtins
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest


REAL_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REAL_REPO / "scripts"))
import contact_c2_launch_p1 as launch

FROZEN = json.loads((REAL_REPO / "configs/contact_c2_v3.json").read_text(encoding="utf-8-sig"))
PROCESS_APIS = ("run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput")
FORBIDDEN_MODULES = ("jax", "numpy", "scipy", "hf_eval", "run_contact_c2", "audit_contact_c2")


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, path + (key,))
    elif isinstance(value, list):
        for key, child in enumerate(value):
            yield from leaves(child, path + (key,))
    else:
        yield path


def changed(value):
    if isinstance(value, str):
        return value + "__changed"
    if type(value) is int:
        return value + 1
    if type(value) is float:
        return value + 0.0123
    raise AssertionError(type(value))


@pytest.fixture
def tree(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    repo = root / "hf_repo"
    for name in FROZEN["implementation_sha256"]:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REAL_REPO / name, target)
    for name in launch.P1_FILES:
        shutil.copyfile(REAL_REPO / name, repo / name)
    (repo / "configs").mkdir(parents=True)
    shutil.copyfile(REAL_REPO / "configs/contact_c1_v1.json", repo / "configs/contact_c1_v1.json")
    protocol = deepcopy(FROZEN)
    source = root / "synthetic_admission_input.txt"
    source.write_text("Synthetic fixture only; no FE or physical admission.\n", encoding="utf-8")
    gate = root / "hf4_c2_diagnostics/saved_field_admission_r3.json"
    write(gate, dict(schema="contact_c2_saved_field_admission_v1", status="pass",
                     input_sha256_from_workspace_root={source.relative_to(root).as_posix(): launch.sha(source)}))
    protocol["saved_field_admission"]["sha256"] = launch.sha(gate)
    for row in protocol["baseline_audits"]:
        path = (repo / "configs" / row["path"]).resolve()
        write(path, dict(schema_version="contact-c1-independent-audit-1.0", status="pass",
                         fixture="synthetic, never a scientific result"))
        row["sha256"] = launch.sha(path)
    protocol_path = repo / "configs/contact_c2_v3.json"
    write(protocol_path, protocol)
    monkeypatch.setattr(launch, "REPO", repo)
    monkeypatch.setattr(launch, "PROTOCOL_SHA256", launch.sha(protocol_path))
    return SimpleNamespace(root=root, repo=repo, path=protocol_path, protocol=protocol,
                           gate=gate, source=source, runs=root / "synthetic_experiments")


@pytest.fixture(autouse=True)
def no_real_process_or_backend(monkeypatch):
    def prohibited(*args, **kwargs):
        raise AssertionError("real process/backend boundary is prohibited by this test")
    for name in PROCESS_APIS:
        monkeypatch.setattr(subprocess, name, prohibited)
    monkeypatch.setattr(launch, "_invoke_backend", prohibited)


def no_heavy_imports(monkeypatch):
    old = builtins.__import__
    calls = []
    def guarded(name, *args, **kwargs):
        if name.split(".")[0] in FORBIDDEN_MODULES:
            calls.append(name)
            raise AssertionError("heavy import before validation: " + name)
        return old(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    return calls


def rejected_without_effects(tree, monkeypatch, path=None, case="padding_2p5", action="solve"):
    run = tree.runs / case
    before = {p.relative_to(tree.runs).as_posix(): launch.sha(p)
              for p in tree.runs.rglob("*") if p.is_file()} if tree.runs.exists() else None
    called = no_heavy_imports(monkeypatch)
    for direct in (False, True):
        args = ["--output" if direct else "--run", str(run), "--case", case,
                "--protocol", str(path or tree.path), "--action", action]
        with pytest.raises(SystemExit) as error:
            launch.cli(args, direct=direct)
        assert error.value.code == 2
    assert not called
    after = {p.relative_to(tree.runs).as_posix(): launch.sha(p)
             for p in tree.runs.rglob("*") if p.is_file()} if tree.runs.exists() else None
    assert before == after


@pytest.mark.parametrize("field", list(leaves(FROZEN)), ids=lambda row: ".".join(map(str, row)))
def test_every_frozen_field_mutation_rejected_by_both_entries(tree, monkeypatch, field):
    altered = deepcopy(tree.protocol)
    parent = altered
    for key in field[:-1]:
        parent = parent[key]
    parent[field[-1]] = changed(parent[field[-1]])
    path = tree.repo / "configs/edited.json"
    write(path, altered)
    rejected_without_effects(tree, monkeypatch, path)
    assert not tree.runs.exists()


@pytest.mark.parametrize("section", list(FROZEN))
def test_missing_or_added_top_level_contract_fields_rejected(tree, monkeypatch, section):
    altered = deepcopy(tree.protocol)
    del altered[section]
    path = tree.repo / "configs/edited.json"
    write(path, altered)
    rejected_without_effects(tree, monkeypatch, path)


@pytest.mark.parametrize("mutation", ["empty_manifest", "partial_manifest", "extra_field", "bool_count",
    "string_tolerance", "float_count", "bad_sequence", "empty_cases", "baseline_case", "same_semantics_new_bytes"])
def test_structural_and_type_contract_edits_rejected(tree, monkeypatch, mutation):
    altered = deepcopy(tree.protocol)
    if mutation == "empty_manifest":
        altered["implementation_sha256"] = {}
    elif mutation == "partial_manifest":
        altered["implementation_sha256"].pop("scripts/run_contact_c2.py")
    elif mutation == "extra_field":
        altered["new_execution_switch"] = True
    elif mutation == "bool_count":
        altered["solver"]["max_checks"] = True
    elif mutation == "float_count":
        altered["solver"]["max_checks"] = 35.0
    elif mutation == "string_tolerance":
        altered["solver"]["tolerance"] = "1e-9"
    elif mutation == "bad_sequence":
        altered["run_sequence"] = altered["run_sequence"][::-1]
    elif mutation == "empty_cases":
        altered["cases"] = {}
    elif mutation == "baseline_case":
        altered["cases"]["baseline_h0125"] = altered["cases"]["outer_free"]
    path = tree.repo / "configs/edited.json"
    write(path, altered)
    if mutation == "same_semantics_new_bytes":
        path.write_text(json.dumps(altered, separators=(",", ":")), encoding="utf-8")
    rejected_without_effects(tree, monkeypatch, path)


@pytest.mark.parametrize("text", ['{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}',
                                 '{"x": -Infinity}', '{"x": 1e999}', '{broken', '{"outer":{"a":1,"a":2}}'])
def test_strict_json_rejects_ambiguous_or_nonfinite_input(tmp_path, text):
    path = tmp_path / "bad.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(launch.ContractError):
        launch.strict_json(path)


@pytest.mark.parametrize("value,expected", [(True, 1), (1.0, 1), ("1e-9", 1e-9), ({"a": 1, "b": 2}, {"a": 1})])
def test_type_aware_contract_comparison(value, expected):
    with pytest.raises(launch.ContractError):
        launch.exact(value, expected, "fixture")


@pytest.mark.parametrize("target", ["source", "missing_source", "gate", "gate_input", "baseline", "c1", "p1_missing"])
def test_source_admission_and_reference_changes_rejected(tree, monkeypatch, target):
    choices = dict(source=tree.repo / "src/hf_eval/split_kernel.py",
                   missing_source=tree.repo / "scripts/run_contact_c2.py", gate=tree.gate,
                   gate_input=tree.source, baseline=(tree.path.parent / tree.protocol["baseline_audits"][0]["path"]).resolve(),
                   c1=tree.repo / "configs/contact_c1_v1.json", p1_missing=tree.repo / launch.P1_FILES[0])
    path = choices[target]
    if target in ("missing_source", "p1_missing"):
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b"\nchanged\n")
    rejected_without_effects(tree, monkeypatch)


def repin_fixture(tree, monkeypatch):
    """Synthetic authority update, unavailable through production CLI."""
    write(tree.path, tree.protocol)
    monkeypatch.setattr(launch, "PROTOCOL_SHA256", launch.sha(tree.path))


@pytest.mark.parametrize("mutation", ["status", "schema", "readback_only", "missing_manifest", "null_digest", "bad_digest"])
def test_bound_admission_has_strict_execution_semantics(tree, monkeypatch, mutation):
    gate = json.loads(tree.gate.read_text())
    if mutation == "status": gate["status"] = "not_pass"
    if mutation == "schema": gate["schema"] = "public_readback_only"
    if mutation == "readback_only": gate["valid_for_execution_admission"] = False
    if mutation == "missing_manifest": gate.pop("input_sha256_from_workspace_root")
    if mutation in ("null_digest", "bad_digest"):
        gate["input_sha256_from_workspace_root"][tree.source.name] = None if mutation == "null_digest" else "0" * 64
    write(tree.gate, gate)
    tree.protocol["saved_field_admission"]["sha256"] = launch.sha(tree.gate)
    repin_fixture(tree, monkeypatch)
    rejected_without_effects(tree, monkeypatch)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:/escape", "a\\b", "a//b", "./a"])
def test_binding_paths_reject_escape_and_noncanonical_names(tree, name):
    with pytest.raises(launch.ContractError):
        launch.confined(tree.root, name)


def test_parent_relative_gate_is_allowed_only_inside_workspace(tree):
    assert launch.confined(tree.path.parent, "../../synthetic_admission_input.txt",
                            limit=tree.root, parents=True) == tree.source
    with pytest.raises(launch.ContractError):
        launch.confined(tree.path.parent, "../../../escape", limit=tree.root, parents=True)


@pytest.mark.parametrize("entry", ["run_contact_c2_p1.py", "run_contact_c2_p1_isolated.py", "contact_c2_launch_p1.py"])
def test_new_modules_import_without_mechanics(tmp_path, monkeypatch, entry):
    calls = no_heavy_imports(monkeypatch)
    runpy.run_path(str(REAL_REPO / "scripts" / entry), run_name="p1_import_only")
    assert not calls


def test_positive_plan_is_read_only_and_binds_sources(tree, monkeypatch):
    calls = no_heavy_imports(monkeypatch)
    plan = launch.plan_launch("solve", tree.runs / "padding_2p5", "padding_2p5", tree.path)
    assert not tree.runs.exists() and not calls
    assert plan["timeout_seconds"] == 700
    assert plan["protocol_sha256"] == launch.PROTOCOL_SHA256
    assert plan["run"] == "synthetic_experiments/padding_2p5"
    assert len(plan["input_sha256"]) >= 40
    assert all(not Path(name).is_absolute() for name in plan["input_sha256"])


@pytest.mark.parametrize("direct", [False, True])
def test_both_public_entries_share_bounded_dispatch_and_worker_revalidation(tree, monkeypatch, direct):
    events = []
    monkeypatch.setattr(launch, "_invoke_backend", lambda plan: events.append(("mock_backend", plan["case_id"])) or 0)
    def intercepted(command, **kwargs):
        events.append(("intercepted_dispatch", kwargs["timeout"]))
        assert kwargs["env"]["JAX_ENABLE_X64"] == "true"
        assert kwargs["env"]["JAX_PLATFORMS"] == "cpu"
        assert command[2].endswith("run_contact_c2_p1_isolated.py")
        result = launch.worker(Path(command[4]), command[6])
        return SimpleNamespace(returncode=result)
    monkeypatch.setattr(subprocess, "run", intercepted)
    args = ["--output" if direct else "--run", str(tree.runs / "padding_2p5"),
            "--case", "padding_2p5", "--protocol", str(tree.path), "--action", "solve"]
    assert launch.cli(args, direct=direct) == 0
    assert events == [("intercepted_dispatch", 700), ("mock_backend", "padding_2p5")]
    saved = json.loads((tree.runs / "padding_2p5.solve.receipt.json").read_text())
    assert saved["schema"] == launch.RECEIPT_SCHEMA and saved["returncode"] == 0
    assert saved["launch_plan_sha256"] == launch.sha(tree.runs / "padding_2p5.solve.p1-plan.json")
    assert not (tree.runs / "padding_2p5").exists()  # mocked backend generated no run


def test_changed_source_between_parent_and_child_never_imports_backend(tree, monkeypatch):
    calls = []
    monkeypatch.setattr(launch, "_invoke_backend", lambda plan: calls.append(plan) or 0)
    def intercepted(command, **kwargs):
        source = tree.repo / "src/hf_eval/split_kernel.py"
        source.write_bytes(source.read_bytes() + b"\n# changed after parent plan\n")
        with pytest.raises(launch.ContractError, match="hash changed"):
            launch.worker(Path(command[4]), command[6])
        return SimpleNamespace(returncode=2)
    monkeypatch.setattr(subprocess, "run", intercepted)
    assert launch.launch("solve", tree.runs / "padding_2p5", "padding_2p5", tree.path) == 2
    assert not calls and not (tree.runs / "padding_2p5").exists()


def history(tree, count=1, *, last_audited=True):
    """Fabricated ordinary-file receipts, never a solver or audit result."""
    for i, case in enumerate(launch.SEQUENCE[:count]):
        run = tree.runs / case
        write(run / "metadata.json", dict(schema="contact_c2_run_v1", kind="TMC", mode="uniform",
              case_id=case, protocol_sha256=launch.PROTOCOL_SHA256, protocol=tree.protocol))
        for action in ("solve", "audit"):
            if action == "audit" and i == count - 1 and not last_audited:
                continue
            log = tree.runs / (case + "." + action + ".log")
            log.write_text("Synthetic fixture only.\n", encoding="utf-8")
            receipt = dict(schema="contact_c2_external_receipt_v1", action=action,
                case_id=case, run_name=case, returncode=0, timed_out=False,
                protocol_sha256=launch.PROTOCOL_SHA256, log_sha256=launch.sha(log),
                elapsed_seconds=1.0, timeout_seconds=700 if action == "solve" else 1200)
            if action == "audit":
                detail = run / "synthetic_detail.json"
                write(detail, dict(fixture=True))
                write(run / "audit.json", dict(schema_version="contact-c2-independent-audit-1.0",
                    status="pass", case_id=case,
                    input_and_helper_sha256={"metadata.json": launch.sha(run / "metadata.json")},
                    detail_output_sha256={detail.name: launch.sha(detail)}))
                receipt["audit_sha256"] = launch.sha(run / "audit.json")
            write(tree.runs / (case + "." + action + ".receipt.json"), receipt)


def edit_receipt(tree, action, field, value, *, delete=False, case="padding_2p5"):
    path = tree.runs / (case + "." + action + ".receipt.json")
    receipt = json.loads(path.read_text())
    if delete:
        receipt.pop(field)
    else:
        receipt[field] = value
    # Deliberate nonfinite token fixtures test strict parser rejection.
    path.write_text(json.dumps(receipt, allow_nan=True), encoding="utf-8")


@pytest.mark.parametrize("field,value", [
    ("elapsed_seconds", -1), ("elapsed_seconds", True), ("elapsed_seconds", "1"),
    ("elapsed_seconds", None), ("elapsed_seconds", float("nan")), ("elapsed_seconds", float("inf")),
    ("elapsed_seconds", 10 ** 400),
    ("timeout_seconds", 0), ("timeout_seconds", True), ("timeout_seconds", 701),
    ("returncode", True), ("returncode", 1), ("returncode", None), ("timed_out", True),
    ("timed_out", 0), ("schema", "other"), ("action", "audit"), ("case_id", "outer_free"),
    ("run_name", "../escape"), ("run_name", "other"), ("protocol_sha256", "0" * 64),
    ("log_sha256", None), ("log_sha256", ""), ("log_sha256", "0" * 64),
])
def test_malformed_or_failed_prior_solve_rejected_before_effects(tree, monkeypatch, field, value):
    history(tree)
    edit_receipt(tree, "solve", field, value)
    rejected_without_effects(tree, monkeypatch, case="outer_free")


@pytest.mark.parametrize("action,field", [("solve", "log_sha256"), ("audit", "log_sha256"),
                                         ("audit", "audit_sha256")])
@pytest.mark.parametrize("mode", ["missing", "null", "malformed", "different"])
def test_required_receipt_hashes_cannot_be_optional(tree, monkeypatch, action, field, mode):
    history(tree)
    value = {"missing": None, "null": None, "malformed": "BAD", "different": "0" * 64}[mode]
    edit_receipt(tree, action, field, value, delete=mode == "missing")
    rejected_without_effects(tree, monkeypatch, case="outer_free")


@pytest.mark.parametrize("mutation", ["missing_audit_receipt", "failed_audit", "changed_detail", "changed_input",
    "missing_bindings", "null_binding", "unknown_file", "orphan_directory", "missing_metadata", "wrong_metadata_protocol",
    "nonobject_metadata", "nonobject_audit"])
def test_serial_evidence_chain_cannot_be_skipped(tree, monkeypatch, mutation):
    history(tree)
    run = tree.runs / "padding_2p5"
    if mutation == "missing_audit_receipt": (tree.runs / "padding_2p5.audit.receipt.json").unlink()
    elif mutation == "failed_audit": edit_receipt(tree, "audit", "returncode", 2)
    elif mutation == "changed_detail": (run / "synthetic_detail.json").write_text("changed")
    elif mutation == "changed_input": (run / "metadata.json").write_text("changed")
    elif mutation in ("missing_bindings", "null_binding"):
        audit = json.loads((run / "audit.json").read_text())
        if mutation == "missing_bindings": audit.pop("input_and_helper_sha256")
        else: audit["detail_output_sha256"]["synthetic_detail.json"] = None
        write(run / "audit.json", audit)
        edit_receipt(tree, "audit", "audit_sha256", launch.sha(run / "audit.json"))
    elif mutation == "unknown_file": (tree.runs / "unreceipted.log").write_text("preserve")
    elif mutation == "orphan_directory": (tree.runs / "failed_attempt").mkdir()
    elif mutation == "missing_metadata": (run / "metadata.json").unlink()
    elif mutation == "wrong_metadata_protocol":
        data = json.loads((run / "metadata.json").read_text())
        data["protocol"]["solver"]["tolerance"] = 1e-3
        write(run / "metadata.json", data)
    elif mutation == "nonobject_metadata": write(run / "metadata.json", [])
    elif mutation == "nonobject_audit":
        write(run / "audit.json", [])
        edit_receipt(tree, "audit", "audit_sha256", launch.sha(run / "audit.json"))
    rejected_without_effects(tree, monkeypatch, case="outer_free")


def test_valid_prior_evidence_permits_only_next_case(tree, monkeypatch):
    history(tree)
    plan = launch.plan_launch("solve", tree.runs / "outer_free", "outer_free", tree.path)
    assert plan["timeout_seconds"] == 700
    rejected_without_effects(tree, monkeypatch, case="mesh_h00625")
    rejected_without_effects(tree, monkeypatch, case="padding_2p5")


def test_first_case_order_and_baseline_are_enforced(tree, monkeypatch):
    rejected_without_effects(tree, monkeypatch, case="outer_free")
    rejected_without_effects(tree, monkeypatch, case="baseline_h0125")


def test_complete_path_cap_rejects_additional_runs(tree, monkeypatch):
    history(tree, 3)
    rejected_without_effects(tree, monkeypatch, case="padding_2p5")


@pytest.mark.parametrize("action,field,value", [("solve", "elapsed_seconds", 2100),
                                             ("audit", "elapsed_seconds", 3600)])
def test_cumulative_budget_exhaustion_stops_next_solve(tree, monkeypatch, action, field, value):
    history(tree)
    edit_receipt(tree, action, field, value)
    rejected_without_effects(tree, monkeypatch, case="outer_free")


def test_successful_final_solve_can_be_audited_after_solve_budget_exhausted(tree):
    history(tree, last_audited=False)
    edit_receipt(tree, "solve", "elapsed_seconds", 2100)
    plan = launch.plan_launch("audit", tree.runs / "padding_2p5", "padding_2p5", tree.path)
    assert plan["timeout_seconds"] == 1200


def test_audit_requires_latest_successful_solve_and_no_prior_audit(tree, monkeypatch):
    rejected_without_effects(tree, monkeypatch, action="audit")
    history(tree, last_audited=False)
    assert launch.plan_launch("audit", tree.runs / "padding_2p5", "padding_2p5", tree.path)
    rejected_without_effects(tree, monkeypatch, action="audit", case="outer_free")
    history(tree)
    rejected_without_effects(tree, monkeypatch, action="audit")


@pytest.mark.parametrize("mode", ["missing", "null", "malformed", "different"])
def test_p1_receipt_requires_its_plan_hash(tree, monkeypatch, mode):
    history(tree)
    edit_receipt(tree, "solve", "schema", launch.RECEIPT_SCHEMA)
    if mode != "missing":
        edit_receipt(tree, "solve", "launch_plan_sha256",
                     {"null": None, "malformed": "BAD", "different": "0" * 64}[mode])
    rejected_without_effects(tree, monkeypatch, case="outer_free")


def test_p1_plan_cannot_omit_current_static_source_identity(tree, monkeypatch):
    plan = launch.plan_launch("solve", tree.runs / "padding_2p5", "padding_2p5", tree.path)
    history(tree)
    plan["input_sha256"].pop("hf_repo/scripts/contact_c2_launch_p1.py")
    path = tree.runs / "padding_2p5.solve.p1-plan.json"
    write(path, plan)
    edit_receipt(tree, "solve", "schema", launch.RECEIPT_SCHEMA)
    edit_receipt(tree, "solve", "launch_plan_sha256", launch.sha(path))
    rejected_without_effects(tree, monkeypatch, case="outer_free")


def test_nonobject_p1_plan_is_controlled_rejection(tree, monkeypatch):
    history(tree)
    path = tree.runs / "padding_2p5.solve.p1-plan.json"
    write(path, [])
    edit_receipt(tree, "solve", "schema", launch.RECEIPT_SCHEMA)
    edit_receipt(tree, "solve", "launch_plan_sha256", launch.sha(path))
    rejected_without_effects(tree, monkeypatch, case="outer_free")


@pytest.mark.parametrize("mode", ["timeout", "spawn_failure"])
def test_dispatch_failures_leave_explicit_nonpassing_receipts(tree, monkeypatch, mode):
    def intercepted(command, **kwargs):
        if mode == "timeout": raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        raise OSError("synthetic spawn failure")
    monkeypatch.setattr(subprocess, "run", intercepted)
    code = launch.launch("solve", tree.runs / "padding_2p5", "padding_2p5", tree.path)
    assert code == (124 if mode == "timeout" else 125)
    saved = json.loads((tree.runs / "padding_2p5.solve.receipt.json").read_text())
    assert saved["returncode"] is None
    assert saved["timed_out"] is (mode == "timeout")
    assert bool(saved["launch_failure"]) is (mode == "spawn_failure")


def test_private_worker_requires_bound_parent_plan_and_disallows_mixed_arguments(tree):
    missing = tree.root / "missing-plan.json"
    with pytest.raises(OSError): launch.worker(missing, "0" * 64)
    with pytest.raises(SystemExit) as error:
        launch.cli(["--_worker-plan", str(missing), "--_worker-sha256", "0" * 64,
                    "--action", "solve", "--run", str(tree.runs / "padding_2p5"),
                    "--case", "padding_2p5", "--protocol", str(tree.path)])
    assert error.value.code == 2


def test_output_tree_must_not_escape_or_target_source_repository(tree):
    for run in (tree.root.parent / "escape/run", tree.repo / "result/run"):
        with pytest.raises(launch.ContractError):
            launch.plan_launch("solve", run, "padding_2p5", tree.path)
        assert not run.exists()


def test_production_constant_and_frozen_sources_remain_unchanged():
    assert hashlib.sha256((REAL_REPO / "configs/contact_c2_v3.json").read_bytes()).hexdigest() == (
        "b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d")
    for name, digest in FROZEN["implementation_sha256"].items():
        assert hashlib.sha256((REAL_REPO / name).read_bytes()).hexdigest() == digest
