"""Stage-0 fixed-direction update-retention intervention, without a FE solve.

Read the published HF4 failed candidate and its already computed correction.
For alpha=1 and 1/2 compare D(round64(u+alpha*delta)) with the ideal state
D(u)+D(alpha)*D(delta), using the existing independent Decimal Q1 reference
at 50 and 80 digits. No production module is imported, no direction is solved
again, and no state is reported as an accepted production state.

The generic reference's relative_residual is deliberately discarded: F0=0
here, and its fallback unit scale is not the frozen HF4 force scale. Each
state uses SF=max(norm(fint_free),norm(fint_fixed),1e-8*E*t*max(abs(d),1e-6)).
Armijo uses the BASE state's SF at the same precision for both merit values.
All original inputs are checked against HF4_CONTENT_MANIFEST before use;
input and implementation hashes are checked again before final release.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from time import perf_counter

import numpy as np


RELATIVE_INPUTS = (
    "hf4_results/fixed_update_probe_001/fixed_correction.npz",
    "hf4_results/fixed_update_probe_001/summary.json",
    "hf4_results/fixed_update_probe_001/trial_01.npz",
    "hf4_results/fixed_update_probe_001/trial_02.npz",
    "hf4_results/fixed_state_probe_001/summary.json",
    "hf4_results/fixed_state_probe_001/last_candidate.npz",
    "hf4_results/fixed_state_probe_001/candidate_004.npz",
    "hf4_results/fixed_state_probe_001/observed_result.json",
    "hf4_results/g1_m1_001/model.npz",
    "hf4_results/g1_m1_001/metadata.json",
    "hf_repo/configs/hf4/validation_spec.json",
    "hf_repo/scripts/hf2_precision_reference.py",
)
ALPHAS = (1.0, 0.5)
PRECISIONS = (50, 80)
TARGET = 0.125
PRODUCTION_TARGET = Decimal("1e-9")
CROSS_TARGET = Decimal("1e-30")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, np.generic):
        return _plain(value.item())
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _write_json(path, value):
    temporary = path.with_name(path.name+".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(_plain(value), stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_npz(path, arrays):
    temporary = path.with_name(path.name+".tmp")
    try:
        with temporary.open("wb") as stream:
            np.savez_compressed(stream, **arrays)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _npz(path):
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name].copy() for name in archive.files}


def _array_record(array):
    contiguous = np.ascontiguousarray(array)
    return dict(shape=list(array.shape), dtype=array.dtype.str,
                content_sha256=hashlib.sha256(contiguous.tobytes(order="C")).hexdigest(),
                content_convention="C-order raw array bytes; shape and dtype bound separately")


def _same(left, right):
    return (left.shape == right.shape and left.dtype == right.dtype
            and left.tobytes(order="C") == right.tobytes(order="C"))


def _float_array(array, shape, name):
    if array.shape != shape or array.dtype != np.dtype("float64") or not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be a finite binary64 array of shape {shape}")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _d(value):
    return Decimal.from_float(float(value))


def _norm(values):
    return sum((value*value for value in values), Decimal(0)).sqrt()


def _dot(left, right):
    if len(left) != len(right):
        raise ValueError("dot product shape mismatch")
    return sum((a*b for a, b in zip(left, right)), Decimal(0))


def _finite_decimals(value):
    if isinstance(value, Decimal):
        return value.is_finite()
    if isinstance(value, (list, tuple)):
        return all(_finite_decimals(item) for item in value)
    return True


def _load_bound_inputs(root, output):
    manifest_path = root/"HF4_CONTENT_MANIFEST.json"
    manifest = _json(manifest_path)
    execution_path = root/"hf4_repair_results/execution_spec.json"
    execution = _json(execution_path)
    stage0 = execution["stage0"]
    _require(execution["schema_version"] == "hf4-repair-execution-1.0"
             and execution["status"] == "frozen_before_stage0"
             and tuple(stage0["alphas"]) == ALPHAS and tuple(stage0["digits"]) == PRECISIONS
             and Decimal(stage0["retained_residual_gate"]) == PRODUCTION_TARGET
             and Decimal(stage0["cross_precision_gate"]) == CROSS_TARGET
             and Decimal(stage0["constraint_gate"]) == Decimal("1e-10")
             and stage0["at_least_one_retained_gate_pass"] is True
             and stage0["all_input_domain_precision_checks_required"] is True,
             "new execution specification differs from the fixed stage-0 intervention")
    _require(manifest["schema_version"] == "hf4-content-manifest-1.0" and manifest["version"] == "0.4.0",
             "expected the published HF4 0.4.0 content manifest")
    entries = {item["path"]: item for item in manifest["files"]}
    _require(len(entries) == len(manifest["files"]), "duplicate manifest path")
    bound = {"HF4_CONTENT_MANIFEST.json": dict(sha256=_sha(manifest_path), bytes=manifest_path.stat().st_size)}
    bound["hf4_repair_results/execution_spec.json"] = dict(sha256=_sha(execution_path), bytes=execution_path.stat().st_size)
    for relative, expected_sha in execution["inputs"].items():
        path = root/relative
        _require(path.is_file() and _sha(path) == expected_sha, "execution input mismatch: "+relative)
        bound[relative] = dict(sha256=expected_sha, bytes=path.stat().st_size)
    for relative in RELATIVE_INPUTS:
        entry = entries[relative]
        path = root/relative
        _require(path.is_file() and path.stat().st_size == entry["bytes"] and _sha(path) == entry["sha256"],
                 "published input mismatch: "+relative)
        bound[relative] = dict(sha256=entry["sha256"], bytes=entry["bytes"])
    snapshots = output/"input_snapshot"
    for relative in bound:
        destination = snapshots/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root/relative).read_bytes())
        _require(_sha(destination) == bound[relative]["sha256"], "snapshot copy hash mismatch")
    model = _npz(root/"hf4_results/g1_m1_001/model.npz")
    correction = _npz(root/"hf4_results/fixed_update_probe_001/fixed_correction.npz")
    candidate = _npz(root/"hf4_results/fixed_state_probe_001/last_candidate.npz")
    last_iteration = _npz(root/"hf4_results/fixed_state_probe_001/candidate_004.npz")
    trials = [_npz(root/f"hf4_results/fixed_update_probe_001/trial_{i:02d}.npz") for i in (1, 2)]
    metadata = _json(root/"hf4_results/g1_m1_001/metadata.json")
    spec = _json(root/"hf_repo/configs/hf4/validation_spec.json")
    update_summary = _json(root/"hf4_results/fixed_update_probe_001/summary.json")
    state_summary = _json(root/"hf4_results/fixed_state_probe_001/summary.json")
    observed = _json(root/"hf4_results/fixed_state_probe_001/observed_result.json")
    spec_sha = bound["hf_repo/configs/hf4/validation_spec.json"]["sha256"]
    _require(spec_sha == execution["physics_spec_sha256"], "execution physics spec binding differs")
    _require(manifest["spec_sha256"] == metadata["spec_sha256"] == update_summary["spec_sha256"]
             == state_summary["spec_sha256"] == spec_sha, "inconsistent historical spec bindings")
    _require(metadata["spec"] == spec, "metadata carries a different scientific specification")
    _require(update_summary["input_sha256"] == bound["hf4_results/fixed_state_probe_001/last_candidate.npz"]["sha256"],
             "stored Newton correction is not bound to the original candidate")
    _require(state_summary["candidate_count"] == 5 and observed["status"] == "failed"
             and observed["target_reached"] is False and observed["target_displacement"] == TARGET,
             "candidate is not the first failed d=0.125 diagnostic target")
    _require(metadata["gamma_index"] == metadata["mesh_index"] == 1
             and metadata["task"]["gamma"] == spec["gammas"][1]
             and metadata["task"]["mesh_size_mm"] == spec["mesh_sizes_mm"][1]
             and spec["targets_mm"][1] == TARGET, "wrong frozen combination or target")
    _require(spec["solver"]["tolerance"] == 1e-9
             and Decimal(spec["numerical_criteria"]["precision_crosscheck_relative"]) == CROSS_TARGET
             and spec["precision_digits"] == 50 and spec["crosscheck_precision_digits"] == 80,
             "scientific gate differs from the published stage-0 prerequisites")
    ndof, ne = 1258, 576
    for name in ("u", "delta", "internal_force"):
        _float_array(correction[name], (ndof,), "correction."+name)
    _require(_same(correction["u"], candidate["u"]) and _same(correction["u"], last_iteration["u"]),
             "u does not exactly identify the saved failed candidate")
    shapes = {"coordinates": (629, 2), "grad": (9, 4, 2), "hessian": (4, 2, 2),
              "weights": (9,), "points": (9, 2), "lam": (ne,), "mu": (ne,),
              "kr": (), "hx": (), "hy": (), "thickness": (),
              "base": (ndof,), "direction": (ndof,), "gap_vector": (ndof,),
              "group_bottom_platen": (ndof,), "group_top_platen": (ndof,)}
    for name, shape in shapes.items():
        _float_array(model[name], shape, "model."+name)
    _require(model["connectivity"].shape == (ne, 4) and model["connectivity"].dtype.kind in "iu"
             and np.all((model["connectivity"] >= 0) & (model["connectivity"] < ndof//2)), "invalid connectivity")
    fixed = model["fixed_dofs"]
    _require(fixed.shape == (663,) and fixed.dtype.kind in "iu" and len(np.unique(fixed)) == len(fixed)
             and np.all((fixed >= 0) & (fixed < ndof)), "invalid fixed DOF identity")
    free = np.setdiff1d(np.arange(ndof), fixed)
    _require(len(free) == 595 and model["solid"].shape == (ne,) and model["solid"].dtype == bool,
             "unexpected free DOF or solid mask shape")
    _require(model["body_ids"].shape == (ne,) and np.array_equal(model["solid"], model["body_ids"] != 0),
             "body and solid labels disagree")
    for name in ("base", "direction", "group_bottom_platen", "group_top_platen"):
        _require(np.all(model[name][free] == 0), name+" is nonzero on free DOFs")
    _require(np.all(correction["delta"][fixed] == 0) and np.any(correction["delta"][free] != 0),
             "stored correction changes prescribed DOFs or is empty")
    lower = np.intersect1d(2*np.flatnonzero(model["coordinates"][:, 1] <= metadata["task"]["geometry"]["lower_height_mm"])+1, free)
    _require(_same(lower, correction["lower_free"]), "stored lower-free set differs from model geometry")
    _require(float(model["hx"]) == float(model["hy"]) == 0.0625
             and float(model["thickness"]) == metadata["task"]["geometry"]["thickness_mm"], "wrong mesh or thickness")
    with localcontext() as context:
        context.prec = 1500
        _require(all(_d(correction["u"][i]) == _d(model["base"][i])+_d(TARGET)*_d(model["direction"][i]) for i in fixed),
                 "original candidate violates exact prescribed values")
    rounded = {}
    product_records = {}
    for alpha, archived in zip(ALPHAS, trials):
        product = np.multiply(alpha, correction["delta"])
        trial = np.add(correction["u"], product)
        _require(_same(trial, archived["u"]), "round64 update does not reproduce its published trial")
        with localcontext() as context:
            context.prec = 1500
            exact_product = [_d(alpha)*_d(value) for value in correction["delta"]]
            exact_state = [_d(value)+increment for value, increment in zip(correction["u"], exact_product)]
            losses = [_d(value)-exact for value, exact in zip(trial, exact_state)]
            _require(all(_d(value) == exact for value, exact in zip(product, exact_product)),
                     "alpha*delta rounded before addition; intervention would mix multiplication and addition changes")
            product_records[str(alpha)] = dict(alpha_binary64_hex=alpha.hex(),
                exact_update_product_decimal=exact_product, exact_retained_u_decimal=exact_state,
                rounded_minus_retained_decimal=losses,
                max_absolute_rounding_loss_mm=max(abs(value) for value in losses),
                product_binary64_matches_exact=True,
                changed_free=int(np.count_nonzero(trial[free] != correction["u"][free])))
        rounded[alpha] = trial
        _write_npz(output/f"rounded_alpha_{'1' if alpha == 1 else 'half'}.npz",
                   dict(u=trial, alpha_delta_binary64=product, alpha=np.array(alpha)))
    _write_json(output/"exact_update_products.json", product_records)
    arrays = {"model": {key: _array_record(value) for key, value in model.items()},
              "fixed_correction": {key: _array_record(value) for key, value in correction.items()},
              "derived_F0": _array_record(np.zeros(ndof, dtype=np.float64))}
    _write_json(output/"input_checks.json", dict(status="pass", manifest_bindings=bound,
        array_identity=arrays, dimensions=dict(ndof=ndof, elements=ne, free=len(free), fixed=len(fixed)),
        candidate_byte_identity=True, archived_rounded_trials_byte_identity=True,
        fixed_delta_exact_zero=True, prescribed_base_exact=True, direction_recomputed=False,
        original_internal_force_byte_identity=_same(correction["internal_force"], candidate["internal_force"])))
    return model, correction, metadata, spec, rounded, fixed, free, bound, update_summary


def _state_metrics(hp, u, alpha, retained, model, metadata, fixed, free, precision):
    with localcontext() as context:
        context.prec = precision
        du = [_d(value) for value in u]
        if retained is not None:
            du = [value+_d(alpha)*_d(delta) for value, delta in zip(du, retained)]
        internal = hp["internal_decimal"]
        material = hp["material_internal_decimal"]
        regularization = hp["regularization_internal_decimal"]
        _require(len(internal) == len(material) == len(regularization) == len(u), "HP force shape mismatch")
        _require(len(hp["J_decimal"]) == 576 and all(len(row) == 9 for row in hp["J_decimal"]), "HP J shape mismatch")
        _require(all(_finite_decimals(hp[key]) for key in
                     ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal",
                      "J_decimal", "material_energy_decimal")), "nonfinite HP result")
        dscale = max(abs(_d(TARGET)), Decimal("1e-6"))
        floor = Decimal("1e-8")*_d(metadata["force_scale_per_length"])*dscale
        free_norm = _norm([internal[i] for i in free])
        fixed_norm = _norm([internal[i] for i in fixed])
        scale = max(free_norm, fixed_norm, floor)
        _require(scale.is_finite() and scale > 0, "invalid HF4 force scale")
        prescribed = [_d(b)+_d(TARGET)*_d(v) for b, v in zip(model["base"], model["direction"])]
        constraint = [du[i]-prescribed[i] for i in fixed]
        error = max(abs(value) for value in constraint)
        reaction = [Decimal(0)]*len(u)
        for i in fixed:
            reaction[i] = internal[i]
        balance = [sum((reaction[i] for i in range(component, len(u), 2)), Decimal(0)) for component in (0, 1)]
        Jmin = min(value for row in hp["J_decimal"] for value in row)
        energy = hp["material_energy_decimal"]
        groups = {name.removeprefix("group_"): _dot([_d(x) for x in vector], reaction)
                  for name, vector in model.items() if name.startswith("group_")}
        return dict(schema_version="hf4-retained-update-hp-1.0", precision_digits=precision,
            internal_decimal=internal, material_internal_decimal=material,
            regularization_internal_decimal=regularization, J_decimal=hp["J_decimal"],
            material_energy_decimal=energy, displacement_at_context_decimal=du,
            free_residual_norm_decimal=free_norm, fixed_reaction_norm_decimal=fixed_norm,
            force_floor_decimal=floor, force_scale_decimal=scale, relative_residual_decimal=free_norm/scale,
            relative_residual_uses="HF4 SF recomputed here; generic reference relative_residual discarded",
            prescribed_decimal=prescribed, fixed_constraint_decimal=constraint,
            constraint_error_decimal=error, relative_constraint_decimal=error/dscale,
            displacement_scale_decimal=dscale, support_reaction_decimal=reaction,
            force_balance_decimal=balance, relative_force_balance_decimal=_norm(balance)/scale,
            group_constraint_on_model_force_decimal=groups, minimum_J_decimal=Jmin,
            solid_material_energy_decimal=sum((value for value, solid in zip(energy, model["solid"]) if solid), Decimal(0)),
            medium_material_energy_decimal=sum((value for value, solid in zip(energy, model["solid"]) if not solid), Decimal(0)),
            diagnostic_state_only=True, production_accepted=False)


def _crosscheck(low, high, free):
    with localcontext() as context:
        context.prec = 110
        checks = {}
        for key in ("internal_decimal", "material_internal_decimal", "regularization_internal_decimal"):
            _require(len(low[key]) == len(high[key]), "cross-precision vector shape mismatch")
            difference = [a-b for a, b in zip(low[key], high[key])]
            absolute = _norm(difference)
            free_absolute = _norm([difference[i] for i in free])
            checks[key] = dict(full_difference_norm_N=absolute, free_difference_norm_N=free_absolute,
                               scale_N=high["force_scale_decimal"],
                               full_relative=absolute/high["force_scale_decimal"],
                               free_relative=free_absolute/high["force_scale_decimal"])
        checks["J_max_absolute_difference"] = max(abs(a-b) for ra, rb in zip(low["J_decimal"], high["J_decimal"])
                                                for a, b in zip(ra, rb))
        # The frozen 1e-30 gate applies to actual total force, full and free.
        total = checks["internal_decimal"]
        checks["passed"] = total["full_relative"] <= CROSS_TARGET and total["free_relative"] <= CROSS_TARGET
        checks["criterion"] = CROSS_TARGET
        return checks


def run(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/"states").mkdir()
    started = perf_counter()
    own_path = Path(__file__).resolve()
    own_sha = _sha(own_path)
    summary = dict(schema_version="hf4-retained-update-summary-1.0", status="incomplete",
                   stage="0", diagnostic_only=True, production_accepted=False,
                   dependent_stage_gate_pass=False, expected_states=5,
                   expected_HP_evaluations=10, completed_HP_evaluations=0, rows=[], errors=[])

    def persist():
        summary["elapsed_seconds"] = perf_counter()-started
        _write_json(output/"summary.json", summary)

    persist()
    try:
        model, correction, metadata, spec, rounded, fixed, free, bound, old_summary = _load_bound_inputs(root, output)
        summary["input_identity_status"] = "pass"
        summary["input_bindings"] = bound
        summary["implementation_sha256"] = own_sha
        helper_path = root/"hf_repo/scripts/hf2_precision_reference.py"
        module_spec = importlib.util.spec_from_file_location("hf2_retained_update_reference", helper_path)
        helper = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(helper)
        fixture = {key: model[key] for key in ("grad", "hessian", "weights", "lam", "mu", "kr", "connectivity", "fixed_dofs")}
        fixture["F0"] = np.zeros(len(correction["u"]), dtype=np.float64)
        references = {precision: helper.DecimalQ1Reference(fixture, precision=precision) for precision in PRECISIONS}
        _require(all(np.array_equal(reference.fixed, fixed) and np.array_equal(reference.free, free)
                     for reference in references.values()), "HP DOF partition differs from archived model")
        _write_json(output/"metadata.json", dict(created_utc=datetime.now(timezone.utc).isoformat(),
            input_bindings=bound, script_sha256=own_sha, source_root_record=str(root),
            target_mm=TARGET, alpha=list(ALPHAS), precisions=list(PRECISIONS), F0="exact zero vector",
            production_target=PRODUCTION_TARGET, crossprecision_target=CROSS_TARGET,
            constraint_target=spec["numerical_criteria"]["hp_relative_constraint"],
            armijo_c_binary64_hex=float(spec["solver"]["armijo_c"]).hex(),
            interpretation="at least one retained intervention must pass; rounded acceptance failures are expected controls",
            strong_compression_or_full_path_claim=False, production_imports=False, direction_recomputed=False))
        states = [("base", 0.0, "base", correction["u"])]
        for alpha in ALPHAS:
            tag = "1" if alpha == 1 else "half"
            states.extend([(f"rounded_{tag}", alpha, "rounded", rounded[alpha]),
                           (f"retained_{tag}", alpha, "retained", correction["u"])])
        base_metrics = {}
        for name, alpha, representation, state_u in states:
            pair = {}
            row = dict(name=name, alpha=alpha, representation=representation, status="incomplete", files={})
            for precision in PRECISIONS:
                begin = perf_counter()
                try:
                    kwargs = dict(direction=correction["delta"], offset=alpha, derivative=False) if representation == "retained" else dict(derivative=False)
                    hp = references[precision].evaluate(state_u, 0.0, **kwargs)
                    metrics = _state_metrics(hp, state_u, alpha,
                        correction["delta"] if representation == "retained" else None,
                        model, metadata, fixed, free, precision)
                    with localcontext() as context:
                        context.prec = precision
                        baseline = metrics if representation == "base" else base_metrics[precision]
                        base_scale = baseline["force_scale_decimal"]
                        phi0 = (baseline["free_residual_norm_decimal"]/base_scale)**2/2
                        phi = (metrics["free_residual_norm_decimal"]/base_scale)**2/2
                        bound_phi = (1-2*_d(spec["solver"]["armijo_c"])*_d(alpha))*phi0
                        metrics.update(base_force_scale_decimal=base_scale, base_phi_decimal=phi0,
                            phi_fixed_base_scale_decimal=phi, armijo_bound_decimal=bound_phi,
                            armijo_pass=bool(phi <= bound_phi),
                            production_target_pass=bool(metrics["relative_residual_decimal"] <= PRODUCTION_TARGET),
                            constraint_pass=bool(metrics["relative_constraint_decimal"] <= Decimal(spec["numerical_criteria"]["hp_relative_constraint"])),
                            positive_J=bool(metrics["minimum_J_decimal"] > 0))
                    if representation == "base":
                        base_metrics[precision] = metrics
                        if precision == 50:
                            _require(metrics["relative_residual_decimal"] == Decimal(old_summary["base_hp_relative_residual"]),
                                     "base HP50 does not reproduce archived candidate residual with the original HF4 scale")
                    metrics.update(name=name, representation=representation, alpha=alpha,
                                   elapsed_seconds=perf_counter()-begin)
                    filename = f"{name}_hp{precision}.json"
                    _write_json(output/"states"/filename, metrics)
                    row["files"][str(precision)] = dict(path="states/"+filename, sha256=_sha(output/"states"/filename))
                    pair[precision] = metrics
                except Exception as error:
                    exception = dict(name=name, precision=precision, type=type(error).__name__, message=str(error))
                    summary["errors"].append(exception)
                    _write_json(output/"states"/f"{name}_hp{precision}_failure.json", exception)
                summary["completed_HP_evaluations"] += 1
                persist()
                print(json.dumps(dict(name=name, precision=precision, completed=summary["completed_HP_evaluations"],
                                      computed=precision in pair)), flush=True)
            if len(pair) == 2:
                comparison = _crosscheck(pair[50], pair[80], free)
                valid = comparison["passed"] and all(value["constraint_pass"] and value["positive_J"] for value in pair.values())
                accept_goal = all(value["production_target_pass"] and value["armijo_pass"] for value in pair.values())
                row.update(status="valid_diagnostic" if valid else "invalid_diagnostic", validity_pass=bool(valid),
                           production_target_and_armijo_pass=bool(accept_goal), crossprecision=comparison,
                           metrics={str(precision): {key: value[key] for key in
                               ("relative_residual_decimal", "force_scale_decimal", "free_residual_norm_decimal",
                                "fixed_reaction_norm_decimal", "force_floor_decimal", "relative_constraint_decimal",
                                "minimum_J_decimal", "phi_fixed_base_scale_decimal", "armijo_bound_decimal",
                                "production_target_pass", "armijo_pass")}
                                    for precision, value in pair.items()})
            else:
                row.update(status="invalid_diagnostic", validity_pass=False, production_target_and_armijo_pass=False)
            summary["rows"].append(row)
            persist()
        unchanged = all(_sha(root/relative) == entry["sha256"] for relative, entry in bound.items()) and _sha(own_path) == own_sha
        all_valid = (not summary["errors"] and len(summary["rows"]) == 5
                     and all(row["validity_pass"] for row in summary["rows"]))
        retained_pass = any(row["representation"] == "retained" and row["validity_pass"]
                            and row["production_target_and_armijo_pass"] for row in summary["rows"])
        summary.update(inputs_and_implementation_unchanged=unchanged, all_diagnostics_valid=bool(all_valid),
                       retained_intervention_pass=bool(retained_pass),
                       dependent_stage_gate_pass=bool(unchanged and all_valid and retained_pass),
                       status="gate_pass" if unchanged and all_valid and retained_pass else "not_pass",
                       conclusion="fixed-update intervention only; no production state accepted and no full-path or strong-compression claim")
    except Exception as error:
        summary["errors"].append(dict(type=type(error).__name__, message=str(error)))
        summary.update(status="not_pass", dependent_stage_gate_pass=False)
    persist()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.output)
    print(json.dumps(dict(status=result["status"], elapsed_seconds=result["elapsed_seconds"],
                          completed_HP_evaluations=result["completed_HP_evaluations"], errors=result["errors"])), flush=True)
    return 0 if result["status"] == "gate_pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
