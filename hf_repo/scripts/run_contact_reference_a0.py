"""Persist one prospectively declared A0 path; no LF or N-line imports."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import platform
import sys

import numpy as np
import jax

jax.config.update("jax_enable_x64", True)

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from hf_eval.contact_reference_a0 import closed_plane_problem
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_kernel import assemble_split
from hf_eval.split_prescribed import solve_split_prescribed_path
from hf_eval.split_state import SplitDisplacement
from hf4_common import write_json, write_npz, sha, timestamp


def run(output, h, amplitude, protocol_path):
    output, protocol_path = Path(output).resolve(), Path(protocol_path).resolve()
    if output.exists():
        raise FileExistsError("refusing to replace an existing run: " + str(output))
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if (protocol["schema"] != "contact_reference_a0_v1"
            or h not in protocol["mesh_sizes_mm"] or amplitude not in protocol["amplitudes"]):
        raise ValueError("undeclared task")
    # This builder implements exactly this immutable physical task. A changed
    # protocol must not silently describe different mechanics from the code.
    if (protocol["geometry"] != {"width_mm": 2., "height_mm": 1., "thickness_mm": 1.,
                                "obstacle_rectangle_mm": [-2., 4., 1., 2.]}
            or protocol["material"] != {"E_N_per_mm2": 100., "nu": .3, "kr": 0.}
            or protocol["targets_mm"] != [0., .03125, .0625, .125, .25]):
        raise ValueError("task builder and protocol disagree")
    problem = closed_plane_problem(h, amplitude)
    model = problem.model
    output.mkdir(parents=True)
    (output / "steps").mkdir()
    write_npz(output / "model.npz", coordinates=model.coordinates,
              connectivity=model.connectivity, lam=model.lam, mu=model.mu,
              kr=np.asarray(model.kr), fixed_dofs=model.fixed_dofs, solid=model.solid,
              F0=np.zeros(model.ndof), base=problem.base, direction=problem.direction,
              lift_shape=problem.lift_shape, top_nodes=problem.top_nodes,
              bottom_nodes=problem.bottom_nodes, **{k: model.ops[k] for k in ("grad", "hessian", "weights")})
    sources = [*sorted((REPO / "src/hf_eval").glob("*.py")), Path(__file__),
               Path(__file__).with_name("hf4_common.py")]
    metadata = {"schema": "contact_reference_a0_run_v1", "started_utc": timestamp(),
                "task": {"W": 2., "H": 1., "E": 100., "nu": .3, "t": 1., "h": h,
                         "amplitude": amplitude, "targets": protocol["targets_mm"]},
                "force_scale_per_length": 100., "protocol": protocol,
                "protocol_sha256": sha(protocol_path), "model_sha256": sha(output / "model.npz"),
                "source_sha256": {p.relative_to(REPO).as_posix(): sha(p) for p in sources},
                "environment": {"python": platform.python_version(), "platform": platform.platform(),
                                **{name: importlib.metadata.version(name) for name in ("numpy", "scipy", "jax", "jaxlib")}},
                "independence": "contact task only; same O material FE and solver; independent Decimal audit required",
                "authority": "u_lift and u_fluctuation as exact sum, never u_display"}
    write_json(output / "metadata.json", metadata)
    entries = []
    write_json(output / "steps/index.json", {"steps": entries})
    # A deterministic arbitrary perturbation, independent of any equilibrium
    # reference. It is zero on prescribed DOFs and normalized in displacement.
    v = np.sin(np.arange(model.ndof, dtype=float) + .37)
    v[model.fixed_dofs] = 0.
    v /= np.linalg.norm(v)

    def accepted(record):
        i = len(entries)
        filename = f"state_{i:03d}.npz"
        state = SplitDisplacement(record["u_lift"], record["u_fluctuation"])
        K, _, _ = assemble_split(model, state, tangent=True)
        write_npz(output / "steps" / filename, u_lift=state.lift,
                  u_fluctuation=state.fluctuation, internal_force=record["internal_force"],
                  J=record["J"], tangent_direction=v, production_tangent_action=K @ v)
        entry = {key: record[key] for key in ("d", "is_original_target",
                 "original_target_displacement", "bisection_depth")}
        entry.update(index=i, file=filename, sha256=sha(output / "steps" / filename))
        entries.append(entry)
        write_json(output / "steps/index.json", {"steps": entries})
        print(json.dumps({"accepted": i, "d": record["d"], "residual": record["relative_residual"]}), flush=True)

    result = solve_split_prescribed_path(model, problem.base, problem.direction,
                problem.lift_shape, protocol["targets_mm"], reaction_groups=problem.reaction_groups,
                settings=PrescribedSettings(**protocol["solver"]), force_scale_per_length=100., on_accept=accepted)
    write_json(output / "result.json", result)
    write_json(output / "completion.json", {"finished_utc": timestamp(), "status": result["status"],
                "result_sha256": sha(output / "result.json"), "index_sha256": sha(output / "steps/index.json"),
                "metadata_sha256": sha(output / "metadata.json"), "accepted_states": len(entries)})
    print(json.dumps({"status": result["status"], "accepted": len(entries), "failure": result["failure"]}), flush=True)
    return result["status"] == "success"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--h", type=float, required=True)
    parser.add_argument("--amplitude", type=float, required=True)
    parser.add_argument("--protocol", default=str(REPO / "configs/contact_reference_a0_v1.json"))
    args = parser.parse_args()
    if Path(args.output).exists():
        parser.error("output already exists; choose a new evidence directory")
    try:
        ok = run(args.output, args.h, args.amplitude, args.protocol)
    except Exception as error:
        directory = Path(args.output)
        if directory.is_dir() and not (directory / "exception.json").exists():
            write_json(directory / "exception.json", {"type": type(error).__name__, "message": str(error), "utc": timestamp()})
        raise
    raise SystemExit(0 if ok else 2)
