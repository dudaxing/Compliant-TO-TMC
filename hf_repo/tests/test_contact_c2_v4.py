"""v4 kernel-repair contract, runner, audit and launch-guard tests.

No test solves an equilibrium path, runs the C2 case or evaluates the HP reference. The runner is exercised only
through its contract validation and its component-JVP entry on a two-element model (arithmetic check). Every
process and backend boundary of the launch guard is a test double on a synthetic workspace, as in the P1 tests.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import jax
import jax.numpy as jnp
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_contact_c2  # noqa: E402
import audit_contact_c2_v4 as audit_v4  # noqa: E402
import contact_c2_launch_p1 as launch_p1  # noqa: E402
import contact_c2_launch_v4 as launch  # noqa: E402
import contact_c2_v4_contract as contract  # noqa: E402
import freeze_contact_c2_v4 as freeze  # noqa: E402
import run_contact_c2_v4 as runner  # noqa: E402
from hf_eval import split_kernel_compensated as kernel  # noqa: E402
from hf_eval.split_state import SplitDisplacement  # noqa: E402
from hf_eval.tmc import rectangular_model  # noqa: E402

V3 = json.loads((ROOT / contract.V3_PROTOCOL_PATH).read_text(encoding="utf-8-sig"))
C1 = json.loads((ROOT / contract.C1_PROTOCOL_PATH).read_text(encoding="utf-8-sig"))
PROCESS_APIS = ("run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def memory_protocol():
    manifest = {name: "0" * 64 for name in contract.REQUIRED_IMPLEMENTATION}
    return freeze.build_protocol(manifest, "1" * 64, "2026-09-27T00:00:00+00:00")


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, path + (index,))
    else:
        yield path


def changed(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return value + "__changed"
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value * 1.5 + 0.0123
    raise AssertionError(type(value))


# ------------------------------------------------------------------ contract
def test_contract_accepts_the_built_protocol_and_keeps_v3_physics():
    protocol = memory_protocol()
    contract.validate_protocol(protocol, V3, C1)
    for section in contract.RETAINED_V3_SECTIONS:
        assert protocol[section] == V3[section]
    assert protocol["cases"] == {"mesh_h00625": V3["cases"]["mesh_h00625"]}
    assert protocol["uniform_targets_mm"] == [0, 0.125, 0.21875, 0.25, 0.28125, 0.375, 0.5]
    assert protocol["budget"]["solver_internal_wall_seconds"] == V3["solver"]["time_limit_seconds"] == 300.0
    assert (protocol["budget"]["subprocess_wall_seconds"], protocol["budget"]["maximum_audit_seconds_per_path"]) == (700, 1200)


CONTRACT_FIELDS = [path for path in leaves(memory_protocol())
                   if path[0] not in ("frozen_utc", "purpose", "stopping", "storage", "prefix_semantics", "implementation_sha256")
                   and path[:2] not in (("relation_to_v3", "retained_sections"), ("relation_to_v3", "changed"),
                                        ("relation_to_v3", "not_carried_over"), ("stable_f_evidence", "sha256"),
                                        ("stable_f_evidence", "path"))]


@pytest.mark.parametrize("field", CONTRACT_FIELDS, ids=lambda row: ".".join(map(str, row)))
def test_every_contract_field_change_is_rejected(field):
    protocol = memory_protocol()
    parent = protocol
    for key in field[:-1]:
        parent = parent[key]
    parent[field[-1]] = changed(parent[field[-1]])
    with pytest.raises(contract.V4ContractError):
        contract.validate_protocol(protocol, V3, C1)


@pytest.mark.parametrize("edit", ["missing_field", "extra_field", "launch_file_in_manifest", "required_file_missing",
                                  "bad_digest", "absolute_path", "parent_path", "bool_for_int", "int_for_float"])
def test_structural_contract_edits_are_rejected(edit):
    protocol = memory_protocol()
    if edit == "missing_field":
        del protocol["kernel"]
    elif edit == "extra_field":
        protocol["tolerance_override"] = 1e-8
    elif edit == "launch_file_in_manifest":
        protocol["implementation_sha256"]["scripts/contact_c2_launch_v4.py"] = "2" * 64
    elif edit == "required_file_missing":
        del protocol["implementation_sha256"]["src/hf_eval/split_kernel_compensated.py"]
    elif edit == "bad_digest":
        protocol["implementation_sha256"]["scripts/hf4_common.py"] = "Z" * 64
    elif edit == "absolute_path":
        protocol["implementation_sha256"]["/etc/passwd"] = "3" * 64
    elif edit == "parent_path":
        protocol["implementation_sha256"]["../outside.py"] = "3" * 64
    elif edit == "bool_for_int":
        protocol["budget"]["maximum_paths"] = True
    elif edit == "int_for_float":
        protocol["solver"]["time_limit_seconds"] = 300
    with pytest.raises(contract.V4ContractError):
        contract.validate_protocol(protocol, V3, C1)


def test_environment_check_reports_each_mismatch(monkeypatch):
    monkeypatch.setattr(contract.importlib.metadata, "version", lambda name: "0.0.0")
    mismatches = contract.environment_mismatches()
    assert {"numpy", "scipy", "jax", "jaxlib"} <= set(mismatches)


# ------------------------------------------------------------------ runner (no path, no C2 case)
def test_runner_kernel_identity_and_protocol_content(monkeypatch):
    runner.check_kernel_identity()
    monkeypatch.setattr(contract, "environment_mismatches", lambda expected=None: {})
    runner.validate(memory_protocol(), ROOT / contract.PROTOCOL_PATH)
    monkeypatch.setattr(contract, "environment_mismatches", lambda expected=None: {"jax": dict(expected="0.11.0", actual="0.9.0.1")})
    with pytest.raises(contract.V4ContractError):
        runner.validate(memory_protocol(), ROOT / contract.PROTOCOL_PATH)


def test_component_jvp_entry_is_compiled_with_the_kernel_strict_options(monkeypatch):
    recorded, real = [], jax.jit

    def recording(function, *args, **kwargs):
        recorded.append(kwargs.get("compiler_options"))
        return real(function, *args, **kwargs)

    monkeypatch.setattr(jax, "jit", recording)
    spec = importlib.util.spec_from_file_location("run_contact_c2_v4_fresh_copy", ROOT / "scripts/run_contact_c2_v4.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert recorded == [kernel.COMPILER_OPTIONS]


def test_component_actions_match_an_independent_jvp_and_the_assembled_tangent():
    fixed = [0, 1, 2, 3, 4, 5]
    model = rectangular_model(2, 1, 1.0, 0.5, E=100.0, fixed_dofs=fixed)
    rng = np.random.default_rng(20260927)
    lift = np.zeros(model.ndof)
    lift[1::2] = -0.02 * model.coordinates[:, 1]
    fluctuation = 1e-3 * rng.standard_normal(model.ndof)
    fluctuation[fixed] = 0.0
    vector = rng.standard_normal(model.ndof)
    vector[fixed] = 0.0
    state = SplitDisplacement(lift, fluctuation)
    actions = runner.component_actions(model, state, vector)

    def independent(L, w, direction):
        def residual(varied):
            fields = jax.vmap(kernel._without_tangent, in_axes=(0, 0, None, None, None, 0, 0, None))(
                L, varied, model.ops["grad"], model.ops["hessian"], model.ops["weights"], model.lam, model.mu, model.kr)
            return fields["material_residual"], fields["regularization_residual"]
        return jax.jvp(residual, (w,), (direction,))[1]

    reference = jax.jit(independent, compiler_options=kernel.COMPILER_OPTIONS)(
        jnp.asarray(lift[model.edofs]), jnp.asarray(fluctuation[model.edofs]), jnp.asarray(vector[model.edofs]))
    assemble = lambda values: np.bincount(model.edofs.ravel(), weights=np.asarray(values).ravel(), minlength=model.ndof)
    np.testing.assert_allclose(actions["material_residual"], assemble(reference[0]), rtol=1e-13, atol=1e-13)
    np.testing.assert_allclose(actions["regularization_residual"], assemble(reference[1]), rtol=1e-13, atol=1e-18)
    matrix, _, _ = kernel.assemble_split(model, state, tangent=True)
    np.testing.assert_allclose(actions["material_residual"] + actions["regularization_residual"], matrix @ vector,
                               rtol=1e-12, atol=1e-12)


# ------------------------------------------------------------------ audit (no HP evaluation)
def test_audit_reuses_the_frozen_numerical_functions_unchanged():
    for name in ("audit_state", "validate_model", "load_controller", "bind_completion", "classify_prefix", "portable_bindings"):
        assert getattr(audit_v4, name) is getattr(audit_contact_c2, name)
    assert audit_v4.THRESHOLDS is audit_contact_c2.THRESHOLDS
    assert sha(ROOT / "scripts/audit_contact_c2.py") == audit_v4.FROZEN_AUDITOR_SHA256


def test_audit_protocol_check_accepts_v4_and_rejects_v3():
    audit_v4.validate_protocol_v4(memory_protocol())
    with pytest.raises(ValueError):
        audit_v4.validate_protocol_v4(deepcopy(V3))


def test_audit_and_guard_import_no_production_kernel_or_jax():
    probe = ("import sys; sys.path[:0]=[r'%s', r'%s']; import audit_contact_c2_v4, contact_c2_launch_v4; "
             "bad=[m for m in sys.modules if m=='jax' or m.startswith('jax.') or m.startswith('hf_eval.split_kernel')]; "
             "print(bad)") % (ROOT / "scripts", ROOT / "src")
    output = subprocess.check_output([sys.executable, "-B", "-c", probe], text=True)
    assert output.strip() == "[]"


# ------------------------------------------------------------------ launch guard on a synthetic workspace
@pytest.fixture
def tree(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    repo = root / "hf_repo"
    manifest = {}
    for name in contract.REQUIRED_IMPLEMENTATION:
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
        manifest[name] = sha(target)
    for name in contract.LAUNCH_FILES:
        shutil.copyfile(ROOT / name, repo / name)
    (repo / "configs").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / contract.C1_PROTOCOL_PATH, repo / contract.C1_PROTOCOL_PATH)
    source = root / "synthetic_admission_input.txt"
    source.write_text("Synthetic fixture only; no FE or physical admission.\n", encoding="utf-8")
    gate = root / "hf4_c2_diagnostics/saved_field_admission_r3.json"
    write(gate, dict(schema="contact_c2_saved_field_admission_v1", status="pass",
                     input_sha256_from_workspace_root={source.relative_to(root).as_posix(): sha(source)}))
    v3 = deepcopy(V3)
    v3["saved_field_admission"]["sha256"] = sha(gate)
    for row in v3["baseline_audits"]:
        path = (repo / "configs" / row["path"]).resolve()
        write(path, dict(schema_version="contact-c1-independent-audit-1.0", status="pass", fixture="synthetic"))
        row["sha256"] = sha(path)
    write(repo / contract.V3_PROTOCOL_PATH, v3)
    evidence = root / "hf4_c2_stable_f_validation/summary_001.json"
    write(evidence, dict(schema="contact-c2-stable-f-validation-summary-1", saved_all_c2_and_c1=dict(states=63, candidate_pass=63)))
    protocol = freeze.build_protocol(manifest, sha(evidence), "2026-09-27T00:00:00+00:00")
    protocol["saved_field_admission"], protocol["baseline_audits"] = v3["saved_field_admission"], v3["baseline_audits"]
    protocol["relation_to_v3"]["v3_protocol_sha256"] = sha(repo / contract.V3_PROTOCOL_PATH)  # the synthetic v3 of this fixture
    protocol_path = repo / contract.PROTOCOL_PATH
    write(protocol_path, protocol)
    monkeypatch.setattr(contract, "V3_PROTOCOL_SHA256", sha(repo / contract.V3_PROTOCOL_PATH))
    monkeypatch.setattr(contract, "environment_mismatches", lambda expected=None: {})
    monkeypatch.setattr(launch, "REPO", repo)
    monkeypatch.setattr(launch_p1, "REPO", repo)
    monkeypatch.setattr(launch, "PROTOCOL_SHA256", sha(protocol_path))
    write(repo / launch.IDENTITY_FILE, dict(schema=launch.IDENTITY_SCHEMA, protocol_path=contract.PROTOCOL_PATH,
                                           protocol_sha256=sha(protocol_path),
                                           launch_files={name: sha(repo / name) for name in contract.LAUNCH_FILES}))
    for name in PROCESS_APIS:
        monkeypatch.setattr(subprocess, name, lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("real process")))

    def prohibited(*args, **kwargs):
        raise AssertionError("real backend boundary is prohibited in this test")

    monkeypatch.setattr(launch, "_invoke_backend", prohibited)
    return SimpleNamespace(root=root, repo=repo, protocol=protocol, path=protocol_path, runs=root / "hf4_c2_v4_results/experiments")


def refused(tree, *args):
    before = sorted(p.as_posix() for p in tree.root.rglob("*"))
    with pytest.raises(launch_p1.ContractError):
        launch.plan_launch(*args)
    assert sorted(p.as_posix() for p in tree.root.rglob("*")) == before


def test_plan_is_accepted_read_only_and_records_the_launch_identity(tree):
    before = sorted(p.as_posix() for p in tree.root.rglob("*"))
    plan = launch.plan_launch("solve", tree.runs / "mesh_h00625_v4", "mesh_h00625", tree.path)
    assert sorted(p.as_posix() for p in tree.root.rglob("*")) == before and not tree.runs.exists()
    assert plan["timeout_seconds"] == 700 and plan["protocol_sha256"] == launch.PROTOCOL_SHA256
    assert set(plan["launch_identity"]) == set(contract.LAUNCH_FILES)
    assert all("hf_repo/" + name in plan["input_sha256"] for name in tree.protocol["implementation_sha256"])


def test_unset_protocol_identity_refuses(tree, monkeypatch):
    monkeypatch.setattr(launch, "PROTOCOL_SHA256", None)
    refused(tree, "solve", tree.runs / "mesh_h00625_v4", "mesh_h00625", tree.path)


@pytest.mark.parametrize("field", [("solver", "tolerance"), ("budget", "subprocess_wall_seconds"), ("kernel", "kernel_version"),
                                   ("environment", "numpy"), ("uniform_targets_mm", 6), ("audit", "relative_force_evaluation")])
def test_edited_protocol_bytes_are_refused(tree, field):
    protocol = deepcopy(tree.protocol)
    protocol[field[0]][field[1]] = changed(protocol[field[0]][field[1]])
    write(tree.path, protocol)
    refused(tree, "solve", tree.runs / "mesh_h00625_v4", "mesh_h00625", tree.path)


def test_protocol_copy_elsewhere_is_refused(tree):
    copy = tree.repo / "configs/contact_c2_v4_copy.json"
    shutil.copyfile(tree.path, copy)
    refused(tree, "solve", tree.runs / "mesh_h00625_v4", "mesh_h00625", copy)


@pytest.mark.parametrize("name", ["src/hf_eval/split_kernel_compensated.py", "src/hf_eval/split_affine_compensated.py",
                                  "scripts/run_contact_c2_v4.py", "scripts/audit_contact_c2_v4.py"])
def test_changed_bound_implementation_is_refused(tree, name):
    with (tree.repo / name).open("ab") as stream:
        stream.write(b"\n# changed\n")
    refused(tree, "solve", tree.runs / "mesh_h00625_v4", "mesh_h00625", tree.path)


@pytest.mark.parametrize("name", contract.LAUNCH_FILES)
def test_changed_launch_layer_file_is_refused_via_the_identity_file(tree, name):
    with (tree.repo / name).open("ab") as stream:
        stream.write(b"\n# changed\n")
    refused(tree, "solve", tree.runs / "mesh_h00625_v4", "mesh_h00625", tree.path)


def test_identity_file_naming_another_protocol_is_refused(tree):
    identity = json.loads((tree.repo / launch.IDENTITY_FILE).read_text(encoding="utf-8"))
    identity["protocol_sha256"] = "4" * 64
    write(tree.repo / launch.IDENTITY_FILE, identity)
    refused(tree, "solve", tree.runs / "mesh_h00625_v4", "mesh_h00625", tree.path)


def test_environment_mismatch_is_refused(tree, monkeypatch):
    monkeypatch.setattr(contract, "environment_mismatches", lambda expected=None: {"jaxlib": dict(expected="0.11.0", actual="0.9.0.1")})
    refused(tree, "solve", tree.runs / "mesh_h00625_v4", "mesh_h00625", tree.path)


def test_undeclared_case_audit_first_and_run_inside_repo_are_refused(tree):
    refused(tree, "solve", tree.runs / "padding_2p5", "padding_2p5", tree.path)
    refused(tree, "audit", tree.runs / "mesh_h00625_v4", "mesh_h00625", tree.path)
    refused(tree, "solve", tree.repo / "results/mesh_h00625_v4", "mesh_h00625", tree.path)


def fake_child(tree, returncode, *, audit=False):
    def run(command, cwd, env, stdout, stderr, timeout):
        assert command[2].endswith("run_contact_c2_v4_isolated.py") and "--_worker-plan" in command
        plan = json.loads(Path(command[command.index("--_worker-plan") + 1]).read_text(encoding="utf-8"))
        run_dir = tree.root / plan["run"]
        if audit:
            write(run_dir / "audit.json", dict(schema_version=contract.AUDIT_SCHEMA, status="pass"))
        else:
            write(run_dir / "metadata.json", dict(schema=contract.RUN_SCHEMA, kind="TMC", mode="uniform", case_id="mesh_h00625",
                                                  protocol=tree.protocol, protocol_sha256=launch.PROTOCOL_SHA256, kernel=contract.KERNEL))
        return SimpleNamespace(returncode=returncode)
    return run


def test_solve_then_one_audit_with_test_doubles_and_no_retry(tree, monkeypatch):
    run = tree.runs / "mesh_h00625_v4"
    monkeypatch.setattr(launch.subprocess, "run", fake_child(tree, 0))
    assert launch.launch("solve", run, "mesh_h00625", tree.path) == 0
    receipt = json.loads((tree.runs / "mesh_h00625_v4.solve.receipt.json").read_text(encoding="utf-8"))
    assert receipt["schema"] == launch.RECEIPT_SCHEMA and receipt["returncode"] == 0 and set(receipt["launch_identity"]) == set(contract.LAUNCH_FILES)
    refused(tree, "solve", tree.runs / "mesh_h00625_v4b", "mesh_h00625", tree.path)
    monkeypatch.setattr(launch.subprocess, "run", fake_child(tree, 0, audit=True))
    assert launch.launch("audit", run, "mesh_h00625", tree.path) == 0
    assert json.loads((tree.runs / "mesh_h00625_v4.audit.receipt.json").read_text(encoding="utf-8"))["audit_sha256"] == sha(run / "audit.json")
    refused(tree, "audit", run, "mesh_h00625", tree.path)


def test_no_audit_after_a_failed_solve(tree, monkeypatch):
    run = tree.runs / "mesh_h00625_v4"
    monkeypatch.setattr(launch.subprocess, "run", fake_child(tree, 2))
    assert launch.launch("solve", run, "mesh_h00625", tree.path) == 2
    refused(tree, "audit", run, "mesh_h00625", tree.path)


def test_worker_revalidates_the_parent_plan_before_the_backend(tree, monkeypatch):
    run = tree.runs / "mesh_h00625_v4"
    plan = launch.plan_launch("solve", run, "mesh_h00625", tree.path)
    tree.runs.mkdir(parents=True)
    plan_file = tree.runs / "mesh_h00625_v4.solve.v4-plan.json"
    plan_file.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (tree.runs / "mesh_h00625_v4.solve.log").write_text("", encoding="utf-8")
    called = []
    monkeypatch.setattr(launch, "_invoke_backend", lambda repeated: called.append(repeated) or 0)
    assert launch.worker(plan_file, sha(plan_file)) == 0 and called and called[0] == plan
    with pytest.raises(launch_p1.ContractError):
        launch.worker(plan_file, "5" * 64)
