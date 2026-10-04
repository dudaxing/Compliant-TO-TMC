"""Offline Decimal certification of a repaired HF-2 path and historical audits.

Never solves or changes a path. The repaired Python path is judged separately
from the old MATLAB/Python states. Historical failure flags are never erased.
The caller supplies the frozen precision spec, primitive fixture, and a separate
seven-response comparison. Run under the shared 600-second budget monitor.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
from pathlib import Path
from time import perf_counter

import numpy as np


PRIMITIVES = ("grad", "hessian", "weights", "points", "lam", "mu", "kr", "connectivity",
              "F0", "fixed_dofs", "coordinates", "solid", "hx", "hy", "thickness", "loaded_nodes")
RESPONSE_METRICS = ("U", "loaded_displacements", "support_reaction",
                    "solid_material_energy", "medium_material_energy", "J_field")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_npz(path):
    with np.load(path, allow_pickle=False) as archive:
        result = {key: archive[key] for key in archive.files}
    if any(a.dtype.kind not in "biuf" or not np.all(np.isfinite(a)) for a in result.values()):
        raise ValueError(f"{path}: all arrays must be finite, real ordinary data")
    return result


def decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def promote(value):
    return Decimal.from_float(float(value))


def dnorm(values):
    return sum((x*x for x in values), Decimal(0)).sqrt()


def force_error(actual, reference, scale, free):
    """Exact float promotion and Decimal subtraction; denominator is load norm.

    In particular, this is not max(norm(internal_reference), load norm), which
    would hide a free-equilibrium error behind large cancelling internal forces.
    """
    with localcontext() as context:
        context.prec = 100
        differences = [promote(a)-b for a, b in zip(np.asarray(actual).ravel(), reference)]
        if len(differences) != len(reference) or len(differences) != np.asarray(actual).size:
            raise ValueError("force vector lengths differ")
        full = dnorm(differences)/scale
        selected = dnorm([differences[i] for i in free])/scale
        return dict(full_relative_error_decimal=str(full), free_relative_error_decimal=str(selected),
                    full_relative_error=float(full), free_relative_error=float(selected))


def precision_error(lower, higher, scale, free):
    with localcontext() as context:
        context.prec = 100
        if len(lower) != len(higher):
            raise ValueError("precision reference vector lengths differ")
        differences = [a-b for a, b in zip(lower, higher)]
        full, selected = dnorm(differences)/scale, dnorm([differences[i] for i in free])/scale
        return dict(full_relative_error_decimal=str(full), free_relative_error_decimal=str(selected),
                    full_relative_error=float(full), free_relative_error=float(selected))


def relative_error(actual, reference, floor):
    a, b = np.asarray(actual), np.asarray(reference)
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch {a.shape} versus {b.shape}")
    absolute = float(np.linalg.norm((a-b).ravel()))
    denominator = max(float(np.linalg.norm(b.ravel())), float(floor))
    return dict(absolute_error=absolute, denominator=denominator, relative_error=absolute/denominator)


def plain(value):
    if isinstance(value, (np.generic,)):
        return value.item()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(plain(value), indent=2, allow_nan=False)+"\n", encoding="utf-8")
    temporary.replace(path)


def load_helper():
    path = Path(__file__).with_name("hf2_precision_reference.py")
    spec = importlib.util.spec_from_file_location("hf2_precision_reference_for_path", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DecimalQ1Reference, path


def load_side(directory, *, matlab=False):
    directory = Path(directory)
    path = read_npz(directory/"cshape_path.npz")
    metadata = read_json(directory/("cshape_path.json" if matlab else "result.json"))
    if matlab:
        normal = dict(levels=path["targets"].ravel(), U=path["U"], J=path["J"],
                      reaction=path["reaction"], solid_energy=path["material_energy_solid"].ravel(),
                      medium_energy=path["material_energy_medium"].ravel(),
                      stored_residual=path["relative_free_residual"].ravel(),
                      internal=path.get("internal_force"), original=np.ones(len(path["targets"]), dtype=bool))
    else:
        normal = dict(levels=path["lambda"].ravel(), U=path["U"], J=path["J"],
                      reaction=path["support_reaction"], solid_energy=path["solid_material_energy"].ravel(),
                      medium_energy=path["medium_material_energy"].ravel(),
                      stored_residual=path["relative_residual"].ravel(),
                      internal=path.get("internal_force"), original=path["original_target"].astype(bool).ravel())
    count = len(normal["levels"])
    if any(len(normal[key]) != count for key in ("U", "J", "reaction", "solid_energy", "medium_energy", "stored_residual", "original")):
        raise ValueError("path arrays disagree on accepted-state count")
    if np.any(np.diff(normal["levels"]) <= 0):
        raise ValueError("accepted state multipliers must increase strictly")
    if normal["internal"] is not None and len(normal["internal"]) != count:
        raise ValueError("internal-force path count mismatch")
    return normal, metadata


def validate(args):
    begin = perf_counter()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    (output/"precision_spec_used.json").write_bytes(Path(args.spec).read_bytes())
    spec = read_json(args.spec)
    limits = spec["path_validation"]
    required = dict(high_precision_digits=50, crosscheck_precision_digits=80,
                    crosscheck_indices=[0, 49, 99], crosscheck_force_tolerance="1e-30",
                    external_residual_tolerance=1e-8, evaluation_error_tolerance=1e-9,
                    expected_original_targets=100)
    for key, value in required.items():
        if key not in limits or (decimal(limits[key]) != decimal(value) if key.endswith("tolerance") else limits[key] != value):
            raise ValueError(f"frozen path_validation.{key} differs from this validator's authorized specification")
    tolerances = spec["original_cshape_tolerances"]
    old_spec = spec["original_validation_spec"]
    if old_spec["cshape"] != tolerances:
        raise ValueError("original_cshape_tolerances differs from embedded original spec")
    fixture = read_npz(args.fixture)
    model = read_npz(Path(args.new_python)/"model.npz")
    setup_checks = []
    def check(name, passed, **detail):
        setup_checks.append(dict(check=name, status="pass" if bool(passed) else "fail", **detail))
    for key in PRIMITIVES:
        if key not in fixture or key not in model:
            raise ValueError(f"missing actual primitive array: {key}")
        a, b = fixture[key], model[key]
        same = a.shape == b.shape and a.dtype == b.dtype and a.tobytes(order="C") == b.tobytes(order="C")
        check("new_model_bitwise_"+key, same)
    if not all(row["status"] == "pass" for row in setup_checks):
        write_json(output/"setup_checks.json", setup_checks)
        raise ValueError("new path primitives do not match the frozen fixture bitwise")
    targets = fixture["targets"].ravel()
    if targets.shape != (100,) or not np.array_equal(model["targets"], targets):
        raise ValueError("new path must preserve the fixture's 100 exact original targets")
    check("target_final_multiplier", targets[-1] == 1.)
    sources = [("new_python", Path(args.new_python), False),
               ("old_python", Path(args.old_python), False), ("matlab", Path(args.matlab), True)]
    side_data = {}
    input_paths = [Path(args.fixture), Path(args.spec), Path(args.comparison),
                   Path(args.new_python)/"model.npz", Path(__file__)]
    for name, directory, is_matlab in sources:
        path, metadata = load_side(directory, matlab=is_matlab)
        side_data[name] = (path, metadata)
        input_paths += [directory/"cshape_path.npz", directory/("cshape_path.json" if is_matlab else "result.json")]
        original_levels = path["levels"][path["original"]]
        check(name+"_all_original_targets_exact", np.array_equal(original_levels, targets))
    new_path, new_meta = side_data["new_python"]
    if new_path["internal"] is None:
        raise ValueError("repaired path must archive production internal_force at each accepted state")
    check("new_python_reported_complete", new_meta["status"] == "success" and
          new_meta["target_reached"] is True and new_meta["original_targets_reached"] == 100)
    check("new_python_internal_tolerance", new_meta["benchmark_config"]["solver"]["tolerance"] == 1e-9)
    check("new_python_kernel_version", new_meta["benchmark_config"]["kernel_version"] == spec["kernel_version"])
    check("new_python_solver_profile", new_meta["benchmark_config"]["solver_profile"] == spec["solver_profile"])
    comparison = read_json(args.comparison)
    response_rows = comparison["per_target_errors"]
    response_only_pass = len(response_rows) == 100 and all(
        all(row.get(key+"_pass") is True for key in RESPONSE_METRICS) and row.get("min_J_pass") is True
        for row in response_rows)
    check("response_comparison_exact_targets", np.array_equal(
        np.array([row["load_multiplier"] for row in response_rows]), targets))
    check("response_comparison_new_path_hash", comparison["inputs"]["python_path_sha256"] == sha256(Path(args.new_python)/"cshape_path.npz"))
    check("response_comparison_matlab_path_hash", comparison["inputs"]["matlab_path_sha256"] == sha256(Path(args.matlab)/"cshape_path.npz"))
    check("seven_response_metrics_all_targets", response_only_pass)
    # Historical statuses are observations. Their strict failures do not become
    # a veto against the repaired version's independent certification.
    Reference, helper_path = load_helper()
    input_paths.append(helper_path)
    reference = Reference(fixture, precision=limits["high_precision_digits"])
    higher_reference = Reference(fixture, precision=limits["crosscheck_precision_digits"])
    fixed, free = reference.fixed, reference.free
    solid = fixture["solid"].astype(bool).ravel()
    ne, ndof = reference.ne, reference.ndof
    E = old_spec["material"]["E"]
    hx, hy, thickness = (float(fixture[key]) for key in ("hx", "hy", "thickness"))
    Lx = tolerances["domain"][0]
    all_rows, precision_rows, exceptions, audits = [], [], [], {}
    completed = 0
    state_log = (output/"state_progress.jsonl").open("w", encoding="utf-8")
    def progress(side, source_index):
        state_log.flush()
        write_json(output/"progress.json", dict(status="running", completed_states=completed,
                    last_side=side, last_source_index=source_index, wall_seconds=perf_counter()-begin))
        print(f"HP validation: {completed} states processed; {side}[{source_index}]; {perf_counter()-begin:.2f} s", flush=True)
    try:
        for side, directory, _ in sources:
            path, metadata = side_data[side]
            selected = np.arange(len(path["levels"])) if side == "new_python" else np.flatnonzero(path["original"])
            arrays = {key: [] for key in ("source_index", "load_multiplier", "original_target", "original_target_index",
                                          "internal", "residual", "J", "material_energy", "reaction")}
            side_rows = []
            chunk_start = 0
            for source_index in selected:
                if perf_counter()-begin > 590:
                    raise TimeoutError("offline validation nearing its frozen 600-second process limit")
                source_index = int(source_index)
                level = float(path["levels"][source_index])
                original_matches = np.flatnonzero(targets == level)
                original_index = int(original_matches[0]) if len(original_matches) == 1 and path["original"][source_index] else -1
                row = dict(side=side, source_index=source_index, load_multiplier=level,
                           original_target=bool(path["original"][source_index]), original_target_index=original_index,
                           precision_digits=limits["high_precision_digits"], production_internal_available=path["internal"] is not None,
                           stored_relative_residual=float(path["stored_residual"][source_index]))
                state_started = perf_counter()
                try:
                    u = path["U"][source_index]
                    if u.shape != (ndof,) or path["J"][source_index].shape != (ne,9):
                        raise ValueError("path state shape differs from fixture")
                    hp = reference.evaluate(u, level)
                    sf = hp["force_scale_decimal"]
                    external_tolerance = decimal(limits["external_residual_tolerance"])
                    relative_hp = Decimal(hp["relative_residual"])
                    row.update(high_precision_relative_residual=hp["relative_residual"],
                               high_precision_minimum_J=hp["minimum_J"], force_scale_decimal=str(sf),
                               external_residual_tolerance_decimal=str(external_tolerance),
                               equilibrium_pass=relative_hp <= external_tolerance,
                               positive_J_pass=Decimal(hp["minimum_J"]) > 0)
                    if path["internal"] is not None:
                        error = force_error(path["internal"][source_index], hp["internal_decimal"], sf, free)
                        row.update({"evaluation_"+key: value for key, value in error.items()})
                        row["evaluation_budget_pass"] = max(Decimal(error["full_relative_error_decimal"]),
                                                              Decimal(error["free_relative_error_decimal"])) <= decimal(limits["evaluation_error_tolerance"])
                        archived_residual = path["internal"][source_index]-level*fixture["F0"]
                        row["archived_internal_relative_residual"] = float(np.linalg.norm(archived_residual[free]))/float(sf)
                    else:
                        row["evaluation_budget_pass"] = None
                    if side == "new_python":
                        row["internal_stopping_pass"] = max(row["stored_relative_residual"], row["archived_internal_relative_residual"]) <= spec["internal_newton_tolerance"]
                    row["fixed_displacement_max"] = float(np.max(np.abs(u[fixed]), initial=0.))
                    row["fixed_displacement_pass"] = row["fixed_displacement_max"] <= 1e-12*Lx
                    with localcontext() as context:
                        context.prec = 100
                        reaction_decimal = [Decimal(0)]*ndof
                        for index in fixed:
                            reaction_decimal[index] = hp["residual_decimal"][index]
                        balance = [sum((reaction_decimal[i]+hp["external_decimal"][i] for i in range(c, ndof, 2)), Decimal(0)) for c in (0,1)]
                        balance_scale = max(sf, Decimal(3)*promote(level))
                        normalized_balance = dnorm(balance)/balance_scale
                        stored_reaction_decimal = [promote(x) for x in path["reaction"][source_index]]
                        stored_balance = [sum((stored_reaction_decimal[i]+hp["external_decimal"][i] for i in range(c, ndof, 2)), Decimal(0)) for c in (0,1)]
                        normalized_stored_balance = dnorm(stored_balance)/balance_scale
                        row.update(high_precision_balance_absolute_decimal=str(dnorm(balance)),
                                   high_precision_balance_relative_decimal=str(normalized_balance),
                                   stored_reaction_balance_relative_decimal=str(normalized_stored_balance),
                                   balance_pass=max(normalized_balance, normalized_stored_balance) <= decimal(tolerances["global_force_balance_tolerance"]))
                        e_solid = sum((e for e, is_solid in zip(hp["material_energy_decimal"], solid) if is_solid), Decimal(0))
                        e_medium = sum((e for e, is_solid in zip(hp["material_energy_decimal"], solid) if not is_solid), Decimal(0))
                    hp_reaction = np.array(reaction_decimal, dtype=float)
                    for name, actual, expected, floor, tolerance in (
                        ("J", path["J"][source_index], hp["J"], 1e-8*np.sqrt(9*ne), tolerances["J_field_relative_tolerance"]),
                        ("reaction", path["reaction"][source_index][fixed], hp_reaction[fixed], 1e-8*3*level, tolerances["reaction_relative_tolerance"]),
                        ("solid_energy", np.asarray(path["solid_energy"][source_index]), np.asarray(float(e_solid)), 1e-8*E*thickness*solid.sum()*hx*hy, tolerances["region_material_energy_relative_tolerance"]),
                        ("medium_energy", np.asarray(path["medium_energy"][source_index]), np.asarray(float(e_medium)), 1e-8*E*1e-6*thickness*(~solid).sum()*hx*hy, tolerances["region_material_energy_relative_tolerance"])):
                        error = relative_error(actual, expected, floor)
                        row.update({name+"_"+key: value for key, value in error.items()})
                        row[name+"_pass"] = error["relative_error"] <= tolerance
                    row["minimum_J_absolute_error"] = abs(float(path["J"][source_index].min())-float(hp["minimum_J"]))
                    row["minimum_J_pass"] = row["minimum_J_absolute_error"] <= tolerances["min_J_absolute_tolerance"]
                    row["free_support_reaction_zero_pass"] = bool(np.all(path["reaction"][source_index][free] == 0.))
                    if side == "new_python" and original_index in limits["crosscheck_indices"]:
                        hp80 = higher_reference.evaluate(u, level)
                        error = precision_error(hp["internal_decimal"], hp80["internal_decimal"], hp80["force_scale_decimal"], free)
                        precision_pass = max(Decimal(error["full_relative_error_decimal"]), Decimal(error["free_relative_error_decimal"])) <= decimal(limits["crosscheck_force_tolerance"])
                        precision_rows.append(dict(side=side, source_index=source_index, original_target_index=original_index,
                                                   load_multiplier=level, lower_digits=50, higher_digits=80,
                                                   tolerance_decimal=str(limits["crosscheck_force_tolerance"]), status="pass" if precision_pass else "fail", **error))
                        np.savez_compressed(output/f"precision_crosscheck_target_{original_index+1:03d}.npz",
                            source_index=np.array(source_index), load_multiplier=np.array(level),
                            internal_50_decimal=np.array([str(x) for x in hp["internal_decimal"]]),
                            internal_80_decimal=np.array([str(x) for x in hp80["internal_decimal"]]),
                            external_80_decimal=np.array([str(x) for x in hp80["external_decimal"]]),
                            free_dofs=free)
                        row["reference_precision_pass"] = precision_pass
                    base_gates = [row[k] for k in ("equilibrium_pass", "positive_J_pass", "fixed_displacement_pass", "balance_pass", "J_pass", "reaction_pass", "solid_energy_pass", "medium_energy_pass", "minimum_J_pass", "free_support_reaction_zero_pass")]
                    row["independent_state_status"] = "pass" if all(base_gates) else "fail"
                    row["new_version_state_status"] = ("pass" if all(base_gates) and row["evaluation_budget_pass"] is True and row["internal_stopping_pass"] and row.get("reference_precision_pass", True) else "fail") if side == "new_python" else "historical_audit_only"
                    arrays["source_index"].append(source_index)
                    arrays["load_multiplier"].append(level)
                    arrays["original_target"].append(row["original_target"])
                    arrays["original_target_index"].append(original_index)
                    for key in ("internal", "residual", "J", "material_energy"):
                        arrays[key].append(hp[key])
                    arrays["reaction"].append(hp_reaction)
                except Exception as exc:
                    row.update(independent_state_status="fail", new_version_state_status="fail" if side == "new_python" else "historical_audit_only", exception_type=type(exc).__name__, exception=str(exc))
                    exceptions.append(dict(side=side, source_index=source_index, load_multiplier=level, exception_type=type(exc).__name__, message=str(exc)))
                row["wall_seconds"] = perf_counter()-state_started
                all_rows.append(row)
                side_rows.append(row)
                state_log.write(json.dumps(plain(row), allow_nan=False)+"\n")
                completed += 1
                if completed % 10 == 0:
                    count = len(arrays["source_index"])
                    if count > chunk_start:
                        np.savez_compressed(output/f"{side}_checkpoint_{count:04d}.npz",
                            **{key:np.asarray(value[chunk_start:]) for key,value in arrays.items()})
                        chunk_start = count
                    progress(side, source_index)
            np.savez_compressed(output/(side+"_high_precision.npz"), **{key:np.asarray(value) for key,value in arrays.items()})
            audits[side] = dict(original_path_status=metadata["status"], selected_states=len(selected), evaluated_states=len(side_rows),
                                original_targets_evaluated=sum(row["original_target"] for row in side_rows),
                                independent_equilibrium_failures=[{k:row[k] for k in ("source_index", "load_multiplier", "high_precision_relative_residual") if k in row}
                                    for row in side_rows if row.get("equilibrium_pass") is not True],
                                independent_failed_states=[row["source_index"] for row in side_rows if row["independent_state_status"] != "pass"],
                                historical_state_status_preserved=True)
            write_json(output/(side+"_audit.json"), audits[side])
            progress(side, int(selected[-1]) if len(selected) else -1)
    finally:
        state_log.flush()
        state_log.close()
    columns = list(dict.fromkeys(key for row in all_rows for key in row))
    with (output/"per_state_validation.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(all_rows)
    new_rows = [row for row in all_rows if row["side"] == "new_python"]
    setup_pass = all(row["status"] == "pass" for row in setup_checks)
    references_pass = len(precision_rows) == 3 and all(row["status"] == "pass" for row in precision_rows)
    new_pass = bool(new_rows) and all(row["new_version_state_status"] == "pass" for row in new_rows)
    closed = setup_pass and references_pass and new_pass
    summary = dict(schema_version="hf2-repaired-path-validation-1.0",
                   repaired_python_numerical_closure_status="pass" if closed else "not_pass",
                   new_python_independent_state_status="pass" if new_pass else "fail_or_incomplete",
                   old_hf2_run_status="partially_complete_historical_record_preserved",
                   original_comparison_full_benchmark_status=comparison["full_benchmark_status"],
                   response_agreement_status="pass" if response_only_pass else "fail",
                   response_gate_scope="Only seven original response metrics; historical MATLAB independent equilibrium does not veto the repaired Python version",
                   full_repair_stage_scope="This file certifies path numerics only; root also checks local/derivative regression and detached installation before overall repair closure",
                   hf3_authorization="not_granted_by_this_validation", units_mode="source_numeric",
                   total_evaluated_states=len(all_rows), new_python_accepted_states=len(new_rows),
                   successful_high_precision_evaluations=sum("high_precision_relative_residual" in row for row in all_rows),
                   historical_reference_evaluation_exceptions=[item for item in exceptions if item["side"] != "new_python"],
                   new_python_original_targets=sum(row["original_target"] for row in new_rows),
                   setup_checks=setup_checks, precision_crosschecks=precision_rows, historical_and_new_audits=audits,
                   new_python_failures=[row for row in new_rows if row["new_version_state_status"] != "pass"],
                   exceptions=exceptions, criteria=limits,
                   original_validation_spec_sha256=spec["original_validation_spec_sha256"],
                   metadata_versions={name:{"status":meta["status"], "source_code_sha256":meta.get("source_code_sha256"),
                                           "benchmark_config":meta.get("benchmark_config"), "kernel_version":meta.get("kernel_version"),
                                           "profile":meta.get("profile")} for name, (_,meta) in side_data.items()},
                   evidence=[dict(path=str(path.resolve()), sha256=sha256(path)) for path in input_paths],
                   wall_seconds=perf_counter()-begin)
    write_json(output/"summary.json", summary)
    write_json(output/"progress.json", dict(status="complete", completed_states=completed, wall_seconds=summary["wall_seconds"]))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("fixture", "spec", "new-python", "old-python", "matlab", "comparison", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must name a new directory; existing evidence will not be modified")
    begin = perf_counter()
    try:
        result = validate(args)
    except Exception as exc:
        args.output.mkdir(parents=True, exist_ok=True)
        failure = dict(schema_version="hf2-repaired-path-validation-1.0",
                       repaired_python_numerical_closure_status="not_pass", validation_status="incomplete",
                       exception_type=type(exc).__name__, message=str(exc), wall_seconds=perf_counter()-begin,
                       note="Any completed state_progress.jsonl and per-side arrays remain; no path was solved or changed")
        write_json(args.output/"validation_failure.json", failure)
        print(json.dumps(failure, indent=2), flush=True)
        return 1
    print(json.dumps({key:result[key] for key in ("repaired_python_numerical_closure_status", "response_agreement_status",
                                                "total_evaluated_states", "new_python_original_targets", "wall_seconds")}, indent=2), flush=True)
    return 0 if result["repaired_python_numerical_closure_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
