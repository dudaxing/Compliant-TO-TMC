"""C1 revision 2: explicitly impose only newly activated constraints at handoff.

The physical protocol and numerical gates are unchanged. Revision 1 and its
failed handoff evidence remain immutable; see HF4_C1_ACTIVATION_REPAIR.md.
"""
from pathlib import Path, PurePosixPath
import argparse
import importlib.metadata
import json
import os
import platform
import sys

import jax
import jax.numpy as jnp
import numpy as np

jax.config.update("jax_enable_x64", True)
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from hf_eval.contact_c1 import build_problem
from hf_eval.contact_c1_activation import prepare_closed_initial
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_affine import solve_split_affine_path
from hf_eval import split_kernel
from hf_eval.split_state import SplitDisplacement
from hf_eval.split_prescribed import state_hash
from hf4_common import write_json, write_npz, sha, timestamp

PROTOCOL_SHA256 = "5b30bafc226cb97038ae1b0d08e745f9f7df2a049333a8019cdf03cc48fe5308"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _confined(root, name):
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise ValueError("source evidence path must be relative POSIX")
    relative = PurePosixPath(name)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("source evidence path escapes its directory")
    target = root.joinpath(*relative.parts).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("source evidence path escapes through a symlink")
    return target


def _bind(root, path, bindings, expected=None):
    actual = sha(path)
    if expected is not None and actual != expected:
        raise ValueError("source evidence hash mismatch: " + str(path))
    bindings[path.relative_to(root).as_posix()] = actual
    return actual


def _completion(source_run, directory, index_name, bindings):
    completion = read_json(directory / "completion.json")
    _bind(source_run, directory / "completion.json", bindings)
    for filename, key in (("metadata.json", "metadata_sha256"),
                          ("result.json", "result_sha256"), (index_name, "index_sha256")):
        _bind(source_run, directory / filename, bindings, completion[key])
    result = read_json(directory / "result.json")
    if completion["status"] != "success" or result["status"] != "success":
        raise ValueError("source must be completed successfully")
    return completion, result


def _source_metadata(source_run, expected_kind, expected_h, bindings):
    metadata = read_json(source_run / "metadata.json")
    _bind(source_run, source_run / "metadata.json", bindings)
    if (metadata["schema"] != "contact_c1_run_v1" or metadata["mode"] != "uniform"
            or metadata["kind"] != expected_kind or metadata["h"] not in (.25, .125)
            or (expected_h is not None and metadata["h"] != expected_h)
            or metadata["protocol_sha256"] != PROTOCOL_SHA256
            or metadata["protocol"] != read_json(REPO / "configs/contact_c1_v1.json")
            or sha(REPO / "configs/contact_c1_v1.json") != PROTOCOL_SHA256):
        raise ValueError("source physical identity or frozen protocol differs")
    sources = metadata["source_sha256"]
    required = {"src/hf_eval/contact_c1.py", "src/hf_eval/split_affine.py",
                "src/hf_eval/split_kernel.py", Path(__file__).relative_to(REPO).as_posix(), "scripts/hf4_common.py"}
    if not isinstance(sources, dict) or not required.issubset(sources):
        raise ValueError("source code manifest is incomplete")
    for name, expected in sources.items():
        if sha(_confined(REPO, name)) != expected:
            raise ValueError("source code identity changed: " + name)
    return metadata


def _source_stage(source_run, phase_id, metadata, bindings):
    targets = {"uniform_precontact": [0., .125, .21875, .25],
               "uniform_closed": [0., .03125, .125, .25],
               "uniform_tmc": [0., .125, .21875, .25, .28125, .375, .5]}
    if phase_id not in targets or (phase_id == "uniform_tmc") != (metadata["kind"] == "TMC"):
        raise ValueError("source phase is not a declared uniform phase")
    stage = _confined(source_run, "stages/" + phase_id)
    completion, result = _completion(source_run, stage, "steps/index.json", bindings)
    stage_meta = read_json(stage / "metadata.json")
    if (stage_meta["phase_id"] != phase_id or stage_meta["kind"] != metadata["kind"]
            or stage_meta["h"] != metadata["h"] or stage_meta["targets"] != targets[phase_id]):
        raise ValueError("source stage physical identity or target sequence differs")
    for filename, key in (("model.npz", "model_sha256"), ("initial_state.npz", "initial_state_sha256")):
        _bind(source_run, stage / filename, bindings, stage_meta[key])
    entries = read_json(stage / "steps/index.json")["steps"]
    records = result["accepted_steps"]
    if len(entries) != len(records) or completion["accepted_states"] != len(entries):
        raise ValueError("source accepted-state counts differ")
    originals, levels, filenames = [], [], []
    for i, (entry, record) in enumerate(zip(entries, records)):
        if entry["index"] != i:
            raise ValueError("source state index is not contiguous")
        for key in ("d", "is_original_target", "original_target_displacement", "bisection_depth"):
            if entry[key] != record[key]:
                raise ValueError("source index/result identity differs: " + key)
        d, target, depth = entry["d"], entry["original_target_displacement"], entry["bisection_depth"]
        if (not np.isfinite(d) or not 0 <= d <= targets[phase_id][-1]
                or target not in targets[phase_id] or not isinstance(entry["is_original_target"], bool)
                or isinstance(depth, bool) or not isinstance(depth, int) or not 0 <= depth <= 8):
            raise ValueError("invalid source accepted target identity")
        if entry["is_original_target"]:
            if d != target:
                raise ValueError("source original target is mislabeled")
            originals.append(d)
        elif not d < target or depth == 0:
            raise ValueError("source substep must precede its original target")
        name = entry["file"]
        if not isinstance(name, str) or PurePosixPath(name).name != name or not name.endswith(".npz"):
            raise ValueError("source step filename must be an NPZ basename")
        path = _confined(stage / "steps", name)
        _bind(source_run, path, bindings, entry["sha256"])
        with np.load(path, allow_pickle=False) as arrays:
            state = SplitDisplacement(arrays["u_lift"], arrays["u_fluctuation"])
            if arrays["u_lift"].dtype != np.dtype("float64") or arrays["u_fluctuation"].dtype != np.dtype("float64"):
                raise ValueError("source split arrays must be binary64")
        if record.get("state_sha256") != state_hash(state):
            raise ValueError("source state identity hash differs from accepted record")
        for key, actual in (("u_lift", state.lift), ("u_fluctuation", state.fluctuation)):
            saved = np.asarray(record[key])
            if (saved.shape != actual.shape or saved.dtype.kind not in "iuf"
                    or np.asarray(saved, dtype="<f8").tobytes() != np.asarray(actual, dtype="<f8").tobytes()):
                raise ValueError("source accepted split arrays differ from saved state")
        levels.append(d)
        filenames.append(name)
    if (originals != targets[phase_id] or not levels or levels[0] != 0
            or any(b <= a for a, b in zip(levels, levels[1:]))
            or len(set(filenames)) != len(filenames)
            or set(filenames) != {p.name for p in (stage / "steps").glob("*.npz")}
            or result.get("target_reached") is not True
            or result.get("reached_displacement") != targets[phase_id][-1]
            or result.get("target_metrics", {}).get("d") != targets[phase_id][-1]):
        raise ValueError("source success does not cover the complete frozen stage")
    return entries


def _source_audit(source_run, bindings):
    audit = read_json(source_run / "audit.json")
    if audit.get("schema_version") != "contact-c1-independent-audit-1.0" or audit.get("status") != "pass":
        raise ValueError("source independent audit must pass")
    recorded = audit.get("input_and_helper_sha256")
    if not isinstance(recorded, dict) or not recorded:
        raise ValueError("source audit has no bound inputs")
    # Audit paths are relative to the run. This permits verified relocation
    # without consulting historical drive names or the audit's display path.
    source_bound, helper_bound = {}, False
    for name, expected in recorded.items():
        if not isinstance(name, str) or "\\" in name or ":" in name or PurePosixPath(name).is_absolute():
            raise ValueError("source audit bindings must be relative POSIX paths")
        actual_path = (source_run / name).resolve()
        if actual_path.is_relative_to(source_run):
            source_bound[actual_path.relative_to(source_run).as_posix()] = expected
        elif not actual_path.is_relative_to(REPO):
            raise ValueError("source audit binding is outside its declared run/helpers")
        if actual_path == REPO / "scripts/audit_contact_c1.py":
            helper_bound = True
        if sha(actual_path) != expected:
            raise ValueError("source audit input/helper identity changed")
    if not helper_bound:
        raise ValueError("source audit must bind its independent audit helper")
    if any(source_bound.get(name) != expected for name, expected in bindings.items()):
        raise ValueError("source audit does not bind the full source evidence chain")
    return sha(source_run / "audit.json")


def _source_run(source_run, expected_kind, expected_h):
    source_run = Path(source_run).resolve()
    bindings = {}
    metadata = _source_metadata(source_run, expected_kind, expected_h, bindings)
    _, result = _completion(source_run, source_run, "stages/index.json", bindings)
    planned = ["uniform_tmc"] if expected_kind == "TMC" else ["uniform_precontact", "uniform_closed"]
    stages = read_json(source_run / "stages/index.json")["stages"]
    if metadata["planned_stages"] != planned or result["stages"] != stages or [s["phase_id"] for s in stages] != planned:
        raise ValueError("source run does not cover every declared uniform phase")
    for stage in stages:
        if stage["status"] != "success" or stage["directory"] != "stages/" + stage["phase_id"]:
            raise ValueError("source run stage is not successfully completed")
        _source_stage(source_run, stage["phase_id"], metadata, bindings)
    return metadata, bindings, _source_audit(source_run, bindings)


def source_state(source_run, phase_id, parameter, current_run, kind, *, expected_h=None):
    source_run, current_run = Path(source_run).resolve(), Path(current_run).resolve()
    source_kind = "TMC" if kind == "TMC" else "A0"
    if kind not in ("A0", "Aalpha", "TMC"):
        raise ValueError("undeclared receiving model")
    internal = source_run == current_run
    expected_phase = "uniform_precontact" if internal else "uniform_tmc" if kind == "TMC" else "uniform_closed"
    expected_parameter = .25 if internal else .375 if kind == "TMC" else .125
    if phase_id != expected_phase or parameter != expected_parameter or (internal and kind != "A0"):
        raise ValueError("source phase/parameter is not the frozen stage handoff")
    audit_hash = None
    if internal:
        bindings = {}
        metadata = _source_metadata(source_run, source_kind, expected_h, bindings)
    else:
        metadata, bindings, audit_hash = _source_run(source_run, source_kind, expected_h)
    entries = _source_stage(source_run, phase_id, metadata, bindings)
    found = [entry for entry in entries if entry["d"] == parameter and entry["is_original_target"]]
    if len(found) != 1:
        raise ValueError("source must have exactly one accepted requested preload state")
    entry = found[0]
    path = _confined(source_run / "stages" / phase_id / "steps", entry["file"])
    with np.load(path, allow_pickle=False) as arrays:
        state = SplitDisplacement(arrays["u_lift"], arrays["u_fluctuation"])
    provenance = dict(type="same_model_inheritance" if source_kind == kind else "cross_model_warm_start",
                      source_run=Path(os.path.relpath(source_run, current_run)).as_posix(),
                      source_phase_id=phase_id, source_state_file="steps/" + entry["file"],
                      source_state_sha256=entry["sha256"], source_step_index=entry["index"],
                      source_parameter=parameter, source_kind=source_kind,
                      source_state_identity_sha256=state_hash(state), source_evidence_sha256=bindings)
    if audit_hash is not None:
        provenance["source_audit_sha256"] = audit_hash
    return state, provenance


def component_actions(model, state, vector):
    """Differentiate both production residual parts; HP audit is independent."""
    args = (jnp.asarray(state.lift[model.edofs]), jnp.asarray(model.ops["grad"]),
            jnp.asarray(model.ops["hessian"]), jnp.asarray(model.ops["weights"]),
            jnp.asarray(model.lam), jnp.asarray(model.mu), jnp.asarray(model.kr))
    function = lambda w: split_kernel._batch_without_tangent(
        args[0], w, args[1], args[2], args[3], args[4], args[5], args[6])
    _, actions = jax.jvp(function, (jnp.asarray(state.fluctuation[model.edofs]),),
                         (jnp.asarray(vector[model.edofs]),))
    return {name: np.bincount(model.edofs.ravel(), weights=np.asarray(actions[name]).ravel(),
                             minlength=model.ndof)
            for name in ("material_residual", "regularization_residual")}


def run_stage(output, phase, kind, h, protocol, initial, provenance):
    problem = build_problem(kind, h, phase, initial_state=initial)
    model = problem.model
    stage = output / "stages" / phase
    (stage / "steps").mkdir(parents=True)
    write_npz(stage / "model.npz", coordinates=model.coordinates, connectivity=model.connectivity,
              lam=model.lam, mu=model.mu, kr=np.asarray(model.kr), fixed_dofs=model.fixed_dofs,
              solid=model.solid, F0=np.zeros(model.ndof), base=problem.base,
              direction=problem.direction, lift_origin=problem.lift_origin,
              lift_shape=problem.lift_shape, top_nodes=problem.top_nodes,
              bottom_nodes=problem.bottom_nodes, bottom_body_nodes=problem.bottom_body_nodes,
              measure_bottom_body=problem.measure_bottom_body,
              measure_bottom_total=problem.measure_bottom_total,
              **{"group_" + k: v for k, v in problem.reaction_groups.items()},
              **{k: model.ops[k] for k in ("grad", "hessian", "weights")})
    initial = problem.initial_state
    if initial is None:
        initial = SplitDisplacement(problem.lift_origin, np.zeros(model.ndof))
    write_npz(stage / "initial_state.npz", u_lift=initial.lift, u_fluctuation=initial.fluctuation)
    offset = .25 if phase == "uniform_closed" else .375 if phase == "perturbation" else 0.
    write_json(stage / "metadata.json", dict(schema="contact_c1_stage_v1", phase_id=phase,
               kind=kind, h=h, force_scale_per_length=100., model_sha256=sha(stage / "model.npz"),
               initial_state_sha256=sha(stage / "initial_state.npz"), source_initialization=provenance,
               targets=problem.targets, physical_mean_drive={"offset": offset,
               "slope": 0. if phase == "perturbation" else 1.}))
    entries = []
    write_json(stage / "steps/index.json", {"steps": entries})
    vector = np.sin(np.arange(model.ndof, dtype=float) + .37)
    vector[model.fixed_dofs] = 0.
    vector /= np.linalg.norm(vector)

    def accepted(record):
        index = len(entries)
        state = SplitDisplacement(record["u_lift"], record["u_fluctuation"])
        matrix, force, fields = split_kernel.assemble_split(model, state, tangent=True)
        actions = component_actions(model, state, vector)
        assembled = {key: np.bincount(model.edofs.ravel(), weights=fields[key].ravel(),
                                     minlength=model.ndof)
                     for key in ("material_residual", "regularization_residual")}
        filename = f"state_{index:03d}.npz"
        write_npz(stage / "steps" / filename, u_lift=state.lift, u_fluctuation=state.fluctuation,
                  internal_force=force, material_internal_force=assembled["material_residual"],
                  regularization_internal_force=assembled["regularization_residual"],
                  J=fields["J"], tangent_direction=vector, production_tangent_action=matrix @ vector,
                  material_tangent_action=actions["material_residual"],
                  regularization_tangent_action=actions["regularization_residual"])
        entry = {key: record[key] for key in ("d", "is_original_target",
                 "original_target_displacement", "bisection_depth")}
        entry.update(index=index, file=filename, sha256=sha(stage / "steps" / filename))
        entries.append(entry)
        write_json(stage / "steps/index.json", {"steps": entries})
        print(json.dumps(dict(phase_id=phase, accepted=index, s=record["d"],
                         residual=record["relative_residual"])), flush=True)

    result = solve_split_affine_path(model, problem.base, problem.direction,
                problem.lift_origin, problem.lift_shape, problem.targets, initial_state=problem.initial_state,
                reaction_groups=problem.reaction_groups,
                settings=PrescribedSettings(**protocol["solver"]), force_scale_per_length=100.,
                on_accept=accepted)
    write_json(stage / "result.json", result)
    write_json(stage / "completion.json", dict(finished_utc=timestamp(), status=result["status"],
                result_sha256=sha(stage / "result.json"), index_sha256=sha(stage / "steps/index.json"),
                metadata_sha256=sha(stage / "metadata.json"), accepted_states=len(entries)))
    return result


def run(output, kind, h, mode, protocol_path, preload_run=None):
    output, protocol_path = Path(output).resolve(), Path(protocol_path).resolve()
    if output.exists():
        raise FileExistsError("refusing to overwrite evidence")
    protocol = read_json(protocol_path)
    if protocol != read_json(REPO / "configs/contact_c1_v1.json") or sha(protocol_path) != PROTOCOL_SHA256:
        raise ValueError("only the frozen default protocol is implemented")
    if h not in protocol["mesh_sizes_mm"] or kind not in ("A0", "Aalpha", "TMC"):
        raise ValueError("undeclared model/mesh")
    if mode == "uniform":
        if preload_run or kind == "Aalpha":
            raise ValueError("uniform stage only accepts A0/TMC without inherited source")
        phases = ["uniform_precontact", "uniform_closed"] if kind == "A0" else ["uniform_tmc"]
    elif mode == "perturbation" and preload_run:
        phases = ["perturbation"]
        _source_run(Path(preload_run), "TMC" if kind == "TMC" else "A0", h)
    else:
        raise ValueError("undeclared mode or missing preload")
    output.mkdir(parents=True)
    (output / "stages").mkdir()
    sources = [*sorted((REPO / "src/hf_eval").glob("*.py")), Path(__file__),
               Path(__file__).with_name("hf4_common.py")]
    write_json(output / "metadata.json", dict(schema="contact_c1_run_v1", started_utc=timestamp(),
               kind=kind, h=h, mode=mode, planned_stages=phases, protocol=protocol,
               implementation_revision="explicit_activation_transfer_v1",
               protocol_sha256=sha(protocol_path),
               source_sha256={p.relative_to(REPO).as_posix(): sha(p) for p in sources},
               environment={"python": platform.python_version(), "platform": platform.platform(),
                   **{name: importlib.metadata.version(name) for name in ("numpy", "scipy", "jax", "jaxlib")}},
               authority="stored lift and fluctuation exact sum; no display array authority"))
    stages, status = [], "success"
    write_json(output / "stages/index.json", {"stages": stages})
    for phase in phases:
        initial, provenance = None, {"type": "geometric_zero"}
        if phase == "uniform_closed":
            initial, provenance = source_state(output, "uniform_precontact", .25, output, kind, expected_h=h)
            initial, transfer = prepare_closed_initial(initial, h)
            provenance["activation_projection"] = transfer
        elif phase == "perturbation":
            initial, provenance = source_state(preload_run, "uniform_tmc" if kind == "TMC" else "uniform_closed",
                                                .375 if kind == "TMC" else .125, output, kind, expected_h=h)
        record = {"phase_id": phase, "directory": "stages/" + phase, "status": "running"}
        stages.append(record)
        write_json(output / "stages/index.json", {"stages": stages})
        result = run_stage(output, phase, kind, h, protocol, initial, provenance)
        record["status"] = result["status"]
        write_json(output / "stages/index.json", {"stages": stages})
        if result["status"] != "success":
            status = result["status"]
            break
    write_json(output / "result.json", {"status": status, "stages": stages})
    write_json(output / "completion.json", dict(finished_utc=timestamp(), status=status,
               result_sha256=sha(output / "result.json"), index_sha256=sha(output / "stages/index.json"),
               metadata_sha256=sha(output / "metadata.json")))
    print(json.dumps(dict(status=status, kind=kind, h=h, mode=mode)), flush=True)
    return status == "success"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--kind", choices=("A0", "Aalpha", "TMC"), required=True)
    parser.add_argument("--h", type=float, required=True)
    parser.add_argument("--mode", choices=("uniform", "perturbation"), required=True)
    parser.add_argument("--preload-run")
    parser.add_argument("--protocol", default=str(REPO / "configs/contact_c1_v1.json"))
    args = parser.parse_args()
    if Path(args.output).exists():
        parser.error("output already exists")
    try:
        ok = run(args.output, args.kind, args.h, args.mode, args.protocol, args.preload_run)
    except Exception as error:
        directory = Path(args.output)
        if directory.is_dir() and not (directory / "exception.json").exists():
            write_json(directory / "exception.json", dict(type=type(error).__name__, message=str(error), utc=timestamp()))
        raise
    raise SystemExit(0 if ok else 2)
