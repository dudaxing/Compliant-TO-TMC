"""Pack accepted MATLAB source states only; no mechanics or restart performed."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="cshape_001")
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    run = base / args.run_id
    setup_path = base / "setup_002/cshape_setup.npz"
    with np.load(setup_path, allow_pickle=False) as data:
        setup = {k: data[k] for k in data.files}
    index = json.loads((run / "path_index_matlab.json").read_text())
    process = json.loads((run / "process_record.json").read_text())
    maps_d = setup["canonical_to_source_dofs"]
    maps_e = setup["canonical_to_source_elements"]
    records = [loadmat(run / step["mat_path"], squeeze_me=True) for step in index["steps"]]
    arrays = {"original_targets": setup["targets"], "targets": np.array([s["lambda"] for s in index["steps"]]),
              "coordinates": setup["coordinates"], "connectivity": setup["connectivity"],
              "gamma": setup["gamma"], "F0": setup["F0"], "fixed_dofs": setup["fixed_dofs"],
              "loaded_nodes": setup["loaded_nodes"], "loaded_dofs": setup["loaded_dofs"]}
    keys = ["U_source", "internal_force_source", "reaction_source", "J_source", "material_energy_source", "force_balance"]
    for key in keys:
        arrays[key] = np.stack([np.asarray(s[key]) for s in records]) if records else np.empty((0,))
    if records:
        arrays.update(U=arrays["U_source"][:, maps_d], reaction=arrays["reaction_source"][:, maps_d],
                      internal_force=arrays["internal_force_source"][:, maps_d], J=arrays["J_source"][:, maps_e],
                      material_energy=arrays["material_energy_source"][:, maps_e])
        arrays["loaded_displacements"] = arrays["U"].reshape(len(records), -1, 2)[:, setup["loaded_nodes"], :]
    for key in ["min_J", "relative_free_residual", "material_energy_solid", "material_energy_medium", "fixed_displacement_max",
                "force_balance_absolute", "target_index", "newton_checks", "solve_seconds", "postprocess_seconds", "elapsed_driver_seconds"]:
        arrays[key] = np.array([s[key] for s in records])
    path = run / "cshape_path.npz"
    np.savez_compressed(path, **arrays)
    index["source_driver_status"] = index["status"]
    if process["termination_reason"] != "completed":
        index["status"] = process["termination_reason"]
    index.update(schema_version="hf2-cshape-reference-1.0", npz_path=path.name, sha256=sha(path),
                 setup_npz_path="../setup_002/cshape_setup.npz", setup_sha256=sha(setup_path),
                 process_record_path="process_record.json", process_record_sha256=sha(run/"process_record.json"),
                 process_wall_seconds=process["wall_seconds"], peak_sampled_tree_rss_bytes=process["peak_sampled_tree_rss_bytes"],
                 source_zip_sha256=json.loads((base/"validation_spec.json").read_text())["source_zip_sha256"],
                 validation_spec_sha256=sha(base/"validation_spec.json"),
                 point_postprocessor="J, reference-volume weighted material energy external; force/reaction from original assembleKtFi",
                 arrays={k:{"shape":list(v.shape),"dtype":str(v.dtype)} for k,v in arrays.items()})
    for step in index["steps"]:
        step["mat_sha256"] = sha(run/step["mat_path"])
    (run/"cshape_path.json").write_text(json.dumps(index,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"status":index["status"],"accepted_count":index["accepted_count"],"last_accepted_lambda":index["last_accepted_lambda"],"wall_seconds":index["process_wall_seconds"]},indent=2))


if __name__ == "__main__":
    main()
