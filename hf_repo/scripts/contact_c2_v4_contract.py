"""Shared v4 kernel-repair contract checks (standard library only; imports no mechanics).

The v4 protocol keeps the frozen v3 physics, geometry, solver controls, audit gates, observables and
targets for the single failed fine-mesh case and changes only the evaluation kernel. The v4 runner, the
v4 audit, the v4 launch guard and the freeze tool all call these checks, so they cannot drift apart.

Identity layering (acyclic): the protocol's ``implementation_sha256`` binds the runner, the audit, this
module, the kernels and all mechanics they import. The launch guard, which pins the protocol's own
SHA-256, is deliberately NOT in that manifest; its bytes are recorded outside the protocol, in the launch
identity file and in every launch plan and receipt.
"""
from __future__ import annotations

import importlib.metadata
import math
import platform
from pathlib import PurePosixPath

SCHEMA = "contact_c2_kernel_repair_v4"
RUN_SCHEMA = "contact_c2_run_v4"
AUDIT_SCHEMA = "contact-c2-v4-independent-audit-1.0"
CASE_ID = "mesh_h00625"
SEQUENCE = [CASE_ID]
PROTOCOL_PATH = "configs/contact_c2_v4.json"
V3_PROTOCOL_PATH = "configs/contact_c2_v3.json"
V3_PROTOCOL_SHA256 = "b17c8328dd1e350563b70305c0b311c8d38c9c0ef68c08b85fac5f13604d0b4d"
C1_PROTOCOL_PATH = "configs/contact_c1_v1.json"
C1_PROTOCOL_SHA256 = "5b30bafc226cb97038ae1b0d08e745f9f7df2a049333a8019cdf03cc48fe5308"
RETAINED_V3_SECTIONS = ("geometry", "geometry_scope", "material", "solver", "audit", "uniform_targets_mm",
                        "observables", "saved_field_admission", "baseline_audits")
KERNEL = {
    "module": "hf_eval.split_kernel_compensated",
    "kernel_version": "p26_q1_split_compensated_dot2_v1",
    "arithmetic_module": "hf_eval.compensated_kinematics",
    "arithmetic_version": "split_affine_dot2_dekker_v1",
    "compiler_options": {"xla_cpu_enable_fast_math": False, "xla_cpu_ftz": False},
    "nonzero_operand_range": [2.0**-400, 2.0**400],
    "path_solver": "hf_eval.split_affine_compensated",
    "path_solver_difference_from_frozen_split_affine": "exactly one line: the kernel import",
    "production_quantities": "path solve, accepted-state force and tangent, and the material/regularization tangent actions all use this kernel; the component JVP entry is compiled with the same compiler options",
}
ENVIRONMENT = {"python": "3.13.6", "numpy": "2.4.6", "scipy": "1.17.1", "jax": "0.11.0", "jaxlib": "0.11.0"}
BUDGET = {"maximum_paths": 1, "solver_internal_wall_seconds": 300.0, "subprocess_wall_seconds": 700,
          "maximum_total_solve_seconds": 700, "maximum_audit_seconds_per_path": 1200,
          "maximum_total_audit_seconds": 1200}
REQUIRED_IMPLEMENTATION = (
    "src/hf_eval/contact_c2.py", "src/hf_eval/split_affine_compensated.py", "src/hf_eval/split_kernel_compensated.py",
    "src/hf_eval/compensated_kinematics.py", "src/hf_eval/split_state.py", "src/hf_eval/tmc.py",
    "src/hf_eval/tmc_kernel.py", "scripts/run_contact_c2_v4.py", "scripts/audit_contact_c2_v4.py",
    "scripts/contact_c2_v4_contract.py", "scripts/audit_contact_c2.py", "scripts/audit_contact_c1.py",
    "scripts/hf4_common.py", "scripts/hf4_split_precision_reference.py", "scripts/hf2_precision_reference.py",
)
# The launch layer pins the protocol SHA, so it must never be inside the protocol's own manifest.
LAUNCH_FILES = ("scripts/contact_c2_launch_v4.py", "scripts/run_contact_c2_v4_isolated.py", "scripts/contact_c2_launch_p1.py")
TEXT_FIELDS = ("purpose", "frozen_utc", "stopping", "storage", "prefix_semantics")
TOP_LEVEL = set(RETAINED_V3_SECTIONS) | set(TEXT_FIELDS) | {
    "schema", "cases", "run_sequence", "kernel", "environment", "budget", "stable_f_evidence", "relation_to_v3",
    "implementation_sha256"}


class V4ContractError(ValueError):
    """The v4 protocol, a run record or the interpreter differs from the frozen v4 contract."""


def require(condition, message):
    if not condition:
        raise V4ContractError(message)


def same(actual, expected, label):
    """Strict JSON equality: types (bool vs int vs float), keys, lengths and values."""
    require(type(actual) is type(expected), label + " has a different JSON type")
    if isinstance(expected, dict):
        require(set(actual) == set(expected), label + " keys differ")
        for key in expected:
            same(actual[key], expected[key], label + "." + key)
    elif isinstance(expected, list):
        require(len(actual) == len(expected), label + " length differs")
        for index, value in enumerate(expected):
            same(actual[index], value, f"{label}[{index}]")
    else:
        require(actual == expected, label + " differs from the frozen v4 contract")


def relative_posix(name, label):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name, label + " must be a relative POSIX path")
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == name, label + " must be canonical and inside the repository")


def digest(value, label):
    require(isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
            label + " is not a lowercase SHA-256")


def validate_protocol(protocol, v3, c1):
    """Content checks of a v4 protocol against the frozen v3 and C1 protocols (identity is the guard's job)."""
    require(type(protocol) is dict, "v4 protocol must be an object")
    require(set(protocol) == TOP_LEVEL, "v4 protocol top-level fields differ: missing "
            + str(sorted(TOP_LEVEL - set(protocol))) + ", extra " + str(sorted(set(protocol) - TOP_LEVEL)))
    same(protocol["schema"], SCHEMA, "schema")
    for section in RETAINED_V3_SECTIONS:
        same(protocol[section], v3[section], section + " (retained from v3)")
    for section in ("geometry", "material", "solver"):
        same(protocol[section], c1[section], section + " (C1 v1)")
    same(protocol["cases"], {CASE_ID: v3["cases"][CASE_ID]}, "cases")
    same(protocol["run_sequence"], SEQUENCE, "run_sequence")
    same(protocol["kernel"], KERNEL, "kernel")
    same(protocol["environment"], ENVIRONMENT, "environment")
    same(protocol["budget"], BUDGET, "budget")
    require(protocol["budget"]["solver_internal_wall_seconds"] == protocol["solver"]["time_limit_seconds"],
            "budget restates the solver's internal wall limit and must equal solver.time_limit_seconds")
    for name in TEXT_FIELDS:
        require(isinstance(protocol[name], str) and protocol[name].strip(), name + " must be a nonempty string")
    relation = protocol["relation_to_v3"]
    require(type(relation) is dict and relation.get("v3_protocol_sha256") == V3_PROTOCOL_SHA256
            and relation.get("v3_history") == "hf4_c2_diagnostics/experiments/mesh_h00625 remains NOT_PASS",
            "relation_to_v3 must name the frozen v3 protocol and keep its history")
    evidence = protocol["stable_f_evidence"]
    require(type(evidence) is dict and set(evidence) == {"path", "sha256", "schema"}, "stable_f_evidence fields differ")
    require(isinstance(evidence["path"], str) and evidence["schema"] == "contact-c2-stable-f-validation-summary-1",
            "stable_f_evidence must name the no-solve validation summary")
    digest(evidence["sha256"], "stable_f_evidence.sha256")
    manifest = protocol["implementation_sha256"]
    require(type(manifest) is dict and manifest, "implementation_sha256 must be a nonempty object")
    for name, value in manifest.items():
        relative_posix(name, "implementation path")
        digest(value, "implementation digest of " + name)
    missing = [name for name in REQUIRED_IMPLEMENTATION if name not in manifest]
    require(not missing, "implementation manifest lacks required files: " + str(missing))
    forbidden = [name for name in LAUNCH_FILES if name in manifest]
    require(not forbidden, "launch-layer files must stay outside the protocol manifest (acyclic identity): " + str(forbidden))
    for value in protocol["kernel"]["nonzero_operand_range"]:
        require(math.isfinite(value) and value > 0, "operand range must be positive and finite")


def environment_mismatches(expected=ENVIRONMENT):
    """Interpreter and package versions that differ from the locked environment (read-only; imports nothing heavy)."""
    actual = {"python": platform.python_version()}
    for name in ("numpy", "scipy", "jax", "jaxlib"):
        try:
            actual[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual[name] = None
    return {name: dict(expected=expected[name], actual=actual.get(name)) for name in expected if actual.get(name) != expected[name]}
