"""Standard-library evidence worker for the separately authorized JIT/AD-1 card.

No scientific imports or subprocesses. The parent meters every invocation.
H1 and optional C1 are frozen independently; canonical sync requires A4 proof.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
from html import escape
import json
import os
from pathlib import Path
import sys
import time
import traceback

from s0_event_log import EventLog
from s0_ad_exception import is_declared_transpose
from s0_preparation_evidence import (
    ARITHMETIC, ClassificationFailure, EvidenceFailure, INPUT_SHA, JAX_FILES,
    MANUFACTURED, OLD_MANIFEST_SHA, OLD_VERSION, TARGET_NODE, append, bound,
    checked, copy_row, path, read, relative, repaired_bytes, require, sha,
    stages_svg, utc, verify_rows, write,
)

TEST = "tests/test_compensated_invariants.py"
H1_TEST = "H1/" + TEST
H1_MANIFEST = "H1/manifest.json"
HISTORY = "hf4_c2_stable_f_validation/s0_ready_001"
HISTORY_BINDING_SHA = "dde34ab02e8666cc78c97d1cbdcddea7fd1db5be4ea7e2c064a1f1a224c3edd9"
AUX_FILES = (
    "hf_repo/scripts/run_jit_ad_preparation.py",
    "hf_repo/scripts/jit_ad_preparation_evidence.py",
    "hf_repo/scripts/probe_jit_ad_preparation.py",
    "hf_repo/scripts/s0_ad_exception.py",
    "hf_repo/scripts/s0_event_log.py",
    "hf_repo/scripts/hf_s0_pytest_events.py",
    "hf_repo/scripts/probe_s0_preparation.py",
    "hf_repo/scripts/s0_preparation_evidence.py",
    "hf_repo/scripts/windows_owned_process.py",
    "hf_repo/tests/test_s0_event_logging.py",
    "docs/HF4_C2_S0_PREPARATION_RESULT_20260928.md",
    "docs/CURRENT_STATUS.md",
)
RUNTIME_FILES = dict(JAX_FILES, **{
    "_src/pjit.py": "fc0f6e9a373ddb517391631bf65245f47829cb7339fd44d90bf4939622256734",
    "_src/stages.py": "9d5f1befad87a29605f342e9e1db4c83b9ddca5327d991f091bc2c740bff87aa",
})
H0_BLOCK = """    compiled=jax.jit(function,compiler_options=ci.COMPILER_OPTIONS)
    _,action=jax.jvp(compiled,(jnp.asarray(x),),(jnp.asarray(direction),))
    _,pullback=jax.vjp(compiled,jnp.asarray(x))
    reverse=np.asarray(pullback(jnp.asarray(cotangent))[0])
"""
H1_BLOCK = """    def jvp_evaluate(z, v):
        return jax.jvp(function, (z,), (v,))

    def vjp_evaluate(z, c):
        y, pullback = jax.vjp(function, z)
        return y, pullback(c)[0]

    _,action=jax.jit(jvp_evaluate,compiler_options=ci.COMPILER_OPTIONS)(
        jnp.asarray(x),jnp.asarray(direction))
    _,reverse_array=jax.jit(vjp_evaluate,compiler_options=ci.COMPILER_OPTIONS)(
        jnp.asarray(x),jnp.asarray(cotangent))
    reverse=np.asarray(reverse_array)
"""


def binary_write(filename, data):
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    checked(filename, hashlib.sha256(data).hexdigest(), len(data))


def harness(root):
    manifest = read(root / H1_MANIFEST)
    checked(root / H1_TEST, manifest["test_sha256"])
    return dict(version="H1", manifest_path=str(root / H1_MANIFEST),
                manifest_sha256=sha(root / H1_MANIFEST),
                test_path=str(root / H1_TEST), test_sha256=manifest["test_sha256"])


def make_h1(root):
    original = (root / "B0/source/hf_repo" / TEST).read_bytes()
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    before = H0_BLOCK.encode().replace(b"\n", newline)
    after = H1_BLOCK.encode().replace(b"\n", newline)
    require(original.count(before) == 1 and after not in original, "H0 exact four-line block differs")
    revised = original.replace(before, after, 1)
    require(revised.replace(after, before, 1) == original, "H1 reverse replacement did not recover H0 bytes")
    old_tree, new_tree = ast.parse(original), ast.parse(revised)
    old_tests = [n.name for n in old_tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    new_tests = [n.name for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    require(old_tests == new_tests and len(new_tests) == 9, "H1 original nine-test inventory differs")
    binary_write(root / H1_TEST, revised)
    patch = "".join(difflib.unified_diff(original.decode().splitlines(True), revised.decode().splitlines(True),
                                        fromfile="H0/" + TEST, tofile="H1/" + TEST))
    binary_write(root / "H1/patch.diff", patch.encode())
    proof = dict(schema="hf-jit-ad-harness-proof-1", before_sha256=hashlib.sha256(original).hexdigest(),
                 after_sha256=hashlib.sha256(revised).hexdigest(), reverse_restores_all_original_bytes=True,
                 change="only the four-line strict JIT/AD block; all assertions and eight other tests unchanged",
                 test_names=new_tests, scientific_execution=False)
    write(root / "H1/proof.json", proof)
    source = root / "B0/source/hf_repo" / TEST
    write(root / H1_MANIFEST, dict(schema="hf-jit-ad-harness-1", version="H1", test_path=H1_TEST,
        test_sha256=sha(root / H1_TEST), before_sha256=sha(source),
        base_manifest_sha256=sha(root / "input_manifest.json"), test_names=new_tests,
        files=[dict(path=H1_TEST, source=str(source), bytes=len(revised), sha256=sha(root / H1_TEST),
                    source_bytes=len(original), source_sha256=sha(source), role="H1_derivation_from_H0")],
        proof_artifacts={"H1/proof.json": sha(root / "H1/proof.json"),
                         "H1/patch.diff": sha(root / "H1/patch.diff")}))


def freeze_history(root, repo):
    old = repo / HISTORY
    binding = read(checked(old / "receipt_binding.json", HISTORY_BINDING_SHA))
    fixed = {
        "plan.json": binding["plan_sha256"], "input_manifest.json": binding["input_manifest_sha256"],
        "execution_receipt.json": binding["receipt_sha256"], "output_sha256.json": binding["output_manifest_sha256"],
        "events/P6_seal.ndjson": binding["seal_event_sha256"], "logs/P6_seal.log": binding["seal_log_sha256"],
        "receipt_binding.json": HISTORY_BINDING_SHA,
    }
    output_index = read(checked(old / "output_sha256.json", binding["output_manifest_sha256"]))
    for name in ("events/P2_baseline.ndjson", "logs/P2_baseline.log", "results/P2_baseline/pytest.xml",
                 "results/controls/summary.json", "events/P2_controls.ndjson", "logs/P2_controls.log"):
        require(name in output_index, "historical failure missing from output manifest")
        fixed[name] = output_index[name]
    require(read(checked(old / "execution_receipt.json", binding["receipt_sha256"]))["status"] == "execution_failure",
            "historical receipt status differs")
    return [copy_row(root, old / name, "provenance/s0_ready_001/" + name, expected=digest,
                     role="immutable_H0_failure_evidence") for name, digest in sorted(fixed.items())]


def prepare(root, repo, events):
    require(not (root / "input_manifest.json").exists() and not (root / "B0").exists()
            and not (root / "H1").exists() and not (root / "C1").exists(), "preparation is write-once")
    old = repo / OLD_VERSION
    original = read(checked(old / "input_manifest.json", OLD_MANIFEST_SHA))
    records = {}
    for row in original["files"]:
        relative(row["path"])
        require(row["path"] not in records, "duplicate B0 manifest path")
        records[row["path"]] = row
    fixed = {"source/hf_repo/pyproject.toml", "source/hf_repo/" + TEST,
             "source/hf_repo/tests/test_windows_owned_process.py"}
    selected = sorted(n for n in records if n.startswith("source/hf_repo/src/") or n in fixed)
    require(fixed.issubset(selected), "B0 required files missing")
    disk = {p.relative_to(old).as_posix() for p in (old / "source/hf_repo/src").rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    require(disk == {n for n in selected if n.startswith("source/hf_repo/src/")}, "B0 source inventory differs")
    rows = [copy_row(root, old / "input_manifest.json", "provenance/b0_input_manifest.json",
                     expected=OLD_MANIFEST_SHA, role="old_snapshot_manifest")]
    for name in selected:
        row = records[name]
        rows.append(copy_row(root, old / name, "B0/" + name, expected=row["sha256"], size=row["bytes"],
                             role="immutable_B0_H0"))
    for name in AUX_FILES:
        rows.append(copy_row(root, repo / name, "aux/" + name, role="diagnostic_auxiliary"))
    installed = path(sys.executable).parent.parent / "Lib/site-packages/jax"
    for name, digest in RUNTIME_FILES.items():
        rows.append(copy_row(root, installed / name, "aux/runtime/jax/" + name, expected=digest,
                             role="installed_primary_JAX_source"))
    rows.extend(freeze_history(root, repo))
    output_path = repo / MANUFACTURED / "output_sha256.json"
    output_index = read(output_path)
    for name in ("inputs.npz", "input_freeze.json"):
        key = "unit__near_rotation/" + name
        rows.append(copy_row(root, repo / MANUFACTURED / key, "data/" + name,
                             expected=output_index[key], role="original_unit_near_rotation"))
    rows.append(copy_row(root, output_path, "data/original_output_sha256.json", role="original_output_manifest"))
    freeze = read(root / "data/input_freeze.json")
    require(freeze["case"] == "unit__near_rotation" and freeze["input_sha256"] == INPUT_SHA, "input freeze differs")
    checked(root / "data/inputs.npz", INPUT_SHA)
    canonical = {}
    canonical_names = sorted(n.removeprefix("source/hf_repo/") for n in selected
                             if n.startswith("source/hf_repo/src/") or n == "source/hf_repo/"+TEST)
    canonical_disk = {p.relative_to(repo / "hf_repo").as_posix() for p in (repo / "hf_repo/src").rglob("*")
                      if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    require(canonical_disk == {n for n in canonical_names if n.startswith("src/")}, "canonical science inventory differs from B0")
    for name in canonical_names:
        source = root / "B0/source/hf_repo" / name
        checked(repo / "hf_repo" / name, sha(source))
        canonical[name] = dict(path=str(repo / "hf_repo" / name), baseline_sha256=sha(source))
    write(root / "input_manifest.json", dict(schema="hf-jit-ad-preparation-inputs-1", created_utc=utc(),
        files=rows, baseline_manifest_sha256=OLD_MANIFEST_SHA, canonical_files=canonical,
        frozen_input_case="unit__near_rotation", direction=0, scientific_admission=False,
        python=dict(executable=sys.executable, version=sys.version),
        scope="B0/H0 immutable; H1 independent; C1 conditional and no canonical sync until A4"))
    make_h1(root)
    result = verify_all(root, repo)
    events.emit("preparation_complete", input_manifest_sha256=sha(root / "input_manifest.json"), harness=harness(root))
    return dict(status="pass", files=len(rows), copied_bytes=sum(r["bytes"] for r in rows), source_verification=result)


def selected_expected(root, version):
    require(version in ("B0", "C1"), "unknown science identity")
    manifest = root / ("C1/source_manifest.json" if version == "C1" else "input_manifest.json")
    return dict(schema="hf-jit-ad-selected-source-1", version=version, source=str(root / version / "source/hf_repo"),
                source_manifest=str(manifest), source_manifest_sha256=sha(manifest),
                harness=harness(root), scientific_admission=False)


def select(root, version):
    value = selected_expected(root, version)
    write(root / "selected_source.json", value)
    return value


def sync_state(root, manifest):
    """Only durable per-file verified rows change expected canonical identity."""
    expected = {n:r["baseline_sha256"] for n,r in manifest["canonical_files"].items()}
    journal = root / "sync_journal.ndjson"
    rows = []
    intents, verified = {}, {}
    if journal.exists():
        selected = read(root / "selected_source.json")
        require(selected == selected_expected(root, selected["version"]), "sync selected identity differs")
        allowed = {TEST: root / H1_TEST}
        if selected["version"] == "C1":
            allowed[ARITHMETIC] = root / "C1/source/hf_repo" / ARITHMETIC
        started = read(root / "sync_started.json")
        require(started["selected"] == selected and set(started["allowed_files"]) == set(allowed),
                "sync authorization record differs")
        checked(root / "events/A4_arithmetic.ndjson", started["A4_event_sha256"])
        raw = journal.read_bytes()
        require(raw.endswith(b"\n"), "sync journal is truncated")
        rows = [json.loads(line) for line in raw.splitlines()]
        for index, row in enumerate(rows, 1):
            require(row["sequence"] == index and row["path"] in expected, "sync journal identity/sequence differs")
            name = row["path"]
            require(name in allowed and path(row["source"]) == allowed[name]
                    and row["new_sha256"] == sha(allowed[name])
                    and path(row["destination"]) == path(manifest["canonical_files"][name]["path"]),
                    "sync row does not describe authorized derived file")
            if row["event"] == "sync_intent":
                require(name not in intents and row["old_sha256"] == expected[name], "duplicate/invalid sync intent")
                intents[name] = row
            elif row["event"] == "sync_verified":
                require(name in intents and name not in verified and all(row[k] == intents[name][k]
                    for k in ("old_sha256", "new_sha256", "source", "destination")), "sync verification lacks matching intent")
                checked(row["source"], row["new_sha256"])
                expected[name] = row["new_sha256"]
                verified[name] = row
            else:
                require(False, "unknown sync journal event")
    receipt = root / "sync_receipt.json"
    if receipt.exists():
        result = read(receipt)
        require(result["status"] == "pass" and result["journal_sha256"] == sha(journal)
                and set(result["files"]) == set(verified) == set(intents)
                and set(verified) == set(allowed) and result["selected"] == selected
                and result["A4_event_sha256"] == started["A4_event_sha256"]
                and result["canonical_sha256"] == expected, "sync receipt does not close journal")
    return expected, dict(intents=len(intents), verified=len(verified),
                         incomplete_intents=sorted(set(intents)-set(verified)), complete_receipt=receipt.exists())


def verify_all(root, repo):
    manifest = read(root / "input_manifest.json")
    count = verify_rows(root, manifest["files"])
    h1 = read(root / H1_MANIFEST)
    require(h1["base_manifest_sha256"] == sha(root / "input_manifest.json"), "H1 base manifest differs")
    verify_rows(root, h1["files"])
    for name,digest in h1["proof_artifacts"].items():
        checked(bound(root, name), digest)
    require(h1["test_sha256"] == sha(root / H1_TEST), "H1 test identity differs")
    c1_count = 0
    c1_path = root / "C1/source_manifest.json"
    if c1_path.exists():
        c1 = read(c1_path)
        require(c1["base_manifest_sha256"] == sha(root / "input_manifest.json")
                and c1["harness_manifest_sha256"] == sha(root / H1_MANIFEST), "C1 derivation binding differs")
        c1_count = verify_rows(root, c1["files"])
        for name,digest in c1["proof_artifacts"].items():
            checked(bound(root, name), digest)
    selection = root / "selected_source.json"
    if selection.exists():
        current = read(selection)
        require(current == selected_expected(root, current["version"]), "selected source/harness identity differs")
    expected, sync = sync_state(root, manifest)
    for name,digest in expected.items():
        checked(repo / "hf_repo" / name, digest)
    actual_src = {p.relative_to(repo / "hf_repo").as_posix() for p in (repo / "hf_repo/src").rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    require(actual_src == {n for n in expected if n.startswith("src/")}, "canonical science inventory changed")
    if (root / "sync_started.json").exists():
        require(sync["complete_receipt"] and not sync["incomplete_intents"],
                "canonical synchronization started but did not durably close")
    return dict(status="pass", input_files=count, H1_files=1, C1_files=c1_count, missing=0, mismatches=0,
                canonical_sha256=expected, sync=sync, input_manifest_sha256=sha(root / "input_manifest.json"),
                harness_manifest_sha256=sha(root / H1_MANIFEST))


def pytest_records(root, phase, version, manifest_sha, required_names):
    filename = root / "events" / (phase + ".ndjson")
    raw = filename.read_bytes()
    require(raw.endswith(b"\n"), "pytest event stream truncated", ClassificationFailure)
    rows = [json.loads(line) for line in raw.splitlines()]
    require(rows, "empty pytest events", ClassificationFailure)
    for index,row in enumerate(rows, 1):
        require(row["schema"] == "hf-s0-event-1" and row["sequence"] == index
                and row["phase"] == phase and row["version"] == version
                and row["source_manifest_sha256"] == manifest_sha
                and row["harness_id"] == "H1" and row["harness_manifest_sha256"] == sha(root / H1_MANIFEST),
                "pytest event identity differs", ClassificationFailure)
    require(not any(r["event"] in ("pytest_internal_error", "pytest_interrupted") for r in rows)
            and not any(r["event"] in ("collection_report", "collection_finish") and r.get("outcome") != "passed"
                        for r in rows), "pytest collection/internal error", ClassificationFailure)
    finish = [r for r in rows if r["event"] == "session_finish"]
    collection = [r for r in rows if r["event"] == "collection_finish"]
    configuration = [r for r in rows if r["event"] == "session_configured"]
    require(len(finish) == len(collection) == len(configuration) == 1 and rows[-1] == finish[0]
            and finish[0]["testscollected"] == len(required_names)
            and collection[0]["collected"] == len(required_names), "pytest session is incomplete", ClassificationFailure)
    require(configuration[0]["maxfail"] == 1 and path(configuration[0]["rootpath"]) == root / "H1"
            and path(configuration[0]["invocation_dir"]) == root,
            "pytest rootdir or fail-fast contract differs", ClassificationFailure)
    reports = [r for r in rows if r["event"] == "test_report"]
    calls = [r for r in reports if r["when"] == "call"]
    require(len(calls) == len(required_names), "pytest did not execute each required call", ClassificationFailure)
    suffix = lambda r: r["nodeid"].replace("\\", "/").split("::")[-1]
    require({suffix(r) for r in calls} == set(required_names) and len({r["nodeid"] for r in calls}) == len(calls)
            and {n.replace("\\", "/").split("::")[-1] for n in collection[0]["nodeids"]} == set(required_names),
            "pytest required test inventory differs", ClassificationFailure)
    for row in reports:
        require(suffix(row) in required_names and path(row["source_path"]) == root / H1_TEST
                and path(row["test_file_path"]) == root / H1_TEST,
                "pytest report was not generated from bound H1", ClassificationFailure)
        if row["when"] != "call":
            require(row["outcome"] == "passed", "pytest setup/teardown failed/skipped", ClassificationFailure)
        require(not row.get("wasxfail"), "xfail is not an allowed pass", ClassificationFailure)
    for name in required_names:
        subset = [r for r in reports if suffix(r) == name]
        require(sorted(r["when"] for r in subset) == ["call", "setup", "teardown"],
                "missing or duplicate pytest reports", ClassificationFailure)
    return calls, finish[0], sha(filename)


def baseline_result(root):
    calls, finish, digest = pytest_records(root, "A3_baseline", "B0", sha(root / "input_manifest.json"),
                                         [TARGET_NODE.split("::")[-1]])
    call = calls[0]
    if call["outcome"] == "passed":
        require(finish["exitstatus"] == 0 and finish["testsfailed"] == 0, "passing A3 did not exit cleanly", ClassificationFailure)
        return dict(status="pass", event_sha256=digest, nodeid=call["nodeid"])
    require(call["outcome"] == "failed" and finish["exitstatus"] == 1 and finish["testsfailed"] == 1
            and call.get("exception_type") == "AssertionError" and is_declared_transpose(call["exception"]),
            "A3 did not reproduce the declared terminal AD XOR AssertionError", ClassificationFailure)
    return dict(status="declared_transpose_failure", event_sha256=digest, nodeid=call["nodeid"], error=call["exception"])


def controls_result(root):
    filename = root / "results/controls/summary.json"
    summary = read(filename)
    require(summary["schema"] == "hf-jit-ad-preparation-probe-1" and summary["mode"] == "controls"
            and summary["source_manifest_sha256"] == sha(root / "input_manifest.json")
            and path(summary["source"]) == root / "B0/source/hf_repo" and summary["harness"] == harness(root)
            and summary["status"] in ("pass", "diagnostic_observation"), "controls identity/status differs", ClassificationFailure)
    eager_keys = {"primal", "jvp", "vjp_construct", "pullback", "closed_form", "duality"}
    stage_keys = {"trace", "lower", "compile", "execute_synchronized", "transfer", "check"}
    observed = []
    controls = summary["controls"]
    require(set(controls) == {"none", "joint", "separate"}, "control kinds differ", ClassificationFailure)
    for kind in ("none", "joint", "separate"):
        value = controls[kind]
        require(set(value) == {"eager", "strict", "linearized_jaxpr"}, "control modes differ", ClassificationFailure)
        require(value["linearized_jaxpr"]["status"] == "pass", "raw linearized graph missing", ClassificationFailure)
        eager, strict = value["eager"], value["strict"]
        require(set(eager) == eager_keys and set(strict) == {"primal", "forward", "reverse", "closed_form", "duality"},
                "control stage inventory differs", ClassificationFailure)
        for name in ("primal", "forward", "reverse"):
            require(set(strict[name]) == stage_keys, "strict stage inventory differs", ClassificationFailure)
        must_pass = [eager[n] for n in ("primal", "jvp", "closed_form")] + [strict["closed_form"]]
        must_pass += [v for n in ("primal", "forward") for v in strict[n].values()]
        require(all(v["status"] == "pass" for v in must_pass), "control primal/forward/closed form failed", ClassificationFailure)
        if kind != "joint":
            require(all(v["status"] == "pass" for v in eager.values())
                    and all(v["status"] == "pass" for v in strict["reverse"].values())
                    and strict["duality"]["status"] == "pass", "none/separate did not fully pass", ClassificationFailure)
            continue
        failed = [n for n in ("vjp_construct", "pullback") if eager[n]["status"] == "failed"]
        if failed:
            require(len(failed) == 1 and is_declared_transpose(eager[failed[0]]["error"]), "joint eager exception not declared", ClassificationFailure)
            require(eager["duality"]["status"] == "not_run"
                    and eager["pullback" if failed[0] == "vjp_construct" else "vjp_construct"]["status"]
                        == ("not_run" if failed[0] == "vjp_construct" else "pass"), "joint eager dependency sequence differs", ClassificationFailure)
            observed.append(dict(mode="eager", stage=failed[0], error=eager[failed[0]]["error"]))
        else:
            require(all(eager[n]["status"] == "pass" for n in ("vjp_construct", "pullback", "duality")), "joint eager incomplete", ClassificationFailure)
        reverse = strict["reverse"]
        if reverse["trace"]["status"] == "failed":
            require(is_declared_transpose(reverse["trace"]["error"])
                    and all(reverse[n]["status"] == "not_run" for n in stage_keys - {"trace"})
                    and strict["duality"]["status"] == "not_run", "joint strict failure/dependencies differ", ClassificationFailure)
            observed.append(dict(mode="strict", stage="reverse.trace", error=reverse["trace"]["error"]))
        else:
            require(all(v["status"] == "pass" for v in reverse.values()) and strict["duality"]["status"] == "pass",
                    "joint strict incomplete or unexpected failure", ClassificationFailure)
    require(summary["status"] == ("diagnostic_observation" if observed else "pass"), "controls summary masks outcomes", ClassificationFailure)
    return dict(status="pass", summary_sha256=sha(filename), joint_failures=observed, scientific_admission=False)


def classify_and_fix(root, repo, events):
    require(not (root / "classification_started.json").exists(), "classification/repair cannot be retried")
    verify_all(root, repo)
    write(root / "classification_started.json", dict(utc=utc(), allowed_repairs=1))
    baseline, controls = baseline_result(root), controls_result(root)
    record = dict(schema="hf-jit-ad-failure-classification-1", baseline=baseline, controls=controls,
                  base_manifest_sha256=sha(root / "input_manifest.json"), harness=harness(root), scientific_admission=False)
    if baseline["status"] == "pass":
        record.update(status="baseline_not_reproduced", repair_performed=False)
        write(root / "failure_classification.json", record)
        return dict(status="pass", classification=record["status"], selected=select(root, "B0"))
    require(controls["joint_failures"], "joint did not reproduce declared failure", ClassificationFailure)
    signature = lambda error: (path(error["terminal"]["filename"]),) + tuple(error["terminal"][key] for key in
        ("module", "function", "lineno", "code_firstlineno", "source_line", "source_sha256"))
    require(any(signature(item["error"]) == signature(baseline["error"]) for item in controls["joint_failures"]),
            "baseline and joint terminal XOR evidence do not agree", ClassificationFailure)
    record.update(status="declared_derivative_interface_defect", repair_authorized=True,
                  repair_scope="only derivative split barriers; freeze C1 without canonical sync")
    write(root / "failure_classification.json", record)
    source = root / "B0/source/hf_repo"
    original = (source / ARITHMETIC).read_bytes()
    revised, primal_hashes, patch = repaired_bytes(original)
    rows = []
    for item in sorted(source.rglob("*")):
        if not item.is_file():
            continue
        name = item.relative_to(source).as_posix()
        target = root / "C1/source/hf_repo" / name
        data = revised if name == ARITHMETIC else item.read_bytes()
        binary_write(target, data)
        row = dict(path=target.relative_to(root).as_posix(), source=str(item), bytes=len(data),
                   sha256=sha(target), source_sha256=sha(item), source_bytes=item.stat().st_size,
                   role="C1_derivation_from_B0")
        rows.append(row)
        append(root / "prepare_journal.ndjson", dict(event="C1_file_verified", utc=utc(), **row))
    binary_write(root / "C1/patch.diff", patch.encode())
    write(root / "C1/repair_proof.json", dict(schema="hf-jit-ad-derivative-repair-proof-1",
        before_sha256=hashlib.sha256(original).hexdigest(), after_sha256=hashlib.sha256(revised).hexdigest(),
        changed_functions=["_linear_pair", "_jax_product_jvp"], added_function="_derivative_mul",
        primal_helper_sha256=primal_hashes, unchanged_remainder_reconstruction=True,
        classification_sha256=sha(root / "failure_classification.json"), canonical_sync_performed=False,
        original_H0_unchanged=True, harness_manifest_sha256=sha(root / H1_MANIFEST)))
    write(root / "C1/source_manifest.json", dict(schema="hf-jit-ad-C1-source-1", files=rows,
        base_manifest_sha256=sha(root / "input_manifest.json"), harness_manifest_sha256=sha(root / H1_MANIFEST),
        arithmetic_sha256=hashlib.sha256(revised).hexdigest(),
        proof_artifacts={"C1/repair_proof.json": sha(root / "C1/repair_proof.json"), "C1/patch.diff": sha(root / "C1/patch.diff")}))
    selected = select(root, "C1")
    verify_all(root, repo)
    events.emit("conditional_C1_frozen", selected=selected, canonical_sync_performed=False)
    return dict(status="pass", selected=selected, classification=record["status"])


def sync(root, repo, events):
    require(not (root / "sync_started.json").exists(), "canonical sync cannot be retried")
    verify_all(root, repo)
    selected = read(root / "selected_source.json")
    h1 = read(root / H1_MANIFEST)
    calls, finish, event_sha = pytest_records(root, "A4_arithmetic", selected["version"],
        selected["source_manifest_sha256"], h1["test_names"])
    require(finish["exitstatus"] == 0 and finish["testsfailed"] == 0 and len(calls) == 9
            and all(r["outcome"] == "passed" for r in calls), "A4 nine H1 calls did not all pass", ClassificationFailure)
    write(root / "sync_started.json", dict(utc=utc(), selected=selected, A4_event_sha256=event_sha,
        allowed_files=[TEST] + ([ARITHMETIC] if selected["version"] == "C1" else [])))
    manifest = read(root / "input_manifest.json")
    replacements = [(TEST, root / H1_TEST)]
    if selected["version"] == "C1":
        replacements.append((ARITHMETIC, root / "C1/source/hf_repo" / ARITHMETIC))
    count = 0
    for name, source in replacements:
        destination = repo / "hf_repo" / name
        before = manifest["canonical_files"][name]["baseline_sha256"]
        after = sha(source)
        checked(destination, before)
        record = dict(path=name, source=str(source), destination=str(destination),
                      old_sha256=before, new_sha256=after)
        count += 1
        append(root / "sync_journal.ndjson", dict(sequence=count, event="sync_intent", utc=utc(), **record))
        temporary = destination.with_name(destination.name + ".jit-ad-sync.tmp")
        binary_write(temporary, source.read_bytes())
        checked(temporary, after)
        checked(destination, before)
        os.replace(temporary, destination)
        checked(destination, after)
        count += 1
        append(root / "sync_journal.ndjson", dict(sequence=count, event="sync_verified", utc=utc(), **record))
        events.emit("canonical_file_sync_verified", **record)
    expected, state = sync_state(root, manifest)
    write(root / "sync_receipt.json", dict(schema="hf-jit-ad-sync-1", status="pass", utc=utc(),
        selected=selected, files=[n for n,_ in replacements], canonical_sha256=expected,
        journal_sha256=sha(root / "sync_journal.ndjson"), A4_event_sha256=event_sha,
        scientific_admission=False, default_kernel_changed=False))
    return dict(status="pass", source_verification=verify_all(root, repo))


def resource_svg(resources):
    rows = resources["phases"]
    height = 90 + len(rows) * 42
    largest_time = max([float(r.get("elapsed_seconds", 0)) for r in rows] + [1.])
    largest_rss = max([float(r.get("peak_tree_rss_bytes", 0)) for r in rows] + [1.])
    text = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/><g font-family="Arial,sans-serif" font-size="12">',
        '<text x="20" y="24">JIT/AD-1 recorded phases BEFORE A7; final parent receipt includes A7; no scientific admission</text>',
        '<text x="390" y="52">Wall seconds</text><text x="790" y="52">Sampled process-tree RSS (MiB)</text>']
    for i,row in enumerate(rows):
        y = 75+i*42
        seconds, rss = float(row.get("elapsed_seconds",0)), float(row.get("peak_tree_rss_bytes",0))
        clean = row.get("cleanup_verified",False)
        status = "exit0/clean" if row.get("returncode") == 0 and clean else str(row.get("reason","unknown"))
        color = "#356c9b" if row.get("returncode") == 0 and clean else "#a84040"
        text.extend((f'<text x="20" y="{y+12}">{escape(row["name"])} | {escape(status)}</text>',
            f'<rect x="390" y="{y}" width="{280*seconds/largest_time:.3f}" height="15" fill="{color}"/>',
            f'<text x="680" y="{y+12}">{seconds:.3f}</text>',
            f'<rect x="790" y="{y}" width="{230*rss/largest_rss:.3f}" height="15" fill="#497f65"/>',
            f'<text x="1040" y="{y+12}">{rss/1024**2:.2f}</text>'))
    return "".join(text) + '</g></svg>\n'


def stage_timings(root, resources):
    cutoff = read(root / "plan.json")["start_monotonic"] + resources["total_elapsed_seconds"]
    rows, bindings = [], {}
    for mode,phase in (("force","A5_force"),("tangent","A6_tangent")):
        summary_path, events_path = root / "results" / mode / "summary.json", root / "events" / (phase+".ndjson")
        if not summary_path.exists():
            rows.append(dict(mode=mode,stage=mode,status="not_reached",seconds=None,timing_basis="no saved probe summary"))
            continue
        summary = read(summary_path)
        bindings[summary_path.relative_to(root).as_posix()] = sha(summary_path)
        starts = {}
        if events_path.exists():
            bindings[events_path.relative_to(root).as_posix()] = sha(events_path)
            lines = events_path.read_bytes().splitlines(keepends=True)
            if lines and not lines[-1].endswith(b"\n"):
                lines.pop()
                rows.append(dict(mode=mode,stage="event_log_tail",status="truncated_tail_preserved",seconds=None,
                                 timing_basis="partial last line excluded from timing only"))
            for line in lines:
                event = json.loads(line)
                if event["event"] == "stage_started":
                    starts[event["stage"]] = event["monotonic"]
        observed = set()
        for step in summary["steps"]:
            stage,state = step["stage"],step["status"]
            observed.add(stage)
            if state in ("pass","failed") and "elapsed_seconds" in step:
                seconds,basis = step["elapsed_seconds"],"complete saved record"
            elif state == "running" and stage in starts:
                state,seconds,basis = "open_at_stop",max(0.,cutoff-starts[stage]),"observation upper interval includes cleanup/dispatch; NOT completed duration"
            else:
                seconds,basis = None,"no complete saved duration"
            rows.append(dict(mode=mode,stage=stage,status=state,seconds=seconds,timing_basis=basis))
        for label in ((mode,"residual_jvp") if mode == "tangent" else (mode,)):
            for suffix in ("trace","lower","compile","execute_synchronized","transfer","save_output","export_ir"):
                stage = label+"."+suffix
                if stage not in observed:
                    rows.append(dict(mode=mode,stage=stage,status="not_reached",seconds=None,timing_basis="no saved started stage"))
    return dict(schema="hf-jit-ad-stage-timings-1",rows=rows,source_sha256=bindings,
                observation_cutoff_monotonic=cutoff,scope="saved A5/A6 only; no A7 or scientific accuracy claim")


def seal(root, repo, events):
    try:
        preservation = verify_all(root,repo)
    except Exception as error:
        # Failure is still evidence. Do not infer sync success from a new
        # destination hash, and do not let an interrupted intent hide payloads.
        preservation = failed_preservation(root, repo, error)
    write(root / "source_preservation.json",preservation)
    resources = read(root / "resources.json")
    binary_write(root / "resources.svg",resource_svg(resources).encode())
    timings = stage_timings(root,resources)
    write(root / "stage_timings.json",timings)
    graph = stages_svg(timings).replace("S0 P4/P5", "JIT/AD-1 A5/A6")
    binary_write(root / "stages.svg",graph.encode())
    phase = os.environ["HF_S0_PHASE"]
    excluded = {"output_sha256.json","receipt_binding.json","execution_receipt.json","ledger.json",
                "logs/"+phase+".log","events/"+phase+".ndjson"}
    result = dict(schema="hf-jit-ad-evidence-worker-1",action="seal",
        status="pass" if preservation["status"] == "pass" else "evidence_failure",scientific_admission=False,
        source_preservation=preservation, resources_scope="before A7 only; parent final receipt includes A7",
        excluded_live_or_final_bindings=sorted(excluded))
    write(root / "results/seal/summary.json",result)
    write(root / "output_sha256.json",{p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob("*"))
        if p.is_file() and p.relative_to(root).as_posix() not in excluded})
    events.emit("seal_complete",output_manifest_sha256=sha(root / "output_sha256.json"))
    return result


def failed_preservation(root, repo, error):
    """Record actual bytes after a failed strict verify; never bless a repair."""
    problems, inventories = [], []
    for manifest_name in ("input_manifest.json", H1_MANIFEST, "C1/source_manifest.json"):
        manifest_path = root / manifest_name
        if not manifest_path.exists():
            inventories.append(dict(manifest=manifest_name, status="absent"))
            continue
        try:
            manifest = read(manifest_path)
            inventories.append(dict(manifest=manifest_name, sha256=sha(manifest_path), files=len(manifest["files"])))
            for row in manifest["files"]:
                for side, filename, digest, size in (
                    ("copy", bound(root, row["path"]), row["sha256"], row["bytes"]),
                    ("source", path(row["source"]), row.get("source_sha256", row["sha256"]),
                     row.get("source_bytes", row["bytes"]))):
                    try:
                        checked(filename, digest, size)
                    except Exception as problem:
                        problems.append(dict(manifest=manifest_name, path=row["path"], side=side,
                            error=type(problem).__name__+": "+str(problem),
                            actual_sha256=sha(filename) if filename.is_file() else None))
            for name,digest in manifest.get("proof_artifacts",{}).items():
                try:
                    checked(bound(root,name),digest)
                except Exception as problem:
                    problems.append(dict(manifest=manifest_name,path=name,side="proof",error=str(problem)))
        except Exception as problem:
            problems.append(dict(manifest=manifest_name,error=type(problem).__name__+": "+str(problem)))
    canonical = {}
    try:
        canonical_names = read(root / "input_manifest.json")["canonical_files"]
    except Exception:
        canonical_names = (TEST,ARITHMETIC)
    for name in canonical_names:
        filename = repo / "hf_repo" / name
        canonical[name] = dict(path=str(filename), exists=filename.is_file(),
                               actual_sha256=sha(filename) if filename.is_file() else None)
    journal = root / "sync_journal.ndjson"
    pending = dict(exists=journal.exists(), receipt_exists=(root / "sync_receipt.json").exists())
    if journal.exists():
        raw = journal.read_bytes()
        pending.update(sha256=sha(journal), complete_last_line=raw.endswith(b"\n"))
        try:
            lines = raw.splitlines(keepends=True)
            if lines and not lines[-1].endswith(b"\n"):
                lines.pop()
            rows = [json.loads(line) for line in lines]
            pending["durable_rows"] = rows
            intended = {r["path"] for r in rows if r.get("event") == "sync_intent"}
            verified = {r["path"] for r in rows if r.get("event") == "sync_verified"}
            pending["intents_without_verified"] = sorted(intended-verified)
        except Exception as problem:
            pending["parse_error"] = str(problem)
    return dict(status="evidence_failure", strict_verify_error=dict(type=type(error).__name__,message=str(error)),
        inventories=inventories, file_problems=problems, canonical_actual=canonical, sync_observation=pending,
        limitation="actual new bytes never substitute for a durable verified record or complete sync receipt",
        scientific_admission=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--repo",type=Path,required=True)
    parser.add_argument("--action",choices=("prepare","verify","validate_controls","classify_and_fix","sync","seal"),required=True)
    args = parser.parse_args()
    root,repo = path(args.root),path(args.repo)
    require(root != repo and not repo.is_relative_to(root), "evidence root must not contain repository")
    root.mkdir(parents=True,exist_ok=True)
    output = root / "results" / args.action
    if args.action == "verify":
        number = 1
        while (root / "results" / f"verify_{number:03d}").exists():
            number += 1
        output = root / "results" / f"verify_{number:03d}"
    events,begin = EventLog(),time.perf_counter()
    try:
        require(not output.exists(), "worker result already exists")
        events.emit("worker_started",action=args.action)
        if args.action == "prepare":
            result = prepare(root,repo,events)
        elif args.action == "verify":
            result = verify_all(root,repo)
        elif args.action == "validate_controls":
            verify_all(root,repo)
            result = controls_result(root)
        elif args.action == "classify_and_fix":
            result = classify_and_fix(root,repo,events)
        elif args.action == "sync":
            result = sync(root,repo,events)
        else:
            result = seal(root,repo,events)
            return 0 if result["status"] == "pass" else 2
        write(output / "summary.json",dict(schema="hf-jit-ad-evidence-worker-1",action=args.action,
            elapsed_seconds=time.perf_counter()-begin,**result))
        events.emit("worker_finished",action=args.action,status=result["status"])
        return 0
    except Exception as error:
        failure = dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        if not (output / "summary.json").exists():
            write(output / "summary.json",dict(schema="hf-jit-ad-evidence-worker-1",action=args.action,
                status="classification_not_supported" if isinstance(error,ClassificationFailure) else "evidence_failure",
                elapsed_seconds=time.perf_counter()-begin,scientific_admission=False,error=failure))
        events.emit("worker_failed",action=args.action,**failure)
        return 2
    finally:
        events.close()


if __name__ == "__main__":
    raise SystemExit(main())
