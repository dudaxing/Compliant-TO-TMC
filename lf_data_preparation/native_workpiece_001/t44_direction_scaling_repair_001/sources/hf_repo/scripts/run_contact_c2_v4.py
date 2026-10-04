"""v4 kernel-repair re-test of the C2 fine-mesh uniform path, preserving all accepted states.

Same model builder, targets, solver controls, stage/record layout and file names as the frozen v3 runner
(scripts/run_contact_c2.py, unchanged); only the evaluation kernel differs. The path is solved by
hf_eval.split_affine_compensated, a copy of the frozen split_affine that differs in exactly one line (the
kernel import). Every recorded production quantity -- internal force, material/regularization force
components, J, the assembled tangent action and the material/regularization tangent actions -- comes from
hf_eval.split_kernel_compensated; the component JVP entry is compiled with the kernel's strict CPU options.

This script checks the protocol CONTENT against the frozen v3/C1 contracts (contact_c2_v4_contract). The
protocol IDENTITY and the launch admission belong to contact_c2_launch_v4.py, which is kept outside the
protocol's implementation manifest so that the identities are not circular.
"""
from pathlib import Path
import argparse
import gzip
import importlib.metadata
import json
import platform
import sys

import jax
import jax.numpy as jnp
import numpy as np
jax.config.update("jax_enable_x64", True)
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from hf_eval.contact_c2 import build_problem, CASES
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_affine_compensated import solve_split_affine_path
from hf_eval.split_state import SplitDisplacement
from hf_eval import compensated_kinematics, split_kernel_compensated as kernel
from hf4_common import read_json, write_json, write_npz, sha, timestamp, plain
import contact_c2_v4_contract as contract


def check_kernel_identity():
    """The imported kernel must be the one the contract names; otherwise nothing is run."""
    expected = contract.KERNEL
    contract.require(kernel.KERNEL_VERSION == expected["kernel_version"], "imported kernel version differs from the v4 contract")
    contract.require(compensated_kinematics.ARITHMETIC_VERSION == expected["arithmetic_version"],
                     "imported arithmetic version differs from the v4 contract")
    contract.require(kernel.COMPILER_OPTIONS == expected["compiler_options"], "kernel compiler options differ from the v4 contract")
    contract.require([compensated_kinematics.OPERAND_MIN, compensated_kinematics.OPERAND_MAX] == expected["nonzero_operand_range"],
                     "kernel operand range differs from the v4 contract")


def validate(protocol, protocol_path):
    v3 = read_json(REPO / contract.V3_PROTOCOL_PATH)
    c1 = read_json(REPO / contract.C1_PROTOCOL_PATH)
    contract.require(sha(REPO / contract.V3_PROTOCOL_PATH) == contract.V3_PROTOCOL_SHA256, "frozen v3 protocol changed")
    contract.require(sha(REPO / contract.C1_PROTOCOL_PATH) == contract.C1_PROTOCOL_SHA256, "frozen C1 protocol changed")
    contract.validate_protocol(protocol, v3, c1)
    check_kernel_identity()
    mismatches = contract.environment_mismatches(protocol["environment"])
    contract.require(not mismatches, "interpreter differs from the locked v4 environment: " + json.dumps(mismatches))


_component_jvp = jax.jit(
    lambda lift, fluctuation, grad, hessian, weights, lam, mu, kr, direction: jax.jvp(
        lambda varied: kernel._guarded_batch(lift, varied, grad, hessian, weights, lam, mu, kr, tangent=False),
        (fluctuation,), (direction,))[1],
    compiler_options=kernel.COMPILER_OPTIONS)


def component_actions(model, state, vector):
    """Material and regularization tangent actions of the compensated kernel (lift fixed, strict compilation)."""
    actions = _component_jvp(jnp.asarray(state.lift[model.edofs]), jnp.asarray(state.fluctuation[model.edofs]),
                             jnp.asarray(model.ops["grad"]), jnp.asarray(model.ops["hessian"]),
                             jnp.asarray(model.ops["weights"]), jnp.asarray(model.lam), jnp.asarray(model.mu),
                             jnp.asarray(model.kr), jnp.asarray(vector[model.edofs]))
    return {name: np.bincount(model.edofs.ravel(), weights=np.asarray(actions[name]).ravel(), minlength=model.ndof)
            for name in ("material_residual", "regularization_residual")}


def run(output, case_id, protocol_path):
    output, protocol_path = Path(output).resolve(), Path(protocol_path).resolve()
    if output.exists():
        raise FileExistsError("refusing to overwrite evidence")
    protocol = read_json(protocol_path)
    validate(protocol, protocol_path)
    contract.require(case_id == contract.CASE_ID, "v4 re-tests only the frozen fine-mesh case")
    spec = protocol["cases"][case_id]
    contract.require(list(CASES[case_id]) == [spec["h_mm"], spec["padding_mm"], spec["outer_bottom_policy"]],
                     "builder and frozen case differ")
    gate_path = (protocol_path.parent / protocol["saved_field_admission"]["path"]).resolve()
    contract.require(sha(gate_path) == protocol["saved_field_admission"]["sha256"] and read_json(gate_path)["status"] == "pass",
                     "saved-field diagnosis admission missing or changed")
    output.mkdir(parents=True)
    problem = build_problem(case_id)
    model, arrays = problem.model, problem.arrays
    stage = output / "stages/uniform_tmc"
    (stage / "steps").mkdir(parents=True)
    write_json(output/"stages/index.json", dict(stages=[dict(phase_id="uniform_tmc",
               directory="stages/uniform_tmc", status="running")]))
    sources = [*sorted((REPO/"src/hf_eval").glob("*.py")), Path(__file__), REPO/"scripts/contact_c2_v4_contract.py",
               REPO/"scripts/hf4_common.py"]
    write_json(output/"metadata.json", dict(schema=contract.RUN_SCHEMA, case_id=case_id,
        kind="TMC", mode="uniform", h=spec["h_mm"], case=spec, protocol=protocol,
        protocol_sha256=sha(protocol_path), protocol_path=protocol_path.relative_to(REPO).as_posix(),
        kernel=contract.KERNEL, started_utc=timestamp(),
        source_sha256={p.relative_to(REPO).as_posix(): sha(p) for p in sources},
        environment=dict(python=platform.python_version(), platform=platform.platform(),
                         **{n: importlib.metadata.version(n) for n in ("numpy", "scipy", "jax", "jaxlib")})))
    write_npz(stage/"model.npz", **arrays)
    write_npz(stage/"initial_state.npz", u_lift=problem.initial_state.lift,
              u_fluctuation=problem.initial_state.fluctuation)
    write_json(stage/"metadata.json", dict(schema="contact_c2_stage_v1", phase_id="uniform_tmc", kind="TMC",
        h=spec["h_mm"], padding=spec["padding_mm"], outer_bottom_policy=spec["outer_bottom_policy"],
        force_scale_per_length=100., targets=problem.targets, physical_mean_drive=dict(offset=0., slope=1.),
        model_sha256=sha(stage/"model.npz"), initial_state_sha256=sha(stage/"initial_state.npz"),
        source_initialization=dict(type="geometric_zero")))
    entries = []
    write_json(stage/"steps/index.json", dict(steps=entries))
    vector = np.sin(np.arange(model.ndof, dtype=float)+.37)
    vector[model.fixed_dofs] = 0.
    vector /= np.linalg.norm(vector)

    def accepted(record):
        state = SplitDisplacement(record["u_lift"], record["u_fluctuation"])
        matrix, force, fields = kernel.assemble_split(model, state, tangent=True)
        actions = component_actions(model, state, vector)
        components = {key: np.bincount(model.edofs.ravel(), weights=fields[key].ravel(), minlength=model.ndof)
                      for key in ("material_residual", "regularization_residual")}
        filename = f"state_{len(entries):03d}.npz"
        write_npz(stage/"steps"/filename, u_lift=state.lift, u_fluctuation=state.fluctuation,
                  internal_force=force, material_internal_force=components["material_residual"],
                  regularization_internal_force=components["regularization_residual"], J=fields["J"],
                  tangent_direction=vector, production_tangent_action=matrix@vector,
                  material_tangent_action=actions["material_residual"],
                  regularization_tangent_action=actions["regularization_residual"])
        record_file = f"state_{len(entries):03d}.record.json.gz"
        with gzip.open(stage/"steps"/record_file, "wt", encoding="utf-8") as stream:
            json.dump(plain(record), stream, allow_nan=False, separators=(",", ":"))
        entry = {k: record[k] for k in ("d", "is_original_target", "original_target_displacement", "bisection_depth")}
        entry.update(index=len(entries), file=filename, sha256=sha(stage/"steps"/filename),
                     record_file=record_file, record_sha256=sha(stage/"steps"/record_file))
        entries.append(entry)
        write_json(stage/"steps/index.json", dict(steps=entries))
        print(json.dumps(dict(case=case_id, accepted=len(entries), d=record["d"], residual=record["relative_residual"])), flush=True)

    result = solve_split_affine_path(model, arrays["base"], arrays["direction"], arrays["lift_origin"],
        arrays["lift_shape"], problem.targets, initial_state=problem.initial_state, reaction_groups=problem.groups,
        settings=PrescribedSettings(**protocol["solver"]), force_scale_per_length=100., on_accept=accepted)
    # Retain the full controller trace once, losslessly compressed; accepted arrays are also in NPZ.
    with gzip.open(stage/"controller_full.json.gz", "wt", encoding="utf-8") as stream:
        json.dump(plain(result), stream, allow_nan=False, separators=(",", ":"))
    compact = {key: result[key] for key in ("status", "target_reached", "reached_displacement")}
    compact.update(accepted_states=len(entries), controller_full_sha256=sha(stage/"controller_full.json.gz"),
                   storage="complete controller JSON in lossless gzip; state arrays also indexed in NPZ")
    write_json(stage/"result.json", compact)
    write_json(stage/"completion.json", dict(status=result["status"], finished_utc=timestamp(),
        metadata_sha256=sha(stage/"metadata.json"), result_sha256=sha(stage/"result.json"),
        index_sha256=sha(stage/"steps/index.json"), accepted_states=len(entries),
        controller_full_sha256=sha(stage/"controller_full.json.gz")))
    stages = [dict(phase_id="uniform_tmc", directory="stages/uniform_tmc", status=result["status"])]
    write_json(output/"stages/index.json", dict(stages=stages))
    write_json(output/"result.json", dict(status=result["status"], stages=stages))
    write_json(output/"completion.json", dict(status=result["status"], finished_utc=timestamp(),
        metadata_sha256=sha(output/"metadata.json"), result_sha256=sha(output/"result.json"),
        index_sha256=sha(output/"stages/index.json")))
    return result["status"] == "success"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--case", required=True, choices=[contract.CASE_ID])
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args()
    try:
        ok = run(args.output, args.case, args.protocol)
    except Exception as error:
        if args.output.is_dir() and not (args.output/"exception.json").exists():
            write_json(args.output/"exception.json", dict(type=type(error).__name__, message=str(error), utc=timestamp()))
        raise
    raise SystemExit(0 if ok else 2)
