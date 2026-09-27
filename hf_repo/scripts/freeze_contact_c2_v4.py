"""Freeze the v4 kernel-repair protocol and, afterwards, the launch identity (write-once; no FE, no solve).

Two separate steps keep the identities acyclic:

  protocol   builds configs/contact_c2_v4.json from the frozen v3 protocol (retained sections copied byte-for-
             byte in value), the v4 contract constants and an implementation manifest computed from the actual
             import closure of the v4 runner and v4 audit (plus the reference script they load by file path).
             The launch-layer files are excluded by construction.
  identity   after PROTOCOL_SHA256 has been written into contact_c2_launch_v4.py, records the protocol SHA and
             the launch-layer file hashes in configs/contact_c2_v4_launch_identity.json.

Both refuse to overwrite an existing file. Importing the runner creates JIT wrappers but compiles and runs
nothing; the closure is computed in a separate interpreter.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import contact_c2_v4_contract as contract  # noqa: E402

CLOSURE_PROBE = r"""
import importlib, json, sys
from pathlib import Path
repo = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(repo / "scripts"), str(repo / "src")]
for name in ("run_contact_c2_v4", "audit_contact_c2_v4"):
    importlib.import_module(name)
files = sorted({Path(m.__file__).resolve().relative_to(repo).as_posix() for m in list(sys.modules.values())
                if getattr(m, "__file__", None) and Path(m.__file__).resolve().is_relative_to(repo)})
print(json.dumps(files))
"""
# Loaded by file path inside hf4_split_precision_reference (never registered in sys.modules).
FILE_LOADED = ("scripts/hf2_precision_reference.py",)

PURPOSE = ("v4 kernel-repair re-test: the frozen v3 physics, geometry, solver controls, audit gates, observables and "
           "the 7 uniform targets for the single failed fine-mesh case (h = 0.0625 mm, padding 2.0 mm, driven outer "
           "bottom); only the evaluation kernel changes to the compensated split kernel. Question: does the fixed-state "
           "arithmetic repair also let the complete Newton/path controller pass the original acceptance?")
STOPPING = ("One solve, then one independent 80/120-digit audit, and the audit only after a successful solve. The "
            "solver's declared in-path controls remain (Armijo backtracking, at most 8 bisection levels, minimum "
            "increment, internal 300 s wall limit); 'no automatic retry' means no second path, no parameter, threshold or "
            "resource change and no audit re-run. Independent checks run in the post-solve audit, not during Newton. Any "
            "source or identity mismatch is refused before running. Failed or timed-out artifacts are preserved as they are.")
STORAGE = ("Run directory hf4_c2_v4_results/experiments/mesh_h00625_v4 (outside hf_repo, separate from the v3 history). "
           "Lightweight records (metadata, results, indices, receipts, compact audit) go into Git; large lossless payloads "
           "(per-state NPZ, full controller gzip, per-state audit details) may be kept outside Git in a hash-verified "
           "archive with a manifest (relative path, bytes, SHA-256, archive location, restore method), after one "
           "original-byte restore check into an empty directory.")
PREFIX = ("A solve that fails or times out keeps every persisted accepted state and its log. Only a contiguous run of "
          "states that pass the independent audit is called a verified comparable prefix; unaudited, incomplete or "
          "unfinished parts do not count. The frozen audit requires a complete controller/completion inventory, so a "
          "hard timeout that leaves only per-state files is not certified; no resume, rescue solve or incomplete-"
          "directory audit is added. The 21 accepted states of the v3 run are a historical observation, not a v4 "
          "requirement: the 7 original targets and the control rules are.")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def implementation_manifest(python):
    closure = json.loads(subprocess.check_output([python, "-B", "-c", CLOSURE_PROBE, str(REPO)], text=True,
                                                 env={**__import__("os").environ, "JAX_PLATFORMS": "cpu", "PYTHONDONTWRITEBYTECODE": "1"}))
    files = set(closure) | set(FILE_LOADED) | set(contract.REQUIRED_IMPLEMENTATION)
    leaked = sorted(files & set(contract.LAUNCH_FILES))
    if leaked:
        raise SystemExit("launch-layer files appear in the implementation closure: " + str(leaked))
    return {name: sha(REPO / name) for name in sorted(files)}


def build_protocol(manifest, evidence_sha256, frozen_utc):
    """The v4 protocol dictionary (pure function of the frozen v3/C1 files, the contract and the given inputs)."""
    v3 = json.loads((REPO / contract.V3_PROTOCOL_PATH).read_text(encoding="utf-8-sig"))
    return {
        "schema": contract.SCHEMA,
        "frozen_utc": frozen_utc,
        "purpose": PURPOSE,
        **{section: deepcopy(v3[section]) for section in contract.RETAINED_V3_SECTIONS},
        "cases": {contract.CASE_ID: deepcopy(v3["cases"][contract.CASE_ID])},
        "run_sequence": list(contract.SEQUENCE),
        # Deep copies: the protocol must never alias the constants it is validated against.
        "kernel": deepcopy(contract.KERNEL),
        "environment": deepcopy(contract.ENVIRONMENT),
        "budget": deepcopy(contract.BUDGET),
        "stable_f_evidence": {"schema": "contact-c2-stable-f-validation-summary-1",
                              "path": "../../hf4_c2_stable_f_validation/summary_001.json", "sha256": evidence_sha256},
        "relation_to_v3": {"v3_protocol_sha256": contract.V3_PROTOCOL_SHA256,
                           "v3_history": "hf4_c2_diagnostics/experiments/mesh_h00625 remains NOT_PASS",
                           "retained_sections": list(contract.RETAINED_V3_SECTIONS),
                           "changed": "evaluation kernel only: the path solver is a one-line-difference copy of split_affine and all recorded production quantities come from the compensated kernel",
                           "not_carried_over": "the other two v3 cases (both passed in v3) and the v3 execution revisions"},
        "stopping": STOPPING,
        "storage": STORAGE,
        "prefix_semantics": PREFIX,
        "implementation_sha256": dict(manifest),
    }


def freeze_protocol(python):
    target = REPO / contract.PROTOCOL_PATH
    if target.exists():
        raise SystemExit("refusing to overwrite the frozen v4 protocol")
    if sha(REPO / contract.V3_PROTOCOL_PATH) != contract.V3_PROTOCOL_SHA256 or sha(REPO / contract.C1_PROTOCOL_PATH) != contract.C1_PROTOCOL_SHA256:
        raise SystemExit("frozen v3 or C1 protocol changed")
    v3 = json.loads((REPO / contract.V3_PROTOCOL_PATH).read_text(encoding="utf-8-sig"))
    c1 = json.loads((REPO / contract.C1_PROTOCOL_PATH).read_text(encoding="utf-8-sig"))
    evidence = REPO.parent / "hf4_c2_stable_f_validation/summary_001.json"
    protocol = build_protocol(implementation_manifest(python), sha(evidence),
                              datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    contract.validate_protocol(protocol, v3, c1)
    write_once(target, protocol)
    print(json.dumps(dict(protocol=contract.PROTOCOL_PATH, sha256=sha(target), implementation_files=len(protocol["implementation_sha256"]))))


def freeze_identity():
    import contact_c2_launch_v4 as launch
    protocol = REPO / contract.PROTOCOL_PATH
    target = REPO / launch.IDENTITY_FILE
    if target.exists():
        raise SystemExit("refusing to overwrite the launch identity")
    if launch.PROTOCOL_SHA256 != sha(protocol):
        raise SystemExit("the launch guard does not pin the frozen v4 protocol")
    write_once(target, dict(schema=launch.IDENTITY_SCHEMA, created_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                            protocol_path=contract.PROTOCOL_PATH, protocol_sha256=sha(protocol),
                            launch_files={name: sha(REPO / name) for name in contract.LAUNCH_FILES},
                            note="Outside the protocol by design: the guard pins the protocol SHA, so the guard cannot be in the protocol's manifest."))
    print(json.dumps(dict(identity=launch.IDENTITY_FILE, sha256=sha(target))))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", choices=("protocol", "identity"))
    parser.add_argument("--python", default=sys.executable, help="interpreter used to compute the import closure (the locked one)")
    args = parser.parse_args()
    if args.step == "protocol":
        freeze_protocol(args.python)
    else:
        freeze_identity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
