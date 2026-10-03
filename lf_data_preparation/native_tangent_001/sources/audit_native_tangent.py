"""Independent HP80/120 audit of two saved native mechanical directions.

All local matrix entries and the full CSC assembly are checked. Independent
mechanics references cover every element/DOF for the two declared directions,
not all matrix columns. Lift is fixed; directions are dimensionless shapes
with a displacement parameter in mm, so directional actions have units N/mm.
No production mechanics, model constructor or matrix assembler is imported.
"""
from __future__ import annotations

from time import perf_counter
STARTED = perf_counter()
import argparse
from decimal import Decimal, Inexact, localcontext
import hashlib
from pathlib import Path
import shutil

import numpy as np
import psutil
from scipy import sparse

from audit_native_force import (HP_HASHES, D, canonical_hash, norm, npz, read,
    require, same_arrays, sha, state_hash, verify_descriptor, verify_fields, write, write_gzip)

COMPONENTS = ("total", "material", "regularization")
HP_KEYS = ("tangent_action_decimal", "material_tangent_action_decimal", "regularization_tangent_action_decimal")
LIMITS = (Decimal("1e-10"), Decimal("1e-9"), Decimal("1e-9"))
HP_LIMIT, FLOOR = Decimal("1e-40"), Decimal("1e-10")
RSS_LIMIT = 8*1024**3
HELPER_SHA = "cd317914cba2e3ad2f5ec5bf5b857804c3406313ab6a433bd1d7b395872ee8bb"


def compare(actual, reference, other):
    denominator = max(norm(reference), FLOOR)
    difference = [D(a)-b for a, b in zip(actual, reference, strict=True)]
    return dict(normalized_error=norm(difference)/denominator,
        hp80_hp120_error=norm([a-b for a, b in zip(reference, other, strict=True)])/denominator,
        denominator_N_per_mm=denominator), difference


def group_inputs(model, state, direction, edofs, checkpoint):
    common = b"".join(model[key].tobytes() for key in ("kr", "grad", "hessian", "weights"))
    left, right, v = state["lift"][edofs], state["fluctuation"][edofs], direction[edofs]
    lookup, groups, membership = {}, [], np.empty(len(edofs), dtype=np.int64)
    for element in range(len(edofs)):
        if element % 256 == 0:
            checkpoint()
        key = common+left[element].tobytes()+right[element].tobytes()
        key += model["lam"][element:element+1].tobytes()+model["mu"][element:element+1].tobytes()+v[element].tobytes()
        if key not in lookup:
            lookup[key] = len(groups)
            groups.append(dict(representative=element, members=[], raw_key_sha256=hashlib.sha256(key).hexdigest()))
        membership[element] = lookup[key]
        groups[lookup[key]]["members"].append(element)
    return groups, membership, left, right, v


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--time-limit", type=float, default=120.)
    args = parser.parse_args()
    require(np.isfinite(args.time_limit) and 0 < args.time_limit <= 120., "Time limit must be in (0,120]")
    repo, stage, output = Path(__file__).resolve().parents[2], args.input.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    process, peak, bindings, sources, records = psutil.Process(), 0, {}, {}, []
    started_calls = completed_calls = checks = 0

    def checkpoint():
        nonlocal peak
        peak = max(peak, process.memory_info().rss)
        require(perf_counter()-STARTED <= args.time_limit, "Independent tangent audit time limit exceeded")
        require(peak <= RSS_LIMIT, "Independent tangent audit sampled RSS limit exceeded")

    def bind(path, expected=None):
        actual = sha(path)
        require(expected is None or expected == actual, "Bound file differs: "+str(path))
        require(path not in bindings or bindings[path] == actual, "Previously bound file changed: "+str(path))
        bindings[path] = actual
        return actual

    def check(condition, message):
        nonlocal checks
        require(condition, message)
        checks += 1

    def file_record(path):
        return dict(path=path.relative_to(output).as_posix(), sha256=sha(path))

    def lifecycle(status, error=None):
        write(output/"lifecycle.json", dict(status=status, error=error, elapsed_seconds=perf_counter()-STARTED,
            HP_calls_started=started_calls, HP_calls_completed=completed_calls, checks_completed=checks,
            completed_directions=len(records), sampled_peak_RSS_bytes=peak, time_limit_seconds=args.time_limit,
            sampled_RSS_limit_bytes=RSS_LIMIT, stop_policy="First failure stops; no retry, repair or solve"))

    def gate(values, limit, label):
        values.update(limit=str(limit), reference_limit=str(HP_LIMIT),
            pass_gate=values["normalized_error"].is_finite() and values["hp80_hp120_error"].is_finite()
                and values["normalized_error"] <= limit and values["hp80_hp120_error"] <= HP_LIMIT)
        check(values["pass_gate"], "Failed "+label+": "+str(values))

    try:
        checkpoint()
        inventory_path, receipt_path = stage/"input_inventory.json", stage/"execution_receipt.json"
        bind(inventory_path)
        bind(receipt_path)
        inventory, receipt = read(inventory_path), read(receipt_path)
        check(inventory["schema_version"] == "native-tangent-input-inventory-1.0"
              and len(inventory["cases"]) == 1, "Wrong one-state inventory")
        row = inventory["cases"][0]
        check({key: Decimal(value) for key, value in inventory["thresholds"].items()}
              == dict(zip(COMPONENTS, LIMITS, strict=True), HP80_HP120=HP_LIMIT),
              "Original tangent/reference gates changed")
        check((row["alias"], row["state_name"], row["elements"], row["dofs"])
              == ("gripper_canonical", "checker", 3200, 6642), "Wrong ordinary coarse supplied state")
        check(receipt["status"] == "pass" and receipt["invocations"] == 1
              and receipt["force_calls"] == receipt["tangent_calls"] == 1
              and receipt["HP_calls"] == receipt["solver_calls"] == 0
              and receipt["input_inventory_sha256"] == sha(inventory_path), "Production scope/identity differs")
        frozen = output/"sources"
        frozen.mkdir()
        for name, expected in receipt["sources"].items():
            bind(repo/name, expected)
            bind(stage/"sources"/Path(name).name, expected)
            shutil.copyfile(repo/name, frozen/Path(name).name)
            sources[name] = expected
        for name, expected in receipt["inputs"].items():
            bind(repo/name, expected)
        for name, expected in {**HP_HASHES, "audit_native_force.py": HELPER_SHA}.items():
            path = Path(__file__).with_name(name)
            bind(path, expected)
            shutil.copyfile(path, frozen/name)
            sources[path.relative_to(repo).as_posix()] = expected
        sources[Path(__file__).relative_to(repo).as_posix()] = bind(Path(__file__))
        shutil.copyfile(__file__, frozen/Path(__file__).name)
        for path in (inventory_path, receipt_path):
            shutil.copyfile(path, output/path.name)
        for key, pin in (("geometry_file", "geometry_file_sha256"), ("geometry_npz_file", "geometry_npz_sha256"),
                         ("task_file", "task_file_sha256"), ("prior_model_file", "prior_model_sha256"),
                         ("state_file", "state_file_sha256")):
            bind(repo/row[key], row[pin])
        origin = stage/row["result_directory"]
        result_path = origin/"result.json"
        bind(result_path, receipt["result_sha256"])
        result = read(result_path)
        verify_descriptor(result)
        check(result["schema_version"] == "hf-native-tangent-result-1.0" and result["matrix_units"] == "N/mm"
              and result["scope"] == "supplied_displacement_test_only" and result["backend"] == "numpy"
              and result["evaluation_mode"] == "three_component_tangent"
              and result["fixed_DOF_rows_columns_retained"] is True and result["matrices_symmetrized"] is False
              and result["fixed_displacement_compatible"] is True and result["JIT_calls"] == 0
              and result["force_calls"] == result["tangent_calls"] == 1
              and result["HP_calls"] == result["solver_calls"] == 0
              and result["equilibrium_qualified"] is False and result["task_target_executed"] is False,
              "Candidate tangent scope differs")
        model_path, model_json_path = (origin/result["model"][key] for key in ("arrays_path", "descriptor_path"))
        bind(model_path, result["model"]["arrays_sha256"])
        bind(model_path, receipt["model_sha256"])
        bind(model_json_path, result["model"]["descriptor_file_sha256"])
        model, metadata = npz(model_path), read(model_json_path)
        verify_descriptor(metadata)
        verify_fields(model, metadata["arrays"]["fields"])
        same_arrays(model, npz(repo/row["prior_model_file"]), "Reviewed versus candidate 23-field native model")
        check(len(model) == 23 and metadata["schema_version"] == "hf-native-project-model-1.0"
              and metadata["descriptor_sha256"] == result["model"]["descriptor_sha256"]
              and metadata["arrays"]["sha256"] == sha(model_path), "Model declaration differs")
        task = read(repo/row["task_file"])
        check(metadata["task"] == task and metadata["task_sha256"] == canonical_hash(task) == result["task_sha256"],
              "Original construction TEST task differs")
        source = metadata["source_geometry"]
        expected_source = dict(source, snapshot={key: "model/"+path for key, path in source["snapshot"].items()})
        check(result["source_geometry"] == expected_source and source["geometry_id"] == row["geometry_id"]
              and source["descriptor_file_sha256"] == row["geometry_file_sha256"]
              and source["arrays_sha256"] == row["geometry_npz_sha256"]
              and source["descriptor_sha256"] == read(repo/row["geometry_file"])["descriptor_sha256"],
              "Source geometry identity/path context differs")
        for key, pin in (("descriptor", "geometry_file_sha256"), ("arrays", "geometry_npz_sha256")):
            bind(origin/expected_source["snapshot"][key], row[pin])
        state_path, tensors_path = (origin/result[key]["path"] for key in ("state", "tangents"))
        state, tensors = npz(state_path), npz(tensors_path)
        for key, path, arrays in (("state", state_path, state), ("tangents", tensors_path, tensors)):
            bind(path, result[key]["sha256"])
            bind(path, receipt[key+"_sha256"])
            verify_fields(arrays, result[key]["fields"])
        same_arrays(state, npz(repo/row["state_file"]), "Original versus candidate split state")
        check(result["state_sha256"] == state_hash(state)
              and result["state_representation"] == "split_displacement_v1"
              and np.all(state["lift"][model["fixed_dofs"]] == -state["fluctuation"][model["fixed_dofs"]]),
              "Split state identity/actual fixed compatibility differs")
        ne, ndof = row["elements"], row["dofs"]
        edofs = (2*model["connectivity"][..., None]+np.arange(2)).reshape(ne, 8)
        check(np.array_equal(edofs, model["edofs"]), "Independent native local DOF mapping differs")
        check(set(tensors) == {component+"_tangent" for component in COMPONENTS}, "Three local tangent fields differ")
        rows, cols = np.repeat(edofs, 8, axis=1).ravel(), np.tile(edofs, (1, 8)).ravel()
        matrices, statistics = {}, {}
        for component in COMPONENTS:
            values = tensors[component+"_tangent"]
            check(values.dtype == np.dtype("float64") and values.shape == (ne, 8, 8)
                  and np.isfinite(values).all(), "Invalid full local tangent: "+component)
            declaration = result["matrices"][component]
            path = origin/declaration["path"]
            bind(path, declaration["sha256"])
            bind(path, receipt["matrix_sha256"][component])
            matrix = sparse.load_npz(path)
            verify_fields({name: getattr(matrix, name) for name in ("data", "indices", "indptr")}, declaration["fields"])
            check(declaration["format"] == matrix.format == "csc" and matrix.shape == (ndof, ndof)
                  and matrix.has_canonical_format and np.isfinite(matrix.data).all(), "Invalid full CSC: "+component)
            independent = sparse.coo_matrix((values.ravel(), (rows, cols)), shape=(ndof, ndof)).tocsc()
            independent.sum_duplicates()
            same_arrays({name: getattr(matrix, name) for name in ("data", "indices", "indptr")},
                {name: getattr(independent, name) for name in ("data", "indices", "indptr")}, "Independent full CSC "+component)
            magnitude = float(np.linalg.norm(matrix.data))
            statistics[component] = dict(shape=list(matrix.shape), nnz=int(matrix.nnz),
                relative_asymmetry=float(np.linalg.norm((matrix-matrix.T).data))/magnitude if magnitude else 0.)
            matrices[component] = matrix
        check(statistics == result["matrix_statistics"], "Stored full matrix statistics differ")
        matrix_decomposition = float(np.linalg.norm((matrices["total"]-matrices["material"]-matrices["regularization"]).data))
        copies = output/"inputs"
        for path in origin.rglob("*"):
            if path.is_file():
                target = copies/path.relative_to(origin)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                check(sha(target) == sha(path), "Candidate snapshot changed")
        check([item["name"] for item in row["directions"]] == ["vx_stripe", "vy_checker"], "Direction scope differs")
        from hf4_split_precision_reference import DecimalSplitQ1Reference
        checkpoint()
        lifecycle("running")
        ny, nx = metadata["grid"]["shape_yx"]
        i, j = np.meshgrid(np.arange(nx+1), np.arange(ny+1))
        for item in row["directions"]:
            checkpoint()
            name, path = item["name"], repo/item["file"]
            bind(path, item["sha256"])
            direction = npz(path)[name]
            expected = np.zeros(ndof)
            expected[0 if name == "vx_stripe" else 1::2] = ((i if name == "vx_stripe" else i+j).ravel() % 2)
            expected[model["fixed_dofs"]] = 0.
            same_arrays(dict(direction=direction), dict(direction=expected), "Independent direction manufacture")
            check(hashlib.sha256(direction.tobytes()).hexdigest() == item["array_sha256"], "Raw direction hash differs")
            directory = output/name
            directory.mkdir()
            groups, membership, left, right, local_v = group_inputs(model, state, direction, edofs, checkpoint)
            counts = {group["raw_key_sha256"]: len(group["members"]) for group in groups}
            check(len(groups) == item["exact_input_classes"] and counts == item["class_member_counts"],
                  "Full raw direction class hashes/member counts differ")
            representatives = np.asarray([group["representative"] for group in groups], dtype=np.int64)
            np.savez_compressed(directory/"membership.npz", element_class=membership, edofs=edofs,
                member_offsets=np.cumsum([0]+[len(group["members"]) for group in groups], dtype=np.int64),
                member_elements=np.concatenate([group["members"] for group in groups]), representatives=representatives,
                lift=left[representatives], fluctuation=right[representatives], direction=local_v[representatives],
                lam=model["lam"][representatives], mu=model["mu"][representatives],
                **{key: model[key] for key in ("kr", "grad", "hessian", "weights")})
            references, reference_files = {80: [], 120: []}, []
            for group_id, group in enumerate(groups):
                element = group["representative"]
                fixture = {key: model[key] for key in ("kr", "grad", "hessian", "weights")}
                fixture.update(lam=model["lam"][element:element+1], mu=model["mu"][element:element+1],
                    connectivity=np.asarray([[0, 1, 2, 3]], dtype=np.int64), F0=np.zeros(8), fixed_dofs=np.empty(0, dtype=np.int64))
                for precision in (80, 120):
                    checkpoint()
                    started_calls += 1
                    lifecycle("running")
                    hp = DecimalSplitQ1Reference(fixture, precision=precision).evaluate(left[element], right[element],
                        tangent_direction=local_v[element], derivative=True)
                    completed_calls += 1
                    references[precision].append(hp)
                    hp_path = directory/f"class_{group_id:03d}_hp{precision}.json.gz"
                    write_gzip(hp_path, dict(group=group, precision=precision, values={key: value for key, value in hp.items()
                        if key.endswith("_decimal") or key == "minimum_J"}))
                    reference_files.append(file_record(hp_path))
                    checkpoint()
                    lifecycle("running")
            global_hp = {}
            with localcontext() as context:
                context.prec = 3000
                context.traps[Inexact] = True
                for precision in (80, 120):
                    action = [[Decimal(0)]*ndof for _ in COMPONENTS]
                    for element, dofs in enumerate(edofs):
                        if element % 256 == 0:
                            checkpoint()
                        hp = references[precision][membership[element]]
                        for column, key in enumerate(HP_KEYS):
                            for local, dof in enumerate(dofs):
                                action[column][dof] += hp[key][local]
                    global_hp[precision] = dict(zip(COMPONENTS, action, strict=True))
            global_path = directory/"global_hp80_hp120.json.gz"
            write_gzip(global_path, global_hp)
            checkpoint()
            actions, exact_gates, worst, global_checks, csc_checks, differences = {}, {}, [], [], [], []
            with localcontext() as context:
                context.prec = 120
                for column, (component, key, limit) in enumerate(zip(COMPONENTS, HP_KEYS, LIMITS, strict=True)):
                    local = np.einsum("eij,ej->ei", tensors[component+"_tangent"], local_v)
                    assembled = np.zeros(ndof)
                    np.add.at(assembled, edofs.ravel(), local.ravel())
                    csc_action = matrices[component] @ direction
                    actions.update({"element_"+component+"_action": local, "global_"+component+"_action": assembled,
                                    "csc_"+component+"_action": csc_action})
                    entries = []
                    for element in range(ne):
                        if element % 128 == 0:
                            checkpoint()
                        group_id = membership[element]
                        values, _ = compare(local[element], references[80][group_id][key], references[120][group_id][key])
                        values.update(element=element, group=int(group_id))
                        entries.append(values)
                        gate(values, limit, f"local {name}/{component}/{element}")
                    exact_gates[component] = entries
                    worst.append(dict(component=component, **max(entries, key=lambda entry: entry["normalized_error"])))
                    for candidate, destination, label in ((assembled, global_checks, "global"), (csc_action, csc_checks, "CSC")):
                        values, difference = compare(candidate, global_hp[80][component], global_hp[120][component])
                        values.update(component=component)
                        gate(values, limit, f"{label} {name}/{component}")
                        destination.append(values)
                        difference_path = directory/f"{label.lower()}_{component}_difference.json.gz"
                        write_gzip(difference_path, difference)
                        differences.append(file_record(difference_path))
                hp_decomposition = norm([a-b-c for a, b, c in zip(*(global_hp[80][key] for key in COMPONENTS), strict=True)])
            np.savez_compressed(directory/"actions.npz", direction=direction, **actions)
            write_gzip(directory/"element_gates.json.gz", exact_gates)
            record = dict(name=name, status="pass", exact_input_classes=len(groups), elements_compared=ne,
                local_action_entries_compared=ne*8*3, global_DOF_entries_compared=ndof*3,
                CSC_DOF_entries_compared=ndof*3, HP_calls=2*len(groups), local_worst=worst,
                global_checks=global_checks, csc_checks=csc_checks,
                class_membership=file_record(directory/"membership.npz"), class_references=reference_files,
                global_references=file_record(global_path), exact_element_gates=file_record(directory/"element_gates.json.gz"),
                actions=file_record(directory/"actions.npz"), differences=differences,
                hp_decomposition_norm_N_per_mm=str(hp_decomposition),
                action_decomposition_norm_N_per_mm=float(np.linalg.norm(actions["global_total_action"]-
                    actions["global_material_action"]-actions["global_regularization_action"])))
            write(directory/"summary.json", record)
            checkpoint()
            records.append(record)
            lifecycle("running")
        check(started_calls == completed_calls == 2*sum(item["exact_input_classes"] for item in row["directions"]),
              "Fresh reference calls do not cover both full direction partitions")
        for path, expected in bindings.items():
            check(sha(path) == expected, "Input/source changed during audit: "+str(path))
        checkpoint()
        summary = dict(schema_version="native-tangent-independent-audit-1.0", status="pass", alias=row["alias"],
            state_name=row["state_name"], elements=ne, dofs=ndof, directions=records, matrix_statistics=statistics,
            full_local_matrix_entries_assembly_checked=ne*8*8*3, full_element_and_global_direction_coverage=True,
            HP_matrix_columns_exhaustively_checked=False, matrix_decomposition_norm_N_per_mm=matrix_decomposition,
            matrix_semantics="K_ij = d f_i / d w_j; full DOFs; fixed lift; unsymmetrized; N/mm",
            input_bindings={path.relative_to(repo).as_posix(): pin for path, pin in bindings.items()},
            source_bindings=sources, HP_calls_started=started_calls, HP_calls_completed=completed_calls,
            candidate_force_calls=0, candidate_tangent_calls=0, solver_calls=0, checks_completed=checks,
            original_limits=dict(zip(COMPONENTS, map(str, LIMITS), strict=True)), reference_limit=str(HP_LIMIT),
            denominator_floor_N_per_mm=str(FLOOR), global_scatter_precision=3000, global_scatter_inexact_trap=True,
            equilibrium_qualified=False, task_target_executed=False, fine_model_checked=False,
            elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak,
            time_limit_seconds=args.time_limit, sampled_RSS_limit_bytes=RSS_LIMIT)
        write(output/"summary.json", summary)
        checkpoint()
        lifecycle("pass")
        checkpoint()
        print("pass: two directions, "+str(completed_calls)+" HP calls", flush=True)
        checkpoint()
    except Exception as error:
        lifecycle("not_pass", repr(error))
        write(output/"summary.json", dict(schema_version="native-tangent-independent-audit-1.0", status="not_pass",
            error=repr(error), directions=records, HP_calls_started=started_calls, HP_calls_completed=completed_calls,
            checks_completed=checks, elapsed_seconds=perf_counter()-STARTED, sampled_peak_RSS_bytes=peak))
        raise


if __name__ == "__main__":
    main()
