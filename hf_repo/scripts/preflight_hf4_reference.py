"""Budgeted HF4 reference preflight; no production/FE imports or operations.

Derive actual binary64 coefficients independently from the frozen JSON spec,
then recompute each (gamma,d) reference at both requested precisions. Every
state and progress summary is committed atomically before proceeding. Failure
is explicit and returns a nonzero process code; physical allowances and
reference arithmetic are reported separately. External monitoring owns the
wall-time/RSS budget. This script contains no automatic retry or parameter
adjustment, and an existing output directory is never overwritten.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
import math
import os
from pathlib import Path
from time import perf_counter

from hf4_normal_reference import crosscheck_normal_reference


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _d(value):
    return Decimal.from_float(float(value))


def _number(value, name, *, positive=True):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a JSON number")
    value = float(value)
    if not math.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ValueError(f"invalid {name}")
    return value


def _criterion(criteria, key):
    value = Decimal(criteria[key])
    if not value.is_finite() or value <= 0:
        raise ValueError(f"criterion {key} must be finite and positive")
    return value


def _check(name, value, limit, *, numerator=None, scale=None, units="1"):
    item = dict(name=name, comparison="<=", value_decimal=str(value),
                limit_decimal=str(limit), units=units, passed=bool(value <= limit))
    if numerator is not None:
        item["absolute_numerator_decimal"] = str(numerator)
        item["scale_decimal"] = str(scale)
    return item


def _condition(name, passed, details=None):
    item = dict(name=name, comparison="boolean", passed=bool(passed))
    if details is not None:
        item["details"] = details
    return item


def _scales(inputs, E):
    return (_d(E)*_d(inputs["width"])*_d(inputs["thickness"]),
            _d(inputs["gap"]), _d(inputs["H1"])+_d(inputs["H2"])+_d(inputs["gap"]))


def _numerical_checks(reference, inputs, E, criteria):
    """Re-evaluate checks from the archived reference values, not self-status."""
    equation_tol = _criterion(criteria, "reference_equation_relative")
    cross_tol = _criterion(criteria, "precision_crosscheck_relative")
    EA, g0, total_height = _scales(inputs, E)
    checks = []
    for label in ("low", "high"):
        values = reference[label]
        finite, hard = values["finite_gamma"], values["hard_contact"]
        for key in ("normalized_length_residual", "normalized_traction_residual"):
            checks.append(_check(label+"_finite_"+key, abs(Decimal(finite[key])), equation_tol))
        hard_length = abs(Decimal(hard["length_residual_mm"]))
        checks.append(_check(label+"_hard_length_equation", hard_length/total_height,
                             equation_tol, numerator=hard_length, scale=total_height))
        checks.append(_condition(label+"_finite_positive_compression_stretches",
                                  all(0 < Decimal(finite[key]) <= 1 for key in ("s_s", "s_v"))))
        checks.append(_condition(label+"_hard_unilateral_conditions",
                                  Decimal(hard["force_N"]) >= 0 and Decimal(hard["gap_mm"]) >= 0
                                  and Decimal(hard["complementarity_MPa_mm"]) == 0))
        checks.append(_condition(label+"_exact_binary64_binding",
                                  all(values["inputs"]["binary64_hex"][key] == float(value).hex()
                                      and values["inputs"]["decimal"][key] == str(_d(value))
                                      for key, value in inputs.items())))
        if inputs["d"] == 0:
            checks.append(_condition(label+"_zero_reference_exact",
                                      Decimal(finite["force_N"]) == 0
                                      and Decimal(finite["gap_mm"]) == g0
                                      and Decimal(finite["s_s"]) == 1 and Decimal(finite["s_v"]) == 1))
    for model in ("finite_gamma", "hard_contact"):
        fields = ("force_N", "gap_mm", "s_s", "s_v") if model == "finite_gamma" else ("force_N", "gap_mm", "s_s")
        for key in fields:
            error = abs(Decimal(reference["low"][model][key])-Decimal(reference["high"][model][key]))
            scale = EA if key == "force_N" else g0 if key == "gap_mm" else Decimal(1)
            checks.append(_check("crossprecision_"+model+"_"+key, error/scale, cross_tol,
                                 numerator=error, scale=scale))
    return checks


def _model_checks(values, inputs, E, criteria):
    """Physical allowance is separate from the same-model numerical checks."""
    EA, g0, _ = _scales(inputs, E)
    d = _d(inputs["d"])
    force, gap = (Decimal(values["finite_gamma"][key]) for key in ("force_N", "gap_mm"))
    hard_force, hard_gap = (Decimal(values["hard_contact"][key]) for key in ("force_N", "gap_mm"))
    gap_error, force_error = abs(gap-hard_gap), abs(force-hard_force)
    if d <= _d(criteria["preclosure_max_d_mm"]):
        phase = "preclosure"
        checks = [_check("preclosure_force_over_EA", abs(force)/EA,
                         _criterion(criteria, "preclosure_force_over_EA"), numerator=abs(force), scale=EA),
                  _check("preclosure_gap_error_over_g0", gap_error/g0,
                         _criterion(criteria, "preclosure_gap_error_over_g0"), numerator=gap_error, scale=g0)]
    elif d == g0:
        phase = "closure"
        checks = [_check("closure_force_over_EA", abs(force)/EA,
                         _criterion(criteria, "closure_force_over_EA"), numerator=abs(force), scale=EA),
                  _check("closure_gap_over_g0", gap/g0,
                         _criterion(criteria, "closure_gap_over_g0"), numerator=gap, scale=g0)]
    elif d >= _d(criteria["postclosure_min_d_mm"]):
        phase = "postclosure"
        if hard_force <= 0:
            raise ValueError("postclosure criterion requires positive hard-contact force")
        checks = [_check("postclosure_force_relative_hard", force_error/hard_force,
                         _criterion(criteria, "postclosure_force_relative_hard"), numerator=force_error, scale=hard_force),
                  _check("postclosure_gap_over_g0", gap/g0,
                         _criterion(criteria, "postclosure_gap_over_g0"), numerator=gap, scale=g0)]
    else:
        raise ValueError("target lies outside the three frozen model-criterion phases")
    return dict(phase=phase, checks=checks,
                signed_force_difference_N=str(force-hard_force),
                signed_gap_difference_mm=str(gap-hard_gap),
                interpretation="finite-medium versus ideal-contact allowance; not numerical residual or experimental validation")


def _bound_assumptions(spec, inputs, gamma):
    """Check the premises of the prospective bounds in the associated note."""
    d = {key: _d(value) for key, value in inputs.items()}
    dg = _d(gamma)
    geometry = {"width": Decimal(1), "H1": Decimal(1), "H2": Decimal(1),
                "gap": Decimal("0.25"), "thickness": Decimal(1)}
    return [
        _condition("proof_geometry_and_E", all(d[key] == value for key, value in geometry.items())
                   and _d(spec["material"]["E_MPa"]) == 1),
        _condition("proof_solid_material_bounds", 0 <= d["lam_s"] < Decimal("0.58")
                   and 0 < d["mu_s"] < Decimal("0.39")
                   and d["lam_s"]+2*d["mu_s"] > Decimal("1.34")),
        _condition("proof_actual_medium_bounds", 0 <= d["lam_v"] < Decimal("0.58")*dg
                   and 0 < d["mu_v"] < Decimal("0.39")*dg),
        _condition("proof_gamma_bound", 0 < dg <= Decimal("1e-6")),
        _condition("proof_target_set", d["d"] in tuple(Decimal(value) for value in
                   ("0", "0.125", "0.21875", "0.25", "0.28125", "0.375"))),
    ]


def _parameters(spec):
    if spec["schema_version"] != "hf4-normal-validation-1.0":
        raise ValueError("unsupported spec schema")
    if spec["status"] != "frozen_before_numerical_execution":
        raise ValueError("preflight requires an explicitly frozen specification")
    g, m = spec["geometry"], spec["material"]
    if m["formulation"] != "plane_strain":
        raise ValueError("reference is restricted to plane strain")
    E, nu = _number(m["E_MPa"], "E"), _number(m["nu"], "nu", positive=False)
    if nu >= 0.5:
        raise ValueError("require 0<=nu<0.5")
    # Written independently of production; ordinary Python float operations
    # intentionally produce actual binary64 material coefficients.
    lam_s = E*nu/((1+nu)*(1-2*nu))
    mu_s = E/(2*(1+nu))
    base = dict(lam_s=lam_s, mu_s=mu_s,
                width=_number(g["width_mm"], "width"), H1=_number(g["lower_height_mm"], "H1"),
                H2=_number(g["upper_height_mm"], "H2"), gap=_number(g["gap_mm"], "gap"),
                thickness=_number(g["thickness_mm"], "thickness"))
    gammas = [_number(value, "gamma") for value in spec["gammas"]]
    targets = [_number(value, "target", positive=False) for value in spec["targets_mm"]]
    if len(gammas) != 2 or len(set(gammas)) != 2 or any(value > 1 for value in gammas):
        raise ValueError("frozen preflight expects two distinct 0<gamma<=1 values")
    if len(targets) != 6 or targets[0] != 0 or any(b <= a for a, b in zip(targets, targets[1:])):
        raise ValueError("frozen preflight expects six increasing targets starting at zero")
    for key in ("reference_equation_relative", "precision_crosscheck_relative"):
        _criterion(spec["numerical_criteria"], key)
    return base, E, gammas, targets


def run(spec_path, output):
    spec_path, output = Path(spec_path).resolve(), Path(output).resolve()
    spec_bytes = spec_path.read_bytes()
    spec = json.loads(spec_bytes.decode("utf-8-sig"))
    base, E, gammas, targets = _parameters(spec)
    output.mkdir(parents=True, exist_ok=False)
    (output/"states").mkdir()
    (output/"spec_used.json").write_bytes(spec_bytes)
    script = Path(__file__).resolve()
    implementation = [script, script.with_name("hf4_normal_reference.py")]
    binding = dict(spec_sha256=hashlib.sha256(spec_bytes).hexdigest(),
                   implementation_sha256={path.name: _sha(path) for path in implementation})
    _write_json(output/"metadata.json", dict(schema_version="hf4-reference-preflight-1.0",
                 created_utc=datetime.now(timezone.utc).isoformat(), binding=binding,
                 spec_copy="spec_used.json", expected_states=len(gammas)*len(targets),
                 coefficient_convention="actual Python binary64 lam_s/mu_s, then actual gamma products",
                 reference_imports="standard library only; no production/FE",
                 crossprecision_scales="force/(E*A), gap/g0, absolute stretch differences",
                 limits=spec["resource_limits"], budget_owner="external process monitor"))
    started = perf_counter()
    rows = []

    def summary(status, reason):
        value = dict(schema_version="hf4-reference-preflight-summary-1.0", status=status,
                     numerical_status="pass" if rows and all(row["numerical_status"] == "pass" for row in rows) else "not_pass",
                     model_status="pass" if rows and all(row["model_status"] == "pass" for row in rows) else "not_pass",
                     expected_states=len(gammas)*len(targets), completed_states=len(rows),
                     failed_states=sum(row["status"] != "pass" for row in rows), states=rows,
                     progress_reason=reason, elapsed_seconds=perf_counter()-started,
                     binding=binding, scope="independent uniform reference preflight only; no FE execution",
                     qualification="not_evaluated", functionality="not_evaluated",
                     cylinder_and_nonuniform_contact="not_evaluated")
        _write_json(output/"summary.json", value)
        return value

    summary("incomplete", "running")
    for gamma_index, gamma in enumerate(gammas):
        for target_index, target in enumerate(targets):
            begin = perf_counter()
            name = f"gamma_{gamma_index:02d}_target_{target_index:02d}.json"
            inputs = dict(base, lam_v=gamma*base["lam_s"], mu_v=gamma*base["mu_s"], d=target)
            record = dict(schema_version="hf4-reference-preflight-state-1.0", gamma_index=gamma_index,
                          target_index=target_index, gamma_binary64_hex=gamma.hex(), d_mm=target,
                          binding=binding, reference_inputs=inputs)
            try:
                with localcontext() as context:
                    context.prec = int(spec["crosscheck_precision_digits"])+32
                    assumptions = _bound_assumptions(spec, inputs, gamma)
                    record["prospective_bound_assumptions"] = assumptions
                    if not all(item["passed"] for item in assumptions):
                        raise ValueError("actual inputs are outside the documented prospective-bound premises")
                    reference = crosscheck_normal_reference(inputs, spec["precision_digits"],
                                                           spec["crosscheck_precision_digits"])
                    numeric = _numerical_checks(reference, inputs, E, spec["numerical_criteria"])
                    # The more accurate independent solve drives the physical
                    # model comparison; both precisions remain in the record.
                    model = _model_checks(reference["high"], inputs, E, spec["model_criteria"])
                    record.update(reference=reference, numerical_checks=numeric, model_comparison=model,
                                  numerical_status="pass" if all(item["passed"] for item in numeric) else "not_pass",
                                  model_status="pass" if all(item["passed"] for item in model["checks"]) else "not_pass")
                    record["status"] = "pass" if record["numerical_status"] == record["model_status"] == "pass" else "not_pass"
            except Exception as error:
                record.update(status="error", numerical_status="not_pass", model_status="not_evaluated",
                              error=dict(type=type(error).__name__, message=str(error)))
            record["elapsed_seconds"] = perf_counter()-begin
            _write_json(output/"states"/name, record)
            rows.append(dict(gamma_index=gamma_index, target_index=target_index, d_mm=target,
                             file="states/"+name, sha256=_sha(output/"states"/name),
                             status=record["status"], numerical_status=record["numerical_status"],
                             model_status=record["model_status"], elapsed_seconds=record["elapsed_seconds"]))
            summary("incomplete", "running")
            print(json.dumps(dict(completed_states=len(rows), expected_states=len(gammas)*len(targets),
                                  gamma_index=gamma_index, target_index=target_index, status=record["status"])), flush=True)
    unchanged = (_sha(spec_path) == binding["spec_sha256"] and
                 all(_sha(path) == binding["implementation_sha256"][path.name] for path in implementation))
    passed = unchanged and all(row["status"] == "pass" for row in rows)
    result = summary("pass" if passed else "not_pass", "completed")
    result["inputs_and_implementation_unchanged"] = unchanged
    _write_json(output/"summary.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.spec, args.output)
    print(json.dumps(dict(status=result["status"], completed_states=result["completed_states"],
                          failed_states=result["failed_states"], elapsed_seconds=result["elapsed_seconds"])), flush=True)
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
