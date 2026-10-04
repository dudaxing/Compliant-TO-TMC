"""Standard-library evidence workers for the separately authorized S0 card.

No scientific module is imported. The parent owns the continuous time/RSS
budget and every invocation; this worker does not launch subprocesses.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import difflib
import hashlib
from html import escape
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import time
import traceback

from s0_event_log import EventLog


OLD_VERSION = "hf4_c2_stable_f_validation/invariants_hu_campaign_001/version_002"
OLD_MANIFEST_SHA = "e8877ce1713dbb648a2d6135dff2f15a7d3618a4fcb0591321824928644e17f5"
MANUFACTURED = "hf4_c2_independent_recheck_20260927/manufactured_001/results"
INPUT_SHA = "2ba110b878186e52996c25f4aad44cb81858be15303c21579c4f5e8ccc013448"
ARITHMETIC = "src/hf_eval/compensated_invariants.py"
TARGET_NODE = "tests/test_compensated_invariants.py::test_physical_jvp_and_vjp_match_closed_form_first_derivatives"
AUX_FILES = (
    "hf_repo/scripts/run_s0_preparation.py",
    "hf_repo/scripts/s0_preparation_evidence.py",
    "hf_repo/scripts/probe_s0_preparation.py",
    "hf_repo/scripts/s0_event_log.py",
    "hf_repo/scripts/hf_s0_pytest_events.py",
    "hf_repo/scripts/windows_owned_process.py",
    "hf_repo/tests/test_s0_event_logging.py",
    "docs/HF4_C2_NEAR_ROTATION_DIAGNOSTIC_20260928.md",
    "docs/HF4_C2_INVARIANTS_HU_ARITHMETIC.md",
    "docs/CURRENT_STATUS.md",
)
JAX_FILES = {
    "version.py": "f8d782855b46304fd9cbe92bc2cef17cbf5cd70360017046f40ad539bf886eab",
    "_src/api.py": "c21207c0d6bd4983c72f2abe858f29da160b5705a2b0e12b689c260d1d953bdc",
    "_src/interpreters/ad.py": "3e54a02d0e2f45c42e0ed0bf9489ab58b6bcf360653539a44864a211b9d601b4",
    "_src/interpreters/partial_eval.py": "e494dab076a6cdf344f837ac81867ceac435efb982f62d1bd339f744ee61a46b",
    "_src/lax/lax.py": "63d0e3fe58e7ad91aaa8b516ca13d09d7434f26aec51c0e283dac3f7037fb478",
}


class EvidenceFailure(ValueError):
    pass


class ClassificationFailure(ValueError):
    pass


def require(ok, message, kind=EvidenceFailure):
    if not ok:
        raise kind(message)


def path(value):
    """Canonical absolute path with Windows long-path support, before I/O."""
    text = os.path.abspath(os.fspath(value))
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        text = "\\\\?\\UNC\\" + text[2:] if text.startswith("\\\\") else "\\\\?\\" + text
    return Path(text)


def sha(value):
    with path(value).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(value):
    return json.loads(path(value).read_text(encoding="utf-8"))


def write(value, data):
    target = path(value)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def append(value, data):
    target = path(value)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def relative(name):
    candidate = PurePosixPath(name)
    require(name == candidate.as_posix() and not candidate.is_absolute()
            and ".." not in candidate.parts and "\\" not in name and ":" not in name,
            "unsafe evidence-relative path: " + str(name))
    return candidate


def bound(root, name):
    relative(name)
    candidate = path(root / name)
    require(candidate.resolve().is_relative_to(root.resolve()), "evidence path escaped root")
    return candidate


def checked(value, digest, size=None):
    value = path(value)
    require(value.is_file(), "source missing: " + str(value))
    require(size is None or value.stat().st_size == size, "byte count changed: " + str(value))
    require(sha(value) == digest, "SHA256 changed: " + str(value))
    return value


def copy_row(root, source, name, *, expected=None, size=None, role):
    source = path(source)
    require(source.is_file(), "copy source missing: " + str(source))
    before = sha(source)
    require(expected is None or before == expected, "copy source identity differs: " + str(source))
    require(size is None or source.stat().st_size == size, "copy source size differs")
    target = bound(root, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists(), "copy destination already exists: " + name)
    with source.open("rb") as left, target.open("xb") as right:
        shutil.copyfileobj(left, right, 1024 * 1024)
        right.flush()
        os.fsync(right.fileno())
    require(sha(target) == before and sha(source) == before, "copy changed bytes: " + name)
    row = dict(path=name, source=str(source), bytes=target.stat().st_size, sha256=before, role=role)
    append(root / "prepare_journal.ndjson", dict(event="copy_verified", utc=utc(), **row))
    return row


def utc():
    return datetime.now(timezone.utc).isoformat()


def prepare(root, repo, events):
    require(not (root / "input_manifest.json").exists(), "preparation is write-once")
    require(not (root / "B0").exists() and not (root / "C1").exists(), "source destination exists")
    old = repo / OLD_VERSION
    old_manifest = checked(old / "input_manifest.json", OLD_MANIFEST_SHA)
    original = read(old_manifest)
    records = {}
    for row in original["files"]:
        relative(row["path"])
        require(row["path"] not in records, "duplicate original manifest path")
        records[row["path"]] = row
    fixed = {"source/hf_repo/pyproject.toml", "source/hf_repo/tests/test_compensated_invariants.py",
             "source/hf_repo/tests/test_windows_owned_process.py"}
    selected = sorted(name for name in records if name.startswith("source/hf_repo/src/") or name in fixed)
    require(fixed.issubset(selected) and any(name.startswith("source/hf_repo/src/") for name in selected),
            "B0 minimum inventory is incomplete")
    disk_src = {p.relative_to(old).as_posix() for p in (old / "source/hf_repo/src").rglob("*")
                if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    require(disk_src == {name for name in selected if name.startswith("source/hf_repo/src/")},
            "B0 source tree contains missing or unmanifested source files")
    rows = [copy_row(root, old_manifest, "provenance/b0_input_manifest.json",
                     expected=OLD_MANIFEST_SHA, role="old_snapshot_manifest")]
    for name in selected:
        row = records[name]
        rows.append(copy_row(root, old / name, "B0/" + name, expected=row["sha256"], size=row["bytes"],
                             role="immutable_B0"))
    for name in AUX_FILES:
        rows.append(copy_row(root, repo / name, "aux/" + name, role="diagnostic_auxiliary"))
    installed = path(sys.executable).parent.parent / "Lib/site-packages/jax"
    for name, digest in JAX_FILES.items():
        rows.append(copy_row(root, installed / name, "aux/runtime/jax/" + name,
                             expected=digest, role="installed_primary_JAX_source"))
    original_outputs = repo / MANUFACTURED / "output_sha256.json"
    output_index = read(original_outputs)
    for filename in ("inputs.npz", "input_freeze.json"):
        key = "unit__near_rotation/" + filename
        require(key in output_index, "original manufacturing output lacks " + key)
        rows.append(copy_row(root, repo / MANUFACTURED / key, "data/" + filename,
                             expected=output_index[key], role="original_unit_near_rotation"))
    rows.append(copy_row(root, original_outputs, "data/original_output_sha256.json",
                         role="original_manufacturing_output_manifest"))
    freeze = read(root / "data/input_freeze.json")
    require(freeze["case"] == "unit__near_rotation" and freeze["input_sha256"] == INPUT_SHA,
            "representative input freeze differs")
    checked(root / "data/inputs.npz", INPUT_SHA)
    canonical = repo / "hf_repo" / ARITHMETIC
    baseline = root / "B0/source/hf_repo" / ARITHMETIC
    checked(canonical, sha(baseline))
    manifest = dict(schema="hf-s0-preparation-inputs-1", created_utc=utc(), files=rows,
        baseline_manifest_sha256=OLD_MANIFEST_SHA, baseline_snapshot=str(old),
        canonical_arithmetic=dict(path=str(canonical), baseline_sha256=sha(baseline)),
        frozen_input_case="unit__near_rotation", direction=0, scientific_admission=False,
        python=dict(executable=sys.executable, version=sys.version),
        scope="B0 original source/tests; diagnostic auxiliary source kept outside B0")
    write(root / "input_manifest.json", manifest)
    result = verify_all(root, repo)
    events.emit("preparation_complete", input_manifest_sha256=sha(root / "input_manifest.json"),
                files=len(rows))
    return dict(status="pass", files=len(rows), copied_bytes=sum(row["bytes"] for row in rows),
                source_verification=result)


def verify_rows(root, rows):
    names = set()
    for row in rows:
        require(row["path"] not in names, "duplicate current manifest path")
        names.add(row["path"])
        checked(bound(root, row["path"]), row["sha256"], row["bytes"])
        checked(row["source"], row.get("source_sha256", row["sha256"]),
                row.get("source_bytes", row["bytes"]))
    return len(names)


def verify_all(root, repo):
    manifest = read(root / "input_manifest.json")
    count = verify_rows(root, manifest["files"])
    c1_path = root / "C1/source_manifest.json"
    expected_canonical = manifest["canonical_arithmetic"]["baseline_sha256"]
    c1_count = 0
    if c1_path.exists():
        c1 = read(c1_path)
        require(c1["base_manifest_sha256"] == sha(root / "input_manifest.json"), "C1 base manifest changed")
        c1_count = verify_rows(root, c1["files"])
        for artifact, digest in c1["proof_artifacts"].items():
            checked(bound(root, artifact), digest)
        expected_canonical = c1["canonical_arithmetic_sha256"]
    checked(repo / "hf_repo" / ARITHMETIC, expected_canonical)
    selection = root / "selected_source.json"
    if selection.exists():
        selected = read(selection)
        expected_source = root / selected["version"] / "source/hf_repo"
        require(selected["version"] in ("B0", "C1") and path(selected["source"]) == expected_source,
                "selected source identity differs")
        expected_manifest = c1_path if selected["version"] == "C1" else root / "input_manifest.json"
        require(path(selected["source_manifest"]) == expected_manifest and
                selected["source_manifest_sha256"] == sha(expected_manifest), "selected manifest differs")
    return dict(status="pass", input_files=count, C1_files=c1_count, missing=0, mismatches=0,
                canonical_arithmetic_sha256=expected_canonical,
                input_manifest_sha256=sha(root / "input_manifest.json"))


def transpose_assertion(error):
    if error.get("type") != "AssertionError":
        return False
    trace = error.get("traceback", "")
    lower = trace.lower()
    symbol = "GradAccum" in trace or "UndefinedPrimal" in trace
    rule = ("bilinear_transpose" in trace or re.search(r"ad\.py.{0,12}(1135|1144)", trace) is not None)
    return bool("jax" in lower and "ad.py" in lower and symbol and rule and "AssertionError" in trace)


def baseline_result(root, manifest_sha):
    event_path = root / "events/P2_baseline.ndjson"
    raw = event_path.read_bytes()
    require(raw.endswith(b"\n"), "baseline event stream is truncated", ClassificationFailure)
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    require(rows, "baseline event stream is empty", ClassificationFailure)
    for index, row in enumerate(rows, 1):
        require(row["sequence"] == index and row["schema"] == "hf-s0-event-1"
                and row["source_manifest_sha256"] == manifest_sha and row["phase"] == "P2_baseline"
                and row["version"] == "B0",
                "baseline event identity/sequence differs", ClassificationFailure)
    require(not any(row["event"] in ("pytest_internal_error", "pytest_interrupted") for row in rows)
            and not any(row["event"] in ("collection_report", "collection_finish")
                        and row.get("outcome") == "failed" for row in rows),
            "baseline has a collection/internal/interruption error", ClassificationFailure)
    reports = [row for row in rows if row["event"] == "test_report"]
    require(reports and all(row["nodeid"].replace("\\", "/").endswith(TARGET_NODE) for row in reports),
            "baseline test nodeid differs", ClassificationFailure)
    calls = [row for row in reports if row["when"] == "call"]
    require(len(calls) == 1 and all(row["outcome"] == "passed" for row in reports if row["when"] != "call"),
            "baseline has setup/teardown failure or incomplete call", ClassificationFailure)
    finishes = [row for row in rows if row["event"] == "session_finish"]
    collections = [row for row in rows if row["event"] == "collection_finish"]
    require(len(finishes) == 1 and rows[-1] == finishes[0] and finishes[0]["testscollected"] == 1
            and len(collections) == 1 and collections[0]["collected"] == 1,
            "baseline pytest did not finish exactly one collected test", ClassificationFailure)
    call = calls[0]
    exitstatus = finishes[0].get("exitstatus", finishes[0].get("exit_status"))
    if call["outcome"] == "passed":
        require(exitstatus == 0, "passing call has nonzero pytest exit", ClassificationFailure)
        return dict(status="pass", event_sha256=sha(event_path), nodeid=call["nodeid"])
    require(call["outcome"] == "failed" and exitstatus == 1, "baseline did not have a complete test failure", ClassificationFailure)
    error = dict(type=call.get("exception_type", call.get("exception", {}).get("type")),
                 traceback=call.get("traceback", call.get("longreprtext", "")))
    require(transpose_assertion(error), "baseline failure is not the declared bilinear-transpose AssertionError", ClassificationFailure)
    return dict(status="declared_transpose_failure", event_sha256=sha(event_path), nodeid=call["nodeid"], error=error)


def controls_result(root, manifest_sha):
    filename = root / "results/controls/summary.json"
    summary = read(filename)
    require(summary["schema"] == "hf-s0-preparation-probe-1" and summary["mode"] == "controls"
            and summary["source_manifest_sha256"] == manifest_sha
            and summary["status"] in ("pass", "diagnostic_observation"),
            "controls summary identity or outcome differs", ClassificationFailure)
    controls = summary["controls"]
    required = {"primal", "jvp", "vjp_construct", "pullback", "closed_form", "duality", "linearized_jaxpr"}
    observed = []
    for kind in ("none", "separate", "joint"):
        require(set(controls[kind]) == {"eager", "jit"}, "control execution modes differ", ClassificationFailure)
        for mode in ("eager", "jit"):
            steps = controls[kind][mode]
            require(set(steps) == required, "control steps differ", ClassificationFailure)
            if kind != "joint":
                require(all(item["status"] == "pass" for item in steps.values()),
                        "non-joint control failed", ClassificationFailure)
                continue
            require(all(steps[name]["status"] == "pass" for name in
                        ("primal", "jvp", "closed_form", "linearized_jaxpr")),
                    "joint control has a non-VJP or numerical failure", ClassificationFailure)
            failed = [name for name in ("vjp_construct", "pullback") if steps[name]["status"] == "failed"]
            if not failed:
                require(all(item["status"] == "pass" for item in steps.values()),
                        "joint control has incomplete non-failure steps", ClassificationFailure)
                continue
            require(len(failed) == 1 and transpose_assertion(steps[failed[0]].get("error", {})),
                    "joint failure is not the declared transpose assertion", ClassificationFailure)
            other = "pullback" if failed[0] == "vjp_construct" else "vjp_construct"
            require(steps[other]["status"] == ("not_run" if other == "pullback" else "pass")
                    and steps["duality"]["status"] == "not_run",
                    "joint control sequencing differs", ClassificationFailure)
            observed.append(dict(mode=mode, stage=failed[0], error=steps[failed[0]]["error"]))
    return dict(summary_sha256=sha(filename), joint_failures=observed)


def function_text(text, name):
    tree = ast.parse(text)
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
    require(len(nodes) == 1, "expected one function: " + name)
    node = nodes[0]
    lines = text.splitlines(keepends=True)
    begin = min([node.lineno] + [item.lineno for item in node.decorator_list])
    return "".join(lines[begin-1:node.end_lineno])


def repaired_bytes(original):
    text = original.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    require("def _derivative_mul(" not in text, "repair helper already exists")
    helper = newline.join((
        "def _derivative_mul(coefficient, direction):",
        "    # Preserve a known primal coefficient during tangent transposition.",
        "    coefficient = _barrier(coefficient, jnp)",
        "    direction = _barrier(direction, jnp)",
        "    return _barrier(coefficient * direction, jnp)", "", "", ""))
    anchor = "def _linear_pair(coefficient, direction):"
    require(text.count(anchor) == 1, "repair anchor differs")
    updated = text.replace(anchor, helper + anchor, 1)
    replacements = {
        "_mul(coefficient[0], direction, jnp)": "_derivative_mul(coefficient[0], direction)",
        "_mul(coefficient[1], direction, jnp)": "_derivative_mul(coefficient[1], direction)",
        "_mul(a, db, jnp)": "_derivative_mul(a, db)",
        "_mul(b, da, jnp)": "_derivative_mul(b, da)",
    }
    for before, after in replacements.items():
        require(updated.count(before) == 1, "repair call pattern differs: " + before)
        updated = updated.replace(before, after, 1)
    ast.parse(updated)
    # Everything except exactly two derivative functions and the new helper
    # must remain textually identical, including primal helper bytes.
    restored = updated.replace(helper, "", 1)
    for before, after in replacements.items():
        restored = restored.replace(after, before, 1)
    require(restored == text, "repair changed undeclared source text")
    primal = {}
    for name in ("_add", "_sub", "_mul"):
        before = function_text(text, name).encode("utf-8")
        after = function_text(updated, name).encode("utf-8")
        require(before == after, "primal helper changed: " + name)
        primal[name] = hashlib.sha256(before).hexdigest()
    # Assert the replaced expressions belong exclusively to the approved
    # derivative functions, rather than relying on global string uniqueness.
    for before in list(replacements)[:2]:
        require(before in function_text(text, "_linear_pair"), "pair repair escaped approved function")
    for before in list(replacements)[2:]:
        require(before in function_text(text, "_jax_product_jvp"), "product repair escaped approved function")
    patch = "".join(difflib.unified_diff(text.splitlines(keepends=True), updated.splitlines(keepends=True),
                                         fromfile="B0/" + ARITHMETIC, tofile="C1/" + ARITHMETIC))
    return updated.encode("utf-8"), primal, patch


def select(root, version):
    manifest = root / ("C1/source_manifest.json" if version == "C1" else "input_manifest.json")
    selected = dict(schema="hf-s0-selected-source-1", version=version,
                    source=str(root / version / "source/hf_repo"), source_manifest=str(manifest),
                    source_manifest_sha256=sha(manifest), scientific_admission=False)
    write(root / "selected_source.json", selected)
    return selected


def classify_and_fix(root, repo, events):
    require(not (root / "classification_started.json").exists(), "classification/repair cannot be retried")
    verify_all(root, repo)
    write(root / "classification_started.json", dict(utc=utc(), allowed_repairs=1))
    manifest_sha = sha(root / "input_manifest.json")
    baseline = baseline_result(root, manifest_sha)
    controls = controls_result(root, manifest_sha)
    record = dict(schema="hf-s0-failure-classification-1", baseline=baseline, controls=controls,
                  base_manifest_sha256=manifest_sha, scientific_admission=False)
    if baseline["status"] == "pass":
        record.update(status="baseline_not_reproduced", repair_performed=False)
        write(root / "failure_classification.json", record)
        return dict(status="pass", classification=record["status"], selected=select(root, "B0"))
    require(controls["joint_failures"], "joint control did not reproduce the declared mechanism", ClassificationFailure)
    record.update(status="declared_derivative_interface_defect", repair_authorized=True,
                  repair_scope="one derivative-path split barrier; no primal or numerical change")
    write(root / "failure_classification.json", record)
    source = root / "B0/source/hf_repo"
    canonical = repo / "hf_repo" / ARITHMETIC
    old_bytes = (source / ARITHMETIC).read_bytes()
    old_sha = hashlib.sha256(old_bytes).hexdigest()
    checked(canonical, old_sha)
    new_bytes, primal_hashes, patch = repaired_bytes(old_bytes)
    new_sha = hashlib.sha256(new_bytes).hexdigest()
    c1_rows = []
    for item in sorted(source.rglob("*")):
        if not item.is_file():
            continue
        name = item.relative_to(source).as_posix()
        target = root / "C1/source/hf_repo" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = new_bytes if name == ARITHMETIC else item.read_bytes()
        with target.open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        row = dict(path=target.relative_to(root).as_posix(), source=str(item), bytes=len(data),
                   sha256=hashlib.sha256(data).hexdigest(), role="C1_derivation_from_B0")
        if name == ARITHMETIC:
            row.update(source_sha256=old_sha, source_bytes=len(old_bytes))
        require(sha(target) == row["sha256"], "C1 copy verification failed")
        c1_rows.append(row)
        append(root / "prepare_journal.ndjson", dict(event="C1_file_verified", utc=utc(), **row))
    patch_path = root / "C1/patch.diff"
    with patch_path.open("xb") as stream:
        stream.write(patch.encode("utf-8")); stream.flush(); os.fsync(stream.fileno())
    proof = dict(schema="hf-s0-derivative-repair-proof-1", before_sha256=old_sha, after_sha256=new_sha,
                 changed_functions=["_linear_pair", "_jax_product_jvp"], added_function="_derivative_mul",
                 primal_helper_sha256=primal_hashes, unchanged_remainder_reconstruction=True,
                 original_tests_unchanged=True, numerical_tests_executed_by_worker=False,
                 classification_sha256=sha(root / "failure_classification.json"),
                 patch_sha256=sha(patch_path), canonical_source=str(canonical))
    write(root / "C1/repair_proof.json", proof)
    write(root / "C1/source_manifest.json", dict(schema="hf-s0-C1-source-1", files=c1_rows,
        base_manifest_sha256=manifest_sha, canonical_arithmetic_sha256=new_sha,
        proof_artifacts={"C1/repair_proof.json": sha(root / "C1/repair_proof.json"),
                         "C1/patch.diff": sha(patch_path)}))
    # The only authorized synchronization to the canonical development tree.
    # Recheck immediately before atomically replacing the known B0 bytes.
    checked(canonical, old_sha)
    temporary = canonical.with_name(canonical.name + ".s0-derivative-repair.tmp")
    with temporary.open("xb") as stream:
        stream.write(new_bytes); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, canonical)
    checked(canonical, new_sha)
    selected = select(root, "C1")
    verify_all(root, repo)
    events.emit("authorized_derivative_repair_complete", before_sha256=old_sha, after_sha256=new_sha)
    return dict(status="pass", classification=record["status"], selected=selected,
                canonical_arithmetic_sha256=new_sha)


def resource_svg(resources):
    rows = resources["phases"]
    height = 90 + len(rows) * 42
    maximum_time = max([float(row.get("elapsed_seconds", 0)) for row in rows] + [1.0])
    maximum_rss = max([float(row.get("peak_tree_rss_bytes", 0)) for row in rows] + [1.0])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="Arial,sans-serif" font-size="13" fill="#202b36">',
             '<text x="20" y="24">S0 recorded phases BEFORE P6; final parent receipt includes P6; no scientific admission</text>',
             '<text x="330" y="52">Wall seconds</text><text x="750" y="52">Sampled process-tree RSS (MiB)</text>']
    for index, row in enumerate(rows):
        y = 75 + index * 42
        seconds = float(row.get("elapsed_seconds", 0))
        rss = float(row.get("peak_tree_rss_bytes", 0))
        parts.extend((f'<text x="20" y="{y+12}">{escape(str(row["name"]))}</text>',
            f'<rect x="330" y="{y}" width="{280*seconds/maximum_time:.3f}" height="15" fill="#356c9b"/>',
            f'<text x="620" y="{y+12}">{seconds:.3f}</text>',
            f'<rect x="750" y="{y}" width="{230*rss/maximum_rss:.3f}" height="15" fill="#497f65"/>',
            f'<text x="990" y="{y+12}">{rss/1024**2:.2f}</text>'))
    parts.append('</g></svg>\n')
    return "".join(parts)


def stage_timings(root, resources):
    """Read saved timing records only; never trace or evaluate a kernel."""
    plan = read(root / "plan.json")
    recorded_cutoff = float(plan["start_monotonic"]) + float(resources["total_elapsed_seconds"])
    rows = []
    bindings = {}
    for mode, phase in (("force", "P4_force"), ("tangent", "P5_tangent")):
        summary_path = root / "results" / mode / "summary.json"
        event_path = root / "events" / (phase + ".ndjson")
        if not summary_path.exists():
            rows.append(dict(mode=mode, stage=mode, status="not_reached", seconds=None,
                             timing_basis="no saved probe summary"))
            continue
        summary = read(summary_path)
        bindings[summary_path.relative_to(root).as_posix()] = sha(summary_path)
        starts = {}
        if event_path.exists():
            raw = event_path.read_bytes()
            bindings[event_path.relative_to(root).as_posix()] = sha(event_path)
            lines = raw.splitlines(keepends=True)
            if lines and not lines[-1].endswith(b"\n"):
                lines.pop()  # Only a complete durable event can set a cutoff.
                rows.append(dict(mode=mode, stage="event_log_tail", status="truncated_tail_preserved",
                                 seconds=None, timing_basis="partial final line excluded from timing only"))
            for line in lines:
                event = json.loads(line)
                if event.get("event") == "stage_started":
                    starts[event["stage"]] = float(event["monotonic"])
        observed = set()
        for row in summary["steps"]:
            stage, state = row["stage"], row["status"]
            observed.add(stage)
            if state in ("pass", "failed") and "elapsed_seconds" in row:
                seconds = float(row["elapsed_seconds"])
                basis = "completed saved stage record"
            elif state == "running" and stage in starts:
                seconds = max(0.0, recorded_cutoff - starts[stage])
                state = "open_at_stop"
                basis = "upper observation interval to parent resources checkpoint; includes cleanup/dispatch; NOT completed stage time"
            else:
                seconds = None
                basis = "no complete saved duration"
            rows.append(dict(mode=mode, stage=stage, status=state, seconds=seconds, timing_basis=basis))
        labels = (mode, "residual_jvp") if mode == "tangent" else (mode,)
        for label in labels:
            for suffix in ("trace", "lower", "compile", "execute_synchronized", "transfer", "save_output", "export_ir"):
                stage = label + "." + suffix
                if stage not in observed:
                    rows.append(dict(mode=mode, stage=stage, status="not_reached", seconds=None,
                                     timing_basis="no saved started stage"))
    return dict(schema="hf-s0-stage-timings-1", rows=rows, source_sha256=bindings,
                observation_cutoff_monotonic=recorded_cutoff, scope="saved P4/P5 records only; no P6 or scientific accuracy claim")


def stages_svg(timings):
    rows = timings["rows"]
    height = 108 + len(rows) * 29
    maximum = max([row["seconds"] for row in rows if row["seconds"] is not None] + [1.0])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="Arial,sans-serif" font-size="12" fill="#202b36">',
             '<text x="20" y="24">S0 P4/P5 stage timing from saved records; no scientific admission</text>',
             '<text x="20" y="46">Orange open intervals end at the saved resource checkpoint; they include cleanup and are NOT completed stage times.</text>']
    for index, row in enumerate(rows):
        y = 70 + index * 29
        parts.append(f'<text x="20" y="{y+11}">{escape(row["stage"])}</text>')
        seconds = row["seconds"]
        color = "#ca842e" if row["status"] == "open_at_stop" else ("#a84040" if row["status"] == "failed" else "#356c9b")
        if seconds is not None:
            parts.append(f'<rect x="390" y="{y}" width="{400*seconds/maximum:.3f}" height="14" fill="{color}"/>')
        shown = "n/a" if seconds is None else f"{seconds:.6f} s"
        parts.append(f'<text x="810" y="{y+11}">{shown} | {escape(row["status"])}</text>')
    parts.append('</g></svg>\n')
    return "".join(parts)


def seal(root, repo, events):
    preservation = verify_all(root, repo)
    write(root / "source_preservation.json", preservation)
    require((root / "resources.json").is_file(), "parent resources must precede seal")
    resources = read(root / "resources.json")
    require(isinstance(resources["phases"], list), "resource phase list is invalid")
    with (root / "resources.svg").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(resource_svg(resources)); stream.flush(); os.fsync(stream.fileno())
    timings = stage_timings(root, resources)
    write(root / "stage_timings.json", timings)
    with (root / "stages.svg").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(stages_svg(timings)); stream.flush(); os.fsync(stream.fileno())
    summary = dict(schema="hf-s0-evidence-worker-1", action="seal", status="pass", scientific_admission=False,
                   source_preservation=preservation,
                   resources_scope="parent-frozen completed phases BEFORE P6; parent final receipt includes P6")
    phase = os.environ["HF_S0_PHASE"]
    excluded = {"output_sha256.json", "receipt_binding.json", "execution_receipt.json", "ledger.json",
                "logs/" + phase + ".log", "events/" + phase + ".ndjson"}
    summary["excluded_live_or_final_bindings"] = sorted(excluded)
    write(root / "results/seal/summary.json", summary)
    files = {}
    for item in sorted(root.rglob("*")):
        if item.is_file() and item.relative_to(root).as_posix() not in excluded:
            files[item.relative_to(root).as_posix()] = sha(item)
    write(root / "output_sha256.json", files)
    events.emit("seal_complete", output_manifest_sha256=sha(root / "output_sha256.json"),
                resources_scope="P6 excluded; parent binds its final receipt after cleanup")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--action", choices=("prepare", "verify", "classify_and_fix", "seal"), required=True)
    args = parser.parse_args()
    root, repo = path(args.root), path(args.repo)
    require(root != repo and not repo.is_relative_to(root), "evidence root must not contain repository")
    root.mkdir(parents=True, exist_ok=True)
    events = EventLog()
    begin = time.perf_counter()
    action = args.action
    output = root / "results" / action
    if action == "verify":
        number = 1
        while (root / "results" / f"verify_{number:03d}").exists():
            number += 1
        output = root / "results" / f"verify_{number:03d}"
    try:
        require(not output.exists(), "worker result directory already exists")
        events.emit("worker_started", action=action)
        if action == "prepare":
            result = prepare(root, repo, events)
        elif action == "verify":
            result = verify_all(root, repo)
        elif action == "classify_and_fix":
            result = classify_and_fix(root, repo, events)
        else:
            seal(root, repo, events)
            return 0
        summary = dict(schema="hf-s0-evidence-worker-1", action=action, elapsed_seconds=time.perf_counter()-begin,
                       scientific_admission=False, **result)
        write(output / "summary.json", summary)
        events.emit("worker_finished", action=action, status=result["status"])
        return 0
    except Exception as error:
        summary = dict(schema="hf-s0-evidence-worker-1", action=action,
                       status="classification_not_supported" if isinstance(error, ClassificationFailure) else "evidence_failure",
                       elapsed_seconds=time.perf_counter()-begin, scientific_admission=False,
                       error=dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()))
        if not (output / "summary.json").exists():
            write(output / "summary.json", summary)
        events.emit("worker_failed", action=action, **summary["error"])
        return 2
    finally:
        events.close()


if __name__ == "__main__":
    raise SystemExit(main())
