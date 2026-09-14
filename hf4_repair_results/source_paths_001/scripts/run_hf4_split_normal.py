"""Run exactly one frozen normal-contact combination with state-first evidence."""
from pathlib import Path
import argparse
from dataclasses import asdict
import os
import sys

os.environ.setdefault("JAX_ENABLE_X64", "true")
os.environ.setdefault("JAX_PLATFORMS", "cpu")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))

import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
from hf_eval.normal_contact import build_normal_contact, normal_task_from_spec
from hf_eval.prescribed import PrescribedSettings
from hf_eval.split_state import SplitDisplacement
from hf_eval.split_prescribed import solve_split_prescribed_path, normal_lift_shape, split_linear_measurement, STATE_SCHEMA, LIFT_SCHEME
from hf4_common import read_json, write_json, write_npz, sha, source_record, timestamp


def run(spec_path, gamma_index, mesh_index, output, *, first_target_only=False):
    spec = read_json(spec_path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output/"steps").mkdir()
    task = normal_task_from_spec(spec, spec["gammas"][gamma_index], spec["mesh_sizes_mm"][mesh_index])
    p = build_normal_contact(task)
    settings = PrescribedSettings(**spec["solver"])
    m = p.model
    lift_shape = normal_lift_shape(p)
    requested_targets = task["targets_mm"][:2] if first_target_only else task["targets_mm"]
    metadata = dict(schema_version="hf4-split-normal-evidence-1.0", created_utc=timestamp(),
                    state_representation=STATE_SCHEMA, lift_scheme=LIFT_SCHEME,
                    requested_targets=requested_targets, execution_scope="first_target_probe" if first_target_only else "full_path",
                    task=task, task_sha256=p.task_sha256, geometry_id=p.geometry_id, mesh_id=p.mesh_id,
                    spec=spec, spec_sha256=sha(spec_path), source_files=source_record(),
                    reference_inputs=p.reference_inputs, regions=p.regions,
                    settings=asdict(settings), gamma_index=gamma_index, mesh_index=mesh_index,
                    force_scale_per_length=task["material"]["E_MPa"]*task["geometry"]["thickness_mm"])
    write_json(output/"metadata.json", metadata)
    arrays = dict(coordinates=m.coordinates, connectivity=m.connectivity, body_ids=p.body_ids,
                  lam=m.lam, mu=m.mu, kr=np.array(m.kr), hx=np.array(m.hx), hy=np.array(m.hy),
                  thickness=np.array(m.thickness), solid=m.solid, fixed_dofs=m.fixed_dofs,
                  base=p.base, direction=p.direction, gap_vector=p.gap_vector, lift_shape=lift_shape, **m.ops,
                  **{"group_"+k:v for k,v in p.reaction_groups.items()})
    write_npz(output/"model.npz", **arrays)
    index = []

    def persist(record):
        i = len(index)
        name = f"state_{i:04d}"
        numerical = {k:v for k,v in record.items() if isinstance(v,np.ndarray)}
        scalar = {k:v for k,v in record.items() if not isinstance(v,np.ndarray)}
        scalar["gap_mm"] = split_linear_measurement(SplitDisplacement(record["u_lift"],record["u_fluctuation"]), p.gap_vector, task["geometry"]["gap_mm"])
        scalar["index"] = i
        write_npz(output/"steps"/(name+".npz"), **numerical)
        write_json(output/"steps"/(name+".json"), scalar)
        index.append(dict(index=i, d=record["d"], file=name+".npz", metadata=name+".json",
                          arrays_sha256=sha(output/"steps"/(name+".npz")),
                          metadata_sha256=sha(output/"steps"/(name+".json"))))
        write_json(output/"steps/index.json", dict(accepted_count=len(index), steps=index))

    result = solve_split_prescribed_path(m, p.base, p.direction, lift_shape, requested_targets,
                                  reaction_groups=p.reaction_groups, settings=settings,
                                  force_scale_per_length=metadata["force_scale_per_length"], on_accept=persist)
    if result.get("last_attempt_candidate") is not None:
        failure_state = result["last_attempt_candidate"]
        arrays = {k:v for k,v in failure_state.items() if isinstance(v,np.ndarray)}
        if result.get("last_corrector") is not None:
            arrays["last_corrector"] = result["last_corrector"]
        write_npz(output/"failed_candidate.npz", **arrays)
        write_json(output/"failed_candidate.json", {k:v for k,v in failure_state.items() if not isinstance(v,np.ndarray)})
        result["last_attempt_candidate"] = {"arrays_file":"failed_candidate.npz", "arrays_sha256":sha(output/"failed_candidate.npz"),
                                           "metadata_file":"failed_candidate.json", "metadata_sha256":sha(output/"failed_candidate.json")}
    result.pop("last_corrector", None)
    # Full per-state arrays have already been committed; result carries scalar history.
    for key in ("accepted_steps",):
        if key in result:
            result[key] = [{k:v for k,v in r.items() if not isinstance(v,np.ndarray)} for r in result[key]]
    for key in ("last_accepted_state", "target_metrics"):
        if isinstance(result.get(key),dict):
            result[key] = {k:v for k,v in result[key].items() if not isinstance(v,np.ndarray)}
    write_json(output/"result.json", result)
    print({"output":str(output), "status":result["status"], "accepted_states":len(index)}, flush=True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--gamma-index", type=int, choices=(0,1), required=True)
    parser.add_argument("--mesh-index", type=int, choices=(0,1), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--first-target-only", action="store_true")
    a = parser.parse_args()
    r = run(a.spec, a.gamma_index, a.mesh_index, a.output, first_target_only=a.first_target_only)
    raise SystemExit(0 if r["status"] == "success" else 2)
