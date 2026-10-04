"""Export all saved fixed-workpiece nodal weak forces; no mechanical replay."""
from time import perf_counter
STARTED = perf_counter()
import argparse
import csv
import json
from pathlib import Path
import sys
from hashlib import sha256
from math import fsum
import numpy as np

from measure_native_workpiece_regions import descriptor_sha, file_sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "input", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--reference", type=Path, help="Optional same-path passing reference; absent means no reference qualification")
    parser.add_argument("--time-limit", type=float, default=120.)
    parser.add_argument("--stop-file", type=Path)
    args = parser.parse_args()
    directory = args.input.resolve()
    directory = directory.parent if directory.is_file() else directory
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    repo = args.repo.resolve()
    reference_file = args.reference.resolve() if args.reference else None
    pins = {}
    states = []
    started = completed = 0
    failure = None
    mechanical_scope_verified = False
    modules = []
    source_snapshots = {}
    reference = None

    def role(path):
        if path.is_relative_to(repo):
            return "repo/"+path.relative_to(repo).as_posix()
        if path.is_relative_to(directory):
            return "input/"+path.relative_to(directory).as_posix()
        if path == reference_file:
            return "reference"
        raise ValueError("Observation input has no declared path role")

    def bind(path, expected=None):
        value = file_sha(path)
        if expected is not None and value != expected:
            raise ValueError("Saved file SHA differs: "+path.name)
        pins[path] = value
        return value

    def read(path, expected=None, descriptor=False):
        bind(path, expected)
        value = json.loads(path.read_text(encoding="utf-8"))
        if descriptor and descriptor_sha(value) != value["descriptor_sha256"]:
            raise ValueError("Saved semantic descriptor differs: "+path.name)
        return value

    def archive(path, declared):
        bind(path, declared["sha256"])
        with np.load(path, allow_pickle=False) as saved:
            arrays = {name: saved[name].copy() for name in saved.files}
        actual = {name: dict(dtype=value.dtype.name, shape=list(value.shape),
                  sha256=sha256(value.tobytes()).hexdigest()) for name, value in arrays.items()}
        if actual != declared["fields"]:
            raise ValueError("Saved archive fields differ: "+path.name)
        return arrays

    def checkpoint():
        if perf_counter()-STARTED > args.time_limit or (args.stop_file and args.stop_file.exists()):
            raise RuntimeError("Saved nodal-force observation window closed")

    try:
        sys.path.insert(0, str(args.repo.resolve()/"src"))
        from hf_eval.workpiece_nodal import observe_workpiece_nodal_forces, COMPONENTS, GROUPS
        sources = [args.repo.resolve()/"src/hf_eval"/name for name in
                   ("__init__.py", "workpiece_nodal.py", "boundary_geometry.py")]
        sources += [Path(__file__).resolve(), Path(__file__).with_name("measure_native_workpiece_regions.py").resolve()]
        (output/"sources").mkdir()
        for source in sources:
            bind(source)
            snapshot = output/"sources"/source.name
            snapshot.write_bytes(source.read_bytes())
            if file_sha(snapshot) != file_sha(source):
                raise ValueError("Saved source snapshot differs")
            source_snapshots[role(source)] = dict(path=snapshot.relative_to(output).as_posix(), sha256=file_sha(source))
        result = read(directory/"result.json", descriptor=True)
        if reference_file is not None:
            reference = read(reference_file)
        if reference is not None and (reference["status"] != "pass" or reference["result_sha256"] != file_sha(directory/"result.json")
                or reference["accepted_states"] != len(result["states"])
                or len(reference["states"]) != len(result["states"])):
            raise ValueError("Require the same saved path's passing reference")
        model_file = directory/result["model"]["descriptor_path"]
        metadata = read(model_file, result["model"]["descriptor_file_sha256"], descriptor=True)
        if (metadata["descriptor_sha256"] != result["model"]["descriptor_sha256"]
                or metadata["arrays"]["sha256"] != result["model"]["arrays_sha256"]
                or metadata["task_sha256"] != result["task_sha256"]):
            raise ValueError("Saved model/task identities differ from the path")
        model = archive(model_file.parent/metadata["arrays"]["path"], metadata["arrays"])
        definition = metadata["region_metadata"]["workpiece"]["definition"]
        centre = definition["center_mm"]
        headers = ["accepted_index", "original_target_index", "leg", "d_mm", "state_sha256",
                   "node_id", "x_mm", "y_mm", "group"]
        headers += [name+"_F"+axis+"_N" for name in COMPONENTS for axis in ("x", "y")]
        with (output/"nodes.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream); writer.writerow(headers)
            for index, state in enumerate(result["states"]):
                checkpoint()
                if reference is not None:
                    checked = reference["states"][index]
                    if (checked["status"] != "pass" or checked["index"] != index
                            or checked["state_sha256"] != state["state_sha256"]
                            or checked["original_target_index"] != state["original_target_index"]
                            or checked["leg"] != state["leg"] or checked["target_mm"] != state["d"]):
                        raise ValueError("Saved reference state identity or path context differs")
                stored = read(directory/state["descriptor_path"], state["descriptor_file_sha256"], descriptor=True)
                if stored != {k:v for k,v in state.items() if k not in ("descriptor_path", "descriptor_file_sha256")}:
                    raise ValueError("Saved state record differs from the path record")
                displacement = archive(directory/state["state"]["path"], state["state"])
                body_dofs = model["workpiece_dofs"]
                if any(np.any(displacement[name][body_dofs]) for name in ("lift", "fluctuation")):
                    raise ValueError("Nodal-force positions require the saved fixed body")
                force_arrays = archive(directory/state["forces"]["path"], state["forces"])
                started += 1
                observed = observe_workpiece_nodal_forces(model, force_arrays,
                    symmetry_y_mm=centre[1], moment_origin_mm=centre)
                complete = observed["summary"]
                if complete["force_on_lower_body_N"] != state["workpiece"]["force_on_lower_body_N"]:
                    raise ValueError("Nodal sums differ from the saved body resultant")
                if complete["holding_reaction_on_model_N"] != state["workpiece"]["holding_reaction_on_model_N"]:
                    raise ValueError("Nodal holding sum differs from the saved reaction")
                selected_holding = force_arrays["support_reaction"].reshape(-1, 2)[observed["node_ids"]]
                if not np.array_equal(-observed["forces_on_body_N"]["total"], selected_holding):
                    raise ValueError("Saved total body force is not minus holding at every node")
                partition_errors = {}
                for component in COMPONENTS:
                    force = observed["forces_on_body_N"][component]
                    reconstructed = [fsum(complete["groups"][group]["force_on_body_N"][component][axis]
                                     for group in GROUPS) for axis in (0, 1)]
                    error = [reconstructed[axis]-complete["force_on_lower_body_N"][component][axis]
                             for axis in (0, 1)]
                    bounds = [8*np.finfo(float).eps*fsum(abs(float(v)) for v in force[:, axis])
                              for axis in (0, 1)]
                    if any(abs(e) > b for e, b in zip(error, bounds)):
                        raise ValueError("Disjoint node-group sums exceed their rounding bound")
                    partition_errors[component] = dict(error_N=error, roundoff_bound_N=bounds)
                masks = observed["masks"]
                if not np.all(np.sum(list(masks.values()), axis=0) == 1):
                    raise ValueError("Every body node must belong to exactly one group")
                for row, (node, point) in enumerate(zip(observed["node_ids"], observed["coordinates_mm"])):
                    group = next(name for name in GROUPS if masks[name][row])
                    values = [float(value) for name in COMPONENTS for value in observed["forces_on_body_N"][name][row]]
                    writer.writerow([index, state["original_target_index"], state["leg"], state["d"],
                                     state["state_sha256"], int(node), *point.tolist(), group, *values])
                states.append(dict(index=index, original_target_index=state["original_target_index"],
                    leg=state["leg"], d_mm=state["d"], state_sha256=state["state_sha256"],
                    moment_origin_mm=observed["moment_origin_mm"].tolist(), summary=complete,
                    group_roundoff=partition_errors,
                    total_minus_component_sum_max_abs_N=float(np.max(np.abs(
                        observed["forces_on_body_N"]["total"]-observed["forces_on_body_N"]["material"]
                        -observed["forces_on_body_N"]["regularization"]))),
                    edges={name: value.tolist() for name, value in observed["edges"].items()}))
                completed += 1
                checkpoint()
        modules = sorted(name for name in sys.modules if name == "hf_eval" or name.startswith("hf_eval."))
        if set(modules)-{"hf_eval", "hf_eval.workpiece_nodal", "hf_eval.boundary_geometry"}:
            raise ValueError("A mechanical hf_eval module was imported")
        for name in modules:
            path = repo/"src/hf_eval"/("__init__.py" if name == "hf_eval" else name.split(".")[-1]+".py")
            if Path(sys.modules[name].__file__).resolve() != path:
                raise ValueError("Pure observation module came from a different repository")
        mechanical_scope_verified = True
        if not all(file_sha(path) == value for path, value in pins.items()):
            raise ValueError("Saved observation sources or inputs changed")
        checkpoint()
    except BaseException as error:
        failure = repr(error)
        raise
    finally:
        report = dict(schema_version="saved-workpiece-nodal-forces-1.0", status="pass" if failure is None else "failed",
            observations_started=started, observations_completed=completed, states=states, failure=failure,
            elapsed_seconds=perf_counter()-STARTED, input_source_bindings={role(p):v for p,v in pins.items()},
            source_snapshots=source_snapshots, production_status=result["status"] if "result" in locals() else None,
            reference_available=reference is not None, saved_reference_status=reference["status"] if reference else "not_available",
            loaded_hf_eval_modules=modules, mechanical_scope_verified=mechanical_scope_verified,
            new_force_tangent_solver_HP_calls=0 if mechanical_scope_verified else None, mechanical_hooks_monitored=False,
            call_count_basis="Saved global-vector lookup and pure boundary topology; no mechanical modules called",
            scope="Signed weak nodal forces in N and derived nodal moment in Nmm; no face-force allocation, pressure, contact or clamp qualification")
        with (output/"summary.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write("\n")
    print(json.dumps(dict(status=report["status"], accepted_states=completed, nodal_rows=len(model["workpiece_nodes"])*completed)))


if __name__ == "__main__":
    main()
